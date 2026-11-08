"""Compare the forced-choice wiki run (v1) with the abstention run (v2) on the same cohort.

Reports how many records abstain, which v1 labels they had been forced into, label agreement on
records both runs call sufficient, and the v2 distribution with abstentions excluded.

Run from the swarm-vsm directory:
  .venv/bin/python -B calibration/wiki_abstain/compare.py \
      --v1 pilot_wiki_overnight/final.jsonl --v2 pilot_wiki_abstain/final.jsonl
"""
import argparse
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load(p):
    return {a["record_id"]: a for a in map(json.loads, Path(p).read_text().splitlines())}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--v1", required=True)
    ap.add_argument("--v2", required=True)
    a = ap.parse_args()
    v1, v2 = load(a.v1), load(a.v2)
    if set(v1) != set(v2):
        raise SystemExit(f"cohorts differ: {len(set(v1) ^ set(v2))} IDs not shared")
    if any(x.get("evidence_status") is None for x in v2.values()):
        raise SystemExit("v2 rows without evidence_status; was --abstain used?")
    ids = sorted(v1)
    abst = [i for i in ids if v2[i]["evidence_status"] == "insufficient_evidence"]
    suff = [i for i in ids if v2[i]["evidence_status"] == "sufficient"]
    n = len(ids)
    v1_dist = Counter(v1[i]["primary_vsm"] for i in ids)
    forced_into = Counter(v1[i]["primary_vsm"] for i in abst)
    agree = sum(v1[i]["primary_vsm"] == v2[i]["primary_vsm"] for i in suff)
    out = {
        "records": n,
        "abstained": len(abst),
        "abstained_share": round(len(abst) / n, 4),
        "abstained_by_v1_label": {k: {"abstained": forced_into.get(k, 0), "v1_total": v,
                                      "share_of_v1_label": round(forced_into.get(k, 0) / v, 4)}
                                  for k, v in v1_dist.most_common()},
        "agreement_on_sufficient": round(agree / len(suff), 4) if suff else None,
        "v2_distribution_excluding_abstentions": dict(Counter(v2[i]["primary_vsm"] for i in suff).most_common()),
        "v1_distribution": dict(v1_dist.most_common()),
        "v1_confidence_of_abstained": {
            "lt_0.6": sum(v1[i]["confidence"] < 0.6 for i in abst),
            "0.6_0.8": sum(0.6 <= v1[i]["confidence"] < 0.8 for i in abst),
            "ge_0.8": sum(v1[i]["confidence"] >= 0.8 for i in abst),
        },
    }
    (HERE / "comparison.json").write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
