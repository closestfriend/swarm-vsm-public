# Judge and prompt robustness

This release adds the second-judge study used in paper section 4.5. It contains frozen sample IDs and page/episode metadata, prompts, scripts and aggregate results. It contains no record text or model rationales.

## Results

Each arm uses 1,000 wiki records and 1,000 Swarm Traces records. The gap is wiki S2 share minus Swarm Traces S2 share, among records each condition judged sufficient. Kappa treats insufficient evidence as a label.

| Arm | Judge and prompt | Registered outcome | Kappa vs Qwen v2, wiki / Swarm Traces | Gap in percentage points, 95% CI |
| --- | --- | --- | --- | --- |
| A | GLM 5.2, corpus-specific v2 | PASS | 0.61 / 0.66 | 54.5 (48.4 to 60.0) |
| A-prime | DeepSeek v4 Flash, corpus-specific v2 | PASS | 0.61 / 0.75 | 57.9 (51.4 to 63.5) |
| B | Qwen 3.5 397B, shared prompt | PARTIAL | 0.50 / 0.82 | 38.3 (34.0 to 42.5) |

Under the shared prompt, wiki S2 is 38.5% and S1 is 46.1%. Swarm Traces retains an S1 majority (86.6%). The wiki S2 share falls by 21.9 percentage points (95% CI 18.6 to 25.1) relative to Qwen v2 on the same sample.

This is a comparison of prompt conditions, not an isolated relay-rule ablation. The shared prompt also merges corpus descriptions and examples. The historical key `what_the_relay_line_bought_wiki_S2` and wording in the preregistration are preserved for provenance; they should not be read as identifying the causal effect of that line alone. The optional B-prime arm was not included in the reported results.

These results measure agreement between models and sensitivity to prompts. They do not establish agreement with human ground truth, and PASS refers only to the preregistered criteria.

## Provenance

`PREREG.md` is unchanged from private research commit `cac6ced896586d44a1abe094ebfb5ea3bfdb6c2c`. The exported files come from `3553399b1ae9581f12e6b4e2e02c11a27ff59b4c`. `provenance.json` records source and released SHA-256 hashes and all export changes. Cohort metadata's absolute workstation paths are reduced to basenames; record IDs, order, episode IDs and turn indices are unchanged. The launchers use explicit local input paths and propagate worker failures. The historical analysis and sample-selection scripts are otherwise unchanged.

The private commit IDs identify the authors' history; public readers cannot access that repository. The public release's preregistration file alone cannot independently establish its pre-run timing.

## Reproduction and missing inputs

The frozen `cohorts/` files can be used directly with `batch_classify_vsm.py --cohort-from`. Download the source corpora separately and configure your own environment and Adaption account before making paid model calls. From the repository root, the launchers require `WIKI_IN`, `SWARM_IN`, and optionally `PY` (default `.venv/bin/python`) and `CONC`. Their argument must be `canary` or `main`. No model calls were made while preparing this release.

`make_samples.py` needs the original local `pilot_wiki_abstain/cohort.json`, `pilot_swarm_abstain/cohort.json` and `pilot_swarm_abstain/final.jsonl`. `analyze.py` additionally needs the local baseline and arm results under the `pilot_*` directories described in its source. These contain text or rationales and are intentionally not released. Consequently this checkout supports inspection of the selection and analysis code, and fresh runs using the frozen cohorts, but cannot independently recompute the historical result from published aggregates alone.

Do not publish `pilot_*` outputs or log files: they can contain corpus-derived text or model rationales.
