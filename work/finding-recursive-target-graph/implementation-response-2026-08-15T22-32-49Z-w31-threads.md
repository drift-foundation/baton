# W31 delivered in source; the v11 return is blocked by the absent trial home

v11 Work `26de18dd-W31` rev 2 ("Adopt subject-bearing Thread
vocabulary") is implemented end to end for the next distribution. The
return through v11 could not be committed: `/home/sl/baton-v11/` no
longer exists (the whole coordination home is gone; the deployed
`6d1b944` distribution remains). That is consistent with the ruled
trial replacement — the fresh authority follows the NEXT distribution,
which requires exactly this change — so I am reporting the evidence on
v10 instead of holding a dangling v11 act. If the home returns, I will
commit the prepared return (`op-id w31-return-1`) on the next wake.

## What was implemented

- **Schema v14**: `threads(id, subject NOT NULL, created_seq,
  created_ts)`, `thread_labels`, `thread_participants`; every
  `discussion` column is `thread`; thread ids are `-T{seq}`. No
  migration; no aliases; fresh authorities only.
- **Transitions**: `create_thread` requires a concise subject
  (non-empty, single line, ≤80 UTF-8 bytes; refusals leave no
  residue; the stored subject is the normalized one). The born
  Thread's subject is the Work's title; accept-created provider
  threads take the created title; replies never carry or repeat a
  subject. Subjects ride payloads and WS-5 fingerprints.
- **Projection 3.0** (breaking version bump): `thread` exposes
  `subject`; `work_threads` rows carry `subject` and a canonical
  `ordinal` (stable label-order index — the T{n} selector renders it,
  never derives it); `threads_for` and the detail preview carry
  subjects.
- **CLI**: `start-thread --subject` replaces `discuss`; `threads`,
  `work-threads`, `thread`, `say`, `label`, `unlabel`, `mark-seen`
  are the thread surface. No Discussion vocabulary remains in
  src/baton_work or the quickstart.
- **TUI**: the thread list leads with `T{ordinal} {subject}` (stable
  id kept); the compact bottom pane is
  `Msgs T{n}/{total} — {subject}`; the Work→Threads→Msgs drill is
  the navigation model.

## Evidence

- New `tests/work/test_w31_threads.py`: the subject contract
  (refusal matrix with no residue), born-title subject, several
  Threads on one Work AND one Thread across Works with stable
  ordinals and one subject each, replies never repeating the subject.
- New Msgs-pane PTY test: `T1/T2` listing by subject and
  `Msgs T2/2 — the follow-up questions` on the selected thread.
- Whole-tree vocabulary migration: 38 test files, wfdriver,
  fixtures; `start-thread` exercised through the CLI in the workflow
  battery.
- Break-sweeps (defect in → red → restore → green, no residue):
  subject validation dropped; born subject replaced; the Msgs
  selector dropped; the ordinal flattened.
- Gates: engine 442; TUI/parity 32; packaged/deploy 14; workflows 56
  — all green on the deployed-product harness; `just test-v11` 546
  parallel + 3 serial. Dossier: PROGRESS.md Step 58.

Everything applies to the next distribution only; `6d1b944` and its
(now absent) authority were never touched. Production operations
remain held.

---

## Addendum (R3): the return SUCCEEDED at the moved authority

The block above was transient: the trial authority had MOVED to
`/home/sl/baton-v11.6d1b944` (`/home/sl/baton-v11` is intentionally
absent, reserved for the fresh init after the next immutable app
deploy — v10 message f0389ec9c6eb2fbcde0e2a589e8cdc5f). The prepared
return committed there exactly once under `op-id w31-return-1`:
evidence message #43 in `26de18dd-D31`, consuming pass to
`baton.feat` (Current baton.feat, Next None). This addendum preserves
the original evidence and corrects the stale operational statement.

## Addendum (W31 review R1): the subject joins the fingerprint

Per review-2026-08-15T22-35-13Z.md R1: the subject is now
validated/normalized BEFORE the operation lookup and included in the
typed effectively-once fingerprint — an identical retry replays the
one committed Thread; a changed subject under the same
participant/op-id refuses "different request" with no authority
residue. The reviewer's fingerprint regression is green and its sweep
(dropping the subject from the fingerprint) bites.

R2 (one normalized single-line ≤80-byte contract for Work title AND
born Thread subject) awaits Slawomir's confirmation as the review
requires; its two regressions remain deliberately red until that
ruling. No full-gate claim is made while they stand.
