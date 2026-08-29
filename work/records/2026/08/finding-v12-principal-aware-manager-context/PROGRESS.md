# Implementer progress — principal-aware manager context

Created 2026-08-26 by `baton.claude` on claiming W16823, as the record
requires.

## Not started, and the ledger now says why

The assignment thread names the edge exactly:

> Intended scheduler dependency is W16823 blocked by W16821; approver action is
> pending under W16793 obligation 16832. The manager correction consumes the
> reviewed authority projection and must not guess it in parallel.

**It did not exist.** `open_blockers` was 0 and `blocked_by` was empty, so
`wait` reported this Work ready and unclaimed. Installed:

    block work=W16823 on=W16821    -> seq 16957

W16821 is itself blocked on W5 by the edge installed at seq 16950, so the
ledger now carries the whole stated order — W5 → W16821 → W16823 — rather than
leaving it as prose in two threads.

## Why the order is not cosmetic here

The brief says this correction **consumes** the reviewed authority projection
and must not guess it in parallel. That is the same failure mode W6634 refused
earlier in this campaign, when both contracts it was told to consume did not yet
exist: writing them would have been inventing another Work's contract, after
which the owning Work either adopts the guess or forces a rewrite with tests
already encoding it.

W16821 has not been implemented — it is blocked on W5 — so the principal,
effective scope and grant provenance this Work is supposed to carry do not exist
to be carried. There is nothing here that could be built truthfully yet.

## What the finding already decides, and I have not touched

`FINDING.md` is specific that the four-part assignment fencing must NOT be
weakened, and that the frozen worker-control and agent-session 1.0 wire
contracts should not be versioned unless a concrete remote consumer must
receive the new context — the sandboxed agent needs a fenced execution
reference, not authority to choose its own principal or scope. Keeping the
authorization context on the trusted manager/adapter side is the first move.

That boundary is the reviewer's and is untouched.

## Deliberately not done

**No revalidation of the W16793 matrix against the manager tree.** It names
`authority_port.py`, `schema.py`, `attempts.py` and `documents.py` — and
`schema.py`, `attempts.py` and `documents.py` are exactly the files W6629,
W6634 and W15232 have been changing this week, three of which are with the
reviewer now. A revalidation produced today describes a tree that is still
moving.

**Nothing pre-empts the approver.** Provider sequencing is pending under W16793
obligation 16832; a dependency edge is about order, not about which provider
implements what.

## State

**Blocked on W16821, unclaimed, and implementation-ready when that gate
clears.** No repository state was mutated.

## 2026-08-28 — the gate cleared legitimately, and PLAN 1 is done

Claimed W16823 at seq 34330. **No repository state was mutated** beyond this
dossier and its retained evidence; no production source was touched.

### The block I installed cleared the way it was supposed to

`W16821` is **closed satisfying** after two review rounds. So this wake is the
intended order — W16821 → W16823 — arriving as an edge rather than as a
coincidence, which is what installing it at seq 16957 was for.

### PLAN 1: measured against the delivered tree, not against the brief

`evidence/w16823-seam-revalidation.py` asks the delivered authority what it
answers, through the ONLY object the manager ever holds: a participant-bound
`Session` behind `AuthorityPort`. It writes nothing. The transcript is retained
beside it.

**What is already there and complete.** The claim decision carries all six
facts the correction wants — endpoint, principal, effective scope, role, grant
provenance, policy generation — and `assignment_events` projects it.

**What is already principal-global with no change at all.** Measured:
`slot_holder('org_b.worker')` answers about the Work claimed through
`org_a.worker`, because W16821 keyed the slot by principal. Half of boundary
item 3 — capacity — needs nothing from this Work.

**The gap, and it is narrow.** `claim` answers
`{work_ref, participant, generation}` and nothing else. The decision is
reachable only by picking a claim event out of `assignment_events`, and the
only key the answer offers is the four-part identity.

**That match is unsound, and W16821's own re-review is the authority for
saying so.** A v11 assignment mints no generation, so two claims through one
endpoint are two acts with IDENTICAL four-part identities. Measured in the
transcript: two claim answers compared `identical: True` while the authority
held claim events at seq 3 and seq 5. A manager matching on the answer cannot
say which claim it just made — which is exactly the join the re-review refused
as "not an exact identity", and which I would be reintroducing on the manager's
side of the boundary.

**And the six principal reads are absent from the session, correctly.**
`principal_of`, `grants_of`, `decision_of`, `endpoints_of`,
`policy_generation`, `slot_holder_of_principal` are configuration on the
bootstrap face the manager never holds. A manager able to ask about other
principals would be a wider capability rather than a fix. The gap is not "the
manager cannot see principals"; it is "the manager cannot name its own claim".

### Implementation NOT started, and this is the same refusal as the last two rounds

Boundary items 1, 2, 4, 5 and the labelling half of 3 all require the manager to
HOLD the principal and scope for the claim it just made. Guessing the
authority's answer is what this Work's brief forbids in terms — it "consumes the
reviewed authority projection and must not guess it in parallel" — and matching
on a nullable tuple would be guessing with extra steps.

**Two candidate shapes are proposed in `FINDING.md`**, both one additive member
at the claim seam, with the session read preferred because it changes no shape
any existing case asserts and because a session can only ever ask about the
assignment it holds. Both edit `authority/`, which is W16821's closed
deliverable, so **which Work carries them is not mine to decide** — that is the
routing question this pass returns.

### What I deliberately did not do

- **I did not add the member myself.** W16821 closed satisfying an hour ago
  after two review rounds; editing its accepted deliverable on my own authority
  is the thing passing work back exists to prevent, and W6's boundary states the
  same rule in its own words.
- **I did not build the manager side against a guessed shape.** Tests written
  against a guess become the pressure that makes the owning Work adopt it.
- **I did not touch the frozen 1.0 wire contracts.** The finding is specific
  that they change only if a concrete remote consumer must receive the context,
  and nothing measured here shows one does — the context belongs on the trusted
  side.

## State

**PLAN 1 done and evidenced. PLAN 2–6 blocked on one additive member at the
claim seam. Passed back rather than held.**

The one question that unblocks everything else: does W16823 carry the additive
authority member, or does it become a W16821 follow-up? Either answer is
workable and the shape is already written down; what is not workable is this
Work inventing it.

## 2026-08-28 — the gate cleared, and the round is sized rather than started

Claimed W16823 at seq 35029. **No production source was changed this round.**
No Git history or index was mutated.

### The ruling's version allocation, revalidated against the tree

M35002 approved authority schema 4 as the cumulative boundary. Both facts it
rests on hold, measured rather than transcribed:

    authority SCHEMA_VERSION on the tree     : 3   (W29400's Work-label model)
    claim still answers the bare assignment  : True

So 4 is the correct next allocation and is still unused, and the reason the
ruling gives for not reusing 3 is live: a schema-3 journal can hold the old
bare claim result.

### What the approved boundary is, as one coupled unit

`Core.claim` answering the closed `{assignment, claim_event, decision}` changes
the VALUE, not just an added member. Measured:
`evidence/w16823-claim-consumers-2026-08-28.txt` lists **37 binding sites
across six accepted suites** — `test_operations` 13, `test_session` 11,
`test_assignment` 8, and four more — plus `authority_port.claim` and
`offers.submit_claim` on the manager side.

**Most of those sites pass the answer on as `expect`**, which must become the
`assignment` member. Every one has to move in the same change or the suite is
broken part-way, and the two stores would sit at half-allocated versions while
it was.

### Why I did not start it

I have started a coupled change and run out inside it once in this campaign,
and the cost was another Work's uncommitted test file. The ruling asks for the
COMPLETE boundary — schema 4, the closed result, manager schema 12, atomic
persistence, replay signatures, trusted labels, and eight named regression
families — and a fragment of it leaves the authority suite red and two schema
versions half-applied, which is worse for the next round than an unstarted one.

What this round leaves instead is the thing the next round needs and did not
have: the exact list of what moves, and confirmation that the approved version
number is still the right one.

## State

**Implementation gate cleared and the unit sized. Passed back rather than
half-built.** PLAN 2–6 remain, and they are one round.

## 2026-08-29 — the approved boundary, implemented

Claimed W16823 at seq 35071. **No Git history or index was mutated.**

### The rulings, revalidated before acting on them

M34905 (the atomic closed claim result and its manager consumer) and M35002
(authority schema 4) are both responded. Both facts M35002 rests on still held
at the start of this round: the authority was at schema 3, and `claim` still
answered the bare assignment.

### What landed

**`Core.claim` answers `{assignment, claim_event, decision}`.** The assignment
is the unchanged four-part fence. `claim_event` is the `assignment_event.seq`
this claim wrote, read back rather than remembered. `decision` is read back
from the row `_record_decision` just wrote -- through the SAME reader
`decision_of` answers history with -- so what a claimant receives and what the
journal retains cannot become two spellings. **Authority schema 4** with no
table change: the version exists because a schema-3 operation journal can hold
the OLD bare answer and this build would hand it to a consumer reading it as
the closed document.

**The port owns the whole result, by both doors.** A submitted claim and a
commit this manager never saw reach the same columns, so they are held to the
same rules: closed shape; a claim event counting from one; a policy generation
counting from one; the durable grant vocabulary; and THREE RELATIONS -- the
decision's endpoint IS the assignment's participant, and its scope and role ARE
what this offer froze from the Work projection at issuance. `scope` and `route`
moved from `PROJECTION_UNREAD` to `PROJECTION_READ` to make that last pair
possible; without them "relationally inconsistent" would have been a phrase
rather than a refusal.

**Manager schema 12.** The offer freezes `work_scope`/`work_route` at issuance
and retains the exact event, principal, scope, role, grant and policy
generation on the claim -- all six or none, tied by CHECK to `state = 'claimed'`
so a settlement that authorized nothing cannot carry evidence of one.
Activation copies them onto the attempt in the same UPDATE that fixes the
fence, under an all-ten-or-none CHECK. `schema.CLAIM_CONTEXT` is the one table
naming the offer column, the attempt column and the composed member, so the
three spellings cannot drift.

**The context rides both replay signatures.** `{offer_id, state}` alone meant
"this offer reached claimed", so a settlement under a different principal
replayed the first record; the activation signature had the same hole one row
later. Both collide now, and both are measured by removal.

**Runtime labels carry `principal` and `effective_scope` BESIDE the fence.**
The manager derives them from the activated row; the two adapter doors that
compose a selector receive them as a trusted `context` operand, because an
adapter holding a control store would be the capability the isolation topology
exists to withhold.

**Nothing below the authority can choose any of it.** There is no operand for
principal or scope on any public operation -- proved by inspecting every
callable in the package rather than by assertion -- and `activate_assignment`
still takes exactly `{store, port, attempt_id, expect}`.

### The acceptance clause that is not implementable, and what replaced it

The original acceptance asked for an injected claim answer with a "well-formed
but WRONG principal" to be refused. M34905 supersedes it and this cut records
the boundary as a CASE rather than pretending to a check: a different but
internally consistent principal from the trusted authority is PERSISTED, and a
companion case proves the six principal reads are absent from the port's
session surface -- so the absence is checkable rather than merely intended.

### One thing the tree told me that no plan did

`worker-control-1.0.schema.json` already makes **`claim_event_seq` a required
member of the frozen `assignmentManifest`**, and nothing in production composes
one: `check_input_pair` validates a manifest the caller supplies, and the only
composers are fixtures writing a literal 7. So the frozen wire had already
decided this fact was necessary and this build had no source for it. The
manager's column is named `claim_event_seq` for that reason -- the frozen
vocabulary's own spelling, not an invention -- and no file under `contracts/`
was touched.

### Existing tests edited, and exactly what changed in each

The approver changed the claim ANSWER, so every site binding it had to move in
the same change. **37 sites in six accepted suites**, and all but one are
plumbing: `x = core.claim(...)` becomes `x = core.claim(...)["assignment"]`
where the site wants the fence, and stays whole where the site compares against
the operation JOURNAL -- which retains the result and must replay it byte for
byte. Registry files (`test_catalog`, `tools/parallel_test`, `test_dependencies`
OPERANDS, the boundary inventory's probe table) took additive members.

**One assertion genuinely changed**, and it is named here rather than buried:
`AnIdentityIsMoreThanAShape.test_the_frozen_range_is_owned_where_the_document_is`
expected the label "the claim answer's identity" and now expects "the claim
answer's result". The property is identical -- the frozen range is owned
exactly once, by the OUTERMOST exact-POD owner -- and what moved is which
document is outermost.

### A regression I caused in the inventory, and repaired

Routing the assignment's ownership through `_claim_result` put it TWO private
helpers from the public door, and the boundary inventory follows exactly one.
So twelve crossings stopped being attributable -- still enforced, no longer
provable, which is the failure mode that whole file exists to prevent. The port
now calls `boundaries.document`, `_assignment` and `_decided` from the public
method, each one level down, and the inventory names all of them again. The
subjects are `claim.assignment.*` rather than `claim.*` because the document
genuinely nests one level deeper now.

### Gates

- `tests/authority`, whole suite -- **320 tests**, 3 failures, all
  pre-existing and W29400's (two snapshot-isolation cases and one replay case
  in `test_work_labels`).
- full v12 parallel source -- **identical to the baseline I measured before
  touching anything, by shard name AND by count**:

      before   282 shards, 1760 tests, 16 failures, 9 errors
      after    294 shards, 1798 tests, 16 failures, 9 errors

  The twelve failing shards are the same twelve: two `test_work_labels`
  (W29400), one `test_dependencies` (W33936's `workspace_gid` registry drift),
  three `test_oci` (the 12 cases damaged under W33936 and reported there), and
  six `test_boundary_inventory` (the accepted baseline). Transcript:
  `evidence/w16823-gate-2026-08-29.txt`.

  An interim run sat at 19 failures, and I chased the three rather than
  rounding them off: two hand-built attempt-row fixtures in the boundary
  inventory carried the fence and not the context, which the attempt's
  document contract correctly refuses. They are fixtures, they are fixed, and
  the count is back where it started -- a "+3 I could not attribute" would
  have been an unexamined regression sitting inside somebody else's accepted
  failure.
- every guard measured BY REMOVAL --
  `evidence/w16823-mutations-2026-08-29.txt`. Twelve mutations, twelve named
  failures. One measured zero on the first run: owning only the assignment on
  the LATE-commit path. That was a real coverage hole, not a harness artefact,
  and the case that closes it drives five malformed committed settlements.

### What I am reporting rather than fixing

`attempts.assignment_principal` and `attempts.assignment_scope` are owned and
unprobed in the boundary inventory. They join a PRE-EXISTING family:
`attempts.input_digest` and `attempts.runtime_attempt_id` were already there
before this cut, because `column_probes` derives probes for the offers and
operations tables and for no other. Covering mine alone would mean a partial
attempts derivation in a file this Work does not own; covering the family
properly is its own change. I am naming it rather than leaving it in a count.

## State

**PLAN 2-6 done. Passed back for independent review.**

Not this cut and unchanged: W32649 owns the cross-attempt runtime lane, and
nothing here pre-implements it.
