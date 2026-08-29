# Implementer progress — the delivered `/input` pair

`PROGRESS.md` has one writer: the implementer (`baton.claude`).

## 2026-08-28 — revalidated, corrected, and measured by removal

Claimed W33935 at seq 34068. **No Git history or index was mutated.** The
mutation harness rewrote two source files in place and restored each one.

### PLAN 1 — the defect, revalidated against the current tree

Not transcribed from W6. `evidence/w33935-probe.py` starts one execution
runtime through `request_runtime_start` and then runs a probe inside the exact
argv the manager composed, with only the entrypoint replaced. Before the
correction:

    workspaces.READ_ONLY_FILE = 0o400     launch.READ_ONLY_FILE = 0o444
    workspaces.READ_ONLY_DIR  = 0o500     launch.READ_ONLY_DIR  = 0o555

    running as       [65532, 65532]
    /input/input.json        0o400 uid 1000  read: PermissionError EACCES
    /input/assignment.json   0o400 uid 1000  read: PermissionError EACCES
    /run/baton/launch.json   0o444 uid 1000  read: 139 bytes

**Two facts the finding did not have, and both mattered.** The `/input` root
itself is `0o775` and IS listable and traversable — only the two files were
unreadable, so the correction is at the files and not at the directory. And
`/input` refuses a write with `EROFS`, from the read-only bind rather than
from any mode, which is what makes a world-readable file safe here.

### PLAN 2 and 3 — the boundary, and why it is the smaller change

`workspaces.READ_ONLY_FILE` is `0o444` and `READ_ONLY_DIR` is `0o555`, the
same two values `launch.py` already uses and for the reason `launch.py`
already wrote down.

**What makes this safe is not the mode.** A worker cannot write here because
the root is bind-mounted read-only, and it cannot reach the root by any other
path because nothing else is mounted. The mode's job is the HOST side: it says
on disk that these bytes are finished, so this manager's own later mistake
cannot rewrite the evidence a claim was made against. Read permission was
never part of that job, and taking it away protected nothing while breaking
the only consumer.

**The second half of the defect, which the constant alone does not fix.**
`_write_read_only` passed `READ_ONLY_FILE` as the CREATION mode to `os.open`,
and a creation mode is filtered by the process umask — so under the ordinary
service umask 077 the corrected constant would still author 0400, silently and
only on some hosts. This is the third time this exact shape has appeared in
this distribution: **W26291 review [P0] found and fixed it at the launch
delivery and wrote the reason out in full**, and the same line here was never
revisited. It now creates at `0o000` with `O_NOFOLLOW` and establishes the mode
with `os.fchmod` on the descriptor it wrote, after the last byte.

### PLAN 3 — the regressions

New module `tests/manager/test_input_delivery.py`, **7 cases** (1 narrow Podman
skip). It reuses W6636's engine fixture and NOT its cases: subclassing
`Composition` outright re-collected all thirty-two of that Work's cases under
this module's class names — a duplicate identity in the shared registry and a
suite running a closed Work's cases twice while attributing them here. The
fixture (`Lifecycle`) is inherited and the twelve helper methods this Work
depends on are adopted by name, which is the honest statement of the coupling.

- **positive**: both documents are opened as uid 65532 inside the composed
  runtime and what comes back is compared against the manager's exact bytes —
  not against `0o444`, which would be the manager agreeing with itself about a
  number.
- **write denial**: asked twice, of two different things (see below).
- **restart/retry reuse**: a second `ControlStore` over the same file adopts
  the running runtime, the engine confirms exactly one container carries the
  labels, and both documents still read identically. A correction applied only
  where the documents are WRITTEN passes the positive case and fails this one.
- **sibling isolation**: a second assignment's root is composed on the same
  host, proved readable from the host, and reported `FileNotFoundError` from
  inside the first assignment's runtime.
- **umask**: composed under 022, 077 and 777 and required to be `0o444` each
  time.
- **the mode's own claim, as bits**: every class may read, no class may write.
- **the two components agree**: `workspaces` and `launch` are held to each
  other, so a future edit cannot move one without the other. That is what would
  have caught this in the first place.

### MEASURED BY REMOVAL

    caught 6 of 6

Retained as `evidence/w33935-mutation-harness.py` with the transcript at
`evidence/w33935-mutation-2026-08-28.txt`.

**Two of my own cases failed that measurement first, and both corrections are
the point of having it.**

- The write-denial case measured nothing about the bind. With the read-only
  flag dropped from the production run vector the in-container write STILL
  failed — the documents are owned by the manager's uid and the container is
  65532, so ownership refuses the write before the bind is ever reached. The
  case now also asks the ENGINE whether the bind it applied is read-only,
  which is the guard a mutation can actually move. This is the same limit W6
  reported for `A-input-is-read-only`, arriving in my own suite.
- The umask mutation measured nothing either, and that one was my mutation
  rather than my case: it restored the creation mode and left the `fchmod` in
  place, so the final mode was still correct. The mutation now removes the fix.

### One property this suite does NOT measure, said plainly

The staging file is created at `0o000` so it is never readable while it is
still partial. Nothing here observes that: it would need to catch the file
between `open` and `fchmod`, and there is no deterministic seam to do it. The
property is inherited from W26291's shape and is stated rather than claimed.

### The second [P0] W6 measured is still present and is not this Work's

Re-measured in the same probe: `/workspace` is `0o775` uid 1000 and the
container at 65532 gets `PermissionError` writing to it, so a worker cannot
write the outputs it is required to declare. It needs an owner; nothing here
touches it.

### Gates

- `tests.manager.test_input_delivery` — 7 tests, 1 narrow Podman skip, green
  against Docker 29.1.3
- `tests.tools.test_parallel_runner` — 36 tests, OK, after registering the new
  module SERIAL (it builds the worker image, starts real containers and counts
  containers for one assignment's labels)
- every engine-owning module run together — `test_lifecycle_composition`,
  `test_output_custody_engine`, `test_workspaces`,
  `test_negative_race_endings`, `test_ended_runtime_adoption`,
  `test_credentials_engine` and `test_input_delivery`: **124 tests, OK**, 4
  narrow skips. Every existing case referencing these modes does so through the
  constants, so none needed editing.
- full v12 parallel source — **6 failures, 0 errors**, every one in
  `test_boundary_inventory`: the accepted baseline unchanged, checked by NAME —
  `test_the_universe_sees_every_persisted_column_that_is_read`,
  `test_every_declared_probe_reaches_its_named_boundary`,
  `test_the_missing_probe_check_can_actually_fail`,
  `test_every_owned_entry_has_exactly_one_probe`,
  `test_every_boundary_call_belongs_to_an_entry_or_is_declared`,
  `test_every_receiving_entry_has_an_owning_validator`.
  Transcript: `evidence/w33935-gate-2026-08-28.txt`. The runner gates the
  serial phase behind the parallel one, so the serial registry did not run
  there; the line above is those modules run directly.

### Existing files edited outside this Work's own module

- `src/baton_v12/worker_manager/workspaces.py` — the two constants and
  `_write_read_only`. This is the deliverable.
- `tools/parallel_test.py` and `tests/tools/test_parallel_runner.py` — the
  serial registry and the guard that pins it, one entry each with the reason.
  The guard is an inventory: a new engine-owning module has to be entered in it
  or the comparison is what fails.

No existing test's assertions were changed.

## State

**Passed back for independent review.** The acceptance's three clauses are
implemented and each is measured by removal.

## 2026-08-28 — review 2026-08-28T21:06:22Z: the root was never frozen

Reclaimed W33935 at seq 34276. **No Git history or index was mutated.** The
finding is accepted in full, including the part about my own measurement.

### The defect, and the review is exactly right about why my harness missed it

`READ_ONLY_DIR` moved from `0500` to `0555` and **nothing in production read
it**. `compose_input_root` wrote both documents and returned, leaving the root
at `0775` — which my own retained probe output shows and which I did not
follow up. A `0444` file inside a writable directory is not protected: unlink
and rename are permissions of the DIRECTORY, so the manager's own uid, or
anything sharing its group, could remove either document and put a different
one at the same name **underneath a worker that had already mounted it**. The
read-only bind stops the container writing; it does not stop the host replacing
a bound file.

**And the mutation I claimed for it measured nothing.** It changed a constant
production code never read and reran a bit-value assertion, so 6 of 6
overclaimed one guard. That is the same class of defect this campaign has
corrected in my work before — a case that agrees with a number rather than
with a behaviour — and it is worth saying plainly that the review caught it
and I did not.

### The correction

`compose_input_root` establishes the exact root mode as `READ_ONLY_DIR`
**after both documents are durably installed** — a root frozen between them
could not receive the second, and §7.0 fixes that order. `os.chmod` on the
root is exact and was never umask-filtered: the umask applies to creation and
this directory already exists.

`0555` rather than `0500` for the same reason the files are `0444`: the
container's fixed uid is not this manager's, and a root it cannot traverse is a
root whose readable documents it cannot reach. Measured in the real runtime —
the root is `0o555`, still listable, and both documents still read at 2651 and
969 bytes.

### The behavioural regression the review asked for

`TheInputRootIsFrozenAndNotOnlyItsFiles`, five cases, all acting on the HOST as
the manager's own identity, because that is the party the freeze is against:

- **create, unlink, rename, replace and replace-in-place are each attempted
  and each required to be denied with `EACCES`**, named separately rather than
  as "no write" — a case that only tried to create would pass while unlink and
  rename, the two that actually replace a bound file, stayed open. And nothing
  moved: the root still holds exactly the two documents and the first still
  parses.
- the root mode is exact under no umask, 022, 077 and 777.
- the manager can still read and traverse what it froze, and `0555` carries the
  execute bit for every class.
- **cleanup removes a frozen root and thaws nothing else**: a sibling
  assignment's frozen root beside it is untouched, mode included.
- recomposition is still refused by the rule that already refused it, so the
  freeze is not doing that job by accident.

**It refuses to run as root.** These cases establish that ordinary permissions
DENY a write, and root is not denied by them; a green run under uid 0 would
prove nothing, so `setUp` raises instead.

### MEASURED BY REMOVAL

    caught 9 of 9

Four mutations replace the one that measured nothing: the root never frozen,
the root frozen owner-only (which breaks the worker's traversal, so the
container case catches it), the freeze run before the second document is
installed, and cleanup unable to remove what it froze.

**The cleanup mutation was wrong the first time and the harness said so.** I
removed the chmod in `_remove`'s subdirectory branch — but that line does not
thaw a frozen root holding files, because the walk reaches the root as
`current` and the files loop thaws it there. Mutating a line that protects
nothing measures nothing, which is the same defect the review found in the
constant. Re-targeted at the line that actually protects the case.

### Gates

- `tests.manager.test_input_delivery` — 12 tests, 1 narrow Podman skip, green
  against Docker 29.1.3
- every engine-owning module together — **129 tests, OK**, 4 narrow skips
- `evidence/w33935-mutation-2026-08-28.txt` — 9 of 9
- `evidence/w33935-revalidation-2026-08-28.txt` — the real-container probe,
  re-run after the freeze
- full v12 parallel source — **6 failures, 0 errors**, every one in
  `test_boundary_inventory`: the accepted baseline unchanged, checked by NAME.
  Transcript: `evidence/w33935-gate-2026-08-28.txt`

## State

**The review's [P0] is answered. Passed back for independent re-review.**

Unchanged: the file readability and write-denial coverage the review asked me
to preserve is untouched. Still not this Work's and still unowned by me:
`/workspace` remains `0775` owned by the manager's uid, so the container at
65532 cannot write the outputs it declares — that is `W33936`.

## 2026-08-28 — re-review 2026-08-28T21:37:50Z: the root's own entry

Reclaimed W33935 at seq 34354. **No Git history or index was mutated.** The
finding is accepted; the reviewer's reproduction was run against the submitted
cut first and reproduced wholesale replacement under the manager's ordinary
uid.

### The defect, and it is the one I did not think through

`0555` on `inputs` governs create, unlink and rename **inside** it. Renaming or
replacing `inputs` **itself** is a write to its parent, and
`assignment_workspace` left the assignment home at the process default. So the
whole frozen root could be moved aside and a writable one put at the same
canonical path with different bytes in it — and a worker that had already
resolved that path would be reading somebody else's documents through a mount
this manager still believed it had frozen.

**A directory entry can only be protected through its parent.** There is no
other mechanism, so the correction is at the home and nowhere else.

### Why the home could not simply be frozen where the root is

The home holds five entries, and three of them are created **after** compose
time by other components: the adapter's `custody` tree and the credential
home's `credentials` and `credential-state`. A parent can only be closed once
nothing more needs creating in it, so `assignment_workspace` now provisions all
five and still ANSWERS with only the two mountable roots — `assignment_roots`
is unchanged, which is what keeps every existing caller and every mount
contract exactly as it was.

`HOME_ENTRIES` is therefore a claim about two other components, so it is held
to them rather than asserted: `TheHomeLayoutIsDeclaredWhereItIsFrozen` walks
`oci.py` and `credentials.py` for every literal joined onto the home and
requires the set to be declared. If either grows a sixth sibling, that case
fails here rather than the freeze failing at run time on somebody else's
machine.

### An interaction the suite caught, in production cleanup

Freezing the home broke `discard_workspace`: `_remove` thawed each directory
only inside its **file** loop, so a directory holding only directories never
reached it and `rmdir` on its children was denied by its own mode. Unlinking a
file and removing a subdirectory are both writes to the same directory, so the
thaw belongs once at the top of each walk step. Corrected there, and the
mutation for it re-anchored.

### The regressions

`TheRootsOwnENTRYIsFrozenToo`, four cases, all on the host as the manager's own
identity:

- **five moves attempted separately and each denied**: rename the root aside,
  make a new root at the canonical path, rename another directory onto it,
  remove the root, and add a sibling entry to the home. Named separately
  because it is the SECOND that actually swaps a mounted root's contents, and a
  case that only tried the first would leave it open. Afterwards the canonical
  path still exists, still holds exactly the two documents, the first still
  reads byte-identically, and the home still holds exactly its declared
  entries.
- **what the frozen home still permits**, because a freeze that broke the arc
  it protects would be worse than the defect: custody trees, volatile
  credential roots and durable credential records are all created inside
  entries the provisioning made, and the writable workspace is still writable.
- cleanup reaches exactly one frozen home and leaves a sibling assignment's
  home AND input root frozen with its documents intact.
- the home is frozen once its entries exist.

The container traversal and readability, restart reuse and child-entry denials
the review asked me to preserve are untouched.

### MEASURED BY REMOVAL

    caught 11 of 11

Two new mutations for the parent boundary — the home never frozen, and the home
frozen before its later siblings are provisioned — measured by removing the
freeze rather than by moving a constant, which is what the review asked for.
**Two earlier mutations reported `[ANCHOR]`** because their lines moved: the
root freeze now sits beside the parent freeze, and the cleanup thaw moved out
of the files loop. Both re-anchored; a harness that had counted stale anchors
as caught would have been the defect.

### Gates

- `tests.manager.test_input_delivery` — 17 tests, 1 narrow Podman skip, green
  against Docker 29.1.3
- every engine-owning module together — **129 tests, OK**, 4 narrow skips
- `evidence/w33935-mutation-2026-08-28.txt` — 11 of 11
- `evidence/w33935-root-entry-after-2026-08-28.txt` — the reviewer's
  reproduction, now stopping with `PermissionError` at its first rename
- `evidence/w33935-revalidation-2026-08-28.txt` — the real-container probe:
  root `0o555`, both documents still read, `/input` still `EROFS`
- full v12 parallel source — **6 failures, 0 errors**, every one in
  `test_boundary_inventory`: the accepted baseline unchanged, checked by NAME.
  Transcript: `evidence/w33935-gate-2026-08-28.txt`

## State

**The re-review's [P0] is answered. Passed back for independent re-review.**

Still not this Work's and still unowned by me: `/workspace` remains `0775`
owned by the manager's uid, so the container at 65532 cannot write the outputs
it declares — that is `W33936`, and the freeze here deliberately leaves that
root writable.

## 2026-08-28 — second re-review: the boundary moved again, and I measured why

Reclaimed W33935 at seq 34461. **No production source was changed this round.**
No Git history or index was mutated.

### Reproduced first

The reviewer's `evidence/w33935-assignment-home-replacement-repro.py` run
against the submitted cut reproduces exactly what they report: the `0555`
assignment home is renamed aside through workspace storage, a `0775` home and
input root are created at the original canonical path, and replacement bytes
are read back.

### The reviewer is right that the obvious continuation is wrong

Freezing workspace storage would close this level and open a worse one: that
directory is the allocator for every later assignment home, so unfreezing it to
create the next one reopens every existing home at once, and races between
allocation and use become a permanent feature rather than a window.

**And there is no name-based end to this regress.** The manager is one
unprivileged uid. Any path it can create in a directory it can write, it can
also rename and replace. Chasing the boundary upwards ends at a directory the
manager cannot allocate into, which is a directory it cannot do its job in.

### So I measured the thing that decides the design instead

`evidence/w33935-identity-probe.py`, retained with its transcript. Two facts,
both measured against a real Docker daemon rather than reasoned about:

**1. A RUNNING container's bind survives the substitution.** With the container
up, the host source was renamed aside and a replacement put at the same
canonical path. The container still reads the original bytes while the host
reads the replacement:

    before-replacement  {"who": "the original"}
    after-replacement   {"who": "the original"}
    host-now-reads      {"who": "the REPLACEMENT"}

The kernel resolved the bind to the INODE at mount time. **A worker that has
started cannot be fooled by a later replacement at all**, so the exposure
window is not "forever after delivery" — it is precisely the interval between
composition and start.

**2. The inode changes on replacement.**

    inode-before  [43, 23593869]
    inode-after   [43, 23593885]
    inode-changed True

So pinning `(st_dev, st_ino)` for the input root at composition and re-proving
it immediately before start **detects** the substitution — with no privilege
this manager does not have, and without freezing anything upward.

### What that means for the acceptance

The recorded acceptance says the input directory and documents remain
"non-replaceable". Under one uid that is not achievable as an impossibility;
it is achievable as a **detected refusal**, and the measurement says a
detection immediately before start covers the entire window that matters.

That is the reviewer's own second option — "an identity-preserving
descriptor/mount contract" — and it turns out to be reachable. Their first
option, an independently owned or brokered anchor, is not: it needs a second
uid or a broker process, and this deployment has neither.

### Why I am raising it rather than building it

This is the third [P0] round on this Work and the boundary has moved up one
level each time, which is itself the signal that the requirement was written as
a property of NAMES and the design needs it as a property of IDENTITY. Pinning
the inode changes `attempts.authorize_input_root` and the control schema — a
new schema version — and it narrows the acceptance from "cannot be replaced" to
"a replacement is refused before anything runs against it".

**That is an acceptance-boundary decision, not an implementation choice**, and
the review names an approver ruling as one of its two resolutions. My previous
round on the sibling Work over-reached into another Work's accepted suite and
destroyed uncommitted changes; the lesson I took from it is to bring the
measurement and the design to the decision rather than to keep pushing the
boundary alone.

## State

**Returned with the measurement and a proposal, and with the tree unchanged
this round.** The child-entry, layout, inventory and cleanup corrections from
the previous rounds stand and are green — 75 tests OK across
`test_input_delivery` and `test_workspaces`, 1 narrow Podman skip.

The decision requested on T33935: pin the input root's `(dev, ino)` at
composition and re-prove it before start — carried by this Work or a successor
— or narrow the acceptance to the child entry inside an assignment home that is
already trusted.

## 2026-08-28 — the ruling landed, and the acceptance is verified against it

Reclaimed W33935 at seq 34772. **No Git history or index was mutated.**

### The ruling, and what it retires

Approver M34768 makes the trust model explicit: manager, host uid, private
state root and daemon are TRUSTED. So the regress that took three rounds is
retired rather than continued — and the reason it had no name-based end is now
the reason it did not need one. **The inode pinning I proposed is not
authorized**, and I did not build it.

What remains is the six properties the ruling names, and this round verifies
them against the tree.

### One guard I wrote and the suite refuted within a minute

The ruling asks for "exclusive creation with collision refusal", and I put it
in `assignment_workspace`: refuse when the home already carries a composed
input root. **`test_ended_runtime_adoption` failed immediately** — a restarted
manager asks for the same attempt's roots again, which is the ordinary
adoption path and not a reused identity.

A rule that cannot tell "the same attempt asking twice" from "a second attempt
reusing an id", using only a directory named after the attempt, refuses the
first to catch the second. **Publication CAN tell them apart**, and
`compose_input_root` already refuses to write over either document of an
existing delivery — so the collision refusal lives there, uniqueness comes from
the attempt identity the manager mints once, and provisioning stays idempotent
because restart requires it. Both facts are now cases.

### The six properties, measured

`TheRuledTrustModel`, eight cases:

- **unique per-attempt roots** — two attempts, two disjoint trees, neither
  inside the other;
- **collision refused at publication**, and **provisioning idempotent** before
  AND after it, which is the restart path;
- **complete before publication** — a pair that agrees with itself but not with
  the manager's live assignment is refused, and the root is left EMPTY: half a
  delivery must never exist at all;
- **not recomposed** once published;
- **no write bit for anybody** on either document, and the root at
  `READ_ONLY_DIR`;
- **exact-attempt cleanup** with a clean retry answering `False` rather than
  refusing, a sibling untouched in contents and modes, and containment refusing
  a traversal out of the storage root.

The read-only worker mount is the class above, unchanged and green: `/input`
answers `EROFS` from inside the real container.

### Gates

- `test_input_delivery`, `test_workspaces`, `test_lifecycle_composition`,
  `test_ended_runtime_adoption`, `test_negative_race_endings`,
  `test_output_custody_engine`, `test_credentials_engine` together —
  **142 tests, OK**, 4 narrow skips, against Docker 29.1.3

No package gate is claimed: `tests/manager/test_oci.py` remains destroyed under
W33936 and its restoration is blocked on owner authority there, which that
review requires before any Work claims one.

## State

**Verified against the ruled trust model. Passed back for independent review.**

## 2026-08-28 — third re-review: exclusive allocation, and I was wrong about why

Reclaimed W33935 at seq 34811. **No Git history or index was mutated.**

### The finding is right, and it corrects my reasoning rather than a typo

Last round I put the collision check in `assignment_workspace`, the restart
path refuted it, and I concluded **the two could not be separated at all** and
moved the refusal to publication. That conclusion was wrong, and the reviewer
proved it with a case I had not thought of: a stale home whose `inputs` entry
is a **symlink to another attempt's root**. The alias is still contained by
manager storage, so containment accepted it and a second attempt received the
first attempt's input root.

And their point about my case is exact: despite its name it called
`compose_input_root` twice with the same attempt and the same published root,
so it proved RECOMPOSITION refusal. A document-exists check at publication
cannot prove exclusive directory allocation — if the aliased root is empty, the
wrong attempt publishes into it first.

### The separation, and it needed no new durable record

A home is named by its attempt, so a home at that path IS that attempt's —
**provided its entries are genuinely its own directories**. So every entry that
already exists must be a real directory, not a link, resolving to exactly the
path under this home; anything else is stale or aliased state and fails closed.
An entry that does not exist is created, which is the first allocation.

That is the separation the review asked for, and it keeps the restart path the
previous cut broke: reopening an attempt finds real directories at their own
paths and is answered, because reopening is not reusing.

**A link is refused even when it points inside manager storage.** What makes a
root private is that it IS this attempt's directory, not that it lands
somewhere this manager owns — which is precisely the gap containment left.

### Cases

The reviewer's `test_a_colliding_home_cannot_alias_another_attempts_root` now
passes. Three of my own beside it, because an alias is one shape of stale state
and I would rather not fix one shape: a regular file, a dangling link and a
link OUT of manager storage each fail closed with the same reason. Plus a home
that is not a directory, and the restart lookup kept green before and after
publication.

### Gates

- `test_input_delivery`, `test_workspaces`, `test_lifecycle_composition`,
  `test_ended_runtime_adoption`, `test_negative_race_endings`,
  `test_output_custody_engine`, `test_credentials_engine`,
  `test_worker_container` together — **196 tests, OK**, 4 narrow skips,
  against Docker 29.1.3

No package gate is claimed: `tests/manager/test_oci.py` remains destroyed under
W33936 and its restoration is blocked on owner authority there.

## State

**Passed back for independent re-review.** Every landed readable/read-only
input behaviour, the cleanup and sibling isolation cases, and the restart
adoption path are unchanged and green.

## 2026-08-28 — fourth re-review: the anchor itself was unproved

Reclaimed W33935 at seq 34836. **No Git history or index was mutated.**

### The finding, and it is the same mistake one level up

I applied the structural proof to the home's CHILDREN and left the home itself
checked only by `os.path.isdir`, which **follows symlinks**. So a home that was
itself a link to another attempt passed — and the child proofs then anchored on
`realpath(home)`, which is the wrong sibling, so both sides of every child
comparison were relocated together and compared equal.

**A structural proof applied to the children and not to the thing they are
measured against is not applied.** That is the whole finding and it is right.

### The correction

The home is proved BEFORE it anchors anything: not a link, a real directory,
and resolving to exactly `<storage>/<attempt>`. The children are then compared
against that proved path rather than against a `realpath` taken from whatever
the home turned out to be.

### Cases

The reviewer's `test_a_colliding_home_cannot_alias_another_attempts_home` now
passes. Beside it, the three shapes a bad home can take — a link to another
attempt's home, a link out of manager storage, and a dangling link — each
refused with the same reason, and the untouched first attempt still answered
afterwards. The child-entry cases from the previous round are unchanged.

### On the shape of these three rounds

Three [P0]s in a row on one guard, each one level out from the last: the child
entry, then the home, and before those the parent's own entry. Each time I
fixed the level I was shown and did not ask what the level was measured
against. The structural rule is now stated once and applied at both levels it
has, which is the answer I should have reached at the first of them.

### Gates

- `test_input_delivery`, `test_workspaces`, `test_lifecycle_composition`,
  `test_ended_runtime_adoption`, `test_negative_race_endings`,
  `test_output_custody_engine`, `test_credentials_engine` together —
  **148 tests, OK**, 4 narrow skips, against Docker 29.1.3

No package gate is claimed: `tests/manager/test_oci.py` remains destroyed under
W33936 and its restoration is blocked on owner authority there.

## State

**Passed back for independent re-review.** Legitimate reopening of a real home
at its own path, distinct-attempt allocation, exact cleanup and retry, sibling
isolation and every readable/read-only input behaviour are unchanged and green.

## 2026-08-28 — fifth re-review: create-or-prove is one operation

Reclaimed W33935 at seq 34860. **No Git history or index was mutated.**

### The [P1], and it is a real one

The proof was a TEST and then a CREATE — `lexists`, then `makedirs` without
`exist_ok`. Two callers could both observe absence; one created the directory
and the other received a raw `FileExistsError` from the OS. An ordinary manager
race became an unexpected fault, and a fault is not a contract answer.

### The correction

`_own_directory` attempts the create and makes the collision its branch: a
caller that loses the race falls through to **exactly the proof a pre-existing
directory gets**, and reopens it when it really is this attempt's own. It is
the same question, asked once, whether the directory has been there for a week
or for a microsecond — and it is now one operation at the home and at every
child, so the two levels cannot drift again.

Any other `OSError` from the create becomes a contract refusal too, so nothing
raw escapes that seam.

### THE REVIEWER'S RACE CASE NO LONGER RACES, and I am saying so rather than
### letting it look green

`test_first_allocation_race_answers_or_refuses_in_contract` holds both callers
at `os.path.lexists`. **The correction removed that call** — create and prove
are one operation, so there is no separate observation of absence to
synchronise on. Left alone the case would pass while racing nothing, which is
the vacuity this campaign keeps catching in my own work.

It is retained, because "no leak and consistent answers" is still a true
weaker property, and three cases are added that hold both callers at
`os.mkdir` itself, which is where the collision now happens:

- the home create race — no leak, consistent answers;
- **the child create race**, which the review asks for by name;
- the loser REOPENS rather than refusing. A refusal would also satisfy the
  contract; this pins the stronger outcome the design actually reaches.

Run five times over: stable.

### Gates

- `test_input_delivery`, `test_workspaces`, `test_lifecycle_composition`,
  `test_ended_runtime_adoption`, `test_negative_race_endings`,
  `test_output_custody_engine`, `test_credentials_engine` together —
  **152 tests, OK**, 4 narrow skips, against Docker 29.1.3

No package gate is claimed: `tests/manager/test_oci.py` remains destroyed under
W33936 and its restoration is blocked on owner authority there.

## State

**Passed back for independent re-review.** The no-link/exact-path proofs at
both levels, sequential restart reopen, distinct-attempt allocation, exact
cleanup and retry, sibling isolation and every readable/read-only delivery
behaviour are unchanged and green.
