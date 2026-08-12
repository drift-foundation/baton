# Plan — recursive target graph with target-scoped discussions

1. **Preserve the confirmed direction** — **done 2026-08-11** in `FINDING.md`:
   one recursive target type, arbitrary-depth strict containment, typed
   non-containment edges, mandatory target-scoped events, goal roll-up, and
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
   mandatory `target_id`, without changing source.
6. **Specify target identity and containment** — resolve stable ids, root and
   parent fields, cycle prevention, arbitrary depth, ancestry queries,
   reparent/promotion rules, and historical-path audit.
7. **Specify lifecycle and roll-up** — resolve states, required/optional gates,
   owner/next-actor transitions, descendant closure rules, reopen, and
   level-triggered readiness.
8. **Specify discussion/event semantics** — resolve mandatory target binding,
   reply inheritance, atomic target-plus-first-message, cross-target references,
   immutable artifact/review revisions, notices, and retention.
9. **Specify Git binding** — stable finding identity, root/path/revision digest,
   promotion without target replacement, idempotent handoffs, and explicit
   no-Git-mutation boundary.
10. **Prototype the bounded TUI information architecture** — preserve the full
   ancestry path while showing root plus the deepest/current levels, local
   children, dependency neighbors, target discussion, and acceptance inspector
   on ordinary and narrow terminals.
11. **Define replacement/migration boundary** — decide whether and how 1.x
   traffic is imported, what clean authority 2.0 requires, and how old/new
   readers fail closed. Do not assume in-place schema evolution.
12. **Revalidate and seek explicit authorization** before any implementation.
    Append supersessions chronologically; do not infer decisions from the
    mailbox discussion alone.

`baton.implementer` creates and exclusively owns `PROGRESS.md` only when this
finding is explicitly selected after the immediate release.
