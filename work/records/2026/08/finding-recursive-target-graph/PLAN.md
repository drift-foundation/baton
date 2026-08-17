# Plan — recursive Work graph with tagged discussions

**Selected-row claim follow-up — 2026-08-16:**
`findings/finding-tui-selected-work-claim/` records the confirmed TUI correction:
lowercase `c` claims the selected Work through the existing canonical atomic
claim operation. Implementation and regression coverage are queued.

**Protocol-11 documentation gate — 2026-08-16:** before declaring v11 landed,
update `docs/EFFECTIVE-BATON.md` from its protocol-10 operating model to teach
honest phase + active-claim transitions, sustained research as claimed work,
queued as awaiting pickup, and safe independent pipeline multiplexing. The
owning ruling is in `findings/finding-active-work-claim/FINDING.md`.

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
sequencing decision. Cancellation was held at this point and is resolved by
the later accelerated-completion ruling below.

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

### 2026-08-15 WS-4 Slice B implementation released

**Authorized by Slawomir after the accepted Slice A commit.** No further
product disposition blocks Slice B. Revalidate the scope below against the
committed Slice A and the chronological rulings in `FINDING.md`; in
particular, the confirmed live-context boundary supersedes
`WS4-DESIGN.md`'s earlier recommendation that orphan/all-terminal discussions
remain postable.

- [ ] Replace the internal Work-addressed carrying bridge with public
  discussion-addressed operators. `@`, `=>`, and planned Next affect exactly
  one currently labelled, eligible open Work. Omitted `--on` resolves only
  when exactly one label is eligible for that operation; zero or several
  refuse, and explicit selection outside the discussion's labels refuses.
- [ ] Keep `+` as the only fan-out operator. Expand it against live endpoints,
  record the exact expansion, add each reached team to monotonic discussion
  participation once, and change no obligation, Current, Next, readiness,
  phase, edge, or Work authority.
- [ ] Bind every `@` obligation to its originating discussion while preserving
  the complete Work-scoped pending/responded/disposed/accepted/withdrawn
  lifecycle. Responses return to that discussion; participation persists
  independently after the obligation terminates.
- [ ] Reconcile WS-3 acceptance atomically: preserve grant, accepted state,
  explicit dependency edge and `via_obligation`, readiness/wake, rationale,
  and audit order; also ensure the originating discussion carries the provider
  Work label, recording collision-safely whether it was `added` or `existing`.
- [ ] Enforce the final live-context rule in-lock. Plain posting and carrying
  activity require at least one labelled open Work; a carrying operator's
  selected Work must itself be eligible and open. All-terminal discussions
  remain durable/readable/searchable but refuse new messages until new open
  Work is labelled. The final label cannot be removed.
- [ ] Execute WF-05 convergence and WF-07 announcement through source and
  packaged CLI/JSON under the new grammar. Preserve WF-06 dedup and the exact
  WS2-WF-04 candidate/review/rework cycle. Cover ambiguity/refusal,
  label-versus-edge inertness, participation persistence, acceptance
  collision, both-order races, crash at every write boundary, restart,
  current retry boundary, pagination/snapshot purity, and audit order.
- [ ] Remove every internal Work-addressed discussion/operator bridge before
  presenting the slice. No compatibility alias or certified temporary API may
  remain.
- [ ] Stop with complete evidence for reviewer inspection. Do not implement
  Work contract revisions or cancellation, begin WS-5/WS-6, deploy, or expand
  the TUI. Append-only Work revisions and cancellation remain separate later
  implementation slices.

**Cancellation product ruling resolved; implementation still held outside
Slice B.** Cancellation uses the ordinary atomic close operation with the
structured outcome `cancelled`. The later terminal-vocabulary ruling expands
the exact close outcomes to `satisfying`, `non-satisfying`, `rejected`, and
`cancelled`, each with a required non-empty rationale; duplicate rejection
also requires an explicit `duplicate_of` relation. Only Current commits a
close after any discussion; it does not cascade, bypass open children, or
reopen later. Dependents receive the exact terminal outcome and make their own
decision. Sequence this implementation and workflow battery after the active
WS-4 Slice B review gate. WF-10 in `WORKFLOW-TESTS.md` is mandatory and runs
all four outcomes through source and packaged CLI/JSON, including authority,
required rationale, duplicate linkage, atomic cleanup and fan-out, child
refusal, races, faults, restart, projection, audit, and immutability.

**Work-revision content ruling resolved; implementation still held outside
Slice B.** Do not add fixed description/requirements/acceptance fields. A
revision append promotes one durable discussion message containing the complete
replacement contract statement and records Work, revision number, expected
prior revision, message provenance, Current actor, rationale, and audit facts.
The effective revision and ordered history must be unambiguous in JSON.
Reusable structure is an external, versioned template file or bundle with
placeholders; rendered content remains stored self-contained in Baton, while
future template id/version/digest metadata is provenance only. Sequence the
revision implementation and its source/packaged workflow battery after the
active Slice B review gate.

**WS-4 Slice B first review: changes requested.** See
`review-2026-08-15T11-01-39Z.md`. R69 removes stale Work-detail advertisements
for the eliminated Work-addressed post/seen bridges. R70 makes the TUI mark
exactly the displayed discussion snapshot rather than a later global
sequence. R71 refuses every wildcard or exact `+` selector that lands nowhere,
including when the match disappears in a config-generation race. Three
additive reviewer regressions reproduce the gaps. Correct only these findings
and stop for re-review; later slices remain held.

**WS-4 Slice B correction re-review: R69–R71 satisfied; R72 requested.** See
`review-2026-08-15T11-12-51Z.md`. The bounded console renders only the returned
thread page but currently marks the discussion-wide `last_seq`, so messages
outside that page can be hidden without reaching the renderer. Mark only the
last message actually returned by the painted page; keep TUI pagination and
navigation out of this correction. One additive reviewer regression reproduces
the false clear. Correct R72 and stop for re-review; later slices remain held.

**WS-4 Slice B accepted.** See `review-2026-08-15T11-16-51Z.md`. R69–R72 are
satisfied; the focused set is 46/46 green and `just test-v11` is 384 parallel
plus 3 serial passed. Work revisions, terminal outcomes, WS-5/WS-6,
deployment, and TUI expansion remain separately gated.

### 2026-08-15 terminal-outcome implementation slice released

**Authorized by Slawomir after committing accepted WS-4 Slice B as
`6e96503`.** Revalidate this scope against the chronological rulings in
`FINDING.md`, especially “every terminal close has a structured outcome and
rationale,” and the executable WF-10 contract in `WORKFLOW-TESTS.md`. This
slice changes terminal closure only; Work revisions, WS-5/WS-6, TUI expansion,
deployment, and migration remain held.

- [ ] Extend the one existing atomic close mechanism to accept exactly
  `satisfying`, `non-satisfying`, `rejected`, or `cancelled`. Every outcome
  requires a non-empty rationale; omission, whitespace, an unknown outcome,
  or inference from classification/discussion prose refuses before commit.
- [ ] Preserve Current-only authority, open-child refusal, Current/Next
  clearing, pending response-obligation and verification-assignment
  withdrawal, dependency result propagation, last-gate wake, immutable close,
  dense audit order, and independent dependent/provider lanes for all four
  outcomes. Cancellation is ordinary accelerated close, never a cascade or
  child bypass.
- [ ] Add the non-gating `duplicate_of` relation for duplicate rejection. It
  names an existing canonical Work explicitly, is recorded in the close event
  and canonical JSON/link projections, refuses self/missing targets and
  incompatible outcome use, and never changes readiness, Current, phase, or
  dependency edges. Ordinary rejection remains valid without it.
- [ ] Bump the fresh v11 schema coherently as required; there is no migration.
  Keep one unambiguous rationale concept across storage, events, CLI, and JSON;
  do not retain two writable prose fields or add a compatibility alias merely
  for this unshipped schema.
- [ ] Execute WF-10 literally from source and the packaged artifact: four
  sibling outcome fixtures; duplicate rejection; proposer-versus-Current
  cancellation authority; open-child cancellation refusal; exact dependent
  fan-out and multi-gate preservation; all pending obligation/assignment
  withdrawals; terminal projection and immutable history.
- [ ] Cover missing/empty rationale, unknown outcome, outsider close,
  duplicate-without-link and incompatible-link refusals; race close against
  response, report, pass, and competing close; inject failure across every
  close write boundary; prove retry/restart, pure deterministic JSON, and no
  partial write or consumed sequence on refusal/failure. Break-sweep the new
  outcome, rationale, duplicate-link, and cancellation guards.
- [ ] Run the focused terminal/workflow suite and `just test-v11`, record exact
  evidence, and stop for review. Do not begin Work revisions or any later
  phase even if this gate is green.

**Terminal-outcome first review: changes requested.** See
`review-2026-08-15T14-39-43Z.md`. R73 requires omitted rationale/outcome to
remain inside the public JSON exit-one error contract rather than escaping as
argparse prose with exit 2. R74 requires `duplicate_of` to name the canonical
survivor directly, refusing duplicate chains and mutual cycles with an in-lock
recheck. Additive reviewer regressions reproduce both gaps. Correct only these
findings and stop for re-review; Work revisions and every later phase remain
held.

**Terminal-outcome slice accepted.** See
`review-2026-08-15T14-45-25Z.md`. R73–R74 are satisfied; the focused set is
46/46 green and `just test-v11` is 403 parallel plus 3 serial passed. Work
revisions, WS-5/WS-6, deployment, migration, and TUI expansion remain
separately gated.

### 2026-08-15 Work-revision implementation slice released

**Authorized by Slawomir after committing the accepted terminal-outcome slice
as `273fe4c`.** Revalidate this scope against the chronological rulings in
`FINDING.md`, especially “assigned Work is revised only by its current
handler” and “Work revisions store complete content; structure comes from
external templates.” Execute WF-11 in `WORKFLOW-TESTS.md`. This slice changes
append-only Work contract revision only; WS-5/WS-6, dossier/template binding,
TUI expansion, deployment, and migration remain held.

- [ ] Add an append-only Work revision record that promotes one complete,
  durable discussion message. Record Work, monotonically increasing revision,
  expected prior revision, promoted discussion/message provenance, Current
  actor and resolution facts, non-empty rationale, audit sequence, and the
  self-contained promoted content. Do not add fixed description,
  requirements, or acceptance fields.
- [ ] Authorize only the resolved Current handler of open Work. Require the
  promoted discussion to carry that open Work label. Preserve Work identity,
  containment/dependencies, phase, Current, Next, discussion content, and all
  earlier revisions; transfer of Current transfers revision authority.
- [ ] Make promotion compare-and-swap on the expected prior revision and
  recheck actor, Current resolution, Work state, label/provenance, and expected
  revision in-lock. Concurrent or stale writers refuse whole without consuming
  an audit/publication sequence.
- [ ] Expose exactly one effective revision plus deterministic ordered history
  in canonical JSON, including complete content and provenance, so agents need
  not replay a discussion to reconstruct the current contract. Terminal Work
  and committed revision history are immutable.
- [ ] Execute WF-11 from source and the packaged artifact. Cover outsider and
  former-handler refusal, Current transfer, missing/wrong expected revision,
  missing or ineligible provenance, empty rationale, concurrent promotion,
  fault injection at every write boundary, restart/retry, child-Work scope,
  pure projection, dense audit ordering, and terminal immutability. Break-sweep
  the authority, CAS, provenance, append-only, and atomicity guards.
- [ ] Keep external template validation/rendering and dossier/artifact binding
  out of this slice. A future layer may add immutable template provenance, but
  the stored promoted content must already be self-contained.
- [ ] Run the focused revision/workflow suite and `just test-v11`, record exact
  evidence, and stop for review. Do not begin WS-5/WS-6 or any later phase even
  if this gate is green.

**Work-revision first review: R75 changes requested.** See
`review-2026-08-15T15-12-51Z.md`. The authority/CAS/provenance behavior and
WF-11 otherwise match the ruling, and the focused implementation set is 28/28
green. Canonical `detail` currently returns the entire revision history as an
unbounded list, contrary to the pinned bounded-pagination contract. The
additive reviewer regression reproduces the missing count/truncation/cursor
and continuation surface. Correct only R75 and stop for re-review; WS-5/WS-6
and every later phase remain held.

**Work-revision slice accepted.** See
`review-2026-08-15T15-17-42Z.md`. R75 is satisfied: direct effective revision,
bounded preview with honest count/truncation/cursor, and pure paginated
continuation agree in source and packaged JSON. The focused re-review is 29/29
green and `just test-v11` is 418 parallel plus 3 serial passed. K remains
stopped; WS-5/WS-6, external template/dossier binding, deployment, migration,
and further TUI expansion remain separately gated.

### 2026-08-15 WS-5 effectively-once retry design challenge released

**Design only, authorized by Slawomir while the accepted Work-revision commit
is being prepared. Implementation remains held.** `baton.implementer` must
revalidate the current mutation paths and produce `WS5-DESIGN.md`; no source,
schema, public CLI, tests, migration, deployment, TUI, or `PROGRESS.md` change
belongs to this pass.

- [ ] Inventory every public mutating operation and its current retry behavior,
  including Work/discussion/seen/revision/verification operations, config
  acceptance, and generation-1 initialization. Separate pure reads and waits.
- [ ] Specify the client operation-id grammar and collision scope; whether it
  is mandatory per mutation; how TUI, agent CLI, and human CLI obtain and
  retain it; and what guarantee is explicitly unavailable when a caller does
  not supply one.
- [ ] Define a canonical semantic request fingerprint over actor, operation,
  and typed input—not shell spelling or dynamic resolution output. Exact retry
  after a committed response loss must return the original committed result;
  conflicting reuse must refuse without mutation.
- [ ] Define the SQLite record and one-transaction algorithm. The operation
  identity/fingerprint, mutation, event sequence, and replayable result commit
  together. Concurrent identical attempts yield one effect and one result;
  concurrent conflicting attempts yield one effect and one closed refusal;
  an ordinary pre-commit refusal records no false success and does not poison a
  corrected attempt unless the design explicitly justifies another rule.
- [ ] Resolve retry lookup ordering against normal validation and later state:
  a committed retry must still be recoverable after the original operation
  changed Work state, while identity/config authorization and information
  disclosure remain coherent. Cover handler reassignment/removal and authority
  restart explicitly.
- [ ] Specify result/envelope semantics (`already_committed` or equivalent),
  operation-record retention/GC, audit projection, pagination, and protocol/
  projection-version consequences. Preserve dense event sequencing and pure
  reads.
- [ ] Extend WF-09 on paper into an executable source+packaged battery: lost
  response then exact retry, same-id same-request race, same-id conflicting
  request/actor, refusal then corrected attempt, crash at every boundary,
  restart, later-state replay, config-generation race, and every mutation
  family. Name focused regressions and break-sweeps.
- [ ] Identify all unresolved product choices or contradictions and recommend
  one disposition for each. Stop for reviewer/Slawomir review. Do not implement
  WS-5 or start WS-6/later phases even if the design appears complete.

**WS-5 design first review: R76–R78 changes requested before product ruling.**
See `review-2026-08-15T15-27-39Z.md`. A successful idempotent no-op currently
leaves its op-id reusable; generation-1 init lacks both the participant needed
by per-participant scope and the existing-authority lookup needed for lost-
response replay; and `already_committed: false` does not reveal whether an
optional-id call has the strong guarantee. Correct the design only and return
the coherent choice list. Implementation and all later phases remain held.

**WS-5 design correction review: R76–R78 satisfied; R79–R81 requested.** See
`review-2026-08-15T15-31-29Z.md`. Give operation history a total cursor
independent of nullable domain-event sequence, update the battery to the
three-shape `operation` envelope, and make the current-authority identity gate
explicit for existing-authority init replay. Correct the design only and stop
again; product ruling and implementation remain held.

**WS-5 design is internally coherent; product ruling required.** See
`review-2026-08-15T15-35-09Z.md`. R79–R81 are satisfied. Slawomir must now
approve or change the P1/P2/P5/P6a/P8/P9/P11/P12/P10 package before an
implementation gate is written. K remains stopped; no WS-5 implementation or
later phase is authorized.

### 2026-08-15 WS-5 effectively-once retry implementation released

**Authorized by Slawomir after approving the complete corrected package.**
Revalidate and implement `WS5-DESIGN.md` exactly, including the R76–R81
corrections and the chronological ruling in `FINDING.md`. This slice changes
mutation retry identity only; WS-6, dossier/template binding, deployment,
migration, and further TUI expansion remain held.

- [ ] Add schema-v12 append-only operation records with per-participant
  `(participant, op_id)` identity, canonical semantic fingerprints, permanent
  retention, nullable domain-event provenance, and the independent dense
  `recorded` cursor. Preserve fresh-schema/no-migration policy and dense domain
  event sequencing.
- [x] Add optional `--op-id` to every public mutation. Commit the operation
  record, effect, event when any, and complete replayable result in one
  transaction with both optimistic and in-lock lookup. Exact retries replay
  without writes; conflicting reuse refuses; pre-commit refusals do not consume
  identity; protected successful no-ops record their result without an event.
- [x] Enforce the current participant identity gate before every replay and
  preserve original committed results across later domain-state changes. Add
  protected config regeneration and the approved participant-aware fresh-init
  and existing-authority re-init behavior.
- [x] Expose the exact `operation` result shapes (`null`, `committed`,
  `replayed`) and pure participant-scoped `operation-log` pagination on
  `recorded`. Bump the additive projection version coherently; remove every
  stale `already_committed` form.
- [x] Pin and execute WF-12 from source and the packaged artifact. Cover lost
  responses, identical and conflicting races, cross-participant independence,
  refusal then correction, every crash boundary, restart, later-state replay,
  config-generation races, every mutation family, protected no-ops, and
  participant-aware init/re-init. Include the focused regressions and
  break-sweeps named in `WS5-DESIGN.md`.
- [x] Run the focused WS-5/workflow suite and `just test-v11`, record exact
  evidence, and stop for review. Do not begin WS-6 or any later phase even if
  this gate is green.

**WS-5 first implementation review: R82–R84 changes requested.** See
`review-2026-08-15T16-15-14Z.md`. Reject the full operation-id control grammar,
fingerprint only once inputs have reached their accepted normalized typed
form, and make current-participant validation plus replay lookup one coherent
observation across optimistic, in-lock, no-op, regen, and existing-init paths.
The three additive reviewer regressions fail while 20 focused implementation
and WF-12 tests pass. Correct WS-5 only and stop for re-review; WS-6 and every
later implementation phase remain held.

**WS-5 correction review: R82/R83 accepted; R85 changes requested.** See
`review-2026-08-15T16-25-26Z.md`. The original regressions and all 446 existing
v11 tests pass, but replay lookup currently precedes the identity query inside
the shared snapshot. A conflicting reuse raises from the operation table before
the removed-participant gate runs, disclosing old operation identity. Make the
current identity query establish the coherent snapshot before exact/conflict
lookup on every replay path, retain both linearization orders, and stop for
re-review. WS-6 implementation remains held.

**WS-5 accepted.** See `review-2026-08-15T16-31-47Z.md`. R82–R85 are
satisfied; the focused review/implementation/WF-12 set passes 26/26 and
`just test-v11` passes 447/447. No WS-5 review finding remains. WS-6 is still
held until its remaining design boundary is pinned and explicitly released.

### WS-6 design rulings queued while WS-5 remains active

- [x] **Binding shape.** The canonical dossier lives permanently from creation
  at a configured repository identity plus repository-relative
  `work/records/YYYY/MM/<stable-record>/`. Baton and communications reference
  only that path. `work/open/` contains optional relative symlinks solely as a
  human sweep/index; it is non-authoritative, outside the protocol, and cleanup
  unlinks only the symlink. No required commit hash, lifecycle move, recursive
  deletion, or reconciliation checker belongs to this shape.
- [x] **Binding authority.** The creator may attach the initial binding in the
  Work-creation transaction. Thereafter only Current may append a correction or
  provenance revision while Work is open, with expected-prior CAS, rationale,
  and complete history. Current transfer transfers authority; terminal binding
  history is immutable and later correction uses follow-up Work.
- [x] **Open-record semantics.** The canonical path is stable but its
  working-tree contents deliberately evolve while Work is open. Baton does not
  hash-pin or ingest them. A missing/unavailable dossier is visible external
  evidence trouble, never authority damage or an implicit lifecycle mutation.
- [x] **Closure semantics.** Closing bound Work preserves the same permanent
  repository/path binding; it does not move, convert, seal, or require a Git
  revision. Optional Git provenance may be appended by Current while open.
  Unbound lightweight Work closes normally, with only the already-required
  close rationale. Removing an `open/` symlink is later non-protocol cleanup.
- [x] **Artifact references.** Dossier evidence uses a normalized path relative
  to an immutable binding revision; resolution never uses `work/open/`.
  Independent configured-root/path references remain legal for genuinely
  external resources. Neither form hash-pins or ingests bytes, and absence does
  not damage authority.
- [x] **Validation boundary.** Mutations validate authority, CAS, configured
  root identity, shape, and safe relative-path syntax atomically. Baton never
  probes the filesystem or Git for canonical reads and adds no persisted
  availability/staleness vocabulary or reconciliation checker in WS-6.
- [x] **Template boundary.** A finding template is an external, team-owned
  Markdown instruction/pattern. The implementer applies it to the actual
  report/research to create a context-appropriate permanent dossier, normally
  with at least `REPORT.md`, `PLAN.md`, and `PROGRESS.md` plus whatever
  test/data/evidence structure the work needs. It is not a copied directory,
  manifest, or renderer contract. Teams may evolve it and contribute
  conventions back. Baton stores no template identity/version/digest and
  performs no template validation; Work revisions remain self-contained.
- [x] **Template distribution.** Core numbered Markdown patterns live under
  source `tmpl/`, ship under the exact versioned `baton-cli` release's `tmpl/`,
  and project bootstrap copies them into the project's top-level `tmpl/` while
  creating `work/open/` and `work/records/`. Bootstrap never symlinks to the
  install or overwrites conflicts; upgrades never silently replace project
  copies. Source and packaged bootstrap must be byte/shape equivalent.
- [x] **Root-address vocabulary.** Preserve configured
  `ROOT_ID:relative/path` addressing across all teams and repositories.
  Accepted `baton.json` declares portable root ids; an explicit machine-local
  resolver supplies absolute base paths. Work team never implies its root.
  Bindings, dossier artifacts, and independent references all name a root plus
  normalized relative path; missing local mappings affect navigation only.
- [x] **Reference availability.** Every public mutation may carry ordered typed
  asset references. References commit atomically with the act and participate
  in its normalized WS-5 fingerprint. Compound acts preserve explicit
  per-result placement; no verb-specific ban, silent copy, omission, or guess
  is allowed.
- [x] **Reference scope.** Any existing bound Work may be cited without first
  labelling the discussion. The explicit Work/binding revision anchors
  provenance; citation adds no label, dependency, participation, or workflow
  mutation.
- [x] **Unbound reference.** Dossier-relative citation requires a real binding
  revision and refuses clearly on unbound Work. Independent `ROOT_ID:path`
  citation remains available; no placeholder binding or guessed locator.
- [x] **Binding path shape.** Canonical bindings require exactly
  `work/records/YYYY/MM/<stable-record>` with four-digit year, month `01`–`12`,
  one safe record component, and full containment syntax. Baton checks no
  calendar correspondence, existence, symlink, Git, or dossier contents.
- [x] **Root retirement.** New bindings/revisions and independent references
  require a live root; ids are never reused. Dossier-relative references may
  continue citing existing immutable binding revisions on retired roots.
  History remains readable, open Work may correct to a live root, and no
  special retirement stranding gate is added.
- [x] **Template release boundary.** Templates are separate deployed assets in
  the exact CLI release's sibling `tmpl/`, never embedded in the zipapp. Slice
  B covers candidate/manifests/release layout, generic installer support, and
  temporary-target parity; production `~/baton` deployment, mailbox creation,
  migration, and cutover remain held.
- [x] **Distribution assets.** A Baton distribution install owns immutable
  versioned binaries/docs/conf/default templates and may live at
  `~/opt/baton`, `/usr/lib/baton`, or elsewhere. Distribution `deploy/install`
  and project `bootstrap` are distinct; bootstrap copies from one exact release
  and never links or writes back.
- [x] **Three location domains.** The complete current model is:
  distribution root (for example `~/opt/baton`) owns immutable products;
  coordination home (`~/baton`, `~/.baton`, or explicit alternative) owns
  instance config/SQLite/local resolver; configured project roots own editable
  templates and dossiers. Deploy, mailbox init, and project bootstrap are
  separate operations and no path is inferred from another.
- [x] **Placement/Git boundary.** Current project roots normally live under
  `~/src/*`; coordination home may live under `~/src/`, `~/baton`, or another
  explicit path and may be Git-managed externally. WS-6 adds no Git/backup
  authority semantics; consistent live-SQLite snapshotting is separate work.
  Exact distribution release directories remain stable and immutable.
- [x] **Parallel trial boundary.** v11 CLI/TUI trials use a separate config,
  database, processes, and runtime paths while deployed v10 remains the live
  coordination authority. No v11 test, bootstrap, restart, or fault injection
  may touch or stop v10; cutover is a later explicit operation.
- [x] **Workflow-test boundary.** `WS6-DESIGN.md` defines WF-13 for portable
  root-scoped binding/reference authority, CAS/transfer/closure/races/restart
  and missing-local-root purity, plus WF-14 for source/package template,
  contained bootstrap, and root-relocation parity. Implementation is split
  into authority/projection Slice A and filesystem/package Slice B with
  separate review gates.

**WS-6 design ready for implementer review; implementation remains held.** K
must revalidate `WS6-DESIGN.md` against the current strict config, schema,
CLI/projection, and packaging surfaces and return contradictions, omissions,
or a concrete two-slice plan. Material product choices return to Slawomir. No
WS-6 source/template/build change is authorized until that review is accepted
and Slice A is explicitly released.

**WS-6 contradiction review received; M1–M6 ruled.** The response is preserved
as
`implementation-response-2026-08-15T17-09-14Z-4aa5527c7a582d33bda2c644be5529f4.md`.
The dated FINDING rulings and `WS6-DESIGN.md` disposition supersede its proposed
limits: references are mutation-wide, bound-Work citation needs no label,
unbound dossier refs refuse without blocking independent refs, binding paths
enforce year/month shape, historical bound citations survive root retirement,
and templates are separate deployed assets rather than zipapp resources. K
must return a corrected two-slice plan. Implementation remains held.

**WS-6 corrected plan reviewed; one new coordination-home UX decision is
open.** K's corrected plan is preserved as
`implementation-response-2026-08-15T17-30-08Z-ca120fff381353be52d8f2b68319ddfb.md`.
It represents M1–M6 and the three-domain placement model correctly. Its two
remaining edge questions are settled: configuration mutations participate in
mutation-wide references, while a reference-bearing mutation that produces no
domain act refuses rather than dropping evidence.

Do not release Slice A yet. Slawomir has added a coordination-home onboarding
requirement: an exact installed CLI scaffolds an empty target with `baton init
.`, the operator edits the instance/root templates, and a pure `baton check .`
validates them before any member starts. The implementation plan must separate
that scaffold from unique SQLite authority activation and from project
template bootstrap. Resolve the public command names for scaffold versus the
existing generation-one `init`, then append the resulting workflow story and
revised slice placement. No source/template/build change begins until this
last boundary is confirmed and Slice A is explicitly released.

**WS-6 onboarding amendment first review: R86/R87 changes requested.** See
`review-2026-08-15T17-37-09Z.md`. The scaffold/check/activate separation and
WF-15 are directionally sound, but strict `baton.json` cannot contain comments,
and a newly generated authority UUID contradicts a byte-identical
re-scaffolding claim unless bounded recognition is defined. Correct the plan
only. Slawomir must still confirm the public command vocabulary; Slice A and
all filesystem implementation remain held.

**WS-6 onboarding vocabulary ruled.** Slawomir confirmed `init DIR` for the
coordination-home scaffold and `activate DIR --participant ...` for strict
generation-one validation plus atomic authority creation. The proposed
separate `check` command is removed: failed activation is pure with respect to
authority state and reports the validation errors for the operator to correct
before retry. K must revise Amendment 3 and WF-15 accordingly while correcting
R86/R87. Implementation remains held until that planning correction is
accepted and Slice A is explicitly released.

An optional pure `check` may be proposed later as a reusable convenience over
the exact same validator, but it is deferred and must not become a third
required onboarding step. The current WS-6 acceptance story remains
`init` -> edit -> `activate`.

**WS-6 Slice A released; Slice B R88 held.** See
`review-2026-08-15T17-40-58Z.md`. R86 is satisfied and the later two-step
ruling removes `check` from the required story. K may now implement the
authority/projection Slice A exactly as bounded in the review, run focused
tests plus `just test-v11`, and stop for review. Slice A may not touch any
filesystem onboarding, resolver, template, build/deploy, WF-14, or WF-15
surface. Before Slice B, correct the one-shot multi-file scaffold: a mid-write
failure must be recoverable without overwriting an edited config or requiring
blind manual cleanup. Slice B remains held.

**R88 superseded by explicit one-shot-init ruling.** Slawomir chose refusal on
any pre-existing Baton-managed target. `init` performs no recognition,
adoption, continuation, overwrite, or cleanup; its structured refusal names
the blockers and explains that initialization either already ran or requires
operator-inspected manual cleanup. A partial write reports the exact files it
created. This closes R88 as a ruled operational tradeoff. Slice A remains the
active released phase; Slice B is not started before Slice A's review gate.

**WS-6 Slice A first review: R89–R91 changes requested.** See
`review-2026-08-15T18-02-37Z.md`. The core authority model and WF-13 are
present, but configuration mutations use a weaker independent-only/path
parser, the ruled TUI root/path parity checkpoint is absent, and the accepted
per-family/compound-fault/both-order evidence matrix is incomplete. Two
additive reviewer regressions currently report 2 failed and 19 passed. Correct
Slice A only, run the focused set plus `just test-v11`, and stop for re-review.
Slice B and every onboarding/filesystem/deployment surface remain held.

**WS-6 post-review release and production-operation boundary.** Once the
Slice A correction is accepted with clean focused and full v11 gates, proceed
directly to the already bounded Slice B without another Slawomir disposition.
Slice B may exercise generic candidate/install behavior only against isolated
temporary targets. Production deployment, mailbox creation or migration,
participant shutdown, and cutover remain separate manual operations owned by
Slawomir and are not authorized by either slice.

**WS-6 Slice A accepted; Slice B released.** See
`review-2026-08-15T18-19-25Z.md`. R89–R91 are satisfied: the focused correction
set is 27/27, `just test-v11` is 491 parallel plus 3 serial passed, and diff
checking is clean. K may proceed directly with the bounded Slice B described
in `WS6-DESIGN.md` and `WS6-REVIEW.md`, including WF-14/WF-15 and isolated
temporary-target packaging/install tests. Production deployment, production
mailbox creation or migration, participant shutdown, and cutover remain held
for Slawomir's manual operation.

**WS-6 Slice B first review: R92–R94 changes requested.** See
`review-2026-08-15T18-48-00Z.md`. Resolve currently accepts traversal and a
root supplied only by the local resolver; bootstrap's phase-two path opens can
follow a parent symlink inserted after validation; and ordinary init/bootstrap
write failures escape without the exact partial-created report. Four additive
reviewer regressions reproduce the gaps. Correct Slice B only, extend the
public workflow coverage, run the focused set plus `just test-v11`, and stop
for re-review. Production operations remain held for Slawomir.

**WS-6 Slice B correction re-review: R92–R94 partly satisfied; R95–R98
requested.** See `review-2026-08-15T18-58-12Z.md`. The original four
regressions pass, but bare/empty independent locators still succeed, nested
directory creation remains path-based and follows a swapped parent symlink,
resolver JSON accepts duplicate/unknown fields, and short writes are reported
as complete files. Five additive regressions report 5 failed and 11 passed.
Correct Slice B only and stop again after focused plus full v11 verification.
Production operations remain held for Slawomir.

**WS-6 Slice B second correction re-review: R95/R97/R98 satisfied; R99
requested.** See `review-2026-08-15T19-07-47Z.md`. The directory correction
still invokes path-based mkdir, detects the resulting escape afterward, then
calls `rmdir` through the raced symlink to erase the out-of-root directory.
Creation must itself be fd-relative and bootstrap must never delete or repair
after failure. One extended reviewer regression fails on the observed rmdir.
Correct R99 only, rerun focused plus full v11 gates, and stop for re-review.
Production operations remain held.

**WS-6 Slice B accepted.** See `review-2026-08-15T19-13-12Z.md`. R99 is
satisfied by fd-relative creation through the held no-follow parent and the
cleanup deletion is gone. The reviewer's three fault hooks were re-keyed to
that required call boundary without changing their assertions. The focused
project suite is 16/16, `just test-v11` is 511 parallel plus 3 serial passed,
and diff checking is clean. No WS-6 Slice B finding remains; the planned WS-6
implementation is accepted. Production deployment, mailbox creation or
migration, participant shutdown, and cutover remain held as Slawomir-owned
manual operations.

**V11-only development gate; Gate B TUI is next.** Slawomir ruled that the
working deployed v10 generation is frozen and no longer rebuilt or retested as
part of routine v11 work. This supersedes the earlier combined `just build` /
`just test` prerequisite for v11 phases. Use focused v11 evidence plus
`just test-v11`; any candidate packaging exercise is scoped to the v11 product
and isolated targets. Resume Gate B with a bounded TUI-completion plan,
same-fixture TUI/JSON parity and a packaged parallel v11 trial. Production
cutover remains held and v10 remains the live coordination channel meanwhile.

**Gate B next-phase proposal requires correction.** See
`review-2026-08-15T19-33-14Z.md`. The revised proposal correctly withdraws
cutover work, but its preliminary full-product/full-suite baseline still
retests v10, and its TUI scope revives superseded `Unans.`/objective
vocabulary. Remove the combined baseline; use Work and personal recursive
`New`; revalidate every displayed field against the current canonical
projection. Presentation layout, responsive widths, sorting and keys may be
prototyped inside the bounded Gate B slice and returned with real-PTY evidence.
Phase 3 trial paths and roster are selected only after Phase 2 acceptance.
Implementation remains held pending the corrected plan.

**Corrected Gate B released.** Slawomir approved the corrected scope after the
review above. K may implement B1–B3 as one v11-only phase: render only current
canonical Work/`New` semantics, complete bounded Work navigation and focused
detail with real-PTY evidence, expand the shared TUI/JSON parity fixture, and
drive the ruled packaged-v11 TUI scenario. Presentation-only layout, width,
sorting, key and detail choices may be prototyped and returned at Stop 1; a
missing semantic value or contradiction stops for ruling before changing the
projection. Run focused v11 suites plus `just test-v11`, then stop for review.
Do not build or test v10. The packaged parallel trial is released only after
Gate B acceptance, when Slawomir will select paths, participants and workflows.
Production migration, deployment, shutdown and cutover remain held.

**Corrected Gate B plan accepted.** See
`review-2026-08-15T19-35-16Z.md`. R100/R101 are satisfied: the gate is v11-only
and the proposed columns match the canonical `_row_view`, using Work and
personal recursive `New` without invented last-update or blocker-summary
semantics. The existing implementation release remains in force. K proceeds
through B1–B3 and stops with focused, real-PTY, packaged and `just test-v11`
evidence. The parallel trial and every production operation remain held.

**Human trial handoff is part of Gate B acceptance.** The Stop 1 response must
give Slawomir exact commands to launch the packaged v11 TUI against a separate
explicit v11 config/database and demonstrate that none of those commands open,
lock, migrate, stop or rewrite the live v10 deployment. The packaged evidence
uses an isolated instance. After acceptance Slawomir selects the lasting trial
paths, roster, roots and workflows and can test/provide feedback without a new
source change; observations become ordinary v11 Work. This is parallel trial
readiness, not production cutover authorization.

**Operator boundary clarified.** Gate B must leave a v11-only deployment entry
point that Slawomir runs against an explicit distribution destination. Deploy
installs immutable v11 executables/docs/config examples/templates only; it
does not create or activate the real coordination home. The handoff supplies
the exact deploy command and installed executable path. Slawomir then runs
`init`, edits the generated config, and runs `activate` himself in a separate
coordination-home directory. Automated acceptance exercises that sequence only
under isolated temporary roots and never touches v10.

**Parallel trial participants confirmed.** After Slawomir deploys and manually
initializes/activates the isolated v11 coordination home, he brings the human,
`baton.reviewer` and `baton.implementer` into that configured instance for a
joint TUI/CLI test drive. The participant/role/route/root topology is declared
during the edit-before-activate step. V10 remains live in parallel as the
coordination and recovery channel; v11 trial defects become reviewed v11 Work
and do not trigger v10 migration, shutdown or repair.

**Gate B Stop 1 review: R102–R106 changes requested.** See
`review-2026-08-15T19-54-12Z.md`. The row/focused rendering is directionally
sound, but the handoff still hand-builds a source-copy zipapp instead of a
complete v11-only deployed distribution; its v10 “byte identity” command
hashes pathnames rather than bytes; the TUI hides declared transitions and B3
does not execute the ruled scenario; linked Work and multiple discussions are
not navigable; and narrow/long tables truncate columns, lose the collapse
footer and allow an invisible cursor. Four additive reviewer cases report five
failures and 20 passes. Correct only Gate B, run focused plus
`just test-v11`, and stop for re-review. The parallel human trial and every
production operation remain held.

**Gate B Stop 1 correction review: R106 satisfied; R102/R104/R105 remain and
R107–R111 requested.** See `review-2026-08-15T20-00-39Z.md`. The responsive
table regressions are green and the exact-directory deploy boundary is useful,
but the candidate still omits the ruled `doc/` and `conf/` payloads, the TUI
only names rather than performs canonical workflow transitions, and linked
Work plus multiple discussions remain non-navigable. B3 still hand-builds a
second archive and exercises only read/seen while CLI commands perform the
onboarding acts; candidate assembly also admits checkout bytecode. Correct the
complete distribution and installed-TUI scenario, run focused plus
`just test-v11`, and stop again. The parallel trial and production operations
remain held.

**Gate B crossed correction review: substantial progress; R112–R116 remain.**
See `review-2026-08-15T20-19-16Z.md`. The four-part payload, isolated canary,
stable-id link drill, selectable discussions, bounded thread read and single
deployed B3 artifact are accepted directions. Installed `init` still ignores
the exact release's `conf/`, the zipapp contains checkout bytecode, and the
command bar permits a second `--participant` to replace the console's validated
identity; three additive regressions reproduce those failures. B3 still omits
the planned return and does not prove include fan-out, while the discussion set
silently truncates after 50. Correct R112–R116 and stop after focused plus full
v11 gates. Parallel trial and production operations remain held.

**Gate B R107–R111 crossed correction: R112/R113 accepted; R117–R119 remain.**
See `review-2026-08-15T20-32-06Z.md`. Exact-release scaffold consumption,
missing-asset refusal, four-family payload ownership, bytecode exclusion and
the unified packaged build path are accepted. Argparse abbreviation still
bypasses the command-bar identity guard, B3 sets but never consumes planned
`Next`, and the Work discussion set discards continuation after 50 rows. Two
additive regressions fail. Correct only those bounded gaps and stop after
focused plus full v11 gates; parallel trial and production operations remain
held.

**Gate B accepted; isolated parallel trial released.** See
`review-2026-08-15T20-41-44Z.md`. R117–R119 are satisfied and the complete
Gate B product passes the targeted scenario, focused suites, 540 parallel plus
3 serial v11 tests, and diff checking. Slawomir may commit the WIP, deploy v11
into a new explicit immutable distribution directory, then personally run the
installed executable's `init`, edit and `activate` flow in a separate new v11
coordination home. The human, `baton.reviewer` and `baton.implementer` may then
join that isolated instance for the ruled test drive beside live v10.
Production deployment, v10 migration, shutdown and cutover remain held.

**Post-acceptance parser delta accepted.** See
`review-2026-08-15T20-44-00Z.md`. Public long-option abbreviation is disabled
at the parser, and both CLI/TUI identity-prefix regressions pass. Gate B remains
accepted and the isolated trial remains released. Await K's reviewed WIP
commit message; production operations remain held.

**Parallel-trial deploy UX correction accepted.** Slawomir ruled that the
operator must not invoke `tools/deploy_work.py` directly. Keep that module as
the single packaging implementation and expose it through `just deploy-v11
EXPLICIT_NEW_DISTRIBUTION_DIRECTORY`. The recipe dry-run expands to the exact
quoted destination and diff checking is clean; no release was published during
verification. The quickstart names only that public surface and the focused
deploy suite passes 9/9. Hand Slawomir the corrected trial command. No v10
behavior or production path changes in this correction.

**Product-name correction pinned for the next v11 distribution.** The current
immutable `6d1b944` trial may run as deployed, but `baton-work` is only its
temporary development executable name. Before the next v11 deployment, rename
the installed executable and current operator documentation/examples to
`baton`; the versioned distribution path distinguishes v11 from v10. No
already-published immutable directory is rewritten.

**Queued child: generated `init` next-command option order.** The first real
trial exposed that `init` prints `baton activate . --participant ...`, while
the public parser requires global options before the subcommand. See
`findings/finding-init-next-option-order/FINDING.md` and its plan. The existing
healthy scaffold is retained and the trial uses the valid order; fix and test
the generated hint before the next v11 distribution.

**Queued child: TUI table-header case.** The first real TUI trial found the
Work headings rendered in all caps. See
`findings/finding-tui-header-case/FINDING.md` and its plan. The next v11
distribution uses `Title`, `St`, `Phase`, and equivalent initial-capital
labels without changing canonical projection fields or responsive column ids.

**TUI table-header child accepted.** V11 Work `26de18dd-W2` carried the
implementation and consuming return to review. The exact renderer/test delta
is accepted with focused PTY evidence, K's full 541+3 v11 gate and clean diff
checking. The source fix waits for the next immutable distribution; `6d1b944`
was not rewritten.

**Queued child: configurable TUI automatic refresh.** The first real trial
confirmed that v11 currently re-renders only after terminal input. See
`findings/finding-tui-auto-refresh/FINDING.md` and its plan. The next v11 TUI
must poll canonical projections automatically with a configurable positive
seconds delay, default 2 seconds, while preserving selection and producing no
seen receipt or workflow mutation. No inotify/file-watch contract is added.

**Queued child: confirmed-defect compact label.** The human trial found
`cnfrm` ambiguous because it describes confirmation rather than the resulting
classification. See `findings/finding-tui-classification-label/FINDING.md` and
its plan. A later v11 distribution renders canonical `confirmed-defect` as
`defct` without changing the authority value or other labels.

**Queued child: leaf Enter navigation.** The human trial found that `Enter` on
a leaf Work drills into an unexplained empty child table, while its discussion
messages are hidden behind `o`. See
`findings/finding-tui-leaf-enter/FINDING.md` and its plan. Preserve parent
child-drill behavior, but make leaf activation useful and discoverable after a
focused UX ruling; explicit seen semantics remain unchanged.

**Queued child: formatted discussion reader.** The human trial found the v11
thread to be a clipped raw list rather than a usable message reader. See
`findings/finding-tui-message-format/FINDING.md` and its plan. Add a compact,
borderless presentation for authorship, chronology, message boundaries,
wrapped bodies, references, and personal new state without changing canonical
JSON, discussion separation, pagination, or explicit seen semantics.

**Split-pane TUI ruling.** The Work table remains in the top pane and the
highlighted Work's selected discussion is continuously readable in a bottom
pane. `Enter` in Work retains child drill-down, `Tab` changes pane focus,
distinct discussions remain switchable, and one with personal `New` is
preferred. Preview never advances seen state; `s` explicitly marks only the
displayed bounded page. This ruling jointly refines the leaf-navigation and
formatted-reader children above.

**Queued child: subject-bearing Thread vocabulary.** The human trial confirmed
`Work -> Threads -> Messages`, superseding `Discussion` as the canonical v11
entity name. See `findings/finding-thread-subject-vocabulary/FINDING.md` and
its plan. Each Thread has a required subject, Messages retain bodies, and the
compact bottom pane is `Msgs` with a selected-Thread indicator such as `T1/3`.
Apply the rename coherently across schema, JSON, CLI, workflows, and TUI in a
new immutable distribution and fresh authority; do not migrate `6d1b944`.

**Fresh next trial confirmed.** The `6d1b944` authority is disposable; do not
build a migration for it. Repository findings carry the durable stories. W31
is the first implementation gate; after its reviewed satisfying close unblocks
W17 and W23, implement the split-pane navigation and formatted reader. W16
(`defct`) and W7 (timer-only automatic refresh) are independent queued
corrections for the same next immutable distribution.

The old trial coordination home now lives at
`/home/sl/baton-v11.6d1b944`; use it only to finish/review its W31 handoff. The
next immutable app initializes a fresh `/home/sl/baton-v11`; do not migrate or
rewrite the archived authority.

**W31 review changes requested.** See
`findings/finding-thread-subject-vocabulary/review-2026-08-15T22-35-13Z.md`.
The subject is missing from `create_thread`'s effectively-once fingerprint,
and `create_work` can store a born Thread subject which the public subject
validator refuses. Focused evidence is 4 passed / 3 failed. Do not WIP-commit,
close W31, or unblock W17/W23 until the corrections and full gate review clean.

**W31 R2 ruling approved.** Work titles and Thread subjects share one
normalized, non-empty, single-line, at-most-80-UTF-8-byte contract. Work
creation stores that normalized title as its born Thread subject; no redundant
subject argument and no silent truncation. K may clear the two remaining
focused regressions, run the full v11 gate, and return W31 to review.

**W31 revision 3 accepted.** See
`findings/finding-thread-subject-vocabulary/review-2026-08-15T22-45-22Z.md`.
The fingerprint and born-Thread invariants are corrected; focused W31 is 7/7,
`just test-v11` is 549 parallel plus 3 serial, and diff checking is clean.
Close W31 satisfying; W17 and W23 may become ready through ordinary dependency
recomputation. This accepts W31 only, not the remaining trial queue or a
production release.

W31 closed satisfying at v11 sequence 52. Authority recomputation leaves W17
and W23 open with zero open blockers and `Ready = true`; their historical edge
to satisfying W31 remains visible. They are not part of the W31 acceptance and
remain queued for a later handoff.

**Queued child: TUI exit confirmation.** The human trial confirmed that `q` in
normal navigation must ask `Exit? y/N`, matching the accepted v10 safety
interaction, rather than exiting immediately. See
`findings/finding-tui-exit-confirmation/FINDING.md` and its plan. Confirmation
and cancellation are one-row, preserve the prior view, and perform no
authority or seen mutation. This is independent of W31 and belongs in the next
immutable v11 distribution.

**Queued child: explicit project roots in `baton.json`.** The second trial
confirmed that a client opened with only `baton.json` cannot locate repository
assets when absolute bases exist only in a separately supplied `roots.json`.
See `findings/finding-configured-project-root-paths/FINDING.md` and its plan.
This supersedes the earlier resolver split: configure each repository base in
`baton.json`, make no filesystem-path assumptions, and prove the behavior with
separated distribution/home/CWD/repository workflow tests before the next
immutable v11 distribution.

**Queued child: three-level Work priority.** The second trial's initial queue
made clear that readiness and phase do not order several simultaneously
actionable items. See `findings/finding-work-priority/FINDING.md` and its plan.
Add team-local `high` / `normal` / `low` priority with `normal` default, audited
same-team revision, stable priority ordering, JSON/TUI parity, and no effect on
workflow state. No additional priority tiers are allowed.

**Queued child: discoverable Work ids in the TUI.** The second trial exposed
that missing `create`'s transient result leaves no TUI path to recover the
exact Work id required by command-bar operations. See
`findings/finding-tui-work-id-discovery/FINDING.md` and its plan. Design a
compact, exact selected-Work identity/targeting interaction and cover missed
output, duplicate titles, narrow screens, scrolling and selection changes
before the next immutable v11 distribution.

**Completed child: key/value operation grammar.** The second trial found the
mixed positional/`--option` grammar cumbersome in the command bar. See
`findings/finding-key-value-command-grammar/FINDING.md` and its plan. Replace
v11 operation inputs with one strict order-independent `key=value` grammar
shared by CLI and TUI, preserving global launcher options and every authority,
retry, ordering and refusal boundary. Do not retain two operation dialects.
Signed off 2026-08-16 in
`findings/finding-key-value-command-grammar/review-2026-08-16T12-44-53Z.md`;
the dependent command-assist, batch, and release Work now recompute from their
remaining live conditions.

**Completed dependent child: context-sensitive command assist.** See
`findings/finding-tui-command-assist/FINDING.md` and its plan. Drive partial
verb, parameter, remaining-key, and closed-value hints from the exact command
specification established by the key/value grammar; render them beside the
command input without hiding typed text or mutating authority. This child must
depend on the grammar child in the v11 Work graph. Signed off 2026-08-16 in
`findings/finding-tui-command-assist/review-2026-08-16T13-10-12Z.md`; W19 and
the release Work now recompute from their remaining live conditions.

**Queued dependent child: `::` multiline command batch.** See
`findings/finding-tui-command-batch/FINDING.md` and its plan. Keep `:` as the
assisted one-liner; add `::` as a paste-friendly multiline buffer with Enter
for new lines and visible `Ctrl-G` Go. Preflight all syntax, execute
sequentially, stop honestly on refusal, retain completed/failed/unrun state,
and preserve per-command retry safety without claiming batch atomicity. This
child depends on the key/value grammar and adds no scripting language or file
execution.

**Changes requested 2026-08-16:** the first W19 review is recorded in
`findings/finding-tui-command-batch/review-2026-08-16T13-26-01Z.md`. Editing a
failed or completed line currently leaves a stale run summary in place and
hides the Go/cancel legend; the batch-specific resize acceptance also lacks its
required regression. Correct those focused gaps and return W19 for review
before advancing the serial queue.

**Superseded by sign-off 2026-08-16:** both W19 review gaps are corrected and
accepted in
`findings/finding-tui-command-batch/review-2026-08-16T13-33-55Z.md`. Buffer
mutations now invalidate stale summaries and restore the controls, and the
batch-specific resize path preserves the whole staged input and caret. W19 may
close satisfying and the serial queue may advance.

**Superseded child: separate live `Blk` and `Dpts` counters.** See
`findings/finding-live-dependency-counters/FINDING.md` and its plan. Expose
canonical open-blocker and open-dependent counts in JSON, but do not add main-
table columns: W71's tree supersedes that presentation and absorbs the JSON
plus detail/links correction. W27 closes cancelled as a separate item.

**Queued child: authority-local Work selectors.** See
`findings/finding-local-work-selectors/FINDING.md` and its plan. Expose stable
`W<sequence>` values in an exact `Id` list column, JSON `local_id`, and Work
details; accept the short or canonical id through one fail-closed resolver for
every Work-valued CLI/TUI parameter. Never infer identity from title, cursor,
order or an ambiguous match, and never truncate the visible selector.

**Queued dependent child: inline dependency cue.** See
`findings/finding-tui-inline-dependency-cue/FINDING.md` and its plan. The main
Work table retains `↳` for the two-level containment tree, adds a distinct
`← Wn` / `← Wn +N` cue for live blocker edges, and removes the opaque `Ready`
column. Queue behind the authority-local selector child so every cue uses the
same reviewed short identity contract.

**Queued child: Work-list `Msg/My` counters.** See
`findings/finding-work-message-action-counts/FINDING.md` and its plan. Project
overlap-safe total Messages and viewer-eligible pending `@` obligations in the
same Work scope, expose explicit JSON fields, and render compact `Msg/My`
without replacing personal `New`. Prove response/withdrawal, multi-handler,
shared-Thread, descendant, rebuild, narrow-screen and read-purity behavior.

**Activated 2026-08-15 after W5:** Slawomir selected v11 W36 as the next
serial item. It is assigned only after revalidating the child finding against
the projection-3.1/schema-14 checkpoint at `8450a40`; the older queue order is
superseded for this one handoff, not erased.

**Closed satisfying 2026-08-16:** W36 passed round-two review and focused
coverage; see `review-2026-08-16T04-05-27Z.md`. Its implementation preserves
schema 14 and the full v11 suite remains part of the release gate.

**Queued child: discoverable message browser and separate references.** See
`findings/finding-tui-message-browser/FINDING.md` and its plan. Message paging
must expose more-state and its controls; Thread ordinals must not masquerade as
message counts; references render in a separate `Refs` section. A borderless
message-index/body split is proposed pending final key and narrow-layout
rulings. This remained separate from W36 and is queued independently as W71.

**Navigation supersession confirmed 2026-08-15:** W71 now owns the final
schema-14 navigation model. The main screen is a two-level Work containment
tree; `Enter` opens Work details and `u` unfolds/re-roots deeper containment.
Details show Threads above the selected Thread's Messages, use `Ctrl-W` pane
navigation, separate `Refs`, and expose no internal `after #N` cursor. This
supersedes the earlier Enter-child-drill and persistent main-screen Msgs pane.

**Queued child: remove root-header noise.** See
`findings/finding-tui-top-level-header-noise/FINDING.md` and its plan. Remove
only the redundant `— top-level work` phrase from the root view while keeping
the participant identity, actionable live summary and real drilled
breadcrumbs. This is presentation-only and is queued independently as W74.

**Queued child: terminal Work has no phase.** See
`findings/finding-terminal-work-no-phase/FINDING.md` and its plan. Open Work
retains a required canonical phase; closed Work projects `phase: null` and
renders `-`, while audit history preserves the last open phase and close.
This is a same-schema projection/presentation correction and introduces no
synthetic `done` phase.

**Deferred child: explicit project metadata and Work filters.** See
`findings/finding-work-project-filters/FINDING.md` and its plan. Configure
canonical projects in `baton.json`; never infer them from paths or bindings.
Expose composable CLI/JSON/TUI filters, including
`:filter project=baton`, and always show the active filter. Persisted project
metadata requires a fresh authority and does not widen the schema-14 trial.

**Superseded 2026-08-16:** team is the project boundary; do not add overlapping
project metadata or a project catalog. The child is now a same-schema filter
feature over existing Work facts. Team filtering is useful only on multi-team
surfaces because a team's home view is already implicitly team-scoped. Startup,
interactive TUI, and CLI/JSON filters still use one grammar and visibly expose
the active filter.

**Parked child: transient recent-Work cue.** See
`findings/finding-tui-recent-work-cue/FINDING.md` and its plan. A future schema
provides per-Work millisecond `last_changed_at` plus stable change sequence;
the TUI animates the most recent visible row only for the remainder of a
configurable age window (default 2000 ms). This has no automatic wake and is
parked until the next schema revision rather than approximated in schema 14.

**Superseded 2026-08-16:** the timestamp-age cue above is replaced by the
live hot-zone cue pinned in the same child. Blink open Work with an active
claimant, plus ready unclaimed review Work; exclude blocked review, waiting,
parked, and closed Work. Blink only the phase/status cell (`actve` or `rview`),
not the whole row. This depends on W108 claimant projection but no longer
depends on recency timestamps.

**Pre-cutover audit 2026-08-16:** W108 is complete and the cue is still absent
from source. The same live Work was moved from parked to queued at sequence
128; implement the hot-zone scope before cutover and do not recreate the stale
“recently changed” item in the fresh authority.

**Completed 2026-08-16:** W84 is implemented and signed off in
`findings/finding-tui-recent-work-cue/review-2026-08-16T13-43-54Z.md`. The cue
derives solely from canonical claimant/readiness state and blinks only the
phase cell; cold, narrow, blocked, waiting, parked, and terminal cases remain
steady. W84 is removed from recreation. This completes the ruled same-schema
pre-cutover cleanup set.

**Reliable-cue clarification 2026-08-16:** terminal blink is not sufficiently
reliable as the sole hot-zone signal. Preserve the same predicate and
phase-cell blink, and additionally bold only the Title cell of hot active and
review rows. Cold rows remain unstyled. See
`findings/finding-tui-hot-cue-live-visibility/`.

**Queued live regression — 2026-08-16:** the fresh-authority TUI showed W2 as
active and claimed but Slawomir's real terminal displayed no visible blink.
See `findings/finding-tui-hot-cue-live-visibility/`. W84 remains closed; this
new item distinguishes escape-attribute emission from visible UX acceptance
and stays queued behind W2 pending a presentation ruling.

**Resolved immediately — 2026-08-16:** the same phase cell began visibly
blinking after the initial observation interval. No replacement cue or v11
Work is needed; the queued-regression paragraph above is superseded and W84
remains complete.

**Queued fresh-authority UX correction — 2026-08-16:** live W2 details proved
W71's flat formatted-message stream unusable. See
`findings/finding-tui-message-index-body-layout/`. Preserve the Work-only main
screen and Thread hierarchy, but use a compact Message index plus one selected
body/Refs reader (wide split, narrow stack). This is new Work; W71 stays
closed and no authority schema change is required.

**Queued footer wording correction — 2026-08-16:** `b links` visually reads as
“blinks” and was mistaken for the hot-zone cue. See
`findings/finding-tui-dependency-key-label/`. Render `[b] deps`; retain the
existing dependency-neighbor action and graph semantics. Queue behind W14.

**Next after W14 — 2026-08-16:** Slawomir prioritized W4
(`findings/finding-local-work-selectors/`) ahead of the other queued feature
Work. Its visible `Id` column and authority-local `Wn` resolver make every
subsequent Work discussion and command easier to identify. Do not start it
until W14 closes.

**Activated same-schema feedback batch — 2026-08-15.** Per Slawomir, proceed
serially through W77 (terminal Work has no phase), W74 (root-header cleanup),
then W71 (discoverable message browser and separate references). Each receives
its own review gate. W78 remains deferred because canonical project metadata
requires persisted schema state.

**Queued post-batch cutover:** See
`findings/finding-fresh-record-layout-cutover/FINDING.md` and its plan. Once
W77/W74/W71 and the full schema-14 gate are checkpointed, stop extending the
trial: adopt permanent `work/records/YYYY/MM/...` dossiers and the human
`work/open/...` index, update `AGENTS.md`, deploy the next schema, and
initialize a fresh authority without migrating trial state. Recreate only
still-relevant Work with canonical record bindings.

**Pre-deploy correction activated 2026-08-16:** W2 is not Work to recreate
after cutover. The already-confirmed product naming decision makes it a
same-schema prerequisite: the next distribution must install `bin/baton`,
while `baton-work` remains only in immutable historical trials and internal
module/package names. See
`findings/finding-v11-executable-name/{FINDING,PLAN}.md`. W92 deployment is
held until W2 closes satisfying.

**Second pre-deploy correction activated 2026-08-16:** W4 is likewise not
post-cutover Work. It changes the strict v11 configuration/runtime contract,
not SQLite storage; the fresh authority must accept repository bases in
`baton.json` at its initial activation. See
`findings/finding-configured-project-root-paths/{FINDING,PLAN}.md`. Sequence
W2 then W4, each with its own review gate, before W92 deployment.

**Queued child: category header.** See
`findings/finding-tui-category-header/FINDING.md` and its plan. Supersede only
the compact Work-table display label `Cls` with `Cat`; retain canonical
`classification`, the schema, JSON, commands, and compact category values.

**Active next iteration: preserve schema 14.** Follow
`SAME-SCHEMA-TRIAL-PLAN.md` serially, starting with W7. The next packaged
executable must reopen the existing second-trial authority; no migration or
replacement database is allowed. W10 priority remains open for the later
fresh-authority release and is not part of the replacement release gate. If
another item proves to require new persisted schema, defer it and return for
review rather than widening this iteration.

**Next focused phase — 2026-08-16: v11 messaging retirement gate.** See
`findings/finding-v11-messaging-cutover-gate/`. Once the current same-schema
trial-defect batch is closed, prioritize v11 messaging until the human,
reviewer, and implementer can coordinate entirely through v11. v10 remains the
reliable wake-up and communication channel during this work and is not
deprecated until a live end-to-end v11 trial passes and Slawomir explicitly
approves retirement.

**Queued claim-age cue — 2026-08-16:** see
`findings/finding-tui-claim-age/`. Add a final fixed-width `Age` column derived
from the current claim's committed timestamp: `MM:SS` below one hour, `HH:MM`
thereafter, `99h+` beyond the range, and `-` while unclaimed. Reuse the existing
refresh scheduler and authority journal; no database-schema change.

**Parked next-schema child: claim heartbeat and stall alert.** See
`findings/finding-work-claim-heartbeat/`. A claimant heartbeats every two
minutes; after three missed beats/six minutes the Age field gains `!`. The
signal is informational only: never release, transfer, rephase, or permit a
second claimant automatically. Heartbeat state is separate from total claim
Age and requires the next authority schema revision.

**Same-schema supersession — 2026-08-16:** the existing append-only event
journal is sufficient. Record claimant-only heartbeat events, use the claim as
the initial beat, and project the latest qualifying beat for all active Work
in one batched read. W47 moves from parked to queued; only a projection-version
bump is anticipated. A future materialized field/index is an optimization,
not a prerequisite.

**Final cue refinement — 2026-08-16:** W33 depends on W23. W23 first adds bold
Title without creating a visibility gap; W33 then adds claim `Age` and removes
phase-cell blink atomically. The final hot-zone presentation is bold plus timer,
with no terminal animation.

**Phase-change cue supersession — 2026-08-16:** the sentence immediately above
is superseded only in saying “no terminal animation.” W33 removes indefinite
hot-state blink but retains a client-local Phase-cell blink for three scheduled
refresh ticks after an observed Phase change. Initial load is cold; keystrokes,
redraws, resize, and immediate mutation refreshes do not consume or restart the
countdown. Bold Title plus claim Age remain the steady presentation.

**Queued timer-label/scale supersession — 2026-08-17:** see
`findings/finding-tui-held-duration/`. The closed W33 stays closed, but its
mixed `MM:SS`/`HH:MM` presentation is superseded. Rename the column `Held` and
render elapsed endpoint responsibility from handoff as `HH:MM` from `00:00`
through `99:59`, with `99h+` as the explicit fixed-width overflow sentinel.
An unclaimed operational handoff prefixes Phase with `>`, changing to `!` after
six minutes; claim removes the prefix without resetting `Held`. JSON exposes
structured facts, never those TUI glyphs. This is queued as W226.

**Queued stage-label correction — 2026-08-16:** see
`findings/finding-tui-current-next-stage/`. Work-table `Current` and `Next`
answer what is happening now and what happens next, so render their resolved
route handles (`impl`, `rview`) rather than endpoint kinds (`baton.impl`,
`baton.feat`). JSON and commands retain the complete structured endpoint.

**Live cutover defect — 2026-08-17:** see
`findings/finding-local-thread-selectors/`. Projection 6.1 displays the born
discussion as `T2`, but `say thread=T2 ...` refuses because only the hidden
canonical Thread id is accepted. Add a strict authority-local `Tn` resolver
for every Thread-valued command operand before v11 messaging can retire v10.
The full canonical id is permitted only as a logged temporary workaround for
continuing this trial.
