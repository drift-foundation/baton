# Managed delivery ignores current Work priority

Work: W119195. Owner: Baton. Recorded by baton.prompt, 2026-09-08.
The ledger Work already exists; attaching this dossier requires baton.ops
authority and is pending after prompt's canonical bind was refused.

## Observed and confirmed

W115599 was ready High with its owner obligation answered at119126 and route
returned to reviewer at119127. W117174 was lowered High to Normal at119180,
12:46:19Z, but reviewer claimed it at119189, 12:47:10Z. Dispatcher log
/home/sl/baton-v11.14aecfb/log/codex-dispatcher.log records both offers queued
around12:45:08 and the next reviewer turn starting12:46:59.878Z.

The deployment's infra.json launches tools/codex-event-bridge from this
checkout. Its event_bridge.mjs #admit appends unclaimed offers in arrival
order. #drain selects the queue head. #revalidate reads current canonical
wait timeout=0, validates the envelope, and checks exact episode membership
and the participant's claim slot; it does not use current readiness ranking
to select between queued offers. The authority's participant_actions already
orders Work by explicit priority, ready blocker preference, and creation.
This is a dispatcher scheduling defect, not an unauthorized claim or evidence
that the reviewer knowingly rejected the owner's priority instruction.

## 2026-09-08 — initial disposition

Initially filed Normal with a proposed temporary next-pickup instruction and
no new W71830 prerequisite. This did not implement priority-aware selection.

## 2026-09-08 — emergency correction supersedes initial deferral

Slawomir explicitly requested drain and correction as an emergency. This
supersedes the initial Normal-priority deferral and next-pickup-only proposal.
W119195 is now High. Drain is owner-controlled: prompt's attempt was refused
for missing dispatch capability; canonical state119208 confirms owner drain
generation98 with the two then-existing claims finishing.

Proposed bounded correction: when choosing an idle queued unclaimed Work
delivery, select by the current validated canonical readiness order rather
than notification arrival. Preserve exact event identities, claimed recovery,
non-Work rules, occupied-slot deferral, unknown/unreadable retention, stale
withdrawal and ambiguous start reconciliation. Do not reorder an in-flight
delivery or use a second read that can disagree with the eligibility snapshot.
No new priority field or scheduler subsystem is required.

Authorization boundary: prompt has no configured Route and cannot claim this
ops Work. A specific emergency exception for direct prompt implementation and
tests has been requested from Slawomir; implementation awaits that response.
The user has authorized draining and fixing, not identity impersonation,
configuration edits, Git mutations or weakened existing assertions.

The regression must reproduce a downgrade while both offers wait behind a
busy turn, and prove that the current higher-ranked offer starts first while
the other remains retained. Also cover unreadable state, withdrawn/new episodes,
claimed recovery, non-Work handling and ambiguous selected-candidate recovery.

## 2026-09-08 — explicit emergency implementation exception granted

Slawomir answered the specific claim-exception request: "I authorize - we need
this in asap". This supersedes the pending-authorization paragraph above for
W119195 only. Baton.prompt may directly implement and test this bounded fix
while managed dispatch is paused, without a routed claim. No participant
impersonation or accepted-config change is authorized or needed. Canonical
snapshot119262 confirms paused generation98, zero claims. Existing product
paths in both bridge packages were clean before this correction.

The selection uses the single current validated readiness snapshot. If its
first unclaimed Work has not yet reached the local queue, retain lower-ranked
offers for bounded retry rather than starting one ahead of it. Already claimed
recovery and non-Work actions retain their existing eligibility rules. The
queue is never globally shuffled; the selected event retains exact identity
through start, ambiguity and settlement. Start with the observed Codex path;
no ACP correctness claim follows from a Codex-only test.

## 2026-09-08 — bounded selection clarified by compatibility verification

The preceding proposal to wait for a higher-ranked event absent from the local
queue is superseded. Full bridge verification exposed four recovery/other-target
regressions from that extra waiting rule. This correction orders current pending
Work deliveries by the authority's current readiness order; it does not create a
new dependency on an event absent from this target's queue or already delivered.
The producer continues to offer new actions normally. In-flight delivery cannot
be preempted by a later arrival. Existing test assertions remain unchanged.

## 2026-09-08 — restart ownership correction

Prompt invoked stop-drained after zero claims, but the managed stack includes
the app-server hosting this interactive context. The call stopped its own
execution path and prevented it from completing the restart. Slawomir recovered
by restarting the stack. This was prompt's operational mistake, not evidence
of failed priority selection. Future maintenance of this hosting stack must
leave stop/start to the operator; prompt prepares and verifies the fix first.
