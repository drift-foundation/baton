"""Unexecuted offline discovery payload; only version/help, never an exec turn."""
import json
import os
from pathlib import Path
import sys
from capture import bounded, snapshot, tool_inventory, OUT, HOME

PROBES = [
    ('debug-help', ['codex', 'debug', '--help']),
    ('doctor-help', ['codex', 'doctor', '--help']),
    ('app-server-help', ['codex', 'app-server', '--help']),
    ('fast-help-only', ['codex', 'exec', '--ignore-user-config', '--strict-config', '-c', 'service_tier="fast"', '--help']),
    ('unknown-key-help-control', ['codex', 'exec', '--ignore-user-config', '--strict-config', '-c', 'baton_unknown_service_tier_probe="sentinel"', '--help']),
]


def main():
    if sys.argv[1:] != ['help-discovery']:
        raise SystemExit('only help-discovery is prepared; no effective-config command is selected')
    os.umask(0o077)
    env = dict(PATH='/usr/local/bin:/usr/bin:/bin', HOME=HOME,
               CODEX_HOME=HOME + '/offline-tier-home', TMPDIR='/tmp', NO_COLOR='1')
    Path(env['CODEX_HOME']).mkdir(mode=0o700, exist_ok=False)
    snapshot('home-before')
    inventory = tool_inventory(env)
    if not inventory['strace']['present']:
        raise SystemExit('retained trace tool absent; no substitution')
    try:
        version = bounded(['codex', '--version'], 'version', env, 10, 4096)
    finally:
        snapshot('home-after-version')
    if version != 0 or (OUT / 'version.stdout').read_bytes() != b'codex-cli 0.169.0\n':
        raise SystemExit('wrong exact build')
    results = []
    for stem, argv in PROBES:
        try:
            status = bounded(['strace', '-f', '-qq', '-e', 'trace=%file,connect', '-o', str(OUT / 'files.trace'), *argv], stem, env, 10, 1024 * 1024)
            results.append(dict(probe=stem, exit_status=status, conclusion='unclassified help evidence'))
        finally:
            if (OUT / 'files.trace').exists():
                (OUT / 'files.trace').rename(OUT / (stem + '.trace'))
            snapshot('home-after-' + stem)
    (OUT / 'conclusions.json').write_text(json.dumps(dict(
        probes=results, service_tier_recognition='unproved', effective_config_with_ignore_user_config='unproved',
        actual_served_tier='unproved', provider_turn_attempted=False,
        reason='Help may short-circuit configuration loading; even strict-config exit0 is not effective-config evidence.'), indent=2) + '\n')


if __name__ == '__main__':
    main()
