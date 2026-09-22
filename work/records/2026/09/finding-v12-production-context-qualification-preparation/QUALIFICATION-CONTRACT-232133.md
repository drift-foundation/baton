# The one-run qualification authorization and production certification — the concrete contract (claim232133)

Per review-2026-09-21T18-30-00Z.md: the details that were missing from the
232082 design, recorded exactly, so the continuing bounded implementation
can land them mechanically and the review can hold it to a written
contract. This claim records; the same authorized continuation implements
against it next, then the focused fake-engine tests, then the exact
executable packet — in that order, as the review sequences it.

**Corrections adopted first.** Branch A needs no new owner decision:
`W194457 OWNER-TRUSTED-IDENTITY-20260917.md` and the current `run_vector`
already select the shared manager/worker execution identity, so same-UID
custody is the standing posture and the cross-UID prerequisite is closed
by the existing ruling — nothing to probe, nothing to implement.
Candidate-183524 remains unreviewed and unaccepted. The 232082 packet's
"fully specified" claim is withdrawn: a packet without an executable, a
manifest, an exact owner command and state/continuity assertions is an
outline, and §4 below states exactly what the real one must contain.

## 1. The profile vocabulary

`_profile` admits `qualification` in `("deterministic", "candidate",
"production")`.

- `deterministic` — unchanged in every consumer; the composed fixtures'
  world.
- `candidate` — admissible ONLY under a live, unconsumed one-run
  authorization (§2) binding this exact profile digest. It exists so the
  qualification run itself never masquerades as either other kind.
- `production` — admissible ONLY after certification (§3) recorded the
  full-config evidence for this exact profile digest.

## 2. The one-run authorization: operands, consumption, replay, failure

A durable owner act in `provider_context.py`:

    authorize_qualification_run(control, *, profile_digest,
                                deployment_binding, job_id, note)

- **Operands bound at authorization:** the candidate profile digest
  (which itself pins `runtime_profile_digest`, `image_digest`,
  `adapter_digest`, `retention_policy_digest`, `argv_policy_digest`,
  `environment_policy_digest`, `cli_build`, `model`, `reported_model` —
  the FULL config, not a model tuple); the deployment binding (authority
  uuid + the deployment's configured context storage path + workspace
  storage identity) so the authorization cannot be spent on another
  instance; the exact `job_id` it may serve; a bounded owner note. The
  act journals under one operation id
  `context-qualification:<profile_digest>` — an exact retry replays, a
  different-operand retry refuses.
- **Consumption:** the authorization is consumed by THE ADMISSION COMMIT
  of the first context use whose attempt belongs to the bound job on the
  bound deployment — inside the same `_transition` that commits the
  `admit`, so a crash before commit leaves it unconsumed and a crash
  after leaves exactly one consumer. Every later admission attempting to
  use it — same job or not — refuses by name. The restore admission of
  the SAME context (the qualification's own second turn) does NOT
  consume a second authorization: consumption is per CONTEXT, checked as
  "this context's opening admission consumed it", so the two-turn run is
  one authorization.
- **Replay:** re-admission of the same attempt replays the committed
  admission (existing replay semantics) and finds the consumption
  already recorded — no double-spend, no refusal.
- **Failure:** any terminal outcome of the qualification Job — fault,
  refusal, timeout, hold — leaves the authorization CONSUMED. There is
  no automatic re-arm; a new run is a new owner act with a new
  authorization. `hold_context_use`/`retire_context` on the
  qualification context do not resurrect it.

## 3. Certification: full-config evidence provenance

    certify_production_profile(control, profile, evidence)

- `profile` is the production-vocabulary twin of the candidate profile:
  every config member equal EXCEPT `qualification`, enforced member by
  member — a production profile never diverges from what was qualified.
- `evidence` names, and the act validates against the store before
  recording: the consumed authorization's operation record; BOTH serving
  receipts of the qualification context (open generation 0 and restore
  generation 1), each already strict (`terminal: success`, `complete:
  true`, exact `model`/`reported_model`/`cli_build`, derived
  conversation id, delivery/input/policy digests); the finalized
  generation-1 manifest (state layout and generation continuity — the
  restore demonstrably ran from the manager-reconstructed minimal state,
  with the exclusion rules applied, which the finalize/validate path
  already enforces); and the run's two attempt-room provider result
  artifacts by digest (the retained usage artifacts named under
  review230731 R2). Certification is refused while the context is
  unretired or any receipt is non-strict. The act journals under
  `context-certification:<production_profile_digest>` with the same
  replay rule.
- **The explicit unresolved evidence, carried into the contract:** the
  real CLI's result-JSON model field behavior (the historical
  `modelUsage` expected-plus-other failures in this dossier) is exactly
  what the strict receipts will measure; certification REQUIRES the
  strict match and therefore fails honestly if the pinned build still
  reports models the profile does not name. No relaxation is
  pre-authorized.

## 4. Behavior at every current profile consumer

| Consumer | `deterministic` | `candidate` | `production` |
| --- | --- | --- | --- |
| `_facts` (admission + every live re-check) | unchanged | admissible only while the §2 authorization is live-or-consumed-by-this-context, bound deployment/job proved each check | admissible only with §3 certification recorded |
| `bind_context_invocation` / `_invocation_base` / `serving_argv` | unchanged | as `_facts` (they re-read the profile; the vocabulary check is centralized in `context_profile_of`'s answer plus one admission-side authorization proof, not scattered) | unchanged mechanics |
| receipt validation (`provider_context.py` receipt/terminal readers) | unchanged | strict fields exactly as production — the qualification run proves the production contract, so nothing is looser | unchanged |
| `context_delivery` materialize / validate_generation / seal_generation | unchanged | unchanged mechanics (custody does not vary by vocabulary; the deployment binding was proved at admission) | unchanged |
| `single_worker._context_preflight` | unchanged | requires the live/this-context authorization before any launch composition, same named refusal as admission | requires certification |
| `oci.OciAdapter._context_execution` | REFUSES real execution, as today | ADMITS when: authorization proved for this attempt's context AND custody valid under the standing shared identity AND the composed context mount boundary present — each unmet precondition refusing by name | ADMITS with certification in place of authorization |

The centralization rule the implementation must follow: `context_profile_of`
keeps answering the stored profile; the vocabulary GATE lives in exactly
two places — the admission (`_facts`, which every consumer already funnels
through for live checks) and `_context_execution`/`_context_preflight`
(the launch boundary). No consumer grows its own copy.

## 5. The focused tests (next step of the same continuation)

Fake-engine, no live model: real `_context_execution` (mock removed)
positives — candidate profile + live authorization admits; production
profile + certification admits — and named-refusal negatives for every
row: deterministic profile at the real guard; candidate without
authorization; consumed authorization on a second context; wrong
deployment binding; wrong job; production without certification;
certification attempts with a non-strict receipt, an unretired context, a
mismatched config member and a replayed/different-operand act. Plus the
§2 replay case (same attempt re-admission) and the two-turn
single-consumption case.

## 6. The exact packet (after §5)

An executable in this dossier (`qualification-run-<claim>.py`), gated on
`--approved-manifest <sha256>` exactly as this Work's earlier fixtures
were, whose manifest binds: the independently rebuilt image digest, the
candidate profile document and digest, the authorization operands, the
Job/submission documents, the supervisor bounds (two turns, 180 s per
provider turn, 600 s total, no retry), and the assertion set — both
strict receipts, generation-1 restoration from reconstructed state,
conversational continuity (the restore answer must reference turn-1
content, which the feedback-bearing prompt makes checkable), and the
hash-bound evidence list written before certification may consume it.
The owner command is ONE line printed by the packet preparation claim
with zero placeholders. No live execution occurs before that separate
owner selection.

## Costs and preservation

This claim: dossier record only — zero tests, builds, live calls,
identities; every guard, consumed identity and retained byte unchanged.
