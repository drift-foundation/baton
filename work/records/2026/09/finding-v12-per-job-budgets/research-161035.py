"""Read-only source/candidate inventory for the managed-integration design."""
import hashlib
import json
import pathlib
import subprocess
import time

root = pathlib.Path('/home/sl/src/baton')
record = pathlib.Path(__file__).resolve().parent
start = time.monotonic()
prior = json.loads((record / 'review-160499.json').read_text())
def file_record(name):
    data = (root / name).read_bytes()
    return {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
paths = [
    'v12/python/src/baton_v12/integration/runtime.py',
    'v12/python/src/baton_v12/integration/oci_delivery.py',
    'v12/python/src/baton_v12/integration/reconciliation.py',
    'v12/python/src/baton_v12/integration/execution.py',
    'v12/python/src/baton_v12/integration/git_profile.py',
    'v12/python/src/baton_v12/integration/recovery.py',
    'v12/python/src/baton_v12/integration/queue.py',
    'v12/python/src/baton_v12/integration/schema.py',
    'v12/python/src/baton_v12/integration/store.py',
    'v12/python/src/baton_v12/worker_manager/attempts.py',
    'v12/python/src/baton_v12/worker_manager/offers.py',
    'v12/python/src/baton_v12/worker_manager/output.py',
    'v12/python/src/baton_v12/worker_manager/intake.py',
    'v12/python/src/baton_v12/worker_manager/workspaces.py',
    'v12/python/src/baton_v12/worker_manager/launch.py',
    'v12/python/src/baton_v12/worker_manager/exchange.py',
    'v12/python/src/baton_v12/worker_manager/oci.py',
    'v12/python/src/baton_v12/job_manager/delegation.py',
    'v12/python/src/baton_v12/job_manager/scheduler.py',
    'v12/python/tools/integration_worker.py',
    'v12/python/tools/integration_bundle.py',
    'v12/python/tools/single_worker.py',
    'v12/python/tools/stage_execution.py',
    'v12/worker/integration_entry.py',
    'v12/worker/integration_workload.py',
    'v12/worker/integration_contract.py',
    'v12/worker/baton_worker.py',
]
candidate = {name: file_record(name) for name in prior['candidate_after']}
source = {name: file_record(name) for name in paths}
head = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=root, check=True, capture_output=True, text=True).stdout.strip()
answer = {'work': 'W156162', 'claim': 161035, 'kind': 'planning source inventory; no runtime verification', 'head': head, 'source_files': source, 'candidate_snapshot': candidate, 'changed_since_review160499': [name for name in candidate if candidate[name] != prior['candidate_after'][name]], 'prior_review_seconds': prior['review_spent_seconds'], 'author_measured_runs': prior['author_measured_runs'], 'author_spent_seconds': prior['author_spent_seconds'], 'unknown_author_activities': 4, 'elapsed_seconds': time.monotonic() - start}
answer['review_spent_seconds'] = answer['prior_review_seconds'] + answer['elapsed_seconds']
(record / 'research-161035.json').write_text(json.dumps(answer, indent=2) + '\n')
print(json.dumps({key: answer[key] for key in ('head', 'changed_since_review160499', 'elapsed_seconds', 'review_spent_seconds', 'author_measured_runs', 'author_spent_seconds')}, indent=2))
