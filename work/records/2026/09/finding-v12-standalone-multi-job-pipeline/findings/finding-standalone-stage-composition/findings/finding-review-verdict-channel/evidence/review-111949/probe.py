"""Independent public-custody observations; no application or test edits."""
import hashlib
import json
from pathlib import Path
from baton_v12.worker_manager import verdict_of, review_cycles
from baton_v12.worker_manager.attempts import attempt_runtime_of
from tests.job_manager.test_review_driver import TheWorkerCompletionTraversesPublicCustody as Case

HERE = Path(__file__).resolve().parent
D = HERE.parents[1]
ROOT = next(p for p in HERE.parents if (p / 'v12/python').is_dir())
baseline = json.loads((D / 'evidence/planning-111746/baseline.json').read_text())
hashes = {}
for path, old in baseline.items():
    data = (ROOT / path).read_bytes()
    hashes[path] = {'sha256': hashlib.sha256(data).hexdigest(), 'baseline': old}
    dest = HERE / 'candidate' / path
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)

def outcome(call):
    try:
        return {'answer': call()}
    except Exception as exc:
        return {'exception': type(exc).__name__, 'message': str(exc)}

def capture(cut):
    case = Case('test_actual_completion_reaches_first_verdict_and_public_custody')
    try:
        case.setUp()
        held = case.produced()
        if cut:
            with case.public_ending(interrupt_after_freeze=True):
                with case.assertRaises(case.after_freeze):
                    case.end(held)
        ended = case.end(held)
        row = verdict_of(case.control, ended['verdict_id'])
        operands = ended['verdict_record']
        mapped = dict(row)
        recorded_at = mapped.pop('recorded_at')
        for old, new in (('base_object', 'base'), ('head_object', 'head'), ('tree_object', 'tree'), ('review_assignment_generation', 'review_generation')):
            mapped[new] = mapped.pop(old)
        case.assertEqual(mapped, operands)
        case.assertTrue(recorded_at)
        return {'freeze_reentry': cut, 'ended': ended, 'persisted_verdict': row,
                'exact_projection_equal': row == operands, 'all_mapped_semantics_equal': mapped == operands,
                'original_custody_assertions': outcome(lambda: case.assert_owned_custody(held, ended)),
                'runtime_after_cleanup': attempt_runtime_of(case.control, held['attempt_id']),
                'verdict_count': case.verdicts(held), 'worker_turns': case.worker_turns,
                'destroy_calls': len(held['adapter'].destroyed_with),
                'post_cleanup_eligibility': outcome(lambda: review_cycles.integration_checkpoint(case.control, row['line_id'])),
                'post_cleanup_replay': outcome(lambda: case.end(held))}
    finally:
        case.doCleanups()

observations = [capture(False), capture(True)]
(HERE / 'probe.json').write_text(json.dumps({'hashes': hashes, 'observations': observations}, indent=2) + '\n')
print(json.dumps({'changed': [p for p, h in hashes.items() if h['sha256'] != h['baseline']], 'observations': [{k: o[k] for k in ('freeze_reentry', 'exact_projection_equal', 'all_mapped_semantics_equal', 'verdict_count', 'worker_turns', 'destroy_calls', 'post_cleanup_eligibility', 'post_cleanup_replay')} for o in observations]}, indent=2))
