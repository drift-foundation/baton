"""Assert the W337955 phase comparisons from retained JSON traces, no execution."""
import argparse
import json
from pathlib import Path


def analyze(root):
    summary = {row['case']: row for row in json.loads((root / 'summary.json').read_text())}
    modes = ('normal', 'blocked_sweep', 'absent_cleanup', 'delayed_snapshot', 'unknown', 'pre_signal', 'snapshot_before')
    assert set(summary) == set(modes), 'all five comparisons and two phase controls required'
    results = {}
    for mode in modes:
        case = root / mode
        reports = list(case.glob('outcome.json.enforcement-*.json'))
        assert len(reports) == 1
        report = json.loads(reports[0].read_text())
        events = [json.loads(line) for line in (case / 'events.jsonl').read_text().splitlines()]
        origin = events[0]['monotonic']
        def selected(name, **values):
            return [row for row in events if row['event'] == name and all(row.get(key) == value for key, value in values.items())]
        def first(name, **values):
            rows = selected(name, **values)
            assert rows, (mode, name, values)
            return rows[0]['monotonic']
        cleanup = summary[mode]
        assert cleanup['managers_reaped'] == cleanup['manager_pids_absent'] and cleanup['guard_reacquired']
        assert cleanup['elapsed'] < 30
        assert report['child_exited'] and report['state'] == 'held', 'no fake workload accepted'
        assert len(selected('manager_guard_held')) == 1
        held = selected('manager_guard_held')[0]
        assert held['guard_pid'] == held['pid'] == cleanup['managers_reaped'][0]
        assert len(selected('trace', function='child_main', kind='call')) == 1
        outcome = (case / 'outcome.json').exists()
        final = bool(selected('snapshot_replaced', finished=True))
        if mode == 'normal':
            assert report['child_status'] == 1 and outcome and final
            assert not selected('outer_signal', signal=15)
            assert first('trace', function='supervise', kind='return') < first('snapshot_replaced', finished=True) < first('manager_reaped')
        elif mode in ('blocked_sweep', 'absent_cleanup'):
            assert report['child_status'] == -9 and not outcome and not final
            assert first('trace', function='_handle', kind='call', mode='raise') < first('defer_call') < first('cleanup_sweep') < first('outer_signal', signal=9)
            assert not selected('trace', function='supervise', kind='return')
            assert not selected('trace', function='stop', kind='call', line=213), 'child never reached Guard.stop'
            attempts = report['enforcement']['attempts']
            assert attempts and all(row['observation']['state'] == 'absent' and row['token']['returned'] and row['token']['revoked'] for row in attempts.values())
            assert 'without final enforcement report' in str(report['enforcement']['faults'])
            deadline = selected('cleanup_sweep')[0]['cleanup_deadline']
            assert first('outer_signal', signal=9) < deadline
            if mode == 'blocked_sweep':
                assert first('blocked_serving_sweep') < first('outer_signal', signal=15)
            else:
                assert selected('deferred_signal_returned')[0]['received'] == ['signal 15', 'signal 15']
        elif mode == 'delayed_snapshot':
            assert report['child_status'] == -9 and outcome and not final
            assert first('trace', function='supervise', kind='return') < first('snapshot_delay') < first('outer_signal', signal=9)
            assert 'without final enforcement report' in str(report['enforcement']['faults'])
        elif mode == 'snapshot_before':
            assert report['child_status'] != -9 and outcome and final
            assert first('snapshot_delay') < first('snapshot_replaced', finished=True) < first('manager_reaped')
        elif mode == 'unknown':
            attempts = report['enforcement']['attempts']
            assert attempts and any(row.get('token') and row['token']['revoked'] and not row['token']['returned'] for row in attempts.values())
            assert any(row['observation']['state'] == 'uncertain' and 'TimeoutError' in row['observation']['why'] and row['settlement']['settled'] == 'held' for row in attempts.values()), 'unknown engine must remain explicit'
            assert report['state'] == 'held'
        elif mode == 'pre_signal':
            assert selected('injected_pre_supervision_signal')
            assert not report['author_invocation_started'] and not outcome and final
            assert not selected('trace', function='supervise', kind='call')
        timeline = []
        interesting = {'outer_signal', 'manager_reaped', 'blocked_serving_sweep', 'defer_call', 'cleanup_sweep', 'snapshot_delay', 'deferred_signal_returned', 'injected_pre_supervision_signal'}
        for row in events:
            if row['event'] in interesting or row['event'] == 'snapshot_replaced' and row['finished'] or row['event'] == 'trace' and row.get('function') in ('_handle', 'supervise', 'stop') and row['kind'] in ('call', 'return'):
                timeline.append(dict(t=round(row['monotonic'] - origin, 6), **{key: value for key, value in row.items() if key not in ('monotonic', 'thread')}))
        results[mode] = {'child_status': report['child_status'], 'outcome_present': outcome, 'finished_snapshot': final, 'elapsed': cleanup['elapsed'], 'checks': 'passed', 'timeline': timeline}
    assert json.loads((root / 'source-unchanged.json').read_text())['unchanged']
    return {'comparisons': 5, 'additional_phase_controls': 2, 'cases': results, 'measured_process_seconds': sum(row['elapsed'] for row in summary.values())}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('root', type=Path)
    args = parser.parse_args()
    print(json.dumps(analyze(args.root), indent=2, sort_keys=True))
