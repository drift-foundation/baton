# Owner disposition: SQLite sidecar effects during evidence opening

Resolved by owner M128249 (and M128251 for the coordinator), 2026-09-09.
The owner selected the explicit SQLite-sidecar exception, superseding the
strict-rule recommendation and pending-decision status below. Current terms
are pinned in FINDING.md, PLAN.md and the parent allocation's amendment.
Original decision support remains history; no independent acceptance implied.

W126880, review127071. This document is decision support, not approval or a new
planning Job. The exact current candidate is retained by
`evidence/review-127071-audit.json` and `evidence/review-127071-candidate/`.
The same operating boundary matters to independently allocated W126887.

Confirmed: the public non-writing database connection can create SQLite
coordination sidecars when the serving connection shuts down before its first
table read. The corrected candidate detects that condition and refuses, leaving
the files. Partial fixed states now refuse before connection. Full evidence is
in `review-2026-09-09T10-17-37Z.md`; the consumer's verified ordinary lifecycle
and retained committed-handoff proof are unaffected.

The decision is whether the no-persistent-store/journal-artifact requirement in
owner126833's allocation remains strict or receives an explicit SQLite-sidecar
exception. Recommendation: retain the strict requirement and keep this candidate
unaccepted until an enforceable opening/lifetime mechanism is specified. Further
guard-only changes do not discharge it. A wider mechanism, if needed, requires
an exact source/test allocation before implementation, using this existing Work.

If the owner prefers an exception, pin it first: distinguish database contents
and committed evidence from -wal/-shm creation/maintenance; state whether the
exception also covers refused opens; preserve mode=ro, coherent committed reads,
identity/schema checks, mutation refusal and unchanged serving semantics. The
present blanket no-artifact rule cannot silently coexist with that exception.
Independent review and any affected test-authority amendment still apply.

The implementer's other suggestions do not independently solve the requirement:
checking that a writer is attached does not ensure it stays attached, and
device/inode attribution does not authorize deleting concurrent SQLite files.
No post-hoc cleanup, immutable-live-file assumption, new lifecycle Job or
consumer workaround is proposed. Owner disposition precedes another local
implementation allocation; current gates, claims and source authority remain.
