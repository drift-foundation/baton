"""R1 proofs. (1) A copy holding ONLY v12/ and the runner's declared inputs
runs the delivery tests. (2) Normal source identity names both root documents
and changes when either changes. Nothing here uses an engine or provider."""
import json, os, shutil, subprocess, sys, time, hashlib
from pathlib import Path
repo = Path('/home/sl/src/baton/work/scratch/w385853-review-386045/repo')
out = Path('/home/sl/src/baton/work/records/2026/11/finding-host-worker-instruction-separation/evidence/review-codxpc-386045')
moved = Path('/home/sl/src/baton/work/scratch/w385853-review-386045/relocated')
python = '/home/sl/.local/state/baton-v12-venv/bin/python'
roots = '/home/sl/src/baton/work/scratch/w385853-review-386045/relocation-roots'
Path(roots).mkdir(exist_ok=True)
env = dict(os.environ, PYTHONPATH='src', BATON_V12_DISK_ROOT=roots, TMPDIR=roots)
declared = json.loads(subprocess.check_output([python, '-c', 'import json; from tools.parallel_test import consumed_inputs; print(json.dumps(consumed_inputs()))'], cwd=repo/'v12/python', env=env))
if moved.exists(): shutil.rmtree(moved)
moved.mkdir()
shutil.copytree(repo/'v12', moved/'v12', symlinks=True, ignore=shutil.ignore_patterns('__pycache__', 'build', 'node_modules', '*.egg-info'))
for one in declared:
    source, target = repo/one, moved/one
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, target, symlinks=True) if source.is_dir() else shutil.copy2(source, target)
top = sorted(p.name for p in moved.iterdir())
names = ['tests.manager.test_provider_home.WorkerInstructionDelivery',
         'tests.tools.test_provider_selection.SelectedCase.test_d2_d3_implementation_turn_carries_role_label_and_exact_worker_instructions',
         'tests.tools.test_provider_selection.SelectedCase.test_d4_delivery_is_in_no_candidate_frozen_output_or_custody',
         'tests.tools.test_provider_selection.SelectedCase.test_d3_d4_restart_then_next_provider_turn_replaces_entry_and_binds_label',
         'tests.tools.test_provider_selection.SelectedHandoffCase']
command = ['just', '--justfile', 'v12/justfile', 'test-one', *names]
start = time.monotonic()
run = subprocess.run(command, cwd=moved, env=dict(env, PYTHONPATH=''), capture_output=True, timeout=600)
(out/'relocation.stdout.log').write_bytes(run.stdout); (out/'relocation.stderr.log').write_bytes(run.stderr)
tail = run.stderr.decode(errors='replace').strip().splitlines()[-3:]
header = {'command': command, 'cwd': str(moved), 'top_level_entries': top, 'declared_inputs': declared,
          'root_documents_present': {n: (moved/n).is_file() for n in ('AGENTS.md', 'docs/V12-WORKER-INSTRUCTIONS.md')},
          'docs_entries': sorted(p.name for p in (moved/'docs').iterdir()), 'exit_status': run.returncode,
          'duration_seconds': time.monotonic()-start, 'result_lines': tail, 'interpreter': python}
(out/'relocation.header.json').write_text(json.dumps(header, indent=2)+'\n')

print(json.dumps(header, indent=2))
sys.exit(run.returncode)
