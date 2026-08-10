# Stage 2.2 plan review — one ruling and plan corrections before schema work

## Accepted direction

Use **N ordinary message rows** for a multi-recipient directed publication.
Every recipient therefore keeps the existing message/claim/disposition,
damage, quarantine, recovery, retention and GC lifecycle by construction.
Sharing immutable inline bytes through existing `contents` deduplication is
safe; each delivery retains its own part-tree rows and external-pin metadata.

The proposed CLI surface is also accepted:

- repeated `send --to exact.participant` for directed multi-recipient work;
- bare `send-notice` for global broadcast;
- `send-notice --scope 'baton.*'` for a scoped notice;
- reject duplicate exact recipients, wildcard `--to`, malformed selectors and
  empty selector expansions before any authority write.

Documentation examples must quote the wildcard so a shell cannot expand it.
The TUI derives selectable scopes from complete dotted participant prefixes;
there is no free-form typo path.

Pure selector grammar/expansion plus tests may start while the ruling below is
pending. Do not write the schema or publication path until the remaining
points are incorporated into the plan.

## R1 — shape A still needs immutable publication metadata

“N ordinary messages” is the lifecycle shape, not permission to derive the
original audience from whatever message rows happen to remain. GC or transient
retention can remove one recipient's terminal delivery before another opens
theirs. Deriving audience from surviving rows would then shrink history,
change the detail header, and invalidate retry/authorization state.

Add an immutable directed-publication record and canonical audience table,
with every ordinary message row linked by `publication_id`. The publication
record holds identity/audience metadata, **not delivery state**; claims and
dispositions remain solely on the ordinary messages. Apply this to
single-recipient directed publications too: later decision obligations and
participant-authorized reread need one publication-time audience model, not a
special private-message path.

Triggers and `doctor` must prove:

- publication and audience membership are immutable and non-empty;
- exactly one ordinary delivery exists per audience member;
- every delivery linked to a publication has the same sender, subject, kind,
  thread, retention, outcome, container type and manifest identity;
- no extra delivery exists outside the canonical audience;
- deleting/GCing a delivery cannot rewrite or prematurely delete audience
  metadata still required by another delivery or retained retry record.

This is still shape A. It is not shape B: no claimable state moves into a
delivery table and no existing lifecycle is re-derived.

## R2 — retry identity has no operation key in the plan

The finding requires an exact retry to compare audience kind, selector and the
canonical explicit set, and to fail closed if the set changed. Current
`send`/`send_notice` always generate a new ID and are not retry-addressable.
`publication_id` merely linking newly created rows does not let a caller find a
commit after the result was lost.

Specify the effectively-once publication seam before implementation:

- a caller-known idempotency/publication token for directed and notice
  publication, including how CLI and TUI generate, retain and retry it;
- exact retry redelivery after a post-commit/pre-result crash;
- mismatch checks covering content manifest, sender, subject/kind/thread,
  retention/outcome, audience kind, selector and canonical audience;
- retention/GC of the retry record, including when a token may lawfully become
  reusable (prefer never within retained authority history);
- no deterministic content hash as the token, because two intentional
  identical publications must remain possible.

If the project instead intends publication to remain at-least-once, then the
finding's retry promises must be explicitly revised by Slawomir. Do not claim
audience retry identity while no retry can address a prior publication.

**Ruled by Slawomir on 2026-08-10:** publication remains at-least-once for
protocol 10. An ambiguous retry is a new publication carrying an immutable,
sender-supplied `possible_duplicate` warning. No token or automatic
correlation is added in this stage; the earlier retry-identity promise is
withdrawn.

## R3 — config regeneration must preserve live frozen audiences

`regen_instance` currently refuses removing participants named by live
messages/notices. Extend the gate to stored notice and directed-publication
audiences while they remain deliverable/actionable. Otherwise config removal
can freeze a participant into an audience and simultaneously make the
participant undeclared and unable to consume it.

Config additions never join old audiences. Scope membership comes only from
the stored expansion. Spell out expiry/terminal/GC behavior so removing a
participant eventually becomes possible without mutating retained history.

## R4 — wire/API/output shapes need to be explicit

The plan must specify before code:

- single-recipient `Store.send` compatibility and return shape;
- multi-recipient return shape (`publication_id` plus recipient-to-message
  mapping/list) and exact retry redelivery;
- delivery/preview/scan/dump fields that distinguish private, multi, scoped
  and global audience kinds without content delivery or receipts;
- reply/follow-up linkage to one delivery while displaying the immutable
  original audience, with default reply only to the original sender;
- TUI scope derivation for multi-segment addresses and multi-selection
  cancellation/atomicity.

## Contract ruling — global notice audience

Today a participant added after a global notice was published can receive that
old notice. The proposed table would freeze global membership at publication,
the same as a scoped notice.

**Ruled by Slawomir on 2026-08-10: freeze global notices too.** A broadcast is
to the participants who existed when it was sent; config addition should not
grant a new identity access to historic broadcast content. One immutable
mechanism is also easier to audit than a global special case that re-evaluates
live config. Matching author-delivery parity remains unchanged. The
publication-retry ruling is also closed: protocol 10 uses the at-least-once
warning model.

## Required plan additions

Add regressions for publication atomicity and injected rollback; independent
claim/reply/close/recovery/quarantine/damage/GC across recipients; immutable
audience after one delivery is removed; possible-duplicate warning propagation;
regen addition/removal; global/scoped author parity; exact segment
matching; empty/duplicate/unknown/mixed wildcard refusal with zero writes;
read-only scan/TUI previews; and query-to-arm/polling wakeup for every and only
eligible participant.
