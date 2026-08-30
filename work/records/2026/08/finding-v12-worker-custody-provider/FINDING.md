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

## 2026-08-29 — seventh independent review findings

**Confirmed corrected:** custody no longer reads a path from
`AllocatedRoots`; the prior private-mapping retarget is closed. Streaming hash
and bounded base64 read evidence also replace the whole-file/lossy-head path.

**Observed [P0]: the raw host-path selector moved to `storage`.**
`attempt_custody_root(workspace_group, storage, assignment_id, which)` derives
below `storage`, but `storage` is ordinary caller-owned text/path authority.
A caller can create `<unrelated>/attempt-1/workspace`, pass `<unrelated>` as
storage and receive a valid `CustodyRoot` for that unrelated host tree. The
existing structural-forgery case creates `inputs` and `workspace` directly
under its supplied storage, so the extra `attempt-1` component makes that test
refuse without exercising the actual derived layout. Derivation under a raw
caller root is still caller path selection. The storage root must come from
manager-owned durable/configured authority, not an ordinary path operand.

**Observed [P1]: result creation precedes parent no-link validation.** For a
missing result, the mint calls `os.makedirs(place)` before it `_no_link`s the
attempt home and workspace. If the attempt home is a symlink to an unrelated
manager-owned tree, the call creates `workspace/result` through the link and
only then refuses the parent. A refused capability mint must not mutate the
very unrelated tree it rejects; validate every existing component first and
create only beneath the validated real workspace.

**Confirmed still open:** the archive ruling, bounded/restart-reclaimable
lifetime, ending composition, retry/restart/crash proof, boundary inventory
and compatible engine certification remain unchanged.

## 2026-08-29 — the seventh P0 corrected: neither operand is a path any more

**Round seven found the remainder round six honestly recorded.** The sixth
correction stopped reading a caller-held object and DERIVED
`<storage>/<assignment>/workspace` instead, and its own finding stated the
limitation in as many words: "it carries the ALLOCATION's authority and not one
bit more". The review ruled that this is not sufficient, and it is right —
`storage` was still an ordinary caller operand, so two `mkdir`s producing a
directory that holds `attempt-1/workspace` yielded a valid capability over an
unrelated host tree. **Deriving from a caller's root is still caller path
selection; it just looks one component deeper.**

**The correction: the workspace STORE becomes a deployment record, exactly as
its group already is.** `WorkspaceStorage` is minted only by
`configured_workspace_storage(store)`, which cross-checks the committed
`workspace-storage.configure` operation against its `meta` projection and fails
closed in every direction of disagreement — the same four properties W33936
established for the group, including that a row of another kind at the derived
identity is not a configuration and that a `result` edited in place no longer
agrees with its recorded signature. Reconfiguring to a different store is
refused for the group's reason applied to paths: every attempt already
allocated under the first store would become unfindable.

`attempt_custody_root(workspace_group, workspace_storage, assignment_id,
which)` therefore takes **two capabilities and a name**, and no path at all.
There is no operand left through which an unrelated directory could be
selected.

**Why the ALLOCATION boundary deliberately still takes a path**, stated so the
asymmetry is a decision rather than an oversight. `assignment_workspace` is the
deployment's own allocation act and the review's requirement is about the
custody MOUNT. A caller may still allocate a workspace wherever it can already
write; what it can no longer do is have a container mounted on one. Custody is
confined to the configured store, and allocating elsewhere grants no custody
there.

## 2026-08-29 — the result root no longer mutates through an unvalidated parent

**Confirmed [P1] and corrected.** For `which="result"` the mint called
`os.makedirs(place)` BEFORE proving the attempt home and workspace, so a home
entry that was a symlink to another manager-owned directory had
`workspace/result` created inside the TARGET — and only then did the parent
proof raise. A refusal that has already written through the alias has not
preserved the boundary it refused for.

Every existing parent is now proved first, and the result path is then derived
from the RESOLVED real workspace rather than from the composed one — so the
creation cannot traverse a link even if one appeared at the home between the
proof and the write, because the path being created no longer contains the
component that was proved.

The review's own regression is kept probative rather than merely passing: it is
driven through the real store capability, because passing a raw path would now
refuse at the type check BEFORE the ordering under test is reached. Driving the
superseded ordering under the corrected code reproduces the failure
(`the refused mint created through its parent link`) and the fix clears it.

## 2026-08-29 — the ninth P0: the interval itself is removed

**Nine rounds, one defect, and this is the shape of it stated plainly.** Every
correction until now defended an object that a caller HELD between the
authenticated lookup and the use:

| round | what was held and re-read |
|---|---|
| 1–2 | a plain mapping, then one with the expected basenames |
| 3–4 | the nominal `AllocatedRoots` answer |
| 5 | that type with its `dict` mutators overridden |
| 6 | that type with `dict` removed from its bases |
| 7 | no object — but `storage`, an ordinary caller path |
| 8 | `WorkspaceStorage`, minted from durable state |
| 9 | …and `CustodyRoot`, minted from a valid derivation |

Round eight mirrored `WorkspaceGroup` and the review is right that this
"copies durable authority back into the forbidden process-state interval":
`object.__setattr__` replaces a slotted member, so a capability read from the
journal and then handed to a caller is a path that caller can still change
before anybody reads it. The same was true of the minted `CustodyRoot`, whose
`.place` `custody_vector` read straight into `--mount source=`.

**THE CORRECTION IS TO DELETE THE INTERVAL, NOT TO DEFEND IT.**
`custody_vector(engine, *, image_digest, name, store, assignment_id,
operation, which)` now reads the deployment's configured store and group out
of the durable record, derives and proves the attempt's root, and composes the
argv — **in one act, handing no path-bearing object to anybody**. There is
nothing to retarget because nothing is held; there is no later re-read because
there is no earlier hand-off.

`CustodyRoot` and the public `attempt_custody_root` are **gone from the
surface** rather than hardened a tenth time. What crosses is this manager's own
store handle and the attempt's NAME. `WorkspaceStorage` survives as the read's
own return value inside that one frame; a holder can still retarget one, and
that no longer reaches anything, which is the point.

This is the rule the dossier had already written down at round six —
"`object.__setattr__` reaches any slot in this language and no representation
closes that; the guarantee must be that the mint does not read the object" —
finally applied to every hop instead of one.

## 2026-08-29 — the literal boundary label that stopped the shared inventory

Round eight's `check_workspace_storage` passed its keyword parameter `what` to
`boundaries.text` instead of a literal. The boundary inventory attributes a
crossing by the label written at the site, so a variable is a crossing it
cannot key — and it RAISES rather than guessing, which stopped the whole
package's scan from producing any verdict at all and blocked every other
checkpoint's inventory acceptance item, not only this one.

`check_workspace_group`, the function that round mirrored, calls no boundary
helper at all, so the pattern did not carry the constraint with it. The label
is a literal now and `what` stays the caller's context word in the refusal
prose, where it reads correctly and decides nothing.

## 2026-08-29 — the tenth P0: the last interval was the RETURN VALUE

Round nine deleted the interval around every *operand* and left one where
nobody had looked: the answer. `custody_vector` authenticated the bind source,
composed it into `--mount source=` and **returned the list**. Every production
ending would then have executed that list separately, so the authenticated
host path sat in an ordinary mutable object in somebody else's hands between
the durable lookup and the engine use — the same defect as rounds one to nine,
one layer further out.

The review is also right that no wrapper closes it. A tuple, a frozen argv
type, a read-only sequence: all of them still hand back the PATH, and a caller
holding a path can compose its own vector. Hardening the container was the
mistake the previous nine rounds already made.

**Decision (pinned): custody is ONE OWNED ACT that performs itself.**
`custody_act(engine, run, *, image_digest, name, store, assignment_id,
operation, which)` reads the durable record, derives and proves the root,
composes the argv, RUNS it through the engine port and answers. There is no
return value a caller can execute, because the execution already happened
inside the act.

`custody_vector` is private (`_custody_vector`) and reachable only by the act
that runs it. **Superseded:** every earlier statement in this record that
names `custody_vector` as the composition's public surface, including round
nine's paragraph above — the composition is unchanged and its name and
visibility are not.

### Why `run` is an operand and not a leak

The engine port is the boundary of the process, not a party inside it. It is
the same `oci.EnginePort` every other vector this manager composes goes
through, and handing it the argv is the INVOCATION rather than a handoff:
there is no interval after it, because there is nothing after it. Routing
custody through the port also puts the act under the §13 durable-secret sweep
that port already owns, which composing-and-returning never had.

### What a holder keeps afterwards

`CustodyAnswer` — the verb, the engine's exit status, the custodian's own
document as a read-only mapping, and a bounded diagnostic. It carries **no
host path**: the program answers paths relative to its own mount, which is the
only namespace it knows. It carries no command vector. It is immutable,
because an answer somebody can edit is an account that disagrees with what
happened.

`ok` requires BOTH a zero exit and a readable document. A zero exit with no
answer is an act this manager cannot account for, and custody that cannot be
accounted for is not custody. The JSON extraction that used to live in each
engine case is the act's own now, so there is one reader rather than one per
caller.

## 2026-08-29 — the `--rm` claim the code made and the record denied

`custody_vector`'s docstring said `--rm` plus foreground meant "a crash between
start and ending leaks no capability a later manager would have to find and
reclaim". **That is false and this record already said so** at the first
review, and `PLAN.md` has carried bounded/derivable/restart-reclaimable helper
lifetime as NOT DONE since.

**Superseded:** that sentence. What `--rm` buys is reclamation on the engine's
normal removal path — the container goes when the act ends. A manager or
client that dies mid-act leaves a helper the engine never reclaims and this
build never looks for. `CUSTODY_NAME` exists so a restarted manager could find
one and nothing reads it yet.

Two live rules that contradict each other are worse than either alone, and one
of them being in a docstring rather than in the record does not make it less
authoritative to the next reader — the docstring is what an implementer reads.

### The answer has no public constructor either

The first cut of `CustodyAnswer` took an ordinary `__init__`, which the shared
boundary inventory correctly saw as four more caller entries with no owning
validator. Removing it is not a way around that gate: an answer is what one
act REPORTED, so a caller that can mint one can report an act that never
happened. `_answered` is private and is called in exactly one place — at the
end of the act it describes — which is the same rule this package already
applies to `WorkspaceGroup`, `WorkspaceStorage` and every other capability it
refuses to let a caller compose.

## 2026-08-30 — eleventh round, after `review-2026-08-30T04-07-53Z.md`

### Pinned: an answer is accounted for by ITS OWN VERB'S DOCUMENT, or not at all

**Superseded:** the tenth round's rule that `ok` is a zero exit plus a readable
document. It was the right correction to the previous shape and it was not
enough. The act validated the verb it SENT and nothing about what came back, so
a `normalize` act whose stdout ended `{"custody": "inspect", "entries": []}`
was reported as successful custody. Zero plus an unrelated document is no
stronger an account than zero plus no document, which this module already
refuses — and the manager was recording that it had normalized a tree when
nothing had.

**The rule now:** `_CUSTODY_RESULT` writes down, per verb, the closed member
set and the type of each member that `CUSTODY_PROGRAM` actually prints, and
`_accountable` holds the returned document to the requested verb's entry before
anything can be `ok`. A member set alone would not have been enough either:
`entries` is a COUNT for `normalize` and a LIST for `inspect`, so the shape is
part of the identity of the answer rather than a detail of it.

`running_as` is held to two integers for the same reason it is printed: an act
whose custodian identity is unstated is one this manager cannot attribute, and
attribution is the whole mechanism this Work rests on.

### Pinned: TWO documents are accountable, and only one of them can be `ok`

`CUSTODY_PROGRAM` can print exactly two things — the requested verb's result,
or its own typed refusal `{"custody": "refused", "why": ...}` with a non-zero
exit. Both are real accounts of what happened, so both are RETAINED; only the
first can make `ok` true. Discarding the refusal as "a document for the wrong
verb" would have thrown away the one sentence explaining why the act did not
run.

### Pinned: a document that is not accountable is not partially believed

None of a mismatched or malformed document becomes `answer`. What a reader gets
instead is `unaccounted` — **this module's own words** about what it could not
account for — while the act's own stderr stays separately in `diagnostic`, so
the two provenances never blur. Reading the recognised members out of a
document from a program that is not the one this module ships is how a manager
ends up accounting for an act it did not understand.

### Pinned: the retained account is frozen ALL THE WAY DOWN, and it is a tuple

**Superseded:** the tenth round's `MappingProxyType` over the parsed document.
A proxy protects assignment to the mapping it wraps and nothing inside it, so
every list and record the custodian nested stayed live: `answer["running_as"][0]
= 0` succeeded, and the retained account disagreed with what the custodian
reported.

**The rule now:** `_frozen` rebuilds the document bottom-up — dictionaries as
`MappingProxyType` over fresh mappings nothing else references, lists as
tuples, scalars as themselves.

**A LIST BECOMES A TUPLE RATHER THAN A GUARDED LIST, and that is this record's
own rule applied to itself.** A `list` subclass refusing its mutators would
have compared equal to a list, serialized as one, and left every existing
assertion untouched — and `list.append(frozen, x)` reaches straight past it,
exactly as `object.__setattr__` reached past six representations of
`AllocatedRoots` in rounds one to six. Choosing the convenient defence here,
in the round that answers a finding about a defence that only looked
sufficient, would have been this Work's characteristic mistake for the seventh
time. The cost is real and is accepted: a frozen sequence no longer equals the
list it came from, and three assertions across two suites changed to say so.

### Pinned: the answer renders itself once

A read-only view cannot be handed to `json.dumps` — a `mappingproxy` is not a
`dict` — and callers were rebuilding one to serialize it, which is re-deriving
the account instead of quoting it. `rendered` is the canonical serialization
produced from the accepted document at mint time and never recomputed.

### The two tables are compared, because two copies of one contract are two contracts

`_CUSTODY_RESULT` is a second copy of what `CUSTODY_PROGRAM` prints.
`TheAnswerContractMatchesTheProgram` runs the REAL program for all six verbs
over a populated tree and requires this module's own validator to accept every
document it printed. Adding a member to the program without adding it to the
table fails as `unexpected`; removing one fails as `missing`. Without that
case, holding the daemon-free fixture to the module's table would have proved
only that the fixture agrees with the validator.

### Closed, and it was this Work's own: the uncovered durable writer

`test_secrets`' §13 sweep reported `workspaces.py:configure_workspace_storage`
as a durable writer with no coverage — a shared gate this Work has been leaving
red since round eight, when the act was written in the shape of
`configure_workspace_group` directly above it and the registration was not
carried along. **The same omission as round nine's boundary label, and the same
lesson: a mirrored pattern does not bring its obligations with it.** The
declaration is the group's own rationale one operand over, and it is true
rather than convenient: the only value written is a path
`check_workspace_storage` has already proved, and it rides
`manager_signature("workspace-storage.configure", {"place": place})` into the
journal the sweep walks.

This is NOT the deferred custody boundary-inventory ownership item, which is a
different gate over `custody.py`'s own entries and stays open.

### Open, unchanged

Archive-content semantics, bounded/restart-reclaimable helper lifetime,
ended-attempt composition with retry/restart/crash proof, compatible-engine
certification, and custody boundary-inventory ownership. The review directs the
decomposition of these into explicit Jobs after this correction returns; they
are named in `PLAN.md` and deliberately not started here.

## 2026-08-30 — compatible-engine certification boundary (W43976)

**Confirmed:** "every compatible OCI engine" means every engine the
deployment explicitly claims as supported, not every OCI implementation that
exists or can be installed. Docker is the current reference and certified
custody engine. Its real-engine custody matrix must exercise the same closed
six-verb contract and manager/custodian identities as the daemon-free suite.

Podman is not currently certified. The available rootless environment cannot
establish the configured supplementary-group workspace precondition, while a
rootful nested environment makes the manager root and cannot prove the
required before-custody denial. Neither a Docker alias nor that non-probative
rootful result is accepted as Podman parity.

**Scheduling ruling:** Podman remains the longer-term, separately parked
certification target owned by W32391. Its absence is an honest unsupported
engine limitation, not an environmental gate on W36540 or the current Docker
custody path. If Podman support is later claimed, W32391 must produce the real
compatible-engine evidence before that claim becomes true.

## 2026-08-30 — archive and attempt-result boundary (W43972)

**Supersession:** M36166's requirement that the current custody helper provide
an `archive` operation, and the matching archive acceptance bullets above, do
not gate the v12 MVP. There is no demonstrated need yet for a transported,
compressed, or separately restorable copy of the entire attempt tree. Keep the
historical ruling as the reason W43972 existed, but do not implement archive
semantics speculatively. A later retention/export Work may reintroduce an
archive artifact after an operational need defines its content and lifetime.

The manager instead owns one persistent attempt-result envelope with this
logical shape:

```text
result/
  output/                 worker-produced candidate data
    repo/                 working clone and commits for Git assignments
    result.json           worker publication, written last
  logs/                   manager-captured attempt and agent logs
```

`result/output/` is worker-writable and remains untrusted until validation. A
Git worker may clone and work directly in `result/output/repo/`; no final move
or duplicate copy is required. A failed attempt may leave `output/` absent or
incomplete.

`result/logs/` is manager-owned. The worker emits available session events,
messages, tool activity, stdout/stderr and runtime diagnostics through its
mediated interfaces; the manager records them so the worker cannot rewrite
its history. Logs are retained for every attempt, successful or failed, and
are correlated to the exact attempt. They contain only information the agent
or runtime exposes, never an invented claim to hidden model reasoning, and
credential material must be excluded or redacted.

The primary consumer is candidate review. A reviewer receives
`result/output/` together with the exact attempt's `result/logs/` and can
inspect the messages, tool activity, provider-exposed thought chunks or
reasoning summaries, tests and runtime diagnostics that led to the candidate.
ACP and App Server adapters therefore preserve those structured events when
their provider emits them, with attempt/session/turn correlation, rather than
relying only on one shared process log. This evidence explains how the code
was produced; it is not proof that the reasoning or candidate is correct, and
it never substitutes for diff inspection, verification or independent
review.

This result envelope is not a custody archive. Read-only assignment input,
credentials, run secrets, container-private temporary space, the base image
and unrelated mounts remain outside it. Custody still must let the manager
normalize and dispose of ended-attempt writable trees regardless of modes;
deferring archive transport does not weaken that ownership invariant.
