# Adoption assessment — W247941 / claim249338

**NOT READY for the explicit current-deployment adoption decision.** Implementation, independent review and historical parallel feasibility are accepted. The missing deliverable is a concrete current two-Job deployment/evidence bridge with bounded operator lifecycle commands. This is a configuration and proof-package gap, not a demonstrated concurrency defect or a request for general recertification.

## Selected scope and evidence

Canonical prerequisite W239533 is closed satisfying at pickup snapshot249337. Work event247968 selects assessment only: no live execution, deployment change or broad refactor. Thread247941 and W2's current adoption checkpoint require fresh-context independent parallel development; reuse is an early Job, not this gate. Human plus agent integrates results; v11 remains the coordination authority.

| Requirement | Accepted evidence reused | Limit for this decision |
| --- | --- | --- |
| Useful implementation, retained proposal and cleanup | ../finding-v12-single-implementation-proof/review-2026-09-23T04-15-56Z.md, live-success-244216 | One bounded implementation; no overlap implied. Preserve reported default3600 vs selected180 metadata observation. |
| Independent attributed review | ../finding-v12-independent-review-proof/review-2026-09-23T15-00-25Z.md, review-attribution-248639.json and live-review-248377/MANIFEST.json; canonical W239533 closed | One separate review; exact checkpoint/base/head/tree and populated producer/reviewer identities checked. One success, not a rate or live disagreement proof. |
| Overlap, separate producer/reviewer lines, per-Job binding and correction isolation | ../finding-v12-multi-job-deployment/findings/finding-per-job-binding/findings/finding-two-job-serving/review-2026-09-11T00-52-04Z.md | Controlled engine/provider fixture, real owner/content operations. Accepted component proof, not current installed deployment certification. |
| Historical live A/B execution and both reviewed outputs | ../finding-v12-standalone-multi-job-pipeline/FINDING.md, 2026-09-12T15:43:55Z; findings/finding-two-job-pipeline-proof/evidence/live-success-nup4nltc | Owner-observed six-stage completion, frozen judgments and final tests. All seven retained hashes independently match. Broader managed-integration path and older configuration; do not relabel as the current four-attempt human-integration deployment. |
| Fresh recovery, safe holds, limits and monitor | ../../08/finding-v12-isolated-agent-workers/review-2026-09-16T04-14-53Z.md and its exact evidence map | Accepted minimum fresh-attempt scope. Not proof of every later deployment binding. |

No historical proof is withdrawn. Two serial current runs are not a substitute for overlapping execution. Conversely, a new model run is not needed merely because the historical concurrency evidence is older: first establish its relevant continuity and exercise missing wiring deterministically.

## Concrete proposed baseline, not yet an adopted deployment

Reuse the accepted review manager snapshot `/home/sl/baton-runs/independent-review-247947/manager-source`: all106 file hashes still match the executed packet manifest. Runtime candidate `/home/sl/baton-runs/managed-correction-236087/build/stack/out/distro`, recorded build1e576ff2186db69e8b44da9d38874ff7e99ebbe3, executable SHA25604aa459aed61704971e98b9260929b19953c41caad906e28551aae0ba457a58a. These are retained packet bindings, not a fresh runtime execution claim.

Reuse image candidate `baton-v12-claude-worker:w239528-244216`, digest sha256:c862c055c6430addc918ca078a9e4d55f6bd8173ed9c9878a8ad9d6cad334ca2 and accepted adapter18c34ff52faa150237df0c8d0206b805801ee71cb9e7a4ec6e84e4379d7f9d8d. Source snapshot includes accepted stage_execution.py6a212c3a2edc5ddb7059e86350d95924aca4b059c059855939e4fd9771ab5801. No image rebuild or mutable-tag-only substitution is proposed.

Proposed initial limit: exactly two independent Jobs, disjoint source/path ownership, two implementation allocations capable of overlapping, distinct reviewer identities from each producer, fresh isolated provider contexts, no session restoration, no automatic corrections/retries, no managed integration. Reviewers may execute sequentially if both verdicts are collected. Preserve immutable source/proposal/results and positive cleanup for all admitted attempts. Do not reuse consumed244216/248377 stores or resubmit their accepted subjects.

## Concrete blockers and smallest next action

**G1 — deployment not bound.** The owning dossier supplies no resolved current two-Job deployment document, participant/capability/handler mapping, worker allocations, private roots, credential references, Job documents or complete start/inspection/stop recipe. The recent supervisors deliberately cap one workload, and W239533 admits only review. Running either twice does not itself establish one supported concurrent arrangement.

Next: prepare a fresh, create-only two-Job package using the proposed accepted artifacts, preserving all old roots. Specify one explicit arrangement (shared manager with per-Job ports/allocations, or separately isolated managers) rather than treating the alternatives as equivalent. Prefer the existing supported multi-worker composition if it fits; no new scheduler or shared capacity design. Resolve Authority/principal/capability/role and worker independence, two distinct writable workspaces, output/log/private-context/scratch roots, credential-reference mapping, immutable source base, exact path ownership, admission caps and deadlines. Hash every artifact and document the selected arrangement's actual overlap capacity.

**G2 — continuity and lifecycle evidence not joined to G1.** The older parallel proof and new serial proofs do not bind that as-yet-unwritten package. No new product defect is inferred from this missing bridge.

Next: compare the relevant older accepted concurrency seams against the selected snapshot (per-Job port/worker/task dispatch, allocation, workspace and result binding, review ending, cleanup). Reuse unchanged or independently accepted successor behavior. For any remaining configuration-specific gap, use a single deterministic two-Job witness through the selected composition with provider simulation at its normal boundary. Require an observed interval in which A and B are both actively executing, distinct runtime/workspace/attempt attribution, both frozen independently attributed review results, and positive stop/cleanup. Inspect concrete identities/timestamps or a controlled overlap barrier, never infer overlap from two submits or test counts. Preserve a faithful transcript and final supported-reader projections.

Use two tiny disjoint source changes and per-Job verification commands, fixed four admissions (two implementation plus two review), no integration and no automatic correction/retry. Proposed preparation timeout ceiling600s inclusive of60s cleanup reserve, per-attempt180s, subject to the generated deterministic witness's actual sensible limits. These are a proposed bounded witness, not an inherited live-run grant. If matching accepted evidence already closes all of G2 after G1 is bound, record the equivalence and omit redundant execution.

A real-engine/provider run requires a separately stated unanswered question and explicit selection. Current provider authentication/judgment is already evidenced by W239528/W239533; do not add live calls merely to obtain another success. If host concurrent mounts/capacity need direct proof beyond accepted evidence, return exactly that proposed engine-only or live question with the executable packet, not a broad campaign.

## Operator recipe requirements

The current verified CLI surfaces are `tools.job_manager ... submit --document`, `serve --control ... --operations tools.stage_execution:factory`, and read-only `status --control ...`; staged composition selects configuration through BATON_V12_STAGE_EXECUTION_CONFIG. Source: v12/python/DEPLOYMENT.md and tools/stage_execution.py CONFIG_ENV/factory. These surface names are not an executable deployment recipe until G1 resolves all operands and binds the source/interpreter.

The next packet must supply literal resolved commands for: create-only preparation and nonmutating pin/precondition check; start with the bound source/interpreter, selected configuration and fresh incarnation; submit each distinct Job exactly once; read-only status for both Jobs plus immutable verdict/manifest readback; bounded stop that closes admission, cancels exact admitted attempts through supported owners, verifies positive cleanup, and publishes a final outcome. A process exit or SIGTERM alone is not proof that worker runtimes stopped. Reuse accepted supervisor termination machinery and validate its two-Job accounting; do not present the single-review supervisor's one-admission command as a parallel runner.

No safe resolved start/stop command exists in this dossier today. That absence is G1, not a reason to publish guessed paths, run the generic unbounded serve loop, or modify the deployment. Existing consumed-run inspection is sufficient evidence and is not an instruction to restart it.

## Handoff and exclusions

Routine bounded preparation goes directly to baton.impl under delivery-continuity policy: pin the exact dossier paths before edits, prepare G1/G2 and the operator recipe, return for independent review. No source refactor, new live call, deployment mutation, prior-root cleanup, copied backlog or Git mutation. Any necessary narrowly demonstrated product gap must be recorded before implementation; do not preemptively add one.

Reviewer owns ASSESSMENT-249338.md and ASSESSMENT-EVIDENCE-249338.json; subsequent corrections append a new review/evidence record rather than overwriting these. Other dossier preparation paths may be owned by the next claimant. PROGRESS.md was absent on pickup: operational observation only, consistent with an assessment-only dossier; no implementer progress was silently fabricated. New measured test/provider/engine execution0s; static review elapsed not measured. Preserve all historical durations and unknowns.
