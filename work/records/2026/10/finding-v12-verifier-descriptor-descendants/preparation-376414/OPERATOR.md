# W325695 bounded image/kernel/capacity proof — preparation376414

Owner E376411 selects preparation only. Source milestone accepted at manifest28abb7c366bd24c266db548b9046d64fca9bcc0e6aa061066319330d26eaa2cb and human checkpoint ef703336b890a4ff08503bc4f293fbeb559f478d (all ten path bytes independently checked). No image build, engine operation, provider call or historical preparation325908 execution has occurred. This NEW packet reuses the historically reviewed runner design with new pinned inputs/payload and mocked checks; old packet remains untouched.

## Exact input and image identities

SOURCE.json enumerates all ten accepted source hashes, copied to accepted-source/. BUILD-INPUTS.json enumerates the exact Dockerfile and complete COPY closure in context/. This build never reads the evolving shared checkout. PACKET-PINS.json binds scripts, both manifests and every frozen source/context file. CHECKPOINT.json verifies the human commit as secondary provenance, not the primary dossier locator.

The candidate image digest is deliberately UNKNOWN until build. The Dockerfile base tag, apt repositories and provider package postinstall remain externally moving inputs; do not claim reproducible image identity from the source hash. Build creates an exact image.id and receipt; its immutable local sha256 image ID, never a tag, is the run operand. Payload independently hashes every COPY destination against BUILD-INPUTS-derived constants before probing. Dockerfile scaffolding and real ownership/modes are checked inside that exact image. No registry publication or image promotion is selected.

## Two separate owner selections and commands

Run from repository root. Read-only packet integrity check (no engine):

```sh
python3 -B work/records/2026/10/finding-v12-verifier-descriptor-descendants/preparation-376414/packet.py check
```

**Selection A: one candidate image build**, after owner records acceptance of this exact packet. This accesses build dependencies over the network; no provider/model execution or credentials. No installation/deployment change. Exact command:

```sh
python3 -B work/records/2026/10/finding-v12-verifier-descriptor-descendants/preparation-376414/packet.py build --owner-selected
```

One build invocation,1800s local CLI timeout. Request2GiB/1CPU through docker build flags; these are requested build-backend limits, not measured enforcement or a guarantee about unrelated daemon activity. Unsupported flags/backend behavior is a failed preparation, not permission to remove limits and retry. BUILD-RECEIPT is exclusive; existing receipt refuses rerun. Build timeout kills/reaps the local CLI, but daemon-side completion may remain uncertain: retain receipt/log/image ID if available and require exact owner reconciliation, not automatic retry/prune/image deletion. Build artifacts stay for inspection. No container is started by this command.

After successful build, form the candidate selection without running it:

```sh
python3 -B work/records/2026/10/finding-v12-verifier-descriptor-descendants/preparation-376414/packet.py select
```

This reads only the matching successful build receipt, exclusively writes SELECTION.json, and prints its SHA256 and fully concrete run command. **Selection B:** owner must select THAT exact image ID, selection document SHA256 and proposed65532:65532 diagnostic identity before the printed command is run. The explicit identity is a bounded diagnostic selection matching the image nonroot identity; it is not an inferred host UID/GID or claimed production workspace-group provisioning. SELECTION.template.json shows the exact contract now but is deliberately invalid until image identity exists. No guessed placeholder may be executed. The printed command has this shape:

```text
python3 -B <canonical preparation376414 path>/packet.py run --owner-selected --selection-sha256 <exact printed digest>
```

The literal digest cannot be supplied truthfully before the build. This two-stage selection is required by the presently unbuilt image, not a request to repeat approval already given. Runner additionally validates selection hashes before its first engine call and uses --pull never.

## Proposed execution boundary

One container, reserved name w325695-proof-376414, explicit65532:65532, read-only root, network none, cap-drop ALL, no-new-privileges,64 processes,2GiB memory,1CPU. No bind mounts, credentials, socket, Authority/Job/control store or repository access. The entrypoint is /usr/bin/python3 with pinned inert payload; never dogfood_entry/provider. Provider installation occurs only as ordinary image recipe content during build and is not invoked by the proof.

Diagnostic tmpfs partition uses accepted selected topology: /tmp32MiB,/dev/shm16MiB, private HOME4MiB/TMPDIR16MiB/cache4MiB/pycache8MiB;80MiB aggregate, all noexec/nosuid/nodev. The separate product16MiB legacy-log decoy is intentionally omitted because this diagnostic has no log channel; product total96MiB accounting remains source evidence, not measured full-runtime fit. Real capacity writes are bounded to one root limit plus1MiB attempt, one root at a time, with files removed after ENOSPC. No fallback or automatic mount growth.

Internal120s deadline,80s work admission,40s cleanup reserve;20s receipt window. Per-call limits are bounded by remaining phase time. No retry. ENGINE-RECEIPT is reserved exclusively and fsynced before engine effects. Intent/name persists before create; exact ID persists before later operations. Lost create reply reconciles only exact name with image/label/user identity. Ambiguous inspection is uncertainty, never absence or permission to delete another object. Remove only acquired exact ID, then independent exact absence inspection, including after removal exceptions. Any uncertain result retains receipt/identity and blocks re-execution. External killing/unavailable receipt storage cannot be claimed crash-safe; owner recovery remains separate.

## Acceptance and honest limits

All must hold: pinned image-file bytes; actual immutable ancestor ownership/modes; product _selected_layout and _pinned_environment/_revalidated_directories accept actual kernel mount facts; all four roots resist rename/remove/symlink substitution and keep identities; ordinary child/grandchild writes and nested image validator succeed; each private root reports genuine ENOSPC within its selected capacity and cleans its probe; detached descendant exists before teardown; exact container absence after cleanup. Runner requires image_bytes/product_mount_checks/capacity_enospc as well as legacy mount/descendant/nested flags. Only success plus no errors plus successful exact cleanup/absence passes.

The payload creates a diagnostic selection in container /tmp from the pinned image marker and explicit selected identity. Its profile/policy/adapter digests are labelled inert fixture identities. This is real image/kernel mechanism evidence through product validators, not proof of installed manager delivery, a Job/provider run, task/3, or production context reuse. Installed composition was separately source-tested. Existing candidate/input preservation and safe-output deterministic evidence is not relabelled as kernel proof. Actual full-command verification workload capacity fit and broad performance are NOT established merely by ENOSPC bounds; report the remaining acceptance gap honestly and retain W325695 open until owner evaluates joined evidence. W321776 acceptance is not silently released.

## Verification performed in preparation

Four scripts AST-parse. New test_engine_proof.py passes five methods,17 mocked execution scenarios and six invalid selections, with fake engine and clock; includes lost create reply, malformed/unknown inspection, cleanup failure, deadlines, no retry and missing-capacity receipt rejection. RUNNER-CHECK.json records measured duration. Real payload not executed (it requires selected engine/kernel mounts); no actual image bytes, mount behavior or capacity outcome claimed. No product or Git mutation.
