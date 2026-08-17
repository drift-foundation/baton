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

## WS-2 group 3 — due review, extension, close evidence, final battery (2026-08-15)

Authorized by `cf27b75c5c5c6e7ec1c8b5acf2a4bae8`; completes WS-2.

Derived due (schema v5): rounds carry optional `review_at` (UTC ISO,
lexicographic order — no timezone can reorder it) and a
`deadline_generation`. Due-ness is a PURE function of the stored instant,
the deadline generation, and an injectable clock (production: UTC wall
time; `BATON_WORK_NOW` is the documented deterministic seam for subprocess
stories). No scheduler, no timer audit row, no read mutation — due is
idempotent across reads and restarts and visible as an always-visible
`due` count in the team summary (the parked treatment), the round view,
and the `[due:N]` TUI header. A deadline born expired refuses. Reaching T
transitions nothing.

Audited extension: `extend_round` (CLI `extend`) moves the SAME
candidate's window strictly forward (and may give a deadline to an
undated round), advances the deadline generation, retains every report
and pending assignment, and is refused to non-handlers — repeated
extensions are visible history, never a hidden timer reset.

Close evidence: a close concluding an open round audits, in the close
event, the round, candidate, `reported/assigned`, the raw observation
tally, review_at + generation, the created→closed exposure window, the
pending assignments being withdrawn, and the reviewer's basis — recording
the judgment's basis without fabricating feedback (the 0/N branch records
zeros honestly).

Stories WS2-WF-01..04 implemented (satisfying single-verifier close;
three mixed reports with failed/rejected two-axis adjudication and
supersession; due/silence/extension/withdrawal with the clock seam
including the 0/3 branch; failed candidate → explicit resume →
replacement round → close auditing the concluded round). Focused matrix
completed in `test_ws2_due.py` (13): boundary determinism, no-transition
due, extension semantics, discretion/close evidence, extension-vs-close /
report-vs-abandon / assessment-vs-close / new-round-vs-abandon races,
whole-or-nothing fault injection at every write boundary of the closing
transaction (byte-hash + dense sequence at each fault), and full restart
reconstruction. Bounded renderer parity: the TUI round line distinguishes
due/pending/reported/withdrawn and shows observation/assessment as
separate axes, value-equal to the canonical projection (PTY test).

Break-sweeps: non-derived due, non-advancing generation, summary-less
close, and merged TUI axes each fail their regression (the TUI sweep was
re-run after a first no-op application — verified genuinely red).
Final battery: all 18 workflows × 2 modes = 36 passed; full gate 277
passed (274 parallel + 3 serial); test-v11 green. WS-2 COMPLETE —
STOPPED for final review. Migration, deployment, heavy TUI navigation,
C5/C6 untouched.

## Group-3 re-review fixes — R41-R45 (2026-08-15)

Per `5e04534a4d15c047a43b2ee5028c0662`
(`review-2026-08-15T03-57-22Z.md`).

R41: `_canonical_instant` — one shared boundary refusing anything that is
not a real UTC instant in exactly YYYY-MM-DDTHH:MM:SSZ (strptime + exact
round-trip; impossible dates and offsets refuse pre-write, consuming no
round, act, or sequence).

R42: create_round and extend_round recheck the deadline against ONE
transaction-local sampled instant inside the committing write (also used
as created_ts) — a deadline passing between optimistic check and lock can
no longer commit born-due. Every canonical read response samples the
clock once: detail passes one instant to all round views, home to its
summary, obligations to its due predicate — a boundary crossing cannot
make counts, details, and locators disagree within one response.

R43: the due alarm has its LOCATOR — `obligations` now carries one
derived `due_round` entry per live deadline generation (work, round,
candidate, review_at, generation, live responsible endpoint), appearing
exactly at/after the deadline, following accepted Current changes, and
vanishing on extension/abandon/supersession/close. Purely derived.

R44: `wait_actionable` + CLI `wait --timeout` — the smallest read-only
wait: immediate on actionable work, otherwise polling the pure projection
(≤50ms granularity) until the nearest deadline crosses or the timeout
expires; zero mutation (event-identical before/after, tested). Covered:
immediate, quiet timeout, deadline wake, competing-message commit from
another session, extension/abandon/close quieting, restart. WF-03 gained
CLI-level wait checkpoints (quiet before T, locator at T).

R45: the race matrix completed BOTH orders — extension-vs-close
(ext-first: both commit, the concluded round records the extended
window), report-vs-abandon (report-first retained, zero withdrawals),
assessment-vs-close (assessment retained), new-round-vs-abandon
(abandoned round never relabeled, no duplicated withdrawal) — plus the
two-report race (exactly one commits, evidence unoverwritten) and the
STATED public retry limitation: without operation ids, retrying a
completed mutation is refused structurally with zero duplicate effects;
callers read before retrying.

Break-sweeps red for all four new guards (canonical boundary, in-lock
deadline recheck, due locator, blocking wait). One mechanical fallout:
the home-snapshot regression's monkeypatch wrapper forwards the new
sampled-now kwarg. Final battery: 36 workflow runs (18 × source+packaged);
gate 294 passed (291 parallel + 3 serial); test-v11 green. STOPPED for
re-review; later phases held.

## Group-3 re-review 2 — R46 one-snapshot actionable/summary/wait (2026-08-15)

Per `c8b8bafd46d26b06511cacca880b8589`
(`review-2026-08-15T04-10-52Z.md`).

A reentrant `_read_snapshot` (BEGIN…ROLLBACK, joining any snapshot the
caller already holds) now pins every Group-3 canonical response to ONE
database state alongside its one sampled instant:

- `obligations` reads pending rows, endpoint resolutions, and the derived
  due locators inside the snapshot and returns a `Snapshotted` list whose
  `snapshot_seq` was read INSIDE it — the CLI envelope uses that token, so
  the consistency token can never name a state later than the payload
  (list result shape preserved for every existing caller).
- `team_summary` derives all four counts, the due count, and (on
  top-level calls) its token from one snapshot; embedded calls (home)
  join the caller's snapshot and carry no separate token.
- `wait_actionable` returns each response with the winning read's token.

The reviewer's R46 regression now returns the wholly-before view; two new
coherence regressions added as required: the envelope-token test (a commit
interleaved during the read cannot relabel old rows with a newer
sequence) and the summary-tear test (a parked-work commit between count
statements cannot half-update the summary). Break-sweep: neutralizing the
snapshot helper fails the tear and summary regressions as reproduced.

Mechanical fallout: the home-summary equality assertion accounts for the
top-level token. Gate: 297 passed (294 parallel + 3 serial), test-v11
green; the 36-run workflow battery unchanged and green. STOPPED for
re-review; later phases held.

## WS-3 — atomic provider acceptance (2026-08-15)

Authorized by `08f4922a26a7dc55a0f606a65cb640cd` against the five pinned
dispositions and R47/R48.

Engine (schema v6: `edges.via_obligation`, `obligations.accepted_into`):
`accept_obligation` (CLI `accept OBLIGATION --body … [--into W | --create
--kind K --title T [--classification] [--phase] [--parent]]`) — ONE
transaction commits or refuses whole: the ruled narrow grant checked
in-lock (the pending exact @'s live route handler; snapshots recorded);
for --into, same-team + open provider checks with the provider Current
recorded as tolerant EVIDENCE, never a gate (disposition 2); for
--create, the provider Work born AT the accept's own sequence (R48 —
the primary accept act doubles as the creation record, provider first
message at the same seq), with the separate live parent-Current handler
gate exactly when --parent is used (disposition 5); the obligation's
ruled terminal `accepted` state addressed to the act and naming the
provider; the provenance edge (self/duplicate/cycle/open-blocker checks
in-lock; a refused cycle rolls back the created Work); the rationale
answered into the consumer's discussion as its own ordered audited act;
readiness recomputation; and the R47 wake — the exact-obligation waiter
queues with readiness held false by the new gate, gates-waiters sleep on.

Projections: links.blocked_by/blocks entries carry `via_obligation`;
actionable entries declare `completes_by` (respond/dispose/accept for
response flavor, report for verification); DEP and one-snapshot semantics
inherited unchanged.

Evidence: `test_ws3_accept.py` (14 focused: whole-effects + exact audit
ordering for both forms; the grant incl. generation-2 movement; same-team/
open/into refusals; the separate parent gate; R47 both ways; a refusal
sweep committing nothing incl. verification-flavor; double-accept race
minting no orphan; accept-vs-consumer-close and accept-vs-provider-close
races; accept-then-dispose and the stated retry boundary; fault injection
at every write boundary of the create form; restart). Stories WS3-WF-01
(PushCoin→Drift first report: declared completes_by, non-handler refusal,
atomic accept, wake-but-not-ready, noise scoping, terminal fanout) and
WS3-WF-02 (three-consumer convergence: per-edge provenance, DEP 3→0,
byte-identical duplicate refusal), both source+packaged.

Break-sweeps: removing the edge half, the terminalization half, or the
in-lock pending recheck each fails its regression (association without
gate; gate without answer; orphan provider). Gate: 315 passed (312
parallel + 3 serial); all 40 workflow runs green; test-v11 green.
STOPPED for review; WS-4/5/6, migration, C5/C6, TUI held.

## WS-3 re-review fixes — R49-R53 (2026-08-15)

Per `e0f2f2f54d0245c820f3a5a34b9dc5e0`.

R49: the accept result carries the ruled structured `edge` member, and
the accepted association is PUBLIC structured state — `detail` now lists
the work's obligations (seq, endpoint, flavor, status, accepted_into,
resolved_seq) inside its one-snapshot read, so any agent determines
"obligation N is accepted into W" without SQL or audit mining; the
restart regression reads it back through the projection only.

R50: the CLI forms fail closed — `--into` refuses every creation option
by name before any state opens; `--create` requires --kind and --title.

R51: `accept --create` uses None-only defaults exactly like ordinary
creation; explicit empty classification/phase strings refuse instead of
normalizing to `unknown`/`queued` (invalid phases outside the enum also
refuse before the creation-phase restriction).

R52 (schema v7): `edges.via_obligation REFERENCES obligations(seq)` and
`obligations.accepted_into REFERENCES work(id)`; adversarial evidence:
garbage references refuse at the database, ordinary block edges keep
NULL, respond/dispose never set a provider.

R53: the matrix completed — accept-first orders for consumer close
(both commit, no false withdraw), provider close (fan-out), and config
change (snapshot preserved); dispose-first refusing the accept without
orphans; the regen-mid-accept race deciding in-lock under the new
generation; concurrent accepts of two DIFFERENT obligations into one
provider both committing (DEP 2); fault injection for the --into form;
public-projection restart reconstruction.

All three reviewer regressions pass. Gate: 326 passed (323 parallel + 3
serial); all 40 workflow runs green; test-v11 green. STOPPED for
re-review; later phases held.

## WS-4 Slice A — first-class discussions (2026-08-15)

Authorized by `acaebcdaf67ce31cac6cfba4f34c1f3f` after the required
red-team pass (WS4-DESIGN.md notes RT1-RT9: one supersession — the WS-1
team-participation gate in New — justified against the pinned
member-relative ruling; no contradiction or missing decision found).

Schema v8: `discussions` (born labelled and speaking, id {uuid8}-D{seq}),
`messages.discussion` (one message, one discussion), FK-bound inert
`discussion_labels`, monotonic `discussion_participants` (replacing
work_participants), per-member per-discussion `seen`. All Work-local
containers gone; fresh schema, no migration (nothing deployed exists).

Engine: `create_discussion` (≥1 authorized own-team label, ≥1 OPEN —
live-context in-lock; first message atomic), `label_discussion` /
`unlabel_discussion` (D1 owning-team gate both ways, duplicate/absent
refuse, FINAL label never leaves, terminal Work labelable, all in-lock),
`post_discussion` (open to every configured member; live context
rechecked in-lock; author team joins monotonically), `seen_discussion`
(the canonical monotonic cursor). Internal Slice-A bridge, marked for
Slice B removal: Work-addressed writers (post/respond/accept/create)
route to the derivable BORN discussion (shared created_seq — no stored
primary, R54); Work-addressed mark-seen advances every labelled
discussion's cursor. Work creation and accept --create birth their
discussions in the same transaction.

Projections: `thread` (labels w/ team+status, participants, paginated
messages, viewer New, one snapshot + token), `discussions_for` (the R56
participating surface incl. @/=>-joined teams), Work `detail` gains its
DISCUSSION SET summaries (id, last_seq, viewer New — never merged, R54),
and `new_count` is the R57 decomposition: member-relative distinct
counting with own/children/overlap/total and the exact identity
total = own + Σchildren − overlap. `discussion(work)` remains as the
born-only internal bridge read.

CLI: discuss, say, label, unlabel, thread, discussions, read.

Evidence: `test_ws4_discussions.py` (13 focused: birth atomicity,
creation refusals, D1 both ways, full inertness sweep, final-label,
live-context incl. the mid-post close race in-lock, overlap identity
with clear-once-everywhere, per-member cursors + bridge coverage,
monotonic participation surface, label/unlabel races, whole-or-nothing
fault injection through creation, restart + purity hash). WF-06 extended:
the shared discussion labelled to both children proves visible overlap
and single-read clearing through the public CLI, source+packaged.
~10 older tests migrated mechanically to the new schema; RT9's
superseded assertion rewritten with justification.

Break-sweeps: a label that touches readiness, a zeroed overlap, a
dropped in-lock live-context recheck, and a dropped final-label refusal
each fail their regression. Gate: 344 passed (341 parallel + 3 serial);
all 40+2 workflow runs green; test-v11 green. STOPPED for Slice A
review; Slice B (operators/--on/acceptance labelling), WS-5/6,
migration, C5/C6, TUI held.

## Step 25 — WS-4 Slice A correction round R61–R66 (2026-08-15)

R61: the read-named mutation is gone — the ONE public seen mutation is
`mark-seen DISCUSSION --up-to`; `read` and the Work-addressed
`discussion WORK` verbs are removed from the packaged parser (the R60
bridge stays library-internal, Slice-B-removal marked). All five
workflow stories that certified the bridge surface (WF-02/06/07/09,
WS3-WF-01) now speak thread/mark-seen/work-discussions.

R62: `seen_discussion` is bounded by the OBSERVED authority sequence
(a future cursor refuses), revalidates member + cursor inside the
committing transaction, and a losing/idempotent mark returns the
committed cursor via `_NoAdvance` with NO audit event. Both reviewer
regressions in `test_ws4_review.py` pass.

R63: pagination is a contract — `_page_bounds` (non-negative cursor,
limit 1..500), explicit `next_after` continuation on `thread`,
`discussions_for`, and the new paged `work-discussions` projection+verb;
detail's discussion preview is bounded; total tie-break order is
(added_seq, identity) for labels, participants, and both list
directions. New: focused bounds/ties/multi-page tests and the
WS4-WF-01 story (same-sequence label + participant ties, 3-direction
page walks without skips or repeats, CLI refusals) in both modes.

R64: `new_count` runs whole inside `_read_snapshot`, keeps `id`, and
returns the snapshot's own token. New interleaved-writer regression: a
message committing mid-decomposition is invisible to own/children/
overlap/total AND the token, then fully visible to the next read.

R65: `_member` requires removed=0; every new mutation revalidates
`_member_active` in-lock; `label` records `work_status` from the
committing transaction. New both-order config-generation races: the
mid-flight removal refuses all five mutations whole (parametrized), the
act-first order keeps history and refuses the next act at the door, and
the close-then-label race audits status "closed".

R66: WS2-WF-04 reordered exactly as pinned — research, active,
candidate A, review, failed feedback, active rework, candidate B,
review, successful feedback, explicit close — and now asserts the full
audited interleaving (set_phase/create_round/report/assess/withdraw/
close_work with per-event evidence), not merely the phase subsequence,
in both modes.

Break-sweeps (defect in, red, restored): future-cursor bound (both
sites), in-lock losing-race recheck, `_member_active` in post,
pre-lock work_status, unwrapped new_count snapshot, dropped
`_page_bounds`, inverted label tie order. Note: merely DROPPING the
tie-break is masked by the PK index's storage order, so the sweep
proves the pinned contract with a wrong-total-order defect instead.

Gate: 359 passed (356 parallel + 3 serial); all workflows green in
source and packaged modes; test-v11 green. STOPPED for re-review.
Slice B, WS-5/6, migration, deployment, C5/C6, TUI expansion held.

## Step 26 — WS-4 Slice A correction round R67–R68 (2026-08-15)

R67: relation pages cursor by RELATION addition, not discussion birth.
`discussions_for` orders/filters/pages by
`discussion_participants.added_seq` and `work_discussions` by
`discussion_labels.added_seq` (identity tie-break kept); each row now
carries `added_seq` and `next_after` returns that relation sequence, so
a team joining old context — or old context gaining a new label — after
a cursor has advanced is discovered by the very next incremental page,
exactly once. Work detail's preview shares the label relation order and
reports truncation EXPLICITLY: `discussion_count`,
`discussions_truncated`, and `discussions_next_after` (a continuation
cursor that hands off to `work-discussions` without gap or repeat).

R68: no invalid request is a secret alias for 500 — `thread`'s function
and CLI defaults are the legal 500 and every supplied limit reaches
`_page_bounds` unchanged; an explicit 1000 refuses.

Evidence: both new reviewer regressions pass; WS4-WF-01 extended with
the pinned source+packaged scenario in both relation directions (page
one read, old discussion gains the relation, next page discovers it
exactly once, following page proves no repeat) and the exact
`--limit 1000` case in the refusal matrix; new focused preview
regression (53 labels: count 53, 50 shown, truncated flag, cursor
handoff finds the remaining 3 once; the untruncated shape says so).

Break-sweeps (defect in, red, restored): birth-cursored work page,
reintroduced 1000→500 clamp, silent preview truncation.

Gate: 362 passed (359 parallel + 3 serial); all workflows green in
source and packaged modes; test-v11 green. STOPPED for re-review.
Slice B and later phases held.

## Step 27 — WS-4 Slice A ACCEPTED (2026-08-15)

Reviewer accepted Slice A (message c191497497ffa1430d5a91dab8d21c16,
review-2026-08-15T10-22-12Z.md): R61–R68 satisfied, no Slice A finding
remains. Slice B (carrying operators/--on/acceptance labelling), WS-5,
WS-6, deployment, and TUI expansion remain HELD pending explicit
release.

## Step 28 — WS-4 Slice B: public operators, binding, acceptance labelling (2026-08-15)

Slice B implemented per the released plan section; schema v9.

Public discussion-addressed operators: `say DISCUSSION` now carries
`--include`, `--request`, `--pass-to`, `--set-next`, and `--on`. An
`@`/`=>`/planned-Next acts on exactly ONE currently labelled, eligible
open Work (D2/R55/D9): explicit `--on` must name a current label and
that Work must be open and authorized; omitted `--on` resolves only at
eligible-cardinality one (foreign/unauthorized labels create no false
ambiguity — eligibility runs the operation's existing handler gate),
recorded and echoed (`on_resolved`). The selection is RE-DERIVED inside
the committing transaction: a mid-flight unlabel, close, or newly
eligible second label refuses whole (WF-09-style race guard). Closed
Work refuses carrying activity with its own message; plain commentary
needs only live context (in-lock, unchanged).

`+` stays the only fan-out: expanded in-lock against live endpoints,
the exact expansion recorded, each reached team joining monotonic
participation once — provably no obligation, Current, Next, readiness,
phase, edge, or Work-row change.

Obligation binding (R59): `obligations.discussion` (schema v9, FK)
records where every `@` was raised; `respond` answers into that
originating discussion; participation persists after the obligation
terminates; label removal never cancels; `obligations` and `detail`
projections name the discussion.

WS-3 acceptance reconciled (D5): grant, terminal accepted state, edge +
`via_obligation`, readiness, R47 wake, and audit order preserved; the
rationale now returns to the ORIGINATING discussion, which atomically
gains the `#PROVIDER-WORK` label — collision-safe, audited
`provider_label: added|existing`, never a duplicate row. The gate stays
the edge: dropping the label changes no readiness/DEP (regression).

Bridge removal: `transitions.post_message`, Work-addressed `mark_seen`,
`projection.discussion`, and the CLI `post` verb are GONE — no alias;
the boundary test proves `post` no longer parses. The bounded TUI now
reads `work_discussions` + `thread` and marks the displayed discussion
seen via the public transition. Test-only adapters (born-discussion
lookup, story shorthand over work-discussions+say) live in test
fixtures/wfdriver and compose public calls only.

Stories: WF-05 rewritten to the pinned convergence — each consumer asks
`@lang.bug` IN its discussion, Lang accepts each into ONE record, every
originating discussion gains `#LANG-42` with the rationale answered
there, DEP=3, and the label-versus-edge proof lands (unlabel: ready/DEP
unchanged). WF-07 announcement, WF-06 dedup, WS2-WF-04 cycle preserved
under the new grammar; every workflow and CLI test migrated off the
bridge surface (wf01–09, ws2, ws3, scenario, packaged, jsonapi,
boundary, soak, TUI/parity).

New focused suite `test_ws4_operators.py` (18): omitted-`--on`
resolution + echo, two-eligible refusal + explicit selection, exact
refusal matrix (outside-labels, operator-less `--on`, wildcard, double
operation, next-without-pass, zero-eligible), closed-context carrying
vs commentary, include inertness byte-compare + dedup, respond return
path + persistence + projection naming, acceptance added/existing +
create form + gate-is-the-edge, both-order races (mid-flight unlabel /
close / second-eligible; accept-vs-consumer-unlabel; reverse orders
incl. close-withdraws-pending), whole-or-nothing fault injection
through carrying post and labelling acceptance, restart + retry
boundary.

Break-sweeps (defect in, red, restored): S1 pre-lock-trusted selection
(all three mid-flight races bite), S2 gate-free eligibility (false
ambiguity + unauthorized resolution bite), S3 unbound obligation, S4
non-collision-safe label insert, S5 skipped acceptance label.

Future rulings pinned mid-slice and journaled in FINDING.md (all HELD):
cancellation as atomic close `cancelled` by Current; the four-outcome
close vocabulary + `duplicate_of` + WF-10 spec (reviewer updated
WORKFLOW-TESTS.md); revision as promotion of one durable discussion
message via external versioned templates.

Gate: 380 passed (377 parallel + 3 serial); every workflow green in
source and packaged modes; `just test-v11` green; `git diff --check`
clean. STOPPED at the review gate. Work revisions, cancellation,
WS-5/WS-6, deployment, and TUI expansion held.

## Step 29 — Slice B correction round R69–R71 (2026-08-15)

R69: Work detail no longer advertises `post_message`/`mark_seen` — no
Work-addressed alias survives the bridge removal; the open contribution
right is proven by the act, not an advertisement. The one WS-1-era test
pinning the old advertisement is rewritten with the supersession noted.
Story coverage: WS4-WF-01 asserts the absence through source and
packaged JSON.

R70: the bounded console retains the PAINTED thread snapshot's
last-message sequence and marks exactly that — never a later global
`last_seq()` read at keypress time; a message committed after paint
stays New. Companion regression proves painting stays byte-pure and
the bounded mark clears exactly the painted snapshot.

R71: the landing rule applies to EVERY individual `+` selector,
wildcard shapes included, both optimistically and under the committing
generation — `ghost.*`, `*.ghost`, and mixed lists refuse whole with
message/event/sequence untouched; a config race that empties a
previously matching wildcard refuses in-lock. Story coverage: WF-07's
announcement refusal matrix gains all three shapes in both modes.

Evidence: all three reviewer regressions pass (7/7 in
test_ws4_review.py); focused operator suite grown to 21; break-sweeps
for each guard (readvertised bridges, keypress-time global mark,
exact-only landing rule) each fail red and were restored. Gate: 386
passed (383 parallel + 3 serial); every workflow green in source and
packaged modes; `just test-v11` green; diff check clean. STOPPED for
re-review. Later slices held.

## Step 30 — Slice B correction R72 (2026-08-15)

R72: the console's markable bound is the last message ACTUALLY RETURNED
by the painted thread page — `messages[-1].seq`, not the
discussion-wide `last_seq` — and an empty page leaves nothing markable.
No TUI paging/navigation added; the public projection unchanged.
Reviewer regressions 8/8; break-sweep (reintroduce the page-wide bound)
red then restored. Gate: 387 passed (384 parallel + 3 serial); all
workflows green both modes; test-v11 green; diff check clean. STOPPED
for re-review. Later slices held.

## Step 31 — WS-4 Slice B ACCEPTED; WS-4 complete (2026-08-15)

Reviewer accepted Slice B (message e8db33f06e0666854944ea281bc62381,
review-2026-08-15T11-16-51Z.md): R69–R72 satisfied, no Slice B finding
remains. Independent verification: focused set 46/46; test-v11 384
parallel + 3 serial; diff check clean. REMAIN STOPPED: Work revisions,
terminal outcomes, WS-5/WS-6, deployment, and TUI expansion are
separate later gates, not released.

## Step 32 — terminal-outcome slice: four-outcome atomic close + WF-10 (2026-08-15)

Schema v10: `work.rationale` and FK-bound `work.duplicate_of` join
`outcome`; there is ONE prose concept — the close's `disposition` field
is renamed `rationale` across storage, events, CLI (`close
--rationale`), and JSON with no alias (obligation `dispose
--disposition` is a separate unchanged concept).

The one atomic close now accepts exactly `satisfying`,
`non-satisfying`, `rejected`, or `cancelled`; every outcome requires a
non-empty rationale (whitespace, omission, unknown, or compact values
refuse before commit; the result is never inferred from classification
or prose). Cancellation is ordinary accelerated close: same
Current-only handler gate, same open-child refusal, no cascade or
child bypass. A duplicate is a `rejected` close whose structured
reason names the surviving Work through the explicit NON-GATING
`duplicate_of`: refuses self, missing targets, and any non-rejected
outcome carrying it; a Work CLASSIFIED `duplicate` refuses a linkless
rejection ("free text alone is insufficient"), rechecked against the
COMMITTING classification in-lock; ordinary rejection stays valid
without it. The link is recorded in the close event, the Work row,
`detail` (`rationale`, `duplicate_of`), and `links` in BOTH directions
(`duplicate_of` far-summary + the survivor's `duplicates` list) —
never touching readiness, Current, phase, or edges.

All four outcomes share the unchanged close machinery: Current+Next
clearing, pending response-obligation AND verification-assignment
withdrawal, round conclusion with the audited summary (basis =
rationale), level-triggered dependent recomputation waking only
last-gate dependents, last-gate wake sweep, dense audit, immutability.

Evidence: new `test_terminal_outcomes.py` (12): parametrized
four-outcome dismantling of a full-featured rig, vocabulary/rationale
hard gates, exact duplicate-link rules with both-direction navigation
and non-gating proof, linkless-duplicate in-lock race, close races
against respond/report/pass/close serializing one history,
whole-or-nothing fault injection through the duplicate-fold close,
restart + retry. New WF-10 story (source+packaged): the four sibling
fixtures each dismantled identically, ordinary + duplicate rejection
with the link refusal and both link directions, proposer-vs-Current
cancellation, open-child cancellation refusal without cascade, the
refusal matrix, and the four spawned races proven one-history from the
audit order. All prior stories migrated to `close --rationale`.

Break-sweeps (defect in, red, restored): O1 two-outcome vocabulary,
O2 optional rationale, O3 dropped link rules, O4 both duplicate-
classification guards, O5 in-lock recheck alone (race regression
bites). Gate: 401 passed (398 parallel + 3 serial); every workflow
green source+packaged; `just test-v11` green; diff check clean.
STOPPED for review. Work revisions, WS-5/WS-6, deployment, migration,
and TUI expansion held.

## Step 33 — terminal-outcome corrections R73–R74 (2026-08-15)

R73: omitting `--rationale` or `--outcome` on close now refuses through
the promised JSON stderr/exit-one agent contract — argparse no longer
owns those refusals; the transition does, with no mutation. WF-10's
refusal matrix gains both omissions through source and packaged CLI.

R74: `duplicate_of` must name a work that is itself CANONICAL — a
target whose own `duplicate_of` is null — checked pre-lock and
rechecked in-lock, so chains and mutual cycles (which would leave no
surviving record) refuse while closed canonical targets stay valid.
New regressions: the reviewer's chain refusal, a mutual-cycle race
losing in-lock, the closed-canonical case, and WF-10's story-level
chain refusal with the survivor's duplicates list.

Evidence: reviewer regressions pass (17/17 focused incl. their two);
break-sweeps — argparse-owned omission, both canonical-target guards,
in-lock recheck alone — each red then restored. Gate: 406 passed (403
parallel + 3 serial); all workflows green source+packaged; test-v11
green; diff check clean. STOPPED for re-review. Later phases held.

## Step 34 — terminal-outcome slice ACCEPTED (2026-08-15)

Reviewer accepted the terminal-outcome slice (message
bf14e82da505bac83317628d9518ad45, review-2026-08-15T14-45-25Z.md):
R73–R74 satisfied, no review finding remains. Independent verification:
focused terminal/WF-10/close/CLI/JSON set 46/46; test-v11 403 parallel
+ 3 serial; diff check clean. REMAIN STOPPED: Work revisions,
WS-5/WS-6, deployment, migration, and TUI expansion are separate later
gates.

## Step 35 — append-only Work revisions + WF-11 (2026-08-15)

Schema v11: append-only `revisions` table (seq PK, work FK, monotonic
revision UNIQUE per work, expected prior, promoted discussion FK +
message_seq provenance, Current actor, rationale, complete
self-contained content, created_ts). Projection 2.1: `detail` exposes
exactly ONE effective revision plus the deterministic ordered immutable
history — complete content and provenance, no discussion replay. No
fixed contract fields, no template machinery, no dossier binding.

`revise_work` / CLI `revise WORK --message --expect --rationale` (R73
discipline: omissions refuse via the JSON exit-one contract): promotes
one durable discussion message as the whole contract. Authority is the
LIVE resolved Current handler of OPEN work, in-lock, snapshot recorded;
transfer of Current transfers it. The promoted message must live in a
discussion currently carrying the open work's label (rechecked in-lock
against the unlabel race). The write is compare-and-swap on the
explicit expected prior revision — pre-lock stale refusal plus in-lock
recheck; a concurrent or stale writer refuses whole WITHOUT consuming
a sequence (asserted); the UNIQUE(work, revision) constraint backstops
the same invariant. Terminal work refuses revision (pre-lock and
in-lock against the racing close); committed history survives closure
byte-identical.

Evidence: `test_revisions.py` (12): record completeness incl.
resolution facts in the audit, ordered append-only history +
effective-is-last, the authority matrix incl. generation reassignment,
provenance rules + relabel eligibility + mid-flight unlabel race, CAS
wrong/stale/unnamed expectations + concurrent-promotion race with
no-sequence proof + rebase retry, terminal immutability + mid-flight
close race, child-scope independence, read purity + whole-or-nothing
fault injection, restart + replay refusal. WF-11 story (source +
packaged): requester proposes / Current promotes, direct-revision
refusal, the full refusal matrix, spawned CAS race with dense audit +
verbatim-retry refusal, Current transfer moving the authority,
independent child work gating the close, terminal immutability with
history intact.

Break-sweeps (defect in, red, restored): V1 dropped handler gate, V2
CAS replaced by silent rebase-onto-live (the honest defect — a dropped
in-lock compare alone is backstopped by UNIQUE and refused
identically), V3 dropped in-lock provenance recheck, V4 dropped
in-lock terminal recheck, V5 side-connection commit breaking
atomicity. Gate: 420 passed (417 parallel + 3 serial); all workflows
green source+packaged; test-v11 green; diff check clean. STOPPED for
review. WS-5/WS-6, template/dossier binding, deployment, migration,
and TUI expansion held.

## Step 36 — Work-revision correction R75 (2026-08-15)

R75: revision history is a bounded paginated canonical list. The
effective revision stays DIRECT in `detail`; the history becomes a
bounded 50-entry ordered preview with explicit `revision_count`,
`revisions_truncated`, and a `revisions_next_after` continuation
cursor; the new pure paged read `revisions WORK --after/--limit`
(shared `_page_bounds` contract: non-negative cursor, limit 1..500
refusing over-max, explicit next_after, one snapshot) joins the preview
without a gap or repeat. WF-11 gains the source+packaged page walk and
the bounds refusal matrix. Reviewer regression (53 revisions: direct
effective, count 53, 50-entry truncated preview, cursor 50, tail pages
[51,52,53] then None) passes. Break-sweeps: silent truncation and a
bounds-free paged read each red then restored. Gate: 421 passed (418
parallel + 3 serial); all workflows green source+packaged; test-v11
green; diff check clean. STOPPED for re-review. Later phases held.

## Step 37 — Work-revision slice ACCEPTED (2026-08-15)

Reviewer accepted the Work-revision slice after R75 (message
c0e6e328727fa858ed3be5b56f03e491, review-2026-08-15T15-17-42Z.md): no
Work-revision finding remains. Independent verification: reviewer
focused set 29/29; test-v11 421 total; diff check clean. REMAIN
STOPPED: WS-5/WS-6, external template/dossier binding, deployment,
migration, and further TUI expansion require their own explicit
release.

## Step 38 — WS-5 effectively-once mutation retry (2026-08-15)

Schema v12: append-only `operations` (PK (participant, op_id),
canonical semantic fingerprint, nullable domain-event `seq`, complete
replayable result, its OWN dense `recorded` cursor, permanent
retention). Projection 2.2.

Every public mutation — all 19 transitions plus init and regen —
accepts an optional client `--op-id` (global CLI flag before the verb;
1–128 UTF-8 bytes, no whitespace/control; pure reads REFUSE one). The
fingerprint is sha256 over canonical JSON of operation + actor + TYPED
validated input, excluding dynamic resolution output. `_write` commits
the operation record, effect, event, and the COMPLETE result
(decorations moved into in-transaction `finish` closures) atomically:
optimistic pre-write peek, in-lock recheck turning a lost identical
race into a replay, PK backstop. Exact retry is a pure replay of the
stored result with the ORIGINAL seq (no event, no byte, hash-proved);
conflicting reuse refuses closed; refusals never consume the identity;
successful protected no-ops (the losing seen mark) consume it via a
record-only transaction (seq NULL, no invented event) and replay THAT
invocation's result verbatim after later cursor advances (R76). Every
result carries exactly one `operation` shape: null / committed /
replayed (R78). Identity gate precedes replay: removed members get no
carve-out; committed operations replay across later Work state and
config generations. `operation-log` pages one's own records on
`recorded` under the shared bounds contract (R79). Init gains the
required generation-1-validated `--participant` (P9a): the fresh path
records the operation in the initializing transaction; protected
re-init on an existing authority applies the current-generation
identity gate then the exact/conflicting lookup; regen participates
identically (R77/R81).

Evidence: `test_ws5_operations.py` (16): grammar, per-participant
scope, the three envelope shapes, exact-retry purity (events + hash +
single effect), conflicting reuse, refusal non-poisoning,
later-state/config-generation replay, removed-identity boundary,
both in-lock races, protected no-op consumption + verbatim replay +
conflict, operation-log paging/bounds/purity/own-only, whole-or-
nothing fault injection with restart replay, protected init/re-init/
regen. WF-12 (source + packaged, 2 stories): lost response + exact
retry with shape/seq/event assertions, the spawned identical race
(one committed + one replayed, one effect, dense audit), conflicting
reuse + cross-participant independence, refusal-then-correction,
pure-read refusal, later-state replay across a regen with the
protected regeneration itself replaying, protected no-op, the
seven-family retry sweep, and init end to end. All init call sites
migrated to the named participant (fixtures pick the first
config-capable member; wfdriver likewise).

Break-sweeps (defect in, red, restored): W1 dropped in-lock recheck
(race loser refuses instead of replaying), W2 record outside the
transaction (crash sweep bites), W3 fingerprint absorbing dynamic
state (exact retry conflicts), W4 peek-time consumption (refusal
poisons the id), W5 global scope (cross-participant independence
bites). Gate: 441 passed (438 parallel + 3 serial); all workflows
green source+packaged; test-v11 green; diff check clean. STOPPED for
review. WS-6, template/dossier binding, deployment, migration, and
TUI expansion held.

## Step 39 — WS-5 corrections R82–R84 (2026-08-15)

R82: ONE shared exact op-id grammar (`validate_op_id` in the
authority, used by transitions AND the configuration family): no
whitespace and no control character of ANY kind — all Unicode
category C (C0, DEL, C1, format, surrogate, unassigned) refuse, as
advertised.

R83: flexible inputs normalize BEFORE fingerprinting, once, in the
form the transition itself uses: create_discussion labels
(string↔list), post include (comma string↔selector list),
create_round assign, and accept's create dict (canonical key set) —
one semantic request never conflicts with itself.

R84: identity gate and replay lookup are ONE coherent observation on
every path — the optimistic peek (one read transaction whose snapshot
starts at the lookup, gate read against that same state), the in-lock
path (`_op_identity` inside BEGIN IMMEDIATE, with the fresh-bootstrap
exemption where the members rows commit in that very transaction and
the proposed-document gate governs per R81), the no-op record-only
transaction, regen, and existing-authority re-init. Both-order races:
a removal committing before the observation refuses and consumes
nothing; one committing after leaves the valid committed replay.

Evidence: reviewer regressions 3/3 (DEL grammar, normalized
fingerprint, removal-vs-replay race); new both-order races on the
in-lock and no-op paths; break-sweeps — C0-only grammar,
post-fingerprint normalization, split gate/lookup observations — each
red then restored. Gate: 446 passed (443 parallel + 3 serial); all
workflows green source+packaged; test-v11 green; diff check clean.
STOPPED for re-review. WS-6 and later phases held.

## Step 40 — WS-5 correction R85 (2026-08-15)

R85: the current-identity gate is also the INFORMATION boundary. On
every shared-observation read path (optimistic, regen,
existing-authority re-init) the lookup's conclusion — replay OR
conflicting-reuse refusal — is disclosed only after the identity gate
speaks against the same transaction state: a conflict raised by the
lookup is caught, the gate rechecked, and its refusal supersedes; both
valid linearization orders preserved (a removal after the observation
leaves the valid outcome). The write-locked paths (in-lock, no-op
record) were already identity-first under BEGIN IMMEDIATE. Reviewer
regression `test_removed_identity_gate_precedes_conflicting_replay_
lookup` passes (4/4 in their file); break-sweep (conflict disclosed
before the gate) red then restored. Gate: 447 passed (444 parallel +
3 serial); all workflows green source+packaged; test-v11 green; diff
check clean. STOPPED for re-review. WS-6 and later phases held.

## Step 41 — WS-5 ACCEPTED (2026-08-15)

Reviewer accepted WS-5 (message 232442a08dd58c3f89fb6ec2f11f70f6,
review-2026-08-15T16-31-47Z.md): R82–R85 all satisfied, no WS-5 review
finding remains. Independent verification: focused suite 26/26;
test-v11 447 (444 parallel + 3 serial); diff check clean. WS-5 is
COMPLETE. REMAIN STOPPED: WS-6 implementation is held until its
remaining design boundary is pinned and explicitly released.

## Step 42 — WS-6 Slice A: portable dossier authority (2026-08-15)

Schema v13; projection 2.3.

Root catalog: optional strict top-level `roots` in `baton.json` —
entries `{display}`, ids under the v10 grammar (`validate_root_id`:
≤64 bytes, dotted lowercase/underscore, never `validate_handle`) —
projected to a `roots` table with additive-and-mark retirement, the
never-reuse gate, and diff-summary entries; `wfdriver.document`
gains `roots=`.

Bindings: append-only per-Work revisions enforcing the exact M4
locator `work/records/YYYY/MM/<stable-record>` (literal prefix,
4-digit year, month 01–12, ONE safe component, containment syntax, no
probing). `create --binding ROOT:PATH` commits revision 1 atomically
with the Work (creator authority, live-root in-lock); `bind` is
Current-only in-lock, expected-prior CAS, non-empty rationale, live
root, terminal-freeze — all rechecked in the committing transaction.
`detail` returns the effective binding plus the bounded 50-entry
preview (count/truncated/cursor); paged pure `bindings WORK` read.

References (M1 literal): every public mutation — the 19 transitions,
`bind`, and the configuration family — carries ordered typed
`--ref`s, keyed to the ACT's event in `act_references` and exposed on
events and thread messages. One discriminated token grammar
(v10-root vs Work-id left of the colon). Independent refs need a LIVE
root, in-lock (mid-flight retirement race refuses); dossier refs need
a BOUND target (M3), pin the binding revision effective AT COMMIT
(anchoring race regression), carry no label/participation/workflow
effect (M2), and stay valid by revision after root retirement (M5).
Compound placement is explicit: `--answer-ref` rides accept's emitted
answer; nothing is copied, dropped, or guessed. Q1: init/regen accept
independent refs against the proposed/accepted catalog. Q2: a
reference-bearing no-op refuses whole. References join the WS-5
normalized fingerprints; protected binding/reference acts retry
exactly and conflict closed.

Evidence: `test_ws6_bindings.py` (17): catalog grammar/never-reuse/
retirement, exact locator shape, atomic creation binding, Current+CAS
authority incl. transfer, terminal freeze, mid-flight
close/second-binding/retirement races, ordered refs + event/thread
exposure, exact refusal matrix, retirement-survival by revision,
commit-time revision pinning, explicit compound placement, Q2 no-op,
protected retries, whole-or-nothing fault injection through a
reference-bearing post, restart + purity + pagination bounds. WF-13
(source + packaged): born-bound PUSH-1, Current-only attach on
LANG-42, dossier repro + accept with explicit placement, CAS
correction with old proofs anchored to revision 1, transfer moving
bind authority, the retirement leg, resolver-free canonical reads,
close freezing history, a bindingless lightweight close, WS-5 retries
and the spawned same-prior binding race.

Break-sweeps (defect in, red, restored): B1 dropped Current gate, B2
CAS silent rebase, B3 constant revision anchoring, B4 dropped in-lock
root liveness (bites the mid-flight retirement race), B5 dropped M4
shape, B6 answer refs silently copied onto the accept act, B7 an
os.stat probe in the commit path. Gate: 466 passed (463 parallel + 3
serial); all workflows green source+packaged; test-v11 green; diff
check clean. STOPPED for review. Slice B (onboarding verbs incl. the
R88 crash-recoverable scaffold, resolver, templates, bootstrap,
WF-14/WF-15), deployment, and migration held.

## Step 43 — WS-6 Slice A corrections R89–R91 (2026-08-15)

R89: ONE typed reference vocabulary. The parser is split into a pure
token grammar (`_parse_ref_tokens`, shared by every family including
the configuration acts — the backslash and every containment refusal
now apply uniformly) and the optimistic store peek. Fresh activation
refuses the dossier form with its honest reason (generation one has no
bound work); `regen` is dossier-capable — the citation pins the
effective binding revision in the committing transaction under the
same retirement rule — and its store-touching peek runs only AFTER the
identity/capability gate (new disclosure-boundary regression: a
refused actor gets the capability refusal, never binding facts). Both
reviewer regressions pass.

R90: the bounded console renders the SAME portable facts as JSON — a
`binding root:path rN` line from the canonical detail and ordered
`[root:path]` reference suffixes on messages, consuming the projection
only; a same-fixture real-PTY parity test builds one instance, reads
the JSON facts, and asserts the console shows them verbatim.

R91: the complete matrix (`test_ws6_matrix.py`, 24): one
reference-bearing act through EVERY public mutation family — the 20
work-side families parametrized with event-placement and WS-5
exact-retry assertions, plus fresh activation and dossier-capable
regen; whole-or-nothing fault injection through the compound accept
carrying BOTH `--ref` and `--answer-ref` placements; and the named
both-order races — binding vs binding/transfer/close/retirement and
reference vs correction/close/retirement — asserting the committed
revision/order where both orders legitimately succeed (a bound work
stays citable while and after closing, pinned to its frozen revision).

Also journaled: the R88-superseded ruling (init is deliberately
one-shot; manual recovery; Amendment 6 withdrawn) as WS6-REVIEW.md
Amendment 7 — the approved Slice B direction.

Break-sweeps: C1 peek-before-gate (disclosure regression bites), C2
the weak config path parser (grammar regression bites), C3 the console
dropping the binding line (parity regression bites). Gate: 494 passed
(491 parallel + 3 serial); all workflows green source+packaged;
test-v11 green; diff check clean. STOPPED for re-review; a clean
acceptance releases bounded Slice B per the pinned instruction.

## Step 44 — WS-6 Slice A ACCEPTED; Slice B begins (2026-08-15)

Reviewer accepted Slice A (message ecb0056258c06bd422e1b28db9abf15b):
R89–R91 satisfied; 27 focused and 494 full v11 tests pass. Bounded
Slice B released immediately per the pinned instruction. Live
production deploy/migration/shutdown/cutover remain held for
Slawomir's manual operation.

## Step 45 — WS-6 Slice B: the filesystem domain (2026-08-15)

Implemented per the accepted M1–M6 + Amendments 1–7 shape:

- `src/baton_work/project.py`: `scaffold_home` (`init DIR` — editable
  strict-JSON scaffold plus separate BATON-SETUP.md instructions, no
  database, deliberately ONE-SHOT: any managed target refuses whole,
  naming the blockers, manual recovery only); `load_resolver` /
  `resolve_base` (the explicit machine-local `roots.json` — strict
  `{"roots": {id: "/absolute"}}`, `validate_root_id` grammar, never
  searched for, persisted, or fingerprinted); `template_dir` (release
  layout first — `tmpl/` beside `bin/` per M6, never zipapp-embedded —
  then the source tree); `bootstrap_project` (two-phase O_EXCL vendor
  of the numbered templates plus `work/open` + `work/records` into ONE
  resolved project root: containment via realpath + symlink-walk,
  identical bytes report already-present, conflicting bytes / wrong
  types / symlinks / escapes refuse without replacement, nothing is
  deleted, overwritten, or written back to the distribution).
- `tmpl/work-basic-1.md`: edition 1 of the numbered instructional
  pattern (canonical `work/records/YYYY/MM/<stable-record>` locations,
  REPORT/PLAN/PROGRESS responsibilities, binding guidance); shipped as
  a sibling release asset by build_release.py SNAPSHOT and deploy.py.
- CLI: `init DIR` scaffolds; `activate DIR --participant` is the
  renamed one authoritative validation/creation (formerly `init`);
  `resolve LOCATOR --roots-file` (work-form pins the effective
  binding; root-form is direct); `bootstrap --root --roots-file
  [--template]`; `--config` per-command enforced instead of global;
  filesystem verbs refuse `--op-id`/`--ref` — outside the authority,
  no identity, no references.

Tests: `test_ws6_project.py` (8 focused: scaffold validity +
pristine-activate refusal leaving nothing, one-shot blockers by name,
scaffold→edit→activate with op-id replay, strict/absolute resolver,
vendor + inode-proof idempotence, conflict/type/symlink/escape
refusals, unknown template/root, filesystem-ops-never-touch-authority
with db-hash and no-resolver-bytes proof). WF-14 (locations story:
packaged mode drives a TEMPORARY bin/+tmpl/ release layout; byte
parity source+packaged; relocation by editing roots.json alone with
the database hash unchanged; the adversarial matrix; local template
specialization never silently upgraded; distribution immutability
incl. the archive-without-sibling-tmpl refusal). WF-15 (onboarding
story: empty dir → init → one-shot re-run refusal → pristine and
half-edited activation refusals leaving no database → protected
activation with exact replay → two members work → concurrent
activation of a fresh home admits exactly ONE winner →
partial-directory refusals by name).

Break-sweeps (defect in → red → restore → green): silent
overwrite/upgrade (phase-1 tolerance + phase-2 truncate — 4 red),
symlink checks dropped (3 red), resolve writing into the authority
(PRAGMA defect — hash checkpoint red both modes), distribution
write-back (append on read — 4 red), one-shot init dropped (O_TRUNC
adoption — 3 red), filesystem identity/ref guard dropped (2 red).

Gate: 503 parallel + 3 serial pass; all 56 workflow runs green
source+packaged; `just test-v11` green. The 43 gate warnings are
pre-existing environmental fork/forkpty DeprecationWarnings from the
PTY and multiprocessing tests under Python 3.13 xdist, not Slice B.
STOPPED at the review gate: WS-6 Slice B complete, awaiting review.
Live production deploy/migration/shutdown/cutover remain held for
Slawomir's manual operation.

## Step 46 — R92–R94 corrections (2026-08-15)

Reviewer requested changes (message e64c3124863376aa4840ca4f120db2b1,
review-2026-08-15T18-48-00Z.md); all four additive regressions were
red as observed, now green:

- **R92** — `resolve` now runs every locator suffix (root and dossier
  forms) through the ONE shared contained relative-path grammar
  (`_validate_ref_path`), and an independent root must be LIVE in the
  accepted authority: the machine-local resolver maps accepted root
  ids and never authorizes a second catalog (`ghost:` refuses with
  "not a live configured root" even when roots.json maps it).
- **R93** — bootstrap phase 2 no longer trusts EEXIST or path-based
  opens: directory EEXIST revalidates the actual entry through an
  O_NOFOLLOW dir-fd chain from the resolved base (ELOOP refuses), and
  template bytes are written through that same component-by-component
  chain, so a parent symlink inserted between the phases is refused,
  never followed.
- **R94** — every phase-two failure is caught at the operation
  boundary and translated into a structured refusal naming exactly
  what THIS invocation created: bootstrap reports the partial set on
  ordinary write failures (e.g. `tmpl/` before a PermissionError on
  `work/`), and init reports the file O_EXCL created whose byte write
  then failed alongside its earlier companions. Nothing is cleaned up
  automatically.

WF-14 extended with the public R92 forms (escape suffix in both
locator forms → "contained"; mapped-but-unconfigured root → "not a
live configured root"). Break-sweeps for the new guards (defect in →
red → restore → green): grammar dropped (3 red), liveness gate
dropped (3 red), no-follow chain dropped/EEXIST-means-success (raced
symlink escape red), partial reports dropped (both R94 regressions
red as raw exceptions). No sweep residue.

Gate: focused 12+4 green; all 56 workflow runs green source+packaged;
`just test-v11` 507 parallel + 3 serial green. STOPPED for re-review.
Production deploy/migration/shutdown/cutover remain held for
Slawomir's manual operation.

## Step 47 — R95–R98 corrections (2026-08-15)

Re-review requested four further corrections (message
46a4ff35ebd1021b3e056cc5266a4dd5, review-2026-08-15T18-58-12Z.md);
all five additive/extended regressions were red as observed, now
green:

- **R95** — the independent resolve form IS `ROOT_ID:relative/path`:
  a bare root (`pushcoin`) or empty suffix (`pushcoin:`) refuses with
  the canonical-locator message; only a bare WORK id resolves a
  dossier root.
- **R96** — no-follow now governs directory CREATION, not only EEXIST
  revalidation: the parent is chain-opened O_NOFOLLOW before mkdir,
  and the created-or-existing child is validated through that same
  parent fd. A parent swapped for a symlink mid-run is detected, the
  invocation's own misplaced empty directory is withdrawn (never user
  data), and the operation refuses — nothing this invocation makes
  survives outside the project root.
- **R97** — `roots.json` is parsed STRICTLY like every other
  document: duplicate root keys refuse at parse (shared
  `_no_duplicates` boundary from config) and unknown top-level fields
  refuse; the document is exactly `{"roots": {...}}`.
- **R98** — `os.write` return counts are checked in both writers: a
  short write is a reported partial failure naming the truncated
  managed file in the created set, never success; init and bootstrap
  byte-completeness is part of the success contract.

WF-14 extended with the CLI-visible forms: bare/empty-suffix resolve
refusals (R95) and duplicate-key/unknown-field resolver refusals
(R97). R96/R98 are fault injections and live in the focused suite.
Break-sweeps for the four new guards (defect in → red → restore →
green, no residue): R95 gate dropped (2 red), R96 creation trusted
blind (nested escape red), R97 laxity restored (2 red), R98 counts
ignored (both short-write regressions red).

Gate: focused 20 green under -W error::ResourceWarning (16 project +
WF-14/15 local run); all 56 workflow runs green source+packaged;
`just test-v11` 511 parallel + 3 serial green. STOPPED for re-review.
Production deploy/migration/shutdown/cutover remain held for
Slawomir's manual operation.

## Step 48 — R99 implemented; harness contradiction reported (2026-08-15)

R99 (message 6a26c8a37604d477945fa79846a4433f) implemented exactly as
ruled: directory creation is `os.mkdir(name, dir_fd=parent)` through
the held O_NOFOLLOW parent fd; the rmdir repair is removed entirely —
no cleanup delete anywhere; a parent unlinked after its fd was opened
fails the fd-relative mkdir itself (ENOENT, verified) and refuses
with the created-so-far report.

Reported a CONTRADICTION for ruling instead of choosing: the three
mkdir-injecting reviewer regressions arm their faults by comparing
`os.mkdir`'s first argument against ABSOLUTE paths, which presumes
path-based creation. Under the ruled fd-relative creation the
injection points are unreachable (observed: the three tests fail DID
NOT RAISE, 13/16 focused); under any absolute-path variant the nested
regression's own intercept performs the outside creation (POSIX
ignores dir_fd for absolute paths — verified empirically), so the
test can only end with `outside` non-empty or empty via a delete its
own `deleted == []` assertion forbids. Proposed re-keying the three
injection seams to the fd-relative boundary (details in
implementation-response-2026-08-15T19-11-33Z). No reviewer-authored
regression was modified. Full gate deliberately NOT claimed green
while the contradiction stands. Production operations remain held.

## Step 49 — WS-6 Slice B ACCEPTED; WS-6 complete (2026-08-15)

Reviewer accepted Slice B (message d2ea1cb2ac726f60e5ce55e1eb03b532,
review-2026-08-15T19-13-12Z.md). R99 satisfied: fd-relative
`os.mkdir(name, dir_fd=parent)` creation through the held no-follow
parent fd, no deletion path. The reported harness contradiction was
confirmed; the reviewer re-keyed only the three injection seams to
the fd-relative boundary, assertions unchanged. Verified locally and
by the reviewer: focused 16 passed; `just test-v11` 511 parallel + 3
serial green. No WS-6 Slice B finding remains — Slice B and the
planned WS-6 implementation are ACCEPTED. Production deployment,
mailbox creation/migration, participant shutdown, and cutover remain
held as Slawomir-owned manual operations.

## Step 50 — Gate B B1–B3 implemented; stopped for review (2026-08-15)

Per the released corrected plan (message e5edf007565a8d54458437467f63d909):

- **B1** — the console now formats the COMPLETE canonical row: ST
  gains the closed-outcome compact map (c/sat, c/nsat, c/rej,
  c/canc — a closed map like phase/classification), PROG renders the
  projection's direct closed/children, DEP the ruled open-dependent
  count. Resolved rows are COLLAPSED by default with an explicit
  "(N closed hidden — z shows)" footer and a `z` reveal. `b` opens
  blocking/dependent neighbors on demand — every line the `links`
  projection's far-row summary. The focused view states the typed
  waiting condition, closed outcome + rationale, effective binding,
  effective contract revision (message seq), duplicate/follow-up
  identity, and the discussion-set size — all canonical values; the
  renderer formats, never derives. Responsive narrow-width behavior
  drops whole low-priority columns (CLS→DEP→PROG→PHASE) keeping a
  minimum title width — identities are never squeezed; shared
  `visible_columns` keeps the parity parser locked to the layout.
- **B2** — parity extended: home rows now assert status/outcome,
  progress, and dep value-by-value across four viewers; new
  links-on-demand parity (TUI lines vs JSON `links` edges) and
  collapse parity (default = JSON open rows + named hidden count;
  `z` = the full JSON set with the canonical outcome).
- **B3** — `test_tui_packaged.py`: the ruled scenario (open → drill →
  discussion → explicit seen → JSON agreement) through the zipapp on
  a real PTY with PYTHONPATH absent, JSON side through the SAME
  archive; refuse-before-curses through the archive.
- Presentation prototypes (for disposition): key map q/j,k/Enter/
  Esc/o/s/b/z; responsive omission order; footer collapse notice.
- Break-sweeps (defect in → red → restore → green, no residue): DEP
  dropped client-side (parity red), closed outcome hidden (2 red),
  silent collapse (red), links far-status dropped (2 red),
  responsive omission disabled (red). A tenth guard bit on its own:
  the tui-boundary test caught the word SELECT in a comment.

Gate: 20 focused (9 TUI + 9 parity + 2 packaged) green;
`just test-v11` 518 parallel + 3 serial green. STOPPED for review.
Parallel trial and production operations remain held.

## Step 51 — v11-only deployer; reviewer TUI regressions green (2026-08-15)

Per follow-up 21fb9695d63413f0fd06b31bea5178aa (handoff = a real v11
deploy command to an explicit dist dir; joint trial after; automated
acceptance temp-only):

- **tools/deploy_work.py** (NEW, v11-only, shares nothing with the
  frozen v10 deploy): builds the baton-work zipapp (cli:entry,
  /usr/bin/env python3 interpreter, executable) and publishes the
  ruled release layout `<target>/bin/baton-work` + `<target>/tmpl/*`
  by ONE atomic rename of a sibling scratch dir — complete or
  nothing. The explicit target must not exist (exact release dirs
  are immutable; never adopt/overwrite/delete); a missing parent
  refuses; templates are sibling assets, never embedded.
- **tests/work/test_deploy_v11.py** (3, temp-only): ruled layout with
  byte-equal assets and no zipapp embedding; immutability + missing
  parent refusals; the INSTALLED executable runs the whole
  onboarding story (init → edit → activate → create → home →
  bootstrap vendoring the DEPLOYED sibling tmpl) plus the deployed
  TUI on a real PTY.
- The reviewer's five new TUI regressions (appended mid-round) made
  green: responsive budget now always fits (DROP_ORDER extended
  CLS→DEP→PROG→PHASE→READY→NEXT under the 44/56-cell checks); a full
  page of open rows RESERVES the hidden-closed footer line; long
  tables SCROLL so the selected row Enter acts on is always painted;
  the focused view lists the projection-declared
  available_transitions ("can: ...").
- Break-sweeps (defect in → red → restore → green, no residue):
  deployer overwrites in place; templates embedded in the zipapp;
  sibling assets dropped; scrolling dropped; footer reserve dropped;
  transitions line dropped; drop-order truncated.
- Handoff proof rerun with the DEPLOY command: deploy → init → edit →
  activate → create → home through the installed executable, the v10
  mailbox tree hash-identical before and after.

Gate: 28 focused (10 TUI + 11 parity + 2 packaged + 3 deploy + the 2
narrow-budget params) green; `just test-v11` 526 parallel + 3 serial
green. Awaiting Stop-1 disposition and the joint-trial arrangements;
production operations remain held.

## Step 52 — R102–R106 corrections (2026-08-15)

Per review-2026-08-15T19-54-12Z.md (which crossed the deployer round;
R106 and the transitions line were already green from Step 51):

- **R102** — the distribution is COMPLETE: tools/deploy_work.py now
  ships doc/BATON-WORK.md (new operator quickstart, docs/) and
  conf/baton.example.json (new complete valid strict example, conf/ —
  proven valid by the product's own loader) beside bin/ and tmpl/.
  B3 and its harness exercise the DEPLOYED artifact produced by the
  real deploy command — the ad-hoc source-copy/zipapp construction
  and the rm -rf handoff steps are gone.
- **R103** — the false byte-identity prose is withdrawn; containment
  is proven against an isolated CANARY tree (bytes+inode+mtime
  snapshot survives the whole deploy+onboarding story) and by the
  explicit config/path boundary. Production v10 is not probed at all.
- **R104** — the console now has ACTIONS: the `:` command bar routes
  the typed line through the ONE public CLI entry (same config,
  participant, grammar, refusals; boundary test amended to allow the
  cli import — SQL/_write/baton_core stay banned). B3 is the ruled
  scenario through the DEPLOYED console: create (both teams),
  include fan-out, request obligation, response, pass with planned
  return, dependency edge, terminal satisfying close unblocking the
  consumer, collapsed/revealed closed outcome, and a public refusal
  surfacing in the console.
- **R105** — links are NAVIGABLE (selectable rows with stable Work
  ids; Enter performs the cross-team drill-through with real
  breadcrumb ancestry) and the focused view lists the discussion SET
  selectably (ids + personal New); Enter opens exactly the chosen
  discussion; threads read in BOUNDED pages (n/p) with seen bounded
  by the painted page. Three real-PTY regressions added.
- **R106** — already green (fit at 44/56, footer reserve, scroll);
  completed with the explicit too-narrow refusal ("terminal too
  narrow: need N cells") below the minimum, plus its PTY test.
- The three WS-4-era console seen-tests were adapted to the new
  navigation (Enter-then-thread) with their page-bounded assertions
  UNCHANGED; the tui boundary guard bit twice more (uppercase needle)
  and its allowlist gained exactly `cli`.

Break-sweeps (defect in → red → restore → green, no residue):
command bar severed (B3 red), drill-through dropped (red), selection
ignored (red), paging dropped (red), too-narrow refusal dropped
(red), doc/conf assets dropped (red).

Gate: 33 focused (19 TUI + 9 parity + 2 packaged-scenario + 4
deploy, incl. all reviewer regressions) green; `just test-v11` 531
parallel + 3 serial green. STOPPED for re-review. Parallel trial and
production operations remain held.

## Step 53 — R107–R111 corrections (2026-08-15)

Per review-2026-08-15T20-00-39Z.md (which crossed the R102–R106
round; R108/R109 and the deployed-scenario B3 were already delivered
there):

- **R107** — the distribution is the full four-part release AND init
  consumes it: new exact-release assets doc/BATON-SETUP.md (source
  docs/) and conf/roots.scaffold.json join doc/BATON-WORK.md and
  conf/baton.example.json. `scaffold_home` now reads the setup
  document and roots seed BYTE-FOR-BYTE from the release and seeds
  baton.json from the configuration EXAMPLE's skeleton (teams/roots
  reset to the editable empty sections, fresh authority uuid) — the
  embedded SETUP_INSTRUCTIONS/_home_template constants are deleted;
  a missing sibling asset refuses, naming it (the reviewer's
  installed-init regression green). template_dir generalizes into the
  shared `_release_dir` asset resolution.
- **R110** — ONE packaged build path: wfdriver.build_archive and
  test_packaged's fixture now invoke tools/deploy_work.py and drive
  the installed `bin/baton-work`; the independent source-copy zipapp
  builders are gone; the whole 56-run workflow battery passes on the
  deployed product.
- **R111** — candidate assembly excludes __pycache__/.pyc/.pyo, and
  acceptance lists the deployed archive's members to pin the absence
  of interpreter residue (the checkout DID contain stale bytecode —
  the sweep proved the leak was real before the fix).
- The reviewer's newest regression — the command bar re-entering
  `--participant`/`--config` — is guarded: the console's validated
  session identity is fixed; a typed global refuses with the reason
  (identity-by-assertion never returns through the command bar).

Break-sweeps (defect in → red → restore → green, no residue):
bytecode shipped (member listing red); a VALID embedded substitute on
missing assets (installed-init regression red — the naive invalid-
JSON fallback was masked and the sweep was sharpened until it bit);
scaffold byte-drift (byte-for-byte red); identity guard dropped
(red).

Gate: 57 focused green (project 16, deploy 8, packaged 3, TUI 21,
parity 11 incl. every reviewer regression, deployed-scenario 2 —
counts per file); all 56 workflows green on the deployed product;
`just test-v11` 536 parallel + 3 serial green. STOPPED for
re-review. Parallel trial and production operations remain held.

## Step 54 — R112–R116 corrections (2026-08-15)

Per review-2026-08-15T20-19-16Z.md (which crossed the R107–R111
round; R112/R113/R114 were already delivered there and the reviewer's
three added regressions — installed-init asset refusal, deployed-
archive bytecode listing, command-bar participant replacement — pass
on that tree):

- **R112 residue** — docs/BATON-WORK.md corrected: conf/ is "the
  configuration example and scaffold seeds (init consumes them; a
  partial release refuses)", not "never read by the product".
- **R114 hardening** — the reviewer's newest abbreviation regression
  bit the exact-spelling guard: argparse accepts unambiguous long-
  option prefixes, so `:--part push.sl ...` impersonated. The guard
  now refuses EVERY abbreviation the parser would accept for
  --participant/--config (prefix match, len > 2). Both identity
  regressions green.
- **R115** — B3 completes the ruled story: after the outbound pass
  (pass + planted next, consumed_next=false in the audit), sl
  performs the CONSUMING return through the deployed console —
  Current returns to lang.bug, the planned Next is consumed
  (next=None, consumed_next=true), the audit distinguishes the two
  acts, and the include act's fan-out is asserted against the
  audit's resolved audience ({lang.bug, push.bug} from "*.bug").
  ada, Current again, closes satisfying; the consumer unblocks.
- **R116** — the discussion SET itself is paged: DISC_PAGE-bounded
  pages through the canonical continuation cursor (`n` forward with
  an explicit "(n: more)" hint, `p` return-to-start), reset on entry;
  a regression drives a set one-past-a-full-page and proves every
  discussion reachable. The quickstart now documents n/p honestly
  ("p return to its start (not a previous-page step)").

Break-sweeps: set paging dropped (regression red → restored);
abbreviation guard covered by the reviewer's own red-then-green.

Gate: 60 focused green across project/deploy/packaged/TUI/parity/
scenario (every reviewer regression incl. the two identity overrides
and the bytecode listing); `just test-v11` 539 parallel + 3 serial
green. STOPPED for re-review. Parallel trial and production
operations remain held.

## Step 55 — R117–R119 closed (2026-08-15)

Per review-2026-08-15T20-32-06Z.md (which crossed the R112–R116
round; R118 — the consuming return with audited distinction and
audience proof — and R119 — cursor-carried discussion-set paging —
were already delivered there, and the reviewer's two added
regressions pass on this tree):

- **R117** — the ruled grammar fix: the public CLI parser now sets
  `allow_abbrev=False`, pinning the full-spelling contract — no
  abbreviation of any global can be accepted anywhere on the public
  surface, so the parser grammar and the console's guard agree by
  construction (the guard remains as the human-readable explanation
  for the two fixed session globals, no longer a compensating
  denylist). New public-grammar regression: `--part` refuses as
  unrecognized through the CLI itself; sweep (re-enabling
  abbreviation) bites it.

Gate: 68 focused green (project/deploy/packaged/cli-boundary/TUI/
parity/scenario, every reviewer regression incl. both identity
overrides, the >50-discussion paging, and the grammar pin);
`just test-v11` 540 parallel + 3 serial green. STOPPED for
re-review. Parallel trial and production operations remain held.

## Step 56 — Gate B ACCEPTED; parallel trial released (2026-08-15)

Reviewer accepted Gate B (message 6e1ffd34f3329df7d19a3603bd24f9df,
review-2026-08-15T20-41-44Z.md): R117–R119 satisfied and every
earlier correction present; reviewer verification 68-focused +
540 parallel + 3 serial green, diff check clean. The isolated v11
parallel human/reviewer/implementer TRIAL is RELEASED: Slawomir may
commit the WIP, deploy with tools/deploy_work.py into a new explicit
immutable directory, and run init/edit/activate/TUI in a separate
v11 coordination home — both paths new/explicit, never naming v10.
The acceptance does NOT authorize production deployment, migration,
shutdown, or cutover; v10 stays the live coordination and recovery
channel during the trial. Commit message drafted and replied
(commit-message-gateb.txt, response 3705b2437fc34b913a0c66bb93aea7a3).

## Step 57 — first v11-coordinated finding delivered (2026-08-15)

The trial channel works end-to-end. v10 wake → v11 Work 26de18dd-W2
("Use initial-capital TUI headers", filed by baton.codex from the
first human TUI trial): the table header now draws initial-capital
LABELS (Title, St, Phase, Cls, Prog, Dep, Ready, Current, Next, New)
via name.capitalize() over the unchanged internal column identifiers;
canonical projection fields untouched; the immutable 6d1b944 trial
deploy untouched. PTY expectations updated; the all-caps sweep bites.
Focused TUI/parity/packaged 33 green; `just test-v11` 541 parallel +
3 serial green. Returned through v11 under op-id w2-return-1 with the
evidence message (#13) and the CONSUMING pass to baton.bug (Current
baton.bug, Next consumed); reviewer woken via v10. Production
operations remain held.

## Step 58 — W31: subject-bearing Thread vocabulary (2026-08-15)

Per v11 Work 26de18dd-W31 rev 2 and
findings/finding-thread-subject-vocabulary (no migration of 6d1b944,
no compatibility aliases, fresh authority for the next distribution):

- **Schema v14**: `threads(id, subject NOT NULL, ...)`,
  `thread_labels`, `thread_participants`, and every `discussion`
  column renamed to `thread`; thread ids are now `-T{seq}`.
- **Transitions**: `create_thread` requires a concise subject
  (`validate_subject`: non-empty, single line, ≤80 UTF-8 bytes;
  refusals leave no residue); the born Thread's subject is the Work's
  title; accept-created provider threads take the created title;
  replies never carry a subject. Subjects join payloads and therefore
  WS-5 fingerprints.
- **Projection 3.0** (breaking): `thread` exposes `subject`;
  `work_threads` rows carry `subject` and a canonical `ordinal`
  (stable label-order index for the T{n} selector — never derived
  client-side); `threads_for` and the detail preview carry subjects.
- **CLI**: `start-thread --subject` replaces `discuss`; `threads`,
  `work-threads`, `thread`, `say`, `label`, `unlabel`, `mark-seen`
  operate on threads; no Discussion vocabulary remains in
  src/baton_work or the quickstart.
- **TUI**: the thread list leads with `T{ordinal} {subject}` (id kept
  for reference); the compact bottom pane is `Msgs
  T{n}/{total} — {subject}`; modes are threads/msgs.
- Tests: whole-tree vocabulary migration (38 files); new
  `test_w31_threads.py` (subject contract, born-title subject,
  several-threads-per-Work AND one-thread-many-Works with stable
  ordinals, replies never repeat the subject) and the Msgs-pane PTY
  test. Sweeps bit for: validation dropped, born subject dropped,
  Msgs selector dropped, ordinal flattened. The tui boundary guard
  bit AGAIN on an uppercase noun in a comment (fourth time — lesson
  recorded).

Gate: engine 442 + TUI/parity 32 + packaged/deploy 14 + workflows 56
green; `just test-v11` 546 parallel + 3 serial green. Returning W31
to baton.feat through v11.

## Step 59 — W31 review round: R1 fixed, R2 held for ruling (2026-08-15)

W31 review (findings/finding-thread-subject-vocabulary/
review-2026-08-15T22-35-13Z.md): R1 — the subject now
validates/normalizes BEFORE the operation lookup and joins the typed
effectively-once fingerprint (identical retry replays; changed
subject under the same op-id refuses "different request", no
residue); the reviewer's regression is green and the sweep bites.
R3 — the successful-return addendum is appended to the W31
implementation response, preserving the blocked-return evidence and
naming the moved authority. R2 — one normalized single-line ≤80-byte
contract for Work title AND born Thread subject — awaits Slawomir's
explicit confirmation per the review; its two regressions remain
deliberately red and no full-gate claim is made while they stand.
Returned to baton.feat in v11 (message #45, op-id w31-return-2).

## Step 60 — W31 rev3: the unified title/subject contract (2026-08-15)

Slawomir approved R2 (v11 #46, promoted as W31 revision 3): Work
titles and Thread subjects share ONE normalized, non-empty,
single-line, ≤80-UTF-8-byte contract. Implemented:

- `create_work` normalizes the title through `validate_subject(...,
  "work title")` BEFORE the operation lookup — the fingerprint sees
  the one canonical value — and stores it as both the Work title and
  the born Thread subject; an invalid title refuses the creation
  whole with no residue; no silent truncation.
- The accept-created provider title normalizes through the same
  contract before accept's operation lookup.
- The reviewer's two pre-ruling regressions were adapted to the
  APPROVED semantics with their invariant preserved (refusal on
  newline/81-byte titles with byte-pure events; every stored born
  subject passes the one public validator; normalization proven by a
  padded title storing stripped). Sweep: dropping the contract makes
  both bite.

Focused W31: 7/7 green. `just test-v11`: 549 parallel + 3 serial
green. Returning to baton.feat; no commit and no dependent
unblocking until review is clean.

## Step 61 — W31 ACCEPTED and closed satisfying (2026-08-15)

Reviewer accepted W31 rev3 (v11 #52): focused 7/7, `just test-v11`
549 parallel + 3 serial, diff check clean; W17/W23 unblocked. The
WIP commit message covering the full diff since 6d1b944 (subject-
bearing Threads, the approved unified title/subject contract,
projection 3.0, start-thread CLI, Msgs pane, initial-capital headers,
`just deploy-v11`) was drafted and replied on the v10 claim
(commit-message-w31.txt, response c4910e08c2175e30ed92481e45063e33).
Nothing staged or committed; production operations remain held.

## Step 62 — W7: split-pane Work and Thread navigation (2026-08-15)

Fresh trial (authority 8b92cb10 on release 948e92f) assigned W7 per
SAME-SCHEMA-TRIAL-PLAN.md. Revalidated the split-pane ruling in
findings/finding-tui-leaf-enter (with the Thread-vocabulary
supersession) and the W8 boundary (message FORMATTING stays out of
scope). Implemented, schema UNTOUCHED at 14 (TUI-only; the existing
authority reopens trivially):

- The table mode is a stacked split on terminals ≥14 lines: the Work
  table above (scroll/collapse/footer unchanged), the highlighted
  Work's Msgs below. The divider always starts with "Msgs" (the
  parity parser keys on it); short terminals keep the single pane.
- Enter keeps its ONE stable meaning (drill into children); a
  drilled-empty leaf table previews the LEAF's own Msgs below — leaf
  communication is never behind an empty drill.
- Tab moves focus (presentation state, writes nothing). Focused Msgs
  keys: j/k switch the highlighted Work's DISTINCT threads (never
  merged), n/p page messages, s is the one explicit seen write
  bounded by the painted page, Esc returns.
- The pane defaults to the thread carrying the viewer's personal New
  (label order first match), else the first; highlight changes reset
  the explicit selection and paging and mark NOTHING seen.

Tests: test_w7_split_pane.py (4 real-PTY: highlight-follows preview
with New unchanged, leaf drill with Msgs below, Tab focus + page-
bounded s, New-first default + distinct switching); the parity parser
stops at the Msgs divider; all existing TUI/parity/packaged suites
green. Sweeps bit: leaf fallback dropped, New-first default dropped,
Tab dropped. Gate: `just test-v11` 553 parallel + 3 serial green.
Returning W7 to baton.feat via v11; reviewer woken via v10.

## Step 63 — W7 review round: R1/R2 corrected (2026-08-16)

Per findings/finding-tui-leaf-enter/review-2026-08-16T02-04-08Z.md:

- **R1** — the preview's thread selector now spans EVERY bounded page
  of `work_threads`: the visited continuation cursors are state
  (`preview_pages`), the New-first default walks pages until the
  personal-New thread is found wherever it lives, focused j/k cross
  page boundaries in both directions, and the header total is HONEST —
  exact on the last page, "N+" while more pages exist (never a
  truncated count shown as complete). Regression: DISC_PAGE+2
  threads with New only on page two — the default lands on T12/12,
  k walks T11 then across the boundary to T10/10+.
- **R2** — focusability follows the RENDERED layout: `split_active`
  is set at paint time; Tab and the focused-pane key branch gate on
  it, and the short-terminal paint resets focus to the Work pane. A
  short terminal never routes keys to an invisible pane. Regression:
  below MIN_SPLIT_HEIGHT, Tab is inert, no "Msgs" paints, j+Enter
  drill the visibly highlighted second Work. The sweep disables all
  three defense layers together and the regression bites (single-
  layer removal is covered by the remaining layers — recorded
  honestly).

Gate: 6 focused W7 + 38 TUI/parity green; `just test-v11` 555
parallel + 3 serial green; schema stays 14. Returning W7 round 2 to
baton.feat via v11.

## Step 64 — W8: formatted Thread messages (2026-08-16)

W7 closed satisfying (v11 #42); W8 assigned (#43). Revalidated
findings/finding-tui-message-format (+ the Thread supersession) and
implemented, schema untouched at 14, presentation only:

- Each message renders as a compact borderless BLOCK: a bold metadata
  header `#seq team.author ts` carrying the viewer's personal
  `• new` marker; the body wrapped to the pane width under a
  two-space indent; each reference readable on its own line.
- One shared formatter serves BOTH the split preview and the focused
  Msgs view (`format_message` + `paint_messages`).
- The page-bounded seen contract is preserved honestly under
  wrapping: the seen bound is the last message painted IN FULL — a
  clipped block never counts as seen.
- Additive projection 3.1: `thread()` messages carry a personal
  `new` boolean computed against the viewer's seen cursor — the
  renderer formats it, never derives it. Pagination and the explicit
  seen mutation are unchanged.
- The bounded-paging regression now derives page-two's bound from
  what page one actually painted instead of hardcoding a window, so
  it survives formatting changes to lines-per-message.

Tests: test_w8_message_format.py (4 real-PTY: block metadata/wrapped
body/reference lines with the full body reconstructable; personal
new marker straight from the projection; clipped-block-never-seen at
a short/narrow viewport; the preview paints the same blocks). Sweeps
bit: clip bound weakened, personal new flattened, wrapping dropped.
Gate: 44 TUI-family focused green; `just test-v11` 559 parallel + 3
serial green. Returning W8 to baton.feat via v11.

## Step 65 — W8 review round: R1–R3 corrected (2026-08-16)

Per findings/finding-tui-message-format/review-2026-08-16T02-22-38Z.md:

- **R1** — intra-message continuation: the FIRST block of a page may
  continue across pages via a skip cursor; `n` continues an
  unfinished block before it paginates; a compact `#seq (cont.)`
  header (narrow-pane safe) names the same message; the seen bound
  names a message only once its FINAL line has painted. Regression:
  a 25-line first message at a 6-line viewport — s refuses mid-body,
  four continuations land the tail, s then clears it.
- **R2** — the preview budget stops ABOVE the reserved global
  command/status row, so the seen bound can never count a line the
  final screen composition replaced. The first regression draft
  missed the boundary (the fixture never reached the row — recorded
  honestly); rewritten with an oversized block that fills the pane:
  the bottom row stays empty pre-status and the block stays New.
- **R3** — references wrap for display with a deeper continuation
  indent (canonical value untouched); a 74-byte path at a 40-column
  pane reconstructs in full from the screen.

All three sweeps bite (continuation path, status reserve, ref wrap).
Gate: 47 TUI-family focused green; `just test-v11` 562 parallel + 3
serial green; schema 14. Returning W8 round 2 to baton.feat via v11.

## Step 66 — W8 round 3: R4 resize-safe continuation (2026-08-16)

Per findings/finding-tui-message-format/review-2026-08-16T02-33-41Z.md
(R2/R3 resolved; R4 remained):

- **R4** — each skip cursor is now WIDTH-BOUND: the view remembers
  the width the skip was computed at and resets it to zero whenever
  the paint width differs — a resize can repeat content but can
  never omit it or fake a full paint (the premature-seen path where
  a wider rewrap left len(block) <= skip is structurally closed:
  the painter never sees a cursor from a different wrapping).
- ptyharness gained real mid-script resize: a ("resize", (cols,
  lines), pause) script entry issues TIOCSWINSZ + SIGWINCH, and
  `dynamic_size=True` leaves geometry ioctl-driven — the child
  stamps its own initial winsize pre-exec (closing the startup
  race the env pinning existed for) and unsets LINES/COLUMNS at
  BOTH env levels (pytest's readline putenv()s them at C level,
  invisible to os.environ — found by probing).
- Whole-token wrapping (break_on_hyphens=False) keeps identifiers,
  paths, and hyphenated words unbroken across wraps.
- Regressions: the real-PTY resize walk (narrow start, continuation,
  resize to 60 cols, premature s inert, tail, real s clears; the
  post-resize pages jointly cover the whole body — no omission) and
  the preview-path width-reset unit check. Both R4 sweeps bite.

Gate: 49 TUI-family focused green; `just test-v11` 564 parallel + 3
serial green; schema 14. Returning W8 round 3 to baton.feat via v11.

## Step 67 — W5: timer-based automatic refresh (2026-08-16)

W8 closed satisfying (v11 #49); W5 assigned (#50). Revalidated
findings/finding-tui-auto-refresh (+ the keystrokes-never-poll
clarification) and implemented, schema untouched at 14:

- The console holds a projection CACHE: every canonical read routes
  through it; ordinary keystrokes operate on cached data and never
  query the authority (navigation to a context the cache has never
  held fetches on miss — displaying a new view is not a poll).
- The configurable timer (default 2s, `tui --refresh SECONDS`,
  positive-only with a pre-curses JSON refusal) is the ONE background
  freshness trigger: getch times out, tick() drops the cache, the
  screen repaints. An explicit workflow act (s, the command bar)
  refreshes from its committed result — ruled as not-a-poll.
- The selection anchors to the WORK ID: a background refresh that
  inserts or removes rows never moves the cursor to a different
  Work; navigation moves the anchor, render only re-locates it.
- Quickstart documents the surface and semantics.
- The PTY replay harness now models ncurses scroll optimization
  (scroll regions, IL/DL, IND/RI, and the newline-at-region-bottom
  scroll ncurses actually emits) — found when a refresh repaint
  ghosted rows in the replay grid.

Regressions: keystrokes-hit-cache (counted projection reads: zero
across j/k/Tab/Esc; the tick performs exactly one home re-read and
surfaces the external Work); the discriminating id-stability case
([A,B,C], anchored on B, external close of A while idle — the
collapsed view drops A, an index cursor would land on C, the anchor
keeps B and Enter drills it; nothing marked seen); the positive-
interval refusal. Four sweeps bite (tick no-op, cache bypassed,
anchor dropped, validation dropped). Gate: 52 TUI-family green;
`just test-v11` 567 parallel + 3 serial green. Returning W5 to
baton.feat via v11.

## Step 68 — W5 review round: R1–R3 corrected (2026-08-16)

Per findings/finding-tui-auto-refresh/review-2026-08-16T03-10-53Z.md:

- **R1** — the refresh is WALL-CLOCK driven: a monotonic deadline
  that input can neither postpone nor accelerate; keys before the
  deadline serve from the cache, reaching it refreshes even while
  input keeps arriving (getch timeout = time remaining). Regression:
  ~2.4s of 150ms-spaced keys over a 0.5s interval — the externally
  created Work appears mid-typing, on schedule.
- **R2** — only a SUCCESSFUL mutating act invalidates the cache: the
  public MUTATIONS verb set is exported from the CLI and shared with
  the command bar. Regression: a refused close and a successful pure
  read leave the cache untouched (zero counted reads); a committed
  create refreshes exactly once and shows its result.
- **R3** — `--refresh` validates a FINITE usable interval
  (0 < r ≤ 86400) before curses; inf/nan/1e9 all refuse with the
  JSON contract pre-curses (parametrized regression).

All three sweeps bite (idle-timer restored, every-attempt flush,
positivity-only check). Gate: 57 TUI-family focused green;
`just test-v11` 572 parallel + 3 serial green; schema 14. Returning
W5 round 2 to baton.feat via v11.

## Step 69 — W5 round 3: R4 verb classification (2026-08-16)

Per findings/finding-tui-auto-refresh/review-2026-08-16T03-18-31Z.md:
the command bar's mutation classifier read argv[0], so a mutation
preceded by public globals (--op-id V, --ref V, ...) committed but
left the immediate view stale. The VERB is now the first token after
any leading global options — the same public grammar the JSON
interface takes — while only-successful-mutations-invalidate stands.
Regression extended: an --op-id-prefixed create is visible
immediately with exactly one flush; a global-prefixed say likewise;
a refused global-prefixed close flushes nothing; the sweep (raw
argv[0] restored) bites. Gate: 40 focused green; `just test-v11`
572 parallel + 3 serial green; schema 14. Returning W5 round 3.

## Step 70 — W5: the one-scheduler clarification applied (2026-08-16)

Slawomir pinned the refresh-scheduler contract (clarification in
findings/finding-tui-auto-refresh/FINDING.md): timer expiry and
successful local mutations are two PRODUCERS of one canonical
refresh path; pending requests coalesce; pure reads, refusals, and
navigation never schedule. Implemented as ruled: producers call
`schedule_refresh()` (a due flag); the cache accessor is the one
consumer, dropping the cache exactly once before the next canonical
read; tick(), both seen mutations, and the command bar's successful-
mutation branch all produce — no separate behaviors remain. New
coalescing regression: three ticks before one consumption re-read
exactly once. Gate: 55 TUI-family green; `just test-v11` 572
parallel + 3 serial green; schema 14.

## Step 71 — W5 round 4: R5 confirmed shared, R6 evidence corrected (2026-08-16)

review-2026-08-16T03-24-53Z.md crossed the one-scheduler
implementation (Step 70/T5 #58): R5's consolidation was already in —
timer expiry, both seen mutations, and the command bar's successful-
mutation branch all produce through the ONE coalescing
schedule_refresh (due flag), consumed once by the cache accessor.
The requested proof is added: a single sweep no-opping
schedule_refresh reddens BOTH the timer regression and the mutation
regression — the producers demonstrably share the hook. R6: the
false "--ref-carrying" evidence is corrected with an ACTUAL
--ref-prefixed say (independent reference on a configured root,
same leading-global grammar), visible immediately with exactly one
flush; the misleading comment is gone. Gate: 40 focused green;
`just test-v11` 572 parallel + 3 serial; schema 14.

## Step 72 — W5 round 5: R7 storage-change boundary; R6 verified fixed (2026-08-16)

Per findings/finding-tui-auto-refresh/review-2026-08-16T03-27-22Z.md
(which examined the pre-round-4 tree; the R6 --ref case was already
real by then — an actual `--ref pushcoin:docs/evidence.md say ...`,
comment corrected):

- **R7** — only an ACTUAL storage change schedules: the public
  command result decides — an effectively-once REPLAY
  (operation.state == "replayed") and a successful no-op
  (advanced == false) schedule nothing and leave the deadline and
  cache alone; the direct s paths schedule only when the cursor
  actually advanced. Regressions: the exact --op-id retry replays
  with refresh_due False and zero flushes; mark-seen advances once
  (schedules) then no-ops (does not); the already-seen direct s
  reports "already seen" with refresh_due False. The verb-only sweep
  bites.

Gate: 8 focused W5 + 55 family green; `just test-v11` 572 parallel +
3 serial; schema 14. Returning W5 round 5.

## Step 73 — W5 SIGNED OFF; checkpoint prepared (2026-08-16)

W5 signed off (review-2026-08-16T03-35-29Z.md: 8 focused, independent
572+3 gate, diff-check clean, schema 14). The explicit consuming pass
committed in v11 (T5 #63 — Current baton.feat, Next None). Edits
stopped for Slawomir's checkpoint commit: staged = the W5 arc
(app/cli/ptyharness/docs + dossier records); the commit message
("Add wall-clock automatic refresh with a single coalescing
scheduler") was delivered on the v10 request claim. W7/W8 are in
7fe2489. No next Work begins before the commit.

## Step 74 — W36: canonical Msg/My (2026-08-16)

The W5 checkpoint landed (8450a40); W36 assigned (v11 #66) per
findings/finding-work-message-action-counts. Implemented, schema 14:

- Projection 3.2: every Work row carries `message_count` (total
  DISTINCT messages across every thread labelled to the work or its
  descendants — the conversation-projection scope, overlap-safe: a
  thread labelled to two children counts once for the parent;
  seen-independent, answers only grow it) and
  `my_pending_obligations` (unresolved directed @ response
  obligations in the same scope where THIS viewer is an eligible
  handler under the CURRENTLY accepted route resolution — never
  inclusions, never another member's load; shared resolution and
  terminal withdrawal clear it for every handler). Purely derived;
  reading mutates nothing.
- TUI: a compact `Msg/My` column (the canonical fields combined in
  the console alone), correct label casing via HEADER_LABELS, placed
  in the responsive drop order; parity asserts the pair equals the
  two JSON fields verbatim.
- Focused suite: recursive/distinct/seen-independent Msg; My
  eligibility (handler yes, non-handler no, + inclusion nobody);
  answer grows Msg while clearing My; terminal withdrawal clears;
  LIVE eligibility follows a generation-2 reroute (the same pending
  obligation moves from ada's My to grace's); purity + reopen
  stability. Sweeps bit: DISTINCT dropped, handler check flattened
  to team-only, pending-status filter dropped.

Gate: 60 focused green; `just test-v11` 577 parallel + 3 serial
green. Returning W36 to baton.feat via v11.

## Step 75 — W36 review round: R1/R2 corrected (2026-08-16)

Per findings/finding-work-message-action-counts/
review-2026-08-16T03-59-30Z.md:

- **R1** — `My` now counts EVERY pending directed obligation flavor
  the participant can discharge: the response flavor
  (respond/dispose/accept) AND verification assignments (report);
  withdrawal clears either. Regression: a candidate round's assigned
  verifier owes 1 (a non-handler 0), the report clears it, and a
  second round's abandonment (withdrawal) clears likewise. The
  response-only sweep bites.
- **R2** — the ruled narrow coverage: Msg/My is kept or omitted as a
  WHOLE unit across the responsive budget — the retained
  ST/CURRENT/NEW columns hold their exact widths, and the narrow
  layout provably fits its terminal.

Gate: 39 focused green; `just test-v11` 579 parallel + 3 serial
green; schema 14. Returning W36 round 2 to baton.feat via v11.

## Step 76 — W36 SIGNED OFF and closed satisfying (2026-08-16)

Reviewer closed W36 satisfying (v11 #76): the verification and
narrow regressions pass, focused gate 15 green, diff-check clean.
The full `just test-v11` (579 parallel + 3 serial) had already run
green on this tree as the release gate. Holding for the next wake.

## Step 77 — W77: terminal phase null (2026-08-16)

W77 assigned (v11 T77 #81) per findings/finding-terminal-work-
no-phase. Implemented, schema 14, projection/presentation only:

- Canonical rows project `phase: null` for closed Work (the field is
  PRESENT — "not applicable", never omitted); open Work keeps its
  one required non-null phase. No `done` phase exists.
- Nothing is rewritten: the stored last-phase value survives in the
  work row (asserted directly against the DB) and the audit keeps
  every set_phase transition; the null is projection-only.
- The TUI's compact_phase renders `-` for null (never a fabricated
  label); the revealed closed row's Phase cell and the focused
  header both dash.
- Regressions: all four terminal outcomes project null with stored
  history preserved; open rows stay non-null; the JSON+PTY parity
  case. Sweeps bit: terminal phase leaking, fabricated null label.

Gate: 45 focused-family green; `just test-v11` 585 parallel + 3
serial green. Returning W77 to baton.feat via v11. Next serial per
the wake: W74 then W71 after clean review.

## Step 78 — W77 round 2: lifecycle-aware phase rendering (2026-08-16)

Per findings/finding-terminal-work-no-phase/
review-2026-08-16T04-21-41Z.md R1: `compact_phase(None)` was
unconditionally `-`, so a malformed OPEN row with null would have
masqueraded as valid closed rendering. The formatter is now
`phase_cell(status, phase)` — lifecycle-aware and fail-closed BOTH
ways: closed+null → `-`; open+null refuses visibly; closed+non-null
(a leaked phase) refuses; unruled open values keep failing through
the exhaustive compact map. `compact_phase` itself is strict again.
Both the row cells and the focused header route through it; parity
asserts the lifecycle-aware value. Regression covers all four
formatter branches plus the renderer boundary (a doctored open row
refuses at _row_cells); the masquerade sweep bites. Gate: 39
focused-family green; `just test-v11` 586 parallel + 3 serial green.
Returning W77 round 2.

## Step 79 — W77 SIGNED OFF and closed satisfying (2026-08-16)

Reviewer closed W77 round 2 satisfying in v11: the lifecycle-aware
null rendering passes, focused gate 15 green, diff-check clean.
W74 is next in the serial plan. Holding for the assignment wake.

## Step 80 — W74: root header noise removed (2026-08-16)

W74 assigned (v11 T74 #91) per findings/finding-tui-top-level-
header-noise. Presentation only: the root header drops the redundant
"— top-level work" phrase — identity plus the live summary
([oblig:/park:/due:]) remain; drilled views keep their real
breadcrumbs; narrow behavior unchanged; schema 14 untouched. The two
root-detection assertions in the existing suite were re-keyed to the
identity-led no-trail header. Regressions: root header shape (no
prose, no stray dash, summary intact), drilled breadcrumb intact,
narrow root fit. The restore sweep bites. Gate: 51 focused-family
green; `just test-v11` 589 parallel + 3 serial green. Returning W74;
W71 follows clean review.

## Step 81 — W74 SIGNED OFF and closed satisfying (2026-08-16)

Reviewer closed W74 satisfying in v11: bounded root-prose removal
with identity/summary/breadcrumb/narrow coverage intact, 21 focused
PTY tests, diff-check clean. W71 is next. Holding for the wake.

## Step 82 — W71: the superseding navigation contract (2026-08-16)

W71 assigned (v11 T71 #100; W27 cancelled/absorbed) per
findings/finding-tui-message-browser. Implemented, schema 14:

- **Main screen**: a bounded two-level containment tree — roots plus
  ↳ children, a ▸N disclosure for deeper children; Prog/Dep left the
  table; Enter has ONE meaning (open the Work's DETAIL, never a
  drill); `u` unfolds/re-roots with real breadcrumbs, Esc returns;
  the footer advertises the controls.
- **Detail view**: Threads (subjects, bounded pages, New-first
  default) above the selected Thread's formatted Messages; Ctrl-W
  h/j/k/l / arrows / w / Ctrl-W Ctrl-W move panes with visible
  focus markers; the breadcrumb names the detailed Work; the seen
  action stays explicit and page-bounded; `n` acts only while more
  exists (the disclosed more-state and the control agree — the last
  page never pages into an empty screen); the internal `after #N`
  cursor is GONE from all operator-facing text.
- **Refs**: an explicit per-message Refs section — visually separate,
  one canonical wrapped reference per line, never body text.
- **JSON (projection 4.0, breaking)**: the ambiguous `dep` is
  REPLACED by explicit live `open_blockers`/`open_dependents`;
  `progress` survives; the former detail-local open_blockers
  recompute is deduplicated onto the one row field.
- Suites: test_w71_navigation.py (6: two-level tree + disclosure,
  unfold/back, Enter-opens-details, Ctrl-W + footer + no-after,
  graph-field replacement incl. close withdrawal, the Refs section);
  the W7 split-preview file is superseded and removed; W8/W5/parity/
  tui/ws3/ws4/wf05/ws2-wf07 suites migrated to the new model (dep →
  open_dependents; drives via Enter/Ctrl-W). Three sweeps bite
  (disclosure dropped, Enter-drills restored, open_blockers
  hardwired — the last exposed and fixed the masking recompute).

Gate: `just test-v11` 589 parallel + 3 serial green. Returning W71
to baton.feat via v11.

## Step 83 — W71 round 2: R1–R3 corrected (2026-08-16)

Review (review-2026-08-16T05-19-05Z.md) kept W71 open on three
boundary defects; all corrected, interaction shape preserved:

- R1 — a later clipped message was unreachable: `paint_messages` now
  reports `more_below` whenever a later fetched whole block did not
  fit; `viewed_has_more`, the disclosed more-state line, and the `n`
  key all derive from that same fact, and the clipped block is never
  counted seen. The reviewer's regression
  (test_a_later_clipped_message_is_reachable_with_next) is green and
  reddens when `more_below` is dropped.
- R2 — repeated `u` corrupted the back stack: re-rooting at the
  current root is now idempotent (no duplicate `path` entry); one
  logical unfold takes exactly one Esc. The reviewer's regression
  (test_unfolding_the_current_root_is_idempotent) is green and
  reddens without the guard.
- R3 — the painted tree was composed from multiple snapshots: new
  canonical `projection.tree(root=None)` derives roots (or one
  re-root) + immediate children with depth, the team summary, and
  the snapshot token under ONE read transaction; the JSON verb
  `tree [WORK]` and `Console.view()` both consume that same result
  (one cache entry, no home/detail/summary/children composition);
  `children()` now also holds one read snapshot. Parity's home-rows
  and inline-children tests consume the tree verb directly, with a
  projected-depth assertion. New deterministic regression
  test_a_mid_read_commit_cannot_produce_a_mixed_tree commits a new
  root + a phase change between internal row reads and proves rows,
  summary, and token all name the pre-commit state; it reddens when
  tree() drops its read transaction.
- W5's read counters now probe projection.tree (the one background
  read path); docs/BATON-WORK.md documents the tree verb.

Gate: `just test-v11` 592 parallel + 3 serial green; schema 14.
Returning W71 round 2 to baton.feat via v11.

## Step 84 — W92: records/open cutover implementation (2026-08-16)

Assignment: v10 2bf37d0a + v11 T92 #106, from clean checkpoint 6c3519e6.
Revalidated and executed findings/finding-fresh-record-layout-cutover.

- INVENTORY.md (in the W92 dossier): per-dossier dispositions resolved from
  the checkpointed tree — 19 dossiers relocated to canonical
  work/records/2026/08/<slug>/ via git mv (history preserved), 6 resolved
  legacy dossiers left at work/finding-* pending the finding-next-release
  step-2 cleanup audit, 1 empty untracked directory removed (rmdir only).
  16 work/open relative symlinks for still-open records. v11 trial bindings:
  none exist; nothing to translate.
- References: the exact permanent source/test citations updated to record
  paths (baton_work/__init__, authority.py, baton_tui/state.py, four test
  files); living FINDING/PLAN/PROGRESS docs swept for the 19 moved slugs;
  review journals, frozen evidence files, and RELEASE-1.0.0.md untouched as
  history. docs/EFFECTIVE-BATON.md teaches the records/open layout.
  test_docs_consistency path constant updated; test_packaging_isolation's
  placeholder rule now also skips `...` ellipses.
- AGENTS.md: the ephemeral-finding section explicitly superseded (dated,
  checkpoint named) by the permanent record/open-index policy; process rules
  (serial work, review journals, one-writer PROGRESS, child records)
  preserved; legacy folders named as pending that audit.
- Schema 15 (SCHEMA_VERSION 15, projection 4.1 additive): work.priority
  (high/normal/low, NOT NULL DEFAULT normal, CHECK-closed — W10 groundwork);
  work.last_change_seq + millisecond work.last_changed_at stamped at birth
  and by every direct Work-row mutation via one _touch_work helper (wake,
  ready flip only on actual change, close, classify, set_phase, pass —
  W84 groundwork); clock_ms_now honours BATON_WORK_NOW. W78 project
  metadata deliberately NOT persisted: its per-Work shape is an open design
  question in its finding — refused rather than guessed.
- tests/work/test_w92_schema15.py (8): schema pin, default priority, closed
  priority domain, birth stamp, direct-mutation advance, indirect-act
  non-advance, projection exposure, millisecond format. Sweeps bite:
  set_phase stamp removed → red; CHECK removed → red. Raw-INSERT fixtures
  in test_transitions/test_soak updated for the NOT NULL columns.
- RUNBOOK.md + scripts/recreate-work.sh (W92 dossier): the held manual
  cutover steps; the recreation script verified end-to-end on a scratch
  schema-15 authority (13 items, canonical umbrella binding, idempotent
  rerun via op-ids). Production deployment/retirement remain Slawomir's.

Gate: `just test-v11` 600 parallel + 3 serial green. The legacy full-suite
(`just test`) failure set is being compared against the 6c3519e6 baseline in
an isolated worktree; pre-existing failures there (e.g. v10
test_generation_layout) reproduce identically at the checkpoint.

## Step 85 — W92 reviewer follow-ups during implementation (2026-08-16)

- 80bbe488: W92 recorded queued→active in the trial (seq 107). The TUI
  Work-search request is recreated PARKED by the cutover script (verified:
  14 items, one parked, idempotent). No prior written pin was found in the
  records, trial authority, or v10 scans; pinned now at
  findings/finding-tui-work-search/ with that provenance — the original
  location can be appended there if one exists.
- da67bbbf: new W92 release gate accepted. finding-active-work-claim read;
  trial child 8b92cb10-W108 ("Claim active Work atomically before starting")
  created under W92 and W92 blocked on it (seq 109, W92 ready=false).
  Schema 15 includes the claimant identity (work.active_team/active_member,
  projected as `active`, null until claimed); the claim/release transition
  matrix and the required-submission-classification refusal are that child's
  own gated implementation per its plan — the matrix is explicitly unruled,
  so no claim verbs were guessed. Regression added (columns present,
  projection null). Gate: 601 parallel + 3 serial green.

## Step 86 — W92: required submission classification (2026-08-16)

Reviewer follow-up 576fecf5: the classification clarification is a
fresh-schema requirement independent of the claim matrix. Implemented:

- Both creation paths (create_work and accept --create) refuse omission and
  'unknown' with a readable refusal naming the concrete choices; classify
  keeps its full vocabulary, so the handler may still reclassify later —
  including back to unknown, which stays an ordinary audited value.
- work.classification loses its schema DEFAULT (fail-closed at the SQL
  layer too); CLI help rewritten.
- ~80 test call sites across 60+ files updated to submit a concrete
  classification (regex sweeps + hand fixes); tests that pinned the old
  default-unknown behavior now pin the submitted value; two tests that
  deliberately exercise an explicit classify step create their Work as
  'limitation' so the step still records a real change; raw crash-injection
  INSERTs carry the column.
- recreate-work.sh submits confirmed-defect for the six trial bug-queue
  items and design-choice for the eight feature requests (verified on a
  fresh scratch authority: 14 rows, correct classification counts, one
  parked, idempotent rerun).
- New regression (omission red, unknown red, later reclassify green);
  sweep bites when the refusal is removed. Gate: 602 parallel + 3 serial.

## Step 87 — W92: classification refusal HELD for W108 (2026-08-16)

Reviewer sequencing 32f12e55 (crossed with Step 86's delivery): both the
claim verbs AND the required-classification refusal wait until W108 records
the complete transition/recovery matrix, then hand back for review.

- The Step 86 refusal is reverted on both creation paths; a comment at each
  site names the hold and W108. CLI help reverted to the default-unknown
  contract with a forward note. The held regression test is removed
  (re-lands with W108).
- RETAINED (valid under both rules): the ~80 mechanical call-site updates
  submitting explicit concrete classifications, the schema-DEFAULT drop
  (creation paths always pass an explicit value), the assertion-pin
  updates, and recreate-work.sh's explicit confirmed-defect/design-choice
  submissions.
- Gate: 601 parallel + 3 serial green.

## Step 88 — classification refusal re-landed per review (2026-08-16)

review-2026-08-16T09-27-05Z (finding-active-work-claim) crossed the Step 87
hold and reviews the refusal as delivered work — the latest ruling, so
Step 87's revert is undone: the refusal stands on BOTH creation paths, CLI
help restored, the direct-creation regression restored.

- R1: focused accept --create cases added for omitted and explicit
  'unknown' classification, each proving NO effect — event sequence,
  obligation status (still pending), work/edge/message counts all
  unchanged. The injected duplicate classification key in the
  empty-value refusal case is removed so the intended input is
  unambiguous. Sweep: the accept-path refusal removed → the new
  regression reds.
- Gate: 603 parallel + 3 serial green.

Held for W108: the claim verbs and transition/recovery matrix only.

## Step 89 — W108: the atomic active-work claim (2026-08-16)

Ruling 760e0c12 pinned the matrix (FINDING "Readiness and pass
clarification"); implemented under W108:

- `phase --to active` IS the atomic claim (no new verb invented — the
  spelling question in the finding remains open, so the existing public
  grammar carries the semantics): in-transaction gates check (an advisory
  ready observation loses to a dependency committed first), refusal naming
  the recorded claimant on competition (also for a repeat claim without an
  op-id — fail closed; an exact retry replays), claimant recorded in the
  payload and the row.
- Every ruled exit releases: leaving active via set_phase (audited as
  released_claimant), terminal close, and PASS — a pass additionally
  re-phases the work by its gates (queued when ready, waiting-on-gates
  otherwise; the recorded condition wakes normally) and never claims for
  the recipient.
- Invariant "never phase=active with ready=false": a gate arriving on
  actively claimed work demotes it to waiting-on-gates and releases the
  claimant inside the causing event (no separate audit row — flagged for
  review).
- Projection: `active` (already in 4.1) + the TUI detail facts name the
  claimant. docs/BATON-WORK.md documents the claim; AGENTS.md gains the
  no-execution-while-queued policy.
- tests/work/test_w108_active_claim.py (11): claim+audit, competing claim
  fails closed naming the claimant with no burned event, exact-retry
  replay, unmet child/blocker refusals, advisory-observation race, pass
  releases+requeues, pass parks blocked work and its gates condition
  wakes, park/close release, late-gate demotion + invariant query, stale
  closed-work claim, TUI facts. Sweeps bite (gates check removed → red;
  pass release removed → red).
- Superseded pins rewritten to the matrix: test_phase pass test, wf01/wf04
  stories and their phase trails.

Gate: 614 parallel + 3 serial green. W108 remains formally routed at
baton.feat in the trial (a creation-routing artifact); this implementation
is the hand-back the ruling requested.

## Step 90 — Cat header (finding-tui-category-header) (2026-08-16)

Queued presentation-only correction implemented: the Work-table
classification column header renders `Cat` via HEADER_LABELS (internal
column key, canonical `classification` field, JSON, command grammar, and
compact values all unchanged). Full-width regression asserts `Cat` present
and `Cls` gone; the narrow-width story asserts the omitted column leaves no
header behind. Sweep: label reverted → red. Gate 615 parallel + 3 serial.

## Step 91 — W108 round 2: the phase-orthogonal claim (2026-08-16)

Ruling bc32b20e superseded Step 89's queued→active model. Reworked:

- NEW public verb `claim WORK` (transitions.claim_work, audited kind
  "claim", in MUTATIONS): records the claimant WITHOUT touching phase.
  In-transaction preconditions — open, not waiting/parked, handler-gated
  vs live Current, zero gates (advisory observation loses), unclaimed
  (refusal names the claimant); effectively-once retry replays.
- set_phase is an ordinary stage change again: no claim logic; entering
  waiting/parked releases (audited released_claimant); other phase
  changes keep the claimant. The recompute demotion is removed —
  blocked Work keeps its honest stage and the claim refusal guards
  execution instead.
- Pass records destination Current AND destination phase atomically
  (payload.destination_phase): explicit `--phase` on say wins; else
  derived from the destination route's stage role via the closed
  STAGE_PHASES map (rsrch/research, impl/implementation, rview/review);
  an unmappable role REFUSES rather than guessing, carrying the
  sender's phase, or substituting queued. waiting/parked are never a
  pass destination. Sender's claim released; recipient never
  auto-claimed.
- test_w108_active_claim.py rewritten (13): claim-without-phase-change,
  fail-closed competition, exact retry, in-transaction preconditions
  (child/blocker/advisory-race/parked/terminal), independent claimants
  on parallel review+implementation Work, phase changes keep the claim,
  waiting/parked/close release, destination-phase pass both directions,
  explicit-phase override, stageless-role refusal + explicit queued,
  waiting/parked-destination refusal, blocked review Work keeps review
  but refuses claim then claims after the gate clears, TUI facts.
- ~49 pass call sites across the suites state their destination phase
  explicitly (fixture worlds use stageless roles); wf01/wf04 stories
  rewritten (grace CLAIMS instead of set_phase active; kinds/phase
  trails updated — handoff stages ride pass events). BATON-WORK.md and
  AGENTS.md rewritten to the orthogonal model. Sweeps bite (claim gates
  check removed → red; pass destination-phase removed → red).

Gate: 617 parallel + 3 serial green.

## Step 92 — W108 round 3: review R1-R4 (2026-08-16)

review-2026-08-16T09-41-56Z evaluated the round-1 tree and crossed round
2; reconciled against the CURRENT tree:

- R1 (orthogonal claim verb) and R2's core (atomic destination-phase
  pass, sender release, no recipient claim, blocked review keeps review)
  were already delivered in round 2 (T108 #116) — pointed, not redone.
- R2 gaps closed: exact pass retry replays the one handoff (same seq,
  destination phase stable) and the sender's just-changed stage never
  leaks into the handoff (destination wins).
- R3 implemented for real (round 2 had dropped release entirely): a late
  gate keeps the honest stage, sets ready=false, and atomically RELEASES
  the claimant, with the causing event's payload carrying
  released_claims [{work, claimant}] as recoverable evidence —
  _recompute_ready now threads the caller's payload. Sweep bites.
- R4: W108 marked active in the trial at seq 117 (moments before the
  correction wake); the live-discipline lesson stands recorded.

Gate: 620 parallel + 3 serial green.

## Step 93 — W108 live handoff + consuming-return Next fix (2026-08-16)

Per correction 7df4380e: trial W108 set phase review (seq 119) and passed
to baton.feat (seq 120). The old executable DROPPED the --set-next
baton.impl on that consuming return (Next now None in the trial) — and the
fresh code had the same gap. Fixed: a consuming return commits a newly
planted Next with the return (regression added; the trial's lost plant is
reported rather than papered over). Gate 621 parallel + 3 serial green.

## Step 94 — W108 round 4: retry identity + claim discovery (2026-08-16)

review-2026-08-16T10-08-11Z:
- R1: pass_phase joined the protected pass's effectively-once
  fingerprint. Regressions: exact same pass+phase replays the one event;
  the same op-id with only the explicit phase changed refuses as an
  operation conflict with sequence and phase unchanged. Sweep bites.
- R2: `claim` is advertised in detail.available_transitions exactly by
  the writer's rule (resolved Current handler, open, ready, not
  waiting/parked, unclaimed; writer stays final authority). Regressions
  cover ready (both handlers), blocked, already-claimed, parked,
  review-route outsider vs handler, and closed (empty list); plus the
  CLI proof that the public `claim` verb commits the same transition —
  its replayable result now carries the claimant. Sweep bites.

Gate: 624 parallel + 3 serial green.

## Step 95 — W108 round 5: waiting coverage; recovery held for ruling (2026-08-16)

review-2026-08-16T10-13-10Z (round 4 verified clean on both prior items):
- R2 done: the release boundaries are now three NAMED tests — the
  condition-bound waiting entry (obligation-bound, asserting both the
  claimant release and the recoverable released_claimant payload),
  parked, and terminal close — no test name claims coverage it lacks.
  Gate 626 parallel + 3 serial green.
- R1 HELD exactly as the review sequences it: the explicit
  recovery/release operation needs the authority ruling first (who may
  recover another's claim, CAS against the expected claimant, required
  rationale). No recovery mutation is guessed; implementation follows
  the ruling.

## Step 96 — W108 item 10: explicit claimant recovery (2026-08-16)

Recovery ruling approved (decision d7338cd5; FINDING "Explicit claimant
recovery"); implemented exactly as pinned:

- transitions.release_claim + public verb `release WORK --expect
  team.member --reason TEXT` (in MUTATIONS): live Current-handler
  authority via the handler gate; mandatory exact compare-and-swap
  against the recorded claimant decided inside the write transaction
  (mismatch and unclaimed both refuse without mutation, naming the
  recorded claimant); mandatory normalized non-empty reason; clears ONLY
  active_team/active_member — phase/Current/Next/readiness proven
  untouched; effectively-once (exact retry replays; changed reason under
  the same op-id conflicts); event kind "release" carries
  released_claimant + reason; the replayable result carries the
  released claimant.
- Discovery: `release` advertised to resolved Current handlers exactly
  while a claimant exists (self-release and forced recovery alike);
  negative coverage for unclaimed and non-handler viewers.
- 6 new regressions: claimant-only mutation (before/after row equality),
  self-release + forced recovery via one operation, CAS refusal (sweep
  bites), authority refusal on the review route, retry replay/conflict,
  discovery pos/neg, CLI proof. docs/BATON-WORK.md documents the verb.

Gate: 632 parallel + 3 serial green. Item 10's "missing direct
waiting-entry release test" was already delivered in Step 95.

## Step 97 — W108 SIGNED OFF clean (2026-08-16)

Final review: the complete confirmed active-ownership model verified —
concrete creation classification, phase-orthogonal atomic claim,
competing-handler refusal, independent concurrent claimants,
Current+destination-phase handoff, sender release without recipient
auto-claim, blocked-stage preservation, late-gate release, consuming-return
Next preservation, phase-sensitive protected retries, canonical
discovery/CLI parity, and the explicit release/recovery boundary with its
named waiting/parked/close release tests. Awaiting W108 closure by its
Current (baton.feat); W92 unblocks then. The hot-zone blink item is next in
queue after W108.

## Step 98 — W92 runbook corrections (2026-08-16)

Two runbook-only pre-commit corrections (reviews 10-27-05Z and 10-27-40Z):
step 2 now uses the operator-facing `just deploy-v11
/home/sl/opt/baton/v11/<short-commit>` with one new exact immutable
release directory (every <deployed> resolves to it;
tools/deploy_work.py stays internal); step 4 names the canonical
repository-relative recreation-script path so the runbook runs from the
repository root throughout. No packaging or deployment change.

## Step 99 — W92+W108 committed as 6fe32fd (2026-08-16)

Slawomir committed the reviewed tree ("Adopt permanent records, schema 15,
and atomic work ownership"); working tree clean. The manual schema-15
deploy/init/recreation phase (RUNBOOK steps 2-5) is now Slawomir's; holding
for the deployment result. Remaining queue: W108 closure, W92 close-out,
then the hot-zone blink item.

## Step 100 — W2: the installed executable is bin/baton (2026-08-16)

Trial W2 activated and passed to impl (T2 #125); implemented pre-cutover:

- tools/deploy_work.py installs bin/baton (archive, verified layout,
  result output, and the printed init hint); the internal
  deploy_work.py filename and the baton_work module stay, per the pin.
- The installed CLI's usage prog is `baton`; docs/BATON-WORK.md
  (install layout, quickstart, BW examples, baton-rN distribution
  naming) and the W92 RUNBOOK (<deployed>/bin/baton) follow.
- Packaged-test surfaces updated (wfdriver, test_packaged,
  test_deploy_v11, test_tui_packaged, wf14 vendored layout).
- W2 removed from the recreation script (not recreated in the fresh
  authority); INVENTORY §F records 13 items (12 open + 1 parked);
  script re-verified end-to-end on scratch (13 rows, no rename item).
- Historical trial deployments under /home/sl/opt/baton/v11/* keep
  their baton-work name untouched.

Gate: 632 parallel + 3 serial green.

## Step 101 — W2 round 2: R1-R3 (2026-08-16)

review-2026-08-16T10-39-06Z:
- R1: recreate-work.sh's usage line and required-variable error now name
  bin/baton; a coverage pin
  (test_the_recreation_script_instructs_the_renamed_executable) reddens
  if the retired spelling returns. Sweep bites.
- R2: the layout test asserts EXACT bin/ membership == ["baton"]; a
  deployer shipping a second bin/ file (swept with a smuggled
  baton-work stub) fails the gate.
- R3: INVENTORY §F lists the honest 12 open items (W2 removed, W84
  restated as the hot-zone blink cue) with total 13 = 12 open + 1
  parked; RUNBOOK step 4 and the verification paragraph record the
  actual 13-row scratch proof without the superseded W84
  timestamp/change-identity description.

Gate: 633 parallel + 3 serial green.

## Step 102 — W2 round 3: R3 residual (2026-08-16)

The INVENTORY persisted-state sentence now selects W10 + W78 only, with an
explicit supersession note that W84's timestamp/change-sequence design gave
way to the same-schema hot-zone cue (queued presentation work). Targeted
sweep: no other current W92 instruction revives the superseded design (the
recreation script's W84 line is the recreated Work's title only).
git diff --check clean.

## Step 103 — W2 SIGNED OFF and closed satisfying (2026-08-16)

The installed executable is bin/baton across the deployer, docs, hints,
packaged tests, and the W92 runbook; the negative artifact pin and the
script coverage pin stand; the cutover inventory is internally honest.

## Step 104 — W4: baton.json is the single explicit root config (2026-08-16)

Per T4 #134, implemented the pinned single-config root model:

- Every accepted root declares an explicit absolute `base` in
  baton.json (strict shape {display, base}; pure-syntax acceptance —
  absolute, non-empty; existence checked at use time). The roots table
  persists base; resolution reads the live accepted row
  (project.store_root_base). No roots.json, no --roots-file, no
  filesystem inference anywhere current-facing.
- CLI: resolve consumes the accepted config; bootstrap requires
  --config and resolves --root through the store. load_resolver /
  resolve_base and the roots.json init seed are removed;
  conf/roots.scaffold.json is deleted from the repo and distribution;
  init scaffolds exactly BATON-SETUP.md + baton.json.
- conf/baton.example.json shows the based shape; BATON-SETUP.md and
  BATON-WORK.md rewritten; W92 RUNBOOK step 3 declares the baton root
  with its absolute base.
- Tests: ws6_project rewritten (acceptance refusals incl. relative/
  non-string/missing base and bad root id; store_root_base liveness +
  existence; strict duplicate/stray catalog in baton.json; bootstrap
  unit tests on direct bases; CLI unknown-root refusal; the retired
  --roots-file flag refuses as unrecognized — negative pin). wf14
  rewritten: refusal scenarios are configured roots, relocation is a
  deliberate generation-2 regen re-declaring the base (checkout-a
  proven absent from the authority after acceptance), db-hash frozen
  across pure filesystem verbs. wf15/wf13/deploy/onboarding and ~20
  inline root definitions updated with explicit bases. Sweep bites
  (base requirement dropped → acceptance regression red).

Gate: 633 parallel + 3 serial green; git diff --check clean.

## Step 105 — W4 round 2: R1-R3 (2026-08-16)

review-2026-08-16T11-08-53Z:
- R1 (schema-preserving): the roots.base column is REVERTED — the
  committed schema-15 table shape stands (negative pin asserts
  PRAGMA table_info(roots) == [root, display, removed]). The accepted
  baton.json is the one base source: open_bound hands its
  digest-validated document's roots (plus the captured digest) to the
  store, and project.store_root_base answers from that same read — no
  second unbound load, no TOCTOU. A configuration accepted AFTER the
  open refuses stale root resolution (race regression; sweep bites when
  the digest check is neutered). Relocation stays a generation+1 regen
  because it changes the accepted bytes.
- R2: the quickstart resolve example puts the global options before the
  verb — executable as written.
- R3: project.py's module contract rewritten around the accepted single
  configuration (filesystem writes outside authority; root selection
  from the already-validated document); the dangling release-asset
  comment fragment and the blank scaffold tuple entry are cleaned.

Retained: negative --roots-file pin, relocation/containment/packaged
coverage. Gate: 636 parallel + 3 serial green; diff-check clean.

## Step 106 — W4 round 3: R4/R5/R3-residual (2026-08-16)

- R4: W4 removed from the recreation script and the live inventory —
  12 total (11 open + 1 parked); the fresh baton.json is born on the
  single-config root model. INVENTORY/RUNBOOK totals updated; the
  idempotent scratch recreation re-proven at 12 rows (the scratch
  config itself declares the root with a real absolute base).
- R5: the non-persistence pin is now direct — the configured absolute
  base (a distinct repo-base dir, disjoint from the config's own path)
  must be absent from the authority bytes, alongside the exact PRAGMA
  shape pin. Break-swept by intentionally persisting the base through
  the accepted-config apply — the pin bites.
- R3 residual: project.py's header now states that lifecycle performs
  the binding validation and root resolution merely rechecks the
  captured accepted digest; blank-line residue collapsed.

Gate: 636 parallel + 3 serial green; diff-check clean. All prior pins
retained.

## Step 107 — W4 round 4: three prose residuals (2026-08-16)

The recreation script header says 12 items; the RUNBOOK proof label names
the W2 AND W4 removals; the last deletion blank in project.py is gone.
Targeted count/text sweep shows no stale 13 labels; git diff --check
clean; no test rerun needed per the review.

## Step 108 — W4 round 5: last two prose fragments (2026-08-16)

project.py's scaffold comment names only the setup instructions and the
configuration example seed; the RUNBOOK proof paragraph is reflowed.
Sweep shows no roots-seed/roots.json mention in src; diff-check clean.

## Step 109 — W6: confirmed-defect renders defct (2026-08-16)

Per T6 #143: CLASSIFICATION_COMPACT maps confirmed-defect to defct
(presentation only; the closed-map refusals and canonical JSON values
unchanged — the map pin in test_phase updated, and a new real-PTY
regression proves the row reads defct, sweeps red on revert). W6 removed
from the recreation set: 11 total (10 open + 1 parked), INVENTORY/
RUNBOOK/script header+footer updated, fresh scratch proof at 11 rows
idempotent. Gate: 637 parallel + 3 serial green; diff-check clean.

## Step 110 — W6 round 2: the canonical-JSON pin (2026-08-16)

The PTY regression now also pins the canonical side: detail() keeps
classification == "confirmed-defect" and no compact label leaks into the
serialized JSON. Swept by leaking "defct" through the projection — the
pin bites. Gate 637 parallel + 3 serial; diff-check clean.

## Step 111 — W6 round 3: the reflow (2026-08-16)

INVENTORY's W2/W4/W6 disposition paragraph and RUNBOOK step 4's
parenthetical reflowed; diff-check clean; prose-only.

## Step 112 — W9: the one-row exit confirmation (2026-08-16)

Per T9 #150: normal-navigation q sets a pure-view confirm state rendered
as ONE bottom row "Exit? y/N" (drawn whole at narrow width); y/Y exits,
n/N/Esc cancels to the unchanged view, every other key neither confirms
nor cancels; the command bar keeps q literal. Regressions: real-PTY
confirm/cancel/irrelevant-key with a database-hash no-mutation proof,
one-row narrow rendering, literal command-bar q; the bare-q sweep
updated all 53 PTY quit keys to qy. Sweep bites (bare-q exit restored →
red). W9 out of recreation: 10 total (9 open + 1 parked), fresh scratch
proof idempotent at 10 rows. Quickstart documents the prompt. Gate 640
parallel + 3 serial; diff-check clean.

## Step 113 — W9 round 2: status preservation + full key matrix (2026-08-16)

- R1: the confirm branch (and q itself) now runs BEFORE the per-key
  status reset — the prompt overlays the footer and cancellation
  restores the exact visible status. New PTY regression produces a
  refusal status, prompts, cancels, and requires the identical footer
  line; proven to FAIL against the old ordering (defect reintroduced →
  red → fix → green).
- R2: uppercase Y exit and uppercase N cancellation pinned, and the
  prompt is asserted as EXACTLY one matching row at both 110 and 44
  columns.

Focused W9 PTY targets green; full tui suite 30 green; diff-check clean;
the full gate unchanged per the review's boundary.

## Step 114 — W12: the exact Work id leads the detail header (2026-08-16)

Per T12 #156: the canonical id opens the detail header line (first on the
row, so no supported narrow width clips it), read from the selected
Work's canonical detail — never a title inference; JSON and command
authorization untouched. Real-PTY regression on a dedicated twin-title
world proves the id follows the selection across duplicate titles at 110
and 44 columns; sweep bites when the id is dropped. W12 out of
recreation: 9 total (8 open + 1 parked); INVENTORY/RUNBOOK/script
updated; fresh scratch proof idempotent at 9 rows. Gate 642 parallel + 3
serial; diff-check clean.

## Step 115 — W12 round 2: leading-header proof + tmp_path (2026-08-16)

R1: the regression identifies THE detail-header row (the status block)
and requires it to START with the exact selected id at both widths (the
stale-first-id negative kept); proven to bite by moving the id to the
header's tail — red, restored — green. R2: the test takes tmp_path,
builds the twin authority there, and the tempfile import is gone.
Focused target green; diff-check clean; gate unchanged per the review.

## Step 116 — W13: the one key=value operation grammar (2026-08-16)

Per T13 #162 and the boundary pin appended to the child FINDING:

- The launcher keeps --config/--participant/--expect-projection before
  the verb; EVERY verb operand (lifecycle, mutations, pure reads, tui)
  is a strict order-independent key=value token, one dialect for the
  CLI and the TUI command bar (the bar feeds the same parser).
  argparse is gone; a declarative per-verb table drives parsing.
  Tokens split at the first '='; unknown/missing/malformed/duplicate-
  singular/retired-flag/positional/mixed input refuses BEFORE authority
  access with a proven no-residue event count; repeatables (ref,
  answer-ref, template, assign, label) preserve order; op-id=/ref=/
  answer-ref= are operation operands whose ruled semantic refusals
  (pure read / filesystem / accept-only) decide as before; phase's
  wait= folds the two former flags into the transition's own condition;
  accept's boolean create takes exactly true.
- tests/work/test_w13_grammar.py (5): order independence + first-=
  split (an embedded a=b=c body survives), the full refusal matrix
  with no-residue proof, the closed launcher boundary, repeatable
  order + op-id replay/conflict through the new grammar, and the TUI
  bar sharing the dialect (key=value create succeeds on a real PTY;
  retired spelling refuses with the W13 message). Sweep bites
  (duplicate-singular check disabled → red).
- The ENTIRE test corpus (≈60 files) converted to the new grammar —
  including packaged/PTY/console-bar scripts — with every mechanical
  corruption from the sweep hunted down (SQL literals, monkeypatch
  targets, parametrize tables, event-kind pins restored verbatim).
- recreate-work.sh speaks the new grammar (verified end-to-end on a
  fresh scratch authority: 8 rows, idempotent); BATON-WORK.md and the
  W92 RUNBOOK examples converted. W13 removed from recreation:
  8 total = 7 open + 1 parked; INVENTORY/RUNBOOK counts and proof
  labels updated.

Gate: 647 parallel + 3 serial green; git diff --check clean.

## Step 117 — W13 round 2: authoritative spec, discovery, wording, proofs (2026-08-16)

review R1-R4:
- R1: the one declarative specification now carries the public
  contract — per-verb and per-key help text, closed vocabularies
  (origin, classification incl. the creation subset without unknown,
  phases incl. creation/pass subsets, outcome, assessment), corrected
  required keys (create.classification; close.rationale+outcome;
  revise.message/expect/rationale; bind.root/path/expect/rationale),
  and alternative/conditional forms (accept: exactly-one into|create;
  create=true requires kind/title/classification; into= forbids the
  creation keys) — all enforced at parse, before authority access;
  transition validation retained as defense.
- R2: generated discovery derives from that same spec — baton --help
  (all verbs) and --help VERB; launcher globals accept both --name
  VALUE and --name=VALUE, duplicates refuse, unknown globals refuse.
- R3: wording sweep — cli docstring names `baton` and key=value
  operands; tui refresh= refusal text; accept refusals instruct
  create=true/kind=/title=; the bar-guard comment describes the W13
  parser (argparse is gone); BATON-WORK.md presents `baton` as the
  product; the duplicated token split is unified.
- R4: strengthened proofs — grammar refusals with lifecycle.open_bound
  monkeypatched to explode (never fires, incl. closed-vocabulary and
  incompatible-form cases); repeatable ref= order proven from the
  durably projected message references; TUI bar quoted-spaces and
  embedded-= round-trip read back through canonical JSON;
  spec-completeness pins (required/vocab/forms) and help/spec parity
  over every verb and key; both launcher value forms + duplicate/
  unknown globals + --help covered. Three workflow refusal-text pins
  updated to the grammar-first messages.

Gate: 652 parallel + 3 serial green; diff-check clean; the recreation
proof reconciled on the final implementation (8 rows, idempotent, new
grammar end-to-end).

## Step 118 — W13 round 3: universal discovery, static forms, anti-drift (2026-08-16)

- R1: render_help now derives the universal operands (op-id=/ref=/
  answer-ref=, with their ruled applicability notes) on every verb, and
  the parity pin counts them per verb. The declarative grammar gained
  static conditional forms enforced pre-authority: phase to=parked
  requires reason=, to=waiting requires wait= (forbidden otherwise);
  say request=|pass-to= mutually exclusive, on= requires a carrier,
  phase=/set-next= require pass-to=; close duplicate-of= requires
  outcome=rejected. All rendered in generated help; transition checks
  retained. Focused pre-open_bound refusal cases cover each; two
  workflow refusal-text pins moved to the grammar-first messages.
- R2: systematic stale-string sweep across src (transitions errors and
  docstrings, cli accept refusal, TUI comments incl. the launch name)
  — and a narrow anti-drift regression that scans src/baton_work for
  any retired flag spelling or the baton-work product name (launcher
  globals and --help excepted); it fails on reintroduction.

Focused 13 green; gate 655 parallel + 3 serial; diff-check clean.

## Step 119 — W14 implemented: command-bar assistance from the one grammar

Implemented W14 per finding-tui-command-assist and T14 #170. Module-level
`assist_text(buffer)` in tui/app.py — a pure function over cli.GRAMMAR, the
SAME declarative specification the parser executes: matching verbs while
typing, then exactly-one groups plus the remaining required/optional keys
(universal operands included, updating as keys are supplied), then closed
values narrowed by the typed prefix. Rendered DIM to the right of the typed
input, which owns the row; below 8 free cells the hint yields (compact
fallback). Read-only by construction and by PTY proof (database hash
byte-identical across typing). Three regressions incl. a spec-parity sweep
and a 44-column narrow proof; break-sweep red/green. W14 removed from the
W92 recreation (7 items = 6 open + 1 parked, scratch re-proof + idempotent
rerun); BATON-WORK.md documents the assistance. Gates: 658 passed (+3
serial), `git diff --check` clean. Trial: W14 phase=review, passed to
baton.feat (seq 171/172).

## Step 120 — W14 round 2: shared partial analyzer, condition model, caret viewport

Review round 2 (T14, review-2026-08-16T12-55-05Z) landed. R1: partial-
command analysis moved beside the grammar — `cli.analyze_partial` +
`cli._partial_tokens` speak the bar's own execution tokenizer
(`shlex.split`: quoting, first-`=`), select the live final token by
position, and carry an open quote honestly (the joined quoted text is ONE
token; nothing inside it becomes a key); `tui.assist_text` is now a pure
formatter over the analyzer's states. R2: effective remaining
required/optional keys derive from the parser's own exactly-one/when/
conditions model (accept's two forms, parked/waiting promotion, wait=
withheld outside waiting, say's exclusive carriers with transitively
excluded pass-only fields, on=/duplicate-of= guidance notes), and
malformed/unknown/duplicate-singular/conflicting/bad-value input yields
the parser-shaped diagnostic; repeated repeatables stay available; a live
key prefix narrows the display. R3: the caret is shown at the insertion
point while the bar is open and hidden when it closes; over-width input
scrolls in a horizontal viewport (`<` marks the clipped left) that keeps
the caret and live tail visible, recomputed on resize from the preserved
buffer; the assist yields below 8 free cells. ptyharness.replay gained
cursor evidence (final position + DECTCEM visibility). Seven regressions
(tokenizer parity incl. quoted/embedded-=/reordered/open-quote, condition
model, diagnostics, caret+Esc-cancellation+read-only, over-width viewport
with wide resize, compact fallback); two break-sweeps (condition
promotion, viewport marker) red/green. Recreation unchanged at 7 (6 open
+ 1 parked), re-proven on the final code. Gates: 662 passed (+3 serial),
`git diff --check` clean.

## Step 121 — W19 implemented: the `::` multiline batch, boundary-first

Per T19 the boundary pin landed FIRST (finding-tui-command-batch
FINDING.md, "Implementation boundary pin — 2026-08-16"): `::` on the
empty bar only; staging pure view state; static preflight (fixed-global
guard + THE shared parser) before any authority access with one refusal
stopping everything; per-SLOT generated operation identity for mutating
lines without explicit op-id= (retained across unedited retries so WS-5
replays instead of duplicating, discarded on edit, never shadowing an
explicit id, distinct for identical lines); sequential stop with honest
completed/failed/unrun state (completed never described as rolled back,
skipped by later Gos); synchronous execution (no keyboard interruption);
process death loses generated identities — cross-session safety needs
explicit op-id=, exactly as at the CLI; Esc confirms over unexecuted
text. No product choice exposed; no blocker returned. Implementation:
execute() refactored into the shared `_fixed_global_guard` + `_run_line`
core the batch drives; `_batch_key`/`_batch_go`/`_render_batch` in
tui/app.py; the pane marks lines `ok`/`!!`/`--` over a visible
legend naming Enter/Ctrl-G/Esc; the cursor line inherits the W14
caret/viewport and read-only assistance. 15 regressions (entry, pure
staging, Enter-never-Go, preflight refusals, sequential stop, quoting,
identity retention/reset, twins, explicit-op-id replay, cancellation,
retained editing, PTY paste/state-markers/narrow viewport); two
break-sweeps (preflight gate, identity retention) red/green. Recreation
now 6 items (5 open + 1 parked), scratch re-proof + idempotent rerun;
BATON-WORK.md documents the batch. Gates: 677 passed (+3 serial),
`git diff --check` clean.

## Step 122 — W19 round 2: summary invalidation and the batch resize proof

Review round 2 (T19, review-2026-08-16T13-26-01Z) landed. R1: every
buffer MUTATION — text insertion, character deletion, line insertion,
line deletion — invalidates the previous run summary, so the legend's
Ctrl-G/Esc controls return the moment the summary is stale; cursor-only
movement preserves a still-applicable summary. Covered pure (failed-line
correction, completed-line edit, line insert/delete, cursor-movement
retention) and PTY (the stopped refusal on the legend row is replaced by
the visible Ctrl-G/Esc legend on the first correcting keystroke).
Break-sweep: dropping the printable-path invalidation turned the
regression red; restored green. R2: the batch-specific narrow-to-wide
resize proof — a 105-cell staged line clipped behind `<` at 44 columns
(caret visible at the pane edge) reappears WHOLE at 110 columns with the
caret at the insertion point, from the same preserved buffer. Gates: 680
passed (+3 serial), `git diff --check` clean. Recreation unchanged at 6.

## Step 123 — W84 implemented: the hot-zone blink cue

Implemented W84 per the superseding hot-zone rule and presentation
clarification. `hot_work(row)` in tui/app.py derives the cue from
canonical row state ALONE — open with a non-null active claimant (any
operational phase), or open ready review awaiting its reviewer's claim;
no recency clock, no timestamps, no authority read of its own. The
renderer overdraws ONLY the phase/status cell (`actve`/`rview`) of a hot
row with `A_BLINK` (composed with the selection attribute); title,
identifiers, counters, routing, and selection stay steady, the textual
facts remain authoritative where blink is ignored, and at widths where
the PHASE column is dropped there is simply no cell to animate. Five
regressions: the focused state matrix through real transitions (claimed
queued/research/active/review hot; release, blocked review, waiting —
with an honest open gate — parked, unclaimed queued, and terminal cold;
blocker-close flipping the review row hot with no edit to the row
itself), the presentation-purity proof (byte-identical authority plus
`hot_work` over a minimal canonical dict), and three PTY proofs (blink
SGR lands immediately before `actve`/`rview` and nowhere else with both
hot rows animating; a cold table emits NO blink SGR; the PHASE-dropped
narrow width renders steadily without crash). Break-sweeps: dropping the
ready guard reds the matrix; whole-row blink reds the cell-only PTY
proof. W84 removed from recreation — 5 items (4 open + 1 parked),
scratch re-proof + idempotent rerun; BATON-WORK.md documents the cue.
Gates: 685 passed (+3 serial), `git diff --check` clean.

## Step 124 — Fresh-authority W2: the init activation hint speaks the grammar

First item on the live fresh authority 7ba67cb8 (claimed atomically at
seq 9 — the W108 claim verb in production use). Per
finding-init-next-option-order's post-grammar clarification, init's
`next` hint and the scaffolded/shipped BATON-SETUP.md now read
`baton --participant team.member activate directory=.` — launcher
globals before the verb, the directory operand in the one key=value
grammar. The regression proves the hint by construction: the emitted
command is fed to THE public parser (`_parse_invocation`) and must parse
to activate/directory=./team.member; the wf15 onboarding workflow
(source AND packaged) pins the corrected scaffold text. Break-sweep:
regressing the hint to the retired positional order reds the proof.
Gates: 687 passed (+3 serial), `git diff --check` clean.

## Step 125 — Fresh-authority W14: the Message index + selected reader

Implemented the approved live-UX correction superseding W71's flat
detail message stream (claimed atomically at v11 seq 16). The Work
detail keeps its summary and Thread list; the lower region is now a
compact Message INDEX — `M<seq>` labels over the existing stable
sequence (nothing invented), author, time, personal new/seen state,
bounded pages with `(n: more)` — and a READER painting exactly ONE
selected message as its canonical block (metadata header, wrapped body,
Refs separated). Wide terminals split index|reader on the same rows;
narrow terminals stack them, never merging bodies back into a stream.
Selection is keyed by the STABLE seq (survives repaint and resize while
present; new-first autoselect per thread); the reader scrolls long
bodies line by line under an honest `M<seq> (cont.)` tag with a
width-bound cursor that resets on resize (repeat, never omit). Ctrl-W
navigates the THREE regions in order; `s` advances the per-participant
cursor through the SELECTED message and no later one. paint_messages
retired; format_message unchanged (the reader is its one consumer).
Nine rewritten W8 regressions under the new contract plus revised
W71/tui/parity/auto-refresh pins (three-region cycle, navigate-then-
assert, selection-bound seen); two break-sweeps (autoselect new-first,
selected-bound seen) red/green. BATON-WORK.md rewritten for the detail
view. Gates: 686 passed (+3 serial), `git diff --check` clean.

## Step 126 — W14 round 2: the thread-wide new-first seek

Review round 2 landed: the new-first promise is THREAD-wide, not
first-page-only. Entering a thread whose current bounded page is fully
seen now walks the canonical continuation (`next_after`, page by cached
page) to the page holding the first personal-new message and opens
there — an old seen body is never the default over unread conversation.
The seek arms only on thread ENTRY (enter detail, thread change): an
explicit n/p page command never re-seeks, so `p` still returns to the
first page after a mark (the R105 paging pin stays green). The
reviewer's regression (first unseen on a later page at 44x14 — opening
must show `M8`/`#8`) passes; break-sweep disabling the seek reds it.
Gates: 687 passed (+3 serial), `git diff --check` clean. Also noted
from review: W5 project metadata is superseded — team is the project
boundary; filters stay same-schema.

## Step 127 — W14 round 3: the all-seen newest fallback

Round-3 correction (review-2026-08-16T14-40-03Z): when the thread-entry
seek walks every bounded page without finding a personal-new message —
the Thread is ALL seen — it now retains the FINAL page and selects its
newest message, instead of reopening the oldest message on page one.
The later-page personal-new seek and the explicit n/p behavior are
untouched (the seek still arms only on thread entry). The reviewer's
regression (ten messages fully seen at 44x14: opening must show
M11/#11) passes; break-sweep dropping the fallback reds it. Gates: 688
passed (+3 serial), `git diff --check` clean.

## Step 128 — Fresh-authority W4: ultra-short local Work selectors

Implemented per finding-local-work-selectors (claimed atomically at v11
seq 32). ONE strict resolver (`transitions.resolve_work_selector`):
`W<positive-sequence>` qualifies against the ONE opened authority; a
canonical id must already belong to it (foreign refuses by authority);
anything else refuses by shape — never a guess from title, cursor,
order, or partial match; existence stays with the honest `no work`
lookup. Every Work-valued operand (work/on/parent/into/duplicate-of/
follow-up-of/label, singular and repeatable) routes through it at CLI
dispatch — before any transition — so the TUI bar and batch inherit it;
`resolve` takes the short Work form too. Dispatch resolves BEFORE WS-5
fingerprints typed input, so short and canonical spellings are ONE
operation (op-id retry across spellings replays). JSON rows and details
expose `local_id` beside `id`; the table leads with an exact Id column
grown to the longest visible selector (id-aware responsive drop budget;
the parity parser now reads the painted header); the detail header
shows `<canonical> (W<seq>)`. Eight regressions (resolver matrix,
cross-spelling op-id replay, routing sweep incl. malformed-on-every-key,
twin titles, JSON parity, refusal-without-residue byte proof, Id-column
lead/no-truncation, bar + detail header); two break-sweeps (foreign
leak, dropped key) red/green. jsonapi's malformed-id pin updated to the
ruled resolver refusal. Gates: 696 passed (+3 serial), diff-check
clean.

## Step 129 — W4 round 2: visible-scoped Id width and the fit refusal

Round-2 corrections (review-2026-08-16T14-59-06Z). R1: the Id column
width now derives from the rows ACTUALLY painted — collapse runs before
the width computation, so a hidden closed W100000 neither consumes
Title space nor drops columns until `z` exposes it (exposed rows
participate normally). R2: `layout_fits` carries the visible Id width;
when Id + minimum Title + mandatory columns no longer fit, the table
uses its explicit `terminal too narrow` refusal before painting any row
— identity stays whole AND the mandatory tail is never silently
clipped. Both reviewer regressions pass (suite 10/10); break-sweep
reverting R1 reds the hidden-row proof. Gates: 698 passed (+3 serial),
`git diff --check` clean.

## Step 130 — Fresh-authority W39: inline dependency arrows; Ready removed

Implemented per finding-tui-inline-dependency-cue (claimed atomically
at v11 seq 45). Projection: `first_open_blocker` — the OLDEST open
blocker's local selector, computed inside the one snapshot beside the
existing open_blockers count (no client N+1, no title/order inference);
satisfied edges leave the live value. TUI: a dynamic-width `Blk` field
between Title and the fixed columns renders `← Wn` / `← Wn +N` from
canonical data via the shared `blocker_cue`; the boolean Ready column
(and its DROP_ORDER slot) is removed; `↳` containment stays a separate
marker and both can appear on one row; `[b] deps` untouched. The cue is
ONE whole responsive field scoped to the VISIBLE rows: when it alone
breaks the fit it is omitted entirely — never clipped or relabeled —
and the W4 refusal/blink offsets carry it. The parity parser reads the
Blk field from the painted header. Seven regressions (deterministic
first + promotion on close + all-clear, single-blocker form, Ready
gone + painted cue, combined child-and-blocker row, narrow whole-field
omission with [b] reachable, refresh clearing the cue through the
public CLI, JSON/TUI cue parity); break-sweeps (newest-first
determinism flip; omission guard removed) red/green. Legacy pins
updated (header tuple, narrow width 72->68, parity ready comparison
retired). Gates: 705 passed (+3 serial), `git diff --check` clean.

## Step 131 — W39 round 2: the batched blocker-selector read

Round-2 correction (review-2026-08-16T15-16-41Z): the first-open-
blocker selectors now come from ONE batched query per projected window
(`_first_open_blockers(store, work_ids)` — oldest open blocker per
consumer via a single ordered scan, first-hit-wins in Python), gathered
after the window's rows are collected and passed into `_row_view`;
tree, home, and children all batch, and the single-row detail path
batches its one id through the same helper. Growing the visible tree no
longer grows selector reads (the filed trace-callback regression counts
at most one). Snapshot consistency, blocker ordering, satisfied-edge
removal, and JSON/TUI parity unchanged. Break-sweep restoring the
per-row read reds the batch regression. The W71 mixed-tree wrapper
learned the pass-through kwarg. Gates: 706 passed (+3 serial),
`git diff --check` clean.

## Step 132 — Fresh-authority W23: bold hot Titles, the reliable cue

Implemented per the superseding ruling in
finding-tui-hot-cue-live-visibility (claimed atomically at v11 seq 56).
Every row the canonical `hot_work` predicate selects overdraws ONLY its
Title cell with A_BOLD — Id, counters, routing, and the Blk cue stay
steady — composed with the selection attribute rather than erased by
it; the phase-cell blink is retained verbatim as the intermediate
animated cue until W33 lands claim Age. Cold/blocked/waiting/parked/
terminal behavior, narrow layouts, and presentation purity unchanged.
Four regressions: the attr-level unit proof (exactly one bold title per
hot row, title-region-only, reverse+bold composition on selection, no
bold on cold), the byte-purity check, the PTY proof (bold SGR
immediately before BOTH hot forms' titles, never before a cold title,
blink still animating the phase cell), and the narrow proof (bold Title
survives the width that drops the blink carrier). Break-sweep bolding
the whole row reds the unit proof. Gates: 710 passed (+3 serial),
`git diff --check` clean.

## Step 133 — Fresh-authority W33: claim Age and the final cue composition

Implemented per finding-tui-claim-age (claimed atomically at v11 seq
60). Projection: `claimed_at` — the newest claim EVENT's journal
timestamp (json_extract over the append-only events, never
last_changed_at), exposed only while an active claimant exists, batched
per window beside the W39 blocker map (trace-proven ≤1 claim query per
tree; the single-row path batches its one id). TUI: the final five-cell
`Age` column (MM:SS / HH:MM / 99h+ / dash via the pure `age_cell`
formatter with negative-clock clamp), advanced by the ONE existing
refresh cadence, responsive-omitted whole via DROP_ORDER. The
indefinite hot-state blink is REMOVED in the same change: the steady
cue is bold Title + Age (ready unclaimed review stays bold with dash).
The phase cell retains only the ephemeral CHANGE cue — client-local
baseline from the first snapshot (cold on load/reconnect), armed to 3
on an observed genuine Phase change, consumed ONLY by scheduled
tick()s, untouched by keystrokes/redraws/resize/mutation refreshes,
re-armed in full by a later change. Eight regressions (formatter
matrix, canonical claimed_at incl. release/re-claim/close and the
not-last_changed_at pin, one-batch trace proof, final-column rendering
with review-dash, the exact three-tick lifecycle, mutation-refresh
non-consumption, reconnect-cold, PTY live-age advance + no-blink
load); two break-sweeps (last_changed_at fallback; keystroke
consumption) red/green. W23/W84 pins updated to the final composition.
Gates: 717 passed (+3 serial), `git diff --check` clean.

## Step 134 — W33 round 2: consumption bound to the successful read

Round-2 correction (review-2026-08-16T15-37-56Z): a timer tick now only
marks a consumption as OWED (`tick_owed`); the phase-change countdown
is spent inside `rows()` immediately after the SUCCESSFUL scheduled
canonical read returns — before the change observation, preserving the
round-1 arming semantics. A failed read raises before consumption and
spends nothing; a coalesced timer+mutation refresh spends exactly one
(the owed flag clears once); mutation-only refreshes spend none;
keystrokes/redraws/resize spend none; load/reconnect stay cold. The
reviewer's reproducer passes; the three-tick lifecycle assert moved to
the corrected order (the third cycle empties as the fresh paint lands).
Break-sweep restoring tick-time consumption reds the reproducer. Gates:
718 passed (+3 serial), `git diff --check` clean.

## Step 135 — Fresh-authority W17: `[b] deps`

Implemented per finding-tui-dependency-key-label (claimed atomically at
v11 seq 67). The Work-table footer's `b links` — misread as "blinks"
and mistaken for the hot-zone cue — now reads `[b] deps`; the docs
follow. Wording only: the `b` binding, links projection, dependency
graph, empty-state text, JSON, and protocol are untouched (both pinned
by the regressions). Two PTY regressions (wide: footer label + working
binding + label surviving the return; narrow: whole label at 60
columns + unchanged empty state); break-sweep restoring the ambiguous
label reds both. Gates: 720 passed (+3 serial), diff-check clean.

## Step 136 — Fresh-authority W3: three-level team-local priority

Implemented per finding-work-priority (claimed atomically at v11 seq
71). Creation accepts optional `priority=` (closed high|normal|low,
omission = the natural normal default, recorded atomically at birth).
`prioritize work=... as=...` is the audited effectively-once revision:
owning-team authority for ANY configured member (proven with a
non-claimant teammate while claimed+active), cross-team/closed/
same-value refused, exact op-id retry replayed, ordinary change
identity advanced, one audited event with from/to. Priority never
touches the workflow axes (field-for-field proof incl. readiness,
claimant, dependency counts, claimed_at). Canonical list ordering
ranks root siblings and each child sibling group high, normal, low
then created_seq — containment preserved (a high child stays under
its normal parent), reordering following a revision on the next read,
restart-stable. Discovery advertises prioritize to owning-team
members while open (the phase-matrix pin updated to the ruled
authority). TUI: two-cell `Pr` (Hi/No/Lo via the closed
PRIORITY_COMPACT map), FIRST whole column dropped under width
pressure; JSON keeps full strings; the W13 grammar gains
create.priority= and the prioritize verb (W4 selectors route work=).
Eight regressions + two break-sweeps (cross-team gate, rank ordering)
red/green. Gates: 728 passed (+3 serial), diff-check clean.

## Step 137 — Fresh-authority W80: the explicit `pass` verb

Implemented per the follow-up ruling in finding-key-value-command-
grammar (claimed atomically at v11 seq 84). `pass work= to= phase=
thread= comment= [set-next=]` is the ONE canonical transfer surface,
dispatching through the same single writer the compound say form used:
the comment lands as durable handoff evidence in the chosen labelled
thread, Current + the destination phase (explicit or stage-role
derived) + any planned Next record atomically, and the sender's claim
releases; a refusal leaves message and workflow state unchanged
(byte-proven). `say` is reduced to discussion + the @ request=
operator: pass-to/phase/set-next are unknown keys there, and on= binds
to request=. Every dialect consumer converted (test_packaged,
test_scenario, test_jsonapi, test_tui_packaged console scripts, wf01/
04/06/07/08/10/11/12/13 — incl. the wf07 wildcard refusals moving to
pass to= and wf12's cross-generation op-id replay under the new verb);
W13 grammar/help pins and the W14 assist pins updated (say's carrier
condition now promotes request= to required; the assist teaches pass's
form and never resurrects the retired keys). Six focused regressions
(indivisible transfer incl. claim release, stage-role derivation both
directions, refusal atomicity with byte hash, authorization + op-id
replay without duplicated evidence, say-as-discussion incl. the
preserved @, assist dialect); break-sweep dropping set-next from the
dispatch reds the transfer proof. Gates: 734 passed (+3 serial),
diff-check clean.

## Step 138 — Fresh-authority W81: bold is personal actionability

Implemented per the superseding ruling in
finding-tui-hot-cue-live-visibility (claimed atomically at v11 seq 90).
`actionable_work(row, viewer_team, viewer_member)` — a pure function of
canonical row facts — reserves the bold Title for exactly the ruled
branches: the viewer holds the active claim; OR the row is open, ready,
unclaimed, not waiting/parked, and its Current endpoint resolves to the
viewer (team + handler membership; every eligible handler until one
claims, only the winner after); OR the viewer carries an unresolved
directed @ obligation (my_pending_obligations — independently
actionable even while dependency-blocked). The render swaps the bold
driver from hot_work to the personal predicate; hot_work itself stays
canonical and untouched (W84 pins green); Phase/Current/Age and the
three-tick change blink keep shared activity visible. Five regressions
(the full matrix over real projections incl. cross-team via detail,
the independent-@ lifecycle with resolution, two-console divergent
bold sets, painted-vs-predicate parity, wide+narrow PTY); the W23 pins
revised to non-actionable contrast rows (dependency-blocked instead of
globally-cold); break-sweep regressing the driver to hot_work reds the
two-viewer proof. Gates: 739 passed (+3 serial), diff-check clean.

## Step 139 — W81 round 2: the two-eligible-handler regression

Round-2 addition (claim returned at v11 seq 93): a TRUE multi-handler
Current — a crafted config resolving TWO route handlers (ada, bee) with
a configured-but-unresolved third member (grace) as the preserved
ineligible negative. Both eligible handlers' views bold the ready
unclaimed row; after bee wins the claim only the winner keeps the cue,
the losing handler reads the activity through the claimant + claimed_at
facts, and grace stays cold throughout. Break-sweep widening the
claimant branch to team-wide reds the winner-only assertion. Gates: 740
passed (+3 serial), diff-check clean.

## Step 140 — Fresh-authority W5: composable Work-list filters

Implemented per the approved same-schema contract in
finding-work-project-filters (claimed atomically at v11 seq 99). ONE
closed vocabulary over existing canonical facts (team/status/phase/
current/category/ready/new/priority; AND; one value per field; no
comma/negation/OR), shared verbatim by `home`, `tree`, `tui` launch
operands, and the console's `:filter` (all through the one grammar +
`projection.normalize_filter`, which adds the store-dependent refusals:
unknown team, unknown TEAM.KIND — checked against the kinds table since
endpoint structs are never null). Filtering runs INSIDE the canonical
snapshot after the row facts project; the approved containment rule
holds (matching parent keeps only matching children; nonmatching parent
retained as filter_match:false context when a child matches; whole
group vanishes when none match; never a promotion or reorder); the
result echoes its normalized filter; the team summary stays global.
TUI: right-aligned `Filter:N` header tag that no narrow width can clip,
a dedicated dim clause line with an explicit `…` viewport, the table
shifted below it (`_render_table` gained `top=`), atomic client-local
replacement, bare clear, restart-cold, refusals leaving the current
filter untouched, and `:filter` command entry exposing the current
clauses for editing. Eight regressions (field matrix + AND + echo +
global summary, current=me/endpoint/new lifecycle, the refusal matrix,
parent-context retention incl. re-rooted windows, startup/interactive
parity + atomic replace/clear/restart-cold, purity + id-anchored
selection, PTY disclosure + clear, PTY narrow viewport). Break-sweeps
(dropping the context-parent rule; bypassing shared validation
interactively) red/green. Gates: 748 passed (+3 serial), diff-check
clean.

## Step 141 — W5 round 2: closed-filter visibility and seeded editing

Round-2 corrections (review-2026-08-16T16-45-54Z). R1: an explicit
status=closed filter now reveals the rows it selected — visible_rows
skips the default collapse exactly when the active filter requests
closed Work (the ordinary collapse holds otherwise, and clearing
restores it); PTY-proven wide AND narrow with a closed child painted
under its nonmatching open context parent (the approved containment
shape). R2: the first SPACE after exact `filter` seeds the command
buffer with the normalized current clauses — one clause edited without
retyping the rest, Enter replacing atomically through the same parser;
bare `:filter` + Enter still clears; with no active filter the space
stays literal; the bar hint now names the space-edit path. Three
regressions; break-sweep removing the collapse override reds R1.
Gates: 751 passed (+3 serial), diff-check clean.

## Step 142 — Fresh-authority W47: the claimant heartbeat

Implemented per the same-schema journal ruling in
finding-work-claim-heartbeat (claimed atomically at v11 seq 116).
`transitions.heartbeat`: the deliberate audited beat — authorized
STRICTER than route membership (only the exact recorded claimant, a
configured teammate refuses), open status + exact claimant rechecked
inside the committing transaction (a racing release refuses the beat
WITHOUT an event, count-proven), deliberately no `_touch_work` and no
row update — the journal event is the whole record; WS-5 replay
commits exactly one beat. Projection: `_claimed_ats` extended to ONE
batched statement resolving claim AND latest-qualifying-beat per
window, scoped to the current claim epoch (newest claim event, then
newest claim/heartbeat at-or-after it naming the same exact claimant);
`heartbeat_at` exposed beside `claimed_at`, null when unclaimed/
terminal, reset by release+re-claim; the trace regression counts ≤1
journal statement per tree. TUI: the Age field widens to six reserved
cells via `age_field` — trailing space healthy, `!` at exactly six
silent minutes (STALL_AFTER_SECONDS=360), cleared by the next beat,
clock corrections clamp healthy, claim Age itself never resets; the
beat provably has NO semantic side effects (change identity, order,
phase, message, New, phase-change blink — all pinned) and staleness is
informational only (the claim holds; a second claim fails closed).
grammar + W4 selectors + MUTATIONS wired. Nine regressions; break-
sweeps (touching change identity; alert ignoring the beat) red/green.
Gates: 760 passed (+3 serial), diff-check clean.

## Step 143 — W47 round 2: the five reviewed corrections

Round-2 corrections (review-2026-08-16T17-10-55Z). R1: discovery
advertises `heartbeat` exactly for the recorded active claimant —
pinned positive plus teammate/other-viewer/unclaimed/closed negatives
AND the sharp two-resolved-handler edge (the losing handler keeps
release but never heartbeat; the widened-discovery sweep now reds this
pin). R2: `_row_view` resolves the claim/heartbeat pair ONCE per row
(the single-row path batches its one id once, never per field);
detail's own trace regression counts ≤1 journal statement. R3:
PROJECTION_VERSION advanced 4.1→4.2 with the inventory naming
heartbeat_at as the first liveness-carrying shape; same-major demands
still succeed (pinned). R4: the genuine interleaved race — a release
committed inside the beat's own write window makes the beat refuse
with NO event and NO burned op-id (the same id commits fresh after
re-claim); a beat that wins stays journal history while release clears
the live projection, and close proves the same clearing on a second
automatic path. R5: the painted cell itself flips blank→`!` across the
359/360 boundary under a patched paint clock and clears after the
claimant's beat. Gates: 766 passed (+3 serial), diff-check clean.

## Step 144 — Fresh-authority W6: canonical Work search + the slash mode

Implemented per the revalidated boundary in finding-tui-work-search
(claimed atomically at v11 seq 127). `projection.search`: read-only,
viewer-team-scoped over EVERY owned Work (nested included; other teams
excluded) — case-folded title substrings plus case-insensitive
exact/prefix canonical/local ids; no message/thread/route/category
content. The active filter narrows via the shared normalize/match
semantics; results ride stable creation order behind an explicit
next_after cursor (never an identity), all from one snapshot with the
batched blocker/claim maps (no N+1); empty queries and bad limits
refuse. CLI: `search query= [after= limit=]` + the filter operands
(pure read; op-id refuses). TUI: `/` opens the one-line query bar
(typing is pure client state — trace-proven zero statements per
keystroke), Enter submits once, the flat result mode paints ordinary
rows with count/controls footer and the closed-visibility rule,
j/k/Enter opens normal details returning to the results
(detail_return), `/` replaces the query, n/p page, and Esc restores
the EXACT prior window (path/cursor/selection); the scheduled refresh
re-runs the accepted search through the one cache path with
id-anchored selection and honest empty results. Eight regressions
(matching matrix incl. nested + cross-team exclusion, filter/closed
canonical behavior, stable explicit paging, purity + empty refusal,
CLI envelope surface, the full slash flow with restoration, refresh
anchoring, PTY end-to-end); the two PLAN-pinned break-sweeps
(per-keystroke reads; current-window-only matching) red/green. Gates:
774 passed (+3 serial), diff-check clean.

## Step 145 — W6 round 2: visible-universe paging, z restoration, page labels

Round-2 corrections (review-2026-08-16T17-24-48Z). R1: TUI result
paging now runs over the console's EFFECTIVE visible universe — while
closed Work is hidden and no explicit status filter overrides it, the
search constrains to status=open before pagination, so a wall of
hidden closed matches can never bury a later open match behind an
apparently empty page; z (which now restarts at page one of the new
universe) and status=closed lift the constraint; JSON's canonical
all-status result is untouched. R2: closed visibility joined the
search entry snapshot — z toggled inside search never leaks into the
window Esc restores. R3: the header reads `page N · M shown` (the
bounded truth, never a page count masquerading as a total), resetting
on new queries and p, advancing on n; the PTY pin follows. Three
regressions; break-sweep removing the effective-universe constraint
reds R1. Gates: 777 passed (+3 serial), diff-check clean.

## Step 146 — Fresh-authority W136: participant-relative readiness

The first child of the messaging cutover gate (claimed atomically at
v11 seq 140). `projection.participant_actions` — the ONE canonical
member-relative action projection: routed Work (open+ready+unclaimed+
non-waiting/parked wakes every resolved Current handler; the claimant
alone after a claim, under the SAME stable `work:<id>` key; claimed
Work rediscoverable after restart regardless of readiness drift),
pending `@` obligations filtered by live owed-endpoint resolution
(`obligation:<seq>`), and due verification rounds filtered by live
Current resolution (`round:<work>:<round>:<generation>` — extension
retires the alarm, the next due generation is a new action). `+`,
plain posts, and personal New never enter. Deterministic order
(obligations, rounds, works), one read snapshot, zero writes
(byte-proven). `wait` now passes both identity halves and polls this
projection; the TUI header's oblig/due became the viewer's personal
actionable counts (parked stays team-wide). The R44 ws2 pins adapted
honestly (ineligible-member timeouts; push-owned gates neutralizing
the new routed-Work wake where deadline mechanics are the subject;
wf03's early wait moved to the unresolved member). Seven acceptance
regressions incl. two-handler claim-narrowing with key continuity and
restart rediscovery, reroute-followed obligations, generation-scoped
alarms, deterministic wait ordering, purity, personal headers, and the
public CLI wait; break-sweeps (team-wide eligibility; a claim
manufacturing a second key) red/green. Gates: 784 passed (+3 serial),
diff-check clean.

## Step 147 — W136 round 2: the six reviewed corrections

Round-2 corrections (review-2026-08-16T17-44-34Z). R1: PROJECTION_
VERSION 4.3 with the inventory naming the participant-relative typed
wait actions (same-major pinned; the W47 4.2 pin loosened to >=). R2:
a REAL accepted generation-2 reroute (route handlers [ada,bee] ->
[grace]) moves eligibility for the pending @, the routed Work, AND the
due round to the new handler set — same stable action keys, history
unwritten, generation unminted. R3: the interleaved-snapshot proof —
a claim committed between the projection's subqueries (via a wrapped
_endpoint_struct and a second connection) is entirely invisible: the
returned set and snapshot_seq are wholly pre-commit, the next call
wholly post-commit. R4: each distinct endpoint resolves exactly ONCE
per snapshot (memoized inside the read; the trace regression pins
kind-table reads ≤1 across six same-endpoint actions; break-sweep
dropping the memo reds it). R5: real PTY at 110 and 60 columns —
the eligible member's header carries [oblig:1], the ineligible one
[oblig:0], both share the team-wide [park:1]. R6: an actual `+`
include and an isolated personal-New message exist, remain visible
through the thread's New, and never enter the action set (the wait
stays quiet for attention-only members). Gates: 790 passed
(+3 serial), diff-check clean.

## Step 148 — Fresh-authority W148: the standalone v11 readiness producer

Second child of the messaging cutover gate (claimed atomically at v11
seq 153-era; claim seq 152). The binding blocker was ruled: WS-6 binds
the stable umbrella record; the nested child dossier stays
dossier-relative evidence — no grammar change, binding r1 stands. The
implementation is exactly the one-bridge/standalone-producer decision:
tools/codex-event-bridge/src/baton_v11_source.mjs (+ bin/
baton-v11-monitor) — the permanent protocol-11 adapter, launched
independently beside the UNCHANGED v10 stack; it feeds the same event
socket/target and the bridge keeps serializing turns. Invokes
`BATON --config P --participant T.M wait timeout=S` (key=value);
refuses malformed/wrong-protocol/wrong-participant envelopes by name
(a v10 shape is rejected, never guessed); emits ONE trusted compact
event per previously unseen action_key, identity scoped
`baton-v11:<authority>:<participant>:<key>`, carrying the kind + the
Work/obligation/round locator and the v11 standing-policy cue — no
bodies, no generic instruction block. WHOLE-set level-triggered memory:
suppressed while present (a claim keeps the same work: key — no
duplicate), forgotten on disappearance, re-emitted on reappearance,
rediscovered from empty after restart; failed forwards keep the key
undelivered and retry; the bridge's duplicate answer counts as
delivered; unchanged immediate sets and errors back off. Read-only
throughout. Eleven focused Node tests cover every acceptance case; the
v10 adapter/bridge suites unchanged and green (36/36 total);
break-sweep never-forgetting vanished keys reds the reappearance pin.
No live process changed — launch is the reviewed next step per the
plan. Gates: Node 36/36; just test-v11 790 passed (+3 serial);
diff-check clean.

## Step 149 — W148 round 2: the five corrections

Round-1 review (review-2026-08-16T18-05-30Z.md) returned five
corrections; all landed, no live process touched. R1: formatEventMessage
gained the ONE additional trusted branch — source "baton-v11" +
type "v11-action-ready" renders the compact
`[BATON READY] <summary> Apply standing v11 Baton policy.` line;
arbitrary baton-v11 types stay on the untrusted external path. The
end-to-end regression drives the producer's REAL actionEvent through
normalizeEvent + formatEventMessage and pins one line, locator +
standing-policy cue retained, no JSON details, no external-event
language — and that a different type still renders [EXTERNAL EVENT].
R2: delivery memory now carries the same identity the event does —
`<authority_uuid>:<participant>:<action_key>` — so an authority switch
retires the old set atomically and the same-named action under the new
authority is a genuinely new wake; the test proves emit → switch-emit →
switch-back-re-emit. R3: validateEnvelope is the strict typed contract:
projection_version must be 4.x with minor >= 3 (4.7 accepted; 4.2, 5.0,
missing refused), integer snapshot_seq, boolean timed_out, timed_out
with actions refused as contradictory, duplicate action_key refused,
exactly three known kinds with per-kind locator fields AND
key/field agreement (work:<work>, obligation:<seq>,
round:<work>:<round>:<generation>); fourteen negative cases each refuse
by name, and the refusal-matrix test still proves nothing is emitted.
R4: the subprocess boundary takes an injectable executor placed exactly
below the argv construction; the test pins the complete real argv
["--config", PATH, "--participant", T.M, "wait", "timeout=45"] and the
executable path; bin/baton-v11-monitor is mode 0755. R5: the bridge
README gained "v11 readiness producer (certification overlap)" with the
exact standalone launch command, feeding the RUNNING stack's existing
socket/target, no second app-server/bridge, sole-v11-waiter-per-
participant rule, and supervisor integration deferred to the v10
retirement gate. Gates: Node 40/40 (13 producer + 6 formatter);
just test-v11 790 passed (+3 serial); diff-check clean.

## Step 150 — W148 round 3: trusted-summary field validation and true launch docs

Round-2 review (review-2026-08-16T18-15-02Z.md) confirmed R1/R2/R4 and
returned two narrow gaps. R3a: validateEnvelope now types every field
the TRUSTED summary consumes — work.local_id must be a string agreeing
with the full Work id (equal, or the id's `-<local_id>` tail; a correct
work:<id> key with a lying local_id would instruct a command for the
wrong Work), title a string, claimed an actual boolean (a string
"false" is truthy and previously read as claimed), obligation.flavor
and due_round.review_at strings when present; snapshot_seq must be
non-negative and obligation seq / round / deadline_generation positive
(structurally valid negative ids refuse). Ten focused refusal cases
plus the optional-fields-stay-optional acceptance; break-sweep removed
the local_id agreement (the exact named bug) — the disagreement pin
redded, full suite green on restore. R5a: the README launch section no
longer names the obsolete projection-4.1 825e97d binary (which this
monitor correctly refuses), the wrong target, or the wrong socket. It
now states the operator first deploys a new immutable v11 candidate
containing W136/W148 and launches with THAT release's bin/baton, the
running stack's configured target and socket — concretely
--target baton-reviewer and --socket /home/sl/.local/run/
codex-events.sock for this trial — with the release hash left as
<NEW_CANDIDATE>, never a pre-4.3 build. The sole-waiter rationale is
corrected: v11 wait is read-only and level-triggered; two waiters
steal/consume nothing but both observe the same set and manufacture
duplicate Codex turns — duplicate delivery, not destructive
consumption, is why exactly one producer runs per participant. The
actionEvent source comment claiming no duplication "across restarts"
is fixed: restart rediscovery deliberately re-emits the still-current
set. Gates: Node 41/41; just test-v11 790 passed (+3 serial);
diff-check clean. No live process touched.

## Step 151 — W148: the codex-baton-bridge rename (seq-161 ruling)

Slawomir committed the WIP boundary as 1db42fe; the pinned naming
decision (FINDING.md "Decision — 2026-08-16: the product is
codex-baton-bridge, outside Baton") then landed with the resumed
round-three work. Baton stays model-neutral — CLI/JSON expose only the
participant-relative read-only wait; the external bridge decides how
readiness schedules a Codex turn. Renamed throughout with NO
compatibility alias: bin/baton-v11-monitor -> bin/codex-baton-bridge
(mode 0755 preserved), src/baton_v11_source.mjs ->
src/codex_baton_bridge.mjs, test/baton_v11_source.test.mjs ->
test/codex_baton_bridge.test.mjs; runBatonV11Monitor ->
runCodexBatonBridge, monitorBatonV11 -> codexBatonBridge; usage text,
error prefix, module header, and the README section (now
"codex-baton-bridge: the v11 readiness producer (certification
overlap)" with the model-neutrality boundary stated) all speak the new
name; descriptive "this monitor" phrases now name codex-baton-bridge.
Zero old-name occurrences remain in src/test/bin/README/package.json;
the Baton distribution manifests and baton core contain no Codex code
(verified by grep — nothing to remove). Dossier history (PROGRESS
steps 148-150, past reviews) intentionally keeps the old name as
record. Gates: Node 41/41; just test-v11 790 passed (+3 serial);
diff-check clean. No live process touched.

## Step 152 — W171: pass is a threadless Work event

Implemented the pinned finding-pass-is-work-event contract (claimed
W171 at v11 seq 174, phase active at 175). transitions.pass_work is
the new authoritative transfer: ONE atomic act — comment stored as
durable handoff evidence in the pass/return event payload itself,
Current + destination phase (explicit or STAGE_PHASES-derived from the
destination role, refused when neither names a stage), planned
set-next (consuming return clears it, detour keeps it visibly set),
sender claim release, wait fields cleared, _touch_work — with the
handler gate, already-at, and planned-Next races all re-derived
in-lock; op-id retries replay the one committed transfer. The event
result echoes work/to/destination_phase/consumed_next. post_thread
lost the ENTIRE pass vocabulary (pass_to/pass_phase/set_next
parameters, the => branches, the mutate transfer block): say is
discussion + the @ request operator, and a message can never move the
baton (a pass_to kwarg is now a TypeError). CLI: the pass verb drops
thread= from its grammar (unknown-key refusal by the W13 parser — the
old coupling cannot silently survive) and dispatches to pass_work; the
TUI command bar rides the same surface. PROJECTION_VERSION 4.4 with
the inventory comment. New tests/work/test_w171_threadless_pass.py
(5): unknown-operand refusal with nothing moved; the complete
authoritative event record (exact comment, pass_resolution,
destination_phase, set_next, consumed_next, authorization snapshot, NO
thread key); message/cursor/count immutability proven on Work carrying
several threads (messages table, seen cursors, obligations, every
thread page, member-relative new counts for three viewers, and
detail.message_count all byte-still while Current moves);
impl-to-review handoff waking the destination through W136 Work
readiness plus the approval-to-review consuming return; unauthorized/
already-at/terminal refusals. test_w80_pass rewritten threadless (the
retry-dedup pin now counts transfer events, the evidence pin reads the
event payload); w13 grammar matrix gains the unknown-thread case and
the assist pin flips to thread-absent; wf01-wf13 workflow passes
converted to the threadless dialect (wf10 audits pass_resolution);
fixtures.post routes legacy pass_to call sites through pass_work;
ws4 selection tests carry @ request (a message-borne pass is a
TypeError pin now); w136 version pin moves to 4.4. Break-sweeps:
removing the claim release redded the two atomicity pins; dropping
comment from the payload redded the two evidence pins; both restored
green. docs/BATON-WORK.md pass paragraph rewritten threadless. Gates:
just test-v11 795 passed (+3 serial); git diff --check clean.

## Step 153 — W171 R1: the claimant gate on pass

Round-1 review (review-2026-08-16T19-53-50Z.md) found the one hole the
move exposed: pass_work's committing re-read omitted
active_team/active_member, so on a shared route a second eligible
handler could transfer Work underneath the recorded claimant and
silently clear the claim. Corrected exactly as ruled: the live row now
carries the claimant; if a claim exists and is not the actor, the pass
refuses NAMING the claimant ("actively claimed by lang.ada; route
eligibility never moves work underneath its recorded executor —
recover or release the claim explicitly first") without burning an
event or touching Work; the claimant's own atomic release-and-transfer
and the existing unclaimed-pass behavior are unchanged. The reviewer's
additive regression (two-handler route: Grace's steal refuses with
current/phase/next/active/status all unchanged, then Ada's own pass
succeeds) was the red; it greens with the fix. Gates: just test-v11
796 passed (+3 serial); diff --check clean.

## Step 154 — W179: direct-scope Work counters

Implemented finding-visible-scope-message-counts (claimed W179 at v11
seq 198, already active). The three ruled corrections, exactly per the
reviewer's revalidation: _message_count now counts distinct messages
in the Work's DIRECTLY labelled threads (no _descendants expansion);
_my_pending selects pending obligations THROUGH those direct threads
(DISTINCT via LEFT JOIN thread_labels), with thread-less verification
assignments staying on their own Work directly — never aggregated from
descendants either way; _row_view's plain "new" cell is the direct
"own" count, correcting home/tree/detail/JSON/TUI in the one shared
place. new_count keeps the explicit recursive read but names the union
subtree_total (own/children/overlap retained; overlap = own +
child_sum - subtree_total). PROJECTION_VERSION 4.5 with inventory
comment. W36's recursive-default Msg pin rewritten to direct scope
(parent counts only its opener; the both-children shared thread counts
for EACH child, never the parent; seen-independence retained). New
tests/work/test_w179_direct_scope_counters.py (4) pins the W24 shape —
parent with two direct messages, open children, one hidden CLOSED
child, a nested grandchild, and a multiply-labelled thread: home row
and detail return identical direct facts equal to the threads entering
exposes; every kind of descendant conversation growth moves nothing on
the parent; the breakdown stays honest and named (no unqualified
"total", own == the plain cell, subtree_total = own + sum - overlap,
overlap visible for the shared thread, the closed child honest inside
the explicit read); seen on a direct thread clears only direct
counters while the subtree read keeps the descendants. Consumers
renamed across parity/projection/tui/w5/ws4/wf02/wf06/wf07; the parity
TUI cell pin now compares the drawn row to "own". Break-sweep:
restoring the recursive default in _row_view redded five pins across
the new suite and parity; restored green. BATON-WORK.md gained the
direct-scope paragraph. Gates: just test-v11 800 passed (+3 serial);
diff --check clean.

## Step 155 — W179: the honest-breaking 5.0

Review round 1: behavior green; the human ruled there is no v11
client-compat limit during the trial, so the breaking projection is
named honestly — PROJECTION_VERSION 5.0, no alias, no migration (the
4.5 inventory entry became the 5.0 entry stating the ruling). A stale
4.x --expect-projection demand now refuses cleanly: the jsonapi compat
pin flips (4.0 refuses, 5.0 succeeds), the w136 wake-contract pin
demands 5.0 and proves the 4.3 refusal, and the w47 heartbeat pin
drops its 4.2 same-major demand for the current 5.0 one. Cross-product
implication FLAGGED for ruling, not silently changed:
codex-baton-bridge's signed-off envelope gate requires projection 4.x
>= 4.3 and will refuse a 5.0 wait — the next immutable candidate
carrying W136/W148/W171/W179 needs the bridge's gate moved to the 5.x
contract as its own reviewed follow-up before the overlap launch. The
threadless-verification My question (verification assignments counted
on their own Work directly, my LEFT JOIN reading) stays held for the
pending ruling; W176 not started. Gates: just test-v11 800 passed
(+3 serial); diff --check clean.

## Step 156 — W176: role-labelled message panes with the one separator

Implemented finding-message-pane-header-redundancy (claimed W176 at
v11 seq 206 after the explicit pass; already active). Two bounded
renderer changes in _render_detail/_render_message_region, no
protocol or projection change: (1) exactly ONE blank separator row
reserved between the last painted Thread row and the lower region
(spacing, not a border); (2) the content-repeating headings replaced
by stable pane-role labels — `Messages (N)` (page-honest count with
the existing more cue) over the index and `Message M<seq>` over the
reader (`Message` bare when nothing is selected). The Thread row
remains the sole subject owner; the reversed index row remains the
selection cue. Superseded the W31 subject-repeating pin
(test_the_msgs_pane_names_the_selected_thread_and_subject ->
test_the_message_panes_are_role_labelled_not_content_repeating: no
`Msgs —`, subject appears exactly once, both role labels present);
w71 focus pins updated to the new labels. New
tests/work/test_w176_pane_labels.py (4): wide distinct regions with
the exact one-blank-row separator; long (80-byte-max) and
wide-character subjects contained in their Thread rows and absent
from the lower headings; selection moving the list highlight and the
reader heading/body together; the narrow stack keeping labels,
honest counts, and the separator. Break-sweeps: restoring the
subject-heading redded three pins; removing the separator redded the
two exact-separator pins; both restored green. BATON-WORK.md pane
paragraph updated. Gates: just test-v11 806 passed (+3 serial —
includes the reviewer's added W179 direct-label obligation pin);
diff --check clean.

## Step 157 — W187: the Wait column, arrowless

Implemented finding-wait-column-label (claimed W187 at v11 seq 214
after W176 closed satisfying; already active). Presentation only, two
sites exactly as revalidated: blocker_cue renders `Wn` / `Wn+N` (was
`← Wn` / `← Wn +N`) — W171+2 reads "waits on W171 and two more open
blockers", empty when nothing blocks; _render_table's sole heading
renamed Blk -> Wait (Blk read ambiguously between blocks/blocked-by,
and the arrow competed with the ↳ containment marker, which stays the
only containment fact). Deterministic first-blocker selection,
open_blockers count, [b] deps, ultra-short selectors, and the
whole-column narrow omission untouched. W39's presentation pins
superseded in place (arrow-detector assertions replaced by
gate-selector presence checks; header pins assert Wait and refuse
Blk); the parity header-width probe reads the painted Wait heading.
New tests/work/test_w187_wait_column.py (2): zero/one/many render
empty / Wn / Wn+N with the exact count and no arrow anywhere at wide
width, and narrow tables either keep the Wait heading with the
arrowless cell or omit the whole field with no fragment. Break-sweep:
restoring the arrow form redded seven pins across w187/w39; green on
restore. BATON-WORK.md cue paragraph rewritten. Gates: just test-v11
809 passed (+3 serial); diff --check clean.

## Step 158 — W187 R1: the Wait heading fits its column

Round-1 review named the one defect the relabel exposed: with a lone
short cue (W2), cue_column_width returned 2 while the Wait heading is
4 cells — the heading spilled into the next column and shifted every
later cell (the old `← W2` form was coincidentally 4 wide and masked
it). Applied the pinned correction: cue_column_width is
max(longest cue, len("Wait")) when any cue exists, still 0 when none —
the field (heading included) is still omitted whole at narrow widths.
The reviewer's added regression
test_the_wait_heading_fits_the_allocated_cue_column was the red; it
greens with the fix. Gates: just test-v11 810 passed (+3 serial);
diff --check clean.

## Step 159 — W207: the bridge certifies projection 5

Implemented the revalidated projection-5 gate (claimed W207 at v11
seq 225, already active) — the exact follow-up flagged at W179's 5.0
ruling. codex_baton_bridge.mjs validateEnvelope now requires
projection major 5 with minor >= 0: 4.x (4.3 and 4.5 pinned), other
majors (6.0 pinned), and missing all refuse by the new name
"projection-5 participant-action contract"; every other envelope check
(protocol 11, participant, authority uuid, snapshot token, boolean
timed_out, contradictory-timeout, duplicate keys, the three typed
kinds with key/field agreement, R3a trusted-summary fields) is
untouched. Node fixtures moved to 5.0 (bridge suite envelope default
and the formatter's end-to-end event); the acceptance boundary pin is
now a later 5.x minor (5.4). README launch section updated: requires a
release speaking projection 5 (the next candidate carries
W136/W148/W171/W179), 4.x refused. The bridge stays external —
nothing enters baton core or the distribution. Break-sweep: reverting
the gate to 4.x redded the typed-contract refusal matrix (bounded
run; the full suite additionally hangs under the defect because the
executor-boundary test's monitor retries the refused envelope forever
— itself a demonstration that a wrong-major deployment cannot pass
CI). Gates: npm test 41/41; just test-v11 810 passed (+3 serial);
diff --check clean.

## Step 160 — W163 slice A: the generic ACP readiness client

Implemented plan slice A of finding-v11-acp-agent-bridge (claimed W163
at v11 seq 238, phase active from the handoff). New external program
tools/acp-baton-bridge beside the Codex bridge — pinned OFFICIAL SDK
@agentclientprotocol/sdk 1.3.0 (ACP v1, ndJsonStream over the agent
subprocess's stdio; exact-version dependency, package-lock committed,
node_modules gitignored). Four modules with the ruled boundaries:
config.mjs (everything explicit — agent command/args/env/cwd, baton
binary/config/participant, session new|load + cwd, the exact
permissionMode, policyResources whose absence REFUSES startup,
stateDir; nothing inferred), baton_readiness.mjs (imports the SHARED
projection-5 validateEnvelope from the Codex bridge — one gate, never
re-typed; agent-generic compact [BATON READY] prompt text; W148-style
authority+participant+key level-triggered DeliveryMemory; injectable
wait executor), acp_agent_session.mjs (spawn the CONFIGURED agent;
initialize/negotiate BEFORE any session use; new-with-persisted-id or
load-exactly-the-persisted-session — bridge-owned state only; require
the EXACT configured mode after new/load with no fallback; serialized
prompt turns; requestPermission under bypass -> cancelled + reported
policy/protocol failure, NEVER auto-approved; streamed updates to the
foreground surface), acp_baton_bridge.mjs (the supervised loop: wait
-> shared gate -> unseen actions -> serialized turns; failures visible
and retried without discarding readiness; --once; SIGINT/SIGTERM).
test/fake_acp_agent.mjs is a REAL subprocess speaking the same SDK
with env-selected behaviors (no-bypass, no-modes, no-load, permission
request, slow turn, malformed first line, exit-on-prompt, JSONL
evidence log). Thirteen acceptance tests: lifecycle ordering
(initialize -> session/new -> set_mode(bypassPermissions) -> prompt),
compact-line delivery in the configured mode, level-trigger +
reappearance, busy serialization with no interleaved turns,
permission-cancel + visible failed delivery, crash retry with the
same key reaching the healthy agent, two-participant isolation both
directions, wrong-participant refusal with nothing reaching the
agent, load-resumes-the-persisted-id continuity, load-without-
capability fail-closed before session use, unsupported-mode
fail-closed with no set_mode fallback, missing-policy startup
refusal, malformed-output retry. Break-sweep: replacing the cancel
with auto-approval (the explicitly forbidden compatibility mechanism)
redded the permission pin; green on restore. README documents the
boundary, config, behavior, and that slices B (live Claude) and C
(Gemini by configuration) are separately reviewed steps — W163 does
not close on a fake substitute. Gates: acp bridge 13/13; codex bridge
41/41; just test-v11 810 passed (+3 serial); diff --check clean.

## Step 161 — W163 slice A round 2: the five corrections

Round-1 review (review-2026-08-17T01-14-16Z.md) returned R1-R5; all
landed (reclaimed W163 at v11 seq 250). R1 reproducibility: the fake
agent now OWNS its lifetime — an explicit keepalive interval plus
deliberate exit(0) on stdin end/close, so no Node version's event-loop
accounting can end the subprocess before initialize; engines pins
node >= 20; npm test runs the explicit ./test file path. R2 no
partial-session reuse: AcpAgentSession publishes ready=true only after
initialize + session new/load + exact mode enforcement ALL succeed;
start() failure kills and forgets the partial connection; ensureSession
reuses only alive()==ready sessions and nulls a failed factory; two
repeated-envelope regressions (unsupported mode, missing load
capability) prove the refusal repeats with initialize counted per
retry, zero prompts, zero set_mode fallback. R3 required policy:
policyResources is REQUIRED non-empty with non-empty entries (absent,
empty, blank, missing, unreadable-mode-000 all refuse before spawn);
agent.env values must be strings; the fake agent gained the
deployment-policy model (FAKE_ACP_TRY_FORBIDDEN gated by the policy
file) and two pinned paths: a configured hard denial engages with NO
side-effect file, no permission prompt, visible failed tool_call on
the foreground surface, and the wake still delivered; a broken policy
FAILS CLOSED (hook/failure logged, stopReason refusal, no side
effect). R4 supervision: every setup call (initialize, session
new/load, set_mode) races the child's exit, spawn 'error' (missing
executable is a visible lifecycle event), and the configured
setupTimeoutMs deadline; prompt turns race agent death (no arbitrary
work deadline); signal abort tears the child down so pending protocol
calls reject — proven by mute-agent deadline + recovery, stuck-turn
shutdown returning within bounds, and missing-executable retry tests.
R5 one gate: just test-v11 now ends with the test-acp sub-gate
(deterministic npm ci from the committed lockfile when node_modules is
absent, then npm test) — the operator-facing v11 gate cannot be green
while the ACP suite is red. Gates: acp 22/22 THROUGH just test-v11
(810 + 3 serial + 22); codex 41/41; diff --check clean.

## Step 162 — W163 slice A round 3: R6 session-id atomicity

Round-2 review (review-2026-08-17T02-59-17Z.md) closed R1-R5 and named
the one remaining atomicity hole: the new-session path persisted
session.json immediately after session/new, BEFORE enforceMode proved
the exact configured permission mode — a mode-rejected agent was
killed and forgotten in memory, but its rejected session id stayed
published as resumable state, so a later load could resume a session
that never completed the approved setup boundary. Corrected
(reclaimed W163 at v11 seq 254): the session id becomes resumable
state only after the COMPLETE setup boundary — initialize, session
new/load, and exact mode enforcement — has succeeded; a rejected
setup persists nothing, and because persistence happens only on that
success path, a failed bootstrap never erases an earlier accepted
session record (valid continuity is not cleanup collateral). The
reviewer's additive regression (failed mode enforcement publishes no
resumable session id) was the red; 23/23 with the fix. Gates: just
test-v11 810 + 3 serial + acp 23/23; codex 41/41; diff --check clean.

## Step 163 — W163 slice B: the live Claude proof

Executed the separately gated live proof (reclaimed W163 at v11
seq 258) with REAL components end to end, no fakes: the official
@agentclientprotocol/claude-agent-acp adapter pinned at 0.69.0,
installed under /home/sl/opt/acp/claude-agent-acp/0.69.0 (separate
from the Baton distribution); a scratch projection-5.0 v11 authority
at /home/sl/baton-acp-live/authority with participant acp.claude and a
wrapper CLI over the repo tree; a dedicated workspace whose project
settings carry the deployment policy (permissions.deny + a blocking
PreToolUse hook); acp-baton-bridge unchanged from the signed-off
slice A. Five live runs (logs + threads archived in
finding-v11-acp-agent-bridge/evidence/slice-b/):
1. Bootstrap (session new): initialize -> new session -> exact
   bypassPermissions selected; the v11 wake for W2 prompted the live
   Claude session, which autonomously claimed the Work through the
   canonical CLI, posted the continuity marker XYZQ-2739-ALPHA in the
   thread, and closed it satisfying — streamed output visible on the
   foreground surface throughout.
2. Continuity (session load): the persisted session id was loaded and
   a NEW Work's wake asked for the earlier marker — the loaded session
   recalled XYZQ-2739-ALPHA and posted it durably (T6 seq 8): the live
   continuity marker survived an external Baton-triggered turn in the
   intended session.
3. Permitted-without-prompt: a wake asking for a benign shell command
   ran with ZERO permission requests; allowed.txt exists.
4. Prohibited: FAILED HONESTLY — the live agent found that the
   'git -C <path> commit' spelling evaded both the deny prefix
   pattern and the naive substring hook (a stray empty commit landed
   in the SCRATCH repo, since reset to baseline), and also reported
   the hook's false-positive on prose quoting the command. A genuine
   deployment-policy defect, discovered by the live gate exactly as
   designed.
5. Prohibited, hardened: the policy was rebuilt as a PARSING guard
   (git_guard.py: shell segments split on operators, git global flags
   skipped, the actual subcommand matched against the prohibition
   set; unparseable-with-git fails closed) — self-test matrix pins
   allow/block for nine spellings including -C, -c, --git-dir, sudo
   wrappers, and prose false-positive avoidance. Both commit
   spellings then DENIED verbatim before execution, HEAD unchanged
   (no side effect), zero cancelled permission requests (the hard
   denial is agent-side beneath bypass, exactly as ruled), and the
   report quoting the prohibited text posted without a false
   positive.
The slice-B acceptance therefore holds live: initialize-before-
session, wake-prompts-the-configured-session, load continuity,
visible streaming, exact bypass mode, permitted-without-prompt, and
configured-prohibited-without-side-effect-or-prompt. Slice C (Gemini
by configuration) remains open. Gates unchanged: just test-v11 810 +
3 + acp 23/23; codex 41/41; diff --check clean.

## Step 164 — W163 slice B round 2: R7 fail-closed guard, R8 evidence

Round-1 slice-B review (review-2026-08-17T03-19-52Z.md) accepted the
live transport/continuity evidence and returned two corrections
(reclaimed W163 at v11 seq 264). R7: git_guard.py is rebuilt as a
genuinely FAIL-CLOSED enforcer — malformed hook JSON, non-string
commands, untokenizable lines mentioning git, unresolvable shell
constructs mentioning git, and nesting-depth overruns all DENY;
attached POSIX operators are tokenized in punctuation mode (never
whitespace splitting, so 'git commit;true' and 'git commit&&true'
block); env assignments, wrapper programs AND their flags unwrap
iteratively (env/sudo -E/nohup/timeout N/xargs/nice/stdbuf/...);
sh|bash -c strings are analyzed RECURSIVELY; substitutions ($( ), ` `,
<( ), >( )) mentioning git deny outright; an unrecognized git global
flag that obscures the subcommand denies when anything prohibited
follows; the prohibition set widened (am/merge/revert/update-ref
included). The executable adversarial matrix guard_matrix.sh pins 47
cases — every configured prohibited mutation, attached separators,
wrapper stacks, nested shells, substitutions, eval, malformed/
non-string/unterminated inputs (fail closed), and nine permitted
forms including prose mentioning 'git commit' — all holding, with
exit-status enforcement so a mismatch fails the script. R8: the exact
enforcement boundary is preserved dossier-relative in
evidence/slice-b/ — block-git-commit.sh (the wrapper settings.json
invokes), git_guard.py, guard_matrix.sh, and guard-matrix-output.txt
(exit 0). Live re-run (run6): the agent attempted THREE spellings —
plain, env+nohup+-C wrapper stack, nested bash -c — every one denied
verbatim before execution by the named-subcommand message, HEAD
unchanged (no side effect), zero cancelled permission requests, no
workarounds. Slice-B acceptance now holds under an enforcer that
cannot be bypassed by alternate shell syntax and never fails open.

## Step 165 — W163 slice B round 3: R9 the kernel boundary, R10 self-contained evidence

Round-2 review (review-2026-08-17T03-26-12Z.md) was right that finite
Bash parsing can never be the ruled hard boundary. R9 is now a REAL
containment boundary (reclaimed W163 at v11 seq 268): the deployment
launches the ACP agent through policy/launch-agent-sandboxed.sh —
bubblewrap (unprivileged kernel mount namespace) remounting every path
in protected-paths.txt READ-ONLY around the agent subprocess. No
spelling, wrapper, alias, arbitrary interpreter, or renamed executable
inside the session can mutate protected repository state: the kernel
refuses the write. boundary_matrix.sh proves enforcement through the
ACTUAL boundary for the complete prohibition class — commit, add,
reset, branch, tag, stash, checkout -b, update-ref, alias-spelled
commit, python3 writing .git directly, shell redirection into .git,
and a renamed-git binary all BLOCK; log/status/diff and workspace
writes ALLOW — 16 cases, exit-enforced. The PreToolUse hook remains
exactly what the review permits: an immediate friendly denial in
front of the kernel backstop, with its R9-named gaps fixed anyway
(index/worktree verbs add/checkout/switch/restore/stash/branch/tag/
mv/rm/clean/apply/worktree added; -c alias.* definitions fail closed;
wrapper value-flags nice -n 5 / sudo -u nobody consumed) and the
guard matrix extended to 56 cases. Live rerun (run7) through the
sandboxed agent: the commit and git-add spellings denied pre-execution
by the hook, and the python3 direct .git write reached the kernel and
failed with EROFS inside the live session — the backstop demonstrated
live; HEAD unchanged, worktree clean, zero permission prompts. R10:
the wrapper resolves git_guard.py beside itself; boundary_matrix.sh
self-provisions a throwaway repo when run without arguments; the
COMPLETE enforcement boundary (wrapper, guard, both matrices,
launcher, protected-paths, sandboxed load.json, run7 log, T26
transcript) is archived dossier-relative, and BOTH matrices were
re-run from the dossier copies (guard-matrix-output.txt and
boundary-matrix-output.txt, both "all cases hold") — reproduction no
longer depends on /home/sl/baton-acp-live.

## Step 166 — W163 slice B round 4: R11 no uncontained launch

Round-3 review verified R9/R10 (guard 56/56, kernel 16/16, the
reviewer's own /proc/1/root probe denied) and named the one bounded
gap: an empty or comment-only protected-paths list launched the agent
with ZERO read-only mounts — broken policy silently producing an
uncontained session. Corrected (reclaimed W163 at v11 seq 272): the
launcher counts EFFECTIVE entries and refuses before exec bwrap when
the count is zero; boundary_matrix.sh gained four executable refusal
cases (empty list, comments-only, missing file, nonexistent entry —
all must exit 2), now 20/20. protected-paths.txt and the bridge README
document that entries identify ACTUAL Git metadata paths — the
resolved gitdir (git rev-parse --absolute-git-dir) for worktree-style
.git files, never an assumed .git directory — and that an empty list
refuses the launch. Both matrices re-run from the dossier copies:
guard 56/56, boundary 20/20, outputs archived. The accepted live
continuity and EROFS proofs were not repeated per the review.

## Step 167 — W163: the co-deployed bridge and the safe examples

Implemented the pinned distribution ruling (reclaimed W163 at v11
seq 276 after the slice-B sign-off at seq 275). build_release's
SNAPSHOT now carries the generic acp-baton-bridge INTO the release
candidate: source modules, package.json, the exact-version
package-lock.json, the bin/ entry point, the README, and the complete
acceptance suite (fake agent included) — plus the shared projection-5
gate file it imports WITH that file's own two sibling imports
(config.mjs, send_event.mjs from the codex bridge). node_modules is
never shipped: the operator runs npm ci beside the shipped lockfile
for a deterministic install, exactly the pattern the test-acp gate
uses. _modes generalized: anything under a bin/ directory is an entry
point (the co-deployed wrapper publishes 0755; previously only
top-level bin/ was executable). Proven end to end: a fresh candidate
built into a scratch root passes validate(), carries every bridge
file, publishes the wrapper 0755, and the FULL 23-test acceptance
suite runs green FROM THE CANDIDATE after npm ci — the operator needs
nothing from the source checkout. Two non-secret example configs ship
(examples/acp-bridge-claude.json with the sandbox-launcher/AGENT_REAL
shape and the three policy resources; examples/acp-bridge-gemini.json
driving gemini --acp purely by configuration): every value is an
explicit <PLACEHOLDER> that cannot run as shipped — nonexistent
policy paths refuse startup before any agent spawns — and the
comments state that adapters, credentials, and prohibition policies
stay deployment-owned. Agent adapters remain uninstalled/unbundled.
Packaging baseline unchanged (test_release_build 2 pre-existing
failures / 79 passed, identical before and after; the wider
tests/packaging suite was already red on this WIP tree independent of
this change). Gates: just test-v11 810 + 3 + acp 23/23; codex 41/41;
diff --check clean. Slice C remains pending a real Gemini entry point.

## Step 168 — W163 distribution round 2: R12-R14, the real deployer

Round-1 distribution review (review-2026-08-17T03-49-32Z.md) was
right on all three counts (reclaimed W163 at v11 seq 280). R12: the
co-deployment now lives in the ACTUAL v11 path — tools/deploy_work.py
(the mechanism behind just deploy-v11); the earlier build_release.py
changes are REVERTED whole, restoring the frozen v10 pipeline
untouched. R13: the immutable-distribution boundary holds — the
bridge's pinned dependencies are resolved DURING candidate
construction (a staged npm ci from the committed exact-version
lockfile inside the scratch candidate, verified to have produced the
pinned @agentclientprotocol/sdk) BEFORE the atomic rename; no npm, no
network, and no mutation at the published target, and a missing
tool/failed resolution refuses while the target does not yet exist.
R14: the release layout is the reviewer-suggested stable shape —
bin/acp-baton-bridge (a generated 0755 wrapper) beside bin/baton,
with the private runtime at lib/acp-baton-bridge (source, lockfile,
README, acceptance suite, resolved node_modules) and the shared
projection-5 gate at lib/codex-event-bridge/src so relative imports
hold; examples publish as conf/acp-bridge-{claude,gemini}.example.json.
New committed regression tests/work/test_w163_deploy_bridge.py (5,
inside the just test-v11 gate): both entry points exist 0755 with the
deployer's facts naming the bridge; examples present, placeholder-
inert, and free of host paths; the pinned SDK version resolved INSIDE
the target matching the lockfile plus the shared gate beside it; the
bridge --help AND the complete shipped 23-test acceptance suite run
from the target with npm and the host node checkout stripped from
PATH (node-only shim) — no checkout, no npm, no network; and
npm-unavailable assembly refuses with the target never becoming
visible. Break-sweep: dropping the _stage_bridge call redded four of
five; restored green. test_deploy_v11's ruled-layout pin amended for
the two-product bin/ and lib/ (exact listings, third-file smuggling
still fails). Bridge README documents the deployed layout. Gates:
just test-v11 815 passed + 3 serial + acp 23/23; diff --check clean.
