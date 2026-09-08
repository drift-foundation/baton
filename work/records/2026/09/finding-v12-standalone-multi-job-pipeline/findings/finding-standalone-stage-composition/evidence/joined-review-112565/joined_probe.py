"""Two bounded joined checks; existing fixtures, no live runtime or product edits."""
import contextlib
import copy
import hashlib
import json
from pathlib import Path
import unittest
from unittest import mock
from baton_v12.contracts import ContractRefusal
from baton_v12.worker_manager import frozen_output_of, intake_receipt_of, retentions_of
from tests.integration.test_driver import _OrdinaryAdmissionWorld
from tests.job_manager.test_review_driver import TheWorkerCompletionTraversesPublicCustody as Lifecycle

here = Path(__file__).resolve().parent
repo = next(p for p in here.parents if (p / 'v12/python/src/baton_v12').is_dir())
pinned = json.loads((here / 'candidate-map.json').read_text())['candidate']
def check_hashes():
    for name, expected in pinned.items():
        assert hashlib.sha256((repo / name).read_bytes()).hexdigest() == expected, name
check_hashes()
report = {}
case = unittest.TestCase()
try:
    original_end = Lifecycle.end
    cut = {}
    def interrupted_end(owner, held):
        if getattr(owner, '_joined_cut_done', False):
            return original_end(owner, held)
        owner._joined_cut_done = True
        case.assertEqual(owner.verdicts(held), 0)
        with owner.public_ending(interrupt_after_freeze=True) as before:
            with case.assertRaises(owner.after_freeze):
                original_end(owner, held)
        case.assertEqual(before, ['quiesce', 'observe', 'freeze'])
        frozen = frozen_output_of(owner.control, held['attempt_id'])
        case.assertIsNotNone(frozen)
        case.assertIsNone(intake_receipt_of(owner.control, held['attempt_id']))
        case.assertEqual(retentions_of(owner.control, held['attempt_id']), ())
        case.assertEqual(owner.verdicts(held), 0)
        case.assertEqual(held['adapter'].destroyed_with, [])
        with owner.public_ending() as after, mock.patch.object(owner, 'turn', side_effect=AssertionError('no repeated review worker')):
            ended = original_end(owner, held)
        case.assertEqual(frozen_output_of(owner.control, held['attempt_id']), frozen)
        case.assertEqual(after, list(__import__('baton_v12.job_manager.review_driver', fromlist=['REVIEW_RESULT_ENDING']).REVIEW_RESULT_ENDING))
        cut.update(before=list(before), after=list(after), retained_frozen=frozen)
        return ended
    with mock.patch.object(Lifecycle, 'end', interrupted_end):
        world = _OrdinaryAdmissionWorld(case)
        world.assert_retained_history()
        first = world.admit()
        receipts = world.publisher.receipts(world.proposal_id)
        calls = copy.deepcopy(world.calls)
        case.assertEqual([verb for verb, _ in calls], ['verify', 'review', 'approve'])
        operations = {operands['operation_id']: world.publisher.operation_record(operands['operation_id']) for _, operands in calls}
        manager_changes = world.manager._connection.total_changes
        coordinator_changes = world.coordinator._connection.total_changes
        with contextlib.ExitStack() as stack:
            stack.enter_context(mock.patch.object(world.owner, 'turn', side_effect=AssertionError('no repeated worker')))
            for adapter in (world.adapter, world.review['adapter']):
                for member in ('stop', 'seal', 'collect', 'retain', 'destroy', 'normalize_directory'):
                    stack.enter_context(mock.patch.object(adapter, member, side_effect=AssertionError('no repeated custody act')))
            for _ in range(2):
                case.assertEqual(world.admit(), first)
                case.assertEqual(world.publisher.receipts(world.proposal_id), receipts)
                case.assertEqual(world.evidence()['observation'], world.observation)
                case.assertEqual({op: world.publisher.operation_record(op) for op in operations}, operations)
        case.assertEqual(world.manager._connection.total_changes, manager_changes)
        case.assertEqual(world.coordinator._connection.total_changes, coordinator_changes)
        case.assertEqual(world.calls, calls * 3)
        case.assertEqual(world.command_runs, [(world.required['argv'], 0)])
        case.assertEqual(world.owner.worker_turns, 1)
        report['freeze_reentry_to_admission'] = dict(cut, actual_commands=world.command_runs,
            observation=world.observation, required_tests=world.required, admitted=first,
            authority_receipts=receipts, exact_replays=2, authority_operation_records_unchanged=True,
            manager_and_coordinator_writes_on_replay=0, review_turns=world.owner.worker_turns,
            writer_destroy_calls=len(world.adapter.destroyed_with), review_destroy_calls=len(world.review['adapter'].destroyed_with))
finally:
    case.doCleanups()

case = unittest.TestCase()
try:
    world = _OrdinaryAdmissionWorld(case)
    world.assert_retained_history()
    case.assertEqual(world.evidence()['observation'], world.observation)
    operation_id = world.review['adapter'].destroyed_with[0]['operation']['operation_id']
    prior = world.manager.operation_record(operation_id)
    case.assertEqual(prior['state'], 'committed')
    world.manager._connection.execute('DELETE FROM operations WHERE operation_id = ?', (operation_id,))
    changes = world.manager._connection.total_changes
    coordinator_changes = world.coordinator._connection.total_changes
    reasons = []
    with world.owner.no_more_external_acts(world.review), contextlib.ExitStack() as stack:
        for adapter in (world.adapter, world.review['adapter']):
            for member in ('stop', 'seal', 'collect', 'retain', 'destroy', 'normalize_directory'):
                stack.enter_context(mock.patch.object(adapter, member, side_effect=AssertionError('no repair or repeat act')))
        stack.enter_context(mock.patch.object(world.owner, 'turn', side_effect=AssertionError('no repeated worker')))
        for _ in range(2):
            with case.assertRaises(ContractRefusal) as caught:
                world.admit()
            reasons.append(str(caught.exception))
            world.assert_no_admission()
    case.assertEqual(world.manager._connection.total_changes, changes)
    case.assertEqual(world.coordinator._connection.total_changes, coordinator_changes)
    report['missing_cleanup_before_admission'] = dict(removed_fixture_operation=operation_id,
        reasons=reasons, authority_receipt_calls=world.calls, execution_entries=world.execution_entries,
        manager_and_coordinator_writes=0, attempts=2)
finally:
    case.doCleanups()
check_hashes()
report['candidate_hashes_unchanged'] = len(pinned)
report['boundary'] = 'Real durable admission; deterministic transport/profile fixtures; no integration execution.'
(here / 'joined-probe.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({'freeze_reentry_admitted': report['freeze_reentry_to_admission']['admitted']['state'],
    'exact_replays': report['freeze_reentry_to_admission']['exact_replays'],
    'missing_cleanup_refusals': report['missing_cleanup_before_admission']['reasons'],
    'candidate_hashes_unchanged': report['candidate_hashes_unchanged']}, indent=2))
