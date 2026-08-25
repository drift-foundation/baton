# Finding: a refusal diagnostic is bounded by the rejected value

Discovered during W4/W2929 composition revalidation on 2026-08-23, while
correcting the same defect one module away.
Canonical Baton Work: W1593 (`2b077949-W1593`), follow-up of the closed W641.

## Observed

`v12/src/worker_manager/records.mjs` — the shared inert-record proof W641
built and owns — interpolates EVERY own member name of a rejected record into
its fault text:

```js
return `carries [${names.join(", ")}] and the contract sends ...`;
```

Measured against the product boundary that consumes it:

| offered value                                   | answer                     |
| ----------------------------------------------- | -------------------------- |
| capability envelope with 20,000 own members      | `policy.denied`, **269,042 characters** |
| capability `fs` with 20,000 own members          | `policy.denied`, **269,065 characters** |

The verdict is correct and the closed `category`/`code` pair holds. Nothing
here is unsafe. The refusal is correct and enormous.

`classify` also materializes the full own-name list before any of this, so the
transient work is proportional to the rejected value as well as the message.

## Why this is a finding and not a nit

W2929's item 4as took the same finding one module away, on the diagnostic
bound in `contracts.mjs`: it probed a length cheaply and then spread a whole
string to slice sixty characters off the front — 1,063 iterator steps for a
61-character answer. The independent review's words were **"a bounded output
is not a bounded operation"**.

That is this, at the member-name list. And it is one property over from the
rule six W2929 review rounds established: **a refusal must never run the value
it is refusing.** The transient cost of explaining a rejection should not
scale with the rejected value either.

A refusal message is also the thing most likely to be logged, retained or
carried onto a wire, which is why W2929 bounds caller-controlled renderings at
60 characters everywhere else in this manager.

## Suggested direction, not a ruling

The shape that worked in W2929 was ONE PASS THAT STOPS: build what the message
needs while counting, return as soon as the limit is passed, and keep a cheap
`.length` test in front so the ordinary case is not iterated at all.

For a member list the natural equivalent also reads better: name the first few
and COUNT the rest. `carries 20,000 members including a, b, c` is a more
useful diagnostic than 20,000 names.

Whatever is chosen, the existing behaviour must not move: the exact-member
verdict, the hidden and non-enumerable member rules, the accessor refusal, the
Proxy-first non-observing guard, and each caller's own error taxonomy are all
signed off across three W641 review rounds.

## Ownership

`records.mjs` is W641's. W641 closed satisfying before this was measured, so
this is a follow-up rather than a reopened round. W2929 declined to fix it
from its own claim: item 4ai reserves that module to W641, and a fix from W4
would have put the change in the wrong Work.

W2929 item 4as added a regression asserting this property over W4's OWN five
boundaries — a reference and an update with 20,000 members and three
40,000-character identifiers, each refusing in under 500 characters. It
carries this measurement in a comment and the two capability rows it should
grow once this is closed.

Nothing fails today because of this: the full v12 gate is 685/685.

## Evidence

`evidence/measurement-2026-08-23.txt`, and W2929's
`evidence/correction-composition-round3-2026-08-23.txt` for the sibling
correction and the shape it used.

## Independent reviewer research — 2026-08-23

**Confirmed:** the measurements reproduce on the current tree. The two ACP
capability refusals are 269,042 and 269,065 characters. A coarse
`describe()` of the same 20,000-member plain record says only “a plain
object” but its shared classification snapshot still retains all 20,000
names.

**Constraint:** exact own-member validation cannot have work wholly bounded
independently of input size. JavaScript own-key reflection returns complete
arrays, and proving there is no extra enumerable, hidden or symbol member
requires one complete key-set observation. That is the unavoidable O(n)
lower bound if the signed-off exact-record verdict remains. The actionable
boundary is therefore: bound the MESSAGE and every avoidable pass/copy/sort,
not claim the reflection lower bound disappeared.

**Confirmed avoidable work:** `classify` gathers keys for coarse shape callers
that never use them. `recordFault` then maps, sorts and joins the complete key
set even when its count already proves mismatch. Shape classification can be
separated from member enumeration; exact `recordFault` can reflect once,
compare counts first, and avoid full transformations on the wide mismatch.

**Proposed diagnostic ruling:** preserve useful small mismatch names, but
bound each; for a wide record report the total count, a fixed bounded sample,
and the omitted count. Keep the whole refusal below 500 characters, reveal no
member values or Symbol descriptions, and preserve caller-local taxonomies
and every signed-off record rule. This is reviewer decision support, not yet
product authority.

Three additive regressions now fail exactly at the primitive and two ACP
consumer boundaries. Focused records is 8/10, taxonomy 11/12, and full v12
684/687. Evidence: `evidence/reviewer-research-2026-08-23.txt`.

**Operational finding:** this dossier has no `PROGRESS.md`. That file is
implementer-owned under repository policy; the implementer must create it
before recording progress. The reviewer did not create it.

## Bounded diagnostic ruling and Python placement — confirmed 2026-08-23

Slawomir approves the bounded hybrid as a portable Worker Manager invariant.
A rejected exact-record document reports the expected rule, missing expected
members, total received member count, at most four individually bounded
unexpected names, and the omitted count. The complete diagnostic remains
below 500 characters and includes no member values or Symbol descriptions.
Exact-key validation may perform its one unavoidable complete key observation,
but coarse diagnostics and avoidable mapping, sorting, joining, copying, or
rendering do not scale across the full rejected key set.

The same ruling also fixes implementation placement. V12 host-side Baton and
the Worker Manager are Python; no new Node or JavaScript code is implemented
outside an isolated worker image. Therefore the existing `records.mjs`
measurement and three additive regressions remain executable-reference
evidence, not authorization for another host-side JavaScript correction. The
Python manager must satisfy the bounded diagnostic through portable black-box
acceptance plus Python-focused unit evidence. The verdict, exact POD rules,
caller-local refusal taxonomy, and no-user-behavior boundary remain unchanged.

## Placement review — 2026-08-24

**Confirmed:** the approved diagnostic is part of W4's Python contracts/POD
slice, not a second implementation beside it. W1593 will wait on W4 and then
independently assess the Python primitive and public capability boundaries.
The existing red Node cases remain measurements against frozen reference code;
their remaining red is expected and is not a request to extend `records.mjs`.

Portable evidence must cover wide and small mismatches, missing plus extra
members, zero through more-than-four unexpected names, long Unicode names,
non-string keys, hostile rendering/iteration hooks, no leaked values, the
caller-local closed refusal pair, sub-500-character output, and a coarse shape
description that performs no key enumeration. Exact POD validation remains
complete; only its diagnostic and avoidable secondary work are bounded.
Review: `review-2026-08-24T04-09-26Z.md`.

## Independent Python review — 2026-08-24

**Confirmed:** W4's Python POD primitive bounds the existing extra-name sample,
long Unicode inputs, non-string names, hostile rendering hooks, and coarse
description of a mapping subclass. The exact-record verdict remains a refusal,
the caller's closed refusal pair is unchanged, and the exercised messages stay
below 500 characters. Coarse refusal performs no caller key enumeration.

**Changes requested:** `own_record` returns as soon as it sees unexpected
members. It therefore cannot report missing expected members in the same
diagnostic, and neither its extra nor missing branch reports the total received
member count. A record containing only `authority_uuid` plus seven unexpected
members says only that three unexpected names and four more arrived; it omits
the missing `work_id`, `participant`, and `provider_session_id`, and omits the
fact that eight members were received. This violates the confirmed hybrid even
though the output is bounded.

Four additive primitive methods preserve the accepted properties and expose
the missing clauses. Focused POD is 27 methods with six failure reports (one
method plus five subtests). The full Python source gate is 581 methods with the
same six failure reports and one environment-sensitive dependency skip; no
pre-existing test fails.

**Scope prerequisite:** the Python tree exposes no ACP client-capability
consumer yet. The frozen schemas name `clientCapabilities`, but there is no
Python public boundary at which to prove the caller-local capability refusal
and black-box composition required by the placement review. W1593 must not
invent that API. Its primitive correction is implementation-ready here; final
sign-off remains contingent on the separately scheduled manager composition
work exposing the real boundary.

Evidence: `evidence/review-python-diagnostic-2026-08-24.txt`. Review:
`review-2026-08-24T22-18-51Z.md`.

## Primitive correction review — 2026-08-24

**Signed off at the Python POD primitive:** `own_record` now computes missing
and unexpected names before one refusal, states the expected exact-record rule
and exact received count, samples at most three individually bounded unexpected
names, reports the omitted count, and emits only the missing/extra clauses that
are true of the rejected document. `counted_sample_of` walks its operand once
and retains only the bounded sample; `own_record` supplies its unexpected names
as a generator and materializes no rejected-name collection for prose.

Independent focused verification is 31/31. The source stage of `just gate` is
585/585 with one expected ambient-versus-locked dependency skip. This managed
reviewer could not independently repeat the locked stage because its package
index is unavailable: the hash-locked install stopped before build or tests.
The implementer's recorded locked result is 585/585. This is a verification
limitation, not contrary product evidence, and no escalation is permitted for a
managed reviewer turn.

**Overall Work remains gated:** the Python source still has no public ACP
client-capability consumer outside the frozen schema assets. The primitive is
accepted, but W1593 cannot close until the separately scheduled contracts
inventory/public-composition Job exposes the actual consumer and the portable
black-box diagnostic is exercised through its caller-local refusal pair.

Evidence: `evidence/review-python-correction-2026-08-24.txt`. Review:
`review-2026-08-24T22-32-23Z.md`.

**Coordination:** W6592, “M2: Complete Python manager contracts inventory and
public composition,” was created under W3 as the concrete owner of that
prerequisite. W1593 depends on W6592 for public-boundary acceptance only; the
signed-off primitive is not reopened by that dependency.

## Final public-boundary review — 2026-08-25

**Confirmed and signed off:** W6592 now exposes the real public
`check_client_capabilities` boundary. Its black-box W1593 case sends an exact
built-in document with 20,000 unexpected members through that boundary,
observes the caller-local closed pair `policy.denied`, and requires the
explanation to remain below 500 characters. The boundary uses the signed-off
`own_record` diagnostic as its reason without inheriting the primitive's
taxonomy.

Independent verification is 1/1 for the wide black-box acceptance, 31/31 for
the unchanged POD primitive, and 32/32 for the complete handshake/composition
module. The public-composition prerequisite is discharged and W1593 is
complete. The deliberately red frozen Node measurements remain reference
evidence and are not part of this Python acceptance gate.

Review: `review-2026-08-25T00-30-06Z.md`.
