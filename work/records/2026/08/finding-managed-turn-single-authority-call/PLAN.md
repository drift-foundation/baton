# Plan — Invoke managed Baton mutations one command at a time

1. [confirmed 2026-08-23] Preserve the W415/W220 exact-command boundary; do
   not grant raw coordination-home write access or broad shell capability.
2. [superseded by item 2 below, 2026-08-23] Put one normative
   standalone-operation bullet in `AGENTS.md`, adjacent to the active-work
   claim and non-interactive managed-turn rules. State that every canonical
   Baton operation is one direct execution request, especially `claim`; do not
   combine it with a read, mutation, wrapper or shell control syntax. Preserve
   the current instruction to report an exact standalone failure rather than
   retrying with broader authority. Add a deterministic positive assertion to
   `tests/work/test_w101_role_instructions.py` so every required role policy
   retains this boundary.
3. [superseded by item 3 below, 2026-08-23] Strengthen
   `tools/codex-event-bridge/smoke/managed_baton_write.mjs`. Present one ready
   Work and ask the managed agent to run canonical `detail` and then canonical
   `claim`; read the exact completed turn with `thread/read includeTurns`, and
   require two separate agent `commandExecution` items whose second item is
   the fixed canonical claim. Also require the claim to commit, zero approval
   requests, and all existing raw-authority negative controls to remain green.
   Reuse the installed command-item shape already interpreted by
   `src/command_oracle.mjs`; do not change `exec_policy.mjs` or broaden its
   rules. Retain W220/W415 wrong identity/config/binary, wrapper, raw store and
   excluded-verb negatives unchanged.
2. [done 2026-08-23] The normative bullet is the FIRST rule of
   `AGENTS.md`'s "Non-interactive managed turns", immediately after "The
   active-work claim" — the claim it binds hardest is defined in the section
   above it. It states the one-standalone-request rule, names `claim` as the
   operation it binds above all, lists what it may not be combined with
   (another read, another mutation, a shell wrapper, `&&`, `;`, a pipe, a
   newline batch), says WHY — an exact canonical invocation is authorized and
   a batch containing one is a different command — and preserves the
   report-do-not-broaden rule. `test_the_required_policy_binds_one_operation_
   per_execution_request` asserts the phrases AND their position, because text
   a regression only greps for can drift to the bottom of a file and pass.
3. [done 2026-08-23; live half BLOCKED and reported] `readinessClaimOutcome`
   in `src/command_oracle.mjs` decides the ordered two-item shape: exactly two
   agent command items, the first the canonical read and the second the
   canonical claim, both terminal and completed, with no COMMAND approval
   correlated to either. Deliberately separate from `requestedItem`, which
   requires exactly one item and would refuse this shape. Eight deterministic
   regressions, including the defect itself — `detail` and `claim` in ONE item
   is refused as "exactly two", which a proof reading only the committed
   Handler would have accepted. The smoke presents ready Work, fixes both
   command strings including the claim's operation id, reads the exact turn
   back with `thread/read includeTurns`, and runs the oracle over it; every
   negative control is untouched and `exec_policy.mjs` is unchanged.
   THE LIVE RUN IS RED and is reported rather than asserted around — see items
   5 and 6.
4. [operator gate] Restart the managed Codex context, redeliver ready Work,
   and prove the standalone claim commits before closing this finding.
5. [operational finding 2026-08-23; BLOCKS the live half of item 3]
   `thread/read` with `includeTurns` on the running codex-cli 0.149.0 returned
   NO `commandExecution` item for a turn that demonstrably ran a command — its
   items were `userMessage` and an `agentMessage` carrying a real Python
   traceback from the deployed executable. A separate minimal probe reproduces
   it with one `/bin/echo`: three items, none of them a command item.
   `CommandExecutionThreadItem` IS in the installed schema's `ThreadItem`
   union, so this is the server not recording it. THIS IS THE PREMISE W2845's
   command oracle RESTS ON, and every command-item verdict in that matrix has
   the same exposure.
6. [operational finding 2026-08-23] The managed invocation ended in an
   UNHANDLED PYTHON TRACEBACK from `baton_work/cli.py entry`, not the typed
   JSON error every other refusal uses — consistent with the read-only
   database this Work is about. The same canonical commands succeed cleanly
   outside the sandbox, verified with no model involved against a scaffolded
   disposable home.
7. [changes requested 2026-08-23; independent review] Correct two P1 defects
   before the operator gate. First, the live thread's developer instruction
   still requires "exactly the one" operation while its turn now requires
   two; make the higher-priority instruction explicitly require the exact
   requested operations as separate direct execution requests, in order, and
   nothing else. Second, `readinessClaimOutcome` must require exit code 0 for
   BOTH completed items; it currently accepts a completed read at exit 7
   followed by a successful claim. Add nonzero-completed read and claim
   regressions, rerun the deterministic gates, and only then rerun the live
   smoke. If items remain absent under a coherent prompt, route that as a
   separate deployment/provider integration finding tied to W2845; do not
   weaken the oracle. Review: `review-2026-08-23T04-30-59Z.md`; evidence:
   `evidence/review-2026-08-23.txt`.

Reviewer baseline: 24/24 focused W101+W220 Python cases and 2/2 selected
role-instruction/command-oracle Node cases. Research evidence:
`evidence/reviewer-research-2026-08-23.txt`.
7. [changes requested 2026-08-23; independent review] Two P1: the smoke's
   thread-level developer instruction still said "exactly the ONE canonical
   Baton operation" while the turn asks for two, so the live failure could not
   diagnose anything; and `readinessClaimOutcome` required `completed` without
   reading `exitCode`, so a read at exit 7 beside a claim at exit 0 was the
   readiness shape.
   Review: `review-2026-08-23T04-30-59Z.md`.
7. [done 2026-08-23] Both closed. The developer contract now says what the
   rule says — the canonical operations asked for, in order, EACH AS ITS OWN
   STANDALONE DIRECT EXECUTION REQUEST — because a proof whose two halves
   disagree cannot diagnose anything, and I had changed the turn without
   re-reading the thread it runs in. Both items require `exitCode === 0`:
   COMPLETED IS THAT IT RAN, NOT THAT IT WORKED, and the read is the half that
   SUCCEEDED in the defect this Work exists for, so the one item the proof
   could not check was the one the original failure left looking healthy. Two
   mutations witnessed; a third — the instruction contradicting again — is
   recorded as not mechanically checkable, since no deterministic case can
   witness a model obeying the wrong half of a contradiction.
   Evidence: `evidence/correction-2026-08-23.txt`.
8. [routed out 2026-08-23 as W7989] The live re-test the review asked for was
   run with the contradiction removed and THE ABSENCE PERSISTS: the turn
   completed, its items were `userMessage` and an `agentMessage`, and there
   was no agent command item. Recorded separately, cross-referencing W2845, at
   `work/records/2026/08/finding-managed-turn-command-item-absent/`. W7830 is
   blocked on it. The W2845 edge could not be recorded from here —
   `baton.claude` is not its resolved handler while it sits with `baton.bug` —
   and is for its handler to add.
   ONE CORRECTION TO MY OWN EARLIER REPORT: the SMOKE run was confounded and
   could not have shown the server finding on its own. The two PROBES were
   not; the finding stands on them.
9. [cancelled by operator 2026-08-23] W7989 proved that the current managed
   custom-tool deployment cannot expose the strict structured live evidence.
   Keep the deterministic guardrail and regressions, but do not reconfigure
   v11 or claim the live gate passed. V12 owns the replacement boundary.
