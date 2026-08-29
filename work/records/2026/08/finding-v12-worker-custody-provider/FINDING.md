# Unconditional manager custody over an ended attempt's directories

## Discovery and ownership

Discovered under W33936 while proving the cleanup half of the approved
workspace-write mechanism. Created as the separate provider Work approver
ruling **M36166** requires:

> "Pin and create this as a separate provider Work. W33936's completed
> workspace-write round may be independently reviewed, but full cleanup
> acceptance remains open until the custody provider lands."

W33936 owns the workspace grant itself -- the configured group, the exact
`02770` allocation, the pre-launch proof and the supplementary `--group-add`.
This record owns what the manager can do with what the worker leaves behind.

## Confirmed defect

Measured on a real Docker daemon, with W33936's corrected mechanism in place
and the container proved absent:

- a FILE the worker created at the workspace root IS removable by the manager,
  because unlinking is a write to the group-writable root;
- an EMPTY directory the worker created is removable for the same reason --
  `rmdir` is a write to the parent;
- a directory the worker created **with content in it** is not. Its mode comes
  from the WORKER'S UMASK -- measured `drwxr-sr-x`, so the group has no write
  -- and the manager owns neither the directory nor a way to `chmod` it.
  `os.chmod` is `EPERM` and unlinking inside it is `EACCES`.

Any real worker creates populated subdirectories, so this leaves trees the
manager cannot remove. It is a CONSEQUENCE of the approved mechanism rather
than a defect in it: the group grants write on the ROOT, and what the worker
creates inside is the worker's.

W33936 made that failure honest -- cleanup fails closed and names which party
owns the object in the way, widening nothing -- which is a diagnosis rather
than a remedy.

## The pinned decision

**Confirmed by approver ruling M36166.** The required invariant is
UNCONDITIONAL MANAGER CUSTODY: after fencing and proving the exact worker
container absent, the Worker Manager must be able to inspect, read, hash,
archive, normalize and recursively delete **every** object in that attempt's
exact workspace and result directories, **regardless of worker-selected
modes**.

**Explicitly not the mechanism:** a worker umask of `002`. It may improve the
cooperative path; it cannot be custody, because custody may not depend on the
worker having cooperated.

**The chosen mechanism:** a short-lived, manager-controlled custody helper,

- mounted ONLY on the exact attempt directory -- no network, no credentials,
  no repository, no unrelated host path;
- running under the owning worker identity, or another narrowly mapped
  custodian identity;
- executing only TYPED MANAGER-OWNED custody operations, and never a
  worker-supplied command.

## Required correction boundary

1. Pin the custody operation vocabulary as closed, typed and manager-owned:
   inspect, read, hash, archive, normalize, recursively delete. No operand
   through which a worker or a caller names a command, a path outside the
   attempt directory, or a second mount.
2. Pin the custodian identity and its mapping, and state how it reaches
   worker-owned objects without acquiring authority over anything else.
3. Compose the helper into the ending W33936 leaves failing closed, so a
   populated worker-created directory becomes removable rather than reported.
4. Preserve every denial W33936 proved: input, launch, credential, repository,
   sibling-attempt and manager-owned paths stay unreachable, and the fixed
   worker identity `65532:65532` and the execution posture are unchanged.
5. Keep the helper SHORT-LIVED and prove it: nothing it creates outlives the
   custody act, and a crash between its start and its ending leaks no
   capability.

## Acceptance

- With a worker-created populated subdirectory at any mode the worker chose,
  the manager inspects, reads, hashes, archives, normalizes and recursively
  deletes the attempt's exact workspace and result directories.
- The helper mounts the exact attempt directory and nothing else; network,
  credentials, repository and unrelated host paths are absent rather than
  merely denied.
- No worker-supplied command reaches it, and the operation vocabulary is
  closed at the boundary that receives it.
- Retry, restart and a crash mid-custody leave no partial state a later act
  cannot describe, and no capability behind.
- Docker and compatible Podman both prove the applied identity and the
  custody result. A missing engine is a named deployment blocker rather than
  a pass.
- W33936's proved denials and its fixed runtime identity are unchanged.

## 2026-08-29 — the mechanism, built and measured

**The helper exists and removes the defect.** `custody.py` composes a
short-lived act with M36166's three constraints as properties of the argv: one
mount at a fixed target, the owning worker identity, and a closed six-verb
vocabulary with the program a constant of the module and no command operand at
all.

**The identity is the mechanism.** Running as the uid that owns the worker's
objects is what makes the custody unconditional — an owner may chmod its own
object at any mode, so no worker choice locks the custodian out. The manager
never acquires that ownership itself, and the helper only normalizes: the
containment rules and the "remove only what this component created" rule stay
on the manager's side, where they belong.

**Two corrections came from running it before wiring it.** The custodian must
touch only what it owns — the mount root is the manager's — and it needs
W33936's configured group to traverse the `02770` workspace at all.

**Still open:** the composition into the cleanup ending, and the
compatible-Podman proof, which this deployment cannot produce for the reason
W33936 already raised for a ruling.

## 2026-08-29 — independent review of the first implementation round

**Confirmed — the mounted boundary is broader than the ruled custody
boundary.** The real-daemon transcript itself shows the helper inspecting
`credential-state`, `credentials`, `custody` and `inputs` alongside
`workspace`. The caller passes `dirname(workspace)`, which is the whole
assignment home, and `custody_vector` accepts any raw absolute
`attempt_root`. Counting one mount does not prove that the one source is the
authorized workspace/result root. This violates the pinned absence rule and
also leaves a public operand capable of selecting an unrelated absolute host
path.

**Confirmed — hostile modes are only handled one barrier deep.** The helper
uses `os.walk(..., topdown=False)`, so it tries to descend before it changes a
mode-zero directory. The walk silently skips an inaccessible subtree, then
normalizes only the outer directory after returning to its parent. A nested
mode-zero directory and everything below it remain hidden. The existing
engine case has only one inaccessible directory; manager deletion succeeds
after that outer directory is changed and therefore does not exercise the
nested case.

**Confirmed — four claimed operations are placeholders.** `read`, `hash`,
`archive` and `discard` return exit 3 with `not composed by this build`.
`inspect` and `normalize` are the only implemented verbs. The six-name tuple
therefore describes intended vocabulary, not the accepted six-operation
capability yet.

**Confirmed — `--rm` does not prove crash custody.** Docker describes `--rm`
as removing the container when it exits. A foreground client disappearing
does not establish that the helper exits, and the implementation has no
bounded execution, durable/stable act identity, observation or restart
reclamation path. The present test asks the engine only after an ordinary
completed invocation. Crash/restart acceptance remains open.

**Confirmed — composition remains absent.** This is stated honestly in the
implementation progress. No ending invokes the helper, and retry/restart and
crash behavior therefore cannot yet be accepted.

## 2026-08-29 — second independent review findings

**Confirmed corrected:** an authentic workspace capability now mounts the
workspace rather than its assignment-home parent, the top-down traversal
reaches nested mode-zero directories, and all six verb branches execute
instead of four returning placeholders.

**Observed [P0]: the new custody capability can still launder an arbitrary
host path.** `attempt_custody_root` accepts an ordinary caller-owned mapping
and treats its `workspace` member as though it were
`assignment_workspace`'s authenticated answer. A forged mapping naming an
unrelated directory is minted successfully. The `result` arm is sharper: a
worker can leave `workspace/result` as a symlink; `isdir` follows it and
`_real` resolves it, minting the symlink target as the bind source. The
nominal `CustodyRoot` class therefore moves but does not close the original
caller-selected-path boundary.

**Observed [P1]: directory symlinks are omitted rather than held as
objects.** The top-down walk removes a directory symlink from `directories`
before yielding, so `inspect` reports no entry and `discard` leaves the link
behind. Not following a link is required; making the link object invisible is
not. The acceptance says every object under the exact root.

**Observed [P1]: `read` and `archive` do not yet provide the named
capabilities.** `read` returns only a lossy UTF-8-decoded 4096-byte head and a
digest; bytes after that head cannot be read back by the manager. `archive`
returns only a manifest of paths, sizes and hashes, with no content or content
locator, so no archived copy exists and nothing can be restored. All three
reading branches also load each entire file into the helper's bounded memory
before hashing, making a sufficiently large worker file terminate the act
rather than producing custody evidence.

**Confirmed still open:** crash-bounded/restart-reclaimable helper lifetime,
ending composition, retry/restart/crash regressions and compatible-Podman
proof remain undone.

## 2026-08-29 — third independent review findings

**Confirmed corrected:** directory symlinks remain visible to `inspect`, are
unlinked by `discard`, and are never traversed. A pre-existing symlink or
worker-owned entry at the proposed result root is refused.

**Observed [P0], still open:** expected directory names and ownership are not
provenance. The revised mint accepts any caller-created, manager-owned parent
containing siblings literally named `inputs` and `workspace`. That deliberate
forgery passes every check and yields a valid `CustodyRoot` for an unrelated
host directory. The correction rejects the first malformed example while
preserving the underlying path-selection capability.

**Confirmed still open:** complete read/archive output custody, streaming and
bounds, crash-bounded/restart-reclaimable lifetime, ending composition,
retry/restart/crash proof and compatible Podman remain required.

## 2026-08-29 — fourth independent review findings

**Confirmed corrected only for a plain mapping:** the structural-forgery case
now refuses an ordinary `dict`, because `attempt_custody_root` requires the
nominal `AllocatedRoots` answer from `assignment_workspace`.

**Observed [P0], still open: the minted answer is caller-retargetable.**
`AllocatedRoots` subclasses mutable `dict`. A caller can obtain an authentic
allocated answer, replace both its `inputs` and `workspace` members with an
unrelated manager-owned pair carrying the expected basenames, and pass the
nominal type plus every retained structural check. `attempt_custody_root` then
mints the unrelated workspace as a valid custody root. The new
`test_a_caller_cannot_retarget_authentic_allocated_roots` reproduces this and
fails because no `ContractRefusal` is raised. Nominal provenance cannot carry
authority while the authority-bearing paths remain caller-editable.

**Confirmed still open:** complete recoverable read/archive output custody,
streaming and bounds, bounded/derivable/restart-reclaimable lifetime, ending
composition, retry/restart/crash proof and the applicable engine-certification
boundary remain required.

## 2026-08-29 — fifth independent review findings

**Confirmed corrected only for ordinary dispatch:** direct item assignment,
deletion and the named `dict` mutator methods now refuse, and the authentic
answer stays unchanged through those calls.

**Observed [P0], still open: a `dict` subclass cannot close the mutation
boundary with overrides.** `AllocatedRoots` inherits `dict.__ior__`, so
in-place union mutates its members without reaching `_frozen`. A caller can
also invoke `dict.__setitem__` or `dict.update` explicitly on the subclass and
bypass the overrides. Using `dict.update` to replace both members with an
unrelated manager-owned `inputs`/`workspace` pair again makes
`attempt_custody_root` mint the unrelated workspace successfully. Three
additive regressions reproduce the protocol bypasses. Authority-bearing paths
must live behind an immutable wrapper/private representation rather than in a
mutable builtin base a holder can invoke directly.

**Confirmed still open, unchanged:** complete recoverable read/archive output
custody, streaming and bounds, bounded/derivable/restart-reclaimable lifetime,
ending composition, retry/restart/crash proof and the applicable engine
certification boundary remain required.

## 2026-08-29 — sixth independent review findings

**Confirmed corrected only at the builtin-inheritance layer:**
`AllocatedRoots` no longer inherits `dict`, so `dict.update`,
`dict.__setitem__` and inherited in-place union cannot mutate it.

**Observed [P0], still open: the new wrapper exposes its mutable backing
mapping.** Authority-bearing paths live in the ordinary dict
`roots._members`. A holder can update both members through that attribute and
then pass the authentic `AllocatedRoots` object; every nominal and structural
check succeeds and `attempt_custody_root` mints the unrelated workspace. The
additive
`test_the_private_member_mapping_cannot_retarget_allocated_roots` reproduces
this directly. Renaming a mutable mapping private does not make the mapping
immutable or move path selection back to the manager.

This is the sixth manifestation of one design error: path authority is still
carried in caller-held mutable process state and then re-read at the custody
mint. The correction must move the choice to manager-owned allocation state
or another representation whose authority-bearing values are not mutable by
the holder; another layer of ordinary method overrides is not sufficient.

**Confirmed still open, unchanged:** complete recoverable read/archive output
custody, streaming and bounds, bounded/derivable/restart-reclaimable lifetime,
ending composition, retry/restart/crash proof and the applicable engine
certification boundary remain required.

## 2026-08-29 — the sixth P0 corrected at its owner, not at its symptom

**The defect was one design error and the six rounds were six of its doors.**
Each round closed the door the previous review walked through, and every one of
them was a door onto the same room: the mount source was READ, at custody time,
out of an object the caller had been holding since allocation.

    roots["workspace"] = elsewhere            # round 1 -- a plain mapping
    dict.update(roots, {...})                 # round 4 -- explicit base call
    roots |= {...}                            # round 5 -- inherited __ior__
    roots._members.update({...})              # round 6 -- the private dict

The sixth is the one that proves overrides could never have finished the job:
`_members` is private by NAME and its value is an ordinary mutable dict, so a
holder edits it through ordinary attribute access with no method call to
override. In this language, a holder of an object can reach what the object
holds; an authority carried in caller-held process state and re-read later is
an authority the caller can change in between.

**The correction: `attempt_custody_root` takes no path-bearing operand at all.**
It now derives `<storage>/<assignment>/workspace` by exactly the rule
`assignment_workspace` allocates it by, from exactly the operands that function
allocates from — the deployment's configured `WorkspaceGroup` capability, the
storage root and the attempt identity:

    attempt_custody_root(workspace_group, storage, assignment_id, which)

There is nothing left to forge, retarget or launder, because nothing is read.
An `AllocatedRoots` object is not accepted, so mutating one — by any of the six
routes above or a seventh nobody has found yet — cannot influence the mount.

**What authority this therefore carries, stated exactly.** It carries the
ALLOCATION's, and not one bit more: any directory this can mount is one
`assignment_workspace` would have allocated for the same operands, and a caller
able to name those operands can already call that function. What is now
impossible — and was the finding — is selecting something that is NOT an attempt
workspace. The composed source is always the `workspace` entry of a home
directly under the storage root, so the assignment home, its `inputs`,
`credentials`, `credential-state` and `custody` siblings, the repository and
every unrelated host path are unreachable rather than refused: there is no
operand from which any of them could be built.

Two supporting corrections came with it. An attempt identity carrying a path
separator is refused — `boundaries.identity` is `boundaries.text` and owns
durable text, saying nothing about path syntax, so `../../etc` would otherwise
have composed a home outside the storage root before containment could see it.
And the resolved source is proved contained under the storage root directly,
which is the property the mount actually depends on.

**`AllocatedRoots` was hardened too, and that is explicitly not what the
guarantee rests on.** Its members now live behind a `MappingProxyType` over a
dict referenced nowhere else, which makes the review's complaint false at its
own site. It is recorded here that this is defence and not the mechanism:
`object.__setattr__` reaches any slot in this language and no representation
closes that. The guarantee is that the mint does not read the object.

## 2026-08-29 — the reading verbs: corrected in part, and one open ruling

**Corrected: the reading acts are streamed and their bounds are honest.**
`read`, `hash` and `archive` each did one `handle.read()` of a whole file, and
that was two defects in one line.

- A worker file larger than the helper's `--memory 512m` ENDED the custody act.
  A property a worker can switch off by writing a big file is not
  unconditional, which is the exact shape of thing this Work exists to rule
  out. Digests are now computed over 1 MiB chunks at constant memory.
- `read` answered `body[:4096].decode("utf-8", "replace")`, which is lossy
  twice: truncated without saying so, and every non-UTF-8 byte replaced with
  U+FFFD. What came back was neither the file nor a recoverable prefix of it.
  It now carries base64 bytes with an explicit `complete` member, and the WHOLE
  file is still measured and digested, so a partial carry is an evidence bound
  rather than a blind spot.

The streaming case is proved under a real `RLIMIT_AS` bound smaller than the
fixture, and a companion case drives the superseded whole-file read under the
same bound and requires it to FAIL. Without that companion the streaming case
would pass against a slurping implementation on any host with enough RAM —
which is how the defect survived the first five rounds.

**Open, and it is a ruling rather than an omission: what `archive` must
return.** The review requires `archive` to preserve recoverable content rather
than a digest manifest. That is in tension with M36166's own single-mount
constraint, and the tension is structural rather than an implementation gap:

- the ONE mount is the custody subject itself, so writing an archive into it
  would change the tree being described;
- the only other channel is the helper's stdout, a bounded JSON document on a
  pipe, which cannot carry an arbitrary worker tree;
- a second, manager-owned mount to receive the archive is the obvious answer
  and is exactly what "mounted ONLY on the exact attempt directory" forbids.

**A proposal, offered as decision support and not taken here.** After
`normalize`, every object under the attempt root is group-accessible to the
manager, which then reads, hashes and archives on the host with its own
streaming and its own containment rules. On that reading `normalize` is the
ENABLING act and `read`/`hash`/`archive` inside the helper are duplicating
manager-side work in the one place that has no good way to return bytes. That
would narrow the confirmed six-verb decision to the verbs custody actually
needs the helper's identity for — which the first review named as an
alternative to implementing all six ("implement all six pinned operations **or
narrow the confirmed decision**"), and which only the approver can do, because
M36166 names six.

Until that is ruled, `archive` declares `content: "manifest-only"` in its own
answer, so it can no longer LOOK like content custody while being a manifest.
