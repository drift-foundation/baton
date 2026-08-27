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

## Fourth review correction — 2026-08-25

`review-2026-08-25T10-49-54Z.md`: the centralized walk was right and its
ORDER was wrong. `boundaries.row` walked after every column rule, and several
of those rules name the value they reject — so a live bearer in a malformed
typed column reached a public `integrity.schema` diagnostic before the walk
could answer with the bounded refusal instead.

1. [done] The walk is the first content check after the row is copied. Safe
   that early because the copy is already exact built-in data: SQLite returns
   `str`, `int`, `float`, `bytes` or `None`, so the walk traverses plain
   values and runs nothing.
2. [done] The same ordering at every other public door whose input has already
   been made exact — `certified_agent_session_profile`,
   `certify_agent_session_profile` and `revive_refusal`. The shape is not
   specific to the function the finding named, and this Work has been
   corrected three times for fixing only what was named.
3. [done] `check_manifest_structure` is deliberately NOT moved: its input is a
   raw caller document, so the schema must establish the shape before anything
   traverses it. The distinction between the two groups is whether the input
   has been made exact built-in data yet, and it is recorded rather than left
   to be re-derived.
4. [done] The reviewer's regression and all five third-correction regressions
   are kept. Two cases added: one drives all four doors and requires
   `secret-leak` with no bearer in the message, and one requires the ordinary
   schema refusal to survive when nothing is held — a correction that turned
   every malformed document into `secret-leak` would be a different defect
   with a green gate.

## Fifth review correction — 2026-08-25

Status: **changes requested** in
`review-2026-08-25T13-19-17Z.md`.

1. [done 2026-08-25] Confirm the fourth correction at all four exact-data
   doors and its 60/60 focused gate.
2. [next] Prevent an ownership/type diagnostic from quoting a live bearer
   before §13 at `certify_agent_session_profile` and
   `record_inquiry_answer`. Keep the additive two-door regression and require
   `integrity.secret-leak` with no bearer in either message.
3. [next] Re-audit the remaining public document owners for any
   ownership/shape/content diagnostic that can run before their secret walk;
   the ordering boundary includes the first diagnostic, not only the first
   semantic validator.
4. [next] Rerun focused and affected adjacent gates, append exact evidence,
   and return for independent review.

## Fifth review correction — 2026-08-25

`review-2026-08-25T13-19-17Z.md`: two public document owners let an
ownership/type diagnostic quote a live bearer before their §13 walk. The
review's items 2 and 3 are done, and item 3's re-audit changed what item 2's
fix had to be.

1. [done] **The two named doors walk the RAW operand first.**
   `certify_agent_session_profile` and `record_inquiry_answer` both walk
   before `boundaries.document`. The review's refutation of the fourth
   correction's rationale is right and is recorded at both sites: this walk
   traverses only exact built-in `dict`, `list`, `tuple` and `str`, so it runs
   no caller behaviour and is safe on an unowned operand.
2. [done] **The re-audit, done by probe rather than by reading, found thirty
   leaking public surfaces rather than two.** Every callable in
   `worker_manager.__all__` was driven with the live bearer in every operand.
   The list is in `evidence/gate-after-fifth-correction-2026-08-25.txt`.
3. [done] **So §13 moves to the one crossing: `ContractRefusal.__init__`.**
   Any refusal naming a caller operand is a §13 surface — an ordinary
   `refused.precondition` leaks exactly as `integrity.schema` does — so
   door-local ordering is a list with one entry per public operation and one
   more for each one written later. The constructor already owns the message
   as durable text; "a bounded diagnostic cannot itself leak" is the fourth
   rule in that list. Pinned in `FINDING.md`.
4. [done] **A third door found by the re-audit:** `seal_refusal` quoted a
   live bearer in its type diagnostic. It walks first now.
5. [done] **The reviewer's additive two-door regression is kept and green**,
   answering `('secret-leak', False)` at both doors.
6. [done] **The probe is kept as a gate, not as a script.**
   `NoPublicRefusalQuotesALiveBearer` derives the same universe the public
   inventory does — asserted equal to it, so the two cannot drift — drives
   every surface with the bearer live, and requires the sweep to have driven
   something that refuses. `TheRefusalConstructorIsTheOneCrossing` holds the
   crossing's own behaviour, including the recursion the first version of this
   correction had.
7. [done] Focused 70/70; adjacent 295 OK; full source suite 1182 with the
   thirteen pre-existing failures, and the boundary-inventory seven PROVED
   pre-existing against a copy of this tree with the correction removed.
8. [next] Independent review.

## Sixth review correction — 2026-08-25

Status: **changes requested** in
`review-2026-08-25T22-52-21Z.md`.

1. [done 2026-08-25] Confirm the fifth correction's centralized crossing, the
   two named document-ordering fixes, its original 70/70 focused gate, and the
   byte-identical source/build mirrors.
2. [next] Remove the equality-only safety assumption for
   `SECRET_LEAK_MESSAGE`. Prove the replacement itself contains no currently
   live value, with a recursion-free fallback when the preferred prose
   overlaps one; preserve the raising site's durability.
3. [next] Keep the additive 32-character-substring regression and require the
   escaping `integrity.secret-leak` message not to contain that live bearer.
4. [next] Rerun the focused, adjacent, source and installed-layout gates,
   append exact evidence, and return for independent review.


## Sixth review correction — 2026-08-25

`review-2026-08-25T22-52-21Z.md`'s one [P1] is corrected. The crossing and the
durability propagation are kept, as the review required.

1. [done] **The equality exemption is removed.** The replacement passes the
   same containment test as every other message.
2. [done] **The fallback is an EMPTY message**, which is safe by construction:
   a non-empty value cannot be contained in it, and `remember_secret` refuses
   an empty value. It is also what bottoms the recursion, so no exemption is
   needed to terminate.
3. [done] **The closed pair survives.** `integrity.secret-leak` and the
   raising site's durability are unchanged; only the readable prose gives way,
   and only when it would leak.
4. [done] **One snapshot answers both questions**, so the message and its
   replacement are one decision rather than two that the registry can move
   between.
5. [done] **One assertion of mine was the defect and is replaced.**
   `..._is_this_build_s_own_prose_and_cannot_recurse` required the exempt
   construction to succeed; it now requires it to refuse. The reviewer's
   additive regression is kept as written and the full public-surface sweep is
   untouched.
6. [done] `test_secrets` 71 -> 75; adjacent 485 OK; source suite and locked
   build both 1223 with eleven failures, **none of them this Work's** — and
   `test_secrets` no longer appears in that list at all.
7. [next] Independent review.

## Seventh review correction — 2026-08-26

Status: **changes requested** in
`review-2026-08-26T01-53-20Z.md`.

1. [done 2026-08-26] Confirm the sixth correction's containment-safe preferred
   prose, empty terminal fallback, shared snapshot, durability propagation,
   and original 75/75 focused gate.
2. [next] Prevent `ContractRefusal`'s earlier category/code pairing assertions
   from interpolating a currently live operand. Preserve assertion taxonomy
   and the closed pair; do not turn invalid build-owned pairs into ordinary
   manager refusals.
3. [next] Keep the additive two-subcase regression, rerun focused, adjacent,
   source and installed-layout gates, and return for independent review.


## Seventh review correction — 2026-08-26

`review-2026-08-26T01-53-20Z.md`'s one [P1] is corrected. The crossing, the
durability propagation, the closed pairing and the assertion taxonomy are all
unchanged, as the review required.

1. [done] **The pair assertions are behind the guard.** `_rejected` renders a
   rejected category or code without ever carrying a live value.
2. [done] **Proved, not suppressed.** An ordinary bad pair is still quoted
   verbatim; only a live value gives way, and to a sentence that says so.
3. [done] **One snapshot** answers the pair assertions and the message guard.
4. [done] **A defect the review did not name**: `repr` ran caller-chosen code
   inside a diagnostic. A pair operand is named by its type now.
5. [done] `test_secrets` 76 -> 81, with the review's regression kept as
   written and five added; all measured to fail against the old rendering.
6. [done] Adjacent 590; source suite and locked build both 1239 with eleven
   failures, and `test_secrets` is not among them.
7. [done 2026-08-26] Independent review confirmed the original 81-case gate
   and found one remaining P1 at the whole constructor-assertion boundary.

## Eighth review correction — 2026-08-26

Status: **changes requested** in
`review-2026-08-26T03-10-29Z.md`.

1. [done 2026-08-26] Confirm the seventh correction for exact string pair
   operands, its one-snapshot rule, closed pairing, assertion taxonomy, and
   original 81/81 focused gate.
2. [next] Own category/code shape before mapping or set membership can hash a
   malformed operand. No rejected value may run caller code before the safe
   assertion is constructed.
3. [next] Prove the complete assertion text by containment against the same
   live snapshot, including pair redaction and inert type-name prose. Safe
   provenance does not establish safe content.
4. [next] Replace metaclass-dispatched type naming at the message and
   durability assertions with the existing safe type-name rule.
5. [next] Keep all three additive regressions and the public-surface sweep,
   rerun focused, adjacent, source and installed-layout gates, and return for
   independent review.


## Eighth review correction — 2026-08-26

`review-2026-08-26T03-10-29Z.md`'s one [P1], in all three manifestations.

1. [done] **Shape before membership.** Category and code are established as
   text before any `in` can hash them, so no caller `__hash__` runs and no
   unhashable operand escapes the taxonomy.
2. [done] **`_defect` proves the complete assertion text**, including any
   redaction sentence or type description it composes, against the one live
   snapshot.
3. [done] **`type_name_of` at the message and durability assertions**, which
   this module has owned since W6782.
4. [done] **By construction, and checked**: an AST case requires every
   `raise AssertionError` in the constructor to pass through `_defect`, and a
   sibling forbids `.__name__` lookup in the class.
5. [done] `test_secrets` 84 -> 90, with the review's three kept as written and
   six added; the whole correction measured to fail without it (7 failures,
   8 errors).
6. [done] Adjacent 682 OK. Source suite and locked build both 1250 with nine
   failures, taken over a tree hashed identical before and after.
7. [done 2026-08-26] Independent ninth review signed off the correction. The
   focused 90-case gate is green, source/build mirrors agree, and the full
   source run contains only the recorded seven boundary-inventory failures
   plus four Docker setup errors caused by this managed context's unavailable
   daemon. Durable review: `review-2026-08-26T04-12-33Z.md`.
