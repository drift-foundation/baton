# Progress

## Claim 322179 (baton.claude, impl) — the packet, prepared

Read first: canonical `detail` at snapshot322178 (queued, unclaimed, routed
baton.impl, next baton.bug, parent W61981, blocking W321776, no obligations, no
open blockers, binding revision 1 at this directory), then the standalone claim;
`work-events` complete, events 321780 → 322179, `next_after` null; `thread`
T321780, its single message. Then this child's FINDING and PLAN, the parent's
`REASSESSMENT-321589.md`, and `v12/DESIGN.md` VER-1 through VER-5.

**Scope, as the handoff states it:** prepare the smallest paired correction
packet — task `/3`, fresh result contracts, exact fixture provenance, bounds,
the focused positive/negative verification and the paired 102 gate. **No product
edits, no live model.** The final source binding waits for accepted W321528.
I own this child dossier and packet only.

## What is delivered

- **`CONTEXT-CONTRACTS.md`** — `/3` as `/2` plus one member, with `/2` frozen
  and its `source_profile`/`declared_base` meaning preserved; the
  `verification_context` document; the refusal table, every row refusing
  *before* materialization and provider work; and the fresh
  `baton.dogfood-context/1` and `baton.dogfood-proposal/3` result shapes.
- **`PACKET.md`** — the one concrete task (the 102 gate), its single declared
  immutable input with measured provenance, the deferred source-binding
  procedure, proposed bounds, and the deterministic-provider default.
- **`VERIFICATION.md`** — one row per VER-5 obligation, outcome-shaped rather
  than command-shaped, with an explicit separation of what this claim measured
  from what only delivery can establish.
- **`PINS-321780.json`** — digests of the governing records, DESIGN, the
  immutable input, and the packet's own artifacts.

## Three decisions worth reviewing

**`/3` is `/2` plus one member, not a redesign.** VER-1 says `/2` stays frozen
and that its name is occupied by the W71917 source-profile shape. The smallest
thing that satisfies the declared-context requirement is one new member on a new
version, with the two `/2` members keeping their exact meaning — and the refusal
that makes versioning real is that a `/3` context offered under `/2` is
**refused** rather than ignored.

**The results are versioned, not widened.** The current shapes cannot express
two outcome axes, and widening them is what VER-1 forbids. `baton.dogfood-context/1`
carries `ready`/`refused` with one closed cause; `baton.dogfood-proposal/3` adds
the command axis beside the unchanged `/2` members. The discipline that matters:
only `passed`/`failed` from a command started in a `ready` context supplies a
verdict, and `exit_status: null` is never a pass — W321528's review measured that
the current producer emits null for a skipped command, a timeout and a failed
start alike, so the closed `command` member is what a consumer compares.

**`import_roots: [src]` with `working_directory: v12/python` is the point.** The
September 102 run reached `PYTHONPATH=src` by a hand-set shell variable, and a
hand-set variable is not a contract. Deriving the path from the declaration at
both holders, closed, with no ambient inheritance, is what turns that run into
something two independent views can reproduce.

## NO SOURCE BASE IS BOUND, deliberately

W321528's candidate `2c89d3aa` is **unaccepted** and the handoff forbids binding
it as an accepted base. `PACKET.md` carries the procedure instead: accepted
W321528 delivery, Slawomir's commit, then that commit as `declared_base` with
these pins re-measured against it. Recording a base today would be exactly the
thing I was told not to do, and a pin taken today is a fact about today.

## Measured, and what it does not establish

    the 102-test credential gate, on the current tree, read-only
      ............................................... 102 PASS  0.222s
    vectors.json ... sha256:fcc19dbdf021246c... 19351 bytes

That establishes the vector and its one immutable input are **intact today**. It
establishes **nothing** about worker or operator materialization — which is the
entire acceptance obligation, and the finding this Work descends from. Every row
in `VERIFICATION.md` is a contract the packet binds, not a result; I have not
claimed any of them.

The reassessment's point is also worth restating because it bears on how this
packet should be judged: the September 102 was a *manually assembled* review
context, and W319114's different focused gate does not replace it. VER-5 agrees —
a different passing subset does not substitute.

## Not claimed

No product edit; no live model, engine or container; no deployment; no Git
operation of any kind; no whole-suite expansion. No edit to W321528's packet or
to `claude_agent.py` — that overlap is gated in W321776 and stays there. No live
run is selected and the packet names no provider question that would need one.

Cumulative verification this claim: about 0.25 seconds of measured deterministic
execution (the gate) plus the provenance digests. Nothing broader is implicated:
this claim changed no code.

A human Git checkpoint is not due for a preparation pass; whether to commit
these records is Slawomir's call and the packet does not depend on it.


## Claim 322256 (baton.claude, impl) — the three packet corrections

APPEND-ONLY. Read: `detail` at snapshot322255, `work-events` after 322179
(events 322204→322256), `thread` T321780, then
`review-2026-10-18T09-07-00Z.md`, the current PLAN and FINDING. All three
findings were correct and all three are documentation.

### 1 — one root per path field, and preflight has two stages

I declared `required_paths` repository-relative and then supplied
working-directory-relative values, and described `import_roots` both ways. Those
paths do not exist at a view root, so the example and the contract disagreed.
There is now a table: `working_directory`, `candidate_destination` and
`inputs[].destination` are **view-relative**; `import_roots` and
`required_paths` are **working-directory-relative**. The concrete layout and
argv match it.

The printed `verification` also carried a shell `PYTHONPATH=` prefix while the
contract derives imports from `import_roots` — a second, disagreeing source of
one fact. It is literal argv now, with no environment assignment.

**And the preflight claim was simply wrong.** I required every missing required
path to refuse *before materialization*, which cannot be done: a path inside a
view that does not exist yet is unobservable, and so is one the implementation
has not yet created or deleted. Split into **Stage A** (static: grammar,
overlap, duplicates, sealed-input availability and digest — before
materialization and provider work, nothing materialized) and **Stage B** (view:
`working_directory`, import roots, required paths, materialized digests, line
readback — before the command starts, owned view cleaned up, source and
candidate retained). That aligns VER-2 and VER-3 rather than changing them.

A consequence worth stating: **a candidate deletion is a Stage-B
`missing-input` refusal supplying no candidate verdict**, not a test failure.
A check that let it arrive as `failed` would report a context fault as evidence
about the code.

### 2 — the pair was half-specified

I defined the worker side and no operator side, while VER-1 requires fresh
proposal **and evidence** contracts. `baton.dogfood-operator-evidence/1` is
added, bound to the exact `task_id`, task digest, candidate base/head and sealed
input digests it observed — so it cannot be read as evidence about something
else.

The combinations are closed now, because "two axes" without constraints lets
contradictions through: five legal rows, and `passed` may not carry a null or
nonzero status, `failed` may not carry `0` or null, `refused` may never carry a
command verdict, and `not-run`/`timed-out` may never carry a status. Legacy `/2`
results are explicitly **not reinterpreted**: an absent `context`/`command`
means the version could not say — never `not-run`, never `passed`. And the
supported `source_profile` variants are stated rather than left implicit in
"every `/2` member": directory and line, with the line readback refusal.

### 3 — it described the workload, not a Job

A composable recipe is added, with `<BASE>` and `<RUN>` as **deferred
placeholders rather than blanks to guess**: source driver, the sealed input
resolved **by name from the seal** (neither holder reads the host checkout by
absolute path), the implementation instruction artifact, the existing
digest-bound image and supervisor, and the focused verification invocation.

**The distinction the review asked for, stated as a boundary:** the
**implementation agent** authors the paired correction — that is a real provider
turn, because writing code is writing code — and the deterministic **fake/replay
providers** verify runtime behaviour at their own boundary. A packet running only
replay providers would prove the plumbing and deliver no code; a packet claiming
a replay run produced the correction would be crediting a fixture with
authorship.

The upstream sequence is retained explicitly: W321688 plus human checkpoint
W322125, then W321528 acceptance, then Slawomir's commit as `<BASE>`, then
W321776. This packet stays disjoint and is corrected now; it binds no unaccepted
candidate.

### Pins and what is still not claimed

`PINS-321780.json` 99758a5a1230 — `CONTEXT-CONTRACTS.md` 295fe2078d33,
`PACKET.md` 50395e025ac0, `VERIFICATION.md` 89a297dfff96, with the fixture
digest and size and the DESIGN digest re-measured.

The 102-test result from the previous claim remains **author evidence of the
current tree**, not paired-context acceptance — the review says so and I am not
upgrading it. Every row in `VERIFICATION.md` is still a contract the packet
binds rather than a result. No product edit, no live model, no engine, no
deployment, no Git operation, no whole-suite expansion. No test was rerun this
claim because nothing executable changed: the corrections are to documents.

Cumulative verification this claim: none beyond the provenance digests, which is
the honest number for a documentation correction.


## Claim 322370 (baton.claude, impl) — source, base and view, bound to the real code

APPEND-ONLY. Read: `detail` at snapshot322369 (queued, unclaimed, routed
baton.impl, next baton.bug, blocking, binding revision 1 at this directory),
then the standalone claim; `work-events` after 322256 (322281 → 322370),
`next_after` null; `thread` T321780; then `review-2026-10-18T09-16-00Z.md` and
the **current** FINDING and PLAN, whose digests moved this round and are
re-measured in the pins. **Both findings were correct, and correcting them
required reading the product rather than reasoning about it.**

### 1 — I had invented the profiles, and then verified the wrong tree

`checkout.py:82` exposes **three** profiles — `generic`, `git`, `git-line` — and
I had written "exactly directory and git-line", inventing directory semantics
and dropping `git` entirely. The pairing is `checkout_plan`'s (`:206-265`): a
base is required for both version-control profiles and **refused** for the
generic one, because a generic profile carrying a base "would deliver the
generic boundary while its author believed a verification had happened". `/3`
now preserves all three, and both holders ask that package instead of restating
it — which is what `dogfood_operator.py:744-750` already does.

**The worse half was the base.** I required the verification view to check out
`declared_base` and read it back. The real worker says otherwise, in three
places I read this claim:

- `claude_agent.py:2452-2521` — `_entered` proves the line is clean and that
  `declared_base` is an **ancestor of** the entry head, never equal to it,
  because "an entry check that demanded `HEAD == base` would reject the second
  round";
- `:2011-2021` — for a line the candidate **is** the mounted worktree; nothing
  is copied;
- `:2077-2080` and `:2101` — verification runs over the **provider-modified**
  worktree, and the commit comes afterwards.

So my Stage-B readback would have run the gate against old code and called the
result a candidate verdict, and demanding that a finished candidate equal the
base would have rejected legitimate delivery. That row is **removed**.
`declared_base` is now an ancestry question against `entry_head`, and the three
facts — base, entry head, candidate — have a table of their own.

**`candidate_head` is gone from the operator evidence.** It cannot identify a
generic candidate, which has no commit at all, and it cannot identify a line's
*verified* state either, since verification precedes the commit and `_unmoved`
requires the head not to have moved. What a holder can honestly publish is what
it **measured**: `tree_digest` over its own no-follow walk, plus the bounded
`changed`/`removed` sets. That is one identity for all three profiles, and the
commit names stay as provenance where a profile has them.

### 2 — the layout could not have existed as drawn

A prepared-line candidate is the whole repository, so putting it at `v12/python`
and drawing `src/` beneath it would have produced
`view/v12/python/v12/python/src`. Putting the whole candidate at the view root
instead would have dropped the declared fixture **inside** the candidate, which
the packet itself forbids. The candidate now lands at `candidate/` and
`working_directory` at `candidate/v12/python`, declared rather than inferred.

**And the fixture genuinely cannot be moved out.** `input_roots.py:29-33`
resolves it as `parents[3] / ".."` from its own file, so with the working
directory inside the candidate it lands at
`candidate/work/records/.../vectors.json` — and only a product edit could change
that. A preparation packet that edited the product to suit its own layout would
have changed what the gate measures, so it does not. The honest resolution is
**two holders of one fact**: the sealed input's declared destination moves to
`sealed/...`, disjoint from the candidate as VER-2 requires, and the
in-candidate path becomes a `candidate.pins` entry at the **same digest**. A
drifted fixture makes the two disagree and Stage B refuses before the command
starts — which is strictly better than the old declaration, under which a
silently edited fixture would simply have passed.

### 3 — the recipe names interfaces now, and the instructions exist

"The governed source-driver preparation ART/TOK already uses" specified nothing,
and the reviewer said so. Every recipe row now names a real surface:
`source_boundary.SOURCE_TARGET`/`WORKSPACE_TARGET`/`declared_profile`/
`nominate_source`, `checkout.checkout_plan`, `workspaces.compose_input_root`,
`tools/accepted_base.py`, and the worker's own `_line_delta` measurement. **No
new copier and no scope expansion** — the candidate reaches a view by the
manager's materialization of the declared line and the seal's materialization of
the declared input, which are the two routes that exist.

`TASK-INSTRUCTIONS.md` is **written and pinned**, not promised at selection
time. `<BASE>`, `<ENTRY>`, `<TREE>` and `<RUN>` are the only deferred values; it
names the two holders to change, the two files the delivering turn must **not**
touch (`checkout.py`, `input_roots.py`), and five mistakes in advance.

### Pins, and what I did not claim

`PINS-321780.json` **943e89c6e4d3** — `CONTEXT-CONTRACTS.md` fbf65502884e,
`PACKET.md` 911066e02713, `VERIFICATION.md` 177fe53938da,
`TASK-INSTRUCTIONS.md` cc01d3e89b3f, plus a new `source_truth_read_this_claim`
block digesting the four product files I read and naming the lines each fact
came from, so a reviewer can check my reading rather than trust it.

**No test was rerun and the 102 gate was not re-measured**: this correction
changed documents only, which the review states needs no live or product
execution. The claim-322179 result stays **author evidence of the current tree**
and not paired-context acceptance. Every row in `VERIFICATION.md` remains a
contract the packet binds rather than a result.

No product edit, no live model, engine or container, no deployment, **no Git
operation of any kind**, no whole-suite expansion. No source base is bound —
W321528's `2c89d3aa` is still unaccepted. W321776 stays dependent on this packet
and on W321528; upstream W321688 and the separate human checkpoint W322125 are
unchanged.

Cumulative verification this claim: none beyond the provenance digests, which is
again the honest number for a documentation correction — against about 0.25
seconds of measured execution across the two prior claims.


## Claim 322472 (baton.claude, impl) — the order of events, finally right

APPEND-ONLY. Read: `detail` at snapshot322471, then the standalone claim;
`work-events` after 322370 (322428 → 322472), `next_after` null; `thread`
T321780; then `review-2026-10-18T09-38-00Z.md`, `REVIEW-PINS-322436.json`, and
the current FINDING and PLAN, re-measured in the pins. **All three findings were
correct. Two of them were things I had asserted about the product without
reading the lines that govern them.**

### 1 — I put facts in a sealed task that could not exist yet

`tree_digest`, `changed` and `removed` were members of `verification_context`,
which is a **required member of the input task**, and Stage A validated them
before any provider work. A useful authoring turn cannot know its own edits
before it runs. `compose_input_root:5779` onward and DESIGN ART-3 forbid
rewriting the pre-claim input binding after the claim to insert them, and
deferring `<TREE>` to selection did not fix that — it only moved an impossible
measurement later.

The two kinds of fact are separated now, and the separation is the contract: a
**sealed task holds constraints**, a **published result holds observations**.
The task's candidate member carries `profile`, `declared_base` and `pins` — and
`entry_head` left too, because the task author does not hold the head the
manager's writer grant admitted. The measured candidate is published after the
provider and before verification, and independent review binds to that retained
output rather than to a task nobody may rewrite.

`pins` survives the split because it is decidable at sealing: the path exists,
its digest is measured, Stage A checks the seal agrees. Nothing about a pin
depends on what the provider will do.

### THE WHOLE-TREE DIGEST IS GONE, and I should not have invented it

`_line_status:2759` records owner ruling 2026-09-21T12:47:17Z retiring the
whole-checkout rehash **by name**: "the superseded broad regime walked and
hashed the whole checkout to catch what an index trick can hide from status; the
ruling retires that guarantee by name, and what remains is honest: the delivered
changes are still proved byte-for-byte, and a path status cannot see is neither
measured nor delivered."

My `tree_digest` over the whole candidate, with "nothing is excluded silently",
reinstated exactly that retired guarantee — and claimed a scope `_line_delta`
does not have, since it is explicitly bounded and **discloses** its ignored and
special exclusions. What the packet binds now is what the adapter produces: the
bounded changed set proved byte-for-byte, the deletions as their own set, and
the exclusion disclosure carried forward so a reader is told what was not
measured. If a broader guarantee is ever needed for acceptance, that is an
**owner decision with a stated unmet requirement** — not something a preparation
packet may assert into existence, which is what I did.

### 2 — the launch was circular

`TASK-INSTRUCTIONS.md` called itself the `instructions` member of a
`baton.dogfood-task/3` document whose job was to make `/3` exist, while the
packet selected the existing image unchanged. Both holders check `/2` by closed
equality — `claude_agent.py:117`, `dogfood_operator.py:768` — so that launch
would have **refused at both ends before the implementation agent could type
anything**.

The roles are named and kept apart now: the launch task is `/2`,
`TASK-INSTRUCTIONS.md` is its `instructions` member, and
`CONTEXT-CONTRACTS.md` is **test data and the acceptance surface** for what the
turn produces. `/3` is first spoken by the code the correction creates.
`<BASE>`, `<RUN>` and the image digest stay deferred; **the schema the launch
speaks does not**, because deferring that is what made it circular.

### 3 — I credited existing helpers with work they do not do

Corrected against the code rather than the names:

- `compose_input_root` **writes and binds** `input.json`/`assignment.json`; it
  does not materialize this fixture into a verification view.
- `nominate_source` proves a source directory's identity and **reads no
  contents**.
- `_line_delta` measures a bounded, status-reported delta and supplies **no**
  whole-tree identity.

The byte transport that does exist, and that I had missed: `_publish_line`
retains the patch, the verification transcript, the result record, and
`BUNDLE = "objects.bundle"` for `base..HEAD` — declared in `CLAIM_NAMESPACE` as
`transport` beside `base` and `head`. **That carries objects a recipient can
resolve.** A digest list, which is what my previous draft offered, supplies
identities and not bytes.

And the honest remainder: `_publish_line` retains **no candidate tree,
deliberately**, so nothing today builds a second *worktree* from that transport.
Initialising the operator's view and resolving `head` out of the bundle is **new
bounded materializer work**, and `PACKET.md` row 8 says so instead of naming an
existing helper that would have been doing something else.

### The trace, and the edit nobody could have sealed

`PACKET.md` now carries one eight-stage trace — seal, materialize, line,
provider, measure, worker view, retain, operator view — with each stage's input,
producer, **available bytes** and immutable identity. The demonstration edit is
made at stage 4, is unknown when the inputs were sealed, and reaches both views
with the sealed input digest unchanged and the retained output bound.

### And I removed restrictions I had no standing to impose

The previous `TASK-INSTRUCTIONS.md` forbade touching `checkout.py` and
`input_roots.py` and said "nothing else is left to the implementing turn's
judgement". The AGENTS owner ruling of 2026-09-28 bounds implementation by
**outcome**, not by an exclusive file list, and a contract this size does not
land without helper and test changes. Both files are now named as
**coordination points with the reason** — `checkout.py` owns the profile rules
both holders should keep asking, and changing `input_roots.py` changes what the
gate measures, so it must be reported rather than adjusted quietly to fit the
view.

### Pins and what I did not claim

`PINS-321780.json` **f8ca4577cc5b** — `CONTEXT-CONTRACTS.md` 9cc59907e0e1,
`PACKET.md` 62a8ecf267bf, `VERIFICATION.md` 8763c1ffc375,
`TASK-INSTRUCTIONS.md` 396021779136. `source_truth_read_this_claim` now digests
five product files and names the exact lines each fact came from, including the
retirement ruling and the transport, so my reading can be checked rather than
trusted. New `launch_envelope` and `candidate_identity` blocks state the two
splits in one place.

**No test was rerun and the 102 gate was not re-measured** — documents only,
which the review states needs no product execution. The claim-322179 result
remains author evidence of the current tree. Every row in `VERIFICATION.md` is
still a contract the packet binds rather than a result.

No product edit, no live model, engine or container, no deployment, **no Git
operation of any kind**, no whole-suite expansion, no new approval gate. No
source base bound — W321528's `2c89d3aa` is still unaccepted. Preparation stays
disjoint; W321776 waits on this packet and W321528; upstream W321688 and the
separate human checkpoint W322125 are unchanged.

Cumulative verification this claim: none beyond the provenance digests — the
honest number again — against about 0.25 seconds of measured execution across
the three prior claims.


## Claim 322535 (baton.claude, impl) — I had reinstated the finding inside its own correction

APPEND-ONLY. Read: `detail` at snapshot322533, then the standalone claim;
`work-events` after 322472 (322519 → 322535), `next_after` null; `thread`
T321780, unchanged at M321780; then `review-2026-10-18T09-49-00Z.md`,
`REVIEW-PINS-322526.json`, and the current FINDING and PLAN, re-measured in the
pins. **Both findings are correct, and the first one is the worst thing I have
written in this packet.**

### THE WORKER VIEW WAS THE EDITED CANDIDATE, which is the defect this Work exists to fix

I wrote that the worker's view was "the worktree itself" and that "nothing is
transported, because the edits are already here", and I gave Stage B a matching
exception: the worker "needs no such comparison — it *is* where the edits were
made". Three documents agreed with each other and all three contradicted DESIGN
VER-3, which requires the worker **and** the independent operator each to
materialize a **fresh private verification view** and forbids verification from
modifying retained candidate bytes.

**The reassessment this Work descends from named direct-in-candidate
verification as the missing behaviour.** So I had reinstated the original
finding inside the correction meant to remove it — by renaming the edited
worktree a view, which supplies no isolation at all. Two consequences make that
concrete, and they are why an identity comparison is no substitute:

- a command that **writes or deletes a source file** alters the **retained
  candidate**, and a post-run digest notices only afterwards;
- a **timeout or start-failure cleanup** that removed this "view" would remove
  the **candidate**.

And the current code does verify in place: `_verify`'s own first line is "the
task's OWN command, in the candidate copy", and for a line profile the candidate
*is* `OUTPUT_ROOT`, the retained worktree. So the worker-side fresh view is
**new bounded materializer work**, named as new exactly as the operator's is,
with its obligations stated as outcomes: obtain the candidate's bytes with the
measured changes applied and the deletions absent **before** the command starts,
materialize each sealed input from the seal, own the view, delete only the view,
and leave the candidate and the seal byte-unchanged on success, test failure,
timeout, failed start and partial materialization alike. The exception is
removed from all three documents rather than softened.

### The transport is incremental, and I had not said where the base comes from

`claude_agent.py:3016-3018` creates `objects.bundle` for **`base..HEAD`**. That
range carries no base history, so a receiving repository without `base` cannot
resolve `head` from the bundle — and stage 8 described initialising the view and
resolving `head` without naming the prerequisite object source at all.

It is named now, and it is one place: the deployment's **own retained
repository** — the instance layout's `repository` root, whose `refs/heads/main`
only `tools/accepted_base.py` advances, as a receipted supported transition. The
view is seeded from there and the bundle is applied over it, with four refusals:
a missing `base` in the object source is `missing-input`; an unsatisfied bundle
prerequisite, a transport resolving some other head, and a result record that is
not the one whose head resolved are each `materialization`. **No fallback to an
ambient host checkout**, and a digest does not supply a missing object — an
operator that fell back to whatever repository happened to be on the host would
be verifying a candidate assembled from an unaudited source, which is the same
class of defect as verifying in the candidate.

### Pins and continuity

`PINS-321780.json` **49a2ebb7e3be** — `CONTEXT-CONTRACTS.md` 682171c7e749,
`PACKET.md` 677f9f666bfb, `VERIFICATION.md` 30ee6608265b,
`TASK-INSTRUCTIONS.md` 3a8bf68b1721. A new `paired_views` block states the
requirement, what the code does today, the two new materializers and the
operator's object prerequisites in one place;
`source_truth_read_this_claim` now digests **six** product files and names the
lines each fact came from, including `_verify`'s in-candidate docstring, the
`base..HEAD` bundle and `accepted_base.py`'s reference advance.

The accepted lifecycle corrections are preserved untouched: the
constraint/observation split, the `/2` launch envelope with `/3` as produced
test data, the bounded collection with no whole-tree audit, and the
outcome-bound scope.

**Upstream, observed through canonical state rather than assumed:** W321688 has
passed independent review and is with its owner; integration and the separate
human checkpoint W322125, and final W321528 acceptance and base selection, must
still be observed before any launch. None is observed as complete here, and no
base is bound.

**No test was rerun and the 102 gate was not re-measured** — documents only,
which the review states needs no product execution. The claim-322179 result
remains author evidence of the current tree. No product edit, no live model,
engine or container, no deployment, **no Git operation of any kind**, no
whole-suite expansion, no new approval gate. W321776 stays dependent on this
packet and W321528.

Cumulative verification this claim: none beyond the provenance digests, against
about 0.25 seconds of measured execution across the four prior claims.
