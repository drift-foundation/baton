#!/usr/bin/env bash
# W385695 package/image/engine qualification. PREPARED, NOT EXECUTED BY ITS AUTHOR.
# Running it is a separately selected act: it builds images and starts containers.
# It needs no live provider. It never replaces, edits or re-stages approved bytes.
#
#   qualify-w385695.sh images            build the five changed images; identity and content assertions
#   qualify-w385695.sh publisher         inspect -> decide -> publication on a prepared instance; mounts, uid, network, cessation
#   qualify-w385695.sh reviewer          continue the same recovery: reviewer delivery, read-only source, verdict
#   qualify-w385695.sh deadline          a SECOND prepared recovery, publisher frozen past its absolute bound; expiry, removal, owner item
#   qualify-w385695.sh cleanup           remove the image tags this script created; report (never delete) leftover containers
#
# Required environment
#   TREE       root of the imported, reviewed tree (contains v12/)
#   EVIDENCE   a NEW directory outside TREE; every observation is written there
# For publisher/reviewer/deadline also
#   DEST       the qualification instance destination (its own justfile; `just start` serves it)
#   INSTANCE   that instance's instance.json
#   OWNER      the owner participant that may approve on the Work
#   JOB STAGE EPISODE DECISION            the failed Job, its implementation stage id, episode, a fresh decision id
#   (deadline) JOB2 STAGE2 EPISODE2 DECISION2   a second failed Job of the same kind
# Optional: ENGINE (docker)
#
# PRECONDITIONS for the instance phases, each checked below where it can be:
#   the instance was installed from TREE with a publication worker whose image digest is the
#   `publication` identity `images` printed, and a reviewer whose provider is the deterministic
#   scripted one; the manager is STOPPED; JOB (and JOB2) completed implementation, failed at output
#   publication and had its runtime removed (publication-inspect answers eligible).
set -euo pipefail
: "${TREE:?}" "${EVIDENCE:?}"
ENGINE="${ENGINE:-docker}"
PY="$TREE/v12/python"
TAG="w385695-qual"
phase="${1:?phase}"
case "$EVIDENCE/" in "$TREE"/*) echo "EVIDENCE must be outside TREE" >&2; exit 2;; esac
mkdir -p "$EVIDENCE"
cd "$PY"
P="$(python3 -m tools.environment interpreter)"
run_py() { env PYTHONPATH=src:. "$P" "$@"; }
manager() { run_py -m tools.job_manager "$@"; }
say() { printf '%s %s\n' "$(date -u +%FT%TZ)" "$*" | tee -a "$EVIDENCE/qualify.log"; }
fail() { say "FAIL: $*"; exit 1; }
json() { run_py -c 'import json,sys; d=json.load(open(sys.argv[1])); 
for k in sys.argv[2].split("."): d = d[int(k)] if isinstance(d, list) else d.get(k) if d is not None else None
print(json.dumps(d))' "$1" "$2"; }
want() { local got; got="$(json "$1" "$2")"; [ "$got" = "$3" ] || fail "$1 $2 is $got, wanted $3"; say "ok   $2 = $3"; }

images() {
  # name | dockerfile | build context | files that must equal the reviewed source bytes
  local rows=(
    "reference|worker/Dockerfile|worker|baton_worker.py=worker/baton_worker.py"
    "provider|worker/Dockerfile.claude|.|baton_worker.py=worker/baton_worker.py claude_agent.py=worker/claude_agent.py"
    "integration|worker/Dockerfile.integration|.|baton_worker.py=worker/baton_worker.py claude_agent.py=worker/claude_agent.py"
    "reconciliation|worker/Dockerfile.reconciliation|.|baton_worker.py=worker/baton_worker.py"
    "publication|worker/Dockerfile.publication|worker|baton_worker.py=worker/baton_worker.py publication_entry.py=worker/publication_entry.py"
  )
  for row in "${rows[@]}"; do
    IFS='|' read -r name recipe context files <<<"$row"
    say "build $name from $recipe"
    run_py -m tools.worker_image --engine "$ENGINE" --tag "baton-v12-$name:$TAG" \
      --dockerfile "$TREE/v12/$recipe" --context "$TREE/v12/$context" | tee "$EVIDENCE/image-$name.identity"
    "$ENGINE" image inspect "baton-v12-$name:$TAG" > "$EVIDENCE/image-$name.inspect.json"
    for pair in $files; do
      inside="${pair%%=*}"; source="$TREE/v12/${pair#*=}"
      got="$("$ENGINE" run --rm --network none --entrypoint python3 "baton-v12-$name:$TAG" -c \
        "import hashlib;print(hashlib.sha256(open('/opt/baton/$inside','rb').read()).hexdigest())")"
      [ "$got" = "$(sha256sum "$source" | cut -d' ' -f1)" ] || fail "$name: /opt/baton/$inside is not the reviewed $source"
      say "ok   $name /opt/baton/$inside = reviewed bytes $got"
    done
  done
  local pub="$EVIDENCE/image-publication.inspect.json"
  want "$pub" 0.Config.Entrypoint '["python3", "/opt/baton/publication_entry.py"]'
  want "$pub" 0.Config.User '"65532:65532"'
  json "$pub" 0.Config.Env | grep -Eq 'ANTHROPIC|CLAUDE|BATON_WORKER|CREDENTIAL' && fail "publication image carries a provider or credential variable"
  say "ok   publication image environment names no provider or credential"
  listed="$("$ENGINE" run --rm --network none --entrypoint python3 "baton-v12-publication:$TAG" -c \
    "import os;print(sorted(os.listdir('/opt/baton')), os.getuid(), os.getgid())")"
  [ "$listed" = "['baton_worker.py', 'publication_entry.py', 'worker-control-1.0.schema.json'] 65532 65532" ] \
    || fail "publication image content or identity: $listed"
  say "ok   publication image holds exactly its three files and runs as 65532:65532"
  say "images: the four existing images' accepted engine gates are their qualification consumers: run"
  say "        'just test-group manager-engine' with each rebuilt identity selected, as TESTING.md section 3 states."
}

stores() {
  : "${INSTANCE:?}" "${DEST:?}" "${OWNER:?}"
  eval "$(run_py -c 'import sys,shlex
from tools import instance
s = instance.read(sys.argv[1]); p = instance.layout(s["destination"])
for k, v in (("JOBS", s["job_store"]), ("CONTROL", s["control_store"]), ("UUID", s["authority_uuid"]), ("AUTHORITY", p["authority_store"]), ("STATE", s["destination"])):
    print(f"{k}={shlex.quote(str(v))}")' "$INSTANCE")"
  COMMON=(--store "$JOBS" --authority-uuid "$UUID" --incarnation "qualify-$$" --control "$CONTROL" --authority "$AUTHORITY" --instance "$STATE")
}

status() { manager publication-status --store "$JOBS" --authority-uuid "$UUID" --incarnation "qualify-$$" --control "$CONTROL" --decision-id "$1" > "$2"; }

watch_containers() {  # $1 = evidence prefix, $2 = action for a container of role publication ("" or pause)
  "$ENGINE" events --filter type=container --filter event=create --filter event=start --filter event=die \
    --filter event=destroy --filter event=pause --filter event=unpause --format '{{json .}}' > "$1.events.jsonl" &
  echo $! > "$1.events.pid"
  ( seen=""
    while [ -e "$1.watching" ]; do
      for id in $("$ENGINE" ps -aq --filter label=baton.v12.runtime_attempt_id); do
        case " $seen " in *" $id "*) continue;; esac
        seen="$seen $id"
        "$ENGINE" inspect "$id" > "$1.container-$id.json" 2>/dev/null || continue
        if [ -n "${2:-}" ] && grep -q "publication_entry.py" "$1.container-$id.json"; then
          "$ENGINE" pause "$id" && echo "$id" > "$1.paused"
        fi
        if grep -q '"/input/source"' "$1.container-$id.json" && ! grep -q "publication_entry.py" "$1.container-$id.json"; then
          # a reviewer: what it was delivered, read while it exists
          "$ENGINE" exec "$id" python3 -c "import json,os,stat
s=os.lstat('/input/recovery-review.json'); d=json.load(open('/input/recovery-review.json'))
print(json.dumps({'regular': stat.S_ISREG(s.st_mode), 'reviewer_verification': d.get('reviewer_verification'), 'handoff_digest': d['handoff_digest']}))" \
            > "$1.reviewer-input-$id.json" 2>/dev/null || true
          "$ENGINE" exec "$id" python3 -c "open('/input/source/qualify-probe','w')" > "$1.reviewer-write-$id.txt" 2>&1 \
            && echo WROTE >> "$1.reviewer-write-$id.txt" || echo REFUSED >> "$1.reviewer-write-$id.txt"
        fi
      done
      sleep 0.2
    done ) &
  echo $! > "$1.watch.pid"
}
stop_watch() { rm -f "$1.watching"; kill "$(cat "$1.events.pid")" 2>/dev/null || true; wait "$(cat "$1.watch.pid")" 2>/dev/null || true; }

decide() {  # $1 job $2 stage $3 episode $4 decision $5 prefix
  manager publication-inspect "${COMMON[@]}" --job "$1" --stage "$2" --episode "$3" --participant "$OWNER" > "$5.inspect.json"
  want "$5.inspect.json" eligible true
  mapfile -t argv < <(run_py -c 'import json,sys
r = json.load(open(sys.argv[1]))
out = ["--expect-attempt=" + r["selector"]["attempt_id"], "--expect-selection-digest=" + r["selection_digest"],
       "--expect-candidate-base=" + r["producer"]["base"], "--expect-candidate-head=" + r["producer"]["head"],
       "--expect-output-digest=" + r["output"]["tree_digest"], "--expect-output-bytes=" + str(r["output"]["total_bytes"]),
       "--expect-producer-status=0", "--context-digest=" + r["producer"]["context_digest"],
       "--declaration-digest=" + r["declaration"]["digest"], "--profile=" + r["profile"]["profile"],
       "--profile-digest=" + r["profile"]["digest"]]
out += ["--producer-verification=" + w for w in r["producer"]["argv"]]
out += ["--stage-word=publication", "--stage-word=review"]
print("\n".join(out))' "$5.inspect.json")
  manager publication-decide "${COMMON[@]}" --job "$1" --stage "$2" --episode "$3" --approve \
    "--participant=$OWNER" "--decision-id=$4" "${argv[@]}" > "$5.decide.json"
  want "$5.decide.json" admitted true
  # THE APPROVED BYTES ARE NEVER TOUCHED AGAIN: the same inspection must read the same original afterwards.
  manager publication-inspect "${COMMON[@]}" --job "$1" --stage "$2" --episode "$3" --participant "$OWNER" > "$5.inspect-after.json"
  [ "$(json "$5.inspect.json" output.tree_digest)" = "$(json "$5.inspect-after.json" output.tree_digest)" ] || fail "the original changed after approval"
}

serve() {  # $1 prefix; starts the manager, records its pid
  ( cd "$DEST" && exec just start ) > "$1.manager.log" 2>&1 &
  echo $! > "$1.manager.pid"
}
stop_manager() { kill -INT "$(cat "$1.manager.pid")" 2>/dev/null || true; wait "$(cat "$1.manager.pid")" 2>/dev/null || true; }

until_status() {  # $1 decision $2 prefix $3 dotted member $4 wanted json $5 seconds
  local end=$(( $(date +%s) + $5 ))
  while [ "$(date +%s)" -lt "$end" ]; do
    status "$1" "$2.status.json" && [ "$(json "$2.status.json" "$3")" = "$4" ] && { say "ok   $3 = $4"; return 0; }
    sleep 5
  done
  fail "$3 did not become $4 within $5 s (last: $(json "$2.status.json" "$3"))"
}

publisher() {
  : "${JOB:?}" "${STAGE:?}" "${EPISODE:?}" "${DECISION:?}"; stores
  local pre="$EVIDENCE/publisher"
  decide "$JOB" "$STAGE" "$EPISODE" "$DECISION" "$pre"
  touch "$pre.watching"; watch_containers "$pre" ""
  serve "$pre"
  until_status "$DECISION" "$pre" recovery.handed_off true 1200
  status "$DECISION" "$pre.status.json"
  want "$pre.status.json" recovery.outcome '"published"'
  want "$pre.status.json" publication_attempt.recorded.execution_runtime '"destroyed"'
  attempt="$(json "$pre.status.json" publication_attempt.attempt_id | tr -d '"')"
  seen="$(grep -l "$attempt" "$pre".container-*.json | head -1)"; [ -n "$seen" ] || fail "the publisher container was not observed"
  want "$seen" 0.Config.User '"65532:65532"'
  want "$seen" 0.HostConfig.NetworkMode '"none"'
  run_py -c 'import json,sys
c = json.load(open(sys.argv[1]))[0]; m = {x["Destination"]: x for x in c["Mounts"]}
assert m["/input/source"]["RW"] is False, "the staged original is not read-only"
bad = [d for d, x in m.items() if d.startswith("/input") and x["RW"]]
assert not bad, f"writable input mounts: {bad}"
writable = sorted(d for d, x in m.items() if x["RW"])
assert writable and all(not d.startswith("/input") for d in writable), writable
assert not any(k.split("=")[0].startswith(("ANTHROPIC", "CLAUDE")) for k in c["Config"]["Env"]), "provider variable"
print("ok   mounts: /input/source read-only; writable:", writable)' "$seen" | tee -a "$EVIDENCE/qualify.log"
  [ -z "$("$ENGINE" ps -aq --filter "label=baton.v12.runtime_attempt_id=$attempt")" ] || fail "the publisher container still exists"
  say "ok   publisher container $attempt is gone after custody"
  say "publisher: leave the manager serving and run the 'reviewer' phase next"
}

reviewer() {
  : "${DECISION:?}"; stores
  local pre="$EVIDENCE/publisher"
  until_status "$DECISION" "$pre" review.state '"completed"' 4800
  status "$DECISION" "$pre.status.json"
  want "$pre.status.json" review.verdict.candidate_is_the_approved_original true
  say "verdict: $(json "$pre.status.json" review.verdict.disposition) by $(json "$pre.status.json" review.reviewer)"
  input="$(ls "$pre".reviewer-input-*.json 2>/dev/null | head -1)"; [ -s "$input" ] || fail "the reviewer's delivered input was not observed"
  want "$input" regular true
  want "$input" reviewer_verification '{"required": true, "command_seconds": 900}'
  grep -q REFUSED "$(ls "$pre".reviewer-write-*.txt | head -1)" || fail "the reviewer could write into /input/source"
  say "ok   /input/source is not writable from the reviewer container"
  stop_manager "$pre"; stop_watch "$pre"
}

deadline() {
  : "${JOB2:?}" "${STAGE2:?}" "${EPISODE2:?}" "${DECISION2:?}"; stores
  local pre="$EVIDENCE/deadline"
  decide "$JOB2" "$STAGE2" "$EPISODE2" "$DECISION2" "$pre"
  # THE APPROVED BYTES AND THE 900-SECOND PROFILE ARE UNCHANGED. The publisher is FROZEN by the engine the
  # moment it exists and released only after the manager's own clock reports the absolute bound reached.
  touch "$pre.watching"; watch_containers "$pre" pause
  serve "$pre"
  until_status "$DECISION2" "$pre" recovery.publication_deadline.reached true 1200
  [ -s "$pre.paused" ] || fail "the publisher was never observed and frozen"
  "$ENGINE" unpause "$(cat "$pre.paused")" 2>/dev/null || say "note: the publisher was already ended by the manager while frozen"
  until_status "$DECISION2" "$pre" recovery.outcome '"expired"' 300
  until_status "$DECISION2" "$pre" recovery.settled true 300
  status "$DECISION2" "$pre.status.json"
  want "$pre.status.json" recovery.published false
  want "$pre.status.json" recovery.review '"blocked"'
  want "$pre.status.json" owner_item.outcome '"expired"'
  want "$pre.status.json" owner_item.automatic_retry false
  want "$pre.status.json" publication_attempt.recorded.execution_runtime '"destroyed"'
  attempt="$(json "$pre.status.json" publication_attempt.attempt_id | tr -d '"')"
  [ -z "$("$ENGINE" ps -aq --filter "label=baton.v12.runtime_attempt_id=$attempt")" ] || fail "the expired publisher container still exists"
  grep '"die"' "$pre.events.jsonl" | tee "$pre.exit-events.jsonl" | grep -Eq '"exitCode":"(75|137|143)"' \
    || fail "the publisher's ending is neither its own bound (75) nor the manager's stop (137/143)"
  say "ok   expired publisher ended ($(grep -o '"exitCode":"[0-9]*"' "$pre.exit-events.jsonl" | tr '\n' ' ')), removed, settled, owner told once"
  manager publication-inspect "${COMMON[@]}" --job "$JOB2" --stage "$STAGE2" --episode "$EPISODE2" --participant "$OWNER" > "$pre.inspect-final.json"
  [ "$(json "$pre.inspect.json" output.tree_digest)" = "$(json "$pre.inspect-final.json" output.tree_digest)" ] || fail "the original changed"
  say "ok   the original output is byte-identical after the expired recovery"
  stop_manager "$pre"; stop_watch "$pre"
}

cleanup() {
  for name in reference provider integration reconciliation publication; do
    "$ENGINE" image rm "baton-v12-$name:$TAG" >> "$EVIDENCE/cleanup.log" 2>&1 || true
  done
  "$ENGINE" ps -a --filter label=baton.v12.runtime_attempt_id --format '{{.ID}} {{.Status}} {{.Labels}}' | tee "$EVIDENCE/leftover-containers.txt"
  say "cleanup: tags removed; any container listed above is reported, not removed -- settle it with 'manager settlement-remove'"
}

case "$phase" in images|publisher|reviewer|deadline|cleanup) "$phase";; *) echo "unknown phase $phase" >&2; exit 2;; esac
say "phase $phase complete"
( cd "$EVIDENCE" && find . -type f ! -name evidence.sha256 -print0 | sort -z | xargs -0 sha256sum > evidence.sha256 )
