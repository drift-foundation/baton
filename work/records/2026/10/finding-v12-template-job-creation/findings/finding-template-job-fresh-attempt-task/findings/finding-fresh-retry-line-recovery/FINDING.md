# Fresh retry writer ownership after a settled prior ending

## 2026-10-27 — confirmed runtime blocker from W364834

Accepted scope: DESIGN REC-4/REC-5/REC-7 requires fresh isolated attempts from known
inputs after exclusion, preserving original evidence, with manager-owned retry
admission. This is a prerequisite of W364834 task continuity and W361912 creation,
not a new recovery product selection or permission to change the specification.

**Confirmed:** parent candidate-364962 test_retry_task_lineage.py:
TheRetriedJobReachesItsOwnRuntimes.test_the_retrys_preparation_is_refused_by_the_lines_own_state
reproduces a retry offered/claimed by an authorized spare producer but exceptional
before runtime start: line state review-ready does not admit a writer. Both Job
identities resolve to one line. Reviewer independently ran all20 cases in13.443s.
Evidence: ../../evidence/review-365063/FOCUSED.txt and parent's review below.
Original ending answers unable with retained artifacts; capacity and routes are
explicitly configured. No task/input disagreement accounts for this failure.

Source: tools/stage_execution.py:3938 line_for uses binding Work with
review_cycles.create_line; worker_manager/review_cycles.py:1848-1864 grants writers
only in idle or correction-ready. A fresh retry is not a review correction.
These are evidence locations, not a prescribed edit list. The test author proposes
correction or another Work as alternatives; neither is selected. Do not manufacture
a review verdict, erase a frozen checkpoint or change Work/input identity merely
to evade writer admission.

**Required finite outcome:** supported fresh retry of this settled failed Job can
obtain safe, exclusively owned writable execution from known selected inputs,
reach its implementation runtime, and produce the checkpoint consumed by its
independent review runtime. Preserve original Work/specification/task identity,
failed attempt evidence and attribution; preserve legitimate pending review and
unresolved runtime exclusion. Manager/provider ownership must govern any required
recovery action with durable replay and restart. Unknown or conflicting prior
execution must refuse before effect. No raw store edits or forged cleanup/verdicts.
Revalidate current supported recovery APIs first; if existing mechanisms suffice,
provide connected evidence rather than unnecessary new product behavior. If a
concrete specification conflict is found, pin exact clauses/options for owner
approval before changing spec or implementing changed semantics. Internal design
choices within accepted recovery scope need no additional approval.

Baseline parent candidate-364962, manifest SHA256
7a2f1b734a1474d2e4e6df5b5759875df65c790c5c5c049055ffc2c733dd6812,
base19f02ce1295b4517a85f0822d48754efc982f388; entire overlay remains unaccepted.
Parent review ../../review-2026-10-27T00-35-03Z.md. Preserve all earlier candidates.

Decomposition: line recovery is now a concrete independently testable runtime
blocker, separate from task-lineage lookup. W364834 is the joined consumer and
retains task provenance/reopen/refusal acceptance. W361912 retains overall workflow,
packaged command and timing. Product execution remains serial: paused ancestors,
child implementer owns isolated candidate/tests/PROGRESS after claim; reviewer owns
FINDING/PLAN/reviews/evidence. Necessary edits chosen and recorded by implementer.
Use deterministic provider/engine/checkpoint seams and disposable owners. No live
execution, deployed-instance change, canonical import, cutover or Git mutation.

## 2026-10-27T00:45:35Z — diagnosis confirmed; authority clarification

review-2026-10-27T00-45-35Z.md independently checks all25 candidate hashes and12 diagnostic
cases. No product correction delivered. Existing implementation lacks the required
recovery transition; options based only on code/docstrings do not establish a
specification conflict. REC-4/5/7 already select safe fresh retry; ART-4/7, REV-1/2
and REC-6 preserve isolation, evidence and replay boundaries. This explicitly
rejects/supersedes the proposed owner-gated disposition in PROGRESS claim365081
and diagnostic-suite prose, without rewriting their history or changing DESIGN.
Continue bounded recovery implementation; exact normative conflict still requires
owner decision if one is subsequently demonstrated.

## 2026-10-27T01:42:10Z — runtime milestone advances; release defects

Review review-2026-10-27T01-42-10Z.md verifies all28 candidate-365155 hashes and199
focused passes. Connected retry reaches both runtimes. Independent probes confirm
R1 public release accepts completed candidate before freeze and R2 old release
replay fails after later checkpoint progress. This supersedes the implementation-
missing status with concrete changes-requested, not acceptance. Preserve prior
research and successful runtime evidence; same bounded operation owns correction.

## 2026-10-27T02:03:50Z — bounded recovery accepted

review-2026-10-27T02-03-50Z.md verifies candidate-365537 all28 hashes,212 focused
passes in86.580s and both original probes corrected. This explicitly supersedes
R1/R2 changes-requested disposition; historical reviews/evidence remain immutable.
Bounded recovery accepted for parent consumption, not whole-overlay import.
Pass to baton.decide for owner disposition under shutdown poke365623; ancestors
remain pending joined acceptance and no parent continuation starts here.
