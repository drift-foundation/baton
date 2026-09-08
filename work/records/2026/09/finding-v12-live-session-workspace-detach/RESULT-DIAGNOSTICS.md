# Closed restored-session result diagnostics — W106673

Prepared by baton.tuner, claim111078, under owner reroute111076 and
review-2026-09-07T14-50-28Z.md. This is a separately bound diagnostic candidate.
Independent review precedes a separate owner execution decision. Preparation
does not authorize a live invocation or inspection of retained private sessions.

The failed restored-first result discarded subtype and is_error. The new
supervisor records their closed classifications at provider-result-validation,
after provider-response-observed and before the unchanged result_projection.
The host validates the exact nested field set and vocabulary before recording it
in the arm's events.json. Existing arm/operation/turn, ordering and timestamp
checks still apply. A failed result still refuses, permits no validated
consumption or replacement, and follows the existing confirmed-ending path.

## Closed field vocabulary

| Field | Exported values |
| --- | --- |
| subtype | success, missing, known-nonsuccess, unknown, wrong-type |
| known_subtype | One of the four fixed labels below only for known-nonsuccess; otherwise null |
| is_error | false, true, missing, wrong-type |

The fixed known labels are error_during_execution, error_max_turns,
error_max_budget_usd and error_max_structured_output_retries. These are verified
against Anthropic's [result subtype contract](https://code.claude.com/docs/en/agent-sdk/agent-loop)
and recorded locally in evidence/result-subtype-contract-111078.json. This
defines an allowlist; it does not prove that the pinned CLI emits every label or
identify a historical failure. Unknown strings stay unknown, never copied.
Both fields are independent: success plus is_error=true still fails; a known
nonsuccess plus is_error=false still fails. Numeric 0/1 are wrong-type flags.

No errors/result text, messages, arbitrary keys, stderr, transcripts, credentials
or private session paths are exported. No additional provider-root-cause or
structured-error-code interpretation is justified by this scope. A known subtype
names only the observed contract label, never an inferred auth/network cause.

The new supervisor always emits result_fields upon reaching result validation.
The host also retains its earlier diagnostic-frame shape for existing offline
fixtures: absence of result_fields means unobserved, not success. It never
fabricates a summary for a legacy frame. This optional observation does not
change any result-acceptance predicate. Extra fields, unknown classifications,
misplaced summaries and inconsistent known_subtype values refuse before logging.

## Separate candidate and invocation

Sources: evidence/live_controller_result_diagnostics.py and
evidence/live_supervisor_result_diagnostics.py.
Manifest: evidence/result-diagnostics-manifest.json.
Incremental patch, baseline, preservation audit and verification use unique
claim111078 paths; old sources, manifests, reviews and exports remain unchanged.

Offline commands:

```sh
/usr/bin/python3 -B /home/sl/src/baton/work/records/2026/09/finding-v12-live-session-workspace-detach/evidence/test_result_diagnostics.py
/usr/bin/python3 -B /home/sl/src/baton/work/records/2026/09/finding-v12-live-session-workspace-detach/evidence/test_result_diagnostics.py --broad
/usr/bin/python3 -B /home/sl/src/baton/work/records/2026/09/finding-v12-live-session-workspace-detach/evidence/live_controller_result_diagnostics.py --audit
```

Proposed one operator invocation, only following independent candidate review
and separate exact owner execution approval:

```sh
sudo -- /usr/bin/env -i PATH=/usr/bin:/bin /usr/bin/python3 -B /home/sl/src/baton/work/records/2026/09/finding-v12-live-session-workspace-detach/evidence/live_controller_result_diagnostics.py --run
```

This supersedes only the future candidate, manifest and invocation selection in
RESTORED-CONSTRUCTOR-CORRECTION.md. RESTORED-ONLY.md's two-container/two-turn scope,
180s per turn, 420s work plus180s ending within600s, fixed image/model/CLI,
ordinary bridge, approved private credential delivery and all custody/ending
rules remain. Nominal USD2 is not a verified hard billing cap. No retained-arm
repeat, automatic retry, model/image substitution or production adoption.

Fresh initial work must pass its result, exact shutdown receipt and fixed-byte
verification before replacement. Restored correction must preserve actual session
and workspace identity, verify the remembered token after ordinary revocation
and confirm final shutdown. Source files, private resources and stopped containers
remain; normal approved credential teardown is unchanged. Success remains
restored-only-passed, with separate timings and matched_comparison=false.
Earlier retained proof remains valid and separate; restoration is still unproved.

## Dependency revalidation and verification

The prior125-input manifest has one current dependency change:
v12/python/src/baton_v12/job_manager/review_driver.py, from
78ddccdf39cf46882f72dbe12b7b1501322f7da7689eb071ac3012a5f5f4b7a1 to
62db37ee8cd52bf99fc4e68b766841586f921324366e9e0191fc9618b33e6765.
The new manifest explicitly binds current bytes; no old manifest is edited and
no unrelated work is reverted. This current observation proves no historical
runtime drift. The module's review lifecycle is outside this experiment; the
offline check imports the actual new snapshot's credential/group/store/source
APIs without constructing a source reader or starting a manager/provider.

Eight focused tests cover all field-shape combinations, actual supervisor-to-host
success/failure, missing results, unchanged late acceptance checks, unknown-value
redaction, exact nested schema, correlation/order and legacy no-summary handling.
The broader gate retains all23 preceding diagnostic/restoration/real-constructor
assertions unchanged, adds the existing stream/result checks against the new
supervisor, and verifies fresh imports from the newly bound runtime snapshot.
AST/text checks bind unchanged acceptance, argv, restoration, credentials,
mount/receipt, source-snapshot, setup and ending behavior. These are offline
observations; historical provider cause and live restoration remain unknown.
