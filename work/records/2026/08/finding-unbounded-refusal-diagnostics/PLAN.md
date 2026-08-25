# Plan: bound a refusal diagnostic by its rule, not by the rejected value

1. [done 2026-08-23] Revalidated on the current tree: 269,042-character
   envelope refusal, 269,065-character nested-fs refusal, and 20,000 retained
   names in a coarse shape snapshot. Evidence:
   `evidence/reviewer-research-2026-08-23.txt`.
2. [awaiting Slawomir ruling] Decide the diagnostic shape before
   implementation. Reviewer proposal: preserve individually bounded names for
   a small mismatch; for a wide record report total count, a fixed bounded
   sample and omitted count; keep the whole message under 500 characters.
3. [implementation-ready after item 2] Bound the MESSAGE and every AVOIDABLE
   unit of work. Exact own-key proof has an unavoidable O(n) reflection lower
   bound because JavaScript returns complete own-key arrays. Separate coarse
   shape classification from key enumeration; reflect the exact key set once
   in `recordFault`; compare counts first; and never map, sort or join the full
   wide mismatch.
4. [queued] Preserve every signed-off behaviour: the exact-member verdict,
   hidden and non-enumerable member rules, accessor refusal, the Proxy-first
   non-observing guard, and each caller's own error taxonomy.
5. [done 2026-08-23; reviewer regressions] Enabled both capability rows in
   W4's under-500 property and added primitive message-bound and coarse-shape
   no-enumeration cases. Full v12 is 684/687 with exactly these three cases
   failing.
6. [queued; implementer only] Create this dossier's missing `PROGRESS.md`
   before recording implementation progress; reviewers do not write it.
7. [approved 2026-08-23; supersedes items 2-3 as Node implementation work]
   Carry the bounded hybrid into the Python Worker Manager: expected rule,
   missing expected members, total received count, at most four bounded
   unexpected names, omitted count, no values or Symbol descriptions, and a
   complete message below 500 characters. Preserve the one unavoidable exact
   key observation while bounding avoidable secondary work. Retain the Node
   measurements and red additive cases as reference evidence; do not extend
   host-side `records.mjs`. Replan the executable acceptance against the Python
   manager before implementation and create `PROGRESS.md` only when that
   implementation claim begins.
8. [done 2026-08-24; W4 dependency discharged] Treat W4's Python contracts/POD slice as
   the one implementation owner. After W4 lands, independently assess the
   primitive and public capability boundaries with wide/small, missing/extra,
   zero-through-more-than-four, long-Unicode and non-string-name rows; hostile
   rendering/iteration hooks; no member values; the caller-local closed pair;
   sub-500 output; and no key enumeration for coarse shape prose. Preserve
   exact-key validation and its unavoidable complete observation. Review:
   `review-2026-08-24T04-09-26Z.md`.
9. [reference evidence, deliberately red] Keep the three Node regressions and
   269k-character measurements unchanged. Host-side JavaScript is frozen; the
   Python black-box/catalog is the acceptance gate that closes this Work.
10. [done 2026-08-24; changes requested] Re-reviewed W4's Python POD primitive.
    Preserve the bounded sampling, hostile/non-string inertness, exact verdict,
    caller taxonomy and coarse no-enumeration behavior. Correct `own_record` so
    one diagnostic reports the expected exact-record rule, missing expected
    members, total received count, at most four bounded unexpected names, and
    the omitted count. Evidence and review:
    `evidence/review-python-diagnostic-2026-08-24.txt` and
    `review-2026-08-24T22-18-51Z.md`.
11. [implementation-ready; implementer] Create the missing `PROGRESS.md`, then
    make the confined POD diagnostic correction and turn the four additive
    primitive methods green. Do not change the frozen Node reference.
12. [blocked on separately scheduled manager composition] Exercise the same
    invariant through the actual public ACP client-capability consumer once
    that Python boundary exists. Do not create a speculative public API in
    W1593 merely to satisfy a test; final sign-off needs the real boundary and
    its caller-local closed refusal pair.
13. [done 2026-08-24; item 11 discharged] Created this dossier's `PROGRESS.md`
    and made the confined POD correction. `own_record` now emits ONE diagnostic
    carrying the exact-record rule, the missing expected members, the total
    received member count, a bounded sample of unexpected names and the omitted
    count; only the clauses TRUE OF THIS DOCUMENT appear, so a record that
    breaks one side is not told about a violation it did not commit. Under 500
    characters at every measured shape (308 combined, 393 for sixty
    300-character names, 391 for four 300-emoji names).
    The work behind the message moved too, which is the half this Work is
    named for: `counted_sample_of` replaces `sample_of`'s `list(names)[:3]`, so
    the rejected name set is WALKED ONCE AND NEVER COPIED and `own_record`
    passes a generator. The membership test is a `frozenset` of our own
    required names. `sample_of` remains as a one-line call, keeping one
    definition of the bound.
    Mutation 14 of 14 killed. THE FIRST ROUND FOUND A DEFECT IN MY TEST rather
    than in the code: re-inserting `list(names)` left every behavioural case
    green, because a copy consumes a generator exactly once too. The property
    is a property of the CODE SHAPE, so a narrow structural case now forbids
    materializing the operand, and that mutant dies.
    The frozen Node reference is untouched and its three cases stay red as
    item 9 requires. NO PUBLIC CAPABILITY API WAS INVENTED: revalidated on the
    current tree, `clientCapabilities` appears only in
    `contracts/schema/agent-session-1.0.schema.json`, so item 12 remains
    blocked on the composition work rather than satisfied by a boundary built
    backwards for a test.
    Gate 585/585 at source and in the locked build. Evidence:
    `evidence/implementation-bounded-diagnostic-2026-08-24.txt`.
14. [signed off 2026-08-24; primitive complete] Independently inspected the
    one-pass bounded sampler and combined rule-oriented refusal. Focused POD is
    31/31 and the source gate is 585/585 with one expected ambient-dependency
    skip. The managed reviewer could not repeat the locked install because its
    package index is unavailable; the implementer's recorded locked gate is
    585/585. Review and evidence:
    `review-2026-08-24T22-32-23Z.md` and
    `evidence/review-python-correction-2026-08-24.txt`.
15. [blocked on W6592; item 12 remains live] W6592 is the separately scheduled
    M2 contracts-inventory/public-composition Job. Once it exposes the real
    Python ACP client-capability consumer, exercise
    this signed-off primitive invariant through the caller-local black-box
    refusal. Do not reopen the primitive or invent a test-only public API.
16. [done 2026-08-25; final sign-off] W6592 closed satisfying and exposed the
    real public `check_client_capabilities` consumer. Its 20,000-member
    black-box case preserves `policy.denied` and a sub-500-character reason.
    Independently verified that case 1/1, the POD primitive 31/31, and the
    complete handshake/composition module 32/32. Items 12 and 15 are
    discharged; W1593 is complete. Review:
    `review-2026-08-25T00-30-06Z.md`.
