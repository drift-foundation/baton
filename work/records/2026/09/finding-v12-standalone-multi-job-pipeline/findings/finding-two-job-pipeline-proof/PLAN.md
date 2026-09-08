# Plan

Parallel preparation, 2026-09-08, lightweight Work W115572: baton.tuner owns only
TUNER-PREFLIGHT-2026-09-08.md under a separate lightweight preparation claim.
Read PREPARATION-2026-09-08.md and the approved three-Job clarification, then
resolve scenario/API feasibility, propose contracts and resource measurements,
and identify exact freeze inputs still owed by assembly. No execution or new
dependency; this Work remains gated on W103068. Tuner returns its report to
baton.prompt through baton.ops coordination and releases its claim.

1. [done; review-2026-09-04T14-10-08Z.md] Review the demonstration shape, evidence
   matrix, operator-intervention budget, test-change scope, injected correction
   and failure, resource measurements, and pass/fail boundary. This stage
   approves only the proof plan; it cannot claim the demonstration passed.
2. [gate run 2026-09-06; DOES NOT PASS -- provider placement approved]
   Revalidate the approved plan against the accepted control-plane,
   source/workspace, concurrent-stage, persistent-correction, and
   serialized-integration components. Material interface drift receives a
   targeted delta review before the run is frozen. No interface drift was
   found; what is missing is the deployment composition for the review lane,
   the verdict/correction cycle, proposal publication and the integration
   driver. FINDING records the evidence. A separate bounded provider now owns
   that composition. Items 3 to 6 stay closed until it is accepted.
3. [pending freeze] Record exact base commit, the two successful Job contracts and fault Job C,
   profiles, dependency/test-change scope, injected review correction,
   injected failure, expected states, verification commands, artifact roots,
   and resource/time limits.
   Use PREPARATION-2026-09-08.md for the ready checklist and provider handoff
   inputs. Owner approved the third fault Job on 2026-09-08; freeze all three
   documents in one submission and review only material deltas from the previously
   approved demonstration contract. Automatic retry remains out of scope.
4. [pending clean run] Submit all three Jobs once and collect manager-owned status,
   timing, resource, workspace, output/log, checkpoint, review, refusal,
   integration, and operator-intervention evidence without manual lifecycle
   commands.
5. [pending verification] Prove concurrency, source immutability, workspace
   isolation/persistence, same-line correction, independent reviews,
   single-target integration, test-scope acceptance/refusal, and failure
   containment.
6. [pending independent assessment] Review the complete retained evidence and
   record whether the narrow standalone design is promising. File every
   non-blocking hardening concern as linked Work rather than expanding this
   slice.

If a component fails, stop the proof, return the defect to its owning Work, and
restart from a fresh submission after correction. Do not patch around it in the
demonstration harness.

Plan review runs ahead of component completion. Before handoff to
implementation, restore every component dependency required by the live proof;
the first restored gate releases the review claim. Then reroute the blocked
Work to implementation. Execution remains blocked until those providers are
accepted.
