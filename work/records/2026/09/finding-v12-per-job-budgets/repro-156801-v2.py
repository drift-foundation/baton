"""Correct reviewer fixture lookup: attempt belongs to an allocation/episode.

The first probe incorrectly expected attempt_id on the static stage row; its
failed run remains retained and is not product evidence.
"""
from pathlib import Path
source = (Path(__file__).parent / 'repro-156801.py').read_text()
old = "    stages = [stage for stage in submission.stage_rows(jobs) if stage['attempt_id'] == attempt_id]"
new = "    from baton_v12.job_manager import scheduler\n    allocation = scheduler.allocation_of(jobs, attempt_id)\n    assert allocation is not None\n    stages = [stage for stage in submission.stage_rows(jobs) if stage['stage_id'] == allocation['stage_id']]"
assert source.count(old) == 1
exec(compile(source.replace(old, new), str(Path(__file__).parent / 'repro-156801.py'), 'exec'))
