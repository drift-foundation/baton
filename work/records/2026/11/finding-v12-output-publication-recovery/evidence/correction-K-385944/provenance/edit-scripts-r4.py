"""Revision 4 of the two qualification scripts (review 2026-11-24T04-42-16Z, C5.1 and C5.2). Applied once to
copies of the reviewed revision-3 files; every replacement must match exactly once."""
import pathlib

STACK_LIVE = r'''stack_live() {  # [TOKEN] -> "name pid" per LIVE process of the instance's stack; status 3 when that cannot be told
  # THE PRODUCT'S OWN ANSWER, through its supported `status`. A process is `running` there only when the pid AND
  # the start time its record carries both still match (tools.stack, "OWNERSHIP IS PROVED, NOT ASSUMED");
  # `unknown` is the product saying it cannot tell, and it is passed on as that (status 3), never as "not
  # running". A status that names neither state for either process is likewise not an answer.
  # WITH A TOKEN, only a process that carries THIS run's start token in its own environment is printed. The
  # stack hands its caller's environment to the processes it starts, so the token is in a process only if this
  # run's start command is what started it. A record, or a pid, alone is not ownership.
  local out="$PREFIX.stack-status.txt"
  timeout --kill-after=10 60 just --justfile "$DEST/justfile" status > "$out" 2>&1 || true
  python3 - "$out" "$STACK_STATE" "${1:-}" <<'PY'
import json, os, re, sys
text, state_root, token = open(sys.argv[1], errors="replace").read(), sys.argv[2], sys.argv[3]
said = {m.group(1): (m.group(2), m.group(3)) for m in
        re.finditer(r"^(manager|publisher)\s+(absent|running|stale|unknown)(?: pid (\d+))?\s*$", text, re.M)}
if set(said) != {"manager", "publisher"} or any(s == "unknown" or (s == "running" and p is None) for s, p in said.values()):
    sys.exit(3)
started = lambda raw: int(raw[raw.rfind(b")") + 2:].split()[19])
for name in ("manager", "publisher"):
    state, pid = said[name]
    if state != "running":
        continue                      # absent or stale: the product says POSITIVELY not running
    if token:
        try:
            record = json.load(open(os.path.join(state_root, name + ".json")))
            first = open("/proc/%s/stat" % pid, "rb").read()
            carried = open("/proc/%s/environ" % pid, "rb").read().split(b"\0")
            again = open("/proc/%s/stat" % pid, "rb").read()
            same = record.get("pid") == int(pid) and record.get("started_at") == started(first) == started(again)
        except (OSError, ValueError, IndexError):
            sys.exit(3)
        if not same:
            sys.exit(3)               # the process changed under the reading: not told
        if ("W385695_STACK_START=" + token).encode() not in carried:
            continue                  # live, and not this run's start
    print(name, pid)
PY
}
'''

# Placed AFTER `finish` and BEFORE `trap finish EXIT` in both scripts, byte-identical in both.
STACK_OWNED = r'''op_alive() {  # FILE holding "pid start-tick" -> success while THAT process (pid AND start time) has not ended
  local pid tick now
  read -r pid tick < "$1" 2>/dev/null || return 1
  now="$(awk '{print $3 ":" $22}' "/proc/$pid/stat" 2>/dev/null)" || return 1
  case "$now" in ""|Z:*) return 1;; esac
  [ "${now#*:}" = "$tick" ]
}
start_stack() {  # LOG -> start the instance's stack as THIS run's. Refuses over another's; stops nothing itself
  # OWNERSHIP IS PROVED, NEVER ASSUMED, AND THE INTENT IS ON DISK BEFORE THE EFFECT. A stack with a live process
  # before this start is somebody else's, and one whose state cannot be told is not known to be nobody's: both
  # are refused and nothing is started or stopped. Then, in this order: the intent with this start's token; the
  # start command, which first records its own process; its ending. `reconcile_stack` works from those records
  # on EVERY exit, so an interruption at any point between them is reconciled and not forgotten.
  local before token code=0 owned="" me
  [ ! -e "$PREFIX.stack-start-intent" ] || fail "an earlier start of this phase is not reconciled ($PREFIX.stack-start-intent); it is reconciled now and nothing new is started over it"
  before="$(stack_live)" || fail "the instance stack's state cannot be established before the start (see $PREFIX.stack-status.txt); nothing was started"
  [ -z "$before" ] || fail "the instance stack is already running ($(echo $before)); this phase starts and stops its own and will not stop another's"
  token="${RUN:-run}-$$-$(date +%s%N)"
  rm -f "$PREFIX.stack-start-op" "$PREFIX.stack-start-op-done" "$PREFIX.stack-started"
  echo "$token" > "$PREFIX.stack-start-intent"
  ( me="$BASHPID"; echo "$me $(awk '{print $22}' "/proc/$me/stat")" > "$PREFIX.stack-start-op"
    W385695_STACK_START="$token" timeout --kill-after=10 300 just --justfile "$DEST/justfile" start > "$1" 2>&1 ) &
  wait $! || code=$?
  echo "$code" > "$PREFIX.stack-start-op-done"
  owned="$(stack_live "$token")" || fail "the instance stack's state cannot be established after the start (status $code); the start intent is retained and reconciled at the end"
  [ -z "$owned" ] || { MANAGER_STARTED=1; echo "$owned" > "$PREFIX.stack-started"; }
  if [ "$code" != 0 ]; then
    if [ -n "$MANAGER_STARTED" ]; then fail "the instance stack did not start (status $code); the processes it recorded are this run's and will be stopped"
    else fail "the instance stack did not start (status $code); it recorded no live process of this run"; fi
  fi
  [ -n "$MANAGER_STARTED" ] || fail "the start command succeeded and the stack records no live process of this run; ownership is not established"
}
reconcile_stack() {
  # FROM THE RECORDS, NOT FROM A VARIABLE: a start whose intent is on disk is reconciled whether or not this
  # process lived to hear its answer. Only what is POSITIVELY this run's is stopped, through the instance's own
  # `stop`, and only a positive read-back ends the matter; anything else is left as it is, reported UNRESOLVED,
  # and the intent is retained for the operator.
  [ -s "$PREFIX.stack-start-intent" ] || return 0
  local token end all="" owned="" rc=0 stray=""
  token="$(head -1 "$PREFIX.stack-start-intent")"
  # 1. THE START COMMAND MUST HAVE ENDED. It records its own process before it asks for anything; a moment is
  #    allowed for a child forked just before an interruption to write that record. Its own bound is 310 s.
  if [ ! -e "$PREFIX.stack-start-op-done" ]; then
    end=$(( $(date +%s) + 3 )); until [ -s "$PREFIX.stack-start-op" ] || [ "$(date +%s)" -ge "$end" ]; do sleep 0.2; done
    if [ -s "$PREFIX.stack-start-op" ]; then
      end=$(( $(date +%s) + 330 )); while op_alive "$PREFIX.stack-start-op" && [ "$(date +%s)" -lt "$end" ]; do sleep 0.2; done
      if op_alive "$PREFIX.stack-start-op"; then
        say "UNRESOLVED: this run's start command ($(cat "$PREFIX.stack-start-op")) has not ended; nothing is stopped under a start in flight; intent retained at $PREFIX.stack-start-intent"
        UNRESOLVED=1; return 0
      fi
    fi
  fi
  # 2. WHAT IS LIVE, AND WHICH OF IT IS THIS RUN'S.
  all="$(stack_live)" || rc=$?
  [ "$rc" != 0 ] || owned="$(stack_live "$token")" || rc=$?
  if [ "$rc" != 0 ]; then
    say "UNRESOLVED: the instance stack's state could not be established (see $PREFIX.stack-status.txt); nothing was stopped; intent retained at $PREFIX.stack-start-intent"
    UNRESOLVED=1; return 0
  fi
  if [ -z "$all" ]; then
    say "cleanup: the instance stack positively records no live process; nothing to stop"
  elif [ "$all" != "$owned" ]; then
    say "UNRESOLVED: the stack's live process(es) ($(echo $all)) are not all this run's start (this run's: $(echo ${owned:-none})); nothing was stopped; intent retained at $PREFIX.stack-start-intent"
    UNRESOLVED=1; return 0
  else
    timeout --kill-after=10 120 just --justfile "$DEST/justfile" stop >> "$PREFIX.cleanup.log" 2>&1 || true
    rc=0; all="$(stack_live)" || rc=$?
    if [ "$rc" = 0 ] && [ -z "$all" ]; then say "cleanup: instance stack stopped (this run's: $(echo $owned))"
    else
      say "UNRESOLVED: the instance stack was asked to stop and is not positively stopped (see $PREFIX.cleanup.log, $PREFIX.stack-status.txt); intent retained at $PREFIX.stack-start-intent"
      UNRESOLVED=1; return 0
    fi
  fi
  # 3. NOTHING OF THIS START OUTSIDE THE STACK'S RECORDS. A start command killed between starting a process and
  #    recording it leaves one no record names; it carries the token. It is REPORTED, never signalled from here.
  stray="$(python3 - "$token" <<'PY'
import os, sys
want = ("W385695_STACK_START=" + sys.argv[1]).encode()
for name in sorted(os.listdir("/proc"), key=lambda n: (len(n), n)):
    if name.isdigit():
        try:
            if want in open("/proc/%s/environ" % name, "rb").read().split(b"\0") and open("/proc/%s/stat" % name, "rb").read().rsplit(b")", 1)[1].split()[0] != b"Z":
                print(name, end=" ")
        except (OSError, IndexError):
            pass
PY
)"
  if [ -n "$stray" ]; then
    say "UNRESOLVED: process(es) this run's start command started are alive outside the stack's records: $stray; intent retained at $PREFIX.stack-start-intent"
    UNRESOLVED=1; return 0
  fi
  mv -f "$PREFIX.stack-start-intent" "$PREFIX.stack-start-reconciled"
}
'''


def edit(path, pairs):
    p = pathlib.Path(path); s = p.read_text()
    for old, new in pairs:
        assert s.count(old) == 1, (path, s.count(old), old[:70])
        s = s.replace(old, new)
    p.write_text(s)


def between(text, start, stop):
    a = text.index(start); b = text.index(stop, a)
    return text[a:b]


q = pathlib.Path("qualify-w385695.sh").read_text()
edit("qualify-w385695.sh", [
    ("# W385695 package/image/engine qualification, revision 3 (reviews 2026-11-24T01-52-00Z and T03-03-48Z, C5).",
     "# W385695 package/image/engine qualification, revision 4 (reviews 2026-11-24T01-52-00Z, T03-03-48Z and T04-42-16Z, C5)."),
    ('OWNED_PIDS=(); PAUSED=""; MANAGER_STARTED=""; ENDING=""\n', 'OWNED_PIDS=(); PAUSED=""; MANAGER_STARTED=""; ENDING=""; UNRESOLVED=""\n'),
    # -- C5.2: positive absence / not-paused versus an observation that failed; in-flight pause settled first
    (between(q, "reconcile_pause() {", "finish() {"), r'''reconcile_pause() {
  # WHAT THE WATCHER INTENDED AND WHAT IT WAS TOLD, read from its own records after it has stopped. An intent
  # is written BEFORE the engine is asked to pause and an acknowledgment after it answers, so a pause whose
  # reply was lost, and one acknowledged before this process copied the id into a variable, are both found
  # here. The id in either record was proved to be the selected attempt's container before it was written.
  local id seen="" state end
  # THE PAUSE REQUEST ITSELF MUST HAVE ENDED FIRST. The watcher is gone by now, but the engine call it made is
  # its own process and records itself before it asks; a request still in flight could pause AFTER this
  # reconciliation looked. Its own bound is ENGINE_SECONDS + 10.
  if [ -s "$PREFIX.pause-intent" ] && [ ! -e "$PREFIX.pause-op-done" ]; then
    end=$(( $(date +%s) + 3 )); until [ -s "$PREFIX.pause-op" ] || [ "$(date +%s)" -ge "$end" ]; do sleep 0.2; done
    if [ -s "$PREFIX.pause-op" ]; then
      end=$(( $(date +%s) + ${ENGINE_SECONDS:-60} + 20 )); while op_alive "$PREFIX.pause-op" && [ "$(date +%s)" -lt "$end" ]; do sleep 0.2; done
      if op_alive "$PREFIX.pause-op"; then
        say "UNRESOLVED: the pause request ($(cat "$PREFIX.pause-op")) has not ended; the selected container may yet be paused; intent retained at $PREFIX.pause-intent"
        UNRESOLVED=1
      fi
    fi
  fi
  for id in "$PAUSED" $(cat "$PREFIX.pause-intent" "$PREFIX.paused" 2>/dev/null); do
    [ -n "$id" ] || continue
    case " $seen " in *" $id "*) continue;; esac
    seen="$seen $id"
    state="$(pause_state "$id")"
    case "$state" in
      true)
        eng unpause "$id" >> "$PREFIX.cleanup.log" 2>&1 || echo "unpause-unacknowledged $id" >> "$PREFIX.cleanup.log"
        # THE RELEASE IS READ BACK, whatever the unpause answered: its reply can be lost in either direction.
        state="$(pause_state "$id")"
        case "$state" in
          false) say "cleanup: unpaused $id (read back: not paused)";;
          absent) say "cleanup: $id ended while it was being released (read back: positively absent)";;
          true) say "UNRESOLVED: container $id is still paused and could not be released; intent retained at $PREFIX.pause-intent"; UNRESOLVED=1;;
          *) say "UNRESOLVED: container $id was paused and its release could not be read back; intent retained at $PREFIX.pause-intent"; UNRESOLVED=1;;
        esac;;
      false) say "cleanup: $id is positively not paused";;
      absent) say "cleanup: $id positively no longer exists; nothing to release";;
      *) say "UNRESOLVED: the pause state of $id could not be read (see $PREFIX.cleanup.log); it was NOT unpaused blind; intent retained at $PREFIX.pause-intent"; UNRESOLVED=1;;
    esac
  done
}
pause_state() {  # ID -> true | false | absent | unknown. The first three are POSITIVE answers of the engine
  # `absent` is the engine ANSWERING a listing by this exact id with nothing; an inspection that merely failed
  # (daemon unreachable, timeout) is `unknown` and is never read as "gone". Three tries, then `unknown`.
  local out try
  for try in 1 2 3; do
    if out="$(eng inspect --format '{{.State.Paused}}' "$1" 2>> "$PREFIX.cleanup.log")"; then
      case "$out" in true|false) echo "$out"; return 0;; esac
    elif out="$(eng ps -aq --no-trunc --filter "id=$1" 2>> "$PREFIX.cleanup.log")" && [ -z "$out" ]; then
      echo absent; return 0
    fi
    [ "$try" = 3 ] || sleep 1
  done
  echo unknown
}
'''),
    (between(q, "finish() {", "trap finish EXIT"), r'''finish() {
  local code=$?
  [ -z "$ENDING" ] || return 0
  ENDING=1; set +e
  # THE WATCHER FIRST, and it is WAITED FOR: nothing is reconciled while it could still be about to pause. Any
  # engine request it had in flight is then settled by `reconcile_pause` before that looks at the container.
  rm -f "$PREFIX.watching"
  local pid
  for pid in "${OWNED_PIDS[@]}"; do
    ended "$pid" 20 || { kill -TERM "$pid" 2>/dev/null; ended "$pid" 10 || { kill -KILL "$pid" 2>/dev/null; ended "$pid" 5 || { say "UNRESOLVED: owned process $pid did not end"; UNRESOLVED=1; }; }; }
  done
  reconcile_pause
  # THE STACK ONLY IF IT IS PROVED THIS RUN'S, on every exit, from the start records (see `start_stack`).
  reconcile_stack
  # WHAT IS LEFT OF THE SELECTED ATTEMPTS IS REPORTED, NEVER REMOVED HERE. It is settled by the product's own
  # owner (`manager settlement-remove`), so nothing this script cannot account for is destroyed by it. An
  # engine that does not answer has not said "nothing is left".
  if [ -s "$PREFIX.selected-attempts" ]; then
    local attempt left
    while read -r attempt; do
      if left="$(eng ps -a --filter "label=baton.v12.runtime_attempt_id=$attempt" --format '{{.ID}} {{.Status}}' 2>> "$PREFIX.cleanup.log")"; then
        [ -z "$left" ] || printf '%s\n' "$left" | sed "s|^|$attempt |" >> "$PREFIX.leftover-containers.txt"
      else say "UNRESOLVED: the engine did not answer for what is left of attempt $attempt"; UNRESOLVED=1; fi
    done < "$PREFIX.selected-attempts"
    [ -s "$PREFIX.leftover-containers.txt" ] && { say "UNRESOLVED: selected containers remain; see $PREFIX.leftover-containers.txt"; UNRESOLVED=1; }
  fi
  # A PHASE WITH UNRESOLVED CLEANUP DID NOT SUCCEED, whatever its own steps answered.
  if [ -n "${UNRESOLVED:-}" ]; then say "phase $phase leaves UNRESOLVED cleanup; what is retained is named above"; [ "$code" != 0 ] || code=1; fi
  say "phase $phase ended with status $code"
  # SEALED LAST, after every writer this run owns has stopped.
  ( cd "$EVIDENCE" && find . -type f ! -name evidence.sha256 -print0 | sort -z | xargs -0 sha256sum > evidence.sha256 )
  exit "$code"
}
''' + STACK_OWNED),
    # -- the watcher's pause is its own recorded process
    ('''          echo "$id" > "$PREFIX.pause-intent"
          eng pause "$id" >> "$PREFIX.watch.log" 2>&1 && echo "$id" > "$PREFIX.paused" || echo "pause-unacknowledged $id" >> "$PREFIX.watch.log"
''', '''          # The request is its OWN process and records itself before it asks, so one that outlives this
          # watcher is still found and waited for.
          rm -f "$PREFIX.pause-op" "$PREFIX.pause-op-done"
          echo "$id" > "$PREFIX.pause-intent"
          ( me="$BASHPID"; echo "$me $(awk '{print $22}' "/proc/$me/stat")" > "$PREFIX.pause-op"
            eng pause "$id" >> "$PREFIX.watch.log" 2>&1 ) &
          if wait $!; then echo "$id" > "$PREFIX.paused"; else echo "pause-unacknowledged $id" >> "$PREFIX.watch.log"; fi
          : > "$PREFIX.pause-op-done"
'''),
    (between(q, "stack_live() {", "serve() {"), STACK_LIVE),
    (between(q, "serve() {", "until_status() {"), '''serve() {
  # See `start_stack`: refused over a stack that is running or cannot be told; the intent is recorded before the
  # effect; and whatever this start left is reconciled by `finish` on every exit.
  start_stack "$PREFIX.manager-start.log"
}
'''),
    ('''  if [ "$(eng inspect --format '{{.State.Paused}}' "$PAUSED" 2>/dev/null)" = "true" ]; then
    eng unpause "$PAUSED" >> "$PREFIX.watch.log" 2>&1 || fail "the frozen publisher could not be released"
  else
    say "note: the publisher was already ended by the manager while frozen"
  fi
  PAUSED=""
''', '''  case "$(pause_state "$PAUSED")" in
    true) eng unpause "$PAUSED" >> "$PREFIX.watch.log" 2>&1 || fail "the frozen publisher could not be released; cleanup reads its state back";;
    false) say "note: the publisher is no longer paused";;
    absent) say "note: the publisher was already ended by the manager while frozen";;
    *) fail "the frozen publisher's pause state could not be read; cleanup tries again and retains what it cannot confirm";;
  esac
'''),
    ('''    now="$(eng image inspect --format '{{.Id}}' "$tag" 2>/dev/null || true)"
    if [ -z "$now" ]; then say "cleanup: $tag is already gone"
    elif [ "$now" != "$id" ]; then''', '''    # A TAG IS GONE ONLY WHEN THE ENGINE SAYS SO: an inspection that failed has not answered.
    if ! now="$(eng image inspect --format '{{.Id}}' "$tag" 2>> "$PREFIX.cleanup.log")"; then
      if now="$(eng image ls -q --no-trunc "$tag" 2>> "$PREFIX.cleanup.log")" && [ -z "$now" ]; then say "cleanup: $tag is already gone (the engine lists no such tag)"
      else say "UNRESOLVED: the engine did not answer for $tag; it stays recorded in images.owned"; UNRESOLVED=1; fi
    elif [ "$now" != "$id" ]; then'''),
])

s = pathlib.Path("option-a-setup.sh").read_text()
edit("option-a-setup.sh", [
    ('MANAGER_STARTED=""; ENDING=""\n', 'MANAGER_STARTED=""; ENDING=""; UNRESOLVED=""\n'),
    (between(s, "stack_live() {", "finish() {"), STACK_LIVE),
    (between(s, "finish() {", "trap finish EXIT"), r'''finish() {
  local code=$?
  [ -z "$ENDING" ] || return 0
  ENDING=1; set +e
  # ON EVERY EXIT, from the start records: see `start_stack` and `reconcile_stack` (the same text as in
  # `qualify-w385695.sh`).
  reconcile_stack
  if [ -n "${UNRESOLVED:-}" ]; then say "phase $phase leaves UNRESOLVED cleanup; what is retained is named above"; [ "$code" != 0 ] || code=1; fi
  say "phase $phase ended with status $code"
  exit "$code"
}
''' + STACK_OWNED),
    ('''  [ -z "$(stack_live)" ] || fail "the instance stack is running; workers are admitted with it stopped"
''', '''  local live; live="$(stack_live)" || fail "the instance stack's state cannot be established (see $PREFIX.stack-status.txt); workers are admitted with it positively stopped"
  [ -z "$live" ] || fail "the instance stack is running; workers are admitted with it stopped"
'''),
    ('''  [ -z "$(stack_live)" ] || fail "the instance stack is already running; this phase starts and stops its own"
  local code=0
  timeout --kill-after=10 300 just --justfile "$DEST/justfile" start > "$PREFIX.start.log" 2>&1 || code=$?
  [ -z "$(stack_live)" ] || MANAGER_STARTED=1
  [ "$code" = 0 ] && [ -n "$MANAGER_STARTED" ] || fail "the instance stack did not start under this run's ownership (status $code)"
''', '''  start_stack "$PREFIX.start.log"
'''),
    ('''  timeout --kill-after=10 120 just --justfile "$DEST/justfile" stop > "$PREFIX.stop.log" 2>&1 || fail "the instance stack did not stop"
  MANAGER_STARTED=""
  [ -z "$(stack_live)" ] || fail "the instance stack still records a live process after stop"
''', '''  # The same reconciliation an interrupted run gets: stop what is positively this run's and read it back.
  reconcile_stack
  [ -z "$UNRESOLVED" ] && [ ! -e "$PREFIX.stack-start-intent" ] || fail "the instance stack is not positively stopped; nothing is settled under a manager that may be serving"
  MANAGER_STARTED=""
'''),
])
