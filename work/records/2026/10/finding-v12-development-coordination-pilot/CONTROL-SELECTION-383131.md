# Proposed finite native Job control selection

W321608, baton.rvpc, E383131, 2026-10-29. **Proposal for owner decision; not selected implementation or execution.**

## Decision

Recommend selecting reusable, persisted native Job cancellation and finite successor/deadline control before the next finite documentation run. The exact blocked operation is starting the proposed one-pair Job with enforceable stage/overall bounds and a supported installed cancellation action. Research W378034 is accepted, but owner E383126 explicitly does not select these missing controls or a specification change.

Proposed behavior for owner selection:

- A versioned per-Job control contract fixes correction-round allowance and stage/Job wall deadlines at admission. The first documentation profile permits one implementation and one independent review, with zero correction rounds. A changes-requested verdict is preserved as such; it cannot open another pair or become acceptance. Reuse existing deployment decline behavior where applicable, rather than implement a second correction mechanism.
- Retain the proposed stage4800s and Job9960s values as explicit policy for this first profile, with provider3600s and verification900s per invocation. Stage time begins when its execution is admitted, before preparation; Job time begins when creation is durably accepted, including queue time. The first deadline or cancellation closes future admission and requests cessation of the exact active execution. These are deliberately tighter than two full7320s native task-token allowances; this policy may terminate a valid long invocation. It does not enlarge or replace token expiry.
- Allow120s for a bounded shutdown attempt after the trigger, separately reported. Failure to prove cessation by that point records unresolved shutdown, retains the hold and continues supported reconciliation; it does not declare success, free capacity, delete output or assert a hard cessation guarantee. Manager outage cannot be advertised as continuous enforcement.
- Expose installed, instance/Job-addressed cancellation through existing owning APIs. Persist stable request identity and fences before external effects. Pending/queued cancellation retires admission; active cancellation orders exact-generation cessation. Replays, late launch replies, concurrent admission and restart cannot reopen cancelled work or stop a replacement generation. Supervisor stop is not cancellation.
- Preserve elapsed time across restart using durable trusted timing evidence. Do not reset limits on restart or correction. Ambiguous time or runtime observations hold admission and report uncertainty. Independent verdict, human acceptance, result retention and stopped-failure settlement remain separate.

This extends current LIM-3/SCH/REC policy and therefore requires explicit owner approval and a pinned DESIGN update before dependent implementation. It is not a request to approve individual tests. The numbers and clock origins above are proposed product choices, not discoveries about existing code.

## Smaller alternative, if the owner prefers earlier learning

Explicitly select a different next-run exposure using existing per-attempt expiry and a qualified dedicated deployment with correction_policy=decline. It has no aggregate/stage deadline and no installed active-cancel command;7320s applies per task token for3600/900 settings, not to the whole Job. The manager must remain available to enforce expiry and reconcile unknown state. Paired deployment behavior and exact installed host/worker compatibility still need proof. This alternative is not selected or recommended by default, and the spent W370268 live grant cannot authorize it.

## Bounded delivery after selection

Two serial reviewable outcomes are justified: (1) installed replayable cancellation and successor-admission fence, including pending/active/late-launch/restart cases; (2) persisted correction/deadline policy feeding that same cancellation owner, with joined deterministic normal/refusal/timeout/unknown/replay evidence. The second depends on the first. W321608 retains integrated control/readiness acceptance. Create canonical Work and actual dependency edges after selection, reusing existing Authority/attempt/token/settlement owners and coordinating actual shared files with W371075 admission work. No parallel edits to common scheduler/CLI/composition files without explicit ownership. The implementer chooses necessary files; evidence locations are not path restrictions.

No product implementation is allocated now because the product decision is unselected. No need to wait for the whole startup/admission campaign to decide this control contract.

## Separate readiness obligations

W376246 is closed satisfying on exact safe preparation/retention source: failed installs retain named effects and refuse occupied retry. It does not certify an installed package or repair the older8876bf95 artifact. Current fresh-process IntegrationStore import still fails at role_contract.py:510; evidence and correction notices remain with W371295 and joined startup W375516. Resolve that concrete defect in the selected candidate before package qualification, without making all /2 admission work an automatic prerequisite to a separately selected /1 run.

Then rebind a coherent exact host candidate and necessary role/profile/transport evidence to the actual worker. W376804 found no worker rebuild necessary for its old source only; current templates/OCI changes mean that fact cannot qualify a new pair. Preserve W371296 and W325695 ownership and applicable evidence. Actual builds, installation, credential delivery, live execution and eventual cutover remain separately selected operations. This proposal authorizes none of them.

The useful documentation learning question and five acceptance criteria in W376804 remain unchanged. V11 remains authority for existing Work; the next native Job owns only its new assignments/results. Routine input-only preparation and the60s requirement remain W371075's outcome, not a bespoke per-run launcher project.
