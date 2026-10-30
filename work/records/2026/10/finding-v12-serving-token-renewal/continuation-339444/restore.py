"""Restore the exact preserved W333485 UNACCEPTED partial input into the private
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
EXPECTED = {'v12/python/src/baton_v12/job_manager/manager.py': {'base_sha256': '4c5bc31f895c0ff0d6dfe8fd4e6f54421e2b3b6cb65a0aa4abf0f9f85a248ceb', 'restored_sha256': 'a3160a5e0939054b772486d2bfb1bc949e2c5ca4644a643a3f117818d05982f2', 'bytes': 62403}, 'v12/python/src/baton_v12/job_manager/renewal.py': {'base_sha256': None, 'restored_sha256': '8ec602a1c89068f459a60d6ef86e1d3f19badffb2ac9d1031a14f485fe16a1d9', 'bytes': 48499}, 'v12/python/tools/job_manager.py': {'base_sha256': '6a374552f879615c4a8621a369525229963fe459685901688defda61e3669704', 'restored_sha256': '73c1d041cf08e545225da0adc740e7c771f4ca2193ad10ad8a507e650fdbbd09', 'bytes': 67438}}


def sha(body):
    return hashlib.sha256(body).hexdigest()


def restore(destination):
    destination = pathlib.Path(destination).resolve(strict=True)
    source = pathlib.Path("/home/sl/src/baton")
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
