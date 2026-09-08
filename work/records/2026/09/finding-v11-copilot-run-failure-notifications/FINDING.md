# Copilot notification of runner failures

2026-09-07 — owner-authorized foreground implementation by baton.prompt.
Work W114322; follow-up to closed W110391. No v12 dependency.

Observed: W110935 remained claimed after ACP turns ended; incidents 35 and 36
were assigned to baton.slaw, and runtime reported failed. The notifier only
read actionable-work and obligations, so neither failure woke the copilot.

Confirmed decision: extend the existing notifier with canonical read-only
incidents and runtime queries. Filter both by exact configured action_owner.
Deliver incident:N and runtime:TEAM.MEMBER locators through the existing
advisory-only prompt channel. Never recover claims, dismiss incidents, launch
workers or read logs automatically in the notifier. No bridge or v12 change.

Failure identity includes participant, incarnation, session, work, episode and
cause. Runtime state-transition time distinguishes later failures; heartbeat,
lease expiry, ages and incident occurrence counters do not trigger advisories.
Correlate an incident with a runtime only when these identities agree and the
incident began at or after that runtime's failed transition. Prefer the incident
when both first appear; a subsequently arriving matching representation is
acknowledged silently only when the first was accepted. Recovery prunes runtime
state; still-open incidents remain operator attention until dismissed. Reads are
separate snapshots: advisories always require a current canonical re-read.

Scope: tools/codex_copilot_notifier.py, tools/test_codex_copilot_notifier.py,
tools/CODEX-COPILOT-NOTIFIER.md and this record. Existing test fixtures may be
adapted for the two added query responses; preserve existing assertions.

Verification before running: focused notifier unittest module only, expected
under 10 seconds. New cases must demonstrate W110935-style failures, ownership,
late/simultaneous correlation, recurrence, heartbeat deduplication, busy recovery,
authority/read failure and locator-only delivery. No broad suite or live advisory.

Implementation clarification: once a runtime version has been paired with an
accepted incident, the cursor remembers that fact for that runtime version.
Another new incident is then distinct attention even if the earlier incident was
dismissed while the same failed runtime remained visible. This prevents late-
representation deduplication from suppressing a genuine subsequent incident.
The optional paired cursor field is backward compatible with existing cursors.

## 2026-09-07 independent review: stale contact is not recovery

Confirmed by baton.codex under claim 114371: an accepted runtime-only failure
is forgotten when lease expiry projects that runtime as derived `unknown`.
An identical failed-state renewal preserves canonical `changed_ts`, but the
notifier treats its original failure version as new and retries the same advisory.
The bridge's finite duplicate window can delay, but cannot prevent, redelivery.
See `review-2026-09-07T23-44-02Z.md` and `evidence/review-114371/probe.json`.

Clarification of the earlier recovery-pruning rule: derived `unknown` from lease
expiry is stale contact, not a reported recovery. Preserve the accepted failure
version and its pairing acknowledgement through that interval. A reported
recovery or replacement must still allow a later distinct failure to notify;
unaccepted attention must not become acknowledged merely because it went stale.
This clarifies the existing no-heartbeat/no-expiry-advisory decision, rather than
authorizing a new runtime or bridge protocol. The candidate is not signed off for
restart until this bounded cursor correction receives independent review.

## 2026-09-08 approved correction, revalidated by baton.prompt

Slawomir approved completing the bounded correction and independent review.
Current projection.py confirms expired contact is state=unknown,
provenance=derived, stale=true; its cause is hidden and since becomes the lease
deadline. Neither value can reconstruct the preceding failure. The notifier
must retain only already accepted version hashes and pairing markers for those
runtime locators, without adding stale rows to attention or inventing acceptance.
Preserve this memory even when another advisory is accepted during expiry.
On a live failed report, compare the complete existing failure digest; a changed
incarnation/session/episode/cause/transition is new attention. Reported recovery,
absence or changed ownership prunes the old cursor. No cursor schema or protocol
change is needed; a stale replacement cannot acknowledge its future failed report
because its incarnation changes the failure digest.

File ownership remains baton.prompt for the three notifier paths and this dossier.
Existing test methods and assertions are preserved; expiry/renewal, pairing,
rejected/busy delivery, replacement and unrelated-advisory regressions are additive.

## 2026-09-08T01:02:34Z — independent corrected-candidate sign-off

Confirmed by baton.codex under claim114925: working notifier155589dc, tests
1e206e01 and documentation e61849dc match the supplied manifest and retained
candidate; baselines match review114371. All28 prior test methods remain
AST-identical with eight additive regressions. Canonical expiry/renewal source
supports the derived/stale retention predicate and stable renewed failure hash.

review-2026-09-08T01-02-34Z.md signs off this bounded correction, superseding
the earlier changes-required/no-restart disposition for these exact bytes.
Accepted hashes and pairing survive expiry and unrelated accepted delivery;
unaccepted attention is never manufactured into accepted state. Reuse the captured
36-test passing transcript; no reviewer suite or live advisory was run.

Current next step remains operator-owned notifier-only restart, preserving config
and cursor, followed by visible delivery proof before closure. This source
sign-off is not a deployment or UI-delivery claim and grants no workflow recovery.
