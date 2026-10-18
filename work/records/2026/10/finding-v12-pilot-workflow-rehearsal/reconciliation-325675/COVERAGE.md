# Joined evidence map — W321690, claim 325675

What the accepted child proofs establish, mapped to the five joined proofs
named in T321690 M324395 and to the original FINDING's acceptance list, with
the exact scenario and assertion each claim rests on. **No evidence is rerun
for consolidation and no manifest is rewritten**: this map cites retained,
manifest-bound runs by digest.

## The accepted sources

| Source | Manifest SHA-256 | Members | Accepted by |
| --- | --- | --- | --- |
| `baton:work/records/2026/10/finding-v12-pilot-human-approval-boundary/boundary-325197/` | `dd2d071a1669fe861a7a4e3eaea80ed4f2310ad9fe7aafd593f56a0c1a907a4f` | 6 | `review-2026-10-18T18-25-51Z.md` (claim 325256) |
| `baton:work/records/2026/10/finding-v12-pilot-diagnostic-recovery-matrix/matrix-325259/` | `970a1a22f209069a7db1595d8d02f34ad40584258ab8d550a31a3d239dd26309` | 12 | `review-2026-10-18T18-43-12Z.md` (claim 325381) |
| `baton:work/records/2026/10/finding-v12-pilot-dossier-binding/correction-322441/DIGESTS.json` | `e8f3f8d96aea26dccbb231310e6e05e33be5cbe23f7464548e32db435e532e25` | — | W321688, closed satisfying |
| `baton:work/records/2026/10/finding-v12-pilot-owner-disposition/candidate-321689/DIGESTS.json` | `dbc163c7dc3f08fcf17030b78923029431c2f615c9bf9c797c5c9223a62b1c77` | ten paths | W321689, closed satisfying |

Both child manifest digests were recomputed in this claim and match the
reviewer's independently published values exactly. The W321688 `DIGESTS.json`
digest is recorded here because the packet cited the file by path only.

**These were four separate deterministic runs on four disposable worlds.** They
are not one continuous session and nothing below says they were. Where two
scenarios share an attempt identity (`attempt-7b5e070a…` appears in both
children) that is the *fixture lineage* deriving the same identity from the same
inputs, not one run observed twice.

## Proof 1 — a terminal result reaches a native eligible independent review

Covered, by both children.

* `matrix-325259` scenario 4, 18 checks: gen 1 implementation
  `attempt-7b5e070a…` → writer `writer-17f33e9b…` → frozen
  `checkpoint-f808f219…`; gen 2 review `attempt-9e961a44…` is a *different
  participant* and its attachment names that exact checkpoint; gen 3 successor
  `attempt-965a8ab8…` is based on the same checkpoint. All on one line
  `line-c71b47a3…` bound to `0000000a-W1`. Read through
  `writer_for_attempt` / `review_for_attempt` / `checkpoint_of` / `line_of` —
  not a status row and not the private `_prepared` inventory.
* `boundary-325197` scenario 2 carries the same chain to a published candidate:
  proposal `integration-driver.proposal:389e6f1e…`, candidate
  `60102b2e6ff33689f9c37f9008ae2e4154a7f45f`, with `ordinary_test_evidence`
  cross-binding attempt, result, checkpoint and assignment.

## Proof 2 — failed, empty and unknown results reach a diagnostic owner and are never accepted

Covered by `matrix-325259` scenarios 5, 6 and 2 (41 checks together).

* **Provider-failed** (scenario 5): stage `exceptional`, `pending_endings`
  empty, and the **authoritative** inventory (`Authority.proposals_of`) empty —
  not inferred from a missing projection member.
* **Empty turn** (scenario 6): a provider exiting 0 that writes nothing settles
  `exceptional`, freezes no completed result, publishes no candidate, is not
  offered a second attempt.
* **Held unknown** (scenario 2): an engine answer whose prose names no
  container leaves the runtime axis `running`, the identity retained, the stage
  gated at `waiting`. The uncertain gate is **not** released.
* **Diagnostic ownership** (scenario 5): the operator names a diagnostic
  handler for the failed Work's route and `baton.diagnostician` claims it — an
  eligible assignment naming that participant and
  `principal:baton.diagnostician`, with an identical claim replaying rather
  than taking a second one; labels are capability-bounded
  (`manage-work-labels`) and make the failure discoverable; or a dedicated
  diagnostic Work is created attributably on its own route for its own owner,
  because one principal holds one claim.

**Historical correction, preserved:** my claim 325037/325138 position — that no
supported operation names a diagnostic owner, and that this is a product gap —
is withdrawn in `baton:work/records/2026/10/finding-v12-pilot-diagnostic-recovery-matrix/matrix-325138/SUPERSESSION.md`. What is true is narrower:
nothing routes an exceptional stage *automatically*; an operator must notice it
and the handler is an explicit deployment selection (§3 of the packet).

## Proof 3 — restart and a lost reply preserve the obligation and the exact claim

Covered by `matrix-325259` scenarios 1 and 3 (29 checks).

* **Lost reply at the exact boundary** (scenario 1): the engine really starts
  the container; the process stops inside the following `ps`, leaving
  `execution_runtime: start-requested` with no attached runtime and the stage
  still `claimed`. A manager reconstructed over the same stores **and the same
  engine state** asks the engine, adopts the exact runtime
  (`runtime-single-1`) on the same attempt with the assignment unchanged,
  starts no second container, prepares no duplicate attempt, invents no
  failure, publishes no candidate, and serves again.
* **No duplicate ownership across the restart** (scenario 3): the assignment is
  identical member by member including participant and generation, the
  committed assignment history is not extended by the recovery, route/handler
  and the runtime ownership record are unchanged; sweeping the *old*
  composition afterwards starts no second container, prepares no second
  attempt and leaves the same single assignment.

## Proof 4 — a stale episode or wrong principal cannot publish or take over

Covered by `matrix-325259` scenarios 7 and 8, and by `boundary-325197`
scenario 2's negatives.

* Scenario 7 (11 checks): both refusals driven against a *live* assignment, and
  after each one the Work's status/phase/route/handler/outcome are unchanged,
  the live assignment is the same one, and **no assignment event was written**.
* Scenario 8 (18 checks): a second live claim through a second writable handle
  is refused (`Work is already claimed`) — the enforcement is the claim's
  compare-and-swap, not the file handle; a read-only handle refuses every
  transition and touches nothing.
* `boundary-325197` scenario 2: a wrong principal is refused the approval
  (`does not hold the approve capability`), a stale candidate digest and a
  wrong review receipt are each refused, and **no receipt changed across every
  refusal**.

## Proof 5 — owner pending, approval, integration reference and closure survive readback

Covered by `boundary-325197` scenario 2 (34 checks) on a candidate published by
the same native lifecycle, and by `matrix-325259` scenario 8 for the
non-satisfying half.

Order as driven: independent `Session.verify` → `Session.review` **with the
approval still absent**; `disposition pending` answering `approval-due`;
integration and satisfying closure **refused while approval is withheld**;
`record bind`; the owner's `approve`, whose exact replay preserves the receipt
identity; `integrated`; `close --outcome satisfying`; and a readback answering
`closed` with the acceptance clause and the cited human record intact. **Four receipts from three
distinct actors** — `baton.verifier-325034` (verification),
`baton.reviewer-325034` (review), and `baton.slaw` for both the approval and
the integration, which is the owner legitimately appearing twice. An earlier
revision of this file said "four distinct actors"; that count was wrong and is
corrected here, per review 2026-10-18T19-33-42Z.

`matrix-325259` scenario 8 adds the honest negative ending: a live cancellation
removes the handler without closing the Work, the **runtime-quiescence gate
survives it** (a re-claim is refused with `Work is blocked by
'runtime-quiescence:1'`), and the owner's installed
`disposition close --outcome non-satisfying` records the operator's own
rationale with no acceptance.

**Historical correction, preserved:** PACKET §7a previously stated that the
packet *cannot* promise single-human approval on the native path. That
conclusion is superseded by W325034 and is withdrawn; the observation it rested
on stands and is narrower — the *automatic integration admission* path
(`_accepted_receipts` via `admit_accepted`/`continue_accepted`) writes
verification, review and approval together, so a deployment that runs it for a
human-approved Work pre-empts the owner. Recorded in
`baton:work/records/2026/10/finding-v12-pilot-workflow-rehearsal/rehearsal-324985/RECEIPT-BOUNDARY.md`; the operational consequence is the
packet's §9 rule not to call automatic admission on that path.

## The original FINDING's acceptance list

| Required | Where | Status |
| --- | --- | --- |
| lost replies / replay at handoff and decision | matrix sc. 1; boundary sc. 2 replays (verify, approve) | covered |
| stale / wrong principal | matrix sc. 7; boundary sc. 2 negatives | covered |
| missing evidence | boundary sc. 1 (four mutated requirement selections withhold the judgment, no receipt written) | covered |
| withheld approval | boundary sc. 2 (integration and closure refused, approval null after both judgments) | covered |
| non-satisfying outcome | matrix sc. 8 | covered |
| cancellation | matrix sc. 8 (live, asserted) | covered |
| held-unknown runtime | matrix sc. 2 | covered |
| manager stop alone cannot permit replacement | W321688 `RECOVERY.md` "Taking a cut" steps 1–2; matrix sc. 3 proves ownership retention, **not** cessation | covered by contract, not by execution — see Limits |
| one writable authority per Work | matrix sc. 8 (claim CAS, read-only handle), sc. 3 (authority identity gate) | covered as stated in Limits |
| stable history / dossier through disposable recovery | W321688 accepted recovery set and its restored-readback rehearsal | covered by W321688, cited not re-proved |
| no v11 shadow assignment | no v11 Work was created, claimed or assigned by any child run; v11 remains the preparation authority only | covered |

## Limits — what these proofs do NOT establish

1. **No live execution.** Every engine and provider is simulated at its own
   boundary and labelled in each scenario's `simulated` member; every verifier,
   reviewer, owner and diagnostic judgment is simulated and labelled
   (`SIMULATED (W325034 rehearsal; no human act, no live provider)`). The
   integration record's own bytes carry forty zeroes for the commit: **a zero
   commit is a labelled fixture, not human delivery evidence.**
2. **Same-authority restart is not restoration or failover.** `matrix-325259`
   scenario 3 reconstructs a manager over the *same retained disposable
   authority*; `Authority.stored_identity` proves store kind and UUID only. It
   is not execution of the recovery-manifest/recovery-check set, not a restored
   backup, and not exclusion or fencing of another writable copy. W321688's
   recovery contract remains the authority for that, and the operator
   obligations stand: positively account for every runtime and launch, and
   admit only one writable instance.
3. **Automatic diagnostic routing is not proved or claimed.** The demonstrated
   path is explicit configuration plus an explicit claim.
4. **The W325034 harness self-check used the broad classifier.** Its `main`
   compared only failure against expectation, so a setup or cleanup error could
   have satisfied the self-check. It did not here: the retained
   `baton:work/records/2026/10/finding-v12-pilot-human-approval-boundary/boundary-325197/scenario-0-harness-self-check.json` records
   `failed_check` = "the review stage is completed immediately after
   submission (INTENTIONALLY FALSE)", with its detail naming the stage states
   it actually read, and carries no `failure` and no `cleanup_failure` member,
   and the accepting review independently validated exactly those facts. The
   strict classifier — intended `CheckFailed` by name, with setup and cleanup
   errors counted unexpected — exists in `baton:work/records/2026/10/finding-v12-pilot-diagnostic-recovery-matrix/matrix-325259/matrix3.py` and is what
   any rerun should use. A zero exit alone is never acceptance.
5. **Four runs, not one.** Joined coverage here is a reconciliation of four
   deterministic runs over separate disposable worlds, by design and under the
   review's instruction to reuse accepted evidence rather than rerun for
   consolidation.

## Provenance

Product tree base `372281f4a473300efb474d5a6573954c15ade367`, which is also
the base both children recorded. `git diff --stat 372281f4 HEAD -- v12/` is
empty, so the two later commits (`61a930e8`, `9debba18`) are record-only and the
pins in the packet hold at `HEAD` = `9debba18` as well. Nothing in this claim
mutates this repository's history, index or working tree; the imported fixtures
build their own disposable version-control history inside temporary roots under
`GIT_CONFIG_GLOBAL=/dev/null`.

## Appended under claim 325757 — the composition boundary

Review 2026-10-18T19-33-42Z found that the packet enforced the human approval
boundary by instruction rather than by control. The supported control is now
pinned in PACKET §3b and driven in
`baton:work/records/2026/10/finding-v12-pilot-workflow-rehearsal/composition-325757/`
(32 checks, 3 scenarios observed, the self-check failed for its own named
reason, 3.667s): a Job whose stage set is `implementation` and `review` only is
served normally, publishes the candidate, and **cannot reach
`admit_accepted`/`continue_accepted` at all** — proved through 40 further ticks
and a fresh serving composition with `recover()`. The independent receipt path
and the withheld-approval refusals were then driven on that same shape.

Two corrections to this file itself, both from that review: the receipt-actor
count above (four receipts, three distinct actors), and the shortened
cross-record locators, now written as canonical `baton:work/records/...`
addresses.
