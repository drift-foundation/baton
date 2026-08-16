# Implementation plan — Baton v11 Work graph (rev 4: Gate A / Gate B)

**Status: DRAFT rev 4, plan only.** Rev 4 aligns A4 and §7 with the
audited `Next`/`return` semantics (the rev 3 A4 edit had not actually
landed — caught in review). Rev 3 applied the two pinned-semantics
fixes from the rev 2 review: typed link traversal in the projection/JSON, and
planned `Next` set-on-pass / consumed-on-return in the transitions and the
scenario. Rev 2 restructure per the 2026-08-14 changes request:
all four blockers are ruled and pinned; the plan is restructured into
**Gate A — JSON/CLI vertical slice plus adversarial soak** and
**Gate B — TUI and parity**, separately gated after the soak. No code and no
`PROGRESS.md` until the reviewer authorizes Gate A under the pinned
authorization update (new gaps still escalate; Gate B remains separately
gated).

Owner: `baton.implementer`. Rev 1 history: two gaps were routed and both are
now ruled; rev 1's analysis is retained in Git history rather than repeated
here.

---

## 1. Pinned rulings this revision builds on

The four blockers, as ruled 2026-08-14, now binding:

1. **Version: 11.0.0.** The application major is the protocol generation it
   serves; "Baton 2.0" survives as informal prose only. Deploy path is
   `app/<product>/v11/v11.0.0/`; the catalog entry, release notes and
   handshake all say 11.0.0. The 2026-08-11 "2.0.0" naming is chronologically
   superseded.
2. **Identity: short canonical handles + display names.** The protocol
   identity is a 6/6-cell handle (terminal display cells, wcwidth semantics,
   validated at registration, never at render); team/member/kind each may
   carry an arbitrary display name. The fresh v11 authority is configured with
   compliant handles; protocol-10 identities are not imported or rewritten.
3. **Re-readable, no receipts.** No at-most-once delivery object exists in
   v11. Every message is re-readable; nothing in the read path records
   delivery.
4. **Explicit seen transition; reads are pure.** A member's seen cursor
   advances ONLY via an explicit audited `mark_seen` transition. Every read —
   projection, JSON, TUI, search, count — is pure and writes nothing. `New`
   derives from the seen cursor and can never change as a side effect of
   looking.

Together, 3 + 4 give the slice one clean invariant, testable in a single
sweep: **the authority's bytes are identical before and after any sequence of
read operations by any viewer.**

The revalidation table of current-vs-superseded rulings from rev 1 is
unchanged and still governs; announcements remain ordinary messages with
`+`/`@`/`=>` cardinality as pinned.

---

## 2. Shape: two gates

    Gate A   authority + model + transitions + canonical projection
             + versioned JSON + `baton-work` CLI
             + the end-to-end scenario through the CLI
             + ADVERSARIAL SOAK (below)
             → reviewer may authorize directly if every ruling is
               represented and no new choice arises; new gaps escalate.

    Gate B   TUI rendering of the same projection + same-fixture parity
             → separately authorized only after the Gate A soak evidence
               is reviewed.

The module boundaries from rev 1 are unchanged, with one consequence made
explicit by the gate split: `tui/` does not exist until Gate B, and nothing in
Gate A may anticipate it beyond `projection.py` remaining renderer-agnostic.

    src/baton_work/
      authority.py   transitions.py   model.py
      projection.py  jsonapi.py       cli.py        (Gate A)
      tui/                                          (Gate B)

Boundary rules (test-enforced from A1): no imports from `baton_core`;
`projection.py` performs no writes; `jsonapi.py` and (later) `tui/` import
only `projection` and `transitions`.

## 3. Gate A serial steps

Each step's acceptance evidence is a test run plus the named break-sweep.
No step starts before its predecessor's evidence exists.

- **A1 — schema, sequence, identity.** Authority init with the pinned
  identity grammar (6/6 wcwidth handles + display names, registration-time
  validation); persisted monotonic publication sequence stamped inside every
  write transaction.
  Evidence: concurrent writers produce strictly increasing, duplicate-free
  sequence; restart does not reuse; an over-wide or zero-width-trick handle is
  refused at registration with the cell count in the error.
  Break-sweep: move the sequence stamp outside the transaction → the
  concurrency test fails.
- **A2 — Work + containment.** Atomic create-with-first-message; cycle-free
  parent enforcement; level-triggered roll-up readiness.
  Evidence: crash injection between Work insert and first message leaves
  neither; cycle refusal happens before any write.
- **A3 — edges + convergence.** `blocked_by` with union cycle check
  (containment ∪ required dependency); N-to-1 fan-in; terminal close
  recomputes every dependent from current blocker state; reopen recomputes
  back with no inverse-propagation path.
  Evidence: the LANG-42 three-consumer scenario plus reopen.
  Break-sweep: recompute replaced by event-walk → reopen test fails.
- **A4 — tags, obligations, seen, planned `Next`.** `+` list/wildcard
  expansion recorded with the publication, deduped per member+message; `@`
  exactly one endpoint with obligation row and respond/dispose transitions;
  `=>` exactly one endpoint, atomic `Current` change, with **planned `Next`
  as a transition pair**: a pass may set `Next` naming the intended return
  endpoint, and a later pass to that endpoint consumes it and is audited as
  `return`, distinct from an ordinary pass; a pass to any other endpoint
  leaves the planned `Next` visibly unconsumed rather than silently clearing
  it. **`mark_seen` is the only writer of the seen cursor.**
  Evidence: wildcard `@`/`=>` refused; unknown/retired kind refused at tag
  time; obligation lifecycle audited; `mark_seen` idempotent and audited;
  pass-with-`Next` records both facts in one transaction; the consuming pass
  is audited as `return` and clears `Next`; a non-consuming pass leaves
  `Next` set and the projection shows it as unconsumed.
  Break-sweeps: let a discussion read advance the cursor → the purity test
  (A5) fails; make an ordinary pass silently clear an unconsumed `Next` →
  the audit-trail assertion in A7 step 5 fails.
- **A5 — canonical projection, pure.** Home rows, breadcrumb, children,
  detail, discussion, per-member `New` (decomposable, derived from seen
  cursors over containment only), actionable obligations, available
  transitions, and **typed link traversal**: a Work's containment and
  dependency edges as typed relations (`contains`, `blocked_by`, each with
  direction and the far Work's id/title/status/`Current`), traversable
  deliberately across teams per the open-graph ruling — including the
  provider-side fan-in view of incoming `blocked_by` edges.
  Evidence: per-member counts on the fixture; **authority file hash identical
  before/after a full projection sweep by every configured member** — the
  rulings-3+4 invariant, run as one test.
- **A6 — JSON surface + CLI.** Versioned envelope (schema version, protocol
  version, viewer, consistency token); sequence-cursor pagination;
  `baton-work` verbs for every projection read and every transition —
  including a `links` read exposing A5's typed edges with stable ids so an
  agent drills across teams by relation, never by search — JSON in and out,
  no terminal formatting.
  Evidence: pagination across a same-second burst joins with no skip or
  repeat; incompatible version fails clearly; unknown fields ignored within a
  version; every mutating verb returns the committed record; the LANG-42
  fan-in is reachable from a consumer's Work by typed traversal alone
  (follow WEB-1's `blocked_by` to LANG-42, then LANG-42's incoming edges).
- **A7 — the scenario through the CLI.** The gate scenario (§4) executed
  end-to-end by driving `baton-work` as a subprocess — create, include (`+`),
  request-response (`@`), pass and return (`=>`), terminal close, dependency
  unblock — asserting the full ordered audit trail by sequence number.
- **A8 — adversarial soak.** A scripted multi-actor run against one authority,
  long enough to interleave everything with everything:
  * concurrent writers across several members and teams — sequence integrity,
    no lost updates, every audit row exactly once;
  * crash injection at every commit boundary of every transition, resumed and
    re-driven — no partial state observable, retries effectively-once by
    operation id;
  * adversarial inputs: cycle attempts through both graphs at once, wildcard
    and comma forms where cardinality forbids them, obligations to retired
    kinds, `mark_seen` races, pagination cursors across concurrent inserts,
    stale consistency tokens, malformed and over-versioned JSON envelopes,
    over-wide identities in every identity-bearing field;
  * a full-duration read purity check: interleaved projection sweeps by every
    member, authority hash compared against a write-quiesced baseline at each
    checkpoint;
  * the soak transcript, seeds, and failure taxonomy recorded in the finding
    folder as the Gate A evidence artifact.

## 4. The end-to-end scenario (CLI-driven in Gate A)

1. `web` creates WEB-1 (origin=external-report, classification=unknown) with
   its first message, atomically.
2. `+lang.rsrch` — attention lands, `New` rises for lang members, no
   obligation.
3. `@lang.rsrch` — one obligation in lang's actionable projection; WEB-1
   `Current` unchanged.
4. Lang creates LANG-42, relates WEB-1 `blocked_by` LANG-42, responds — the
   obligation is disposed.
5. `=>lang.impl` **with planned `Next` = lang.rev**, then the return pass
   `=>lang.rev` which **consumes the planned `Next`** and is audited as a
   return — one `Current` throughout, each pass atomic, and the audit trail
   distinguishes the outbound pass from the consuming return.
6. Terminal close of LANG-42 recomputes readiness; WEB-1 unblocks; the
   ordered audit trail is asserted end-to-end.

Gate B re-runs the same fixture through the TUI and the parity suite.

## 5. Gate B (planned now, executed only after Gate A soak review)

- **B1 — TUI rendering** of the canonical projection: home table, drill,
  breadcrumb, discussion view, and the transitions the JSON declares.
  Real-pty tests using the existing `_replay` harness discipline; no direct
  authority access (boundary test from A1 extended).
- **B2 — same-fixture parity.** One fixture through both surfaces: rows,
  counts, drill relationships and actionable state must agree.
  Break-sweep: skew the renderer by one row → parity fails.
- **B3 — packaged run.** The scenario through the packaged artifacts, not the
  source tree.
- TUI column priorities, sorting, keys, narrow layouts remain prototype-grade
  inside B1; they are presentation, not semantics, per the parity ruling.

## 6. Migration / clean-start boundary (unchanged)

Clean start: the v11 authority begins empty; protocol-10 history is neither
imported nor rewritten and stays readable via the deployed 10.2.0 tools. v11
ids carry an authority-uuid/generation qualifier so retained protocol-10
references can never silently resolve to new records. Any later import is a
separate gated project.

## 7. Deferred

Unresolved-`@` withdrawal; within-team duplicate retarget; reparenting,
promotion, Git dossier binding, restart-reconstruction projection;
retention/GC; invitations; route reassignment; streaming readiness; any
protocol-10 bridge. Each remains addable without schema migration — the test
it passed to stay deferred.

Planned `Next` is NOT deferred: set-on-pass, audited consuming `return`, and
the visible-unconsumed rule are in the slice (A4, A7 step 5). What remains
deferred about `Next` is only policy layered on top of it — route
suggestions or constraints on who may set or redirect it.

## 8. Failure and retry posture (unchanged, now soaked)

Every transition is one SQLite transaction; retries are effectively-once by
client-supplied operation id; crash injection at every commit boundary is
acceptance, and A8 additionally soaks it under concurrency rather than only
in isolation.
