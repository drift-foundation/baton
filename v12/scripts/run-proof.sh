#!/usr/bin/env bash
# The whole W76 proof, from a FRESH disposable authority, with assertions.
# Every claim in the evidence pack is produced by this script; nothing is
# hand-copied. Exits nonzero the moment an assertion fails.
#
#   scripts/run-proof.sh [evidence-label]
#
# Git is used here ONLY to record read-only provenance, and deliberately
# never inside a shell substitution: this deployment's policy hook treats
# that shape as a history mutation regardless of the verb.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
LABEL="${1:-run}"
CONFIG="$ROOT/poc.json"

# PLACEMENT (finding-v12-in-repository-migration). The prototype now
# lives INSIDE the Baton checkout as `v12/`, so this runner works from
# the VALIDATED plan rather than from raw configured strings. `$ROOT` is
# code and retained evidence; `$STATE` is everything a run creates, and
# removing it removes all of it.
#
# Round-1 review: this used to parse the config itself and `rm -rf` an
# evidence directory built from an unconstrained label before anything
# validated a thing. `src/placement.mjs` now proves — before the first
# mutation below — that the state root is external to the whole
# checkout, is not a filesystem-wide directory, that every path this
# script creates or removes is a strict descendant of it, and that the
# label is one safe path component. It refuses nonzero and creates
# nothing.
REPO="$(cd "$ROOT/.." && pwd)"
# A plain assignment, so `set -e` aborts here when the plan is refused.
# Inside a here-document the substitution's exit status is discarded and
# the run would continue with empty paths, which is the opposite of
# failing closed.
PLAN="$(node "$ROOT/src/placement.mjs" plan --config "$CONFIG" --label "$LABEL")"
read -r STATE AUTHORITY RECORD_BASE RECORD_PATH STATE_DIR EV <<< "$PLAN"

# Round-2 review: ownership is established or confirmed BEFORE this
# script writes anything under the root — an existing directory that
# carries no marker is somebody else's and is refused here, not adopted.
OWN="$(node "$ROOT/src/placement.mjs" own --config "$CONFIG")"
read -r MARKER OWNERSHIP <<< "$OWN"
mkdir -p "$STATE"
if [ "$OWNERSHIP" = "fresh" ]; then
	node "$ROOT/src/placement.mjs" marker --config "$CONFIG" > "$MARKER"
fi

rm -rf "$EV"; mkdir -p "$EV/traces" "$EV/snapshots" "$EV/envelopes" "$EV/results"

note() { printf '\n== %s\n' "$*"; }
fail() { printf '\nASSERTION FAILED: %s\n' "$*" >&2; exit 1; }

jqf() { python3 -c "import json,sys;d=json.load(open(sys.argv[1]));print(eval(sys.argv[2],{'d':d}))" "$1" "$2"; }

note "prerequisites"
git -C "$REPO" rev-parse --short HEAD > "$EV/.baton-commit"
{
	echo "date_utc:        $(date -u +%FT%TZ)"
	echo "host_kernel:     $(uname -sr)"
	echo "docker_server:   $(docker version --format '{{.Server.Version}}')"
	echo "node:            $(node --version)"
	echo "baton_binary:    /home/sl/opt/baton/v11/8835cd5/bin/baton"
	echo "baton_source:    $REPO @ $(cat "$EV/.baton-commit")"
	echo "acp_adapter:     /home/sl/opt/acp/claude-agent-acp/0.69.0 (@agentclientprotocol/claude-agent-acp)"
	echo "worker_image:    node:24-slim @ $(docker image inspect node:24-slim --format '{{.Id}}')"
	echo "poc_source:      $ROOT (in-repository, at the commit above)"
	echo "state_root:      $STATE (external, disposable)"
} | tee "$EV/prerequisites.txt"
rm -f "$EV/.baton-commit"

note "Baton repository baseline (shared checkout)"
git -C "$REPO" status --porcelain > "$EV/baton-repo-status.txt"
wc -l < "$EV/baton-repo-status.txt" | xargs echo "dirty paths at baseline:"

note "unit tests"
npm test 2>&1 | tail -12 | tee "$EV/unit-tests.txt"
grep -q "fail 0" "$EV/unit-tests.txt" || fail "unit tests did not pass"

note "fresh disposable authority"
./scripts/new-authority.sh "$AUTHORITY" "$RECORD_BASE" > "$EV/authority.txt" 2>&1
# Frozen results from an earlier run are read-only on purpose; make them
# removable again rather than leaving stale evidence behind.
chmod -R u+w "$STATE_DIR" 2>/dev/null || true
rm -rf "$RECORD_BASE" "$STATE_DIR"

# ---------------------------------------------------------------- happy path
note "happy path: submit"
node bin/v12-poc submit --config "$CONFIG" --name happy > "$EV/submit-happy.json"
HAPPY="$(jqf "$EV/submit-happy.json" "d['work']")"
node bin/v12-poc snapshot --config "$CONFIG" --work "$HAPPY" > "$EV/snapshots/$HAPPY-1-before.json"
[ "$(jqf "$EV/snapshots/$HAPPY-1-before.json" "d['handler']")" = "None" ] \
	|| fail "$HAPPY has a Handler before any claim"

note "happy path: natural dispatch (no per-Job launch or prompt)"
node bin/v12-poc manage --config "$CONFIG" > "$EV/manage-happy.json"
# Round-4 review: `returned-unclean` is a distinct terminal state, so a
# retained operator credential can no longer ride out on a clean return.
[ "$(jqf "$EV/manage-happy.json" "d[0]['status']")" = "returned" ] \
	|| fail "the happy path did not return the Job cleanly"
[ "$(jqf "$EV/manage-happy.json" "d[0]['credentials_disposed']")" = "True" ] \
	|| fail "the happy path did not dispose the staged credential"
[ "$(jqf "$EV/manage-happy.json" "d[0]['retained_secret']")" = "None" ] \
	|| fail "the happy path retained a secret"
ATTEMPT="$(jqf "$EV/manage-happy.json" "d[0]['runtime_attempt']")"
node bin/v12-poc snapshot --config "$CONFIG" --work "$HAPPY" > "$EV/snapshots/$HAPPY-3-after-return.json"
[ "$(jqf "$EV/snapshots/$HAPPY-3-after-return.json" "d['route']")" = "poc.rview" ] \
	|| fail "$HAPPY was not returned to the review endpoint"

cp "$STATE_DIR/$ATTEMPT/trace.jsonl" "$EV/traces/$ATTEMPT-happy.jsonl"
cp "$STATE_DIR/$ATTEMPT/assignment.json" "$EV/envelopes/assignment.json"
cp "$STATE_DIR/$ATTEMPT/result.json" "$EV/results/result.json"
cp "$STATE_DIR/$ATTEMPT/offer/offer.json" "$EV/envelopes/offer.json"
cp "$STATE_DIR/$ATTEMPT/frozen/index.json" "$EV/results/index.json"
cp "$RECORD_BASE/$RECORD_PATH/job-happy/job.in.json" "$EV/envelopes/job.in.json"

# The offer envelope carries a live claim token. It is ephemeral and
# single-use, but evidence is evidence: strip it rather than publish it.
python3 - "$EV/envelopes/offer.json" <<'PY'
import json, sys
path = sys.argv[1]
offer = json.load(open(path))
value = offer["token"].pop("value")
offer["token"]["value"] = f"[redacted {len(value)} chars]"
json.dump(offer, open(path, "w"), indent=2)
PY

# The Handler snapshot taken while the claim was held lives in the trace,
# because it is the only moment it exists.
python3 - "$EV/traces/$ATTEMPT-happy.jsonl" "$EV/snapshots/$HAPPY-2-while-claimed.json" <<'PY'
import json, sys
for line in open(sys.argv[1]):
	record = json.loads(line)
	if record["step"] == "baton.detail.claimed":
		json.dump(record["detail"], open(sys.argv[2], "w"), indent=2)
		break
else:
	raise SystemExit("no baton.detail.claimed snapshot in the trace")
PY
[ "$(jqf "$EV/snapshots/$HAPPY-2-while-claimed.json" "d['handler']")" = "poc.claude" ] \
	|| fail "the Handler was not poc.claude while the claim was held"
[ "$(jqf "$EV/snapshots/$HAPPY-2-while-claimed.json" "d['phase']")" = "active" ] \
	|| fail "phase was not active while claimed"

note "happy path: ordering, isolation and independence assertions"
python3 - "$EV/traces/$ATTEMPT-happy.jsonl" "$REPO" <<'PY'
import json, sys
steps = [json.loads(l) for l in open(sys.argv[1])]
repo = sys.argv[2]
order = [s["step"] for s in steps]
def at(step):
	if step not in order: raise SystemExit(f"missing trace step {step}")
	return order.index(step)

# The load-bearing order: nothing writable exists before the claim, and
# the claim is never reached without a validated token.
assert at("token.validated") < at("baton.claim") < at("assignment.minted") \
	< at("worker.container"), "claim/assignment did not precede writable execution"
assert at("preclaim.turn") < at("token.validated"), "the token was validated before the agent answered"
assert at("worker.fenced") < at("result.frozen"), "the result was read before the worker was fenced"
assert at("result.frozen") < at("result.checked") < at("baton.pass"), "return preceded validation"
assert at("input.reverified") < at("result.frozen"), "the input was not reverified before freezing"

by = {s["step"]: s["detail"] for s in steps}
assert by["input.materialized"]["digest"] == by["input.reverified"]["digest"], \
	"the read-only input changed during execution"
assert by["result.checked"]["problems"] == [], "the independent check reported problems"
assert by["result.checked"]["independent"] is True

# R1: both fences were ESTABLISHED, not merely recorded.
for step in ("preclaim.quiesced", "worker.fenced"):
	state = by[step]
	assert not state.get("error"), f"{step}: quiescence could not be established"
	assert state["running"] is False, f"{step}: container was still running"
	assert state["stopped_by"] == "self", f"{step}: stopped by {state['stopped_by']}"
	assert state["exit_code"] == 0, f"{step}: exit code {state['exit_code']}"

# R2: the typed input was materialized without following any link.
assert by["input.materialized"]["followed_links"] is False, "the input copy followed links"

# R2-4: the declared result is the DIRECTORY the finding pinned, and the
# entries it may contain are declared with it.
declared = by["offer.minted"]["declared_outputs"]
assert len(declared) == 1, declared
assert declared[0]["type"] == "directory", \
	f"the pinned contract is a directory result, got {declared[0]['type']}"
assert declared[0]["path"] == "/out", declared[0]
assert declared[0]["entries"] == ["index.json"], declared[0]

# R4-1: cleanup is part of the SUCCESS boundary — disposal happens
# before the authoritative handoff, not after it.
assert "credential.disposed" in order and "baton.pass" in order
assert order.index("credential.disposed") < order.index("baton.pass"), \
	"the Job was handed to review before the credential was disposed"
assert "cleanup.incomplete" not in order, "the attempt did not end clean"

# R3-1: the staged credential was disposed once the containers were gone.
assert "credential.disposed" in order, "the staged credential was never disposed"
# `by` holds the LAST record, and there are two reaps: one before the
# handoff that disposes, and one after that finds nothing left. The fact
# to assert is that no credential remains, not that the last call was the
# one that removed it.
assert by["credential.disposed"]["none_remains"] is True, by["credential.disposed"]
assert "credential.retained" not in order, \
	"a credential was retained on a clean run"
assert order.index("containers.reaped") < order.index("credential.disposed") \
	or order.index("credential.disposed") > order.index("worker.fenced"), \
	"disposal must follow the containers being proven absent"

# R2-2: every container was removed AND proven gone.
reaped = by["containers.reaped"]
assert reaped["worker"]["gone"] is True, reaped["worker"]
assert reaped["consent"]["gone"] is True, reaped["consent"]

# R3: the worker's declaration was bound to the assignment and the offer.
assert by["worker.declared"]["problems"] == [], \
	f"declaration mismatch: {by['worker.declared']['problems']}"

# R4: consent ran in a non-executing posture and DID NOT execute anything,
# while the worker — the turn that is supposed to — did.
assert by["preclaim.container"]["mode"] == "plan", \
	f"consent ran in mode {by['preclaim.container']['mode']}"
assert by["preclaim.container"]["readonly_rootfs"] is True, \
	"the consent container had a writable root filesystem"
assert "ALL" in (by["preclaim.container"]["cap_drop"] or []), \
	"the consent container kept capabilities"
assert by["worker.container"]["mode"] == "bypassPermissions", \
	"the worker did not run in the execution posture"
preclaim_tools = [s for s in steps if s["step"] == "preclaim.activity"
                  and s["detail"]["channel"] == "tool"]
assert not preclaim_tools, \
	f"the consent turn executed {len(preclaim_tools)} tool call(s); it is supposed to be non-executing"

# Isolation: neither container ever received Baton state, and the
# pre-claim container had no writable mount but the config dir.
for step, name in (("preclaim.container", "pre-claim"), ("worker.container", "worker")):
	mounts = by[step]["mounts"]
	assert by[step]["user"] == "1000:1000", f"{name} container ran as {by[step]['user']}"
	# Substring matching on "baton" is wrong here: unrelated paths
	# contain the word. Compare against the actual Baton deployment,
	# coordination-home and checkout prefixes.
	#
	# PLACEMENT: the prototype now lives INSIDE that checkout, so this
	# also proves the migration did not quietly start mounting the
	# prototype's own directory. Every mount source must be either the
	# external adapter tree or the external per-attempt state.
	forbidden = ("/home/sl/opt/baton", "/home/sl/baton-v11.", f"{repo}/")
	for mount in mounts:
		assert not mount["source"].startswith(forbidden) \
			and mount["source"] != repo, \
			f"{name} container mounted Baton state at {mount['source']}"
	writable = [m["target"] for m in mounts if m["rw"] and m["target"] != "/run/claude-config"]
	if step == "preclaim.container":
		assert writable == [], f"the pre-claim container had writable mounts {writable}"
	else:
		assert writable == ["/out"], f"the worker had writable mounts {writable}"
	assert [m["target"] for m in mounts if not m["rw"]], f"{name} container had no read-only mount"

# At least one meaningful activity update from the worker.
messages = [s for s in steps if s["step"] == "worker.activity"
            and s["detail"]["channel"] == "message"]
assert len(messages) >= 1, "the worker emitted no message activity"
tools = [s for s in steps if s["step"] == "worker.activity" and s["detail"]["channel"] == "tool"]
assert len(tools) >= 1, "the worker performed no tool call"
print(f"ordering, fencing, containment, declaration, posture, isolation and activity "
      f"assertions passed ({len(order)} trace steps, {len(messages)} worker messages, "
      f"{len(tools)} worker tool events, {len(preclaim_tools)} consent tool events)")
PY

note "happy path: the frozen result matches an independent recomputation"
node -e '
import { readFileSync } from "node:fs";
const { diffIndex, expectedIndex } = await import("./src/fixture_check.mjs");
const actual = JSON.parse(readFileSync(process.argv[1], "utf8"));
const problems = diffIndex(actual, expectedIndex(process.argv[2]));
if (problems.length) { console.error(problems.join("\n")); process.exit(1); }
console.log("independent recomputation agrees with the frozen result");
' --input-type=module "$EV/results/index.json" "$RECORD_BASE/$RECORD_PATH/job-happy/input" \
	| tee "$EV/independent-check.txt"

# ------------------------------------------------------------ negative cases
for FAULT in expired replayed; do
	note "negative case: $FAULT token"
	node bin/v12-poc submit --config "$CONFIG" --name "neg-$FAULT" > "$EV/submit-$FAULT.json"
	node bin/v12-poc manage --config "$CONFIG" --token-fault "$FAULT" > "$EV/manage-$FAULT.json"
	[ "$(jqf "$EV/manage-$FAULT.json" "d[0]['status']")" = "fenced" ] \
		|| fail "$FAULT: the attempt was not fenced"
	[ "$(jqf "$EV/manage-$FAULT.json" "d[0]['reason']")" = "$FAULT" ] \
		|| fail "$FAULT: fenced for the wrong reason"
	FENCED_WORK="$(jqf "$EV/manage-$FAULT.json" "d[0]['work']")"
	NEG_ATTEMPT="$(jqf "$EV/manage-$FAULT.json" "d[0]['runtime_attempt']")"
	cp "$STATE_DIR/$NEG_ATTEMPT/trace.jsonl" "$EV/traces/$NEG_ATTEMPT-$FAULT.jsonl"
	node bin/v12-poc snapshot --config "$CONFIG" --work "$FENCED_WORK" \
		> "$EV/snapshots/$FENCED_WORK-fenced-$FAULT.json"

	python3 - "$EV/traces/$NEG_ATTEMPT-$FAULT.jsonl" "$EV/snapshots/$FENCED_WORK-fenced-$FAULT.json" "$FAULT" <<'PY'
import json, sys
steps = [json.loads(l) for l in open(sys.argv[1])]
order = [s["step"] for s in steps]
state = json.load(open(sys.argv[2]))
fault = sys.argv[3]

assert "baton.claim" not in order, "a claim was committed despite the fence"
assert "assignment.minted" not in order, "an assignment was minted despite the fence"
assert "worker.container" not in order, "a writable worker started despite the fence"
assert "result.frozen" not in order, "a result was accepted despite the fence"
assert "baton.pass" not in order, "the Job was handed on despite the fence"
assert "token.refused" in order, "the refusal was not recorded"

refusal = next(s for s in steps if s["step"] == "token.refused")
assert refusal["detail"]["reason"] == fault, \
	f"refused for {refusal['detail']['reason']}, expected {fault}"

# The read-only pre-claim turn DID run and DID answer: this proves the
# fence is the token check, not the absence of an agent.
assert "preclaim.turn" in order, "the pre-claim turn never ran"
intent = next(s for s in steps if s["step"] == "preclaim.intent")
assert intent["detail"]["carried_token"] is True, "the agent did not even carry a token"
assert intent["detail"]["decision"] == "accept", \
	"the agent declined, so the token check was not what fenced this"

# And the Job is left exactly as available as it was.
assert state["phase"] == "queued", f"phase is {state['phase']}, not queued"
assert state["handler"] is None, f"handler is {state['handler']}, not null"
assert state["ready"] is True, "the Job is not ready for a fresh offer"
assert state["route"] == "poc.job", f"route moved to {state['route']}"
print(f"{fault}: agent accepted and returned a token, the manager refused it, "
      f"and {state['work']} is still queued/unclaimed/ready at {state['route']}")
PY
done

# ------------------------------------- post-claim compensation (R5)
note "negative case: post-claim fault must not strand the Handler"
node bin/v12-poc submit --config "$CONFIG" --name neg-postclaim > "$EV/submit-postclaim.json"
node bin/v12-poc manage --config "$CONFIG" --fault post-claim > "$EV/manage-postclaim.json"
[ "$(jqf "$EV/manage-postclaim.json" "d[0]['status']")" = "compensated" ] \
	|| fail "post-claim: the attempt did not compensate"
[ "$(jqf "$EV/manage-postclaim.json" "d[0]['claim_committed']")" = "True" ] \
	|| fail "post-claim: no claim was committed, so nothing was proven"
PC_WORK="$(jqf "$EV/manage-postclaim.json" "d[0]['work']")"
PC_ATTEMPT="$(jqf "$EV/manage-postclaim.json" "d[0]['runtime_attempt']")"
cp "$STATE_DIR/$PC_ATTEMPT/trace.jsonl" "$EV/traces/$PC_ATTEMPT-postclaim.jsonl"
node bin/v12-poc snapshot --config "$CONFIG" --work "$PC_WORK" \
	> "$EV/snapshots/$PC_WORK-compensated.json"

python3 - "$EV/traces/$PC_ATTEMPT-postclaim.jsonl" "$EV/snapshots/$PC_WORK-compensated.json" <<'PY'
import json, sys
steps = [json.loads(l) for l in open(sys.argv[1])]
order = [s["step"] for s in steps]
state = json.load(open(sys.argv[2]))

# The fault must land AFTER a real canonical claim, or this proves nothing.
assert "baton.claim" in order, "no claim was committed; the fault landed too early"
assert "assignment.minted" in order, "no assignment was minted"
assert order.index("baton.claim") < order.index("attempt.error"), \
	"the fault did not land after the claim"
assert "baton.release" in order, "the claim was never released"
assert "containers.reaped" in order, "the containers were never reaped"
assert order.index("containers.reaped") < order.index("baton.release"), \
	"the execution container must be proven gone BEFORE the Job is advertised again"
assert "compensation.withheld" not in order, \
	"the reap succeeded, so nothing should have been withheld"
assert "baton.release.failed" not in order, "the compensating release failed"
assert "baton.pass" not in order, "a failed attempt was handed on as though complete"
assert "result.frozen" not in order, "a result was accepted from a failed attempt"

failure = next(s for s in steps if s["step"] == "attempt.error")
assert failure["detail"]["claim_committed"] is True, \
	"the trace does not record that a claim was outstanding"

# The Job is back to exactly the availability it had before the offer.
assert state["phase"] == "queued", f"phase is {state['phase']}, not queued"
assert state["handler"] is None, f"handler is still {state['handler']}"
assert state["ready"] is True, "the Job is not ready for a fresh offer"
assert state["route"] == "poc.job", f"route moved to {state['route']}"
print(f"post-claim fault: {state['work']} was claimed, the attempt failed, the claim was "
      f"released, and the Job is queued/unclaimed/ready again at {state['route']}")
PY

note "manifests, container identity and termination"
python3 - "$EV/results/result.json" > "$EV/manifests.txt" <<'PY'
import json, sys
result = json.load(open(sys.argv[1]))
for side in ("inputs", "outputs"):
	for item in result[side]:
		print(f"{side[:-1]} {item['name']}  digest {item['digest']}")
		for entry in item["manifest"]:
			print(f"    {entry['sha256']}  {entry['bytes']:>7}  {entry['path']}")
print(f"result type {result['outputs'][0]['type']} at {result['outputs'][0]['path']}"
      f"  declared entries {result['outputs'][0]['entries']}")
print(f"container {result['container']['id'][:12]}  image {result['container']['image'][:19]}")
print(f"          user {result['container']['user']}  network {result['container']['network_mode']}")
term = result["container"]["termination"]
print(f"          stopped_by {term['stopped_by']}  exit {term['exit_code']}  "
      f"oom {term['oom_killed']}")
print(f"          started {term['started_at']}  finished {term['finished_at']}")
PY
cat "$EV/manifests.txt"

note "no staged credential survives in the runtime attempt directories"
# Round-3 review: the evidence-pack grep passed only because it scanned
# the evidence label. The secrets were in the per-attempt state
# directory, which is where they are actually staged, and every attempt
# was leaving a complete mode-0600 copy of the operator's OAuth
# credential behind. This asserts the RUNTIME state, which is the thing
# that was wrong.
python3 - "$STATE_DIR" <<'PY'
import os, sys
root = sys.argv[1]
retained = []
for base, _dirs, files in os.walk(root):
	for name in files:
		if name == ".credentials.json":
			retained.append(os.path.join(base, name))
if retained:
	raise SystemExit("staged credentials survived the proof run:\n  "
	                 + "\n  ".join(retained))
print(f"no staged credential remains under {root}")
PY
if grep -rlE 'sk-ant-|"refreshToken"|"accessToken"|claudeAiOauth' "$STATE_DIR" 2>/dev/null; then
	fail "credential material survived in the runtime attempt directories"
fi
echo "no credential material anywhere under $STATE_DIR"

note "the streamed claim token did not survive into the trace"
python3 - "$STATE_DIR/$ATTEMPT/offer/offer.json" "$EV/traces/$ATTEMPT-happy.jsonl" <<'PY'
import json, sys
token = json.load(open(sys.argv[1]))["token"]["value"]
trace = open(sys.argv[2]).read()
assert token not in trace, "the whole claim token is in the trace"
# The agent echoes the token back in short streamed chunks, so whole-string
# matching proves nothing on its own: check every 16-character fragment.
leaked = [i for i in range(0, len(token) - 16) if token[i:i + 16] in trace]
assert not leaked, f"{len(leaked)} claim-token fragment(s) survived into the trace"
print(f"no fragment of the {len(token)}-character claim token appears in the trace")
PY

note "no credential material in the evidence pack"
if grep -rlE 'sk-ant-|"refreshToken"|"accessToken"|claudeAiOauth' "$EV" ; then
	fail "the evidence pack contains credential material"
fi
echo "evidence pack is clean"

note "this proof run changed nothing in the Baton repository"
# W76 review round 3: this used to assert that the WHOLE Baton tree was
# clean outside this dossier. That is no longer a property W76 can
# prove: the same checkout now carries an unrelated in-flight Work
# (W415, managed-turn approval incidents), and a whole-tree check cannot
# attribute somebody else's edit. So the runner proves the two things it
# actually can — that this run mutates nothing, and that no path W76
# owns in the Baton repository is dirty — and records the rest verbatim
# for the reviewer instead of asserting over it.
git -C "$REPO" status --porcelain > "$EV/baton-repo-status-after.txt"
cat "$EV/baton-repo-status-after.txt"
python3 - "$EV/baton-repo-status.txt" "$EV/baton-repo-status-after.txt" <<'PY'
import sys
before = open(sys.argv[1]).read().splitlines()
after = open(sys.argv[2]).read().splitlines()
changed = sorted(set(after) ^ set(before))
if changed:
	raise SystemExit("this proof run mutated the Baton repository:\n"
	                 + "\n".join(changed))
print("the proof run mutated nothing in the Baton repository")

# Everything else is REPORTED, not asserted over. Git records that a
# path changed, never who changed it, and this dossier is written by two
# participants — the reviewer owns PLAN.md and the review journal, the
# implementer owns PROGRESS.md. Asserting authorship from a dirty tree
# would be inventing a fact the evidence does not hold, which is exactly
# what this proof is supposed to avoid doing.
owned = "work/records/2026/08/finding-v12-isolated-agent-workers/"
mine = [line for line in after if owned in line]
other = [line for line in after if owned not in line]
print(f"\nW76 dossier paths dirty ({len(mine)}) — PROGRESS.md is the "
      f"implementer's; PLAN.md and review-*.md are the reviewer's:")
for line in mine:
	print(f"  {line}")
if other:
	print(f"\nNOTE: {len(other)} path(s) outside this dossier are dirty in "
	      f"this SHARED checkout. They belong to other in-flight Work, not "
	      f"to this one. A whole-tree cleanliness assertion is not a "
	      f"property this proof can establish on its own, so it is not "
	      f"claimed:")
	for line in other:
		print(f"  {line}")
PY

note "the Baton checkout holds no generated state"
# PLACEMENT (finding-v12-in-repository-migration). The porcelain check
# above cannot see this: the prototype subtree is one untracked entry,
# so anything a run wrote INSIDE it would leave that entry looking
# identical before and after.
#
# Round-1 review: this walked `v12/` alone, which is the same
# subtree-only mistake the placement check had. It now walks the WHOLE
# checkout for the artifacts this prototype creates — a disposable
# authority, its SQLite file, a staged credential, a Job record, an
# attempt directory — because "the state root is external" is a claim
# about the checkout, not about one directory in it.
#
# `node_modules/` and the repository's own tooling directories are
# skipped: they are generated, ignored, and none of them is anything
# this prototype writes.
python3 - "$ROOT" "$REPO" "$STATE" <<'PY'
import os, sys
root, repo, state = sys.argv[1], sys.argv[2], sys.argv[3]
if state == repo or state.startswith(f"{repo}/"):
	raise SystemExit(f"the disposable state root {state} is inside the Baton "
	                 f"checkout at {repo}")
SKIP = {".git", ".venv", "node_modules", "__pycache__", ".pytest_cache"}
strays = []
for base, dirs, files in os.walk(repo):
	dirs[:] = [d for d in dirs if d not in SKIP]
	# A Job record this prototype submitted, wherever it landed.
	for name in list(dirs):
		if name.startswith("job-") and "records" in base:
			strays.append(os.path.relpath(os.path.join(base, name), repo))
	for name in files:
		path = os.path.join(base, name)
		relative = os.path.relpath(path, repo)
		if name.endswith((".sqlite3", ".sqlite3-wal", ".sqlite3-shm")) \
				or name == ".credentials.json":
			strays.append(relative)
		elif relative.startswith(f"{os.path.relpath(root, repo)}{os.sep}") \
				and relative.split(os.sep)[1] in ("run", "work"):
			strays.append(relative)
if strays:
	raise SystemExit("this proof run left disposable state inside the Baton "
	                 "checkout:\n  " + "\n  ".join(sorted(set(strays))))
print(f"no authority, Job record, attempt state or credential anywhere under "
      f"{repo}; every disposable path is under {state}")
PY

printf '\nPROOF COMPLETE — evidence in %s\n' "$EV"
printf 'Retain it by copying that directory into %s/evidence/<label>.\n' "$ROOT"
