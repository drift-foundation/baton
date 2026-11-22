# Minimal prerequisite: immutable heavy native control profile

M385644 / E385646 preparation only. Owner M385638 already selected provider7200s, stage9000s, Job21600s including queue, unchanged verification/correction/retry/shutdown policy. This is product registration plus qualification, not operator configuration available in the current binary. No further numerical-policy decision is requested.

## Separately deliverable outcome and ownership

Propose one small prerequisite Work: register and qualify `native-handoff-heavy/1` for ordinary `/3` implementation/review Jobs. Coordinator assigns it separately and records the prerequisite edge before releasing W385623 execution. No Work/edge created here. Serial owner for profile code and associated tests; coordinate overlap with W385635 and W385623, neither of which owns this change implicitly. Independent review accepts the exact profile delta/runtime provenance before use. No feature correction, retained import, general profile editor, new launcher, runtime profile migration or timeout reset belongs here.

Definition bytes: PROFILE-DEFINITION.json SHA256 `25b45962a2c785ceff8f0ebb53bc3778e29c54de3bb10e3a75027b800e1769cb`. This is a proposed stable implementation name and exact approved-policy record, not an installed configuration schema. The product must retain its own existing resolved-document identity conventions; do not pretend this file SHA is an existing admission wire field.

Minimum code seam: `job_manager/job_control.py` adds a NEW PROFILES entry with correction_rounds0, stage_seconds9000, job_seconds21600, provider_turn_seconds7200, verification_command_seconds900, and a matching CONTINUATIONS entry1. One resolved clarification continuation preserves native-handoff/1 behavior; it is not an automatic correction/retry. Existing dictionary indexing in evaluation/refuse_continuation and stage_execution._continued makes the continuation entry necessary. Export a constant if appropriate; no renaming existing identities. Preserve old profile and resolved-document bytes, stage1-analysis/1 and stage1-verification-review/1 definitions, execution_limits generations and all old admitted clocks. Pin the owner decision in applicable DESIGN LIM-5/profile documentation as part of the separate reviewed change, without widening other policies.

No new CLI is needed: `manager create --control-profile native-handoff-heavy/1 --provider-turn-seconds 7200` already has the required shape. `job_control.owned_control` currently refuses this unknown profile; `agreeing` requires the resolved provider ceiling to match it. Selecting the new profile without7200 still resolves default3600 and must refuse. Selecting native-handoff/1 with7200 must continue refusing. Do not relax agreeing or mutate defaults to make the command pass. Do not add `--verification-command-seconds900`: that override also changes integration/host verification boundaries, while leaving it absent preserves their current defaults and ordinary verification900.

Existing execution_limits accepts7200 (range1..86400); per-Job limit propagation and worker `_resolved_bound` already exist. Pool composition's default3600 metadata is not proof the Job override is enforced: prove admitted-limit propagation through the connected dispatch/worker boundary. Alter another seam only if focused evidence identifies a real enforcement gap; do not rewrite profile/adapter policy speculatively.

## Focused deterministic acceptance, then independent check

Use ordinary local focused fixtures, fake clocks and provider runners; no real7200s wait, live provider, Docker campaign or full suite.

- New profile resolves exact approved values and one continuation. Old profile/resolved bytes and old persisted admissions are unchanged across replay/reopen.
- Real create/template/submit path accepts new profile plus7200, preserves ordinary900 and other verification defaults, records21600 Job clock including queue,9000 stage clock from admission and invocation7200 from actual start. CLI output and canonical readback agree.
- Unknown profile, mismatched override, missing override and tampered replay refuse without side effects. New binary opening old admissions does not rewrite deadlines; older binary cannot silently admit the new profile.
- Fake-clock expiry at Job/stage boundaries, uncertain clocks, cancellation and restart retain current guarantees. One resolved handoff continuation remains allowed, second refused, no correction round granted and no reset clocks.
- Connected stage-execution/task-token/worker fake-runner probe receives and reports7200 in both implementation and review,900 for ordinary verification; preserve shutdown ceiling and actual-start attribution. Selected source/runtime image compatibility is checked, not assumed from constants.
- Build the accepted prerequisite runtime once, verify its immutable inventory, then exercise packaged CLI creation/readback in disposable fixtures. Produce exact runtime/source identities, selected source paths, measured per-test outcomes/durations, failures/skips and limitations. Registry coverage updates are included only if needed for new test modules.

Useful existing test homes: tests.job_manager.test_job_control, test_templates, test_creation, test_execution_limits, test_native_handoffs; tests.tools.test_job_control_command, test_connected_creation, test_packaged_creation and focused stage-execution/worker bound tests. These are locations to select meaningful cases, not an instruction to rerun whole groups. No tests were run in this preparation.

## Bundle/source sequencing — no hidden join

1. Complete the separately allocated profile-only implementation in an isolated candidate on an accepted source. Independent review accepts its exact delta. Owner checkpoints/preserves that prerequisite source P and its reviewed input identity. Do not import the unaccepted Stage1-A candidate to obtain P.
2. Build and qualify a runtime bundle from P. Current OLD/distro lacks the new table entry; a source edit, JSON file or command-line override cannot teach a frozen binary the profile. New runtime is used for initial installation, compose-worker, create, serving and publishing in the fresh correction instance; do not update the old running instance.
3. Keep the feature source exactly f13e0b12, materialized from the already verified retained bundle. Bootstrap supports runtime distro P and `--repository-source` f13e0b12 independently. The correction task continues from retained bytes, not P or72e1093. No profile patch is silently applied to f13e0b12. Record BOTH runtime P/build identity and source f13e0b12 in kickoff evidence. Verify source-side support needed by composed tasks and unchanged image COPY inputs. If qualification discovers a required source/runtime join, stop with the exact incompatibility and obtain a reviewed isolated combined candidate; do not fabricate a compatible join.
4. After qualification, select the separate correction execution and explicitly apply the bounded same-family exception to it. Revised COMMANDS.md uses the new runtime and correct profile/override. Existing profile/task source definitions for analysis are unchanged. Native independent review evaluates the corrected Stage1-A candidate; eventual integration separately checks cumulative retained-base→final plus the accepted prerequisite, preserving provenance.

The runtime prerequisite can be implemented using the existing supported development workflow; it does not require heavy-profile support before its own small implementation. If using native execution, a separately selected small Job uses an existing finite profile; do not pretend to run heavy work before the prerequisite exists. No prerequisite implementation is assigned or launched by this packet.

## Exact conditional build and runtime selection

Only after the prerequisite source is independently accepted and selected. `HEAVY_CHECKOUT` is its isolated checkout; the exact digest/commit must come from its review, not an invented value here. These commands are a build/qualification boundary, not executed preparation:

```bash
set -euo pipefail
: "${HEAVY_CHECKOUT:?Set to the isolated independently reviewed prerequisite checkout}"
: "${HEAVY_SOURCE_COMMIT:?Set to its reviewed source commit}"
test "$(git -C "$HEAVY_CHECKOUT" rev-parse HEAD)" = "$HEAVY_SOURCE_COMMIT"
test -z "$(git -C "$HEAVY_CHECKOUT" status --porcelain -- v12)"
just --justfile "$HEAVY_CHECKOUT/v12/justfile" build
HEAVY_DISTRO=$HEAVY_CHECKOUT/v12/python/build/out/distro
"$HEAVY_DISTRO/baton-v12-stack" identity
```

The prerequisite's packaged deterministic evidence must establish profile resolution and propagation in this exact bundle; `identity` alone does not prove them. Retain build identity/inventory and independent signoff before moving to COMMANDS.md. No such bundle or signoff exists in this preparation, so the recommendation is conditional, not launch-ready. Proposed command delta is:

```bash
# Installation, preserving retained feature source:
just --justfile "$REPO/v12/justfile" bootstrap "$PACKET/bootstrap-inputs.json" "$DEST" "$HEAVY_DISTRO" "--repository-source $SRC"
# In the existing manager create invocation (full command in COMMANDS.md):
# --control-profile native-handoff-heavy/1 --provider-turn-seconds 7200
```

Remaining concrete blockers: separately allocated/accepted profile implementation and qualified bundle; new execution/model-exception selection. Same-Job retained correction and typed predecessor link remain unsupported, as previously reported. Do not repeat prior candidate verification merely to settle this profile prerequisite.
