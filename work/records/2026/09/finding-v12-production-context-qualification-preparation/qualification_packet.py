"""W177936 bounded qualification evidence transport; no live authority.

The verifier consumes bytes, never caller-supplied recall verdicts. Publication
belongs after the restore terminates; second-input capture belongs before it.
"""
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import stat

LIMIT = 64 * 1024 * 1024
ENTRIES = 4096
SCHEMA = 'baton.qualification-capsule/2'
FEEDBACK = 'Recall the 32-character lowercase hexadecimal value selected in your first turn. Return only RECALL: followed by that value. Do not write the value to any file.'


class Refusal(ValueError):
    pass


def require(condition, reason):
    if not condition:
        raise Refusal(reason)


def sha(raw):
    return 'sha256:' + hashlib.sha256(raw).hexdigest()


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()


def closed(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, 'duplicate JSON key')
            result[key] = value
        return result
    try:
        return json.loads(raw, object_pairs_hook=pairs)
    except (ValueError, UnicodeError) as error:
        raise Refusal('invalid qualification JSON') from error


def read(path, limit=LIMIT):
    """No-follow at every component; special files cannot block the open."""
    path = Path(path)
    require(path.is_absolute() and '..' not in path.parts, 'absolute evidence path required')
    fd = os.open('/', os.O_RDONLY | os.O_DIRECTORY)
    try:
        for part in path.parts[1:-1]:
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = child
        leaf = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd)
        try:
            before = os.fstat(leaf)
            require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and before.st_size <= limit, 'evidence type or bound')
            raw = bytearray()
            while len(raw) <= limit:
                chunk = os.read(leaf, min(65536, limit + 1 - len(raw)))
                if not chunk:
                    break
                raw.extend(chunk)
            after = os.fstat(leaf)
            require((before.st_size, before.st_mtime_ns, before.st_ctime_ns) == (after.st_size, after.st_mtime_ns, after.st_ctime_ns), 'evidence changed during read')
            require(len(raw) == before.st_size, 'evidence size changed')
            return bytes(raw)
        finally:
            os.close(leaf)
    finally:
        os.close(fd)


def blob(raw):
    return {'bytes': len(raw), 'digest': sha(raw), 'base64': base64.b64encode(raw).decode('ascii')}


def unblob(value):
    require(type(value) is dict and set(value) == {'bytes', 'digest', 'base64'}, 'blob shape')
    require(type(value['bytes']) is int and 0 <= value['bytes'] <= LIMIT and type(value['base64']) is str, 'blob bound')
    require(len(value['base64']) <= (LIMIT + 2) // 3 * 4, 'encoded blob bound')
    try:
        raw = base64.b64decode(value['base64'], validate=True)
    except ValueError as error:
        raise Refusal('blob encoding') from error
    require(len(raw) == value['bytes'] and sha(raw) == value['digest'], 'blob digest')
    return raw


def _capture_tree(task_bytes, feedback_bytes, workspace):
    """Capture the provider-visible workspace before restore; no omitted files.

    Refuse links and special files instead of calling partial coverage complete.
    The context HOME is deliberately outside this root: it is the sole permitted
    channel for recall. This capture is byte exclusion, not an information-flow
    proof against deliberately encoded content.
    """
    root = Path(workspace)
    require(root.is_absolute() and '..' not in root.parts, 'workspace root')
    fd = os.open('/', os.O_RDONLY | os.O_DIRECTORY)
    rows, directories, total, entries = [], [], len(task_bytes) + len(feedback_bytes), 0
    try:
        for part in root.parts[1:]:
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = child
        def walk(directory, prefix, depth):
            nonlocal total, entries
            require(depth <= 32, 'workspace depth bound')
            before = os.fstat(directory)
            for name in sorted(os.listdir(directory)):
                entries += 1
                require(entries <= ENTRIES, 'workspace inventory bound')
                info = os.stat(name, dir_fd=directory, follow_symlinks=False)
                require(stat.S_ISDIR(info.st_mode) or stat.S_ISREG(info.st_mode), 'workspace entry type')
                flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK
                if stat.S_ISDIR(info.st_mode):
                    flags |= os.O_DIRECTORY
                child = os.open(name, flags, dir_fd=directory)
                try:
                    held = os.fstat(child)
                    require((held.st_dev, held.st_ino, held.st_mode) == (info.st_dev, info.st_ino, info.st_mode), 'workspace entry changed')
                    path = prefix + name
                    total += len(path.encode('utf-8'))
                    require(total <= LIMIT, 'input byte bound')
                    if stat.S_ISDIR(held.st_mode):
                        directories.append(path)
                        walk(child, path + '/', depth + 1)
                    else:
                        require(held.st_nlink == 1 and held.st_size <= LIMIT - total, 'workspace file bound or alias')
                        raw = bytearray()
                        while len(raw) <= held.st_size:
                            chunk = os.read(child, min(65536, held.st_size + 1 - len(raw)))
                            if not chunk:
                                break
                            raw.extend(chunk)
                        after = os.fstat(child)
                        require((held.st_size, held.st_mtime_ns, held.st_ctime_ns) == (after.st_size, after.st_mtime_ns, after.st_ctime_ns) and len(raw) == held.st_size, 'workspace file changed')
                        total += len(raw)
                        rows.append({'path': path, 'content': blob(raw)})
                finally:
                    os.close(child)
            after = os.fstat(directory)
            require((before.st_mtime_ns, before.st_ctime_ns) == (after.st_mtime_ns, after.st_ctime_ns), 'workspace inventory changed')
        walk(fd, '', 0)
    except OSError as error:
        raise Refusal('incomplete workspace inventory') from error
    finally:
        os.close(fd)
    require(total <= LIMIT, 'input byte bound')
    return {'task': blob(task_bytes), 'feedback': blob(feedback_bytes), 'workspace': rows, 'directories': directories}


def capture_inputs(task_bytes, feedback_bytes, workspace, *, inputs, source):
    """Capture all three data mounts, including the source overlaid on /input.

    The caller must stop before provider admission. This helper cannot establish
    that timing; the supervisor and its launch-boundary evidence must do so.
    Credentials and the reconstructed context are never opened here.
    """
    trees = {}
    for label, root in (('workspace', workspace), ('inputs', inputs), ('source', source)):
        captured = _capture_tree(b'', b'', root)
        trees[label] = {'files': captured['workspace'], 'directories': captured['directories']}
    result = {'task': blob(task_bytes), 'feedback': blob(feedback_bytes), 'trees': trees}
    require(len(encoded(result)) <= LIMIT, 'input transport bound')
    return result


def capsule(control, *, run_id, context_id, provider_paths, second_inputs):
    """Collect real retained custody after both turns; no certification act."""
    from baton_v12.worker_manager import provider_context as context, context_delivery as delivery, workspaces
    chain = context._history(control, context_id)
    admits = [one for one in chain if one['action'] == 'admit']
    finals = [one for one in chain if one['action'] == 'finalize']
    require(len(admits) == len(finals) == len(provider_paths) == 2, 'exactly two finalized turns required')
    require([one['payload']['mode'] for one in admits] == ['open', 'restore'], 'open/restore required')
    require(all(one['payload'].get('qualification_run') == run_id for one in admits), 'grant mismatch')
    profile = context.context_profile_of(control, admits[0]['payload']['profile_digest'])
    receipts, providers = [], []
    for admission, final, path in zip(admits, finals, provider_paths):
        attempt = admission['payload']['attempt_id']
        require(Path(path).name == 'provider.stdout.log' and Path(path).parent.name == attempt, 'provider attempt room')
        delivery.validate_generation(control, delivery.configured_context_storage(control), context_id, final['payload'])
        def reader(attempt_id, artifact_id):
            raw = delivery.read_context_receipt(control, attempt_id=attempt_id, artifact_id=artifact_id, workspace_storage=workspaces.configured_workspace_storage(control).place)
            receipts.append(blob(raw))
            return raw
        require(context._receipt(control, admission, reader) == final['payload']['receipt_digest'], 'retained receipt mismatch')
        raw = read(Path(path).absolute(), 16 * 1024 * 1024)
        providers.append({'path': str(path), 'content': blob(raw)})
    value = {'schema': SCHEMA, 'run_id': run_id, 'context_id': context_id, 'profile': profile,
             'attempts': [one['payload']['attempt_id'] for one in admits],
             'conversation_id': admits[0]['payload']['conversation_id'],
             'receipt_digests': [one['payload']['receipt_digest'] for one in finals],
             'generation_digests': [one['payload']['manifest_digest'] for one in finals],
             'receipts': receipts, 'providers': providers, 'second_inputs': second_inputs}
    require(len(encoded(value)) <= LIMIT, 'capsule bound')
    return value


def review(raw, expected_digest):
    """Independent process entry: recompute recall/exclusion from transported bytes."""
    require(len(raw) <= LIMIT and sha(raw) == expected_digest, 'capsule digest or bound')
    value = closed(raw)
    require(type(value) is dict and value.get('schema') == SCHEMA, 'capsule schema')
    require(len(value['providers']) == len(value['receipts']) == len(value['attempts']) == len(value['receipt_digests']) == len(value['generation_digests']) == 2, 'capsule turn count')
    tokens, results, measured_receipts = [], [], []
    for index, (provider, receipt) in enumerate(zip(value['providers'], value['receipts'])):
        body = unblob(provider['content'])
        result = closed(body)
        require(type(result) is dict and result.get('type') == 'result' and result.get('subtype') == 'success' and result.get('is_error') is False, 'provider terminal failure')
        require(result.get('session_id') == value['conversation_id'] and result.get('model') == value['profile']['reported_model'], 'provider identity')
        answer = result.get('result')
        require(type(answer) is str and re.fullmatch(r'RECALL:[0-9a-f]{32}', answer) is not None, 'recall answer shape')
        tokens.append(answer[7:].encode())
        receipt_raw = unblob(receipt)
        require(sha(receipt_raw) == value['receipt_digests'][index], 'receipt byte identity')
        measured = closed(receipt_raw)
        require(measured.get('complete') is True and measured.get('terminal') == 'success', 'strict receipt required')
        require(measured.get('schema') == 'baton.provider-context-receipt/2' and measured.get('attempt_id') == value['attempts'][index] and measured.get('context_id') == value['context_id'], 'receipt identity')
        require(measured.get('mode') == ('open' if index == 0 else 'restore') and measured.get('status') == 0 and measured.get('observed_model') == value['profile']['reported_model'] and measured.get('cli_build') == value['profile']['cli_build'], 'receipt mode/model/build')
        require(measured.get('observed_conversation_id') == value['conversation_id'], 'receipt conversation')
        measured_receipts.append(measured)
        path = Path(provider['path'])
        require(path.is_absolute() and path.name == 'provider.stdout.log' and path.parent.name == value['attempts'][index], 'provider locator')
        results.append({'path': str(path), 'bytes': len(body), 'digest': sha(body)})
    require(tokens[0] == tokens[1], 'recall differs')
    inputs = value['second_inputs']
    require(type(inputs) is dict and set(inputs) == {'task', 'feedback', 'trees'}, 'second input shape')
    require(type(inputs['trees']) is dict and set(inputs['trees']) == {'workspace', 'inputs', 'source'}, 'input mount coverage')
    bodies = [unblob(inputs['task']), unblob(inputs['feedback'])]
    def name(path, seen):
        require(type(path) is str and path and not path.startswith('/') and not any(one in ('', '.', '..') for one in path.split('/')) and path not in seen, 'input path')
        seen.add(path)
        bodies.append(path.encode('utf-8'))
    for tree in inputs['trees'].values():
        require(type(tree) is dict and set(tree) == {'files', 'directories'}, 'input tree shape')
        require(type(tree['files']) is list and type(tree['directories']) is list and len(tree['files']) + len(tree['directories']) <= ENTRIES, 'input inventory bound')
        seen = set()
        for path in tree['directories']:
            name(path, seen)
        for entry in tree['files']:
            require(type(entry) is dict and set(entry) == {'path', 'content'}, 'input entry shape')
            name(entry['path'], seen)
            bodies.append(unblob(entry['content']))
    require(sum(map(len, bodies)) <= LIMIT, 'input byte bound')
    require(all(tokens[0] not in body for body in bodies), 'recall leaked into second input')
    from baton_v12.worker_manager.provider_context import context_prompt
    require(measured_receipts[1]['task_digest'] == sha(bodies[0]), 'captured task differs from serving receipt')
    prompt = context_prompt(closed(bodies[0]), bodies[1].decode('utf-8')).encode()
    require(measured_receipts[1]['prompt_digest'] == sha(prompt), 'captured feedback differs from serving receipt')
    report = {key: value[key] for key in ('run_id', 'context_id', 'attempts', 'receipt_digests', 'generation_digests')}
    report.update(schema='baton.context-qualification-review/1', provider_results=results,
                  recall={'expected_digest': sha(tokens[0]), 'observed_digest': sha(tokens[1]), 'second_inputs_excluded': True})
    return {'schema': 'baton.review-report/1', 'verdict': 'accepted', 'findings': encoded(report).decode()}


def publish(path, value):
    """Exclusive private evidence publication; a consumed identity never resets."""
    raw = encoded(value)
    require(len(raw) <= LIMIT, 'publication bound')
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
    except BaseException:
        # Preserve a partial publication as a consumed failed artifact.
        raise
    return sha(raw)
