# W170387 final-acceptance evidence index and documentation draft

Advisory Work W173922, claim 173954, baton.claude via baton.impl.
**Read-only pass. Nothing was executed:** no test, probe, provider, model,
engine, image build, Git mutation or worker. No product, test, original dossier
or main `DEPLOYMENT.md` was edited. This is advice for the future W170387
acceptance owner and is **not independent acceptance**.

Observations are live-tree, dated 2026-09-15 under claim 173954, and provisional.

## 1. The finding that matters most for an acceptance pass

**The accepted candidates no longer match the working tree, and that is normal —
but it means acceptance must verify against the immutable snapshots, not the
tree.** Measured now:

| Accepted candidate | Files | Match live tree | Match immutable snapshot |
| --- | --- | --- | --- |
| W170380 `candidate-170569.json` | 8 | **0 of 8** | **8 of 8** |
| W170382 `candidate-172672.json` | 17 | **6 of 17** | **17 of 17** |

Both snapshot directories are intact and byte-exact:
`findings/finding-managed-preparation-completion/candidate-170569/` and
`findings/finding-managed-preparation-recovery/candidate-files-172672/`.

The drift is expected — W170385 is actively editing the shared coordinator and
capacity paths under baton.tuner — but **anyone who re-hashes the live tree will
conclude the accepted evidence is gone.** It is not. State the verification
procedure explicitly in the acceptance packet:

    verify candidate-<claim>.json hashes against candidate-files-<claim>/,
    NOT against v12/python/... in the working tree

## 2. Evidence index

### W170380 — closed satisfying (seq 170651)

| Item | Locator |
| --- | --- |
| Accepted candidate | `finding-managed-preparation-completion/candidate-170569.json`, manifest SHA-256 `e3ba732f17fa0efb83f78dd92bb1f3692e14479bc6935389de878e85c2817fa3` |
| Immutable snapshot | `candidate-170569/` — 8 of 8 files match |
| Accepting review | `review-2026-09-14T16-19-56Z.md` (independent, baton.codex) |
| Author record | `PROGRESS.md`, `verification-170569.json`, `baseline-170569.json` |

**Independently accepted**, with the review's own limits preserved: deterministic
engine/provider simulation with a real separate worker process, explicitly *not*
an actual image or live-engine certificate.

### W170382 — closed satisfying (seq 172901)

| Item | Locator |
| --- | --- |
| Accepted candidate | `finding-managed-preparation-recovery/candidate-172672.json`, SHA-256 `b3248a8da92f2b39339144ba07ba810be41d72627a39250f707f191478e63ba7` |
| Immutable snapshot | `candidate-files-172672/` — 17 of 17 files match |
| Accepting review | `review-2026-09-14T22-42-50Z.md` (independent, baton.codex) |
| Acceptance packet | `ACCEPTANCE-172672.md` |
| Owner closure | seq 172901, accepting **reduced** group2 scope |
| Documentation | `DEPLOYMENT-SLICE2-DRAFT.md` (98 lines) |

**A provenance point the index must carry, and I am the interested party so I
state it plainly:** I authored W170382 through candidate-172393 and returned it
incomplete. The **accepted** candidate is 172672, produced by baton.tuner after
owner decisions M172655/M172691/M172730/M172741 superseded the late-identity
design direction. My earlier candidates (172112, 172200, 172286, 172393) are
**author claims and history, not accepted evidence.** An acceptance index that
cited them as accepted would be citing me on my own work.

What the owner actually accepted, per the closure text: manual recovery, the
concrete cleanup and default fixes, and retained evidence. **v13 matrices remain
deferred.**

### W170385 — open, active under baton.tuner (seq 173788)

**No accepted candidate exists.** Current state is author progress only:

- `ledger-170385.json`: **47 rows, 217.061789 s**; steps 46
  (`selected-final-regressions`) and 47 (`final-replay-and-gates`) pass, step 45
  (`late-admission-gates`) failed and is retained.
- Latest independent review: `review-2026-09-15T00-40-22Z.md`.
- Amendments: `PREPARATION-OUTPUT-AMENDMENT-172988.md`,
  `SCHEDULER-COMPOSITION-AMENDMENT-173130.md`; selected scope
  `SLICE3-SCOPE-172905.md`.

**This moves fast.** When I wrote W173847's ADVICE.md roughly an hour earlier the
ledger had 34 rows and step 34 was failing. Any index entry for W170385 must be
re-measured at acceptance time; do not copy these numbers forward.

## 3. Revalidating W173847 ADVICE.md (my own earlier report)

Asked for, and it needs correcting:

| ADVICE.md claim | Status now |
| --- | --- |
| §1 ledger has 34 rows; step 33 passes, step 34 fails | **STALE.** 47 rows; steps 46 and 47 pass. The step-34 case may well be resolved. |
| §2 three `settle_failed_integration` call sites exist | **HOLDS.** Now at `stage_execution.py:2587` (apply) and `:5141` (prepare), plus the `integration_worker.py` prepare site. Line numbers moved. |
| §3 `managed_failure.settled` at `projection.py:120` is tested before the integration observation at `:159` | **HOLDS**, both line numbers unchanged. The ordering argument is intact. |
| §3 conclusion "settlement did not run" for step 34 | **Provisional and probably overtaken.** It described a failure that may no longer exist. Do not carry it into an acceptance packet as a defect. |
| §4 failed-apply-with-target-publication refuses and settles nothing | Structurally unchanged; still worth confirming as intended rather than a gap. |

## 4. Smallest remaining final checks — proposed, not executed

After W170385 completes and is independently accepted:

1. **Re-verify both closed candidates against their snapshots** (§1). Cheap,
   mechanical, and the thing most likely to be done wrongly against the tree.
2. **Re-verify W170385's accepted candidate** the same way once it exists.
3. **One consolidated focused run** over the union of the three slices' selected
   modules, to show they still pass *together* at the accepted bytes rather than
   only in their own claims. Proposed selector shape, from `v12/python` with
   `PYTHONPATH=src:tools:.`:
   `python3 -m unittest tests.tools.test_managed_preparation tests.tools.test_managed_apply tests.job_manager.test_managed_integration_capacity tests.integration.test_managed_storage tests.manager.test_reconciliation_task tests.tools.test_integration_bundle`
4. **A regression baseline for the shared modules** — `tests.tools.test_stage_execution`
   and `tests.tools.test_single_worker` carried **13 pre-existing errors** through
   W170382, baselined by restoring the accepted source bytes and reproducing the
   same count. Re-establish that pairing at final acceptance rather than
   inheriting my number; it is a year-old-style trap to quote a stale baseline.
5. **No broad discovery run.** `unittest discover -s tests` without `-t .` is a
   known trap here: it makes `tests` the top-level directory and produces ~20
   spurious loader `ImportError`s. I hit exactly this and reported an invalid
   full-suite result because of it. If a broad run is wanted, use
   `discover -s tests -t .`.

**Supervise every run**, including experiments: per-run timeout, own process
group, TERM-then-KILL escalation, and record failures as well as passes.

## 5. Provenance and simulation limits to carry into acceptance

State these in the acceptance packet rather than leaving them to the reader:

- **All evidence is deterministic simulated provider/engine evidence** with real
  disposable Authority/Job/Control owners and actual separate worker and harness
  processes. It does **not** establish actual OCI behaviour, image build/pull, or
  model/provider-specific behaviour.
- **The accepted group2 scope is reduced.** Partial-delivery recovery, expanded
  adversarial identity/artifact/custody, causal/timeout/limit, two-Job
  permutations, and expanded uncertain-ending/leader-first/TERM-resistant
  cancellation are **deferred to v13 and unproved — not passed.**
- **Automatic late-identity recovery is superseded**, deliberately, by a visible
  manual-recovery boundary.
- **Author-recorded durations are a recorded subset, not a total.** W170382's
  first three claims ran reversals outside the supervisor with no per-run
  timings. Preserve that unknown; do not reconstruct it.

## 6. Documentation draft — what exists and what is missing

`DEPLOYMENT-SLICE2-DRAFT.md` already covers slice 2 well: selecting the local
preparation path, what a successful preparation means, failure and restart, and
qualification/deferred coverage. **Do not rewrite it.** Its manual-recovery
section is the strongest part and should be the model for the others.

**The gap is a consolidated user-facing view** spanning preparation → apply →
settlement. Proposed wording below. **All of it is proposed and awaits final
acceptance**; the only parts traceable to accepted evidence are marked
**[accepted]**, and everything about apply is **[proposed — W170385 not yet
accepted]**.

> ### Managed integration, end to end
>
> **[accepted]** A managed integration prepares in a container, on a published
> input bundle, under capacity your parent stage already reserved. Preparation
> creates its own child Work, claims it, records and activates a runtime attempt,
> admits capacity, and only then starts a runtime. The parent is never claimed
> while its preparation runs.
>
> **[accepted]** Every step is committed before the step that depends on it, so
> an interrupted sweep resumes rather than repeats. You will not get two child
> Works, two claims, two runtimes or two harness runs from a restart.
>
> **[proposed — not yet accepted]** A reviewed candidate is then applied to the
> target and the outcome is settled. A failed apply refuses its queue entry and
> settles the orchestration without touching the target.
>
> ### When something fails
>
> **[accepted]** A failure is *settled*, not retried. The stage becomes
> `exceptional` and its successors stay blocked. The control plane does not
> reopen an exceptional stage — you decide what happens next.
>
> **[accepted]** If a start failed after creating a runtime, the runtime is
> destroyed, its credential and launch delivery roots are removed, and the result
> directory is **retained** — kept on purpose, because material from a failed run
> is untrusted but may be the only evidence of what happened.
>
> **[accepted]** If a start failed and no runtime was identified, **automatic
> cleanup is unresolved and human inspection is required.** The sweep reports
> that a worker may still exist, along with the known Job, Work, attempt and
> start-operation identifiers, and either the current runtime or an explicit
> "unknown". **Treat an unknown runtime as possibly alive, never as absent.**
> This report and its holds survive restart. Later visibility of the runtime is
> new evidence; it does not rewrite the original failure receipt or authorize a
> second launch.
>
> ### What is not provided
>
> **[accepted]** No automatic late-runtime attachment, cleanup convergence,
> abandonment, or capacity-release procedure. Human cleanup and any subsequent
> release need your own operational authority. A held allocation does not
> self-heal, and that is deliberate: resetting it would reset a failure rather
> than recover it.

## 7. Stale wording and reconciliation

- **Per-claim cumulative caps.** Where any of the three slice dossiers still
  frames cumulative seconds as an allowance, `AGENTS.md` line 95 records the
  2026-09-14 owner ruling that cumulative stopwatch budgets are **not approval**.
  Keep measured durations; drop refusal-on-exhaustion language. Proposed for the
  owning dossiers — I did not edit them.
- **Do not reconstruct deferred matrices.** The acceptance packet should list the
  v13 deferrals by name and stop there. Re-deriving them would reopen scope the
  owner explicitly closed.

## 8. Unresolved decisions for the owner

1. **W170387 is `phase: block` and W170385 has no accepted candidate.** Final
   acceptance cannot begin; the index above will need re-measuring when it can.
2. **Whether "failed apply with a target publication" needs its own observable
   outcome** (carried forward from W173847 §4 — still open).
3. **Whether the consolidated user-facing document lives in a slice dossier or
   eventually in main `DEPLOYMENT.md`.** I was explicitly barred from editing the
   latter and make no recommendation about when that changes.
4. **Whether the 13 pre-existing shared-module errors are in scope for final
   acceptance at all**, or remain a separately owned pre-existing condition.

## 9. Assumptions and limits

- I ran nothing; every behavioural claim comes from reading source, accepted
  reviews and recorded ledgers/logs, and every structural claim is a citation.
- I did not read or alter anything owned by W170385 beyond read-only evidence,
  and did not interrupt the tuner.
- I am the former author of W170382 and have labelled my own superseded work as
  such in §2 rather than indexing it as accepted evidence.
- Nothing here is acceptance of W170380, W170382, W170385 or W170387, and none
  of it changes a release gate.
