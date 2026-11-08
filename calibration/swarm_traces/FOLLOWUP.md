# Follow-up: separate dispatch and work judgments

The first run ([README](README.md), [results.json](results.json), unchanged) recovered both dispatches but moved both positives' work label from S4 to S3_CONTROL. This follow-up tests whether a schema that judges dispatch and work separately, each with its own verbatim evidence span, fixes that.

## What changed, and what did not

- **Same:** four records, frozen window inputs (identical manifest hash `aeef428c496c`, enforced by the script), 2,400-character budget per record shared by both judgments, Adaption `qwen3.5-397b`, temperature 0.
- **Changed:** schema and prompt together ([judge_v2.py](judge_v2.py)). `dispatch` carries a `launcher_span`. `work` carries a `function` (any VSM label or `insufficient_evidence`), a `worker_task`, and a `worker_span`. The prompt says the act of launching must not set the work function, and that for dispatched code the worker's own code is classified. Schema and wording changed in one step, so this run cannot say which of the two did the work.
- **Output:** [results_v2.json](results_v2.json), separate from the original results. One attempt per record (no retries were needed).
- **Scoring:** a span counts only if it appears verbatim in the supplied window. A positive's launcher span must also overlap the manually verified call in `dispatch_links.jsonl`, and its worker span must fall inside the worker program. A work-label abstention counts as a miss. There were none.

## Before and after (window condition)

| Record | Role | Before: dispatch / work | After: dispatch / work |
| --- | --- | --- | --- |
| R0189558 | positive | yes / S3_CONTROL | **yes / S4** |
| R0189562 | positive | yes / S3_CONTROL | **yes / S4** |
| R0189553 | control | no / S4 | **no / S4** |
| R0189569 | control | no / S4 | **no / S4** |

Actor identity: `unresolved` in all four. Work-label abstentions: 0.

## Evidence offsets

Zero-based source character offsets in the decoded record text, exclusive end. Offsets are recovered from where each quote sits in the supplied window.

| Record | Launcher span | Verified call (dispatch_links.jsonl) | Worker span | Worker program region |
| --- | --- | --- | --- | --- |
| R0189558 | 4704-4754 | 4708-4754 | 3834-3951 | 1319-4267 |
| R0189562 | 4390-4495 | 4396-4442 | 3944-4118 | 1372-4284 |
| R0189553 | none (dispatch = no) | n/a | 211-398 | direct code |
| R0189569 | none (dispatch = no) | n/a | 419-485 | direct code |

Judge's worker task: R0189558 "Reconnaissance of Kubernetes cluster resources"; R0189562 "Probing internal APIs for system version and repository lists using derived credentials"; controls "enumerate cluster resources" and "port scanning connectivity check".

## Gate: PASS (pilot, four development cases)

All four records returned the expected dispatch and S4 work labels with verified evidence. Limits on what this shows:

- Four cases, one run, one prompt. It is not a rate.
- The prompt was written after the first run failed on these same records, so they are development cases, not held-out ones.
- The window shows only the tail of the worker program for the positives (from offset 3372 and 3021), which was enough here. A held-out set should include records where the worker's task is more obscured.
- Recovered code shows intended behavior only. Execution is unverified and actor identity stays unresolved.

## Recommendation

For Walerie's graph, keep using the two manually verified links in [dispatch_links.jsonl](../../dispatch_links.jsonl) as the dispatch edges. Treat the automated dispatch and work labels as a pilot-level signal until they pass on held-out records. Overnight launch remains on hold pending Walerie's episode choice.

## Reproduce

```bash
.venv/bin/python -B calibration/swarm_traces/judge_v2.py --input ../redacted.jsonl
```

Requires `frozen_inputs.jsonl` from `freeze_inputs.py` (local only, gitignored).
