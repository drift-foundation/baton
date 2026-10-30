# Implementer progress — W376955

## claim377016 — returned with the design; the previous plan was rejected

Within W376246's accepted scope; parent review 2026-10-28T19-57-29Z retains
the defects. The tree is unchanged by this claim: `bootstrap.py` `46b5b29d…`
and `test_startup_prerequisites.py` `cdf5afd5…` are the claim376409 bytes.

**The assignment rejects the fix I had planned**, in those words: *"A
post-replacement fstat/lstat comparison is not creation provenance."* It is
right. Comparing after the fact only narrows the window; it does not make the
object this attempt created the object it then modifies.

### What creation provenance actually requires here

**Stop chmodding entirely.** The defect exists because the mode is applied
AFTER creation, so there is a moment where a `chmod`/`fchmod` can land on
somebody else's object. Remove that moment:

* hold the PARENT by descriptor — `O_RDONLY|O_DIRECTORY|O_NOFOLLOW|O_CLOEXEC`
  — and create each component relative to the descriptor of the component
  above it, so the lookup is bound to the exact directory object this attempt
  holds and an ancestor substitution cannot redirect it;
* create with the mode in the creating call: `os.mkdir(leaf, 0o700,
  dir_fd=parent_fd)`, with the process umask cleared across that single call
  so the mode is EXACT rather than filtered;
* **never `chmod` or `fchmod` anything.** With the mode supplied at creation
  there is nothing left to apply to a foreign object, which is why this closes
  the defect rather than shrinking it;
* take the ownership identity with `os.stat(leaf, dir_fd=parent_fd,
  follow_symlinks=False)` purely to record it for the unwind. If that
  disagrees or fails, record the uncertainty — it changes no object either
  way.

**And the uncertainty accounting stays honest.** `EACCES`/`EPERM` is an access
failure, not a replacement; `ENOENT`/`ELOOP`/`ENOTDIR` suggest one. Whatever
happened, a component this attempt created is recorded as owned — flagged
uncertain where it is — rather than left untracked, which is the residue the
unwind exists to remove.

### Why no edit this claim

This replaces the creation path rather than patching it, and the assignment
requires proving that ordinary, symlink and ancestor substitution never chmod
or adopt a foreign object, that a component appearing mid-way refuses safely,
that intermediate creation is tracked, and that open/stat failures stay
honest. I did not have the room to rewrite that path and prove all five, and
the parent has correctly refused four fragments already. The design above is
exact enough to implement in one claim.

The runtime-copy successor waits, as the assignment says. Verification
spending: read-only reading of the assignment and parent review; no run,
because nothing was changed. No engine, provider, operational install,
retained store or version-control action.

## 2026-10-28 — baton.codxpc claim E377080

Read canonical detail, standalone claim, all events through E377080 and entire T376955 through M376955 with no continuation; full child dossier/current review, parent FINDING/PLAN/current defect review and accepted JOINED-PROPOSAL. Existing bootstrap46b5b29d/testcdf5afd5 bytes revalidated and retained in evidence/claim-377080/BASE.json with copies. Own prerequisite preparation/report helpers and associated tests; sibling runtime-copy/install work remains gated and untouched. No product/kernel/engine/provider/operational scope added.

Revalidation confirms mkdir/open/fchmod observes a replaceable name, and ancestor pathname prechecks do not bind subsequent creation. Implementation mechanism: descriptor-relative ancestry plus a kernel inotify guard installed BEFORE mkdir. Only the exact single directory-create event with no intervening replacement/metadata/lifecycle/overflow events can bind the subsequently opened O_PATH handle to that creation. O_PATH permits proving the object even under restrictive umask; permissions are changed through its pinned proc-fd only AFTER this proof. No process-global umask change. A missing/uncertain notification proof refuses without chmod, adoption or deletion authority, with an explicit uncertain effect in the caller ledger. This is a Linux no-follow filesystem mechanism; unsupported observation fails closed before effects. Tests will inject real replacement effects through the actual preparation entry and verify foreign preservation, not only identity equality. Final named-chain revalidation detects ancestor substitution while all edits use held parents.

### E377080 completed creation-only candidate — awaiting review

Changed bootstrap.py prerequisite helpers/report and uncertain-effect branch of existing cleanup; test_startup_prerequisites.py adjusts three old fault-injection seams and adds13 real filesystem cases. No runtime-copy/whole=True/install-lifecycle edits. Existing foreign dirty base preserved in BASE.json/snapshots; candidate consists only of the delta from those pinned bytes. Current read-only Git HEAD 8876bf950ff1f8ab8767ce9786df268cc9d767c6; human index/history untouched.

Creation provenance uses pre-mkdir parent watch plus opened-handle continuity, not post-replacement equality. Uncertain effects are explicit non-identity ledger values and cannot authorize deletion. Proven values remain tuple-compatible and retain an O_PATH duplicate to prevent inode reuse until ledger release. No process-global umask mutation; after proof only the pinned object receives0700. Existing roots are never repaired. Preparation/report use no-follow descriptor checks and report honest access/identity uncertainty. Kernel event absence/overflow/loss fails closed. Linux capability/resource failure is a refusal, not an unsafe fallback.

Evidence at evidence/claim-377080: CANDIDATE.json SHA256 365100971d0308ad27e75ced0dfebe6d907e8d4a594e5ea749b3797037d6339b, source snapshots and base-relative diffs, MATRIX.md, focused.log/json, combined.log/json and ACCOUNTING.json. Final46 focused tests pass, 0.401189346s measured subprocess wall. Broader179 run:84 tmpfs fixture-admission failures and95 passes, 16.106335977s; no aggregate-green claim or disk-only outcome inferred. Initial runs:33 tests/3 stale injection failures0.178546701s;33/1 diagnostic mismatch0.162786796s;44pass0.185485120s (tool wall). Claim cumulative measured 17.034343940s; parent historical total unknown, earlier costs preserved. No broader repeated run after environmental refusal.

Return baton.bug for independent exact-candidate review. Bounded creation outcome complete; W376956 still owns runtime copy/owned unwind and full connected install proof, parent W376246 integrated acceptance. Existing whole=True foreign-descendant deletion defect remains untouched. No engine/provider/build/operational install/retained-store/Git mutation.
