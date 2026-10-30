"""Preparation-only syntax, manifest and source-byte checks. No product imports."""
import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import tarfile
import time

HERE = Path(__file__).resolve().parent
REPO = Path('/home/sl/src/baton')
BASE = 'fb48797903160aa764229d58f3a5beaf29648bfc'
RUN = 'shutdown-deadline-w338305-prep338308'
SUPERVISOR = 'work/records/2026/09/finding-v12-single-implementation-proof'
BOOTSTRAP = Path('/home/sl/baton-runs/managed-correction-236087/build/stack/out/distro/baton-v12-stack')


def sha(content):
    return hashlib.sha256(content).hexdigest()


def git(*args):
    return subprocess.check_output(['git', *args], cwd=REPO)


def require(condition, description):
    if not condition:
        raise ValueError(description)


def main():
    started = time.monotonic()
    pins = json.loads((HERE / 'PREPARATION-PINS.json').read_text())
    source = json.loads((HERE / 'SOURCE.json').read_text())
    require(pins['base'] == source['base'] == BASE, 'base mismatch')
    for name, expected in pins['files'].items():
        path = REPO / name
        require(path.is_file() and not path.is_symlink(), 'non-regular pin: ' + name)
        require(sha(path.read_bytes()) == expected, 'pin drift: ' + name)
    require(sha(BOOTSTRAP.read_bytes()) == pins['historical_bootstrap_binary_sha256'], 'bootstrap drift')
    for name, expected in source['files'].items():
        require(sha(git('show', BASE + ':' + name)) == expected, 'Git input drift: ' + name)
    with tarfile.open(HERE / 'source.tar.gz', 'r:gz') as archive:
        members = archive.getmembers()
        require(len(members) == len(source['files']), 'archive member count')
        require({m.name for m in members} == set(source['files']), 'archive paths')
        for member in members:
            require(member.isfile(), 'non-file archive member')
            require(sha(archive.extractfile(member).read()) == source['files'][member.name], 'archive bytes')
    for name, expected in pins['manager_files'].items():
        require(source['files']['v12/python/' + name] == expected, 'manager snapshot disagreement')
    for name, expected in pins['supervisor_files'].items():
        require(sha(git('show', BASE + ':' + SUPERVISOR + '/' + name)) == expected, 'supervisor Git drift')
    module = ast.parse((HERE / 'prepare.py').read_text())
    values = {node.targets[0].id: node.value for node in module.body
              if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name)}
    require(ast.literal_eval(values['BASE']) == BASE, 'prepare base')
    require(ast.literal_eval(values['RUN']) == RUN, 'prepare run')
    bounds = {k.arg: ast.literal_eval(k.value) for k in values['BOUNDS'].keywords}
    require(bounds == dict(turn_seconds=3600, total_seconds=4800, cleanup_seconds=60,
                           implementer_invocations=1, retry=False), 'prepare bounds')
    gate = ast.literal_eval(values['GATE'])
    require(gate == ['tests.manager.test_authoring_shutdown_deadline.FastContract',
                     'tests.manager.test_authoring_enforcement.OwnerLane',
                     'tests.manager.test_authoring_enforcement.LateLaunch',
                     'tests.manager.test_authoring_enforcement.UnboundLaunch'], 'gate drift')
    # Interpret only the closed literal/string expression used for argv. Never
    # import prepare.py or execute its Python statements.
    def literal(node):
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.List):
            return [literal(one) for one in node.elts]
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            return literal(node.left) + literal(node.right)
        if (isinstance(node, ast.Call) and ast.unparse(node.func) == 'json.dumps'
                and len(node.args) == 1 and isinstance(node.args[0], ast.Name)
                and node.args[0].id == 'GATE' and not node.keywords):
            return json.dumps(gate)
        raise ValueError('unexpected static argv expression')
    argv = literal(values['VERIFICATION'])
    ast.parse(argv[-1])
    preview = json.loads((HERE / 'TASK-PREVIEW.json').read_text())
    require(preview == dict(schema='baton.dogfood-task/2', task_id=RUN,
                           instructions=(HERE / 'TASK.md').read_text(),
                           source_root='source', source_profile='git-line',
                           declared_base=BASE, verification=argv), 'task preview mismatch')
    supplemental = json.loads((HERE / 'SUPPLEMENTAL-ARGV.json').read_text())
    require(supplemental[:3] == ['python3', '-B', '-c'], 'supplemental command shape')
    ast.parse(supplemental[-1])
    # Existing gate classes are present in the committed input. The new class is
    # deliberately a required author deliverable, not a passing preparation test.
    enforcement = ast.parse(git('show', BASE + ':v12/python/tests/manager/test_authoring_enforcement.py'))
    classes = {node.name for node in enforcement.body if isinstance(node, ast.ClassDef)}
    require(all(name.rsplit('.', 1)[1] in classes for name in gate[1:]), 'existing gate class absent')
    ast.parse((HERE / 'check-static.py').read_text())
    head = git('log', '-1', '--format=%H').decode().strip()
    changed = git('diff', '--name-only', BASE, head, '--', 'v12', SUPERVISOR).decode().splitlines()
    require(not changed, 'selected base versus observed HEAD product/supervisor drift')
    print(json.dumps(dict(
        state='static-preparation-checks-passed', observed_utc=datetime.now(timezone.utc).isoformat(),
        base=BASE, observed_head=head, run=RUN,
        manager_files=len(pins['manager_files']), source_files=len(source['files']),
        supervisor_files=len(pins['supervisor_files']), packet_input_files=len(pins['files']),
        bounds=bounds, gate=gate, new_gate_class='required-author-deliverable-unrun',
        formal_verifier_seconds=30, supplemental_command_seconds=120,
        supplemental_termination_seconds=5,
        product_execution_seconds=0, bootstrap_bind_executed=False,
        stores_opened=False, provider_engine_invoked=False,
        image_auth_availability='unverified',
        proposed_root_absent=not Path('/home/sl/baton-instances/' + RUN).exists(),
        measured_static_check_seconds=time.monotonic() - started), indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
