# W285464 — implementer progress (baton.claude)

## 2026-09-27 claim 286467 — the pin, and the first connected slice

This file did not exist before this claim; the finding and PLAN both say so, and the reviewer
was right not to treat its absence as missing evidence. I create it here at implementation
start.

Read: canonical detail286457 before claiming, complete work-events for W285464 (create285464,
edges285466/285468, wake286438, reviewer claim286441, reviewer pass286456), T285464 in full
(seq285464 scope handoff and seq285819 owner prompt about the tuner packet), the bound
FINDING and PLAN, and the advisory
`work/records/2026/09/finding-v12-maintenance-child-preparation/HANDOFF-PACKET.md`.
No file I needed was unreadable.

**Predecessor revalidated by digest.** All 19 entries of the accepted facility manifest
`candidate-2026-09-27T14-48-27Z.json` recomputed and MATCH, including maintenance.py
2c141d062c88, workspaces.py 0e0368a0bff4, custody.py 2f88554e782d, oci.py 6810a8c4ccfa,
test_maintenance.py 126e25ddfb8f and DESIGN.md 239151a039b8. W285463 is closed satisfying.
That is inherited evidence about the facility and says nothing yet about connected behaviour.

**Measured starting state**, before my edits:

    tests.manager.test_maintenance          79 PASS
    tests.manager.test_boundary_inventory   323 tests, 26 FAIL  (residual debt of other modules)
    tests.manager.test_dependencies         21 tests, 70 FAIL   (same)
    unowned receiving entries               571
    tools/single_worker.py                  7225a403015a, UNCHANGED by me this claim

**Confirmed against the tree, not remembered:** `_SingleWorker._mounted` (single_worker.py:1910)
calls `workspaces.assignment_workspace` on the host and only then composes the source boundary;
`_prepared` (1945) pins the boundary identity and runs `_input` (1440), which publishes the task
document (`_published_task`, 1509) and calls `workspaces.compose_input_root`, which freezes the
input root and the home; `_attempt_scratch` (1634) adopts a scratch the allocation provisioned.
So the reviewer is right that inserting `establish-result-root` after host allocation would not
satisfy this child.

### The pin, before any product edit

**The selected path** is the ordinary no-context/no-review one: `_mounted` → `_prepared` →
`_input`, with `self.stage is None`. Persistent line, review, context and restoration
compositions are out of scope by the finding and I have not touched them.

**The governed writers this child must move**, read off the code rather than assumed:

    assignment_workspace   home, HOME_ENTRIES, workspace/result-<attempt>, group adoption
    source_mountpoint      the input source mountpoint inside the input root
    _published_task        the exclusive task document, its fsync/fchmod, refusal unlink
    compose_input_root     input.json + assignment.json, then the freeze of root and home
    _attempt_scratch       revalidation only -- the scratch is provisioned by the allocation

**Operation vocabulary.** `PREPARATIONS` gains `allocate-assignment-roots` beside the accepted
`establish-result-root`. The verb decides which root is mounted (`MOUNTED_ROOT`), and a caller
that names another root is refused rather than re-pointed.

**Result schema**, version 1, closed and typed per verb:

    allocate-assignment-roots: {version, submission, place, established, entries, mode,
                                running_as}

`entries` is the home layout the program established, compared by the host against
`workspaces.HOME_ENTRIES` plus the manager-derived result name — a report naming another layout
is not an account of this allocation.

**The mounted root is the configured STORAGE, and the sibling boundary is the pin.** An
allocation cannot act inside an attempt root that does not exist, so what is mounted is the
parent. A shared parent is not authority over siblings: the program receives ONE name, derived
by the host from the durable attempt identity, refuses any name that could leave its own subtree
(separator, traversal, absolute, `.`/`..`), creates nothing else, and the host proves afterwards
that what appeared is exactly that subtree. `custody.CUSTODY_ROOTS` is deliberately NOT widened;
`maintenance.MAINTENANCE_ROOTS` adds `storage` and the window readers use that set.

**The pre-allocation conflict identity and its mapping to the task's object** — the thing the
review asked to be pinned before edits:

* identity `<storage device>:<storage inode>/<attempt>`, stable before the home exists,
  derivable after, per deployment and per attempt, never global;
* while the object does not exist, the exclusion carrier is the per-attempt maintenance
  WINDOW, which every workspaces admission and the custody claim already read — and a task
  start reaches one of those admissions, `assignment_workspace`;
* when the object exists, the host records the created workspace root's `device:inode` and the
  exact `workspace:<device>:<inode>` domain in the durable settlement. That record IS the
  mapping: a later reader holding the receipt compares the task's own domain against it;
* the task token is unchanged — `tokens.workspace_governance` still contends for the workspace
  object. No second token system, no global serialization.

**Timing** is the facility's, unchanged: 900s grant, 300s program alarm, 360s act bound, 5s
reclaim stop, no renewal.

### What landed this claim

    maintenance.py    d4bed3f2d663   the allocate-assignment-roots verb: program branch,
                                     schema, storage-root derivation, pre-allocation identity,
                                     per-verb semantic rules, host subtree confirmation and the
                                     durable mapping in the receipt
    workspaces.py     96c1f9ce987b   the reciprocal window reader now walks MAINTENANCE_ROOTS,
                                     so a standing ALLOCATION window is visible to
                                     refuse_if_held and to all four admissions
    custody.py        9863cbab2d67   same one-line widening in the reciprocal claim read
    test_maintenance.py  78ef6305dcbb   91 cases (was 79)
    test_boundary_inventory.py 1ff0799c22fa   delegations re-pointed to the new owner

Twelve new cases, each named in the suite: the home, entries, result root, group and mode are
established INSIDE the execution; the host creates nothing (live-instrument trap on `mkdir`,
`chmod` AND `chown`); exactly one mount and it is the storage, with a sibling attempt's tree
present and provably untouched and only this attempt's entry appearing; five escaping names
reach no engine; the pre-allocation identity is stable before the home exists; the receipt
records the mapping and it equals the domain `tokens.workspace_identity` answers for an attempt
row; a standing allocation window refuses `assignment_workspace`, `refuse_if_held` and a removal
admission; a well-formed report for a home nothing created is NOT confirmed; a report naming
another layout settles nothing; a verb cannot be pointed at another root; a second allocation of
one attempt is refused rather than repeated; and the vocabulary, mount table and schema are one
set with custody's pair unwidened.

### What this claim did NOT do — the exact remaining scope

**This is a partial slice returned for review, not a completed child.** `single_worker.py` is
byte-identical to the accepted baseline (7225a403015a) and no H case is claimed:

1. **The wiring.** `_mounted` must call the facility instead of performing the host allocation,
   which needs the worker's engine capability available at that point and the split of owner
   validation/admission from the governed effects in `assignment_workspace`.
2. **The remaining writers.** Source mountpoint, `_published_task`, `compose_input_root`'s
   documents and freeze, and refusal cleanup are still host-side. The allocation verb is the
   first of these effects, not all of them.
3. **H1–H9** in `tests/tools/test_single_worker.py`: the real composed path with real disposable
   stores and an injected engine distinguishing maintenance from task containers (H1), the
   authority-gate negatives (H2), both admission orders at the composed seam (H3), prepared-object
   replacement before task acquisition (H4), fresh-handle replay without a second effect (H5),
   unknown maintenance endings blocking task admission (H6), host-mutation traps over the whole
   set of moved writers (H7), no-DB-transaction-during-external-work with a second connection
   making unrelated progress (H8), and the created maintenance/task mount vectors compared as
   vectors (H9).
4. **`source_boundary.py`** is untouched; whether the mountpoint migration needs it is a pin I
   have not made yet.

### Measured, this claim

    tests.manager.test_maintenance          91 PASS 1.254s   (was 79)
    tests.manager.test_custody              OK
    tests.manager.test_workspaces           OK
    tests.manager.test_intake               OK
    tests.manager.test_oci                  OK
    tests.manager.test_boundary_inventory   323 tests, 26 FAIL -- name-set BYTE-IDENTICAL
    tests.manager.test_dependencies          21 tests, 70 FAIL -- name-set unchanged
    unowned receiving entries               571, RE-COUNTED, none in maintenance.py
    facility probes review_failed_unknown / review_exit_status / review_allocation_first /
      review_exclusion_v2                   all still pass on these bytes

`tests/tools/test_single_worker.py` was NOT run: I changed neither it nor `single_worker.py`,
and running it would not be H-case evidence. No live engine, no `test_custody_engine`, no daemon
contact, no deployment, no cleanup.

### Human milestone checkpoint

Predecessor checkpoint 56431e14 is observed and inherited. This child has no accepted delivery
yet, so it carries no milestone of its own; the truthful WIP message for the tree as it stands:

    WIP v12 G2: ordinary allocation moved into the maintenance execution

    The attempt home, its entries and the result root are now established inside the
    admitted maintenance execution over a narrowly mounted storage parent, with the
    program confined to one host-derived name and the host proving the subtree
    afterwards. The receipt records the pre-allocation identity's mapping to the
    workspace object the task's own token will name. The connected wiring at
    _mounted, the remaining staged writers and the H1-H9 proofs are not done.

Commit identity unobserved; no staging, no commit, no other repository mutation by me.


## 2026-09-27 claim 286595 — confinement is the mount, and what that costs

Read: detail286587 before claiming, events after286467 (my pass286564, reviewer claim286569,
reviewer pass286586), T285464 through286584 including the owner clarification message, the
reviewer's review-2026-09-27T15-11-34Z.md, OWNER-ISOLATION-20260927.md, the refreshed
FINDING/PLAN and candidate-2026-09-27T15-11-34Z.json. Nothing unreadable. Reproduced the probe
FIRST: **1 FAIL 0.020s**, `commonpath(source, sibling) == source`.

### The review and the owner are right, and my pin was wrong

I mounted the configured STORAGE writable and argued that a host-derived name plus an
untouched-sibling assertion confined the act. It does not. A bind mount has no sub-path, so
every sibling attempt — credentials included — was inside the writable source, and "this
program did not touch them" is a statement about one cooperative program's manners rather than
about what the container could reach. My own vector comment claiming credential siblings are
absent was false for that verb. **Confinement is the mount or it is nothing.**

### What changed

    MOUNTED_ROOT[allocate-assignment-roots]   the attempt's OWN home, not the storage
    MAINTENANCE_ROOTS                          ("workspace", "result", "home")

The mount is `<storage>/<attempt>` and nothing above it, so sibling isolation is a property of
the boundary. The program now acts directly inside `/maintenance` — the home — and there is no
sibling in its filesystem view to reach by any name. The pre-allocation identity is unchanged
and still read from the CONTAINING storage, which is what makes it derivable before the object
exists.

### THE ONE HOST SYSCALL, reported rather than waived

`--mount type=bind` refuses a source that does not exist, so **one empty directory must appear
before the act can be confined to it**. This manager now creates exactly that: `os.mkdir` at
mode `0o700`, no group, no content, inside the maintenance WINDOW and AFTER the token is
acquired, recorded in the durable receipt as `cradle: "created" | "present"`, and adopted rather
than replaced if a real directory of this manager's is already there.

**I am not calling that a clean win, and this is the exact incompatible operation the review
asked me to report rather than paper over.** The stated goal for this path is that the host
writes nothing governed. With the mechanisms available to this child there are three ways out
and only one is mine to take:

1. the host creates the empty cradle under the window and token — what I implemented, and what
   makes the enforced boundary possible today;
2. the deployment provisions per-attempt directories in advance — outside this child's scope
   and a deployment/ops change;
3. an engine feature that binds a SUB-PATH of a mount — `--mount type=bind` has none; Docker's
   `volume-subpath` applies to named volumes, not bind sources.

If (1) is not acceptable, the operation that is incompatible is precisely "create the empty
per-attempt directory a confined bind mount requires", and it needs the owner's ruling between
(2) and a stated relaxation. I have not proposed relaxing anything, and every GOVERNED effect —
the six home entries, the result root, the modes, the group adoption — is inside the execution.
Measured, not asserted: the host performs exactly one `mkdir` and **zero** `chmod` and `chown`
calls on this path.

### The misleading test is replaced by the enforcement it should have been

`test_the_mount_EXCLUDES_every_sibling_attempt` asserts the reviewer's own assertion — the
sibling is NOT a descendant of the bind source — for the named sibling and for every other entry
in the storage, plus that the source is this attempt's home and not the storage.
`test_the_HOST_MAKES_EXACTLY_ONE_EMPTY_DIRECTORY_AND_NOTHING_ELSE` replaces my "host creates
nothing" case with the truth: positive instrumentation records every `mkdir`, `chmod` and
`chown`, the recorded sets are compared exactly, and the receipt's `cradle` member is checked.

**And a witness of mine had to change with the closed set.** The boundary-inventory witness
listed `home` as a value naming no root; `home` is a root now, so leaving it there would have
asserted that a real root refuses. It uses `storage` — the name I first chose and deliberately
did not keep — instead.

### Measured, this claim

    reviewer review_mount_scope_20260927.py   BEFORE 1 FAIL 0.020s -> AFTER OK 0.020s
    tests.manager.test_maintenance            91 PASS 1.267s
    tests.manager.test_custody                OK
    tests.manager.test_workspaces             OK
    tests.manager.test_intake                 OK
    tests.manager.test_oci                    OK
    tests.manager.test_boundary_inventory     323 tests, 26 FAIL -- name-set BYTE-IDENTICAL
                                              (27 first, from my own stale witness; corrected)
    unowned receiving entries                 571, re-counted, none in maintenance.py
    four facility probes                      all still pass on these bytes

    maintenance.py              b338fcb9bacf  103497 B
    workspaces.py               96c1f9ce987b  unchanged this claim
    custody.py                  9863cbab2d67  unchanged this claim
    tools/single_worker.py      7225a403015a  UNCHANGED, still the accepted baseline
    tests/manager/test_maintenance.py         c1f54ab6025e  104135 B, 91 cases
    tests/manager/test_boundary_inventory.py  743190c6ffff  844207 B

### Remaining scope, unchanged from my previous handoff

1. The wiring at `_mounted`/`_prepared`; `single_worker.py` is still untouched.
2. Source mountpoint, `_published_task`, `compose_input_root`'s documents and freeze, and
   refusal cleanup, all still host-side.
3. H1–H9 in `tests/tools/test_single_worker.py`; none claimed.
4. Whether `source_boundary.py` is needed for the mountpoint migration — still unpinned.

### Human milestone checkpoint

Predecessor 56431e14 inherited; this child has no accepted milestone. Truthful WIP:

    WIP v12 G2: allocation confined to the attempt home; connected preparation pending

    The ordinary allocation now runs inside a maintenance execution whose mount is the
    attempt's own home, so no sibling attempt is inside the writable bind. The host's
    only remaining effect on this path is the one empty directory a confined bind mount
    requires, created under the window and token and recorded in the receipt; that
    operation is reported for a ruling rather than waived. Wiring, the remaining staged
    writers and H1-H9 are not done.

Commit identity unobserved; no staging, no commit, no other repository mutation by me.


## 2026-09-27 claim 286789 — the owner reversed the model; the superseded bytes are withdrawn

Read: detail286783 before claiming, events after286595 (my pass286664, reviewer claim286666,
reviewer pass286679, **owner reroute286782**), T285464 through286584, review-2026-09-27T15-24-51Z.md,
the refreshed FINDING and PLAN including the new entry "owner selects host-side initial
preparation", the updated `v12/DESIGN.md` (digest cfbfbb3b320d, 62486 B) at **TOK-7's new
initial-preparation exception**, **HOST-1** and **§19.1**. Nothing unreadable.

### What the owner selected, and what it means for my last two claims

TOK-7 now carries an explicit initial-preparation exception: the single Host manager MAY
allocate a fresh private attempt's directories, create source mountpoints, publish
task/input/assignment files and set initial permissions before job-container handoff, and **no
maintenance container is required for this phase**. §19.1 supersedes the September 26
container-only allocation rule. The conditions that remain: exclusive ownership and current
claim/eligibility; no job container reaching the resources until preparation completes, is
durably recorded and its identity revalidated before task admission; all external I/O outside
DB transactions; **interrupted or timed-out preparation must not permit launch or reuse while
any host writer can still complete**; restart reconciles partial state and uncertain writers;
deadline expiry alone does not prove cessation; and after handoff the exception grants no host
mutation authority.

So the direction of my previous two claims is withdrawn by the owner, not by me: the
`allocate-assignment-roots` verb existed only to move an effect that is now legitimately the
host's, and the `_cradled` host `mkdir` — which the reviewer correctly blocked under the
then-current TOK-7 — is moot because the whole allocation stays host-side.

### What I did this claim: withdraw the superseded product bytes

I removed the allocation verb, its program branch, its schema entry, the storage/home root
kinds, `check_maintenance_root`, `_mounted_root`, `_allocation_identity`, `_cradled`,
`_allocated`, the per-verb mount table, the receipt's `cradle` member and the twelve tests of
that model, and I reverted the reciprocal-reader widenings in `workspaces.py` and `custody.py`
and the re-pointed declarations in `test_boundary_inventory.py`.

**Verified by digest against the accepted facility manifest** `candidate-2026-09-27T14-48-27Z.json`:

    workspaces.py                0e0368a0bff4   BYTE-IDENTICAL to accepted
    custody.py                   2f88554e782d   BYTE-IDENTICAL to accepted
    tests/manager/test_maintenance.py         126e25ddfb8f   BYTE-IDENTICAL to accepted
    tests/manager/test_boundary_inventory.py  db019ed19a31   BYTE-IDENTICAL to accepted
    maintenance.py               5221fd9f595c  83463 B   accepted is 2c141d062c88 at 83462 B

**maintenance.py is functionally restored but ONE BYTE larger than the accepted file, and I am
not claiming byte-identity.** I rebuilt the object-confirmation block by hand from the earlier
reading rather than from the original bytes, and one byte of whitespace or comment residue is
left that I could not locate. The reviewer holds the accepted candidate and can diff it exactly;
behaviourally the suite is back to the accepted 79 cases with no additions.

`tools/single_worker.py` is still 7225a403015a, the accepted baseline, and has never been
edited by me.

### Two reviewer probes are now unrunnable, and that needs saying plainly

`review_mount_scope_20260927.py` and `review_host_allocation_20260927.py` both import
`TheOrdinaryALLOCATIONHappensInsideTheExecution`, the class I withdrew, so they now fail at
IMPORT rather than on an assertion. Those artifacts are immutable and I did not edit them. Their
findings stand as history: the first proved my shared storage bind exposed sibling attempts (I
corrected that), and the second proved `_cradled` performed a host `mkdir` before container
creation (which the owner's amendment now permits as ordinary host preparation). Both concerns
are moot for the selected model because the host performs the allocation outright.

### The revised pin — what H1–H9 must prove under the host model

Revised from the container model, mapped to the owner's conditions rather than to a maintenance
lifecycle:

    H1  the ordinary claimed path prepares on the HOST and starts the task: claim/eligibility
        first, exclusive preparation ownership, durable completion record, identity
        revalidation, then task token acquisition and inert create/bind/admit/start
    H2  expired offer, lost claim race and stale assignment reach the authority gate and
        produce no preparation effect and no task create
    H3  competing allocation/removal/cleanup/adoption/custody admissions against a live host
        preparation, both orderings, one winner, loser without effect, unrelated attempt free
    H4  prepared workspace/source/checkpoint replaced after completion and before task
        acquisition -> refused before any task create, original evidence retained
    H5  same preparation re-entered from a fresh store handle -> no repeated effect; changed
        operands refuse
    H6  INTERRUPTED OR TIMED-OUT preparation -> no launch and no reuse while any host writer
        could still complete; restart reconciles partial state; a deadline is not cessation
    H7  every governed host writer is accounted for durably -- allocation, mountpoint,
        publication, freeze and refusal cleanup -- with positive instrumentation
    H8  no filesystem or engine I/O inside a DB transaction, with a second connection making
        unrelated progress while external work is paused
    H9  the created task mount vectors: input/source read-only, output/scratch exact, sibling
        isolation preserved, no credential or control-database exposure

H6 and H7 are the substance of this child under the revised contract: today an interrupted host
preparation leaves partial state whose completion nothing durably records, and that is the
defect the revalidation must find or disprove.

### Remaining scope — all of the implementation

Nothing of the host-model implementation is done. In order: the durable preparation-completion
record and its revalidation at task admission; the unfinished/uncertain-writer block on launch
and reuse; the `_mounted`/`_prepared` revalidation and any concrete defects found there; then
H1-H9 in `tests/tools/test_single_worker.py`. `source_boundary.py` unpinned.

### Measured, this claim

    tests.manager.test_maintenance          79 PASS 1.134s  (the accepted set, no additions)
    tests.manager.test_custody              OK
    tests.manager.test_workspaces           OK
    tests.manager.test_oci                  OK
    tests.manager.test_intake               OK
    four facility probes                    all OK on the restored bytes
    two handoff probes                      unrunnable by import, accounted for above

### Human milestone checkpoint

Predecessor 56431e14 inherited; this child has no accepted milestone. Truthful WIP:

    WIP v12 G2: superseded container-allocation bytes withdrawn after owner reversal

    The owner amended TOK-7 to permit host initial preparation, so the allocation verb
    and its cradle are withdrawn and the facility files are back at their accepted
    state. H1-H9 are re-pinned against the host model, whose substance is that an
    interrupted or uncertain host writer must block launch and reuse and that
    preparation completion must be durably recorded and revalidated. None of that
    implementation is done.

Commit identity unobserved; no staging, no commit, no other repository mutation by me.


## 2026-09-27 claim 286869 — the durable host preparation account and its admission gate

Read: detail286858 before claiming, events after286789 (my pass286841, reviewer claim286843,
reviewer pass286857), T285464 through286584 (no later message),
review-2026-09-27T15-47-25Z.md and the revised PLAN whose H1-H9 are now the gate. The reviewer
located my one-byte difference exactly — a blank line after `place = os.path.join(ROOT, PLACE)`
inside the embedded program — and verified the withdrawal; I have left maintenance.py at
5221fd9f595c rather than touching it again this claim.

### The pin, before the product edit

**What was missing, read off the tree.** Allocation, removal, cleanup and adoption each carry
an admission window, and `assignment_workspace` closes its own window even when its creation
FAILED — deliberately, because a window left open would block this attempt's cleanup forever.
So after the whole staging sequence there was **no durable fact saying the preparation
finished**, and nothing at the start gate asked. What a restart could see was a filesystem it
could re-read, which is inference about material rather than an account of a writer.

**The record.** `workspaces.PREPARED_KIND = "attempt-preparation.completed"`, one identity per
attempt, body: the attempt, the `device:inode` of the home, inputs and workspace, and the
documents published. Written in `_prepared` immediately after `_input` — the last governed
writer on this path, which publishes the task and the protocol pair and freezes the root — and
before the task is admitted. Idempotent by identity: a restart walking the same preparation
writes the same operands and replays.

**The gate.** `workspaces.require_prepared(control, attempt, roots, what)`, called in
`_prepared` on the fresh-start branch before `request_runtime_start`. Three questions, none
answered by a clock:

1. **can any host writer still finish?** a standing allocation, removal, cleanup or adoption,
   or an unreconciled custody uncertainty, all refuse — expiry proves nothing about cessation;
2. **did the preparation finish at all?** absent account, no launch;
3. **are these the same objects?** the recorded inputs and workspace identities are compared
   against the entries that are there NOW, so a replaced root refuses before any task create.

The gate deliberately DISTRUSTS the `roots` mapping it is handed: it lstats the entries rather
than believing the caller, which is what makes a substituted mapping a refusal instead of a
repin.

### Evidence, and which H cases it reaches

Five new cases in `tests/tools/test_single_worker.py`, class
`TheHostPreparationIsAccountedForBeforeAnyTaskStart`, driven through the real composed
ordinary path with the existing fake engine:

    H1 (part)  the account exists, names this attempt, lists `task.json`, and its workspace
               identity EQUALS `tokens.workspace_identity` of the attempt row -- so what the
               record holds is the object the task's own token contends for
    H6         a standing allocation with no completion refuses the start gate, naming the
               writer that may still be finishing
    H6         an absent account refuses, in the words "recorded no completed host
               preparation ... UNKNOWN"
    H4         the same objects pass, then a substituted workspace refuses with "is not the
               resource that was prepared", and the original record is unchanged -- nothing
               repinned itself
    H5 (part)  a second `record_preparation` with the same operands replays rather than
               recording a second preparation

**A measured correction inside the H4 case.** I first wrote it as `os.rename` of the workspace
inside the home; that is EPERM, because `compose_input_root` freezes the home to `0555` — which
is itself evidence the freeze happened. The case asserts that mode and then drives the
comparison with a different object at the same role, which is what a replacement looks like at
this gate.

### An operational incident of mine, reported immediately

While sweeping consumers I ran `tests.manager.test_input_delivery`, which contains
`DockerConfiguredGroup` with `engine = "docker"` and `required = True` — a **live-engine suite
this Work forbids**. This is the same class of error as the R4 incident and I am reporting it
myself: one execution, 22 failures/errors observed, no rerun.

**Attribution, established without another run.** My `workspaces.py` change is provably
INSERTION-ONLY: removing my inserted block reproduces the accepted digest `0e0368a0bff4`
exactly, byte for byte, so no existing function in that module changed. `record_preparation`
and `require_prepared` are reached only from `single_worker._prepared`, which
`test_input_delivery` does not drive. So my bytes cannot have caused those failures; what I
cannot do without another forbidden run is say what did, and I am not claiming to know.

### Measured, this claim

    tests.tools.test_single_worker            169 PASS 11.6s   (164 before, +5 new)
    tests.manager.test_workspaces             OK
    tests.manager.test_maintenance            79 PASS
    tests.manager.test_custody                OK
    tests.manager.test_intake                 OK
    tests.manager.test_boundary_inventory     324 tests, 26 FAIL -- name-set BYTE-IDENTICAL
    tests.manager.test_dependencies           21 tests, 70 FAIL -- name-set unchanged
    unowned receiving entries                 571, re-counted; the 11 new entries are owned
    tests.manager.test_input_delivery          RUN IN ERROR, see above; not evidence

    workspaces.py                 feaacf66eec7  317893 B  (insertion-only over accepted)
    tools/single_worker.py        864265690c7e  212243 B  (first edit of this file by me)
    tests/tools/test_single_worker.py         ff4a0ed9c5dd  242617 B  169 cases
    tests/manager/test_boundary_inventory.py  762ce8c8d5c8  849570 B
    tests/manager/test_dependencies.py        59a53a3a4a28   61564 B
    maintenance.py                5221fd9f595c  unchanged this claim

### Remaining scope

1. **H1 in full** — a single case that traces claim, preparation, completion record,
   revalidation, token acquisition and inert create/bind/admit/start in one order, asserting
   each hook fired.
2. **H2** the authority-gate negatives; **H3** competing admissions in both orders at the
   composed seam; **H7** positive instrumentation over every host writer including refusal
   cleanup; **H8** no filesystem or engine I/O inside a DB transaction with a second connection
   progressing; **H9** the task mount vectors compared as vectors.
3. **H6 beyond this gate**: an actual interrupted preparation reaching the gate on the next
   tick. The existing crash/restart harness is the vehicle; I have proved the gate's refusals
   but not yet driven a real interruption through it.

### Human milestone checkpoint

Predecessor 56431e14 inherited; child unaccepted. Truthful WIP:

    WIP v12 G2: host preparation is durably accounted for before any task start

    The host now records that its preparation finished -- naming the home, inputs and
    workspace by device:inode and what it published -- and the start gate refuses
    while any host writer could still finish, when no account exists, or when the
    prepared objects are not the ones there now. Five composed cases cover H1 in
    part, H4, H5 in part and H6's refusals; the rest of H1-H9 remains.

Commit identity unobserved; no staging, no commit, no other repository mutation by me.


## 2026-09-27 claim 287050 — preparation ownership spans every writer

Read: detail287039 before claiming, events after286869 (my pass287015, reviewer claim287022,
reviewer pass287038), T285464 through286584 (no later message),
review-2026-09-27T16-13-26Z.md and review_staging_exclusion_20260927.py. Reproduced the probe
FIRST: **1 FAIL 0.102s**, a real removal admitted in the middle of `compose_input_root`.

### R1 — the completion record alone did not supply ownership, and the reviewer is right

The allocation's own window closes when creation ends. So the source mountpoint, the task
publication, the protocol pair and the freeze all ran with nothing excluding a competing
admission, and a gate before the START does not repair that: by then the competitor has already
been admitted over material somebody was still writing.

**`workspaces.PREPARING_KIND = "attempt-preparation.admitted"`** now owns the roots for the
whole preparation. `admit_preparation` takes it in one short `BEGIN IMMEDIATE` — journal reads
only, refusing on a standing removal, cleanup, adoption or custody episode — and the COMPLETION
record closes it. So "admitted with no completion" is exactly "a host writer may still be
finishing here", which is the state the amended TOK-7 says must not permit launch or reuse. An
interruption leaves it open, because a timeout is not an ending.

**Every other admission reads it under its own lock:** `_admitted_allocation`,
`_admitted_removal`, `_admitted_adoption`, `admit_cleanup` and the `refuse_if_held` chokepoint,
plus `require_prepared` at the start gate.

**The holder is exempt, and only for the window it names.** `preparing` is the ordinal
`admit_preparation` answered in this same act, threaded through `assignment_workspace` to the
allocation admission and the chokepoint. A wrong or absent value makes the act STRICTER rather
than weaker — the exemption can only cover the ordinal it names, which one boundary-inventory
witness drives with `None`, `2` and `0`.

### Evidence

Seven new cases in `ThePreparationOWNSTheRootsForItsWholeWriterLifetime`, every act through the
owner's own API, interposed inside the real `compose_input_root` before it publishes:

    removal, cleanup, adoption and a second allocation are each REFUSED mid-staging,
      naming "host preparation ... may still be creating, staging, publishing or freezing",
      and the ordinary path still completes with exactly one start
    an UNRELATED attempt takes its own preparation ownership in the same instant, so the
      exclusion serializes nothing it should not
    the window is closed by the COMPLETION, after which allocation, the chokepoint and
      removal are free again -- not by a clock
    an interrupted preparation leaves the window STANDING: removal, adoption and the
      chokepoint all refuse, and a second `admit_preparation` ADOPTS ordinal 1 rather than
      opening a second window, which is how a restart re-walks the same preparation

The reviewer's probe: **1 FAIL -> OK**.

### Two corrections of mine, both measured

* I first wrote the cleanup/adoption/allocation cases as one subTest loop. The fixture derives
  the attempt identity from the submission, so the second iteration adopted an already-staged
  home, never reached the writer, and failed for that reason rather than on the rule. One
  interposed schedule per case now.
* `admit_preparation` first drew a `uuid` owner nonce. `test_dependencies` refused it —
  `uuid` is outside this package's ruled import set — and the nonce was unnecessary anyway:
  the identity is (attempt, ordinal), the decision is made under `BEGIN IMMEDIATE`, and HOST-8
  already makes the Host manager unique. Removed rather than allowlisted.

### R2 — the excluded live-suite execution, recorded as an accountable checkpoint

Exact command, run once from `/home/sl/src/baton/v12/python`:

    timeout 900 env PYTHONPATH=src python3 -m unittest tests.manager.test_input_delivery

Reported result: `FAILED (failures=19, errors=3, skipped=2)` — 22 of 24 non-skipped outcomes.
Captured output retained in that claim's session record; the failing names I read were in
`DockerConfiguredGroup` (engine `docker`, `required = True`), `TheRuledTrustModel`,
`TheInputRootIsFrozenAndNotOnlyItsFiles` and `TheRootsOwnENTRYIsFrozenToo`. The process COMPLETED
and returned — it was not killed and did not time out. Attributable resources: that module
allocates under its own temporary roots and, for the Docker classes, may create containers; I
performed no inspection of engine state this claim and none is authorized.

**What stays uncertain, and I am not narrowing it beyond the evidence:** the CAUSE of those 22
outcomes. My insertion-only observation supports a narrow code-delta claim and, as the reviewer
says, is not by itself proof that neither my bytes nor the environment contributed. I did not
rerun and will not.

**The preflight I now apply**, pinned here so it is checkable rather than a promise: before
running any suite I have not run before, grep the target module for `engine = "docker"`,
`engine = "podman"`, `required = True` and `subprocess.run([self.engine`, and name explicit
deterministic selectors (module.Class.test) rather than a bare module. Every command this claim
used named either a module I had already run under this Work or an explicit class.

### Measured, this claim

    reviewer review_staging_exclusion_20260927.py   BEFORE 1 FAIL 0.102s -> AFTER OK 0.064s
    tests.tools.test_single_worker                  176 PASS 12.2s   (169 before, +7)
    tests.manager.test_workspaces                   OK
    tests.manager.test_custody                      OK
    tests.manager.test_maintenance                  OK
    tests.manager.test_intake                       OK
    tests.manager.test_boundary_inventory           325 tests, 26 FAIL -- name-set IDENTICAL
    tests.manager.test_dependencies                 21 tests, 70 FAIL -- name-set unchanged
    unowned receiving entries                       571, re-counted; my 6 new entries owned

    workspaces.py                c60dedfb4cd1  327502 B
    tools/single_worker.py       8a4070a1a3bd  213062 B
    tests/tools/test_single_worker.py        cd3d0300625d  251323 B  176 cases
    tests/manager/test_boundary_inventory.py 35b9f33b3e3a  853719 B
    tests/manager/test_dependencies.py       00dc82f4f7a8   61922 B

### Remaining scope

1. **The atomic transition at task admission.** `require_prepared` is still a check BEFORE
   `request_runtime_start`; the reviewer asks for exclusion established AT the admission
   transition. The shared-token `eligible` predicate is the mechanism I intend — the same one
   the facility uses — reached through a governance wrapper in `workspaces.py` so `tokens.py`
   and `attempts.py` stay untouched. NOT DONE.
2. **H1 in full** as one traced case; **H2** authority-gate negatives; **H7** positive
   instrumentation over every host writer including refusal cleanup; **H8** no FS/engine I/O
   inside a DB transaction with a second connection progressing; **H9** task mount vectors.
3. **H6 driven through a real interruption** with the crash/restart harness, rather than through
   the window's API.

### Human milestone checkpoint

Predecessor 56431e14 inherited; child unaccepted. Truthful WIP:

    WIP v12 G2: host preparation owns its roots for the whole writer lifetime

    Preparation ownership is admitted before the first governed writer and closed by
    the durable completion, so allocation, removal, cleanup, adoption and custody are
    all excluded while staging can still write -- and the holder is exempt only for
    the window it names. An interruption leaves the window standing. The atomic
    exclusion at the task-admission transition and most of H1-H9 remain.

Commit identity unobserved; no staging, no commit, no other repository mutation by me.


## 2026-09-27 claim 287243 — the three missing edges, and an ordinal is not authority

Read: detail287233 before claiming, events after287050 (my pass287214, reviewer claim287218,
reviewer pass287232), T285464 through286584 (no later message),
review-2026-09-27T16-41-41Z.md and review_preparation_matrix_20260927.py. Reproduced FIRST:
**3 FAIL 0.017s**, all three edges confirmed before any edit.

### The three gaps, each closed where it was

1. **A standing ALLOCATION did not exclude a new preparation.** My admission checked removal,
   cleanup and adoption and omitted it — reverse-order protection only. `admit_preparation` now
   reads standing allocation, removal, cleanup and adoption, the custody episodes over both
   roots, AND the maintenance window, all inside its own `BEGIN IMMEDIATE`.
2. **A standing preparation did not exclude a CUSTODY claim.** `custody._claim_episode`'s
   reciprocal callback knew about removals and maintenance windows and nothing about this one;
   it reads `_preparation_refusal` now, by derived identity, with no filesystem work under that
   lock. The facility's own `maintenance._conflicting` reads it too, so the edge holds both ways.
3. **An unfinished window was adopted by anybody who asked** — and the reviewer is right that
   this was my worst error of the three. I reasoned from HOST-8, which excludes a duplicate
   MANAGER and says nothing about a second execution, worker, delayed callback or uncertain
   writer inside one. An ordinal anybody receives is not authority to write.

### Adoption now has exactly two grounds, and neither is a clock

* **the same execution** re-entering its own window: `execution` is the caller's own identity —
  the attempt's runtime identity on the ordinary path — compared for EQUALITY. An UNNAMED
  caller never matches, so absence is stricter here rather than permissive, which is what keeps
  the reviewer's own probe's third case refused;
* **a proved ending of the previous manager PROCESS**: the window was opened by a different
  incarnation AND this process holds the exclusive manager instance guard for this storage —
  an OS `flock` this module holds itself, asked of its own `_HELD_GUARDS` cache rather than of a
  caller. The previous process cannot still hold it, and a host preparation writer lives in that
  process, so its death is its cessation. The takeover is RECORDED
  (`attempt-preparation.reconciled`) naming both incarnations and the ground, inside the
  admitting transaction.

Anything else refuses, naming the window, its execution and its incarnation.

### Evidence

Eight new cases in `ThePreparationMatrixIsClosedInBothDirections`, every act through the
owner's own API on isolated stores:

    allocation / removal / adoption / cleanup admitted first    -> preparation refuses,
      each in its own store, and no window is left standing
    a standing preparation                                      -> a real custody claim is
      refused and records NO episode
    a standing preparation                                      -> `maintenance._conflicting`
      names it, so the facility edge holds too
    an unnamed or foreign execution                             -> refused, twice, with
      "an ordinal is not authority to write"; the SAME execution continues
    a held instance guard                                       -> the only other ground:
      refused without it, adopted with it, and the takeover record names both incarnations
      and the guard as the reason

Plus, in the earlier class, my own adoption expectation is rewritten: it asserted unconditional
adoption, which was the regression rather than the rule.

### A fixture lesson I have now hit twice, and named as such

This fixture answers ONE control store per test, so a subTest loop over four competing writers
left the first iteration's window standing and the later acts refused each other instead of
refusing the preparation. One schedule per case, again — the same correction as the staging
cases last claim.

### Measured, this claim

    reviewer review_preparation_matrix_20260927.py   BEFORE 3 FAIL 0.017s -> AFTER OK 0.020s
    reviewer review_staging_exclusion_20260927.py    OK (preserved)
    two facility probes spot-checked                 OK
    tests.tools.test_single_worker                   184 PASS 12.2s   (176 before, +8)
    tests.manager.test_workspaces / test_custody /
      test_maintenance / test_intake                 OK
    tests.manager.test_boundary_inventory            326 tests, 26 FAIL -- name-set IDENTICAL
    tests.manager.test_dependencies                  21 tests, 70 FAIL -- name-set unchanged
    unowned receiving entries                        571, re-counted; the new `execution`
                                                     operand is owned and witnessed

    workspaces.py                 24fe72a5fe89  332918 B
    custody.py                    7a2171f1fd33  140024 B
    maintenance.py                0ce7be13f087   83571 B
    tools/single_worker.py        7fba2a4804fe  213464 B
    tests/tools/test_single_worker.py         6270451b4f1f  260866 B  184 cases
    tests/manager/test_boundary_inventory.py  8f70c25f6732  855664 B
    tests/manager/test_dependencies.py        00dc82f4f7a8   61922 B

Every selector this claim ran was preflighted against `engine = "docker"`, `engine = "podman"`,
`required = True` and `subprocess.run([self.engine` — including the modules I had run before, as
the review directs. No live-engine suite was executed.

### Remaining scope

1. **The atomic task-admission transition**: journal-only eligibility under the shared-token
   acquisition lock, through a governance wrapper in `workspaces.py`. Still NOT DONE.
2. **H1 in full** as one traced case; **H2** authority-gate negatives; **H7** positive
   instrumentation over every host writer including refusal cleanup; **H8** no FS/engine I/O
   inside a DB transaction with a second connection progressing; **H9** task mount vectors.
3. **H6 through a real interruption** with the crash/restart harness rather than the window API.

### Human milestone checkpoint

Predecessor 56431e14 inherited; child unaccepted. Truthful WIP:

    WIP v12 G2: the preparation ownership matrix is closed in both directions

    Allocation, removal, cleanup, adoption, custody and maintenance all exclude a host
    preparation and are excluded by it, at their own atomic admissions. An unfinished
    window is continued only by the same execution or after the previous manager
    process is provably gone -- a held instance lock, never a deadline -- and that
    takeover is recorded. The atomic task-admission transition and most of H1-H9 remain.

Commit identity unobserved; no staging, no commit, no other repository mutation by me.


## 2026-09-27 claim 287394 — continuation is a capability, not a name

Read: detail287370 before claiming, events after287243 (my pass287353, reviewer claim287357,
reviewer pass287369), T285464 through286584, review-2026-09-27T17-01-18Z.md and
review_same_attempt_reentry_20260927.py. Reproduced FIRST: **1 FAIL 0.100s** — the real staging
writer paused, the admission called again with exactly the production operands, and the second
act admitted.

### My third correction of one rule, and the reviewer is right each time

First I adopted any standing window. Then I compared an EXECUTION name — and the production
path passes the attempt identity as that name, so every re-entry for that attempt compared
equal and a second act was admitted while the first could still write. **A name for the same
attempt cannot distinguish a writer's lifetime.**

`workspaces.PreparationOwnership` is now what continues a window: minted only by the admission
that opened it, gated by this module's mint, immutable, compared by type and members. A second
call cannot present it, so it is refused while that window stands. The worker holds one per
attempt in its own composition for exactly as long as it is preparing.

### The guard ground's premise, now stated and driven

The review is right that a held flock plus a different incarnation label is not by itself a
death observation. The takeover now carries the invariant it depends on, written in the code:

    EVERY WRITER OF THIS PATH IS A CALL IN THE MANAGER PROCESS. Host initial preparation
    allocates, stages, publishes and chmods through this module; it starts no container,
    spawns no subprocess and leaves no callback that outlives the call.

Given that, taking the exclusive flock IS an OS observation that no other process holds the
guard, and a process that is gone has no in-process writers left. The invariant is driven rather
than asserted: `test_the_preparation_path_SPAWNS_NOTHING_which_is_the_guard_premise` watches
`subprocess.Popen` between the preparation admission and the completion record and requires zero
spawns, and the comment says plainly that if a preparation ever spawns anything this ground
stops being sound and the takeover must be refused instead.

### Evidence, five new cases

    the reviewer's schedule                 test_a_second_call_with_the_production_operands_is_refused
    a caller cannot mint an ownership       test_a_caller_cannot_mint_an_ownership
    a holder cannot revise one              test_an_ownership_is_not_revised_by_its_holder
    another window's ownership is not this  test_an_ownership_for_another_window_does_not_continue_this_one
    the guard premise                       test_the_preparation_path_SPAWNS_NOTHING...

And my own earlier cases are corrected: the ones that blessed name-equality now assert the
refusal, and two boundary-inventory witnesses that rested on it were updated for the same
reason — a witness asserting a rule the product no longer has is worse than no witness.

### Measured, this claim

    reviewer review_same_attempt_reentry_20260927.py   BEFORE 1 FAIL 0.100s -> AFTER OK 0.064s
    reviewer review_preparation_matrix / staging      OK (both preserved)
    tests.tools.test_single_worker                    189 PASS 12.4s   (184 before, +5)
    tests.manager.test_workspaces / test_custody /
      test_maintenance / test_intake                  OK
    tests.manager.test_boundary_inventory             327 tests, 26 FAIL -- name-set IDENTICAL
    tests.manager.test_dependencies                   21 tests, 70 FAIL -- name-set unchanged
    unowned receiving entries                         571, re-counted; the four new capability
                                                      entries are owned and witnessed

    workspaces.py                            ac18c9d812f0  336922 B
    tools/single_worker.py                   7fc2b6aaaff0  214407 B
    tests/tools/test_single_worker.py        2a3088b21b8e  267911 B  189 cases
    tests/manager/test_boundary_inventory.py b55123dd1fef  859694 B
    tests/manager/test_dependencies.py       e7f8afb74ceb   62256 B

Every selector was preflighted for `engine = "docker"`, `engine = "podman"`, `required = True`
and `subprocess.run([self.engine`. No live-engine suite ran.

### Measured mistakes of mine this claim

* patching `workspaces.admit_preparation` with a wrapper that called the module attribute
  recursed through its own patch — a `RecursionError`, fixed by capturing the honest function
  first;
* the ownership is an object, so every case and witness comparing it to an integer `1` had to
  read `.ordinal`; I found those by running them rather than by reading.

### Remaining scope

1. **The atomic task-admission transition** — journal-only eligibility under the shared-token
   acquisition lock through a governance wrapper in `workspaces.py`. STILL NOT DONE.
2. **H1 in full**, **H2**, **H7**, **H8**, **H9** composed; **H6** through a real interruption
   with the crash/restart harness rather than the window API.

### Human milestone checkpoint

Predecessor 56431e14 inherited; child unaccepted. Truthful WIP:

    WIP v12 G2: only the holder of a preparation may continue it

    Continuation of an unfinished preparation now needs the ownership capability the
    opening admission answered -- a name for the same attempt is not a writer's
    lifetime -- and the only other ground, a gone manager process, carries the stated
    invariant that every writer of this path is an in-process call, driven by a
    no-spawn case. The atomic task-admission transition and most of H1-H9 remain.

Commit identity unobserved; no staging, no commit, no other repository mutation by me.


## 2026-09-27 claim 287546 — the guard ground is withdrawn, and H8's violation with it

Read: detail287540 before claiming, events after287394 (my pass287525, reviewer claim287527,
reviewer pass287539), T285464 through286584, review-2026-09-27T17-26-12Z.md.

### The guard ground is WITHDRAWN, not re-argued

I had allowed a takeover when the window's incarnation differed and this process held the
manager instance guard. The review is right that the premise was never proved: a held flock
establishes PRESENT exclusivity, not that the previous process died or that its writers drained
— and my own fixture only relabelled an incarnation inside one live process, which observes
nothing. A no-subprocess witness says what this path spawns; it does not observe a release.

So the uncertainty is **held**: a standing window whose holder is not here refuses, and the
refusal names what would resolve it.

**That also removed H8's violation.** The reviewer found `admit_preparation` reaching
`_guarding` → `_real` → `os.path.realpath` inside `BEGIN IMMEDIATE`. The guard lookup is gone
with the ground, so the admission's transaction now does journal reads only — and a new case
instruments `realpath` and `lstat` against `connection.in_transaction`, asserts the instrument
is live (a `realpath` inside a deliberate transaction IS recorded), then requires zero records
across an open-and-continue.

### And the one in-process ending that IS provable

Holding every unfinished window forever broke four ACCEPTED restart cases — measured, not
predicted: a resumed composition could never finish a preparation, so no task ever started.
That is not a safe conservatism, it is a stop.

`release_preparation` is the answer, and it rests on a fact rather than a clock: **a writer that
RETURNS has ended, and reaching its own unwinding is the proof.** `_prepared`'s caller now
releases the window in a `finally` unless the completion already closed it, recording that the
writer ended WITHOUT completing — a third fact, distinct from both. Only the holder may release.

**What stays held is exactly the case nothing in this process can speak for:** a manager that
dies mid-write runs no `finally`, so its window has neither a completion nor a release and the
next act refuses as UNKNOWN. That remainder is W285465's restart work, and I am not claiming it.

### Evidence

    the withdrawn ground            test_a_HELD_GUARD_IS_NOT_A_GROUND_and_the_uncertainty_is_held
                                    (guard held, incarnation changed, still refused, window
                                     still standing)
    the provable ending             test_a_RETURNED_writer_releases_its_window_and_that_is_the_
                                    cessation -- only the holder may release, a release is NOT
                                    a completion, and the start gate still refuses afterwards
    H8 at this admission            test_no_FILESYSTEM_read_happens_inside_the_admission_
                                    transaction, with a live-instrument control
    the four restart cases          PASS again, which is how I know the release restores the
                                    accepted behaviour rather than merely looking safer

### Measured, this claim

    reviewer review_same_attempt_reentry / preparation_matrix / staging_exclusion   all OK
    tests.tools.test_single_worker            191 PASS 12.4s   (189 before, +2 net)
    tests.manager.test_workspaces / test_custody / test_maintenance / test_intake   OK
    tests.manager.test_boundary_inventory     327 tests, 26 FAIL -- name-set IDENTICAL
    tests.manager.test_dependencies           21 tests, 70 FAIL -- name-set unchanged
    unowned receiving entries                 571, re-counted; the two release entries owned

    workspaces.py                            7814965abd11  336799 B
    tools/single_worker.py                   d6db22568e99  216576 B
    tests/tools/test_single_worker.py        43dbcf960039  271551 B  191 cases
    tests/manager/test_boundary_inventory.py 7ed3d2bfc6da  860785 B
    tests/manager/test_dependencies.py       995a6afa4d2d   62502 B

Every selector preflighted for `engine = "docker"`, `engine = "podman"`, `required = True` and
`subprocess.run([self.engine`. No live-engine suite ran.

### Remaining scope

1. **The atomic task-admission transition** — journal-only eligibility under the shared-token
   acquisition lock. STILL NOT DONE, and it is now the oldest outstanding item.
2. **H1 in full**, **H2**, **H7**, **H9** composed; **H6** through a real interruption (a
   process that dies mid-write, which is the remainder the release deliberately does not cover).

### Human milestone checkpoint

Predecessor 56431e14 inherited; child unaccepted. Truthful WIP:

    WIP v12 G2: an ended writer releases its window; an unknown one keeps it

    The guard-based takeover is withdrawn as unproved, which also removed a filesystem
    read from inside the admission transaction. What closes a window now is either the
    completion or a release recorded by the writer's own unwinding -- the one in-process
    ending that is provable -- and a manager that dies mid-write leaves the window
    standing and reported UNKNOWN. The atomic task-admission transition remains.

Commit identity unobserved; no staging, no commit, no other repository mutation by me.


## 2026-09-27 claim 287626 — the task token is acquired UNDER the preparation condition

Read: detail287616 before claiming, events after287546 (my pass287602, reviewer claim287604,
reviewer pass287615), T285464 through286584, review-2026-09-27T17-37-14Z.md. The review verified
the guard withdrawal and the removed realpath-under-transaction from source, and named the oldest
outstanding deliverable as this claim's work.

### The gap, and where the decision moved

`require_prepared` is the early refusal and it reads the OBJECTS — an `lstat`, which cannot
happen under a write lock. So a conflict arriving between that check and `tokens.acquire` was
excluded by nothing.

`workspaces.prepared_workspace_governance` composes the SAME `tokens.Governance` the ordinary
start already uses — one domain, one journal, no second token system — and reserves through it
with the preparation facts re-asked inside `tokens.acquire`'s own `BEGIN IMMEDIATE`, as its
`eligible` predicate. What the predicate reads is journal-only: standing preparation,
allocation, removal, cleanup and adoption windows, the custody overlap, and the durable
completion. The object comparison stays outside every transaction, where it belongs.

`release`, `overdue` and `revoke` are the ordinary governance's own, so the endings, the
reclamation and the conflict domain are exactly the accepted G1 ones.

### Evidence

    the reached interleaving   test_a_conflict_arriving_before_the_acquisition_refuses_the_start
                              -- a REAL removal admitted after the gate and before the acquire:
                              no task start, and no token outstanding over the workspace object
    the positive control      test_the_ordinary_path_still_acquires_and_starts -- one start, and
                              the outstanding generation's execution IS this attempt
    H8 at the acquisition     test_the_eligibility_predicate_reads_ONLY_the_journal, with a
                              live-instrument control asserting the trap can fail
    the witness               test_the_task_acquisition_carries_the_preparation_condition drives
                              the governance directly: with no completed preparation it refuses
                              the ACQUISITION in the predicate's own words, and nothing is
                              acquired

### Two corrections of mine, both measured

* the wrapper first held `resource_kind`/`identity` as CLASS attributes, so `self.identity(...)`
  became a bound method and passed `self` as the attempt — a `TypeError` from the first composed
  start, fixed by reading the ordinary governance directly;
* it first took a `roots` operand and read nothing from it. An operand nothing reads is one a
  caller could believe means something, so it is gone rather than declared.

### The stale docstring is gone

`admit_preparation`'s prose still described name-equality and the guard ground as live rules.
Both are withdrawn in the executable code, so the docstring now states the single ground — the
ownership capability — and says plainly that `execution` is recorded as ATTRIBUTION only.

### Measured, this claim

    tests.tools.test_single_worker             194 PASS 12.8s   (191 before, +3)
    tests.manager.test_workspaces / test_custody / test_maintenance / test_intake /
      test_attempts                            OK
    reviewer same_attempt_reentry / preparation_matrix / staging_exclusion   all OK
    tests.manager.test_boundary_inventory      328 tests, 26 FAIL -- name-set IDENTICAL
    tests.manager.test_dependencies            21 tests, 70 FAIL -- name-set unchanged
    unowned receiving entries                  571, re-counted; the three governance entries
                                               are owned and witnessed

    workspaces.py                            c61a27e6ec9a  341965 B
    tools/single_worker.py                   772a67fd2323  217261 B
    tests/tools/test_single_worker.py        3bd740e49d42  276990 B  194 cases
    tests/manager/test_boundary_inventory.py a3143e4efe6b  863564 B
    tests/manager/test_dependencies.py       995a6afa4d2d   62502 B  unchanged

Every selector preflighted for `engine = "docker"`, `engine = "podman"`, `required = True` and
`subprocess.run([self.engine`. No live-engine suite ran.

### Remaining scope

The finite composed set in PLAN, and nothing else outstanding that I know of:

    H1  one traced case: claim -> ownership -> durable completion -> revalidation ->
        acquisition -> inert create/bind/admit/start, asserting each hook fired
    H2  expired offer, lost claim race, stale assignment reaching the AUTHORITY gate
    H6  a real interruption: a process that dies mid-write, leaving the window standing,
        proving no launch and no reuse. The release covers the writer that RETURNS; this is
        the remainder, and W285465 owns the extended reconciliation
    H7  positive instrumentation over every host writer including the refusal-cleanup paths
    H9  the created task mount vectors compared as vectors

### Human milestone checkpoint

Predecessor 56431e14 inherited; child unaccepted. Truthful WIP:

    WIP v12 G2: the task token is acquired under the preparation condition

    The preparation condition is now decided inside the acquiring transaction as
    tokens.acquire's own journal-only eligibility predicate, so a conflict arriving
    after the early gate refuses the acquisition instead of slipping through. Same
    domain, same journal, same G1 endings. The composed H1/H2/H6/H7/H9 set remains.

Commit identity unobserved; no staging, no commit, no other repository mutation by me.


## 2026-09-27 claim 287701 — the loser asks about the winner

Read: detail287698 before claiming, events after287626 (my pass287675, reviewer claim287682,
reviewer pass287697), T285464 through286584, review-2026-09-27T17-48-17Z.md and
review_task_first_20260927.py. Reproduced FIRST: **1 FAIL 0.069s** — the real acquisition
committed and a real removal was then admitted for the same attempt.

### The defect, in the reviewer's words and mine

A first-winner predicate is not an atomic transfer when the losing operation never asks about
the winner. My acquisition condition closed the conflict-arrives-first order and left the
opposite one open: with the task token OUTSTANDING, a removal, cleanup or adoption was still
admitted, so both actors held authority over the same roots.

`_task_token_refusal` is the answer and it is journal-only, which is what lets it run inside
another act's `BEGIN IMMEDIATE`: the attempt row carries the PINNED workspace object — the two
members `tokens.workspace_identity` reads — so the domain is computed from durable facts with no
`lstat`, and `tokens.outstanding` is a walk over derived identities. It is asked by
`_admitted_removal`, `admit_cleanup`, `_admitted_adoption` and `admit_preparation`.

**NOT by allocation, deliberately and stated in the code:** the ordinary path re-enters
`assignment_workspace` every tick and ADOPTS the roots its own live task is using, so refusing
there would refuse the reconcile path itself. What this guards are the acts that take ownership
away.

**And the exemption is the attempt's own execution.** Without it, every later tick's
`admit_preparation` refused against the token its own start had taken — eighteen composed cases
failed with my own refusal text, which is how I found it. An act that takes ownership away
passes no exemption and is refused by any outstanding generation.

### The reviewer's source concern, closed in the same change

The task eligibility predicate did not name `_journal_maintenance`, so an open maintenance
window BEFORE any token could have been read as free. It reads it now, and a case drives it: a
window opened between the start gate and the acquisition, and no task starts.

### Evidence, six new cases

    removal / cleanup / adoption refused while the task token is outstanding, each naming the
      generation and saying ownership transfers after the token is RETURNED
    a FOREIGN preparation of the same attempt refused for the same reason
    the attempt's OWN re-entry NOT refused by its own token -- the exemption, and the case
      says how I found it
    the task eligibility refusing a standing MAINTENANCE window, with no start

### Measured, this claim

    reviewer review_task_first_20260927.py            BEFORE 1 FAIL 0.069s -> AFTER OK 0.066s
    reviewer same_attempt_reentry / preparation_matrix / staging_exclusion   all OK
    tests.tools.test_single_worker                    200 PASS 13.1s   (194 before, +6)
    tests.manager.test_workspaces / test_custody / test_maintenance / test_intake /
      test_attempts                                   OK
    tests.manager.test_boundary_inventory             26 FAIL -- name-set IDENTICAL
    tests.manager.test_dependencies                   70 FAIL -- name-set unchanged
    unowned receiving entries                         571, re-counted; no new entries of mine
                                                      (the reader is private)

    workspaces.py                            c817b244be9f  345827 B
    tools/single_worker.py                   772a67fd2323  unchanged this claim
    tests/tools/test_single_worker.py        59027be0c18b  283198 B  200 cases

Every selector preflighted for `engine = "docker"`, `engine = "podman"`, `required = True` and
`subprocess.run([self.engine`. No live-engine suite ran.

### Remaining scope

    H1  one traced case: claim -> ownership -> completion -> revalidation -> acquisition ->
        inert create/bind/admit/start, asserting each hook fired
    H2  expired offer, lost claim race, stale assignment reaching the AUTHORITY gate
    H6  a real interruption -- a process that dies mid-write -- proving no launch and no reuse
    H7  positive instrumentation over every host writer including the refusal-cleanup paths
    H8  the second-connection half: unrelated DB progress while external work is paused
    H9  the created task mount vectors compared as vectors

### Human milestone checkpoint

Predecessor 56431e14 inherited; child unaccepted. Truthful WIP:

    WIP v12 G2: a live task token owns the roots until it is returned

    The ownership transfer is now decided in both directions: the acquisition carries the
    preparation condition inside its own transaction, and removal, cleanup, adoption and a
    foreign preparation each refuse while that token is outstanding -- from the attempt
    row's pinned object, with no filesystem read under any lock. The attempt's own
    re-entry is exempt, which is what keeps the reconcile path working. H1, H2, H6, H7,
    H8's second connection and H9 remain.

Commit identity unobserved; no staging, no commit, no other repository mutation by me.


## 2026-09-27 claim 287793 — a re-entry beside a live task is a REVALIDATION

Read: detail287783 before claiming, events after287701 (my pass287766, reviewer claim287769,
reviewer pass287782), T285464 through286584, review-2026-09-27T18-00-36Z.md and
review_live_task_edges_20260927.py. Reproduced FIRST: **2 FAIL 0.129s** — with the task running,
a real custody claim and a real mutating allocation admission both succeeded.

### Both edges closed, and the distinction the review asked for

* **custody** — a custody act is a writer inside these roots, so `_claim_episode` now asks
  `_task_token_refusal` as well: the token is returned first, and that is the ownership
  transfer.
* **allocation** — `_admitted_allocation` asks it too, and with **no same-attempt exemption**,
  because an allocation IS a writer: `_own_directory` attempts a `mkdir` and the group adoption
  chmods, so "the same attempt" is not a licence to write again after handoff.

**And the ordinary re-entry no longer reaches that admission.** `assignment_workspace` takes a
read-only path while this attempt's task token is live: `_revalidated_roots` proves the home and
every entry is this manager's own real directory, answers the same roots, and **refuses anything
missing, replaced or partial rather than repairing it beside a live task**. Nothing there
creates, chmods or chowns.

### Evidence, four new cases

    a custody claim refused beside a live task, recording NO episode
    a mutating allocation admission refused, leaving NO standing allocation
    the ordinary re-entry REVALIDATES and writes nothing -- positive instrumentation over
      `mkdir`, `chmod` and `chown` with a live-instrument control, and the same roots answered
    the revalidation REFUSES material that is gone, and repairs nothing

### Two measured corrections of mine

* the live-token question must be asked through the admission's own `asking` handle, not the
  raw store: this entry's thread affinity is real, and asking the caller's handle raised
  `sqlite3.ProgrammingError` ahead of the accepted off-thread refusal — found by
  `test_the_original_shared_group_pattern_is_refused_off_thread`;
* one of my own H6 cases admitted an allocation for the running attempt to exercise the gate;
  that is now refused for the task-first reason, so the case uses an attempt with no live token
  and says why.

### Measured, this claim

    reviewer review_live_task_edges_20260927.py   BEFORE 2 FAIL 0.129s -> AFTER OK 0.120s
    reviewer task_first / same_attempt_reentry / preparation_matrix / staging_exclusion  all OK
    tests.tools.test_single_worker                204 PASS 12.7s   (200 before, +4)
    tests.manager.test_workspaces / test_custody / test_maintenance / test_intake        OK
    tests.manager.test_boundary_inventory         26 FAIL -- name-set IDENTICAL
    tests.manager.test_dependencies               70 FAIL -- name-set unchanged
    unowned receiving entries                     571, re-counted; no new entries (the
                                                  revalidation reader is private)

    workspaces.py                            fdb8dd57a7eb  350083 B
    custody.py                               53edf82ecf69  140491 B
    tests/tools/test_single_worker.py        dffde017000a  289431 B  204 cases

Every selector preflighted for `engine = "docker"`, `engine = "podman"`, `required = True` and
`subprocess.run([self.engine`. No live-engine suite ran.

### Remaining scope

    H1  one traced case: claim -> ownership -> completion -> revalidation -> acquisition ->
        inert create/bind/admit/start, asserting each hook fired
    H2  expired offer, lost claim race, stale assignment reaching the AUTHORITY gate
    H6  a real interruption -- a process that dies mid-write -- proving no launch and no reuse
    H7  positive instrumentation over every host writer INCLUDING the refusal-cleanup paths and
        the ordinary re-entry (the re-entry half landed this claim)
    H8  the second-connection half: unrelated DB progress while external work is paused
    H9  the created task mount vectors compared as vectors

### Human milestone checkpoint

Predecessor 56431e14 inherited; child unaccepted. Truthful WIP:

    WIP v12 G2: a re-entry beside a live task revalidates rather than writes

    Custody claims and mutating allocation admissions are both refused while the task
    token is outstanding, with no same-attempt exemption for a writer. The ordinary
    re-entry takes a read-only proof of the prepared roots instead, refusing material
    that is missing, replaced or partial rather than repairing it beside a live task.
    H1, H2, H6, H7's refusal paths, H8's second connection and H9 remain.

Commit identity unobserved; no staging, no commit, no other repository mutation by me.


## 2026-09-27 claim 287863 — the composed H set: H1, H2, H8 and H9 delivered

Read: detail287854 before claiming, events after287793 (my pass287840, reviewer claim287842,
reviewer pass287853), T285464 through286584, review-2026-09-27T18-10-28Z.md.

### The source point first

"Directory/type/owner validation alone is not durable identity proof." `_revalidated_roots` now
compares the entries that are there NOW against the `device:inode` the COMPLETION record holds
for `inputs` and `workspace`, so a directory of the right shape at the right path is refused
when it is not the same object.

### The composed cases, with their exact selectors

All in `tests/tools/test_single_worker.py`, class `TheConnectedHANDOFFIsProvedEndToEnd`, driven
through the real ordinary composition with real disposable stores and the fake engine:

    H1  test_H1_the_whole_ordering_is_claim_prepare_account_revalidate_acquire_start
        the claim exists for this attempt; the hooks fired in order -- admit_preparation
        before record_preparation before require_prepared before acquire; the durable account
        exists and its window is closed; the launch is the INERT `create`; and the outstanding
        generation's execution is this attempt with its container the runtime the engine named
    H2  test_H2_a_lost_claim_reaches_the_authority_gate_and_prepares_nothing
        the gate is `_claim`'s own reading of the claimed offers, answered empty as a lost race
        leaves it: no preparation admitted, no launch, and no attempt home created
    H8  test_H8_a_second_connection_makes_progress_during_the_engine_call
        at the launch boundary the connection holds NO transaction, and a SECOND connection
        completes an unrelated attempt's preparation while that external call is in flight
    H9  test_H9_the_task_vectors_mount_exactly_what_this_deployment_allows
        the actual created vector: `/input` read-only from the attempt's inputs, `/output`
        writable from its workspace, `/scratch` from its scratch, `/input/source` read-only,
        and no storage root, credential HOME, credential-state or control database mounted

### Four measured corrections of mine, each found by running

* H9 first asserted a `/workspace` target; the writable output root is mounted at `/output`.
  The case reads the real targets now.
* H9 first asserted "no credential mount at all"; the task's own exact credential FILE delivery
  is mounted on purpose. What must not appear is the attempt's credential DIRECTORY or the
  journal, and that is what it asserts.
* H8 first patched `engine.__call__` on the instance, which changed nothing because the
  composition captures the callable it is given. The engine is wrapped at construction now.
* H2 first opened two patchers in one `with`, and the second raised on a name this module does
  not export — so the FIRST was never unwound and `workspaces.admit_preparation` stayed patched
  for the rest of the class, which is why H8 then saw no launch at all. One patcher per
  `start()` with its own cleanup now. **And repairing that leak is also how I found that an
  earlier surgical edit of mine had spliced H8's body into the next class's method** — the file
  is whole again and the suite proves it.
* H2 first expected an empty storage; it holds the manager's own instance guard and authority
  marker, which `operations_from` writes at startup. Measured rather than assumed.

### Measured, this claim

    tests.tools.test_single_worker                 208 PASS 12.8s   (204 before, +4)
    tests.manager.test_workspaces / test_custody / test_maintenance / test_intake   OK
    reviewer live_task_edges / task_first / same_attempt_reentry / preparation_matrix /
      staging_exclusion                            all OK
    tests.manager.test_boundary_inventory          26 FAIL -- name-set IDENTICAL

    workspaces.py                            67a695e59ba9  351222 B
    tests/tools/test_single_worker.py        ad58b57bf12b  299573 B  208 cases

Every selector preflighted for `engine = "docker"`, `engine = "podman"`, `required = True` and
`subprocess.run([self.engine`. No live-engine suite ran.

### Remaining scope — two items

1. **H6, a REAL abrupt interruption.** Everything in-process runs its `finally`, so a genuine
   mid-write death needs the composition in a child process that is SIGKILLed, with the parent
   then reopening the stores to prove no launch and no reuse. I have NOT built that harness; the
   in-process half (the window standing, every admission refusing, the gate refusing) is proved,
   and the abrupt half is not. I am not claiming it by another route.
2. **H7's refusal-cleanup paths.** The ordinary re-entry half landed last claim and the writers
   are instrumented at the preparation seam; what is not yet driven is a refusal DURING staging
   with its unwind — `_published_task`'s unlink and the launch/credential unwinds — asserted as
   effects that happened and effects that did not.

### Human milestone checkpoint

Predecessor 56431e14 inherited; child unaccepted. Truthful WIP:

    WIP v12 G2: the connected handoff is proved end to end for H1, H2, H8 and H9

    The composed ordinary path now has its ordering, its authority negative, its
    no-transaction-during-external-work with a second connection progressing, and its
    actual mount vectors as reached selectors. The re-entry consumes the preserved
    durable identity rather than only the type and owner. H6's abrupt interruption needs
    a kill harness I have not built, and H7's refusal-cleanup paths remain.

Commit identity unobserved; no staging, no commit, no other repository mutation by me.


## 2026-09-27 claim 288003 — the whole composed package, H6 included

Read: detail287989 before claiming, events after287863 (my pass287974, reviewer claim287977,
reviewer pass287988), T285464 through286584, review-2026-09-27T18-29-46Z.md. The review's list
was exact and this claim closes all of it. **No product byte changed: this is evidence.**

### H6 — an abrupt death, with no unwinding at all

The reviewer's suggestion is what made this tractable: a controlled deterministic subprocess.
`AnABRUPTDeathLeavesTheWindowStandingAndLaunchesNothing` forks a child that performs the REAL
preparation with the same fake engine and the same disposable stores, signals the parent through
a pipe when it reaches the allocation, and calls **`os._exit`** — no exception, no `sys.exit`, no
`finally`, no `atexit`. The parent checks the child's exit status is exactly that death, then
reopens the journal and asks:

    the window is STANDING -- no completion and no release, because nothing ran
    no token was ever acquired over the workspace object
    the start gate, a removal, an adoption and a later preparation each refuse, naming
      "host preparation 1"
    and a FRESH composition driven through the real reconcile loop launches NOTHING and
      leaves the window standing

### The four gaps the review named, each closed

* **H1** now compares the token and engine acts as ONE sequence:
  `acquire, journal_launch, create, bind_container, admit_activation, start,
  settle_activation` — the two-act shape, in order — and counts the activations of the bound
  container exactly once.
* **H2** has three negatives, not one: a lost claim, an **expired** offer, and a **stale**
  assignment naming another attempt. Each reaches `_claim`'s own comparison, admits no
  preparation, launches nothing, and leaves the storage holding only the manager's guard and
  authority marker.
* **H8** has both halves: the engine boundary AND a paused **filesystem** writer — the real
  `compose_input_root` — with a second connection completing an unrelated attempt's preparation
  while each is in flight, and no transaction held at either.
* **H9** compares the **whole** mount set as a closed list, so an extra mount fails: `/input`
  read-only, `/output` and `/scratch` writable from this attempt's own roots, `/input/source`
  read-only and sourced from the NOMINATED tree rather than a copy, the credential delivery a
  read-only FILE under the credential prefix, the launch document read-only, the exchange and
  log deliveries writable — and no storage root, credential directory, credential-state or
  journal anywhere in the vector.
* **H7** has its refusal-cleanup path: the task document is published and the protocol pair then
  refuses, which is the ordering `_input` exists for. The case asserts what DID happen (the
  publication) and what did NOT (no completion, no token, no launch) — and that the window is
  RELEASED, because that writer returned, so a partial root is refused by the absent account
  rather than by a window nobody can discharge. Plus the re-entry half at the composed seam:
  later ticks write nothing and compose no second launch, under live instruments.

### A measured correction of mine, twice now the same one

The tracer first patched `engine.__call__` on the instance and recorded no engine acts at all —
the composition captures the callable it is given. Both H1's tracer and H8 wrap the engine at
CONSTRUCTION now, and the comment says so where it bit.

### Measured, this claim

    tests.tools.test_single_worker             215 PASS 13.2s   (208 before, +7)
    tests.manager.test_workspaces / test_custody / test_maintenance                 OK
    reviewer live_task_edges / task_first / same_attempt_reentry / preparation_matrix /
      staging_exclusion                        all OK
    tests.manager.test_boundary_inventory      26 FAIL -- name-set IDENTICAL
    tests.manager.test_dependencies            70 FAIL -- name-set unchanged

    workspaces.py                       67a695e59ba9  unchanged this claim
    tools/single_worker.py              772a67fd2323  unchanged this claim
    tests/tools/test_single_worker.py   b9ab2ebc607b  318530 B  215 cases

Every selector preflighted for `engine = "docker"`, `engine = "podman"`, `required = True` and
`subprocess.run([self.engine`. No live-engine suite ran, and the H6 child uses the fake engine
and no second Host manager.

### The H package, mapped to exact selectors

    H1  TheConnectedHANDOFFIsProvedEndToEnd.test_H1_the_whole_ordering_is_claim_prepare_
          account_revalidate_acquire_start
    H2  ...test_H2_a_lost_claim_reaches_the_authority_gate_and_prepares_nothing
        ...test_H2_an_EXPIRED_offer_reaches_the_gate_and_prepares_nothing
        ...test_H2_a_STALE_assignment_reaches_the_gate_and_prepares_nothing
    H3  ThePreparationMatrixIsClosedInBothDirections (8 cases)
        ThePreparationOWNSTheRootsForItsWholeWriterLifetime (7 cases)
        ALiveTaskTOKENOwnsTheRootsUntilItIsReturned (6 cases)
        TheREENTRYBesideALiveTaskIsAREVALIDATION (4 cases)
    H4  TheHostPreparationIsAccountedForBeforeAnyTaskStart.test_a_replaced_prepared_root_
          refuses_before_any_task_is_created
    H5  ...test_the_record_replays_rather_than_recording_a_second_preparation
        OnlyTheHOLDEROfAPreparationMayContinueIt (5 cases)
    H6  AnABRUPTDeathLeavesTheWindowStandingAndLaunchesNothing (2 cases)
        ThePreparationOWNSTheRootsForItsWholeWriterLifetime.test_an_interrupted_
          preparation_leaves_the_window_STANDING
    H7  ...test_H7_a_refusal_DURING_staging_unwinds_and_launches_nothing
        ...test_H7_the_full_REENTRY_writes_nothing_and_starts_nothing_new
    H8  ...test_H8_a_second_connection_makes_progress_during_the_engine_call
        ...test_H8_a_second_connection_progresses_while_a_FILESYSTEM_writer_is_paused
        TheTaskTOKENIsAcquiredUnderThePreparationCondition.test_the_eligibility_predicate_
          reads_ONLY_the_journal
    H9  ...test_H9_the_task_vectors_mount_exactly_what_this_deployment_allows

### What I do NOT claim

W285465 owns the extended restart reconciliation and the integrated G2 acceptance: discharging a
standing window after an abrupt death is named, proved to HOLD, and deliberately not resolved
here. The excluded-run incident checkpoint and the residual catalog debt stand as recorded.

### Human milestone checkpoint

Predecessor 56431e14 inherited; child unaccepted pending this review. Truthful WIP:

    WIP v12 G2: the connected preparation-to-task handoff, H1 through H9

    An abrupt death now has a real harness -- a forked child that calls os._exit with no
    unwinding -- and it leaves the window standing, launches nothing and lets nothing
    reuse the roots. H1 compares the token and engine acts as one ordered sequence with
    the activation counted; H2 has three authority negatives; H7 has its staging-refusal
    unwind and its re-entry; H8 pauses both an engine call and a filesystem writer with a
    second connection progressing; and H9 compares the whole mount set as a closed list.

Commit identity unobserved; no staging, no commit, no other repository mutation by me.
## 2026-09-27 claim 288120 — the reviewer's three finite corrections: H2, H7, H9

Read: detail288112 before claiming, events after288084 (my pass288082, reviewer claim288084,
reviewer pass288111), T285464 through286584, review-2026-09-27T18-47-03Z.md. The amended
DESIGN.md digest cfbfbb3b320d and owner286782's host-initial-preparation scope revalidated
against the current tree before editing.

NO PRODUCT BYTE CHANGED THIS CLAIM. workspaces.py stays 67a695e59ba9 and single_worker.py stays
772a67fd2323 -- the reviewer's three items are all EVIDENCE corrections, and none of them turned
out to name a product defect. Everything below is in tests/tools/test_single_worker.py.

### 1. H2 -- the gate is now reached with a REAL row behind it

`refused_at_the_gate(label, mutate, expected)` drives ONE ordinary run with
`single_worker.claimed_offers_for` wrapped: the HONEST reader answers this attempt's own rows,
`mutate` changes exactly one thing about them, and the composition sees the result. So the
condition under test is the only difference from an accepted offer, which is what the review
asked for. It asserts the gate refused with the intended message AND that the honest reader
really did answer at least one row (an empty universe cannot pass as a refusal), and it keeps
the three negatives: no preparation admitted, no launch, and the storage root holding only
`.baton-manager-instance` and `.baton-workspace-authority`.

    test_H2_no_claimed_offer_reaches_the_gate_and_prepares_nothing        0 rows
    test_H2_two_claimed_offers_reach_the_gate_and_prepare_nothing         the real row, twice
    test_H2_another_stages_offer_reaches_the_gate_and_prepares_nothing    offer_id mutated
    test_H2_another_participants_offer_reaches_the_gate_too               participant mutated
    test_H2_a_STALE_assignment_is_excluded_by_the_SELECTION_itself        see below
    test_H1_the_claim_exists_BEFORE_the_preparation_is_admitted           observed AT admission

MEASURED, AND IT CORRECTS MY OWN FRAMING RATHER THAN THE PRODUCT: `_claim` compares
`offer_id, authority_uuid, work_id, participant, profile_digest, input_digest, policy_digest`
and does NOT compare `expires_at` or `runtime_attempt_id`. There is therefore no expiry or
staleness condition at this gate for a test to reach. Staleness is excluded one layer earlier --
`claimed_offers_for` SELECTS by attempt -- and the stale case now proves exactly that
(this attempt's row comes back, another attempt's name answers nothing) and claims nothing about
offer expiry, which is the Authority's own admission rule.

TWO OF MY OWN DEFECTS, FOUND BY RUNNING. My first helper read the real row from a PRELIMINARY
run and then drove a second one; this fixture then answered stores whose task was already
started and the pipeline did nothing at all -- measured, as an empty refusal list on three of
six cases. The mutation-at-the-honest-reader form is one run and has no such seam.

### 2. H7 -- the composed re-entry, the wider writer set, and the two cleanup paths

`host_writes()` is the new instrument: `mkdir, makedirs, chmod, chown, lchown, rename, replace,
unlink, remove, rmdir, symlink, link, truncate, mkfifo, utime` plus `os.open` with any writing
flag, filtered to this fixture's root with the two sqlite stores excluded by name. It PROVES
ITSELF LIVE on two different boundaries before returning, so an unused trap cannot pass.

    test_H7_a_composed_REENTRY_writes_nothing_and_starts_nothing_NEW
        the job and operations are RETAINED and reconciled three more times -- the actual later
        tick of a live manager. The stage is still `waiting`; no write reaches the attempt's
        storage home, its launch or credential delivery, its log directory or the nominated
        source; there is no second `create` and no second activation; the completion record is
        the same row, the window stays closed and the token generation is unchanged.
        MEASURED, AND NAMED RATHER THAN HIDDEN: a later tick DOES call
        `makedirs(<launch home>/logs, exist_ok=True)` while adopting the log delivery. It
        creates nothing -- the directory's `(device, inode, mode)` is identical across all
        three ticks -- and it is outside every root the container mounts, so the case asserts
        that exact set instead of claiming zero calls.
    test_H7_the_ALLOCATION_ALONE_writes_nothing_over_a_prepared_root
        the allocation-only probe, RELABELLED as the review required: it calls
        `assignment_workspace` directly with no claim, no gate and no start, and what it proves
        is that the adoption half of HOST-8 is read-only over roots that already exist.
    test_H7_a_FAILED_publication_removes_the_name_it_created
        the publication failure, driven at the write: `os.write` answers 0 for this
        deployment's task bytes, which is the product's own "could not be written whole"
        condition. The exclusive name it created is unlinked (observed through the unlink), the
        pathname does not exist, no completion and no token exist, and no container started.
    test_H7_the_prestart_unwind_ends_the_CREDENTIAL_before_the_LAUNCH
        a refusal at `require_prepared` -- the last gate before a container exists, with both
        pre-start deliveries already on the host. The order recorded at
        `CredentialHome.tear_down` and `launch.discard` is CREDENTIAL then LAUNCH, which is the
        product's stated rule, and neither delivery is left on the host.

TWO MEASURED FACTS THAT CHANGED THESE CASES. Both of those refusals are RECORDED, not raised:
`reconcile` does not propagate them, the stage becomes `exceptional` and the account is
`attempt_preparation_failure_of`. I first wrote both as expected exceptions and both assertions
were empty. And `mock.patch.object` on a CLASS attribute is not a descriptor, so the wrapper
received no instance (`TypeError: missing 1 required positional argument`) until `autospec=True`.

### 3. H9 -- the mount vector compared as a vector

The destination-keyed dict is gone. The case builds the whole list of
`(source, destination, mode)` tuples off the created vector and compares it against this
attempt's nine known delivery pathnames: inputs, workspace, scratch, the nominated source, the
EXACT credential file `<credential home>/credentials/<attempt>/api`, `launch.json`, the exchange
`command` and `events`, and the shared log root's per-attempt directory -- count first, then the
exact sorted set, then uniqueness in both senses (no repeated tuple, no two mounts over one
destination). The read-only/writable mode of every one of the nine is part of the tuple. The
credential file is also proved to be a real file, and the storage root, the attempt's credential
DIRECTORY, its credential-state and the control database are still asserted absent.

### Negative controls, because a passing assertion is not a working one

Each ran as a subclass of the real case with one thing broken, and each FAILED as intended:

    one mount duplicated on the created vector          FAIL (10 != 9)
    one extra mount added                               FAIL (10 != 9)
    a later tick writing into the attempt's workspace   FAIL, composed re-entry
    the same write during the allocation                FAIL, allocation-only

### Measured, this claim

    tests.tools.test_single_worker.TheConnectedHANDOFFIsProvedEndToEnd
      + AnABRUPTDeathLeavesTheWindowStandingAndLaunchesNothing   16 PASS 0.831s
    tests.tools.test_single_worker                               220 PASS 13.4s (215 before)
    reviewer staging_exclusion / preparation_matrix / same_attempt_reentry / task_first /
      live_task_edges                                            all OK, unchanged
    tests.manager.test_boundary_inventory                        26 FAIL, unchanged
    tests.manager.test_dependencies                              70 FAIL, unchanged
    unowned receiving entries                                    571, RE-COUNTED directly
                                                                 (2074 entries, 571 with
                                                                 owner_of()[0] is None)

    workspaces.py                            67a695e59ba9  351222 B  UNCHANGED
    single_worker.py                         772a67fd2323  217261 B  UNCHANGED
    maintenance.py                           0ce7be13f087   83571 B  UNCHANGED
    tests/tools/test_single_worker.py        9bd3cc2a06a0  330255 B  220 cases

Every selector preflighted for `engine = "docker"`, `engine = "podman"`, `required = True` and
`subprocess.run([self.engine`. No live engine, provider or daemon ran; no deployment, no
destructive cleanup, no repository mutation, no graph or specification change.

### The candidate/path/test-expectation audit

    every pathname this claim asserts is compared against a real object on disk in the same
      run -- the nine mount sources, the unlinked task document, both unwound deliveries, the
      log root's identity -- so no expectation is a transcribed literal nobody checked
    every new assertion's instrument is proved live in the same test: the host-writer trap
      records two boundaries before it is used, the publication case asserts the stalled write
      length, the gate cases assert the honest reader answered, and the unwind case asserts
      both teardown hooks fired
    the four negative controls above are the falsifiability evidence for the two rebuilt cases
    no test in this class asserts a value I did not measure; the two framings I could not
      measure (offer expiry at `_claim`, "zero host calls" on re-entry) are withdrawn above
      and replaced with what the product actually does

### Remaining scope

    the reviewer's independent verification of these three corrections
    W285465 keeps extended restart reconciliation and integrated G2 acceptance
    the two prior unauthorized-live-run incidents stay recorded and unresolved; no rerun and
      no cleanup selected this claim
    boundary 26 FAIL and dependencies 70 FAIL remain residual unaccepted debt

### Human milestone checkpoint

Predecessor fabc37e4 inherited; child unaccepted. Truthful WIP:

    WIP v12 G2: reach the real gates -- mutated offers, composed re-entry, exact mounts

    The authority gate is now driven with this attempt's own claimed offer mutated in one
    member at a time, so each refusal is the named condition and nothing else. The later
    tick is the composition reconciled again with fifteen host writers plus writing opens
    instrumented, proving no post-handoff write touches the attempt's material and no second
    launch is composed, with the one idempotent log-root ensure named rather than hidden.
    The publication-failure unlink and the credential-before-launch unwind are reached, and
    the task mount vector is compared as nine exact source/destination/mode tuples with
    duplicates and extras rejected. No product byte changed; four negative controls fail on
    purpose. Offer expiry is not compared at this gate and that framing is withdrawn.

Commit identity unobserved; no staging, no commit, no other repository mutation by me.
## 2026-09-27 claim 288344 — the deleted H8 filesystem regression, restored

Read: detail288339 before claiming, events after288319 (reviewer claim288321, reviewer
pass288339, my claim288344), T285464 through286584 with no new discussion, and
review-2026-09-27T19-20-00Z.md with candidate-2026-09-27T19-20-00Z.json. Owner286782 scope and
the amended DESIGN.md cfbfbb3b320d revalidated; unchanged.

### The correction, and it was mine

`TheConnectedHANDOFFIsProvedEndToEnd.test_H8_a_second_connection_progresses_while_a_FILESYSTEM_writer_is_paused`
was gone from the module. THE CAUSE, named exactly: my H7/H9 rewrite of claim 288120 replaced one
span reaching from `test_H7_the_full_REENTRY_...` to
`test_H8_a_second_connection_makes_progress_during_the_engine_call`, and that H8 case sat inside
it along with the two H2 cases the review did ask me to replace. Nothing about the filesystem
case was superseded; it was collateral of a coarse splice, and a deleted accepted slice is a
coverage regression whatever the intent. It is RESTORED VERBATIM -- the real
`compose_input_root` paused, `control._connection.in_transaction` observed False, an unrelated
attempt's preparation admitted on a SECOND `ControlStore` connection while the staging writer is
in flight, and the ordinary launch still completing -- with a comment recording the deletion and
its cause so the next splice has the warning in front of it.

### The independent deletion audit I should have run before passing

Every `test_...` selector named anywhere in this dossier's prose, checked against the tree:

    52 selectors named across FINDING/PLAN/PROGRESS/every review
    all present, except the four this claim's predecessor deliberately replaced with the
      reviewer's own accepted corrections (the lost-claim, EXPIRED and STALE H2 cases and
      `test_H7_the_full_REENTRY_...`, now the mutated-row H2 set and the relabelled
      allocation-only case), and:
    test_the_mount_EXCLUDES_every_sibling_attempt
    test_the_HOST_MAKES_EXACTLY_ONE_EMPTY_DIRECTORY_AND_NOTHING_ELSE
    test_the_mount_is_the_storage_and_no_sibling_is_reachable_by_name
      -- the WITHDRAWN container-allocation model's cases, removed when the owner amended
      TOK-7 on 2026-09-27 and the host-initial-preparation model replaced them. Their absence
      is that recorded withdrawal, not a splice; restoring them would contradict the amended
      specification, so they stay withdrawn and are named here so the absence is accounted
      for rather than merely unnoticed.

The boundary catalogue's witness strings (`test_the_task_acquisition_carries_the_preparation_
condition` and its siblings) are methods OF that catalogue, not of this module; each was located
where it is defined rather than assumed missing.

### Measured, this claim

    the restored selector alone, then the whole focused H package
      TheConnectedHANDOFFIsProvedEndToEnd + AnABRUPTDeathLeavesTheWindowStanding...
                                                               18 PASS 0.887s
    TheConnectedHANDOFFIsProvedEndToEnd                        15 PASS 0.718s (14 before)
    tests.tools.test_single_worker                             221 PASS 13.4s (220 before)
    tests.manager.test_offers.ExpiryIsASettlement              4 PASS 0.012s (retained,
                                                               preflighted, unchanged by me)

    workspaces.py                            67a695e59ba9  351222 B  UNCHANGED
    single_worker.py                         772a67fd2323  217261 B  UNCHANGED
    maintenance.py                           0ce7be13f087   83571 B  UNCHANGED
    tests/tools/test_single_worker.py        89475e50e641  332684 B  221 cases
      full: 89475e50e641b5d8bff5507920230f6a213b66842d6db359cdeab498436e1f93

Selectors preflighted for `engine = "docker"`, `engine = "podman"`, `required = True` and
`subprocess.run([self.engine`, including `tests/manager/test_offers.py`. No live engine,
provider or daemon ran; no broad suite rerun; no deployment, no destructive cleanup, no
repository mutation, no graph or specification change. Boundary 26 FAIL and dependencies 70 FAIL
remain residual unaccepted debt, not rerun this claim. The two prior unauthorized-live-run
incidents stay recorded and unresolved.

### The reviewer's H2 correction, adopted into my own record

Review 19:20:00Z corrects the earlier demand rather than my code: offer-acceptance EXPIRY belongs
before a claim, and `tests.manager.test_offers.ExpiryIsASettlement` already proves late
acceptance refuses and records expired/spent, sweep expiry, and preservation of an already
accepted authorization. Combined with `offers.py:117` selecting only claimed rows for the exact
attempt and my reached absent-claim refusal, that is the expiry boundary -- so my previous
claim's line attributing expiry "to the Authority's own admission rule" should be read as this
manager-side offers boundary, which is tested, and not as a claim about an untested layer.

### Remaining scope

    the reviewer's final digest-bound review and acceptance
    W285465 keeps extended restart reconciliation and integrated G2 acceptance

### Human milestone checkpoint

Predecessor fabc37e4 inherited; child unaccepted. Truthful WIP:

    WIP v12 G2: restore the deleted second-connection filesystem regression

    A coarse splice in the previous claim removed an accepted H8 case along with the two
    H2 cases the review asked to replace. The filesystem half is restored verbatim -- the
    real staging writer paused, no write lock held, an unrelated attempt's preparation
    admitted on a second connection, and the ordinary launch still completing -- and the
    deletion and its cause are recorded at the case. Every selector this dossier names is
    audited against the tree; the only other absences are the container-allocation cases
    the amended TOK-7 withdrew, named so they are accounted for. No product byte changed.

Commit identity unobserved; no staging, no commit, no other repository mutation by me.
