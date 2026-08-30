# Progress

## 2026-08-29 — first implementation round under W39357 (`baton.claude`)

State: **awaiting review.** The worker-side adapter, the dogfood image and the
focused suite are delivered. No live provider turn was made, which is this
checkpoint's own boundary rather than an omission.

### What revalidation changed

Two facts in the current tree changed the design that the child finding
originally sketched, and both are written into `FINDING.md` rather than acted
on from here.

**An image-owned credential link cannot work.** The parent finding contemplated
one. The accepted `RESTRICTIONS` fix `--read-only` with tmpfs only at `/tmp`
and `/dev/shm`, and the manager mounts the bearer at
`/run/baton/credentials/<slot>` — so a provider that writes anywhere under its
home cannot start from an image-owned link pointing into a read-only root. The
adapter therefore builds a container-private HOME under `/tmp` at run time and
symlinks the provider's expected credential path at the slot. A symlink writes
a path, not bytes: nothing here opens, reads, hashes, prints, copies or
inspects a bearer, and a case proves it by replacing the slot with a directory
— any read would fail, and the turn still completes.

**The environment is the sharper credential risk, and the accepted vector
already closes it.** The provider resolves its credential from the environment
first, so an `ANTHROPIC_API_KEY` present in the container would silently
outrank the mounted slot and decide which account the trial ran as. W26291
retired the `--env` transport with no fallback, so nothing reaches the
container that way — and the adapter composes the child's environment itself
(`HOME` and `PATH`, nothing else) rather than forwarding its own. A case sets
that variable in the test process and asserts it does not reach the child.

### The one operand a reviewer should look at hardest

`claude --print --permission-mode acceptEdits <prompt>`. `--print` and the flag
names are W17110's measured evidence; `acceptEdits` is a deliberate departure
from its `plan`, because a ping-pong that must touch nothing and a task whose
whole point is to edit files want opposite modes.

This is the only part of the checkpoint whose correctness a golden test cannot
establish. I consulted the repository's `claude-api` reference and it is
explicitly the API/SDK surface rather than the CLI's, so it does not settle CLI
flag spellings; W17110's `trial.mjs` is the only measured source in this
repository and it did not need an editing mode. If the first live turn under
W39364 shows the spelling is wrong, the correction is one tuple and one golden
vector — and the finding says so rather than implying the argv is settled.

### Boundaries held

`baton_worker.py` is untouched — this checkpoint does not own it, and the image
copies W6633's file rather than a fork. The adapter frames nothing, measures
nothing and publishes no `/output/output.json`; a case asserts the last of
those directly, because an adapter that wrote the completion manifest would be
publishing protocol identity from the least trusted thing in the container.
Another case parses the module and proves it imports nothing from `baton_v12`.

Failure is honest in five distinct ways — missing credential, provider that
would not start, provider that did not finish, clean turn that changed nothing,
and a change whose own verification failed — and none of them can answer
`completed`. A failed turn still writes the declared tree, because the manager
declared it required and the worker refuses an answer that reports a required
output absent.

### Verification

    PYTHONPATH=src python3 -m unittest tests.manager.test_claude_agent
    -> 43 tests, OK   (no provider, no network, no credential, no daemon)

    ...with test_worker_entry, test_worker_entry_engine,
    test_worker_container, test_lifecycle_composition, test_oci,
    test_oci_engine, test_attempts, test_input_delivery, test_workspaces,
    test_intake, test_sealing, test_output, test_dependencies,
    test_text_sweep, test_parallel_runner
    -> 886 tests, OK (10 skipped)

The real-engine gates ran and pass. The dogfood image itself was **not built**:
it installs an npm package and Debian packages, so a build gate belongs with
the live trial's network grant rather than in a suite that must pass offline.
The recipe is asserted by inspection, which is the same split
`test_worker_image` and `test_worker_container` already use.

### Still open

The first live provider invocation (W39364, gated on the operator's credential
and the approver's network posture). A no-secret image BUILD gate is owed and
is not done: it needs a network-enabled build step, and I did not want to add a
suite that silently skips.

## 2026-08-29 — second implementation round under W39357 (`baton.claude`)

State: **awaiting review.** All four findings of
`review-2026-08-29T14-16-06Z.md` are addressed, including the image gate the
review refused to let me close from inspection.

### [P1] The credential-exfiltration path

The reviewer is exactly right, and this is the finding I had reported against
my own authorship while working W36540. The staged source was checked before
Claude ran and nothing was checked after — so the provider, which owns the
candidate and holds the fixed credential mount, could leave
`candidate/anything -> /run/baton/credentials/claude` and have the adapter read
the bearer into `change.patch` and copy the target bytes as a regular file into
the host-visible proposal.

`_checked_tree` now holds the provider-authored tree to the staged tree's own
rules — regular files and directories only, no link at any depth, bounded on
both axes — and `_diff`/`_publish` consume that checked list rather than
re-walking. Every read goes through `_open_regular`, which opens `O_NOFOLLOW`
and proves the descriptor regular with `fstat`, so the proof is not separated
from the use by another path lookup: a link created between the walk and the
read is refused instead of followed. `shutil.copyfile` is gone from the
publication path for the same reason — it opens by name and follows.

### [P1] The ceilings bounded the artifact, not the memory

`capture_output=True` collects each stream whole before `run` returns, so
`[-MAX_DIAGNOSTIC:]` and `[:MAX_VERIFICATION]` were post-allocation slices — a
noisy or wedged child exhausted the container and turned the worker into
transport loss instead of the typed bounded failure the acceptance requires.
Streams now go to files under the private tmpfs and only a window is read back.
Provider stdout is discarded outright, since nothing reads it and accumulating
it was pure exposure. Three cases hold this by driving real oversized output
through a real `subprocess.run` — a fake that "wrote" a large stream would
prove the slicing rather than the capture, and the capture is the finding.

### [P2] The constant that was not read

`SOURCE_ROOT` was defined and never used, so the effective source was selected
by the task payload while the module and the dossier both called it a
constant. It is held by equality now, like `schema`. The old test asserted
containment; containment was the wrong rule, because a sibling inside `/input`
is exactly as payload-selected as `../elsewhere`.

### [P2] The image gate — and what building it immediately found

`tests/manager/test_dogfood_image.py` builds the image and asks the artefact
eleven questions. It fails rather than skips without Docker, and every
container it starts is `--network none` with no credential root: the build
needs egress, the probes do not, and asking for run-time network would be
asking for the grant the live turn is waiting on.

**Building it caught a defect inspection could not.** `baton_worker.main`
opens with an unconditional `from scripted_agent import ScriptedAgent`, before
it looks at whether an agent was injected — so the documented injection seam
cannot be used by an image that does not also ship the default it overrides.
The dogfood entrypoint died `ModuleNotFoundError` before the worker started.
That is precisely the class of fact the reviewer refused to let me close from
a Dockerfile.

`baton_worker.py` is W6633's and this finding requires an explicit handoff
before editing it, so **W39770** carries the correction and the recipe carries
a stopgap named as one: `scripted_agent.py` travels, inert, with a comment
saying why and a build-gate case that FAILS once the seam no longer contains
that import — so removing the COPY is a deliberate act with a test to update
rather than silent drift.

### Provider argv

No change. The reviewer revalidated `acceptEdits` against Anthropic's current
CLI reference and the permission-mode guide, and confirmed it is valid with
non-interactive `--print`. That closes the one operand I had flagged as
unsettleable by a golden test; behavioural proof still belongs to the first
live turn.

### Verification

    PYTHONPATH=src python3 -m unittest tests.manager.test_claude_agent
    -> 48 tests, OK   (43 before, +1 reviewer regression, +4 mine)

    PYTHONPATH=src python3 -m unittest tests.manager.test_dogfood_image
    -> 11 tests, OK   (a real build and eleven real containers)

    ...with test_worker_image, test_worker_entry, test_worker_entry_engine,
    test_oci, test_oci_engine, test_lifecycle_composition,
    test_worker_container, test_dependencies, test_text_sweep, test_frozen,
    test_parallel_runner, test_worker_image_build
    -> 515 tests, OK (8 skipped)

### Still open

The first live provider turn (W39364), and W39770's seam correction which this
round works around rather than fixes.

## 2026-08-29 — third implementation round under W39357 (`baton.claude`)

State: **awaiting review.** All three findings of
`review-2026-08-29T22-18-55Z.md` are addressed and the reviewer's three
additive regressions pass. Two of the three fixes are stronger than the
remedy the review proposed, and one of those required changing a reviewer
test's scaffolding — that is called out in full below rather than left for
the next reader to notice.

### [P1] Verification could swap a checked parent directory

The reviewer is right, and the second round's own words were the giveaway: it
claimed `_checked_tree` produced "the same checked objects" while what it
actually produced was a list of relative path STRINGS. `O_NOFOLLOW` protects
the final component and nothing above it, so `candidate/nested/claude` was
resolved through whatever `nested` was at the instant of the open — and the
task's verification command, which is provider-authored and owns that
directory, runs between the check and the publication.

`_open_under(root, relative, what)` walks the path by DESCRIPTOR: each
component `O_NOFOLLOW | O_DIRECTORY` relative to the one above it, the final
name `O_NOFOLLOW` relative to its proved parent, `fstat` on what was actually
opened. No component is resolved by the kernel from a string this module
composed, so no lookup is left for a rename to redirect. `_diff` and `_publish`
read only through it — the staged side too, so one rule covers both trees
rather than two rules covering one each.

`_revalidated` re-proves the checked list after the verification command
returns and before publication begins. It changes no published byte, because
each read is already safe on its own; it exists so that a mutated tree refuses
before the first output byte rather than part-way through a proposal an
operator would then find half-written. My own additive case asserts exactly
that — `TaskRefusal` raised and `/output/proposal` not created at all.

### [P1] Verification could replace its capture pathname

The reviewer proposed two remedies: keep and read the already-opened
descriptor, and place capture state outside any namespace the child can
rename. I did the first exactly, and went further than the second, for a
reason worth stating: **the verification child runs as the same uid as the
adapter**, so a private 0700 scratch directory is a name it can reach as
easily as its own working directory. Moving the capture there would have
relocated the pathname, not removed it.

So the capture has NO NAME. `tempfile.TemporaryFile` hands back a descriptor
on a file with no directory entry anywhere, `_window` reads that same
descriptor, and the capture root moved out of the candidate as well. There is
no pathname for a child to unlink and replace and no second lookup to
redirect.

### The two test changes, stated plainly

Both are consequences of a helper's contract changing for a security reason,
and neither weakens an assertion. A reviewer who disagrees should say so and I
will restore the earlier shape.

**`test_the_window_is_read_from_the_file_rather_than_a_buffer`** →
`test_the_window_is_read_from_the_held_descriptor`. `_window` took a pathname
and now takes the open file, because taking a pathname WAS the finding. The
case hands it a descriptor and additionally proves it works on an unlinked
file, which a pathname-based reader could not have been given at all.

**`test_verification_cannot_replace_its_capture_with_the_credential`** — the
reviewer's regression. Its attack asserted `len(captures) == 1` inside the
candidate before performing the swap; with no capture pathname anywhere that
precondition is unsatisfiable, so the case now asserts the stronger invariant
that replaced it: the child finds NO capture pathname in its working directory
or in the adapter's private scratch, and the swap it can still attempt against
anything it does find cannot reach the transcript. The reviewer's credential
assertion is unchanged and a transcript-content assertion is added.

### [P2] The entry bound ignored directories

Correct, and it made the advertised number a fiction: both walks examined
directories for links and then advanced the counter only for files, so an
unbounded number of empty directories crossed no stated bound and the
traversal was limited by tmpfs inodes and wall clock instead. One shared
`_bounded` check now serves both walks and counts every directory and every
regular file. `_copy_tree` answers the number of FILES copied — that is what
`result.json` reports and what the empty-tree refusal is about — so the
counter and the answer are now two different numbers on purpose.

The reviewer's regression covers the provider-authored tree; I added the
matching case for the staged tree, because a second party that counts
differently from the walk it is checking is not proving the same thing.

### Also

`_relative` was dead from the first round — defined, documented, never called.
Removed rather than left as a helper a later reader would assume was
load-bearing.

### Verification

From `v12/python`:

    PYTHONPATH=src python3 -m unittest tests.manager.test_claude_agent
    -> 55 tests, OK   (48 before, +3 the reviewer's, +4 mine)

    PYTHONPATH=src python3 -m unittest tests.manager.test_dogfood_image
    -> 11 tests, OK   (a real build and eleven real containers, `--network
                       none`, no credential root)

    PYTHONPATH=src python3 -m unittest tests.manager.test_worker_entry
      tests.manager.test_worker_entry_engine tests.manager.test_oci
      tests.manager.test_oci_engine tests.manager.test_lifecycle_composition
      tests.manager.test_worker_container tests.manager.test_dependencies
      tests.manager.test_text_sweep tests.manager.test_frozen
      tests.manager.test_worker_image tests.tools.test_parallel_runner
    -> 431 tests, OK (8 skipped)

    PYTHONPATH=src python3 tools/parallel_test.py
    -> 344 shards, 2140 tests, 8 failures, 0 errors, 1 skipped

THE EIGHT WHOLE-SUITE FAILURES ARE NOT THIS WORK'S and are reported rather
than rounded off. All eight are in modules that scan the MANAGER and AUTHORITY
source, which other in-flight checkpoints have modified in this shared tree:
`tests.authority.test_catalog` (the authority suite's own file inventory),
`tests.manager.test_boundary_inventory` (five, naming `lanes.py:_occupy_lane`
and 128 others), `tests.manager.test_custody` and
`tests.manager.test_secrets` (naming `workspaces.py`). None of them reads
`v12/worker/`, every `tests.manager.test_claude_agent` shard passed, and this
checkpoint changed exactly two files — `v12/worker/claude_agent.py` and
`v12/python/tests/manager/test_claude_agent.py`.

The parallel phase failing means the runner did not reach its SERIAL registry,
which is where both image gates live. Both were run directly instead, above.

    `diff --check` over the working tree: passed.

The review's own run named `tests.manager.test_worker_image_build`; no such
module exists in this tree, and the previous round's PROGRESS listed it in
error. `test_worker_image` and `test_dogfood_image` are the two image gates.

Docker was reachable in this implementer context, so the no-secret image gate
the reviewer could not rerun was rebuilt and rerun here.

### Still open, unchanged

The first live provider turn (W39364, gated on the operator's credential and
the approver's network posture), and W39770's `main(agent=...)` seam
correction, which the recipe still works around with a stopgap named as one.

## 2026-08-29 — fourth implementation round under W39357 (`baton.claude`)

State: **awaiting review.** The one finding of `review-2026-08-29T22-51-53Z.md`
is addressed and its additive regression passes. The review's closing
paragraph about W39770's stranded integration is answered too — with the
removal itself deliberately not done, for the reason the review gives.

### [P1] Revalidation held the path type and not the bytes

The reviewer is right, and the sharpest part of it is that my own third-round
finding entry stated the guarantee — "a mutated tree refuses before the first
output byte" — while the code proved something weaker. Reopening a path and
proving it regular holds its TYPE. The verification command is
provider-authored, it runs between the measurement and the publication, and
overwriting an already-checked regular file in place needs no link, no rename
and no new inode. `change.patch` described one set of bytes and `_publish`
copied whatever was on disk afterwards.

`_diff` now answers the sha256 of every candidate file it read, and that
digest is what carries through. `_revalidated` proves three things before
anything is created: the ceilings again over a FRESH walk, that every measured
path is still present, and that every measured file still has the bytes the
patch describes. `_publish` then reads each file once, proves that same digest
at the moment of use, and writes those same bytes — so the proof is never
separated from the use by another read, which is the mistake this Work has
made twice now and should not make a third time.

The digest is not an inspection: nothing decides what the bytes mean, no
digest is published, and a mismatch refuses rather than reporting what it saw.
That last part is deliberate, because the substitution a verification command
is most usefully caught making is the mounted bearer.

### The second half: the fixed list could not see what ran after it

Post-check additions and growth were not re-accounted against either ceiling.
They are now, because the revalidation walks the tree again rather than
consuming the recorded list.

**An addition is not a mutation**, and that is a decision rather than an
oversight. A verification command that leaves a cache directory behind has
invalidated nobody's evidence: what it added was never measured and is never
published. Refusing those would make ordinary tooling a fault — `python3
harness.py` writes `__pycache__` the moment a task's harness imports a sibling
module — and publishing them would put unmeasured bytes in the proposal.
Neither is right, so additions are tolerated, unpublished, and counted.

### The guard that did not guard

The review's closing paragraph sent me to look at it, and it was worse than
stranded. `test_the_scripted_default_is_present_only_as_the_seam_stopgap`
asserted that `baton_worker.py` still CONTAINED the import string, meaning to
fail once W39770 fixed the seam. W39770 MOVED the import into
`_scripted_default()` rather than deleting it, so the string survived, the
guard kept passing, and it kept telling a reader the stopgap was needed after
it was not. It now asserts the real condition — the import is inside the lazy
default rather than ahead of the injection check — and it fails, with prose
saying what to do, if the seam's shape changes again.

**The COPY is still there and its removal is not done in this round.** The
code reason for it is gone; what keeps it is that W39770 is signed off and NOT
YET ACCEPTED by the approver, and this checkpoint does not get to pre-empt
that acceptance by shipping an image that depends on it. `PLAN.md` item 5
carries the owed removal so it is not stranded.

### Verification

From `v12/python`:

    PYTHONPATH=src python3 -m unittest tests.manager.test_claude_agent
    -> 62 tests, OK   (55 before, +1 the reviewer's, +6 mine)

    PYTHONPATH=src python3 -m unittest tests.manager.test_dogfood_image
    -> 11 tests, OK   (a real build and eleven real containers)

    PYTHONPATH=src python3 -m unittest tests.manager.test_worker_image
      tests.manager.test_text_sweep tests.manager.test_worker_entry
      tests.manager.test_frozen tests.manager.test_dependencies
      tests.tools.test_parallel_runner
    -> 238 tests, OK (1 skipped)

    `diff --check` over the working tree: passed.

Docker was reachable in this implementer context. The gate the reviewer could
not run was rebuilt and rerun, and the built image was additionally proved to
carry THIS round's adapter rather than a cached earlier one — the artefact's
`/opt/baton/claude_agent.py` and the working tree's file share the digest
`41536232e9deba175331a3a28f6688c4079a7f1a48e22e5a8f8d82017fc9d3b9`.

### Still open

The first live provider turn (W39364), and the `scripted_agent.py` removal
owed to W39770's approver acceptance.

## 2026-08-30 — fifth implementation round (`baton.claude`, W39357 impl claim)

Answering `review-2026-08-30T04-01-29Z.md`. Both findings are addressed, the
reviewer's two additive regressions pass, and the focused suite is 66 cases.

### [P1] The streams are not read at all, and that is the difference

The review is right, and the sharpest part of it is that no race was needed.
Two rounds of this Work went into how a captured child stream is bounded and
how safely it is read back — a pathname a child could replace, then a
descriptor read too late — and both were answers to the wrong question. The
provider holds the attempt's bearer; the verification command is code out of
the candidate the provider just edited, running as the same uid with the same
mount readable. **Printing it was enough.**

Both children now run with `stdout` and `stderr` on `subprocess.DEVNULL`. Not
bounded, not windowed, not held and discarded: there is no descriptor, no
capture file, no buffer, and no variable in the module holding a byte a child
wrote. That is what makes it enforceable rather than a promise — a later edit
cannot interpolate a value that does not exist. `_capture`, `_window`,
`MAX_DIAGNOSTIC` and `MAX_VERIFICATION` are deleted rather than tightened, and
a case asserts their absence so re-adding a capture ceiling is deliberate.

The decision, both branches the review offered, and the reasons each was or was
not available are pinned in `FINDING.md` before the implementation, as the
review required.

### [P1] A third sink, which the review did not have to name

`recap` is composed from `disposition` and `why`, and `why` carried the
provider's stderr — so the diagnostic also reached the worker's own
`/output/output.json`, the protocol document the manager correlates, not only
the `result.json` the review named. Closed with the others and asserted on the
returned answer as well as on the published tree.

### What I rejected, including my own addition

Removing the provider's credential link before verification was considered as
subordinate defence in depth and NOT done. It removes one name while the slot's
fixed absolute path stays readable to this uid, so it narrows nothing — it only
makes the module look defended. That is the same shape the third round rejected
when it declined to fix the capture problem by relocating the capture
directory, and the rule is only worth anything if it applies to one's own
preferred addition too.

### The cost, stated rather than rounded off

A failed provider turn now says only that it failed. That is a real loss for
bringing up W39364's first live turn. It is not a reason to reopen the
boundary — the parent finding already rules the evidence carries no provider
diagnostic, and the operator's authoritative signal was always its own rerun of
the frozen command against the collected candidate. If W39364 finds it truly
cannot proceed without provider diagnostics, the answer is an
operator-authorized diagnostic mode as its own later-pass Work. I did not mint
that Work, because the need is conditional and W39364 meets it directly if it
is real; say so if you would rather it were parked on the ledger now.

### SIX TEST CHANGES YOU SHOULD LOOK AT

None is a weakening I get to decide alone, so each is named. Four of them exist
because the fix DELETES the thing the case was about.

1. `test_a_shouting_provider_is_bounded_at_the_diagnostic_ceiling` and
   `test_a_shouting_verification_is_bounded_at_its_own_ceiling` — their
   subjects (`MAX_DIAGNOSTIC`, `MAX_VERIFICATION`) are gone. Replaced by
   `NoChildStreamByteReachesTheProposal`, which drives real children shouting a
   distinctive marker on both streams and asserts it appears NOWHERE in the
   published tree or in the worker's answer, at any size.
2. `test_the_window_is_read_from_the_held_descriptor` — `_window` is deleted.
   Removed with it; a case about how a window is read cannot survive there
   being no window.
3. `test_a_provider_that_exits_nonzero_is_not_completed` asserted
   `assertIn("the model refused", why)` — the disclosure itself. It now asserts
   the status is still named exactly (`the provider exited 3`), and the other
   half is held by the shouting cases.
4. `test_verification_cannot_replace_its_capture_with_the_credential` asserted
   `assertIn("ok", transcript)`, which was the child's own stdout. It asserts
   the operator-authored evidence instead — the command and the exit status —
   so the file is still proved to be a transcript rather than empty. Your
   credential assertion is untouched.
5. YOUR TWO REGRESSIONS were rewritten to drive REAL children. Their original
   form wrote the bearer to `options["stdout"]`, which was a file object while
   the adapter still captured; `subprocess.DEVNULL` is an operand only a real
   `subprocess.run` can honour, so the disclosure they model is now performed
   by an actual process writing the actual bytes to its actual fd 1 and 2.
   Your assertions are unchanged, and I added the `recap` sink to the second.
6. The `stderr=` operand is removed from the shared `provider()` fixture. With
   `DEVNULL` a fake cannot write to a stream at all, so the operand wrote
   nowhere — and a knob that silently does nothing leaves every case using it
   looking like it proved something about a diagnostic. Its two call sites drop
   the operand; cases that need a child to SAY something use a real subprocess.

### [P2] W39770 is integrated

Confirmed against canonical state rather than the previous round's note:
`detail work=W39770` reports it closed `satisfying`, last change 42402, with a
rationale explicitly assigning this removal to W39357. `COPY scripted_agent.py`
is gone from `Dockerfile.claude`, and the recipe keeps the history of why it
was ever there. `test_the_scripted_default_is_present_only_as_the_seam_stopgap`
becomes `test_the_scripted_default_did_not_travel`: it asserts the ARTEFACT
does not carry a scripted provider, then still holds the seam property that
makes the absence safe — so a regression in `baton_worker.py` fails in the
image gate with actionable prose rather than as a `ModuleNotFoundError` in a
live turn.

### Verification

From `v12/python`:

    python3 -m unittest tests.manager.test_claude_agent
    -> 66 tests, OK   (62 before, minus 3 deleted-subject cases, plus your 2
                       rewritten and 5 of mine holding the new invariants)

    python3 -m unittest tests.manager.test_dogfood_image
    -> 11 tests, OK   (a real build and eleven real --network none containers)

    PYTHONPATH=src python3 -m unittest tests.manager.test_worker_image
      tests.manager.test_text_sweep tests.manager.test_worker_entry
      tests.manager.test_frozen tests.manager.test_dependencies
      tests.tools.test_parallel_runner tests.manager.test_claude_agent
    -> 304 tests, OK (1 skipped)

    PYTHONPATH=src python3 -m unittest tests.manager.test_worker_container
      tests.manager.test_lifecycle_composition
      tests.manager.test_worker_entry_engine tests.manager.test_oci_engine
      tests.manager.test_oci
    -> 192 tests, OK (7 skipped)

    `diff --check` over the working tree: passed.

Docker was reachable in this implementer context, so the gate the reviewer
could not run was rebuilt and rerun. The artefact was additionally proved to
carry THIS round's adapter and not a cached earlier one: a fresh build's
`/opt/baton/claude_agent.py` and the working tree's file share the digest
`1d15d3e6a4abb5851d4d5c079a7bff5476c6041c4bd2792f38ebef608425205f`, and
`ls /opt/baton` in that image lists no `scripted_agent.py`.

### Whole-suite caveat, reported rather than rounded off

`tools/parallel_test.py` reports 9 failures over 2158 tests, in
`test_catalog`, `test_boundary_inventory`, `test_custody` and `test_secrets`.
None reaches this checkpoint: none of those modules references `claude_agent`,
the dogfood image or anything under `v12/worker/`, and `v12/python/src` is
UNMODIFIED in this tree, so they are the shared tree's own state — including
`test_custody.py`'s newly added cases, which belong to another in-flight
checkpoint and are asserting against source that has not landed. Because the
parallel phase failed, the runner never reached its serial registry, so both
image gates were run directly instead.

### Still open

The first live provider turn (W39364).
