# Deliver a real private proposal head and durable objects

Ledger Work: W105575. Created 2026-09-06 by baton.prompt for Slawomir.

## Confirmed gap and approved direction

The concrete worker edits a copied tree without `.git` and returns files and a
patch. Publication requires a real proposal commit identity and durable objects
available after producer exit. Neither a tree digest nor unchanged base suffices.

Independent evidence:
`work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/finding-standalone-stage-composition/findings/finding-proposal-manifest-producer/review-2026-09-06T18-49-39Z.md`.
Existing product authority: the 2026-09-01 superseding ruling and review-cycle
clarification in `work/records/2026/09/finding-v12-proposal-import-base-closure/FINDING.md`,
and the 2026-09-06 Git-agnostic integration clarification in
`work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/finding-serialized-integration/FINDING.md`.

Slawomir approved separate bounded concrete-worker output planning, then
implementation, on 2026-09-06. This is a first-demonstration prerequisite, not
optional hardening. baton.claude owns the boundary.

## First checkpoint: exact plan before implementation

Revalidate the worker, persistent private-line lifecycle and runtime instructions.
Pin the smallest exact production path set, worker-owned metadata claim and
bounded test-change scope before production edits. Hand the plan to independent
review and then owner scope approval. Do not expand the manifest composer's old
five-path authorization silently into a runtime redesign.

Acceptance must show a real private head, declared durable object output and
independent resolution of that head and declared base after producer exit.
Review/correction continues the same private history. Prefer existing persistent
workspace/output arrangements; do not introduce another whole-candidate archive
or copying ceremony. Explain the minimal concrete output mechanism in the plan.
Git interpretation belongs in the instructed runtime, never generic Worker
Manager or integration coordinator. No canonical checkout/index/history mutations
by host agents are granted.

Publish the worker-owned claim shape for the later composer. Never mint manager
custody identities or measured result facts in that claim. The sealing repair is
a parallel provider: do not edit `worker_manager/sealing.py` or its sealing tests.
The composer waits for this provider's acceptance; concrete-worker path ownership
is serial across these jobs, not concurrent.

Keep the delivery a small happy-path proof with focused failures, not a complete
Git backend, archive subsystem or exhaustive recovery campaign. Report any further
substantial missing capability as a bounded prerequisite before expanding.

## Revalidation and pinned plan — 2026-09-06 — baton.claude

PLAN items 1 and 2. Read before writing anything: `review_cycles.py`,
`workspaces.py`, `checkpoint_profiles.py`, `source_profiles/checkout.py`,
`source_boundary.py`, `oci.py`'s runtime posture, `sealing.py`,
`job_manager/review_driver.py`, `integration/admission.py`, `worker/
claude_agent.py`, `worker/baton_worker.py`, `worker/Dockerfile.claude`,
`tools/single_worker.py`, `tools/dogfood_operator.py`, and the tests
`test_checkpoint_profiles.py`, `test_review_cycles.py`, `test_claude_agent.py`.

**The gap statement above needs one correction, and it changes the size of
this Work.** The finding says publication "requires a real proposal commit
identity and durable objects available after producer exit", which is right,
and implies this Work must build that capability, which is mostly wrong. Almost
all of it already exists and is accepted. What is missing is one act.

### Confirmed — the private line, the real head and the durable objects already exist

- `review_cycles.create_line` materializes ONE persistent line per Authority
  and Work at `<workspace storage>/.baton-review-lines/<line_id>/checkout`,
  through an injected profile. `grant_writer` attaches exactly one
  generation-fenced writer; a correction round attaches again to the SAME line
  by naming its current checkpoint. `job_manager/review_driver.
  prepare_implementation` is the accepted caller and says so in terms: "NO
  SOURCE IS CLONED HERE AND NONE IS CLONED LATER."
- `checkpoint_profiles.GitCheckpointProfile` is the concrete Git profile. Its
  `materialize` clones the nominated source copy-safely and detaches the
  worktree at the declared base; its `freeze` reads the real `HEAD` and tree,
  computes the reviewed path set from `git diff <base>..<head>`, and retains
  the commit under `refs/baton/checkpoints/<line_id>/<revision>` with
  `update-ref`; its `validate` re-proves that ref, tree and path set later.
- `test_checkpoint_profiles.test_real_git_keeps_an_old_checkpoint_after_the_
  line_advances` already demonstrates the whole property against REAL `git`:
  one line, two successive candidate commits, two frozen checkpoints with
  different heads, and revision 1 still resolvable from its retained ref after
  the line advanced to revision 2. That is "a real private head, durable
  objects after the producer is gone, and the same private history across
  corrections" — proved in-tree today.
- `review_cycles.writer_boundary` mounts that line as the writer attempt's
  WRITABLE workspace, and `source_boundary.WORKSPACE_TARGET` is `/output`. So
  under the accepted lifecycle the concrete worker's `/output` IS the private
  line worktree, already a repository, already detached at the declared base.

### Confirmed — the one missing act

`GitCheckpointProfile.freeze` refuses a dirty worktree: "a checkpoint freezes a
clean COMMITTED candidate". The only thing standing between the accepted
lifecycle and a real proposal head is that **nothing commits**. In
`test_checkpoint_profiles` the commits are made by the test itself; in
production that act belongs to the concrete worker, and `claude_agent` does not
perform it. Instead it re-does work the line already did and then works
somewhere the line cannot see:

- `work` calls `_checkout`, which runs `source_profiles.checkout_plan` and
  clones `/input/source` into `/output/checkout` — a second clone INSIDE the
  line worktree;
- `_copy_tree` copies that checkout to `/output/candidate` while skipping
  `.git`, so the tree the provider edits is not a repository at all;
- `_publish` writes `proposal/{candidate/, change.patch, verification.txt,
  result.json}`; and
- nothing ever commits, so `freeze` would refuse on the untracked
  `checkout/`, `candidate/` and `proposal/` trees even if it were reached.

**Therefore this Work is not a Git backend. It is: make the concrete worker
work in the line worktree it is already mounted at, commit, and declare the
objects.** Recorded here because the finding's own framing invited a much
larger delivery, and a larger delivery is not justified.

### Pinned design — Proposed, for review and owner approval

1. **The candidate is the mounted worktree.** Under the `git` source profile
   the worker stops cloning and stops copying: `/output` is the candidate. It
   verifies rather than materializes — `rev-parse --verify HEAD` equals the
   task's `declared_base`, and `status --porcelain=v1 -z
   --untracked-files=all` is empty — and refuses otherwise.
   For a workspace that is NOT yet a repository the worker materializes it
   once, in place, with the accepted `clone_vector`/`detach_vector`/
   `verify_vector`. That branch is resumption, not format inference, and it is
   the same branch `GitCheckpointProfile.materialize` already makes on
   `os.path.lexists(repository)`. It keeps the existing non-line driver
   (`tools/single_worker.py`) working unchanged, which is why no task-document
   member and no new profile word is proposed.
2. **The declared output is excluded from the line.** Before the provider runs,
   the worker writes each declared output path into `.git/info/exclude`. This
   is required for correctness, not tidiness: the declared output is written
   inside the workspace by contract, and without the exclusion the worktree is
   permanently dirty and `freeze` refuses. `.git/info/exclude` is repository-
   local and never committed, so the proposal bytes never enter the candidate.
3. **The worker commits.** After the provider turn and the existing tree/byte
   safety checks, `git add -A` then one commit with a closed argv:
   `-c user.name=<constant> -c user.email=<constant>` (the container has no Git
   configuration and a private `HOME` under `/tmp`), `--no-gpg-sign`, and a
   worker-authored message that interpolates NO child output — the module's
   existing rule. `rev-parse --verify HEAD` is then the real proposal head,
   with the declared base as its ancestor. An empty diff produces no commit and
   the existing `no-candidate`/`unable` disposition, unchanged.
4. **The declared durable object output is a bundle.** `git bundle create
   proposal/objects.bundle <base>..HEAD` — the base→head object range, not a
   second copy of the candidate. `proposal/candidate/` is REMOVED: the
   candidate now lives as a commit on the persistent line, and copying the
   whole tree beside it is exactly the copying ceremony this finding forbids.
   Net effect on the declared output is smaller, not larger:
   `proposal/{objects.bundle, change.patch, verification.txt, result.json}`,
   with `change.patch` now `git diff <base>..HEAD` and `result.json` gaining
   `base` and `head`.
5. **Every worker Git vector carries `-c safe.directory=<exact path>`.** The
   runtime posture pins `--user 65532:65532` while the line and the nominated
   source are owned by the manager's uid, so Git's dubious-ownership check
   applies to both. Composed as a closed argv operand; no configuration file is
   written and no global state is touched.
6. **The vectors are composed in `claude_agent.py`.** `Dockerfile.claude` copies
   only `source_profiles` into the image, so the worker cannot import
   `checkpoint_profiles`, and a shared composer would cost a new package plus a
   Dockerfile change. If review prefers one composer for both parties, the path
   set grows by `source_profiles/checkout.py`, `Dockerfile.claude` and their
   tests, and that is a decision for this review rather than a silent choice.

### Pinned worker-owned claim — Proposed

One namespaced member on the declared proposal output's `result_metadata`,
carried opaquely by `baton_worker` and, once the parallel sealing repair lands,
by the sealed `artifactOutput`:

```json
{"baton.git-proposal/1": {
   "base": "<40 or 64 lower-case hex>",
   "head": "<40 or 64 lower-case hex>",
   "transport": "objects.bundle",
   "recap": "<bounded worker-authored text>"}}
```

Closed member set. `base` is the revision the worker PROVED its worktree was
at; `head` is the commit it made; `transport` is the relative path of the
object bundle inside the worker's own declared output; `recap` is the
implementation recap the worker already computes. Plain hex rather than
`{algorithm, hex}`: the composer derives the algorithm from the object-name
width by the accepted `source_profiles.BASE_KINDS` rule, which is the same rule
already pinned for `target_revision` in the composer's dossier.

Forbidden in this claim, and refused by the composer if present: any artifact
id, media type, byte count, content digest or custody locator; any manifest,
result, input, policy or profile digest; any assignment reference, generation
or operation identity; and any `author_tests` or `dossier_evidence` entry,
because an `evidenceRef` requires a custody `artifactRef` the worker cannot
mint. It maps to exactly three `proposalManifest` members: `source_base`,
`proposal_head` and `implementation_recap`.

### Pinned path set — Proposed

Production, ONE file:

- `v12/worker/claude_agent.py`

Tests, ONE file:

- `v12/python/tests/manager/test_claude_agent.py`

Explicitly NOT in scope and not to be edited: `worker_manager/sealing.py` and
`tests/manager/test_sealing.py` (the parallel provider's), any other
`worker_manager` module, the frozen schemas, `checkpoint_profiles.py`,
`source_profiles/`, `job_manager/`, `integration/`, `tools/single_worker.py`,
`tools/dogfood_operator.py`, `tools/parallel_test.py` and `Dockerfile.claude`.
If the delivery cannot be completed in these two files, it returns for targeted
review before anything else is edited.

### Bounded test-change scope — Proposed, needs explicit approval

New cases in `test_claude_agent.py`, all against REAL `git` in a temporary
repository owned by the test's own uid, in the style
`test_checkpoint_profiles.py` already uses:

- a positive turn over a materialized line produces one commit whose parent is
  the declared base, a clean worktree afterwards, and a declared output of
  exactly the four members;
- `GitCheckpointProfile.freeze` over that same line succeeds and its `head` is
  the head the worker claimed, and its `paths` are the changed set;
- independent resolution after producer exit: a FRESH clone of the source at
  the declared base, which never saw the worker's workspace, unbundles
  `proposal/objects.bundle` and resolves both the head and the base, and
  `merge-base --is-ancestor` proves the relationship;
- correction continuity: two successive turns on one line produce two commits
  with the second's parent the first, both resolvable;
- the claim's exact closed shape, and that it carries no custody identity;
- focused refusals: a workspace not at the declared base; a dirty workspace on
  entry; a provider that moved `HEAD` off the declared base's ancestry; an
  unchanged tree producing no commit and no proposal; and the declared output
  never entering the commit.

Existing cases requiring assertion changes, enumerated rather than described:
the candidate root becomes `/output` instead of `/output/candidate`, so the
path assembly in `NeitherChildLeavesEphemeraInTheCandidate`,
`TheCredentialIsLinkedAndNeverRead`, `ThePositiveTurnWritesTheDeclaredProposal`,
`TheMeasuredBytesAreWhatGetPublished`, `FailureIsHonest` and
`TheSourceCopyIsBoundedAndFollowsNoLink` moves with it. Their INTENT is
unchanged — every ephemeral root stays outside the candidate, no bearer is
opened, no child stream byte is published, and the measured bytes are still what
is published. The `proposal/candidate/` assertions are removed with the tree
they describe and replaced by the bundle assertions above. No existing refusal
is weakened, and this enumeration is the case-specific confirmation
`AGENTS.md` requires; it is not authority for any other test change.

Internal changes this implies, recorded so review can size them: `_checked_tree`
and the byte measurement must skip `.git` and the declared output paths, since
the candidate root now contains both; and `_diff`'s two-tree textual diff is
replaced by `git diff <base>..HEAD` for the patch, with the per-path byte
digests that `_revalidated` and `_publish` depend on kept and computed
separately. The byte-identity guarantee is preserved exactly.

### Reported prerequisite — Confirmed — the private line is not writable by the worker

This is the one substantial missing capability found, and it is outside this
Work's paths.

`workspaces.assignment_workspace` makes a per-attempt workspace writable by
calling `adopt_workspace_group`, which chowns the root to the configured
workspace group and sets a group-writable mode; `oci` then composes
`--group-add <gid>` beside the pinned `--user 65532:65532`. Its own refusal
text states the stakes: "without it the worker cannot write the outputs it must
declare."

`workspaces.line_assignment_workspace` performs no such adoption. It proves the
persistent line's device and inode and returns it as the workspace. The line
tree is created by `_line_place` at `0700` and populated by
`GitCheckpointProfile.materialize`'s `git clone` under the MANAGER's uid, so
uid 65532 receives no write access to the worktree, to the tracked files, or to
`.git`. A group adoption of the top directory alone would not be enough either,
since the tree already holds manager-owned files.

**So the worker half can be implemented and proved on its own — the tests above
use a line the test uid owns — but the live end-to-end demonstration is blocked
until the persistent line is provisioned writable for the runtime identity.**
That is a bounded correction in `workspaces.py` (with whatever `review_cycles.py`
must pass it), it needs an owner decision on how the line tree is owned, and it
is reported here rather than reached into.

### Observation for the owner — not in this Work

`integration/admission.resolved_account` cross-binds the Authority proposal
against the frozen checkpoint's line, digest, evidence and path set, and against
the writer's frozen result — but it never compares the proposal's
`candidate_digest` with the checkpoint's `head_object`. Once a real head exists
those are the same fact from two producers, and binding them is what would make
"the published candidate is the reviewed commit" mechanical rather than
conventional. Raised as an observation only; `integration/` belongs to another
owner and is not edited here.

### Not verified in this environment

Two mechanism details are asserted from documented Git behaviour and in-tree
precedent, not from a probe: that `.git/info/exclude` keeps `status
--untracked-files=all` empty for the declared output, and the exact accepted
spelling of the bundle range. This participant's deployment policy hook refuses
Git history and index mutations from its shell, including inside a throwaway
temporary repository, so the probe could not be run and no stronger form of it
was attempted. Both are proved by the new cases above at implementation time,
and neither is load-bearing for the design: if the range spelling differs, it is
the argv that changes and nothing else.

## Independent plan review — 2026-09-06 — baton.codex

**Changes requested before owner scope acceptance.** See append-only
`review-2026-09-06T23-54-31Z.md` for the exact current source boundaries,
corrections and focused verification. No production or existing-test edit is
approved by this review.

The persistent line and retained checkpoint refs are confirmed reusable. The
statement that only one commit act is missing is **superseded as a completeness
claim**: the proposed worker ending and compatibility path still miss these
first-demonstration requirements:

1. Original immutable proposal base B and correction-entry head H1 are distinct.
   The line/profile still use B on round two, while the worker starts at H1.
   Keeping the proposed `HEAD == declared_base` check rejects the correction;
   changing `declared_base` and the claim's `base` to H1 conflicts with the
   composer's required source-base/target equality while the target remains B.
   Pin both meanings and accepted sources before publishing the claim contract.
2. `baton_worker` writes `output.json` after `ClaudeAgent.work` returns.
   Excluding only declared proposal directories leaves the real checkpoint
   dirty. Pin reserved control/output paths, collision refusal and a positive
   test including actual completion publication before freeze and correction.
3. The fresh non-line workspace already contains its manager-created
   `result-<attempt-id>` directory, so a clone into `/output` is not a clone
   into an empty destination. Pin lifecycle selection and compatibility;
   missing metadata on an existing line must not authorize recloning it.
4. Existing worker fixtures are GENERIC, and the dogfood reader still requires
   `proposal/candidate/`. Their candidate-tree assertions are not made obsolete
   by a new Git-output mechanism. Pin the selected output contract and its
   consumers before removing that directory or changing those assertions.

The proposed four-member worker-only namespace and keeping Git commands local
to the concrete worker remain reasonable recommendations, subject to those
corrections. Pin the commit-parent and verified-tree relationship and prove the
retained incremental bundle from an independent base-only recipient. A claim
or clean status alone does not establish those equalities.

**Authority clarification:** the earlier sentence calling the implementer's
test enumeration “the case-specific confirmation” is superseded. It proposes
the test-change scope; the explicit first-checkpoint instruction still requires
owner scope approval after independent plan review. No test change is granted
by the proposal itself.

**Separate recorded prerequisite:** W105706 owns runtime access provisioning
at `baton:work/records/2026/09/finding-v12-private-line-runtime-access/`.
`_line_place` sets custody PARENTS to 0700, not the checkout root; the confirmed
gap is that the populated persistent checkout never receives the runtime
sharing policy when it replaces the ordinary attempt workspace. Live denial
under exact deployed modes/identity still needs that provider's proof. The
reviewer could not record the W103083 dependency because both dependency and
directed-request operations require its implementation-route authority; neither
operation changed the ledger. The implementer handoff requests that gate.

## Revised plan — 2026-09-06 — baton.claude — supersedes the pinned design above

Every correction in the review is accepted; each was re-checked against the
tree rather than taken on the reviewer's word, and each held. Three of them
change the design rather than refine it, so this section **supersedes the
"Pinned design", "Pinned worker-owned claim", "Pinned path set" and "Bounded
test-change scope" subsections of the 2026-09-06 revalidation above.** Those
subsections stay as written: they are how this arrived at a two-file answer
that did not survive its own completion path, and the next reader needs that
to see why the selector below is not overengineering.

The ledger gate the review asked for is recorded: W103083 is now blocked on
W105706 at event 105757, from the implementation route.

### Re-verified — what the review got right, and the evidence

- **B and the entry head are distinct.** `freeze_checkpoint` passes
  `line["declared_base"]` — the immutable B — to `profile.freeze` on EVERY
  revision, and `_evidence` refuses a checkpoint whose base is not it. But
  `grant_writer` admits a correction writer only when it names the line's
  current checkpoint, and then calls `profile.validate(..., current=True)`,
  whose `current` branch requires the worktree's HEAD to equal that
  checkpoint's head. So round two starts at H1 while the publication base is
  still B. An entry check of `HEAD == declared_base` rejects it. Confirmed.
- **The completion document dirties the line.** `baton_worker.handle` calls
  `agent.work`, measures the declared outputs, then `publish_completion`
  writes `<OUTPUT_ROOT>/output.json` via a `.publishing` staging name and
  `os.replace`. Both names are untracked, both appear after the agent has
  returned, and `GitCheckpointProfile._clean` refuses any of it. Confirmed.
- **A fresh `/output` is not empty.** `workspaces.assignment_workspace` creates
  `workspace/result-<attempt-id>` before runtime start, and `custody` refuses
  its ABSENCE as a contradiction. So the in-place clone fallback I proposed
  cannot run on the non-line path. Confirmed.
- **Generic consumers still need `proposal/candidate/`.** The existing
  `test_claude_agent.AdapterCase` task is `source_profile: "generic"` with a
  null base, and `dogfood_operator._derived` reads
  `<proposal>/candidate` to recompute the diff and rerun the verification
  outside the container. Removing that tree breaks a live consumer, and the
  result schema is still `baton.dogfood-proposal/1`. Confirmed.

### Confirmed — one further gap the review's third point exposes

Under `line_assignment_workspace` the workspace IS the line checkout, and
nothing creates `result-<attempt-id>` inside it — `assignment_workspace` made
that directory in the attempt's OWN workspace root, which the line mount
replaces. `custody` then refuses: "this manager establishes it before the
runtime starts, so its absence contradicts an attempt that ran". So a live
line-driven attempt fails at custody for a second, independent reason beyond
W105706's permissions. Recorded here and belonging to W105706 or the assembly,
not to this Work; it is also why the reserved-path set below covers that name.

### Revised design — Proposed

**1. The workload is SELECTED, never inferred.** A third source-profile word,
`git-line`, means "the workspace is a prepared persistent development line".
`checkout_plan` answers it with `source_root` = the workspace, `steps = ()`
and the declared base carried through — no clone and no detach, because the
line was materialized by `GitCheckpointProfile.materialize` before this
runtime existed. It requires a declared base exactly as `git` does. This is
the accepted place for the decision: the profile word is what the assignment
SAYS, and `source_boundary._profile` deliberately never compares it against a
list, so the generic manager stays unaware. A missing or corrupt repository
under `git-line` REFUSES; nothing recreates or re-clones a line.

**2. The compatibility matrix is explicit and only the new row changes.**

- `generic` — unchanged in every respect, including `proposal/candidate/` and
  `baton.dogfood-proposal/1`. No existing assertion moves.
- `git` (non-line) — unchanged: clone to `/output/checkout`, copy to
  `/output/candidate`, same declared output, same result schema. The in-place
  clone fallback is withdrawn; it was impossible.
- `git-line` (new) — the mounted worktree is the candidate; the worker commits;
  the declared output is `proposal/{objects.bundle, change.patch,
  verification.txt, result.json}` with no `candidate/`, and `result.json` is
  `baton.dogfood-proposal/2` carrying `base` and `head`. The one consumer of
  this workload is the line-driven assembly that does not exist yet, so no
  current reader is broken and `dogfood_operator` is untouched.

**3. B and the entry head are two facts, and the worker consumes the
manager's guarantee rather than restating it.** The task's `declared_base` is
B and nothing else; its meaning is unchanged. At entry, under `git-line`, the
worker writes its exclusions, then requires the worktree clean, then reads
`E = rev-parse --verify HEAD` and requires `merge-base --is-ancestor B E`
(satisfied by `E == B` on round one). E is not declared anywhere and is not
guessed: it is whatever the manager's own `grant_writer`/`validate` left the
line at, and the ancestry check is the worker proving it received a line that
still descends from the base it was told to publish against. Nothing new is
asked of the task document or of any producer.

**4. The commit continues E, and exactly one commit is the worker's.** After
the provider turn the worker requires `HEAD == E` still — a provider that
committed anything is refused, which is what makes "one worker-authored
commit" an established account rather than a hope. Then `git add -A`, then one
commit with a closed argv: explicit `-c user.name=`/`-c user.email=`
constants, `--no-verify` so no hook rewrites the candidate, `--no-gpg-sign`,
`-c safe.directory=<exact path>`, and a message interpolating no child output.
Then `rev-parse HEAD` is Hn and `rev-parse Hn^` MUST equal E.

**5. The byte-identity proof transfers to the commit.** The removed
`_publish` per-file comparison is replaced, not dropped: for every changed
path the worker compares `cat-file blob Hn:<path>` against the digest it
already measured from the worktree, so a clean/smudge filter or anything else
that made the committed bytes differ from the verified bytes refuses before
publication. `status --porcelain=v1` empty after the commit additionally
proves worktree, index and HEAD tree agree.

**6. Reserved paths, exclusions and collisions.** The reserved set is the
completion document `output.json`, its `.publishing` staging name, the
root-anchored `result-*` namespace, and every declared output path. Exclusions
are written to `.git/info/exclude` BEFORE the entry cleanliness check, since
the manager-created result root would otherwise fail it. Declared paths are
emitted as exact root-anchored patterns; a declared path containing a gitignore
metacharacter (`*?[]!#\` or a trailing space) is REFUSED rather than escaped
and guessed at, because a declared path is not an ignore pattern. `result-*`
is the one deliberate glob and is named as such. If the source TRACKS any path
in the reserved set, the turn refuses: an ignore rule cannot remove tracked
content, so this must fail loudly rather than produce a permanently dirty line.
The reserved constants are spelled in `claude_agent.py` with an additive test
asserting they equal `baton_worker`'s, so the two cannot drift — the pattern
`test_worker_entry` already uses for the worker's literals.

**7. The bundle, and its recipient proof.** `git bundle create
proposal/objects.bundle <B>..HEAD`, cumulative from the immutable base on every
round, so round two's bundle covers B..H2. It is an INCREMENTAL bundle and the
plan says so: the recipient must already hold B, which it does, because B is
the canonical target. The acceptance test resolves it from a recipient that has
B and no access to the producer worktree or its objects, and verifies the exact
head and the candidate bytes there. If a detached HEAD turns out not to be an
advertised reference in the bundle, the implementation instead retains a
worker-owned ref and bundles that; the test decides which, and it is an argv
detail rather than a design change.

### Revised worker-owned claim — Proposed

```json
{"baton.git-proposal/1": {
   "base": "<B: 40 or 64 lower-case hex>",
   "head": "<Hn: 40 or 64 lower-case hex>",
   "transport": "objects.bundle",
   "recap": "<worker-authored text, at most 4000 characters>"}}
```

The correction is `base`: it is the task's immutable `declared_base` B, never
the entry head E, so `source_base == target_revision` still holds on every
correction round while the canonical target remains B. E is proved and used,
and is deliberately NOT published: it is a fact about this line's history,
which Git already holds through `Hn^`, and the composer has no member for it.

`transport` is a relative locator INSIDE the worker's measured declared output
and nothing more. It does not describe, replace or stand in for the manager's
retained `artifactOutput`; the composer still binds `proposal_artifact` and
`output_digest` from the manager's own measurement. Bounds: both hex members at
one of the two real object-name widths, `transport` a relative canonical path
without `..` at most 128 characters, `recap` at most the module's existing
`MAX_RECAP`. Every custody identity, manager measurement, assignment
reference and policy digest remains forbidden, and `author_tests` and
`dossier_evidence` remain the empty list.

### Revised path set — Proposed

Production, TWO files:

- `v12/python/src/baton_v12/source_profiles/checkout.py` — the `git-line` word
  and its plan. Selection has to live where the other two words live; the
  alternative is inference, which this codebase refuses on principle and which
  the review refused specifically.
- `v12/worker/claude_agent.py` — the `git-line` branch, the commit, the
  exclusions and the bundle. Git vector composition stays here, as the review
  allows.

Tests, TWO files, both ADDITIVE:

- `v12/python/tests/manager/test_source_boundary.py` — the new word's pairing
  and plan cases beside the existing two.
- `v12/python/tests/manager/test_claude_agent.py` — the `git-line` cases.

Still explicitly out: `worker_manager/` including `sealing.py`, the frozen
schemas, `checkpoint_profiles.py`, `job_manager/`, `integration/`,
`tools/dogfood_operator.py`, `tools/single_worker.py`,
`tools/parallel_test.py` and `Dockerfile.claude` — the image already copies
`source_profiles`, so the new word ships without touching it.

### Revised test scope — the earlier request is WITHDRAWN

The previous section asked for authority to change existing assertions in six
test classes. **That request is withdrawn and no existing-test change is
sought.** It rested on removing `proposal/candidate/` for everyone, and the
review's generic-fixture finding is what makes that unnecessary: `generic` and
non-line `git` behaviour is untouched, so every existing case still describes
the workload it was written for. All new coverage is additive:

- one `git-line` turn over a real materialized line: exclusions written, entry
  clean, `E == B`, exactly one worker commit with `Hn^ == E`, the four declared
  members present and no `candidate/`, and `result.json` at
  `baton.dogfood-proposal/2`;
- **the complete worker ending**: the real `baton_worker` completion
  publication runs after `work` returns, and `GitCheckpointProfile.freeze` then
  succeeds over that same line, with its `head` equal to the claimed Hn, its
  `base` equal to B and its `paths` the changed set;
- **two rounds against an unchanged canonical target B**: round two enters at
  H1, refuses nothing, commits H2 with `H2^ == H1`, freezes revision 2, leaves
  revision 1 still resolvable from its retained ref, and claims `base == B`
  again so the second round's metadata is still publishable against B;
- **independent recipient resolution**: a fresh clone holding only B unbundles
  the retained `objects.bundle`, resolves Hn, and matches the candidate bytes,
  with no access to the producer worktree — run for the cumulative round-two
  range too;
- **committed-bytes identity**: `cat-file blob Hn:<path>` equals the measured
  digest for every changed path;
- focused refusals: a worktree not descending from B; a dirty entry; a provider
  that moved HEAD; a source tracking a reserved path; a declared output path
  carrying a gitignore metacharacter; an unchanged tree producing no commit, no
  bundle and no proposal; and a missing or corrupt line repository refusing
  rather than being re-cloned;
- the claim's exact closed shape and bounds, and that it carries no custody
  identity;
- the reserved-name constants equal `baton_worker`'s.

This is a proposal for owner scope acceptance after independent re-review. It
is not self-granted authority, and the earlier sentence claiming otherwise was
correctly superseded by the review.

### Still not verified in this environment

Unchanged and restated because the design now leans on one more Git behaviour:
the `.git/info/exclude` treatment under `status --untracked-files=all`, the
bundle range and advertised-reference spelling, and now the `--no-verify` and
`cat-file` identity checks are all asserted from the documented contracts and
proved by the cases above at implementation time. This participant's deployment
policy hook refuses Git history and index mutations from its shell, including
in a throwaway temporary repository; the probe was not run and no stronger form
of it was attempted.

The absence of a Git-head comparison in generic admission does not authorize
adding one there. Preserve the owner ruling that format-specific review binds
the published candidate to the actual checkpoint. This plan's revised positive
proof must show that binding for the worker output it produces.

## Independent plan re-review — 2026-09-07 — baton.codex

**Proposed for owner acceptance:** the revised four-path plan is suitable for
the bounded worker implementation with the following precise amendments. The
review is `review-2026-09-07T00-09-06Z.md`. This is design sign-off for an owner
decision, not an implemented-candidate approval or self-granted scope authority.

**Confirmed correction; supersedes revised design item 4's hook claim:**
`--no-verify` does not suppress `prepare-commit-msg` and does not disable all
hooks. The worker-controlled commit must use the per-command override
`-c core.hooksPath=/dev/null` as well as the pinned author, signing and parent
checks. Apply the override to worker-controlled Git operations that could run
hooks. Add an additive case with a mutating `prepare-commit-msg` hook that must
not execute. This replaces the mechanism, not the intended no-hook contract.
Sources: [Git hook contract](https://git-scm.com/docs/githooks) and
[Git configuration contract](https://git-scm.com/docs/git-config#Documentation/git-config.txt-corehooksPath).

**Clarification; supersedes revised design item 5's claim that empty status
alone proves byte agreement:** status is an additional cleanliness gate. The
commit-tree check must bind the complete measured change to the committed
change: exact path set, bytes for added/modified regular files, and absence for
deleted paths. A deleted path has no blob to compare. Retain existing file-type
and mode boundaries; no ignored addition or unexpected staged change may be
silently omitted from that equality. Add a deletion case and a transforming
clean-filter refusal case alongside the already proposed byte-identity proof.
These are additive cases in the same pinned worker test file, not new scope.

**Clarification:** `git-line` is a source-consumption selector. The existing
checkpoint profile remains `GitCheckpointProfile` with its own `git` identity.
The future assembly selects both deliberately; this Work does not rename the
checkpoint profile or teach the generic manager to interpret either word.

**Confirmed source correction; supersedes "one further gap" above insofar as
it claims a demonstrated custody refusal:** `line_assignment_workspace`
substitutes the mounted workspace, but `custody._target` independently derives
`<store>/<attempt>/workspace[/result-<attempt>]`, where the ordinary allocator
already created the result root. It does not look for that directory inside
the line. Its quoted absence refusal therefore does not prove the claimed
failure. **Open:** whether live line composition applies the required custody
actions to the intended roots. W105706's owner must triage that locator seam
before the live assembly demonstration; it is not a worker change or an
authorization to create a result directory in the line. The existing
W103083-on-W105706 gate is confirmed in the ledger. Unit worker work can proceed
after scope acceptance without claiming that live composition is proven.

All other revised boundaries stand: B is immutable, E is the admitted entry
head, Hn has exactly E as its parent, the cumulative bundle resolves in an
independent recipient holding B, the real completion publication precedes
freeze and correction, generic/non-line git remain compatible, and both test
files receive additions only. No production edit or Git mutation was performed
for this review. The proposed execution proofs remain implementation gates.

## Owner acceptance — 2026-09-07 — baton.prompt for Slawomir

Slawomir approved the revised four-path implementation scope WITH the amendments
in `review-2026-09-07T00-09-06Z.md`. This supersedes the pending owner-acceptance
status above, not the preserved superseded designs. K may implement in
`v12/python/src/baton_v12/source_profiles/checkout.py` and
`v12/worker/claude_agent.py`, with additive coverage only in
`v12/python/tests/manager/test_source_boundary.py` and
`v12/python/tests/manager/test_claude_agent.py`.

Accepted: explicit git-line selection; immutable B versus entry E; same private
history across corrections; complete worker completion before freeze; cumulative
object transport independently resolved from B; per-command hook suppression;
complete measured/committed path and byte equality including deletion absence;
additive hook/filter/deletion proofs. Preserve generic/non-line behavior. No
existing assertion mutation, core Git adapter, host Git mutation, bulk archive
ceremony or access-provisioning changes are authorized. Return the bounded
implemented candidate for independent review. Runtime-access planning proceeds
separately with tuner and remains a live-assembly prerequisite.

## Independent candidate review — 2026-09-07 — baton.codex

**Observed and reproduced: changes requested.** Review
`review-2026-09-07T01-06-23Z.md` binds the four submitted file hashes and
records three failures from `evidence/review_regressions.py`. The retained
output is `evidence/review-regressions-2026-09-07.txt`.

1. A real verification command reads an ignored file and passes, but the worker
   returns `completed` with a commit omitting that required file. `_identical`
   checks only committed paths against measured paths, not their equality in
   both directions. The complete measured-change contract is not implemented.
2. A repository `post-index-change` hook runs during the worker turn because
   only the commit vector disables hooks; status/staging vectors do not. The
   accepted no-hook policy must cover those operations too.
3. A no-op correction returns empty metadata and null head while the preceding
   turn's unchanged `objects.bundle` remains in its declared output directory.
   Fresh-line no-op coverage does not prove persistent-line output freshness.

These observations supersede any claim that the first candidate fully meets
the accepted equality, no-hook and no-bundle-on-no-head boundaries. They do
not change the accepted design or expand its four-path scope. Correct the
worker and add bounded regressions to its accepted test file; preserve all
existing assertions, generic/non-line behavior, private history and previously
sealed custody. The implementer owns its response in PROGRESS. Reviewer
execution used the existing disposable Git fixture, with no canonical Git
mutation, product edit or successful-suite rerun.

## Independent correction review — 2026-09-07 — baton.codex

**Confirmed resolved:** the original three probes pass in retained correction
evidence. Every worker Git vector now disables hooks, the stale bundle is
removed by exact name, and full committed/measured path sets are compared in
both directions. This supersedes their outstanding-case status above while
preserving the original observed failures.

**Observed and reproduced, P1 still open:** complete byte equality remains
incomplete. With a tracked file marked assume-unchanged at fixture entry, real
verification reads its new bytes and passes; the worker returns `completed`
but its commit retains the old bytes. The path sets match, and only the other
edited file appears in the Git diff, so `_identical` never compares the hidden
tracked edit's blob. `_representable` checks paths/types, not all file bytes.

Review `review-2026-09-07T01-16-13Z.md` binds the correction hashes and keeps
the reproduction in `evidence/review_tracked_bytes.py` with retained output
`evidence/review-tracked-bytes-2026-09-07.txt`. The required bounded correction
is the accepted contract itself: every measured candidate file must match its
raw committed blob independently of Git's reported change set. Add the focused
tracked-byte regression within the existing additive worker-test scope. No
scope expansion, product edit or canonical Git mutation occurred in review.

## Independent candidate sign-off — 2026-09-07 — baton.codex

**Confirmed resolved and signed off:**
`review-2026-09-07T01-22-56Z.md` binds the four final candidate hashes. The
remaining tracked-byte finding is resolved: `_identical_bytes` compares every
independently measured candidate file with its raw committed blob through one
binary batch, regardless of Git diff/status membership. The unchanged reviewer
probe passes in retained evidence; path-set/type/deletion checks and the earlier
hook/output-freshness corrections remain intact.

This supersedes the preceding outstanding-candidate status, preserving all
failure/review history. The accepted bounded worker capability is ready for
owner acceptance and satisfying closure, then consumption by W103874. Both
existing test files remain additive (+610/-0 and +58/-0); no assertion changes
are approved. The claim contract and exact output members are summarized in
the signed-off review. Actual runtime access and line-aware custody remain
separate W105706/W105982 prerequisites for live composition, not capabilities
claimed by these host fixture results. PROGRESS remains implementer-owned.

## Owner candidate acceptance — 2026-09-07 — baton.prompt for Slawomir

Slawomir approved accepting and closing this bounded prerequisite. All four current
source/test hashes were rechecked against `review-2026-09-07T01-22-56Z.md` and
match. The reported 1015-test relevant sweep and retained four reviewer probes
are accepted without duplicate reruns; the documented whole-discovery baseline
failures are not declared green. This supplies the real private-head and durable
object claim to the manifest composer. Runtime permissions/custody and the new
detach experiment remain separate; no production detach adoption, integration
receipt, Git mutation or deployment is implied by closure.
