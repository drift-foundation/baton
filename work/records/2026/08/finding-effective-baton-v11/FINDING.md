# Finding: make EFFECTIVE-BATON the v11 operating guide

## Context

Child of W99. `docs/EFFECTIVE-BATON.md` currently teaches protocol-10 mailbox operation. At retirement it must become the practical v11 agent guide: participant identity, Work claim/pass/phase discipline, Threads/Messages and directed obligations, readiness, dossiers/roots, review, terminal outcomes, and recovery—without a v10 fallback.

The guide documents confirmed behavior only. It does not become a second protocol specification.

## Observed — 2026-08-17

The existing guide is not merely a stale command reference. It teaches the
protocol-10 unit of accountability: messages are claimed, replied to, and
closed. Protocol 11 instead makes Work authoritative and keeps these facts
separate:

- the stable Current endpoint says which route owns the next decision;
- phase says what stage the open Work is in;
- an active claim says which eligible member is executing it now;
- dependencies, exact-obligation waits, and parking say why it cannot proceed;
- discussion Messages carry context while Events carry workflow acts; and
- terminal outcome records how the Work ended without reopening it later.

A mechanical command substitution would leave agents with the wrong mental
model and recreate the operational races v11 is meant to prevent.

## Confirmed operating contract — 2026-08-17

The rewrite is an agent-facing operating guide, organized around complete
workflows rather than an exhaustive protocol description. It must pin the
following rules and show the canonical JSON CLI acts that realize them.

### Identity, configuration, and startup

- A coordination home is managed separately from the explicit immutable Baton
  distribution that serves it. `init directory=...` scaffolds the home without
  creating an authority. The operator edits its strict `baton.json`; an
  explicit participant then runs `activate directory=...`.
- Every later invocation names the exact config and `<team>.<member>` identity.
  Teams, members, roles, routes, kinds, project roots, and accepted generation
  come from `baton.json`; none are inferred from the current directory.
- A proposed generation is inactive until an authorized `regen` accepts it.
  Raw SQLite reads or writes are never an operating technique.
- The JSON CLI is the canonical agent surface. The TUI is the human projection
  of the same authority, not a separate workflow implementation.

### Work accountability and execution

- Current is the responsible endpoint, not a person. The accepted route maps
  it to eligible members. Next is only a planned return destination; it neither
  transfers nor claims Work.
- No implementation, review, research, approval, or other Current-owned
  execution starts until `claim work=...` succeeds atomically. A claim is
  orthogonal to phase, competing claims fail closed, and an unclaimed handoff
  is visible unfinished pickup rather than assumed work.
- Phase tells the truth about the current stage: `queued`, `research`,
  `active`, `review`, `waiting`, or `parked`. Research is visible work. Passing
  to a staged route derives the destination phase; it is not supplied as a
  second guess. Same-owner iteration uses the authorized phase operation.
- `pass work=... to=... comment=...` is the sole ownership transfer. It records
  threadless handoff evidence, changes Current, releases the sender's claim,
  and never claims for the recipient. Review rejection may pass the same Work
  back for another `active -> review` iteration without reopening or hiding
  changed scope.
- Waiting and parking are not synonyms for inactivity. Explicit waiting names
  an exact obligation or the Work's dependency gates and releases the claim.
  Parking is an explicit un-gated deferral with a reason and remains a visible
  loose end. A dependency by itself does not rewrite phase: blocked Work keeps
  its honest stage, is not ready, and cannot be claimed.

### Work shape, scope, and dependencies

- Parent/child containment organizes a deliverable. It is not itself an
  execution dependency: a parent may proceed while children are open, but it
  cannot close until every child is terminal. Dependency edges are explicit,
  independently reviewable, and many-to-many.
- `block` adds a live `blocked_by` edge with rationale. Readiness requires all
  live blockers to finish. `unblock` corrects a mistaken live edge with its own
  rationale; it does not close or rewrite either Work, and Events preserve both
  acts.
- A separately accountable new requirement becomes new Work, normally a
  child. Discussion may refine an assigned contract, but only the live Current
  handler may promote a complete replacement revision with compare-and-swap.
  Outsiders propose; they do not edit assigned scope underneath the handler.

### Discussion, attention, requests, and provider intake

- Discussion containers and Messages hold conversation. `include=` requests
  attention only. `request=TEAM.KIND on=WORK` creates one directed obligation
  while Current stays with the requester; contribution by somebody else does
  not silently discharge it.
- Once W159 lands, a directed request waits by default in the same authority
  transaction: publish Message, create obligation, enter the exact wait, and
  release the requester's claim. `wait=false` is the deliberate asynchronous
  override. The guide must be written and its examples executed against that
  final grammar, not the pre-W159 two-command workaround.
- The receiving endpoint may respond, dispose/reject, request more evidence,
  or accept the intake. Acceptance may link to existing provider Work or create
  provider Work and the consumer dependency atomically. Provider and consumer
  remain independent lanes; one provider may gate many consumers.
- Team-wide visibility is for context, while New and unresolved-obligation
  counts remain participant-relative. Workflow handoffs and dependency acts
  belong in Events; prose belongs in Messages.

### Trials, review, and closure

- A provider reviewer may open a `try` trial for one immutable candidate and
  exact verifier endpoints. Reports (`passed`, `failed`, `unable`), assessments
  (`accepted`, `rejected`, `inconclusive`), extensions, and abandonment are
  separate audited acts. Counts and elapsed time inform the reviewer but never
  decide automatically.
- Every terminal close names exactly one outcome—`satisfying`,
  `non-satisfying`, `rejected`, or `cancelled`—and a non-empty rationale.
  Closing a provider ends its dependency gate but never decides or closes a
  consumer. Closed Work never reopens; contradictory later evidence creates
  linked follow-up Work and new explicit dependency edges where needed.
- Review evidence follows the permanent dossier rules: confirmed decisions in
  `FINDING.md`, actionable state in `PLAN.md`, implementer-owned
  `PROGRESS.md`, and append-only review files. Work and Messages bind through a
  configured repository root to canonical `work/records/YYYY/MM/...` paths,
  never through `work/open`, checkout-absolute paths, or remembered commits.

### Readiness, recovery, and retry

- `wait timeout=...` is a read-only participant-relative readiness projection:
  ready unclaimed Work, unresolved directed obligations, and due trials. It
  never claims. One readiness consumer serves one participant; every returned
  action is revalidated and claimed or otherwise handled explicitly.
- External Codex/ACP adapters may wake a model runner, but do not change Baton
  authority or policy. Agents recover canonical context from `wait`, `detail`,
  Messages, Events, and the bound dossier rather than trusting a wake prompt.
- `release work=... expect=TEAM.MEMBER reason=...` is the exact compare-and-swap
  recovery for an abandoned claim. Recovery does not stop the external agent,
  so operators coordinate before forcing it.
- Mutating examples use operation identities where the public grammar supports
  them and explain exact replay versus mismatch. An interrupted operation is
  retried through the public API; authority state is never reconstructed by
  hand.

## Required workflow examples

The guide must present a small ordinary path first, then focused examples for:

1. create, claim, research/classify, pass to implementation, pass to review,
   and satisfying close;
2. non-blocking inclusion versus a directed request and its exact wait;
3. cross-team provider acceptance, explicit dependency, provider completion,
   and independent consumer disposition;
4. failed candidate, rework, a new trial, reviewer adjudication, and immutable
   terminal close;
5. accountable scope revision versus creation of separate child Work; and
6. crash/restart recovery, claim release, retry, and config regeneration.

Examples use the public `VERB key=value` grammar with conventional
`--config`/`--participant` launcher options. Every example must be executed
against the release candidate that ships the rewrite. Exact command names and
the request grammar are revalidated after the current W159 slice. This Work
uses the currently implemented `Thread` vocabulary; W3 is deliberately gated
on the v10-retirement parent and will later rename the product and this guide
consistently. W104 must not wait on W3 and make that retirement graph circular.
The guide must not publish a compatibility fiction for an older trial build.

## Documentation boundary

`docs/EFFECTIVE-BATON.md` explains how a participant works safely and why each
step matters. The shipped quickstart explains installation and surface
discovery. The protocol/design records remain the authority for exhaustive
schema, transition, projection, and race contracts. The operating guide links
to those sources where depth is needed instead of copying them into a second
specification.

## Superseded terminology — 2026-08-18 (W245)

Everything above was confirmed before W245
(`finding-current-is-claimant`) was ruled and implemented. W245 changes
the two nouns this finding uses most, so the statements below are
superseded **as terminology**. They are left intact rather than
rewritten, per the append-only record rule; this section is the live
reading.

W245 separates what this finding called "Current" into two facts:

- **`route`** is the endpoint whose resolved handlers are eligible.
  Authorization resolves here, always. This is what the text above
  means wherever it says Current endpoint, Current handler, or Current
  route.
- **`current`** is the EXACT participant holding the claim, and is
  `null` while nobody holds it. The claimant-valued `active` projection
  this finding referred to no longer exists; no alias was kept.

The specific clauses that must be read in the new terms:

- "Current is the responsible endpoint, not a person" — that is now
  `route`. Current IS a person, or null.
- "`pass` ... changes Current" — `pass` changes `route`, derives the
  destination phase, and CLEARS `current` by releasing the sender's
  claim.
- "Directed requests ... Current does not move" — the ROUTE does not
  move. The default blocking form enters `waiting` and releases the
  claim, so `current` becomes null: nobody is executing Work that is
  blocked on somebody else's answer.
- "only the live Current handler may promote a complete replacement
  revision" — that is the resolved ROUTE handler. Verified against the
  authority rather than inferred: `revise_work` gates on `_handler_gate`
  (route membership), so an eligible handler who holds NO claim can
  promote a contract on Work claimed by somebody else. Reproduced
  2026-08-18 with two handlers on one route.

The behavioural rules this finding pinned are otherwise unchanged; only
the names moved. `PROJECTION_VERSION` moved 7.0 -> 8.0 for the change,
so a consumer pinned to 7.x refuses rather than misreading `current`.

## Superseded again — 2026-08-18 (W288)

The W245 section above is historical from here down on one point, and it
is the last clause of the list: it reads

> "only the live Current handler may promote a complete replacement
> revision" — that is the resolved ROUTE handler. Verified against the
> authority ... an eligible handler who holds NO claim can promote a
> contract on Work claimed by somebody else.

That paragraph accurately described the IMPLEMENTATION on 2026-08-18 and
correctly reported the reproduction. It was wrong as a statement of the
contract, and the behaviour it recorded was the defect rather than the
rule. W288 (`finding-revise-requires-current-claimant`) corrected the
authority.

**The live rule, superseding both earlier readings:**

- **Route controls eligibility.** It names the endpoint whose resolved
  handlers may claim the Work, and revision still requires the actor to
  be one of them at commit.
- **The exact current claimant alone promotes a revision.** Being
  eligible is not sufficient. A route peer who holds no claim may
  propose in the thread and may argue for it, but cannot replace the
  contract of Work somebody else is executing.
- **Unclaimed Work refuses promotion.** Discussion stays open; the
  contract waits for somebody accountable for it.
- Both conditions are revalidated inside the transaction that commits
  the revision compare-and-swap, so a claim released, passed, or
  recovered mid-flight fails closed.

The route-peer success recorded in the W245 section is therefore named
here as the defect W288 fixed, not as intended behaviour. This is the
authoritative reading; the sections above are kept for their history.
