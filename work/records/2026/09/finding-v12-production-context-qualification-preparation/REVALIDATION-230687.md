# Resumption revalidation — what the runtime already does, and the one missing behavior (claim230687)

Per owner 2026-09-21T14:37:12Z. Read-only revalidation of the retained
dossier, candidate-183524 and the CURRENT runtime, performed before any
implementation-path selection, as the resumption requires. No file outside
this dossier was edited; no test, live call, engine act or identity was
consumed.

## 1. The runtime moved past this Work's premises while it was parked

W177936's fixture campaign (five consumed identities, candidate-183524)
qualified an OFFLINE stand-in: saved-state layout, two-UID custody and
publication rules for a hand-rolled qualification worker. While it was
parked, the W202663-era campaign built the REAL thing into the product,
and it is deterministically proven there today:

- `worker_manager/provider_context.py` — certified context profiles, the
  closed serving argv policy (`--print/--output-format json`, `--session-id`
  to OPEN, `--resume` to RESTORE, `--model` pinned), admitted context uses
  with derived `conversation_id`, generations, delivery digests, serving
  receipts with strict model/terminal acceptance, hold/retire.
- `worker_manager/context_delivery.py` — materialized per-use context
  storage delivered into the container at `/run/baton/context`.
- `tools/single_worker.py` + `tools/stage_execution.py` — implementation-only
  context preflight, admission, materialization, invocation binding and
  start revalidation, wired into the real launch path.
- `worker/claude_agent.py` — the contextual serving branch composes the
  exact bound argv (`--session-id`/`--resume` + conversation + prompt),
  enforces `prompt_digest`/`argv_digest` agreement, uses the delivered
  context HOME, writes the intent marker and the context receipt.
- `tests/manager/test_claude_context.py` — a composed end-to-end case
  ALREADY DRIVES THE OWNER'S SCENARIO SHAPE: episode 1 opens with
  `--session-id`; a changes-requested review produces a correction
  attempt; the correction's invocation binds `mode: restore` with the SAME
  `context_id`/`conversation_id`; the actual second call carries
  `--resume`; the fresh HOME differs; and the restored saved state
  continues the conversation (`session.json` turn 1 → turn 2). The
  manager-side and worker-side prompt composers are asserted twins
  (`context_prompt(task) == claude_agent._prompt(task)`).

**Consequence for the retained candidate:** candidate-183524 remains
preserved, unreviewed evidence of the OFFLINE qualification design. Its
custody/publication findings (traversal-not-contents, two-UID modes)
informed the shipped machinery; its fixture code is NOT the integration
path and nothing in this continuation adopts its bytes.

## 2. The one missing bounded behavior

The owner's intended behavior is "a separately scheduled correction
execution that receives independent review feedback and resumes the
original implementer's Claude conversation." The runtime resumes the
conversation — but `provider_context.context_prompt(task)` composes the
SAME original-instructions prompt for `open` and `restore` alike, and the
worker twin `_prompt(task)` matches it. A correction round therefore
resumes the conversation only to repeat the original task text, with the
REVIEW'S FINDINGS reaching the implementer nowhere. That is the gap, and
it is the whole gap.

## 3. The pinned design (exact changed paths, for the next implementation claim)

Ownership: `v12/python/src/baton_v12/worker_manager/provider_context.py`,
`v12/python/src/baton_v12/worker_manager/context_delivery.py`,
`v12/python/tools/stage_execution.py`, `v12/worker/claude_agent.py`, and
`v12/python/tests/manager/test_claude_context.py`. No other file; the
closed context-launch field set in `baton_worker.py` is deliberately
untouched (no new delivery member is needed — see the digest argument
below).

1. **Prompt composition** — `context_prompt(task, feedback=None)` and its
   worker twin `_prompt(task, feedback=None)`: `restore` invocations
   REQUIRE a bounded feedback text (≤ 32 KiB) and append one delimited
   section — "an independent review of your previous proposal requested
   changes …" + the findings text + the unchanged verification reminder;
   `open` invocations refuse a feedback operand. The twin-equality test
   extends to the feedback form.
2. **Feedback resolution (manager)** — at `bind_context_invocation` for a
   restore-mode use, the triggering feedback is resolved from the durable
   record: the implementation line's latest CHANGES-REQUESTED verdict →
   its frozen review result manifest → the `findings` artifact's
   `report.json`, content-digest-checked against the frozen manifest
   before one byte is trusted, `report["findings"]` extracted and
   bounded. Resolution lives beside the other custody-aware composition
   in `tools/stage_execution.py` and is handed to the binding; a restore
   with no resolvable changes-requested verdict refuses by name.
3. **Feedback delivery (worker)** — the resolved text is materialized as
   one read-only `feedback` file in the delivered context-use root
   (mounted at `/run/baton/context`). The worker's contextual branch, on
   `mode == "restore"`, reads it no-follow and bounded, composes the twin
   prompt, and the EXISTING `prompt_digest`/`argv_digest` equality checks
   make the whole path tamper-evident end to end — which is why no new
   digest member and no `baton_worker` field change is needed: a modified
   or missing feedback file cannot produce the bound digests.
4. **Deterministic proof** — extend the existing composed correction case:
   the first call's prompt carries NO feedback section, the second call's
   prompt CONTAINS the exact findings text the fake review produced;
   negatives: restore with a tampered feedback file refuses at the digest
   gate, restore with the file absent refuses by name, oversized findings
   refuse at the bound, and an open-mode invocation offered feedback
   refuses. No live call anywhere.

Measurement note, per the resumption's own rule: this design PRESERVES
context; it does not promise token/cache savings. The receipts already
carry per-invocation usage; comparing a resumed correction against a
fresh-conversation correction is a measurement the owner can order once
the behavior exists.

## 4. The remaining provider-specific qualification, as a concrete proposal

W177936's still-open live question, reframed onto the shipped machinery:
**does the pinned CLI (2.1.247, image lineage now at `5c2eb55d…`) actually
resume the conversation from the manager-reconstructed minimal saved
state under `--resume <conversation-id>` in one-shot JSON mode, answering
the strict receipt fields (model, terminal success, conversation
identity)?** The offline fixtures could not answer it in 2026-09-15's
campaign and the composed tests substitute a fake provider today.

Proposal for the owner's separate selection (NOT executed now): ONE live
two-turn qualification through the REAL serving path on a disposable
instance — episode 1 `open` with a trivial bounded task, a scripted
changes-requested review, correction episode `restore` — with strict
receipt acceptance, two turns, 180 s per turn, 600 s total, no retry and
no production enabling. This becomes executable only AFTER the feedback
behavior above is implemented and reviewed, since the restore prompt is
part of what it qualifies.

## 5. Costs and preservation

This claim: read-only revalidation; zero tests run, zero provider or
engine spend, no identity consumed. All five consumed identities, every
evidence artifact and candidate-183524's bytes remain exactly as parked.
Cumulative historical spending in this dossier's FINDING/PROGRESS records
stands unchanged.
