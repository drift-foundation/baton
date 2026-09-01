# Plan

**Status — current Baton Work `W28` (`43c55d4b-W28`); roadmap with one
signed-off proof now resident under `v12/`. The original `bec445ce-W193`,
`bcbb9dbf-W2`, `5f717eee-W2`, and `88990a87-W2` authorities are retired. W76's
bounded PoC and W126's in-repository relocation are independently complete.
The protocol-owned assignment state machine and durable identity placement are
independently signed off. The next design gate is the versioned worker-control
API and its typed input, proposal, result, and verification manifests; no
production implementation is authorized yet.**

0. [done 2026-08-20] Claude independently reviewed the complete pinned design
   for contradictions, missing invariants, feasibility, and ordering risks,
   made no implementation changes, and returned W2 to `baton.feat`. Ten
   findings in `review-2026-08-20T11-37-13Z.md`; no blocking objection to the
   direction. The v11-enforcement scope, assignment-generation primitive,
   read-only authority mediation, proposal approval stage, and v12 Git-policy
   boundary are now resolved. No design-review contradiction remains. The
   bounded end-to-end spike between items 1 and 2 is approved; its deliverable
   is observed evidence and corrections to items 1-4, not production code.

0a. [done 2026-08-20] Pin the authority-mediation boundary exposed during the
   review: sandboxed agents send structured intents; the trusted Worker Manager
   alone accesses Baton authority, commits the explicit atomic claim, and only
   then unlocks execution and publication capability.

0b. [done 2026-08-20] Clarify the accepted v11 boundary: Baton enforces claim
   before authoritative pass or close, but cannot prevent pre-claim edits or
   tests in its shared writable checkout. Defer that filesystem enforcement to
   v12 rather than creating throw-away v11 work.

0c. [done 2026-08-20] Define the assignment-generation fencing identity. The
   successful atomic claim alone generates the monotonically increasing
   per-Work ID; every later claim gets a new ID, and release, pass, close, or
   revocation invalidates it. Keep delivery episodes, runtime incarnations,
   configuration generations, runtime attempts, and proposals distinct.

0d. [done 2026-08-20] Define four separate candidate gates: clean verification,
   technical `rview`, explicit `approv`, and mechanical integration. Bind review
   and approval to the exact immutable proposal, verified candidate tree, and
   target revision; revisions restart the gates and target movement refuses
   integration rather than silently changing the candidate.

0e. [done 2026-08-20] Scope the Git-mutation exception to a claimed,
   Worker-Manager-certified disposable proposal clone at the v12 cutover.
   Canonical, integration, verifier, reviewer, and ordinary host workspaces stay
   immutable to agents; publication and canonical integration remain trusted
   manager operations. Keep the blanket current rule until enforcement exists.
   Scope clarified by 0af: activation is per isolated participant/profile, not
   one global cutover.

0f. [done 2026-08-20] Make committed findings and plans immutable assignment
   inputs. A worker owns only its record's `PROGRESS.md` and Work-scoped
   evidence, may autonomously return a typed `plan-rejected` disposition, and
   never edits a parent plan. Plan revision is separate Work and any retry gets
   a new claim generation; concurrent access to one plan or dossier stops as a
   protocol violation rather than becoming an automatic merge.

0g. [done 2026-08-20] Permit automatic refresh/rebase only when replay is
   conflict-free. Any content conflict stops with evidence and requires a new
   assignment from the accepted target; resolving a conflict is separately
   planned Work, never worker or integrator discretion.

0h. [done 2026-08-20] Make credential and quiescence conformance claims
   testable. Prove non-persistence and scan known retained surfaces, fail
   publication on detected leakage, and bound residual risk with scope,
   lifetime, revocation, and network policy. Require generation fencing and
   isolation; seek positive quiescence but permit an explicit uncertain path
   only when stale access and publication remain impossible.

0i. [done 2026-08-20] Keep configured routing stable while the Worker Manager
   tracks `certified`, `probation`, or `disabled` eligibility for each exact
   runtime-profile digest. Exclude unhealthy profiles from automatic offers,
   require explicit recertification, and expose `no-certified-runtime` when an
   endpoint has no executable profile rather than rerouting or claiming it.

0j. [done 2026-08-20] Make the Worker Manager's monotonic/UTC clock
   authoritative for detecting deadline expiry while leaving consequences to
   the assignment's pinned route policy. Default expiry is reported and
   preserves work; every automatic action names its policy clause, fences the
   exact generation, journals the result, and avoids silent destruction.

0k. [done 2026-08-20] K independently re-reviewed the complete design after
   the ten rulings were pinned, made no product, prototype, dependency or
   schema change, and returned W2 to `baton.feat`. All ten first-review
   findings are resolved. Seven new findings in
   `review-2026-08-20T16-00-50Z.md`; no blocking objection. Two should be
   settled before ordering because they come from authority facts newer than
   the rulings: one-slot claim capacity now bounds how many live assignment
   generations one participant may hold, and W2938's participant pickup
   obligation overlaps the manager's claim-acceptance deadline on a second
   authoritative clock. Three smaller open rulings: plan-rejection can loop
   without a schedulability gate, leaf `PLAN.md` status marks are unowned under
   plan immutability, and an isolated worker has no way to file a discovery.
   The spike's scenario list needs plan rejection, a real conflict stop and one
   claim-deadline policy clause added, and a statement of which open decisions
   it is NOT expected to close.

0l. [done 2026-08-20] Retain the authority's one-live-claim capacity: one
   participant has at most one assignment generation and worker. Parallelism
   and failover use distinct configured participant identities, even when they
   share an underlying provider, model, adapter, or role.

0m. [done 2026-08-20] Represent competitive fan-out as one coordinating parent
   plus one child Work per attempt. Selection identifies the exact winning
   child Work, assignment generation and proposal; every losing attempt keeps
   an explicit disposition and attributable history.

0n. [superseded 2026-08-27 by item 25] Make a short-lived, single-use, manager-issued claim
   token the only pre-claim handoff deadline. Bind it to authority, Work,
   participant, runtime attempt and expiry; require the inside agent to return
   it with its claim intent. Expiry fails closed without a Handler or assignment
   generation and leaves the canonical participant pickup obligation open.

0o. [done 2026-08-20] Make `plan-rejected` end the claim and atomically add a
   typed `plan-revision` scheduler gate. Reoffer is forbidden until the plan
   owner publishes an accepted immutable revision and explicitly satisfies the
   gate; the subsequent implementation claim creates a fresh assignment
   generation.

0p. [done 2026-08-20] Keep `PLAN.md` immutable and free of mutable execution
   status. Record generation-attributed step status, evidence, blockers,
   retries and handoffs in the separate `PROGRESS.md` journal; derive current
   views from that journal and canonical Baton events.

0q. [done 2026-08-20] Accept generation-bound structured worker activity
   updates as canonical Baton Events so the UI can show current plan step,
   action, evidence, retry, blocker and handoff preparation. Keep activity
   distinct from claims, heartbeats, permissions and lifecycle transitions;
   retain `PROGRESS.md` as the durable worker-owned execution journal.

0r. [superseded 2026-08-20 by 0y] Add manager-mediated, idempotent
   `file-discovery` for an
   isolated worker to create accountable child Work and return its Work ID.
   Gate the new Work on trusted permanent-record materialization, grant no
   claim by filing, and block the current assignment only when the worker
   explicitly reports the discovery as a blocker.

0s. [done 2026-08-20] Keep compact labels such as `W2@g3` presentation-only.
   Persist and mutate only through full structured authority, Work,
   participant and assignment-generation identity; resolve any human shorthand
   before committing an operation.

0t. [done 2026-08-20] Expand the bounded spike to cover expired-token
   reassignment, plan-rejection gating, a real conflict stop, four distinct
   verification/review/approval/integration actors, competitive fan-out and
   stale-generation fencing. After the local OCI skeleton, repeat the essential
   lifecycle through an SSH or equivalent adapter to a genuinely non-local
   worker before schemas freeze. Expire one post-claim cancellation-grace
   deadline to exercise its pinned policy clause/digest and generation CAS.
   Explicitly exclude production credential, retention, cache, signing and
   proposal-store decisions from spike claims.

0u. [done 2026-08-20] Claude performed the final review-only consistency pass
   over the complete current record and both append-only reviews, made no
   product, prototype, dependency or schema change, and returned W2 to
   `baton.feat`. All seven second-review findings are resolved and the
   remote-adapter requirement is pinned consistently across the finding, the
   spike and 0v/6. Not a clean return: six residual items in
   `review-2026-08-20T16-31-16Z.md`, none blocking. Settle first that the
   conformance invariant list does not require the remote-specific properties
   the remote ruling makes mandatory, and that no post-claim deadline scenario
   exercises the pinned policy digest before manifests freeze. Four are text
   corrections: the unqualified parallel-child-Work sentence, the missing
   `AGENTS.md` transition clause for plan-status immutability,
   child-versus-independent `file-discovery`, and the conflated pre/post-claim
   expiry sentence.

0v. [done 2026-08-20] Keep remote execution behind runtime adapters. An SSH
   adapter may trigger and communicate with a remote worker, but SSH and remote
   host mechanics never enter Baton protocol vocabulary. Preserve manager-held
   authority, token/generation fencing, digest-bound inputs and proposals, and
   uncertain-quiescence handling across transport loss. Test a genuinely
   non-local adapter during the bounded spike, after the local OCI skeleton and
   before worker-control or manifest schemas freeze.

0w. [done 2026-08-20] Give every successfully claimed worker a
   generation-scoped writable record-output area for progress, research,
   reproductions, evidence and draft discovery dossiers. Keep it separate from
   immutable contract inputs, the private source clone and canonical records;
   let only the trusted manager validate, collect and materialize its contents.

0x. [done 2026-08-20] Treat the source proposal and validated record-output set
   as one immutable reviewed candidate. Bind verification and approval to both
   digests, then atomically integrate source plus canonical dossier artifacts;
   any later output change creates a new proposal revision and repeats the
   gates.

0y. [done 2026-08-20] Supersede automatic worker-side Baton filing. Give each
   assignment a private writable output mount backed by adapter-managed storage;
   the worker only writes drafts/assets and emits path notifications. A trusted
   intake agent later rejects, edits, merges, splits or materializes accepted
   discoveries as child or independent Work with source-assignment provenance.

0z. [done 2026-08-20] Claude performed the narrow review-only closure pass
   against `review-2026-08-20T16-31-16Z.md`, including the superseding
   mounted-output/intake model, and made no implementation or product change.
   All six residuals are resolved and the supersessions leave no competing live
   rule: the superseded discovery and output text is retained, marked, dated
   and pointed at its replacement, and 0r is marked superseded by 0y. One
   decision-ready residual in `review-2026-08-20T16-53-53Z.md`: the explicit
   "a discovery is not lost when its parent proposal is rejected" guarantee
   disappeared with the mechanism it depended on, and drafts from a cancelled
   assignment or rejected proposal have no stated path to trusted intake.

0aa. [done 2026-08-20] Preserve discovery drafts across cancellation, forced
   stop, plan rejection, and proposal rejection. Route sealed/quarantined
   output to trusted intake with the source assignment and disposition as
   provenance; intake must deliberately accept, transform, or reject each
   draft without implying acceptance of the source proposal.

0ab. [done 2026-08-20] Claude performed the final yes/no closure check and made
   no implementation or product change. Clean: the sole residual from
   `review-2026-08-20T16-53-53Z.md` is resolved by 0aa across all four terminal
   paths, the inspection clause keeps preservation from becoming a fencing
   hole, and no competing live rule remains. Recorded in
   `review-2026-08-20T16-58-40Z.md`.

0ac. [done 2026-08-20] Replace the assumption that every assignment is Git
   Work with typed source descriptors. Keep acquisition in the trusted worker
   bootstrap, make URI scheme transport-only, and initially define `git` and
   digest-bound read-only `directory` sources. Git carries repository identity,
   source/integration refs and an immutable base revision; directory Work gets
   an immutable file collection plus a separate writable output role and no
   synthetic repository. Never persist credentials in source URIs.

0ad. [done 2026-08-20] Define the matching named output contract. Separate the
   human result/acceptance specification from machine-readable IN/OUT roles;
   give the worker only stable local paths, never external delivery authority.
   The trusted manager freezes, validates, hashes and collects declared Git,
   directory and record outputs for the exact assignment generation. Missing
   or invalid required results fail the result, later changes create a new
   revision, and only trusted tooling may deliver or integrate accepted output.

0ae. [done 2026-08-20; repository placement superseded by 0ai, reuse
   restriction superseded by 0ag] Isolate the first
   Claude ACP proof of concept from the existing Baton product. Keep its source,
   dependencies, tests, fixtures,
   manifests, image and runtime state in a disposable external root; consume
   only the immutable deployed CLI/JSON boundary and standard ACP. Modify no
   v11 application, bridge, lifecycle, test or deployment source, import no
   private internals, and open no authority database. Retain only W2/child
   records, traces and conclusions; successful adoption still requires new
   reviewed implementation Work.

0af. [done 2026-08-20] Make v11 and v12 execution coexist during gradual
   rollout. Migrate one configured participant/runtime profile at a time; never
   run legacy readiness and Worker Manager consumption for the same identity.
   Route each concrete offer to one participant/mode, grant v12 capabilities
   only to certified isolated claims, and retain legacy policy elsewhere.
   Roll back by fencing the isolated profile and routing later Work to an
   eligible legacy participant, without replacing the authority or undoing
   unrelated v11 Work.

0ag. [done 2026-08-20] Permit unlimited v11 reuse inside the disposable PoC
   root while preserving the no-modification boundary around existing Baton.
   Snapshot or copy useful source, bridges, CLI/JSON code, tests and fixtures
   with provenance to `8835cd5`; never import through, symlink to, or write back
   to the live checkout. Start with JSON and CLI natural dispatch and defer all
   TUI work.

0ah. [done 2026-08-21; retired-authority child Work `W76`] Prove natural dispatch to one Claude ACP
   worker under
   `findings/finding-v12-claude-acp-dispatch-poc/`. Start only from the committed
   clean handoff, keep all prototype source in the separate disposable root,
   and return traces plus a go/revise/no-go conclusion before production design
   or implementation expands.

0ai. [done 2026-08-21; child Work `W126`] After W76's external implementation
   passes independent review, relocate its source-controlled prototype into
   this repository's self-contained top-level `v12/` subtree. Include its own
   `justfile`, package/dependency manifests and lockfiles, source, tests,
   scripts, fixtures, configuration and container definitions so it builds and
   tests without root v11 recipes. Add no root-recipe delegation, packaging,
   deployment or release integration while it is experimental. Preserve the
   no-v11-edit boundary and provenance; exclude generated dependencies, images,
   secrets, authorities, logs and runtime state. Do not delete the external
   root before the in-repository gates pass; once they do, remove
   `/home/sl/src/baton-v12-poc` as the final approved migration step so only
   one canonical prototype tree remains. W126 closed satisfying after five
   review rounds, external-root removal, the 78/78 gate, and standalone proof.
   Child `W1395` records the post-reboot placement-test fixture defect. Its
   test-only isolation correction is independently accepted; the in-repository
   gate is 78/78 again, and now holds whether the sample root is absent,
   existing-unmarked or existing-owned. Cancelled child `W1466` records the
   discovery of pre-existing temporary-fixture leakage; independently
   scheduled top-level W1478 now owns that non-blocking cleanup and does not
   reopen W1395 or gate W2.

0aj. [done 2026-08-21; current Work `W28`] Revalidate the accepted in-repository
   PoC against the pending roadmap before ordering production work. Confirmed
   78/78 focused tests and recorded that the PoC's constant generation,
   authority-local selectors and process-memory offer/token state are bounded
   spike choices, not production contracts. Pin the next design gate and the
   unresolved authoritative placement in `FINDING.md` and
   `review-2026-08-21T15-29-46Z.md` without changing application code.

0ak. [done 2026-08-21] Keep W28 as the durable v12 campaign umbrella rather
   than executing the remaining roadmap as one oversized Work. Every
   independently schedulable milestone and bounded slice gets its own Work.
   W28 owns ordering, cross-slice rulings and the campaign index; it is not
   claimed to perform a child's execution. Use an explicit dependency only
   when a concrete W28 decision truly cannot proceed before another Work,
   never merely because that Work is contained here.

0al. [done 2026-08-22; child Work `W4511`] Pin affinity review and independent
   opinion as distinct future v12 scheduler intents. Affinity preserves the
   same reviewer across implementation→review→implementation revision cycles
   with fallback when unavailable; independent opinion selects a different
   participant and may also require a different provider or model. Keep the
   canonical dossier authoritative and treat model context only as an
   efficiency advantage. Make no v11 reviewer-pool or scheduler change.

0am. [done 2026-08-22] Make Offered→Claimed the two-phase v12 operator model.
   Offered shows which participant/runtime attempt received the Work and starts
   the visible claim-acceptance countdown while Work remains queued and Handler
   remains empty. Claimed stops that timer, makes Work active, fills Handler,
   and mints the assignment generation. Failed, refused, and expired are typed
   Offered outcomes, not extra phases.

0an. [done 2026-08-22] Make every v12 runtime failure actionable without
   depending on a final agent message. Show a concise typed cause with `fail`
   and provide a direct Work-detail path to the exact attempt's durable,
   redacted diagnostics or log locator. The Worker Manager or adapter publishes
   this evidence even when the agent turn is interrupted or quarantined.

## Campaign milestones

- **M0 — Foundation (done):** bounded PoC, in-repository relocation, and the
  signed-off assignment state machine (items 0ah-1).
- **M1 — Contract freeze (awaiting approval as W1408):** worker-control API,
  typed manifests, ACP boundary, and runtime-neutral conformance contract
  (items 2-4) are independently signed off and cross-contract reconciled.
- **M2 — Local execution (conditionally approved as W1425):** OCI reference
  worker, trusted Worker Manager, and one complete local isolated lifecycle
  (items 5-6, local portion). W1425 waits explicitly on W1408; M1 closure
  surfaces M2 for bounded decomposition without authorizing later milestones.
- **M3 — Proposal pipeline (conditionally approved as W1427):** refresh,
  immutable proposal, clean verification, technical review, approval, and
  trusted integration (items 7-9). W1427 waits on W1425.
- **M4 — Runtime certification (conditionally approved as W1429):** certify
  Claude, Gemini, and Codex against the same local worker contract while
  retaining only a contract placeholder for a future remote adapter (item 10).
  W1429 waits on W1425 and does not wait on M3.
- **M5 — Resilience and scale (conditionally approved as W1431):** failure/race
  recovery plus concurrent multi-agent isolation trials (items 11-12). W1431
  waits on both W1427 and W1429.
- **M6 — Rollout and adoption (conditionally approved as W1433):** mixed
  v11/v12 operation, observability, documentation, identity separation, and
  the production-adoption decision (items 13-14). W1433 waits on W1431; v11
  retirement additionally requires a usable v12 TUI and a separate ruling.

Each milestone becomes a direct child Work of W28 when scheduled. Its bounded
implementation and verification slices become children of that milestone,
preserving the two-child-level limit. As superseded on 2026-08-21, M2-M6 are
conditionally scheduled behind explicit dependency gates; only milestones
whose prerequisites have closed are actionable.

1. [done 2026-08-21; child Work `W151`] Model assignment generations, read-only pre-claim inspection,
   expiring single-use claim tokens, claim-capability-gated writable
   workers, cancellation, quiescence, stale-worker rejection, runtime-profile
   probation/disablement, typed plan rejection and revision, and integration
   dispositions as one protocol state machine. The approver rules that the
   monotonically increasing integer generation is minted and persisted by the
   v12 authority's atomic claim transaction; the random single-use pre-claim
   token remains a separate secret capability. The design deliverable must include a transition
   table, invariants, restart/reconciliation behavior, full durable identity
   shapes, and executable model tests. Five independent review rounds resolved
   the restart and retirement races; the final 54/54 model gate passed and the
   executable design contract was signed off without changing application,
   protocol, runtime, schema, or dependency code.
2. [done 2026-08-22; child W1439 closed satisfying] Specify the outer versioned Baton worker-control API plus typed
   input, immutable local change-proposal or non-Git result, and verifier-result
   manifests. Include named source descriptors, source type/URI/destination,
   Git base/target/proposal identities or directory content/output digests,
   role/policy/toolchain/image digests, tests, logs, and dossier evidence.
3. [done 2026-08-22; child W1440 closed satisfying] Specify ACP as the normalized inner agent endpoint without adding
   repository or container lifecycle to ACP: use a mediated ACP relay for
   native ACP agents and a narrow ACP adapter for non-ACP runtimes such as
   Codex App Server.
4. [done 2026-08-22; child W1441 closed satisfying] Specify the runtime-neutral worker conformance suite covering
   typed-source materialization and digest verification, read-only input,
   declared-output containment, freeze/validation/collection, workspace and Git
   isolation, generation-gated publication, cancellation and
   quiescence, pre-claim execution denial, claim-timeout reporting and explicit
   route-policy consequences, runtime-profile reliability policy, credential
   non-retention, explicit policy, untrusted outputs, normalized lifecycle,
   transport-partition fencing, proof-bound remote reattachment, and
   negative/race/crash/recovery behavior.
4a. [pending] Revise the completed worker-control and conformance contracts
   for the 2026-08-25 artifact-neutral-manager supersession. The core manager
   exposes only read-only `/input/input.json` and writable-then-frozen
   `/output/output.json`, freezes and digests output generically, and never
   interprets its format. Private ephemeral storage is runtime capacity rather
   than protocol vocabulary. Workers and downstream consumers interpret the
   manifests' opaque consumption/result descriptions. Preserve the earlier
   Git/directory source and result types as explicitly superseded history and
   cover persistent-output workspaces, ephemeral-workspace export, publication
   of `output.json` last, unresolved identifier-only output, and frozen
   output-to-read-only-input chaining.
5. [pending] Build one OCI reference worker, runnable by Docker or Podman, that
   receives the standardized read-only input directory and persistent writable
   output directory, reads `input.json`, and publishes `output.json` last. It
   may use private ephemeral storage or work directly below output, without
   teaching the manager the input or result format. Permit broad,
   non-interactive command freedom inside the
   assignment's private writable surfaces, including destructive commands,
   without granting host privilege or per-command approval. Preserve
   defense-in-depth sandboxing, prohibit privileged containers, host
   namespaces, host devices and nested container runtimes, never expose the
   host container-runtime socket, drop unnecessary capabilities, and require
   the worker to pass the runtime conformance suite.
6. [pending] Build the trusted host-side Worker Manager and OCI runtime adapter
   behind the worker-control API. Normalize start/cancel/inspect/collect/
   destroy, mount the standardized input/output surfaces, validate only the
   generic JSON envelopes, persist attempt-to-runtime reconciliation
   identities, freeze and digest output without format-specific
   interpretation, and prove
   cancellation fencing and quiescence before replacement; keep engine CLI or
   API mechanics deployment-specific. After the local reference path, certify
   a remote runtime adapter such as SSH against the same contract without
   exposing authority or canonical write access remotely.
7. [pending] Implement the pre-submission refresh/rebase/test rule and publish
   immutable, forge-independent local change proposals. Treat every revision
   as a new proposal rather than rewriting a submitted one.
8. [pending] Build a clean verifier that imports a proposal into a fresh clone,
   constructs the candidate merge against the current target, runs the gates,
   and binds evidence to the exact candidate tree. Invalidate or reverify when
   the target moves.
9. [pending] Build read-only technical review, explicit proposal approval, and
   the trusted integrator path as distinct stages. Keep canonical write
   authority out of workers, verifiers, and reviewers; import only objects
   approved for the exact verified target and update it atomically without
   resolving conflicts or editing code.
10. [pending] Certify Claude and Gemini through ACP relays and Codex through an
   ACP-to-App-Server adapter against the same local worker contract. Preserve a
   typed remote-runtime extension point, but defer implementation and
   certification of SSH or another remote adapter to separately approved Work.
11. [pending] Exercise crash, provider overload, cancellation race, late
   recovery, duplicate assignment, stale candidate, conflicting candidates,
   rejected review, mid-turn contract supersession (the W2938 incident),
   revision, and manual-salvage workflows. Prove that forced cancellation can
   discard only the superseded attempt's private writes without touching the
   canonical checkout or another worker.
12. [pending] Run a multi-agent trial with concurrent independent Work and
   verify that no worker can alter another worker or the canonical checkout.
13. [pending] Define gradual per-participant/profile rollout and rollback,
    mixed legacy/isolated deployment, local proposal storage, operating
    documentation, retention, and observability—including distinct visible
    Offered and Claimed stages—before considering broader v12
    production adoption. Removal of the legacy path is a later explicit gate
    and cannot occur before v12 provides a practically usable TUI.
14. [deferred] Separate the one human-attached interactive copilot from managed
    background workers so every participant identity has exactly one live
    execution context. Treat conversation threads as non-authoritative session
    detail, use distinct participants or attempts for parallel execution, and
    make participant runtime state unambiguous. This is not part of the current
    single-Claude PoC and does not receive a child Work until later ordering.
15. [deferred] Implement explicit v12 reviewer scheduling policy for the two
    pinned intents. Affinity review prefers the prior reviewer through revision
    cycles and falls back when unavailable; independent opinion excludes the
    prior reviewer and may additionally require provider/model diversity. Both
    paths must reconstruct authority from the canonical dossier rather than
    depending on retained model context. This item changes no v11 reviewer pool
    or scheduling behavior and receives implementation Work only after later
    ordering and approval.
16. [deferred; confirmed 2026-08-22] Add stage-scoped dependency gates to the
    v12 scheduler. Model outcome dependencies as whole-Work gates,
    implementation dependencies as implementation-offer gates, and integration
    dependencies as verification/acceptance/integration gates. Recheck the
    named gate atomically when issuing that stage's offer. Leave v11's coarse
    Work-level dependency behavior and the current W2929→W2930 edge unchanged;
    create bounded implementation Work only when the v12 scheduler slice is
    ordered. Permit plan, contract, acceptance and fixture review ahead of an
    implementation-only gate; retain outcome gating when predecessor results
    can change that preparation, and require an actual immutable proposal
    before technical proposal/code review.
17. [deferred; confirmed 2026-08-23] Modularize the v12 TUI after the isolated
    worker path is practically usable end to end. Separate terminal input,
    navigation, view state, rendering, command editing, and authority
    interaction instead of reproducing v11's large `app.py`. Treat this as an
    adoption and maintainability requirement rather than an early PoC gate.
    Keep v11 changes bounded to necessary usability and defect corrections;
    do not start a broad v11 refactor or create implementation Work for this
    item until v12 has passed its usability proof.
18. [confirmed 2026-08-23; adoption gate] Keep provider-native language and SDK
    choices inside the isolated worker image. Expose only versioned canonical
    worker-control, agent-session, ACP/JSON where applicable, event, artifact,
    and evidence contracts to the host. Treat the current Node tree as the M2
    executable reference, not a production-language commitment. Before product
    integration, choose the host-side authority and Worker Manager language
    explicitly and run the portable black-box conformance suite against that
    implementation; keep runtime-specific hardening in the worker or adapter
    implementation that needs it.
19. [confirmed 2026-08-23; supersedes item 18's open host-language gate]
    Implement v12 host-side Baton, authority, scheduler, Worker Manager,
    durable control store, runtime adapters, proposal intake, and operator
    surfaces in Python. Permit a future Drift migration only through separate
    explicit Work. Admit Node or JavaScript only inside isolated worker images
    when practical for a provider SDK; do not expose those internals outside
    the canonical worker boundary. Freeze the current host-side Node tree as
    executable-reference evidence, replan M2 around the Python host, and do not
    extend Node host modules as the implementation path.
20. [confirmed 2026-08-24; apply at the next W4 handoff] Represent campaigns
    and milestones as roll-up Work containing bounded, independently reviewable
    implementation Jobs. Give every planned cut its own claim, discussion,
    evidence, review cycle and terminal outcome; use explicit dependency edges
    only where ordering is real. Do not split underneath a live claim. Let W4
    finish its current canonical-locator correction, then create or order
    separate M2-contained Jobs for the contracts inventory, section 13 and
    retention before any of those slices starts. Apply the same decomposition
    rule to later v12 milestones so progress is visible through child counts
    rather than hidden in a single large message history.
20a. [clarified 2026-08-24 after W6592 intake] Multiple named cuts or review
     rounds inside one Work do not satisfy item 20. W6592 ends with its already
     implemented public-composition Cut A after independent review. Create the
     still-unstarted contracts-package receiving inventory as a separate
     W3-contained Job with its own dossier, claim, evidence, review and outcome
     before routing it for implementation.
20b. [confirmed 2026-08-24; scheduler and proposal-pipeline invariant] Treat
     the complete Work graph as the project execution model, without a product
     limit on child count or logical nesting. Schedule independent ready leaf
     Jobs across N available workers, preserve every result as an isolated
     immutable proposal, and merge only through clean verification, review and
     the trusted integrator. Keep dossier-path flattening or promotion an
     indexing concern that never reduces logical containment, dependency or
     scheduling fidelity.
21. [deferred; confirmed requirement 2026-08-25; ledger W9901] Model v12 principals
    separately from hierarchical team scopes so one approver can serve a
    bounded organizational subtree while another team binds a dedicated
    one-to-one approver. Preserve one principal's inbox, runtime state,
    capacity and audit identity across those scopes. Keep organizational
    hierarchy independent from repositories, Work containment and dependency
    edges. Design and certify deterministic fail-closed role resolution in a
    separate M6-contained Job; do not backport this model to v11.
22. [deferred; confirmed 2026-08-26] Render opaque human-facing identifiers as
    lower-case, separator-free, typed Crockford Base32 shorthands such as
    `w12abc` in the v12 TUI, using the shortest prefix unambiguous in the stated
    authority/view. Accept either ASCII case from human input, case-fold for
    resolution, re-render lower-case, and never generate mixed-case compact
    IDs. Resolve every shorthand to its full canonical identity before
    mutation and fail closed on ambiguity. Preserve human-readable names and
    canonical digest encodings. Order this with the post-proof modular TUI
    work in item 17; do not migrate v11 IDs or delay the Docker ping-pong proof
    for it.
23. [confirmed 2026-08-27; MVP credential boundary] Permit a trusted runtime
    profile to pass one exact provider-owned host credential file into one
    running worker container through a read-only bind mount. Keep the image,
    assignment, argv, environment, labels, logs, Events, durable Baton state
    and outputs credential-free; expose no containing host state directory.
    Do not require an assignment-private Baton copy for the MVP, although the
    already staged W17110 provider remains an acceptable stricter input while
    that live Work is claimed. Revalidate this ruling at the next bounded
    credential-capability handoff and defer writable refresh caches,
    short-lived service credentials and multi-tenant brokerage until after the
    two-provider Docker proof.
24. [active scheduling rule; confirmed 2026-08-27] Use `baton.tuner` as the
    third campaign execution lane. At each queue review, identify ready,
    unclaimed, bounded leaves whose dossier and file ownership do not overlap a
    live claim, and reroute suitable documentation, packaging, fixtures,
    registries, additive test ownership, evidence repair and narrow polish to
    `baton.tune`. Do not manufacture parallelism across one coherent seam;
    preserve explicit ownership and independent review. W26296 is the first
    application of this rule.
25. [confirmed 2026-08-27; supersedes item 0n's inside-agent consent] Use one
    claimed execution runtime, not a separate consent runtime. The trusted
    adapter accepts a bounded reservation without launching the model; the
    Worker Manager atomically claims; only a successful claim launches one
    execution container. Offer expiry or a lost claim race launches nothing.
    Preserve model autonomy through typed `plan-rejected` and `unsupported`
    results after claim. The claimed container may receive the exact declared
    Work source under the read-only `/input` contract, but never the Baton
    authority store, integration credentials, unrelated host paths, or a
    writable canonical checkout. Cancel W26295 as superseded, remove the
    consent-posture axis from W26291 and W6636, and retain credentials as the
    separately governed read-only provider.
26. [confirmed requirement 2026-08-27; terminology clarified 2026-08-28 UTC;
    ledger W28880] Add generic, user-defined labels to v12 Work for
    cross-cutting metadata such as release name, requester identity and `v12`,
    with later exact filtering. A label is one opaque key, not parsed
    `name=value`; structured metadata is a separate future attribute or
    annotation feature. Keep labels distinct from containment, dependencies
    and scheduler state. The bound
    `work/records/2026/08/finding-v12-work-tags/` dossier owns grammar,
    mutation authority, event, projection, filter and TUI decisions. W28880 is
    independently scheduled because `baton.prompt` cannot authoritatively
    attach a child beneath the approver-routed W2 umbrella.
27. [confirmed 2026-08-28; apply at W6636's next handoff] Put the smallest
    honest end-to-end Docker happy path on the v12 critical path. Require the
    assertions and corrections needed to prove that positive arc, but split
    materially unstarted restart, race, alternate-engine and defensive
    hardening outcomes into separately claimed M2 Jobs. Schedule independent
    hardening in parallel where ownership permits, and do not make those Jobs
    dependencies of the next proof stage unless their exact invariant is
    required for an honest result. Treat this first finish line as evidence
    that the design is promising, not production-ready; then walk back through
    the preserved hardening Jobs after the architecture is validated. Do not
    change W6636's scope under its live review claim; perform the decomposition
    after that claim passes or releases.
27a. [confirmed 2026-08-28; campaign sequencing] Model v12 maturity as explicit
     capability passes, each ending in a demonstrable acceptance result. Keep
     every requirement deferred from the current pass in an owning finding and
     planned or parked Job assigned to a later pass. Do not place pass-N
     hardening on the critical path while pass N−1 cannot yet demonstrate a
     promising solution; after a pass validates the design, resume its recorded
     hardening Jobs toward the next maturity boundary.
27b. [confirmed 2026-08-28; development direction] Build v12 top-down through
     thin end-to-end vertical slices, then revisit each working slice in later
     passes to harden it. Use tests as evidence that the current pass's useful
     result is honest and repeatable; do not maximize isolated component and
     what-if coverage before the downstream architecture has earned that
     investment through an integrated demonstration.
27c. [confirmed 2026-08-28; durable engineering notes] Convert material TODO,
     improvement, hard-coding and revisit concerns discovered during a pass
     into attributable findings or lightweight Jobs linked to that pass. Keep
     them off the current critical path unless they can falsify its result; an
     inline comment may reference the Work but never replace it. If later
     design changes remove the concern, close the unstarted Job as superseded
     or cancelled with its rationale rather than implementing obsolete work.
28. [confirmed 2026-08-28; controlled early adoption] After a promising v12
    capability pass proves isolated input, execution, candidate output and
    review, use it in a bounded dogfood lane to develop suitable v12 leaves
    while later hardening proceeds. Keep the known-good coordination/recovery
    path until a separate cutover gate; admit only discardable isolated
    proposals during the pilot. Build toward at least two distinct coder lanes
    and two distinct reviewer lanes, each with its own participant/runtime
    identity and one claim, and preserve explicit serialization for overlapping
    ownership. Use stage-scoped dependencies to schedule honest review-ahead
    work so downstream contracts can be ready when implementation gates open.
    Record dogfood defects as later-pass Work.
28a. [confirmed 2026-08-28; coding route intents] Provide `impl` for initial
     honest vertical-slice delivery and `harden` for bounded robustness Work
     against an already validated design. Allow participant membership in
     either or both routes and scale each pool independently. Require `impl` to
     fix false-success defects and record deferred concerns; require `harden`
     to preserve accepted capability or request plan revision before redesign.
     Keep `tuner` distinct and do not encode provider fallback as `impl2`.
28b. [confirmed 2026-08-29; pooled scheduling and affinity] Treat route intents
     and future label-selected policies as eligibility inputs, not exclusive
     participant partitions. Select offers from the full eligible worker pool;
     prefer a participant/runtime with useful prior Work, dossier, repository,
     or revision-cycle context, but fall back after a bounded offer window so
     affinity never strands Work or leaves compatible capacity idle. Preserve
     one named recipient per offer, one successful atomic claim, no movement
     beneath a live Handler, and hard participant/model separation only for an
     explicitly requested independent opinion.
27d. [applied 2026-08-28; W6636 capability pass] W6636 closed satisfying as
     the bounded one-container Docker capability proof. W32382 owns the
     deferred negative/race endings; W32385 owns exact ended-runtime restart
     adoption; W32391 owns real-engine Podman certification and must be parked
     while that engine is unavailable. All three are M2 children of W3 and
     atomic follow-ups to W6636, with their own canonical dossiers.
29. [queued 2026-08-29; W38956; next v12 finish line] Run the first useful
    supervised v12 dogfood task. Compose the accepted host-side Python Worker
    Manager and real Claude Docker-worker seams into one operator-invoked,
    low-risk repository change: read-only declared input, no writable canonical
    checkout or Baton authority, candidate output under `/output`, correlated
    terminal result, and explicit human inspection, testing and acceptance or
    rejection. This is the campaign's high-priority critical path, not another
    component-proof detour. Full M3 automation, Podman, labels, remote
    execution, multiple lanes and later-pass hardening do not gate it unless an
    observed defect can make the positive result false. The bound
    `work/records/2026/08/finding-v12-first-useful-dogfood-task/` dossier owns
    its exact scope and evidence.
30. [confirmed 2026-08-29; W39435] Treat v12 canonical dossiers
    as one flat set of stable record locations. Store every mutable Work
    relationship only in Baton; filesystem ancestry carries no containment,
    dependency, campaign, follow-up, promotion, folding, routing, or scheduling
    semantics. Existing immutable v11-era paths remain historical rather than
    being moved. The top-level
    `work/records/2026/08/finding-v12-flat-dossier-storage/` record owns the
    materializer, locator, compatibility, projection, and generated-navigation
    follow-up. This does not gate W38956, but must land before the v12 dossier
    materializer and binding contract freeze.
31. [confirmed 2026-08-29; W39649; later M4 hardening] Normalize worker telemetry and
    introspection through the existing provider-neutral `probe`/`inquire`
    boundary. Use stable ACP usage/capability updates for ACP agents, Codex App
    Server's structured status/usage/account/quota/model/failure surfaces for
    Codex, and explicit unknowns for less capable agents. Never scrape terminal
    `/status` output or turn telemetry into workflow authority. The top-level
    `work/records/2026/08/finding-worker-telemetry-introspection/` record owns
    this follow-up. Its descriptive Job title deliberately omits a `V12`
    prefix; label `v12` is the future campaign organizer. It does not gate
    W38956.
32. [confirmed 2026-08-30; W43972; MVP result boundary] Give every attempt a
    manager-owned persistent `result/` envelope split into worker-writable,
    untrusted `output/` and manager-owned `logs/`. Permit Git workers to use
    `output/repo/` as their working clone and publish `output/result.json`
    last. Retain correlated, credential-safe logs on success and failure, and
    present them with the candidate during review so provider-exposed agent
    reasoning, messages, tools, tests and runtime events can explain how the
    output was produced without being mistaken for verification evidence.
    Defer transported custody-archive semantics until a demonstrated
    retention/export need defines them; archive work does not gate the first
    useful v12 path.
33. [confirmed 2026-08-31; post-W38956 objective] When W38956 closes
    satisfying, create a separately bound Work for a bounded v12 Job-migration
    pilot. Use v11 as the authoritative message bus and lifecycle record;
    preserve the selected Work identity and correlate it to one v12 Job and
    attempt for isolated execution and result custody. Migrate strictly one
    Work at a time, returning progress, result, failure, review and disposition
    to that same v11 Work before admitting another. Prove one non-synthetic
    leaf end to end before expanding beyond serialized migration. Do not start
    this pilot from a provisional or non-satisfying W38956 outcome, and do not
    treat it as the production cutover or a second Work authority.
33a. [confirmed 2026-09-01; supersedes item 33's trigger and automated bridge]
     Keep W38956's non-satisfying outcome as history. After W55758 closes the
     orphan-runtime and credential recovery gap, manually execute one low-risk
     real v11 Work through one correlated v12 attempt. V11 remains the sole
     Work authority; the prompt and approver freeze the input, invoke and
     monitor v12, inspect and test its untrusted result, and return progress,
     review and disposition to the same v11 Work. Admit no second Work until
     the first is resolved. Build no adapter, synchronization service or
     temporary migration automation.
33b. [confirmed 2026-09-01; native scheduler follows manual evidence] Repeat
     item 33a for two or three strictly serialized Works. If that evidence is
     credible, make the native v12 scheduler and control plane the next product
     objective rather than automating the v11-to-v12 procedure. Establish and
     exercise structured CLI/JSON scheduler surfaces first. Implement the v12
     TUI last, after the scheduler contract and recovery behavior stabilize.
33c. [clarified 2026-09-01; supersedes item 33b's unqualified last sentence]
     After the scheduler publishes an honest inspectable projection, build a
     read-only v12 TUI viewer for Jobs, workers, offers, attempts, gates, logs
     and results. Keep all commands in the human-attached context over the v11
     bus during this phase. A command-capable v12 TUI remains last and does not
     gate scheduler dogfooding or the first read-only monitoring surface.
