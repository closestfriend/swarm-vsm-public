# Overnight VSM labelling: wiki agent text

The overnight batch for the wiki agent-text release (`records.jsonl.gz` and its companion files in `Adaption-Research/`). This is a separate corpus from Swarm Traces (`redacted.jsonl`). Its labels go in their own output and should not be pooled with the Swarm Traces labels.

## Cohort

[cohort.json](cohort.json) holds the frozen cohort: 6,051 record IDs (sha256 text hashes from `records.jsonl.gz`), each with an `episode_id` and `turn_index`. There is no trace text in it.

- **Episode:** `page:<source_id>`, the first origin's source page (for example `page:dse/OECDEquityLiveJul10`). A shared page is candidate channel evidence, not proof that agents interacted.
- **Turn order:** by the origin's `source_date_literal`, then record ID.
- **Inclusion:**
  - Only dated records.
  - Only pages with two or more dated records: 1,054 pages holding 7,348 records.
  - At most the 50 earliest records per page, which leaves 6,051.
  - 8 pages hit the cap, and 1,297 of their later records are not labelled. The three largest are the wiki's shared landing pages: `dse/WillkommenImWiki` (1,011 dated records), `dse/StartSeite` (245) and `dse/TestSeite` (103). The other five are sequence-collaboration pages with 52–95 records each.
  - Most of the dropped records come from `WillkommenImWiki`. If that page matters for the graphs, label it separately.
- **Coverage:** 985 of the 1,054 pages are on `dse`, 49 on `probier`, and 20 on `fractal`.
- **Excluded:** 3,824 undated records and records on single-record pages. Neither can form a time-ordered episode.

## Prompt

[../wiki_prompt.md](../wiki_prompt.md) (hash `bef3bc698b4b…`, stored in the cohort):

- The decision rules are copied unchanged from `calibration/prompt.md`.
- A short preface and a section on applying them to wiki text were added. That section covers status relays as candidate S2, what S3 requires, link publication as S1, and template text as S0.
- Identity fields are treated as observations: `source_agent_id` is `unresolved` unless the text gives a stable handle.
- Texts over 2,400 characters (196 records) are judged on their first 2,400 characters, matching the Swarm Traces runner.

The runner refuses to resume a pilot directory if the prompt or source has changed since the cohort was frozen.

## Calibration (40 records, before launch)

20 pages chosen by sha256 order, 2 records each, using `--wiki-cap 2 --wiki-pages 20`.

- **Validity:** 40 of 40 rows passed schema validation, with no failures, at 25.8 rec/min (concurrency 16, MacBook).
- **Labels:** 21 S2, 13 S1, 6 S4.

| Label | What it was given to |
| --- | --- |
| S2 | Timed status relays that ask other cohorts to post the next round or deadline |
| S1 | Pages that publish link lists |
| S4 | API query URLs that gather external data |

Errors I noticed reading all 40:

- "HELLO COORD TEST" was labelled S2 at confidence 0.65. Under the rules it should be S0.
- Near-identical link-list pages split across S1, S2 and S4.
- No S3, S3* or S5 appeared in this sample.

I did not change the prompt after reading these. This is a sanity check, not a measured accuracy. Before the labels support claims, spot-check them stratified by label and confidence.

## Run

The run is on the 2020 iMac in `~/swarm-vsm-canary`, at concurrency 16, under `caffeinate -is`. It launched at 2026-11-06 11:52 UTC.

- **First 10 minutes:** 566 rows, 0 failures, 54–56 rec/min. The wiki texts are much shorter than Swarm Traces records, so the rate is about 3.5x the canary's.
- **Expected finish:** about 13:45 UTC if the rate holds.

- [run_overnight.sh](../../run_overnight.sh) reruns the identical command until no IDs are missing (up to 8 attempts), then writes `verify.json`.
- The API key exists only in the detached process's environment.

```bash
# status
ssh wer 'cd ~/swarm-vsm-canary && tail -3 overnight.log && grep -c . pilot_wiki_overnight/results.jsonl'
# relaunch or resume after a stop (same frozen cohort; only missing IDs are submitted)
ssh wer 'cd ~/swarm-vsm-canary && read -r K; export ADAPTION_API_KEY=$K; nohup caffeinate -is ./run_overnight.sh pilot_wiki_overnight records.jsonl.gz 16 > overnight.log 2>&1 < /dev/null &'
# when done: pull and verify
scp -r wer:swarm-vsm-canary/pilot_wiki_overnight ./ && .venv/bin/python -B verify_batch_output.py pilot_wiki_overnight
```

## Result (completed 2026-11-06 14:27 UTC)

**Verified complete:** 6,051 of 6,051 rows schema-valid in both `final.jsonl` and `results.jsonl`. There are no gaps, duplicates, or stray IDs, and the episode and turn assignments match the frozen cohort. The output was copied from the iMac by hand during a home wifi outage, and I verified it again on the MacBook after the copy.

**Runs:**
- Attempt 1 wrote 5,777 rows in 2 h 26 min (39.5 rec/min overall).
- 274 requests failed with "Request timed out", all inside one window (13:39–13:54 UTC). That points to an API-side slowdown, not bad records.
- Attempt 2, started automatically by the wrapper, skipped the 5,777 completed rows and wrote the 274 missing ones with 0 failures.

**Labels.** Every record was forced into one of the seven labels, because the schema has no `insufficient_evidence` option. Read low-content records as forced choices, not as positive evidence.

| Primary | Records | Share |
| --- | ---: | ---: |
| S2_COORDINATION | 3,305 | 54.6% |
| S1_OPERATIONS | 1,676 | 27.7% |
| S4_INTELLIGENCE | 891 | 14.7% |
| S0_NOISE | 143 | 2.4% |
| S3_STAR_AUDIT | 33 | 0.5% |
| S3_CONTROL | 2 | <0.1% |
| S5_POLICY | 1 | <0.1% |

- **Confidence:** 27 rows below 0.6, 3,166 from 0.6 to 0.8, and 2,858 at 0.8 or above.
- **`source_agent_id`:** `unresolved` for 3,015 rows. The other 3,036 carry a handle written in the text, which is an observation, not an authenticated actor.
- **Within-page transitions:** S2 is highly persistent (P(S2→S2) = 0.85). S1 and S4 mostly persist or move to S2. The full matrices are in `summary.json`.

**The three rare primary labels (read by hand):**

- **S3_CONTROL, `2b63aa68…`** (`page:dse/IHMEFamilyPlanningFeb07Cohort`, turn 10): a signed message from one cohort handle to another. "Please accelerate now. At R4 answer Bahrain immediately, then post continuation notice…". This looks like a real allocation of a bounded task.
- **S3_CONTROL, `6f747634…`** (`page:dse/PoliceWageAgeSequenceMar10Collab`, turn 17): reports R4, then "@MAR13 … please race/report R6 … and later rounds". This also looks like a real allocation.
- **S5_POLICY, `e51943c6…`** (`page:dse/WillkommenImWiki`, turn 48): the wiki's own German welcome text, asking visitors to enter a name under Settings to limit spambot abuse, with an agent-added link appended. It is a host-site rule for human editors, not a policy of the agent system. Treat it as a mislabel for swarm-level S5, or report it separately as host-environment policy. The text also shows mojibake (`mÃ¶chten`), so its encoding was mangled somewhere along the way.

These are labels from one forced-choice run, not measured accuracy. Before the paper relies on the distribution, spot-check a sample stratified by label and confidence.

The outputs are `final.jsonl` (one `TraceAnnotation` per cohort ID, in cohort order) and `summary.json` (state distribution and per-episode Markov transitions), both in the pilot directory. `parent_id` is always null for this corpus. Within-page transitions come from `episode_id` and `turn_index`.

## Correction (2026-11-13): attribution of the timeout window

The note above attributes the 274 clustered timeouts to "an API-side slowdown." That was an inference, not an observation: the home internet connection in use during this run was later found degraded (outside wiring repaired and router replaced by a technician after this run). A client-side network fault in the same window explains the clustering equally well, and cannot be ruled out from the logs we kept. Both causes produce the same signature; the run's own mitigation (resumable wrapper, attempt 2 with 0 failures) is correct under either attribution. No change to the results or the cap analysis.
