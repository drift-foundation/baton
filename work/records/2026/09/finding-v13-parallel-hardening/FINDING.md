# V13 hardening through v12 parallel development

Ledger Work: W165786. Recorded by baton.prompt, 2026-09-14 UTC.

## Confirmed objective and release boundary

Slawomir selected the strategy of delivering v12's reliable parallel development
Jobs and then using that concurrency to expedite v13 hardening. A lightweight
read-only Job monitor remains required in v12. The owner subsequently requested
a v13 umbrella for the existing Jobs classified as v13.

The canonical release ruling is
`baton:work/records/2026/08/finding-v12-isolated-agent-workers/FINDING.md`,
section "V12 parallel delivery enables v13 hardening". It preserves v12 execution
correctness, isolation, recovery, context reuse and reviewed result collection.
Broader stress/race matrices, performance, advanced scheduling/shared capacity,
distributed execution and richer TUI behavior belong to v13. Concrete defects
that invalidate v12's required correctness do not become optional by labelling
them hardening.

## Existing Work moves by relationship, not by duplication

This umbrella organizes v13 deliverables in the existing v11 authority now.
Existing Work IDs, canonical dossier locations, findings, accepted evidence and
history remain intact. Containment represents release membership; dependencies
represent actual required inputs. A historical V12 title is not a release gate.
Do not move dossier directories, recreate existing Work or bulk-migrate the store.

The owner specifically excluded W103950, expanded stage composition hardening,
from v12 delivery. It is the first selected v13 member. At creation it is standalone
and blocks no consumer; its containment change remains to be applied by an
authorized route handler. Preserve its own children and assess any necessary
v12 correctness capability independently without importing the expanded matrix.

W165782 owns classification of the remaining existing queue and exact proposed
containment/dependency amendments. Each proposed member must name its concrete
outcome, reason for v13 placement, true prerequisites and retained evidence.
Changing a parent does not make a Job ready or discharge a gate. Do not move
live claimed Work underneath its handler or close uncompleted requirements.

## Execution transition

When v12 meets its readiness criterion, select independent v13 tasks and execute
them through v12 with preserved input/result identity and acceptance criteria.
Keep v11 as the current coordination authority while preparing this transition.
No synchronization service, automatic authority cutover, implementation assignment,
test/model/runtime execution or new verification allowance is created here.

## Operational limitation — existing Work cannot be reparented by this v11 CLI

Observed during setup: the deployed 0650c61 CLI exposes parent= on create, but
its complete --help surface exposes no existing-Work reparent/attach operation.
Both --help attach and --help fold report unknown command. This is an interface
limitation, not a handler-permission refusal for an existing reparent command.
The earlier setup assumption that an authorized handler could simply apply the
W103950 containment change is superseded by this observation.

Stated stopgap after recording this limitation: PLAN's explicit release-member
table records W103950 as selected for v13 while leaving its actual ledger
containment unchanged. It is not a claim that W165786 contains it in the graph.
W165782 must report which proposed moves the deployed interface can express and
which cannot; preserve Work IDs and never repair the store directly. This does
not add a v11 reparenting feature to the v12 critical path. Future supported
organization/transition can reconcile graph membership with the recorded release
classification without rewriting the original evidence.

## Owner approval — 2026-09-14

Slawomir explicitly approved the created W165786 umbrella, W103950's recorded
v13 membership and the stated release-table stopgap after being informed that
the deployed v11 CLI cannot reparent existing Work. Preserve existing Work IDs,
canonical dossiers and actual graph relationships. W165782 continues the queue
classification under that approved boundary. This approval does not introduce
a v11 reparenting feature, duplicate the backlog, or start v13 execution before
v12 readiness. Recorded by baton.prompt from the interactive "I approve".

## 2026-09-14T09:04:44Z — park until v12 readiness

Owner accepted the three-Work disposition with "lets do it". Keep W165786 as
the approved v13 umbrella and park it until v12 is ready. W165782 proceeds now
with selected release classification, unresolved current-consumer triage and
minimum-viewer commissioning, including serial updates to the membership table.
The approved table remains a documentary stopgap, not canonical containment.
No v13 product implementation is selected now. Route W165786 briefly to the
managed reviewer solely to perform the authorized parking transition; the prompt
does not claim Work or impersonate the operator. This supersedes leaving the
umbrella queued as though there were immediate campaign execution to perform.
