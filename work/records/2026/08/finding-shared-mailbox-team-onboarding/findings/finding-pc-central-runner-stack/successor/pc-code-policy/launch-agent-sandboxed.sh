#!/usr/bin/env bash
# W163 R9: the HARD prohibition boundary. The ACP agent subprocess runs
# inside a kernel mount namespace (bubblewrap, unprivileged) where every
# protected path is remounted READ-ONLY. No shell spelling, interpreter,
# alias, or renamed executable inside the session can mutate protected
# repository state: the kernel refuses the write. The PreToolUse hook
# remains only as an immediate friendly denial in front of this boundary.
# Deployment supplies AGENT_REAL and the protected-paths list beside
# this script. Missing configuration fails closed.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
PATHS_FILE="${PROTECTED_PATHS_FILE:-$HERE/protected-paths.txt}"
: "${AGENT_REAL:?AGENT_REAL (the real ACP agent executable) is required}"
[[ -r "$PATHS_FILE" ]] || { echo "launch-agent-sandboxed: $PATHS_FILE missing; refusing" >&2; exit 2; }
ARGS=(--dev-bind / /)
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
