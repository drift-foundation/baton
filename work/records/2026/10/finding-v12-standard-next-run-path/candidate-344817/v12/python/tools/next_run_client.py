#!/usr/bin/python3 -I
"""Unprivileged convenience client for one exact managed admission command."""
import json
import subprocess
import sys

ENTRY = '/opt/baton-next-run/entry.py'


def request(argv, stream):
    if argv == ['prepare']:
        raw = stream.read(1024 * 1024 + 1)
        if len(raw) > 1024 * 1024:
            raise ValueError('task exceeds1MiB')
        return {'action': 'prepare', 'task': json.loads(raw)}
    if len(argv) == 2 and argv[0] in ('check', 'start', 'status'):
        return {'action': argv[0], 'run': argv[1]}
    raise ValueError('prepare < task.json | check|start|status RUN')


def main(argv=None):
    value = request(sys.argv[1:] if argv is None else argv, sys.stdin.buffer)
    # Client parsing grants no trust. The protected entry independently checks
    # shape, limits, caller and custody; this never executes arbitrary argv.
    return subprocess.run(['/usr/bin/sudo', '-n', ENTRY, 'request'], input=json.dumps(value).encode()).returncode


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (ValueError, OSError) as failure:
        print('next-run client refused: ' + str(failure), file=sys.stderr)
        raise SystemExit(2)
