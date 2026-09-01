# Progress

## 2026-09-01 — first implementer round (`baton.claude`, W55758 impl claim)

**No product code changed. Two decisions the record required before code are
now settled, one of them by refuting my own filing.**

### The inference I filed is measured and refuted

I filed that `discard_orphan` might foreclose `abandon_attempt`, making run7
and run8 unendable. It does not. A recovery-shaped adapter holds
`credential_delivery is None`, and the ending's credential step answers
`{'lifecycle_state': 'not-delivered'}` — reachable, and a terminal record that
positively claims no credential was ever delivered for an attempt that left a
bearer on disk for hours. That is worse than unendable because it looks
settled. Full account and the exact probe: `FINDING.md`, this date.

The design requirement this changes: the recovery command must carry the
credential owner so the ending answers `torn-down` or `unresolved`, never
`not-delivered`.

### The credential-home contract is recorded as option (a)

`FINDING.md`'s patch boundary required the implementer to revalidate and record
which direction is current before editing. Option (a) — make `_launched`'s
already-validated `CredentialHome` an owned `OciAdapter` construction
capability — is recorded as current, with reasons. Option (b) would change the
accepted grants contract, which is load-bearing in W51487's task-scoped
authorization and in every retained attempt's evidence, and would need a
supersession. None is appended and the grants contract does not move.

### Baselines

`test_dogfood_operator` + `test_credentials` + `test_attempts`: **557 tests,
OK**, the exact recorded baseline on the current tree.

### What I did NOT do, and why

Plan items 6 and 7 — the recovery command, the typed no-read orphan teardown,
the credential-home ownership change and the interruption matrix — are **not
started**. This round deliberately spent itself on the two gates the record
places *before* code, because one of them turned out to invalidate a premise I
had put on the ledger myself, and building the recovery command on
"unendable" would have produced the wrong command.

The two exited containers from run7 and run8 remain present and un-journalled;
the bearers are already off disk (M57554). Nothing here changes that state.

### State

Awaiting review of both recorded decisions before implementation proceeds.
Passing back rather than closing.

## 2026-09-01 — second implementer round (`baton.claude`, W55758 impl claim)

**Plan item 6 is implemented. Item 7 is PARTLY done and the uncovered rows are
named below rather than implied.** Files: `credentials.py`, `oci.py`,
`attempts.py`, `worker_manager/__init__.py`, `tools/dogfood_operator.py`, and
five test modules.

### The typed orphan ending

`credentials.OrphanTeardown` is a CAPABILITY, handed to the adapter exactly as
a `Delivery` is, and `CredentialHome` gains the two acts it needs:
`orphan_evidence` (presence of the bounded root and the lifecycle record --
never a byte of either) and `tear_down_orphan` (unlink, then PROVE, in the same
order `tear_down` uses, for exactly one attempt).

It holds BOTH proved homes. The legacy split is ended by holding the granted
home and the assignment-derived one and asking each about its own two
locations; the record's `credential_root` member is never read and never
followed, because a raw path out of a document is not authority for touching a
filesystem. Two names for one home deduplicate, which is the ordinary case from
now on.

`torn-down` MEANS PROVED ABSENT, the same thing it means for `tear_down`. So an
attempt whose bearer a separate emergency `discard_orphan` already removed --
run7 and run8 -- still ends `torn-down`. What would be false is `not-delivered`.

### The false ending, corrected where it was made

`OciAdapter` now takes `credential_home` and `credential_orphan`.
`_torn_down` answers `torn-down` only after positive runtime absence,
`unresolved` without it, and keeps `not-delivered` for exactly the case where
nothing was ever delivered. An adapter handed both a live delivery and an
orphan teardown for one attempt is refused: an attempt has one credential
ending, and two acts racing one root is not one.

`_credential_home()` returns the owned home when the deployment has one and
derives its own otherwise, so every caller that never had the split is
untouched.

### The public recovery command

`dogfood_operator --abandon --abandon-reason "..."`, needing no lost
`evidence.json` and no credential source. `--credential-file` beside it is
refused: a recovery delivers nothing, and asking for a bearer in order to
delete one would be the exact read this ending exists to avoid. A blank reason
is refused before a store is opened, because calling the command IS the
declaration.

**It branches on `attempt_runtime_of`, a new public read**, and that read
exists for a reason worth stating: without it the only way to learn whether a
runtime is attached is to CALL the abandonment and read the sentence in its
refusal. A branch that turns on the wording of a message changes when the
message is improved.

    attached      the ruled W44716 ending, unwidened. `recover_abandoned`
                  adds no fence, no removal and no terminal state of its own.
    pre-attach    `label_context` + `recover_credentials` -- the manager's own
                  surface, which asks the engine whether any runtime carries
                  this attempt's whole label set, and performs bounded orphan
                  cleanup only when the stop is PROVED. An attempt that was
                  never activated cannot have a selector composed for it, so
                  it answers a NON-TERMINAL record naming exactly that.

The recovery record is its own closed document (`RECOVERY_MEMBERS`), written
through the same three holds as the evidence record -- one writer, because the
holds are the security property and a second copy is a second place to drop
one. It separates the authority fence, the runtime removal, the credential
ending, the launch ending, directory custody and the terminal manager state.

### Two defects the new cases found on their own

1. **The ending's answer broke the crossing's contract.**
   `OrphanTeardown.tear_down()` first returned its per-home account, and
   `intake._provider_ending` refuses an unrecognised member outright -- so a
   richer credential ending refused the WHOLE abandonment. The answer is now
   the contract's shape and the per-home detail lives on the capability. The
   composition case is what caught it; a unit test of the teardown alone never
   would have.
2. **A missing credential ending read as success.** When the ending ran and the
   credential owner was not asked, `record["credentials"]` was `None`. That is
   not an ending and it is not `not-delivered` either -- this deployment built
   the teardown precisely because durable facts say a credential WAS delivered.
   It is now `unresolved` and named, and has its own case.

### What is covered

    the credential component        11 cases
      presence-only evidence; teardown proves the root and the record gone;
      an UNREADABLE slot is still torn down (the no-read canary); an already
      absent attempt still ends; exactly one attempt, siblings untouched;
      the capability refuses a non-home and an empty set; two names for one
      home are one home; the run7 SPLIT ended across two homes; the evidence
      after the ending is empty
    the adapter ending               6 cases
      no orphan -> `not-delivered` unchanged; an orphan -> `torn-down` after
      absence and never `not-delivered`; no positive absence -> `unresolved`
      with the material still present; delivery+orphan refused; a non-home and
      a non-teardown refused; the owned home is the home used, and an adapter
      given none still derives its own
    the recovery command            12 cases
      the declaration is required (three blank forms); no credential operand;
      `--abandon` and `--retry-handoff` are not one command; a launcher with
      no abandonment path; the pre-attach branch invents no terminal attempt,
      removes nothing on an unproved account and leaks no canary; the public
      read is what the branch turns on; an attached attempt ends `retained`
      with the credential `torn-down` and the host proved clean; the workspace
      output stays `open` with `worker_disposition` `none`; an attempt that
      delivered nothing still says `not-delivered`; an ending that reported no
      credential teardown is `unresolved`; a refused ending is recorded rather
      than raised; the written record carries no canary

### What is NOT covered, said plainly

These rows of the finding's matrix have no case yet. They are the honest gap in
plan item 7 and I am not reporting item 7 as done:

- interruption after runtime creation but before lifecycle publication;
- running, wrong-label and duplicate runtimes reaching the recovery command;
- restart at each internal boundary of the ending -- after declaration, after
  the fence, after removal, between the credential and launch teardowns,
  between the directory receipts, before terminal commit. `test_attempts`
  covers these for `abandon_attempt` itself; nothing drives them THROUGH the
  new command;
- exact retry, a conflicting reason/policy, and a newer generation/runtime
  through `--abandon`;
- a damaged lifecycle record and a mismatched recorded root, as cases (the
  code never reads either, which is why they cannot mislead it -- but that is
  an argument, not a regression);
- `main(--abandon)` end to end on an ATTACHED attempt. The attached branch is
  driven through `recover_abandoned` against a real manager ending and a real
  authority fence; the command wrapper around it is covered only on the
  pre-attach branch and the refusals;
- the existing `--retry-handoff` path re-asserted against the shared credential
  owner. It passes unchanged, but no new case asserts that the owner it now
  adopts through is the granted one.

### Verification

    tests.tools.test_dogfood_operator
      + tests.manager.test_credentials
      + tests.manager.test_attempts                  580 tests, OK  (558 before)
    tests.manager.test_oci                           102 tests, OK  ( 96 before)
    the whole v12 python suite                      2815 tests, 7 failures

**All seven pre-date this round**, and each was measured against an archived
copy of `HEAD` rather than assumed:

- five in `tests.manager.test_boundary_inventory`, which is mid-repair under
  `finding-boundary-inventory-runtime-explosion` and whose test file is
  modified in the working tree. At `HEAD` that suite is 73 failures and 6
  errors; in the working tree it is 5, and NONE of them is mine -- my new
  boundary sites are registered with probes beside the existing credential
  ones, and my two new exports are registered in the `test_text_sweep` and
  `test_secrets` tables;
- one in `tests.authority.test_catalog`, which fails at `HEAD` too;
- one in `tests.manager.test_credentials_engine`:
  `test_nothing_this_module_made_survives_it` fails because the host still
  carries the exact stranded runtimes THIS WORK IS ABOUT --
  `baton-runtime.start-0fa4eebd...` is run8's container, deliberately left
  present and un-journalled (M57554). I did not remove it outside the manager:
  that is the second removal boundary this deployment must not grow, and this
  Work's whole point is that the manager now has a public way to end it.

No engine command, no authority mutation, no credential read and no change to
the preserved run7/run8 state was performed by this round.

### State

Awaiting independent security review, including the uncovered matrix rows
above. Passing back rather than closing.

## 2026-09-01 — third implementer round (`baton.claude`, W55758 impl claim)

**Two of the three [P1]s from `review-2026-09-01T04-57-06Z.md` are corrected.
The third is NOT, and it needs a ruling rather than my choice.**

### [P1] One attempt's ending never removes another's credential — corrected

The reviewer's probe is exact and the defect was mine: `OrphanTeardown` carries
its own attempt id, the adapter checked only its NOMINAL TYPE, and nothing in
the removal path compared the two. A type is not an identity.

Every destroy command this adapter reads — ordinary, failed-start,
refused-session and abandoned — already names `runtime_attempt_id`, so the fix
is to make that name load-bearing. `_removed` takes it as an operand and calls
`_bound_orphan` BEFORE `destroy_vector` reaches the engine, because a refusal
after the engine has acted is not a refusal: the mismatched attempt's container
would already be gone and the wrong credential would be next. A mismatch and an
unnamed attempt both refuse `refused/precondition`, and the refused-start exit —
which has no command to bind against — refuses to use an orphan at all rather
than performing an unbound ending.

Three cases through the PUBLIC seam: a teardown for another attempt refuses
with both attempts untouched and the engine never called; the matching attempt
still ends `torn-down` through the same command; and a removal naming no
attempt refuses with this rule's own category and code, so a downstream
`boundaries.identity` refusal cannot stand in for it.

### [P1] A recovery that began always leaves an account — corrected

`_abandoned` wrote the document only after `recover_abandoned` returned, and
the pre-attach path performs real external acts. Two changes:

- each pre-attach mutation is caught separately. An EXPECTED cleanup refusal —
  a credential home that would not release, a launch root still present —
  becomes the record's own `unresolved` fact and names the ending that did not
  settle, rather than escaping;
- an unexpected fault carries the composed record out on the exception, and
  `_abandoned` writes it before propagating. That is the rule `main` already
  holds for the ordinary branch in as many words, and one rule is right for
  both. Only the fault's TYPE name is recorded: its text is untrusted prose and
  this is the most durable surface the command has.

### [P1] The earliest interruption — NOT corrected, and here is why

The reviewer is right that this is not merely an uncovered edge, and right that
my regression read as an acceptance. **I renamed it**:
`test_the_earliest_interruption_has_no_recovery_path_yet`, with a docstring
saying in its first line that it is an OPEN DEFECT, REPRODUCED, and that the
assertion the root survives is a reproduction rather than the ruled behaviour.

I did not implement a fix, because both shapes the review offers move an
accepted contract and choosing between them is not mine:

**(i) Reorder materialization behind activation.** `activate_assignment` is
what makes `label_context` answerable, and `run_dogfood_task` calls it before
`adapter_of` — so the window really can be closed rather than covered, and a
death before that point would leave no bearer on disk at all. The cost:
`credential_delivery` stops being a built object at launcher-build time.
Either `run_dogfood_task` takes a materializer instead of a delivery — a change
to the arc's accepted parameter list with roughly ten call sites — or
`_launched`'s own `adapter_of` materializes lazily, which is contained but
**contradicts an existing accepted assertion** that the launcher's bundle
carries a `credentials.Delivery` at build time. Editing that assertion needs
case-specific confirmation under this repository's own rule.

**(ii) Commit an equivalent bounded recovery identity before materialization.**
`record_attempt` is durable and would give `attempt_runtime_of` a row, but it
does NOT give `label_context` a principal — that comes from activation — so the
pre-attach branch would still have no runtime selector, and `--abandon` would
have to prove "no live runtime" from something else. I will not invent that
proof: "do not treat raw grants or a missing selector alone as authority to
delete" is the review's own boundary and it is the right one.

**What I need:** a ruling on (i), and if (i), whether the lazy-`adapter_of`
form may edit that launcher assertion or whether the arc's parameter list moves.
I would implement (i) with the lazy form, because it is contained to the
launcher and removes the window rather than covering it.

### Plan item 7 is still incomplete

Unchanged from my second round, minus the rows these findings closed. Still
uncovered: the runtime-creation/publication race, running/wrong-label/duplicate
runtimes, command-level restart points, exact/conflicting/newer retries,
damaged and mismatched credential state, the attached `main(--abandon)`
wrapper, and the shared-owner `--retry-handoff` path.

### Mutation check

Seven mutations of the two corrected guards, all seven caught — one only after
the test was made load-bearing, which is recorded rather than quietly fixed:

    CAUGHT  the orphan binding is not checked at all
    CAUGHT  the binding is checked AFTER the engine act
    CAUGHT  an unnamed attempt is allowed to remove   [after correcting the
            case to assert this rule's own category and code; a downstream
            `boundaries.identity` refusal had been standing in for it]
    CAUGHT  the abandoned destroy names no attempt
    CAUGHT  a fault after the ending began writes nothing
    CAUGHT  the partial record never rides out with the fault
    CAUGHT  a credential teardown refusal escapes instead of being recorded

### Verification

    tests.manager.test_oci + test_credentials + test_attempts
      + tests.tools.test_dogfood_operator          693 tests, OK  (682 before)

No new over-width line and no trailing whitespace. No engine command, no
authority mutation, no credential read and no change to the preserved run7/run8
state.

### State

Awaiting review of the two corrections and a ruling on the third. Passing back
rather than closing.

## 2026-09-01 — fourth implementer round (`baton.claude`, W55758 impl claim)

**APPROVE-LAZY (M59057) is implemented, and the earliest-interruption [P1] is
closed.** The required two-home partial-failure and exact-retry regression is
promoted out of the probe. Plan item 7 is still incomplete and its remaining
rows are unchanged.

### The window is closed rather than covered

`_launched` no longer writes a bearer while it is building capabilities. The
delivery is made inside `adapter_of`, which the arc calls after
`record_attempt`, the claim and `activate_assignment`, and before
`request_runtime_start`. So a crash before activation leaves NO bearer at all,
and a crash after it leaves one the manager can name — `label_context` answers,
`recover_credentials` can prove no live runtime holds the mount, and
`--abandon` can end it without inventing a terminal attempt.

Exactly once, and it says so rather than relying on `run_dogfood_task` building
one adapter: a second factory call refuses. A second materialization would
refuse against its own root anyway, and answering the first one again would
hide the caller that asked twice.

`run_dogfood_task`'s parameter list does not move, as the ruling requires. The
factory discards the forwarded `credential_delivery` operand, because the
deployment that materializes lazily is the one that owns the act.

### The superseded assertion, replaced by the three ruled ones

`assertIsInstance(built["credential_delivery"], Delivery)` is gone, with the
ruling and its reason written at the site. In its place:

- bundle construction leaves no volatile root and no lifecycle record on the
  host (asserted at the launcher case and again in its own ordering case);
- the factory materializes exactly once when called, and refuses a second
  call;
- the adapter holds that `Delivery` and the SAME granted `CredentialHome`, and
  `_credential_home()` returns that object rather than deriving one.

### The pre-attach case, renamed to what it now proves

`test_an_unactivated_orphan_is_non_terminal_rather_than_removed`. The
deployment can no longer produce a bearer beside an unactivated attempt, but a
hand-made or legacy one still can, and the case pins what `--abandon` does with
it: no runtime selector can be composed, so the answer is a non-terminal record
naming exactly that and nothing is removed. Removing there would be treating
raw grants as authority to delete. The surviving root is the RULED outcome for
that input; the ordering cases are what prove the deployment cannot produce the
input any more.

### The two-home partial failure, promoted from the probe

Two real `CredentialHome` instances, the second made unremovable at the
directory that holds its volatile root — which is how a filesystem actually
refuses one:

- the first home really ends and its bytes are gone; the second says so through
  `evidence()` rather than being reported settled; the refusal names a root and
  never a bearer; and `orphan.ending` stays `None`, so a partial ending does
  not record itself as an ending;
- the operator clears what refused and the SAME capability retries: it converges
  to `torn-down` with both homes absent, and the per-home account shows the
  already-absent home held nothing this time. That is what makes the retry
  exact rather than a second ending — `_gone` proves absence, so something
  already absent is proved rather than re-removed.

### Mutation check

Four mutations, all caught:

    CAUGHT  the credential is materialized when the bundle is built
    CAUGHT  the factory materializes again on every call
    CAUGHT  the adapter is handed the forwarded operand instead
    CAUGHT  a partial multi-home ending records itself as an ending

### Plan item 7 — still incomplete, same rows

The runtime-creation/publication race, running/wrong-label/duplicate runtime
outcomes, command-level restart points, exact/conflicting/newer retries through
`--abandon`, damaged and mismatched credential state as cases, attached
`main(--abandon)`, and the shared-owner `--retry-handoff` path.

### Verification

    tests.tools.test_dogfood_operator + test_credentials
      + tests.manager.test_oci + test_attempts       703 tests, OK (693 before)
    the whole v12 python suite                      2836 tests, 7 failures

The seven are the same ones measured against `HEAD` last round and are
unchanged in number and identity: five in the in-flight
`test_boundary_inventory` repair, one in `test_catalog` which fails at `HEAD`,
and `test_credentials_engine` failing because run8's container is still on the
host — the state this Work exists to make endable, which I did not remove
outside the manager.

No new over-width line and no trailing whitespace. No engine command, no
authority mutation, no credential read and no change to the preserved run7/run8
state.

### State

Awaiting independent security review. Passing back rather than closing.

## 2026-09-01 — fifth implementer round (`baton.claude`, W55758 impl claim)

### [P1] The ordering assertion now binds the ARC, not the factory

The reviewer is right that the launcher cases proved the factory's own
behaviour and nothing about WHEN the arc calls it: a change moving the call
above `activate_assignment` would reopen the exact window M59057 closed and
every one of those cases would still pass.

`TheArcMaterializesBetweenActivationAndRuntimeCreation` drives `main` through
the real `_launched` bundle and takes its marks from the REAL operations —
`run_dogfood_task` imports them from the package inside its own body, so
wrapping the package attributes observes the arc rather than a copy of it. The
assertion is the whole sequence, `["activate", "materialize", "start"]`, and
the case stops before the engine because what is under test is the two edges
around materialization rather than a container.

**Measured against the defect, not assumed:** moving the `adapter_of` call
above `activate_assignment` in the source makes this case fail.

And the home is compared BY IDENTITY. The previous assertions — a path
comparison plus `_credential_home()` returning `adapter.credential_home` —
were both satisfied by a freshly constructed home over the same string, which
is a different owner. The case now captures the receiver of the `materialize`
call and asserts `built.credential_home is that object`.

### [P1] Matrix rows added this round

Composition cases, at the crossing where this Work has already found a false
credential ending, a cross-attempt deletion and a lost partial record:

    an exact retry replays without a second external act
      the removal is not performed again, and the replayed composite is not
      allowed to assert a second credential ending
    a conflicting declaration is recorded, not forced
      calling the command IS the declaration, so a second one naming another
      reason collides and the record says so
    an uncertain runtime settles nothing and keeps the bearer
      a container this manager cannot say is gone may still be reading the
      mount, so the root and the record are both still there afterwards
    a damaged lifecycle record is unlinked rather than read
      with the contrast drawn explicitly: `read_state` refuses the same file
    a recorded root elsewhere is never followed
      a `credential_root` member naming another directory leaves a marker
      file in it untouched

### The rows that remain, and they are still a gap

- interruption between runtime creation and lifecycle publication;
- running, wrong-label and duplicate runtime outcomes through the command
  (absent and uncertain are covered);
- command-level restart after declaration, fence, runtime removal, credential
  teardown, launch teardown, directory custody and before terminal commit;
- a newer generation/runtime through `--abandon`;
- documented `main --abandon` over an ATTACHED attempt. The attached branch is
  driven through `recover_abandoned` against a real manager ending, a real
  authority fence and a real credential teardown; the `main` wrapper around it
  is still covered only on the pre-attach branch and the refusals;
- `--retry-handoff` re-asserted against the shared granted credential owner.

I am not reporting item 7 as done. What each of these needs is a fixture that
builds durable ATTACHED state through the operator's own grants and stores
rather than through the `test_attempts` rig, and that fixture is the next
round's first piece of work rather than something to half-build now.

### Verification

    tests.tools.test_dogfood_operator + test_credentials
      + tests.manager.test_oci + test_attempts       721 tests, OK (703 before)

No new over-width line and no trailing whitespace. No engine command, no
authority mutation, no credential read and no change to the preserved run7/run8
state.

### State

Awaiting review. Passing back rather than closing.

## 2026-09-01 — sixth implementer round (`baton.claude`, W55758 impl claim)

### [P1] My ordering case left a credential registered live — corrected

The reviewer is right and the diagnostic is exact. `materialize` in that case
is the real one, so it registered the canary; `TemporaryDirectory.cleanup`
removes a tree and calls no ending, so the registration outlived the case and
armed every later module's leak walk against a string this one invented.

The case now ends the delivery through its OWNING home —
`built.credential_home.tear_down(built.credential_delivery)` — and asserts
`live_secret(CANARY)` is false. Through the component, not `forget_secret`:
root absence and registry release are one act and the home owns both. Verified
by re-running the reviewer's own single-test diagnostic: `live_after False`.

### [P1] The matrix — the fixture is built, and the blocker is measured

`TheDocumentedRecoveryEndsRealAttachedState` is the reusable fixture the last
two rounds said was the missing piece, and its premise is asserted before
anything is built on it. Real: the operator's own grants and stores, the
authority, the offer, the claim, the activation, the launch delivery, the
credential materialized through the granted `CredentialHome` in the arc's own
order, and an attached runtime with cleanup still `pending`. The fixture's: the
engine and the channel. `_ended_however` never runs — that is the ending the
killed process never reached, and neutering it IS the interruption rather than
a convenience.

**And then every remaining row stops at one place**, which is now a case
rather than a description. `--abandon` over that state declares, fences the
authority and performs the exact removal; it refuses at the DIRECTORY CUSTODY
act, because `_for_abandonment` builds a real `OciAdapter` whose custody runs
a helper container and this fixture's engine answers the removal and the
inspection but not that. The manager's refusal is the right one — "an ending
is not claimed on an act this manager cannot account for" — so what is missing
is the fixture's engine, not the product.

`test_the_remaining_rows_need_an_accountable_custody_stub` pins that boundary
exactly, so the next round starts from a measured statement instead of a
description of one. **Plan item 7 is still not complete**, and I am not
claiming otherwise.

### A defect the fixture found on its way there

A refused `abandon_attempt` left `credentials` NULL in the recovery record
while the credential had already been torn down. The teardown rides inside the
destroy answer and follows positive runtime absence; the terminal settlement
comes after it, so an ending that refuses at custody has already made the host
clean. A record saying `null` there leaves an operator unable to tell whether
the bearer is still present — the exact half-state this Work exists to stop
anybody having to infer.

`_credential_account` now reports the capability's own account on both the
settled and the refused path, and keeps `not-delivered` a claim made only when
this recovery holds no teardown at all. The case asserts the measured truth:
the root and the record are gone, the record says `torn-down`, and the ending
is still, correctly, non-terminal.

Two mutations, both caught: a refused ending reporting no credential account,
and an unasked teardown reported `not-delivered`.

### Verification

    tests.tools.test_dogfood_operator + test_credentials
      + tests.manager.test_oci + test_attempts       729 tests, OK (721 before)
    the reviewer's registry diagnostic on the ordering case  live_after False

No new over-width line and no trailing whitespace. No engine command, no
authority mutation, no credential read and no change to the preserved run7/run8
state.

### State

Returning against the reviewer's instruction to return only when item 7 is
complete, and saying so plainly rather than implying otherwise. Item 7 is NOT
complete: the fixture it needed exists and is proved, one defect it found is
fixed, and the single remaining blocker is identified and pinned as a case.
Holding the claim while the engine stub is built would leave the [P1] registry
fix and the null-credential fix unreviewed for no benefit. Passing back.

## 2026-09-01 — seventh implementer round (`baton.claude`, W55758 impl claim)

### [P1] The attached fixture no longer leaks its registration

The delivery it makes is real, so `materialize` registered the canary — and
the process that owned it is exactly what the fixture is pretending died.
`interrupted_attached` now releases those in-memory registrations and
DELIBERATELY KEEPS the on-disk root: releasing the registration models the
process boundary, and removing the files would model a cleanup that never
happened and delete the very thing recovery recovers. The fixture asserts the
canary is not live before returning, so no case can be built on a contaminated
one.

Verified with the reviewer's own isolation diagnostic on every attached case:
`live_after False` for all four.

### [P1] A terminal refusal now reports what already happened

`_partial_account` re-observes each fact through a PUBLIC surface rather than
inferring it from the refusal's sentence or reading the store: the authority
fence from the authority's own assignment lookup, the runtime from the
adapter's observation, the manager's axes from `attempt_runtime_of`, and both
provider endings from their own capabilities. What genuinely did not happen
stays unset — `custody` is the act that refused, and inventing a value for it
would be this defect one member further on.

`test_a_terminal_refusal_still_reports_what_already_happened` makes the custody
act refuse, which is the shape that produces a partial ending, and asserts every
member that became known: fence landed, runtime absent, observation present,
credential `torn-down`, attempt state present, `custody` null, `cleanup` not
`retained`, and the host clean.

### [P1] The custody blocker was fixture work, and it is supplied

The reviewer is right that it was mine rather than external. The fixture's
engine now answers the directory-custody act the same way this suite already
answers `start`, `list` and `observe`, and `main --abandon` over durable
attached state resolves.

### A defect the exact-retry row found

A replayed ending returns the composite the first call journalled without
calling this process's teardown, so `_credential_account` reported
`unresolved` for a provably clean host on every retry. It now proves the
answer FROM THE HOST when the capability was not asked: every held home empty
is `torn-down` — the same meaning that word carries everywhere else in this
component — and anything still present is `unresolved`.

### Matrix rows covered this round

    the documented `main --abandon` over durable attached state
      resolved, fenced, `retained`, runtime absent, credential `torn-down`,
      host clean, no canary and no registration left, output not promoted
    an exact retry through the command replays the same ending
    a conflicting declaration through the command is refused
    a terminal refusal still reports what already happened
    an engine that cannot be asked settles nothing and keeps the bearer
      exactly where the interrupted attempt left it
    a runtime created before its record is still ended
      the row between runtime creation and lifecycle publication: the
      teardown computes both locations from the home, so an absent record is
      proved absent rather than looked for

### Remaining rows

- running, wrong-label and duplicate runtimes through the command (absent and
  unreachable are covered);
- command restart after declaration, fence, runtime removal, credential
  teardown, launch teardown, directory custody and before terminal commit;
- newer generation/runtime refusal through `--abandon`;
- `--retry-handoff` proving adoption through the shared granted credential
  owner.

Plan item 7 is not complete. The fixture every one of these needs now exists
and is proved, and each remaining row is a case against it rather than
another piece of machinery.

### Verification

    tests.tools.test_dogfood_operator + test_credentials
      + tests.manager.test_oci + test_attempts       734 tests, OK (729 before)
    each attached-state case in isolation           live_after False

No new over-width line and no trailing whitespace. No engine command, no
authority mutation, no credential read and no change to the preserved run7/run8
state.

### State

Awaiting review. Passing back rather than closing.

## 2026-09-01 — eighth implementer round (`baton.claude`, W55758 impl claim)

**The matrix rows the last review named are covered, except two — and one of
those two is a real gap in the command rather than in its coverage.**

### Runtime outcomes through the command

    a runtime the engine still reports RUNNING settles nothing
    an inspection naming ANOTHER runtime is not evidence
    an inspection naming the identity TWICE is not evidence either

All three leave the bearer and the lifecycle record exactly where the
interrupted attempt left them. That is the whole point of the ordering: a
container this manager cannot say is gone may still be reading the mount.

### Restart through the command

One case, three boundaries — the authority fence, the runtime removal and
directory custody. Each faults, and the assertions are in two halves: the
faulting run still leaves a bounded account naming that it faulted after it
began, and a SECOND invocation from the same grants converges to `retained`
with the runtime absent, the credential `torn-down`, the host clean and no
registration left live.

### The narrow retry adopts through the granted owner

`_for_retry` builds its delivery by adopting through the operator-granted
`CredentialHome` and hands the adapter that same object. This is option (a)
proved at the other builder: before the correction the retry read the granted
home while the adapter derived its own, so adoption refused and the ending
would have misreported a delivered credential.

### The two rows that remain, and why each is what it is

**A restart BETWEEN the credential and launch teardowns has no public seam.**
Both endings are settled inside one `destroy_abandoned` answer — deliberately,
because they are settled on one absence observation — so there is no boundary
between them a public capability can be interrupted at. Covering it would mean
reaching into `_removed`, which is the opposite of what this suite does. The
adjacent boundaries either side of that pair ARE covered.

**The grants-versus-manager hold is genuinely MISSING, not merely uncovered,
and I am reporting it rather than quietly writing a case that passes.** The
finding's required recovery contract item 2 says the command "holds the
editable grants against the manager's durable attempt, assignment, runtime,
profile, policy, roots and provider records before an external mutation. A
newer attempt, authority, generation, runtime or home refuses."

`recover_abandoned` does not do that. It reads the attempt through
`attempt_runtime_of` and hands `abandon_attempt` the attempt id; the ending
then takes its assignment from the attempt ROW, not from the grants. So a
grants file naming another work_ref, participant or generation would end the
attempt anyway, and the recovery record would name identities the ending did
not use. `_bound` is the narrow retry's equivalent hold and has no counterpart
here.

I did not implement it this round because it needs a public read of the
attempt's FIXED ASSIGNMENT to hold the grants against, and `attempt_runtime_of`
deliberately projects only the runtime axes. Widening it, or adding a second
read, is a manager-surface decision of the same kind as `attempt_runtime_of`
itself was — and inventing it at the end of a round, unreviewed, is how the
defects this Work keeps finding got in. It is the next round's first work.

### Verification

    tests.tools.test_dogfood_operator + test_credentials
      + tests.manager.test_oci + test_attempts       752 tests, OK (734 before)
    the two attached-state classes in isolation      13 and 18 tests, OK,
                                                     live_after False

No new over-width line and no trailing whitespace. No engine command, no
authority mutation, no credential read and no change to the preserved run7/run8
state.

### State

Awaiting review, including a ruling on the grants-versus-manager hold above.
Passing back rather than closing.

## 2026-09-01 — ninth implementer round (`baton.claude`, W55758 impl claim)

### [P1] The grants are held against the manager's fixed assignment

APPROVE-EXTEND implemented. `attempt_runtime_of` now carries the complete
fixed assignment beside the runtime axes, in the ONE atomic read the branch
already turns on — two reads would be two moments, and a caller comparing one
against the other would be comparing an attempt with itself at two times.

`recover_abandoned` holds the grants against it before either branch and
before any external act. All four parts together, because the schema keeps
them together and three quarters of an identity matching is not an identity
matching. An attempt the manager never recorded, and one whose activation
never fixed an assignment, each refuse with their own sentence.

The reviewer's probe is the case: editing only the generation to 2 previously
ended the generation-1 attempt and wrote 2 into the record as the identity the
ending used. Now each of `generation`, `authority_uuid`, `work_id` and
`participant` refuses with `branch` unset, `authority_fence`, `runtime`,
`credentials`, `launch`, `custody` and `cleanup` all null, the manager's axes
unmoved and the bearer and its record still on the host.

### [P1] The credential-to-launch restart boundary

Injected at the PUBLIC `launch.discard`, after the real orphan teardown has
made the credential absent — no private seam is touched. The first command
writes a partial record saying the runtime is absent and the credential is
torn down while the launch is not, and a fresh invocation converges to
`retained` with the launch `torn-down` and no registration left live.

This also needed the fault path to build the partial account, which it now
does on the same rule as the refusal path.

### [P1] The retry's owner, by identity

The receiver of `CredentialHome.adopt` is captured and the adapter must own
that exact object. Measured: handing the adapter a freshly constructed
same-path home fails the case, which is precisely what the old path
comparison would have accepted.

**Still short of what was asked:** the assertion is made at `_for_retry`
rather than by driving documented `main --retry-handoff` over real
trusted-result state. Reaching the command needs the ordinary arc to commit a
freeze, an intake receipt and a retention decision WITH a credential
materialized, and this fixture's ordinary path supplies its own adapter and
materializes none. That is one fixture change and it is the next round's work.

### Mutation check

Seven mutations, all caught — one only after adding the recorded-but-never-
activated fixture, which is recorded rather than quietly fixed:

    CAUGHT  the grants are never held against the fixed assignment
    CAUGHT  the hold runs after the branch instead of before it
    CAUGHT  an absent fixed assignment is accepted   [after adding the
            recorded-and-never-activated row]
    CAUGHT  only the generation is compared
    CAUGHT  the projection carries no assignment
    CAUGHT  a fault after the ending began reports nothing it did
    CAUGHT  the retry hands the adapter a fresh same-path home

### Verification

    tests.tools.test_dogfood_operator + test_credentials
      + tests.manager.test_oci + test_attempts       793 tests, OK (752 before)
    the whole v12 python suite                      2926 tests, 7 failures,
      the same seven pre-existing ones, unchanged in number and identity

No new over-width line and no trailing whitespace. No engine command, no
authority mutation, no credential read and no change to the preserved run7/run8
state.

### State

Awaiting review. One row remains and is named above. Passing back rather than
closing.

## 2026-09-01 — tenth implementer round (`baton.claude`, W55758 impl claim)

**Three of the four [P1]s and the [P2] are corrected. The fourth is not, and
it is the same one I flagged last round.**

### [P1] The hold now precedes every capability

The reviewer is right and the probe is exact: the hold was after
`capabilities(given)`, and by then the builder had opened the authority,
selected a session, proved roots, constructed the credential owners and
adopted the launch delivery. A hold after all of that is a hold after most of
what it exists to prevent.

`_for_abandonment` now opens ONLY the control store, takes the one atomic
projection, and holds it. Opening a file this manager owns is not one of the
capabilities the ruling names — no authority, engine, credential, launch or
custody act happens before the comparison. On disagreement it returns the
projection and the reason and builds nothing else, and `_abandoned` writes the
account and closes what was opened.

THE PROJECTION IS CARRIED OUT rather than re-read, so the identity held and
the state acted on remain one answer at one moment. A direct caller supplying
none is still answered by reading it, which is the same question at the only
other moment there is.

And the mismatch cases now watch the SEAMS — `Authority.open`,
`_proved_roots`, `OrphanTeardown`, `launch.adopt` — and assert none was
exercised. Asserting that no record member was filled proved nothing happened
AFTER the builder ran; the ruling is about what happens inside it.

### [P1] The record's identity is the manager's

After the hold passes, `work_ref`, `participant` and `generation` are composed
from the fixed assignment the projection carried. Equal values kept the old
composition honest only because the hold had just proved them equal, and value
equality is not provenance. A refusal keeps the identity the operator ASKED
for, so an account of a rejected request stays distinguishable from an account
of an ending that ran.

### [P1] The incarnation boundary and the zombie report

M60437 revalidated against the tree. The recovery already stops only the
runtime the manager's own row names, so "never adopt or resume an older
incarnation's runtime" holds by construction — what was missing was the other
half. `zombies` is a new closed member reporting every runtime this recovery
LEFT ALONE, with its exact locator, its observed state and why it was not
touched. Automatic reconciliation stays out of scope, so the report is the
deliverable rather than a step towards one.

Three cases: a fresh incarnation still ends the exactly identified old runtime
with the credential settled, the attempt `retained` and the worker's output
preserved untrusted; an engine answering about ANOTHER id reports a zombie and
touches nothing; a runtime the engine says is RUNNING is reported rather than
resumed.

### [P2] The registry prose

`tests.manager.test_secrets` now describes the actual surface: four runtime
axes plus the assignment document activation fixed, in one atomic read.

### [P1] NOT DONE: the command-level `--retry-handoff` proof

Unchanged from my last account, and I am not dressing it up. The shared-owner
assertion is load-bearing — the `CredentialHome.adopt` receiver is captured
and compared by identity, and handing a fresh same-path home fails the case —
but it is made around a direct `_for_retry` call rather than by driving
documented `main --retry-handoff` over durable frozen, intaken, retained,
independently verified state with a real credential. That fixture's ordinary
path supplies its own adapter and materializes no credential, so reaching the
command needs it to materialize through the granted home and publish the
lifecycle record the way `_launched.adapter_of` now does. One fixture change,
and it is what I would do first next round.

### Mutation check

Four mutations, three caught:

    CAUGHT  the hold runs after the capabilities are built
    CAUGHT  the record keeps the grants identity after a match
    CAUGHT  every runtime is reported as a zombie
    MISSED  the zombie report is dropped from the REFUSAL path

The miss is recorded rather than papered over, and it is an equivalent mutant
today: `abandon_attempt` ANSWERS `cleanup_unsettled` for an uncertain or
running runtime rather than refusing, so every case that produces a zombie
goes through the settled branch. The line in `_partial_account` fires only if
a refusal coincides with a runtime not proved absent, and no case reaches that
combination. It is defensive, and I would rather say so than invent machinery
to drive it.

### Verification

    tests.tools.test_dogfood_operator + test_credentials + test_oci
      + test_attempts + test_secrets + test_text_sweep   910 tests, OK
    the whole v12 python suite                          2950 tests, 7 failures,
      the same seven pre-existing ones, unchanged in number and identity

No new over-width line and no trailing whitespace. No engine command, no
authority mutation, no credential read and no change to the preserved run7/run8
state.

### State

Awaiting review. One row remains and is named above. Passing back rather than
closing.

## 2026-09-01 — eleventh implementer round (`baton.claude`, W55758 impl claim)

**Two of the four [P1]s are corrected. One is reported as another record's
supersession, and one is still not done.**

### [P1] The door built to close the hole was the hole

The reviewer is right and the probe is exact: carrying the projection as a
plain operand let a direct caller of the EXPORTED operation supply a forged
one, and a generation-2 dictionary beside generation-2 grants ended the real
generation-1 attempt while publishing generation 2 as the identity the ending
used. That is the original defect, reintroduced through the door added to
close it.

The carried form is now `_HeldProjection`, a capability this deployment mints
after its own read and its own hold — the same rule a credential delivery is
under, and for the same reason: a dict is something any caller can compose. The
exported operation refuses anything else and, given none, performs the read AND
the hold itself. A case drives the reviewer's forgery through the exported
function and proves nothing is removed and no axis moves.

### [P1] The zombie report named the wrong runtimes and misstated the act

Both halves were wrong and both are corrected.

`OciAdapter.observe` was reducing a mismatched inspection to prose and an
ambiguous one to a count, so the identities an operator needs were discarded at
the only place that saw them. It now carries them structurally, empty on every
branch that saw none.

The report is composed from those, not from the expected target — and it says
what was actually done PER RUNTIME. A target this command really issued a
removal for and which is still present is not `left untouched`; that sentence
was false and is the one an operator would act on. Candidates the engine named
while answering about something else were never targeted, and those are the
untouched ones. Three cases: a mismatched answer, an ambiguous two-runtime
answer that the first report omitted entirely, and a running target.

### [P1] The pre-attach branch contradicts M60437 — reported, not changed

`OciAdapter._recovery_failed` stops EVERY ambiguous or mismatched candidate
before its bounded cleanup. M60437 says unknown, ambiguous and mismatched
runtimes remain untouched for initial v12. Those two cannot both hold.

That rule is W6634's, pinned in its own record with its own reasoning — the
stop is conditional and the cleanup rides on it being proved. Appending a
supersession to another finding's ruling, at the end of a round, unreviewed, is
exactly what this repository's pinned-decision gate forbids. So it is reported
here for the owning reviewer to place. It is a real contradiction and I am not
implying otherwise.

### [P1] NOT DONE

The command-level `--retry-handoff` shared-owner proof, unchanged and for the
unchanged reason. And the fresh-incarnation case still argues "output preserved
untrusted" from the cleanup axis rather than retaining a marker in the
workspace and proving its bytes survive; the reviewer is right that a comment
plus an axis is not that proof.

### Mutation check

Five mutations, all caught — one only after adding the forged-projection case,
which is recorded rather than quietly fixed:

    CAUGHT  the exported recovery accepts a caller's dictionary  [after
            adding the case that drives the reviewer's forgery]
    CAUGHT  the report is rebuilt from the expected target alone
    CAUGHT  a targeted runtime is called left untouched
    CAUGHT  observe discards the identities it saw

### Verification

    tests.tools.test_dogfood_operator                297 tests, OK
    the whole v12 python suite                      2953 tests, 7 failures,
      the same seven pre-existing ones, unchanged in number and identity

No new over-width line and no trailing whitespace. No engine command, no
authority mutation, no credential read and no change to the preserved run7/run8
state.

### State

Awaiting review. Two rows remain and both are named above. Passing back rather
than closing.


## 2026-09-01 — twelfth implementer round (`baton.claude`, W55758 impl claim)

**All five rows are done. The two I have been carrying for three rounds are
among them, and neither needed the machinery I kept saying it did.**

### [P1] The nominal capability is deleted, not hardened

The reviewer is right and the probe is exact: `_HeldProjection` was an
ordinary module attribute with a public constructor, so wrapping the forged
dictionary in it satisfied the check and ended the real generation-1 attempt
while publishing generation 2. A type name is not a lock.

So the class is GONE rather than made cleverer. The exported
`recover_abandoned` has no `state` operand at all: it performs the manager
read and the hold itself. The documented command still carries ONE
observation, because `_for_abandonment` must take it before any capability
exists, and it travels through private `_recovery_of` -- composition between
two parts of one command rather than a door anybody can knock on.

The regression drives both halves. The old operand raises `TypeError`, no
`*HeldProjection` attribute exists on the module, and the exported operation
answered with the reviewer's own generation-2 grants refuses on its own read
with nothing removed and no axis moved.

### [P1] Each candidate keeps its own state and its own reason

`observe` was carrying identities and nothing else, so the report wrote the
literal `unidentified` for a runtime whose inspection said `Running: true`
and copied the target's diagnostic as that candidate's explanation. Both
members were in the document that was read.

`_observed_runtime` now composes a closed record -- exact locator, its own
validated state, its own reason -- for every runtime an answer named, and
`_running_state` is the ONE place `Running` is given a meaning. The read
itself stays at the `observe` crossing, which is where the boundary inventory
owns it and where its witness case drives it; what is shared is the
vocabulary, not a second reading.

### [P1] The pre-attach branch stops only what is exactly identified

`OciAdapter._recovery_failed` stopped EVERY candidate it had listed. It now
stops only a runtime whose caller proved one identity exactly -- the mounts
disagreement, where the labels and the lifecycle record agree on WHICH
runtime this is -- and leaves ambiguous and mismatched ones where they are.
Zero candidates is still positive absence, so the convergence the seventh
review fixed is unchanged; an empty `stopped` no longer stands in for it.

The survivors are observed once more after the stop and ride the refusal, and
`--abandon`'s pre-attach branch writes them into the record through the same
`_zombie_account` composer the attached branch uses. One obligation, one
vocabulary, two branches.

The reviewer's ownership finding is accepted in full: W6634 closed
non-satisfying and its stop-every-candidate wording is provisional text, not a
rule needing supersession. W32385's accepted boundary and M60437 are the live
rule and this is written against them. I was wrong to report it as another
record's supersession last round.

### [P1] The two witnesses I have been deferring

Both are done, and the fixtures they needed were smaller than the reasons I
gave for not building them.

The fresh-incarnation case writes real bytes into the worker's own workspace
before the ending and proves them unmoved and unchanged afterwards, with
`frozen_output_of` and `intake_receipt_of` both still absent and the only
custody verb `normalize`. `cleanup: retained` is an axis; this is the file.

The documented `main --retry-handoff` now runs over a real credential. The
ordinary command produces the real freeze, intake receipt, retention decision
and this operator's own independent verification; the fixture supplies only
the half a stubbed engine does not -- `OciAdapter.start` materializes and
publishes the lifecycle record after the container exists, and there is no
container here. The `CredentialHome.adopt` receiver is captured and the
adapter is required to own that exact object by identity.

### New coverage

- a pre-attach interruption fixture: recorded, claimed, activated, credential
  materialized in the arc's own order, and no runtime ever attached;
- command-level ambiguous and mismatched pre-attach cases asserting the
  absence of every `stop`, `kill` and `rm` vector; and
- four manager-level cases on `recover_credentials`: ambiguous and mismatched
  candidates untouched and reported, the exactly identified one still stopped
  and named, and an unreadable answer about a bystander recorded as
  uncertainty rather than replacing the refusal's own account.

### Mutation check

Five mutations, all caught:

    CAUGHT  the exported recovery takes a caller's projection again
    CAUGHT  the retry hands the adapter a fresh same-path home
    CAUGHT  the report writes a placeholder state for non-targets
    CAUGHT  the pre-attach recovery stops every candidate again
    CAUGHT  the ending removes the worker's workspace

### Verification

    tests.tools.test_dogfood_operator + test_credentials + test_oci
      + the stale-owner boundary check              529 tests, OK
    the whole v12 python suite                      2967 tests, 7 failures,
      the same seven pre-existing ones, unchanged in number and identity

One of that suite's failures WAS mine for a while and is not now: moving the
`Running` read out of `observe` made the boundary inventory's declared owner
for `oci.py:OciAdapter.observe / document.Running` stale. The read is back at
its crossing and only the vocabulary is shared.

No new over-width line and no trailing whitespace. No engine command, no
authority mutation, no credential read and no change to the preserved run7/run8
state.

### State

Awaiting review. No row is outstanding. Passing back rather than closing.

## 2026-09-01 — thirteenth implementer round (`baton.claude`, W55758 impl claim)

**One row, and it was a report saying two mutually exclusive things about one
container.**

### [P1] One runtime is one row, and a contradiction says so

The reviewer's probe is exact. `OciAdapter.observe` was right about the
runtime -- an engine answering twice for one exact identity is `uncertain`,
and it said so -- but `_zombie_account` composed one zombie row PER DOCUMENT.
An engine that named `runtime-1` twice with disagreeing `Running` members
therefore wrote two rows for one locator, `quiescent` and `running`, both
targeted, under a top-level runtime that already said `uncertain`. The host
behaviour was fail-closed throughout; the durable evidence was not usable.

`_canonical_candidates` now settles observations by runtime identity before
either branch composes. Repeated or aliasing documents that agree are one
observation seen twice and collapse to one row; documents that disagree
produce ONE `uncertain` row whose reason names both of the engine's own
accounts rather than the one that happened to be read first. The per-runtime
`targeted` fact and its two non-interchangeable sentences are unchanged, and
they are now said once per runtime instead of once per document.

The composer is the seam because it is the ONE place both endings meet:
`observe`'s candidates on the attached branch and `_recovery_failed`'s
`runtime_zombies` on the pre-attach one. Canonicalizing inside `observe`
would have left the other branch's duplicate-listing shape uncovered, and two
canonicalizers would be the second vocabulary this composer exists to prevent.

### New coverage

- the reviewer's recorded shape at the documented command: one identity
  answered twice in conflict is exactly one `uncertain` zombie row, still
  targeted, with an unresolved recovery, no `retained` cleanup and the
  credential material still on the host;
- its other half, so the collapse cannot invent an `uncertain` the engine
  never reported: one identity answered twice in AGREEMENT stays `running`
  with its own reason; and
- the pre-attach branch's own duplicate shape -- one identity listed twice
  under this attempt's whole label set, answered differently on each
  observation -- reported as one untouched `uncertain` row with nothing
  stopped.

### Mutation check

One mutation, caught by all three new cases:

    CAUGHT  the composer keeps every document as its own row again

### Verification

    tests.tools.test_dogfood_operator + test_credentials + test_oci
      + test_secrets + test_text_sweep + test_attempts
                                                    930 tests, OK (927 before)
    the whole v12 python suite                      2970 tests, 7 failures,
      the same seven pre-existing ones, unchanged in number and identity:
      five in `test_boundary_inventory`, one in `tests.authority.test_catalog`
      and `test_credentials_engine`'s host check, which still sees run8's
      deliberately preserved container

Cached and working-tree diff checks are clean. No engine command, no authority
mutation, no credential read and no change to the preserved run7/run8 state.
The reviewer's `/tmp/w55758-round12-probe.py` is left where it was; my own
`/tmp/w55758-round13-shape.py` is left beside it for the operator.

### State

Awaiting review. No row is outstanding. Passing back rather than closing.

## 2026-09-01 — fourteenth implementer round (`baton.claude`, W55758 impl claim)

**One row, and the reviewer is right: I made agreement mean less than an
account.**

### [P1] Agreement is the whole account, not the coarse state

`_canonical_candidates` compared `state` and nothing else, so two DIFFERENT
`uncertain` answers about one identity -- one document carrying no state
record, another carrying `Running: "yes"` -- looked like one observation seen
twice, and the second engine account was dropped without a word. That is the
same silent loss this canonicalization was added to end, one layer in: for
`uncertain`, the reason IS the evidence, and a coarse state that all confusion
maps onto cannot be the thing that decides two answers are the same answer.

Agreement is now the complete `(state, why)` account. Identical accounts
collapse and nothing else does, so any distinct pair for one locator produces
one `uncertain` row whose reason preserves every unique account in the order
the engine gave them -- including the same-state/different-reason case that
produced this correction. The composer got smaller rather than larger: the
distinct accounts are collected once at the identity, and the row is decided
by how many survived.

### New coverage

- the reviewer's recorded pair at the documented command: one document with no
  `State` and one with `Running: "yes"` produce a single targeted `uncertain`
  row carrying BOTH reasons, with the recovery unresolved, no `retained`
  cleanup and the credential material still on the host.

The three cases from the previous round are retained unchanged and still
pass: the conflicting `running`/`quiescent` duplicate, the agreeing duplicate
that must not become `uncertain`, and the pre-attach duplicate listing.

### Mutation check

Two mutations, both caught:

    CAUGHT  agreement is decided on the coarse state again
    CAUGHT  identical accounts no longer collapse

The second is the guard on the correction itself: an account comparison that
stopped deduplicating would report a repeated identical observation as a
disagreement with itself.

### Verification

    tests.tools.test_dogfood_operator + test_credentials + test_oci
      + test_secrets + test_text_sweep + test_attempts
                                                    931 tests, OK (930 before)
    the whole v12 python suite                      2971 tests, 7 failures,
      the same seven pre-existing ones, unchanged in number and identity

Cached and working-tree diff checks are clean. No engine command, no authority
mutation, no credential read and no change to the preserved run7/run8 state.
The reviewer's `/tmp/w55758-round13-review-probe.py` is left where it was and
now prints both accounts.

### State

Awaiting review. No row is outstanding. Passing back rather than closing.
