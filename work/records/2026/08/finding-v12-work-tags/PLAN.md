# Plan: v12 Work labels

**Status:** approved contract; serial implementation children dependency-gated
as Baton Work `W28880`

1. [done 2026-08-27] Record the confirmed product requirement and bind it to
   one authoritative Baton Work.
2. [done 2026-08-28] Revalidate the current v12 Work schema, identity,
   operation journal, session surface, projection and schema-open policy;
   distinguish user Work labels from Thread–Work labels and OCI runtime labels.
3. [approved 2026-08-28] Approve or replace the proposed grammar, normalization,
   limits, scope-resolved mutation authority, terminal-lifecycle rule,
   non-inheritance and repeated-filter composition recorded in `FINDING.md`.
4. [approved 2026-08-28] Approve or replace the proposed indexed live set,
   append-only attributable events, convergent no-op semantics, replay and
   snapshot projection contract.
5. [approved 2026-08-28] Approve or replace the proposed create-time `label=`,
   distinct `label-work`/`unlabel-work` verbs, exact list/search filters and
   clear failure behavior.
6. [approved 2026-08-28] Approve or replace the proposed wrapped detail,
   optional wide labels column and persistent filter disclosure in the modular
   v12 TUI.
7. [blocked on W16821 before implementation] Consume the canonical
   principal/effective-scope/grant authorization seam. Do not ship a temporary
   authority derived from Route, claimant, participant spelling or membership.
8. [done 2026-08-28] Decompose implementation into independently reviewable,
   serial children: W29400 authority (blocked on W16821), W29401 protocol/CLI
   (blocked on W29400), and W29408 TUI (blocked on W29401). W29400 owns the
   explicit schema upgrade/rebuild disposition.
9. [pending implementation] Add the positive, negative, authorization,
   lifecycle, retry, race, snapshot, filter, non-interference and TUI
   conformance matrix recorded in `FINDING.md` before acceptance.
10. [approved 2026-08-28 by M34988] W29400 adds one generic attributable,
    replayable Work-creation pipeline. The authority-generated trusted-
    bootstrap kind is first; initial labels share its immutable creation act.
    Preserve the envelope for a later genuinely authorized creation kind and
    never backfill bootstrap history.
