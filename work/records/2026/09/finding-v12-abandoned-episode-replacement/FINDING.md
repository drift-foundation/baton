# Replace the safely abandoned correction episode once

Work W128698. Provider C approved by owner128669 in T119114. Discovery and
independent evidence: W119114 review-2026-09-09T14-55-17Z.md under
baton:work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/finding-standalone-stage-composition/findings/finding-composed-one-job-proof/.

Confirmed: the existing explicit abandonment ends an attempt, not its live Job
episode. manager._replace only opens successors of closed replaceable endings.
The existing abandoned-after-restart reason applies to issued offers with
unaccounted bearers; falsely reusing it for a claimed worker loses ownership.

Owner128669 approves exactly, relative to v12/python:
- src/baton_v12/job_manager/documents.py
- src/baton_v12/job_manager/episodes.py
- tests/job_manager/test_documents.py
- tests/job_manager/test_recovery.py

Tests remain additive. W128682 and W128692 supply independently accepted
committed abandonment/discharge and restored-checkpoint evidence. This provider
owns the exact Job episode boundary; W119114 later wires the explicit recovery
path and proves fresh ordinary allocation. No timer, generalized retry policy,
new Work routing or private custody-table access is authorized.

## 2026-09-09 — provider acceptance and dispatch revalidation, claim129402

The preceding additive-only restriction is superseded by
AGENTS.md#w71830-standing-test-change-authority through campaign completion or
revocation. Record test changes and reasons without further per-test requests;
acceptance behavior, four paths and20s cumulative verification remain.

Confirmed accepted inputs: A at
baton:work/records/2026/09/finding-v12-abandoned-cleanup-discharge/review-2026-09-09T15-29-15Z.md
and evidence/accepted-128851/; B at
baton:work/records/2026/09/finding-v12-abandoned-checkpoint-restore/review-2026-09-09T16-52-52Z.md
and evidence/review-129380/. Their public CONTRACT documents remain the receipt
authority. B now refuses altered unfinished-intent ownership before any effect.

Confirmed current source: episodes.restart_abandoned_correction is absent.
documents.EPISODE_ENDINGS and REPLACEABLE_ENDINGS lack the accepted new ending.
manager._replace delegates a replaceable projected ending to episodes.open_next;
that existing journal identity and one-live-episode uniqueness provide the
ordinary successor boundary. No manager/projection source change is scheduled.
episodes.advance_correction demonstrates existing public verdict/line readers,
stable historical replay and precondition rechecks under the Job transaction.
Reuse those owning interfaces without importing provider private helpers or
parsing custody tables. This consumer ends only the selected implementation
episode; it must not repeat advance_correction or advance the review episode.

Current four-file baseline bytes/hashes/modes are retained in
evidence/base-129402/. No implementation or tests ran during dispatch research.
First prove accepted A/B receipts permit one ordinary successor, then the
bounded retry/foreign/incomplete-evidence controls in CONTRACT.md. Preserve the
same fixture for W119114 rather than making a separate final-proof narrative.

## 2026-09-09 — revalidation and one pinned deviation, claim129415

All four baseline hashes and modes in `evidence/base-129402/manifest.json` match
the tree. A (W128682) and B (W128692) are both closed satisfying, and only their
public readers are consumed.

**One deviation from CONTRACT.md's literal wording, pinned before editing.**
The contract says to add `abandoned-after-exclusion` to BOTH
`documents.EPISODE_ENDINGS` and `REPLACEABLE_ENDINGS`. Adding it to
`EPISODE_ENDINGS` breaks the build at import: `manager.py:52` asserts
`EPISODE_ENDINGS` is a strict subset of `events.TERMINAL_OFFER_STATES` with the
difference exactly `{"claimed"}`, and `manager.py` is outside this Work's four
paths. `abandoned-after-exclusion` is not an offer state at all — nobody
declined, expired or refused anything; an operator declared an attempt
abandoned — so it belongs beside `superseded-by-correction`, which
`documents.py` already keeps in its OWN closed set for exactly that reason.

So it is added as its own closed set, `EXCLUSION_ENDINGS`, and to
`REPLACEABLE_ENDINGS`, and `documents.py`'s own subset assert is restated to
say the corrected rule. `projection.replaceable` reads `REPLACEABLE_ENDINGS`
alone, so the ordinary successor path works unchanged and no fifth file is
touched. The contract's behaviour — one closed, distinct, replaceable ending —
is met; only its placement differs, and this is why.

**Test delta authority** is `AGENTS.md#w71830-standing-test-change-authority`;
affected paths and reasons are recorded in PROGRESS without a per-test gate.

## 2026-09-09T17:07Z — independent review129471

Review-2026-09-09T17-07-35Z.md accepts the EXCLUSION_ENDINGS placement as a
clarification of the originally specified literal set membership. The old
EPISODE_ENDINGS placement requirement is explicitly superseded; its offer
semantics and the one ordinary successor behavior remain unchanged.

Observed in the candidate: the ordinary successor proof passes, but the
consumer accepts a valid restored checkpoint different from the Job's recorded
correction, ends an episode after an accepted review arrives between preflight
and transaction, and returns a malformed committed replay result. Exact
independent reproductions and full candidate custody are in
evidence/review-129471/. These are the remaining accepted handoff/ownership
requirements, not new scheduler features. Three controls pass in0.290509/3s.
Author7.070/20s cumulative leaves12.930s for the bounded correction.

The reported lack of package re-exports is not a provider defect: B's accepted
public CONTRACT locates both operations in worker_manager.review_cycles.
Normal module import is the specified consumer interface; no workaround or
source expansion is required.

## 2026-09-09T17:19Z — review129555 narrows the remaining journal boundary

The exact review129471 probes now refuse and three positive controls pass.
Review-2026-09-09T17-19-25Z.md retains the remaining failures: foreign Job and
episode accepted on replay, replay despite a missing historical ending, and a
foreign correction signature permitting fresh episode closure. Full candidate
and probe custody are in evidence/review-129555/. DIAGNOSIS.md records the
common cause and complete owner relationship for the next correction.

The ordinary successor capability and exclusion vocabulary remain established.
After two failed candidate reviews, bounded continuation is justified because
the unfinished outcome is one consumer journal relationship, with no separable
capability or source allocation. This supersedes the previous three-gap plan
as the actionable sequence. Author15.191/20s used leaves4.809s; independent
verification this pass used0.535087/3s. Standing campaign test authority remains.

## 2026-09-09T17:26Z — independent provider C acceptance

Review-2026-09-09T17-26-15Z.md accepts the four candidate paths retained in
evidence/review-129599/. All six retained counterexamples refuse, three positive
controls pass, and an independent trace proves the second connection reaches
BEGIN IMMEDIATE while the first action holds its transaction, with identical
answers and one ending. Reviewer0.723306/3s; author19.339/20s,0.661s remaining.
The previous remaining-journal diagnosis is resolved for this bounded contract.
The accepted A/B/C chain may now be consumed by W119114's joined proof.
