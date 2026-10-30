"""Read-only binding verification; never imports, extracts or runs product code."""
from pathlib import Path, PurePosixPath
import hashlib
import json
import subprocess
import tarfile
import time

started = time.monotonic()
here = Path(__file__).resolve().parent
repo = here.parents[5]
sha = lambda data: hashlib.sha256(data).hexdigest()
raw = (here / 'HOST-POLICY.json').read_bytes()
assert sha(raw) == 'eb57aa9c3ba74886e2d9856cfe3382ceab6a2bdb1799283512a4943dfeb62d52', 'binding drift'
binding = json.loads(raw)
for relative, expected in binding['input_pins'].items():
    assert sha((repo / relative).read_bytes()) == expected, 'input drift: ' + relative
candidate_path = next(name for name in binding['input_pins'] if name.endswith('bootstrap-347778/CANDIDATE.json'))
candidate = json.loads((repo / candidate_path).read_text())
accepted_paths = {entry['path']: entry for entry in candidate['paths']}
for relative, entry in accepted_paths.items():
    assert sha((repo / candidate_path).parent.joinpath('candidate', relative).read_bytes()) == entry['candidate_sha256'], relative
for relative, entry in binding['provenance'].items():
    if entry['origin'] == 'independently-accepted-candidate':
        assert entry['sha256'] == accepted_paths['v12/python/' + relative]['candidate_sha256']
    else:
        assert entry['origin'] == 'accepted-candidate-base' and entry['sha256'] == entry['base_sha256']
consumer_pin = next(value for name, value in binding['input_pins'].items() if name.endswith('execution-347396/PACKET-INPUTS.json'))
assert consumer_pin == '7df8bcbc5ac4d8549bc15501b07d27f53b9127e28a614953ed199ba559dd2ed3', 'consumer acceptance mismatch'
archive = here / binding['archive']['path']
assert sha(archive.read_bytes()) == binding['archive']['sha256'], 'archive drift'
with tarfile.open(archive, 'r:gz') as held:
    members = held.getmembers()
    assert len(members) == len(binding['manager_files']) == binding['archive']['members']
    assert len({member.name for member in members}) == len(members), 'duplicate path'
    for member in members:
        path = PurePosixPath(member.name)
        assert member.isfile() and not path.is_absolute() and '..' not in path.parts and member.mode == 0o644
        assert sha(held.extractfile(member).read()) == binding['manager_files'][member.name], member.name
for relative, entry in binding['provenance'].items():
    path = 'v12/python/' + relative
    old = subprocess.check_output(['git', 'show', binding['acceptance']['host_base'] + ':' + path], cwd=repo)
    assert sha(old) == entry['base_sha256'], 'base drift: ' + relative
assert binding['authoring_controller']['sha256'] == binding['manager_files'][binding['authoring_controller']['path']]
assert binding['shutdown_helper']['sha256'] == binding['manager_files'][binding['shutdown_helper']['path']]
assert binding['stage_bootstrap_launch_authorized'] is False and binding['execution_selection'] is None
print(json.dumps({'verified': True, 'members': len(members), 'host_policy_sha256': sha(raw), 'seconds': time.monotonic() - started, 'product_imports': False, 'extracted': False, 'staged': False}, indent=2))
