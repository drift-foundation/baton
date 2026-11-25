"""Default check is read-only and does not select an unbuilt image."""
import importlib.util,json
from pathlib import Path
from unittest import mock
P=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('q2owner',P/'owner-run.py');owner=importlib.util.module_from_spec(spec);spec.loader.exec_module(owner)
before=(owner.ROOT.exists(),owner.DEST.exists())
with mock.patch('subprocess.Popen',side_effect=AssertionError('preflight cannot spawn')):answer=owner.check()
assert before==(owner.ROOT.exists(),owner.DEST.exists())
import native
assert native.IMAGE is None
print(json.dumps(dict(passed=True,preflight=answer,image_qualification='pending',real_engine_calls=0)))
