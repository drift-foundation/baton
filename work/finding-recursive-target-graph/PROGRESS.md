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

### Gate B — B1, B2, B3 (2026-08-14)

`src/baton_work/tui/` (renderer of the canonical projection; imports held to
projection+transitions by AST test, no SQL); `tests/work/ptyharness.py`
(compact grid replay); `test_tui.py`, `test_parity.py`, `test_packaged.py`.
Suite: tests/work 101 passed + 1 xfailed; `just test-v11` split runner green;
full gate 2998 passed + 1 xfailed.

**B1** — real-pty: home table with the pinned borderless fixed columns,
Enter drill + breadcrumb, escape climbs back, discussion shows the planned
Next, explicit `s` commits the seen cursor, and VIEWING ALONE changes
nothing. Refuse-before-curses is held as a strict xfail because it exposed a
GATE A SEMANTIC GAP, reported for ruling (message 726165a5…): the projection
read surface never validates the viewer, so an unknown member gets an empty
console instead of a refusal. Not patched — the gate forbids changing the
shared projection unilaterally, and no TUI-side workaround exists through
the permitted surfaces.

**B2** — same-fixture parity: home rows value-by-value (title, status,
ready, current, next, New) for four viewers; drill children order; the
obligation count on the console header vs the JSON actionable list; and one
mark_seen through the CONSOLE re-read by both surfaces — the decomposition
moves by exactly `own`. The parser decodes rows with the app's own column
budget, so a layout change moves both or fails.

**B3** — the scenario through a zipapp built by stdlib `zipapp` from the
same sources, with PYTHONPATH stripped, plus a poisoned-lookalike test
proving the archive answers alone. Stated plainly: v11 has no catalog entry
yet, so the artifact is built in the test rather than by `just build` — the
release integration is later work outside this gate.

Harness findings, fixed in the harness not the renderer (verified by
driving the renderer with a fake screen first): the v10 tokenizer never met
ECH, relative cursor moves, or erase-below; and the child's winsize ioctl
races curses init under pytest, fixed by stating LINES/COLUMNS.

One v10-suite adjustment: `test_the_session_hook_does_not_prepare_the_
candidate` forbade ALL pytest hooks in conftest; bed522d's `pytest_configure`
registers the serial marker and builds nothing, so the assertion now permits
exactly that hook and still refuses anything that builds or does more than
register markers.

### C1 — v11 configuration schema and loader (2026-08-14)

`src/baton_work/config.py`, pure per the authorization: strict parse with
duplicate keys refused at every level, unknown fields refused at every
level, 6/6 grammar at every identity position, protocol/generation/identity
fields validated (uuid 32-hex in `instance`, `database` fixed to
work.sqlite3, no WORK.json anywhere), participants first-class with
display/roles/capabilities, named routes (role + handlers, handlers must
HOLD the role), kinds resolving through named routes.
`tests/work/test_config.py`, 27 tests; work suite 128 passed + 1 xfailed.

Refusals are exercised by MUTATING the one valid document, never strawmen;
the grammar vectors run at all five identity positions. Break-sweeps:
dropping the duplicate-key hook fails the parse test; disabling the
handler-holds-role check fails its reference test. Purity held bluntly:
loading twice creates nothing and touches no mtime. The read-side
no-transaction boundary test now covers config.py.

STOPPED after C1 evidence as authorized. C2 (acceptance, generation
transitions, stranding policy) remains held.

### C1 rev 2 — reviewer-reproduced strictness gaps closed (2026-08-14)

All four reproduced gaps fixed in `config.py` and pinned by 15 adversarial
vectors plus a hostile-shape sweep (42 config tests total, 143 work suite):
- `_exact_int`: bool is an int subclass and 1.0 == 1, so plain equality
  admitted `true` and floats for config/protocol/generation — now
  type-exact with the offending type named;
- `_string_list`: role/handler/capability lists refuse non-string members
  (previously a raw TypeError path via iteration/membership), refuse
  duplicates ("a repeated entry is a claim nothing distinguishes");
- empty `teams` refused ("an instance with nobody in it is a mistake, not
  a bootstrap");
- non-string route/kind references refuse legibly.
The blanket test drives ~66 hostile shapes at every field and accepts
nothing but WorkError.

### C2 — config↔authority binding (2026-08-14)

`src/baton_work/lifecycle.py` (`init_from_config`, `open_bound`,
`accept_config`); schema gains roles/routes/route_handlers/member_roles/
member_capabilities projection tables plus removed flags; WORK.json creation
REMOVED from the authority and its test replaced by one pinning the ABSENCE.
`tests/work/test_lifecycle.py`, 15 tests (work suite 158 + 1 xfailed).

Evidence per the authorization:
- crash-safe init: built complete in a temp sibling, published by one atomic
  rename + dir fsync; a simulated crash at the commit point leaves NOTHING
  at work.sqlite3 and the retry succeeds;
- bound open validates the triangle directly (uuid pair, digest
  "edited but not accepted", generation agreement);
- acceptance: generation+1 declared in the proposal, audited event with
  old/new generation, digest and structural diff (added/removed/rerouted);
  topology tables are the projection (mark-removed, never delete);
- capability gate: grace granting herself `config` IN the proposal cannot
  accept it — the capability is read from the accepted generation;
- stranding refusal names the records (open work + pending obligations) and
  the same proposal passes after the work is closed;
- no silent reuse: a kind retired by generation 2 refuses reintroduction in
  generation 3;
- 16-process acceptance race: exactly one winner, losers legible, sequence
  dense.

Two defects found and fixed on the way, both by tests:
- the generation check ran BEFORE the write transaction, so every racer
  "won" and each wrote its own acceptance event — the same
  validate-inside-the-lock lesson as the A3 cycle walk, now re-learned at
  the acceptance boundary and break-swept (removing the in-lock recheck
  fails the race test);
- my first edit attempt left `old` as a tuple via a trailing comma and
  silently changed nothing — caught because the race test still failed, and
  a reminder that an edit is proven by the test that needed it, not by the
  script reporting success.

STOPPED after C2 evidence. C3 (CLI migration, route-resolution transitions,
projection 2.0) and later remain held. Noted for C5: the preserved Gate B
PTY tests need `serial` marks for the split runner.

### C2 rev 2 — the review's four correctness gaps (2026-08-14)

All four confirmed and fixed, each with its regression
(`tests/work/test_lifecycle.py`, 19 tests; work suite 162 + 1 xfailed;
`just test-v11` green):

- R1: publication is now atomic CREATE-IF-ABSENT via link(2) — rename
  replaces an existing destination, so of two concurrent initializers the
  second silently overwrote the winner. Regression: 8 racing initializers,
  exactly one "won", every loser refused with "already exists", the winner
  still opens and binds.
- R2: the stranding/no-reuse checks now run INSIDE the write transaction as
  the authoritative gate (pre-lock pass kept as fast diagnostics only) —
  the third occurrence of the validate-inside-the-lock lesson (A3 cycle
  walk, C2 generation recheck, now the gate). Deterministic regression:
  the pre-check is blinded for one call to model the racing writer; the
  in-lock gate refuses and nothing is projected.
- R3: routes joined the no-reuse sweep — a removed route name refusing
  reintroduction with a different role.
- R4: the reroute audit compares the COMPLETE responsibility mapping
  (role + handlers); a role-only change with the same handler now reports
  `rerouted`.
