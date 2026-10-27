"""Verify the exact imported candidate using disk-backed scratch outside checkout."""
from pathlib import Path
import hashlib, json, os, stat, subprocess, tempfile, time

evidence = Path(__file__).resolve().parent
root = next(p for p in evidence.parents if (p / 'v12/python').is_dir())
receipt = json.loads((evidence / 'receipt.json').read_text())
def check_import():
    for item in receipt['paths']:
        path = root / item['path']
        assert path.is_file() and not path.is_symlink(), str(path)
        assert hashlib.sha256(path.read_bytes()).hexdigest() == item['candidate'], str(path)
        assert oct(stat.S_IMODE(path.stat().st_mode)) == item['mode'], str(path)
check_import()
scratch = tempfile.mkdtemp(prefix='baton-integration-366616-', dir='/var/tmp')
run = evidence / ('verification-' + time.strftime('%Y%m%dT%H%M%SZ', time.gmtime()))
run.mkdir()
env = os.environ.copy()
env.update(PYTHONPATH='src:.', BATON_V12_DISK_ROOT=scratch, BATON_V12_STACK_TEST_ROOT=scratch, BATON_V12_OBS0_REPORT=str(run / 'OBS0-INTERVALS.json'), PYTHONDONTWRITEBYTECODE='1')
argv = ['python3', '-m', 'unittest', '-v', 'tests.tools.test_connected_startup', 'tests.tools.test_joined_workflow']
start = time.monotonic()
with (run / 'focused.log').open('w') as log:
    try:
        process = subprocess.run(argv, cwd=root / 'v12/python', env=env, stdout=log, stderr=subprocess.STDOUT, timeout=180)
        result = {'exit': process.returncode}
    except subprocess.TimeoutExpired:
        result = {'exit': 124, 'timed_out': True}
result.update(wall_seconds=time.monotonic() - start, argv=argv, cwd=str(root / 'v12/python'), disk_root=scratch)
check_import()
result['postcheck'] = 'all 32 candidate hashes and modes match'
(run / 'verification.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
print('Evidence:', run)
print('\n'.join((run / 'focused.log').read_text().splitlines()[-12:]))
raise SystemExit(result['exit'])
