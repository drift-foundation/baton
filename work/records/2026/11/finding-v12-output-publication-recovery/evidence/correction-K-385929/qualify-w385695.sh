#!/usr/bin/env bash
# W385695 package/image/engine qualification, revision 2 (review 2026-11-24T01-52-00Z C5).
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
#   qualify-w385695.sh cleanup         remove only the image tags this run recorded, if still the recorded image
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
OWNED_PIDS=(); PAUSED=""; MANAGER_STARTED=""; ENDING=""

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
finish() {
  local code=$?
  [ -z "$ENDING" ] || return 0
  ENDING=1; set +e
  rm -f "$PREFIX.watching"
  # THE ONE CONTAINER THIS RUN FROZE, if it is still the selected attempt's. Bounded; a failure is recorded.
  if [ -n "$PAUSED" ]; then
    if [ "$(eng inspect --format '{{.State.Paused}}' "$PAUSED" 2>/dev/null)" = "true" ]; then
      eng unpause "$PAUSED" >> "$PREFIX.cleanup.log" 2>&1 && say "cleanup: unpaused $PAUSED" \
        || say "UNRESOLVED: container $PAUSED is still paused and could not be released"
    fi
  fi
  # THE MANAGER THIS RUN STARTED, through the instance's own stop, which stops only what that stack owns.
  if [ -n "$MANAGER_STARTED" ]; then
    timeout --kill-after=10 120 just --justfile "$DEST/justfile" stop >> "$PREFIX.cleanup.log" 2>&1 \
      && say "cleanup: instance stack stopped" || say "UNRESOLVED: the instance stack did not stop; see $PREFIX.cleanup.log"
  fi
  local pid
  for pid in "${OWNED_PIDS[@]}"; do kill -TERM "$pid" 2>/dev/null; done
  for pid in "${OWNED_PIDS[@]}"; do
    ended "$pid" 20 || { kill -KILL "$pid" 2>/dev/null; ended "$pid" 5 || say "UNRESOLVED: owned process $pid did not end"; }
  done
  # WHAT IS LEFT OF THE SELECTED ATTEMPTS IS REPORTED, NEVER REMOVED HERE. It is settled by the product's own
  # owner (`manager settlement-remove`), so nothing this script cannot account for is destroyed by it.
  if [ -s "$PREFIX.selected-attempts" ]; then
    while read -r attempt; do
      eng ps -a --filter "label=baton.v12.runtime_attempt_id=$attempt" --format '{{.ID}} {{.Status}}' \
        | sed "s|^|$attempt |" >> "$PREFIX.leftover-containers.txt" 2>/dev/null
    done < "$PREFIX.selected-attempts"
    [ -s "$PREFIX.leftover-containers.txt" ] && say "UNRESOLVED: selected containers remain; see $PREFIX.leftover-containers.txt"
  fi
  say "phase $phase ended with status $code"
  # SEALED LAST, after every writer this run owns has stopped.
  ( cd "$EVIDENCE" && find . -type f ! -name evidence.sha256 -print0 | sort -z | xargs -0 sha256sum > evidence.sha256 )
  exit "$code"
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
  local name="$1" tag="baton-v12-$1:w385695-$RUN"
  if eng image inspect "$tag" > /dev/null 2>&1; then fail "tag $tag already exists; this run owns only tags it created"; fi
  say "build $name from $2"
  ( cd "$TREE/v12/python" && timeout --kill-after=30 "$BUILD_SECONDS" env PYTHONPATH=src:. \
      "$(python3 -m tools.environment interpreter)" -m tools.worker_image --engine "$ENGINE" --tag "$tag" \
      --dockerfile "$TREE/v12/$2" --context "$TREE/v12/$3" ) | tee "$EVIDENCE/image-$name.identity"
  local id; id="$(eng image inspect --format '{{.Id}}' "$tag")"
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
  [ ! -e "$EVIDENCE/run-id" ] || fail "this EVIDENCE already holds a run; use a new directory for a new run"
  RUN="$(date -u +%Y%m%dT%H%M%SZ)-$$"; echo "$RUN" > "$EVIDENCE/run-id"; : > "$EVIDENCE/images.owned"
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

fixture_image() {
  RUN="$(run_id)"
  local base; base="$(owned_image provider)"; [ -n "$base" ] || fail "this run built no provider image"
  local work; work="$(mktemp -d "$EVIDENCE/fixture-image.XXXXXX")"
  cat > "$work/claude" <<'PY'
#!/usr/bin/python3
"""QUALIFICATION FIXTURE, NOT A PROVIDER: a scripted program standing where the CLI stands. No model."""
import json, os, subprocess, sys
if os.path.isdir(".git") or os.path.exists(".git"):
    open("big.txt", "w").write("x" * (1048576 + 4096))          # an implementer whose output is over its ceiling
else:
    recovery = json.load(open("/input/recovery-review.json"))
    prefix = os.environ.get("CLAUDE_CODE_SHELL_PREFIX")
    ran = subprocess.run([prefix, "true"]).returncode if prefix else None   # one command through the supervisor
    json.dump({"schema": "baton.review-report/1", "verdict": "accepted",
               "findings": f"Scripted qualification review; one supervised command exited {ran}.",
               "recovery_digest": recovery["handoff_digest"]}, open("review-report.json", "w"))
print(json.dumps({"type": "result", "subtype": "success", "is_error": False, "result": "scripted"}))
PY
  cat > "$work/Dockerfile" <<EOF
FROM $base
LABEL baton.v12.qualification-fixture=scripted-provider
COPY claude /usr/local/bin/claude
RUN chmod 0555 /usr/local/bin/claude
EOF
  local tag="baton-v12-qualification-fixture:w385695-$RUN"
  if eng image inspect "$tag" > /dev/null 2>&1; then fail "tag $tag already exists"; fi
  timeout --kill-after=30 "$BUILD_SECONDS" "$ENGINE" build -t "$tag" "$work" > "$EVIDENCE/fixture-image.build.log" 2>&1 || fail "fixture image build failed"
  echo "fixture $tag $(eng image inspect --format '{{.Id}}' "$tag")" >> "$EVIDENCE/images.owned"
  say "fixture-image: $(owned_image fixture) -- a LABELLED scripted stand-in for the provider program only"
}

# -- the instance, through its own installed command ------------------------
stores() {
  : "${INSTANCE:?}" "${OWNER:?}"
  RUN="$(run_id)"
  eval "$(python3 - "$INSTANCE" <<'PY'
import json, shlex, sys
s = json.load(open(sys.argv[1])); d = s["destination"]
deployment = json.load(open(s["deployment"]))
for k, v in (("DEST", d), ("CMD", d + "/distro/baton-v12-stack"), ("JOBS", s["job_store"]), ("CONTROL", s["control_store"]),
             ("UUID", s["authority_uuid"]), ("AUTHORITY", d + "/stores/authority.sqlite3"),
             ("STORAGE", deployment["workspace_storage"])):
    print(f"{k}={shlex.quote(str(v))}")
PY
)"
  [ -x "$CMD" ] || fail "the instance's installed command $CMD is missing"
  case "$CMD" in "$TREE"/*) fail "the instance command is inside TREE; that is not an installed bundle";; esac
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
  python3 - "$DEST/deployment.json" "$EVIDENCE/images.owned" <<'PY' || fail "the deployment does not select this run's images"
import json, sys
deployment = json.load(open(sys.argv[1]))
owned = {line.split()[0]: line.split()[2] for line in open(sys.argv[2]) if line.strip()}
text = json.dumps(deployment)
missing = [name for name in ("publication",) if owned.get(name, "-") not in text]
if not any(owned.get(name, "-") in text for name in ("provider", "fixture")):
    missing.append("provider-or-fixture")
if missing:
    print("deployment.json names no image identity of this run for:", ", ".join(missing), file=sys.stderr); sys.exit(1)
PY
  say "ok   the deployment selects this run's publication image and its provider (or labelled fixture) image"
  manager publication-inspect "${COMMON[@]}" --job "$1" --stage "$2" --episode "$3" --participant "$OWNER" > "$4.inspect.json" \
    || fail "publication-inspect refused Job $1; see $4.inspect.json"
  want "$4.inspect.json" eligible true
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
          eng pause "$id" >> "$PREFIX.watch.log" 2>&1 && echo "$id" > "$PREFIX.paused" || echo "pause-failed $id" >> "$PREFIX.watch.log"
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
serve() {
  timeout --kill-after=10 300 just --justfile "$DEST/justfile" start > "$PREFIX.manager-start.log" 2>&1 \
    || { MANAGER_STARTED=1; fail "the instance stack did not start"; }
  # A STACK THAT WAS ALREADY RUNNING IS NOT THIS RUN'S TO STOP. The start command says so in these words
  # (`tools/stack.py`); this run then owns no manager, stops none, and does not continue.
  if grep -qi "already running" "$PREFIX.manager-start.log"; then
    fail "the instance stack was already running; these phases start and stop their own and will not stop another's"
  fi
  MANAGER_STARTED=1
}
until_status() {  # DECISION DOTTED.PATH EXPECTED-JSON SECONDS
  local end=$(( $(date +%s) + $4 ))
  while [ "$(date +%s)" -lt "$end" ]; do
    if status "$1" "$PREFIX.status.json" 2>/dev/null && same "$(json "$PREFIX.status.json" "$2")" "$3"; then say "ok   $2 = $3"; return 0; fi
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
  want "$seen" 0.Config.User '"65532:65532"'
  want "$seen" 0.HostConfig.NetworkMode '"none"'
  python3 - "$seen" "$STORAGE" <<'PY' | tee -a "$EVIDENCE/qualify.log" || fail "the publisher's mounts are not the approved ones"
import json, sys
c = json.load(open(sys.argv[1]))[0]; m = {x["Destination"]: x for x in c["Mounts"]}
assert m["/input/source"]["RW"] is False, "the staged original is not read-only"
assert not [d for d, x in m.items() if d.startswith("/input") and x["RW"]], "a writable input mount"
writable = sorted(d for d, x in m.items() if x["RW"])
assert writable == ["/output"], f"writable mounts are {writable}, wanted exactly the output"
names = [k.split("=")[0] for k in c["Config"]["Env"]]
assert not [n for n in names if n.startswith(("ANTHROPIC", "CLAUDE")) or "CREDENTIAL" in n or "TOKEN" in n], "a provider, credential or token variable"
assert not [d for d in m if "credential" in d.lower()], "a credential mount"
print("ok   publisher mounts: /input/source read-only, /output the one writable mount, no credential or token")
PY
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
  if [ "$(eng inspect --format '{{.State.Paused}}' "$PAUSED" 2>/dev/null)" = "true" ]; then
    eng unpause "$PAUSED" >> "$PREFIX.watch.log" 2>&1 || fail "the frozen publisher could not be released"
  else
    say "note: the publisher was already ended by the manager while frozen"
  fi
  PAUSED=""
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
    now="$(eng image inspect --format '{{.Id}}' "$tag" 2>/dev/null || true)"
    if [ -z "$now" ]; then say "cleanup: $tag is already gone"
    elif [ "$now" != "$id" ]; then say "cleanup: $tag now names $now, not the $id this run built; left alone"
    elif eng image rm "$tag" >> "$PREFIX.cleanup.log" 2>&1; then say "cleanup: removed $tag"
    else say "UNRESOLVED: $tag could not be removed (in use?); see $PREFIX.cleanup.log"; fi
  done < "$EVIDENCE/images.owned"
  say "cleanup: only tags recorded in images.owned were considered; no container was touched"
}

case "$phase" in
  images|preflight|recovery|deadline|cleanup) "$phase";;
  fixture-image) fixture_image;;
  *) echo "unknown phase $phase" >&2; exit 2;;
esac
say "phase $phase complete"
