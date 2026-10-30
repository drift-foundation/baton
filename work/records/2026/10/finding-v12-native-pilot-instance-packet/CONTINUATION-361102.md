# W325959 — manager retry continuation, 2026-10-24

Prepared by baton.rvpc under claim361102. These commands were NOT executed.
This supersedes the old helper's retry instructions, not the retained evidence.

## Current checkpoint and next selected outcome

W358969 owner acceptance E361092 closes the implementation dependency with this
explicit boundary: “Exact-byte integration and human Git checkpoint remain
pending; no deployment or live retry authorized.” W325959 remains open for
the pilot; W321608 consumes its eventual acceptance.

The next bounded outcome is integration of the independently accepted candidate,
followed by Slawomir's Git checkpoint. The candidate is
`../finding-v12-manager-fresh-attempt-admission/findings/finding-host-exclusion-lifetime/candidate-360912/`.
Its MANIFEST.json SHA256 is
`164546f94cc88854271d623a149835e1283e76a4f8d9049bdc68a402656ab13f`.
The joined review is
`../finding-v12-manager-fresh-attempt-admission/review-2026-10-24T01-46-13Z.md`.
Recheck every target's type, owner-write permission, base bytes, overlap and
candidate digest before import. Import only the 15 manifest members, preserving
normal target modes; no redesign, other edits, staging or Git mutation by an
agent. Suggested human commit: `feat(v12): add manager-owned fresh-attempt admission`.

Read-only verification this turn: all 15 candidate member digests match;
all 12 existing target files match canonical_base; all three new targets remain
absent. This is evidence of pending integration, not an import receipt.

## Deployment prerequisite — unresolved, not an upgrade recipe

After integration and human checkpoint, select and prepare a bounded build and
deployment update for the retained instance. Pin its build identity and bundle
digest and verify the supported update preserves authority, stores, failed Job,
workers and existing bindings. No reviewed new bundle or retained-instance
update procedure is supplied by W358969. The old installed build identity is
not evidence that it contains fresh-attempt. Do not rerun the old fresh-instance
bootstrap or copy candidate Python into an installed frozen bundle.

The downstream command below is concrete interface guidance for that updated
installation, not authorization to deploy or execute it now. Keep deployment
preparation distinct from the later live-provider question: can the retained
instance run the bounded retry with actual refreshed authentication? Deterministic
proof covers admission, not current credentials or a real provider response.

## Retry operands after deployment and separate execution selection

Use the retained third instance. The authority below is its previously recorded
identity and must agree with the updated installation's retained identity.

```sh
D=/home/sl/baton-instances/native-coordination-pilot-w321608-3
C="$D/distro/baton-v12-stack"
A=5a8fa4b4275b4f7fa32efafc2c48f546
"$C" identity
"$C" manager --store "$D/db/jobs.sqlite3" --incarnation w325959-owner-retry-manager-1 --authority-uuid "$A" fresh-attempt --help
```

Read-only interface checks are insufficient build provenance by themselves.
After the deployment prerequisite and explicit retry selection, the mutation is:

```sh
"$C" manager --store "$D/db/jobs.sqlite3" --incarnation w325959-owner-retry-manager-1 --authority-uuid "$A" fresh-attempt --prior-job quickstart-c --control "$D/db/control.sqlite3" --authority "$D/db/authority.sqlite3" --instance "$D"
```

`--instance` here is the state root, not instance.json. Omitted identity overrides
derive `quickstart-c-retry-2` and its submission; the prior open Work
`5a8fa4b4-W1` is reused. Preserve the emitted receipt. There is no second `submit`.
The operation performs admission and additive binding itself. An exact retry of
this invocation is the replay/resume path; preserve its incarnation if interrupted
while incomplete. Do not invent new IDs or switch incarnation to bypass refusal.
Unknown cessation, active ownership, unavailable workers, changed identities or
incompatible evidence require a bounded diagnosis, not store edits or the old helper.

Serving is a further live operation, only after successful admission and explicit
selection of that execution:

```sh
"$C" start --instance "$D/instance.json"
"$C" monitor --instance "$D/instance.json" --interval 5
"$C" attempt-diagnostics "$D/state/status.json"
"$C" stop --instance "$D/instance.json"
```

Use start/monitor/diagnostics/stop as separate operator steps, not an unattended
script. A published snapshot may be stale; it does not replace host admission
evidence or current cleanup proof. Preserve the 3600s provider and 900s verification
per-invocation limits, both implementation/review roles and human acceptance.
Admission success is not provider success, independent review or pilot acceptance.

## Evidence and acceptance limits

The accepted exact candidate has 159 passing independent focused cases plus the
joined real-CLI disposable-store/real-binding probe (operations status simulated).
See the joined review and its evidence/review-360999. No suite rerun was needed
for this documentation-only consumption. Shell blocks here were syntax checked.
No live store, process or credential was inspected; no live admission, deployment,
runtime or Git mutation occurred. Historical OAuth refresh, reboot and destroyed
runtime observations are not fresh readiness evidence.

Decomposition: implementation and independent joined acceptance are complete.
Integration/human checkpoint, deployment preparation and selected pilot execution
are distinct remaining outcomes; none may be treated as silently completed by a
closed dependency. This preparation pass creates no parallel executor allocation.
Reviewer owns this document, FINDING/PLAN and its new review only; immutable
candidates and author PROGRESS remain untouched. Owner chooses the next operation.
