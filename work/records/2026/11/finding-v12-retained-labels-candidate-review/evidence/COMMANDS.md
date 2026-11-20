# Reproduce bounded review checks

From repository root, after reconstructing work/scratch/w385292/export from read-only `git archive d8f77700f06b6a8b68f5f3fc2aedbcc95169afc6 v12` and the retained patch (fuzz zero), create work/scratch/w385292/roots. Each command uses only the disposable export and temporary databases:

```sh
TMPDIR=/home/sl/src/baton/work/scratch/w385292/roots PYTHONPATH=/home/sl/src/baton/work/scratch/w385292/export/v12/python/src:/home/sl/src/baton/work/scratch/w385292/export/v12/python timeout 60 /home/sl/.local/state/baton-v12-venv/bin/python work/records/2026/11/finding-v12-retained-labels-candidate-review/evidence/probe.py
TMPDIR=/home/sl/src/baton/work/scratch/w385292/roots PYTHONPATH=/home/sl/src/baton/work/scratch/w385292/export/v12/python/src:/home/sl/src/baton/work/scratch/w385292/export/v12/python timeout 60 /home/sl/.local/state/baton-v12-venv/bin/python work/records/2026/11/finding-v12-retained-labels-candidate-review/evidence/focused.py
```

The scripts are preserved evidence, not product tests or native execution. Four observational probes and 58 focused tests only; registry checks inspect the whole module listing without executing it. No broad suite or packaging build is implied.
