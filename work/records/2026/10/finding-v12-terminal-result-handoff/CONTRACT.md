# Proposed completion reporter contract

Status: historical unselected proposal. Owner 2026-10-18 prioritizes native v12
coordination over building this v12-to-v11 bridge; see latest FINDING/PLAN.
Not an implemented or deployed capability.

## Registration and identity

Before the selected supervisor launch, durably register a versioned envelope:
v11 authority UUID/full Work id/origin episode and configured review endpoint;
v12 authority UUID, run/Job/submission identity; reviewed packet digest and
selection reference; exact expected outcome locator; evidence root; reporter
participant; stable registration identity. Do not use the preparation claim as
the current execution claim. The caller supplies explicit canonical v11 binary
and config; reporter checks opened authority identity and never guesses a store.

Registration binds one selected run, not a wildcard directory scan. Attempt IDs
are filled from matched retained outcome/public status, never inferred from the
Job name. Zero admissions is explicit; unknown is distinct from an empty list.
Registration/dispatch state belongs to the adapter, never pretends to be workflow
authority. Keep credentials, arbitrary provider logs and authentication tokens
out of the envelope and v11 message. Preserve safe evidence locators and digests.

## Reconciliation and publication

1. Reconcile all registered, undelivered runs at startup and at a bounded interval;
   prompt reconciliation after supervisor exit is an optimization. Restart does
   not submit, serve, cancel or retry a Job and never re-runs the supervisor.
2. Validate version, identity, containment and exact outcome bytes. Distinguish
   supervisor-ended held, Job/stage disposition, container cessation and cleanup
   uncertainty. Settled, failed, held, interrupted and no-admission results all
   need collection. None means product acceptance. If supervisor died without
   outcome, retain a visible incomplete state; supported current readback may
   supply an explicitly incomplete diagnostic, never fabricated successful output.
3. Persist the exact bounded create operands before sending. Stable op-id derives
   from registration identity plus origin authority/run identity, not outcome
   content. Otherwise changed content could create a second result. Bind content
   digest in the immutable operands. Conflicting later evidence is a visible
   conflict requiring reconciliation, never silently overwritten or resent under
   a new key. Concurrent reporters serialize the same registration.
4. Invoke supported v11 create once logically: configured review kind, top-level
   external-report Work, explicit classification, finite collection/diagnosis
   title and immutable body naming origin/full run/attempt/evidence/outcome.
   No parent/follow-up guess based on racy origin state; no bind to the existing
   origin dossier (one dossier belongs to one Work). A lightweight collection
   Work may reference that dossier without claiming its binding.
5. On lost reply, retry identical canonical operands/op-id under the SAME actor.
   V11's committed creation is the authority. Save returned Work/event identities;
   read back its route/detail. A missing local ack is not permission for new Work.
   Unavailable CLI/authority leaves durable pending delivery and an actionable
   error, with bounded retry/backoff; it never launches another provider.
6. On actor/config/authority/route mismatch, retain evidence and refuse publication
   until explicitly reconciled. Never impersonate a reviewer/owner or silently
   switch actor to bypass replay. Origin may now be closed, re-routed or claimed:
   collection still reports the historical run and does not mutate that origin.

The consumer claims collection Work, verifies evidence/current origin, diagnoses
failures or independently reviews the exact candidate. Subsequent origin routing
uses existing authority and coordination, not reporter privileges. Cessation
uncertainty remains explicit and prevents unsafe replacement; creating diagnosis
Work does not release any v12 resource gate.

## Required deterministic acceptance

- Each settled/failed/held/interrupted/no-admission case reaches one actionable
  review Work with exact origin, packet, Job/attempt, evidence and uncertainty.
- Crashes before publish, after v11 commit/before reply, and after reply/before
  local acknowledgement reconcile without loss or duplicate creation. Use a
  disposable real v11 CLI authority for replay tests, with deterministic v12
  outcome fixtures; no live provider question is needed for reporter semantics.
- Concurrent reconciliations create one Work; changed outcome or envelope under
  one identity refuses; two independent Jobs make two independently routed Works.
- Origin changes episode, closes, or is claimed before/during delivery: origin
  stays byte-for-byte equivalent in workflow state/events caused by this adapter;
  collection records original identity and leaves current ownership intact.
- Missing/partial/malformed/foreign outcome, inaccessible evidence, stale status,
  uncertain runtime and unavailable CLI remain explicit; no false acceptance,
  cleanup, provider retry, raw SQL or automatic original-Work close occurs.
- Safe bounded evidence only: credential/log prose does not enter v11 payload;
  public supported readback names the result-collection Work and delivery state.

Prepared packet must pin source/manifest, tests, command, runtime, limits and
ownership. Implementation is a v12 Job after independent packet review. Future
real deployment needs selected reporter identity, lifecycle owner/startup hook,
durable storage and exact authorized CLI access; this proposal enables none.
