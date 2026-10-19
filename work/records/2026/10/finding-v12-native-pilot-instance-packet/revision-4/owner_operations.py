"""Proposed owner-run operations. Never invoked by the preparation proof.

Requires explicit owner selection outside this script. No submission or serving.
"""
import argparse
import json
import pathlib
import subprocess

import prepare
from tools import bootstrap, instance


def git_read(source, *args):
    return subprocess.run(['git', '-C', str(source), *args], check=True, capture_output=True, text=True, timeout=30).stdout.strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=('repositories', 'configure'))
    parser.add_argument('--owner-selected', action='store_true', required=True)
    parser.add_argument('--source', help='Owner-prepared checkout whose HEAD equals the selected base')
    args = parser.parse_args()
    revision = pathlib.Path(__file__).resolve().parent
    packet = revision.parent
    prepare.verify_frozen(revision)  # Before any effect.
    root = prepare.SELECTED
    places = instance.layout(root)
    document = prepare.configuration(packet, 'configure-inputs.json')
    if args.operation == 'repositories':
        if pathlib.Path(root).exists():
            raise SystemExit('REFUSED: selected destination already exists; preserve it and inspect the prior operation')
        if not args.source or git_read(args.source, 'rev-parse', 'HEAD') != prepare.BASE:
            raise SystemExit('REFUSED: source HEAD must be the pinned base before repository creation')
        if git_read(args.source, 'status', '--porcelain'):
            raise SystemExit('REFUSED: source checkout must have no uncommitted changes')
        document['jobs'][0]['work_id'] = '12345678-W1'  # Plan-only; never registered.
        answer = bootstrap.prepare_repositories(document, places, source=str(pathlib.Path(args.source).resolve()))
        print(json.dumps(answer, indent=2))
        return 0
    # Every repository is real and independent, with the selected base available.
    # These read-only checks precede authority registration or task writes.
    document['jobs'][0]['work_id'] = '12345678-W1'
    bootstrap.repositories_proved(document, places, bootstrap.repository_plan(document, places))
    for _, path, _ in bootstrap.repository_plan(document, places):
        if git_read(path, 'rev-parse', 'HEAD') != prepare.BASE:
            raise SystemExit('REFUSED: repository HEAD differs from selected base: ' + path)
    if not pathlib.Path(places['instance']).is_file():
        raise SystemExit('REFUSED: install once with --no-repositories before configuration')
    checks = prepare.Checks()
    answer = prepare.pass_two_binds_the_two_stage_job(packet, root, checks, preflight=False)
    prepare.say(pathlib.Path(root) / 'generated', 'preparation-readback.json', {'result': answer, 'checks': checks.document()})
    print(json.dumps(answer, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
