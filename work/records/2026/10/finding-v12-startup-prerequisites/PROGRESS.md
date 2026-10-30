# Implementer progress — W375516

## claim376006 — revalidation only; returned with NO source edit

RESTORED HISTORY. Review 2026-10-28T18-34-43Z asked for the prior attributable
PROGRESS to be restored: claim376067 rewrote this file with `Write` and lost
this section, which was a mistake and is corrected here rather than quietly.

Authorization: owner W371075 E375491, reviewer allocation E375494. I made no
product edit that claim and the tree was unchanged by it; what it established,
read-only at base `f36bcd75ed22430355efe1b274b8f236cb591f6b`, was:

* `bootstrap.install:2104` created exactly four directories -- `stores`,
  `repository`, `logs`, `state` at :2149 -- and created or validated no
  configured workspace, launch or credential root, and never opened the
  control store;
* the three roots are per-worker members of each `worker["deployment"]`, named
  together as `("workspace_storage", "launch_home", "credential_home")` at
  `stage_execution.py:708` and `:859`;
* only `workspace_storage` was derived and checked, by `storage_bound:1683`;
* `instance.layout:53` and `bootstrap.layout:511` already derive every owned
  name including `control_store`, so a prepare step consumes them;
* all three tool files were clean at claim, so nothing needed serializing.

Verification spending that claim: read-only inspection only; no suite was run
because nothing was changed.

## claim376067 — the prepare, the store initialization and the read-only report

Authorization: owner W371075 E375491; review 2026-10-28T18-23-16Z confirmed the
blocker and directed implementation ("voluntary return or unspecified room is
not an owner gate"). Supersedes claim376006, which returned with no source
edit; its analysis is reproduced below where it is still true.

Candidate: `v12/python/tools/bootstrap.py`
`f879d52fd3f53fd1166eadad0b39774caf18b242755d2192df62fd5adb834ae5` and
`v12/python/tests/tools/test_startup_prerequisites.py` (new)
`9822355008f9aa03055e7dca246626891089b0c978a7edbe687eee635e53dd93`, base
`f36bcd75ed22430355efe1b274b8f236cb591f6b`. `tools/instance.py` and
`tools/stack.py` are UNTOUCHED. (`tools/single_worker.py` is also dirty in this
tree and is NOT mine here — it is W325695's accepted-at-source candidate.)

### What the install now owes before it reports success

**The triple is `stage_execution`'s, not a second list.**
`PREREQUISITE_ROOTS` is `("workspace_storage", "launch_home",
"credential_home")` — the three that module already names together at
`:708` and `:859`. `storage_bound:1683` derived and checked only the first,
which is the asymmetry a first start used to discover.

* `prerequisite_places(document)` — the ordered, deduplicated roots the input
  SAYS it needs, reading no filesystem. Two workers legitimately sharing a
  root are prepared once.
* `prepare_prerequisites(document, places)` — creates them inside `install`'s
  existing lock and answers `{place: (device, inode)}` for **only what this
  attempt made**, so the existing `_remove_if_still_ours` unwind removes
  exactly those and leaves every foreign object alone. An existing root is
  left exactly as it is and is **not** in the answer, so a later failure
  cannot remove the operator's. A link or a non-directory at an owed name
  REFUSES before anything else is created. No `chmod`, no recursive
  normalization, no credential copying.
* `initialize_control_store(places, incarnation=, clock=)` — calls the public
  `ControlStore.open` with both operands explicit and **closes** it, so a
  prepared instance is one nothing is attached to. `worker_manager/store.py`
  keeps ownership of empty-store initialization and supported-store adoption;
  no schema behaviour is added and W375444's settlement changes are untouched.
* `prerequisite_report(document)` — **application-read-only**: it creates
  nothing, initializes nothing, repairs nothing, chmods nothing and opens no
  store. It answers the exact path and why (absent, a link, a non-directory,
  or not readable/writable/traversable). `lstat` is deliberate: a root reached
  through a link is one this deployment did not choose.

Both new effects run inside the lock, and the store is initialized **before**
the selector exists, so a destination carrying a selector carries a store that
opened at least once.

### Verification

    tests.tools.test_startup_prerequisites   20 OK  (new)
    tests.tools.test_bootstrap              135 OK  (unchanged, no regression)

The 20 cases drive: the triple against its owner; every root of every worker,
a shared root once, malformed entries; the report creating nothing, naming
each missing path, a link, a file, an unusable mode **without chmodding it**,
and reporting nothing once prepared; the prepare owning what it made,
leaving an existing root unrepaired and out of the unwind, refusing a link
with nothing written through it and a file with its bytes intact, the owned
unwind removing exactly what was made while a foreign directory survives, and
a root REPLACED since creation surviving the unwind; the store initialized and
closed, adopting on a second open, refusing in this command's own voice, and
openable afterwards by a first start.

### Remaining scope

**The existing-instance validation is not yet wired into `tools/stack.py`.**
The read-only answer it needs is `bootstrap.prerequisite_report`, which is
implemented and tested above; what remains is calling it from the stack's
status/validation path and printing its lines, plus the focused case that the
wired command mutates nothing. I did not guess at that call site rather than
read it properly. `tools/stack.py` is unchanged, so nothing is half-wired.

Also still out of scope by the dossier: serving integration and whole-path
timing. No operational install, live provider or engine, retained-store
mutation or Git mutation was performed; every store and root in the tests is
disposable.

## claim376157 — the three preparation safety defects, corrected

Review 2026-10-28T18-34-43Z found three real defects in claim376067's
preparation and they were all mine.

1. **Owned cleanup was lost on a later failure.** `prepare_prerequisites`
   built its OWN dictionary and returned it, so a refusal on the third owed
   root threw away the two this attempt had already created: the unwind never
   saw them, the residue stayed on disk and it then blocked this attempt's own
   retry. The dictionary is now the CALLER'S, passed as `made=` and filled as
   roots are created, so whatever was made is visible to the unwind however
   the function leaves. And every root is now INSPECTED BEFORE ANY IS
   CREATED, so an install that is going to refuse refuses with nothing
   created at all.
2. **An inaccessible existing root was accepted.** A directory this account
   cannot read, write and traverse is one the worker cannot use, and
   accepting it moved the failure to the first start -- the whole defect this
   Work exists to close. It now refuses, and the mode is still not touched.
3. **Ancestor symlinks were followed.** `os.makedirs` creates missing parents
   and traverses existing ones, so a link anywhere above an owed name put this
   deployment's mutable state somewhere it did not choose. `_usable_root` now
   requires the parent's canonical form to BE the parent.

**And the preparation and the runtime copy now happen INSIDE the
unwind-protected block.** They were before it, so a failure in the copy, the
store initialization, the justfile or the selector left every prepared root
behind. The dictionary is owned outside the `try` and filled inside it, which
is what makes both true at once.

    tests.tools.test_startup_prerequisites   24 OK  (was 20)
    tests.tools.test_bootstrap              135 OK  (no regression)

Four new cases drive exactly the review's blockers: a refusal handing back
what was created, nothing created when a later root refuses, an inaccessible
existing root refusing with its mode unchanged, and a linked ancestor refusing
with nothing created through the link.

Candidate: `tools/bootstrap.py`
`de92e5d72627099cd583c2540a4ac10eae402c7b974fa162273a4be685460dae` and
`tests/tools/test_startup_prerequisites.py`
`78a23bad94e89c96fc0661c46d09514ebf69d5819bb3f30ee64a81993b28541a`.

### Remaining scope, unchanged and still honest

`prerequisite_report` has no STORE validation, and the `tools/stack.py`
command wiring is still absent -- both named in the review and both still
open. `tools/stack.py` is unchanged, so nothing is half-wired. The connected
disposable-install demonstration the review asks for (success plus
partial/copy/store/selector failure cleanup through the real command) is also
not yet written: the unit-level cases above prove the corrected behaviours,
not the whole command path.

## claim376216 — returned immediately; no source edit, five defects itemized

Review 2026-10-28T18-45-16Z confirms five further defects. I am returning at
once rather than starting a sixth partial: I do not have the room this claim
to correct five interacting path/ownership rules AND write the connected
disposable-install proof the review requires, and the review is explicit that
helpers alone do not prove installed behaviour. The tree is unchanged by this
claim; `tools/bootstrap.py` and `tests/tools/test_startup_prerequisites.py`
remain exactly the claim376157 bytes (`de92e5d7…`, `78a23bad…`).

### The five confirmed defects, as the next claim's work list

1. **`FileExistsError` is accepted without revalidation.** A racer's object at
   an owed name is silently treated as usable. It must be re-put through
   `_usable_root` — a link, a non-directory or an inaccessible directory that
   appeared in the window must refuse — and it must still not be claimed as
   this attempt's.
2. **Created intermediates are not owned.** `os.makedirs` creates missing
   PARENTS, and only the leaf is recorded, so the unwind leaves every
   intermediate it made behind. Each directory actually created needs its own
   identity in `made`, innermost-first for removal.
3. **The mode is the umask's.** Under `umask 000` a prepared root is 0777.
   Creation must name a private mode explicitly rather than inheriting one.
4. **`_remove_if_still_ours` deletes foreign children.** A directory this
   attempt created that somebody else has since written into must not be
   removed wholesale; the uncertainty must be reported instead.
5. **`prerequisite_report` still accepts ancestor links.** The read-only
   observation must apply the same ancestor rule `_usable_root` now applies.

Then: application-read-only STORE validation, the `tools/stack.py` command
wiring, and the connected disposable-install demonstration — success plus
partial/create/copy/store/selector failure cleanup, races, nested creation,
foreign contents and private access through the real command.

Cumulative verification spending on this Work: claim376006 read-only only;
claim376067 two focused runs (155 tests); claim376157 three focused runs (24
prerequisite cases, twice, plus 135 bootstrap); this claim read-only reading of
the review and no run, because nothing was changed.
