# W121887 session forwarding — baton.tuner, claim121893

Authority: this record's FINDING/PLAN19:26Z allocation and T121887. Provider
acceptance is finding-v12-quiescence-gate-discharge/review-2026-09-08T15-10-00Z.md.
Revalidated the real AuthorityPort/session contract; add only the direct
_AuthoritySession.satisfy_gate operand-document forwarding, related wrapper
documentation and three additive controls in the two allocated files.

Question: does the wrapped AuthorityPort/session crossing preserve the exact
operands, successful answer/replay and original refusal while leaving existing
behavior untouched? Use the existing local Authority SessionCase fixture;
no daemon, assembled lifecycle, live deployment gate or inventory research.

Command from repository root: `PYTHONPATH=v12/python/src:v12/python python3
work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/finding-standalone-stage-composition/findings/finding-composed-one-job-proof/evidence/session-forwarding-121893/verify.py`.
Run only TheWorkerSessionForwardsGateDischarge plus an exact AST/hash audit.
Cumulative focused budget10s; save logs/timing even on failure. Reuse provider
evidence. Both baselines match the prior consumer's recorded hashes.

Operational finding: a guessed test_authority_port.py search path was absent;
the actual readable provider tests are test_offers.py/test_intake.py, and the
real local session fixture is tests/authority/test_session.py. No required
record was omitted. Reporting guidance reread and adopted.

Initial result: forwarding/refusal and real port replay pass. The third new
control incorrectly expected the gate kind instead of the evidence kind in
the Authority answer; its actual kind is runtime-absent. Correct only that
new expected value, preserving the original log/candidate. Run verify-final.py
with the same command/environment for that one corrected control and reuse
the two unchanged passes after an exact one-line comparison. No product
correction or existing assertion change is required.

Final result: all three controls pass across retained runs; combined focused
execution/audit0.514s within10s. The wrapper forwards the same operand object
and returns the same session answer. Through AuthorityPort, exact operands and
evidence reach the real local session; replay leaves one gate-evidence record.
Wrong-token and unreachable-runtime refusals preserve the original exception
and leave the gate closed. This proves the forwarding slice only.

final-verification.json binds sourceff383296 and testsaf445808 (full hashes
there); final-candidate-* and final-*.patch retain exact candidate bytes/diffs.
Removing the new method/test class and restoring only two related docstrings
reproduces every baseline AST node, preserving existing assertions. Whitespace
passes. The initial expected-kind error remains in verification.json and its
candidate snapshots; the final runner proves that single new assertion is the
only correction. Return baton.bug for independent acceptance. The consumer's
assembled proof/recovery glue and two-file reservation remain in force.
