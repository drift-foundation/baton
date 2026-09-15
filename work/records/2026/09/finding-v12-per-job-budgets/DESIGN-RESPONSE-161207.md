# Response to independent design review161103

baton.codex, claim161207, 2026-09-13. V2 is a proposal for independent review,
not a sign-off on my own design. Current source/candidate inventory is
research-161207.json; all29 candidate paths and27 previously inventoried source
paths are unchanged. Three additional source paths are now fingerprinted.

| Review finding | Response and concrete revision |
| --- | --- |
| P1: no representation for child capacity; pool kind/unique occupancy matters | Agreed. V2 §A selects explicit root/member relations in JobStore, preserving current stage-allocation FK and unique live indexes. A membership is not a fabricated stage allocation. One root occupies the real integrator; unique admitted member enforces serial phases; parent apply also requires admission. Common `_move` guards every release branch. Schema/store/scheduler scope is explicit |
| P1: portable custody belongs in slice one | Agreed. V2 §B names separate managed result storage and closed semantic task/report, avoiding dummy legacy paths. Existing integration schema5 has no migration: narrowly scoped5→6 additive migration/read-only compatibility is explicitly proposed. Cross-table creation/read guards preserve one result per source/target snapshot |
| P2: target-owner boundary affirmed but adapter absent | Accepted as independently reviewed boundary. V2 names a trusted node-local entrypoint with canonical target, entry/lease/fence, admitted old revision, authorized candidate and collected evidence. Live owner capabilities resolve locally; stale/unavailable grants refuse. Generic transport is unchanged; no farm/backend success presumed |
| P2: exact existing host tests need managed equivalents | V2 §C enumerates exact methods, including all four scratch/release cases. Preserve legacy behavior; new managed counterparts assert the same command/bound/content/harness/prefix/suffix/custody. Existing `_watching` supplies a host-execution trap, whose reach must itself be checked |
| Serial phases need an enforcement point | Explicit begin/admit/end operations, unique active-member index, durable admission before start, and all-release guard. Separate-store/adapter crashes retain membership and reconcile exact ordinary operation rather than pretending a distributed atomic commit |
| No report vs report with no exit status | Required different states in §B. Unavailable collected output stays manager uncertainty; never invent a worker report or numerical failure status |

One further concrete obligation is added to the design, not silently solved:
preparation failure can leave the parent's final-apply attempt activated without
a runtime. `finalize_quiescent_assignment` refuses this; `request_cancellation`
fences it but `ordered=false` is not stop proof. V2 proposes a narrow public
fenced-before-start reader, requiring actual cancellation/fence, no start intent,
no attached runtime and the cancelling axis. If a start raced, retain/reconcile
the real attempt. Independent review must affirm this reader and both race orders
before its scope is accepted. No generic start/cancel rewrite is authorized.

These revisions resolve the documentary omissions with explicit, reviewable
choices; they do not claim the new contracts already exist. No source or test
was edited and no runtime experiment was needed. Read-only inventory0.0027992710020043887s
brings reviewer cumulative147.7342205499972s. Author246runs2530.5844189850177s plus
four unknown activities unchanged. Positive recovery/isolation acceptance remains.
