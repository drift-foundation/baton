# Plan

**Status — 2026-08-18:** complete; independently reviewed and signed off in
`review-2026-08-18T01-34-16Z.md`.

**Ownership boundary (ruled at review round 1).** W245 owns the authority,
projection, CLI grammar and help, TUI, and the directly coupled tests and
docstrings. It does NOT own the public documents. `README.md`,
`docs/EFFECTIVE-BATON.md`, `docs/AGENTS-MAILBOX-PROTO.md`, and
`docs/BATON-WORK.md` belong to W103/W104; seq 259 had already ruled that
EFFECTIVE-BATON and its executable proof are updated under W104 AFTER W245
lands, through a new W104 review pass. The terminology edits already present
in those four files are incidental and remain UNREVIEWED W103/W104 work —
they are not accepted by this Work's review, and the known-incomplete
statements in `BATON-WORK.md` (`active` (JSON), mutation authority given to a
"Current handler") are deliberately left for that pass rather than finished
here.

1. Revalidate every authority, projection, grammar, readiness, ACP, and TUI
   use of endpoint-valued `current` and claimant-valued `active`. **Done:** the
   exact source and test surfaces are recorded in `FINDING.md`.
2. [done] Rename storage routing columns to `route_team/route_kind`, claimant columns
   to `current_team/current_member`, the public routing projection to `route`,
   and make public `current` the structured exact claimant or null. Keep
   authorization derived from route.
3. [done] Update every transition atomically: handoff changes route/phase and clears
   current; claim populates current; all release paths clear it.
4. [done] Split filters: `route=` selects endpoint eligibility (`route=me` means this
   viewer is eligible), while `current=` selects the exact claimant
   (`current=me` means this viewer holds the claim). Update canonical JSON,
   Events, CLI output, readiness envelopes, ACP prompt generation, and TUI
   columns without compatibility aliases.
5. [done] Add positive, negative, retry, race, restart, configuration-change, blocked,
   parked, waiting, release, terminal, packaged-client, JSON/TUI parity, and
   stale-consumer tests.
6. [done] Run the complete v11 gate and independently review before producing
   the next trial distribution and fresh authority.
