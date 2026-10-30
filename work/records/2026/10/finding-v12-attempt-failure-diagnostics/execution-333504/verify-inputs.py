"""Read-only input check for the W333486 execution packet.

Opens no store, writes nothing, starts nothing. It proves that every pinned
input is still its declared bytes, that the declared base still holds the exact
manager and supervisor source this packet stages, that the historical bootstrap
binary has not moved, that the task carries the sealed gate's own module names,
and that neither gate module the turn must CREATE already exists on the host.

Run this first. A drifted input means this packet is describing something that
is no longer there, and re-sealing it at the new bytes is the correct response
-- never editing a pin to match.
"""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
REPO = Path('/home/sl/src/baton')
DISTRO = Path('/home/sl/baton-runs/managed-correction-236087/build/stack/out/distro')
OLD = 'work/records/2026/09/finding-v12-single-implementation-proof'
OWED = ('v12/python/tests/manager/test_attempt_failure_cause.py',
        'v12/python/tests/tools/test_attempt_diagnostics.py')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def blob(base, relative):
    return hashlib.sha256(subprocess.check_output(
        ['git', 'show', base + ':' + relative], cwd=REPO)).hexdigest()


def main():
    pins = json.loads((HERE / 'PREPARATION-PINS.json').read_text())
    base = pins['base']
    wrong = []

    for name, expected in pins['files'].items():
        held = sha(REPO / name) if (REPO / name).is_file() else None
        if held != expected:
            wrong.append(f'preparation input {name}: {held} != {expected}')

    if sha(DISTRO / 'baton-v12-stack') \
            != pins['historical_bootstrap_binary_sha256']:
        wrong.append('the historical bootstrap binary is not its declared bytes')

    for relative, expected in pins['manager_files'].items():
        try:
            held = blob(base, 'v12/python/' + relative)
        except subprocess.CalledProcessError:
            held = None
        if held != expected:
            wrong.append(f'base manager source {relative}: {held} != {expected}')

    for name, expected in pins['supervisor_files'].items():
        try:
            held = blob(base, OLD + '/' + name)
        except subprocess.CalledProcessError:
            held = None
        if held != expected:
            wrong.append(f'base supervisor source {name}: {held} != {expected}')

    for name in pins['task_inputs']:
        if not (REPO / name).is_file():
            wrong.append(f'declared task input is absent: {name}')

    # THE SEALED ARGV AND THE TASK MUST NAME THE SAME TWO NEW MODULES. A gate
    # that asks for a module the task never mentions is a gate the turn cannot
    # satisfy, and the mismatch is silent until the provider turn is over.
    task = (HERE / 'TASK.md').read_text()
    program = (HERE / 'prepare.py').read_text()
    for name in OWED:
        if name not in task:
            wrong.append(f'the task does not name the gate module {name}')
        dotted = name[len('v12/python/'):-len('.py')].replace('/', '.')
        if repr(dotted) not in program and f"'{dotted}'" not in program:
            wrong.append(f'the sealed gate does not name {dotted}')
        if (REPO / name).exists():
            wrong.append(f'a gate module the turn must create already exists '
                         f'on the host: {name}')

    provenance = json.loads((HERE / 'PROVENANCE.json').read_text())
    if provenance['base'] != base or provenance['accepted'] is not False:
        wrong.append('the provenance disagrees with these pins')
    if provenance['checkpoint']['paths']:
        wrong.append('the provenance declares a restored buffer this '
                     'preparation does not carry')

    if wrong:
        for one in wrong:
            print('DRIFTED: ' + one)
        return 1
    print(f'inputs verified against {base}: '
          f'{len(pins["manager_files"])} manager files, '
          f'{len(pins["supervisor_files"])} supervisor files, '
          f'{len(pins["files"])} preparation inputs, '
          f'{len(pins["task_inputs"])} task inputs, '
          f'{len(OWED)} gate modules still owed')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
