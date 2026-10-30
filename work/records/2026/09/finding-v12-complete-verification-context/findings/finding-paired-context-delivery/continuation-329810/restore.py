"""Restore the exact preserved W321776 Stage-A checkpoint into the private
checkout. Copies verified buffers; performs no version-control operation and
writes nothing outside the destination.

EVERY BUFFER AND EVERY BASE FILE IS VALIDATED BEFORE THE FIRST WRITE, so a
mismatch anywhere leaves the checkout exactly as it was. `base_sha256` is the
bytes the declared base holds, or `None` for a file the base does not carry at
all -- a file that exists where the base has none is a different tree, and that
is a refusal rather than an overwrite.
"""
import hashlib
import json
import os
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
EXPECTED = {
    'v12/python/src/baton_v12/verification_context.py': {
        'base_sha256': None,
        'restored_sha256': 'f599072ac1202e9b759d9e7850f76c98790e23710cf6181d5a6e8907dd51650e',
        'bytes': 26520},
    'v12/python/tests/manager/test_verification_context.py': {
        'base_sha256': None,
        'restored_sha256': '42dcbfc99ef97c5191461d901bc32630ac58641c77c73341cae9bea1b0f264ff',
        'bytes': 35250},
    'v12/worker/Dockerfile.claude': {
        'base_sha256': '9f7e439babafabb5303aac0c17a2ac5179390c5a63fb74824b6c851ea4ab12ef',
        'restored_sha256': '487748a01c72906d3725b78ecafe060a4d290c070822ecb20c8373fe82589b49',
        'bytes': 14206},
    'v12/.dockerignore': {
        'base_sha256': '7aae9bcf1a62bf98ef26c6c7ac284430d4d253da456283cda018db39f9fa96c6',
        'restored_sha256': 'b7da7ead0d55e0df74be3b2df79d309fd3aa5455967e3a6bc1d705293cb57ca8',
        'bytes': 2931},
    'v12/python/tests/manager/test_claude_agent.py': {
        'base_sha256': '42191d077e411f9e0a08b82b69c7e2b06e8583a6a0acd6c8da6a4fa8b703492d',
        'restored_sha256': '215e9db278b9d87c971be970528646d2fd5fad5b74ef927a49036916ba37288e',
        'bytes': 211808},
}


def sha(body):
    return hashlib.sha256(body).hexdigest()


def restore(destination):
    destination = pathlib.Path(destination).resolve(strict=True)
    source = HERE.parents[7]
    # Neither the mounted source nor the canonical host checkout may ever be a
    # destination: this script restores INTO a private checkout and nowhere else.
    for forbidden in [pathlib.Path('/input/source'),
                      pathlib.Path('/home/sl/src/baton'), source]:
        if destination == forbidden or forbidden in destination.parents:
            raise ValueError('destination is protected source')
    buffers = {}
    for relative, declared in EXPECTED.items():
        content = (HERE / 'candidate-input' / relative).read_bytes()
        if sha(content) != declared['restored_sha256'] \
                or len(content) != declared['bytes']:
            raise ValueError('preserved input digest mismatch: ' + relative)
        buffers[relative] = content
        target = destination / relative
        if any(parent.is_symlink()
               for parent in [target, *target.parents] if parent != destination):
            raise ValueError('symlink target: ' + relative)
        held = sha(target.read_bytes()) if target.exists() else None
        if held != declared['base_sha256']:
            raise ValueError('base mismatch: ' + relative)
    # All buffers and all base files validated; now and only now, write.
    for relative, content in buffers.items():
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
    result = {one: sha((destination / one).read_bytes()) for one in EXPECTED}
    if any(result[one] != EXPECTED[one]['restored_sha256'] for one in result):
        raise ValueError('restoration result mismatch')
    print(json.dumps({'state': 'restored-exact-preserved-checkpoint',
                      'paths': result}, sort_keys=True))


if __name__ == '__main__':
    restore(sys.argv[1] if len(sys.argv) == 2 else os.getcwd())
