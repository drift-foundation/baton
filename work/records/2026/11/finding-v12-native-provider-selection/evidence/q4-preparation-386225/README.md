# Consolidated next-step packet after Q2 — q4-preparation-386225

Prepared 2026-11-25 by K (`baton.prompt`, interactive copilot, no claim) on owner request after M386225. Coordination: T385830 seq 386226.
Source checkpoint `b5abf7983fb07eb3a8268f2d4559a04de9c0f1bd` (still HEAD). No product path, DESIGN or protected Git edit. No engine, build, credential or provider operation. Private roots under `/var/tmp/baton-codex-*` were not opened.

| Part | File | State |
| --- | --- | --- |
| 1. Launcher completion detection | `q2-launcher/`, `checks/` | Corrected and proved deterministically. |
| 2. Claude gates against existing selections | `RECONCILIATION.md` | Done. Four owner choices are genuinely open. |
| 3. Path to Codex implementation → Claude review | `PATH.md` | Two execution selections. Commands are concrete where today's facts allow; see "what is not exercised". |
| Owner decisions, all together | `DECISIONS.md` | Four choices plus two execution selections. |

## Part 1 — completion detection

- Cause, reproduced without the private root: the manager settles the stage (`waiting` → `completed`) and clears the transient exchange between two polls. The 386221 loop only looked at the exchange (`checks/repro-386221-loop.json`: 13 polls, never a terminal, edit verified).
- Correction: `q2-launcher/observe.py`, used by `q2-launcher/owner-run.py`. Capture now ends on either form:
  - **exchange** — the transient exchange is answered or faulted with a terminal (unchanged behaviour);
  - **custody** — the stage is `completed` and the durable records bind to the watched attempt.
- Identity checks for the custody form: stage id, attempt id, current episode's attempt, Work and Authority of the runtime assignment, settled runtime, a `completed` frozen result for that attempt in the control store, a readable content-addressed result manifest recording a present proposal, and Job-status artifacts equal to the control store's (id, bytes, digest) and located inside that attempt's custody. A file artifact is re-hashed; the proposal is a sealed tree and is located, not re-hashed (the edit's bytes are still verified by `collect.py` after cessation).
- A completed stage that fails any of these **refuses**: capture fails and stays held. It is neither waited on nor accepted. Elapsed time and directory presence decide nothing.
- Result fields added: `completion_observation` (`exchange` / `custody` / null) and `container_inspected`. Acceptance stays `held-for-private-evidence-review`; `native_job_success` stays false.
- One related change: the container is no longer inspected once the stage is completed (it is already destroyed); the manager's launched-image receipt remains the image binding.
- Preserved: `../q2-execution-386221/RESULT.json` (`fee25c75…`, the failed launcher result) and the whole `../q2-correction-386221/` packet are unchanged. This launcher is a successor with its own ids (`q2-386225`, payload `4ee53fd4463979474b134a776cb5a9bb29ea701710fc755ac188d299c2134b6f`). No Q2 rerun is proposed.

| Check (`checks/`) | Result |
| --- | --- |
| `check_observe.py` | 30 cases: 7 with no observation (3 keep waiting, 4 ended-without-result states stop), 3 exchange terminals, 2 accepted custody forms, 18 identity refusals. All as expected. |
| `check_execute.py completed` | Real `execute()`, manager, stores and OCI vector; engine substituted; provider replaced by four labelled synthetic framing records. Stage `completed`, exchange null, capture ended by custody in 1.8 s against a 240 s bound, edit verified, exit 0. |
| `provider-seam`, `fault-terminal`, `layout-missing` | Still end by the exchange form. |
| `launch-fail`, `oversize`, preflight, image gate, collection, layout | Unchanged, pass. |

## What is not exercised

- Part 1 uses a synthetic provider stream (framing only) to reach `completed`. It is a simulation at the provider boundary, labelled as such.
- Part 3's commands for the instance route come from `v12/STACK.md` and the command surfaces of the frozen source (`--help` run from source). I did not run them: each needs a build. The first selection in `PATH.md` is offline and is where they are exercised before any credential or provider call.

## Handoff

- Outcome: one packet; part 1 complete; parts 2 and 3 ready for owner decisions.
- Next: review of this packet; the four choices in `DECISIONS.md`; then selection A in `PATH.md`.
- I authored this packet and do not review it.
