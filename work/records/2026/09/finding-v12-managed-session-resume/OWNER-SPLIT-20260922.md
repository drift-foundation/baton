# Owner decision — separate Jobs, not a larger staged Job

2026-09-22, recorded by baton.prompt from the owner's explicit correction:
"we need to split the job, then run these separately".

The immediate execution sequence is now:

1. W239528, one implementation container through valid proposal, stopped
   execution and positive cleanup. Dossier:
   ../finding-v12-single-implementation-proof/.
2. W239533, independent review of that retained proposal in its own run,
   valid attributed verdict, stop and positive cleanup. Dossier:
   ../finding-v12-independent-review-proof/.
3. W236087, the remaining restored-context correction proof, after the two
   prerequisites are independently accepted. Preserve actual open context and
   review provenance; do not fabricate restore inputs or weaken acceptance.

This supersedes continuing to expand W236087 into one combined baseline,
review and resume execution. Historical failed runs and accepted component
proofs remain intact; none of the Jobs is closed by this decision.

Claude currently holds W236087 (claim239485, episode239483 observed). Preserve
its current changes/evidence and return a handoff before reassigning execution
or applying a dependency to that active claim. No force-release, overlapping
edits or live run follows this split. Prompt creates the two new dossiers and
this standalone decision; Claude retains its existing implementation files and
FINDING/PLAN/PROGRESS until the explicit handoff. The handler must append this
decision to FINDING and make PLAN identify only remaining resume scope before
further implementation. The new prerequisite dossiers already record the ruling.

After release, W236087 waits on W239533, which waits on W239528. Route only the
baseline for execution first. Outstanding old-runtime cleanup and the consumed
grant remain preserved facts; splitting does not authorize destructive recovery.
