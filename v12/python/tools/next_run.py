"""Reusable input preparation over an operator-installed authoring environment.

This command is NOT a privileged broker. Installation selects already provisioned
slots; each slot has its own authority/work and operational roots. No environment
variable or task input may supply arbitrary installation configuration. A slot
is retained after consumption, including uncertain failure, and never recycled.
"""
import argparse
import contextlib
import copy
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
import time

from tools import authoring_baseline as baseline
from tools import authoring_enforcement as enforcement
from tools import next_run_bindings as bindings
from tools import stage_execution

SCHEMA = 'baton.next-run-installation/1'
TASK = 'baton.next-run-input/1'
NAME = re.compile(r'[a-z][a-z0-9-]{0,63}')


class Refusal(ValueError):
    pass


def sha(data):
    return hashlib.sha256(data).hexdigest()


def encode(value):
    return (json.dumps(value, sort_keys=True, indent=2) + '\n').encode()


def read(path):
    path = Path(path)
    for parent in reversed(path.absolute().parents):
        if parent.is_symlink():
            raise Refusal('symlink ancestor: ' + str(parent))
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, 'rb') as stream:
        st = os.fstat(stream.fileno())
        if not stat.S_ISREG(st.st_mode) or st.st_nlink != 1:
            raise Refusal('regular unlinked input required: ' + str(path))
        return stream.read()


def document(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise Refusal('duplicate JSON member: ' + key)
            result[key] = value
        return result
    return json.loads(read(path), object_pairs_hook=unique)


def create(path, value):
    data = encode(value)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    directory = os.open(Path(path).parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)


def directory(path, *, make=False):
    path = Path(path)
    if not path.is_absolute() or '..' in path.parts:
        raise Refusal('absolute canonical directory required: ' + str(path))
    # Validate ancestors before mkdir, including a dangling final symlink.
    for parent in [*reversed(path.parents), path]:
        try:
            st = parent.lstat()
        except FileNotFoundError:
            if not make:
                raise
            parent.mkdir(mode=0o700)
            st = parent.lstat()
        if not stat.S_ISDIR(st.st_mode):
            raise Refusal('non-directory or link: ' + str(parent))
    return path


def private(path, *, make=False):
    place = directory(path, make=make)
    st = place.stat()
    if st.st_uid != os.getuid() or st.st_mode & 0o077:
        raise Refusal('private executor-owned directory required: ' + str(place))
    return place


@contextlib.contextmanager
def lock(root):
    private(root)
    fd = os.open(root / '.lock', os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            raise Refusal('installation lock is not regular')
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield
    finally:
        os.close(fd)


def inventory(selected):
    manager = Path(selected['manager_source'])
    paths = [manager / name for name in bindings._tree(str(manager))]
    paths += [Path(selected['supervisor_path']), Path(selected['vectors']),
              Path(selected['instance']['runtime_path']) / 'baton-v12-stack']
    return {str(path): sha(read(path)) for path in sorted(set(paths))}


def install(root, inputs):
    """Capture an existing environment once; refuse partial/occupied installs.

    Bootstrap owns Authority provisioning. This bounded layer neither invents
    capabilities nor treats permission failures as permission to provision them.
    """
    root = Path(root).absolute()
    if set(inputs) != {'schema', 'slots'} or inputs['schema'] != SCHEMA:
        raise Refusal('unsupported installation document')
    if not isinstance(inputs['slots'], dict) or not inputs['slots']:
        raise Refusal('at least one independently provisioned slot required')
    captured = copy.deepcopy(inputs)
    seen_stores, seen_works = set(), set()
    for name, slot in captured['slots'].items():
        if not NAME.fullmatch(name) or set(slot) != {'base', 'compose'}:
            raise Refusal('slot names base and compose selections')
        bindings._base_object(slot['base'])
        selected = slot['compose']
        forbidden = {'run_root', 'run_id', 'base', 'context_mode', 'task_instructions', 'verification', 'verification_seconds', 'bounds', 'places'} & set(selected)
        if forbidden:
            raise Refusal('routine operands cannot be installation overrides: ' + repr(sorted(forbidden)))
        if selected['supervisor_path'] != str(Path(baseline.__file__).resolve()):
            raise Refusal('installation must bind the loaded product supervisor')
        if Path(selected['manager_source']).resolve() != Path(__file__).resolve().parents[1]:
            raise Refusal('installation must bind the loaded manager source')
        instance = selected['instance']
        work = (instance['authority_uuid'], selected['participants']['work_id'])
        if work in seen_works:
            raise Refusal('slots cannot share a Work')
        seen_works.add(work)
        for key in ('job_store', 'control_store'):
            path = Path(instance[key]).absolute()
            directory(path.parent)
            if str(path) in seen_stores:
                raise Refusal('slots cannot share operational stores')
            seen_stores.add(str(path))
        slot['inventory'] = inventory(selected)
    # No setup/launch/store opening happened above. Partial publication remains
    # visible and cannot be mistaken for a ready installation.
    directory(root.parent)
    root.mkdir(mode=0o700)
    (root / 'runs').mkdir(mode=0o700)
    create(root / 'installation.json', captured)
    return {'installation': str(root), 'slots': list(captured['slots']), 'state': 'installed-configuration', 'privileged_provisioning': 'external bootstrap prerequisite'}


def installed(root):
    root = Path(root).absolute()
    private(root)
    held = document(root / 'installation.json')
    if held.get('schema') != SCHEMA:
        raise Refusal('unknown installation')
    return root, held


def validate_inventory(slot):
    current = inventory(slot['compose'])
    if current != slot['inventory']:
        raise Refusal('installation source/runtime inventory changed; new reviewed installation required')


def task_input(value, slot):
    members = {'schema', 'run_id', 'instructions', 'files', 'base', 'verification', 'limits'}
    if set(value) != members or value['schema'] != TASK:
        raise Refusal('unsupported task input')
    if not isinstance(value['run_id'], str) or not NAME.fullmatch(value['run_id']):
        raise Refusal('invalid run identity')
    if value['base'] != slot['base']:
        raise Refusal('task base differs from accepted installation base')
    if not isinstance(value['instructions'], str) or not value['instructions'].strip():
        raise Refusal('nonempty task instructions required')
    if not isinstance(value['verification'], list) or not value['verification'] or any(not isinstance(x, str) or not x for x in value['verification']):
        raise Refusal('verification argv required')
    limits = value['limits']
    if set(limits) != {'provider', 'verification', 'total', 'cleanup'} or any(type(x) is not int or not 1 <= x <= 86400 for x in limits.values()):
        raise Refusal('explicit positive integer provider/verification/total/cleanup limits required')
    if limits['total'] <= limits['cleanup'] + limits['provider'] + limits['verification']:
        raise Refusal('total must reserve provider, verification and cleanup time')
    files = value['files']
    if not isinstance(files, list) or not files or len(set(files)) != len(files):
        raise Refusal('distinct selected source files required')
    source = Path(slot['compose']['source_root'])
    pinned = {}
    for name in files:
        if not isinstance(name, str) or Path(name).is_absolute() or any(p in ('', '.', '..') for p in name.split('/')):
            raise Refusal('selected file must be repository-relative')
        pinned[name] = sha(read(source / name))
    return pinned


def prepare(root, slot_name, value):
    received = time.monotonic()
    root, configured = installed(root)
    if slot_name not in configured['slots']:
        raise Refusal('unknown slot')
    slot = configured['slots'][slot_name]
    validate_inventory(slot)
    files = task_input(value, slot)
    run = root / 'runs' / value['run_id']
    with lock(root):
        # A slot has one run, retained indefinitely after consumption. Failed
        # partial composition is not silently overwritten or deemed reusable.
        assignment = root / (slot_name + '.assigned.json')
        if assignment.exists() or run.exists() or (root / ('run-' + value['run_id'] + '.json')).exists():
            raise Refusal('slot or run already assigned; inspect/recover the retained run')
        create(root / ('run-' + value['run_id'] + '.json'), {'run_id': value['run_id'], 'slot': slot_name})
        create(assignment, {'run_id': value['run_id'], 'input_sha256': sha(encode(value))})
        selected = copy.deepcopy(slot['compose'])
        selected['participants']['fixture_files'] = files
        limits = value['limits']
        documents = bindings.compose(**selected, run_root=str(run), base=value['base'], run_id=value['run_id'], context_mode='fresh', task_instructions=value['instructions'], verification=value['verification'], verification_seconds=limits['verification'], bounds={'turn_seconds': limits['provider'], 'total_seconds': limits['total'], 'cleanup_seconds': limits['cleanup'], 'implementer_invocations': 1, 'retry': False})
        places = bindings.write(str(run), documents)
        os.chmod(run, 0o700)
        create(run / 'input.json', value)
        packet = baseline.held_packet(places['PACKET.json'])
        baseline.verify_imported_sources(packet)
        enforcement.verify_controller(packet)
        helper = str(Path(enforcement.__file__).with_name('authoring_shutdown.py').relative_to(Path(packet['manager_source']['path'])))
        if helper not in packet['manager_source']['files']:
            raise Refusal('shutdown helper is not bound')
        # Supersede composer commands before publishing readiness. Partial runs
        # never have a ready receipt and cannot be started through this tool.
        command = [sys.executable, '-B', '-m', 'tools.next_run']
        commands = {'start': command + ['start', '--installation', str(root), '--run', value['run_id']], 'status': command + ['status', '--installation', str(root), '--run', value['run_id']], 'recover': command + ['recover', '--installation', str(root), '--run', value['run_id']], 'environment': {'PYTHONPATH': os.pathsep.join([str(Path(selected['manager_source']) / 'src'), selected['manager_source']]), 'PYTHONDONTWRITEBYTECODE': '1'}, 'controller': [sys.executable, '-B', '-m', 'tools.authoring_enforcement', '--packet', places['PACKET.json']]}
        # commands.json is still unpublished preparer output, never a receipt.
        (run / 'commands.json').write_bytes(encode(commands))
        receipt = {'schema': 'baton.next-run-ready/1', 'slot': slot_name, 'run_id': value['run_id'], 'input_sha256': sha(encode(value)), 'files': {p.name: sha(read(p)) for p in run.iterdir() if p.is_file()}, 'installation_sha256': sha(read(root / 'installation.json')), 'preparation_seconds': time.monotonic() - received, 'work_start': 'unknown', 'candidate_acceptance': 'not implied'}
        create(run / 'ready.json', receipt)
        return receipt


def held_run(root, name):
    root, configured = installed(root)
    if not NAME.fullmatch(name):
        raise Refusal('invalid run identity')
    run = private(root / 'runs' / name)
    receipt = document(run / 'ready.json')
    if receipt['run_id'] != name or sha(read(root / 'installation.json')) != receipt['installation_sha256']:
        raise Refusal('foreign or changed installation/run binding')
    slot = configured['slots'][receipt['slot']]
    assigned = document(root / (receipt['slot'] + '.assigned.json'))
    if assigned != {'run_id': name, 'input_sha256': receipt['input_sha256']}:
        raise Refusal('foreign slot assignment')
    validate_inventory(slot)
    for rel, expected in receipt['files'].items():
        if Path(rel).name != rel or sha(read(run / rel)) != expected:
            raise Refusal('changed prepared input: ' + rel)
    packet = baseline.held_packet(str(run / 'PACKET.json'))
    baseline.verify_imported_sources(packet)
    enforcement.verify_controller(packet)
    return root, run, receipt, packet


def prerequisites(packet):
    """Prepare required parents before admission, never follow a planted link."""
    paths = [Path(packet['outcome_path']).parent]
    paths += [Path(packet['deployment'][key]).parent for key in ('job_store', 'control_store')]
    deployment = document(packet['deployment']['config_path'])
    paths.append(Path(deployment['state_root']))
    for worker in deployment['workers']:
        for key in ('workspace_storage', 'launch_home', 'credential_home'):
            paths.append(Path(worker['deployment'][key]))
    for path in paths:
        private(path, make=True)
    stage_execution.held_configuration(deployment, checkout=packet['code_boundary'])


def start(root, name):
    root, run, receipt, packet = held_run(root, name)
    with lock(root):
        if (run / 'consumed.json').exists():
            raise Refusal('consumed run: recover reports retained evidence; no replay')
        prerequisites(packet)
        # Engine availability/image identity is a prerequisite, not an effect.
        baseline.verify_worker_image(packet, image_inspect=baseline._engine_inspect)
        create(run / 'consumed.json', {'ready_sha256': sha(read(run / 'ready.json')), 'run_id': name, 'state': 'dispatch-uncertain', 'time_ns': time.time_ns()})
        # Keep the lock through dispatch. Any exception/kill leaves consumption
        # intact. Recovery never interprets a missing outcome as no effects.
        old = os.environ.get('BATON_V12_STAGE_EXECUTION_CONFIG')
        os.environ['BATON_V12_STAGE_EXECUTION_CONFIG'] = packet['deployment']['config_path']
        try:
            result = enforcement.main(['--packet', str(run / 'PACKET.json')])
            create(run / 'controller-return.json', {'status': result, 'candidate_acceptance': 'requires independent review'})
            return result
        finally:
            if old is None:
                os.environ.pop('BATON_V12_STAGE_EXECUTION_CONFIG', None)
            else:
                os.environ['BATON_V12_STAGE_EXECUTION_CONFIG'] = old


def status(root, name):
    root, _ = installed(root)
    if not NAME.fullmatch(name):
        raise Refusal('invalid run identity')
    run = root / 'runs' / name
    # Read-only even after interrupted preparation. Do not open/create stores.
    result = {'run_id': name, 'state': 'partial', 'work_start': 'unknown', 'candidate_acceptance': 'not implied'}
    for file, key in [('ready.json', 'ready'), ('consumed.json', 'consumed'), ('controller-return.json', 'controller_return')]:
        try:
            result[key] = document(run / file)
        except FileNotFoundError:
            pass
    if 'consumed' in result:
        result['state'] = 'consumed-held'
        result['recovery'] = 'retain evidence; no replay; controller result/cessation requires independent assessment'
    elif 'ready' in result:
        result['state'] = 'prepared'
        result['recovery'] = 'start revalidates all prerequisites before consumption'
    else:
        result['recovery'] = 'partial preparation retained; no dispatch admitted'
    return result


def recover(root, name):
    """Release only a never-consumed reservation; preserve every old run byte.

    Missing ready/consumed receipts mean this launcher could not dispatch: the
    exclusive consumption record is fsynced before calling the controller.
    Consumed runs are held regardless of exit code or missing result evidence.
    """
    root, configured = installed(root)
    if not NAME.fullmatch(name):
        raise Refusal('invalid run identity')
    with lock(root):
        report = status(root, name)
        if 'consumed' in report:
            return report
        for slot in configured['slots']:
            assigned = root / (slot + '.assigned.json')
            try:
                held = document(assigned)
            except FileNotFoundError:
                continue
            if held['run_id'] != name:
                continue
            # Publish evidence before releasing the reservation. An interrupted
            # recovery can repeat using the same receipt, never a reset.
            released = root / (slot + '.released-' + name + '.json')
            evidence = {'assignment': held, 'reason': 'never consumed', 'run_id': name}
            if released.exists():
                if document(released) != evidence:
                    raise Refusal('conflicting recovery evidence')
            else:
                create(released, evidence)
            assigned.unlink()
            report['recovery'] = 'reservation released; preserve old run; prepare a NEW run identity in the same slot'
            report['state'] = 'unconsumed-released'
            return report
        return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['install', 'prepare', 'start', 'status', 'recover'])
    parser.add_argument('--installation', required=True)
    parser.add_argument('--inputs')
    parser.add_argument('--slot')
    parser.add_argument('--run')
    args = parser.parse_args(argv)
    try:
        if args.action == 'install':
            answer = install(args.installation, document(args.inputs))
        elif args.action == 'prepare':
            answer = prepare(args.installation, args.slot, document(args.inputs))
        elif args.action == 'start':
            return start(args.installation, args.run)
        elif args.action == 'recover':
            answer = recover(args.installation, args.run)
        else:
            answer = status(args.installation, args.run)
        print(json.dumps(answer, sort_keys=True))
        return 0
    except (OSError, ValueError, TypeError, KeyError, bindings.BindingRefusal, baseline.SupervisorRefusal, RuntimeError) as error:
        print('next-run refused: ' + str(error), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
