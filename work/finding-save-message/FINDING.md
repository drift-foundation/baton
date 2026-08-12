# Save any message body

Status: **required for 1.1; Slawomir approved the detailed whole-message save
contract on 2026-08-11. First implementation review requested corrections on
2026-08-11; prerequisite single-part boundary repair remains signed off.**

Humans need a direct way to save the complete content of any claimed message,
including large inline text bodies that do not fit on one screen. `materialize`
is currently limited to materializable external content and is not a general
message export operation.

The feature must preserve the ordered typed-part envelope and support saving a
single message to an explicitly chosen path without changing mailbox state
beyond the existing claim/read semantics. Unsafe filenames and overwrites need
an explicit policy.

## Confirmed clarification — 2026-08-11

The opening premise above is **superseded**. `materialize` already projects one
INLINE leaf and deliberately refuses an EXTERNAL leaf because that leaf is
already a hash-pinned file. The missing feature is a WHOLE-MESSAGE save to a
chosen output path, not inline-part support.

Confirmed boundaries for that future operation:

- transient retention remains protected and continues to refuse projection;
- external leaves remain `root_id`, `path`, and digest references and are not
  copied into an unpinned duplicate;
- the existing no-clobber/idempotent projection publication policy is reused;
- the ordered typed-part envelope must be preserved.

A causally related TUI boundary repair was approved separately: `m` must save a
selected inline part whenever that content is already fully viewable — answered
or closed inbound messages, sent messages, and seen notices — while an
unclaimed inbound-pending message remains refused. The first implementation's
driver affordance still blocked those no-claim rows; that defect and its
evidence are preserved in `review-2026-08-11T13-23-29Z.md`.

## Re-review — 2026-08-11

The driver-affordance defect above is **superseded as current implementation
state**: the correction now passes focused, broad, and independent real-key
verification, including Sent and unseen-notice edges. Functional review is
approved. The required implementer-owned `PROGRESS.md` was then supplied and
the prerequisite repair received final sign-off; see
`review-2026-08-11T13-40-32Z.md` and
`review-2026-08-11T13-43-06Z.md`.

## 1.1 inclusion ruling — 2026-08-11

The earlier first-stretch/cut option is superseded. Slawomir answered the
whole-message-save readiness item with “this needs to go in.” Whole-message
save to a chosen output path is required before the 1.1 candidate soak. The
design/review gate is not waived: ordered typed parts, external references,
transient refusal, safe paths, and no-clobber/idempotent publication must be
pinned before implementation.

## Whole-message representation and UI proposal — 2026-08-11

Status of this section: **proposed by `baton.reviewer`; awaiting Slawomir's
explicit ruling before implementation.** The required feature is confirmed,
but its representation and interaction are product decisions and are not
inferred from the word “save.”

### Revalidated source boundary

**Observed:** `_content_repr()` already produces the lossless ordered content
shape used by delivery: container media type and manifest digest; nested parts
in manifest order; leaf address, media type, disposition, advisory name, size,
digest and storage; UTF-8 text as `text`; all other inline bytes as `base64`;
and external leaves as `attachment {root_id, path, generation}` with their
size/digest on the leaf and no copied bytes.

**Observed:** `_publish_bytes_at()` already supplies the required publication
policy: scratch write, fsync, no-clobber link, directory fsync, exact existing
bytes accepted as resume, and mismatching/symlink/non-regular destinations
refused. `_open_dir_no_follow()` rejects relative/noncanonical paths and walks
every parent component without following symlinks.

**Confirmed:** `authorize_read()` is the read boundary: message sender or
frozen audience; notice author or frozen-audience recipient who already has a
seen receipt. It does not create claims, receipts, transitions, or audit rows.
Whole-message save must reuse that authorization and must not make an unseen
notice or unopened pending message a second delivery path in the TUI.

### Recommended version-1 file

Save one deterministic UTF-8 JSON file. The suggested suffix is
`.baton.json`, but a caller's explicit output filename is not rewritten. Its
top level is:

```json
{
  "format": "baton.whole-message",
  "version": 1,
  "message": {}
}
```

or, for a notice, the same `format`/`version` with a `notice` member. Exactly
one of `message` and `notice` is present.

The message member contains the immutable delivery envelope fields: `id`,
`from_participant`, `to_participant`, `kind`, `subject`, `thread_id`,
`retention`, `outcome`, `created_ts`, `responds_to`, frozen `audience`,
`possible_duplicate`, and `content`. The notice member contains `id`,
`from_participant`, `kind`, `subject`, `created_ts`, `ttl_seconds`,
`audience_kind`, `selector`, `possible_duplicate`, and `content`.

Mutable reader/process state is deliberately absent: no claim, seen receipt,
message state, completion time, saving participant, save timestamp, or output
path. Saving the same immutable message before and after a lifecycle change
therefore produces the same bytes and can resume at the same chosen path.

`content` is the existing `_content_repr()` shape without translation. Its
part arrays preserve order and nesting. Text/base64 preserves inline bytes;
external leaves preserve `root_id`, `path`, binding generation, size and
digest and copy no external bytes. Subject-only/contentless messages save with
`content: null` rather than being refused as “nothing to materialize.” JSON is
serialized deterministically with sorted object keys, two-space indentation,
UTF-8, and one final newline.

Before serialization, every external leaf is revalidated against its accepted
root binding, size, and digest. A damaged pin fails closed; the save must not
publish a reference while presenting the message as an intact export.

### Recommended core and CLI surface

- Add a read-only store operation taking owner id, participant, and exact
  output path. It resolves message/notice indistinguishably from the existing
  authorized materialize path, enforces transient refusal before opening the
  destination, builds the immutable envelope above, revalidates external pins,
  and publishes one file through `_publish_bytes_at()`.
- Add `baton save OWNER_ID --participant WHO --output ABSOLUTE_PATH`.
  `--output` is required, canonical, absolute, names the file itself, and has
  an already-existing parent. The command never creates parent directories,
  silently appends a suffix, overwrites, or resolves a relative path against
  the launch directory.
- Return the chosen path. An exact existing file is the same successful result
  as a new publication, matching current materialize behavior. The operation
  remains read-only with respect to the authority.
- Keep `materialize` unchanged as the one-leaf, generated-name operation.

### Recommended TUI interaction

- Bind currently-unused uppercase `M` to **save whole message**; lowercase `m`
  remains **materialize selected part**. Help and mode legends name the
  difference.
- `M` captures the selected row by `(row_type, id)` before opening a one-line
  path editor. Polling, filtering, view switching, or row reordering can never
  retarget the save through a numeric cursor.
- Seed the editor with
  `<projection_dir>/<message|notice>-<created>-<id>.baton.json` when a
  projection directory is configured; otherwise start empty. The human may
  replace it with any canonical absolute file path. Enter explicitly accepts
  that exact path; Esc cancels; a path refusal keeps the editor and target
  intact for correction. No second confirmation is needed because publication
  cannot clobber an existing different file.
- The row eligibility matches the already-ruled readable-content boundary:
  active claims, answered/closed inbound, Sent, authored notices, and seen
  notices are eligible; unclaimed inbound-pending and unseen received notices
  are refused with the existing Enter guidance. Core authorization and
  transient refusal remain authoritative at Enter time.

### Acceptance boundary for this design

Add new tests rather than changing existing ones unless Slawomir gives
case-specific authorization. Cover:

1. exact deterministic JSON for single text, binary, multipart/nested, mixed
   disposition/name, contentless, message, and notice envelopes;
2. external references include root/path/generation/size/digest, copy no
   external bytes, and fail before publication when the binding or pin is
   stale;
3. transient pending, claimed, answered, and scrubbed messages all refuse with
   no destination/scratch artifact; notices retain their current TTL model;
4. sender/audience/seen-notice authorization, unknown/non-party
   indistinguishability, and full authority `dump()` equality;
5. canonical absolute path, missing parent, symlink ancestor/final target,
   directory/FIFO target, mismatching existing file, exact resume, and a
   publication race;
6. CLI output and isolated packaged CLI execution;
7. TUI key/help/path editing, default suggestion, empty/relative refusal,
   Esc, retry after path error, fixed target across refresh/filter/reorder,
   every eligible row shape, unopened/unseen/transient negatives, and a real
   candidate-zipapp PTY path;
8. large inline text and binary bodies without truncation or byte drift.

### Open ruling

Approve or replace the recommended v1 contract: a single deterministic
`.baton.json` envelope, `baton save --output`, and TUI `M` with an explicit
absolute-path editor. Implementation remains blocked until this paragraph is
answered and the result is appended chronologically.

## Whole-message design ruling — 2026-08-11

Slawomir replied **“Approved”** to the complete “Whole-message representation
and UI proposal” above. That proposal is no longer merely recommended: it is
the confirmed Baton 1.1 v1 contract and authorizes implementation within its
named core, CLI, TUI, path-safety, retention, authorization, representation,
external-pin, deterministic-output, and regression boundaries.

No part of the approval relaxes the prerequisite rules: transient messages
still refuse; unseen received notices and unopened inbound-pending rows are
not made readable through the TUI; external bytes are never copied; output is
one deterministic file at the exact canonical absolute path; and frozen 1.0
artifacts/manifests and the live authority/config remain untouched.

## Implementation-start revalidation — 2026-08-11

Immediately before delegation, the approved contract was rechecked against
current next-generation source. `_content_repr()` remains the single ordered,
typed delivery representation; `authorize_read()` remains the
sender/frozen-audience and seen-notice boundary; `_publish_bytes_at()` remains
the no-clobber/exact-resume publication primitive; and the existing
`materialize_authorized_part()` remains a one-inline-leaf operation. No
whole-message `save` command or TUI `M` flow has appeared since the ruling, so
the approved patch boundary is still current and is not superseded.

Implementation is now the sole serial item delegated to `baton.implementer`.
The implementer owns core, CLI, TUI, new tests, and `PROGRESS.md`; the reviewer
retains FINDING/PLAN/review-journal ownership. Frozen 1.0 binaries/manifests,
the live authority/config, deployment, activation, and Git state remain out of
scope.

## Whole-message implementation review — 2026-08-11

The first implementation pass is **changes requested** in
`review-2026-08-11T20-13-44Z.md`. Independent focused and packaged-PTY tests
passed, but boundary probes proved that the TUI strips the exact typed path and
that a double-root `//...` spelling is accepted as canonical. The pass also
translates an empty content container contrary to the ruled no-translation
shape, carries false notice-audience and timestamp rationale, and lacks several
explicit acceptance-matrix regressions.

Two one-member updates to existing exhaustive registry tests remain outside
sign-off pending Slawomir's required case-specific authorization. Whole-message
save remains the sole serial item; bulk archive/restore is not started.

## Representation clarification after correction review — 2026-08-11

Review pass 1 item 3 is **superseded**. It incorrectly requested that an empty
internal content container be exported verbatim. The approved design already
contains the more specific rule: “Subject-only/contentless messages save with
`content: null`.” That specific sentence is the intentional exception to the
general “existing `_content_repr()` shape without translation” rule, which
governs owners with actual content parts.

Baton stores a subject-only message using an empty `multipart/mixed` sentinel,
but version-1 whole-message export represents that contentless case as JSON
`null`, exactly as Slawomir approved. Nested, typed, inline, and external
content with actual parts remains the delivery representation without
translation. The correction pass must restore the narrow contentless
normalization while retaining exact delivery-shape tests for non-empty content.

All other first-review corrections and missing acceptance regressions were
accepted on re-review; see `review-2026-08-11T20-30-57Z.md`. Existing-test
authorization remains separately pending.

## Functional acceptance; policy gate pending — 2026-08-11

K restored the specific contentless `null` exception and retained exact
delivery representation for every owner with actual parts. Independent final
feature verification passed 62 focused and packaged-PTY tests. No further
feature correction is requested; see
`review-2026-08-11T20-42-26Z.md`.

Overall sign-off remains withheld solely because the two technically correct
one-member updates to existing exhaustive registry tests still lack
Slawomir's case-specific authorization. The finding remains the sole serial
item until that human policy gate is resolved.

K's no-change alternatives analysis is recorded in
`review-2026-08-11T20-43-32Z.md`. Removing either entry would weaken a safety
invariant: the save-accept key would cease to be classified as effectful, or
the `M` dispatch gate would split from the shared affordance query. Reviewer
recommendation is therefore to authorize exactly the two one-member edits,
but the recommendation does not replace Slawomir's confirmation.

## Test-addition policy ruling and final source sign-off — 2026-08-11

Slawomir changed repository policy in response message
`c34b344061243c5a8d66af82338b04eb`: **adding tests is always approved**. The
earlier case-specific-authorization gate for additive coverage is superseded.
`AGENTS.md` now makes the boundary explicit: new tests and additive cases or
members in existing exhaustive registries need no separate authorization;
editing or weakening existing assertions or expected behavior still does.

This ruling authorizes the two already-reviewed one-member additions to
`test_the_effectful_events_are_exactly_these` and
`test_nothing_advertised_refuses_for_want_of_state`. Neither weakens or changes
an existing expectation. The sole remaining policy gate is therefore closed,
and whole-message save source is signed off in
`review-2026-08-11T23-26-58Z.md`. Candidate-build/deployed-path exercise
remains part of the release umbrella rather than this source review.
