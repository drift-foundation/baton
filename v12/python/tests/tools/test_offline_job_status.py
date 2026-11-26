"""Offline installed-instance acceptance; engine and provider are deterministic.

The installer/runtime stand-in and worker seams are the existing connected
creation and composed lifecycle fixtures. No live engine or provider is used.
"""
import hashlib
import io
import json
import os
import select
import pty
import struct
import termios
import time
import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock

from baton_v12.job_manager import JobStore, status
from baton_v12.worker_manager import ControlStore
from tests.tools import test_connected_creation, test_stage_execution
from tools import instance, job_manager, job_observation, stack, stage_execution


def job_facts(job):
    return dict(job_id=job['job_id'], lifecycle=job.get('lifecycle'),
                stages=[dict(stage_id=stage['stage_id'], work_id=stage['work_id'], state=stage['state'],
                             result=stage.get('result'), artifacts=stage.get('artifacts'),
                             activity=(stage.get('runtime') or {}).get('activity')) for stage in job['stages']])


def guarded_client(module, operands, *, reading):
    """Fresh-process instrumentation: any execution or writable read fails closed."""
    import sqlite3
    from tools import single_worker

    def forbidden(*args, **kw):
        raise AssertionError('an offline client attempted execution or a process record')

    stack._spawn = stack.write_record = job_manager._serve = forbidden
    stage_execution.factory = stage_execution.operations_from = forbidden
    single_worker.operations_from = forbidden
    connections = []
    connect = sqlite3.connect

    def connecting(database, *args, **kw):
        if reading and database != ':memory:':
            assert kw.get('uri') is True and 'mode=ro' in str(database), database
            connections.append(str(database))
        return connect(database, *args, **kw)

    sqlite3.connect = connecting

    def audit(event, args):
        if event in ('subprocess.Popen', 'os.system', 'os.fork', 'os.posix_spawn', 'socket.connect'):
            forbidden()
        if reading and event in ('os.mkdir', 'os.remove', 'os.rename', 'os.rmdir', 'os.truncate'):
            forbidden()
        if reading and event == 'open' and isinstance(args[0], (str, bytes)) and args[0] != '/dev/tty':
            flags = args[2] if isinstance(args[2], int) else 0
            assert not flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND), args

    sys.addaudithook(audit)
    import importlib
    try:
        raise SystemExit(importlib.import_module(module).main(operands))
    except SystemExit as ended:
        if ended.code not in (0, None):
            raise
    if reading:
        assert len(connections) >= 2, connections



class OfflineJobStatus(test_connected_creation.ConnectedCreationCase,
                       test_stage_execution.ComposedOneJobCase):
    def setUp(self):
        # The serving fixture runs in its own process, which exits before reads.
        pass

    now = test_stage_execution.OwnerPacedResearchTurns.now
    ticks = test_stage_execution.OwnerPacedResearchTurns.ticks
    projection = test_stage_execution.OwnerPacedResearchTurns.projection
    enter_worker = test_stage_execution.OwnerPacedResearchTurns.enter_worker
    finish_worker = test_stage_execution.OwnerPacedResearchTurns.finish_worker

    def completed_instance(self):
        from baton_v12 import provider_policy
        from baton_v12.authority import Authority
        from baton_v12.contracts import digest, job_input_identity
        from baton_v12.job_manager import manual, research
        from tests.manager import provider_fixtures
        from tools import single_worker

        self.seconds, self.providers = 0, {}
        selected, identities = provider_fixtures.identities()
        profile = dict(identities['runtime_profile'], image_digest=self.config['image_digest'], network=self.config['network'])
        adapter = provider_policy.adapter(selected, network=self.config['network'], research=True)
        manifest = dict(self.manifest, outputs=research.outputs(), runtime_profile_digest=digest(profile),
                        tool_policy_digest=digest(provider_policy.POLICY))
        manifest.pop('manifest_digest')
        manifest['manifest_digest'] = digest(manifest)
        worker = self.stage_worker('research-0', 'research', 'baton.research-0', input_manifest=manifest,
                                  launch_home=os.path.join(self.root, 'research-launch'),
                                  credential_home=os.path.join(self.root, 'research-credentials'))
        worker['deployment'].update(schema=single_worker.PROVIDER_CONFIG_SCHEMA, provider_context=None, verifier_layout=None,
            profile_name=profile['name'], profile_digest=digest(profile), adapter_name='report-only-claude', adapter_digest=digest(adapter),
            credential_slots=['claude'], credential_profile={'claude': {'provider': 'fixture', 'reference': 'test-key'}},
            provider_home_root=os.path.join(self.root, 'job-work'),
            provider_contract={'selection': selected, 'runtime_profile': profile, 'adapter': adapter})
        self.installed(workers=self.workers()[:2] + [worker], jobs=[], owner_participant='baton.slaw',
                       line_declared_base=self.base, canonical_target_id=self.base)
        with Authority.open(self.owned['authority_store'], expected_authority_uuid=self.owned['authority_uuid']) as authority:
            authority.create_work(self.work, 'research', contract='v12-assignment-1', operation_id='offline-research-work')
        self.engine = test_stage_execution._ConcurrentEngine()
        self.job = JobStore.open(self.owned['job_store'], authority_uuid=self.owned['authority_uuid'], incarnation='fixture', clock=self.now)
        self.control = ControlStore.open(self.owned['control_store'], incarnation='fixture', clock=self.now)
        self.addCleanup(self.job.close)
        self.addCleanup(self.control.close)
        self.composed = stage_execution.operations_from(self.configuration(), self.job, self.control, engine_run=self.engine,
            credential_provider=lambda *_: self.secret, clock=self.now, checkout=self.checkout)
        self.addCleanup(self.composed.close)
        manual.create(self.job, 'study', {'scope': ['worker-task.txt'], 'wall_seconds': 100})
        installed = self.composed.deployment.given['workers'][-1]['deployment']
        descriptor = dict(kind='research', statement='Summarize routing', scope=['worker-task.txt'], source_commit=self.base,
                          depends_on=[], work_id=self.work, policy_digest=installed['policy_digest'],
                          profile_name=installed['profile_name'], profile_digest=installed['profile_digest'])
        descriptor['input_digest'] = job_input_identity(research.delivery(installed, descriptor)['input_manifest'])
        manual.add_phase(self.job, 'study', 'routing', descriptor)
        manual.start_phase(self.job, 'study', 'routing')
        self.ticks()
        self.enter_worker('routing')
        attempt = self.finish_worker('routing')
        from baton_v12.worker_manager import observe_activity
        observe_activity(self.control, attempt_id=attempt, bytes_observed=73)
        self.seconds = 7
        self.ticks()
        self.assertEqual(self.projection()['stages'][0]['state'], 'completed')
        manual.close_job(self.job, 'study')
        completed = status(self.job, self.composed, observed_at=self.now())
        self.assertEqual(completed['jobs'][0]['lifecycle'], 'closed')
        self.composed.close()
        self.control.close()
        self.job.close()
        return completed

    def client_argv(self, module, operands, *, reading=True):
        code = ('from tests.tools.test_offline_job_status import guarded_client; '
                + 'guarded_client(' + repr(module) + ', ' + repr(list(operands)) + ', reading=' + repr(reading) + ')')
        return [sys.executable, '-B', '-c', code]

    def client(self, *args):
        operands = ['--instance', str(Path(self.state, 'instance.json')), *args]
        done = subprocess.run(self.client_argv('tools.stack', operands), capture_output=True, text=True, timeout=60)
        self.assertEqual(done.returncode, 0, done.stderr)
        return done.stdout

    def terminal(self, locator):
        import fcntl
        from tests.tools import test_job_tui
        master, slave = pty.openpty()
        child = None
        try:
            fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack('HHHH', 35, 400, 0, 0))
            operands = ['--instance', str(Path(self.state, 'instance.json')), 'tui']
            child = subprocess.Popen(self.client_argv('tools.stack', operands), stdin=slave, stdout=slave, stderr=slave,
                                     env=dict(os.environ, TERM=test_job_tui._terminal()), start_new_session=True)
            drawn = b''

            def until(needle):
                nonlocal drawn
                deadline = time.monotonic() + 15
                while needle.encode() not in drawn and time.monotonic() < deadline:
                    if select.select([master], [], [], 0.1)[0]:
                        drawn += os.read(master, 65536)
                    if child.poll() is not None:
                        break
                self.assertIn(needle.encode(), drawn, drawn.decode(errors='replace'))

            until('study')
            until('job-offline-queued')
            until('CLOSED')
            until('QUEUED')
            os.write(master, b'G\n')
            until('Retained findings: ' + locator)
            until('Phase COMPLETED')
            os.write(master, b'q')
            deadline = time.monotonic() + 10
            while child.poll() is None and time.monotonic() < deadline:
                if select.select([master], [], [], 0.1)[0]:
                    drawn += os.read(master, 65536)
                if len(drawn) > 1024 * 1024:
                    self.fail('unbounded terminal output')
            self.assertEqual(child.wait(timeout=10), 0, drawn.decode(errors='replace'))
            self.assertNotIn(b'DISCONNECTED', drawn)
            return drawn
        finally:
            if child is not None and child.poll() is None:
                child.kill()
                child.wait(timeout=10)
            os.close(master)
            os.close(slave)

    def durable_bytes(self):
        return {str(path): hashlib.sha256(path.read_bytes()).hexdigest()
                for path in Path(self.state).rglob('*') if path.is_file() and not path.name.endswith(('-shm', '-wal'))}

    def test_stopped_instance_reads_durable_jobs_without_execution(self):
        from tests.manager import disk_roots
        code = 'from tests.tools.test_offline_job_status import prepare_fixture; prepare_fixture()'
        prepared = subprocess.run([sys.executable, '-B', '-c', code], capture_output=True, text=True, timeout=60)
        self.assertEqual(prepared.returncode, 0, prepared.stderr)
        held = json.loads(prepared.stdout)
        self.root, self.state, self.owned = held['root'], held['state'], held['owned']
        self.addCleanup(disk_roots.remove_owned_root, self.root)
        completed = held['completed']
        selector = instance.read(Path(self.state, 'instance.json'))
        root = Path(selector['state'])
        self.assertEqual(stack.stop(root, stream=io.StringIO()), 0)
        stack.snapshot_path(root).unlink(missing_ok=True)
        made = subprocess.run(self.client_argv('tools.job_manager', self.argv(task='offline-queued'), reading=False),
                              capture_output=True, text=True, timeout=60)
        self.assertEqual(made.returncode, 0, made.stderr)
        queued = json.loads(made.stdout)
        before = self.durable_bytes()
        self.assertEqual(queued['job_id'], 'job-offline-queued')
        self.assertEqual(queued['binding']['job_work_id'], self.job_work('job-offline-queued'))
        shown = self.client('status')
        self.assertIn('Job study: MANUAL · CLOSED', shown)
        self.assertIn('Job job-offline-queued: QUEUED', shown)
        self.assertIn('Retained findings:', shown)
        exported = json.loads(self.client('status', '--json'))
        manager = subprocess.run(self.client_argv('tools.job_manager', [
            '--store', self.owned['job_store'], '--incarnation', 'fresh-reader',
            '--authority-uuid', self.owned['authority_uuid'], 'status',
            '--control', self.owned['control_store'], '--observe', 'tools.stage_execution:observing_factory']),
            capture_output=True, text=True, timeout=60, env=dict(os.environ, **instance.settings(selector)))
        self.assertEqual(manager.returncode, 0, manager.stderr)
        self.assertEqual([job_facts(job) for job in json.loads(manager.stdout)['jobs']],
                         [job_facts(job) for job in exported['jobs']])
        self.assertEqual({one['job_id'] for one in exported['jobs']}, {'study', 'job-offline-queued'})
        by_id = {one['job_id']: one for one in exported['jobs']}
        self.assertEqual(job_facts(by_id['study']), job_facts(completed['jobs'][0]))
        result = by_id['study']['stages'][0]['result']
        locator = result['locator']
        self.assertIn(locator, shown)
        self.assertEqual(Path(locator.removeprefix('file://'), 'report.txt').read_text(), 'Findings for routing')
        activity = by_id['study']['stages'][0]['runtime']['activity']
        self.assertEqual(activity['bytes_observed'], 73)
        self.assertNotEqual(activity['observed_at'], exported['observed_at'])
        self.assertIn('last at ' + activity['observed_at'], shown)
        for job in exported['jobs']:
            view = job_observation.job_view(exported, job)
            self.assertIn('Job ' + job['job_id'] + ': ' + view['labelled_headline'], shown)
            for phase in view['phases']:
                self.assertIn(phase['stage_id'] + ': ' + phase['position'], shown)
                for fact in phase['facts']:
                    self.assertIn(fact, shown)
        self.terminal(locator)
        self.assertEqual(self.durable_bytes(), before)
        # An explicitly old export must never shadow the newer queued Job.
        stack.snapshot_path(root).write_text(json.dumps(completed))
        old = stack.snapshot_path(root).read_bytes()
        self.assertIn('Job job-offline-queued: QUEUED', self.client('status'))
        self.assertEqual([job_facts(job) for job in json.loads(self.client('status', '--json'))['jobs']],
                         [job_facts(job) for job in exported['jobs']])
        self.terminal(locator)
        self.assertEqual(stack.snapshot_path(root).read_bytes(), old)
        stack.snapshot_path(root).unlink()
        for name in stack.PROCESSES:
            self.assertIsNone(stack.read_record(root, name))
        self.assertFalse(stack.snapshot_path(root).exists())


def prepare_fixture():
    from contextlib import redirect_stdout
    fixture = OfflineJobStatus()
    # The normal inherited installer and composed-worker setup, in this process only.
    test_connected_creation.ConnectedCreationCase.setUp(fixture)
    try:
        with redirect_stdout(io.StringIO()):
            completed = fixture.completed_instance()
        print(json.dumps(dict(root=fixture.root, state=fixture.state, owned=fixture.owned, completed=completed)))
    except BaseException:
        fixture.doCleanups()
        raise
    # Preserve the installed root for the parent; all worker children have joined,
    # the composition is closed, and process exit releases the serving guard.


class ReadOnlyLaunchAdoption(unittest.TestCase):
    def setUp(self):
        from tests.manager import test_exchange
        self.fixture = test_exchange.Home()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        from baton_v12.worker_manager import exchange, launch
        self.launch = launch
        self.operands = dict(attempt_id='attempt-offline', session='session-offline',
                             contract='fixture', role='implementation',
                             transport=exchange.EXCHANGE_TRANSPORT, workspace_group=self.fixture.group)
        self.delivery = launch.materialize(self.fixture.launch_home, **self.operands)

    def read(self, **changed):
        with mock.patch('os.makedirs', side_effect=AssertionError('read created storage')):
            return self.launch.adopt(self.fixture.launch_home, **dict(self.operands, **changed), read_only=True)

    def test_existing_and_absent_log_storage_are_read_without_repair(self):
        logs = self.delivery.logs
        self.assertEqual(self.read().logs, logs)
        os.rmdir(logs.native_root)
        self.assertEqual(self.read().logs, logs)
        self.assertFalse(Path(logs.native_root).exists())
        # Execution adoption still repairs the missing native directory.
        self.assertEqual(self.launch.adopt(self.fixture.launch_home, **self.operands).logs, logs)
        self.assertTrue(Path(logs.native_root).is_dir())
        os.rmdir(logs.native_root)
        os.rmdir(logs.log_root)
        os.rmdir(logs.root)
        self.assertIsNone(self.read().logs)
        self.assertFalse(Path(logs.root).exists())
        self.assertIsNone(self.read(attempt_id='attempt-absent'))
        self.assertFalse(Path(self.fixture.launch_home, 'attempt-absent').exists())

    def test_canonical_launch_bytes_are_required_on_both_paths(self):
        from baton_v12.contracts import ContractRefusal
        path = Path(self.delivery.place)
        os.chmod(path, 0o600)
        path.write_text(json.dumps(self.delivery.document, indent=2))
        os.chmod(path, self.launch.READ_ONLY_FILE)
        for read_only in (True, False):
            with self.subTest(read_only=read_only), self.assertRaisesRegex(ContractRefusal, 'not the one this manager'):
                self.launch.adopt(self.fixture.launch_home, **self.operands, read_only=read_only)

    def test_exchange_workspace_group_is_required_on_both_paths(self):
        from baton_v12.contracts import ContractRefusal
        from baton_v12.worker_manager import exchange
        for read_only in (True, False):
            with self.subTest(read_only=read_only):
                # Force a different validated deployment gid, without needing host groups.
                with mock.patch.object(exchange.workspaces, 'check_workspace_group', return_value=os.getgid() + 1):
                    with self.assertRaisesRegex(ContractRefusal, 'event namespace is in group'):
                        self.launch.adopt(self.fixture.launch_home, **self.operands, read_only=read_only)

    def test_execution_and_observation_refuse_changed_log_room_mode(self):
        from baton_v12.contracts import ContractRefusal
        os.chmod(self.delivery.logs.log_root, 0o700)
        for read_only in (True, False):
            with self.subTest(read_only=read_only), self.assertRaisesRegex(ContractRefusal, 'log room is mode'):
                self.launch.adopt(self.fixture.launch_home, **self.operands, read_only=read_only)


class MissingStatusStores(unittest.TestCase):
    def test_missing_stores_refuse_without_creating_storage(self):
        from tests.manager import disk_roots
        from baton_v12.job_manager.reading import read_status
        from baton_v12.contracts import ContractRefusal
        root = disk_roots.disk_backed_under(self)
        job = str(Path(root, 'jobs.sqlite3'))
        control = str(Path(root, 'absent', 'control.sqlite3'))
        operands = dict(authority_uuid='1' * 32,
                        incarnation='offline', clock=lambda: '2026-11-26T00:00:00.000Z')
        with mock.patch('os.makedirs', side_effect=AssertionError('read created storage')):
            with self.assertRaises(ContractRefusal):
                read_status(job, control_store=control, **operands)
        self.assertFalse(Path(job).exists())
        with JobStore.open(job, **operands):
            pass
        before = {str(p) for p in Path(root).rglob('*')}
        with mock.patch('os.makedirs', side_effect=AssertionError('read created storage')):
            with self.assertRaises(ContractRefusal):
                read_status(job, control_store=control, **operands)
        self.assertFalse(Path(control).parent.exists())
        self.assertEqual({str(p) for p in Path(root).rglob('*') if not p.name.endswith(('-wal', '-shm'))},
                         {p for p in before if not p.endswith(('-wal', '-shm'))})
