"""Independent bounded-correction audit; no engine/provider or real target."""
import ast
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path.cwd()
sys.path[:0] = [str(ROOT / "v12/python/src"), str(ROOT / "v12/python")]
from baton_v12.authority import MAX_SAFE_INTEGER
from baton_v12.contracts import ContractRefusal
from baton_v12.job_manager import scheduler
from baton_v12.worker_manager import configured_workspace_group
from tests.job_manager import fixtures
from tests.tools.test_single_worker import Engine
from tests.tools.test_stage_execution import ServingCase
from tools import stage_execution

HERE = Path(__file__).resolve().parent
DOSSIER = HERE.parents[1]
EXPECTED = {
    "v12/python/tools/stage_execution.py": "95271d77edc044653eef59f79169c82394c5e2b30d1b5ffb1edb48b16d88da47",
    "v12/python/tools/single_worker.py": "5dfd0df1b393f87e6a48e75f0845b266c73d2929e5cd6ad53509e1c02ef9dc27",
    "v12/python/tests/tools/test_stage_execution.py": "16ac448aafef3a29fc7a7778613dc32281ff4b1bbe0e9a38e4cf946f23e5f8d5",
    "v12/python/tests/tools/test_single_worker.py": "95808aee8529d27bab0519f3fe8d45ae4e51507594c4825495530a8882d9af6c",
    "v12/python/tools/parallel_test.py": "eb90384d91cb5a4afe22bc147b8113863c8cf039eb5efbcae7ed4f614870ab9e",
}
hashes = {}
for name, expected in EXPECTED.items():
    raw = (ROOT / name).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == expected, name
    place = HERE / "candidate" / name
    place.parent.mkdir(parents=True, exist_ok=True)
    with place.open("xb") as stream:
        stream.write(raw)
    hashes[name] = expected
progress = (DOSSIER / "PROGRESS.md").read_bytes()
with (HERE / "PROGRESS-at-review.md").open("xb") as stream:
    stream.write(progress)
heads = [line for line in progress.decode().splitlines() if line.startswith("## ")]
assert heads[-2:] == [
    "## 2026-09-07 — baton.claude — the two ordering defects, corrected",
    "## 2026-09-07 — baton.claude — the two bounded corrections"]
before = (DOSSIER / "evidence/review-110968/candidate/v12/python/tests/tools/test_stage_execution.py").read_text()
after = (ROOT / "v12/python/tests/tools/test_stage_execution.py").read_text()
old_tree, new_tree = ast.parse(before), ast.parse(after)
old_classes = {node.name: ast.dump(node) for node in old_tree.body if isinstance(node, ast.ClassDef)}
new_classes = {node.name: ast.dump(node) for node in new_tree.body if isinstance(node, ast.ClassDef)}
assert all(new_classes.get(name) == body for name, body in old_classes.items())
added = set(new_classes) - set(old_classes)
assert added == {"AGenerationOutsideTheInteroperableRangeIsRefused"}
results = []
def state(job, control, path):
    try:
        group = configured_workspace_group(control).gid
    except ContractRefusal:
        group = None
    return dict(group=group, pool=scheduler.active_generation(job), integration_exists=Path(path).exists())
for member, value in (("policy_generation", MAX_SAFE_INTEGER + 1), ("pool_generation", MAX_SAFE_INTEGER + 1), ("policy_generation", MAX_SAFE_INTEGER)):
    case = ServingCase()
    try:
        case.setUp()
        job, control = case.stores("review-111157-" + member + "-" + str(value))
        given = case.composed_document(**{member: value})
        before_state = state(job, control, case.integration_store)
        record = dict(member=member, value=value, before=before_state)
        try:
            composed = stage_execution.operations_from(given, job, control, engine_run=Engine(),
                credential_provider=lambda *_: case.secret, clock=lambda: fixtures.NOW, checkout=case.checkout)
            case.addCleanup(composed.close)
            record["constructed"] = True
        except ContractRefusal as refusal:
            record.update(constructed=False, category=refusal.category, code=refusal.code)
        record["after"] = state(job, control, case.integration_store)
        if value > MAX_SAFE_INTEGER:
            assert record["constructed"] is False
            assert (record["category"], record["code"]) == ("integrity", "limit")
            assert record["before"] == record["after"]
        else:
            assert record["constructed"] is True
        results.append(record)
    finally:
        case.doCleanups()
report = dict(candidate_hashes=hashes, prior_test_classes_unchanged=len(old_classes),
              added_test_classes=sorted(added), progress_section_order=heads,
              progress_snapshot_sha256=hashlib.sha256(progress).hexdigest(), boundary_probes=results,
              limits="Prior review did not snapshot PROGRESS, so complete historical byte equivalence is not independently established. Current order and preserved historical accounts reviewed; this snapshot enables later exact audits. No unchanged suite rerun.")
with (HERE / "audit.json").open("x") as stream:
    json.dump(report, stream, indent=2)
    stream.write("\n")
print(json.dumps(dict(candidate_files=len(hashes), prior_test_classes_unchanged=len(old_classes), boundary_probes=results), indent=2))
