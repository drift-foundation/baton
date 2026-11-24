#!/bin/bash
# run.sh NAME SCRIPT.json [ENV=VAL...] : one pinned-CLI print turn against the stub
set -u
D=/home/sl/src/baton/work/scratch/w385695-K-385929; N=$1; S=$2; shift 2
W=$D/probe/runs/$N; rm -rf "$W"; mkdir -p "$W/home" "$W/cwd" "$W/tmp"
PORT=$((20000 + RANDOM % 20000))
python3 $D/probe/stub.py $PORT "$S" "$W/api.log" & STUB=$!
sleep 0.5
( cd "$W/cwd" && timeout -k 5 ${RUN_TIMEOUT:-120} env -i HOME="$W/home" PATH=/usr/local/bin:/usr/bin:/bin TMPDIR="$W/tmp" \
  ANTHROPIC_BASE_URL=http://127.0.0.1:$PORT ANTHROPIC_API_KEY=stub-not-a-credential \
  CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1 DISABLE_AUTOUPDATER=1 "$@" \
  $D/cli/native/package/claude --print --dangerously-skip-permissions --output-format json "run the scripted commands" \
  > "$W/stdout.json" 2> "$W/stderr.txt" < /dev/null; echo "exit=$?" > "$W/exit" )
kill $STUB 2>/dev/null; wait $STUB 2>/dev/null
cat "$W/exit"; head -c 600 "$W/stdout.json"; echo; head -c 400 "$W/stderr.txt"; echo; cat "$W/api.log" | cut -c1-900
