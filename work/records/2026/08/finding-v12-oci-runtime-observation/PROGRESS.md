# Progress

`PROGRESS.md` has one writer: the implementer (`baton.claude`).

## 2026-08-27 — claimed and implemented

Claimed W26294 at seq 27156. This is the second [P0] I reported while holding
W6636: `list_vector` is `ps --all`, `_attach` recorded `running` for anything
the label filter returned, and an exited container therefore satisfied
reconciliation exactly as a live one did. The adapter had `observe` all along
with nothing calling it.

Evidence: `evidence/w26294-2026-08-27-runtime-observation.txt`.
Harness: `evidence/w26294-mutation-harness.py`.
No Git history or index was mutated.

### PLAN 1 — revalidation found a blocker before any code changed

**The axis could not record what `observe` answers.** `execution_runtime` had no
transition from `start-requested` to `quiescent`, and none from `not-started`
either. So the truthful answer for a container that finished between the start
and the reconciliation was unrepresentable, and the manager would have had to go
on recording `running` for a container it had just been told is not.

That is now the *ordinary* case rather than an edge one: W26291 delivered the
launch environment, so the reference worker starts, finds no frames on a closed
stdin and exits cleanly within milliseconds. Both transitions are added, and the
map's own note already anticipated them — a reconciliation must be able to
record what it finds "including positive destruction".

`absent` maps to `destroyed` because it is **positive** evidence about one exact
identity: the adapter answers it only when the engine says that container does
not exist. What stays forbidden is inferring destruction from a failure to
*look*, and that is `uncertain`, which the map still refuses to let become
`destroyed`.

### The defect survived inside the fix for it, and a case caught that

My first version recorded the observed state **inside** `_attach`, where the
axis move already lived. That looked right — the existing comment explains, for
good reasons, why the move must be in the attachment's transaction.

It was wrong. `_attach` is effectively-once on `(attempt, runtime)`, so the
second reconciliation **replays** the first answer without running the action:
the state froze at whatever it was when the runtime was first attached, and a
container that exited afterwards stayed `running` forever. The diagnostic case
this Work was meant to convert **still passed**, which is what exposed it.

An observation is not part of an attachment. The identity is settled once and
the state changes underneath it, so the state is recorded by the caller on every
pass — and losing that write to a fault is now self-healing rather than
permanent. The returned document also carries the state just observed rather
than the attachment's stale one, which a replay would otherwise reproduce.

### The full gate found what a focused run could not

Adding a required capability broke a fake adapter in `test_boundary_inventory`,
and the probe-coverage cases cascaded off it: 7 failures became 21. Registering
the new seam then took three passes, each ~14 minutes, and each found something
real:

- the two receiving entries needed a probe **driver that reaches them** — my
  first one never started a runtime, so the fake listed nothing and
  reconciliation took the "nothing is listed" path without touching the
  boundary it named;
- the capability check sat in a private function the inventory's universe does
  not see, so it was an orphan call. It now lives at the public boundary beside
  the existing `list` check, which is also the shape `request_runtime_start`
  already uses — one place where both capabilities are proved before either is
  asked anything.

### Gates

- **9 mutations, all caught**
- full v12 tree — **1606 tests, 6 failures**

**The baseline is now six, not seven.** `check_input_pair`'s three receiving
parameters — the W19784 leftover I reported while holding W6636 and in every
Work since — have been registered in the contracts inventory by someone else,
and that check passes. The remaining six are `test_boundary_inventory`'s
long-accepted set, and my seam appears in none of them.

## State

PLAN 1–5 done. Passed for independent review rather than closed.

### For review

- The transition-map change is the one place this Work touched policy-adjacent
  state. It adds two *discoveries* (`quiescent` reachable from `not-started` and
  `start-requested`) and removes nothing; `uncertain` still cannot become
  `destroyed`. If review reads that as lifecycle policy rather than observation,
  it belongs to W6636 and I would rather be told.
- This Work establishes observation only. It does not retry, remove a runtime,
  discard output, release or reassign Work, or reinterpret uncertainty as
  absence — W6636 retains those consequences and now has four truthful states to
  act on.

## 2026-08-28 - the reviewed findings, corrected

Reclaimed W26294 at seq 30506. Both P0s reproduced on the tree first:

    observation failure leaves execution_runtime = running
    zero-listing decision = uncertain, observe calls = ['runtime-1']

### [P0] Positive absence was unreachable in normal operation

`_observed` ran only inside the one-candidate branch. So the ORDINARY shape --
the container removed, `ps --all` therefore empty, the attempt still holding
the exact immutable runtime id -- returned uncertain without asking the
adapter about the identity it already had. My own positive-absence case used a
listing that kept returning the runtime while observation said absent, which
is a possible race and is not the path that happens every time a container
ends. I proved a corner and called it the shape.

Reconciliation now takes the exact identity from the durable attachment, or
from `minted` when nothing is attached yet, and observes it. Only a
reconciliation that names no runtime at all remains unable to ask, and that
case is asserted too.

### [P0] A failed observation kept saying running

`_observed`'s docstring already said that a failed observation, an
unrecognised answer and a malformed one are all reasons to say uncertain. The
code raised instead, so the durable axis stayed where it was -- including
`running`. An observation that FAILED was indistinguishable from one that
answered liveness, which is this Work's own defect one level up. The docstring
was right and the code was not; now they agree.

The real-engine case meant to prove the opposite was inverted: it required a
refusal and then asserted only `not quiescent`, which stale `running`
satisfies. It asserts the durable uncertain now.

### Two decisions worth disagreeing with

**A failed observation still ATTACHES.** When the listing proved which runtime
this is, `decision` is about the attachment and `observed` is about the state
-- which is exactly what `runtime.attached` gaining `observed` was for. The
pair attached + uncertain is honest, and the durable axis is what must never
still say running. I wrote my first companion probe asserting
`decision == "uncertain"` and it failed; the assertion was my over-reach, not
the code's error, and I changed the assertion rather than the code.

**An inconclusive observation carries its reason.** `runtime.attached` gains
an OPTIONAL `why`, supplied only when the observation was inconclusive. A
state recorded with no reason is the confusion this Work exists to make
legible arriving in a different shape.

### What the measurement caught that I had not

The two boundary owners for the observation's members no longer propagate
their refusal, so their inventory probes stopped reaching a refusal. They are
registered in NO_PROBE with the reason: the rule still runs and still decides,
and a probe asserting the refusal ESCAPES would be asserting the defect the
correction removed. The behaviour is covered where it now lives.

And the harness reported two anchors matching twice rather than mutating
something else -- because the correction's second caller had duplicated the
record-and-return step. That is now one owner, `_settled`, and the harness
found the duplication before a reader would have.

### Gates

- test_attempts 92
- the observation harness -- **13 of 13 mutations caught**, four of them new
- tools/parallel_test.py -- 1568 tests, **6 failures, all in
  test_boundary_inventory**, the accepted baseline and none this Work's
- --phase serial -- 105 tests, 0 failures on a real daemon
- evidence/w26294-corrected-reproductions.py -- exit 0

### On the reviewer's reproduction file

Kept exactly as produced. Its first probe asserts the observation failure
PROPAGATES, which the required correction stops; its second asserts a zero
listing makes no second observe call, which the correction also stops. Both
were true of the defective tree. The corrected companion measures the same two
properties against the corrected behaviour, plus the one reconciliation that
still legitimately cannot ask.

No version-control history or index was mutated.

## 2026-08-28 — the re-review's [P1], corrected

Claimed W26294 at seq 30935. Evidence: `evidence/w26294-corrected-replay.py`.
The reviewer's `evidence/w26294-review-replay-reproduction.py` is kept
byte-for-byte. No Git history or index was mutated.

### Reproduced on the tree first

The reviewer's file runs and prints both stale shapes exactly as reported:

    running -> uncertain: {... 'observed': 'uncertain', 'runtime_id': 'runtime-1'}
    uncertain -> running:  {... 'observed': 'running', ..., 'why': 'the exact
                            runtime could not be observed: the original observer failed'}

### The fix is a rebuild, and the reason it had to be

`_settled` returned `{**attached, "observed": value}`. `_attach` is
effectively-once, so every pass after the first replays the FIRST pass's
document, and refreshing one member of a replay leaves every other member as
old as the attachment. That is worse than not refreshing at all: a reader
cannot tell which members describe now and which describe then.

The document is now composed from the two things true when it is answered —
the stable attachment identity, which is the one member a replay is genuinely
authoritative about, and this pass's observation. `runtime_id` is taken from
the attachment rather than from the caller's argument; the two are equal on
every path that reaches there, so **that particular choice is not
independently measurable** and no mutation claims otherwise. It is a statement
of provenance, and it is named here rather than counted as evidence.

`inconclusive` is now read once, from `value` — which is both what the axis
records and what the document publishes as `observed`. Deciding it from the
answered value is what makes the document consistent with itself rather than
with a variable a reader has to go and check.

A cancellation from `_attach` passes straight through. It answers a mismatch,
not an attachment; rebuilding it as one would have assembled a document its own
contract refuses.

### The correction opened a coverage hole, and the mutation harness found it

Making the answer independent of the stored attachment also left nothing
checking the stored attachment. It showed up as an existing mutation that
STOPPED being caught: dropping `why` from the `_attach` call changed no answer
any case looked at. The journalled document is what an exact retry replays and
what an operator reads out of the operation log, so
`test_the_recorded_attachment_keeps_the_reason_it_was_made_with` asserts it
through `store.replay` directly. The signal was a measurement going quiet
rather than a test going red, which is the harder one to notice.

### Measured, not read

- **all 17 mutations caught**, none expected-unseen — five added, including the
  one the review named (restoring the merge) and the two half-rebuild
  directions either side of it: a conclusive answer that keeps a reason, and an
  inconclusive one that explains nothing. A third breaks `inconclusive` itself,
  and a fourth rebuilds a cancellation as an attachment.
- against the PRE-FIX source: **3 of the 4 new cases fail**. The fourth is
  `test_the_recorded_attachment_keeps_the_reason_it_was_made_with`, which
  passes either way BY DESIGN — it exists to restore coverage the rebuild would
  otherwise have dropped, not to catch the defect. Named rather than counted.

### Gates

- `tests.manager.test_attempts` — 96 tests, OK
- full v12 parallel source — **1572 tests, 6 failures**, every one in
  `test_boundary_inventory` and none of them this Work's: the accepted baseline
  is unchanged, and no receiving entry was added or moved
- serial registry — **105 tests, 0 failed, 6 skipped**
- `evidence/w26294-corrected-replay.py` and
  `evidence/w26294-corrected-reproductions.py` — both OK, exit 0
- the reviewer's `w26294-review-replay-reproduction.py` now fails at its own
  `assert "why" not in answer`, which is the correction landing

## State

The re-reviewed [P1] is corrected and measured. Passed back for independent
review rather than closed.

### For review

- **`runtime_id` from the attachment is unmeasurable and said so above.** The
  attachment and the caller's argument are equal on every path that reaches the
  rebuild, so no mutation can distinguish them. If the reviewer wants that
  provenance enforced rather than merely expressed, it needs a shape where the
  two can differ, and this Work does not have one.
- **The four observations still map through `OBSERVED_RUNTIME` unchanged.** The
  rebuild moved where the document is assembled, not what any state means.
