"""Bounded client/cleanup helpers derived from accepted Q1; no execution at import."""
import argparse, ast, hashlib, json, os, re, selectors, shutil, signal, subprocess, sys, tarfile, time
from pathlib import Path

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def save(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')

def safe_root(path):
    assert path.is_absolute() and path == Path(os.path.realpath(path))
    for parent in (path, *path.parents):
        assert not (parent / '.git').exists() and (not ((parent / 'HEAD').exists() and (parent / 'objects').is_dir()))

def extract(archive, target):
    target.mkdir(mode=448)
    with tarfile.open(archive) as t:
        for item in t:
            assert item.isfile() and (not item.name.startswith('/')) and ('..' not in Path(item.name).parts)
        t.extractall(target, filter='data')

class Commands:

    def __init__(self, root):
        self.root = root
        self.n = 0
        self.deadline = time.monotonic() + 1200
        self.created = None
        self.launches = 0
        self.builds = 0
        self.expected_labels = {}
        self.env = {'PATH': '/usr/local/bin:/usr/bin:/bin', 'HOME': str(root / 'client-home'), 'DOCKER_CONFIG': str(root / 'docker-config'), 'DOCKER_HOST': 'unix:///var/run/docker.sock', 'DOCKER_BUILDKIT': '0', 'TMPDIR': str(root / 'tmp'), 'LANG': 'C.UTF-8'}

    def __call__(self, argv, seconds=None, cap=2 * 1024 * 1024):
        assert seconds is None or seconds > 0, 'nonpositive command bound'
        seconds = min(30 if seconds is None else seconds, max(0, self.deadline - time.monotonic()))
        assert seconds > 0, 'outer deadline exceeded'
        if argv[0] == 'docker' and argv[1] == 'build':
            assert self.builds == 0, 'second build refused'
            self.builds += 1
        if argv[0] == 'docker' and argv[1] in ('run', 'create'):
            assert self.launches == 0, 'retry or second container refused'
            name = argv[argv.index('--name') + 1]
            absent = self.required(['docker', 'ps', '--all', '--filter', 'name=^/' + name + '$', '--format', '{{.Names}}'], seconds=15)
            assert not absent['stdout'].strip(), 'pre-existing name; no takeover'
            self.created = name
            self.launches += 1
            self.expected_labels = dict((argv[i + 1].split('=', 1) for i, x in enumerate(argv[:-1]) if x == '--label'))
            save(self.root / 'container-intent.json', dict(name=self.created, argv=argv))
        self.n += 1
        stem = self.root / 'commands' / f'{self.n:03d}'
        start = time.monotonic()
        save(str(stem) + '.command.json', dict(argv=argv, bound_seconds=seconds, output_cap_bytes=cap, environment=self.env))
        proc = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=self.env, cwd=self.root, start_new_session=True)
        streams = {}
        buffers = {'stdout': bytearray(), 'stderr': bytearray()}
        failure = None
        selector = selectors.DefaultSelector()
        for key, pipe in [('stdout', proc.stdout), ('stderr', proc.stderr)]:
            os.set_blocking(pipe.fileno(), False)
            selector.register(pipe, selectors.EVENT_READ, key)
            streams[key] = open(str(stem) + '.' + key, 'wb')
        try:
            while selector.get_map():
                if time.monotonic() - start > seconds:
                    raise TimeoutError('command bound exceeded')
                for key, _ in selector.select(0.1):
                    raw = os.read(key.fd, 65536)
                    if not raw:
                        selector.unregister(key.fileobj)
                        continue
                    remaining = cap - sum(map(len, buffers.values()))
                    kept = raw[:remaining]
                    buffers[key.data].extend(kept)
                    streams[key.data].write(kept)
                    if len(raw) > remaining:
                        raise RuntimeError('output bound exceeded')
            proc.wait(timeout=max(0.1, seconds - (time.monotonic() - start)))
        except BaseException as exc:
            failure = type(exc).__name__ + ': ' + str(exc)
            try:
                os.killpg(proc.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid, signal.SIGKILL)
                proc.wait(timeout=5)
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        finally:
            selector.close()
            for stream in streams.values():
                stream.close()
            proc.stdout.close()
            proc.stderr.close()
            save(str(stem) + '.result.json', dict(status=proc.returncode, duration_seconds=time.monotonic() - start, failure=failure, pid=proc.pid, pgid=proc.pid, stdout_bytes=len(buffers['stdout']), stderr_bytes=len(buffers['stderr'])))
        if failure:
            raise RuntimeError(failure)
        return dict(status=proc.returncode, stdout=buffers['stdout'].decode('utf-8', 'replace'), stderr=buffers['stderr'].decode('utf-8', 'replace'))

    def required(self, argv, seconds=30, cap=2 * 1024 * 1024):
        result = self(argv, seconds=seconds, cap=cap)
        assert result['status'] == 0, (argv[:4], result['status'])
        return result

def cleanup(run, root):
    """Only this packet's exact persisted runtime name. No prune or image removal."""
    run.deadline = time.monotonic() + 90
    answer = dict(container_name=run.created, ceased=None, removed=None)
    if run.created is None:
        answer.update(ceased=True, removed=True, reason='no qualification create/run attempted')
        save(root / 'cleanup.json', answer)
        return answer
    try:
        from baton_v12.worker_manager.oci import _absent_prose
        observed = run(['docker', 'inspect', '--type', 'container', run.created])
        if observed['status'] == 0:
            obj = json.loads(observed['stdout'])[0]
            assert run.expected_labels and all((obj['Config']['Labels'].get(k) == v for k, v in run.expected_labels.items())), 'foreign container; do not remove'
            answer['runtime_id'] = obj['Id']
            if obj['State']['Running']:
                run.required(['docker', 'stop', '--time', '5', obj['Id']], seconds=15)
            obj = json.loads(run.required(['docker', 'inspect', '--type', 'container', obj['Id']])['stdout'])[0]
            assert obj['State']['Running'] is False
            answer.update(ceased=True, exit_code=obj['State']['ExitCode'], state=obj['State'])
            run.required(['docker', 'rm', obj['Id']], seconds=15)
        else:
            assert _absent_prose('docker', observed['stderr'], run.created), 'inspect failed without exact positive absence'
        absent = run(['docker', 'inspect', '--type', 'container', run.created], seconds=15)
        listing = run.required(['docker', 'ps', '--all', '--filter', 'name=^/' + run.created + '$', '--format', '{{.Names}}'], seconds=15)
        assert absent['status'] != 0 and _absent_prose('docker', absent['stderr'], run.created) and (not listing['stdout'].strip())
        answer.update(ceased=True, removed=True)
    except BaseException as exc:
        answer['error'] = type(exc).__name__ + ': ' + str(exc)
    save(root / 'cleanup.json', answer)
    return answer
