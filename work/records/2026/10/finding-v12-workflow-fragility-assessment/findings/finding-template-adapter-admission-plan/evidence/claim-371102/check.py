"""Inert planning probe: existing readers only, no proposed admission implementation."""
from pathlib import Path
import hashlib
import json
import sys
import time

START = time.monotonic()
ROOT = next(p for p in Path(__file__).resolve().parents if (p / 'v12/justfile').exists())
HERE = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'v12/python'), str(ROOT / 'v12/python/src'),
               str(ROOT / 'v12/python/src/baton_v12'), str(ROOT / 'v12/worker')]
from baton_v12.contracts import digest
from baton_v12.job_manager import templates
from tools import job_task
import claude_agent

prior = ROOT / 'work/records/2026/10/finding-v12-shared-output-template-preparation'
binding = prior / 'INVENTORY-370820.json'
assert hashlib.sha256(binding.read_bytes()).hexdigest() == '2cc804344888ca5d116a7965ac8523729c2a33a94f174294ba5bffe30493295b'
packet = json.loads((prior / 'candidate-370820/BOOTSTRAP-FIXTURE.json').read_text())
task = json.loads((prior / 'candidate-370820/task.json').read_text())
manifest = packet['workers'][0]['deployment']['input_manifest']
descriptor = json.loads((HERE / 'ROLE-CONTRACT.proposed.json').read_text())
capability = json.loads((HERE / 'CAPABILITY.synthetic.json').read_text())
assert descriptor['outputs'] == manifest['outputs']
assert descriptor['task_schema'] == task['schema']
assert descriptor['source_profile'] == task['source_profile']
assert digest(descriptor) == capability['role_contract_digest']
assert digest(descriptor) == 'sha256:21b78036947430e3ae073a04fd5237b10a844471207a52cba9ea6186acdffdaf'
answers = {}
for role, produces in [('implementation', claude_agent.IMPLEMENTATION_OUTPUTS), ('review', claude_agent.REVIEW_OUTPUTS)]:
    present, absent = claude_agent._selected(descriptor['outputs'], produces, role)
    answers[role] = {'produces': [one['name'] for one in present], 'absent': [one['name'] for one in absent]}
legacy = json.loads(json.dumps(manifest))
legacy['outputs'] = [dict(legacy['outputs'][0], required=True)]
derived = job_task.manifest_for(legacy, (prior / 'candidate-370820/task.json').read_text())
assert derived['outputs'] == legacy['outputs']
try:
    claude_agent._selected(derived['outputs'], claude_agent.REVIEW_OUTPUTS, 'review')
except claude_agent.TaskRefusal as error:
    gap = str(error)
else:
    raise AssertionError('current composition unexpectedly repaired role outputs')
print(json.dumps({'scope': 'inert planning probe, no proposed validator implemented',
                  'descriptor_digest': digest(descriptor), 'capability_digest': digest(capability),
                  'roles': answers, 'current_manifest_for_preserves_bad_outputs': True,
                  'review_refusal': gap,
                  'current_template': templates.template_document(templates.IMPLEMENTATION_REVIEW),
                  'seconds': time.monotonic() - START}, indent=2, sort_keys=True))
