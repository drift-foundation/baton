# Plan — recursive Work graph with tagged discussions

1. **Preserve the confirmed direction** — **done 2026-08-11** in `FINDING.md`:
   one recursive objective type, arbitrary-depth strict containment, typed
   non-containment edges, objective-linked discussions, goal roll-up, and
   bounded TUI focus with root/current breadcrumbs.
2. **Name the product boundary** — **confirmed 2026-08-11**: this is Baton
   2.0.0 and an architectural restart, not an incremental protocol-11 feature.
   Reuse is opt-in cherry-picking after revalidation; no 1.x workflow/schema/UI
   component is presumed to survive.
3. **Defer implementation until after the immediate release** — **confirmed
   2026-08-11**. This finding is not a 1.1 gate and does not authorize protocol,
   authority, CLI, TUI, migration, artifact, or deployment changes.
4. **Inventory reuse versus replacement** — later reviewer research: identify
   which 1.x integrity/content/publication primitives are architecture-neutral
   enough to cherry-pick, and which message/claim/readiness/TUI assumptions
   must be discarded. Revalidate every candidate; resemblance is not approval.
5. **Inventory protocol-10 assumptions** — later reviewer research: identify
   every message/thread/claim/readiness schema and CLI/TUI path affected by
   objective/discussion/tag routing, without changing source.
6. **Specify Work and collaboration vocabulary** — review `Work` as the neutral
   umbrella and the smallest honest milestone/finding/action model. Origin is
   immutable; classification is mutable; research is an operational phase in
   the confirmed intake example rather than origin or defect proof. A team
   groups leaf members; members hold roles; `@team.kind` is
   a public endpoint; and a route is the team's internal kind-to-role/handler
   mapping, not a workflow pipeline. Compact usernames remain separate from
   display names. Resolve handle grammar and protocol-10 migration together
   with stable Work ids, containment, ancestry, reparenting, and audit.
7. **Specify Work lifecycle and baton transitions** — expose type, status,
   progress, blockers, exactly one owning-team current endpoint and member
   handler, and an optional planned successor. External blockers are never
   additional current owners. A pass requires and atomically activates a
   successor; an authorized terminal close has none and propagates graph state. Resolve
   report/research/waiting-evidence/accept/reject/redirect/deduplicate states
   and dispositions, role-authorized classification transitions, explicit
   atomic classify-and-pass operations, policy-suggested successors,
   required/optional gates, reopen, and level-triggered readiness.
8. **Specify discussion, tag, and message semantics** — discussions are shared
   reusable conversations; `#WORK` supplies Gmail-like many-to-many context;
   `+team.kind` supplies optional inclusion, `@team.kind` creates a required
   response without changing Work ownership, and `=>team.kind` passes the one
   Work baton and changes `Current`. JSON uses structured operators rather than
   parsing glyphs. V11 has no standalone notice/broadcast object:
   announcements are ordinary discussion messages. Only `+` fans out: it may
   take comma-separated selectors or wildcards such as `+*.*`, with attention
   deduplicated per member/message. `@` creates one required response from one
   exact endpoint; `=>` passes one Work to one exact new Current. Neither
   accepts multi-destination or expanding-wildcard forms. Any future bulk
   required-response operation must expose the separate `@` obligations it
   creates. Resolve withdrawal of unresolved `@` obligations, selector
   expansion failures, route-tag lifecycle/return, follower promotion, unknown
   kinds, participating-team visibility, tag audit, per-member seen cursors,
   replies, artifact/review revisions, and retention.
9. **Specify the cross-team dependency web** — team-owned Work may link across
   teams and be drilled on demand without entering unrelated default tables or
   `New` counts. Define high-level external projection, N-to-one deduplication,
   provider-side convergence by applying one provider-local `#WORK` label to
   several consumer discussions while atomically creating separate explicit
   required edges. Work, links, and fan-in are deliberately discoverable by
   drill-through, browse, or search; team scoping is a default-view noise and
   responsibility boundary, never cross-team read access control. `#` never
   gates workflow; only the cycle-checked edge does. Define one-to-N terminal fan-out,
   multiple blockers, satisfying versus failing
   dispositions, global required-edge cycle checks, atomic relinking, reopen,
   and bounded one-hop/default navigation.
10. **Specify pinned finding binding and parallel evidence** — keep the Work
   as live workflow authority and the `work/finding-*` folder as rich Git
   dossier; define configured-root/path binding while open, optional origin or
   summary-message navigation pins that never affect delivery/FIFO state,
   tagged discussion evidence, final revision binding at closure, and
   healthy normal folder removal. Preserve promotion without Work
   replacement, idempotent handoffs, and the explicit no-Git-mutation boundary.
11. **Specify restart/replacement reconstruction** — define the minimum Work
    status projection and folder records from which a successor reconstructs
    outcome, rulings, evidence/assets, reviewed state, open dependencies,
    current endpoint/action, blockers, and acceptance gates; surface stale or
    contradictory sources explicitly rather than guessing.
12. **Prototype the bounded TUI information architecture** — **initial
    navigation ruled 2026-08-13**: open on a borderless fixed-width table of
    top-level Work; drill through immediate-child tables at arbitrary depth;
    preserve an ancestry breadcrumb; and show rows beginning with type,
    status, neutral title, progress, current
    endpoint/handler, optional next endpoint, and a
    participant-relative recursively aggregated numeric `New` counter. `New`
    counts discussion visible since that member's own seen position and never
    another member's state. Still resolve
    responsive column priorities, sorting, keys, dependency navigation,
    tagged discussions, acceptance inspection, and ordinary/narrow-terminal
    layouts through prototypes before implementation. Define the canonical
    versioned semantic projection at the same time: TUI and agent JSON consume
    the same rows, breadcrumbs, children, typed links, discussions, personal
    unseen and actionable state, readiness, and transitions. JSON retains full
    structured values, deterministic ordering, bounded pagination, viewer and
    snapshot identity, and never requires screen scraping. Add semantic parity
    tests between both presentations. **Sequencing ruled 2026-08-14:** first
    stabilize the authority, transitions, projection, and packaged JSON CLI
    through adversarial agent use; only then add the TUI and parity half over
    the frozen shared semantics.
13. **Define replacement/migration boundary** — decide whether and how 1.x
   traffic is imported, what clean authority 2.0 requires, and how old/new
   readers fail closed. Do not assume in-place schema evolution.
14. **Revalidate and seek explicit authorization** before any implementation.
    Append supersessions chronologically; do not infer decisions from the
    mailbox discussion alone.

`baton.implementer` creates and exclusively owns `PROGRESS.md` only when this
finding is explicitly selected after the immediate release.

## 2026-08-14 implementation-planning gate

**Confirmed by Slawomir.** The next step is an implementation plan, not source
implementation. `baton.implementer` owns a new
`IMPLEMENTATION-PLAN.md` draft in this finding and must first reread the whole
finding folder, revalidate its current rulings against the repository, and
distinguish chronological superseded material from the current plan.

The draft must turn the architecture into the smallest working vertical slice:
v11 authority/schema and stable ordering; Work/discussion/message/route
transitions; the shared canonical projection and versioned JSON interface; a
minimal TUI rendering of that projection; same-fixture semantic parity tests;
and an end-to-end create, include, request-response, pass, return, close, and
dependency-unblock scenario. It must identify module boundaries, serial steps,
acceptance evidence, failure/retry cases, migration or clean-start boundary,
and which later refinements are deliberately deferred.

K must not resolve gaps or contradictions by assumption. She reports each
blocking ambiguity through Baton with the conflicting text, concrete impact,
options, and recommendation so `baton.reviewer` and Slawomir can clarify it.
No implementation, `PROGRESS.md`, schema migration, or source/test edit begins
until the draft is reviewed, all blocking rulings are pinned, and Slawomir
explicitly authorizes implementation.

### 2026-08-14 rulings for the plan revision

Slawomir approved all four blocking review outcomes: version `11.0.0`;
six-cell wcwidth-validated canonical team/member/kind handles with unrestricted
display names and no v10 identity migration; re-readable messages with no
at-most-once delivery receipts; and an explicit idempotent seen-cursor
transition while ordinary reads stay pure.

K now revises `IMPLEMENTATION-PLAN.md` accordingly and reorders the slice into
two gates. Gate A delivers authority through packaged JSON CLI and passes an
agent-driven adversarial soak while v10 remains the coordination authority.
Gate B adds the TUI strictly over the stable shared projection and completes
same-fixture parity. This revision is still planning only; implementation
requires Slawomir's separate explicit authorization after focused review.

### 2026-08-14 delegated Gate A authorization

**Confirmed by Slawomir; supersedes the separate post-review authorization
sentence immediately above for Gate A only.** This message supplies conditional
implementation authorization and delegates its final gate check to
`baton.reviewer`. When K
returns the revised implementation plan, the reviewer performs one focused
check that all pinned rulings are represented, Gate A and Gate B remain
separate, acceptance evidence is executable, and no blocking contradiction or
unresolved product choice remains. If that check passes, the reviewer tells K
to proceed with Gate A without another Slawomir review.

The delegation does not authorize guessing through a newly discovered gap or
starting Gate B. Any material contradiction, new product tradeoff, scope
expansion, or decision not already pinned returns to Slawomir. Gate B still
requires its own post-soak review and authorization.

### 2026-08-14 Gate A verification entry point

- [x] `just test-gate-a` naming was proposed and immediately superseded; do not
  expose that recipe.
- [x] Provide `just test-v11` as the focused source-tree verification for all
  Gate A tests under `tests/work/`, including the adversarial soak.
- [x] Make `just test-v11` show individual pytest node IDs and use one xdist
  worker per CPU available to `nproc`; pin xdist in the dev environment.
- [x] Use the explicit `spawn` process context in Gate A concurrency tests so
  all-core xdist runs do not fork multithreaded workers or hide warnings.
- [x] Mark the three self-parallel Gate A tests `serial`; run all other v11
  tests with all-core xdist, then run the marked process workloads without
  xdist.
- [ ] Preserve `just build` followed by `just test` as the separate full
  candidate/release gate.

### 2026-08-14 Gate B authorization

**Slawomir authorized the next phase after Gate A commit `bed522d`; this
supersedes the earlier text that Gate B awaits separate authorization.**

- [ ] B1: render the canonical projection in the v11 TUI with real-PTY tests
  and no direct authority access.
- [ ] B2: run the shared fixture through JSON and TUI surfaces and require
  semantic parity for rows, counts, drill links, and actionable state.
- [ ] B3: run the ruled scenario through packaged artifacts rather than the
  source tree.
- [ ] Stop and return any missing semantic state or product contradiction for
  ruling before altering Gate A's shared projection contract.
- [ ] **BLOCKED ON SLAWOMIR:** rule whether viewer-relative reads validate a
  known member (recommended), require a separate `whoami` preflight, or accept
  an unknown viewer as an empty world. B2 may proceed; do not change the shared
  projection or resolve the strict xfail until ruled.

### 2026-08-14 configuration correction; Gate B paused

**Slawomir ruled that v11 requires a `baton.json` instance configuration,
superseding the narrow viewer-validation choice above. Gate B authorization is
paused until this foundational correction is planned, reviewed, and accepted.**

- [ ] Revise the implementation plan before more source edits: define the v11
  `baton.json` schema for protocol metadata, authority location, teams, roles,
  routes, participants/members, display names, and assignments.
- [ ] Use `mailbox/v11/baton.json` as the canonical deployed path; retain an
  explicit protocol declaration inside the document and refuse any mismatch.
- [ ] Remove `WORK.json` from the v11 design. Put the authority UUID/database
  identity in `baton.json`, persist the matching UUID and accepted config facts
  in SQLite, and define crash-safe generation-1 bootstrap.
- [ ] Specify which configuration facts are authoritative, what the SQLite
  authority persists/audits, how generation changes are accepted, and how a
  disagreement refuses without guessing.
- [ ] Restore the public protocol-10 vocabulary and launch boundary:
  `--config` plus `--participant`; remove `--viewer` as a separate identity and
  validate the configured participant before any output or curses startup.
- [ ] Model route resolution explicitly: public `team.kind` resolves through
  the receiving team's route configuration to a role and current handler;
  member authorship remains distinct from endpoint responsibility.
- [ ] Reassess Gate A tests and packaged JSON CLI against the corrected config
  boundary, then seek review before resuming Gate B.

### 2026-08-14 C1 authorization

- [ ] **AUTHORIZED:** implement and test the pure strict `baton.json` loader
  and schema using the approved first-class participant/route model.
- [ ] Validate roles on participant records and route handlers against those
  assignments; validate every kind's named route.
- [ ] Resolve only the fixed sibling `work.sqlite3`; put its authority UUID in
  `baton.json`; create/read no `WORK.json`.
- [ ] Stop after C1 evidence. C2 authority acceptance and generation lifecycle
  are not authorized by this C1 gate.

### 2026-08-14 C2 authorization — accepted

- [x] **AUTHORIZED:** implement crash-safe generation-1 initialization that
  binds `baton.json` UUID/digest/generation to sibling `work.sqlite3` and
  creates no `WORK.json`.
- [x] Implement the bounded generation+1 proposal path and atomic audited
  acceptance; ordinary open must continue to refuse unaccepted drift.
- [x] Project accepted teams, participants, roles, routes and kinds into the
  authority while preserving retired historical identities.
- [x] Authorize acceptance from the currently accepted generation only;
  proposals cannot grant their own acceptor.
- [x] Require generation bumps for handler reassignment and refuse proposals
  that strand open Work or pending obligations, naming affected records.
- [x] Remove superseded `WORK.json` creation/read code and tests.
- [x] Stop after C2 evidence. C3 and later correction steps remain held.

### 2026-08-14 C2 review — changes requested

- [x] Make generation-1 publication atomic create-if-absent so concurrent
  initializers produce one winner and cannot replace its authority.
- [x] Revalidate open Work and pending obligations inside the acceptance write
  transaction; the pre-lock query is not an authoritative stranding gate.
- [x] Preserve removed route handles as non-reusable historical identities.
- [x] Include route-role changes, not only handler-list changes, in the
  structural acceptance audit.
- [x] Re-run the focused lifecycle suite and `just test-v11`, then stop for C2
  re-review. C3 and later steps remain held.

**Accepted by `baton.reviewer` at 2026-08-14T14:47:06Z.** The focused suite
reports 19 passed; `just test-v11` reports 162 passed plus the one previously
held strict xfail. The C2 multiprocessing regressions and preserved Gate B PTY
tests still emit Python 3.13 fork-from-multithreaded warnings under xdist; C5
must include them in the already-ruled serial scheduling pass. This does not
change C2 authority semantics. C3 and later steps remain held pending the next
authorization.

### 2026-08-14 C3 authorization — accepted

- [x] **AUTHORIZED:** replace `--authority`/`--viewer` with
  `--config`/`--participant`, with no compatibility aliases.
- [x] Open ordinary CLI/JSON/TUI operations through `open_bound` and refuse an
  unknown configured participant before output or curses startup.
- [x] Wire generation-1 `init` to the config lifecycle and expose audited
  generation acceptance as `regen`, requiring the acting participant and its
  currently accepted `config` capability.
- [x] Remove `register-team`, `register-member`, `register-kind`, and
  `retire-kind`; configuration acceptance is the sole topology writer.
- [x] Keep transition and projection shapes otherwise unchanged. C4 route
  resolution, projection 2.0, C5 migration, and Gate B remain held.
- [x] Add focused CLI failure/success evidence for the changed boundary, run
  the relevant suite, and stop for C3 review.

### 2026-08-14 C3 review — changes requested

- [x] Require and validate `--participant` for every ordinary read as well as
  every mutation and TUI launch; `links`, `breadcrumb`, `discussion`, and
  `events` currently permit anonymous operation.
- [x] Remove the remaining public refusal wording that calls the acting
  participant a `viewer`.
- [x] Remove the always-true `assert database == path or True` from the shared
  fixture; assert the fixed-sibling invariant honestly.
- [x] Add the missing-participant read regression, re-run the focused boundary
  tests and `just test-v11`, then stop for C3 re-review. C4 remains held.

**C3 accepted by `baton.reviewer` at 2026-08-14T15:09:07Z.** Focused
boundary/TUI verification reports 13 passed; `just test-v11` reports 170
passed. The mechanical config-fixture migration required by removal of the old
CLI remains in this accepted step. The previously recorded C5 serial scheduling
cleanup is still outstanding.

### 2026-08-14 C4 authorization — released

**AUTHORIZED: C3 re-review is clean; no additional Slawomir gate.**

- [x] Resolve every endpoint use at commit time through the accepted route,
  recording endpoint, route, role, handlers, and config generation for Work
  creation, `+`, `@`, `=>`, and planned Next.
- [x] Preserve historical resolution snapshots across later config changes;
  obligations remain owed by the stable endpoint rather than a named handler.
- [x] Advance the JSON projection to 2.0, rename envelope `viewer` to
  `participant`, and expose structured endpoint values consistently in home,
  detail, links, Current/Next, and obligations.
- [x] Keep the compact TUI columns rendering `team.kind`; routing detail may be
  exposed in drill-in without changing responsibility semantics.
- [x] Preserve team-wide visibility/contribution. A route is accountable
  lookup, not exclusive authorization or a dispatch pipeline.
- [x] Add reassignment/history regressions and JSON/TUI parity evidence, run
  `just test-v11`, and stop for C4 review. C5/C6 remain separate.

### 2026-08-14 C4 review — changes requested

- [x] Move `+` wildcard/comma expansion and deduplication inside the authority
  write transaction so its membership and every recorded endpoint snapshot
  come from one accepted configuration generation.
- [x] Keep
  `test_include_expansion_uses_the_generation_at_commit` as the deterministic
  regression; moving expansion back before `_write` must fail it.
- [x] Re-run the focused C4 suites and `just test-v11`, then stop for C4
  re-review. The workflow-story phase remains queued until clean acceptance.

**C4 accepted by `baton.reviewer` at 2026-08-14T15:32:15Z.** Focused C4
verification reports 33 passed; `just test-v11` reports 174 passed (171
parallel plus 3 serial). The workflow-story phase below is now released as the
next serial item without another human gate.

### 2026-08-14 workflow acceptance suite

**PRE-AUTHORIZED ON CLEAN C4 REVIEW; BLOCKS HEAVY TUI WORK.** Once C4 is
accepted, the reviewer releases this phase without another Slawomir gate. Until
then C4 remains the serial item and this is preparation only. This supersedes
moving directly from C4 into C5/C6 or further Gate B implementation.

- [x] Review and implement the executable CLI/JSON spines of the graded
  end-to-end workflows in
  `WORKFLOW-TESTS.md`, from one-team report-to-close through cross-team
  convergence, recursive release gating, announcements, rerouting, restart,
  and races.
- [ ] Reuse one packaged-CLI process driver and the canonical projection;
  selected TUI checkpoints prove parity without making the screen an API.
- [x] Treat the coverage gaps named in that document as explicit scheduling or
  ruling inputs. Do not weaken a workflow to fit the currently implemented
  surface.
- [x] When a workflow discovers a defect, retain the workflow and extract a
  minimal regression for the first incorrect phase/transition. Link both ways;
  require both tests to pass before the defect is closed.
- [x] First produce a coverage/implementation pass over every workflow: mark
  what is already executable, what needs an engine/CLI/JSON operation, and what
  still needs a ruling. Sequence the missing semantic slices before adding new
  TUI behavior.
- [x] Stop for reviewer acceptance of the CLI/JSON workflow gate. Only then
  resume substantial TUI work, C6 Gate B completion, or new GUI interaction.

### 2026-08-14 workflow-gate review — changes requested

- [x] Revalidate the live parent inside `reopen_work`'s write transaction and
  refuse reopening a child whose parent raced closed; recompute the in-lock
  parent rather than the optimistic row.
- [x] Select the latest applicable close event inside the same write
  transaction and derive the restored Current from it; a complete competing
  reopen/pass/close cycle must not make reopen restore an obsolete endpoint.
- [x] Keep the two additive `test_wf09_reopen_*` regressions, rerun focused
  transition/workflow coverage and `just test-v11`, then stop for re-review.
  The workflow gate and heavy TUI remain held until clean acceptance.

**CLI/JSON workflow gate accepted by `baton.reviewer` at
2026-08-14T15:56:21Z.** Focused transitions and workflows report 42 passed;
`just test-v11` reports 199 passed (196 parallel plus 3 serial). The remaining
TUI-parity bullet above stays pending for the later TUI phase. K is stopped
pending rulings and release of the next semantic slice.

### 2026-08-14 WS-1 classification ruling — partially settled

- [x] Canonical classification is never null; new Work starts as `unknown`.
- [x] JSON and audit surfaces use full canonical `unknown`; the TUI renders
  `unkwn` in a classification column capped at five display cells.
- [x] Keep SQLite integer/string encoding private to the authority.
- [x] Reserve `parked` / compact `park` for deliberate suspension with no
  dependency or automatic wake; explicitly preserve its risk of indefinite
  suspension and do not add synonymous `delayed` or `postponed` phases.
- [x] Render canonical `review` as `rview`, never ambiguous `rev`, if `review`
  is retained in the final phase enum.
- [x] Fix the non-null phase enum and compact renderings as `queued`/`queue`,
  `research`/`rsrch`, `waiting`/`wait`, `active`/`actve`, `review`/`rview`, and
  `parked`/`park`; default new Work to `queued`.
- [x] Keep lifecycle status, dependency-derived readiness/blocking, phase, and
  Current/Next orthogonal; no pass silently rewrites phase and there is no
  redundant `done` phase. Narrow exception: satisfying the condition recorded
  by `waiting` atomically moves it to `queued` and audits `wake`; dependencies
  do not otherwise rewrite phase.
- [x] Require a reason to park, retain Current, resume explicitly to `queued`,
  and expose an always-visible parked count in equivalent JSON and TUI summary
  projections.
- [x] Authorize currently resolved Current-route handlers to make explicit,
  audited phase changes; permit ordinary open-phase/rework transitions, while
  enforcing the special waiting wake, parked-to-queued, and closed rules.
- [x] Treat delegation as ordinary `=>` ownership transfer with optional Next;
  add no scoped decision-grant primitive. `@` requests input without granting
  mutation authority or changing Current.
- [x] Define typed waiting conditions: either aggregate required Work gates
  (all open children and `blocked_by` dependencies must close) or one exact
  pending `@` obligation. The last satisfying transition atomically queues and
  audits one `wake`; an already-satisfied condition is refused.
- [x] **AUTHORIZED:** extend WF-01/WF-04 and focused transition/race tests with
  the approved
  default, authorization, waiting, parking, projection, reconfiguration, and
  closed-state cases before WS-1 review.
- [x] **AUTHORIZED:** implement the combined classification and phase slice
  through authority, CLI, canonical JSON/audit, workflows, and bounded compact
  TUI vocabulary/summary parity. Heavy TUI navigation remains held.

### 2026-08-14 WS-1 review — changes requested

- [x] R1: enforce the confirmed ownership-transfer rule beyond
  classification/phase; the additive regression proves an `@` respondent can
  currently pass and close Work whose Current never moved.
- [x] Pin the complete owner-versus-participant operation matrix before the R1
  correction; keep plain contribution/`+`/personal seen and exact obligation
  response distinct from Current-owned workflow decisions.
- [x] R2: expose `classify` and `set_phase` in JSON
  `available_transitions` only for the live Current route's resolved handlers,
  following `=>` and accepted handler reassignment.
- [x] R3: include the always-visible parked count in the canonical top-level
  JSON projection consumed by both JSON and TUI, not only a separate summary
  call; add same-snapshot parity coverage.
- [x] R4: make WF-04 actually execute/assert its claimed
  `research -> review -> active -> review` phases around the independent route
  passes.
- [x] R5 ruling: pin explicit <=5-cell compact labels for every canonical
  classification; remove mechanical truncation fallback.
- [x] R5 implementation: use `unkwn`, `suspt`, `cnfrm`, `limit`, `dupe`,
  `desgn`, and `rejct`; reject unmapped values rather than truncating them.
- [x] Accept creation refusal for `waiting`/`parked`, same-Work obligation
  waits, and closed-Work classification refusal as faithful interpretations.
- [x] Run focused phase/workflow/projection/parity evidence and
  `just test-v11`, then stop for re-review. Heavy TUI, C5/C6, Gate B, and WS-2
  remain held.

### 2026-08-14 WS-1 second re-review — changes requested

- [x] R1: let any configured participant who drills into open Work contribute
  an ordinary message or `+` attention without prior Work participation;
  atomically record the contributing team while retaining every owner gate.
- [x] R1 projection: expose ordinary contribution and own seen state without
  prior Work participation; participation must never expose owner mutations.
- [x] R2: make `available_transitions` match writer preconditions: an open
  blocker does not suppress honest close, while a closed parent does suppress
  child reopen until the ancestry is open. Retire the contradictory old
  projection expectation rather than changing the ruled writer behavior.
- [x] R3: execute the complete top-level home projection and its advertised
  `snapshot_seq` against one SQLite read snapshot; keep reads pure.
- [x] Keep the four additive regressions from
  `review-2026-08-14T20-33-18Z.md`, run focused/break-sweep evidence and
  `just test-v11`, then stop for re-review. Heavy TUI, C5/C6, Gate B, and WS-2
  remain held.

**WS-1 accepted by `baton.reviewer` at 2026-08-14T20:42:37Z.** The four
reviewer regressions pass and independent `just test-v11` reports 225 passed
(222 parallel plus 3 serial). WS-2 is next, but remains a human semantic ruling
before implementation: distinguish satisfying from non-satisfying
dispositions and decide their effect on consumer dependency edges.

### 2026-08-14 WS-2 disposition and verification ruling — partially settled

- [x] Make terminal closure immutable. Remove v11 reopen semantics and
  supersede their automatic re-block behavior.
- [x] Represent later evidence as new Work linked by non-gating
  `follow_up_of`; require new explicit dependency edges for affected
  consumers and never silently re-block prior consumers.
- [x] Record provider closure as explicitly satisfying or non-satisfying,
  never inferred from classification or disposition prose.
- [x] End the provider gate on either terminal result and return the decision
  to each consumer without moving its Current or automatically classifying or
  closing it. Queue only when its last open gate clears; preserve other gates.
- [x] Keep candidate provider Work open during staged verification. Publish a
  pinned candidate and create separate exact `@` verification obligations;
  the obligation makes a team actionable without clearing its dependency.
- [x] Give the responsible provider reviewer/verifier sole judgment over the
  evidence threshold. Responses provide evidence but never vote or trigger
  closure automatically; feedback may drive closure or resumed work.
- [x] Model candidate-specific verification rounds with an exact selected
  assignment set. Show received feedback as `n/total` plus per-assignment
  outcomes; the fraction is receipt progress, never an automatic threshold.
- [x] Start a new round when the candidate changes, retain prior rounds as
  evidence, and explicitly withdraw obsolete/pending assignments with route
  notification when a round or Work ends.
- [x] Allow an optional reviewer-selected `review_at` time. It makes the round
  due and notifies Current but never decides automatically; the reviewer may
  close on elapsed exposure even at `0/N`, with the evidence basis, count,
  elapsed time, and withdrawals recorded.
- [x] Keep verifier observation and provider adjudication separate. Count all
  terminal reports in `N/total`, expose the raw result plus the reviewer's
  accepted/rejected/inconclusive assessment and rationale, and make changed
  assessments append-only supersessions. Neither axis decides automatically.
- [x] On `review_at`, mark the round due and notify its reviewer without any
  state transition. Require an audited reviewer decision to extend the same
  candidate's window, close it as satisfying, or resume work; retain feedback
  across extensions and expose repeated extensions as history.
- [x] Rule verifier observations as `passed`, `failed`, or `unable`, and
  provider assessments as `accepted`, `rejected`, or `inconclusive`.
- [x] Name the terminal state for an assignment no longer required
  `withdrawn`. Keep progress as reports received over assignments selected;
  expose withdrawals separately and never count them as feedback.
- [x] Define the complete WS-2 workflow and focused regression battery in
  `WORKFLOW-TESTS.md`, including immutable close/follow-up, explicit provider
  outcomes, staged verification, due review, adjudication, races, rollback,
  restart, and projection parity.
- [ ] Replace the accepted-but-superseded reopen
  implementation/tests, extend WF-03/WF-04 with satisfying, non-satisfying,
  staged-confirmation, failed-verification, and follow-up stories, then stop
  for review. **Implementation remains held until the documented battery is
  handed to and accepted by the implementer.**

### 2026-08-14 WS-2 pre-implementation decision challenge

**Confirmed by Slawomir.** K's first WS-2 task is to challenge the decisions,
not implement them. Before any source or test edit, she must walk the workflow
battery against the current authority and actively look for contradictory
transitions, missing states, ambiguous authorization, non-atomic boundaries,
unrepresentable JSON, and stories whose asserted result does not follow from
the pinned model.

She returns a written disposition that either lists each issue with its exact
decision/test impact and recommended ruling, or states which workflow and
focused-regression classes she challenged and why no blocker remains. Silence
or a general acknowledgement is not acceptance. Implementation begins only
after `baton.reviewer` reviews that disposition, resolves any product question
with Slawomir, and explicitly releases the first implementation group.

**First challenge returned; changes requested.** See
`review-2026-08-14T21-27-46Z.md`. Implementation remains held pending concrete
options and recommendations for due notification without read mutation,
verification assignments versus exact `@` obligations, provider-outcome and
closed-target edge applicability, and the precise closed-Work mutation rule.

**Expanded disposition reviewed.** See
`review-2026-08-14T21-29-55Z.md`. Slawomir must approve or correct four
recommendations: level-triggered derived due actionability; verification as a
specialized exact `@` obligation; required dependency edges targeting only
open Work; and an explicit satisfying/non-satisfying outcome on every terminal
close. No implementation group is released yet.

### 2026-08-14 WS-2 decision challenge resolved; group 1 released

- [x] Derive due as level-triggered actionable state with an always-visible
  count and deadline-aware wait; create no timer audit row or scheduler.
- [x] Model verification as a specialized exact `@` obligation with structured
  reporting, but forbid it as an automatic Work waiting/wake condition.
- [x] Refuse new required dependency edges targeting terminal Work; use new
  open follow-up Work for later blockers.
- [x] Require exactly `satisfying` or `non-satisfying` on every terminal close,
  independent of current graph shape or verification history.
- [x] Preserve closed-history reads, traversal, references, and personal seen
  hygiene while refusing further workflow mutation or new carrying activity.
- [x] **GROUP 1 AUTHORIZED:** remove every reopen surface; require explicit
  terminal outcomes; add non-gating `follow_up_of`; refuse new blockers that
  target closed Work; preserve dependency propagation, atomicity, audit, JSON,
  authorization, race, rollback, and packaged workflow coverage. Stop after
  group 1 focused tests and affected stories pass and return evidence for
  review. Groups 2 and 3 remain held.

**Group 1 review: changes requested.** See
`review-2026-08-14T21-50-10Z.md`. Closing currently leaves classic `@`
obligations pending and actionable on immutable Work; the additive reviewer
regression fails. Slawomir must rule atomic withdrawal versus close refusal,
then K corrects the loose end and the ineffective follow-up race claim. Groups
2 and 3 remain held.

### 2026-08-14 group 1 correction released

- [x] Rule terminal close to atomically withdraw every pending exact `@`
  obligation carried by that Work; serialize response/dispose/report versus
  close so exactly one terminal result commits and no closed-history response
  can land.
- [x] Keep provider Work independent: a consumer closing or withdrawing its
  request changes no provider classification, phase, Current, status, or
  outcome.
- [x] Expose only `DEP`, the live open-dependent count, in active projections;
  drill lists live dependents, while historical edges and count changes remain
  reconstructable through journal/audit without a total-dependents counter.
- [x] **AUTHORIZED GROUP 1 CORRECTION:** make the additive reviewer regression
  pass with atomic withdrawal, actionable/journal/route visibility, and honest
  race coverage; add live `DEP` projection/count/drill coverage; correct the
  ineffective follow-up race test and its evidence claim; run group-1 stories
  plus `just test-v11`, then stop for re-review. Groups 2 and 3 remain held.

**Group 1 correction re-review: changes requested.** See
`review-2026-08-14T22-09-07Z.md`. Each withdrawn obligation must resolve to its
own `withdraw` event, and one detail response must read `DEP`, live drill, and
snapshot sequence coherently from one pure SQLite snapshot. Two additive
reviewer regressions fail. These are implementation corrections under the
approved rules; no human product ruling is required. Groups 2 and 3 remain
held.

**Group 1 accepted.** See `review-2026-08-14T22-14-53Z.md`. The focused WS-2
closure and workflow regressions pass 17/17, and `just test-v11` passes 236/236
(233 parallel plus 3 serial). Groups 2 and 3 remain held pending explicit
release.

### 2026-08-14 WS-2 group 2 released

**Authorized by Slawomir after the Group 1 commit.** Implement candidate
verification rounds, exact selected-route assignments, immutable raw reports,
append-only reviewer assessments and supersessions, internally consistent
assignment counters, round abandonment with pending-assignment withdrawal,
and the canonical pure JSON projection described by WS2-WF-07, WS2-WF-08, and
the focused regression matrix in `WORKFLOW-TESTS.md`.

- [x] Add focused authority, authorization, cardinality, candidate-pinning,
  assignment-state, assessment-history, counter, withdrawal, audit, and
  one-snapshot JSON regressions before or with the implementation.
- [x] Run WS2-WF-07 and WS2-WF-08 through the source interface plus all
  affected existing stories and `just test-v11`.
- [x] Stop after Group 2 passes and return evidence for reviewer inspection.
- [x] **GROUP 3 REMAINS HELD:** do not implement due/review-at notification,
  extension, fault-injection expansion, the remaining race/restart/packaged
  matrix, or bounded renderer parity in this group.

**Group 2 review: changes requested.** See
`review-2026-08-15T03-09-41Z.md`. Four additive regressions expose a flavored
obligation boundary violation, two incomplete audit identities, and missing
declaration of the new Work-level round actions in canonical JSON. Correct
these within Group 2, rerun its focused stories and `just test-v11`, then stop
for re-review. Group 3 remains held.

**Group 2 accepted.** See `review-2026-08-15T03-15-38Z.md`. The corrected
focused and workflow set passes 17/17, and `just test-v11` passes 253/253 (250
parallel plus 3 serial). Group 3 remains held pending explicit release.

### 2026-08-14 WS-2 group 3 released

**Authorized by Slawomir after the Group 2 commit; supersedes the hold above.**
Complete WS-2 with the remaining pinned battery:

- [x] Add optional `review_at`, derived level-triggered due actionability and
  an always-visible due count, plus deadline-aware waiting. Due reads and
  restarts remain pure: no scheduler, timer audit row, or one-shot notification
  mutation is introduced.
- [x] Add the audited extension of the same candidate's review window while
  retaining reports and pending assignments. Explicit reviewer decisions may
  extend, abandon/resume work, or close; elapsed time and feedback never choose
  a branch automatically.
- [x] Make a close based on a verification round audit the round, candidate,
  reported/assigned and observation summary, decision rationale/basis, elapsed
  exposure, and pending withdrawals without fabricating feedback.
- [x] Implement WS2-WF-01 through WS2-WF-04 and complete the mandatory focused
  due, discretion, atomic-close, race, restart/retry, configuration-generation,
  audit, and one-snapshot JSON matrix in `WORKFLOW-TESTS.md`.
- [x] Add bounded renderer parity for due/pending/reported/withdrawn and raw
  observation versus reviewer assessment using the canonical projection. Full
  TUI navigation remains outside WS-2.
- [x] Run every WS-1 and WS-2 workflow from source and built artifacts plus
  `just test-v11`, then stop and return the complete evidence for review.
- [x] Do not start migration, deployment, heavy TUI navigation, or unrelated
  C5/C6 work during this group.

**Group 3 review: changes requested.** See
`review-2026-08-15T03-57-22Z.md`. Six deterministic failures expose missing
canonical deadline validation, create/extend commit-time expiry races, and a
due alarm with no actionable locator. The required deadline-aware wait is
absent, and the mandatory race/retry matrix is incomplete. Correct these
within Group 3, rerun its complete focused/workflow/package gate and
`just test-v11`, then stop for re-review. Later phases remain held.

**Group 3 re-review: one change requested.** R41–R45 pass, but see
`review-2026-08-15T04-10-52Z.md`: the actionable projection can tear across a
concurrent close, and its JSON envelope may label the old payload with a later
`snapshot_seq`. Pin actionable, summary, and wait results to one pure database
snapshot plus one sampled instant, add envelope/summary regressions, rerun the
complete gate, and stop for re-review. Later phases remain held.

**Group 3 accepted; WS-2 complete.** See
`review-2026-08-15T04-17-56Z.md`. R46 is corrected at both the database and
JSON-token boundaries; all focused regressions pass, all 18 workflows pass
from source and packaged artifacts, and `just test-v11` passes 297/297 (294
parallel plus 3 serial). Migration, deployment, heavy TUI navigation, C5, and
C6 remain held pending their own plan release.

### 2026-08-15 WS-3 design challenge released

**Authorized by Slawomir after the WS-2 commit. Design and ruling only; source
implementation remains held.** `baton.implementer` must re-read the current
finding, `WORKFLOW-TESTS.md`, `WORKFLOW-COVERAGE.md`, and the live authority,
transition, CLI, and projection boundaries, then return a compact adversarial
WS-3 design/options document for review.

- [x] Specify the one atomic provider-dedup operation: exact inputs, actor and
  route authorization, committed relation and dependency effects, canonical
  JSON/CLI result, and dense audit identity.
- [x] Reconcile WS-3 with the fact that WS-4 first-class discussions and
  reusable `#WORK` labels do not exist yet. Demonstrate an honest narrow
  association on today's model or recommend and justify a sequencing/scope
  correction; do not smuggle a partial WS-4 model into WS-3.
- [x] Walk the PushCoin/Drift scenario from first external report through one
  provider Work, then N independent consumer reports converging on it. Show
  default-view noise boundaries, drill-through, live `DEP`, and closure fanout.
- [x] Define refusals and atomicity for duplicate attempts, self/duplicate/
  cyclic edges, closed provider or consumer Work, wrong handler, route/config
  generation changes, concurrent providers accepting the same report, crash at
  every write boundary, and retry without operation ids.
- [x] Propose the focused regression and source/packaged workflow matrix,
  including break-sweeps proving neither half can commit alone.
- [x] Identify every unresolved product choice or contradiction for Slawomir;
  otherwise recommend the smallest implementation slice and stop for reviewer
  approval.
- [x] Do not edit source/tests or begin WS-4, WS-5, WS-6, migration,
  deployment, C5/C6, or substantial TUI work during this design pass.

**WS-3 design review complete; implementation held for product rulings.** See
`WS3-DESIGN.md` and `review-2026-08-15T04-31-38Z.md`. The reviewer accepts the
narrow obligation+edge-provenance association ahead of WS-4, recommends five
specific D1/D6 dispositions, and identifies two required corrections: an
accepted obligation may wake its exact obligation waiter, and compound audit
ordering must not sequence acceptance before provider Work creation. Present
the dispositions to Slawomir; do not implement until confirmed.

### 2026-08-15 WS-3 implementation released

**Authorized by Slawomir; supersedes the implementation hold immediately
above.** Implement the smallest atomic-acceptance slice under the confirmed
WS-3 rulings in `FINDING.md` and the corrections in
`review-2026-08-15T04-31-38Z.md`.

- [x] Add the narrow `accept` transition and CLI forms for existing provider
  Work and atomic provider-Work creation. One transaction commits or refuses
  the obligation terminalization, structured provider association, rationale
  messages, dependency edge/provenance, readiness, wait wake if applicable,
  audit events, and optional provider Work creation.
- [x] Enforce the confirmed authority matrix in-lock: live handler of the
  exact request route; open provider Work owned by that endpoint team for
  `--into`; and the additional parent-Current handler gate only when
  `--create --parent` is requested. Provider Current is recorded but is not a
  second `--into` authorization gate.
- [x] Add canonical `accepted` obligation state and nullable
  `edges.via_obligation`; expose structured accepted-provider and provenance
  fields in one-snapshot JSON projections and declare `accept` only for the
  eligible handler. Do not introduce reusable discussions or `#WORK` labels.
- [x] Make event/message sequence history truthful for both forms. In the
  create form, provider Work must exist at or before the acceptance that names
  it; pin exact ordered acts and both consumer/provider messages.
- [x] Implement D5/D7's refusal, both-order race, config-generation, crash at
  every write boundary, retry, restart, projection, and break-sweep matrix,
  expanded with obligation-wait wake versus gates-wait non-wake and exact audit
  ordering.
- [x] Run the PushCoin/Drift first-report and N-consumer convergence stories
  through source and packaged CLI/JSON, including default-view noise, drill,
  provenance, live `DEP`, terminal fanout, and one-snapshot tokens; then run
  all existing workflows and `just test-v11`.
- [x] Stop and return complete evidence for reviewer inspection. Do not begin
  WS-4/5/6, migration, deployment, C5/C6, or substantial TUI work.

**WS-3 first implementation review: changes requested.** See
`review-2026-08-15T04-49-51Z.md`. R49 requires the accepted-provider relation
and canonical edge result to be visible through public structured JSON rather
than reviewer-only SQL. R50/R51 require fail-closed CLI form separation and
None-only defaults. R52 requires integrity binding for both new structural
references. R53 completes the D7 race/fault/restart matrix that the release
required. The three additive reviewer regressions are intentionally red;
WS-4/5/6 and later work remain held until correction and re-review.

**WS-3 accepted by `baton.reviewer` at 2026-08-15T04:56:49Z.** See
`review-2026-08-15T04-56-49Z.md`. R49–R53 are satisfied; the reviewer added
all-create-option and source+packaged public-contract pins. Focused review is
32/32 and `just test-v11` is green at 326/326. Atomic provider acceptance is
complete. The next sequenced item is WS-4's separate design/ruling round;
implementation remains held pending authorization.

### 2026-08-15 WS-4 design challenge released

**Authorized by Slawomir after the accepted WS-3 commit.** This phase produces
one reviewable `WS4-DESIGN.md`; it does not change source, schema, tests, or
deployment.

- [ ] Inventory the implemented Work-local message/seen/participant model and
  every confirmed discussion/`#WORK`/`@`/`+`/`=>` ruling. Name supersessions,
  contradictions, and representation assumptions explicitly.
- [ ] Specify canonical discussion/message/label records, invariants,
  creation and label mutations, authority, audit ordering, public JSON,
  pagination, and one-snapshot reads.
- [ ] Specify personal seen/New semantics over many-to-many labels and
  containment, including deduplication and label-add/remove effects.
- [ ] Specify multi-label operator scope, explicit Work selection,
  participation/responsibility lifecycle, announcement fan-out, and terminal
  Work interaction. No punctuation may require clients to infer structure.
- [ ] Reconcile WS-3 atomic acceptance with provider-side discussion labelling
  while preserving the distinct explicit gate and provenance.
- [ ] Walk WF-05, WF-06, and WF-07 end to end; add refusal, race, crash,
  restart, retry, default-noise, deliberate-traversal, and source/packaged
  acceptance matrices. Identify the smallest implementation slices if WS-4
  should not land monolithically.
- [ ] List every product disposition required from Slawomir with K's
  recommendation and consequences. Stop for review; do not implement WS-4,
  start WS-5/WS-6, migrate/deploy, or expand the TUI.

**WS-4 design returned; implementation held for corrected dispositions.** See
`WS4-DESIGN.md` and `review-2026-08-15T09-03-22Z.md`. The independent
discussion/message/label foundation is accepted in principle, but the review
requires exact many-discussion Work navigation, eligible-label operator scope,
separate lasting team participation, decomposable deduplicated New, a product
ruling on orphan/terminal posting, collision-safe WS-3 labelling, and no
temporary Work-addressed public API at a slice gate. Present the nine
recommended dispositions to Slawomir; do not implement before confirmation.

**Eight corrected WS-4 dispositions approved; one product boundary remains.**
The approved rules are pinned in `FINDING.md`: owning-team member label
authority; eligible-label `--on` resolution; one labelled authorized Work per
operation; monotonic team participation separate from obligation lifecycle;
per-discussion seen plus explicit overlap decomposition; collision-safe WS-3
provider labelling and originating-discussion responses; fresh schema; and two
review-gated slices with no certified temporary API. Implementation remains
held only on the terminal/orphan-discussion ruling from review R58.

### 2026-08-15 WS-4 Slice A implementation released

**The final R58 ruling is confirmed and supersedes the hold above.** Implement
Slice A only, under all WS-4 rulings now pinned in `FINDING.md` and corrections
R54–R60 in `review-2026-08-15T09-03-22Z.md`.

- [ ] Before coding, red-team the corrected model against current WS-1–WS-3
  code and every confirmed ruling. Append the resolved corrections to
  `WS4-DESIGN.md`; if a contradiction or missing product decision remains,
  stop and return it rather than choosing silently.
- [ ] Replace the Work-local storage model with foreign-key-bound discussions,
  one-discussion messages, many-to-many inert Work labels, monotonic
  discussion-team participation, and per-member discussion cursors in a fresh
  schema. No migration or compatibility authority is built.
- [ ] Preserve atomic Work creation as Work + born discussion + owning label +
  first message. Add explicit public discussion creation with at least one
  authorized label and first message; refuse unlabelled creation, duplicate or
  unauthorized labels, absent unlabel, and removal of the final label.
- [ ] Add public discussion list/detail, both-direction Work/label navigation,
  deterministic pagination and one-snapshot tokens. Work detail lists distinct
  discussion summaries; it never merges them into a false timeline.
- [ ] Add plain discussion posting and mark-seen. Posting requires at least one
  labelled open Work; all-terminal discussion remains readable but refuses new
  messages until open Work is labelled. Carrying operators remain for Slice B.
- [ ] Implement Work `New` over distinct discussion messages with `own`,
  truthful per-child counts, `overlap`, and `total`; add the separate
  participating-discussion attention surface using the same cursor.
- [ ] Run the WF-06 multiply-labelled containment story plus focused authority,
  label/post/close, dedup, race, crash-at-every-boundary, restart, retry,
  snapshot, purity, source, and packaged regressions. Break-sweep every inert
  label guarantee and overlap computation.
- [ ] Any temporary Work-addressed operator bridge is internal, explicitly
  marked for removal in Slice B, and absent from certified public docs and new
  packaged acceptance. Do not implement `--on`, change obligations/accept, run
  WF-05/WF-07 under the new grammar, begin Slice B/WS-5/WS-6, deploy, or expand
  the TUI.
- [ ] Stop with full evidence for reviewer inspection. Slice B remains held
  even if Slice A is green.

**Iteration preservation applies throughout WS-4.** This adds no phase and no
Slice A scope. Preserve the existing cyclic ordinary-open transition graph and
reviewer-controlled candidate rounds; discussion/projection changes must not
turn research, implementation, review, or verification into a one-way
pipeline. Later Slice B and TUI acceptance must include a multi-candidate
review/rework story.

**Executable iteration pin.** Expand WS2-WF-04 while adapting workflows to the
discussion model: source and packaged CLI/JSON must execute and audit
`research -> active -> review -> active -> review` across failed candidate A
and replacement candidate B. Reports and assessments must leave phase and
Current unchanged; only explicit handler transitions iterate and only explicit
terminal close ends the provider gate.

**Confirmed Work-revision boundary; implementation not silently added to
Slice A.** Assigned Work may be revised only by its Current handler. Other
members propose changes through a labelled discussion; the handler may append
a provenance-bound, compare-and-swap revision without changing Work identity,
dependencies, or Current. New independently accountable scope becomes child
Work, and terminal Work remains immutable. Pin this rule in the eventual
revision/contract implementation and workflow battery, but do not expand the
currently released WS-4 Slice A schema or source boundary without an explicit
sequencing decision. Cancellation semantics remain open.

**WS-4 Slice A first review: changes requested.** See
`review-2026-08-15T09-42-45Z.md`. R61 restores the explicit `mark_seen`/pure
read contract and keeps the Work bridge out of the packaged public API. R62
fixes future cursors and the lower-mark race. R63 completes bounded,
total-ordered pagination in both relation directions. R64 makes the new
overlap decomposition one-snapshot and preserves Work identity. R65 closes
configured-member/config-generation and label-audit races. R66 executes the
pinned candidate-A review/rework ordering rather than merely producing the
same phase subsequence later. Slice B and all later phases remain held until
correction and re-review.

**WS-4 Slice A correction re-review: R61–R66 satisfied; R67/R68 requested.**
See `review-2026-08-15T10-13-09Z.md`. Relation-list cursors must use the
label/participation addition sequence so a newly attached old discussion does
not fall permanently behind a creation-time cursor; bounded detail preview
must expose truncation/continuation. An explicit page limit above the maximum
must refuse rather than being silently clamped through the default-value
special case. Two additive reviewer regressions reproduce these remaining
gaps. Slice B remains held.

**WS-4 Slice A accepted.** See
`review-2026-08-15T10-22-12Z.md`. R61–R68 are satisfied; the focused set is
33/33 green and `just test-v11` is 359 parallel plus 3 serial passed. Slice B,
WS-5, WS-6, deployment, and TUI expansion remain held pending their explicit
release.
