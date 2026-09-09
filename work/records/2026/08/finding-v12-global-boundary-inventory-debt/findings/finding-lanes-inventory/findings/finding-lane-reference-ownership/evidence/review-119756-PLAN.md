# Independent verification plan

W119476 claim119756, baton.codex, 2026-09-08.

Question: do the exact submitted final bytes execute all 21 additive controls
and preserve the original runtime-lane cases? PROGRESS reports 19 new/50 total
tests while the final file adds 21, and only inventory failure lists are
retained as machine output. The final two discovery/rule controls therefore
lack unambiguous executed-final-candidate evidence.

Run once from v12/python:
`PYTHONPATH=.:src python3 -m unittest tests.manager.test_runtime_lane`.
Budget: 30 seconds. Retain output, candidate hashes and additive/base AST audit.
Also use a quick direct hostile-dict/string-subclass probe through the exported
helper to cover the approved no-caller-behavior contract not exercised by the
new plain non-document cases. No daemon or broad inventory/module sweep.

Compare the retained before/after inventory failure lists; use them only as
author evidence of the unchanged failure identifiers, not as full independently
executed inventory results. No broader repeat is warranted by this two-path
correction unless the focused verification uncovers a new issue.
