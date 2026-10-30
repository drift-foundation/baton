# V12: controlled test groups and a clean full-suite baseline

W384870 (kind decide, route baton.decide, priority high), created 2026-10-29T16:10:02Z
by baton.prompt from the owner's ruling in T384870 (M384870). Owner: Slawomir.
Interactive-only coordination: Slawomir plans, reviews and accepts with the
baton.prompt copilot; K (Claude) implements in her interactive session. Manual
handoffs only between baton.decide and baton.impl. No other agents, managed
reviewers, background readiness consumers or delegation.

## Owner ruling — 2026-10-29T16:10Z (T384870 M384870)

Pinned here verbatim in substance; the message is the evidence, this is the record.

- Planning milestone (owner-held): inventory the v12 Python suite and the
  existing just/parallel runner; propose one unambiguous `just` full-test entry,
  logical test-group entries and focused individual-test usage; classify
  Docker/build/environment requirements; cluster the retained baseline failures
  before product edits.
- Baseline: `/tmp/baton-v12-python-tests.log`, 11136 tests in 1334.733 s,
  failures=220, errors=148, skipped=21. Preserve it in the canonical dossier;
  no discovery full-suite rerun.
- Implementation follows owner approval of the group map and repair plan.
- Every supported test accounted for; new work declares affected groups and
  runs focused verification by default; full-suite runs only at explicit
  integration checkpoints.
- Reuse the existing runner where suitable. Repair product defects and
  incorrect tests; remove obsolete tests only with documented rationale and
  review. Investigate every skip and define required environment so missing
  prerequisites cannot yield a false green.
- Final acceptance: a complete clean supported full-suite run, no failures or
  errors, no silently omitted required tests; retain logs, exact source
  identity, durations and environment. Pre-existing failures are not waived.
- Legacy Node reference suite stays explicitly distinguished from the Python
  product suite; any exclusion needs a documented reviewed classification.
- Test changes within scope are authorized. No product/design weakening, live
  models, deployment changes or Git mutation. Not routed to baton.bug,
  baton.tune, baton.codx or baton.merge. Preserve uncommitted W321776 and
  other candidate bytes; coordinate overlap. Dossier before implementation.
  The Work does not start implementation or tests automatically.

## 2026-10-29 — Observed: the baseline log was lost; evidence recovered

**Observed.** `/tmp` is tmpfs on this host and the host rebooted 2026-10-29 at
15:50 local (21:50Z), after the baseline run and after W384870 was created.
`/tmp/baton-v12-python-tests.log` no longer exists anywhere on the filesystem.

**Recovered.** The earlier copilot session's local transcript captured the
summary, the run command, the per-module and per-symptom counts over all 368
report blocks, and 316 of the 368 exact FAIL/ERROR identifiers. Saved under
`evidence/baseline-2026-10-29/` with provenance in its README. Labelled as
recovered partial evidence; exact source identity of that run is unknown.

**Confirmed.** The baseline command was
`just --justfile v12/python/justfile test`, one serial `unittest discover`
process over `tests/` with `PYTHONPATH=src` on the ambient interpreter
(Python 3.13.7, ambient jsonschema 4.19.2 vs lock 4.26.0).

**Inferred.** The ~52 unrecovered identifiers are mostly in
`tests.manager.test_dependencies` and `tests.manager.test_boundary_inventory`
(module totals 91 and 28 are known; the id list was truncated). They will be
re-enumerated by the first controlled group run under the agreed group map,
not by a discovery full-suite rerun.

## 2026-10-29 — Observed: claim admission and identities

**Confirmed** in the deployed authority (0650c61, `transitions.py` claim path):
while dispatch is not `running`, EVERY claim is refused inside the write
transaction, including a direct human CLI claim. Slawomir resumed dispatch at
2026-10-29T22:12:38Z (control generation 133). All managed services in
`/home/sl/baton-v11.14aecfb` are stopped, so no background consumer can claim.

**Open.** The configured `baton.impl` handlers are `baton.claude` (the managed
claude-acp service) and `baton.codxpc` (codx-pc). Neither is an interactive-K
identity. Supported options for the implementation claim, for the owner to
select:

- (a) config regen adding an interactive implementer participant with role
  `impl`, then `pass` W384870 to `baton.impl` for that participant to claim;
- (b) owner holds the claim as `baton.slaw` at `baton.decide`; K edits as
  copilot under that claim, with PROGRESS entries attributed to it.

`baton.prompt` never claims. Planning while unclaimed is permitted.

## 2026-10-29 — Proposed: group map, entry commands, failure clusters

See `PLAN.md` (status PROPOSED, awaiting owner agreement).
Summary: nine logical groups (authority, job_manager, manager-pure,
manager-engine, integration, tools-pure, tools-packaged, supervised, scans);
three `just` entries (`test-all`, `test-group GROUP`, `test-one ID`) composed
over the existing `tools/parallel_test.py`; ten failure clusters C1–C10; a
six-batch repair order B0–B5. The legacy Node suite under `v12/package.json`
is classified outside the Python product suite.

**Observed** hygiene facts feeding the proposal: 57 of 181 test modules are in
no runner registry (the runner refuses; `tests.tools.test_parallel_runner`
fails for this reason); 61 leftover `v12/python/v12-w71917-*` directories from
earlier runs sit in the package root and are referenced by 48 baseline errors;
user namespaces are not permitted on this host (bind-mount proof skips by
design); no built distro is present (packaging cases skip unless built).

## 2026-10-29T22:34Z — Owner agrees with the direction (T384870 M384874)

Slawomir agrees with the proposed test-group and repair-batch direction,
subject to three clarifications settled before execution: (1) one clear B0
execution scope with no discovery full-suite rerun; (2) coverage accounting
that avoids duplicate execution across groups and proves collected versus
executed identities omit no required test; (3) required-versus-optional
classification of skipped proofs and an explicit legacy Node suite
classification, since separation from Python alone does not authorize
exclusion from acceptance. The six-batch direction and the final acceptance
(a clean complete supported run with retained evidence) are preserved. The
manual implementation claim arrangement stays unresolved and is presented
separately from test strategy. This authorizes planning clarification only;
no tests or implementation before execution scope and claim arrangement are
settled. Manual handoffs with interactive K only.

**Proposed** clarifications are in PLAN.md: §3 (B0 scope: harness and hygiene
first, then ONE `test-all` as B0's closing checkpoint, which becomes the
controlled baseline), §5 (exact module partition, each runner class run once,
collected set E equals result set R, unaccounted or duplicate ids fail,
required skips fail), §7 (required/optional table; Node suite choice N1
superseded proof-of-concept reference out of acceptance by recorded
rationale, or N2 frozen reference gate), §10 (claim arrangement A: new
interactive impl participant via regen; B: owner-held baton.decide claim).

## 2026-10-29 — Owner approves the clarified plan with selections (T384870 after M384875)

Slawomir approves the clarified W384870 plan with these selections, pinned here:

- B0 ends with ONE controlled full-suite run after focused harness
  verification. Further full runs only at B5 or an explicitly selected
  checkpoint.
- Disjoint groups and exact test-identity accounting. Corrected clean-run
  summary: passed + optional skipped = collected, with zero failures, errors,
  duplicates or unaccounted tests.
- Engine (G4), packaged (G7) and supervised (G8) coverage remains REQUIRED.
  The user-namespace bind-mount proof and the large-workspace proof are
  OPTIONAL; their skips are enumerated explicitly in every log.
- Node suite: N1 selected. The superseded Node prototype (`v12/package.json`,
  `baton-v12-poc`, `v12/test/*.test.mjs`) is excluded from supported
  acceptance with this recorded rationale: `v12/DESIGN.md` records the Node-
  host design as superseded; the Python product has no dependency on it. Its
  files are retained unchanged.
- Claim arrangement A selected: a dedicated interactive `baton.k` implementer
  identity. Packet prepared under `config/` (see below). Managed services
  stay stopped.
- Cleanup of the 61 leftover `v12/python/v12-w71917-*` directories is
  approved after confirming they are disposable test artifacts and recording
  the affected paths (recorded in
  `evidence/leftover-test-directories-2026-10-29.txt`).
- The dossier binding is already in place (baton.slaw, revision 1, seq
  384873); the earlier pending bind action is withdrawn.
- Once `baton.k` exists and K's claim succeeds: proceed with B0, then return
  its evidence for review. No other agents, background execution, live models
  or Git mutation.

**Confirmed: the leftover directories are disposable test artifacts.** All 61
are untracked, created by `tests/manager/disk_roots.py` (`mkdtemp` prefix
`v12-w71917-`) when the first candidate, `tempfile.gettempdir()`, is tmpfs and
the chooser falls through to the distribution directory before `/var/tmp`.
Contents are per-case fixtures: disposable `authority.sqlite3`/`control.sqlite3`
stores, `checkout` trees, fixture `credentials` directories keyed by attempt
digests, `storage` roots. Newest mtime 2026-10-29 06:34, oldest 2026-09-17;
117 828 KiB in total. Their removal is scheduled inside B0 under the claim,
together with the chooser fix (prefer `/var/tmp` or an explicit
`BATON_V12_DISK_ROOT` before the distribution).

**Prepared: generation-15 configuration packet** at `config/`:
`baton-generation15.json` (live generation 14 plus participant `k`, display
"K interactive", roles `["impl"]`, and the impl role instructions naming
`baton.k`; validated with the repository's strict `baton_work.config.loads`),
`base.json` (live config SHA-256
e38db7b3bcac500b12481c61a029d49891d9e7744e3bb4c37a2f5eb97adeb438 and the
candidate digest), `install.py` (drift-checked backup and replace),
`activate.sh` (install, then `regen` as baton.slaw, then an instructions
read-back as baton.k). Owner-only; `baton.prompt` cannot accept a regen.

## 2026-10-29 — Observed: generation 15 accepted, but `baton.impl` still resolves only to baton.claude

**Observed.** The owner ran the generation-15 activation, claimed and passed
W384870 to `baton.impl` (pass event E384879, comment "interactive baton.k
only"). Canonical `detail` resolves the route as endpoint baton.impl, route
`impl`, handlers `['claude']`.

**Confirmed cause.** In this configuration a route's eligibility is its
explicit `routes.<name>.handlers` list, not role membership: `routes.impl`
is `{"role": "impl", "handlers": ["claude"]}`, `routes.implpc` is
`{"role": "impl", "handlers": ["codxpc"]}`. Generation 15 added participant
`k` with role impl but changed no route, so `k` holds the role and no route.
Not a Baton defect: the eligibility model is explicit by design.

**Bounded correction (prepared, owner-only).** Generation 16 changes exactly
one value: `routes.impl.handlers` from `["claude"]` to `["claude", "k"]`.
Packet under `config/`: `baton-generation16.json` (validated with
`baton_work.config.loads`; diff against live is the generation number and that
one list), `base16.json` (live generation-15 SHA-256
3cf5fde616356fa640f7ac2cab050362179a59d74a15e5085aa1d356e0944f46), `install16.py`
(drift-checked, backs up generation 15), `activate16.sh` (install, `regen` as
baton.slaw, then a read-only `detail` as baton.k). No claim or pass is
repeated: the Work already sits queued at baton.impl and route resolution is
re-evaluated inside the claim transaction. baton.claude stays listed; its
managed service remains stopped, so only baton.k can claim. A dedicated
`implk` alternate route was considered and not selected: it would need an
owner reroute and is a larger change than the outcome requires.

## 2026-10-29 — Owner selects arrangement B, superseding arrangement A

Slawomir selects the owner-held arrangement B: W384870 stays assigned to him
at `baton.decide`; K implements as his interactive copilot (`baton.prompt`),
with K's authorship recorded explicitly in this dossier's PROGRESS.md and
evidence. This SUPERSEDES the arrangement-A selection above and the
generation-16 correction: do not activate generation 16; K never claims as
baton.k. Generation 15 (participant `k`, accepted) stays as history; `k`
holds role impl and no route, which is harmless. The `config/` packets are
retained as record and marked superseded; `activate16.sh` now refuses to run.

Supported owner commands, each standalone, as baton.slaw (owning-team
authority for `reroute`; route handler for `claim`):

1. `reroute work=W384870 to=baton.decide reason="Arrangement B: owner-held claim; K implements as interactive copilot"`
2. `claim work=W384870`

Then K proceeds with the approved B0 scope under the owner's claim and
returns B0 evidence for review. Test, accounting and acceptance requirements
are unchanged. No identity impersonation, no background services.

## 2026-10-29 — Observed during B0: the serial baseline ran 26 tests twice

**Confirmed.** Three test modules bound sibling `TestCase` classes in their
module namespace (test_job_task_delivery from test_single_worker;
test_retry_task_lineage from test_job_task_delivery;
test_stopped_settlement_joined from test_stopped_settlement_command), so
`unittest discover` collected those classes under both modules. The lost
baseline's 11 136 "tests" therefore included duplicate executions. Corrected
in B0 by importing the sibling module instead, and guarded: the runner's
collector refuses a module that binds test classes defined elsewhere, before
any shard runs. This is cluster C11 (test hygiene), closed in B0.

## 2026-10-29 — B0 delivered: the controlled, accounted baseline exists

**Observed** (`evidence/b0-2026-10-29/`): `just test-all` on the prepared
interpreter, HEAD 8876bf95 with 559 dirty paths (digest ba01e9d589bbf03b),
fresh bundle, supervised gate through its reviewed supervisor with the
preloaded image sha256:9b8c9882…1de8. Collected 11 239 = executed 11 239;
passed 11 037; optional skipped 2; required skipped 11; failed 102; errors 89;
duplicates 0; unaccounted 0. 6 min 5 s wall on 32 CPUs against the lost serial
baseline's 22 min. Every required test is now accounted for by id.

**Confirmed** hygiene outcomes: the 48 FileNotFoundError errors under
`v12-w71917-*` roots are gone (temp roots now land in /var/tmp); the 26
duplicate executions are gone; the 57 unregistered modules are registered;
the serial `unittest discover` recipe remains documented as reference only.

**Open for the owner.** Eleven required skips remain: 7 podman-variant engine
cases (`podman is not on PATH`), 4 initial-access private-line engine cases
(`BATON_V12_INITIAL_ACCESS_ENGINE` not enabled), 1 retained-destination
fixture case. Each needs an owner classification (optional with rationale, or
prerequisite enabled). Two files K touched for the duplicate fix already held
other Work's uncommitted candidate bytes (test_job_task_delivery.py,
test_stopped_settlement_joined.py); K's edits are the import lines only.

## 2026-10-30 — Owner readback M384885: two reconciliations recorded

**Deviation, recorded.** Two full executions were made at B0 (attempts 2 and
3), not the agreed one; attempt 1 was refused at collection. K reran after
fixing a regression K had introduced, without asking. All attempts retained.

**Accounting defect, confirmed and fixed.** The first B0 ledger counted tests
that never started (class fixture skipped or errored) as passed, and collapsed
all class-level skip events into one key. Corrected in the runner (started
ids, whole fixture ids, fixture skip/error categories, both failing);
reconciled from retained evidence without a rerun: 112 tests never started,
passed 10 925 (not 11 037), 8 class-level podman skips (7 modules), 2 class-level errors.
Exact account: `evidence/b0-2026-10-29/RECONCILIATION.md`,
`test-all.reconciled.summary.json`; PROGRESS 2026-10-30 entry.

**Open for the owner.** Required-skip classification now reads: 8 class-level
podman-engine skips covering 93 tests, 5 per-test podman skips, 4
initial-access private-line engine skips, 1 retained-destination fixture skip.
B0 acceptance and B1 remain pending.

## 2026-10-30 — Owner rulings M384887–M384890 and B1 release (session message)

Pinned from T384870 and Slawomir's session message of 2026-10-30:

- **Reconciled run accepted as the REPAIR baseline** (not final acceptance of
  the harness or suite). **B1 authorized**: C1 circular import and C2
  admission-API repairs. Independent verification of the corrected accounting
  remains an ACCEPTANCE OBLIGATION (carried in PLAN). Focused verification
  only; no additional full run before B5 unless explicitly selected.
- **M384887 — testing guide is required and following it is critical.** K
  authors `v12/python/TESTING.md` against the implemented runner and
  justfile, with concise links from the relevant README and repository
  `AGENTS.md`. AGENTS.md must require agents doing v12 test work to read and
  follow the guide, declare affected groups, use focused verification by
  default and respect explicitly selected full-suite checkpoints. Guide
  content: exact working directory and copyable `test-one`/`test-group`/
  `test-all` commands with argument order; prepared environment and
  prerequisites; logical groups versus execution shards; parallel/serial/
  packaged/supervised behaviour and isolation constraints; adding tests and
  keeping complete disjoint registry coverage; required versus explicitly
  optional skips; actual-started accounting, fixture-level skips/errors and
  never-started tests; non-zero conditions; retained logs, source identity
  and summaries; when full runs or retries need a selected checkpoint.
  Transient Work ids, failure counts and run history stay in the dossier.
  Honest about limitations. Documentation and policy links are required
  before W384870 acceptance.
- **M384888 — Podman removal.** Docker is the current product and acceptance
  target; retaining Podman behind an optional/excluded profile is REJECTED.
  Bounded removal of the Podman-specific surface (adapters, configuration,
  fixtures, tests, current documentation) preserving shared OCI abstractions
  used by Docker and preserving historical records/evidence. Not blanket
  permission to delete anything failing. Update registries, group accounting
  and TESTING.md; record removed paths/coverage; demonstrate required Docker
  coverage intact with focused verification. Supersedes the earlier
  optional-profile suggestion.
- **M384889 — the four initial-access Docker engine tests remain REQUIRED.**
  Prepare their explicit image and dedicated workspace-group prerequisites
  within the engine repair batch (B4), retaining writer-access, reviewer
  read-only and correction-continuity coverage. Missing setup is not grounds
  to skip. Owner runs operator commands when asked; present exact commands and
  purpose.
- **M384890 — remove** `test_and_the_RETAINED_RUN_composed_no_apply_input`
  (test_importing_fixture) which depends on the historical machine directory
  `/home/sl/baton-v12-lifecycle-200564-clean`. Authorizes removing the
  obsolete suite check only, never the deployment directory. Ensure the
  underlying delivery behaviour has reproducible disposable-fixture coverage
  (reuse or add). Not retained as an optional skip.
- Arrangement B continues; K's authorship recorded; Git deferred; no other
  agents or background dispatch. Correct stale dossier summaries.

## 2026-10-30 — Owner authorizes B2 (T384870 M384892)

B2, the dependency and boundary inventory repairs (C3 and C9), is authorized
under arrangement B. Preserve genuine dependency/boundary restrictions:
distinguish stale inventory entries from actual architectural violations; do
not merely change expected values to obtain passes or weaken the accepted
specification. B1 is reported complete, not independently accepted;
independent B1 review and verification of the corrected harness/accounting
remain acceptance obligations and do not block B2. Git remains deferred by the
owner and is not a continuation gate. Correction ordered: the Podman
class-level skips in the current summaries were EIGHT classes (across seven
serial modules; test_input_delivery held two), not seven — corrected in PLAN,
the removal evidence and the reconciliation note by dated addendum; historical
PROGRESS entries stand. Follow v12/python/TESTING.md. No additional full-suite
run before B5 unless selected; no other agents or background dispatch.

## 2026-10-30 — Observed in B2: the boundary-ownership debt is committed, product-wide

**Confirmed.** `tests.manager.test_boundary_inventory` fails at HEAD 8876bf95
with 688 receiving entries no validator owns, 190 unattributed validator
calls and 266 owned entries no probe reaches (working tree: 696/190/266).
Measured by running the same tests over `git archive HEAD`. The entries are
real public crossings in provider_context, workspaces, failure_cause, launch,
oci, context_delivery, documents, attempts, attempt_logs, intake, custody,
exchange, review_cycles, handshake and source_boundary. Per-module table:
`evidence/b2-2026-10-30/BOUNDARY-DEBT.md`.

**Done in B2** (stale inventory only, each justified in the test's own
comments): dependency inventory green; 15 stale stated owners relocated or
removed; one duplicate stated owner removed; the fourth recordless-cleanup
site pinned; one dead public parameter (`read_context_receipt(...,
workspace_storage)`) removed from the product rather than declared.
No expectation was changed to obtain a pass.

**Open for the owner — scope/specification decision** (PLAN "B2 decision"):
D1 schedule the ownership campaign as bounded Work; D2 re-scope the rule in
the specification (owner approval required first); D3 record an explicit
exclusion. K recommends D1. Also flagged: `settle_cleanup` exposes the
caller's open SQLite connection as a public parameter (declared with its
docstring's contract); the owner may want that boundary reviewed.

## 2026-10-30 — Owner response to the B2 decision (T384870 M384894)

Owner agrees with the proposed response: accepted requirements and clean-suite
acceptance are preserved; no specification weakening or exclusion of these
failures. Inventory counts alone do not establish hundreds of missing runtime
validations. Before any product-wide boundary campaign is authorized, K
prepares representative cases across the reported categories and modules —
exact code paths, existing validator/call-chain evidence, focused
reproductions — distinguishing (i) genuinely absent validation, (ii)
validation already performed elsewhere, (iii) inventory attribution
limitations, for owner/copilot INDEPENDENT review; K's classification is not
independent acceptance. K finishes the small B2 probe-fixture corrections and
investigates the two `port` double owners against accepted behaviour. The
validated classification then yields bounded repair slices (outcomes,
dependencies, overlap, acceptance evidence); the broad campaign is NOT yet
authorized. B3 may proceed within its selected CLI/authoring-lifecycle scope
where it does not overlap those changes; record actual file ownership and
sequencing. W384870 final acceptance stays dependent on resolving required
failures; independent B1 and corrected-accounting review carried forward.
Follow TESTING.md; focused verification only; no new full-suite run before B5
unless selected; arrangement B; Git deferred; no other agents.

## 2026-10-30 — Observed in the B2 continuation: the inventory counts measure attribution, mostly

**Confirmed by reading and reproduction** (`evidence/b2-2026-10-30/REPRESENTATIVE-CASES.md`,
`representative-reproductions.log`): of the 646 caller entries the inventory
reports unowned, 364 are validated through module-private helpers (`_text`,
`_hash`, `_component`, `_job_execution`, `named`, `_emit`, …), 38 through
private methods, 5 through named validators, 66 by inline exact-type or
membership checks; 90 are forwarded and 81 show no visible validation; 2 are
parameters never read. The 190 "unattributed" `boundaries` calls are those
helpers seen from the other side; the 266 unprobed entries are owned.
Reproductions R1, R3b, R4b, R5, R6, R7, R10 show refusals from those helpers;
R2 shows a store capability (`jobs=None`) escaping as AttributeError.

**Two product findings, unchanged, for the owner:** `workspaces.settle_cleanup`
never reads its `connection` parameter while its docstring states a
transaction contract (Case H); the intake discharge gates revalidate `port`
that `AuthorityPort.__init__` already owns (Case I). K's classification is not
independent acceptance.

## 2026-10-30 — Independent review accepted B1; harness corrections R1/R2; S1 then S4 authorized (M384897, M384898)

Independent owner/copilot review `review-2026-10-30T02-52-46Z.md` (evidence
`evidence/review-b1-accounting-20261030/`): bounded B1 C1/C2 ACCEPTED (178
tests, 29.992 s wall); the class-fixture accounting defects independently
verified fixed. Harness acceptance requests two corrections: **R1** `base_id`
treats message-bearing subtest failures (`test [message]`) as synthetic ids and
leaves the parent PASSED — bind outcomes structurally to parent ids at the
result boundary, preserve diagnostics, cover message/parameter failures,
errors and skips; **R2** `test-all` hashes `git status` text, not source bytes
— retain content-bound selected-source provenance including untracked inputs,
exclude generated evidence/build outputs by a documented boundary, detect
drift, document accurately in TESTING.md. Focused synthetic verification
suffices; no new full run.

Packet readback: provider_context helper validation confirmed; `documents._emit`
owns member NAMES only, not values (all-None members accepted) — never
blanket-credit it in S1; `settle_cleanup`'s unused `connection` does not alone
prove broken atomicity (transact/_record share the store connection); the
`port` method versus wrapped-session capability chain must be traced before any
guard removal.

**Owner selection (M384898):** bounded S1 attribution of DEMONSTRATED existing
validation — each attributed helper must demonstrably enforce the specific
claimed rule, with negative evidence that removing or bypassing that check is
detected — followed by bounded S4 probe authoring that exercises the named
owner and its required refusal (not merely silencing lists). S2/S3/S5 remain
per-case investigation; no blanket specification change, guard removal or
broad campaign. B3 continues under M384894's non-overlap authority. R1/R2
first, returned for independent verification. B1 bounded acceptance stands;
final harness and full Work acceptance pending. TESTING.md; arrangement B;
Git deferred.

## Decisions pending (owner)

1. Independent verification of the R1/R2 harness corrections and the S1 attribution (evidence/s1-2026-10-30/).
2. Review of S1 attribution evidence (per helper, with negative probes) and S4 probes as K returns them.
3. Cases H and I remain per-case investigation (S5), not authorized for change.
4. Git checkpoint remains deferred by the owner.

## 2026-10-30 — Owner selects scheduled-reboot stop after K handoff

Slawomir confirmed stopping after K handed over (latest M384903) and requested shutdown preparation. Execution stops pending explicit resume; no implementation or tests are selected during preparation. RESTART-20261030.md pins accepted versus reported outcomes, unfinished R2/S1/S4/B3-B5 work, persistent evidence, exact owner release/reclaim commands and observed runtime state. Owner-held arrangement B remains selected. The copilot does not release as baton.slaw, stop the unrelated MariaDB container, mutate Git, or initiate reboot. Older PLAN text is superseded for the immediate next action by this restart checkpoint; historical decisions remain intact.

## 2026-10-30 — Owner clarifies top-level development status

Slawomir explicitly directs the top-level README to state that v11 is development-frozen, v12 is the active development version, and readers should consult v12/README.md. This is documentation of the selected development direction; it does not switch the running coordination authority or authorize deployment. Interactive Codex copilot added that status and link near the top of README.md.

## 2026-10-30 — Owner selects portable development records and disk-backed scratch

Slawomir directs classification of outstanding files so development can resume on another computer: preserve source, tests, decisions and required evidence in version control; keep genuinely reproducible disposable outputs in explicitly ignored storage. This machine is not the sole trusted copy. Clarification: avoid `/tmp` by default because it is reboot-volatile and consumes memory on this host; reserve it for short-lived temporary files such as compiler side effects. Prefer ignored, disk-backed `work/scratch/` for disposable development scratch. Reboot persistence does not make scratch durable evidence.

Interactive copilot owns only this housekeeping documentation and inventory; K retains active source/test ownership. No Git mutation, deletion, dossier relocation or broad evidence ignore is authorized by this classification. Existing dossier files are preserved pending artifact-specific disposition. Large or sensitive required artifacts need a verified durable external copy and a checked-in locator/digest before their local copy can be treated as disposable; no such external backup is claimed here.

## 2026-10-30T08:20:12Z — Independent R2/S1/S4 review

See review-2026-10-30T08-20-12Z.md and evidence/review-r2-s1-s4-20261030/.
R2 remainder accepted for this checkout (88 focused tests OK, 16.469 s);
S4 first delivery accepted as partial progress. S1 needs two actual profile
witnesses: its newly stated restore_abandoned_correction and
settle_restoration_execution owners map to a base-class suite that never calls
either entry (independent spies: zero calls while witness passes). Correction
stays in the accepted scope; no new owner decision. Existing 47 missing probe
pairs and nine older unmatched declarations remain; do not confuse successful
probe execution with complete attribution. Absolute fixture checkout paths remain
a portability limitation. Owner checkpoint 84f66f43 now exists, superseding the
prior pending-checkpoint statement for the candidate; this review is new work.

## 2026-10-30 — Owner requires checkout portability; personal home paths are not prerequisites

Slawomir rejects treating hard-coded `/home/sl` fixture dependencies as a
permanent TESTING.md limitation: other developers do not have that home directory.
Repository fixtures and source must resolve from the checkout actually under test;
external resources need explicit configuration or private disposable fixtures,
never an assumed developer home. This supersedes the previous option to merely
refuse another checkout or document the limitation as a sufficient outcome.

K owns the bounded test portability correction after the current S1 witness
correction. Readback confirms the four reported REPO constants and two additional
consumers: tests/manager/test_attempt_logs.py:35 and
 tests/manager/test_claude_agent.py:2196. Audit other executable personal-home
references and their loaded helpers for real dependencies; distinguish deliberately
hostile path literals and historical prose from paths actually read. Do not rewrite
permanent historical evidence or alter unrelated deployment state.

Acceptance: affected fixtures use the selected checkout and its declared inputs;
focused tests from a differently named checkout/root succeed without reading the
original checkout or requiring `/home/sl`. Exercise resolution, not only a text
search. Missing inputs remain honest failures. Keep provenance aligned with the
bytes actually consumed, update TESTING.md when verified, and return exact evidence
for independent review. No full suite or live provider/engine is selected here.

## 2026-10-30 — Next target selected without interrupting current Work

Owner selects existing W383215 (native installed Job cancellation/admission
fencing) after this Work completes, with focused deterministic regular-suite
tests and no automatic full run per Job. The selection and exact test strategy
are pinned in ../finding-v12-native-job-cancellation/FINDING.md and PLAN.md.
W384870 acceptance and current K corrections remain first. No claim, route or
dependency change is implied by this planning entry.

## 2026-10-30 — Owner requires closure and complete Git checkpoint before switching

Slawomir clarifies the next-assignment boundary: W383215 must not start until
W384870 is independently accepted, formally closed on Baton, and all its final
changes, reviews, decisions and required evidence are checked in by the owner.
The checkout must be ready for handoff with no outstanding current-Job files.
This supersedes any earlier wording permitting a switch after acceptance alone,
or treating the final checkpoint as optional. Closure alone is insufficient;
a commit alone is insufficient. Revalidate canonical closure and the final Git
checkpoint/status before releasing the next assignment. Planning ahead remains
allowed. Agents do not mutate Git or impersonate the owner to satisfy this gate.

## 2026-10-30 — Owner requires visible version-level test commands

Slawomir directs v12/justfile to expose the supported test entries directly;
users should not need to know the implementation language or discover a nested
justfile. Interactive copilot owns the small forwarding recipes and guide/README
edits while K retains implementation ownership elsewhere. Expose test-one,
test-group and test-all with useful list descriptions, preserve the one existing
runner and accounting rules, and make v12/ the documented command entry point.
No full-suite run is selected by this usability change.

## 2026-10-30 — Independent acceptance and remaining active-tool portability fix

Review review-2026-10-30T08-51-30Z.md accepts S1 witness correction and the
six-module portability correction. Independent 202 focused tests pass in20.829s;
727 relocated tests pass in32.132s (48.921s traced wall), zero original-tree
accesses. Active live_ab/deployment.py still renders a personal registry path;
K must make that external input explicit and verify rendering/refusal
without live execution. Existing S4/B3 work remains authorized; B4/B5 and full
closure/check-in gate remain.

## 2026-10-30 — Owner refines the version-level test interface

Owner explicitly selects `just test` for the complete mega suite (a likely
nightly use, not an instruction to install a schedule). Focused selection stays
with test-one/test-group; expose group discovery as `list-test-groups` per owner
naming preference. Remove obsolete prototype test recipes from the active
interface. Agent execution-selection policy must not appear as a command usage
restriction. Copilot implemented the three-file interface/doc change; bare just
lists commands to avoid an implicit mega run. Full-run defaults retain logs on
disk-backed ignored work/scratch/test-all; required evidence must be promoted
before handoff. Existing prerequisites and accounting are unchanged. Small actual
entry smoke test, dry runs and group listing checked; no mega run was performed.

## 2026-10-30T09:29:47Z — Closure refused; B3 partial acceptance and C5 reproduced

See review-2026-10-30T09-29-47Z.md. W384870 is NOT ready to close. Independent
227 B3 focused tests pass (15.198s); bounded five-module fixes accepted. C5
still fails all3 outside the tool sandbox with the same confined-Git /dev/null
error (16.425s); owner also reports3 failures from the normal terminal. K must
trace the actual confinement/fixture chain, not dismiss this as the tool sandbox.
S4 _read_table changes request correction: actual unresolved SELECT crossings
cannot vanish from the inventory; static FROM plus dynamic WHERE also regresses.
Known cleanup/portability, C7, inventory, B4/B5 and final full-accounting work
remain. No closure or next-Job execution; final all-files owner checkpoint remains.

## 2026-10-30T16-20-31Z — restart review and corrected C5 diagnosis

C5 fixture correction and S4 P2 read-visibility correction ACCEPTED: 8 focused
tests pass in 30.224s. See review-2026-10-30T16-20-31Z.md. This supersedes the earlier C5
confined-Git /dev/null diagnostic direction and the pending-review status below:
the actual failure was reading the wire launch envelope as a decoded payload.
Unresolved table placeholders remain explicit debt, not accepted complete coverage.

K's next bounded milestone is C7's three shutdown modes/token settlement.
Live A/B registry portability, caller/closure/replay discovery, S4 probes, B4 and
B5 clean accounted full run remain required. Review the released version-level
command/docs changes too. No new owner decision or claim needed under arrangement B.
Close W384870 and check in all final files before starting W383215.


## 2026-10-30T17-17-47Z — C7 independent review: bounded guard correction

Read review-2026-10-30T17-17-47Z.md. Independent shutdown/enforcement run: 38 passed in 62.670s.
Envelope fit and token expectations are supported; no owner specification decision
needed. C7 still needs mode-specific reachability assertions so unintended early
refusal cannot recreate vacuous passes. Correct the claim of runtime execution in
all eleven modes: deliberate create-refusal and pre-invocation modes are distinct.
K returns focused evidence for this bounded correction before C7 signoff. Remaining
portability/inventory/B4/B5 and closure/check-in gates are unchanged.


## 2026-10-30T17-25-53Z — C7 and registry corrections independently accepted

Read review-2026-10-30T17-25-53Z.md: 14 focused tests passed in 61.019s.
C7 guard/evidence correction and explicit live A/B registry input accepted.
This supersedes their pending-review status and the C7 changes request below.
Next bounded K milestone: dynamic-table caller resolution, closure/replay inventory
discovery and S4 probes, preserving visible unresolved debt and genuine coverage.
B4, B5 clean accounted full run, final command/docs review, formal closure and
owner check-in remain required. W383215 is not released. No owner decision needed.


## 2026-10-30T18-07-52Z — inventory review: nested closure correction required

Read review-2026-10-30T18-07-52Z.md. Fourteen focused tests pass (18.998s), but an independent
nested-shadowing reproduction proves false ownership: _closure_pieces visits a
nested body's calls under the enclosing context as well as its own context.
K corrects scope traversal and adds negative evidence before inventory signoff.
New replay debt stays visible; counts await corrected discovery. This supersedes
the pending-review status below, not the outstanding B4/B5 and closure/check-in gates.


## 2026-10-30T18-13-59Z — discovery correction accepted; closure plan now required

Read review-2026-10-30T18-13-59Z.md: unchanged nested-closure reproduction passes; 15 focused tests
pass in 19.138s. This supersedes the closure changes request below. Whole Job
acceptance remains pending: eight scans failures, inventory/probe debt, B4 and B5.
Owner asks to finish the Job. K's next handoff supplies one finite closure plan
with exact failures, grouped debt dispositions, remaining required runs and operator
prerequisites, while continuing ordinary authorized repairs. No silent deferrals or
coverage waivers. Formal closure and all-files owner check-in still gate W383215.


## 2026-10-30T18:15:13+00:00 — fixed closure order and next K deliverable

Owner requests more specific direction. CLOSURE-CHECKLIST.md now fixes the sequence.
Next K handoff is only the bounded scratch-mount and exported-callable text-sweep
failures, with focused evidence and digests. Return before inventory/replay/B4 work.
Then six remaining scans failures in named groups, B4, B5, independent acceptance,
closure and all-files owner check-in. No speculative discovery expansion or blanket
coverage waiver. This supersedes the open-ended continuation in M384931.

