# Plan

**Status — current Baton Work `W2` (`5f717eee-W2`); roadmap only.
The original `bec445ce-W193` and later `bcbb9dbf-W2` authorities are retired.
No v12 implementation has started. The operational decisions and review
corrections are pinned. The approved order specifies the minimal state machine
first, then a bounded real end-to-end spike before compatibility manifests or
production implementation.**

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

0n. [done 2026-08-20] Make a short-lived, single-use, manager-issued claim
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

1. [pending] Model assignment generations, read-only pre-claim inspection,
   expiring single-use claim tokens, claim-capability-gated writable
   workers, cancellation, quiescence, stale-worker rejection, runtime-profile
   probation/disablement, typed plan rejection and revision, and integration
   dispositions as one protocol state machine.
2. [pending] Specify the outer versioned Baton worker-control API plus typed
   input, immutable local change-proposal or non-Git result, and verifier-result
   manifests. Include named source descriptors, source type/URI/destination,
   Git base/target/proposal identities or directory content/output digests,
   role/policy/toolchain/image digests, tests, logs, and dossier evidence.
3. [pending] Specify ACP as the normalized inner agent endpoint without adding
   repository or container lifecycle to ACP: use a mediated ACP relay for
   native ACP agents and a narrow ACP adapter for non-ACP runtimes such as
   Codex App Server.
4. [pending] Specify the runtime-neutral worker conformance suite covering
   typed-source materialization and digest verification, read-only input,
   declared-output containment, freeze/validation/collection, workspace and Git
   isolation, generation-gated publication, cancellation and
   quiescence, pre-claim execution denial, claim-timeout reporting and explicit
   route-policy consequences, runtime-profile reliability policy, credential
   non-retention, explicit policy, untrusted outputs, normalized lifecycle,
   transport-partition fencing, proof-bound remote reattachment, and
   negative/race/crash/recovery behavior.
5. [pending] Build one OCI reference worker, runnable by Docker or Podman, that
   supports both a configured read-only Git source cloned into private writable
   storage and a digest-bound read-only directory source with separate writable
   result output. Preserve OS/agent sandboxing, prohibit nested container
   runtimes, never expose the host container-runtime socket, and require it to
   pass the runtime conformance suite.
6. [pending] Build the trusted host-side Worker Manager and OCI runtime adapter
   behind the worker-control API. Normalize start/cancel/inspect/collect/
   destroy, persist attempt-to-runtime reconciliation identities, and prove
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
   ACP-to-App-Server adapter against the same worker contract.
11. [pending] Exercise crash, provider overload, cancellation race, late
   recovery, duplicate assignment, stale candidate, conflicting candidates,
   rejected review, mid-turn contract supersession (the W2938 incident),
   revision, and manual-salvage workflows. Prove that forced cancellation can
   discard only the superseded attempt's private writes without touching the
   canonical checkout or another worker.
12. [pending] Run a multi-agent trial with concurrent independent Work and
   verify that no worker can alter another worker or the canonical checkout.
13. [pending] Define migration, deployment, local proposal storage, operating
    documentation, retention, and observability before considering v12
    production adoption.
