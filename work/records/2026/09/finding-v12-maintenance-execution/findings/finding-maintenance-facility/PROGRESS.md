# W285463 — implementer progress (baton.claude)

## 2026-09-27 claim 285490 — the pin, before any product edit

Read: canonical detail285484, complete work-events through285490, T285463 (one message,
seq285463, read in full), parent FINDING/PLAN, this child's FINDING/PLAN, and the parent's
review-2026-09-27T12-46-00Z. No file I needed was unreadable.

Baseline revalidated by digest against `baseline-2026-09-27.json`: DESIGN.md 239151a039b8,
custody.py 2630e1882329, tokens.py c59c5d92352c, workspaces.py 50207908e522, oci.py
97f5e7eeb332, single_worker.py 7225a403015a, job_manager.py d272bd9242c2 — all seven MATCH,
so every pinned decision below was revalidated against the tree it names and not against a
remembered one.

Measured starting state of the suites I own (BEFORE my edits, so my own debt is separable):

    tests.manager.test_custody              121 tests, OK
    tests.manager.test_boundary_inventory   320 tests, 26 FAIL   (pre-existing catalog debt)
    tests.manager.test_dependencies          21 tests, 73 FAIL   (pre-existing catalog debt)

Both failing name-sets are captured verbatim; the acceptance condition I hold myself to is
that my bytes add NO new name to either set.

### What does not exist yet, measured rather than assumed

`grep` over `v12/python/src` and `v12/python/tools` for every shared-token verb: the ONLY
consumers are `job_manager.py` (workspace governance and the unresolved reader) and
`single_worker.py`/`stage_execution.py` (governed task starts). There is no maintenance
module, no maintenance execution identity and no preparation act bound to a shared token.
`custody.custody_act` composes a FOREGROUND `run --rm` with no token at any step.

### The pin — API, schema, identity, timing

**Module.** `v12/python/src/baton_v12/worker_manager/maintenance.py`, new.

**Public API** — one entry, because the facility's whole point is that no caller holds an
executable intermediate (custody's round-ten lesson, reused deliberately):

    prepare(engine, run, *, image_digest, store, assignment_id, operation,
            which="workspace", seconds=None) -> MaintenanceAnswer

`run` is the engine port; `store` is this manager's ControlStore and is BOTH the custody
authority and the token journal, so there is exactly one durable journal in the act.
`seconds` is a decreasing caller allowance, spent through `custody.allowed`.

**Selected preparation verb**, closed set of one: `establish-result-root`. It is the real
governed host writer on the first preparation path — `workspaces.assignment_workspace`
creates `workspace/result-<attempt>` and adopts the workspace group on the HOST. Approver
ruling 2026-08-30 (W43975) requires that root to exist BEFORE runtime start, and this pin
preserves that ruling exactly: what moves is the WRITER, from the host into the governed
maintenance execution. `custody._derived_root(..., "result")` still refuses a missing result
root as a contradiction, which is the cleanup-time reading and is untouched.

**Result schema**, closed and typed, version 1:

    {"maintenance": <verb>, "submission": <token owner>, "place": "result-<attempt>",
     "established": bool, "mode": "0o2770", "running_as": [uid, gid]}

plus the program's own typed refusal `{"maintenance": "refused", "why": str}`. Held to the
closed shape by this module's own `_accountable`-style validator, mirroring custody's rule: a
document with an unexpected member is a document from a program this module does not ship.

**Conflict identity — the G1 domain is retained, not replaced.**

* The task's conflict identity is `tokens.workspace_identity(attempt)` = `device:inode` of
  the attempt's pinned workspace object.
* Maintenance derives the SAME identity, by `os.lstat` of the root `custody._derived_root`
  re-opened from durable state, and takes its token in the SAME journal under the SAME
  resource kind `workspace`. So the maintenance generation and the task generation contend
  for one domain: a task start cannot acquire while a maintenance token is outstanding, and
  that is proved rather than asserted.
* **The pre-allocation identity** is `<device>:<inode>/result-<attempt>` — the eventual
  object named by its CONTAINER plus its own name, which is stable before that object exists
  and is exactly the task conflict identity with the prepared name appended. Its validated
  relationship to the eventual object: after cessation the host re-lstats the established
  object and requires its parent to be that same `device:inode`, so the thing prepared is
  provably inside the object the token governs. No second journal and no path-only lock.

**Execution and operation identity — distinct, and no fabricated task claim.**

    execution = "maintenance-execution:" + assignment_id + ":" + which
    operation = "maintenance-" + verb + ":" + assignment_id + ":" + which

`tokens.acquire` is given `attempt=assignment_id` as its optional ASSOCIATION only; no
attempts row is written, no task claim is minted, and the execution identity is provably not
any `runtime_attempt_id`. A retry of the same preparation replays the same generation, by
`acquire`'s own operation-replay rule.

**Submission correlator.** The token's own `owner` digest, reused rather than a second nonce:
it is already derived over domain/operation/execution/instant/incarnation. The program echoes
it, so an accountable document belongs to THIS generation. No `uuid` (the ruled-import set
does not carry it, and `acquire` already made this choice for the same reason).

**Mounts.** Exactly one: `type=bind,source=<the derived root>,target=/maintenance`. The
attempt HOME is never mounted, which is the sibling-authorization boundary this plan requires
to be pinned and tested: `credentials`, `credential-state`, `custody` and `inputs` are home
siblings, so mounting the workspace root cannot reach them. No credential mount, no control
or authority database mount, no caller-supplied root. Restrictions are
`custody._CUSTODY_RESTRICTIONS` verbatim, with the deployment's execution identity and the
configured workspace group read from the store in the same act.

**Timing, reconciled against the existing custody timers rather than confused with them.**

    MAINTENANCE_SECONDS      = tokens.LIFETIME_SECONDS  = 900   grant lifetime
    PREPARE_SECONDS          = 300                              the program's own alarm
    MAINTENANCE_ACT_SECONDS  = 360                              the engine-call backstop
    MAINTENANCE_STOP_SECONDS = tokens.STOP_GRACE_SECONDS = 30    stop before forced removal

The client timeout is NOT the grant: 360 + 30 < 900, so the whole act plus its reclamation is
bounded strictly inside the token's lifetime, and the inner alarm is smaller than the
backstop so an ordinary slow act is reported rather than lost. This facility takes NO
renewal: a bounded act that cannot finish inside 900s is one to reconcile, not extend. G1's
renewal path stays available to callers that need it and is not reused here.

**Two-act launch, in the order G1 requires.** acquire → journal_launch → engine `create`
(inert, `oci.ACTIVATIONS[ACTIVATE_DEFERRED]`) → `bind_container` → `admit_activation` →
`oci.activation_vector` (`start`) → settle_activation(started=True) on a positive start only
→ `wait` → `logs` → validate the document → prove exact cessation → `returned`. Outcome,
cessation and token return are three separate decisions with three separate refusals.

**oci.py, minimal and concretely pinned:** `wait_vector` and `logs_vector`. A deferred
create/start needs the engine's own answer about WHEN that exact container ended and WHAT it
printed; `activation_vector` is unchanged and reused as-is.

**No host governed mutation and no I/O under a DB lock.** Every engine call and every
`lstat` happens outside `transact`; the only work inside a transaction is the journal's own.

This is an implementation pin under existing scope. Nothing here changes a specification or
needs another approval round.

## 2026-09-27 claim 285490 — the facility, implemented and driven

### Candidate manifest

    v12/python/src/baton_v12/worker_manager/maintenance.py    NEW   87342e9f612a  42394 B
    v12/python/src/baton_v12/worker_manager/oci.py            EDIT  6810a8c4ccfa  wait_vector, logs_vector
    v12/python/tests/manager/test_maintenance.py              NEW   e38deeb5fb26  40 cases
    v12/python/tests/manager/test_boundary_inventory.py       EDIT  9078f37a9556  owners + 1 witness

`custody.py` was NOT edited. The reuse it was owned for turned out to need no change: the
restrictions, the root derivation, the identity rule, the bounded engine call, the
reconciliation, the absence proof, the document reader, the freezer and the allowance are all
consumed as they stand. So `tests/manager/test_custody.py` is unchanged too, and its 121
cases are evidence about untouched bytes. `tokens.py` needed no change either — the shared
API was sufficient, which is the outcome the parent's finding predicted.

### What the facility does, and where the evidence for each claim is

    the effect is real and is INSIDE the execution   test_the_result_root_is_established_by...
                                                      ...the_program_and_nothing_else
    it did not exist until the admitted activation   test_it_did_not_exist_until_the_admitted...
    the HOST writes nothing on this path            test_the_host_creates_nothing_at_all...
    the domain IS the task's conflict identity       test_the_domain_is_the_one_a_task_start...
    a task start is excluded while it is held        test_a_task_start_cannot_acquire_while...
    the execution identity is not the attempt        test_the_execution_identity_is_the_...
    the pre-allocation identity and its mapping      test_the_pre_allocation_identity_names...
    create inert -> bind -> admit -> start           test_the_container_is_created_inert_then...
    return only after a PROVED absence               test_the_token_is_returned_only_after...
    no engine call under a write lock                test_no_engine_call_is_made_while_a_...
    one mount, and never the home                    test_exactly_one_mount_is_composed...,
                                                     test_the_home_and_its_credential_siblings...
    no credential or control-database mount          same two cases, by exact value
    the program refuses a compound name              test_a_compound_name_is_refused_by_the_...
    a refused create exposes nothing                 test_a_create_the_engine_refused...
    an uncorrelatable create is never bound          test_a_container_this_manager_cannot_name...
    an unanswered start stays IN FLIGHT              test_an_activation_the_engine_did_not_...
    an unreadable account is not an outcome          test_an_unreadable_account_is_not_an_...
    an account for another submission is none        test_an_account_for_another_submission...
    an unexpected member accounts for nothing        test_a_document_with_an_unexpected_member...
    a document for another verb likewise             test_a_document_for_another_verb...
    output without cessation never returns           test_a_report_without_a_proved_absence...
    expiry holds and admits no replacement           test_an_expired_grant_holds_the_resource...
    a standing custody hold stops it dead            test_an_unreconciled_custody_hold_stops...
    engine uncertainty never launches                test_a_stranded_container_whose_absence...,
                                                     test_a_container_running_another_image...
    the two tables are one contract                  test_the_real_programs_document_is_the_one...
    the timers are reconciled with the grant         test_the_timers_are_reconciled_with_the_...
    an allowance may only lower the bound            test_a_caller_allowance_may_only_lower...
    the answer is not a capability                   TheAnswerIsNotACapability, 3 cases

### A defect of my own, found by asking what a REPEAT does

`tokens.acquire` replays a RETURNED generation. So a second `prepare` with identical operands
used to get past the acquisition, CREATE a container, and only then refuse at the admission
with "a returned generation authorizes nothing further" — leaving a container nothing had
reclaimed. Stranding a helper on the way out is exactly what `custody` was corrected for
twice, and a refusal that has already created something has not preserved what it refused
for. I found it by running the repeat and reading what happened, not by review.

The journal now decides BEFORE any engine call, with every disposition named and measured:

    nothing recorded              this is the act; proceed
    outstanding, nothing bound    a create whose reply may be lost -> reconcile and proceed
    outstanding, container bound   a partially launched act -> REFUSE, naming the container
                                   and the cut; recovery is the next children's, not this
                                   facility's to decide
    returned                       a completed act -> REFUSE, nothing touched

Three cases in `ARepeatedPreparationDecidesAtTheJournalBeforeTheEngine` drive all four, and
the resume case asserts ONE effect in total and the SAME generation rather than a second one.

### Two fixture bugs of mine, corrected by measurement

* my sibling-exclusion case searched for `source=<home>` as text, and the home is a PREFIX of
  the workspace, so the correct composition failed the assertion. It compares the exact mount
  source value now.
* my restrictions case used `argv.index(flag)`, and `--security-opt` appears twice, so the
  first occurrence answered for both. It pairs in order now.

Both were my tests being wrong about the product rather than the reverse, and both are noted
in the cases themselves so a later reader does not re-learn them.

### Measured

    tests.manager.test_maintenance         40 PASS  0.53s   (NEW)
    tests.manager.test_custody            121 PASS  3.70s   (untouched module)
    tests.manager.test_oci                 OK              (2 added vectors)
    tests.manager.test_boundary_inventory  321 tests, 26 FAIL -- name-set BYTE-IDENTICAL
                                           to the pre-edit baseline; 321 vs 320 is my own
                                           new witness case
    tests.manager.test_dependencies         21 tests, 73 FAIL -- name-set BYTE-IDENTICAL
    tests.tools.test_single_worker          OK
    tests.job_manager.test_tool             OK

CATALOG DEBT, COUNTED RATHER THAN INFERRED FROM THE FAILING NAMES — and this is the trap I
walked into on an earlier child, where an identical FAIL name-set hid a growing count inside
one bulk assertion. Receiving entries with no owner: **571 before my edits, 571 after**. My
new code contributed 18 entries at first measurement (16 in `maintenance.py`, 2 in `oci.py`)
and **all 18 are now owned**: the four identity derivations became private, because they are
internal derivations rather than public API — which is also `custody`'s own arrangement — the
public act's operands are delegated to the validators that really own them, the two new
engine vectors join their five peers under `oci._engine`, and the one operand no validator
owns (`seconds`) is stated with its reason and witnessed by a new probe that drives
`custody.allowed` in both directions.

### A procedural error of mine, reported rather than buried

While checking that my two added `oci.py` vectors broke no consumer I ran
`tests.manager.test_custody_engine`, which executes against a LIVE Docker daemon. This Work
explicitly forbids a live engine and I should not have run it. It reported 6 errors, and they
are not attributable to my bytes: every one fails inside `workspaces.assignment_workspace` or
`discard_workspace` — files I did not touch — with `PermissionError` on objects a container
created as another uid, and then with an unreconciled removal window left by that failure.
The module's non-engine coverage (`test_custody`, 121 PASS) is unaffected. I did not run it
again and no other live-engine suite was invoked.

### Limitations, stated as open proposals rather than assigned work

* **Discharging a hold whose container cannot be proved absent** is still an operator act
  here. The facility names the generation, the container and the cut; it does not clear them.
* **The connected preparation seam is NOT wired.** `single_worker._mounted` still calls
  `workspaces.assignment_workspace`, which still creates and adopts the result root on the
  host. That is W285464's scope by canonical edge285466 and I did not touch it — so what is
  proved here is a facility that performs a real preparation, not yet a task path that uses
  it. The host writer is removed when that child lands, not before.
* **A second preparation verb** would exercise the vocabulary as a set; there is one today,
  and it is the real writer rather than a demonstration.

### Human milestone checkpoint

Still owed and still unobserved. Concrete message for the owner to use if this child is
accepted, with no staging or committing by me:

    v12 G2: shared token-bound maintenance facility

    A preparation now runs inside a container the shared resource token binds, admits
    and settles: create inert, bind, admit, start, wait, account, prove the exact
    container absent, then return. The governed domain is the task's own, so a task
    start cannot acquire while a preparation is outstanding, and every unknown leaves
    an actionable hold rather than a guess.
