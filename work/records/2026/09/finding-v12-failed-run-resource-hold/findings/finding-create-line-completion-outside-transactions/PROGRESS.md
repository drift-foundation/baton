# Implementation progress — W301404

## Claim 301428 — the correction, and the one property it could not keep

READ FIRST: `detail work=W301404` (phase active, handler baton.claude, binding revision 1 at this
dossier), `thread thread=2b077949-T301404` (one message, 301404, read in full), this dossier's
`FINDING.md` and `PLAN.md`, the consumer's `review-2026-09-28T22-22-49Z.md` and
`probe_create_line_299768.py` under `work/records/2026/09/finding-v12-startup-failure-fresh-packet`.
Revalidated the source against current bytes before editing, as the FINDING requires.

### The baseline, reproduced before anything changed

    probe_create_line_299768.py   1 FAIL, 0.246s
    the last observation printed: lstat of
    `<scratch>/storage/.baton-review-lines/line-c71b47a3.../checkout` with in_transaction=True

So the reached violation is present on the bytes I started from, and the connected positive still
completes -- which is exactly why it survived: the happy path passes while the lock is held across a
filesystem walk.

### The correction

`v12/python/src/baton_v12/worker_manager/review_cycles.py` (51b3787c64a2, 4114 lines),
`create_line` only. Three acts left the completion transaction, in the order W194457 fixed:

    `_object` re-measurement, `workspaces.prove_line_integrity`, `workspaces.establish_line_access`
    now run BEFORE `store.transact`. The callback keeps a journal read (the state, for a diagnostic a
    caller can act on) and the one conditional write
    `UPDATE ... SET line_device=?, line_inode=?, state='idle' WHERE line_id=? AND state='materializing'`,
    which is what actually excludes a second completion.

WHAT PROTECTS THEIR LIFETIME, since they no longer sit under the lock:

    EXCLUSIVE PREPARATION is unchanged -- the row is committed `materializing` by the reservation and
    only a completion that still finds it in that state may publish.
    THE PUBLISHED OBJECT IS THE PROVED OBJECT: the identity is measured before the proof and MEASURED
    AGAIN after the access change, so the pair that reaches the row is the pair both acts were
    performed against.
    A REPLAY IS STILL FREE OF EFFECTS. This needed a second correction I did not anticipate: with the
    filesystem acts outside, `store.transact` skipping its callback for a recorded operation no longer
    skips them, so a late re-entry established access twice. Measured, by
    `test_late_creator_cannot_reprovision_an_admitted_line` counting 2 where the property is 1. The fix
    is the same early-replay branch the non-`materializing` case already used, asked one moment
    earlier: `store.replay("review-line.create:<id>", signature, ...)` before the filesystem block,
    validating the object and returning the recorded result.

### The property I could NOT keep, stated as a failure rather than dressed up

`tests.manager.test_review_cycles.StableLineLifecycle`
`.test_root_replacement_before_initial_publication_never_provisions_replacement` FAILS:
`'idle' != 'materializing'` at `tests/manager/test_review_cycles.py:1171`.

That case swaps the line root for a fresh directory INSIDE a hook on `store.transact` -- that is, at the
instant the completion transaction begins, after every act that is now outside it. No ordering of
outside-the-lock checks can observe a swap injected at that instant; only a check inside the transaction
can, and that check is the DB-1 violation this Work removes. The two requirements meet here.

WHAT STILL HOLDS on that path, measured on the same run:

    the swap IS detected and the creation REFUSES -- the case's `assertRaises(ContractRefusal)` passes,
      through the post-commit `_validate_line_object`;
    the replacement is NEVER provisioned -- its mode is still `0o700`, the case's own assertion at
      line 1170, so no permission act reached the new tree;
    every consumer re-validates the object (`grant_writer` and the boundary readers call
      `_validate_line_object`), so the published row is unusable rather than merely suspect.

WHAT DOES NOT HOLD: the line is left `idle` instead of `materializing`. The refusal arrives after the
flip rather than before it, which is publication ahead of the final proof and is the thing the FINDING
tells me not to do quietly. I am not weakening the assertion to make it pass, and I am not choosing
between the designs below on my own, because each changes something the FINDING pinned:

    (A) ACCEPT THE NARROWED PROPERTY: detection, no provisioning of the replacement, consumer refusal,
        and the state label left `idle`. One assertion in that case changes, with the reason recorded.
    (B) TWO-STEP COMPLETION: commit the measured device/inode while still `materializing`, re-measure
        outside, then flip conditional on `state='materializing' AND line_device=? AND line_inode=?`.
        Strictly stronger for every window EXCEPT the injected instant above, which it also cannot see,
        and it adds a second recorded operation to the creation lifecycle.
    (C) KEEP THE CHECK UNDER THE LOCK: preserves the case exactly and does not correct DB-1.

I read the FINDING as selecting against (C). Between (A) and (B) the difference is a durable protocol
change, which the owner's bounded selection did not name, so I am passing this back for the choice
rather than making it inside a claim.

### Required evidence, with what covers each

    connected no-I/O-under-transaction regression -- `probe_create_line_299768.py` 1 PASS, 0.257s,
      unchanged bytes, run with the consumer's own selector environment; the connected positive still
      completes inside it.
    positive creation and no-effect replay -- `test_line_and_each_operation_replay_exactly`,
      `test_late_creator_cannot_reprovision_an_admitted_line` (now 1 establish, not 2).
    conflicting operands/object refusal -- `test_line_materialization_crash_resumes_only_the_recorded_
      operands` (operation-collision on other operands), `test_authority_and_work_identity_isolate_
      line_custody`, `test_creating_a_line_PROVES_its_integrity_before_granting_access` (the hardlink
      the walk alone refuses), `test_replaced_line_refuses_launch`.
    safe competing and stale completion -- `test_writer_race_has_one_winner_and_reserved_line_survives_
      cleanup`, `test_live_child_and_stale_progress_refuse_without_mutation`,
      `test_changed_current_checkpoint_cannot_admit_a_stale_correction`.
    interrupted preparation/access effect -- NEW, mine:
      `test_an_INTERRUPTION_after_the_access_act_leaves_a_recoverable_line` in
      `tests/manager/test_review_cycles.py` (f4e39e5bf4c1). It kills the act after the permission pass
      really ran, then asserts the line stays `materializing`, the `0o2775` effect IS on disk rather
      than pretended away, and a re-entry completes to `idle` at the same path with the effect intact.
    the mechanism assertion that had to move -- `test_establishing_access_is_serialized_before_idle_and_
      never_repeated` asserted `in_transaction` was TRUE during the permission act, which is the
      violation itself. It now asserts no transaction is open and keeps every other assertion
      (state still `materializing`, exactly once, final mode `0o2775`).

### Measurements

    probe_create_line_299768.py                 1 FAIL 0.246s before -> 1 PASS 0.257s after
    tests/manager/test_review_cycles.py         163 tests, 1F (the root-replacement case above)
    discover -s tests/manager                   4550 tests, 142F+74E+21 skipped, 228s. The W285465
                                                baseline on these suites is 141F+74E; the delta is
                                                exactly the one case named above, so nothing else in
                                                that tree moved.
    discover -s tests/job_manager               915 OK, 11.3s
    tests/manager/test_private_line_access_engine  4 skipped (needs an engine; none run)

No live engine, provider, build or deployment; no canonical store opened; disposable fixture stores
only. No Git mutation of any kind, and no file outside the two named above and this PROGRESS was
edited. Parent and consumer evidence untouched.

## Claim 301527 — both P1s closed: the stale effect and the publication mismatch

READ: `detail work=W301404` (active, handler baton.claude), `work-events after=301507` (claim 301510,
pass 301524), `review-2026-09-29T02-32-53Z.md`, `review_late_preparation_301510.py`,
`candidate-2026-09-29T02-32-53Z.sha256`, the updated FINDING/PLAN, and T301404 (no new messages).
Source revalidated before editing: `review_cycles.py` 8224b8e07aa1 (4294 lines),
`test_review_cycles.py` a4e1c9b39c62 (3183 lines).

### P1 — the stale creator's external effect, closed at the act that has one

The review is right that my early replay only narrowed a window, and its probe shows exactly how: the
`materializing` row is SHARED, so a competitor admitted during this creator's integrity proof settled
the line, took a writer, and this creator still permissioned the tree while the line was `writing`.

    A SECOND CREATOR IS NOT REFUSED, and that is deliberate — I tried it first and it is wrong. An
    exclusive in-process hold does refuse the competitor, but a second `create_line` for the same
    Authority and Work is PROTOCOL-ADMITTED: the recorded recovery path is one, and
    `test_line_materialization_crash_resumes_only_the_recorded_operands` is that property. Refusing the
    competitor also made the reviewer's probe ERROR on the refusal instead of asserting its property,
    which is the shape of an answer that moves a failure rather than fixing it.
    SO THE GUARD IS ON THE ACT WITH AN EFFECT. `prove_line_integrity` only READS, so a stale prover
    changes nothing. `establish_line_access` is the effect, and it is now preceded by
    `_settled_elsewhere`, one short `BEGIN IMMEDIATE` over journal reads only (the row state and this
    line's own operation record) that answers what the loser does INSTEAD: replay the recorded creation,
    or refuse when the line left `materializing` with nothing recorded. Neither answer touches the
    filesystem, and the decision is one atomic read rather than two a competitor can slip between.
    `review_late_preparation_301510.py` 1 PASS, 0.007s, unchanged reviewer bytes.
    MY OWN CASE OVER THE SAME SCHEDULE, because their probe asserts one fact and there are three:
    `test_a_STALE_creator_replays_instead_of_permissioning_a_live_line` asserts NO permission act runs
    at all, the stale creator returns the competitor's recorded creation rather than a second one, and
    the live writer's line is still `writing` with its own `0o600` entry untouched.
    THE HONEST LIMIT: this closes the reproduced deterministic schedule and every in-process one,
    because the check and the act are adjacent with no yield between them in this manager. A
    cross-process competitor that commits in the instant between that atomic read and the `fchmod` is
    not excluded by it; excluding that instant needs either a lock held across the filesystem act
    (DB-1) or filesystem-level exclusion, and neither is selected here. I am naming it rather than
    implying the window is gone.

### P1 — the publication mismatch, answered with a durable state instead of a relabel

The root can be replaced in the instant between the last measurement and the completion commit, and no
check outside a transaction can observe that instant. The mismatch was always DETECTED, by the
post-commit object validation; what was wrong is what it left behind. It now WITHDRAWS the publication
it just made:

    `_withdraw_publication` is DB-only and CONDITIONAL on `state = 'idle' AND revision = 0 AND
    current_checkpoint_id IS NULL`, so it can only pull back the publication this call made and never a
    line a writer has advanced. The refusal still propagates.
    THE OBJECT MEMBERS GO WITH IT because the SCHEMA says so, not because I preferred it: the table's
    CHECK is `state = 'materializing' AND line_device IS NULL AND line_inode IS NULL`, and keeping them
    raised `IntegrityError`. Measured, corrected, and recorded in both the code and the case.
    RECOVERY IS THEREFORE EXPLICIT: `_published_recorded_line` re-applies the RECORDED creation's own
    members to a withdrawn row when the early replay finds one, which is idempotent and is not a second
    creation; the validation still decides whether the object is really there.
    `test_root_replacement_before_initial_publication_never_provisions_replacement` now PASSES on its
    original assertions, and my
    `test_a_WITHDRAWN_publication_leaves_a_recoverable_materializing_line` adds what its assertions do
    not reach: the withdrawn row's members are NULL, the replacement is never provisioned (`0o700`),
    and restoring the object lets the recorded creation republish to `idle` at the same path.
    SO THE PROTECTED LIFETIME, stated plainly: the object is measured, proved and permissioned while the
    line is exclusively `materializing`; the settlement is conditional on that state; and if the object
    named at settlement is not the object present, the durable state is `materializing` with no
    measurement — a line no consumer treats as usable and the recorded creation can republish over.

### Verification

    probe_create_line_299768.py                  1 PASS 0.223s   (connected DB-1, unchanged bytes)
    review_late_preparation_301510.py            1 PASS 0.007s   (unchanged reviewer bytes)
    tests/manager/test_review_cycles.py          165 OK, 1.6s    (163 -> 165; the two new cases)
    tests/manager/test_checkpoint_profiles.py     42 OK
    tests/manager/test_provider_context.py        65 OK
    tests/job_manager/test_review_driver.py      163 OK
    discover -s tests/job_manager                915 OK, 11.2s

No broad manager/job rerun this claim — the review asked me not to repeat known counts, and the four
focused consumer suites above are the ones that own `create_line`'s callers. Exception-based
interruption remains exception-based: it proves re-entry with effects retained, NOT process death, and
that limit stays recorded. No live engine, provider, build, deployment or canonical store; disposable
fixture stores only; no Git mutation; no file edited outside `review_cycles.py`,
`test_review_cycles.py` and this PROGRESS.

## Claim 301607 — the exclusion is the hold, not a closer read

READ: `detail work=W301404`, `work-events after=301583` (claim 301591, pass 301604),
`review-2026-09-29T02-43-58Z.md`, `review_access_boundary_301591.py`,
`candidate-2026-09-29T02-43-58Z.sha256`, updated FINDING/PLAN, T301404 (no new messages). Source
revalidated before editing. Now `review_cycles.py` b91a77bc4f53 (4312 lines),
`test_review_cycles.py` a6fab1653809 (3193 lines).

### What the review settled, and what it says about my last two attempts

Both of my previous answers were wrong in opposite directions, and the new probe is what shows it:

    THE ATOMIC READ WAS NOT A CRITICAL SECTION. `review_access_boundary_301591.py` switches at the
    ACTUAL `fchmod`, after `_settled_elsewhere` has committed, and the stale permission act ran anyway.
    No read is close enough, because the effect is a syscall rather than a transaction -- so "another
    closer read" was never going to be the answer, exactly as the review said.
    AND REFUSING A LIVE COMPETITOR IS SAFE. I had built that first, then removed it because the
    historical probe drove its competitor to completion and errored on the refusal. The review is
    explicit that the old probe ADMITTED a competitor to EXPOSE the defect, which is not a requirement
    to admit a still-live one, and that non-DB exclusion mechanisms are not prohibited. So the hold is
    reinstated and is now actually consulted.

### The correction

`_PREPARING` is the exclusion rather than a record: a second `create_line` that names a line this
manager is already preparing is REFUSED, and the hold spans the external acts and the settlement and is
released in a `finally`.

    IT DOES NOT BLOCK RECOVERY, which is the distinct schedule the review named. The hold is
    in-process, so a manager that DIED mid-preparation leaves `materializing` with no live hold and
    `test_line_materialization_crash_resumes_only_the_recorded_operands` still resumes; the interruption
    case still recovers with its access effect retained.
    `_settled_elsewhere` STAYS, for what the hold cannot see: a competitor in another process, and the
    ordinary case where the line was settled before this creator reached its effect. It answers replay
    or refusal without touching the filesystem.
    THE WITHDRAWAL STAYS as delivered at 301527, with the schema-required NULL members and the
    republication path.

### Honest results, including the probe that no longer passes

    review_access_boundary_301591.py           1 PASS 0.006s   (the new boundary schedule)
    probe_create_line_299768.py                1 PASS 0.222s   (connected DB-1, unchanged bytes)
    review_late_preparation_301510.py          1 ERROR 0.006s  -- and this is the expected consequence,
      not a silent regression. Its competitor is refused with "another preparation of this line is in
      flight in this manager", and because it drives that competitor to completion the refusal
      propagates out of its own creator call. The property it asserted (`"writing"` never observed at a
      permission act) HOLDS -- the act never happens at all. The review pre-authorized this outcome:
      safe refusal is allowed and the historical probe is preserved unchanged. I did not edit it.
    tests/manager/test_review_cycles.py        165 OK, 1.6s
      `test_a_COMPETING_creator_is_refused_while_this_one_holds_the_line` REPLACES my previous
      stale-replay case, which asserted the behaviour the review has now superseded. It drives the
      competitor at the same interval both reviewer probes use and asserts four facts: the competitor
      refuses while the holder is inside its own preparation, the holder still completes, the line is
      published exactly ONCE (one permission act, one row), and a live-work entry below the root keeps
      its own mode.
    tests/manager/test_checkpoint_profiles.py   42 OK
    tests/manager/test_provider_context.py      65 OK
    tests/job_manager/test_review_driver.py    163 OK
    discover -s tests/job_manager              915 OK, 11.1s

No broad unrelated suites, no maintenance restoration, no live engine/provider/build/deployment, no
canonical store, disposable fixture stores only, no Git or graph mutation. Files changed this claim:
`v12/python/src/baton_v12/worker_manager/review_cycles.py`,
`v12/python/tests/manager/test_review_cycles.py`, and this PROGRESS. Child unaccepted and W257627
remains blocked until independent acceptance.

## Claim 301648 — the hold made per-resource, and taken before the first effect

READ: `detail work=W301404`, `work-events after=301622` (claim 301624, pass 301646),
`review-2026-09-29T02-49-10Z.md`, `review_hold_scope_301624.py`, the updated candidate manifest, and
T301404 (no new messages). Source revalidated before editing. Now `review_cycles.py` 706a2e138ea2
(4348 lines), `test_review_cycles.py` c5de1d97a8fa (3289 lines).

### Both defects the review measured, and they were both mine

    THE HOLD WAS TAKEN TOO LATE. It sat after `profile.materialize`, which IS an external
    preparation effect -- it creates the checkout. So a competitor that the hold later refused had
    already materialized: two `materialize` calls where the property is one. A refusal that arrives
    after the effect it is supposed to exclude has not excluded anything, and that is the same
    mistake as the closer read, one layer up.
    THE KEY WAS THE HANDLE. `id(store)` is an object identity, and the reviewer opened a SECOND
    `ControlStore` on the same file in the same process and walked straight past it -- two handles,
    one resource, no exclusion at all.

### The correction

    PER-RESOURCE KEY: `_line_resource` keys the hold on `os.path.realpath(store.database)` -- the
    database this handle was opened on, which every handle on that store agrees about -- paired with
    the line. A handle carrying no database path falls back to itself, and that is STATED as a limit
    rather than hidden: a store constructed directly around a connection names no file, and every
    supported deployment opens through `ControlStore.open`, which records the path.
    ATOMIC: `_hold_preparation` tests and adds under one `threading.Lock`, so two threads cannot
    both believe they hold it. The lock guards the REGISTRY only and is never held across a
    filesystem act or a transaction.
    TAKEN BEFORE THE FIRST EFFECT AND RETAINED THROUGH VALIDATION: it is acquired immediately after
    the line identity and path are derived -- before the reservation, before `materialize` -- and
    released in a `finally` that wraps materialization, the proof, the permission act, the
    settlement and the publication validation. The body moved into `_reserved_line` so that
    `finally` covers every path out, including the refusals.
    RECOVERY IS UNCHANGED, and it is why the hold stays in-process: a manager that died leaves the
    row `materializing` with no live hold, so the crash-resume and interruption schedules still
    recover. `_settled_elsewhere` and the conditional settlement still cover what a hold cannot see.

### Evidence, including the two the review asked me to add

    review_hold_scope_301624.py                2 PASS 0.010s  (unchanged reviewer bytes: the
                                               refused competitor never materializes, and the
                                               second handle cannot bypass)
    review_access_boundary_301591.py           1 PASS 0.005s  (unchanged)
    probe_create_line_299768.py                1 PASS 0.223s  (connected DB-1, unchanged)
    review_late_preparation_301510.py          1 ERROR 0.007s -- unchanged from the last claim and
                                               for the same pre-authorized reason: its competitor
                                               is refused and it drives that competitor to
                                               completion. I have not edited it.
    tests/manager/test_review_cycles.py        167 OK, 1.6s (165 -> 167)
      NEW `test_a_SECOND_HANDLE_on_the_same_store_cannot_bypass_the_exclusion` -- a real second
        `ControlStore.open` on the same path, refused, with one materialization.
      NEW `test_an_INDEPENDENT_line_is_not_blocked_by_another_preparation` -- the control, because
        an exclusion keyed too coarsely would serialize every line in the deployment, which is a
        worse defect than the one it fixes. A different Work's line completes while one is held.
      UPDATED `test_late_creator_cannot_reprovision_an_admitted_line` -- its competitor now refuses
        BEFORE materializing, and the case asserts the two facts it has always been about (one
        permission act, the live worker's `0o600` file untouched) plus `materialize_calls == 1`.
      TWO MISTAKES IN MY OWN NEW PROBES, recorded because they were mine: the hook set its flag
        AFTER the nested call, so the independent line refused against ITSELF; and it called the
        PATCHED `prove_line_integrity`, which recursed. Both fixed by binding the original and
        flagging before the call.
    tests/manager/test_checkpoint_profiles.py   42 OK
    tests/manager/test_provider_context.py      65 OK
    tests/job_manager/test_review_driver.py    163 OK
    discover -s tests/job_manager              915 OK, 11.1s

No broad unrelated suites, no maintenance restoration, no live engine/provider/build/deployment, no
canonical store, disposable fixture stores only, no Git or graph mutation. Files changed this claim
are the same two plus this PROGRESS. Child unaccepted; W257627 stays blocked.
