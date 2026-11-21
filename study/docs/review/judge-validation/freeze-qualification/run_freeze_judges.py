"""Freeze-set qualification runs for the seated pair (PM19): two identical passes each
over the 248-item gold set, per-judge locked configs from evals/grading/judge.py."""
import json, os, sys, time
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, "/mnt/vault/work/agency-layer/repo/evals/grading")
from judge import parse_verdict
from openai import OpenAI

G = "/mnt/vault/work/agent-staging/claude/2026-08-24_goldset"
items = [json.loads(l) for l in open(f"{G}/goldset_full.jsonl")]
os.makedirs(f"{G}/judge_answers", exist_ok=True)

JUDGES = {
    "mistral-primary": dict(base="https://api.mistral.ai/v1", model="mistral-medium-2604", env="MISTRAL_API_KEY", temp=0.0, mt=8, stop=["\n"], workers=4),
    "kimi-secondary":  dict(base="https://api.moonshot.ai/v1", model="kimi-k3", env="KIMI_API_KEY", temp=1.0, mt=4096, stop=None, workers=6),
}

def call(cfg, client, item):
    kw = dict(model=cfg["model"], messages=[{"role": "user", "content": item["prompt"]}], max_tokens=cfg["mt"], temperature=cfg["temp"])
    if cfg["stop"]: kw["stop"] = cfg["stop"]
    for attempt in range(4):
        try:
            r = client.chat.completions.create(**kw)
            c = r.choices[0].message.content or ""
            return {"id": item["id"], "parsed": parse_verdict(c), "raw": c[:100]}
        except Exception as e:
            if attempt == 3: return {"id": item["id"], "parsed": None, "raw": f"ERROR {str(e)[:100]}"}
            time.sleep(4 * (attempt + 1))

def run(judge, npass):
    cfg = JUDGES[judge]
    out = f"{G}/judge_answers/{judge}_pass{npass}.jsonl"
    if os.path.exists(out) and sum(1 for _ in open(out)) == len(items): return
    client = OpenAI(base_url=cfg["base"], api_key=os.environ[cfg["env"]], timeout=240)
    with ThreadPoolExecutor(cfg["workers"]) as ex:
        rows = list(ex.map(lambda it: call(cfg, client, it), items))
    with open(out, "w") as f:
        for r in rows: f.write(json.dumps(r) + "\n")
    print(f"{judge} pass {npass}: {sum(1 for r in rows if r['parsed'])}/{len(rows)} parsed", flush=True)

with ThreadPoolExecutor(2) as ex:
    list(ex.map(lambda j: [run(j, 1), run(j, 2)], JUDGES))
print("done")
