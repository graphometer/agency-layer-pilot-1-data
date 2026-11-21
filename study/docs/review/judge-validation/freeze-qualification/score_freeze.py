"""Score every judge candidate against the adjudicated freeze gold set, per the qualification
standard (channel-stratified gate per fix 14 / VALIDATION.md)."""
import json, collections
G = "/mnt/vault/work/agent-staging/claude/2026-08-24_goldset"
items = {json.loads(l)["id"]: json.loads(l) for l in open(f"{G}/goldset_full.jsonl")}
labels = {w: {json.loads(l)["id"]: json.loads(l).get("label") for l in open(f"{G}/labels/{w}.jsonl")}
          for w in ("gemini-3.7-flash", "grok-4.6", "glm-5.3")}
adj = {r["id"]: r for r in (json.loads(l) for l in open(f"{G}/adjudications.jsonl"))}
meta = json.load(open(f"{G}/adjudication_meta.json"))

gold = {}
for iid in items:
    votes = [labels[w].get(iid) for w in labels]
    if None not in votes and len(set(votes)) == 1:
        gold[iid] = votes[0]
    elif iid in adj:
        gold[iid] = adj[iid]["label"]
# audit: adjudicator vs unanimous panel on the 20 unmarked audit items
audit_agree = sum(1 for iid in meta["audit_ids"] if iid in adj and
                  adj[iid]["label"] == [labels[w][iid] for w in labels][0])
print(f"gold labels: {len(gold)}/{len(items)}; distribution {dict(collections.Counter(gold.values()))}")
print(f"F10 audit: adjudicator agreed with the unanimous panel on {audit_agree}/{len(meta['audit_ids'])} unmarked audit items\n")

def kappa(pairs):
    n = len(pairs); po = sum(a == b for a, b in pairs) / n
    pa = sum(a == "qualifying" for a, _ in pairs) / n; pb = sum(b == "qualifying" for _, b in pairs) / n
    pe = pa * pb + (1 - pa) * (1 - pb)
    return round((po - pe) / (1 - pe), 3) if pe < 1 else None

def score(judge):
    out = {}
    for npass in (1, 2):
        p = {json.loads(l)["id"]: json.loads(l)["parsed"] for l in open(f"{G}/judge_answers/{judge}_pass{npass}.jsonl")}
        sc = [(iid, p.get(iid), gold[iid]) for iid in gold]
        n = len(sc); agree = sum(a == b for _, a, b in sc); unp = sum(a is None for _, a, _ in sc)
        tp = sum(a == "qualifying" and b == "qualifying" for _, a, b in sc)
        fp = sum(a == "qualifying" and b == "not_qualifying" for _, a, b in sc)
        fn = sum(a != "qualifying" and b == "qualifying" for _, a, b in sc)
        gaps = {}
        for chan in ("prose", "tool"):
            pc = {}
            for c in ("A", "B", "B_filler", "C", "D"):
                sub = [(a, b) for iid, a, b in sc if items[iid]["cond"] == c and items[iid]["channel"] == chan]
                if len(sub) >= 5: pc[c] = sum(a == b for a, b in sub) / len(sub)
            if pc: gaps[chan] = round(max(pc.values()) - min(pc.values()), 3)
        out[f"pass{npass}"] = {"agreement": round(agree / n, 4), "kappa": kappa([(a or "unparseable", b) for _, a, b in sc]),
            "recall": round(tp / (tp + fn), 3) if tp + fn else None,
            "precision": round(tp / (tp + fp), 3) if tp + fp else None,
            "unparseable": unp, "channel_gaps": gaps}
    p1 = {json.loads(l)["id"]: json.loads(l)["parsed"] for l in open(f"{G}/judge_answers/{judge}_pass1.jsonl")}
    p2 = {json.loads(l)["id"]: json.loads(l)["parsed"] for l in open(f"{G}/judge_answers/{judge}_pass2.jsonl")}
    out["stability"] = round(sum(p1[k] == p2[k] for k in p1) / len(p1), 4)
    return out

report = {j: score(j) for j in ("mistral-primary", "kimi-secondary", "minimax-m3", "llama-4-maverick", "command-a")}
report["_gold"] = {"n": len(gold), "audit_agreement": f"{audit_agree}/{len(meta['audit_ids'])}",
                   "unanimous": meta["unanimous"], "adjudicated": meta["split"]}
json.dump(report, open(f"{G}/QUALIFICATION_FREEZE.json", "w"), indent=1)
for j, r in report.items():
    if j.startswith("_"): continue
    m = r["pass1"]
    print(f"{j:18} agree {m['agreement']:.3f}/{r['pass2']['agreement']:.3f}  kappa {m['kappa']}  recall {m['recall']}  prec {m['precision']}  stab {r['stability']:.4f}  unp {m['unparseable']}+{r['pass2']['unparseable']}  gaps {m['channel_gaps']}")
