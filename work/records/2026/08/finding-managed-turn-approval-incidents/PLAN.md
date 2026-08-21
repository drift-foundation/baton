# Plan

**Status — 2026-08-21:** items 1–6 are independently signed off and deployed.
Items 7–8, the W99 cross-Work continuation fence and its review, are complete
and signed off in `review-2026-08-21T21-33-55Z.md`. The approver rejected arbitrary per-thread config overrides and
confirmed the deployment-owned exact command-policy route. The mediated-MCP
recommendation in `review-2026-08-20T23-42-34Z.md` is superseded.

1. [done] Revalidate the repeated approval episodes against the current
   managed-turn command construction, Codex policy matching, dispatcher
   recovery, runtime publisher, and Inbox projection.
2. [done] Provision a deployment-owned exact allow rule for the
   installed Baton executable, accepted config, participant, and exactly the
   approved verbs; prove it against the effective app-server policy with the
   broad rule removed. Refuse same-participant rules for unapproved verbs;
   read-only commands need no sandbox-crossing exception. Keep the
   writable-authority-root proposal and arbitrary turn overrides removed.
3. [done] Define and persist the action-owner incident, including safe
   correlation, coalescing, explicit dismissal, and append-only audit history.
4. [done] Surface open incidents through `[Inbox*]` without conflating them
   with current runner state or offering an approval action.
5. [done] Complete the exact-policy live positive/negative matrix,
   remove the stale writable-root vocabulary from its smoke, retain the
   restart, deduplication, dismissal, and redaction regressions, and run the
   focused bridge/authority/TUI suites and complete applicable gate.
6. [done] Independently review before deployment.
7. [done 2026-08-21] Fence semantic continuation
   across managed Work turns after denial/interruption. Quarantine the context
   until a full managed-stack restart and apply the scoped supersession in
   `finding-readiness-target-wedged-turn`. Reproduce approval-blocked Work A
   followed by Work B; prove that no Work-A operation executes in Work B and
   that incident correlation remains truthful. Keep Docker, broad shell,
   destructive-command auto-approval, and v12 automatic context replacement
   out of scope.

   Delivered as W99: sticky `tainted` context state beside the live `blocked`
   turn state, `#drain` fenced on it, an immutable delivery attempt selected
   by the approval request's own turn id, terminal `failed` publication
   instead of `idle`, a `tainted` status row naming the full managed-stack
   stop/start remedy, and `test/cross_work_fence.test.mjs`. The superseded
   drain assertion in the W3243 suite is rewritten and names its supersession.
   Detail in `PROGRESS.md`, round 8.

   Independent review found that `tainted` is process-local, so restarting
   only the dispatcher against the same rendered thread clears the fence and
   delivers the reoffered Work. It also found that a named approval request
   arriving during `turn/start` is attributed to the pending Work even when
   its turn id disagrees. Both findings were reproduced and corrected in round
   9: the quarantine is persisted per managed context in
   `src/quarantine_store.mjs` and restored before anything opens, and an
   unproven named turn defers only its Work attribution — bounded by the
   delivery attempt — while the fence, denial and interrupt stay immediate.
   The reviewer's two regressions are green and mutation-checked; four more
   cover the new mechanism's edges. Two fixture-only changes to reviewer tests
   are flagged for checking in `PROGRESS.md` round 9.

   Round-2 review confirmed those two corrections and fixture changes, then
   found two restart edges: an existing malformed/unreadable marker is treated
   as absent and makes its context deliverable, and a process restart can lose
   the durable incident while its Work attribution is pending. Two additive
   regressions are red pending correction; see
   `review-2026-08-21T16-38-15Z.md`.

   Round 10 corrected both. `load` now answers `absent`/`present`/`damaged`
   with only `ENOENT` clean; damaged bytes are copied aside and the context
   loads unknown-but-tainted rather than refusing startup, so one corrupt file
   never takes down a healthy target. The marker carries a durable
   `incidentFiled` acknowledgement written only after the report lands, so a
   restore recovers an unpublished incident exactly once and never re-files an
   acknowledged one. Both reviewer regressions are green and mutation-checked.
   The reviewer withdrew the pruning question as non-blocking; unpruned markers
   are the accepted limit.

   Round-4 review confirmed those corrections and found that recovery filed
   every restored incident uncorrelated, discarding a Work origin an `exact`
   marker had already proven. Round 11 corrected it: `#provenAction`
   reconstructs the closed action locator from the marker only when the
   correlation is `exact` and its work, episode and action key are all
   well-formed, and every other restored correlation — `pending`, `unmatched`,
   `unknown`, or a malformed locator — still files uncorrelated.

   Round-5 review found three remaining edges; round 12 corrected all three.
   Reconstruction now also requires the record to be internally consistent —
   an `exact` marker without the turn id whose match made it exact proves
   nothing — and its locator text to be in the same trimmed, non-blank form
   the live normalizer stores, so blank or padded values file uncorrelated
   instead of injecting a locator this dispatcher never derived. A marker
   instant counts as present only when the formatter used during restore
   accepts it, so a finite out-of-range value is damaged like any other
   corruption and stays isolated to its own context instead of aborting
   startup for healthy targets. The hash separator in `quarantine_store.mjs`
   is now an escape rather than a literal NUL, so the source is text to Git
   again with identical runtime bytes. Five regressions cover it — the
   reviewer's three plus padded-locator refusal and repair-on-restart — each
   mutation-checked; `npm test` is 199 green.

8. [done 2026-08-21; signed off in round 7] Independently review the W99 fence before the next managed-stack
   deployment. Round 7 owns the identity boundary round 6 settled in one
   direction: whether one shared predicate at binding, selection and recovery
   is the right alignment, or whether the deployment wants an explicit
   stricter turn-id contract enforced at live binding instead. The reviewer owns
   confirming that the quarantine, the correlation selection, and the
   rewritten W3243 drain assertion match the ruling, and that no smoke matrix
   owned by items 2 and 5 regressed.

   Round-4 review confirms the damaged-marker fail-closed correction, durable
   acknowledgement, and truthful publisher stubs, but finds that restart
   recovery unconditionally discards a correlation already proven and stored
   as `exact`. A new additive regression is red: a failed first publication
   restores the exact W30 marker, then recovery files the incident without its
   Work, episode, or action key. Preserve the stored locator only when the
   marker is `exact`; `pending`, `unmatched`, damaged, and unknown markers
   remain uncorrelated. See `review-2026-08-21T16-53-35Z.md`.

   Round-5 review confirms the positive exact-marker recovery and the earlier
   quarantine/correlation corrections, then finds three remaining edges. A
   malformed `exact` marker can still inject correlation without the proving
   turn id or with whitespace-only locator text; a finite timestamp outside
   JavaScript's `Date` range aborts dispatcher startup instead of isolating the
   damaged marker to its target; and the literal NUL separator makes the new
   JavaScript source binary to Git. Three additive regressions are red for the
   two P1 boundaries. See `review-2026-08-21T20-52-08Z.md`.

   Round-5 review's three findings are corrected in round 12 and its three
   regressions are green. Still open for the reviewer or approver, and
   deliberately not fixed by the implementer: the Markdown whitespace
   findings `baton.prompt` raised against three append-only review journals.
   They are the reviewer's own two-space hard breaks in an append-only file
   that policy says is never edited; the disposition and recommendation are
   in `PROGRESS.md` round 12.

   Round-6 review confirms those three corrections and the stricter
   Work/action-key text boundary, but finds that the same trimming predicate
   was also applied to the separate opaque turn id. The live bridge and the
   generated app-server schema accept and preserve a string turn id verbatim,
   so a live-created `exact` marker can become uncorrelated on restart solely
   because its turn id contains surrounding whitespace. One additive
   regression is red; align the live and recovery contracts before sign-off.
   See `review-2026-08-21T21-20-06Z.md`.

   Round-6 review confirmed the three round-5 corrections and found one P1:
   recovery applied the action-locator trimming contract to the separate
   opaque turn id, so a marker the live path had itself proven could be
   refused on restart. Round 13 corrected it with a single shared
   `#liveTurnId` predicate used by `#bindAttempt`, `#approvalOrigin` and
   `#provenAction`, so the binding, selection and recovery boundaries cannot
   drift apart. An `exact` marker still requires a present turn id, and
   `work`/`actionKey` still require the trimmed non-blank form. The
   implementer's own round-12 `padded turn id` assertion encoded the
   overturned rule and was removed; its companion case is narrowed to the
   empty string, the only turn id the live binding refuses. A round-12 README
   documentation claim that turned out to be false is corrected in the same
   round; see `PROGRESS.md`, round 13.

   Round-7 review confirms the shared opaque turn-id boundary, the corrected
   marker cases, and the documentation. Focused W99 evidence is 28/28 and the
   full bridge suite is 201/201. No further correction is requested; see
   `review-2026-08-21T21-33-55Z.md`.
