# Progress: the Python v12 assignment authority

Implementer-owned, created after the Baton claim on W2845.

## Cut 1 — package, identity, POD ownership, store compatibility (2026-08-24)

Delivered to the boundary in `evidence/python-authority-boundary-2026-08-24.txt`
and handed back for independent review. Evidence: `evidence/cut1-2026-08-24.txt`.

### Revalidated before writing anything

Python 3.13.7 and SQLite 3.46.1; the frozen Node authority's seven modules read
end to end; its seven test files present and untouched; the Node reference gate
at 684/687 with exactly the three W1593-owned failures the boundary names.

And the two build-artifact hashes **recomputed** from
`/usr/share/python-wheels` rather than copied from the boundary document. A
lock whose hashes came from a document rather than from the artifacts pins a
claim.

### The one place I did not port the Node host

Its `Store.open` creates when absent, adopts when present, and writes the schema
before establishing whose store it is. That was tolerable for a disposable
single-host authority and is not tolerable here: this distribution sits beside
three other SQLite files whose first schema version is also `1`, and a
create-or-adopt `open` against any of them writes tables into somebody else's
database — **and the failure mode is silent success**.

So `create` and `open` are separate non-adopting operations; `create` reserves
the path with `O_CREAT | O_EXCL` before SQLite is involved; `open` probes
read-only and checks **kind before version before UUID**, because "version 1" is
true of three other products and reporting the wrong VERSION when it is the
wrong PRODUCT sends someone to fix the wrong thing.

A refusal leaves the file as it was found — not "after we fixed the PRAGMAs".
The journal mode is the only persistent sqlite setting involved, so `open`
withholds it until the recheck under the write lock has passed.

### The snapshot correction, ported by obligation

Python's version of the Node getter hazard is `dict`/`list` subclasses,
`__getitem__` overrides, arbitrary mappings and objects with hooks. `own()` does
not defend against them; it makes them unreachable — `type(x) is T`, never
`isinstance`, so a subclass is refused rather than admitted with its overrides
intact. A `LyingDict` that answers one participant once and another afterwards
is refused for being a subclass, before either answer matters.

And a `Hostile` fixture that raises from eight different hooks is offered as the
operand, as a member, as an entry and nested; nothing runs in any position.

### Twenty mutations, and four zeros worth naming

Nineteen witnessed. One — the explicit empty-file check — is a **genuine
equivalence**: the read-only probe already refuses a zero-length file. Kept
because it changes the *reason*, and "the file is empty" is the accurate
diagnosis of an interrupted creation.

Three others measured zero and were **my instrument or my coverage**: a case
that refused before reaching the mutated line, a case that failed before the
reservation it was meant to exercise was even held, and a mutation that replaced
the first textual `sort_keys=True` — which was in a **comment** describing the
call rather than the call.

That last is the fourth instrument error I have recorded this week. Two more
turned up in the boundary tests: a schema word-scan that failed on
`integration_attempt` and on comment prose, and a source scan that failed on
this package's own docstrings, which say correctly that nothing here opens
`work.sqlite3`. **A checker that cannot tell a claim from a reach punishes
documentation.** Both were replaced with precise instruments.

### The trust claim is the narrow one

The tests prove the exported surface, the import graph, the absence of any
literal reaching for v11 or the Node host, and that the schema's table set is
exactly the authority's. They do **not** claim underscores are a sandbox: a
determined trusted in-process module can import a private module, and saying
otherwise would be a false guarantee dressed as a test.

### Verification

- `just gate` in `v12/python` — **53 tests, 53 pass, 0 fail**, Python 3.13.7.
- Zero temp roots retained; every fixture owns and cleans its own.
- `v12/src/authority` and all seven frozen authority test files **untouched**.
- The Node v12 gate is 684/687 — the same three W1593-owned failures that
  predate this Work and that it does not touch.
- Whitespace clean.

### State

**Awaiting independent review of cut 1.** Cuts 2-5 are not implemented, not
stubbed and not promised: `test_a_later_cut_adds_methods_rather_than_stubs`
asserts the runtime transitions are absent, because a stub raising
`NotImplementedError` is a method the exported surface claims to have. W4 stays
blocked on W2845.

## Cut 1 correction — 2026-08-24

`review-2026-08-24T04-41-03Z.md`: five P1 and one P2, all correct. Evidence:
`evidence/cut1-correction-2026-08-24.txt`.

**All six reproduced before any edit**, as one probe script run against the
delivered cut. The useful fact about my own work is that the 53-case gate passed
while all ten reproductions were true: **my cases proved the rules I had thought
of.**

### The five defects

1. `open` built the Store from the **probe's** UUID, so with the file replaced
   in the window the face named A while the connection governed B — an authority
   answering to two identities. The live identity governs now, and a
   probe/live disagreement **refuses** rather than resolving itself.
2. The recorded UUID was checked for **existence**, not validity, so a
   marker-only file recording `not-a-uuid` was a recognized authority and
   opening it grew the full 18-table schema inside it. It is held to the frozen
   grammar now, on the probe and the live recheck.
3. `COMMIT` was in a `finally`, so a fault partway through the schema committed
   what had already run — a failed open leaving tables in somebody else's
   database, the exact outcome the non-adopting design exists to prevent,
   reached through the **error** path.
4. `is_v12_contract` invoked the caller's `__ne__`, `gate_token` its
   `__format__` while assembling a **durable** value, and `same_assignment`
   short-circuited on `None` before validating anything. **I proved the rule at
   `own` and not at the doors people walk through** — the same "applied at one
   of N sites" shape I have been given all week, this time between an internal
   helper and its own exported surface.
5. `str()` of an integer is **not inert** in Python 3.13 above 4,300 digits, so
   the function whose entire job is to describe a rejected value safely was
   itself the escape. Wide integers are named by `bit_length()` now.

### The lock is consumed rather than described

`just build` resolves the lock **offline** with `--require-hashes` and
`--ignore-installed`, builds and installs with `--no-build-isolation`, imports
from **outside** the source tree asserting `site-packages`, and runs the whole
suite against the **installed** layout — so a packaging mistake cannot hide
behind `PYTHONPATH=src`. It **refuses rather than skips** when the wheelhouse is
absent, and it is part of `just gate`.

### A zero that was my case again

Ten mutations; nine witnessed, one equivalent given its neighbour. The
`same_assignment` mutation measured zero because my first draft only inspected
the outcome **when something was raised**, so a helper that *accepted* the
hostile operand passed — which is exactly how the defect slipped through. That
is the same weakness a reviewer found in a sweep case of mine two days ago,
repeated in a case written for the very defect it then tolerated. Every row must
refuse now.

### Verification

- `just gate` — version, **60 tests**, and the locked build: all pass on
  Python 3.13.7.
- Every original reproduction now refuses, with nothing run and no file
  modified.
- Zero temp roots; the frozen Node reference untouched; whitespace clean.

### State

**Awaiting cut-1 re-review.** Cuts 2-5 remain absent, and the case asserting the
runtime transitions do not exist still holds. W4 stays blocked.

## Cut 2 — claim, the one ending, fences, gates, projections (2026-08-24)

Cut 1 signed off in `review-2026-08-24T04-51-24Z.md`. Cut 2 delivered and handed
back. Evidence: `evidence/cut2-2026-08-24.txt`.

### The operand I did not add

Every transition in the frozen host takes an `operation_id` and is wrapped in
the journal's `replay`. The journal is cut 3, so I left the operand out.
Accepting it here and doing nothing with it would be **a claim with no mechanism
behind it** — an exact retry would re-perform the act while the caller believed
it was effectively-once. That is the same finding the cut-1 review gave me about
`requirements.lock`, and the frozen host states the rule itself: a caller who
supplies an operand and has it ignored believes it chose something. Cut 3 will
therefore change these signatures, which is said here rather than discovered
there.

### Three gaps I found by probing my own cut

The cut-1 review's most useful sentence was that my gate passing proves the
rules I thought of. So I probed cut 2 the way a reviewer would. All 36 new cases
passed first time **and** the probe found three things:

- `install_gate` with a **stale** `expect` on an **unclaimed** Work was
  *accepted* — the frozen host takes the unclaimed branch first and never looks
  at `expect`, so a caller believed it had done a compare-and-swap and hadn't.
  A supplied `expect` is always compared now. A deliberate divergence from the
  frozen host, on the frozen host's own rule about ignored operands.
- **A clock answering `banana` wrote `banana` into a durable `created_at`.**
  `_now` checked for nonempty *text*; "validated UTC text" has to mean the shape
  or it means nothing. The frozen `timestamp` grammar is enforced now.
- A clock that *raises* leaks, and that is left as it is deliberately: the clock
  is a trusted bootstrap collaborator, and an act whose failure we cannot
  describe is not one we may record an outcome for. What is asserted is that the
  fault takes nothing with it. Reported as a decision, not fixed quietly.

### Twenty-four mutations, four zeros, one survivor

Two zeros were guards whose only contribution was a **better message** — "this
Work has a live assignment; name it" versus "an assignment identity is a
document". A specific refusal no case distinguishes from the generic one can be
deleted without anything noticing, so the cases assert the message and both
mutations now fail.

One zero was **my mutation being nonsense** — it added a dict key rather than
caching anything. Written as a real cache it fails ten cases. Fifth instrument
error this week; caught only because a zero on a freshness property looked
wrong.

One is a genuine equivalence **today**: the phase/gate check inside the ending
helper, which every current caller already satisfies one frame up and which
becomes load-bearing when cut 4 adds `close` and `advance_contract`. Kept for
the ordering property, not counted.

### Verification

- `just gate` — version, **99 tests**, and the locked build: all pass on
  Python 3.13.7; the suite also passes from the **installed** layout.
- Zero temp roots; frozen Node reference untouched; whitespace clean.

### State

**Awaiting cut-2 review.** Cuts 3-5 remain absent; the case asserting the
runtime transitions are not on the bootstrap face still holds. W4 stays blocked.

## Cut 2 correction — 2026-08-24

`review-2026-08-24T05-12-08Z.md`: five P1 and two P2, all correct, all
reproduced first. Evidence: `evidence/cut2-correction-2026-08-24.txt`.

**Fifteen reproductions were true while 99 cases passed.** I probed this cut
before handing it over and found three things; the reviewer found seven more.
The lesson is not that probing is useless — it is that probing my own design
finds the gaps I can imagine, and that is a smaller set than the gaps that
exist.

### The five P1s

1. **A compare-and-swap that compared one object and mutated another.** An
   assignment for Y satisfied `_expect` *correctly* — it was Y's live
   assignment — and then X was gated; on the live path Y was **ended** and X
   untouched. I had treated `_expect` as "is this identity current"; the
   question here is "is this identity current **for this Work**", and the second
   is not implied by the first.
2. **The generation space is finite and I minted past its end.** I bounded
   integers in `own` and `check_generation` in cut 1 and then minted one without
   going through either — the bound was on what a caller may send, and the
   authority is also a *producer*. Running out is an ordinary refusal now.
3. **One text rule, not two.** `_text` required exact nonempty `str`; `own`
   also required *encodable*. The scalars had the weaker rule sitting beside the
   stronger one, so a lone surrogate reached SQLite from a route, prose, a plan
   digest, and out of `gate_token`. A rule that exists twice holds in one of the
   two places.
4. **A gate is discharged by proof, not by truthiness.** A list stood for an
   exact runtime identity and satisfied a plan-revision gate. Each kind names
   its shape now, and the proof is **bound to the configured fact** —
   contract-runtime evidence must name the certified profile.
5. **The history is the whole life, in whole identities.** Claim wrote no event,
   so the journal said who *lost* the Work and never who took it; and events
   answered in separate columns, which is three quarters of an identity in the
   one place a reader reconstructs history from. The case that pinned the
   reference's omission was updated, as the review directs.

### The one representation decision, raised rather than assumed

`isolation_certified` as a boolean made "pinned" mean "somebody once said yes",
and the evidence then only had to be truthy — neither side named anything. The
policy now holds the **clause identity** and the evidence must name that clause.
I took the strict reading because it is the safe direction and because "pinned
clause" reads as an identity in the frozen prose, but it is a choice and the
review invited it to be raised. Raised.

### Fourteen mutations, one zero

The zero was the same shape as two zeros last round: the refusal still happened,
from the next check, with a *different message*. "No clause is pinned" points at
the configuration; "this evidence names a clause the deployment has not pinned"
points at the evidence — different problems with different owners. Two rounds
running, the answer to "this guard has no witness" has been **assert what it
actually tells the caller**.

### Verification

- `just gate` — version, **107 tests**, and the locked build: all pass on
  Python 3.13.7; the suite also passes from the installed layout.
- Every reproduction now refuses, and every previously-accepted row moved
  nothing.
- All 99 prior cases preserved (two updated per the review); zero temp roots;
  frozen Node reference untouched; whitespace clean.

### State

**Awaiting cut-2 re-review.** Cuts 3-5 absent; W4 stays blocked.

## Cut 3 — the operation journal, settlement, restart, real races (2026-08-24)

Cut 2 signed off in `review-2026-08-24T05-21-50Z.md`. Cut 3 delivered and handed
back. Evidence: `evidence/cut3-2026-08-24.txt`.

### The operand cut 2 promised, with the mechanism that gives it meaning

Every mutating transition now requires an `operation_id` and runs through
`Store.replay`. Seven signatures changed, exactly as cut 2's hand-back said they
would.

### The two kinds of refusal, proved where they live

No cut-3 *transition* raises a durable refusal — the stale-target integration
that does is cut 4 — so the savepoint mechanism is exercised directly through
`Store.replay`: an ordinary refusal writes nothing and stays retryable, a
durable one keeps its writes and is **replayed** on retry, and a non-`Refusal`
fault journals nothing at all. Proving it now rather than waiting means cut 4
doesn't arrive on an untested savepoint.

### My first barrier was a head start, not a barrier

The parent wrote the start file after spawning, so the children merely began at
different times and the "race" was a sequence with extra steps. Each child now
announces that it is loaded and connected, and the parent releases them only
once it has seen **every** one.

Three races: competing claims (one winner, and the assertion is on **why** each
loser lost — a claim reason, never "locked"); one fixed operation id across
three processes (**all three succeed**, because same operands and same id means
the later arrivals replay rather than lose a race they weren't in); and a claim
against a settlement, where **both orders are correct** and the case asserts
each on its own terms. Run repeatedly, both orders occur — 4 committed and 2
retired over six runs — so it is exercising a real race rather than a fixed
outcome.

### Two gaps I found by probing, and one I raised instead

- **A 1 MB operation id became a durable primary key.** An operation id *is* an
  opaque identity and the frozen contract already has a grammar for those, so
  the rule is **reused** rather than invented — stated in one place so a second
  boundary can't reach a different conclusion about the same string.
- A lying clock now stops a transition **before** the journal is touched, so no
  operation row is stamped with nonsense and the id stays usable.
- **Measured, not fixed, and raised:** the settlement `signature` is
  caller-supplied durable text with no bound (a 1 MB signature is written on
  retirement). I did not invent a limit, because the authority *produces*
  signatures whose length follows the operands and a short bound would make a
  legitimate settlement impossible. Cut 3's only callers are trusted; the
  natural moment is cut 5.

### Seventeen mutations, no zeros

The first cut where every mutation had a witness on the first pass. Two of them
are the same line mutated in **opposite directions** and each fails different
cases — a guard that only mattered one way would have shown up as a zero.

### Verification

- `just gate` — version, **135 tests**, and the locked build: all pass on
  Python 3.13.7; the suite also passes from the installed layout.
- Zero temp roots; frozen Node reference untouched; whitespace clean.

### State

**Awaiting cut-3 review.** Cuts 4 and 5 absent; W4 stays blocked.

## Cut 3 correction — 2026-08-24

`review-2026-08-24T05-38-39Z.md`: one P1 and one P2, both correct. Evidence:
`evidence/cut3-correction-2026-08-24.txt`.

### I stated the rule in one place and called it from one site

Cut 3's own evidence says I put the opaque-id rule in one place "so a second
boundary cannot reach a different conclusion about the same string". I put the
**rule** in one place and called it from `Store.replay` and nowhere else.
Settlement and both journal reads kept the weaker text check.

The review found the worse half: **settlement could record an invalid identity as
retired**, and a claim under the same id then refused on *shape* before ever
reading the retirement — two authority paths disagreeing about whether a durable
identity existed, with the bound retirement reason never replayed. That is not a
size problem; it is two answers to one question.

`check_opaque_id` serves all four paths now. This is the third time this week I
have made that mistake in a different shape:
documented-but-unimplemented, implemented-at-one-of-two-sites, and now
stated-once-called-once.

### The race children were reading the source tree under the installed gate

Both child scripts began by prepending the repository `src`, so under the
installed gate the parent used the wheel and every child ran source code — the
five subprocess race cases proved something about `src/` while the gate claimed
to exercise the installed layout.

The children are told the store path and **nothing** about imports now; they
inherit the gate's own environment and each *reports* where it imported from,
and the parent asserts the origins agree. **Measured:** restoring the child's
path insertion makes `just build` fail with four failures, so the guard detects
exactly the skew that was there.

### A mutation harness that lied to me

Its first run reported three mutations as zero. Direct runs show 6, 6, and — for
settlement's own check — that it is **equivalent alone and load-bearing in
combination**: `settle_operation` calls `operation_result` before deciding, so
its own check is shadowed by its neighbour's; weakening both fails thirteen
subtests. I could not reconstruct why the harness disagreed, so I re-measured
every one by hand and report the hand numbers.

**A false zero is more dangerous than a false failure:** a false failure gets
investigated, and a false zero gets written into an evidence file as
"equivalent". Sixth instrument error this week and the first in the
false-negative direction.

### Verification

- `just gate` — version, **136 tests**, locked build: all pass on Python 3.13.7,
  with the race children now *proven* to import the wheel rather than asserted
  to.
- The one-path case was **replaced** by a four-path table, because a case
  covering one of four paths is what let this through.
- Zero temp roots; frozen Node reference untouched; whitespace clean.

### State

**Awaiting cut-3 re-review.** Cuts 4-5 absent; W4 stays blocked.

## Cut 4 — progression, the candidate, the four receipts, close (2026-08-24)

Cut 3 signed off in `review-2026-08-24T05-47-26Z.md`. Cut 4 delivered and handed
back. Evidence: `evidence/cut4-2026-08-24.txt`.

### The corrections I ported with the code

The frozen host's one undifferentiated digest (a candidate that could not say
what it was built *from*); actorless receipts (one consumer could publish,
self-verify, self-review, self-approve, integrate into the canonical target and
close the Work); the optional policy generation outside the signature (one
identity taking two different durable meanings); the blanket durable flag (every
integration refusal permanently closed, including ones that wrote nothing); and a
close with no actor at all — **holding the assignment is not authority to
terminalize the Work**, and a case says so.

And one lesson carried forward rather than waiting to be told again: a supplied
`expect` on `close` must name the Work being closed. That was cut 2's P1 on
`install_gate`.

### `activity` belonged to neither cut's list

Neither cut 2's nor cut 4's scope mentions it. An assignment-owned durable act
with a caller-supplied idempotency key belongs with the assignment-owned
transitions, so it is here and **named** rather than left between cuts.

### The gap I found by probing

A `receipt_id` reused — across kinds on one proposal, or across two proposals —
hit the table's uniqueness and left as `IntegrityError`: a **fault**, which takes
the transaction down and journals nothing, so the caller got an unexplained
crash instead of "that identity is taken". `publish` already had exactly this
rule for proposal identities; the receipts did not. Same omission, neighbouring
transition — the shape I have now been shown four times, so I looked for it
deliberately and it was there.

### Twenty-six mutations, three zeros, three different answers

- **Two were missing coverage,** and missing for the same reason: the approval
  check is *shadowed* by the review check that fires before it, so three cases
  mentioned "integration requires explicit approval" and none ever reached that
  line. One case — verification passed, review accepted, nothing else —
  witnesses both, and also pins that this refusal is ordinary and that a
  *denied* approval is not an approval.
- **One was genuine redundancy, and I removed it** rather than reporting it: a
  separate "is it missing" check in front of `check_text` changed neither the
  verdict nor the message. Collapsed to one mechanism; mutating *that* fails
  sixteen cases.

**"No witness" has three distinct answers — missing case, redundant code, real
equivalence — and in the last two rounds I reached for the third one first.**

### Verification

- `just gate` — version, **169 tests**, locked build: all pass on Python 3.13.7,
  and 169/169 from the wheel with the race children still proving their origin.
- Zero temp roots; frozen Node reference untouched; whitespace clean.

### State

**Awaiting cut-4 review.** Cut 5 absent — the session face, and the natural
moment for cut 3's raised settlement-signature question. W4 stays blocked.

## Cut 4 correction — 2026-08-24

`review-2026-08-24T06-03-28Z.md`: three P1, all correct. Six reproductions, all
true while 169 cases passed. Evidence: `evidence/cut4-correction-2026-08-24.txt`.

### A frozen result identity named two different things

`result_id` had only the text rule, so an identifier with a space was accepted
and — the part that matters — the same identity could be published twice with
**contradictory digests**. It is an opaque id now, checked before the signature
and the journal, and the binding is stable: an existing `result_id` must name the
same digest and the same full assignment. **Consistent reuse stays permitted** —
one frozen result may back several proposals — so the rule is about contradiction
rather than about reuse.

### Generic storage plus a specific meaning

`policy` is deliberately generic and `own` is what makes any document safe to
*store*. `canonical_target` then handed whatever it found into a durable column:
a dict reached parameter binding as a raw `ProgrammingError`, and an empty string
was worse — it published successfully, so the proposal was bound to **no target
at all**. The semantic accessor is the only place that knows the meaning, so
that is where the type is asserted, and it now covers both side effects —
publication and integration.

### I corrected one projection and then wrote four more the old way

Cut 2 corrected `assignment_events` to answer with a nested `assignment_ref`.
Cut 4 then added activity answers, contract events, proposal reads and a publish
result — four new projections, all in bare columns, the publish result with no
assignment at all.

The reason is instructive: I ported each projection from the *frozen host's*
shape rather than from the corrected shape beside it. **The correction was in the
file I was editing.** There is one projector now, and `assignment_events` was
rewritten to use it rather than keep its own copy.

### Seven mutations, no zeros

S6 — the shared projector answering in bare columns — fails **twelve** cases.
One line, five projections, twelve witnesses: that is the argument for having one
instead of five.

### Verification

- `just gate` — version, **174 tests**, locked build: all pass on Python 3.13.7,
  174/174 from the wheel with the race children still proving their origin.
- Every reproduction now refuses or answers with the whole identity.
- Two existing cases updated rather than pinned; zero temp roots; frozen Node
  reference untouched; whitespace clean.

### State

**Awaiting cut-4 re-review.** Cut 5 absent; W4 stays blocked.

## Cut 5 — 2026-08-24 — the participant-bound session face (the last cut)

Plan item 6. The exact exported bootstrap, the participant-bound session, the
portable catalog comparison, and cut 3's raised settlement-signature question.

### The two faces, and the reason there are two

`Authority` configures, reads and MINTS. `Session` acts, for exactly one
participant, and holds no path, no store and no handle back. The frozen Node host
carried both on one object: a consumer claimed as `publisher`, granted
`publisher` the close capability, closed the live Work as that actor and moved
the canonical target with zero receipts. A capability nobody can take away from
you is not a capability.

So the claimant and every receipt actor come from the BINDING, and supplying
`actor` or `participant` is refused rather than dropped. **An operand that looks
authoritative and is not is worse than no operand.**

I also wrote the LIMIT of the claim into the module rather than implying it:
private attributes are not a sandbox, a trusted in-process module can import
`core` directly, and what is enforced here is the supported exported surface and
the deployment wiring. Untrusted workers are isolated by process and container,
which is a mechanism that enforces something.

### The surface is written out

16 transitions, 16 reads, in tables that name each transition's whole key set.
Deriving them from `Core` would mean adding a method there silently widened the
runtime boundary. Operands are taken ONCE as an owned copy — the frozen host read
`operands.expect.participant` for its binding check and handed the same object to
the core, so a getter answering one participant twice and another afterwards
passed the check and then ended somebody else's assignment.

`Authority.close` became `dispose`. One name meaning both "release the file
handle" and "end this Work with an outcome" is an API that invites the wrong one.

### The catalog is compared, and what it cannot prove is written down

`test_catalog.py` asserts the frozen reference is present, RE-MEASURES its size
rather than quoting it, maps every frozen file to a counterpart, and refuses to
let an obligation area vanish. It asserts no name-for-name equality, because the
port is by obligation and equality would force a bad transliteration — and the
file says so, so a green run is not overread. **A word in a test name is not
evidence of a guard.** Two areas failed first time and both were my needle.

### The settlement signature, measured instead of argued

100,000-character legitimate key → 100,185-character authority-produced signature
→ settles correctly. A cap below that refuses the settlement of an operation this
authority committed, which is worse than the unbounded operand. Ruling unchanged,
now pinned by a case.

### Thirteen mutations, and two zeros that were my instrument

T8 and T9 both measured zero. T8's mutation used a key no case supplies and one
that would be refused as unknown anyway — rewritten, it fails 14 cases. U5
weakened a threshold BELOW the actual value, which can never fail — rewritten to
break the counting, it fails.

T9 is genuinely equivalent and stays: the session's `own` is unobservable
*because* the exact-type rules hold, since a container that changes between the
two reads needs an overridden `__getitem__` and that is a subclass. Reported as
defence in depth, not counted as coverage.

### Verification

- `just gate` — version, **200 tests**, locked build: all pass on Python 3.13.7,
  200/200 from the wheel imported out of site-packages, race children still
  proving their package origin.
- 20 exported names; zero temp roots; frozen Node authority untouched;
  whitespace clean; still no runtime dependencies.
- Gap probe clean, and reported as clean.

### State

**Awaiting final independent review.** All five implementation cuts are present;
nothing is absent on purpose any more. Carried forward for a ruling rather than
silently: the durable-text bound the signature measurement implies, and the
`slot_holder` read that answers about another participant. Plan item 7 — the
satisfying close that unblocks W4 — is the reviewer's after sign-off.

## Cut 5 correction — 2026-08-24

Review `review-2026-08-24T06-36-30Z.md`: one P1, one P2. Both real, both
reproduced to the character before any edit, both closed. No cut 1-4 code
changed.

### The P1 is the shape I keep being shown

`errors.py` states the rule two files away — caller-controlled text in a refusal
is bounded by the RULE and never by the operand — and **cut 5's own evidence
asserted the bound held in the session**, while two sites in the file I was
writing interpolated caller text directly. A one-million-character participant
produced a 1,000,057-character refusal; the same string as an operand name
produced 1,000,089.

I checked the helper I was calling instead of the message I was writing. That is
cut 4's projection defect one cut later, and it is now four times in this Work
that the correction was already in the file.

Every rendering goes through `name_of`, including the session's *own*
participant — a grammar with no length is not a short string. Unknown names
become a bounded sample plus a count, because the multi-name half is the worse
half and the single-key probe does not show it: **510 names of 100,000
characters each was a ~51,000,000-character refusal.** The count is what makes
the sample honest.

A third site — `__repr__` — I found by sweeping the module rather than by being
told.

### The P2 was my own rule, broken by my own default

`given=None` made an omitted document and an explicitly supplied `None` the same
empty dict, **in the one place whose stated purpose is to refuse an operand
supplied and then ignored**, and a second document left as a raw `TypeError`.
`*documents` now, with all three answering the one-document rule. The case
calling explicit `None` "a legitimate operand document for nothing" is updated as
authorized — that sentence was the defect written down as a rule.

### Raised rather than silently fixed

An AST sweep of every `Refusal` interpolation in the package found the same
defect at cut 1-4 sites — **1,000,030** and **1,000,118** characters, measured.
Those files are signed off and the boundary says correct cut 5 only, so they are
reported for a ruling with reproductions attached. The root cause is one thing:
durable text has no system-wide bound. Same question as the settlement signature
and as W1593.

### A new instrument shape, recorded

The harness first reported one mutation as **eight** failing; by hand it is
**one**. It had a stripped environment, so the real-process race children failed
intermittently and added phantom failures. Cut 3 recorded that a false zero is
dangerous because it gets written down as "equivalent"; a **false non-zero** is
dangerous the other way, because it gets written down as "witnessed" and the
guard is never checked. Every one of the ten numbers was re-measured with the
gate's own environment and with failing case NAMES captured, so each is
attributable rather than counted.

### Verification

- `XDG_RUNTIME_DIR=/tmp just gate` — version, **205 tests**, locked build: all
  pass on Python 3.13.7, 205/205 from the wheel imported out of site-packages.
- Ten mutations, no zeros, every number attributed to named cases.
- 20 exported names; zero temp roots; frozen Node authority untouched;
  whitespace clean; cut 1-4 source unchanged.

### State

**Awaiting final re-review.** The two resolved questions are taken as ruled and
recorded here so the next reader finds the ruling rather than the question: the
cross-participant `slot_holder` read stays, and there is no settlement-only
signature cap. Open for a ruling: the cut 1-4 rendering sites in section 4 of the
correction evidence.

## Authority-wide diagnostic audit — 2026-08-24

Review `review-2026-08-24T06-51-18Z.md` ruled the correction in-Work, overruling
my decision to raise-and-not-touch. **The reviewer was right and my boundary was
wrong:** earlier cut sign-off is not an exemption from a still-live package
invariant when later evidence exposes a contradiction. Sign-off says nobody had
found a defect.

### The audit, done by walking rather than by reading

116 `Refusal` interpolations across five modules, enumerated with an AST walk —
because *reading* for them is how this survived two reviews. 26 corrected: 13 in
`core.py`, 12 in `store.py`, 1 in `identity.py`, covering the Work identity,
participant, assignment, contract, gate-token, frozen-result, receipt and
store-path families, including the path rendered inside a **label** handed to
another checker.

### The mechanism had the defect it exists to prevent

`name_of` bounded a rejected string and then rendered a rejected value's **type
name** raw, so a class named with 200,000 characters produced a
200,000-character diagnostic *from the helper whose entire job is safe
description*. Same shape as the earlier integer finding. **Twice now the
bounding helper has been the unbounded path.** The sixty-character rule lives in
one place now.

### The real fix is that the rule is checked

Two reviews found the same defect at different sites, and cut 5's evidence
asserted the bound held while the file being written broke it. **A rule nothing
checks is a rule that holds wherever somebody happened to look.** So the AST
check is now part of the gate, with its own vacuous-pass modes refused — one of
which fired during development on an allow-list entry I had added for a site the
walker cannot see.

Its blind spot is named and **measured**: helpers that build text for a refusal
are invisible to it, so injecting a rejected value into `opaque_id_fault`'s prose
is caught by the family suite and not by the walker. That is the argument for
having both.

### The instrument, twice

Four mutations started as zeros and **all four were missing cases**, each already
flagged by the AST check — the source check found the sites and the zeros told me
which had no behaviour behind them. And requiring a phrase per family exposed
**three families measuring the wrong rule**: one intercepted by the session
binding check, one refused by the UUID grammar, one hitting the empty-file rule
because `sqlite3.connect` writes no bytes.

A second instrument shape: one mutation first measured 8 and by hand was 1. The
cause was not the stripped environment I blamed last round — Python caches
bytecode by (mtime, size), so a mutation restored within the same second can be
measured against the previous file. Everything was re-measured with
`PYTHONDONTWRITEBYTECODE=1` and `__pycache__` cleared. Three shapes now recorded
across this Work — false zero, false non-zero, stale bytecode — one remedy:
attribute the number to named cases.

### Verification

- `XDG_RUNTIME_DIR=/tmp just gate` — version, **213 tests**, locked build: all
  pass on Python 3.13.7, 213/213 from the installed wheel.
- Twenty mutations, all witnessed, every number attributed.
- 20 exported names unchanged; zero temp roots; frozen Node authority untouched;
  whitespace clean; both reviewer regressions green.

### What did not change, deliberately

No durable-text operand cap. No accepted operand shortened or rejected for
length. The settlement ruling stands and its case passes unchanged: the authority
still accepts and exactly compares the 100,185-character signature it can itself
produce. Only the **rendering of a rejected value** is bounded.

### State

**Awaiting final re-review.** Nothing is open from my side.

## Label and classifier correction — 2026-08-24

Review `review-2026-08-24T07-10-44Z.md`: one P1, one P2. Both real, both
reproduced to the character first.

### The check I wrote is why the defect survived

The audit classified an interpolation by **unparsing it and matching a string
prefix**. So it read `name_of(value) + value` as bounded because the text began
with `name_of`, accepted any `join` of anything, and accepted `what` **because of
how the variable was spelled**.

`what` is package prose at every internal call site and caller text at every
exported one. One entry written for the internal sites silently covered the ten
exported helpers, and a million-character label produced refusals of 1,000,014 to
1,000,139 characters.

I wrote last round that a rule nothing checks holds wherever somebody happened to
look. **A check that matches spelling instead of origin is another place for
somebody to have looked once.**

### The label, bound once — and the bound measured

`label_of` at the entry of every function that accepts a label: ten in
`identity`, one in `store`, four in `core`. A label isn't quoted like a rejected
value — it's prose — but the length rule is the same rule.

Binding it at the **sixty-character value limit truncated this package's own
longest label mid-word** and took the member name with it, so twelve publication
cases stopped saying which digest was missing. The settlement-signature lesson in
a second place: a bound below what the authority legitimately produces breaks the
authority, not the caller. The limit is 160 and a case measures the longest label
plus one rendered member.

### The hostile label, found by a zero

A non-text label was returned raw and interpolated — and `f"{what}"` calls
`__str__`. A caller supplying a hostile label could replace a refusal the
boundary had already decided on with an exception of its own choosing: **the
exact rule `name_of` exists to enforce, in the one place nobody had checked it.**
I would not have looked if the mutation had not measured zero.

### The classifier now proves shapes and origins

One whole bounding call; a join only when its source is package-owned; constants
proved **by fixpoint** across the package so `frozenset({NAMES})` is owned on the
second pass; locals proved by assignment along the **scope chain**; and a
named-site table keyed by module, function and expression whose non-travel is
enforced with fabricated findings rather than described. It also attributed each
closure's refusals twice — it descends with a scope stack now.

116 interpolations, 22 unproven, 11 named. **The old classifier reported zero
unproven, which is what a prefix match looks like when it agrees with you.**

### Verification

- `XDG_RUNTIME_DIR=/tmp just gate` — version, **221 tests**, locked build: all
  pass on Python 3.13.7, 221/221 from the installed wheel.
- Twelve mutations, all witnessed; two began as zeros — one my own ill-formed
  mutation, one the missing hostile-label case.
- 20 exported names unchanged; zero temp roots; frozen Node authority untouched;
  whitespace clean; both reviewer methods green.

### State

**Awaiting final re-review.** No durable-text operand cap; the settlement case
passes as written. Nothing is open from my side.

## Label encoding and origin proof — 2026-08-24

Review `review-2026-08-24T07-25-10Z.md`: one P1, one P2. Both real, both
reproduced first — including all four analyzer false positives, each of which the
audit reported clean.

### An exact string is inert but it is not text

`label_of` proved the label was an exact `str` — which makes it safe to *read* —
and returned it. A lone surrogate then turned an ordinary refusal into a
`UnicodeEncodeError` at whatever logged it. **That is the same failure `name_of`
uses `ascii` to prevent for a rejected value**, and I did not carry it across when
I wrote the parallel boundary for a rejected label.

And "ordinary prose is returned as written" is now a case: rendering every label
through `ascii` bounds and encodes just as well and **nothing in the suite
noticed**, so preserving prose was an intention rather than a property. Found by
a mutation with no witness.

### The origin proof was still spelling, four ways

Package-global constant names; locals collected across nested scopes; a name
proved by *any* safe assignment regardless of a later or branching raw one; and
exceptions keyed by a short function name that many nested `body` closures share.

Constants are per module now, with shadowing decided by **counting bindings**
rather than inspecting one of them. Locals stay in their own scope and are proved
only when every binding is a top-level bounding call that dominates the use — a
loop target, a `with` target, a walrus or a `global` makes the name unproven,
because this analyzer does not model data flow and must not pretend to. Each site
carries its **dotted lexical path**, and an exception covers the number of sites
it declares: a spelling has no count, which is how one entry excused ten exported
helpers.

Seven more shapes it could have guessed at are fabricated and refused as cases.

### Verification

- `XDG_RUNTIME_DIR=/tmp just gate` — version, **227 tests**, locked build: all
  pass on Python 3.13.7, 227/227 from the installed wheel.
- Ten mutations, nine witnessed; one zero was a missing case, and one is a
  **measured equivalence** reported as such — the scope restriction is redundant
  given the binding rule, and both stay because either alone is unsound if the
  other is relaxed.
- All three reviewer methods green; 20 exported names; zero temp roots; frozen
  Node authority untouched; whitespace clean.

### State

**Awaiting final re-review.** No durable-text operand cap; the settlement case
passes as written. Nothing is open from my side.

