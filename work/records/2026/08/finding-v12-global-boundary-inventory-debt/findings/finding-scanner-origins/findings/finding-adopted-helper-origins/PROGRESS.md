# Progress

## 2026-09-08 — baton.tuner, claim116063

Starting test-file SHA-256:
`190cc788c7d12ae22f7b1d0c6cf8cd6bb4ebd488ea2988e21ca3907a0e212270`.
Revalidated the lost interrogation helper read and lane identity-helper return
against current source. No runtime validator changes are needed for these.

Implemented lexical module/class return summaries with actual parameter
substitution, and adopted positional/keyword/chained helper member propagation.
Added eight independent fragment/live-origin controls. Dynamic labels/mount
context and writer-key stimulus remain separate scopes, unchanged here.

Verification planned before execution: in v12/python, run
`PYTHONPATH=src python3 -m unittest tests.manager.test_boundary_inventory.AdoptedHelperOriginsAreContextual`
to answer whether the actual origins and collision/cycle negative controls
are preserved. If green, run
`PYTHONPATH=src python3 -m unittest tests.manager.test_boundary_inventory.TheDiscoveryProjectionsAreBoundedAndImmutable tests.manager.test_boundary_inventory.EveryReceivingEntryHasOneOwner.test_the_universe_sees_every_persisted_column_that_is_read`.
This is the broader relevant discovery regression and original check8, not
the unrelated whole-suite gate. The diagnosis lacks corrected-source evidence;
these runs close that exact gap. Cumulative planned budget30s; stop and reassess
if it exceeds that budget. Retain output and do not weaken any existing check.

First focused run: one newly added fragment omitted the genuine intermediate
`runtime_lanes.record` read from its expected set; corrected that new witness
to include the actual read, then all eight controls passed (0.474s). Existing
cache/immutability controls passed; original check8 exposed `claim_generation`
after the bare-name shortcut was removed (combined seven checks,3.057s).
The actual path is attempts._claim_of's explicit local import of
offers.claimed_offers_for. Added source-proved relative import/alias resolution
and an independent import witness, rather than restoring a bare-name fallback.
Repeat the focused and declared broader discovery checks against this changed
candidate; the missing column and cache behavior of import summaries are the
new questions. Remains within the original30s cumulative budget.

Final result: nine focused fragment/live-origin tests pass (0.489s), then all
seven broader cache/immutability plus original column checks pass (3.170s).
`git diff --check` is clean. No aggregate assertion, existing refusal stimulus,
runtime validator or shared registry was changed. Original check8 has targeted
passing evidence; this does not discharge the remaining inventory checks.

Retained evidence/before.py matches the measured starting hash, verified
against the read-only HEAD blob before retention. evidence/candidate.py is
SHA-256 `88705883487787340f1b7c07e745b9c57aef7335c6bf1c33af8677d21ed41f82`.
evidence/candidate.patch isolates this Work's change; hashes.txt and
verification.txt retain exact identities, commands, results and earlier reds.
Awaiting independent review. The dynamic-context successor must not edit this
file while this candidate is being assessed.

## 2026-09-08 correction episode — baton.tuner claim116178

Independent review returned P1 local reassignment nontermination and P2
import-alias shadowing. Correction choice pinned in FINDING.md. Verification
question: do both counterexamples now terminate/withhold unrelated origins,
while all prior long-chain/import/adopted/cache witnesses and original check8
remain valid? Budget30s for new+prior focused class followed by the existing
bounded/immutable class and original check8, with a2s child timeout for the
nontermination regression. No whole suite or daemon test scheduled.

Correction candidate SHA256
fdaeb9d086a97061dc3170d04184f8553ec2c782e709a958a7915c2475da7571.
Finite assignment traversal replaces repeated member growth; actual lexical
parameter/local bindings gate both returned helper origins and delegation.
Four additive methods cover2s bounded single/double reassignment, multi-target
assignment, nested-body/12-link join, parameter/local import-alias shadowing,
and local helper shadowing. All24 original classes and prior9 new methods are
AST-identical. Focused13 pass0.610s; existing cache6+original check8 pass2.931s.
Diff check clean. Exact candidate, full/last-review patches, hashes and output
retained in evidence/correction-116178/. Awaiting independent review again;
W116058 remains gated and no aggregate inventory/suite acceptance is claimed.

## 2026-09-08 — baton.tuner claim116239

Read second review fresh and revalidated live candidate identity. P1 branch
origin erasure and P2 nested-scope import leakage are the current correction.
Before execution: verification budget30s cumulative, focused fragment class
then existing bounded/immutable six and original persisted-column check8.
Question: do branch order and nested dead code cease to change actual origins,
while sequential overwrite, bounded reassignment, long chains and immutable
cache witnesses remain valid? No aggregate/daemon suite scheduled.

Initial19 focused witnesses pass0.754s; seven existing/cache/check8 pass3.495s.
Before handoff, local inspection identified statement timing as a remaining
consequence of final-only binding resolution. Added a scoped correction choice
and read-before/after-overwrite controls. Repeat the same focused+broader group
only after this new change; cumulative30s budget still applies.

Correction candidate SHA256
2ea16b185a9c5eac40bb553a932c92d6e317a54ed4db1b90bd3f1346611ae9a5.
Alternative paths join immutable may-origin sets; actual sequential assignments
replace bindings. Per-expression environments preserve statement timing for
returns, members and delegation. Lexical-body collection excludes nested
imports/returns/delegations while preserving known local/module imports.
Nine additive methods cover branch swaps, distinct origins reaching both member
and owner projections, sequential overwrite, zero/body loop alternatives,
nested class/function import and return/delegation isolation, reads before and
after overwrite, expression-specific owner/return resolution and comprehension
producers. All24 original classes and prior13 added methods are AST-identical.

The first context revision exposed14 missing columns through _offers list
comprehension: outer-expression snapshot hid the generator binding. Corrected
Name-specific context lookup and added that independent producer witness;
existing assertion unchanged. Complete intermediate/final result history is in
evidence/correction-116239/verification.txt. Final22 fragment+6 immutable/cache+
original check8:29 tests pass4.932s, cumulative measured test time14.386s <30s.
Diff check clean. Exact candidate/full and last-review patches/hashes retained
beside verification. Awaiting independent assessment; shared-file W116058 stays
gated. No aggregate inventory or ordinary whole-suite acceptance claimed.

## 2026-09-08 — baton.tuner claim116317

Read third review and current dossier; prior exact cases resolved, current P1s
are partial summary freezing and try-handler origin loss. Correction choices
pinned before editing. Verification question: do summary alternatives complete
regardless of declaration order, and do handlers see only reachable protected
states, while finite recursion and statement timing remain intact? Budget30s
cumulative for focused fragment class then six existing immutable/cache checks
and original persisted-column check8. No daemon or aggregate suite scheduled.

Correction candidate SHA256
31a86520c467acfd4685bfca1c00ed8c44fc26058e0d7102a2b8f8e04504b01f.
Dependency-driven summaries resolve every nonrecursive call path before union,
cache by site/relevant ancestor exclusions, and stop recursive re-entry. All
six definition orders of mixed direct/indirect/transitive returns agree; mutual
recursive base returns remain available and recursive member expansion has a2s
bounded witness. No arbitrary pass/depth limit suppresses acyclic chains.

Protected-body expression/raise states feed handlers; explicit block exits
stop later assignments. Else runs after normal completion; finally includes
normal/return and raised handler/else outcomes. Function-level bindings retain
exceptional terminal names (the unchanged lane witness requires held), while
individual expression snapshots preserve actual read timing. Nine added
methods cover the specified return/exception controls and finally-on-handler
raise. All24 original classes and prior22 added methods are AST-identical.

Initial focused30 exposed the missing function-level exceptional held binding;
the correction preserves it without changing any assertion. Focused30 then
pass0.828s; existing7 pass4.125s. After the finally-on-handler-raise control,
final31 fragments+6 cache+original check8:38 pass4.573s. Total measured10.345s
within30s. Full result history, exact candidate/full and last-review patches,
and hashes are retained in evidence/correction-116317/. Diff check clean.
Awaiting independent assessment; W116058 stays gated. No runtime/catalog/probe
edits, daemon run, aggregate inventory or whole-suite acceptance claim.

## 2026-09-08 — baton.tuner claim116389

Read fourth review/current dossier and pin loop/exception correction choices.
Verification question: do nearest-loop exits reach their proper destinations,
and do implicit else/handler failures execute finally and propagate outward
with the reaching bindings? Budget30s cumulative for focused fragment class,
then six existing immutable/cache checks and original persisted-column check8.
Correct only the one new witness explicitly named by review/PLAN; retain all
pre-Work assertions. No aggregate/daemon suite scheduled.

Correction candidate SHA256
cd600e9ad74ee9dc9a3072a120b04e35aebe6ee5ec376832265f965d8c3438b6.
For/while share finite nearest-loop break/continue routing: break reaches after
the loop and bypasses else; exhaustion/continue reach else; nested exits remain
local. Finally updates pending loop bindings or overrides their exits.
Else/handler implicit failures are retained separately from protected-body
states, join finally inputs, and escape to the outer collector after finally.

Six new methods cover both loops, nested conditional break, continue and loop
else, nested-loop ownership, break through finally, implicit else/handler
failures and post-finally outer-handler state. Corrected exactly the new
finally witness named by fourth review/PLAN to include first.identity when the
else assignment fails. AST verification: all24 pre-Work test classes unchanged;
all other prior new methods unchanged. No blanket assertion mutation.

Focused37 pass0.821s; six cache/immutable+original check8 pass4.074s. Total44,
cumulative4.895s <30s; diff check clean. Exact candidate/full and last-review
patches/hashes/output retained in evidence/correction-116389/. Awaiting
independent review; W116058 remains gated. No runtime/catalog/probe edits,
daemon/aggregate suite or broader acceptance claim.

## 2026-09-08 — baton.tuner claim116443

Read fifth review/current dossier and pinned destination-preserving finally
correction. Verification question: do terminal states stay out of break/normal
continuations while finally still sees its real alternatives and overrides
pending exits? Budget30s cumulative for focused class, six immutable/cache
checks and original persisted-column check8. No prior assertions, runtime,
catalog/probe edits or daemon/aggregate runs scheduled.

Correction candidate SHA256
080cc29bd6ce9d4e9f80bd8433d3faa8a4b17db61abf00ff918015933e305dd9.
Finally inputs retain normal, return-expression, raise and nearest-loop
destinations; only matching destinations join. Finally transformations and
actual overrides emit their outcomes to the correct destinations. Consumed
inner-loop exits no longer sit in pending function outcomes. Historical terminal
bindings remain a separate inspection summary. Repeated finally traversal unions
observed expression snapshots while evaluating against the current destination's
bindings; overridden return expressions cannot supply helper summaries.

Five added methods cover break-vs-return, fallthrough-vs-return with both
alternatives observed inside finally, finally return overriding pending breaks
and returns, consumed inner-loop overwrite, and escaping exception vs normal
continuation. All24 pre-Work classes and all37 prior new methods AST-identical.
Focused42 pass1.165s; six cache/immutable+original check8 pass6.872s. Total49,
cumulative8.037s within30s. Diff check clean; exact candidate/full and last-review
patches/hashes/output retained in evidence/correction-116443/.
Awaiting independent review; W116058 remains gated. No prior assertions,
runtime/catalog/probe edits, daemon/aggregate suite or broader acceptance claim.
