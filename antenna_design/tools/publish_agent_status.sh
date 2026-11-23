#!/bin/bash
# Publish antenna_design/status/agents_status.json to GitHub while FDTD rounds or subagent tasks run.
# Only with the owner's consent (CLAUDE.md: no loops or automations on our own initiative).
# Every INTERVAL s: rebuild the status; when the task list, finished list or round counter differ from what
# is already on origin, commit only that file and push. Progress between pushes is extrapolated by the viewer.
# A failed push stays pending and is retried every cycle. Exits after MAX_IDLE consecutive cycles with nothing
# running (note: a stale entry in status/agents_manual.json "agents" keeps it alive), or if the branch changes.
# Commit trailers come from $STATUS_COAUTHOR and $STATUS_SESSION (empty = no trailer).
# Usage: bash antenna_design/tools/publish_agent_status.sh [interval_s=600] [max_idle=1]
INTERVAL=${1:-600}; MAX_IDLE=${2:-1}
BRANCH=codex/uwb-ch9-antenna-design
cd "$(dirname "$0")/../.." || exit 1
F=antenna_design/status/agents_status.json
key() { python3 -c "import json,sys; d=json.load(sys.stdin); print(json.dumps([[(t['agent'],t['task']) for t in d['running']], d['done'], d['rounds']], sort_keys=True))" 2>/dev/null; }
idle=0; fails=0
while :; do
  [ "$(git branch --show-current)" = "$BRANCH" ] || { echo "not on $BRANCH: stop"; exit 2; }
  if ! python3 antenna_design/tools/build_agent_status.py > /dev/null; then
    fails=$((fails+1)); [ $fails -ge 5 ] && { echo "builder failed 5 times: stop"; exit 1; }
    sleep "$INTERVAL"; continue
  fi
  fails=0
  git fetch -q origin "$BRANCH" 2>/dev/null
  if [ "$(git show "origin/$BRANCH:$F" 2>/dev/null | key)" != "$(key < $F)" ]; then
    msg=(-m "Update agent status")
    tr=""; [ -n "$STATUS_COAUTHOR" ] && tr="Co-Authored-By: $STATUS_COAUTHOR"
    [ -n "$STATUS_SESSION" ] && tr="$tr${tr:+$'\n'}Claude-Session: $STATUS_SESSION"
    [ -n "$tr" ] && msg+=(-m "$tr")
    git diff --quiet HEAD -- "$F" || git commit -q --only "$F" "${msg[@]}" || echo "$(date -u +%H:%M:%S) commit failed"
    ok=0
    for i in 1 2 3 4; do git push -q origin "$BRANCH" && { ok=1; break; }; sleep $((2**i)); done
    [ $ok = 1 ] && echo "$(date -u +%H:%M:%S) pushed" || echo "$(date -u +%H:%M:%S) push pending (retry next cycle)"
  fi
  running=$(python3 -c "import json; print(len(json.load(open('$F', encoding='utf-8'))['running']))")
  if [ "$running" = "0" ]; then idle=$((idle+1)); [ $idle -ge $MAX_IDLE ] && [ "${ok:-1}" = 1 ] && exit 0; else idle=0; fi
  sleep "$INTERVAL"
done
