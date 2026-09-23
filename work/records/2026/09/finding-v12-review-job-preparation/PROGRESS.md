# Preparation progress

## 2026-09-23 — baton.tuner, claim244188

Prepared OPERATOR.md and INPUTS.md under W244180. File ownership is confined to
these two new files and this PROGRESS.md. FINDING/PLAN, other dossiers, product
source, tests, stores, deployment and Git state were not edited.

Read W244180 detail, complete work-events and T244180; read W239528/W239533
canonical detail, T239533, bound records, the owner split and relevant source.
At snapshot244191, W239533 remained blocked by W239528. During preparation,
W239528 review-2026-09-23T03-19-21Z.md accepted the custody source correction,
with corrected image/artifact and packet preparation still pending. This is not
acceptance of a successful baseline or a proposal; the recipe preserves that gate.

Deliverables distinguish verified reviewer/verdict/read interfaces from missing
review-only supervision and unresolved cross-Job checkpoint binding. G1–G3 in
INPUTS.md record the exact observed gaps and limitations; no workaround was
attempted. OPERATOR.md includes input/preflight order, conditional command
forms, output interpretation and stop/cleanup acceptance, explicitly withholding
a launch command that does not yet exist for this scope.

Verification: source inspection plus three actual argparse help runs via
`tools.stack_command`, using Python
`/home/sl/.local/state/baton-v12-venv/bin/python -B` and PYTHONPATH
`/home/sl/src/baton/v12/python/src:/home/sl/src/baton/v12/python`:

- `manager --store /tmp/w244180-not-opened/job.sqlite3 --incarnation preparation --authority-uuid 00000000000000000000000000000000 status --help`: exit0, 0.017430617s.
- `view --help`: exit0, 0.013231272s.
- `logs --logs /tmp/w244180-not-opened/logs --attempt preparation follow --help`: exit0, 0.013844633s.

These exit during parsing, before store or log access. Total measured help
execution 0.044506522s. No product tests, provider, container or live execution
ran. This verifies source command parsing, not a selected deployed binary or
review Job. Source is a working tree with existing changes; these observations
do not independently accept those bytes for execution.

Documentation validation: all four shell blocks pass `bash -n`; all seven
relative Markdown links resolve; no trailing whitespace; help placeholder root
was not created. Measured 0.002453310s, making this claim's measured verification
0.046959832s. `git diff --check` also passed; these new untracked documents were
checked directly because Git's ordinary diff does not include untracked files.

Inspected source SHA256 values (preparation provenance, not candidate approval):

| Path | SHA256 |
| --- | --- |
| v12/python/tools/stack_command.py | 26393cd3dd2c6c134d1706e520427291d04e46d7cfd094d18d95c58819fb8c43 |
| v12/python/tools/job_manager.py | 78a8103f009df2a1b01eff240aa9a1acd719ae03f3e30ed461b04d7fa6924a12 |
| v12/python/tools/job_viewer.py | 70fe513789786565c2ddf4d4748f830478e53f89d4a9df13fedf213153a86b6e |
| v12/python/tools/attempt_logs_command.py | c360591014aeafc1f3fcd39253cba38de81e88d3e5691c842553faec694372f5 |
| v12/python/tools/stage_execution.py | ebc9be29d2bd23cf129afe33943f5336832df2ef24256c724708004220032896 |
| v12/python/src/baton_v12/job_manager/review_driver.py | 9a8a4a8193ff7b1c709c184dee3ba43a1b1e16e60891dcf31277279d2c220ae4 |
| v12/python/src/baton_v12/worker_manager/review_cycles.py | b6083a63557abef8970040ca4c446e05f28a15a12672abc630024c3649cecf83 |
| v12/worker/claude_agent.py | 18c34ff52faa150237df0c8d0206b805801ee71cb9e7a4ec6e84e4379d7f9d8d |
| ../finding-v12-single-implementation-proof/baseline.py | f27f3cd766f9271c4b3eddb6c657bca4770d18c11a74f377e717bef23df18fd5 |
| ../finding-v12-single-implementation-proof/baseline_bindings.py | d994cce02419fd82483560a541790f4b9d367f27d2b634a166bfbdb009ae2c5e |

State: preparation delivered for independent review through baton.bug. Actual
W239533 packet development/acceptance/execution remains outside this claim.
