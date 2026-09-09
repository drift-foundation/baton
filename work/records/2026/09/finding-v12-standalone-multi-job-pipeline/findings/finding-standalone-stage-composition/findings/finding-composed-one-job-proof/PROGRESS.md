# Progress

Implementation entries belong to the assigned change author.

## 2026-09-08 — W119114 claim119398 — baton.claude — in progress

**Revalidation before any edit.** The five owned paths in the current tree hash
exactly to review-119371's accepted baseline, so the preparation correction is
the state this proof builds on and no pinned ruling has drifted:

| Path relative to `v12/python` | SHA-256 |
| --- | --- |
| `tools/stage_execution.py` | `db280363bf8e1f7bc534a25dd163275a87aad3a21d784d330801823ce9f3cb60` |
| `tools/single_worker.py` | `5dfd0df1b393f87e6a48e75f0845b266c73d2929e5cd6ad53509e1c02ef9dc27` |
| `tests/tools/test_stage_execution.py` | `44dd0d4ccef341f4d33e41560a46fef4987b37fd8dc2d64f812e9b8884534b54` |
| `tests/tools/test_single_worker.py` | `95808aee8529d27bab0519f3fe8d45ae4e51507594c4825495530a8882d9af6c` |
| `tools/parallel_test.py` | `f00fec0efebca9df1e25c025d1c9f07d350d1c79f0f0c880e673888bac884547` |

Re-read against the tree: this record's FINDING/PLAN, the parent assembly
FINDING/PLAN and `review-2026-09-08T12-41-47Z.md`, the accepted preparation leaf
and its `review-2026-09-08T13-16-48Z.md`, the port contract
`../finding-integration-runtime-port/HANDOFF-CONTRACT-2026-09-08.md`, and
W105982's `review-2026-09-07T15-46-38Z.md` for the exact remaining custody check.

### The one composition defect this proof exposes before it can run

`StageComposition.end` resolves the review verdict through the deployment's own
`verdict` seam and calls the explicit-operand `review_driver.end_review`. The
acceptance forbids a manufactured review verdict, so that seam cannot carry this
proof. W110772 has since delivered and independently accepted the production
channel — `review_driver.end_review_from_result`, which reads the reviewer's own
namespaced claim back out of the immutable frozen review result and cross-binds
it to the attempt, assignment generation and checkpoint evidence. Its own record
says the shared `tools/stage_execution.py` hookup is the assembly author's.
Wiring it is therefore inside this Work's existing five-path scope.

`_no_verdict` and `TheReviewersVerdictHasNoChannelAndIsNotInvented` are left
exactly as they are — no assertion is changed — and the supersession is recorded
in FINDING.md rather than by rewriting the history that reported the gap.

### Verification question and budget, recorded before any run

**Question:** does one submitted Job actually traverse implementation, an
independent review, one correction on the same persistent line, acceptance,
integration and terminal handoff over the real serving factory and ordinary
manager ticks — and do the real intake/retention/cleanup receipts still resolve
their retained bytes afterwards? No retained evidence answers it: every prior run
in this campaign stops at component boundaries, which is why the reviewer split
W119114 out.

**Scope and budget:** focused runs of `tests.tools.test_stage_execution` alone
while the proof is being built (~20s each), then one broader relevant sweep over
`tests.tools.test_stage_execution tests.tools.test_integration_worker
tests.tools.test_single_worker tests.integration.test_driver` (retained baseline
308 tests / 15.1s) once the focused acceptance is green. The whole-subtree gate
log `b4f19ea4…` is audited, not repeated, unless this candidate's own diff makes
it informative.

### Delivered: the composed implementation half and the mandatory custody proof

**One test path changed, and only additively:**
`v12/python/tests/tools/test_stage_execution.py`. No source path was edited, no
existing test method was touched, and no assertion was weakened.

| Path relative to `v12/python` | SHA-256 |
| --- | --- |
| `tools/stage_execution.py` | `db280363bf8e1f7bc534a25dd163275a87aad3a21d784d330801823ce9f3cb60` (unchanged) |
| `tools/single_worker.py` | `5dfd0df1b393f87e6a48e75f0845b266c73d2929e5cd6ad53509e1c02ef9dc27` (unchanged) |
| `tests/tools/test_stage_execution.py` | `bf7d2edee5417a6b94c5f5019a614893e388e5f55635cac3869669cfe9359cc8` |
| `tests/tools/test_single_worker.py` | `95808aee8529d27bab0519f3fe8d45ae4e51507594c4825495530a8882d9af6c` (unchanged) |
| `tools/parallel_test.py` | `f00fec0efebca9df1e25c025d1c9f07d350d1c79f0f0c880e673888bac884547` (unchanged) |

`parallel_test.py` needed no entry: its registry names modules and
`tests.tools.test_stage_execution` is already among them, so the three added
classes are collected without touching the shared registry.

**One `ComposedOneJobCase` fixture and three case classes, all new.** The
fixture composes the actual `operations_from` factory over real local
Authority/Job/Control/Integration stores, three configured roles, the real
checkpoint profile over a real version-controlled source, and a shared-Job input
manifest declaring the union of both stages' outputs. It drives ORDINARY
`job_manager.sweep` ticks and runs one REAL worker turn: the actual
`claude_agent` workload, entered through `baton_worker.serve_exchange` over
exactly the namespaces this deployment mounted.

Two deterministic seams, and both are the allowance this leaf's ruling grants:

- the ENGINE is a callable with no daemon, modelling three real facts — a
  stopped container stops running, a removed one is positively absent to a later
  inspection **in the engine's own absence sentence naming that identity**, and
  the custody helper answers the verb it was asked for. `Engine` alone could
  reach neither the freeze nor a settled cleanup, so this is what a real engine
  does rather than a shortcut around either;
- the PROVIDER inside the workload is injected exactly as `test_claude_agent`
  injects it. Version control is not simulated at all: the worker really commits
  the line, really bundles its objects and really runs the task's verification.

No daemon, container, image, network, live model or live credential is reached.

**What ran, measured at each owner's own durable record rather than from the
answer the composition returned:** the line materialized at the declared base;
the writer mounted it writable at
`<storage>/.baton-review-lines/<line>/checkout`; the worker committed it and
declared `baton.git-proposal/1` with `base` equal to the fixture's own base and
a different `head`; `output` reached `sealed`; `intake_receipt_of` answers a real
receipt; `retentions_of` answers one `retain`; the proposal published while the
producer assignment was still live; the checkpoint froze; and ordinary cleanup
settled at `retained` with `execution_runtime = destroyed`. One worker container
was ever started. The other stage's declared half is `missing-optional` rather
than invented, which is the shared-Job declaration set working.

**W105982's one remaining acceptance is complete**, and it is proved over bytes
rather than pathnames exactly as its review required: the retained artifact
reopens at its own recorded `custody_locator` and its measured tree digest equals
the receipt's; the retained result manifest reopens and names the same artifact
identity and digest; the custody tree is outside `roots['workspace']` — the
directory this attempt's container really had writable — and is the line's own
sibling; and the line survives at `review-ready` revision 1 with its checkpoint
pin REVALIDATED through the accepted profile against the real repository.

### The blocker, and why it is not worked around

The checkpoint freeze fences the producer assignment and the Authority installs
`runtime-quiescence:<generation>`. The review stage of a composed Job is another
assignment of the SAME Work, so its offer is refused every tick and the lifecycle
stops there. Nothing in this build discharges that gate. Filed as **W119548**
with canonical record `baton:work/records/2026/09/finding-v12-quiescence-gate-discharge/`
and an executable reproduction; baton.codex has since claimed it for interface
review and confirmed the missing composition. Three cases record the blocker as
a regression that fails when it lands; M119587 schedules their conversion.

I did not invent the discharge inside these five paths. The manager holds the
positive-absence evidence, but an assembly asserting it to the Authority would be
the deployment certifying the manager's own observation.

### The second defect, inside this scope and NOT fixed

`StageComposition.mount` calls `_prepare` unconditionally rather than through the
`_prepared` cache `end` uses, so a second `conclude` for the same attempt
re-grants the writer and refuses once the checkpoint has frozen:

    operation 'review-line.grant-writer:writer-…' is already recorded with a
    different kind or signature

Measured during this claim while the cleanup axis was left non-terminal. It
contradicts `end_implementation`'s own re-entrancy contract. Recorded in FINDING
and scheduled first in the next pass rather than attempted at the end of a claim;
the correct fix reads the existing writer back instead of re-granting one, and a
reviewer should see that stated before it is coded.

### Verification

Question, scope and budget were recorded above before any run.

- Focused, the owned suite: `PYTHONPATH=.:src python3 -m unittest
  tests.tools.test_stage_execution` — **105 tests, OK, 4.120s** (93 before, 12
  added).
- One broader relevant sweep, the four modules this candidate can affect:
  `PYTHONPATH=.:src python3 -m unittest tests.tools.test_stage_execution
  tests.tools.test_integration_worker tests.tools.test_single_worker
  tests.integration.test_driver` — **320 tests, OK, 16.638s**, against the
  retained 308-test baseline. It answers a real new question rather than ritual:
  this candidate patches `Engine.__call__` and inserts two `sys.path` entries at
  module import, either of which could disturb a sibling suite in one process.
  Neither does.
- **No whole-subtree run was performed, deliberately.** The retained gate log
  `b4f19ea440037846d4e1a5b0abfb3a84e4a0d8da05e1e66fa01770c4fe4f70c6` (5167 tests,
  275.509s, 28 failures) is audited rather than repeated; its diagnostics are 24
  boundary-inventory and 4 engine-cleanup failures owned by
  `work/records/2026/09/finding-v12-unresolved-suite-checks/` and unwaived. This
  candidate is one additive test file and cannot have moved them.

Evidence: `evidence/implementation-119398/` — `EXECUTION.md` and
`repro-quiescence-gate.py`, the standalone reproduction of the blocker.

### One working-tree observation that is not mine

`v12/python/tests/manager/test_boundary_inventory.py` carries 105 added lines in
the working tree (mtime 2026-09-08T13:20:18Z, minutes before claim119398). I did
not author or touch it, and it is outside this Work's five paths. Reported so its
ownership is explicit rather than swept into this candidate's diff.

### Not delivered here, and not claimed

The review round, the same-line correction, the acceptance, the integration
through the real port, the terminal handoff, the reconstructed-manager restart
and the preserved operator-held uncertain integration are all downstream of the
W119548 handoff and remain undelivered. The reviewer verdict channel hookup
(`end_review_from_result`) is decided and recorded in FINDING but deliberately
not coded, because it cannot be honestly proved until the review stage is
reachable.

**State: handed back blocked on W119548, with this bounded increment complete
and its evidence retained.**

## 2026-09-08 — W121887 claim121893 — baton.tuner

Implemented the separately allocated session satisfy_gate forwarder and related
wrapper documentation, with three additive controls. Exact operand/result
preservation, real AuthorityPort/session discharge/replay and unchanged refusal
propagation pass. Combined focused verification/audit0.514s within10s;
existing code/assertions are preserved. Initial new-assertion correction,
candidate hashes and all evidence are retained once in
evidence/session-forwarding-121893/EXECUTION.md. Awaiting independent acceptance;
the two-file reservation persists. Claude retains recovery and the assembled
lifecycle proof. Reporting guidance reread and adopted.

## 2026-09-08 — baton.claude, claim 121999

### Revalidation

All four prerequisites are accepted and were confirmed against the tree before
editing: W119548, W119733, W121887 and W120519. `tools/single_worker.py` hashes
to W121887's accepted candidate `ff383296…`, so its `_AuthoritySession.
satisfy_gate` forwarding is reused and not reimplemented;
`tools/parallel_test.py` carries the accepted registry line. Both are untouched
by this claim.

### Question and budget, before running

Do the two consumer seams the accepted drivers now expect behave correctly, and
does either change the meaning of an existing assembly assertion? Budget: about
20s — the assembly module, then the modules that reach these seams.

### Delivered — two bounded seams, not the assembled proof

**`Publication.published_of`.** The replay half `review_driver.
PUBLICATION_HISTORY` names, answered by `integration.publication_for_attempt`:
no publisher, no remembered selector, and deliberately NOT `self.published` —
an in-memory list satisfies the driver's shape and fails every restart.

**`StageComposition._prepare` recovers rather than re-grants.** `mount` called
it unconditionally and `_SingleWorker.ending` calls `mount` before `end`, so a
second `conclude` re-ran `grant_writer`, which refuses once the checkpoint has
frozen — the non-re-enterable ending this record filed against itself. `mount`
now reuses the prepared boundary, and for an attempt whose runtime is already
destroyed `_granted_writer` reads the writer back from the frozen checkpoint
instead of granting one. The accepted driver still binds that writer to the
attempt and generation, so a moved pointer refuses there rather than being
believed here.

### Verified

107 assembly tests OK (105 plus 2 additive); 456 OK across assembly,
single-worker, review-driver and integration-driver. Hashes, modes, commands
and budget: `evidence/consumer-121999.json`.

### Still owed by this Work, and not claimed

The ending-obligation registration and settlement with the gate discharge; the
`end_review_from_result` channel replacing `deployment.verdict`; the three
approved assertion conversions; and the assembled factory/tick-driven
correction, acceptance, integration, terminal handoff, restart and held
integration. This claim delivered the two seams the accepted providers require
and did not begin that proof.

### Next

Independent review of these two seams, or a fresh claim to continue the
assembled proof.

## 2026-09-09 — baton.claude, claim 128468

**Claimed first**, at seq128468, before any edit.

### Revalidation against the tree, not against pinned text

Every blocker this Work waited on is closed satisfying: W119113, W119548,
W119733, W121887 and W122060. `first_open_blocker` is null, so the gate the
PLAN names as the entry condition is actually released rather than assumed.

The current acceptance is `RESTART-ACCEPTANCE-2026-09-09.md` under the campaign
04:13Z ruling and M124896/M125007. The earlier same-attempt intermediate
continuation and pre-intent adoption text in FINDING.md is historical, and I am
not treating it as a gate.

W122060's accepted candidate is in the tree and carries far more of this
lifecycle than the PLAN's text anticipated: `TheComposedJobTraversesReview
AndAcceptance` and `OrdinaryTerminalLifecycle` already drive implementation →
handoff → real reviewer container → accepted verdict → correction on the same
line → integration through the accepted port → terminal handoff, plus the
uncertain-integration hold, the committed-handoff cut before local
acknowledgement, and a separate-process read-only observation. The PLAN's
instruction is explicit about what that means for me: reuse it, and "run only
what is missing or invalidated by changed bytes."

### What is actually missing

Reading the current acceptance against the current tree, one required result
has no control: **safe abandonment of unfinished scratch work** — stop/fence
the old worker, prove exclusion before a fresh assignment can write, and let
that fresh assignment repeat from the last committed handoff/checkpoint without
duplicating a committed effect. The committed-handoff cut proves recovery of a
handoff; it does not prove that a still-live stale writer is excluded first.

The joined custody re-verification also currently sits on the implementation
half (`TheRetainedResultReopensAfterOrdinaryCleanup`), not on the accepted
checkpoint the terminal lifecycle actually integrates.

### Question and budget, declared before any run

Does one submitted Job traverse the whole composed lifecycle on ordinary ticks
with its retained bytes and pins still verifiable afterwards, and can an
unfinished worker be fenced so a fresh assignment repeats from the last
committed handoff/checkpoint without duplicating a committed effect?

Budget: **600s cumulative** for this Work. That is larger than earlier focused
allowances on purpose — these cases run real version control and real worker
subprocesses, and the final assembled regression runs the serial lane. Each run
is recorded with its exact command and wall time; no reset.

### Delivered — the one missing result, and the joined custody

**`UnfinishedWorkIsFencedBeforeAnythingRepeatsIt`** (4 cases). One Job driven
to the committed changes-requested handoff; the correction round started and
left unfinished with uncommitted scratch in its writable mount; then an
**operator declaration** through W44716's accepted `abandon_attempt`, made
against the deployment's own control store, port and adapter. Nothing was added
to the composition — `abandon_attempt` says calling it IS the declaration, and
`single_worker.conclude` says deciding it is not this composition's.

Proved: the engine really removed that exact runtime and the attempt settled
`destroyed`/`retained` on positive absence; the Authority fenced the exact
generation the attempt held, replayed through the operation the declaration
itself named, and blocked the Work behind `runtime-quiescence:<generation>`;
the reviewed checkpoint, the committed route and the first round's publication
are byte-identical afterwards; and the scratch reaches no proposal.

**Two cases added to `OrdinaryTerminalLifecycle`** carry the mandatory custody
check onto the joined chain rather than only the first round: the CORRECTION's
retained artifact reopens at its own recorded locator with a measured tree
digest equal to its intake receipt's, it was never inside that round's writable
mount, and the integration eligibility names the correction's checkpoint — whose
writer is the corrected attempt and whose pin revalidates through the accepted
profile against the real repository.

**`tools/parallel_test.py`**: one comment corrected. The entry still said this
module "owns no engine … and starts nothing", which stopped being true when the
composed lifecycle landed. It is still PARALLEL for a narrower reason, now
stated. No member added, removed or moved.

### Blocked, reported rather than worked around

The acceptance's other half — restart from the last committed
handoff/checkpoint — **does not happen**, and I measured why rather than
arranging for it. After the declaration, ordinary ticks reach `implementation:
exceptional` with review and integration blocked, and no fresh attempt is ever
prepared. Three causes, all outside this Work's five paths:

1. **The episode never ends.** The declaration ends the ATTEMPT; nothing ends
   the stage's live EPISODE. `projection.replaceable` needs an ended episode
   whose ending is in `documents.REPLACEABLE_ENDINGS`, whose single member is
   `abandoned-after-restart` — the ending a manager records when a RESTART
   cannot account for an offer's bearer. An operator's declaration is not that
   ending and produces none, so `manager._replace` never opens a successor.
2. **The line is still held.** The abandoned attempt's writer is still `active`
   and the line still `writing`. `grant_writer` admits a writer only from
   `idle` or `correction-ready`, and the only thing in this build that revokes
   a writer is `freeze_checkpoint` — which an abandoned attempt never reaches.
3. **The Work is still gated.** The fence installs
   `runtime-quiescence:<generation>` and nothing discharges it: the ordinary
   discharge is an ENDING's, and this attempt has no ending to carry the
   positive-absence evidence — even though the abandonment observed exactly
   that absence.

`test_no_fresh_assignment_follows_the_declaration_and_why` registers this and
FAILS when the capability lands, the same pattern this record used for the
undischarged quiescence gate. It does not say which of the three owners should
change.

### The assembled regression

**Serial lane: OK** — 19 shards, 507 tests, 0 failures, 17 skipped, including
the real image gate, real containers, `test_dogfood_arc_engine` and both
registered stage drivers.

**Parallel source: FAILED** — 5206 tests, 28 failures across 11 shards, and the
harness then refused to run the serial registry from that invocation, which is
why the serial lane was run separately. Every failing shard is a whole-universe
SOURCE scan, and **this claim changed no file under `src/` at all** — the two
edited paths are a test module and a registry comment — so none of them can be
mine. Attribution, measured:

- `authority.test_boundary.ExportedSurface` — the surface gained
  `open_readonly`; **W126880, my own candidate, unaccepted at `baton.bug`**.
- `authority.test_boundary.EveryDiagnosticIsBoundedByTheRule` — unbounded
  diagnostics at `store.py:_writable`; same candidate.
- `manager.test_dependencies.NoPublicOperationTakesInternalState` —
  `AuthorityPort:satisfy_gate` parameter `gate` is not a declared operand;
  W119548's forwarding.
- `manager.test_text_sweep` — the callable table does not name `cleanup_of`.
- `manager.test_boundary_inventory` (7 shards) — the declared owner
  `('caller', 'oci.py:OciAdapter.observe', 'document.Running')` is stale.

**Operational finding for the owners:** W126880 and W126887 were reviewed on
their focused suites only, and their candidates have consequences in four
whole-universe scans OUTSIDE their two-path allocations —
`tests/authority/test_boundary.py`, `tests/manager/test_text_sweep.py`,
`tests/manager/test_dependencies.py` and `tests/manager/test_boundary_inventory.py`.
Reported here rather than corrected: those paths are not this Work's.

### Runs

148 OK (15.702s baseline) → six class iterations (8.709s) → three probes (~1.8s)
→ 2 OK (1.240s) → 154 OK (17.901s) → 541 OK (29.008s) → parallel harness
(21.627s) → serial harness (~255s) → four attribution runs (~2.5s).
**173.7s of the declared 600s.** Commands, logs, probes and hashes:
`evidence/provider-128468.json`.

Passing back to `baton.bug` unaccepted. The joined lifecycle, the custody and
the fencing half are delivered and green; the restart half is a reported
blocking defect with three named owners, and W103083 still holds final joined
acceptance.
