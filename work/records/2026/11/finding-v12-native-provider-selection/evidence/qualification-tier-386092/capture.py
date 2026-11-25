"""Proposed container payload. Not executed during preparation.

All provider output is PRIVATE, not publishable. No credential source reads.
No JSONL interpretation or native-success claim; no retries.
"""
import json
import os
from pathlib import Path
import signal
import shutil
import subprocess
import sys
import threading
import time

OUT = Path('/private-output')
HOME = '/run/baton/provider-home'


def bounded(argv, stem, env, seconds, limit):
    streams = []
    p = subprocess.Popen(argv, env=env, cwd='/workspace', stdin=subprocess.DEVNULL,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
    overflow = threading.Event()
    def drain(pipe, path):
        n = 0
        with path.open('xb') as f:
            while True:
                chunk = pipe.read(65536)
                if not chunk:
                    break
                n += len(chunk)
                if n > limit:
                    overflow.set()
                    break
                f.write(chunk)
        pipe.close()
    for pipe, suffix in [(p.stdout, 'stdout'), (p.stderr, 'stderr')]:
        t = threading.Thread(target=drain, args=(pipe, OUT / (stem + '.' + suffix)), daemon=True)
        t.start(); streams.append(t)
    started = time.monotonic(); reason = None
    while p.poll() is None:
        if (OUT / 'files.trace').exists() and (OUT / 'files.trace').stat().st_size > 16 * 1024 * 1024:
            overflow.set()
        if overflow.is_set() or time.monotonic() - started > seconds:
            reason = 'output-bound' if overflow.is_set() else 'deadline'
            os.killpg(p.pid, signal.SIGTERM)
            try:
                p.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(p.pid, signal.SIGKILL); p.wait()
            break
        time.sleep(.05)
    for t in streams:
        t.join(timeout=2)
    if (OUT / 'files.trace').exists() and (OUT / 'files.trace').stat().st_size > 16 * 1024 * 1024:
        overflow.set()
    report = dict(argv=argv, exit_status=p.returncode, elapsed_seconds=time.monotonic()-started,
                  stop_reason=reason, incomplete_drain=any(t.is_alive() for t in streams),
                  semantic_outcome='unclassified', qualification=False)
    (OUT / (stem + '.json')).write_text(json.dumps(report, indent=2) + '\n')
    if reason or overflow.is_set() or report['incomplete_drain']:
        raise SystemExit(124)
    return p.returncode


def metadata():
    answer = []
    for parent, dirs, files in os.walk(HOME, followlinks=False):
        for name in sorted(dirs + files):
            path = Path(parent) / name
            stat = path.lstat()
            answer.append(dict(path=str(path.relative_to(HOME)), mode=oct(stat.st_mode),
                               bytes=stat.st_size, mtime_ns=stat.st_mtime_ns))
            if len(answer) > 2000:
                raise SystemExit('home metadata bound exceeded')
    return answer


def snapshot(name):
    (OUT / (name + '.json')).write_text(json.dumps(dict(
        observed_at_unix=time.time(), entries=metadata()), indent=2) + '\n')


def tool_inventory(env):
    result = {}
    for name in ('codex', 'python3', 'strace', 'git', 'sha256sum'):
        found = shutil.which(name, path=env['PATH'])
        result[name] = dict(present=found is not None, path=found,
                            resolved=str(Path(found).resolve()) if found else None)
    (OUT / 'tools.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


def main():
    os.umask(0o077)
    mode, = sys.argv[1:]
    if mode not in ('login-help', 'login-status', 'live'):
        raise SystemExit('unsupported mode')
    env = dict(PATH='/usr/local/bin:/usr/bin:/bin', HOME=HOME, TMPDIR='/tmp', NO_COLOR='1')
    if mode == 'live':
        cfg = json.loads(Path('/packet/live-context.json').read_text())
        if cfg.get('authorization') is None or cfg.get('qualification_only') is not True:
            raise SystemExit('missing selected qualification envelope')
        if not all(cfg.get(k) for k in ('login_status_help_evidence', 'tool_inventory_evidence', 'image_tool_decision')):
            raise SystemExit('local-status/tool/image prerequisites unresolved')
        env['CODEX_HOME'] = cfg['codex_home']
        argv = cfg['argv']
        if argv[:6] != ['codex', 'exec', '--dangerously-bypass-approvals-and-sandbox', '--ignore-user-config', '--ignore-rules', '--json']:
            raise SystemExit('wrong argv prefix')
        if argv[6] != '--model' or (len(argv), argv[8:-1]) not in ((9, []), (11, ['-c', 'service_tier="fast"'])):
            raise SystemExit('wrong argv shape')
        expected_tier = 'fast' if len(argv) == 11 else None
        if cfg.get('service_tier') != {"requested": expected_tier, "observed": None}:
            raise SystemExit('requested tier and actual argv disagree')
    else:
        env['CODEX_HOME'] = HOME + '/offline-auth-home'
        Path(env['CODEX_HOME']).mkdir(exist_ok=False)
        argv = ['codex', 'login', '--help' if mode == 'login-help' else 'status']
    snapshot('home-before')
    try:
        tools = tool_inventory(env)
        if mode == 'live' and not all(tools[k]['present'] for k in ('git', 'sha256sum')):
            raise SystemExit('required git/sha256sum missing; no exec attempted')
        try:
            version_status = bounded(['codex', '--version'], 'version', env, 10, 4096)
        finally:
            snapshot('home-after-version')
        if version_status != 0 or (OUT / 'version.stdout').read_bytes() != b'codex-cli 0.169.0\n':
            raise SystemExit('wrong exact build or version probe failed')
        if mode == 'live':
            # Local status is a precheck, not proof of server authentication.
            # Output stays private. Any refusal/nonzero/bound stops before exec.
            try:
                status = bounded(['codex', 'login', 'status'], 'local-login-status', env, 20, 1024 * 1024)
            finally:
                snapshot('home-after-login-status')
            if status != 0:
                raise SystemExit('local login status refused; no exec attempted')
            return bounded(argv, 'turn', env, 180, 8 * 1024 * 1024)
        # connect includes Unix/keyring/secret-service endpoints. No send/recv,
        # read/write payloads; empty auth home and network=none in Stage A.
        trace = ['strace', '-f', '-qq', '-e', 'trace=%file,connect', '-o', str(OUT / 'files.trace'), *argv]
        return bounded(trace, mode, env, 20, 1024 * 1024)
    finally:
        snapshot('home-after')


if __name__ == '__main__':
    raise SystemExit(main())
