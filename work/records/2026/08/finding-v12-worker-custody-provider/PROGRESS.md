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

## 2026-08-29 — eighth implementation round (`baton.claude`)

State: **awaiting review.** Both findings of `review-2026-08-29T13-48-14Z.md`
are corrected and the review's two regressions pass — one of them after being
kept probative rather than merely green.

### [P0] — the last path operand is gone

Round seven found exactly the limitation round six recorded in its own finding:
`storage` was still an ordinary caller operand, so deriving
`<storage>/<assignment>/workspace` from it was still caller path selection, one
component deeper. The reviewer is right that this is not sufficient.

The workspace STORE is now a deployment record, minted only by
`configured_workspace_storage(store)` — the same shape, the same
journal-versus-projection cross-check and the same fail-closed directions
W33936 established for the group. `attempt_custody_root(workspace_group,
workspace_storage, assignment_id, which)` takes two capabilities and a name and
no path at all, so there is no operand left through which an unrelated
directory could be selected.

I kept `assignment_workspace` taking a path, and want that on the record as a
decision rather than an oversight: it is the deployment's own ALLOCATION act,
and the requirement is about the custody MOUNT. A caller may still allocate
where it can already write; it can no longer have a container mounted there.

### [P1] — and the ordering, mutation-checked

The result root was created before its parents were proved, so an aliased home
had `workspace/result` written inside the target and only then raised. Parents
are proved first now, and the result path is derived from the RESOLVED real
workspace, so the write cannot traverse a link that appears between the proof
and the creation.

**The review's regression needed one change to stay probative.** Passing a raw
path now refuses at the type check — before the ordering under test is reached
— so the case would have passed without exercising anything. It is driven
through the real store capability instead, with the alias inside the configured
store, which is where a worker-era alias would actually appear. Driving the
superseded ordering under the corrected code reproduces the reviewer's failure
verbatim; the fix clears it.

### Verification

    PYTHONPATH=src python3 -m unittest tests.manager.test_custody
    -> 41 tests, OK   (was 41: 39 pass, 2 fail)

    ...with test_custody_engine, test_workspaces (+9 new store-record cases),
    test_lifecycle_composition, test_input_delivery, test_worker_container,
    test_oci, test_oci_engine, test_attempts, test_intake, test_sealing,
    test_output, test_store, test_dependencies, test_text_sweep,
    test_negative_race_endings, test_ended_runtime_adoption,
    test_parallel_runner
    -> 907 tests, OK (12 skipped)

`test_dependencies` caught `workspace_storage` as an undeclared public operand;
it is declared, and named apart from the allocation boundary's `storage` on
purpose — one name for a caller's path and a deployment's capability would be
one name for the two things this whole correction separates.

### Two failures in the shared tree that are NOT this Work's

Both are reviewer regressions against Works I do not hold, and both look real
to me. Reported rather than touched:

- `tests.manager.test_worker_entry.
  test_a_receive_timeout_is_lost_instead_of_escaping` — **W39356**, queued at
  `baton.impl`. `_Reader._more()` does not catch an exception from
  `channel.receive`, so a peer timeout escapes `converse` instead of becoming
  the closed `lost` ending. `surplus()` already catches; `_more()` does not.
- `tests.manager.test_claude_agent.
  test_a_provider_created_link_cannot_copy_the_bearer_to_the_proposal` —
  **W39357**, active with `baton.codex`. This one is serious and it is mine by
  authorship: `_copy_tree` validates the SOURCE, but the candidate is
  provider-controlled afterwards and neither `_diff` nor `_publish`
  revalidates it, so a symlink the provider creates is followed by
  `shutil.copyfile` and can copy the mounted bearer into the proposal. It is a
  credential-exfiltration path in code I wrote, and it is captured as a
  failing regression in the tree so it cannot be lost.

### Still open, unchanged

Helper lifetime, ending composition, retry/restart/crash regressions,
compatible-Podman certification, and the `archive` content ruling.

## 2026-08-29 — ninth implementation round (`baton.claude`)

State: **awaiting review.** Both [P0]s are corrected by deleting the interval
they lived in rather than defending it a tenth time.

### What the nine rounds were actually about

Every correction until now defended an object a caller HELD between the
authenticated lookup and the use — a plain mapping, one with the right
basenames, the nominal `AllocatedRoots`, that type with its mutators
overridden, with `dict` off its bases, with its members behind a private
attribute; then no object but a caller `storage` path; then a
`WorkspaceStorage` minted from durable state; then a `CustodyRoot` minted from
a valid derivation. The reviewer's sentence is the right diagnosis of round
eight: mirroring `WorkspaceGroup` "copies durable authority back into the
forbidden process-state interval."

So this round deletes the interval. `custody_vector(engine, *, image_digest,
name, store, assignment_id, operation, which)` reads the deployment's
configured store and group out of the durable record, derives and proves the
attempt's root, and composes the argv **in one act, handing no path-bearing
object to anybody**. `CustodyRoot` and the public `attempt_custody_root` are
off the surface — there is nothing to retarget because nothing is held, and no
later re-read because there is no earlier hand-off.

`WorkspaceStorage` survives as the read's own return value inside that one
frame. A holder can still retarget one; it no longer reaches anything, which
is the point and is why the reviewer's own case now asserts exactly that.

This is the rule the dossier wrote down at round six — `object.__setattr__`
reaches any slot and no representation closes that, so the guarantee must be
that nothing re-reads the object — finally applied to every hop instead of one.

### The reviewer's two regressions, re-aimed rather than deleted

Both drove `object.__setattr__` on a held capability and expected a refusal.
With the handoff gone there is no operand to corrupt, so a refusal assertion
would have been asserting the wrong thing. They assert the stronger property
now: the retarget still succeeds on the held object, and the composed mount is
still this attempt's own directory with the unrelated path absent from the
argv entirely. The signature case lists the operands and names the five that
are gone.

### The literal label that stopped the shared inventory

Round eight's `check_workspace_storage` passed its keyword `what` to
`boundaries.text` instead of a literal. The inventory attributes a crossing by
the label at the site, so a variable is one it cannot key — and it RAISES
rather than guessing, which stopped the whole package's scan from producing any
verdict and blocked every checkpoint's inventory item, not only this one. I
reported it from W39356 when I did not hold this Work; holding it now, it is
fixed. `check_workspace_group`, the function that round mirrored, calls no
boundary helper at all, which is why the pattern did not carry the constraint.

### Verification

    PYTHONPATH=src python3 -m unittest tests.manager.test_custody
    -> 42 tests, OK   (was 41: 40 pass, 2 fail)

    ...with test_custody_engine, test_workspaces, test_dependencies,
    test_lifecycle_composition, test_input_delivery, test_worker_container,
    test_oci, test_oci_engine, test_attempts, test_intake, test_sealing,
    test_output, test_store, test_text_sweep, test_worker_entry,
    test_parallel_runner
    -> 999 tests run; the only failure is not this Work's (below)

`test_dependencies`' stale-declaration half caught the leftover
`workspace_storage` entry, which is removed — the operand no longer exists.

**The boundary-inventory scan was re-run after the label fix and had not
finished when this was written.** What is established is that the raise which
prevented any verdict is gone; whether the gate is otherwise green is
W39666's question, and that Work already carries it.

### Not this Work's, and reported

`tests.manager.test_claude_agent.
test_verification_cannot_swap_a_checked_parent_for_the_credential_root` fails —
a new regression against **W39357**, which is active with `baton.codex`. It is
sharp and correct: `O_NOFOLLOW` protects only the FINAL component, and the
task's verification command runs provider-authored code *between*
`_checked_tree`/`_diff` and `_publish`, so it can replace an intermediate
directory with a link and redirect the later open into the credential root.
Mine by authorship, not mine to correct under this claim.

## 2026-08-29 — tenth implementation round under W36540 (`baton.claude`)

State: **awaiting review.** Both findings of `review-2026-08-29T22-28-08Z.md`
that this round owns are addressed. The four outcomes the review lists as
still-open remain open and are unchanged; a decomposition proposal for them is
in `PLAN.md` and is deliberately not minted here.

### [P0] The final path-bearing handoff was the return value

The reviewer is right, and the part worth admitting is that round nine's own
finding entry described the correct rule and then stopped one hop short of
applying it. Nine rounds deleted the interval around every OPERAND. The tenth
one was in the answer: `custody_vector` authenticated the source, put it in
`--mount source=` and handed the list back, so the caller held the
authenticated path between the durable lookup and the engine use. That is the
same defect, one layer out.

The review's second sentence is the one that decided the shape: *a tuple or
another frozen argv wrapper would not close the boundary*. It would not — a
holder of a path can compose its own vector, and hardening the container is
exactly the mistake the previous nine rounds already made. So the correction
is not a tenth container.

`custody_act(engine, run, *, image_digest, name, store, assignment_id,
operation, which)` performs the act: it reads the durable record, derives and
proves the root, composes the argv, RUNS it through `oci.EnginePort` and
answers. There is no return value a caller can execute, because the execution
already happened inside the call. `custody_vector` is `_custody_vector` now,
reachable only by the act that runs it.

`run` is the engine port — the same seam `OciAdapter` takes, under the same
name. It is the boundary of the process rather than a party inside it, so
handing it the argv is the invocation and there is no interval after it. It
also puts custody under the §13 durable-secret sweep `EnginePort` owns, which
composing-and-returning never had.

What a holder keeps is `CustodyAnswer`: the verb, the exit status, the
custodian's document as a read-only mapping, and a bounded diagnostic. No host
path — the program answers paths relative to its own mount, which is the only
namespace it knows — and no command vector. Immutable, and `ok` requires both
a zero exit AND a readable document, because a zero exit this manager cannot
account for is not custody.

### [P1] The docstring the record already contradicted

`custody_vector`'s docstring said `--rm` plus foreground meant a crash leaks
no capability a later manager would have to reclaim. This dossier's first
review found otherwise and `PLAN.md` has carried reclaimable lifetime as NOT
DONE ever since. The docstring now says what `--rm` actually buys — removal on
the engine's normal path — and names the owed work and the unread
`CUSTODY_NAME` explicitly. An implementer reads the docstring, so a false
sentence there is as authoritative as one in the record.

### Test changes, stated rather than absorbed

The reviewer's regression `test_the_authenticated_mount_is_not_returned_as_a_
mutable_handoff` asserted that mutating the returned argv's mount member does
not stick — a requirement **no returned list can meet**, which is the review's
own point. It now asserts what the review actually asked for: the act returns
a typed answer, `custody.custody_vector` does not exist, and the answer's
rendering contains no host path, no `--mount`, no engine name and no bind
spec. Three further cases of mine hold the answer's immutability, the
no-account-no-custody rule and the bounded diagnostic.

The daemon-free fixture changed shape once, at one place: `vector()` now
returns what the ENGINE PORT was handed rather than what a public function
returned. Every existing argv assertion — the single mount, the closed
program, the worker identity, the restrictions — is unchanged and still runs,
and it now runs through the real public act instead of a composer nothing
would have called.

### Verification

From `v12/python`:

    PYTHONPATH=src python3 -m unittest tests.manager.test_custody
      tests.manager.test_workspaces tests.manager.test_dependencies
    -> 147 tests, OK (1 skipped)   [test_custody is 47, was 43]

    PYTHONPATH=src python3 -m unittest tests.manager.test_custody_engine
    -> 7 tests, OK (1 skipped: podman is not on PATH)

The real-daemon gate ran: all six Docker cases, including the acceptance —
the manager refuses to remove the worker's tree before the act and removes it
after — now drive `custody_act` with a real engine port rather than composing
an argv and running it themselves.

    PYTHONPATH=src python3 -m unittest
      tests.manager.test_boundary_inventory.EveryReceivingEntryHasOneOwner
      tests.manager.test_boundary_inventory.EveryProbeProvesItArrived
      tests.manager.test_secrets.EveryDurableWriterIsGuarded
    -> 21 tests, 6 failures, in 1643s

    `diff --check` over the working tree: passed.

THE SIX ARE THE SAME SIX THIS TREE ALREADY HAD, measured earlier the same day
before this round touched `custody.py`, and they are the shared-gate failures
`PLAN.md` item 8 already records as blocked on orphaned entries that predate
this Work. The custody regression the review filed is the one that is gone.

WHAT THIS ROUND ADDS TO THAT GATE, stated rather than left for the reviewer to
find. `custody.py` contributes seven unowned receiving entries —
`custody_act`'s `engine`, `image_digest`, `name`, `assignment_id`,
`operation`, `which` and `run` — against a total of 132. Six of those seven
are `custody_vector`'s own parameters under a new name; the one this round
genuinely adds is **`run`**, and it is a real operand with a declared
rationale in `test_dependencies`.

`CustodyAnswer` was written with a public `__init__` in the first cut of this
round, which put four more caller entries into that same failing gate.
Measuring it is what caught it, and the correction is not a gate-dodge: the
class has **no public constructor** now, because an answer is what one act
REPORTED and a caller that could mint one could report an act that never
happened — the same rule every capability in this package is already under.
`_answered` is private and is called in exactly one place.

### Still open, unchanged, and not started in this round

Bounded/derivable/restart-reclaimable helper lifetime; ending composition and
its retry/restart/crash regressions; the `archive` ruling, which is the
approver's; compatible-Podman certification; and `custody.py`'s absent
`test_boundary_inventory` entries. `PLAN.md` carries the decomposition the
review directs for the round that follows this handoff.

## 2026-08-30 — eleventh implementation round (`baton.claude`, W36540 impl claim)

Answering `review-2026-08-30T04-07-53Z.md`. Both parts of the one [P1] are
corrected, the reviewer's two additive regressions pass, and the focused suite
is 59 cases. The four deferred outcomes are untouched, as the review directs.

### [P1a] `ok` meant "some JSON came back", and it should have meant this act

You are right, and it is worth being exact about what was being reported: a
`normalize` act carrying an `inspect` document was recorded as a successful
normalization of a tree nothing had touched. The tenth round validated the verb
it SENT and nothing about what came back.

`_CUSTODY_RESULT` now writes down, per verb, the closed member set and the type
of every member `CUSTODY_PROGRAM` prints, and `_accountable` holds the returned
document to the requested verb's entry before `ok` can be true. Member names
alone would not have been enough — `entries` is a COUNT for `normalize` and a
LIST for `inspect` — so types are part of the identity of an answer here rather
than a detail of it. `running_as` is held to two integers, because an act whose
custodian identity is unstated is one this manager cannot attribute, and
attribution is the entire mechanism this Work rests on.

TWO DOCUMENTS ARE ACCOUNTABLE and only one can be `ok`. The program can print
its own typed refusal, and discarding that as "a document for the wrong verb"
would throw away the one sentence saying why the act did not run. It is
retained; it can never be `ok`.

AND A MISMATCH IS NOT PARTIALLY BELIEVED, which is your "without guessing at
partial documents". None of it becomes `answer`. `unaccounted` carries THIS
MODULE'S own words about what it could not account for, and the act's stderr
stays separately in `diagnostic`, so the two provenances never blur.

### [P1b] The freeze, and why it is a tuple

`MappingProxyType` protected the outer mapping and nothing inside it. `_frozen`
rebuilds the document bottom-up: mappings behind a proxy over a fresh
dictionary nothing else references, lists as tuples, scalars as themselves.

THE TUPLE IS THE PART TO SCRUTINISE, and I want it visible rather than
discovered. A `list` subclass refusing its mutators would have compared equal
to a list, serialized as one, and left every existing assertion untouched —
and `list.append(frozen, x)` reaches straight past it, exactly as
`object.__setattr__` reached past six representations of `AllocatedRoots` in
rounds one to six. Taking the convenient defence in the round that answers a
finding about a defence that only looked sufficient would have been this Work's
characteristic mistake for the seventh time. The cost is that a frozen sequence
no longer equals the list it came from, and three assertions changed to say so.

### The two tables are compared, because otherwise they are two contracts

`_CUSTODY_RESULT` is a second copy of what `CUSTODY_PROGRAM` prints.
`TheAnswerContractMatchesTheProgram` runs the REAL program for all six verbs
over a populated tree — file, nested file, directory, link — and requires this
module's validator to accept every document it printed. Without that case,
holding the daemon-free fixture to the module's own table would have proved
only that the fixture agrees with the validator.

### FOUR TEST CHANGES YOU SHOULD LOOK AT

1. YOUR NESTED REGRESSION asserts `answer["running_as"] == [65532, 65532]`.
   It reads `(65532, 65532)` now. That is not a relaxation — it is the direct
   consequence of the only non-bypassable freeze, and the alternative that
   would have kept your line verbatim is the guarded-list defence above. Your
   `assertRaises` half is unchanged and passes.
2. THE DAEMON-FREE FIXTURE emits shape-correct documents per verb now. It
   returned `{"custody": op, "entries": 3, "running_as": [...]}` for every
   verb, which is a valid `inspect` document and an invalid `normalize` one,
   so without this every case would exercise the refusal path. The stubs are
   spelled out rather than derived from `custody._CUSTODY_RESULT`, because a
   fixture that agreed with the validator by construction would prove nothing;
   the program-agreement case above is what binds them.
3. THREE CASES SERIALIZED THE ANSWER with `json.dumps(dict(answered.answer))`
   to assert no host path appears in it. A `mappingproxy` nested inside is not
   a `dict`, so that call now raises on any document with nested records —
   and rebuilding a view to serialize it was re-deriving the account anyway.
   They use `answered.rendered`, the canonical serialization produced once at
   mint time, which covers the whole nested document rather than one level.
4. THE REAL-DAEMON ACCEPTANCE at `test_custody_engine.py:168` asserted the
   same list equality as (1) and failed against a real container. Same change,
   same reason. Worth noting that this is a failure the review could not have
   seen, because the managed reviewer has no daemon.

### Closed as well, and it was this Work's own

`test_secrets`' §13 sweep reported `workspaces.py:configure_workspace_storage`
as a durable writer with no coverage. That is a shared gate this Work has been
leaving red for the whole tree since round eight, when the act was written in
the shape of `configure_workspace_group` directly above it and the coverage
declaration was not carried along — the same omission as round nine's boundary
label, and the same lesson. The declaration is the group's own rationale one
operand over, and I checked it is TRUE rather than convenient: the only value
written is a path `check_workspace_storage` has proved, and it rides
`manager_signature("workspace-storage.configure", {"place": place})` into the
journal the sweep walks.

This is NOT the deferred custody boundary-inventory ownership item, which is a
different gate over `custody.py`'s own entries and stays open.

### Verification

From `v12/python`:

    PYTHONPATH=src python3 -m unittest tests.manager.test_custody
    -> 61 tests, OK   (50 before: 48 pass + your 2 failing; +11 of mine)

    PYTHONPATH=src python3 -m unittest tests.manager.test_custody
      tests.manager.test_workspaces tests.manager.test_dependencies
    -> 159 tests, OK (1 skipped)

    PYTHONPATH=src python3 -m unittest tests.manager.test_custody_engine
    -> 7 tests, OK (1 podman skip) -- SIX REAL DOCKER CASES INCLUDING THE
       ACCEPTANCE. Docker is reachable in this implementer context, so the
       gate the managed reviewer cannot start was run, and it is what caught
       change (4) above.

    PYTHONPATH=src python3 -m unittest tests.manager.test_secrets
    -> 90 tests, OK   (was 89 pass / 1 fail on the writer above)

    PYTHONPATH=src python3 -m unittest tests.manager.test_boundary_inventory
    -> NOT COMPLETED. Started early in this round and still running when the
       handoff was written, as it also was at the ninth round. No verdict is
       claimed from it either way. What this round can say is narrower and is
       measured: it adds no `boundaries.*` call site, so it introduces no new
       crossing for that gate to attribute; `custody.py`'s seven unowned
       receiving entries are unchanged and remain the deferred inventory item.

    `diff --check` over the working tree: passed.

### Still open, unchanged, and deliberately not started in this round

Archive-content semantics; bounded/restart-reclaimable helper lifetime; ending
composition and its retry/restart/crash regressions; compatible-Podman
certification; and `custody.py`'s absent `test_boundary_inventory` entries.
`PLAN.md` carries the decomposition the review directs for the round that
follows this handoff, still as a proposal rather than minted Work.
