#!/bin/bash
# Overnight wrapper for the resumable runner. Reruns the identical command until every cohort ID
# has a validated row (exit 0), up to MAX_ATTEMPTS. Expects ADAPTION_API_KEY in the environment;
# the key is never written to disk. Usage (on the iMac, from ~/swarm-vsm-canary):
#   caffeinate -is ./run_overnight.sh PILOT_DIR INPUT CONCURRENCY [extra runner flags...]
# e.g. extra flags for the abstention run: --wiki-prompt calibration/wiki_prompt_v2.md --abstain
set -u
PILOT="$1"; INPUT="$2"; CONC="${3:-16}"; MAX_ATTEMPTS="${MAX_ATTEMPTS:-8}"
shift 3 || shift $#
for attempt in $(seq 1 "$MAX_ATTEMPTS"); do
  echo "[wrapper] attempt $attempt $(date -u +%FT%TZ)"
  .venv/bin/python -B batch_classify_vsm.py --source "${SOURCE:-wiki}" --pilot-dir "$PILOT" --input "$INPUT" \
    --limit 0 --concurrency "$CONC" "$@"
  rc=$?
  echo "[wrapper] attempt $attempt exited rc=$rc $(date -u +%FT%TZ)"
  if [ "$rc" -eq 0 ]; then
    .venv/bin/python -B verify_batch_output.py "$PILOT" > "$PILOT/verify.json"
    echo "[wrapper] verify rc=$? (see $PILOT/verify.json)"
    exit 0
  fi
  sleep 60
done
echo "[wrapper] gave up after $MAX_ATTEMPTS attempts; rerun to resume"
exit 2
