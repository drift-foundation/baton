"""Operator entry: fresh fixture repositories, deterministic images, submit/serve."""
from datetime import datetime, timezone
import argparse
import hashlib
import importlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import uuid

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
BASE_IMAGE = 'sha256:0697b6595aff0af2a39a81d492223bf33cf69877426ec859fe1abb90abd617e4'


def command(argv, **kwargs):
    if argv[0] == 'git':
        kwargs['env'] = dict(os.environ, GIT_CONFIG_GLOBAL='/dev/null',
                             GIT_CONFIG_SYSTEM='/dev/null', GIT_CONFIG_NOSYSTEM='1')
    done = subprocess.run(argv, text=True, capture_output=True, timeout=120, **kwargs)
    if done.returncode:
        raise RuntimeError('setup command failed: ' + repr(argv) + '\n' + done.stderr[-4000:])
    return done.stdout.strip()


def write(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def images(root):
    """Build only from a locally present immutable base, without network."""
    command(['docker', 'image', 'inspect', BASE_IMAGE])
    context = root / 'image-context'
    context.mkdir()
    names = ['baton_worker.py', 'claude_agent.py', 'dogfood_entry.py', 'integration_entry.py',
             'integration_workload.py', 'integration_contract.py', 'worker-control-1.0.schema.json']
    for name in names:
        shutil.copyfile(REPO / 'v12/worker' / name, context / name)
    shutil.copytree(REPO / 'v12/python/src/baton_v12/source_profiles', context / 'source_profiles',
                    ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    shutil.copyfile(HERE / 'provider.py', context / 'provider.py')
    shutil.copytree(HERE / 'fixtures', context / 'fixtures')
    # Replaces the executable at the existing provider subprocess boundary.
    # No modification of ClaudeAgent, worker framing or integration workload.
    recipe = ('FROM ' + BASE_IMAGE + '\nUSER root\nCOPY . /opt/baton/\n'
              'RUN rm -f /usr/local/bin/claude && ln -s /opt/baton/provider.py /usr/local/bin/claude '
              '&& chmod 0755 /opt/baton/provider.py\nUSER 65532:65532\n'
              'ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONPATH=/opt/baton PYTHONHASHSEED=0\n')
    selected = {}
    for role, entry in [('provider', 'dogfood_entry.py'), ('integration', 'integration_entry.py')]:
        (context / 'Dockerfile').write_text(recipe + 'ENTRYPOINT ["python3", "/opt/baton/' + entry + '"]\n')
        command(['docker', 'build', '--network=none', '--pull=false', '--iidfile', str(root / (role + '.iid')), str(context)])
        selected[role] = (root / (role + '.iid')).read_text().strip()
        shutil.copyfile(context / 'Dockerfile', root / ('Dockerfile.' + role))
    write(root / 'image-context-manifest.json', {str(p.relative_to(context)): hashlib.sha256(p.read_bytes()).hexdigest()
          for p in sorted(context.rglob('*')) if p.is_file()})
    return selected


def repositories(root):
    """Only the operator invokes this helper; all Git writes are disposable."""
    source = root / 'source'
    shutil.copytree(HERE / 'fixtures/baseline', source)
    command(['git', 'init', '-b', 'main', str(source)])
    command(['git', '-C', str(source), 'add', '.'])
    command(['git', '-C', str(source), '-c', 'user.name=Baton synthetic fixture',
             '-c', 'user.email=synthetic@baton.invalid', '-c', 'core.hooksPath=/dev/null',
             'commit', '-m', 'standalone-ab-v1 synthetic baseline'])
    base, tree = command(['git', '-C', str(source), 'show', '--no-patch', '--format=%H %T', 'HEAD']).split()
    target = root / 'target'
    target.mkdir(mode=0o2775)
    os.chown(target, -1, 1001)
    os.chmod(target, 0o2775)
    command(['git', 'clone', '--no-hardlinks', str(source), str(target)])
    command(['git', 'init', '--bare', str(root / 'integration-workspace')])
    for path in [target, *target.rglob('*')]:
        if path.is_dir():
            os.chmod(path, 0o2775)
        elif path.is_file():
            os.chmod(path, 0o664 if path.is_relative_to(target / '.git') else 0o644)
    # Initial fresh target preparation, as in the accepted operator recipe.
    # Never repairs a submitted attempt and never changes the Baton checkout.
    subprocess.run(['sudo', '--', 'chown', '-R', '--no-dereference', '65532:1001', str(target)], check=True)
    return base, tree


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, help='new absolute disk-backed run root; default under ~/.local/state/baton/v12')
    args = parser.parse_args()
    if 1001 not in os.getgroups():
        raise RuntimeError('operator process must hold supplementary workspace gid1001')
    root = args.root
    if root is None:
        parent = Path.home() / '.local/state/baton/v12'
        parent.mkdir(parents=True, exist_ok=True)
        root = Path(tempfile.mkdtemp(prefix='synthetic-ab-', dir=parent))
    else:
        if not root.is_absolute() or root != root.resolve():
            raise ValueError('run root must be absolute and canonical')
        root.mkdir(mode=0o700, parents=False, exist_ok=False)
    print('SIMULATED provider A/B; retained root: ' + str(root), flush=True)
    began = time.monotonic()
    setup = {'provider': 'synthetic standalone-ab-v1', 'root': str(root), 'live_provider': False}
    try:
        from baton_v12.worker_manager.source_boundary import check_disk_backed
        check_disk_backed(str(root), what='the synthetic scenario root')
        selected = images(root)
        base, tree = repositories(root)
        settings = {'authority_uuid': uuid.uuid4().hex, 'base': base, 'tree': tree,
                    'created_at': datetime.now(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z'),
                    'provider_base': BASE_IMAGE, 'images': selected}
        write(root / 'settings.json', settings)
        credential = root / 'synthetic-credential.json'
        credential.write_text('{"synthetic": "standalone-ab-v1; no real credential"}\n')
        os.chmod(credential, 0o600)
        registry = root / 'credential-sources.json'
        write(registry, {'schema': 'baton.user-credential-sources/1', 'sources': [
            {'provider': 'synthetic-fixture', 'reference': 'standalone-ab-v1', 'path': str(credential)}]})
        os.chmod(registry, 0o600)
        os.environ['BATON_AB_RUN_ROOT'] = str(root)
        sys.path.insert(0, str(HERE))
        deployment = importlib.import_module('deployment')
        deployment.provision()
        setup['setup_seconds'] = time.monotonic() - began
        importlib.import_module('run').main()
        setup['result'] = 'simulated-provider coordination passed'
    except BaseException as failure:
        setup['failure'] = type(failure).__name__ + ': ' + str(failure)
        raise
    finally:
        setup['total_seconds'] = time.monotonic() - began
        write(root / 'scenario-result.json', setup)
        print(json.dumps(setup), flush=True)


if __name__ == '__main__':
    main()
