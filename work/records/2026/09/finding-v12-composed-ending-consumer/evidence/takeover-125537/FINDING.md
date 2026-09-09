# W122060: successful integration result never reaches the completion consumer

2026-09-09, baton.tuner, claim125537. Bounded fixture takeover under
`../../review-2026-09-09T05-47-14Z.md` and the owning FINDING/PLAN. This is an
observed source blocker returned for independent review, not authority to edit
production in the current claim.

**Confirmed:** one submitted Job and retained line now traverse implementation,
changes-requested review, correction, accepted second review, and an actual
integration worker. The public delivery reader returns `answered` with result
`integrated`; actual verification `python3 harness.py` exits0 and the disposable
target contains `print('the accepted correction')`. This completes the fixture
provisioning missing from the previous port-only assertion: stable post-bootstrap
policy pin, public target activation, actual instruction digest, descriptor-based
Git object runner, target base mode, scratch root and adapter credential/home.

**Confirmed blocker:** after the worker result, three ordinary sweeps each
refresh integration as `quiescent` but attempt `dispatch`, which refuses
`precondition`: the attempt has no exchange delivery. The integration consumer's
`run` call count across those sweeps is0. The integration stage stays `starting`,
its coordinator entry stays `leased`, and the same Work retains its integration
handler. See `probe.json` and `verification-10.log`. This is not a refusal from
the completed workload and no provider/helper was called to advance the manager.

**Source explanation:** `v12/python/tools/stage_execution.py`,
`StageExecution.__getattr__` delegates `dispatch` to pooled worker operations;
only `launch` and `conclude` reach the integration driver. The latter explicitly
documents that integration has no exchange. Meanwhile
`v12/python/src/baton_v12/job_manager/projection.py` maps `starting` to dispatch,
and `manager.py` calls that operation. The ordinary scheduler never reaches the
re-entrant integration completion composition after launch.

**Proposed next bounded allocation:** correct integration-specific ordinary
scheduling at `v12/python/tools/stage_execution.py` (its dispatch/observation
seam), with this exact positive control. Independent review should determine
whether a job-manager projection change is necessary before authorizing any
additional path. Preserve the generic exchange protocol and all negative tests.
Completion/Authority receipt, lease release, final stage projection and Work
handoff remain unproved downstream of this first blocker; no claim is made
that one seam correction alone establishes them all.

**Candidate and validation:** `candidate-test_stage_execution.py`,
`candidate.patch`, and `final.json` bind the sole added
`OrdinaryTerminalLifecycle` class. All existing stage-test bytes/AST and the
three other reserved files/modes match intake. The positive completion selector
still FAILS at the scheduling refusal (`verification-9.log`), deliberately
retaining its success expectation rather than blessing the defect. The final
diagnostic succeeds as an observation, not as lifecycle acceptance. Ten
iterative test/probe processes consumed8.770261242985725s of the cumulative20s
budget; all commands, failed fixture iterations and process limits are in
`verification.json` and `EXECUTION.md`. No full suite or recovery run followed.

**Still owed:** ordinary terminal completion, then the actual reconstructed
manager cut after committed handoff before local acknowledgement. The owner
clarification M124896 permits abandoning uncommitted scratch and replaying
from the committed checkpoint; this finding adds no recovery requirements.
W119114 retains the separately assigned full lifecycle/custody acceptance.
