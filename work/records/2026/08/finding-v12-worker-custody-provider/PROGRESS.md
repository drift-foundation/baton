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

## 2026-08-29 — provenance, not shape

Reclaimed W36540 at seq 38817. The [P0] is corrected; the remaining scope is
unchanged.

### [P0] Directory shape is not allocation provenance

The reviewer is right and the reasoning is one I should have applied to my own
correction. Last round I replaced a raw path with a structural proof — the two
paths share a parent, each carries its expected basename, all three are
manager-owned — and every one of those properties is reproducible by any
caller with `mkdir`. **Shape may validate authority; it cannot create it.** I
had built a check that looked like a capability and was a naming convention.

`assignment_workspace` now mints its answer. `AllocatedRoots` is a `dict`
subclass, so every existing caller still reads `roots["workspace"]` unchanged
and nothing else in the tree had to move — and a plain dict is not an instance
of it, which is the entire difference. `attempt_custody_root` requires that
type before anything else, and the structural checks still run behind it:
shape validates the authority it can no longer manufacture.

A `dict` subclass rather than a wrapper was deliberate. The roots have always
been a mapping and every caller reads them as one; making provenance a wrapper
would have meant editing all of them to prove a property none of them needed.

### Unchanged and still required

Complete recoverable read/archive output custody with streaming and bounds;
bounded, derivable, restart-reclaimable helper acts; the ending composition;
retry/restart/crash regressions; compatible Podman certification.

### Gates

- `test_custody` — **27 tests, OK**, the reviewer's forged-shape case among
  them;
- `test_custody_engine` 7 OK with one honest Podman skip;
- `test_workspaces` 69, `test_input_delivery` 54, `test_dependencies` 21,
  `test_secrets` 90, `test_text_sweep` 3 — OK. `test_input_delivery` matters
  here: it is the heaviest consumer of `assignment_workspace`'s answer and is
  what says the minted type did not disturb anything reading it as a mapping.

## State

**The [P0] is corrected.** Passed back; the read/archive, lifetime and
composition scope remains open.

## 2026-08-29 — the answer became immutable

Reclaimed W36540 at seq 38887. The [P0] is corrected; the open scope is
unchanged.

### [P0] An authentic allocation answer could be retargeted

Right again, and this is the third round on one boundary — worth saying
plainly. Last round I made `assignment_workspace` mint a nominal type so that
shape could no longer manufacture authority. But `AllocatedRoots` was a
MUTABLE `dict` subclass and `attempt_custody_root` checked the type and then
trusted the paths currently inside it. So a caller could take an authentic
answer, overwrite its two members with an unrelated manager-owned parent, and
hand the same authentic object on — passing the nominal check and every
structural check behind it.

**A capability whose contents the holder may rewrite delegates nothing.** It
names a thing and then lets the holder choose which thing it named. I had
fixed who can MINT the answer and left open what the answer SAYS.

The answer is immutable now. Every mutating entry point is closed —
`__setitem__`, `__delitem__`, `update`, `setdefault`, `pop`, `popitem`,
`clear` — enumerated rather than assumed, because `dict` has more of them than
the two obvious ones and each reaches the same members. `copy()` deliberately
answers a PLAIN dict: a copy is a caller's own mapping that happens to hold the
same strings, and typing it as an allocation answer would hand back exactly the
forgery the mint refuses.

### The reviewer's case moved earlier

Their regression mutated the roots and expected the refusal from
`attempt_custody_root`. The correction refuses at the WRITE instead, which is
stronger: there is no window in which an authentic object holds foreign paths
at all. The case now brackets both ends, so either refusal satisfies it, and it
additionally proves the answer is unchanged afterwards and that the other five
mutating doors are closed too.

### Unchanged and still required

Complete recoverable read/archive output custody with streaming and bounds;
bounded, derivable, restart-reclaimable helper acts; the ending composition;
retry/restart/crash regressions; compatible Podman certification. This review
did not narrow any of them and neither do I.

### Gates

- `test_custody` — **28 tests, OK**, the reviewer's regression among them;
- `test_custody_engine` 7 OK with one honest Podman skip;
- `test_workspaces` 69, `test_input_delivery` 54, `test_attempts` 228,
  `test_oci` 83, `test_dependencies` 21, `test_secrets` 90 — OK. Those matter
  this round: making the allocation answer immutable would break any caller
  that wrote into it, and they say none does.

## State

**The [P0] is corrected.** Passed back; the read/archive, lifetime and
composition scope remains open.

## 2026-08-29 — not a dict at all

Reclaimed W36540 at seq 38929. The [P0] is corrected; the open scope is
unchanged.

### [P0] A mutable builtin cannot be made immutable by overriding it

The reviewer's sentence is the whole finding: **overriding more methods cannot
close explicit base-class invocation.** `dict.update(roots, {...})`,
`dict.__setitem__(roots, ...)` and `roots |= {...}` each reach the base
implementation without ever calling an override, and the last of those minted
an unrelated custody root — the original host-path escape through a different
door.

`AllocatedRoots` does not inherit from `dict` now. The members live in a
private attribute and the class implements the READ half of the mapping
protocol and nothing else: `__getitem__`, `__iter__`, `__len__`,
`__contains__`, `keys`, `items`, `copy`. There is no inherited mutator to
call, and `dict.update(roots, ...)` fails on its own argument type because the
object is not a dict.

**That refusal is Python's, not ours, and it is the stronger one.** It cannot
be talked out of by a future edit and it is exactly what the previous two cuts
could not produce. The typed refusals that remain — `__setitem__`, `__ior__`,
`update` and the rest — exist for the DIAGNOSTIC, so a caller reaching for one
gets a sentence rather than a bare `TypeError`. The guarantee is the
representation.

### Three rounds, one lesson

Raw path, then reproducible shape, then a mutable nominal type, then an
overridable one. Each round I closed the door I had just been shown. The
question I should have asked at the first correction — *what else can still
reach the mount* — is the one the reviewer has now had to ask four times.

### Two of the reviewer's cases assert a different exception now

`dict.__setitem__` and `dict.update` raise `TypeError`, not `ContractRefusal`,
because the object is not a dict — and that is the correction rather than a
shortfall. Both cases accept either, and both additionally prove the roots are
UNCHANGED afterwards. The update case goes further: it mints from the
authentic answer and asserts the result is this attempt's own workspace and
not the unrelated one, so the retarget is proved impossible rather than merely
detected.

### The operand guard caught a real thing

Adding `get(key, default)` for completeness put mapping-protocol words into
the declared operand vocabulary. `test_dependencies` refused them, correctly:
a public parameter here is a domain operand or it should not exist. `get` and
`values` are gone — nothing reads the roots that way.

### Unchanged and still required

Complete recoverable read/archive output custody with streaming and bounds;
bounded, derivable, restart-reclaimable helper acts; the ending composition;
retry/restart/crash regressions; compatible Podman certification.

### Gates

- `test_custody` — **31 tests, OK**, the reviewer's three among them;
- `test_custody_engine` 7 OK with one honest Podman skip;
- `test_workspaces` 69, `test_input_delivery` 54, `test_attempts` 228,
  `test_oci` 83, `test_intake` 74, `test_dependencies` 21, `test_secrets` 90
  — OK. Those are the consumers of the allocation answer, and replacing its
  type would break any that treated it as a dict.

## State

**The [P0] is corrected.** Passed back; the read/archive, lifetime and
composition scope remains open.

## 2026-08-29 — seventh implementation round (`baton.claude`)

State: **awaiting review.** The sixth review's [P0] is closed at its owner, and
one previously-open item is closed in part with the rest turned into an
explicit ruling request.

### The [P0], and why this round changed the owner instead of the guard

Six rounds closed six doors onto one room. The mount source was READ, at
custody time, out of an object the caller had held since allocation — first a
plain mapping, then one with the right basenames, then the nominal type, then
that type with `dict` mutators overridden, then with `dict` removed from its
bases, then with the members in a private attribute. The sixth is the proof
that overrides could never finish: `roots._members.update(...)` needs no method
of the class at all, so there was nothing left to override.

`attempt_custody_root` now takes no path-bearing operand:

    attempt_custody_root(workspace_group, storage, assignment_id, which)

It derives `<storage>/<assignment>/workspace` by the same rule and from the
same operands `assignment_workspace` allocates by. Nothing is read, so there is
nothing to forge, retarget or launder, and a seventh representation of
`AllocatedRoots` would be equally irrelevant.

I want to be exact about what this buys, because overclaiming it is how the
last six rounds each looked finished. It carries the ALLOCATION's authority and
not one bit more: any directory it can mount is one `assignment_workspace`
would allocate for the same operands, and a caller that can name those operands
can already call that function. What is now impossible — and was the finding —
is selecting something that is not an attempt workspace at all. The assignment
home, its `inputs`/`credentials`/`credential-state`/`custody` siblings, the
repository and every unrelated host path are unreachable rather than refused.

`AllocatedRoots` members also moved behind a `MappingProxyType`. That makes the
review's complaint false at its own site, and it is recorded in the finding as
defence rather than as the mechanism: `object.__setattr__` reaches any slot in
this language, which is precisely why the guarantee must not depend on it.

### Tests changed, and it is a signature change rather than a weakening

The mint's operands changed, so its call sites did. Every case kept its intent:

- the four retarget cases still prove `AllocatedRoots` refuses mutation, and
  now additionally prove the mint is unaffected by it;
- the reviewer's own
  `test_the_private_member_mapping_cannot_retarget_allocated_roots` is
  STRENGTHENED, not relaxed — it now asserts both that the backing mapping
  refuses the mutation and that the derived root is this attempt's own;
- `test_a_caller_mapping_cannot_launder_an_unrelated_host_root` and
  `test_a_caller_cannot_forge_the_expected_directory_shape` are re-aimed at the
  new boundary rather than deleted.

Added: `test_the_mint_reads_no_path_bearing_object_at_all` (the owner change,
asserted as a signature) and `test_an_attempt_identity_cannot_carry_a_path`.

### The reading verbs

Streaming and bounds are corrected: digests over 1 MiB chunks at constant
memory, and `read` carrying base64 bytes with an explicit `complete` member
instead of a 4096-byte U+FFFD-mangled head that said nothing about being
partial. A worker file bigger than the helper's memory bound used to END the
custody act, which is a property a worker could switch off by writing a big
file.

The streaming case runs under a real `RLIMIT_AS` bound smaller than the
fixture, and `test_the_bound_this_suite_imposes_can_actually_be_reached` drives
the superseded whole-file read under the same bound and requires it to fail
(measured: `MemoryError` at the slurp line, streaming exits 0). Without that
companion the streaming case would pass against a slurping implementation on
any host with enough RAM.

`archive` returning recoverable CONTENT is not done, and I am asking for a
ruling rather than guessing a third shape. It is in structural tension with
M36166's single mount: the one mount is the custody subject, so writing an
archive into it changes the tree being described; stdout is a bounded JSON
document; and a second manager-owned mount is what "mounted ONLY on the exact
attempt directory" forbids. The finding records the analysis and a proposal —
that after `normalize` the manager reads and archives host-side under its own
rules, narrowing the six-verb decision — which only the approver can take,
because M36166 names six. `archive` now declares `content: "manifest-only"` so
it cannot be mistaken for content custody meanwhile.

### Verification

    PYTHONPATH=src python3 -m unittest tests.manager.test_custody
    -> 39 tests, OK   (was 32: 31 pass, 1 fail)

    PYTHONPATH=src python3 -m unittest tests.manager.test_custody_engine
    -> 7 tests, OK (1 skipped: podman is not on PATH)
       Docker gate ran for real; a bare `docker run` on this host measures
       0.198s, which is what makes the suite's 2.4s consistent with the
       containers it starts.

    ...plus test_workspaces, test_lifecycle_composition, test_input_delivery,
    test_intake, test_oci, test_attempts, test_worker_entry, test_sealing,
    test_output, test_offers, test_sessions, test_credentials, test_launch,
    test_store
    -> 1050 tests, OK (4 skipped)

### Still open, unchanged

Bounded/derivable/restart-reclaimable helper lifetime; ending composition and
the retry/restart/crash regressions that depend on it; compatible-Podman
certification (externally blocked, unchanged reason). `archive` content custody
is now an open ruling rather than an open implementation.

### Owed, and named rather than quietly left

`custody.py` has no entries in `tests/manager/test_boundary_inventory.py` at
all — this module was never registered in that gate, and no review round has
raised it. It is owed. Not added this round: that gate is currently failing on
29 orphaned entries across seven modules that predate this work, and the file
carries another participant's uncommitted edit, so establishing ownership comes
first.
