"""Paper figures from the abstention-aware label runs (fallback for the transition graphs).

Static figures for the PDF: PNG (300 dpi) + vector PDF + a CSV table twin for each.
Palette and mark rules follow the dataviz reference palette (light mode); the two series
colours were checked with its validator (all checks pass).

Inputs (local, gitignored): pilot_wiki_overnight/, pilot_wiki_abstain/, pilot_swarm_abstain/.
Run from the swarm-vsm directory:
  .venv/bin/python -B figures/make_figures.py
"""
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent

# Reference palette (light)
SURFACE, INK, INK2, MUTED = "#fcfcfb", "#0b0b0b", "#52514e", "#898781"
GRID, BASE = "#e1e0d9", "#c3c2b7"
SLOT1, SLOT2 = "#2a78d6", "#eb6834"  # wiki, Swarm Traces
SEQ = ["#cde2fb", "#b7d3f6", "#9ec5f4", "#86b6ef", "#6da7ec", "#5598e7", "#3987e5",
       "#2a78d6", "#256abf", "#1c5cab", "#184f95", "#104281", "#0d366b"]
BLUES = LinearSegmentedColormap.from_list("ref_blue", SEQ)

LABELS = ["S0_NOISE", "S1_OPERATIONS", "S2_COORDINATION", "S3_CONTROL",
          "S3_STAR_AUDIT", "S4_INTELLIGENCE", "S5_POLICY"]
SHORT = {"S0_NOISE": "S0 noise", "S1_OPERATIONS": "S1 operations", "S2_COORDINATION": "S2 coordination",
         "S3_CONTROL": "S3 control", "S3_STAR_AUDIT": "S3* audit", "S4_INTELLIGENCE": "S4 intelligence",
         "S5_POLICY": "S5 policy"}

plt.rcParams.update({
    "font.family": "sans-serif", "font.sans-serif": ["Helvetica", "Arial", "DejaVu Sans"],
    "font.size": 9, "axes.edgecolor": BASE, "axes.linewidth": 0.6, "axes.labelcolor": INK2,
    "xtick.color": MUTED, "ytick.color": INK2, "xtick.major.width": 0.6, "ytick.major.size": 0,
    "axes.facecolor": SURFACE, "figure.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "axes.titlesize": 10, "axes.titleweight": "bold", "axes.titlecolor": INK, "axes.titlelocation": "left",
})


def load(p):
    return [json.loads(line) for line in (ROOT / p).read_text().splitlines() if line.strip()]


def save(fig, name, header, rows):
    for ext in ("png", "pdf"):
        fig.savefig(OUT / f"{name}.{ext}", dpi=300, bbox_inches="tight")
    plt.close(fig)
    with open(OUT / f"{name}.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


def style_axis(ax, grid_axis="x"):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.grid(axis=grid_axis, color=GRID, linewidth=0.5)
    ax.set_axisbelow(True)


def main():
    wiki = load("pilot_wiki_abstain/final.jsonl")
    wiki_v1 = {a["record_id"]: a for a in load("pilot_wiki_overnight/final.jsonl")}
    st = load("pilot_swarm_abstain/final.jsonl")
    kind = {}
    for line in (ROOT / "pilot_swarm_abstain/cohort_rows.jsonl").read_text().splitlines():
        r = json.loads(line)
        kind[r["id"]] = r["kind"]

    # ---- Figure 1: abstention rate by record group (one series -> one colour)
    groups = [("Wiki agent text (all)", wiki)]
    for k, lab in (("payload", "payload"), ("response", "response"), ("recovered_text", "recovered text")):
        groups.append((f"Swarm Traces: {lab}", [a for a in st if kind[a["record_id"]] == k]))
    groups.append(("Swarm Traces (all)", st))
    rows = []
    for name, recs in groups:
        ab = sum(a["evidence_status"] == "insufficient_evidence" for a in recs)
        rows.append((name, len(recs), ab, round(100 * ab / len(recs), 1)))
    fig, ax = plt.subplots(figsize=(6.2, 2.5))
    names = [r[0] for r in rows][::-1]
    vals = [r[3] for r in rows][::-1]
    ax.barh(names, vals, color=SLOT1, height=0.55)
    for y, (v, r) in enumerate(zip(vals, rows[::-1])):
        ax.text(v + 1.2, y, f"{v:.0f}%  ({r[2]:,} of {r[1]:,})", va="center", color=INK2, fontsize=8)
    ax.set_xlim(0, 100)
    ax.set_xlabel("Records the judge marked insufficient_evidence (%)")
    ax.set_title("Share of records too thin to label")
    style_axis(ax)
    save(fig, "fig1_abstention", ["group", "records", "abstained", "abstained_pct"], rows)

    # ---- Figure 2: label distribution among sufficient records, two datasets
    def dist(recs):
        s = [a for a in recs if a["evidence_status"] == "sufficient"]
        c = Counter(a["primary_vsm"] for a in s)
        return {lab: (c.get(lab, 0), 100 * c.get(lab, 0) / len(s)) for lab in LABELS}, len(s)

    dw, nw = dist(wiki)
    ds, ns = dist(st)
    fig, ax = plt.subplots(figsize=(6.2, 3.4))
    ys = list(range(len(LABELS)))[::-1]
    h = 0.36
    ax.barh([y + h / 2 + 0.02 for y in ys], [dw[l][1] for l in LABELS], height=h, color=SLOT1,
            label=f"Wiki agent text (n = {nw:,} sufficient)")
    ax.barh([y - h / 2 - 0.02 for y in ys], [ds[l][1] for l in LABELS], height=h, color=SLOT2,
            label=f"Swarm Traces (n = {ns:,} sufficient)")
    for y, lab in zip(ys, LABELS):
        for off, (cnt, pct) in ((h / 2 + 0.02, dw[lab]), (-h / 2 - 0.02, ds[lab])):
            txt = f"{pct:.1f}%" if pct >= 1 else (f"n = {cnt}" if cnt else "0")
            ax.text(pct + 1, y + off, txt, va="center", color=INK2, fontsize=7.5)
    ax.set_yticks(ys)
    ax.set_yticklabels([SHORT[l] for l in LABELS])
    ax.set_xlim(0, 100)
    ax.set_xlabel("Share of records with sufficient evidence (%)")
    ax.set_title("Primary VSM label, records with sufficient evidence")
    ax.legend(frameon=False, loc="lower right", fontsize=8)
    style_axis(ax)
    save(fig, "fig2_label_distribution", ["label", "wiki_n", "wiki_pct", "swarm_n", "swarm_pct"],
         [(l, dw[l][0], round(dw[l][1], 2), ds[l][0], round(ds[l][1], 2)) for l in LABELS])

    # ---- Figure 3: wiki within-page transitions between adjacent sufficient turns
    by_page = defaultdict(list)
    for a in wiki:
        by_page[a["episode_id"]].append(a)
    trans = Counter()
    for turns in by_page.values():
        turns.sort(key=lambda a: a["turn_index"])
        for x, y in zip(turns, turns[1:]):
            if y["turn_index"] == x["turn_index"] + 1 and \
                    x["evidence_status"] == y["evidence_status"] == "sufficient":
                trans[(x["primary_vsm"], y["primary_vsm"])] += 1
    out_n = Counter()
    for (s, _), n in trans.items():
        out_n[s] += n
    states = [l for l in LABELS if out_n[l] >= 30]  # rows with enough transitions to estimate
    cols = states
    mat = [[trans[(r, c)] / out_n[r] if out_n[r] else 0 for c in cols] for r in states]
    fig, ax = plt.subplots(figsize=(4.8, 3.9))
    im = ax.imshow(mat, cmap=BLUES, vmin=0, vmax=1)
    for i, r in enumerate(states):
        for j, c in enumerate(cols):
            p = mat[i][j]
            if p >= 0.05:
                ax.text(j, i, f"{p:.2f}", ha="center", va="center", fontsize=8,
                        color="#ffffff" if p >= 0.5 else INK)
    ax.set_xticks(range(len(cols)))
    ax.set_xticklabels([SHORT[c] for c in cols], rotation=30, ha="right")
    ax.set_yticks(range(len(states)))
    ax.set_yticklabels([f"{SHORT[r]}  (n = {out_n[r]:,})" for r in states])
    ax.set_xlabel("Next turn on the same page")
    ax.set_ylabel("Current turn")
    ax.set_title("Wiki pages: P(next label | current label)")
    for s in ax.spines.values():
        s.set_visible(False)
    ax.tick_params(axis="x", colors=INK2, length=0)
    cb = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cb.outline.set_visible(False)
    cb.ax.tick_params(colors=MUTED, length=0)
    dropped = {l: out_n[l] for l in LABELS if 0 < out_n[l] < 30}
    save(fig, "fig3_wiki_transitions", ["current", "next", "count", "p_next_given_current"],
         [(r, c, trans[(r, c)], round(trans[(r, c)] / out_n[r], 4)) for r in LABELS for c in LABELS
          if out_n[r] and trans[(r, c)]])

    # ---- Figure 4: wiki label stability, v1 forced choice -> v2 (v2-sufficient records)
    suff = [a for a in wiki if a["evidence_status"] == "sufficient"]
    pair = Counter((wiki_v1[a["record_id"]]["primary_vsm"], a["primary_vsm"]) for a in suff)
    v1n = Counter(wiki_v1[a["record_id"]]["primary_vsm"] for a in suff)
    rs = [l for l in LABELS if v1n[l] >= 30]
    m4 = [[pair[(r, c)] / v1n[r] for c in rs] for r in rs]
    fig, ax = plt.subplots(figsize=(4.8, 3.9))
    im = ax.imshow(m4, cmap=BLUES, vmin=0, vmax=1)
    for i in range(len(rs)):
        for j in range(len(rs)):
            p = m4[i][j]
            if p >= 0.05:
                ax.text(j, i, f"{p:.2f}", ha="center", va="center", fontsize=8,
                        color="#ffffff" if p >= 0.5 else INK)
    ax.set_xticks(range(len(rs)))
    ax.set_xticklabels([SHORT[c] for c in rs], rotation=30, ha="right")
    ax.set_yticks(range(len(rs)))
    ax.set_yticklabels([f"{SHORT[r]}  (n = {v1n[r]:,})" for r in rs])
    ax.set_xlabel("Label with abstention option (v2)")
    ax.set_ylabel("Forced-choice label (v1)")
    ax.set_title("Wiki: label retention, forced-choice vs abstention prompt")
    for s in ax.spines.values():
        s.set_visible(False)
    ax.tick_params(axis="x", colors=INK2, length=0)
    cb = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cb.outline.set_visible(False)
    cb.ax.tick_params(colors=MUTED, length=0)
    save(fig, "fig4_wiki_label_stability", ["v1_label", "v2_label", "count", "share_of_v1_label"],
         [(r, c, pair[(r, c)], round(pair[(r, c)] / v1n[r], 4)) for r in LABELS for c in LABELS
          if v1n[r] and pair[(r, c)]])

    meta = {"fig3_rows_dropped_under_30_transitions": dropped,
            "fig3_transitions_total": sum(trans.values()),
            "fig4_rows_dropped_under_30": {l: v1n[l] for l in LABELS if 0 < v1n[l] < 30},
            "wiki_sufficient": nw, "swarm_sufficient": ns}
    (OUT / "figures_meta.json").write_text(json.dumps(meta, indent=2) + "\n")
    print(json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()
