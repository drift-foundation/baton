# Finding: final-polish work needs an independent tuner persona

## Observed

Protocol and application implementation is owned by the implementer. Final
polish such as documentation, `just` recipes, packaging, deployment UX,
templates, and other non-core tooling can proceed independently, but sending
it through the implementation endpoint serializes unrelated work.

## Confirmed decision — 2026-08-18

Introduce a Codex-based `baton.tuner` participant with the `tuner` role. A new
`baton.tune` endpoint resolves through the `tuner` route to that participant.
The tuner owns final polish and non-core tooling; `baton.impl` retains Baton
protocol and application-code ownership. Concurrent work still requires
non-overlapping file ownership.

The existing `bug`, `feat`, `impl`, `ops`, `decide`, and `rsrch` endpoint
semantics remain unchanged. In particular, this addition does not silently
reroute existing operational or approval Work.

## Confirmed decision — 2026-08-18 (durable operating instructions)

The tuner's operating description must be reusable configuration, not a
one-off prompt remembered by an operator. Baton configuration owns the role's
durable instructions; a launcher or readiness adapter uses those configured
instructions when it creates or resumes the participant's agent session.

The accepted generation-2 configuration does not yet prove that vocabulary or
the launch integration. Until it does, the existing manually prompted tuner
thread is only a bootstrap aid, not the final contract.

## Revalidation — 2026-08-18 (W101 implementation start)

The ruling still matches the current tree and protocol. The accepted
generation-2 `baton.json` declares the tuner topology but no reusable role
instructions, while both readiness adapters still rely on sessions whose
operating persona was established outside Baton.

The implementation boundary is now concrete:

- role entries gain one optional, strict `instructions` string; existing
  uninstructed roles remain valid for non-agent participants;
- one participant-relative JSON read resolves the effective instructed role,
  inferring it only when exactly one held role has instructions and refusing
  zero or multiple matches unless the caller selects a held role explicitly;
- external launchers consume that read. The installed Codex app-server schema
  accepts `developerInstructions` on both `thread/start` and `thread/resume`.
  ACP has no equivalent developer-instruction field, so its bridge resolves
  the text before session creation/load and includes it in every supervised
  readiness prompt delivered to that session, including the first;
- instruction selection happens before a launcher creates or resumes an agent
  session. A malformed, missing, foreign, or ambiguous selection fails closed
  without falling back to an operator-authored prompt.

This is an additive configuration and launcher feature. It does not change
Work, routing, readiness, message, or event semantics, and it does not restore
the retired v10 all-session stack.

The accepted tuner role text for the next configuration generation is:

> You are baton.tuner. Own documentation, recipes, packaging, deployment UX,
> templates, and other final-polish work. Do not modify Baton protocol or
> application code unless explicitly reassigned.

## Implemented — 2026-08-18 (W101)

- Strict role entries accept only an optional non-empty `instructions` string;
  the new participant-relative `instructions role=...` read projects the text
  and accepted generation from the digest-bound configuration.
- Codex launch can create a thread with that text as
  `developerInstructions`; configured targets re-resolve the accepted text
  before startup and reapply it on every resume.
- The ACP launcher resolves before session selection or agent-process use and
  carries the text in every supervised readiness prompt because ACP exposes no
  developer-instruction field.
- Release examples, setup/operation guides, bridge configuration, and the
  deployed ACP runtime carry the new path. Existing manually prompted sessions
  remain compatible bootstrap sessions until deliberately restarted/resumed.

Focused and packaging verification passed. The complete parallel Python slice
also passed 1,231 tests. Its subsequent serial TUI slice was not a W101
failure: concurrent schema-20/TUI work built some fixtures with schema 19 and
produced 14 version/row-shape failures in W30/W7 paths outside this record.
Those files and tests were left untouched.

## Revalidation — 2026-08-18 (changes-requested assignment)

The independent review's two P1 findings reproduce on the settled candidate:
`src/baton_work/jsonapi.py` now publishes projection 10 while the unchanged
participant-action envelope is still accepted only through projection 9 by
the shared Codex/ACP readiness validator, and W101's instruction reader also
accepts only projection 9 even though its result is unchanged in projection
10. The bounded contracts are therefore 7/8/9/10 for readiness and 9/10 for
role instructions; projection 6 is pre-readiness-contract, projection 8 is
pre-instruction-contract, and future major 11 remains unsupported.

The Codex target schema also validates each new `identity.participant` but no
longer retains the former cross-target uniqueness check. Distinct targets and
threads naming the same participant would violate the one-readiness-path rule.
Restore uniqueness over `identity.participant`; an explicit role does not make
a duplicate participant assignment safe.

## Review corrections implemented — 2026-08-18

- The shared Codex/ACP readiness validator now accepts the bounded unchanged
  participant-action contract through projection 10 and still refuses
  pre-contract projection 6 and unsupported future projection 11.
- The role-instruction reader accepts exactly projection majors 9 and 10,
  with positive 10.x coverage and negative pre-contract/future coverage.
- Codex configuration again refuses one Baton participant assigned to two
  targets, even when the threads and selected roles differ.
- Focused Codex launch/config/readiness tests pass, the complete Codex bridge
  suite passes, all 40 ACP bridge tests pass (including new and loaded session
  first-turn instruction delivery), and the four W101 Python tests pass.
  `git diff --check` remains clean.

## Superseding decision — 2026-08-18 (complete role bootstrap contract)

The earlier W101 boundary in **Revalidation — 2026-08-18 (W101
implementation start)** is superseded where it made role `instructions`
optional and allowed uninstructed roles. The tuner exposed the need, but it is
not a special case: every configured role must carry non-empty durable
instructions. A deployment with any uninstructed role is incomplete and must
fail configuration validation.

Instructions are owned once by the role and inherited by every member when
launched in that role; they are not copied into each participant. Every agent
launch selects one explicit role held by its configured participant, even
when the participant currently holds only one role. This keeps a later
multi-role assignment from silently changing the persona and makes the
participant, role, and scope of the session auditable deployment inputs.

The durable role instructions include both:

- the role's authority, responsibilities, exclusions, and handoff boundary;
- the required bootstrap/read material, including repository policy and the
  operating or role-specific documents needed before the first assignment.

Read directives remain instruction text, so they may name repository-relative
files, configured-root references, or other deployment material without
making authority reads depend on the current filesystem. The launcher must
deliver the complete accepted text before the first readiness assignment. The
agent, not the launcher, reads and applies the named material. Missing files
or an inability to read them are reported as an operational finding rather
than silently dropping the directive.

The next Baton deployment must provide complete instructions for `rview`,
`impl`, `approv`, and `tuner`. At minimum, every repository-working agent is
directed to read the repository's `AGENTS.md`; Baton roles also read the
current Baton operating guide and the exact Work dossier named by an
assignment. Role-specific text then constrains reviewer, implementer,
approver, or tuner authority. The tuner remains the first rollout proof, not
the only instructed persona.

This ruling reopens W101's implementation boundary after the clean
generation-3 review. That review remains valid evidence for instruction
transport, generation binding, and launcher delivery, but deployment is
blocked until universal role validation, explicit launch selection, complete
role texts, and their regressions are independently reviewed.

## Revalidation — 2026-08-18 (expanded W101 assignment)

The settled tree confirms that the expansion does not require another
instruction transport. `participant_instructions`, Codex
`developerInstructions`, and ACP first/readiness-turn delivery already carry
the accepted text. The remaining gaps are all at the configuration and launch
boundary:

- role validation still treats `instructions` as optional;
- the participant-relative read and launcher configurations may infer a role
  when exactly one instructed role is held;
- the shipped example and current Baton generation do not define complete
  instructions for every role;
- the docs still describe only "agent-backed" roles as instructed and do not
  make required reading part of the bootstrap contract.

Protocol configuration remains role-generic: it requires instructions on
every declared role but never hard-codes `rview`, `impl`, `approv`, or `tuner`.
Those four are the Baton deployment's roles and its next accepted generation
must give them these minimum boundaries:

- `rview`: read `baton:AGENTS.md`, `baton:docs/EFFECTIVE-BATON.md`, and the
  exact assigned Work dossier; own research, durable findings and plans,
  coordination, and independent review; do not implement protocol or
  application changes unless explicitly reassigned.
- `impl`: read the same policy, operating guide, and exact dossier; own only
  claimed implementation and its tests, revalidate pinned decisions, maintain
  implementer progress, preserve independent review, and never mutate Git.
- `approv`: read the same policy, operating guide, and relevant dossier; own
  product/operational rulings, configuration acceptance, Git, and destructive
  deployment gates; do not represent unreviewed implementation as complete.
- `tuner`: read the same policy, operating guide, and exact dossier; own
  documentation, recipes, packaging, deployment UX, templates, and other
  explicitly assigned final polish; do not modify protocol or application
  code unless explicitly reassigned.

`baton:` above is the configured repository identity, not an inferred
checkout path. A deployment for another team names its own configured-root
references and role-specific material. README material may be included for
product orientation, but it does not replace repository policy or the
operating guide.

Every configured participant must hold at least one fully instructed role.
Instructions remain role-owned and are not copied into member entries. Every
agent launcher configuration supplies both participant and role; the
participant-relative `instructions` read likewise requires `role=`. This is
an intentional fail-closed launch contract even for a participant that holds
only one role.

## Acceptance

- The editable coordination config contains the `tuner` role, route,
  participant, and `tune` kind.
- Existing routes and handlers are unchanged.
- Baton accepts the next config generation atomically through `regen`.
- `baton.tuner` resolves as the sole handler of `baton.tune`.
