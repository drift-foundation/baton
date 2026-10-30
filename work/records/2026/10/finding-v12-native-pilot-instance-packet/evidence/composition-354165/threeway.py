"""A line-level three-way merge that REFUSES rather than guesses.

W325959. `attempts.py` is the one accepted-diagnostics path whose base
(bc925cf5) and current committed baseline (d6881d8a) disagree, because the
human integrated W339626's candidate345109 at d3a7a41c and that commit added a
function to this file. The review requires every base/supplier mismatch
enumerated with an explicit resolution, and forbids letting the old candidate
bytes overwrite newer current paths without analysis.

So this composes rather than overwrites: it takes each side's edit regions
against the common base and applies both. IF THE TWO SIDES TOUCH AN
OVERLAPPING BASE REGION IT REFUSES, because a silent pick would be exactly the
overwrite the review forbids. It is deliberately not a general merge tool --
`git merge-file` is unavailable here and a hand-placed insertion would be a
guess.
"""
import difflib
import hashlib
import json
import pathlib
import sys


def regions(base, side):
    """Each (base_start, base_end, replacement_lines) this side changes."""
    out = []
    matcher = difflib.SequenceMatcher(a=base, b=side, autojunk=False)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag != 'equal':
            out.append((i1, i2, side[j1:j2], tag))
    return out


def merge(base, ours, theirs):
    mine, yours = regions(base, ours), regions(base, theirs)
    # OVERLAP IS A REFUSAL. Two edits to the same base lines cannot both be
    # applied and choosing one is the silent overwrite this exists to avoid.
    for a1, a2, _lines, _tag in mine:
        for b1, b2, _l, _t in yours:
            if max(a1, b1) < min(a2, b2) or (a1 == a2 and b1 == b2 == a1):
                raise SystemExit(
                    'REFUSED: both sides edit base lines '
                    f'[{a1},{a2}) and [{b1},{b2}); this needs a human '
                    'resolution, not a merge tool guess')
    edits = sorted(mine + yours, key=lambda one: (one[0], one[1]))
    out, cursor = [], 0
    for start, end, lines, _tag in edits:
        if start < cursor:
            raise SystemExit('REFUSED: edit regions are not disjoint')
        out.extend(base[cursor:start])
        out.extend(lines)
        cursor = end
    out.extend(base[cursor:])
    return out, mine, yours


here = pathlib.Path(sys.argv[1])
base = (here / 'base.py').read_text().splitlines(keepends=True)
ours = (here / 'head.py').read_text().splitlines(keepends=True)
theirs = (here / 'candidate.py').read_text().splitlines(keepends=True)

merged, mine, yours = merge(base, ours, theirs)
text = ''.join(merged)
(here / 'merged.py').write_text(text)

report = {
    'file': 'v12/python/src/baton_v12/worker_manager/attempts.py',
    'base': 'bc925cf5c62d69426ed5862af4d41f4d2a967b0f',
    'current_baseline': 'd6881d8adbd567b6e92a4a2a1d0cb68ee781f70a',
    'base_lines': len(base),
    'current_baseline_lines': len(ours),
    'candidate_lines': len(theirs),
    'merged_lines': len(merged),
    'current_baseline_edit_regions': [
        {'base_lines': [a1, a2], 'tag': tag, 'replacement_lines': len(lines)}
        for a1, a2, lines, tag in mine],
    'candidate_edit_regions': [
        {'base_lines': [b1, b2], 'tag': tag, 'replacement_lines': len(lines)}
        for b1, b2, lines, tag in yours],
    'overlap': False,
    'resolution': 'BOTH SIDES APPLIED, no overlap. The current baseline adds '
                  'runtime_recovery_inventory after attempt_runtime_of; the '
                  'accepted candidate changes _order_quiescence branches to '
                  'carry the recording degradation. Disjoint base regions, so '
                  'neither overwrites the other.',
    'merged_sha256': hashlib.sha256(text.encode()).hexdigest(),
}
print(json.dumps(report, indent=1))
