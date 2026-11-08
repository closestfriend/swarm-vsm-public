"""Convention convergence test for the wiki corpus (see PREREG.md).

For each token: spread, and the exposed share of authors' first adoptions versus a null that
shuffles record dates within each page. Writes results.json next to this file.

Run from the swarm-vsm directory:
  .venv/bin/python -B calibration/convergence/convergence.py \
      --records ../records.jsonl.gz --labels pilot_wiki_overnight/final.jsonl
"""
import argparse
import json
import random
import re
import statistics as st
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from batch_classify_vsm import load_wiki_records  # noqa: E402

HERE = Path(__file__).resolve().parent
I = re.IGNORECASE
TOKENS = {
    # family, regex (pre-registered)
    "round_marker": ("env_possible", re.compile(r"\bR[1-9]\b")),
    "timer": ("env_possible", re.compile(r"\btimer\b", I)),
    "deadline": ("env_possible", re.compile(r"\bdeadline\b", I)),
    "cooldown": ("env_possible", re.compile(r"\bcooldown\b", I)),
    "confirmed": ("protocol_S2", re.compile(r"\bconfirmed\b", I)),
    "relay": ("protocol_S2", re.compile(r"\brelay", I)),
    "signal": ("protocol_S2", re.compile(r"\bsignal", I)),
    "ping": ("protocol_S2", re.compile(r"\bping\b", I)),
    "ETA": ("protocol_S2", re.compile(r"\bETA\b")),
    "task_clock": ("protocol_S2", re.compile(r"\btask[- ]clock\b", I)),
    "cohort": ("identity_S5", re.compile(r"\bcohort", I)),
    "collective_peer_swarm": ("identity_S5", re.compile(r"\b(collective|peers?|swarm)\b", I)),
    "oai_self_name": ("identity_S5", re.compile(r"\b(?:OpenAI|OAI)[A-Za-z0-9]+\b|\b[A-Za-z0-9]+OAI\b")),
    "signature": ("identity_S5", re.compile(r"--\s*[A-Z][A-Za-z0-9]{2,}\s*$")),
    "hold_veto_stop": ("governance", re.compile(r"\b(HOLD|VETO|STOP)\b")),
    "must_never_rule": ("governance", re.compile(r"\b(must|never|rule)\b", I)),
    "we_our_us": ("context_only", re.compile(r"\b(we|our|us)\b", I)),
}
MIN_AUTHORS = 20


def exposure(order, recs, has):
    """order: record indices in time order. Returns (adoptions, exposed) for one token."""
    pos = {r: i for i, r in enumerate(order)}
    page_first = {}
    for r in order:
        if has[r] and recs[r]["page"] not in page_first:
            page_first[recs[r]["page"]] = pos[r]
    adopted, author_exposed = set(), set()
    n_adopt = n_exp = 0
    for i, r in enumerate(order):
        a, p = recs[r]["author"], recs[r]["page"]
        if a is None:
            continue
        page_prior = page_first.get(p, 10**9) < i
        if has[r] and a not in adopted:
            adopted.add(a)
            n_adopt += 1
            if page_prior or a in author_exposed:
                n_exp += 1
        if page_prior:
            author_exposed.add(a)
    return n_adopt, n_exp


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--records", type=Path, required=True)
    ap.add_argument("--labels", type=Path, required=True)
    ap.add_argument("--perms", type=int, default=500)
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()

    raw = load_wiki_records(a.records)
    recs = []
    for line in a.labels.read_text(encoding="utf-8").splitlines():
        ann = json.loads(line)
        r = raw[ann["record_id"]]
        author = ann["source_agent_id"]
        recs.append({
            "id": r["id"], "page": r["source_id"], "date": r["date"], "text": r["text"].strip(),
            "author": None if author == "unresolved" else author,
        })
    n = len(recs)
    order = sorted(range(n), key=lambda i: (recs[i]["date"], recs[i]["id"]))
    by_page = defaultdict(list)
    for i, r in enumerate(recs):
        by_page[r["page"]].append(i)

    rng = random.Random(a.seed)
    null_orders = []
    for _ in range(a.perms):
        new_date = {}
        for idxs in by_page.values():
            dates = [recs[i]["date"] for i in idxs]
            rng.shuffle(dates)
            new_date.update(zip(idxs, dates))
        null_orders.append(sorted(range(n), key=lambda i: (new_date[i], rng.random())))

    out = {"n_records": n, "n_resolved_author_records": sum(r["author"] is not None for r in recs),
           "n_authors": len({r["author"] for r in recs if r["author"]}), "perms": a.perms,
           "seed": a.seed, "tokens": {}}
    for name, (family, rx) in TOKENS.items():
        has = [bool(rx.search(r["text"])) for r in recs]
        idx = [i for i in range(n) if has[i]]
        first = min((recs[i]["date"] for i in idx), default=None)
        n_adopt, n_exp = exposure(order, recs, has)
        obs = n_exp / n_adopt if n_adopt else None
        nulls = []
        if n_adopt:
            for o in null_orders:
                na, ne = exposure(o, recs, has)
                nulls.append(ne / na if na else 0.0)
        res = {
            "family": family, "records": len(idx), "pages": len({recs[i]["page"] for i in idx}),
            "adopting_authors": n_adopt, "first_seen": first[:7] if first else None,
            "exposed_share": round(obs, 3) if obs is not None else None,
        }
        if nulls:
            res.update(null_mean=round(st.mean(nulls), 3), lift=round(obs - st.mean(nulls), 3),
                       p_one_sided=round(sum(x >= obs for x in nulls) / len(nulls), 4),
                       unexposed_adopters=n_adopt - n_exp,
                       interpreted=n_adopt >= MIN_AUTHORS and family not in ("context_only",))
        out["tokens"][name] = res
    (HERE / "results.json").write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(f"records {n}, with resolved author {out['n_resolved_author_records']}, authors {out['n_authors']}")
    print(f"{'token':24} {'family':13} {'recs':>5} {'pages':>5} {'auth':>5} {'first':>7} "
          f"{'exp':>6} {'null':>6} {'lift':>6} {'p':>7}")
    for k, v in out["tokens"].items():
        print(f"{k:24} {v['family']:13} {v['records']:5} {v['pages']:5} {v['adopting_authors']:5} "
              f"{str(v['first_seen']):>7} {str(v['exposed_share']):>6} {str(v.get('null_mean')):>6} "
              f"{str(v.get('lift')):>6} {str(v.get('p_one_sided')):>7}")


if __name__ == "__main__":
    main()
