# Reclaim custody helpers after manager interruption

Work: W43974
Parent: W36540 (`work/records/2026/08/finding-v12-worker-custody-provider/`)

## Purpose

Make the custody helper's lifetime bounded, its identity derivable, and a
helper stranded by an interrupted manager reclaimable — so `CUSTODY_NAME`
becomes load-bearing rather than a constant the record mentions and no code
reads.

## Confirmed boundary (from the parent, and unchanged here)

- One mount, the exact attempt directory, derived inside the act from durable
  state. This child changes nothing about `_derived_root`.
- Typed manager-owned verbs only; no worker-supplied command.
- No host path and no executable vector crosses back to a caller.
- The answer contract of the eleventh round stands: a document is accounted
  for only as the requested verb's own closed typed result or as the
  custodian's typed refusal.

## 2026-08-30 — implementation revalidation (`baton.claude`, W43974 impl claim)

### Confirmed against the current tree

Every observation in the parent `PLAN.md`'s W43974 enrichment holds:

- `_custody_vector` takes `name` as an ordinary caller operand, validated only
  for shape by `_NAME`. Nothing derives it.
- `CUSTODY_NAME = "baton-custody"` is referenced by no code path.
- The vector composes `--rm` and runs foreground, which reclaims only on the
  engine's normal completion path.
- `EnginePort.__call__` imposes no deadline; the injected `run` capability
  owns whatever bound exists (the engine cases use `subprocess.run(timeout=)`).

### Confirmed reusable seams

`oci.py` already owns `inspect_vector`, `stop_vector`, `destroy_vector`, the
per-engine absence sentences behind `_absent_prose`, and the listing
vocabulary `_decoded` / `_one_of` / `_LISTED_IMAGE` / `_image_identity`. It
also already states the rule this child needs most, at `OciAdapter.list`:
**engine-side selection is not proof that a returned row has the values
requested.**

### Pinned: the helper's identity is DERIVED, and `name` stops being an operand

**Superseded:** the parent's `name` operand on `custody_act` and
`_custody_vector`. A name a caller chooses is a name a restarted manager
cannot re-derive, so the reclamation this Work owes was impossible by
construction — there was nothing to look for.

**The rule now:** the identity is
`CUSTODY_NAME + "-" + digest({store, assignment_id, which, operation})`,
truncated to the module's own `_NAME` bound, and it is composed inside the act
from the same durable read `_derived_root` already performs. It is derivable
by any manager that can open the store, which is what makes restart
reclamation possible; and it is not a caller operand, which is the parent's
own no-interval rule applied to the one operand that had survived it.

The configured workspace store is in the digest because the identity must be
unique to a DEPLOYMENT and not merely to an attempt: two managers on one host
with different stores may hold the same attempt name. It is a digest input and
never appears in the name, the answer or any diagnostic.

### Pinned: a stranded helper is ENDED and the act redone, never adopted

The enrichment offers adopt, await or remove. **Adoption is not available and
the reason is structural rather than a preference:** a custody answer is the
document the helper printed to the stdout THIS manager held. A helper started
by a process that has since died printed to a pipe nobody holds, so its answer
is unrecoverable — attaching to a running container's stdout yields what it
writes from now on, not what it already said. There is nothing to adopt.

Awaiting is the same problem with a delay in front of it.

**So the reconciliation ends the stranded helper and performs the act again.**
That is sound because every verb in the vocabulary is safe to interrupt and
repeat: `normalize` and `discard` are idempotent in effect, and `inspect`,
`read`, `hash` and `archive` write nothing. A partially completed `discard`
that is re-run completes; a partially completed `normalize` re-run normalizes
what is left.

### Pinned: the state table, and every uncertain branch fails closed

Reconciliation happens before launch, against the exact derived identity:

| observed | decision |
| --- | --- |
| no candidate | launch |
| one candidate, image is this act's | end it, prove absence, launch |
| one candidate, image is not this act's | REFUSE |
| more than one candidate | REFUSE |
| the listing failed | REFUSE |
| absence unproved after removal | REFUSE |

**The listing filter narrows and never decides.** The engine is asked for
candidates whose name CONTAINS the derived identity, and every returned row is
then compared for exact name equality here. A substring filter can over-match
and cannot under-match on either engine, so a same-prefix stranger is returned
and then rejected by this module rather than by the daemon — which is
`OciAdapter.list`'s own rule, applied to a selector that is not a label.
An anchored regex filter was rejected: an engine that does not honour anchors
returns nothing, and a false ABSENCE is the one answer this must never
produce.

### Pinned: two deadlines, each at the layer that can enforce one

**Superseded:** the parent's position that helper boundedness is open. It is
bounded here in two places, because one place cannot see both failures.

1. **Inside the custodian.** `CUSTODY_SECONDS` is compiled into
   `CUSTODY_PROGRAM`, which arms `signal.alarm` and, on expiry, prints its own
   typed refusal and exits non-zero. This is manager-owned — the number is
   this module's constant travelling inside the program the manager ships —
   and it bounds the act's own work at the place doing it, with no engine
   feature required.
2. **Around the call.** Whatever ends the wait — the injected run capability's
   own transport timeout, or any other failure raised out of the port —
   `custody_act` catches it, performs reclamation against the derived
   identity, and answers a typed timeout rather than escaping. The manager
   does not own that number yet; `EnginePort` still imposes no deadline, and
   giving it one is a shared change this child deliberately does not make.
   What this child guarantees is that no ending leaves an unreclaimed helper
   whose identity nobody can derive.

### Pinned: an engine acknowledgement is not absence

Removal orders `stop`, then `rm --force`, then INSPECTS the exact identity and
requires this engine's own absence sentence to name it. `oci._absent_prose` is
reused rather than re-expressed, and an inspect that neither succeeds nor
produces that sentence leaves the reclamation UNRESOLVED and refuses.

## Acceptance

- The helper identity is derived, restart-derivable, and is not a caller
  operand anywhere on the public surface.
- Normal completion still reclaims through `--rm` with no extra engine calls.
- A stranded helper — running or exited — is found by a fresh manager, ended,
  proved absent, and the act redone.
- Ambiguity, a contradictory image, a failed listing and an unproved absence
  each refuse rather than launch.
- A same-prefix stranger is returned by the filter and left untouched.
- Each of the six verbs is safe to retry through this path.
- The in-custodian deadline is proved against the real program.

## 2026-08-30 — what the real daemon changed, during implementation

### Superseded before it shipped: the image comes from `inspect`, not the listing

The state table above was written to read the candidate's image out of the
`ps` listing, the way `OciAdapter.list` reads it for a runtime. **Running it
against a real Docker daemon refused every reclamation**, and the refusal was
correct:

    a listed helper's image is 'baton-w6636-lifecycle:e4cc3effd8c6', which is
    not an image digest; an engine that cannot name the image by digest has
    not said which image is running

`docker ps --format {{json .}}` answers `Image` as the TAG the container was
started from. `_LISTED_IMAGE` reads `ImageID`/`ImageId`/`Image` in that order,
and `ps` carries none of the first two — so the fallback landed on a tag, and
`_image_identity` refuses a tag on purpose, because a tag is a pointer that
was true when somebody last pushed.

**The rule now:** the listing SELECTS and the container's own `inspect` record
IDENTIFIES. Once one exact-name candidate exists, it is inspected, and the
image digest and the name are both read from that record. It costs one engine
call and only when there is something to reclaim; the ordinary act still asks
the engine exactly `ps` and `run`.

Two branches came out of that inspect and both are in the table now:

- **inspect proves the candidate ABSENT** — it ended between the two questions,
  which is the state the reclamation was trying to reach. Not an error; the
  act proceeds.
- **inspect neither succeeds nor proves absence** — refuse. Neither present nor
  provably absent is not a state to launch in.

And the record's own `Name` is compared against the identity that selected it,
which is `OciAdapter.list`'s rule ("engine-side selection is not proof")
applied to the second question as well as the first.

This is recorded rather than quietly folded in because it is the one thing in
this child that inspection could not have settled, and the parent record has
now been taught the same lesson twice — the first time when a build gate found
a seam defect no recipe review had seen.

## 2026-08-30 — second round, after `review-2026-08-30T05-15-08Z.md`

### Superseded: "an `EnginePort` deadline is out of scope" was the wrong answer

The first round bounded the act inside the custodian and named the manager-side
bound out of scope, on the ground that `EnginePort` is a shared seam. The review
is right that this left the child's central acceptance unmet: `CUSTODY_SECONDS`
starts when the custodian's Python program starts, so it bounds the act and
nothing before it — a stalled image pull, a daemon that never answers, a result
lost after launch. And an optional timeout carried by whatever the deployment
injected is not a property this module owns or can assert.

**The rule now: custody owns the bound, and enforces it itself.** `_bounded`
runs each engine call on a daemon thread and waits `seconds` for it.
`CUSTODY_ACT_SECONDS` bounds the act; `CUSTODY_RECLAIM_SECONDS` bounds every
listing, inspection, stop and removal — reclamation is what runs when something
has already gone wrong, so an unbounded call there is the same failure one
layer in.

Requiring the injected capability to ACCEPT a deadline operand was considered
and rejected: a capability may take an operand and ignore it, which is the same
"chosen by the injector" property the review refuses. The shared seam is still
not changed, and it no longer needs to be.

**What the thread buys, stated exactly, because it is less than it looks.** On
expiry the underlying call is NOT cancelled — nothing here can cancel a
synchronous callable this module did not write. What happens is that custody
stops waiting and reclaims the helper by its derived identity, and removing the
container is what actually ends the engine call, after which the thread
finishes. It is a daemon thread, so a stalled engine cannot hold the
interpreter open.

`CUSTODY_ACT_SECONDS` is deliberately LARGER than `CUSTODY_SECONDS`. The inner
alarm is how an overrun is ordinarily reported, because it is typed and names
the bound it crossed; the outer is the backstop for a call that never reaches
the program. Equal bounds would race, and an ordinary slow act would come back
as a lost one.

`CustodyDeadline` is deliberately not a `ContractRefusal`: nothing has been
judged and no contract broken. It says only that this manager stopped waiting.

### Superseded: the exception's CLASS decided whether the helper had run

The first round re-raised `ContractRefusal` untouched, on the reasoning that a
refusal happens before anything runs. **`EnginePort.__call__` invokes the
injected capability and validates the answer AFTERWARDS**, so a malformed
engine answer is a refusal that arrives with the helper already launched — and
that helper was left unreconciled.

**The rule now: every ending that is not an engine answer goes through
recovery, and the exception's class decides nothing about whether the helper
ran.** A genuinely pre-invocation refusal is harmless on that path: recovery
finds nothing and does nothing.

What the class still decides is how the ending is REPORTED. A `ContractRefusal`
is this manager's own judgement and propagates as one; `KeyboardInterrupt` and
`SystemExit` are the operator ending the process and are not this module's to
swallow into a custody answer. Both are re-raised — after the helper has been
reclaimed, which is not conditional. The first round's `except BaseException`
that turned every ending into a typed result is superseded.

### Superseded: recovery removed by name before identifying anything

The first round called the removal with the derived NAME as the runtime id, so
the exceptional path — the one that runs when something has already gone
wrong — ordered a stop and a force-remove against whatever answered to that
name, having never identified it. `_reconciled` already treats a derived name
as DISCOVERY rather than authority, and recovery skipped that rule entirely.

**The rule now: recovery asks the same question the launch did.** List, match
the exact name, inspect, hold the image and the name. Only a candidate
identified as this act's helper is removed; a contradiction refuses without
sending `rm`; and nothing found is not the end of it either — see below.

### Pinned: nothing listed is not absence, on the recovery path

The launch path may treat an empty listing as nothing-there, because
`run --name` fails closed on a conflict if the listing was wrong. **Recovery
has no such backstop** — it would conclude the helper was reclaimed on the
strength of a filter that returned no rows — so it proves absence through the
engine's own sentence naming the identity, which is the same proof a removal
must pass. `_proved_absent` is that one proof, used by both.

### The reviewer's two regressions contradicted each other, and which gave way

`test_a_post_invocation_contract_refusal_still_reclaims_the_helper` asserted
the sequence `ps, run, stop, rm, inspect` — a removal ordered against a helper
nothing had identified, which is exactly what the same review's third finding
forbids. `test_lost_act_does_not_remove_a_same_name_replacement` requires the
opposite and is the one that states the rule.

The first case's expected sequence is now `ps, run, ps, inspect` and its stated
requirement is met exactly: the refusal propagates, and it propagates only
after the derived helper is PROVED absent — by the engine's own absence
sentence, which is stronger than the empty listing the original sequence would
have accepted before ordering a removal anyway.

## 2026-08-30 — third round, after `review-2026-08-30T05-28-16Z.md`

### Superseded: bounding the WAIT is not bounding the engine operation

The second round ran each engine call on a daemon thread and abandoned it on
expiry. **That bounded the wait and nothing else.** The review is right, and
the consequence is worse than "incomplete": the abandoned call was free to
finish a stalled image pull and create the helper AFTER recovery had listed,
inspected and proved that exact name absent — so the deadline manufactured
exactly the stranded helper this child exists to prevent.

A thread this manager stops waiting for is not a cancelled engine operation
and not a reaped OS child. Nothing inside this process can cancel a
synchronous callable it did not write; the party that spawned the child is the
only one that can end it.

**The rule now: the deadline lives at the engine boundary, and the call is
OVER by the time it returns or raises.** `EnginePort.__call__` takes an
optional `seconds` and forwards it to the capability. The capability's
contract is that it has TERMINATED AND REAPED its child before answering —
which is exactly `subprocess.run(argv, timeout=seconds)`, and which leaves no
interval afterwards for a late mutation to happen in, because nothing is still
running.

`CustodyDeadline` and the thread watchdog are DELETED rather than kept beside
the new path, and a case asserts their absence so re-introducing one is a
deliberate act.

### The shared change, made rather than blocked, and why

The review permitted an explicit blocker if a shared engine-provider change
were required. One is: `EnginePort.__call__` gained `seconds=None`. It is
additive and forwarded only when given, so every caller that passes nothing
invokes its capability exactly as before and no other adapter is disturbed.
Five lines in the one place that owns invocation seemed a poorer candidate for
a blocking dependency than for a reviewed change inside this child — but the
choice belongs to the reviewer, and splitting it out remains available.

### What this manager still cannot verify, said plainly

A capability that ACCEPTS `seconds` and ignores it. That is the same class of
trust as handing it an argv and believing it ran that argv, and it is the
trust boundary `EnginePort` has always been. What changed is that honouring
the deadline is part of the contract instead of an optional kindness.

### Pinned: the wrong-shaped capability is refused on a READ

A pre-flight signature check was written and removed: `inspect` is not in the
manager's ruled dependency set, and `test_dependencies` caught it immediately.
Adding a stdlib module to that allowlist to gain a check the first call
already performs is the wrong trade — the act's FIRST call is the read-only
reconciliation listing, so a capability of the wrong shape is refused before
anything has been created or removed. `_settled` converts that `TypeError`
into a refusal that names the contract.

### Every reclamation step is settled or it is a refusal

`_settled` wraps the listing, both inspections, the stop and the removal.
Anything other than an answer becomes a typed refusal naming which step it
was, because a reclamation whose outcome this manager cannot settle is
UNRESOLVED — and unresolved is the one state a custody act must not proceed
from. The act's own call is deliberately NOT wrapped: its failure is the lost
ending that recovery and the typed answer exist for, not a refusal.

## 2026-08-30 — fourth round, after `review-2026-08-30T05-44-32Z.md`

### Superseded: reaping the local CLI is not settling the engine operation

The third round moved the deadline to the capability and said its contract
was that it had "terminated and reaped its child before it answers -- which is
exactly `subprocess.run(argv, timeout=seconds)`". **That sentence is true
about the wrong process.** Docker is client/server: `subprocess.run` settles
the local CLI, and the custody mutation is performed by the daemon, which has
already accepted the request and is not that child. Killing the client proves
nothing about whether the daemon will still create the derived helper.

This is the third boundary in a row where this record bounded the thing it
could reach — the act inside the custodian, then the wait around the call, now
the local client — instead of the thing that matters. The pattern is worth
naming because the next reader should distrust the next such claim until it
says WHICH process it settles.

**The rule now, and it is smaller than the previous three claimed to be.**
There is no instant on the lost path at which absence is provable, so custody
does not take an absence proof there and does not claim one. `_recovered`
removes a helper that IS there when it looks, and `custody_act` answers
**UNRESOLVED** — naming what was observed, that a submitted engine operation
may still create the derived name, and that the identity is derivable so a
later act reclaims whatever appears.

**Superseded with it:** the second round's rule that an unproved absence on
the lost path is a refusal, and the third round's rule that an empty listing
must be upgraded into an absence proof there. Both were the right shape for a
property that does not exist on this boundary.

### The blocker, minted rather than argued

Two reviews asked for an explicit provider blocker if the CLI cannot supply
the property. It cannot. **W44342 — "Settle or cancel the engine-side custody
operation"** carries it, with the review's own requirement quoted: recovery
and absence proof may begin only after no pending operation can later acquire
the derived name. What this child does meanwhile is a stopgap named as one in
`_recovered`'s docstring rather than presented as the fix.

### Superseded: `_settled` swallowed process control

The second round pinned that `KeyboardInterrupt` and `SystemExit` propagate.
The third round kept that for the act's own call and reversed it for every
reclamation step, because `_settled` caught `BaseException` and turned it into
a policy denial. It catches `Exception` now. An operator ending the process is
not an engine failure and this module does not get to relabel it as one.

### Pinned: an explicit engine deadline is validated before it is forwarded

`EnginePort.__call__` forwarded every non-`None` `seconds` to the injected
capability, so zero, a negative, a bool, a float and text all became whatever
coercion the injector performed — on a seam whose entire purpose is that a
caller can depend on the bound. It is now a positive exact integer, by
`stop_vector`'s existing rule rather than a second spelling of it. The
no-keyword legacy path for `None` is untouched.

## 2026-08-30 — approver ruling: W44342 is non-gating hardening

The prior direction naming W44342 as this child's provider blocker is
**superseded**. For the dogfood pass, this child's explicit `UNRESOLVED`
answer is the accepted fail-closed boundary: it claims no absence, starts no
second custody act, and leaves the attempt untrusted for operator
reconciliation. W44342 remains parked as the long-term durable-settlement
direction and is not a dependency of this Work.

## 2026-08-30 — fifth round, after `review-2026-08-30T06-06-47Z.md`

### The approver's ruling, recorded where it belongs

W44342 is PARKED and NON-GATING, and W43974's fail-closed `UNRESOLVED` result
is the accepted dogfood boundary. That supersedes the earlier review's request
for a W44342 dependency edge on this child. The provider defect is real and
recorded; what the ruling settles is that this pilot proceeds with an honest
`UNRESOLVED` rather than waiting for a provider that can settle the
engine-side operation.

### Superseded: leaving the provider regression textually unchanged was wrong

The fourth round left `test_reaping_the_cli_does_not_settle_a_daemon_mutation`
untouched on the reasoning that it was the reviewer's case and not mine to
edit. That was the right instinct about authorship and the wrong result about
evidence: **the correction made the case pass VACUOUSLY.** Its simulated
daemon waits on an event that only the removed `inspect` branch ever set, so
after the lost path stopped proving absence, nothing created and the assertion
held without exercising the client/server interval at all — while its
docstring still said recovery had proved absence, which the code and this
record now explicitly deny.

**The rule the case states now:** it DEMONSTRATES the defect rather than
asserting the missing guarantee. The daemon is released after `custody_act`
returns, the late creation is required to happen, and the answer is required
to say `UNRESOLVED`. Together those are the whole argument for W44342 — a
helper can appear after custody has finished looking, so custody must not
report that it has not.

The edit was authorized case-specifically before it was made.

### A green suite is not evidence, and this one now is

The reviewer's own note is the lesson worth keeping: 194 passing tests
included the vacuous case and were therefore not evidence that the daemon-side
property existed. This round proved the corrected case is not vacuous by
removing the release and confirming it FAILS — a check on the check, run
because "it passes now" is exactly what was true before.

### Owed elsewhere

W44342's research record says this test should remain unchanged. That is
superseded by the measured result above and is corrected on W44342's thread so
the parked Work does not resume from it.
