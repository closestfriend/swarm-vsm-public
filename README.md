# swarm-vsm: where does a swarm keep its identity?

Apart Research **Swarm Alignment Sprint** (Nov 6–8, 2026), Tracks 2 & 4. LA hub at AE Studio.

We map trace records from two AI-agent swarm incidents onto Stafford Beer's **Viable System Model** (S1 operations, S2 coordination, S3 control, S3\* audit, S4 intelligence, S5 identity and policy), using an LLM judge that is allowed to answer **"insufficient evidence"**. We then ask where the swarm's identity function (S5) lives.

## Findings

- **Two incidents, two pictures.**
  - Wiki agent text (6,051 records): of the records with enough evidence, **58% are S2 coordination**, and on a page S2 is followed by S2 **87%** of the time.
  - Swarm Traces, the July 2026 Hugging Face attack payloads (6,000 stratified records): **85.5% S1** and **14.2% S4**, with almost no coordination.
  - The corpora were labelled with different prompts, so the contrast is suggestive.
- **Abstention matters.** 58% of Swarm Traces records and 8% of wiki records are too thin to label. Forced-choice confidence did not identify them.
- **S5 cannot be found by labelling records.** Every record-level S5 label was a false positive. S5 is attested at the system level: METR's investigation documents collective identity, self-sacrifice, succession and binding rules (see `calibration/S5_EVIDENCE.md`).
- **Where S5 sits differs between the incidents.** In the wiki corpus, identity conventions are widespread but are not transmitted from page to page (pre-registered test, `calibration/convergence/`). Agents arrive already carrying them. That points to an S5 outside the observed channel. Where that function sits decides where to intervene.

The limits of each result are stated next to it: see each folder's README and `figures/README.md`.

## Layout

| Path | What |
| --- | --- |
| `schema.py` | `TraceAnnotation` (Pydantic), including optional `evidence_status` |
| `batch_classify_vsm.py` | Resumable labelling runner: frozen cohorts, per-record durable results, retries, wiki and Swarm Traces sources, abstention mode |
| `verify_batch_output.py`, `tests/` | Checks one schema-valid row per cohort ID; offline tests |
| `calibration/` | Prompts, the four-case dispatch check, labelling runs (results and READMEs), the convergence test (pre-registration first), the S5 evidence ladder |
| `figures/` | The four paper figures (PNG, PDF, CSV) and the script that makes them |
| `dispatch_links.jsonl`, `HANDOFF.md` | Two manually verified dispatch links, and the graph handoff notes |
| `video/` | The 3-minute video: storyline, spec, data module, and the narration-cut tooling (no recordings) |

## Reproduce

Requires Python 3.11+, `uv`, and an Adaption API key in `ADAPTION_API_KEY`.

```bash
uv sync
.venv/bin/python -B tests/test_resume.py && .venv/bin/python -B tests/test_abstain.py   # offline
# Wiki labels with abstention (records.jsonl.gz from the wiki agent-text release):
.venv/bin/python -B batch_classify_vsm.py --source wiki --input records.jsonl.gz \
  --pilot-dir pilot_wiki_abstain --wiki-prompt calibration/wiki_prompt_v2.md --abstain --limit 0
# Swarm Traces labels with abstention (redacted.jsonl from swarmtraces.org):
.venv/bin/python -B batch_classify_vsm.py --source swarm --swarm-cohort stratified --swarm-n 6000 --seed 0 \
  --swarm-prompt calibration/swarm_prompt_v2.md --abstain --input redacted.jsonl --pilot-dir pilot_swarm_abstain --limit 0
.venv/bin/python -B verify_batch_output.py pilot_swarm_abstain
```

Cohort IDs are frozen in `calibration/*/cohort.json`. Labelled outputs contain corpus-derived text, so they are not included.

## Data

- **Swarm Traces** (swarmtraces.org): a redacted dataset of payloads reconstructed from the July 2026 Hugging Face incident.
- **Wiki agent text:** a public release of agent-written wiki revisions, May–Sept 2026.
- **METR (2026):** an investigation of the same Hugging Face incident; used as documented evidence, not re-labelled.

No raw corpus text is published here. Eight short verbatim code spans that the judge quoted (in `calibration/swarm_traces/results*.json`) are replaced by SHA-256 hashes and source offsets. No credentials are included.

## Preexisting work (per sprint rules)

- **Before the sprint (Nov 5):** project setup (`pyproject.toml`, environment) and a smoke test (not included).
- **Nov 6, before the 1:30 PM PT kickoff:** first versions of `schema.py` and `batch_classify_vsm.py`, `calibration/prompt.md`, and the first dispatch links.
- **During the sprint:** everything else, including the resumable runner, abstention mode, all labelling runs, the convergence test, the figures and the video.

## Team

- **Hunter:** lead author; implementation, data, analysis, writing.
- **Valerie Kim:** co-author; theory framing (Beer/Ashby, cadence).

Labels come from Adaption `qwen3.5-397b`. AI coding assistants helped with code and drafting; the authors are responsible for all claims.
