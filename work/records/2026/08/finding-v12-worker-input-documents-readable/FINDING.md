# Make delivered worker input documents readable

## Discovery

Discovered by W6's digest-bound real-Docker capability pass. This is a
top-level record because W6 already occupies the permitted second child level.

Ledger Work: `W33935`.

## Confirmed defect

Inside the composed execution container the worker runs as uid/gid 65532, but
`/input/assignment.json` and `/input/input.json` are owned by uid/gid 1000 with
mode `0400`. Both reads fail with `EACCES`; the reference worker therefore
cannot consume either required document. The sibling launch document is mode
`0444` and is readable, demonstrating the required delivery shape.

Evidence is retained under W6 at
`work/records/2026/08/finding-v12-isolated-agent-workers/findings/finding-v12-local-isolated-execution/findings/finding-v12-local-conformance-proof/evidence/w6-seal/input-pair.json`.

## Acceptance

- Both input documents remain immutable/read-only to the runtime and are
  readable by the fixed worker identity.
- Ownership/mode changes do not make the input directory or documents
  writable, replaceable, or traversable through sibling paths.
- Real-container positive and write-denial regressions cover both documents,
  restart/retry reuse, and sibling isolation.

## 2026-08-28 — corrected

**Confirmed on the current tree before acting.** The probe reproduced both
`EACCES` reads inside a real composed runtime, and added two facts the finding
did not have: the `/input` root is `0o775` and IS listable and traversable, so
the defect is at the files alone; and the root refuses a write with `EROFS`
from the read-only bind rather than from any mode, which is what keeps a
world-readable document safe.

**Corrected, and the constant was only half of it.** `READ_ONLY_FILE` is
`0o444` and `READ_ONLY_DIR` is `0o555`, matching the launch delivery. The other
half is that `_write_read_only` passed the mode to `os.open`, where the process
umask filters it — so the corrected constant would still have authored `0400`
under the ordinary service umask 077, silently and only on some hosts. W26291
review [P0] found and fixed this exact shape at the launch document and wrote
the reason out; the same line here was never revisited. The mode is now
established with `fchmod` on the descriptor after the last byte.

**Acceptance, clause by clause.** Both documents are read by uid 65532 inside
the runtime the manager composed and compared against the manager's exact
bytes; neither they nor the root became writable, asked of the engine's applied
bind AND of the container; and the real-container regressions cover both
documents, restart reuse through a second manager incarnation, and sibling
isolation. Measured by removal, 6 of 6.

**Not this Work's, and still present.** `/workspace` is `0o775` owned by the
manager's uid and the container at 65532 cannot write it, so a worker cannot
write the outputs it declares. Re-measured in the same probe; it needs an
owner.

## 2026-08-28 — the root, frozen

**Confirmed [P0].** `READ_ONLY_DIR` was changed and never applied:
`compose_input_root` returned with the root at `0775`, so unlink and rename —
permissions of the directory, not of the file — left both `0444` documents
replaceable by the manager's own uid underneath a worker that had already
mounted them. My own retained probe recorded the `0775` root and I did not
follow it up, and the mutation I claimed for it changed a constant production
code never read.

**Corrected.** The exact root mode is established after both documents are
durably installed, `0555` so the container's fixed uid can still traverse it.
Five host-side cases prove create, unlink, rename, replace and replace-in-place
are denied, that nothing moved, that cleanup can still remove a frozen root and
thaws nothing beside it, and that the mode is exact under every umask. They
refuse to run as root, because root is not denied by ordinary permissions.

## 2026-08-28 — independent re-review: the root entry remains replaceable

**Observed [P0]:** `compose_input_root` freezes the directory's contents at
`0555`, but the directory itself is an entry in its assignment-home parent,
which remains `0775`. Rename and replacement of a directory entry are governed
by the parent. The manager's ordinary uid can therefore rename the completed
input root wholesale, create a new writable root at the same canonical path and
write replacement bytes there. The old frozen root remains `0555`; its mode
does not protect its former name.

The public host reproduction is retained at
`evidence/w33935-root-entry-replacement-repro.py`. It observes the displaced
root at `0555`, the replacement root at `0775`, and attacker-controlled bytes
at the canonical input path. The seven submitted daemon-free cases remain
green because they mutate entries *inside* the root and never mutate the root
entry through its parent.

**Confirmed boundary:** the acceptance names both the input directory and its
documents as non-replaceable. Freezing only the input directory closes document
unlink/rename but not input-root rename/replacement. Custody must also remove
write authority at the exact parent boundary after every required sibling root
has been provisioned, while cleanup deliberately thaws only the owned
assignment home. Add behavioral root rename/replacement denial, cleanup and
sibling-isolation cases; a constant or root-content assertion is insufficient.

## 2026-08-28 — the parent boundary

**Confirmed [P0], reproduced before changing anything.** `0555` on `inputs`
protects what is inside it; the root's own ENTRY is governed by the assignment
home, which was left writable — so the frozen root could be renamed aside and a
writable one put at the same canonical path.

**Corrected at the only place that can protect an entry: its parent.**
`assignment_workspace` provisions every entry the home will ever hold — the two
mountable roots plus the adapter's custody tree and the credential home's two
places — and still answers with only the two roots, so no mount contract
changes. `compose_input_root` freezes the home after the pair is installed.
`HOME_ENTRIES` is held to `oci.py` and `credentials.py` by a case, because it
is a claim about them.

**One production interaction the suite caught:** freezing the home broke
cleanup, because `_remove` thawed a directory only inside its file loop and a
directory of directories never reached it. Both removals are writes to the same
directory, so the thaw is now once per walk step.

## 2026-08-28 — independent second re-review: the home entry remains replaceable

**Observed [P0]:** the correction moved the same authority gap one directory
up. `compose_input_root` now freezes the assignment home at `0555`, which
correctly prevents replacement of the `inputs` entry *inside* that home. The
home itself is still an entry in the manager's writable workspace-storage
directory, however. The manager's ordinary uid can rename the whole frozen
home, recreate a writable home and input root at the original canonical path,
and install different `input.json` bytes there.

The public host reproduction is retained at
`evidence/w33935-assignment-home-replacement-repro.py`. It observes the
displaced home at `0555`, the replacement home at `0775`, and
attacker-controlled bytes at the original canonical input path. The earlier
root-entry reproduction now correctly stops with `PermissionError`, and all
12 submitted daemon-free delivery/layout cases pass; those facts confirm that
the child boundary was fixed but do not protect the home entry.

**Confirmed boundary:** another mode on the child cannot close this. Rename of
the assignment home is governed by workspace storage, and that directory must
remain writable in the current same-uid/path-based design to allocate later
assignment homes. The correction therefore needs either a stable custody
authority outside that writable-name model (for example an independently
owned/brokered anchor or identity-preserving descriptor/mount contract), or an
explicit approver ruling that narrows the non-replaceability acceptance to the
input entry inside an assignment home already trusted by identity. Repeating
the same `chmod(parent, 0555)` one level higher without resolving allocation
and races is not a complete boundary.

## 2026-08-28 — the regress is about names, and the measurement says so

**Confirmed [P0] by reproduction**, and confirmed that the obvious continuation
is wrong: freezing workspace storage would reopen every existing home each time
a new one is allocated. Under one unprivileged uid there is no name-based end
to the regress — any path the manager can create, it can replace.

**Measured, against a real daemon.** A RUNNING container's bind survives the
substitution entirely: the container reads the original bytes while the host
reads the replacement, because the kernel resolved the bind to the inode at
mount time. The exposure window is therefore only between composition and
start. And the inode changes on replacement, so pinning `(st_dev, st_ino)` at
composition and re-proving it before start detects the substitution without any
privilege this manager lacks.

**Therefore the acceptance's "non-replaceable" is achievable as a detected
refusal rather than as an impossibility**, and that is an acceptance-boundary
decision. Raised for an approver ruling with the measurement attached.

## 2026-08-28 — approver ruling M34768: the trust model, and the acceptance narrowed

**Confirmed by approver response M34768:** the Worker Manager, its host uid,
its private state root and the Docker daemon are TRUSTED. This capability pass
is not to be defended against a malicious same-uid host process, and no
brokered, signed, inode-security or schema-expanded input protocol is to be
built. Non-replaceability narrows to the untrusted worker/container and to
accidental manager corruption.

**Superseded:** the inode-pinning proposal raised at M34475 is not authorized.
Its measurement stands as decision history — a running container's bind
survives host replacement, and the inode changes — but the ruling makes the
first fact the reason the defence is unnecessary rather than the basis for a
new mechanism.

**The six properties this Work now carries:** unique never-reused per-attempt
directories; exclusive creation with collision refusal; complete input
composition before publication; no mutation after publication; read-only worker
mounts; and exact-attempt cleanup with retry and sibling isolation. The landed
readable/read-only input and cleanup corrections are preserved.

## 2026-08-28 — independent third re-review: allocation is not exclusive

**Observed [P0]:** the ruled trust model is recorded correctly, but the
submitted allocator implements its exclusive-creation property as the
opposite. `assignment_workspace` calls `os.makedirs(..., exist_ok=True)` for
every home entry and then accepts the resolved path whenever it remains
somewhere under workspace storage. It neither creates the attempt home
exclusively nor proves that an existing home belongs to this attempt.

A retained reviewer regression constructs a stale second attempt home whose
`inputs` entry is a symlink to the first attempt's still-contained input root.
`assignment_workspace` accepts it and returns the first attempt's root for the
second attempt. The focused output is `accepted ... aliases True`; the additive
case `TheRuledTrustModel.test_a_colliding_home_cannot_alias_another_attempts_root`
fails because no refusal is raised.

This is inside the narrowed ruling: it does not posit a malicious same-uid host
process. It asks the manager to refuse an accidentally stale or corrupt name
instead of adopting it. The existing clean-allocation comparison cannot expose
the alias, and the case named "a second attempt cannot publish" actually
recomposes the same attempt into the same already-published root. Publication's
document-exists check therefore does not supply exclusive directory creation
or per-attempt root isolation.

**Required boundary:** distinguish exclusive first allocation from an
authorized restart lookup. A pre-existing or aliased attempt/root name must
fail closed unless durable manager-owned state proves it is the exact existing
attempt being reopened; a generic `exist_ok=True` path is not that proof.
Preserve same-attempt adoption, distinct-attempt concurrency, exact cleanup and
the landed readable/read-only delivery behavior.

## 2026-08-28 — exclusive allocation, separated from restart lookup

**Confirmed [P0]:** `assignment_workspace` adopted any existing entry that
passed containment, so a stale home whose `inputs` was a symlink to another
attempt's root returned that root for a second attempt. Containment proves the
path lands in manager storage; it does not prove the root is this attempt's.

**Corrected structurally, with no new durable record.** An existing entry must
be a real directory — not a link — resolving to exactly its path under this
attempt's home; anything else fails closed. An absent entry is created, which
is the first allocation. Reopening an attempt still answers, because its
entries are real directories at their own paths.

**Superseded:** the previous round's conclusion that exclusive allocation and
restart lookup could not be separated. They can; the separation is structural
rather than a publication check, which proved only recomposition refusal.

## 2026-08-28 — independent fourth re-review: the home anchor still aliases

**Observed [P0]:** the entry-level correction refuses an `inputs` symlink and
the retained regression now passes, but the attempt home itself is not held to
the same rule. `os.path.isdir(home)` follows a home symlink, and each child is
then compared with a path anchored at `os.path.realpath(home)`. For a home
symlink to a sibling attempt, that comparison proves only that the sibling's
children are beneath the sibling; it does not prove the requested attempt owns
its home.

The additive reviewer case
`TheRuledTrustModel.test_a_colliding_home_cannot_alias_another_attempts_home`
symlinks the second attempt's whole home to the first. The allocator accepts it
and returns the first attempt's roots for the second. The focused set runs 83
daemon-free cases: 82 pass and this expected-refusal case fails.

**Required boundary:** apply the structural exact-path/no-link proof to the
attempt home before using it as the anchor for its entries. Preserve the valid
entry checks, restart reopening of a real home at its own path, distinct-attempt
concurrency, exact cleanup and the landed delivery behavior.

## 2026-08-28 — the anchor is proved too

**Confirmed [P0]:** the structural proof reached the home's children but the
home itself was checked with `os.path.isdir`, which follows symlinks. An
aliased home therefore passed and then anchored the child proofs on the wrong
sibling, where both sides of each comparison compared equal.

**Corrected:** the home is proved before it anchors anything — not a link, a
real directory, resolving to exactly its own path under storage — and the
children are compared against that proved path. A proof applied to the children
and not to what they are measured against is not applied.

## 2026-08-28 — independent fifth re-review: allocation race leaks an OS fault

**Observed [P1]:** the exact-home and child alias cases now pass, but exclusive
allocation remains a check-then-create race. Two callers can both observe an
absent attempt home; one `os.makedirs(home)` succeeds and the other raises raw
`FileExistsError`. The same shape exists for each absent child entry. Isolation
fails closed, but the ruled "collision refusal" is not delivered through the
manager's `ContractRefusal` boundary, so an ordinary allocation collision is an
unexpected manager fault instead of a retryable/typed answer.

The deterministic reviewer regression
`TheRuledTrustModel.test_first_allocation_race_answers_or_refuses_in_contract`
holds both callers after the same absence observation. It consistently records
one valid root answer and one leaked `FileExistsError`. The focused set runs 85
daemon-free cases: 84 pass and this race case fails.

**Required boundary:** make create-or-collision one owned-directory operation
at both the home and child levels. A lost creation race may reopen and prove the
exact directory or issue a typed collision refusal, but it must not leak a raw
filesystem exception. Preserve sequential restart reopening and every alias
refusal.

## 2026-08-28 — allocation is one owned operation

**Confirmed [P1]:** the structural proof was a test and then a create, so two
callers could both observe absence and one received a raw `FileExistsError`.

**Corrected:** `_own_directory` attempts the create and treats the collision as
its branch — the loser falls through to the same proof a pre-existing directory
gets and reopens it when it is this attempt's own. One operation at the home
and at every child, with any other `OSError` becoming a refusal.

**Noted:** the reviewer's race case synchronises on a call the correction
removed, so it no longer races. It is retained as a weaker true property and
three cases added that hold both callers at the create itself, including the
child-entry race the review names.

## 2026-08-28 — independent sixth re-review: signed off

**Confirmed:** `_own_directory` makes creation and collision one operation at
both the attempt-home and child-entry levels. A creation loser proves and
reopens the exact no-link directory; other creation failures become
`ContractRefusal`. The actual `os.mkdir` races for the home and `inputs` child,
plus the loser-reopen outcome, pass independently.

All retained structural aliases, sequential restart reopening, exact cleanup,
sibling isolation, umask-independent `0444` documents and frozen roots pass in
the 88-case daemon-free focused gate. Together with the implementer's retained
real-Docker read/EROFS evidence and 152-case engine gate, the narrowed approver
acceptance is satisfied. Docker access remains an independent-review
limitation, not an independently claimed pass.
