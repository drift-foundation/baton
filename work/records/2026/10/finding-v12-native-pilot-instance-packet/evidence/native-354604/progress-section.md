
## 2026-10-22 — baton.claude, claim354604 — THE DISK-ROOT FINDING ABSORBED; THE TWO-STAGE PROOF SCOPED, NOT HALF-BUILT

Claimed at snapshot354604 after reading canonical state (queued, unclaimed,
routed `baton.impl`, `last_change_seq 354601`, zero open blockers), the
complete handoff through `work-events` (87 events, no pagination remaining) and
thread T325959 in full (5 messages, `last_seq 329708`, unchanged). Read
`review-2026-10-22T19-42-43Z.md` and `REVIEW-INPUTS-354590.json`.

### The reviewer's operational finding, absorbed without a source edit

Review354590 met 3 failures until it set
`BATON_V12_DISK_ROOT=/var/tmp/baton-w257624`. **There is no defect to fix**:
the real-composition cases inherit `SingleWorkerCase`/`ServingCase`, which
already take a disk-backed root through `tests.manager.disk_roots`
(`test_single_worker.py:287`), and that helper **refuses by name** on a tmpfs
rather than falling back — by design, since *"a suite that skipped itself on a
tmpfs `/tmp` would report green on a host where the boundary was never
exercised"*. The reviewer read the refusal and supplied the operand, which is
the designed path; changing the mechanism would be churn and would weaken a
deliberate refusal.

What I did instead: recorded the requirement in the test module's own
docstring, so the next runner reads that refusal as an environment operand
rather than as a failure of this subject. **12 cases still OK.** Test file
`6de86489…` → `4cdc1afcf954a4beacaa261aceb35f6458feb1c621b3b9d307b04b3969a80cef`.

### The named gap, scoped rather than half-built

The reviewer is right that *"two real stage workers carrying one policy prove
delivery, not both stages reaching actual acquired tokens"* — my
`NativeStageComposition` case proves delivery by object identity and nothing
about the review stage's own acquisition.

What I established about its shape this claim:

- `SingleWorkerCase.submission` composes **one** stage
  (`test_single_worker.py:414-421`), so the harness my acquisition case uses is
  structurally single-stage and cannot reach a review stage at all.
- `ServingCase.serving()` **does** compose both stage workers and is the right
  base (`test_stage_execution.py:3592` reads both roles), but driving the
  review stage to its own acquisition needs the implementation stage completed
  and the review gate opened first.
  `test_a_review_stage_is_admitted_by_the_review_worker` (`:3609`) exercises
  `_matches` **structurally** — it hand-builds a stage dict and asserts no
  refusal; it starts nothing.

So the two-stage acquisition proof needs a fixture that completes an
implementation stage and opens the review gate — materially more than
extending an existing case.

**Why I stopped rather than starting it.** I had budget to begin but not to
finish and verify. A half-built two-stage drive reported as progress would be
the third surrogate in a row after `inspect.getsource` and the mocked
composer, and the reviewer has corrected me twice on exactly that. The shape,
stated honestly, is worth more than an unverified attempt.

**Exact next executable step**: base the proof on `ServingCase.serving()`;
complete the implementation stage and open the review gate through the existing
`prepare_implementation` / `freeze_checkpoint` / `prepare_review` helpers named
at `test_stage_execution.py:727` and `:2469`; then drive each stage's own
acquisition and **observe both acquired tokens** — each carrying its Job's
composed lifetime and exceeding 900, with the review stage's token its own
generation rather than the implementation's.

### Unchanged and retained

All four product paths byte-unchanged (`24f27d77…`, `7db36ee6…`,
`70cc0806…`, `765c1567…`); **zero product edits this claim**. The combined
candidate is the 31-path composition plus my five paths, manifest and delta
unchanged except the docstring. All five link-reversion arms from claims354527
and 354566 are retained in their own evidence directories and were not
repeated, as the review directed.

Still owed: both stages reaching actual acquired tokens; exact stop/cancel;
cleanup and unknown holds; reopened-store original timing with no duplicate
effects or revival; and the joined owner-produced cause through durable
capture, `/7` status and the packaged report.

No live instance, engine, provider or credential; no deployment, recovery,
migration or shared import; no version-control mutation — reads only. Measured:
focused 0.213s. Prior spending retained unchanged.
