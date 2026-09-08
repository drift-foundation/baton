# Exact engine residue disposition proposal

Prepared by baton.tuner under W116016 claim116136, 2026-09-08T04:20:38Z.
Status: read-only reconciliation complete; NO disposal approved or executed.

## Observed

The current name-filter listings reproduce the diagnosis's same 32 full IDs:
31 baton-runtime.start containers and one baton-w6633-test container. Exact
inspection finds all32 exited; one runtime exits1, the other31 exit137.
Selected immutable runtime-label members are retained with id, name, image,
creation/start/finish times and state in evidence/current-containers.json.
No environment, logs, command, mount source, bearer or credential digest was
read. evidence/inspection-command.txt is the exact direct Docker command.

The old test tag resolves to
sha256:db9f397171153338ce068b46a7c9ab48c79b80d9f1ad1db4c149541a5eb8199b.
Its RepoTags are baton-w6633-test:7dc2c25ca26c,
baton-w81857-exchange:1 and baton-w81857-exchange:2. No image-ID removal is
proposed. Image creation epoch is normalized reproducibility metadata, not
proof of age. The current tag lookup alone does not enumerate every possible
new matching tag; final suite assertions must still run after disposition.

## Ownership and preservation

The31 runtimes name participant baton.claude, principal:baton.claude,
generation1, scope:deployment. Their authority-qualified Work groups are:

| Label Work | Count | Evidence / decision still needed |
| --- | ---: | --- |
| 36d545af-W71917 | 1 | Labelled standalone attempt; no live owner-state query supplied. |
| f6f92f75-W71917 | 1 | Labelled standalone attempt; no live owner-state query supplied. |
| 26050b09-W71917 | 1 | Exact attempt matches the preserved cross-authority collision witness below. |
| a3393700-W33937 | 1 | attempt-w33937-run1; prior review retains proposal separately. |
| 61984a06-W61984 | 1 | attempt-w61984-run6; manager ending unobserved here. |
| 214bb17b-W52821 | 1 | attempt-w52821-run5b; quiescent-finalization finding describes unresolved authority ending. |
| d00004d5-W51487 | 1 | attempt-w51487-run8; explicitly preserved recovery state. |
| 2bdb4a5d-W51487 | 1 | attempt-w51487-run7; exact ID matches prior inspection; explicitly preserved recovery state. |
| 43c55d4b-W6636 | 23 | Labelled local-conformance attempts; individual removal authority unestablished. |
| no v12 runtime labels | 1 | Exact W6633 suite name/image matches diagnosis, not an owner lifecycle receipt. |

Source records, all canonical in repository baton:

- work/records/2026/08/finding-interrupted-dogfood-attempt-strands-runtime-credential/evidence/run7-runtime-inspection.md:
  exact afed4c76... ID, stopped but not manager-proved absent. Its FINDING.md
  preserves run7 state; PROGRESS.md records deliberate run7/run8 preservation.
- work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/finding-source-workspace-mounts/findings/finding-cross-authority-attempt-id-collision/FINDING.md:
  exact 26050b09... authority and attempt-1851504c... match c4c12927... here;
  retained containers are negative controls and operator cleanup, not migration inputs.
- work/records/2026/09/finding-v12-quiescent-assignment-finalization/FINDING.md:
  run5b finalization was refused; its historical narrative says no container
  remained, while this exact labelled ID exists now. Do not infer terminal
  manager state from either statement; obtain supported current owner evidence.
- work/records/2026/08/finding-v12-decline-bearer-contract-conflict/review-2026-09-02T13-54-46Z.md
  identifies the run1 retained proposal, separate from container disposal.

These v12 authority UUIDs differ from the canonical v11 coordination authority
2b077949c86e8bef24304f59c28ec398. Numeric Work suffixes and the participant
label do not establish a current claim or manager terminal state. No live
v12 ownership observation endpoint/store binding was supplied with this
assignment. That is an operational evidence gap, not permission to open
SQLite or infer abandonment. Exit137 does not establish its cause.

## Proposed selected decision

Retain every resource now. Ask Slawomir, after independent assessment, to
select exact IDs from evidence/proposed-removal-commands.txt for disposal and
to authorize the single old test tag removal. The list enumerates all32
candidates individually; it is not blanket approval and is not executable by
this claim. For run7/run8 and the collision witness, any selected disposal
must explicitly supersede physical-container preservation while keeping the
existing dossiers and host custody/proposals. Unknown live owner state must
be reconciled through a supported owner surface or explicitly dispositioned
by the owner. Removing a container alone does not close a manager attempt,
remove credentials, release a lane or accept output.

Before EACH later authorized removal, re-inspect the exact ID and verify the
full retained identity/labels/image/created/started/finished/state. Any drift,
running state, ambiguity, missing approval or retained-evidence requirement
stops the act. Use ordinary docker rm with no force and no volume removal.
After each approved act obtain direct exact-ID absence evidence. Immediately
before tag removal recheck image ID and all3 aliases; remove only the named
tag, then inspect both shared aliases and require the original image ID.
Never prune, expand by prefix, remove shared image IDs, remove files/volumes,
read credentials, or use raw store access.

Original checks9–12 remain unresolved. Run no daemon suite until the owner
has dispositioned every matching residue or established a separate authorized
verification engine. Later targeted lifecycle checks need a recorded scope,
resource ownership and budget; final ordinary whole suite remains W115981.
