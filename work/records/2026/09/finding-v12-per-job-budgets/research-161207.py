"""Read-only planning inventory; no runtime execution or store access."""
import hashlib
import json
from pathlib import Path
import time

root = Path('/home/sl/src/baton')
record = Path(__file__).resolve().parent
out = record / 'research-161207.json'
assert not out.exists(), 'preserve prior evidence'
start = time.monotonic()
prior = json.loads((record / 'research-161035.json').read_text())
def measured(path):
    data = (root / path).read_bytes()
    return dict(bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
source_paths = list(prior['source_files']) + ['v12/python/src/baton_v12/job_manager/schema.py', 'v12/python/src/baton_v12/job_manager/store.py', 'v12/python/src/baton_v12/worker_manager/documents.py']
candidate = {p: measured(p) for p in prior['candidate_snapshot']}
source = {p: measured(p) for p in source_paths}
answer = dict(work='W156162', claim=161207, kind='planning source inventory only', candidate_snapshot=candidate, source_files=source, changed_candidate_since161035=[p for p,v in candidate.items() if v != prior['candidate_snapshot'][p]], changed_existing_source_since161035=[p for p,v in prior['source_files'].items() if source[p] != v], prior_review_seconds=prior['review_spent_seconds'], author_measured_runs=prior['author_measured_runs'], author_spent_seconds=prior['author_spent_seconds'], unknown_author_activities=4, elapsed_seconds=time.monotonic()-start)
answer['review_spent_seconds'] = answer['prior_review_seconds'] + answer['elapsed_seconds']
out.write_text(json.dumps(answer, indent=2)+'\n')
print(json.dumps({k:v for k,v in answer.items() if k not in ['candidate_snapshot','source_files']}, indent=2))
