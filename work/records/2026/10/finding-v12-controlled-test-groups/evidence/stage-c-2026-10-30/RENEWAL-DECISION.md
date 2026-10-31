# Decision packet: a rewritten RENEWED `expires_at` still decides expiry (W275775 / TOK-9)

Prepared by K (copilot under owner claim E384905) for Slawomir, as review
2026-10-31T03:05:05Z asked. Nothing below is implemented; the regression that
any selected correction must keep is
`StageCProtections.test_an_honest_renewal_moves_the_deadline_once_and_a_lost_reply_replays_it`.

## The gap, exactly

`tokens.renew` signs the REQUEST -- `{version, domain, generation, revision, operation,
execution, owner, seconds}` -- and records as the result that request plus the two
instants this manager ANSWERED: `renewed_at` (the clock) and `expires_at`
(`boundaries.deadline(renewed_at, seconds)`). `ControlStore.replay` binds the
signature, not the result bytes, and the manager's integrity model for a journal
row is "the signature is the account; a result that differs from it is refused"
(`store.replayed_as_signed`). The renewal's deadline is not in that account, so a
rewritten `expires_at` (reviewer's `renewal-probe.py`: 2030 clock, honest `expired`
True; result rewritten to 2099, `expired` False) changes the one decision the
renewal exists to make. Shape ownership (`boundaries.instant`) cannot see it.

The acquisition does not have this gap: `acquire` signs `acquired_at` and
`expires_at` (its identity is `_acquired_id(domain, generation)` and it is never
retried under a different clock), so `replayed_as_signed` verifies them.

Why the renewal cannot simply do the same: its replay contract. TOK-9: "Same-operation
replay returns the recorded renewal without extending again. A lost renewal reply
grants nothing beyond the committed authority state." Child A's review
2026-09-26T13:41:00Z found `returned` stamping the clock into its signed operands,
so an exact retry changed its own signature and collided with itself; `renew` was
written to avoid exactly that. Putting the decided instant into the signed
operands would reintroduce that collision for every lost-reply retry.

## Which judgement variants are affected (audit)

- RENEWED `expires_at`: DECISION INPUT. `token_of` answers it as the current
  deadline; `_owning` refuses or admits every late act on it; `_judge_expired`
  classifies against it. Affected.
- RENEWED `renewed_at`: informational (`token_of["renewed_at"]`); no decision reads
  it. Shape ownership is adequate.
- EXPIRED / TIMING_AMBIGUOUS `expires_at`, `revision`: COPIES of the state the
  judgement correlated with; no reader decides on them -- stickiness is the record's
  EXISTENCE (`judged is not None`). `observed_at`, `decided_at`: informational
  (`expiry_judged_at`, `timing_*`). Shape ownership is adequate; a hardening would be
  to compare the copies with the verified acquisition/renewal chain on read (cheap,
  additive, no semantics change), listed under option A below as optional.

## Option A (recommended): a self-signed DECISION record beside the renewal

Keep the renewal request record exactly as it is (identity, signed operands, replay).
In the same `transact` callback (`extend`), write a second record, kind
`resource-token.renewal-decided`, identity derived from the renewal's
(`_renewed_id(...) + ":decided"`), whose SIGNED OPERANDS ARE ITS RESULT:
`{version, domain, generation, revision, renewed_at, expires_at}`. `_renewals_of`
reads each renewal through the request record (unchanged) and its decision through
`replayed_as_signed`, refuses a renewal whose decision record is absent or whose
`expires_at`/`renewed_at` differ from the decision's, and answers the decision's
instants. The reviewer's probe then refuses instead of answering `expired` False.

- Replay: unchanged. A lost-reply retry carries the same request signature, `transact`
  answers the recorded renewal, `extend` is not reached and the decision record
  written with the first commit already stands. Nothing extends twice.
- Atomicity: both rows are written under `transact`'s `BEGIN IMMEDIATE`/SAVEPOINT;
  a rollback drops both. The decision record is written with `control._record`
  inside the callback, the same shape `settle_cleanup` uses inside an ending.
- Specification: TOK-9's text is satisfied as written ("durable operation ID,
  expected deadline revision and recorded new deadline"; the recorded deadline is
  now a signed record). No DESIGN.md text change. W275775's dossier gains the
  decision as a clarification ("the recorded new deadline is self-signed").
- Schema: none (same `operations` table; one more kind).
- Existing records: a renewal without a decision record is REFUSED on read as
  unverifiable (fail closed). Only disposable development stores exist for v12
  (owner ruling 2026-10-18: no production deployment selected), so no migration;
  if the owner prefers, a one-time reconciliation could write decision records from
  the result bytes of pre-existing renewals, explicitly labelled as adopted from
  unverified bytes.
- Decisive tests: the pinned regression (honest renewal, lost-reply replay, skip
  refusal, expiry against the renewed deadline, one record); the reviewer's probe
  as a negative witness (rewritten renewal `expires_at` refuses with "signed
  operands"); a renewal whose decision record is deleted refuses; the probe table
  gains the decision record's rows; `test_fence_wins_over_preflighted_renewal_replay`
  and the other test_stopped_settlement renewal cases unchanged.

## Option B: derive the deadline from signed data (semantics change)

Define the renewed deadline as the PREVIOUS deadline plus `seconds` (acquisition's
signed `expires_at` + the signed `seconds` of each renewal), not the clock plus
`seconds`. Then `_document` recomputes it from verified records and refuses a
differing result; no second record. But this changes the lease semantics (a renewal
asked early grants more than `seconds` from now), needs TOK-9 and W275775 text to
say "extends the recorded deadline by the renewal's lifetime", and changes every
existing deadline expectation in test_stopped_settlement / test_maintenance. Not
recommended for a correction.

## Option C: sign the decided instant (rejected)

Add `expires_at`/`renewed_at` to the signed operands. Verifiable, but a lost-reply
retry would compute a different signature and collide instead of replaying --
exactly the defect Child A corrected for `returned`. Rejected unless replay were
redefined to identity-only, which is a store contract change.

## What this packet asks

Select A (recommended) or B; A needs no specification text change and K implements
it as a bounded correction with the tests above. Until selected, the gap stands as
recorded here and in STAGE-C.md; the renewal's `expires_at` is NOT claimed protected.
