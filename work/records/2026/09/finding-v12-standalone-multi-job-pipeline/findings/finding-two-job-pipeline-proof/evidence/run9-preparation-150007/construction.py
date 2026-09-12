"""Recorded one-time preparation; refuses an existing package. No host operation."""
from pathlib import Path
import hashlib
import json
import re

REC = Path('/home/sl/src/baton/work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/finding-two-job-pipeline-proof')
OLD = REC / 'prepared-149854'
NEW = REC / 'prepared-150007'
EVIDENCE = REC / 'evidence/run9-preparation-150007'
CREATED = (EVIDENCE / 'created.txt').read_text()
OLD_RULING = 'M141636/return149484; run8 preparation and exactly one operator attempt after independent input review authorized; no agent model execution or automatic retry'
RULING = 'M141636/return150004; run9 preparation and exactly one operator attempt after required input checks and genuine execution bindings authorized; no agent model execution or automatic retry'
NEW.mkdir()
for source in OLD.rglob('*'):
    relative = source.relative_to(OLD)
    if not source.is_file() or any(x in {'frozen-config', 'image-build', '__pycache__'} for x in relative.parts):
        continue
    if source.name in {'validation.json', 'selected-images.json', 'execution-review.json', 'candidate-manifest.json', 'test_run8_preparation.py'}:
        continue
    target = NEW / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(source.read_bytes())
deployment = (OLD / 'deployment.py').read_text().replace('run8', 'run9').replace('c71879b2000000000000000000000001', 'c71879b3000000000000000000000001').replace('2026-09-12T03:32:20.835Z', CREATED).replace(OLD_RULING.replace('run8', 'run9'), RULING).replace('w71879-149488-validation-', 'w71879-150007-validation-')
(NEW / 'deployment.py').write_text(deployment)
(NEW / 'run.py').write_text((OLD / 'run.py').read_text().replace('w71879-run8', 'w71879-run9'))
(NEW / 'operator-prepare.sh').write_text((OLD / 'operator-prepare.sh').read_text().replace('run8', 'run9').replace('prepared-149488/target_posture.py', 'prepared-150007/target_posture.py'))
for name in ('test_manifest_timestamp.py', 'test_report_instructions.py', 'test_observed_status.py', 'offline_fixture.py', 'verify_offline.py'):
    text = (OLD / name).read_text().replace('run8', 'run9').replace('w71879-149488-', 'w71879-150007-').replace('2026-09-12T03:32:20.835Z', CREATED)
    (NEW / name).write_text(text)
(NEW / 'test_early_failure.py').write_text((OLD / 'test_early_failure.py').read_text().replace(".replace(INCARNATION, 'w71879-run8')", ".replace(INCARNATION, 'w71879-run9')"))
for path in (NEW / 'tasks').glob('*.json'):
    task = json.loads(path.read_text())
    task['task_id'] = task['task_id'].replace('run8', 'run9')
    path.write_text(json.dumps(task, indent=2, sort_keys=True) + '\n')
for path in (NEW / 'policies').glob('*.json'):
    policy = json.loads(path.read_text().replace('w71879-run8', 'w71879-run9'))
    if path.stem == 'policy':
        policy['ruling'] = RULING
    path.write_text(json.dumps(policy, indent=2, sort_keys=True) + '\n')
for name in ('FINDING.md', 'PLAN.md'):
    (NEW / 'record-snapshot' / name).write_bytes((REC / name).read_bytes())
helpers = {name: 'sha256:' + hashlib.sha256((NEW / name).read_bytes()).hexdigest() for name in ('run.py', 'deployment.py', 'target_posture.py', 'failure_observation.py')}
(NEW / 'runner-helpers.json').write_text(json.dumps(helpers, indent=2, sort_keys=True) + '\n')

# Four whole-document/equality cases advance to the accepted correction package.
test = (OLD / 'test_run8_preparation.py').read_text()
test = test.replace("PRIOR = HERE.parent / 'prepared-149053'", "PRIOR = HERE.parent / 'prepared-149854'")
test = test.replace("CREATED = '2026-09-12T03:32:20.835Z'", 'CREATED = ' + repr(CREATED))
test = test.replace('RULING = ' + repr(OLD_RULING), 'RULING = ' + repr(RULING))
mapping = {'run7': 'run8', 'run8': 'run9', 'Run8': 'Run9', 'c71879b1': 'c71879b2', 'c71879b2': 'c71879b3', 'w71879-149488-public-bootstrap-': 'w71879-150007-public-bootstrap-'}
test = re.sub('|'.join(re.escape(x) for x in sorted(mapping, key=len, reverse=True)), lambda m: mapping[m[0]], test)
lines = test.splitlines()
for index, line in enumerate(lines):
    if line.startswith('        expected = old.replace('):
        lines[index] = "        expected = old.replace('run8', 'run9').replace('c71879b2000000000000000000000001', 'c71879b3000000000000000000000001').replace('2026-09-12T03:32:20.835Z', CREATED).replace(" + repr(OLD_RULING.replace('run8', 'run9')) + ", RULING).replace('w71879-149488-validation-', 'w71879-150007-validation-')"
    if line.startswith('        expected_runner = expected_runner.replace('):
        lines[index] = ''  # The accepted predecessor already contains this exact correction.
    if line.startswith("        expected = (PRIOR / 'operator-prepare.sh')"):
        lines[index] = "        expected = (PRIOR / 'operator-prepare.sh').read_text().replace('run8', 'run9').replace('prepared-149488/target_posture.py', 'prepared-150007/target_posture.py')"
(NEW / 'test_run9_preparation.py').write_text('\n'.join(lines) + '\n')
print(json.dumps({'created': CREATED, 'helpers': helpers, 'authority': 'c71879b3000000000000000000000001'}, indent=2))
