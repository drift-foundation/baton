#!/usr/bin/env bash
# W163 R9: the HARD prohibition boundary. The ACP agent subprocess runs
# inside a kernel mount namespace (bubblewrap, unprivileged) where every
# protected path is remounted READ-ONLY. No shell spelling, interpreter,
# alias, or renamed executable inside the session can mutate protected
# repository state: the kernel refuses the write. The PreToolUse hook
# remains only as an immediate friendly denial in front of this boundary.
# Deployment supplies AGENT_REAL and the protected-paths list beside
# this script. Missing configuration fails closed.
#
# W28681: THIS SCRIPT IS ALSO THE PROCESS DOMAIN, and that is a second
# duty rather than a detail of the first.
#
# The incident: five tool process groups left below one managed agent
# survived 34-36 hours and several later turns; four of them had called
# `setsid`, so they were in neither the bridge's process group nor its
# session, and the runaway sixth held a full core. A signal to the
# bridge's group could not reach any of them, and the bridge does not
# launch tool subprocesses so it cannot enumerate them either.
#
# `--unshare-pid` gives this launch its own PID namespace with
# bubblewrap as the minimal PID 1 reaper: a `setsid` inside escapes a
# process group and a session, and does not escape a namespace. When
# this process exits the namespace goes with it, so the supervisor's
# "kill the direct child and prove it exited" becomes a proof about
# EVERY descendant rather than about one process.
#
# `--die-with-parent` closes the other direction: a bridge that dies
# without tearing down takes its sandbox with it instead of leaving an
# orphaned domain nobody owns.
#
# Neither flag is optional in a managed configuration, and neither can
# be established from inside a nested sandbox — run
# `preflight-process-domain.sh` from the actual service launch context
# before installing this.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
PATHS_FILE="${PROTECTED_PATHS_FILE:-$HERE/protected-paths.txt}"
: "${AGENT_REAL:?AGENT_REAL (the real ACP agent executable) is required}"
[[ -r "$PATHS_FILE" ]] || { echo "launch-agent-sandboxed: $PATHS_FILE missing; refusing" >&2; exit 2; }
# W28681: the process domain FIRST, then the mount boundary. Both are
# properties of the same launch; the order here is only readability.
ARGS=(--unshare-pid --die-with-parent --dev-bind / /)
effective=0
while IFS= read -r path; do
	[[ -z "$path" || "$path" == \#* ]] && continue
	[[ -e "$path" ]] || { echo "launch-agent-sandboxed: protected path $path does not exist; refusing" >&2; exit 2; }
	ARGS+=(--ro-bind "$path" "$path")
	effective=$((effective + 1))
done < "$PATHS_FILE"
# W163 R11: zero effective entries would launch an UNCONTAINED agent.
# An empty or comment-only protection list is broken policy: refuse.
if [[ $effective -eq 0 ]]; then
	echo "launch-agent-sandboxed: $PATHS_FILE names no effective protected path; an uncontained launch is refused (fail closed)" >&2
	exit 2
fi
# Entries must identify ACTUAL Git metadata paths. Worktree-style
# checkouts keep a .git FILE pointing at the real gitdir elsewhere —
# protect the resolved gitdir (git rev-parse --absolute-git-dir), not
# an assumed .git directory.
exec bwrap "${ARGS[@]}" "$AGENT_REAL" "$@"
