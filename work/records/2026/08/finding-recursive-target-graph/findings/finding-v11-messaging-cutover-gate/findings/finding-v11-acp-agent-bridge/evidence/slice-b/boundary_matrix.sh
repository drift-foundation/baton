#!/usr/bin/env bash
# W163 R9: proves the kernel boundary itself — every configured
# prohibited Git history/index mutation (and arbitrary-interpreter
# writes to protected state) fails inside the sandbox regardless of
# spelling, while permitted reads and workspace writes succeed.
# Run: boundary_matrix.sh <repo-with-protected-.git>
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
# Self-provisioning (W163 R10): with no argument, a throwaway repo is
# created and protected, so the archived copy reproduces anywhere.
REPO="${1:-}"
if [ -z "$REPO" ]; then
	SCRATCH="$(mktemp -d)"
	trap 'rm -rf "$SCRATCH"' EXIT
	REPO="$SCRATCH/repo"
	git init -q "$REPO"
	git -C "$REPO" commit --allow-empty -q -m baseline
	export PROTECTED_PATHS_FILE="$SCRATCH/protected-paths.txt"
	printf '%s\n' "$REPO/.git" > "$PROTECTED_PATHS_FILE"
fi
failures=0
sandboxed() {
	AGENT_REAL=/bin/sh "$HERE/launch-agent-sandboxed.sh" -c "$1" >/dev/null 2>&1
}
check() {
	local expect="$1" label="$2" command="$3"
	sandboxed "$command"
	local status=$?
	local verdict="ALLOW"; [ $status -ne 0 ] && verdict="BLOCK"
	if [ "$verdict" = "$expect" ]; then echo "ok   $expect  $label"
	else echo "FAIL expected $expect got $verdict  $label"; failures=$((failures+1)); fi
}
cd "$REPO"
# prohibited history/index mutations — the COMPLETE class, any spelling
check BLOCK "commit"          "cd $REPO && git commit --allow-empty -m x"
check BLOCK "add"             "cd $REPO && touch f && git add f"
check BLOCK "reset"           "cd $REPO && git reset --hard"
check BLOCK "branch"          "cd $REPO && git branch b1"
check BLOCK "tag"             "cd $REPO && git tag t1"
check BLOCK "stash"           "cd $REPO && echo x > stashme && git stash"
check BLOCK "checkout -b"     "cd $REPO && git checkout -b b2"
check BLOCK "update-ref"      "cd $REPO && git update-ref refs/heads/main HEAD"
check BLOCK "alias commit"    "cd $REPO && git -c alias.c=commit c --allow-empty -m x"
check BLOCK "python .git write" "cd $REPO && python3 -c \"open('.git/probe','w')\""
check BLOCK "sh redirect .git"  "cd $REPO && echo x > .git/probe"
check BLOCK "rename attack"     "cp \$(command -v git) /tmp/notgit 2>/dev/null && cd $REPO && /tmp/notgit commit --allow-empty -m x"
# permitted operations through the same boundary
check ALLOW "git log"         "cd $REPO && git log --oneline"
check ALLOW "git status"      "cd $REPO && git status"
check ALLOW "git diff"        "cd $REPO && git diff"
check ALLOW "workspace write" "cd $REPO/.. && echo ok > boundary-allowed.txt"
# --- R11: broken protection lists REFUSE the launch itself ---------------
refuse_case() {
	local label="$1" paths_content="$2" missing="$3"
	local scratch_file
	scratch_file="$(mktemp)"
	if [ "$missing" = "missing" ]; then
		rm -f "$scratch_file"
	else
		printf '%s' "$paths_content" > "$scratch_file"
	fi
	PROTECTED_PATHS_FILE="$scratch_file" AGENT_REAL=/bin/true \
		"$HERE/launch-agent-sandboxed.sh" >/dev/null 2>&1
	local status=$?
	rm -f "$scratch_file"
	if [ $status -eq 2 ]; then echo "ok   REFUSE $label"
	else echo "FAIL expected launch refusal (2) got $status  $label"; failures=$((failures+1)); fi
}
refuse_case "empty protection list" "" present
refuse_case "comments-only list" "# nothing protected
# still nothing
" present
refuse_case "missing list file" "" missing
refuse_case "nonexistent entry" "/nonexistent/gitdir
" present

echo "----"
if [ $failures -eq 0 ]; then echo "boundary matrix: all cases hold"; exit 0; fi
echo "boundary matrix: $failures FAILURES"; exit 1
