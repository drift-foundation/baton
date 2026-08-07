# The seed is not a credential boundary; the participant address is the identity

Folder: `work/finding-seed-credential-boundary/`
Status: **confirmed; contract chosen by Slawomir; implementation not started.**
Raised: 2026-08-07, after `web.implementer` authenticated as
`baton.implementer` using a seed read out of `dump`.

Disclosure, participant binding, and issuance are recorded as one finding
because they are one credential boundary and have to be threat-modelled
together. Fixing any one alone leaves the others reachable.

## Confirmed evidence

**1. `dump` discloses raw seeds and requires no identity.**
Its dispatch is `_print_result(dump(ns.config))` — no `--participant`,
`--actor` or `--seed`. Seeds appear in four places in its output:
`claims.seed`, `notices.author_seed`, `notice_seen.seed`,
`transitions_tail.seed`. On the live instance it emitted all six distinct
participant seeds. `scan`, `inspect` and `doctor` do not leak seeds.

**2. `reply` and `close` parse `--participant` and then ignore it.**
The CLI passes only `actor=ns.actor, seed=ns.seed` into `store.reply` and
`store.close_claim`. `_load_active_claim` authorizes on exactly two fields:

    if row["actor"] != actor or row["seed"] != seed:
        raise BatonError(f"claim {claim_id!r} is owned by actor ...")

`claims` stores no participant. So any holder of a matching actor+seed can
dispose of another participant's claim, and the resulting ledger looks
correct.

**3. There is no seed issuance contract.**
A new participant on a fresh instance has no documented way to learn its seed.
The instruction "choose one stable, private 32-hex seed" admits two readings —
mint one, or find the one you are supposed to use — and one of them is
catastrophic.

**How it was actually exercised.** `web.implementer` came up on the fresh
protocol-7 instance with no seed, ran `dump`, saw claims held by actor `k`,
and adopted the seed on those rows. They were `baton.implementer`'s. This was
not a coincidental collision; it was credential adoption from a diagnostic,
self-reported unprompted. `dq.implementer` independently verified the
disclosure and declined to collect anyone else's value, noting that confirming
a leak does not require collecting the credentials.

**A near-miss worth recording.** `baton.implementer` later found that claim,
matched the seed, concluded it was an orphan of its own, and came close to
closing another team's in-flight research handoff. Only the transition ledger
distinguished them. A seed match is not proof of ownership, and the tooling
offered no cheaper way to find that out.

## The trust model, as chosen

**The participant address in `team.actor` form — for example
`baton.implementer` — is the complete logical identity.** The separate process
actor and private 32-hex seed add ceremony without establishing a credible
security boundary.

**Mailbox filesystem access is the explicit trust boundary.** Anyone who can
read the instance directory can read the database directly; the seed never
protected against that party, and pretending otherwise misled everyone who
handled it. This is cooperative coordination between trusted agents, not
application-level authentication.

This deployment has exactly one consumer role per participant and no
demonstrated duplicate-role requirement.

## Target model

- One consumer identity per participant address.
- Claims are owned by the **recipient participant**; disposition requires the
  caller to be that participant.
- Notice authorship and seen receipts are keyed by participant.
- Recovery of abandoned work remains **capability-authorized**, unchanged.
- Multiple concurrent consumers, if ever required, receive **distinct
  participant addresses** rather than sharing one identity.
- No seed issuance system is built. There is no seed.

### Consequences that are breaking, stated plainly

**Notice receipts collapse to `(notice_id, participant)`.** Today the primary
key is `(notice_id, participant, actor)` and two actors of one participant
each receive a notice. With one identity per participant there is no
per-actor fanout because actors no longer exist.

Slawomir's option-A ruling on self-authored notices is **re-affirmed
knowingly** under the new key: a publishing participant receives its own
notice once, if unseen. The original reasoning cited the per-actor key; the
decision survives the key changing.

**The whole actor identity layer leaves the public contract**, not just one
claim column: `identity: agent|singleton`, `singleton_actor`, the `--actor`
and `--seed` CLI flags, their validation, the config schema, the example
config, and the documentation. This is a protocol-breaking config and CLI
change.

**The ledger is not migrated.** The protocol-7 authority is retired intact as
historical evidence and a replacement authority is initialized fresh under the
new schema. So the new schema carries **no legacy nullable actor/seed
columns**, and append-only history stays untouched inside the retired
instance.

## Protocol 7 containment versus the target model

These are distinct and must not be conflated.

**Transitional containment (protocol 7, if wanted):** bind the caller's
participant to the claimed message's recipient in `reply`/`close`, including
retries. `_load_active_claim` already selects `m.to_participant`, so this
needs no schema change — the participant is derivable from the immutable
message. Optionally redact seeds from `dump`. This narrows accidental
cross-disposition during transition. It is containment, not the model.

**The target model** arrives with a protocol bump, and should not invest in a
permanent seed issuance system on the way.

## Release shape

**Live-first.** Build and review against the still-live authority, then retire
it and start a fresh authority at the new protocol. **Do not attempt in-place
migration** — see `work/finding-live-first-mailbox-upgrade/`, where an
in-place cutover cost this deployment more than ten hours of coordination.

The human console follows this identity correction, so it is built against the
simplified interface rather than against a contract known to be changing.

## Acceptance tests

1. A participant cannot dispose of a claim whose message names a different
   recipient — first disposition and retry both refused.
2. A known foreign claim id, presented by a participant that is not the
   recipient, is refused; the refusal is not a lookup failure.
3. `dump` output contains no bearer credential; asserted by scanning its
   output for any field that authorizes an operation.
4. Notice receipts dedupe per participant: a second consumption by the same
   participant returns nothing.
5. A publishing participant receives its own unseen notice exactly once.
6. Recovery of an abandoned claim still requires the `recovery` capability.
7. A config carrying `identity`, `singleton_actor`, actor or seed fields is
   rejected by the new protocol rather than silently ignored.
8. `doctor` reports no identity-shaped inconsistency on a fresh instance.

## Open risks

- **Concurrency.** A seed never enforced one live consumer: two waits sharing
  participant, actor and seed still raced, and one claimed into a process
  whose output nobody read. The new contract remains **exactly one tracked
  consumer path per participant**, enforced by policy. Do not invent
  credential or lease machinery unless implementation evidence proves policy
  insufficient.
- **Audit legibility.** With actor gone, the ledger attributes actions to a
  participant only. That is the intent, but any "which process did this"
  question becomes unanswerable from the store.
- **Every deployment's config becomes invalid** at the bump. That is expected
  for a protocol-breaking change and is why the release is fresh-authority
  rather than migration, but it must be announced, not discovered.
- **`scan` should show the owning participant on every claim.** The near-miss
  above required transition-ledger forensics to answer "whose claim is this",
  which routine inventory should make unnecessary.

## Not designed here, deliberately

No credential machinery, no issuance system, no lease protocol, no rotation
policy. The chosen model removes the need for all of them. Adding any of it
back requires evidence that participant-address identity is insufficient.
