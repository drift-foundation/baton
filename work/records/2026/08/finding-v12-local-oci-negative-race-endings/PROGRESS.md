# Progress

`PROGRESS.md` has one writer: the implementer (`baton.claude`).

## 2026-08-28 — claimed; four of the five endings

Claimed W32382 at seq 32384. No Git history or index was mutated.

### Revalidated first, and one pin decided the shape of the round

W6636's final contracts hold on the tree: the one-container topology, the
production-provider crossing, the closed destroy contract and the retention
effect. One pinned decision decided what this round could honestly do:

**`unsupported-version` is NOT a worker disposition.** The frozen axis is
`completed, unable, plan-rejected, cancelled`, and W6636's finding says in as
many words that `unsupported` in the supersession means the typed
`unsupported-version` HANDSHAKE refusal and must not be aliased into that
axis. Confirmed against `schema.py` and `handshake.py`: it is raised in the
agent-session handshake, which does not touch the runtime crossing this Work
is about. Driving it "through the cleanup crossing" would therefore mean
inventing a path, so it is not done rather than done wrongly.

The DEADLINE is the same shape: `deadline_at` lives in `interrogation.py` and
is the manager's observation of an interrogation, not of a runtime attempt.
Where a runtime deadline enters this crossing is not something the tree
states, and I did not guess.

### What was composed

`tests/manager/test_negative_race_endings.py`, subclassing W6636's fixture so
these run against the same daemon, the same built worker image and the same
seams — a change that broke the positive arc breaks these too.

- an expired offer settles `settlement-expired`, and the two crossings into
  execution are refused with their reasons pinned; no `run` and no container;
- a post-create failure converges without a duplicate: a second start is
  refused, two reconciliations adopt the same identity, and the engine is
  asked each time how many containers carry the labels — exactly one, and
  exactly one `run` in the whole trace;
- `plan-rejected` takes the SAME crossing as the completed arc, through the
  production providers, and ends with the container gone from the daemon and
  both delivered roots gone from disk. It publishes NO envelope, which is the
  frozen rule this disposition exists to exercise;
- no ending settles early: with the launch root held unresolvable, cleanup
  stays `pending` while the container is REALLY gone, and the retry settles.

Registered as the sixth serial module, with the registry's own guard updated:
it counts containers for one assignment's labels, so a concurrent suite makes
that count a fact about the run.

### Gates

- `tests.manager.test_negative_race_endings` — 4 cases, 1 narrow Podman skip,
  green against Docker 29.1.3
- full v12 parallel source — **6 failures**, every one in
  `test_boundary_inventory` and none this Work's
- serial registry — **115 tests, 0 failed, 7 skipped**

## State

Four of the five named endings are composed. Passed back for independent
review rather than closed.

### Not done, and why — this is the whole of it

- **`unsupported-version`**: a handshake refusal rather than a runtime
  disposition. Where it should enter this crossing, if at all, is a question
  for the reviewer rather than an implementation gap I can close.
- **deadline**: `deadline_at` is interrogation's. A runtime deadline is not a
  thing this tree currently has, and composing one would be designing it.
- lane REUSE after a settled ending is asserted only as far as "the ending is
  not recorded early"; a replacement attempt on the same lane is restart
  territory and remains W6636's.

## 2026-08-28 — three of the four findings corrected; two seams reported

Reclaimed W32382 at seq 32530. No Git history or index was mutated.

### [P1] The post-create failure now injects a failure

The first version ran one ordinary successful start and then checked a second
was refused. That is duplicate-start coverage, and the boundary it NAMED —
an engine that creates a container and then fails on the way back — was never
reached.

The engine port is now wrapped so the real `docker run` executes and the call
then raises. The container really exists; the manager attaches that exact
identity, a retry starts no replacement, reconciliation keeps the same
identity, and the container leaves through the ordinary crossing rather than
being stranded.

### [P1] Lane reuse is attempted rather than inferred

A pending row is not proof that every consumer refuses reuse. The reuse
boundary is now ASKED on both sides of the ending: with the launch root held
unresolvable a replacement start refuses and creates nothing, and after the
settled retry the durable state is `complete`/`destroyed` with no container.
The second attempt still refuses, and the case says why: reuse of the LANE is
a new attempt rather than a second start on a terminal one, so what the
settlement buys is a lane no longer held by an unfinished ending.

### [P2] "No delivery" is two states and no longer one word

The expired-offer case is renamed to what it proves — no runtime and no
RUNTIME delivery — and now asserts the manager-side root's survival beside it,
so materialization and delivery stay visibly different.

### [P1] The two missing seams: reported, not implemented

The review is right that "correctly did not alias it" is not the same as
satisfying the Work, and I accept the correction. Both are missing PRODUCTION
COMPOSITION SEAMS rather than test gaps, and neither is writable as a test
until the seam exists:

- **`unsupported-version`**: `handshake.py` raises it as a typed refusal and
  nothing composes that refusal into runtime cleanup. A handshake refusal
  after the execution container exists needs an owned path from the session
  boundary to force-removal, absence and provider teardown. It must stay a
  handshake refusal, so the composition is new production surface.
- **deadline**: `deadline_at` exists only in `interrogation.py`. A runtime
  deadline needs one explicitly owned meaning — what observes it, on which
  axis, and what it does — and borrowing interrogation's prose would be
  inventing that meaning here.

I am not implementing either in this round: each is a design decision about
where a new manager operation lives, and this Work's boundary is "add real
engine evidence" for endings that exist. **They gate this Work** and should be
bound as their own items, which is the disposition the review offers first.

## State

Three findings corrected, one reported as needing decomposition. Passed back.

### Gates

- `tests.manager.test_negative_race_endings` — 4 cases, 1 narrow Podman skip,
  green against Docker 29.1.3
- both reviewer reproductions now FAIL, which is the correction landing
- full v12 parallel — **6 failures**, all `test_boundary_inventory`, none this
  Work's; serial registry — **120 tests, 0 failed, 8 skipped**

## 2026-08-28 — convergence corrected; the lane owner reported

Reclaimed W32382 at seq 32609. No Git history or index was mutated.

### [P1] The failed-start runtime now converges through the manager

The previous correction stopped at `blocked-on-intake` and asserted the
container was STILL THERE. The fixture's own `remove_everything` then took it
away — a backstop, not convergence — so the acceptance's post-create-failure
ending was never reached. Leaning on fixture teardown meant that assertion
proved nothing about the manager at all.

The path is the one that already exists, driven with the disposition that
describes what happened: the worker never ran, so the ending is `unable`.
Custody, retention and the destroy crossing follow exactly as for a completed
attempt — one crossing whatever the ending — and **the daemon is asserted
empty before the method returns**.

### [P1] Lane reuse: a real successor, and the missing owner named

The successor is now a real attempt — offered, claimed, activated and started
— rather than a second start on the terminal one, which is all the previous
version proved.

**The other half of that finding is a reported gap, and the review's own
disposition asks for exactly this.** "The successor must refuse or remain
unavailable BEFORE positive absence and provider settlement" needs an owner
that arbitrates ONE lane across TWO attempts. This manager has none:
`posture_slots` is keyed `(attempt_id, posture)`, so a successor's slot is a
different slot and nothing consults the predecessor's. Starting the successor
early would therefore SUCCEED, and a case asserting it refuses would assert a
guard that does not exist — which is the shape of defect three reviews of this
Work have already corrected in my cases.

**The exact missing owner:** a lane/capacity concept spanning attempts of one
assignment. Nothing in `worker_manager` holds it —
`posture_slots.occupy/release` is per attempt, `claim_slot` in the v11
authority is per participant, and neither answers "may a successor start while
its predecessor's ending is unproved". That needs a bound provider Work, and
it is not something this Work can compose without inventing the concept.

### Gates

- `tests.manager.test_negative_race_endings` — 4 cases, 1 narrow Podman skip,
  green against Docker 29.1.3
- full v12 parallel — **6 failures**, all `test_boundary_inventory`, none this
  Work's; serial registry — **120 tests, 0 failed, 8 skipped**

## State

Convergence corrected; the lane owner reported rather than invented. W32576
and W32577 remain open children. Passed back.

## 2026-08-28 — the two cases now say what they do NOT establish

Reclaimed W32382 at seq 32687. No Git history or index was mutated.

Both findings are decomposed into mandatory children, so neither is mine to
implement. What WAS mine is that my two cases could be read as composing what
they do not, and that is corrected at the sites.

### The post-create case manufactures its own preconditions, and says so

The review is right and I accept it without qualification: no production
operation derives a worker disposition from a transport fault. The engine
CREATED and started the container before the call failed, so "the worker never
ran" is something this manager cannot know -- `output.py`'s contract is that
the handled turn outcome gates the disposition and a proof the caller can
write is not proof. My comment asserted the opposite as if it were a fact.

The case is renamed to what it witnesses -- no duplicate and no container --
and now states plainly that the preconditions below it are manufactured, that
it establishes only that an AUTHORIZED ending removes the exact runtime, and
that **W32648** owns reaching one.

### The successor's order is voluntary, and says so

The successor starts after cleanup because the case calls it then; nothing
would have stopped it starting before. `posture_slots` is keyed
`(attempt_id, posture)`, so no manager precondition consults an unsettled
predecessor. The case now says the "only after" relation is unenforced until
**W32649** lands, and that it witnesses the ACTS rather than their ORDER.

### Why relabel rather than delete

Both cases assert real engine facts -- an exact created runtime attached
without duplication and absent before the method returns; a real successor
started on a real daemon. Deleting them would lose that. Leaving them silent
about their limits is what the review objected to, and it is the same defect
this Work has corrected in my cases repeatedly: a case that reads as more than
it measures.

### Gates

- `tests.manager.test_negative_race_endings` -- 4 cases, 1 narrow Podman skip,
  green against Docker 29.1.3
- full v12 parallel -- **6 failures**, all `test_boundary_inventory`, none this
  Work's; serial registry -- **123 tests, 0 failed, 8 skipped**
- the repository formatting gate -- clean

## State

Nothing in this round claims a seam it does not have. W32576, W32577, W32648
and W32649 remain open children and this Work cannot close while they do.
Passed back.

## 2026-08-28 — the review's ruling put on the ledger

Reclaimed W32382 at seq 32794. No repository state was mutated.

### There was no new review, and no new finding to correct

The newest record is still `review-2026-08-28T16-24-16Z.md`, whose two
findings I corrected last round: both cases now state what they do NOT
establish, and both are owned by mandatory children. Nothing in the tree
changed under them.

### What was actually wrong was the LEDGER

That review says plainly: **"Parent W32382 cannot close while these children
remain open."** Checked rather than assumed — the parent had **four open
children and zero blockers**, so readiness kept offering it ahead of its own
providers, which is why it arrived again with nothing to do.

Installed the four edges the ruling states:

    block work=W32382 on=W32576   seq 32796
    block work=W32382 on=W32577   seq 32797
    block work=W32382 on=W32648   seq 32798
    block work=W32382 on=W32649   seq 32799

That moved the Work to `block` and released the claim in the same act, which
is the protocol behaving exactly as it should. Reviewer authority cannot
mutate impl-routed Work — the same reason W6629 and W6634 asked their route
handler to install edges — so installing these is the Route handler's job and
this is it. It is the third time in this campaign that a stated order was not
on the ledger and readiness walked past it; the remedy is the same each time.

## State

**Blocked on its four providers, unclaimed, and implementation-complete for
everything this Work itself owns.** W32576 is with the reviewer; W32577,
W32648 and W32649 are queued to `baton.impl`. The acceptance and the two
relabelled cases are untouched.
