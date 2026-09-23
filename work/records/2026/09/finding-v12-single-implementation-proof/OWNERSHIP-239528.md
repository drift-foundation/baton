# File ownership across the three split Jobs

Claim 239653, baton.claude, W239528. Established as owner reroute 239632 and
review 2026-09-22T14-56-01Z require: "Establish exact new file ownership when
W239528 is claimed; this turn grants no concurrent editing right over them."

## The release this ownership rests on

`detail work=W236087` at the start of this claim: `phase: block`,
`agent: null`, `claimed_at: null`, route `baton.decide`. Its active handler
released safely, so there is no concurrent claim to overlap with. W239533 is
also `block` and unclaimed.

## What W239528 owns and may edit

Everything under
`work/records/2026/09/finding-v12-single-implementation-proof/` and nothing
else:

    FINDING.md                    the owner's split decision, appended
    PLAN.md                       current action
    PROGRESS.md                   this implementer's record (new this claim)
    DIAGNOSIS-239528.md           the fault and cleanup diagnosis
    OWNERSHIP-239528.md           this file
    PROVIDER-QUESTION-239528.md   the one real-provider question
    OPERATOR-239528.md            the bounded owner command
    SELECTIONS-239528.json        its operands
    baseline.py                   the implementation-only supervisor
    baseline_bindings.py          its packet composer
    test_baseline.py              focused deterministic verification
    test_baseline_bindings.py     the generated packet, driven
    verify.py                     the measurement that writes the receipt
    verification-1.json/.log      that receipt

## What it READS and must not edit

`work/records/2026/09/finding-v12-managed-session-resume/` in full. It is
W236087's, that Work is blocked rather than closed, and it continues into the
resume proof. In particular `supervisor.py`, `packet_bindings.py`,
`test_supervisor.py`, `test_packet_bindings.py`, `test_generated_packet.py`,
`LIVE-RUN-239365.md`, `live-239365/`, the 239485 operator/selections/packet
records, `verification-20/21` and every append-only review stay exactly as the
preservation handoff left them.

**Proved, not asserted.** All ten digests recorded in that dossier's
`review-evidence-239589.json` were re-read at the end of this claim and every
one matches, including `PACKET-INPUTS-239485.json` at
`5672cb741f3437a73ca33c9ba378e6af9181df7f765a739831bf4f906f16cb40`.
`verify.py` records the five ancestor digests in its own receipt, so a later
drift is visible rather than silent.

`work/records/2026/09/finding-v12-independent-review-proof/` is W239533's and
is untouched: this claim created no file in it and read only its `FINDING.md`
and `PLAN.md` for the split ordering.

## Why the code was COPIED rather than imported

`baseline.py` and `baseline_bindings.py` are W236087's `supervisor.py` and
`packet_bindings.py` reduced to one stage. Importing them across the dossier
boundary was considered and rejected: W236087 continues to change for the
resume proof, and a baseline whose proof moved whenever the resume Job edited a
shared module would not be a baseline. The split ruling says to run these
separately, so they are separately bound.

The cost of that decision is duplication, and it is paid explicitly:
`verification-1.json` records the digest of every ancestor file, so a reviewer
can diff the two and see exactly what was removed -- the review stage, the
correction, the restore mode, the dispositions and the `review_invocations` and
`corrections` bounds -- and what was added, which is the proposal attribution.

## No product byte was changed

No file under `v12/` was edited under this claim. This Job needs no product
change: the adapter's commit ownership, the `_unmoved` refusal and the
manager's own cleanup journal are all existing behaviour, and the baseline
reads them rather than altering them.

The one product constraint this Job ran into is recorded rather than routed
around: `stage_execution._held_workers` refuses a deployment naming no review
worker -- "a Job that cannot be produced or independently reviewed serves
nothing" -- so `baseline_bindings` CONFIGURES a review worker and never submits
a review stage. See `FINDING.md` and the module docstring.

## Claim 240196 -- files added under this claim

    test_entrypoints.py           the two operator entrypoints, run as commands
    records_240196.py             this claim's dossier writer
    verification-2.json/.log      the 77-check receipt

`OPERATOR-239528.md`, `SELECTIONS-239528.json`, `baseline.py`,
`baseline_bindings.py`, `test_baseline.py`, `test_baseline_bindings.py`,
`verify.py`, `FINDING.md`, `PLAN.md` and `PROGRESS.md` were edited under this
claim and are this Job's own.

**The reviewer's files were not touched**: `review-2026-09-22T15-32-51Z.md`,
`review-evidence-239808.json`, `review-tests-239808.log`,
`review-probes-239808.py` and `review-probes-239808.json` belong to baton.rvpc
and are append-only history. `verification-1.json/.log` is claim 239653's
receipt and is kept beside the new one rather than replaced.

All ten inherited W236087 digests in that dossier's
`review-evidence-239589.json` were re-verified byte-identical again under this
claim.

## Claim 242687 -- the first product change this Job has made

Files added:

    DIAGNOSIS-242687.md           the expired-credential diagnosis
    OPERATOR-FAILURE-242687.md    the bounded failure-path command
    PRODUCT-CHANGE-242687.json    before/after digests of every changed path
    live-242687/                  read-only copy of the live failure evidence
    test_failure_path.py          the retained-bytes regression
    pin_242687.py, records_242687.py, finish_242687.py
    verification-3.json/.log

PRODUCT paths edited, pinned in PLAN before the first edit:

    v12/python/src/baton_v12/job_manager/review_driver.py
    v12/python/tools/stage_execution.py
    v12/python/tests/manager/test_claude_context.py

Nothing else under `v12/` was touched. `v12/worker/claude_agent.py` is
deliberately unchanged: the adapter answered correctly.

`/home/sl/baton-runs/single-implementation-239528/run` was READ and not
modified, and no store belonging to it was opened. The W236087 dossier and its
ten preserved digests are unchanged; the reviewer's own files for both earlier
reviews are untouched.

## Claim 242906 -- packet corrections only; no product byte changed

Files added:

    MANAGER-SOURCE-242687.json     manifests both snapshots
    SELECTIONS-FAILURE-242687.json the composed failure-path input
    snapshot_242687.py             prepares and VERIFIES the successor snapshot
    test_successor_snapshot.py     the three-part exercise of it
    records_242906.py              this claim's dossier writer
    verification-4.json/.log       the 100-check receipt

`OPERATOR-FAILURE-242687.md`, `PLAN.md`, `PROGRESS.md` and this file were
edited under this claim.

OUTSIDE the checkout, and both are new rather than modified:

    /home/sl/baton-runs/single-implementation-242687/manager-source
        the successor snapshot, 106 files

PRESERVED and NOT written to, verified under this claim:

    /home/sl/baton-runs/managed-correction-236087/manager-source
        still the pre-correction bytes W236087's packet is bound to
    /home/sl/baton-runs/single-implementation-239528/
        the first run's stores, runtime and evidence; its ending and cleanup
        are unfinished and that is the evidence

Nothing under `v12/` was touched under this claim; the three paths changed
under claim 242687 still carry their accepted after-hashes. The reviewers' own
files for all three reviews are untouched.

## Claim 243174 -- supervisor corrections; no product byte changed

Files added:

    live-success-243174/        read-only copy of the successful run's evidence
    pin_243174.py               the findings and pin, recorded first
    records_243174.py           this claim's dossier writer
    test_no_progress.py         the live stall, reproduced
    verification-5.json/.log    the 112-check receipt

Edited: `baseline.py`, `snapshot_242687.py`, `FINDING.md`, `PLAN.md`,
`PROGRESS.md`, this file.

**Nothing under `v12/` was touched.** The three product paths accepted under
claim 242687 still carry their accepted after-hashes.

PRESERVED and verified under this claim:

    /home/sl/baton-runs/single-implementation-success-239528/run
    /home/sl/baton-runs/single-implementation-242687/manager-source  (--verify)
    /home/sl/baton-runs/managed-correction-236087/manager-source
    /home/sl/baton-runs/single-implementation-239528/

## Claim 243284 -- R1/R2/R3; no product byte changed

Added: `OPERATOR-SUCCESSOR-243284.md`, `SELECTIONS-SUCCESSOR-243284.json`,
`records_243284.py`, `verification-6.json/.log`.

Edited: `baseline.py` (R1), `snapshot_242687.py` (R2),
`baseline_bindings.py` (R3 bounds), `test_no_progress.py`,
`test_successor_snapshot.py`, `PLAN.md`, `PROGRESS.md`, this file.

**Nothing under `v12/` was touched.** The three product paths accepted under
claim 242687 still carry their accepted after-hashes.

PRESERVED and verified: the bound successor snapshot and its manifest
(`--verify`), the W236087 snapshot, and all three earlier run roots. The R2
regressions build only into temporary directories and remove the manifests
they create.

## Claim 243990 -- remaining R2/R3; no product byte changed

Added: `test_successor_packet.py`, `records_243990.py`,
`verification-7.json/.log`.

Edited: `snapshot_242687.py` (R2 provenance),
`OPERATOR-SUCCESSOR-243284.md` (R3), `test_successor_snapshot.py`,
`PLAN.md`, `PROGRESS.md`, this file.

**Nothing under `v12/` was touched.** The historical
`MANAGER-SOURCE-242687.json` is unchanged and still records claim 242906. The
R2 regressions build only into temporary directories and remove the manifests
they create.

## Claim 244098 -- the custody mode, fixed at creation

Added: `pin_244098.py`, `records_244098.py`,
`PRODUCT-CHANGE-244098.json`, `verification-8.json/.log`.

Edited: `test_no_progress.py`, `PLAN.md`, `PROGRESS.md`, `FINDING.md`, this
file.

PRODUCT paths edited, pinned before the first edit:

    v12/worker/claude_agent.py                      PROVIDER_UMASK
    v12/python/tests/manager/test_claude_context.py the fixture repair removed
    v12/python/tests/manager/test_claude_agent.py   the focused adapter case

The three paths accepted under claim 242687 are unchanged and still carry their
accepted after-hashes. No custody check was weakened. No retained evidence was
chmodded, moved or deleted.

## Claim 244216 -- the corrected image and its packet

Added: `pin_244216.py`, `image_244216.py`, `IMAGE-ARTIFACT-244216.json`,
`SELECTIONS-SUCCESSOR-244216.json`, `OPERATOR-SUCCESSOR-244216.md`,
`records_244216.py`, `verification-9.json/.log`.

Edited: `test_successor_packet.py`, `verify.py`, `FINDING.md`, `PLAN.md`,
`PROGRESS.md`, this file.

**No file under `v12/` was edited.** The accepted adapter source is the one
review 2026-09-23T03:19:21Z accepted and is unchanged.

OUTSIDE the checkout:

    NEW        baton-v12-claude-worker:w239528-244216
                   sha256:c862c055c6430addc918ca078a9e4d55f6bd8173ed9c9878a8ad9d6cad334ca2
    PRESERVED  baton-v12-claude-worker:w236087-236349
                   sha256:2e9e84ff23319778760d5b22c70d543d4290931510a3ab3ecf40bcdaad7456bd
                   re-read and unchanged; neither retagged, rebuilt nor removed

W244180's dossier (`finding-v12-review-job-preparation`) and W239533 were not
touched.

## Claim 244292 -- the parameterized preparation step

Added: `prepare_instance.py`, `test_preparation.py`, `records_244292.py`,
`verification-10.json/.log`.

Edited: `OPERATOR-SUCCESSOR-244216.md`, `verify.py`, `PLAN.md`, `PROGRESS.md`,
this file.

**No file under `v12/` was edited, and no image was rebuilt.** Both images,
both manager-source snapshots and every consumed instance are untouched.
`OPERATOR-SUCCESSOR-243284.md` is kept as it stands: its block is historical
and the successor page now says why not to reuse it.

## Claim 244389 -- R1/R2 and the documented entrypoint

Added: `records_244389.py`, `verification-11.json/.log`.

Edited: `prepare_instance.py`, `test_preparation.py`,
`OPERATOR-SUCCESSOR-244216.md`, `verify.py`, `PLAN.md`, `PROGRESS.md`, this
file.

**No file under `v12/` was edited, and no image was rebuilt.** All five product
paths carry their currently accepted after-hashes; both images, both
manager-source snapshots, every consumed instance and all ten inherited
W236087 digests were re-read and are unchanged. The entrypoint test builds only
inside a temporary directory and copies -- never moves or chmods -- the
disposable Authority it opens.
