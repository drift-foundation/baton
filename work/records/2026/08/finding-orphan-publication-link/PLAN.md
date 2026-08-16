# Dispositioning the orphaned replies

## Ruling — fresh authority, no backfill

Slawomir chose option C on 2026-08-10. The 28 historical reply rows are not
operationally valuable enough to justify a repair ceremony. Do not implement
or run a backfill and do not port those rows into the replacement authority.

Keep communications live on the current authority until the replacement build
and cutover procedure are ready. Then archive the old authority intact and
initialize a fresh one through Baton's supported lifecycle; never rewrite or
delete the old SQLite state with raw SQL. Communications-first cutover remains
the rule: prepare the replacement, switch quickly, and let participants resend
anything still relevant.

Slawomir separately approved `messages.publication_id NOT NULL` on 2026-08-10.
Build that invariant into the fresh authority's schema before cutover. Do not
migrate, backfill, or rewrite the archived authority merely to satisfy it; the
old authority remains an intact historical artifact under its original schema.

Written before code. The code half of the defect is FIXED and pinned — `send`
and `reply` share one `Store._publish`, and `doctor` now reports orphan links.
This plan is only about the rows that already exist.

## The state

The live authority holds 28 directed messages with `publication_id IS NULL`,
every one a response created by `reply` before the fix. `doctor` reports
`ok: false` for them, correctly and for the first time.

Fresh instances cannot acquire new ones: both creation paths publish, and a
regression asserts no directed message exists without a publication.

## Why this needs a ruling rather than a script

AGENTS.md: "Never mutate it with raw SQL or manually reconstruct protocol
state." A backfill is reconstruction by definition. The mitigating fact is
that nothing has to be INVENTED — every field a publication needs is already
on the message row it would describe:

    publications.from_participant  <- messages.from_participant
    publications.kind              <- messages.kind
    publications.subject           <- messages.subject
    publications.thread_id         <- messages.thread_id
    publications.retention         <- messages.retention
    publications.outcome           <- messages.outcome
    publications.content_type      <- messages.content_type
    publications.manifest_sha256   <- messages.manifest_sha256
    publications.created_ts        <- messages.created_ts
    publication_audience           <- {messages.to_participant}
    possible_duplicate             <- 0

So the reconstruction is a derivation, not a guess. The one field with no
source is `publication_id`, which is new identity rather than recovered fact.

`possible_duplicate` is 0 because these senders asserted nothing. Writing 0 is
recording that no warning was given, which is true.

## Three options

**A. Audited repair ceremony.** A new maintenance-gated verb that derives one
single-recipient publication per orphan and audits the count. Restores the
invariant, makes `NOT NULL` possible afterwards, and leaves an audit record
saying exactly what was reconstructed and when.

**B. Leave them.** They stay orphaned, `doctor` keeps reporting them, and
`NOT NULL` can never be added. The 28 messages permanently deliver
`audience: []`. Honest, and it keeps the evidence — but it means the schema
can never state the invariant, so the next path that forgets to publish is
caught by a doctor warning nobody reads rather than by the database.

**C. Fresh authority again.** Consistent with the protocol-10 cutover
precedent and costs the history a second time. Disproportionate: the defect
is repairable and the history is now the record of this work.

**A is what I would do**, and the reason is B's tail: an invariant the schema
cannot state is an invariant that depends on every future author remembering
it, which is exactly how this defect happened in the first place.

## What A must not do

- NOT run automatically, and not as a side effect of any other verb. It is a
  ceremony, gated on maintenance, invoked deliberately.
- NOT touch a message that already has a publication.
- NOT invent a `created_ts` -- the publication is stamped with the message's
  own, because the publication describes an event that already happened.
- NOT be reusable as a general "fix my database" surface. It repairs this one
  named defect and refuses everything else.
- NOT run against the live authority before a snapshot exists.

## Order

1. ruling on A/B/C;
2. if A: the ceremony, break-checked, with a test asserting it is a no-op on a
   healthy instance and exact on an orphaned one;
3. snapshot the live authority through the existing `snapshot` ceremony;
4. run the repair; `doctor` returns to ok;
5. only THEN `NOT NULL` on `messages.publication_id`, which is a schema change
   and therefore an outage for the human console until migrated in place.

Step 5 is separable and may be deferred indefinitely without leaving anything
broken; steps 1-4 stand on their own.
