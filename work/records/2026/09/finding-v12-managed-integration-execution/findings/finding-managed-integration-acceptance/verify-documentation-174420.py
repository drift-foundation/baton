"""Read-only static checks; writes only this claim's new evidence when requested."""
from pathlib import Path
import datetime
import hashlib
import json
import re
import stat
import sys

record = Path(__file__).resolve().parent
sha = lambda data: hashlib.sha256(data).hexdigest()
manual = Path('v12/python/DEPLOYMENT.md')
base = (record / 'DEPLOYMENT-base-174271.md').read_bytes()
final = manual.read_bytes()
assert sha(base) == '48a3268e456765c02696c897558f1aed9511c39a4188480a8d194b21ac50077f'
regions = json.loads((record / 'regions-174420.json').read_text())
assert len(regions) == 5  # Four selected regions; table cell and paragraph are separate edits.
expected = []
def extent(begin, end):
    a = base.index(begin)
    return a, base.index(end, a)
cell = b'host composition verification |'
a = base.index(cell)
expected.append((a, a + len(cell)))
expected.append(extent(b'`host_verification` bounds', b'\n\n'))
expected.append(extent(b'- **`host_verification`**', b'\n- **A derived judgment**'))
expected.append(extent(b'**What an operator cannot do to a host hold.**', b'\n\n'))
expected.append(extent(b'## Managed integration: what exists so far (W161230 slice 1)', b'## Runtime-attempt deadlines'))
assert [(x['base_start'], x['base_end']) for x in regions] == expected
rebuilt = bytearray(); cursor = 0; unchanged = []
for item in regions:
    a, b = item['base_start'], item['base_end']
    unchanged.append({'base_start': cursor, 'base_end': a, 'sha256': sha(base[cursor:a])})
    rebuilt += base[cursor:a] + item['replacement'].encode()
    cursor = b
rebuilt += base[cursor:]
unchanged.append({'base_start': cursor, 'base_end': len(base), 'sha256': sha(base[cursor:])})
assert bytes(rebuilt) == final, 'Changes outside selected replacements'
suffix = final[final.index(b'## Runtime-attempt deadlines'):]
assert suffix == base[base.index(b'## Runtime-attempt deadlines'):]
assert sha(suffix) == '9331091b9ab11742b620b92b476e97775fc52739a9d37139b08bb1afe6e7ef89'
mode = manual.lstat().st_mode
assert stat.S_ISREG(mode) and stat.S_IMODE(mode) == 0o664

# Check fence structure across the whole document, and every new link.
opened = None; fence_count = 0
for line in final.decode().splitlines():
    match = re.match(r'^\s*(`{3,}|~{3,})(.*)$', line)
    if not match:
        continue
    marker, rest = match.groups()
    if opened is None:
        opened = marker
    elif marker[0] == opened[0] and len(marker) >= len(opened) and not rest.strip():
        opened = None
    fence_count += 1
assert opened is None, 'Unclosed Markdown fence'
assert '#managed-integration' in final.decode() and b'## Managed integration\n' in final
added_links = []
for item in regions:
    for target in re.findall(r'\]\(([^)]+)\)', item['replacement']):
        if target.startswith('#'):
            assert target == '#managed-integration'
        else:
            assert (manual.parent / target).exists(), target
        added_links.append(target)
assert Path('v12/worker/Dockerfile.reconciliation').is_file()

# Preserve the independent assessment's effective current candidate, without repinning drift.
checks = []
baseline = json.loads((record / 'baseline-174271.json').read_text())
for item in baseline['files']:
    if item['kind'] == 'current-latest-accepted':
        actual = sha(Path(item['path'].removeprefix('baton:')).read_bytes())
        checks.append({'path': item['path'], 'expected': item['sha256'], 'actual': actual, 'matches': actual == item['sha256']})
assert len(checks) == 33 and all(x['matches'] for x in checks)
evidence = {'claim': 174420, 'checked_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'manual': 'baton:v12/python/DEPLOYMENT.md', 'base_sha256': sha(base),
            'final_sha256': sha(final), 'final_bytes': len(final), 'mode': oct(stat.S_IMODE(mode)),
            'exact_selected_region_extents': expected, 'outside_regions_byte_identical': True,
            'unchanged_segments': unchanged, 'protected_suffix_sha256': sha(suffix),
            'protected_suffix_bytes': len(suffix), 'markdown_fences_balanced': True,
            'fence_marker_count': fence_count, 'replacement_links': added_links,
            'effective_current_paths': checks, 'runtime_tests_run': 0}
if '--record' in sys.argv:
    destination = record / 'verification-174420.json'
    assert not destination.exists(), 'Do not overwrite recorded verification'
    destination.write_text(json.dumps(evidence, indent=2) + '\n')
print(json.dumps({key: evidence[key] for key in ('final_sha256', 'final_bytes', 'mode', 'outside_regions_byte_identical', 'protected_suffix_sha256', 'markdown_fences_balanced')}))
print('33/33 effective accepted paths match; new local references resolve.')
