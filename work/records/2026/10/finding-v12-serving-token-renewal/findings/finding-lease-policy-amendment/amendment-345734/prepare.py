"""Minimal sealed task substitution over the reviewed preparation vehicle.

--verify is read-only. stage/bind require the parent's joined readiness and exact
successor selection; this adapter itself neither selects nor launches execution.
"""
import argparse
import hashlib
import json
from pathlib import Path
import types

HERE = Path(__file__).resolve().parent
PRIOR = HERE.parents[2] / 'continuation-339444'
ROOT = Path('/home/sl/baton-instances/serving-renewal-w333485-339444')
OLD_MANIFEST = '0f8eba8caa8eca82639f83b184c90dbafd7a19757be7fe6336c5494ce4329adb'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load():
    amendment = json.loads((HERE / 'AMENDMENT.json').read_text())
    if sha(PRIOR / 'PACKET-INPUTS.json') != OLD_MANIFEST or amendment['predecessor_sha256'] != OLD_MANIFEST:
        raise RuntimeError('predecessor binding drift')
    prior = json.loads((PRIOR / 'PACKET-INPUTS.json').read_text())
    for root, files in ((PRIOR, prior['files']), (HERE, amendment['files'])):
        for name, digest in files.items():
            if Path(name).is_absolute() or '..' in Path(name).parts or sha(root / name) != digest:
                raise RuntimeError('sealed input mismatch: ' + name)
    # One expression changes. All setup/bootstrap/composition/restoration/source
    # machinery remains inherited verbatim, with its original __file__/HERE.
    source = (PRIOR / 'prepare.py').read_text()
    old = "task_instructions=(HERE / 'TASK.md').read_text(),"
    new = "task_instructions=AMENDED_TASK.read_text(),"
    if source.count(old) != 1:
        raise RuntimeError('reviewed task expression no longer unique')
    module = types.ModuleType('reviewed_preparation')
    module.__file__ = str(PRIOR / 'prepare.py')
    module.AMENDED_TASK = HERE / 'TASK.md'
    exec(compile(source.replace(old, new), module.__file__, 'exec'), module.__dict__)
    original_pins = module.pins
    def pins():
        selected = original_pins()
        old_task = str((PRIOR / 'TASK.md').relative_to(module.REPO))
        new_task = str((HERE / 'TASK.md').relative_to(module.REPO))
        selected['task_inputs'] = [new_task if name == old_task else name for name in selected['task_inputs']]
        for name in ('TOK-9.md', 'AMENDMENT.json'):
            selected['task_inputs'].append(str((HERE / name).relative_to(module.REPO)))
        return selected
    module.pins = pins
    return module


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('step', choices=['verify', 'stage', 'bind'])
    parser.add_argument('--root', type=Path)
    args = parser.parse_args()
    module = load()
    if args.step == 'verify':
        if args.root is not None: parser.error('verify takes no root')
        pins = module.pins()
        print(json.dumps({'state': 'amendment-pins-match-not-launched', 'run': module.RUN, 'base': module.BASE, 'task_inputs': pins['task_inputs'], 'bounds': module.BOUNDS, 'gate': module.GATE}, sort_keys=True))
    else:
        if args.root != ROOT: parser.error('exact selected root required')
        getattr(module, args.step)(args.root)


if __name__ == '__main__':
    main()
