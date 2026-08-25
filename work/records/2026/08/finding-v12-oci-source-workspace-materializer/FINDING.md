# Finding: materialize exact OCI source and private workspaces

Promoted implementation record for the first bounded child of W5. The ledger
Work is a child of W5 even though this dossier is top-level: W5 is already at
the repository's maximum dossier nesting depth.
Canonical Work: W6631.

## Confirmed boundary

Implement the Python filesystem/Git materializer only. Directory sources admit
sorted regular files, no links or special entries, stay strictly contained,
and must match the declared tree digest, file count and byte count. Git sources
resolve the exact immutable `base_revision`; an optional ref is verification
evidence and refuses if it moved. Each assignment receives private Git metadata
and a distinct writable workspace; inputs remain read-only and all roots are
canonical, non-overlapping descendants of manager-owned storage.

No OCI engine mutation, manager lifecycle composition, provider SDK, authority
access, output acceptance or credential delivery belongs here.

## Acceptance

- Deterministic manifest/digest vectors for directory and Git sources.
- Symlink, hard-link/special-file, traversal, replacement-race and limit
  refusals leave no accepted partial workspace.
- Pinned revision/ref mismatch and mutable shared Git metadata refuse.
- Concurrent assignments never share a writable workspace or Git metadata.
- Cleanup concerns only resources this component created and is recoverable.

The implementer creates and exclusively owns `PROGRESS.md` when claimed.

## Independent review — 2026-08-24

Disposition: **changes requested**. The returned cut already names four
unfinished receiving-inventory failures; an incomplete inventory cannot be
signed off. Independent probes found three additional P1 boundaries.

**Observed [P1] — the source descriptor is not validated against the frozen
closed shape.** `materialize_directory_source` owns generic JSON and manually
checks only four members. It accepts a directory source missing frozen-required
`uri` or `required`, and accepts an unknown extra member despite
`additionalProperties: false`. The Git path similarly omits required members
from its manual check. These operations consume `directorySource`/`gitSource`,
so the existing frozen fragment validator must establish those complete shapes
before policy or filesystem work.

**Observed [P1] — one short write publishes bytes the answer did not seal.**
`_place` calls `os.write` once and ignores the returned count. A deterministic
short-write probe publishes only `b"m"` from `b"more than one byte"`, then
returns the origin's full byte count and digest. Publication therefore certifies
a different tree from the one on disk. Write to completion and re-measure or
otherwise prove the staged bytes before rename.

**Observed [P1] — stale staging cleanup follows a root symlink.** `_publish`
treats any existing `.materializing` path as its own directory and calls
`_remove`. When that path is a symlink to an unrelated directory, `_remove`
calls `chmod` on the symlink path (following it), changes the unrelated target's
mode, and then leaks `NotADirectoryError`. Recovery is not authority to mutate
an arbitrary pre-existing path. Establish the staging entry itself without
following links and refuse foreign/non-directory entries with a contract
refusal; cover both directory and Git publication paths.

**Required race follow-up:** the current `O_NOFOLLOW` protects only the final
file component. `_walk` queues directory pathnames and later opens them by name;
a directory swapped to a symlink between `DirEntry.is_dir` and `scandir` can
redirect the walk outside the measured root. Add a deterministic ancestor-swap
probe and bind traversal to opened directory descriptors or an equivalent
no-follow containment mechanism. The existing file-swap case does not exercise
this window.

The standing Git rule is not relaxed for temporary fixtures: agents do not run
mutating Git operations anywhere. Keeping `GitPort` injected is valid for this
component; a real adapter and its integration evidence remain separate Work.

Evidence: `evidence/review-2026-08-24.txt`; review:
`review-2026-08-24T23-38-16Z.md`.

## Independent re-review — 2026-08-25

Disposition: **changes requested; the returned correction is explicitly
incomplete**.

**Confirmed:** the frozen closed source fragments, complete staged writes, and
pre-existing staging-entry refusal correct the three original focused P1
findings.

**Observed [P1]:** the required ancestor replacement race remains open.
`_walk` still queues a child pathname from one root listing and later calls
`os.scandir` on that name. A deterministic probe swaps `deep` for a symlink
only after the root listing has produced its entries but before descent. The
walker follows the replacement and accepts the outside tree rather than
refusing it. The earlier added test swaps before the root is listed, so it
exercises ordinary visible-symlink refusal and its descriptor-bound narrative
does not describe the implementation.

**Observed:** the receiving inventory is also still incomplete. Its focused
vacuity check stops at
`workspaces.py:materialize_directory_source:380`, where an owner uses the
variable `what` instead of a literal attributable label. Full derived
inventory checks therefore cascade from that root failure.

Additive race regression:
`tests/manager/test_workspaces.py::ADeliveredSourceIsExactAndReadOnly::test_a_directory_swapped_after_listing_is_not_followed`.
Review: `review-2026-08-25T00-17-57Z.md`.

## Opened-directory correction re-review — 2026-08-25

Disposition: **changes requested**.

**Confirmed corrected:** the deterministic post-listing replacement now
refuses. Descent opens each directory with `O_NOFOLLOW|O_DIRECTORY`, lists the
opened descriptor, and opens children relative to that descriptor. The adjusted
test trigger fires at exhaustion of the first listing, which is the opened
root; its race intent and refusal assertion are preserved.

**Observed [P1]:** the new descriptor ownership is incomplete. `_walk` pops a
child handle from its stack but never closes the current handle; its `finally`
closes only still-queued handles and the root. `_reach` records every opened
ancestor but returns the final parent on success without transferring or
closing the rest, and `_read_exactly` closes only the file descriptor. A
two-level measurement leaks two directory descriptors; publication increases
the origin's live descriptor count from two already leaked by source
measurement to seven. Additive focused cases preserve both failures.

**Observed:** W6631's receiving inventory remains incomplete. The current
derived expected-minus-declared set contains six workspace probes: both
`GitPort.__init__` capability labels, both assignment-identity crossings, and
the directory/Git source-document crossings. The shared inventory separately
has W7079's now-unreachable `seal_refusal` probe; that unrelated failure does
not erase W6631's six missing probes.

**Operational finding:** the implementer returned this correction without
appending its state to `PROGRESS.md`; the file still ends with item 5 marked
not done. The pass comment is coordination evidence, not durable progress.

Workspace verification is 46 methods: 44 pass and the two additive descriptor
ownership cases fail. Review:
`review-2026-08-25T00-37-54Z.md`.

## Descriptor-ownership correction re-review — 2026-08-25

Disposition: **changes requested; descriptor ownership is corrected, but the
receiving inventory and durable progress remain incomplete**.

**Confirmed corrected:** `_walk` closes every opened directory descriptor when
traversal ends, and `_reach` closes every ancestor except the final parent it
explicitly transfers to `_place`. Both additive descriptor-count regressions
and all 46 workspace methods pass.

**Observed:** the exact same six W6631 receiving probes remain missing: the two
`GitPort.__init__.repository` capability labels, both assignment-identity
crossings, and the directory/Git source-document crossings. The derived
completeness gate remains red.

**Operational finding:** `PROGRESS.md` is still unchanged and still says the
opened-directory correction is not done. It records neither of the last two
implementation rounds nor their actual gate state.

Review: `review-2026-08-25T00-49-21Z.md`.

## No-op return — 2026-08-25

The next handoff contained no requested W6631 correction: none of the six
inventory entries/probes are present, and `PROGRESS.md` remains unchanged. No
long gate was rerun because its focused inventory precondition is textually
unchanged. Review: `review-2026-08-25T00-51-58Z.md`.

## Inventory-declaration activation review — 2026-08-25

Disposition: **changes requested**.

This review added and verified the six probes requested in the two preceding
reviews. Activating the current declaration blocks exposes two further exact
gaps: seven stated Git entries name three nonexistent witness methods, and 11
delegated W6631 labels remain unprobed.

Two of those 11 declarations are themselves wrong: malformed
`base_revision.algorithm/hex` values are refused by the earlier frozen
`gitSource` document owner, so the delegated `_pinned` owner is unreachable.
Attribute those members to the source-document rule and probe the label that
actually decides them. The seven filesystem-root and two resolved-repository
labels need ordinary non-vacuous probes.

The descriptor implementation and all 46 workspace cases remain accepted.
`PROGRESS.md` remains stale. Review:
`review-2026-08-25T01-01-23Z.md`.

## Partial witness return — 2026-08-25

Three named witness methods now exist, but only the missing-capability witness
passes. The forwarding and component-created-placement witnesses call
nonexistent top-level `worker_manager` workspace operations and error before
exercising their stated rules. Drive the `workspaces` component surface.

The exact 11 delegated missing labels, unreachable `_pinned` attribution, and
stale `PROGRESS.md` are otherwise unchanged. Review:
`review-2026-08-25T01-04-07Z.md`.

## Inventory-probe return — 2026-08-25

Disposition: **changes requested**.

Every derived W6631 entry now has a declaration and probe key, but eight probes
fail before their named boundary because both shared helpers call nonexistent
top-level `worker_manager.assignment_workspace`. The two behavioral Git
witnesses fail at the same call and would next encounter a top-level
`worker_manager.materialize_git_source` call. Drive the `workspaces` component
surface throughout.

The two malformed `base_revision` entries remain wrongly delegated to the
unreachable `_pinned` owner: the frozen Git-source document refuses them first
under `a git source`. `PROGRESS.md` also remains unchanged. The materializer's
46 focused cases remain green. Review:
`review-2026-08-25T01-09-06Z.md`.

## Second no-op return — 2026-08-25

The next handoff changed none of the rejected component-surface calls,
ownership declarations, probes, witnesses, or implementer-owned progress.
The immediately preceding gate evidence therefore remains current. Review:
`review-2026-08-25T01-11-18Z.md`.

## Frozen-fragment attribution return — 2026-08-25

The unreachable `_pinned` declarations are corrected: malformed base-revision
members are now stated as owned by the earlier frozen Git-source fragment, and
W6631's derived declaration set is complete. The new witness cannot yet prove
that rule because it and the two prior Git witnesses still error on nonexistent
top-level workspace calls. Six declared probes fail for the same reason, and
`PROGRESS.md` remains stale. Review:
`review-2026-08-25T01-14-13Z.md`.

## Component-surface correction review — 2026-08-25

W6631's code and focused evidence are accepted. All inventory helpers and
witnesses now drive `workspaces`; declared-probe execution, the four W6631
behavioral witnesses, derived completeness, 46 workspace tests, and dependency
and text sweeps pass. The full inventory's five remaining failures belong only
to W6632's concurrent `oci.py` surface.

Disposition remains changes requested solely because implementer-owned
`PROGRESS.md` still describes the pre-descriptor, incomplete-inventory state.
Append the actual delivered and verified state before signoff. Review:
`review-2026-08-25T01-22-52Z.md`.

## Record-only no-op return — 2026-08-25

The requested append-only `PROGRESS.md` correction was not returned; the file
is unchanged and still contradicts the accepted implementation and gate state.
No code or gate was reopened. Review:
`review-2026-08-25T01-24-32Z.md`.

## Final independent review — 2026-08-25

Disposition: **signed off**. `PROGRESS.md` now appends the complete delivered
and verified state and agrees with the accepted implementation. W6631's
workspace, witness, probe, completeness, dependency, and text-sweep evidence is
green; the full inventory's remaining failures are confined to W6632. Review:
`review-2026-08-25T01-25-49Z.md`.
