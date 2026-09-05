# Progress

Not started. W62098 supplies the confirmed decisions; this bounded child owns
their source/workspace implementation. Revalidate current dogfood/workspace
file ownership before editing because the working tree contains live changes.

## 2026-09-05 — baton.claude — correcting the run7 candidate (PLAN item 8)

The run7 proposal is evidence, not a base to package again: PLAN item 8 asks
for its two P0 and four P1 defects corrected as one coherent change. The
correction is being made in the working tree, on top of the run7 candidate
bytes, against `HEAD` `8f809a9`.

### Where the run7 candidate came from, and what was reproduced first

The eleven changed paths were read from the retained immutable proposal's
`result.json` and copied into the tree from its `candidate/` archive. Before
touching anything, both of the reviewer's measurements were reproduced exactly:
`tests.tools.test_single_worker` is 85/85 on the baseline and 91 with one
failure and one error on the candidate, and the two named cases are the ones
that fail. `tests.manager.test_source_boundary` plus `test_dependencies` run 75
with two skips, as reported.

### Done: the mount-safe cleanup [P0]

`_remove` decided "this is a mount" by comparing `st_dev` with the tree root,
and a bind mount from the same filesystem keeps the bound directory's device
number — so a source bind-mounted from the same disk passed that test and its
contents were walked and unlinked.

`st_dev` answers "is this another filesystem", which is a different question
from "is this a mount", and only the second one was being asked. The kernel's
own table answers it, so `workspaces` gains `mount_table` and `mount_points`
reading `/proc/self/mountinfo`, and the walk refuses any directory the table
names. The device comparison is KEPT beside it: it needs no `/proc` and still
catches a cross-device mount if the table is ever the thing that is wrong.

The table is read ONCE, before the walk removes anything — a per-directory
re-read would be a window, and an unreadable table now refuses the cleanup
before a single entry is gone rather than being read as "no mounts here",
which is the reading that would quietly restore the defect.

There was already one reader of `mountinfo`, in `source_boundary.filesystem_of`.
Two modules parsing the same file with two copies of the escape rules is how
they end up disagreeing about which directory a mount point is, so the reader
moved to the lower module and `filesystem_of` now imports it. `source_boundary`
does not gain an import cycle: it already imports `workspaces`.

Three cases. The discriminating one leaves the device number ALONE and reports
the mountpoint through the kernel's table, which is the fact the corrected code
reads; measured against the device-only implementation it fails, and the two
pre-existing cleanup cases still pass there — so it catches this defect and
nothing else. A second case proves the unreadable-table refusal happens before
removal. The third is the REAL bind mount the review asked for, gated on an
actual capability probe rather than assumed: this host refuses
`unshare --mount`, so it skips, and its skip message names the case that proves
the same boundary without the capability. A suite that could only skip here
would report green on a host where nothing was exercised, which is why the
table-driven case exists beside it rather than instead of it.

### Done: the exact-base checkout [P1]

The plan was `clone` then `rev-parse --verify <base>^{commit}`, and neither of
those checks anything out. `clone` takes the source's CURRENT HEAD and
`rev-parse` proves only that the object is PRESENT, so a source whose HEAD had
moved on while still containing the declared commit satisfied both commands and
the worker edited the wrong revision.

`detach_vector` is added between them — `checkout --detach <base>^{commit}`,
which makes the worktree the commit and fails on a tag or a tree of the same
name — and `verify_vector` now asks for the ACTIVE HEAD rather than for the
base's existence.

That changes what a step is. Exit status cannot express "the worktree is at
this exact commit", because the command that answers which commit it is on
succeeds whatever the answer; so a step is now an argv AND the output it must
produce, and the party that runs it compares rather than interprets. A step
with nothing to compare says so with `None` instead of leaving a reader to
infer it.

The regression is a REAL repository whose HEAD is a second commit while the
assignment declares the first. The argv-shape case cannot see this defect —
both superseded commands compose fine and both exit zero — so this one runs
the steps and reads the file. Measured against the superseded plan it fails
with the checkout holding the later commit's content, which is exactly the
worker editing the wrong revision.

### Done: the faulted-terminal observation test [P1]

The candidate removed `self._temporary` while the pre-existing W85500
no-mutation case still dereferenced it. It now allocates a second disk-backed
directory through the same helper the root uses, which is outside the digested
root by construction and goes away with the case; pointing at the root's parent
would have written into whichever shared directory that helper chose. The
W85500 assertion is unchanged and the case passes.

### Measured after these three

`tests.manager.test_source_boundary` + `test_dependencies`: 75 → 79, all
passing, three skips (the two pre-existing ones plus the capability-gated real
bind). `tests.tools.test_single_worker`: 91 with ONE failure — the composition
case, which is the defect below and not yet corrected. The error the candidate
had is gone.

### Not done yet, and named rather than implied

- **[P0] the worker never executes the source profile or uses the disk
  workspace.** This is the central acceptance path and the largest of the six:
  the task document has no profile or declared base to carry, the worker image
  ships no `baton_v12.source_profiles`, and `claude_agent.work` still copies
  `/input/source` into its 64 MiB `/tmp` scratch. Correcting it touches the
  task-document contract, the production publisher in `tools/single_worker.py`,
  `v12/worker/Dockerfile.claude` and `v12/worker/claude_agent.py` — the last
  two are outside the run7 candidate's eleven paths and will be added to the
  set. `test_a_work_request_over_the_composed_root_reaches_the_provider` stays
  failing until it lands, and it is the case that must then exercise the real
  read-only-source-to-workspace transition rather than a fake.
- **[P1] restart re-nominates a replaced source.** Needs persisted
  manager-owned identity recovered across incarnations, path resolution kept
  tied to the validated object through handoff, and races that actually
  substitute the nominated directory.
- **[P1] the workspace quota is declared but not enforced.** Either the live
  byte/entry boundary is enforced against worker writes, or the weaker
  capacity-only contract is recorded as an explicit superseding decision in
  FINDING.md. The finding and deployment text currently promise a bounded
  workspace, so the second option is a ruling and not a documentation edit.

No proposal is packaged for this round: a partial correction bound to a digest
would be a candidate that reads as complete. The Work stays claimed.

## 2026-09-05 — baton.claude — the production connection (PLAN item 8, continued)

The operator released the orphaned claim for continuation and the working tree
was intact. This continues the same correction; the three above are unchanged.

### Done: the worker executes the profile, in the workspace [P0]

This was the central acceptance path and the largest of the six. The profile
package composed plans that no component executed, no runtime field carried the
declared base to the worker, the image shipped no profile package, and the
worker still copied the mounted source into its 64 MiB tmpfs.

**The task document carries the two facts, and one reader owns them.** The
workload contract moves to `baton.dogfood-task/2` with `source_profile` and
`declared_base` beside `source_root`. The host deliberately does not parse this
document — `_task_bytes` says so in as many words, because a host-side copy of
the vocabulary would be a second reader of one contract — so the manager keeps
carrying its own profile word through the manifest as opaque text and the
worker reads its own. The pairing rule is not restated either: `checkout_plan`
already refuses a git profile with no base and a generic profile with one, so
the worker checks only the shapes its document may carry.

**The plan runs, and it runs in the workspace.** `_checkout` executes each step
and compares the output the plan says it must produce; a mismatch is a refusal
rather than a disposition, because a worker that edited the wrong revision and
mentioned it afterwards has already written the wrong patch. `OUTPUT_ROOT` is
the disk-backed workspace bind, so the checkout and the editable candidate both
land there and the tmpfs keeps only the child ephemera roots.

`_scratch`'s superseded reason is worth recording rather than deleting. It said
an editable copy in the workspace "would be material the manager has to collect
and reason about". Collection is by DECLARATION: `output._compare_declared`
refuses an undeclared path outright, so a checkout and a candidate beside the
declared proposal are workspace material that goes away with the workspace. The
placement cost was real and one-directional — the tmpfs is 64 MiB.

**The copy and the diff skip version-control metadata, and infer nothing.** The
skip is passed in and only when the assignment DECLARED the git profile, so no
tree is examined to decide whether it looks version-controlled and a generic
profile's directory of that name is ordinary material.

**The image carries the profile package without gaining the manager.** The
recipe's rule — nothing from `baton_v12` travels, because a worker that could
import the manager is one bug away from holding its capabilities — is kept
literally: the package is copied to a TOP-LEVEL name, `claude_agent` imports
exactly `source_profiles`, and no `baton_v12` namespace exists in the image.
The suites that drive the worker put the package's directory on `sys.path`
under that same name, which reproduces the image's layout rather than relaxing
the rule. The context widened from `v12/worker` to `v12` because a context
cannot reach above itself, and a `.dockerignore` came with it: the wider
context would otherwise pack the whole distribution, and byte-code caches must
not travel — W85497 is the record of what they cost.

**Two things were measured rather than assumed, and one of them was wrong.**
The image was built and inspected: `source_profiles` imports, `import
baton_v12` raises `ModuleNotFoundError`, and no `__pycache__` travelled. It
also had NO GIT — so the Git profile's three steps would each have failed at
the first one, which is the run7 defect one layer down: a capability present
everywhere except where it runs. `git` is now installed and a recipe case
holds it there.

**The composition test exercises the transition.** It stages the container's
view of the bind — the manager composes an empty mountpoint on purpose and this
process has no mount namespace — and then asserts the writable half for real:
the candidate is under the workspace, it is NOT under the scratch, its content
is the mounted source's, and the mount is unchanged by the turn.

### Existing tests changed, and what each change is

Named here because they are the ones a reviewer must weigh.

- `tests/manager/test_claude_agent.py`: the `TASK` fixture moves to `/2` and
  gains the two members; the another-generation case now names `/1`, which is
  the same test against the neighbouring version. `test_the_provider_runs_in_
  the_private_copy_and_not_the_source` becomes `..._in_the_workspace_copy_...`
  — the rule is unchanged and its never-the-source assertion is kept, with a
  NEW assertion that it is not on the tmpfs either. `test_nothing_from_the_
  manager_is_copied_in` stated its property by proxy, refusing the string
  `baton_v12` anywhere in a COPY; it now states the property directly and more
  strictly — no manager module travels, and nothing lands under a `baton_v12`
  destination. Two cases added: the profile package's copy line, and git.
- `tests/manager/test_worker_entry.py`, `test_worker_image.py`,
  `test_claude_agent.py`: one `sys.path` entry each, reproducing the image's
  layout.
- `tests/manager/test_dogfood_image.py`, `tests/tools/test_dogfood_arc_engine.py`:
  the build context operand, one line each.
- `tests/tools/test_single_worker.py`: the delivered task fixture moves to
  `/2`; the composition case stages the mount view and asserts the workspace
  transition.

No existing assertion was weakened. The one case whose subject genuinely moved
says so in its own docstring.

### Candidate path set

Run7 declared eleven paths. This correction adds seven: `v12/worker/
claude_agent.py`, `v12/worker/Dockerfile.claude`, `v12/.dockerignore`,
`tests/manager/test_claude_agent.py`, `tests/manager/test_worker_entry.py`,
`tests/manager/test_worker_image.py`, `tests/manager/test_dogfood_image.py`
and `tests/tools/test_dogfood_arc_engine.py` — nineteen in total, and the
worker paths are outside `v12/python`, which the packaging has to say.

### The whole tree found what the focused suites could not

The first whole-tree run after the contract bump reported nine failures where
seven are pre-existing. The two new ones were both in
`test_dogfood_operator.TheOperatorAndTheWorkerAgreeOnTheTasksCONSTANTS`, and
they were the right test failing for the right reason: the dogfood operator
holds its own copy of the workload's closed member set and schema, on purpose,
so that a document from another generation is refused on the way IN rather
than at a failed provider attempt. A contract bumped at one end and not the
other is exactly what that class exists to catch.

`tools/dogfood_operator.py` moves to `/2` with the two members. Its suite's own
`TASK` fixture moves with it, its two neighbouring-generation cases now name
`/1` — the same test against the version this end must still refuse — and its
`worker()` loader, which imports `claude_agent` by file location, gained the
image's top-level profile name on `sys.path` exactly as the other three suites
did. That suite is 345 passing.

Two more paths join the candidate set for this: `tools/dogfood_operator.py` and
`tests/tools/test_dogfood_operator.py`.

**And the run after that found the two REAL-DAEMON suites, which is the more
useful result.** With Docker available the whole tree also runs
`test_dogfood_arc_engine` and `test_dogfood_retry_engine`, and five of their
cases errored on the same contract bump: each stages its own `task.json`
literal for a real container run. Both fixtures move to `/2`. They now pass —
six cases in 102 seconds — and that is worth naming precisely, because it is
the first evidence beyond a recipe read that the WIDENED BUILD CONTEXT and the
new image content actually work: the arc suite builds the image from `v12` and
drives a real dry run to the worker entrypoint against a live daemon. It is not
the certified provider gate, and it is not a substitute for one, but the image
this correction rebuilds is now known to build and run rather than only to
parse.

Two further paths join for those: `tests/tools/test_dogfood_arc_engine.py` and
`tests/tools/test_dogfood_retry_engine.py` — twenty-three in total.

### Still open

- **[P1] restart re-nominates a replaced source — NOW CORRECTED**; see the
  section below. The ruling was pinned in FINDING.md first, under "Object
  identity is durable; content identity is still refused". Within one incarnation
  `adopt_source_boundary` compares the re-nominated inode against the boundary
  it holds in memory; across a restart there is nothing to compare against
  because the boundary is recomposed from configuration. The ruling supersedes
  exactly that sentence and keeps the sentence beside it: what becomes durable
  is the device and inode this manager already observed — no walk, no read, no
  hash — and what stays refused is any identity of the tree's CONTENTS. It goes
  in the manager's control store rather than the retained input manifest,
  because that manifest is delivered read-only into the container and a host
  device number is a fact the worker has no use for. The same-incarnation
  handoff window is part of the same ruling: what the engine binds must be the
  object the manager proved, not a path it re-reads.
- **[P1] the workspace quota is declared but not enforced**, whose alternative
  is an explicit superseding decision rather than a documentation edit.
- The real-container gate for the rebuilt image. The image was built and
  inspected here; the certified end-to-end run is an operator act.

## 2026-09-05 — baton.claude — the restart identity (PLAN item 8, continued)

The ruling was pinned before the code, and the code follows it exactly.

### Done: a replaced source no longer survives a restart [P1]

`attempts` gains two nullable columns, `source_device` and `source_inode`, with
the same all-or-none CHECK the activity pair has — half an object identity
compares against nothing — and the schema moves to 15. There is no migration
and none is invented: `ControlStore` refuses a database at another schema
because it "does not guess across versions", and this finding's rollout
boundary already requires fresh Job and control stores for production
acceptance.

`pin_source_identity` is WRITE-ONCE and an exact repeat is not a write. Every
later incarnation composes over the same attempt roots, so it either
re-observes the same object or it is looking at a replacement — and a
replacement must refuse rather than re-pin, because re-pinning would erase the
evidence that catches it.

`adopt_source_boundary` takes `pinned` and compares against it. The check it
already had compares a fresh reading with the boundary this same process
composed, which after a restart is ANOTHER fresh reading — that is the whole
defect, and it is why the new comparison is against durable evidence rather
than against a recomputation of the same guess. The deployment reads the pinned
pair unconditionally: a caller that has one and does not pass it gets the
weaker gate.

Three cases, and the discriminating one is measured. The replaced-source case
genuinely unlinks and recreates the nominated directory between incarnations,
asserts that the recomposed boundary AGREES WITH ITSELF — which is the point,
the in-memory gate cannot tell anything happened — and then requires the pinned
pair to refuse. Against an implementation that ignores `pinned` it fails, while
the ordinary-restart case, the same-incarnation substitution and the
pre-existing restart case all still pass there. So it catches this defect and
nothing else.

Two closed registries needed additive members and both are stated: the
persisted-attempt column contract in `schema.ATTEMPT_COLUMNS`, and
`test_dependencies.OPERANDS` for `device`, `inode` and `pinned` — three values
a caller supplies, none of them traversal state.

### Not closed, and named rather than glossed

The ruling has a second half: **what the engine binds must be the object the
manager proved, not a path it re-reads.** Re-proving immediately before the
start NARROWS that window and does not close it — `boundary_mounts` still hands
the engine a path, and the substitution case above proves the narrowing rather
than the closure. Closing it means keeping the validated object reachable
through the handoff, which is an engine-adapter change and is not done here.
The finding pins the property as not optional, so this is an open item and not
a resolved one.

### The registries the schema change touched, and one that only looked like it

Adding two columns and two public functions broke four exhaustive registries,
all of which take additive members and all of which are stated rather than
quietly extended: `schema.ATTEMPT_COLUMNS`; `test_dependencies.OPERANDS`;
`test_secrets`' durable-writer and public-surface accounting; and
`test_text_sweep`'s callable table. Two fixture rows in
`test_boundary_inventory` also carry the persisted-attempt document, and a row
missing a column is not a persisted attempt — which is why six probe cases
about `intake.py` digests failed without `intake.py` being touched at all.
Those are back to the five pre-existing boundary-inventory failures, and the
column-universe one still fails on `operation_id` and `settled_at`, which are
not this candidate's.

### The widened context was fragile, and only the whole tree could show it

The image build failed inside a whole-tree run while passing every time it was
run on its own, and the difference is the change I made: a build context is
TARRED AS IT IS READ, and `v12/python` is a directory the suite writes into
while it runs. Widening the context from `v12/worker` to `v12` put the build's
input under concurrent modification by other cases.

The first `.dockerignore` was a denylist — caches, `.pytest_cache`, build and
dist. That cannot fix this, because it would have to name every transient tree
a suite might create. It is now an ALLOWLIST: exclude everything, re-include
exactly the two directories the recipe copies, then carve caches back out of
those. Nothing else can appear in the context, so nothing else can change under
it. Measured: the context is 288.3 kB, and a `--no-cache` build from it
produces an image whose `source_profiles` imports, whose `git` is present and
which carries no `__pycache__`.

This is worth naming as a lesson rather than a fix. The focused suites could
not see it, the two Docker suites run together could not see it, and a build
that succeeds nine times out of ten under load is exactly the kind of thing
that gets recorded as a flake. What made it findable was that the whole-tree
run does two things at once.

**And the allowlist did not fix it, which is recorded here rather than
discovered by a reviewer.** The next whole-tree run failed the same way, in the
OTHER of the two image-building classes — `test_dogfood_image` where the
previous run failed `test_dogfood_arc_engine`. So the concurrent-context
explanation above is at best incomplete: the allowlist is right on its own
terms and measurably shrank the context to 288.3 kB, but it is not the whole
cause.

**The cause is not yet known, and the diagnostic is why.** Both build sites
asserted on `stderr` alone, and the legacy Docker builder writes its steps AND
its failures to STDOUT — so a real build failure was reported as the daemon's
`DEPRECATED: The legacy builder…` banner and nothing else, naming neither the
step that failed nor the reason. That is a diagnostic that turns a real failure
into an unreadable one, so both assertions now show a tail of both streams and
the exit status. Disk was checked and is not it: 677 GB free.

What is NOT claimed: that this is environmental, that it is a flake, or that it
is unrelated to this correction. The widened context is my change and it is the
obvious suspect; it simply has not been proved yet, and writing either
conclusion down before the next run reads the real error would be the kind of
guess this record exists to prevent.

### The quota [P1]: written up as a RULING TO TAKE, not taken

`workspace_quota` validates two numbers are in range, `_capacity` asks whether
the filesystem currently has that many bytes free, and OCI then supplies an
ordinary writable bind. Nothing bounds what the worker writes and `max_entries`
never reaches the mounted workspace at all — so for the workspace, "quota" is
currently a capacity check wearing a limit's name. For scratch the bound is
real and kernel-enforced; the two are not the same and the acceptance text
treats them as one.

FINDING.md now carries both options with their real costs — a live ceiling
needs privilege or host configuration this rootless launch was deliberately
built without, and the honest weaker contract means a worker CAN fill the
backing filesystem, which has to be said out loud rather than implied — and a
recommendation with its reason. **Nothing in the code is changed either way**,
so whichever is ruled starts from the same place. This one is not an
implementer's call to make quietly: it either changes the deployment's
privilege model, which several other Works rest on, or it weakens a stated
acceptance criterion.

## 2026-09-05 — baton.claude — the capacity ruling, implemented (PLAN item 8)

Six of six findings corrected. The operator released the previous claim and
ruled the quota question; this round is that ruling written into the code, the
names, the tests and the deployment text, and nothing else. The whole-tree
real-Docker gate was deliberately NOT rerun here — the previous run's build
error was the managed turn tearing down its own process domain, not a
Dockerfile diagnosis, and that gate belongs at a durable operator boundary.

### Done: the workspace bound says what it is [P1]

The approved ruling is option B: a launch-time declared-capacity preflight,
admission evidence only, no reservation and no live ceiling, with the exposure
stated out loud. What that costs is a rename with teeth rather than a comment.

`WorkspaceQuota` is `WorkspaceCapacity` and `workspace_quota` is
`workspace_capacity`. `SourceBoundary.quota` is `capacity`, and the
configuration member `workspace_quota` is `workspace_capacity`. The refusal
texts moved with them: "a quota the storage cannot hold" said the storage had
failed to honour a limit, and what actually happened is that a declaration
could not be met AT THAT INSTANT, so it now says that.

**`max_entries` is REMOVED rather than documented as inert.** It was validated
against this build's bound, carried into the composed boundary, and then
reached no mount, no runtime and no sweep — a limit's name over no mechanism,
which is the one shape the ruling explicitly does not permit. Removing it from
the closed configuration member set is what makes a deployment that still
declares it get a refusal instead of a silent ignore, and that is the whole
reason to remove it from the SET rather than from the docstring. The
`max_entries` that stays is `workspaces.copied_manifest`'s, which is a
different delivery's real ceiling and is enforced.

This is a member rename inside `single-worker-deployment/4`, and `/4` has
never shipped: `HEAD` `8f809a9` is at `/3` with `input_source` and no
workspace member at all. So there is no compatible reading to break and no
migration to write — the version this Work introduces is simply defined
correctly the first time.

**Where the honest statement is written, because a rename alone would leave
the reader to infer the contract.** `source_boundary`'s module docstring now
states that scratch is kernel-bounded and the workspace is not, why a live
ceiling needs privilege this rootless launch was built without, and that a
worker can fill the backing filesystem after admission. `_capacity` says it
proves an instant and takes nothing. `DEPLOYMENT.md` gains "The workspace
bound is admission evidence, not a running limit", which says the exposure in
one sentence, tells an operator to size `workspace_storage` for it, and says
the check is not a reservation either. `source_profiles` says it too, because
that is the package that decides how much a checkout writes.

### The two cases that make it a rule rather than a claim

- **No entry ceiling reaches anything.** `WorkspaceCapacity.__slots__` is
  exactly `("max_bytes",)`, a second positional argument is a `TypeError`, the
  composed boundary carries no entry member, and the writable half of
  `boundary_mounts` is an ordinary bind with no size operand. MEASURED against
  a capacity that keeps `max_entries`: it fails on the slots and it is the
  ONLY failure in that class — 1 of 9, with the eight beside it still passing,
  so it catches this and nothing else.
- **The declaration is proved, not reserved.** Two assignments compose over
  one filesystem whose free bytes are held at exactly the declaration, and
  both are admitted. An implementation that deducted an admitted declaration
  from a pool would refuse the second. The filesystem's answer is fixed for
  the case on purpose: a host with room to spare would admit both whatever
  this component did, and the case would prove nothing.

A third is in the deployment: a configuration declaring `max_entries` beside
`max_bytes` is refused as a schema error naming the member, which is the
closed-member-set half of the removal.

### Existing tests changed this round, and what each change is

- `tests/manager/test_source_boundary.py`: the fixture and every call site
  follow the rename. `test_a_quota_no_larger_than_the_scratch_bound_is_
  refused` and `test_a_quota_the_storage_cannot_hold_...` are renamed to say
  capacity; their assertions are unchanged. `test_a_quota_is_two_positive_
  whole_numbers` becomes `test_a_declared_capacity_is_one_positive_whole_
  number` — the removed member is why it tests one number, and the case still
  refuses non-integers, booleans, zero and negatives. Two cases added.
- `tests/manager/test_dependencies.py`: the `OPERANDS` registry entry `quota`
  becomes `capacity`, with the reason recorded beside it rather than swapped
  silently. `max_entries` stays declared — `copied_manifest` still takes it.
- `tests/tools/test_single_worker.py`: the configuration fixture follows the
  member rename and drops `max_entries`; the scratch-bound case is renamed.
  One case added.

No assertion was weakened. No case was deleted.

### Measured, focused

- `tests.manager.test_source_boundary` + `test_dependencies`: 79 → 84,
  all passing, 3 skips (the >64 MiB proof and the two capability-gated ones).
- `tests.tools.test_single_worker`: 91 → 92, all passing.
- `tests.manager.test_claude_agent` + `test_worker_entry` +
  `test_worker_image`: 263, all passing.
- `tests/job_manager` (discovered): 290, all passing.
- `tests.manager.test_oci` + `test_boundary_inventory` + `test_secrets` +
  `test_text_sweep` + `test_contracts_inventory`: 348 run, 5 failures, all
  five in `test_boundary_inventory` and all five the pre-existing ones this
  record already named — the column-universe case still fails on
  `operation_id` and `settled_at`, which are not this candidate's. None of the
  five names a capacity or workspace symbol.

Suites are run with `PYTHONPATH=src:../worker` from `v12/python`.

### Broad gate: not run here, and precisely why

The previous whole-tree result is not evidence about this correction. It ran
3,834 cases in 224.989s with seven failures and two errors, and the image
build returned 143 while downloading packages because the managed turn ended
and tore down its process domain; the detached parent finished after the
runtime was already marked failed. So the earlier note in this record that
"the cause is not yet known" is answered for that run — it was the turn
boundary, not the widened context — and the improved build diagnostics stay,
because they are what would read a real failure if one happens.

The broad real-Docker sweep is therefore recorded as OWED at a durable
operator or v12-managed boundary rather than attempted again inside a bounded
managed turn. The seven pre-existing failures and one pre-existing registry
error remain the known baseline going into it.

### Candidate path set

Twenty-eight paths, enumerated in the handoff. This round changed eight of
them and added none: `DEPLOYMENT.md`, `worker_manager/source_boundary.py`,
`worker_manager/oci.py`, `source_profiles/__init__.py`, `tools/single_worker.py`,
`tests/manager/test_source_boundary.py`, `tests/manager/test_dependencies.py`
and `tests/tools/test_single_worker.py`.

### Still open, and named rather than glossed

- **The same-incarnation handoff window.** `boundary_mounts` hands the engine
  a PATH, and the finding pins that what the engine binds must be the object
  the manager proved. Re-proving immediately before the start narrows the
  window; it does not close it. Closing it is an engine-adapter change and is
  PLAN item 10.
- **The certified real-container provider gate** against the rebuilt image,
  and the broad whole-tree sweep beside it. Both are operator acts at a
  durable boundary; PLAN item 11.

No digest-bound immutable proposal exists for this correction. It was made in
the working tree on top of the run7 candidate bytes against `HEAD` `8f809a9`,
at the operator's direction, and the run7 digests bind evidence that is now
superseded. What review binds is the working tree diff over that baseline; a
digest-bound package, if integration wants one, is a separate act over
unchanged bytes.

## 2026-09-05 — baton.claude — the second review's corrections (PLAN item 10)

Four of five findings corrected and the fifth narrowed to the one interval this
manager does not own, which is written up as a ruling rather than taken. The
review is `review-2026-09-05T05-51-35Z.md`; it was right on every count, and
two of its findings were real custody failures my own focused suites could not
see because they only ever asked the shape that happened to work.

### Done: cleanup asks the mount question BEFORE it descends [P0]

The run7 correction put the check inside the bottom-up walk and argued that
one pass was enough because "a directory is always visited before its parent".
That is true of a mount's own entries and false of everything below them:
`os.walk(topdown=False)` yields a mount's SUBDIRECTORIES first, so a mount
holding one directory had that directory emptied and the refusal arrived after
the data was gone. My two cleanup cases both put their file directly at the
mount root, which is precisely the shape the defect gets right.

The walk is now TOP-DOWN, which is the order in which a mount can be
recognised before anything under it is reached, and removal is a second pass
over the directories the first one ADMITTED. That makes a stronger property
than the review asked for and it is worth naming: a refusal now precedes every
unlink IN THE TREE, not merely the unlinks in the subtree that reached the
mount. A cleanup that half-ran is one an operator cannot reason about.

What is buffered between the passes is directory PATHS and not their contents,
and the second pass lists each admitted directory again through a new
`_entries` — one extra listing per directory, against a guarantee that no
foreign entry is ever removed. The superseded reasoning is recorded in the
docstring and in FINDING.md rather than deleted, because a reader who found
only the new code would not know why one pass is not enough.

Two cases. The nested one builds the tree a real source actually has — a file
at the mount root, one a level down, one two levels down — and requires all of
them afterwards. The second puts the manager's OWN material in another subtree
and requires that a refused cleanup leaves it too. MEASURED against the
superseded walk: both fail, 2 of 7, while the three pre-existing cleanup cases
and the ordinary-arc case still pass there.

### Done: a boundary belongs to the assignment it was proved over [P1]

This one was a real cross-wire and the reviewer's probe is reproduced by the
case. A boundary composed GENUINELY for attempt A — over a source that happens
to be attempt B's workspace, which is nothing to A, because containment is
asked about A's own roots — was accepted by a start vector carrying B's own
genuinely allocated roots. The same host directory then reached the container
writable at `/output` and read-only at `/input/source`, so the read-only claim
was false and a worker could rewrite the Work it was given through the other
name.

Every rule the family had passed: the target is the contract's constant, it is
strictly inside a read-only assignment mount, and the capability is typed and
this manager minted it. None of them asks WHOSE assignment it was proved over.
`oci._source_mount` now takes the start's roots and compares the boundary's
workspace and mountpoint against them, so a capability is provenance about one
attempt rather than about the shape of a topology.

Two cases, one per half — the workspace and the input root — and both fail
against the superseded adapter.

### Done: the object is re-proved where the binds are derived [P1, in part]

`adopt_source_boundary` proved `(device, inode)` and the argv was then composed
from a NAME that the adapter resolved again and the engine resolves once more.
`boundary_mounts` now re-proves the object at the moment the binds are derived,
which is the last instant at which this manager holds anything but a string,
and refuses a path re-pointed since adoption. The case unlinks and recreates
the nominated directory after adoption and requires the refusal; it fails
against the superseded derivation.

NOT CLOSED, and FINDING.md carries it as a ruling with both options and their
real costs rather than a claim. The interval between that proof and the
ENGINE's own resolution of the same pathname cannot be closed while the engine
takes a path: `docker` and `podman` accept `--mount source=<pathname>` and
resolve it themselves. Handing them `/proc/<pid>/fd/<n>` would close it and
costs a daemon that can read this manager's `/proc`, plus a recorded mount
source that is meaningless once the manager exits — which is exactly what
`oci._mounts_disagree` compares a restarted manager's observation against, so
W81857's restart safety would have to be reopened. That is a privilege and
restart-model decision, not an implementer's, and the code says in as many
words that "re-proved" is not "closed".

### Done: the sender validates the two new task members [P1]

`/2` added `source_profile` and `declared_base` to the operator's closed member
set and nothing asked about their VALUES, so `source_profile=7,
declared_base=[]` was returned unchanged and refused inside the container —
which is the refusal this operator's read exists to move earlier, arriving
exactly where it was not supposed to.

`held_task` now asks `source_profiles.checkout_plan`, which owns all three
answers: the profile vocabulary, the base revision's grammar, and the PAIRING.
A copy of those rules here would be a second definition to drift from, and the
two container paths it is asked about are the manager's own constants, which is
what makes it the same question the worker will ask. The both-ends class gains
three cases that ask actual PREDICATES of both ends rather than comparing
constants — six malformed shapes, two unpaired ones, and three well-formed
pairs so the negatives prove something. The two negative cases fail against
the superseded sender; the acceptance case passes there, which is the point of
including it.

### Done: the image boundary is an allowlist again [P2]

The reviewer is right that this was a material weakening and that PROGRESS.md
claimed otherwise; the claim was wrong and this entry supersedes it. Naming
`worker_manager`, `contracts` and `authority` is a denylist, and a COPY of
`attempts.py` or `offers.py` to a top-level destination would have passed while
violating the property the case states.

The distribution has exactly ONE path the image may take, so the case names it
and refuses every other source under `baton_v12` whatever it is called.
MEASURED: with `COPY python/src/baton_v12/attempts.py` added to the recipe the
case fails, and the denylist it replaces would not have seen it.

The continuation defect the reviewer also found is fixed with it. The recipe
has one COPY split across two physical lines, and reading lines separately made
its last token a backslash — so its destination was never asserted and its
continuation was skipped as "not a COPY". `copies()` joins continuations first,
and a second case asserts every COPY's destination including that one, with an
explicit assertion that the split COPY was joined so a future regression in the
joining cannot silently switch the check off again.

### Measured, focused

- `test_workspaces` + `test_source_boundary` + `test_dependencies` +
  `test_oci` + `test_claude_agent` + `test_worker_entry` + `test_worker_image`
  + `test_single_worker` + `test_dogfood_operator`: 990 run, all passing,
  3 skips (the >64 MiB proof and the two capability-gated ones).
- `tests/job_manager` (discovered): 290, all passing.
- `test_boundary_inventory` + `test_secrets` + `test_text_sweep` +
  `test_contracts_inventory` + `test_custody` + `test_intake`: 433 run, 5
  failures, all five the pre-existing boundary-inventory ones this record
  already names. None of them names a symbol this round touched.

Counts by suite where they moved: source_boundary 65 → 68, claude_agent 99 →
100, dogfood_operator 345 → 348. Run with `PYTHONPATH=src:../worker` from
`v12/python`.

Every new case was measured against the behaviour it is about, and in each
measurement only the intended cases failed:

- nested/whole-tree cleanup: 2 of 7 fail against the superseded bottom-up walk.
- cross-assignment and re-pointed source: 3 of 10 fail against the superseded
  adapter and derivation.
- the two new-member cases: 8 subtests across 2 cases fail against the
  superseded sender.
- the image allowlist: 1 of 10 fails against a recipe carrying a smuggled
  manager module.

### Still open

- **The engine's own resolution of the source pathname**, which is PLAN item
  11 and a ruling. Both options and their costs are in FINDING.md.
- **The certified real-container provider gate and the broad whole-tree
  sweep**, PLAN item 12, at a durable operator or v12-managed boundary. Not
  attempted here: the previous attempt inside a bounded managed turn produced
  a build failure that was the turn tearing down its own process domain, and
  the operator ruled that gate off this turn's path.
- **The immutable proposal and digest**, PLAN item 13. The corrections again
  live in the working tree over `HEAD` `8f809a9`; freezing them is the act
  that follows the gate above, and a digest bound before it would bind bytes
  the gate could still change.

### Candidate path set

Unchanged at 28 paths. This round changed seven of them and added none:
`worker_manager/workspaces.py`, `worker_manager/source_boundary.py`,
`worker_manager/oci.py`, `tools/dogfood_operator.py`,
`tests/manager/test_source_boundary.py`, `tests/manager/test_claude_agent.py`
and `tests/tools/test_dogfood_operator.py`.

## 2026-09-05 — baton.claude — the workspace is an object too (PLAN item 11)

The third review's one correctable finding is corrected and its ruling request
is made symmetric. `review-2026-09-05T06-12-29Z.md` verified the previous
round's five corrections and found the half I had left with only a pathname.

### Done: both roots are objects, not one object and one name [P1]

`SourceBoundary` proved the source's `(device, inode)` and held the workspace's
SPELLING. So a real directory created at the workspace's pathname after
composition passed every question adoption asked — it resolves to the same
characters, it is a directory of its own, it is on real storage — and the only
existing replacement case substitutes a SYMLINK, which the spelling checks
already catch. A symlink does not distinguish path identity from object
identity; a real directory is the shape that does, which is why the suite could
not see this.

It is also the half that matters most: the workspace is where the assignment's
answer is collected from, so a runtime started over a replacement would write
its result into material this manager never took custody of. And the acceptance
clause already said a replaced source **or workspace** refuses before a runtime
starts, so this was a gap in this record's own promise rather than new scope.

`_object_of` is `nominate_source`'s last step for the OTHER root — the same
`O_DIRECTORY | O_NOFOLLOW` descriptor, never listed — split out rather than
duplicated, because the workspace is this manager's own answer from
`assignment_workspace` and its spelling has already been proved. The boundary
carries `workspace_device` and `workspace_inode`, and both roots are compared
at adoption, against durable evidence when a caller has it, and again in
`boundary_mounts` where the runtime binds are derived.

**The durable pin now records both pairs in ONE write.** `pin_source_identity`
becomes `pin_boundary_identity(store, *, attempt_id, source, workspace)` and
`source_identity_of` becomes `boundary_identity_of`. One act rather than two,
because the boundary proves the two roots together and two writes would allow a
row that had proved one — the same argument the all-or-none CHECK on each pair
is under, one level up. Each identity is passed as a pair rather than as two
loose numbers, so there are two operands instead of four and no order to get
wrong.

`schema` moves to 16 with `workspace_device` and `workspace_inode` and a CHECK
that ties the four columns together. NO MIGRATION IS INVENTED, for the reason
schema 15 did not invent one: `ControlStore` refuses a database at another
schema because it does not guess across versions, and this finding's rollout
boundary already requires fresh Job and control stores.

Three cases, and each is measured. The same-incarnation one is the reviewer's
own probe — rename the workspace away, create a different real directory at the
pathname, adopt. The restart one recomposes over the replacement, asserts that
the recomposed boundary AGREES WITH ITSELF, and then requires the pinned pair
to refuse. The third replaces the workspace after adoption and requires
`boundary_mounts` to refuse. MEASURED against a boundary that trusts the
composed workspace value: all three fail, 3 of 71, and the 68 beside them pass
there.

### Existing tests changed this round, and what each change is

- `tests/manager/test_source_boundary.py`: the two restart cases pass `pinned`
  as the two pairs rather than one — the shape changed, their assertions did
  not, and each now carries the real workspace identity beside the source's so
  that the half under test is the only thing that can refuse. The
  caller-minted-boundary case passes the two new positional arguments. Three
  cases added.
- `tests/manager/test_dependencies.py`: `device` and `inode` leave the
  `OPERANDS` registry and `workspace` joins it, with the supersession recorded
  beside the entry rather than swapped silently. `source` was already declared.
  This is a REMOVAL from an exhaustive registry and is named as one: the two
  operands no longer exist because the pin takes pairs.
- `tests/manager/test_secrets.py` and `tests/manager/test_text_sweep.py`: the
  durable-writer entry, the public-surface sentence and the callable table
  follow the rename and now describe four numbers rather than two.
- `tests/manager/test_boundary_inventory.py`: the two persisted-attempt fixture
  rows take the two new columns. A row missing a column is not a persisted
  attempt, which is why seven probe cases about `intake.py` digests failed
  without `intake.py` being touched — the same fallout schema 15 produced, and
  it is recorded again because the next column will do it a third time.

No assertion was weakened.

### Done: the pending ruling is symmetric

The reviewer is right that a source-only ruling would leave the writable half of
the same boundary unstated. FINDING.md's handoff section is amended in place to
say its scope was too narrow, and "Both bind sources, not one" states the two
options over BOTH pathnames — object delivery for both roots with the daemon
and restart-comparison costs paid twice, or an explicit supersession of the
absolute wording for both residual intervals. A source-only ruling is
explicitly not one of the options. `DEPLOYMENT.md` gains the workspace
replacement to its list of what refuses before a start, and says the engine's
own resolution of each bind source is not closed.

### Measured, focused

- `test_workspaces` + `test_source_boundary` + `test_dependencies` +
  `test_oci` + `test_claude_agent` + `test_worker_entry` + `test_worker_image`
  + `test_single_worker` + `test_dogfood_operator` + `test_attempts` +
  `test_store` + `test_secrets` + `test_text_sweep`: 1564 run, all passing,
  3 skips.
- `tests/job_manager` (discovered): 290, all passing.
- `test_boundary_inventory` + `test_contracts_inventory` + `test_custody` +
  `test_intake` + `test_offers` + `test_lifecycle_composition`: 448 run, 5
  failures, all five the pre-existing `test_boundary_inventory` ones this
  record already names.

`test_source_boundary` is 68 → 71. Run with `PYTHONPATH=src:../worker` from
`v12/python`.

### Still open

- **The engine's own resolution of both bind source pathnames**, PLAN item 12,
  awaiting the owner ruling now stated over both roots.
- **The certified real-container provider gate and the broad whole-tree
  sweep**, PLAN item 13, at a durable operator or v12-managed boundary.
- **The immutable proposal and digest**, PLAN item 14, which follows that gate.

### Candidate path set

Still 28 paths; this round changed eleven of them and added none:
`worker_manager/source_boundary.py`, `worker_manager/attempts.py`,
`worker_manager/schema.py`, `worker_manager/__init__.py`,
`tools/single_worker.py`, `DEPLOYMENT.md`,
`tests/manager/test_source_boundary.py`, `tests/manager/test_dependencies.py`,
`tests/manager/test_secrets.py`, `tests/manager/test_text_sweep.py` and
`tests/manager/test_boundary_inventory.py`.

## 2026-09-05 — baton.claude — the pin is write-once under the lock (PLAN item 11)

Both findings in `review-2026-09-05T06-27-02Z.md` are corrected. The reviewer's
concurrency probe found a real defect in my own correction: the durable pin I
added to make a restart refusal possible was not write-once at the one
concurrency boundary that refusal exists for.

### Done: the four-column pin is a compare-and-set under the write lock [P1]

`pin_boundary_identity` read through `boundary_identity_of`, decided absence in
Python, and then executed an unconditional `UPDATE`. `ControlStore` opens
SQLite with `isolation_level=None`, so those were TWO autocommit transactions
with a window between them. The reviewer drove two real store connections
through the absence read before either wrote: both were told they had pinned,
neither refused, and the later write replaced the first identity.

That is not a stale return. It is the mechanism failing exactly where it
matters — two incarnations composing on opposite sides of a directory
replacement, where the replacement's identity can overwrite the original and
then satisfy the restart gate the pin exists to make possible. The
"write-once" sentence in the docstring was false, and it was false in the
concurrency case rather than in the sequential one the suites exercised.

`BEGIN IMMEDIATE` now precedes the read, the replay and collision decisions are
made inside that transaction, and the `UPDATE` carries its own
all-four-columns-still-NULL predicate with a `rowcount` check. The pattern is
`manifests.retain_manifest`'s and `store._initialize`'s, which is the same rule
this store already applies to every other decide-then-write: the check outside
answers the common case, the lock decides.

**The predicate is not redundant with the lock, and the comment says why.** The
lock makes concurrent writers serialize; the predicate is what makes the write
REFUSE rather than clobber if the row were ever reached by a path not holding
this transaction, and a `rowcount` other than one delivers that as a refusal
instead of as a silent overwrite. A collision found inside the lock also rolls
back rather than committing, because nothing was written and a read-only
transaction should not commit.

Four cases in `test_attempts.py`, which joins the candidate path set this
round and is named as one. It is an EXISTING repository test file, so the
addition is an existing-test change and is accounted for below rather than
listed as a new file. Three are the sequential contract — first pin recorded and
read back, exact repeat is not a write, a differing identity in either root
refuses with the evidence untouched. The fourth is the forced schedule: both
callers are held at the absence observation by a barrier, each opening its own
`ControlStore` in its own thread, because a SQLite connection belongs to the
thread that made it and this case is about two real manager connections.

**The barrier is what makes it deterministic, and it breaks on purpose.**
Against the corrected code the second caller never reaches the barrier — it is
waiting on the write lock the first one took BEFORE reading — so the barrier
times out, breaks, and the case still completes in about a second. MEASURED
against the superseded write: both callers arrive, both write, both are told
they were first, and the case fails 2 != 1 with both answers present. It is the
only failure of the four there.

The stored value is read back on a THIRD connection that neither writer used,
because an answer that agreed with itself while the row held the other identity
would be the same defect one layer along.

### Done: the schema history names what 16 adds [P2]

The history explained the source pair as 15 and then set `SCHEMA_VERSION = 16`,
so a refused old store could not be related to the actual cutover. The entry is
written: 16 adds the writable workspace's object identity, it is a separate
version rather than an amendment to 15 because a 15 store cannot answer the
question, the CHECK ties all four columns together, and nothing authorized
under 15 is authorized differently under 16.

### Measured, focused

- `test_attempts` + `test_source_boundary` + `test_store` + `test_workspaces`
  + `test_oci` + `test_single_worker` + `test_dependencies` + `test_secrets`
  + `test_text_sweep`: 957 run, all passing, 3 skips.
- `test_claude_agent` + `test_worker_entry` + `test_worker_image` +
  `test_dogfood_operator`: 611 run, all passing.
- `tests/job_manager` (discovered): 290, all passing.
- `test_boundary_inventory` + `test_contracts_inventory` + `test_custody` +
  `test_intake` + `test_offers` + `test_lifecycle_composition`: 448 run, 5
  failures, all five the pre-existing `test_boundary_inventory` ones.
- `git diff --check -- v12`: no output.

`test_attempts` gains four cases. Run with `PYTHONPATH=src:../worker` from
`v12/python`.

### Still open

- **The engine's own resolution of both bind source pathnames**, PLAN item 12,
  awaiting the owner ruling stated over both roots.
- **The certified real-container provider gate and the broad whole-tree
  sweep**, PLAN item 13.
- **The immutable proposal and digest**, PLAN item 14, which follows that gate.

### Candidate path set

**29 paths now, up from 28.** `v12/python/tests/manager/test_attempts.py`
joins the set with the concurrency regression the review required; the
reviewer's own accounting anticipated that it would. It is an existing
repository test file, and the change to it is PURELY ADDITIVE: one new class
of four cases plus two names on the existing import list. No existing
assertion, fixture or case was touched. The other two paths changed this round
are `worker_manager/attempts.py` and `worker_manager/schema.py`.

Every existing test path changed anywhere in the 29-path candidate is
unchanged from the previous accounting except for this one addition.

## 2026-09-05 — baton.claude — the corrected broad gate, and the freeze (PLAN item 14)

The approved ruling is reflected in the code and the deployment text, the
canonical parallel runner runs for the first time in this campaign, and the
candidate bytes now carry a reproducible content digest.

### Done: the ruling is written where the code is read

`FINDING.md` already carried the approved ruling before I reached it, so this
adds nothing to the record and instead makes the implementation agree with it.
`boundary_mounts`' docstring said the residual interval "is a ruling rather
than an implementer's choice"; it now says the ruling was TAKEN, names the
accepted residual for both roots, and states that a descriptor-derived mount
source, a daemon-namespace coupling and a restart-model change are explicitly
out of scope — so a later reader finding that comment does not have to
re-derive why the obvious closure was not the one taken. `DEPLOYMENT.md` says
the same thing to an operator and adds the one sentence an operator actually
needs: the trust boundary includes whoever can write the parent directories of
`nominated_source` and `workspace_storage` between the manager's last proof
and the engine's start.

I drafted a second FINDING section for the ruling before noticing the record
already had one, and removed it rather than leaving two live statements of one
decision. It was minutes old and never reviewed.

### Done: the canonical parallel runner runs at all

`tools/parallel_test.py` refused before executing anything, because
`tests.manager.test_source_boundary` and `tests.tools.test_
quiescent_assignment_finalization` belonged to no registry. That gate is
working exactly as designed — a new module is a loud failure rather than a
silent assumption — and it means the broad parallel sweep has been unrunnable
for every caller since `fda9cf6`.

Both are registered, and the second one is registered WITHOUT being claimed.
Its entry says so in the file: W61984 owns that module, its classification is
read off that suite's own fixture — a disposable control store under its own
temporary directory, an injected fake session, and no agent call, runtime-stop
call, daemon, image or container, which is the module's whole subject — and
W71917 is simply the first Work that made the sharded gate runnable. This is a
one-line repair outside this Work's scope, disclosed rather than absorbed.

### Found and fixed: a latent path defect only the sharded gate could see

With the registry corrected the parallel phase ran and reported 15 errors, all
`ModuleNotFoundError: No module named 'baton_worker'` in
`tests.tools.test_single_worker`.

That module drives the real worker at `serve_exchange` in two of its classes
and reached `baton_worker` by SIDE EFFECT: `test_claude_agent` inserts the
worker directory on `sys.path` at module scope, and single-process discovery
happens to import it first. Under the parallel runner a shard is one TestCase
class in a fresh interpreter, so nothing imports `test_claude_agent` and the
dependency simply is not there.

It is declared now, in the same shape the three sibling suites already use.
**It is not this Work's defect** and the comment says whose it is: W81857's
`worked()` helper reaches the image's module, and the canonical discovery gate
could never have shown it. Measured: `PYTHONPATH=src python3 -m unittest
tests.tools.test_single_worker` — without the extra worker path this suite has
needed until now — is 92 passing.

### The corrected gate, measured

**Parallel phase**, `PYTHONPATH=src python3 tools/parallel_test.py`:
520 shards, **3,634 tests, 6 failures, 0 errors, 3 skipped**. The 15 errors are
gone. The six failures are exactly the recorded baseline and neither is this
Work's:

- `tests.authority.test_catalog.TheMigrationChecklistIsRead.test_the_suite_is_
  one_gate_and_not_a_pile_of_files` — the authority suite's own file registry
  does not list `test_work_label_exposure.py`, which is W29401's module.
- the five `tests.manager.test_boundary_inventory` failures this record has
  named at every round, still failing on `operation_id` and `settled_at`.

Nothing in `tests.manager.test_source_boundary` failed.

**Serial phase**, `--phase serial` (the runner will not reach it while the
parallel phase fails, so it was run explicitly): 16 shards, **235 tests, 4
failures, 0 errors, 13 skipped** — the same count and the same four the
operator's durable run recorded. Every one is an engine-CLEANLINESS assertion
against residue that predates this run: 31 retained `baton-runtime.start-*`
containers and the hour-old `baton-w6633` container and image. The functional
Docker assertions passed, including the real dogfood arc and retry engines
against a live daemon.

**Nothing was deleted to make them pass.** The record says ambient retained
evidence must not be removed or silently attributed to this Work, and it is
not: the four failures are reported as they are, with what they are about.

### Done: the candidate is frozen with a reproducible content digest

There is no attempt custody archive to bind, because this candidate is a
working-tree change rather than a v12 attempt's proposal. What a freeze owes
review is the same either way: an exact statement of WHICH bytes at WHICH paths
were reviewed, so a verdict cannot be quietly outlived by the tree.

`candidate-2026-09-05T07-21-55Z.manifest` in this record is that statement. One
line per path — the proposed file mode, the SHA-256 of the file's bytes, and
the repository-relative path — sorted bytewise, over the 30 paths of the
candidate against base `8f809a9`. The aggregate is the SHA-256 of that text:

    content-digest sha256:daf2bd4f13eb8d095efdd0098e258ba494d2b74467a41b8b21
                          41da6d74d6f52f

It is REPRODUCIBLE and was proved so rather than asserted: a second run over
the unchanged tree produced byte-identical output and the same digest. A
reviewer or integrator recomputes it the same way and a single changed byte at
any path changes the aggregate.

### Candidate path set

**30 paths, up from 29.** `v12/python/tools/parallel_test.py` joins with the
two registry entries. The other three paths changed this round are
`v12/python/src/baton_v12/worker_manager/source_boundary.py` (the docstring
ruling), `v12/python/DEPLOYMENT.md` (the operator-facing caveat) and
`v12/python/tests/tools/test_single_worker.py` (the `sys.path` declaration) —
four in all, none of them new files. Every path and its digest is enumerated in
the manifest above.

### Still open

- **The certified real-container provider gate** was run by the operator at a
  durable boundary and passed; nothing here re-runs it. The broad gate is now
  green apart from the baseline named above.
- The pre-existing baseline items are separately attributable and are NOT this
  Work's to fix: the authority catalog registry, the five boundary-inventory
  failures, the unregistered quiescence module's ownership, and the ambient
  engine residue the four cleanliness assertions see.

## 2026-09-05 — baton.claude — the inventory gate, and a superseding digest

The digest-bound review's [P1] is corrected. It was a real defect and the more
useful kind: not a wrong answer, but a TRUE STATEMENT THAT MISLED.

### What I got wrong, and why the reviewer's framing is the correction

I reported the broad gate's six failures as "exactly the recorded baseline" and
proved it by TEST NAME and COUNT. Both were right and neither was the question.
`test_boundary_inventory`'s failures are set comparisons, and this candidate
had ENLARGED the sets: `source_boundary.py` does not exist at base and the four
identity columns do not exist at base, so nothing they contain can be
pre-existing. A failing test whose name and count are unchanged can be failing
about entirely new things, and mine was.

The rule this leaves behind is worth stating: a baseline failure is a
statement about the failure's CONTENTS, and attribution by name or count is not
attribution.

### Done: every candidate-introduced boundary is classified and probed [P1]

Thirty-four receiving entries and four persisted columns, each given the
treatment its own shape asks for rather than one blanket declaration.

**Ten real probes**, in a new `source_boundary_probes()` group registered in
`all_probes()`. Each drives the real public operation with one operand spoiled
and `refusing` requires the refusal to NAME the boundary's label, so a probe
stopped by an earlier precondition fails instead of passing quietly:
`check_disk_backed`'s workspace path, `filesystem_of`'s filesystem path,
`nominate_source`'s nominated directory, `source_mountpoint`'s inputs root,
`source_consumption`'s profile word, and the five origins of
`declared_profile`'s one declaration — the descriptor, its `consumption`, and
each of the three members the declaration must carry. The member drivers OMIT
the member rather than spoiling its value, because a present-but-wrong member
is refused by a policy rule one line later and a probe satisfied by that
refusal would be naming the wrong owner.

**Twenty-nine stated owners**, in three groups with three different reasons:

- the minted capabilities — `NominatedSource`, `SourceBoundary` and
  `WorkspaceCapacity` — whose members are never caller data because a caller
  cannot reach the constructor at all;
- the typed capabilities a caller hands BACK, each an exact type check against
  a class only this build mints, made before any member is read. A
  boundary-layer rule cannot express "this is the object I made", and identity
  is the whole point;
- this build's own diagnostic noun `what`, a literal at every call site, which
  reaches no decision and no durable record.

**One delegation.** `source_consumption`'s profile word is owned in `_profile`,
where `declared_profile`'s copy of the same word is already owned. Two owners
for one rule is how a Git-agnostic manager acquires a Git-aware exception, so
it is written once and the delegation says so.

**Four `NO_PROBE` declarations** for the identity columns, in the same words
and for the same reason `attempts.assignment_generation` already carries: they
are `count` columns in a STRICT table, so SQLite refuses the value a corruption
probe would have to write and the probe would be proving a boundary no writer
can drive. `test_every_unprobed_entry_is_a_real_owned_entry` holds each to
being a live, layer-owned entry, so the exemption cannot retire anything.

**Twelve witnesses**, because a stated owner is a claim until something
exercises it and `EveryStatedOwnerHasAWitness` enforces exactly that. Each new
`StatedRules` method drives the rule it names: the three constructors refuse a
caller that did not mint; composition and adoption refuse a plain mapping
carrying the same paths; a pinned identity refuses a single pair, a short pair
and a non-numeric pair; `boundary_mounts` refuses anything it did not compose;
the declared capacity is held to floor and ceiling; the pin proves its attempt
row before reading or writing an identity, and refuses a half or negative pair
with the row still unpinned; and the adapter's source delivery is refused where
the binds are composed.

The diagnostic-noun witness is STRUCTURAL rather than behavioural, and that is
deliberate: the claim is that no caller can put anything there, so it walks the
two modules' syntax and requires every `what=` argument to be a literal, a
composed literal, or the same noun forwarded. A behavioural probe would prove
the opposite of the claim by finding a way to supply one.

**These witnesses need real storage.** `BoundaryCase`'s root is `tempfile`'s,
which is a tmpfs on this host, and `check_disk_backed` correctly refuses a
workspace there — so the witnesses take a disk-backed root through the existing
`disk_roots` helper rather than failing for the environment.

### Measured

- `tests.manager.test_boundary_inventory`: 125 → 137 cases; the five failures
  remain and **contain no candidate-introduced entry**. Verified mechanically
  rather than by eye: the full failure text is scanned for every token this
  candidate introduces — `source_boundary`, `mount_table`, `mount_points`,
  `pin_boundary_identity`, `boundary_identity_of`, `source_delivery`, the four
  identity columns, the three constructors and each new operation — and the
  count is zero.
- `test_boundary_inventory` + `test_source_boundary` + `test_attempts` +
  `test_oci` + `test_dependencies` + `test_single_worker` + `test_workspaces`:
  948 run, the same five failures, 3 skips.
- **The canonical parallel gate**: 520 shards, **3,646 tests, 6 failures, 0
  errors, 3 skipped** — twelve more cases than the previous run, the same six
  failures, and now the five inventory ones are demonstrably about the
  pre-existing `operation_id`/`settled_at` gap alone. The sixth is still the
  authority catalog's own file registry, which does not list W29401's
  `test_work_label_exposure.py`.
- `git diff --check -- v12`: no output.

The serial real-Docker phase was not rerun: nothing in this correction touches
the recipe, the build context or any container, and the runner will not reach
that phase while the pre-existing parallel baseline fails.

### The superseding digest

`candidate-2026-09-05T07-51-05Z.manifest`, same 30 paths, same base `8f809a9`:

    content-digest sha256:cdd285d098dd67dc449be864a016f6cf3c539e9418a45de700e
                          ae7e39c140199

It **supersedes** `sha256:daf2bd4f…`, which bound the bytes the digest-bound
review examined and is retained as the evidence that review names. Reproduced
in place, as before: a second run over the unchanged tree gives byte-identical
output and the same aggregate.

### Candidate path set

**Still 30 paths.** This round changed exactly one:
`v12/python/tests/manager/test_boundary_inventory.py`, which was already in the
set. Its change is ADDITIVE — a new probe group, new registry members and new
witness methods — and it touches no existing assertion, fixture or case.

Every other path's bytes are unchanged, and that is MEASURED rather than
claimed: diffing the two manifests' content lines reports exactly one
differing line, `tests/manager/test_boundary_inventory.py`.

## 2026-09-05 — baton.claude — two witnesses that could not witness

Both [P1]s in `review-2026-09-05T07-57-56Z.md` are corrected. They are the same
mistake twice over, and it is worth naming as one: a witness that does not
reach the door it is registered against proves nothing, however carefully it is
written.

### Done: the diagnostic noun is bounded at each PUBLIC door [P1]

`workspaces.mount_table` and `mount_points` are EXPORTED operations, and my
stated owner said the noun was "a literal at every call site". That is a fact
about this package and says nothing about what an external caller may hand in
— and the reviewer showed the difference was real, not theoretical: with
`MOUNTINFO` pointed at a missing file, an object whose `__format__` raises
escaped both operations as `RuntimeError` instead of this build's closed
refusal, because the message interpolated it directly.

`check_disk_backed` already had the right shape. Both doors now `label_of`
their own noun at entry, and `mount_points` bounds its own even though it
forwards to `mount_table`, which bounds again: it is a separate exported
operation, a caller reaching it is at a boundary of its own, and `label_of` is
idempotent over a label it already produced.

**The stated reasons are superseded in place rather than edited quietly**, with
the old wording quoted and the reason it was wrong beside it.

**And the witness is behavioural now, which inverts what it used to do.** It
drove the modules' SYNTAX; it now drives all three doors on their own
documented refusal paths with five values no call site here would ever pass —
the hostile object whose `__format__`, `__str__` and `__repr__` all raise, a
lone surrogate that would become a `UnicodeEncodeError` the moment anything
logged it, a label far past the bound, an integer and `None` — and requires
this build's closed refusal from every one. Fifteen drives in all.

That inversion is the lesson: a source scan cannot establish what a caller may
supply, and the case that made that mistake was itself a check about ownership
of caller data.

### Done: the OCI witness reaches the constructor it names [P1]

The registered witness called `oci.run_vector(..., source_delivered=...)`,
which is a DIFFERENT entry at a different site. It never built an adapter, so
it could not have exercised `OciAdapter.__init__`'s rule, and the stated reason
it was registered against — "forwarded to `_source_mount`" — was itself wrong:
the constructor owns the operand directly, with its own exact type check and
its own posture rule, and then HOLDS it.

The reason now says that, and the witness proves both halves:

- three non-boundary values are refused at construction, each naming this
  build's own composed-and-proved capability;
- a real boundary is refused at construction on a posture that mounts nothing;
- and an adapter built with a CROSS-WIRED boundary — genuinely composed over
  one assignment's real roots while the adapter holds another's — is asserted
  to hold that exact object, and its `start` then refuses at "proved over the
  workspace", which is only reachable if the value the constructor held is the
  value the binds were composed from.

The last half needed care to avoid being vacuous: `start` refuses for a missing
launch document, for labels that disagree with the launch delivery's attempt,
for a workspace whose group is not the configured one, and for a malformed
engine listing — all BEFORE it reaches any vector. So the witness supplies a
real launch delivery, allocates the adapter's roots for the attempt its labels
name, and gives the engine an empty listing. Each of those was a wrong refusal
this case landed on first, and each is now excluded on purpose.

### Measured

- `tests.manager.test_boundary_inventory`: 137 cases, the five pre-existing
  failures, and **no candidate-introduced token in any of them** — the same
  mechanical scan as the previous round, still zero.
- `test_workspaces` + `test_source_boundary` + `test_oci` + `test_attempts` +
  `test_dependencies` + `test_secrets` + `test_text_sweep` +
  `test_single_worker` + `test_dogfood_operator` + `test_claude_agent`:
  1,353 run, all passing, 3 skips.
- **The canonical parallel gate**: 520 shards, **3,646 tests, 6 failures, 0
  errors, 3 skipped** — the same six, unchanged in contents.
- `git diff --check -- v12`: no output.

The serial real-Docker phase was not rerun: nothing here touches the recipe,
the build context or any container.

### The superseding digest

`candidate-2026-09-05T08-16-44Z.manifest`, same 30 paths, same base `8f809a9`:

    content-digest sha256:15291e091b85e5674dd074913eedd9a100e667dc1665fabd0a1
                          7af99c32c0a89

It supersedes `sha256:cdd285d0…`, which bound the bytes this review examined.
Reproduced in place, as before.

### Candidate path set

**Still 30 paths.** Two changed this round, and it is measured by diffing the
two manifests' content lines rather than asserted:
`v12/python/src/baton_v12/worker_manager/workspaces.py` — two `label_of` calls
and their reasons — and `v12/python/tests/manager/test_boundary_inventory.py`,
whose change is the two corrected witnesses and the two superseded stated
reasons. No existing assertion outside this Work's own two witnesses was
touched.
