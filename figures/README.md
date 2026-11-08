# Paper figures (fallback set)

These are made from the abstention-aware label runs so the paper isn't blocked on the transition graphs. Each figure has a PNG (300 dpi), a vector PDF, and a CSV with the same numbers.

Regenerate from the swarm-vsm directory:

```bash
.venv/bin/python -B figures/make_figures.py
```

The pilot directories are local and gitignored, so this only runs where they exist. matplotlib is installed in the venv only, not listed in `pyproject.toml`. The palette is the dataviz reference palette in light mode, and its validator passed for the two series colours.

## Figure 1: Share of records too thin to label

The share of records the judge marked `insufficient_evidence`: wiki agent text (6,051 records) and Swarm Traces (6,000, stratified by kind).

- Wiki: 8% abstain.
- Swarm Traces: 58% overall, ranging from 41% of payloads to 74% of recovered texts.

Most Swarm Traces records are fragments, encoded blobs, or loader chunks that can't be labelled on their own.

**Caption caveat:** abstention is the judge's call under one prompt per corpus. It is not a measured property of the records.

## Figure 2: Primary VSM label among records with sufficient evidence

Two series: wiki (n = 5,544) and Swarm Traces (n = 2,530). Counts under 1% are printed as n.

- Wiki is S2-dominant (58.2%).
- Swarm Traces is S1-dominant (85.5%), with S4 at 13–14% in both.

**Caption caveats:**
- The two corpora were labelled with different prompts. The wiki prompt explicitly allows status relays as S2. The contrast is suggestive, not a controlled comparison.
- Record-level S5 labels (2 in the wiki run) are judge false positives and are not evidence about S5.
- Half of Swarm Traces' 6 S3 labels look like misreads of code-submission JSON.
- The S1/S4 split is soft (see Figure 4).

## Figure 3: Wiki pages, P(next label | current label)

Transitions between adjacent turns on the same wiki page (turns in source-date order), counted only where both turns have sufficient evidence. An abstained turn breaks the chain rather than being skipped. That gives 4,324 transitions.

**Rows and columns:** only labels with at least 30 outgoing transitions are shown. S3* (18), S5 (2) and S3 (1) are omitted, so a few rows sum to slightly under 1. Full counts are in the CSV.

**Reading:**
- S2 is strongly self-persistent (0.87).
- S1 and S4 flow into S2 about a quarter and a fifth of the time.
- S0 rarely persists.

**Caption caveats:**
- Turn order is the date order of the published records on a page. It is not observed agent-to-agent interaction.
- The 50-record cap per page truncates the longest pages.
- No S3 rows exist to show an S2 → S3 step. This figure does not test the Figure 1 phase sequence (S1 → S2 → S3).

**Swarm Traces has no transition figure.** It has no time order (IDs are undocumented, `time_utc` is empty), and its parent links are a payload's own layers and replies, not steps in time.

## Figure 4: Wiki label stability between runs

For records judged sufficient in v2: the share of each v1 (forced-choice) label that got each v2 label. Rows have at least 30 records; S3 (2) and S5 (1) are omitted.

**Reading:**
- S2 is stable (0.91).
- S1 (0.70) and S4 (0.66) exchange labels in both directions.
- S3* is unstable (0.42).

**Use this as the method caveat for any S1/S4 share.**
