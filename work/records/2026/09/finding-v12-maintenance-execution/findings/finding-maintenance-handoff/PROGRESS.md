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
