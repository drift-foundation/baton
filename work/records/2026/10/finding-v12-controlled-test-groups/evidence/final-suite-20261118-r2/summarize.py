"""W384870 final suite — summarize the test-all JSON ledger (reads only; pure evidence tooling).

Usage: python3 -I summarize.py test-all.summary.json
Prints a Markdown table of the ledger's totals and per-group collected counts, then EVERY
non-passing entry by outcome (failed, errors, fixture skips/errors, unaccounted, required skips,
duplicates, uncollected, unexpected successes, stray errors) and the optional skips with reasons.
"""
import json
import pathlib
import sys


def main(path):
    d = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    n = lambda k: len(d.get(k) or [])
    print(f"ledger: {path}")
    print(f"verdict ok: {d.get('ok')}")
    print()
    print("| collected | executed | passed | opt skip | req skip | failed | errors | fixture skip | fixture err | dup | unacc | uncoll | stray | unexp. success |")
    print("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    print(f"| {n('collected')} | {n('executed')} | {n('passed')} | {n('optional_skipped')} | {n('required_skipped')} | {n('failed')} | {n('errors')} | {n('fixture_skipped')} | {n('fixture_errors')} | {n('duplicates')} | {n('unaccounted')} | {n('uncollected')} | {n('stray_errors')} | {n('unexpected_successes')} |")
    print()
    print("| group | collected |"); print("|---|---|")
    for g, c in sorted((d.get("groups") or {}).items()):
        print(f"| {g} | {c} |")
    print()
    print(f"accounting identity: passed {n('passed')} + optional skipped {n('optional_skipped')} = {n('passed') + n('optional_skipped')} of collected {n('collected')}")
    print()
    for key in ("failed", "errors", "unaccounted", "duplicates", "uncollected", "unexpected_successes"):
        items = d.get(key) or []
        print(f"## {key} ({len(items)})")
        for one in items:
            print(f"- {one if isinstance(one, str) else json.dumps(one)[:300]}")
        print()
    for key in ("required_skipped", "fixture_skipped", "fixture_errors", "optional_skipped"):
        items = d.get(key) or {}
        print(f"## {key} ({len(items)})")
        for one, why in items.items():
            print(f"- {one} — {str(why)[:200]}")
        print()
    stray = d.get("stray_errors") or []
    print(f"## stray_errors ({len(stray)})")
    for one in stray:
        print(f"- {json.dumps(one)[:300]}")
    phases = d.get("phases")
    if phases:
        print(); print("## phases"); print(json.dumps(phases, indent=1)[:4000])


if __name__ == "__main__":
    main(sys.argv[1])
