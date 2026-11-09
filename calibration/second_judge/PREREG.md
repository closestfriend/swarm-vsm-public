# Pre-registration: judge dependence and prompt confound

Written and committed before any API call for this study (2026-11-08). Design reviewed by the cybernetic-analyst session (fixes J1–J4 applied). All results are reported whatever they show. This tests whether our labels depend on the judge or the prompt; it does not validate them against human ground truth.

## Question

The paper's corpus labels come from one judge (`qwen3.5-397b`) under corpus-specific prompts. The two v2 prompts share identical decision rules; the wiki prompt adds an "Applying the rules to wiki text" section whose first line lets status relays, requests to report a value and schedule handoffs count as S2. We ask:

- **A (judge dependence):** does a second judge from a different model family reproduce the labels and the headline pattern?
- **B (prompt confound):** does the wiki-versus-Swarm-Traces contrast survive one shared prompt without the wiki S2 relay line?

## Samples (IDs only; `make_samples.py`, committed)

- **Wiki:** 1,000 records, simple random by `sha256("sj1:" + id)` from the 6,051-record v2 cohort.
- **Swarm Traces:** 1,000 records, proportional to kind by largest remainder. The cohort has payload 2,881, recovered_text 2,391 and response 728, giving quotas of 480 / 399 / 121. Within each kind, records are taken in `sha256("sj1:" + id)` order.
- **Canaries:** the next 10 records of each corpus in the same order (Swarm Traces: 4 / 4 / 2 by kind), outside the main samples. They check schema validity only and are excluded from all results.

## Arms

| Arm | Judge | Prompt | File SHA-256 |
| --- | --- | --- | --- |
| A | `glm-5.2` | unchanged v2 prompts: `calibration/wiki_prompt_v2.md` (wiki), `calibration/swarm_prompt_v2.md` (Swarm Traces) | `13b54f47…62cd` / `ed66b3a2…df15` |
| B | `qwen3.5-397b` | one shared prompt for both corpora: `calibration/second_judge/shared_prompt.md` | `23cc3c22…2f84` |
| B′ (optional) | `qwen3.5-397b` | shared prompt plus the wiki S2 relay line, on both corpora | written before running, if run |
| A′ (optional) | `deepseek-v4-flash` | unchanged v2 prompts | — |

**Shared prompt (B).** It has the same decision rules, abstention instructions and S5 rule as v2, with no level instruction. It merges the corpus descriptions neutrally, saying what each source and `record_kind` is without characterising the agents' activity. The abstention examples, identity text and cadence text are merged into one list each. It keeps the wiki prompt's S3 line, S1 default and S0 lines in corpus-neutral form. It drops only the S2 relay line ("A message posted for other agents to read and answer on a shared page … can qualify as S2_COORDINATION").

**Fixed settings.** Temperature 0. The same 2,400-character truncation and Pydantic schema as v2, with abstention on. Up to 3 attempts per call (runner default), then one rerun pass over failures. Records still failing are counted as **INVALID** in every denominator, never dropped. Model strings, prompt hashes and run logs are kept in each run directory. The optional arms run only if credits remain after A and B, and are reported if run.

## Comparisons

Every arm is compared with Qwen v2 labels on the same IDs (existing runs).

## Metrics (`analyze.py`)

Per corpus and arm, against Qwen v2:

1. **Overall agreement,** with `insufficient_evidence` and INVALID as labels: Cohen's κ, raw agreement, PABAK.
2. **`evidence_status` agreement:** κ, raw agreement, PABAK.
3. **`primary_vsm` agreement among records both judges call sufficient:** κ, raw agreement, per-label agreement, confusion matrix.
4. **Label shares** over two denominators: sufficient-only, and all records (with insufficient and INVALID as categories).
5. **Gap D** = wiki S2 share minus Swarm Traces S2 share (sufficient-only), with a bootstrap 95% CI: 2,000 resamples, seed 0. Wiki records are resampled by **page** (`episode_id`, clustered); Swarm Traces records are resampled within kind strata.
6. **Reported quantity, "what the S2 relay line bought":** wiki S2 share (sufficient-only) under Qwen v2 minus under arm B, on the same 1,000 IDs, with a page-bootstrap CI.

**Kappa bands (conventional):** ≥ 0.6 substantial, 0.4–0.6 moderate, < 0.4 weak.

**S5 hand-check.** Every `S5_POLICY` label from a new run is checked by hand against the Tier-1 four-function criterion (identity, whole over part, succession, binding policy). Checker and verdict are logged per record. Record labels are never counted as evidence about S5.

## Decision criteria (applied to arms A and B separately)

- (i) Wiki S2 is the plurality label among sufficient wiki records.
- (ii) Swarm Traces S1 is the majority label among sufficient Swarm Traces records.
- (iii) The lower bound of the 95% CI of gap D is above 20 percentage points.

### Arm A outcome and the paper sentence we will use

- **PASS:** (i)–(iii) hold, and overall κ ≥ 0.6 in both corpora.
  > "A second judge from a different model family (glm-5.2) reproduced the headline pattern (wiki S2 plurality, Swarm Traces S1 majority, S2-share gap above 20 points) with substantial record-level agreement (overall κ = [wiki], [Swarm Traces])."
- **FAIL:** any of (i)–(iii) fails, and overall κ < 0.4 in at least one corpus.
  > "A second judge (glm-5.2) did not reproduce the headline pattern and agreed weakly with qwen3.5-397b (overall κ = [wiki], [Swarm Traces]); the corpus profiles in §4.2 are one model's reading and should be treated as judge-dependent."
- **PARTIAL:** every other case.
  > "A second judge (glm-5.2) [reproduced / did not reproduce] the corpus-level pattern ([which of (i)–(iii) held]) with [moderate / substantial / weak] record-level agreement (overall κ = [wiki], [Swarm Traces]); record-level labels are partly judge-dependent."

### Arm B outcome and the paper sentence we will use

- **PASS:** (i)–(iii) hold under the shared prompt.
  > "Under one shared prompt without the wiki-only S2 relay line, wiki S2 remained the plurality label and the S2-share gap stayed above 20 points (95% CI lower bound [x]); the relay line accounted for [y] points of wiki S2."
- **FAIL:** (i) fails and (iii) fails.
  > "Without the wiki-only S2 relay line, wiki S2 dominance did not hold (gap 95% CI lower bound [x]); the coordination-versus-action contrast in §4.2 depends on corpus-specific prompting."
- **PARTIAL:** every other case.
  > "Under one shared prompt, the contrast weakened: [which of (i)–(iii) held]; the relay line accounted for [y] points of wiki S2, so the size of the contrast is prompt-sensitive."

Whatever the outcome, the paper keeps "blinded multi-human spot check" in next steps and does not use the word "validated".
