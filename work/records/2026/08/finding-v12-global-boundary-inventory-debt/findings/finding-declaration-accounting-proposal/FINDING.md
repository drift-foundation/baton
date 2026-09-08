# Prepare exact accounting for contextual helper declarations

Work W116962, inventory parent W48697. Created under inventory planning claim116930.

Proposal-only follow-on to accepted B1. Diagnose the retained symbolic helper declaration orphan rows and their actual propagated owner relationships, including the two intake._provider_ending labels and related contextual declarations. Read existing scanner and aggregate assertions; prepare a bounded source/expected-behaviour proposal with independent positive/negative cases, preserving absent-owner and double-ownership detection. Do not edit existing test helpers or assertions until explicit bounded scope is accepted. No blanket NOT_AN_ENTRY, symbolic probes or runtime changes. This research result precedes module scopes because shared accounting can change their census.

The exact retained planning inputs are in evidence/inputs.json. They are
observed scanner/catalog rows, not proof of absent runtime validation or
authority to fabricate owners. Parent MODULE-SCOPES.md defines the common
assessment and source-hash baseline. Preserve all accepted predecessor history.

## 2026-09-08 — claim117120 research decision (baton.tuner)

The independent planning review at ../finding-module-scope-review/review-2026-09-08T06-42-22Z.md accepts this research only. No existing inventory helper, assertion, probe or runtime file will be edited by this claim. The proposed accounting must retain the lexical boundary call's source span, its contextual owner site/label/subject, and the receiving entry actually claiming that occurrence. A matching label somewhere else is insufficient. A private helper declaration may be accounted for by a claimed propagated occurrence of that exact source call; an unclaimed propagated context must remain visible. Neither the existing global `(kind, label)` set nor subtracting `propagated_owners()` proves this relationship.

Read-only source revalidation found the runtime package at v12/python/src/baton_v12/worker_manager. The initial guessed v12/python/baton/manager/intake.py path did not exist; the canonical source was located and read before further research. This was a path lookup error, not a missing required policy or a Baton defect.

Before execution: retain an isolated proposal model and independent source fragments in evidence/. Run only that bounded model against the pinned live scanner and its unchanged independent discovery, plus positive/absent-owner/same-label/unclaimed-context/double-ownership controls. Cumulative execution budget10seconds; no probe, suite, daemon or runtime act. Real-source results must enumerate every symbolic declaration's source-call identity, actual propagated contexts and exact entry claims, and retain newly exposed residuals rather than forcing a green aggregate. Implementation disposition and a separate blocking gate are required before module work resumes.

The initial model and full evidence are preserved under evidence/initial/ (2.639535seconds,9controls passed). It linked13 of17 symbolic rows but reported250 orphan rows because repeated projections of the SAME lexical read/validator, concrete label and qualified read origin had no entry at their projection site. Observed examples include manifests._manifest_row and store.ControlStore._operation_row. The initial rule requiring each projected site to claim such a copy is superseded in the proposal: copies may share an actual claim only with identical source-call span, kind, concrete label and qualified read/session subject. Distinct read sites, members, source calls and labels cannot borrow it. Two additive controls cover this correction; a second model run is justified by this demonstrated accounting error and remains inside the original cumulative10second budget. This does not change any live scanner behavior.

Final proposal and candidate are documented in PROPOSAL.md. The candidate resolves13 of17 symbolic rows, retains4, and exposes18 previously hidden diagnostic rows. It preserves discovery/owner projections and yields77 residual rows rather than pretending inventory completion. Source/expected-behaviour scope is frozen by candidate830496b44569e7a88c29771577d616f94b52bcd3066c48f6fa338aab24a30d04. Eleven controls pass both standalone and in the candidate; the aggregate still fails. The first candidate artifact had a harness-only pathlib transcription error, retained under evidence/candidate-build-error/ before correction. No live source changed. W117174 retains the actual implementation gate, and lanes waits for that gate. Independent technical review and explicit bounded existing-test disposition remain pending.

## 2026-09-08 independent technical acceptance — claim117208

Technically accepted exact unapplied830496b4 candidate for owner disposition;
review-2026-09-08T07-05-06Z.md evaluates the changed assertion behaviour and
enumerates the exact recommended one-file scope. Independent six cache checks,
same-label/distinct-read attribution and occurrence discriminators pass within
15seconds; evidence/review-117208.json. Live3973301e baseline remains unchanged.
This supersedes pending-technical-review state only. Explicit bounded existing-
test disposition is still required and is routed to baton.ops. Pin the selected
ruling here and in W117174 before edits.77 residual rows remain for module work.

## 2026-09-08 — owner disposition pinned by baton.tuner, claim119093

Confirmed: baton.slaw closed proposal W116962 satisfying at event118950,
2026-09-08T12:22:01Z: "Accept the independently reviewed exact declaration-accounting
proposal with explicit owner approval in response to117235." That explicit
reference accepts the bounded change requested in T116962 message117235 and
technically reviewed in finding-declaration-accounting-proposal/review-2026-09-08T07-05-06Z.md.
It supersedes the earlier pending-owner-disposition/no-live-authority state;
it does not supersede the proposal's historical measurements or review.

Approved sole product target: v12/python/tests/manager/test_boundary_inventory.py,
base SHA2563973301e09e27a4cb724969c158a0441a629037718d755dae1ada594a2a24b5c,
exact candidate SHA256830496b44569e7a88c29771577d616f94b52bcd3066c48f6fa338aab24a30d04.
Scope: EveryReceivingEntryHasOneOwner.test_every_boundary_call_belongs_to_an_entry_or_is_declared
uses exact occurrence claims/declaration links instead of global kind/label
claims, preserving its final empty-list assertion; new occurrence/claim helpers,
imports, MEMOISED registration and eleven additive controls. Other assertions,
scanner semantics, owner/probe catalogs and runtime remain outside this ruling.

Revalidated before application: live/base and candidate hashes match exactly;
all 27 recorded runtime source hashes and all proposal evidence hashes match.
The existing target is a non-symlink regular owner-writable file, mode0644.
Implementation owns application and evidence/module-input accounting under
W117174, followed by independent acceptance. Proposal closure alone completes
neither that implementation nor the inventory campaign.
