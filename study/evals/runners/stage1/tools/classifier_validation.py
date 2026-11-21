"""Measure a configured prose classifier on probes and observed turns.

This is a reporting tool, not a quality gate. Low accuracy is written to the
report and never changes the successful exit status.
"""

import argparse
import glob
import json
import os
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from harness import config as config_module, prose_classifier  # noqa: E402
from harness.cli import build_route_classifier  # noqa: E402
from harness.llm_classifier import FROZEN_PROMPT_VERSION, FROZEN_SAMPLING, ROUTES  # noqa: E402

# The validation inputs (real rehearsal turns and the independent label files) live in local
# staging and are withheld from the repository by design (PM14: rehearsal transcripts are never
# committed). There is therefore no committed default; pass --real-turns/--labels-dir explicitly
# or set the env vars. Provenance of the published report: the 2026-08-23 classifier staging area.
DEFAULT_REAL_TURNS = os.environ.get("AL_CLASSIFIER_REAL_TURNS", "")
DEFAULT_LABELS_DIR = os.environ.get("AL_CLASSIFIER_LABELS_DIR", "")
ERROR_LABEL = "__error__"


def read_jsonl(path):
    records = []
    with open(path, "r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if line.strip():
                record = json.loads(line)
                record["_line"] = line_number
                records.append(record)
    return records


def confusion(rows, expected_key="expect", predicted_key="got"):
    labels = list(ROUTES) + [ERROR_LABEL]
    matrix = {expected: {got: 0 for got in labels} for expected in ROUTES}
    for row in rows:
        expected = row[expected_key]
        got = row.get(predicted_key) or ERROR_LABEL
        if expected in matrix and got in matrix[expected]:
            matrix[expected][got] += 1
    return matrix


def accuracy_summary(rows, expected_key="expect", predicted_key="got"):
    correct = sum(row.get(predicted_key) == row.get(expected_key) for row in rows)
    count = len(rows)
    return {
        "count": count,
        "correct": correct,
        "accuracy": correct / count if count else None,
        "confusion": confusion(rows, expected_key, predicted_key),
    }


def classify_rows(classifier, rows, expected_key=None):
    output = []
    for row in rows:
        decision = classifier.classify(row["text"])
        item = {key: value for key, value in row.items() if key != "_line"}
        item.update({
            "got": decision.route,
            "ok": decision.route == row.get(expected_key) if expected_key else decision.ok,
            "raw": decision.raw,
            "error": decision.error,
            "failure_kind": decision.failure_kind,
            "sampling_sent": decision.sampling_sent,
            "usage": decision.usage,
        })
        output.append(item)
    return output


def cohen_kappa(labels_a, labels_b):
    pairs = [(labels_a[item], labels_b[item]) for item in labels_a if item in labels_b]
    count = len(pairs)
    if not count:
        return {"count": 0, "observed_agreement": None, "expected_agreement": None,
                "kappa": None}
    observed = sum(a == b for a, b in pairs) / count
    counts_a = Counter(a for a, _ in pairs)
    counts_b = Counter(b for _, b in pairs)
    expected = sum((counts_a[label] / count) * (counts_b[label] / count)
                   for label in set(counts_a) | set(counts_b))
    kappa = None if expected == 1.0 else (observed - expected) / (1.0 - expected)
    return {"count": count, "observed_agreement": observed,
            "expected_agreement": expected, "kappa": kappa}


def breakdown(consensus_rows, field):
    groups = {}
    for row in consensus_rows:
        groups.setdefault(str(row.get(field)), []).append(row)
    return {name: accuracy_summary(rows, "consensus_label", "got")
            for name, rows in sorted(groups.items())}


def label_analysis(real_results, labels_dir):
    result_by_id = {row["id"]: row for row in real_results}
    labellers = {}
    ignored_files = []
    consensus_labels = {}
    consensus_sources = {}
    for path in sorted(glob.glob(os.path.join(labels_dir, "*.jsonl"))):
        name = os.path.splitext(os.path.basename(path))[0]
        records = read_jsonl(path)
        if name == "consensus":
            for row in records:
                if row.get("id") in result_by_id and row.get("label") in ROUTES:
                    consensus_labels[row["id"]] = row["label"]
                    consensus_sources[row["id"]] = row.get("source")
            continue
        required = {"id", "label", "specific_request", "note"}
        if not records or any(not required.issubset(row) for row in records):
            ignored_files.append(os.path.basename(path))
            continue
        labels = {row["id"]: row["label"] for row in records}
        specific_requests = {row["id"]: row["specific_request"] for row in records}
        matched = []
        for identifier, label in labels.items():
            if identifier in result_by_id:
                matched.append({"id": identifier, "expect": label,
                                "got": result_by_id[identifier]["got"]})
        labellers[name] = {"labels": labels,
                           "specific_requests": specific_requests,
                           "agreement": accuracy_summary(matched)}

    names = sorted(labellers)
    kappas = {}
    for index, first in enumerate(names):
        for second in names[index + 1:]:
            kappas[f"{first}|{second}"] = cohen_kappa(
                labellers[first]["labels"], labellers[second]["labels"]
            )

    # The published consensus file is authoritative because it includes
    # adjudicated labels. Fall back to unanimous labels only for a fixture that
    # has no consensus file.
    if not consensus_labels and len(names) >= 2:
        for identifier in result_by_id:
            available = [labellers[name]["labels"][identifier] for name in names
                         if identifier in labellers[name]["labels"]]
            if len(available) >= 2 and len(set(available)) == 1:
                consensus_labels[identifier] = available[0]
                consensus_sources[identifier] = "unanimous labellers"

    # The two full-coverage files are the independent labellers; a short third
    # file is an adjudicator. Use their unanimous specific_request marks to make
    # PM15's mixed objection-plus-question subgroup identifiable.
    primary_names = sorted(names, key=lambda name: len(labellers[name]["labels"]), reverse=True)[:2]
    consensus_rows = []
    mixed_precedence_flags = []
    for identifier, label in consensus_labels.items():
        result = result_by_id.get(identifier)
        if result is None:
            continue
        row = dict(result)
        row["consensus_label"] = label
        row["consensus_source"] = consensus_sources.get(identifier)
        specifics = [labellers[name]["specific_requests"].get(identifier)
                     for name in primary_names]
        flag = None
        if len(specifics) == 2 and all(value is True for value in specifics) \
                and label == "on_dissent":
            flag = "specific_request_but_on_dissent"
        elif len(specifics) == 2 and all(value is False for value in specifics) \
                and label == "on_clarify":
            flag = "on_clarify_without_specific_request"
        row["mixed_precedence_flag"] = flag
        if flag:
            mixed_precedence_flags.append({"id": identifier, "flag": flag,
                                           "consensus_label": label,
                                           "model": row.get("model"),
                                           "condition": row.get("condition")})
        consensus_rows.append(row)

    return {
        "labellers": {name: data["agreement"] for name, data in labellers.items()},
        "ignored_label_files": ignored_files,
        "inter_labeller_kappa": kappas,
        "consensus": {
            **accuracy_summary(consensus_rows, "consensus_label", "got"),
            "labels": {row["id"]: row["consensus_label"] for row in consensus_rows},
            "by_condition": breakdown(consensus_rows, "condition"),
            "by_family": breakdown(consensus_rows, "family"),
            "by_subject_model": breakdown(consensus_rows, "model"),
            "mixed_precedence_flags": mixed_precedence_flags,
            "primary_specificity_labellers": primary_names,
        },
    }


def build_report(classifier, real_turns_path, labels_dir):
    probes = prose_classifier.load_probes()
    probe_results = classify_rows(classifier, probes, expected_key="expect")
    probe_sections = {}
    for split in ("train", "holdout"):
        rows = [row for row in probe_results if row.get("split") == split]
        probe_sections[split] = {**accuracy_summary(rows), "results": rows}

    real_turns = read_jsonl(real_turns_path)
    real_results = classify_rows(classifier, real_turns)
    keyword_rows = [{"expect": row["keyword_route"], "got": row["got"]}
                    for row in real_results]
    sent_values = []
    for row in probe_results + real_results:
        if row["sampling_sent"] not in sent_values:
            sent_values.append(row["sampling_sent"])
    return {
        "classifier": {
            "classifier_id": classifier.classifier_id,
            "version": classifier.version,
            "prompt_version": FROZEN_PROMPT_VERSION,
            "sampling_requested": dict(FROZEN_SAMPLING),
            "sampling_sent_observed": sent_values,
        },
        "probes": probe_sections,
        "real_turns": {
            "count": len(real_results),
            "keyword_agreement": accuracy_summary(keyword_rows),
            "results": real_results,
            "labels": label_analysis(real_results, labels_dir),
        },
    }


def format_accuracy(summary):
    if summary["accuracy"] is None:
        return f"{summary['correct']}/{summary['count']} n/a"
    return f"{summary['correct']}/{summary['count']} {summary['accuracy']:.3f}"


def render_confusion(title, matrix):
    labels = list(ROUTES) + [ERROR_LABEL]
    lines = [title, f"  {'expected':<13}" + "".join(f"{label:>12}" for label in labels)]
    for expected in ROUTES:
        lines.append(f"  {expected:<13}" +
                     "".join(f"{matrix[expected][got]:>12}" for got in labels))
    return lines


def render_table(report):
    lines = [
        f"Classifier: {report['classifier']['version']}",
        f"Sampling requested: {json.dumps(report['classifier']['sampling_requested'], sort_keys=True)}",
        f"Sampling sent observed: {json.dumps(report['classifier']['sampling_sent_observed'], sort_keys=True)}",
        "",
        "Dataset                         Correct/Count Accuracy",
        f"Probes train                    {format_accuracy(report['probes']['train'])}",
        f"Probes holdout                  {format_accuracy(report['probes']['holdout'])}",
        f"Real turns vs keyword           {format_accuracy(report['real_turns']['keyword_agreement'])}",
    ]
    labels = report["real_turns"]["labels"]
    for name, summary in sorted(labels["labellers"].items()):
        lines.append(f"Real turns vs {name:<14} {format_accuracy(summary)}")
    lines.append(f"Real turns vs consensus         {format_accuracy(labels['consensus'])}")
    if labels["ignored_label_files"]:
        lines.append("Ignored non-labeller files: " + ", ".join(labels["ignored_label_files"]))
    lines.extend(["", "Consensus accuracy by condition"])
    for name, summary in labels["consensus"]["by_condition"].items():
        lines.append(f"  {name:<29} {format_accuracy(summary)}")
    lines.append("Consensus accuracy by family")
    for name, summary in labels["consensus"]["by_family"].items():
        lines.append(f"  {name:<29} {format_accuracy(summary)}")
    lines.append("Consensus accuracy by subject model")
    for name, summary in labels["consensus"]["by_subject_model"].items():
        lines.append(f"  {name:<29} {format_accuracy(summary)}")
    lines.append("Mixed objection-plus-question flags")
    flags = labels["consensus"]["mixed_precedence_flags"]
    if flags:
        for item in flags:
            lines.append(f"  {item['id']:<8} {item['flag']} "
                         f"label={item['consensus_label']} model={item['model']} "
                         f"condition={item['condition']}")
    else:
        lines.append("  none")
    lines.append("Inter-labeller Cohen's kappa")
    if labels["inter_labeller_kappa"]:
        for pair, values in labels["inter_labeller_kappa"].items():
            shown = "n/a" if values["kappa"] is None else f"{values['kappa']:.3f}"
            lines.append(f"  {pair:<29} n={values['count']} kappa={shown}")
    else:
        lines.append("  n/a (fewer than two label files)")
    lines.extend(["", *render_confusion(
        "Probe train confusion", report["probes"]["train"]["confusion"]
    )])
    lines.extend(["", *render_confusion(
        "Probe holdout confusion", report["probes"]["holdout"]["confusion"]
    )])
    lines.extend(["", *render_confusion(
        "Real turns vs keyword confusion",
        report["real_turns"]["keyword_agreement"]["confusion"],
    )])
    for name, summary in sorted(labels["labellers"].items()):
        lines.extend(["", *render_confusion(
            f"Real turns vs {name} confusion", summary["confusion"]
        )])
    lines.extend(["", *render_confusion(
        "Real turns vs consensus confusion", labels["consensus"]["confusion"]
    )])
    return "\n".join(lines) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description="Measure a configured prose classifier")
    parser.add_argument("--config", required=True)
    parser.add_argument("--allow-live", action="store_true")
    parser.add_argument("--real-turns", default=DEFAULT_REAL_TURNS,
                        **({} if DEFAULT_REAL_TURNS else {"required": True}))
    # Without this, an empty labels dir would glob "*.jsonl" in the cwd and silently
    # consume unrelated files (Grok step-7 review, finding 5).
    parser.add_argument("--labels-dir", default=DEFAULT_LABELS_DIR,
                        **({} if DEFAULT_LABELS_DIR else {"required": True}))
    parser.add_argument(
        "--out", default="results/classifier_validation_mock.json",
        help="JSON report path (default: results/classifier_validation_mock.json)",
    )
    parser.add_argument("--text-out", help="plain-text report path; defaults beside --out")
    arguments = parser.parse_args(argv)

    config = config_module.load_config(arguments.config)
    classifier = build_route_classifier(
        config, allow_live=arguments.allow_live,
        config_dir=os.path.dirname(os.path.abspath(arguments.config)),
    )
    if classifier is None:
        raise ValueError("the config has no route_classifier")
    report = build_report(classifier, arguments.real_turns, arguments.labels_dir)
    text_path = arguments.text_out or os.path.splitext(arguments.out)[0] + ".txt"
    for path in (arguments.out, text_path):
        directory = os.path.dirname(os.path.abspath(path))
        os.makedirs(directory, exist_ok=True)
    with open(arguments.out, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, ensure_ascii=False, sort_keys=True)
        handle.write("\n")
    table = render_table(report)
    with open(text_path, "w", encoding="utf-8") as handle:
        handle.write(table)
    print(table, end="")
    print(f"JSON: {arguments.out}")
    print(f"Text: {text_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
