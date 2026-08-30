# Plan

1. Revalidate W33936's delivered workspace grant and the exact failure this
   provider must remove, against the current tree rather than against this
   record.
2. Pin the closed custody operation vocabulary, the custodian identity and its
   mapping, and the single mount, with the reasoning for each written down.
3. Implement the short-lived helper and its typed manager-owned crossing.
4. Compose it into the cleanup ending W33936 leaves failing closed.
5. Add positive, denial, retry/restart, crash-mid-custody and
   worker-mode-hostile cases, plus the Docker and compatible Podman engine
   proofs.
6. Return for independent review; W33936's full cleanup acceptance stays open
   until this closes.

## 2026-08-29 — first implementation round

1. [done] The defect revalidated against the tree rather than the record: the
   W33936 case that documents it still passes, so it is still real.
2. [done] `custody.py` pins the closed six-verb vocabulary, the single mount at
   a fixed target, the owning-worker identity, and the frozen manager-owned
   program. Two design corrections came from running it against a real daemon
   before wiring: the custodian normalizes only what it OWNS, and it needs
   W33936's configured group to traverse the manager-owned workspace root.
3. [done] `tests/manager/test_custody.py` (17) and
   `tests/manager/test_custody_engine.py` (6 + honest Podman skip). The engine
   suite proves the manager's removal is REFUSED before the act and succeeds
   after it, at every mode a worker can choose including `0000`.
4. [NOT DONE] Compose the helper into the ending W33936 leaves failing closed.
   The helper is proved to remove the defect; nothing calls it automatically
   yet. This is the remaining half.
5. [partly done] Positive, denial, mode-hostile, short-lived and single-mount
   cases are in. Retry/restart and crash-mid-custody cases wait on item 4,
   because what they must be idempotent ABOUT is the composed act.
6. [blocked, reported] The compatible-Podman proof cannot be produced on this
   deployment: rootless Podman does not map the manager's supplementary gid, so
   the worker cannot write the workspace and the precondition never exists;
   rootful Podman makes the manager root, and a root manager can remove
   anything, so the "before" refusal cannot occur either. Same constraint
   W33936 raised for a ruling.

## 2026-08-29 — independent review: changes requested

1. [required] Replace the raw caller-selected `attempt_root` with a typed
   manager-owned custody root derived from the assignment's established
   layout. Mount only the exact workspace or result root for that act; never
   the assignment home containing inputs, credentials and manager-owned state.
2. [required] Correct traversal so every nested worker-owned directory is
   made traversable before descent, without following links or widening the
   manager-owned mount root. Hold this with the added nested mode-zero case.
3. [required] Implement all six pinned operations or narrow the confirmed
   decision before claiming a six-operation provider. Place returned
   read/hash/archive evidence under an explicit manager-owned contract.
4. [required] Give custody acts a bounded, restart-reclaimable lifecycle.
   `--rm` after normal exit is cleanup, not proof that a manager crash cannot
   leave a live helper holding the mount.
5. [required] Compose the corrected provider into the ended-attempt cleanup
   and add retry, restart and crash-mid-act regressions.
6. [blocked externally] Retain the honest compatible-Podman gate and resolve
   it through the already-recorded deployment/certification decision rather
   than treating a skip as acceptance.

## 2026-08-29 — second independent review: changes requested

1. [confirmed corrected] Retain the exact workspace mount for authentic
   roots and the pre-descent normalization that reaches nested hostile modes.
2. [required P0] Make the root capability originate from authority the caller
   cannot reconstruct or edit. Refuse forged root mappings, symlinked roots
   and a worker-created `result` alias before the engine sees a bind source.
3. [required] Treat every link as an object without following its target:
   inspect it, account for it in hash/archive as the contract defines, and
   unlink it during discard.
4. [required] Define and implement result contracts under which `read`
   delivers complete bytes and `archive` preserves recoverable content rather
   than returning only a head or digest manifest. Stream bounded processing
   rather than reading an arbitrary worker file wholly into memory.
5. [required, unchanged] Implement bounded/restart-reclaimable helper
   lifetime, compose it into the ending, and add retry/restart/crash cases.
6. [blocked externally] Keep compatible Podman as an explicit certification
   blocker until the existing deployment decision supplies a real gate.

## 2026-08-29 — third independent review: changes requested

1. [accepted] Preserve directory symlinks as observable/removable objects
   while excluding their targets from traversal. Preserve the no-link and
   manager-owner refusal at an existing result entry.
2. [required P0] Replace structural inference with real provenance. A caller
   can deliberately reproduce directory basenames and ownership; the custody
   root must instead be derived from an unforgeable allocation capability or
   re-opened from manager-owned durable storage plus the exact attempt
   identity and containment proof.
3. [required, unchanged] Deliver complete read/archive output contracts with
   streaming/bounds, then implement bounded restart-reclaimable lifetime and
   ending composition with retry/restart/crash regressions.
4. [blocked externally] Retain compatible Podman as an explicit blocker.

## 2026-08-29 — fourth independent review: changes requested

1. [accepted narrowly] Preserve refusal of a structurally forged plain
   mapping; expected directory names and ownership remain validation rather
   than provenance.
2. [required P0] Make the authenticated allocation answer immutable at the
   custody boundary, or re-open the exact roots from manager-owned durable
   state keyed by attempt identity. A caller that holds an authentic answer
   must not be able to replace its paths and retarget the mount.
3. [required, unchanged] Deliver complete recoverable read/archive output with
   streaming and bounds, then implement bounded, derivable,
   restart-reclaimable helper lifetime and ending composition with
   retry/restart/crash regressions.
4. [coordination] Apply the current approved engine-certification ruling
   without weakening W36540's separate unconditional-custody boundary.

## 2026-08-29 — fifth independent review: changes requested

1. [accepted narrowly] Preserve refusal from ordinary item assignment,
   deletion and named mutator dispatch.
2. [required P0] Replace the mutable-`dict` inheritance boundary. Inherited
   `__ior__` and explicitly invoked base `dict` methods bypass subclass
   overrides and can retarget both authority-bearing paths; use an immutable
   wrapper/private representation whose storage the holder cannot mutate.
3. [required, unchanged] Deliver complete recoverable read/archive output with
   streaming and bounds, then bounded/derivable/restart-reclaimable lifetime,
   ending composition, and retry/restart/crash regressions.
4. [coordination, unchanged] Apply the current engine-certification ruling
   without weakening unconditional custody.

## 2026-08-29 — sixth independent review: changes requested

1. [accepted narrowly] Preserve removal of `dict` inheritance and the three
   builtin-protocol regressions.
2. [required P0] Remove the mutable `roots._members` authority path. A holder
   can update that ordinary dictionary and mint an unrelated workspace from
   the authentic wrapper. Move root selection to manager-owned allocation
   state keyed by the exact attempt/assignment, or another representation
   whose authority-bearing values are not holder-mutable; do not add another
   mutator override list.
3. [required, unchanged] Deliver complete recoverable read/archive output with
   streaming and bounds, then bounded/derivable/restart-reclaimable lifetime,
   ending composition, and retry/restart/crash regressions.
4. [coordination, unchanged] Apply the current engine-certification ruling
   without weakening unconditional custody.

## 2026-08-29 — seventh implementation round

1. [done] **The sixth-round P0 is corrected at its owner.**
   `attempt_custody_root(workspace_group, storage, assignment_id, which)`
   derives the mount from the allocation operands and reads no path-bearing
   object at all, so no representation of `AllocatedRoots` — mutable or not —
   can retarget it. `AllocatedRoots` members additionally moved behind a
   `MappingProxyType`, recorded as defence rather than as the mechanism.
2. [done] **Path-shaped attempt identities refused**, and the resolved source
   proved contained under the storage root. `boundaries.identity` owns durable
   text and says nothing about path syntax, so this had to be stated directly.
3. [done] **The reading verbs stream at constant memory**, and `read` carries
   base64 bytes with an explicit `complete` member instead of a silently
   truncated, U+FFFD-mangled head. Proved under a real `RLIMIT_AS` bound, with
   a companion case that drives the superseded whole-file read under the same
   bound and requires it to fail.
4. [OPEN RULING, not implemented] **What `archive` must return.** Recoverable
   content is in structural tension with M36166's single mount; the analysis
   and a proposal are in `FINDING.md`. `archive` now declares
   `content: "manifest-only"` so it cannot be mistaken for content custody.
   This needs the approver, because M36166 names six verbs and narrowing that
   is the approver's act.
5. [NOT DONE, unchanged] Bounded/derivable/restart-reclaimable helper lifetime.
6. [NOT DONE, unchanged] Ending composition, and the retry/restart/crash
   regressions that depend on it.
7. [blocked externally, unchanged] Compatible-Podman certification.

## Owed against this Work, and not previously raised by any review

`custody.py` has NO entries in `tests/manager/test_boundary_inventory.py` at
all — this Work's module was never registered in that gate. It is owed and is
named here so it is not lost. It is not added in this round for the reason
W38956 recorded the same week: that gate is currently failing on 29 orphaned
entries across `attempts.py`, `intake.py`, `interrogation.py`, `lanes.py`,
`oci.py`, `posture_slots.py` and `workspaces.py` that predate this round, and
the file carries another participant's uncommitted edit. Adding entries to a
registry whose attribution mechanism is mid-change, in a file somebody else is
editing, is the parallel-edit collision `AGENTS.md` requires ownership to be
established for first.

## 2026-08-29 — seventh independent review: changes requested

1. [accepted narrowly] Preserve removal of the path-bearing
   `AllocatedRoots` operand and the streamed/bounded read/hash corrections.
2. [required P0] Authenticate the workspace storage root through
   manager-owned durable/configured authority. Deriving
   `<storage>/<attempt>/workspace` does not remove caller path selection while
   `storage` itself remains an ordinary caller-supplied host path.
3. [required P1] Validate the attempt home and workspace with no-link/ownership
   checks before creating a missing result directory; a refused mint must not
   create through a parent symlink target.
4. [required, unchanged] Resolve archive semantics, bounded/reclaimable helper
   lifetime, ending composition, retry/restart/crash proof and the applicable
   engine/boundary-inventory gates.

## 2026-08-29 — eighth implementation round

1. [done] **[P0] The workspace store is a deployment record.**
   `WorkspaceStorage`, `configure_workspace_storage` and
   `configured_workspace_storage` mirror the group's capability exactly,
   including the journal/projection cross-check and the refusal to
   reconfigure. `attempt_custody_root` takes two capabilities and a name, and
   no path.
2. [done] **[P1] The result root is created only after every existing parent
   is proved**, and is derived from the resolved real workspace so the write
   cannot traverse a link that appears after the proof. Held by the review's
   own regression, kept probative and mutation-checked.
3. [done] Nine cases for the new store record in `test_workspaces.py`, mirroring
   the group's four properties plus construction, absence and validation.
4. [done] `workspace_storage` declared in `test_dependencies`' operand
   vocabulary, named apart from the allocation boundary's `storage`.
5. [NOT DONE, unchanged] Bounded/derivable/restart-reclaimable helper lifetime;
   ending composition; retry/restart/crash regressions.
6. [OPEN RULING, unchanged] What `archive` must return — the analysis and a
   proposal are in `FINDING.md` and only the approver can narrow M36166's
   six-verb decision.
7. [blocked externally, unchanged] Compatible-Podman certification.

## 2026-08-29 — ninth implementation round

1. [done] **[P0] Both path-bearing handoffs are deleted.** `custody_vector`
   reads the durable record, derives and proves the root, and composes the
   argv in one act; `CustodyRoot` and the public `attempt_custody_root` are
   off the surface. The operands are a store handle and an attempt NAME.
2. [done] **The inventory-blocking literal label**, which this round's own
   eighth-round code introduced and which stopped the shared scan from
   producing any verdict.
3. [done] The stale `workspace_storage` operand declaration removed — the
   operand no longer exists, and `test_dependencies`' stale-declaration half
   caught the leftover.
4. [NOT DONE, unchanged] Bounded/derivable/restart-reclaimable helper
   lifetime; ending composition; retry/restart/crash regressions.
5. [OPEN RULING, unchanged] What `archive` must return.
6. [blocked externally, unchanged] Compatible-Podman certification.

## 2026-08-29 — tenth implementation round

1. [done] **[P0] The returned argv is gone.** `custody_act(engine, run, ...)`
   looks up, composes, RUNS through `oci.EnginePort` and answers
   `CustodyAnswer`; `custody_vector` is private and reachable only by the act
   that runs it. Nothing a caller holds afterwards is a host path or an
   executable vector.
2. [done] **[P1] The `--rm` docstring is truthful.** It claimed a crash leaks
   no capability, which contradicts this record's own first-review finding and
   items 4–6 below. It now says what `--rm` actually buys and names the owed
   lifetime work.
3. [done] `run` declared in `test_dependencies`' operand vocabulary, with its
   rationale, under the same name `OciAdapter` already takes it.
4. [NOT DONE, unchanged] Bounded, derivable and restart-reclaimable helper
   lifetime. `CUSTODY_NAME` is still unread.
5. [NOT DONE, unchanged] Ending composition, and the retry/restart/crash
   regressions that depend on it.
6. [OPEN RULING, unchanged] What `archive` must return. Only the approver can
   narrow M36166's six-verb decision.
7. [blocked externally, unchanged] Compatible-Podman certification.
8. [OWED, unchanged] `custody.py` has no entries in
   `tests/manager/test_boundary_inventory.py`. That gate is still failing on
   orphaned entries that predate this round and the file carries another
   participant's uncommitted edit.

## Proposed decomposition, for the round that follows this handoff

The 2026-08-29T22:28:08Z review calls this Work's history a decomposition
warning and directs that items 4–7 be separated into explicit child Jobs
before another subsystem-sized round is added. Naming them here so the
proposal is on the record; **minting them is not done in this round**, because
the review schedules the separation AFTER this correction is handed off and
formal enrichment and priority are the reviewer's and the human's by default.

1. **Resolve what `archive` must return** — an approver ruling, not an
   implementation. M36166 names six verbs and narrowing one is the approver's
   act; `content: "manifest-only"` is the current honest placeholder.
2. **Bounded, derivable, restart-reclaimable helper lifetime** — make
   `CUSTODY_NAME` load-bearing so a restarted manager can find and reclaim a
   helper whose client died mid-act.
3. **Compose custody into the ended-attempt path** — the retry, restart and
   crash-mid-act regressions depend on an ending that actually calls the act,
   and no ending calls it today.
4. **Compatible-engine certification** — externally blocked, and it should
   stop blocking a Work that is otherwise finishable.
