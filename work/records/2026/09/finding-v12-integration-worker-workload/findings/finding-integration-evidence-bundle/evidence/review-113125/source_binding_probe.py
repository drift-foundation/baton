"""Exercise an actual descriptor-relative read while the pathname is replaced."""
import json
import os
from pathlib import Path
import sys

REPO = Path('/home/sl/src/baton')
HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(REPO/'v12/python'), str(REPO/'v12/python/src')]
from tests.tools import test_integration_bundle as fixtures

case = fixtures.ProducerCase()
case.setUp()
observed = []
try:
    line = Path(case.line['line_path'])
    (line/'review-origin').write_bytes(b'original')
    original = line.stat()
    substituted = False
    def runner(argv, *, directory):
        global substituted
        if not substituted:
            parked = Path(str(line)+'-review-parked')
            line.rename(parked)
            line.mkdir()
            (line/'review-origin').write_bytes(b'replacement')
            assert (line/'review-origin').read_bytes() == b'replacement'
            handle = os.open('review-origin', os.O_RDONLY | os.O_NOFOLLOW, dir_fd=directory)
            try:
                payload = os.read(handle, 32)
            finally:
                os.close(handle)
            assert payload == b'original'
            assert os.path.samestat(os.fstat(directory), original)
            answer = case.objects(argv, directory=directory)
            line.rename(str(line)+'-review-replacement')
            parked.rename(line)
            substituted = True
        else:
            assert os.path.samestat(os.fstat(directory), original)
            answer = case.objects(argv, directory=directory)
        observed.append(list(argv))
        return answer
    answer = case.compose(runner=runner)
    fixtures.contract.read_bundle(answer['root'])
    assert observed and all('-C' not in argv and str(line) not in argv for argv in observed)
    report = dict(claim=113125, calls=len(observed), pathname_content_during_read='replacement', descriptor_content_during_read='original', published_from_proved_directory=True, worker_readback=True, limitation='Disposable real-owner world with deterministic Git object answers; the marker read itself uses the actual supplied directory descriptor during substitution.')
finally:
    case.doCleanups()
with (HERE/'source-binding.json').open('x') as stream:
    json.dump(report, stream, indent=2)
    stream.write('\n')
print(json.dumps(report, indent=2))
