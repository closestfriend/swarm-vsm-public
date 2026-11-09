"""Draw the pre-registered judge-robustness samples from the frozen v2 cohorts (IDs only).

Wiki: 1,000 records, simple random by sha256("sj1:" + id) from the 6,051-record cohort.
Swarm Traces: 1,000 records, proportional to kind (480 payload / 399 recovered_text / 121 response),
within each kind the first by sha256("sj1:" + id).
Canaries: the next 10 records of each corpus in the same order, outside the main samples.
Writes cohort files usable with batch_classify_vsm.py --cohort-from. Run from the repo root:
    python3 calibration/second_judge/make_samples.py
"""
import json
from collections import Counter
from hashlib import sha256
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "calibration/second_judge/cohorts"
key = lambda rid: sha256(f"sj1:{rid}".encode()).hexdigest()


def write(name, src, records):
    counts = Counter(r["episode_id"] for r in records)
    cohort = {"config": src["config"], "episode_counts": dict(counts), "records": records}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{name}.json").write_text(json.dumps(cohort, indent=1) + "\n")
    return len(records)


wiki = json.loads((ROOT / "pilot_wiki_abstain/cohort.json").read_text())
order = sorted(wiki["records"], key=lambda r: key(r["id"]))
print("wiki_main", write("wiki_main", wiki, order[:1000]), "of", len(order))
print("wiki_canary", write("wiki_canary", wiki, order[1000:1010]))

swarm = json.loads((ROOT / "pilot_swarm_abstain/cohort.json").read_text())
kind = {json.loads(l)["record_id"]: json.loads(l)["record_kind"]
        for l in open(ROOT / "pilot_swarm_abstain/final.jsonl")}
pop = Counter(kind[r["id"]] for r in swarm["records"])
exact = {k: 1000 * n / sum(pop.values()) for k, n in pop.items()}
quota = {k: int(v) for k, v in exact.items()}   # largest-remainder allocation to exactly 1,000
for k in sorted(exact, key=lambda k: exact[k] - int(exact[k]), reverse=True)[:1000 - sum(quota.values())]:
    quota[k] += 1
assert quota == {"payload": 480, "recovered_text": 399, "response": 121}, quota
assert sum(quota.values()) == 1000
main, canary = [], []
for k in sorted(quota):
    rows = sorted((r for r in swarm["records"] if kind[r["id"]] == k), key=lambda r: key(r["id"]))
    main += rows[:quota[k]]
    canary += rows[quota[k]:quota[k] + {"payload": 4, "recovered_text": 4, "response": 2}[k]]
print("cohort kind counts:", dict(pop), "-> quotas:", quota)
print("swarm_main", write("swarm_main", swarm, main))
print("swarm_canary", write("swarm_canary", swarm, canary))
assert not ({r["id"] for r in canary} & {r["id"] for r in main})
