# W71879 supported provider detail — claim148870

This is a bounded diagnostic successor to accepted prepared-147109. It preserves
historical run6 operands for offline tests only. Do not provision, prepare, render,
validate, build images or execute run.py from this directory. No fresh-run packaging
or execution marker is supplied. The inherited evidence subdirectory is historical
claim147109 evidence, not a statement that old source bindings describe this change.

The owning current handoff is ../PROVIDER-DETAIL-148870.md. Current evidence and
candidate manifest are under ../evidence/diagnostic-148870. The product patch lives
at v12/worker/claude_agent.py and its additive tests at
v12/python/tests/manager/test_claude_agent.py. This directory changes only the
failure_observation.py reader, replaces this README and adds test_provider_detail.py.
Every other inherited file stays exact. The run.py, deployment.py and
target_posture.py helpers remain unchanged; the fourth helper needs its new digest
in any future independent execution review binding.

The actual installed2.1.247 provider's bundled source supplies an exact fixed OAuth
expiry/refresh-failure explanation and a nullable integer api_error_status in its
result output. The adapter keeps existing failure_reason and adds an optional
provider.diagnostic on nonzero provider results. It copies no arbitrary text or ID.
The new seven-field baton.provider-diagnostic/1 object contains:

- http_status: an exact integer400..599 or null; status alone is never an auth cause.
- classification: authentication_failed only for the exact supported constant;
  otherwise unknown.
- explanation: the source-backed fixed OAuth sentence or null.
- explanation_status: supported-constant, withheld or unavailable.
- request_id: null; request_id_status: unavailable.
- schema: baton.provider-diagnostic/1.

The recognized sentence is: Failed to authenticate: OAuth session expired and could
not be refreshed. It is reconstructed from an adapter constant after whole-value
equality, never substring/pattern matching. Unknown prose is explicitly withheld.
Malformed/partial/over-ceiling/unsupported records retain gaps. Status/terminal
fields and detail do not change lifecycle outcome. Success/start-error/timeout and
older injected providers retain their former provider shape without diagnostic.

The successor report reader requires exact schema/key/value consistency and a
nonzero process status with the existing api-error reason. It reconstructs the
constant/typed detail, preserves HTTP status and explicit omissions, and exposes
a provider-reported OAuth cause only for the recognized explanation. Legacy
reports remain accepted with unknown cause. Its existing artifact/task/attempt
correlation, no-follow reads and bounds remain; diagnostic detail is supplementary
published evidence, not a new artifact attestation or lifecycle owner.

Validation:181 adapter tests,54 offline package tests(49 inherited plus five new),
and106 offline worker-entry tests pass. Nine additive adapter cases include real
pipe/sentinel publication, strict parser/bounds/success handling and proposal1/2/
review-log1 compatibility. All preexisting test classes/functions are AST-identical.
The first failed adapter fixture and duplicate discovery in the first reader run
are retained and explained in the owning FINDING and handoff. No copied provider
code, real credentials, network/model/image execution or retry was used.

Ordinary offline verification only:

    python3 -B work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/finding-two-job-pipeline-proof/prepared-148870/verify_offline.py

Both images include claude_agent.py and remain the old bytes. Any future image
build/use must bind this reviewed source, exact provider installation evidence and
new immutable image digests. This source/helper change is not a deployed fix, does
not reconstruct discarded run6 detail and does not prove that OAuth caused run6.
Other provider prose/request identifiers remain unavailable under this boundary.
Six failed runs, all limits/guards/deferrals and real A/B proof obligations remain.
