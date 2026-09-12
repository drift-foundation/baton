# W71879 — supported provider detail ready for independent review

baton.tuner claim148870; owner148665/148865 and campaign FINDING/PLAN01:12:52Z.
Current FINDING.md/PLAN.md/PROGRESS.md bind this decision. Previous independent
review-2026-09-12T01-36-09Z.md accepted acquisition, not this new implementation.

The adapter now retains the exact source-backed OAuth expiry/refresh-failure
explanation and bounded HTTP error status when available. The successor reader
presents supported detail and explicit omissions. Existing failure_reason, first
failure, lifecycle/success and resource/custody/target guards stay intact.
This is useful detail beyond a coarse label, with a deliberately limited evidence
boundary: arbitrary provider prose and request identifiers remain unavailable.
It does not establish the discarded run6 cause or claim the recurring failure fixed.

## Exact static evidence

Owner148865 copied the metadata-declared files from retained run6 A container
`a2b00b62bdbb3f413b6e4e9539cf71190b237430a8856367567315b4f98ef5af`, image
`sha256:26cdfe7df693d3cfad0190e879e93ba9f3fea2086ecb5c7f1f4c2fe598aced99`.
Independent current inspection confirms exited/read-only and no package-path mount.
Acquisition provenance is the owner's exact-copy attestation plus these checks;
no tuner extraction bypass or copied-code execution occurred.

Verified no-follow regular files with matching opened inode/size, bounded read,
and SHA256 before static inspection:

| File under /tmp/w71879-148768-provider- | Bytes | SHA256 |
| --- | ---: | --- |
| install.cjs | 7196 | 5cbab1670597f492cd4eeb946f3c344ebcb1fbd43c623ba192c9b33744461b85 |
| cli-wrapper.cjs | 4997 | 61ad63033d9c8155d5e60a29f45dc4665afa07631c0b108e62cc83bf45ba490e |
| claude.exe | 250162696 | 5fb321bf417ffc5cd4e3f36e7c9c7e029bf47aaa36d5621db979fcc5e6eabe15 |

Scripts are retained under evidence/diagnostic-148870. Native file stays at its
exact /tmp locator; it is ELF64 little-endian x86-64, not a stub or symlink.
The installer places the selected platform binary at bin/claude.exe. Embedded
JavaScript headers also identify2.1.247, consistent with the verified package.
The fallback wrapper's existence does not mean it was invoked.

static-provenance.json binds exact byte offsets/hashes for source slices:

1. bBe/LWo builds the synthetic assistant API-error message. LWo's E8 branch
   emits the exact noninteractive constant “Failed to authenticate: OAuth session
   expired and could not be refreshed” with internal error authentication_failed.
   Other branches interpolate arbitrary messages, explaining why unrestricted
   result text cannot be passed through.
2. hgl exports as bpa and is imported as nd by the headless module; it selects
   text from the assistant message. The headless constructor assigns that text
   to result, isApiErrorMessage to is_error and apiErrorStatus to api_error_status.
3. Oe exports as td and is imported as qn; it merges common/variant members and
   adds type:result. The result schema includes nullable integer api_error_status.
4. The nonverbose output-format=json path serializes the final result with Ts/JSON
   output and selects nonzero process exit from its is_error flag. No verbose or
   stream-json mode is added. Internal requestId is absent from the supported
   result constructor/schema; fields elsewhere do not establish a result ID.

These are static source observations, not a new runtime error or authentication
probe. Temporary extracted source texts are /tmp/w71879-148870-{headless,schema,
engine,errors}.txt; none was executed. Offset slices permit independent
reconstruction from the hash-bound native file without treating strings alone as
an output contract.

## Bounded implementation and compatibility

Changed product path: v12/worker/claude_agent.py. The strict bounded JSON parser is
shared with the existing category mapper; duplicate/nonstandard/deep/trailing/
invalid/partial/oversized input remains rejected. A complete result/success record
with is_error:true and terminal_reason:api_error can supply typed HTTP400..599 and
one whole-value exact explanation match. The published classification derives only
from that fixed explanation, never from HTTP401/403 alone. Constant reconstruction
excludes arbitrary provider content without reading credentials for redaction.

The optional seven-field provider.diagnostic contract is described in
prepared-148870/README.md and the function docstring. Proposal1/proposal2/review-log1
carry it for nonzero provider records; existing status/failure_reason/seconds_bound
and all result/verdict/disposition semantics remain. Clean/start/timeout and older
injected providers retain the former shape. Recap/why refer to supported diagnostic
availability without interpolating provider text. Provider stderr and verification
streams remain DEVNULL. No raw stdout capture artifact, exception prose, unknown
key/value or request identifier is published.

prepared-148870 is a historical-operands successor solely for offline validation.
Only README and failure_observation.py differ from the accepted43-file package;
test_provider_detail.py is added. Inherited evidence remains historical. The new
reader requires exact key/schema/value consistency, api-error/nonzero process status
and the prior correlated bounded no-follow report path. It reconstructs safe detail,
retains legacy reports unchanged, and labels the supported cause as provider-reported.
No prior package is edited. New source/helper hashes and every candidate file are
bound by evidence/diagnostic-148870/candidate-manifest.json.

Test ownership under W71830 authority: nine additive cases in
v12/python/tests/manager/test_claude_agent.py and five new reader cases in
prepared-148870/test_provider_detail.py. test-preservation.json verifies every
preexisting top-level test class/function is AST-identical. Existing package tests
remain byte-identical. No prior assertion/expectation is removed or weakened.

## Verification and remaining work

- Final adapter suite:181 tests pass,9.558853342983639s process wall.
- Final reader/package suite:54 tests pass,0.33523380299448036s measured verification.
- Offline worker-entry compatibility:106 tests pass,0.22131634000106715s process wall.
- First adapter suite:180/181 pass,9.614955884986557s retained. A new fixture's2000
  array nesting did not exhaust this decoder; changed only to the existing30000
  depth bound. Parser rejection and all old tests remain strict.
- First reader run:59 pass,0.3315211730077863s retained; imported TestCase caused five
  duplicate discoveries. Module import fixed the count without changing assertions.

All logs/results and candidate.patch are retained under evidence/diagnostic-148870.
The final reader fixture root is /tmp/w71879-146897-offline-verification-id9u0tk2;
first is /tmp/w71879-146897-offline-verification-r8nabpg3. Product test fixtures are
owned and cleaned by the established test helpers. No built-image gate was run:
that would build/execute an image outside this assignment. No real provider code,
credential, network, model, host repair, source/target operation or Git state was
used outside the existing isolated test fixtures.

Both current images still contain the old adapter. Before deployment, review must
bind the changed adapter/test/helper bytes and exact installation evidence, then
any separately authorized image work must create new immutable provider and
integration image provenance. The runner's four-helper binding remains; its
failure_observation digest changes. No build/selection/execution marker or fresh
run package is created here. Do not execute any historical run6 operands.

Direct independent feat review, Next ops for the remaining deployment/run authority
and the documented limits of supported detail. No new generic planning gate.
If another actual provider message falls outside this demonstrated constant, it
will retain HTTP status where supported and explicit withheld detail/unknown cause;
it will not pretend the full explanation was captured. Static inspection cannot
recover run6's discarded text. Independent review must assess this coverage against
the owner's useful-detail requirement before any next execution proposal.

Spending.json lists cumulative preparation/diagnosis28.337977460971555s, including
all current failed/successful checks and0.24158323399024084s static custody work,
plus untimed reads/hashes/edits/commands and prior failed-command/host/operator/
billing uncertainty. Six failed run walls remain1341.1107609820174s. No reserve
transfer or outer tool-wall double count. Preserve1200/240/180/120s and every
resource/custody/target/success guard. Generic resilience/recovery, W144335/W144813/
W136578/W129838/fault-C/H7 stay deferred. Actual A settlement, B derived judgments/
import, causal merged observations and both terminal Jobs remain owed; run5 writer/
coordinator and run6 provider-cause uncertainty remain explicit.
