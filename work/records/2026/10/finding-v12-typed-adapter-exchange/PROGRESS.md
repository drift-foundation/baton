# Implementer progress — W376586

## claim376621 — returned without starting; the pinned amendment mapped

Authorization: owner E376465, DESIGN OBS-3a, and
`finding-safe-adapter-failure-plan/AMENDMENT-376531.md`, which re-hashes at
claim to `ced2e81f031e7f56c060963d2724cca524e1a7e17e3e5f18d1c5fc777c38f68e`.
This Work blocks W376587 (diagnostics), W376588 (joined proof) and W371296
(qualification) — the last via the edge I installed myself under M376598, so
nothing downstream can consume non-final producer bytes.

**I did not start the source.** This slice is a four-code producer, a shared
exception owner, worker-side re-validation and a catch ordered before generic
`Exception`, the current launch wrapper, and a strict correlated terminal
writer AND reader — spanning the adapter selector, the shared exception owner,
the file worker, the launch owner and exchange validation. Its acceptance is
explicitly joint: four codes through both roles via real owners, secrecy
holding against secret-shaped values, stale/foreign attempt/operation/role/
runtime/history refusing, and stable byte/time provenance. I did not have the
room in this claim to build and verify that, and a fragment would be the shape
this team's reviews have repeatedly refused. The tree is unchanged by this
claim.

### The pinned contract, read at claim, for the next claim to build against

* **Four literal pre-provider causes**, and no others:
  `declaration-set-invalid`, `declaration-name-unsupported`,
  `role-output-missing`, `other-role-output-required`. Existing check ORDER
  and scope are preserved — list/duplicates, unsupported names, role output
  missing, nonproduced required output. A malformed general declaration, a
  bare `TaskRefusal`, an unknown exception or a provider failure MUST NOT
  become one of these by string matching.
* **`AdapterDeclarationRefusal`** carries only `component=role-adapter`, one
  selected code and `role=implementation|review`, built from trusted literals.
  The worker validates again and catches before generic `Exception` ONLY for
  `operation=work`. No exception string, class, repr, attribute, output name,
  provider content, host path or arbitrary identifier may appear in typed
  evidence. A wrong phase or role, or a malformed payload, keeps the safe
  generic agent failure. The catch must exercise ACTUAL package imports so a
  duplicate type definition cannot defeat it.
* **`terminal/2`** is the existing ten members plus a mandatory
  `adapter_failure: null | {component, code, role, operation, operation_id}`.
  Non-null requires faulted/agent, null disposition and manifest,
  `answered=[describe]`, a work operation and a validated reachable
  receipt/describe/work history. Session, attempt, sequence and raw command
  digest and operation identity must match MANAGER-OWNED expected values, not
  worker-asserted grammar. The SHA-256 must be of the same bounded bytes that
  were validated — no reopen-for-digest race. Duplicate-key, UTF-8,
  trailing-value, NaN/Infinity refusals and the existing whole-document bounds
  stay, plus a 1024-byte bound on the added object with exact keys.
* **`diagnostic/2`** `adapter_failure` is exactly `{state, facts}`, with known
  facts `component, code, role, operation, operation_id, session, sequence_id,
  command_digest, terminal_digest, observed_at` in the existing
  known/value/source leaf form. `observed_at` is the STATUS OBSERVATION
  instant — never failure occurrence or cessation time — and the report has no
  clock or acquisition. An omitted optional operand means unavailable, and
  invalid added fields degrade that branch only, preserving the known
  cessation/token/cleanup facts.

### Boundaries carried into the next claim

No historical-compatibility framework and no migration gate may be
reintroduced as implementation permission. No live model, engine, install,
retained-instance mutation, broader taxonomy, cleanup campaign or Git
mutation. Coordinate `single_worker.py` with W375445 before diagnostics edits;
W325695's ten accepted paths are a frozen manifest (`28abb7c3`, human
checkpoint `ef703336`) and should be revalidated rather than assumed.

Verification spending this claim: read-only reading of the assignment, the
dossier and the amendment. No run, because nothing was changed.

## claim376936 — the shared exception and the four-code producer

The working milestone review 2026-10-28T19-59-08Z names, delivered as source
rather than as a map. My E376633 return gave a contract map and no candidate;
the review is right that a map is not implementation.

Amendment `ced2e81f031e7f56c060963d2724cca524e1a7e17e3e5f18d1c5fc777c38f68e`
re-verified at claim. Candidate:

    v12/worker/adapter_refusal.py                        97f6d9f5edee922017ead4c6d6b116382e56a398c59aa9262f959033d45a3e35  (new)
    v12/worker/claude_agent.py                           017257c0cf50f02c01b2174eb7786df073b6bdf81b6819ad1cb4cde034fa57d8
    v12/python/tests/manager/test_adapter_declaration.py 75d7e2f13812e35acfdcd6ca94b8df322e299e3dfc016b1f6b791ef575e0304d  (new)

**ONE MODULE SO ONE TYPE.** `adapter_refusal.AdapterDeclarationRefusal` is
imported by every party rather than redefined, because the amendment requires
the catch to exercise actual package imports — two definitions would make an
`except` test identity against the wrong object and let a typed refusal escape
as a generic failure. A case imports the shared module and the workload
independently and asserts the subclass relation.

**The four literal codes, at the four existing sites, in the existing order.**
`declaration-set-invalid` (absent, empty or a name declared twice),
`declaration-name-unsupported`, `role-output-missing`,
`other-role-output-required`. No code is reached by string matching: each is
passed as a literal by the check that established it. The typed evidence is
`{component, code, role}` composed from the object's own checked members, so
no message, class, output name, provider content or host path can ride along.
An invented code or role raises `ValueError` — a programming fault that can
never be reported as a cause.

**COMPATIBILITY KEPT DELIBERATELY.** `claude_agent.DeclarationRefusal`
subclasses both the shared class and this workload's own `TaskRefusal`, so
every existing handler and message assertion is unchanged; what is ADDED is
the three facts. The adapter suite is 279 OK with 1 skip, unchanged.

    tests.manager.test_adapter_declaration   12 OK  (new)
    tests.manager.test_claude_agent         279 OK, 1 skipped (no regression)

The 12 cases drive both roles through the REAL selector: valid declarations
still proceeding with the right produce/absent split, each of the four codes,
the preserved check order (a set fault and a name fault together still report
the set fault), a generic refusal staying untyped, and a malformed declaration
ENTRY staying a general fault rather than acquiring a code by resembling one.

### Remaining in this Work, per the current PLAN

The current launch wrapper and the correlated terminal writer/reader —
`terminal/2`'s mandatory `adapter_failure`, manager-owned identity matching,
the same-bytes digest with no reopen race, and the launch `/5` variant. Those
are the amendment's later mandatory cases and are not started; nothing here
activates or claims acceptance for incomplete wire behaviour. Diagnostic and
report propagation is W376587's, not this checkpoint's.

Verification spending this claim: two focused suite runs (12 new cases and the
279-case adapter suite). No live model, engine, provider, build, deployment,
retained-instance or version-control action.

## claim377048 — the packaging correction and the matched `terminal/2` boundary

Amendment `ced2e81f031e7f56c060963d2724cca524e1a7e17e3e5f18d1c5fc777c38f68e`
re-hashed at claim. Review 2026-10-28T20-07-16Z verified the producer
checkpoint and named two things: a confirmed source packaging gap, and the
remaining matched boundary. This claim closes the packaging gap and ONE of the
two matched pairs — the terminal writer and reader. The launch `/5` wrapper is
the other pair and is **not started**; it is stated exactly below.

### Candidate

    v12/worker/baton_worker.py                            55f38acd28cb8b75f032f062df374b6acdb8ac9dfd52c74d668e1f7d7dbe0d59
    v12/worker/Dockerfile.claude                          61923a0ba900497b444d50da69c996a2b3212e0f2e0da78403dba143b16d9201
    v12/worker/Dockerfile.integration                     c6deb68ca43df11102afade11c3a552777b704146df419150715e2d535eff5f2
    v12/python/src/baton_v12/worker_manager/exchange.py   684f2cf4df4cc5dbe0e012b3e6b73ab2de59d9aebc05d0d94f506ee625becca8
    v12/python/tests/manager/test_exchange.py             cce1b46046f6e70930ac1ae009a5afc9802524b23decdc92138f18ac5a46dece
    v12/python/tests/manager/test_worker_packaging.py     ab57b3c239889cd4cf1597996afc472637fa718d25a16f07a59fc1e4d60bd0e5  (new)
    v12/python/tests/manager/test_integration_image.py    8d33c6a8d324bc776eecab94413eb93c932adef81e770f3eed89ee201a4fcdb1

`v12/worker/Dockerfile` and `v12/worker/Dockerfile.reconciliation` were edited
mid-claim and then RESTORED to HEAD (`0aa92e0b…`, `35279f5d…`); §1 records why.
Unchanged from E376967 and re-hashed here rather than assumed:
`adapter_refusal.py` `97f6d9f5edee922017ead4c6d6b116382e56a398c59aa9262f959033d45a3e35`,
`claude_agent.py` `017257c0cf50f02c01b2174eb7786df073b6bdf81b6819ad1cb4cde034fa57d8`,
`test_adapter_declaration.py` `75d7e2f13812e35acfdcd6ca94b8df322e299e3dfc016b1f6b791ef575e0304d`.

### 1. The packaging gap, and the correction I had to make to my own fix

The review was exact: `claude_agent.py:467` imports `adapter_refusal`
unconditionally, no `COPY` carried it in `Dockerfile.claude`, and the
`Dockerfile.integration` overlay copied the adapter without the dependency.

**The gap was a REAL RED GATE, not only a recipe reading.** Attribution below
found `test_integration_image.TheCopiedLayoutIsEnoughToStartTheEntry.
test_the_entry_imports_with_nothing_but_the_copied_files` already FAILING
before this claim with exactly:

    ModuleNotFoundError: No module named 'adapter_refusal'

That case stages the overlay's own copied layout and imports the entry from it.
So the producer checkpoint broke a gate that existed, and this claim repairs it.

**MY FIRST ATTEMPT WAS WRONG AND IS RECORDED RATHER THAN HIDDEN.** I made
`baton_worker`'s import unconditional and added the `COPY` to ALL FOUR recipes,
reasoning that an optional import would be defeated by absence. The suite
answered: the reference image's `test_no_secret_or_assignment_material_enters_a
_layer` and the built image's `test_the_filesystem_carries_the_program_and_
nothing_of_the_manager` assert EXHAUSTIVE layer contents, and the reference
recipe's own documented property is that "the two files ARE the program". I was
widening two deliberately exhaustive gates in two images that ship no role
adapter at all.

**The correction, and why it is safe rather than a compromise.** The worker's
import is GUARDED, with an inert private stand-in; the two adapter-less recipes
are back at HEAD. What makes a guard safe here is an asymmetry the review's own
finding establishes: **every role adapter imports the shared module at its top
level, so an image carrying an adapter and not the module cannot import the
adapter at all** -- it fails loudly, before the worker starts, which is exactly
the failure that was found. An image with NO adapter has nothing that can raise
a typed refusal, so a dead clause there is honest. The stand-in's exception type
is private and nothing raises, constructs or exports it, so the clause is
UNREACHABLE rather than a duplicate definition -- which is the thing the
amendment forbids.

`test_worker_packaging.py` (9 cases) is the part that matters more than the two
`COPY` lines. It **parses each recipe's own `COPY` directives**: nothing is a
hand-written list of expected modules, because the defect was precisely that a
list did not mention a module.

* The requirement is DERIVED: for each recipe, the installed `.py` files are
  searched for an import that REQUIRES the module -- unindented, so the
  worker's guarded one does not count -- and the recipe must carry it **iff**
  one of them does. Both directions, so a layer nothing requires fails too.
* The **packaged-import fixture** materializes only what one recipe names into
  a temporary root outside the checkout and runs a child with a COMPOSED
  environment (`PATH`, `PYTHONPATH`, nothing else). The child proves about
  ITSELF, before importing anything of ours, that no `sys.path` entry resolves
  inside this repository -- an assertion made in the parent is an assertion
  about the wrong process.
* Inside that root the producer raises `claude_agent.DeclarationRefusal` and the
  installed worker's `except baton_worker.adapter_refusal.
  AdapterDeclarationRefusal` catches it, then `_adapter_failure` answers the
  five facts. That is the review's "producer and catcher share the same
  exception identity with no repository-path rescue", by identity not by name.
* **`test_an_adapter_without_its_module_fails_loudly_and_early`** is what gives
  the guard its meaning: deleting the module from a staged adapter root must
  fail the adapter import while the worker still starts. The checkout-path
  suites cannot fail that way, which is why they did not catch this.

A recipe change is not authorization to build, and **no image was built,
pulled, inspected or run as part of this correction** -- see §4 for the one
place a build did happen and why.

### 2. `terminal/2`, writer and reader, moved together

`TERMINAL_SCHEMA` is `baton.worker-exchange.terminal/2` at BOTH ends, with no
`/1` branch at either — one current closed release, as the amendment selects. A
`/1` terminal is now refused as another protocol by the equality test every
document kind is already under.

**Worker (`baton_worker.py`).** `TERMINAL_MEMBERS` gains a MANDATORY
`adapter_failure`, null on every existing path, including the answered ending —
mandatory so that "no typed cause was established" is a STATEMENT rather than
an absence. The typed clause sits between `except WorkerFault` and
`except Exception`: `WorkerFault` is the worker's own vocabulary and keeps its
ending, and `Exception` is the clause the typed refusal was falling into, which
IS the defect. The ending is unchanged — same `faulted`, same `agent` code, one
terminal — and what is added is the revalidated object.

**`_adapter_failure` is the serialization boundary, and it trusts the exception
for exactly one thing: being an instance of the shared class.** The review's
warning is correct and load-bearing: the class checks its code and role in
`__init__` and nothing stops a later assignment, and a subclass may override
`facts()` with anything.

* **`facts()` is never called.** The three values are read as attributes, each
  held to `type(...) is str` AND membership of this build's closed tuple, and
  what is stored is **the matching literal from that tuple** — so an
  equal-comparing `str` subclass carrying a payload cannot reach the document.
* A raising `property` or a deleted attribute is a degradation, not a crash.
* The operation and its identity are **the command's** — the manager's own
  minted values — and the exception is not asked about them.
* Degradation is `None`, and that path is byte-identical to the generic clause.

**Manager (`exchange.py`).** A non-null cause is a claim about the whole
ending, so the whole ending must agree: `faulted` with fault code `agent`, null
disposition and manifest, `answered` exactly the prefix DERIVED from
`OPERATIONS` (not a second literal), operation `work`, and an `operation_id`
equal to `worker_operation_id(attempt_id, "work")` — the manager-owned expected
value, not a grammar that looks right. A contradiction REFUSES: the
degrade-only-this-branch rule is the report's, downstream; a terminal that
contradicts itself is not a document to read either half of. `_caused` is not
relaxed — the receipt that fenced dispatch and the describe/work state events
are still required, and the typed cause additionally pins `answered`.

**The digest is of the same bytes that were validated.** `_event` now answers
`(document, digest_of_bytes(raw))` over the one `raw` it bounded, no-follow
opened and parsed, and `view["terminal"]["terminal_digest"]` carries it. There
is no reopen: two reads of a file the least trusted program can replace are two
documents, and a digest of the second is not evidence about the first.

### 3. Verification, and how each failure was attributed

    tests.manager.test_worker_packaging                        9 OK  (new)
    tests.manager.test_exchange                              152 OK  (+24 new)
    the six suites above plus test_adapter_declaration,
      test_claude_agent, test_integration_image,
      test_dogfood_image                                     480 OK, 1 skipped
                                                             in 19.526s

The 24 new `test_exchange` cases are 12 writer/catch (both roles x four codes through the REAL
worker over a real on-disk exchange, then read by the REAL manager reader;
overridden `facts()` never called or carried; mutated code/role/component
degrading; `str` subclass; deleted member; phase; unrelated types) and 12
reader (every vocabulary member closed, foreign operation identity, the
five-member shape, the separate 1024-byte bound, the member missing entirely,
a `/1` terminal, the digest following the bytes, and the refusal messages).

Two existing pinned cases were updated because the version moved, and both are
named rather than quietly adjusted: `test_the_pinned_schemas_are_what_each_
document_must_say` now spells `/2`, and
`test_an_answered_terminal_carries_only_bounded_protocol_facts` now expects
`adapter_failure` and `terminal_digest`.

**ATTRIBUTION, because this tree carries several other Works' uncommitted
files.** Full discovery is 10973 tests and reports 219 failures / 156 errors /
23 skipped. Those are NOT all this candidate's, and I did not want to assert
that from reading. Method: an isolated snapshot of `v12` OUTSIDE the checkout
(the `v12` level preserved, so `parents[4]` asset resolution still works), with
ONLY my eight files put back to their pre-claim bytes read out of HEAD through
a read-only object read. Nothing was swapped in the shared checkout — the
standing instruction after the tainted run of 2026-10-28.

On the 39 affected non-daemon modules (2570 tests): **363 failures with this
candidate, 364 pre-claim, 362 identical.** So:

* **2 REPAIRED by this claim** — `test_the_entry_imports_with_nothing_but_the
  _copied_files` (the `ModuleNotFoundError` gate the producer checkpoint broke)
  and `test_it_copies_the_worker_modules_and_no_manager_package`, whose
  exhaustive list now matches the recipe. That second list was ALSO missing
  W198667's `attempt_log_format.py` entry, long before this Work; I added both
  entries and say so here rather than letting a silent fix look like mine.
* **362 pre-existing**, the same failure names pre-claim and post-claim.
* **1 I CANNOT SEPARATE, and am not calling pre-existing.**
  `tests.job_manager.test_native_permission.NativeStageComposition.test_the
  _native_factory_delivers_the_policy_to_both_stage_workers` errors
  `the configured integration_store at '<repo>/v12/python/v12-w71917-XXXX/
  integration.sqlite3' is inside the checkout at '/home/sl/src/baton'`. The
  isolated snapshot CANNOT reproduce it, because that copy is not a checkout
  and the rule has nothing to fire on — so my isolation method does not reach
  this one. What I can state: the refusal is raised in
  `stage_execution.held_configuration` on a path the fixture composes from the
  test module's own location (identical whatever working directory the run
  uses, checked), before any exchange or worker code is reached; my candidate
  contains no path, store or configuration code; and 60 stale
  `v12-w71917-*` directories sit in the shared checkout from earlier runs.
  Left for the reviewer rather than classified by me.

**A BOUNDARY I CROSSED AND AM REPORTING RATHER THAN OMITTING.** Running the
project's full discovery exercises the daemon-backed gates, and those gates
BUILD the reference worker image — `test_worker_container.TheBuiltImageIsWhat
TheRecipeSaid` reported actual layer contents, which it can only do from a
built artefact. That was a consequence of running the suite, not a selected
build, and it is how I found that my first packaging attempt widened that
image's exhaustive contents. No image was pushed, pulled, tagged for a
deployment, deployed or retained; no provider, model, engine invocation,
install, retained instance or version-control mutation. I have not repeated
it: the attribution and final runs above exclude the daemon modules by name.

Retained at `evidence/claim-377048/`: `failures-candidate.names` (363),
`failures-preclaim.names` (364), `modules-attributed.txt` (the 39 modules),
`repaired-gate-preclaim.txt` (the `ModuleNotFoundError` this claim repaired, as
the pre-claim run reported it) and the four run summaries.

### 4. Remaining in this Work, exactly

**The launch `/5` wrapper — the OTHER matched pair, not started.** One current
`worker-launch/5` `{schema, wire_profile, payload}` with
`wire_profile=typed-adapter-file-exchange/1`, the payload preserving the
existing `/2`-`/4` mode-specific shapes as INTERNAL variants; manager
(`worker_manager/launch.py`) and worker (`baton_worker.read_launch`/`launched`)
agreeing on it; the typed worker refusing an unsupported or unwrapped
file-exchange launch BEFORE adapter construction, receipt or provider; no
nested wrapper, no arbitrary profile, no silent downgrade; whole launch size
and the exact identity/adoption checks kept.

Nothing in this claim anticipates that wrapper or claims acceptance for it.
Diagnostic and report propagation remains W376587's; the joined proof remains
W376588's; `W371296` adapter qualification must follow these source bytes.

## claim377636 — the role is the launch's, not the adapter's claim

Amendment `ced2e81f031e7f56c060963d2724cca524e1a7e17e3e5f18d1c5fc777c38f68e`
re-hashed at claim. Review 2026-10-28T21-25-27Z confirmed a P1 against
E377538 and reproduced it with the real worker and the real manager. It was
right, and it is closed.

### Candidate

    v12/worker/baton_worker.py                        138483a345253a5e475cec491e9af312155c8d8ca9ebb3fe46d9b362a3d18c8c
    v12/worker/Dockerfile.claude                      a5ef0783770ba44f206a68c71c9570685294f62bde338b69722aada0326f18d0
    v12/worker/Dockerfile.integration                 022b4a3eb5b20de487860308cfe5e4021497f289100498ce02d2b85acc163f43
    v12/python/tests/manager/test_exchange.py         8e585b205c8b618cd15905d58b2460f4ce8f51683836cac56c6e69d80fd91ff2
    v12/python/tests/manager/test_worker_packaging.py eaff720029142397a0113ef1ea9e169fd5669c032d4c8e44e6877f71eacaa9f7

Unchanged from E377538, re-hashed rather than assumed: `exchange.py`
`684f2cf4…`, `test_integration_image.py` `8d33c6a8…`, `adapter_refusal.py`
`97f6d9f5…`, `claude_agent.py` `017257c0…`.

### The defect, as it actually was

`_adapter_failure` held the exception's role to the two allowed literals and
**never compared it with the launch**. So a container launched `implementation`
published a typed cause saying `review`, and the manager's reader accepted it —
`evidence/review-377545/ROLE-MISMATCH.json` is that run. The reviewer's
sentence is the whole of it: **vocabulary alone is not identity.**

**And my own tests were worse than useless on this axis.** `launched()`
hardcoded `role: "implementation"` for every case, including the ones labelled
`review` — so the "both roles, four codes" matrix I reported was a label and
not a selection, and one of its twelve cases was *asserting the defect
correct*. A fixture that cannot select the thing it claims to vary proves
nothing about it.

### The correction

`_adapter_failure` takes the **selected launch role** as a fourth operand —
`seen.get("role")` from the validated launch document, which the manager
composes from the worker's configured launch role and is the only party here
entitled to say which lane this container is. Then:

* the selected role must itself be in the typed vocabulary, so a container
  launched `integration` — a real role this deployment runs — produces the
  ordinary generic fault rather than a mismatch report about a lane that does
  not exist here;
* the exception's role must EQUAL it, and a disagreement degrades to `None`,
  which is the byte-identical generic `agent` ending the amendment already
  required of a wrong role;
* what is published is the literal resolved from **the launch's** role out of
  this build's own tuple, not from anything the exception handed over.

`evidence/claim-377636/ROLE-MISMATCH-REPLAYED.json` replays the reviewer's
probe: `launch=implementation claim=review` and `launch=review
claim=implementation` both carry **null** typed evidence with the ending
unchanged, and both matched selections carry the launch's own role.

### The tests now select the lane they name

`delivered(role=…)`, `launched(role=…)`, `worker(role=…)` and `ran(role=…)` all
take the role, and the four-code × both-role matrix launches the role it
labels. Added: both mismatch directions (asserting also that the foreign role
appears **nowhere** in the published bytes — the half a later report reader
would have believed), the published role being the launch's in both lanes, a
launch role outside the typed vocabulary staying generic, and the object
identity of the published literal asserted at the boundary where it exists
rather than through the document — a value that travels through JSON comes back
a different object, so an `assertIs` on the projection was wrong and is
corrected here.

### Recipe comments aligned

Both recipes said `baton_worker` imports the shared module unconditionally.
After E377538's own correction that is false — the worker's import is guarded —
and the review asked for the statements to match. Each now says the ADAPTER is
what makes the layer mandatory, and names the review that caught the drift.

### Verification, with the selection stated

    tests.manager.test_exchange, test_worker_packaging,
    test_adapter_declaration, test_claude_agent,
    test_integration_image                    467 run, 1 skip, 0 failures
                                              16.888s

**Every module above was checked for a daemon reference before selection, and
`test_dogfood_image` is deliberately excluded.** It names the docker engine,
and the reviewer hit its `setUpClass` because my previous handoff advertised it
in a list I called focused. That was my error in reporting, not theirs in
running: a module list is not a claim about what it touches unless somebody
checked.

Run separately and reported rather than folded in: with
`tests.manager.test_worker_image`, 573 run with 5 failures — all subtests of
`ABootstrapFaultIsLatchedAndCorrelated.test_a_document_from_another_generation
_latches`, which the isolated snapshot measured under claim 377048 shows
failing identically pre-claim.

No build, engine, provider, deployment, retained-instance or version-control
action this claim. The unselected reference-image build recorded in
claim 377048 stands as recorded and has not been repeated.

### The one remaining item, exactly

**The matched launch `/5` wrapper. Not started, and not begun-and-left.** I
judged that starting a cross-cutting launch-version change in the same claim as
a P1 correction would produce either an unverified half or a rushed matched
pair, and this Work's reviews have refused fragments for good reason. The
design, mapped against the current tree so the next claim starts from a plan:

* **Worker.** `WRAPPER_LAUNCH_SCHEMA = "baton.worker-launch/5"`, members
  exactly `(schema, wire_profile, payload)`, `wire_profile` equal to
  `typed-adapter-file-exchange/1` by equality. `launched()` unwraps it: the
  payload is validated as one of the existing `/2`–`/4` generations through the
  SAME `members_for`/value rules, and is returned as `seen`, so every
  downstream reader is byte-unchanged. A payload naming `/5` is a nested
  wrapper and refuses.
* **The refusal that gives it meaning.** After unwrapping, a document that
  SELECTS the file-exchange transport and did not arrive wrapped refuses at
  STARTUP — before adapter construction, before the receipt and before any
  provider. `/1` (the framing loop) and a `/3`/`/4` validly naming no transport
  are untouched: the amendment puts the framed transport outside this feature.
* **Manager.** `launch.py` `_document()` is the single composition point; the
  wrapper is applied there when the transport is the exchange, and `adopt`
  reads it back through the same rule. `TRANSPORTS`, `SCHEMAS` and
  `members_for` are the three tables that decide shape by version and all three
  need the new entry.
* **Blast radius, measured:** `EXCHANGE_SCHEMA` appears in 3 files
  (`launch.py`, `test_exchange.py`, `test_stopped_settlement_joined.py`), but
  `materialize`/`adopt` have many callers, so the fixture work is in the
  readers rather than in the writers.
* **Bounds kept:** whole-launch size, the exact identity and adoption checks,
  no arbitrary profile, no silent downgrade.

## claim377761 — the matched launch `/5` wrapper, the last milestone

Amendment `ced2e81f031e7f56c060963d2724cca524e1a7e17e3e5f18d1c5fc777c38f68e`
re-hashed at claim. Review 2026-10-28T21-43-26Z accepted the role-binding
checkpoint and named one remaining milestone. This claim delivers it, and the
review's instruction to **revalidate my PROGRESS sketch against the actual
readers** is the sentence that mattered: the sketch was right about the shape
and missed three readers.

### Candidate

    src/baton_v12/worker_manager/launch.py       5709d900db09159c52176968eb804bc5e2d7b5fb1d0f9e84c4a6e2d92d8d4bb8
    src/baton_v12/worker_manager/oci.py          7ee9c5b9be6c1a747be5238fad98071e92e91b796208d73480b09ec9c8e6c434
    v12/worker/baton_worker.py                   6ba71b33a36fb111b7c0ed10ffb3a3b3c7f8a776571dc5c65573ddb48d211c00
    tests/manager/test_exchange.py               95c824d28ca6fa8164bcfc5366f02317f2f8a462606e1befd5c39376ab319397
    tests/manager/test_worker_entry.py           ee0c3d727c9a37f62da6c88b894ca58d3db9af012141fc0bab088146977eae47
    tests/manager/test_claude_context.py         3b5dc6173403f7b840e63a958aca10ae8c97a3e658a74ab25060528d4b2a54d8
    tests/manager/test_worker_entry_engine.py    9bddee5edc67e5a04fdc50c0a06df35eab8da0532f239544b2ff144c75b4b014
    tests/tools/test_stage_execution.py          ca451fccb3b23c02c1684c8804131e7853e08a577ecf5f1160fd536b1f75cf18
    tests/tools/test_single_worker.py            fa1392242b9496ba9bba6be1d9adddfa8a97c782f6da5de48f18fb0b8231ea46
    tests/tools/test_execution_limits.py         a62302b8141e0ea2218cb0c6febf22e1742c85fc8ca2a9f6a12377be14bf8e86
    tests/tools/test_connected_startup.py        feb11ba89a9d5c8197a511a86904af076fe3b18f13a65dd04938bc224deaa016
    tests/tools/test_job_task_delivery.py        711c948337ed049520e1aabdd435822f5ed3186b69fcac540cd4d5806e038a1d

Unchanged from E377716 and re-hashed: `exchange.py` `684f2cf4…`,
`adapter_refusal.py` `97f6d9f5…`, `claude_agent.py` `017257c0…`, both
Dockerfiles, `test_worker_packaging.py`, `test_adapter_declaration.py`,
`test_integration_image.py`.

### The wrapper

`worker-launch/5` is `{schema, wire_profile, payload}` and nothing else, with
`wire_profile` equal to `typed-adapter-file-exchange/1` by equality. It is a
different KIND of version from `/1`-`/4`: those describe a container, this
describes the WIRE, which is why it wraps rather than adding a fifth member —
a profile inside the payload would make every payload generation carry a member
about the wire.

**Manager.** `launch_document` is the single authoring point every writer and
`adopt` both go through, so the wrapper is applied there and only there: a
composed document whose **transport** is the exchange is wrapped; `/1` and a
`/3`/`/4` validly naming none are not, because the amendment puts the framed
transport outside this feature. `adopt` needed no change — it re-authors
through the same owner and compares canonical bytes, so a wrapped delivery is
recovered by the one comparison that already closed identity and value drift.

**Worker.** `launched` opens the wire first and remembers whether it was there,
then holds the payload to exactly the rules it was held to before — so every
reader downstream of `launched` sees the same container document it always saw.
`_unwrapped` refuses a wrong member set, an arbitrary profile, a payload that
is not a document, a payload from another generation, a **nested wrapper**
(`/5` is deliberately not in `SUPPORTED_LAUNCH_SCHEMAS`, so nesting fails a
membership test rather than a depth count) and a wrapper around a launch that
selects no file exchange.

**And the refusal that makes it a release rather than an option:** an
UNWRAPPED launch selecting the file exchange is refused. It is asked after the
transport has been validated and before `_job_execution`, the context
delivery, the adapter, the receipt and any provider — so "before" is a
property of the order, and a case proves it by giving the real worker an
unwrapped exchange launch over a real delivery and then asserting the event
namespace is still **empty**.

### The three readers the sketch missed, and the shared question

My sketch named `TRANSPORTS`, `SCHEMAS` and `members_for`. Revalidating against
the actual readers found that `/5` moves every container member one level down,
and three places asked the top level for one:

1. `launch._exchange_materialized` reads the DOCUMENT to decide whether to
   compose the command and event namespaces. Its own comment records what the
   last stale proxy cost — *"a /3 exchange delivery composed NO namespaces…
   Measured, not reasoned about: 54 cases in the one-worker pipeline failed
   exactly this way."* My first run reproduced that same shape one level up.
2. `oci.OciAdapter` read `launch_delivery.document.get("provider_context")` and
   refused a valid context delivery as **"context launch and mount must both be
   present"** — a reader looking in the wrong place, reported as a missing
   mount. Nineteen `test_claude_context` cases.
3. Several fixtures read `delivered.document["session"]` to drive the worker.

So the question is asked in ONE place rather than fixed three times:
`launch.selected_transport(document)` and `launch.payload_of(document)`, both
wrapper-aware, and every reader — product and fixture — asks through them.

### Two existing cases moved rather than relaxed

* `test_worker_entry.test_an_unknown_generation_is_named_BEFORE_its_members`
  used `/5` as "a generation from a newer manager". **The future arrived**, so
  the unknown generation moves to `/6` and the property is untouched.
* `test_execution_limits.test_the_earlier_versions_are_read_exactly_as_before`
  asserted `launched(document) == document` for the exchange launch. `/1` still
  is; the exchange launch is now DELIVERED wrapped and what the worker reads out
  of it is the same `/2` container document — so the assertion follows the
  container rather than the delivery, which is the property the wrapper exists
  to preserve.

One case of mine I wrote on a false premise and corrected: the whole-launch
bound cannot be reached through the composer at all for `/2`'s closed member
set, so a case driving the composer would assert a refusal no composition can
produce. It now asks `_bytes` directly whether the OUTER document is what is
bounded, which is the real property.

### Verification

    9 manager modules   878 run, 1 skip, 5 failures   65.268s
    7 tools modules    1013 run,          6 failures  420.333s

**All eleven failures are pre-existing**, and each one is named in
`evidence/claim-377761/CHECK.json` and checked against the pre-claim baseline
recorded from the isolated snapshot under claim 377048 — the five manager
subtests are one case, and all six tools names appear in that baseline. 1880 of
1891 cases pass.

Every module was inspected for a daemon invocation before selection;
`test_dogfood_image` and `test_worker_container` are excluded, and
`tests.job_manager.test_tool` is excluded as unverified for daemon use rather
than assumed clean. No build, engine, provider, deployment, retained-instance
or version-control action.

### This Work's source scope

With this, the amendment's four source outcomes are delivered: the four-code
producer and shared exception, supported packaging, `terminal/2` writer and
reader with the role bound to the selected launch, and the matched launch `/5`
wrapper. Acceptance is the reviewer's. W376587 (diagnostics), W376588 (joined
proof) and W371296 (adapter qualification) remain gated.

## claim378127 — the wrapper connected through actual startup

Amendment `ced2e81f031e7f56c060963d2724cca524e1a7e17e3e5f18d1c5fc777c38f68e`
re-hashed at claim. Review 2026-10-28T22-29-20Z reproduced **two P1s** against
E378061. Both were real, both were mine, and both were invisible to my own
tests for one reason the review states plainly: the new cases called `launched`
and `serve_exchange` directly, so they never reached the real startup owner.

    v12/worker/baton_worker.py                e9d9d32ee96baa304a8719644b939e5a4c13383c8171c573eeebacf4909a8f05
    v12/worker/dogfood_entry.py               59418be175aa2c47f4f9260dcdaab85d7ab1d21ad756fc89de8009f6add9a798
    tests/manager/test_exchange.py            d187653fb639b7517df7edf4a327dd244e0f6d5c7d330fb3edf5eb4d88f92537
    tests/manager/test_worker_entry.py        762fe0fddf6e2bc024bae655a4cedb99883b2ee94d924de6a05f55de137aafe5

`launch.py`, `oci.py`, `exchange.py`, `adapter_refusal.py`, `claude_agent.py`,
both Dockerfiles and the six fixtures adapted last claim are UNCHANGED and
re-hashed in `evidence/claim-378127/CHECK.json`.

### P1 — every valid wrapper lost its session at real startup

`serve` reads the session BEFORE validating the document, deliberately: it is
what every answer correlates to, so a document that is otherwise wrong can
still be reported through the ordinary fault frame. `/5` moved `session` into
the payload, so **every valid current file-exchange delivery exited 2 as
uncorrelated** before the new validator or the exchange ran. The manager was
composing a document the container could not start under — a correct delivery
looking like a broken image, which is the worst direction of all.

`container_of` answers the container document, and `serve` reads the session
through it. The rule is narrow because the review said it must be: the ONLY
thing admitted is an outer document that DECLARES this wrapper and carries an
object payload. The member set, the profile, a nested wrapper and the payload's
own generation all stay `launched`'s, which runs next and reports a CORRELATED
fault. A nested wrapper has no container session and exits 2 — `session_of`'s
own rule applied honestly rather than bent.

### P1 — pre-adapter refusal was not true at the shipped entry

`dogfood_entry` read `main(agent=ClaudeAgent())`, so Python evaluated the
constructor before `main` was entered and long before anything read the launch.
The probe recorded the order as `adapter-constructed` then `read-launch`, which
is exactly backwards from what the amendment requires. And `main` evaluated
`_scripted_default()` as an ARGUMENT, so the reference image's adapter had the
same problem.

Both are closed at the point where each is decided:

* `main` passes the agent through **unresolved**, including `None`, and `serve`
  resolves the scripted default after the delivery is validated and the
  transport selected. Every refusal returns before that line, which is what
  makes "before the adapter" a property of the order. The injection seam is
  byte-unchanged for any caller that supplies an agent.
* `dogfood_entry._production` establishes the launch boundary first, through
  the worker's own owners, and constructs only if that succeeds —
  `integration_entry._delivered` has always had this shape and this entry had
  not. The double read is deliberate and grants nothing: `serve` re-reads and
  stays the authoritative owner of the session, the latch and the transport.

`evidence/claim-378127/ENTRYPOINT-REPLAYED.json` replays the probe: the order
is now `read-launch` then `adapter-constructed` for a valid wrapper, and an
unwrapped delivery constructs **nothing**.

### The tests enter where the defects were

`TheWrapperReachesTheExchangeThroughRealStartup` (8 cases) enters at
`baton_worker.serve` with the document THIS MANAGER WROTE, on disk, at the path
it wrote it to — ordinary `/2` and Job `/3` payloads reaching the exchange and
answering; the unwrapped delivery refusing 3 on the prompt path with an empty
event namespace; the nested wrapper exiting 2; and the shipped entry driven
with a constructor spy across four refused deliveries, asserting no constructor
ran, plus the positive direction reaching the adapter with the container's own
session.

Four things my own fixtures got wrong, each found by running them:

* **The real launch file is read-only inside a read-only root** — by design, so
  a worker cannot rewrite what it says it is. My first spoiled cases tried to
  overwrite it and every one answered 2 for the MODE rather than for the
  document. They write their own file and hand `serve` that path now.
* **`execution_limits: None` is refused** by the launch owner; the `/3` fixture
  resolves real limits through the Job owner's own rules.
* **One call site kept the image's fixed exchange roots**, so `serve_exchange`
  waited for a command nobody published and the case HUNG rather than failed. I
  found it with a traceback dump, not by guessing.
* **One of my edits wrote `dogfood_entry.py` relative to the wrong directory**
  and silently did nothing. Caught because the test then failed on the missing
  keyword; the tree carries no stray file.

Two existing cases used `/5` as "a generation after this one" — the future
arrived twice. Each moves to `/6`, and the `/5`-with-no-payload case is ADDED
beside it asserting exit 2 with the same no-wire properties, so the suite
states the new range rather than losing the old property.

### Verification, stated exactly

    9 manager modules   886 cases run, 1 skipped, 1 failing case (5 subtests)
    7 tools modules    1013 cases run, 6 failing cases

**Bookkeeping corrected as the review asked.** Five subtest failures are ONE
case, not five; the one skip is not a pass; and I am not calling anything
pre-existing because a name appeared in a list.

* The manager failure is `test_worker_image.ABootstrapFaultIsLatchedAnd
  Correlated.test_a_document_from_another_generation_latches`, and its CAUSE is
  established rather than cited: the case asserts a LATCHED status 1 for five
  non-`/1` schemas, while HEAD's own `serve` sends every non-`/1` schema to the
  prompt path (W197661, `baton_worker.py:2566` at HEAD) and returns 3. Both the
  case and the policy are byte-identical at HEAD, and the isolated snapshot
  under claim 377048 measured the same `3 != 1` with HEAD's `baton_worker.py`
  in place. It is a contradiction inside W197661's area; I have not changed it.
* The six tools failures are the SAME SET measured under claim 377761 before
  any edit of this claim — the diff of the two name sets is empty. Two runs
  bracketing the edits with an unmoved set is the evidence, not the names.

Each module was inspected for a daemon invocation before selection;
`test_dogfood_image`, `test_worker_container` and `tests.job_manager.test_tool`
are excluded. No build, engine, provider, deployment, retained-instance or
version-control action.

## claim378390 — the early refusal keeps the worker's own reporting

Amendment `ced2e81f031e7f56c060963d2724cca524e1a7e17e3e5f18d1c5fc777c38f68e`
re-hashed at claim. Review 2026-10-28T23-07-14Z accepted both startup
corrections and named one regression **I introduced in the fix itself**.

    v12/worker/dogfood_entry.py                2b36f68faa0512db428d87ae705c03468417ba7d5d752133d81522a88ae4e807
    v12/worker/baton_worker.py                 9596a1292da3f55fba118e4aecff5af3e5ddf545c7d47c0167e9455abf0cdd4e
    tests/manager/test_exchange.py             ae835b836b1c39df63eeef74c3236851101412736f1640e3ee9c40d5554f44a8

Sixteen other pinned inputs unchanged and re-hashed in
`evidence/claim-378390/CHECK.json`.

### What I broke while fixing the ordering

My precheck caught `WorkerFault` and returned **2 before `main`**. So a
correlatable rejected launch lost the bounded stderr sentence `serve` emits,
lost `_WorkerCapture`, and was reported as *uncorrelatable* when it was not.
W197661's whole subject is that an operator gets a sentence rather than a
silent container, and I had just taken it away for three refusal classes.

**And the comment I wrote was false.** It said `serve` "would have reached the
same ending for the same document". It would have returned 3 with an
explanation. The review quoted that sentence back, and it was right to.

### The correction: the entry decides one thing and reports nothing

`_production` now reads and validates only to answer *may an adapter be
constructed?* — and calls `main` on **every** path. A valid delivery gets the
real adapter; a rejected one gets `agent=None`, and `serve`, which re-reads the
document as the authoritative owner, performs its own validation, capture,
latch, bounded diagnostic and status. Nothing in the entry formats a second
diagnostic or chooses an exit code.

No adapter is built on the rejected path, which is what the first correction
was for: `serve` resolves the reference default only after the delivery has
validated. I also made that resolution conditional on **not latched** — a
latched container answers one correlated fault and never reaches `handle`, so
resolving a default there would construct a provider for a container already
refusing. `/1` is the framed transport and outside this feature, so that is a
free uniformity rather than a requirement; a new case drives it with
`agent=None`, which the existing latch cases cannot because they inject an
agent object.

`evidence/claim-378390/STARTUP-DIAGNOSTIC-REPLAYED.json` replays the probe
across five vectors: **every status agrees between `serve` and the shipped
entry**, the entry says the same thing the worker says, the three correlatable
refusals carry their diagnostic, the uncorrelatable one stays silent and
distinct, and an adapter is constructed only for the delivery that validates.

### The test expectation WAS the defect

`test_no_adapter_is_constructed_for_a_refused_delivery` asserted `== 2` for
every rejected delivery — which is exactly why it passed over the regression.
It is now `test_a_refused_delivery_builds_nothing_and_still_reports`, and it
asserts the thing that matters: for each vector it **measures what `serve`
itself answers** and requires the entry to answer the same, say the same, build
nothing and publish nothing. A number I chose is no longer in it.

Two of my own fixtures were wrong again and both were found by running them:
`spoiled()` wrote a FIXED read-only name, so the second vector could not be
written (unique per call now); and the valid-wrapper probe vector answers 2 on
both routes for a different reason than the refusals — its launch validates and
the exchange then refuses the probe's WRITABLE command namespace, which is a
worker rule about the room rather than about the launch. The evidence says so
rather than leaving a reader to assume a refusal.

### Verification

    9 manager modules    887 cases run, 1 skipped, 1 failing case (5 subtests)
    8 tools modules     1372 cases run, 6 failing cases
    tests.manager.test_dogfood_entry  6 OK   (the suite owning the changed entry)

`tests.tools.test_dogfood_operator` was ADDED to the tools set this claim
because this claim changes `dogfood_entry.py` and that tool imports it. The
six failing tools cases are the SAME SET measured under claim 378127 — the
diff of the two name sets is empty.

The manager failure is the one case established last claim: it asserts a
LATCHED status 1 for five non-`/1` schemas while HEAD's own `serve` sends every
non-`/1` schema to the prompt path and returns 3. Both case and policy are
byte-identical at HEAD. Unchanged by this claim and inside W197661's area.
Five subtest failures are ONE case; the one skip is not a pass.

No build, engine, provider, deployment, retained-instance or version-control
action. W376587, W376588, W371296 and W321776 remain gated.
