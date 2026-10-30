"""Pre-stage executor capability check for the selected W341357 invocation.

Read-only. Engine version and image inspect only; no container created, no
workload started, no Job submitted, no credential value read, nothing written
by this program except its own report on stdout.

The author's claim352156 copy of this check lived under /tmp and is gone after
the announced wipe (T341357 message352206). This is a REGENERATED check against
the same packet pins, not recovered historical bytes.
"""
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

PACKET = Path('/home/sl/src/baton/work/records/2026/10/finding-v12-attempt-'
              'failure-diagnostics/findings/finding-durable-failure-capture/'
              'execution-352156')
ROOT = Path('/home/sl/baton-instances/durable-capture-w341357-352156')
DISTRO = Path('/home/sl/baton-runs/managed-correction-236087/build/stack/out/distro')
BINARY_PIN = '04aa459aed61704971e98b9260929b19953c41caad906e28551aae0ba457a58a'
IMAGE = 'baton-v12-claude-worker:w239528-244216'
IMAGE_CONFIG_PIN = ('sha256:c862c055c6430addc918ca078a9e4d55f6bd8173ed9c9878a8'
                    'ad9d6cad334ca2')
REGISTRY = Path('/home/sl/.baton/credential-sources.json')
REFERENCE = 'w202663-development'
SLOT = 'claude'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def probe(name, argv):
    done = subprocess.run(argv, capture_output=True, text=True, timeout=30)
    return name, {'probe': name, 'argv': argv, 'status': done.returncode,
                  'stdout': done.stdout, 'stderr': done.stderr}


started = time.time()
denials = []
probes = {}

engine_answers = False
try:
    name, report = probe('engine-version',
                         ['docker', 'version', '--format', '{{json .}}'])
    probes[name] = {k: v for k, v in report.items() if k != 'stdout'}
    engine_answers = report['status'] == 0
    if not engine_answers:
        denials.append('engine does not answer: ' + report['stderr'].strip())
except Exception as exc:                                  # pragma: no cover
    denials.append('engine probe failed: %r' % (exc,))

image_available = False
inspected = None
try:
    name, report = probe('image-inspect',
                         ['docker', 'image', 'inspect', IMAGE,
                          '--format', '{{json .Id}}'])
    probes[name] = {k: v for k, v in report.items() if k != 'stdout'}
    image_available = report['status'] == 0
    if image_available:
        inspected = json.loads(report['stdout'].strip())
    else:
        denials.append('image not available: ' + report['stderr'].strip())
except Exception as exc:                                  # pragma: no cover
    denials.append('image probe failed: %r' % (exc,))

if image_available and inspected != IMAGE_CONFIG_PIN:
    denials.append('image config digest %r does not match the pinned %r'
                   % (inspected, IMAGE_CONFIG_PIN))

# Credential: REFERENCE EXISTENCE AND BACKING-FILE PRESENCE ONLY. No value is
# read, decoded or emitted.
credential = {'registry': str(REGISTRY), 'registry_present': REGISTRY.is_file(),
              'reference': REFERENCE, 'slot': SLOT, 'value_read': False,
              'note': 'reference existence and backing-file presence only; no '
                      'credential value was read, emitted or decoded'}
backing = None
if credential['registry_present']:
    sources = json.loads(REGISTRY.read_text())
    entries = sources.get('sources', sources)
    found = None
    if isinstance(entries, list):
        for one in entries:
            if one.get('reference') == REFERENCE or one.get('id') == REFERENCE:
                found = one
                break
    elif isinstance(entries, dict):
        found = entries.get(REFERENCE)
    credential['reference_present'] = found is not None
    if found:
        backing = found.get('path') or found.get('file') or found.get('source')
        credential['provider'] = found.get('provider') or found.get('kind')
    if not credential['reference_present']:
        denials.append('credential reference %r is not in the registry' % REFERENCE)
else:
    credential['reference_present'] = False
    denials.append('credential registry %s is absent' % REGISTRY)
if backing:
    credential['backing_path'] = str(backing)
    credential['backing_present'] = Path(backing).is_file()
    if not credential['backing_present']:
        denials.append('credential backing file %s is absent' % backing)

runtime = {'distro': str(DISTRO), 'distro_present': DISTRO.is_dir()}
binary = DISTRO / 'bin' / 'baton-v12-stack'
if not binary.is_file():
    matches = sorted(DISTRO.rglob('baton-v12-stack'))
    binary = matches[0] if matches else binary
runtime['binary_path'] = str(binary)
runtime['binary_present'] = binary.is_file()
if runtime['binary_present']:
    runtime['binary_sha256'] = sha(binary)
    runtime['binary_matches_pin'] = runtime['binary_sha256'] == BINARY_PIN
    if not runtime['binary_matches_pin']:
        denials.append('runtime binary digest does not match the pin')
else:
    runtime['binary_matches_pin'] = False
    denials.append('runtime binary is absent under %s' % DISTRO)

manifest = sha(PACKET / 'PACKET-INPUTS.json')

report = {
    'schema': 'baton.w341357-executor-capability/1',
    'claim': 352586,
    'when': 'BEFORE STAGING, as reroute352577 and the accepted PLAN require',
    'packet': str(PACKET.relative_to('/home/sl/src/baton')),
    'packet_manifest': manifest,
    'engine': 'docker',
    'engine_answers': engine_answers,
    'image_reference': IMAGE,
    'image_available': image_available,
    'image_config_digest_pinned': IMAGE_CONFIG_PIN,
    'image_config_digest_inspected': inspected,
    'image_digest_matches_pin': bool(image_available
                                     and inspected == IMAGE_CONFIG_PIN),
    'credential': credential,
    'runtime': runtime,
    'root': {'proposed': str(ROOT), 'absent': not ROOT.exists()},
    'probes': probes,
    'denials': denials,
    'read_only': 'engine version and image inspect only; no container created, '
                 'no workload started, no Job submitted, no credential value '
                 'read, nothing written anywhere',
    'regenerated': "the author's claim352156 copy of this check was under /tmp "
                   'and is absent after the announced wipe; this is a '
                   'regenerated check against the same packet pins, not '
                   'recovered historical bytes',
    'what_a_denial_means': 'Per reroute340145 a denial is reported and the turn '
                           'STOPS. No escalation, no workaround, no alternative '
                           'engine, no image build, no credential substitution.',
    'what_a_structural_check_cannot_do':
        'it cannot establish that a provider session is valid. run341637 failed '
        'on an expired OAuth session 0.337s after a clean check of this kind.',
    'why_not_the_boundary_preflight':
        'the boundary preflight reads packet/AUTHORING-COMMAND.json, which only '
        'exists after bind. This is the earlier check, against the packet pins; '
        'the boundary preflight still runs after bind and is the stronger one.',
}
if not ROOT.exists():
    pass
else:
    denials.append('proposed root %s already exists' % ROOT)
    report['root']['absent'] = False
report['denials'] = denials
report['verdict'] = 'capable' if not denials else 'denied'
report['seconds'] = round(time.time() - started, 3)
print(json.dumps(report, indent=1, sort_keys=True))
sys.exit(0 if not denials else 1)
