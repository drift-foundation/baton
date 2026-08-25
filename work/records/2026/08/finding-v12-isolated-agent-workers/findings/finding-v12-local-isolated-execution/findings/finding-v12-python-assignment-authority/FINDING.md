# Finding: build the Python v12 assignment authority

Work `W2845`. This M2 prerequisite replaces the frozen host-side Node authority with the
trusted Python authority required by the Python Worker Manager. It is
independently scheduled and linked to W4 by an authoritative dependency edge;
this nested dossier preserves its causal M2 context without pretending that
repository layout is ledger containment.

## Confirmed boundary

The v12 trusted host uses Python 3.13 or newer. Authority and Worker Manager
ship in the one self-contained `v12/python/` distribution, while remaining
separate modules, Work, SQLite files, connections, schemas and transactions.
Packaging them together does not grant the manager authority ownership.

The authority exclusively owns authoritative Work identity, assignment
generation, Handler/claim state, typed gates, operation replay and the minting
of participant-bound sessions. A session exposes only the operations and
projections its participant may use. It never exposes bootstrap, configuration,
the authority store path, a database handle, SQL or a way to mint another
participant's session.

The existing `v12/src/authority/` Node implementation and its reviewed tests
are executable-reference evidence. The Python implementation carries forward
portable behavior and vectors; trusted host runtime code neither imports nor
bridges through the Node implementation.

## Package and dependency contract

`v12/python/pyproject.toml` declares Python `>=3.13`, package metadata and
direct dependencies. `v12/python/requirements.lock` pins the complete resolved
environment with hashes. Product schema copies are package data and tests
prove byte identity with their canonical dossier assets. A genuine pinned
Draft 2020-12 validator is used where the authority consumes a frozen schema;
ambient packages and handwritten partial substitutes are refused.

## Acceptance

- Persist the authority UUID once and refuse reassignment or store adoption.
- Allocate assignment generations and claim/settlement state transactionally,
  with exact retry versus collision and compare-and-swap behavior.
- Preserve the full assignment identity: authority UUID, Work ID, participant
  and generation. Local selectors and participant names alone are not durable
  identities.
- Mint a participant-bound Python session capability that implements the
  projections and transitions required by the manager without exposing the
  authority implementation or store.
- Keep authority and manager databases independent and prove that neither can
  open, mutate or transact through the other's store.
- Cover restart, concurrency, stale generation, replay, cancellation fencing,
  gate transitions and cross-participant refusal with portable Python tests.
- Return for independent review before W4 begins implementation against the
  real session capability.

The implementer creates and exclusively owns `PROGRESS.md` after successfully
claiming the corresponding Work.

## Reviewer implementation revalidation — 2026-08-24

**Confirmed:** W151 `1-ruled`, the signed-off W2928 authority and the new
Python-host ruling agree on the authority-owned state machine. The current
design model passes 64/64 (the older dossier count of 61 is stale), and the
frozen Node authority has 75 named reference cases. W4 is already blocked on
this Work in the authoritative ledger.

**Proposed Python boundary, accepted for implementation handoff:** use exact
built-in JSON data and frozen snake-case identity shapes; separate non-adopting
`create`/`open`; mark the Python authority store kind so it cannot accept the
Node, v11, manager or arbitrary SQLite schema; use explicit `BEGIN IMMEDIATE`
transactions and savepoint-scoped ordinary versus durable refusals; export
trusted bootstrap and a minted participant-bound runtime session as separate
faces; and port behavior by contract obligation rather than JavaScript syntax.

The authority slice itself is standard-library-only and consumes no frozen
JSON Schema, so it does not prematurely add W4's validator dependency. It may
establish the shared Python package and lock/build boundary; W4 later adds its
approved pinned Draft 2020-12 validator. Tests use standard-library
`unittest`, SQLite and real spawned-process races.

**Python trust clarification:** private attributes and module names are not a
sandbox. The supported/exported session API and deployment wiring expose no
bootstrap, store, path, SQL or session mint, while the filesystem/process
boundary withholds those capabilities. Tests must prove that exact boundary,
not claim that a trusted in-process Python module cannot use reflection.

Implementation proceeds in five bounded review cuts. Exact modules, public
methods, transaction semantics and portable test catalog are recorded in
`evidence/python-authority-boundary-2026-08-24.txt`; handoff review:
`review-2026-08-24T04-20-07Z.md`.

## Final-boundary review resolutions — 2026-08-24

**Confirmed:** a participant-bound session may read `slot_holder` for another
participant. The value is the deployment-wide scheduler-capacity projection,
not secret material and not authority to act as that participant; sessions
already read cross-deployment Work/Handler projections. Claimant, receipt actor
and assignment-owned mutation identity remain exclusively session-bound.

**Confirmed:** settlement receives no local signature-length cap. A legitimate
authority operation can produce a 100,185-character signature, and the same
authority must be able to settle it exactly. A durable-text limit must be
system-wide at the ingress that admitted the text, not a shorter settlement
rule that strands an accepted operation.

## Final diagnostic ruling — 2026-08-24

**Confirmed:** the Cut 5 Session corrections close both findings from the first
final review. Focused cases pass 5/5, and the complete source and installed-wheel
gate passes 205/205 before the next reviewer regressions are added.

**Confirmed:** the bounded-diagnostic rule is authority-package-wide, including
the trusted bootstrap and Core paths implemented in earlier cuts. A valid
million-character duplicate Work id produces a 1,000,030-character Refusal, and
a valid million-character Session participant lacking a receipt capability
produces a 1,000,126-character Refusal. Both are rejected-value diagnostics and
contradict `authority/errors.py`'s existing rule that caller-controlled text in
a message is bounded by the rule rather than by the operand. Earlier cut
sign-off does not supersede that invariant; the authority must audit every
Refusal construction rather than repair only the two measured sites.

**Confirmed distinction:** accepted durable operands remain exact and
untruncated. In particular, settlement still has no local signature cap and
must compare a legitimate long authority-produced signature exactly. This
ruling bounds only diagnostic renderings of rejected values; it creates no
system-wide durable-text limit.

Independent re-review and red regressions:
`review-2026-08-24T06-51-18Z.md` and
`evidence/re-review-cut5-correction-2026-08-24.txt`.

## Diagnostic-audit re-review — 2026-08-24

**Confirmed:** the authority-wide audit closes the two prior public-face
reproductions, corrects 26 Core/store/identity renderings, bounds caller-
controlled type names in `name_of`, and preserves exact uncapped settlement of
accepted long signatures.

**Observed:** the audit globally allow-lists the expression `what` as package-
owned prose, but ten exported identity helpers let their caller supply that
label. A million-character label still produces million-character authority
Refusals. The source classifier also accepts composite `name_of(value) + value`
and arbitrary `join` expressions because it matches the unparsed expression's
prefix rather than proving the whole AST node bounded. Thus the standing guard
reports clean over both a live defect and unsafe future forms.

**Confirmed correction boundary:** bound labels at the exported helper
boundary, remove global trust in variable spelling, and classify only exact safe
AST shapes whose whole value is proved bounded. This remains diagnostic-only:
no operand cap and no settlement change. Independent re-review:
`review-2026-08-24T07-10-44Z.md`; evidence:
`evidence/re-review-authority-wide-diagnostic-audit-2026-08-24.txt`.

## Label/classifier re-review — 2026-08-24

**Confirmed:** caller-supplied labels are length-bounded without truncating the
package's legitimate digest labels, non-text labels run no caller behavior, and
the expression classifier rejects the composite forms named by the prior
review. Source and installed-wheel gates pass 221/221.

**Observed:** an exact string label containing a lone surrogate remains raw in
the Refusal and raises `UnicodeEncodeError` at the first log/wire encoding. The
origin analyzer also conflates same-named constants across modules, collects
nested-function assignments as enclosing locals, ignores later/branching unsafe
reassignments, and lets a named-site exception travel between distinct nested
functions sharing the short name `body`.

**Confirmed correction boundary:** labels must be encodable as well as inert and
bounded. Origin proof must respect module/import shadowing, lexical scope,
reaching definitions and unique lexical site identity; a conservative refusal
to prove is safer than a clean false positive. No operand or settlement rule
changes. Independent re-review: `review-2026-08-24T07-25-10Z.md`; evidence:
`evidence/re-review-label-and-classifier-correction-2026-08-24.txt`.

## Final independent sign-off — 2026-08-24

**Confirmed:** the label-encoding and origin-proof correction closes the final
three reviewer regressions. Labels are bounded, inert and encodable while
ordinary prose remains unchanged. The analyzer proves whole expression shape,
module/import origin and lexical scope, conservatively refuses control flow it
does not model, and pins the dotted lexical paths of its counted named-site
exceptions.

**Verified:** the complete source suite and the locked installed-wheel suite
both pass 227/227 on Python 3.13.7. The package still exports 20 names, the
long-signature settlement case passes unchanged, and the frozen Node authority
is untouched.

All acceptance items are satisfied. Final review:
`review-2026-08-24T07-33-54Z.md`; evidence:
`evidence/final-signoff-2026-08-24.txt`. W2845 closes satisfying and releases
the existing dependency gate on W4.
