# Optional service tier — candidate for independent review

Author: baton.prompt (K, model Fable 5.2), interactive copilot, no claim.
2026-11-25 UTC. Owner-selected slice; coordination M386089. Prepared in a
disposable copy outside the checkout (`/var/tmp/baton-k-tier-386088`, no Git
metadata). No main product file is changed. No build, engine, credential or
provider operation; no live call.

Candidate `sha256:9c365d72625de16e193198d2f1938d82cc51cedad59d3dd54f1cd259db66c458`,
eight paths, base `1ed26970e74ea48013e3e533e057e6ace08d0058` (each base hash
equals the current working tree). Archive
`8563be759cde8ab13abf5b2440f8532c35a2d68553626a0f30fdd04bef9f9d0a`.
`candidate-manifest.json`, `candidate-files.tar.gz`, `delta.patch`.

## What it does

- **Configuration.** A selection may carry one optional member,
  `service_tier`. `pool compose-worker --service-tier <tier>` sets it.
  Unset is spelled by omitting the member; `null` refuses.
- **Closed table.** `provider_policy.SERVICE_TIERS` names what exists:
  `fast` for Codex 0.169.0, as `["-c", 'service_tier="fast"']`. Any other
  value, provider or CLI build refuses, at selection, composition and in
  the adapter. Claude with a tier refuses. Nothing selects a tier
  automatically.
- **Forwarding.** Host `provider_policy.argv` and `CodexAgent.provider_argv`
  both produce `… --model <model> -c service_tier="fast" <prompt>`; as a
  shell line, `-c 'service_tier="fast"'`. A launched worker takes the tier
  only from its validated selection; an operand there refuses. The
  existing worker check that its argv equals the manager's covers the
  tier. A detached caller (the qualification launcher) passes
  `service_tier=` explicitly.
- **Execution identity.** The tier is in the selection, in the runtime
  profile (`service_tier`) and in the adapter (`argv_policy.service_tier`),
  so the profile digest and adapter digest differ from the untiered ones.
  `delivery` refuses a profile whose tier disagrees with the selection.
- **Unset is unchanged.** Without the member, selection, profile, adapter
  and argv bytes are the same as on the base. Checked: Claude adapter
  digest `1f6d8756…` and argv identical on base and candidate.
- **Requested versus observed.** Attribution records
  `service_tier: {requested, observed: null, outcome: "missing"}` only when
  a tier is selected, and the diagnostic says
  `Service tier requested: fast; observed: no evidence`. Nothing reads an
  observed tier: no build declares a source for it. The tier adds no hold
  cause.

## Pinned-build support — what is and is not verified

From the retained 0.169.0 `exec` help (fixture `exec-help.txt`,
`b7bbe3ad…`): `-c, --config <key=value>` exists for `exec`, and the value
is parsed as TOML. That is the grammar the pair uses.

**Not verified:** that 0.169.0 recognizes the key `service_tier`, that
`fast` is a value it accepts, and that `-c` still applies together with
`--ignore-user-config`. The retained help does not mention the key (a test
asserts this, so the claim cannot drift silently). I ran no probe: engine
operations are not selected. An offline check on the retained image would
answer the first two without a credential; it needs the owner's selection.
Until then the table entry is the owner's instruction, not evidence.

## Verification

Prepared interpreter, `unittest -v`, roots under `/var/tmp` outside every
repository, export of `1ed26970` with the declared test inputs.

- Nine modules, **604 collected, 604 run, 604 ok**, 61.9 s, exit 0:
  `tests.manager.test_codex_draft`, `tests.tools.test_codex_selection`,
  `tests.manager.test_provider_home`, `tests.manager.test_claude_agent`,
  `tests.manager.test_worker_packaging`,
  `tests.tools.test_provider_selection`, `tests.tools.test_pool`,
  `tests.tools.test_parallel_runner`, `tests.tools.test_connected_creation`.
  Log `focused.stderr.log`. Groups touched: manager-pure, tools-pure; no
  group run. New cases: four in `test_codex_draft`, six in a new class
  `CodexServiceTier` in `test_codex_selection`. No new module; registry
  unchanged.
- Each guard was removed in turn and the two Codex modules rerun; seven
  mutants fail as they should: host argv drops the tier; delivery ignores
  the profile tier; observed copies requested; profile omits the tier;
  worker drops the selected tier; CLI drops the operand; null accepted.
- An eighth mutant showed that a tier comparison I had added to
  `single_worker._held` was redundant (the delivery check already
  refuses), so that edit was removed and `single_worker.py` is not in the
  candidate.
- Two earlier runs in my export failed for reasons of the export, not of
  the change: I named a test module that does not exist, and declared
  dossier inputs were missing from the export (same failure on the base).
  Both corrected before the final run.

All Codex cases use the patch-only synthetic realization of
`tests/manager/codex_fixtures.py`. No Codex realization exists in
production, so nothing here can run a tiered Codex worker yet.

## Qualification launcher

Packets `71c44a15` and the successor are codexpc's and immutable; I did
not edit them. `LAUNCHER-DELTA.md` gives the exact lines a tier-aware
successor needs. With the candidate imported, the existing launcher call
`provider_argv(prompt, model=…)` still yields the nine-element argv.

## Limits

- Observed tier has no source. Whether the provider reports one is a
  question for the live run's evidence.
- `--service-tier` alone, without the other selection operands, is refused
  by the existing selection check, like a lone `--requested-model`.
- Status output changes only for a tiered selection.

Next milestone: independent review of these exact bytes, then import and
human checkpoint. Suggested message:
`Add optional provider service tier to selection, Codex adapter and attribution`.
