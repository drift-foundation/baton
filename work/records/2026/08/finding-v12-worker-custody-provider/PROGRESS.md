# Progress

## 2026-08-29 — the mechanism, proved before it was wired

Claimed W36540 at seq 37604. First round on this record.

### Plan 1: the defect, revalidated against the tree

`DockerConfiguredGroup.test_manager_cleanup_of_worker_content_is_measured_not_
assumed` still passes, which means the failure it documents is still real: a
worker-created directory with content in it, at the worker's own umask, is one
the manager can neither `chmod` nor unlink inside. The record's account matched
the tree, so I built on it rather than re-deriving it.

### Plan 2: the mechanism, and TWO corrections that came from running it

`custody.py` — a short-lived helper with M36166's three constraints, each
built as a property of the argv rather than a promise:

**ONE MOUNT, the exact attempt directory,** at a fixed container path. Absent
rather than denied: a path that is not mounted cannot be reached by any means,
which survives a bug in the program it is running. There is no target operand,
so no caller decides what the program walks.

**THE OWNING WORKER IDENTITY, and this is the whole mechanism.** The helper
runs as the same uid the worker ran as, so it OWNS every object the worker
created — and an owner may always `chmod` its own object at whatever mode the
worker chose. There is no mode a worker can pick that locks the custodian out,
which is what "unconditional" has to mean if it is to survive a worker that
did not cooperate. The manager never acquires that ownership itself.

**TYPED MANAGER-OWNED OPERATIONS ONLY.** The vocabulary is M36166's exact six,
and the program is a CONSTANT of the module. There is no command operand at
all — only a verb, checked against the closed set on the composing side AND by
the program's own copy on receipt.

**I ran it before wiring it, and it was wrong twice.** Both corrections are in
`evidence/w36540-probe-2026-08-29.txt`:

1. **The custodian must not touch what it does not own.** The first cut
   normalized everything under the mount and then the mount itself, and died
   with EPERM on the mount — which is the attempt directory the MANAGER owns.
   Ownership is the rule now, and it is the same rule that makes the act
   unconditional. The transcript reports `not_ours: 5`.
2. **The custodian needs the configured workspace group.** The first cut
   composed none, and the helper could not so much as ENTER the workspace: the
   root is `02770` and manager-owned, so uid 65532 without the group has no
   `x` on it. It listed the attempt home, reported five entries that were none
   of its business, and never reached the worker's. It takes W33936's
   `WorkspaceGroup` capability now, on that Work's rule.

### The property, on a real daemon

    BEFORE  the manager's own removal          REFUSED (owner named)
    CUSTODY normalize                          entries 3, not_ours 5,
                                               running_as [65532, 65532]
    AFTER   the same removal, unchanged        REMOVED = True, tree gone

The refusal before the act is what makes the removal after it mean anything;
without it the case would prove only that `rm` works.

### What is NOT done, and I would rather say so than imply otherwise

**Plan item 4 — composing the helper into the cleanup ending — is not wired.**
The helper is proved to remove the defect and the manager's own
`discard_workspace` succeeds after it, but nothing yet calls the custody act
automatically on the fail-closed path. That is the remaining half of this Work
and it is the next round's.

**The Podman half is blocked by a constraint already on the record.** Under
rootless Podman the worker cannot write the workspace at all — the manager's
supplementary gid does not map through the user namespace — so this suite
cannot even establish its precondition. That is the same finding W33936 raised
for a ruling this morning, now blocking a second Work. Under rootful Podman
the manager would be root, and a root manager can remove anything, so the
"before" refusal this acceptance turns on cannot occur either. `PodmanCustody`
SKIPS rather than passing.

**A false pass I caught and fixed.** `PodmanCustody` first reported six passes
on a host with no Podman: my helpers used the module-level `ENGINE` constant
instead of `self.engine`, so the Podman class was silently running Docker. It
inherits the engine-parameterized gate now and skips honestly.

### Gates

- `test_custody` — **17 tests, OK** (vocabulary, mount, identity, restrictions);
- `test_custody_engine` — **6 tests OK**, 1 honest Podman skip;
- `test_workspaces` 69, `test_secrets` 90, `test_dependencies` 21,
  `test_text_sweep` 3, `test_parallel_runner` 36 — OK;
- the complete serial registry, now eleven modules.

## State

**The mechanism is built and proved; the composition is not.** Passed back for
independent review of what is here, with the remaining half named.

## 2026-08-29 — the two [P0]s, and the vocabulary made real

Reclaimed W36540 at seq 37704. Both [P0]s corrected, the [P1] vocabulary
implemented, the [P1] lifetime finding NOT corrected.

### [P0] The mount contained the deliveries

The reviewer is right and my own probe transcript is the evidence: every
caller passed `dirname(roots["workspace"])`, the assignment HOME, whose
siblings are `credentials`, `credential-state`, `inputs` and the launch root —
and the helper's own `inspect` answer listed all four. I read that output,
wrote "not_ours: 5" into the evidence as if it were reassurance, and did not
see that skipping what the helper does not own is not the boundary. **The
pinned boundary is absence, and I proved exposure and called it a skip.**

`CustodyRoot` is a capability now, minted only by `attempt_custody_root` from
`assignment_workspace`'s own answer. There is no host-path operand at all, so
a repository, a credential root or an unrelated sibling cannot be selected —
and the mount is the exact workspace or result directory, never their parent.
The engine case asserts the four forbidden siblings are ABSENT from `inspect`.

One case had to change rather than pass: `test_the_custodian_touches_nothing_
it_does_not_own` asserted `not_ours > 0`, which was only ever true because the
mount was too wide. It measures the manager-owned roots outside the mount now.

### [P0] A nested mode-zero directory stayed outside custody

`os.walk(topdown=False)` must enter a directory before the bottom-up yield
that would have made it enterable, so a mode-zero directory inside a mode-zero
directory was silently omitted from the walk and the act still reported
success. The existing matrix put one hostile mode on `nested`, which was
exactly shallow enough to hide it.

The walk is top-down now and each OWNED directory is made traversable on the
way IN, before anything descends. Links are never followed. Measured at two
levels of `0000`: `read`, `hash` and `archive` reach `outer/inner/deep.txt`,
`normalize` changes 3, `discard` removes 3.

### [P1] Four verbs were a future-work list

`read`, `hash`, `archive` and `discard` printed "not composed by this build"
and exited 3, while `CUSTODY_OPERATIONS` advertised them. A closed vocabulary
is a capability claim, not a list of intentions. All six are implemented under
manager-owned result shapes: the three reading acts share one walk and report
an unreadable entry rather than omitting it, `archive` answers a manifest with
a tree digest rather than a tarball this manager would then have to trust, and
`discard` removes bottom-up over a tree already made traversable, counting
what it does not own instead of touching it.

### NOT corrected, and it is a real finding

**[P1] `--rm` does not establish crash-bounded lifetime.** The reviewer is
right: `--rm` removes a container when it EXITS and does nothing about one
still running after the manager disappeared. There is no timeout, no durable
act identity, no observation path and no restart reclamation, and my source
comment and test claimed a property they do not establish. Correcting it means
a derivable act name, a bounded runtime and a reclamation path a restarted
manager can drive — which is a design cut, not an edit, and I would rather
return the two [P0]s than bundle a half-considered fourth mechanism with them.

**The composition into the ending is still not wired**, unchanged from the
last round.

### Gates

- `test_custody` — **22 tests, OK**, the reviewer's six among them;
- `test_custody_engine` — **7 tests OK**, 1 honest Podman skip;
- `test_workspaces` 69, `test_secrets` 90, `test_dependencies` 21,
  `test_text_sweep` 3 — OK. The operand registry caught `attempt_root` going
  stale on its own.

## State

**Both [P0]s and the vocabulary [P1] are corrected.** Passed back; the
lifetime [P1] and the ending composition are named as not done.

## 2026-08-29 — the mint stopped laundering, and links became objects again

Reclaimed W36540 at seq 37753. The [P0] and the symlink [P1] are corrected;
the read/archive [P1] and the accepted lifetime/composition half are not.

### [P0] The mint laundered caller paths into capabilities

`attempt_custody_root` took `roots`, proved only that `inputs` and `workspace`
keys existed, and canonicalized whatever `workspace` said — so a caller could
pass the authentic inputs path beside ANY unrelated absolute directory and get
a valid `CustodyRoot` for it. **A type that anything shaped like a dict can
obtain is not a capability; it is a cast.** I introduced the capability last
round precisely to stop a raw path being chosen, and left the door open one
level up.

The layout is PROVED now rather than read: `assignment_workspace` builds
`<home>/inputs` and `<home>/workspace` as siblings, each named for its role,
and an arbitrary path cannot satisfy that by accident. What gets mounted is
then re-derived from the proved home rather than taken from the mapping.

**And the `result` arm was a second escape, this one available to the ended
worker.** The workspace is worker-writable, so `result` is a name the worker
can leave as a symlink; `os.path.isdir` followed it, `_real` resolved it, and
a worker-controlled alias became a mount. Every component is `lstat`ed now,
from the home down — a link anywhere on the way is refused, and so is an entry
this manager does not own.

### [P1] Directory symlinks vanished from inspect and survived discard

My traversal correction dropped links out of `directories` before the yield.
That stopped descent, correctly, and also made the link OBJECT invisible:
`inspect` answered an empty list for a root holding one directory symlink, and
`discard` reported success while leaving it in place.

Links ride with the files now — one entry to report and one entry to unlink,
never a way in. The link goes and its target is untouched.

### NOT corrected

**[P1] `read` and `archive` return descriptions, not custody.** The reviewer is
right: a 4096-byte replacement-decoded head is not the file, and a manifest
proving bytes once existed is not an archive of them. Correcting it needs
explicit manager-owned output contracts, a place to preserve content, and
streaming with bounds — `handle.read()` also loads an arbitrary worker file
whole into a helper capped at 512 MiB, which turns an unconditional act into an
OOM exit on a large object. That is a design cut and I am not bundling a
half-considered one with two safety corrections.

**The lifetime and composition half is unchanged** — no derivable act identity,
no bounded execution, no restart reclamation, no ending composition, and
compatible Podman still blocked.

### Gates

- `test_custody` — **26 tests, OK**, the reviewer's four among them;
- `test_custody_engine` — 7 OK, 1 honest Podman skip;
- `test_workspaces` 69, `test_dependencies` 21, `test_secrets` 90,
  `test_text_sweep` 3 — OK.

## State

**The [P0] and the symlink [P1] are corrected.** Passed back; read/archive
custody and the lifetime/composition half remain open.
