# Audit: remaining findings against the live protocol-10 boundary

Written before editing, as asked. Protocol 10 is released and committed; the
live authority runs its schema. Nothing below proposes changing it.

Two things changed the sorting, and both are consequences of what actually
landed rather than opinions about it:

- **The oracle is retired.** Several items were protocol-10-bound ONLY because
  they changed `_impl.py` while `test_core_parity.py` measured it against the
  frozen `baton_v6.py`. That measurement no longer exists, so that reason for
  bundling them is gone.
- **Audiences shipped.** Items deferred because "authorization must be
  designed after the immutable publication-time audience snapshot" are
  unblocked: `publication_audience` and `notice_audience` exist, are frozen at
  publication, and are live.

## 1. No-cutover block — lands against the present authority

### 1a. Non-empty message bodies — `finding-nonempty-message-bodies`

No schema change; the finding says so itself, and legacy zero-byte rows stay
valid, deliverable and doctor-clean.

REPRODUCED just now against a fresh protocol-10 instance:

    s.send('a.one','a.two',kind='k',body=b'')
    -> stored part: 0 bytes, sha e3b0c44298fc1c14...

**This one has cost us real work in the last hour.** Repeated review messages
arrived with zero-byte bodies, so their entire content was the subject line,
and this audit's own source umbrella records the identical failure: "Both the
original message and its correction arrived with ZERO-BYTE bodies, so
everything above comes from subject lines. That is the whole record, which is
exactly the reason not to design from it."

A subject is a summary written for a list. Designing from one is how a
specification gets invented by the reader.

**Operational consequence that must be decided, not discovered:** the reviewer
is currently sending zero-byte bodies routinely. Enforcing this will make
those sends FAIL until the sending path supplies content. That is the point of
the change, but it lands as an immediate behaviour change for a live
participant, so it should be announced before it ships rather than diagnosed
after.

### 1b. External-part default type — `finding-attach-part-default-type`

REPRODUCED: `_impl.py:447` defaults every node without a declared type to
`DEFAULT_CONTENT_TYPE`, regardless of whether it carries `attach`.
`DEFAULT_ATTACHMENT_TYPE` is applied only on the `send(attach=...)`
convenience path, so the two authoring surfaces still disagree about the same
file, and the CLI stopgap still covers exactly one caller.

Its only blocker was the oracle decision, and that is resolved: retired. No
schema, no wire change.

ONE RISK, small and worth stating: the correction changes the media type
recorded for NEW parts that omit a type on an `attach` node, and the media type
participates in the manifest digest. Stored rows do not change and committed
retries stay idempotent, because their manifests are already recorded. The
exposure is an operation authored before the change and retried after it — a
deploy-window concern, not a data one.

### 1c. Participant-scoped read — `finding-cli-read-authority`, partially

REPRODUCED: `materialize` still takes a bare `message_id` with no
`--participant` option. In a mailbox holding ten teams, any participant can
project any other's message content, and the read leaves no identity anywhere.

The authorization itself needs NO schema: the immutable audience is already
stored. Extending `materialize` to address a NOTICE the participant has
already seen is likewise no-schema — `notice_audience` says who is a party,
and re-reading retained bytes creates no second receipt, so at-most-once is
untouched.

**But the audit half is schema-bound** (see 2f), which is the sharpest thing
in this audit: the finding says "an unrecorded privileged read must not be the
final contract". If block 1 ships authorization without recording, that is a
deliberate partial delivery and must be stated as such, not left to look
finished.

### 1d. TUI claim-on-highlight dwell — umbrella §"Claim-on-highlight dwell"

TUI-only, monotonic-clock, no wire or schema change. Independent of 1a-1c and
can proceed in parallel with them. Its acceptance list is already written and
unusually complete.

### 1e. `dump` renders `"parts": null` on message records — CLOSED, does not reproduce

**No longer reproducible; no source change made.** Verified 2026-08-10 against
a fresh protocol-10 instance: the `messages` table has no `parts` column, so
`SELECT *` cannot emit that key, and a dump's message record carries none.

    message keys: completed_ts, content_type, created_ts, from_participant,
                  id, kind, manifest_sha256, outcome, publication_id,
                  responds_to, retention, state, subject, thread_id,
                  to_participant

The finding described an older dump shape; the symptom disappeared on its own,
most likely when messages stopped carrying attachment columns during the
multipart work. The structural observation behind it is still true — part rows
live in sibling top-level tables — but that is a faithful rendering of the
schema, and the finding itself calls it a clarity item rather than a defect.

Recorded as closed rather than fixed: inventing a source change to satisfy a
symptom that no longer exists would be worse than leaving the schema legible.

## 2. Schema-bound — one future boundary, protocol 11

None of these can land against the live authority without a new protocol
number and a fresh-authority cutover:

- **2a. Decision obligations, LIKE/DISLIKE answers, multi-recipient voting.**
  New request/obligation and answer records with an immutable audit; the
  umbrella's own ruling says `transitions` cannot carry it today (no answer
  payload, message/claim entities only).
- **2b. Append-only claim progress.** New claim-bound append-only stream.
- **2c. Targeted blockers.** Distinct contract from 2b: a directed participant
  relationship that can exist without a claim and is viewer-relative.
- **2d. Priority, queue ordering, fairness.** Changes selection order, which
  `_first_deliverable` and readiness both depend on.
- **2e. Durable per-participant dismissal, plus bulk selection and Trash.**
  Ruled as a protocol-authority table, explicitly NOT a console-side store.
- **2f. Recorded privileged reads.** The audit half of 1c.
- **2g. Presence leases.** Ruled last, and nothing depends on it.
- **2h. External-reference semantics.** **Added by Slawomir 2026-08-11,
  superseding the earlier seven-item completeness.** Protocol 11 removes the
  external hash-pinned `--attach` contract and uses references whose targets
  may float, change, or disappear without damaging delivery or authority
  health. Git commit-addressed references remain proposed design work in
  `work/finding-protocol-11-reference-semantics/`.

Designing these as ONE boundary is right, and the reason is the same one the
umbrella gives for protocol 10: discovering an eighth item after cutover is the
failure the inventory exists to prevent. I would add that 2a-2e all touch
either ordering or per-participant view state, so designing them together is
not merely a cutover convenience — they interact.

## 3. Exploratory — do not pull in

- **Vi Normal/Insert modes.** The finding says outright it is not a confirmed
  direction, has no acceptance criteria, and that `Esc` remains CANCEL. Its
  entire record is subject lines from zero-byte messages.
- **Archive.** Reserved by name as distinct from Trash, with no contract yet.

## Recommended first block, in dependency order

1. **1a non-empty bodies** — first, because it is the one actively costing us
   information, and because every later finding's evidence arrives through
   messages.
2. **1b default type** — independent of 1a; both touch validation/normalization
   in `_impl.py`, so doing them adjacently keeps one review context.
3. **1c participant-scoped read, authorization only** — after 1a/1b, and only
   with the audit split stated explicitly.
4. **1d TUI dwell** — parallel; touches no core file the others touch.

1e can ride with 1c.

Files: `baton_core/_impl.py` (1a, 1b, 1c, 1e), `baton_core/authoring.py`
(1b stopgap removal), `baton_tui/state.py` and `driver.py` (1d),
`test_core_conformance.py`, `test_tui_driver.py`, README and
`AGENTS-MAILBOX-PROTO.md`.

Acceptance: the twelve regressions listed in the non-empty-bodies finding; a
parts-path/convenience-path agreement test plus explicit-type-still-wins for
1b; a non-party refusal and an audience-member success for 1c, with the
notice-reread case creating no second receipt; and the dwell finding's own
eleven-item list for 1d. Each break-checked.

## Decisions Slawomir must make

1. **Does the unscoped `materialize` survive at all?** As an operator tool, or
   does `--participant` become required? And does `human.slawomir`'s
   `recovery` capability grant projection of anything?
2. **Must an authorized read be RECORDED?** If yes it is schema-bound and
   moves to the protocol-11 bundle, and block 1 ships authorization alone —
   which needs to be an explicit choice, because a read surface that refuses
   outsiders but records nothing looks complete.
3. **Announcing 1a before it ships.** It will break the reviewer's current
   zero-byte sends on contact.

No edits started. Nothing staged.
