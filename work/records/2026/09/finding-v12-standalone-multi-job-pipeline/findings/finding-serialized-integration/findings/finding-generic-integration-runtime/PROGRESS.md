# Progress

Ledger Work W101490 created; prepared for assignment to K.

## 2026-09-06 — baton.claude — the boundary, composed rather than invented

W101490's first implementation round, against HEAD `652cb2c`, which carries the
coordinator this composes on. New `src/baton_v12/integration/runtime.py` and
`tests/integration/test_runtime.py`; `src/baton_v12/integration/__init__.py`
re-exports the boundary; one `tools/parallel_test.py` registry entry; and one
correction to `integration/store.py` that this round's sweep asked for. 58
focused cases for this leaf, and the coordinator's 187 pass beside them.

### What the revalidation changed about the plan

Plan item 1 was not a formality. Three things this leaf was going to build
already exist, and one of them exists more strongly than the plan assumed.

- `worker_manager/exchange.py` already owns the mechanism the acceptance clause
  describes: five-step atomic publication, no-follow bounded regular-file reads
  proved on the descriptor, closed schemas, and an observation that reports
  unreadable worker material rather than raising -- because a manager that
  raised would let the least trusted program in the deployment stop the sweep
  for every other stage.
- `launch.py`, `workspaces.py`, `source_boundary.py` and `attempts.py` own the
  launch document, the mounts and the runtime axes.
  `job_manager/delegation.py` states the rule this follows in a sentence I did
  not improve on: THERE IS NO SECOND STATE MACHINE.
- **Agent quiescence is not runtime quiescence, and the tree says so louder
  than the plan did.** `sessions.satisfies_runtime_quiescence_gate` answers
  false BY CONSTRUCTION -- a finished conversation is not evidence that the
  runtime holding the generation is gone. I had intended to take a session fact
  for "the prior runtime cannot mutate". It would have been wrong and it would
  have looked right. The positive answers live only on the manager's
  `execution_runtime` axis, where `uncertain` may never become `destroyed`
  because destruction is a fact about the world.

### What the boundary is

Four documents and their verbs, each owned where it is READ as well as where it
is built:

- **the profile** -- a deployment's trusted wiring for one target. It carries
  no location, no argv and no mount table, because the manager's own components
  own all four and a profile that carried them would be this boundary deciding
  another one's contract while calling itself generic.
- **the assignment** -- composed ONLY from a live grant read from the
  coordinator inside the same call. The grant's own values fill the target,
  entry, lease and fence members rather than the caller's: the two are equal
  only when the proof passed, and using the store's is what makes that visible
  instead of assumed.
- **the result** -- the runtime's claim, adopted as untrusted input, in the
  coordinator's own three terminal words so a later leaf choosing
  `settle_integrated`, `refuse_entry` or `block_target` is choosing a verb and
  not translating a vocabulary. Adopting one settles nothing.
- **the hold** -- an account whose members are exactly `block_target`'s reason
  and detail. Composed and returned; never applied.

**Writable access is decided here and is not an operand.** It needs the live
grant AND a positive prior-runtime observation. `ACCESS_KINDS` is a ONE-member
tuple, deliberately: I wrote `("none", "read-only", "writable")` first and took
the other two out, because a runtime that cannot write the target cannot
perform the integration it was launched for. Those are refusals, and a refusal
should say what it refused rather than be encoded as an access kind a caller
could ask for.

### The durable delivery, and the sentence it narrows

The revalidation section says this leaf "mints NO second exchange". That was
written before the file half was built, and FINDING.md now narrows it rather
than leaving it to be read as more than it is. What stands is that no second
MECHANISM and no second state machine exist: every rule the delivery uses is
`exchange.py`'s. What is narrowed is that this leaf does materialize its own
two namespaces -- and `exchange.py`'s own argument for being a third delivery
is the argument for this being a fourth. Its `command/` and `events/` carry one
attempt's OPERATION SEQUENCE, and an integration assignment is not one of those
two operations; `inputs` is frozen and closed over W19784's protocol pair;
anything under `workspace` is reachable through the runtime's own writable
mount, so an assignment placed there could be replaced by the very program it
is addressed to.

So: `integration/assignment/`, manager-written and mounted read-only at a fixed
target, and `integration/result/`, created in the deployment's configured
workspace group and read here as untrusted input. Unreadable runtime material
becomes a HOLD rather than an exception -- a link at the fixed name, material
wider than the bound, bytes that do not decode, a result outside the contract,
a result answering another integration, and an assignment replaced underneath
the observation. `waiting` is deliberately not rounded into a hold: an
integration with no result yet may still be running.

### One correction this round's sweep asked for

The first full sweep ERRORED in `tests.manager.test_store` with a raw
`sqlite3.OperationalError: database is locked` from
`PRAGMA journal_mode = WAL` inside `ControlStore._initialize`. That module is
another record's and the test passes in isolation, so it is filed as **W101621**
rather than fixed here -- but it sent me to look at my own coordinator store,
which had the same line. `PRAGMA journal_mode` is one of the statements SQLite
can answer BUSY on without the busy handler retrying it, so two coordinators
opening one store at the same instant could have left one holding a raw
`OperationalError` out of a public constructor. The eighth round's own docstring
already claimed WAL was a request and not a requirement; now it is one.
`test_the_wal_switch_is_a_request_and_a_busy_answer_is_not_one` drives it
deterministically with a second connection holding the write lock.

### What I did not build, and why the tests say so

No candidate admission, no target mutation, no version-control operation, no
Authority receipt, no reconciliation. Three of those are GATES rather than
promises: `test_this_module_reaches_no_settlement_verb` reads what the module
CALLS through its AST, `test_this_module_imports_no_version_control_package`
reads what it IMPORTS, and `TheIntegrationBoundaryIsVCSNeutral` reads the
identifiers of every member tuple and closed vocabulary it owns. All three read
CODE rather than prose deliberately: the commentary names those verbs and that
package on purpose, because explaining which verb a claim will earn is most of
why this boundary exists, and `source_profiles/` is the separation this one
copies.

### Verification

Focused, this leaf and the coordinator it composes:

    PYTHONPATH=src:. python3 -m unittest tests.integration.test_runtime \
        tests.integration.test_coordinator
    -> Ran 245 tests, OK

One class per acceptance clause: `WritableAccessNeedsTheLiveGrant`,
`ThePriorRuntimeIsPROVEDUnableToMutate` (every state of the manager's own axis,
positive and not, with `uncertain` named), `TheRuntimeSCLAIMIsNotASettlement`,
`TheDeliveryIsDurableAndManagerCustodied` (publication, replay, the refusal of
a second assignment, every untrusted-material case, restart adoption, and that
adopting performs no recovery), `AnInterruptionProducesAHoldAndNothingElse`,
`TheProfileIsWiringAndNotAPlan` and `TheIntegrationBoundaryIsVCSNeutral`.

Broad sweep, both phases of the host's safe parallel harness:

    PYTHONPATH=src:. python3 tools/parallel_test.py
    -> parallel source: 563 shards, 3957 tests, 6 failures, 0 errors, 3 skipped
    PYTHONPATH=src:. python3 tools/parallel_test.py --phase serial
    -> serial source: 16 shards, 235 tests, 4 failures, 13 skipped

4192 tests, 10 failures, byte-identical to the recorded baseline: five
`test_boundary_inventory` cases and one `tests.authority.test_catalog` case,
whose failing sets name `worker_manager` entries this package is not in, plus
the four Docker-engine residue cases. The `test_store` error that the first
sweep of this round caught did NOT recur here, which is consistent with it
being load-induced; it is W101621 either way.

The whitespace gate is clean, no new file carries trailing whitespace, and the
registry gate passes.

### Open, and named rather than left implicit

This leaf composes the assignment and its delivery; it does not START a
runtime. That is W101492's, which this Work blocks, and the boundary is shaped
so that leaf composes rather than widens it: a published assignment is a
document at a fixed read-only target with a digest, and a result comes back
through one closed reader.

The mount PLAN is also not composed here. `source_boundary.boundary_mounts`
and `launch.py` own how a target and these two namespaces reach a container,
and composing them would mean deciding W101492's runtime shape from underneath
it. What this boundary fixes is the two container targets, which is the part
both leaves must agree on.

## 2026-09-06 — baton.claude — the review's five findings, and the two claims underneath them

`review-2026-09-06T12-55-42Z.md` found three [P0]s and two [P1]s. All five are
corrected. 82 focused cases for this leaf (58 before), 269 with the coordinator
it composes on. Two of the findings were about SENTENCES I had written, not
only about code, so FINDING.md carries both as supersessions.

### [P0] A caller-authored dictionary is not a runtime observation

I had already learned once this round that agent quiescence is not runtime
quiescence -- and then shipped the same unsupported claim one layer out. The
witness was a document a CALLER handed in, typed member by member against the
manager's frozen vocabulary, and completely unbacked: a witness naming an
unrelated attempt as `destroyed` authorized a writer, and omitting the operand
authorized one unconditionally.

There is no witness operand now. WHICH attempt held the previous grant is the
coordinator's answer out of its own lease history; WHAT that runtime is doing is
`attempts.attempt_runtime_of`, the manager's durable row for exactly that
runtime. Absence is durable on both sides: a target with no earlier grant has
no predecessor to prove, and a predecessor the manager holds no attempt for is
a contradiction between two stores rather than a quiet "nothing was running".

**Owning the shape of a claim is not observing the fact it claims.** That is
the rule this leaves behind, and it is the same shape as W101714's -- a member
that is typed, closed and validated can still be whatever its author chose to
write.

### [P0] The attempt and the accepted profile kind were not the grant's

`compose_assignment` validated the caller's attempt id and wrote it in without
comparing it to the one the lease was granted to, so a live grant for one
attempt composed an assignment and a delivery for any other. The acceptance
boundary names an exact target, entry, ATTEMPT and fence, and three out of four
is a different boundary. It also checked only the integrator participant, so a
lease admitted for one profile kind composed a runtime for another.

Both come out of `granted_context`, a new coordinator read that returns the
live grant, the accepted entry under it and the grant it follows from ONE
relationship pass. `live_grant` is now a projection of it, which also closes a
smaller instance of the eighth W71878 review's own finding: it read the lease
and the target in two separate snapshots.

### [P1] The publication rule I inherited was that module's OLD one

The finding claimed every rule came from `exchange.py`. It came from an earlier
version of it: one fixed staging name, one unchecked `os.write`,
umask-dependent creation and `os.rename`. The reviewer reproduced all four
consequences -- a stale staging file wedged publication forever, a short write
published a truncated document as successful, a restrictive umask produced a
mode-000 file under a declared `0444` contract, and `rename` could replace a
concurrent winner.

**Copying a mechanism copies the version you read**, and a claim about lineage
is exactly the kind that stops being true without anybody editing it. The
current invariants are present and DRIVEN rather than named: unique staging
name, whole-write loop, `fchmod` on the descriptor, file sync, no-clobber
`link` with winner comparison, directory sync, and staging cleanup on every
path.

### [P1] Adoption proved neither type nor mode nor custody

`os.path.isdir` follows links. Adoption now opens both namespaces no-follow,
proves directory type and exact mode on the descriptor, and proves the
runtime-written namespace's group against the manager-minted `WorkspaceGroup`
-- which is why `adopt_delivery` takes that trusted input now.

### Verification

    PYTHONPATH=src:. python3 -m unittest tests.integration.test_runtime \
        tests.integration.test_coordinator
    -> Ran 269 tests, OK (skipped=1)

The skip is honest rather than convenient: the wrong-group adoption case needs
a second group this host's user can actually move a directory into, and it says
so instead of asserting something weaker.

New classes: `TheGrantDecidesEveryIdentityInTheAssignment`,
`PublicationIsTheINHERITEDMechanism` and `AdoptionProvesMANAGERCustody`, plus
`ThePriorRuntimeIsPROVEDUnableToMutate` rebuilt around whole scenarios -- each
case builds its own target and predecessor, because repointing a lease at
another attempt is refused by the coordinator's own journal proof, exactly as
it should be.

Broad sweep, both phases:

    -> parallel source: 567 shards, 3986 tests, 6 failures, 0 errors, 4 skipped
    -> serial source: 16 shards, 235 tests, 4 failures, 13 skipped

4221 tests, 10 failures, byte-identical to the recorded baseline. The
whitespace and registry gates pass.

The reviewer's own probe at `/tmp/w101490-review.py` CANNOT run as written: it
imports `witness`, the caller-authored quiescence door, and that door is gone
rather than fixed. `/tmp/w101490-recheck.py` drives all five findings at the
surfaces that replaced them and prints, in order: the wrong attempt refused and
the right one accepted, the wrong profile kind refused and the accepted one
returned, the caller witness door absent as a `TypeError`, a running
predecessor refused and a destroyed one accepted, publication surviving a stale
staging file under a `0o777` umask at mode `0o444`, and a moved result-namespace
mode refused.

## 2026-09-06 — baton.claude — the re-review: a proof only as deep as its components

`review-2026-09-06T13-13-54Z.md` accepted the three [P0]s and the publication
mechanism and found two [P1]s and one [P2]. All three are corrected. 91 focused
cases for this leaf (82 before), 284 with the coordinator.

### [P1] `O_NOFOLLOW` binds the FINAL component and nothing else

The previous round's custody correction was right about the leaves and blind
about their parent. Adoption opened `<root>/integration/assignment` and
`<root>/integration/result` no-follow, at exact modes, on their own
descriptors -- and said nothing whatever about `integration`. A symlink at that
name was followed, so an arbitrary correctly shaped tree behind it was reported
as this manager's own delivery; a root whose mode had drifted was adopted too.

This is the SAME finding as the first review's, surviving in the one component
that correction did not reach. The fix is the rule applied to every component
rather than to the last one: the delivery root is opened no-follow and proved
at its established mode, and both namespaces are opened relative to ITS
descriptor. Its mode is now established with `chmod` rather than requested
through `makedirs`, because a umask decides what a request gets -- a case
drives that under `0o077`.

**A path proof is only as deep as its components.** That is the sentence I did
not have last round.

### [P1] The public contract described a document no function returns

`WITNESS_MEMBERS` stayed exported, declaring `attempt_id`, `execution_runtime`
and `evidence`, while the manager-derived helper that replaced the caller
document returns two members. `evidence` was the CALLER's word for why it
believed itself; the manager's row needs no such member, because the row IS the
evidence. It is `OBSERVED_RUNTIME_MEMBERS` now, exactly what
`prior_runtime_witness` answers with, and `OneObservationDocumentAndOneAnswer`
asserts that equality instead of trusting it -- including that the old name is
gone from the module rather than kept as a compatibility surface for a
candidate that has never been accepted.

### [P2] Two present-tense claims that had stopped being true

The publication docstring still specified `rename` and syncing "the rename",
which the previous round had already replaced with no-clobber `link`; and the
module header still said "no second file transport" where this record had
narrowed that to no second transport MECHANISM. Both now describe what the code
does, with the history in FINDING. Contradictory present-tense instructions
beside corrected code are how the next reader learns the wrong rule -- and this
is the second round in which stale prose was a finding, so it is worth naming
rather than just fixing.

### Verification

    PYTHONPATH=src:. python3 -m unittest tests.integration.test_runtime \
        tests.integration.test_coordinator
    -> Ran 284 tests, OK (skipped=1)

New classes: `AdoptionProvesTheROOTAsWellAsItsChildren` (the exact
intermediate-symlink reproduction, a non-directory root, a moved root mode, the
umask case, and that a sound delivery still adopts and absence is still an
ordinary answer) and `OneObservationDocumentAndOneAnswer`.

Broad sweep, both phases:

    -> parallel source: 571 shards, 4006 tests, 6 failures, 0 errors, 4 skipped
    -> serial source: 16 shards, 235 tests, 4 failures, 13 skipped

4241 tests, 10 failures, byte-identical to the recorded baseline. The
whitespace and registry gates pass.

The reviewer's `/tmp/w101490-rereview.py` is a counterexample suite, so the
correction BREAKS it: three of its seventeen cases now error --
`test_a_symlinked_integration_root_is_currently_adopted`,
`test_a_moved_integration_root_mode_is_currently_adopted` and
`test_the_exported_witness_shape_does_not_describe_the_answer` -- because the
first two now refuse and `WITNESS_MEMBERS` no longer exists. The other fourteen
still pass.

## 2026-09-06 — baton.claude — the third review: bookkeeping, and a correction to my own evidence

`review-2026-09-06T13-33-05Z.md` accepted every runtime-safety and custody
finding and left two [P2]s. Both are corrected, and one of them is a correction
to what an earlier entry in THIS file claimed.

### [P2] The export contract had two entries for one replacement

`runtime.__all__` listed `OBSERVED_RUNTIME_MEMBERS` twice -- 37 names, 36 of
them distinct -- my own slip while removing the superseded `WITNESS_MEMBERS`.
It is the same boundary as the finding it came from: replacing one stale public
shape should leave ONE coherent export. The duplicate is gone and
`test_the_export_contract_is_one_closed_list` compares the sequence with its
distinct members and proves every exported name resolves, so a closed list with
a repeat in it fails rather than being read past.

### [P2] Three durable records disagreed with the code beside them

- The delivery commentary and the test class called this the THIRD delivery,
  while the module introduction and FINDING had already established that
  `exchange.py` is the third -- after `inputs` and `workspace` -- and this is
  the fourth. Both now say fourth.
- PLAN items 3 and 4 were still marked "changes requested" and "corrections
  required" while item 5 and the implementation said both were done. They are
  marked complete.
- FINDING carried the "proof that stops at the last component" section TWICE. I
  appended it twice: a first script failed part-way and I re-ran a repaired one
  without noticing the first write had landed. The file is append-only, so the
  duplicate stays and is now LABELLED as a duplicate -- two identical
  correction sections read as two chronological rounds, which is a worse lie
  than the duplication.

### The correction to my own verification claim

**A previous entry in this file said `/tmp/w101490-recheck.py` still drives the
prior five findings. That was false when I wrote it.** W101714's accepted
fixture moved `profile_kind` from `repository` to `git`, and the probe
hard-codes its own profile, so every setup was rejected on the profile-kind
binding -- the very check it claims to demonstrate -- and it crashed before
reaching the publication and adoption lines. I reported a probe's output
without re-running it after a sibling Work changed the value it depends on.

The probe now takes `PROFILE_KIND` from the fixture rather than spelling a
word, and it runs to completion again:

    PYTHONPATH=src:. python3 /tmp/w101490-recheck.py
    p0-attempt-not-the-grant-s     REFUSED  policy.denied
    p0-attempt-control             ACCEPTED attempt-1
    p0-profile-kind-not-admitted   REFUSED  policy.denied
    p0-profile-kind-control        ACCEPTED git
    p0-caller-witness-door         RAISED   TypeError (the door is gone)
    p0-running-predecessor         REFUSED  policy.denied
    p0-predecessor-control         ACCEPTED writable
    p1-stale-staging-and-umask     ACCEPTED True
    p1-published-mode              0o444
    p1-moved-result-mode           REFUSED  policy.denied

The lesson is narrow and I would rather write it down than repeat it: A PROBE
IS EVIDENCE ONLY IN THE RUN THAT PRODUCED IT. Two Works sharing a fixture means
either can invalidate the other's retained evidence, and re-running is cheaper
than the claim being wrong in a durable record.

### Verification

    PYTHONPATH=src:. python3 -m unittest tests.integration.test_runtime \
        tests.integration.test_coordinator
    -> Ran 287 tests, OK (skipped=1)

Broad sweep, both phases:

    -> parallel source: 571 shards, 4009 tests, 6 failures, 0 errors, 4 skipped
    -> serial source: 16 shards, 235 tests, 4 failures, 13 skipped

4244 tests, 10 failures, byte-identical to the recorded baseline. The
whitespace and registry gates pass.

## 2026-09-06 — baton.claude — the fourth review: I marked history in place

`review-2026-09-06T13-44-19Z.md` accepts every implementation and test
correction and requests one record-policy fix. No production or test byte
changed in this round.

### The finding, and it is a policy I got backwards

The third review asked me to mark the duplicated FINDING section. I marked it
by inserting a note UNDER THAT SECTION'S OWN HEADING -- which edits an earlier
chronological entry in place, and is exactly what this repository's append-only
rule forbids. AGENTS.md carves out no exception for an edit that is small and
helpful, and the reason is the one this case demonstrates: an annotation woven
into an old entry reads as though it had always been there, so the record stops
being able to say when anybody knew what.

The inserted note is removed and the earlier section is back to the bytes it
was written with. The clarification is now an appended dated section after the
current history, naming both headings, stating that they are one correction
round rather than two, and recording the cause.

### And the clarification's own first draft was wrong

I wrote that the two sections carry "identical text". While restoring them I
diffed the two blocks and they are NOT byte-identical: I had reworded a few
sentences between the failed script and the repaired one, so the file holds two
DRAFTS of one correction. No sentence in either contradicts the other and
neither is a second decision -- the differences are wording -- but "identical"
was a claim I made before checking, in the same round whose whole subject is
records that say things nobody verified. The appended clarification says so.

**A LATER ACCOUNT IS APPENDED, NEVER WOVEN INTO AN EARLIER ONE**, and the
narrower lesson underneath it is the one this round keeps teaching me in
different costumes: check the bytes before describing them.

### Verification

No code changed, so no broad sweep was spent on this round. The focused gate
was run to show the tree is where the fourth review left it:

    PYTHONPATH=src:. python3 -m unittest tests.integration.test_runtime \
        tests.integration.test_coordinator
    -> Ran 287 tests, OK (skipped=1)

The whitespace gate is clean.
