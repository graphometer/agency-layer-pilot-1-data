"""Blinded judge qualification battery (R38): identical items, per-candidate locked configs.
Runs 3 candidates x 80 items x 2 passes; writes answers/<cand>_pass<n>.jsonl and QUALIFICATION.json."""
import json, os, sys, time, threading
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, "/mnt/vault/work/agency-layer/repo/evals/grading")
from judge import parse_verdict
from openai import OpenAI

V = "/mnt/vault/work/agent-staging/claude/2026-08-23_judge-validation"
items = [json.loads(l) for l in open(f"{V}/judge_items_full.jsonl")]
labels = {w: {json.loads(l)["id"]: json.loads(l)["label"] for l in open(f"{V}/labels/{w}.jsonl")} for w in ("sol", "kimi", "fable")}

def majority(iid, who):
    votes = [labels[w][iid] for w in who]
    q = votes.count("qualifying")
    if q * 2 == len(votes): return None  # tie
    return "qualifying" if q * 2 > len(votes) else "not_qualifying"

PANEL = {i["id"]: majority(i["id"], ("sol", "kimi", "fable")) for i in items}
PANEL_NO_KIMI = {i["id"]: majority(i["id"], ("sol", "fable")) for i in items}

CANDS = {
    "mistral-medium-2604": dict(base="https://api.mistral.ai/v1", model="mistral-medium-2604", env="MISTRAL_API_KEY", temp=0.0, mt=8, stop=["\n"]),
    "kimi-k3":             dict(base="https://api.moonshot.ai/v1", model="kimi-k3", env="KIMI_API_KEY", temp=1.0, mt=4096, stop=None),
    "grok-4.6":            dict(base="https://api.x.ai/v1", model="grok-4.6", env="XAI_API_KEY", temp=0.0, mt=4096, stop=None),
}

os.makedirs("answers", exist_ok=True)
lock = threading.Lock()

def call_one(cfg, item, client):
    kw = dict(model=cfg["model"], messages=[{"role": "user", "content": item["prompt"]}], max_tokens=cfg["mt"], temperature=cfg["temp"])
    if cfg["stop"]: kw["stop"] = cfg["stop"]
    for attempt in range(4):
        t0 = time.time()
        try:
            r = client.chat.completions.create(**kw)
            m = r.choices[0].message
            content = m.content or ""
            return {"id": item["id"], "cond": item["cond"], "raw": content[:200], "parsed": parse_verdict(content),
                    "latency": round(time.time() - t0, 2),
                    "out_tokens": r.usage.completion_tokens if r.usage else None, "in_tokens": r.usage.prompt_tokens if r.usage else None}
        except Exception as e:
            if attempt == 3:
                return {"id": item["id"], "cond": item["cond"], "raw": f"ERROR {type(e).__name__}: {str(e)[:150]}", "parsed": None, "latency": None}
            time.sleep(5 * (attempt + 1))

def run_pass(name, cfg, npass):
    out = f"answers/{name}_pass{npass}.jsonl"
    if os.path.exists(out):
        rows = [json.loads(l) for l in open(out)]
        if len(rows) == len(items): return rows
    client = OpenAI(base_url=cfg["base"], api_key=os.environ[cfg["env"]], timeout=180)
    workers = 1 if name.startswith("mistral") else 6
    with ThreadPoolExecutor(workers) as ex:
        rows = list(ex.map(lambda it: call_one(cfg, it, client), items))
    with open(out, "w") as f:
        for row in rows: f.write(json.dumps(row) + "\n")
    with lock: print(f"done {name} pass {npass}", flush=True)
    return rows

def kappa(pairs):
    n = len(pairs)
    if not n: return None
    po = sum(a == b for a, b in pairs) / n
    pa = sum(a == "qualifying" for a, _ in pairs) / n
    pb = sum(b == "qualifying" for _, b in pairs) / n
    pe = pa * pb + (1 - pa) * (1 - pb)
    return round((po - pe) / (1 - pe), 3) if pe < 1 else None

def metrics(rows, truth):
    by = {r["id"]: r for r in rows}
    scored = [(i["id"], by[i["id"]]["parsed"], truth[i["id"]]) for i in items if truth[i["id"]] is not None]
    n = len(scored)
    agree = sum(p == t for _, p, t in scored)
    unparse = sum(p is None for _, p, _ in scored)
    tp = sum(p == "qualifying" and t == "qualifying" for _, p, t in scored)
    fp = sum(p == "qualifying" and t == "not_qualifying" for _, p, t in scored)
    fn = sum(p != "qualifying" and t == "qualifying" for _, p, t in scored)
    percond = {}
    for c in "ABCD":
        sub = [(p, t) for iid, p, t in scored if by[iid]["cond"] == c]
        percond[c] = round(sum(p == t for p, t in sub) / len(sub), 3) if sub else None
    lat = [r["latency"] for r in rows if r["latency"]]
    return {"n": n, "agreement": round(agree / n, 4), "kappa": kappa([(p or "unparseable", t) for _, p, t in scored]),
            "qualifying_precision": round(tp / (tp + fp), 3) if tp + fp else None,
            "qualifying_recall": round(tp / (tp + fn), 3) if tp + fn else None,
            "unparseable": unparse, "per_condition_agreement": percond,
            "condition_gap": round(max(v for v in percond.values() if v is not None) - min(v for v in percond.values() if v is not None), 3),
            "mean_latency_s": round(sum(lat) / len(lat), 1) if lat else None,
            "total_out_tokens": sum(r.get("out_tokens") or 0 for r in rows)}

def main():
    passes = {}
    with ThreadPoolExecutor(3) as ex:
        futs = {name: ex.submit(lambda n=name, c=cfg: [run_pass(n, c, 1), run_pass(n, c, 2)]) for name, cfg in CANDS.items()}
        for name, f in futs.items(): passes[name] = f.result()
    report = {"gold_set": "judge_items_full.jsonl (80 items)", "panel_ties_excluded": sum(v is None for v in PANEL.values()),
              "no_kimi_ties_excluded": sum(v is None for v in PANEL_NO_KIMI.values()), "candidates": {}}
    for name, (p1, p2) in passes.items():
        m1, m2 = metrics(p1, PANEL), metrics(p2, PANEL)
        b1, b2 = {r["id"]: r["parsed"] for r in p1}, {r["id"]: r["parsed"] for r in p2}
        both = [(b1[i["id"]], b2[i["id"]]) for i in items]
        stability = round(sum(a == b for a, b in both) / len(both), 4)
        entry = {"config": {k: v for k, v in CANDS[name].items() if k != "env"}, "pass1": m1, "pass2": m2, "exact_label_stability": stability}
        if name == "kimi-k3":
            entry["pass1_vs_panel_excluding_own_votes"] = metrics(p1, PANEL_NO_KIMI)
            entry["pass2_vs_panel_excluding_own_votes"] = metrics(p2, PANEL_NO_KIMI)
        report["candidates"][name] = entry
    json.dump(report, open("QUALIFICATION.json", "w"), indent=2)
    print(json.dumps({k: {"agree_p1": v["pass1"]["agreement"], "agree_p2": v["pass2"]["agreement"],
                          "stability": v["exact_label_stability"], "kappa": v["pass1"]["kappa"],
                          "recall": v["pass1"]["qualifying_recall"], "gap": v["pass1"]["condition_gap"],
                          "unparseable": v["pass1"]["unparseable"] + v["pass2"]["unparseable"]}
                      for k, v in report["candidates"].items()}, indent=2))

main()
