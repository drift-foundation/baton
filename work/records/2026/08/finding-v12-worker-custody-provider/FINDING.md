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
