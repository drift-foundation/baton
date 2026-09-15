"""Operator entry: fresh fixture repositories, pinned live-provider images, submit/serve."""
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
    """Reuse the existing immutable live images; never rebuild or run one."""
    selected = json.loads((HERE / 'live-images.json').read_text())
    bindings = json.loads((HERE / 'input-bindings.json').read_text())
    for name, expected in bindings.items():
        if hashlib.sha256((REPO / name).read_bytes()).hexdigest() != expected:
            raise RuntimeError('prepared live input changed: ' + name)
    for name, entry in selected['worker_sources'].items():
        if 'sha256:' + hashlib.sha256((REPO / 'v12' / name).read_bytes()).hexdigest() != entry['sha256']:
            raise RuntimeError('current worker source differs from selected live image: ' + name)
    for role, image in selected['images'].items():
        actual = command(['docker', 'image', 'inspect', image, '--format', '{{.Id}}'])
        if actual != image:
            raise RuntimeError('pinned live image unavailable: ' + role)
    shutil.copyfile(HERE / 'input-bindings.json', root / 'prepared-inputs.json')
    write(root / 'image-context-manifest.json', selected['worker_sources'])
    write(root / 'selected-live-images.json', selected)
    return selected['images']


def repositories(root):
    """Only the operator invokes this helper; all Git writes are disposable."""
    source = root / 'source'
    shutil.copytree(HERE / 'fixtures/baseline', source)
    command(['git', 'init', '-b', 'main', str(source)])
    command(['git', '-C', str(source), 'add', '.'])
    command(['git', '-C', str(source), '-c', 'user.name=Baton A/B fixture',
             '-c', 'user.email=synthetic@baton.invalid', '-c', 'core.hooksPath=/dev/null',
             'commit', '-m', 'live-ab-v1 baseline'])
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
        root = Path(tempfile.mkdtemp(prefix='live-ab-', dir=parent))
    else:
        if not root.is_absolute() or root != root.resolve():
            raise ValueError('run root must be absolute and canonical')
        root.mkdir(mode=0o700, parents=False, exist_ok=False)
    print('LIVE provider A/B; retained root: ' + str(root), flush=True)
    began = time.monotonic()
    setup = {'provider': 'Claude CLI live-ab-v1', 'root': str(root), 'live_provider': True}
    try:
        from baton_v12.worker_manager.source_boundary import check_disk_backed
        check_disk_backed(str(root), what='the live confirmation root')
        selected = images(root)
        base, tree = repositories(root)
        settings = {'authority_uuid': uuid.uuid4().hex, 'base': base, 'tree': tree,
                    'created_at': datetime.now(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z'),
                    'provider_base': BASE_IMAGE, 'images': selected}
        write(root / 'settings.json', settings)
        os.environ['BATON_LIVE_AB_RUN_ROOT'] = str(root)
        sys.path.insert(0, str(HERE))
        deployment = importlib.import_module('deployment')
        deployment.provision()
        setup['setup_seconds'] = time.monotonic() - began
        importlib.import_module('run').main()
        setup['result'] = 'live-provider confirmation passed'
    except BaseException as failure:
        setup['failure'] = type(failure).__name__ + ': ' + str(failure)
        raise
    finally:
        setup['total_seconds'] = time.monotonic() - began
        write(root / 'scenario-result.json', setup)
        print(json.dumps(setup), flush=True)


if __name__ == '__main__':
    main()
