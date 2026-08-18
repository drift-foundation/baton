# Progress

## Step 1 — the authority correction (2026-08-18)

`revise_work` gated only on `_handler_gate`, which resolves ROUTE
membership. Route says who MAY claim; it never said who is executing, so
one eligible handler could replace the live contract of Work another was
executing — the single-executor boundary the claim exists to draw.

The check now requires the exact current claimant IN ADDITION to live
route eligibility, and it runs inside the same lock as the revision
compare-and-swap. That placement is the point: a claim released, passed,
or recovered between the caller's read and the write fails closed
instead of racing.

Two refusals, deliberately distinct:

    revise: W2 is unclaimed; the Work contract is promoted by the
    participant executing it — claim it first, or keep proposing in
    the thread

    revise: W2 is claimed by lang.ada; a route peer may propose in the
    thread but never rewrites assigned scope underneath its executor

Eligibility is still checked FIRST, so a foreign team hears that it is
not a handler rather than a claim-ownership fact it could not act on.
The authorization snapshot in the event payload now records the
claimant, so the evidence says who was executing when the contract
moved.

## Step 2 — acceptance (2026-08-18)

`tests/work/test_w288_revise_requires_claimant.py`, 11 checks on the
two-handler-one-route shape that produced the defect: the claimant
promotes; an eligible peer refuses with NO mutation (no seq burned, no
revision, route/current/phase unchanged); unclaimed Work refuses while
discussion stays open; an outsider refuses on eligibility.

Losing the claim ends the authority through every path — release, pass,
and forced recovery — and a release landing INSIDE the committing
transaction refuses rather than racing. Effectively-once holds: an exact
retry replays the one revision, and a retry after the claim moved
replays the stored result rather than becoming fresh authorization for
somebody no longer executing, while a genuinely new request from the
former claimant refuses.

Break-sweep: dropping the claimant check reds 8.

## Step 3 — the suites that encoded the old contract

Seven gate failures, all one cause: tests promoting a contract without
claiming. Each gained the claim its setup now needs; no assertion was
weakened.

Two got genuinely stronger rather than merely repaired:

- `test_revisions.py`'s reassignment case asserted that accepting a new
  generation moves revision authority. Under W288 it does not by
  itself — W245 deliberately preserves the identity a live claim
  captured. It now proves three things in order: the former handler
  refuses on eligibility, the incoming handler refuses on the CLAIM
  while eligible, and only recovering the claim transfers the
  authority.
- WF11's transfer step likewise became two-step: the pass moves
  eligibility and clears current, and the incoming handler holds the
  authority only once it claims.

## Step 4 — W104's guide and proof

The guide taught route-handler authority — true of the implementation,
wrong as a contract. It now names the exact current claimant, states
that eligibility alone is not enough, quotes the peer refusal, and says
unclaimed Work refuses. The W104 regression was inverted to match and
now pins all four claims.

`verify-examples.py` proves it publicly: an eligible route peer refuses
on claimed Work, the refusal changes no contract, the claimant
promotes, and promotion refuses once the claim is released.

## Evidence

- Release under test: `archive_sha256`
  `5f369b4f161e92c6011957514db3840a8f70734f2ecbaafbf7b70322327b695b`
- Executable proof: **48/48** against that artifact in a fresh home.
- Gate: **1073 passed** + 4 serial + acp 35/35 on 32 cores.
- Break-sweep: removing the claimant check reds 8.
- Whitespace check clean.

## Step 5 — review round 1 (2026-08-18)

Both gaps were real, and the second is pointed.

**Public help.** `revise` described only the compare-and-swap, so the
one precondition an operator cannot infer — that eligibility through
the route is not enough — was discoverable only by being refused. The
verb help now states that the exact current claimant, still eligible
through the route, may promote it, and that unclaimed Work refuses; the
`work=` operand says you must hold its claim.

Two assertions guard it rather than one. The first pins the help text.
The second is the useful one: it asserts each of the help's three
claims against the LIVE authority in the same test — unclaimed refuses,
a route peer refuses, an outsider refuses on eligibility, the claimant
succeeds. Help and behaviour can now only drift apart by reddening.

**The record that still stated the rejected rule.** The W245
supersession I appended to W104's `FINDING.md` closed with a paragraph
reporting that a route handler holding no claim could promote a
contract — accurate about the implementation that day, and the exact
behaviour W288 then deleted. It had become the last authoritative
reading of that record, so the file asserted the defect as the rule.

Appended a dated W288 section after it rather than editing: route
controls eligibility, the exact current claimant alone promotes,
unclaimed refuses, both revalidated in the committing transaction. It
names the route-peer success recorded above it as the defect W288
corrected, so a reader reaching the end of the file gets the live rule
and can still see how it moved.

That is twice now that a supersession I wrote became stale within a
day. The durable protection is the executable one — the help/authority
drift check and the W104 guide regression — rather than the prose.

Break-sweep: dropping the precondition from the help reds both new
checks.

### Evidence

- Gate: **1075 passed** + 4 serial + acp 35/35 on 32 cores.
- Focused W288 + W104 + revisions: 36 passed.
- Whitespace check clean.
