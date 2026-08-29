# Plan

1. Revalidate the frozen handshake refusal, session, assignment-ending, exact
   reconciliation, intake, retention, and cleanup contracts.
2. Pin the one trusted composition operation and its effectively-once operands;
   keep `unsupported-version` outside the worker-disposition axis.
3. Implement the bounded manager/session path using existing authority,
   reconciliation, custody, retention, adapter and provider owners.
4. Add positive, negative, restart, retry, identity-mismatch, multiplicity,
   uncertainty and sibling-preservation tests.
5. Run focused daemon-free and required Docker gates, then return for
   independent review before parent W32382 can close.

## 2026-08-28 — first independent review

- [accepted partial] A bounded helper preserves the typed
  `refused/unsupported-version` pair, leaves worker disposition untouched, and
  delegates authority-first cancellation ordering to its existing owner.
- [required, P1] Put the composition on the production/public session path and
  bind the exact persisted agent-session reference, its attempt assignment,
  and its pinned certified profile. A caller-created refusal and free profile
  digest/version are not session evidence.
- [required, P1] Use one fixed refusal act per exact session whose signature
  contains every operand, so changed profile/version/refusal operands collide
  rather than journal a second incompatible fact.
- [required, P1] Drive the refusal through exact removal, positive absence,
  credential/launch teardown, cleanup settlement, and the reuse boundary.
  `cancel-requested` plus a stop order is not that ending.
- [required] Add the pinned mismatch, uncertainty, multiplicity,
  sibling-preservation, restart/retry, and non-skipping real Docker evidence.

## 2026-08-28 — second independent review

- [no completion delta] The implementer removed the duplicate import and
  explicitly confirmed that all four P1 findings above remain open. No
  production/session, identity, cleanup, or engine/race correction was offered
  for review.
- [required] Complete the coupled P1 round above before returning W32576 for
  another independent review. The private test-only helper is accepted only as
  partial scaffolding and does not satisfy this Work.

## 2026-08-28 — correction re-review

- [accepted partial] Persisted session/profile provenance replaces the
  caller-built refusal, and one fixed session operation now collides on a
  changed answered version.
- [required, P1] Prove the session is currently in the ruled handshake phase
  and owns the applicable execution posture; historical/terminal rows cannot
  authorize a fresh ending.
- [required, P1] Derive refusal and pinned profile/version evidence from one
  certified-profile snapshot under the operation concurrency boundary.
- [still required] Complete exact removal, positive absence, provider
  settlement, reuse ordering, public production composition, and the full
  daemon-free plus non-skipping Docker race matrix.

## 2026-08-28 — second correction re-review

- [accepted partial] Post-handshake states are refused and refusal/signature
  members now use one pre-read profile snapshot.
- [required, P0] Remove the caller-supplied profile bypass from exported
  `negotiate_acp`; use a private already-owned-profile helper instead.
- [required, P1] Re-prove that the exact epoch owns the occupied execution
  posture slot in the refusal transaction; handshake-looking state alone is
  insufficient.
- [required, P1] Replay a committed refusal before mutable session/profile
  preconditions. Add exact retry after state advance, slot release, profile
  withdrawal, and process/store restart.
- [still required] The complete cleanup, public production caller, and engine
  race matrix remain the Work's unsatisfied centre.

## 2026-08-28 — public-boundary correction re-review

- [accepted] The P0 caller-supplied profile bypass is removed and covered by a
  black-box public-door negative.
- [unchanged, required] Exact occupied-slot proof and replay before mutable
  session/profile checks remain open.
- [unchanged, required] Complete the cleanup/provider/reuse composition and
  full engine/restart/race evidence before another review return.

## 2026-08-28 — slot and replay correction re-review

- [accepted] Exact occupied-slot ownership is proved transactionally.
- [accepted] Committed refusal replay precedes mutable preconditions and
  survives world movement plus store restart; changed call operands collide.
- [remaining, required] Complete plan items 3–5: public production cleanup,
  exact removal/absence/providers/reuse, and the full Docker/race matrix.

## 2026-08-29 — the ending, and plan items 3–5

- [done, item 3] `authorize_refused_session_cleanup` composes the ending from
  the existing owners: `_not_an_ending`, `_provider_ending`, the shared
  `_removed` core in the adapter, and `lanes._release_lane`. It takes the
  session reference because the record is filed under the session act, and it
  reads the attempt from the proved row.
- [done, item 3] The third sibling surface M34998/M34999's rule requires: a
  `session.unsupported-version` record contract, a
  `destroy.refused-session-command` contract, `destroy_refused_session` over
  the shared removal core, and `refused_session_destroy_operation`.
- [done, item 3] `settle_unsupported_version` records the runtime it is about
  and is now exported; the private helper's identity derivation is named so
  the ending can find the row it authorizes on.
- [done, item 4] Positive, negative, restart, retry, identity-mismatch,
  uncertainty, provider-retry and reuse-ordering cases:
  `tests/manager/test_refused_session_cleanup.py`. Eleven mutations, eleven
  named failing cases.
- [done, item 5] The non-skipping real-Docker acceptance:
  `tests/manager/test_refused_session_engine.py`, registered serial. A real
  container, a genuinely derived refusal after it exists, real removal, real
  absence, roots torn down, sibling container untouched, restart, and the
  freeze door proved still shut.
- [raised, not done] `_settle_recordless_cleanup` duplicates
  `_settle_failed_start_cleanup` with the lane reason as an operand. The two
  should be one function; merging them would edit W32648's code while it is
  out for independent review. One-line change once it closes.

## 2026-08-29 — independent ending review

- [required, P1] Validate the committed refusal body's own semantic evidence
  before its digest authorizes destruction: exact decision/category/code,
  pinned-versus-answered version relation, and agreement with the persisted
  session profile. A shape-correct body saying `decision: accepted` currently
  reaches the custodian and settles.
- [required regression] Make
  `test_a_record_that_no_longer_says_unsupported_version_authorizes_nothing`
  refuse as `integrity/schema` with no custodian command, then add the sibling
  mutations for category/code and version/profile disagreement.
- [required, P2] Merge the two recordless settlement bodies now. W32648 closed
  satisfying before this implementation round began, so its review is no
  longer a valid reason for two owners of the same ordering.
- [accepted] Preserve the submitted session provenance, exact runtime command,
  fencing, observation/provider settlement, retained-output, replay, lane and
  real-Docker evidence while making those corrections.

## 2026-08-29 — the record's meaning, and one settlement owner

19. [done] `_refused_session_record` requires the closed verdict — `decision`,
    `category` and `code` together — before the authorization digest is
    computed, and requires the recorded wire versions to be integers that
    still disagree.
20. [done] The retained `profile_digest` is compared against the PERSISTED
    session row rather than a certification lookup, so an exact retry still
    replays after the profile is withdrawn. A case drives exactly that.
21. [done] `_settle_recordless_cleanup` is the single owner of both recordless
    endings; `_settle_failed_start_cleanup` is gone and the failed-start
    ending calls the shared one with its own lane reason.
22. [done] Fifteen mutations, fifteen named failing cases.

## 2026-08-29 — independent final disposition

23. [accepted] The closed verdict, typed unequal versions and persisted-session
    profile agreement are proved before authorization is reduced to a digest.
24. [accepted] Failed-start and refused-session cleanup share the one
    recordless settlement owner; both sibling paths remain green.
25. [done] W32576 satisfies the daemon-free, retained Docker and ordering
    acceptance and can close, unblocking parent W32382.
