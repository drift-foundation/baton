"""Bind the exact candidate bytes for independent review."""
import hashlib
import json
import os
import subprocess

REPO = "/home/sl/src/baton"
DOSSIER = os.path.join(
    REPO, "work/records/2026/10/finding-v12-pilot-owner-disposition")
BASE = "6348161e608187393e45454db63c192a93f6deb3"

PRODUCT = [
    "v12/python/tools/disposition_command.py",
    "v12/python/tools/stack_command.py",
    "v12/python/tools/bootstrap.py",
    "v12/python/tools/dossier_command.py",
    "v12/python/src/baton_v12/authority/core.py",
    "v12/python/src/baton_v12/authority/api.py",
]
TESTS = [
    "v12/python/tests/tools/test_disposition_command.py",
    "v12/python/tests/tools/test_bootstrap.py",
    "v12/python/tests/authority/test_boundary.py",
    "v12/python/tests/authority/test_session.py",
]


def digest(path):
    with open(path, "rb") as handle:
        return "sha256:" + hashlib.sha256(handle.read()).hexdigest()


def blob(path):
    """The committed bytes at the base, or None for a new file."""
    held = subprocess.run(["git", "-C", REPO, "rev-parse",
                           BASE + ":" + path],
                          capture_output=True, text=True)
    if held.returncode != 0:
        return None
    return held.stdout.strip()


def main():
    members = {}
    for path in PRODUCT + TESTS:
        whole = os.path.join(REPO, path)
        about = os.lstat(whole)
        members[path] = {
            "digest": digest(whole),
            "bytes": about.st_size,
            "mode": oct(about.st_mode & 0o7777),
            "kind": "product" if path in PRODUCT else "test",
            "state": "new" if blob(path) is None else "modified",
            "base_blob": blob(path),
        }
    said = {
        "schema": "baton.w321689.candidate/1",
        "work": "2b077949-W321689",
        "base_commit": BASE,
        "base_note": "v12/python is unchanged between 433b09d6 (the W321688 "
                     "checkpoint) and this base; the two intervening commits "
                     "are documentation only",
        "execution_provenance": "direct shared-checkout implementation under "
                                "the owner's W321689-only completion "
                                "exception, 2026-10-18; no v12 Job provenance "
                                "is claimed",
        "members": members,
        "changed_paths": sorted(members),
        "frozen_bundle": {
            "built_from": "packaging/stack.spec through the prepared v12 "
                          "interpreter at "
                          "/home/sl/.local/state/baton-v12-venv/bin/python "
                          "(PyInstaller 6.16.0)",
            "distpath": "v12/python/build/w321689/out/distro (an ignored "
                        "build artifact, not candidate bytes)",
        },
        "not_in_this_candidate": [
            "src/baton_v12/authority/store.py -- the two pre-existing "
            "bounded-diagnostic failures in tests/authority/test_boundary.py "
            "are reported, not fixed: that file is outside this Work's scope "
            "and weakening the sweep to pass would remove defect coverage",
        ],
    }
    with open(os.path.join(DOSSIER, "candidate-321689", "DIGESTS.json"),
              "w", encoding="utf-8") as handle:
        json.dump(said, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps(said, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
