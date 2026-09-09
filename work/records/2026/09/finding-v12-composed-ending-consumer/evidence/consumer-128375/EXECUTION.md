# Read-only consumer join — claim128375

Question before testing: after all serving handles close, can a new process
load the actual observing_factory and report the same owned terminal completion
without invoking a serving act, while rejecting missing/foreign evidence and
retaining an absent handoff as owed? Does it close both owner handles on success
and refusal? Use the unchanged public provider APIs with configured Authority
UUID. SQLite-managed WAL/SHM activity is allowed by owner128249/128251; database
contents, modes and committed evidence remain protected.

Scope: only stage_execution.py/test_stage_execution.py and attributable dossier
evidence/progress. Preserve all16 intake paths except that pair. Reuse accepted
ordinary/reconstruction evidence; no provider or unchanged full-suite reruns.

Carry8.87630141095724s/20s from consumer126807, leaving11.12369858904276s.
The retained runner enforces the remaining cumulative process budget and logs
every run. First run only the new fresh-process method; if it passes, run the
three existing observation-only compatibility controls affected by this join.
