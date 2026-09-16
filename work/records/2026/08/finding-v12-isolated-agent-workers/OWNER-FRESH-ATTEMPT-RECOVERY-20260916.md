# Owner ruling: fresh-attempt recovery is the v12 minimum

Confirmed 2026-09-16T04:07:24.167298+00:00 in the interactive prompt. Slawomir agreed to the proposal:
allow fresh-context retries as the supported recovery path and defer production
session reuse unless a concrete v12 workflow depends on it.

## Selected behavior

A failed attempt reports an actionable error; previous execution is positively
stopped or fenced; a new isolated attempt can retry from known inputs with a
fresh identity; result lineage and independent acceptance remain correct.
Preserve legitimate completed effects and do not duplicate them through retry.
Reuse of an existing provider conversation is an optional efficiency feature,
not a minimum v12 release requirement. Repository changes are judged through
their own diff/verifier/review contract, not through session-continuity proof.
This ruling does not automatically relaunch arbitrary failed Jobs or change
retry counts, public timeout semantics or target/import authority.

## Explicit supersession and classification

Supersedes the production-context-reuse requirement in the Sep14 release ruling
and Sep15 usable-v12 sequence, and any instruction that unfinished W177936 must
complete before usable-v12 readiness. It does NOT waive execution isolation,
cleanup/fencing, honest failure, lineage, independently reviewed results or
known work-loss/duplicate-effect/false-success defects.

W177936 is now explicitly deferred optional production session reuse work,
nonblocking for minimum v12. Preserve its Work identity, canonical dossier, all
failed runs, partial candidate bytes and unresolved model/custody findings. Do
not close it satisfying or label restoration qualified. Its five run identities
remain consumed. No live run, fresh identity, private inspection or enabling.

W161234 remains closed satisfying for its accepted bounded deterministic proof;
its historical required-context architecture and evidence are not rewritten.
The v12 readiness assessment must distinguish accepted context-enabled evidence
from evidence that fresh-context recovery is actually supported. A completed
context-enabled trace alone is not proof of that newly selected supported path.
The production context profile remains disabled/refused until separately
qualified. Model-use ambiguity in this experiment remains recorded; if it also
affects the selected fresh-execution surface, report that concrete dependency
rather than silently transferring or waiving a release gate.

## Immediate coordination and bounded readiness assessment

Claude currently holds W177936. Explicitly notify the handler of this changed
owner selection. Stop additional implementation at a safe boundary, terminate
and clean up any owned ongoing verification, preserve/describe any partial
changes and current path ownership, update its dossier for this ruling and
release Work to ops for deferral disposition. No forced release or rerouting
of an active claim by baton.prompt. Unreviewed partial bytes must not be treated
as accepted product code or silently imported.

Use existing W2 for a bounded reviewer evidence assessment of minimum readiness:
1. Reuse accepted fresh-attempt/failed-attempt/cleanup/lineage/result evidence,
   including relevant W161230/W161234/W63255 evidence and monitor completion.
   Establish how the actually selected configuration runs with context disabled
   and fresh attempts. Verify targeted configuration/source only where needed.
2. Identify any concrete missing requirement in that path with exact evidence,
   or recommend usable-v12 readiness. Do not reopen accepted suites, invent a
   general certification gate or assume readiness solely from closed blockers.
3. Incorporate the pending DEPLOYMENT-PROPOSED-182748.md publication into a
   concrete documentation recommendation consistent with optional reuse; product
   documentation editing remains a subsequent bounded publication action.
4. Return ops with the finite conclusion and exact remaining action, if any.
   This is read/static assessment and dossier updates only: no tests, providers,
   actual engines, product edits, broad audit or new architecture project.

Formal W2 umbrella closure remains distinct from minimum readiness; historical
open children are preserved. V11 remains the coordination authority. This ruling
is a scope change, not evidence that readiness or deferral ledger mutation has
already occurred.
