# Progress

Not started. The 2026-09-01 decision is pinned and awaits an isolated v12
implementation attempt.

## Implementation — 2026-09-02

Actor: Claude Code agent (Opus 5) acting for sl@pushcoin.com, working in the
isolated v12 candidate tree `/tmp/dogfood-vhhwutrl/candidate`. No Git action
was taken: nothing was imported, staged, committed or otherwise mutated.

Exactly the two files named in `FINDING.md` "Confirmed patch boundary" were
changed.

1. `v12/worker/claude_agent.py` — `PROVIDER_ARGUMENTS` now reads
   `("--print", "--dangerously-skip-permissions", "--output-format", "json")`.
   The three-word `--permission-mode acceptEdits` fragment is replaced in place
   by the one activation flag. `--print`, `--output-format json` and the prompt
   as the final argv member (`argv = [PROVIDER_PROGRAM, *PROVIDER_ARGUMENTS,
   _prompt(task)]`) are preserved. The block comment above the tuple was
   rewritten in the same file so it records the W64268 ruling and names the two
   spellings deliberately not used, rather than continuing to explain
   `acceptEdits`.

2. `v12/python/tests/manager/test_claude_agent.py` — the golden vector in
   `TheProviderArgvAndEnvironmentAreClosed.
   test_the_argv_is_exactly_the_pinned_vector_plus_one_prompt` now pins
   `["claude", "--print", "--dangerously-skip-permissions", "--output-format",
   "json"]` with `len(argv) == 6`. A new sibling case,
   `test_the_inner_permission_policy_is_bypassed_and_not_re_spelled`, asserts
   that `--permission-mode`, `acceptEdits` and
   `--allow-dangerously-skip-permissions` are all absent from the composed argv
   and that `--dangerously-skip-permissions` occurs exactly once.

Nothing else was touched. `worker_manager/oci.py`, the OCI restriction and
mount vectors, host execution policy, the v11 runner, networking, the image
recipe and lifecycle are unchanged, as are every other production and test
file.

## Verification — 2026-09-02

Static, and complete for what a read can establish:

- A tree-wide search for `acceptEdits`, `--permission-mode`, `dangerously`,
  `PROVIDER_ARGUMENTS` and `len(argv)` shows the only surviving mentions of the
  superseded spellings are the explanatory prose in the two changed files. No
  product source composes `--permission-mode` any more.
- `"--print"` appears in exactly two places tree-wide — the provider tuple and
  the one golden case — confirming the finding's claim that the golden vector
  has a single owner and that no second expected-argv fixture was left stale.

Not established by this attempt:

- `python3 v12/python/tests/manager/test_claude_agent.py -v` was NOT run. Each
  attempt to execute it in this environment was refused as requiring approval,
  which is the same class of refusal this Work exists to remove; no escalation
  or workaround was attempted. The focused suite result is therefore unproved
  here and must be produced by the reviewer or by a worker running under the
  corrected boundary.
- Both live proofs required by `FINDING.md` "Required isolated verification"
  remain outstanding: that the rebuilt 2.1.247 image's `claude --help` names
  `--dangerously-skip-permissions`, and that one live provider task edits only
  its private candidate and runs its own ordinary Python verification without
  an approval request while the outer worker independently reruns the frozen
  command.
- The OCI vector and input-delivery gates were not re-run; the argument that
  the container posture is untouched rests on the patch boundary above, not on
  a fresh execution.

Status: awaiting independent review. Not imported.
