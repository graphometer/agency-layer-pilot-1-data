"""Freeze-time gold set builder (R39-F10). Deterministic, seed recorded.
Strata: (1) every mistral-vs-kimi disagreement from the dev+filler corpus; (2) every stop where a
judge abstained or returned no parseable answer; (3) every both-not_qualifying stop (minority class);
(4) stratified fill of both-qualifying stops balanced over condition x channel; target ~200 items.
Prompts are rebuilt from the fix-14 blinded views so labellers see the frozen instrument's input."""
import json, glob, random, sys, hashlib
sys.path.insert(0, "/mnt/vault/work/agency-layer/repo/evals/grading")
from judge import judge_input, prompt_text, stop_turns, render_issue_description
from pathlib import Path

C = "/mnt/vault/work/agent-staging/claude/2026-08-23_filler-grading/combined/judged"
PREP = "/mnt/vault/work/agent-staging/claude/2026-08-24_goldset/prep/per_run_blinded"
RESULTS = "/mnt/vault/work/agent-staging/claude/2026-08-23_filler-grading/combined/results"

def stop_channel(run, stop_idx):
    rows = [json.loads(l) for l in open(Path(RESULTS) / run / "transcript.jsonl")]
    if 0 <= stop_idx < len(rows):
        r = rows[stop_idx]
        for call in (r.get("tool_calls") or []):
            name = call.get("name") or (call.get("function") or {}).get("name") or ""
            if name.startswith("agency_layer_"):
                return "tool"
    return "prose"
SCEN = "/mnt/vault/work/agency-layer/repo/evals/scenarios"
OUT = "/mnt/vault/work/agent-staging/claude/2026-08-24_goldset"
SEED = 20260824

pools = {"disagree": [], "instrument": [], "both_not": [], "both_qual": []}
for fn in glob.glob(C + "/*.jsonl"):
    run = fn.rsplit("/", 1)[1][:-6]
    verd = {}
    for line in open(fn):
        r = json.loads(line)
        if r.get("kind") != "qualifying_issue_verdict": continue
        verd.setdefault((r["stop_key"], r["stop_source_index"]), {})[r["judge_id"]] = r
    for key, v in verd.items():
        m = v.get("mistral-primary", {}); k = v.get("kimi-secondary", {})
        a, b = m.get("parsed_verdict"), k.get("parsed_verdict")
        item = (run, key[0], key[1])
        if a in ("qualifying", "not_qualifying") and b in ("qualifying", "not_qualifying") and a != b:
            pools["disagree"].append(item)
        elif a == "cannot_determine" or b is None or a is None or b == "cannot_determine":
            pools["instrument"].append(item)
        elif a == b == "not_qualifying":
            pools["both_not"].append(item)
        elif a == b == "qualifying":
            pools["both_qual"].append(item)

rng = random.Random(SEED)
take = pools["disagree"] + pools["instrument"] + pools["both_not"]
# stratified fill from both_qual over condition x channel proxy (structured stop keys start with the affordance name; prose keys are sha256:)
strata = {}
for it in pools["both_qual"]:
    cond = it[0].split("__")[1]
    chan = stop_channel(it[0], it[2])
    strata.setdefault((cond, chan), []).append(it)
fill_target = 200 - len(take)
keys = sorted(strata)
per = max(1, fill_target // len(keys))
fill = []
for s in keys:
    pool = sorted(strata[s]); rng.shuffle(pool)
    fill.extend(pool[:per])
rng.shuffle(fill)
fill = fill[:fill_target]
items = take + fill
# channel enrichment: the channel-stratified gate needs tool-channel coverage; include every
# tool-channel both_qual stop not already selected (the corpus has few, all in C and D)
chosen = set(items)
tool_extra = [it for it in sorted(pools["both_qual"]) if it not in chosen and stop_channel(it[0], it[2]) == "tool"]
rng.shuffle(tool_extra)
items.extend(tool_extra[:50])
rng.shuffle(items)

full, label_only = [], []
skipped = 0
for n, (run, stop_key, stop_idx) in enumerate(items, 1):
    blinded_file = Path(PREP) / run / "blinded.jsonl"
    transcript = [json.loads(l) for l in open(blinded_file)]
    scen_dir = run.split("__")[0]
    issue = render_issue_description(Path(SCEN) / scen_dir / "scenario.yaml")
    matches = [(sk, si) for sk, si in stop_turns(transcript) if sk == stop_key and si == stop_idx]
    if not matches: skipped += 1; continue
    value = judge_input(transcript, issue, stop_key, stop_idx)
    iid = f"fz-{n:03d}"
    full.append({"id": iid, "run": run, "cond": run.split("__")[1], "family": int(run.split("-")[0][1:]),
                 "stop_key": stop_key, "stop_index": stop_idx, "channel": stop_channel(run, stop_idx),
                 "pool": next(p for p, lst in pools.items() if (run, stop_key, stop_idx) in lst),
                 "prompt": prompt_text(value)})
    label_only.append({"id": iid, "prompt": full[-1]["prompt"]})

with open(f"{OUT}/goldset_full.jsonl", "w") as f:
    for r in full: f.write(json.dumps(r) + "\n")
with open(f"{OUT}/goldset_for_labelling.jsonl", "w") as f:
    for r in label_only: f.write(json.dumps(r) + "\n")
import collections
print(f"seed {SEED}; items {len(full)} (skipped {skipped} unmatched after re-blind)")
print("pools:", {p: sum(1 for r in full if r['pool']==p) for p in pools})
print("cond:", dict(collections.Counter(r['cond'] for r in full)))
print("channel:", dict(collections.Counter(r['channel'] for r in full)))
print("family:", dict(collections.Counter(r['family'] for r in full)))
