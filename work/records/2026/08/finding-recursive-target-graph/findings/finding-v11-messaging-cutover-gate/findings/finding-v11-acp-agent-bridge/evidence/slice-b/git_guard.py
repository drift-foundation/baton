"""Deployment-owned hard denial (W163 R7): a FAIL-CLOSED enforcer for
Git history/index mutations beneath bypassPermissions.

Fail-closed contract: any input this guard cannot fully understand —
malformed hook JSON, a non-string command, an untokenizable command
line, a shell construct it cannot resolve that mentions git — DENIES
(exit 2). Attached POSIX operators are tokenized (punctuation mode,
not whitespace splitting), env/wrapper programs are unwrapped
iteratively, `sh|bash -c` strings are analyzed recursively, and
command substitutions that mention git deny outright. A blacklist
that merely fails to recognize a spelling can never allow it to run.
"""
import json
import re
import shlex
import sys

PROHIBITED = {"commit", "commit-tree", "rebase", "reset", "push",
              "cherry-pick", "filter-branch", "reflog", "gc", "prune",
              "am", "merge", "revert", "update-ref",
              # index/worktree mutations (W163 R9)
              "add", "checkout", "switch", "restore", "stash", "branch",
              "tag", "mv", "rm", "clean", "apply", "worktree"}
GIT_GLOBAL_WITH_VALUE = {"-C", "-c", "--git-dir", "--work-tree",
                         "--namespace", "--super-prefix",
                         "--config-env", "--exec-path"}
WRAPPERS = {"command", "nohup", "sudo", "env", "exec", "time", "nice",
            "stdbuf", "setsid", "ionice", "xargs", "timeout", "doas"}
# Wrapper flags that consume a following value (nice -n 5, sudo -u x).
WRAPPER_FLAGS_WITH_VALUE = {"-n", "-u", "-g", "-o", "-i", "--adjustment"}
SHELLS = {"sh", "bash", "zsh", "dash", "ksh", "fish"}
EVALUATORS = {"eval", "source", "."}
GIT_WORD = re.compile(r"\bgit\b")
SUBSTITUTION = re.compile(r"\$\(|`|<\(|>\(")
MAX_DEPTH = 8


def deny(reason):
    print(f"deployment policy: git history/index mutations are "
          f"prohibited (blocking PreToolUse hook; {reason})",
          file=sys.stderr)
    sys.exit(2)


def tokenize(command):
    """Attached-operator-safe tokenization; None means unparseable."""
    lexer = shlex.shlex(command, posix=True, punctuation_chars=True)
    lexer.whitespace_split = True
    try:
        return list(lexer)
    except ValueError:
        return None


def is_operator(token):
    return token != "" and all(ch in ";|&<>()" for ch in token)


def split_segments(tokens):
    segments, current = [], []
    for token in tokens:
        if is_operator(token):
            segments.append(current)
            current = []
        else:
            current.append(token)
    segments.append(current)
    return [segment for segment in segments if segment]


def check_git_segment(segment):
    """segment[0] is git; find the subcommand honestly or deny."""
    index = 1
    while index < len(segment):
        token = segment[index]
        # R9: an alias definition can rename any subcommand; it cannot
        # be resolved statically — fail closed on definition.
        if token == "-c" and index + 1 < len(segment) \
                and segment[index + 1].startswith("alias."):
            deny("git alias definition cannot be resolved")
        if any(token.startswith(pre) for pre in ("-calias.",)) \
                or token.startswith("--config-env=alias."):
            deny("git alias definition cannot be resolved")
        if token in GIT_GLOBAL_WITH_VALUE:
            index += 2
            continue
        if any(token.startswith(flag + "=")
               for flag in GIT_GLOBAL_WITH_VALUE):
            index += 1
            continue
        if token.startswith("-"):
            # Unknown global flag: whether it consumes a value is not
            # knowable here. Fail closed if anything prohibited could
            # follow; otherwise it cannot name a prohibited mutation.
            if any(entry in PROHIBITED for entry in segment[index:]):
                deny(f"unrecognized git flag {token!r} obscures the "
                     f"subcommand")
            return
        if token in PROHIBITED:
            deny(f"subcommand {token!r}")
        return
    return


def analyze(command, depth=0):
    if depth > MAX_DEPTH:
        deny("nesting depth exceeded")
    if not isinstance(command, str):
        deny("non-string command")
    # Substitutions cannot be resolved statically: if they appear in a
    # command that mentions git anywhere, deny rather than guess.
    if SUBSTITUTION.search(command) and GIT_WORD.search(command):
        deny("git inside a shell substitution")
    tokens = tokenize(command)
    if tokens is None:
        if GIT_WORD.search(command):
            deny("untokenizable command mentioning git")
        return
    for segment in split_segments(tokens):
        index = 0
        for _bound in range(len(segment)):
            if index >= len(segment):
                break
            token = segment[index]
            if "=" in token and not token.startswith("-") \
                    and "/" not in token.split("=", 1)[0]:
                index += 1                     # env assignment
                continue
            program = token.rsplit("/", 1)[-1].lstrip("\\")
            if program in WRAPPERS:
                index += 1
                if program == "timeout" and index < len(segment) \
                        and not segment[index].startswith("-"):
                    index += 1                 # the duration argument
                continue
            if token.startswith("-"):
                # wrapper flags; some consume the NEXT token as a value
                if token in WRAPPER_FLAGS_WITH_VALUE:
                    index += 2
                else:
                    index += 1
                continue
            break
        if index >= len(segment):
            continue
        program = segment[index].rsplit("/", 1)[-1].lstrip("\\")
        rest = segment[index + 1:]
        if program in SHELLS:
            flagged = [entry for entry in rest
                       if not entry.startswith("-")]
            if any(flag in ("-c", "-lc", "-ic") or
                   (flag.startswith("-") and "c" in flag)
                   for flag in rest if flag.startswith("-")):
                if not flagged:
                    deny("shell -c with no resolvable command")
                analyze(flagged[0], depth + 1)
            elif any(GIT_WORD.search(entry) for entry in rest):
                deny("shell invocation mentioning git that cannot "
                     "be resolved")
            continue
        if program in EVALUATORS:
            if any(GIT_WORD.search(entry) for entry in rest):
                deny("evaluator invocation mentioning git")
            continue
        if program == "git":
            check_git_segment([program, *rest])


def main():
    try:
        payload = json.load(sys.stdin)
        command = payload.get("tool_input", {}).get("command", "")
    except Exception:
        deny("malformed hook input")           # fail CLOSED
        return
    analyze(command)
    sys.exit(0)


main()
