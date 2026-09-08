"""Read-only source/preservation audit; no private source or runtime execution."""
import ast
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[5]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def definitions(path):
    tree = ast.parse(path.read_text())
    result = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            result[node.name] = ast.dump(node, include_attributes=False)
        if isinstance(node, ast.ClassDef):
            for method in node.body:
                if isinstance(method, ast.FunctionDef):
                    result[node.name + "." + method.name] = ast.dump(method, include_attributes=False)
    return result


def main():
    baseline = json.loads((HERE / "result-diagnostics-baseline-111078.json").read_text())
    changed = []
    for relative, expected in baseline["prior_files"].items():
        observed = digest(REPO / relative)
        if observed != expected:
            changed.append(dict(path=relative, expected=expected, observed=observed))
    assert changed == baseline["current_dependency_changes"]
    assert len(changed) == 1 and changed[0]["path"] == "v12/python/src/baton_v12/job_manager/review_driver.py"
    protected = {name: expected for name, expected in baseline["dossier_files"].items()
                 if Path(name).name not in ("FINDING.md", "PLAN.md", "PROGRESS.md")}
    for name, expected in protected.items():
        assert digest(REPO / name) == expected, name
    comparisons = {}
    for previous, candidate, permitted in (
        ("live_controller_restore_constructor.py", "live_controller_result_diagnostics.py", {"diagnostic_frame", "Fixture.start"}),
        ("live_supervisor_restore.py", "live_supervisor_result_diagnostics.py", {"Supervisor.observe", "Supervisor.turn"}),
    ):
        old, new = definitions(HERE / previous), definitions(HERE / candidate)
        modified = {name for name in old if old[name] != new.get(name)}
        assert modified == permitted, (candidate, modified)
        comparisons[candidate] = dict(changed_existing_definitions=sorted(modified), unchanged_definitions=len(old) - len(modified),
                                      added_definitions=sorted(new.keys() - old.keys()))
    old = (HERE / "live_controller_restore_constructor.py").read_text()
    new = (HERE / "live_controller_result_diagnostics.py").read_text()
    start_old = definitions(HERE / "live_controller_restore_constructor.py")["Fixture.start"]
    start_new = definitions(HERE / "live_controller_result_diagnostics.py")["Fixture.start"]
    assert start_new == start_old.replace("live_supervisor_restore.py", "live_supervisor_result_diagnostics.py")
    begin_old = old[:old.index("def diagnostic_frame(")]
    begin_new = new[:new.index("def diagnostic_frame(")]
    assert begin_new == begin_old.replace("restore-constructor-manifest.json", "result-diagnostics-manifest.json").replace("live_supervisor_restore", "live_supervisor_result_diagnostics")
    assert new[new.index("def response_shape("):] == old[old.index("def response_shape("):].replace("live_supervisor_restore.py", "live_supervisor_result_diagnostics.py")
    old_turn = definitions(HERE / "live_supervisor_restore.py")["Supervisor.turn"]
    new_source = (HERE / "live_supervisor_result_diagnostics.py").read_text()
    normalized = new_source.replace('self.observe("provider-result-validation", result=value)', 'self.observe("provider-result-validation")')
    tree = ast.parse(normalized)
    supervisor = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "Supervisor")
    turn = next(node for node in supervisor.body if isinstance(node, ast.FunctionDef) and node.name == "turn")
    assert ast.dump(turn, include_attributes=False) == old_turn
    import live_supervisor_result_diagnostics as wire
    contract = json.loads((HERE / "result-subtype-contract-111078.json").read_text())
    assert set(contract["known_nonsuccess_labels"]) == set(wire.KNOWN_RESULT_SUBTYPES)
    assert all(key == value for key, value in wire.KNOWN_RESULT_SUBTYPES.items())
    runtime = {str(p.relative_to(REPO)) for p in (REPO / "v12/python/src/baton_v12").rglob("*.py")}
    assert runtime == {name for name in baseline["prior_files"] if name.startswith("v12/python/src/baton_v12/") and name.endswith(".py")}
    # The newly bound review driver is inert definitions/imports/constants at import;
    # no manager, store, provider, callback or default-expression execution is added.
    driver = ast.parse((REPO / changed[0]["path"]).read_text())
    for node in driver.body:
        assert isinstance(node, (ast.Expr, ast.ImportFrom, ast.Import, ast.Assign, ast.FunctionDef))
        if isinstance(node, ast.Expr):
            assert isinstance(node.value, ast.Constant) and isinstance(node.value.value, str)
        if isinstance(node, ast.Assign):
            ast.literal_eval(node.value)
        if isinstance(node, ast.FunctionDef):
            assert not node.decorator_list
            for default in [*node.args.defaults, *(value for value in node.args.kw_defaults if value is not None)]:
                ast.literal_eval(default)
    print(json.dumps(dict(prior_inputs=len(baseline["prior_files"]), unchanged_prior_inputs=len(baseline["prior_files"]) - len(changed),
        rebound_dependencies=changed, historical_dossier_files_unchanged=len(protected), definition_audits=comparisons,
        exact_original_result_acceptance=True, exact_original_runtime_argv=True, exact_original_restoration_and_ending=True,
        runtime_file_set_unchanged=True, current_review_driver_import_has_no_execution=True,
        contract_allowlist_matches=True, live_run=False), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
