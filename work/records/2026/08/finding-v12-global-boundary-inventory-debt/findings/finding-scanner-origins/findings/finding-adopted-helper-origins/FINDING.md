# Adopted and identity-helper origins

Work W116051. Parent scanner W116031, inventory W48697. The owner-approved
B1 helper scope in the retained W115824 review is split by independent result.

Change only v12/python/tests/manager/test_boundary_inventory.py:
_through_helpers must preserve adopted read-site/table member origins through
positional, keyword and chained helper calls; _source/_returned_origins must
substitute the actual origin into identity returns and resolve module/class
lexical helper identity. Add independent positive/negative fragments and real
interrogation/lane witnesses. Do not modify runtime validators, catalog/probes,
completeness/equality assertions, flat column scan or source ASTs.
Dynamic getattr/provider/label context remains the sibling's explicit scope.

## 2026-09-08 independent review: changes requested

Confirmed on retained candidate SHA-256
88705883487787340f1b7c07e745b9c57aef7335c6bf1c33af8677d21ed41f82,
identical to the live scanner at review. Review
review-2026-09-08T04-17-45Z.md and evidence/review-116112.py plus
evidence/review-116112.json retain the reproductions and baseline comparison.

1. Contextual identity-return substitution makes `_origins` repeatedly append
   the returned member when a parameter is reassigned from that helper. A finite
   source fragment times out after 2s; the retained baseline completes in 0.191s.
   The fixed-point map changes values indefinitely despite a finite name set.
2. `_helper_site` resolves a module import even when the calling function has a
   parameter with that alias. The scanner falsely attributes the parameter's
   return to an unrelated producer SQL read, violating the lexical negative
   control promised by this Work.

Proposed repair stays in the existing helper/additive-witness scope. Preserve
valid chained origins, immutable projections, every existing assertion and the
unshadowed import positive control. This is not a claim that current repository
discovery already hangs: the nontermination is reproduced on the explicit finite
fragment. Sibling dynamic-provider work remains gated on this slice's acceptance.

## 2026-09-08 correction choice — claim116178

Replace the incorrect monotone-name claim in `_origins`: evaluate finite
assignment syntax in lexical execution order, visiting nested control-flow
bodies before their following statements and each assignment once. Helper-return
discovery retains its finite inter-function closure; local reassignment never
replays a member append against its own last result. Record lexical parameters
and local bindings before helper resolution so a shadowed bare name or module
alias cannot borrow a return/delegation summary. Preserve unshadowed imports and
self-method resolution. Add bounded reassignment, nested-body chain and
parameter/local shadowing witnesses within this slice's existing authority.

## 2026-09-08 second independent review — claim116214

Review review-2026-09-08T04-28-57Z.md binds corrected candidate
fdaeb9d086a97061dc3170d04184f8553ec2c782e709a958a7915c2475da7571.
Confirmed: the original exact reassignment-timeout and parameter-shadowing
reproductions now pass. The choice above to visit alternative branches against
one sequential environment is superseded: it drops an adopted SQL origin when
the other arm assigns None, and swapping equivalent arms changes discovery.
Finite traversal must preserve alternative-path origins and distinguish true
sequential overwrites. Also confirmed: nested-function imports leak into parent
helper lookup through imports_at(ast.walk(node)), borrowing an unrelated SQL
origin. That lexical defect exists in both candidates of this Work.

Retained evidence/review-116214.py and JSON include both counterexamples and
the resolved original cases. Proposed corrections and additive witnesses stay
inside the existing helper scope. No prior assertions or runtime files need
changes. Current disposition remains changes requested; W116058 stays gated.

## 2026-09-08 correction choice — claim116239

Implement finite alternative-path joins as immutable sets of possible origin
strings (singletons retain the existing string representation). Propagate each
possibility through expression/member resolution and owner/entry projection;
never select one SQL origin based on branch order. Assignments still replace
the prior binding, so an actual sequential None overwrite removes the origin.
An if joins independently evaluated arms; loops join zero/one syntactic body
passes and do not repeatedly grow member suffixes. No claim of concrete loop
iteration execution follows from this static may-origin analysis.

Use one lexical-body walker for imports, returns and helper delegation so a
nested function/class/lambda body cannot supply its parent's return or alias.
Retain function-local and module-level positive import controls, and add nested
import/return negatives plus branch-order, distinct-origin, sequential overwrite
and loop controls. This supersedes the prior single-environment alternative-arm
choice; existing record history remains intact.

Statement-timing clarification under the same claim: final-name bindings alone
can erase an earlier member read when a later assignment overwrites that name.
Retain per-expression environment snapshots in the finite traversal and use
them for return, member, owner and delegation resolution. They are local
analysis values, not mutations of shared ASTs or cached projection results.
Add independent read-before/after-overwrite and return-before-overwrite controls.

## 2026-09-08 third independent review — claim116291

Review review-2026-09-08T04-41-45Z.md binds candidate
2ea16b185a9c5eac40bb553a932c92d6e317a54ed4db1b90bd3f1346611ae9a5.
Confirmed: all four earlier exact counterexamples are corrected, including
equivalent branch orders and nested-import isolation. Two remaining confirmed
origin losses block acceptance: write-once helper summaries discard additional
returns resolved on later passes, and the new try-handler analysis discards
bindings assigned inside the protected body before an exception.

The current interpretation of handlers as alternatives starting exclusively
before the try statement is superseded by this counterexample. Proposed repair
must account for exceptional-path states with finite traversal and retain actual
statement timing. Summary completion must admit later-resolved alternatives
while retaining the existing recursion/member-growth boundedness requirement.
Retained evidence/review-116291.py and JSON include prior/new comparisons and
original-case replays. This remains helper/additive-witness work; no runtime or
original assertion changes. W116058 remains gated pending independent acceptance.

## 2026-09-08 correction choice — claim116317

Replace write-once iterative partial summaries with dependency-driven complete
summaries over finite simple lexical call paths. Resolve a referenced helper
before combining all returns; memoize by site and relevant ancestor exclusions.
A recursive re-entry ends that path, while independent direct/base returns and
other nonrecursive paths remain available. Thus declaration order and arbitrary
pass counts cannot suppress a later-resolved alternative or a valid long chain.
This supersedes the prior setdefault summary-freezing choice.

Handlers begin from possible exceptional exits of the protected body, including
successful preceding assignments. Explicit return/raise stops that block before
later assignments; unreachable expressions cannot supply a summary/delegation.
Else runs on normal try completion; finally observes the joined outcomes.
Retain expression snapshots and true overwrite behavior. Add direct/indirect
order/transitive controls, recursive base/member controls, handler assignment,
early raise/late assignment, else/finally and overwrite controls. All remain
within this Work's helper/additive-witness scope; no runtime or catalog edits.

## 2026-09-08 fourth independent review — claim116366

Review review-2026-09-08T04-54-22Z.md binds candidate
31a86520c467acfd4685bfca1c00ed8c44fc26058e0d7102a2b8f8e04504b01f.
All previous exact counterexamples pass. Confirmed remaining losses: while
break states are discarded before the following statement, and implicit
exceptions in else/handlers do not contribute their pre-assignment state to
finally. Evidence/review-116366.py and JSON retain prior/current comparisons.

Clarification superseding the preceding flow choice where incomplete: loop
break outcomes reach the statement after the loop, and finally must observe
implicit expression failures as well as explicit raises. Exceptions from else
and handlers do not enter this try's handlers but still run its finally.
The newly added, unaccepted test_try_else_and_finally_keep_only_the_reaching_bindings
witness currently expects only the second origin; this omits the first origin
when the else assignment fails and must be corrected within this Work's new
witness contribution. No pre-Work assertions or runtime changes are proposed.
Changes remain requested and W116058 remains gated.

## 2026-09-08 correction choice — claim116389

Use one finite loop-outcome model for for/while: record break/continue against
the nearest loop; break bypasses else and reaches the following statement,
while zero/exhaustion/continue paths reach else. Nested-loop exits never belong
to an outer loop. Finally transforms pending loop exits before they arrive.
This supersedes treating loop stops as discarded function alternatives.

Capture else/handler expression failures in a separate collector. Their
pre-assignment states join finally inputs but never enter the same handlers.
Propagate escaping states to an outer collector after finally, including its
writes, rather than publishing stale pre-finally bindings. Retain explicit
raises and overwrite controls. The exact newly contributed finally witness
named by review116366 is authorized for correction to first+second origins;
no pre-Work assertion change is authorized or needed.

## 2026-09-08 fifth independent review — claim116419

Review review-2026-09-08T05-02-43Z.md binds candidate
cd600e9ad74ee9dc9a3072a120b04e35aebe6ee5ec376832265f965d8c3438b6.
All previous exact counterexamples pass. Confirmed remaining defect: finally
joins terminal and continuing states, then copies that union into pending break
or fallthrough destinations. A row present only on a returning path is falsely
attributed to a later member read that path cannot reach. Two independent
loop/non-loop fragments are in evidence/review-116419.py and JSON.

The preceding finally transformation choice is clarified/superseded where it
copies one joined state to every pending exit: state must remain associated
with its pending destination through finally, including overrides. Only states
reaching the same destination may be joined afterward. Expressions inside
finally can still observe the alternatives that actually execute there. This
is one bounded correction to the current helper traversal, with additive
negative controls; pre-Work assertions and the corrected new finally witness
remain intact. Acceptance is still pending and W116058 remains gated.

## 2026-09-08 correction choice — claim116443

Carry explicit continuation, return-expression, escaping-exception and nearest-
loop destinations with their pending states through finally. Join only matching
destinations before applying finally; emit each surviving/overridden outcome to
its destination afterward. Keep consumed inner-loop exits out of pending
function outcomes. Preserve separate historical terminal bindings for inventory
inspection without using them as control-flow inputs.

Finally expressions may execute for several destinations: union their observed
snapshots for projection, but evaluate each traversal against its current
bindings. Active return expressions, not returns overridden by finally, supply
helper summaries. This supersedes copying a joined finally environment to all
destinations. Add the two review negatives plus finally-observation/override,
consumed-inner-loop and exception-versus-continuation controls. No prior test
assertion changes are scheduled for this correction.

## 2026-09-08 independent acceptance — claim116481

Accept candidate 080cc29bd6ce9d4e9f80bd8433d3faa8a4b17db61abf00ff918015933e305dd9
under review-2026-09-08T05-11-49Z.md. This supersedes the changes-requested
disposition, preserving all earlier observations and correction history.
Independent evidence/review-116481.py and JSON assert13 retained projection
cases plus finite reassignment; all pass in0.320s. All24 pre-Work classes remain
unchanged. Author49 focused/cache/original-check8 cases pass within budget.

The bounded helper result is accepted, including destination-specific finally
transformation, complete dependency summaries, actual adopted origin propagation
and lexical isolation. W116051 can close satisfying and release W116058 for its
separate shared-file claim. Parent scanner/inventory work and W115981's final
whole-suite gate remain open; no broader green result is implied. The review
records the current size assessment and authorizes no further undivided round.
