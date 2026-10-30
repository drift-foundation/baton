# W333486 execution-selection packet, revision 2 — 2026-10-19

Author `baton.claude`, role `impl`, claim333707. Bound dossier
`work/records/2026/10/finding-v12-attempt-failure-diagnostics`.

**Supersedes `../execution-333504`**, which is preserved unchanged with its own
seal `bca87e931532560d6feebcaff36f59be82592841550d09807ad88f00c811fcf3`. No
hash of it was edited.

**State: `prepared-not-executed`. The start is HELD — see `HOLD.md`.** No Job
was submitted, no engine or container was invoked, no provider was contacted,
no credential was read, no product or test file was edited on the host, and the
shared-authoring falsification was **reused** from W333485 rather than re-run.

This revision answers `decisions/review-333691.md`, which verified the
superseded packet's seals and pins and then required corrections in three
places plus a locator demonstration and an explicit authoring hold.

## What changed, and why

| # | Change | Driver |
| --- | --- | --- |
| 1 | `TASK.md` item 1 now covers the **actual reclaim-to-settlement composition** and **both** release paths, plus restart and replay at every external-effect cut including a crash after the engine stop | review item 2 |
| 2 | `TASK.md` item 3 keeps a **known typed stop/engine failure** separate from an **unknown cessation** instead of folding the first into the second | review item 3 |
| 3 | The "nothing records" claim is **narrowed** to the missing causal/operation/outcome composition; `tokens.revoke`'s durable revocation and `tokens.returned` on both paths are named as evidence to read | review item 3 |
| 4 | The retained-evidence locator is now a **demonstrated round trip** through the supported `attempt_logs` reader, not a device/inode pair asserted to be a locator | review, closing paragraph |
| 5 | The packaged-table obligation is a source-level assertion **plus an explicit remaining rebuilt-bundle obligation**, because source proof is not bundle proof | review, closing paragraph |
| 6 | `HOLD.md` records the shared authoring hold explicitly and **withdraws** the superseded OPERATOR's unsupported 900-second transfer claim | review item 1 |
| 7 | Decision inputs are **immutable snapshots** under `decisions/`; three base-committed documents moved to the private checkout and are not fixture-pinned at all | review, closing paragraph |
| 8 | `prepare.py stage` refuses without `--acknowledge-hold`, so preparation cannot drift into a start | review item 1 |

### 1 and 3 — the composition, and a claim that was too broad

The superseded task said the capture belongs "after positive confirmation and
before `govern.release`". Revalidated at this base, that names only one of two
releases, and probably not the one that ran:

- `intake.reclaim_expired_resource` revokes, stops, removes, observes — then
  calls `_resource_cessation` (`intake.py:1122`), which answers `None` unless a
  committed cleanup carries both halves of its proof. `_custody_already_committed`
  returns `None` for a running attempt whose roots were never normalized, so
  the ordinary outcome for a reclaimed live attempt is **`held`** and the
  reclaim's own `govern.release` is never reached.
- `tools/job_manager.py:_reclaiming` then calls
  `intake.settle_revoked_resource`, and **its** `govern.release`
  (`intake.py:5909`) is what finishes the generation.

So a capture bound to the reclaim's own release would have recorded nothing
about the path that most plausibly completed the pilot's termination. `TASK.md`
item 1 now requires capturing eligibility and stop intent **before the engine
is asked**, capturing the outcome separately, and making completion
attributable on **either** release path — preferring `resource-token.returned`,
which both paths already journal, over inventing a third record.

And the claim is narrowed. `tokens.revoke` (`tokens.py:728`) already journals
the revoked generation with its domain, generation, owner, bound container and
the `expired_at` it blew, under the store's own `settled_at`. What is missing is
the **causal/operation/outcome composition** — which component ordered this
exact runtime stopped, under which operation identity, with what engine outcome,
and whether cessation was established. `TASK.md` now says that, and also says
that the absence of a start- or preparation-failure record is **expected** for
this component rather than independent proof of the proposed cause.

### 2 — a known failure is not an unknown

The superseded task treated a refused stop as unknown "because it is not a
termination". Not claiming termination was right; discarding what the manager
*does* know was not. `TASK.md` item 3 now requires an outcome vocabulary that
separates positively established cessation, **a known typed stop or engine
failure with cessation still unknown**, an uncertain observation, an
exact-runtime mismatch and a lost reply — none of them reducible to "no
termination evidence".

### 4 — the locator is a demonstration

The supported path is the deployed `logs` subcommand over
`worker_manager.attempt_logs`, whose contract is
`baton-v12-stack logs --logs <launch-home>/logs --attempt <id> locators`. The
report must emit the attempt identity and the manager's own recorded
`artifacts`, emit the exact invocation shape, name the one operand the operator
must supply, and say why it does not resolve the deployment root — a report
that resolved a deployment document would be a reader that can be pointed at a
store. Device and inode stay, explicitly labelled an object identity and
explicitly **not** a path and **not** a locator by themselves. And a case must
take the report's emitted fields, feed them to the supported reader over a real
retained delivery, and show the operator reaches the evidence while the report
itself carries no stream content.

## Selected identities

| element | selection |
| --- | --- |
| declared base | `bbdacb5d38f6cf2d2461e9da103d28f9ab30cc6c` — this tree's committed `HEAD`, revalidated this claim |
| run identity | `attempt-diagnostics-w333486-333707` |
| selected root | `/home/sl/baton-instances/attempt-diagnostics-w333486-333707` — **does not exist**; `stage` refuses reuse |
| worker image | `baton-v12-claude-worker:w239528-244216`, config digest `sha256:c862c055c6430addc918ca078a9e4d55f6bd8173ed9c9878a8ad9d6cad334ca2` — existing, revalidated, **not rebuilt** |
| manager runtime | `/home/sl/baton-runs/managed-correction-236087/build/stack/out/distro`, binary `sha256 04aa459a…`, build commit `1e576ff2` |
| manager source | 112 files from `v12/python/{src/baton_v12,tools}` at the declared base |
| supervisor | `baseline.py` `c1b0a10e…`, `baseline_bindings.py` `09fbf3c5…`, `prepare_instance.py` `d08514cb…` at the declared base — **the held vehicle; see `HOLD.md`** |
| launch envelope | `baton.dogfood-task/2`, `source_profile` `git-line`, `context_mode` `fresh` |
| terminal policy | `report-and-hold`; one implementation invocation, no automatic retry |
| **start** | **HELD.** `HOLD.md`; `PROVENANCE.json` `start_authorized: false` |

## Inputs: pinned, snapshotted, and deliberately not pinned

Three classes, because they fail for three different reasons:

- **Fatal if drifted** — 112 committed manager files, 3 committed supervisor
  files, 2 preparation inputs the composer consumes (`vectors.json`, the image
  artifact), and the bootstrap binary. These decide what would be built.
- **Immutable snapshots, fatal if damaged** — the 7 decision documents under
  `decisions/`, byte-for-byte with their source paths and source digests in
  `decisions/INDEX.json`, pinned as the packet's `fixture.files` together with
  `TASK.md`. They live inside the packet, so a difference is a damaged packet
  rather than a moved decision.
- **Reported, never fatal** — whether each live decision source still matches
  its snapshot. This is the fix for the superseded packet's real defect: it
  pinned the **mutable reviewer-owned** `FINDING.md` and `PLAN.md`, so every
  ordinary current-plan update invalidated a sealed packet.
  `verify-inputs.py` now prints a `DECISION-SOURCE DRIFT` section and exits 0,
  leaving review and the owner to judge whether the snapshot still reflects
  accepted scope. A snapshot records what was accepted when taken; it is not a
  second authority.
- **Not pinned at all** — `v12/DESIGN.md`, `AGENTS.md` and
  `finding-v12-minimum-worker-visibility/FINDING.md`. All three are committed
  at the declared base, so the private checkout carries them; pinning a mutable
  mount copy would make this packet refuse on an unrelated policy edit.

No overlay and no preserved candidate buffer: every byte this correction begins
from is committed, so there is no `restore.py`. The five dirty W321776 Stage-A
files are named in `PROVENANCE.json` as a deliberate exclusion.

## Verification, and the ceiling that bounds it

The sealed argv runs nine existing modules plus the two the turn must create.
`tests.manager.test_intake` and `tests.job_manager.test_tool` are in it
**specifically** because review item 2's reclaim-to-settlement composition
lives across them.

Measured against a clean `git archive` export of the declared base — **the
preparing author's evidence, not independent product acceptance**: 1091 tests,
all passing, zero skips, **11.830s** (`test_status` 0.343/65, `test_delegation`
0.059/44, `test_documents` 0.002/31, `test_tool` 0.575/72, `test_intake`
4.121/207, `test_maintenance` 2.396/148, `test_attempts` 4.048/431,
`test_worker_visibility` 0.277/78, `test_contracts_inventory` 0.010/15).

`GATE-CHECK.json` records this packet's own composed argv run verbatim from
`packet/task.json` against that base with a deliberately useless ambient
`PYTHONPATH`: **status 1, 1093 tests in 11.758s, failing on exactly the two
owed modules and nothing else.** That is the designed state.

`LIMITS-CHECK.json` reads the **generated** documents: `policy.json` and
`submission.json jobs[0].execution_limits` agree — provider 3600s, verification
30s, one invocation, `report-and-hold`; bounds 4800s total, 60s cleanup, 1110s
residual. The 30-second ceiling is fixed by the composer at
`baseline_bindings.py:345` and `:522` with no compose parameter, so the two new
modules have **≈18.17s** between them; `TASK.md` states that as a design
constraint and requires an honest measured report rather than deleted coverage.

### Two excluded modules, both explicitly unverified baseline reports

`decisions/review-333691.md` records these as the author's unverified baseline
observations with no cleanup selected. Neither is attributable to this
candidate and neither is worked around:

- **`tests.manager.test_boundary_inventory` does not pass at this base** — 328
  tests, 28 failures, 1 error, zero skips, 49.469s measured alone on base
  bytes; 49.5s would exceed the ceiling by itself. `TASK.md` excludes it,
  forbids fixing it, and still requires the turn to register the receiving
  entries and probes its **own** new boundary introduces.
- **`tests.tools.test_packaging`'s subcommand case fails on this host** because
  it holds the source `stack_command.COMMANDS` table against the **installed
  bundle**, built at `1e576ff2` before `record` and `disposition` joined that
  table (`'disposition' not found`). Inside a private checkout it SKIPs, which
  the gate refuses. **Source command-table proof is not proof that an eventual
  rebuilt bundle carries the new verb**, and `TASK.md` keeps that deployment
  obligation explicit in both the module and the turn's report.

## Preparation evidence

`PREFLIGHT.json` holds the whole run; the selected root is untouched.

- `stage --acknowledge-hold` 0.115s, `bootstrap --no-repositories` 0.597s,
  `bind` 0.355s — **1.192s**, all status 0, first attempt, ending at
  `PREPARED.json: state prepared-not-executed, start_authorized false`.
- `bind` ran `baseline.held_packet`, which re-pinned every artifact the packet
  binds including all 9 `fixture.files`, and `baseline.verify_imported_sources`,
  which proved the process was running the staged code.
- **Eleven probes, all behaving as intended, 0.923s**: stage refused without
  `--acknowledge-hold` leaving no root; drifted staged manager source (on its
  own staged-but-unbound root, so the packet-existence check cannot mask it); a
  wrong supervisor digest, leaving no root; a **damaged decision snapshot**; a
  **provenance claiming an authorized start**; an existing root; a root already
  holding a packet; an already-present gate module refused by both programs;
  **decision-source drift reported with exit 0**; and a clean pass that reports
  no drift and states the hold.
- `verify-inputs.py` on the current tree: 112 manager files, 3 supervisor
  files, 2 preparation inputs, 9 task inputs, 7 decision snapshots, 3 checkout
  documents, 2 gate modules still owed, no decision-source drift, 0.109s.
- The composed packet digest and authority uuid are **per-instance preflight
  facts**, not proposed production identities: `bind` derives the Work id from
  the bootstrap's generated uuid (`uuid[:8] + "-W1"`), which travels into the
  submission, so the owner's run composes different ones. The stable, pinned
  half is the input side.

Carried forward from the superseded packet: its `stage` ordering fix, which
resolves and proves every base byte in memory before creating the root, so a
refused stage leaves the filesystem exactly as it found it.

## Overlap declaration to sibling W333485

Unchanged in substance, declared again because this is a new packet. Surfaces:
`worker_manager/{documents,attempts,intake,diagnostics}.py`,
`job_manager/{delegation,documents,projection}.py`,
`tools/attempt_diagnostics.py`, `tools/stack_command.py`, and the two new test
modules.

**Intersection empty.** This candidate touches neither
`tools/job_manager.py` nor `job_manager/manager.py`, which W333485's PACKET.md
expected to share: the new observation member is composed inside
`delegation.ManagerOperations.observe`, which both the serving loop and the
read-only `status` surface already reach. `TASK.md` forbids touching them. The
one residual risk is `worker_manager/intake.py` if the sibling's renewal
integration reaches the reclaim or settlement paths — declared, and to be
integrated serially rather than overwritten.

No behavioural dependency either way. **What is shared is the authoring
prerequisite, not the renewal outcome**: this packet takes no dependency on
W333485's production renewal result, and `decisions/review-333691.md` is
explicit that none is warranted merely because the vehicle is common. Declared
on T333485 at seq333677.

## What is still owed

The entire correction in `decisions/FINDING.md`. This packet contains no
implementation. Owed: the owner's decision on the shared authoring
prerequisite; a safe authoring vehicle; the run; the retained immutable
candidate; independent review of it; the parent W325959's joined acceptance
with W333485; and the human Git checkpoint the parent PLAN carries. A retained
proposal is not an accepted candidate and nothing here is self-acceptance.
