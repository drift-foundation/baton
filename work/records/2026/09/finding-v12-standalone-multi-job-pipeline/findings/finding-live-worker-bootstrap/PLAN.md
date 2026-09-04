# Plan

1. [done, reviewer revalidation 2026-09-03] Map the exact public Authority,
   offer/claim, workspace, credential, launch, runtime adapter and observation
   calls already proven by v12. The focused Job-manager baseline is 188 passing
   tests at `4641ce0`. Reuse the operations; do not import or extract the
   dogfood command wholesale.
2. [done 2026-09-03] Add one level-triggered post-claim launch
   capability to the serving operations seam. Invoke it after each sweep
   reacquires bound canonical state, including restart, and never hide launch
   inside `claim()` or call it from read-only status.
3. [done 2026-09-03] Define one closed trusted deployment
   configuration and production `module:factory`. Open the expected Authority,
   resolve participant/principal through its bootstrap face, mint only that
   participant's restricted session, validate all static runtime/input
   identities before admission, and release every factory-owned handle.
4. [done 2026-09-03] Deliver the ephemeral offer bearer once into an
   exact immediate acceptance. After the claim commits, idempotently compose
   attempt record, activation, bootstrap workspace/input, retained manifest,
   lazy credential delivery, launch delivery, OCI adapter and runtime start
   using only public owner operations.
5. [done 2026-09-03] Recover each partial boundary from canonical
   state: replay attempt/activation, structurally adopt the workspace, adopt
   exact launch and credential deliveries, tear down only the proven
   pre-start credential orphan, and reconcile `start-requested` before any
   possible start. Never retry `uncertain` or another settled failure.
6. [done 2026-09-03] Add the narrow public start-failure observation
   required for status to derive `exceptional`, including the case where
   failed-start reconciliation attached a runtime id. Keep the failure in the
   Worker Manager's journal rather than adding shadow Job runtime state.
7. [done 2026-09-03] Add a tiny successful implementation fixture,
   a documented production command, capability/configuration refusals, and
   crash-point restart cases proving no duplicate offer, claim, attempt,
   workspace, credential delivery, launch delivery or runtime. Prove a failed
   stage is exceptional without stopping observation of an independent stage.
8. [done 2026-09-03, superseded earlier path correction] Correct new Job
   Manager episode identity derivation to produce deterministic bounded worker-contract
   `opaqueId` values. Preserve every identity already stored by migration or
   an earlier process; update the bounded Job-manager test expectations that
   asserted the old derivation. Do not encode an invalid identity only at the
   workspace boundary or weaken the frozen worker manifest grammar.
9. [done 2026-09-03, superseded by item 10] The preparation record has
   one pinned meaning — the deployment's post-claim ending, no account of a
   start act, no cleanup authority — written into the schema comment, both
   API docstrings and `DEPLOYMENT.md`, with the obsolete wording superseded in
   the FINDING. Identification now rides the owner's own call BEFORE the
   record, so it is level-triggered, covers every post-start boundary rather
   than the absence branch alone, and never takes the ending with it; the
   guard it replaced the axis check with is the sibling start-failure record.
   Before a start, both the credential and the launch delivery are disposed of
   whether this invocation authored or adopted them; after one, neither is.
   The delivery's cleanup owner stays live across the start request, so a
   bearer equal to the attempt's own identity is released before durable state
   is read again. Regressions: a crash between ending and identification,
   contradictory launch material, a launch adopted after a crash and then
   stranded by a provider refusal, and an end-to-end colliding bearer — each
   driven against the unfixed code first. Boundary-inventory counts remain
   49/35/132 with no W76207 delta. The patch remains outside
   W71917/W71877/W71918/W71878, Git, review, correction, integration and
   dogfood policy.
   Independent correction-pass review found that reconcile-before-record is
   still edge-triggered across process death: reconciliation attaches the
   runtime and projects the stage `running` before the preparation ending is
   written, after which the Job Manager no longer calls the launch capability.
   Make identification plus the ending crash-resumable without exposing an
   intermediate state that removes the obligation, and add the exact
   after-reconcile/before-record crash regression.
10. [done 2026-09-03, superseded by item 11] The ending and the naming are ONE act.
   Asking the engine and committing its answer are separated: `_identify`
   makes every adapter call and answers a plan with no durable effect,
   `_reconciled` owns what that plan means durably, and `reconcile_runtime` is
   those two halves. The failed-preparation ending applies the plan inside the
   transaction that writes `runtime.preparation-failed`, through `_attach`'s
   `within` operand, so a death in the interval leaves neither fact and the
   stage still `claimed`. No adapter call is made under the store's write
   lock. The plan is an operand by identity and by digest — which runtime the
   engine named, never its prose — so a different runtime still collides, the
   same ending still replays, and an adapter-supplied name the registry holds
   live can neither wedge the signature nor be quoted in the account.
   Applying is contained inside the act by its own savepoint; a
   `BaseException` is not. Regressions: a death between the naming and the
   ending at the production seam, the same interval focused at the manager, a
   contained attachment whose ending still stands over the axes as they really
   are, a stable identification that replays, and an identified name the
   secret registry holds live — the first two driven against the pass-5 ordering first, where
   they reproduce the review's probe exactly. Boundary-inventory counts remain
   49/35/132 with no W76207 delta; three delegations and three probe sites
   follow the code to `_identify`. The patch remains outside
   W71917/W71877/W71918/W71878, Git, review, correction, integration and
   dogfood policy.
   Independent review confirms the reported preparation crash interval is
   closed, but found two adjacent P1 races: `_settled_and_recorded` still
   attaches before its start-failure row in separate durable acts, and the
   preparation ending does not revalidate its sibling start-failure row after
   the external identification query. Make the start ending atomic too, make
   the two ending kinds mutually exclusive inside their owner transactions,
   and add the exact crash and interleaving regressions.
11. [done 2026-09-03, superseded by item 12] Both endings are one act, and the sibling
   guard is asked where there is no interval. `_settled_and_recorded` asks
   through the shared `_identification` and commits the plan inside the
   transaction that writes `runtime.start-failed`, through the shared
   `_identified_within`; `_settle_unknown_start` is no longer a third separate
   write and no longer takes an adapter it never used.
   `refuse_runtime_preparation` asks `attempt_start_failure_of` again inside
   its own transaction, so a start ending that wins the race leaves neither
   the preparation row nor its attachment — and the lost race is contained and
   accounted for, so the caller still reads its own refusal. Regressions: a
   death between the naming and the record at the manager and through the Job
   projection with an engine that denies a start it already made, the uncertain
   settlement proved part of the same act and resumable, and an interleaving
   case proving exactly one ending survives. Boundary-inventory counts remain
   49/35/132 with no W76207 delta. Recorded OPEN and not corrected:
   `single_worker._unwound` can remove a live container's mounts because it
   decides from the pre-start axis; two narrower conditions each broke a rule
   already pinned here, and the direction that works needs the OCI adapter's
   own `unresolved` answer to reach the deployment as a value.
   Independent review confirms both requested atomicity fixes and all three
   preserved probes. The recorded OPEN is an in-scope P1: the
   created-then-denied production fixture leaves a live runtime while
   `_unwound` deletes both mounted source roots. Carry the owner's structured
   settlement across the boundary and gate local unwind on it; preserve the
   created runtime's unresolved mounts without regressing pre-adapter or
   colliding-bearer cleanup.
12. [done, independent review 2026-09-03] The unwind defers to the owner that already
   decided. `OciAdapter._undelivered` keeps its structured settlement on the
   adapter instead of only in the refusal prose its caller composes, and
   `single_worker._unwound` reads it: a settlement present means both mounts
   were decided on engine evidence and nothing here ends them; `None` means no
   owner reached that boundary and `fresh` remains the whole rule. Regressions
   prove three sides together — a created-then-denied runtime keeps both
   `unresolved` roots and its registered bearer, a refusal before the
   adapter/start boundary ends both local deliveries, and the colliding-bearer
   path still releases its delivery and stays exceptional and non-retried. The
   first fails against the pass-7 unwind and the other two pass under both.
   Boundary-inventory counts remain 49/35/132 with no W76207 delta. Independent
   correction-pass review confirmed the structured settlement is populated
   only at the owner's engine-backed boundary, the live created runtime keeps
   both roots and its registration, and the pre-boundary and colliding-bearer
   cleanup paths remain intact. No further findings were identified.
13. [pending handoff to `baton.ops`, 2026-09-03] Integrate the reviewed
   bootstrap and submit W71917 through it as the first ordinary self-hosted
   v12 workload. The implementation is signed off by
   `review-2026-09-03T22-32-34Z.md` in the visible working tree, and no
   immutable proposal or candidate digest was produced — so this is not
   integration approval and `baton.merge` has nothing to import. What remains
   belongs to the approver: own the remaining diff as Git state, and decide
   W71917, the blocked Work this seam exists to carry, which is itself routed
   to `baton.ops`.
