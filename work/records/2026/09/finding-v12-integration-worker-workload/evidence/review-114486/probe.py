"""Real entry/provider/verifier/parser; plain target and injected revision only."""
import hashlib
import json
import os
from pathlib import Path
import stat
import sys

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[6]
sys.path[:0] = [str(REPO / 'v12/python'), str(REPO / 'v12/python/src')]
from tests.manager import test_integration_worker as fixture


def run_case(kind):
    case = fixture.WorldCase('run')
    case.setUp()
    try:
        case.bundle(operation='add')
        target = Path(case.target(repository=False))
        reviewed = case.reviewed()
        body = 'from pathlib import Path\nimport os\n'
        if kind == 'bytes':
            body += f'Path({reviewed!r}).write_bytes(b"changed by verification\\n")\n'
        elif kind == 'mode':
            body += f'os.chmod({reviewed!r}, 0o755)\n'
        elif kind == 'delete':
            body += f'Path({reviewed!r}).unlink()\n'
        elif kind == 'witness':
            # Plain files simulating only the documented metadata witness;
            # no Git repository is initialized and no Git process is invoked.
            (target / '.git').mkdir()
            (target / '.git/index').write_bytes(b'original witness\n')
            body += 'Path(".git/index").write_bytes(b"changed witness by verification\\n")\n'
        elif kind == 'failed':
            body += 'raise SystemExit(3)\n'
        elif kind != 'control':
            raise ValueError(kind)
        (target / 'harness.py').write_text(body)
        status = case.entry(target=str(target))
        observed = case.observed()
        path = target / reviewed
        content = path.read_bytes() if path.exists() else None
        return {'case': kind, 'entry_status': status, 'provider_turns': len(case.commands),
                'candidate_matches': content == case.CANDIDATE,
                'mode': oct(stat.S_IMODE(path.stat().st_mode)) if path.exists() else None,
                'actual_sha256': hashlib.sha256(content).hexdigest() if content is not None else None,
                'expected_sha256': hashlib.sha256(case.CANDIDATE).hexdigest(),
                'witness_changed': (target / '.git/index').read_bytes() != b'original witness\n' if kind == 'witness' else None,
                'observed': observed}
    finally:
        case.doCleanups()


result = {'boundary': 'real producer/entry/provider subprocess/verification subprocess/result reader; existing revision seam and plain disposable target; no Git command, engine, credential, or live model',
          'cases': [run_case(k) for k in ('control', 'bytes', 'mode', 'delete', 'witness', 'failed')]}
(HERE / 'probe.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
