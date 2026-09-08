# W106673 closed failure-reason candidate — claim112817

Owner112815 authorizes dossier-only preparation after the scoped operator debug
search found no matching regular files. Independent candidate review precedes a
separate exact owner execution decision. No live run or private-data inspection
is authorized by this package. The search does not exclude every possible diagnostic.

## One optional result field

The official [Agent SDK ResultMessage source](https://raw.githubusercontent.com/anthropics/claude-agent-sdk-python/main/src/claude_agent_sdk/types.py)
defines `api_error_status` for a failed API call reported with `subtype=success`
and `is_error=true`, dating CLI emission to 2.1.110. The official
[message parser](https://raw.githubusercontent.com/anthropics/claude-agent-sdk-python/main/src/claude_agent_sdk/_internal/message_parser.py)
reads that top-level field. This supports selecting it for CLI2.1.247; actual
emission by the fixed image remains unobserved. The historical exported run
retains no such field, so its status and provider cause remain unknown.

The new supervisor adds `failure_reason` to the existing result-validation
diagnostic, immediately before the unchanged result acceptance predicate:

```json
{"shape":"known","http_status":429}
```

This example is synthetic. Allowed integer values are 400,401,402,403,404,409,
413,429,500,504,529 from the official [HTTP error list](https://platform.claude.com/docs/en/api/errors).
The value names only the CLI-reported HTTP status. It does not prove an expired
credential, account quota, unavailable model, remote acceptance or historical cause.
No prose classification or provider-specific cause mapping is performed.

| Input api_error_status | shape | http_status |
| --- | --- | --- |
| Absent | missing | null |
| JSON null | null | null |
| Exact integer in the allowlist | known | The fixed integer |
| Other integer | unknown | null |
| Any other type, including boolean/float/string | wrong-type | null |

The projection reads only this field; result/errors text, assistant content,
request IDs, arbitrary nested keys, stderr and private files remain excluded.
Unknown values are never copied or stringified. Each summary contains exactly
`shape` and `http_status`; inconsistent or extra values refuse at the host before
logging. The host permits it only at the existing diagnostic result-validation
stage, with unchanged arm/operation/turn/time/order checks. Earlier frames lacking
the summary remain unobserved, not fabricated success. The result_fields summary
remains independently optional for legacy frames and unchanged when present.

A status never grants or revokes acceptance. A true error flag still refuses,
including subtype=success with a known status. Existing session/model/turn/cost,
consumption, restoration, credential and ending predicates remain unchanged.
No additional turn, frame stage, retry or runtime option is introduced.

## Exact separate candidate and proposed invocation

Sources: evidence/live_controller_failure_reason_112817.py and
 evidence/live_supervisor_failure_reason_112817.py.
Manifest: evidence/failure-reason-112817-manifest.json.
Tests: evidence/test_failure_reason_112817.py.
Baseline, transport-contract observations, incremental source patches, transcribed
focused test result and reproducible preservation audit: evidence/failure-reason-112817/.
All152 prior input bindings are retained unchanged; no production source is edited.

Offline commands:

```sh
/usr/bin/python3 -B /home/sl/src/baton/work/records/2026/09/finding-v12-live-session-workspace-detach/evidence/test_failure_reason_112817.py
/usr/bin/python3 -B /home/sl/src/baton/work/records/2026/09/finding-v12-live-session-workspace-detach/evidence/live_controller_failure_reason_112817.py --audit
```

One proposed operator invocation after independent review and separate owner
execution approval:

```sh
sudo -- /usr/bin/env -i PATH=/usr/bin:/bin /usr/bin/python3 -B /home/sl/src/baton/work/records/2026/09/finding-v12-live-session-workspace-detach/evidence/live_controller_failure_reason_112817.py --run
```

This supersedes only the future source/manifest/invocation selection in
DEPENDENCY-REBIND-112609.md. All earlier candidates, reviews and exports remain
historical. The earlier execution grant was consumed and is not reused.

RESTORED-ONLY.md and RESULT-DIAGNOSTICS.md retain their experiment boundaries:
two containers/two user turns,180s each,420s work plus180s ending within600s,
fixed image/CLI/model, ordinary bridge and existing private credential delivery.
Nominal USD2 is not a verified hard billing cap. Initial success, exact confirmed
shutdown and fixed-byte verification precede replacement; same-session/workspace
restoration and the remembered-token correction after ordinary revocation precede
restoration acceptance. Closed exports and exact ending observations return for
independent evidence review. Uncertain shutdown retains credential delivery.
No automatic retry, production adoption, cleanup expansion or retained-arm repeat.
Accepted retained proof remains separate; restoration and comparison are unproved.

## Verification

Seventeen focused checks pass: seven new status/redaction/correlation checks,
eight unchanged result-diagnostic cases and two unchanged custody/ending cases.
Real supervisor-to-host methods exercise synthetic success/failure streams and
retained event output. Invalid summaries are rejected before logging. Tests cover
all fixed codes, missing/null/unknown/malformed inputs, extra fields, cross-turn/
arm/stage/order attempts, original acceptance predicates and legacy absence.

Exact source comparison verifies unchanged result acceptance, full turn loop,
CLI invocation, credentials, restoration, custody and ending bodies. All305
protected historical files match the claim baseline. The new manifest's standalone
audit verifies the complete current source closure. Tests construct no live
provider/container or credential reader. No broad suite was run; earlier broad
failures remain unwaived. These checks prepare a diagnostic observation, not a
historical explanation or live restoration result.
