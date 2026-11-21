# Selective Git commands for the owner (not run by K; only after the joined review accepts and the import is done)

Import (K or the integrator, under the owner's instruction; refuses on any drift):
```sh
cd /home/sl/src/baton
python3 -I work/records/2026/10/finding-v12-development-coordination-pilot/evidence/joined-composition-20261121/import/integrate.py preflight work/records/2026/10/finding-v12-development-coordination-pilot/evidence/joined-composition-20261121 work/records/2026/10/finding-v12-development-coordination-pilot/evidence/joined-composition-20261121/import
python3 -I work/records/2026/10/finding-v12-development-coordination-pilot/evidence/joined-composition-20261121/import/integrate.py import   work/records/2026/10/finding-v12-development-coordination-pilot/evidence/joined-composition-20261121 work/records/2026/10/finding-v12-development-coordination-pilot/evidence/joined-composition-20261121/import
sha256sum -c work/records/2026/10/finding-v12-development-coordination-pilot/evidence/joined-composition-20261121/import/post-import.sha256
```

Stage exactly the 20 accepted paths and commit:
```sh
cd /home/sl/src/baton
git status --porcelain -- v12            # exactly 20 " M" lines, all in import/imported-paths.txt
xargs -a work/records/2026/10/finding-v12-development-coordination-pilot/evidence/joined-composition-20261121/import/imported-paths.txt git add --
git diff --cached --stat                 # 20 files
git commit -F work/records/2026/10/finding-v12-development-coordination-pilot/evidence/joined-composition-20261121/import/commit-message.txt
git rev-parse HEAD                       # report on T321608
```
Optionally stage the four dossiers' records (owner's choice). Separate boundaries after the commit: bundle build and the worker image rebuild (`claude_agent.py`/`baton_worker.py` are Dockerfile inputs), installation, any live run — the qualification packet's steps.
