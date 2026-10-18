"""Deterministic baseline interleaving, two real handles, public submission."""
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch
root = Path(__file__).resolve().parents[5]
sys.path[:0] = [str(root / 'v12/python/src'), str(root / 'v12/python')]
from baton_v12.job_manager import JobStore, submit, projection
from tests.job_manager.fixtures import UUID, NOW, FakeOperations, submission
place = Path(tempfile.mkdtemp(prefix='w319114-repro-'))
clock = lambda: NOW
writer = JobStore.open(str(place / 'jobs.sqlite3'), authority_uuid=UUID, incarnation='writer', clock=clock)
reader = JobStore.open_readonly(str(place / 'jobs.sqlite3'), authority_uuid=UUID, incarnation='reader', clock=clock)
original = projection.stage_states

def interleave(*args, **kwargs):
    held = original(*args, **kwargs)
    submit(writer, submission())
    return held

try:
    with patch.object(projection, 'stage_states', interleave):
        try:
            projection.status(reader, FakeOperations(), observed_at=NOW)
        except KeyError as error:
            print('CONFIRMED baseline KeyError:', error, 'retained:', place)
        else:
            raise SystemExit('Baseline no longer reproduces; revalidate the interleaving')
finally:
    reader.close()
    writer.close()
