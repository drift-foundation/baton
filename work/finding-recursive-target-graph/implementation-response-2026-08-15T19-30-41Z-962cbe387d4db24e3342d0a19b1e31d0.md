# Reconciliation of the committed WS-6 tree and the next-phase proposal

In reply to question `962cbe387d4db24e3342d0a19b1e31d0` (claim
`3cb88f08a810ed05f00ca92e9f541316`). No implementation has begun; this
is planning only.

## Reconciliation: committed tree vs FINDING/PLAN

Commit `9c799f4` ("Add WS-6 portable dossier bindings and the
filesystem location domains") contains exactly the accepted Slice A+B
tree; `git status` shows a clean source tree with only dossier records
(this finding's review/response files) uncommitted. Checked against
the live documents:

- Every WS-6 design checkbox in PLAN.md (binding shape/authority,
  open-record and closure semantics, artifact references, validation
  boundary, template boundary/distribution/release-asset rulings,
  root-address vocabulary, reference availability/scope/unbound,
  binding path shape, root retirement, distribution assets, three
  location domains, placement/Git boundary, parallel-trial boundary,
  workflow-test boundary) is implemented and covered by the accepted
  evidence (test_ws6_bindings 20, test_ws6_matrix 24, test_ws6_project
  16 incl. R92–R99, WF-13/14/15 source+packaged; final gate 511
  parallel + 3 serial; review-2026-08-15T19-13-12Z.md).
- The mid-Slice-B FINDING pins that were "held for a future slice"
  are all long since delivered by earlier accepted slices: the
  four-outcome terminal close with mandatory rationale and
  `duplicate_of` (WF-10), and Work revisions as whole-message
  promotion (WF-11). Cancellation exists exactly as pinned: an atomic
  `cancelled` close by Current, no cascade, no child bypass.
- No FINDING ruling within this finding's scope remains unimplemented.

Recorded open boundaries that are deliberately NOT implementation
debts of this finding: the optional pure `check` convenience
(explicitly deferred, must never become a third onboarding step); the
v10→v11 adoption/cutover (a separately planned, explicitly
coordinated operation); a consistent SQLite authority snapshot
procedure (ruled "a separate explicit recovery procedure outside
WS-6"); production deployment/mailbox creation/migration/shutdown
(Slawomir-owned manual operations).

## Proposed next bounded phase: v11 release candidate and cutover readiness

The implementation program of this finding is complete, so the
natural next phase is making the accepted product OPERABLE without
touching anything live.

**Objective.** Produce the first exact versioned `baton-work` v11
release candidate through the existing build_release/deploy tooling,
prove the full three-domain story end-to-end against isolated
temporary targets only, and deliver the two operator documents the
recorded boundaries call for — a cutover runbook and a consistent
authority snapshot/recovery procedure — for Slawomir's manual
execution.

**Scope (in).**
1. Release engineering: an exact versioned candidate of the
   baton-work product (bin zipapp + doc + conf + tmpl release assets)
   through build_release/deploy, with manifest and digest evidence;
   nothing installed outside temp directories.
2. WF-16, source+packaged: install the exact candidate into a
   TEMPORARY distribution root -> `init`/edit/`activate` a TEMPORARY
   coordination home -> `bootstrap` a TEMPORARY project root -> drive
   a representative work story (create/bind/say/refs/close) through
   the INSTALLED product only -> prove distribution immutability,
   relocation, and that nothing outside the temp targets was read or
   written.
3. The snapshot procedure: a documented, tested consistent-backup
   method for a live authority (SQLite backup API or checkpointed
   copy), exercised against TEMP authorities under concurrent
   mutation; delivered as an operator procedure (tool shape per
   decision D3 below).
4. The cutover runbook: a document (docs/) with the exact ordered
   manual steps, verification checkpoints, and abort points for
   Slawomir to install the release, create the production
   coordination home, and later cut over from v10 — explicitly NOT
   executed by this phase.

**Scope (out, held).** Any read or write of the live v10 mailbox or
its runtime; production deployment, mailbox creation/migration,
shutdown, cutover; TUI expansion; the deferred `check` verb unless
D1 rules it in.

**Review gate.** Focused new tests + WF-16 both modes green; the full
`just test-v11` gate green; the runbook and snapshot procedure
reviewed as documents against the recorded boundaries; break-sweeps
for every new guard; stop before anything production-facing.

**Slawomir decisions / blockers.**
- D1: does the optional pure `check` convenience (same validator,
  read-only) ship in this phase, or stay deferred?
- D2: the candidate's product name/version for the release manifest
  (first v11 line entry alongside the existing baton/baton-tui
  products).
- D3: snapshot delivery shape — a CLI verb on the v11 surface, or an
  operator script/document only?
- D4: the production location names the runbook should print
  (distribution root, coordination home path) — documentation only,
  no path is created.

No source, template, build, or document change begins until the
reviewer's disposition of this proposal.
