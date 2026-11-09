#!/bin/bash
# Run the pre-registered arms. Usage: run_arms.sh canary|main
# Outputs go to pilot_sj_<arm>_<corpus>_<set>/ (gitignored; per-record rationales stay local).
set -eu
cd "$(dirname "$0")/../.." || exit 1
SET="${1:?canary or main}"
case "$SET" in canary|main) ;; *) echo "Expected canary or main" >&2; exit 2 ;; esac
PY="${PY:-.venv/bin/python}"
WIKI_IN="${WIKI_IN:?set WIKI_IN to your local records.jsonl.gz}"
SWARM_IN="${SWARM_IN:?set SWARM_IN to your local redacted.jsonl}"
C=calibration/second_judge/cohorts
CONC="${CONC:-12}"

pids=()
run() {  # name source model prompt-flag prompt input cohort
  "$PY" -B batch_classify_vsm.py --source "$2" --model "$3" "$4" "$5" --abstain --input "$6" \
    --cohort-from "$7" --pilot-dir "pilot_sj_$1_$SET" --concurrency "$CONC" --timeout 300 \
    > "pilot_sj_$1_$SET.log" 2>&1

}

run A_wiki  wiki  glm-5.2      --wiki-prompt  calibration/wiki_prompt_v2.md               "$WIKI_IN"  "$C/wiki_$SET.json" &
pids+=("$!")
run A_swarm swarm glm-5.2      --swarm-prompt calibration/swarm_prompt_v2.md              "$SWARM_IN" "$C/swarm_$SET.json" &
pids+=("$!")
run B_wiki  wiki  qwen3.5-397b --wiki-prompt  calibration/second_judge/shared_prompt.md   "$WIKI_IN"  "$C/wiki_$SET.json" &
pids+=("$!")
run B_swarm swarm qwen3.5-397b --swarm-prompt calibration/second_judge/shared_prompt.md   "$SWARM_IN" "$C/swarm_$SET.json" &
pids+=("$!")
failed=0
for pid in "${pids[@]}"; do wait "$pid" || failed=1; done
exit "$failed"
