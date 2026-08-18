# Progress

## Step 1 — the rewrite (2026-08-18)

`docs/EFFECTIVE-BATON.md` replaced wholesale: 335 lines of protocol-10
mailbox operation become 441 lines of v11 operating guide. The old
document was not merely a stale command reference — it taught the wrong
UNIT OF ACCOUNTABILITY (claim a message, reply, close it). A mechanical
command substitution would have left agents with the v10 mental model
and recreated exactly the races v11 prevents, so the structure is new:
the model paragraph, one-time setup, the straight-through path, then
each thing that makes Work stop moving, in the order an operator meets
them.

### The ordering constraint was real, and is now satisfied

W104 was deliberately not started twice, because the FINDING requires
examples written and executed against the FINAL request grammar rather
than a pre-W159 workaround. W159 is now closed satisfying, and the
question I had flagged as unruled turned out to be answered by the
shipped implementation:

    a blocking request suspends W16, which is unclaimed;
    claim it first or send the request with wait=false

That refusal — and its sibling for somebody else's claim — is now
documented, because an example omitting it simply cannot run.

### Everything is executed, nothing is remembered

Every command and every quoted refusal in the guide was run against a
built release in a throwaway home. That process corrected two things I
would otherwise have written from memory:

- I assumed a second open trial would be REFUSED. It is not: `try`
  SUPERSEDES the open trial, and both trials plus their evidence survive
  in the record. The guide documents supersession because that is what
  the authority does.
- `accept` returns BOTH `work` (the consumer) and `provider` (the newly
  created provider Work). My first read took `work` for the provider.
  The guide calls the distinction out, since the obvious misreading
  silently gates the wrong item.

Also captured from real refusals rather than invented: route/kind handles
are limited to 6 display cells; `include=` takes endpoint selectors, not
participant addresses; a claim leaves phase untouched; and a proposal
cannot authorize its own acceptor.

## Step 2 — acceptance (2026-08-18)

W103 R5's lesson was that a hand-verified claim does not protect a
release, so this lands with both halves.

**Regression protection** — `tests/work/test_w104_effective_baton.py`,
nine checks. The mechanical ones are the durable value: every verb the
guide tells a reader to run must exist in `cli.GRAMMAR`, and every phase
and outcome it names must be in the authority's own enums. A guide that
drifts ahead of or behind the shipped grammar now reds the gate instead
of being discovered by a reader whose command refuses.

**Acceptance proof** — `verify-examples.py` beside this record, a
re-runnable script asserting 37 properties across all six required
workflows against a built distribution. It is not in `tests/work`
because it needs a real deployment and coordination home, which the
hermetic suites do not provide; it is kept executable rather than as a
transcript so a future release can be checked the same way instead of
trusted. `example-home.baton.json` is the exact config it runs against.

**Packaging** — the guide now ships in `doc/` with the release, for the
same reason the agent policy does: a participant learns how to work THIS
release safely from this release. `test_deploy_v11.py` asserts the
deployed copy is byte-equal to source and names protocol 11.

### A correction in my own earlier work

W103's `test_the_readme_does_not_send_readers_into_a_non_v11_guide` was
written to retire itself once this guide became v11. Its mechanism was a
token scan including `mailbox`, which misfires: my rewrite names the
retired mailbox in a RETIREMENT sentence, which the sibling test already
allows via a disclaimer window. Rather than edit a review-pending test's
assertion, I rephrased the guide's sentence so the guard retires exactly
as designed. The weaker token scan is worth replacing with the
window-based rule when W103 next moves; flagging rather than doing it.

### README

The README's documentation table linked every current document except
this one, with an explicit note that the link would be restored once the
content was v11. That condition is now met, so the guide is linked and
the note is gone — leaving it would have made the README lie. This
touches W103's file for precisely the reason W103 R2 wrote the note.

### Evidence

- Release under test: `archive_sha256`
  `a909332b32eabd0b4b2f361e90f4ddb9cc860db0458b68c9fa08e290eb63509d`
- Examples: 37/37 verified against that artifact.
- Break-sweeps: an unknown verb, an invented outcome, a dropped
  claim-before-execute rule, a `pass` supplying its own phase, and an
  undocumented `wait=false` each red their own check and nothing else;
  removing the guide from `SOURCE_ASSETS` reds the deploy shape test.
- Gate: **1040 passed** + 4 serial + acp 35/35 on 32 cores; whitespace
  check clean.

## Step 3 — the post-W245 response (2026-08-18)

W245 landed, so the guide and its proof move to the final route /
nullable-current contract. The pre-W245 evidence in step 2 (artifact
`a909332b...`, 1040-test gate) describes a projection that no longer
exists and is kept only as history; the candidate evidence below
supersedes it.

### The finding's own terminology

`FINDING.md` stated the superseded contract as live, which left two
contradictory live rules in one record. Appended a dated supersession
section rather than rewriting the confirmed text: it maps every clause
that says Current-as-endpoint onto `route`, and states that `current` is
now the exact claimant or null.

### The request invariant

The guide said the route does not move because the answer is owed to
"the current handler" — half right in a way that hides the interesting
fact. Both halves are now stated separately: the ROUTE does not move,
and CURRENT does clear, because entering the wait releases the claim.
Nobody is executing Work that is blocked on somebody else's answer.

### Scope-revision authority — a correction to the review

Review finding 3 asked for the revision paragraph to say "exact current
claimant". That would document a stricter rule than the product
enforces. `revise_work` gates on `_handler_gate`, which resolves ROUTE
membership and never consults the claim, so an eligible handler holding
NO claim may promote a contract on Work claimed by somebody else.

Reproduced before writing anything: with `ada` and `bee` both handlers
of one route and `ada` holding the claim, `bee` promoted revision 1
successfully. The guide therefore says a resolved **Route** handler, and
adds that it does not require holding the claim. Raised here rather than
silently following the instruction; if the intent is to CHANGE that
authority to the claimant, that is a behavioural finding of its own and
not a documentation fix.

### The regression that protected the wrong model

`test_the_guide_keeps_the_blocking_request_precondition` accepted either
"Current does not move" or "answer is owed *to*". W245 made the first
false, so the check would have passed on a guide teaching the
superseded model. Split into two: the precondition check keeps the
W159 half, and a new check asserts route stability and claim clearing
as separate facts AND that the superseded sentence is absent. A third
new check pins the route-handler revision authority.

Both new checks collapse whitespace before matching — the phrases wrap
across lines, and a line-by-line match reports a true statement as
missing. That exact trap cost a round on W245.

### The executable proof

`verify-examples.py` gains section 7: route and current read as
SEPARATE values across create, claim, blocking request, response wake,
release, pass, and close — so a transition that moves one can never be
reported as having moved the other. It records the one asymmetry that
matters: `pass` moves the route AND clears current, while every other
suspension leaves the route alone.

### Candidate evidence

- Release under test: `archive_sha256`
  `a38c0c8b4bad12db27259b7fd9fe9e7877c2987248a47c280b17e258a5ec8434`
  (built from this tree, ships this guide).
- Executable workflow proof: **44/44** verified against that artifact,
  in a fresh coordination home.
- Focused W104 + deployment checks: green.
- Complete gate: **1062 passed** + 4 serial + acp 35/35 on 32 cores.
- Whitespace check clean.

## Step 4 — W288 lands the claimant-only contract (2026-08-18)

My step-3 pushback was accepted as a behavioural defect and became W288.
The authority now requires the exact current claimant for `revise`, so
the guide's scope-revision paragraph is corrected AGAIN — from the
route-handler authority I had documented (accurate to the old
implementation) to the claimant-only contract that was always intended.

The W104 regression moved with it and now pins four claims: the exact
current claimant, still-eligible-through-route, unclaimed refuses, and
the peer refusal text.

`verify-examples.py` now proves the boundary publicly rather than only
the happy path: an eligible route peer refuses on claimed Work, that
refusal changes no contract, the claimant promotes, and promotion
refuses once the claim is released.

Candidate evidence superseding step 3's: `archive_sha256`
`5f369b4f161e92c6011957514db3840a8f70734f2ecbaafbf7b70322327b695b`,
**48/48** executable proof, gate **1073 passed** + 4 serial + acp 35/35.

## Step 5 — post-W288 candidate evidence (2026-08-18)

W288 closed satisfying, and its step 4 already landed this review's
items 1-3 inside that Work: the `FINDING.md` W288 supersession naming
claimant-only promotion, the guide wording, the replaced regression, and
the executable proof of both the claimant success and the eligible-peer
refusal.

Item 4 was NOT complete, because W288's own review round then changed
`cli.py`'s `revise` help. The candidate recorded in step 4
(`5f369b4f...`, gate 1073) therefore no longer matches the tree that
ships this guide. Rebuilt and re-ran everything against the final state
rather than letting a stale digest stand as the release evidence.

### Candidate

- Release under test: `archive_sha256`
  `056c2ccb7668a131613fd77ec2d90974c1df21bd778cb89d4f1edf0e6256df7b`
- The shipped `doc/EFFECTIVE-BATON.md` is byte-identical to source.
- Executable workflow proof: **48/48** against that artifact, in a fresh
  coordination home — all six required workflows plus the W245
  route/current transition matrix and the W288 revision boundary.
- Focused W104 + deployment + public-docs checks: 28 passed.
- Complete gate: **1075 passed** + 4 serial + acp 35/35 on 32 cores.
- Whitespace check clean.

Every earlier digest in this record (`a909332b...`, `a38c0c8b...`,
`5f369b4f...`) describes a superseded tree and is kept only as history.
