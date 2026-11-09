#!/bin/bash
# Pre-registered optional arm A' (deepseek-v4-flash, unchanged v2 prompts). Usage: run_aprime.sh canary|main
set -eu
cd "$(dirname "$0")/../.." || exit 1
SET="${1:?canary or main}"
case "$SET" in canary|main) ;; *) echo "Expected canary or main" >&2; exit 2 ;; esac
PY="${PY:-.venv/bin/python}"
WIKI_IN="${WIKI_IN:?set WIKI_IN to your local records.jsonl.gz}"
SWARM_IN="${SWARM_IN:?set SWARM_IN to your local redacted.jsonl}"
C=calibration/second_judge/cohorts
CONC="${CONC:-16}"
pids=()
run() {
  "$PY" -B batch_classify_vsm.py --source "$2" --model deepseek-v4-flash "$3" "$4" --abstain --input "$5" \
    --cohort-from "$6" --pilot-dir "pilot_sj_$1_$SET" --concurrency "$CONC" --timeout 300 \
    > "pilot_sj_$1_$SET.log" 2>&1

}
run Ap_wiki  wiki  --wiki-prompt  calibration/wiki_prompt_v2.md  "$WIKI_IN" "$C/wiki_$SET.json" &
pids+=("$!")
run Ap_swarm swarm --swarm-prompt calibration/swarm_prompt_v2.md "$SWARM_IN"     "$C/swarm_$SET.json" &
pids+=("$!")
failed=0
for pid in "${pids[@]}"; do wait "$pid" || failed=1; done
exit "$failed"
