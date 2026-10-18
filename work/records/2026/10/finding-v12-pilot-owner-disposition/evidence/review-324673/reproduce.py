"""Public disposable fixture: repeat the command after citation refusal."""
import json
from tests.tools.test_disposition_command import Fixture, WORK, RECORD

f = Fixture()
f.setUp()
try:
    f.accepted_candidate()
    assert f.approve()[0] == 0
    authority = f.authority()
    authority.record_dossier_evidence(
        WORK, RECORD, 'sha256:' + '9' * 64, operation_id='op-cite-1')
    authority.dispose()
    f.write_record()
    results = []
    for number in range(2):
        code, out, err = f.integrated()
        results.append({'try': number + 1, 'exit': code,
                        'answer': json.loads(out) if out else None,
                        'stderr': err})
    print(json.dumps(results, indent=2))
finally:
    f.doCleanups()
