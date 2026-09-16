"""Independent identity delta checks; no live admission or root reservation."""
import json
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from unittest import mock

record = Path(__file__).resolve().parent
sys.path.insert(0, str(record / 'evidence'))
import test_qualification as tests

result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(tests))
assert result.wasSuccessful()
fixture, c = tests.fixture, tests.c
manifest = json.loads(fixture.MANIFEST.read_bytes())
observed = []
with mock.patch.object(fixture, 'engine', side_effect=AssertionError('engine admission')), mock.patch.object(fixture, 'credential', side_effect=AssertionError('credential admission')):
    assert fixture.audit('5e789f4e3115b5eb9a7623772adf0a17aac3e45135afaa65bc11a35eb30e951f') == '5e789f4e3115b5eb9a7623772adf0a17aac3e45135afaa65bc11a35eb30e951f'
    for field in ('run_identity', 'private_root', 'credential_copy_root', 'export_root'):
        changed = dict(manifest, **{field: manifest[field].replace('180078', '178579')})
        raw = c.encoded(changed)
        with tempfile.TemporaryDirectory(prefix='w177936-review-180134-') as place:
            path = Path(place) / 'manifest.json'
            path.write_bytes(raw)
            with mock.patch.object(fixture, 'MANIFEST', path):
                try:
                    fixture.audit(c.sha(raw))
                except c.Refusal as error:
                    assert c.failure_code(error) == 'manifest-constants'
                    observed.append(field)
                else:
                    raise AssertionError('matching digest bypassed identity comparison')
    for previous in json.loads((record / 'EVIDENCE-180078.json').read_bytes())['refused_manifests']:
        try:
            fixture.audit(previous)
        except c.Refusal as error:
            assert c.failure_code(error) == 'manifest-digest'
        else:
            raise AssertionError('stale digest accepted')
live = [thread.name for thread in threading.enumerate() if thread is not threading.main_thread()]
print(json.dumps({'tests': result.testsRun, 'matching_digest_identity_refusals': observed, 'stale_digest_refusals': 4, 'live_threads': live}))
assert not live
