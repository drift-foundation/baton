# Finding: separate the interactive prompt from background Codex Work

## Observed — 2026-08-21

The human-attached Codex conversation and the managed background reviewer both
used `baton.codex`. The foreground context claimed W2 while the runtime lease
published by the managed context correctly reported its own state as idle.
The TUI therefore showed `Handler=baton.codex` beside `Run=idle` even though
the foreground conversation was doing the Work.

The authority did not fabricate either fact; one participant identity was
being used for two execution contexts. That defeats runtime observability and
creates a duplicate-execution risk if the managed context wakes while the
foreground context is acting.

## Confirmed identity model — 2026-08-21

- `baton.prompt` is the one human-attached interactive copilot. It remains
  available for Slawomir's prompts, translates confirmed decisions into
  durable findings and coordination requests, and does not consume or claim
  routed background Work.
- `baton.codex` is the managed background Codex participant. It owns review,
  research, planning, and management of Work workflows through the configured
  reviewer route and its one readiness/runtime path.
- `baton.claude`, `baton.tuner`, `baton.slaw`, and `baton.gemini` retain their
  current identities and responsibilities.
- `baton.prompt` is a participant with one explicit `prompt` role but is not a
  handler of a routable endpoint. It may read, discuss, and create Work as a
  trusted team member; actions requiring a live route Handler remain with the
  appropriate background participant.
- The mapping is one-to-one in both directions: every participant names exactly
  one live execution context, and every execution context uses exactly one
  participant. The interactive and background contexts never share a
  participant identity, runtime lease, or active claim, and no hidden second
  context acts under either address. A conversation thread is not an identity.
- Each participant's runtime publisher observes that exact mapped context.
  `Run` is therefore evidence about the same execution context that can become
  Handler. `baton.prompt` has runtime reporting for its interactive context but
  no Work-readiness consumer; runtime visibility and readiness consumption are
  separate responsibilities.
- The managed `baton.codex` dispatcher may continue working while
  `baton.prompt` is idle between user messages. Its canonical Handler and
  adapter-reported `Run` state then describe the same execution context.

This concretizes the generic v12 decision in
`finding-v12-isolated-agent-workers/FINDING.md` under “Interactive and managed
execution identities” and also corrects the current v11 deployment topology.
It changes configuration, launch instructions, and repository policy only; it
does not require a Baton protocol, application-code, or SQLite schema change.

## Migration boundary

1. Add the `prompt` role and `baton.prompt` participant to the deployment
   proposal without adding a kind or route for it.
2. Keep exactly one readiness/runtime publisher for `baton.codex`; it targets
   the managed background Codex thread.
3. Launch the human-attached conversation explicitly as `baton.prompt`, publish
   runtime state for that exact interactive context, and give it no readiness
   consumer.
4. Do not relabel a live claim. Release or complete any foreground
   `baton.codex` claim first, then let the managed background context claim a
   fresh assignment episode.
5. Update repository identity policy and operating guidance so a restarted
   agent does not silently collapse the two identities again.

## Deployment supersession — 2026-08-21

The prepared in-place generation-3 cutover against authority `88990a87` is
**superseded** as the rollout path. Its files remain useful validation
evidence, but they must not be installed over the live schema-26 authority.
W1477 now requires schema 27 and a fresh authority, so carrying W1594 as a
separate regen/restart would add a second cutover while preserving no useful
state.

Land and deploy the two compatible changes together. Initialize a fresh
coordination home with the new release, add `prompt` and `baton.prompt` to the
generation-1 proposal before activation, preserve the existing kinds and
routes, and start the fresh backend with separate prompt, reviewer, and tuner
contexts. Generate the execution policy from that accepted fresh config and
attach the human TUI only to the minted prompt context. The old generation-3
candidate is never copied blindly: its authority UUID, paths, release binary,
and generation are old-instance facts.

The combined rollout does not weaken W1594's acceptance gate. The retained
fresh-context tests must first describe the three-context contract, the
dispatcher template must assert the prompt target explicitly, and the suite
must prove there is no readiness service for `baton.prompt`. A red retained
test is a correction request, not an acceptable deployment exception.

## Acceptance

- The accepted configuration contains `baton.prompt` with role `prompt` and no
  routable endpoint.
- The repository policy names both identities and their non-overlapping scope.
- One managed background thread/readiness path publishes runtime facts for
  `baton.codex`. The one interactive context publishes its own runtime facts
  for `baton.prompt`, but no readiness path exists for `baton.prompt`.
- Runtime inventory proves a one-to-one participant/context mapping; a context
  shared by two participants or a participant represented by two contexts is
  unhealthy and must not receive Work.
- A background `baton.codex` claim displays a `Run` state from that same
  context while the interactive prompt remains responsive.
- Existing participants and routes are otherwise unchanged.
- The schema-27 fresh rollout starts with the prompt identity already present;
  no in-place generation-3 regen is part of the accepted operator sequence.
