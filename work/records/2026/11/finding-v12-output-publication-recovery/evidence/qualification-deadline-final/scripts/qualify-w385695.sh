#!/usr/bin/env bash
# W385695 package/image/engine qualification, revision 5 (reviews 2026-11-24T01-52-00Z, T03-03-48Z, T04-42-16Z and T05-49-33Z, C5).
# PREPARED, NOT EXECUTED BY ITS AUTHOR against any engine. Running an engine phase is a
# separately selected act: it builds images and starts containers. It needs no live model.
# It never replaces, edits or re-stages approved bytes.
#
#   qualify-w385695.sh images          build the five changed images under FRESH tags this run owns; identity,
#                                      content and in-image command-supervisor assertions
#   qualify-w385695.sh fixture-image   build the LABELLED scripted-provider fixture image on top of this run's
#                                      provider image (see "THE DETERMINISTIC PROVIDER" below)
#   qualify-w385695.sh preflight       check every prerequisite of the instance phases and refuse by name
#   qualify-w385695.sh recovery        inspect -> decide -> publication -> reviewer -> verdict, ONE invocation
#   qualify-w385695.sh deadline        a second recovery whose publisher is frozen past its absolute bound
#   qualify-w385695.sh cli-in-image    the REAL pinned CLI inside this run's provider image, against a scripted
#                                      endpoint on the container's own loopback, with no network at all
#   qualify-w385695.sh cleanup         remove only the image tags this run recorded, if still the recorded image
#
# The Option A instance and its two failed producers are prepared by `option-a-setup.sh` (same packet), which
# uses only the instance's supported verbs. `preflight` here proves what that left.
#
# Required environment
#   TREE       root of the imported, reviewed tree (contains v12/)
#   EVIDENCE   a directory outside TREE; `images` creates it and its run identity, later phases reuse it
# For preflight/recovery/deadline also
#   INSTANCE   the qualification instance's instance.json (installed by `just bootstrap INPUTS DEST`)
#   OWNER      the owner participant that may approve on the Work
#   JOB STAGE EPISODE DECISION                  the failed Job, its implementation stage id, episode, a fresh decision id
#   (deadline) JOB2 STAGE2 EPISODE2 DECISION2   a second failed Job of the same kind
# Optional: ENGINE (docker), ENGINE_SECONDS (60) per engine call, BUILD_SECONDS (1800) per image build,
#           OBSERVE_SECONDS (600) for the selected publisher to exist
#
# EVERY EFFECT IS ON ONE EXACTLY IDENTIFIED CONTAINER. An isolated instance is not an isolated engine: other
# Baton containers may be running on this daemon. Nothing here lists containers by a shared label and acts on
# what it finds. The attempt id is read from THIS instance's `publication-status` for THIS decision; the one
# container carrying that exact attempt label is then held to this instance's own storage roots and to the image
# identity this run built BEFORE it is paused, exec'd into or unpaused. A container that fails either check is
# recorded and left alone, and the phase fails.
#
# THE INSTALLED COMMAND IS WHAT RUNS. Every manager operation below is the instance's own bundled command
# (`<destination>/distro/baton-v12-stack manager ...`) with nothing of TREE in its environment. TREE is used to
# build images and to compare their content with the reviewed bytes, and for nothing else.
#
# THE DETERMINISTIC PROVIDER, and the capability this product does not have. An installed instance's
# implementation and review workers run the provider image, whose `claude` is the live CLI with a per-user
# credential. v12 has no deployment selection for a deterministic provider, so nothing installed can produce the
# two failed producers or a scripted review without a live model. This script does not paper over that:
#   * `fixture-image` builds `FROM` this run's provider image and replaces ONLY the `claude` program with a
#     scripted one (it writes an over-ceiling file as an implementer, a bound report as a reviewer, and runs one
#     command through the delivered CLAUDE_CODE_SHELL_PREFIX). The adapter, the worker, the command supervisor
#     and every mount are the reviewed bytes; the pinned CLI is NOT exercised in a container by it. The image is
#     labelled `baton.v12.qualification-fixture=scripted-provider` and is never tagged as the provider image.
#   * Selecting that image as the qualification instance's worker image, and creating the two Jobs, is the
#     operator's act through the instance's ordinary `manager ... create` and deployment document; `preflight`
#     then proves the result instead of assuming it.
#   * The pinned CLI's own behaviour under the shell prefix is evidenced separately, on the host, against a
#     local scripted API endpoint (correction packet `harness/cli-prefix/`).
set -euo pipefail
: "${TREE:?}" "${EVIDENCE:?}"
ENGINE="${ENGINE:-docker}"
ENGINE_SECONDS="${ENGINE_SECONDS:-60}"
BUILD_SECONDS="${BUILD_SECONDS:-1800}"
OBSERVE_SECONDS="${OBSERVE_SECONDS:-600}"   # how long the selected publisher may take to exist
phase="${1:?phase}"
TREE="$(realpath "$TREE")"
case "$(realpath -m "$EVIDENCE")/" in "$TREE"/*) echo "EVIDENCE must be outside TREE" >&2; exit 2;; esac
mkdir -p "$EVIDENCE"; EVIDENCE="$(realpath "$EVIDENCE")"
PREFIX="$EVIDENCE/$phase"
OWNED_PIDS=(); PAUSED=""; MANAGER_STARTED=""; ENDING=""; UNRESOLVED=""

say() { printf '%s %s\n' "$(date -u +%FT%TZ)" "$*" | tee -a "$EVIDENCE/qualify.log"; }
fail() { say "FAIL: $*"; exit 1; }
eng() { timeout --kill-after=10 "$ENGINE_SECONDS" "$ENGINE" "$@"; }

# -- values are compared PARSED, never as serialized text -------------------
json() {  # FILE DOTTED.PATH -> canonical JSON of the member (null when absent)
  python3 - "$1" "$2" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
for k in sys.argv[2].split("."):
    d = (d[int(k)] if isinstance(d, list) and k.isdigit() and int(k) < len(d)
         else d.get(k) if isinstance(d, dict) else None)
print(json.dumps(d, sort_keys=True))
PY
}
same() {  # JSON-TEXT JSON-TEXT -> success when the two PARSE to equal values
  python3 -c 'import json,sys; sys.exit(0 if json.loads(sys.argv[1]) == json.loads(sys.argv[2]) else 1)' "$1" "$2"
}
want() {  # FILE DOTTED.PATH EXPECTED-JSON
  local got; got="$(json "$1" "$2")"
  same "$got" "$3" || fail "$(basename "$1") $2 is $got, wanted $3"
  say "ok   $2 = $3"
}
text() { python3 -c 'import json,sys; v=json.loads(sys.argv[1]); print("" if v is None else v)' "$(json "$1" "$2")"; }

# -- processes this invocation started, and nothing else --------------------
own() { OWNED_PIDS+=("$1"); echo "$1 $2" >> "$PREFIX.owned-pids"; }
ended() {  # PID SECONDS -> wait, bounded, for an owned process to end
  local end=$(( $(date +%s) + $2 ))
  while kill -0 "$1" 2>/dev/null; do [ "$(date +%s)" -lt "$end" ] || return 1; sleep 0.2; done
}
reconcile_pause() {
  # WHAT THE WATCHER INTENDED AND WHAT IT WAS TOLD, read from its own records after it has stopped. An intent
  # is written BEFORE the engine is asked to pause and an acknowledgment after it answers, so a pause whose
  # reply was lost, and one acknowledged before this process copied the id into a variable, are both found
  # here. The id in either record was proved to be the selected attempt's container before it was written.
  local id seen="" state end open=""
  # THE PAUSE REQUEST ITSELF MUST HAVE ENDED FIRST. The watcher is gone by now, but the engine call it made is
  # its own process and records itself before it asks; a request still in flight could pause AFTER this
  # reconciliation looked. Its own bound is ENGINE_SECONDS + 10.
  if [ -s "$PREFIX.pause-intent" ] && [ ! -e "$PREFIX.pause-op-done" ]; then
    end=$(( $(date +%s) + 3 )); until op_recorded "$PREFIX.pause-op" || [ "$(date +%s)" -ge "$end" ]; do sleep 0.2; done
    if ! op_recorded "$PREFIX.pause-op"; then
      # NO READABLE RECORD OF THE REQUEST IS NOT PROOF THERE WAS NONE. What is paused now is still released
      # below; the intent stays, because a request that has not yet recorded itself may pause afterwards.
      say "UNRESOLVED: the pause intent has no readable record of its request ($PREFIX.pause-op), so the request is not known to have ended or never begun; the selected container may yet be paused; intent retained at $PREFIX.pause-intent"
      UNRESOLVED=1; open=1
    else
      end=$(( $(date +%s) + ${ENGINE_SECONDS:-60} + 20 )); while op_alive "$PREFIX.pause-op" && [ "$(date +%s)" -lt "$end" ]; do sleep 0.2; done
      if op_alive "$PREFIX.pause-op"; then
        say "UNRESOLVED: the pause request ($(cat "$PREFIX.pause-op")) has not ended; the selected container may yet be paused; intent retained at $PREFIX.pause-intent"
        UNRESOLVED=1; open=1
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
          true) say "UNRESOLVED: container $id is still paused and could not be released; intent retained at $PREFIX.pause-intent"; UNRESOLVED=1; open=1;;
          *) say "UNRESOLVED: container $id was paused and its release could not be read back; intent retained at $PREFIX.pause-intent"; UNRESOLVED=1; open=1;;
        esac;;
      false) say "cleanup: $id is positively not paused";;
      absent) say "cleanup: $id positively no longer exists; nothing to release";;
      *) say "UNRESOLVED: the pause state of $id could not be read (see $PREFIX.cleanup.log); it was NOT unpaused blind; intent retained at $PREFIX.pause-intent"; UNRESOLVED=1; open=1;;
    esac
  done
  # A PAUSE POSITIVELY SETTLED IS FILED AS THAT; one that is not keeps its intent, and `deadline` refuses over it.
  if [ -z "$open" ] && [ -e "$PREFIX.pause-intent" ]; then mv -f "$PREFIX.pause-intent" "$PREFIX.pause-reconciled"; fi
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
finish() {
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
op_recorded() {  # FILE -> success only for a readable record of exactly "pid start-tick", both numbers
  local pid tick rest
  read -r pid tick rest < "$1" 2>/dev/null || return 1
  case "$pid:$tick:$rest" in *[!0-9:]*|:*|*::*) return 1;; esac
  [ -z "$rest" ]
}
op_alive() {  # FILE holding "pid start-tick" -> success while THAT process (pid AND start time) has not ended
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
  # THE ONE STEP THIS INVOCATION CAN VOUCH FOR: between these two assignments an intent may exist and no command
  # has been forked. The second is made BEFORE the fork, so "intent-only" is never true of a forked command.
  STACK_START_STAGE=intent-only; echo "$token" > "$PREFIX.stack-start-intent"
  STACK_START_STAGE=launched
  # The recorded process outlives a signal sent to this run's whole group: it handles it and stays until the
  # start command, which `timeout` runs in a group of its own, has ended.
  ( trap : TERM INT HUP; me="$BASHPID"; echo "$me $(awk '{print $22}' "/proc/$me/stat")" > "$PREFIX.stack-start-op"
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
  #    ONLY POSITIVE EVIDENCE ENDS THIS STEP: the completion record; or the command's own record with that
  #    process positively ended; or THIS invocation knowing it wrote the intent and never forked. An intent with
  #    no readable record of its command proves nothing about a command that may yet act -- waiting is not
  #    proof -- so it stays UNRESOLVED, retained, and no new start is made over it.
  if [ ! -e "$PREFIX.stack-start-op-done" ]; then
    if [ "${STACK_START_STAGE:-}" = intent-only ]; then
      echo never-launched > "$PREFIX.stack-start-op-done"
    else
      end=$(( $(date +%s) + 3 )); until op_recorded "$PREFIX.stack-start-op" || [ "$(date +%s)" -ge "$end" ]; do sleep 0.2; done
      if ! op_recorded "$PREFIX.stack-start-op"; then
        say "UNRESOLVED: the start intent has no readable record of its start command ($PREFIX.stack-start-op), so it is not known to have ended or never begun; nothing was reconciled; intent retained at $PREFIX.stack-start-intent"
        UNRESOLVED=1; return 0
      fi
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
trap finish EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

run_id() { [ -s "$EVIDENCE/run-id" ] || fail "no run identity here: run the 'images' phase into this EVIDENCE first"; cat "$EVIDENCE/run-id"; }
owned_image() {  # NAME -> the image id this run recorded for it
  awk -v n="$1" '$1 == n { print $3 }' "$EVIDENCE/images.owned" 2>/dev/null | tail -1
}

# -- images -----------------------------------------------------------------
built() {  # NAME RECIPE CONTEXT  -> a fresh tag this run owns, recorded with its image id
  local name="$1" tag="baton-v12-$1:w385695-$RUN" recipe="$TREE/v12/$2" existing actual base
  existing="$(owned_image "$name")"
  if [ -n "$existing" ]; then
    actual="$(eng image inspect --format '{{.Id}}' "$tag")" || fail "cannot verify retained $name"
    [ "$actual" = "$existing" ] || fail "retained $name tag drift"
    say "reuse recorded $name $existing"
    return 0
  fi
  case "$name" in
    integration|reconciliation)
      base="$(owned_image provider)"
      [[ "$base" =~ ^sha256:[0-9a-f]{64}$ ]] || fail "missing exact provider base"
      mkdir -p "$EVIDENCE/recipes"
      python3 - "$recipe" "$EVIDENCE/recipes/Dockerfile.$name" "$base" <<'PYBASE'
import hashlib, json, pathlib, sys
source, destination = map(pathlib.Path, sys.argv[1:3]); base = sys.argv[3]
text = source.read_text(); needle = 'FROM ${PROVIDER_BASE}'
assert text.count(needle) == 1
resolved = text.replace(needle, 'FROM ' + base)
destination.write_text(resolved)
destination.with_suffix(destination.suffix + '.json').write_text(json.dumps({'source': str(source), 'source_sha256': hashlib.sha256(text.encode()).hexdigest(), 'provider_base': base, 'resolved_sha256': hashlib.sha256(resolved.encode()).hexdigest(), 'change': 'resolve required FROM operand only'}, indent=2) + '\n')
PYBASE
      recipe="$EVIDENCE/recipes/Dockerfile.$name";;
  esac
  if eng image inspect "$tag" > /dev/null 2>&1; then fail "tag $tag already exists; this run owns only tags it created"; fi
  say "build $name from $2"
  ( cd "$TREE/v12/python" && timeout --kill-after=30 "$BUILD_SECONDS" env PYTHONPATH=src:. \
      "$(python3 -m tools.environment interpreter)" -m tools.worker_image --engine "$ENGINE" --tag "$tag" \
      --dockerfile "$recipe" --context "$TREE/v12/$3" ) | tee "$EVIDENCE/image-$name.identity"
  local id; id="$(eng image inspect --format '{{.Id}}' "$tag")"
  # THE IDENTITY THE BUILD TOOL ANSWERED IS THE ONE THE ENGINE HOLDS UNDER THE TAG. It is what a deployment
  # names as a worker's image digest and what a container of it reports as its image.
  grep -qx "$id" "$EVIDENCE/image-$name.identity" || fail "$name: the build tool answered $(tail -1 "$EVIDENCE/image-$name.identity") and the engine holds $id under $tag"
  echo "$name $tag $id" >> "$EVIDENCE/images.owned"
  eng image inspect "$tag" > "$EVIDENCE/image-$name.inspect.json"
}
inside() {  # NAME PROGRAM ARGV... -> run one bounded, networkless, read-only program in this run's image
  local name="$1" program="$2"; shift 2
  eng run --rm --network none --read-only --cap-drop ALL --security-opt no-new-privileges --pids-limit 512 \
    --tmpfs /tmp:rw,nosuid,nodev,size=16m --entrypoint "$program" "$(owned_image "$name")" "$@"
}
reviewed_bytes() {  # NAME FILE-IN-IMAGE SOURCE-UNDER-v12
  local got; got="$(inside "$1" python3 -c "import hashlib;print(hashlib.sha256(open('/opt/baton/$2','rb').read()).hexdigest())")"
  [ "$got" = "$(sha256sum "$TREE/v12/$3" | cut -d' ' -f1)" ] || fail "$1: /opt/baton/$2 is not the reviewed v12/$3"
  say "ok   $1 /opt/baton/$2 = reviewed bytes $got"
}
images() {
  if [ -e "$EVIDENCE/run-id" ]; then
    [ "${RESUME_IMAGES:-}" = 1 ] || fail "existing run requires explicit RESUME_IMAGES=1"
    RUN="$(run_id)"; [ -s "$EVIDENCE/images.owned" ] || fail "missing prior image records"
  else
    RUN="$(date -u +%Y%m%dT%H%M%SZ)-$$"; echo "$RUN" > "$EVIDENCE/run-id"; : > "$EVIDENCE/images.owned"
  fi
  built reference worker/Dockerfile worker
  built provider worker/Dockerfile.claude .
  built integration worker/Dockerfile.integration .
  built reconciliation worker/Dockerfile.reconciliation .
  built publication worker/Dockerfile.publication worker
  local name
  for name in reference provider integration reconciliation publication; do reviewed_bytes "$name" baton_worker.py worker/baton_worker.py; done
  for name in provider integration; do reviewed_bytes "$name" claude_agent.py worker/claude_agent.py; done
  reviewed_bytes publication publication_entry.py worker/publication_entry.py
  reviewed_bytes provider bounded_command.py worker/bounded_command.py
  # THE COMMAND SUPERVISOR, IN THE IMAGE THE REVIEWER RUNS IN: executable, not writable by the worker, and it
  # ends a command and its detached descendant at the bound under the container's own restrictions.
  inside provider python3 -c "
import json, os, stat, subprocess, tempfile, time
p = '/opt/baton/bounded_command.py'; s = os.stat(p)
assert stat.S_ISREG(s.st_mode) and os.access(p, os.X_OK) and not os.access(p, os.W_OK), oct(s.st_mode)
d = tempfile.mkdtemp(); began = time.monotonic()
r = subprocess.run([p, 'setsid sleep 300 & echo \$! > %s/pid; sleep 300' % d], env={'PATH': os.environ['PATH'],
    'BATON_COMMAND_SECONDS': '1', 'BATON_COMMAND_DEADLINE': repr(time.monotonic() + 60), 'BATON_COMMAND_LEDGER': d})
record = [json.load(open(os.path.join(d, n))) for n in os.listdir(d) if n.endswith('.json')][0]
print(json.dumps({'status': r.returncode, 'outcome': record['outcome'], 'descendants_gone': record['descendants_gone'],
    'detached_alive': os.path.exists('/proc/' + open(d + '/pid').read().strip()), 'seconds': round(time.monotonic() - began, 1)}))
" > "$EVIDENCE/image-provider.supervisor.json"
  want "$EVIDENCE/image-provider.supervisor.json" status 124
  want "$EVIDENCE/image-provider.supervisor.json" outcome '"timed-out"'
  want "$EVIDENCE/image-provider.supervisor.json" descendants_gone true
  want "$EVIDENCE/image-provider.supervisor.json" detached_alive false
  local pub="$EVIDENCE/image-publication.inspect.json"
  want "$pub" 0.Config.Entrypoint '["python3", "/opt/baton/publication_entry.py"]'
  want "$pub" 0.Config.User '"65532:65532"'
  python3 - "$pub" <<'PY' || fail "publication image carries a provider or credential variable"
import json, sys
env = json.load(open(sys.argv[1]))[0]["Config"].get("Env") or []
sys.exit(1 if any(k.split("=")[0].startswith(("ANTHROPIC", "CLAUDE", "BATON_WORKER")) or "CREDENTIAL" in k.split("=")[0] for k in env) else 0)
PY
  say "ok   publication image environment names no provider or credential"
  inside publication python3 -c "import json,os;print(json.dumps({'files': sorted(os.listdir('/opt/baton')), 'uid': os.getuid(), 'gid': os.getgid()}))" \
    > "$EVIDENCE/image-publication.content.json"
  want "$EVIDENCE/image-publication.content.json" files '["baton_worker.py", "publication_entry.py", "worker-control-1.0.schema.json"]'
  want "$EVIDENCE/image-publication.content.json" uid 65532
  want "$EVIDENCE/image-publication.content.json" gid 65532
  cat > "$EVIDENCE/per-image-gates.txt" <<EOF
PER-IMAGE ACCEPTANCE. Each rebuilt image is accepted by the engine gates that already consume it, run from
$TREE/v12/python with the identity recorded in images.owned selected. These are separately selected runs.
  reference       $(owned_image reference)
      BATON_V12_LIFECYCLE_IMAGE=<id> BATON_V12_WORKER_ENTRY_IMAGE=<id> just test-group manager-engine
  provider        $(owned_image provider)
      the dogfood engine gates in manager-engine (tests.manager.test_dogfood_image) build and ask this recipe's artefact
  integration     $(owned_image integration)
      tests.manager.test_integration_image (manager-engine)
  reconciliation  $(owned_image reconciliation)
      the reconciliation image gate in manager-engine
  publication     $(owned_image publication)
      this script's 'recovery' and 'deadline' phases, with this identity as the deployment's publication worker image
EOF
  say "images: identities in images.owned; per-image gates in per-image-gates.txt"
}

# THE OUTPUT CEILING THE TWO PRODUCERS ARE MADE TO EXCEED. An ordinary Job's proposal is admitted under
# `role_contract.MAX_OUTPUT_BYTES`; the recovery is for an original over that and inside the corrective
# declaration (`publication_recovery`). The fixture writes this many bytes over it. `pinned_ceiling` holds the
# number to the reviewed tree, so a ceiling that moves is a refusal and not a producer that quietly succeeds.
ORIGINAL_CEILING=1048576
FIXTURE_OVER=4096
pinned_ceiling() {
  ( cd "$TREE/v12/python" && env PYTHONPATH=src:. python3 - "$ORIGINAL_CEILING" "$FIXTURE_OVER" <<'PY'
import sys
from baton_v12.job_manager import publication_recovery, role_contract
ceiling, over = int(sys.argv[1]), int(sys.argv[2])
assert role_contract.MAX_OUTPUT_BYTES == ceiling == publication_recovery.ORIGINAL_PROPOSAL_BYTES, "the ordinary proposal ceiling moved"
assert ceiling + over <= publication_recovery.corrective_declaration()["output"]["constraints"]["max_bytes"], "the fixture output does not fit the corrective declaration"
PY
  ) || fail "the pinned output ceiling $ORIGINAL_CEILING is not the reviewed tree's"
  say "ok   ordinary proposal ceiling is $ORIGINAL_CEILING bytes; the fixture writes $((ORIGINAL_CEILING + FIXTURE_OVER))"
}
fixture_image() {
  RUN="$(run_id)"
  pinned_ceiling
  local base; base="$(owned_image provider)"; [ -n "$base" ] || fail "this run built no provider image"
  local user; user="$(eng image inspect --format '{{.Config.User}}' "$base")"; [ -n "$user" ] || fail "the provider image names no runtime user"
  local work; work="$(mktemp -d "$EVIDENCE/fixture-image.XXXXXX")"
  cat > "$work/claude" <<SCRIPTED
#!/usr/bin/python3
"""QUALIFICATION FIXTURE, NOT A PROVIDER: a scripted program standing where the CLI stands. No model."""
import json, os, subprocess, sys
if os.path.exists(".git"):
    open("big.txt", "w").write("x" * ($ORIGINAL_CEILING + $FIXTURE_OVER))   # an implementer whose output is over its ceiling
else:
    recovery = json.load(open("/input/recovery-review.json"))
    prefix = os.environ.get("CLAUDE_CODE_SHELL_PREFIX")
    ran = subprocess.run([prefix, "true"]).returncode if prefix else None   # one command through the supervisor
    json.dump({"schema": "baton.review-report/1", "verdict": "accepted",
               "findings": f"Scripted qualification review; one supervised command exited {ran}.",
               "recovery_digest": recovery["handoff_digest"]}, open("review-report.json", "w"))
print(json.dumps({"type": "result", "subtype": "success", "is_error": False, "result": "scripted"}))
SCRIPTED
  # INSTALLED AS ROOT, RUN AS THE PROVIDER IMAGE'S OWN USER. The provider recipe ends as an unprivileged user,
  # which may neither replace a root-owned program nor change its mode; so the derivative installs as root and
  # then RESTORES the exact user the base declares. Only the `claude` program differs from the base.
  cat > "$work/Dockerfile" <<RECIPE
FROM $base
LABEL baton.v12.qualification-fixture=scripted-provider
USER 0:0
RUN rm -f /usr/local/bin/claude
COPY --chown=0:0 claude /usr/local/bin/claude
RUN chmod 0555 /usr/local/bin/claude
USER $user
RECIPE
  local tag="baton-v12-qualification-fixture:w385695-$RUN"
  if eng image inspect "$tag" > /dev/null 2>&1; then fail "tag $tag already exists"; fi
  timeout --kill-after=30 "$BUILD_SECONDS" "$ENGINE" build -t "$tag" "$work" > "$EVIDENCE/fixture-image.build.log" 2>&1 || fail "fixture image build failed"
  echo "fixture $tag $(eng image inspect --format '{{.Id}}' "$tag")" >> "$EVIDENCE/images.owned"
  eng image inspect "$tag" > "$EVIDENCE/image-fixture.inspect.json"
  want "$EVIDENCE/image-fixture.inspect.json" 0.Config.User "\"$user\""
  [ "$(eng image inspect --format '{{index .Config.Labels "baton.v12.qualification-fixture"}}' "$tag")" = scripted-provider ] \
    || fail "the fixture image does not carry its label"
  # ONLY THE PROVIDER PROGRAM DIFFERS: everything under /opt/baton is byte-identical to the provider image's,
  # the scripted program is the one the adapter's PATH resolves, the runtime user cannot write it, and the
  # runtime user is the provider image's.
  local probe='import hashlib,json,os,shutil
P="/usr/local/bin:/usr/bin:/bin"
print(json.dumps({"opt":{n:hashlib.sha256(open("/opt/baton/"+n,"rb").read()).hexdigest() for n in sorted(os.listdir("/opt/baton")) if os.path.isfile("/opt/baton/"+n)},"claude":shutil.which("claude",path=P),"claude_sha256":hashlib.sha256(open(shutil.which("claude",path=P),"rb").read()).hexdigest(),"writable":os.access(shutil.which("claude",path=P),os.W_OK),"uid":os.getuid()}))'
  inside provider python3 -c "$probe" > "$EVIDENCE/image-provider.content.json"
  inside fixture python3 -c "$probe" > "$EVIDENCE/image-fixture.content.json"
  same "$(json "$EVIDENCE/image-provider.content.json" opt)" "$(json "$EVIDENCE/image-fixture.content.json" opt)" || fail "the fixture image changed something under /opt/baton"
  want "$EVIDENCE/image-fixture.content.json" claude '"/usr/local/bin/claude"'
  want "$EVIDENCE/image-fixture.content.json" claude_sha256 "\"$(sha256sum "$work/claude" | cut -d' ' -f1)\""
  want "$EVIDENCE/image-fixture.content.json" writable false
  same "$(json "$EVIDENCE/image-provider.content.json" uid)" "$(json "$EVIDENCE/image-fixture.content.json" uid)" || fail "the fixture image runs as another user"
  say "fixture-image: $(owned_image fixture) -- a LABELLED scripted stand-in for the provider program only"
}

# -- the real pinned CLI, inside this run's provider image -------------------
cli_in_image() {
  # NEITHER THE SUPERVISOR SELF-CHECK NOR THE FIXTURE IMAGE EXERCISES THE REAL CLI IN A CONTAINER. This does:
  # the provider image's own `claude` (the pinned build) is started by `cli-in-image-driver.py` INSIDE one
  # container with NO NETWORK, against a scripted endpoint on that container's loopback, with the image's own
  # /opt/baton/bounded_command.py as its shell prefix. No model, no credential, no instance, no other container.
  RUN="$(run_id)"
  local here; here="$(dirname "$(realpath "$0")")"
  [ -f "$here/harness/cli-prefix/stub.py" ] && [ -f "$here/cli-in-image-driver.py" ] || fail "run this from the packet: the scripted endpoint and the driver are beside this script"
  local pinned; pinned="$(sed -n 's/^ARG CLAUDE_VERSION=//p' "$TREE/v12/worker/Dockerfile.claude")"; [ -n "$pinned" ] || fail "the recipe pins no CLI version"
  timeout --kill-after=30 600 "$ENGINE" run --rm --network none --read-only --cap-drop ALL --security-opt no-new-privileges --pids-limit 512 \
    --tmpfs /tmp:rw,nosuid,nodev,exec,size=256m -v "$here/harness/cli-prefix/stub.py:/qualify/stub.py:ro" -v "$here/cli-in-image-driver.py:/qualify/driver.py:ro" \
    --entrypoint python3 "$(owned_image provider)" /qualify/driver.py --stub /qualify/stub.py --supervisor /opt/baton/bounded_command.py --work /tmp/qualify \
    > "$EVIDENCE/cli-in-image.json" 2> "$EVIDENCE/cli-in-image.err" || fail "the in-image CLI check did not complete; see cli-in-image.err"
  want "$EVIDENCE/cli-in-image.json" cli_version "\"$pinned\""
  want "$EVIDENCE/cli-in-image.json" supervisor_sha256 "\"$(sha256sum "$TREE/v12/worker/bounded_command.py" | cut -d' ' -f1)\""
  want "$EVIDENCE/cli-in-image.json" verdict '"pass"'
  say "cli-in-image: the pinned CLI $pinned in $(owned_image provider) hands every scripted shell-tool command to the image's supervisor"
}

# -- the instance, through its own installed command ------------------------
stores() {
  : "${INSTANCE:?}" "${OWNER:?}"
  RUN="$(run_id)"
  eval "$(python3 - "$INSTANCE" <<'PY'
import json, shlex, sys
s = json.load(open(sys.argv[1])); d = s["destination"]
deployment = json.load(open(s["deployment"]))
roots = {w["deployment"]["workspace_storage"] for w in deployment["workers"]}
if len(roots) != 1: raise SystemExit("qualification workers must share one configured storage root")
storage = roots.pop()
# THE INSTALLED LAYOUT, as `tools.instance.layout` derives it from the one destination: the stores are under
# `db/`, the runtime under `distro/`, the stack's process records under `state/`. Below, these are held to the
# reviewed tree's own `layout()` answer, so a layout that moves is a refusal here and not a wrong path.
for k, v in (("DEST", d), ("CMD", d + "/distro/baton-v12-stack"), ("JOBS", s["job_store"]), ("CONTROL", s["control_store"]),
             ("UUID", s["authority_uuid"]), ("AUTHORITY", d + "/db/authority.sqlite3"), ("STACK_STATE", d + "/state"),
             ("STORAGE", storage)):
    print(f"{k}={shlex.quote(str(v))}")
PY
)"
  [ -x "$CMD" ] || fail "the instance's installed command $CMD is missing"
  case "$CMD" in "$TREE"/*) fail "the instance command is inside TREE; that is not an installed bundle";; esac
  local store
  for store in "$JOBS" "$CONTROL" "$AUTHORITY"; do [ -f "$store" ] || fail "the instance store $store does not exist"; done
  if [ -d "$TREE/v12/python/tools" ]; then
    ( cd "$TREE/v12/python" && env PYTHONPATH=src:. python3 - "$DEST" "$CMD" "$JOBS" "$CONTROL" "$AUTHORITY" "$STACK_STATE" <<'PY'
import sys
from tools import instance
want = instance.layout(sys.argv[1])
got = dict(zip(("command", "job_store", "control_store", "authority_store", "state"), sys.argv[2:]))
wrong = {k: (v, want[k]) for k, v in got.items() if v != want[k]}
sys.exit("layout disagrees with tools.instance.layout: %r" % wrong if wrong else 0)
PY
    ) || fail "this script's installed paths are not the reviewed tree's instance layout"
  fi
  COMMON=(--store "$JOBS" --authority-uuid "$UUID" --incarnation "qualify-$RUN" --control "$CONTROL" --authority "$AUTHORITY" --instance "$DEST")
}
# NOTHING OF THE CHECKOUT IN ITS ENVIRONMENT, as tests/tools/test_packaged_creation runs it.
manager() { ( cd / && env -i HOME="$EVIDENCE/home" PATH="/usr/local/bin:/usr/bin:/bin" "$CMD" manager "$@" ); }
status() { manager publication-status --store "$JOBS" --authority-uuid "$UUID" --incarnation "qualify-$RUN" --control "$CONTROL" --decision-id "$1" > "$2.tmp" && mv "$2.tmp" "$2"; }

preflight_checks() {  # JOB STAGE EPISODE PREFIX
  mkdir -p "$EVIDENCE/home"
  "$CMD" identity > "$4.identity.json" 2>&1 || fail "the installed command does not answer 'identity'"
  want "$4.identity.json" frozen true
  # WHAT THE STACK SAYS OF ITSELF, kept as evidence. Whether a manager was already running is decided where it
  # can be decided -- at `serve`, from the start command's own "already running" answer -- not guessed here.
  timeout --kill-after=10 60 just --justfile "$DEST/justfile" status > "$4.stack-status.txt" 2>&1 || true
  # EVERY PROVIDER ROLE RUNS THE LABELLED FIXTURE, AND NOTHING ELSE. A worker of an implementation or review
  # role on any other image -- this run's real provider image included -- would reach for a live provider, so it
  # is refused here by worker id. The publication worker runs this run's publication image.
  python3 - "$DEST/deployment.json" "$EVIDENCE/images.owned" <<'PY' || fail "the deployment's worker images are not this run's Option A selection"
import json, sys
deployment = json.load(open(sys.argv[1]))
owned = {line.split()[0]: line.split()[2] for line in open(sys.argv[2]) if line.strip()}
wrong, roles = [], set()
for worker in deployment.get("workers", []):
    role, image = worker.get("role"), (worker.get("deployment") or {}).get("image_digest")
    roles.add(role)
    need = owned.get("publication") if role == "publication" else owned.get("fixture")
    if need is None or image != need:
        wrong.append(f"{worker.get('worker_id')} ({role}) runs {image}, wanted {need}")
missing = sorted({"implementation", "review", "publication"} - roles)
if wrong or missing:
    print("; ".join(wrong + ["no worker of role " + r for r in missing]), file=sys.stderr); sys.exit(1)
PY
  say "ok   implementation and review workers run the labelled fixture image; the publication worker runs this run's publication image"
  manager publication-inspect "${COMMON[@]}" --job "$1" --stage "$2" --episode "$3" --participant "$OWNER" > "$4.inspect.json" \
    || fail "publication-inspect refused Job $1; see $4.inspect.json"
  want "$4.inspect.json" eligible true
  # THE INTENDED FAILURE, NOT AN ASSUMED ONE: the retained original is over the ordinary ceiling its producer
  # was admitted under and inside the corrective declaration.
  want "$4.inspect.json" output.exceeded true
  want "$4.inspect.json" output.fits_corrective true
}
preflight() {
  : "${JOB:?}" "${STAGE:?}" "${EPISODE:?}"; stores
  preflight_checks "$JOB" "$STAGE" "$EPISODE" "$PREFIX-1"
  if [ -n "${JOB2:-}" ]; then preflight_checks "$JOB2" "${STAGE2:?}" "${EPISODE2:?}" "$PREFIX-2"; fi
  say "preflight: every checked prerequisite holds"
}

# -- one exactly identified container ---------------------------------------
selected() {  # ATTEMPT ROLE-IMAGE-NAME... -> the id of THE container of this attempt, proved this instance's; else empty
  local attempt="$1"; shift
  local ids; ids="$(eng ps -aq --no-trunc --filter "label=baton.v12.runtime_attempt_id=$attempt" 2>/dev/null)" || return 1
  [ -n "$ids" ] || return 1
  [ "$(printf '%s\n' "$ids" | wc -l)" = 1 ] || { say "REFUSED: $(printf '%s\n' "$ids" | wc -l) containers carry attempt $attempt"; return 2; }
  eng inspect "$ids" > "$PREFIX.container-$attempt.json" 2>/dev/null || return 1
  local images=""; local name
  for name in "$@"; do images="$images $(owned_image "$name")"; done
  python3 - "$PREFIX.container-$attempt.json" "$attempt" "$DEST" "$STORAGE" $images <<'PY' || { say "REFUSED: container $ids is not provably this instance's attempt $attempt"; return 2; }
import json, os, sys
c = json.load(open(sys.argv[1]))[0]; attempt, roots, images = sys.argv[2], [os.path.realpath(p) for p in sys.argv[3:5]], sys.argv[5:]
assert c["Config"]["Labels"].get("baton.v12.runtime_attempt_id") == attempt, "label"
assert c["Image"] in images, f"image {c['Image']} is not one this run built"
binds = [m["Source"] for m in c["Mounts"] if m["Type"] == "bind"]
assert binds, "no bind mounts"
outside = [s for s in binds if not any(os.path.realpath(s) == r or os.path.realpath(s).startswith(r + os.sep) for r in roots)]
assert not outside, f"mounts outside this instance: {outside}"
PY
  printf '%s' "$ids"
}
attempt_of() {  # DECISION MEMBER(publication_attempt|review) -> the attempt id this instance records, or empty
  # ITS OWN FILE: the watcher and the phase both ask, and neither reads the other's half-written answer.
  status "$1" "$PREFIX.watch-status.json" 2>/dev/null || return 0
  text "$PREFIX.watch-status.json" "$2.attempt_id"
}
note_attempt() { grep -qx "$1" "$PREFIX.selected-attempts" 2>/dev/null || echo "$1" >> "$PREFIX.selected-attempts"; }

watch() {  # DECISION ACTION("observe"|"freeze-publisher") -- runs in THIS invocation, ends with it
  local decision="$1" action="$2" publisher="" reviewer="" probed="" id
  while [ -e "$PREFIX.watching" ]; do
    if [ -z "$publisher" ]; then
      publisher="$(attempt_of "$decision" publication_attempt)"
      [ -z "$publisher" ] || note_attempt "$publisher"
    fi
    if [ -n "$publisher" ] && [ ! -e "$PREFIX.publisher-seen" ]; then
      if id="$(selected "$publisher" publication)"; then
        echo "$id" > "$PREFIX.publisher-seen"
        if [ "$action" = freeze-publisher ]; then
          # INTENT, THEN THE EFFECT, THEN THE ACKNOWLEDGMENT. `finish` reconciles from these two records.
          # The request is its OWN process and records itself before it asks, so one that outlives this
          # watcher is still found and waited for.
          rm -f "$PREFIX.pause-op" "$PREFIX.pause-op-done"
          echo "$id" > "$PREFIX.pause-intent"
          ( trap : TERM INT HUP; me="$BASHPID"; echo "$me $(awk '{print $22}' "/proc/$me/stat")" > "$PREFIX.pause-op"
            eng pause "$id" >> "$PREFIX.watch.log" 2>&1 ) &
          if wait $!; then echo "$id" > "$PREFIX.paused"; else echo "pause-unacknowledged $id" >> "$PREFIX.watch.log"; fi
          : > "$PREFIX.pause-op-done"
        fi
      fi
    fi
    if [ "$action" = observe ] && [ -z "$reviewer" ]; then
      reviewer="$(attempt_of "$decision" review)"
      [ -z "$reviewer" ] || note_attempt "$reviewer"
    fi
    if [ -n "$reviewer" ] && [ -z "$probed" ]; then
      if id="$(selected "$reviewer" provider fixture)"; then
        probed=1
        # WHAT THE REVIEWER WAS DELIVERED, and whether it can write the reviewed source. The probe answers a
        # STRUCTURED result from inside; an exec that failed or a container that vanished answers nothing and
        # is recorded as that, never as a refusal.
        eng exec "$id" python3 -c "
import errno, json, os, stat
out = {}
s = os.lstat('/input/recovery-review.json'); d = json.load(open('/input/recovery-review.json'))
out['input'] = {'regular': stat.S_ISREG(s.st_mode), 'reviewer_verification': d.get('reviewer_verification'), 'handoff_digest': d['handoff_digest']}
try:
    open('/input/source/qualify-probe', 'w').close(); os.unlink('/input/source/qualify-probe'); out['write'] = 'wrote'
except OSError as refused:
    out['write'] = 'refused:' + errno.errorcode.get(refused.errno, str(refused.errno))
out['supervisor'] = {'executable': os.access('/opt/baton/bounded_command.py', os.X_OK), 'writable': os.access('/opt/baton/bounded_command.py', os.W_OK)}
print(json.dumps(out))" > "$PREFIX.reviewer-probe.json" 2> "$PREFIX.reviewer-probe.err" \
          || echo '{"write": "exec-failed"}' > "$PREFIX.reviewer-probe.json"
      fi
    fi
    sleep 0.5
  done
}
events() {  # every engine event of containers carrying ANY label is NOT wanted: subscribe per selected attempt
  local attempt="$1"
  timeout --kill-after=10 "${EVENT_SECONDS:-7200}" "$ENGINE" events --filter type=container \
    --filter "label=baton.v12.runtime_attempt_id=$attempt" --format '{{json .}}' >> "$PREFIX.events-$attempt.jsonl" &
  own $! "events:$attempt"
}

decide() {  # JOB STAGE EPISODE DECISION
  manager publication-inspect "${COMMON[@]}" --job "$1" --stage "$2" --episode "$3" --participant "$OWNER" > "$PREFIX.inspect.json"
  want "$PREFIX.inspect.json" eligible true
  mapfile -t argv < <(python3 - "$PREFIX.inspect.json" <<'PY'
import json, sys
r = json.load(open(sys.argv[1]))
out = ["--expect-attempt=" + r["selector"]["attempt_id"], "--expect-selection-digest=" + r["selection_digest"],
       "--expect-candidate-base=" + r["producer"]["base"], "--expect-candidate-head=" + r["producer"]["head"],
       "--expect-output-digest=" + r["output"]["tree_digest"], "--expect-output-bytes=" + str(r["output"]["total_bytes"]),
       "--expect-producer-status=0", "--context-digest=" + r["producer"]["context_digest"],
       "--declaration-digest=" + r["declaration"]["digest"], "--profile=" + r["profile"]["profile"],
       "--profile-digest=" + r["profile"]["digest"]]
out += ["--producer-verification=" + w for w in r["producer"]["argv"]]
out += ["--stage-word=publication", "--stage-word=review"]
print("\n".join(out))
PY
)
  manager publication-decide "${COMMON[@]}" --job "$1" --stage "$2" --episode "$3" --approve \
    "--participant=$OWNER" "--decision-id=$4" "${argv[@]}" > "$PREFIX.decide.json"
  want "$PREFIX.decide.json" admitted true
  # THE APPROVED BYTES ARE NEVER TOUCHED AGAIN: the same inspection reads the same original afterwards.
  manager publication-inspect "${COMMON[@]}" --job "$1" --stage "$2" --episode "$3" --participant "$OWNER" > "$PREFIX.inspect-after.json"
  same "$(json "$PREFIX.inspect.json" output.tree_digest)" "$(json "$PREFIX.inspect-after.json" output.tree_digest)" || fail "the original changed after approval"
}
stack_live() {  # [TOKEN] -> "name pid" per LIVE process of the instance's stack; status 3 when that cannot be told
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
serve() {
  # See `start_stack`: refused over a stack that is running or cannot be told; the intent is recorded before the
  # effect; and whatever this start left is reconciled by `finish` on every exit.
  start_stack "$PREFIX.manager-start.log"
}
until_status() {  # DECISION DOTTED.PATH EXPECTED-JSON SECONDS
  local end=$(( $(date +%s) + $4 )) next_report=0
  while [ "$(date +%s)" -lt "$end" ]; do
    if status "$1" "$PREFIX.status.json" 2>/dev/null; then
      if same "$(json "$PREFIX.status.json" "$2")" "$3"; then say "ok   $2 = $3"; return 0; fi
      if [ "$2" = review.state ]; then
        case "$(text "$PREFIX.status.json" review.state)" in
          settlement-expired|claim-refused|expired|cancelled|exceptional|failed|rejected)
            fail "review ended without the requested result: $(text "$PREFIX.status.json" review.state); retained status: $PREFIX.status.json";;
        esac
      fi
    fi
    if [ "$(date +%s)" -ge "$next_report" ]; then
      say "waiting: $2 = $(json "$PREFIX.status.json" "$2" 2>/dev/null || echo unknown); remaining $((end - $(date +%s)))s; $PREFIX.status.json"
      next_report=$(( $(date +%s) + 30 ))
    fi
    sleep 5
  done
  fail "$2 did not become $3 within $4 s (last: $(json "$PREFIX.status.json" "$2" 2>/dev/null))"
}
gone() {  # ATTEMPT -> fail unless no container carries this exact attempt
  local left; left="$(eng ps -aq --filter "label=baton.v12.runtime_attempt_id=$1")" || fail "the engine did not answer for attempt $1"
  [ -z "$left" ] || fail "a container of attempt $1 still exists"
}
ending_of() {  # ATTEMPT -> the exit code in this attempt's own die event
  python3 - "$PREFIX.events-$1.jsonl" <<'PY'
import json, sys
codes = [json.loads(line)["Actor"]["Attributes"].get("exitCode") for line in open(sys.argv[1]) if line.strip() and json.loads(line).get("Action") == "die"]
print(codes[-1] if codes else "")
PY
}

recovery() {
  : "${JOB:?}" "${STAGE:?}" "${EPISODE:?}" "${DECISION:?}"; stores
  preflight_checks "$JOB" "$STAGE" "$EPISODE" "$PREFIX-preflight"
  decide "$JOB" "$STAGE" "$EPISODE" "$DECISION"
  touch "$PREFIX.watching"; watch "$DECISION" observe & own $! watch
  serve
  until_status "$DECISION" recovery.handed_off true 1200
  want "$PREFIX.status.json" recovery.outcome '"published"'
  want "$PREFIX.status.json" publication_attempt.recorded.execution_runtime '"destroyed"'
  local attempt; attempt="$(text "$PREFIX.status.json" publication_attempt.attempt_id)"
  [ -s "$PREFIX.publisher-seen" ] || fail "the publisher container of attempt $attempt was not observed"
  local seen="$PREFIX.container-$attempt.json"
  python3 "/home/sl/src/baton/work/records/2026/11/finding-v12-output-publication-recovery/evidence/qualification-deadline-final/scripts/verify-publisher.py" "$seen" "$INSTANCE" "$attempt" || fail "publisher runtime posture differs from its configuration"
  gone "$attempt"; say "ok   publisher container of $attempt is gone after custody"
  # THE REVIEWER, in the same invocation: delivery, read-only source, its supervised verification, its verdict.
  until_status "$DECISION" review.state '"completed"' 4800
  want "$PREFIX.status.json" review.verdict.candidate_is_the_approved_original true
  say "verdict: $(json "$PREFIX.status.json" review.verdict.disposition) by $(json "$PREFIX.status.json" review.reviewer)"
  [ -s "$PREFIX.reviewer-probe.json" ] || fail "the reviewer container was not observed"
  # THE PROBE'S OWN ANSWER FIRST: an exec that failed, or a container that vanished, answered nothing about
  # the mount and is reported as that -- never read as a refusal, and never as a missing input either.
  local wrote; wrote="$(text "$PREFIX.reviewer-probe.json" write)"
  case "$wrote" in
    refused:EROFS|refused:EACCES|refused:EPERM) say "ok   /input/source refuses a write from the reviewer container ($wrote)";;
    wrote) fail "the reviewer could write into /input/source";;
    *) fail "the reviewer probe did not answer ($wrote; see $PREFIX.reviewer-probe.err); an exec failure is not a refusal";;
  esac
  want "$PREFIX.reviewer-probe.json" input.regular true
  want "$PREFIX.reviewer-probe.json" input.reviewer_verification '{"required": true, "command_seconds": 900}'
  want "$PREFIX.reviewer-probe.json" supervisor.executable true
  want "$PREFIX.reviewer-probe.json" supervisor.writable false
  gone "$(text "$PREFIX.status.json" review.attempt_id)"; say "ok   reviewer container is gone after its verdict"
}

deadline() {
  : "${JOB2:?}" "${STAGE2:?}" "${EPISODE2:?}" "${DECISION2:?}"; stores
  [ ! -e "$PREFIX.pause-intent" ] || fail "an earlier pause of this phase is not reconciled ($PREFIX.pause-intent); it is reconciled now and nothing new is frozen over it"
  preflight_checks "$JOB2" "$STAGE2" "$EPISODE2" "$PREFIX-preflight"
  decide "$JOB2" "$STAGE2" "$EPISODE2" "$DECISION2"
  # THE APPROVED BYTES AND THE 900-SECOND PROFILE ARE UNCHANGED. The one selected publisher is frozen by the
  # engine when it exists and released only after the manager's own clock reports the absolute bound reached.
  touch "$PREFIX.watching"; watch "$DECISION2" freeze-publisher & own $! watch
  serve
  local end=$(( $(date +%s) + OBSERVE_SECONDS ))
  until [ -s "$PREFIX.paused" ]; do [ "$(date +%s)" -lt "$end" ] || fail "the selected publisher was never observed and frozen"; sleep 1; done
  PAUSED="$(cat "$PREFIX.paused")"
  local attempt; attempt="$(head -1 "$PREFIX.selected-attempts")"
  events "$attempt"
  until_status "$DECISION2" recovery.publication_deadline.reached true 1200
  case "$(pause_state "$PAUSED")" in
    true) eng unpause "$PAUSED" >> "$PREFIX.watch.log" 2>&1 || fail "the frozen publisher could not be released; cleanup reads its state back";;
    false) say "note: the publisher is no longer paused";;
    absent) say "note: the publisher was already ended by the manager while frozen";;
    *) fail "the frozen publisher's pause state could not be read; cleanup tries again and retains what it cannot confirm";;
  esac
  until_status "$DECISION2" recovery.outcome '"expired"' 300
  until_status "$DECISION2" recovery.settled true 300
  want "$PREFIX.status.json" recovery.published false
  want "$PREFIX.status.json" recovery.review '"blocked"'
  want "$PREFIX.status.json" owner_item.outcome '"expired"'
  want "$PREFIX.status.json" owner_item.automatic_retry false
  want "$PREFIX.status.json" publication_attempt.recorded.execution_runtime '"destroyed"'
  same "\"$attempt\"" "$(json "$PREFIX.status.json" publication_attempt.attempt_id)" || fail "the frozen container was not this recovery's publisher"
  gone "$attempt"
  local code; code="$(ending_of "$attempt")"
  case "$code" in 75|137|143) say "ok   expired publisher $attempt ended with $code, was removed, settled, and the owner told once";;
    *) fail "the publisher's own die event reports '$code': neither its bound (75) nor the manager's stop (137/143)";; esac
  manager publication-inspect "${COMMON[@]}" --job "$JOB2" --stage "$STAGE2" --episode "$EPISODE2" --participant "$OWNER" > "$PREFIX.inspect-final.json"
  same "$(json "$PREFIX.inspect.json" output.tree_digest)" "$(json "$PREFIX.inspect-final.json" output.tree_digest)" || fail "the original changed"
  say "ok   the original output is byte-identical after the expired recovery"
}

cleanup() {
  RUN="$(run_id)"
  local name tag id now
  while read -r name tag id; do
    [ -n "$tag" ] || continue
    # A TAG IS GONE ONLY WHEN THE ENGINE SAYS SO: an inspection that failed has not answered.
    if ! now="$(eng image inspect --format '{{.Id}}' "$tag" 2>> "$PREFIX.cleanup.log")"; then
      if now="$(eng image ls -q --no-trunc "$tag" 2>> "$PREFIX.cleanup.log")" && [ -z "$now" ]; then say "cleanup: $tag is already gone (the engine lists no such tag)"
      else say "UNRESOLVED: the engine did not answer for $tag; it stays recorded in images.owned"; UNRESOLVED=1; fi
    elif [ "$now" != "$id" ]; then say "cleanup: $tag now names $now, not the $id this run built; left alone"
    elif eng image rm "$tag" >> "$PREFIX.cleanup.log" 2>&1; then say "cleanup: removed $tag"
    else say "UNRESOLVED: $tag could not be removed (in use?); it stays recorded in images.owned as $id and is not forced; see $PREFIX.cleanup.log"; UNRESOLVED=1; fi
  done < "$EVIDENCE/images.owned"
  say "cleanup: only tags recorded in images.owned were considered; no container was touched"
}

case "$phase" in
  images|preflight|recovery|deadline|cleanup) "$phase";;
  fixture-image) fixture_image;;
  cli-in-image) cli_in_image;;
  *) echo "unknown phase $phase" >&2; exit 2;;
esac
say "phase $phase complete"
