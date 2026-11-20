import io
import json
from pathlib import Path
from unittest import mock
import unittest
from tools import bootstrap
from tests.tools.test_connected_creation import TheNativeRoutingThroughTheRealInstaller as Fixture

class ReviewProbe(Fixture):
    def test_both_addresses_refuse_before_effect_functions_in_both_forms(self):
        for field in ('reviewer', 'decision_recipient'):
            for destination in (True, False):
                with self.subTest(field=field, destination=destination):
                    routing=dict(self.ROUTING, **{field: 'not-an-address'})
                    document=self.document(jobs=[], native_handoff_routing=routing)
                    inputs=Path(self.root)/'review-inputs.json'
                    inputs.write_text(json.dumps(document))
                    argv=['--inputs',str(inputs)]
                    if destination:
                        argv += ['--destination', self.state, '--distro', self.stand_in_runtime()]
                    with mock.patch.object(bootstrap,'admit') as admit, mock.patch.object(bootstrap,'prepare_repositories') as repos, mock.patch.object(bootstrap,'prepare_prerequisites') as roots, mock.patch.object(bootstrap,'prepare_worker_sources') as workers, mock.patch.object(bootstrap,'prepare') as prepare:
                        out=io.StringIO()
                        self.assertEqual(bootstrap.main(argv,stream=out),2,out.getvalue())
                        self.assertIn('a participant is team.member',out.getvalue())
                        for effect in (admit,repos,roots,workers,prepare): effect.assert_not_called()

    def test_invalid_reviewer_repeat_preserves_installed_input_and_policy(self):
        self.installed(jobs=[], line_declared_base='a'*40,canonical_target_id='target-1',native_handoff_routing=dict(self.ROUTING))
        inputs=Path(self.state)/'install-inputs.json'
        before=inputs.read_bytes()
        policy=self.authority().native_routing()
        document=self.install_document()
        document['native_handoff_routing']=dict(self.ROUTING,reviewer='not-an-address')
        attempt=Path(self.root)/'review-repeat.json'; attempt.write_text(json.dumps(document))
        out=io.StringIO()
        self.assertEqual(bootstrap.main(['--inputs',str(attempt)],stream=out),2,out.getvalue())
        self.assertEqual(inputs.read_bytes(),before)
        self.assertEqual(self.authority().native_routing(),policy)

if __name__=='__main__':
    suite=unittest.TestSuite(ReviewProbe(name) for name in ('test_both_addresses_refuse_before_effect_functions_in_both_forms','test_invalid_reviewer_repeat_preserves_installed_input_and_policy'))
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(not result.wasSuccessful())
