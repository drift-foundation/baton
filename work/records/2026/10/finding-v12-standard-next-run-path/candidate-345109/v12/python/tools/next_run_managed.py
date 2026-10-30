"""One-time trusted installation and automatic, nonrecycling run allocation.

Only installed next_run_entry.py is a managed privilege entry. This module is
loaded from its root-protected inventory, never from a caller-selected Python
path. Installation is an operator act; test Host substitutions are not CLI inputs.
"""
import copy
import fcntl
import hashlib
import io
import json
import os
from pathlib import Path
import pwd
import grp
import shutil
import stat
import subprocess
import sys
import tempfile
import uuid

from tools import bootstrap, next_run as nr, next_run_bindings as bindings
from tools import authoring_baseline as baseline
from tools import authoring_enforcement as enforcement

ROOT = Path('/opt/baton-next-run')
STORAGE = Path('/var/lib/baton-next-run')
SCHEMA = 'baton.managed-next-run-installation/1'


def admission_rule(root, caller_uid):
    # Literal argument matching is supported by the selected sudo-rs. Dynamic
    # input is bounded JSON on stdin, not an argument wildcard or interpreter.
    return (f'#{caller_uid} ALL=(root) NOPASSWD: {root / "entry.py"} request\n').encode()


def dispatch_environment(record, packet, root):
    operational = Path(record['storage'])
    manager = root / 'code'
    # Initial -I boot receives explicit roots; subsequent fresh -m children
    # inherit ONLY these installed roots, never the caller's Python settings.
    return {'PATH': '/usr/bin:/bin', 'HOME': str(operational / 'home'), 'TMPDIR': str(operational / 'tmp'), 'LANG': 'C.UTF-8', 'PYTHONDONTWRITEBYTECODE': '1', 'PYTHONNOUSERSITE': '1', 'PYTHONPATH': os.pathsep.join([str(manager / 'src'), str(manager)]), 'BATON_V12_STAGE_EXECUTION_CONFIG': packet['deployment']['config_path']}


class Host:
    """The privileged OS boundary; no shell strings or caller-supplied commands."""
    def require_root(self):
        if os.geteuid() != 0:
            raise nr.Refusal('operator root execution required')

    def owned(self, path, uid=0, private=False):
        st = path.lstat()
        if stat.S_ISLNK(st.st_mode) or st.st_uid != uid or st.st_mode & (0o077 if private else 0o022):
            raise nr.Refusal('unsafe custody: ' + str(path))

    def chown(self, path, uid, gid):
        os.chown(path, uid, gid, follow_symlinks=False)

    def account(self, name):
        try:
            pwd.getpwnam(name)
        except KeyError:
            pass
        else:
            raise nr.Refusal('execution account already exists; preserve partial installation')
        subprocess.run(['/usr/sbin/useradd', '--system', '--user-group', '--no-create-home', '--home-dir', '/nonexistent', '--shell', '/usr/sbin/nologin', name], check=True, timeout=30)
        entry = pwd.getpwnam(name)
        return {'uid': entry.pw_uid, 'gid': entry.pw_gid}

    def admission(self, root, caller_uid):
        # The fixed wrapper parses every operand and accepts no Python/config
        # path. request reads bounded JSON on stdin. No environment preserved.
        target = Path('/etc/sudoers.d/baton-next-run')
        if target.exists():
            raise nr.Refusal('admission already exists; no overwrite')
        entry = str(root / 'entry.py')
        data = admission_rule(root, caller_uid)
        temporary = root / 'admission.sudoers'
        exclusive(temporary, data, mode=0o440)
        subprocess.run(['/usr/sbin/visudo', '-cf', str(temporary)], check=True, timeout=10)
        exclusive(target, data, mode=0o440)

    def authority_check(self, record, packet, root, work_id):
        # SQLite read-only may create WAL sidecars. Open as the execution uid,
        # never as root, so a check cannot strand root-owned operational files.
        script = "import os,sys,json;os.setgroups(json.loads(sys.argv[1]));os.setgid(int(sys.argv[2]));os.setuid(int(sys.argv[3]));os.umask(0o077);sys.path[:0]=sys.argv[4:6];from tools.next_run_confinement import restrict_writes;restrict_writes(sys.argv[6]);from baton_v12.authority import Authority;a=Authority.open_readonly(sys.argv[7],expected_authority_uuid=sys.argv[8]);w=a.project_work(sys.argv[9]);a.dispose();sys.exit(0 if w['status']=='open' else 2)"
        result = subprocess.run(['/usr/bin/python3', '-I', '-B', '-c', script, json.dumps(record['groups']), str(record['gid']), str(record['uid']), str(root / 'code/src'), str(root / 'code'), record['storage'], packet['deployment']['authority_store'], packet['deployment']['authority_uuid'], work_id], capture_output=True, timeout=20)
        if result.returncode != 0:
            raise nr.Refusal('execution identity cannot read its open Work; authority check refused')

    def processes_stopped(self, record):
        # An exclusive, never-recycled uid is stronger than a saved PID (which
        # can be reused). The broker lock excludes a root dispatch in transition.
        # Inspection errors other than a vanished process are uncertainty.
        for process in Path('/proc').iterdir():
            if not process.name.isdecimal():
                continue
            try:
                lines = (process / 'status').read_text().splitlines()
            except FileNotFoundError:
                continue
            uids = next((line.split()[1:] for line in lines if line.startswith('Uid:')), None)
            if uids is None or len(uids) != 4:
                raise nr.Refusal('cannot establish process identity')
            if record['uid'] in [int(value) for value in uids]:
                raise nr.Refusal('execution identity still has processes; recovery held')

    def recovery_evidence(self, record, packet, root):
        # Run installed owner readers with the old uid, fixed environment and
        # Landlock. Never trust a writable outcome file as cessation evidence.
        script = "import os,sys,json;os.setgroups(json.loads(sys.argv[1]));os.setgid(int(sys.argv[2]));os.setuid(int(sys.argv[3]));os.umask(0o077);sys.path[:0]=sys.argv[4:6];from tools.next_run_confinement import restrict_writes;restrict_writes(sys.argv[6]);from tools.next_run_recovery import inspect;print(json.dumps(inspect(sys.argv[7])))"
        result = subprocess.run(['/usr/bin/python3', '-I', '-B', '-c', script, json.dumps(record['groups']), str(record['gid']), str(record['uid']), str(root / 'code/src'), str(root / 'code'), record['storage'], str(root / 'runs' / record['run_id'] / 'PACKET.json')], env=dispatch_environment(record, packet, root), cwd=root / 'code', capture_output=True, timeout=packet['bounds']['cleanup_seconds'])
        if result.returncode != 0:
            raise nr.Refusal('owner cessation check refused; recovery held')
        return json.loads(result.stdout)

    def dispatch(self, record, packet, root):
        # This process becomes the controller. No privileged Python remains in
        # the execution subtree; cwd/env/import roots are fixed installed paths.
        operational = Path(record['storage'])
        env = dispatch_environment(record, packet, root)
        manager = root / 'code'
        boot = "import sys,runpy;sys.path[:0]=sys.argv[1:3];sys.argv=['tools.authoring_enforcement','--packet',sys.argv[3]];runpy.run_module('tools.authoring_enforcement',run_name='__main__')"
        os.chdir(manager)
        os.setgroups(record['groups'])
        os.setgid(record['gid'])
        os.setuid(record['uid'])
        os.umask(0o077)
        from tools.next_run_confinement import restrict_writes
        restrict_writes(operational)
        os.execve('/usr/bin/python3', ['/usr/bin/python3', '-I', '-B', '-c', boot, str(manager / 'src'), str(manager), str(root / 'runs' / record['run_id'] / 'PACKET.json')], env)
        raise nr.Refusal('exec returned')


def exclusive(path, data, mode=0o600):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, mode)
    with os.fdopen(fd, 'wb') as out:
        out.write(data)
        out.flush()
        os.fsync(out.fileno())
    fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def publish(path, value, mode=0o600):
    # A crash while writing must not expose a truncated reservation/receipt.
    # Linking a fully fsynced sibling publishes without replacing any evidence.
    fd, temporary = tempfile.mkstemp(prefix='.' + path.name + '-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as out:
            os.fchmod(out.fileno(), mode)
            out.write(nr.encode(value))
            out.flush()
            os.fsync(out.fileno())
        os.link(temporary, path, follow_symlinks=False)
    finally:
        os.unlink(temporary)
    directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)


def protected(host, path, directory=False):
    for parent in reversed(path.parents):
        host.owned(parent)
        if not parent.is_dir():
            raise nr.Refusal('unsafe ancestor')
    host.owned(path)
    if directory and not path.is_dir():
        raise nr.Refusal('directory required')
    return path


def own_tree(host, path, uid, gid):
    # Only freshly created private operational trees enter this function.
    for parent, dirs, files in os.walk(path, followlinks=False):
        for name in dirs + files:
            item = Path(parent) / name
            st = item.lstat()
            if not (stat.S_ISREG(st.st_mode) or stat.S_ISDIR(st.st_mode)) or st.st_nlink > 1 and stat.S_ISREG(st.st_mode):
                raise nr.Refusal('linked or special operational output')
            os.chmod(item, 0o700 if item.is_dir() else 0o600)
            host.chown(item, uid, gid)
    os.chmod(path, 0o700)
    host.chown(path, uid, gid)


def source_payload(selected):
    source_manager = Path(selected['manager_source'])
    # Hold every source byte before publication. Never copy tests/scratch or
    # trust a caller-controlled source after the root installation starts.
    held = {}
    for prefix in ('src/baton_v12', 'tools'):
        for path in sorted((source_manager / prefix).rglob('*')):
            if '__pycache__' in path.parts or path.suffix == '.pyc':
                continue
            if path.is_symlink():
                raise nr.Refusal('linked installation source')
            if path.is_file():
                held['code/' + str(path.relative_to(source_manager))] = nr.read(path)
    held['entry.py'] = nr.read(source_manager / 'tools/next_run_entry.py')
    held['client.py'] = nr.read(source_manager / 'tools/next_run_client.py')
    runtime = Path(selected['instance']['runtime_path'])
    for path in sorted(runtime.rglob('*')):
        if path.is_symlink():
            raise nr.Refusal('runtime links require a reviewed packaging rule')
        if path.is_file():
            held['runtime/' + str(path.relative_to(runtime))] = nr.read(path)
    held['vectors.json'] = nr.read(selected['vectors'])
    if 'runtime/baton-v12-stack' not in held:
        raise nr.Refusal('runtime executable missing')
    return held


def payload_digest(held):
    return nr.sha(nr.encode({p: nr.sha(data) for p, data in held.items()}))


def install(inputs, *, root=ROOT, storage=STORAGE, host=None):
    host = Host() if host is None else host
    host.require_root()
    required = {'schema', 'caller_uid', 'capacity', 'groups', 'template', 'credential_sources', 'source_digest'}
    if set(inputs) != required or inputs['schema'] != SCHEMA:
        raise nr.Refusal('unsupported trusted installation input')
    if type(inputs['capacity']) is not int or not 2 <= inputs['capacity'] <= 64 or type(inputs['caller_uid']) is not int or inputs['caller_uid'] <= 0:
        raise nr.Refusal('positive caller and capacity2..64 required')
    if type(inputs['groups']) is not list or any(type(g) is not int or g < 0 for g in inputs['groups']):
        raise nr.Refusal('explicit supplementary group identities required')
    template = inputs['template']
    nr.bindings._base_object(template['base'])
    # Only an operator-selected template supplies paths, executable identity,
    # credentials, participants or limits. Routine input cannot replace them.
    if set(template) != {'base', 'compose'}:
        raise nr.Refusal('template names base and compose')
    selected = template['compose']
    if Path(selected['manager_source']).resolve() != Path(__file__).resolve().parents[1]:
        raise nr.Refusal('install from the reviewed running source tree')
    held = source_payload(selected)
    if payload_digest(held) != inputs['source_digest']:
        raise nr.Refusal('reviewed installation source digest mismatch')
    # Secret reads belong only to this explicit operator installation, once.
    registry = nr.document(inputs['credential_sources'])
    from tools.user_credentials import held_registry
    registry = held_registry(registry)
    secrets = []
    for entry in registry:
        secrets.append((entry, nr.read(entry['path'])))
    protected(host, root.parent, True)
    protected(host, storage.parent, True)
    root.mkdir(mode=0o755)
    storage.mkdir(mode=0o755)
    for name in ('runs', 'state'):
        (root / name).mkdir(mode=0o755 if name == 'runs' else 0o700)
    for rel, data in held.items():
        path = root / rel
        parent = root
        for part in Path(rel).parts[:-1]:
            parent = parent / part
            if not parent.exists(): parent.mkdir(mode=0o755)
        exclusive(path, data, mode=0o755 if rel in ('entry.py', 'client.py', 'runtime/baton-v12-stack') else 0o644)
    accounts = []
    installation_id = uuid.uuid4().hex[:10]
    for index in range(inputs['capacity']):
        account = host.account('bnr-' + installation_id + '-' + str(index))
        if account['uid'] in (0, inputs['caller_uid']) or any(a['uid'] == account['uid'] for a in accounts):
            raise nr.Refusal('execution identity is not exclusive')
        credential_root = storage / ('credentials-' + str(index))
        credential_root.mkdir(mode=0o700)
        copied = []
        for number, (entry, data) in enumerate(secrets):
            target = credential_root / str(number)
            exclusive(target, data)
            copied.append(dict(entry, path=str(target)))
        publish(credential_root / 'sources.json', {'schema': 'baton.user-credential-sources/1', 'sources': copied})
        own_tree(host, credential_root, account['uid'], account['gid'])
        account['credentials'] = str(credential_root / 'sources.json')
        accounts.append(account)
    installed = copy.deepcopy(inputs)
    installed.pop('credential_sources')
    installed.update(accounts=accounts, storage=str(storage), files={p: nr.sha(data) for p, data in held.items()})
    compose = installed['template']['compose']
    compose['credential_sources'] = None
    compose['manager_source'] = str(root / 'code')
    compose['code_boundary'] = str(root / 'code')
    compose['supervisor_path'] = str(root / 'code/tools/authoring_baseline.py')
    compose['vectors'] = str(root / 'vectors.json')
    compose['instance']['runtime_path'] = str(root / 'runtime')
    publish(root / 'installation.json', installed, mode=0o644)
    # Admission publication last. A partial install never enables execution.
    host.admission(root, inputs['caller_uid'])
    publish(root / 'READY', {'installation_sha256': nr.sha(nr.read(root / 'installation.json'))}, mode=0o644)
    return {'state': 'installed', 'capacity': len(accounts), 'root': str(root)}


class Broker:
    def __init__(self, root=ROOT, *, host=None):
        self.host = Host() if host is None else host
        self.host.require_root()
        self.root = Path(root)
        protected(self.host, self.root, True)
        self.config = nr.document(protected(self.host, self.root / 'installation.json'))
        ready = nr.document(protected(self.host, self.root / 'READY'))
        if ready != {'installation_sha256': nr.sha(nr.read(self.root / 'installation.json'))}:
            raise nr.Refusal('installation readiness mismatch')
        for rel, expected in self.config['files'].items():
            if Path(rel).is_absolute() or '..' in Path(rel).parts:
                raise nr.Refusal('invalid inventory member')
            if nr.sha(nr.read(protected(self.host, self.root / rel))) != expected:
                raise nr.Refusal('installed source/runtime drift')

    def locked(self):
        # Root-only state directory; persistent inode never unlinked/replaced.
        return broker_lock(self.host, self.root / 'state')

    def prepare(self, task):
        nr.task_input(task, self.config['template'])
        with self.locked():
            if os.path.lexists(self.root / 'state' / (task['run_id'] + '.prepared.json')):
                raise nr.Refusal('run identity already prepared; use check/start/status')
            return self._continue_preparation(task, recovery_from=None)

    def _prepare(self, task, recovery_from=None, continuation_of=None):
        # Validate the routine input before reserving any account or creating
        # state. It cannot name a slot, source root, identity or executable.
        template = self.config['template']
        files = nr.task_input(task, template)
        name = task['run_id']
        if (self.root / 'state' / (name + '.allocation.json')).exists():
            raise nr.Refusal('run identity already allocated')
        for pending in (self.root / 'state').glob('*.recovery.json'):
            intent = nr.document(protected(self.host, pending))
            if intent['task']['run_id'] == name and intent['run_id'] != recovery_from:
                raise nr.Refusal('run reserved by recovery')
        for pending in (self.root / 'state').glob('*.continuation.json'):
            transition = nr.document(protected(self.host, pending))
            if transition['target'] == name and (transition['recovery_from'] != recovery_from or transition['run_id'] != continuation_of):
                raise nr.Refusal('run reserved by interrupted preparation continuation')
        reserved = []
        for index in range(len(self.config['accounts'])):
            path = self.root / 'state' / ('account-' + str(index))
            if path.exists() and nr.document(protected(self.host, path))['run_id'] == name:
                reserved.append(index)
        if len(reserved) > 1:
            raise nr.Refusal('ambiguous account reservation')
        index = reserved[0] if reserved else next((i for i in range(len(self.config['accounts'])) if not (self.root / 'state' / ('account-' + str(i))).exists()), None)
        if index is None:
            raise nr.Refusal('isolated capacity retained; no account reuse without positive cessation/fencing')
        account = self.config['accounts'][index]
        operational = Path(self.config['storage']) / name
        record = dict(account, run_id=name, storage=str(operational), groups=self.config['groups'], input_sha256=nr.sha(nr.encode(task)))
        record.update(recovery_from=recovery_from, continuation_of=continuation_of)
        reservation = dict(run_id=name, allocation=record)
        reservation_path = self.root / 'state' / ('account-' + str(index))
        # Under the broker lock no dispatch can precede a complete prepared
        # receipt. Only a reservation with NO allocation effects can resume.
        if reserved:
            if any(os.path.lexists(self.root / 'state' / (name + '.' + suffix + '.json')) for suffix in ('prepared', 'consumed', 'continuation')):
                raise nr.Refusal('unexpected admission evidence before allocation; held')
            if nr.document(protected(self.host, reservation_path)) != reservation:
                raise nr.Refusal('partial reservation binding mismatch')
            if os.path.lexists(operational) or os.path.lexists(self.root / 'runs' / name):
                raise nr.Refusal('unexpected effects before allocation; held')
            self.host.processes_stopped(record)
        else:
            if os.path.lexists(operational) or os.path.lexists(self.root / 'runs' / name):
                raise nr.Refusal('allocation destination collision')
            publish(reservation_path, reservation)
        publish(self.root / 'state' / (name + '.allocation.json'), record)
        operational.mkdir(mode=0o700)
        for child in ('home', 'tmp', 'packet'):
            (operational / child).mkdir(mode=0o700)
        selected = copy.deepcopy(template['compose'])
        # Bootstrap's public preparation creates this run's own identity,
        # then composes the selected Work/routes/grants. No raw SQL.
        initial = {'schema': bootstrap.SCHEMA, 'state_root': str(operational / 'instance'), 'checkpoint_profile': 'git', 'integration_profile': selected['instance']['integration_profile'], 'retention_policy_digest': selected['instance']['retention_policy_digest'], 'retention_disposition': 'retain', 'pool_generation': 1, 'policy_generation': 1, 'receipt_participants': selected['participants']['receipts']}
        prepared = bootstrap.prepare(initial, stream=io.StringIO())
        instance = selected['instance']
        instance.update({key: prepared['places'][key] for key in ('authority_store', 'integration_store', 'job_store', 'control_store')}, authority_uuid=prepared['authority_uuid'])
        from baton_v12.authority import Authority
        authority = Authority.open_readonly(instance['authority_store'], expected_authority_uuid=instance['authority_uuid'])
        try:
            selected['participants']['work_id'] = instance['authority_uuid'][:8] + '-W1'
            for role in ('implementation', 'review'):
                selected['participants'][role + '_principal'] = authority.principal_of(selected['participants'][role])
        finally:
            authority.dispose()
        selected['participants']['fixture_files'] = files
        selected['credential_sources'] = record['credentials']
        selected.pop('places', None)
        places = {key: str(operational / key) for key in ('workspaces', 'launch', 'credentials', 'private-contexts', 'deployment-state')}
        limits = task['limits']
        run = self.root / 'runs' / name
        docs = bindings.compose(**selected, run_root=str(run), run_id=name, base=task['base'], context_mode='fresh', task_instructions=task['instructions'], verification=task['verification'], verification_seconds=limits['verification'], runtime_uid=record['uid'], workspace_group=record['gid'], places=places, bounds={'turn_seconds': limits['provider'], 'total_seconds': limits['total'], 'cleanup_seconds': limits['cleanup'], 'implementer_invocations': 1, 'retry': False})
        docs['PACKET.json']['outcome_path'] = str(operational / 'packet/outcome.json')
        bindings.write(str(run), docs)
        os.chmod(run, 0o755)
        workers = [dict(one, participant=one['deployment']['participant']) for one in docs['deployment.json']['workers']]
        full = dict(initial, workers=workers, jobs=[{'job_id': 'job-' + name, 'work_id': selected['participants']['work_id'], 'line_declared_base': task['base'], 'canonical_target_id': task['base'], 'source_worker_id': 'implementation-worker'}])
        bootstrap.prepare(full, stream=io.StringIO())
        publish(run / 'input.json', task, mode=0o644)
        commands = {verb: [str(self.root / 'client.py'), verb, name] for verb in ('check', 'start', 'status')}
        (run / 'commands.json').write_bytes(nr.encode(commands))
        # Configuration is root protected. Only operational output becomes
        # owned by the exclusive execution identity, never code or packets.
        for path in run.iterdir():
            if path.is_file(): os.chmod(path, 0o644)
        own_tree(self.host, operational, record['uid'], record['gid'])
        receipt = {'run_id': name, 'authority_uuid': instance['authority_uuid'], 'work_id': selected['participants']['work_id'], 'uid': record['uid'], 'files': {p.name: nr.sha(nr.read(p)) for p in run.iterdir() if p.is_file()}, 'input_sha256': record['input_sha256'], 'commands': commands}
        receipt.update(recovery_from=recovery_from, continuation_of=continuation_of)
        publish(self.root / 'state' / (name + '.prepared.json'), receipt)
        return receipt

    def check(self, name):
        if not nr.NAME.fullmatch(name):
            raise nr.Refusal('invalid run identity')
        if (self.root / 'state' / (name + '.continuation.json')).exists():
            raise nr.Refusal('partial preparation superseded; retained and never dispatchable')
        record = nr.document(protected(self.host, self.root / 'state' / (name + '.allocation.json')))
        receipt = nr.document(protected(self.host, self.root / 'state' / (name + '.prepared.json')))
        run = self.root / 'runs' / name
        for rel, expected in receipt['files'].items():
            if Path(rel).name != rel or nr.sha(nr.read(protected(self.host, run / rel))) != expected:
                raise nr.Refusal('changed prepared input')
        packet = baseline.held_packet(str(run / 'PACKET.json'))
        # Installed CLI imports exactly these files. Tests may load the same
        # candidate from their source copy and do not claim installed imports.
        if type(self.host) is Host:
            baseline.verify_imported_sources(packet)
            enforcement.verify_controller(packet)
        operational = Path(record['storage'])
        if operational != Path(self.config['storage']) / name:
            raise nr.Refusal('noncanonical operational root')
        protected(self.host, operational.parent, True)
        self.host.owned(operational, record['uid'], private=True)
        self.host.authority_check(record, packet, self.root, receipt['work_id'])
        for parent, dirs, files in os.walk(operational, followlinks=False):
            self.host.owned(Path(parent), record['uid'], private=True)
            for child in dirs + files:
                item = Path(parent) / child
                self.host.owned(item, record['uid'], private=True)
                st = item.lstat()
                if not (stat.S_ISREG(st.st_mode) or stat.S_ISDIR(st.st_mode)) or stat.S_ISREG(st.st_mode) and st.st_nlink != 1:
                    raise nr.Refusal('unsafe operational node')
        return record, packet

    def start(self, name):
        with self.locked():
            record, packet = self.check(name)
            consumed = self.root / 'state' / (name + '.consumed.json')
            if consumed.exists():
                raise nr.Refusal('consumed; no replay')
            # All required output parents were created by allocation. Recreate
            # a missing output parent under custody before consuming selection.
            operational = Path(record['storage'])
            deployment = nr.document(packet['deployment']['config_path'])
            required = [operational / 'home', operational / 'tmp', Path(packet['outcome_path']).parent, Path(deployment['state_root'])]
            for worker in deployment['workers']:
                required += [Path(worker['deployment'][key]) for key in ('workspace_storage', 'launch_home', 'credential_home')]
            for target in required:
                if not target.is_relative_to(operational):
                    raise nr.Refusal('output prerequisite outside private allocation')
                parent = operational
                for part in target.relative_to(operational).parts:
                    parent = parent / part
                    if not parent.exists():
                        parent.mkdir(mode=0o700)
                        self.host.chown(parent, record['uid'], record['gid'])
                    self.host.owned(parent, record['uid'], private=True)
                    if not parent.is_dir(): raise nr.Refusal('output prerequisite is not a directory')
            # Validate original real deployment rules again after preparation.
            nr.stage_execution.held_configuration(deployment, checkout=packet['code_boundary'])
            baseline.verify_worker_image(packet, image_inspect=baseline._engine_inspect)
            publish(consumed, {'run_id': name, 'packet_sha256': nr.sha(nr.read(self.root / 'runs' / name / 'PACKET.json')), 'state': 'dispatch-uncertain'})
            return self.host.dispatch(record, packet, self.root)

    def recover(self, name, task):
        if not nr.NAME.fullmatch(name) or task.get('run_id') == name:
            raise nr.Refusal('recovery requires a fresh run identity')
        nr.task_input(task, self.config['template'])
        with self.locked():
            state = self.root / 'state'
            consumed = nr.document(protected(self.host, state / (name + '.consumed.json')))
            intent_path = state / (name + '.recovery.json')
            target = task['run_id']
            if intent_path.exists():
                intent = nr.document(protected(self.host, intent_path))
                if intent['task'] != task or intent['consumed_sha256'] != nr.sha(nr.encode(consumed)):
                    raise nr.Refusal('recovery already bound to different input; old evidence retained')
            else:
                # Reject collisions BEFORE fencing or allocating anything.
                if (state / (target + '.allocation.json')).exists():
                    raise nr.Refusal('recovery target already allocated')
                record, packet = self.check(name)
                self.host.processes_stopped(record)
                evidence = self.host.recovery_evidence(record, packet, self.root)
                self.host.processes_stopped(record)
                if evidence.get('state') != 'ceased' or evidence.get('run_id') != name or evidence.get('authority_uuid') != packet['deployment']['authority_uuid']:
                    raise nr.Refusal('positive owner cessation required')
                intent = {'run_id': name, 'task': task, 'consumed_sha256': nr.sha(nr.encode(consumed)), 'evidence': evidence}
                publish(intent_path, intent)
            return self._continue_preparation(task, recovery_from=name)

    def _continue_preparation(self, task, recovery_from):
        state = self.root / 'state'
        target = task['run_id']
        # Follow immutable continuation edges. Never retry bootstrap or
        # overwrite a partly published packet. Fresh allocation uses another
        # installed identity and leaves every old byte/store in place.
        predecessor = None
        seen = set()
        while target not in seen:
            seen.add(target)
            selected_task = dict(task, run_id=target)
            transition_path = state / (target + '.continuation.json')
            if transition_path.exists():
                transition = nr.document(protected(self.host, transition_path))
                expected = self._partial_evidence(target, selected_task, recovery_from, predecessor)
                if transition['evidence'] != expected or transition['recovery_from'] != recovery_from or transition['run_id'] != target or not nr.NAME.fullmatch(transition['target']):
                    raise nr.Refusal('partial continuation evidence drift; held')
                predecessor, target = target, transition['target']
                continue
            prepared = state / (target + '.prepared.json')
            if prepared.exists():
                receipt = nr.document(protected(self.host, prepared))
                if receipt.get('recovery_from') != recovery_from or receipt.get('continuation_of') != predecessor or receipt['input_sha256'] != nr.sha(nr.encode(selected_task)):
                    raise nr.Refusal('recovery target attribution mismatch')
                return receipt
            if (state / (target + '.allocation.json')).exists():
                evidence = self._partial_evidence(target, selected_task, recovery_from, predecessor)
                successor = 'continuation-' + uuid.uuid4().hex
                transition = dict(run_id=target, target=successor, recovery_from=recovery_from, evidence=evidence)
                publish(transition_path, transition)
                predecessor, target = target, successor
                continue
            return self._prepare(selected_task, recovery_from=recovery_from, continuation_of=predecessor)
        raise nr.Refusal('cyclic continuation; held')

    def _partial_evidence(self, name, task, recovery_from, continuation_of):
        state = self.root / 'state'
        if os.path.lexists(state / (name + '.consumed.json')) or os.path.lexists(state / (name + '.prepared.json')):
            raise nr.Refusal('partial preparation has execution admission evidence; held')
        path = state / (name + '.allocation.json')
        record = nr.document(protected(self.host, path))
        reservations = []
        for index, account in enumerate(self.config['accounts']):
            reservation_path = state / ('account-' + str(index))
            if reservation_path.exists():
                reservation = nr.document(protected(self.host, reservation_path))
                if reservation['run_id'] == name:
                    expected = dict(account, run_id=name, storage=str(Path(self.config['storage']) / name), groups=self.config['groups'], input_sha256=nr.sha(nr.encode(task)), recovery_from=recovery_from, continuation_of=continuation_of)
                    if record != expected or reservation != dict(run_id=name, allocation=expected):
                        raise nr.Refusal('partial allocation binding drift; held')
                    reservations.append(nr.sha(nr.read(reservation_path)))
        if len(reservations) != 1:
            raise nr.Refusal('partial allocation reservation missing or ambiguous')
        self.host.processes_stopped(record)
        # These are never-dispatched preparation trees, not running stores.
        # Preserve and bind their exact bytes; do not open or repair any DB.
        inventory = {}
        def unreadable(error):
            raise nr.Refusal('partial preparation inventory unreadable; held') from error
        for label, root in [('operational', Path(record['storage'])), ('packet', self.root / 'runs' / name)]:
            protected(self.host, root.parent, True)
            if not os.path.lexists(root):
                inventory[label] = None
                continue
            if not stat.S_ISDIR(root.lstat().st_mode):
                raise nr.Refusal('unsafe partial preparation root; held')
            for parent, dirs, files in os.walk(root, followlinks=False, onerror=unreadable):
                for item in [Path(parent)] + [Path(parent) / child for child in dirs + files]:
                    st = item.lstat()
                    if not (stat.S_ISREG(st.st_mode) or stat.S_ISDIR(st.st_mode)) or stat.S_ISREG(st.st_mode) and st.st_nlink != 1:
                        raise nr.Refusal('unsafe partial preparation node; held')
                    try:
                        self.host.owned(item)
                    except nr.Refusal:
                        if label != 'operational': raise
                        self.host.owned(item, record['uid'], private=True)
                    key = label + '/' + str(item.relative_to(root))
                    inventory[key] = [st.st_dev, st.st_ino, st.st_mode, nr.sha(nr.read(item)) if item.is_file() else None]
        self.host.processes_stopped(record)
        return dict(allocation_sha256=nr.sha(nr.read(path)), reservations=reservations, files=inventory, dispatch='never-admitted')

    def status(self, name):
        if not nr.NAME.fullmatch(name):
            raise nr.Refusal('invalid run identity')
        result = {'run_id': name, 'state': 'unknown', 'work_start': 'unknown'}
        for suffix in ('allocation', 'prepared', 'consumed', 'recovery', 'continuation'):
            path = self.root / 'state' / (name + '.' + suffix + '.json')
            if path.exists():
                result[suffix] = nr.document(protected(self.host, path))
                result['state'] = suffix
        return result


import contextlib
@contextlib.contextmanager
def broker_lock(host, state):
    protected(host, state, True)
    fd = os.open(state / 'broker.lock', os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        previous_umask = os.umask(0o077)
        try:
            yield
        finally:
            os.umask(previous_umask)
    finally:
        os.close(fd)


def read_request(stream):
    raw = stream.read(1024 * 1024 + 1)
    if len(raw) > 1024 * 1024:
        raise nr.Refusal('request exceeds1MiB')
    def unique(pairs):
        value = {}
        for key, member in pairs:
            if key in value: raise nr.Refusal('duplicate request member')
            value[key] = member
        return value
    request = json.loads(raw, object_pairs_hook=unique)
    if type(request) is not dict:
        raise nr.Refusal('request must be an object')
    action = request.get('action')
    if action == 'prepare' and set(request) == {'action', 'task'} and type(request['task']) is dict:
        return request
    if action == 'recover' and set(request) == {'action', 'run', 'task'} and type(request['run']) is str and nr.NAME.fullmatch(request['run']) and type(request['task']) is dict:
        return request
    if action in ('check', 'start', 'status') and set(request) == {'action', 'run'} and type(request['run']) is str and nr.NAME.fullmatch(request['run']):
        return request
    raise nr.Refusal('unsupported action or request operands')


def execute_request(broker, request):
    action = request['action']
    if action == 'prepare':
        return broker.prepare(request['task'])
    if action == 'recover':
        return broker.recover(request['run'], request['task'])
    result = getattr(broker, action)(request['run'])
    if action == 'check':
        return {'state': 'checked', 'run_id': request['run']}
    return result


def main(argv=None):
    args = sys.argv[1:] if argv is None else argv
    if len(args) == 5 and args[0] == 'install' and args[1] == '--inputs' and args[3] == '--sha256':
        raw = nr.read(args[2])
        if nr.sha(raw) != args[4]: raise nr.Refusal('installation input digest mismatch')
        print(json.dumps(install(json.loads(raw)), sort_keys=True))
        return 0
    if args != ['request']:
        raise nr.Refusal('the managed entry accepts only literal request; pass bounded JSON on stdin')
    request = read_request(sys.stdin.buffer)
    broker = Broker()
    result = execute_request(broker, request)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
