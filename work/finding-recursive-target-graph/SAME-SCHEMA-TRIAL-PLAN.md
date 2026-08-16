# Same-schema v11 trial iteration

## Goal

Deliver the largest useful next v11 trial improvement that can restart against
the existing `/home/sl/baton-v11` authority. This is an explicit
schema-preserving iteration, not the fresh-authority release.

## Hard compatibility gate

- SQLite `SCHEMA_VERSION` remains `14`.
- No migration, shadow database, replacement authority, or data rewrite is
  added.
- The packaged next executable must reopen the current authority and preserve
  its complete Work, Thread, Message, obligation, operation, edge, and event
  history.
- Projection and client grammar may advance. Configuration changes may use the
  existing audited configuration-regeneration model only if the same database
  remains valid and recoverable. If any queued item cannot satisfy this gate,
  stop that item and defer it rather than widening this release.

`8b92cb10-W10` (three-level Work priority) is explicitly deferred because it
requires new persisted Work state. It remains open and is not a dependency of
the replacement same-schema release gate.

## Serial implementation order

Work remains independently reviewable and is handed to the implementer one at
a time. Each item revalidates its exact repository finding before code changes,
reports evidence in its v11 Thread, and passes Current back to its original
review endpoint.

1. TUI conversation and safety:
   - `W7` — split-pane Work and Thread navigation (start here);
   - `W8` — formatted Thread messages;
   - `W5` — timer-based automatic refresh;
   - `W9` — exit confirmation;
   - `W6` — `defct` compact classification label.
2. Command and identity foundation:
   - `W13` — key/value operation grammar;
   - `W12` — canonical Work id in details;
   - `W34` — ultra-short authority-local Work selectors.
3. Live list projections:
   - `W27` — separate `Blk` and `Dep` counters;
   - `W36` — `Msg/My` counters.
4. Grammar-dependent TUI features:
   - `W14` — context-sensitive command assistance (blocked on `W13`);
   - `W19` — multiline `::` batch mode (blocked on `W13`).
5. Configuration and distribution cleanup:
   - `W4` — explicit repository paths in `baton.json`, only if audited config
     regeneration preserves the existing schema-14 authority;
   - `W3` — valid generated activation command;
   - `W2` — installed/current-facing product name `baton`.

## Review and release

Every item receives focused regressions plus `just test-v11` in proportion to
its boundary. The final packaged gate must reopen a byte-preserved copy of the
current schema-14 authority and exercise both JSON and TUI reads before and
after restart.

V10 remains the reliable wake, handoff, and completion-notification channel
during this iteration. V11 is the desired workflow record: the implementer
posts progress/evidence in the corresponding v11 Thread and passes Current back
to its planned review endpoint. The implementer also reports that return over
v10 so the reviewer is reliably awakened. On every v10 completion, the
reviewer verifies both the repository result and that v11 records the matching
message/ownership state before accepting the item. Neither channel silently
stands in for the other while v11 wake delivery remains under trial.

The existing release Work `W11` already depends on fresh-schema `W10`, and the
current protocol has no dependency-withdrawal transition. Slawomir closes W11
`cancelled` with a supersession rationale and creates a follow-up same-schema
release Work containing only the eligible dependencies above. W10 is not
closed, deleted, or treated as resolved.
