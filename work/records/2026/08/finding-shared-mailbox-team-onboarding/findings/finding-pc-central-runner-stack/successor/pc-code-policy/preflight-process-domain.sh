#!/usr/bin/env bash
# W28681: prove THIS launch context can create the process domain the managed
# ACP configuration requires, and that terminating the domain owner actually
# removes the tool descendants the incident found.
#
# Why a separate script rather than a check inside the launcher: an
# unprivileged PID namespace is a property of the SERVICE LAUNCH CONTEXT, not
# of the repository or of any agent turn. A managed reviewer sandbox is refused
# with "No permissions to create new namespace" and cannot certify the host
# either way, so this has to be run where the service actually starts -- and it
# has to be possible to run it without starting anything.
#
# REVIEW [P1], FIRST CORRECTION: this script used to run a pid echo inside
# bubblewrap and accept 1 or 2. That proves a namespace exists and says nothing
# about the acceptance invariant -- that killing the domain owner removes a
# DETACHED, session-leader descendant.
#
# REVIEW [P0], SECOND CORRECTION, AND IT IS THE SAME MISTAKE THE INCIDENT WAS
# ABOUT. The first correction identified its descendants with `pgrep -f` on
# tokens -- and those tokens are inside the shell program passed as an ARGUMENT
# to bubblewrap, so the OWNER'S OWN ARGV satisfied both "the descendant
# started" checks. When the owner exited the tokens went with it, and the
# script called that reaping. A stand-in `bwrap` whose whole body is a sleep
# passed this gate. Bracketing the pattern stops the MATCHER matching itself;
# it does nothing about the OWNER carrying the token.
#
# So NOTHING HERE IS PROVED BY MATCHING A COMMAND LINE. The descendants publish
# liveness by APPENDING to their own files -- something no argv can do -- and
# their exact host-visible pids are read out of the process tree below the
# owner. Those pids are required alive before termination and absent after it.
#
# Exit 0 means this context creates the domain AND the domain reaps its
# descendants. Any other exit means the managed configuration must not be
# installed here: the launcher would still contain the agent's writes and would
# NOT own its processes, which is the half of the boundary this Work exists
# for.
set -euo pipefail

WORK=""
OWNER=""
CONTROL=""

cleanup() {
	[ -n "$OWNER" ] && kill -KILL "$OWNER" 2>/dev/null || true
	[ -n "$CONTROL" ] && kill -KILL "$CONTROL" 2>/dev/null || true
	for one in ${SEEN:-}; do kill -KILL "$one" 2>/dev/null || true; done
	[ -n "$WORK" ] && rm -rf "$WORK" || true
}
trap cleanup EXIT

fail() { echo "preflight-process-domain: $*" >&2; exit "${2:-2}"; }

command -v bwrap >/dev/null 2>&1 \
	|| fail "bwrap is not on PATH in this launch context"
command -v setsid >/dev/null 2>&1 \
	|| fail "setsid is not on PATH; this probe needs it to make the exact
  escaped descendant the incident found"
command -v pgrep >/dev/null 2>&1 || fail "pgrep is not on PATH"

WORK="$(mktemp -d /tmp/w28681-preflight-XXXXXX)"
ESCAPED="$WORK/escaped.beat"
BUSY="$WORK/busy.beat"
OUTSIDE="$WORK/control.beat"

beats() { [ -r "$1" ] && wc -l < "$1" || echo 0; }

# EVERY PROCESS BELOW ONE PARENT, transitively, by host pid. This is the
# identity half: a pid is a fact about the process table, and an argv cannot
# forge one.
descendants() {
	local parent="$1" child
	for child in $(pgrep -P "$parent" 2>/dev/null || true); do
		printf '%s\n' "$child"
		descendants "$child"
	done
}

# THE CONTROL, outside the domain and started by THIS script so its pid is
# known exactly. A teardown that removed this too would be reaching past its
# own boundary, which the finding forbids as plainly as it requires the
# reaping.
setsid /bin/sh -c 'while :; do echo . >> "$0"; sleep 0.2; done' \
	"$OUTSIDE" >/dev/null 2>&1 &
CONTROL=$!

# THE DOMAIN, composed exactly as the launcher composes it: a PID namespace
# with bubblewrap as its minimal PID 1 reaper, and death tied to this parent.
# The two descendants publish liveness by appending to their own files.
bwrap --unshare-pid --die-with-parent --dev-bind / / \
	/bin/sh -c "
		setsid /bin/sh -c 'while :; do echo . >> \"\$0\"; sleep 0.2; done' \
			'${ESCAPED}' &
		/bin/sh -c 'i=0; while :; do i=\$((i+1));
			[ \$((i % 20000)) -eq 0 ] && echo . >> \"\$0\"; done' \
			'${BUSY}' &
		while :; do sleep 1; done
	" >/dev/null 2>&1 &
OWNER=$!

# BOTH DESCENDANTS ALIVE, proved by their files GROWING. An owner that starts
# nothing writes nothing, however long it is waited for.
first_escaped=0; first_busy=0
for _ in $(seq 1 20); do
	kill -0 "$OWNER" 2>/dev/null || fail "this launch context could not create
  the required PID namespace, or the domain owner died before its descendants
  started; the managed ACP configuration must not be installed here" 3
	a="$(beats "$ESCAPED")"; b="$(beats "$BUSY")"
	if [ "$a" -gt 0 ] && [ "$b" -gt 0 ] \
			&& [ "$a" -gt "$first_escaped" ] && [ "$b" -gt "$first_busy" ] \
			&& [ "$first_escaped" -gt 0 ] && [ "$first_busy" -gt 0 ]; then
		break
	fi
	[ "$a" -gt 0 ] && first_escaped="$a"
	[ "$b" -gt 0 ] && first_busy="$b"
	sleep 0.5
done
# THESE TWO ANSWER "DID THEY EVER RUN", and nothing else. The
# "have they stopped" question is asked further down, against a baseline taken
# after absence -- see the review [P1] note there.
held_escaped="$(beats "$ESCAPED")"; held_busy="$(beats "$BUSY")"
[ "$held_escaped" -gt 1 ] || fail "the escaped (setsid) descendant never ran
  inside the domain; nothing was started, so this probe would prove nothing
  about reaping it" 4
[ "$held_busy" -gt 1 ] || fail "the busy descendant never ran inside the
  domain" 4

# AND THEIR EXACT HOST IDENTITIES, read from the process tree rather than from
# any command line.
SEEN="$(descendants "$OWNER" | tr '\n' ' ')"
count=0
for one in $SEEN; do count=$((count + 1)); done
[ "$count" -ge 2 ] || fail "the domain owner has $count descendant(s) in the
  host process table; a domain that owns nothing cannot be shown to reap
  anything" 4

# TERMINATE THE OWNER AND AWAIT ITS EXIT. This is exactly what the bridge's
# bounded teardown does, and the question is whether that exit means the
# domain is empty.
kill -TERM "$OWNER" 2>/dev/null || true
for _ in $(seq 1 10); do
	kill -0 "$OWNER" 2>/dev/null || break
	sleep 0.5
done
if kill -0 "$OWNER" 2>/dev/null; then
	kill -KILL "$OWNER" 2>/dev/null || true
	fail "the domain owner did not exit on SIGTERM within five seconds" 5
fi
wait "$OWNER" 2>/dev/null || true

# Namespace teardown is the kernel's; give it a bounded moment rather than
# racing it.
for _ in $(seq 1 6); do
	still=""
	for one in $SEEN; do
		kill -0 "$one" 2>/dev/null && still="$one"
	done
	[ -z "$still" ] && break
	sleep 0.5
done

surviving=""
for one in $SEEN; do
	kill -0 "$one" 2>/dev/null && surviving="${surviving:+$surviving }$one"
done
[ -z "$surviving" ] || fail "host process(es) ${surviving} survived the domain
  owner's exit; this context creates a namespace that does not reap, so a tool
  that calls setsid would outlive its turn exactly as the incident found" 6

# AND THEY STOPPED WRITING. A pid can be reused; a file that stopped growing
# while the control's keeps growing is the second, independent statement.
#
# REVIEW [P1]: THE BASELINE IS TAKEN AFTER ABSENCE, and the first version took
# it before the signal. A descendant may append one last heartbeat between the
# count being read and the kernel tearing it down, so comparing post-teardown
# files to pre-signal counts called that final write evidence of survival --
# and a launcher that reaped its complete tree was REFUSED. The counts before
# teardown answer "did they ever run"; only counts taken after every recorded
# pid is proved absent can answer "have they stopped".
settled_escaped="$(beats "$ESCAPED")"; settled_busy="$(beats "$BUSY")"
sleep 1
[ "$(beats "$ESCAPED")" -eq "$settled_escaped" ] \
	|| fail "the escaped descendant is still writing after its domain owner
  exited and after every recorded pid was proved absent" 6
[ "$(beats "$BUSY")" -eq "$settled_busy" ] \
	|| fail "the busy descendant is still writing after its domain owner
  exited and after every recorded pid was proved absent" 6

kill -0 "$CONTROL" 2>/dev/null || fail "an UNRELATED process outside the domain
  was killed too; a teardown that reaches past its own boundary is not the
  boundary this configuration asks for" 7
control_now="$(beats "$OUTSIDE")"
sleep 0.5
[ "$(beats "$OUTSIDE")" -gt "$control_now" ] || fail "the unrelated control
  process outside the domain stopped running; a teardown that reaches past its
  own boundary is not the boundary this configuration asks for" 7

echo "preflight-process-domain: ok -- this context creates a PID namespace," \
	"runs an escaped (setsid) and a busy descendant inside it (${count} host" \
	"processes below the owner), removes every one of them when the owner" \
	"exits, and leaves an unrelated process running"
