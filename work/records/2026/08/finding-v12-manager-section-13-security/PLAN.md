# Plan: worker-control section 13 security surfaces

1. [done 2026-08-24] Create this dossier and revalidate §13 and the closed W4
   record. Recorded in `FINDING.md`: the contract anchor is the `secret-leak`
   code, already in Python's closed `integrity` pairing, and §13 has no `$defs`
   because it is behaviour rather than a shape. The frozen host carries a
   complete reference whose five design decisions this Job should port rather
   than re-derive -- the walk at any depth, both halves being independent,
   value CONTAINMENT rather than equality, the named-field set, and the
   live-secret registry with synchronous cleanup.
2. [blocked on W6592] The leak refusal itself, applied to W6592's public and
   durable surfaces rather than to a parallel set this Job names.
3. [blocked on item 2] The live-secret registry and assignment-scoped delivery
   authority, with restart and cancellation FORGETTING rather than persisting.
4. [blocked on item 3] Bounded diagnostics that cannot themselves leak -- the
   place this Job meets W1593, since a refusal that quotes an operand is a
   durable surface like any other.
5. [blocked on item 4] The sweep: every durable and public surface this manager
   has -- operations, labels, logs, store rows, artifacts and refusals --
   enumerated rather than probed, in the manner the boundary inventory already
   uses, so a surface added later without a check fails the gate.
6. [blocked on item 5] Tests, evidence and independent review.

## Implementation — 2026-08-25

Status: **changes requested.** W6592 closed satisfying, so items 2–6 were
unblocked and implemented; item 8 is the active correction from independent
review.

2. [done] The leak refusal, applied to the completed public and durable
   surfaces: the manifest composite (which is now the trust entry its own
   docstring promised), the agent-session profile certification, and
   `ControlStore._record` — the journal every mutating act passes through.
3. [done] The reference-counted registry, with `held_secret` as a context
   manager so an act's registration ends however the act ends, and the bearer
   made live for exactly the offer acts that spend it. Restart and cancellation
   forget by construction: the registry is process state and reaches no column.
4. [done] Bounded diagnostics that cannot themselves leak — a durable refusal
   is sealed into the journal, so its message is walked with the bearer live.
   This is where §13 meets W1593, and the containment case is what proves it.
5. [done] The sweep, DERIVED from the AST: every INSERT and UPDATE in the
   manager package, keyed by module, lexical site and table, each covered by
   the journal walk or by a declared entry naming the rule that covers it —
   and the declarations checked for staleness in the other direction.
6. [done] Tests and evidence: `tests/manager/test_secrets.py`, 39 cases; the
   contracts inventory's ownership and probe tables extended;
   `evidence/gate-after-2026-08-25.txt` bounds what this slice changed.
7. [done 2026-08-25] Independent review recorded in
   `review-2026-08-25T06-35-31Z.md`: changes requested on one P1 coverage
   defect. The derived sweep enumerates durable writers but not public
   surfaces; `manager_signature` and `seal_refusal` both construct and return
   live-bearer representations before the later journal guard runs.
8. [next] Guard protocol-identity and portable-refusal construction before
   either public operation returns, keep both added regressions, and extend
   the bidirectional derived inventory to the applicable public surfaces PLAN
   item 5 requires. Return for independent review.

## Review correction — 2026-08-25

Status: **changes requested after re-review.**

1. [done] [P1]: `manager_signature` and `seal_refusal` walk before they answer.
   §13 now guards the public CONSTRUCTION boundary, not only the eventual
   journal write — a guard that runs after protocol identity or a portable
   diagnostic has been handed out establishes nothing about either.
2. [done] Item 5's public half is derived: every exported callable from
   `__all__`, each in exactly one declared class, checked both ways, with the
   constructing ones probed against a live bearer.
3. [done] Both reviewer regressions kept and green; `test_secrets` is 45/45 and
   the full suite carries only the twelve pre-existing failures.
4. [done 2026-08-25] Re-review confirmed the two original constructor fixes,
   then found the public inventory incomplete. Durable review:
   `review-2026-08-25T06-57-14Z.md`.
5. [done 2026-08-25] Walk direct `revive_refusal` input and retained profiles
   on read; derive and classify public methods of exported classes; re-audit
   prose-only classifications that return adopted or composed content. Keep
   the three added regressions and return for independent review.

## Second review correction — 2026-08-25

1. [done] **`revive_refusal` walks its input.** The old reason said the bytes
   were walked on the way in. That is true of `_revived`, the internal replay
   path, whose input is a journal row this build wrote — and false of the
   public door, whose input is whatever text a caller holds. The two paths
   were already split for the adoption; the §13 walk now follows the same
   split, and `_revived` says out loud why it does NOT walk: re-walking a
   journal row `_record` already cleared would be blanket revalidation, and it
   would make an exact durable replay of a refusal quoting a since-forgotten
   secret fail on the retry.
2. [done] **`certified_agent_session_profile` re-walks before returning.** The
   function exists because a write-side guard cannot see a later store edit,
   and it already re-checks shape and digest for that reason. §13 was the one
   rule left out of its own argument.
3. [done] **Both moved from the prose-only class to the constructing one**,
   with reasons that describe the public path, and both are probed there
   against a live bearer.
4. [done] **The universe reaches methods.** `exported()` walks an exported
   class's public attributes, so `ControlStore.operation_record`, `replay`,
   `transact`, `open`, `close` and the eight `AuthorityPort` members are each
   classified. `test_the_method_universe_is_derived_and_not_listed` asserts
   the enumeration against `dir()` for BOTH classes, so a method added
   tomorrow is in the universe tomorrow and an enumeration that quietly
   covered one class fails.
5. [done] **The re-audit found a third false reason, and it was a real
   leak.** `record_inquiry_answer`'s durable-sweep entry and its public entry
   both credited the journalled signature `_ask` walks. They should not have:
   an answer arrives at its own boundary long after the request, and that
   function writes through a direct `UPDATE` rather than `transact`. An answer
   body carrying a live bearer reached the `interrogations.answer` column with
   no walk at all. It is guarded at its own boundary now, with three
   regressions — a live bearer refused and not written, a member NAMED for a
   secret refused, and an ordinary answer recorded unchanged.
   `request_freeze`'s reason was also corrected: it answers with a request
   document, not with what `record_frozen_result` walked.

## Third review correction — 2026-08-25

Status: **changes requested after third review.** Durable review:
`review-2026-08-25T09-30-45Z.md`.

1. [done 2026-08-25] Confirm the three second-review corrections and their
   52/52 focused gate.
2. [next] Walk adopted journal rows at the receiving boundary before
   `ControlStore.operation_record` or `replay` can return them. Keep the added
   two-surface regression and require `integrity.secret-leak` from both.
3. [next] Re-audit the remaining public persisted-row projections. Replace any
   reason that relies only on a past write-side walk with evidence about the
   bytes received now; update the derived public accounting accordingly.
4. [next] Run the focused and affected adjacent manager gates, record durable
   evidence, and return for independent review.

## Third review correction — 2026-08-25

`review-2026-08-25T09-30-45Z.md`: the three second-review corrections are
present and the 52-case gate was green, but one false safe-by-reason
classification survived — journal rows were not walked at their receiving
boundary, so a hand edit could put a live bearer into `operations.result` and
both `operation_record` and `replay` would return it.

1. [done] **The walk is at `boundaries.row`, not in the two readers the review
   named.** The column contract proves the SET and the SHAPES and says nothing
   about content; that function's own docstring already calls the store a
   receiving trust domain, which is the argument for putting §13 there. Every
   adopted row in this manager comes through it, so a projection added
   tomorrow is covered tomorrow — whereas "walk it in each public reader" is a
   list somebody has to maintain, and this Work has now been corrected three
   times for reasons that described a path other than the one that ran.
2. [done] **Correction 2's re-audit, done by construction rather than by
   inspection.** Every public persisted-row projection —
   `claimed_offers_for`, `agent_sessions_of`, `posture_slot`,
   `frozen_output_of`, `interrogation_of`, `interrogations_of`,
   `operation_record`, `replay` — reaches the same guard. Their inventory
   reasons are rewritten to say the row is walked where it crosses out of the
   store, which is a statement about the bytes leaving the read.
3. [done] **The ownership split is kept and is now the point.** The rule is
   DYNAMIC: it refuses a value this process is holding live. A genuinely
   forgotten secret is absent from the registry, so its row stays readable and
   an exact durable replay still returns it —
   `test_a_forgotten_value_stays_readable_and_replayable`.
4. [done] The reviewer's regression is kept and both subcases refuse with
   `integrity.secret-leak`. Four cases of mine generalize it: a hand-edited
   offer cannot leave `claimed_offers_for`; a forgotten value stays
   replayable; the bearer `issue_offer` deliberately returns is never a
   persisted column, so the central walk cannot collide with the one
   sanctioned disclosure; and the guard is proved to be reached from a reader
   whose own module contains no §13 call at all.

## Fourth review correction — 2026-08-25

Status: **changes requested** in
`review-2026-08-25T10-49-54Z.md`.

1. [done 2026-08-25] Confirm the centralized row guard, the original two-read
   regression, the four generalizing cases, and the 57/57 focused gate.
2. [next] Run `check_no_durable_secret` as the first row-content rule, before
   any column validator can quote a live bearer into its own refusal. Preserve
   the one-crossing design and the dynamic forgotten-value behavior.
3. [next] Keep the additive invalid-instant regression and require both
   `integrity.secret-leak` and a diagnostic containing no bearer.
4. [next] Rerun focused, affected adjacent, full source and installed-layout
   gates, append exact evidence, and return for independent review.
