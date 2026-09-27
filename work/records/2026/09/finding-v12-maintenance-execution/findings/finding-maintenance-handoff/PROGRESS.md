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
