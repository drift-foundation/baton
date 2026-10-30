"""Read-only input check for the W333486 packet at the corrected shutdown checkpoint.

Opens no store, writes nothing, starts nothing.

TWO KINDS OF ANSWER, and the difference is the point. **Refusals** are things
that decide what would be built: a pinned preparation input, the declared
base's own manager and supervisor bytes, the bootstrap binary, the pinned
controller, the pinned shutdown helper the controller imports, a damaged
decision snapshot, an absent task input, a checkout document missing from the
base, a gate module that already exists. **Reports** are things that decide
what is next: whether each live decision source still matches the immutable
snapshot taken from it.

An earlier packet pinned the mutable reviewer-owned `FINDING.md` and
`PLAN.md`, so an ordinary current-plan update invalidated a sealed packet.
Review 2026-10-19T16-44-00Z asked for snapshots instead. Drift
in a live decision source is therefore REPORTED, exits 0, and is for review and
the owner to judge -- a snapshot records what was accepted when it was taken
and is not a second authority.

A drifted input means this packet is describing something that is no longer
there, and re-sealing it at the new bytes is the correct response -- never
editing a pin to match. That is exactly what happened to `../execution-337453`:
the shutdown correction moved the controller and the supervisor baseline under
it, so a successor was sealed and that one was preserved.

AND IT IS WHY THE PREVIOUS PACKET IS STILL VALID WHERE IT WAS PINNED.
`../execution-339421` pins the same vehicle bytes this packet pins; nothing
drifted under it. It is superseded for what its documents SAID -- worker-owned
post-run collection, absence read as a publication timeout, an overstated
filesystem non-effect, and absolute sibling file bans -- all four corrected
here under `decisions/review-339623.md`. When this program reported
DECISION-SOURCE DRIFT on `FINDING.md` and `PLAN.md` for that packet, that was
the design working: the reviewer had moved them, and reporting rather than
refusing is what let the sealed packet stay honest about what it was told.
"""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
PACKET_DIR = 'work/records/2026/10/finding-v12-attempt-failure-diagnostics/findings/finding-durable-failure-capture/execution-345822'
REPO = Path('/home/sl/src/baton')
DISTRO = Path('/home/sl/baton-runs/managed-correction-236087/build/stack/out/distro')
OLD = 'work/records/2026/09/finding-v12-single-implementation-proof'
OWED = ('v12/python/tests/manager/test_attempt_failure_cause.py',)
CONTROLLER = 'tools/authoring_enforcement.py'
SHUTDOWN = 'tools/authoring_shutdown.py'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


WORKER_DOCUMENTS = ('TASK.md', 'RECOVERY.md', 'COMPLETION.md', 'FIXTURE.md',
                    'ENFORCEMENT.md', 'SHUTDOWN.md', 'FAILURE.md')


def _recovery_checks(pins, held, repo, read):
    """The retained candidate, held against four independent records.

    Retargeted at `baton.w341357-recovery/3`. The previous revisions pinned a
    PRODUCER DIFF split out of an unfrozen working tree; this one pins the
    EXACT RETAINED CANDIDATE a completed run returned, so the records it is
    checked against are different records:

      1. the pinned bytes on disk, against the pin (done by the caller);
      2. the recovery index, against the pin -- same patch digest, same schema;
      3. the reviewer's INDEPENDENTLY PUBLISHED digests for the patch, the
         transport bundle and the candidate content, so a drift on either side
         is a refusal rather than a silent divergence;
      4. the RUN'S OWN retained evidence index, which is a separate immutable
         record of what that run returned -- head, base and content digest.

    The transport bundle is NOT pinned as a task input, deliberately: this
    campaign creates no version-control object on this host. Its digest is
    still checked against the reviewer's, because a drifted transport means the
    evidence set moved under the packet.
    """
    source = read(repo / held['index'])
    if source.get('schema') != held['index_schema']:
        raise RuntimeError('the recovery index is not '
                           + held['index_schema'] + ': ' + repr(source.get('schema')))
    patch = held['patch_relative']
    if source['candidate_patch']['sha256'] != held['files'][patch]:
        raise RuntimeError('the recovery index and the pins disagree about the '
                           'retained candidate patch')
    if not source.get('agrees_with_reviewer_digests'):
        raise RuntimeError('the recovery index does not record agreement with '
                           "the reviewer's published digests")
    candidate = held['candidate']
    for field in ('head', 'base'):
        if source.get(field) != candidate[field]:
            raise RuntimeError('the recovery index names another candidate '
                               + field)
    if source.get('candidate_content_digest') != candidate['content_digest']:
        raise RuntimeError('the recovery index names another candidate content')
    published = held['reviewer_published_digests']
    if source['reviewer_published_digests'] != published:
        raise RuntimeError("the recovery index carries different reviewer "
                           'digests than these pins')
    if published['candidate_patch'] != held['files'][patch]:
        raise RuntimeError('the pinned candidate patch disagrees with the '
                           "reviewer's published digest")
    bundle = repo / held['transport_bundle']
    if not bundle.is_file():
        raise RuntimeError('the retained candidate transport is absent: '
                           + held['transport_bundle'])
    if hashlib.sha256(bundle.read_bytes()).hexdigest() \
            != published['candidate_objects_bundle']:
        raise RuntimeError('the retained candidate transport is not the '
                           "reviewer's published bytes")
    if held['transport_bundle'] in pins['task_inputs']:
        raise RuntimeError('the candidate transport must NOT be a task input: '
                           'this campaign creates no version-control object on '
                           'this host and restores nothing into the checkout')
    evidence = read(repo / held['run_evidence_index'])
    if evidence['run'] != candidate['run'] \
            or evidence['attempt'] != candidate['attempt']:
        raise RuntimeError('the run evidence index describes another run or '
                           'attempt')
    retained = evidence['candidate']
    if retained['head'] != candidate['head'] \
            or retained['base'] != candidate['base'] \
            or retained['content_digest'] != candidate['content_digest']:
        raise RuntimeError("the run's own evidence index names another "
                           'candidate than these pins')
    if sorted(source['changed_paths']) != sorted(retained['changed_paths']):
        raise RuntimeError('the recovery index and the run evidence disagree '
                           'about the candidate changed paths')
    return source


def recovery(pins, held):
    return _recovery_checks(pins, held, REPO, lambda place: json.loads(place.read_text()))


def blob(base, relative):
    return hashlib.sha256(subprocess.check_output(
        ['git', 'show', base + ':' + relative], cwd=REPO)).hexdigest()


def main():
    pins = json.loads((HERE / 'PREPARATION-PINS.json').read_text())
    base = pins['base']
    wrong, drift = [], []

    for name, expected in pins['files'].items():
        held = sha(REPO / name) if (REPO / name).is_file() else None
        if held != expected:
            wrong.append(f'preparation input {name}: {held} != {expected}')

    if sha(DISTRO / 'baton-v12-stack') \
            != pins['historical_bootstrap_binary_sha256']:
        wrong.append('the historical bootstrap binary is not its declared bytes')

    # THE ACCEPTED CONTROLLER MUST BE PINNED, because its own verify_controller
    # resolves itself inside the packet manager source and compares the digest.
    # A packet that staged it unpinned would refuse at launch rather than here.
    #
    # AND THE SHUTDOWN HELPER MUST BE PINNED TOO, for a blunter reason: the
    # controller imports it at line 26, so a manager source staged without it
    # does not start. Both are checked the same three ways -- the pin, the
    # packet's own manager source, and the declared base.
    for which, relative in (('authoring_controller', CONTROLLER),
                            ('shutdown_helper', SHUTDOWN)):
        held = pins[which]
        if held['relative'] != relative:
            wrong.append(f'the pinned {which} is not {relative}')
        elif pins['manager_files'].get(relative) != held['sha256']:
            wrong.append(f'the {which} digest disagrees with the pinned '
                         f'manager source')
        else:
            try:
                if blob(base, 'v12/python/' + relative) != held['sha256']:
                    wrong.append(f'the {which} is not its declared bytes at '
                                 f'the base')
            except subprocess.CalledProcessError:
                wrong.append(f'the {which} is not at the base')

    for relative, expected in pins['manager_files'].items():
        try:
            held = blob(base, 'v12/python/' + relative)
        except subprocess.CalledProcessError:
            held = None
        if held != expected:
            wrong.append(f'base manager source {relative}: {held} != {expected}')

    for name, expected in pins['supervisor_files'].items():
        try:
            held = blob(base, OLD + '/' + name)
        except subprocess.CalledProcessError:
            held = None
        if held != expected:
            wrong.append(f'base supervisor source {name}: {held} != {expected}')

    for name in pins['task_inputs']:
        if not (REPO / name).is_file():
            wrong.append(f'declared task input is absent: {name}')

    for name in pins['read_from_checkout_at_base']:
        try:
            blob(base, name)
        except subprocess.CalledProcessError:
            wrong.append(f'declared checkout input is not at the base: {name}')

    # THE SNAPSHOTS THEMSELVES ARE FATAL, because they live inside this packet:
    # a difference is a damaged packet, not a moved decision.
    index = json.loads((HERE / 'decisions/INDEX.json').read_text())['snapshots']
    for name, held in index.items():
        place = HERE / 'decisions' / name
        if not place.is_file():
            wrong.append(f'decision snapshot is absent: {name}')
        elif sha(place) != held['snapshot_sha256']:
            wrong.append(f'decision snapshot is damaged: {name}')

    # AND THE LIVE SOURCES ARE REPORTED. This is the whole reason the snapshots
    # exist; see the module docstring.
    for name, held in sorted(index.items()):
        source = REPO / held['source_path']
        now = sha(source) if source.is_file() else None
        if now != held['source_sha256']:
            drift.append(f'{held["source_path"]}: live {now} != snapshot '
                         f'{held["source_sha256"]} (decisions/{name})')

    task = (HERE / 'TASK.md').read_text()
    program = (HERE / 'prepare.py').read_text()
    for name in OWED:
        if name not in task:
            wrong.append(f'the task does not name the gate module {name}')
        dotted = name[len('v12/python/'):-len('.py')].replace('/', '.')
        if f"'{dotted}'" not in program:
            wrong.append(f'the sealed gate does not name {dotted}')
        if (REPO / name).exists():
            wrong.append(f'a gate module the turn must create already exists '
                         f'on the host: {name}')

    # THE RETAINED CANDIDATE. Fatal, like every other input that decides what
    # would be built: this packet continues from returned work and the turn's
    # first act is to apply exactly these bytes.
    held = pins.get('recovery_input')
    if not held:
        wrong.append('these pins declare no recovery input, and this packet '
                     'continues from preserved partial work')
    else:
        for relative, expected in sorted(held['files'].items()):
            place = REPO / relative
            if not place.is_file():
                wrong.append('a recovery input is absent: ' + relative)
            elif sha(place) != expected:
                wrong.append('a recovery input is not its declared bytes: ' + relative)
            if relative not in pins['task_inputs']:
                wrong.append('a recovery input is not a task input, so the turn '
                             'could not read it off the mount: ' + relative)
        try:
            recovery(pins, held)
        except RuntimeError as refused:
            wrong.append(str(refused))
        for name in WORKER_DOCUMENTS:
            if not (HERE / name).is_file():
                wrong.append('a worker-visible document is absent: ' + name)
            if f'{PACKET_DIR}/{name}' not in pins['task_inputs']:
                wrong.append('a worker-visible document is not a task input, so '
                             'the turn could not read it: ' + name)

    provenance = json.loads((HERE / 'PROVENANCE.json').read_text())
    if provenance['base'] != base or provenance['accepted'] is not False:
        wrong.append('the provenance disagrees with these pins')
    if provenance['start_authorized'] is not False:
        wrong.append('the provenance claims a start this packet holds')
    if provenance['checkpoint']['paths']:
        wrong.append('the provenance declares a restored buffer this '
                     'preparation does not carry')
    if provenance['start_selected'] is not False:
        wrong.append('the provenance claims a start nobody has selected')
    for which in ('enforcement', 'shutdown'):
        if not (HERE / provenance[which]['document']).is_file():
            wrong.append(f'the declared {which} document is absent')

    if wrong:
        for one in wrong:
            print('DRIFTED: ' + one)
        return 1
    print(f'inputs verified against {base}: '
          f'{len(pins["manager_files"])} manager files, '
          f'{len(pins["supervisor_files"])} supervisor files, '
          f'{len(pins["files"])} preparation inputs, '
          f'{len(pins["task_inputs"])} task inputs, '
          f'{len(index)} decision snapshots, '
          f'{len(pins["read_from_checkout_at_base"])} checkout documents, '
          f'1 pinned authoring controller, 1 pinned shutdown helper, '
          f'{len(held["files"]) if held else 0} pinned recovery inputs, '
          f'{len(OWED)} gate modules still owed')
    if drift:
        print('\nDECISION-SOURCE DRIFT (reported, not fatal; the turn reads the '
              'snapshots, and review decides whether they still reflect '
              'accepted scope):')
        for one in drift:
            print('  ' + one)
    else:
        print('no decision-source drift: every live source still matches its '
              'snapshot')
    print('\nSTART IS NOT SELECTED -- see ENFORCEMENT.md and SHUTDOWN.md. Every '
          'input gate is CLOSED; what remains is independent preparation '
          'review and then an exact execution selection. Use '
          'packet/AUTHORING-COMMAND.json, never commands.json start.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
