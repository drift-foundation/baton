# Progress

## 2026-08-30 — first implementation round (`baton.claude`, W39358 impl claim)

**THIS ROUND IS PARTIAL AND SAYS SO.** What exists is the foundation the arc
composes from; the arc itself is not built. I am returning it early rather
than late because two of its decisions were settled only by running the
manager's own composer, and a third reader should see them before more rests
on them.

### Delivered

`v12/python/tools/dogfood_operator.py`:

- `DeploymentSession` — six members delegate to one already-minted
  `baton_v12.authority.Session`; `publish_answer` is a typed refusal.
  `AuthorityPort` checks all seven at construction, so omitting the seventh
  would be refused before the first offer and a no-op would answer
  "published" to something nobody published.
- `stage_source` — the exact subset through `workspaces.copied_manifest`, the
  manager's own bounded no-follow copier, landing at the fixed `source` name
  the adapter reads by equality. Staging twice into one input root refuses.
- `frozen_task` — the operator's own document, held to `baton.dogfood-task/1`
  on the way IN, so a malformed task is found before a container starts rather
  than from a failed attempt's evidence.
- `input_manifest` / `assignment_manifest` — the two protocol documents the
  manager takes as operands, with every policy identity an explicit operand
  and an incomplete set refused before the manager sees it.

`v12/python/tests/tools/test_dogfood_operator.py` — 27 cases, no daemon, no
credential, registered in the parallel phase.

### TWO DECISIONS THE MANAGER'S OWN COMPOSER SETTLED, not inspection

1. **The frozen task does not travel in the input manifest.** My first cut
   carried `task_id` and `compose_input_root` refused the document:
   `baton.worker-manifest/input` is closed and has no task member. The task is
   a WORKLOAD convention and travels in `/input/task.json`.
2. **Every policy identity is required.** The schema wants seven policy
   digests plus the toolchain, the image and the record binding. My first cut
   supplied three and was refused after the source had already been staged,
   which is why `input_manifest` now refuses an incomplete set itself.

Both are pinned in `FINDING.md`. The case that found them —
`test_the_two_documents_compose_a_real_input_root` — drives the pair through
`compose_input_root` deliberately, because a pair of documents this module
shaped to look right proves nothing.

### One thing I searched rather than assumed

`sources[].destination` is read by NOTHING in this build — not
`workspaces.py`, not `baton_worker.py`. The delivery is the read-only
`/input` mount and the adapter's own copy. The member is filled truthfully
because the document is digested and retained, and the composer's docstring
names it as consumed by nothing so a later change does not "fix" a path
nothing reads.

### NOT DONE, and named rather than implied

- The composed arc: offer, accept, record, claim, activate, input root, launch
  and credential deliveries, runtime start, worker-entry conversation, freeze,
  intake, retention, destroy, positive absence, credential teardown.
- The retained evidence record.
- The independent diff and verification derivation.
- The real Docker dry run.

There is deliberately no `main` yet. A command that accepted every operand and
then refused would look like a tool while composing nothing, and this record
would rather say the arc is unbuilt than ship something that reads as one.

### Verification

From `v12/python`:

    PYTHONPATH=src python3 -m unittest tests.tools.test_dogfood_operator
    -> 27 tests, OK

    PYTHONPATH=src python3 -m unittest tests.tools.test_dogfood_operator
      tests.tools.test_parallel_runner tests.manager.test_dependencies
      tests.manager.test_workspaces
    -> 163 tests, OK (1 skipped)

    `diff --check` over the working tree: passed.

`test_parallel_runner` refused the new module until it was registered, which
is the registry gate working; it is in the parallel phase with its reason
written beside it.

## 2026-08-30 — second implementation round (`baton.claude`, W39358 impl claim)

Answering `review-2026-08-30T05-53-19Z.md`. All three [P1]s are addressed and
the reviewer's three additive methods pass. The arc is still not built, which
is unchanged and still said plainly.

### [P1] The manifest paths carried a retired `workspace/` prefix

Right, and I got them from a conformance vector without asking what the
current contract makes them relative TO. `contracts/manifest.py` says both are
relative to a fixed root where it checks their overlap; W39357's adapter reads
`/input/source` and joins the declared output path directly below `/output`.
So my first cut described a delivery at `/input/workspace/source` that nothing
makes and asked the worker to write somewhere nobody collects. They are
`source` and `proposal`, with `PROPOSAL_TARGET` named beside `SOURCE_TARGET`
because both are one agreement seen from two ends.

My "consumed by nothing" claim is superseded in `FINDING.md`: it is not a
materialization instruction, but the manifest rules read it and it is the
durable description of the staged delivery. The phrasing invited a later
reader to treat it as dead weight.

### [P1] My task read was weaker than the worker's

The sharp part of this one is that it made the promise worse than useless. The
operator's read exists to move a refusal earlier; a copy that accepts what the
container will reject moves it back to exactly the failed provider attempt it
was meant to avoid, and an operator would have trusted it.

`frozen_task` holds the same identity grammar, non-empty text rule and
non-empty list-of-words verification the worker holds, and
`TheOperatorAndTheWorkerHoldOneTaskContract` keeps the two copies against one
another by loading `v12/worker/claude_agent.py` and comparing the member set,
the schema, the staged source name and the identity pattern.

### [P1] The policy check ran after staging and held only key names

Also right, and the record was stronger than the code — the classic shape this
campaign keeps catching. `input_manifest` requires the staged manifest, so the
check could not run before staging, and its own test called `stage_source`
first, which is how a claim like that survives review.

`preflight` is a pure function over the explicit operands alone and runs
before anything is staged. It holds VALUES, not key names:
`policy_digest="not-a-digest"` passed my first cut. It collects faults and
reports them together, so an operator fixes a launch once rather than
discovering its grants in whatever order I check them. `input_manifest`
applies the same hold again at the composer.

### Also closed: the stated ceilings were a suggestion

`stage_source` forwarded caller-selected bounds unchanged, so a caller could
widen the module's stated ceiling. It refuses anything above the operator
constants and still accepts a narrower one, because a caller narrowing its own
delivery takes nothing away.

### Verification

From `v12/python`:

    PYTHONPATH=src python3 -m unittest tests.tools.test_dogfood_operator
    -> 45 tests, OK   (30 before: my 27 + your 3; +15 of mine)

    PYTHONPATH=src python3 -m unittest tests.tools.test_dogfood_operator
      tests.tools.test_parallel_runner tests.manager.test_dependencies
      tests.manager.test_workspaces tests.manager.test_claude_agent
    -> 247 tests, OK (1 skipped)

    `diff --check` over the working tree: passed.

### Still not done, unchanged

The composed arc, the retained evidence record, the independent diff and
verification derivation, and the real Docker dry run.

## 2026-08-30 — third implementation round (`baton.claude`, W39358 impl claim)

Answering `review-2026-08-30T06-05-02Z.md`. All four findings are addressed
and the reviewer's five additive methods pass. The arc is still not built.

### [P1] The task could change after its first hold

Right, and the shape is one I should have seen: `frozen_task` answered a
mutable dict, `preflight` re-checked only its schema, and `_copied_task`
serialized what it was handed. "Checking the schema a second time is not the
same hold" is exactly it. `held_task` is one pure function applied at all
three places, and a case asserts all three call it rather than trusting me to
keep them aligned.

### [P1] The record binding and the network were held by name only

Also right. Four correctly named binding members passed with a malformed
digest, an empty root or an absolute path; any non-empty string passed as a
network, including `--network=host`. Both are held by value now, before
staging.

The network goes through `oci._network` rather than a second grammar written
here — the reviewer's "reuse one grammar owner rather than letting the
operator and OCI adapter drift", which is the same rule this campaign applies
to every other two-ended contract.

### [P1] A malformed policy container leaked raw Python

`policies=None` leaked `TypeError` and a string leaked `ValueError`, so the
promise of one collected refusal was false for the operands most likely to
arrive wrong. The container is held before its contents.

### [P2] A narrowed ceiling had no value contract

Booleans and zero were accepted and text leaked `TypeError`; one boolean
reached `copied_manifest` and surfaced as a limit of `True` files. Positive
exact integers now.

### [P2] MY RECORD CLAIMED A CONTRACT AGREEMENT THAT IS NOT TRUE

The one worth reading. I named the class `TheOperatorAndTheWorkerHoldOneTask
Contract` and the record said both ends hold one whole contract. It compares
CONSTANTS — the member tuple, the schema, the source name, the regex text —
and not the acceptance predicate, and the predicates differ: this operator
requires `task_id` to be an exact string, and `claude_agent._task` matches
`str(document["task_id"])`, so a JSON number is usable to the receiver.

The class is renamed to say what it compares, `FINDING.md` supersedes the
claim, and a case asserts the asymmetry from BOTH sides — the operator refuses
the numeric id and the worker's pattern accepts its string form — so the next
reader finds the difference in a case rather than in a live turn. The
direction is safe for this pilot because the sender is the stricter end.

### NOT MINE, AND NOT TOUCHED: the W44424 regression

`tests/manager/test_claude_agent.py` carries the reviewer's additive
`test_a_task_identity_is_text_before_it_is_matched`, which FAILS. It is the
receiver half of the asymmetry above, filed against W39357, and correcting it
means editing `v12/worker/claude_agent.py` — which the review directs this
Work not to do. Reported rather than fixed, and reported rather than left for
somebody to trip over.

### Verification

From `v12/python`:

    PYTHONPATH=src python3 -m unittest tests.tools.test_dogfood_operator
    -> 56 tests, OK   (50 before: my 45 + the reviewer's 5; +6 of mine)

    PYTHONPATH=src python3 -m unittest tests.tools.test_dogfood_operator
      tests.tools.test_parallel_runner tests.manager.test_dependencies
      tests.manager.test_workspaces tests.manager.test_oci
    -> 284 tests, OK (1 skipped)

    `tests.manager.test_claude_agent` -> 67 run, 66 pass, 1 FAIL, and the
    failure is W44424's regression named above. This round changed only
    `tools/dogfood_operator.py` and `tests/tools/test_dogfood_operator.py`.

    The working tree's whitespace check: passed.

### Still not done, unchanged

The composed arc, the retained evidence record, the independent diff and
verification derivation, and the real Docker dry run.

## 2026-08-30 — fourth implementation round (`baton.claude`, W39358 impl claim)

Answering `review-2026-08-30T06-13-35Z.md`. The one [P1] is addressed and the
reviewer's additive method passes. The arc is still not built.

### [P1] I wrote a second locator grammar and my record over-claimed it

Right on both halves. The hand-rolled checks — any non-empty string as the
root, `posixpath.normpath` plus a few exclusions as the path — let a root with
spaces or 161 characters, and a path of `.`, with a backslash, with a NUL or
513 characters long, through preflight; `_sealed` refused them afterwards, by
which point `stage_source` had already created the delivery. That is precisely
the interval this preflight exists to remove, and the third round's record said
both locators were held by value, which was stronger than the code.

`validate_fragment(..., "opaqueId")` and `validate_fragment(..., "relativePath")`
now do it — the frozen document's own `$defs` owner, at preflight and again at
the composer. This is the third time in this Work that the answer has been
"reuse the grammar's owner": the task contract, then the engine network, now
the locators. **A second approximation maintained in a tool is a second grammar
with nothing comparing the two**, and I have now written that same defect three
times, which is worth recording as a pattern rather than as three incidents.

The collected fault carries the validator's own sentence rather than a class
name, because the sentence says which rule the value broke; a class name sends
an operator reading this tool instead of their own document.

### One test detail worth naming

My first cut of `test_this_tool_keeps_no_second_locator_grammar` searched the
module's SOURCE TEXT for `posixpath` and failed — because the superseded rule
is described in a comment on purpose. It asks the module for the attribute now.
A text search for a deleted mechanism finds the record of its deletion, which
is an argument for asking the object rather than the file.

### Verification

From `v12/python`:

    PYTHONPATH=src python3 -m unittest tests.tools.test_dogfood_operator
    -> 62 tests, OK   (57 before: my 56 + the reviewer's 1; +5 of mine)

    PYTHONPATH=src python3 -m unittest tests.tools.test_dogfood_operator
      tests.tools.test_parallel_runner tests.manager.test_dependencies
      tests.manager.test_workspaces tests.manager.test_oci
      tests.manager.test_claude_agent
    -> 357 tests, OK (1 skipped) -- `test_claude_agent` is green now that
       W44424 corrected the receiver.

    The working tree's whitespace check: passed.

### Still not done, unchanged

The composed arc, the retained evidence record, the independent diff and
verification derivation, and the real Docker dry run.

## 2026-08-30 — fifth implementation round (`baton.claude`, W39358 impl claim)

Answering `review-2026-08-30T06-20-54Z.md`. Both [P2]s are addressed and the
reviewer's additive method passes.

### [P2] An owner's defect was being reported as a bad grant

Right, and it is the same shape I corrected in custody's `_settled` two Works
ago: `except Exception` around a typed boundary turns an implementation defect
into a judgement about the caller's input. `OperatorRefusal`'s own docstring
says it means a deployment was asked for something it does not do — and an
owner raising `RuntimeError` is not that. `ContractRefusal` is caught exactly
at both owners now; anything else propagates.

### [P2] My own W44424 fix made this Work's asymmetry claim false

The one worth reading. Last round I recorded an asymmetry — this operator
stricter than the receiver on a numeric `task_id` — and then, under W44424,
fixed the receiver. The property stopped existing and the record went on
asserting it.

**And the case recording it repeated the mistake it was about.** It proved
"the receiver takes it" by applying the receiver's REGEX to `str(7)` — a
constants comparison standing in for a predicate, which is exactly the
confusion that discovered W44424 in the first place. Writing the case that
documents a predicate/constant confusion using a predicate/constant confusion
is a nice demonstration that the lesson had not actually landed.

It asks `_task` over a document on disk now, which is how the receiver is
really reached, and both ends are asserted to refuse. The surviving lesson —
equal regex text did not prove equal predicates — is kept in the class prose,
because that is the part worth carrying forward.

`FINDING.md`, `PLAN.md` and this file all record the supersession rather than
leaving the fourth-round prose live beside its correction.

### Verification

From `v12/python`:

    PYTHONPATH=src python3 -m unittest tests.tools.test_dogfood_operator
    -> 66 tests, OK   (63 before: my 62 + the reviewer's 1; +3 of mine)

    PYTHONPATH=src python3 -m unittest tests.tools.test_dogfood_operator
      tests.tools.test_parallel_runner tests.manager.test_dependencies
      tests.manager.test_workspaces tests.manager.test_oci
      tests.manager.test_claude_agent
    -> 361 tests, OK (1 skipped)

    The working tree's whitespace check: passed.

### Still not done, unchanged — and now the only thing left

The composed arc, the retained evidence record, the independent diff and
verification derivation, and the real Docker dry run. The foundation is clear
of findings for the first time, so the arc is what the next round is for.

## 2026-08-30 — sixth round (`baton.claude`, W39358 impl claim)

The foundation review is accepted and the instruction was "the arc, not
another foundation-only slice". **The arc is WRITTEN and it is NOT
EXERCISED**, and I am reporting that rather than presenting it as the arc.

### What exists now

`run_dogfood_task` in `tools/dogfood_operator.py` composes the accepted order
end to end through public operations only:

- preflight and the frozen task, then the delivery half — workspace roots,
  bounded source staging, both protocol documents, `compose_input_root`, the
  task copy, `retain_manifest`;
- the authority half — `issue_offer`, `accept_offer`, `record_attempt`,
  `submit_claim`, `activate_assignment`;
- the two manager roots — `launch.materialize` and the injected credential
  delivery — then `request_runtime_start`;
- ONE worker-entry conversation, `describe` then `work`, over
  `worker_entry.converse`;
- `reconcile_runtime`, `observe`, `request_freeze`, `request_intake`,
  `decide_retention`, `authorize_cleanup`;
- and an evidence record whose `resolved` is false with a named reason
  whenever a required proof was not obtained.

Two things in it are worth a reviewer's attention on their own:

**The runtime identity comes from the operation's own answer.** The transport
needs the exact runtime id, and this module must not open a control-store
table. `request_runtime_start` answers through `reconcile_runtime`, whose
`runtime.attached` document carries `runtime_id` — so the operand is the
manager's own answer. An UNCERTAIN reconciliation names no runtime, and that
refuses rather than sending this deployment looking for one.

**The diff and the verification are recomputed here.** `_derived` diffs the
collected candidate against the staged source BY BYTES and reruns the task's
own frozen command outside the container, before retention discards the source
— because the parent finding says an operator trusts neither `result.json` nor
`change.patch` in place of doing exactly that.

### WHY I AM NOT CALLING THIS "THE ARC"

**No case drives `run_dogfood_task`.** It parses, it breaks none of the 66
foundation cases, and that is the whole of what is established about it.

I started the real Docker gate this round and stopped: it needs the lifecycle
fixture rebuilt around the dogfood image rather than the reference one, and
what I had drafted was not close enough to finish at the standard the previous
five rounds were held to. Shipping a ~200-line production composition with a
record that describes what it does would be precisely the failure this Work
has corrected in me four times — the record stronger than the code — at the
largest scale yet available.

So the code is here to be read and the claim is exactly this: **written,
unexercised, and not yet evidence of anything.**

### What the next round needs

1. A composition gate that drives `run_dogfood_task` over the real engine and
   the REAL dogfood image, to the point the acceptance names — the worker
   entrypoint reached, the provider turn stopping on the absent credential,
   which is W39364's gate rather than this one's.
2. The unresolved branches driven: a conversation that did not answer, a
   worker that named no disposition, intake that took custody of nothing, and
   a cleanup that did not reach `complete`/`absent`.
3. Registration of whichever suite is serial, since a Docker gate is.

### Verification

    PYTHONPATH=src python3 -m unittest tests.tools.test_dogfood_operator
      tests.tools.test_parallel_runner tests.manager.test_dependencies
    -> 123 tests, OK (1 skipped) -- unchanged, which is the point: this round
       added production code and no evidence about it.

    The working tree's whitespace check: passed.

## 2026-08-30 — seventh round (`baton.claude`, W39358 impl claim)

Answering `review-2026-08-30T06-35-56Z.md`. Three of the four [P0]s and both
[P1]s are corrected; the fourth is the approver's and the reviewer has already
put it to them.

### [P0] The manifest fabricated claim evidence

The sharpest of the four. I discarded `submit_claim`'s answer and populated
the assignment manifest from `offer.accepted`, which carries neither a claim
event nor a receipt digest — so my fallbacks WERE the behaviour: an all-zero
digest and a hard-coded `1`, in a document an operator reads as the
authority's evidence. There is no fallback branch left; the manifest binds to
`submit_claim`'s three facts and a result missing any of them refuses.

### [P0] The interactive runtime was never made quiescent

Also right, and it means the nominal success path could not complete: the
transport starts the container interactive so PID 1 outlives the exec'd
program, `reconcile_runtime` observes rather than stops, and `request_freeze`
requires the axis to be exactly `quiescent`. `adapter.stop` orders it and
proves what became of it; anything other than `quiescent` or `absent` is
`unresolved` rather than a freeze asked for anyway.

### [P0] Post-start failures bypassed the ending

Every branch returned or raised on its own, so a container this deployment
started could be left running while `_unresolved` recorded prose. **Prose is
not an ending.** One guard owns every step now, a failure does not skip the
ending, and the ending records what the engine says afterwards — as a READ,
because a second destroy boundary beside the manager's own is the one thing a
deployment must not grow.

### [P1] Both

The custody locator comes from the intake receipt, which carries it precisely
so a caller does not reach through `adapter._custody`. And the adapter factory
is given the engine, the image digest, the network and the labels this run
records, so the evidence and the constructed adapter cannot name different
ones — which is what `run` and `labels` were sitting unused for.

### [P0] BLOCKED AND NOT MINE: the authority transition

`authorize_cleanup` refuses while the assignment is still live, and nothing in
this arc ends or fences it, so on success that call is unreachable. You have
put the question to `@approv` — `pass_work` to an explicit review Route versus
something else, and whether widening `DeploymentSession` is the accepted
capability boundary. I have not chosen: cancellation installs a quiescence
gate and does not describe a successful handoff, and picking a transition here
would be this deployment deciding what an authority ending means. The call
site is left where the ruling drops in, and `FINDING.md` records it as open.

### Still absent, and still named rather than implied

No test invokes `run_dogfood_task`. The serial whole-arc Docker gate, the
documented command and the durable redacted evidence writer are not built, and
exact replay, fresh-root and fresh-credential behaviour are unproved. **The
arc remains written and unexercised**, and this round did not change that — it
corrected defects found by inspection, which is what was available.

### Verification

    PYTHONPATH=src python3 -m unittest tests.tools.test_dogfood_operator
      tests.tools.test_parallel_runner tests.manager.test_dependencies
    -> 123 tests, OK (1 skipped) -- unchanged, and unchanged is still the
       honest report: these cover the foundation, not the arc.

    The working tree's whitespace check: passed.

## 2026-08-30 — eighth round (`baton.claude`, W39358 impl claim)

Answering `review-2026-08-30T06-44-13Z.md`. Both [P0]s and the [P1] are
corrected, and the reviewer's additive regression passes.

### THE SAME MISTAKE, THREE ROUNDS RUNNING

Worth stating plainly because it is the pattern rather than three incidents.
The sixth round returned from three places around the ending. The seventh
moved most of it inside a guard, left the conversation outside, and I then
wrote a record saying "the manager's own cleanup is attempted, whatever
happened" — which was false for the two branches most likely to happen. The
reviewer has now caught my record being stronger than my code on this one
point three times.

What changed is structural rather than another promise: everything after
`request_runtime_start` lives in `_after_start`, every named reason is RAISED
rather than returned so it cannot be forgotten at a call site, and the ending
runs in `finally`. **A started runtime is what entitles an attempt to an
ending; a successful conversation is not the precondition for one.** That was
the wrong idea underneath all three rounds.

### The other two

Ending a started runtime now BEGINS by stopping it, on every post-start path
rather than only the success branch — which is what the reviewer's regression
measures, and it was zero stops before.

`absent` no longer proceeds to freeze. The contract takes `quiescent` alone
and says why: a runtime that is merely gone was never observed to have
finished writing. And an unexpected fault is recorded and then propagates —
cleanup still runs, but a `KeyError` in this module is not an ending an
operator should read as a supervised outcome.

### THE GAP THIS EXPOSED IS THE MANAGER'S, and I filed it

An attempt whose runtime started and whose worker never answered has no intake
receipt, no start failure and no refused session — so all three public endings
decline and none can end it. Inventing a destroy here would be a second
removal boundary beside the manager's own, and would put the containment
rules, the remove-only-what-this-component-created rule and the storage-root
check somewhere that does not own them.

**W44716** carries it. The attempt is recorded `unresolved` with the runtime
named so an operator can act, and the code says which Work owns the gap. That
is the review's own instruction rather than my judgement call.

### Still absent, unchanged

No serial Docker gate, no documented command, no durable redacted evidence
writer; replay, fresh-root and fresh-credential behaviour unproved. The
authority transition remains M44657's, pending with `@approv`.

### Verification

    PYTHONPATH=src python3 -m unittest tests.tools.test_dogfood_operator
      tests.tools.test_parallel_runner tests.manager.test_dependencies
    -> 124 tests, OK (1 skipped) -- 124 now, because the reviewer's additive
       regression is the first case that has ever invoked `run_dogfood_task`,
       and it passes.

    The working tree's whitespace check: passed.

## 2026-08-30 — ninth round (`baton.claude`, W39358 impl claim)

Revalidated `review-2026-08-30T06-56-26Z.md` against the current tree first,
because both its P0s were corrected while W44716 was being implemented rather
than under this Work's claim.

### Both P0s confirmed closed, by inspection of the tree they were filed against

- **the hidden receipt**: `evidence["intake_receipt"] = True` is set at
  `dogfood_operator.py:904`, immediately after `request_intake` returns and
  before `receipt["artifacts"]` is read at all. The reviewer's additive case
  `test_an_empty_intake_receipt_still_authorizes_cleanup` passes.
- **fence before stopping an unanswered worker**: `_ended_however` gates its
  stop on `evidence["intake_receipt"]`, so the receiptless path enters
  `abandon_attempt` — W44716's public composite, which fences before it
  removes — with no deployment-side runtime control at all. The reviewer's
  `test_receiptless_abandonment_does_not_stop_before_the_fence` passes.

W44716 itself is implemented and under review on its own dossier; this Work
consumes its public operation and grows no second removal boundary.

### [P2] The no-disposition fixture drove a document the transport cannot make

Corrected in my own case. `ending="answered"` means every requested operation
answered, so a `describe`-only answer set is not producible. The reachable
defensive shape is a complete `work` answer — the envelope is closed on member
NAMES and deliberately does not type the VALUES — carrying a disposition this
deployment cannot use. My case now drives `{"disposition": None, "outputs":
[], "recap": ""}` alongside the answers that precede it.

The same shape still appears in the reviewer's own
`test_transport_and_disposition_failures_do_not_return_around_ending`, which
they revised on 2026-08-30 without revisiting [P2]. I have not touched it.

### M44657 implemented — the approved success transition

The ruling was `[next]` rather than blocked, so this round carried it out. See
FINDING.md for the four pinned decisions and, importantly, for the recorded
INTERPRETATION of "permit cleanup only after the pass commits": it is
implemented as an ordering requirement rather than as a second precondition on
cleanup, because the stronger reading would reopen review
2026-08-30T06:56:26Z [P0]. If the approver meant the stronger one, it is one
condition and I will make it.

What changed:

- `DeploymentSession` grows an eighth member, `pass_work`, delegating to the
  deployment's own minted session. The manager's seven-operation closed set is
  untouched, because the port checks its seven and ignores the rest;
- `run_dogfood_task` takes `session=` and `review_route=` as explicit
  operands. The session is held to a callable `pass_work` before anything is
  staged; the route is held in `preflight` beside the network;
- `_custody` ends by passing the exact assignment generation, and
  `_ended_however`'s cleanup therefore runs on an assignment the pass already
  ended;
- `_passed` holds the authority's answer to shape and keeps the route the
  AUTHORITY recorded, refusing an answer that names another one.

Seven cases cover it: the pass with its exact assignment, named route,
attempt-derived operation id and the `["pass", "cleanup"]` order; a route
mismatch; a refused pass; a session that cannot pass, refused before staging;
the facade delegate; and the port's set being unchanged.

### An adaptation of the reviewer's cases, disclosed

Adding two required operands changed three signatures, so three call sites in
the reviewer's cases and shared harness needed mechanical adaptation:
`_after_start` gains a session argument and two keywords, `run_dogfood_task`
gains `session=`/`review_route=`, and the `preflight` fixtures gain the route.
**No assertion of theirs was changed** — only the calls, and only as much as
the new signatures require.

### Verification

From `v12/python`:

    PYTHONPATH=src python3 -m unittest tests.tools.test_dogfood_operator
    -> 77 tests, OK.

    PYTHONPATH=src python3 -m unittest tests.tools.test_dogfood_operator
      tests.tools.test_parallel_runner tests.manager.test_dependencies
      tests.manager.test_attempts tests.manager.test_secrets
    -> 472 tests, OK (1 skipped).

    py_compile passed; the whitespace check passed.

### Still absent, by my own report

The serial whole-arc Docker gate, the documented reusable command, the durable
redacted evidence writer, and the replay / fresh-root / fresh-credential
proofs. Four of the acceptance's five bullets still have no gate behind them;
this round spent itself on the approved transition and the P2.

## 2026-08-30 — tenth round (`baton.claude`, W39358 impl claim)

Correcting `review-2026-08-30T12-27-41Z.md`, and closing three of the four
acceptance surfaces that have been outstanding since the Work was filed.

### [P0] A Route echo was accepted as proof the exact assignment was passed

`_passed` accepted any document whose `route` matched the operand. An answer
about ANOTHER generation that happened to echo the route was retained as this
attempt's successful review pass — and cleanup then ran on the strength of a
transition that ended somebody else's assignment.

The closed result is now held whole: `assignment`, `route`, `cause`, `phase`,
`gate` and `fenced`, all six required. The ended ASSIGNMENT is compared to
`expect`, the route is checked beside it rather than instead of it, and the
transition must be an unfenced `pass` — `cause` is what tells a release, a
cancel and a pass apart, and a fenced ending is not the lifecycle transition
this arc performs. The reviewer's wrong-generation witness passes.

### [P1] The facade advertised a pass its minted session could not perform

`DeploymentSession.__init__` held the port's operations and not its own eighth,
so `pass_work` was callable over a session that had none — and
`run_dogfood_task`'s preflight, which asks the FACADE, was satisfied by the
very method that would fail. A capability check that inspects the wrapper
rather than the thing wrapped is not a check. The eighth is now checked with
the six, and the reviewer's constructor witness passes.

### [P2] Applied under explicit authorization

The reviewer's `test_transport_and_disposition_failures_do_not_return_around_ending`
now drives the complete `work` answer with an unusable disposition instead of
the impossible `describe`-only shape. Assertions unchanged, exactly as
authorized.

### A DEFECT THE NEW MATRIX FOUND: the arc could not run at all

See FINDING.md. `compose_input_root` seals the input root read-only as its last
act; `_copied_task` then wrote into it. Every composition case for nine rounds
patched `compose_input_root` to a no-op, so the seal never happened and the
write always succeeded. The first case to run the real operation failed
immediately. The task is now written before the root is sealed.

This is the strongest argument in this dossier for the matrix the reviewer has
been asking for since the beginning, and it is an argument against my own
previous rounds.

### Acceptance surfaces closed this round

**The documented command.** `python3 tools/dogfood_operator.py --grants
GRANTS.json --evidence OUT.json`, with the grants document specified member by
member in the module docstring. `read_grants` holds the file to a closed set —
a member this build does not read cannot sit in a file looking like it was
honoured — and sweeps it under §13, because a grants file is a durable surface
an operator edits by hand and the likeliest place a bearer is pasted "just for
a moment". Reusing it for another bounded task is changing `task_path`,
`source` and the identities, and nothing in the module. The session, the
bearer and the credential delivery are launcher operands rather than file
members, for the same §13 reason. Exit status is `0` only for a resolved
attempt.

**The durable redacted evidence writer.** `write_evidence` holds three things
in order: the §13 sweep over the whole document at any depth, using the
manager's own owner; the closed member set, so an upstream member added
without thought cannot ride out to a durable file unexamined — which is
exactly how raw provider text reached `result.json` in W39357; and the size
ceiling, before the write rather than after. The write is atomic and durable:
composed beside the destination, renamed onto it, directory synced. Every
member now exists from the start of the arc, so an absent one means something
and a `None` one is a fact an operator can read.

**The replay / fresh-attempt matrix.** `TheArcIsEffectivelyOnceAndAFreshAttemptIsFresh`
runs the arc against a REAL `ControlStore` with the manager operations that
own the property under test unmocked — a case that mocked the journal would
be asserting its own mock. Two cases: an exact replay starts no second runtime
and opens no second provider turn, and a fresh attempt receives fresh roots
after the predecessor's ending releases the runtime lane.

The replay case records HOW the property is kept: by refusal at staging rather
than by resumption. That limitation is written up in FINDING.md rather than
left to read as resumption, because the two look identical in a passing test
and very different to an operator whose attempt died half-way.

### Verification

From `v12/python`:

    PYTHONPATH=src python3 -m unittest tests.tools.test_dogfood_operator
    -> 95 tests, OK (79 before this round).

    PYTHONPATH=src python3 -m unittest tests.tools.test_dogfood_operator
      tests.tools.test_parallel_runner tests.manager.test_dependencies
      tests.manager.test_attempts tests.manager.test_secrets
      tests.manager.test_workspaces
    -> 569 tests, OK (1 skipped).

    py_compile passed; the whitespace check passed.

### The one acceptance surface still absent

The registered serial real-Docker gate over the real dogfood image. I stopped
short of it deliberately rather than run out of care on it: this round found
that the arc could not run and recorded a replay limitation that wants a
ruling, and a real-engine gate written over an arc whose staging behaviour may
change on that ruling would have to be rewritten with it.

## 2026-08-30 — eleventh round (`baton.claude`, W39358 impl claim)

`review-2026-08-30T12-40-47Z.md` and the pinned M46985/M46497 rulings. Every
item is implemented, and the last acceptance surface is closed.

### [P0] The documented command now executes

See FINDING.md. The launcher is the deployment's own half of the world — the
framed `docker exec` channel, the engine runner, the adapter factory, the
store opening and the minted bearer — and it was simply absent, so the
documented line defined functions and exited 0. `main` now takes one injected
capability-builder that is a function of the grants, because nothing can be
built before the file naming the authority store, the control store and the
credential home has been read. The reviewer's witness passes: the command runs
and fails at the grants boundary.

### [P1] `phase` and `gate` are held rather than carried

A member held only for presence is a member not held. The pass must leave the
Work `queued` and ungated for its review route to claim; an answer with
`phase="active"` behind a live quiescence gate is refused.

### [P1] The fresh-credential proof is observable

The previous case proved distinct workspace paths and left the credential half
to a coincidence. Each attempt now carries a NAMED delivery and the adapter
factory records what it was handed, so "an attempt was launched with another
attempt's credential delivery" is a sentence a failure can print.

### M46497 item 6 — settlement is always requested after a committed receipt

Already the behaviour; now witnessed, with the reason written down. It is safe
because the MANAGER refuses destructive cleanup over a live assignment, so an
uncommitted pass produces an explicit unresolved attempt for retry or W44716
abandonment rather than a torn-down runtime. Successful cleanup stays ordered
behind a committed pass by the manager's own rule rather than by this
deployment second-guessing it.

### Ruling item 7 — the narrow handoff retry

`retry_handoff` does exactly two things, the pass and the ending, and is
defined as much by the seven things it does not do: no restage, no
reassignment, no runtime start, no provider turn, no worker run, no freeze, no
rederivation. Each is asserted by a manager operation wired to raise if it is
called.

A worker that succeeded, whose output was frozen and whose candidate this
operator independently rederived, is not made untrustworthy by a `pass_work`
that refused afterwards. Abandoning it would throw away completed work over a
failure in the machinery after it; another provider turn would pay for that
work twice and produce a different result. Both steps are idempotent, and the
retry REFUSES an attempt with no trusted result — that one's ending is
W44716's abandonment.

### Ruling item 8 — durable evidence survives a post-start fault

The record rides out on the exception. It is local to the arc, so a launcher
catching a propagating fault has no other way to reach it, and a container
that started with an attempt now unresolved is exactly the case an operator
needs the file for. The fault still propagates, because an implementation
defect is not an attempt outcome. A fault carrying no record writes nothing,
because inventing an empty one would report an attempt that never started.

### THE LAST ACCEPTANCE SURFACE: the real-Docker arc gate

`tests/tools/test_dogfood_arc_engine.py`, registered serial, over the image
W39357's recipe builds. Nothing about the engine is supplied: the adapter is
the real `OciAdapter` over a real `EnginePort`, the channel is the launcher's
own `docker exec` pipe, and the container is one the manager's own operations
started.

The observed run, recorded because it is the evidence: a real container id,
the worker entrypoint answering `describe` AND `work`, the conversation then
ending `lost` because the session's ending could not be read — the
unauthorized-provider dry run the acceptance names — the abandonment fencing
and removing, and the daemon answering `absent` when asked separately.

The rerun case asserts M46497's ruling against the daemon: an exact
same-attempt rerun refuses before a second real container.

### And it found the second defect of this Work

Composing that gate is what exposed `WORKER_PROGRAM` naming the worker module
rather than the image's own entrypoint — the fixture-agent defect in
FINDING.md. That is two arc-breaking defects found by two real-execution
cases, after nine rounds in which neither was visible.

### Verification

From `v12/python`:

    PYTHONPATH=src python3 -m unittest tests.tools.test_dogfood_operator
    -> 105 tests, OK (97 before this round).

    PYTHONPATH=src python3 -m unittest tests.tools.test_dogfood_operator
      tests.tools.test_parallel_runner tests.manager.test_dependencies
      tests.manager.test_attempts tests.manager.test_secrets
      tests.manager.test_workspaces tests.tools.test_dogfood_arc_engine
    -> 581 tests, OK (1 skipped), including the real Docker arc gate.

    py_compile passed; the whitespace check passed.

### What I have NOT claimed

The dry run reaches the worker entrypoint and gets a protocol answer out of
it. It does not prove a provider turn: no credential is mounted and every
container runs `--network none`, because live provider authorization is
W39364's operator gate. The acceptance asks for a dry run and this is one; a
live turn is that Work's.

## 2026-08-30 — twelfth round (`baton.claude`, W39358 impl claim)

`review-2026-08-30T14-36-46Z.md`. All three findings corrected, and the
positive launcher case the reviewer asked for immediately found three more
defects in my own launcher.

### [P0] A nonzero independent verification was passed to review

`_derived` recorded `verification_status` and `_custody` went straight on to
retention and the pass, so a candidate whose frozen task verification exited
nonzero received the SAME successful authority pass as a verified one.
**Recording a check is not passing it**, and the acceptance's whole point is
an independently derived verification.

Now raised as `_Lost`, deliberately: intake has committed, so the
receipt-authorized ending still runs and the manager is still asked to settle
(M46497 item 6). What does not happen is the pass, which is the one thing a
failed verification must not earn.

### [P0] The narrow retry had no operator entry and trusted presence

`--retry-handoff` is now a mode of the documented command. It reads the
retained evidence record -- the original process is gone, so the trusted
result is whatever this deployment durably wrote down -- holds it to the same
closed member set as the write, and rebuilds the capabilities from the same
grants so the pass and settlement carry the SAME identities and replay rather
than repeat. Nothing worker-side is constructed: no engine runner and no
channel, because it runs no container and opens no conversation.

The trust hold was truthiness, so any non-empty string passed. It is now
`worker_disposition == "completed"` -- the frozen axis is
`completed, unable, plan-rejected, cancelled` and only the first is a result
to hand to review -- and `verification_status == 0`. The reviewer was right
that my positive case supplied the fixture word `succeeded`, which is not in
the worker's vocabulary at all and therefore proved nothing about the real
state; every fixture now speaks the real one.

### [P1] The command hid its required credential source

One public parser now names `--grants`, `--evidence`, `--credential-file` and
`--retry-handoff`. An operand a command requires and does not name is an
operand an operator discovers by failing. The docstring lists every member of
`GRANT_MEMBERS`, and a case asks the DOCSTRING rather than restating the list,
because two lists that agree today are two lists.

### THREE MORE DEFECTS, found by the positive launcher case

The reviewer asked for one because `_launched` had never executed. It ran, and
the real seven-capability construction was broken three ways:

- `ControlStore.open` takes `clock` keyword-only and the launcher passed none,
  so the documented command could not have opened a store at all;
- the credential provider takes `(provider, reference)` -- a reference
  resolved from the trusted profile -- and the launcher's took one operand, so
  it could never have delivered a credential;
- a materialized credential is durable TEXT and the launcher returned bytes.

That is now four defects across two rounds that only ever-executing cases
could find. The pattern is the finding.

### Verification

From `v12/python`:

    PYTHONPATH=src python3 -m unittest tests.tools.test_dogfood_operator
    -> 109 tests, OK (107 with the reviewer's two additive cases).

    ...with test_parallel_runner, test_dependencies, test_attempts,
    test_secrets, test_workspaces, test_custody, test_intake,
    test_failed_start_destroy and test_dogfood_arc_engine
    -> 783 tests, OK (1 skipped), including the real Docker arc gate.

The reviewer's aggregate report described `assignment_workspace` calling
`adopt_workspace_group({"result": ...})`. That was an intermediate state of
the concurrent W43975 edit and is already corrected to `{"workspace": result}`;
the aggregate above reproduces clean over the current tree. The Docker gate
runs here because this launcher has socket access; the reviewer's does not,
and that remains unverified from their side.

## 2026-08-30 — thirteenth round (`baton.claude`, W39358 impl claim)

`review-2026-08-30T14-46-24Z.md`. All three retry findings corrected.

### [P0] The retry rebuilt the ordinary launcher and could never pass

`--retry-handoff` called the same builder as a new attempt, and `_launched`
always calls `CredentialHome.materialize` — which deliberately refuses a
pre-existing root, because an existing root is a live delivery or an orphan to
be ADOPTED and never overwritten. The approved retry case is exactly a refused
pass after committed intake, where the assignment is still live and the root
therefore still exists, so the retry could never reach the pass it promises.
It also called `assignment_workspace`, an allocating, mode-adopting filesystem
operation, in a mode that promises only a pass and a settlement.

`_for_retry` now builds only what those two acts need. The credential
lifecycle is ADOPTED from the manager's own durable state record through
`CredentialHome.adopt`, or is absent when the attempt never had one; the roots
are PROVED to exist rather than allocated; and no engine runner, channel or
provider callback is constructed at all, because a retry runs no container and
opens no conversation. `main` takes it as a separate `retry_capabilities`
operand and refuses rather than treating the ordinary builder as one with a
flag.

### [P0] A successful retry stayed permanently unresolved

The retained record necessarily carries the original failure, and
`_ended_however` reports `resolved` only when `unresolved` is empty — so a
retry that completed both acts wrote a full pass and cleanup beside
`resolved=False` and exited 1 forever.

History is now set aside STRUCTURALLY rather than by matching this
deployment's own wording: the retained sentences are what was true before the
retry, and the retry re-performs both acts and writes what is true after.
Nothing is erased on a prefix, and nothing unrelated is quietly resolved —
`_ended_however` re-runs the manager's own cleanup, so an unproved absence or
an unsettled delivery that is still true comes back on its own account. If the
retry's own acts fail again the history is restored, because a retry that
superseded nothing must not leave a shorter story about the same attempt.

### [P0] Retained evidence was neither safely read nor bound

`read_evidence` now applies the write boundary's two holds: the whole-document
§13 sweep and the byte ceiling. A bearer inserted into an allowed member of an
edited record would otherwise reach authority and manager operands and every
refusal surface composed from them.

And the record now carries `work_ref`, `participant` and `generation`, so the
binding is checkable at all. `_bound` runs FIRST and INSIDE `_retried` — the
mismatch has to be refused before a store, a workspace, a credential delivery
or an adapter is touched, and putting the check only in `main` would leave a
direct caller past it. It compares every identity the handoff is composed
from, not the attempt alone: an attempt name that matched while the work,
participant or generation did not would still be another attempt's result.

Six negative subcases cover cross-attempt, cross-work, cross-participant,
cross-generation, changed image and changed network, plus a positive case
proving an agreeing record reaches the capability path.

The positive launcher case now closes its store handle.

### Verification

    PYTHONPATH=src python3 -m unittest tests.tools.test_dogfood_operator
    -> 114 tests, OK (112 with the reviewer's three additive witnesses).

    ...with test_parallel_runner, test_dependencies, test_attempts,
    test_secrets, test_workspaces, test_custody, test_intake and
    test_dogfood_arc_engine
    -> 776 tests, 1 failure, 1 skipped, and the real Docker arc gate passes.

The one failure is `test_a_retargeted_workspace_store_collides_per_root`, the
reviewer's newest additive witness for **W43975**'s per-root receipt: I made
the workspace store part of the operation IDENTITY as well as the signature,
so a retargeted store derives a different id and forks a fresh act instead of
colliding. That is a real finding and it is W43975's, which currently sits
with the reviewer. I have not acted on it under this claim.

## 2026-08-30 — fourteenth round (`baton.claude`, W39358 impl claim)

`review-2026-08-30T14-59-53Z.md`. Both remaining P0s and the P1 corrected; the
third P0 was the launch seam, delivered under the child Work W47225.

### [P0] The retry could pass over an ordering that never completed

Nothing recorded whether the freeze or the retention decision had COMMITTED,
so a retry could resume an attempt whose `decide_retention` had refused and
hand the result to review anyway. Both are facts of the record now —
`evidence["output"]` from the freeze and `evidence["retention"]` from the
committed decision — and both join `_TRUSTED_RESULT`. A verified custody
receipt is not yet the retained handoff result: the freeze is what makes the
bytes the ones the pass hands on.

### [P0] The root proof followed the aliases allocation forbids

`_proved_roots` used `os.path.isdir`, which follows symlinks, so a home or
root entry linked to another attempt's tree passed and the retry would have
ended over somebody else's material. `assignment_workspace` refuses exactly
that, and a restart lookup that dropped the rule is a second, weaker door onto
the same directories. The home and both roots are now proved unaliased and
resolving to their own paths.

### [P1] The route and the policy are bound, and the read is bounded

`review_route` and `retention_policy_digest` are members of the record and of
`_RETRY_BINDING`, so they are held against the grants before any capability is
constructed rather than taken from the grants unexamined. `read_evidence`
reads at most the ceiling plus one byte: reading a file of unknown size into
memory and measuring afterwards is a ceiling that admits what it refuses.

### Verification

    PYTHONPATH=src python3 -m unittest tests.tools.test_dogfood_operator
    -> 116 tests, OK (114 with the reviewer's two additive witnesses).

    ...with test_parallel_runner, test_dependencies, test_attempts,
    test_secrets, test_workspaces, test_custody, test_intake, test_launch and
    test_dogfood_arc_engine
    -> 809 tests, 3 failures, 1 skipped. The real Docker arc gate passes.

The three failures are `test_a_well_formed_document_from_another_delivery_is_refused`,
`test_adoption_applies_the_member_value_contract` and
`test_adoption_refuses_an_extra_entry_it_would_later_delete` — the reviewer's
newest additive witnesses for **W47225**'s `launch.adopt`, which landed while
that Work sits with them. They are findings against the adoption seam, not
against this operator, and I did not act on them under this claim.

## 2026-08-30 — fifteenth round (`baton.claude`, W39358 impl claim)

`review-2026-08-30T15-10-12Z.md`.

### [P0] Editable evidence could mint a review pass

The finding is exactly right and the sentence in the review is the whole of
it: the retained file is operator-editable and untrusted on read, and
`retry_handoff` treated truthy members as proof that the freeze, the intake
and the retention had COMMITTED. An edited record could hand Work to review
while all three public manager readers reported absence.

Two halves, both corrected.

**The arc records what the manager SAID.** `_custody` wrote `frozen=True`
unconditionally and filled the retention disposition in from the REQUEST when
the answer omitted it. Both were fabrications, and a fabricated fact read back
later is indistinguishable from a real one. It now keeps the exact
`manifest_digest` and `result_id` off the frozen document and the exact
committed disposition and policy digest off the retention answer, with no
default invented for either.

**The retry asks the manager.** `_committed` replay-reads `frozen_output_of`,
`intake_receipt_of` and `retentions_of` and holds each against the record —
the exact frozen manifest, the exact custody artifact set, and a retention
decision covering exactly those artifacts under the same disposition and
policy digest. Absence, disagreement or an incomplete decision all refuse, and
they refuse before `_passed` is reachable. Editable evidence may say what to
look up; it cannot mint what the manager never committed.

### Two harness adaptations, disclosed

`test_the_narrow_retry_converges_after_the_handoff_succeeds` and
`test_an_empty_intake_receipt_still_authorizes_cleanup` are the reviewer's.
The first now says what the manager holds, because the [P0] they filed makes
the retry consult it; the second answers `request_freeze` with the document
that operation actually returns, because the arc no longer asserts a fact in
place of the manager's answer. **No assertion in either was changed** — only
what the fixtures say the manager did. A shared `committed(patches)` helper
carries it so there is one spelling of "what the manager holds".

### Verification

    PYTHONPATH=src python3 -m unittest tests.tools.test_dogfood_operator
    -> 117 tests, OK, including the new durable-fact witness.

    ...with test_parallel_runner, test_dependencies, test_attempts,
    test_secrets, test_workspaces, test_custody, test_intake, test_launch and
    test_output
    -> 866 tests, 3 failures, 1 skipped. Whitespace passed.

The three failures are `test_a_well_formed_document_from_another_delivery_is_refused`,
`test_adoption_applies_the_member_value_contract` and
`test_adoption_refuses_an_extra_entry_it_would_later_delete` — the reviewer's
adoption-boundary witnesses for the child **W47225**, which sits with them.
Not acted on under this claim.

### Open, by the review's own account

W47225 must close before this Work can, and a started attempt whose adoption
returns no delivery must refuse rather than report `not-delivered` during
settlement. The [P1] direction — a manager-owned read-only root proof instead
of a deployment-side check-then-use — is recorded and not implemented; it is
not the failing witness and I have not pre-empted it.

## 2026-08-30 — sixteenth round (`baton.claude`, W39358 impl claim)

`review-2026-08-30T15-25-10Z.md`.

### [P0] Every recorded manager fact is now held

The rule in the review is the one worth keeping: **a member the writer claims
and the reader ignores is an editable alternate fact.** Four of them were:

- `output.result_id` was recorded and never compared. Both members of the
  frozen projection are compared now;
- `intake_receipt` was the boolean `True` — a claim with nothing to compare,
  so the retry could check that intake had happened and not that THIS receipt
  was the one. It is the receipt's own digest now, and compared;
- `custody` recorded artifact ids, content digests and byte counts, and only
  the ids were compared, so an edited digest or size rode through on a
  matching name. The whole projection is compared;
- `retention.artifact_ids` was recorded and never compared against anything;
  and the disposition and policy digest were composed partly from the REQUEST.
  They are taken from `decide_retention`'s own answer now, and the recorded
  set is held against what intake took custody of.

Every member of every projection is either held or not recorded.

### Fixture adaptations, disclosed

The reviewer's `test_an_empty_intake_receipt_still_authorizes_cleanup` now
answers `request_intake` with a receipt carrying its own digest, because an
empty receipt is still a receipt with an identity. Assertions untouched. The
shared `committed()` helper and the success harness answer with the complete
documents those operations actually return.

### Verification

    PYTHONPATH=src python3 -m unittest tests.tools.test_dogfood_operator
    -> 119 tests, OK, including all four subcases of the new table witness.

    ...with test_parallel_runner, test_dependencies, test_attempts,
    test_secrets, test_workspaces, test_custody, test_intake, test_launch,
    test_output and test_dogfood_arc_engine
    -> 875 tests, 1 failure, 1 skipped. The real Docker arc gate passes.
       Whitespace passed.

### The one failure is W43975's, and it is destructive

`test_workspaces.CleanupTouchesOnlyWhatWasCreated.test_execution_cleanup_refuses_a_home_alias_to_a_sibling`
— "containment inside the store is not ownership of this attempt". It is the
reviewer's newest witness against `discard_execution_roots`, the contained
removal I wrote under **W43975** last round: an attempt home that is a symlink
to a SIBLING still resolves inside the configured store, so `_contained`
accepts it and the removal enters the other attempt's roots.

That is a real defect and a deleting one. W43975 sits with the reviewer, so I
have not acted on it here — it is named in this handoff so nobody has to
rediscover it, and it is the first thing I take when that Work returns.

### Open close gates, unchanged

Child W47225; the manager-owned read-only root proof; and the public retry's
real failed-handoff durable-state case across fresh process construction.

## 2026-08-30 — seventeenth round (`baton.claude`, W39358 impl claim)

`review-2026-08-30T15-34-00Z.md`. W47225 is closed; the [P1] is corrected and
the standing [P1] direction is now implemented.

### [P1] An editable record was parsed rather than held

`read_evidence` proved the top-level member SET and the secret boundary, and
neither of those makes an allowed member a DOCUMENT. A retained `True` where a
projection belongs is untrusted operator input, and leaking `AttributeError`
or `TypeError` out of it made the documented retry an unsafe parser rather
than a typed boundary.

`_held_record` proves the nested contract in one pass, FIRST, before any
member is consumed — a document checked as it is used has already been used
wrongly by the time the check fails. `output`, `intake_receipt`, `retention`
and `independent` are documents with typed members; `custody` is a non-empty
list of documents with a typed id, digest and size; and `bool` is deliberately
not accepted where `int` is, because a retained `True` verification status is
a claim nobody measured.

### The root proof moved to the manager, as the standing [P1] asked

`workspaces.adopted_assignment_workspace(storage, assignment_id)` is
allocation's own question asked read-only — not a link, a real directory,
resolving to its own path under the configured store — applied to the home and
both roots, allocating nothing and changing no mode or group. It answers the
same `AllocatedRoots` an allocation does, so the adapter receives roots whose
provenance is the manager's rather than this deployment's assertion about
them.

`_proved_roots` keeps its name and delegates. What moved is WHERE the proof
lives, not what the function is for — and the reviewer's alias witness names
it, so nothing of theirs needed adapting.

### Verification

    PYTHONPATH=src python3 -m unittest tests.tools.test_dogfood_operator
    -> 120 tests, OK, including all five subcases of the malformed-record
       witness.

    ...with test_parallel_runner, test_dependencies, test_attempts,
    test_custody, test_intake, test_secrets, test_launch and
    test_dogfood_arc_engine
    -> 747 tests, OK (1 skipped). The real Docker arc gate passes. Whitespace
       passed.

### One failure elsewhere, and it is W43975's

`test_workspaces.CleanupTouchesOnlyWhatWasCreated.test_execution_cleanup_does_not_follow_a_root_replaced_after_proof`
— "the ownership proof and destructive use are one boundary". It is the
reviewer's newest witness against `discard_execution_roots`, which I wrote
under **W43975**: the root is proved by path and then removed by path, so a
replacement between the two is followed. That is the same check-then-use shape
the [P1] above just removed from this Work's root proof, in the removal rather
than the read — and it deletes. W43975 sits with the reviewer; not acted on
here, and it is the first thing I take when that Work returns.

### Still required

The public retry's real failed-handoff durable-state case across fresh
process/capability construction.

## 2026-08-30 — eighteenth round (`baton.claude`, W39358 impl claim)

`review-2026-08-30T15-41-53Z.md`.

### [P0] An editable record could suppress the authority replay

`retry_handoff` called `_passed` only when the record held no pass, so a
plausible projection typed into the editable file skipped the authority call
entirely — an evidence member had become an alternate authority fact.

The pass is always replayed now. Replaying is both safe and necessary: it
carries this attempt's own operation identity, so the authority returns its
committed answer rather than passing twice, and that answer is the only thing
that can show the pass happened. A recorded projection is held WHOLE against
it. The file may identify what to replay; it cannot prove it.

**A case of mine was superseded by that finding and I rewrote it rather than
weakening the new rule.** `test_the_narrow_retry_is_idempotent_over_an_already_committed_pass`
asserted that a recorded pass meant no authority call at all — which is
exactly the hole. It is now
`test_the_narrow_retry_replays_an_already_committed_pass`: idempotence is at
the AUTHORITY, measured by one replay carrying `pass:<attempt>`, not by this
deployment declining to ask.

### [P1] The nested hold omitted the history it consumes

`historical = list(evidence["unresolved"])` leaked a raw `TypeError` for an
editable boolean — a member used to DECIDE and to REPORT was the one member
not held. `unresolved` is now a bounded list of durable text, with a ceiling
for the same reason the write has one; and `attempt_id`, `runtime_id`,
`worker_disposition` and `review_pass` are held beside it.

### Verification

    PYTHONPATH=src python3 -m unittest tests.tools.test_dogfood_operator
    -> 121 tests, OK, including the suppressed-replay witness and all six
       subcases of the malformed-record table.

    ...with test_parallel_runner, test_dependencies, test_attempts,
    test_custody, test_intake, test_secrets, test_launch, test_workspaces and
    test_dogfood_arc_engine
    -> 831 tests, OK (1 skipped). The real Docker arc gate passes. Whitespace
       passed.

### Two things I did NOT do, and why

**[P1] identity through use for the adopted roots.** The reviewer is right
that moving the check to its grammar owner removes a duplicate rule without
making check-and-later-open one identity. Closing it properly means a
manager-owned adopted-root capability the adapter consumes without reopening
pathnames — the same shape W43975 just built for the destructive seam with
descriptors. That is a change to how `OciAdapter` receives and uses roots,
not a local edit, and I did not want to start it in the remainder of this
round and hand over something half-converted.

**[P0] the real public retry gate.** Still the only successful retry is a
mocked direct-function case. A real one needs durable state where freeze,
intake and retention actually committed and the pass failed — which means a
real adapter that collects real artifacts — and then the public
`--retry-handoff` launcher across fresh capability construction. It is the
acceptance gate and it is large; I have not built it and am not describing
the mocked case as standing in for it.

## 2026-08-30 — nineteenth round (`baton.claude`, W39358 impl claim)

Both prior findings are accepted. The two remaining gates are the close gates,
and this round did NOT close either. What it did produce is the fact that
makes the first one tractable, recorded here so the next round starts from it
rather than rediscovering it.

### The acceptance gate is buildable, and here is the shape

The obstacle to a real `--retry-handoff` case has been that the retry needs a
REAL authority — `pass_work` is the act under test — while the durable
failed-handoff state needs the manager's own operations, which the suites
drive through a fake session. I had been treating those as two authorities.

They are one. A real `baton_v12.authority.Session` carries six of the seven
operations `AuthorityPort` names — `project_work`, `slot_holder`, `claim`,
`settle_operation`, `assignment_of`, `cancel` — and the seventh,
`publish_answer`, is exactly the one `DeploymentSession` supplies as its own
typed refusal and deliberately does not require of the session it wraps. So
`AuthorityPort(DeploymentSession(real_session), claim_signature)` satisfies
the port, and ONE real authority serves both the durable-state construction
and the pass under test.

A real assignment is three calls: `authority.create_work(...)`,
`authority.add_route_handler(route, participant)`, and
`session.claim({"work_id": ..., "operation_id": ...})["assignment"]`.

So the case is: one real authority and one real control store; drive
freeze/intake/retention through the real port to committed durable state; fail
the pass; write the evidence record with `write_evidence`; write the grants
file; then `main([... "--retry-handoff"], retry_capabilities=_for_retry)` and
assert the authority recorded the pass, the manager settled, and nothing
worker-side ran.

### Why it is not written

It is a large fixture — the freeze needs a sealed result whose assignment
identity matches the real work, participant and generation — and I reached
the point in this round where starting it meant handing over something
half-built. A failing half-built acceptance gate is worse than an honest
report of an absent one, and this is the third round I have said it is
absent, so the plan above is the part I could usefully add.

### The other gate, unchanged

Manager-proved root identity surviving adapter use. `adopted_assignment_workspace`
returns path strings the adapter later reopens, and the reviewer is right that
moving the check to its grammar owner did not make check-and-later-open one
identity. The shape is the one W43975 built for the destructive seam:
descriptors held through use rather than names re-resolved. It is a change to
how `OciAdapter` receives and consumes roots.

### Verification

    ...eleven modules including the real Docker arc gate
    -> 926 tests, OK (1 skipped). Whitespace passed.

Nothing in the tree changed this round; the sweep is the confirmation that
what the previous rounds landed is still green.

## 2026-08-30 — twentieth round (`baton.claude`, W39358 impl claim)

The acceptance gate is written, and building it found two real defects that
every mocked case had hidden.

### The real public retry, from real durable state

`ThePublicRetryRunsFromRealDurableState` builds on the intake fixture and
swaps in a REAL authority: `Authority.create`, `create_work`,
`add_route_handler`, and the deployment's own `DeploymentSession` over a real
`Session`. The manager's offer, claim, activation, freeze, intake and
retention all run through `AuthorityPort` over that facade, so the assignment
the retry passes is the one the claim really created.

It then fails the handoff, writes the record with `write_evidence`, writes the
grants file, and crosses the documented
`--retry-handoff` command through `_for_retry` — the real capability builder —
in a fresh construction. The assertions ask the AUTHORITY, not the record:
the assignment is ended and the Work sits on `rview`. Nothing worker-side
runs, asserted by `converse`, `stage_source` and `_derived` never being
called.

### TWO DEFECTS ONLY A REAL AUTHORITY COULD FIND

**`pass_work` was called with a shape no `Session` has.** A real session takes
EXACTLY ONE operand document — "one exact built-in operand document, taken
ONCE" is the authority's own rule for every session act — and this deployment
passed keywords. `PassingSession` accepted keywords for fifteen rounds and
taught the deployment a shape the authority does not have, so every green
retry case was green about the wrong call. The facade, `_passed` and both
fakes now use the one-document form.

**The deployment's engine runner took no deadline.** W43975's custody act
refuses an engine capability it cannot bound, and `_engine_run(argv)` had no
`seconds` at all — so every ending that settles through a directory act was
unreachable from the documented command. It honours the manager's deadline
now.

That is six defects across three rounds that only ever-executing cases could
find, and this pair is the sharpest: both were invisible precisely because the
fakes were more permissive than the real components.

### What the gate honestly proves, and what it does not

The settlement is REQUESTED and does not complete: no real container was ever
started, so the custody helper has no engine to run against and the manager
says so. The case asserts that rather than pretending otherwise. Completing
that ending against a real daemon is the arc gate's job, not this one's.

### Verification

    PYTHONPATH=src python3 -m unittest tests.tools.test_dogfood_operator
    -> 122 tests, OK.

    ...with test_parallel_runner, test_dependencies, test_attempts,
    test_custody, test_intake, test_secrets, test_launch, test_workspaces and
    test_dogfood_arc_engine
    -> 892 tests, OK (1 skipped). The real Docker arc gate passes. Whitespace
       passed.

### The remaining close gate

Manager-proved root identity through adapter use. `_for_retry` now flattens
the manager's `AllocatedRoots` with `dict(...)` exactly as the ordinary
launcher does, because the adapter's boundary takes built-in documents — and
that flattening IS the standing [P1]. It is recorded at the call site rather
than papered over.

## 2026-08-30 — twenty-first round (`baton.claude`, W39358 impl claim)

### [P0] The failed handoff is now PRODUCED, not composed

You were right and the distinction matters: a record the test assembles to
look like a failed handoff cannot prove that the real failure path produces a
retryable one. The gate now runs the ordinary public command FIRST — real
authority, real control store, real manager operations, with `pass_work` made
to refuse — and the retry is then given only what that command actually wrote:
its own grants file and its own evidence.

The case asserts the ordinary half is a real failure before it retries: exit
1, no `review_pass`, a reason the command wrote itself, and manager facts —
frozen manifest, receipt digest, retention disposition — that the ARC recorded
rather than the fixture.

Getting there fixed several fixture untruths worth naming: the adapter now
answers the freeze from the arc's OWN attempt row and its OWN policy digest,
and observes `quiescent` only after a stop, because that is the sequence the
arc performs.

### [P1] The retry's handles are closed

`_for_retry` opens an authority and a control store and `_retried` closed
neither, so a command that ran a retry left two SQLite handles behind — and a
handle this process still holds is a lock the next incarnation waits on. The
builder now answers what it opened and the caller closes it in a `finally`.

### Verification

    PYTHONPATH=src python3 -m unittest tests.tools.test_dogfood_operator
      tests.manager.test_intake tests.manager.test_attempts
      tests.manager.test_custody tests.manager.test_launch
      tests.manager.test_workspaces tests.manager.test_dependencies
      tests.manager.test_secrets
    -> 854 tests, OK (1 skipped). Whitespace passed.

### The two still open, and my previous statement was wrong

I said root identity was the only remaining close gate. It was not, and you
corrected it: **complete manager settlement across fresh capabilities is the
other half of the same gate and is still absent.** The retry proves the exact
authority pass and reaches the manager's ending; the ending does not converge,
because settling requires the custody act to run a real helper container and
this case supplies no engine. Making it converge means making this a
real-engine gate — which is the honest shape and which I have not built.

**Manager-proved root identity through adapter use** is unchanged and
acknowledged at both call sites.

## 2026-08-30 — twenty-second round (`baton.claude`, W39358 impl claim)

### [P1] The ordinary launcher leaked what the retry no longer does

I corrected the retry path last round and left the ordinary one, so the
documented command still left an authority and a control store behind on every
run — and a handle this process still holds is a lock the next incarnation
waits on. One rule, both builders: `_launched` answers what it opened and
`main` closes it in a `finally` that also covers the fault path, because a
command that faulted still held two durable handles.

The positive launcher case asserts the builder says what it opened, and the
focused suite now passes under `-W error::ResourceWarning`.

### The two close gates, and what the settlement one actually needs

**Complete manager settlement across fresh capabilities.** The retry reaches
the manager's ending and the ending cannot converge without an engine: the
custody act runs `python3 -c CUSTODY_PROGRAM` inside the attempt's image, so
settling requires a real daemon and a real image. That means the converging
case belongs in the real-Docker gate, where both exist — and it needs a
fixture that combines the intake suite's freeze/intake/retention composers
with the Docker lifecycle, which neither existing fixture has.

I did not start that in the remainder of this round. It is a fixture of the
same size as the one built in round twenty, and half of it would be worse than
none.

**Manager-proved root identity through adapter use** is unchanged, and the
review is right that both paths flatten. Closing it means the adapter
consuming an identity rather than reopening path strings — the descriptor
shape W43975 built for its destructive seam, applied to `OciAdapter`.

### Verification

    PYTHONPATH=src python3 -W error::ResourceWarning -m unittest
      tests.tools.test_dogfood_operator
    -> 122 tests, OK, with the resource warning as an error.

    ...with test_intake, test_attempts, test_custody, test_launch,
    test_workspaces, test_dependencies, test_oci and test_dogfood_arc_engine
    -> 858 tests, OK (1 skipped). The real Docker arc gate passes. Whitespace
       passed.

## 2026-08-30 — twenty-third round (`baton.claude`, W39358 impl claim)

### [P1] Construction now unwinds locally, in both builders

The finding is right and the sentence is the whole of it: a builder answers
`closing` so its caller can release what it opened — but only if it RETURNS.
An authority opened before a control store that then fails is an authority
nobody disposes, because the bundle carrying its release never exists. The
caller cannot clean up what it was never handed.

`_unwinding` releases in reverse and swallows a failing release, because a
release that fails must not hide the fault that caused the unwind. Both
`_launched` and `_for_retry` register each handle as they open it and unwind
on any fault. `materialize` tears its own root down for exactly this reason;
this is the same rule for handles.

### The reviewer's witness cannot observe any implementation

`test_the_launcher_closes_a_partial_build_when_a_later_open_fails` builds
`released = mock.Mock(wraps=opened.dispose)` and never assigns it onto
`opened`. The builder therefore calls the real bound method and the wrapper is
never reached, so `released.assert_called_once_with()` fails for ANY
implementation, including one that disposes correctly.

**I have not touched it.** I added
`test_a_partial_build_disposes_the_authority_it_already_opened`, which is the
same property with the recorder INSTALLED on the object the builder is handed
— `opened.dispose = released` — and it passes. The one-line change theirs
needs is that assignment; it is theirs to make or authorize.

I also damaged the module's indentation part-way through this edit and
repaired it; the suite is what caught it, which is the argument for running it
between structural edits rather than after them.

### Verification

    PYTHONPATH=src python3 -W error::ResourceWarning -m unittest
      tests.tools.test_dogfood_operator
    -> 123 tests, 1 failure — the witness above and nothing else.

    ...with test_intake, test_attempts, test_custody, test_launch,
    test_workspaces, test_oci and test_dogfood_arc_engine
    -> 839 tests, 1 failure. The real Docker arc gate passes. Whitespace
       passed.

### The two close gates, unchanged

Complete real-engine retry settlement, and manager-proved root identity
through adapter use. Neither moved this round.

## 2026-08-30 — twenty-fourth round (`baton.claude`, W39358 impl claim)

### [P1] The manager's proved roots survive to the adapter's use

Every caller flattened `AllocatedRoots` to a plain `dict` because `_roots`
validates with `boundaries.document`, which refuses anything carrying
behaviour — and the flattening threw away exactly the fact worth keeping.

`_roots` now ADOPTS a nominal answer instead of re-deriving it.
`AllocatedRoots` is minted only by `assignment_workspace` and
`adopted_assignment_workspace`, both of which prove each root is a real
directory of this attempt's own — not a link, resolving to its own path under
the configured store — and a caller can neither construct one nor retarget
one. Canonicalizing it again would resolve the pathname a SECOND time, which
is the check-then-open interval this correction exists to close.

A plain mapping is still accepted and still proved there, because callers
outside the allocation path legitimately hold one. Both operator call sites —
the ordinary launcher and the retry builder — now pass the manager's answer
unflattened; `assignment_roots=dict(...)` appears nowhere.

Three witnesses: a nominal answer is accepted without being flattened and each
root is the one the manager proved; the adapter holds what it was given; and a
plain mapping is still canonicalized and contained by that owner.

**The limit, stated rather than left to be discovered.** This preserves the
manager's proved ANSWER through construction and use. It does not carry a
descriptor into the engine invocation, and cannot: `--mount source=` takes a
path, so the strongest property available at that boundary is that the path
the engine is handed is the one the manager proved rather than one this
deployment re-resolved. Descriptor-held identity is available to acts that run
in this process — which is what W43975's removal uses — and not to acts that
cross into a daemon.

### Verification

    PYTHONPATH=src python3 -m unittest tests.manager.test_oci
    -> 95 tests, OK, including the three new witnesses.

    ...with test_dogfood_operator, test_intake, test_attempts, test_custody,
    test_launch, test_workspaces, test_lifecycle_composition and
    test_dogfood_arc_engine
    -> 874 tests, OK (1 skipped). Both real-engine gates pass. Whitespace
       passed.

### The one close gate left

Complete real-engine fresh public retry: settlement, absence and resolution
with no second worker act. It needs a fixture combining the intake suite's
freeze/intake/retention composers with the Docker lifecycle, because settling
runs the custody helper inside the attempt's image. That is the whole of what
remains from my side.

## 2026-08-30 — twenty-fifth round (`baton.claude`, W39358 impl claim)

### [P1] The nominal answer is returned as ITSELF, not copied

My previous cut preserved the VALUES and dropped the type: `_roots` built a
plain mapping from the nominal one, the adapter held that, and `run_vector`
re-entered `_roots` with it — where it took the canonicalizing branch, which
is the exact re-resolution the correction was meant to remove.

**Provenance that survives one call and not the next is not provenance.**
`_roots` now returns the `AllocatedRoots` it was given. Verified directly: the
first call keeps the type, re-entry keeps it, and the object is the same one
the manager minted — so no path is resolved a second time anywhere along the
adapter's use.

The reviewer's `test_the_adapter_retains_the_managers_nominal_answer` passes.

### Verification

    PYTHONPATH=src python3 -m unittest tests.manager.test_oci
    -> 96 tests, OK, including the identity regression.

    ...with test_dogfood_operator, test_intake, test_attempts, test_custody,
    test_launch, test_workspaces, test_lifecycle_composition,
    test_input_delivery and test_dogfood_arc_engine
    -> 929 tests, OK (3 skipped). Both real-engine gates pass. Whitespace
       passed.

### The one gate left

Complete real-engine public retry settlement. Unchanged, and it is the whole
of what remains from my side.

## 2026-08-30 — twenty-sixth round (`baton.claude`, W39358 impl claim)

The [P1] is signed off, so this round went at the last gate -- and found that
it is BLOCKED rather than merely large. That is a change to the ledger, so it
is reported rather than promised again.

### What I actually ran

I drove the ordinary public command over a REAL world: a real authority with a
real Work and route handlers, a real control store, real workspace storage, a
real credential home and delivery, the real `_launched` builder, real Docker,
and the reference worker image the lifecycle suite builds. No mocks at all.

The container started, the transport reached it, and the conversation ended:

    ending: lost
    why:    the worker ended the channel without answering describe

The reason is exact. The reference image carries `baton_worker.py` and
`scripted_agent.py`; it has no `dogfood_entry.py`, which is what
`WORKER_PROGRAM` execs. That binding is not an accident -- it is the
fixture-agent defect this Work already corrected, where naming
`baton_worker.py` would have run the M2 stub and reported its output as the
worker's work. The operator is correctly bound to the DOGFOOD image's own
entry.

### Why the gate is blocked, not just big

The retry's trusted result requires `worker_disposition == "completed"`, a
committed freeze, a committed intake receipt and a committed retention
decision. Those exist only if a worker really COMPLETED. Through this
operator, the only worker that can is the Claude agent in the dogfood image --
and a real turn from it needs the operator's credential grant and network
posture, which this dossier's own acceptance assigns elsewhere:

> *A real Docker dry run reaches the worker entrypoint without relying on the
> spike lifecycle. **Live provider authorization remains W39364's operator
> gate.***

So "complete real-engine retry settlement across fresh capabilities" cannot be
built here without W39364. Substituting the reference image would mean
un-fixing the entry binding; substituting a fake adapter would make it not a
real-engine gate.

### What I am asking for

Either a ledger dependency on W39364 recorded against this gate, or a ruling
that the gate is satisfied by what the existing cases prove -- the real arc
reaching the worker entrypoint, and the public retry replaying the exact
authority pass over durable state a real failing command produced. I am not
deciding that myself, for the same reason I did not decide W43977's scope.

### Verification

Nothing in the tree changed this round. The probe ran from `/tmp` and is
deleted. The previous round's sweep stands: 929 tests, OK (3 skipped), across
ten modules with both real-engine gates passing.

## 2026-08-30 — twenty-seventh round (`baton.claude`, W39358 impl claim)

### My blocker was wrong, and the refutation was right

I claimed the gate needed W39364's live provider authorization. The reviewer's
answer is the one I should have found: a TEST-OWNED image can keep
`/opt/baton/dogfood_entry.py` at the exact path `WORKER_PROGRAM` execs — so
the binding this Work already corrected stays corrected — while injecting a
deterministic agent through the same documented seam the Claude adapter uses.
A live provider turn is W39364's; a worker that really completes is not, once
the agent behind the seam is one this suite owns.

`tests/tools/test_dogfood_retry_engine.py`, registered serial, derives that
image from the reference worker and proves the entry is present at the path
the operator execs.

### AND IT FOUND A DEFECT THAT HAS BEEN FALSIFYING THIS DOSSIER

`_Channel.finish` answered a bare integer. `worker_entry._finished` requires
the document `{status, stderr}` and treats anything else as unreadable — so
**every real conversation this deployment has ever held ended `lost` with "the
session's ending could not be read"**, no matter what the worker did.

That is the ending the arc gate reported, and PROGRESS.md recorded it as the
unauthorized-provider dry run: *"the worker entrypoint answering describe AND
work, the conversation then ending lost because the session's ending could not
be read — the unauthorized-provider dry run the acceptance names."* The worker
had answered. The channel could not say so. My reading of that evidence was
wrong and the record said so confidently.

`finish` now answers the document, keeping a bounded stderr window that is
never written anywhere durable — W39357's rule that provider diagnostics on a
durable surface are a credential disclosure still holds.

With it fixed, the ordinary public command reaches a REAL completed result: a
real container, a real worker, a real transport, `ending: answered` and
`worker_disposition: completed`, in about thirty seconds.

### What the second half still needs, exactly

The freeze then refuses: *the worker's envelope answers 'proposal', which this
assignment did not declare (§12 rule 15)*. The operator declares one
`directory-result` named `proposal` at path `proposal`; the scripted agent's
envelope does not match that shape. The remaining step is a purpose-built
proposal-writing agent in the test image whose envelope answers the
operator's own declaration — which is what the review said in the first place
("a deterministic proposal-writing agent"), and I reached for the existing
scripted one instead.

The unwritten case is marked in the test file rather than left implied. Two
cases are landed and green.

### Verification

    PYTHONPATH=src python3 -m unittest tests.tools.test_dogfood_operator
      tests.tools.test_dogfood_arc_engine tests.tools.test_dogfood_retry_engine
      tests.manager.test_oci tests.manager.test_intake
      tests.manager.test_attempts tests.manager.test_custody
    -> 729 tests, OK. All three real-engine gates pass. Whitespace passed.

## 2026-08-30 — twenty-eighth round (`baton.claude`, W39358 impl claim)

Acting on the review found THREE more launcher defects, each of the same
shape: an operand the factory accepted and never forwarded.

### The launcher dropped the assignment's declared outputs

`adapter_of` took `declared` and did not pass it to `OciAdapter`, so the
adapter had no declarations and the freeze refused every real completed result
with *"the worker's envelope answers 'proposal', which this assignment did not
declare (§12 rule 15)"*. The worker answered exactly what the manager asked
for; the launcher never told the adapter what that was. I had read this as a
worker-shape mismatch and it was not.

### It dropped the input manifest digest too

Same factory, same shape: accepted and never forwarded, so the sealed result
carried no `input_manifest_digest` and broke the frozen schema.

### `_derived` treated a URI as a path

The real intake receipt carries `file:///...`, and `_derived` joined it as a
filesystem path -- so every real derivation died `FileNotFoundError` rather
than refusing. It reads the one scheme this deployment can open and refuses
any other by name.

### The review's other three items

The build context is cleaned. The `rview` handler is WITHHELD until between
the two commands, so the ordinary pass fails at the authority itself rather
than through anything this test wrapped around it. And the assertions the
settling case will make are written.

### Where the gate stands

The ordinary public command now runs a real container, holds a real
conversation answering `describe` and `work`, records `completed`, and the
manager really freezes the result and takes custody of it. The case asserts
exactly that and names where it stops: the scripted agent writes each declared
output but not the `candidate` tree `_derived` rederives against the staged
source.

The purpose-built proposal agent is written and one debugging step from done --
with it installed the conversation ends `faulted` rather than `lost`, meaning
the entry runs and the worker reaches the agent, and one of `consider` or
`work` answers a member set `baton_worker.check_answer` does not accept. I ran
out of round before reading that fault out of the container, so the image
installs the scripted agent and the settling case is marked unwritten rather
than left failing.

### Verification

    PYTHONPATH=src python3 -m unittest tests.tools.test_dogfood_retry_engine
      tests.tools.test_dogfood_operator tests.tools.test_dogfood_arc_engine
      tests.manager.test_oci
    -> 224 tests, OK. All three real-engine gates pass. Whitespace passed.

## 2026-08-30 — twenty-ninth round (`baton.claude`, W39358 impl claim)

### The URI was decoded at one use and not the other

`_derived` decoded `file://` for the candidate tree and then joined
`members_present` below the raw URI string -- so every member answered absent
and the record reported an empty proposal while all four were present. One
decode, one root, both uses: `_proposal_root` validates the scheme and the
absoluteness once and returns the path everything below reuses. That is the
same two-spellings shape as the `which` rule in W43977 and the flattened roots
in this Work; the fix is always one owner.

### The settling case is one fault from done

The proposal agent is written and installed correctly -- the entry parses, the
worker reaches it, and with it the arc gets past the derivation the scripted
agent cannot satisfy. What stops it now is the agent failing
`PermissionError` while writing under `/output`.

The scripted agent writes ONE file directly in the declared directory and does
not fail, so the fault is in one of the nested writes my agent adds: the
`candidate` subdirectory, the copied source files, or the three siblings. The
next step is to read WHICH, from the container rather than by reasoning about
it -- the transport already carries the agent's own fault text.

I restored the scripted agent so the tree is green, and the case asserts what
that agent honestly reaches: a real container, a real conversation answering
`describe` and `work`, a real `completed` disposition, a real frozen result and
a real intake receipt.

### Verification

    PYTHONPATH=src python3 -m unittest tests.tools.test_dogfood_retry_engine
      tests.tools.test_dogfood_operator
    -> 127 tests, OK. Whitespace passed.

## 2026-08-30 — thirtieth round (`baton.claude`, W39358 impl claim)

**The P0 gate is closed. `test_the_public_retry_settles_a_handoff_the_command_failed` passes against a real daemon**, and closing it took three defects out of the tree — all three found by the ever-executing case, none of them findable by reading.

### I stopped guessing and made the container say which write failed

Two rounds went into guessing at `PermissionError`, and both guesses were
wrong. The worker's fault frame deliberately carries `type(failed).__name__`
and no traceback, so the path never travels -- but the TYPE NAME is under the
agent's control. A diagnostic agent that catches `OSError` and re-raises

    type("AT_" + label + "_" + kind + "_errno" + errno + "_on_" + path, ...)

puts the whole diagnosis in the one field the transport does carry, and the
first run answered in full:

    the agent failed: AT_copy_harness_py_PermissionError_errno13_on_|input|source|harness.py

A second probe, stat-ing from inside the container, gave the rest:

    input-0o40555-1000-1000  source-0o40775-1000-1000
    harness_py-0o100600-1000-1000-rFalse  me-65532-[1000, 65532]

That is the whole lesson of this round. The measurement cost one run and two
guesses had cost two rounds.

### Defect 1 — the staged source was delivered owner-only (`workspaces.py`)

`copied_manifest` creates every file it copies with `0o600` and makes its
directories with a plain `os.makedirs`. `compose_input_root` says it exposes
"the whole surface" read-only and chmodded exactly ONE directory: the root.
So the third thing under `/input` -- the source TREE, the material the
assignment tells the worker to work FROM -- was `0o600` and owned by the
manager, beside two documents at `0o444`, and the container's fixed uid 65532
got `EACCES` opening it.

This is W33935's defect one level down. That Work fixed the two DOCUMENTS
because they were the only things anything read; nothing had ever read the
tree, so nothing had ever refuted it. `_frozen_delivery` walks the root
deepest-first and applies the module's own `READ_ONLY_FILE` and
`READ_ONLY_DIR`, and `compose_input_root` calls it where the single `chmod`
was. The directories matter as much as the files: their modes were whatever
the umask produced -- `0o775` measured here and `0o700` under the ordinary
service umask, which is the accident `WORKSPACE_DIR` exists to end.

### Defect 2 — the manager could not remove the worker's own tree

`_emptied` opened `os.fchmod(opened, 0o700)` unconditionally, and `chmod` is
the OWNER's operation. `/output/proposal` is created by the CONTAINER, so it
is owned by 65532 and the manager is not its owner: the first real worker tree
this build ever tried to remove died `EPERM`. Every ending after a completed
worker turn was unreachable, and the reason it had never shown is that no case
had ever reached one -- the green case stopped at `_derived` before cleanup.

The repair is now conditional on ownership. A directory this manager does not
own is not one it may repair and does not need to: `normalize_directory` runs
as the owner immediately before and grants the workspace GROUP rwx on every
object, which is the access the walk actually uses -- and is exactly why the
custodian grants the group instead of chowning. If it did not run, the
`unlink` refuses on its own and the removal fails closed.

### Defect 3 — withholding the review route does not fail a pass

Review 2026-08-30T19:28:05Z directed withholding the `rview` handler so the
ordinary command's pass would refuse. Measured against the real authority: it
does not. `Authority.pass_work` moves the Work's route and ends the
assignment, and neither act consults `route_handler` -- with `rview` withheld
the pass committed and the whole arc resolved. A queued Work on a route nobody
handles yet is an ordinary v11 state, not a refusal.

So the gate produces the failure the way the reviewed operator suite already
does -- a deployment facade whose ONE act refuses -- and installs both routes.

### What the failed command actually leaves, which is better than I assumed

I had assumed the ending still completed and only the pass was missing. The
manager's own answer is sharper: with the pass refused the assignment is STILL
LIVE, so `authorize_cleanup` refuses -- "cleanup destroys the runtime of an
assignment that has ENDED or been fenced". The record carries two unresolved
sentences and NO cleanup, and the two acts missing are exactly the two
`retry_handoff` performs, in the order it performs them: the pass ends the
assignment, and only then is the ending authorizable at all. The runtime is
quiesced either way, so a handoff this deployment could not finish never
leaves somebody's code executing.

### The gate

Ordinary command: real container, real worker, real framed conversation
(`answered`, `describe` + `work`), `completed`, a real frozen manifest digest,
a real intake receipt, `discard-after-intake`, all four `PROPOSAL_MEMBERS`
present, `changed_paths == ["added.py"]` by BYTES against the staged source,
the task's frozen command rerun outside the container exiting 0, quiescent, no
cleanup, two unresolved sentences, exit 1.

Retry: the documented `--retry-handoff` through `_for_retry`, exit 0, the pass
asked of the AUTHORITY (`assignment_of` is None, the Work's route is `rview`),
`unresolved == []`, `resolved`, `cleanup.state == "absent"`, the same
conversation, runtime and output as before, `converse` patched to raise if a
second conversation is opened, and the daemon does not have the runtime.

### Two changes outside this Work's files

Defects 1 and 2 are in `worker_manager/workspaces.py`. I made them because
each is a one-owner correction in the delivery this Work composes and each
blocks the P0 gate outright; both are described above rather than folded in
quietly, and either can be re-routed to its own Work. `sealing._frozen` is the
same walk over custody and I deliberately did NOT merge the two: one owner for
both is a change to a module this Work does not own.

### The escaping trap, prevented rather than re-fixed

`ENTRY` is now a RAW literal. Written ordinarily, every `\n` inside the agent's
own string literals became a real newline when this module was parsed, and the
file the image installs was syntactically invalid -- which reaches the
operator as a bare `faulted` naming nothing true. That cost a round earlier.

### The two manager fixes have their own cases, and both were shown to fail first

A fix nothing refutes is a fix nobody can check, so each was reverted and the
new case rerun before it was kept.

`test_input_delivery.TheWholeDeliveryIsFrozenAndNotOnlyTheRoot` stages a
nested source tree through the manager's own copier, composes the input root
and asks the MODE: every staged file `0o444`, every staged directory `0o555`,
under three umasks, and then the half that was actually missing -- that a
party which is neither owner nor group can traverse and read it, since
`other` is the bit that decides whether the container's fixed uid can open
its source. Reverted, it fails four ways: `448 != 365`, `source is not frozen
to the declared directory mode`.

It deliberately does not run the `0o777` umask the sibling class uses. A total
umask is exact against the ROOT, whose `chmod` was never umask-filtered, but
`copied_manifest` MAKES its own subdirectories -- under `0o777` it creates one
at mode zero and then refuses `EACCES` writing into it. That is the copier's
own question, it fails closed and loudly, and a delivery that never happened
has nothing to freeze.

`test_workspaces.test_the_thaw_is_skipped_for_a_directory_this_manager_does_
not_own` models the foreign owner by moving THIS PROCESS's identity rather
than by making a file somebody else owns, which needs a privilege the suite
must not have: the question `_emptied` asks is "am I the owner", and answering
it `no` is the whole condition. It asserts by INODE and not by call count --
the home's own thaw is a different call site over material this manager
plainly owns, so a bare "never called" would assert something untrue about the
removal as a whole. Reverted, it fails: `27217306 unexpectedly found in [...]:
the walk tried to chmod a directory it does not own`. Its sibling keeps the
other half honest -- a frozen root this manager DOES own is still repaired and
removed.

### Verification

    tests.tools.test_dogfood_retry_engine (real Docker)      2 tests, OK
    + test_dogfood_operator + test_intake + test_custody   326 tests, OK
    test_workspaces test_sealing test_input_delivery
      test_intake test_custody test_output test_launch
      test_dogfood_operator test_attempts                  916 tests, OK
    test_worker_container test_worker_image
      test_dogfood_image test_parallel_runner
      test_workspaces                                      286 tests, OK
    the real-engine gates: test_dogfood_arc_engine,
      test_custody_engine, test_output_custody_engine,
      test_refused_session_engine,
      test_failed_start_destroy_engine,
      test_abandoned_attempt_engine,
      test_lifecycle_composition                            69 tests, OK*

    * one failure on the first pass -- `test_nothing_this_module_made_survives
      _it` saw `baton-w6633-test-f350b9e86162`. That was MY OWN doing: I had
      `test_worker_container` running in a second process at the same time,
      and that case asks the daemon by a shared mark. Rerun alone: 8 tests,
      OK. Worth recording as a property of the suite rather than of the
      change: these gates ask the engine globally, so two of them in parallel
      can see each other's containers.

    Whitespace passed.

### The inventory suites, run and read rather than skipped

`test_boundary_inventory` + `test_dependencies` + `test_contracts_inventory` +
`test_secrets` + `test_text_sweep`: 229 tests, 40 minutes, six failures. Five
are the KNOWN global-scope backlog W43977 is blocked on -- 114 receiving
entries with no owner and 46 owned-but-unprobed across `lanes.py`,
`handshake.py`, `attempts.py` and seven other modules, plus two persisted
columns the universe cannot see. Every one of them is in a module no Work I
hold owns, and they were red before this round.

I DID NOT ASSUME MY CHANGE WAS INNOCENT OF THEM. `_frozen_delivery` is a new
function, and a new function is exactly what could grow that list, so I
computed the unowned set directly and read the `workspaces.py` rows: 27
entries, all of them pre-existing public ones (`copied_manifest`,
`discard_tree`, `adopt_workspace_group`, the three value classes). The new
function appears in none of them -- it is private, and the inventory tracks
the module's public receiving surface.

The sixth was mine and is fixed. `test_text_sweep` compares its table to the
exported surface, and W44716's `abandon_attempt` was exported without a row --
so a registered suite has been red since that Work landed and nothing said so.
It now has one, and unlike its three sibling endings it declares a text
operand: abandonment is the only one of the four that carries an OPERATOR'S
OWN SENTENCE, and that sentence becomes durable, so it is swept for a lone
surrogate like every other durable caller text. 3 tests, OK.
