# Deliver the production task document to the v12 worker

Ledger Work: W81115

Follow-up to W76207.

## Observed — 2026-09-03

`tools.single_worker._input` copies the configured `input_source` only below
the input manifest's one declared source destination, then
`compose_input_root` writes only `/input/input.json` and
`/input/assignment.json`. The production OCI adapter mounts that composed root
at `/input`.

The currently certified Claude worker calls `claude_agent._task()` before it
does any provider work. That operation requires the frozen workload document
at exactly `/input/task.json`, while the source tree is fixed separately at
`/input/source`. A manifest source destination cannot be `.` and the
single-worker composition has no other task-delivery operation. Consequently
the reviewed W76207 production composition can start the image but cannot give
that image the task document it requires; W71917 would fail before the agent
could implement anything.

This was not exercised by W76207's production-composition tests because they
replace the OCI engine boundary and prove the start vector rather than running
the real worker entry through its first `work` request.

## Proposed correction

Keep source and workload instruction as separate immutable inputs. Extend the
closed single-worker deployment document with one absolute task-document path.
Before freezing the input root, open that path no-follow as a bounded ordinary
file, prove its byte count and content digest against the input manifest's
`human_contract`, and install those exact bytes as read-only
`/input/task.json`. The worker remains the owner of the task document's
provider-specific schema; the host composition treats it as digest-bound
content and does not import the worker adapter's parser.

The task is configuration-file content, never an environment payload. This
correction does not restore dogfood, copy a candidate archive, redesign the
source/workspace boundary owned by W71917, or add general attachment handling.

## Acceptance

- The public `tools.single_worker:factory` can launch the certified Claude
  image with both protocol manifests, `/input/task.json`, and `/input/source`
  present at their fixed locations.
- Task bytes are bounded, opened no-follow, verified against the frozen human
  contract before any offer, and copied exactly once before the input root is
  frozen.
- Missing, changed, linked, oversized, colliding, or mismatched task material
  refuses before runtime start and creates no partial observable input root.
- A real worker-entry fixture reaches the task rather than failing on its
  absence. Existing restart and preparation-settlement behavior remains
  unchanged.

## Test-change authority

This Work authorizes additive tests and bounded edits to existing tests under
`v12/python/tests/tools/` for the single-worker configuration, task delivery,
refusal cases, and one real worker-entry reachability fixture. Deleting or
weakening unrelated expectations is excluded.

## Reviewer revalidation — 2026-09-04

### Confirmed: the running projection is not evidence of a runnable worker

The reproduction at
`evidence/reproduce_missing_worker_inputs.py` drives the public production
composition with the existing recording OCI engine, then asks the certified
Claude adapter's own task reader about the root the engine was given. It
reports:

```text
stage_state: running
engine_starts: 1
task_at_worker_path: false
worker_task_read: this assignment has no readable .../inputs/task.json
```

This confirms the reported defect. `single_worker._input` copies only the one
configured source tree and calls `compose_input_root`; that owner writes only
`input.json` and `assignment.json`. `OciAdapter` mounts the resulting directory
at `/input`, and `claude_agent._task` opens `/input/task.json` before it invokes
the provider. No later operation can make the missing document appear.

### Confirmed: no existing public operation owns this file delivery

Repository-wide call-site review found no public task-delivery operation.
`workspaces.copied_manifest` is a bounded directory-tree copier and cannot
publish one file at the sibling workload path. `compose_input_root` owns the
two protocol manifests and freezes the completed root; teaching it a Claude
task would put workload vocabulary in the generic Worker Manager.

The old `dogfood_operator.frozen_task` and `_copied_task` are not a reusable
owner. They are private operations of the supervised dogfood deployment, open
the task with ordinary `open` (following a final symlink), parse its
provider-specific schema on the host, and reserialize the object rather than
copying the exact bytes. Importing them would restore the retired dogfood
composition and would not satisfy this Work's no-follow, exact-content
boundary.

### Confirmed adjacent fact: the production profile must also bind the fixed source path

The same reproduction reports
`configured_source_destination: workspace/source` and
`source_at_worker_path: false`. That value comes from the generic conformance
fixture, not from a production Claude profile. The public factory currently
accepts any sole source destination, while the certified Claude task contract
fixes `source_root` to `source` and copies `/input/source`.

This does not enlarge W81115 into W71917's new direct-mount design. It does mean
the closed bootstrap profile and its positive fixture must require the current
copied source destination to be exactly `source`; otherwise adding
`task.json` still leaves the very reachability acceptance in this dossier
false. That check also reserves `task.json` from a source-directory collision.
W71917 remains responsible for replacing the copied source path with its ruled
direct read-only mount after this bootstrap can execute it.

## Revised proposal — 2026-09-04

This supersedes the unqualified part of the initial proposal that says any
configured task can be checked against `input_manifest.human_contract`. The
relationship is valid only if this production profile explicitly defines the
task document itself as that manifest's human-contract artifact. Existing
dogfood examples do not: they point `human_contract` at a Markdown dossier and
carry a separate generated `task.json`, so comparing those two would correctly
fail every time.

For this production profile, make the relationship explicit and closed:

- Supersede `baton.v12.single-worker-deployment/1` with schema `/2`; adding a
  required member to a closed, version-named document is a new contract, not a
  compatible interpretation of `/1`. There is no fallback. Add one absolute
  `task_document` path.
- Require the input manifest's `human_contract` to describe this exact task
  artifact: `media_type` is `application/json`, its `bytes` is no greater than
  the worker's 1 MiB read ceiling, and its byte count and SHA-256 digest equal
  the held task bytes. The artifact locator remains provenance and is not
  interpreted as a host path; `task_document` names the local materialization.
- During static configuration validation, before Authority is opened and
  before an offer exists, open `task_document` once with `O_NOFOLLOW`,
  `O_CLOEXEC`, and `O_NONBLOCK`; prove with `fstat` that the opened object is a
  regular file; read at most the fixed ceiling plus one; and hold those exact
  bytes in the constructed deployment. Missing, linked, non-regular,
  oversized, byte-count-mismatched, and digest-mismatched material refuses at
  this point. Do not import or duplicate `claude_agent`'s JSON/schema parser;
  that workload remains the receiving-end owner.
- On an empty attempt input root, atomically publish the held bytes as the
  ordinary read-only file `task.json`, before the source copy and before
  `compose_input_root` freezes the tree. Use exclusive/no-follow creation and
  verify the final file from its descriptor; never reopen the configured
  source path. A change to that path after construction therefore cannot
  change what this deployment delivers.
- On restart, accepting an already-composed root requires proving the existing
  `task.json` is a no-follow ordinary file with the exact held bytes, byte
  count, digest, and read-only mode, in addition to the existing manifest-pair
  comparison. Do not infer task integrity merely from `input.json`, because
  the generic manifest reader deliberately reads only its two protocol
  documents.
- Keep W76207's partial-root rule. A process death after publishing any
  workload material but before the protocol pair is frozen leaves a partial
  root that the next process refuses and records as one preparation ending; it
  is never repaired in place. Static task failures happen before allocation,
  so they create no attempt root at all.

The implementation boundary is `tools/single_worker.py`, its deployment
documentation, and the already-authorized focused tests. No worker-control
schema, generic workspace operation, Claude task parser, dogfood operator, or
W71917 source/workspace implementation is changed.

## Verification matrix for implementation

- Positive composition: exact task bytes, mode `0444`, fixed `task.json` and
  `source` paths, frozen input root, and an otherwise unchanged start vector.
- Static negatives before Authority/offer/root creation: missing final name,
  symlink, directory/FIFO, greater than 1 MiB, manifest byte-count mismatch,
  digest mismatch, non-JSON media type, and a source destination other than
  `source`.
- Attempt-root negatives: a pre-existing `task.json`, a changed task in an
  already-composed root, and an interrupted task/source composition all refuse
  without repair, runtime start, or repeated polling.
- Restart: every existing W76207 checkpoint remains green, one task is
  published, and no restart rewrites it or starts a duplicate runtime.
- Receiving-end reachability: reuse the real in-process `baton_worker` framing
  fixture with `ClaudeAgent` and an injected process runner, pointed at the
  root produced by `single_worker`; its `work` request must pass `_task` and
  reach the provider seam. A direct call to a host-side parser alone is not
  sufficient, and a live provider credential or Docker daemon is not needed.

Baseline at review: all 49 existing `tests.tools.test_single_worker` tests
pass. The reproduction above fails at the intended worker task read while the
Job projection is already `running`.

## Approved correction — 2026-09-03

Slawomir approved both linked profile decisions in the revised proposal:

- supersede closed single-worker deployment schema `/1` with `/2`, carrying
  one absolute `task_document` path whose exact held JSON bytes are the input
  manifest's `human_contract` artifact and are delivered read-only at
  `/input/task.json`; and
- bind this certified Claude bootstrap profile's current copied source
  destination to `source`, producing the worker's fixed `/input/source` path.

Implement the bounded validation, publication, restart proof and receiving-end
fixture exactly as reviewed. This approval does not extend into generic Worker
Manager vocabulary, dogfood composition, or W71917's direct source/workspace
design.

## Independent implementation review — 2026-09-04T00:56:36Z

### Confirmed: the ordinary path now reaches the certified worker

The focused 63-test single-worker suite passes, the dossier reproduction now
reports `accepted` with both fixed worker paths present, and the receiving-end
case drives the real framed `baton_worker` entry and `ClaudeAgent` to its
injected provider seam. Static validation holds exact no-follow ordinary bytes
against the human-contract artifact, composition publishes those held bytes,
and restart proof does not infer task integrity from the protocol pair.

### P1: final-name publication can replace a racing foreign task

`tools/single_worker.py::_published_task` checks `lexists(task.json)`, creates
and proves `task.json.composing` exclusively, closes it, and then calls
`os.replace(staged, place)`. The exclusivity therefore protects only the
staging name. A foreign `task.json` created after the initial check and before
the rename is silently removed by `os.replace`; publication succeeds with the
held task in its place. That contradicts the approved no-replacement rule and
the acceptance condition that colliding task material refuses before runtime
start.

`evidence/reproduce_publish_collision.py` deterministically creates the
foreign final name at the rename boundary. The reviewed implementation reports:

```text
{'refused': None, 'foreign_target_survived': False, 'held_target_replaced_it': True}
```

The final-name transition must itself be no-clobber and atomic. A collision at
that transition must preserve the foreign bytes, remove only this operation's
staging name, become a typed `ContractRefusal` that the existing preparation
settlement records, and never start the runtime. Add a deterministic regression
at this exact check/publish interval; a pre-existing target before the initial
check does not exercise it.

### P2: two promised negative boundaries are not exercised

The static non-regular matrix tests a directory but not the specifically
recorded FIFO case, so it does not execute the `O_NONBLOCK` protection that
prevents static validation from hanging. The changed-task test mutates a task
only after the runtime is already running and correctly leaves that runtime
alone; despite its name, it does not exercise restart adoption of a fully
composed but not-yet-started root. Add the FIFO case and a stopped-after-input,
mutated-before-start restart case that proves one exceptional preparation
ending, no repair, and no runtime start.

## Correction — 2026-09-04, review `review-2026-09-04T00-56-36Z.md`

### [P1] The final transition publishes or refuses; it never replaces

**Observed.** `_published_task` guarded the STAGING name with `O_EXCL` and
finished with `os.replace`, which clobbers. The separate `lexists` check on the
final name was therefore only an early answer, and a creator that won the
interval between it and the rename had its document silently replaced —
violating the pinned rule that a task this composition did not write is
refused rather than replaced. The reviewer's probe at
`evidence/reproduce_publish_collision.py` recorded
`foreign_target_survived: False`, `held_target_replaced_it: True`. Driven at
the production seam with the same rename in place, the stage went on to
`running` with one engine start and no recorded ending — a worker started over
a root whose workload document this deployment had overwritten.

**Correction.** The final transition is `os.link(staged, place,
follow_symlinks=False)`: it creates the final name atomically or fails
`EEXIST`, so there is no window in which this operation can remove somebody
else's document. On collision the foreign target is left exactly as it is,
only this operation's own staging name is removed, and a typed `integrity/path`
refusal travels out through the existing preparation ending — so the stage is
recorded exceptional and no runtime starts. `follow_symlinks=False` because a
link left at the staging name must be published as itself rather than resolved
into a target this operation never wrote. The `lexists` check stays as what it
always was: the cheap early answer, not the decision.

**Note on the preserved probe.** `reproduce_publish_collision.py` injects at
`os.replace`, which this composition no longer calls, so it now exercises an
ordinary uncontended publication and its output says nothing about the race.
The same interval one operation later — injected at `os.link` — reports
`foreign_target_survived: True`, `held_target_replaced_it: False`, with only
`task.json` left in the root.

### [P1, 2026-09-04 review `review-2026-09-04T01-06-30Z.md`] The second pathname is removed rather than defended

**Observed.** The no-clobber link corrected the transition and left the STAGING
NAME as a mutable pathname between the proof and the publication. The
descriptor that wrote and proved the bytes was closed, and the final
publication was then made from that name — so a creator that unlinked it and
put a symlink there had the symlink itself hard-linked at `task.json`, the
staging name unlinked as though it still denoted this operation's inode, and
success returned. The reviewer's probe at
`evidence/reproduce_staging_substitution.py` recorded `final_is_symlink: True`,
`foreign_bytes_published: True`. Driven through the production seam with that
publication in place, the stage went on to `running` with one engine start and
no recorded ending: production froze and started over task material this
composition neither held nor proved.

**Both defects are one defect.** A name proved at one moment and used at
another — first the final name across a rename, then the staging name across a
link. Defending that interval a third time would be the same bet again.

**Correction: there is no second pathname.** The document is created directly
at its final name with `O_CREAT | O_EXCL | O_NOFOLLOW`, which IS the no-clobber
decision — an existing file, directory or symlink at that name fails `EEXIST`
and nothing is written — and every act after it is on the descriptor that
creation returned: the bytes, the readback, and the mode. The proved descriptor
and the published object are one inode by construction, and there is no other
name for anything to substitute. A failure before the mode is set unlinks the
name this operation exclusively created, which is its own.

**What is given up, and why it is worth it.** The final name now exists,
unreadable at mode 0, while the document is still being written; the staged
form made the name appear complete or not at all. That property is real where
`workspaces._write_read_only` lives, because those documents are composed into
a root a container may already be mounting. Here the write happens before the
root is frozen and before any runtime exists, so nothing can observe the
incomplete name — and what an interrupted composition leaves is refused twice
over, by the partial-root rule above and by `_proved_task`'s mode check.

### [P2] The negative matrix is completed

- A FIFO joins the static cases. A directory refuses at the open, so it never
  reached the boundary `O_NONBLOCK` exists for: nothing has the FIFO open for
  writing, and an ordinary blocking open would hang the deployment before it
  started rather than refusing it.
- The adopted-root case that was missing is added: composition completed, the
  process stopped before the start, and the task changed before the next
  process adopted the root. `read_input_root` accepts that root — its protocol
  pair is untouched — so the task proof is the only thing between a worker and
  a document nobody delivered. It records one exceptional preparation ending,
  starts no runtime, and repairs nothing. The pre-existing changed-task case
  keeps its own subject: a root mutated under an already-running runtime.

## Independent correction review — 2026-09-04T01:06:30Z

### Confirmed: the requested final-target and negative cases are corrected

The focused suite now passes 65 tests. A final `task.json` created at the
publication call survives, the stage records one exceptional preparation
ending, and no runtime starts. The FIFO static case and the fully-composed,
stopped-before-start task mutation case also exercise the two missing matrix
boundaries. The receiving-end reproduction remains accepted.

### P1: the proved staging inode is no longer bound to the published name

The correction closes and discards the descriptor that wrote and proved
`task.json.composing` before calling `os.link` by pathname. A concurrent
creator can therefore unlink that staging name and replace it after the proof
but before the link. `follow_symlinks=False` does not refuse that replacement:
it hard-links the replacement symlink itself at `task.json`. The helper then
unlinks the staging name and returns success without proving what the final
name denotes. Composition can consequently freeze and start over foreign task
bytes despite the exact held-byte and no-follow guarantees.

`evidence/reproduce_staging_substitution.py` deterministically replaces the
proved staging name with a symlink at the link boundary. The reviewed
correction reports:

```text
{'refused': None, 'final_is_symlink': True, 'foreign_bytes_published': True, 'held_bytes_published': False}
```

The publication decision must remain bound to the descriptor/inode that was
written and proved; a mutable staging pathname cannot become the authority
after that descriptor is closed. A staging substitution must be impossible or
must yield a typed preparation refusal before final publication, without
unlinking the replacement entry as though it still belonged to this
operation. Add a deterministic regression at this exact proved-descriptor /
final-publication interval and prove no foreign or linked object reaches
`task.json`, no runtime starts, and the preparation ending is recorded.

## Approver scope disposition — 2026-09-04

The corrected implementation removed the staging pathname and creates
`task.json` directly with `O_CREAT | O_EXCL | O_NOFOLLOW`, then writes, reads
back, and changes the mode through that one descriptor. The focused suite now
passes 67 tests, the receiving-end reproduction reaches the provider seam,
the relevant 765-test manager slice passes, and the broad sweep has no new
failing identity.

Two fresh Codex-backed review contexts subsequently ended with the provider's
`cyber_policy` refusal before they could publish a verdict. The last context
surfaced one question before that refusal: a same-uid host process could unlink
and replace the final directory entry while this process continued proving its
open descriptor.

Slawomir ruled that question outside this Work's acceptance boundary. This is
the exact trust-model decision already recorded by W34768/M34768: the Worker
Manager, its host uid, its private state root, and the Docker daemon are
trusted; v12 does not defend this pass against a malicious same-uid host
process and does not add inode pinning, signed input, or another brokered
publication mechanism. An ordinary competing composition does not unlink or
replace the entry: it encounters the non-empty/partial root or loses the
exclusive final-name creation and refuses. The worker cannot observe the
incomplete document because composition precedes runtime start and the
finished root is mounted read-only.

Accordingly, the provider refusal is not a product-review finding and the
same-uid replacement scenario does not reopen implementation. The accepted
boundary remains accidental manager corruption and ordinary concurrent
composition, with partial-root refusal, exclusive no-clobber creation,
restart re-proof, and read-only worker delivery. Protection from a malicious
trusted-host peer is explicitly not claimed.
