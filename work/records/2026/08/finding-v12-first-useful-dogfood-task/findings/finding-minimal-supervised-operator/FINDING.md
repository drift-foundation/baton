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
