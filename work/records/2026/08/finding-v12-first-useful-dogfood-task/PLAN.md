# Plan

## Current checkpoint plan — confirmed 2026-08-29

1. [done] The one-episode exception returned at sequence 39342 with item 3
   delivered, items 4-8 open, an exact changed-file inventory and recorded
   tests/concerns. No later implementation resumes under the parent.
2. [done] Four canonical child dossiers and Works exist: W39356 transport,
   W39357 Claude adapter/image, W39358 supervised operator and W39364 useful
   task plus independent acceptance.
3. [done] W39358 is blocked on W39356 and W39357; W39364 is blocked on W39358.
   W38956 is blocked on W39364, keeping the roll-up dormant until the final
   critical-path result returns. The child findings pin non-overlapping initial
   file ownership.
4. [done] W39366 is the separate top-level non-gating hardening Work. It is
   parked at low priority and has no edge into this roll-up.
5. [active children; critical-path correction confirmed 2026-08-30] W39357 is
   closed. Return W39356 for final independent review without waiting for
   W39666; that separately owned boundary-inventory hardening remains open but
   non-gating. W39356 acceptance releases W39358; its acceptance releases
   W39364.
6. [roll-up] Close W38956 only after W39356, W39357, W39358 and W39364 are
   independently accepted and the useful supervised result satisfies this
   record.

At the first handoff, map the active episode's output into these children.
Completed pieces still require child-scoped independent review; incomplete
pieces become the relevant child's starting evidence rather than one more
giant parent round.

## Prior single-claim plan — superseded by checkpoint decomposition

The items below preserve the revalidated technical inventory. They are inputs
to the child plans, not one implementation checklist for W38956's live claim.

1. [done] Revalidate W6636 and W17110 against the current tree. W6636 composes
   production lifecycle/custody with a fake control session and host-authored
   output; W17110 proves real Claude in Docker through a spike-only lifecycle.
   No reusable operator, real Claude worker adapter or Docker worker-entry
   transport currently joins them.
2. [done] Select the first task: add focused subprocess-vector and result-
   mapping coverage for ping-pong `_observed_readable`, including readable,
   unreadable, absent and nonzero-probe endings. The current harness mocks that
   crossing, so this is a real isolated regression gap with one focused gate.
3. [done, awaiting review] Implement and unit-test the narrow Docker
   worker-entry transport. Delivered as
   `v12/python/src/baton_v12/worker_manager/worker_entry.py` with
   `oci.exec_vector`, the opt-in `interactive` start operand and the explicit
   `network` posture operand; 45 cases in
   `v12/python/tests/manager/test_worker_entry.py`, whose positive half drives
   the image's own `baton_worker.serve` over a real pipe pair rather than a
   fake peer. See FINDING.md's 2026-08-29 implementation revalidation for the
   measured reason the transport is `docker exec` and not `docker attach`.
4. [next] Build the dogfood Claude worker image/entrypoint by injecting a real
   agent into `baton_worker.main(agent=...)`. Reuse W17110's pinned installation
   evidence without reusing its trial protocol. Golden-test provider argv,
   fixed credential-slot use, source copy and declared proposal writes.
5. [next] Implement one documented Python operator entry point. Require an
   explicit source subset, frozen task, Claude credential source, engine,
   manager state/evidence roots and configured workspace group; provide no
   home-directory credential or mutable-tag fallback. It also requires the
   explicit network posture operand added at item 3, and composes the port's
   session itself because the v12 `Session` carries six of the port's seven
   operations.
6. [next] Stage the nominated source subset with `copied_manifest`, compose the
   accepted input/assignment/launch and `proposal` declaration, then drive the
   public offer/claim/start/control/freeze/intake/retention/cleanup operations.
   Test positive, provider/control/transport negatives, exact retry, isolation
   and every cleanup ending with injected capabilities before real Docker.
7. [next] Run the frozen ping-pong regression task through one real Claude
   container, using `evidence/first-task.md` and its exact three-file source
   subset. Retain the correlated input, task, image, assignment, runtime,
   output, cleanup and redacted verification transcript; retain no bearer or
   raw provider conversation.
8. [next] Independently compare `proposal/candidate` with the measured staged
   input, inspect `change.patch`, run
   `python3 v12/spike/ping-pong/test_harness.py` outside the worker, and record
   explicit acceptance or rejection. Never copy the candidate into the
   canonical checkout automatically.
9. [next] Return the reusable vertical slice for independent review. Split
   observed nonessential hardening into owned follow-up Work; a defect that can
   make the positive result false remains in W38956.

## Scheduling

This milestone is high priority and may begin from the accepted Docker
capability pass without waiting for W32382 negative/race hardening, W32391
Podman certification, W28880 labels or the complete W7 proposal pipeline.
W36540 may proceed concurrently; its unconditional hostile-output custody is
a later guarantee rather than a condition for cooperative output in this
bounded pilot.

W29400 may finish the implementation claim it already held when W38956 was
created. Do not start W29401 or another unrelated label follow-up ahead of
W38956 once this milestone passes to the implementation route.


## What items 7 and 8 wait on, and it is not implementation

Two grants belong to the operator and cannot be self-authorized by an
implementer. They gate the live trial whatever state items 4 to 6 reach:

- **The exact credential operand.** The finding already requires it and
  explicitly does not inherit W17110's bounded permission. There is no
  home-directory default and none will be added.
- **The network posture.** Item 3's revalidation found that every runtime this
  manager can start is `--network none`, so the accepted adapter could not have
  reached a provider at all. The posture is now one explicit operand defaulted
  closed; which value the first trial names is an approver decision, because
  the alternative reading -- an egress allowlist or proxy for provider traffic
  only -- produces a materially different operator command.

## Owed against item 3, and named rather than quietly left

Three boundary entries this change introduces have no owner in
`tests/manager/test_boundary_inventory.py`:

    ('oci.py:_network', 'text', 'an engine network')
    ('oci.py:exec_vector', 'text', 'an exec program word')
    ('worker_entry.py:converse', 'identity',
     'a worker-entry operation identity')

They are NOT added here on purpose. That gate is already failing on 29 other
entries that predate this Work -- `attempts.py`, `custody.py`, `intake.py`,
`interrogation.py`, `lanes.py`, `posture_slots.py`, `workspaces.py` and most of
`oci.py` -- and the file is under another participant's uncommitted edit in the
current tree. Adding entries to a registry whose attribution mechanism is
mid-change, in a file somebody else is editing, is the parallel-edit collision
`AGENTS.md` requires ownership to be established for first. The three are owed
and are recorded here so they cannot be lost.
