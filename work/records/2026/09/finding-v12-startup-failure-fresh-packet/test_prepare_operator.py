"""Deterministic owner-recipe checks: no Docker, Git mutation or live credentials.

Connected preparation uses real frozen bootstrap/Authority/composer; only the
repository clone/read and private registry operands are disposable test seams.
Each connected case runs in its own process so import-origin checks stay real.
"""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
import prepare_operator as recipe


def worker(root, fail):
    spec = json.loads(recipe.SPEC.read_text())
    spec['instance_root'] = str(root / spec['run_id'])
    spec['artifact_root'] = str(root / 'packets' / spec['run_id'])
    (root / 'packets').mkdir()
    registry = root / 'registry.json'
    bearer = root / 'bearer'
    bearer.write_text('deterministic-unused-test-value')
    bearer.chmod(0o600)
    registry.write_text(json.dumps({'schema':'baton.user-credential-sources/1','sources':[{'provider':'operator-file','reference':'w202663-development','path':str(bearer)}]}))
    registry.chmod(0o600)
    spec['credential_registry'] = str(registry)
    called = []
    def repositories(document, places, *, source, stream, runner):
        called.append('repositories')
        if fail:
            raise RuntimeError('injected repository preparation failure')
        destination = Path(places['repository']) / 'workspace'
        for name in spec['task_files']:
            target = destination / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((Path(source) / name).read_bytes())
        return {'simulated_repository_boundary':True,'source':source}
    with mock.patch.object(recipe, 'git_read', return_value=(spec['base']+'\n').encode()):
        try:
            answer = recipe.prepare(spec, repository_preparer=repositories)
        except RuntimeError:
            if not fail:
                raise
            failed = Path(spec['instance_root']) / 'preparation/FAILED.json'
            assert failed.is_file()
            assert not Path(spec['artifact_root']).exists()
            try:
                recipe.prepare(spec, repository_preparer=repositories)
            except RuntimeError as error:
                assert 'fresh canonical root' in str(error)
            else:
                raise AssertionError('rerun adopted partial state')
            assert called == ['repositories']
            print(json.dumps({'failure_preserved':True,'rerun_refused':True}))
            return
    complete = json.loads(Path(answer).read_text())
    assert complete['job_started'] is False
    packet = json.loads(Path(complete['packet']).read_text())
    assert packet['context'] == {'mode':'fresh'}
    submission = json.loads(Path(packet['submission']['path']).read_text())
    assert len(submission['jobs']) == 1
    assert len(submission['jobs'][0]['stages']) == 1
    assert submission['jobs'][0]['execution_limits'] == {'provider_turn_seconds':180,'verification_command_seconds':30}
    assert not Path(packet['deployment']['job_store']).exists()
    assert not Path(packet['deployment']['control_store']).exists()
    assert not Path(packet['outcome_path']).exists()
    prepared = json.loads((Path(answer).parent / 'prepare-instance.json').read_text())
    assert len(prepared['granted']) == 4
    assert prepared['work_id'] == complete['work_id']
    commands = json.loads(Path(complete['commands']).read_text())
    assert commands['start'][0] == sys.executable
    assert str(Path(spec['instance_root']) / 'manager-source/v12/python') in commands['environment']['PYTHONPATH']
    assert called == ['repositories']
    print(json.dumps({'prepared':True,'job_started':False,'grant_count':4,'commands_emitted':True}))


class OperatorRecipe(unittest.TestCase):
    def test_candidate_and_source_preflight_without_engine(self):
        result = recipe.preflight(json.loads(recipe.SPEC.read_text()), inspect_image=False)
        self.assertFalse(result['effects'])

    def test_candidate_drift_refuses_before_effects(self):
        spec = json.loads(recipe.SPEC.read_text())
        name = next(iter(spec['files']))
        spec['files'][name] = '0' * 64
        with self.assertRaisesRegex(RuntimeError, 'candidate drift'):
            recipe.preflight(spec, inspect_image=False)
        self.assertFalse(Path(spec['instance_root']).exists())
        self.assertFalse(Path(spec['artifact_root']).exists())

    def test_image_mismatch_refuses_before_effects(self):
        spec = json.loads(recipe.SPEC.read_text())
        real = recipe.command
        def inspect(argv, **kwargs):
            if argv[0] == 'docker':
                return b'"sha256:wrong"'
            return real(argv, **kwargs)
        with mock.patch.object(recipe, 'command', side_effect=inspect):
            with self.assertRaisesRegex(RuntimeError, 'local image differs'):
                recipe.preflight(spec)
        self.assertFalse(Path(spec['instance_root']).exists())

    def test_existing_root_refuses_before_effects(self):
        with tempfile.TemporaryDirectory() as root:
            spec = {'instance_root':root,'artifact_root':root+'-absent'}
            with self.assertRaisesRegex(RuntimeError, 'fresh canonical root'):
                recipe.fresh(spec)

    def test_symlink_root_refuses_before_effects(self):
        with tempfile.TemporaryDirectory() as root:
            p = Path(root)
            (p/'link').symlink_to(p/'missing')
            with self.assertRaisesRegex(RuntimeError, 'fresh canonical root'):
                recipe.fresh({'instance_root':str(p/'link'),'artifact_root':str(p/'other')})

    def connected(self, fail=False):
        with tempfile.TemporaryDirectory(prefix='w257627-operator-test-') as root:
            result = subprocess.run([sys.executable,'-B',__file__,'--worker',root,str(int(fail))],capture_output=True,text=True,timeout=40)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            self.assertIn('true',result.stdout)

    def test_connected_preparation_no_job_submission(self):
        self.connected()

    def test_failure_preserves_partial_root_and_refuses_rerun(self):
        self.connected(fail=True)


if __name__ == '__main__':
    if len(sys.argv)>1 and sys.argv[1]=='--worker':
        worker(Path(sys.argv[2]),bool(int(sys.argv[3])))
    else:
        unittest.main()
