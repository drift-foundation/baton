"""Mechanical live packaging checks; never start a runtime or read credentials."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[4]
HERE = REPO / 'v12/testing/live_ab'


class LiveProviderPreparation(unittest.TestCase):
    def test_live_documents_use_pinned_images_real_reference_and_current_task_ids(self):
        images = json.loads((HERE / 'live-images.json').read_text())['images']
        with tempfile.TemporaryDirectory(prefix='live-ab-render-test-') as temporary:
            root = Path(temporary)
            shutil.copytree(HERE / 'fixtures/baseline', root / 'source')
            settings = {'authority_uuid': 'ab123456000000000000000000000002', 'base': 'a' * 40,
                        'tree': 'b' * 40, 'created_at': '2026-09-12T15:30:00.000Z',
                        'provider_base': json.loads((HERE / 'live-images.json').read_text())['base'], 'images': images,
                        # W384870: a FAKE registry path that does not exist; the composer only carries it.
                        'credential_registry': str(root / 'nowhere' / 'fake-credential-sources.json')}
            (root / 'settings.json').write_text(json.dumps(settings))
            (root / 'image-context-manifest.json').write_text('{}\n')
            script = '''import sys
sys.path.insert(0,sys.argv[1])
import deployment as d
facts=d.bootstrap(d.RUN/'authority.sqlite3')
d.CONFIG.mkdir()
d.documents(d.CONFIG,d.SETTINGS['images'],facts)
'''
            done = subprocess.run([sys.executable, '-c', script, str(HERE)], cwd=REPO / 'v12/python',
                env=dict(os.environ, BATON_LIVE_AB_RUN_ROOT=str(root), PYTHONPATH='src:.', PYTHONDONTWRITEBYTECODE='1'),
                capture_output=True, text=True, timeout=15)
            self.assertEqual(done.returncode, 0, done.stderr)
            config = json.loads((root / 'config/stage-execution.json').read_text())
            workers = [one['deployment'] for one in config['workers']]
            workers += [one['deployment'] for one in config['result_judgment_workers']['job-b'].values()]
            self.assertEqual(len(workers), 8)
            for worker in workers:
                self.assertEqual(worker['network'], 'bridge')
                self.assertEqual(worker['credential_sources'], settings['credential_registry'])
                self.assertEqual(worker['credential_profile'], {'claude': {'provider': 'operator-file', 'reference': 'w64268-run1'}})
                self.assertIn(worker['image_digest'], images.values())
                task = json.loads(Path(worker['task_document']).read_text())
                self.assertTrue(task['task_id'].startswith(settings['authority_uuid'] + '-'))
                self.assertNotIn('BATON-SYNTHETIC', task['instructions'])
            self.assertNotIn('BATON-SYNTHETIC', (root / 'config/integration-instructions.txt').read_text())
            self.assertFalse((root / 'credential-sources.json').exists())
            self.assertFalse((root / 'nowhere').exists(), 'the composer never touches the registry path')
            self.assertFalse((root / 'jobs.sqlite3').exists())
            self.assertFalse((root / 'control.sqlite3').exists())
            self.assertEqual(json.loads((root / 'config/stage-execution.json').read_text())['workers'][0]['deployment']['credential_sources'].startswith('/home/sl/'), False)

    def test_the_registry_is_an_explicit_run_input_and_a_bad_one_refuses_composition(self):
        # W384870 (M384918): no personal-home default; missing or relative refuses before any store or render.
        for name, settings_extra in (('missing', {}), ('relative', {'credential_registry': 'relative/credential-sources.json'}), ('unnormalized', {'credential_registry': '/var//tmp/../x.json'}), ('empty', {'credential_registry': ''})):
            with self.subTest(name=name), tempfile.TemporaryDirectory(prefix='live-ab-registry-test-') as temporary:
                root = Path(temporary)
                settings = {'authority_uuid': 'ab123456000000000000000000000002', 'base': 'a' * 40, 'tree': 'b' * 40,
                            'created_at': '2026-09-12T15:30:00.000Z', 'provider_base': 'sha256:' + 'c' * 64, 'images': {}, **settings_extra}
                (root / 'settings.json').write_text(json.dumps(settings))
                done = subprocess.run([sys.executable, '-c', 'import sys\nsys.path.insert(0,sys.argv[1])\nimport deployment', str(HERE)], cwd=REPO / 'v12/python',
                    env=dict(os.environ, BATON_LIVE_AB_RUN_ROOT=str(root), PYTHONPATH='src:.', PYTHONDONTWRITEBYTECODE='1'), capture_output=True, text=True, timeout=15)
                self.assertNotEqual(done.returncode, 0, name)
                self.assertIn('settings.credential_registry', done.stderr, name)
                self.assertEqual(sorted(path.name for path in root.iterdir()), ['settings.json'], 'refusal renders nothing')

    def test_the_scenario_requires_the_registry_operand_before_any_preparation(self):
        done = subprocess.run([sys.executable, str(HERE / 'scenario.py'), '--root', '/var/tmp/never-created-live-ab'], cwd=REPO / 'v12/python',
            env=dict(os.environ, PYTHONPATH='src:.', PYTHONDONTWRITEBYTECODE='1'), capture_output=True, text=True, timeout=15)
        self.assertEqual(done.returncode, 2, done.stderr)
        self.assertIn('--credential-registry', done.stderr)
        self.assertFalse(Path('/var/tmp/never-created-live-ab').exists())

    def test_live_image_preflight_refuses_input_drift_before_engine_access(self):
        spec = importlib.util.spec_from_file_location('live_scenario', HERE / 'scenario.py')
        scenario = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(scenario)
        selected = json.loads((HERE / 'live-images.json').read_text())
        with tempfile.TemporaryDirectory(prefix='live-ab-drift-test-') as temporary:
            with patch.object(scenario.json, 'loads', side_effect=[selected, {'v12/testing/live_ab/scenario.py': 'wrong'}]), \
                    patch.object(scenario, 'command') as engine:
                with self.assertRaisesRegex(RuntimeError, 'prepared live input changed'):
                    scenario.images(Path(temporary))
            engine.assert_not_called()


if __name__ == '__main__':
    unittest.main()
