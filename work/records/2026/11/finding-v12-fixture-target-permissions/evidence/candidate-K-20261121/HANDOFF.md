# W385454 — fixture-only candidate for independent review (K, owner-held arrangement)

K (`baton.prompt`, no claim; M385455/M385454 under the standing owner-held pilot arrangement). Isolated, not imported. Both feature packets untouched and frozen (their digests are pinned in `manifest.json`).

## Candidate

| | |
|---|---|
| Base | `7ac02c7f01cc59b43ade0c98b55be59ea750af41` (host `v12/` clean at it; the base copy here equals `git show 7ac02c7f:<path>` and the host bytes) |
| Path | `v12/python/tests/tools/test_stage_execution.py` — one path, modified; nothing under `src/` or `tools/` |
| Digests | base `2596473888c0c8d3d444157add13d121ed52d540cb834764ea7dd61ca3eff127` → candidate `03a7710ee7440e3c1c1aaa95ac40e9931dfcaedfe75391874ecd7b72079a99d2`; tree (SHA-256 of `candidate.sha256`) **`c6755437f3effa6f5ddc2fcc69e6235e46dd02a66428cdb844570fa09d94cc99`**; patch `candidate-from-7ac02c7f.patch` `0c752249…` (107 lines) |
| Overlap | none with W385427 (13 paths, tree `5348d4b3…`) or W385424 (10 paths, listing `e686d8c2…`): neither touches this file, so composition is disjoint |

## The correction

- `establish_target_posture(case, place, gid)` (module-level helper): asserts the directory's group IS the configured workspace group (it never `chown`s — an ordinary uid cannot, and a fixture that silently skipped the group half would prove less than the product checks) and sets exactly the two bits `oci_delivery.prove_target_posture` requires, `S_IWGRP | S_IXGRP`, on top of whatever mode the directory has. Nothing else changes; the call is idempotent.
- `traversing(...)`: immediately where the scenario nominates the fixture's source repository as the deployment's canonical target (`given["integration_target"] = self.source`), the posture is established with `os.getgid()` — the gid the fixture itself configures as the workspace group (`group()`: `workspaces.configure_workspace_group(control, os.getgid())`). The comment there says why.
- `TheTraversedTargetPostureIsExplicit` (4 focused cases, run under `umask 077` with restoration): a restrictive umask leaves the group bits out and the helper puts exactly them back; only the two bits change and the call is idempotent (`0o2700 → 0o2730`, `0o775` stays); the product predicate's own terms hold over the resulting stat; a foreign gid is a test failure, not a repair.
- `import stat` added. No product byte changed; `prove_target_posture`, `compatible_target` and the integration runtime's refusal are untouched; `tests/manager/test_oci_integration.TheTargetPostureIsProvedAndNeverRepaired` (the negative coverage: `0o755` refused with "operator provisioning" and nothing repaired; `0o2760` without traversal refused) is unchanged and still passes.

Not touched, by choice: the bare `integration-workspace` created beside the target (the product proves the target's posture, not the workspace's), and the other two scenarios that nominate `self.source` as a target directly to `integration_worker` (lines ~5721, ~5996) — they are not the confirmed defect's path; if they share the dependence it is a separate observation.

## Proof

1. **The exact two owner-approved cases under 002, 022 and 077**, on the corrected tree, under the established confinement (bubblewrap: whole host read-only except one fresh run directory, no network, PID namespace, caps dropped; W385427's fixture Git guard sha256 `28e29e31…` first on `PATH` logging every invocation and target; `TMPDIR` and both disk roots inside the run's fresh `fixtures/`; prepared interpreter; bytecode off; harness = W385427's `fixture_runner.py` + process umask + a retention wrapper on `prove_target_posture`): `umask-runs/SUMMARY.json`:

   | run | umask | result | posture observed → answered | Git |
   |---|---|---|---|---|
   | fix-002 | 002 | **2/2 OK**, 11.5 s | target `0o775`, gid 1000 → accepted ×4 | 442 invocations, 0 refused, none outside the fixture roots |
   | fix-022 | 022 | **2/2 OK**, 11.5 s | `0o775` → accepted ×4 | 442 / 0 / none |
   | fix-077 | 077 | **2/2 OK**, 11.6 s | `0o730` → accepted ×4 | 442 / 0 / none |

   Control: the same harness on the uncorrected base and on W385424's frozen candidate (M385452, `…/native-attempt-be4fbac0-recovery/umask-probe/`) fails both cases under 022 and 077 with `prove_target_posture` refusing `0o755`/`0o700`. Candidate and base were held constant there; here the only change is this file.
2. **Focused checks** (`logs/focused-posture-run2.log`, Git shimmed out with W385427's `no-git` entrypoint, roots outside the checkout): `TheTraversedTargetPostureIsExplicit` 4/4 + `TheTargetPostureIsProvedAndNeverRepaired` 3/3 = **Ran 7, OK**. Honest accounting: run 1 (`focused-posture-run1-expectation-error.log`) failed one NEW case on my own expectation (`0o2770` where the helper correctly yields `0o2730` — it grants write and traversal, not read); the expectation was corrected, the helper was not.

Not run: the whole `tests.tools.test_stage_execution` module or the tools-pure group (their fixtures initialise and commit disposable Git repositories beyond the two approved cases; the owner exception names those two cases only). The reviewer may select that under its own boundary. Affected logical group: tools-pure.

## Boundaries

No host import, no live run, no worker-wide umask or policy change, no Git mutation of the owner checkout or any existing repository (fixture Git only inside the fresh confined roots under `/var/tmp/baton-v12-w385454/verification-git/`, logged), no change to either feature packet. The isolated trees under `/var/tmp/baton-v12-w385454/` are disposable. Independent review and, after acceptance, serial composition of the three deltas (W385427, W385424, this) with a joined review precede any host import and human checkpoint.
