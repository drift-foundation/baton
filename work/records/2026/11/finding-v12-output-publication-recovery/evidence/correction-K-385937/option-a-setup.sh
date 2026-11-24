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
TEMPLATE="baton.v12.job-template.implementation-review/1"
MANAGER_STARTED=""; ENDING=""

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

stack_live() {
  python3 - "$STACK_STATE" <<'PY'
import json, os, sys
for name in ("manager", "publisher"):
    try:
        pid = json.load(open(os.path.join(sys.argv[1], name + ".json"))).get("pid")
    except (OSError, ValueError):
        continue
    if isinstance(pid, int) and os.path.exists("/proc/%d" % pid):
        print(name, pid)
PY
}
finish() {
  local code=$?
  [ -z "$ENDING" ] || return 0
  ENDING=1; set +e
  if [ -n "$MANAGER_STARTED" ]; then
    timeout --kill-after=10 120 just --justfile "$DEST/justfile" stop >> "$PREFIX.cleanup.log" 2>&1 \
      && say "cleanup: instance stack stopped" || say "UNRESOLVED: the instance stack did not stop; see $PREFIX.cleanup.log"
  fi
  say "phase $phase ended with status $code"
  exit "$code"
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
  [ -z "$(stack_live)" ] || fail "the instance stack is running; workers are admitted with it stopped"
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
  for n in 1 2; do
    run_step "create-$n" "$PREFIX.create-$n.json"
    [ -n "$(field "$PREFIX.create-$n.json" job_id)" ] || fail "creation $n answered no Job"
    [ "$(field "$PREFIX.create-$n.json" template.version)" = "$TEMPLATE" ] || fail "creation $n is not under $TEMPLATE"
  done
  [ "$(field "$PREFIX.create-1.json" job_id)" != "$(field "$PREFIX.create-2.json" job_id)" ] || fail "the two creations answered one Job"
  say "jobs: $(field "$PREFIX.create-1.json" job_id) and $(field "$PREFIX.create-2.json" job_id), both under $TEMPLATE"
}

settlement() { installed manager "$@"; }
failures() {
  : "${OWNER:?}"
  local n job stage
  [ -z "$(stack_live)" ] || fail "the instance stack is already running; this phase starts and stops its own"
  local code=0
  timeout --kill-after=10 300 just --justfile "$DEST/justfile" start > "$PREFIX.start.log" 2>&1 || code=$?
  [ -z "$(stack_live)" ] || MANAGER_STARTED=1
  [ "$code" = 0 ] && [ -n "$MANAGER_STARTED" ] || fail "the instance stack did not start under this run's ownership (status $code)"
  # BOTH PRODUCERS MUST STOP AS FAILED PUBLICATIONS, and the product says when: its own settlement preview
  # answers `eligible` for an attempt whose runtime is positively stopped with nothing collected.
  local end=$(( $(date +%s) + PRODUCER_SECONDS ))
  for n in 1 2; do
    job="$(field "$PREFIX.create-$n.json" job_id)"; stage="$job/implementation"
    until settlement settlement-preview --instance "$INSTANCE" --job "$job" --stage "$stage" --episode 1 --operation-id "option-a-$RUN-$n" \
            > "$PREFIX.preview-$n.json" 2> "$PREFIX.preview-$n.err" \
          && [ "$(field "$PREFIX.preview-$n.json" eligibility.eligibility)" = eligible ]; do
      [ "$(date +%s)" -lt "$end" ] || fail "producer $n ($job) did not stop as a settleable failure within $PRODUCER_SECONDS s; see $PREFIX.preview-$n.err"
      sleep 10
    done
    say "ok   producer $n ($job) has stopped and is settleable"
  done
  # THE MANAGER IS STOPPED BEFORE ANYTHING IS SETTLED: both settlement verbs take the instance's manager guard.
  timeout --kill-after=10 120 just --justfile "$DEST/justfile" stop > "$PREFIX.stop.log" 2>&1 || fail "the instance stack did not stop"
  MANAGER_STARTED=""
  [ -z "$(stack_live)" ] || fail "the instance stack still records a live process after stop"
  : > "$PREFIX.env"
  for n in 1 2; do
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
