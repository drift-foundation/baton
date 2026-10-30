"""Selected no-provider proof. Engine seam is injectable for deterministic checks."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time

HERE = Path(__file__).resolve().parent
HEX = r'[0-9a-f]{64}'


def digest(data):
    return hashlib.sha256(data).hexdigest()


MAX_RESPONSE = 65536


def stream_evidence(value):
    # Arbitrary daemon/child text is never copied into the durable receipt.
    # Length and digest preserve discriminating evidence without secrets or
    # terminal control characters. Classifications below are closed constants.
    if type(value) is not str:
        return {'type': 'non-text'}
    raw = value.encode('utf-8', errors='surrogatepass')
    return {'bytes': len(raw), 'sha256': digest(raw)}


def closed_json(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError('duplicate JSON key')
            result[key] = value
        return result
    return json.loads(raw, object_pairs_hook=pairs)


def inspection(ref, result):
    evidence = {'reference': ref, 'status': result.returncode,
                'stdout': stream_evidence(result.stdout), 'stderr': stream_evidence(result.stderr),
                'classification': 'uncertain', 'reason': 'unsupported-response'}
    def answer(state, reason, obj=None):
        evidence.update(classification=state, reason=reason)
        return obj, evidence
    if type(result.stdout) is not str or type(result.stderr) is not str:
        return answer('uncertain', 'non-text-response')
    if len(result.stdout) > MAX_RESPONSE or len(result.stderr) > MAX_RESPONSE:
        return answer('uncertain', 'response-too-large')
    out, err = result.stdout.strip(), result.stderr.strip()
    if type(result.returncode) is not int:
        return answer('uncertain', 'invalid-status')
    if result.returncode == 1 and out in ('', '[]', '[ ]'):
        prefixes = ('Error: No such object: ', 'Error: No such container: ', 'Error response from daemon: No such container: ')
        for prefix in prefixes:
            # Case folding applies ONLY to known diagnostic words. The ref
            # is literal, case sensitive, and consumes the entire suffix.
            if re.fullmatch('(?i:' + re.escape(prefix) + ')' + re.escape(ref), err):
                return answer('absent', 'exact-no-such-object')
    if result.returncode != 0 or err:
        return answer('uncertain', 'status-or-diagnostic')
    try:
        value = closed_json(out)
    except (ValueError, RecursionError):
        return answer('uncertain', 'invalid-json')
    if type(value) is not list or len(value) != 1 or type(value[0]) is not dict:
        return answer('uncertain', 'not-one-object')
    obj = value[0]
    cid = obj.get('Id')
    if type(cid) is not str or not re.fullmatch(HEX, cid):
        return answer('uncertain', 'invalid-full-id')
    if re.fullmatch(HEX, ref):
        matches = cid == ref
    else:
        matches = obj.get('Name') in (ref, '/' + ref)
    if not matches:
        return answer('uncertain', 'reference-mismatch')
    return answer('present', 'exact-object', obj)


def validate(selection, layout_bytes, payload_bytes, runner_bytes):
    keys = {'schema', 'image', 'uid', 'gid', 'proof_id', 'layout_sha256', 'payload_sha256', 'runner_sha256'}
    if set(selection) != keys or selection['schema'] != 'baton.verifier-engine-proof-selection/1':
        raise ValueError('selection shape')
    if not re.fullmatch('sha256:' + HEX, selection['image']):
        raise ValueError('image digest')
    for name in ('uid', 'gid'):
        if type(selection[name]) is not int or not 0 < selection[name] < 2**31:
            raise ValueError('selected execution identity')
    if not re.fullmatch(r'w325695-proof-[a-z0-9-]{1,40}', selection['proof_id']):
        raise ValueError('proof identity')
    for name, data in [('layout', layout_bytes), ('payload', payload_bytes), ('runner', runner_bytes)]:
        if selection[name + '_sha256'] != digest(data):
            raise ValueError(name + ' selection mismatch')


class Proof:
    def __init__(self, selection, layout, payload, receipt, run=subprocess.run, clock=time.monotonic, sleep=time.sleep):
        self.selection, self.layout, self.payload = selection, layout, payload
        self.receipt, self.run, self.clock, self.sleep = Path(receipt), run, clock, sleep
        self.start = clock()
        self.total_deadline = self.start + 120
        self.work_deadline = self.total_deadline - 40
        self.record = {'selection': selection, 'state': 'reserved', 'container_id': None,
                       'owned': False, 'create_intent': False, 'exact_absence': False,
                       'errors': [], 'calls': [], 'provider_invoked': False}
        # One durable reservation, including interrupted or uncertain executions.
        # Never reuse it; recovery is a separate exact-object operation.
        self.receipt.mkdir(mode=0o700)
        self.save()

    def save(self):
        self.record['elapsed_seconds'] = self.clock() - self.start
        target = self.receipt / 'state.json'
        temporary = self.receipt / 'state.next'
        with temporary.open('w') as f:
            json.dump(self.record, f, indent=2, sort_keys=True)
            f.write('\n'); f.flush(); os.fsync(f.fileno())
        os.replace(temporary, target)
        fd = os.open(self.receipt, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)

    def error(self, phase, failed):
        self.record['errors'].append({'phase': phase, 'type': type(failed).__name__})
        self.save()

    def call(self, phase, args, deadline, cap=10):
        remaining = deadline - self.clock()
        if remaining <= 0:
            self.record['exhausted_phase'] = phase
            self.save()
            raise TimeoutError(phase)
        timeout = min(cap, remaining)
        entry = {'phase': phase, 'args': args, 'timeout_seconds': timeout}
        self.record['calls'].append(entry); self.save()
        try:
            answer = self.run(['docker', *args], capture_output=True, text=True, timeout=timeout)
        except BaseException as failed:
            entry['exception'] = type(failed).__name__
            entry['stdout'] = stream_evidence(getattr(failed, 'stdout', None))
            entry['stderr'] = stream_evidence(getattr(failed, 'stderr', None))
            if isinstance(failed, (subprocess.TimeoutExpired, TimeoutError)):
                self.record['timeout_phase'] = phase
                if self.clock() >= deadline:
                    self.record['exhausted_phase'] = phase
            self.save()
            raise
        entry['status'] = answer.returncode
        entry['stdout'] = stream_evidence(answer.stdout)
        entry['stderr'] = stream_evidence(answer.stderr)
        if self.clock() > deadline:
            self.record['exhausted_phase'] = phase
            self.save()
            raise TimeoutError(phase)
        self.save()
        return answer

    def inspect(self, ref, phase, deadline, cap=10):
        r = self.call(phase, ['inspect', ref], deadline, cap)
        obj, evidence = inspection(ref, r)
        self.record.setdefault('inspections', []).append(dict(phase=phase, **evidence))
        self.save()
        if evidence['classification'] == 'uncertain':
            raise ValueError('indeterminate inspection')
        return obj

    def acquire(self, obj):
        s = self.selection
        if (obj.get('Name') not in (s['proof_id'], '/' + s['proof_id']) or obj['Image'] != s['image'] or obj['Config']['Labels'].get('baton.proof') != s['proof_id']
                or obj['Config']['User'] != f"{s['uid']}:{s['gid']}"
                or (self.record['container_id'] is not None and obj['Id'] != self.record['container_id'])):
            raise ValueError('inspection identity mismatch')
        self.record.update(container_id=obj['Id'], owned=True)
        self.save()

    def vector(self):
        s, v = self.selection, self.layout
        argv = ['create', '--name', s['proof_id'], '--label', 'baton.proof=' + s['proof_id'], '--pull', 'never',
                '--read-only', '--network', 'none', '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges',
                '--user', f"{s['uid']}:{s['gid']}", '--pids-limit', '64', '--memory', '2g', '--cpus', '1',
                '--entrypoint', '/usr/bin/python3']
        roots = [('/tmp', v['tmp_bytes']), ('/dev/shm', v['shm_bytes'])]
        roots += [(one['target'], one['bytes']) for one in v['roots'].values()]
        for target, size in roots:
            mode = '0700' if target.startswith('/run/baton-verifier/') else '1777'
            argv += ['--tmpfs', f"{target}:rw,noexec,nosuid,nodev,size={size},mode={mode},uid={s['uid']},gid={s['gid']}"]
        return argv + [s['image'], '-c', ('PROOF_IMAGE=' + repr(s['image']) + ';PROOF_UID=' + repr(s['uid']) + ';PROOF_GID=' + repr(s['gid']) + '\n' + self.payload)]

    def cleanup(self):
        self.record['state'] = 'cleanup'; self.save()
        if self.record['create_intent'] and not self.record['owned']:
            try:
                obj = self.inspect(self.selection['proof_id'], 'reconcile-create', min(self.clock() + 5, self.total_deadline), 5)
                if obj is not None:
                    self.acquire(obj)
                else:
                    # A lost create reply may still complete after this observation.
                    self.record['creation_uncertainty'] = 'create completion not established; name absent at observation'
                    self.save()
            except BaseException as failed:
                self.error('reconcile-create', failed)
        if self.record['owned']:
            cid = self.record['container_id']
            try:
                r = self.call('remove', ['rm', '--force', cid], min(self.clock() + 25, self.total_deadline - 10), 25)
                self.record['cleanup_status'] = r.returncode
                self.save()
            except BaseException as failed:
                self.error('remove', failed)
            # Independent observation still attempted after removal exceptions.
            try:
                obj = self.inspect(cid, 'confirm-absence', self.total_deadline, 10)
                if obj is None:
                    self.record['exact_absence'] = True
                else:
                    self.acquire(obj)
                    self.record['cleanup_uncertainty'] = 'exact object still present'
                self.save()
            except BaseException as failed:
                self.error('confirm-absence', failed)
        if self.record['create_intent'] and not self.record['exact_absence']:
            self.record['cleanup_uncertainty'] = 'cessation unconfirmed; preserve exact ID or creation name for recovery'
        self.save()

    def execute(self):
        try:
            if self.inspect(self.selection['proof_id'], 'preflight', self.work_deadline) is not None:
                raise ValueError('proof name already occupied')
            self.record.update(state='creating', create_intent=True); self.save()
            r = self.call('create', self.vector(), self.work_deadline)
            if r.returncode != 0 or not re.fullmatch(HEX, r.stdout.strip()):
                raise ValueError('create reply')
            # Save exact returned identity before any additional engine operation.
            self.record['container_id'] = r.stdout.strip(); self.save()
            obj = self.inspect(self.record['container_id'], 'acquire-created', self.work_deadline)
            if obj is None:
                raise ValueError('created object absent')
            self.acquire(obj)
            r = self.call('start', ['start', self.record['container_id']], self.work_deadline)
            if r.returncode != 0:
                raise ValueError('start failed')
            receipt_deadline = min(self.clock() + 20, self.work_deadline)
            while True:
                r = self.call('receipt', ['logs', self.record['container_id']], receipt_deadline)
                if r.returncode != 0:
                    raise ValueError('logs failed')
                if r.stdout.strip():
                    if len(r.stdout) > MAX_RESPONSE or r.stderr.strip():
                        raise ValueError('payload response')
                    payload = closed_json(r.stdout)
                    if type(payload) is not dict:
                        raise ValueError('payload shape')
                    if any(payload.get(k) != 'passed' for k in ('mount_binding', 'ordinary_grandchild', 'nested_validator', 'image_bytes', 'product_mount_checks', 'capacity_enospc')):
                        raise ValueError('payload receipt')
                    keys = ('mount_binding', 'ordinary_grandchild', 'nested_validator', 'image_bytes', 'product_mount_checks', 'capacity_enospc')
                    safe = {key: payload[key] for key in keys}
                    if 'capacity' in payload:
                        capacity = payload['capacity']
                        if type(capacity) is not dict or set(capacity) != set(self.layout['roots']):
                            raise ValueError('capacity receipt shape')
                        safe['capacity'] = {}
                        for name, root in self.layout['roots'].items():
                            row = capacity[name]
                            if (type(row) is not dict or type(row.get('bytes_written')) is not int
                                    or not 0 <= row['bytes_written'] <= root['bytes']
                                    or type(row.get('configured_bytes')) is not int or row['configured_bytes'] != root['bytes']
                                    or row.get('errno') != 'ENOSPC'):
                                raise ValueError('capacity receipt values')
                            safe['capacity'][name] = {key: row[key] for key in ('bytes_written', 'configured_bytes', 'errno')}
                    if 'descendant_started' in payload:
                        pid = payload['descendant_started']
                        if type(pid) is not int or not 0 < pid < 2**31:
                            raise ValueError('descendant receipt')
                        safe['descendant_started'] = pid
                    self.record['payload'] = safe
                    self.save(); break
                left = receipt_deadline - self.clock()
                if left <= 0:
                    raise TimeoutError('receipt')
                self.sleep(min(.5, left))
            obj = self.inspect(self.record['container_id'], 'running', self.work_deadline)
            self.acquire(obj)
            if obj['State']['Running'] is not True:
                raise ValueError('expected live descendant container')
            self.record['proof_observed'] = True; self.save()
        except BaseException as failed:
            self.error('execution', failed)
        finally:
            try:
                self.cleanup()
            except BaseException as failed:
                # Includes unexpected cleanup response shape/program errors; state
                # already has identity/intent even if this final save cannot succeed.
                self.error('cleanup', failed)
            self.record['success'] = bool(self.record.get('proof_observed') and self.record['exact_absence'] and not self.record['errors'] and self.record.get('cleanup_status') == 0)
            self.record['state'] = 'finished' if self.record['success'] else 'failed-or-uncertain'
            self.save()
        return self.record


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--selection', required=True)
    p.add_argument('--selection-sha256', required=True)
    p.add_argument('--execute-reviewed', action='store_true')
    a = p.parse_args()
    raw = Path(a.selection).read_bytes()
    if not a.execute_reviewed or digest(raw) != a.selection_sha256:
        p.error('exact reviewed selection digest and execution selection required')
    selection = json.loads(raw)
    layout = (HERE / 'LAYOUT.json').read_bytes(); payload = (HERE / 'kernel-payload.py').read_bytes()
    validate(selection, layout, payload, Path(__file__).read_bytes())
    proof = Proof(selection, json.loads(layout), payload.decode(), HERE / 'ENGINE-RECEIPT')
    return 0 if proof.execute()['success'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
