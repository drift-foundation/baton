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
