# The composition that enforces the human approval boundary — W321690

`composition.py`, one run from `v12/python`: **32 checks passed, 3 scenarios
observed, 1 failed exactly as it must, 0 unexpected, 3.667s.** Evidence bound
by `MANIFEST.json`. Source base `372281f4a473300efb474d5a6573954c15ade367`
(`git diff --stat 372281f4 HEAD -- v12/` empty); zero changes under `v12/`.

## The question the review asked

Review 2026-10-18T19-33-42Z found the real defect in my packet: §9A said the
manager serves and §9B told the operator not to call automatic integration
admission. **An instruction is not a control.**
`tools/stage_execution.py` reaches `admit_accepted` (3118, 3153) and
`continue_accepted` (3149) during ordinary manager progress, with the
deployment's own verification, review and approval sessions — so a serving
composition can take the owner's decision however firmly a document forbids it.
Name the supported shape that enforces the boundary while preserving result
pickup and review, or name the exact unavailable operation.

## The answer: the submitted Job's own stage set

**A Job composed of `implementation` and `review` only.** Not a new operation,
not a product change, not an owner product choice — a submission the deployment
already composes. Driven in scenario 1 (15 checks):

| property | result |
| --- | --- |
| pickup and the real worker turn | served normally |
| the implementation ending | `completed` |
| the independent review assignment and its real turn | `completed` |
| the candidate | **published** — `integration-driver.proposal:…`, whose `candidate_digest` equals the reviewed frozen checkpoint's own head |
| the line and checkpoint the receipt actors judge | the review attachment, the checkpoint and the line all agree, and the line is bound to this Work |
| receipts | **all four absent** |
| a falsely complete integration stage | none exists to be left |
| the Work | open, no handler, handed on to the configured outgoing route |

And then the part an instruction cannot give: **40 further ticks admit
nothing, and a fresh serving composition over the same stores plus
`recover()` admits nothing either** — no receipt appears, no second candidate
is published, and the restarted composition still shows two stages. There is no
integration call site in this Job for a serving manager to reach.

## The human path on that shape (scenario 2, 11 checks)

On the same world, with the grants written first and the policy generation read
back: the owner holds **no** `verify` or `review` capability; the verification
actor's `Session.verify` records `passed` and the review actor's
`Session.review` records `accepted`, each attributed to its own participant;
**the approval is still absent**, and so is the integration receipt;
`disposition pending` answers `approval-due`; and with the approval withheld
both `disposition integrated` (citing a human integration record) and
`disposition close --outcome satisfying` are **refused**, with no receipt
changed across either refusal.

The owner's own `approve` → `integrated` → `close satisfying` → readback chain
is the accepted W325034 proof
(`baton:work/records/2026/10/finding-v12-pilot-human-approval-boundary/boundary-325197/`
scenario 2) and is deliberately not repeated here.

## The contrast, measured rather than assumed (scenario 3, 6 checks)

With the integration stage composed, on this same fixture: implementation and
review complete, a candidate is published, and **no receipt is written here
either** — because this fixture's deployment configures no integration
instructions, so the sweep *defers* the stage with its own contained refusal
(`refused`/`capability`, "this deployment configures no
integration_instructions"). The stage holds at `claimed`.

So this scenario does **not** show automatic admission happening, and says so
in its own `not_claimed` member. What it does establish is the operational
difference that makes the stage set the control: with an integration stage
composed the Work does **not** reach the owner — it is held by the integration
participant under a decision nobody has made. The evidence for what a fully
configured integration deployment does at that boundary is the retained
`baton:work/records/2026/10/finding-v12-pilot-workflow-rehearsal/rehearsal-324985/RECEIPT-BOUNDARY.md`:
verification, review and approval written together before any runtime.

**No product defect is claimed.** The supported configuration answers the
question, which is what the review asked me to check before proposing anything
else.

## Harness

The strict classifier from
`baton:work/records/2026/10/finding-v12-pilot-diagnostic-recovery-matrix/matrix-325259/matrix3.py`:
`0-harness-self-check` asserts something deliberately false and must fail with
its **own named** `CheckFailed`, with no setup traceback and no cleanup
failure; anything else counts unexpected and `main` refuses the run. Two of my
own faults were caught by it during this claim rather than by prose: a
misplaced subcommand verb (the CLI takes the verb first) made `argparse` exit
the whole process after scenario 1 with no summary — `except Exception` does
not catch `SystemExit` — so `command()` now contains it and the scenario loop
catches `BaseException`; and a wrong sweep-report key made my
contained-refusal check fail. A zero exit alone is never acceptance.

## Boundaries and provenance

The composed native Job world is imported from
`tests.tools.test_stage_execution` and not modified. The engine answers without
a daemon; the provider is injected at the adapter's own process seam; the
verifier's, reviewer's and owner's judgments are simulated and labelled, and
the human integration record's commit is forty zeroes — **a labelled fixture,
not delivery evidence**. `_accepted_receipts`, `admit_accepted` and
`continue_accepted` are never called by this driver. No product edit, no forged
receipt, no raw SQL, no live model, no live credential, no deployment, and
nothing that mutates this repository's history, index or working tree — the
imported fixture builds its own disposable history inside a temporary root
under `GIT_CONFIG_GLOBAL=/dev/null`.
