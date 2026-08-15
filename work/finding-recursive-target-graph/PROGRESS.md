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

### C3 — the CLI configuration boundary (2026-08-14)

Surface migrated exactly as authorized: `--config PATH` +
`--participant team.member`, with `--authority`/`--viewer` REMOVED (argparse
refuses them, tested); every ordinary read, mutation and TUI launch opens
through `lifecycle.open_bound` and validates the participant against the
accepted generation BEFORE any output or curses; `init` consumes the
generation-1 config; `regen` is `accept_config` under the C2 capability
gate; the four registry verbs are gone — accepted generations are the only
topology writer. The TUI's raw-path module entry is retired; `tui/` exports
`run` and only the CLI launches it.

Migrated with it, because the old surface cannot open config-bound
authorities: THE fixture now writes a generation-1 `baton.json` and
initializes through the lifecycle (`fixtures.config_document` /
`build_instance`); the jsonapi/scenario/parity/tui/packaged suites drive
the new flags; the pty harness execs `--config/--participant`.

THE HELD XFAIL FLIPPED: `ghost.gone` at the console is now refused before
curses claims the screen — the Gate A viewer gap, closed by the boundary
the rulings chose rather than the narrow patch first proposed.

New focused suite `test_cli_boundary.py` (6 tests): removed verbs refuse,
unknown participant refuses pre-output for reads and mutations, an edited
config refuses every ordinary command, `regen` applies gen+1 under the
capability (grace refused, ada accepted), `init` reports the binding.

Suite: tests/work 169 passed, 0 xfailed. STOPPED for review; C4+ held.

### C3 rev 2 — the review's three corrections (2026-08-14)

- R1: EVERY non-init command now requires and validates the participant —
  links/breadcrumb/discussion/events had stayed anonymous ("identity by
  assertion wearing a read-only disguise"). Regression added covering all
  previously anonymous reads; the four suites that exercised them supply
  their participants.
- R2: the last public refusal saying "viewer" now says "participant".
- R3: the fixture's `assert database == path or True` escape hatch replaced
  with the real equality against the fixed sibling.

Suite: tests/work 170 passed; test-v11 green. Still stopped; C4+ held.

### C4 — operational route resolution and projection 2.0 (2026-08-14)

Resolution snapshots: `transitions.resolve_endpoint` runs INSIDE the write
transaction (the fourth validate-inside-the-lock site — a regen committing
between a pre-read and the write would stamp a stale resolution) and records
`(endpoint, route, role, handlers, generation)` for create, every `+`
expansion entry, `@` (also into the obligation row's new snapshot columns),
`=>`, and planned Next. The kinds projection gained the kind→route mapping
it had silently dropped. History is never partly resolved and never bare.

Projection 2.0: envelope field `participant`; every endpoint-bearing value
(home/detail/links rows, obligations' `owed_by`) is a structured
`{endpoint, route, role, handlers}` resolved at read time against the
CURRENT generation, with an unresolvable endpoint shown explicitly
unresolved rather than dropped or stringly; version bumped to 2.0 (1.x now
refuses, 2.x minors accepted). The TUI keeps rendering the endpoint string
in its columns.

Mechanical fallout ridden with the step (per the C3-review precedent): the
remaining internal-registration fixtures (transitions/tags/edges/soak) moved
to config-based init — retirement now happens the only way the boundary
allows, by generation-2 acceptance dropping the kind.

Evidence: `tests/work/test_resolution.py` — a full-trail sweep proving every
endpoint-establishing event carries complete snapshots; a reassignment test
proving one handler swap changes the LIVE projection while history and the
obligation row keep generation-1 handlers byte-for-byte; read-time honesty
for historical endpoints. Break-sweep: degrading include snapshots fails
both the sweep and the tags expansion test. Suite: 173 passed; test-v11
green. STOPPED for C4 review; C5/C6 held.

## C4 re-review fix — R1: + expansion moved inside the write transaction (2026-08-14)

The C4 review (`60d1f5cecee78e6061e4108b1e194090`,
`review-2026-08-14T15-23-16Z.md`) confirmed one defect, R1: `post_message`
expanded `+` selectors from `store.conn` BEFORE `Authority._write`'s
BEGIN IMMEDIATE, so a `regen` committing between expansion and the message
write produced generation-1 membership stamped with generation-2 snapshots —
complete snapshots over a stale set. The reviewer's deterministic regression
(`test_include_expansion_uses_the_generation_at_commit`) reproduced it:
gen 2 adds `web.perf` mid-flight; the committed event held only
`("web.bug", 2)` instead of both endpoints under generation 2.

Fix: wildcard membership is itself endpoint resolution, so it now resolves
at the same validate-inside-the-lock site as the snapshots. The expansion
body moved to `_expand_selectors(conn, selectors)`; `_expand_include(store,
...)` remains as the optimistic pre-lock parse (same refusals, advisory
membership — and the seam the regression's monkeypatch models the race
through), while `mutate` re-expands from the transaction connection and
derives the recorded expansion, its snapshots, and `touched_teams` from
that in-lock set only.

Break-sweep per the review: membership reverted to the pre-lock result —
the regression fails exactly as reproduced (`[('web.bug', 2)]`, missing
`web.perf`); restored, everything green. Focused C4 suites
(resolution/tags/jsonapi/parity): 33 passed. Full gate: 171 parallel +
3 serial = 174 passed, `just test-v11` green. STOPPED for C4 re-review;
the workflow-story phase stays queued behind it; C5/C6 held.

## Workflow-story phase — coverage pass + CLI/JSON workflow gate (2026-08-14)

Authorized by `37c339edbafea3c6a1f06aefc3659314` (C4 accepted; phase released
without another gate).

Deliverable 1 — the coverage/implementation pass:
`WORKFLOW-COVERAGE.md` marks every WF-01…WF-09 step EXECUTABLE /
NEEDS-OPERATION / NEEDS-RULING and sequences six missing slices (WS-1
public classification … WS-6 dossier binding). No contradictions found; the
one candidate — WF-08's history-vs-live `owed_by` split — matches the C4
implementation exactly. The known ruling gaps (WF-03 disposition semantics,
WF-09 retry ids) are confirmed from the implementation side and stay with
the reviewer. TUI parity column deferred per the authorization.

Deliverable 2 — the workflow gate: `tests/work/workflows/` — shared
subprocess driver + config builders (`wfdriver.py`, `conftest.py`), nine
workflow files, every workflow driven twice: from source (`-m
baton_work.cli`) and through the zipapp artifact with PYTHONPATH stripped.
Checkpoints assert the canonical JSON projection only; refusal checkpoints
assert byte-identical audit around the refusal; every workflow ends on the
dense-audit + one-Current/terminal-bare invariant sweep.

The workflows did their job — two defects exposed, both kept with their
stories per the workflow-to-regression rule:

1. WF-06 cycle-refusal checkpoint: the PACKAGED CLI exited 0 on every
   refusal (zipapp __main__ discards the target's return value; only the
   stderr JSON survived). Fix: `cli.entry` owns the exit status; archives
   target `cli:entry`. Regression:
   `test_packaged.test_a_refusal_exits_nonzero_through_the_archive`.
   Break-sweep: retargeting `cli:main` fails it as reproduced.
2. WF-09 race 1: respond AND dispose both committed against one obligation
   — terminal-competition checks ran only pre-lock. Fixed as a CLASS (the
   validate-inside-the-lock discipline extended to every terminal
   competitor): in-lock rechecks in create (parent open), post_message
   (status + pass already-at/consumes-Next re-derivation), close_work
   (status + open children + `was_current_*` recorded from the row AT
   COMMIT so reopen restores the truth), reopen, add_dependency (status +
   duplicate), respond, dispose. Regressions: four deterministic
   interleavings in `test_transitions.py` (`test_wf09_*`) through the
   `_write` seam — the same modeling the C4 review used. Break-sweeps:
   removing respond's recheck fails race 1; reverting the payload
   enrichment fails the was-current regression.

Design note for review: `post_message` cannot recompute the EVENT KIND
inside the lock (the kind is fixed at the `_write` call), so a pass whose
already-at/consumes-Next decision no longer matches the live row REFUSES
with a retry refusal instead of committing a mislabeled pass/return. History
therefore always equals one of the legal serials; the alternative (kind
chosen in-lock) is an `Authority._write` API change left for a ruling if
preferred.

Suite: 197 passed (194 parallel + 3 serial), `just test-v11` green — the
prior 174 plus 18 workflow runs and 5 extracted regressions. STOPPED for
workflow-gate review; heavy TUI, C5, C6 untouched.

## Workflow-gate re-review fix — reopen validates completely in the lock (2026-08-14)

The workflow-gate review (`c0361a4a9aaf2cbe4a2c338f210daf1d`,
`review-2026-08-14T15-53-09Z.md`) added two deterministic WF-09-class
regressions exposing the reopen legs my class fix left pre-lock: the
ancestry check (a parent closing after the optimistic check let a child
reopen beneath a terminal parent) and the close-event selection (a full
reopen/pass/close cycle committing before the lock made the original reopen
restore from the obsolete close event).

Fix: reopen's mutate now re-reads EVERYTHING from the transaction
connection — status, the live parent's status, and the LATEST close event —
and uses those in-lock facts for the restoration and the ancestor
recomputation. The pre-lock reads remain as optimistic early refusals only,
the same shape as every other site in the class.

Break-sweep: reverting mutate to the pre-lock facts fails both reviewer
regressions exactly as described (child reopened under a terminal parent;
stale endpoint restored). Restored: transitions 24 passed, workflows 18
passed, full gate 199 passed (196 parallel + 3 serial), `just test-v11`
green. STOPPED for re-review; heavy TUI/C5/C6 held.

## WS-1 — public classification and operational phase (2026-08-14)

Authorized by `85b35cecf67e97762bfa8538c7498ecf` against the settled rulings
in FINDING.md and the acceptance matrix in WORKFLOW-TESTS.md.

Authority/engine: `work` gains NOT NULL `classification` (canonical default
`unknown` — never null) and `phase` (default `queued`), plus
`wait_type`/`wait_obligation`; schema version 2. New transitions `classify`
and `set_phase`, both authorized by `_handler_gate` — the actor must be a
currently resolved handler of the Work's Current route, checked IN THE LOCK
with the C4 resolution snapshot recorded in the audit payload, so @ input
and mere membership never grant mutation and authority follows the baton
after `=>`. Ordinary open phases move freely (rework cycles included); a
pass never touches phase; closed work refuses both mutations; `parked`
requires a reason, keeps Current, and leaves only through explicit
parked→queued; `waiting` records exactly one typed condition (aggregate
gates — refused when no gate is open — or one exact pending @ obligation on
the SAME work) and leaves only through the wake.

The wake: `_sweep_wakes` runs at the end of every transaction that can
satisfy a condition (close, respond, dispose, and reopen for staleness),
flipping satisfied open waiters to `queued` and emitting one `wake` event
via `_emit`, which allocates the NEXT sequence number inside the same
transaction — the wake exists iff the satisfying commit does, density holds,
and a racing retry finds `queued` and wakes nothing twice.

Surfaces: CLI `--classification`/`--phase` on create, `classify`, `phase`
(--reason/--wait-on-gates/--wait-on-obligation), `summary`
(open/parked/waiting counts). Projection rows expose `phase` and
`waiting_on`; `team_summary` carries the always-visible parked count.
Bounded TUI: PHASE/CLS columns with the APPROVED compact vocabulary
(queue/rsrch/wait/actve/rview/park; unkwn), `[park:N]` on the summary line;
parity asserts TUI-compact == compact(JSON-canonical) row by row.

Evidence: `test_phase.py` (15 focused tests: defaults, authorization incl.
reassignment, round-trips, orthogonality, typed waiting, wake-at-last-gate
atomicity, wake races via the `_write` seam, in-lock already-satisfied
refusal, parking, projections). WF-01 extended (classify + research/active/
review with rework; authority follows the baton), WF-04 extended (provider
classification/phase; consumer gates-waiting whose wake rides the provider
close, seq == close+1). Break-sweeps: removing close's wake sweep, the
in-lock satisfied-gate check, and the handler gate each fail their tests as
reproduced. Gate: 214 passed (211 parallel + 3 serial), test-v11 green.

Interpretations reported for review (not decided silently): creation refuses
initial `waiting`/`parked` (they need condition/reason, so they enter only
via their explicit transitions); obligation wake conditions must name an
obligation of the SAME work; classification of closed work refuses
(symmetric with phase); compact TUI labels for the six non-`unknown`
classifications are unruled — rendered as mechanical 5-cell truncation
pending vocabulary confirmation. STOPPED for WS-1 review; heavy TUI/C5/C6
held.

## WS-1 re-review fixes — R1-minimum, R2, R3, R4 (2026-08-14)

Per review `e316f26a22c2c17fe0aa4a7e7a2f1210`
(`review-2026-08-14T17-59-02Z.md`). R1's complete operation matrix and R5's
compact classification vocabulary stay HELD for Slawomir; nothing was
implemented around them.

R1 (pinned minimum): `_handler_gate` now guards the `=>` pass leg of
post_message and terminal close_work, in the lock, recording the
authorization snapshot as `payload["authorization"]`. An @ respondent can no
longer pass or close the requester's Work; both reviewer regressions pass.
Consequence made visible by WF-09's race: after a pass wins, the racing
close by the FORMER handler now loses on ownership — exactly one racing
terminal action commits in either serialization, and the workflow asserts
that stronger property (the new handler then closes deliberately).
Mechanical fallout: the deterministic race regressions' interleaved actors
switched from grace to the authorized ada over a second connection.

R2: `projection.detail` computes availability from the SAME live
route/handler resolution the authority enforces: pass/classify/set_phase/
close are handler-only (set_phase absent while `waiting` — it leaves only
through the wake; close still needs clear gates); post/request/dependency/
mark_seen stay participation-based pending the R1 matrix ruling; the
reviewer regression proves authority follows `=>` in the projection too.

R3: `home` is now ONE projection carrying `{summary, rows}` — the parked/
waiting counts and the table are the same snapshot; the TUI's top level
consumes exactly that projection (no second call to skew), and a new parity
regression parks a work and holds `[park:1]` equal to the JSON summary.

R4: WF-04 executes the phases its prose claimed: research → review →
active → review beside the passes, asserting after every pass that the pass
itself changed nothing, with the full audited phase trail checked.

Break-sweeps: stripping the pass/close gate fails the reviewer's @-authority
regression; reverting home to a bare list fails the projection/envelope
regressions. Gate: 217 passed (214 parallel + 3 serial), test-v11 green.
STOPPED for re-review; R1-matrix + R5 vocabulary await Slawomir; heavy
TUI/C5/C6/WS-2 held.

## R1 complete authority matrix + R5 classification vocabulary (2026-08-14)

Authorized by `c20a3690e9f7fbb4c98665331fd2829c` against the pinned rulings
in FINDING.md ("complete Work authority matrix and classification labels").

R1, the matrix in full — every workflow decision now runs through the live
route-to-handler resolution inside the committing transaction, with the
authorization snapshot recorded in the payload:
- `@` obligation creation (post_message request leg), dependency changes
  (add_dependency), and child attachment (create_work with a parent) join
  pass/close/classify/set_phase under `_handler_gate`;
- reopen resolves the Current it RESTORES (from the in-lock latest close
  event) and requires the actor to be that endpoint's live handler;
- respond/dispose require a resolved handler of the route the obligation
  names (`_obligation_gate`) — answering grants nothing else;
- contribution, `+` attention, own seen state, and open-graph reads remain
  participation operations, untouched.
Projection: `available_transitions` mirrors the whole matrix — request/
pass/add_dependency/create_child/classify/set_phase(+close) are
handler-only; a closed work offers `reopen` exactly to the live handlers of
the endpoint reopen would restore; participants keep post_message/mark_seen.

R5: `CLASSIFICATION_COMPACT` is the ruled closed map (unkwn/suspt/cnfrm/
limit/dupe/desgn/rejct); both compact lookups now FAIL VISIBLY on unmapped
canonical values — no label is ever invented by truncation.

Fallout: the WF-09 obligation race (workflow + deterministic regression)
now races respond vs dispose as the SAME authorized handler over two
sessions — grace's dispose would lose on ownership before the race could
happen, which is the matrix working as ruled.

Evidence: four new focused regressions (full-matrix gating, obligation-
route answering, matrix-mirroring available_transitions incl. reopen
visibility, closed-and-complete vocabulary). Break-sweeps: stripping the
new gates fails the matrix regressions; reintroducing truncation fails the
vocabulary regression. Gate: 221 passed (218 parallel + 3 serial),
test-v11 green. STOPPED for review; heavy TUI/C5/C6/Gate B/WS-2 held.

## WS-1 re-review 2 fixes — contribution ACL, availability mirror, one snapshot (2026-08-14)

Per review `bb99cacc83a94dff4771ae623629c7f9`
(`review-2026-08-14T20-33-18Z.md`); all four reviewer regressions kept
additive and passing.

R1 (contribution): post_message's participation barrier is GONE — any
configured member may post ordinary/`+` discussion on open Work, and the
committing transaction records their team as a durable participant
(touched_teams includes the author's team). Owner gates untouched — the
regression proves chipping in still cannot close. The old
barrier-pinning test in test_tags was rewritten to the ruled contract;
availability now offers post_message/mark_seen to every configured viewer
of open Work.

R2 (availability mirrors the writer): `close` is hidden only by open
CHILDREN — an open blocker gates readiness, never an honest terminal
close (the stale projection assertion replaced per instruction); `reopen`
is offered only when the closed parent rule also passes (ancestry open),
matching the writer's refusal exactly.

R3 (one snapshot): `home` reads rows, summary, and its sequence inside one
BEGIN…ROLLBACK read transaction — a writer committing mid-read changes
none of them — and the envelope's `snapshot_seq` for home is the seq
observed INSIDE that snapshot (envelope accepts the projection-supplied
value). Read purity preserved: nothing inserts, updates, or commits; the
boundary guard was updated from "no BEGIN" to "never
INSERT/UPDATE/DELETE/COMMIT, and every BEGIN has its ROLLBACK" — the old
formulation forbade the very snapshot the ruling now requires.

Break-sweeps: restoring the participation barrier fails the contribution
regression while the owner-gate regression stays green; re-gating close on
blockers / dropping the parent-open check fails the two availability
regressions; removing the read transaction fails the torn-snapshot
regression. Gate: 225 passed (222 parallel + 3 serial), test-v11 green.
STOPPED for re-review; heavy TUI/C5/C6/Gate B/WS-2 held.

## WS-2 group 1 — immutable closure, universal outcomes, follow-up (2026-08-14)

Preceded by the required adversarial pass (WS2-DISPOSITION.md) and the
options round (WS2-OPTIONS.md); implemented only after the explicit release
(`ddb963d4abe43c41d455466a19c3043e`) pinned the rulings: universal terminal
outcomes; derived-only due; verification-as-@ but never a wake condition;
new blockers target only open Work; the precise closed-Work rule.

Authority (schema v3): `work.outcome`, `work.follow_up_of`. `reopen_work`
is GONE — verb, engine, projection availability, wake-sweep hook, and every
refusal message that advised it (closed work now points at follow-up work).
`close_work` requires exactly `satisfying|non-satisfying`, recorded on the
row and in the event; the row keeps `was_current_*` history in the close
event only. `add_dependency` refuses closed blockers pre-lock AND in-lock.
`create_work` takes `follow_up_of`, valid only against terminally closed
predecessors (pre-lock + in-lock), non-gating, exposed in rows and
navigable from both sides in `links` (with the predecessor's outcome).
Closed availability is [] for everyone; links far-summaries carry outcome.

CLI: `close --outcome` required; `create --follow-up-of`; `reopen` verb
removed (unknown-verb refusal changes nothing, proven in-story).

Superseded surfaces replaced per the PLAN authorization: the four reopen
unit tests, the two reopen in-lock race regressions, WF-05/WF-06 reopen
legs, the closed-blocker-gates-nothing test (now: refuses), the soak's
reopen branch (now: follow-up creation), and the closed-detail
`["reopen"]` assertions (now: `[]`). ~60 close sites across the suites
gained explicit outcomes.

New evidence: `test_ws2_close.py` (7 focused: canonical-outcome refusals
and recording; either outcome ends the gate atomically — wake seq ==
close seq + 1 — waking last-gate waiters, holding multi-gate waiters, and
mutating no consumer; the closed-work refusal sweep with byte-identical
audit and mark_seen retained; no reopen surface anywhere; follow-up
closed-only/non-gating/navigable; two mid-flight races). Stories
`test_ws2_wf05.py` (non-satisfying close returns the decision — visible,
actionable, never "fixed") and `test_ws2_wf06.py` (immutable close, refused
contradiction, selective follow-up with new explicit edges; old history
byte-unchanged by the follow-up's own close), both source+packaged.

Break-sweeps: outcome-optional fails the canonical-outcome test; allowing
closed blockers fails both edge guards; removing BOTH follow-up target
checks fails the closed-only test (one layer alone is covered by the
in-lock recheck — defense in depth verified deliberately). Gate: 230
passed (227 parallel + 3 serial), test-v11 green. STOPPED for group-1
review; groups 2 (rounds) and 3 (due/races/parity) not started.

## WS-2 group 1 correction — withdrawal at close, DEP, R2 fix (2026-08-14)

Authorized by `00d315b9e45f638c221f1cc4d7303141` (Slawomir resolved the
blocker).

R1: terminal close now atomically WITHDRAWS every pending exact @
obligation the closing work carries — status `withdrawn`, one audited
`withdraw` event per obligation inside the closing transaction, each
carrying the route accountability recorded at creation (endpoint, route,
role, handlers, generation). Late answers refuse in-lock ("already
withdrawn"); answer-versus-close serializes both ways (close-first: the
answer refuses and closed history gains nothing; answer-first: the close
keeps the committed response and withdraws nothing) — both serializations
pinned by deterministic `_write`-seam races. The reviewer's additive
regression passes.

DEP (ruled): projection rows expose `dep` — the count of OPEN work
currently depending on this one — and the `links.blocks` drill lists only
that live set; a consumer's closure removes it from both without deciding
anything on the provider, while the journal retains every edge act.
(TUI rendering of DEP is left to group 3's bounded parity pass.)

R2: the ineffective follow-up interleave test was corrected to its honest
claim — the open-target refusal fires at the precheck, and under immutable
closure the in-lock recheck is defense in depth (proven wired by the
two-layer break-sweep), not a live reverse race.

Break-sweeps: removing the withdrawal block fails the reviewer regression
and the visibility regression; counting all dependents fails the DEP
regression. Gate: 234 passed (231 parallel + 3 serial), test-v11 green.
STOPPED for re-review; groups 2 and 3 not started.

## Group-1 re-review fixes — withdrawal address, detail snapshot (2026-08-14)

Per `b72692c7a4a77a272230349f109a7026`
(`review-2026-08-14T22-09-07Z.md`); both mechanical, no ruling needed.

R1: each withdrawal's `resolved_seq` now addresses its OWN `withdraw`
event (allocated by `_emit` in the same closing transaction), never the
enclosing close whose payload does not name the obligation; multiple
withdrawals each carry their own address.

R2: `detail` reads everything — DEP counter, live drill, links, New,
availability, and its own `snapshot_seq` — inside one BEGIN…ROLLBACK read
snapshot following `home`'s pattern; a consumer close racing the reads
appears wholly before or wholly after, never torn. Purity preserved (the
hash-sweep purity test covers detail).

Both reviewer regressions pass; break-sweeps red (close-addressed
resolved_seq fails the address regression; unwrapping detail fails the
snapshot regression). Gate: 236 passed (233 parallel + 3 serial),
test-v11 green. STOPPED for re-review; groups 2 and 3 not started.

## WS-2 group 2 — candidate rounds and staged verification (2026-08-15)

Authorized by `f38f8cf2a6fc88dba07c0cb9970903d5`; group 3 (due/review_at,
fault/race/restart matrix, renderer parity) untouched.

Authority (schema v4): obligations gain `flavor`
(response|verification), `round`, `observation`, `evidence`; new `rounds`
(work-scoped ordinal, immutable candidate, open|superseded|abandoned|
closed) and append-only `assessments` tables. An assignment IS a flavored
exact @ obligation (the accepted mapping): same identity, cardinality,
snapshot columns, actionable projection, and named-route-handler gate —
completed only by `report`, never by respond/dispose, never a wake
condition, and it transitions nothing.

Transitions, all Current-handler gated in-lock with recorded
authorization: `create_round` (exact candidate required; exact selection —
wildcards and duplicates refuse; an open round is superseded and its
pending assignments withdrawn with route notification, one audited
`assign` event per assignment carrying its resolution); `report`
(immutable raw passed|failed|unable + evidence, pinned to
assignment/round/candidate; second report and late report refuse in-lock);
`assess` (accepted|rejected|inconclusive + rationale, append-only;
reassessment is a superseding act; requires a returned report — assessment
never invents feedback; reporters cannot assess); `abandon_round` (round
ends, work untouched, pending withdrawn+notified). Work close now closes
open rounds and the shared `_withdraw_pending` sweeps ALL pending
obligations, both flavors.

Projection: `detail` carries `rounds` inside its one read snapshot — per
round: immutable candidate, status, assigned/reported/pending/withdrawn,
`reported/assigned` progress (receipt, never support), and per-assignment
route/state/raw observation/evidence/effective assessment/full assessment
history — both axes side by side (`failed / rejected`). Obligations
projection exposes flavor. CLI verbs: round, report, assess, abandon.

Evidence: `test_ws2_rounds.py` (9 focused: pinning+cardinality, report
immutability and nothing-transitions, route-handler-only reporting and
wake ineligibility, append-only adjudication, supersession keeping pinned
reports at 1/2 while round 2 starts 0/1, abandon at 1/3 + 2 withdrawals,
close ending rounds and assignments, generation-2 authority following
config without rewriting snapshots). Stories WS2-WF-07 (subset of five:
round total 2, outsider contribution readable but counter untouched,
outcome fans through all five edges) and WS2-WF-08 (abandon without
closing; byte-identical refusals for late reports; new candidate = new
round), both source+packaged.

Break-sweeps: supersession without withdrawal, delete-then-insert
assessments, and an ungated report each fail their regression. Gate: 249
passed (246 parallel + 3 serial), test-v11 green. STOPPED for group-2
review; group 3 not started.

## Group-2 re-review fixes (2026-08-15)

Per `9faea62ea0a8b75fcb5ef13e4a6b6589`
(`review-2026-08-15T03-09-41Z.md`); all four within approved semantics.

1. respond/dispose now refuse verification assignments outright — the
   flavored subtype completes only by report or withdrawal, so no
   unprojectable responded/disposed assignment state can exist.
2. The report act records the exact candidate identity and the evidence
   reference in its own immutable payload — the audit contract, not a
   join over mutable tables.
3. A reassessment names the assessment it supersedes
   (payload["supersedes"], resolved in-lock from the append-only chain).
4. `detail` declares `create_round` to the eligible Current handler on
   open work, and `abandon_round` exactly while an open round exists.

All four reviewer regressions pass; four break-sweeps red. Gate: 253
passed (250 parallel + 3 serial), test-v11 green. STOPPED for re-review;
group 3 held.
