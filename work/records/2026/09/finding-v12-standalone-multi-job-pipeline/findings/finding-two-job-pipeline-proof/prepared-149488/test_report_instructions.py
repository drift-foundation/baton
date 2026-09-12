"""Offline actual-constructor/prompt/report checks; every report is synthetic.

No Authority, provider, Docker, Git or real result namespace is accessed.
"""
from copy import deepcopy
import json
from pathlib import Path
import re
import tempfile
import unittest

import deployment
from offline_fixture import documents_in_fixture
import integration_contract as contract
import integration_workload as workload

HERE = Path(__file__).resolve().parent


class ReportInstructionsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = Path(tempfile.mkdtemp(prefix='w71879-149488-report-fixtures-'))
        print('Retained synthetic report fixture root:', cls.root, flush=True)
        (cls.root / 'FIXTURE-ONLY.txt').write_text('Synthetic offline documents, prompts and reports. No actual result namespace or execution evidence.\n')
        facts = {'authority_uuid': deployment.UUID, 'policy_generation': 24,
                 'principals': {actor: 'principal:w71879-run8-' + actor for actor in deployment.ACTORS},
                 'fixture_scope': 'synthetic offline facts, not Authority observations'}
        cls.config = cls.root / 'constructor'
        documents_in_fixture(cls.config, json.loads((HERE / 'offline-images.json').read_text()), facts)
        cls.instructions = (cls.config / 'integration-instructions.txt').read_text()
        cls.extension = cls.instructions.split('Provider completion contract', 1)[1]
        cls.rows = [{'path': path, 'operation': 'edit',
                     'base': {'blob': 'c' * 64, 'mode': '100644'},
                     'candidate': {'blob': 'd' * 64, 'mode': '100644'}}
                    for path in ('demo/greeting.py', 'tests/test_greeting.py')]
        cls.operands = {'instructions': cls.instructions.encode(), 'bundle_root': '/input/source',
                        'target_root': '/target', 'report_place': str(cls.root / 'SYNTHETIC-report.json'),
                        'assignment': {'attempt_id': 'synthetic-attempt', 'canonical_target_id': 'synthetic-target',
                                       'entry_id': 'synthetic-entry', 'fence': 1},
                        'assignment_digest': 'sha256:' + 'a' * 64, 'bundle_digest': 'sha256:' + 'b' * 64,
                        'rows': cls.rows, 'authority': [{'path': 'tests/test_greeting.py', 'requires': ['existing-test']}],
                        'scope': ['tests/test_greeting.py'],
                        'documents': [{'output_name': 'findings', 'files': [{'path': 'review.txt'}]}],
                        'verification': ['python3', 'check_greeting.py']}
        cls.prompt = workload.compose_prompt(**cls.operands)
        (cls.root / 'SYNTHETIC-prompt.txt').write_text(cls.prompt)

    def report(self, outcome='imported', phase='verification', code=None, verification=None):
        # Follow the actual-value instruction: take digest strings from the
        # unchanged prompt's exact operands, not a report template's placeholders.
        return {'schema': contract.REPORT_SCHEMA,
                'assignment_digest': re.search(r'The assignment it answers is (sha256:[a-f0-9]{64})\.', self.prompt)[1],
                'bundle_digest': re.search(r'Its measured identity is (sha256:[a-f0-9]{64})\.', self.prompt)[1],
                'outcome': outcome, 'phase': phase,
                'paths': [row['path'] for row in self.rows] if outcome == 'imported' else [],
                'verification': verification, 'code': code}

    def check(self, report):
        return contract.check_report(json.dumps(report).encode())

    def test_actual_composed_instructions_supply_exact_contract_vocabulary(self):
        keys = re.findall(r'^- ([a-z_]+):', self.extension, re.M)
        self.assertEqual(list(contract.REPORT_MEMBERS), keys)
        for key, values in (('outcome', contract.REPORT_OUTCOMES), ('phase', contract.REPORT_PHASES), ('code', contract.REPORT_CODES)):
            text = self.extension.split('- ' + key + ':', 1)[1].split('\n- ', 1)[0]
            self.assertEqual(list(values), json.loads(re.search(r'\[[^]]+\]', text)[0]))
        self.assertIn(str(contract.MAX_REPORT_BYTES), self.extension)
        self.assertIn(str(contract.MAX_PATHS), self.extension)
        for phrase in ('copy the exact digest string', 'including its sha256: prefix',
                       'Never invent either digest', 'Do not put placeholder text in the report',
                       'sorted, unique JSON array', 'paths actually\n  changed',
                       'null if you did not perform verification', 'with exactly argv and status',
                       'Never substitute zero', 'observed integer exit status',
                       'or null if no\n  exit status was obtained', 'end the provider turn',
                       "Do\nnot publish the manager's integration-result", 'Do not start another import or verification attempt'):
            self.assertIn(phrase, self.extension)

    def test_original_full_tasks_and_runtime_guards_remain_exact(self):
        old = (HERE.parent / 'prepared-145397/frozen-config/integration-instructions.txt').read_text()
        self.assertTrue(self.instructions.startswith(old))
        for task in ('a', 'b'):
            self.assertIn(deployment.task_documents()[task]['instructions'], self.prompt)
        old_prompt = workload.compose_prompt(**dict(self.operands, instructions=old.encode()))
        boundary = "-- this runtime's exact operands --"
        self.assertEqual(old_prompt.split(boundary)[1], self.prompt.split(boundary)[1])
        for phrase in ('EVALUATE THE WHOLE CANDIDATE', 'EMPTY authority account is not permission',
                       'Before importing anything', 'Do not change version-control state',
                       'Do not repair permissions', 'run over the target by this runtime'):
            self.assertIn(phrase, self.prompt)
        for phrase in ('before-write scope, review, base, path, type,', 'mode or ownership check',
                       'phase "verification"', 'code\nnull', 'runtime still independently reads back the target'):
            self.assertIn(phrase, self.extension)

    def test_synthetic_success_refusal_and_held_use_real_closed_report_parser(self):
        cases = [self.report(), self.report(verification={'argv': ['python3', 'check_greeting.py'], 'status': 0}),
                 self.report('refused', 'preflight', 'scope-exceeded'),
                 self.report('held', 'import', 'partial-import'),
                 self.report('held', 'verification', 'verification-failed', {'argv': ['python3', 'check_greeting.py'], 'status': 1}),
                 self.report('held', 'verification', 'provider-unable', {'argv': ['python3', 'check_greeting.py'], 'status': None})]
        for i, report in enumerate(cases):
            with self.subTest(case=i):
                self.assertEqual(report, self.check(report))
                (self.root / ('SYNTHETIC-shape-' + str(i) + '.json')).write_text(json.dumps(report))
        for outcome in ('refused', 'held'):
            for code in contract.REPORT_CODES:
                self.assertEqual(code, self.check(self.report(outcome, 'preflight', code))['code'])

    def test_missing_extra_keys_invalid_codes_and_unsorted_paths_are_rejected(self):
        good = self.report()
        invalid = []
        for key in contract.REPORT_MEMBERS:
            report = deepcopy(good); del report[key]; invalid.append(report)
        for change in ({'extra': 'not allowed'}, {'outcome': 'integrated'}, {'phase': 'done'},
                       {'code': 'provider-unable'}, {'outcome': 'held', 'code': None},
                       {'outcome': 'refused', 'code': 'unknown'}, {'paths': list(reversed(good['paths']))},
                       {'paths': [good['paths'][0]] * 2}, {'paths': ['../outside']}):
            invalid.append(dict(good, **change))
        for i, report in enumerate(invalid):
            with self.subTest(case=i), self.assertRaises(contract.BundleRefusal):
                self.check(report)

    def test_verification_preserves_nonzero_null_and_rejects_invalid_shapes(self):
        for status in (0, 1, -9, None):
            value = {'argv': ['python3', 'check_greeting.py'], 'status': status}
            self.assertEqual(value, self.check(self.report('held', 'verification', 'provider-unable', value))['verification'])
        for value in ({}, {'argv': [], 'status': 0}, {'argv': [''], 'status': 0},
                      {'argv': ['check'], 'status': True}, {'argv': ['check'], 'status': '0'},
                      {'argv': ['check'], 'status': 0, 'extra': 'ignored'}):
            with self.subTest(value=value), self.assertRaises(contract.BundleRefusal):
                self.check(self.report(verification=value))

    def test_real_report_reader_correlates_exact_digest_strings(self):
        path = Path(self.operands['report_place'])
        good = self.report()
        expected = {key: self.operands[key] for key in ('assignment_digest', 'bundle_digest')}
        path.write_text(json.dumps(good))
        self.assertEqual(good, workload._report(str(path), expected, self.rows))
        for key in expected:
            bad = dict(good, **{key: 'sha256:' + 'e' * 64})
            path.write_text(json.dumps(bad))
            with self.subTest(key=key), self.assertRaises(workload._Held) as caught:
                workload._report(str(path), expected, self.rows)
            self.assertEqual('report-foreign', caught.exception.reason)
        path.write_text(json.dumps(good))


if __name__ == '__main__':
    unittest.main(verbosity=2)
