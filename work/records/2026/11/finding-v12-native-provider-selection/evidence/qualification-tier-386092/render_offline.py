"""Render proposal only; no engine, provider, credential or probe execution."""
import json
import sys
from pathlib import Path

IMAGE = 'sha256:17d250b7f620cf69fce0fd96dc1ccbb5b76151a2a6f6bae4fedb2027076f6b0c'


def render(s):
    if s.get('image') != IMAGE or s.get('mode') != 'help-discovery':
        raise ValueError('unselected image/mode')
    root = Path(s['execution_root'])
    if not root.is_absolute() or any(c in str(root) for c in (',', '\n', '\0')):
        raise ValueError('unsafe run root')
    if any(type(s.get(k)) is not int or s[k] <= 0 for k in ('uid', 'gid')):
        raise ValueError('explicit non-root uid/gid required')
    name = 'n4q-tier-discovery-386092'
    mounts = []
    for source, target, ro in [('packet', '/packet', True), ('home', '/run/baton/provider-home', False), ('workspace', '/workspace', False), ('private-output', '/private-output', False)]:
        mounts += ['--mount', 'type=bind,src=' + str(root / source) + ',dst=' + target + (',readonly' if ro else '')]
    return dict(proposal_only=True, authorization=s.get('authorization'), engine_executed=False,
        create=['docker', 'create', '--name', name, '--label', 'baton.qualification=tier-discovery-386092', '--network', 'none', '--read-only', '--cap-drop=ALL', '--security-opt=no-new-privileges', '--user', f"{s['uid']}:{s['gid']}", '--pids-limit', '128', '--memory', '512m', '--cpus', '1', '--tmpfs', '/tmp:rw,nosuid,nodev,size=128m', '--workdir', '/workspace', *mounts, '--entrypoint', 'python3', IMAGE, '/packet/offline_tier_probe.py', 'help-discovery'],
        preflight=[['docker', 'image', 'inspect', IMAGE]], start=['docker', 'start', name], wait=['docker', 'wait', name],
        inspect_before_removal=['docker', 'inspect', name], outer_deadline_seconds=150,
        on_deadline=[['docker', 'stop', '--time', '15', name], ['docker', 'inspect', name]],
        only_if_still_running=['docker', 'kill', name], after_confirmed_exit=['docker', 'rm', name],
        verify_absence=[['docker', 'inspect', name], ['docker', 'ps', '-aq', '--filter', 'label=baton.qualification=tier-discovery-386092']],
        no_automatic_retry=True, effective_config_evidence='unresolved; help exits never close it')


if __name__ == '__main__':
    print(json.dumps(render(json.loads(Path(sys.argv[1]).read_text())), indent=2))
