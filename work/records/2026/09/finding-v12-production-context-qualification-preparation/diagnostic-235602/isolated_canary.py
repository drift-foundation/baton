"""Owner-selected isolated recall experiment; audit is offline, run is opt-in.

This fixture never opens Baton authority storage or certifies a profile. Its
private evidence is evaluated independently after both workers have stopped.
"""
import argparse
import base64
import hashlib
import json
import multiprocessing
import os
from pathlib import Path
import re
import secrets
import select
import signal
import stat
import subprocess
import sys
import time
import uuid

HERE = Path(__file__).resolve().parent
MANIFEST = HERE / 'CANARY-MANIFEST-235602.json'
RUN = 'w177936-diagnostic-235602'
ROOT = Path('/tmp') / RUN
SLOTS = Path('/dev/shm') / RUN
IMAGE = 'sha256:e84a033c6600fdb65c92f5034e72db1578678d3adeb83df519b3845dee5925e0'
MODEL = 'claude-opus-5'
MODEL_ACCEPTANCE = {'scope': 'recall-only-mixed-model/1', 'usage_models': ['claude-haiku-4-5-20251001', 'claude-opus-5'],
                    'direct_model': 'absent-or-exact-requested', 'model_attribution': 'unestablished'}
CLI = '2.1.247'
DOCKER = ['/usr/bin/docker', '--host', 'unix:///var/run/docker.sock']
DOCKER_ENV = {'PATH': '/usr/bin:/bin', 'HOME': '/nonexistent', 'DOCKER_CONFIG': '/nonexistent'}
CREDENTIAL_SOURCE = Path('/home/sl/.claude/.credentials.json')
SLOT = '/run/baton/credentials/claude'
HOME = '/run/baton/context/home'
SESSION_PREFIX = '.claude/projects/-output/'
BOUNDS = {'turn_seconds': 180, 'active_seconds': 420, 'total_seconds': 600, 'turns': 2, 'retry': False}
LIMIT = 2 * 1024 * 1024
TRANSPORT_LIMIT = 12 * 1024 * 1024
PROCESS_REASONS = {'ok', 'process-exit', 'process-timeout', 'process-output-bound', 'process-spawn', 'process-io'}
STATE_LIMIT = 32 * 1024 * 1024


class Refusal(Exception):
    pass


def require(ok, code):
    if not ok:
        raise Refusal(code)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def decoded(raw, limit=LIMIT):
    require(len(raw) <= limit, 'json-size')
    def pairs(rows):
        result = {}
        for key, value in rows:
            require(key not in result, 'json-duplicate')
            result[key] = value
        return result
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=lambda _: require(False, 'json-number'))


def read(path, limit=LIMIT):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        before = os.fstat(fd)
        require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and before.st_size <= limit, 'file-boundary')
        raw = bytearray()
        while len(raw) <= limit:
            part = os.read(fd, min(65536, limit + 1 - len(raw)))
            if not part:
                break
            raw.extend(part)
        after = os.fstat(fd)
        require(len(raw) == before.st_size and (before.st_ino, before.st_mtime_ns, before.st_ctime_ns) == (after.st_ino, after.st_mtime_ns, after.st_ctime_ns), 'file-drift')
        return bytes(raw)
    finally:
        os.close(fd)


def put(path, raw):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())


def save(path, value):
    put(path, encoded(value))


def contract():
    # In-image mount and host dependency are the SAME pinned file.
    import importlib.util
    path = HERE / 'evidence/qualification_contract.py' if (HERE / 'evidence').is_dir() else HERE / 'qualification_contract.py'
    spec = importlib.util.spec_from_file_location('canary_contract', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def prompt(turn, token=None):
    if turn == 1:
        require(type(token) is str and re.fullmatch('[0-9a-f]{32}', token), 'canary-shape')
        return 'Remember this canary in this conversation only: ' + token + '. Do not use tools or write files. Reply exactly READY.'
    require(turn == 2 and token is None, 'turn-bound')
    return 'Recall the canary from the previous turn of this conversation. Do not use tools or write files. Reply exactly RECALL: followed immediately by that canary, with no other text.'


def argv(session, turn, text):
    require(str(uuid.UUID(session)) == session and turn in (1, 2), 'session-turn')
    return ['claude', '--print', '--dangerously-skip-permissions', '--output-format', 'json', '--model', MODEL,
            '--session-id' if turn == 1 else '--resume', session, text]


class ProcessFailure(Refusal):
    def __init__(self, record):
        super().__init__(record['reason'])
        self.record = record


def output_record(stdout, stderr, code, reason, elapsed, truncated):
    return {'exit_code': code, 'reason': reason, 'elapsed_seconds': elapsed,
            'stdout': base64.b64encode(stdout).decode('ascii'), 'stderr': base64.b64encode(stderr).decode('ascii'),
            'stdout_truncated': truncated[0], 'stderr_truncated': truncated[1]}


def process_streams(record, limit=LIMIT):
    require(type(record) is dict and set(record) == {'exit_code', 'reason', 'elapsed_seconds', 'stdout', 'stderr', 'stdout_truncated', 'stderr_truncated'}, 'process-record')
    require(record['exit_code'] is None or type(record['exit_code']) is int and -255 <= record['exit_code'] <= 255, 'process-status')
    require(type(record['reason']) is str and record['reason'] in PROCESS_REASONS, 'process-reason')
    require(type(record['elapsed_seconds']) in (int, float) and 0 <= record['elapsed_seconds'] <= 600, 'process-duration')
    values = []
    for name in ('stdout', 'stderr'):
        require(type(record[name]) is str and len(record[name]) <= 4 * ((limit + 2) // 3) and type(record[name + '_truncated']) is bool, 'process-stream')
        try:
            raw = base64.b64decode(record[name], validate=True)
        except (ValueError, __import__('binascii').Error):
            raise Refusal('process-encoding') from None
        require(len(raw) <= limit, 'process-stream-bound')
        values.append(raw)
    if record['reason'] == 'ok':
        require(record['exit_code'] == 0 and not record['stdout_truncated'] and not record['stderr_truncated'], 'process-success-shape')
    return values


def invoke(arguments, *, seconds, env, cwd=None, own_group=True, capture=False, output_limit=LIMIT):
    """Drain both streams under one deadline; retain bounded failure evidence."""
    started = time.monotonic()
    buffers = [bytearray(), bytearray()]
    truncated = [False, False]
    reason, code = 'ok', None
    try:
        process = subprocess.Popen(arguments, cwd=cwd, env=env, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, start_new_session=own_group, bufsize=0)
    except OSError:
        record = output_record(b'', b'', None, 'process-spawn', time.monotonic()-started, truncated)
        if capture:
            return record
        raise ProcessFailure(record) from None
    try:
        streams = {process.stdout.fileno(): 0, process.stderr.fileno(): 1}
        for fd in streams:
            os.set_blocking(fd, False)
        while streams or process.poll() is None:
            remaining = started + seconds - time.monotonic()
            if remaining <= 0:
                reason = 'process-timeout'
                break
            ready = select.select(list(streams), [], [], min(remaining, .05))[0]
            for fd in ready:
                data = os.read(fd, 65536)
                if not data:
                    del streams[fd]
                    continue
                index = streams[fd]
                room = output_limit - len(buffers[index])
                buffers[index].extend(data[:room])
                if len(data) > room:
                    truncated[index] = True
                    reason = 'process-output-bound'
            if reason != 'ok':
                break
        if reason == 'ok' and process.returncode != 0:
            reason = 'process-exit'
    except OSError:
        reason = 'process-io'
    finally:
        try:
            os.killpg(process.pid, signal.SIGKILL) if own_group else process.kill()
        except ProcessLookupError:
            pass
        process.wait(timeout=3)
        code = process.returncode
        process.stdout.close()
        process.stderr.close()
    record = output_record(*buffers, code, reason, time.monotonic()-started, truncated)
    if capture:
        return record
    if reason != 'ok':
        raise ProcessFailure(record)
    return bytes(buffers[0])


def worker(request_path=Path('/qualification/request.json'), *, call=invoke, home=HOME, cwd='/output'):
    request = decoded(read(request_path))
    require(set(request) == {'run', 'attempt', 'turn', 'session', 'prompt'}, 'request-shape')
    turn = request['turn']
    require(type(turn) is int and turn in (1, 2) and request['run'] == RUN and request['attempt'] == RUN + '-turn-' + str(turn), 'request-binding')
    if turn == 1:
        token = request['prompt'].split(': ', 1)[1].split('.', 1)[0]
        require(request['prompt'] == prompt(1, token), 'request-prompt')
    else:
        require(request['prompt'] == prompt(2), 'request-prompt')
    env = {'HOME': str(home), 'PATH': '/usr/local/bin:/usr/bin:/bin', 'TMPDIR': '/tmp', 'XDG_CACHE_HOME': '/tmp/cache', 'PYTHONDONTWRITEBYTECODE': '1'}
    records = []
    version = call(['claude', '--version'], seconds=10, env=env, cwd=cwd, capture=True)
    records.append(version)
    version_raw, _ = process_streams(version)
    version_ok = version['reason'] == 'ok' and version_raw.strip() == (CLI + ' (Claude Code)').encode()
    if version_ok:
        records.append(call(argv(request['session'], turn, request['prompt']), seconds=180, env=env, cwd=cwd, capture=True))
        process_streams(records[-1])
    # Even failed provider status travels through Docker stdout in private custody.
    return encoded({'schema': 'baton.canary-worker-output/1', 'run': RUN, 'attempt': request['attempt'],
                    'turn': turn, 'session': request['session'], 'processes': records})


def worker_records(raw, turn, session):
    value = decoded(raw, TRANSPORT_LIMIT)
    require(type(value) is dict and set(value) == {'schema', 'run', 'attempt', 'turn', 'session', 'processes'}, 'worker-output-shape')
    require(value['schema'] == 'baton.canary-worker-output/1' and value['run'] == RUN and type(value['turn']) is int and
            value['turn'] == turn and value['attempt'] == RUN+'-turn-'+str(turn) and value['session'] == session, 'worker-output-binding')
    records = value['processes']
    require(type(records) is list and 1 <= len(records) <= 2, 'worker-process-count')
    streams = [process_streams(record) for record in records]
    return value, streams


def unpack_worker(raw, root, turn, session):
    value, streams = worker_records(raw, turn, session)
    records = value['processes']
    save(root / ('worker-output-' + str(turn) + '.json'), value)
    for index, (stdout, stderr) in enumerate(streams):
        label = 'version' if index == 0 else 'provider'
        put(root / (label + '-' + str(turn) + '.stdout'), stdout)
        put(root / (label + '-' + str(turn) + '.stderr'), stderr)
    require(records[0]['reason'] == 'ok' and streams[0][0].strip() == (CLI + ' (Claude Code)').encode(), 'cli-version')
    require(len(records) == 2, 'provider-not-invoked')
    # Preserve the raw provider response before interpreting status or JSON.
    put(root / ('provider-' + str(turn) + '.json'), streams[1][0])
    require(records[1]['reason'] == 'ok', records[1]['reason'])
    return streams[1][0]


def session_path(session):
    require(str(uuid.UUID(session)) == session, 'session-id')
    return SESSION_PREFIX + session + '.jsonl'


def session_bytes(home, session):
    """Read ONLY the allowlisted file, through no-follow directory descriptors."""
    relative = session_path(session)
    fd = os.open(home, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for name in relative.split('/')[:-1]:
            child = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = child
        leaf = os.open(relative.split('/')[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd)
        try:
            before = os.fstat(leaf)
            require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and 0 < before.st_size <= STATE_LIMIT, 'session-file')
            raw = bytearray()
            while len(raw) <= STATE_LIMIT:
                data = os.read(leaf, min(65536, STATE_LIMIT + 1 - len(raw)))
                if not data:
                    break
                raw.extend(data)
            after = os.fstat(leaf)
            require(len(raw) == before.st_size and before.st_mtime_ns == after.st_mtime_ns and before.st_ctime_ns == after.st_ctime_ns, 'session-drift')
            return bytes(raw)
        finally:
            os.close(leaf)
    finally:
        os.close(fd)


def prepare(root, turn, session, state=None):
    require(turn in (1, 2) and (state is not None) == (turn == 2), 'prepare-turn')
    place = root / ('turn-' + str(turn))
    place.mkdir(mode=0o700)
    home = place / 'home'
    home.mkdir(mode=0o700)
    (home / '.claude').mkdir(mode=0o700)
    (home / '.claude/.credentials.json').symlink_to(SLOT)
    for name in ('input', 'source', 'workspace'):
        (place / name).mkdir(mode=0o500)
    if state is not None:
        target = home / session_path(session)
        target.parent.mkdir(mode=0o700, parents=True)
        put(target, state)
        require(session_bytes(home, session) == state, 'reconstruction')
    return place


def initial_home(home, session, state):
    expected = {'.claude': 'directory', '.claude/.credentials.json': 'credential-slot'}
    if state is not None:
        expected.update({'.claude/projects': 'directory', '.claude/projects/-output': 'directory', session_path(session): sha(state)})
    observed = {}
    def walk(place, prefix=''):
        with os.scandir(place) as entries:
            for entry in entries:
                name = prefix + entry.name
                require(name in expected, 'initial-home-extra')
                info = entry.stat(follow_symlinks=False)
                if stat.S_ISDIR(info.st_mode):
                    observed[name] = 'directory'
                    walk(entry.path, name + '/')
                elif name == '.claude/.credentials.json':
                    require(stat.S_ISLNK(info.st_mode) and os.readlink(entry.path) == SLOT, 'initial-credential')
                    observed[name] = 'credential-slot'
                else:
                    observed[name] = sha(read(entry.path, STATE_LIMIT))
    walk(home)
    require(observed == expected, 'initial-home-set')
    return observed


def vector(place, request, slot, turn, uid, gid):
    mounts = [(place / 'home', HOME, False), (place / 'workspace', '/output', True),
              (place / 'input', '/input', True), (place / 'source', '/source', True),
              (slot, SLOT, True), (request, '/qualification/request.json', True),
              (HERE / 'isolated_canary.py', '/qualification/isolated_canary.py', True),
              (HERE / 'evidence/qualification_contract.py', '/qualification/qualification_contract.py', True)]
    name = RUN + '-turn-' + str(turn)
    args = ['create', '--pull=never', '--name', name, '--label', 'baton.qualification=' + RUN,
            '--label', 'baton.attempt=' + name, '--network', 'bridge', '--user', f'{uid}:{gid}',
            '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges', '--read-only', '--pids-limit', '64',
            '--memory', '2g', '--cpus', '1', '--tmpfs', '/tmp:rw,nosuid,nodev,mode=1777,size=268435456',
            '--workdir', '/output', '--env', 'PYTHONDONTWRITEBYTECODE=1', '--entrypoint', 'python3']
    for source, target, readonly in mounts:
        require(',' not in str(source), 'mount-path')
        args += ['--mount', f'type=bind,src={source},dst={target},bind-propagation=rprivate' + (',readonly' if readonly else '')]
    return args + [IMAGE, '-B', '/qualification/isolated_canary.py', '--worker'], mounts


def validate_runtime(value, identity, mounts, turn, uid, gid):
    require(value['Id'] == identity and value['Image'] == IMAGE and value['Config']['Labels']['baton.qualification'] == RUN and
            value['Config']['Labels']['baton.attempt'] == RUN + '-turn-' + str(turn), 'runtime-binding')
    require(value['Config']['Entrypoint'] == ['python3'] and value['Config']['Cmd'] == ['-B', '/qualification/isolated_canary.py', '--worker'], 'runtime-command')
    host = value['HostConfig']
    require(value['Config']['User'] == f'{uid}:{gid}' and value['Config']['WorkingDir'] == '/output' and
            host['NetworkMode'] == 'bridge' and host['ReadonlyRootfs'] is True and host['Privileged'] is False and
            host['CapDrop'] == ['ALL'] and 'no-new-privileges' in host['SecurityOpt'] and host['PidsLimit'] == 64 and
            host['Memory'] == 2147483648 and host['NanoCpus'] == 1000000000, 'runtime-posture')
    observed = {(m['Source'], m['Destination'], m['RW']) for m in value['Mounts'] if m['Type'] == 'bind'}
    require(observed == {(str(source), target, not readonly) for source, target, readonly in mounts}, 'runtime-mounts')
    require(all(m.get('Propagation') == 'rprivate' for m in value['Mounts'] if m['Type'] == 'bind'), 'mount-propagation')
    require(not any(m['Type'] not in ('bind', 'tmpfs') for m in value['Mounts']), 'extra-mount')
    require(host['Tmpfs'] == {'/tmp': 'rw,nosuid,nodev,mode=1777,size=268435456'}, 'scratch-posture')


def stopped(value):
    state = value['State']
    require(state['Running'] is False and state['Pid'] == 0 and state['Status'] == 'exited' and state['ExitCode'] == 0, 'worker-not-successfully-stopped')


class Engine:
    def __init__(self, deadline, *, own_group=True, evidence=None):
        self.deadline = deadline
        self.own_group = own_group
        self.evidence = evidence
        self.sequence = 0

    def __call__(self, args, seconds=15):
        left = min(seconds, self.deadline - time.monotonic())
        require(left > 0, 'engine-deadline')
        try:
            return invoke(DOCKER + args, seconds=left, env=DOCKER_ENV, own_group=self.own_group,
                          output_limit=TRANSPORT_LIMIT if args[:2] == ['start', '--attach'] else LIMIT)
        except ProcessFailure as error:
            if self.evidence is not None:
                self.sequence += 1
                save(self.evidence / ('engine-failure-' + str(os.getpid()) + '-' + str(self.sequence) + '.json'), error.record)
            raise

    def inspect(self, identity, kind='container'):
        rows = decoded(self([kind, 'inspect', identity]))
        require(type(rows) is list and len(rows) == 1, 'inspect-shape')
        return rows[0]


def terminal(raw, session, expected):
    c = contract()
    value = decoded(raw)
    projection = c.projection(raw, session)
    require(c.valid_terminal(projection, session) and c.success(projection), 'strict-terminal')
    usage = value.get('modelUsage')
    require(type(usage) is dict and set(usage) == set(MODEL_ACCEPTANCE['usage_models']), 'mixed-model-set')
    require('model' not in value or type(value['model']) is str and value['model'] == MODEL, 'direct-model-conflict')
    require(value.get('result') == expected, 'recall-mismatch')
    # Preserve the strict projection (actual_model remains null); this is a
    # separately selected recall experiment, never strict-model qualification.
    return {'strict_terminal': projection, 'experiment': dict(MODEL_ACCEPTANCE)}


def execute(root, slots, manifest_digest, engine):
    """Same controller used with the real Docker boundary and deterministic fake."""
    image = engine.inspect(IMAGE, 'image')
    require(image['Id'] == IMAGE and not image['Config'].get('Volumes'), 'image-drift')
    session, token = str(uuid.uuid4()), secrets.token_hex(16)
    save(root / 'binding.json', {'work': 'W177936', 'run': RUN, 'session': session, 'manifest': manifest_digest,
                               'attempts': [RUN + '-turn-1', RUN + '-turn-2'], 'identity_kind': 'qualification-fixture'})
    records = []
    chronology = []
    state = None
    for turn in (1, 2):
        # State was obtained ONLY after prior stopped/removed proof below.
        chronology.append({'event': 'prepare', 'turn': turn, 'monotonic_ns': time.monotonic_ns()})
        place = prepare(root, turn, session, state)
        save(root / ('initial-home-' + str(turn) + '.json'), initial_home(place / 'home', session, state))
        request = root / ('request-' + str(turn) + '.json')
        save(request, {'run': RUN, 'attempt': RUN + '-turn-' + str(turn), 'turn': turn, 'session': session, 'prompt': prompt(turn, token if turn == 1 else None)})
        if turn == 2:
            require(token.encode() not in read(request), 'canary-in-second-request')
        # Independently sourced credentials, never copied from provider HOME.
        source = CREDENTIAL_SOURCE
        meta = source.lstat()
        require(stat.S_ISREG(meta.st_mode) and meta.st_uid == os.getuid() and not meta.st_mode & 0o077, 'credential-boundary')
        slot = slots / ('slot-' + str(turn))
        put(slot, read(source))
        args, mounts = vector(place, request, slot, turn, os.getuid(), os.getgid())
        save(root / ('intent-' + str(turn) + '.json'), {'attempt': RUN + '-turn-' + str(turn), 'argv_digest': sha(encoded(args)), 'mounts': [(str(p), t, r) for p, t, r in mounts]})
        identity = engine(args).decode().strip()
        require(re.fullmatch('[0-9a-f]{64}', identity), 'container-id')
        before = engine.inspect(identity)
        validate_runtime(before, identity, mounts, turn, os.getuid(), os.getgid())
        require(before['State']['Status'] == 'created' and before['State']['Running'] is False and before['State']['Pid'] == 0, 'worker-already-started')
        save(root / ('runtime-before-' + str(turn) + '.json'), before)
        start_failure = None
        try:
            wire = engine(['start', '--attach', identity], seconds=195)
        except ProcessFailure as error:
            start_failure = error
            save(root / ('start-failure-' + str(turn) + '.json'), error.record)
            wire, _ = process_streams(error.record, TRANSPORT_LIMIT)
        put(root / ('worker-wire-' + str(turn) + '.json'), wire)
        unpack_failure = None
        try:
            raw = unpack_worker(wire, root, turn, session)
        except Exception as error:
            unpack_failure = error
        # Keep whatever stopped/failed runtime facts are obtainable before cleanup.
        try:
            after = engine.inspect(identity)
            save(root / ('runtime-after-' + str(turn) + '.json'), after)
        except Exception:
            save(root / ('runtime-after-unavailable-' + str(turn) + '.json'), {'state': 'unavailable'})
            raise
        if start_failure is not None:
            raise start_failure
        if unpack_failure is not None:
            raise unpack_failure
        validate_runtime(after, identity, mounts, turn, os.getuid(), os.getgid())
        stopped(after)
        for name in ('input', 'source', 'workspace'):
            require(not list((place / name).iterdir()), 'non-session-write')
        engine(['rm', identity])  # Deletes precisely this test-owned stopped worker and its tmpfs.
        require(not engine(['ps', '--all', '--no-trunc', '--filter', 'name=^/' + RUN + '-turn-' + str(turn) + '$', '--format', '{{.ID}}']).strip(), 'worker-removal')
        chronology.append({'event': 'stopped-and-removed', 'turn': turn, 'monotonic_ns': time.monotonic_ns()})
        slot.unlink()
        projection = terminal(raw, session, 'READY' if turn == 1 else 'RECALL:' + token)
        records.append({'attempt': RUN + '-turn-' + str(turn), 'container': identity, 'terminal': projection, 'provider_sha256': sha(raw), 'stopped_and_removed': True})
        if turn == 1:
            state = session_bytes(place / 'home', session)
            put(root / 'selected-session.jsonl', state)
            save(root / 'transfer.json', {'path': session_path(session), 'sha256': sha(state), 'bytes': len(state), 'source_attempt': RUN + '-turn-1', 'target_attempt': RUN + '-turn-2', 'only_session_copied': True})
    save(root / 'chronology.json', chronology)
    result = {'schema': 'baton.isolated-canary/1', 'run': RUN, 'manifest': manifest_digest, 'session': session, 'turns': records,
              'recall': 'exact', 'experiment': dict(MODEL_ACCEPTANCE), 'production_certification': False, 'independent_review': 'pending'}
    save(root / 'observed.json', result)
    return result


def cleanup(engine, slots, evidence=None):
    results = []
    for turn in (1, 2):
        name = RUN + '-turn-' + str(turn)
        try:
            ids = engine(['ps', '--all', '--no-trunc', '--filter', 'name=^/' + name + '$', '--format', '{{.ID}}'], seconds=8).decode().split()
            require(len(ids) <= 1, 'cleanup-ambiguous')
            if ids:
                held = engine.inspect(ids[0])
                if evidence is not None:
                    save(evidence / ('cleanup-before-' + str(turn) + '.json'), held)
                require(held['Image'] == IMAGE and held['Config']['Labels'].get('baton.qualification') == RUN and held['Config']['Labels'].get('baton.attempt') == name, 'cleanup-identity')
                if held['State']['Running']:
                    engine(['stop', '--time', '2', ids[0]], seconds=8)
                    held = engine.inspect(ids[0])
                    if evidence is not None:
                        save(evidence / ('cleanup-stopped-' + str(turn) + '.json'), held)
                require(held['State']['Running'] is False and held['State']['Pid'] == 0, 'cleanup-stopped')
                engine(['rm', ids[0]], seconds=8)
                require(not engine(['ps', '--all', '--no-trunc', '--filter', 'name=^/' + name + '$', '--format', '{{.ID}}'], seconds=8).strip(), 'cleanup-removal')
            slot = slots / ('slot-' + str(turn))
            if slot.exists():
                slot.unlink()
            results.append({'attempt': name, 'confirmed': True})
        except Exception:
            results.append({'attempt': name, 'confirmed': False})
    return results


def audit(approved):
    raw = read(MANIFEST)
    require(sha(raw) == approved, 'manifest-digest')
    manifest = decoded(raw)
    require(manifest['schema'] == 'baton.isolated-canary-manifest/1' and manifest['work'] == 'W177936' and manifest['owner_event'] == 235600 and manifest['qualification'] == 'isolated-recall-only-candidate' and manifest['production_certification'] is False, 'manifest-scope')
    require(manifest['run'] == RUN and manifest['image'] == IMAGE and manifest['bounds'] == BOUNDS and
            manifest['root'] == str(ROOT) and manifest['slots'] == str(SLOTS) and manifest['model'] == MODEL and
            manifest['model_acceptance'] == MODEL_ACCEPTANCE and manifest['cli'] == CLI and
            manifest['diagnostics'] == {'stream_bytes': LIMIT, 'transport_bytes': TRANSPORT_LIMIT, 'worker_schema': 'baton.canary-worker-output/1'}, 'manifest-binding')
    require(set(manifest['files']) == {'isolated_canary.py', 'test_isolated_canary.py', 'evidence/qualification_contract.py', 'CANARY-OPERATOR-235602.md'}, 'manifest-files')
    for name, digest in manifest['files'].items():
        require(sha(read(HERE / name)) == digest, 'package-drift')
    require(set(manifest['supporting_evidence']) == {'IMAGE-VERIFICATION-234131.json', 'MANAGER-ARTIFACT-234277.json', 'MANAGER-INVENTORY-REVIEW-234346.json', 'REVIEW-EVIDENCE-234346.json', 'MODEL-SELECTION-234686.json', 'REVIEW-EVIDENCE-235117.json', 'REVIEW-EVIDENCE-235562.json'}, 'supporting-file-set')
    for name, digest in manifest['supporting_evidence'].items():
        require(sha(read(HERE / name)) == digest, 'supporting-evidence-drift')
    require(manifest['profile']['state_paths'] == [SESSION_PREFIX + '<fresh-session-UUID>.jsonl'] and manifest['profile']['state_bytes'] == STATE_LIMIT and manifest['profile']['cwd'] == '/output', 'manifest-state')
    require(manifest['deployment']['engine'] == DOCKER and manifest['deployment']['entrypoint'] == ['python3', '-B', '/qualification/isolated_canary.py', '--worker'] and manifest['job']['attempts'] == [RUN+'-turn-1', RUN+'-turn-2'] and manifest['job']['automatic_retry'] is False, 'manifest-execution')
    return manifest


def child(root, slots, approved, deadline):
    os.setsid()
    try:
        execute(root, slots, approved, Engine(deadline, own_group=False, evidence=root))
    except BaseException as error:
        save(root / 'failure.json', {'outcome': 'failed', 'code': str(error) if isinstance(error, Refusal) else type(error).__name__})


def _run(approved):
    audit(approved)
    require(os.getuid() != 0, 'nonroot-required')
    # Both roots reserved before reading credentials or touching the engine.
    # Even partial reservation consumes this identity; no automatic retry.
    ROOT.mkdir(mode=0o700)
    SLOTS.mkdir(mode=0o700)
    started = time.monotonic()
    process = multiprocessing.Process(target=child, args=(ROOT, SLOTS, approved, started + BOUNDS['active_seconds']))
    process.start()
    interrupted = False
    try:
        process.join(BOUNDS['active_seconds'])
    except BaseException:
        interrupted = True
    if process.is_alive():
        interrupted = True
        process.terminate()
        process.join(3)
        if process.is_alive():
            process.kill()
            process.join(3)
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    ending = cleanup(Engine(started + BOUNDS['total_seconds'] - 5, evidence=ROOT), SLOTS, evidence=ROOT)
    complete = not interrupted and process.exitcode == 0 and (ROOT / 'observed.json').exists() and all(row['confirmed'] for row in ending)
    save(ROOT / 'completion.json', {'outcome': 'observed-awaiting-review' if complete else 'failed', 'cleanup': ending,
                                   'interrupted': interrupted, 'elapsed_seconds': time.monotonic() - started, 'manifest': approved})
    print(json.dumps({'outcome': 'observed-awaiting-review' if complete else 'failed', 'evidence': str(ROOT)}))
    return 0 if complete else 1


def run(approved):
    # Catch ordinary operator stop so the parent still fences its controller and
    # performs bounded cleanup. SIGKILL/host loss cannot be recovered in-process.
    def interrupted(signum, frame):
        raise InterruptedError('operator-stop')
    previous = signal.signal(signal.SIGTERM, interrupted)
    try:
        return _run(approved)
    finally:
        signal.signal(signal.SIGTERM, previous)


def review(root, approved):
    """Independent offline evaluation; emits no session content or canary."""
    audit(approved)
    completion = decoded(read(root / 'completion.json'))
    require(completion['outcome'] == 'observed-awaiting-review' and completion['manifest'] == approved and
            completion['interrupted'] is False and completion['elapsed_seconds'] < 600 and
            len(completion['cleanup']) == 2 and all(row['confirmed'] is True for row in completion['cleanup']), 'incomplete-run')
    binding = decoded(read(root / 'binding.json'))
    require(binding['work'] == 'W177936' and binding['run'] == RUN and binding['manifest'] == approved and
            binding['attempts'] == [RUN + '-turn-1', RUN + '-turn-2'] and binding['identity_kind'] == 'qualification-fixture', 'evidence-binding')
    chronology = decoded(read(root / 'chronology.json'))
    require([(r['event'], r['turn']) for r in chronology] == [('prepare', 1), ('stopped-and-removed', 1), ('prepare', 2), ('stopped-and-removed', 2)] and all(type(r['monotonic_ns']) is int for r in chronology) and all(a['monotonic_ns'] < b['monotonic_ns'] for a,b in zip(chronology, chronology[1:])), 'shutdown-order')
    session = binding['session']
    first = decoded(read(root / 'request-1.json'))
    second = decoded(read(root / 'request-2.json'))
    token = first['prompt'].split(': ', 1)[1].split('.', 1)[0]
    require(first['prompt'] == prompt(1, token) and second['prompt'] == prompt(2) and token not in second['prompt'], 'prompt-evidence')
    transfer = decoded(read(root / 'transfer.json'))
    state = read(root / 'selected-session.jsonl', STATE_LIMIT)
    require(transfer == {'path': session_path(session), 'sha256': sha(state), 'bytes': len(state), 'source_attempt': RUN + '-turn-1', 'target_attempt': RUN + '-turn-2', 'only_session_copied': True}, 'state-evidence')
    identities = []
    for turn, request in ((1, first), (2, second)):
        require(request['run'] == RUN and request['session'] == session and request['turn'] == turn and request['attempt'] == RUN + '-turn-' + str(turn), 'request-evidence')
        before = decoded(read(root / ('runtime-before-' + str(turn) + '.json')))
        after = decoded(read(root / ('runtime-after-' + str(turn) + '.json')))
        intent = decoded(read(root / ('intent-' + str(turn) + '.json')))
        place = root / ('turn-' + str(turn))
        expected_home = {'.claude': 'directory', '.claude/.credentials.json': 'credential-slot'}
        if turn == 2:
            expected_home.update({'.claude/projects': 'directory', '.claude/projects/-output': 'directory', session_path(session): sha(state)})
        require(decoded(read(root / ('initial-home-' + str(turn) + '.json'))) == expected_home, 'initial-home-evidence')
        args, mounts = vector(place, root / ('request-' + str(turn) + '.json'), SLOTS / ('slot-' + str(turn)), turn, os.getuid(), os.getgid())
        require(intent['argv_digest'] == sha(encoded(args)) and intent['mounts'] == [[str(p), t, r] for p,t,r in mounts], 'intent-evidence')
        validate_runtime(before, before['Id'], mounts, turn, os.getuid(), os.getgid())
        validate_runtime(after, before['Id'], mounts, turn, os.getuid(), os.getgid())
        stopped(after)
        require(before['State']['Status'] == 'created' and before['State']['Running'] is False and before['State']['Pid'] == 0, 'already-started-evidence')
        identities.append(before['Id'])
        wire = read(root / ('worker-wire-' + str(turn) + '.json'), TRANSPORT_LIMIT)
        envelope, streams = worker_records(wire, turn, session)
        require(decoded(read(root / ('worker-output-' + str(turn) + '.json'), TRANSPORT_LIMIT), TRANSPORT_LIMIT) == envelope, 'worker-output-evidence')
        require(len(envelope['processes']) == 2 and all(r['reason'] == 'ok' for r in envelope['processes']), 'worker-process-failed')
        require(streams[0][0].strip() == (CLI + ' (Claude Code)').encode(), 'cli-version')
        raw = read(root / ('provider-' + str(turn) + '.json'))
        require(raw == streams[1][0], 'provider-output-evidence')
        terminal(raw, session, 'READY' if turn == 1 else 'RECALL:' + token)
        for name in ('input', 'source', 'workspace'):
            require(not list((place / name).iterdir()), 'non-session-evidence')
    require(identities[0] != identities[1], 'worker-reused')
    return {'schema': 'baton.isolated-canary-review/1', 'run': RUN, 'manifest': approved, 'session': session,
            'result': 'recall-and-isolation-observed', 'experiment': dict(MODEL_ACCEPTANCE), 'production_certification': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--audit', action='store_true')
    group.add_argument('--run', action='store_true')
    group.add_argument('--review', action='store_true')
    group.add_argument('--worker', action='store_true')
    parser.add_argument('--approved-manifest')
    args = parser.parse_args()
    try:
        if args.worker:
            wire = worker()
            sys.stdout.buffer.write(wire)
            sys.stdout.buffer.flush()
            records = decoded(wire, TRANSPORT_LIMIT)['processes']
            return 0 if len(records) == 2 and all(r['reason'] == 'ok' for r in records) else 1
        require(args.approved_manifest is not None, 'manifest-required')
        if args.audit:
            audit(args.approved_manifest)
            print(json.dumps({'audit': 'pass', 'run': RUN}))
            return 0
        if args.review:
            print(json.dumps(review(ROOT, args.approved_manifest)))
            return 0
        return run(args.approved_manifest)
    except BaseException as error:
        print(json.dumps({'outcome': 'refused', 'code': str(error) if isinstance(error, Refusal) else type(error).__name__}))
        return 1


if __name__ == '__main__':
    sys.exit(main())
