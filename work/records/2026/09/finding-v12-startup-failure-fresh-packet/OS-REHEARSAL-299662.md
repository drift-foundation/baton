# Literal OS rehearsal — tuner claim299662

Authority owner291841, reviewer handoff299659 and review21:55:22; events read
through299662, discussionT257627 unchanged through292130. Only selected
single-implementation-proof/test_baseline_bindings.py changed. No fifth product
path, shared Git mutation, live engine/provider, image build or deployment.

## Boundary and evidence

The generated commands.json start argv and environment run in an OS subprocess,
without reconstructing argv or injecting baseline.main/compose/supervise. A
repository-shaped copied runtime carries baton_v12/tools, and start validates
its bytes/import origins before opening disposable stores. PATH contains only
an explicit fake Docker executable plus Git/Python for actual local fixture
version control and task verification. Unknown engine commands fail closed;
there is no real engine fallback. Credential registry contains a fake bearer.

The fake engine parses actual create labels/mounts, permits exactly one creation
and activation, and starts a separate local worker process at start. It maps the
selected mounts onto the real worker/ClaudeAgent module constants (simulated OCI
namespace), uses the real emitted launch/exchange documents, and substitutes only
the provider subprocess's edit result. Git/proposal/verification run for real in
the disposable fixture. No self-approved receipt or direct store-state fabrication.
The source-profile import follows the image's top-level source_profiles layout.

Engine inspection observes actual local PID exit (/proc absent or zombie), not
just a written completion marker. Stop signals the exact worker process group and
waits for its exit before reporting quiescence. An interrupted worker's exit code
is left unknown, rather than invented. Test teardown kills only its own still-live
worker, after checking its command identity; that cleanup is not supervisor proof.
This Linux local-process simulation does not prove OCI UID/GID, image or provider
behavior. It does not execute dogfood_entry/container boot.

Immutable JSON captures in evidence/claim299662-final/{positive,interrupt,deadline,
inaccessible}.json retain emitted packet/commands, supervisor exit/stderr, complete
outcome/status, engine argv, worker log/completion or process-cessation observation,
and output mode before fixture teardown. Earlier evidence/claim299662 remains.
All underlying test roots are fresh disposable fixtures and are removed by fixture
teardown; captured locators describe those historical roots, not currently retained
live instances. Product preservation was asserted before teardown. Existing
consumed instances were never touched.

## Four distinct fresh runs

- Positive: unmodified300-total/60-cleanup packet, exit0, one Job, one episode,
  one admitted attempt, one provider invocation and one proposal correlated to
  that attempt; generated status reports that exact Job/attempt. No context
  invocation in the real ControlStore, no context evidence modes, no helper/run
  command, no second task, no outstanding cleanup.
- Interrupt: wait for worker to enter provider, then SIGINT the actual supervisor.
  Exit130, retained interrupted outcome, exact active worker stopped. No result
  exists, so outstanding_cleanup names that same attempt and state stays held.
  This is cessation plus an honest unresolved result/cleanup hold, not clean success.
- Deadline: active worker waits in provider. Test packet uses12 total/5 reserved
  cleanup seconds (7 serving), real monotonic time, no mocked clock. Supervisor
  reaches overall-bound-exceeded and stops the worker; exit1/held with the exact
  unresolved attempt. This tests cooperative cutoff, not production240 elapsed
  seconds, a hard wall-clock guarantee, or arbitrary blocking-call interruption.
- Inaccessible: real worker completes, fixture removes output-root permissions
  before collection. Supervisor exits1/held; mode000/root preserved, no helper.
  Generated status carries the actual PermissionError and path/operation. Generic
  outcome alone lacks that detail, so both surfaces are required for readback.
  Fixture restores mode only after assertions/capture for its own teardown.

All four use distinct run/Job/attempt identities and separate stores/roots. Each
asserts one create/start, one Job/stage/episode and no context invocation. No retry
or automatic recovery of a hold was exercised or claimed.

## Iterations and changed expectations

Initial worker fixture omitted top-level source_profiles: module import failed,
supervisor test timed out35.089s. The worker had exited; no real engine existed.
Corrected import layout: positive1PASS4.334s. First four-mode run:1PASS/3FAIL in
39.211s. Two assertions wrongly demanded clean completion after killing a provider;
accepted scope requires cessation OR an honest unresolved hold. Replaced these
new assertions with exact outstanding-attempt/no-committed-cleanup/quiescent
cancellation checks, preserving genuine failure coverage. Access assertion looked
only in outcome; literal status is the surface carrying PermissionError. Focused
access check1PASS13.215s. Four-mode retained run4PASS40.479s. Final stronger exact
Job/attempt/proposal/episode and ControlStore context checks: entire bindings
module40PASS43.391s. ResourceWarning treated as error in test runner; no live suites.

git diff --check passes. Episode measured unittest duration175.719s; historical
author9.246s =>184.965s. Historical reviewer0.643s plus latest2.983s =>3.626s,
separately attributed. No cumulative budget gate or fabricated wall-time bound.
