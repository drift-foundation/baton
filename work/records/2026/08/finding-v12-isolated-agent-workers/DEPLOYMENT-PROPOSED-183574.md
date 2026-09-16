# Deployment publication recommendation — W2 claim183574

Proposed documentation only, not an applied product change. Supersedes the
pending insertion in
baton:work/records/2026/09/finding-v12-correction-restart-proof/DEPLOYMENT-PROPOSED-182748.md
for publication after the Sep16 fresh-attempt ruling. Preserve that historical
proposal. Existing documentation ownership should publish this one bounded
insertion and return its exact candidate for independent review.

Target baton:v12/python/DEPLOYMENT.md SHA256
5dc34d45d5b098baca7318df305f96bc02275cd3ecaaa9a20e0f4758a641c7a5.
Insert after `### Qualification and remaining limits`, immediately before
`## Runtime-attempt deadlines`. Revalidate the target and anchor before editing;
preserve all surrounding bytes. No runtime test or provider rerun is needed.

## Exact proposed insertion

### Fresh attempts and optional conversation reuse

The minimum recovery path uses a fresh provider conversation in a new isolated
attempt. For this path, implementation worker configuration uses
`baton.v12.single-worker-deployment/4`, with no `provider_context` member and no
reserved `provider-context-receipt` output declaration. The ordinary staged
deployment supports these worker configurations, including multiple configured
workers and per-Job bindings. The worker creates a private provider home and
does not pass session-resume arguments. The repository's retained checkpoint
and attempt lineage are separate from the provider conversation.

This is a configuration for new context-free work, not permission to downgrade
an already context-bound attempt. Its existing context binding cannot be removed
to bypass admission or finalization checks. Unknown previous execution remains
held until positively excluded through the applicable runtime and authority
owners. Recovery is explicit; failed Jobs are not automatically relaunched.

Accepted deterministic abandonment evidence stops and fences an unfinished
correction, restores its retained checkpoint, revokes its writer, ends its
abandoned episode, and lets ordinary serving allocate a fresh assignment. The
same recovered Job proceeds through independent review and integration, with
its retained result still bound to the corrected publication. Uncommitted
scratch from the explicitly abandoned attempt may be discarded; the retained
checkpoint and earlier accepted effects remain attributable. The managed
integration recovery described above completes missing settlement without
repeating a recorded target update. Unknown runtime and uncertain target-effect
holds remain manual recovery cases.

Separate deterministic context-enabled evidence proves useful code correction
through independent review, managed preparation, judgments, apply and authorized
import. Its counted manager reopen closes and reconstructs the composition and
Job/Control handles after a durable result and destroyed original runtime.
Positive original provider-call and engine-start counts remain unchanged after
reopen and continued serving; the distinct correction executes once. Synthetic
duplicate observations are rejected. This is manager recomposition within one
process using deterministic provider/verifier subprocesses and simulated OCI,
not host or power-loss exactly-once proof.

Production conversation reuse is optional and remains unqualified. Its production
profile and actual OCI context execution remain refused. Saved-state custody,
restoration, strict terminal model identity and cache savings are not established
by the context-enabled deterministic proof. The ordinary fresh path does not
depend on those context receipt fields and does not establish their correctness.
It also does not establish an exact selected live model merely from a successful
provider exit. Preserve the existing runtime profile and attribution limits;
strict model qualification cannot be inferred from this recovery selection.
