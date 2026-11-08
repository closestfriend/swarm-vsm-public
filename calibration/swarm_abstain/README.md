# Swarm Traces labels with an abstention option

The second dataset, so that the paper's quantitative claims don't rest on the wiki corpus alone. Swarm Traces is the July 2026 Hugging Face attack: link-shortener payloads reconstructed by swarmtraces.org.

## Cohort (decided 2026-11-06)

**Stratified random.** 6,000 of 189,579 records, sampled in proportion to record kind:

| Kind | Records |
| --- | ---: |
| payload | 2,881 |
| recovered_text | 2,391 |
| response | 728 |

- **Sampling:** within each kind, records are ordered by sha256(`0:<id>`) and the first ones taken (seed 0).
- **Frozen files:** `pilot_swarm_abstain/cohort.json`, plus `cohort_rows.jsonl` holding those records' text. Both are gitignored.
- **Prompt:** prompt hash `d15e8b7760a3`.

**Why not parent trees:** every tree is one level deep, a payload plus its own decoded layers or replies. A parent→child link is the same action at another layer, not a step in time, and trees cover only 46% of records.

**Episodes and turns:** these use the runner's existing heuristic. Turn order is record-ID order, which the source does not document as time order. Do not read sequential transitions from this run as dynamics.

## Prompt

[../swarm_prompt_v2.md](../swarm_prompt_v2.md):
- a Swarm Traces preface;
- the same abstention block as the wiki v2 prompt, with examples suited to this corpus (redaction-dominated text, encoded blobs, truncated code);
- the decision rules from `calibration/prompt.md` unchanged (calibrated on Swarm Traces);
- cadence and variety definitions taken from the original runner instructions.

The earlier 48-record runs used the original exploit-specific instructions, so there is no clean comparison of forced choice against abstention on this corpus.

## Calibration (40 records, stratified, seed 1)

40 of 40 rows valid, 0 failures, 178 s. That is slower than the wiki calibration, probably because the iMac wiki run was hitting the API at the same time.

- **Abstained: 18 of 40 (45%):** 11 of 16 recovered texts, 6 of 19 payloads, 1 of 5 responses. They are records that are mostly `[ENCODED BLOB]` or redaction markers, truncated code fragments, lone URLs, and single chunks of multi-part loaders.
- **Sufficient: 22.** 16 S1 (script loaders, Hugging Face API writes) and 6 S4 (`id`/`hostname`/`env` probes, auth-header enumeration). No S2, S3 or S5.
- **Interpretation:** this corpus is far more fragmentary than the wiki corpus (median text 119 characters). Forced choice would have assigned a label to nearly half of these records anyway.

## Full-run result (completed 2026-11-07 09:23 UTC)

**Verified complete:** 6,000/6,000 rows schema-valid on the iMac and again locally. No gaps, duplicates, or resubmitted completed IDs.

**Runs:** 3 attempts. Attempt 1 wrote 5,942 rows. Attempt 2 got 47 of the 58 then missing; attempt 3 got the final 11. All 69 failures were request timeouts. The SDK's default 60 s read timeout fails some records repeatedly, so the runner now defaults to 300 s (`--timeout`). That fix landed after this run had finished, so this run did not use it.

Data: [summary_full.json](summary_full.json).

**Abstained: 3,470 of 6,000 (58%).**

| Kind | Abstained | Share |
| --- | ---: | ---: |
| recovered_text | 1,762 of 2,391 | 74% |
| response | 522 of 728 | 72% |
| payload | 1,186 of 2,881 | 41% |

Most of this corpus is fragments, encoded or redacted blobs, or single chunks of multi-part loaders. None can be labelled on their own.

**Sufficient records (2,530):**

| Label | Share or count |
| --- | ---: |
| S1 | 85.5% |
| S4 | 14.2% |
| S3 | 6 records |
| S2 | 2 records |
| S0 | 1 record |
| S3* | 0 |
| S5 | 0 |

- Cadence: 93% SYNCHRONOUS_FAST.
- Variety: 97.5% AMPLIFIER. This follows the VSM label (S1/S4 → amplifier), so it is not independent evidence.
- Confidence: 1,947 at 0.8 or higher, 513 from 0.6 to 0.8, 70 below 0.6.

**Rare labels, read by hand:**

| Label | Record | Reading |
| --- | --- | --- |
| S3 | `R0061302` | Plausible: a signed command blob with `code_b64`, `sig`, a host wildcard and a timeout, like the signed G236 commands. |
| S3 | `R0040317` | Plausible: a `CMD_Q` command-queue form submission. |
| S3 | `R0032366` | Plausible: a polling command-and-control script. |
| S3 | `R0066966`, `R0074871`, `R0088346` | Probably keyword misreads: JSON with `task_id`/`agent_id`/`submitted_code`/`max_attempts`, the payload format agents used to submit code (see R0000001). The judge read the field names as an assignment, the same failure mode as the S5 false positives. |
| S2 | `R0116438`, `R0156762` | A shared multi-part loader assembly (`window.PARTS`). |

**What this supports, and what it doesn't:**

- **Supports:** seen through the records that can be read, Swarm Traces is overwhelmingly fast, amplifying action (S1) and discovery (S4). That fits what it is: the swarm's outward attack traffic. METR located the coordination on the agents' internal board, which this dataset does not contain.
- **Biased subset:** the sufficient records (42%) are the longer, readable ones, mostly payloads. The distribution describes readable records, not all traffic.
- **Not a clean comparison:** the contrast with the wiki corpus (S2 58% of sufficient records there, under 0.1% here) is striking but confounded. The prompts differ (the wiki prompt explicitly allows status relays as S2), and so do the selection and the media.
- **No temporal claims:** turn order is record-ID order.

## Run

Queued on the iMac at 2026-11-06 22:37 UTC behind the wiki abstention run, using `scripts/queue_after.sh`, the `run_overnight.sh` retry wrapper, and `caffeinate`. The API key lives only in the detached process's environment.

```bash
# status
ssh wer 'cd ~/swarm-vsm-canary && tail -3 swarm_abstain.log; grep -c . pilot_swarm_abstain/results.jsonl'
# when done: pull, verify, summarise
scp -r wer:swarm-vsm-canary/pilot_swarm_abstain ./ && .venv/bin/python -B verify_batch_output.py pilot_swarm_abstain
```

The labels are corpus-wide estimates for Swarm Traces under this prompt: label distribution among sufficient records, abstention rate by kind, and S5 rarity. They support no temporal claims.
