# W103525: evidence accepted, completion choices for discussion

2026-09-13T14:10:03Z — baton.codex, claim161114. Owner directions M161116
and M161128, pinned in FINDING at14:01:28Z and14:03:55Z. This is the requested
consolidation, not an implementation handoff or a request for a blanket allowance.

**Recommendation:** retain the proven trace foundation and four terminal imports
in each order. Select a small correctness tranche: actual code correction,
non-vacuous restart/provider counters, and W156162 managed integration. Decide
shared-slot configuration and session identity before authoring more fixture
loops. Defer priority enhancement and broad randomized/TUI coverage. Consider
dropping the explicit-only fallback rule in favor of the already accepted soft
affinity rule, but only by an explicit owner amendment. None of these proposed
dispositions has taken effect; full certification remains open.

## Evidence binding and review result

Only the two currently authorized new test files were reviewed; neither was
edited. Full SHA256s:

| Artifact | SHA256 |
| --- | --- |
| `v12/python/tests/tools/scheduler_trace.py` (93492 bytes) | `fa9e69f2df32b11cd2a830dc962900796e5aeb89398c50c5175d8e8e87ccf0d5` |
| `v12/python/tests/tools/test_scheduler_trace.py` (313954 bytes) | `a57c0a71e52629ee6008f054dccb1ef2d563bb886453b6bd8317daefe2437e17` |
| `trace-160959-composed.json` | `5a3ead46c46b5586cbd3a74d7454b402fd04dfbe34414e33a061ac9e90fb9303` |
| `trace-160959-composed.py` | `cfe80425e122ab1199be9378c7f3a6f853819549af6039bada8c3fb9e2f4114e` |
| `review-161114-a_before_c.json` | `1cd78f206510fba1a73b89546489365ad894cdc66d578e158314be720bfaa36c` |
| `review-161114-c_before_a.json` | `35bb0afd65ac089e04e35cc9f89f88980e1d90ecc6995c7685f27b3770ebab3a` |

**Confirmed independently:** `repro-161114.py` ran both current scenario methods
with the real owners and simulated engine/provider boundaries. Each fresh trace
has97 records,12 stage completions, four integration acts and four each of
verification/review/approval receipts. Every Job A/B/C/D terminates once. The
orders are A/B/C/D and C/A/B/D for integration. Each run captured three real
causal observer answers; each uses the same harness digest across failing
base-added, passing isolated and passing combined observations. Artifacts and
`review-161114-*-causal.json` retain all identities and answers.

`audit-161114.py` independently reread the exact author export:18 unique scenario
names and zero validator violations. Terminal author traces end at ticks34 and26,
under100. This was an artifact audit, not a fresh execution of all18 schedules.
Fresh execution was limited to the two terminal-order methods. Both have ZERO
`correct` acts, no sessions and no reopen. Validator success does not assert the
presence of every acceptance scenario.

Current source checks preserve scheduler SHA `aec56f1fe1d78bd50798403b46648c63c6c6231678971399da339246a7901194`,
projection SHA `db9b3f55fc09625a2f8394ed06313a29f02699ae39440dbbf1e3c5b3faa71641`,
and stage_execution SHA `02d83d92b6f9b0d44f42813239fb591b5d11fc13b35514665d5b4d36f6571d81`.
They match the export's environment source manifest. Scripted engine execution
does not prove actual Docker isolation, process absence or live-provider behavior.

## One acceptance and evidence matrix

Paths without a prefix below are within this dossier. Product/test symbols are
under `v12/python/`. “Accepted component” preserves its measured boundary; it is
not a complete-contract pass.

| Requirement | Independently supported status and reusable evidence | Remaining boundary; type |
| --- | --- | --- |
| Causal trace/oracle, replay, reservation before offer/accept/claim and effective-principal exclusion | Accepted foundation at prior reviewed boundaries; unchanged oracle hash above; PLAN items2–5 and prior append-only reviews retain the synthetic negative cases. Current artifact audit passes | Keep negative cases and distinguish synthetic invalid input from execution. No new broad oracle rewrite; final focused regression after affected changes. Test coverage |
| A→B dependency while C/D progress; alternate terminal orders | Accepted current two-team, ONE-target, four-producer/four-reviewer configuration. Fresh97-record traces each have all12 completions and four authorized imports | Combined two-repository/two-effective-slot/reopen/correction contract is not supplied by these traces. Fixture/configuration |
| Independent result judgments and authorized terminal integration | Current fresh traces contain one direct plus three reconciled imports each. Each derived result selects its own three judges and own receipt chain. The author now configures a distinct Work per Job/judgment kind | Host reconciliation and its verification are current execution behavior, not the newly required managed Docker architecture. Revalidate affected path after W156162. Product/isolation |
| Actual requested code correction | `composed-correction` has19 records and an owner-verdict-bound `correct` act into episode2. Existing `test_a_correction_opens_a_second_episode_on_the_same_line` stops after revised attempt preparation; only the first implementation completion is exported. Current terminal traces have zero corrections | Need revised code, completed revised implementation, accepted revised review and authorized import in the selected combined schedule, retaining old and new attempt/episode/verdict identities. Trace-label fixes are a DIFFERENT completed correction. Test/fixture gap |
| Durable reopen and no duplicate effects | `composed-reopen-and-continue` has15 records; fresh handles adopt B's still-running modeled runtime and finish A review. Source uses a nonzero engine launch count keyed by the attempt operand, plus an injected duplicate that makes comparison fail | Same-process recomposition with shared fake engine, no complete four-Job third schedule, no provider invocation count. Both session lists being empty cannot establish zero provider invocations. Need a counted deterministic provider boundary that actually executed before reopen and continued afterward. Test/fixture gap, product only if a concrete failure appears |
| Implementation/review session separation | `composed-role-sessions` has17 records and three distinct owner session references for consent/implementation/review; prior independent review accepted reference/assignment cross-checks | Session IDs were supplied at the public owner seam; this is separate identity bookkeeping coverage, not serving-session adoption or restart invocation evidence. Preserve this qualification. Coverage boundary |
| Healthy worker AND session across same-line correction | `composed-correction-continuity` proves the same configured worker is chosen for a new attempt and explicitly records missing session continuation. Current owner session row identity includes attempt/posture/epoch | No serving path proof of healthy provider conversation reuse across correction. Do not infer universal impossibility from attempt-keyed rows: provider conversation and owner row identities differ. Owner must choose intended identity/lifecycle, then bound adoption work. Product/contract choice |
| Two teams, two repositories, two effective implementation/review slots | Public scope/capability and wrong-repository component tests are accepted at their observed boundaries. Three configuration exports now correctly contain zero execution records. `test_four_jobs_do_bind_and_serve_across_two_repositories` and prior review preserve positive source/target bindings | Complete four-Job traces still use one target and four independent producer/reviewer records. Prior source-binding refusal for C/D is specific to reusing A/B's per-Work manifests. It is NOT proof no legal configuration can represent four per-Job records over two effective principals. Configuration feasibility must precede a product prerequisite. Do not bypass real identity/scope checks |
| Explicit-only fallback, work conservation | `scheduler.reserve` lines316–385 chooses a compatible idle alternative automatically when preferred worker is unavailable and records fallback; existing W71877 accepted soft affinity. Existing unit coverage and retained distinguishing gap remain valid | W103525's stronger explicit-only wording conflicts with that behavior and can conflict with keeping idle compatible capacity busy. Decide the rule; a test cannot settle policy. Contract choice |
| Composed unavailable-source-worker fallback | `_job_workers` lines4279–4341 retains exact source_worker_id plus Work/input/task compatibility; `_job_eligibility` excludes others before reserve. This is a safety boundary accepted by W130216 | Unit fallback does not prove another producer can serve this Job. A successor, if selected, must bind legitimate per-Job operands before admission and preserve principal/workspace independence. Product/configuration |
| Priority pool, affinity then creation chronology | Source `projection.owed_acts` sorts stage IDs; scheduler sorts compatible workers by worker_id and uses affinity within available workers. Current closed configuration has no promised priority contract; retained inversion case labels the gap | Implementing priority is a new scheduling feature, not a fix to the completed trace loop. No fairness/chronology certification from stable lexical order. Optional enhancement relative to isolation, still open under current acceptance |
| Dependency-conformant final verification | Every current export labels jsonschema4.19.2 vs pinned4.26.0, CPython3.13.7, conformant=false; initial missing-package failure remains recorded | Final selected certification must use a provisioned conformant interpreter/image with recorded lock/input hashes. Operator configuration task; no installation or live execution authorized here |

## Existing Work and exact reuse boundary

Canonical searches `schedul`, `session`, `pool`, `priority`, `fallback` and open
`environment` were read at snapshots161147–161164. Searches are title/prefix
discovery, not a claim of exhaustive semantic equivalence. Relevant detail and
records were read; no new dossier or mandatory backlog was created.

| Existing Work | Current canonical disposition and reuse |
| --- | --- |
| W103525 | Owns this evidence, acceptance choices and selected test-only completion. Keep unresolved proposals here until discussion selects them |
| W156162, `baton:work/records/2026/09/finding-v12-per-job-budgets/` | Existing owner of managed integration design. `MANAGED-INTEGRATION-DESIGN-2026-09-13.md`, `DESIGN-REVIEW-161103-2026-09-13.md`, M161127. Design review rejects unrepresented child-to-parent capacity charging; requires portable custody in slice one and names the missing target-owner entrypoint. Do not create a competing integration Work or presume design approved |
| W71877, `baton:work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/finding-concurrent-stage-scheduling/` | Closed satisfying. Its soft-affinity/occupancy decision and focused evidence are reusable history. A changed selection policy requires explicit new scope; do not reopen or reinterpret its acceptance silently |
| W119403 and W119405, `baton:work/records/2026/09/finding-v12-multi-job-deployment/findings/finding-multi-worker-pool/` and `findings/finding-per-job-binding/` | Both closed satisfying. W119403 accepted actual2+2 reservations, effective-principal alias capacity and exact replay; W119405 accepted per-Job serving/correction at its scoped boundaries. Children W130216/W130224/W130229 also closed. Reuse these proofs; they do not certify four Jobs in the requested combined setup |
| W106673, `baton:work/records/2026/09/finding-v12-live-session-workspace-detach/` | Closed satisfying, review-2026-09-07T20-20-41Z.md independently accepted restored provider session/workspace, useful code correction, confirmed old-process shutdown and replacement-process continuation. Earlier retained-session proof also accepted. Reuse these live receipts; no new model experiment is needed. The record explicitly excludes production manager adoption/restart recovery, so it does not discharge W103525 serving adoption |

No exact open priority/fallback/environment successor was found by those title
searches. W116987 session receiving-boundary inventory is a different open audit,
not healthy-session adoption. Do not repurpose it. If discussion selects a missing
product/configuration prerequisite, first create ONE bounded successor Work with
its dossier/owner and reference these closed predecessors. Until then it remains
an explicit proposal within W103525, not unrecorded implementation.

## Independently decidable chunks

Effort estimates are planning ranges in focused author/reviewer work sessions,
NOT subprocess budgets, permission or promises. Small means one bounded fixture
or audit session; medium means design plus a few focused implementation/review
sessions; large means several independently reviewed lifecycle slices. Existing
1200s/300s caps remain the only W103525 execution allowances.

| Chunk and recommendation | Benefit and bounded finish condition | Owner, dependency, effort/uncertainty | Consequence of defer/drop |
| --- | --- | --- | --- |
| A. Retain evidence and choose target contract — **NOW, discussion** | Accept the four-import result at its exact boundary; choose the rows below explicitly. Final record names selected requirements, deferred requirements and any explicit supersession | W103525, Slawomir decision via baton.decide; reviewer records it. Small/low; this report completes preparation | No decision means no next partial implementation handoff and no full certification |
| B. Managed integration capacity/custody — **NOW in W156162** | Candidate-executing preparation/reconciliation/verification follows actual managed attempts, bounded limits and positive stop; portable inputs/outputs; trusted target owner uses local capabilities. First finish is an independently approved capacity/portable-record design, then finite implementation slices | W156162 reviewer/implementer, owner for scope; M161127 gates first design. Large/high. Not charged to W103525; W103525 final managed integration evidence follows it | Essential isolation/recovery requirement remains unfulfilled. Existing host traces remain valuable historical evidence but cannot certify managed execution |
| C. Requested code correction and restart counters — **NOW after A; final terminal evidence after B** | In the selected scenario, owner requests correction, revised bytes complete independent review/import; declared reopen keeps durable identities. Count actual deterministic provider invocations and engine launches before/after; inject duplicate to show counters detect it; each terminal effect once. Reuse existing correction helpers and observer | W103525 implementer owns ONLY two new test files, reviewer independently checks. Medium/medium. First code-correction/provider-counter subcases can be scoped separately; one final combined run after B/configuration choice avoids repeating obsolete integration execution | Loss of defect coverage for revised attempts and duplicate provider execution. These are correctness gaps, not cosmetic export cleanup; full current contract remains open |
| D. Four Jobs over shared effective slots/repositories — **NOW one configuration feasibility decision; implement only if selected** | Name two actual implementation and two independent review principal capacities with valid per-Job Work/input/source bindings. Demonstrate admission/queuing without forged identities, then use this setup in three bounded schedules. If impossible at existing public configuration, return exact refused operands and a finite proposed source seam | W103525 bounded research; reuse W119403/W119405. Small feasibility/medium uncertainty. Any product successor is created only after owner selection, owned by impl with independent review; likely admission/composition boundary. Must coordinate scheduler path ownership with B | Four-worker setup remains valid component coverage; requested two-effective-slot combined certification remains open. No evidence currently justifies automatically changing product code |
| E. Healthy provider-session continuation — **DECIDE NOW; DEFER adoption unless context reuse is required now** | Choose whether continuity means same provider conversation across fresh attempt rows or a retained live runtime lifecycle; define healthy/unavailable boundary. Reuse W106673 proof. Finish selected adoption with actual serving protocol invocation/identity evidence and a useful corrected result; separate restoration from same-process retention | W103525 owner decision, then bounded successor if product adoption selected; reviewer design/impl change. Medium-to-large/high. Depends on D for fallback and B only where integration completion is claimed | Fresh isolated sessions may be an acceptable product choice but the current healthy-session requirement is NOT met. Deferral keeps certification open; dropping needs explicit acceptance amendment. No automatic live-provider rerun |
| F. Explicit-only fallback rule — **DROP stronger rule is recommended, subject to owner amendment** | Explicitly prefer healthy compatible affinity while allowing automatic eligible fallback and recording its cause, generation and fresh session. Keep no-duplicate and independence rules; separately select composed source rebinding if needed | W103525 decision referencing W71877. Small decision/medium adoption uncertainty. If stronger rule retained, create bounded scheduler-policy successor and resolve work-conservation tension before code | Dropping the stronger wording would align acceptance with accepted soft affinity, not weaken isolation. Without owner amendment the stronger requirement remains open. Source-ineligible replacement is still prohibited |
| G. Priority/creation ordering — **DEFER** | If selected later: precise priority schema/defaults and starvation/tie behavior, then admission/projection/reserve changes plus inversion/replay tests. One bounded successor Work, not fixture-only assertions | Owner selects; reviewer design then impl. Medium/high; no exact open matching Work found. Preserve existing deterministic ordering until chosen | No priority-service or chronology guarantee. Basic eligibility/causal safety evidence survives, but full current W103525 priority acceptance cannot close without implementation or explicit narrowing |
| H. Conformant final environment — **NOW provision planning, verification LAST** | Operator supplies exact usable interpreter/image matching the lock, including jsonschema4.26.0; no hidden install. Run selected final focused suite and one coherent export after affected bytes stabilize, then independent review | Operator baton.ops (Slawomir); W103525 holds request/acceptance, separate configuration Work only if setup is needed and selected. Small/low-to-medium depending availability. After B–G selected scope | All current evidence remains accurately exploratory; no conformant certification claim |
| I. Random interleavings, TUI, repeated live experiments — **DEFER random/TUI; DROP automatic live repetitions** | Keep stable artifact schema and explicit partial orders now; later consumers can add rendering/random coverage in their own scope. Reuse applicable live evidence | Owner scheduling; no new Work until selected. Medium/open for enhancements | No loss of currently proven safety boundaries; broader stress/usability claims remain unmade. Mandatory live sequence was already superseded by deterministic-provider policy |

“NOW” recommends an order for discussion; it does not authorize another managed
implementation turn before the owner selects the report's chunks.

## Finite sequence and W156162 revalidation

1. Return this report to baton.decide. Record chosen chunks and any precise
   acceptance amendment chronologically in FINDING and current PLAN. Do not infer
   acceptance deletion from “defer” or from an absent session list.
2. Resolve W156162's independent design findings in its own Work. In parallel
   planning, choose the session/fallback/priority contract and the shared-slot
   configuration. Avoid simultaneous product-file edits; scheduler.py and
   stage_execution.py need explicitly serialized ownership if both scopes touch
   them. This is dependency planning, not authority to spawn extra agents.
3. Create only selected missing prerequisite Work, with exact paths, owner,
   acceptance, verification spending and independent review before implementation.
   No new raw SQL, forged claims, synthetic owner receipts, extra effective
   capacity or host-path transport shortcut can make the fixture pass.
4. Implement selected test-only correction/counter/configuration cases once their
   public seams are available. Stop after the bounded finish conditions, inspect
   failures before repeating, and reuse passing component evidence.
5. Run the selected three100-tick schedules in the conformant environment only
   after the managed integration and chosen product semantics stabilize. Audit
   one coherent export plus relevant negative validator cases; independent
   reviewer binds exact candidate/source/env hashes and each acceptance row.
   If a selected required row remains absent, preserve partial evidence and
   return its exact remaining scope; do not relabel it passed.

**Reuse unchanged:** causal partial-order definitions, source/Work/role admission
refusals, negative oracle cases, correction-verdict identity bindings, and the
historical one-direct/three-derived authorization and test-content observations.
They still explain expected behavior after relocation.

**Must revalidate after W156162:** every derived integration preparation and
verification execution location; parent/child or replacement attempt capacity;
positive stop before release/import; collected phase custody; exact
base/isolated/combined command, harness digest and completed-prefix/not-run suffix;
independent judgments over portable candidate content; trusted target-owner
lease/fence/old-revision publication; restart without duplicate phase launch,
provider call or import. An unchanged final receipt count cannot prove these new
lifecycle boundaries. M161127 confirms no scheduler relation currently charges a
child to its parent; an unallocated child would hide capacity. That gate is real.

**Remote boundary:** ordinary existing input/output envelopes are the required
transport. Deterministic disjoint-root placement replay can prove relocation
without inventing an RPC or running a farm. Coordinator-local paths/inodes are
not portable custody. Actual remote deployment and actual engine/provider claims
are separate questions, not automatic W103525 prerequisites beyond the chosen
architecture/acceptance. Do not fabricate either from a simulated trace.

## Budget and handoff boundary

Author ledger remains289 runs, **1063.5077970099796/1200s**, remaining
**136.4922029900204s**. Historical **0.8047997559610849s** overrun against the
old780s cap remains charged and unwaived. Reviewer prior130.96222113902036s plus
fresh two-order probe10.87323230200127s and artifact audit0.03151493900077185s
equals **141.8669683800224/300s**, remaining **158.1330316199776s**.
Initial research baseline0.2879257239692379s remains separate. Both new subprocess
entries in `review-161114.json` persist fresh starting cap/spent/remainder,
expected cost, margin and timeout before execution. No allowance reset/transfer.

No product or test bytes, author PROGRESS, Git state, installed dependencies or
live runtimes were changed in consolidation. New artifacts and reviewer-owned
records only. A guessed read of `src/baton_v12/job_manager/boundaries.py` failed
ENOENT; `rg --files` located `worker_manager/boundaries.py`. This was reviewer
path misuse, not a Baton defect or missing required policy. No store was opened
directly. Return the completed report for owner discussion, not partial author
implementation or a generic budget extension.
