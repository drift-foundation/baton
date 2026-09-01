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

