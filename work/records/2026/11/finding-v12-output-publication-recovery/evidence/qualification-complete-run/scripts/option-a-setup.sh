#!/usr/bin/env bash
# W385695 Option A (owner selection M385933): prepare the qualification instance's workers, its two Jobs and
# their two completed-but-publication-failed producers, using ONLY the instance's supported verbs.
# PREPARED, NOT EXECUTED BY ITS AUTHOR against any engine. The `workers` and `jobs` phases start nothing; the
# `failures` phase starts the instance's stack and therefore containers, and is a separately selected act.
#
#   option-a-setup.sh workers     compose the three workers on this run's images and admit them by the repeat
#   option-a-setup.sh jobs        create the two ordinary Jobs under the 1 MiB-proposal template
#   option-a-setup.sh failures    serve until both producers have stopped, stop, settle and remove both, and
#                                 write the environment `qualify-w385695.sh` takes
#   option-a-setup.sh argv STEP   print the exact argv of one step as JSON and run nothing (STEP: compose-implementation,
#                                 compose-review, compose-publication, repeat, create-1, create-2)
#
# THE INSTANCE ITSELF IS INSTALLED FIRST, BY THE OPERATOR, with the product's own command and a document of the
# operator's own instance selections (v12/STACK.md "just bootstrap", "What you must name"):
#       just bootstrap INPUTS DESTINATION            (repositories from --repository-source as that manual says)
# Those selections -- profiles, participants, digests, the repositories -- are the instance's and are not
# invented here. Everything Option A adds to that instance is below, and nothing below is a placeholder.
#
# Required environment (every one a fact of this host or of that install; none has a default):
#   EVIDENCE            the qualification run's evidence directory (holds run-id and images.owned from
#                       `qualify-w385695.sh images` and `fixture-image`)
#   INSTANCE            the installed instance.json
#   (INPUTS)            optional: the input document the instance was installed from. Omitted, the copy the
#                       instance itself keeps (<destination>/install-inputs.json) is the one repeated.
#   REPOSITORY_SOURCE   the checkout the instance's repositories were prepared from
#   CHECKOUT RECORD     the repository checkout and the repository-relative dossier path the Jobs' Work is bound to
#   TASK_DOCUMENT       absolute path of the installed task document the workers are sealed over
#   WORKSPACE_GROUP     the provisioned workspace group id (DEPLOYMENT.md "Provisioning the workspace group")
#   NETWORK             the approved OCI network name the provider roles are configured with
#   CREDENTIAL_SOURCES  absolute path of a QUALIFICATION-ONLY private credential registry
#   CREDENTIAL          one slot mapping SLOT=PROVIDER:REFERENCE into it. The scripted fixture never reads the
#                       credential and reaches no network; the adapter still requires the slot to be delivered.
#   VERIFIER_LAYOUT     the worker/verifier-layout-marker.json of the tree the images were built from
#   CLI_BUILD           the provider CLI build the provider recipe pins (recorded by the worker document)
#   IMPLEMENTER REVIEWER PUBLISHER   the three participants (implementation and review may share neither
#                       participant nor principal; all three are participants of the install document)
#   OWNER               the owner participant, for the final inspection
# For `jobs`: WORK_SCOPE (the repository path the Jobs may change)
# Optional: PRODUCER_SECONDS (1800) for both producers to stop
set -euo pipefail
phase="${1:?phase}"
: "${EVIDENCE:?}" "${INSTANCE:?}"
EVIDENCE="$(realpath "$EVIDENCE")"
PREFIX="$EVIDENCE/option-a"
PRODUCER_SECONDS="${PRODUCER_SECONDS:-1800}"
# THE ORDINARY TEMPLATE, NAMED. Its proposal output is admitted under 1048576 bytes, which is the ceiling the
# scripted implementer writes past; `/4` (100 MiB) would let the same producer succeed and is refused here.
TEMPLATE="baton.v12.job-template.implementation-review/3"
MANAGER_STARTED=""; ENDING=""; UNRESOLVED=""

say() { printf '%s %s\n' "$(date -u +%FT%TZ)" "$*" | tee -a "$EVIDENCE/option-a.log"; }
fail() { say "FAIL: $*"; exit 1; }
field() { python3 -c 'import json,sys
d = json.load(open(sys.argv[1]))
for k in sys.argv[2].split("."):
    d = d.get(k) if isinstance(d, dict) else None
print("" if d is None else d if isinstance(d, str) else json.dumps(d))' "$1" "$2"; }
owned_image() { awk -v n="$1" '$1 == n { print $3 }' "$EVIDENCE/images.owned" 2>/dev/null | tail -1; }
owned_tag() { awk -v n="$1" '$1 == n { print $2 }' "$EVIDENCE/images.owned" 2>/dev/null | tail -1; }

eval "$(python3 - "$INSTANCE" <<'PY'
import json, shlex, sys
s = json.load(open(sys.argv[1])); d = s["destination"]
for k, v in (("DEST", d), ("CMD", d + "/distro/baton-v12-stack"), ("DEPLOYMENT", s["deployment"]), ("JOBS", s["job_store"]),
             ("CONTROL", s["control_store"]), ("UUID", s["authority_uuid"]), ("AUTHORITY", d + "/db/authority.sqlite3"),
             ("STACK_STATE", d + "/state")):
    print(f"{k}={shlex.quote(str(v))}")
PY
)"
RUN="$(cat "$EVIDENCE/run-id" 2>/dev/null)" || true
[ -n "$RUN" ] || { echo "no run identity in EVIDENCE: run 'qualify-w385695.sh images' and 'fixture-image' first" >&2; exit 2; }

# -- the exact argv of every step, composed in ONE place ---------------------
ARGV=()
compose_argv() {  # ROLE WORKER-ID PARTICIPANT IMAGE-NAME
  : "${CHECKOUT:?}" "${RECORD:?}" "${TASK_DOCUMENT:?}" "${WORKSPACE_GROUP:?}"
  local image; image="$(owned_image "$4")"; [ -n "$image" ] || fail "this run recorded no $4 image"
  ARGV=(pool compose-worker --deployment "$DEPLOYMENT" --worker-id "$2" --role "$1" --participant "$3"
        --image-reference "$(owned_tag "$4")" --image-digest "$image"
        --workspace-group "$WORKSPACE_GROUP" --task-document "$TASK_DOCUMENT" --record "$RECORD" --checkout "$CHECKOUT"
        --template "$TEMPLATE" --into "$PREFIX.worker-$2.json")
  if [ "$1" != publication ]; then
    # THE PROVIDER OPERANDS AND THE VERIFIER LAYOUT, required of a role that has a provider and REFUSED for the
    # deterministic publication role, which invokes none and is delivered no credential.
    : "${CLI_BUILD:?}" "${NETWORK:?}" "${CREDENTIAL_SOURCES:?}" "${CREDENTIAL:?}" "${VERIFIER_LAYOUT:?}"
    ARGV+=(--cli-build "$CLI_BUILD" --network "$NETWORK" --credential-sources "$CREDENTIAL_SOURCES" --credential "$CREDENTIAL"
           --verifier-layout "$VERIFIER_LAYOUT")
  fi
}
step_argv() {
  case "$1" in
    compose-implementation) compose_argv implementation qualify-impl "${IMPLEMENTER:?}" fixture;;
    compose-review) compose_argv review qualify-review "${REVIEWER:?}" fixture;;
    compose-publication) compose_argv publication qualify-publisher "${PUBLISHER:?}" publication;;
    repeat) : "${REPOSITORY_SOURCE:?}"; ARGV=(bootstrap --inputs "$PREFIX.inputs.json" --repository-source "$REPOSITORY_SOURCE");;
    create-1|create-2)
      : "${WORK_SCOPE:?}"
      local n="${1#create-}"
      ARGV=(manager --store "$JOBS" --incarnation "option-a-$RUN" --authority-uuid "$UUID" create --instance "$DEST"
            --control "$CONTROL" --authority "$AUTHORITY" --task "w385695-qualify-$RUN-$n"
            --statement "W385695 qualification producer $n: write the scripted candidate." --acceptance "The candidate is committed on the Job's line."
            --work-scope "$WORK_SCOPE" --template "$TEMPLATE");;
    *) echo "unknown step $1" >&2; exit 2;;
  esac
}
# NOTHING OF A CHECKOUT IN ITS ENVIRONMENT: the installed command, as tests/tools/test_packaged_creation runs it.
installed() { ( cd / && env -i HOME="$EVIDENCE/home" PATH="/usr/local/bin:/usr/bin:/bin" "$CMD" "$@" ); }
run_step() {  # STEP OUTPUT-FILE
  step_argv "$1"
  printf '%s\n' "${ARGV[@]}" > "$PREFIX.argv-$1.txt"
  installed "${ARGV[@]}" > "$2" 2> "$2.err" || fail "step $1 was refused; see $2.err"
  say "ok   $1"
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
finish() {
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

workers() {
  INPUTS="${INPUTS:-$DEST/install-inputs.json}"
  [ -f "$INPUTS" ] || fail "the install document $INPUTS does not exist"
  mkdir -p "$EVIDENCE/home"
  [ -x "$CMD" ] || fail "the instance's installed command $CMD is missing"
  [ "$(awk '$1 == "fixture"' "$EVIDENCE/images.owned" | wc -l)" = 1 ] || fail "this run recorded no labelled fixture image (run 'qualify-w385695.sh fixture-image')"
  local live; live="$(stack_live)" || fail "the instance stack's state cannot be established (see $PREFIX.stack-status.txt); workers are admitted with it positively stopped"
  [ -z "$live" ] || fail "the instance stack is running; workers are admitted with it stopped"
  run_step compose-implementation "$PREFIX.compose-implementation.txt"
  run_step compose-review "$PREFIX.compose-review.txt"
  run_step compose-publication "$PREFIX.compose-publication.txt"
  # THE REPEAT: the install document, unchanged, with exactly these three workers and no Job added. It is the
  # one-operand form that admits composed workers and prepares their nominated sources.
  python3 - "$INPUTS" "$PREFIX.inputs.json" "$PREFIX.worker-qualify-impl.json" "$PREFIX.worker-qualify-review.json" "$PREFIX.worker-qualify-publisher.json" <<'PY'
import json, sys
document = json.load(open(sys.argv[1]))
if document.get("workers") or document.get("jobs"):
    sys.exit("the install document already names workers or jobs; Option A adds its own to a fresh instance")
document["workers"] = [json.load(open(path)) for path in sys.argv[3:]]
document["jobs"] = []
json.dump(document, open(sys.argv[2], "w"), sort_keys=True)
PY
  run_step repeat "$PREFIX.repeat.txt"
  # WHAT THE INSTANCE NOW SELECTS, read back: the labelled fixture for both provider roles, never the provider image.
  python3 - "$DEPLOYMENT" "$(owned_image fixture)" "$(owned_image publication)" <<'PY' || fail "the deployment does not carry the Option A workers"
import json, sys
workers = {w["worker_id"]: w for w in json.load(open(sys.argv[1])).get("workers", [])}
want = {"qualify-impl": ("implementation", sys.argv[2]), "qualify-review": ("review", sys.argv[2]), "qualify-publisher": ("publication", sys.argv[3])}
wrong = [name for name, (role, image) in want.items()
         if name not in workers or workers[name]["role"] != role or workers[name]["deployment"]["image_digest"] != image]
sys.exit("wrong or missing: " + ", ".join(wrong) if wrong or set(workers) != set(want) else 0)
PY
  say "workers: three workers admitted; both provider roles run the labelled fixture image"
}

jobs() {
  mkdir -p "$EVIDENCE/home"
  local n
  for n in 1; do
    run_step "create-$n" "$PREFIX.create-$n.json"
    [ -n "$(field "$PREFIX.create-$n.json" job_id)" ] || fail "creation $n answered no Job"
    [ "$(field "$PREFIX.create-$n.json" template.version)" = "$TEMPLATE" ] || fail "creation $n is not under $TEMPLATE"
  done
  say "jobs: $(field "$PREFIX.create-1.json" job_id), one independent original under $TEMPLATE"
}

settlement() { installed manager "$@"; }
failures() {
  : "${OWNER:?}"
  local n job stage
  start_stack "$PREFIX.start.log"
  # BOTH PRODUCERS MUST STOP AS FAILED PUBLICATIONS, and the product says when: its own settlement preview
  # answers `eligible` for an attempt whose runtime is positively stopped with nothing collected.
  local end=$(( $(date +%s) + PRODUCER_SECONDS ))
  for n in 1; do
    job="$(field "$PREFIX.create-$n.json" job_id)"; stage="$job/implementation"
    until settlement settlement-preview --instance "$INSTANCE" --job "$job" --stage "$stage" --episode 1 --operation-id "option-a-$RUN-$n" \
            > "$PREFIX.preview-$n.json" 2> "$PREFIX.preview-$n.err" \
          && [ "$(field "$PREFIX.preview-$n.json" eligibility.eligibility)" = eligible ]; do
      # A terminal pre-runtime failure cannot become a retained-output failure.
      if settlement --store "$JOBS" --incarnation "option-a-observe-$RUN" --authority-uuid "$UUID" status --control "$CONTROL" \
          > "$PREFIX.producer-status-$n.json" 2> "$PREFIX.producer-status-$n.err"; then
        if python3 - "$PREFIX.producer-status-$n.json" "$job" <<'PY_STATUS'
import json, sys
d = json.load(open(sys.argv[1]))
stages = [s for j in d.get("jobs", []) if j.get("job_id") == sys.argv[2] for s in j.get("stages", []) if s.get("kind") == "implementation"]
failed = any(s.get("state") == "exceptional" and (s.get("attempt_diagnostics") or {}).get("preparation_failure_recorded", {}).get("value") is True for s in stages)
sys.exit(0 if failed else 1)
PY_STATUS
        then fail "producer $n failed during preparation; settlement polling cannot recover this case; see $PREFIX.producer-status-$n.json and $PREFIX.preview-$n.err"; fi
      fi
      [ "$(date +%s)" -lt "$end" ] || fail "producer $n ($job) did not stop as a settleable failure within $PRODUCER_SECONDS s; see $PREFIX.preview-$n.err"
      sleep 10
    done
    say "ok   producer $n ($job) has stopped and is settleable"
  done
  # THE MANAGER IS STOPPED BEFORE ANYTHING IS SETTLED: both settlement verbs take the instance's manager guard.
  # The same reconciliation an interrupted run gets: stop what is positively this run's and read it back.
  reconcile_stack
  [ -z "$UNRESOLVED" ] && [ ! -e "$PREFIX.stack-start-intent" ] || fail "the instance stack is not positively stopped; nothing is settled under a manager that may be serving"
  MANAGER_STARTED=""
  : > "$PREFIX.env"
  for n in 1; do
    job="$(field "$PREFIX.create-$n.json" job_id)"; stage="$job/implementation"
    settlement settlement-preview --instance "$INSTANCE" --job "$job" --stage "$stage" --episode 1 --operation-id "option-a-$RUN-$n" > "$PREFIX.preview-$n.json"
    python3 -c 'import json,sys; json.dump(json.load(open(sys.argv[1]))["request"], open(sys.argv[2], "w"), sort_keys=True)' "$PREFIX.preview-$n.json" "$PREFIX.request-$n.json"
    settlement settle-stopped --instance "$INSTANCE" --document "$PREFIX.request-$n.json" > "$PREFIX.settled-$n.json" || fail "settle-stopped refused producer $n"
    [ "$(field "$PREFIX.settled-$n.json" settlement.state)" = settled ] || fail "producer $n is not settled"
    settlement settlement-remove --instance "$INSTANCE" --job "$job" --stage "$stage" --episode 1 \
      --reason "W385695 qualification: the stopped original is removed for recovery" > "$PREFIX.removed-$n.json" || fail "settlement-remove refused producer $n"
    [ "$(field "$PREFIX.removed-$n.json" removed)" = true ] || fail "producer $n's runtime was not removed"
    settlement publication-inspect --store "$JOBS" --authority-uuid "$UUID" --incarnation "option-a-$RUN" --control "$CONTROL" \
      --authority "$AUTHORITY" --instance "$DEST" --job "$job" --stage "$stage" --episode 1 --participant "$OWNER" > "$PREFIX.inspect-$n.json" \
      || fail "publication-inspect refused producer $n"
    [ "$(field "$PREFIX.inspect-$n.json" eligible)" = true ] || fail "producer $n is not an eligible original: $(field "$PREFIX.inspect-$n.json" holds)"
    [ "$(field "$PREFIX.inspect-$n.json" output.exceeded)" = true ] || fail "producer $n's output is not over the ordinary ceiling"
    if [ "$n" = 1 ]; then printf 'export JOB=%q STAGE=%q EPISODE=1 DECISION=%q\n' "$job" "$stage" "option-a-$RUN-D1" >> "$PREFIX.env"
    else printf 'export JOB2=%q STAGE2=%q EPISODE2=1 DECISION2=%q\n' "$job" "$stage" "option-a-$RUN-D2" >> "$PREFIX.env"; fi
    say "ok   producer $n ($job) is settled, removed and an eligible over-ceiling original"
  done
  say "failures: source $PREFIX.env and run 'qualify-w385695.sh preflight'"
}

case "$phase" in
  workers|jobs|failures) "$phase";;
  argv) step_argv "${2:?step}"; python3 -c 'import json,sys; print(json.dumps(sys.argv[1:]))' "${ARGV[@]}"; trap - EXIT; exit 0;;
  *) echo "unknown phase $phase" >&2; exit 2;;
esac
say "phase $phase complete"
