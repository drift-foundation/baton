# Progress — directed requests wait by default

Owned exclusively by the implementer (`baton.claude` under v11).

## Step 1 — W159 implemented (2026-08-17)

Claimed W159. Revalidated the confirmed contract against the current
paths first: `post_thread` created the obligation, `set_phase` entered
the exact-obligation wait as a separate command, `_sweep_wakes` already
cleared that wait on resolution, and `_operation` fingerprinted the
carrier's inputs. Nothing about the wake path needed changing — only the
default and the atomicity.

### The blocking form

One transaction now publishes the Message, creates the obligation,
enters `waiting` on that exact obligation sequence, and releases the
claim. `Current` is deliberately untouched: the answer is owed TO the
current handler, not instead of it. The whole act consumes ONE sequence
and is pinned as such, because the defect being fixed is precisely the
window between two commits.

Authorization needed more than the carrying `_select_target` gate that
was already there. Suspending Work is a workflow act, so the blocking
form additionally requires the actor to HOLD that Work's active claim.
Without it, any eligible route handler could park work out from under
the participant actually executing it.

### A branch I wrote and then removed

I first added a refusal for a Work already `waiting` or `parked`. It is
unreachable: entering either phase releases the claim, so such a Work is
necessarily unclaimed and the claim gate refuses first. The test that
would have covered it now documents WHY no phase test exists, so the
next reader does not add one back. Dead defensive code reads as a
guarantee it is not making.

### The asynchronous override

`wait=false` publishes and creates the obligation and changes nothing
else — phase, claim, Current, and wait condition are all asserted
byte-identical before and after. `wait=` without `request=` refuses, in
both the authority and the grammar's own condition.

### Grammar

`say` gained `wait=`, and the CLI gained a genuine two-valued `boolean`
operand kind alongside the existing true-only FLAG kind. They are kept
separate deliberately: `wait=false` has to be sayable, while
`create=false` on `accept` must stay meaningless rather than silently
satisfying its exactly-one-of condition.

Effectively-once identity uses the EFFECTIVE boolean, so an exact retry
may spell the default explicitly while flipping it fails closed.

### Evidence

New `tests/work/test_w159_request_waits.py` (15): the blocking default
in both spellings, with Current pinned unmoved and the obligation
actionable for the asked endpoint; the one-sequence atomicity and the
effective value in event evidence; respond, dispose and BOTH resolutions
waking the exact waiter exactly once; an unrelated resolution not waking
it; `wait=false` leaving state byte-identical while still creating the
obligation; every refusal proven to commit nothing — `wait=` without a
request, a malformed boolean through the real CLI, an unclaimed Work, and
somebody else's claim; retry replay and conflicting-flip failure; the
canonical JSON waiting condition and the Events journal showing the
choice and released claimant; and the grammar advertising it so the
choice never has to be inferred from omission.

Break-sweeps: defaulting to asynchronous reds 10; dropping the
claim-ownership gate reds 1; removing the effective value from retry
identity reds 1.

## Step 2 — the collateral call sites (2026-08-17)

No ruling arrived on the scope question raised at v11 sequence 182, but
the W101 handoff sequenced that Work "after finishing the current W159
shared tree batch", and the unresolved default was blocking every
downstream item. I therefore proceeded with option (A) — stating the
historical intent explicitly at the affected call sites — rather than
leaving the tree red. Option (B), revising the contract's unclaimed
case, would be Slawomir's to make and is not foreclosed by this.

The argument for (A) is that it is not a weakening. Every affected call
site was written when a directed request was asynchronous, and each one
exercises obligation mechanics rather than the blocking form. Adding
`wait=false` states what those tests always meant; it does not relax
what they check.

Applied in three places:

- `fixtures.post` sets `wait=False` for carrying calls that do not
  choose, with a comment saying WHY — those call sites predate the rule
  and mean the asynchronous ask. A caller that means the blocking form
  passes `wait=True`, and W159's own tests call `post_thread` directly
  so they exercise the real default.
- CLI-operand call sites across 17 files gained an explicit
  `wait=false` token.
- Direct `post_thread` call sites across 11 files gained `wait=False`.

### Two things the mechanical pass got wrong

A regex inserted `"wait=false"` into `test_wf07`'s list of MALFORMED
request tokens — a refusal loop, not a command — so it became a token
under test rather than an operand. Caught because the refusal message
changed from "exactly one" to the new `wait=` diagnostic, and repaired.

A packaged-console call built its operands in one f-string
(`f'request=push.bug on={epic}'`), which the pattern did not match, so
that site was fixed by hand.

Both are worth recording because they are the failure mode of a
mechanical sweep across 39 files: it edits text, not meaning, and the
places it is wrong are the places the text looked the same but meant
something else.

### Gate

`just test-v11`: **993 passed + 4 serial + acp 35/35**, on the 32
available cores. That is the first fully clean whole-tree gate since
this Work began; the earlier isolation runs (983 passing with only
W159's own tests failing) are now superseded by a real one.

## Step 3 — W159 R1-R4 (2026-08-17)

**R1 — an invalid spelling replayed a valid post.** Real, and mine.
`post_thread` consulted `_operation` before rejecting `wait=` without
`request=`. For a plain post the effective value collapses to false
whether `wait` was absent or explicitly supplied, so the fingerprints
matched and an invalid retry REPLAYED instead of refusing — an invalid
spelling accepted because its meaning happened to be unreachable. The
conditional grammar is now validated before the replay lookup, and the
later duplicate check (now unreachable) was removed rather than left as
dead defence. Omitted-versus-explicit-true equivalence for an actual
request is unchanged, which is the equivalence the ruling asks for.

**R2 — the default had no public proof, and WS3 preserved the defect.**
Both correct. `test_ws3_wf01` and `test_ws3_wf02` said the consumer
"waits" while publishing asynchronously and then issuing the retired
second `phase to=waiting wait=<obligation>` command — the exact
two-command race W159 removes, kept alive by my own collateral sweep.
Both are migrated to claim-then-ask in ONE act, asserting the waiting
phase, the exact obligation, the released claim, and unmoved Current.

New `tests/work/workflows/test_wf15_request_waits.py` proves the
contract through the PUBLIC JSON CLI in source and packaged lanes: the
one-sequence atomicity, the exact wait, the released claim, unmoved
Current, the actionable obligation, the Events evidence, and the single
wake on `respond`; `wait=false` as the deliberate contrast; and the
public refusals for an unclaimed target, `wait=` without a request, and
a malformed boolean.

I audited the remaining mechanical `wait=false` additions as instructed.
Only `test_wf05` also says "waits", and there it refers to an unrelated
dependency blocker — those consumers genuinely continue, so the override
is right. No other site was wrongly migrated.

**R3 — atomicity and race evidence.** The exploding-connection pattern
now covers the BLOCKING branch: every write boundary is faulted in turn
and each must restore a byte-identical database, identical events,
identical phase/wait/claim, and no operation receipt; the test asserts
at least three boundaries were actually exercised, so it cannot pass by
faulting once and stopping. The committed act then replays across a
restart. Added serialization proof: a release that wins first makes the
blocking request refuse without stranding a waiter, and competing
response/dispose against one obligation commit exactly once with one
wake, one Message, and one episode.

**R4 — cross-surface acceptance.** This found a real gap beyond `wait=`.
The assistance offered every optional key regardless of its declared
condition, so `wait=` appeared on a plain `say` — and so did `on=`,
which has had the same unmet condition all along. `analyze_partial` now
withholds a conditional key until its requirement is actually present,
which is the documented promise (form conditions applied exactly as the
parser enforces them) and fixes both keys from one declarative rule.
Added a console test that drives the real command path and proves the
user-facing mutation produces the same waiting, unclaimed,
exact-obligation facts as canonical JSON and Events.

**One existing test corrected, declared.**
`test_partial_analysis_speaks_the_execution_tokenizer` asserted `on=`
appears on a plain `say`. That assertion was incidental to its purpose —
proving quoted text invents no keys — and is now stated with the
unconditional keys, plus an explicit assertion that the conditional pair
is absent. `test_assist_applies_the_parsers_condition_model` gained the
positive and negative forms for both keys.

Break-sweeps: moving validation back after the replay lookup reds 2;
offering conditional keys regardless of requirement reds 3.

Gate: 1019 passed + 4 serial + acp 35/35 on the 32 available cores;
diff --check clean.

## Step 4 — W159 R5 (2026-08-18)

The finding's acceptance boundary names JSON RESULTS separately from
Events, and I had only covered Events. `finish(result)` decorated the
public `say` result with `included` and `work`, so a blocking request
and an asynchronous one returned the identical shape: an operator had to
read the journal back to learn whether their own Work was now suspended.
That is inference from omission, which is exactly what the boundary
forbids.

The committed and replayed result now carries the effective Boolean for
a directed request. A plain message still carries no `wait` key at all —
omission used deliberately, because a message with no request has
nothing to wait on and a `false` there would be a misleading answer to a
question nobody asked. Both halves are pinned.

Evidence: parametrised result assertions for omitted, explicit true, and
explicit false, each cross-checked against what actually happened to the
Work; a plain-message test asserting the key is ABSENT; a protected
replay test proving the stored result round-trips identically rather
than being recomputed; and public assertions in the WF-15 workflow for
both forms plus the plain contrast, in source and packaged lanes.

Break-sweep: omitting the echo reds 9.

Gate: 1031 passed + 4 serial + acp 35/35 on 32 cores; diff --check clean.
