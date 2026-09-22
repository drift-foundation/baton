"""Deterministic tests of the exact canary controller and worker boundary."""
import copy
import json
import contextlib
import io
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock
import isolated_canary as q


class FakeEngine:
    """Only the engine/provider boundary is simulated; filesystem/copy is real."""
    def __init__(self):
        self.containers = {}
        self.turns = []
        self.calls = []
        self.fault = None

    def inspect(self, identity, kind='container'):
        if kind == 'image':
            return {'Id': q.IMAGE, 'Config': {'Volumes': None}}
        row = copy.deepcopy(self.containers[identity])
        if self.fault == 'running' and row['State']['Status'] == 'exited':
            row['State']['Running'] = True
        if self.fault == 'writable-input':
            next(m for m in row['Mounts'] if m['Destination'] == '/input')['RW'] = True
        return row

    def provider(self, argv, *, seconds, env, cwd):
        if argv == ['claude', '--version']:
            return (q.CLI + ' (Claude Code)\n').encode()
        self.turns.append(argv)
        home = Path(env['HOME'])
        session = argv[-2]
        path = home / q.session_path(session)
        first = '--session-id' in argv
        if first:
            token = argv[-1].split(': ', 1)[1].split('.', 1)[0]
            path.parent.mkdir(parents=True)
            path.write_text(json.dumps({'token': token, 'session': session}))
            # Poison every discarded writable home location. None may cross.
            (home / 'scratch-token').write_text(token)
            (home / '.claude/cache').mkdir()
            (home / '.claude/cache/token').write_text(token)
            result = 'READY'
        else:
            assert not (home / 'scratch-token').exists()
            assert not (home / '.claude/cache').exists()
            state = json.loads(path.read_text())
            assert state['session'] == session
            assert state['token'] not in argv[-1]
            result = 'RECALL:' + state['token']
            if self.fault == 'recall':
                result = 'RECALL:' + '0' * 32
        document = {'type': 'result', 'subtype': 'success', 'is_error': False, 'session_id': session,
                    'modelUsage': {name: {} for name in q.MODEL_ACCEPTANCE['usage_models']}, 'result': result}
        if self.fault == 'session':
            document['session_id'] = 'wrong'
        if self.fault == 'model':
            document['modelUsage'] = {q.MODEL: {}, 'other-model': {}}
        # A real short subprocess supplies the provider JSON, no live model.
        return q.invoke([sys.executable, '-c', 'import sys;sys.stdout.write(sys.argv[1])', json.dumps(document)], seconds=2, env=os.environ)

    def __call__(self, args, seconds=15):
        self.calls.append(list(args))
        command = args[0]
        if command == 'create':
            turn = 1 + len([c for c in self.calls if c[0] == 'create']) - 1
            identity = str(turn) * 64
            mounts = []
            for index, flag in enumerate(args):
                if flag == '--mount':
                    fields = dict(one.split('=', 1) if '=' in one else (one, True) for one in args[index + 1].split(','))
                    mounts.append({'Type': 'bind', 'Source': fields['src'], 'Destination': fields['dst'], 'RW': not fields.get('readonly', False), 'Propagation': 'rprivate'})
            self.containers[identity] = {'Id': identity, 'Image': q.IMAGE,
                'Config': {'Labels': {'baton.qualification': q.RUN, 'baton.attempt': q.RUN + '-turn-' + str(turn)},
                           'User': f'{os.getuid()}:{os.getgid()}', 'WorkingDir': '/output', 'Entrypoint': ['python3'], 'Cmd': ['-B', '/qualification/isolated_canary.py', '--worker']},
                'HostConfig': {'NetworkMode': 'bridge', 'ReadonlyRootfs': True, 'Privileged': False, 'CapDrop': ['ALL'],
                               'SecurityOpt': ['no-new-privileges'], 'PidsLimit': 64, 'Memory': 2147483648, 'NanoCpus': 1000000000,
                               'Tmpfs': {'/tmp': 'rw,nosuid,nodev,mode=1777,size=268435456'}},
                'Mounts': mounts, 'State': {'Running': False, 'Pid': 0, 'Status': 'created', 'ExitCode': 0}}
            return identity.encode()
        if command == 'start':
            row = self.containers[args[-1]]
            mounts = {m['Destination']: Path(m['Source']) for m in row['Mounts']}
            for target in ('/input', '/source', '/output'):
                assert not list(mounts[target].iterdir())
            if len(self.turns):
                assert len(self.containers) == 1  # First worker already removed.
            raw = q.worker(mounts['/qualification/request.json'], call=self.provider, home=mounts[q.HOME], cwd=str(mounts['/output']))
            row['State']['Status'] = 'exited'
            return raw
        if command == 'rm':
            del self.containers[args[-1]]
            return b''
        if command == 'ps':
            name = args[args.index('--filter') + 1][7:-1]
            return '\n'.join(identity for identity, row in self.containers.items() if row['Config']['Labels']['baton.attempt'] == name).encode()
        if command == 'stop':
            self.containers[args[-1]]['State'].update(Running=False, Pid=0, Status='exited')
            self.fault = None
            return b''
        raise AssertionError(args)


class Canary(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        parent = Path(self.temp.name)
        self.root = parent / 'run'
        self.root.mkdir(mode=0o700)
        self.slots = parent / 'slots'
        self.slots.mkdir(mode=0o700)
        self.credential = parent / 'credential'
        q.put(self.credential, b'fake credential never exported')
        self.engine = FakeEngine()
        self.digest = 'a' * 64
        for name, value in (('CREDENTIAL_SOURCE', self.credential), ('SLOTS', self.slots)):
            patch = mock.patch.object(q, name, value)
            patch.start()
            self.addCleanup(patch.stop)

    def execute(self):
        return q.execute(self.root, self.slots, self.digest, self.engine)

    def complete(self):
        result = self.execute()
        q.save(self.root / 'completion.json', {'outcome': 'observed-awaiting-review', 'manifest': self.digest,
               'interrupted': False, 'elapsed_seconds': 1, 'cleanup': q.cleanup(self.engine, self.slots)})
        return result

    def review(self):
        with mock.patch.object(q, 'audit'):
            return q.review(self.root, self.digest)

    def test_two_fresh_workers_restore_only_exact_session_and_independent_review(self):
        result = self.complete()
        self.assertEqual(result['recall'], 'exact')
        self.assertEqual(result['experiment'], q.MODEL_ACCEPTANCE)
        for turn in result['turns']:
            self.assertIsNone(turn['terminal']['strict_terminal']['actual_model'])
            self.assertEqual(turn['terminal']['experiment'], q.MODEL_ACCEPTANCE)
        self.assertEqual(self.review()['experiment'], q.MODEL_ACCEPTANCE)
        self.assertEqual(len(self.engine.turns), 2)
        self.assertIn('--session-id', self.engine.turns[0])
        self.assertIn('--resume', self.engine.turns[1])
        self.assertEqual(self.engine.turns[0][-2], self.engine.turns[1][-2])
        self.assertEqual(self.engine.containers, {})
        self.assertEqual(list(self.slots.iterdir()), [])
        self.assertEqual(self.review()['result'], 'recall-and-isolation-observed')
        self.assertFalse(self.review()['production_certification'])
        with self.assertRaises(FileExistsError):
            self.execute()  # Existing binding consumes the run, before any new turn.
        self.assertEqual(len(self.engine.turns), 2)

    def test_failed_first_turn_never_admits_second(self):
        for fault in ('session', 'model', 'running', 'writable-input'):
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as directory:
                root = Path(directory) / 'run'
                root.mkdir()
                slots = Path(directory) / 'slots'
                slots.mkdir()
                engine = FakeEngine()
                engine.fault = fault
                with self.assertRaises(q.Refusal):
                    q.execute(root, slots, self.digest, engine)
                self.assertLessEqual(len(engine.turns), 1)
                self.assertFalse((root / 'turn-2').exists())
                self.assertTrue(all(r['confirmed'] for r in q.cleanup(engine, slots)))

    def test_wrong_recall_cannot_publish_observation(self):
        self.engine.fault = 'recall'
        with self.assertRaisesRegex(q.Refusal, 'recall-mismatch'):
            self.execute()
        self.assertFalse((self.root / 'observed.json').exists())
        self.assertEqual(len(self.engine.turns), 2)

    def test_review_refuses_missing_or_changed_evidence(self):
        self.complete()
        cases = [('transfer.json', lambda x: dict(x, sha256='0'*64)),
                 ('chronology.json', lambda x: [x[0],x[2],x[1],x[3]]),
                 ('initial-home-2.json', lambda x: dict(x, cache='unlisted')),
                 ('binding.json', lambda x: dict(x, manifest='0'*64)),
                 ('request-2.json', lambda x: dict(x, session=str(__import__('uuid').uuid4()))),
                 ('completion.json', lambda x: dict(x, elapsed_seconds=601)),
                 ('runtime-after-1.json', lambda x: {**x, 'State': {**x['State'], 'Running': True}})]
        for name, change in cases:
            path = self.root / name
            original = path.read_bytes()
            path.write_bytes(q.encoded(change(q.decoded(original))))
            with self.subTest(name=name), self.assertRaises(q.Refusal):
                self.review()
            path.write_bytes(original)
        path = self.root / 'provider-2.json'
        path.unlink()
        with self.assertRaises(FileNotFoundError):
            self.review()

    def test_review_rechecks_both_raw_model_sets_and_conflicting_direct_fields(self):
        self.complete()
        for turn in (1, 2):
            path = self.root / ('provider-' + str(turn) + '.json')
            original = path.read_bytes()
            doc = q.decoded(original)
            for change in ({'modelUsage': {'claude-opus-5': {}}},
                           {'modelUsage': {**doc['modelUsage'], 'unknown': {}}},
                           {'model': 'claude-haiku-4-5-20251001'}):
                path.write_bytes(q.encoded(dict(doc, **change)))
                with self.subTest(turn=turn, change=change), self.assertRaises(q.Refusal):
                    self.review()
                path.write_bytes(original)
        self.assertEqual(self.review()['experiment']['model_attribution'], 'unestablished')

    def test_session_selection_rejects_link_and_alias_and_unknown_home(self):
        session = str(__import__('uuid').uuid4())
        place = q.prepare(self.root, 1, session)
        home = place / 'home'
        path = home / q.session_path(session)
        path.parent.mkdir(parents=True)
        external = self.root / 'external'
        q.put(external, b'private')
        path.symlink_to(external)
        with self.assertRaises(OSError):
            q.session_bytes(home, session)
        path.unlink()
        os.link(external, path)
        with self.assertRaisesRegex(q.Refusal, 'session-file'):
            q.session_bytes(home, session)
        with self.assertRaisesRegex(q.Refusal, 'initial-home-extra'):
            q.initial_home(home, session, None)
        with self.assertRaisesRegex(q.Refusal, 'prepare-turn'):
            q.prepare(self.root, 3, session, b'state')

    def test_worker_rejects_third_turn_before_provider(self):
        request = self.root / 'request.json'
        q.save(request, {'run': q.RUN, 'attempt': q.RUN+'-turn-3', 'turn': 3, 'session': str(__import__('uuid').uuid4()), 'prompt': 'bad'})
        with mock.patch.object(q, 'invoke') as provider, self.assertRaisesRegex(q.Refusal, 'request-binding'):
            q.worker(request, call=provider)
        provider.assert_not_called()

    def test_process_timeout_and_output_bound(self):
        began = time.monotonic()
        with self.assertRaisesRegex(q.Refusal, 'process-timeout'):
            q.invoke([sys.executable, '-c', 'import time;time.sleep(10)'], seconds=.1, env=os.environ)
        self.assertLess(time.monotonic()-began, 3)
        with self.assertRaisesRegex(q.Refusal, 'process-output-bound'):
            q.invoke([sys.executable, '-c', 'import sys;sys.stdout.write("x"*3000000)'], seconds=2, env=os.environ)

    def test_supervisor_timeout_cleanup_failure_and_exclusive_reservation(self):
        def stalled(*args):
            os.setsid()
            time.sleep(10)
        self.root.rmdir()
        self.slots.rmdir()
        bounds = dict(q.BOUNDS, active_seconds=.05, total_seconds=10)
        with mock.patch.object(q, 'ROOT', self.root), mock.patch.object(q, 'audit'), mock.patch.object(q, 'child', stalled), mock.patch.object(q, 'BOUNDS', bounds), mock.patch.object(q, 'cleanup', return_value=[{'attempt': 'test', 'confirmed': False}]) as cleanup, contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(q.run(self.digest), 1)
            completion = q.decoded(q.read(self.root / 'completion.json'))
            self.assertTrue(completion['interrupted'])
            self.assertEqual(completion['outcome'], 'failed')
            cleanup.assert_called_once()
            with self.assertRaises(FileExistsError):
                q.run(self.digest)
            cleanup.assert_called_once()



class Package(unittest.TestCase):
    def test_exact_mixed_usage_with_absent_or_matching_direct_model(self):
        session = str(__import__('uuid').uuid4())
        self.assertEqual(q.MODEL, 'claude-opus-5')
        expected = ['claude-haiku-4-5-20251001', 'claude-opus-5']
        self.assertEqual(q.MODEL_ACCEPTANCE['usage_models'], expected)
        for turn in (1, 2):
            arguments = q.argv(session, turn, 'text')
            self.assertEqual(arguments[arguments.index('--model')+1], 'claude-opus-5')
        for direct in (False, True):
            for answer in ('READY', 'RECALL:' + 'a' * 32):
                with self.subTest(direct=direct, answer=answer):
                    good = self.document(session, answer)
                    if direct:
                        good['model'] = q.MODEL
                    result = q.terminal(q.encoded(good), session, answer)
                    self.assertEqual(result['experiment'], q.MODEL_ACCEPTANCE)
                    self.assertEqual(result['experiment']['model_attribution'], 'unestablished')
                    self.assertIsNone(result['strict_terminal']['actual_model'])
                    self.assertEqual(result['strict_terminal']['model_usage_diagnostic'], 'expected-plus-other')
                    self.assertTrue(q.contract().valid_terminal(result['strict_terminal'], session))

    @staticmethod
    def document(session, answer='READY'):
        return {'type': 'result', 'subtype': 'success', 'is_error': False,
                'session_id': session, 'result': answer,
                'modelUsage': {'claude-opus-5': {}, 'claude-haiku-4-5-20251001': {}}}

    def test_missing_unknown_and_malformed_usage_rejected_even_with_direct_opus(self):
        session = str(__import__('uuid').uuid4())
        cases = [None, [], 'models', True, {}, {'claude-opus-5': {}},
                 {'claude-haiku-4-5-20251001': {}}, {'other': {}},
                 {'claude-opus-5': {}, 'claude-haiku-4-5': {}},
                 {'claude-opus-5': {}, 'claude-haiku-4-5-20251001': {}, 'unknown': {}}]
        for usage in cases:
            for direct in (False, True):
                with self.subTest(usage=usage, direct=direct), self.assertRaisesRegex(q.Refusal, 'mixed-model-set'):
                    doc = self.document(session)
                    doc['modelUsage'] = usage
                    if direct:
                        doc['model'] = q.MODEL
                    q.terminal(q.encoded(doc), session, 'READY')
        doc = self.document(session)
        del doc['modelUsage']
        doc['model'] = q.MODEL
        with self.assertRaisesRegex(q.Refusal, 'mixed-model-set'):
            q.terminal(q.encoded(doc), session, 'READY')

    def test_conflicting_direct_model_rejected(self):
        session = str(__import__('uuid').uuid4())
        for model in (None, False, 1, [], {}, 'opus', 'claude-fable-5', 'claude-opus-4-8', 'claude-haiku-4-5-20251001'):
            with self.subTest(model=model), self.assertRaisesRegex(q.Refusal, 'direct-model-conflict'):
                q.terminal(q.encoded(dict(self.document(session), model=model)), session, 'READY')

    def test_exact_terminal_session_and_answer_requirements_preserved(self):
        session = str(__import__('uuid').uuid4())
        for change in ({'type':'other'}, {'subtype':'error'}, {'is_error':True}, {'is_error':0},
                       {'session_id':'wrong'}, {'session_id':None}, {'result':'READY\n'},
                       {'result':'wrong'}, {'result':None}):
            with self.subTest(change=change), self.assertRaises(q.Refusal):
                q.terminal(q.encoded(dict(self.document(session), **change)), session, 'READY')
        for key in ('type', 'subtype', 'is_error', 'session_id', 'result'):
            doc = self.document(session)
            del doc[key]
            with self.subTest(missing=key), self.assertRaises(q.Refusal):
                q.terminal(q.encoded(doc), session, 'READY')

    def test_duplicate_usage_keys_and_nonobject_terminal_refuse(self):
        session = str(__import__('uuid').uuid4())
        good = q.encoded(self.document(session))
        duplicate = good.replace(b'"claude-opus-5":{}', b'"claude-opus-5":{},"claude-opus-5":{}')
        with self.assertRaisesRegex(q.Refusal, 'json-duplicate'):
            q.terminal(duplicate, session, 'READY')
        for raw in (b'[]', b'null', b'false'):
            with self.subTest(raw=raw), self.assertRaises(Exception):
                q.terminal(raw, session, 'READY')

    def test_historical_packets_and_strict_contract_preserved(self):
        parent = Path(q.__file__).parent.parent
        for package, manifest_name, digest in (
                (parent, 'CANARY-MANIFEST-234516.json', '1ad6342ab05ad765f51d251190f2a48591e15164b1170b27399ee1e63f77f62d'),
                (parent/'opus-234686', 'CANARY-MANIFEST-234686.json', '80c797de553a52dd3d78c5d36e040f3c94c6dfb26a80e9b2bb2b23df6ac6dee3')):
            raw = q.read(package/manifest_name)
            self.assertEqual(q.sha(raw), digest)
            manifest = q.decoded(raw)
            for name, expected in {**manifest['files'], **manifest['supporting_evidence']}.items():
                self.assertEqual(q.sha(q.read(package/name)), expected)
        self.assertEqual(q.read(Path(q.__file__).parent/'evidence/qualification_contract.py'),
                         q.read(parent/'opus-234686/evidence/qualification_contract.py'))

    def test_manifest_and_drift_gate(self):
        digest = q.sha(q.read(q.MANIFEST))
        self.assertEqual(q.audit(digest)['run'], q.RUN)
        with self.assertRaisesRegex(q.Refusal, 'manifest-digest'):
            q.audit('0'*64)


if __name__ == '__main__':
    unittest.main()
