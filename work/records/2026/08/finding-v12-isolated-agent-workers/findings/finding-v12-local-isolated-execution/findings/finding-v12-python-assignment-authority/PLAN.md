# Plan: Python v12 assignment authority

1. [done 2026-08-24] Revalidated W151 `1-ruled`, all 64 current executable
   design cases, the complete signed-off W2928 record, 75 frozen Node authority
   test names and the current Python/SQLite/build environment. Pinned the
   Python-owned behavior without transliterating Proxy/getter/Date/undefined
   mechanics. Review: `review-2026-08-24T04-20-07Z.md`; evidence:
   `evidence/python-authority-boundary-2026-08-24.txt`.
2. [done 2026-08-24; independently signed off] Established the self-contained `v12/python/` package
   and lock/build gate, then implement Refusal, exact built-in POD ownership,
   frozen snake-case identity/gate/signature helpers, Python-authority store
   kind, and distinct non-adopting `Authority.create`/`open`. This authority
   slice has no third-party runtime dependency and uses `unittest`; do not add
   W4's schema validator early. Independent review found stale/live UUID
   divergence, malformed UUID adoption, commit-on-open-failure, exported helper
   callback execution, unbounded integer diagnostic faults, and an unexercised
   build lock. All six are corrected with focused regressions and the locked
   installed-layout gate. Reviews: `review-2026-08-24T04-41-03Z.md` and
   `review-2026-08-24T04-51-24Z.md`.
3. [done 2026-08-24; independently signed off] Implement Work/route/capability/
   contract configuration, generation-bearing claim, deployment-wide claim
   slot, centralized assignment end, fences, typed gates, events, projections
   and invariant checks. Independent review found a cross-Work gate CAS,
   unsafe generation overflow, unvalidated durable Unicode and gate evidence,
   missing/full-identity event history, a cancellation taxonomy escape, and an
   incomplete scheduler invariant backstop. All seven are corrected with
   focused regressions. Reviews: `review-2026-08-24T05-12-08Z.md` and
   `review-2026-08-24T05-21-50Z.md`.
4. [done 2026-08-24; independently signed off] Implemented the authority operation journal,
   savepoint-scoped ordinary/durable refusals, exact replay/collision,
   retirement/settlement, restart and deterministic real-process races.
   Independent review found that settlement and journal reads bypass the
   frozen opaque operation-ID grammar, allowing invalid durable retirements,
   and that installed-gate race children force-import the source tree. Both are
   corrected with focused regressions and child/parent package-origin proof.
   Reviews: `review-2026-08-24T05-38-39Z.md` and
   `review-2026-08-24T05-47-26Z.md`.
5. [done 2026-08-24; independently signed off] Implemented contract
   progression, proposal publication, immutable verification/review/approval/
   integration receipts, policy-generation binding, configured capabilities,
   authorized close and stale-target durable integration attempts. Independent
   review found three gaps: result identities lacked opaque-ID and immutable-
   binding enforcement, malformed canonical-target policy could escape as a
   SQLite fault or empty durable target, and Cut 4 projections omitted the
   authority UUID or whole assignment identity. All three are corrected; the
   reviewer added the requested restart/read/fresh-copy regression, and the
   complete source and installed-wheel gate passes 175/175. Reviews:
   `review-2026-08-24T06-03-28Z.md` and
   `review-2026-08-24T06-12-12Z.md`.
6. [done 2026-08-24; final independently signed off] Implemented the exported bootstrap and
   participant-bound session faces, enumerated transition/read surface, owned
   operands, fresh answers, portable catalog, and long-signature settlement
   measurement. The two Session-boundary findings from final review are
   corrected and independently green. Re-review then confirmed the
   implementer's raised earlier-Core diagnostic gap: public bootstrap and
   runtime paths still produce million-character Refusals from valid Work and
   participant identities, violating the package's own bounded-diagnostic
   rule. Audit every authority Refusal for raw caller-controlled or
   caller-originated stored text. That audit corrects 26 sites and the prior
   reviewer cases are green, but re-review found its global `what` allow-list
   misses caller-supplied labels on ten exported identity helpers, while its
   string-prefix classifier accepts bounded-plus-raw expressions and arbitrary
   joins. Those paths are corrected and independently green at 221/221 source
   and installed, but re-review found that a lone-surrogate label is still
   unencodable and the origin proof crossed module-name shadowing, nested
   scopes, unsafe reaching assignments, and same-named nested functions. Those
   final paths are corrected: all three reviewer methods pass, and the complete
   source and installed-wheel gate passes 227/227. No operand cap or settlement
   change. Reviews:
   `review-2026-08-24T06-36-30Z.md`,
   `review-2026-08-24T06-51-18Z.md`,
   `review-2026-08-24T07-10-44Z.md`,
   `review-2026-08-24T07-25-10Z.md`, and
   `review-2026-08-24T07-33-54Z.md`.
7. [done 2026-08-24] Close W2845 satisfying on the recorded final sign-off. The existing dependency
   then unblocks W4 so the Python Worker Manager consumes the real minted
   session and authority-owned claim signature rather than inventing or
   mirroring authority.

## Cut 1 outcome — 2026-08-24

Delivered: `v12/python/` with `pyproject.toml` (>=3.13, no runtime dependency
and deliberately no schema validator), `requirements.lock` (an EMPTY runtime set
stated rather than omitted, plus two build artifacts whose hashes were
RECOMPUTED from the local wheels rather than copied), a `justfile` gate that
refuses an interpreter below 3.13, and
`src/baton_v12/authority/{errors,identity,schema,store,api}.py`.

The one deliberate divergence from the frozen Node host is `create`/`open`: its
single create-or-adopt `open` writes the schema before establishing whose store
it is, which is silent adoption once three neighbouring SQLite files also call
their first schema version `1`. Kind is checked before version before UUID, and
every refusal leaves the file exactly as found — the journal mode, the only
persistent setting involved, is withheld until the recheck under the write lock.

Twenty mutations: nineteen witnessed, one reported as a genuine equivalence
(the explicit empty-file check, which the read-only probe already covers and
which is kept for its better diagnosis). Three zeros were my instrument or my
coverage, and two more instrument errors turned up in the boundary tests; all
five are named in the evidence.

`just gate` 53/53 on Python 3.13.7; zero retained temp roots; the frozen Node
authority and its seven test files untouched; the Node gate unchanged at
684/687 with its three W1593-owned failures.
Evidence: `evidence/cut1-2026-08-24.txt`.

## Cut 1 correction — 2026-08-24

Five P1 and one P2 from `review-2026-08-24T04-41-03Z.md`, all reproduced first
and all closed. `open` now takes its identity from the LIVE recheck and refuses
a probe/live disagreement; the recorded UUID is held to the frozen grammar on
both reads; commit is on the success path only; the three exported helpers that
ran caller code or answered unvalidated operands prove their operands first; and
wide integers are named by bit length, because `str()` of one is not inert in
Python 3.13 and the diagnostic was the escape.

`requirements.lock` is CONSUMED now: `just build` resolves it offline with
`--require-hashes --ignore-installed`, installs with `--no-build-isolation`,
imports from outside the source tree, and runs the suite against the INSTALLED
layout — refusing rather than skipping when the wheelhouse is absent, and part
of `just gate`.

Ten mutations, nine witnessed, one equivalent given its neighbour and reported
as such. Seven regressions added; the suite is 53 -> 60. `just gate` all green
on Python 3.13.7; frozen Node reference untouched; whitespace clean.
Evidence: `evidence/cut1-correction-2026-08-24.txt`.

## Cut 2 outcome — 2026-08-24

Configuration, the generation-bearing claim, the deployment-wide slot, the ONE
assignment-ending helper with all six of its Handler-clear callers, fences,
typed gate install and satisfaction, events, projections and the invariant
backstop. `Core` stays private; the bootstrap face gained configuration and
projections and NO transition.

DELIBERATELY NOT ADDED: the `operation_id` operand. The journal is cut 3, and an
operand with no mechanism behind it is the defect the cut-1 review named about
the lock. Cut 3 changes these signatures; that is stated rather than discovered.

Three gaps found by probing my own cut before handing it over: a stale `expect`
was ignored on an unclaimed Work (a deliberate divergence from the frozen host,
on its own rule); a clock answering garbage wrote garbage into a durable
timestamp (the frozen grammar is enforced now); and a clock that raises is left
to raise, as a trusted collaborator's fault, with a case proving it takes
nothing with it.

Twenty-four mutations. Four zeros: two were guards whose value was the MESSAGE,
now asserted so both mutations fail; one was my mutation being nonsense; one is
a genuine equivalence today that becomes load-bearing in cut 4. 39 regressions
added, the suite is 60 -> 99, `just gate` all green including the locked build.
Evidence: `evidence/cut2-2026-08-24.txt`.

## Cut 2 correction — 2026-08-24

Seven findings, all reproduced first and all closed. `install_gate` requires the
supplied identity to belong to the Work being acted on (it could compare Y and
end Y while gating X); `claim` refuses when the frozen generation range is
exhausted rather than minting an unreadable number; one `check_text` rule
replaces the weaker scalar one, so no lone surrogate reaches SQLite or a durable
gate token; gate evidence is validated by SHAPE per kind and bound to the
configured fact; `claim` writes its event atomically and every assignment event
answers with the full four-part identity; the missing-assignment refusal is
common to all four ending transitions; and the invariant backstop checks the
closed phase axis, both directions of the phase/gate pairing, and the gate's
kind and detail.

ONE REPRESENTATION DECISION RAISED: the pinned isolation clause is now an
identity the evidence must name, not a boolean. Strict reading taken as the safe
direction; overrule it and I will change it.

Fourteen mutations, thirteen witnessed; the one zero was a guard whose value was
the MESSAGE, now asserted. Eight regressions added, the suite is 99 -> 107, all
99 prior cases preserved with the two that pinned the reference's event omission
updated. `just gate` all green including the locked installed-layout build.
Evidence: `evidence/cut2-correction-2026-08-24.txt`.

## Cut 3 outcome — 2026-08-24

The operation journal with its four durable states, the savepoint that stores an
ordinary refusal and a durable one in opposite ways, exact replay and collision
over the FULL operands including the prose, retirement answered before the
operands, settlement as one transaction rather than lookup-then-write with
`may_retire` defaulting to false, the single fault-injection seam that makes
"I could not ask" testable, restart, and three real spawned-process races.

The `operation_id` operand arrived with the mechanism, as cut 2 promised; seven
transitions were re-signatured.

Two gaps found by probing before hand-back: an unbounded operation id (now held
to the frozen opaque-id grammar, REUSED rather than invented), and a lying clock
that could stamp a journal row (now refused before the journal is touched). One
raised rather than fixed: the settlement signature is unbounded caller text, and
a bound shorter than what the authority itself can produce would break a
legitimate settlement -- so it is measured and left for a ruling, naturally at
cut 5 where a participant first supplies it.

Seventeen mutations, ALL witnessed -- the first cut with no zeros. 28 regressions
added, the suite is 107 -> 135, `just gate` all green including the locked
installed-layout build.
Evidence: `evidence/cut3-2026-08-24.txt`.

## Cut 3 correction — 2026-08-24

Both findings closed. `check_opaque_id` is applied at all FOUR journal paths --
replay, settlement and both reads -- because I had stated the rule in one place
and called it from one site, which let settlement record an invalid identity as
retired while a claim under the same id refused on shape and never read the
retirement. And the race children no longer prepend the repository `src`: they
inherit the gate's own import path and report where they imported from, with the
parent asserting the origins agree -- measured, restoring the insertion makes the
installed gate fail four cases.

The settlement-signature cap stays UNINVENTED, as ruled: settlement compares the
exact signature the authority produced, and the contract has no system-wide text
bound.

Six mutations plus one combination. One is equivalent ALONE and load-bearing in
combination, reported as such. The mutation harness reported three false zeros;
all were re-measured by hand and the hand numbers are what is recorded -- a false
zero is more dangerous than a false failure, because it gets written down as
"equivalent". Two regressions added (the one-path case REPLACED by a four-path
table), suite 135 -> 136, `just gate` all green including the installed stage.
Evidence: `evidence/cut3-correction-2026-08-24.txt`.

## Cut 4 outcome — 2026-08-24

Contract progression with the typed gate for an uncertified target, canonical
activity (named here because neither cut's list mentioned it), proposal
publication with all five digests, the four immutable attributable receipts in
order behind their configured capabilities, the policy generation validated
before the journal and riding the signature, integration with the ONE durable
refusal, and authorized close in both forms.

Every frozen-host correction ported with it: the undifferentiated digest, the
actorless receipts, the generation outside the signature, the blanket durable
flag, and the close with no actor. Plus cut 2's `install_gate` lesson applied to
`close` before anyone had to find it again.

One gap found by probing: a reused `receipt_id` left as `IntegrityError` -- a
fault -- where `publish` already refused the same collision for proposals.
Receipt identities are claimed once now.

Twenty-six mutations. Three zeros with three different answers: two were MISSING
COVERAGE (the approval check was shadowed by the review check, so three cases
mentioned the rule and none reached it), and one was REDUNDANT CODE, which I
removed rather than reported. 33 regressions added, the suite is 136 -> 169,
`just gate` all green including the installed stage.
Evidence: `evidence/cut4-2026-08-24.txt`.

## Cut 4 correction — 2026-08-24

Three P1 closed. `result_id` is a frozen opaque identity checked before the
journal AND stably bound to one digest and one full assignment, with consistent
reuse still permitted because the rule is about contradiction. The
`canonical_target` accessor validates the one policy value this authority reads
SEMANTICALLY -- a dict used to escape as a raw SQLite fault and an empty string
used to publish successfully, binding a proposal to no target -- and the refusal
covers publication and integration alike. And every cut-4 projection answers
with the nested four-part identity through ONE shared projector, including
`assignment_events`, which was rewritten to use it rather than keep its own copy.

The instructive part of the third finding: cut 2 had already corrected
`assignment_events`, and I then wrote four new projections the old way because I
ported each from the frozen host's shape rather than from the corrected shape
beside it -- in the same file I was editing.

Seven mutations, all witnessed; the shared projector fails twelve cases, which is
the argument for having one instead of five. Five regressions added, the suite is
169 -> 174, two existing cases updated rather than pinned, `just gate` all green
including the installed stage.
Evidence: `evidence/cut4-correction-2026-08-24.txt`.

## Cut 5 outcome — 2026-08-24 (the last cut)

Two faces. `Authority` is the TRUSTED BOOTSTRAP that creates, opens, configures,
reads and MINTS sessions; `Session` is the runtime boundary, bound at
construction to one participant, holding no path, no store and no way back. The
actor on every receipt and the claimant on every claim come from the BINDING, and
a supplied `actor` or `participant` is REFUSED rather than dropped -- the frozen
host dropped it silently, so a caller could believe it had been honoured.

The surface is 16 transitions and 16 reads in tables, written out rather than
derived, each entry naming its whole key set: an operand supplied and ignored is
one the caller believes it chose. Operands are taken ONCE as an owned copy and
the caller's object is never read again, which is the frozen host's
check-one-view-execute-another defect removed rather than documented. `close` is
deliberately not binding-checked -- §7 authorizes it by capability, and an
approver closing a Work somebody else is executing is the ordinary case.
`Authority.close` was renamed `dispose`, because `close` is the Baton verb that
terminalizes a Work and one name for both invites the wrong one.

The portable catalog is now COMPARED rather than cited: the frozen reference is
asserted present, its size re-measured rather than quoted, every frozen file
mapped to a named counterpart, and no obligation area allowed to vanish. What it
does not claim is stated in the file, because a green run on a name-matching
check is not evidence of a guard. Two areas failed first time and both were my
needle rather than the coverage.

Cut 3's raised settlement-signature question is now a NUMBER: a legitimate
100,000-character activity key yields a 100,185-character authority-produced
signature that settles correctly, so any cap below that would refuse the
settlement of an operation this authority committed. The ruling is unchanged and
now pinned by a case instead of remembered by a comment; the bound belongs on
durable text system-wide.

Thirteen mutations. TWO ZEROS WERE MY INSTRUMENT, not the code, and both were
rewritten until they expressed the defect (a `who` key no case supplies; a
threshold weakened below the actual value, which can never fail). One zero is
GENUINELY EQUIVALENT and reported as defence in depth with the reason: the
session's `own` is unobservable precisely because the exact-type rules hold, and
it is the guard that stays correct if one is ever relaxed. A clean gap probe is
reported as clean, with one read named for a reviewer to decide rather than
discover: a session may read `slot_holder` for any participant.

25 regressions added, the suite is 175 -> 200, `just gate` all green including
the installed stage. Nothing is absent any more.
Evidence: `evidence/cut5-2026-08-24.txt`.

## Cut 5 correction — 2026-08-24

Both findings closed, both reproduced to the character first. Every
caller-controlled rendering in the session goes through `name_of` now -- the
assignment's named participant, the session's own participant (a grammar with no
length is not a short string), and unknown operand names as a bounded SAMPLE plus
a count. The multi-name half is the worse half and the single-key probe does not
show it: 510 unexpected names of 100,000 characters each was a
~51,000,000-character refusal from a boundary that had already decided to refuse.
A third site, `__repr__`, was found by sweeping the module rather than by being
told.

The instructive part: cut 5's own evidence ASSERTED this bound held here, because
I checked the helper I was calling instead of the message I was writing. That is
cut 4's projection defect one cut later.

"Exactly one operand document" is now exactly one. The generated method takes
`*documents`, so zero, an explicit `None` and several are each the one-document
rule saying so, instead of a silent substitution and a raw `TypeError`. The case
that called explicit `None` "a legitimate operand document for nothing" is
updated as specifically authorized -- that sentence was the defect written down
as a rule.

RAISED, NOT SILENTLY FIXED: an AST sweep of every `Refusal` interpolation in the
package found the same unbounded rendering at cut 1-4 sites, measured at
1,000,030 and 1,000,118 characters. Those files are signed off and the boundary
says correct cut 5 only, so the measurements are reported for a ruling. The root
cause is the single question already carried twice -- durable text has no
system-wide bound.

Ten mutations, all witnessed, and EVERY NUMBER ATTRIBUTED TO NAMED CASES after
the harness reported one false NON-ZERO from a stripped environment. Cut 3
taught that a false zero gets written down as "equivalent"; this is the mirror --
a false non-zero gets written down as "witnessed". Five regressions added, the
suite is 200 -> 205, `just gate` all green including the installed stage.
Evidence: `evidence/cut5-correction-2026-08-24.txt`.

## Authority-wide diagnostic audit — 2026-08-24

RULED IN-WORK, overruling my judgement, and the reviewer was right: earlier cut
sign-off is not an exemption from a still-live package invariant when later
evidence exposes a contradiction. A signed-off cut says nobody had found a
defect, not that none is there.

116 `Refusal` interpolations enumerated by AST walk across five modules; 26
corrected -- 13 in `core.py`, 12 in `store.py`, 1 in `identity.py` -- covering the
Work identity, participant, assignment, contract, gate, frozen result, receipt
and store-path families.

`name_of` ITSELF had the defect it exists to prevent: it bounded a rejected
string and rendered a rejected value's TYPE NAME raw, so a class named with
200,000 characters produced a 200,000-character diagnostic from the one helper
whose job is safe description. That is the second time the bounding helper has
been the unbounded path -- the integer finding was the first. The sixty-character
rule now lives in one place, `_shown`, and `type_name_of` gives the type-rule
messages a bounded way to say so.

THE REAL FIX IS THAT THE RULE IS NOW CHECKED. `EveryDiagnosticIsBoundedByTheRule`
walks the package AST and requires every interpolated value to be a bounded
rendering or one of fourteen named package-owned expressions, so a new raw
interpolation fails the gate rather than waiting for a third review. Its own
vacuous-pass modes are covered, and its blind spot -- helpers that BUILD text for
a refusal -- is named and measured rather than left implicit.

Twenty mutations, all witnessed. FOUR STARTED AS ZEROS AND ALL FOUR WERE MISSING
CASES that the AST check had already flagged, which is the useful division of
labour. A required phrase per family then exposed THREE families measuring the
wrong rule -- a case that accepts any refusal measures whichever one arrives.

Six regressions added, the suite is 207 -> 213. No durable-text operand cap was
introduced and the settlement ruling is unchanged: only the rendering of a
rejected value is bounded.
Evidence: `evidence/authority-wide-diagnostic-audit-2026-08-24.txt`.

## Label and classifier correction — 2026-08-24

The P2 is the finding and the P1 is its consequence. The audit I wrote to stop
unbounded diagnostics classified by UNPARSING an interpolation and matching a
string prefix, so it read `name_of(value) + value` as bounded, accepted any join
of anything, and accepted `what` because of how the variable was SPELLED. `what`
is package prose at every internal call site and caller text at every exported
one, so one entry written for the internal sites silently covered the ten
exported ones -- and a one-million-character label produced refusals of 1,000,014
to 1,000,139 characters through `own`, all six identity checks, `assignment_key`
and `normalize_assignment`.

A rule nothing checks holds wherever somebody happened to look. The sharper
version: A CHECK THAT MATCHES SPELLING INSTEAD OF ORIGIN IS ANOTHER PLACE FOR
SOMEBODY TO HAVE LOOKED ONCE.

`label_of` bounds the label once at the boundary of every function that accepts
one -- ten in identity, one in store, four in core -- and THE BOUND IS MEASURED:
binding at the sixty-character value limit truncated this package's own longest
label mid-word and took the member name with it, so twelve publication cases
stopped saying which digest was missing. That is the settlement-signature lesson
again, and a case now measures the longest label plus one rendered member.

A mutation with no witness found a third thing: a non-text label was returned raw
and then interpolated, and `f"{what}"` CALLS `__str__` -- so a caller supplying a
hostile label could replace a decided refusal with an exception of its own
choosing. Named by type now, with a case whose label raises from `__str__`,
`__repr__` and `__format__`.

The classifier proves node shapes and origins: one whole bounding call, a join
only when its source is package-owned, constants proved BY FIXPOINT across the
package, locals proved by assignment along the scope chain, and a named-site
table keyed by module, function and expression whose non-travel is enforced with
fabricated findings rather than described. It also attributed each closure's
refusals twice; it descends with a scope stack now.

Twelve mutations, all witnessed. Two began as zeros: one was my own ill-formed
mutation, and one was the missing hostile-label case. Six regressions added, the
suite is 215 -> 221, `just gate` green from source and from the installed wheel.
Evidence: `evidence/label-and-classifier-correction-2026-08-24.txt`.

## Label encoding and origin proof — 2026-08-24

Both closed, both reproduced first. `label_of` proved the label was an exact
`str` -- which makes it safe to READ -- and then returned it, so a lone surrogate
turned an ordinary refusal into a `UnicodeEncodeError` at whatever logged it.
That is the same failure `name_of` uses `ascii` to prevent for a rejected VALUE,
not carried across to the parallel boundary for a rejected LABEL: two rules that
are the same rule, applied in one of the two places.

The analyzer proved four things the AST does not say -- package-global constant
spellings, locals collected across nested scopes, a name proved by ANY safe
assignment regardless of later or branching raw ones, and exceptions keyed by a
short function name that many nested `body` closures share. Constants are per
module with shadowing decided by COUNTING bindings; locals stay in their own
scope and are proved only when every binding of them is a top-level bounding
call that dominates the use; each site carries its dotted lexical path; and an
exception covers the number of sites it declares, because a spelling has no
count.

Seven further shapes the analyzer could have guessed at are now fabricated and
refused as cases rather than described as intent.

Ten mutations, nine witnessed. One zero was a missing case -- nothing pinned that
an ordinary label survives unquoted -- and one is a MEASURED EQUIVALENCE reported
as such: the scope restriction is redundant given the binding rule, and both stay
because either alone is unsound if the other is relaxed. Three regressions added,
the suite is 224 -> 227, `just gate` green from source and from the installed
wheel.
Evidence: `evidence/label-encoding-and-origin-proof-2026-08-24.txt`.
