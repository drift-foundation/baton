# Plan

1. [pending prerequisites/revalidation] Re-read W62098's latest review-cycle
   ruling and the accepted W71917 workspace plus W71875 stage-state contracts.
2. [pending] Define durable development-line, mutable workspace, immutable
   checkpoint, verdict, and current-stage identities without teaching the
   generic manager Git semantics.
3. [pending] Compose implementation completion, checkpoint freeze, read-only
   independent review, changes-requested return, later checkpoint creation,
   and final integration eligibility.
4. [pending] Enforce one writer while allowing disposable runtime replacement
   and independently scheduled readers of immutable checkpoints.
5. [pending] Prove ten correction rounds, immutable earlier checkpoints,
   review identity/binding, no restage/clone/candidate copy, restart at both
   handoff edges, and rejection of intermediate checkpoints from integration.
6. [pending independent review] Bind the final proposal digest and enumerate
   every changed production and test path.

This leaf is blocked on W71875 and W71917. Pool selection remains W71877;
integration eligibility consumption remains W71878.
