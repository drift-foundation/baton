import sys, json
R = sys.argv[1]; sys.path[:0] = [R + '/v12/python/src', R + '/v12/python']
from baton_v12.worker_manager import image_receipts as I
A = 'sha256:' + 'a' * 64; F = 'sha256:' + 'f' * 64
base = {'engine': 'docker', 'runtime_id': 'runtime-1', 'image_id': A, 'started_at': '2026-11-25T00:00:00.123456789Z', 'labels': {}, 'resolution': None}
cases = {'docker_nanosecond_utc': {}, 'podman_offset_stamp': {'engine': 'podman', 'started_at': '2026-11-24T22:00:00.123456789-07:00'},
         'podman_bare_hex_image': {'engine': 'podman', 'image_id': 'a' * 64}, 'never_started': {'started_at': '0001-01-01T00:00:00Z'},
         'naive_stamp': {'started_at': '2026-11-25T00:00:00'}, 'tag_image': {'image_id': 'worker:latest'}, 'other_engine': {'engine': 'nerdctl'},
         'resolution_ok': {'image_id': F, 'resolution': {'image_id': F, 'registry_digest': A}},
         'resolution_other_image': {'image_id': F, 'resolution': {'image_id': A, 'registry_digest': A}},
         'resolution_extra_member': {'image_id': F, 'resolution': {'image_id': F, 'registry_digest': A, 'requested': A}},
         'extra_member': {'worker_claim': A}, 'runtime_id_with_slash': {'runtime_id': 'a/b'}}
out = {k: I.valid({**base, **v}) for k, v in cases.items()}
out['required_none'] = I.required(None)
for p in ('claude', 'codex'):
    out['required_' + p] = I.required({'delivery': {'contract': {'selection': {'provider': p}}}})
print(json.dumps(out, indent=1))
