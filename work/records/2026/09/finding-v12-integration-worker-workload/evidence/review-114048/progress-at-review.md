# Progress

Not started. No implementation author has claimed this provider.

## 2026-09-07 — baton.claude — claim113322, adoption and the additive provider wrapper

**This turn does not deliver W110935.** It delivers the adoption and pin the
plan requires before any source edit, one additive public method, its focused
suite and one registry entry. The workload, the entry, the recipe, the image
suite and the joined proof are **not started**, and that is stated here first
rather than at the end.

### Revalidation before acting

The eight inputs in `evidence/revalidation-113300/audit.json` were re-measured
against the current tree: all eight match, including the four accepted child
hashes and the accepted `claude_agent.py` base
`65a9d8b7dda16f76665c0a620740653b43692ac315e246fd4e822fe222101817`. All five
planned new paths were absent. Nothing was acted on without that check.

### What was decided, and pinned before the edit

The dated FINDING entry pins the workload decisions the plan asked for: that the
report carries the producer's `bundle_digest` — the canonical digest of the
measured whole-file manifest — and never `envelope_digest`, which covers one
file; the complete correlation set that must agree before a provider starts; a
whole preflight that precedes every write, with repository target-mode authority
deciding the imported mode rather than custody file modes; semantic evaluation
of the scheduled test scope and the frozen independent review, because an
internally consistent bundle is not blanket authority to modify an existing
test; and a conservative ending in which a failure after writable work was
available is `held` unless a pre-mutation refusal is positively proved.

### What was built

`ClaudeAgent.invoke_provider(prompt=, room=)` — additive, at the one existing
worker path this Work is authorized to touch. It owns **no new mechanism**: it
is the adapter's existing private provider turn — composed argv, an environment
composed rather than inherited, the prepared credential home, the bounded
drained stdout and the closed failure classification — exposed under one public
name so a second workload does not grow a second copy of rules that keep a
credential inside one boundary. It answers the same closed
`ok`/`status`/`failure_reason`/`why` document `work` already consumes, and it
decides nothing: `ok` says the provider exited zero and says nothing about what
the provider did.

`tests/manager/test_integration_worker.py` drives it through the real adapter
with a recording process seam, and asserts the caller's prompt is the one
composed, the room is the working directory, the environment carries no ambient
credential variable and no ambient `HOME`, a failing turn publishes this
module's word rather than the provider's prose, and every refusal starts no
provider at all. One case asserts the four missing paths are **absent**, so a
reviewer reading a green suite does not have to take a prose sentence for it —
when one of them lands, that case fails, which is the reminder to bring its
proof with it.

One additive `parallel_test.py` registration. The second registration belongs to
the image suite and is not added, because that suite does not exist.

### Not delivered

`v12/worker/integration_workload.py`, `v12/worker/integration_entry.py`,
`v12/worker/Dockerfile.integration`, `tests/manager/test_integration_image.py`
and its registry entry are **not started**. The joined acceptance proof — an
accepted producer bundle carried through the real entry into a provider-driven
import of a disposable target, with independent byte and mode read-back, actual
result parsing, whole-path preflight refusal and a conservative partial or
uncertain hold — is **not built**. Nothing in this turn is evidence for any of
it. W110774 stays blocked and this Work is not complete.

### Verification

`tests.manager.test_integration_worker` — 10 passing, 0 failures.
`tests.manager.test_claude_agent` — **172 passing, unchanged**, which is the
check that matters for an additive edit to a shared accepted file.
`tests.tools.test_parallel_runner` — 36 tests, one error, the same pre-existing
registry gap reported throughout this campaign and unchanged here.

| Path | SHA-256 |
| --- | --- |
| `v12/worker/claude_agent.py` | `9a16f57c516660f2ccb2ad56fc404c91bc2c575bf3dd52970f64017b1ee29955` |
| `v12/python/tests/manager/test_integration_worker.py` | `047df6ff39ba413acaad3990ed9bad5379fbce27717534d7d90d8d71aa43c467` |
| `v12/python/tools/parallel_test.py` | `371ef8a507f94807c52e35f7cbd3f3df2efc0b3bd9157af8d7f622d2103e284c` |

The four accepted W112630 child files are byte-identical and were not touched.
No existing helper, action or assertion changed; the only edit to
`claude_agent.py` is the one new method. No version-control mutation of any kind
was performed.

**Canonical subtree gate: 4923 tests in 247.5s, 11 failures, 1 error, 21
skipped**, retained at `evidence/implementation-113322/subtree-gate.txt`. Handed
over red with the **distribution unchanged**: six boundary-inventory, four
live-engine cleanup, one authority-catalog, one registry error. The count moved
by exactly the 10 tests added. No new failure and no new diagnostic.

## 2026-09-07 — baton.claude — correction113398, the P2 and one wording error

Appended at review113415's request, which resolves the P2 and leaves no review
or owner approval pending for this correction.

**The absence assertion is removed.** `TheRemainingWorkloadIsNotBuilt` asserted
that the four planned files did not exist. It was mine, and the review is right
about what it was: a development status check wearing a product regression's
clothes, which would have rejected the completion of this very Work merely
because the scheduled artifacts existed, whatever their correctness. I added it
to stop a green suite reading as coverage; the dossier is where that belongs.
The one method, its class and its now-inapplicable docstring are gone and the
module docstring records why rather than leaving a silent deletion. The nine
wrapper and fixture methods and every pre-existing Claude-agent assertion are
untouched.

**Scheduled in its place**, when the workload lands: the positive real-entry
bundle-to-import-to-result path, independent byte and mode read-back, and the
negative whole-path preflight refusal and conservative partial/uncertain held
regressions.

**The signature is pinned concretely**: `invoke_provider(*, prompt, room)`
answering the closed `ok`/`status`/`failure_reason`/`why` document, both
operands keyword-only, `room` an absolute real directory of its own reached by
its own canonical name. `ok` means the provider exited zero and is not an
outcome.

**And one wording error of mine, corrected.** I wrote that the four accepted
W112630 child files are byte-identical. Three are; `tools/parallel_test.py`
carries this Work's own authorized additive registration and was never meant to
be.

Verified: `tests.manager.test_integration_worker` and
`tests.manager.test_claude_agent` together 181 passing, the adapter's 172
unchanged. No broad rerun for a one-method removal; the 4923-test gate at
`evidence/implementation-113322/subtree-gate.txt` remains the current broad
account with its historical reds unwaived.

## 2026-09-07 — baton.claude — claim113433, the concrete blocker

Review113425 asks that a handoff which cannot carry the complete candidate name
the concrete blocker and the required external action rather than repeat a
status. So, plainly:

**The blocker is this implementer turn's working capacity, and nothing in the
repository or the dossier.** The remaining deliverable is a greenfield build of
`integration_workload.py`, `integration_entry.py`, `Dockerfile.integration` and
`test_integration_image.py`, plus the joined acceptance proof that drives an
accepted producer bundle through the real entry with an injected provider
performing actual disposable-target edits, independent byte and mode read-back,
real result parsing, whole-path preflight refusal and a conservative
partial/uncertain hold. That is several files of new source and two new suites,
and it does not fit in the room remaining in this turn.

**Nothing else blocks it.** W112630's contract is accepted and closed, the
producer is available, the eight revalidation inputs match, the decisions are
pinned, the wrapper the workload will call exists and is reviewed, and the
authority to write all four paths plus the second registry entry is already
granted with no further planning approval needed. There is no missing owner
ruling, no unreadable file, no absent dependency and no external system to wait
on.

**The required external action is scheduling, not a decision:** hand the
remaining four paths and their joined proof to a fresh implementer turn with
room to complete them in one piece — or split them the way this campaign split
W112630 out of this Work, if a reviewer would rather see the workload and the
recipe/image suite accepted separately. Either is an ops choice; I am not
choosing it, and I flag the second only because the first attempt at a single
large deliverable is what produced this sequence of partial handbacks.

**The tree is left clean.** Nothing is half-written: all four remaining paths
are absent, and the three files this Work has touched are exactly the reviewed
bytes — `claude_agent.py`
`9a16f57c516660f2ccb2ad56fc404c91bc2c575bf3dd52970f64017b1ee29955`,
`test_integration_worker.py`
`95c3258c4265f55b6f33454934d9ae58f69a6692323a82be9e354566583cce62`,
`tools/parallel_test.py`
`371ef8a507f94807c52e35f7cbd3f3df2efc0b3bd9157af8d7f622d2103e284c`. No
version-control mutation of any kind was performed.

## 2026-09-07 — baton.claude — claim113568, scheduling disposition

Review113446 asks for a scheduling disposition and records that a one-turn
finish is not required: durable incremental work and context continuation are
allowed. My disposition, so the next turn starts from an answer rather than a
question:

**Accepted, and incremental is the right mode.** I am not asking for a new
ruling, a child Work or a scope change. The remaining scope stays cohesive as
the review recommends, and I will build it in this order, each step landing
complete with its own tests rather than as a partial file:

1. `integration_workload.py` — correlation of assignment, launch, profile and
   instructions against the envelope; the whole-path preflight; then the
   provider turn through the reviewed `invoke_provider`, the independent
   byte/mode read-back, the report check and the conservative outcome.
2. `integration_entry.py` — the composition that reads the delivery, runs the
   workload and publishes the result, kept to one readable act like
   `dogfood_entry.py`.
3. `Dockerfile.integration` — after the entry exists, because a recipe that
   copies a file nobody wrote is not a recipe.
4. `test_integration_image.py` and the second registry entry.

Steps 3 and 4 depend on step 2 and step 2 on step 1; that ordering is a real
dependency and not a preference, which is why no later path could have been
started first in the turns already spent.

**The joined proof travels with step 1 and 2**, not after them: an accepted
producer bundle through the real entry with an injected provider doing actual
disposable-target edits, independent byte and mode read-back, real result
parsing, whole-path preflight refusal and a conservative partial or uncertain
hold. I will not report the capability as delivered on any narrower evidence.

**What I did NOT do this turn, deliberately:** start `integration_workload.py`.
The room left in this turn would have produced a partial file with no tests,
and a half-written workload in the tree is worse than an honest handoff — it is
the one thing that would make the next turn's starting point worse rather than
better. The tree is unchanged from the reviewed hashes and all four remaining
paths are still absent.

No source or test changed in this turn; only this record.
