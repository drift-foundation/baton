#!/usr/bin/env bash
# W163 R7/R8: the executable adversarial regression matrix for the
# fail-closed Git guard. Every case states its expected verdict; any
# mismatch fails this script. Run: policy/guard_matrix.sh [guard-path]
set -u
GUARD="${1:-$(dirname "$0")/block-git-commit.sh}"
failures=0

check() {
	local expect="$1"; shift
	local label="$1"; shift
	local payload="$1"
	printf '%s' "$payload" | "$GUARD" >/dev/null 2>&1
	local status=$?
	local verdict="ALLOW"; [ $status -ne 0 ] && verdict="BLOCK"
	if [ "$verdict" = "$expect" ]; then
		echo "ok   $expect  $label"
	else
		echo "FAIL expected $expect got $verdict  $label"
		failures=$((failures + 1))
	fi
}

cmd() { python3 -c "import json,sys; print(json.dumps({'tool_input':{'command':sys.argv[1]}}))" "$1"; }

# --- prohibited mutations, plain spellings -------------------------------
check BLOCK "plain commit"            "$(cmd 'git commit --allow-empty -m test')"
check BLOCK "-C form"                 "$(cmd 'git -C /tmp/repo commit -m x')"
check BLOCK "cd chain"                "$(cmd 'cd repo && git commit -m x')"
check BLOCK "--git-dir reset"         "$(cmd 'git --git-dir=/x/.git reset --hard')"
check BLOCK "-c config commit"        "$(cmd 'git -c user.name=x commit')"
check BLOCK "push"                    "$(cmd 'git push origin main')"
check BLOCK "rebase"                  "$(cmd 'git rebase -i HEAD~3')"
check BLOCK "cherry-pick"             "$(cmd 'git cherry-pick abc123')"
check BLOCK "filter-branch"           "$(cmd 'git filter-branch --all')"
check BLOCK "reflog expire"           "$(cmd 'git reflog expire --all')"
check BLOCK "gc"                      "$(cmd 'git gc --prune=now')"
check BLOCK "merge"                   "$(cmd 'git merge feature')"
check BLOCK "revert"                  "$(cmd 'git revert HEAD')"
check BLOCK "update-ref"              "$(cmd 'git update-ref refs/heads/main abc')"
# --- attached separators (R7) --------------------------------------------
check BLOCK "attached semicolon"      "$(cmd 'git commit;true')"
check BLOCK "semicolon prefix"        "$(cmd 'true;git commit -m x')"
check BLOCK "attached and-chain"      "$(cmd 'git commit&&true')"
check BLOCK "attached pipe"           "$(cmd 'git commit|cat')"
check BLOCK "attached background"     "$(cmd 'git commit&')"
# --- wrappers (R7) --------------------------------------------------------
check BLOCK "env assignment wrapper"  "$(cmd 'env X=1 git commit -m x')"
check BLOCK "bare assignment prefix"  "$(cmd 'X=1 git commit -m x')"
check BLOCK "sudo -E"                 "$(cmd 'sudo -E git commit -m x')"
check BLOCK "nohup"                   "$(cmd 'nohup git commit -m x')"
check BLOCK "timeout duration"        "$(cmd 'timeout 5 git commit -m x')"
check BLOCK "pipe into xargs git"     "$(cmd 'echo x | xargs git commit -m')"
check BLOCK "backslash escape"        "$(cmd '\git commit -m x')"
check BLOCK "absolute path git"       "$(cmd '/usr/bin/git commit -m x')"
# --- nested shells and substitutions (R7) --------------------------------
check BLOCK "bash -c"                 "$(cmd 'bash -c "git commit -m x"')"
check BLOCK "sh -c chained"           "$(cmd 'sh -c "cd repo && git commit -m x"')"
check BLOCK "bash -lc"                "$(cmd 'bash -lc "git commit -m x"')"
check BLOCK "shell script arg w/ git" "$(cmd 'bash run.sh git commit')"
check BLOCK "command substitution"    "$(cmd 'echo $(git commit -m x)')"
check BLOCK "backtick substitution"   "$(cmd 'echo `git commit -m x`')"
check BLOCK "process substitution"    "$(cmd 'diff <(git commit) /dev/null')"
check BLOCK "eval"                    "$(cmd 'eval "git commit -m x"')"
# --- fail-closed inputs (R7) ---------------------------------------------
check BLOCK "malformed JSON"          '{not json'
check BLOCK "non-string command"      '{"tool_input":{"command":42}}'
check BLOCK "unterminated quote git"  "$(cmd "git commit -m 'unterminated")"
check BLOCK "unknown flag obscuring"  "$(cmd 'git --weird-flag commit -m x')"
# --- R9-named hook gaps ---------------------------------------------------
check BLOCK "git add"                 "$(cmd 'git add tracked.txt')"
check BLOCK "git stash"               "$(cmd 'git stash')"
check BLOCK "git checkout branch"     "$(cmd 'git checkout -b side')"
check BLOCK "git branch"              "$(cmd 'git branch b1')"
check BLOCK "git tag"                 "$(cmd 'git tag v1')"
check BLOCK "git restore"             "$(cmd 'git restore .')"
check BLOCK "alias definition"        "$(cmd 'git -c alias.c=commit c --allow-empty -m x')"
check BLOCK "nice with value"         "$(cmd 'nice -n 5 git commit -m x')"
check BLOCK "sudo -u value"           "$(cmd 'sudo -u nobody git commit -m x')"
# --- permitted operations stay permitted ---------------------------------
check ALLOW "git log"                 "$(cmd 'git log --oneline')"
check ALLOW "git status"              "$(cmd 'git status')"
check ALLOW "git diff chained"        "$(cmd 'cd repo && git diff --stat')"
check ALLOW "prose mentioning commit" "$(cmd 'bin/baton say body="the words git commit inside prose"')"
check ALLOW "plain echo"              "$(cmd 'echo hello > allowed.txt')"
check ALLOW "bash -c harmless"        "$(cmd 'bash -c "ls -la"')"
check ALLOW "env wrapper harmless"    "$(cmd 'env X=1 ls')"
check ALLOW "unterminated no git"     "$(cmd "echo 'unterminated")"
check ALLOW "substitution no git"     "$(cmd 'echo $(date)')"

echo "----"
if [ $failures -eq 0 ]; then
	echo "guard matrix: all cases hold"
	exit 0
fi
echo "guard matrix: $failures FAILURES"
exit 1
