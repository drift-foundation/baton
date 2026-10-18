
## Appended 2026-10-18, claim 325259 — two claims from this directory withdrawn

Review 2026-10-18T18-17-05Z accepted this directory's assertion and
live-cancellation corrections and refused its conclusions. The nine files here
are unedited; `../matrix-325259/` carries the completed run.

1. **"This fixture exposes no engine-absence seam."** Withdrawn. It exposes it
   at the `engine_run` boundary: `ComposedOneJobCase.quiescing` already models
   stop and positive, exactly-identified absence, and the reason I could not
   reach it is that `serving()` installs a NEW engine on every call, so my
   "restart" was reconciling against an engine that had never heard of the
   container the first one started. Composing with
   `stage_execution.operations_from` and the same engine object drives both the
   lost-reply restart and the absence vector — scenarios 1 and 2 of the new
   run, 30 checks between them.

2. **"Nothing creates an eligible diagnostic assignment or names a diagnostic
   principal, and that is a bounded product gap."** Withdrawn. It was inferred
   from members the status projection does not carry, which the review
   correctly refused as a basis. Asked of the Authority's own route, handler,
   claim, label and creation surfaces, the path exists: a diagnostic handler is
   named for the Work's route and the diagnostic participant claims it, giving
   an assignment that names that participant and its principal — or a dedicated
   diagnostic Work is created on its own route and claimed by its own owner.
   Scenario 5 drives both, 21 checks. What remains true is narrower and is
   deployment policy rather than a missing operation: nothing routes an
   exceptional stage automatically, so an operator must notice it.

3. **The self-check here accepted ANY failure**, including a setup or cleanup
   error. The new harness requires the intended `CheckFailed` by name, with no
   setup traceback and no cleanup failure, and the first corrected run proved
   it: invoked from the wrong directory, every scenario failed in setup and the
   harness refused the run instead of reporting itself sound.

4. **"No Git command"**, repeated in this directory's prose, was imprecise: the
   imported fixture's own `vcs` helper runs version control against its
   disposable temporary source tree. Nothing mutates this repository's history,
   index or working tree, which is the accurate statement.
