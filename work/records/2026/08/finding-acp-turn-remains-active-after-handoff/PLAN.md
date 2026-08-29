# Plan

1. [done] Preserve the W29400/W38956 sequence, runtime projection, process
   inventory, pending poke, and final ACP log boundary.
2. [done] Revalidate the deployed process against W28681. The live Aug 27
   `dd1dc3e` bridge has no prompt deadline and its active config has no
   `turnTimeoutMs`; current source already bounds the exact never-settling
   prompt shape, tears down its process domain, reports correlated failure,
   retains the readiness key, and polls again.
3. [next, implementation] Add an explicit deployment-selected
   `turnTimeoutMs` to every repository ACP lifecycle template and add a gate
   that keeps those templates aligned with the bridge's mandatory schema. Do
   not infer a repository-wide duration from the pc.code successor's one-hour
   choice.
4. [next, approver/operator] Build and install a current bridge release, render
   the `baton.claude` config with the approved duration, and install the
   reviewed PID-domain launcher and preflight through the documented
   fail-closed cutover. The old config cannot start the current bridge and the
   old launcher cannot satisfy W28681, so replacing only the process is not a
   valid recovery.
5. [next, operator verification] Run the exact service-context process-domain
   preflight before activation; positively observe the old PID/domain absent;
   then start the replacement and verify its configured runtime facts.
6. [next, verification] In an isolated bridge fixture, prove one
   never-settling injected turn reaches the configured correlated failure and
   preserves its readiness key. In the live lane, use a normal bounded smoke
   to prove W38956 or the canonical next offer is delivered once without a
   duplicate claim; do not deliberately wedge the production participant.
   Reuse W28681's focused matrix and do not add a handoff-derived deadline.

The former reproduction/new-watchdog steps are superseded by W28681's existing
coverage. This follow-up owns the missing template and deployment crossing.
Keep the v12 useful-dogfood milestone ahead of application changes, but its
implementation lane cannot recover until this old bridge is operationally
replaced.
