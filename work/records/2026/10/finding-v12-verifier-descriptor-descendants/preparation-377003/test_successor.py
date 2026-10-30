"""Composed deterministic runner tests; no engine subprocess is invoked."""
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('base_fixture', HERE / 'test_engine_proof.py')
b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)
m = b.m


class Composed(unittest.TestCase):
    def run_case(self, hook=None, case='success'):
        with tempfile.TemporaryDirectory(prefix='w325695-successor-') as root:
            receipt = Path(root) / 'receipt'
            fake = b.Fake(case, receipt)
            def engine(argv, **kw):
                phase = json.loads((receipt / 'state.json').read_text())['calls'][-1]['phase']
                response = hook(fake, phase, argv, kw) if hook else None
                return response if response is not None else fake(argv, **kw)
            proof = m.Proof(dict(b.SELECTION), json.loads(b.LAYOUT), b.PAYLOAD.decode(), receipt, run=engine, clock=fake.clock, sleep=fake.sleep)
            result = proof.execute()
            raw = (receipt / 'state.json').read_text()
            self.assertEqual(json.loads(raw), result)
            self.assertNotIn('SECRET_RESPONSE', raw)
            self.assertLess(len(raw), 60000)
            return result, fake

    def answer(self, argv, status, out, err):
        return subprocess.CompletedProcess(argv, status, out, err)

    def test_supported_absence_at_both_consumers(self):
        for prefix in ('Error: No such object: ', 'error: no such object: ', 'ERROR: NO SUCH CONTAINER: ', 'Error response from daemon: No such container: '):
            for stdout in ('', '[]\n', '[ ]'):
                with self.subTest(prefix=prefix, stdout=stdout):
                    def hook(fake, phase, argv, kw):
                        if phase in ('preflight', 'confirm-absence'):
                            return self.answer(argv, 1, stdout, prefix + argv[-1] + '\n')
                    result, _ = self.run_case(hook)
                    self.assertTrue(result['success'])
                    self.assertEqual([x['classification'] for x in result['inspections'] if x['phase'] in ('preflight', 'confirm-absence')], ['absent', 'absent'])

    def test_uncertain_responses_at_both_consumers(self):
        variants = [
            (1, '[]', lambda ref: 'error: no such object: ' + ref + '-other'),
            (1, '[]', lambda ref: 'error: no such object: ' + ref.upper()),
            (1, '[]', lambda ref: 'prefix error: no such object: ' + ref),
            (1, '[]', lambda ref: 'error: no such object: ' + ref + '\nI/O error SECRET_RESPONSE'),
            (1, '[]', lambda ref: 'error: no such object: ' + ref + '\nerror: no such object: ' + ref),
            (0, '[]', lambda ref: ''),
            (0, '[]', lambda ref: 'I/O error SECRET_RESPONSE'),
            (1, '', lambda ref: 'permission denied SECRET_RESPONSE'),
            (1, '', lambda ref: 'Cannot connect to daemon SECRET_RESPONSE'),
            (1, 'other output SECRET_RESPONSE', lambda ref: 'error: no such object: ' + ref),
            (0, '[{}]', lambda ref: ''),
            (0, '{}', lambda ref: ''),
            (0, 'not JSON SECRET_RESPONSE', lambda ref: ''),
            (2, '[]', lambda ref: 'error: no such object: ' + ref),
            (0, 'x' * 70000, lambda ref: ''),
        ]
        for phase in ('preflight', 'confirm-absence'):
            for i, (status, out, error) in enumerate(variants):
                with self.subTest(phase=phase, case=i):
                    def hook(fake, current, argv, kw):
                        if current == phase:
                            return self.answer(argv, status, out, error(argv[-1]))
                    result, fake = self.run_case(hook)
                    self.assertFalse(result['success'])
                    self.assertFalse(result['exact_absence'])
                    self.assertEqual(next(x for x in result['inspections'] if x['phase'] == phase)['classification'], 'uncertain')
                    if phase == 'preflight':
                        self.assertFalse(result['create_intent'])
                        self.assertFalse(fake.calls)
                    else:
                        self.assertTrue(result['owned'])
                        self.assertIn('cleanup_uncertainty', result)

    def test_occupied_name_is_never_acquired_or_removed(self):
        def hook(fake, phase, argv, kw):
            if phase == 'preflight':
                fake.created = True
                return fake(argv, **kw)
        result, fake = self.run_case(hook)
        self.assertFalse(result['create_intent'])
        self.assertFalse(result['owned'])
        self.assertIsNone(result['container_id'])
        self.assertFalse(result['success'])
        self.assertEqual([x[0] for x in fake.calls], ['inspect'])

    def test_strict_identity_before_start_or_removal(self):
        mutations = [lambda obj: obj.update(Id='c'*64), lambda obj: obj.update(Id='abc'),
                     lambda obj: obj.update(Name='/somebody-else'), lambda obj: obj.update(Image='sha256:'+'d'*64),
                     lambda obj: obj['Config'].update(User='1:2'), lambda obj: obj['Config']['Labels'].update({'baton.proof':'foreign'}),
                     lambda obj: obj.update(Config={}), lambda obj: obj.update(Name='/W325695-proof-test')]
        for mutate in mutations:
            with self.subTest(mutation=mutate):
                def hook(fake, phase, argv, kw):
                    if phase in ('acquire-created', 'reconcile-create'):
                        response = fake(argv, **kw)
                        obj = json.loads(response.stdout)[0]
                        mutate(obj)
                        return self.answer(argv, 0, json.dumps([obj]), '')
                result, fake = self.run_case(hook)
                self.assertFalse(result['owned'])
                self.assertFalse(result['exact_absence'])
                self.assertFalse(any(op in ('start', 'rm') for op, _ in fake.calls))

    def test_present_object_with_mixed_stderr_or_duplicate_identity_refuses(self):
        for mixed in (True, False):
            def hook(fake, phase, argv, kw):
                if phase in ('acquire-created', 'reconcile-create'):
                    response = fake(argv, **kw)
                    out = response.stdout if mixed else response.stdout.replace('"Id":', '"Id":"' + b.CID + '","Id":')
                    return self.answer(argv, 0, out, 'SECRET_RESPONSE' if mixed else '')
            result, fake = self.run_case(hook)
            self.assertFalse(result['owned'])
            self.assertFalse(any(op == 'rm' for op, _ in fake.calls))

    def test_lost_create_and_later_exact_absence_stays_uncertain(self):
        result, fake = self.run_case(case='create-unobserved')
        self.assertTrue(result['create_intent'])
        self.assertFalse(result['exact_absence'])
        self.assertIsNone(result['container_id'])
        self.assertIn('creation_uncertainty', result)
        self.assertEqual(result['inspections'][-1]['classification'], 'absent')
        self.assertFalse(any(op == 'rm' for op, _ in fake.calls))

    def test_lost_create_can_reconcile_exact_owned_object_only(self):
        result, fake = self.run_case(case='create-loss')
        self.assertTrue(result['owned'])
        self.assertTrue(result['exact_absence'])
        self.assertFalse(result['success'])
        self.assertIn('rm', [op for op, _ in fake.calls])

    def test_remove_failure_still_observes_absence_independently(self):
        def hook(fake, phase, argv, kw):
            if phase == 'remove':
                fake.removed = True
                raise subprocess.TimeoutExpired(argv, kw['timeout'], output='SECRET_RESPONSE')
        result, _ = self.run_case(hook)
        self.assertTrue(result['exact_absence'])
        self.assertFalse(result['success'])
        self.assertEqual(result['inspections'][-1]['phase'], 'confirm-absence')
        self.assertTrue(any(e['phase'] == 'remove' for e in result['errors']))

    def test_full_work_deadline_preserves_cleanup_reserve(self):
        def hook(fake, phase, argv, kw):
            if phase == 'receipt':
                fake.now = 80
                raise subprocess.TimeoutExpired(argv, kw['timeout'])
            if phase == 'remove':
                self.assertEqual(fake.now, 80)
                self.assertEqual(kw['timeout'], 25)
                fake.now += 25
                raise subprocess.TimeoutExpired(argv, kw['timeout'])
            if phase == 'confirm-absence':
                self.assertLessEqual(kw['timeout'], 15)
                fake.now += kw['timeout']
                return self.answer(argv, 1, '[]', 'error: no such object: ' + argv[-1])
        result, fake = self.run_case(hook)
        self.assertFalse(result['success'])
        self.assertTrue(result['exact_absence'])
        self.assertLessEqual(fake.now, 120)
        self.assertEqual(result['timeout_phase'], 'remove')

    def test_sensitive_payload_extras_are_not_persisted(self):
        def hook(fake, phase, argv, kw):
            if phase == 'receipt':
                response = fake(argv, **kw)
                obj = json.loads(response.stdout)
                obj['unexpected'] = 'SECRET_RESPONSE'
                return self.answer(argv, 0, json.dumps(obj), '')
        result, _ = self.run_case(hook)
        self.assertTrue(result['success'])
        self.assertNotIn('unexpected', result['payload'])

    def test_capacity_metrics_are_retained_without_untrusted_extras(self):
        for bad in (False, True):
            def hook(fake, phase, argv, kw):
                if phase == 'receipt':
                    response = fake(argv, **kw)
                    obj = json.loads(response.stdout)
                    obj['capacity'] = {key: {'bytes_written': root['bytes'], 'configured_bytes': root['bytes'], 'errno': 'ENOSPC', 'extra': 'SECRET_RESPONSE'} for key, root in json.loads(b.LAYOUT)['roots'].items()}
                    if bad:
                        obj['capacity']['HOME']['bytes_written'] = 'SECRET_RESPONSE'
                    return self.answer(argv, 0, json.dumps(obj), '')
            result, _ = self.run_case(hook)
            self.assertEqual(result['success'], not bad)
            if not bad:
                self.assertEqual(len(result['payload']['capacity']), 4)
                self.assertEqual(result['payload']['descendant_started'], 10)

    def test_used_receipt_refuses_before_any_call(self):
        with tempfile.TemporaryDirectory() as root:
            receipt = Path(root) / 'receipt'
            receipt.mkdir()
            (receipt / 'partial').write_text('preserved')
            with self.assertRaises(FileExistsError):
                m.Proof(dict(b.SELECTION), {}, '', receipt, run=lambda *a, **k: self.fail('engine invoked'))
            self.assertEqual((receipt / 'partial').read_text(), 'preserved')


if __name__ == '__main__':
    unittest.main(verbosity=2)
