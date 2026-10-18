import json
from pathlib import Path
from tests.tools.test_disposition_command import Fixture
results = {}
f = Fixture(); f.setUp()
try:
    f.delivered()
    f.write_record(f.record_document(notes='later drift'))
    code, out, err = f.integrated(**{'--commit': 'a' * 40})
    results['changed_commit_after_drift'] = {'exit': code, 'answer': json.loads(out), 'stderr': err, 'citations': len(f.citations())}
finally:
    f.doCleanups()
f = Fixture(); f.setUp()
try:
    f.delivered()
    assert f.close()[0] == 0
    expect = Path(f.repo) / 'changed-assignment.json'
    expect.write_text(json.dumps(f.assignment))
    code, out, err = f.close(**{'--expect-assignment': str(expect)})
    results['changed_close_assignment'] = {'exit': code, 'answer': json.loads(out), 'stderr': err}
finally:
    f.doCleanups()
print(json.dumps(results, indent=2))
