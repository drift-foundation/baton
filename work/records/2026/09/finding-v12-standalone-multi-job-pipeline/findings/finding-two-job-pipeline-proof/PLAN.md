# Plan

1. [pending independent plan review] Review the demonstration shape, evidence
   matrix, operator-intervention budget, test-change scope, injected correction
   and failure, resource measurements, and pass/fail boundary. This stage
   approves only the proof plan; it cannot claim the demonstration passed.
2. [execution entry gate] Revalidate the approved plan against the accepted
   control-plane, source/workspace, concurrent-stage, persistent-correction,
   and serialized-integration components. Material interface drift receives a
   targeted delta review before the run is frozen.
3. [pending freeze] Record exact base commit, two bounded Job contracts,
   profiles, dependency/test-change scope, injected review correction,
   injected failure, expected states, verification commands, artifact roots,
   and resource/time limits.
4. [pending clean run] Submit both Jobs once and collect manager-owned status,
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
