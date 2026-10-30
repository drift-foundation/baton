import json, sys, glob
root = sys.argv[1]
r = json.load(open(glob.glob(root + '/outcome.json.enforcement-*.json')[0]))
print('report state', r['state'], 'faults', r['enforcement']['faults'], 'child_status', r.get('child_status'))
for k, row in r['enforcement']['attempts'].items():
    print('runtime', {x: (row['runtime'] or {}).get(x) for x in ('runtime_id', 'execution_runtime', 'cleanup')})
    print('observation', row['observation'])
    t = row['token']
    print('token', None if t is None else {x: t.get(x) for x in ('seconds', 'renewals', 'returned', 'revoked', 'container', 'activating', 'expired', 'expires_at', 'settlement_fence', 'timing_ambiguous')})
    print('faults', row['faults'], 'reclaim', row.get('reclaim'), 'settlement', row.get('settlement'))
rows = [json.loads(l) for l in open(root + '/events.jsonl')]
t0 = rows[0]['monotonic']
for e in rows:
    if e['event'] in ('token_acquire', 'token_acquire_refused', 'start_refused', 'fake_engine', 'blocked_serving_sweep', 'outer_signal', 'deferred_signal_returned', 'manager_reaped', 'stalled_cleanup_sweep') or (e['event'] == 'trace' and e['function'] in ('stop', 'defer') and e['kind'] == 'call'):
        d = {k: v for k, v in e.items() if k not in ('event', 'monotonic', 'pid', 'thread')}
        if 'argv' in d: d = d['argv'][1]
        print('%6.2f %s %s' % (e['monotonic'] - t0, e['event'], str(d)[:200]))
