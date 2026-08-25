# Implementer progress — exact sources and private workspaces

Created 2026-08-24 by `baton.claude` on claiming W6631, as the record requires.

## Delivered

`v12/python/src/baton_v12/worker_manager/workspaces.py`, with
`tests/manager/test_workspaces.py` — **36 methods, all passing**.

**The manifest is measured, never trusted.** `directory_manifest` walks a tree
and produces the frozen `contentManifest` — and the exported §12 rule accepts
what it produces, which is the same check every consumer applies. Entries are
sorted **bytewise**, because a manifest that recomputes differently under
another collation is one two conforming readers disagree about.

**Nothing but regular files.** Symbolic links refuse wherever they sit; a
**hard link** refuses too, asked of the descriptor rather than the directory
entry, since `st_nlink` is a property of the inode and there is nothing in a
listing that distinguishes a second name for one inode from a file. Special
files refuse. The root is canonicalized before it is walked, because lexical
containment is not containment.

**The open file is the measured file.** Each entry is opened once with
`O_NOFOLLOW`, and its kind, link count, size and bytes all come from that one
descriptor. A file swapped afterwards is a file this component never held.

**Nothing partial is published.** Delivery builds under a staging name this
component owns and publishes by one rename; every refusal removes it. Each
refusal case asserts the inputs root is empty afterwards.

**The race the component reads every file twice for.** The copy re-reads the
origin and compares against the digest measured a moment earlier, so a file
replaced *between* the measurement and the copy is caught rather than delivered
under the digest of the version that is gone.

**Private, non-overlapping roots.** `inputs`, `workspace` and `git` are
siblings, never nested — a worker able to write into its own inputs would make
the seal over them describe a tree that has since changed. 24 assignments
created concurrently across 8 threads produce 24 distinct roots for each.
Asking twice for the same assignment answers the same roots, because a manager
that crashed after creating them must be able to ask again.

**The revision is the contract and a ref is evidence.** The pinned
`base_revision` is what is checked out; an advertised `source_ref` or
`integration_ref` that no longer names it **refuses** rather than being
followed. §12 rule 7's algorithm/object-format disagreement refuses. Metadata is
created once per source and never shared. What a checkout writes is measured
like any other tree — a checkout is somebody else's process writing into a
directory this component owns, so its answer is evidence and the tree is the
fact.

## Not finished, and named precisely rather than rounded up

**The receiving-boundary inventory is partially integrated.** Adding a module to
this package means declaring every caller entry with an owner and a probe, and
that work is real. Done: literal owner labels at every site (a shared helper
carrying its caller's label is a boundary the inventory cannot attribute — the
same lesson as the previous cut), the seven path entries delegated to `_real`,
the seven `GitPort` forwarding entries stated, and three witnesses written.
I also applied the structural half of the fix. `materialize_git_source` had
**three** owner calls at three labels, so the inventory attributed all three to
every caller entry of that function; each is now a private single-owner helper
-- `_pinned`, `_advertised`, `_resolved` -- which is the pattern
`attempts.py:_attempt_row` and `_source_identity` already use.

What remains is the declaration table catching up with that split, and it is a
mechanical pass rather than a design question:

- `DELEGATED` entries pointing each subject at its new helper
  (`source.base_revision` at `_pinned`, the two ref members at `_advertised`,
  the repository's answer at `_resolved`);
- the same for the seven path entries, which I declared and which the walk
  still reports as unowned -- the delegation is written and not yet effective,
  and I had not finished diagnosing why;
- one probe per resulting `(entry, label)`.

`tests.manager.test_boundary_inventory` therefore has **4 failures that are
mine**, and I am not reporting them as anything else. I stopped here rather
than push a large mechanical edit I could not finish and verify in one pass:
leaving that table half-written is worse than leaving it named.

## Two operational findings

**1. Building Git fixtures would violate the standing role instruction.** The
instruction for this deployment is "Never perform mutating Git operations", and
a real fixture repository means `init` and `commit`. So the transport is an
injected `GitPort` — which is the better design regardless, is the shape
`AuthorityPort` already uses, and keeps the *verification* (what W6631 owns)
provable without this package deciding how a repository is reached. The tests
drive a fake that answers the same two questions.

What this does **not** prove is that a real repository answers them that way.
That adapter is genuinely the next cut, and I would rather name the gap than
write it blind or quietly run the commands the instruction forbids. **If the
reviewer rules that temporary throwaway repositories under `/tmp` are outside
the intent of that instruction, say so and I will add them.**

**2. The full Python gate is red for reasons that are not this Work's.** W6592
cut A came back changes-requested during this claim, with reviewer-added cases
in `tests/manager/test_handshake.py` that currently fail. Those are mine from a
different claim, tracked there, and I have not touched them under this one —
"own only the implementation you have claimed."

## State

**Awaiting independent review.** The component and its 36 cases are complete;
the inventory integration is not, and is the first thing to finish.


## Review corrections — 2026-08-24

Four of the seven items are done; three are not, and they are named rather than
rounded up. `test_workspaces` is **43 methods, all passing**;
`test_dependencies`, `test_text_sweep` and `test_handshake` are green beside it.

**Item 2 — the frozen closed fragment, done.** Both operations now validate
against `directorySource` / `gitSource` before a member is read or the
filesystem is touched. My hand-written member list was a *second* contract for
a shape the schema already states exactly, and it let a malformed source reach
a `realpath` call before anything had established it was a source. A consequence
worth recording: the frozen `relativePath` type now refuses `../escape` earlier
than my own containment check, so that case was migrated to assert the earlier
refusal. The containment check is **not** redundant — it answers what the
schema cannot, which is whether a well-formed relative path lands inside *this*
assignment's inputs root once links are resolved.

**Item 3 — the short write, done.** `os.write` may move fewer bytes than it was
given; a truncated delivery would have been published under the digest of the
whole file, which is the seal describing the wrong tree by another route. The
write now loops, and a case drives it deterministically by making every write
move one byte, then **re-measures the published tree** and requires it to equal
the measured one.

**Item 4 — the staging name, done.** It used to *remove* whatever it found: a
symbolic link planted there would have been followed by that removal, deleting
somebody else's tree. It now `lstat`s the name — asking about the name rather
than what it points at — and refuses. A case plants a link, a directory and a
file in turn and requires each to survive untouched.

**Item 5 — NOT done, and my test does not prove what its name suggests.** I
added a case for an ancestor directory replaced by a symlink and it passes, but
it passes because the link is visible in the listing — it exercises the
*unraced* case. The reviewer's point is the raced one: a directory swapped
*after* it was listed and *before* it was descended into, which a no-follow open
of the final file does not stop. The correct fix is what the review says —
descend by **opened directory identity**, opening each directory
`O_NOFOLLOW|O_DIRECTORY` and reading it through that descriptor. I did not
attempt it in this round rather than start a partial rewrite of the walk I could
not finish and verify; the case I added stays, with its name honest about being
the unraced case.

**Item 1 — NOT done.** The four boundary-inventory failures remain: the
delegation declarations and one probe per resulting owned entry.

**Item 6 — partially done.** Focused, dependency and sweep suites are green. The
full source suite and the locked gate were not run to completion under this
claim, and the source suite is known to carry the inventory failures above plus
W6632's.

**Item 7 — acknowledged, and it upholds what I reported.** The standing
no-mutating-Git policy includes throwaway `/tmp` fixtures, so the injected
`GitPort` stays and the transport adapter belongs to its own component. That was
the question I raised rather than resolved, and the ruling answers it.

## Delivered and verified state — 2026-08-25

The record above stops before most of what happened. This is what is actually
in the tree.

### The component itself

Items 2, 3 and 4 of the first review landed as described earlier: the frozen
closed `directorySource`/`gitSource` fragment ahead of every member read, the
looping write so a short write cannot publish a truncated file under a whole
file's digest, and a staging name that is refused rather than removed when
something is already there.

**Item 5 — the fd-based descent.** The walk descends by **opened directory
identity**: each directory is opened `O_NOFOLLOW|O_DIRECTORY` and read through
that descriptor, each child opened relative to it with `dir_fd`. A component
replaced after it was listed is a directory the walk never enters. The copy's
second read got the same treatment, because resolving the relative path as a
string walked ancestors by name again — the door the fd walk exists to close.

**The descriptor leak that fix introduced.** Two reviewer cases caught it and
were right. The walk's stack held only directories *not yet descended into*, so
every directory it entered leaked its descriptor for the generator's life; and
`_reach` closed its ancestors only on the failing path, leaking one per
directory above every delivered file. Both now close everything they open. A
security fix that opened a resource hole is worth recording as such.

### The inventory contribution

Written, lost, rewritten, and now complete: eleven `DELEGATED` entries, five
`STATED_OWNERS`, their `WITNESSES`, four witness methods and eleven probes,
with **every declared probe reaching the boundary it names**.

Three corrections along the way, each diagnosed rather than guessed:

- **`base_revision.algorithm`/`.hex` are the frozen fragment's, not
  `_pinned`'s.** Item 2's own correction moved that ownership and neither side
  noticed at the time.
- **`_pinned` is therefore gone.** Measured over every malformed revision a
  caller could send, the fragment admits none of them, so `_pinned` could never
  refuse anything reaching it. The tenth boundary this campaign has removed
  rather than documented.
- **Every fixture failure traced to one line.** `worker_manager.assignment_workspace`
  does not exist — `workspaces` is a submodule and is not re-exported — so the
  drivers errored before their spoiled operands were read. I had hit the same
  `AttributeError` in a throwaway diagnostic two rounds earlier and fixed it
  only there.

### Operational note on this file's edit history

Two earlier attempts at the inventory failed to persist by two different
mechanisms: a block that vanished after having passed at 67/67, and an edit
that asserted on its second anchor and wrote nothing while reporting nothing
wrong. Since then every change to it is confirmed by grep afterwards, which has
caught both a silent absence and a duplicate fixture definition I would
otherwise have shipped.

### Verification

- `tests.manager.test_workspaces` — **46, all pass**.
- `StatedRules` and `EveryStatedOwnerHasAWitness` — **39, all pass**.
- `test_every_declared_probe_reaches_its_named_boundary` — **passes**.
- Full `tests.manager.test_boundary_inventory` — **72 run, 5 failures**, and
  those five are attributed directly rather than by inference: the entry list
  names only `oci.py`, which is W6632's concurrent surface.
- Not run to completion under these claims: the full source suite and the
  locked gate.

## State

**Awaiting independent review.**
