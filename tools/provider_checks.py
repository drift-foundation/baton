"""Bounded, sequential saved-login and live checks of user-configured accounts."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import re
import selectors
import signal
import subprocess
import sys
import tempfile
import time

LIMIT = 1024 * 1024
PROMPT = 'Reply with pong. Do not use tools, inspect files, or perform any other action.'
# Selection must not accidentally become a check of an ambient API key/backend.
OVERRIDES = (
    'CODEX_HOME', 'CLAUDE_CONFIG_DIR', 'OPENAI_API_KEY', 'CODEX_API_KEY',
    'CODEX_ACCESS_TOKEN', 'OPENAI_BASE_URL', 'ANTHROPIC_API_KEY',
    'ANTHROPIC_AUTH_TOKEN', 'ANTHROPIC_BASE_URL', 'CLAUDE_CODE_OAUTH_TOKEN',
    'CLAUDE_CODE_OAUTH_TOKEN_FILE_DESCRIPTOR', 'CLAUDE_CODE_USE_BEDROCK',
    'CLAUDE_CODE_USE_VERTEX', 'CLAUDE_CODE_USE_FOUNDRY', 'CLAUDECODE',
)


def location(value):
    if not isinstance(value, str) or not value or '\0' in value:
        raise ValueError('home must be an absolute path or ~/path')
    if value.startswith('~/'):
        value = str(Path.home() / value[2:])
    path = Path(value)
    if not path.is_absolute():
        raise ValueError('home must be an absolute path or ~/path')
    return str(path)


def accounts_at(path):
    with path.open('rb') as source:
        raw = source.read(LIMIT + 1)
    if len(raw) > LIMIT:
        raise ValueError('configuration exceeds 1 MiB')
    doc = json.loads(raw)
    if not isinstance(doc, dict) or set(doc) != {'accounts'}:
        raise ValueError('configuration must contain only accounts')
    entries = doc['accounts']
    if not isinstance(entries, list) or not entries:
        raise ValueError('accounts must be a nonempty array')
    labels, result = set(), []
    for entry in entries:
        if not isinstance(entry, dict) or set(entry) - {'provider', 'label', 'home'}:
            raise ValueError('each account needs provider, label and optional home')
        provider, label = entry.get('provider'), entry.get('label')
        if provider not in ('codex', 'claude'):
            raise ValueError('provider must be codex or claude')
        if not isinstance(label, str) or not re.fullmatch(r'[\w .-]{1,64}', label, re.ASCII) or not label.strip() or label in labels:
            raise ValueError('labels must be unique, 1-64 letters/digits/spaces/dots/hyphens/underscores')
        labels.add(label)
        home = location(entry.get('home', str(Path.home() / ('.' + provider))))
        result.append((provider, label, home))
    return result


def child_environment(provider, home):
    env = os.environ.copy()
    for name in OVERRIDES:
        env.pop(name, None)
    env['CODEX_HOME' if provider == 'codex' else 'CLAUDE_CONFIG_DIR'] = home
    env['NO_COLOR'] = '1'
    return env


def commands(provider):
    if provider == 'codex':
        return (['codex', 'login', 'status'],
                ['codex', 'exec', '--json', '--ephemeral', '--ignore-user-config',
                 '--ignore-rules', '--skip-git-repo-check', '--sandbox', 'read-only', PROMPT])
    return (['claude', 'auth', 'status', '--json'],
            ['claude', '--print', '--output-format', 'stream-json', '--verbose', '--no-session-persistence',
             '--tools', '', '--disable-slash-commands', '--setting-sources', '',
             '--settings', '{"disableAllHooks":true}', '--strict-mcp-config',
             '--mcp-config', '{"mcpServers":{}}', '--', PROMPT])


def kill_group(process, sig):
    try:
        os.killpg(process.pid, sig)
    except ProcessLookupError:
        pass


def run(argv, env, cwd, seconds, *, rate_limits=False):
    """Drain bounded output; kill the private process group on every exit path."""
    try:
        process = subprocess.Popen(argv, env=env, cwd=cwd, stdin=subprocess.PIPE if rate_limits else subprocess.DEVNULL,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   start_new_session=True)
    except FileNotFoundError:
        return None, '', '', 'missing-cli'
    except OSError:
        return None, '', '', 'launch-error'
    captured = {'stdout': bytearray(), 'stderr': bytearray()}
    status = None
    deadline = time.monotonic() + seconds
    pending = bytearray()
    response = None
    waiting_id = 1
    def send(message):
        process.stdin.write(json.dumps(message).encode() + b'\n')
        process.stdin.flush()
    try:
        if rate_limits:
            send({'id': 1, 'method': 'initialize', 'params': {
                'clientInfo': {'name': 'baton_provider_checks', 'version': '1'}}})
        with selectors.DefaultSelector() as selector:
            for stream, name in ((process.stdout, 'stdout'), (process.stderr, 'stderr')):
                os.set_blocking(stream.fileno(), False)
                selector.register(stream, selectors.EVENT_READ, name)
            while selector.get_map() or process.poll() is None:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    status = 'timeout'
                    break
                for key, _ in selector.select(min(remaining, 0.1)):
                    data = os.read(key.fileobj.fileno(), 65536)
                    if not data:
                        selector.unregister(key.fileobj)
                    else:
                        captured[key.data].extend(data)
                    if rate_limits and key.data == 'stdout':
                        pending.extend(data)
                if sum(map(len, captured.values())) > LIMIT:
                    status = 'output-limit'
                    break
                if rate_limits:
                    while b'\n' in pending:
                        line, _, pending = pending.partition(b'\n')
                        message = json.loads(line)
                        if not isinstance(message, dict):
                            raise ValueError('invalid RPC message')
                        # Ignore notifications and unrelated replies. A reply must
                        # have our integer id, a result, and no competing error.
                        if type(message.get('id')) is not int or message['id'] != waiting_id:
                            continue
                        if 'error' in message:
                            status = 'provider-error'
                            break
                        if not isinstance(message.get('result'), dict):
                            raise ValueError('invalid RPC result')
                        if waiting_id == 1:
                            send({'method': 'initialized', 'params': {}})
                            send({'id': 2, 'method': 'account/rateLimits/read'})
                            waiting_id = 2
                        else:
                            response = message['result']
                            break
                    if status or response is not None:
                        break
    except (OSError, ValueError):
        status = 'transport-error'
    finally:
        # Includes descendants left behind after a leader exits or closes pipes.
        kill_group(process, signal.SIGTERM)
        try:
            process.wait(timeout=0.5)
        except subprocess.TimeoutExpired:
            pass
        kill_group(process, signal.SIGKILL)
        process.wait()
        process.stdout.close()
        process.stderr.close()
        if process.stdin is not None:
            try:
                process.stdin.close()
            except BrokenPipeError:
                pass
    if rate_limits:
        return (0, json.dumps(response), '', None) if response is not None else (process.returncode, '', '', status or 'missing-response')
    return (process.returncode, captured['stdout'].decode('utf-8', 'replace'),
            captured['stderr'].decode('utf-8', 'replace'), status)


def failure(text, code):
    text = text.lower()
    # Fixed messages only: parser output can contain private paths or values.
    if any(word in text for word in ('invalid mcp configuration', '--mcp-config validation failed', 'error parsing mcp config', 'failed to parse mcp config')):
        return 'invocation-error (MCP config; check probe argv and docs/PROVIDER-CHECKS.md)'
    if any(word in text for word in ('invalid json provided to --settings', 'invalid --setting-sources', 'error processing --settings')):
        return 'invocation-error (settings; check probe argv and docs/PROVIDER-CHECKS.md)'
    if any(word in text for word in ('unknown option', 'unrecognized option', 'unexpected argument', 'requires an argument', 'missing required argument')):
        return 'invocation-error (CLI options; check installed CLI --help and docs/PROVIDER-CHECKS.md)'
    if any(word in text for word in ('usage limit', 'rate limit', 'rate_limit', 'quota', 'insufficient_quota', '429', 'credit balance')):
        return 'usage-limited'
    if any(word in text for word in ('not logged in', 'unauthorized', 'authentication', 'invalid api key', 'invalid_api_key', 'token expired', '401')):
        return 'authentication-error'
    return f'failed (unclassified; exit={code}; check CLI version and docs/PROVIDER-CHECKS.md)'


def classify(provider, phase, result):
    code, out, err, status = result
    if status:
        return status
    if phase == 'login' and provider == 'codex':
        if code == 0 and 'logged in' in (out + err).lower() and 'not logged in' not in (out + err).lower():
            return 'ok'
        return failure(out + err, code) if code else 'inconclusive'
    try:
        if provider == 'claude':
            if phase == 'login':
                doc = json.loads(out)
                if not isinstance(doc, dict):
                    return 'inconclusive'
                if code == 0 and doc.get('loggedIn') is True:
                    return 'ok'
                if doc.get('loggedIn') is False:
                    return 'not-logged-in'
            else:
                _, doc = claude_events(out)
                if doc is None:
                    # R1 (review 2026-09-25T14-07-55Z): stdout carries the
                    # provider's structured diagnostic, so dropping it here made
                    # a recognized failure unclassified. `failure` returns fixed
                    # sanitized text, and success still needs a unique terminal
                    # result below, so including `out` classifies without
                    # disclosing anything or relaxing success.
                    return failure(out + err, code) if code else 'inconclusive'
                if code == 0 and doc.get('subtype') == 'success' and doc.get('is_error') is False and isinstance(doc.get('result'), str) and doc['result'].strip():
                    return 'ok'
            if code != 0 or doc.get('is_error') is True:
                return failure(json.dumps(doc) + err, code)
        else:
            events = [json.loads(line) for line in out.splitlines() if line.strip()]
            if any(not isinstance(event, dict) for event in events):
                return 'inconclusive'
            if code != 0 or any(e.get('type') in ('error', 'turn.failed') for e in events):
                return failure(out + err, code)
            completed = any(e.get('type') == 'turn.completed' for e in events)
            messages = [e.get('item') for e in events if e.get('type') == 'item.completed']
            if completed and any(isinstance(item, dict) and item.get('type') == 'agent_message' and isinstance(item.get('text'), str) and item['text'].strip() for item in messages):
                return 'ok'
    except (ValueError, TypeError):
        pass
    return failure(out + err, code) if code else 'inconclusive'


def claude_events(out):
    events = [json.loads(line) for line in out.splitlines() if line.strip()]
    if any(not isinstance(event, dict) for event in events):
        raise ValueError('invalid stream event')
    results = [event for event in events if event.get('type') == 'result']
    return events, results[0] if len(results) == 1 else None


def claude_allowance(result, observed):
    empty = allowance(None, observed)
    _, out, _, status = result
    if status:
        return empty
    try:
        events, terminal = claude_events(out)
    except (ValueError, TypeError):
        return empty
    if terminal is None:
        return empty
    session = terminal.get('session_id')
    if not isinstance(session, str) or not session:
        return empty
    # All explicitly attributed events must belong to this terminal's session.
    if any('session_id' in e and e['session_id'] != session for e in events):
        return empty
    bucket, conflicts = {}, set()
    for event in events:
        if event.get('type') != 'rate_limit_event':
            continue
        if event.get('session_id') != session:
            return empty
        info = event.get('rate_limit_info')
        if not isinstance(info, dict):
            continue
        kind = info.get('rateLimitType')
        if kind not in ('five_hour', 'seven_day'):
            continue
        position = 'primary' if kind == 'five_hour' else 'secondary'
        used = info.get('utilization')
        valid = type(used) in (int, float) and 0 <= used <= 1
        window = {'usedPercent': used * 100 if valid else None,
                  'windowDurationMins': 300 if kind == 'five_hour' else 10080,
                  'resetsAt': info.get('resetsAt')}
        if position in bucket and bucket[position] != window:
            conflicts.add(position)
        bucket[position] = window
    for position in conflicts:
        bucket.pop(position, None)
    return allowance({'rateLimits': bucket}, observed)


def utc_time(epoch):
    if type(epoch) not in (int, float) or not 0 <= epoch <= 253402300799:
        return None
    try:
        return datetime.fromtimestamp(epoch, timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z')
    except (ValueError, OverflowError, OSError):
        return None


def allowance(result, observed):
    """Return only validated subscription fields, never tokens or credits."""
    windows = {kind: {'remaining': None, 'reset': None, 'minutes': None, 'reason': 'unavailable'}
               for kind in ('session', 'weekly')}
    if not isinstance(result, dict):
        return windows
    if 'rateLimitsByLimitId' in result and result['rateLimitsByLimitId'] is not None:
        buckets = result['rateLimitsByLimitId']
        bucket = buckets.get('codex') if isinstance(buckets, dict) else None
    else:
        bucket = result.get('rateLimits')
    if not isinstance(bucket, dict) or bucket.get('limitId') not in (None, 'codex'):
        return windows
    seen = set()
    for position in ('primary', 'secondary'):
        window = bucket.get(position)
        if not isinstance(window, dict):
            continue
        minutes = window.get('windowDurationMins')
        if type(minutes) is not int:
            continue
        kind = 'weekly' if minutes == 10080 else 'session' if 0 < minutes < 1440 else None
        if kind is None:
            continue
        if kind in seen:
            windows[kind] = {'remaining': None, 'reset': None, 'minutes': None, 'reason': 'ambiguous-windows'}
            continue
        seen.add(kind)
        used = window.get('usedPercent')
        reset = utc_time(window.get('resetsAt'))
        valid = type(used) in (int, float) and 0 <= used <= 100
        stale = reset is not None and window['resetsAt'] <= observed
        windows[kind] = {'remaining': 100 - used if valid and not stale else None,
                         'reset': reset, 'minutes': minutes,
                         'reason': 'stale-reset' if stale else 'reported' if valid else 'invalid-percentage'}
    return windows


def usage_lines(provider, home, cwd, seconds, live_result=None):
    """Optional informational query, separate from login/live pass/fail."""
    result = None
    reason = None
    if provider == 'claude':
        observed = time.time()
        return render_usage(claude_allowance(live_result, observed) if live_result is not None else allowance(None, observed), observed)
    if provider == 'codex':
        if not Path(home).is_dir():
            reason = 'missing-home'
        else:
            _, text, _, status = run(['codex', 'app-server', '--listen', 'stdio://'],
                                    child_environment(provider, home), cwd, seconds, rate_limits=True)
            reason = status
            if status is None:
                result = json.loads(text)
    observed = time.time()
    return render_usage(allowance(result, observed), observed, reason)


def readable_time(value):
    return value.replace('T', ' ').removesuffix('Z') + ' UTC'


def render_usage(windows, observed, reason=None):
    # Unknowns remain in the validated data, but are omitted from human output.
    if reason:
        return []
    lines = []
    for kind, window in windows.items():
        if window['remaining'] is None:
            continue
        value = f"{window['remaining']:g}% remaining"
        if window['reset'] is not None:
            value += '; resets ' + readable_time(window['reset'])
        else:
            value += '; reset not reported'
        lines.append(kind.capitalize() + ': ' + value)
    return lines


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path)
    parser.add_argument('--timeout', type=float, default=45, help='seconds per check (default 45, max 300)')
    args = parser.parse_args(argv)
    if not math.isfinite(args.timeout) or not 0 < args.timeout <= 300:
        parser.error('--timeout must be greater than zero and at most 300')
    selected = args.config or os.environ.get('PROVIDER_CHECKS_CONFIG')
    path = Path(selected).expanduser() if selected else Path(os.environ.get('XDG_CONFIG_HOME') or Path.home() / '.config') / 'baton/provider-checks.json'
    try:
        accounts = accounts_at(path)
    except (OSError, ValueError):
        # Don't echo a configuration's content or provider diagnostics.
        print('Configuration unavailable or invalid. See docs/PROVIDER-CHECKS.md; expected accounts with provider, label, optional home.', file=sys.stderr)
        return 2
    failed = 0
    def interrupted(_signal, _frame):
        raise KeyboardInterrupt
    previous = signal.signal(signal.SIGTERM, interrupted)
    try:
        with tempfile.TemporaryDirectory(prefix='baton-provider-checks-') as cwd:
            for provider, label, home in accounts:
                print(f'[{provider}/{label}]', flush=True)
                verdicts = []
                live_result = None
                for phase, command in zip(('login', 'live'), commands(provider)):
                    if not Path(home).is_dir():
                        verdict = 'missing-home'
                    else:
                        result = run(command, child_environment(provider, home), cwd, args.timeout)
                        verdict = classify(provider, phase, result)
                        if phase == 'live':
                            live_result = result
                    verdicts.append(f'{phase}: {verdict}')
                    failed += verdict != 'ok'
                print('  ' + '; '.join(verdicts), flush=True)
                for line in usage_lines(provider, home, cwd, args.timeout, live_result):
                    print('  ' + line, flush=True)
    except KeyboardInterrupt:
        print('Interrupted; current check process group stopped.', file=sys.stderr)
        return 130
    finally:
        signal.signal(signal.SIGTERM, previous)
    print(f'{len(accounts)} accounts, {len(accounts) * 2} checks, {failed} failed/inconclusive')
    print('Report completed: ' + readable_time(utc_time(time.time())))
    return 1 if failed else 0


if __name__ == '__main__':
    raise SystemExit(main())
