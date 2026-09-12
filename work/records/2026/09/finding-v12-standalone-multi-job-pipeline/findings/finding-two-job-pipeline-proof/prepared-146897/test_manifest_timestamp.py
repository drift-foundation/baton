"""Actual frozen-schema regressions; emitted files are offline fixtures only.

No Authority is opened or created. No host validate/render gate is bypassed:
only the document constructor receives explicitly synthetic run6-shaped facts.
"""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from baton_v12.contracts.errors import ContractRefusal
from baton_v12.contracts.manifest import check_manifest_structure
import deployment
from offline_fixture import documents_in_fixture

HERE = Path(__file__).resolve().parent
ORIGINAL = '2026-09-11T15:06:04Z'
CORRECTED = '2026-09-11T19:51:48.071Z'


class ManifestTimestampTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.retained = Path(tempfile.mkdtemp(prefix='w71879-146897-schema-fixtures-'))
        print('Retained offline schema fixture root:', cls.retained, flush=True)
        (cls.retained / 'FIXTURE-ONLY.txt').write_text('Synthetic constructor parameters and document outputs. Not host validation or final run inputs. No Authority/model/runtime created.\n')
        cls.images = json.loads((HERE / 'candidate-images.json').read_text())
        cls.facts = {'authority_uuid': deployment.UUID, 'policy_generation': 24,
                     'principals': {actor: 'principal:w71879-run6-' + actor for actor in deployment.ACTORS},
                     'fixture_scope': 'synthetic offline constructor parameters, not public Authority observations'}
        cls.good = cls.retained / 'valid'
        cls.hashes = documents_in_fixture(cls.good, cls.images, cls.facts)

    def test_candidate_constructor_emits_all_six_valid_manifests(self):
        self.assertEqual(CORRECTED, deployment.CREATED)
        files = [p for p in self.good.rglob('*') if p.is_file()]
        self.assertEqual(33, len(files))
        manifests = sorted((self.good / 'manifests').glob('*.json'))
        self.assertEqual(['a', 'approval', 'b', 'integrator', 'review', 'verification'], [p.stem for p in manifests])
        for path in manifests:
            with self.subTest(manifest=path.name):
                given = json.loads(path.read_text())
                self.assertEqual(CORRECTED, given['created_at'])
                self.assertEqual(given, check_manifest_structure(given, 'inputManifest'))
        self.assertEqual(deployment.sha(self.good / 'stage-execution.json'), self.hashes['configuration'])
        self.assertEqual(deployment.sha(self.good / 'submission.json'), self.hashes['submission'])

    def test_old_value_is_rejected_by_real_frozen_manifest_validator(self):
        for path in sorted((self.good / 'manifests').glob('*.json')):
            with self.subTest(manifest=path.name):
                given = deepcopy(json.loads(path.read_text()))
                given['created_at'] = ORIGINAL
                given.pop('manifest_digest')
                given['manifest_digest'] = deployment.digest(given)
                with self.assertRaisesRegex(ContractRefusal, 'created_at.*pattern'):
                    check_manifest_structure(given, 'inputManifest')

    def test_original_constant_refuses_through_actual_constructor(self):
        # Only the value under test is substituted; validators are never mocked.
        with mock.patch.object(deployment, 'CREATED', ORIGINAL):
            with self.assertRaisesRegex(ContractRefusal, 'created_at.*pattern'):
                documents_in_fixture(self.retained / 'invalid', self.images, self.facts)
        self.assertEqual(CORRECTED, deployment.CREATED)
        self.assertFalse((self.retained / 'invalid/stage-execution.json').exists())


if __name__ == '__main__':
    unittest.main(verbosity=2)
