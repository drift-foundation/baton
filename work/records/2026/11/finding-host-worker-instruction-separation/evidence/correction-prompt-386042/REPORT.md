# W385853 instruction delivery — R1/R2 correction, exact delta

Author: baton.prompt (K, model Fable 5.2). Owner-selected direct interactive
correction, no claim taken or impersonated; coordination M386042.
2026-11-24. Answers review M386040, `review-2026-11-24T22-30-06Z.md`
(`79379937…`). **For independent delta review by baton.codxpc.**

## Candidate and delta

- New candidate: `sha256:6580545d6cb0c9673e9baf4dce3699b41813024654da1af5386e85dcbe59d440`,
  12 paths on base `317351e73c92749e201f536ba115c9fdf213077d`. Full archive
  sha256 `5abb5d904c9e2c655823e16ebfb4e424077cbf618cdbef76ac400d19b07ad965`.
- Prior, reviewed: `sha256:a1d4ba20…`. Its packet
  `evidence/implementation-prompt-386030/` is unchanged (`packet.sha256`
  re-verified).
- **Delta: exactly three paths.** Delta archive sha256
  `8f6faa4517103676c10102b197c023c2d187e3ea05ec95037b2bcba4b6c852ba`;
  `delta-manifest.json`, `delta.patch`.

| Path | In prior candidate | Change |
| --- | --- | --- |
| `v12/python/tools/parallel_test.py` | No (new to the candidate) | `CONSUMED_INPUTS` gains `docs/V12-WORKER-INSTRUCTIONS.md` and `AGENTS.md` with their consumers. Registries and groups untouched |
| `v12/python/tests/tools/test_parallel_runner.py` | No (new to the candidate) | The one declared-inputs regression: a declared input outside `work/` must be one exact repository file; Work-record inputs keep the existing prefix and no-whole-dossier rules; consumer, existence and duplicate checks kept for all |
| `v12/python/tests/tools/test_provider_selection.py` | Yes | R2 proofs; helper methods moved to a test-less `SelectedBase` so a second case class can use them without re-running `SelectedCase`'s tests |

- **The nine other prior paths are byte-identical**, including every
  production file. No interface change: `MANAGED`, `LABEL_ROLES`,
  `labelled`, `context_record`, `managed_payloads`, `worker_instructions`
  are as handed off in M386036.
- Not imported. No N4a join. No build, image, engine, credential, registry
  or provider. No protected Git mutation. No resume implementation.

## R1 — corrected

- Both root documents are declared with their consumers.
- **Relocation** (`relocation.py`, `relocation.header.json`, logs): a copy
  holding only `v12/` and `consumed_inputs()` (top level: `AGENTS.md`,
  `docs`, `v12`, `work`; `docs` holds the one file) runs
  `just test-one` over the delivery proofs: 12 tests, all pass, exit 0. This
  includes the reviewer's failing id
  `…WorkerInstructionDelivery.test_packaged_copy_is_byte_identical_to_the_canonical_document`.
- **Source identity** (`identity-sensitivity.json`): `tools.source_identity
  --declared v12` lists both documents as consumed inputs; appending one byte
  to either changes the content digest; restored, the digest returns.
- **Mismatch still fails** (`mismatch-still-fails.log`): one byte appended to
  the packaged copy fails the equality proof (1 failure), then reverted.
- Runner regression module: 73 of 73 in the focused run.

## R2 — evidence completed

New proofs, all in `tests.tools.test_provider_selection` (`new-test-ids.json`):

| Row of contract §3.2 | Proof | What it asserts |
| --- | --- | --- |
| Clarification stop, implementation | `SelectedHandoffCase.test_d3_continuation_and_response_turns_…` turn 1 | The builder that ran is `_handoff_prompt`; prompt = `implementation` label + blank line + exactly that builder's output; argv equals the policy's; entry bytes at child start |
| Reviewer's clarification response | same test, turn 2 | Builder is `_response_prompt`; `review` label; reviewer's own home; entry at start |
| Continuation on the retained checkpoint | same test, turn 3 | Builder is `_handoff_prompt`; the reviewer's answer is in the prompt; same home as turn 1; a rewritten entry is replaced; provider-owned file kept; no session or resume operand |
| Records for all three | same test | Each attempt's ending assessment is `matched` with the recomputed label record for its role; implementation digests equal each other and differ from the review's; status says the label was reported |
| Restart, then the next turn | `SelectedCase.test_d3_d4_restart_then_next_provider_turn_…` | Stores closed and reopened, fresh serving object; the next implementation turn runs: `_prompt` builder, label, argv, rewritten entry replaced, provider state and session marker kept, same home, ending `matched` with a checkpoint bound |
| Caller's prompt (`invoke_provider`) | `…test_d3_caller_prompt_turn_carries_the_label_of_the_proved_launch_role`, `…refuses_the_integration_role_before_any_provider` | See the trace below |

These run the real composed owners and the real worker under `/7` with the
`/3` handoff template and bootstrap-composed routing; only the provider and
engine are simulated. The finding-request kind uses the same builders and
is not separately run under `/7` (the legacy handoff suite covers the kind).

**Trace of the caller-prompt row.**
- `invoke_provider` has one production caller: `worker/integration_workload.py`
  (asserted in the test). It passes its proved launch, whose role is
  `integration`.
- Composition under `/7` refuses only context workers and publication. An
  integration worker carrying a provider contract is composable.
- `integration` is not in the label vocabulary. Such a turn refuses before
  any provider process: "the execution-context label cannot be delivered".
  Proved: zero provider invocations.
- So the row's reachable outcome under `/7` is **refusal**. The second test
  shows that a caller prompt under a labelled role would get that role's
  label and an otherwise verbatim prompt; no production caller does that.

## Findings from this correction — not fixed, for the reviewer and owner

- **F1. Contract text was wrong about integration.** §3.2 says integration
  workers "run no provider". The integration workload does take a provider
  turn. With this candidate, an integration worker under a selected provider
  policy is refused at that turn. Before it, such a turn ran unlabelled.
  The N2 and delivery fixtures compose integration without a provider
  contract, which is why nothing failed. Whether integration gets a label
  role is a decision the contract did not make; I did not make it.
- **F2. `invoke_provider` prepares the child home before it binds the
  caller's launch** (`claude_agent.py`, `_child_environments` then
  `self._seen = seen`). Under `/7` the preparation therefore takes the
  unselected path: neither the selected credential placement nor the managed
  entry happens for this entry point. Present at 317351e7; unreachable today
  because of F1's refusal. It must be corrected by whatever work gives
  integration a label role. The labelled caller-prompt test deliberately does
  not assert the home entry and says why.

## Verification

Prepared interpreter, `just test-one`, roots under `/home`, explicit id
accounting (`run-focused.py`).

| Run | Collected | Executed | Passed | Failed / errors / skips / unaccounted | Seconds |
| --- | --- | --- | --- | --- | --- |
| `focused` — the six affected modules, the runner regression module and the native-handoff module whose base class is reused | 503 | 503 | 503 | 0 | 69.2 |
| relocation (above) | 12 | 12 | 12 | 0 | — |

- All 411 ids of the reviewed run are present and pass; 4 are new; 73 runner
  and 15 native-handoff ids make up the rest.
- Source identity before and after is equal, and equals the packaged bytes.
- `git diff --check` clean.
- **Reused, not rerun:** the 2,404-test neighbouring run and the five
  mutation checks of the prior packet. Every production path is
  byte-identical to the candidate they ran on; of that run's modules only
  `test_parallel_runner` changed, and it is rerun here.
- Groups: `manager-pure`, `tools-pure`. No group, packaged or full run.

## Disclosures

- The caller-prompt proofs end the turn with a deliberate refusal after the
  one `invoke_provider` call, because an invocation creates its private
  child roots exactly once. Stated in the test.
- My first caller-prompt test made two calls in one invocation and failed on
  that rule; my first version also asserted the home entry and exposed F2.
  Development logs are in scratch `logs/`, not promoted.
- The continuation and restart proofs simulate the container's fixed
  credential slot path, as the prior correction proof did (`fixed_slot`).
- Earlier disclosures of the prior report stand unchanged, except "two root
  documents are undeclared", which R1 resolves.

## For the N4a join

Unchanged from M386036 except the candidate to consume: the **accepted and
imported checkpoint of `sha256:6580545d…`**. The join will also touch
`tools/parallel_test.py`; this candidate changes only its `CONSUMED_INPUTS`
tuple. Codex credential path, N4b and qualification stay gated.

## Next

One milestone: codexpc's independent delta review of the three paths. Then
owner import and human checkpoint; then the N4a join. F1 is for the owner
when convenient; it does not block this delta.
