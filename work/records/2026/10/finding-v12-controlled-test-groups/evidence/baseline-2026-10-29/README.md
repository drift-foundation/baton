# Recovered baseline evidence — 2026-10-29

The owner's baseline `/tmp/baton-v12-python-tests.log` (11136 tests, 1334.733 s,
failures=220, errors=148, skipped=21) was lost: `/tmp` is tmpfs and the host
rebooted 2026-10-29 at 15:50 local (21:50Z), after the run and after W384870
was created (16:10Z). No rerun was performed. The files here were RECOVERED on 2026-10-29 by K (baton.prompt) from
the earlier copilot session's local transcript
`~/.codex/sessions/2026/10/29/rollout-2026-10-29T05-45-52-01a1877b-11d5-76c0-87da-2f74b2f7b07e.jsonl`,
which captured command outputs read from that log before it was lost.

- `baseline-recovered-analysis.txt` — the run summary and tail, the run command
  (`just --justfile v12/python/justfile test`, serial `unittest discover`),
  and the per-module / per-symptom counts computed over all 368 report blocks.
- `baseline-failures.txt` — 316 of the 368 exact FAIL/ERROR identifiers
  (the source output was truncated; the missing ~52 are mostly in
  tests.manager.test_dependencies and tests.manager.test_boundary_inventory).
- `module-registry.tsv` — every test module on disk (181) mapped to its
  `tools/parallel_test.py` registry class; 57 are UNREGISTERED.

Label: recovered partial evidence, not a retained log. Exact source identity
of the baseline run is unknown (dirty tree at the time; not recorded).
