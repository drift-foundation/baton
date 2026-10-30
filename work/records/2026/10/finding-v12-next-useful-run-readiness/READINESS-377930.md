# W376804 — next documentation run readiness

Prepared by baton.tuner under claim E377930, 2026-10-28. **Not ready for
installation or live execution.** The smallest useful next outcome is a qualified
host installation with safe prerequisite/unwind behavior and an explicit supported
failure-control path. There is no technical reason in the measured source closure
to rebuild the existing worker image. Do not spend another live invocation to
discover those installation/control gaps.

This successor corrects READINESS-376826 sections 2, 3, 6 and 7; the original is
preserved as history. It addresses review-2026-10-28T20-10-19Z.md and owner
clarification M377743. It is a concrete unsupported-operation disposition, **not
a completed runnable packet or a claim of routine-startup acceptance**. No new
implementation, qualification framework or launcher is proposed here.

## Measured source and artifact boundary

CHECK-377930.json records 1,078 committed v12 file SHA256s, all ten image build
input comparisons, eight inert parser checks, the task digest and measured time.
The source was exported from Git objects without changing Git state or importing
dirty checkout modules. Retained export: `/tmp/w376804-8876bf95-6mw5zvec`.
It contains ordinary files, not a transport-ready Git repository. The export is
reproducible with check-377930.py; each invocation creates and retains a unique
directory. That helper is development evidence, never a per-Job operating step.

| Selection | Finding and next action |
| --- | --- |
| Source | Confirmed `8876bf950ff1f8ab8767ce9786df268cc9d767c6`; HEAD was still this commit on this claim. Keep explicit source selection even if HEAD advances. |
| Worker | Reuse candidate image `sha256:47e733834bb690fd4601e102f81e527a08b6ffe55da8b8cb345f45edfcb1517e`. All ten BUILD-INPUTS hashes from W325695 preparation-376414 equal the selected source, including Dockerfile, worker, Claude adapter, marker, source profiles and verification context. No rebuild is indicated by these bytes. |
| Host/worker compatibility | The selected host's OCI/source-boundary code retains the ef703336 topology contract. The 8876bf95 single_worker diff extracts the same exchange adoption into `exchange_delivery` and adds settlement access; it does not change the worker wire contract. Its control schema changes 18 to 19, so use fresh stores, never migrate a retained instance. Source compatibility is supported; installed pair qualification is still absent. |
| Kernel proof | Now accepted: W325695 review-2026-10-28T21-48-41Z.md and preparation-377003/ENGINE-RECEIPT/state.json, SHA256 `992a374394a43d9ced6e7edc10d2ce97f1e3c2e25ae97d1a97fac3de3be29123`. Reuse exact-image descendant/mount/ENOSPC/owned-cleanup evidence. It proves neither workload fit nor provider/authentication nor installed host integration. No repeat requested. |
| Historical failed probe | Original stdout/stderr were not retained. Its cause is unknown. Later reproduced classifier failure and the successful successor do not reconstruct those missing observations. |
| Host package | No candidate-specific qualified bundle is established here. Old package `1da85eed` is not the observation fix. Minimum artifact need is a host bundle containing the fixed observer and settlement command, plus accepted installer behavior for the chosen install path. A worker rebuild is not a substitute. |
| Shared outputs | Reuse W370688 successor-371277 inventory `00add5d1b3fba1ca655abbdff9640f4a20134bd05cb00803c9acb5e1b55bec38`, retaining f36bcd75 provenance. Its proposal/findings/logs union is optional across roles; actual role-required outputs still gate result consumption. Simulated provider/Git and intentionally invalid bundle do not qualify actual transport. |
| Settlement | Reuse W375446 review-2026-10-28T19-53-19Z.md: 37 independently passing joined deterministic checks, real disposable owners, simulated OCI and frozen identity. No native package, real engine effects or old-instance recovery claim follows. |

## Useful task, preserved criteria

Create `v12/TEMPLATE-JOBS.md`, a reusable guide to ordinary template creation and
observation. TASK-377930.json preserves the earlier task instructions and entire
mechanical verification argv byte-for-byte as JSON values; only declared_base
and task_id change. SHA256:
`ae6e3187929bf89ff66796cde989622df2363e6b7ac023caf604f41df9201180`.
Proposed task `template-job-guide-w376804`, Job `template-guide-w376804`, submission
`template-guide-w376804-1`; template explicitly
`baton.v12.job-template.implementation-review/1`; source `installed` must resolve
to the selected immutable Git base. Scope is only `v12/TEMPLATE-JOBS.md`; no
product/test edits or imposed heading order.

The five original criteria are retained verbatim in CHECK-377930.json and in
COMMANDS-377930.md's create example. They require supported input-only creation,
truthful source/deployment/limit distinctions, read-only monitoring, separation
of execution/review/acceptance/integration, and semantic checking against owners.
The mechanical checker imports the actual parser and requires a create example;
it is not the semantic reviewer and supplies no owner receipt.

Comparison at the selected commit:

* README is primarily the historical disposable PoC and authority overview.
* QUICKSTART is explicitly instance 4 and its older installed command inventory;
  its settlement addition must not be read as evidence of installation there.
* STACK explains installation, process lifecycle, storage and bootstrap inputs.
* NEXT-RUN describes a different managed candidate, not an accepted generic
  template creation guide.
* TEMPLATE-JOBS.md is absent. The new guide fills the ordinary-create gap without
  rewriting historical instance facts. It must state that /1 direct creation
  requires an idle manager at this source, and distinguish that limitation from
  the required create-while-serving behavior. Do not pretend `/2` is installed.

Independent review must inspect every command's meaning and actual guide bytes,
not just accept headings or a parser pass. Real Git proposal transport and actual
role delivery remain execution acceptance, not satisfied by this preparation.

## Installation and routine-operation gaps

Proposed new destination is
`/home/sl/baton-instances/useful-template-job-w376804`; its availability and disk
properties were not inspected. It is neither created nor reserved. All mutable
roots must derive from this selector, outside source and retained instances, with
no aliases/overlap and supported private storage/access checks. A fresh name does
not establish these facts.

At **selected committed source**, `tools/bootstrap.py::_remove_if_still_ours`
compares the root inode then calls `shutil.rmtree`. Foreign additions beneath an
unchanged root can therefore be removed on install failure. `install` also uses
`copytree`; root identity does not prove ownership of every copied child or every
mid-copy effect. There is no selected safe-path proof that contains these hazards.
Do not recommend bootstrap at this commit merely with a fresh destination or
invent a manual precreation/permission/cleanup workaround.

Existing owners already have the concrete corrections:

| Gap | Existing delivery owner and finite result needed |
| --- | --- |
| Creation provenance, prerequisite access and owned install unwind | W376246 under W375516; W376955 supplies creation identity and W376956 runtime-copy/foreign-preserving unwind. Consume independently accepted connected install success/failure evidence, then bind those exact host bytes. |
| Read-only prerequisite/store validation through instance commands | W376254, joined through W375516. Existing source/fixture checks are not proof the future package serves them. |
| Create while serving | W375517 admission owner and W375518 commands under W371075. Current `creation.create_template_job` takes the manager instance guard; a serving manager owns it. Routine stop/create/start is not accepted as the permanent path. |
| Whole-path startup | W375519 under W371075: measure receipt of task/inputs through attributable substantive work, including preparation, within 60 seconds. Parser/runtime tests and dispatch timestamps alone do not prove it. |
| Role pair | W371296 owns actual adapter qualification. Canonical detail snapshot377944 shows W371295 and W376586 dependencies. No `/2` grant is available from that Work; reuse a separately reviewed /1 qualification only if it establishes the actual selected pair/task/output contract. Do not reroute or bypass those owners. |

This table is coordination evidence for baton.bug/W321608 to consume; it installs
no dependency edges and makes no new allocation. Queue/startup delivery is a
routine-startup acceptance requirement, not automatically a gate on a separately
selected one-off /1 diagnostic. The concrete installer defect and missing
failure-control procedure do gate the fresh-install/run proposed here. Typed
diagnostic polish, reuse completion, broad certification and authority cutover
are not blanket gates on this learning question.

## Proposed one-time deployment selections

Use two distinct workers/principals: `impl-w376804` /
`baton.claude-w376804` and `review-w376804` / `baton.reviewer-w376804`, with distinct
private writable roots and no concurrent writer/reviewer attachment. These are
proposals, not registered identities. Independent technical review remains
baton.bug in v11; owner receipts remain separate.

Use the supported docker-single-worker adapter and explicit fresh-context /1
roles, with the qualified image above. The old fixture's adapter
`sha256:5f2ef38f05ed7a9aecd11dd7e23e9cfbe1f0243fe27bd2c9aa1b004580fcdef1`
and profile `sha256:93fdea4ac36c54656a7534b72ba0ea7d796b5294cdb2fd7de4056d52709675be`
are **historical references**, not qualified pins for this new image/topology.
The current matched deployment/profile/adapter digests are unknown pending
one-time qualification and publication; do not copy the old `/4` fixture and
replace its image string. No synthetic grant or bootstrap document is supplied.

Credential selection stays logical: slot `claude`, provider `operator-file`,
reference `w202663-development`, subject to one-time deployment validation.
No credential file was opened. Fresh authority UUID must be minted and read back
by the installer; the parser-only zero UUID in CHECK is never an operational
operand. The task, independent principals, matching profile/adapter, exact package
and image must be reported by the installed selection before dispatch.

## Limits and failure handling

Propose provider 3600s and verification 900s **per invocation**, zero automatic
correction and zero automatic retry. One implementation plus one review is the
maximum selected pair. A changes-requested verdict ends this selection and
retains the proposal for disposition. The current CLI exposes no correction-count
operand; do not claim an invented flag enforces that bound.

Proposed supervision envelope: 60s startup target; 4,800s per stage including
300s cessation/settlement reserve; 9,960s total (two stages, 60s startup and 300s
final accounting). These are proposed ceilings, not measured timings or installed
enforcement. A per-command verification limit is not an aggregate verification
limit. Before selection, the existing runtime controller must demonstrably enforce
the stage/overall ceilings, compatible token duration and renewal policy; an
unwired timer or these numbers in prose is not enforcement. If that path cannot
represent them, return the precise capability gap instead of a bespoke supervisor.

1. Observe using status, monitor, Job view, attempt diagnostics and retained logs
   in COMMANDS-377930.md. Record timestamp/freshness, exact attempt, assignment
   generation, launch operation, full container ID, token generation and retained
   output location. Snapshot time is not worker contact.
2. On failure/deadline/cancellation request, stop admitting successors and use the
   selected manager's exact-runtime stop/reconciliation path. **There is no
   installed assignment-cancel verb at this source.** QUICKSTART names
   `Authority.cancel` as an owner API act; it is not a pasteable installed command.
   This packet supplies no raw SQL, guessed Docker name, or alternate API script.
   The missing installed operational cancellation procedure must be supplied by
   W321608's existing runtime/recovery owner before live selection.
3. `stop --instance ...` stops owned supervisors only. Do not use it to infer
   container cessation or disable overdue enforcement while a runtime is still
   unresolved. Stop supervisors for offline settlement only after exact confined
   runtime cessation/launch accounting, or under a separately selected emergency
   action that explicitly preserves the unresolved hold.
4. Then preview and settle the exact failed stopped episode through the installed
   commands. Preview may inspect the engine and is outside this claim's execution
   authority. Save its exact request object, inspect bindings, and reuse that
   unchanged request after reply loss. Settlement rechecks and may refuse;
   it neither cancels a running attempt nor disposes Authority Work nor deletes
   anything. Unknown create/start/runtime/writer/effect state stays held.
5. Reserve exhaustion means an unresolved, retained failure, not successful
   cleanup. Preserve selector, deployment, package identity, stores, task, request,
   logs, status and private outputs. Slawomir owns retained-instance disposition,
   backup and eventual deletion; runtime owner owes cessation/settlement evidence.
   No historical instance cleanup, retry or deletion is selected here.

## Next disposition

Return to baton.bug with this concrete unsupported fresh-install/control operation,
the finished task and measured compatibility/command evidence. Request consumption
by the existing W371075 and recovery owners through W321608; no competing product
chain. The next build is host-only after exact safe installer bytes are selected;
COMMANDS supplies the supported build form and its binding requirement. Installing
8876bf95 now would knowingly retain the defect. A full new packet with fabricated
profile digests would conceal it rather than complete preparation.

Human checkpoint after accepted preparation remains pending:
`Prepare next bounded useful documentation checkpoint`. No commit is claimed.
Only this dossier's new files and attributable PROGRESS append were changed.

Operational read findings: two guessed locators did not exist:
`finding-v12-stopped-settlement-joined/PLAN.md` and
`finding-v12-template-adapter-qualification/PLAN.md`. Resolved by repository search
and canonical W371296 detail to `finding-v12-stopped-settlement-proof` and
`finding-v12-role-contract-qualification`; both required records were then read.
No required policy or bound dossier remains unreadable.
