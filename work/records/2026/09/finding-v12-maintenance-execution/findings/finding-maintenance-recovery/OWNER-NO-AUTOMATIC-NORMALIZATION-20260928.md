# Owner selection — no automatic permission repair or maintenance launch

Recorded by baton.prompt on 2026-09-28 UTC (September 27 owner local date).

After explanation of custody.normalize, Slawomir selected the shared-group job
contract: job-created files must have group ownership and permissions that allow
the required host access. Inaccessible files are a reported permission error;
preserve the workspace rather than automatically changing permissions. The owner
agreed to defer automatic permission repair and explicitly said not to start a
maintenance container at this point.

This supersedes W285465's currently selected automatic result-then-workspace
normalization and fresh maintenance-generation transition. Do not continue that
implementation as a v12 delivery gate. No automatic maintenance/custody helper
launch is selected for this completion/recovery path. Host-side chmod/chown,
privileged bypass, automatic deletion/reset, and fabricated normalization receipts
are not substitutes authorized by this decision.

Keep exact job-container shutdown, associated-writer cessation, exclusive
ownership, identity checks, durable honest outcome and recovery reconciliation.
Where access is insufficient, report the exact error and preserve affected files
and unresolved holds. Do not claim successful collection, retention or cleanup
without evidence. The ordinary shared-group-accessible case must progress without
requiring a normalization receipt or helper launch. Filesystem/engine I/O remains
outside DB transactions; initial preparation remains host-side as already selected.

Preserve historical implementation, accepted evidence and prior reviews. Historical
normalization requirements are superseded for this selected path, not silently
waived as passing tests. Adjust current FINDING/PLAN and focused acceptance to
prove the accessible positive path and inaccessible error/preservation path with
zero maintenance-container launches. Revalidate current failing tests against the
new outcome before changing expectations; retain genuine isolation, duplicate-effect
and false-success coverage. Automatic repair is deferred, not another release gate.

This does not close W285465 or its parent, change graph edges, authorize live
execution, or select a new general host cleanup/custody design. Existing rules for
future separately selected mutating operations do not require such operations to
run on this path. Routine bounded implementation and independent review continue.
