"""Disposable public-API fixture: prior citation is not validated command evidence."""
import json
from tests.tools.test_disposition_command import Fixture, WORK, RECORD

fixture = Fixture()
fixture.setUp()
try:
    fixture.accepted_candidate()
    assert fixture.approve()[0] == 0
    authority = fixture.authority()
    prior = authority.record_dossier_evidence(
        WORK, RECORD, 'sha256:' + '9' * 64, operation_id='op-cite-1')
    authority.dispose()
    # No human integration file has ever existed in this fixture.
    code, out, err = fixture.integrated(**{'--commit': 'a' * 40})
    print(json.dumps({'prior_citation': prior, 'exit': code,
                      'answer': json.loads(out), 'stderr': err}, indent=2))
finally:
    fixture.doCleanups()
