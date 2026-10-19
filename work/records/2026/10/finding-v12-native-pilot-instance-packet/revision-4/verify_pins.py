"""Focused no-effects refusal for a changed frozen input."""
import json
import pathlib
import shutil
import sys
import tempfile
import time
import prepare

started = time.monotonic()
revision = pathlib.Path(__file__).resolve().parent
with tempfile.TemporaryDirectory(prefix='w325959-pin-check-') as temporary:
    packet = pathlib.Path(temporary) / 'packet'
    candidate = packet / 'revision-4'
    candidate.mkdir(parents=True)
    for name in ('inputs', 'configuration'):
        shutil.copytree(revision / name, candidate / name)
    shutil.copyfile(revision / 'FROZEN-INPUTS.json', candidate / 'FROZEN-INPUTS.json')
    target = candidate / 'configuration/task.json'
    target.write_bytes(target.read_bytes() + b' ')
    root = pathlib.Path(temporary) / 'w325959-preflight-refused'
    evidence = pathlib.Path(temporary) / 'evidence'
    sys.argv = ['prepare.py', '--packet', str(packet), '--root', str(root), '--evidence', str(evidence)]
    try:
        prepare.main()
    except prepare.CheckFailed as failure:
        assert failure.label == 'frozen input changed before preparation'
        assert not root.exists() and not evidence.exists()
    else:
        raise AssertionError('changed frozen input was accepted')
answer = {'changed_task_refused_before_any_root_or_evidence_creation': True, 'seconds': time.monotonic() - started}
(revision / 'evidence/PIN-REFUSAL.json').write_text(json.dumps(answer, indent=2) + '\n')
print(json.dumps(answer))
