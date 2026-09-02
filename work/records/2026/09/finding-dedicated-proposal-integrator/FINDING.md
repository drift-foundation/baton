# Add a dedicated proposal integrator

Ledger Work: W65212

## Finding

W61984 completed implementation in an isolated v12 worker and passed an
independent review, but the accepted proposal returned directly to the human
approver. That collapses two different responsibilities into one step:

- deciding whether the proposal is correct; and
- integrating that exact accepted proposal into the current target tree.

Integration has its own failure modes: the target may have moved, an intended
path may overlap unrelated work, the retained artifact may not match the
reviewed digest, or applying it may expose a target-level verification failure.
Those conditions require a distinct accountable Handler rather than another
implementation turn or an implicit approver-side file copy.

## Confirmed decision — 2026-09-01

Introduce a Codex-backed `baton.merge` participant holding the `integ` role.
The initial workflow is:

```text
implementation -> independent review -> integration -> approval/commit
```

The integration role initially owns only final integration review and a
bounded import into the current working tree:

1. read the Work dossier and the newest independent review;
2. resolve the exact retained proposal and verify the review-bound digest;
3. compare the proposal with its declared base and the current target;
4. refuse on missing provenance, digest mismatch, target drift, overlapping
   divergence, or conflict rather than inventing a merge;
5. import only the accepted proposal paths into the working tree;
6. inspect the resulting repository diff and run the bounded integration
   verification named by the Work; and
7. pass the Work to the approver with the exact imported paths, checks, and
   remaining operator action.

The integrator does not redesign the accepted proposal, make opportunistic
implementation changes, resolve a rejected plan, or silently broaden its
path set. A required correction returns through a new implementation/review
revision.

Repository Git policy remains unchanged. The integrator may prepare and verify
filesystem changes, but it never stages files, commits, rebases, merges Git
history, creates branches or tags, or pushes. Slawomir alone owns those Git
mutations. Here, "integration" means bringing an accepted proposal into the
current working tree and proving the resulting diff is ready for Slawomir's
commit.

This role operationalizes W62098's already confirmed distinct Git-aware
integration stage. It does not change that record's artifact-neutral Worker
Manager boundary or reintroduce custom proposal ancestry in place of Git.

## Initial deployment shape

For the Baton team, add:

- participant `baton.merge`, display name `Integrator`;
- role handle `integ`, display name `Integrator`;
- route handle `integ`, resolved only by member `merge`;
- kind handle `merge`, display name `Integration`, defaulting to `integ`;
- one dedicated Codex context, dispatcher target and readiness consumer for
  `baton.merge`; and
- the exact managed execution-policy rules required by that participant.

The participant has its own context and runtime publication. It is never an
alias for `baton.codex`, `baton.prompt`, or `baton.slaw`.

## Implementation revalidation — 2026-09-02

Generation 4 of the live v11 authority still has no `merge` participant,
`integ` role/route, or `merge` kind. Its managed infrastructure already proves
the required one-context/one-target/one-readiness pattern for the reviewer and
tuner, so the dedicated integrator is an additive deployment instance of that
existing contract rather than a bridge or protocol change.

The repository-owned implementation surface is `AGENTS.md`,
`docs/PROPOSAL-INTEGRATOR.md`, `conf/infra.example.json`, and
`conf/codex-event-bridge.template.json`. The live mailbox configuration,
execution-policy installation, configuration acceptance, drain/restart, and
Git mutation stay deployment-owned approver actions. This separation is not a
scope reduction: the tuner prepares and verifies the exact configuration and
runtime shape, while `baton.slaw` performs the privileged acceptance and
restart gate the accepted role model reserves to it.

## First use

After the role is accepted and its managed runtime is healthy, W61984 is the
first integration assignment. It must use only the independently signed run10
proposal with digest
`sha256:540b2b4bd3c29db29ed027bef9338e55c3dff766770008c8eb04ef19534f11d8`.
Run8 and every other retained candidate are out of scope.

## Acceptance

- The accepted Baton configuration resolves `baton.merge` as the sole Handler
  of `baton.integ` and exposes `baton.merge` Work through the `merge` kind.
- Role instructions state the exact read, import, refusal, verification and
  Git boundaries above.
- Managed infrastructure creates one fresh Codex context, dispatcher target
  and readiness consumer for `baton.merge`, and startup proves that target is
  loadable.
- The execution-policy bundle contains the exact canonical Baton operations
  for `baton.merge`; no broad shell or Git mutation authority is added.
- W61984 can be routed to the integrator, claimed by `baton.merge`, imported
  from the exact signed run10 proposal, verified, and returned to `baton.ops`
  without the integrator touching the Git index or history.
