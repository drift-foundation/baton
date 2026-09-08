# Exact declaration accounting proposal — W116962

Prepared by baton.tuner under claim117120. Awaiting independent review and explicit bounded existing-test disposition. The live inventory remains unchanged at SHA2563973301e09e27a4cb724969c158a0441a629037718d755dae1ada594a2a24b5c.

## Concrete proposed source change

Review evidence/candidate.patch and evidence/candidate.py, candidate SHA256830496b44569e7a88c29771577d616f94b52bcd3066c48f6fa338aab24a30d04. These are unapplied review artifacts. The sole proposed target is v12/python/tests/manager/test_boundary_inventory.py.

The candidate adds immutable `_BoundaryOccurrence` records, `_boundary_calls`, cached `boundary_occurrences`, `_boundary_claims`, `_account_boundary_calls`, and registers the new projection in MEMOISED. It adds sys/NamedTuple/mock.patch imports, the independent eleven-method HelperDeclarationsHaveExactAccounting class and its fragment/cache-cleanup helper. No runtime or catalog path changes are proposed.

The only existing method changed is EveryReceivingEntryHasOneOwner.test_every_boundary_call_belongs_to_an_entry_or_is_declared. Its final `assertEqual(orphans, [], "boundary calls attributed to no entry")` remains. Its input changes from the global claimed `(kind, label)` set to exact occurrence claims and declaration links. evidence/candidate-audit.json proves all other existing functions and classes are AST-identical, including every other method in this class. Existing missing-owner, double-ownership, independent-universe, stale-declaration, probe-completeness and wrong-boundary assertions remain unchanged.

This exact method edit and MEMOISED addition require an explicit bounded ruling before implementation. Independent review should evaluate the expected-behaviour change itself, not merely the candidate path/hash. This Work's proposal-only scope does not grant it. W117174 owns the separate conditional implementation gate and W116972 now waits on it as well as this proposal; acceptance of a proposal cannot silently release module work.

## Accounting semantics

An occurrence retains `(lexical site, lineno, col_offset, end_lineno, end_col_offset)`, projected owner site, validator kind, contextual label, subject origin, lexical label and whether it was propagated. Source hashes bind spans to the inspected bytes. The projection uses the accepted `_origins`, `_delegations`, `_contexts_at`, `_subject` and `_label` semantics. Its projection to the old owner quadruples is exactly equal on the live package, so it invents no validator and changes no origin.

For each independently discovered entry and existing DELEGATED placement, select actual occurrences using the existing exact-subject-before-covering precedence. Keep the selected occurrence itself; selecting one label never claims another occurrence with that label but a different subject.

An unclaimed occurrence is accounted for only by one of the following:

1. An existing exact NOT_AN_ENTRY triple, whose declaration and stale-exception guard remain unchanged.
2. An actual claimed occurrence with the identical source call, kind, contextual label and qualified read/session origin. This accounts for repeated projections of a helper that performs its own read; a different read site, member, label or source call cannot borrow it.
3. A private helper's lexical caller-parameter declaration linked to actual claimed propagation of the identical source call. This is how `{provider}` at the declaration relates to credentials/launch labels at real receiving sites. Merely appearing in propagated_owners is insufficient. Every propagated occurrence that lacks a direct claim or exact equivalent remains residual even if another context claimed the declaration.

The diagnostic still lists site/kind/label rows for compatibility; evidence retains complete source occurrences so duplicate rows do not erase source identity. No symbolic probe, fabricated owner, label-only waiver or new NOT_AN_ENTRY entry is proposed. Caller-origin helper propagation remains exactly as in the accepted scanner; this accounting proposal does not extend it. Existing named exceptions retain their prior triple granularity, not a newly broadened waiver.

## Measured result and exact scope of the claim

| Measurement | Accepted live baseline | Unapplied candidate |
| --- | ---: | ---: |
| Independent receiving entries | 1365 | 1365 |
| Existing owner triples | unchanged | identical |
| Orphan diagnostic rows | 72 | 77 |
| Retained symbolic rows resolved | 0 | 13 of17 |

There are697 exact occurrences:411 directly claimed,199 linked to actual claims (including25 lexical declaration occurrences),8 covered by existing exceptions, and79 residual occurrences producing77 diagnostic rows. The candidate removes13 old rows and exposes18 previously hidden rows; `72 - 13 + 18 = 77`. This is not a passing inventory. The final candidate's actual aggregate assertion was invoked and failed on the retained residuals as required.

evidence/research.json names every declaration span, actual contextual owner and exact receiving entry, all77 residual rows/79 occurrences, the13 removed rows and18 added rows. The18 additions belong to already scheduled attempts, intake, interrogation, lanes, oci, posture_slots, review_cycles, sessions and workspaces scopes. They are observed accounting residuals, not proof of a runtime defect or authority for automatic new owners. W117174 must revalidate and append the exact module input deltas after accepted implementation; existing planning inputs are preserved as history.

The two provider declarations at intake.py:_provider_ending:2334 and :2336 each link to eight concrete owners: credentials and launch at `_destroyed`, `_destroyed_abandoned`, `_destroyed_failed_start` and `_destroyed_refused_session`. For example, the document at :2334 links to injected/intake.py:_destroyed/adapter.destroy.credentials under `a credentials teardown ending`; the text call at :2336 links to that entry's lifecycle_state under `a credentials teardown ending's state`. The launch labels and subjects stay paired separately. No provider is inferred from a symbolic fragment.

The other eleven resolved symbolic rows belong to AuthorityPort._assignment (six, at assignment_of/cancel/claim/settle_operation) and AuthorityPort._decided (five, at claim/settle_operation). Four remain unresolved: exchange._instant's dynamic member label; OciAdapter._removed and _bound_orphan's dynamic identities; review_cycles._profile's dynamic capability. Their current occurrence projections contain no actual claimed propagation sufficient to discharge these declarations. The source has real call sites (exchange.py:903, oci.py:2566/:2800/:2837/:2866/:2991/:3025, review_cycles.py:535/:632/:747/:908/:1171/:1352/:1543); source calls alone do not prove an inventory claim. Preserve these rows for the already scheduled module revalidation.

## Evidence and verification

The independent fragments assert literal expected call coordinates, labels, read origins and entry keys. They cover actual adopted ownership; absent claims; deleting a validator while preserving the independently discovered entry and the unchanged missing-owner failure; unrelated same-label helpers; same-site/same-line calls with different columns and subjects; one claimed and one unclaimed read context; unreachable helper calls; the unchanged double-owner assertion with an additional stated owner; existing owner-projection parity; repeated projections of one adopted read; and a different label attempting to borrow the same call/origin claim.

Final model:11controls pass,2.606801seconds. Final integrated candidate:11controls pass, exact residual equality, actual aggregate still fails, new projection cached/immutable/registered,2.092230seconds. Initial model9controls passed in2.639535seconds but overcounted projection copies; its bytes and result remain under evidence/initial/. The first candidate build had a harness-only `pathlib` transcription error, so all11 controls stopped before projection; candidate-build-error/ retains its candidate/hash/log and0.071758second failure. The builder was corrected to match the module alias at a word boundary. Neither correction changed the live source or weakened a control.

Including both candidate construction/compile audits (0.175115 and0.183501seconds), measured research/build/verification execution totals7.768940seconds within the predeclared cumulative10second budget. No probes, suite or daemon ran. No result is claimed for the other aggregate failures or module repairs. Independent acceptance should additionally assess the new projection's boundedness using the existing cache suite under a separately stated review budget.

## Required disposition and continuation

Independently review the exact candidate, source/entry links, all controls, thirteen removals, eighteen additions, preserved guards, and the unchanged source baseline. If technically accepted, route for an explicit bounded existing-test disposition rather than silently turning proposal acceptance into implementation permission. Pin that ruling in this FINDING and in W117174's FINDING. Only then may W117174 apply the accepted scope, revalidate affected module inputs, and obtain its own independent acceptance. Preserve any newly discovered separate scanner/module defect as its own bounded gate. W48697 stays open through actual module coverage, unchanged aggregate gates and W115981's final whole-suite gate.
