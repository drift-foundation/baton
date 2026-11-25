"""Exact host import of the reviewed one-line build-context correction.

Preflight first; a refusal leaves the target untouched. Filesystem only."""
from pathlib import Path
import hashlib, json, os, stat, subprocess
ROOT = Path('/home/sl/src/baton'); NAME = 'v12/.dockerignore'
P = ROOT/'work/records/2026/11/finding-v12-native-provider-selection/evidence/import-dockerignore-04e364e4'
R2 = ROOT/'work/records/2026/11/finding-v12-native-provider-selection/evidence/product-image-preparation-r2'
BASE = 'ad6dcad0aa38f8ccc17fd6a50bd92bf6f2d8c402'
BEFORE = 'b7da7ead0d55e0df74be3b2df79d309fd3aa5455967e3a6bc1d705293cb57ca8'
AFTER = '04e364e4dbc1fdf8cf9fa7a76d81473563e1f129608df6fde2a6688548907da7'
ANCHOR = b'!python/src/baton_v12/source_profiles\n'; LINE = b'!python/src/baton_v12/provider_policy\n'
sha = lambda b: hashlib.sha256(b).hexdigest()
git = lambda *a: subprocess.run(['git', *a], cwd=ROOT, capture_output=True, env={**os.environ, 'GIT_OPTIONAL_LOCKS': '0'}).stdout.decode().strip()
c = json.loads((R2/'results/context-correction.json').read_text())
assert (c['path'], c['before'], c['after']) == (NAME, BEFORE, AFTER), 'retained evidence names another correction'
assert sha((R2/'context-correction.patch').read_bytes()) == '0c570f985ceee8253149134b82bd20f3078803d3620a1873921981d67521bf3f'
head = git('rev-parse', 'HEAD'); assert head == BASE, 'HEAD is not the reviewed base'
assert not git('diff', '--cached', '--name-only'), 'index has staged content'
assert not git('status', '--porcelain', '--', NAME), 'target drift against HEAD'
path = ROOT/NAME; s = path.lstat()
assert stat.S_ISREG(s.st_mode) and not path.is_symlink() and not path.parent.is_symlink()
old = path.read_bytes(); assert sha(old) == BEFORE and old.count(ANCHOR) == 1 and LINE not in old
new = old.replace(ANCHOR, ANCHOR + LINE); assert sha(new) == AFTER and len(new) == len(old) + len(LINE)
mode = stat.S_IMODE(s.st_mode); path.write_bytes(new)
assert sha(path.read_bytes()) == AFTER and stat.S_IMODE(path.stat().st_mode) == mode
changed = sorted(l[3:] for l in subprocess.run(['git', 'status', '--porcelain', '--untracked-files=all', '--', 'v12'], cwd=ROOT, capture_output=True, env={**os.environ, 'GIT_OPTIONAL_LOCKS': '0'}).stdout.decode().splitlines())
(P/'import.json').write_text(json.dumps({'path': NAME, 'base': BASE, 'head': head, 'index_empty': True, 'before': BEFORE, 'after': AFTER,
    'added_line': LINE.decode().strip(), 'mode': oct(mode), 'v12_status_paths_after': changed}, indent=2) + '\n')
print(json.dumps({'imported': NAME, 'after': AFTER, 'v12_status_paths_after': changed}))
