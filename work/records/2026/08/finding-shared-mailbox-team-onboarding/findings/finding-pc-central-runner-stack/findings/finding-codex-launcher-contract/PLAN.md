# Plan — supply the Baton contract to Codex contexts

1. [done 2026-08-25] Revalidate the Codex thread bootstrap and dispatcher
   target boundary. `bootstrapThread` and `resolveTargetInstructions` hold the
   exact four values but pass only accepted role prose as
   `developerInstructions`; the generated app-server start/resume contract has
   no per-thread environment field.
2. [done 2026-08-25] Added one pure Codex-only launcher-contract renderer from the
   configured absolute binary/config and validated participant/role. Compose
   it with accepted role prose in both fresh `thread/start` and every
   dispatcher `thread/resume`. Require `--role` directly in the bootstrap
   operand gate. Do not change the shared instruction projection, ACP env,
   `BOOTSTRAP_PROMPT`, `CodexClient`, command policy, or authority protocol.
3. [done 2026-08-25] Added the focused matrix recorded in `FINDING.md`: exact presence,
   missing fields, participant/role mismatch, two-target non-crossing,
   restart recomposition, no ambient-env/filesystem inference, four-field-only
   redaction, ACP compatibility, and existing uniqueness guards.
4. [done 2026-08-25] Updated the Codex bridge and connectivity documentation to
   distinguish Codex developer-instruction labels from ACP agent environment,
   then run the focused files, full Codex event-bridge suite, applicable v11
   gate, and `git diff --check`.
5. [done 2026-08-26] Obtained independent review of the implementation and its
   compatibility with one context and one readiness path per participant.
6. [pending; operator] Drain and deploy only after review, restart with fresh
   contexts, complete W12181 through
   `pc.rsrch -> pc.impl -> pc.rsrch -> pc.ops`, and return W10198 for final
   acceptance. An existing thread is not the required smoke.

7. [pending 2026-08-26 review] Reject relative `--baton` and
   `--baton-config` bootstrap operands before the instruction read or Codex
   connection, make the additive bootstrap regression pass, rerun focused and
   full gates, and return for independent review before item 6.

**Status 2026-08-25 (reviewer):** research and the implementation-ready
boundary are complete. Items 2–4 are ready for serial implementation; W11910
currently overlaps the Codex README and should finish first rather than being
mixed into this Work.


**Status 2026-08-25 (implementer).** Items 2-4 are complete. The renderer is
`launcherContract`/`codexDeveloperInstructions` in `role_instructions.mjs`,
composed by `resolveTargetInstructions` and `bootstrapThread` and by nothing
else; `--role` is a required `--start-thread` operand. Focused counts moved
12 -> 18 and 8 -> 13; ACP is 64/64 and the full Codex suite is 395 with two
failures that belong to W11910 and were MEASURED to reproduce with every
W12229 change reverted to HEAD. Two existing assertions were replaced because
they required role prose and nothing else, which is the defect itself; neither
was weakened. See `PROGRESS.md` and
`evidence/gate-2026-08-25.txt`. Item 6 remains the operator's: a live smoke on
an existing thread does not satisfy the fresh-context acceptance.


## Review correction — 2026-08-26

`review-2026-08-26T01-31-59Z.md`'s one [P1] is corrected.

7. [done 2026-08-26] **`bootstrapThread` refuses a relative `--baton` or
   `--baton-config`** in the same operand gate that refuses a missing one,
   before the instruction read and before any client factory. The dispatcher
   validation and the four-field renderer are unchanged, as the review
   required.
8. [done 2026-08-26] **The ACP door refuses the same shape.** `baton.binary`
   and `baton.config` are this family's half of the same contract and were
   checked for non-emptiness only. Beyond the review's literal ask and flagged
   for its ruling.
9. [done 2026-08-26] Focused `bootstrap_thread` 19 -> 22 and ACP 66 -> 67;
   both guards measured to fail without them. Codex 399/399 and ACP 67/67 —
   both Node suites fully green — and the whitespace check clean.
10. [done 2026-08-26] Independent review signed off the correction and ruled
    the ACP absolute-source admission check within this Work. PLAN item 6's deploy
    and the fresh-context W12181 smoke, which remain the operator's.

**Status 2026-08-26 (reviewer):** implementation is signed off; no W12229
finding remains. Item 6 is still pending. Before deploying the shared tree,
the concurrent W11910 claim-slot regression newly present in the full Codex
suite must also be green; see `review-2026-08-26T02-49-05Z.md`.
