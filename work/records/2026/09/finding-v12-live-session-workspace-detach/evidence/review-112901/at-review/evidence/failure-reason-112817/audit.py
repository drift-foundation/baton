"""Offline binding and exact preserved behavior audit."""
import ast
import hashlib
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent
EVIDENCE = OUT.parent
REPO = EVIDENCE.parents[5]


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def definitions(source):
    tree = ast.parse(source)
    result = {}
    def visit(body, prefix=''):
        for node in body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                result[prefix + node.name] = ast.dump(node, include_attributes=False)
            elif isinstance(node, ast.ClassDef):
                visit(node.body, prefix + node.name + '.')
    visit(tree.body)
    return result


def main():
    baseline = json.loads((OUT / 'baseline.json').read_text())
    for name, expected in baseline['protected'].items():
        assert sha(REPO / name) == expected, name
    manifest = json.loads((EVIDENCE / 'failure-reason-112817-manifest.json').read_text())
    assert baseline['prior_files'].items() <= manifest['files'].items()
    for name, expected in manifest['files'].items():
        p = REPO / name
        assert p.is_file() and not p.is_symlink() and sha(p) == expected, name
    runtime = {str(p.relative_to(REPO)) for p in (REPO / 'v12/python/src/baton_v12').rglob('*.py')}
    assert runtime == {p for p in manifest['files'] if p.startswith('v12/python/src/baton_v12/') and p.endswith('.py')}
    before_host = (EVIDENCE / 'live_controller_rebound_112609.py').read_text()
    after_host = (EVIDENCE / 'live_controller_failure_reason_112817.py').read_text()
    block = '''    if "failure_reason" in value:
        require(value.get("event") == "diagnostic"
                and value.get("stage") == "provider-result-validation" and operation == "turn", "diagnostic-frame-invalid")
        wire.validate_failure_reason(value["failure_reason"])
        fields = fields | {"failure_reason"}
'''
    assert after_host.count(block) == 1
    normalized = after_host.replace(block, '').replace('failure-reason-112817-manifest.json', 'result-diagnostics-rebound-112609-manifest.json').replace('live_supervisor_failure_reason_112817', 'live_supervisor_result_diagnostics')
    assert normalized == before_host
    before_worker = (EVIDENCE / 'live_supervisor_result_diagnostics.py').read_text()
    after_worker = (EVIDENCE / 'live_supervisor_failure_reason_112817.py').read_text()
    inserted = after_worker.index('# One documented result field; fixed values only, never provider prose.')
    end = after_worker.index('def result_projection(value, session):', inserted)
    normalized = after_worker[:inserted] + after_worker[end:]
    emission = '            projection["failure_reason"] = failure_reason(result)\n'
    assert normalized.count(emission) == 1
    assert normalized.replace(emission, '') == before_worker
    bd, ad = definitions(before_worker), definitions(after_worker)
    changed = sorted(name for name in bd if bd[name] != ad[name])
    assert changed == ['Supervisor.observe']
    assert sorted(ad.keys() - bd.keys()) == ['failure_reason', 'validate_failure_reason']
    assert bd['result_projection'] == ad['result_projection']
    assert bd['Supervisor.turn'] == ad['Supervisor.turn']
    for name in ('live_controller_failure_reason_112817.py', 'live_supervisor_failure_reason_112817.py', 'test_failure_reason_112817.py'):
        ast.parse((EVIDENCE / name).read_text())
    log = json.loads((OUT / 'focused-tests.json').read_text())
    assert log['exit_code'] == 0 and log['tests'] == 17 and log['broad_suite'] is False
    print(json.dumps(dict(claim=112817,protected_files=len(baseline['protected']),
        package_inputs=len(manifest['files']),unchanged_prior_inputs=len(baseline['prior_files']),
        runtime_python_modules=len(runtime),source_comparison='exact except documented diagnostic blocks and candidate selectors',
        unchanged_result_acceptance=True,unchanged_turn_dispatch=True,unchanged_cli_argv=True,
        unchanged_credential_custody_ending=True,existing_tests_unchanged=True,
        focused_checks=17,broad_suite=False,live_run=False),indent=2,sort_keys=True))


if __name__ == '__main__':
    main()
