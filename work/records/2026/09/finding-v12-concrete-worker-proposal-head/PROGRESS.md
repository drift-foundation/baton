# Progress

## 2026-09-06 — baton.claude — the bounded plan, and a smaller Work than the finding assumed

Claimed W105575 and ran the planning checkpoint. Only this dossier's
`FINDING.md`, `PLAN.md` and `PROGRESS.md` were written, which is the whole of
what item 2 authorizes. State: **awaiting independent review and owner scope
acceptance**.

The revalidation changed the size of this Work and that is the main thing to
report. The finding is framed as if a real private head and durable object
transport had to be built. They exist. `create_line` materializes one
persistent line per Authority and Work; `GitCheckpointProfile` clones it
copy-safely, detaches it at the declared base, reads the real head and tree,
and retains the commit under `refs/baton/checkpoints/<line>/<revision>`;
`writer_boundary` mounts that line as the writer's `/output`; and
`test_checkpoint_profiles.test_real_git_keeps_an_old_checkpoint_after_the_line_
advances` already proves two successive candidate commits, two frozen
checkpoints and the older one still resolvable after the line advanced — with
real `git`, in tree, today.

What is missing is one act. `GitCheckpointProfile.freeze` refuses a dirty
worktree — "a checkpoint freezes a clean COMMITTED candidate" — and nothing
commits. In that existing test the commits are made by the test itself. In
production they belong to the concrete worker, and `claude_agent` instead
clones a second time into `/output/checkout`, copies that to `/output/candidate`
with `.git` skipped, and edits a tree that is not a repository at all.

So the pinned design is: stop cloning and copying, let the provider edit the
line worktree the manager already mounted, exclude the declared output through
`.git/info/exclude` so the worktree can be clean, commit with a closed argv, and
declare `proposal/objects.bundle` over the base→head range in place of the
removed `proposal/candidate/` tree. The declared output gets smaller, not
larger, which is what "no whole-candidate archive or copying ceremony" asks for.
Path set: `v12/worker/claude_agent.py` and its own test file. Nothing else.

Two decisions are for review rather than mine. The Git vectors are composed in
the worker because `Dockerfile.claude` copies only `source_profiles` into the
image, so a shared composer would cost a package and a Dockerfile change; if
review wants one composer the path set grows and that should be said out loud.
And the existing-test changes are enumerated in FINDING by class, because the
candidate root moves from `/output/candidate` to `/output` and the path assembly
moves with it. Their intent is unchanged and no refusal is weakened, but that
enumeration is the case-specific confirmation the repository rule requires and I
am not treating the planning checkpoint as blanket authority.

One substantial missing capability is reported rather than reached into.
`workspaces.line_assignment_workspace` never calls `adopt_workspace_group`, and
the line tree is created `0700` under the manager's uid while the runtime is
pinned to `--user 65532:65532`. The per-attempt workspace gets the configured
group and a group-writable mode; the persistent line does not. So the worker
cannot write the line it is mounted at. The worker half is still independently
implementable and provable — the new tests own a line at the test's own uid —
but the live end-to-end demonstration is blocked until the line is provisioned
for the runtime identity. That is a bounded `workspaces.py` correction needing
an owner decision on how the line tree is owned.

Also raised, as an observation only: `admission.resolved_account` cross-binds
the proposal against the checkpoint's line, digest, evidence and path set, but
never compares the proposal's `candidate_digest` against the checkpoint's
`head_object`. Once a real head exists those are one fact from two producers.
`integration/` is another owner's and was not edited.

Two mechanism details are unverified here and say so in FINDING: that
`.git/info/exclude` keeps `status --untracked-files=all` empty for the declared
output, and the exact bundle range spelling. This participant's deployment
policy hook refuses Git history and index mutations from its shell, including
in a throwaway temporary repository, so the probe did not run and no stronger
form of it was attempted. Both are proved by the planned cases at
implementation time and neither is load-bearing for the design.

## 2026-09-06 — baton.claude — plan revised against the independent review

Reclaimed W105575 after changes were requested and ran the dossier-only
correction. State: **awaiting independent re-review, then the explicitly
required owner scope acceptance.** No production or test file was touched.

Every correction in `review-2026-09-06T23-54-31Z.md` was re-checked against the
tree rather than taken on the reviewer's word, and every one held. Three of them
break the earlier design rather than refine it, so the revised section in
FINDING supersedes my first pinned design, claim, path set and test scope, and
says so explicitly; the superseded text stays where it is.

What the re-check found, in the order it changed my mind:

`freeze_checkpoint` passes the line's immutable `declared_base` to the profile
on EVERY revision, while `grant_writer` admits a correction only at the current
checkpoint and `validate(current=True)` requires the worktree to be at that
checkpoint's head. So round two genuinely starts at H1 with the publication
base still B, and my `HEAD == declared_base` entry check would have rejected
it. The fix is that B and the turn-entry head E are two facts: the claim's
`base` stays B so `source_base == target_revision` survives every round, and E
is proved by ancestry from B and used only as the commit's parent. Nothing is
asked of the task document or of any producer, because E is whatever the
manager's own grant left the line at.

`baton_worker.handle` writes `output.json` through a `.publishing` staging name
AFTER `agent.work` returns, so my declared-output exclusions left the real
checkpoint dirty and my positive test would have proved a freeze that cannot
happen. The revised proof runs the actual completion publication before the
freeze and before the next correction, and the reserved set now covers the
completion document, its staging name, the `result-*` namespace and the
declared outputs — written before the entry cleanliness check, with
tracked-path collisions and ignore-pattern metacharacters refused rather than
escaped and hoped about.

My in-place clone fallback was impossible: `assignment_workspace` creates
`workspace/result-<attempt-id>` before runtime start and `custody` refuses its
absence, so `/output` is never an empty clone destination. Withdrawn.

And the compatibility claim was wrong in the way that matters most: the
existing worker fixtures are GENERIC, and `dogfood_operator._derived` reads
`proposal/candidate/` to recompute the diff and rerun the verification outside
the container. Removing that tree for everyone would have broken a live reader.
So the workload is now SELECTED by a third profile word, `git-line`, and only
that row changes; `generic` and non-line `git` keep their behaviour, their
output and their result schema.

The best consequence of that last correction is that **the existing-test-change
request is withdrawn entirely.** It only existed because the candidate root was
going to move for everybody. It is not, so every new case is additive and I am
asking for no change to any existing assertion. The reviewer was also right
that my earlier enumeration was a proposal and not the case-specific
confirmation the repository rule means; I had claimed otherwise and that claim
is superseded.

Cost of the correction: one more production file. Selection has to live with
the other two profile words in `source_profiles/checkout.py`, because the
alternative is the worker inferring its own lifecycle from what it finds on
disk, which is what the review refused and what this codebase refuses on
principle. Path set is now `source_profiles/checkout.py` and
`worker/claude_agent.py`, plus two additive test files. Version-control command
composition stays in the worker, as the review allows.

Recorded the ledger gate the review could not: W103083 is blocked on W105706 at
event 105757, from the implementation route.

One further live-composition gap was confirmed while revising, and it belongs
to that same provider rather than here: under `line_assignment_workspace` the
workspace IS the line checkout, and nothing creates `result-<attempt-id>`
inside it, so `custody` would refuse an otherwise healthy line-driven attempt
for a second reason independent of permissions.

The unverified mechanism details are unchanged and now cover the `--no-verify`
and `cat-file` identity checks as well. The deployment policy hook still
refuses history and index mutations from this participant's shell, including in
a throwaway temporary repository; the probe did not run and no stronger form of
it was attempted.

## 2026-09-07 — baton.claude — the accepted scope, implemented

Claimed W105575 after owner acceptance and implemented the four accepted paths.
State: **awaiting independent candidate review.** All four inputs matched the
re-review's recorded digests before the first edit, so the accepted design was
revalidated against the exact bytes it was accepted over.

Changed, and nothing else:

- `v12/python/src/baton_v12/source_profiles/checkout.py` (+60 −19) — the
  `git-line` word, its empty plan, and the workspace as its source root.
- `v12/worker/claude_agent.py` (+706 −38) — the line branch.
- `v12/python/tests/manager/test_source_boundary.py` (+58 −0)
- `v12/python/tests/manager/test_claude_agent.py` (+485 −0)

**Both test files are strictly additive — 543 lines added, zero removed.** No
existing assertion or expected behaviour changed anywhere, which is the
condition the acceptance set and the one I most wanted to be able to state as a
measurement rather than an intention.

The amendments landed as accepted. Hooks are suppressed by
`core.hooksPath=/dev/null` on the commit vector rather than by `--no-verify`,
and a mutating `prepare-commit-msg` hook installed in the line is proved not to
run. The committed change is bound to the measured change completely: the exact
path set from `diff --name-status`, raw blob equality for added and modified
paths against the digests this adapter measured, ABSENCE for deletions, an
empty post-commit status as the supplementary gate, and a refusal for any path
carrying a content filter — with a deletion case and a real `tr a-z A-Z` clean
filter both covered.

Two things the implementation found that the plan had not:

The `HEAD == entry` check cannot live inside the commit path. A provider that
COMMITS its own work leaves a clean worktree, so a check reached only on the
way to committing never runs and that history is silently adopted and reported
as this adapter's. It is now `_unmoved`, called right after the turn is
measured and before anything is decided. The refusal case is what caught it.

And the exclusion writer must not create `.git`. It was creating the metadata
directory on the way to `info/exclude`, which turned "this workspace is not the
prepared line" into a confusing failure three commands later — and would have
had a worker quietly building the arrangement it was supposed to have been
handed. It now requires the repository and establishes only `info`.

Verification. `test_claude_agent` 123 tests, `test_source_boundary` 75,
`test_checkpoint_profiles`, `test_worker_entry`, `test_worker_image`,
`test_dogfood_operator` and `test_dependencies` — 733 tests together, all
passing. The full `python3 -m unittest discover -s tests -t .` run is 4431
tests with 10 failures and 1 error, and every one of them is pre-existing and
unrelated: three are Docker engine cases complaining that an earlier run's
containers and image tag survived it; four are `test_boundary_inventory`
entries naming `attempts.py` and `lanes.py`; one is `test_parallel_runner`
refusing the untracked `tests.integration.test_driver` and
`tests.job_manager.test_review_driver` baseline modules; and one is
`test_catalog` naming an authority file. None names a path this Work touched.

The bundle question the plan left open is settled by execution rather than by
argument: `git bundle create <file> <base>..HEAD` advertises `HEAD`, and a
recipient holding only the base — a fresh clone that never saw the producer
worktree — verifies the bundle, fetches `HEAD:refs/heads/incoming`, resolves
the exact claimed head and reads the candidate bytes back. The second
correction round's cumulative range resolves the same way for a recipient that
never saw round one. No worker-owned ref was needed.

Real completion publication is in the positive proof: `baton_worker.
publish_completion` is called with `OUTPUT_ROOT` at the line, and
`GitCheckpointProfile.freeze` then succeeds over that same line and returns the
head the worker claimed. Two rounds advance one line against an unchanged base,
the second commit's parent is the first, and revision one stays resolvable from
its retained ref.

## 2026-09-07 — baton.claude — three reproduced defects, corrected

Reclaimed W105575 after `review-2026-09-07T01-06-23Z.md`. All three probes in
`evidence/review_regressions.py` reproduced against my candidate before I
changed anything, and all three were real. State: **awaiting independent
review**; still the same four accepted paths, and both test files still
strictly additive — now 576 and 58 lines added, zero removed.

**P1, the ignored dependency, was the serious one and my reasoning was wrong
rather than incomplete.** I compared the committed change against the measured
tree in one direction and called that complete equality. It cannot be: a path
the repository IGNORES is in no status, no staging and no diff, so it is in
neither account and a check over the change set can never see it. The probe's
turn verifies successfully BECAUSE the file is on disk and commits a tree
without it, so the published head resolves to something nobody verified.

The fix is not another pass over the change set. `_representable` now takes the
equality that actually matters to a recipient — the committed tree, restricted
to candidate material, IS the measured tree — using `ls-tree -r` rather than a
diff, because the missing file never changed anything and a diff is the wrong
question. The measured side comes from the filesystem walk, which knows nothing
about Git and cannot be talked out of seeing a file. Set difference in both
directions, and the tree entry's MODE is checked there too, which puts the
walk's own type boundary on the side a recipient resolves. An unrepresentable
candidate refuses; force-adding would be this adapter overriding a repository's
own rules about what belongs in it.

**P1, index hooks.** `core.hooksPath` was on the commit vector only, and
`post-index-change` fires on an index WRITE, so staging reached a hook. It is
now composed by `_git` onto every vector — one prefix rather than a policy
applied per call site, because a per-site rule gains a gap the moment somebody
adds a site.

**P2, the stale bundle.** On a persistent line the declared output directory
survives the turn that wrote it, so a no-op correction left the previous
attempt's `objects.bundle` in this turn's declared output — objects for a head
this turn does not claim, ready to be collected and sealed as though it did.
The three text members are rewritten unconditionally and were never exposed;
the bundle is the one member whose absence is meaningful, so its absence is now
made rather than assumed. `_discarded` removes exactly that one worker-owned
name, by name and through a directory descriptor. Sealed custody and retained
checkpoint refs are untouched, and one of the new cases proves the line and its
revision-one ref survive the no-op round.

Regressions added for all three, plus a later-turn-replaces-earlier-bundle case
and a both-directions tree equality case.

Verification. `evidence/review_regressions.py` re-run unchanged: 3 tests, exit
0, output preserved at
`evidence/review-regressions-after-correction-2026-09-07.txt`. Focused suites —
worker, source-boundary, checkpoint-profile, worker-entry, worker-image,
dogfood-operator, dependencies — 740 tests, all passing. The profile-consuming
suites `test_coordinator`, `test_review_cycles` and `test_review_driver` are
273 tests, all passing, run because this Work adds a word to
`source_profiles.PROFILES`.

The baseline classification the review asked for is now evidence rather than a
description: `evidence/baseline-failures-2026-09-07.md` carries the exact
commands, all eleven ids, the re-executed subjects for the seven that need no
engine, and the working-tree provenance of every path those subjects name. No
second discovery campaign was run. It also states what it does not claim: it is
not a reverted-tree comparison, because obtaining the pre-candidate bytes would
require mutating Git state this participant may not touch.

## 2026-09-07 — baton.claude — the byte half, and the pattern behind three rounds

Reclaimed after `review-2026-09-07T01-16-13Z.md`. The probe reproduced: an
index entry marked `assume-unchanged` leaves the edit invisible to status and
to every diff, so `preflight.py` is in BOTH path-set accounts, absent from the
reported change, and its committed blob stays the original — while the real
verification that returned 0 read the new bytes. Corrected in the same four
paths; both test files still additive, now 610 and 58 lines added, zero removed.

**The correction worth recording is not the case, it is the pattern.** Three
review rounds have now caught one version of the same mistake, and each time I
fixed the instance rather than the premise. Round one: compare the change set
against the measured tree. Round two: also compare path sets, because an
ignored addition is in neither. Round three: path sets are equal and the bytes
still differ. Every one of those proofs asked Git WHICH paths mattered, and so
inherited every reason Git might answer wrongly — an ignore rule, an index
flag, and a content filter are three such reasons and there is no argument that
they are the last three.

So `_identical_bytes` does not ask. It takes the whole measured tree, one path
at a time, and asks Git only for the bytes it stored: one `cat-file --batch -Z`
over every measured path, each committed blob compared against the digest this
adapter read from the worktree through no-follow descriptors. The change set is
still parsed, but only for what it is actually authoritative about — the
add/modify/delete marks, deletion absence, and refusing a rename or a type
change. Path-set equality and the tree-entry mode check stay where they are.
The batch is one process and is bounded by the ceiling `_checked_tree` already
applies to the candidate.

Regressions added: the `assume-unchanged` case refusing by name and bytes, and
a case proving an UNCHANGED file's bytes are compared too — `preflight.py`
never appears in `changed_paths` and is still held against the commit.

Verification. Both reviewer probes re-run unchanged and pass:
`review_tracked_bytes.py` 1 test exit 0, `review_regressions.py` 3 tests exit
0, output preserved at
`evidence/review-tracked-bytes-after-correction-2026-09-07.txt` and
`evidence/review-regressions-after-correction-2026-09-07.txt`. The relevant
sweep is now 1015 tests — worker, source-boundary, checkpoint-profile,
worker-entry, worker-image, dogfood-operator, dependencies, coordinator,
review-cycles and review-driver — all passing. No new discovery campaign, and
the baseline note from the previous round stands unchanged.
