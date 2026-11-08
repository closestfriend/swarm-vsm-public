# Wiki labels with an abstention option

**Status:** done.
- 40-record calibration: 2026-11-06.
- Full 6,051-record run: completed 2026-11-07 00:40 UTC on the iMac in 2 h 21 min, with no failed attempts and no retries. Verified 6,051/6,051, no gaps or duplicates.

## Full-run result (v1 forced choice vs v2 abstention, same 6,051 records)

Data: [comparison_full.json](comparison_full.json).

**Abstained: 507 (8.4%).** In v1 these records had been labelled:

| v1 label | Abstained | Share of that label |
| --- | ---: | ---: |
| S0 | 106 of 143 | 74% |
| S1 | 239 of 1,676 | 14% |
| S4 | 96 of 891 | 11% |
| S2 | 66 of 3,305 | 2% |
| S3*, S3, S5 | 0 | 0% |

v1 used S0 as the place for thin records. 75 of the 507 had v1 confidence of 0.8 or higher, so forced-choice confidence does not identify thin records.

**v2 distribution among sufficient records (5,544):**

| Label | Share |
| --- | ---: |
| S2 | 58.2% |
| S1 | 26.9% |
| S4 | 13.3% |
| S0 | 1.1% |
| S3* | 0.4% (22) |
| S3 | 2 records |
| S5 | 2 records |

**Label stability on sufficient records: 81% agree with v1.**
- S2 keeps its label 91% of the time, S1 70%, S4 66%.
- The flips are mostly across the S1/S2 and S1/S4 boundaries, in both directions: S2→S1 236, S1→S2 234, S4→S1 232, S1→S4 162.
- For the paper:
  - **The S2 share is robust.**
  - **The S1/S4 split is soft.** Prompt wording and run-to-run variation move it by tens of percent.
  - For reference, the canary's two-machine replay of the same prompt agreed on 45/48.

**Record-level S5 labels (a fact about the judge, not about S5).** Both v2 S5 labels are false positives:
- the host wiki's welcome text, labelled S5 again;
- a link list titled "Official filtered variants set", labelled S5 because of the word "Official".

Under the evidence ladder (Rule 2), record labels cannot establish or rule out S5, which is a system-level function. Report these in methods as a judge failure mode: wording that sounds official or rule-like is misread as policy. Do not report them as an S5 result.

## Calibration result (40 records: same 20 pages, 2 per page, as the v1 calibration)

40 of 40 rows were valid, with 0 failures, in 79 s at concurrency 16. Comparison data: [comparison_calib40.json](comparison_calib40.json).

**7 of 40 abstained (17.5%):**
- five lone URLs with no surrounding words;
- the test string "HELLO COORD TEST", which v1 had labelled S2;
- one link bundle labelled "temporary research link". This one is borderline; it could reasonably count as sufficient.

**Which forced v1 labels they came from:**
- 4 of v1's 6 S4 labels;
- 2 of 13 S1;
- 1 of 21 S2.

In v1, lone API URLs were mostly read as S4, so v1's S4 share is likely inflated.

**v1 confidence on those 7:** all between 0.6 and 0.8. Forced-choice confidence does not identify thin records.

**Agreement on records v2 judged sufficient:** 28 of 33. All 5 changes are link-list pages moving between S1, S2 and S4, the same instability seen in v1. This is a boundary problem in the rubric, separate from abstention. The prompt was not changed after this calibration.

## Why

The overnight wiki run used `TraceAnnotation`, whose `primary_vsm` has to be one of the seven VSM labels. Every record was therefore forced into a label, including test strings and lone links. This run adds the option to answer `insufficient_evidence`, on the same records, so the two can be compared.

## What changed (and what didn't)

- **`schema.py`:** new optional field `evidence_status` (`sufficient` / `insufficient_evidence`).
  - Existing rows read as `None`, so the overnight `final.jsonl` and Walerie's scripts stay valid.
  - `primary_vsm` is unchanged and still required. On an abstention it holds the judge's best guess, which is kept only for comparison.
- **`calibration/wiki_prompt_v2.md`:** the v1 prompt plus one block asking for `evidence_status` first. It says that abstaining is a correct answer, and distinguishes S0 (no function) from insufficient evidence (a function that can't be seen). Nothing else changed, so the comparison isolates the abstention option.
- **`batch_classify_vsm.py`:**
  - `--wiki-prompt` selects the prompt file.
  - `--abstain` adds `evidence_status` to the requested schema and rejects answers without it.
  - `--cohort-from` freezes a new pilot directory with another run's exact IDs, episodes and turns.
  - Without these flags the behaviour is identical to the overnight run (prompt hash `bef3bc698b4b`, checked by test).
- **`run_overnight.sh`:** passes extra runner flags through.
- **`compare.py`:** writes `comparison.json` with:
  - abstention count and share;
  - which v1 labels the abstentions had been forced into;
  - agreement on records both runs judge sufficient;
  - the v2 distribution with abstentions excluded.

## Ready to run

`pilot_wiki_abstain/cohort.json` is frozen locally (gitignored). It has the same 6,051 records as the overnight cohort, prompt hash `1bc57ad5a3b6…`, and abstain on.

Expected: about 2–2.5 h at concurrency 16, judging by the overnight run.

**Step 1 (recommended): 40-record calibration** (about 2 min). Read the abstentions before committing to 6,051 records.

```bash
.venv/bin/python -B batch_classify_vsm.py --source wiki --input ../records.jsonl.gz \
  --pilot-dir pilot_wiki_abstain_calib --wiki-prompt calibration/wiki_prompt_v2.md --abstain \
  --wiki-cap 2 --wiki-pages 20 --limit 0 --concurrency 16
```

**Step 2: full run on this Mac.** Resumable, so a dropped connection just means rerunning the same command.

```bash
.venv/bin/python -B batch_classify_vsm.py --source wiki --input ../records.jsonl.gz \
  --pilot-dir pilot_wiki_abstain --wiki-prompt calibration/wiki_prompt_v2.md --abstain \
  --limit 0 --concurrency 16
```

**Step 2 (alternative): full run on the iMac**, once home wifi is back. First copy `batch_classify_vsm.py`, `schema.py`, `run_overnight.sh`, `calibration/wiki_prompt_v2.md` and `pilot_wiki_abstain/cohort.json` across. Then start it with the API key piped in as before, and:

```bash
nohup caffeinate -is ./run_overnight.sh pilot_wiki_abstain records.jsonl.gz 16 \
  --wiki-prompt calibration/wiki_prompt_v2.md --abstain > abstain.log 2>&1 < /dev/null &
```

**Step 3: verify and compare.**

```bash
.venv/bin/python -B verify_batch_output.py pilot_wiki_abstain
.venv/bin/python -B calibration/wiki_abstain/compare.py \
  --v1 pilot_wiki_overnight/final.jsonl --v2 pilot_wiki_abstain/final.jsonl
```

## Tests (offline, no API)

```bash
.venv/bin/python -B tests/test_abstain.py   # default unchanged, abstain enforced, cohort copy exact, compare works
.venv/bin/python -B tests/test_resume.py    # resume behaviour unchanged
```
