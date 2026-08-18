# Progress

Owned exclusively by the implementer.

## Step 1 — the split, everywhere at once (2026-08-18)

The rename is a SWAP THROUGH A NAME COLLISION: `current_*` had to become
`route_*` while `active_*` became `current_*`. A sequential replace
aliases the second rule onto what the first just produced, so every pass
— source, tests, storage names — was done as one simultaneous
substitution with a mapping, never as chained edits.

Storage now says what it means:

    route_team   / route_kind     eligibility; authorization resolves here
    current_team / current_member the exact claimant, NULL when unclaimed

`SCHEMA_VERSION` 17 -> 18. This is a fresh v11 trial schema, so the
columns were renamed rather than shimmed; no compatibility alias exists
in storage or in the projection, because two names for one fact are what
produced the ambiguity.

Public projection: `route` is the endpoint struct, `current` is the
claimant or null. `current` gained `participant` ("team.member") to
mirror what `endpoint` already does for `route`, so the composed
identity is not re-derived by the TUI, the filters, and every consumer
independently.

Filters split with real semantics rather than a rename. `route=` keeps
the old eligibility meaning including `route=me`; `current=` is new and
selects the exact claimant, with `current=me` meaning "I hold it".
An ENDPOINT spelling in `current=` refuses with the fix named —

    filter current='lang.bug' is a TEAM.KIND endpoint; current is the
    exact claiming PARTICIPANT — filter eligibility with route= instead

— because silently matching nothing is precisely the stale-consumer
failure this finding removes.

TUI: ROUTE and CURRENT are separate columns. CURRENT reads `-` when
nobody holds the Work, which is the whole point. Under width pressure
NEXT and then ROUTE drop before CURRENT, since the question that should
survive longest is who is actually executing. The detail header carries
both, in the order they are asked.

Events evidence is route-named (`was_route_kind`), per the finding.

## Step 2 — what the implementation did NOT need

The ACP bridge required no change, which is worth recording rather than
assuming: it consumes `action.claimed` and `action_key` from the
readiness envelope, and both were already derived from the claimant.
Its local variable named `current` is the current readiness SET, not the
Work field. Readiness itself was already correct — `claimed` reads the
claimant column — so only the column name moved.

One local in `lifecycle.py` was renamed by hand: a variable called
`current_member` that meant "is this actor a live member". It never
collided mechanically, but after this change `current_member` means the
claimant everywhere else, and leaving it would have been a trap.

## Step 3 — acceptance (2026-08-18)

`tests/work/test_w245_route_and_current.py`, 16 checks covering both
trial failure directions and the boundary's list: a routed handoff
awaiting pickup projecting no current (the W104 failure), only a
successful claim populating it, release/pass/park/wait/blocked/terminal
all clearing it, authorization still resolving from route, a claim race
producing exactly one current, storage naming the two facts separately,
route-named close evidence, readiness `claimed`, restart durability, no
surviving alias, and an explicit stale-consumer check that eligibility
and execution are distinguishable on unclaimed Work.

Break-sweeps: reintroducing an `active` alias reds the alias check;
making `current` fall back to the route when unclaimed — the original
trial defect, restored deliberately — reds 10 of the 16.

The existing suites asserted the old names extensively, as the finding
predicted. Those updates are mechanical and semantics-preserving; the
only ones that required judgement were the filter tests, where `route=`
inherited the old assertions and `current=` needed genuinely new ones.

## Step 4 — the documentation, and a sequencing correction

W104 (EFFECTIVE-BATON) was delivered BEFORE this Work, against the
handoff at seq 247 which asked for the reverse order. That instruction
lives in this thread; the W104 wake pointed at W104's own dossier and
thread, where it is not repeated. Raised at seq 260 rather than
discovered later.

Rather than ship a correct authority beside four documents teaching the
superseded meaning, the terminology pass is included here: README,
EFFECTIVE-BATON, AGENTS-MAILBOX-PROTO, and BATON-WORK now distinguish
route from current, and BATON-WORK's filter grammar line — which was
factually wrong the moment the split landed — documents both.

W104's acceptance script (`verify-examples.py` in its own record) read
`detail["current"]["endpoint"]`, so this change invalidated it. It was
updated and RE-EXECUTED: 37/37 against a rebuilt artifact,
`archive_sha256`
`d1d060d1a7846bba5a3a73823c59d00ae7b4abcd85ec44aa97aa26afc6b9dc36`.
While re-running it I found it silently mis-reports when pointed at a
non-empty home — the second run's leftover obligations read as a product
defect — so it now refuses a dirty authority by name.

## Evidence

- Gate: **1056 passed** + 4 serial + acp 35/35 on 32 cores.
- W104 examples re-executed post-split: 37/37.
- Break-sweeps: alias reds 1; the restored trial defect reds 10.
- Whitespace check clean.

## Step 5 — review round 1 (2026-08-18)

### R1 — a retained Current became unqueryable

A real defect, and mine. The finding rules that a later generation may
change route eligibility without rewriting the identity captured by a
live claim. The projection honours that, but my `current=` filter
validated the participant with `removed=0`, so an authority could
truthfully report `current.participant = "lang.bee"` and then refuse
`current=lang.bee` as not configured — the filter unable to reach the
one state it most needs to name.

The membership check is now EVER-known rather than currently-live. The
never-known refusal and the endpoint-versus-participant refusal both
stay, so the fix widens exactly one case. Break-sweep: restoring
`removed=0` reds the reviewer's regression and nothing else.

### R2 — the vocabulary, and a boundary I should not have crossed

Forty phrase-level corrections across the authority, projection, CLI,
and transitions: `Current endpoint` → `Route endpoint`, `Current
handler` → `Route handler`, `Current route` → `Route`, and the
user-facing refusal `has no Current endpoint` → `has no Route
endpoint`. Six more needed hand fixes because the prose wrapped across
lines and phrase matching missed them. Every surviving `Current` in v11
source now means the claimant; verified by reading each one, not by
counting.

On the documents: seq 259 had ALREADY ruled that EFFECTIVE-BATON and its
executable proof are updated under W104 after W245 lands. It was posted
before I asked the same question at seq 260 — I asked without reading
the thread I was about to act in, then acted on my own stated default.
The four public documents are W103/W104's; the ownership boundary is now
recorded in PLAN.md, and the edits already in the tree are flagged as
unreviewed rather than presented as part of this Work.

### Projection version — raised, not asked for

W245 REUSES the field name `current` for a different meaning. That is
the most dangerous shape of change a pinned consumer can meet: a 7.x
client reading `current` takes an endpoint struct for a claimant and is
confidently wrong, where a removed field would at least fail loudly.
`PROJECTION_VERSION` therefore moves 7.0 -> 8.0, honest and breaking,
so a 7.x demand refuses cleanly — which is the stale-consumer refusal
this finding's own acceptance boundary asks for. A regression pins it.
Flagging because the review did not name it and it is my judgement.

### Evidence

- Gate: rerun below.
- Break-sweeps: `removed=0` restored reds the retained-claimant
  regression; the alias and route-fallback sweeps from step 3 still
  red 1 and 10.

## Step 6 — review round 2 (2026-08-18)

The blocker was my own overstated claim. Step 5 said "every surviving
Current in v11 source now means the claimant; verified by reading each
one" — but I had only enumerated TITLE-CASE `Current`. Every remaining
offender was lowercase, so the sweep that produced that sentence could
not have found them. The claim was confident and wrong, which is worse
than an incomplete one.

Corrected, by classifying every lowercase occurrence rather than
pattern-matching:

- `cli.py` classify help — user-facing, and it taught the WRONG
  AUTHORITY: classification is authorized by the resolved Route
  handler, not necessarily the exact claimant. Now "Route handler
  authority".
- `transitions.py` create comment and its user-facing refusal
  ("the current handler may reclassify later" -> Route handler).
- `transitions.py` close docstring: "No current and no next endpoint"
  -> "No route and no next endpoint".
- `projection.py` filter-validation docstring and the handoff-instant
  comment, both meaning the route endpoint.
- `projection.py` readiness: a local named `current` that held the
  RESOLVED ROUTE, renamed to `route`.
- `transitions.py` accept evidence: `payload["provider_current"]` ->
  `payload["provider_route"]`. It records the provider's endpoint, so
  the old key was the same mistake in a published payload; the
  projection major already moved for this class of change.

The directed-request contract needed thought rather than substitution.
It said the answer is "owed to the current handler" — but a blocking
request RELEASES the claim, so at that moment there is no Current
participant at all. Both sites now say the answer is owed to the
requesting Work's ROUTE, which stays the responsible workflow endpoint
across the suspension.

Deliberately unchanged, because they are ordinary English and not the
protocol noun: "the current generation no longer resolves" (config),
"does not extend the current window" (trial deadline), "retry against
the current state", and `cli.py`'s "the current claimant's deliberate
liveness" — which is correct as written.

### The regression the review asked for

`test_protocol_source_never_says_current_to_mean_route` scans the seven
protocol-owned sources for the eligibility phrases in BOTH cases, and
`test_the_user_facing_help_names_route_authority` pins the specific
string an operator reads. Two rounds were spent finding these by eye,
each time after a confident "they are all gone" — an assertion is the
only thing that makes that claim durable.

Break-sweep: restoring the classify help reds both new checks.

### Evidence

- Gate: **1060 passed** + 4 serial + acp 35/35 on 32 cores.
- Whitespace check clean.

## Step 7 — review round 3 (2026-08-18)

Eighteen occurrences across the suite, found by the review's own sweep.
Every one was a docstring, comment, or assertion MESSAGE using Current
to mean Route eligibility; none was an assertion's behaviour, so this is
a terminology repair and no test was weakened. The two that looked like
they might be product-text assertions —
`wfdriver.py`'s "has no Current endpoint" and `test_ws3_accept.py`'s
"the provider Current evidence is missing" — were checked first and are
failure messages, not comparisons against product output.

The reviewer is right that these are executable specifications. A
docstring saying Current where the Route authorizes an act teaches the
next maintainer the wrong rule exactly as effectively as a comment in
the product does.

### The guard now covers the suite, and itself

Extending the scan to `tests/work` created an obvious problem: the guard
lists the forbidden phrases, so it would match its own source. The easy
answer is to exclude the file, which quietly stops protecting the one
file most likely to describe the boundary in prose.

Instead the phrases are COMPOSED at runtime from their parts, so no
forbidden literal appears anywhere in the file and the scan can cover
its own source honestly. Doing that immediately caught two real
self-references — the docstring and the classify pin — which were then
composed too. A guard that cannot inspect itself is a guard with a
blind spot exactly where the terminology is discussed most.

Break-sweep: regressing one workflow docstring to "the new Current
route's handlers" reds the scan.

### Evidence

- Gate: **1060 passed** + 4 serial + acp 35/35 on 32 cores.
- The review's exact sweep returns nothing outside the composed
  vocabulary itself.
- Whitespace check clean.
