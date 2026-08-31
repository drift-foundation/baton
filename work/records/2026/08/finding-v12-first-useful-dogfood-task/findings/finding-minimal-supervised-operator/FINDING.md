# Compose the minimal supervised dogfood operator

Work: W39358
Parent: W38956
Dependencies: W39356 and W39357

## Purpose

Provide one documented Python entry point that composes the already accepted
Worker Manager lifecycle with the accepted Docker transport and real Claude
worker. It is a thin deployment composition, not a second manager.

## Confirmed boundary

- Require explicit source subset, frozen task, image digest, engine, manager
  state/evidence roots, workspace group, credential source and network name.
  There is no home credential, mutable image tag or open-network default.
- Stage source outside manager core with the bounded no-follow manifest path,
  compose the accepted input/assignment/launch documents and mount source
  read-only at `/input/source`.
- Compose the deployment authority-session facade: six members delegate to
  the v12 `Session`; `publish_answer` is a typed refusal because this pilot
  runs no `inquire` and invents no Baton publication.
- Drive offer, reservation, claim, activation, input, launch, runtime start,
  correlated worker-entry conversation, freeze, intake, retention, destroy,
  positive absence and credential teardown through the public operations.
- Independently derive the candidate diff and verification result; never
  stage, merge or write into the canonical checkout.
- Preserve an unresolved attempt whenever runtime absence, output custody or
  credential cleanup cannot be proved.

## Initial file ownership

This child owns a new dogfood operator module below `v12/python/tools/`, its
operator documentation and focused composition tests below
`v12/python/tests/tools/`. It consumes W39356 and W39357 as accepted
capabilities and does not edit their transport or worker files without an
explicit handoff.

## Acceptance

- One documented command is reusable for another bounded task and records
  input tree/task/image/network/assignment/runtime/output identities without
  credential or raw provider text.
- Injected unit/composition tests prove the positive order and honest
  provider/control/transport/verification failures required for this positive
  slice.
- Exact replay cannot start a second runtime or provider turn; a fresh attempt
  receives fresh roots and credentials.
- Success and post-start failure use the accepted destroy/absence/credential
  cleanup path, with uncertainty preserved rather than relabelled success.
- A real Docker dry run reaches the worker entrypoint without relying on the
  spike lifecycle. Live provider authorization remains W39364's operator gate.

## 2026-08-30 — implementation revalidation (`baton.claude`, W39358 impl claim)

### Confirmed against the current tree

Both dependencies are closed `satisfying` and their public surfaces hold:

- W39356's transport is reached as a COMPONENT — `from
  baton_v12.worker_manager import worker_entry` — and `converse` takes the
  caller's own operation identities. `__init__.py` states in terms that
  neither `converse` nor `exec_vector` is exported and why.
- W39357's adapter is injected at `baton_worker.main(agent=)`, reads
  `/input/source` and `/input/task.json`, and holds `baton.dogfood-task/1` to
  a closed five-member set.
- `AuthorityPort` names seven `SESSION_OPERATIONS` and checks every one is
  callable at construction, which is what makes the facade's shape a
  precondition rather than a convention.
- `workspaces.copied_manifest` is the reviewed bounded no-follow copier and
  answers the manifest of what it copied.

### Pinned: `sources[].destination` is contract vocabulary this build does not consume

Searched rather than assumed: neither `workspaces.py` nor
`v12/worker/baton_worker.py` reads `sources` at all. The actual delivery is
the read-only `/input` mount, and W39357's adapter copies `/input/source` into
container-private scratch itself.

The member is therefore filled TRUTHFULLY — the document is digested,
retained and compared — and named in the composer's docstring as consumed by
nothing, so the next reader does not go looking for the code that acts on it.
The alternative, leaving it to look load-bearing, is how a later change
"fixes" a path nothing reads.

### Pinned: the frozen task does NOT travel in the input manifest

**Found by the manager's own composer rather than by inspection.** A first cut
of `input_manifest` carried `task_id`, and `compose_input_root` refused the
document: `baton.worker-manifest/input` is closed and has no task member.

The task is a WORKLOAD convention and travels in `/input/task.json` — the same
boundary the parent finding draws for Git. It is recorded because an operator
reading the composed manifest will wonder where the task went.

### Pinned: every policy identity is an OPERAND

The frozen input manifest requires seven policy digests plus the toolchain
digest, the worker image digest and the record binding. Each names something
the deployment is accountable for, so each is an explicit operand and
`input_manifest` refuses an incomplete set BEFORE the manager sees it — an
operator learns about a missing policy identity while nothing has been staged
rather than from a refused root with the source already in place.

### Pinned: `publish_answer` is a typed refusal, not an omission and not a no-op

`AuthorityPort` checks all seven operations at construction, so a facade that
simply omitted this one would be refused before the first offer. A no-op would
answer "published" to something nobody published. This pilot runs no
`inquire`, so the honest member is one that says the deployment does not carry
that capability.

`OperatorRefusal` is deliberately not a `ContractRefusal`: the latter is the
manager judging its own contract, and this is a deployment saying it was asked
for something it does not do. An operator that read a composition mistake as a
protocol refusal would look for the defect in the wrong package.

## Scope actually delivered in this round, and what is NOT

**Delivered and tested:** the deployment authority-session facade, the bounded
source staging, the frozen task read on the way in, and the two
manager-authored protocol documents — including one case that drives them
through `compose_input_root`, which is the boundary a real delivery crosses.

**NOT delivered:** the composed arc itself — offer through positive absence —
the retained evidence record, the independent diff and verification
derivation, and the real Docker dry run. `PLAN.md` and `PROGRESS.md` say so
plainly rather than leaving it to be inferred, and no `main` exists that would
imply otherwise.

## 2026-08-30 — second round, after `review-2026-08-30T05-53-19Z.md`

### Superseded: the manifest paths carried a retired `workspace/` prefix

**Superseded:** the first round's `destination: "workspace/source"` and
`path: "workspace/proposal"`, copied from a conformance vector without asking
what the current contract makes them relative TO.

Both are relative to a fixed root. `contracts/manifest.py` says so where it
checks their overlap; W39357's adapter reads `/input/source` and joins the
declared output path directly below `/output`; and the parent finding's
accepted proposal is at `/output/proposal`. So the first cut described a
delivery at `/input/workspace/source` that nothing makes, and asked the worker
to write `/output/workspace/proposal`, which nobody collects. They are
`source` and `proposal` now, and `PROPOSAL_TARGET` is a named constant beside
`SOURCE_TARGET` because both are one agreement seen from two ends.

### Superseded: "`sources[].destination` is consumed by nothing"

It is not a materialization instruction in this build — nothing copies a
source to it — but the MANIFEST RULES read it, and it is the durable
description of the staged delivery. The first round's phrasing invited a later
reader to treat it as dead weight. Filling it truthfully matters for that
reason rather than for tidiness.

### Superseded: the operator's task read was weaker than the worker's

The first round held the member set, the schema and the source root, and
nothing else — so an integer task id, empty or non-text instructions and a
scalar or empty verification all passed the operator and were refused by
`claude_agent._task` INSIDE the container. **That moves the promised refusal
to exactly the failed provider attempt it exists to avoid**, which makes the
promise worse than useless: an operator would trust it.

`frozen_task` now holds the same task-identity grammar, the same non-empty
text rule and the same non-empty list-of-words verification the worker holds,
and `TheOperatorAndTheWorkerHoldOneTaskContract` keeps the two copies against
one another — the member set, the schema, the staged source name and the
identity grammar — so a drift is a failing case rather than a live-turn
surprise.

### Superseded: the policy check ran after staging and held only key names

**Superseded:** the first round's claim that an incomplete policy set is found
"while nothing has been staged". `input_manifest` requires the already-produced
staged manifest, so the check could not run before staging and the record was
stronger than the code. Its own test called `stage_source` first, which is how
a claim like that survives.

`preflight` is that refusal, as a pure function over the explicit operands
alone: every policy identity, the image, the toolchain, the profile, the role
instructions, the record binding, the network name and the task's schema. It
runs before anything is staged or started, and it holds VALUES rather than key
names — `policy_digest="not-a-digest"` was accepted by the first cut and left
for the manager to refuse after the delivery existed.

It collects its faults and reports them together, so an operator fixes a
launch once instead of discovering its grants in the order this module happens
to check them. `input_manifest` applies the same hold again at the composer,
which is the second party proving it rather than assuming the first did.

### Pinned: the stated ceilings are a CEILING and not a default

`stage_source` forwarded caller-selected `max_entries` and `max_bytes`
unchanged, so a caller could widen the bound this module states — which makes
a stated bound a suggestion. A LOWER value is still accepted, because a test
or a cautious operator narrowing its own delivery takes nothing away; anything
above the operator constants refuses.

## 2026-08-30 — third round, after `review-2026-08-30T06-05-02Z.md`

### Pinned: ONE task hold, applied everywhere a task is believed

**Superseded:** the second round's arrangement, in which `frozen_task` held a
task fully, `preflight` re-checked only its `schema`, and `_copied_task`
serialized whatever it was handed. `frozen_task` answers an ordinary mutable
dict, so a task could be read valid, have its identity, instructions,
verification vector or source root changed, pass preflight, and be copied into
`/input/task.json` as the changed thing.

**Checking the schema a second time is not the same hold** — the review's own
sentence, and the reason `held_task` exists. It is one pure function over a
document, applied at the first read, at the preflight and immediately before
the copy. Three applications of one function rather than three chances to
disagree.

### Pinned: the record binding and the network are held by VALUE, before staging

**Superseded:** the second round's checks, which held the record binding's four
NAMES and the network's non-emptiness. Four correctly named members passed with
a malformed digest, an empty root or an absolute path, and any non-empty string
passed as a network — including `--network=host`, `../bridge` and `two words`.
Both were refused later, by the frozen manifest schema and by `oci._network`
respectively, which is after the source is staged.

Both digests are held, the root must be named, and the path must be a canonical
repository-relative record path — the same rule `AGENTS.md` puts on every Work
binding, and for the same reason: an absolute one is not portable across the
participants who have to read it.

**The network reuses `oci._network`**, which is the grammar's existing owner. A
second grammar written here would be two spellings of one rule with nothing
comparing them, which is the defect this campaign keeps correcting elsewhere.

### Pinned: the container is held before its contents

`policies=None` leaked `TypeError` and a string leaked `ValueError`, so the
public promise of one collected `OperatorRefusal` over explicit grants was
false for exactly the operands most likely to arrive wrong. The shape is held
first, and the collected faults follow.

### Pinned: a narrowed ceiling is still a ceiling

`stage_source` accepted booleans and zero and leaked `TypeError` for text, and
one boolean reached `copied_manifest` and surfaced in a manager refusal as a
limit of `True` files. Positive exact integers, by the manager's own rule for
every other count operand.

### Superseded: "the operator and the worker hold one whole contract"

That claim was FALSE and the record made it. The agreement test compares the
member tuple, the schema, the staged source name and the regex TEXT; it does
not compare the acceptance PREDICATE, and the two predicates differ — this
operator requires `task_id` to be an exact string, while `claude_agent._task`
applies the same regex to `str(document["task_id"])`, so a JSON number is a
usable identity to the receiver.

The class is renamed to say what it compares, and a case asserts the ASYMMETRY
from both sides rather than claiming it away. **The direction is safe for this
pilot** — the sender refuses what the receiver would accept, never the reverse
— so the sender boundary this Work owns is not reopened. **W44424 carries the
receiver correction against W39357, and this Work does not edit that closed
child's owned file.**

## 2026-08-30 — fourth round, after `review-2026-08-30T06-13-35Z.md`

### Superseded: the record-binding locators had a grammar written HERE

**Superseded:** the third round's hand-rolled checks — any non-empty string as
the root, `posixpath.normpath` plus a few exclusions as the path — and with
them the third round's claim that both locators are held by value. That claim
was stronger than the code: a root with spaces or 161 characters, and a path
of `.`, containing a backslash or a NUL, or 513 characters long, all passed
preflight and were refused by `_sealed` **after `stage_source` had created the
delivery** — which is exactly the interval the preflight exists to remove.

**The rule now:** `validate_fragment(value, "opaqueId")` and
`validate_fragment(value, "relativePath")`, the frozen document's own `$defs`
owner. This is the same rule the engine network operand is already under, and
the reason is the one that keeps proving itself in this campaign: **a second
approximation maintained in a tool is a second grammar with nothing comparing
the two.** The `posixpath` import is gone, and a case asks the MODULE rather
than its text — the superseded rule is described in a comment on purpose, so a
source search would find the word and report a grammar that is not there.

The collected fault carries the frozen validator's OWN sentence rather than a
class name, because the sentence says which rule the value broke and that is
what an operator needs to fix a launch; a class name sends them reading this
tool instead of their own document.

## 2026-08-30 — fifth round, after `review-2026-08-30T06-20-54Z.md`

### Pinned: only the TYPED outcome of a grammar owner is a bad grant

Both owner calls caught `except Exception`, so an implementation defect inside
`oci._network` or `validate_fragment` became an `OperatorRefusal` — telling a
human to edit a grant that is fine, and hiding the boundary that actually
failed. `OperatorRefusal`'s own docstring draws exactly that distinction
between a deployment saying it was asked for something it does not do and a
contract judgement, and catching broadly erased it.

`ContractRefusal` is caught exactly at both owners; anything else propagates.

### Superseded by W44424: the sender/receiver asymmetry no longer exists

**Superseded:** the fourth round's asymmetry — the claim that this operator is
the stricter end because `claude_agent._task` matched
`str(document["task_id"])`. W44424 is closed satisfying and the receiver holds
the identity as exact text before matching, so **both ends refuse a numeric
identity** and there is no asymmetry to record.

**And the case that recorded it made the same mistake it was about.** It
proved "the receiver takes it" by applying the receiver's REGEX to `str(7)` —
a constants comparison standing in for a predicate, which is precisely the
confusion that discovered W44424. It asks `_task` over a document on disk now,
which is how the receiver is actually reached.

**The lesson that survives, and it is the useful one:** equal regex text did
not prove equal predicates. That is why the class is named for what it
compares, and why the one predicate question in it is now asked of the
predicate.

## 2026-08-30 — seventh round, after `review-2026-08-30T06-35-56Z.md`

### Superseded: the assignment manifest could fabricate claim evidence

**Superseded:** the sixth round's `_claim_receipt` and `_claim_event`, which
fell back to an all-zero digest and a hard-coded `1` when the document they
were handed carried neither. They were handed `offer.accepted`, which never
carries either, so the fallback WAS the behaviour.

A syntactically valid placeholder in an assignment manifest is worse than an
absent field, because it reads as a fact. `submit_claim`'s own answer carries
the authority's assignment, claim event and decision; the manifest binds to
those, the receipt digest is over them, and there is no fallback branch left —
a claim result missing any of the three refuses.

### Pinned: quiescence is ORDERED, and reconciliation does not order it

The accepted transport starts the container INTERACTIVE so idle PID 1 outlives
the exec'd worker program. `reconcile_runtime` observes; it does not stop. So
the sixth round's arc reached `request_freeze` with a running runtime, and the
axis refused it — the nominal success path could not complete.

`adapter.stop` is the boundary that already exists for this: it orders the
stop and then PROVES what became of the runtime. The arc calls it, and a state
that is neither `quiescent` nor `absent` is `unresolved` rather than a freeze
this deployment asks for anyway.

### Pinned: ONE guarded ending owns every post-start branch

**Superseded:** the sixth round's shape, in which a lost conversation, a
missing disposition, a freeze or intake refusal and any transport fault each
returned or raised on its own. A container this deployment started could be
left running with nobody having tried to end it, while `_unresolved` recorded
prose. **Prose is not an ending.**

Every step now runs inside one guard; a failure records its reason and does
not skip the ending; and the ending records what the engine says is true
afterwards, so an operator reading `unresolved` also reads whether a container
is still there. That last read is a READ and never a removal — a second
destroy boundary beside the manager's own is the one thing a deployment must
not grow.

### Pinned: the custody locator is the RECEIPT'S

`intake_artifact` carries `custody_locator` precisely so a caller does not
reach for it. The sixth round used the adapter's private `_custody`, which
contradicts this module's own public-operations claim and couples a deployment
to OCI internals.

### Pinned: the adapter factory is given the grants this run records

It received neither the engine, the resolved image digest, the network nor the
labels, so the evidence could name one image and network while an unchecked
closure constructed an adapter for another. `run` and `labels` were accepted
and unused for the same reason.

### BLOCKED, and it is the approver's: which authority transition ends the assignment

`authorize_cleanup` refuses while `port.assignment_of(...)` still equals the
attempt's assignment, and nothing in this arc ends or fences it — so on the
success path that call is unreachable. The reviewer has put the question to
`@approv`: whether the trusted operator calls the already-minted `Session`'s
`pass_work` for the exact assignment to an explicit review Route operand, and
whether widening `DeploymentSession` with `pass_work` is the accepted
capability boundary.

**This round does not choose.** Cancellation installs a quiescence gate and
does not describe a successful handoff, and inventing a transition here would
be this deployment deciding what an authority ending means. The call site is
left where the ruling drops in.

### 2026-08-30 — approver ruling: successful work passes explicitly

The question above is resolved as v11 business-as-usual carried into v12:
claim, work and then an explicit pass to the next Route. A worker process
ending, output appearing, intake succeeding or verification passing does not
silently end authority. After successful intake, independent verification and
retention, the trusted operator calls the already-minted Session's
`pass_work` for the exact assignment generation to an explicit review Route
operand. Only a committed pass permits `authorize_cleanup` to run.

`DeploymentSession` is widened with that exact capability. The destination is
an explicit operator operand, never a default and never chosen by the worker.
If the pass refuses or its outcome is uncertain, cleanup does not run and the
attempt remains unresolved. Cancellation remains the wrong success ending:
it fences failed work rather than handing a completed candidate to review.

## 2026-08-30 — eighth round, after `review-2026-08-30T06-44-13Z.md`

### Superseded, for the THIRD time: "one guarded ending" was still not one

The sixth round returned from three places around the ending. The seventh
round moved most of it inside a guard and left the conversation OUTSIDE it —
so a lost conversation or an answer without a disposition still returned
before any ending, and the guard's own early returns still skipped cleanup
while the `finally` merely observed. **The record claimed a common ending
three rounds running while the code had bypasses each time.**

**The rule now, and it is structural rather than a promise:** everything after
`request_runtime_start` is inside `_after_start`; every named reason is
RAISED as `_Lost` rather than returned, so it cannot be forgotten at a call
site; and the ending runs in `finally`. A started runtime is what entitles an
attempt to an ending — a successful conversation is not the precondition for
one, which is the mistake all three rounds shared.

### Pinned: ending a started runtime BEGINS by stopping it

The stop used to live only in the success branch, so a lost conversation left
the container running. It is ordered on every post-start path now, through
`adapter.stop`, which both orders and proves — and it is ordered once, decided
by the evidence record rather than by where the call sits.

### Superseded: `absent` was accepted as a quiescence proof

The seventh round let `quiescent` OR `absent` proceed to freeze. The freeze
contract takes `quiescent` alone and says why: a runtime that is merely GONE
was never observed to have finished writing, so freezing its output would seal
bytes nobody watched the end of. Only `quiescent` proceeds.

### Pinned: an unexpected fault is recorded and then PROPAGATES

Catching every `Exception` turned a defect in this module into a supervised
attempt outcome. Cleanup still runs — that is what `finally` is for — and then
the fault propagates, because an implementation defect is not an ending an
operator should read as one.

### The gap this exposed is the MANAGER'S, and it is filed rather than papered over

An attempt whose runtime started and whose worker never answered has no intake
receipt, no start failure and no refused session — so `authorize_cleanup`,
`authorize_failed_start_cleanup` and `authorize_refused_session_cleanup` each
decline, and **no public operation ends it.**

Inventing a destroy here would be a second removal boundary beside the
manager's own, and would put the containment rules, the
remove-only-what-this-component-created rule and the storage-root check in a
place that does not own them. So the attempt is recorded `unresolved` with the
runtime named, and **W44716** carries the manager finding — which is the
review's own instruction: "If the public manager surface cannot honestly end
one of these states, record that as a manager finding rather than calling
observation cleanup."

### 2026-08-30 — W44716 ruling supersedes direct stop on unanswered paths

The rule above that every post-start ending begins with this deployment's
`adapter.stop` is **superseded for a lost conversation or unusable worker
disposition**. The runtime still belongs to a live authority generation, so a
deployment-owned stop before a fence is not a safe ending.

W44716 now owns one minimal composite manager operation: durably name the
attempt/generation/runtime, fence that exact generation, stop/remove the exact
runtime, prove absence, retain untrusted output and tear down exact deliveries.
W39358 consumes that public ending and grows no second removal boundary. A
timer alone does not invoke it; explicit operator or Route policy decides
abandonment. Successful worker completion retains its ordinary quiesce,
freeze, verify, pass-to-review and cleanup path.

### 2026-08-30 — M44657 implemented: the pass is the deployment's, and it is an ORDER

The approver's ruling is carried out: after intake, the independent
verification and retention, this deployment explicitly `pass_work`s the EXACT
assignment generation to an operator-supplied review Route. The v11 lifecycle
is preserved — the operator does not close the Work, it hands it on.

**Pinned: the pass is the DEPLOYMENT's act, not the manager's.**
`AuthorityPort` names seven session operations, checks those seven are
callable at construction, and ignores anything else. So `pass_work` is an
eighth member on `DeploymentSession`, over the deployment's own already-minted
session, and the manager's closed member set is untouched. This is what the
ruling says in as many words — "add `pass_work` to `DeploymentSession`" — and
it is also the only reading that does not widen a manager contract from a
deployment.

**Pinned: the session is an explicit operand.** `run_dogfood_task` takes
`session=` beside `port=`, and holds it to a callable `pass_work` before
anything is staged. It does NOT read `port._session`: helping itself to a
private attribute of another module to obtain a capability is exactly the
mistake review 2026-08-30T06:44:13Z caught in `_derived` reaching for
`adapter._custody`. A capability this deployment uses is one it was given.

**Interpretation recorded, because the ruling admits two readings.** "Permit
cleanup only after the pass commits" is implemented as an ORDERING
requirement, not as an additional precondition on cleanup:

- the pass is the last step of `_custody`, and cleanup runs in
  `_ended_however` after it — so on the success path cleanup necessarily
  happens on an assignment the pass has already ENDED. That is the substance
  of the rule: `pass_work` moves the Route and ends the assignment in one
  authority act, so cleanup afterwards is never cleanup of a live assignment;
- it is NOT read as "an attempt that never reached the pass may not be
  cleaned up". Review 2026-08-30T06:56:26Z [P0] ruled that a committed intake
  receipt authorizes `authorize_cleanup` and that every later failure must
  reach it. Making the pass a second precondition would reopen exactly that
  finding. On such a path the manager's own operation decides what it can
  settle — a still-live assignment is its refusal to make, not this
  deployment's to pre-empt.

If the approver meant the stronger reading, the change is one condition in
`_ended_however` and I will make it; I have not guessed in that direction
because the weaker one is the only one that keeps both rulings true.

**Pinned: the review Route is a named grant.** Held in `preflight` beside the
network, so an operator who did not say where the Work goes next gets a
refusal rather than this module's guess at a sensible destination.

**Pinned: the pass is effectively once by identity.** The operation id is
`pass:<attempt_id>`, derived from the attempt, so an exact replay of the arc
replays the authority's committed answer instead of passing twice; a different
generation carries a different signature and collides rather than silently
reusing this one's pass. What the evidence keeps is the route the AUTHORITY
recorded, and an answer naming another route is a refusal.

### 2026-08-30 — DEFECT: the arc could not run, and mocking is why nobody knew

`compose_input_root` exposes the whole input surface READ-ONLY as its last act
— the root ends `r-xr-xr-x`. `_copied_task` wrote `task.json` into that root
*after* the composition, so the real sequence raised `PermissionError` and this
deployment could not complete a single attempt.

**Nine rounds of composition tests did not catch it because every one of them
patched `compose_input_root` to a no-op.** The seal never happened, so the
write always succeeded. A mock that removes the very act an ordering depends
on cannot observe that ordering — and the case that finally ran the real
operation failed on its first attempt.

Corrected: the task is written before the root is sealed. The pinned decision
that the frozen task does not travel in the input manifest is unaffected — the
manifest was composed from the staged tree above and names nothing here.

### 2026-08-30 — Recorded limitation: an exact replay REFUSES rather than resumes

The acceptance requires that an exact replay start no second runtime and open
no second provider turn. This arc keeps that property, and it keeps it by
refusing before either: `stage_source` will not stage into an input root that
already holds a delivery the manager has measured, so a second run of the same
attempt identity stops in the delivery half.

That is a stronger guarantee than the manager's own effectively-once would
give, and a narrower capability. **An interrupted attempt is therefore not
continued by re-running the command; it is rerun under a fresh attempt
identity.** Recorded rather than dressed up as resumption, because the two read
identically in a passing test and differently to an operator whose attempt died
half-way. If the reviewer or approver wants resumption instead, the change is
in `stage_source`'s refusal and not in the arc.

### 2026-08-30 — approver ruling on M46497: refuse exact rerun; request settlement after pass failure

The recorded exact-rerun limitation above is accepted for the pilot. An
interrupted attempt is not resumed under the same attempt identity. Re-running
that identity refuses before a second runtime or provider turn; retry requires
a fresh attempt identity and assignment generation. Same-attempt resumption is
later hardening, not a gate on the first useful dogfood run.

This ruling also clarifies and partially supersedes two sentences in the
earlier successful-pass ruling: "Only a committed pass permits
`authorize_cleanup` to run" and "If the pass refuses or its outcome is
uncertain, cleanup does not run." Those sentences remain true only when
"cleanup" means the successful path's authorized destructive cleanup. They do
not mean that the deployment skips asking the manager to settle an attempt
after a committed intake receipt.

After intake commits, every later path calls the manager's
`authorize_cleanup`, including a refused or uncertain pass. The call is a
settlement request, not proof that cleanup happened. While the exact assignment
is live, the manager must refuse it; no workspace, result, credential delivery
or runtime is thereby destroyed or relabelled trusted. The refusal leaves an
explicit unresolved attempt for the operator to either retry through the
effectively-once pass or end through W44716's explicit abandonment path. That
path fences the exact generation before stopping the runtime, retains output as
untrusted and releases the lane. The successful path still performs actual
cleanup only after `pass_work` commits.

**Clarification: a post-worker machinery failure is not worker abandonment.**
The worker may have completed normally, become quiescent and produced a frozen,
independently verified result while some later manager, handoff, repository or
external-service operation fails. That later failure does not taint the result,
does not make the worker wedged and does not justify rerunning or reassigning
the worker. The trusted retained result is the input to an idempotent retry of
only the failed middle-machinery step. The worker runtime may be stopped after
its clean quiescence; the retained result remains available until the handoff
commits or an explicit operator disposition replaces it.

An external service such as GitHub is an example of why middle machinery can
fail, not part of Baton protocol vocabulary and not part of Baton's local
`pass_work` transaction. Where possible, Baton passes the retained result to
the next local Route and that Route owns the independently retryable external
operation. If a manager or Baton handoff step itself fails before that pass,
retry that exact step with its existing operation identity. Neither case opens
a second provider turn or restages the worker attempt.

### 2026-08-30 — critical-path scope freeze after the oversized review loop

W39358 has run for days, through twenty-eight implementation rounds and
twenty-nine independent reviews. It is no longer acceptable to treat another
failed check as one more undifferentiated round on this parent. The current
implementation episode is the final parent-level correction round.

The remaining parent acceptance is frozen to the latest review's two items:

1. decode and validate the manager's local `file:///...` custody locator once,
   then use that one absolute proposal root for the candidate and every member;
2. complete the real-Docker failed-handoff then fresh-retry settlement gate,
   proving resolved evidence, cleanup, positive absence and no second worker
   act.

The next review checks those items and nothing broader. A newly discovered
issue that does not prevent W39364's live provider run becomes separately
ledgered follow-up Work. If either frozen item still fails, the reviewer
creates one separately claimable leaf Work per failure and blocks W39358 on
those visible leaves; W39358 is not returned for a thirtieth monolithic round.
Live provider authorization and the useful task itself remain W39364's scope.

### 2026-08-30 — DEFECT: the transport execd the worker's FIXTURE agent

`WORKER_PROGRAM` named `/opt/baton/baton_worker.py`. That module's `main` runs
with `agent=None` and falls back to `_scripted_default()` — the M2 fixture
agent. Against the dogfood image this is wrong twice over:

- **in principle**, a supervised pilot would have reported a stub's output as
  the worker's work, which is the one failure mode this deployment must not
  have;
- **in fact**, W39770 removed `scripted_agent.py` from this image, so the
  fallback dies `ModuleNotFoundError` and the conversation is lost for a
  reason that names nothing true about the attempt.

`dogfood_entry.py` is the documented injection seam — one line calling
`baton_worker.main(agent=ClaudeAgent())` — and it is what the image's own
`ENTRYPOINT` names. Corrected, and the agreement is now asked of the RECIPE
rather than restated in a constant: an `ENTRYPOINT` and an `exec`ed program
that drifted apart would be two workers.

Found while composing the real-engine gate, like the input-root ordering
defect before it. Both were invisible to composition cases that supplied the
image and the engine themselves.

### 2026-08-30 — The launcher is the deployment's half, and it was missing

`worker_entry` says of the framed channel: *"this is the object the package
deliberately does not contain"* — every outward act in the Worker Manager
crosses an injected capability, and the thing that actually spawns a process
belongs to the deployment. This module IS the deployment, so the channel, the
engine runner, the adapter factory and the store opening live here now.

That is the whole of review 2026-08-30T12:40:47Z [P0]: every rule had been
written and the half that RUNS them had not, so the documented command loaded
definitions and exited 0.

`main` takes ONE injected thing and it is a FUNCTION OF THE GRANTS, because
the authority store, the control store and the credential home are all named
in the file and no capability can be built before it is read.

**Pinned: the bearer is minted in-process and the credential material is named
by PATH.** Neither is a grant member and neither is an environment variable,
because both of those are durable surfaces and §13 keeps the one deliberate
secret off every one of them. The path is not the secret. Live provider
authorization remains W39364's operator gate; what this launcher does is hand
whatever the operator authorized to the manager's own credential home, which
registers it live before a byte of it lands.

### 2026-08-30 — DEFECT: the editable record holds member names, not member values

**Observed.** `read_evidence` holds the byte ceiling, secret boundary and
closed top-level member set, then returns allowed nested values without
validating their shapes. `retry_handoff` and `_committed` consume those values
with `.get`, subscripting and sorting. Truthy JSON booleans in `independent`,
`output` or `intake_receipt`, a boolean custody item, and a string `retention`
escape as raw `AttributeError` or `TypeError` rather than `OperatorRefusal`.

**Confirmed boundary.** The retained file is explicitly operator-editable and
untrusted. A closed set of member names does not make the value under an
allowed name trusted. The retry must hold the complete nested result and
manager-projection contracts before consuming any of them. Broadly catching
Python faults after consumption would hide implementation defects and is not
the correction.

### 2026-08-30 — DEFECT: editable evidence can suppress the authority pass

The first nested hold covers the five witnessed result projections but omits
retry-owned history and the pass projection. A boolean `unresolved` therefore
still leaks raw `TypeError` when copied into history.

More importantly, a non-null editable `review_pass` makes `retry_handoff` skip
`_passed` entirely. The authority pass is effectively once and is exactly the
operation this retry exists to finish, so there is no reason to believe the
file instead of replaying its durable identity. Evidence may retain the
authority's answer only if the retry replay-reads and holds that answer whole;
it cannot mint or suppress the pass.

### 2026-08-30 — clarification: moving a path check is not holding identity

`workspaces.adopted_assignment_workspace` correctly centralizes the no-link
grammar and performs no allocation or permission mutation. It returns plain
path strings, however, and `OciAdapter` later reopens those names and derives
provider homes from them. The duplicate grammar is removed; the proof/use
interval is not. A manager-owned adoption boundary must preserve the proved
identity through use, not only relocate the same check before a later open.

### 2026-08-30 — resolved: retry replay-reads the authority pass and holds history

The editable-pass defect above is resolved. The narrow retry always performs
the exact authority operation; its attempt-derived identity makes an already
committed pass replay, and any retained pass projection must equal that replay
answer whole. A file can no longer suppress the pass by claiming it happened.

Retry-owned unresolved history is now held as a bounded list of durable text
before it is copied, and malformed history produces `OperatorRefusal` rather
than a raw Python fault. The adopted-root identity-through-use clarification
above and the real public fresh-process retry proof remain open.

### 2026-08-30 — public retry fixture produces the failure but does not prove the ending

**Confirmed correction.** The real-authority fixture now runs the ordinary
public command first and retries only the evidence and grants that command
wrote. The retained failure is produced rather than fabricated, and the
retry-specific builder's authority and control-store handles are closed.

**Observed open P0.** The same fixture discards the retry's process status and
does not inspect `resolved`, cleanup or current unresolved reasons. Its adapter
cannot complete the real custody settlement, a fact the implementation record
also states. Thus an exact authority pass beside an unfinished exit-1 ending
currently satisfies the test named as the final acceptance. Acceptance still
requires fresh capabilities, exact pass, complete manager settlement, positive
absence, exit 0 and no second worker-side act in one public-path case.

### 2026-08-30 — ordinary capability construction leaks durable handles

**Observed P1.** The 122-test focused run emits an unclosed SQLite warning;
tracemalloc points to `Authority.open` inside `_launched`. That function opens
both authority and control-store handles, but the ordinary `main` path has no
ownership/closure bundle or `finally`. The positive launcher test manually
closes only the store, so the authority warning is visible; the real command
closes neither. Ordinary capability lifetime must be explicit across success,
unresolved return and exception.

**Clarified after the first correction.** `main` now closes every handle in a
successfully returned ordinary capability bundle, including on a later compose
fault. Construction itself remains unsafe: `_launched` opens Authority before
ControlStore/configuration/credential setup, and a failure in any later step
returns no closure bundle for `main` to unwind. A reviewer regression makes
Authority open and ControlStore fail and observes zero disposals. Ownership
begins when each handle opens, so `_launched` must unwind the resources it has
already acquired on its own partial-construction path.

**Resolved after correcting the reviewer fixture.** Both builders now register
and locally unwind handles acquired during partial construction. The prior
reviewer witness had wrapped `dispose` without installing the wrapper on the
Authority instance and therefore could not observe any implementation; after
that harness correction, both partial-build cases and all 124 focused tests
pass with resource warnings fatal. The real-engine settlement and adopted-root
identity-through-use gates remain open and are separate from handle lifetime.

### 2026-08-30 — correction attempt still flattens the nominal root proof

The operator call sites now pass `AllocatedRoots` intact, but `oci._roots`
immediately copies its two members into a plain dictionary. The adapter stores
that copy and later gives it to `run_vector`, whose plain-mapping branch
canonicalizes the pathnames again. Thus the manager's nominal answer still
does not survive to use and the recorded proof/use interval remains open.

The initial witnesses only compared equal path strings and could not detect
the lost provenance. An additive reviewer witness now requires the adapter to
retain the exact minted value; it fails on the plain dictionary currently
stored. The public real-engine retry settlement gate remains independently
open.

### 2026-08-30 — resolved: nominal root proof survives adapter re-entry

`oci._roots` now returns the exact `AllocatedRoots` value on its nominal path.
Both operator constructions pass that value intact, the adapter stores it,
and `run_vector` re-enters the nominal path rather than canonicalizing a copied
dictionary. The reviewer identity witness and the full OCI and operator
modules pass. The manager-proved root identity-through-use gate is closed;
the public real-engine retry settlement gate remains open.

### 2026-08-30 — the reference-image mismatch does not block settlement proof

**Observed:** a live probe using the reference image reaches Docker and the
transport but loses the conversation because that image intentionally has no
`/opt/baton/dogfood_entry.py`. The operator must not revert to invoking
`baton_worker.py` directly; doing so would restore the fixture-agent binding
defect already corrected here.

**Confirmed:** W39364 is already blocked by W39358, so a reverse dependency is
not a possible ledger resolution. W39364 owns the live Claude turn and its
human credential/network grants; W39358's remaining gate owns lifecycle and
retry settlement.

**Proposed and implementation-ready:** build a test-owned Docker context that
keeps the exact `/opt/baton/dogfood_entry.py` injection seam and supplies a
deterministic agent which writes the declared proposal. Then drive the public
ordinary and retry commands with real Docker, OCI adapter, authority, stores,
deliveries and manager operations. This needs no live provider authority and
does not substitute a fake adapter. The public real-engine retry settlement
gate remains open pending that witness.

### 2026-08-30 — channel ending corrected; retry fixture remains partial

**Confirmed correction:** `_Channel.finish` now returns the exact
`{status, stderr}` document the worker-entry transport requires. The prior
bare status made every real conversation unreadable at its ending even after
the worker answered. Focused operator and worker-entry tests pass, and the
bounded stderr is not copied into durable evidence.

**Observed incomplete gate:** the test-owned image proves the exact dogfood
entry path can inject a deterministic agent and reach a completed worker
disposition, but the generic scripted agent does not write the operator's
declared proposal shape. Freeze refuses, so no real intake, retention, failed
pass, retry or settlement has yet been witnessed.

**Required fixture correction:** the fixture currently registers the review
Route before the ordinary command. After its proposal agent is fixed, the pass
would therefore succeed rather than produce the failed handoff under test.
Withhold that handler until the ordinary command has failed, then add it before
the fresh retry. The temporary image build context must also be removed by
class cleanup.

The managed reviewer could not independently run the Docker module because
the local daemon socket denied access; no escalation was requested. The P0
gate remains open.

### 2026-08-30 — launcher forwarding fixed; URI use and settling remain open

**Confirmed:** the ordinary adapter factory now forwards the declared outputs
and input-manifest digest it accepts. The real fixture withholds the review
handler until retry and cleans its temporary build context.

**Observed:** `_derived` strips `file://` to find `candidate`, but checks every
other proposal member below the unchanged URI string. A reviewer regression
places all four members below a real `file:///...` receipt root; verification
passes and `members_present` is still empty. The locator must be validated and
decoded once to one absolute local proposal root used for every read.

**Still open:** the deterministic proposal-writing agent is not installed and
the real settling case remains unwritten. The current ordinary witness expects
an implementation `FileNotFoundError` before retention/pass and invokes no
retry. The complete public real-engine retry P0 remains open.

### 2026-08-30 — resolved: receipt URI has one root; settling still absent

`_proposal_root` now validates the manager's local `file://` locator as an
absolute pathname and supplies one proposal root to both candidate derivation
and all member checks. The reviewer URI regression and all 125 non-daemon
operator tests pass. The URI finding is resolved.

The real-engine module still uses `ScriptedAgent`, expects an independent-
derivation `FileNotFoundError`, and contains no public retry. The proposed
proposal-writing agent currently faults on a nested `/output` write and is not
installed. Therefore the public real-engine settlement P0 remains open in
full.

### 2026-08-30 — verification cadence ruling after the long correction loop

The remaining W39358 correction iterates only with the smallest deterministic
proposal-writing/retry-engine witness and its focused operator dependencies.
It does not rerun the whole source tree or unrelated boundary inventories after
each edit. Once the frozen settlement witness is green, the handoff runs one
broader relevant regression sweep.

That broad sweep uses the repository's reviewed parallel harness: isolated
source shards consume the host's available CPUs, while the explicitly
registered Docker/shared-daemon modules remain serial. A broad failure blocks
W39358 only when it can invalidate the promised supervised dogfood path;
unrelated failures become separately ledgered Work. This ruling changes the
verification cadence, not the frozen acceptance boundary above.
