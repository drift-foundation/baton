# Prepared settlement commands — owner selection pending

Owner E370683 selected preparation only. No command below that closes or stops anything was executed. Read-only pending was executed and retained in evidence/research-370686/pending.json. These are commands for the human owner, not authority for an agent to impersonate baton.slaw.

## Revalidate first (read-only)

```sh
/home/sl/baton-instances/useful-template-job-w366962/distro/baton-v12-stack disposition pending --authority-store /home/sl/baton-instances/useful-template-job-w366962/db/authority.sqlite3 --authority-uuid 6dcb60dce5cd485b8bf03c24bc4afc82 --work 6dcb60dc-W1 --participant baton.slaw
```

Check current assignment against the retained expected-assignment.json: authority6dcb60dce5cd485b8bf03c24bc4afc82, Work6dcb60dc-W1, participant baton.reviewer-w366962, generation2. The participant flag above reports capability; it does not perform an owner act. If assignment/capability differs, stop and prepare a newly reviewed command rather than altering the precondition blindly. Current evidence shows active review assignment, proposal integration-driver.proposal:4f11c905608c7b06eac7765d5ce65c817b72c2e252ea0fb760548846ce2bb819, and no verification/review/approval/integration receipts. Worker-local verification exit0 is not an authority verification receipt.

## Proposed honest closure — NOT selected or executed

If the owner selects non-satisfying closure and the readback still matches, the exact prepared command is:

```sh
/home/sl/baton-instances/useful-template-job-w366962/distro/baton-v12-stack disposition close --authority-store /home/sl/baton-instances/useful-template-job-w366962/db/authority.sqlite3 --authority-uuid 6dcb60dce5cd485b8bf03c24bc4afc82 --participant baton.slaw --work 6dcb60dc-W1 --operation-id w370560-nonsatisfying-close-370686 --outcome non-satisfying --rationale 'Implementation candidate retained; review assignment faulted under incompatible output declarations; no independent verdict or accepted useful Job outcome. Preserve all evidence and unresolved cleanup.' --expect-assignment /home/sl/src/baton/work/records/2026/10/finding-v12-documentation-review-startup-fault/evidence/research-370686/expected-assignment.json
```

Expected effect: authority records an honest non-satisfying ending with existing evidence retained; exact assignment precondition protects against changed ownership. The command may still refuse on current policy/state. It does not remove the container, settle all job-manager cleanup, approve the candidate or integrate it. Use the identical operation/operands for an uncertain-result retry; do not reuse this identity for a different outcome. Read pending again after any selected execution.

## Observe resource state (read-only)

```sh
docker inspect --format '{{json .State}}' a813a59f691c23022343cb25f3050df2c95386ae36b7dbab647fd4108d906ee6
/home/sl/baton-instances/useful-template-job-w366962/distro/baton-v12-stack status --instance /home/sl/baton-instances/useful-template-job-w366962/instance.json
/home/sl/baton-instances/useful-template-job-w366962/distro/baton-v12-stack attempt-diagnostics /home/sl/baton-instances/useful-template-job-w366962/state/status.json
```

Cleanup is not yet established. Installed top-level and manager command surfaces expose no standalone abandonment/reclamation command identified by this research. A Python library abandon_attempt exists, but invoking it directly with hand-built capabilities/stores is NOT a prepared supported operator procedure. This missing settlement surface is the operational finding; do not replace it with raw store manipulation or direct Docker removal.

## Supervisor stop — NOT selected, cleanup prerequisite unsatisfied

Only after later selection and fresh confirmation of actual cessation plus settled cleanup (or an explicitly selected owner exception):

```sh
/home/sl/baton-instances/useful-template-job-w366962/distro/baton-v12-stack stop --instance /home/sl/baton-instances/useful-template-job-w366962/instance.json
```

This stops supervisors, not containers. No current stop readiness is asserted. No container-removal command is proposed, no retry is prepared, and no new install is selected.
