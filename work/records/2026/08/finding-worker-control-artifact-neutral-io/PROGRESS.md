# Implementer progress — artifact-neutral worker-control I/O

Created 2026-08-26 by `baton.claude` on claiming W14251.

## Done under this claim

The canonical record the policy requires before implementation, and the
revalidation of the 2026-08-25 ruling against the current tree.

**What the revalidation confirmed.** The superseded acquisition and result
vocabulary lives in the control schema rather than in either SPEC — neither
prose file names those types, and neither names `output.json` at all. So this
revision's centre of gravity is the schema, its vectors and the conformance
cases, and the narrative edits follow them rather than lead.

**What it corrected.** The version-control object type is referenced by four
surfaces that belong to the proposal and integration items rather than to
worker-control's input/output, so the bounded revision cuts the PATH from the
input manifest to it and not the type. Removing it wholesale would delete
vocabulary this supersession did not supersede.

**What it found that this Job does not own.** The shipped manager already
exports acquisition-aware materialization in
`v12/python/src/baton_v12/worker_manager/workspaces.py`, which is precisely
what the ruling removes from the core manager. Revising the contract to forbid
it while the code still exports it would leave two live rules contradicting
each other. It is PLAN item 2 and it is a question rather than a blocker I may
resolve: this is a contract Job, and widening it to delete a shipped module is
not a call to make silently.

**And the finding that sets the shape of the rest.** The record's schema and
the one the v12 distribution ships as package data are BYTE IDENTICAL, and the
manager validates live manifests against the shipped copy. So the schema edit,
the vectors and the 1309-case suite are one pass rather than three: from the
moment the schema moves, a green distribution is what is being changed. That is
not a reason to narrow the assignment -- it is the reason items 3 and 5 were
merged in the plan rather than ordered.

## Item 3 built, measured, and reverted — 2026-08-26

I wrote the neutral schema revision and applied it to both copies: one generic
staged-input descriptor with an opaque consumption member and no acquisition
kind or URI, the two acquisition types removed, the result-kind enums replaced
by opaque ids, and a required `result_metadata` on the answered output because
the ruling's own commit-identifier example has nowhere else to go. 53
definitions become 51 and the copies stay byte-identical.

**Then it measured the thing I had recorded as a question nothing waits on, and
the question turned out to be load-bearing.** `workspaces.py` validates its
operands against the removed definitions BY NAME:

    ContractRefusal: a directory source names definition 'directorySource',
    which is not one of the frozen worker-control schema's own definitions

So there is no version of this revision that lands green while that module
stands. About sixty further failures in `test_output` and `test_manifest_rules`
are the vectors and fixtures, which are this Job's own item 5; the workspaces
failures are not — they are a module this Job does not own, refusing because
the contract it reads no longer says what it reads.

**Escalated to a blocking obligation rather than resolved by choosing.** The
two ways forward are different Jobs: delete a shipped module and its suite from
a green distribution, or land a contract that forbids what the shipped manager
exports. The second is what `AGENTS.md` forbids; the first is a widening this
implementer may not grant itself.

**And the tree is back green.** Both schema copies were restored from the
committed bytes — read through the repository's own read-only history view,
written with a file copy, and no repository state was mutated — then
re-measured: `test_workspaces`, `test_output`, `test_manifest_rules`,
`test_secrets`, 228 tests, OK. A blocked Work that also left a red
distribution behind would make the block somebody else's problem twice.

The revision itself is not lost: `evidence/revise_schema.py` reproduces it and
`evidence/schema-patch-2026-08-26.diff` is what it produced.

## Not implemented

No SPEC, vector or conformance file has been edited, and both schema copies are
at their committed bytes.

## State

**BLOCKED on PLAN item 2**, with the claim released by the blocking request
rather than held while somebody else answers. No repository state was mutated.


## Unblocked and landed — items 3 and 5, 2026-08-26

W15232 closed satisfying, so the gate this Work was blocked on since I raised
it is gone. Revalidated first rather than trusting the preserved patch: both
schema copies were still byte-identical at their committed bytes, and
`workspaces.py` now names the removed definitions only in historical prose —
nothing executable, which is exactly what W15232's sign-off claimed.

**The schema, in both copies.** `sourceDescriptor` is one generic staged-input
descriptor — name, destination, required, content manifest, and an OPAQUE
`consumption` member; the two acquisition types are gone; `gitObject` stays
because four of its six referents are the proposal and integration surfaces
this supersession did not supersede; the result-kind enums are opaque ids; and
`artifactOutput` carries `result_metadata`, because the ruling's own example —
a worker reporting a commit identifier as format-specific metadata — had
nowhere to go without it. 53 definitions become 51.

**The §12 source rules went with the members they read.** Two rules stood over
a source: a `uri` grammar check and rule 7's object-namespace comparison. Both
read members the neutral descriptor does not have. The rules ABOVE them stay,
because they are about staging rather than acquisition — names unique across
sources and outputs, destinations not overlapping.

`check_uri` is deliberately untouched. It still guards artifact locators and
`fixtures/uri-vectors.json` is still the authority for that grammar. What ended
is this manager reading a SOURCE's acquisition locator, not the grammar for
locators it still receives.

**The vectors and fixtures.** The published input-manifest vector carries the
neutral descriptor and is resealed; the result fixtures carry
`result_metadata`. The `durable-source-query-refused` invalid case is removed:
the rule it exercised — a durable source URI may not carry a query, because a
query is where a credential rides — was a property of acquisition-aware
sourcing, and the manager no longer receives a URI at all. **That protection
now belongs to whoever stages the input**, and it is recorded here rather than
quietly dropped.

Two focused cases went the same way, replaced by
`test_no_source_rule_reads_an_acquisition_member`, which asserts the absence
and re-asserts that the locator grammar is still applied to artifacts.

### A revalidation miss of my own: there are THREE copies, not two

I recorded "the two copies are byte-identical" and repeated it in three
handoffs. There is a third -- `v12/src/worker_manager/schema/` -- kept by the
retired Node proof, and `test_frozen` compares all three plus a RECORDED
DIGEST of the bytes.

The frozen gate caught it, which is the system working. But my own
revalidation stated a fact about how many copies exist and got the number
wrong, and every "both copies" sentence I wrote about this Work was true of
two out of three.

All three are synced now, and the recorded digest is updated with the previous
value kept beside it -- the schema is FROZEN, so moving its bytes has to be a
decision somebody can see rather than a drift a gate discovers.

## NOT done, and these are not small

**PLAN item 4 — the control record's `SPEC.md` prose.** It must name
`/input/input.json` and `/output/output.json`, the read-only and
writable-then-frozen roles, publication of `output.json` LAST, ephemeral space
as capacity rather than protocol, and preserve the superseded acquisition and
result types as explicitly dated supersession history.

**PLAN item 6 — the conformance contract.** `SPEC.md`,
`schema/conformance-1.0`, `cases.json` and `obligations.json`, for the same two
surfaces.

**PLAN item 7 — revalidating affected downstream Work**, W6633 at least, which
this Work blocks.

The executable half is done and the tree is honest about it; the narrative and
conformance halves are the remaining deliverable.

## State

**Awaiting independent review, with items 4, 6 and 7 outstanding.** No
repository state was mutated.


## Review corrections and the remaining items — 2026-08-26

The review was right on both defects and right that the Work was incomplete.
Items 4, 6 and 7 are done in this round, so the whole assignment is now
implemented rather than half of it.

### [P1] The revised canonical vector crashed its own contract model

`contract_model.py:_validate_input_manifest` still indexed `source["uri"]` and
branched on `source["type"]`, `source["object_format"]` and
`source["base_revision"]`, so the record's own canonical valid vector raised
`KeyError: 'uri'` the moment the schema moved.

**And my progress note claiming item 5 had landed was simply wrong.** I made
exactly this edit in the shipped `contracts/manifest.py`, measured that, and
then recorded the record-side half as done without running it. The two files
implement one rule and I revised one of them.

The same edit is now in the contract model: the two source rules are gone with
the members they read, the staging rules above them stay -- names unique,
destinations canonical and non-overlapping, all true of an already-staged tree
-- and `validate_uri` is untouched because it still guards artifact locators.
24 cases, all passing.

### [P1] A fourth tracked build copy still shipped the superseded contract

I recorded "there are THREE copies, not two" as my own revalidation miss one
round ago. The number was still wrong: `v12/python/build/` is tracked, and it
carries a fourth schema **and a fourth manager**.

`PYTHONPATH=build/lib` imported `directorySource` and `gitSource` from the
schema and `GitPort`, `materialize_git_source` and `materialize_directory_source`
from `workspaces.py` -- the exact acquisition-aware manager W15232 removed and
this Work exists to gate out. A tracked build shadow is importable by an
ordinary path, so it is a live account rather than a leftover.

Three files are synchronized, and they are precisely the ones this
supersession makes contradictory:

    contracts/schema/worker-control-1.0.schema.json
    contracts/manifest.py
    worker_manager/workspaces.py

Measured after: no superseded definition, no acquisition surface, 51
definitions.

**The shadow diverges in other ways and I did not touch those.** `documents.py`,
`worker_manager/__init__.py`, `oci.py`, `output.py` and `schema.py` differ, and
`intake.py`, `sealing.py` and `credentials.py` are absent entirely. Those belong
to W6628, W6629, W6632 and W6634, and syncing them here would drag one Work's
unreviewed implementation into a tracked path under another Work's claim. It is
reported rather than done.

**The underlying problem is not mine to decide either.** `build/lib` is a
side-effect of `pip install .` that somebody committed. Every Work that touches
the manager now has to remember to update a second copy of it, and this review
is the second time in two rounds that forgetting has been the defect. Whether
it should be tracked at all is a repository-policy question; I am raising it
rather than answering it, because untracking it is a mutating Git operation
this role does not perform.

## Item 4 — the control SPEC, done

`.../finding-worker-control-api-manifests/SPEC.md`. A dated supersession header
says plainly that this is a SUPERSESSION and not a clarification: documents that
satisfied the old §7 stop being conformant, because the vocabulary they used no
longer exists.

**§7 is rewritten around the two roles.** `/input/` read-only for the whole
runtime with `input.json`; `/output/` writable until quiescence then frozen,
with `output.json` published LAST and atomically. Both paths are constants of
the contract rather than operands, for the reason W14828 makes concrete: a path
a manifest can vary is a path a runtime can be pointed at wrongly.

New subsections state the four rules the ruling adds and the reasoning behind
each: staged-input descriptors with an OPAQUE `consumption` member; opaque
output types with no two declarations over one tree; result outputs with
`result_metadata` and publication-last; unresolved identifiers refused as
durable results; and private ephemeral space as CAPACITY with no standardized
path, stated explicitly because the obvious alternative -- a third standardized
path -- would be a third protocol artifact bought for an implementation's
convenience.

**§7.6 keeps the superseded vocabulary as dated history**, as the plan
required: the common source fields, both acquisition variants, the three closed
output kinds, why each went, and what did NOT go with them. The reasoning that
was superseded is how the next reader knows why the current rule is not the
obvious one.

**§3.3 and §12 rules 4 and 7 are narrowed rather than deleted.** The URI grammar
still governs artifact locators; the object-format rule still governs the §8.5
proposal and §8.6 integration surfaces where the version-control object type
still lives. Both narrowings name the protection that was lost with the member
it guarded -- a durable source URI could not carry a query BECAUSE a query is
where a credential rides, and that now belongs to whoever stages the input.

## Item 6 — the conformance contract, done

`.../finding-worker-runtime-conformance/`. This contract is mechanically gated:
the register and the matrix must agree in both directions, every obligation
must name its observable and all three verdicts, and a test asserts the exact
case count. So the revision is data plus prose plus counts, and all of it moves
together.

**The two acquisition cases are REMOVED rather than renamed.** A case that tests
a rule which no longer exists asserts nothing, and keeping it under a new name
would make the matrix claim coverage it does not have. That is the same
judgement I made about `durable-source-query-refused` in the vectors last round,
applied to the suite that certifies runtimes.

**Eight cases replace them**, one per rule the ruling introduces:

    A-manager-acquires-nothing                  no transport, no consumption read
    A-staged-tree-matches-its-manifest          generic integrity of a staged tree
    A-output-json-published-last                the ordering
    A-interrupted-publish-leaves-no-output-json the atomicity, driven by process-kill
    A-identifier-only-output-refused            a promise is not a durable result
    A-output-persists-past-the-runtime          persistent output workspaces
    A-ephemeral-not-exported-not-collected      capacity is not protocol
    A-ephemeral-exported-is-collected           and the other half of it
    A-frozen-output-chains-as-read-only-input   chaining, by content manifest

`A-input-readonly` is renamed `A-input-is-read-only` because it is now about a
standardized root rather than about a directory source.

**Obligations `A-01` and `A-02` are restated** over the staged-input contract
with new observables and verdicts; `A-03`, `A-07` and `A-08` re-cite the
sections that moved, and `A-08` moves to §8.5 because a change proposal is a
proposal-surface rule that this supersession did not touch. `A-10` through
`A-14` are new, each with its `observable`, all three verdicts and its cases.

The matrix is 118 cases (112 - 2 + 8) and the register 75 obligations. Every
count in the SPEC that describes the live suite moved with them -- the §7
matrix, the refusal count in §5.2, the profile split in §8.3, the two "107 of
110" illustrations and the evidence inventory in §10. The two dated 2026-08-22
amendment headers keep their historical numbers, because those describe what
was true then.

`test_conformance_model` **74 cases, OK**. Its fixture case had to be
repointed: ten assertions used `A-git-exact-base` as a generic control-success
case, and it no longer exists.

## Item 7 — W6633 revalidated, and the exact affected contract

W6633 (`work/records/2026/08/finding-v12-oci-reference-worker-image/`) is
blocked on this Work and its own eighth review already named why. Revalidated by
MEASURING `v12/worker/baton_worker.py` rather than by re-reading that review:

- the work request carries an inline `task` member (`OPERATIONS["work"]`);
- the execution posture requires `BATON_WORKER_ASSIGNMENT`,
  `BATON_WORKER_WORKSPACE` and `BATON_WORKER_OUTPUT` in its environment;
- the work reply returns `disposition`, `workspace` and `recap`;
- neither `/input/input.json` nor `/output/output.json` appears anywhere in the
  file.

**The affected contract, exactly.** Against the revision now pinned, W6633 must:

1. read its assignment from `/input/input.json` rather than from an inline
   `task` frame or an environment variable, treating `/input/` as read-only;
2. write declared outputs under `/output/` and publish `/output/output.json`
   LAST and atomically -- its presence under its final name is the completion
   signal, so no separate one is needed;
3. answer each declared output with its opaque `type`, `status`,
   content manifest, artifact reference and `result_metadata`, and never a
   `workspace` member -- the manager is artifact-neutral and a workspace path
   is a host fact;
4. treat private ephemeral space as capacity: nothing in it is a result until
   it is exported into a declared output path before quiescence; and
5. carry no acquisition semantics at all. Version-control conventions may ride
   inside the opaque `consumption` and `result_metadata` payloads; they are not
   worker-control vocabulary and the reference worker may not read them as such.

Three of the environment members it exposes -- `BATON_WORKER_ASSIGNMENT`,
`BATON_WORKER_WORKSPACE`, `BATON_WORKER_OUTPUT` -- become unnecessary rather
than merely renamed: with two fixed paths there is nothing left for them to
say. That is a surface removal rather than a rewrite, and it belongs to W6633.

**No other downstream Work is affected.** The gating edges into this Work are
W6633's; the proposal and integration surfaces that still use the
version-control object type are W5's later children and this revision left
their vocabulary intact, which is why `gitObject` stayed.

## State

**Awaiting independent re-review, with every PLAN item implemented.** No
repository state was mutated.


## Second re-review — both [P1]s, and the revalidation I got wrong

### [P1] The worker-authored `output.json` required manager-only facts

This is the sharpest finding on this Work and it is right. §8.4 identified
`/output/output.json` with `baton.worker-manifest/result`, whose schema
requires `freeze_operation`, `manager_observed_at` and custody artifact
references. None of those exists until after the worker is quiescent. **So the
contract told the worker to publish last a document the worker cannot author**,
and my own conformance cases encoded the opposite owner while my W6633 handoff
encoded the first one. An unimplementable cycle, exactly as named.

**It is a SEPARATION, not a supersession, and that is worth stating.** I
re-read the pinned ruling rather than assuming: it says the worker "writes
every durable result below `output/` and publishes `output.json` last", AND it
says that after quiescence the manager "freeze[s] or snapshot[s] the declared
output, compute[s] generic integrity evidence, and bind[s] the frozen tree to
the assignment generation". Those are two acts by two parties. Reading them as
one document is what created the cycle; reading them as two makes both
sentences true at once, and needs no ruling to overturn.

| | `/output/output.json` | the frozen-result receipt |
| --- | --- | --- |
| schema | `baton.worker-manifest/completion` | `baton.worker-manifest/result` |
| author | the WORKER | the MANAGER |
| when | last, before quiescence | after quiescence, at freeze |
| where | inside `/output/` | manager custody, never `/output/` |

**The schema gains `workerOutput` and `completionManifest`** — name, opaque
type, the DECLARED RELATIVE PATH (which the manager-side `artifactOutput` does
not carry, because by then a locator says where), status, content manifest,
opaque `result_metadata`. It carries no freeze operation, no manager
observation and no artifact reference, and each absence has one reason: the
worker cannot know it yet.

`resultManifest` gains ONE OPTIONAL member, `completion_manifest_digest`,
naming the worker envelope the manager validated. Optional rather than
required, deliberately: the vocabulary has to exist before W6633's worker can
publish an envelope and W6634's sealing can bind one, and neither is this
Work's to change. Making it required today would break a green distribution
for a member nothing yet produces.

51 definitions become 53, so the frozen digest moves again and is recorded with
its predecessor beside it, in all four copies.

**The conformance cases carried the defect too.** Three family-A cases were
driven by a manager `output.freeze`, which made the manager the publisher. They
are driven by the worker now, and `A-15` with
`A-manager-receipt-is-not-the-worker-envelope` covers the split itself —
because "two documents with two authors" is a rule a suite can observe, and an
unobservable rule is prose. 119 cases, 76 obligations, and every live count in
that SPEC moved with them.

### [P1] Input and output paths were compared in one root

`/input/repo` and `/output/repo` are disjoint, so equal or nested RELATIVE
spellings across the two roles cannot alias. The rule is unchanged and still
load-bearing — two staged inputs over one tree deliver the same material twice,
and one declared output inside another has the worker writing into a tree the
seal also describes. **What changed is the set each comparison ranges over.**

Corrected in `contracts/manifest.py`, in the record's `contract_model.py`, and
in §12 rule 3. Names stay unique across BOTH, and that is deliberately a
different rule: a name is how one manifest's declarations are told apart, and
two roles sharing one is ambiguous wherever the name is used.

**The pre-existing case and its rationale needed the same correction**, as the
review said. It nested a declared output inside a source destination and called
that aliasing on the old shared-workspace model — asserting a rule the contract
no longer has. It now drives overlap WITHIN each role, and the invalid vector
`manifest-overlapping-input-and-output` became
`manifest-overlapping-outputs-in-one-root`.

### The revalidation I got wrong

I wrote "No other downstream Work is affected". That was false, and the review
is right that W6634 is directly affected. I checked the gating EDGES and called
that a revalidation; the actual question is which Work implements a surface
this contract describes, and W6634 implements the manager side of exactly this
publication boundary.

**W6634, revalidated by measurement.** `sealing.py` publishes `sealed.json`
under `<home>/custody/<attempt-id>/`, with schema
`baton.worker-manifest/result`, atomically, after every declared output is
staged and frozen. Under the split that is **correct as built**: it is the
MANAGER's receipt, in manager custody, outside `/output/`. Two obligations
follow and neither is a defect in what it has:

1. it should carry `completion_manifest_digest` once a worker publishes an
   envelope for it to name; and
2. nothing in the manager yet READS `/output/output.json` — measured: the
   string appears nowhere in `worker_manager/`. Validating the worker envelope
   before freezing is a manager duty this contract now states and W6634 does
   not yet perform.

**W6633, restated under the split.** Its worker publishes
`baton.worker-manifest/completion` at `/output/output.json` — NOT the
frozen-result manifest, which the earlier revalidation wrongly implied. The
other four obligations recorded last round stand unchanged.

### Verification

Focused shipped gate 223 cases including the review's additive two-root
regression. The record's contract model 24, the conformance model 74. All four
schema copies byte-identical with the new digest recorded.

### And a note on what this round did NOT touch

`tests.manager.test_credentials` gained five more additive regressions from
W6634's own review while this ran. They are that Work's, on that Work's files,
and it is with its reviewer.


## Third re-review — three landed, one escalated with its measurement

### [P1] The fixed manifest filenames were valid payload destinations

Correct. `/input/input.json` is the manager-authored input manifest and
`/output/output.json` is the worker-authored completion envelope, and both were
ordinary `relativePath` values a payload could take.

Reserved now in the shipped validator, in the record's contract model, and in
four invalid vectors. Two decisions inside it:

- **Each name is reserved in ITS OWN root and nowhere else.** An output called
  `input.json` sits under `/output/` and collides with nothing. Reserving both
  names in both roots would be forbidding a spelling rather than protecting a
  document.
- **Nesting counts.** `input.json/data` requires that name to be a DIRECTORY
  while the protocol document is a file, so it is the same collision. A rule
  comparing only equality would let the nested spelling through, which is why
  the review named it.

**And I did NOT put it in the schema, deliberately.** The review listed the
schema among the places, and I built it there first: `sourceDescriptor.
destination` and `outputDescriptor.path` gained a `not` on a reserved pattern.
Measured, that makes the review's own regression unsatisfiable — it asserts
`integrity.path`, and a schema refusal carries `integrity.schema` and cannot
name which rule failed — and it makes the semantic rule unreachable, because
this contract decides schema-first by design. So the rule lives where its
taxonomy is, and the schema bytes did not move for it. If the shape-level
reservation is wanted as well, that is a taxonomy decision to take explicitly
rather than a side effect of adding a pattern.

### [P1] The shipped validator accepted envelopes the model rejected

Also correct, and the sharper half of it is the reason: this is the validator
W6634 will call when it begins reading `/output/output.json`, so leaving the
rules in design evidence made the downstream instruction incomplete. That is
the same defect as writing a rule in prose.

`_check_completion_manifest` is in `contracts/manifest.py` and dispatched for
`baton.worker-manifest/completion`: unique names, non-overlapping paths, the
reserved output name, and a status that agrees with its integrity evidence in
both directions.

**The cross-document relations went somewhere else on purpose.** Exactly one
answer per declared output, no extras or omissions, exact `name`/`type`/`path`,
and no `missing-optional` answer for a required declaration — those are
comparisons against the INPUT manifest, and a function handed one document
cannot make them. They are §12 rule 15 now, and the conformance suite carries
four cases for them (`A-16`), because a rule needing two documents is exactly
the kind a suite can observe and a validator cannot.

### [P2] §7.1 still stated the superseded cross-root rule

Replaced. It said destinations cannot overlap "any output" while §12 rule 3
correctly said the two roots are never compared — two live normative answers
after the code correction, which is the thing a contract may least afford.
§7.1 now states the within-root rule and both reserved names.

## [P1] The receipt's binding — ESCALATED, with the number

The review is right and I am not going to argue the point: a permanently
optional link means a conforming manager can forever publish a receipt that
does not bind the worker claim it says it validated, and §8.4's
"implementation sequencing" explanation is an excuse rather than a rule.

**The rule I would write on a clean tree**, and I built it to find out what it
costs: a receipt whose `disposition` is `completed` MUST carry
`completion_manifest_digest`. Under this contract the worker's envelope IS the
completion signal, so a `completed` receipt naming none claims a completion
nothing signalled. The other three dispositions may omit it, and that is not an
accommodation either — `unable`, `plan-rejected` and `cancelled` are exactly
the endings where the worker may have died before publishing, and requiring an
envelope there would require the worker to have succeeded in order to be
recorded as having failed.

**Measured: it refuses 96 cases across three other Works' suites.**

    tests/manager/test_intake.py         58   W6629
    tests/manager/test_output.py         34   W6628
    tests/manager/test_credentials.py     2   W6634

Every one is a fixture that predates the split and declares `completed` without
an envelope digest. None of those files is this Work's, and W6628 and W6629 are
CLOSED — there is no active claim to hand the correction to.

**I also tried the review's second option and it is not reachable inside 1.0.**
A versioned boundary was the obvious answer: minor 0 the legacy path, minor 1
the split's. But `$defs.version` pins `minor` to `const: 0`, so a 1.1 receipt
cannot be expressed at all without widening the version vocabulary — which is a
larger contract decision than this Work was given, and one that would let any
document claim a version nothing negotiates.

**So this is a decision I am asking for rather than taking.** The three ways
forward are different Works: require it and correct three other suites' fixtures
(96 cases, two of them in closed Work); widen `version` and define the minor-1
boundary; or accept the optional member with an explicit, dated statement that
it is a floor. The first is what I would choose. The tree is left GREEN with the
member optional, and `test_manifest_rules` pins both what the contract says
today and that the question is open, so the gap is visible rather than implied.

This is the same escalation shape as W15232: measure it, restore the tree, and
put the decision where it belongs rather than either weakening the contract or
breaking somebody else's green suite.

### Verification

Focused shipped gate **228 cases** including all three of the review's additive
regressions. The record's contract model 24 with four new invalid vectors, and
the conformance model 74 with the matrix at 123 cases and 77 obligations. All
four schema copies byte-identical; the recorded digest did not move, and the
comment in `test_frozen` says why for both halves.


## Fourth re-review — the escalation is settled, and the rule is landed

### [P1] A completed receipt must bind its completion envelope

The decision I asked for came back, and it went against my reluctance rather
than against my proposed rule: **the measured first correction, and do not
widen the version vocabulary to preserve the bypass.** That is right on both
counts, and the sentence that settles it is the reviewer's: *their Work
provenance does not make those fixtures a compatibility promise.*

I had treated 96 refusals in three other Works as a reason to escalate. The
count was real; the inference was not. A fixture that constructs the changed
frozen contract is migration cost, and calling it somebody else's territory
turned a contract question into a scheduling one.

**Landed.** Under 1.0 a `completed` frozen-result receipt MUST carry
`completion_manifest_digest`, in the schema across all four copies, in the
record's contract model, and in the vectors. `unable`, `plan-rejected` and
`cancelled` may omit it — those are the endings where the worker may have died
before publishing anything, and requiring an envelope there would require the
worker to have succeeded in order to be recorded as having failed. §8.4 also
states the rule the schema cannot: **whenever an envelope WAS validated, the
receipt binds it whatever the disposition became**, and a case pins that the
shape admits it on every disposition.

**The migration was 92 of 96 in ONE shared helper.** `OutputCase.result` in
`tests/manager/test_output.py` is imported by `test_intake`, so binding the
envelope there carried all of them. That is worth recording because it is the
answer to my own escalation: I reported a number without looking at whether it
was one change or ninety-six.

**And the number I reported was short.** The aggregate run turned up 57 more in
`test_boundary_inventory`, which builds its own sealed result rather than using
that helper — so my "96" was the cost of the four suites I happened to run, not
the cost of the change. One more fixture carried all 57. The lesson is the same
one twice in two rounds: I measured, reported the measurement as if it were the
whole, and it was the whole of what I looked at.

### The two comments the review named

Both were claims I should not have written.

- `test_manifest_rules`'s class said minor 1 was the stable boundary while
  `$defs.version` pins `minor` to `const: 0` — a rule described against a
  version the contract cannot express. It now states the 1.0 rule and records
  that the version boundary was proposed and refused, with the reason.
- `_check_completion_manifest` said W6634 "performs" the cross-document
  comparison. It has not implemented envelope intake — measured, nothing under
  `worker_manager/` reads `/output/output.json`. The comment states §12 rule 15
  as a downstream OBLIGATION and names `A-16` as what will observe it, rather
  than describing a future implementation as a present fact.

A comment that asserts something untrue is worse than no comment, because the
next reader has no reason to check it. Both of these would have read as settled.

### Verification

Focused shipped gate **230 cases**, including the negative the review required
kept: a completed receipt with no digest is refused, and the same receipt with
one is accepted, so `required` is demonstrably the keyword that refused it.
Three more cases cover the unfinished endings and the envelope bound on one.

The record's contract model 24, with a `resultManifest` rule of its own, one new
valid vector and one new invalid vector. The conformance model 74 at 123 cases
and 77 obligations. All four schema copies byte-identical; the recorded digest
moved with a comment naming both what moved it and what deliberately did not.


## Fifth re-review — a vacuous vector of my own, and a duplicated rule

### [P1] The invalid vector did not test what it named

Patching `completion_manifest_digest` to `null` leaves the member PRESENT, so
the conditional `required` succeeded and the branch refused a TYPE instead. The
vector passed anyway because its expected text was the bare word `required` and
the harness flattens every error from the top-level `oneOf` over all document
kinds — 112 messages containing that word, from branches with nothing to do
with a result receipt.

**This is the vacuous-probe shape, and I am the one who has been correcting it
all campaign.** I wrote a `null` patch because the patch language has no
deletion syntax, told myself it was "absent enough", and then let a
one-word expectation stand in for the rule. The measurement I did not do is the
one I keep insisting on: nothing checked that the vector reached the branch it
names.

The reviewer's route is the one taken, and it is better than inventing deletion
syntax. There is now a valid vector for a receipt that LEGITIMATELY has no
envelope — an `unable` ending, where the worker may have died before publishing
— and the invalid one derives from it by changing exactly one member,
`disposition`, to `completed`. The expectation is the exact diagnostic,
`'completion_manifest_digest' is a required property`, rather than a word any
branch can produce.

Measured: restoring the `null` patch and the one-word expectation fails the
review's own additive regression.

### [P2] The model duplicated a rule the schema owns

`contract_model.py` says at the top that it models only the invariants JSON
Schema CANNOT express, and I then wrote `_validate_result_manifest` repeating
the conditional requirement the frozen schema already carries. Under a
schema-first harness that branch could never be the owner of a missing-member
refusal — the schema had already refused the document — so it was one rule
stated twice, unreachable by construction, and the kind of copy that later
drifts from the original.

Removed, with a comment where it was saying what it was and why the part that
genuinely cannot be expressed locally stays elsewhere: an envelope that WAS
validated is bound whatever the disposition became. That is a fact about an
act rather than about the document, so it lives in §8.4, is observable in
conformance, and is W6634's to satisfy.

### Verification

The record's contract model **25 cases** including the review's additive
regression, which now passes because the vector reaches its rule rather than
because a word matched. The shipped focused gate 322 across the frozen,
manifest-rule, output, secret, workspace, intake and sealing suites. The
conformance model 74 at 123 cases and 77 obligations. No schema bytes moved
this round.

