# Plan: provision bounded Docker inspection

1. [done 2026-08-22] Extend the deployment-owned managed execution-policy
   generator with the four approved read-only Docker prefixes. Landed as a
   SECOND profile, `managed-docker-inspection`, printed from
   `profile=managed-docker-inspection` and taking no other operand — see the
   pinned decisions in `FINDING.md`.
2. [done 2026-08-22] Add positive coverage for each inspection prefix and
   negative coverage for unrestricted and representative mutable Docker
   commands. `tools/codex-event-bridge/test/docker_inspection_policy.test.mjs`,
   the new inspection cases in `test/exec_policy_cli.test.mjs`,
   `tests/work/test_w2845_docker_inspection_policy.py`, and the deployed-artifact
   matrix in `tests/work/test_deploy_v11.py`.
3. [done 2026-08-22] Verify policy generation, audit and installed-policy
   provisioning without weakening exact Baton workflow rules. The generator
   reproduces the installed live policy byte-for-byte, both preflights pass
   against it, and the same preflight reproduces the observed defect against
   the operator's pre-fix backup — `evidence/preflight-2026-08-22.txt`. The two
   profiles audit independently on the one nominated file.
   [pending — operator] The LIVE managed inspection. The preflight reads the
   nominated file and is not a measurement of the effective boundary; that is
   `tools/codex-event-bridge/smoke/exact_policy_matrix.mjs`, extended here with
   the four inspection positives and the unruled/mutable negatives. It is a
   manual run that spends real model turns and stages a copy of the operator's
   Codex credential, so it is not run from an implementer turn.
4. [done 2026-08-22] Returned for independent review.
5. [done 2026-08-22] Correct round-1 review [P1]: the preflight parsed one
   spelling of `prefix_rule` and treated every other valid construct as
   absent, so an unrestricted `docker` rule audited as satisfied. The module
   now ACCOUNTS for the whole file — decomposable rules, blank lines and `#`
   comments — and fails closed on anything else. The same correction closes
   the identical hole in the Baton workflow profile. Six new Node regressions
   using the installed `codex execpolicy` as the oracle, plus deployed-artifact
   coverage. 222 Node, 2873 pytest.
   Evidence: `evidence/correction-2026-08-22.txt`.
6. [done 2026-08-22] Correct round-2 review [P1]: the escape decoder claimed
   to understand Starlark strings and did not, so hex/Unicode/octal-escaped
   executables audited as exact. Only the three escapes this generator can
   emit are accepted; every other escape is UNACCOUNTED. Oracle regressions
   for both profiles, plus deployed-artifact coverage. 223 Node, 2873 pytest.
   Evidence: `evidence/correction-round2-2026-08-22.txt`.
7. [done 2026-08-22] Correct round-3 review [P1]: whole-file accounting
   skipped every JavaScript whitespace character, so a TAB before one exact
   rule audited as satisfied while the installed evaluator refused to parse
   the file at all — no rule in force, preflight green. The accepted
   whitespace is now SPACE and LF, measured against the evaluator rather
   than read off a grammar, a top-level construct must begin its line, and
   UNACCOUNTED is reported before missing/broad/extra. Oracle regressions on
   both profiles, plus deployed-artifact coverage. 227 Node, 2876 pytest.
   Evidence: `evidence/correction-round3-2026-08-22.txt`.
8. [done 2026-08-22] Correct round-4 review [P1]: `decompose` stopped at
   "every operand is a string literal" and never asked whether the evaluator
   ACCEPTS those literals, so a repeated named operand (silently overwritten),
   an empty pattern, and any decision string at all audited exact on files
   Codex refuses to load. A repeated operand, an empty pattern in either
   spelling, and a decision outside the MEASURED `allow`/`prompt`/`forbidden`
   domain are now UNACCOUNTED. Probing the evaluator added a fourth case the
   review did not have — a duplicate `decision`. The two `decision="deny"`
   unit cases, which asserted the audit's answer about a decision the
   evaluator rejects, now spell the restriction `forbidden`. Oracle
   regressions on both profiles in `test/policy_syntax.test.mjs` and
   `tests/work/test_w2845_docker_inspection_policy.py`, plus deployed-artifact
   coverage in `tests/work/test_deploy_v11.py`. 267 Node, 2847 + 52 pytest.
   Evidence: `evidence/correction-round4-2026-08-22.txt`.
9. [done 2026-08-22] Correct round-5 review [P1]: `splitTopLevel` discarded
   every empty comma-separated field, though only ONE empty tail is the valid
   trailing comma, so an empty head field, an empty middle field and a second
   trailing comma each reached the rest of the scanner as a well-formed
   operand list while the evaluator refused the whole file with `unexpected
   symbol ','`. Empty fields other than one tail are now UNACCOUNTED, in the
   call operand list and the pattern list alike. Probing added two forms the
   review did not have: a double trailing comma inside the pattern list, and
   an empty middle field in the positional spelling. Oracle regressions on
   both profiles in `test/policy_syntax.test.mjs` and
   `tests/work/test_w2845_docker_inspection_policy.py`, plus deployed-artifact
   coverage in `tests/work/test_deploy_v11.py`. 272 Node (one unrelated
   pre-existing failure, see `PROGRESS.md`), 2850 + 52 pytest, 55 ACP, 161 v12.
   Evidence: `evidence/correction-round5-2026-08-22.txt`.
   The review it answers:
   `splitTopLevel` discards every empty comma-separated field, so malformed
   pattern lists and call operand lists audit exact although the evaluator
   refuses the entire file. Preserve one valid trailing comma but make empty
   head/middle fields and a second trailing comma UNACCOUNTED; add pure-audit,
   evaluator-oracle, and deployed-artifact regressions for both profiles.
   Evidence: `evidence/fifth-review-empty-comma-fields-2026-08-22.txt`.
10. [done 2026-08-22] Sixth independent review [P2]: the round-5 comma-field
   correction is sound, but `readPolicy` rejects a TAB-only blank line that
   the installed evaluator accepts. This contradicts the measured boundary
   already recorded in `FINDING.md` and turns fail-closed into a fail-blind
   startup refusal. Account for evaluator-valid blank lines without widening
   the existing refusal of tabs before or inside statements; add pure-audit,
   evaluator-oracle, and deployed-artifact regressions for both profiles.
   Review: `review-2026-08-22T15-10-46Z.md`.
11. [done 2026-08-22] Correct round-6 review [P2]: `readPolicy` refused every
   `OTHER_WHITESPACE` character wherever it sat, so a tab-only blank line made
   an exact operator policy fail preflight although the evaluator loads it and
   authorizes the ruled inspections. Blank-line whitespace is now decided for
   the whole LINE and is exactly SPACE and TAB, measured per character against
   the evaluator; a tab before, inside or TRAILING a rule is still refused, and
   round 3's negatives are re-asserted rather than trusted. A blank line
   holding a lone CR remains refused under the standing CRLF limitation, now
   re-measured and stated. Oracle regressions on both profiles in
   `test/policy_syntax.test.mjs` and
   `tests/work/test_w2845_docker_inspection_policy.py`, plus deployed-artifact
   coverage in `tests/work/test_deploy_v11.py`. 283 Node (one unrelated W4303
   failure, see `PROGRESS.md`), 2853 + 52 pytest, 55 ACP, 161 v12.
   Evidence: `evidence/correction-round6-2026-08-22.txt`.
12. [changes requested 2026-08-22] Seventh independent review [P2]: the
   round-6 blank-line correction is sound, but a TAB-indented comment is
   refused before `readPolicy` reaches its comment branch even though the
   installed evaluator loads it. This contradicts the pinned support for
   indented comments and makes startup reject a valid exact policy. Review:
   `review-2026-08-22T15-47-35Z.md`; evidence:
   `evidence/seventh-review-tab-indented-comments-2026-08-22.txt`.
13. [done 2026-08-22] Correct round-7 review [P2]: `readPolicy` handled
   `OTHER_WHITESPACE` before `#`, so a SPACE/TAB-indented comment was consumed
   as unaccounted although the evaluator loads the exact policy and authorizes
   the ruled inspections — contradicting the round-3 boundary that a comment
   is accounted for wherever it sits. `commentLineEnd` now accounts for
   indentation before a comment, scanned from the LINE start so a tab sharing
   a line with a rule is still refused, and rounds 3 and 6 keep their negative
   sets re-asserted on both profiles. Oracle regressions in
   `test/policy_syntax.test.mjs` and
   `tests/work/test_w2845_docker_inspection_policy.py`, plus deployed-artifact
   coverage in `tests/work/test_deploy_v11.py`. 286 Node (one unrelated W4303
   failure), 2883 + 52 pytest, 55 ACP, 186 v12.
   Evidence: `evidence/correction-round7-2026-08-22.txt`.
14. [changes requested 2026-08-22] Eighth independent re-review [P2]: the
   round-7 indentation correction is sound, but a comment inside a supported
   multi-line `prefix_rule(...)` remains unaccounted although the installed
   evaluator loads the exact rule. Account for evaluator-valid in-construct
   comments without treating comment punctuation as syntax or `#` inside a
   string as a comment. Add pure-audit, evaluator-oracle, and deployed-
   artifact regressions for both shared profiles. Review:
   `review-2026-08-22T16-46-17Z.md`; evidence:
   `evidence/eighth-review-comment-inside-rule-2026-08-22.txt`.
15. [done 2026-08-22] Correct round-8 review [P2]: a comment INSIDE a
   multi-line `prefix_rule(...)` was retained by `matchingParen` and handed to
   the operand reader, so an exact rule the evaluator loads and honours became
   unaccounted and its prefix was reported missing. Comment spans are now
   MASKED to spaces before any structural scan — not parsed — so comment
   punctuation can never become syntax; a `#` inside a string stays data and a
   TAB before the `#` stays a tab in code, both measured against the
   evaluator. Rounds 3, 6 and 7 keep their negative sets, re-asserted inside
   the new cases. 293 Node, 2905 + 52 pytest, 55 ACP; the seven other failures
   belong to W4996 and W2929 and were not touched from here.
   Evidence: `evidence/correction-round8-2026-08-22.txt`.
16. [changes requested 2026-08-22] Ninth independent re-review [P2]: the
   round-8 in-rule comment correction is sound for BMP text, but
   `maskComments` builds a code-point array and writes it with UTF-16 code-unit
   offsets. An astral character in a valid comment therefore shifts the mask
   and makes a later valid rule unaccounted although the evaluator loads it.
   Review: `review-2026-08-22T17-42-34Z.md`; evidence:
   `evidence/ninth-review-astral-comment-mask-2026-08-22.txt`.
17. [done 2026-08-22] Round-9 correction: the comment mask is built with
   `text.split("")` so it lives in the same UTF-16 code-unit index space as
   every scanner that indexes the source, and `maskComments` throws unless the
   mask is exactly the source's length. Measured against the installed
   evaluator on five astral fixtures — top-level comment, in-rule comment,
   trailing comment on an operand line, several at both levels, and astral
   inside a string operand — each carrying a LATER rule so drift is
   observable. Covered on both shared profiles and in the deployed-artifact
   lane. 297 Node, 2916 + 52 pytest, 55 ACP; the seven other failures belong
   to W4615, W4996 and W2929 and were not touched from here.
   Evidence: `evidence/correction-round9-2026-08-22.txt`.
18. [done 2026-08-22] Tenth independent re-review: round 9 is sound. The
   code-unit mask, exact-length invariant, both shared profiles, installed-
   evaluator fixtures, and deployed artifact agree. 297 Node, 24 focused
   W2845 pytest, and the deployed exact-policy boundary pass. Signed off in
   `review-2026-08-22T18-25-27Z.md`; no reviewer finding remains.
19. [changes requested 2026-08-22] Operator acceptance: the compatible
   current-tree matrix passed every pre-Docker case and all four ruled Docker
   positives, but its four unruled negatives observed neither mutation nor
   the denied approval request the harness uses as proof. Correct the live
   negative oracle so it proves each requested command was attempted and
   refused by the intended boundary, then re-run the complete matrix. Do not
   install or restart on absence-of-mutation evidence alone. Evidence:
   `evidence/live-matrix-2026-08-22.txt`.
   NOTE for installation: the preflight now REQUIRES the inspection rules, so a
   policy file generated before this change makes the dispatcher refuse to
   start until it is regenerated. The refusal names the four missing prefixes.
   The documented procedure in `conf/codex-event-bridge.template.json` now
   appends the inspection profile into the same staged file.
20. [changes requested 2026-08-22; operator-oracle review] Correct the shared
   matrix observation boundary in
   `review-2026-08-22T20-31-27Z.md`. After each completed turn, read the exact
   turn with `includeTurns=true` and require one exact agent
   `commandExecution` item. Positives require `completed`, exit code 0 and no
   approval; negatives require direct `declined` or a correlated denied
   approval plus a non-completed terminal item. Absence, a wrong/additional
   command, or a bare execution failure is not policy evidence. Retain the
   runtime non-mutation check, add synthetic oracle regressions, and rerun the
   complete credential-bearing matrix. Do not install or restart before it
   passes. Evidence: `evidence/operator-oracle-review-2026-08-22.txt`.
18. [signed off 2026-08-22] Independent re-review accepted the round-nine
   index-space correction and the policy generator, auditor and parser.
   Review: `review-2026-08-22T18-25-27Z.md`.
19. [changes requested 2026-08-22; operator-acceptance oracle] The LIVE MATRIX
   does not observe command execution: `runCase` returned only server-request
   METHOD names, so a Docker positive passed on an empty list and a negative
   failed on the same empty list. The operator run produced exactly that.
   Review: `review-2026-08-22T20-31-27Z.md`; reviewer evidence:
   `evidence/operator-oracle-review-2026-08-22.txt`.
20. [done 2026-08-22] Corrected. `src/command_oracle.mjs` is a PURE verdict
   over one turn: exactly one agent `commandExecution` item matching the
   requested command, `completed` with exit 0 and no correlated approval for a
   ruled inspection; `declined`, or a correlated approval denied and a
   terminal non-completed item, for an unruled one. A bare `failed` is NOT a
   refusal, and approvals are correlated by threadId/turnId/itemId rather than
   counted. `runCase` reads the exact turn back through `thread/read` with
   `includeTurns` after completion. Field names, enums and the `source`
   default were read out of the INSTALLED schema, which caught a defect of my
   own: `source` defaults to `agent` and is not required, so requiring it
   would have reported a perfect inspection as unattempted. 14 synthetic-turn
   cases; five mutations, each independent. 311 Node (297 before).
   Evidence: `evidence/correction-oracle-2026-08-22.txt`.
21. [operator gate, outside implementation] Rerun the complete
   credential-bearing matrix against the compatible candidate. Installation
   and the managed-stack restart stay blocked until it passes. Not an
   implementer act: it needs live provider credentials and a running
   app-server.
22. [changes requested 2026-08-22; matrix-oracle correction re-review]
   Require the exact installed-schema method
   `item/commandExecution/requestApproval`, rather than treating any request
   sharing thread/turn/item ids as command-policy evidence. Record and require
   the successful `respondError` denial for an unruled approval-path verdict;
   observing a request whose response could not be sent is not a denial.
   Correct the synthetic method spelling and retain both additive cases.
   Review: `review-2026-08-22T21-02-03Z.md`; evidence:
   `evidence/review-command-approval-correlation-2026-08-22.txt`.
   The operator gate in item 21 remains blocked behind this correction.
22. [changes requested 2026-08-22] Matrix-oracle re-review: correlation
   stopped one boundary short. Identity matched but the METHOD did not, and
   the installed schema gives file-change and permission approvals the same
   thread/turn/item triple; and `respondError`'s own result was discarded, so
   an observed request the client never answered was described as denied.
   Review: `review-2026-08-22T21-02-03Z.md`; reviewer evidence:
   `evidence/review-command-approval-correlation-2026-08-22.txt`.
23. [done 2026-08-22] Corrected. `approvalsFor` matches
   `item/commandExecution/requestApproval` AND the identity triple;
   `runCase` records `denied` from `respondError`; the unruled approval path
   requires a SENT denial plus the terminal non-completed item; a ruled
   inspection still fails on the mere request, answered or not; a direct
   `declined` still needs no approval and a bare `failed` is still
   insufficient. The synthetic fixtures build their method from the exported
   constant, so the wrong spelling cannot recur. 19 oracle cases (16 before),
   four mutations, 316 Node.
   Evidence: `evidence/correction-oracle-round2-2026-08-22.txt`.
24. [operator gate, outside implementation] After independent re-review of
   this boundary: rerun the complete credential-bearing matrix against the
   compatible candidate, then install and restart the managed stack. Not an
   implementer act.
25. [signed off 2026-08-22; matrix-oracle second-correction re-review] The
   exact command-approval method and identity triple now correlate the one
   relevant request, and the approval path requires `respondError` to have
   successfully sent a denial. Other request methods, unsent answers, direct
   decline, bare failure and ruled-positive requests remain distinguished.
   Bridge suite 316/316; matrix syntax and whitespace checks clean. Review:
   `review-2026-08-22T21-12-54Z.md`; evidence:
   `evidence/review-command-approval-correlation-round2-2026-08-22.txt`.
   Proceed to the operator gate in item 24. Do not install or restart unless
   the complete credential-bearing matrix passes.
26. [changes requested 2026-08-23; operator gate] The corrected live matrix
   passed every Baton case but observed no agent `commandExecution` item for
   any of the eight Docker cases. Correct the live driver so each exact
   requested Docker command is attempted and observable by the existing
   conservative oracle; retain the passing authority, negative-mutation and
   cleanup boundaries. Evidence:
   `evidence/live-matrix-final-2026-08-23.txt`. Independently review the
   correction, then rerun the complete credential-bearing operator gate. Do
   not install or restart from this failed result.
27. [proposed 2026-08-23; awaiting `baton.ops` acceptance] Keep the strict
   turn-item oracle and exact commands. Run the Docker cases first in a
   dedicated fresh app-server phase; require the model to submit exactly one
   literal shell command and wait for its terminal result instead of answering
   from knowledge or pre-judging policy; on a missing attempt, retain bounded
   turn status, item-type and agent-message diagnostics. State explicitly for
   the safe absent-target negatives that the command must be submitted and
   the execution boundary is expected to refuse it. Add focused prompt and
   missing-attempt diagnostic regressions. Do not replace managed-turn proof
   with direct `command/exec`, and do not weaken the existing oracle. Preserve
   all Baton authority, negative-mutation and cleanup cases, independently
   review the correction, then rerun the complete 21/21 operator gate before
   installation or restart. Review:
   `review-2026-08-23T04-13-22Z.md`; evidence:
   `evidence/reviewer-driver-correction-2026-08-23.txt`.
28. [done 2026-08-23; item 27 partly REFUTED BY MEASUREMENT] Item 27's
   items 1 and 2 rest on a diagnosis — that the model is not invoking the
   shell tool — and that diagnosis is wrong. A decisive probe asked a managed
   turn for `date +%s%N`, a value it cannot know without executing: the agent
   returned a nanosecond timestamp INSIDE the run window, and `thread/read`
   with `includeTurns` returned NO `commandExecution` item for that turn. An
   independent `/bin/echo` probe agrees. `CommandExecutionThreadItem` IS in
   the installed schema's `ThreadItem` union, so this is the RUNNING SERVER
   (codex-cli 0.149.0) not recording it. A stricter prompt and a dedicated
   Docker phase would change behaviour that is already correct, and the eight
   cases would fail identically. Items 1 and 2 are therefore NOT implemented
   and no oracle relaxation is proposed — the review is right that none is
   acceptable. Item 3 IS implemented, because a bounded diagnostic is right
   whatever the cause and is what made the cause findable:
   `missingAttemptDiagnostic` renders the turn id and status, the ordered item
   types, bounded agent-message text with its true length, and any agent
   commands; `reasoning` payloads contribute their type only, and it decides
   nothing. The matrix prints it for a failed Docker verdict. Item 4's
   diagnostic regressions are added (4 cases); item 5's boundaries — the exact
   commands, the Baton cases, the non-mutation probe and cleanup — are
   untouched, as is the oracle. 328 bridge, 2977+52 pytest, 55 acp, 492 v12,
   syntax and whitespace clean. THE LIVE MATRIX IS NOT RERUN: on the measured
   evidence it fails the same eight cases for the same reason.
   Evidence: `evidence/measured-cause-2026-08-23.txt`.
29. [changes requested 2026-08-23; diagnostic review] The decisive timestamp
   probe is accepted and SUPERSEDES item 27's inference that the model did not
   invoke the shell; the strict oracle and blocked 21/21 gate remain correct.
   Bound `missingAttemptDiagnostic` in total, not only per agent message.
   Cap the reported item types, messages and commands; truncate every command
   string; expose true totals/truncation markers; and add regressions for many
   messages, many commands and one long command. A 1,000-command synthetic
   turn currently creates a 1,029,041-character summary. Keep reasoning
   payloads excluded and keep diagnostics out of verdicts. After correction,
   independently re-review, then return the deployment incompatibility to
   `baton.ops` for a compatible build/managed-turn transport/wait decision.
   Review: `review-2026-08-23T04-49-11Z.md`; evidence:
   `evidence/review-bounded-diagnostic-2026-08-23.txt`.
29. [changes requested 2026-08-23] The measured diagnosis is ACCEPTED and
   supersedes item 27's premise; the strict oracle stands. One P2: the new
   bounded diagnostic had no TOTAL bound — 1000 commands of 1000 characters
   produced a 1,029,041-character summary.
   Review: `review-2026-08-23T04-49-11Z.md`.
29. [done 2026-08-23] Closed. A CAP ON THE PARTS IS NOT A BOUND ON THE WHOLE,
   and the input that triggers this diagnostic is the input that broke it: it
   exists for the moment a model goes off-script, which is the moment a turn
   has a thousand items. Hard caps on COUNTS as well as sizes — 40 item types,
   5 messages, 10 commands, 400 chars per message, 200 per command — kept
   PRIVATE, with a caller-supplied `limit` able only to tighten, because an
   exported helper its caller can make unbounded is unbounded. True totals are
   always reported and every cut list carries an explicit omission marker,
   because the COUNT is often the finding — eight cases with zero command
   items is the whole of this Work's current state. The reviewer's own
   reproduction is now a case: 1,029,041 -> 3,095 characters with both totals
   intact. Six mutations, all six witnessed; H4 keeps every constant and only
   unclamps `limit`, and fails. Unchanged: the strict oracle, the eight exact
   commands, the Baton cases, the non-mutation probe and cleanup. 333 bridge,
   2977+52 pytest, 55 acp, 492 v12, syntax and whitespace clean. The live
   matrix still cannot pass on this build — W7989.
   Evidence: `evidence/correction-bounded-diagnostic-2026-08-23.txt`.
30. [changes requested 2026-08-23; diagnostic re-review round 2] The ordinary
   high-cardinality case is corrected, but `limit: NaN` disables clipping and
   externally supplied item type/id/status strings remain length-unbounded.
   Normalize invalid limits, hard-bound every retained external string or the
   whole serialized result, and add `NaN` plus oversized-metadata regressions.
   Preserve true totals, omission markers, reasoning exclusion, and the
   diagnostic-only boundary. The strict oracle is accepted and unchanged.
   Review: `review-2026-08-23T05-04-02Z.md`; evidence:
   `evidence/review-bounded-diagnostic-round2-2026-08-23.txt`.
30. [changes requested 2026-08-23] The count caps and omission markers are
   accepted. One P2: `Math.min(NaN, hardMaximum)` is NaN and
   `length > NaN` is false, so `limit: NaN` REMOVED the cap; and item-type
   strings, the turn id, the turn status and each command status were retained
   uncapped, so one oversized value produced a million-character summary.
   Review: `review-2026-08-23T05-04-02Z.md`.
30. [done 2026-08-23] Closed. `tighten` normalizes the optional limit before
   use — a non-number, a non-finite or anything below one falls back to the
   private hard maximum — because A CLAMP A NON-NUMBER WALKS THROUGH IS NOT A
   CLAMP, and this one failed OFF, the direction that never announces itself.
   Every externally supplied string retained in the result or the summary is
   capped: types, ids, statuses, messages, commands. A HARD PROPERTY THAT
   DEPENDS ON THE PROTOCOL BEING OBEYED IS THE PROTOCOL'S, in a diagnostic
   whose whole purpose is the turn that did something unexpected. Three
   regressions: eleven invalid limit values; oversized metadata across id,
   status, type and command status; and every dimension at once with the
   COMPLETE serialized diagnostic asserted under 20,000 characters while the
   true counts survive. Five mutations, four witnessed; the summary backstop
   is INERT with every field capped and is recorded as such rather than
   counted. 336 bridge, 2977+52 pytest, 55 acp, 492 v12, syntax and whitespace
   clean; no Docker command executed. The live matrix still cannot pass on
   this build — W7989.
   Evidence: `evidence/correction-bounded-diagnostic-round2-2026-08-23.txt`.
31. [signed off 2026-08-23; blocked on W7989] The round-2 diagnostic
   correction is sound. Invalid limits cannot remove private caps, every
   retained external string is bounded, and an all-dimensions regression
   asserts a fixed maximum for the complete serialized result while retaining
   true totals. Full bridge suite: 336/336. No reviewer finding remains in the
   diagnostic or strict oracle. The live 21-case operator gate cannot proceed
   until W7989 resolves the current managed provider's missing structured
   command-item evidence. Review: `review-2026-08-23T05-13-32Z.md`.
32. [cancelled by operator 2026-08-23] W7989 established that the current
   managed custom-tool deployment cannot expose the strict structured live
   evidence. Keep the exact policy, oracle, bounded diagnostics, and
   deterministic regressions, but do not claim the 21-case live gate passed
   and do not redesign v11 around observability. V12 owns the replacement
   boundary.
