"""Deterministic external boundaries for the real installed controller process.

Never invokes Docker, Git, a provider, sudo, or account management. Unexpected
external requests fail, rather than delegating them to the host.
"""
import json
import os
from pathlib import Path
import sys
import shutil
import threading
import subprocess
import hashlib
import time


def main():
    code, tests_root, trace, *args = sys.argv[1:]
    sys.dont_write_bytecode = True
    sys.path[:0] = [str(Path(code) / 'src'), code, tests_root]
    from tools import authoring_enforcement as enforcement, authoring_baseline as baseline, single_worker, stage_execution
    from tests.tools.test_single_worker import Engine
    engine = Engine()
    original = engine.__call__
    def record(kind, value):
        with open(trace, 'a') as out:
            out.write(json.dumps({'kind': kind, 'value': value}) + '\n')
    def external(argv, *, seconds=None):
        record('engine', list(argv))
        if argv[1] == 'stop': engine.running = False
        if argv[1] == 'rm': engine.runtime_id = None
        if argv[1] == 'inspect' and engine.runtime_id is None:
            return engine.answer(status=1, stderr='Error response from daemon: No such container: ' + argv[-1])
        return original(argv, seconds=seconds)
    heads = {}
    blobs = {}
    def git(argv, **kwargs):
        record('simulated-git', list(argv))
        argv = list(argv)
        if 'clone' in argv:
            # W339626: THE PRE-RUNTIME SOURCE-LINE REFUSAL, injected at the
            # boundary and answered by the REAL product profile code. The live
            # run w339626-live-345599 died here with a permission denial on the
            # null device the Git launcher opens, so the denial is reproduced
            # as the backend's own answer rather than by stubbing the refusal.
            if deny_line:
                record('simulated-git-line-denied', argv[-2:])
                return dict(returncode=128, stdout='',
                            stderr="fatal: could not open '/dev/null' for "
                                   'reading and writing: Permission denied')
            source, destination = argv[-2:]
            shutil.copytree(source, destination)
            (Path(destination) / '.git/info').mkdir(parents=True)
            heads[destination] = 'a'*40
            blobs[destination] = (Path(destination) / 'subject.py').read_bytes()
            return dict(returncode=0, stdout='', stderr='')
        repository = argv[argv.index('-C')+1]
        args = argv[argv.index('-C')+2:]
        settings = {}
        while args and args[0] == '-c':
            name, value = args[1].split('=', 1)
            settings[name] = value
            args = args[2:]
        command = args[0]
        current = (Path(repository) / 'subject.py').read_bytes()
        head = heads.get(repository, 'a'*40)
        output = ''
        if command == 'rev-parse':
            expression = args[-1]
            output = ('c'*40 if expression.endswith('^{tree}') else 'a'*40 if expression == 'HEAD^' else head) + '\n'
        elif command == 'status':
            output = '' if current == blobs.get(repository, current) else ' M subject.py\0'
        elif command == 'ls-files':
            output = '' if '--' in args else 'subject.py\0'
        elif command == 'commit':
            heads[repository] = hashlib.sha1(current).hexdigest()
            blobs[repository] = current
            identity = settings['user.name'] + ' <' + settings['user.email'] + '>'
            (Path(repository)/'.git/fixture-commit.json').write_text(json.dumps(dict(head=heads[repository], parent=head, identity=identity)))
        elif command in ('checkout', 'add', 'merge-base', 'update-ref'): pass
        elif command == 'diff':
            output = ('M\0subject.py\0' if '--name-status' in args else 'subject.py\0' if '--name-only' in args else 'simulated patch for subject.py\n') if head != 'a'*40 else ''
        elif command == 'check-attr': output = 'subject.py\0filter\0unspecified\0'
        elif command == 'ls-tree': output = '100644 blob ' + hashlib.sha1(current).hexdigest() + '\tsubject.py\0'
        elif command == 'cat-file':
            output = hashlib.sha1(current).hexdigest().encode() + b' blob ' + str(len(current)).encode() + b'\0' + current + b'\0'
        elif command == 'bundle':
            Path(args[-2]).write_bytes(b'simulated object transport; not a Git bundle')
        else: raise RuntimeError('unmodelled Git boundary: ' + repr(args))
        return dict(returncode=0, stdout=output, stderr='')
    fail_start = '--fixture-fail-start' in args
    if fail_start: args.remove('--fixture-fail-start')
    # W339626: THE FLAG HAS TO REACH THE PROCESS THAT ACTUALLY MATERIALIZES.
    # `main` strips it before calling the controller, and the source line is
    # composed in the WATCHDOG'S CHILD rather than here -- so without the
    # explicit propagation in `Process` below the child parses no flag,
    # `deny_line` is False there, and the clone succeeds. Measured before the
    # correction: the production clone argv appeared in the trace while
    # `simulated-git-line-denied` never did, and the run failed as "froze no
    # result at all" instead of as a pre-runtime source refusal.
    deny_line = '--fixture-deny-line' in args
    if deny_line: args.remove('--fixture-deny-line')
    worker_threads = []
    def run_worker():
        try:
            worker_root = Path(tests_root).parent / 'worker'
            sys.path[:0] = [str(worker_root), str(Path(code) / 'src/baton_v12')]
            import baton_worker, claude_agent
            mounts = {m['Destination']: m['Source'] for m in engine.mounts}
            record('worker-mounts', mounts)
            baton_worker.INPUT_ROOT = claude_agent.INPUT_ROOT = mounts['/input']
            baton_worker.OUTPUT_ROOT = claude_agent.OUTPUT_ROOT = mounts['/output']
            credential = Path(os.environ['HOME']) / 'worker-credential'
            credential.mkdir(exist_ok=True)
            (credential/'claude').write_text('fixture-only')
            claude_agent.CREDENTIAL_ROOT = str(credential)
            def provider(argv, **options):
                if argv[0] == 'git':
                    result = git(argv, **options)
                    out = result['stdout']
                    if options.get('text', False) and isinstance(out, bytes): out = out.decode()
                    if not options.get('text', False) and isinstance(out, str): out = out.encode()
                    return subprocess.CompletedProcess(argv, result['returncode'], out, '' if options.get('text', False) else b'')
                if argv[0] == 'claude':
                    prompt = ' '.join(argv)
                    selected = next((name for name in ('first', 'second', 'recovered') if 'Change subject.py: ' + name in prompt), None)
                    if selected is None: raise RuntimeError('task instruction did not reach provider')
                    record('substantive-work', dict(monotonic=time.monotonic(), cwd=options['cwd'], task=selected))
                    (Path(options['cwd'])/'subject.py').write_text('print(' + repr('implemented ' + selected) + ')\n')
                    return subprocess.CompletedProcess(argv, 0, None, None)
                if argv != ['python3', 'subject.py']: raise RuntimeError('unexpected verification command')
                return subprocess.run(argv, **options)
            home = Path(os.environ['HOME']) / 'worker-home'; home.mkdir(exist_ok=True)
            launch = json.loads(Path(mounts['/run/baton/launch.json']).read_text())
            answer = baton_worker.serve_exchange(claude_agent.ClaudeAgent(run=provider, home=str(home)), launch, launch['session'], mounts['/run/baton/exchange/command'], mounts['/run/baton/exchange/events'])
            record('worker-exit', answer)
        except BaseException as error:
            import traceback
            record('worker-error', traceback.format_exc())
        finally:
            engine.running = False
    prior_external = external
    def external(argv, *, seconds=None):
        result = prior_external(argv, seconds=seconds)
        if argv[1] == 'start':
            thread = threading.Thread(target=run_worker, daemon=True)
            worker_threads.append(thread)
            thread.start()
        return result
    single_worker._engine_run = external
    stage_execution._git_run = git
    def git_read(repository, *args, **kwargs):
        record('simulated-git-read', list(args))
        if args[:2] != ('cat-file', 'commit'): raise RuntimeError('unmodelled Git read')
        commit = json.loads((Path(repository)/'.git/fixture-commit.json').read_text())
        if args[2] != commit['head']: raise RuntimeError('unknown simulated commit')
        return 'tree ' + 'c'*40 + '\nparent ' + commit['parent'] + '\nauthor ' + commit['identity'] + ' 0 +0000\ncommitter ' + commit['identity'] + ' 0 +0000\n\nfixture commit\n'
    baseline._git_read = git_read
    baseline._engine_inspect = lambda reference: {'Id': 'sha256:' + 'a'*64}
    original_process = enforcement.Process
    class Process(original_process):
        def __init__(self, argv, **kwargs):
            if fail_start: raise OSError('simulated controller child launch failure')
            # The fixture flag is RE-COMPOSED for the child, because `main`
            # consumed it out of this process's argv and the child is where the
            # product's own source line runs. It precedes `argv[3:]` so the
            # child still sees the controller's operands in the same order.
            carried = ['--fixture-deny-line'] if deny_line else []
            super().__init__([argv[0], '-I', '-B', __file__, code, tests_root, trace, *carried, *argv[3:]], **kwargs)
    enforcement.Process = Process
    if args[0] == '--fixture-recover':
        from tools import next_run_recovery
        engine.runtime_id = None
        print(json.dumps(next_run_recovery.inspect(args[1])))
        return 0
    return enforcement.main(args)


if __name__ == '__main__':
    raise SystemExit(main())
