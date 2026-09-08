"""Prepare and apply the exact operator-authorized managed Claude setting."""
import hashlib
import json
import pathlib
import sys

TARGET = pathlib.Path('/home/sl/baton-v11.14aecfb/acp-claude.template.json')
EVIDENCE = pathlib.Path(__file__).resolve().parent / 'evidence'
KEY = 'CLAUDE_CODE_DISABLE_BACKGROUND_TASKS'

if sys.argv[1:] == ['prepare']:
    original = TARGET.read_bytes()
    document = json.loads(original)
    if KEY in document['agent']['env']:
        raise SystemExit('Setting already present; revalidate instead of overwriting.')
    document['agent']['env'][KEY] = '1'
    candidate = (json.dumps(document, indent=2) + '\n').encode()
    EVIDENCE.mkdir(exist_ok=True)
    for name, data in [('template-before.json', original), ('template-after.json', candidate)]:
        with (EVIDENCE / name).open('xb') as output:
            output.write(data)
    print('Prepared one agent.env key; no deployment file changed.')
elif sys.argv[1:] == ['apply']:
    original = (EVIDENCE / 'template-before.json').read_bytes()
    candidate = (EVIDENCE / 'template-after.json').read_bytes()
    before = json.loads(original)
    after = json.loads(candidate)
    if after['agent']['env'].pop(KEY) != '1' or after != before:
        raise SystemExit('Candidate is not the exact one-key change.')
    if TARGET.is_symlink() or not TARGET.is_file() or TARGET.read_bytes() != original:
        raise SystemExit('Deployment template drifted or changed type; refusing.')
    mode = TARGET.stat().st_mode
    with TARGET.open('wb') as output:
        output.write(candidate)
        output.flush()
        import os
        os.fsync(output.fileno())
    if TARGET.read_bytes() != candidate or TARGET.stat().st_mode != mode:
        raise SystemExit('Post-write verification failed.')
    print(json.dumps({'setting': KEY, 'value': '1', 'sha256': hashlib.sha256(candidate).hexdigest(), 'mode_preserved': True}))
else:
    raise SystemExit('Expected prepare or apply.')
