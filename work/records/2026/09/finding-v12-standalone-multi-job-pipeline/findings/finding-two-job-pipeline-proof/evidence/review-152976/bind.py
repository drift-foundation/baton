"""Create genuine final reviewer bindings only after recorded independent acceptance."""
from pathlib import Path
import hashlib
import json
import os
import time

REPO = Path('/home/sl/src/baton')
HERE = Path(__file__).resolve().parent
PROOF = HERE.parent.parent
PACKAGE = PROOF / 'prepared-152826'
REVIEW = PROOF / 'review-2026-09-12T13-55-45Z.md'
MANIFEST = PROOF / 'evidence/run10-freeze-152932/candidate-manifest.json'
def sha(path):
    return 'sha256:' + hashlib.sha256(path.read_bytes()).hexdigest()
started = time.monotonic()
assert REVIEW.is_file()
verified = json.loads((HERE / 'verification.json').read_text())
assert sha(MANIFEST) == verified['manifest_sha256'] == 'sha256:4299b6db0997fdf26ceeaeb32fa3ebc88dbc73d8b43d8fab7dca4b6c2e484f21'
manifest = json.loads(MANIFEST.read_text())
bindings = {str(REPO / name): value['sha256'] for name, value in manifest['files'].items()}
bindings[str(MANIFEST)] = sha(MANIFEST)
assert len(bindings) == 359
for path, expected in bindings.items():
    assert sha(Path(path)) == expected, path
images = json.loads((PACKAGE / 'candidate-images.json').read_text())
assert images == {'provider':'sha256:2e222e4cf33ff7f52b2048ae1a9c0a2139707e36943328fdd8674b84937f2b13', 'integration':'sha256:d739fefe6bf885db8ad79122611316f3fbe8b393fa4c821933388e8cd15e2533'}
config = {'stage-execution.json':'sha256:401f13768132ab7d47650f9afe8bec59068d31d017298c8ace0faf84dcace84e', 'submission.json':'sha256:c9ef35157bf768aa09c481cda2fe6aa4b5aaf773ace34154e4db4301907d6e7d'}
for name, expected in config.items():
    assert sha(PACKAGE / 'frozen-config' / name) == expected
for name in manifest['five_helpers']:
    assert bindings[str(PACKAGE / name)] == manifest['five_helpers'][name]
for name in ('selected-images.json','execution-review.json'):
    assert not os.path.lexists(PACKAGE / name)
review = {'reviewer':'baton.codex', 'reviewed_at':'2026-09-12T13:55:45Z',
          'review_locator':'baton:' + str(REVIEW.relative_to(REPO)), 'verdict':'accepted',
          'execution_authorized':True,
          'authorization_note':'Owner152823, reaffirmed152925, authorizes exactly ONE OPERATOR attempt after required actual input checks and genuine bindings, now complete. No agent model execution or automatic retry.',
          'config_files':config, 'runtime_profile_digest':'sha256:34ff1ebdcec8ddc607109be4d6600595e650360b6d3773b95cf124ebef3b1f69',
          'images':images, 'reviewed_files':bindings}
for name, document in [('selected-images.json',images), ('execution-review.json',review)]:
    with (PACKAGE / name).open('x') as output:
        output.write(json.dumps(document,indent=2,sort_keys=True)+'\n')
    assert json.loads((PACKAGE / name).read_text()) == document
observed = json.loads((PACKAGE / 'execution-review.json').read_text())
for name, expected in observed['reviewed_files'].items():
    assert sha(Path(name)) == expected, name
report = {'claim':152976, 'reviewed_files':len(bindings), 'all_five_helpers_bound':True,
          'actual_inputs_bound':sum('/prepared-152826/frozen-config/' in name for name in bindings),
          'markers':{name:sha(PACKAGE / name) for name in ('selected-images.json','execution-review.json')},
          'review_locator':review['review_locator'], 'seconds':time.monotonic()-started}
assert report['actual_inputs_bound'] == 33
(HERE / 'bindings.json').write_text(json.dumps(report,indent=2)+'\n')
cost = json.loads((HERE / 'spending.json').read_text())
cost['binding_seconds'] = report['seconds']
cost['current_listed_seconds'] += report['seconds']
cost['cumulative_listed_preparation_seconds'] += report['seconds']
(HERE / 'spending.json').write_text(json.dumps(cost,indent=2)+'\n')
print(json.dumps({'bindings':report,'spending':cost},indent=2))
