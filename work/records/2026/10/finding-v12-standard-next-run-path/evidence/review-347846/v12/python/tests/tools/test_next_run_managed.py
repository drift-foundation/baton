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

    def processes_stopped(self, record):
        if getattr(self, 'process_state', 'stopped') != 'stopped':
            raise nr.Refusal('simulated processes live or unknown')

    def recovery_evidence(self, record, packet, root):
        from tools import next_run_recovery
        from baton_v12.worker_manager import ControlStore
        from unittest.mock import Mock
        with ControlStore.open(packet['deployment']['control_store'], incarnation='recovery-fixture', clock=managed.enforcement.utc) as control:
            return next_run_recovery.prove(control, packet, Mock())

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

    def consumed(self):
        self.broker.prepare(self.fixture.task('first'))
        with patch.object(managed.baseline, 'verify_worker_image'):
            self.broker.start('first')

    def test_consumed_recovery_is_fresh_attributed_and_never_relaunches(self):
        self.consumed()
        old = {p.name: p.read_bytes() for p in (self.install / 'state').glob('first.*')}
        request = {'action': 'recover', 'run': 'first', 'task': self.fixture.task('second')}
        receipt = managed.execute_request(self.broker, managed.read_request(io.BytesIO(json.dumps(request).encode())))
        prior = json.loads(old['first.prepared.json'])
        self.assertNotEqual(receipt['uid'], prior['uid'])
        self.assertNotEqual(receipt['authority_uuid'], prior['authority_uuid'])
        self.assertEqual(receipt['recovery_from'], 'first')
        self.assertEqual(self.broker.recover('first', request['task']), receipt)
        self.assertEqual(len(self.host.dispatched), 1)
        self.assertFalse((self.install / 'state/second.consumed.json').exists())
        for name, data in old.items(): self.assertEqual((self.install / 'state' / name).read_bytes(), data)
        self.assertEqual(len(self.host.accounts), 3)
        self.assertEqual(len(self.host.admissions), 1)
        with self.assertRaises(nr.Refusal): self.broker.recover('first', self.fixture.task('third'))
        with patch.object(managed.baseline, 'verify_worker_image'):
            self.broker.start('second')
        self.assertEqual(self.broker.recover('first', request['task']), receipt)
        self.assertEqual(len(self.host.dispatched), 2)

    def test_recovery_holds_live_and_unknown_processes_before_allocation(self):
        self.consumed()
        for state in ('live', 'unknown'):
            self.host.process_state = state
            with self.assertRaises(nr.Refusal): self.broker.recover('first', self.fixture.task('second'))
            self.assertFalse((self.install / 'state/first.recovery.json').exists())
            self.assertFalse((self.install / 'state/second.allocation.json').exists())

    def test_recovery_interruption_retains_intent_and_excludes_target_collision(self):
        self.consumed()
        task = self.fixture.task('second')
        with patch.object(self.broker, '_prepare', side_effect=RuntimeError('interrupted after intent')):
            with self.assertRaises(RuntimeError): self.broker.recover('first', task)
        self.assertTrue((self.install / 'state/first.recovery.json').exists())
        with self.assertRaises(nr.Refusal): self.broker.prepare(task)
        receipt = self.broker.recover('first', task)
        self.assertEqual(receipt['recovery_from'], 'first')
        self.assertEqual(len(list((self.install / 'state').glob('account-*'))), 2)

    def test_recovery_after_prepared_receipt_interruption_replays_one_allocation(self):
        self.consumed()
        original = self.broker._prepare
        def interrupt(*args, **kwargs):
            original(*args, **kwargs)
            raise RuntimeError('reply lost after preparation')
        with patch.object(self.broker, '_prepare', side_effect=interrupt):
            with self.assertRaises(RuntimeError): self.broker.recover('first', self.fixture.task('second'))
        receipt = self.broker.recover('first', self.fixture.task('second'))
        self.assertEqual(receipt['run_id'], 'second')
        self.assertEqual(len(list((self.install / 'state').glob('account-*'))), 2)
        self.assertEqual(len(self.host.dispatched), 1)

    def test_installed_recovery_reader_uses_real_private_owner_store(self):
        self.consumed()
        script = "import sys,json;sys.path[:0]=sys.argv[1:3];from tools.next_run_recovery import inspect;print(json.dumps(inspect(sys.argv[3])))"
        answer = subprocess.run(['/usr/bin/python3', '-I', '-B', '-c', script, str(self.install / 'code/src'), str(self.install / 'code'), str(self.install / 'runs/first/PACKET.json')], capture_output=True, text=True, timeout=15)
        self.assertEqual(answer.returncode, 0, answer.stderr)
        evidence = json.loads(answer.stdout)
        self.assertEqual(evidence['state'], 'ceased')
        self.assertEqual(evidence['attempts'], [])
        self.assertEqual(evidence['admission'], 'halted')

    def test_recovery_partial_reservation_never_consumes_another_identity(self):
        self.consumed()
        original = managed.publish
        def interrupt(path, value, *args, **kwargs):
            if path.name == 'second.allocation.json': raise RuntimeError('interrupted')
            return original(path, value, *args, **kwargs)
        with patch.object(managed, 'publish', side_effect=interrupt):
            with self.assertRaises(RuntimeError): self.broker.recover('first', self.fixture.task('second'))
        receipt = managed.Broker(self.install, host=self.host).recover('first', self.fixture.task('second'))
        self.assertEqual(receipt['run_id'], 'second')
        self.assertEqual(receipt['recovery_from'], 'first')
        self.assertEqual(len(list((self.install / 'state').glob('account-*'))), 2)
        self.assertEqual(len(self.host.dispatched), 1)

    def test_interrupted_allocation_bootstrap_and_publication_continue_without_rewriting(self):
        # A fresh installation per subcase; all actual bootstrap/Authority and
        # composition effects execute. Faults interrupt those real boundaries.
        for cut in ('allocation', 'during-bootstrap', 'initial-bootstrap', 'packet', 'full-bootstrap', 'ownership', 'prepared-publication'):
            with self.subTest(cut=cut):
                self.doCleanups()
                self.setUp()
                self.consumed()
                task = self.fixture.task('second')
                original_publish = managed.publish
                original_bootstrap = managed.bootstrap.prepare
                original_write = managed.bindings._write
                original_bootstrap_publish = managed.bootstrap._publish
                original_own = managed.own_tree
                def publishing(path, value, *args, **kwargs):
                    if cut == 'prepared-publication' and path.name == 'second.prepared.json':
                        raise OSError('interrupted before final receipt')
                    result = original_publish(path, value, *args, **kwargs)
                    if cut == 'allocation' and path.name == 'second.allocation.json':
                        raise OSError('interrupted after allocation')
                    return result
                def bootstrapping(document, *args, **kwargs):
                    result = original_bootstrap(document, *args, **kwargs)
                    if cut == ('full-bootstrap' if 'workers' in document else 'initial-bootstrap'):
                        raise OSError('interrupted after bootstrap')
                    return result
                def writing(*args, **kwargs):
                    result = original_write(*args, **kwargs)
                    if cut == 'packet': raise OSError('interrupted inside packet publication')
                    return result
                def bootstrap_publishing(*args, **kwargs):
                    result = original_bootstrap_publish(*args, **kwargs)
                    if cut == 'during-bootstrap': raise OSError('interrupted inside bootstrap publication')
                    return result
                def owning(host, path, uid, gid):
                    result = original_own(host, path, uid, gid)
                    if cut == 'ownership': raise OSError('interrupted after ownership')
                    return result
                with patch.object(managed, 'publish', side_effect=publishing), patch.object(managed.bootstrap, 'prepare', side_effect=bootstrapping), patch.object(managed.bindings, '_write', side_effect=writing), patch.object(managed.bootstrap, '_publish', side_effect=bootstrap_publishing), patch.object(managed, 'own_tree', side_effect=owning):
                    with self.assertRaises(OSError): self.broker.recover('first', task)
                retained = {str(p): p.read_bytes() for root in (self.storage / 'second', self.install / 'runs/second', self.install / 'state') if root.exists() for p in root.rglob('*') if p.is_file()}
                restarted = managed.Broker(self.install, host=self.host)
                receipt = restarted.recover('first', task)
                self.assertNotEqual(receipt['run_id'], 'second')
                self.assertEqual(receipt['continuation_of'], 'second')
                self.assertEqual(receipt['recovery_from'], 'first')
                self.assertEqual(receipt['uid'], 61002)
                self.assertEqual(restarted.recover('first', task), receipt)
                restarted.check(receipt['run_id'])
                for name, content in retained.items(): self.assertEqual(Path(name).read_bytes(), content)
                self.assertEqual(len(list((self.install / 'state').glob('account-*'))), 3)
                self.assertEqual(len(self.host.dispatched), 1)
                self.assertEqual(len(self.host.accounts), 3)
                self.assertEqual(len(self.host.admissions), 1)
                with self.assertRaises(nr.Refusal): restarted.start('second')
                with patch.object(managed.baseline, 'verify_worker_image'):
                    restarted.start(receipt['run_id'])
                self.assertEqual(restarted.recover('first', task), receipt)
                self.assertEqual(len(self.host.dispatched), 2)

    def test_initial_reservation_and_preparation_interruptions_use_same_prepare_input(self):
        for cut in ('reservation', 'bootstrap', 'packet', 'receipt'):
            with self.subTest(cut=cut):
                self.doCleanups()
                self.setUp()
                task = self.fixture.task('first')
                original_publish = managed.publish
                original_write = managed.bindings._write
                def publishing(path, value, *args, **kwargs):
                    if (cut == 'reservation' and path.name == 'first.allocation.json') or (cut == 'receipt' and path.name == 'first.prepared.json'):
                        raise OSError('injected initial preparation interruption')
                    return original_publish(path, value, *args, **kwargs)
                def writing(*args, **kwargs):
                    answer = original_write(*args, **kwargs)
                    if cut == 'packet': raise OSError('injected packet interruption')
                    return answer
                original_bootstrap = managed.bootstrap.prepare
                def bootstrapping(*args, **kwargs):
                    if cut == 'bootstrap': raise OSError('injected bootstrap interruption')
                    return original_bootstrap(*args, **kwargs)
                with patch.object(managed, 'publish', side_effect=publishing), patch.object(managed.bootstrap, 'prepare', side_effect=bootstrapping), patch.object(managed.bindings, '_write', side_effect=writing):
                    with self.assertRaises(OSError): self.broker.prepare(task)
                retained = {str(p): p.read_bytes() for root in (self.storage/'first', self.install/'runs/first', self.install/'state') if root.exists() for p in root.rglob('*') if p.is_file()}
                for state in ('live', 'unknown'):
                    self.host.process_state = state
                    with self.assertRaises(nr.Refusal): self.broker.prepare(task)
                self.host.process_state = 'stopped'
                with self.assertRaises(nr.Refusal): self.broker.prepare(dict(task, instructions='different request'))
                restarted = managed.Broker(self.install, host=self.host)
                receipt = restarted.prepare(task)
                self.assertIsNone(receipt['recovery_from'])
                self.assertEqual(receipt['uid'], 61000 if cut == 'reservation' else 61001)
                self.assertEqual(receipt['continuation_of'], None if cut == 'reservation' else 'first')
                restarted.check(receipt['run_id'])
                for path, data in retained.items(): self.assertEqual(Path(path).read_bytes(), data)
                if cut != 'reservation':
                    self.assertEqual(restarted.prepare(task), receipt)
                    with self.assertRaises(nr.Refusal): restarted.start('first')
                self.assertEqual(len(self.host.dispatched), 0)
                self.assertEqual(len(self.host.admissions), 1)

    def partial_recovery(self):
        self.consumed()
        with patch.object(managed.bootstrap, 'prepare', side_effect=OSError('bootstrap interrupted')):
            with self.assertRaises(OSError): self.broker.recover('first', self.fixture.task('second'))

    def test_partial_continuation_intent_and_response_loss_replay_after_restart(self):
        self.partial_recovery()
        task = self.fixture.task('second')
        original = self.broker._prepare
        with patch.object(self.broker, '_prepare', side_effect=OSError('after continuation intent')):
            with self.assertRaises(OSError): self.broker.recover('first', task)
        transition = nr.document(self.install / 'state/second.continuation.json')
        with self.assertRaises(nr.Refusal): self.broker.prepare(dict(task, run_id=transition['target']))
        def lost_response(*args, **kwargs):
            original(*args, **kwargs)
            raise OSError('response lost')
        with patch.object(self.broker, '_prepare', side_effect=lost_response):
            with self.assertRaises(OSError): self.broker.recover('first', task)
        restarted = managed.Broker(self.install, host=self.host)
        receipt = restarted.recover('first', task)
        self.assertEqual(receipt['run_id'], transition['target'])
        self.assertEqual(restarted.recover('first', task), receipt)
        self.assertEqual(len(list((self.install / 'state').glob('account-*'))), 3)
        self.assertEqual(len(self.host.dispatched), 1)

    def test_replacement_reservation_interruption_keeps_the_same_recorded_target(self):
        self.partial_recovery()
        original = managed.publish
        def interrupt(path, value, *args, **kwargs):
            if path.name.startswith('continuation-') and path.name.endswith('.allocation.json'):
                raise OSError('replacement reserved')
            return original(path, value, *args, **kwargs)
        task = self.fixture.task('second')
        with patch.object(managed, 'publish', side_effect=interrupt):
            with self.assertRaises(OSError): self.broker.recover('first', task)
        target = nr.document(self.install / 'state/second.continuation.json')['target']
        receipt = managed.Broker(self.install, host=self.host).recover('first', task)
        self.assertEqual(receipt['run_id'], target)
        self.assertEqual(receipt['continuation_of'], 'second')
        self.assertEqual(len(list((self.install / 'state').glob('account-*'))), 3)
        self.assertEqual(len(self.host.dispatched), 1)

    def test_partial_continuation_rejects_symlinked_root(self):
        self.partial_recovery()
        root = self.storage / 'second'
        retained = self.storage / 'retained-second'
        root.rename(retained)  # Fixture injects a substituted partial root.
        root.symlink_to(retained, target_is_directory=True)
        with self.assertRaisesRegex(nr.Refusal, 'unsafe partial preparation root'):
            self.broker.recover('first', self.fixture.task('second'))
        self.assertFalse((self.install / 'state/second.continuation.json').exists())
        self.assertEqual(len(list((self.install / 'state').glob('account-*'))), 2)

    def test_partial_continuation_holds_live_unknown_and_consumed_state(self):
        self.partial_recovery()
        for observation in ('live', 'unknown'):
            self.host.process_state = observation
            with self.assertRaises(nr.Refusal): self.broker.recover('first', self.fixture.task('second'))
            self.assertFalse((self.install / 'state/second.continuation.json').exists())
        self.host.process_state = 'stopped'
        managed.publish(self.install / 'state/second.consumed.json', {'state': 'uncertain'})
        with self.assertRaises(nr.Refusal): self.broker.recover('first', self.fixture.task('second'))
        self.assertEqual(len(list((self.install / 'state').glob('account-*'))), 2)

    def test_partial_continuation_holds_unreadable_inventory(self):
        self.partial_recovery()
        def unreadable(root, *, followlinks, onerror):
            onerror(PermissionError('injected unavailable subtree'))
            return iter(())
        with patch.object(managed.os, 'walk', side_effect=unreadable):
            with self.assertRaisesRegex(nr.Refusal, 'inventory unreadable'):
                self.broker.recover('first', self.fixture.task('second'))
        self.assertFalse((self.install / 'state/second.continuation.json').exists())

    def test_partial_continuation_holds_binding_and_retained_byte_drift(self):
        self.partial_recovery()
        allocation = self.install / 'state/second.allocation.json'
        original = allocation.read_bytes()
        changed = json.loads(original); changed['uid'] = 99999
        allocation.write_text(json.dumps(changed))
        with self.assertRaisesRegex(nr.Refusal, 'binding drift'): self.broker.recover('first', self.fixture.task('second'))
        allocation.write_bytes(original)  # Fixture restores its injected corruption.
        with patch.object(self.broker, '_prepare', side_effect=OSError('after intent')):
            with self.assertRaises(OSError): self.broker.recover('first', self.fixture.task('second'))
        (self.storage / 'second/packet/drift').write_text('changed after cessation receipt')
        os.chmod(self.storage / 'second/packet/drift', 0o600)
        with self.assertRaisesRegex(nr.Refusal, 'evidence drift'): self.broker.recover('first', self.fixture.task('second'))
        self.assertEqual(len(list((self.install / 'state').glob('account-*'))), 2)

    def test_reservation_unknown_effects_are_not_resumed(self):
        self.consumed()
        original = managed.publish
        def interrupt(path, value, *args, **kwargs):
            if path.name == 'second.allocation.json': raise OSError('after reservation')
            return original(path, value, *args, **kwargs)
        with patch.object(managed, 'publish', side_effect=interrupt):
            with self.assertRaises(OSError): self.broker.recover('first', self.fixture.task('second'))
        (self.storage / 'second').mkdir()
        with self.assertRaisesRegex(nr.Refusal, 'unexpected effects'): self.broker.recover('first', self.fixture.task('second'))
        self.assertEqual(len(list((self.install / 'state').glob('account-*'))), 2)

    def test_receipt_publication_failure_never_exposes_partial_final_document(self):
        target = self.install / 'state/example.json'
        with patch.object(managed.os, 'link', side_effect=OSError('interrupted before publication')):
            with self.assertRaises(OSError): managed.publish(target, {'ready': True})
        self.assertFalse(target.exists())
        managed.publish(target, {'ready': True})
        with self.assertRaises(FileExistsError): managed.publish(target, {'ready': False})
        self.assertEqual(nr.document(target), {'ready': True})

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

    # -- W339626: THE CONFINED SOURCE LINE ------------------------------------
    #
    # The run w339626-live-345599 died before any runtime with
    # `ProfileRefusal: Git line materialization failed: fatal: could not open
    # '/dev/null' for reading and writing: Permission denied`. The case above
    # proves an allowed file and a denied file; it never starts REAL Git under
    # REAL confinement, and that combination is what failed. These do.
    #
    # They use the real kernel and the real `git` binary deliberately: a mocked
    # Git cannot prove a Landlock boundary. `test_next_run_flow` replaces
    # `Host.dispatch` and never calls `restrict_writes`, so it cannot either.

    def _confined(self, script, *operands, timeout=30):
        """Run `script` in a real child that applies the real confinement."""
        code = Path(managed.__file__).resolve().parents[1]
        return subprocess.run(
            [sys.executable, '-I', '-B', '-c', script, str(code / 'src'),
             str(code), *[str(one) for one in operands]],
            capture_output=True, text=True, timeout=timeout,
            env=dict(os.environ, GIT_CONFIG_GLOBAL='/dev/null',
                     GIT_CONFIG_SYSTEM='/dev/null',
                     GIT_AUTHOR_NAME='fixture',
                     GIT_AUTHOR_EMAIL='fixture@invalid',
                     GIT_COMMITTER_NAME='fixture',
                     GIT_COMMITTER_EMAIL='fixture@invalid'))

    def _line(self, place):
        """A REAL one-commit repository, built here and thrown away."""
        place.mkdir(parents=True, exist_ok=True)
        for argv in (['git', 'init', '--quiet', '-b', 'main', str(place)],
                     ['git', '-C', str(place), 'commit', '--quiet',
                      '--allow-empty', '-m', 'fixture']):
            done = subprocess.run(argv, capture_output=True, text=True,
                                  timeout=30,
                                  env=dict(os.environ,
                                           GIT_CONFIG_GLOBAL='/dev/null',
                                           GIT_CONFIG_SYSTEM='/dev/null',
                                           GIT_AUTHOR_NAME='fixture',
                                           GIT_AUTHOR_EMAIL='fixture@invalid',
                                           GIT_COMMITTER_NAME='fixture',
                                           GIT_COMMITTER_EMAIL='fixture@invalid'))
            self.assertEqual(done.returncode, 0, done.stderr)
        return place

    REAL_GIT = ("import subprocess,sys;sys.path[:0]=sys.argv[1:3];"
                "from tools.next_run_confinement import restrict_writes;"
                "restrict_writes(sys.argv[3]);"
                "d=subprocess.run(['git','clone','--quiet','--no-hardlinks',"
                "sys.argv[4],sys.argv[3]+'/checkout'],capture_output=True,"
                "text=True);sys.stderr.write(d.stderr);sys.exit(d.returncode)")

    def test_confined_real_git_materializes_a_source_line(self):
        inside = self.root / 'confined-git'
        inside.mkdir()
        line = self._line(self.root / 'line')
        done = self._confined(self.REAL_GIT, inside, line)
        # BEFORE the null-device allowance this is status 128 with
        # "could not open '/dev/null' for reading and writing: Permission
        # denied" -- the exact production wording.
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertNotIn('Permission denied', done.stderr)
        self.assertTrue((inside / 'checkout/.git').is_dir())

    def test_the_null_allowance_denies_every_other_device_write(self):
        """WRITE_FILE on one validated inode is not a /dev grant."""
        inside = self.root / 'one-inode'
        inside.mkdir()
        script = ("import os,sys;sys.path[:0]=sys.argv[1:3];"
                  "from tools.next_run_confinement import restrict_writes;"
                  "restrict_writes(sys.argv[3]);"
                  "os.close(os.open('/dev/null',os.O_RDWR));"
                  "d={}\n"
                  "for name in ('/dev/zero','/dev/full','/dev/random'):\n"
                  "  try:\n"
                  "    os.close(os.open(name,os.O_WRONLY)); d[name]='allowed'\n"
                  "  except OSError as f: d[name]='denied'\n"
                  "  except Exception: d[name]='absent'\n"
                  "try:\n"
                  "  os.close(os.open('/dev/w339626-probe',os.O_WRONLY|os.O_CREAT,0o600))\n"
                  "  d['create']='allowed'\n"
                  "except OSError: d['create']='denied'\n"
                  "print(repr(d));sys.exit(0 if all(v!='allowed' for v in d.values()) else 3)")
        done = self._confined(script, inside)
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        self.assertNotIn("'allowed'", done.stdout)

    def test_confinement_still_denies_sibling_installation_and_credentials(self):
        """The allowance widens nothing it was not asked to widen."""
        inside = self.root / 'mine'
        inside.mkdir()
        sibling = self.root / 'sibling-run'
        sibling.mkdir()
        (sibling / 'held').write_text('preserved')
        installation = self.install / 'code'
        credential = self.root / 'credentials'
        credential.mkdir()
        (credential / 'token').write_text('preserved')
        script = ("import sys;sys.path[:0]=sys.argv[1:3];from pathlib import Path;"
                  "from tools.next_run_confinement import restrict_writes;"
                  "restrict_writes(sys.argv[3]);"
                  "bad=[]\n"
                  "for one in sys.argv[4:]:\n"
                  "  try:\n"
                  "    Path(one).write_text('x'); bad.append(one)\n"
                  "  except OSError: pass\n"
                  "print(repr(bad));sys.exit(0 if not bad else 3)")
        done = self._confined(script, inside, sibling / 'held',
                              sibling / 'new', installation / 'intruded',
                              credential / 'token', credential / 'new')
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        self.assertEqual((sibling / 'held').read_text(), 'preserved')
        self.assertEqual((credential / 'token').read_text(), 'preserved')
        self.assertFalse((sibling / 'new').exists())
        self.assertFalse((credential / 'new').exists())

    def test_a_grandchild_inherits_the_confinement(self):
        """Descendants inherit, which is what a dispatched tree relies on."""
        inside = self.root / 'inherited'
        inside.mkdir()
        outside = self.root / 'kept'
        outside.write_text('preserved')
        script = ("import subprocess,sys;sys.path[:0]=sys.argv[1:3];"
                  "from tools.next_run_confinement import restrict_writes;"
                  "restrict_writes(sys.argv[3]);"
                  "d=subprocess.run([sys.executable,'-I','-B','-c',"
                  "'import sys;open(sys.argv[1],\"w\").write(\"bad\")',"
                  "sys.argv[4]],capture_output=True,text=True);"
                  "sys.exit(0 if d.returncode!=0 else 3)")
        done = self._confined(script, inside, outside)
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(outside.read_text(), 'preserved')

    def test_an_unusable_null_facility_fails_closed(self):
        """A wrong device refuses with NO boundary applied, never a weaker one."""
        inside = self.root / 'closed'
        inside.mkdir()
        decoy = self.root / 'not-a-device'
        decoy.write_text('regular file')
        outside = self.root / 'still-mine'
        outside.write_text('preserved')
        script = ("import sys;sys.path[:0]=sys.argv[1:3];from pathlib import Path;"
                  "from tools import next_run_confinement as c;"
                  "c.NULL_DEVICE=sys.argv[4]\n"
                  "try:\n"
                  "  c.restrict_writes(sys.argv[3])\n"
                  "except ValueError as f:\n"
                  "  Path(sys.argv[5]).write_text('refused-and-unconfined')\n"
                  "  print(str(f));sys.exit(0)\n"
                  "sys.exit(3)")
        for operand, expected in ((decoy, 'not a character device'),
                                  (Path('/dev/zero'), 'not the null device'),
                                  (self.root / 'absent-device',
                                   'could not be opened')):
            with self.subTest(operand=str(operand)):
                outside.write_text('preserved')
                done = self._confined(script, inside, operand, outside)
                self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
                self.assertIn(expected, done.stdout)
                # Nothing was applied: the refusal happened before
                # landlock_restrict_self, so this write outside still works.
                self.assertEqual(outside.read_text(),
                                 'refused-and-unconfined')

    def test_installed_imports_bind_controller_and_helper(self):
        self.broker.prepare(self.fixture.task())
        code = self.install / 'code'
        packet = self.install / 'runs/first/PACKET.json'
        script = "import sys;sys.path[:0]=sys.argv[1:3];from tools import authoring_baseline as b,authoring_enforcement as e;p=b.held_packet(sys.argv[3]);b.verify_imported_sources(p);e.verify_controller(p)"
        done = subprocess.run([sys.executable, '-I', '-B', '-c', script, str(code / 'src'), str(code), str(packet)], capture_output=True, text=True, timeout=20)
        self.assertEqual(done.returncode, 0, done.stderr)
