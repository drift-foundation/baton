# Reproduce narrow composition checks

Read-only git archive 86c1c22b9125176b0127fc4a86fa00855ed6d127 v12 into work/scratch/w385292/joined-export. Apply native-labels-5-joined/joined.patch with patch --batch --fuzz=0 -p1; verify all11 output hashes against the pinned manifest. Check ten non-shared files against correction-3 and strip the exact four-line observation block from the joined registry to compare it to accepted labels bytes. Compare the six other monitoring files against its accepted manifest.

Run check-composition.py using timeout60 and /home/sl/.local/state/baton-v12-venv/bin/python, PYTHONPATH=/home/sl/src/baton/work/scratch/w385292/joined-export/v12/python/src:/home/sl/src/baton/work/scratch/w385292/joined-export/v12/python and TMPDIR=/home/sl/src/baton/work/scratch/w385292/roots. This checks full registry accounting but only executes7observation tests.

Run the packet preflight/import_preflight.py using that interpreter with --manifest <pinned-packet>/manifest.json --host /home/sl/src/baton --candidate <pinned-packet>/candidate --json <new-review-evidence-output> --apply-plan. This prints a plan only, never imports. Verify manifest/helper hashes against this review first. Preserve original evidence on reruns.
