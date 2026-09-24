"""Claim-249551: make the fixture-root requirement explicit and checkable."""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent

CHECK = '''
# WHERE THE DISPOSABLE FIXTURE ROOT MAY LIVE, and why it is not folklore.
#
# Review 2026-09-23T17:25:40Z ran the roundtrip cases with a fixture root the
# product refused: `held_configuration` calls any mutable state inside "the
# checkout" a policy denial, and the checkout it detects is derived from the
# SOURCE THAT IMPORTED IT. Bound to the pinned snapshot under
# `/home/sl/baton-runs/...`, that makes `/home/sl/baton-runs` the checkout --
# so a fixture root under it is refused even though it is nowhere near the
# repository.
#
# The guard is right and is not weakened here. What this names is the setup
# that satisfies it: a DISK-BACKED directory outside both the repository and
# the pinned source's own root.
FIXTURE_ROOT_VARIABLE = "BATON_V12_DISK_ROOT"
FIXTURE_ROOT = "/var/tmp/baton-w247941"


def fixture_root_setup():
    """The exact command that prepares a usable disposable root."""
    return (f"mkdir -p {FIXTURE_ROOT} && "
            f"{FIXTURE_ROOT_VARIABLE}={FIXTURE_ROOT}")


def held_fixture_root(place=None):
    """Why a given fixture root will or will not serve. READ ONLY."""
    import os
    place = place or os.environ.get(FIXTURE_ROOT_VARIABLE)
    if not place:
        return [f"{FIXTURE_ROOT_VARIABLE} is unset; the suite would choose a "
                f"root for itself and may choose one the product refuses. "
                f"Use: {fixture_root_setup()}"]
    held = []
    whole = os.path.realpath(place)
    for what, root in (("this repository", str(CHECKOUT)),
                       ("the pinned source's own root",
                        os.path.dirname(str(SNAPSHOT)))):
        root = os.path.realpath(root)
        if os.path.commonpath([whole, root]) == root:
            held.append(f"{whole} is inside {what} at {root}; "
                        f"`held_configuration` denies mutable state there. "
                        f"Use: {fixture_root_setup()}")
    return held

'''


def main():
    place = HERE / "verify_247941.py"
    body = place.read_text(encoding="utf-8")
    if "FIXTURE_ROOT_VARIABLE" not in body:
        anchor = "def sha(path):"
        body = body.replace(anchor, CHECK.lstrip("\n") + "\n" + anchor, 1)
        body = body.replace(
            '''        held["found"]["runtime_executable_sha256"] = (''',
            '''        held["fixture_root"] = held_fixture_root()
        held["found"]["runtime_executable_sha256"] = (''')
    # the fixture-root finding must not silently pass the pin check
    body = body.replace(
        '''    held["agree"] = all(held["found"].get(name) == value
                        for name, value in PINNED.items())''',
        '''    held["fixture_root"] = held_fixture_root()
    held["agree"] = all(held["found"].get(name) == value
                        for name, value in PINNED.items())''')
    place.write_text(body, encoding="utf-8")

    page = HERE / "ADOPTION-247941.md"
    body = page.read_text(encoding="utf-8")
    if "FIXTURE ROOT" not in body:
        body = body.replace(
            "## Step 2 — resolve the selections",
            '''### Running this dossier's own checks

```sh
mkdir -p /var/tmp/baton-w247941
BATON_V12_DISK_ROOT=/var/tmp/baton-w247941 \\
PYTHONPATH="$BOUND:$DOSSIER" "$PY" -B "$DOSSIER/verify_247941.py"
```

**THE FIXTURE ROOT MATTERS, and the guard it satisfies is not weakened.**
`held_configuration` denies mutable deployment state inside "the checkout",
and the checkout it detects is derived from the source that imported it —
bound to the pinned snapshot under `/home/sl/baton-runs/...`, that makes
`/home/sl/baton-runs` the checkout. A disposable root under it is refused even
though it is nowhere near the repository. `verify_247941.py --pins` reports
`fixture_root` findings for exactly this reason.

## Step 2 — resolve the selections''', 1)
        page.write_text(body, encoding="utf-8")
    print("fixture-root requirement recorded")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
