"""W384870 M385102 — consolidate the five accounted group ledgers into one remainder list.

Usage: python3 -I consolidate.py DIR
Reads DIR/<group>.summary.json, DIR/<group>.log, DIR/exit-codes.txt and DIR/known-g2-ids.txt; prints a
Markdown per-group table and every non-passing id (failed, errors, fixture skips/errors, unaccounted,
required skipped, duplicates, uncollected, unexpected successes), each marked KNOWN-G2 or NEW. Reads only.
"""
import json
import pathlib
import re
import sys

GROUPS = ("authority", "job_manager", "manager-pure", "tools-pure", "integration")
LIST_KEYS = ("failed", "errors", "unaccounted", "duplicates", "uncollected", "unexpected_successes")
DICT_KEYS = ("required_skipped", "fixture_skipped", "fixture_errors")


def main(root):
    root = pathlib.Path(root)
    known = set(filter(None, (root / "known-g2-ids.txt").read_text().split()))
    codes = {}
    for line in (root / "exit-codes.txt").read_text().splitlines():
        g, code, secs = line.split()
        codes[g] = (int(code), int(secs))
    print("| group | collected | executed | passed | opt skip | req skip | failed | errors | fixture skip | fixture err | dup | unacc | uncoll | stray | verdict | exit | elapsed s |")
    print("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    remainder = {}
    for g in GROUPS:
        path = root / f"{g}.summary.json"
        if not path.exists():
            print(f"| {g} | (no ledger) |" + " |" * 15)
            continue
        d = json.loads(path.read_text())
        n = lambda k: len(d.get(k) or [])
        code, secs = codes.get(g, ("?", "?"))
        log = (root / f"{g}.log").read_text() if (root / f"{g}.log").exists() else ""
        verdict = "OK" if d.get("ok") else "FAILED"
        drift = "stable" if "source identity stable" in log else ("DRIFT" if "SOURCE DRIFT" in log else "?")
        print(f"| {g} | {n('collected')} | {n('executed')} | {n('passed')} | {n('optional_skipped')} | {n('required_skipped')} | {n('failed')} | {n('errors')} | {n('fixture_skipped')} | {n('fixture_errors')} | {n('duplicates')} | {n('unaccounted')} | {n('uncollected')} | {n('stray_errors')} | {verdict} (source {drift}) | {code} | {secs} |")
        for k in LIST_KEYS:
            for one in d.get(k) or []:
                remainder.setdefault(one, set()).add(k)
        for k in DICT_KEYS:
            for one in d.get(k) or {}:
                remainder.setdefault(one, set()).add(k)
        for one in d.get("stray_errors") or []:
            text = one if isinstance(one, str) else json.dumps(one)[:200]
            remainder.setdefault(f"STRAY {text}", set()).add("stray_errors")
    print()
    known_rows = sorted(i for i in remainder if i in known)
    new_rows = sorted(i for i in remainder if i not in known)
    print(f"non-passing entries: {len(remainder)}; KNOWN-G2 {len(known_rows)} of {len(known)} known ids; NEW {len(new_rows)}")
    print()
    print("## KNOWN-G2 (still failing)")
    for i in known_rows:
        print(f"- {i} — {', '.join(sorted(remainder[i]))}")
    print()
    print("## KNOWN-G2 ids NOT in the remainder (now passing or not collected)")
    for i in sorted(known - set(remainder)):
        print(f"- {i}")
    print()
    print("## NEW (not in the known G2 list)")
    for i in new_rows:
        print(f"- {i} — {', '.join(sorted(remainder[i]))}")
    print()
    print("## optional skips (registry)")
    for g in GROUPS:
        path = root / f"{g}.summary.json"
        if path.exists():
            for i, why in (json.loads(path.read_text()).get("optional_skipped") or {}).items():
                print(f"- [{g}] {i} — {why[:120]}")


if __name__ == "__main__":
    main(sys.argv[1])
