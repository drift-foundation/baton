# W385853 instruction delivery — candidate handoff

Author: baton.prompt (K, model Fable 5.2). Owner-selected direct interactive
implementation, no claim taken or impersonated; coordination M386030.
2026-11-24. Contract: `DELIVERY-CONTRACT-FINAL-2026-11-24.md` (`c66c8c5e…`),
approved by the owner. Ownership: `OWNERSHIP-N4A-DELIVERY-2026-11-24.md`.

**For independent review by a participant other than me.** I wrote the
contract and this candidate; I must not be its reviewer.

## Candidate

- Identity: `sha256:a1d4ba200543fed639864a9221e8bd46e6a947f236c11343e1470de17cb5ef8a`
- Base: `317351e73c92749e201f536ba115c9fdf213077d`. 10 paths (9 changed, 1 added).
- Archive `candidate-files.tar.gz`, sha256
  `5360ab0e5b2f1fa88d38923b121e9205d6442ea603c0e52bb7d2c754c20b1972`;
  `candidate-manifest.json`, `delta-manifest.json`, `delta.patch`.
- Built in a disposable export of the base under `work/scratch/w385853-impl/repo`
  (its own repository, no shared Git metadata). The protected checkout's
  product files were not edited. Not imported. No Git mutation of the
  protected repository. No build, image, engine, credential, registry or
  provider. No resume implementation.

| Path | Change |
| --- | --- |
| `v12/python/src/baton_v12/provider_policy/__init__.py` | Label template and `context_label`, `labelled`, `context_record`; packaged-copy reader `worker_instructions`; `managed_payloads`; adapter gains the managed entry and the `context_label` member; a realization without delivery tables refuses |
| `v12/python/src/baton_v12/provider_policy/worker_instructions.md` | New. Byte-identical copy of `docs/V12-WORKER-INSTRUCTIONS.md` (`369ccb17…`, 5,646 bytes) |
| `v12/python/pyproject.toml` | Package data includes the copy |
| `v12/worker/claude_agent.py` | `_provider` prefixes the label under a selection and records it; `_prepared_home` delivers the managed entry instead of refusing a non-empty list; `work` attaches the label record beside attribution; one docstring sentence |
| `v12/python/src/baton_v12/worker_manager/model_attribution.py` | Ending check: label record recomputed and compared; typed hold; diagnostic shows role, digests, whether reported |
| `v12/python/tools/job_observation.py` | The two label causes shown as holds needing owner action |
| `v12/PROVIDER-SELECTION.md` | New section; one sentence corrected ("managed-entry list is empty") |
| `tests/manager/test_provider_home.py`, `tests/tools/test_provider_selection.py`, `tests/manager/test_claude_agent.py` | New proofs; see below |

Not changed: `tools/parallel_test.py` (no new module; all proofs are in
modules already registered), `Dockerfile.claude` (it already copies the whole
package directory), `tools/pool.py`, `tools/single_worker.py`,
`dogfood_entry.py`, `v12/DESIGN.md`, `AGENTS.md`, `docs/`.

## Behaviour delivered

- Every provider turn under deployment `/7`: prompt = label + one blank line
  + the builder's unchanged prompt. Label names native-worker context, the
  launch role, the worker-instruction file and digest, and the host-only
  procedures that do not apply. No Job, attempt or protocol identifier.
- `.claude/CLAUDE.md` in the retained home is the packaged bytes, replaced
  at every start; provider-written files are untouched.
- Refused before any provider process: role outside the list; changed
  template; absent, changed, empty or oversized packaged copy; adapter of the
  317351e7 shape; a realization with no delivery tables.
- Ending: a result with no label record, or a different one, is held as
  `context-label-missing` / `context-label-mismatch`; no checkpoint, verdict,
  retry or downstream opening; stable across passes and a store reopen;
  status says "held: …; owner action needed".
- Legacy `/4`–`/6`, context-reuse and provider-free workers: unchanged.

## Verification

Prepared interpreter, `just test-one`, temporary roots under `/home`.
`test-one` has no registry accounting; ids are accounted explicitly from
the verbose log against the collected set (`run-focused.py`).

| Run | Collected | Executed | Passed | Failed / errors / skips / unaccounted | Seconds |
| --- | --- | --- | --- | --- | --- |
| `focused` — six affected modules | 411 | 411 | 411 | 0 | 32.7 |
| `adjacent` — fourteen neighbouring modules, incl. the runner regression | 2404 | 2404 | 2404 | 0 | 580.8 |

- Before my change the same six modules were 393 of 393. 18 tests are new.
- Source identity before and after each run is equal, and both equal the
  final packaged bytes (`source-reconciliation.json`).
- Groups: `manager-pure`, `tools-pure` (and `job_manager` modules among the
  neighbours). No group or full-suite run is claimed. `tools-packaged` was
  not run: it needs a build, which is not selected.
- `git diff --check` clean.

**Mutation checks** (`mutation-checks.log`; each change was applied, the named
proofs failed, the change was reverted):

| Mutation | Result |
| --- | --- |
| Worker passes the prompt without the label | 2 failures |
| Worker does not place the managed entry | 4 failures |
| Manager ignores the label record at the ending | 2 failures |
| Worker labels an implementation turn as `review` | 2 failures |
| One byte appended to the packaged copy | 1 failure |

**Contract checks → proofs**

| # | Proofs |
| --- | --- |
| 1 | `test_claude_agent…test_the_prompt_carries_the_task_and_names_nothing_protocol` (legacy prompt equals the builder's bytes, no label); `test_provider_home.WorkerInstructionDelivery.test_only_one_instruction_selector_name_exists_in_the_tracked_tree`; the unchanged legacy suites in `adjacent` |
| 2 | `test_provider_selection.SelectedCase.test_d2_d3_implementation_turn_…`, `test_d2_d3_review_turn_…`; `WorkerInstructionDelivery.test_packaged_copy_is_byte_identical_…`, `test_label_names_role_instructions_and_what_does_not_apply` |
| 3 | The two `test_d2_d3_…` (prompt = label + builder output; argv equals the policy's); `test_d4_correction_replaces_entry_keeps_provider_state_and_is_a_fresh_invocation`; existing proof 47 and the existing `/7`-with-context refusal, unchanged |
| 4 | `test_d4_delivery_is_in_no_candidate_frozen_output_or_custody` (home holds exactly credential reference, entry, simulated provider file) |
| 5 | `test_d5_changed_template_…`, `test_d5_absent_packaged_instructions_…`, `test_d5_changed_packaged_instructions_…`, `test_d5_role_outside_the_label_vocabulary_…` (zero provider invocations each); `test_d5_result_without_label_record_is_held_as_missing`, `test_d5_result_with_another_label_digest_is_held_as_mismatch`; `WorkerInstructionDelivery.test_changed_absent_empty_or_oversized_…`, `test_label_refuses_unknown_role_changed_template_and_oversize`, `test_earlier_adapter_shape_and_undeclared_realization_refuse` |
| 6 | Bounds asserted in `test_label_names_…` (≤ 2,048), `test_packaged_copy_…` (≤ 16,384), `test_label_refuses_…` (oversize refuses); suffix intact in `assert_labelled` |

## Disclosures and limits

- **Simulated provider.** These proofs show what Baton composed, placed,
  passed and bound. They do not show that Claude 2.1.247 loads the home
  file, or that a model read or followed the label.
- **Hold precedence.** When both a label cause and an attribution cause
  apply, the label cause is reported. My choice; the contract does not say.
- **Assessment record gained a member** (`context_label`). No `/7` attempt
  exists in native use, so no stored record is reinterpreted.
- **Recovery path.** Original-producer recovery re-checks attribution, as
  before; it does not re-check the label record. The contract did not ask.
- **`_provider(None, …)` workloads** take the launch role. Which roles reach
  that call was not traced (contract assumption, unchanged).
- **One existing test changed:** `test_25_simulated_codex_…` now also
  declares simulated delivery tables for its simulated provider, because a
  realization without them now refuses. **One existing fixture extended:**
  `SelectedCase.provider` records the child environment and the entry bytes.
- **Correction proof simulates the fixed credential slot.** The harness gives
  each attempt its own credential directory; a container has one fixed path.
  Stated in the test.
- **Two root documents are read by the new tests** and are outside the `v12`
  identity scope: `docs/V12-WORKER-INSTRUCTIONS.md`, `AGENTS.md`. I did not
  add them to the runner's declared inputs: that list and its regression are
  specific to `work/records` paths, and widening it is another module's
  expectation. Their digests are in `source-reconciliation.json`. Reviewer's
  call whether the list should be widened.
- **Old-image row** (new adapter on the image built at 317351e7) rests on the
  base bytes' refusal of a non-empty list; it cannot be rerun on new bytes.
- An earlier development run had one error (`test_25`, above) and one of my
  new static checks was wrong twice before it was narrowed. Development
  logs are in scratch `logs/`, not promoted; the retained runs are final.
- The label line naming the instruction file is longer than its neighbours
  after substitution. Cosmetic.

## For the N4a join (codexpc)

Consume **this candidate's accepted and imported checkpoint**, not this
scratch tree: `sha256:a1d4ba20…` on `317351e7`, once independently accepted
and checkpointed by the owner. Interface, all in `provider_policy`:

| Name | Contract |
| --- | --- |
| `MANAGED[provider]` | `{"path": <home-relative>, "kind": "worker-instructions"}`. Codex adds its row. Path is the N4 contract's to justify (J1 family); none is written here |
| `LABEL_ROLES[provider]` | Codex: `["implementation"]`. The single source for the role restriction |
| `adapter(selection, network=…)` | Refuses a provider present in `REALIZATIONS` but absent from either table. Emits `managed_entries` and `context_label` |
| `labelled(adapter, role, prompt) -> str` | The prompt operand. Call it before building argv; compare argv on its result |
| `context_record(adapter, role) -> dict` | What the worker reports under result-metadata key `baton.native-worker-context/1` |
| `managed_payloads(adapter)` | Tuples for `home.prepare(managed=…)` |
| `worker_instructions()` | Packaged bytes or refusal |

- A Codex subclass that reuses `ClaudeAgent._provider`, `_prepared_home` and
  `work` gets all of this without a second implementation.
- The Codex image recipe must copy the whole `provider_policy` directory.
- Label text begins with `[`, which also satisfies N4a's R1 by construction;
  R1's own refusal stays.
- Still gated and untouched here: the Codex credential path (J1), N4b turn
  parsing and participation sources, any qualification, conversation resume.

## Next

One milestone: independent review of this candidate (not by me); then owner
import and human checkpoint; then the N4a shared-file join on that checkpoint.
