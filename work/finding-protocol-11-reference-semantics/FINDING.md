# Protocol 11 reference semantics

Status: **queued for the protocol-11 boundary; external hash-pinned
`--attach` is ruled out, references replace it, and the durable locator design
remains open. Protocol 10 and Baton 1.1.0 remain unchanged.**

## Discovery

Several teams reported a “broken mailbox” after a repository file published
as a protocol-10 external part changed or disappeared. The authority and later
deliveries were healthy, but the immutable publication's external hash pin no
longer verified. `wait` continued to report the damaged FIFO head, an exact
claim failed closed, and `doctor` remained non-OK until a recovery-capable
participant quarantined the delivery.

This is correct enforcement of protocol 10's current external-part contract,
but the incident exposed a semantic mismatch. Operators read `--attach` as
“put these bytes in the message so the message is independent of the source
file.” Baton's protocol-10 spelling instead publishes a hash-pinned reference
to bytes that remain outside the store.

The immediate incident was discussed in messages
`98ff6a761eee9550b9ff094e4cc8a188` and
`a9e071c40a6fa41474a8b452393223dd`. Slawomir's protocol-11 ruling is message
`b715bbdc45db930e3bf255d1210b0eed`.

## Confirmed ruling — 2026-08-11

Slawomir ruled:

> in the next proto (11) we cannot use --attach as it implies something being
> inlined and independent from the outside world. We are using references not
> attachments. Refs can float/change/disappear

Therefore protocol 11 must not retain the current external hash-pinned
`--attach` contract or present it under attachment terminology. A reference is
navigational metadata, not message content: its target may change, move, or
disappear without changing the published message, damaging the delivery,
blocking readiness, or making authority health non-OK.

When exact bytes must travel independently of the outside world, those bytes
must be copied into the store as an inline content leaf. Whether protocol 11
retains `attachment` as a content-disposition name for such stored bytes is a
separate naming decision; the ruled removal concerns the current CLI
`--attach ROOT:PATH` external-part behavior.

This is a protocol-11 boundary, not permission to alter the frozen
protocol-10 authority or the 1.1.0 release. Protocol 10 continues to verify its
existing pins, fail closed on changed external bytes, allow bare claim to skip
damaged deliveries, and require audited quarantine for terminal recovery.

## Cross-team cleanup transfer — 2026-08-11

Later, `workflows.reviewer` transferred a second concrete case in message
`3f243fd443dcb9af8deba579a3af4f50`: repository policy makes completed finding
folders mandatory-ephemeral branch work, so a hash-pinned external part inside
one is expected to disappear during normal closure cleanup. Workflows will use
references-only for in-repository handoffs and asked Baton to assess vanished
parts on already-resolved messages.

**Confirmed protocol-10 behavior from current code and regressions:**

- a closed/answered message is no longer in the pending queue, so a later
  vanished external part does not block readiness or claim selection and does
  not appear in `scan`'s pending-only `damaged` list;
- `doctor` deliberately revalidates external parts on every retained message,
  including terminal ones, so the vanished target makes the whole authority
  non-OK until explicitly acknowledged;
- `open_received`, `open_sent`, and whole-message save revalidate the pin and
  fail closed, so the durable message can no longer be reread/exported as a
  complete publication even though it was previously delivered;
- a recovery-capable participant may quarantine the already-terminal message;
  this preserves its existing terminal state and adds an immutable audit row,
  after which `doctor` reports a warning and returns healthy;
- quarantine retains the external part and original pin. Config regeneration
  considers every retained external part, without excluding quarantined or
  terminal messages, so its configured root still cannot be removed or
  remapped while that history remains; and
- single-part materialization already refuses external leaves because Baton
  stored no bytes to project. This is independent of whether the target still
  exists.

The terminal case proves this is not only pending-queue recovery. A normal
repository cleanup can make historically resolved durable work require a
privileged ceremony and retain an otherwise-obsolete root binding forever.
That is incompatible with the confirmed protocol-11 reference promise.

## Observed current contracts

- `--attach ROOT:PATH` resolves and reads a configured filesystem root at
  publication, records the external path/size/hash, and revalidates it before
  delivery.
- `--references FILE` publishes a
  `text/vnd.baton.references; charset=utf-8` leaf containing `ROOT:PATH`
  addresses. It reads no target, pins no bytes, and requires no target to
  exist.
- `--body` and general inline parts copy their bytes into the store and remain
  deliverable without their source files.

Protocol 11 should make these promises visually and mechanically distinct:
stored content is content; a reference is only an address.

## Proposed Git-addressed direction

Slawomir raised Git-only resources with a commit identifier as a possible
reference model. The strongest initial design candidate is an explicit Git
locator containing at least a configured repository/root identity, full commit
object id, and repository-relative POSIX path. It offers a stable historical
address without making the referenced bytes part of the Baton message.

That remains **Proposed**, not confirmed. A commit object may be unavailable
on another machine or later garbage-collected; a private repository still
requires authorization; submodules and renamed roots complicate resolution;
and Git-only references cannot name generated artifacts or evidence that is
not committed. Failed resolution must remain a reference-viewing problem, not
message or authority damage.

A likely model needs two promises with different types rather than one
ambiguous syntax:

1. an immutable Git locator such as `(repository, commit_oid, path)`; and
2. an explicitly floating advisory locator such as `(root, path)`.

Neither promises that Baton stored or delivered the target bytes. If a sender
needs that promise, the sender publishes the bytes as stored content.

## Open decisions

1. Are protocol-11 references Git-only, or does the content model support
   typed locator schemes with Git as the first one?
2. Are immutable and floating locators distinct leaf media types, distinct
   manifest fields, or two variants inside one typed references document?
3. Does Baton ever resolve a reference, or does it only transport the locator
   for clients to resolve under their own repository authorization?
4. How are repository identity, commit algorithm, path, submodules, and an
   unavailable object represented without falling back to host-local paths?
5. Does protocol 11 remove external-part schema columns entirely, and how are
   retained protocol-10 authorities retired during the fresh-authority
   cutover?
6. Which CLI term authors stored attachment-disposition content without
   reviving the false promise attached to today's `--attach` spelling?

## Acceptance boundary

- Changing, deleting, or making a referenced target unreadable never changes
  message state, claimability, readiness, or `doctor` authority health.
- Claim and reread do not touch the referenced filesystem or repository.
- Resolving a message before its reference target changes does not create a
  later health transition: deleting an ephemeral finding folder after closure
  requires no quarantine, does not add a warning, and does not prevent a root
  remap/removal.
- Stored content remains byte-exact and deliverable with its authoring source
  absent.
- The CLI and documentation never call an external reference an attachment or
  imply that Baton copied its target.
- Any immutable Git locator names repository identity, full commit object id,
  and path unambiguously; resolution failure is explicit and non-damaging.
- Protocol-10 external publications and their quarantine audit remain
  historically intelligible after the protocol-11 cutover.
- Reread and whole-message save preserve the published locator even when it
  cannot be resolved; inability to fetch the target is reported separately
  from reading or exporting the Baton message.
