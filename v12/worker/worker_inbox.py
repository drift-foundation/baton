"""One provider-independent, read-only Job inbox fetch; no host capability."""
import argparse
import contextlib
import contextvars
import json
import os
import re
import stat

COMMAND_ROOT = '/run/baton/exchange/command'
EVENT_ROOT = '/run/baton/exchange/events'
MAX_BYTES = 65536
MAX_ENTRIES = 128
INSTRUCTIONS = ('Use python3 /opt/baton/worker_inbox.py --after SEQUENCE to fetch newer '
                'entries from your own Job main thread during this turn. Before handing off '
                'a candidate or verdict, check for newer entries with this fetch. Continue '
                'from last_sequence until no entries are returned. The recorded cursor is '
                'delivery evidence only; it does not imply comprehension or action. Notes '
                'have no scheduling effect.')


_channel = contextvars.ContextVar('worker_inbox_channel', default=None)


@contextlib.contextmanager
def channel(command_root, event_root):
    """The wrapper binds the already governed exchange for this invocation."""
    token = _channel.set((command_root, event_root))
    try:
        yield
    finally:
        _channel.reset(token)


def roots():
    return _channel.get() or (COMMAND_ROOT, EVENT_ROOT)


def available():
    return os.path.isfile(os.path.join(roots()[0], '.inbox.json'))


def _read(root, name, limit=MAX_BYTES):
    directory = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        handle = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
    finally:
        os.close(directory)
    try:
        if not stat.S_ISREG(os.fstat(handle).st_mode):
            raise ValueError('inbox document is not regular')
        raw = os.read(handle, limit + 1)
    finally:
        os.close(handle)
    if len(raw) > limit:
        raise ValueError('inbox document exceeds its bound')
    return json.loads(raw)


def fetch(after=0, *, command_root=None, event_root=None):
    configured_command, configured_event = roots()
    command_root = configured_command if command_root is None else command_root
    event_root = configured_event if event_root is None else event_root
    if type(after) is not int or not 0 <= after < 2**63:
        raise ValueError('invalid inbox cursor')
    binding = _read(command_root, '.inbox.json', 1024)
    if type(binding) is not dict or set(binding) != {'attempt_id'} or type(binding['attempt_id']) is not str:
        raise ValueError('invalid inbox binding')
    numbers = sorted(int(name[7:-5]) for name in os.listdir(command_root)
                     if re.fullmatch(r'\.inbox-[1-9][0-9]{0,18}\.json', name))
    if after > (numbers[-1] if numbers else 0):
        raise ValueError('cursor beyond this attempt inbox')
    page = {'entries': [], 'last_sequence': after}
    for number in numbers:
        if number <= after:
            continue
        item = _read(command_root, f'.inbox-{number}.json')
        if set(item) != {'attempt_id', 'entry'} or item['attempt_id'] != binding['attempt_id']:
            raise ValueError('foreign inbox entry')
        entry = item['entry']
        if type(entry) is not dict or set(entry) != {'message_id', 'sequence', 'author', 'kind', 'body', 'phase'} or entry['sequence'] != number:
            raise ValueError('invalid inbox entry')
        proposed = {'entries': page['entries'] + [entry], 'last_sequence': number}
        if len(json.dumps(proposed).encode()) > MAX_BYTES:
            break
        page = proposed
        if len(page['entries']) == MAX_ENTRIES:
            break
    # Evidence is explicitly untrusted at the host. Preserve a higher local
    # claim on a repeated fetch; only the manager decides whether it is valid.
    last = page['last_sequence']
    try:
        prior = _read(event_root, 'inbox-fetched.json', 1024)
    except FileNotFoundError:
        prior = None
    if prior is not None and prior.get('attempt_id') == binding['attempt_id'] and type(prior.get('last_sequence')) is int:
        last = max(last, prior['last_sequence'])
    document = dict(binding, last_sequence=last)
    directory = os.open(event_root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        name = '.inbox-fetched.json.tmp'
        handle = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600, dir_fd=directory)
        with os.fdopen(handle, 'w') as output:
            json.dump(document, output)
            output.flush()
            os.fsync(output.fileno())
        os.rename(name, 'inbox-fetched.json', src_dir_fd=directory, dst_dir_fd=directory)
        os.fsync(directory)
    finally:
        os.close(directory)
    return page


def prompt():
    try:
        document = _read(roots()[0], '.inbox-start.json')
    except FileNotFoundError:
        document = None
    page = None if document is None else {key: document[key] for key in ('entries', 'last_sequence')}
    return '\n\n' + INSTRUCTIONS + ('\nPhase-start inbox: ' + json.dumps(page) if page else '')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=INSTRUCTIONS)
    parser.add_argument('--after', type=int, default=0)
    print(json.dumps(fetch(parser.parse_args().after)))
