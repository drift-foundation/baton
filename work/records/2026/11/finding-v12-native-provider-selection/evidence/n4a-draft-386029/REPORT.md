# Disjoint N4a draft — E386029

Author: baton.codxpc, impl. 2026-11-24. Selection E386028 and owner instruction; independent preparation assessment M386027. Base: `317351e73c92749e201f536ba115c9fdf213077d`. This is the completed disjoint draft, not joined acceptance, an import selection or native qualification.

## Candidate

Seven new paths are retained under `candidate/` and in `candidate.tar.gz`. Exact path/hash/size/mode list: `candidate-manifest.json`, SHA256 `dac8d6bd2b5541a3779c255725fe74101ad323bbdfd084c464293684635fd00c`.

- `v12/worker/codex_agent.py`: exact inventory-derived exec argv and explicit model; R1 rejects empty/whitespace prompts, leading hyphens and exact resume/fork/review/help before home preparation or invocation. NUL/non-string prompts also refuse. Prompts remain one literal operand. Fresh launch, implementation-only context-label and exact-build guards are present on the subclass.
- `v12/worker/codex_entry.py`: existing production validation and supervisor reused through their existing injection seams; no shared entry edit needed.
- `v12/worker/Dockerfile.codex`: source-only exact npm version pin, current worker dependencies and verifier layout, nonroot user and Codex entry. No image built.
- `v12/python/tests/manager/test_codex_draft.py` plus three files under `fixtures/codex-0.169.0/`: dedicated offline tests and verbatim retained N3 exec-help/version bytes with provenance.

No existing base file changed: 1,144 verified against the pinned archive. No protected product file imported. Ownership confirmation M386022/M386023 and review M386027 govern; latest D implementation notice M386030 consumed and acknowledged M386032. Shared edits remain D-first. K is independently implementing D; this packet does not modify or take over its paths.

## Focused evidence

Affected future logical group: **manager-pure**. Per the explicit M386027/owner exception, this draft module is unregistered and the run is **unaccounted**. Do not import the test module into the main tree before the serialized registry join.

`just test-one tests.manager.test_codex_draft` from isolated `repo/v12`, prepared interpreter `/home/sl/.local/state/baton-v12-venv/bin/python`: **14 collected, 14 executed, 14 passed; zero failure/error/skip**, exit 0. Measured command time 0.445947458 seconds; unittest reports 0.002 seconds. Raw stdout/stderr, source-before/after header, prepared-interpreter collection and per-ID draft summary are alongside this report. A log-reconciliation script initially duplicated method suffixes; its assertion failed, the parser was corrected, and original results reconciled without changing source or rerunning tests.

| Behavior | Evidence and limit |
| --- | --- |
| Inventory/argv/R1 | Retained exact-build help/version hashes; option/subcommand checks; invalid prompt refuses before home/runner; valid operand remains literal |
| Roles/fresh/build | Subclass refusal and simulated post-validation contracts only; no host composition proof |
| Entry | Real invalid document constructs no adapter; simulated accepted validation proves constructor order; existing supervisor delegation checked, no new process lifecycle implementation |
| Terminal boundary | Exit 0/nonzero/signal plus empty/malformed/synthetic shapes all remain unclassified; no positive turn fixture or parser |
| Recipe | Source/copy existence, exact pin, verifier/ENV preservation and entry/user checks; no build/runtime evidence |

## Join gates and next milestone

Next bounded milestone: independent **draft assessment** of these bytes. Accounted acceptance and integration follow D's accepted/imported human checkpoint. At that join, N4a owns the version decoder and delivered credential-slot hooks, host pool/single_worker fresh/role/slot guards, policy entrypoint and qualified realization, registry and documentation, as allocated in M386027 J2. Keep legacy `_context_home` byte-identical. The role list comes from D's `context_label.roles`.

The current shared version decoder cannot parse `codex-cli 0.169.0`; no decoder correction is claimed here. The current policy has no Codex realization; native composition stays refused. `_prepared_home` deliberately refuses before any inherited Claude slot can be used, and session-root lookup refuses an unevidenced layout. These are draft join fences, not finished home integration. D label/package/ending behavior has not been tested here.

J1 remains: selected evidence must establish the exact-build credential path before a Codex realization can land. No null/guessed credential path or auto-loading claim. N4b JSONL parsing/participation and successful turn attribution remain gated on exact-build turn evidence. No credentials, provider calls, engine operations, builds, resume, full suite or protected Git mutation occurred.

## Recovery and disposition

`START.json`, candidate bytes/archive/manifest, raw focused evidence, `boundary-check.json` and DESIGN context are durable dossier artifacts. Isolated scratch `work/scratch/w385830-n4a-386029/` is retained; no cleanup deletion needed, no container/process was launched by the adapter tests. The test command exited normally. Recovery requires the pinned base plus this candidate; the scratch copy is not the backup. Human checkpoint/backup remains pending; suggested message after review: `Retain disjoint N4a Codex adapter draft and focused evidence`. This is not a major accepted product milestone.

Read positions: parent M386031, D M386030 (ack M386032), canonical E386029. Owning FINDING/PLAN/PROGRESS retain continuation and handoff disposition.
