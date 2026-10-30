"""Actual bootstrap/Authority/composer with simulated privileged OS effects.

No useradd, sudoers, chown, engine, provider or deployed store is touched. The
fake Host records identity/custody requests; it is not proof of kernel isolation.
"""
import json
import io
import os
from pathlib import Path
import stat
import subprocess
import sys
import unittest
from unittest.mock import patch

from baton_v12.authority import Authority
from tools import next_run as nr
from tools import next_run_managed as managed
from tools import next_run_client as client
from . import test_next_run as fixture_module


class FixtureHost(managed.Host):
    def __init__(self, root):
        self.root = root
        self.owners = {}
        self.accounts = []
        self.admissions = []
        self.dispatched = []

    def require_root(self):
        pass

    def owned(self, path, uid=0, private=False):
        if not path.is_relative_to(self.root):
            return
        st = path.lstat()
        owner = self.owners.get(str(path), 0)
        if stat.S_ISLNK(st.st_mode) or owner != uid or st.st_mode & (0o077 if private else 0o022):
            raise nr.Refusal('unsafe simulated custody: ' + str(path))

    def chown(self, path, uid, gid):
        self.owners[str(path)] = uid

    def account(self, name):
        result = {'uid': 61000 + len(self.accounts), 'gid': 61000 + len(self.accounts)}
        self.accounts.append((name, result))
        return result

    def admission(self, root, caller_uid):
        self.admissions.append((root, caller_uid))

    def authority_check(self, record, packet, root, work_id):
        authority = Authority.open_readonly(packet['deployment']['authority_store'], expected_authority_uuid=packet['deployment']['authority_uuid'])
        try:
            if authority.project_work(work_id)['status'] != 'open':
                raise nr.Refusal('Work is not open')
        finally:
            authority.dispose()
        # Model the sidecars that this read creates AS the selected uid. Real
        # Host drops uid before opening; the fixture performs no actual chown.
        for suffix in ('-wal', '-shm'):
            path = Path(packet['deployment']['authority_store'] + suffix)
            if path.exists(): self.owners[str(path)] = record['uid']

    def dispatch(self, record, packet, root):
        self.dispatched.append((record, packet, root))
        return {'state': 'simulated-dispatch', 'work_start': 'unknown'}


class ManagedAllocation(unittest.TestCase):
    def setUp(self):
        self.fixture = fixture_module.NextRun()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.root = self.fixture.root
        self.host = FixtureHost(self.root)
        self.install = self.root / 'trusted'
        self.storage = self.root / 'storage'
        secret = self.root / 'fixture-secret'
        secret.write_text('fake-only')
        os.chmod(secret, 0o600)
        registry = self.root / 'credential-sources.json'
        registry.write_text(json.dumps({'schema': 'baton.user-credential-sources/1', 'sources': [{'provider': 'fixture', 'reference': 'fixture/one', 'path': str(secret)}]}))
        os.chmod(registry, 0o600)
        self.inputs = {'schema': managed.SCHEMA, 'caller_uid': 1000, 'capacity': 3, 'groups': [], 'template': self.fixture.inputs['slots']['one'], 'credential_sources': str(registry)}
        self.inputs['source_digest'] = managed.payload_digest(managed.source_payload(self.inputs['template']['compose']))
        managed.install(self.inputs, root=self.install, storage=self.storage, host=self.host)
        self.broker = managed.Broker(self.install, host=self.host)

    def test_one_installation_allocates_distinct_authorities_and_identities(self):
        first = self.broker.prepare(self.fixture.task('first'))
        second = self.broker.prepare(self.fixture.task('second'))
        self.assertNotEqual(first['authority_uuid'], second['authority_uuid'])
        self.assertNotEqual(first['work_id'], second['work_id'])
        self.assertNotEqual(first['uid'], second['uid'])
        self.assertEqual(len(self.host.accounts), 3)
        self.assertEqual(len(self.host.admissions), 1)
        for name, receipt in [('first', first), ('second', second)]:
            record, packet = self.broker.check(name)
            self.assertEqual(self.host.owners[str(self.storage / name)], receipt['uid'])
            self.assertNotIn(str(self.install / 'runs' / name / 'PACKET.json'), self.host.owners)
            authority = Authority.open_readonly(packet['deployment']['authority_store'], expected_authority_uuid=receipt['authority_uuid'])
            try:
                work = authority.project_work(receipt['work_id'])
                self.assertEqual(work['status'], 'open')
                self.assertEqual(authority.canonical_target(), 'a'*40)
            finally:
                authority.dispose()
            task = nr.document(self.install / 'runs' / name / 'task.json')
            self.assertIn(name, task['instructions'])
            self.assertEqual(packet['manager_source']['path'], str(self.install / 'code'))
            self.assertEqual(packet['outcome_path'], str(self.storage / name / 'packet/outcome.json'))
        self.assertFalse(self.host.dispatched)

    def test_preflight_before_consumption_and_no_replay(self):
        self.broker.prepare(self.fixture.task())
        parent = self.storage / 'first/packet'
        parent.rmdir()
        with patch.object(managed.baseline, 'verify_worker_image', side_effect=RuntimeError('engine unavailable')):
            with self.assertRaisesRegex(RuntimeError, 'unavailable'):
                self.broker.start('first')
        self.assertTrue(parent.is_dir())
        self.assertFalse((self.install / 'state/first.consumed.json').exists())
        self.assertFalse(self.host.dispatched)
        with patch.object(managed.baseline, 'verify_worker_image', return_value={}):
            self.broker.start('first')
            with self.assertRaisesRegex(nr.Refusal, 'consumed'):
                self.broker.start('first')
        self.assertEqual(len(self.host.dispatched), 1)
        self.assertEqual(self.broker.status('first')['state'], 'consumed')

    def test_bad_task_and_collision_do_not_allocate_another_account(self):
        task = self.fixture.task(); task['base'] = 'b'*40
        with self.assertRaisesRegex(nr.Refusal, 'base'):
            self.broker.prepare(task)
        self.assertFalse(list((self.install / 'state').glob('account-*')))
        self.broker.prepare(self.fixture.task())
        with self.assertRaisesRegex(nr.Refusal, 'already'):
            self.broker.prepare(self.fixture.task())
        self.assertEqual(len(list((self.install / 'state').glob('account-*'))), 1)

    def test_partial_allocation_retains_identity_and_uses_another_for_next_input(self):
        with patch.object(managed.bootstrap, 'prepare', side_effect=OSError('interrupted fixture bootstrap')):
            with self.assertRaises(OSError): self.broker.prepare(self.fixture.task())
        self.assertEqual(self.broker.status('first')['state'], 'allocation')
        second = self.broker.prepare(self.fixture.task('second'))
        self.assertEqual(second['uid'], 61001)
        self.assertEqual(len(self.host.accounts), 3)
        self.assertFalse(self.host.dispatched)

    def test_changed_installed_code_and_linked_output_refuse(self):
        self.broker.prepare(self.fixture.task())
        parent = self.storage / 'first/packet'
        parent.rmdir(); parent.symlink_to(self.root)
        with self.assertRaisesRegex(nr.Refusal, 'custody'):
            self.broker.start('first')
        self.assertFalse((self.install / 'state/first.consumed.json').exists())
        code = self.install / 'code/tools/authoring_shutdown.py'
        code.write_text('changed')
        with self.assertRaisesRegex(nr.Refusal, 'drift'):
            managed.Broker(self.install, host=self.host)

    def test_fresh_controller_child_inherits_only_installed_imports(self):
        self.broker.prepare(self.fixture.task())
        record, packet = self.broker.check('first')
        with patch.dict(os.environ, {'PYTHONPATH': '/caller-controlled', 'PYTHONHOME': '/caller-home'}):
            env = managed.dispatch_environment(record, packet, self.install)
        self.assertEqual(env['PYTHONNOUSERSITE'], '1')
        poison = Path(record['storage']) / 'home/.local/lib' / ('python%d.%d' % sys.version_info[:2]) / 'site-packages'
        poison.mkdir(parents=True)
        marker = self.root / 'untrusted-import-ran'
        (poison / 'sitecustomize.py').write_text('from pathlib import Path; Path(' + repr(str(marker)) + ').write_text("bad")')
        self.assertEqual(env['PYTHONPATH'], os.pathsep.join([str(self.install / 'code/src'), str(self.install / 'code')]))
        self.assertNotIn('PYTHONHOME', env)
        code = self.install / 'code'
        # Real production Process creates a fresh interpreter with the same -m
        # command/environment as the controller. The parent uses isolated mode,
        # just as Host.dispatch does; no in-process import path survives by luck.
        script = "import os,sys;sys.path[:0]=sys.argv[1:3];from tools.authoring_enforcement import Process;out=open(sys.argv[3],'wb');lock=os.open(sys.argv[4],os.O_CREAT|os.O_RDWR,0o600);child=Process([sys.executable,'-m','tools.authoring_enforcement','--help'],output=out,lock_fd=lock);code=child.wait(timeout=15);out.close();os.close(lock);sys.exit(code)"
        output = self.root / 'fresh-child.log'
        done = subprocess.run([sys.executable, '-I', '-B', '-c', script, str(code / 'src'), str(code), str(output), str(self.root / 'fresh-child.lock')], cwd=code, env=env, capture_output=True, text=True, timeout=20)
        self.assertEqual(done.returncode, 0, done.stderr + output.read_text())
        self.assertIn('--child-of', output.read_text())
        self.assertFalse(marker.exists())
        # Separately prove the same fresh environment resolves the exact bound
        # installed controller/helper/supervisor rather than just any tools.
        check = "import sys;from tools import authoring_baseline as b,authoring_enforcement as e;p=b.held_packet(sys.argv[1]);b.verify_imported_sources(p);e.verify_controller(p);print(e.__file__)"
        done = subprocess.run([sys.executable, '-B', '-c', check, str(self.install / 'runs/first/PACKET.json')], cwd=code, env=env, capture_output=True, text=True, timeout=20)
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(done.stdout.strip(), str(code / 'tools/authoring_enforcement.py'))
        broken = dict(env); broken.pop('PYTHONPATH')
        done = subprocess.run([sys.executable, '-B', '-m', 'tools.authoring_enforcement', '--help'], cwd=code, env=broken, capture_output=True, text=True, timeout=20)
        self.assertNotEqual(done.returncode, 0)
        self.assertIn('baton_v12', done.stderr)

    def test_fixed_admission_and_request_dispatch(self):
        rule = managed.admission_rule(self.install, 1000)
        self.assertEqual(rule, f'#1000 ALL=(root) NOPASSWD: {self.install / "entry.py"} request\n'.encode())
        self.assertNotIn(b'*', rule)
        policy = self.root / 'candidate.sudoers'; policy.write_bytes(rule)
        checked = subprocess.run(['/usr/sbin/visudo', '-cf', str(policy)], capture_output=True, text=True, timeout=10)
        self.assertEqual(checked.returncode, 0, checked.stderr)
        # Actual parser -> actual broker, not a permissive dispatcher mock.
        value = managed.read_request(io.BytesIO(json.dumps({'action': 'prepare', 'task': self.fixture.task()}).encode()))
        prepared = managed.execute_request(self.broker, value)
        self.assertEqual(prepared['run_id'], 'first')
        for action in ('check', 'status'):
            value = managed.read_request(io.BytesIO(json.dumps({'action': action, 'run': 'first'}).encode()))
            self.assertEqual(managed.execute_request(self.broker, value)['run_id'], 'first')
        with patch.object(managed.baseline, 'verify_worker_image', return_value={}):
            value = managed.read_request(io.BytesIO(b'{"action":"start","run":"first"}'))
            managed.execute_request(self.broker, value)
        self.assertEqual(len(self.host.dispatched), 1)
        for action in ('check', 'start', 'status'):
            self.assertEqual(prepared['commands'][action], [str(self.install / 'client.py'), action, 'first'])
        # Every routine request uses the SAME exact sudo argv. Input cannot add
        # an executable/config operand or a policy wildcard.
        from unittest.mock import Mock
        for args, stream in [(['prepare'], io.BytesIO(json.dumps(self.fixture.task()).encode())), (['check', 'first'], io.BytesIO()), (['start', 'first'], io.BytesIO()), (['status', 'first'], io.BytesIO())]:
            with patch.object(client.sys, 'stdin', type('Input', (), {'buffer': stream})()), patch.object(client.subprocess, 'run', return_value=Mock(returncode=0)) as call:
                self.assertEqual(client.main(args), 0)
                self.assertEqual(call.call_args.args[0], ['/usr/bin/sudo', '-n', client.ENTRY, 'request'])
                managed.read_request(io.BytesIO(call.call_args.kwargs['input']))

    def test_unsafe_request_operands_refuse_before_broker_access(self):
        malformed = [b'[]', b'{"action":"install","run":"first"}', b'{"action":"start","run":"../other"}', b'{"action":"start","run":"first","root":"/tmp"}', b'{"action":"start","run":"first","interpreter":"python"}', b'{"action":"start","action":"status","run":"first"}', b'{"action":"prepare","task":{},"config":"other"}', b'x'*(1024*1024+1)]
        for raw in malformed:
            with self.subTest(raw=raw[:120]):
                with self.assertRaises((nr.Refusal, ValueError)):
                    managed.read_request(io.BytesIO(raw))
        with patch.object(managed, 'Broker', side_effect=AssertionError('must not instantiate')):
            for argv in (['start', 'first'], ['request', 'first'], ['request', '--root', '/tmp'], ['status', '*']):
                with self.assertRaises(nr.Refusal): managed.main(argv)
        self.assertFalse(self.host.dispatched)

    def test_reviewed_installation_drift_refuses_before_effects(self):
        self.inputs['source_digest'] = '0' * 64
        with self.assertRaisesRegex(nr.Refusal, 'digest mismatch'):
            managed.install(self.inputs, root=self.root / 'other', storage=self.root / 'other-storage', host=self.host)
        self.assertFalse((self.root / 'other').exists())
        self.assertEqual(len(self.host.accounts), 3)

    def test_pool_exhaustion_never_recycles_an_execution_identity(self):
        for name in ('first', 'second', 'third'):
            self.broker.prepare(self.fixture.task(name))
        with self.assertRaisesRegex(nr.Refusal, 'capacity retained'):
            self.broker.prepare(self.fixture.task('fourth'))
        self.assertEqual(len(self.host.accounts), 3)
        self.assertFalse((self.storage / 'fourth').exists())

    def test_landlock_confines_a_real_unprivileged_child(self):
        inside = self.root / 'confined'; inside.mkdir()
        outside = self.root / 'outside'; outside.write_text('preserved')
        code = Path(managed.__file__).resolve().parents[1]
        script = "import sys;sys.path[:0]=sys.argv[1:3];from pathlib import Path;from tools.next_run_confinement import restrict_writes;restrict_writes(sys.argv[3]);Path(sys.argv[3]+'/allowed').write_text('ok');\ntry: Path(sys.argv[4]).write_text('bad')\nexcept PermissionError: sys.exit(0)\nsys.exit(3)"
        done = subprocess.run([sys.executable, '-I', '-B', '-c', script, str(code / 'src'), str(code), str(inside), str(outside)], capture_output=True, text=True, timeout=10)
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(outside.read_text(), 'preserved')
        self.assertEqual((inside / 'allowed').read_text(), 'ok')

    def test_installed_imports_bind_controller_and_helper(self):
        self.broker.prepare(self.fixture.task())
        code = self.install / 'code'
        packet = self.install / 'runs/first/PACKET.json'
        script = "import sys;sys.path[:0]=sys.argv[1:3];from tools import authoring_baseline as b,authoring_enforcement as e;p=b.held_packet(sys.argv[3]);b.verify_imported_sources(p);e.verify_controller(p)"
        done = subprocess.run([sys.executable, '-I', '-B', '-c', script, str(code / 'src'), str(code), str(packet)], capture_output=True, text=True, timeout=20)
        self.assertEqual(done.returncode, 0, done.stderr)
