"""Score the keyword pass on both splits of the frozen probe set.

The two numbers mean different things and are reported separately on purpose.

TRAIN is every probe the rules were written or tuned against, including the five
Sol raised in review round 3 and the rules were then repaired to handle. Its
accuracy measures fitting. It is not evidence of anything else.

HOLDOUT is probes written before they were scored and never tuned against. Its
accuracy is the honest generalization estimate, and it is the number that
decided the keyword pass could not stay authoritative.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from harness import prose_classifier  # noqa: E402

ROUTES = ["on_clarify", "on_dissent", "on_decline", "none"]


def confusion_table(confusion):
    lines = ["             " + "".join(f"{c:>12}" for c in ROUTES)]
    for expected in ROUTES:
        row = "".join(f"{confusion.get((expected, got), 0):>12}" for got in ROUTES)
        lines.append(f"{expected:>13}" + row)
    return "\n".join(lines)


def report(verbose=False):
    """Returns (train_accuracy, holdout_accuracy, holdout_misses)."""
    out = {}
    for split in ("train", "holdout"):
        results, accuracy, confusion = prose_classifier.score_probes(split=split)
        wrong = [r for r in results if not r["ok"]]
        out[split] = (results, accuracy, confusion, wrong)
        if verbose:
            print(f"=== {split}: {len(results) - len(wrong)}/{len(results)} "
                  f"= {accuracy:.3f}")
            for r in wrong:
                print(f"    MISS {r['id']:<5} exp={r['expect']:<11} got={r['got']:<11} "
                      f"[{r['rule']}]")
                print(f"         {r['text'][:84]!r}")
            print(confusion_table(confusion))
            print()
    if verbose:
        print(f"rules {prose_classifier.RULES_VERSION}: "
              f"train {out['train'][1]:.3f} (fitting), "
              f"holdout {out['holdout'][1]:.3f} (generalization)")
        print("The keyword pass is not authoritative. The frozen LLM classifier decides "
              "and this route is recorded beside it.")
    return out["train"][1], out["holdout"][1], out["holdout"][3]


if __name__ == "__main__":
    report(verbose=True)
    # Exit 0 either way: the hold-out number is a measurement to report, not a
    # gate to pass. Turning it into a gate would invite tuning against it.
    raise SystemExit(0)
