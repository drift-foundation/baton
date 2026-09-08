# Restored-only constructor correction — W106673

Prepared by baton.tuner, claim 110596, responding to
review-2026-09-07T13-42-14Z.md. Independent review and separate exact owner
execution approval through baton.ops remain required. No live run occurred.

The earlier fresh constructor reused its arm-name parameter for the private
work/home/cache loop, then refused because the arm had become cache. This new
controller renames that loop variable to subdirectory and points to a new
manifest. Those are its only differences from live_controller_restore.py.
The supervisor remains the exact earlier live_supervisor_restore.py bytes.
All earlier frozen inputs and reviews remain unchanged.

This corrects the reproduced pre-container defect. It does not identify the
unknown cause of the earlier live restored-first failure, withdraw accepted
retained-session proof or recover the disclosed older unbound reviewer-log loss.

## Exact candidate and invocation

Candidate: evidence/live_controller_restore_constructor.py.
Manifest: evidence/restore-constructor-manifest.json.
Supporting evidence uses exclusive claim-110596 paths.

Offline checks:

```sh
/usr/bin/python3 -B /home/sl/src/baton/work/records/2026/09/finding-v12-live-session-workspace-detach/evidence/live_controller_restore_constructor.py --audit
/usr/bin/python3 -B /home/sl/src/baton/work/records/2026/09/finding-v12-live-session-workspace-detach/evidence/test_restore_constructor.py
```

Proposed single operator invocation, only after independent review and separate
exact execution approval:

```sh
sudo -- /usr/bin/env -i PATH=/usr/bin:/bin /usr/bin/python3 -B /home/sl/src/baton/work/records/2026/09/finding-v12-live-session-workspace-detach/evidence/live_controller_restore_constructor.py --run
```

This supersedes the controller/manifest/invocation selection in RESTORED-ONLY.md
for a future run. Its experiment, runtime identity, limits, authority, evidence,
acceptance and teardown requirements otherwise remain applicable unchanged.

There are exactly two proposed containers and at most one user turn each, 180s
per turn, with 420s work plus 180s ending within 600s runtime. Result/export
flushing follows ending. Nominal USD2 CLI settings are not a verified hard
billing cap. The fixed image, CLI 2.1.247, model, existing private credential
delivery, ordinary bridge egress, receipt gates and normal teardown are unchanged.
No retained arm or protected failed-session reuse is exposed.

Fresh initial work must pass confirmed shutdown and fixed-byte verification
before creating the replacement. Restoration must preserve the actual session
and workspace in a different process, pass the remembered-token correction
after ordinary revocation, and confirm final shutdown. Successful output is
restored-only-passed with separate restoration_timings and matched_comparison=false.
The accepted retained observation is separate evidence; no speedup comparison or
production adoption is established. Private files/stopped containers remain;
only existing normal credential teardown removes sensitive delivery after
confirmed ending. Export remains the same closed non-secret evidence set.

## Regression evidence

Twenty-three offline checks pass: all 21 preceding assertions unchanged against
the new controller, plus two tests through the actual constructor and base
constructor. Only chown is mocked for successful construction; real temporary
directories, permissions, UUID generation and workspace identity are exercised.
Docker, subprocess and runtime credential APIs are forbidden-call spies, and
credentials receive no calls. Fresh and replacement fixtures retain their exact
arm labels; work/home/cache remain private directories; replacement reuses the
same session UUID, directory and workspace without rewriting private content.
Unsupported arm labels still refuse before any external/credential operation.

The new regression also fails against the frozen old controller with
diagnostic-arm-invalid, demonstrating coverage of the reported defect. The
baseline log retains that expected failure separately from the passing candidate
log. Neither constructor checks nor simulated orchestration prove live restoration.
The narrow source patch and preservation audit bind all prior 116 inputs plus
the earlier manifest; no earlier test assertion or frozen evidence is edited.
