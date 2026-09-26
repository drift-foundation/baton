# Reconstruction of the damaged `review_cycles.py` span — 2026-09-26

Owner decision 270917 selects **documented reconstruction and independent
revalidation**. This record is the document that decision asks for. It is written
by baton.claude, who caused the damage. It is NOT a claim that anything here is
accepted: the owner's message is explicit that delivery requires provenance
reconciliation *and* correction acceptance, and that historical acceptance does not
transfer to reconstructed bytes.

## 1. What happened, in one paragraph

While replacing a block in `worker_manager/review_cycles.py`, I computed the end of
the region to delete with `s.index("def _restore_operation_id(")`. That definition
sits ~1600 lines after the block, so the splice removed everything between them.
44 function definitions were deleted and the module stopped importing.
No copy of the last-good state existed: my own `/tmp` backups from earlier claims had
each been removed after their mutation probes, and the file was already
uncommitted-modified before this session.

## 2. Bounded recovery inspection, and its result

Performed under owner 270917's instruction to look for a trustworthy pre-splice
source before accepting a baseline.

- **Every `review_cycles.py` on reachable storage was hashed**: 1,629 files under
  `/tmp`, `/var/tmp` and `/home/sl`, yielding 16 distinct hashes.
- **None matches any recorded W257624 candidate.** Tested against every hash this
  dossier has ever recorded for the file:
  `938bc0c6…` (the pre-session state), `0f994874…` (grant_writer correction,
  accepted), `04741974…`, `4dfe05da…` and `3efca9df…` (the restore corrections).
  All five: zero matches.
- **Preserved dossier candidates**: the reviewer's
  `review-candidate-2026-09-26T02-25-54Z.py.txt` (`67c376b4…`) and
  `review-candidate-2026-09-26T02-35-33Z.py.txt` are POST-damage snapshots, not
  pre-splice sources.
- **Session tool-result captures** were searched for the lost symbols. Three
  contain them; the only one that is source rather than test output is a PARTIAL
  dump dated 2026-09-07 (73,214 bytes, 43 definitions, starting mid-file at
  `__all__`). It is 19 days older than the damage and incomplete. Rejected.
- **`__pycache__`** holds a `.pyc` dated 2026-09-17, older than the baseline and
  not a faithful source of comments. Rejected.
- **Attribution of the lost delta.** The committed baseline
  `b6083a63…` is recorded in `finding-v12-workspace-shared-identity` as of
  2026-09-17 (W194457, closed satisfying). The pre-session state `938bc0c6…` is
  recorded ONLY by this dossier and by `finding-v12-fresh-attempt-recovery`, in both
  cases as **UNCHANGED** — that is, neither Work edited the file while recording it.
  A search of every `PROGRESS.md` and review journal dated 2026-09-18 or later found
  **no Work record claiming to have edited `review_cycles.py`** in that window.
  So the delta `b6083a63…` → `938bc0c6…` is **unattributed**: no dossier claims it.

**CONCLUSION: no trustworthy pre-splice source was recovered.** Per owner 270917 the
committed `b6083a63…` is therefore used as a reconstruction **baseline only**, and
explicitly not as evidence that prior uncommitted changes survived.

**THE RESIDUAL RISK, STATED PLAINLY.** The unattributed delta is real and its content
is unknown. "No dossier claims it" bounds who is likely to miss it; it does not prove
it was empty. Anything it contained that the selectors below do not observe is lost
and I cannot enumerate it. This is the irreducible gap in this reconstruction.

## 3. Inventory of every affected function, with its evidence

44 definitions were deleted and restored from the baseline. Coverage
below is **measured**, not asserted: a `sys.settrace`/`threading.settrace` collector
recorded every function in this file actually executed while running
`tests.manager.test_review_cycles`, `test_restore_outside_the_lock` and
`test_grant_writer_admission` (192 cases). The script is `/tmp/trace_span.py`;
tracing perturbs three timing-sensitive threaded cases, which is why that run shows
39 problems against the 36-error baseline — the call record is unaffected.

### 3a. Re-applied from documented, independently reviewed corrections (3)

Not restored from the baseline — these did not exist in it. Re-applied by me from
corrections whose text is recorded in this dossier and which a reviewer verified
against the pre-damage candidates:

  `_LINE_OBJECT` / `_line_object` / `_proved_line_object` — the accepted
  `grant_writer` I/O-under-lock correction (review 2026-09-26T01:32:28Z).
  `_resumed_writer` and `_proved_restoration_object` — the restore corrections
  (reviews 2026-09-26T01:23:34Z onward).

EVIDENCE: `test_grant_writer_admission` 12 cases OK exercises the first group
directly and is the reviewer's own accepted proof of that correction;
`test_restore_outside_the_lock` 18 cases OK exercises the second.
GAP: none identified, but note these were re-typed by me rather than recovered, so
their bytes are mine and not the reviewed candidate's.

### 3b. Restored from the baseline AND measured as executed (41 of 44)

  `_assignment_agrees`, `_attachment`, `_attachment_row`, `_attempt`,
  `_bound_to_act`, `_committed_fence`, `_committed_history`,
  `_committed_operands`, `_completed_review`, `_consumable_line`,
  `_current_fence`, `_derived_identity`, `_evidence`, `_fence`, `_id`,
  `_journalled`, `_line_place`, `_object`, `_one_by_attempt`, `_profile`,
  `_quiescent_completed`, `_requested_pair`, `_review_result`,
  `_same_assignment`, `_storage`, `_validate_line_object`, `_verdict_row`,
  `_within`, `attach_review`, `checkpoint_of`, `create_line`,
  `freeze_checkpoint`, `grant_writer`, `line_of`, `record_progress`,
  `record_verdict`, `review_for_attempt`, `review_of`, `verdict_of`,
  `writer_for_attempt`, `writer_of`

EVIDENCE: each name above was observed executing during the accepted selectors.
Behaviour is therefore exercised. GAP: coverage proves the restored definition
behaves acceptably; it does not prove an unattributed pre-session edit to it is
present. That gap is the section 2 residual and applies to every name here.

### 3c. Restored from the baseline and NOT observed executing (3)

  `_cleaned_review`, `_committed_act`, `_custodied_review`

These are the **unresolved gaps** the owner asks to be recorded per function. They
were restored verbatim from the baseline and no accepted selector in the measured set
reached them, so this reconstruction has neither behavioural evidence for them nor
provenance evidence. They are review-verdict and custody helpers on the
`record_verdict` path; the suites exercise `record_verdict` itself, so the likely
reason is that these branches need dispositions the measured selectors do not
produce. I am NOT asserting they are correct.

## 4. Duplicate definitions, reconciled

Review 2026-09-26T02:25:54Z confirmed `_proved_restoration_object` at 1035/2046 and
`_resumed_writer` at 2064/2105 — my re-application landed beside copies the surviving
tail already held. Both pairs were compared **byte-for-byte before removal** (871 and
2,080 bytes, identical), so no choice was made between diverging versions. The later
copy of each was removed; definition count 77 → 75, then 74 after `_claim_execution`
was folded into the admission transaction. Module imports; no duplicates remain.

## 5. Preserved artefacts

- `RECONSTRUCTION-CANDIDATE-2026-09-26T02-40-00Z.py.txt` — byte copy of the current
  candidate (`a7760cd9…`), so the delta under review cannot move while reviewed.
- The reviewer's `review-candidate-2026-09-26T02-25-54Z.py.txt` (`67c376b4…`) and
  `review-candidate-2026-09-26T02-35-33Z.py.txt` — untouched.
- All four reviewer probes, every review journal, both LIVE-RUN-RESIDUE inventories
  and Tuner's R5-PREPARATION.md — untouched.

## 6. What independent revalidation still needs to cover

1. The reconstructed span as a delta against `b6083a63…`, read rather than trusted.
2. The three section 3c functions, which have no evidence either way.
3. Whether the section 3a re-typed corrections match what was accepted, since their
   bytes are mine.
4. The unattributed `b6083a63…` → `938bc0c6…` delta, which nobody can produce.

I make no claim that historical acceptance transfers to any of it.
