# Progress

Not started. The defect was found during W71917 launch preparation after
W76207 closed satisfying.

## 2026-09-04 — `baton.claude` (`impl`), W81115 first implementation pass

Claimed at the reviewer-revalidated dossier. Every pinned decision revalidated
against the current tree before acting on it, and the reproduction reproduces:
`stage_state: running`, `engine_starts: 1`, `task_at_worker_path: false`,
`source_at_worker_path: false`, and the certified reader refusing for want of
the document. The correction is the approved one and is confined to
`tools/single_worker.py` and `DEPLOYMENT.md`.

### The contract moved, so the version did

`CONFIG_SCHEMA` is `baton.v12.single-worker-deployment/2` and carries one
required absolute `task_document`. There is deliberately no fallback: a `/1`
document names no task, and a deployment that started anyway would start the
certified worker over a root it refuses before doing any provider work — which
is the defect. A `/1` configuration is refused by the same equality test that
already read the schema.

### Read once, before anything exists to undo

`_task_bytes` runs inside static configuration validation — before Authority is
opened, before an offer, before an attempt or a workspace. It opens the path
`O_NOFOLLOW | O_CLOEXEC | O_NONBLOCK`, proves the OPENED OBJECT is regular with
`fstat`, reads at most the worker's own 1 MiB ceiling plus one, and holds the
exact bytes on the constructed deployment. `O_NONBLOCK` is there so that a FIFO
nobody has opened for writing answers instead of hanging the deployment before
it starts.

THE HELD BYTES, NEVER THE PATH, ARE WHAT IS DELIVERED. A change to the
configured file after construction cannot change what a later composition
publishes, and a case asserts exactly that by rewriting the configured path
between construction and composition.

THE MANIFEST IS WHAT THEY ARE PROVED AGAINST, which is the approved decision
this rests on: for this profile the task document IS the input manifest's
`human_contract` artifact, so its media type, width, byte count and digest are
already frozen evidence. The locator stays provenance and is never read as a
host path.

### The adjacent fact was real and is fixed with it

The manifest's one source destination is now required to be exactly `source`.
Without it, adding `task.json` would still have left this dossier's own
reachability acceptance false, because the workload's task contract fixes
`source_root` and the adapter copies exactly `/input/source`. It also reserves
the task name from a colliding source directory. W71917 still replaces the copy
with its ruled direct mount; what this pins is the path, which is the part the
worker fixes.

### Published before the freeze, proved on every restart

`_published_task` installs the held bytes as read-only `task.json` BEFORE the
source copy and before `compose_input_root` freezes the root at 0555 — after
which nothing can be added. It refuses rather than replaces when the name is
taken, creates the file unreadable and no-follow, reads the bytes back and
sets the mode ON THE DESCRIPTOR IT WROTE, and only then puts it at its final
name.

It is deliberately not `workspaces._write_read_only`. That is the private owner
of the two PROTOCOL documents, and publishing workload material through it
would mean making a generic Worker Manager operation public to carry workload
vocabulary — the boundary this Work is explicitly held to. What is different
here is also worth having: the bytes are compared before the document becomes
readable at all.

`_proved_task` re-proves the installed document whenever an already-composed
root is adopted. `read_input_root` reads exactly the two protocol documents —
that is the generic component's whole contract — so a matching manifest pair
says nothing about the workload material beside it, and inferring the task from
`input.json` would be this deployment concluding something the reader it called
never looked at.

### Verification

- `tests.tools.test_single_worker`: 63 tests, exit 0 (49 before this pass).
- The dossier reproduction now reports `task_at_worker_path: true`,
  `source_at_worker_path: true`, `configured_source_destination: source`, and
  `worker_task_read: accepted` — the certified worker's own reader accepting
  the document this deployment composed.
- Static negatives, all refusing with no claimed offer and an empty workspace
  storage: the superseded `/1` schema, a missing member, a missing file, a
  symlink, a directory, an oversized document, and each of the four
  human-contract relationships (media type, declared width, byte count,
  digest), plus a source destination the workload does not read.
- Composed root: exactly `assignment.json`, `input.json`, `source`,
  `task.json`; the task at mode 0444 inside a 0555 root with no staging name
  left; the engine's `/input` mount naming that exact root read-only.
- Attempt-root negatives: a foreign `task.json` planted before composition
  ends the stage `exceptional` with no runtime and one recorded preparation
  failure; a changed task in an adopted root is never repaired; an interrupted
  composition leaves a partial root the next process refuses.
- Restart: the adopted root is neither republished nor rewritten, the inode and
  mtime are unchanged, and no second runtime starts.
- RECEIVING END: the real `baton_worker` program, in this process, over the
  real framed transport, with the real `ClaudeAgent` behind the documented
  `main(agent=...)` seam and only the provider process injected, driven at the
  exact root `single_worker` composed. Its `work` request passes `_task` and
  reaches the provider seam, and the prompt carries the delivered task's own
  instructions. The two fixed names are asserted against the workload's own
  constants, because the image cannot import this package and this package
  cannot import the image.
- The three new positive cases were driven with the publication disabled and
  all three fail there, so they discriminate rather than merely pass.
- `tests/job_manager` discovery 210, and `test_attempts`, `test_oci`,
  `test_workspaces`, `test_claude_agent`, `test_worker_entry` 765: exit 0.
- `tests.manager.test_boundary_inventory`: the same five pre-existing
  failures, counts at 49/35/132 with no delta.
- Broad sweep `tests` discovery: 3548 tests, the same eight recorded failing
  identities and none new.

### State

Passing back for independent review. PLAN item 5 — resuming W71917 through the
corrected composition — remains blocked on that review and on W71917's own
approver. No version-control state was mutated.

## 2026-09-04 — `baton.claude` (`impl`), W81115 correction pass 1

Responding to `review-2026-09-04T00-56-36Z.md`. One P1 and one P2, both
corrected.

### P1 — the final transition clobbered

You are right, and the shape of the mistake is one worth naming: I put the
exclusivity on the STAGING name, where nothing was racing, and finished the act
with `os.replace`, which is defined to clobber. The `lexists` check that was
supposed to enforce "refused rather than replaced" was then only an early
answer to a question nothing later re-asked — the same two-moment error I
corrected twice in W76207, arriving here through a filesystem call instead of a
durable read.

`os.link(staged, place, follow_symlinks=False)` is the transition now: it
publishes the final name atomically or fails `EEXIST`, so there is no window
in which this operation can remove somebody else's document. On collision the
foreign target is untouched, only this operation's own staging name is
removed, and a typed `integrity/path` refusal travels out through the existing
preparation ending. `follow_symlinks=False` because a link left at the staging
name must be published as itself rather than resolved into a target this
operation never wrote.

ABOUT YOUR PRESERVED PROBE, said plainly rather than reported as a pass.
`reproduce_publish_collision.py` injects at `os.replace`, which this
composition no longer calls, so it now drives an ordinary uncontended
publication and its output says nothing about the race either way. The same
interval one operation later — injected at `os.link` — reports
`foreign_target_survived: True`, `held_target_replaced_it: False`, and only
`task.json` left in the root. The production-seam regression drives it through
a real reconcile.

### P2 — the matrix is completed

A FIFO joins the static cases, and it is the one that actually reaches the
`O_NONBLOCK` boundary: a directory refuses at the open, so the anti-hang rule
was asserted in prose and never executed. Nothing has the FIFO open for
writing, so an ordinary blocking open would hang the deployment before it
started.

The adopted-root case you asked for is added and is distinct from the existing
one: composition completed, the process stopped before the start, and the task
changed before the next process adopted the root. That root's protocol pair is
untouched, so `read_input_root` accepts it and the task proof is the only thing
between a worker and a document nobody delivered. The pre-existing case keeps
its own subject — a root mutated under an already-running runtime.

### Verification

- `tests.tools.test_single_worker`: 65 tests, exit 0, with the collision
  regression, the adopted-root regression and the FIFO case.
- BOTH new cases were driven against the uncorrected code first. With the
  rename seam restored, the production collision reports
  `foreign_target_survived: false`, `held_target_replaced_it: true`,
  `stage_state: running`, one engine start and no preparation failure — a
  worker started over a root whose task this deployment had overwritten. With
  the restart proof removed, the adopted-root case reports `running` where it
  requires `exceptional`, while the ordinary restart case still passes.
- The dossier reproduction still reports `worker_task_read: accepted` with both
  fixed paths present.
- `tests/job_manager` discovery 210 and the five relevant manager suites 765:
  exit 0. Boundary inventory unchanged at 49/35/132.
- Broad sweep `tests` discovery: 3550 tests, the same eight recorded failing
  identities and none new.

### State

Passing back for independent review. PLAN item 6 — resuming W71917 — stays
blocked on that review and on W71917's own approver. No version-control state
was mutated.

## 2026-09-04 — `baton.claude` (`impl`), W81115 correction pass 2

Responding to `review-2026-09-04T01-06-30Z.md`. One P1, and it is the same
defect I corrected last pass, one pathname earlier.

### P1 — the staging name was a second pathname, so it was a second race

I closed the descriptor that wrote and proved the bytes and then published from
a NAME. `os.link(staged, place, follow_symlinks=False)` does exactly what it
says: it links whatever that name denotes, and if a creator unlinked it and put
a symlink there in between, the symlink is what gets published — and then I
unlinked the staging name as though it still denoted my inode, and returned
success.

TWO REVIEWS, ONE DEFECT: a name proved at one moment and used at another. First
the final name across a rename, then the staging name across a link. I was
defending the interval rather than removing it, and defending it a third time
would have been the same bet again.

So the interval is gone. The document is created directly at its final name
with `O_CREAT | O_EXCL | O_NOFOLLOW` — which IS the no-clobber decision, since
an existing file, directory or symlink there fails `EEXIST` and nothing is
written — and the bytes, the readback and the mode all reach the descriptor
that creation returned. The proved descriptor and the published object are one
inode by construction, and there is no other name to substitute.

WHAT I GAVE UP, stated rather than glossed. The final name now exists,
unreadable at mode 0, while the document is still being written, where the
staged form made it appear complete or not at all. That property is real where
`workspaces._write_read_only` lives, because those documents go into a root a
container may already be mounting; here the write happens before the root is
frozen and before any runtime exists, so nothing can observe the incomplete
name — and what an interrupted composition leaves is refused twice over, by the
partial-root rule and by `_proved_task`'s mode check. Removing the second
pathname is worth more than atomic appearance is at this point in the
composition.

ABOUT YOUR PROBE, again plainly. `reproduce_staging_substitution.py` injects at
`os.link`, which no longer exists in this operation, so it now measures an
uncontended publication; its members all read correctly — not a symlink, held
bytes published — but that is not the race passing, it is the race having
nowhere left to happen. What I drove instead is your substitution through the
PRODUCTION seam with the staged-and-linked publication restored: `stage_state:
running`, one engine start, no preparation failure, `final_is_symlink: true`,
`foreign_bytes_published: true`. That is your finding at the level it matters.

### Verification

- `tests.tools.test_single_worker`: 67 tests, exit 0. The collision regression
  is re-aimed at the only seam this operation has left — the exclusive
  creation — and two cases join it: a link arriving at the final name is
  refused and never followed, and the published object is an ordinary
  single-linked 0444 file carrying exactly the held bytes.
- The substitution driven against the previous publication through the
  production seam reports the symlinked foreign task published, `running`, one
  start and no ending; against this one it is refused with one recorded
  preparation ending and no runtime.
- The dossier reproduction still reports `worker_task_read: accepted` with both
  fixed paths present.
- `tests/job_manager` discovery 210 and the five relevant manager suites 765:
  exit 0. Boundary inventory unchanged at 49/35/132.
- Broad sweep `tests` discovery: 3552 tests, the same eight recorded failing
  identities and none new.

### State

Passing back for independent review. PLAN item 7 — resuming W71917 — stays
blocked on that review and on W71917's own approver. No version-control state
was mutated.
