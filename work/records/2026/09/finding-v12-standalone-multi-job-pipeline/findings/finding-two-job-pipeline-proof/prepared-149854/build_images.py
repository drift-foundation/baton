"""Build two COPY-only candidates and inspect never-started containers.

Operator preparation only. No provider execution, network download, credentials,
Git operation or image selection. Partial outputs and inspection containers remain.
"""
import hashlib
import io
import json
from pathlib import Path
import posixpath
import re
import stat
import subprocess
import tarfile
import time

HERE = Path(__file__).resolve().parent
CONTEXT = HERE / 'image-context'
BASE = 'sha256:0697b6595aff0af2a39a81d492223bf33cf69877426ec859fe1abb90abd617e4'


def sha(data):
    return 'sha256:' + hashlib.sha256(data).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def checked_file(data, expected):
    """Inspect exactly one regular archive member without extracting to disk."""
    with tarfile.open(fileobj=io.BytesIO(data)) as archive:
        members = archive.getmembers()
        if len(members) != 1 or not members[0].isfile():
            raise RuntimeError('image copy is not exactly one regular file')
        item = members[0]
        if item.size != expected['bytes'] or item.mode != expected['mode']:
            raise RuntimeError('image file size or mode differs')
        measured = sha(archive.extractfile(item).read())
        if measured != expected['sha256']:
            raise RuntimeError('image file bytes differ')
        return {'sha256': measured, 'bytes': item.size, 'mode': item.mode}


def checked_launcher(data):
    with tarfile.open(fileobj=io.BytesIO(data)) as archive:
        members = archive.getmembers()
        if len(members) != 1 or not members[0].issym():
            raise RuntimeError('provider launcher is not one symlink')
        target = posixpath.normpath(posixpath.join('/usr/local/bin', members[0].linkname))
        if target != '/usr/local/lib/node_modules/@anthropic-ai/claude-code/bin/claude.exe':
            raise RuntimeError('provider launcher differs from verified package executable')
        return {'target': target, 'linkname': members[0].linkname}


def main():
    output = HERE / 'image-build'
    output.mkdir(exist_ok=False)
    report = {'selected': False, 'complete': False, 'base': BASE, 'commands': [], 'images': {}, 'content_checks': {}, 'inspection_containers': {}}
    started = time.monotonic()

    def run(argv, seconds=30):
        tick = time.monotonic()
        try:
            done = subprocess.run(argv, capture_output=True, timeout=seconds)
        except Exception as error:
            report['commands'].append({'argv': argv, 'wall_seconds': time.monotonic() - tick, 'error_type': type(error).__name__})
            raise
        number = len(report['commands'])
        (output / f'command-{number}.stderr').write_bytes(done.stderr)
        report['commands'].append({'argv': argv, 'returncode': done.returncode, 'wall_seconds': time.monotonic() - tick})
        if done.returncode:
            raise RuntimeError('command failed; see retained command-' + str(number) + '.stderr: ' + repr(argv))
        return done.stdout

    try:
        if (HERE / 'candidate-images.json').exists() or (HERE / 'selected-images.json').exists():
            raise RuntimeError('fresh image preparation refuses existing candidate/selection')
        manifest = json.loads((HERE / 'image-context-manifest.json').read_text())
        installation = json.loads((HERE / 'provider-installation.json').read_text())
        for name, expected in manifest.items():
            path = CONTEXT / name
            if path.is_symlink() or not path.is_file() or sha(path.read_bytes()) != expected['sha256'] or path.stat().st_size != expected['bytes']:
                raise RuntimeError('image context drift: ' + name)
        base = json.loads(run(['docker', 'image', 'inspect', BASE]))[0]
        if base['Id'] != BASE:
            raise RuntimeError('immutable historical base unavailable')
        write_json(output / 'base.inspect.json', base)
        for kind in ('provider', 'integration'):
            recipe = CONTEXT / ('Dockerfile.provider' if kind == 'provider' else 'worker/Dockerfile.integration')
            command = ['docker', 'build', '--pull=false', '--no-cache', '--network', 'none', '--platform', 'linux/amd64',
                       '--iidfile', str(output / (kind + '.iid')), '--tag', 'baton-w71879-' + kind + ':candidate-149053', '--file', str(recipe)]
            if kind == 'integration':
                command += ['--build-arg', 'PROVIDER_BASE=' + BASE]
            command += [str(CONTEXT)]
            (output / (kind + '.build.log')).write_bytes(run(command, seconds=180))
            image = (output / (kind + '.iid')).read_text().strip()
            if not re.fullmatch(r'sha256:[0-9a-f]{64}', image):
                raise RuntimeError('build returned no immutable ID')
            facts = json.loads(run(['docker', 'image', 'inspect', image]))[0]
            entry = ['python3', '/opt/baton/' + ('dogfood_entry.py' if kind == 'provider' else 'integration_entry.py')]
            if facts['Id'] != image or facts['Os'] != 'linux' or facts['Architecture'] != 'amd64' or facts['Config']['User'] != '65532:65532' or facts['Config']['Entrypoint'] != entry:
                raise RuntimeError('candidate image identity/platform/user/entrypoint differs')
            if facts['RootFS']['Layers'][:len(base['RootFS']['Layers'])] != base['RootFS']['Layers']:
                raise RuntimeError('candidate does not inherit exact historical provider layers')
            if any(value.startswith(('ANTHROPIC_', 'CLAUDE_CODE_OAUTH_TOKEN=')) for value in facts['Config'].get('Env', [])):
                raise RuntimeError('candidate contains a credential override')
            write_json(output / (kind + '.inspect.json'), facts)
            container = run(['docker', 'create', '--name', 'w71879-check-' + kind + '-149053', '--network', 'none', '--read-only', '--entrypoint', '/bin/true', image]).decode().strip()
            if not re.fullmatch(r'[0-9a-f]{64}', container):
                raise RuntimeError('inspection container identity invalid')
            report['inspection_containers'][kind] = container
            checked = {}
            for name, expected in manifest.items():
                if name.endswith('Dockerfile.integration') or (kind == 'provider' and '/integration_' in name) or (kind == 'integration' and name.endswith('/dogfood_entry.py')):
                    continue
                target = ('/opt/baton/source_profiles/' if '/source_profiles/' in name else '/opt/baton/') + Path(name).name
                checked[target] = checked_file(run(['docker', 'cp', container + ':' + target, '-']), dict(expected, mode=stat.S_IMODE((CONTEXT / name).stat().st_mode)))
            for target, expected in installation['files'].items():
                checked[target] = checked_file(run(['docker', 'cp', container + ':' + target, '-']), expected)
            checked['/usr/local/bin/claude'] = checked_launcher(run(['docker', 'cp', container + ':/usr/local/bin/claude', '-']))
            state = json.loads(run(['docker', 'inspect', container]))[0]
            if state['Image'] != image or state['State']['Status'] != 'created' or state['State']['Running'] or not state['HostConfig']['ReadonlyRootfs'] or state['HostConfig']['NetworkMode'] != 'none' or state['Mounts']:
                raise RuntimeError('inspection container started or lost isolation')
            write_json(output / (kind + '.container.inspect.json'), state)
            report['images'][kind] = image
            report['content_checks'][kind] = checked
        report['complete'] = True
        write_json(HERE / 'candidate-images.json', report['images'])
    finally:
        report['wall_seconds'] = time.monotonic() - started
        write_json(output / 'result.json', report)
    print(json.dumps({'images': report['images'], 'selected': False, 'wall_seconds': report['wall_seconds']}))


if __name__ == '__main__':
    main()
