"""Reversal probes for walk-180078.py. Each reverts ONE guard and must fail.

REMOVED PROBES ARE RECORDED, NOT QUIETLY DROPPED. A `wider-export-names` probe
that added a seventh name to the export zip was tried and removed: it reverts
nothing, because `zip` truncates against the six-element key, so a name can only
reach the output if the KEY is widened too -- which `names-in-the-export`
already covers, loudly. Two independent things must change for a name to leak,
and that is a property of the code rather than a gap in the tests.

A probe that passes is a test that was not testing anything -- which is how the
missing first-turn artifact case was found at 179146 and the missing
expected-key case at 179295. Each probe runs in its own temporary copy with
__pycache__ removed and -B, so no probe can read another's bytecode.
"""
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
NAMES = ("walk-180078.py", "walk-180078-selftest.py")

PROBES = [
    ("no-link-skip", "walk-180078.py",
     "                        if stat.S_ISLNK(info.st_mode):\n                            links += 1\n                            continue\n", "",
     "links are no longer counted as unfollowed"),
    ("no-credential-skip", "walk-180078.py",
     "                        if CREDENTIAL.search(entry.name):\n                            credentials += 1\n                            continue\n", "",
     "credential-shaped entries are descended into"),
    ("follow-symlinks-on-stat", "walk-180078.py",
     "info = entry.stat(follow_symlinks=False)\n", "info = entry.stat(follow_symlinks=True)\n",
     "entry metadata follows links to their target"),
    ("opendir-follows", "walk-180078.py",
     "_OPEN_DIR = os.O_RDONLY | os.O_NOFOLLOW | os.O_DIRECTORY\n",
     "_OPEN_DIR = os.O_RDONLY | os.O_DIRECTORY\n",
     "a symlinked component is followed instead of refused"),
    ("no-truncation-flag", "walk-180078.py",
     "        if self.entries >= MAX_ENTRIES:\n            self.truncated = True\n            return False\n",
     "        if self.entries >= MAX_ENTRIES:\n            return False\n",
     "a truncated walk reports as complete"),
    ("no-depth-flag", "walk-180078.py",
     "                            budget.depth_limited = True\n", "",
     "a depth-limited walk reports as complete"),
    ("no-timeout-flag", "walk-180078.py",
     "            self.timed_out = True\n", "",
     "a timed-out walk reports as complete"),
    # Corrected at claim180413. The first version passed `row.get("name")`,
    # which is always None because `classify` never sets it -- the key gained an
    # empty slot and leaked nothing, so the probe reverted no guard at all.
    # Corrected twice. Adding a name to `row` leaks nothing, because `count`
    # builds the key from six named fields; adding a seventh key element leaks
    # nothing either, because the export zips against six names and truncates.
    # That truncation IS the protection, so the probe has to widen the export.
    ("names-in-the-export", "walk-180078.py",
     '        key = (row["type"], row["uid"], row["gid"], row["mode"], row["readable"], row["searchable"])\n',
     '        key = (row["type"], row["uid"], row["gid"], row["mode"], row["readable"], row["searchable"], row["seen_name"])\n',
     "a discovered name becomes part of the exported aggregate key"),
    # Corrected at claim180413. The first version reverted the `scandir`
    # handler, but an unsearchable directory fails at `os.open` and is caught by
    # the `opendir` handler -- the probe reverted a branch the test never
    # reaches. The `scandir` handler stays defence in depth with no synthetic
    # case, which is recorded rather than claimed as coverage.
    ("opendir-errors-swallowed", "walk-180078.py",
     '                        except OSError as failure:\n                            note_error("opendir", failure)\n',
     "                        except OSError:\n                            pass\n",
     "an unsearchable directory becomes a silent gap"),
    ("permissive-bit-order", "walk-180078.py",
     "    if info.st_uid == who[\"euid\"]:\n        return (mode >> 6) & 7\n", "",
     "owner bits are skipped, so the group/other answer is used for owned files"),
]

results = []
for label, filename, old, new, expectation in PROBES:
    with tempfile.TemporaryDirectory(prefix="w177936-walk-probe-") as place:
        copy = Path(place)
        for name in NAMES:
            shutil.copy2(HERE / name, copy / name)
        text = (copy / filename).read_text()
        assert text.count(old) == 1, (label, filename, text.count(old))
        (copy / filename).write_text(text.replace(old, new))
        for stale in copy.glob("__pycache__"):
            shutil.rmtree(stale)
        done = subprocess.run([sys.executable, "-B", str(copy / "walk-180078-selftest.py")],
                              capture_output=True, text=True, timeout=120, cwd=place)
        failed = sorted(set(re.findall(r"^(?:FAIL|ERROR): (\w+) \(", done.stderr, re.M)))
        results.append({"probe": label, "reverts": expectation,
                        "exit_code": done.returncode, "failing_tests": failed})
        print("%-24s exit=%d  %s" % (label, done.returncode, ", ".join(failed) or "NONE"))

HERE.joinpath("probes-180413.json").write_text(
    json.dumps({"probes": results,
                "note": "each probe reverts one guard in an isolated copy; every probe must fail"},
               indent=2) + "\n")
print("\nall probes failed as required:", all(r["exit_code"] != 0 and r["failing_tests"] for r in results))
