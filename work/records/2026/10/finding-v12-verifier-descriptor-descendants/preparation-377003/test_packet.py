"""Packet entry checks over disposable copies; engine is always injected."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import types
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('packet', HERE / 'packet.py')
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)


class Packet(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='w325695-packet-')
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.copy = root / HERE.name
        shutil.copytree(HERE, self.copy, ignore=shutil.ignore_patterns('__pycache__', 'ENGINE-RECEIPT'))
        # Only read these immutable inputs; each test writes its own copy.
        for name in ('preparation-376414', 'preparation-376852'):
            (root / name).symlink_to(HERE.parent / name, target_is_directory=True)
        held = patch.object(p, 'HERE', self.copy)
        held.start()
        self.addCleanup(held.stop)

    def test_check_and_unselected_run_never_invoke_engine(self):
        with patch.object(subprocess, 'run', side_effect=AssertionError('engine forbidden')):
            self.assertTrue(p.check()['receipt_unused'])
            with contextlib.redirect_stderr(io.StringIO()):
                for args in (['run'], ['run', '--owner-selected', '--selection-sha256', '0'*64]):
                    with self.assertRaises(SystemExit):
                        p.main(args)
        self.assertFalse((self.copy / 'ENGINE-RECEIPT').exists())

    def test_changed_input_and_used_receipt_refuse(self):
        target = self.copy / 'LAYOUT.json'
        original = target.read_bytes()
        target.write_bytes(original + b' ')
        with self.assertRaises(ValueError):
            p.check()
        target.write_bytes(original)
        (self.copy / 'ENGINE-RECEIPT').mkdir()
        with self.assertRaises(ValueError):
            p.check()

    def test_selected_entry_composes_runner_and_spends_receipt_once(self):
        real = p.runner()
        selected = json.loads((self.copy / 'SELECTION.json').read_text())
        cid = 'a'*64
        calls = []
        removed = False
        def engine(argv, **kw):
            nonlocal removed
            op = argv[1]
            calls.append(op)
            reply = lambda code=0, out='', err='': subprocess.CompletedProcess(argv, code, out, err)
            if op == 'inspect':
                if len(calls) == 1 or removed:
                    return reply(1, '[]', 'error: no such object: ' + argv[-1])
                return reply(out=json.dumps([{'Id':cid, 'Name':'/'+selected['proof_id'], 'Image':selected['image'], 'Config':{'User':f"{selected['uid']}:{selected['gid']}", 'Labels':{'baton.proof':selected['proof_id']}}, 'State':{'Running':True}}]))
            if op == 'create':
                self.assertIn(selected['image'], argv)
                return reply(out=cid)
            if op == 'start':
                return reply()
            if op == 'logs':
                return reply(out=json.dumps({key:'passed' for key in ('mount_binding','ordinary_grandchild','nested_validator','image_bytes','product_mount_checks','capacity_enospc')}))
            if op == 'rm':
                self.assertEqual(argv[-1], cid)
                removed = True
                return reply()
            self.fail('unexpected engine command')
        def construct(*args):
            return real.Proof(*args, run=engine)
        fake_module = types.SimpleNamespace(validate=real.validate, Proof=construct)
        with patch.object(p, 'runner', return_value=fake_module):
            self.assertEqual(p.main(['run', '--owner-selected', '--selection-sha256', p.sha(self.copy / 'SELECTION.json')]), 0)
            prior = list(calls)
            with self.assertRaises(ValueError):
                p.main(['run', '--owner-selected', '--selection-sha256', p.sha(self.copy / 'SELECTION.json')])
            self.assertEqual(calls, prior)
        state = json.loads((self.copy / 'ENGINE-RECEIPT/state.json').read_text())
        self.assertTrue(state['success'])
        self.assertEqual(state['selection'], selected)
        self.assertEqual(calls, ['inspect','create','inspect','start','logs','inspect','rm','inspect'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
