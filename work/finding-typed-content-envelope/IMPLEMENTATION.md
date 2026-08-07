# Implementation handoff — typed, multipart-capable content envelope

Implements `FINDING.md` in this folder, authorized 2026-08-07 after commit
`b7a7a6f`. Rides inside protocol 8 as the finding required, so the fresh
authority takes ONE teardown rather than two. No Git mutation; Slawomir stages
and commits.

    tool 4.0.0   protocol 8
    artifact_sha256      a3e5f7f1ed647102460b763f163364b0a3656db06abce81754fb3b00cb36a908
    source_sha256        3542bb23e0ea76eb2bde987142a260f63a02873c91030186fff8d6b3f175e964
    protocol_doc_sha256  c38bd1dba2dd1c7b6ef36826b2f366d4cd0b3f4b6ec30ebde155a56b9d26533b

**365 tests pass, 0 fail** (319 carried forward, 46 new).

## Version numbers — read this first

**The protocol stays 8. The tool goes to 4.0.0.** That combination is
deliberate and is the one thing most likely to look like a mistake.

Protocol 8 has never existed on disk. The seedless-identity commit defined it;
nothing was ever initialized at it, because the finding pinned this work to
land first. So the schema this release ships **is** protocol 8 as released, and
both breaking changes cost one cutover — which was the entire argument for the
sequencing.

The tool version bumps because the delivery envelope changed breakingly between
two commits, and the tool version is what distinguishes them.

An instance created by the pre-release 3.0.0 build is therefore not a
protocol-8 instance. Verified: exact schema-text validation refuses it with a
precise missing/extra/changed diff and **exit 6**, on both `claim` and
`doctor`. It fails closed rather than misreading it.

## The contract as built

Every body is an ordered tree of typed parts, owned by a message, a notice, or
a close disposition. A single-part message is not a special case anywhere below
the authoring API.

    "content": {
      "content_type": "multipart/mixed",
      "manifest_sha256": "...",
      "parts": [
        {"content_type": "text/markdown; charset=utf-8",
         "disposition": "inline", "filename": null,
         "size": 17, "sha256": "...",
         "encoding": "text", "text": "# Handoff\nReady.\n"}
      ]
    }

**Exactly one representation per leaf, named by `encoding`.** `text` for
`text/...; charset=utf-8`, `base64` for everything else, never both. The choice
follows the DECLARED type, not whether the bytes happen to decode.

That last clause is the substance of the change. The old `utf8` field appeared
only when the bytes decoded, so the same key came and went with the payload and
a consumer had nothing stable to dispatch on. `test_representation_follows_the_
declared_type_not_the_bytes` pins it: identical ASCII bytes under two declared
types now deliver through different keys.

`encoding` is `null`, with neither content key present, once a transient body
is scrubbed. **The manifest outlives the payload** — a consumed transient part
still states its type, size and hash.

## Multipart readiness is real, in storage as well as delivery

The finding was explicit that wrapping one body in an array buys nothing.

**Parts are their own rows.** A new `parts` table holds
`(owner_kind, owner_id, parent_part_id, ordinal, content_type, disposition,
filename, content_id, sha256, size)`. Order and metadata are rows, not columns
on the owner and not a serialized blob. `messages` lost `content_id` and
`content_sha256` entirely; it keeps a container `content_type` and a
`manifest_sha256`, and **there is no column left that could hold a second
part's metadata** — asserted directly in
`test_parts_are_rows_with_explicit_order_not_owner_columns`.

**Nesting works today, not in principle.**
`test_nested_containers_need_no_schema_change` round-trips
`multipart/alternative` inside `multipart/mixed` beside a binary attachment
part, and asserts the set of tables is **unchanged** before and after. That is
the finding's own test of whether this was done properly.

**Ordering is enforced at every level by two PARTIAL unique indexes**, not one
composite index. SQLite treats NULLs as distinct in a `UNIQUE` constraint, so a
single index over `(owner, parent_part_id, ordinal)` would leave top-level
ordinals — the ones with a NULL parent — completely unconstrained. I nearly
shipped exactly that. `test_part_order_is_uniquely_constrained_at_every_level`
checks both levels because one of them was the easy thing to get wrong.

**Containers and leaves are separated by schema CHECKs**, not only by the
Python that normally writes them: a `multipart/*` row may hold no bytes,
`content_id` or `filename`; a leaf must have `sha256` and `size`. Same standard
as every other guarded table here.

## Retry identity covers the manifest, not the bytes

`_verify_retry` compares `manifest_sha256`, computed over the canonical JSON of
the ordered tree — `content_type`, `disposition`, `filename`, `sha256`, `size`,
and nesting, in order.

So two retries that differ **only** in part order, media type, disposition or
filename are different operations and fail closed, even though every byte
matches. That is this finding's central requirement and it has four
regressions: a parametrized one over each of the three metadata fields, one for
reordered parts, and one proving `reply` and `close` do not diverge. Each also
asserts the *unchanged* retry still redelivers, so a refusal cannot be a
broken retry path masquerading as a check.

The manifest survives scrubbing, which is the other reason to compare it rather
than the payload.

Media types canonicalize to one spelling before hashing, so
`text/markdown; charset=UTF-8` and `TEXT/Markdown;charset=utf-8` are not two
different contents.

## Open questions from the finding, answered

**Default type.** `text/markdown; charset=utf-8`. Every body this project has
carried is Markdown, `materialize` has always emitted `.md`, and the protocol
document names Markdown as the review-document format. The type is stated in
every delivery, so nothing is implicit downstream.

**Undeclared type — rejected or defaulted?** Defaulted, but the default
declares `charset=utf-8`, so **non-UTF-8 bytes are refused at publication**
with the fix named. Falling back to base64 whenever the bytes failed to decode
would put back exactly what this envelope removed: a representation that
changes with the payload while the declared type describes something the
content is not. A consumer acts on the label; a wrong label is worse than a
refusal. `--content-type application/octet-stream` is the whole fix and
round-trips losslessly.

**charset on `text/*` is required**, per RFC 7763 for `text/markdown` and
because the delivery encoding depends on it. A bare `text/plain` is refused
with the corrected spelling in the message rather than silently rewritten.

**`filename` is advisory only.** Baton never opens, creates, or names a file
from it — `materialize` derives its name from the caller's explicit `--prefix`
and `--dir`, pinned by `test_materialize_ignores_the_advisory_filename`. It is
still validated (no separators, NUL, control characters, `.`/`..`, leading
`-`, 255-byte cap), because the consumer downstream may be less careful and a
transport that forwards `../../authorized_keys` unchallenged has helped.

**Size limits: per message, summed across parts.** Bounding each part instead
would let a caller carry an unbounded transient payload by splitting it.

**Alternatives are a nested part list**, not siblings with a preference order —
so `multipart/alternative` needs no new columns and nesting is uniform.

**Attachments did NOT converge.** See below.

## What I would review hardest

**The attachment scope line.** The finding asked that attachments and parts
"converge rather than coexist unexplained". I explained the relationship and
did not converge them. An attachment is still five columns on `messages`, still
limited to one per message, still mutually exclusive with content, still
untyped.

I judged real convergence to be a second protocol-breaking change touching
`verify_attachment`, `_first_deliverable`, `quarantine-attachment`, `scan`,
`doctor` and the `messages` CHECK constraints — large enough to endanger the
skip-and-continue behaviour from `work/finding-damaged-attachment-queue/`, and
not on the finding's *required* list. **This is the judgement call most worth
overriding if you disagree**, because the window argument runs the other way:
riding inside protocol 8 was free, and doing it later costs its own teardown.

I recorded it as `work/finding-attachment-part-convergence/` rather than
leaving the explanation to become the permanent answer, and marked the
partially-met criterion in the superseded finding rather than claiming it.

**`doctor`'s new manifest check.** It recomputes each owner's manifest from
stored parts and compares. This is the only check that catches a part dropped,
reordered or retyped behind the API — every remaining byte stays valid, so
nothing byte-level notices. Two regressions corrupt a live instance through
`_raw_corrupt` and assert both `doctor` failure and `EXIT_DAMAGE` on delivery.
If the digest is computed differently in either place, these pass while the
check is useless; that is the failure mode to look for.

**Deletion order.** `parts.parent_part_id` is a self-referencing foreign key,
so `gc` and `expire` must delete deepest-first or orphan children behind their
parents. `_parts_depth_first` computes depth with cycle detection.
`test_multipart_survives_gc_and_expire` exercises a nested tree through
`expire` and asserts no part and no content row survives.

**Tests I rewrote rather than deleted.** Four pinned behaviour the finding
changes. Each was replaced at the same seam, not dropped — check none lost a
property:

- `test_non_utf8_and_empty_bodies` — now asserts one representation chosen by
  declared type; gained `test_undeclared_binary_is_refused_not_mislabelled`,
  which pins the refusal AND the lossless round-trip once declared.
- `test_notice_body_lossless` — parametrized over `(body, content_type)`; still
  asserts byte-exact round-trip and hash equality, now also that exactly one
  representation key is present.
- `test_transient_scrub_in_consuming_txn` — asserts the bytes go and the
  manifest, type, size and hash stay.
- `test_transient_close_retains_identity_not_bytes` — same, at the disposition
  seam.

The rest of the suite churn was mechanical (`msg["body"]` → helper,
`content_sha256` → `manifest_sha256`, raw-SQL column names). **Check the diff,
not the test count** — that is where the damage hid last round.

## Not done, deliberately

- **No rendering, no content negotiation, no transformation.** Baton moves
  bytes and describes them accurately. Notably: no transcoding — a
  `text/...; charset=iso-8859-1` part is delivered as base64 rather than
  converted, because a transport that rewrites content is a transport that can
  corrupt it.
- **No multipart authoring over the CLI.** The CLI publishes one part
  (`--content-type`, `--disposition`, `--filename`); the store API writes
  arbitrary trees and is what the multipart tests use. The finding permits
  restricting writers provided readers do not assume the restriction, and
  readers do not. A repeatable per-part flag is now a capability extension.
- **No attachment convergence** — recorded, see above.
- **Empty bodies still permitted.** `work/finding-nonempty-message-bodies/`
  remains open and untouched. Note for whoever takes it: the question is now
  per-part, and an empty *leaf* inside a non-empty manifest may deserve a
  different answer than an empty message.

## Verification

- 365 passed, 0 failed, including the isolated standalone-distribution run.
- Deterministic rebuild; artifact, source and protocol-document hashes match
  `DISTRIBUTION.json`. `bin/baton --version` reports tool 4.0.0, protocol 8.
- `git diff --check` clean.
- The README's documented flow runs end to end **against the built
  executable**: `init`, `send`, reviewer `wait`, `reply`, implementer `wait`,
  inline `send-notice`, `see`, `doctor ok: true`. Documentation that does not
  execute is a defect I have shipped before in this project.
- A nested `multipart/mixed[ multipart/alternative[text, html], image/png ]`
  message was published, claimed and materialized part-by-part on a live
  instance, not only in fixtures.
- The pre-release schema refusal was verified against a real instance built
  from commit `b7a7a6f`, not asserted from reading the code.

## Sequencing note

Both pinned changes are now in. **The fresh authority may be initialized.**
There is no third blocker: `work/finding-attachment-part-convergence/` is
explicitly a later protocol bump and must NOT hold up this cutover.

`work/finding-human-console/` is next and is what restores Slawomir to the
channel.
