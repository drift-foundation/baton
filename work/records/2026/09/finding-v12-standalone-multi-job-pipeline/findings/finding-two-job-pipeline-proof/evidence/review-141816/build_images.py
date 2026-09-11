"""Build/inspect W71879 candidates from one retained context; never selects them.

No provider run, credentials, source/target mount, package download, or Git
mutation. The two inspection containers are never started and are removed by
this helper that owns them. All build/inspection commands are retained.
"""

import io
import json
from pathlib import Path
import re
import subprocess
import tarfile
import time

from deployment import HERE, PROVIDER_BASE, sha, write_json

CONTEXT = HERE / 'image-context'


def main():
    output = HERE / 'image-build'
    output.mkdir(exist_ok=False)
    manifest = json.loads((HERE / 'image-context-manifest.json').read_text())
    for name, record in manifest.items():
        if sha(CONTEXT / name) != record['sha256']:
            raise RuntimeError('retained build context drift: ' + name)
    report = {'selected': False, 'base': PROVIDER_BASE, 'commands': [], 'images': {}, 'content_checks': {}}
    started = time.monotonic()

    def run(argv, seconds=30, binary=False):
        tick = time.monotonic()
        done = subprocess.run(argv, capture_output=True, timeout=seconds)
        report['commands'].append({'argv': argv, 'returncode': done.returncode,
                                   'wall_seconds': time.monotonic() - tick})
        if done.returncode:
            raise RuntimeError('command failed: ' + repr(argv) + '\n' + done.stderr.decode(errors='replace')[:2000])
        return done.stdout if binary else done.stdout.decode()

    try:
        if run(['docker', 'image', 'inspect', PROVIDER_BASE, '--format', '{{.Id}}']).strip() != PROVIDER_BASE:
            raise RuntimeError('selected historical base is absent')
        for kind in ('provider', 'integration'):
            iidfile = output / (kind + '.iid')
            recipe = CONTEXT / ('Dockerfile.provider' if kind == 'provider' else 'worker/Dockerfile.integration')
            command = ['docker', 'build', '--pull=false', '--no-cache', '--network', 'none',
                       '--platform', 'linux/amd64', '--iidfile', str(iidfile),
                       '--tag', 'baton-w71879-' + kind + ':candidate-141676', '--file', str(recipe)]
            if kind == 'integration':
                command += ['--build-arg', 'PROVIDER_BASE=' + PROVIDER_BASE]
            command += [str(CONTEXT)]
            (output / (kind + '.build.log')).write_text(run(command, seconds=180))
            image = iidfile.read_text().strip()
            if not re.fullmatch(r'sha256:[0-9a-f]{64}', image):
                raise RuntimeError('engine returned no immutable image ID')
            facts = json.loads(run(['docker', 'image', 'inspect', image]))[0]
            expected_entry = ['python3', '/opt/baton/' + ('dogfood_entry.py' if kind == 'provider' else 'integration_entry.py')]
            if facts['Id'] != image or facts['Config']['User'] != '65532:65532' or facts['Config']['Entrypoint'] != expected_entry:
                raise RuntimeError('candidate identity/user/entrypoint mismatch')
            if any(item.startswith(('ANTHROPIC_', 'CLAUDE_CODE_OAUTH_TOKEN=')) for item in facts['Config'].get('Env', [])):
                raise RuntimeError('candidate carries a provider credential environment override')
            write_json(output / (kind + '.inspect.json'), facts)
            container = run(['docker', 'create', '--name', 'w71879-check-' + kind + '-141676',
                             '--network', 'none', '--read-only', '--entrypoint', '/bin/true', image]).strip()
            if not re.fullmatch(r'[0-9a-f]{64}', container):
                raise RuntimeError('inspection container identity is not exact')
            checked = {}
            try:
                for name, record in manifest.items():
                    if name.endswith('Dockerfile.integration'):
                        continue
                    if kind == 'provider' and '/integration_' in name:
                        continue
                    if kind == 'integration' and name.endswith('/dogfood_entry.py'):
                        continue
                    target = '/opt/baton/source_profiles/' + Path(name).name if '/source_profiles/' in name else '/opt/baton/' + Path(name).name
                    data = run(['docker', 'cp', container + ':' + target, '-'], binary=True)
                    with tarfile.open(fileobj=io.BytesIO(data)) as archive:
                        members = [item for item in archive.getmembers() if item.isfile()]
                        if len(members) != 1:
                            raise RuntimeError('image inspection did not return one regular file')
                        payload = archive.extractfile(members[0]).read()
                    from baton_v12.contracts import digest_of_bytes
                    measured = digest_of_bytes(payload)
                    if measured != record['sha256']:
                        raise RuntimeError('image source bytes differ: ' + target)
                    checked[target] = measured
            finally:
                # Only this helper's exact never-started inspection container.
                run(['docker', 'rm', container])
            report['images'][kind] = image
            report['content_checks'][kind] = checked
        write_json(HERE / 'candidate-images.json', report['images'])
    finally:
        report['wall_seconds'] = time.monotonic() - started
        write_json(output / 'result.json', report)
    print(json.dumps({'images': report['images'], 'selected': False, 'wall_seconds': report['wall_seconds']}))


if __name__ == '__main__':
    main()
