"""Pre-registered analysis (PREREG.md). Writes aggregates only to calibration/second_judge/results.json.

usage: python3 calibration/second_judge/analyze.py [main|canary]
"""
import json, random, sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SET = sys.argv[1] if len(sys.argv) > 1 else "main"
COH = ROOT / "calibration/second_judge/cohorts"
BASE = {"wiki": ROOT / "pilot_wiki_abstain/final.jsonl", "swarm": ROOT / "pilot_swarm_abstain/final.jsonl"}
ARMS = {"A": "glm-5.2, v2 prompts", "B": "qwen3.5-397b, shared prompt", "Ap": "deepseek-v4-flash, v2 prompts"}
B_N, SEED = 2000, 0


def load_labels(path, ids):
    """id -> label; 'INSUFF' for insufficient_evidence; ids without a valid row -> 'INVALID'."""
    rows = {}
    p = Path(path)
    for name in ("final.jsonl", "results.jsonl"):
        f = p / name if p.is_dir() else p
        if f.exists():
            for line in open(f):
                try:
                    r = json.loads(line)
                except json.JSONDecodeError:
                    continue
                rows[r["record_id"]] = r
            break
    out = {}
    for i in ids:
        r = rows.get(i)
        if r is None:
            out[i] = "INVALID"
        elif r.get("evidence_status") == "insufficient_evidence":
            out[i] = "INSUFF"
        else:
            out[i] = r["primary_vsm"]
    return out


def kappa_stats(a, b):
    n = len(a)
    if n == 0:
        return {"n": 0}
    cats = sorted(set(a) | set(b))
    po = sum(x == y for x, y in zip(a, b)) / n
    ca, cb = Counter(a), Counter(b)
    pe = sum(ca[c] * cb[c] for c in cats) / n ** 2
    k = len(cats)
    return {"n": n, "raw": round(po, 4), "kappa": round((po - pe) / (1 - pe), 4) if pe < 1 else None,
            "pabak": round((k * po - 1) / (k - 1), 4) if k > 1 else None, "categories": k}


def shares(labels):
    allc = Counter(labels)
    suff = Counter(l for l in labels if l not in ("INSUFF", "INVALID"))
    ns = sum(suff.values())
    return {"n_all": len(labels), "n_sufficient": ns,
            "all_records": {k: round(v / len(labels), 4) for k, v in allc.most_common()},
            "sufficient_only": {k: round(v / ns, 4) for k, v in suff.most_common()} if ns else {}}


def s2_share(labels):
    suff = [l for l in labels if l not in ("INSUFF", "INVALID")]
    return sum(l == "S2_COORDINATION" for l in suff) / len(suff) if suff else float("nan")


def criteria(wl, sl):
    ws = Counter(l for l in wl if l not in ("INSUFF", "INVALID"))
    ss = Counter(l for l in sl if l not in ("INSUFF", "INVALID"))
    i = bool(ws) and ws.most_common(1)[0][0] == "S2_COORDINATION"
    ii = bool(ss) and ss["S1_OPERATIONS"] / sum(ss.values()) > 0.5
    return i, ii


def boot_gap(wiki_ids, wpage, wl_map, swarm_ids, skind, sl_map, extra=None):
    """Gap D = wiki S2 share - ST S2 share; wiki resampled by page, ST within kind. Returns (point, lo, hi)."""
    rng = random.Random(SEED)
    pages = defaultdict(list)
    for i in wiki_ids:
        pages[wpage[i]].append(i)
    plist = sorted(pages)
    strata = defaultdict(list)
    for i in swarm_ids:
        strata[skind[i]].append(i)
    point = s2_share([wl_map[i] for i in wiki_ids]) - s2_share([sl_map[i] for i in swarm_ids])
    vals = []
    for _ in range(B_N):
        w = [i for p in (rng.choice(plist) for _ in plist) for i in pages[p]]
        s = [rng.choice(v) for k in sorted(strata) for v in [strata[k]] for _ in v]
        vals.append(s2_share([wl_map[i] for i in w]) - s2_share([sl_map[i] for i in s]))
    vals = sorted(v for v in vals if v == v)   # drop NaN resamples (no sufficient records)
    n = len(vals)
    return round(point, 4), round(vals[int(0.025 * n)], 4), round(vals[max(0, int(0.975 * n) - 1)], 4)


def boot_bought(wiki_ids, wpage, base_map, arm_map):
    rng = random.Random(SEED + 1)
    pages = defaultdict(list)
    for i in wiki_ids:
        pages[wpage[i]].append(i)
    plist = sorted(pages)
    f = lambda ids: s2_share([base_map[i] for i in ids]) - s2_share([arm_map[i] for i in ids])
    vals = sorted(v for v in (f([i for p in (rng.choice(plist) for _ in plist) for i in pages[p]])
                              for _ in range(B_N)) if v == v)
    n = len(vals)
    return round(f(wiki_ids), 4), round(vals[int(0.025 * n)], 4), round(vals[max(0, int(0.975 * n) - 1)], 4)


wc = json.loads((COH / f"wiki_{SET}.json").read_text())["records"]
sc = json.loads((COH / f"swarm_{SET}.json").read_text())["records"]
wiki_ids, swarm_ids = [r["id"] for r in wc], [r["id"] for r in sc]
wpage = {r["id"]: r["episode_id"] for r in wc}
skind = {json.loads(l)["record_id"]: json.loads(l)["record_kind"] for l in open(BASE["swarm"])}
base = {"wiki": load_labels(BASE["wiki"], wiki_ids), "swarm": load_labels(BASE["swarm"], swarm_ids)}

out = {"set": SET, "n": {"wiki": len(wiki_ids), "swarm": len(swarm_ids)},
       "swarm_kind_counts": dict(Counter(skind[i] for i in swarm_ids)), "baseline_qwen_v2": {}, "arms": {}}
bi, bii = criteria([base["wiki"][i] for i in wiki_ids], [base["swarm"][i] for i in swarm_ids])
out["baseline_qwen_v2"] = {
    "shares": {c: shares([base[c][i] for i in ids]) for c, ids in (("wiki", wiki_ids), ("swarm", swarm_ids))},
    "criteria": {"i": bi, "ii": bii,
                 "gap_D": boot_gap(wiki_ids, wpage, base["wiki"], swarm_ids, skind, base["swarm"])}}

arm_labels = {}
for arm, desc in ARMS.items():
    if not all((ROOT / f"pilot_sj_{arm}_{c}_{SET}").exists() for c in ("wiki", "swarm")):
        print(f"Arm {arm}: no run directories yet, skipped")
        continue
    labs = {c: load_labels(ROOT / f"pilot_sj_{arm}_{c}_{SET}", ids)
            for c, ids in (("wiki", wiki_ids), ("swarm", swarm_ids))}
    arm_labels[arm] = labs
    res = {"description": desc, "per_corpus": {}}
    for c, ids in (("wiki", wiki_ids), ("swarm", swarm_ids)):
        a = [base[c][i] for i in ids]
        b = [labs[c][i] for i in ids]
        st = lambda l: "insufficient" if l == "INSUFF" else ("invalid" if l == "INVALID" else "sufficient")
        both = [(x, y) for x, y in zip(a, b) if x not in ("INSUFF", "INVALID") and y not in ("INSUFF", "INVALID")]
        per_label = {}
        for L in sorted({x for x, _ in both} | {y for _, y in both}):
            na, nb = sum(x == L for x, _ in both), sum(y == L for _, y in both)
            nab = sum(x == L and y == L for x, y in both)
            per_label[L] = {"qwen_v2": na, "arm": nb, "both": nab,
                            "specific_agreement": round(2 * nab / (na + nb), 4) if na + nb else None}
        res["per_corpus"][c] = {
            "overall_with_insufficient_as_label": kappa_stats(a, b),
            "evidence_status": kappa_stats([st(x) for x in a], [st(y) for y in b]),
            "primary_vsm_both_sufficient": kappa_stats([x for x, _ in both], [y for _, y in both]),
            "per_label": per_label,
            "confusion_qwen_v2_to_arm": {f"{x}->{y}": n for (x, y), n in Counter(both).most_common()},
            "shares": shares(b),
            "invalid": sum(l == "INVALID" for l in b),
            "s5_ids_for_hand_check": [i for i in ids if labs[c][i] == "S5_POLICY"],
        }
    i_, ii_ = criteria([labs["wiki"][i] for i in wiki_ids], [labs["swarm"][i] for i in swarm_ids])
    gap = boot_gap(wiki_ids, wpage, labs["wiki"], swarm_ids, skind, labs["swarm"])
    iii = gap[1] > 0.20
    res["criteria"] = {"i_wiki_S2_plurality": i_, "ii_swarm_S1_majority": ii_, "gap_D": gap,
                       "iii_gap_lower_CI_gt_20pp": iii}
    kw = res["per_corpus"]["wiki"]["overall_with_insufficient_as_label"].get("kappa") or 0
    ks = res["per_corpus"]["swarm"]["overall_with_insufficient_as_label"].get("kappa") or 0
    if arm in ("A", "Ap"):
        outcome = ("PASS" if (i_ and ii_ and iii and kw >= 0.6 and ks >= 0.6) else
                   "FAIL" if ((not (i_ and ii_ and iii)) and min(kw, ks) < 0.4) else "PARTIAL")
    else:
        res["what_the_relay_line_bought_wiki_S2"] = boot_bought(wiki_ids, wpage, base["wiki"], labs["wiki"])
        outcome = "PASS" if (i_ and ii_ and iii) else ("FAIL" if (not i_ and not iii) else "PARTIAL")
    res["outcome"] = outcome
    out["arms"][arm] = res

if "A" in arm_labels and "Ap" in arm_labels:   # pre-registered: agreement between the two new judges
    out["glm_vs_deepseek"] = {c: kappa_stats([arm_labels["A"][c][i] for i in ids], [arm_labels["Ap"][c][i] for i in ids])
                              for c, ids in (("wiki", wiki_ids), ("swarm", swarm_ids))}
    print("glm-5.2 vs deepseek-v4-flash overall:", out["glm_vs_deepseek"])

dest = ROOT / f"calibration/second_judge/results{'' if SET == 'main' else '_' + SET}.json"
dest.write_text(json.dumps(out, indent=1) + "\n")
for arm, r in out["arms"].items():
    pc = r["per_corpus"]
    print(f"Arm {arm} ({r['description']}): {r['outcome']} | criteria {r['criteria']}")
    for c in ("wiki", "swarm"):
        print(f"  {c}: overall κ {pc[c]['overall_with_insufficient_as_label'].get('kappa')} "
              f"raw {pc[c]['overall_with_insufficient_as_label'].get('raw')} | invalid {pc[c]['invalid']} | "
              f"suff shares {dict(list(pc[c]['shares']['sufficient_only'].items())[:3])}")
    if "what_the_relay_line_bought_wiki_S2" in r:
        print("  relay line bought (wiki S2, qwen v2 - arm B):", r["what_the_relay_line_bought_wiki_S2"])
print("baseline qwen v2 on sample:", out["baseline_qwen_v2"]["criteria"])
print("wrote", dest.relative_to(ROOT))
