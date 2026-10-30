# Current milestone — R1/R2 delivered for independent verification; S1 attribution next, then S4; B3 in the disjoint scope

R1/R2 done (PROGRESS 2026-10-30 "Harness corrections R1 and R2"; digests in
evidence/r1r2-2026-10-30/CANDIDATE-SHA256.txt). Awaiting independent
verification; S1 starts meanwhile in tests/manager/test_boundary_inventory.py only.

Authority: M384897 (independent review) and M384898 (owner selection), pinned
in FINDING. Milestones, finite: (R1) subtest outcomes bound to parent ids
structurally in `tools/parallel_test.py`, with fake-tree regressions for
message-only, parameters-only, message+parameters failures/errors/skips;
(R2) content-bound source identity for `test-all` (HEAD + digest over the
bytes of every modified/untracked file in the selected scope `v12/`, build and
evidence outputs excluded by a documented boundary), with a disposable-repo
regression proving same-status byte changes change the identity, TESTING.md §9
rewritten; both returned for independent verification. Then (S1) per-helper
attribution in `tests/manager/test_boundary_inventory.py`, each with a negative
probe that fails when the named check is removed or bypassed, `documents._emit`
credited for member names only; then (S4) probes exercising the named owner's
refusal. Ownership: K edits `tools/parallel_test.py`, `v12/python/justfile`,
`tools/source_identity.py` (new), `tests/tools/test_parallel_runner.py`,
`tests/tools/test_source_identity.py` (new), `TESTING.md`, and for S1/S4 only
`tests/manager/test_boundary_inventory.py`; no product edits in S1/S4.


B2 continuation delivered (PROGRESS 2026-10-30 "B2 continuation per M384894"):
5 probe fixtures fixed; `port` investigated; representative-case packet at
`evidence/b2-2026-10-30/REPRESENTATIVE-CASES.md` with reproductions; slices
S1–S5 proposed, not authorized. Owner review next. B3 then proceeds within
C7 (authoring lifecycle, credentials doubles, runtime lane settlement
assertion, reconciliation_worker) and C5 (next_run_flow), with the file
ownership and exclusions recorded in PROGRESS; launch-version drift
(test_launch, test_execution_limits) stays with the Work whose candidate
bytes carry it; test_secrets inventories join the S1–S4 decision.


Owner M384894 (2026-10-30): no weakening or exclusion; the broad campaign is
not yet authorized. K prepares `evidence/b2-2026-10-30/REPRESENTATIVE-CASES.md`
(exact code paths, call-chain evidence, focused reproductions) classifying each
case as absent validation / validated elsewhere / inventory attribution
limitation, for owner/copilot independent review; finishes the 5 probe-fixture
corrections; investigates the 2 `port` double owners; then proposes bounded
repair slices. B3 (C5 CLI drift, C7 authoring lifecycle) may proceed where it
does not overlap, with file ownership and sequencing recorded here.


B2 result (PROGRESS 2026-10-30 "B2 (C3 + C9)"): C3 green (dependency
inventory: 3 ids → 0, one dead product parameter removed); C9 stale entries
fixed (15 stale owners, 1 duplicate, the fourth recordless site). Remaining
C9: 696 unowned receiving entries (688 at HEAD), 190 unattributed validator
calls, 266 unprobed owned entries, 5 probe-fixture drifts, 2 `port` double
owners, and one settlement-behaviour assertion that belongs to C7/B3.

## B2 decision (owner)

The remaining boundary-inventory debt is committed product debt, not stale
bookkeeping: making `tests.manager.test_boundary_inventory` green honestly is
a product-wide ownership campaign (~650 crossings to own across ~16 modules,
~190 helper validations to attribute, ~266 probes to write). Options:
- D1: schedule it as its own bounded Work (or several, by module), keep
  W384870's final acceptance conditional on it, and sequence B3–B5 around it.
- D2: re-scope the receiving-domain rule in the specification (which modules
  it binds today) — a DESIGN/specification change requiring the owner's
  explicit approval before any expectation changes; K has not touched them.
- D3: accept the debt explicitly as an owner-recorded exclusion with
  rationale — same caveat: it is a specification decision, not a repair.
K recommends D1. Small remaining C9 items (5 probe fixtures, 2 `port`
owners) can be finished inside B2 once the direction is chosen.


Authorized by owner M384892 (2026-10-30). Rule: distinguish stale inventory
entries from genuine architectural violations; never change an expected value
merely to pass or weaken the accepted specification; surface any concrete
scope/specification decision to the owner. Focused verification (`just
test-group scans`, `test-one` on the two modules). B1 remains reported, not
independently accepted; that review and the corrected-accounting verification
are acceptance obligations, not B2 gates. Git deferred by the owner.


B1 (C1 circular import: product fix; C2 admission fixture: test fix) is done,
with the Podman removal (M384888), the retained-directory test removal
(M384890) and TESTING.md + README + AGENTS.md policy (M384887); see PROGRESS
2026-10-30 "B1 and the owner-selected cleanups" and
evidence/PODMAN-REMOVAL-2026-10-30.md. Packaged group is green (24/24), so C8
is closed with C1. Next after owner review: B2 (C3 + C9 inventories).

Initial-access prerequisites (M384889, for B4): the four cases in
tests.manager.test_private_line_access_engine need
`BATON_V12_INITIAL_ACCESS_ENGINE=1`, `BATON_V12_PRIVATE_LINE_IMAGE=sha256:<64 hex>`
(an operator-approved installed image id) and `BATON_V12_WORKSPACE_GROUP=<gid>`
(a dedicated workspace group). K will present the exact operator commands
(image selection or build, group creation, variable export for the run) when
B4 starts; `test-all` does not set them itself (TESTING.md §2 limitation).


Owner (2026-10-30) accepted the RECONCILED attempt-3 run as the repair
baseline and authorized B1. Also in this milestone, by owner rulings
M384887–M384890: `v12/python/TESTING.md` with README and AGENTS.md links and
policy; bounded Podman removal; removal of the retained-directory test with
disposable coverage; initial-access prerequisites prepared in B4. Acceptance
obligation carried: INDEPENDENT verification of the corrected accounting
(started ids, fixture events, never-started tests) before W384870 acceptance.
Focused verification only; no full run before B5 unless selected.

Required-skip status after reconciliation: podman engine variants 8 class-level
+ 5 per-test (98 tests) → REMOVED with the Podman surface (M384888);
initial-access private-line engine 4 → REQUIRED, prerequisites in B4
(M384889); retained-destination fixture 1 → test removed, behaviour covered by
disposable fixtures (M384890). After these, the optional-skip registry holds
exactly the two owner-classified proofs.

B0 record (historical). The controlled baseline is
`evidence/b0-2026-10-29/test-all.log` + `test-all.summary.json` + `ACCOUNTING.md`:
collected 11 239; RECONCILED (see evidence RECONCILIATION.md): passed 10 925,
optional skipped 2, per-test required skipped 10, failed 102, errors 88,
never started 112 (8 class-level podman skips across 7 modules, 2 class-level
errors), 6 min 5 s.
Deviation recorded: two full executions were made at B0 (attempts 2 and 3).
Human Git checkpoint still due: `B0: controlled v12 test groups and accounted baseline`.

Checkpoint: W384870 events through E384883, T384870 through M384881 plus
this session's owner approval; dispatch running; managed services stopped.

---

W384870, queued at baton.decide, unclaimed. Status: clarified plan APPROVED
by owner (FINDING "Owner approves the clarified plan with selections"):
§§3, 5, 7 settled as written below, N1 and claim arrangement A selected,
leftover-directory cleanup approved. Preparation complete; B0 starts
once the owner holds the claim at baton.decide (arrangement B, §10).
Authority: FINDING.md owner rulings.
Evidence: `evidence/baseline-2026-10-29/` (recovered partial baseline).

Checkpoint: read W384870 events through E384879 (pass to baton.impl) and
T384870 through M384876.
Dispatch running since 2026-10-29T22:12:38Z (generation 133); managed services
stopped. Claim arrangement A selected (§10); packet under `config/`.

## 1. Inventory (static, current tree, 2026-10-29)

- Suite `v12/python/tests`: 181 `test_*.py` modules, ~10 406 `def test_`
  (baseline counted 11 136 tests because subtests expand).
  authority 13 · job_manager 26 · manager 81 · integration 9 · tools 52.
- Baseline command: `just --justfile v12/python/justfile test`
  = `PYTHONPATH=src python3 -m unittest discover -s tests -t . -v`, one serial
  process, ambient interpreter. 1334.7 s.
- Existing parallel runner `v12/python/tools/parallel_test.py`
  (`just --justfile v12/python/justfile parallel-test [JOBS]`): explicit
  fail-closed registries, PARALLEL 104 modules, SERIAL 19, SUPERVISED 1,
  METHOD_SPLIT 2 classes. 57 modules on disk are in no registry, so the runner
  refuses today; `tests.tools.test_parallel_runner` fails for the same reason.
  Mapping: `evidence/baseline-2026-10-29/module-registry.tsv`.
- Legacy Node suite: `v12/package.json` (`baton-v12-poc`, `npm test` =
  `node --test test/*.test.mjs`, 28 files under `v12/test/`, product under
  `v12/src/*.mjs`). Classification proposed in §7.

## 2. Test groups — an exact partition by module

Groups are DISJOINT module sets; every module on disk belongs to exactly one
group and exactly one runner class (parallel, serial, supervised, packaged).
The earlier G3/G9 overlap is removed: the scan modules leave G3.

| Group | Modules | Runner class | Needs | Baseline fail/err (recovered) |
|---|---|---|---|---|
| G1 authority | tests/authority (13) | parallel | nothing | 3 |
| G2 job_manager | tests/job_manager (26) | parallel; review_driver serial | nothing | 5 |
| G3 manager-pure | manager modules not in G4/G8/G9 (≈60) | parallel | nothing | ~120 (C4, C7) |
| G4 manager-engine | SERIAL registry manager modules (15) | serial | Docker daemon, built worker images, egress for the dogfood image | ~30 (C6) |
| G5 integration | tests/integration (9) | parallel; test_driver serial | nothing | 15 (C1, C2) |
| G6 tools-pure | tools modules except G7 and the two engine tools (46) | parallel | `just`, git | ~75 (C5, C10) |
| G7 tools-packaged | test_packaging, test_packaged_creation | packaged gate | built distro | 11 (C8) |
| G8 supervised | manager.test_runtime_deadline_engine | supervised | W32577 supervisor + preloaded image | 1 |
| G9 scans | manager.test_boundary_inventory, test_dependencies, test_contracts_inventory, test_text_sweep, test_source_boundary | parallel, method-split | nothing; long poles | ~120 (C3, C9) |

The two engine tools modules (test_dogfood_arc_engine, test_dogfood_retry_engine)
join G4 by runner class. The partition is encoded once in the runner's
registry and checked mechanically: a module in no group, or in two, refuses the
run. Exact per-group id counts come from B0's first controlled run.

## 3. B0 execution scope (clarification 1)

Resolved: there is ONE first full run and it is B0's closing checkpoint, not a
discovery rerun. The "controlled per-group baselines" are the per-group
sections of that one `test-all` log, not separate earlier full runs.

- Before that run, B0 only changes harness and hygiene: register the 57
  modules into the partition, add the entries in §4, fix cwd-relative temp
  roots, run on the prepared environment. Focused verification during B0 is
  limited to the groups it touches: G6 (runner tests) and `test-group` smoke of
  one small group (G1) to prove the entry works.
- Then `just test-all` runs once, under the implementation claim, with the log
  retained in `evidence/b0-<date>/`. That log replaces the lost baseline as the
  controlled baseline: exact ids, per-group counts, skips with reasons, source
  identity, durations, environment.
- No full-suite run happens between B0 and B5 unless the owner selects a
  checkpoint. Batches B1–B4 verify with `test-group` on the groups they
  declare.

## 4. `just` entries (v12/python/justfile)

- `just test-all [JOBS] LOG=path` — the full supported run: each runner class
  executed exactly once (parallel phase, serial phase, supervised step,
  packaged gate), reported per group, with the accounting in §5. Non-zero on
  any failure, error, unaccounted id, or skipped required proof. `LOG=` is
  explicit, never /tmp. The log header records `git rev-parse HEAD`, a digest
  of the dirty paths, python, jsonschema, docker, uid, userns capability, CPUs.
- `just test-group GROUP [JOBS]` — one group of §2 through the same runner;
  refuses an unknown group.
- `just test-one ID…` — focused `unittest` ids on the prepared environment.
- `test` (serial discover) remains as a documented reference recipe, not the
  gate; `parallel-test` remains and `test-all` composes it.
- Required-proof variable (§7) so a missing prerequisite FAILS inside
  `test-all`, reusing the pattern `test_packaging` already has.

## 5. Coverage accounting (clarification 2)

No duplicate execution: because §2 is a partition and `test-all` iterates
runner classes once, each test id is scheduled exactly once. The runner's
existing collect step (child interpreters report exact unittest ids) produces
the EXPECTED set E over all modules on disk, including supervised and packaged
modules (collected, then routed to their gate). Every shard, the supervised
step and the packaged gate return per-id RESULTS R (pass, fail, error, skip
with reason). `test-all` proves and prints:

- `|E| == |R|` and `E == ids(R)`: every collected id has exactly one result;
  an id with no result is UNACCOUNTED and fails the run.
- a duplicate id in R fails the run (duplicate scheduling);
- a one-off cross-check in B0 only: the serial `unittest discover` id set
  equals E, proving the partition collects what discovery would;
- skips listed by id with reason, classified required/optional per §7; a skip
  of a required proof fails the run.

The final acceptance line is "collected N, passed P, optional skipped K,
P + K = N, failed 0, errors 0, duplicates 0, unaccounted 0", with every
optional skip listed by id and reason.

## 6. Environment classification (this host, 2026-10-29)

- Python 3.13.7 (lock requires ≥3.13): OK.
- jsonschema ambient 4.19.2 vs lock 4.26.0: MISMATCH. The gate runs on the
  prepared environment (`tools.environment`, `BATON_V12_VENV`), never ambient.
- Docker 29.1.3 present; podman absent; uid 1000; 32 CPUs.
- User namespaces not permitted (`unshare -rm` fails).
- /dev/shm is tmpfs.
- No built distro unless `just build` ran.
- Pollution: 61 leftover `v12/python/v12-w71917-*` directories in the package
  root; 48 baseline errors reference them. Cause confirmed: `tests/manager/
  disk_roots.py` tries `tempfile.gettempdir()` (tmpfs here) then the
  distribution directory before `/var/tmp`. Cleanup APPROVED (owner); paths
  recorded in `evidence/leftover-test-directories-2026-10-29.txt`; removal
  and the chooser fix happen in B0 under the claim.

## 7. Skips, required versus optional proofs, exclusions (clarification 3)

Default: every test in G1–G9 is REQUIRED. Only the proofs below are classified
otherwise; each stays enumerated by id in every `test-all` log.

| Proof | Classification | Rule in test-all |
|---|---|---|
| G7 packaged bundle (test_packaging, test_packaged_creation) | REQUIRED | `test-all` builds the distro (or names one) and sets the REQUIRED variable so absence fails, never skips |
| G8 supervised deadline engine | REQUIRED via supervisor | executed through the W32577 supervisor as a distinct step; its ids enter R; if the supervisor or image is unavailable the run fails; owner may exclude only by recorded rationale |
| G4 engine groups | REQUIRED | Docker present on this host; an unreachable daemon fails (`required=True` path of the engine fixtures) |
| `_stage_case is None` import guards (test_bootstrap, test_stack, test_pool) | REQUIRED | a skip here means fixtures failed to import; treated as a failure |
| Bind-mount userns proof (test_source_boundary) | OPTIONAL on this host | sibling case proves the same boundary (its skip text says so); skip allowed and listed; run on a userns-capable host when available |
| Large-workspace proof (`BATON_V12_LARGE_WORKSPACE_PROOF`) | OPTIONAL | host-capacity proof; listed; owner may select it once for final acceptance |
| Root-only skips (`skipIf uid==0`) | not applicable | run as uid 1000 |

21 baseline skips are expected to resolve to: G7 (≥9, becomes required),
userns (1, optional), large workspace (1, optional), the rest identified by
id in B0 and classified here before B5.

Legacy Node suite `v12/` (`baton-v12-poc`): separation from Python does not
exclude it; a classification is needed. Facts: it tests the Node-host design
that `v12/DESIGN.md` records as superseded (its decision-history row: "older
Node-host ... designs are superseded"); its last known run was 691 tests with
88 failing; nothing in the Python product imports it. Classification SELECTED
by owner: N1. The superseded Node prototype is excluded from supported
acceptance with the recorded rationale (DESIGN supersession, no product
dependency); not repaired; files retained unchanged until a separate owner
decision retires the directory. (N2, a frozen reference gate with its 88
failures repaired or accepted, was not selected.)

## 8. Failure clusters (368 report blocks: 220 failures, 148 errors)

| # | Cluster | Modules (count) | Symptom | Likely nature |
|---|---|---|---|---|
| C1 | Circular import role_contract → integration.driver → admission | stage_execution, next_run*, read-completed subprocess (≥5) | ImportError `admit_candidate` from partially initialised module | product defect (uncommitted role_contract.py, W321776-era) |
| C2 | admission/manifests API drift | integration.test_admission (11), test_driver (4) | `'function' object has no attribute 'execute'` (`store._connection` is a method) | product defect |
| C3 | Dependency/parameter inventory stale | manager.test_dependencies (91) | `'uuid'/'urllib' not found in {…}`, `'component' not found` | inventory registries not extended for new modules; some genuine rule hits |
| C4 | Delivery root mode + leftover dirs | manager.test_integration_worker (62), input_delivery (22) | `ancestor is mode 0o775, manager established 0o700`; FileNotFoundError under v12-w71917-* | environment (umask) + hygiene; some product |
| C5 | job_manager CLI contract drift | tools.test_next_run_managed (34), test_next_run (11), next_run_flow (3) | `usage: job_manager --store --incarnation`, exit 2 | product/test drift |
| C6 | Engine groups | custody_engine (6), worker_image (5), lifecycle_composition, negative_race_endings, ended_runtime_adoption, oci_integration, worker_entry_engine, integration_image (≈20) | `[1000,1000] != [65532,65532]` (14); daemon/image state | environment (uid mapping) + image build state |
| C7 | Attachment/authoring lifecycle | authoring_shutdown_deadline (11), authoring_enforcement (8), authoring_manager_guard (7), credentials (4) | `'retained' != 'complete'`, `'running' != 'quiescent'` | in-flight W383239 settlement work; product or expectation |
| C8 | Packaged bundle | test_packaged_creation (10), test_packaging (1) | stale or absent bundle | environment; the gate must fail, not skip |
| C9 | Boundary inventory | manager.test_boundary_inventory (28) | `'provider_context'/'jobs'/'authority' not found`, KeyError provider_context | inventory vs new boundary entries (verification views, provider context) |
| C10 | Singletons | launch (6), execution_limits (6), correction_restart (5; setUpClass ×2), secrets (3), authority.test_boundary (3), parallel_runner (1), stage_execution_hardening (1), environment, single_worker, text_sweep, source_boundary, quiescent_finalization, runtime_lane (2), reconciliation_worker (2), job_manager ×3 | individual | triage each |

Recovered identifiers: 316 of 368 (`evidence/baseline-2026-10-29/baseline-failures.txt`).
Cluster "nature" is a hypothesis from symptoms, not an established root cause.

## 9. Repair sequence (six batches, preserved)

1. B0 harness + hygiene, closing with the one controlled `test-all` (§3).
2. B1 C1 + C2 (imports, API drift).
3. B2 C3 + C9 inventories.
4. B3 C5 CLI drift; C7 authoring lifecycle (coordinate with W383239 bytes).
5. B4 C4 + C6 environment/engine; C8 packaged gate made required.
6. B5 C10 singletons; skip classification completed (§7); final clean
   `just test-all` with retained log, source identity, durations, environment,
   and the §5 accounting line at zero failures, errors and unaccounted ids.

Each batch declares its groups and verifies with `test-group`; full runs only
at B0 and B5 or an owner-selected checkpoint. Human Git checkpoint due after
B0 and after B5 at least.

## 10. Manual implementation claim arrangement — B selected (A superseded 2026-10-29)

Owner now selects arrangement B: W384870 is held by Slawomir at
`baton.decide`; K implements as interactive copilot `baton.prompt` with
authorship recorded in PROGRESS.md. Generation 16 is NOT activated and K
never claims as baton.k. Owner commands, each standalone, as baton.slaw:

1. `/home/sl/opt/baton/v11/0650c61/bin/baton --config /home/sl/baton-v11.14aecfb/baton.json --participant baton.slaw reroute work=W384870 to=baton.decide reason="Arrangement B: owner-held claim; K implements as interactive copilot"`
2. `/home/sl/opt/baton/v11/0650c61/bin/baton --config /home/sl/baton-v11.14aecfb/baton.json --participant baton.slaw claim work=W384870`

The text below this line is the superseded arrangement-A history, kept as is.

### Superseded: arrangement A (2026-10-29)

Owner selected A: a dedicated interactive `baton.k` implementer identity.
Packet: `config/activate.sh` installs `config/baton-generation15.json`
(participant `k`, roles `["impl"]`, impl instructions naming baton.k,
generation 15) and accepts it with `regen` as baton.slaw. Managed services
stay stopped, so no other impl handler can claim.

Owner commands, each one standalone (B = the deployed binary with its config):

1. `bash /home/sl/src/baton/work/records/2026/10/finding-v12-controlled-test-groups/config/activate.sh`
2. `B --participant baton.slaw claim work=W384870`
3. `B --participant baton.slaw pass work=W384870 to=baton.impl comment="B0 under W384870 plan; interactive baton.k only"`

Generation 15 was accepted and steps 2 and 3 were done (E384879), but
`routes.impl.handlers` lists only `claude`, so baton.k is not yet eligible.
Correction: owner runs `config/activate16.sh` (generation 16 adds `k` to
`routes.impl.handlers`; nothing else changes; no claim or pass repeated).

Then K, as `baton.k`, issues `claim work=W384870` alone, reads detail,
work-events and the thread, and starts B0. At B0's end K passes back:
`pass work=W384870 to=baton.decide comment=<B0 evidence>`; the owner reviews
and passes again for B1, and so on through B5. `baton.prompt` never claims.

## Next executable milestone

B0 (§9 item 1) under the owner's `baton.decide` claim (arrangement B),
after the owner's reroute and claim (§10). Deliverable: harness entries, partition registry, temp-root
fix and cleanup of the recorded leftover paths, then the one controlled
`test-all` with its retained log under `evidence/b0-<date>/`, passed back to
baton.decide for review.
