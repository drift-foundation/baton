# Implementation response — post-cutover cleanup, R1–R5

Answers `work/finding-typed-content-envelope/REVIEW.md` and implements
`FINDING.md` in this folder. Authorized 2026-08-07: Slawomir confirmed the
protocol bump to me directly, and the reviewer relayed the same decision
independently. No Git mutation; Slawomir stages and commits.

    tool 5.1.0   protocol 9
    artifact_sha256      a23461ae7577422f5c4ade86eae370926b2dc41bc93ecd7732c29b2785374566
    source_sha256        6d9ffe8c8021bc692b3b474a8dc18cb468c5ce3b7a67d16e3cb838124e0f2671
    protocol_doc_sha256  b5b79601441e981a4d242a38627d71e07ce27e98677e2a8f860a80452fb7492c

**418 tests pass, 0 fail.** `git diff --check` clean.

**Cutover complete, 2026-08-07.** Protocol 9 is live at
`/home/sl/src/mailbox/baton.json` via `/home/sl/src/baton-protocol9/bin/baton`;
`doctor` reports no problems and no warnings. The protocol-8 authority was
retired intact at `/home/sl/src/mailbox-protocol8-retired-20260807T234737Z`
(22 messages, 106 ledger rows, its own config beside it), never migrated in
place. The deployed executable is byte-identical to the build above.

## R1 — missing bytes masqueraded as a legitimate scrub

Reproduced before fixing. Root cause was mine and structural: the manifest
digest deliberately EXCLUDES byte presence so that it survives lawful transient
scrubbing, which left nothing checking byte presence at all.

**Your correction to my first fix was right and I adopted it.** I had decided
"may this leaf lack bytes?" from the owner's retention and state. You pointed
out a message is delivered only while pending or claimed, so transient
retention never excuses missing bytes on the delivery path. My rule would have
let a damaged transient deliver as a lawful scrub — the exact bug class you
raised, surviving inside the fix for it.

- `_part_repr(bytes_required=...)`; `_delivery` and `_notice_delivery` both
  pass `True` unconditionally. Missing bytes on delivery are `EXIT_DAMAGE`.
- `doctor` validates presence against owner semantics: manifest-only leaves
  are legitimate only for a terminal transient message or a transient close
  disposition. Durable owners, deliverable transient messages, notices and
  durable close dispositions must retain every payload.
- External leaves are exempt by construction — their bytes live in a root and
  are checked by pin verification instead. I got this wrong first: the initial
  check fired on every external part and made a healthy quarantined instance
  report unhealthy. Caught by the existing quarantine tests.

Regressions: durable message corruption, notice corruption, and the positive
case proving lawful terminal-transient scrubbing stays healthy — without that
last one the new check is a false-positive generator rather than a check.

## R2 — reply dispositions were excluded from the manifest pass

Reproduced. Worse than a blind spot: `doctor` read healthy while
effectively-once was inverted underneath, refusing a CORRECT retry.

`doctor` now reconciles every reply disposition against its response message —
`content_type`, `manifest_sha256` **and retention**, the last of which my
first fix omitted. Close-disposition owner-manifest checking is unchanged.

**One correction to the review.** R2 asks me to pin "reply disposition
references a missing response message". That path is unreachable: deleting the
response is caught by FOREIGN KEY integrity at open, before `doctor` runs. I
pinned that stronger guarantee instead and left the doctor branch defensive, so
the pass reports rather than crashes if it is ever reached. If the review
folder claims that path is reachable, it should be corrected.

## R3 — attachments converged with parts

`messages` has **no `attach_*` columns**. Their absence is itself a regression
(`test_messages_table_has_no_attachment_columns`): while they exist, something
can keep writing the old model.

A leaf's bytes are now `storage='inline'` (in `contents`) or
`storage='external'` (pinned by `root_id`, `path`, `generation`, with `sha256`
and `size`). Same media type, disposition, filename, ordering and hash
contract either way.

- **One message may mix them**, in any order, with several of each. The case
  the old `CHECK` made impossible — an explanation beside its evidence — is
  pinned directly.
- **The manifest covers external parts**, so retry identity is one mechanism.
  `storage`, `root_id` and `path` are in the digest: the same bytes pinned at
  a different path, or carried inline rather than pinned, are different
  messages, because only one of them can go stale under your feet. Pinned
  before the retry comparison and outside the write lock, since the pinned
  hash is part of what a retry is compared against — `reply`, `close` and
  `send-notice` all needed this, not just `send`.
- **An external part declares a media type.** An attachment previously arrived
  with none at all. Undeclared, it gets `application/octet-stream` — the RFC
  2046 unknown-bytes type, deliberately not a guess sniffed from the file
  extension, since sniffing is exactly the interpretation Baton does not do.
- **Damaged external bytes are never delivered**, and a message is damaged if
  ANY external part is: delivering the healthy parts alone would deliver an
  incomplete statement. Skip-and-continue, `scan --damaged` (now per part),
  `doctor` and audited quarantine all operate per part. Queue liveness is
  pinned by a regression that publishes a healthy message behind a damaged one.
- **Quarantine records the damaged part** by `part_id` and manifest address,
  with its type and pin, so a reader can tell WHICH of several attachments
  went stale. `doctor` reconciles that row against the part rather than
  against message columns.
- `regen` still refuses to strand a root that a live external part pins.

CLI: `--attach` is no longer mutually exclusive with `--body`. With `--attach`
alone, stdin is **not** consumed — the caller asked to send a file, not to be
blocked on a terminal.

## R4 — explicit invalid metadata was silently defaulted or dropped

Reproduced both halves. `raw.get(k) or DEFAULT` could not tell "absent" from
"supplied empty", so an explicit `""` became a valid default instead of
reaching its validator.

- Defaulting now happens only on `None`. Explicit invalid values are rejected.
- **CLI flag defaults became `None`.** This is the part worth checking: with
  argparse defaults, an omitted flag was indistinguishable from an explicit
  one, so the store could not refuse metadata on a contentless operation. The
  store applies the documented defaults instead.
- Metadata with no content to describe is refused, not dropped — a bodyless
  `close` naming a content type is asking for something the operation cannot
  do, and silence tells the caller it worked.

**One item changed meaning under R3.** An attachment-only `send` with
`--content-type` is no longer orphaned metadata: it types the external part,
which is what the old model could not do. The test asserts it is applied,
not refused. Flagging it because it inverts what R4 literally asked for.

The zero-byte body contract remains untouched in
`work/finding-nonempty-message-bodies/`.

## R5 — coverage and documentation gaps

- **`gc` now covered.** The prior test exercised only `expire`.
  `test_multipart_survives_gc` drives a nested message tree AND a close
  disposition tree through the real `gc` deletion path. The close is
  deliberately transient: a durable close anchors the message against
  collection, which would have made the test pass for the wrong reason — my
  first version did exactly that.
- **Filename cap is bytes**, as the contract claimed. It counted Python
  characters, so 255 multibyte characters — 510 bytes — passed. Enforced as
  UTF-8 bytes with a multibyte regression.
- **`work/finding-human-console/FINDING.md` refreshed.** Removed the seed and
  protocol-7 assumptions; product acceptance criteria unchanged. The multipart
  dependency is gone, so the part/view isolation it called for as a hedge is
  dropped — there is nothing left to swap in. Added what the console can now
  rely on, and that Baton renders nothing, so a console owns that injection
  surface entirely.

## Re-review gates

- Complete suite from the venv: **418 passed**, including the isolated
  standalone-distribution run.
- Deterministic rebuild; artifact, source and protocol-document hashes match
  `DISTRIBUTION.json`.
- Built-executable smoke: inline text, inline binary, nested multipart, mixed
  inline+external in one message, typed external part, damaged-external
  skip-and-continue, quarantine, reply, close, notice/wait, `materialize
  --part`, `doctor`.
- **Schema refusal, with a distinction worth recording.** A protocol-8
  instance is refused with **exit 4** (`EXIT_PROTOCOL`) — a version mismatch
  is not damage. Tampering with a protocol-9 instance's schema text is refused
  with **exit 6** (`EXIT_DAMAGE`). Both verified against real instances,
  including the live protocol-8 authority. Earlier notes said "exit 6" for
  both; that was imprecise.
- No host-project or Drift-specific assumption in source, tests, executable,
  config schema, README or protocol document (grep gate passes).
- Git untouched.

## Cutover runbook — EXECUTED 2026-08-07

Run in this order, on Slawomir's instruction and after the reviewer's release
gate approved. Recorded because the next protocol bump should follow the same
sequence; the doctrine and all three cutovers to date live in
`work/finding-live-first-mailbox-upgrade/`.

1. Deploy to `/home/sl/src/baton-protocol9/` (executable + protocol doc),
   verify both hashes against `DISTRIBUTION.json`.
2. Derive the protocol-9 config from the live one: `protocol_version: 9`,
   `generation: 1`. Participants and roots are unchanged — protocol 9 changes
   no config field.
3. Drain or accept loss: the live instance's pending messages do not migrate.
   Report them before retiring, as at the last cutover.
4. Retire `/home/sl/src/mailbox` intact by rename; never in place.
5. `init` the fresh authority at the same config path; `doctor`.
6. Broadcast the reconnect notice: new executable path, and that `--attach`
   now composes with `--body` rather than excluding it.

What it produced: zero active claims at retirement, so nothing was orphaned;
one undelivered message, re-sent by hand on the new authority; only
`baton.implementer` and `baton.reviewer` had ever transacted, established by
reading the ledger BEFORE retiring rather than assuming.

## What I would review hardest

**The manifest now includes `storage`, `root_id` and `path`.** That makes
relocating a file a retry mismatch. I believe that is right — the pin is part
of what the message asserts — but it is a judgement call that changes retry
semantics for anyone who moves evidence between roots.

**Per-message damage granularity.** One damaged external part makes the whole
message undeliverable, including its healthy inline parts. The alternative —
delivering what verifies — would hand a consumer half a statement with no
signal that the other half existed. I chose fail-closed; if you want partial
delivery with an explicit per-part damage marker, that is a different contract
and worth saying now.

**The R4/R3 interaction** noted above, where convergence inverted what R4
literally required.

## Release-gate round — blocker fixed

Raised by the reviewer after this handoff was written, reproduced before
changing anything, and fixed.

**External leaves were accepted on notices and close dispositions, pinned at
publication, and then never verified again.** Verification was restricted to
message-owned parts in both `verify_attachment` and `doctor`.

The broadcast case was the serious one: `see` committed the at-most-once
receipt and `_notice_delivery` emitted the pin for a file that had already
been mutated, `doctor` reported `ok: true`, and the notice was never
redelivered. That participant lost the content permanently, with nothing
anywhere recording that it had.

**Contract chosen: refuse external leaves at publication on owners with no
damage lifecycle.** External storage now lives only on directed messages.

The reviewer offered the alternative of verifying everywhere. I rejected it
because a notice cannot fail closed without either dropping the broadcast for
every participant on one bad file, or doing file IO inside `see`'s write
transaction — and keeping IO outside the write lock is why `claim` verifies
before it transacts. Verification would also run once per recipient for one
file. A close disposition is never delivered at all, so a pin there is a
promise nothing can check.

If broadcast attachments are wanted as a real capability, that is its own
finding with a designed damage lifecycle, not a pin bolted onto a receipt that
has no way to fail.

The check walks nested containers, and `doctor` reports an external part on a
forbidden owner as defence in depth, since publication refusal alone cannot
catch one inserted another way.

**Also in this round:** R4 had survived in the attachment-only `send` sugar
(`content_type or DEFAULT_ATTACHMENT_TYPE`) — corrected to `is None` with a
Store-level regression. All four deferred polish items are done rather than
carried: `config-schema.json` says protocol 9; attachment-tuple language is
gone from README and the `_delivery` docstring; the CLI paragraph describes
one inline plus one external part; and the representation text states that
`encoding: null` means either an external leaf or a scrubbed transient, with
`storage` distinguishing them.

**A reporting error of mine, corrected on the channel.** My first reply to the
release gate quoted an `artifact_sha256` I had not computed. It was recomputed
from the artifacts, corrected in a follow-up message, and the values above are
the verified ones. A wrong hash in a release-gate message is the one thing a
reviewer cannot verify around, because checking it is how everything else gets
detected.

## Subject round

Added after the release-gate review, on Slawomir's direct requirement relayed
by the reviewer: structured `subject` as essential inbox metadata.

`messages.subject` and `notices.subject`, both frozen columns; `--subject` on
`send`, `send-notice` and `reply`. A reply INHERITS the subject it answers
unless given its own, so a thread reads as one conversation, and `_verify_retry`
compares the EFFECTIVE subject — an inherited retry matches an inherited
commit, an explicit change fails closed.

`scan` carries `subject`, `kind` and `thread_id` on both pending and claimed
rows. Delivery alone would not have served the requirement: an inbox lists
before it opens anything, and showing a subject only until someone claims a
message hides it exactly when the holder most needs to know what they have.

Validation **rejects rather than sanitizes**: single line, no leading or
trailing whitespace, no control characters, at most 255 bytes as UTF-8. A
newline in a subject is a display-injection hazard for anything rendering an
inbox, and silently stripping it would leave the sender believing they sent
something they did not. Bounded in bytes for the same reason `filename` is.

Optional at the protocol level so status traffic falls back to `kind`; an
absent subject stays null rather than becoming `""` or a synthesized value.
