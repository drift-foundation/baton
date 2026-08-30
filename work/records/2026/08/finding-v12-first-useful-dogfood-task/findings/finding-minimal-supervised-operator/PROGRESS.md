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
