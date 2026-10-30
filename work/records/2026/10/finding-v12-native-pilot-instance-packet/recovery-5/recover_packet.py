"""Guarded, separately owner-selected application; never submits or starts a Job."""
import argparse
from contextlib import ExitStack
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import stat

from baton_v12.worker_manager import ControlStore, outstanding_offers, recover_on_restart
from baton_v12.worker_manager.workspaces import configured_workspace_storage, hold_manager_instance
from tools import job_manager

DEST = Path('/home/sl/baton-instances/native-coordination-pilot-w321608-1')
PACKET = Path(__file__).resolve().parent


def now():
    return datetime.now(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read_state(root):
    selector = json.loads((root / 'instance.json').read_text())
    with ControlStore.open_readonly(selector['control_store'], incarnation='w325959-recovery-read', clock=now) as control:
        workspace = configured_workspace_storage(control).place
        offers = outstanding_offers(control)
    output = io.StringIO()
    code = job_manager.main(['--store', selector['job_store'], '--incarnation', 'w325959-recovery-read', '--authority-uuid', selector['authority_uuid'], 'status', '--control', selector['control_store']], stream=output)
    if code != 0:
        raise RuntimeError('canonical Job readback refused')
    status = json.loads(output.getvalue())
    if not status['canonical']:
        raise RuntimeError('noncanonical Job observation')
    return {'authority_uuid': selector['authority_uuid'], 'workspace_root': workspace, 'outstanding_offers': offers, 'jobs': status['jobs']}


def checked_bytes(path):
    held = path.lstat()
    if not stat.S_ISREG(held.st_mode) or path.resolve() != path.absolute():
        raise RuntimeError('non-regular or symlink target: ' + str(path))
    return path.read_bytes(), stat.S_IMODE(held.st_mode)


def preflight(root, packet, *, phase, resume=False):
    pin = json.loads((packet / 'CHANGE.json').read_text())
    if str(root) != pin['destination']:
        raise RuntimeError('wrong destination')
    for record in pin['stores'].values():
        held = Path(record['path']).stat()
        if (held.st_dev, held.st_ino) != (record['device'], record['inode']):
            raise RuntimeError('store replaced: ' + record['path'])
    if read_state(root) != pin['state']:
        raise RuntimeError('committed workspace or retained Job/episode/offer state changed')
    if pin['state']['outstanding_offers']:
        raise RuntimeError('this recovery only covers no issued/accepted/claimed offers')
    for name, expected in pin['preserved_files'].items():
        data, mode = checked_bytes(root / name)
        if sha(data) != expected['sha256'] or mode != expected['mode']:
            raise RuntimeError('preserved file changed: ' + name)
    states = []
    for name, item in pin['changes'].items():
        data, mode = checked_bytes(root / name)
        if mode != item['mode'] or not mode & stat.S_IWUSR:
            raise RuntimeError('target mode changed or not owner-writable: ' + name)
        candidate = (packet / 'after' / name).read_bytes()
        if sha(candidate) != item['after']:
            raise RuntimeError('candidate digest mismatch: ' + name)
        current = sha(data)
        state = 'before' if current == item['before'] else 'after' if current == item['after'] else 'drift'
        if state == 'drift':
            raise RuntimeError('target byte drift: ' + name)
        states.append(state)
    if phase == 'recover' and any(s != 'after' for s in states):
        raise RuntimeError('apply all reviewed bytes before recovery')
    if phase == 'apply' and len(set(states)) > 1 and not resume:
        raise RuntimeError('partial application; inspect and explicitly select --resume')
    return pin


def apply_bytes(root, packet, pin):
    """Only reviewed JSON replacements, no bootstrap/rebinding/store rewrite."""
    for name, item in pin['changes'].items():
        target = root / name
        current = sha(target.read_bytes())
        if current == item['after']:
            continue
        if current != item['before']:
            raise RuntimeError('target changed during application: ' + name)
        temporary = target.with_name(target.name + '.w325959-recovery-5.tmp')
        # Exclusive staging preserves an interrupted candidate for inspection.
        with temporary.open('xb') as handle:
            handle.write((packet / 'after' / name).read_bytes())
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, item['mode'])
        os.replace(temporary, target)
        if sha(target.read_bytes()) != item['after'] or stat.S_IMODE(target.stat().st_mode) != item['mode']:
            raise RuntimeError('replacement readback mismatch: ' + name)


def execute(root, packet, phase, *, resume=False):
    pin = preflight(root, packet, phase=phase, resume=resume)
    selector = json.loads((root / 'instance.json').read_text())
    with ExitStack() as stack:
        read = stack.enter_context(ControlStore.open_readonly(selector['control_store'], incarnation='w325959-recovery-guard', clock=now))
        # Guard both old roots: even the failing two-root manager must be absent.
        for place in pin['guard_roots']:
            stack.enter_context(hold_manager_instance(read, place))
        preflight(root, packet, phase=phase, resume=resume)
        if phase == 'apply':
            apply_bytes(root, packet, pin)
            answer = {'applied': list(pin['changes'])}
        else:
            # This is the public recovery boundary; it does not sweep, offer,
            # claim, launch, resubmit or replace Job episodes. Exact empty-offer
            # state is guarded above; any other recovery state refuses here.
            with ControlStore.open(selector['control_store'], incarnation='w325959-owner-recovery-5', clock=now) as control:
                answer = recover_on_restart(control, now=now())
                if answer['abandoned'] or answer['recoverable']:
                    raise RuntimeError('unexpected recovery result; preserve and inspect')
        preflight(root, packet, phase='recover')
    return {'operation': phase, 'result': answer, 'state_preserved': True, 'at': now()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=('check', 'apply', 'recover'))
    parser.add_argument('--owner-selected', action='store_true')
    parser.add_argument('--resume', action='store_true')
    args = parser.parse_args()
    if args.operation == 'check':
        pin = preflight(DEST, PACKET, phase='apply', resume=args.resume)
        print(json.dumps({'state': pin['state'], 'changes': pin['changes']}, indent=2))
    else:
        if not args.owner_selected:
            raise SystemExit('REFUSED: application/recovery requires separate owner selection')
        print(json.dumps(execute(DEST, PACKET, args.operation, resume=args.resume), indent=2))


if __name__ == '__main__':
    main()
