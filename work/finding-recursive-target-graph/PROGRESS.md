# Progress — Baton v11 Work graph, Gate A

Owned exclusively by `baton.implementer`. Created on Gate A authorization.

## 2026-08-14 — Gate A opened

Authorization: message `f7a220277798c5407abe9512c539bedb` from
`baton.reviewer` under the pinned delegated-authorization update
(`0efb3554b17e822debee419726d85a12`), following IMPLEMENTATION-PLAN rev 4.
Slawomir's rulings represented: 11.0.0; 6/6 canonical handles + display
names; re-readable/no receipts; explicit `mark_seen` with pure reads.
Resource grant: up to 16-way test execution (`753e8dc269586682e68e14dfcf8698c4`).
Scope: A1–A8 serially, plan rev 4. Gate B is NOT authorized.

The stale scenario heading was corrected before starting, as instructed.

## Step log

(One entry per step, appended when its acceptance evidence exists.)

### A1 — schema, sequence, identity (2026-08-14)

`src/baton_work/{__init__,authority}.py`; `tests/work/test_authority.py`,
25 tests.

Evidence:
- 16 concurrent processes, 400 registrations: sequence exactly 1..400, no
  duplicate, no hole; restart continues above the last committed number.
- Identity grammar: `implementer` (11 cells), `reviewer` (8) and `research`
  (8) all refused with the measured count — the protocol-10 casualties are
  the test vector. CJK width measured (6 chars = 12 cells refused, 3 chars =
  6 cells accepted); combining marks and zero-width joiners refused outright.
- Kinds retire but never vanish or come back.
- Purity: database file hash identical across meta/events/failed-validation
  sweeps.

The first break-sweep (allocation moved outside the transaction) PASSED —
the suite was weak: every refusal happened in pre-validation, never inside
the transaction. Two tests added to reach the property: an exploding mutate
after allocation, and 16 processes racing to register the SAME five teams
(pre-check passes everywhere; constraint refuses losers in-transaction).
The race test then found a real defect — losers escaped as raw
`sqlite3.IntegrityError` — fixed by translating to `WorkError` in `_write`.
Re-applied break: the exploding-mutate test fails (burned number visible);
restored: 25 pass.

### A2 — Work + containment (2026-08-14)

`src/baton_work/transitions.py` (create/close/reopen, level-triggered
`_recompute_ready`); schema gains `work` and `messages`;
`tests/work/test_transitions.py`, 18 tests (43 total).

Evidence:
- create is Work + first message in ONE event, id qualified by authority
  uuid; crash injection between the two inserts leaves neither row and burns
  no sequence number.
- children gate the parent; closing over open children refused BY NAME;
  terminal close clears Current/Next and records the disposition; reopen
  visibly reopens the ancestor gate; reopen under a closed parent refused
  top-down.
- Break-sweep: dropping the parent recompute on close fails both the gating
  and the reopen tests; restored, 43 pass.

Defect found by writing the reopen test HONESTLY: reopen restored `Current`
from the live row that close had just nulled, leaving open work with nobody
responsible — the exact state the finding forbids. Fixed by recording the
cleared endpoint in the close EVENT and restoring from history; a close event
without a prior endpoint now refuses reopen rather than guessing.

### A3 — edges + convergence (2026-08-14)

`add_dependency` with the union cycle walk INSIDE the write transaction
(two concurrent inserts can each be acyclic alone and cyclic together; the
IMMEDIATE lock serializes them); readiness is now the conjunction of open
children and open blockers. `tests/work/test_edges.py`, 8 tests (51 total).

Evidence:
- the finding's LANG-42 scenario executed literally: three teams converge,
  one close fans out, the dependent with a second blocker stays blocked, the
  provider sees fan-in of 3;
- reopen re-blocks every dependent through the same recomputation;
- a union cycle (containment + dependency, each graph acyclic alone) refused
  with the loop named; self/duplicate edges refused; a closed work takes no
  new blockers; an already-closed blocker gates nothing.
- Break-sweep (the plan's named one): recompute replaced by an event-walk —
  the multi-blocker case and the reopen case both fail, which is exactly the
  pair level-triggering exists for. Restored: 51 pass.

### A4 — tags, obligations, seen, planned Next (2026-08-14)

`post_message` (include/request/pass with the cardinality law),
`respond_obligation`, `dispose_obligation`, `mark_seen`; tables
`work_participants`, `obligations`, `seen`. `tests/work/test_tags.py`,
18 tests (69 total).

Evidence:
- `+` expands wildcards over live endpoints, deduplicated, and the EXACT
  expansion is recorded in the publication event (ruled); a selector that
  lands nowhere refuses at tag time.
- `@` creates one pending obligation and the baton does not move; every
  fan-out shape (`*.bug`, `push.*`, `*.*`, comma list) refused; respond
  discharges with the answer in one transaction; dispose is the explicit
  no-action answer; a second discharge refuses.
- `=>` moves the one Current; pass-with-Next plants the return; the pass to
  the planned endpoint is AUDITED AS `return` and consumes it; a detour
  leaves Next visibly set.
- `mark_seen` is the only cursor writer, idempotent, monotonic, per member.
- Break-sweeps: silent Next clear on detour → the detour test fails;
  monotonicity guard removed → the cursor test fails. Restored: 69 pass.

### A5 — canonical projection, pure (2026-08-14)

`src/baton_work/projection.py` (home, breadcrumb, children, links,
discussion, new_count, obligations, detail); THE shared fixture
`tests/work/fixtures.py`; `tests/work/test_projection.py`, 8 tests
(77 total).

Evidence:
- home is the viewer's own top-level table and a linked external record does
  NOT enter another team's default table (noise boundary), while `links`
  exposes the LANG-42 fan-in to any driller (open graph) — both rulings in
  one pair of tests;
- `New` is per member and decomposes exactly (`own + Σ children`), and a
  team that participates only at the epic's root contributes zero through
  the children — the containment-only, no-cross-team-aggregation rule;
- obligations are the actionable set: a responded one leaves, a `+` never
  enters;
- `detail` declares available transitions per viewer (a blocked work does
  not offer close; the planned Next is visible);
- purity: authority file hash identical across the ENTIRE read surface swept
  as all five members.
- Break-sweep: a discussion read that "helpfully" advances the reader's
  cursor fails the purity sweep. Restored: 77 pass.

Fixture defect found while wiring: step_fix was created already AT lang.impl
and the fixture then passed it to lang.impl — refused by the no-op-pass
guard. Fixed by creating at rsrch and passing, which is the canonical flow
anyway.

### A6 + A7 — JSON surface, CLI, and the gate scenario (2026-08-14)

`jsonapi.py` (envelope: projection/protocol versions, authority uuid,
snapshot seq, viewer; major-version compatibility that FAILS clearly),
`cli.py` (`baton-work`: every read and every transition, JSON out, JSON
errors on stderr with exit 1); boundary tests. `tests/work/`, 88 tests.

Evidence:
- pagination joins with no skip or repeat across a 41-message same-second
  burst — the protocol-10 defect demonstrated fixed, because the cursor is
  the sequence;
- the LANG-42 fan-in is reachable from a consumer BY TYPED TRAVERSAL ALONE
  (blocked_by → provider → blocks);
- incompatible projection major refused, compatible minor served;
- every mutating verb returns the committed record, and the audit
  vocabulary distinguishes post_message / request / pass / return (tightened
  when the CLI test exposed that an ordinary pass audited as a plain
  message);
- A7: the full gate scenario through the CLI AS A SUBPROCESS — create,
  include, request-response, block, pass-with-Next, consuming return,
  terminal close, dependent unblocks — with the dense ordered audit trail
  asserted at the end.

Two honest corrections along the way:
- my out-of-order test invented a rule (close refuses over an open BLOCKER);
  the rulings refuse closure only over open children — a consumer may close
  honestly (reject/duplicate/defer) while its provider is open. The test now
  documents that deliberately and asserts the ruled refusal instead.
- the boundary test failed on its own package docstring (grep found the
  words "baton_core" in prose saying we do not import it); rewritten over
  the AST to read imports rather than prose.

### A8 — adversarial soak, and Gate A complete (2026-08-14)

`tests/work/test_soak.py`; artifact `soak-report-2026-08-14.json` beside this
file. 16 workers × 150 seeded ops against one authority: four saboteur
workers inject exceptions INSIDE the write transaction (84 injected failures,
every one rolled back), two workers die by `os._exit` INSIDE an uncommitted
transaction (rows inserted, sequence allocated, no commit — SQLite crash
recovery for real; the first version exited BETWEEN transactions and the
docstring overclaimed, fixed before recording). 2120 events committed; 42
refusal classes in the taxonomy, all legible WorkErrors including
mid-transaction race losers.

Post-soak, everything re-derived from scratch and compared with what the
transitions maintained: dense sequence, stored `ready` == recomputed
readiness for every work, every open work has a responsible endpoint, the
union graph is acyclic, obligation bookkeeping consistent, and the full read
sweep as every member changes no byte.

Suite: tests/work 89 passed. Full gate `just test`: 2986 passed, 0 failed.

Retired en route, with the reason in the module: the two R38
proposal-exercising tests, whose subject (`proposed-baton.json`) was consumed
by the v10 cutover and then dropped from the tree by commit fb9420a. A test
suite must not read live production config, and a copied fixture would be the
lookalike R38 forbade.

**Gate A: A1–A8 all complete with acceptance evidence and break-sweeps.**
Gate B (TUI + parity) is NOT authorized and nothing of it exists.
