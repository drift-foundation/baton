# Post-cutover review — changes required

Reviewer: `baton.reviewer`  
Reviewed: committed tool 4.0.0 / protocol 8 at `81f2fd7`  
Status: **service restoration accepted; cleanup changes required**

The live protocol-8 authority is healthy and the restored communication path
works end to end. I independently received a directed message through `wait`,
replied transactionally, received the broadcast notice through the same wait
path, and verified `doctor` reports no problems or warnings. Those checks close
the service-restoration phase.

The following items belong to the post-cutover cleanup phase. The first two are
integrity defects independently reproduced against fresh protocol-8 instances.
Attachment convergence is now required: Slawomir explicitly authorized the
protocol bump on 2026-08-07.

## R1 — Missing durable/deliverable bytes masquerade as a legitimate scrub

`Store._read_parts` uses a left join and returns `body=None` whenever a leaf's
`content_id` or `contents` row is missing. `_part_repr` then emits
`encoding: null`, which is the legitimate representation of an intentionally
scrubbed terminal transient body. Neither delivery nor `doctor` checks whether
the owning object is actually allowed to be manifest-only.

Independent reproduction:

1. Publish a durable directed message.
2. Simulate offline damage by nulling its leaf `content_id` and deleting the
   corresponding `contents` row with the guard triggers temporarily removed in
   the existing `_raw_corrupt` test helper.
3. `doctor` reports `ok: true`.
4. Claim delivery succeeds and emits the leaf with `encoding: null` and no
   bytes.

This silently converts durable evidence loss into an apparently valid
retention event. It also permits the same misreporting for pending or claimed
transient messages and for notices, whose bytes have not legitimately been
scrubbed.

Required correction and regressions:

- Delivery refuses `EXIT_DAMAGE` when any delivered leaf lacks bytes. A
  directed message is delivered only while pending/claimed, so transient
  retention does not make missing bytes valid on that path.
- Notice delivery likewise refuses missing leaf bytes.
- `doctor` validates payload presence against owner semantics. At minimum,
  manifest-only leaves are legitimate only for terminal transient message
  owners and transient close dispositions deliberately written without
  retained bytes. Durable owners, deliverable transient messages, notices, and
  durable close dispositions must retain every leaf payload.
- Add corruption regressions for a durable message, a pending/claimed
  transient message, and a notice, plus positive regressions proving legitimate
  terminal-transient message scrubbing and transient-close manifest-only
  storage remain healthy.
- Preserve manifest metadata after legitimate scrubbing and do not weaken the
  existing byte/hash/size or tree-manifest checks.

Relevant implementation: `baton_v6.py` `_read_parts`, `_part_repr`,
`_content_repr`, and the `doctor` content/parts pass.

## R2 — `doctor` omits reply-disposition manifest reconciliation

The owner-manifest pass includes message parts, notice parts, and only close
disposition parts (`response_message_id IS NULL`). A reply disposition owns no
parts because its response message owns them, but `doctor` never reconciles the
reply disposition's recorded content identity with that response message.

Independent reproduction:

1. Send, claim, and reply normally.
2. Simulate offline damage by changing the reply disposition's
   `manifest_sha256` to 64 zeroes.
3. `doctor` reports `ok: true`.
4. An exact retry fails because `_verify_retry` trusts the corrupted
   disposition as its idempotency authority.

The insert trigger checks this relationship only at publication; it cannot
diagnose offline damage after triggers are bypassed.

Required correction and regressions:

- `doctor` checks every reply disposition has a surviving response message and
  that its `content_type`, `manifest_sha256`, and retention agree with that
  response message.
- Corrupt each relationship independently and require `doctor` to report
  damage.
- Keep close-disposition owner-manifest checking unchanged.
- Preserve exact-retry behavior for healthy reply and close dispositions.

Relevant implementation: `baton_v6.py` `trg_disp_reply_hash`,
`_verify_retry`, and `doctor`'s `owner_manifests` list.

## R3 — Converge pinned attachments with parts in the next protocol

The implementation correctly records that protocol 8 still has two models for
one concept: typed ordered inline parts versus one untyped external attachment
stored in five `messages` columns and excluded from the content manifest.
That leaves an accepted criterion only partly met and would require another
protocol change for a note plus evidence, multiple external parts, or typed
external content.

The prior reason for deferral was avoiding a fresh-authority cutover. Slawomir
has explicitly accepted a protocol bump, so that reason no longer decides the
scope. Implement `work/finding-attachment-part-convergence/FINDING.md` before
this review closes:

- external storage is a leaf-part representation with the same media type,
  disposition, filename, order, size, and hash contract as inline content;
- `messages` has no `attach_*` columns and the manifest covers inline and
  external parts through one retry-identity mechanism;
- one message can mix an inline explanation with one or more pinned evidence
  parts;
- claim-time verification, skip-and-continue, `scan --damaged`, `doctor`, and
  audited quarantine work per damaged part without regressing queue liveness;
- damaged external bytes are never delivered, and healthy messages behind a
  damaged one remain deliverable;
- the CLI and public protocol documentation expose one truthful model rather
  than promising that every delivery has content while attachment-only
  deliveries return `content: null`.

Use the live-first upgrade contract: prepare and review the new release first,
then make the replacement authority live quickly. Do not mutate or migrate the
live SQLite authority in place.

## R4 — Explicit invalid or meaningless metadata is silently defaulted/dropped

`normalize_parts` uses `raw.get("content_type") or DEFAULT_CONTENT_TYPE` and
the same pattern for disposition; `content_spec` uses
`container_type or DEFAULT_CONTAINER_TYPE`. Therefore explicit falsey values
such as an empty content type or disposition silently become valid defaults
instead of reaching their validators.

Separately, `content_spec(None, None, content_type=..., disposition=...,
filename=...)` returns `(None, None)` and ignores all supplied metadata. The
current CLI exposes this with attachment-only `send` and bodyless `close`:
type/disposition/filename flags can be accepted and then discarded without an
error.

Required correction and regressions:

- Default only when a field is absent/`None`; reject explicitly supplied
  values of the wrong type or invalid/empty value.
- Reject per-part or container metadata when no corresponding content exists.
  Attachment convergence should naturally make attachment metadata describe
  the external part instead of being discarded; bodyless `close` must reject
  meaningless content metadata.
- Cover the programmatic Store surface as well as the CLI.
- Keep the separate zero-byte-body contract in
  `work/finding-nonempty-message-bodies/`; this item does not authorize an
  ad-hoc implementation of that finding.

## R5 — Close the claimed coverage and documentation gaps

- `test_multipart_survives_gc_and_expire` currently exercises only `expire`.
  Add a nested transient message/disposition component that reaches the actual
  `gc` deletion path, proving child-first deletion removes all parts and
  contents without orphaning.
- The handoff claims a 255-**byte** filename cap, while `validate_filename`
  enforces 255 Python characters. Either enforce the claimed UTF-8 byte bound
  with a multibyte regression or correct the handoff/public contract to the
  intended character bound.
- Refresh `work/finding-human-console/FINDING.md` before implementation: it
  still describes hiding seeds and sequencing after protocol 7, both of which
  are obsolete. Keep its product acceptance criteria; update only the shipped
  protocol assumptions and current sequencing.

## Re-review gate

Return a focused implementation response mapping each R item to code and
regressions. Required before approval:

- complete standalone suite passes from the venv;
- deterministic distribution rebuild and hash verification;
- built-executable smoke for inline text, inline binary, nested multipart,
  mixed inline/external parts, damaged-external skip-and-continue, reply,
  close, notice/wait, materialize, and `doctor`;
- schema refusal across the superseded live protocol and the fresh-authority
  cutover/runbook documented;
- no host-project or Drift-specific assumption in source, tests, executable,
  config schema, README, or protocol document;
- Git remains untouched by agents; Slawomir alone stages and commits.
