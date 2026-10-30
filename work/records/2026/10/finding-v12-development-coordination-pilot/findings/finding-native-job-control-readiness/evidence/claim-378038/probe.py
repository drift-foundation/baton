"""Read-only pinned-source probe; no engine, provider, instance or product edit."""
import contextlib, hashlib, io, json, pathlib, subprocess, sys, tarfile, tempfile, time
COMMIT = '8876bf950ff1f8ab8767ce9786df268cc9d767c6'
started = time.monotonic()
root = pathlib.Path(tempfile.mkdtemp(prefix='w378034-source-'))
archive = subprocess.check_output(['git', 'archive', COMMIT, 'v12/python'])
with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
    tar.extractall(root, filter='data')
base = root / 'v12/python'
sys.path[:0] = [str(base), str(base / 'src')]
from baton_v12.job_manager import execution_limits
from baton_v12.contracts import ContractRefusal
from tools import job_manager, stage_execution, stack_command, stopped_settlement
for module in (execution_limits, job_manager, stage_execution, stack_command, stopped_settlement):
    assert pathlib.Path(module.__file__).is_relative_to(root)
results = {}
resolved = execution_limits.resolved({'provider_turn_seconds':3600, 'verification_command_seconds':900})
results['native_task_token_seconds'] = execution_limits.task_token_seconds(resolved)
assert results['native_task_token_seconds'] == 7320
for key in ('max_corrections', 'stage_seconds', 'job_seconds'):
    try:
        execution_limits.owned_execution_limits({key:0})
    except ContractRefusal as exc:
        results['limits_refuse_' + key] = str(exc)
    else:
        raise AssertionError('unsupported member accepted: ' + key)
# Exercise installed manager parser only. Help/unknown verb cannot open a store.
for name, args, code in [
    ('manager_help',['--help'],0),
    ('create_help',['--store','unused','--incarnation','probe','--authority-uuid','0'*32,'create','--help'],0),
    ('cancel_refused',['--store','unused','--incarnation','probe','--authority-uuid','0'*32,'cancel'],2),
    ('settlement_help',['settle-stopped','--help'],0)]:
    out=io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
        try: job_manager.main(args)
        except SystemExit as exc: assert exc.code == code, (name,exc.code)
        else: raise AssertionError('parser unexpectedly executed')
    results[name] = out.getvalue()
assert '--max-corrections' not in results['create_help']
assert '--stage-seconds' not in results['create_help']
# Real pinned routed method: no stores are supplied. A decline must avoid act.
import ast
parsed=ast.parse(pathlib.Path(stage_execution.__file__).read_text())
owner=next(n.name for n in parsed.body if isinstance(n,ast.ClassDef) and any(isinstance(m,ast.FunctionDef) and m.name=='routed' for m in n.body))
cls=getattr(stage_execution,owner)
obj=object.__new__(cls)
obj.correction_policy='decline'
answer=cls.routed(obj,{'job_id':'probe-job'},{'outcome':'correction','verdict_id':'probe-verdict'})
assert answer['correction'] is None and answer['verdict_id']=='probe-verdict'
results['deployment_decline_without_store_act']=answer
results['stack_commands']=sorted(stack_command.COMMANDS)
results['selected_source']=COMMIT
results['export']=str(root)
results['archive_sha256']=hashlib.sha256(archive).hexdigest()
results['elapsed_seconds']=time.monotonic()-started
print(json.dumps(results,indent=2))
