# W333486 execution packet, revision 5 — sealed preparation at `bc925cf5`

`baton.claude`, claim339421, role `impl`. **Preparation only.** No Job
submitted, no attempt, no runtime, no engine, no provider, no credential read,
no Git mutation, no host product or test edit. **The start is not selected.**

| | |
| --- | --- |
| base | `bc925cf5c62d69426ed5862af4d41f4d2a967b0f` |
| proposed run | `attempt-diagnostics-w333486-339421` |
| proposed root | `/home/sl/baton-instances/attempt-diagnostics-w333486-339421` — **absent** |
| supersedes | `../execution-333504`, `../execution-333707`, `../execution-334663`, `../execution-337453` — all preserved, all seals still verifying |
| start | `start_authorized: false`, `start_selected: false` |
| exact commands | `COMMANDS.md` (five, no placeholders) |

## Read in this order

1. **`COMMANDS.md`** — the five exact commands.
2. **`OPERATOR.md`** — what each step does and what to expect.
3. **`SHUTDOWN.md`** — why this packet exists, what the vehicle publishes when
   it ends, and the rule that a missing final report is incomplete rather than
   success.
4. **`ENFORCEMENT.md`** — the vehicle, the composer's wrong start command, the
   900-second lease, the two measured ceilings.
5. **`FAILURE.md`** — the one actual execution of this Work and why it failed.
6. **`TASK.md`** — what the authoring turn is actually asked to build.

Evidence: `PREPARATION-PINS.json`, `PROVENANCE.json`, `PREFLIGHT.json`,
`GATE-CHECK.json`, `LIMITS-CHECK.json`, `decisions/` (15 immutable snapshots
indexed by `decisions/INDEX.json`), `SHA256SUMS` and `PACKET-INPUTS.json`.

## Why there is a fifth packet

`../execution-337453` was independently accepted as preparation and then held
for the finalization assessment. The assessment produced the W338305 shutdown
correction; it was independently accepted and committed, and it moved the exact
bytes that packet pinned — controller `bc8c0363…` → **`d12769df…`**, supervisor
baseline `c1b0a10e…` → **`8e5987f5…`** — and added
`tools/authoring_shutdown.py` (**`af9e5ea6…`**), which the controller imports.

I verified all six accepted paths myself this claim, three ways each — the
committed object at this base, the host checkout file, and the independently
accepted digest in `decisions/shutdown-integration.json` — and all three agree
on every one.

So this packet pins **114 manager files** rather than 113, and both the
controller and the helper are cross-checked three ways by `prepare.py` and
`verify-inputs.py`. The helper pin is load-bearing and that is measured, not
assumed: importing the controller from a staged source with
`tools/authoring_shutdown.py` removed fails with `ModuleNotFoundError`. A
missing helper is a **startup failure**, not a refusal, and `FAILURE.md` records
what a startup failure cost this Work the last time.

## What changed in the task

`TASK.md` keeps every accepted obligation from revisions 1 to 4 — intent before
effects, typed outcome separate from unknown cessation, both release paths and
crash/replay cuts, the token-bound identity rule, the three-case
absent/quiescent replay table, cancellation as a second terminating component,
the safe locator round trip, the read-only allowlisted report, and
source-versus-rebuilt-bundle proof — and adds three things:

- **revalidation item (e)**: the bounded shutdown semantics of the vehicle the
  turn runs inside, including that `begin()` does not renew an allowance, that
  `bounded()` is cooperative rather than a guarantee about kernel I/O, and that
  a publication `TimeoutError` makes the controller return 1 and write nothing
  on purpose;
- **milestone item 6**: report this run's own ending honestly — the controller
  final report, the workload final report, the shutdown progress file, the
  actual expiry and cessation facts, what remains uncertain, the retained
  partial output and the missing evidence. *No startup success and no producer
  exit substitutes for final-result acceptance.*
- **one further preserved axis**: an incomplete final report is not an
  acceptance, and a deadline-bounded publication failure is not cessation
  evidence.

It also states the vehicle files as off-limits: the turn edits neither
`tools/authoring_enforcement.py`, `tools/authoring_shutdown.py` nor the
supervisor baseline, which is the condition the two gate exclusions rest on.

`intake.py` and `attempts.py` are **byte-identical between `fb487979` and this
base**, verified read-only this claim, so items (a) to (d) are the same facts
revision 4 carried, re-confirmed at their current line numbers —
`_resource_cessation` at `intake.py:1122`, `reclaim_expired_resource` at
`:5611`, its unreached `govern.release` at `:5750`, `_custody_already_committed`
at `:5756`, `settle_revoked_resource` at `:5781` with its release at `:5927`,
and `_order_quiescence` at `attempts.py:3490`.

## Preparation evidence, measured this claim

- **Input check**: 0.116s, clean — 114 manager files, 3 supervisor files, 2
  preparation inputs, 20 task inputs, 15 decision snapshots, 4 checkout
  documents, 1 pinned controller, 1 pinned shutdown helper, 2 gate modules still
  owed, **no decision-source drift**.
- **Preparation exercised once** into `/tmp/w333486-preflight-339421`: stage
  0.126s, bootstrap `--no-repositories` 0.591s, bind 0.361s — **1.194s, all
  status 0**, ending `prepared-not-executed` / `start_selected false` /
  `composer_start_is_unenforced true`, after `held_packet` re-pinned all 20
  `fixture.files` and `verify_imported_sources` passed.
- **Nineteen probes, all refusing as intended, 1.154s.** Every root-creating
  one also asserts whether the root was created. New this revision: an
  **unpinned** shutdown helper, a **drifted** shutdown helper, and a damaged
  shutdown-review snapshot. Also covered: no acknowledgement; the superseded
  controller digest; a drifted manager source; the superseded supervisor
  baseline; a provenance claiming a selected start; one claiming an authorized
  start; an absent `SHUTDOWN.md`; an absent task input; a checkout input not at
  the base; a gate module already on the host; a root inside the repository; a
  relative root; an existing root (left untouched); a second `bind` over a
  composed packet; and a `bind` against a root staged for another run.
- **The controller binding proved both ways**, read-only, opening no store and
  starting nothing: `verify_controller` **accepted** this packet's composed
  documents from the staged source (0.3s) and **refused** them from the host
  checkout — *"authoring controller is outside the pinned manager source"*.
- **Sealed gate**, argv verbatim from the composed `task.json`, run against a
  clean export of the declared base with a deliberately useless ambient
  `PYTHONPATH`: **status 1, 1126 tests, 14.18s, errors on exactly the two owed
  modules and nothing else, zero skips.** The ten existing modules alone:
  **1124 tests, all passing, zero skips, 13.642s** unittest / 14.007s measured.
- **Generated limits agree** (`LIMITS-CHECK.json`, read from the composed
  documents, not from prose): provider 3600, verification 30, one invocation, no
  automatic retry, `report-and-hold`, 4800 total, 60 cleanup, 1110 residual.

Author evidence, **not** independent product acceptance.

## Disclosures, all retained

- **The composer still emits the unenforced start.** `baseline_bindings.py` is
  unchanged at this base (`09fbf3c5…`, re-measured) and line 721 still composes
  `baseline.py` directly. Reported for classification, **not patched** —
  correcting it is host product work this Work does not own — and mitigated by
  `AUTHORING-COMMAND.json`, `PREPARED.json`'s `composer_start_is_unenforced`
  flag and both operator documents. **Every later authoring packet inherits
  this** until the composer is corrected.
- **The 900-second lease is enforced and unextended.**
  `worker_manager/tokens.py:37` still reads `LIFETIME_SECONDS = 900`, measured
  at this base. W333735 made it real; W338305 made the *ending* bounded. The
  3600/4800 ceilings are requested bounds, not a promised run length.
- **No authoring invocation has ever completed for this Work.** One was
  selected and died 0.506s into startup. Two corrected failures are not a
  demonstration that a third attempt completes.
- **The 30-second verification fit remains unproved**, with ≈16.36s left for the
  two modules the turn must create, and no coverage may be removed to force a
  pass.
- **Two excluded real-process modules are reused, never re-run here** —
  `decisions/shutdown-review.md` (44 tests, 72.891s, authority338596) and
  `decisions/guard-integration-result.json` (79 tests, 15.278s,
  authority337376) — on the stated condition that this candidate edits none of
  the three vehicle files.
- **Two excluded modules already fail at base**, both explicitly unverified
  baseline reports with no cleanup selected:
  `tests.manager.test_boundary_inventory` (not re-measured this claim; the
  49.469s figure is from an earlier base's bytes) and
  `tests.tools.test_packaging`'s subcommand case.
- **`AGENTS.md` at this base carries the older W321689 exception section**,
  because the host's replacement of it is an uncommitted working-tree edit. The
  turn reads the base copy. The exception is expired either way; this packet's
  documents are the authority on what is permitted here.
- **Both temporary direct-implementation exceptions have expired** and neither
  ever covered diagnostics.
- One of my own probe expectations was wrong and was corrected toward the code:
  a copied packet with `FAILURE.md` deleted still staged, because the
  task-input existence check validates the **repository-resident** packet whose
  bytes travel as `fixture.files`, not the copy being executed. The probe now
  declares a task input that exists nowhere and is refused by name.

## Ownership and what is still owed

`baton.impl` owns this packet, `PROGRESS.md` and the isolated candidate;
the reviewer owns `FINDING.md`, `PLAN.md` and the reviews. W333485 owns the
separate serving-renewal preparation at `baton.codx`, with no dependency either
way on its completion. The declared candidate intersection remains
`worker_manager/intake.py` and `worker_manager/attempts.py` at the accepted
bytes, for serial integration; `tools/job_manager.py` and
`job_manager/manager.py` are the sibling's and are forbidden here.

Still owed: independent review of **this** preparation; an exact separate
execution selection; a run that actually completes, which has never happened for
this Work; the entire correction in `FINDING.md`; independent review of the
retained candidate; parent W325959's joined acceptance with W333485; and the
parent's pending human Git checkpoint.

**Nothing in this packet selects or authorizes a start.**
