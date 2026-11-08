# Resumable batch canary

Proof that `batch_classify_vsm.py --pilot-dir` resumes from a frozen cohort, resubmits only missing IDs, and ends with exactly one schema-valid row per ID. Pilot outputs live in `pilot_*/` (gitignored, like the legacy artifacts) and never touch `vsm_batch_output.jsonl` or `vsm_markov_summary.json`.

## Cohort

[cohort.json](cohort.json) is the frozen cohort: 48 record IDs in order, each with `episode_id` and `turn_index` as assigned by the runner (IDs and assignments only, no trace text). Episodes: `initial_payload_stream` 10, `dag:R0000027` 3, `dag:R0024455` 3, `slack-search` 4, `g23619scmd` 10, `g23619cmd` 18. The two `dag:` episodes carry parent-to-child links. Once `cohort.json` exists in a pilot directory the runner never reselects, whatever selection flags a restart passes.

## Reproduce

Run from the swarm-vsm directory.

```bash
CMD=".venv/bin/python -B batch_classify_vsm.py --pilot-dir pilot_canary --input ../redacted.jsonl --limit 48 --concurrency 8"
$CMD            # interrupt it at any point (Ctrl-C or kill -9)
$CMD            # identical command resumes; only missing IDs are submitted
.venv/bin/python -B verify_batch_output.py pilot_canary                      # final.jsonl
.venv/bin/python -B verify_batch_output.py pilot_canary --file results.jsonl # append-only store
.venv/bin/python -B tests/test_resume.py                                     # offline, fake classifier
```

Files in a pilot directory: `cohort.json` (frozen), `results.jsonl` (append-only, fsynced per result), `failures.jsonl` (failed IDs stay eligible), `run_log.jsonl` (per-run skipped and submitted IDs, per-result completion time), `final.jsonl` and `summary.json` (written only when complete).

## Restart evidence (MacBook Air, qwen3.5-397b, concurrency 8)

- Run 1 submitted 48, was killed with SIGKILL after 15 results were on disk.
- Run 2, same command: `already done 15 (skipped) | submitting 33`; wrote 33, 0 failed, 0 missing.
- `verify_batch_output.py`: 48 valid rows, 0 gaps, 0 duplicates, 0 strays, 0 completed IDs resubmitted, episode/turn unchanged. Exit 0.
- Offline tests also cover a failed ID staying eligible and a torn final write. The torn-write test found a real bug (the next append landed on the torn fragment); fixed by truncating an unterminated tail before appending.

## Throughput

Same frozen cohort, concurrency 8, no failures in either run.

| Machine | Records | Wall time | Overall rate | Mid-run rate (middle 50% of completions) |
| --- | ---: | ---: | ---: | ---: |
| 2020 Intel iMac (iMac20,1, i9-10910, Python 3.11.11), cold run | 48 | 183.5 s | 15.7 rec/min | 23.5 rec/min |
| MacBook Air, resumed portion of the canary | 33 | 296.4 s | 6.7 rec/min | 15.3 rec/min |

The machines differ by 2.3x overall, but the work is API-bound (mean time in flight is about 31 s on the iMac and about 72 s on the MacBook), so this is most likely Adaption latency varying between the runs, not hardware. Treat the range as the uncertainty.

Reproducibility: at temperature 0 the two machines' `primary_vsm` labels agreed on 45 of 48 records. Differences: R0000007 and R0062486 (S4 vs S1), R0189572 (S2 vs S4). Keep one run as the source of truth for the graphs; do not mix labels across runs.

## Proposed overnight cap

**3,000 records**, assuming:

1. An 8-hour window, concurrency 8, same model and prompt, one machine.
2. Plan on the slowest observed rate (6.7 rec/min, about 3,200 records in 8 h), so the cap completes even if latency matches the MacBook run. At the iMac's 15.7 rec/min it finishes in about 3.2 h.
3. The sample is 48 records over 3 to 5 minutes. It does not show behavior over hours: rate limits, sleep, or network drops are untested, and the canary's long g236 records may not match the length mix of the sample drawn for the overnight run.
4. The corpus has about 189k rows, so a full pass is not feasible at these rates (about 200 h at 15.7 rec/min).

If the first hour of the real run is at or above 15 rec/min, the cap can be raised on resume by regenerating a larger cohort in a new directory. Raising concurrency is untested.

The iMac has a venv at `~/swarm-vsm-canary/.venv` (Python 3.11.11, adaption 0.19.0, pydantic 2.14.3) and the runner files. No API key is stored there; the key was passed over ssh stdin for the session.
