# Four-case Swarm Traces dispatch check

Does a prefix-only judge miss intended dispatch that sits past character 2,400, and does an evidence window recover it without disturbing the work label?

Records: R0189558 and R0189562 (intended-dispatch positives); R0189553 and R0189569 (direct-reconnaissance controls). Expected work function for all four: S4_INTELLIGENCE.

## Inputs (frozen before judging)

- **Prefix:** first 2,400 characters of the decoded text.
- **Evidence window:** 2,400 characters. Positives keep the first 300 characters (record banner), a `[...]` marker, and the final 2,100 characters, which contain the manually verified dispatch call and the later polling. Controls are 883 and 556 characters, so they are intact and identical in both conditions.
- Source offsets and SHA-256 hashes: [manifest.json](manifest.json). `judge.py` refuses to run if the frozen file no longer matches.
- Same metadata (record kind, tags, heuristic source ID, targets, artifacts, record length) in both conditions.

## Judge

Adaption `qwen3.5-397b`, temperature 0, one prompt (hash in results), one call per record and condition. Output reports `intended_dispatch` with a verbatim `dispatch_evidence_span`, `worker_task`, `actor_identity`, and `work_function` separately. Recovered code supports intended dispatch only; execution is unverified.

## Reproduce

Run from the swarm-vsm directory.

```bash
.venv/bin/python -B calibration/swarm_traces/freeze_inputs.py --input ../redacted.jsonl
.venv/bin/python -B calibration/swarm_traces/judge.py
.venv/bin/python -B calibration/swarm_traces/judge.py --retry-errors   # only if an item hit a transient API error
```

`frozen_inputs.jsonl` holds raw corpus excerpts, is gitignored, and has never been committed; keep it local. [results.json](results.json) holds the judgments.

## Result

| Record | Role | Prefix: dispatch / work | Window: dispatch / work |
| --- | --- | --- | --- |
| R0189558 | positive | insufficient_evidence / S4 | **yes** / S3_CONTROL |
| R0189562 | positive | insufficient_evidence / S4 | **yes** / S3_CONTROL |
| R0189553 | control | no / S4 | no / S4 |
| R0189569 | control | no / S4 | no / S4 |

Actor identity was `unresolved` in all eight judgments.

R0189558's window judgment first returned an API `InternalServerError` and was re-run once with the identical frozen input and prompt (`--retry-errors`); no other item was re-run.

Evidence check (built into the gate, no API calls: `judge.py --rescore`): a flagged dispatch counts as recovered only if its quoted span appears verbatim in the supplied window. Both flagged quotes do, and they map back to source offsets 4704-4808 (R0189558) and 4390-4495 (R0189562), which contain the manually verified call spans.

## Gate: FAIL

The window recovered both intended dispatches (spans match the manually checked calls in [dispatch_links.jsonl](../../dispatch_links.jsonl)) and flagged neither control. It did not preserve the S4 work label: both positives moved from S4_INTELLIGENCE to S3_CONTROL. The prefix condition recovered no dispatch.

So the dispatch signal appears when the window shows the call, but the judge then labels the record by the dispatch rather than by the reconnaissance the worker performs, which is the distinction the check was built to protect. The judge's `worker_task` text was generic ("execute the containerized payload"), because the pod's command is encoded in the record, so the window does not show what the worker does.

Consequences per the pre-stated rule:

- Mark automated dispatch labels **exploratory**.
- Cite the two manually verified links in [dispatch_links.jsonl](../../dispatch_links.jsonl) as the evidence.
- No prompt changes were made after seeing results. Four cases, one prompt, one run each: this is not an estimate of a rate.
