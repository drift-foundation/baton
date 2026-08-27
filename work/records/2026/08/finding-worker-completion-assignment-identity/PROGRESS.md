# Implementer progress

## 2026-08-26 — PLAN item 3, contract alignment

Evidence: `evidence/w19784-2026-08-26-item3-contract-alignment.txt`.
No repository state was mutated.

### What the approved ruling turned out to need

The approver pinned `/input/assignment.json` as the delivery. Working through
the frozen assets, the shape of the change is narrower than the finding's
framing suggests, and that is worth stating plainly because it decides what
"align the schema copies" meant:

**No frozen schema copy changed, and none should have.** `assignmentManifest`
has been in `worker-control-1.0` since it was frozen. W19784 adds a PATH and a
LIFECYCLE, not a document. All four copies remain byte-identical and the
recorded digest in `tests/manager/test_frozen.py`
(`22caa60a…a3301bc`) is untouched — verified by hashing every copy in the tree,
not by assuming.

That is also why the amendment is recorded as a **defect fix** rather than a
supersession: no document that satisfied the old §7 text stops being
conformant, because under that text no conformant execution container could be
built at all.

### Delivered

**The shipped validator** — `v12/python/src/baton_v12/contracts/manifest.py`:

- `_RESERVED` became per-role tuples, so `/input/` reserves both `input.json`
  and `assignment.json`, and `_check_reserved` ranges over every name in the
  role rather than one. Nesting still counts.
- new public `check_input_pair(input_manifest, assignment_manifest)`, exported
  from `contracts/__init__.py`, holding the two `/input/` documents against
  each other: same Work, the assignment minted against that exact input
  manifest digest, and equal `policy_digest` / `runtime_profile_digest`.

**Driven cases** — `tests/manager/test_manifest_rules.py`,
`TheTwoInputDocumentsAreOnePair`: the canonical pair accepted with the
generation reaching the caller; every binding spoiled one at a time from a
document that is proved structurally valid ALONE first, so the refusal under
test is the relation and not the shape; the input side repinned; each
document refused as a stand-in for the other; both reserved names in both
spellings; and an output legitimately named `assignment.json` under `/output/`
accepted, because the reservation is per-root.

**The record's executable model** —
`finding-worker-control-api-manifests/evidence/contract_model.py`: the same
reservation and a `validate_input_pair`, with the reasoning for why a
two-document rule lives in this module rather than in `validate_manifest`.

**Vectors** — that record's `vectors.json` gained a canonical
`assignment-manifest-delivered-beside-its-input` minted against the published
input vector, two invalid vectors for the new reserved name, and a new
`input_pairs` section, because a two-document rule cannot be expressed in a
harness that drives one document through one validator. The addition is
additive: the existing `valid`/`invalid` consumers look their vectors up by
name and are untouched.

**Normative text** — that record's `SPEC.md`: a new dated amendment at the
head; §7.0 rewritten to three protocol documents in two filesystem roles with
the authors, the lifecycle and the consent posture; §7.1's reserved-name rules;
§8.1 on why "no generation before claim" is load-bearing; §8.2 on the new
delivery path; §8.7 on where "the exact `assignment_ref`" now comes from; §12
rule 3 extended and new §12 rule 16.

**Conformance** — `finding-worker-runtime-conformance`: obligations `A-17`
(the delivery, its mount mode, the pair bindings, consent visibility) and
`A-18` (the identity actually reaching the envelope and the manager's
comparison before custody), and nine cases covering delivery, missing,
malformed, wrong-input, wrong-Work, consent-visibility, the positive copy,
stale-generation and wrong-attempt. Register 77 → **79**, matrix 123 → **132**
(28 success / 54 refusal / 50 invariant), `local-oci` core 122 → **131**. Every
live count in that SPEC updated and read back from the data.

### Two rules the ruling names that were deliberately NOT written

Both are recorded in `§12 rule 16` and in the code, as discharged rather than
dropped:

1. **`assignment_contract` is not compared across the pair.** The reviewer
   recommendation lists it among the cross-checks. The frozen schema pins it to
   `const: "v12-assignment-1"` on BOTH documents, so two structurally valid
   manifests cannot disagree and the branch could never execute — a guard no
   removal can measure, which is the shape this campaign has been corrected for
   before. A version that widened the vocabulary moves the comparison into the
   rule.
2. **The generation is not compared across the pair.** The input manifest has
   none; that asymmetry IS the defect. The assignment side is the sole source,
   and demanding agreement would be unsatisfiable by construction. A case pins
   that moving the generation alone is not a pair error.

### Measurement

Every guard added on both sides was measured by removing it and observing which
named cases refuse the removal. Ten mutations, no vacuous guard, and both
sources restored byte-identical afterwards. Details in the evidence file.

### Two things found, not introduced

1. **Conformance SPEC family-table drift.** Row **E** read 13 while
   `cases.json` held 15; W4487's re-review added
   `E-operation-signature-covers-kind` and
   `E-operation-signature-mismatch-refused` and never touched the prose. The
   row is corrected and the correction is recorded in that section, which
   already warned that a matrix duplicated in prose will disagree with itself.

2. **`v12/test/worker_manager_contracts.test.mjs` is RED at 55/60, and it is
   not this Work's.** All five failures read a source's `uri` or
   `object_format` — members W14251's artifact-neutral ruling deleted — or look
   up an invalid vector W14251 renamed. Measured rather than asserted:
   reverting this Work's three vector additions leaves exactly the same five
   failures. The JS runtime was never migrated with the ruling. Recording it
   here rather than fixing it: it belongs to W14251's scope, not this
   assignment's, and it is not mine to close.

### Gates

- `tests.manager.test_manifest_rules` + `test_frozen` + `test_canonical` +
  `test_output` + `test_sealing` + `test_secrets` — **264 tests, OK**
- the contract record's `test_contract_model` — **31 tests, OK**
- the conformance record's `test_conformance_model` — **74 tests, OK**
- whitespace check over the working tree — clean

## 2026-08-26 — PLAN items 4 and 5, the delivery itself

Evidence: `evidence/w19784-2026-08-26-items45-delivery-and-suites.txt`.
No repository state was mutated.

### The worker (`v12/worker/baton_worker.py`)

The workaround the finding names is gone. `input_manifest()` used to read
`assignment_ref` out of `/input/input.json` — a member the frozen
`inputManifest` schema forbids — so the reader and the schema disagreed and
only a test-only fixture kept it standing.

Now: `_document(name)` reads one bounded manager-authored document;
`input_manifest()` takes the declarations and nothing else;
`assignment_manifest()` takes the identity and refuses an `assignment_ref`
that is not exactly the frozen three members, because this worker COPIES the
value and a wider or narrower one is either short of the generation the
envelope requires or something the worker would be inventing; `one_delivery()`
holds the pair (§12 rule 16). All of it runs BEFORE `agent.work`, so a
mis-composed container writes nothing at all.

### The manager (`worker_manager/workspaces.py`)

New `compose_input_root(inputs, input_manifest, assignment_manifest)`. It
performs §7.0's lifecycle rather than describing it: the pair is validated by
the shipped `check_input_pair` BEFORE anything is written, each document is
published atomically under its final name, each lands read-only on disk, and a
root that already holds either document is refused rather than repaired —
rewriting `input.json` under a claim made against it would change the evidence
the result is measured by.

**What did NOT change, and that is the finding.** W6634's
`_completion_envelope` already compared the envelope's `assignment_ref` with
the manager's owned assignment before touching custody. That comparison was
always right; what it lacked was a satisfiable other side, because no
conforming worker could author a matching value. It now has one, and I added
a comment saying so rather than a second check.

**What I did NOT build.** Nothing in the package calls `compose_input_root` —
for the same reason nothing calls its sibling `assignment_workspace`: the
launch sequencer that ties workspace allocation to `run_vector` has not been
assigned to any Work. Adding an orchestrator to give my own function a caller
would be building an unassigned slice, so I did not.

### Both worker suites

`tests/manager/test_worker_image.py`: the `staged()` fixture now delivers the
record's own input manifest and an assignment minted against it, replacing the
hand-written `{"assignment_ref": ..., "outputs": ...}` that hid the defect. A
new `TheAssignmentIdentityComesFromItsOwnDocument` carries eight cases —
the positive (run the whole path, read what landed in the durable document,
generation included), the input side not being the source, missing, malformed,
every mis-composed binding, an identity the worker would have to invent, a
delivery short a binding member, and consent seeing neither document.

`tests/manager/test_worker_container.py` — **the daemon-backed gate, which
W6633 left untouched and unrun.** It was at 29 of 31, and the two failures
were the only two cases that ask the built image to WORK: they sent a `task`
operand and read a `workspace` answer member, both removed by W14251, and
mounted nothing at all. So the artefact had never once been asked to do the
thing it exists for. `talk` now takes mounts, `roots()` builds a real host
`/input/` and `/output/`, and the suite runs the true two-root, two-document
delivery — plus a container-level negative for each way the delivery can be
wrong and a consent container proved to see neither document. **33 of 33.**

### Measurement

Twelve further mutations across the worker and the manager, each measured by
removal against the cases that name it — including the ORDERING guard (moving
`agent.work` above the pair check is caught by five cases). Two guards came
back vacuous on the first pass, `publication is atomic` and `the inputs root
is a directory this manager owns`; both are now driven by cases that observe
them (an interrupted write, and a root that is missing or is a file) rather
than deleted.

**A measurement-harness defect found and fixed.** The mutation runs rewrite one
file repeatedly inside a single filesystem timestamp tick, so CPython's
mtime-based bytecode cache could serve the PREVIOUS mutation — which reads
exactly like a guard that is not where the source says it is, and briefly did.
All four harnesses now drop the `__pycache__` with each write, and the earlier
contract-layer measurements were re-run under the fix and were unchanged.

### The two failures that remain, and why they are not mine

Measured, not assumed: reconstructing the pre-W19784 worker gave **9 failures
of 61** in `test_worker_image`. It is now **2 of 69**.

Both are one open contradiction inside W6633's slice:

1. `test_the_correlated_work_answer_names_outputs_only` requires the framed
   `work` answer to carry bounded output NAMES;
   `baton_worker.check_answer` explicitly EXEMPTS `outputs` from that rule and
   `handle` frames the whole published documents. One of the two is wrong and
   deciding which is W6633's call. My own migrated case deliberately asserts
   only what both readings agree on rather than quietly picking a winner.
2. `test_declared_output_limits_hold_before_completion_publication` requires a
   declaration's `constraints` to be enforced before publication, and the word
   `constraints` does not appear in `baton_worker.py` at all.

W6633 is with its reviewer with its own record of this. I did not fix either,
because both are implementation decisions in a slice I do not hold.

### Gates

- focused manager gate, 14 modules — **692 tests, 2 failures** (the two above)
- `test_worker_container`, daemon-backed — **33 tests, OK** (was 29 of 31)
- `test_workspaces` — **33 tests, OK**; `test_dependencies` — **21, OK**
- the contract record's `test_contract_model` — **31, OK**
- the conformance record's `test_conformance_model` — **74, OK**
- `test_boundary_inventory` — **93 tests, 6 failures**, the accepted
  long-standing baseline; 93 rather than 92 is the new witness. Three entries
  were added: the input root DELEGATED to `workspaces._real` with its own
  probe, and the two documents STATED as owned by `contracts.check_input_pair`.
  An intermediate run failed a SEVENTH case,
  `test_every_stated_owner_names_a_witness_that_exists` — a stated owner is a
  claim until something exercises it, and mine had none yet. That is the check
  doing its job; `test_the_input_pair_is_owned_by_the_contracts_own_composite`
  is the answer, and its third case is two structurally perfect documents that
  are not one delivery, which is exactly what the boundary layer cannot see.
  Verified by reading the failure diffs rather than the count: none of the six
  names a W19784 site.

### State

**Ready for independent review.** All five plan items are complete. No
repository state was mutated.

## 2026-08-27 — the review's three P0s and one P1

Evidence: `evidence/w19784-2026-08-27-review-corrections.txt`.
No repository state was mutated.

All four findings were correct. Two of them are the same mistake in two places,
and it is worth naming as one: **I proved a thing agreed with itself and called
that validation.** The worker compared the two documents' digest strings with
each other; the manager compared the two documents with each other. Neither
comparison can fail for a delivery that is internally consistent and wrong.

### [P0-1] The worker now validates both delivered documents

`_document` used to shallow-extract the members the worker wanted, so a false
self-digest or an extra top-level member — a second identity alias, which the
ruling rejected by name — reached the agent.

**The fix could not be a hand-typed member list.** That is a second copy of the
contract, and a second copy is a second thing to keep true. So the frozen
schema now travels with the image as DATA and `_definition` derives each closed
member set from it: a fifth byte-identical copy, gated by `test_frozen`, which
also asserts the recipe actually copies it and that the image carries no
contract it does not speak. `_closed_manifest` then proves three things —
every required member present, nothing else present, and the document's own
`manifest_digest` recomputed over its own canonical bytes.

**What this deliberately is not** is a JSON Schema implementation. The image
carries no validator library and must not grow one. What is proved is what a
mis-composed or edited delivery breaks and what this program can prove alone;
the manager proves the whole schema before it mounts, and the worker's derived
sets and the manager's validator are held to one document.

Two constants went with the change rather than beside it: `ASSIGNMENT_MEMBERS`
and the two manifest-schema strings were this program's own list of what a
document must carry and be, and keeping them would have been exactly the second
copy the derivation exists to avoid.

Covered through the built image as the finding asked — the daemon-backed suite
runs a container-level negative for each spoiling and compares the artefact's
own copy of the contract byte for byte. **35 of 35.** The review could not run
that gate; its managed turn had no Docker socket.

### [P0-2] The manager authenticates the root it exposes

`compose_input_root` gained **required** `assignment` and `runtime_attempt_id`
operands — the manager's own values, with no default, because a caller that
could omit them would be a caller that composes an unauthenticated root.

And the launch path is wired: new `authorize_input_root` reads the two
documents back **off disk** — what a runtime mounts is the disk, not a value
threaded down from whoever composed it — and holds them against three
manager-owned facts: the assignment the attempt activated, the runtime attempt
being started, and the input digest the attempt was claimed against.
`request_runtime_start` calls it before it journals the start operation.

**The requirement is derived, not optional**, and that distinction is the whole
design. `inputs=None` is reachable only when the attempt records no input
digest — meaning this manager has nothing a root could be bound to and no root
to expose. Every real delivery is offered and claimed against an input manifest
and records that digest, so from that moment a start without an authorized root
is refused. I considered a plain required operand and rejected it: it would
have forced ~80 lifecycle cases whose subject is not the root to construct one,
which is cost without coverage, and an *optional* operand would have been the
hole itself.

A shared `tests/manager/input_roots.py` builds roots for those suites **through
`compose_input_root`**, so a suite that got a root that way got one the
production boundary would accept. A fixture that wrote the two files directly
would be a second composer, and two parties disagreeing about one delivery is
the defect this Work started from.

### [P0-3] Conformance now certifies the identity at the right moment

The two negatives operated only at `output.freeze` — after the agent has run.
So a root nothing had authorized could be mounted, an agent could work against
it, and the suite called that conformant because the freeze refused afterwards.
`A-18` now states the identity as proved **twice**, and three cases carry the
pre-mount moment. The freeze cases stay as defence in depth, which is what they
always were and never the only line. Matrix 132 → **135**. `SPEC` §12 gained
**rule 17**: the pair rule is not an authorization, and the moment is normative.

### [P1] The gate can no longer run against stale bytecode

`v12/worker/` is rewritten in place by the mutation harnesses inside a single
filesystem timestamp tick, and CPython invalidates a `.pyc` by mtime **and
size** — both unchanged across two sources written that fast. The suite now
drops `v12/worker/__pycache__` **before** it imports the worker, so it cannot
be run against a stale cache by a caller who has never heard of the harnesses;
two cases pin the ordering and that the loaded module is the file on disk.

Proved by manufacturing the exact defect — bytecode cached for a mutated
worker, source restored with identical mtime and size — and confirming the
**ordinary command, no `-B`**, still reports the tree's result.

The transcript the review called out now carries a **retraction notice at its
head** naming which section is wrong and why. I had found this same defect
hours earlier while writing W6634's checkpoint addendum and corrected it
*there*; I did not go back and correct it *here*, which is how it reached the
reviewer. Finding a defect in one dossier and not sweeping the others it
touches is the gap, and it is mine.

### Measurement

Twelve guards, each measured by removal, each witnessed by named cases; all
three sources restored byte-identical. Two came back vacuous on the first pass
and are now **driven rather than deleted**: the schema-const check (a document
carrying exactly the input manifest's members while declaring itself something
else) and the read-back revalidation (a root edited after composition).

### Gates

- `test_worker_image` — **75 tests, 2 failures**, both W6633's own open
  contradiction, unchanged and independently owned. All four of the review's
  additive regressions pass.
- `test_worker_container` (daemon-backed) — **35 tests, OK**
- focused manager gate, 18 modules — **878 tests, 2 failures** (the two above)
- contract model **31, OK**; conformance model **74, OK**
- `test_boundary_inventory` — **93 tests, 6 failures**, the accepted baseline.
  An intermediate run showed ten: my own first-round probe and witness called
  `compose_input_root` without the new required operands. Fixed; verified by
  reading the diffs rather than the count.
- whitespace check — clean

### Still open, and still not mine

`test_worker_image`'s two failures are one contradiction inside W6633's slice —
`check_answer` exempts `outputs` from the bounded-text rule while a case
requires bounded names, and declared-output `constraints` are required before
publication while the word does not appear in `baton_worker.py`. W6633 is with
its reviewer.

## 2026-08-27 — the second review's P0: authorization and mount were two operations

Evidence: `evidence/w19784-2026-08-27-authorization-to-mount.txt`.
No repository state was mutated.

The finding is correct, and it is the same failure mode as the first review's
one layer further out. Last round I proved two documents agreed **with each
other** and called that authorization. This round I proved a **directory** —
that it named the live assignment, this attempt and the claimed input digest —
and then started a runtime whose mount plan was an entirely separate value.
`_mounts` checked containment and writability and said yes, because it is about
a different question: the sibling `workspace` is contained and readable too,
and `/inputs` is a target this manager never fixes.

**A proof about one value is not a proof about another.** Two boundaries that
never compare their operands are two boundaries that can both pass while the
container is wrong.

### Both halves, because neither subsumes the other

The finding offered a choice — carry the source across the seam **or** compare
with the adapter's immutable plan. I did both, and they answer at two different
moments:

- `attempts._plan_agrees` holds an adapter's **declared** plan to the proved
  root *before the start operation is journalled*, so a refusal leaves nothing
  to settle and nothing to reconcile. This cannot be the boundary: it reads an
  attribute an adapter may not have, and requiring it would make every narrow
  adapter declare a plan it does not own.
- the authenticated source **crosses the seam** as `input_root`, and
  `OciAdapter._mounts_the_authorized_root` requires it: exactly one bind, that
  exact source canonically, read-only, at the fixed `/input`. This cannot be
  the only line either — its refusal arrives after the manager has committed a
  start it now has to settle.

The split is stated at both sites rather than left to be inferred.

**Absence is decided too.** With no authorized root there is nothing a `/input`
bind could be, so one is refused rather than passed through. "The manager did
not say" is not a reason to expose an unproved directory at the path the worker
trusts.

### Proved at the argv, and at the artefact

The finding asked for an OCI vector case proving those exact bytes reach the
engine. `TheRootThatWasProvedIsTheRootThatIsMounted` reads the argv back —
`type=bind,source=.../inputs,target=/input,readonly=true`, and exactly one bind
on that path. Seven more cover each way a plan can disagree: the sibling
workspace, another target, writable, two binds, none at all, and one claimed
with nothing proved — each refused *before* the engine is reached.

And at the artefact, which the review could not run because its managed turn
had no Docker socket: a real container proved it cannot write the input root it
was given, and a real worker published the identity it read out of that exact
mount. **37 of 37.**

### Conformance saw none of this

`A-17` now states that the root authorized is the root mounted, and carries a
case that reads the engine's own argv. Matrix 135 -> **136**. `SPEC` §12 rule 17
gained the paragraph.

### Measurement

Seven guards, each measured by removal, each witnessed by named cases. One came
back vacuous on the first pass — the seam-carrying itself, masked by the
manager's earlier refusal — and is now driven by a case that observes the value
**arriving** at the adapter, in both the present and the absent form.

### Also closed

The three `ResourceWarning`s the review noted in `test_workspaces`' mutation
lambdas. A leaked-handle warning in a suite about filesystem boundaries is
noise in exactly the place a real leak would show.

### Gates

- the reviewer's own regression — **preserved and passing**
- `test_oci` **82, OK**; `test_attempts` **60, OK**; `test_workspaces`
  **37, OK** (clean under `-W error::ResourceWarning`)
- `test_worker_container`, daemon-backed — **37, OK**
- focused manager gate, 18 modules — **889 tests, 2 failures**, both W6633's
  own open contradiction, unchanged
- contract model **31, OK**; conformance model **74, OK**
- `test_boundary_inventory` — **93 tests, 6 failures**, the accepted baseline
- whitespace check — clean

## 2026-08-27 — the third review's P1: a paraphrased rule

Evidence: `evidence/w19784-2026-08-27-canonical-spelling.txt`.
No repository state was mutated.

The finding is correct and narrow, and the interesting part is not that my
pre-journal check normalized too early. It is that **it was a paraphrase of a
rule that already existed.** The OCI adapter refuses `..` and `:` on a mount
spelling *before* normalization can erase them, and deliberately, with the
reason written at the site. I wrote a second version of that check that
normalized first — so `/else/../input` arrived already collapsed onto the fixed
path, `<inputs>/../inputs` already collapsed onto the proved source, both were
accepted, the start was journalled and the adapter was invoked. The adapter
then refused, correctly, leaving this manager an operation to settle for a plan
that could never have been mounted.

A paraphrase agrees with its original until it doesn't, and it stops agreeing
exactly where it costs most.

### One rule, one owner

So the fix is not a corrected second copy. The target rule **left `_mounts`**
and became `oci.canonical_target`, beside `canonical_source` — the rule it had
always been the twin of — and all three sites call them: `_mounts`,
`OciAdapter._mounts_the_authorized_root`, and `attempts._plan_agrees`.

**Two functions rather than one with a flag**, and the reason is in them: a
source is a HOST path the engine will resolve, so it is `realpath`'d; a target
names a path inside a container that does not exist yet, so resolving it
against *this* host would be asking the wrong machine.

The measurement shows the property rather than asserting it — removing the
single spelling check fails **four** cases across both boundaries and both
spellings, where before the change it would have failed one.

### The inventory noticed the move

Moving the rule moved its **owner**, and an intermediate run failed a seventh
boundary-inventory case: the probe for `run_vector`'s mount target still
expected the old label. The entry now names `canonical_target` and the literal
label that site writes — `a container path`, which says the thing the rule is
about.

### An operational finding I am reporting rather than fixing

My first generation of this evidence file said "both remaining are W6633's"
while the transcript above it showed **three** lines. That is precisely the
inconsistency the first review caught me on, and I will not ship it twice — so
I chased it before writing anything.

`tests/manager/test_store.py` opens three `sqlite3` connections in fixtures and
closes none. Run alone the suite is `OK`, because the warnings arrive at
interpreter shutdown. Run with the other seventeen under
`-W error::ResourceWarning`, the collector fires *during* the suite and the
warning becomes an error attributed to whichever case happens to be executing —
mine caught `test_concurrent_first_openers_adopt_one_initialized_store`, a
concurrency case with nothing to do with it.

**Not mine and not fixed here**: another suite's fixture, predating this Work,
touched by no gate of mine. But a reviewer running warnings-fatal over the
whole gate will keep seeing a different case fail each time, so it is worth
somebody's Work. The headline gate in the evidence is therefore run under
ordinary flags, with the warnings-fatal run scoped to the four suites this Work
touches — three times, same result each time.

### Gates

- the reviewer's two regressions — **preserved and passing**
- `test_oci` **83, OK**; the authorization/mount class **9, OK**
- the four suites this Work touches under `-W error::ResourceWarning`, three
  times — **257 tests, the same 2 W6633 failures every run**, no warnings
- focused manager gate, 18 modules, ordinary flags — **892 tests, 2 failures**
- `test_worker_container`, daemon-backed — **37, OK**
- contract model **31, OK**; conformance model **74, OK**
- `test_boundary_inventory` — **93 tests, 6 failures**, the accepted baseline
- whitespace check — clean
