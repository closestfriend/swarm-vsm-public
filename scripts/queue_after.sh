#!/bin/bash
# Wait until no process matches WAIT_PATTERN, then run run_overnight.sh with the given args.
# Expects ADAPTION_API_KEY in the environment (never written to disk) and SOURCE for the runner.
# Usage (iMac, from ~/swarm-vsm-canary):
#   WAIT_PATTERN="run_overnight.sh pilot_wiki_abstain" SOURCE=swarm \
#     nohup caffeinate -is ./queue_after.sh PILOT INPUT CONC [runner flags] > queue.log 2>&1 &
set -u
echo "[queue] waiting for: $WAIT_PATTERN  $(date -u +%FT%TZ)"
while pgrep -f "$WAIT_PATTERN" > /dev/null; do sleep 60; done
echo "[queue] predecessor finished; starting  $(date -u +%FT%TZ)"
exec ./run_overnight.sh "$@"
