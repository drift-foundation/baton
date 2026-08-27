# Plan

1. Revalidate W16821's reviewed authority projection and W16793's manager
   inventory against the current tree.
2. Pin one trusted-manager authorization-context document that keeps endpoint
   assignment, principal, effective scope, role, provenance and policy
   generation distinct.
3. Version the manager control-store rows and port answer checks; bind context
   atomically at claim activation and into replay signatures.
4. Extend trusted runtime labels/reconciliation and execution session evidence
   with principal-global identity without changing consent posture.
5. Prove no worker-supplied operand chooses or widens the context and decide,
   with a recorded compatibility analysis, whether any frozen wire schema needs
   a new negotiated version.
6. Add positive, negative, restart, replay, multi-endpoint and cancellation
   tests, then return for independent review before M2 conformance.

