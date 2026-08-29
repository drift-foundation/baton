"""Measure W29146 by removing its rules one at a time.

Every mutation breaks ONE thing the correction claims, and is reverted before
the next runs. The modules are the new focused suite plus every suite whose
ruled behaviour this correction touches -- W2938's pickup star, W25's tab
grammar, W6's search, W292's navigation and the parity surface -- because a
correction that only its own tests notice has not been measured against the
rulings it had to keep.
"""
import pathlib, shutil, subprocess, sys

HOME = pathlib.Path("/home/sl/src/baton")
SRC = HOME / "src" / "baton_work"
MODULES = ["tests/work/test_w29146_cross_team_attention.py",
           "tests/work/test_w2938_participant_pickup.py",
           "tests/work/test_w25_jobs_teams_inbox.py",
           "tests/work/test_w6_search.py",
           "tests/work/test_w292_breadcrumb_navigation.py",
           "tests/work/test_parity.py"]

APP = "tui/app.py"
PROJ = "projection.py"

MUTATIONS = [
    # -- the attention-aware roster -----------------------------------------
    ("the foreign overdue exception is dropped again", APP,
     "\t\t\t\telif self._overdue(member):\n\t\t\t\t\trows.append(member)",
     "\t\t\t\telif False:\n\t\t\t\t\trows.append(member)"),

    ("every foreign member is shown, not only the overdue ones", APP,
     "\t\t\t\telif self._overdue(member):\n\t\t\t\t\trows.append(member)",
     "\t\t\t\telse:\n\t\t\t\t\trows.append(member)"),

    ("only the FIRST overdue foreign member is shown", APP,
     "\t\treturn [member for entry in self._roster() if not entry[\"mine\"]\n"
     "\t\t        for member in entry[\"members\"] if self._overdue(member)]",
     "\t\treturn [member for entry in self._roster() if not entry[\"mine\"]\n"
     "\t\t        for member in entry[\"members\"]\n"
     "\t\t        if self._overdue(member)][:1]"),

    ("pending is treated as attention", APP,
     "\t\treturn (member.get(\"pickup\") or {}).get(\"state\") == \"overdue\"",
     "\t\treturn (member.get(\"pickup\") or {}).get(\"state\") in (\n"
     "\t\t\t\"overdue\", \"pending\")"),

    # -- the scope line -----------------------------------------------------
    ("the scope line hides that a stranger is present", APP,
     "\t\texceptions = len(self.team_exceptions())\n"
     "\t\tif not exceptions:\n\t\t\treturn \"own team\"",
     "\t\texceptions = 0\n"
     "\t\tif not exceptions:\n\t\t\treturn \"own team\""),

    # -- entry focus --------------------------------------------------------
    ("a starred Teams tab opens on no cause at all", APP,
     "\t\t\tif self.tab == \"teams\":\n\t\t\t\tself._focus_attention()",
     "\t\t\tif False:\n\t\t\t\tself._focus_attention()"),

    ("entry focus moves the cursor even with nothing overdue", APP,
     "\t\tfirst = next((row for row in self.team_rows()\n"
     "\t\t              if self._overdue(row)), None)",
     "\t\tfirst = next((row for row in self.team_rows()), None)"),

    # -- the vanished-exception fallback ------------------------------------
    ("a vanished exception falls back to whatever index it held", APP,
     "\t\tmine = next((index for index, row in enumerate(rows)\n"
     "\t\t             if row[\"participant\"] == f\"{self.team}.{self.member}\"),\n"
     "\t\t            None)\n"
     "\t\tself.team_cursor = mine if mine is not None else 0",
     "\t\tself.team_cursor = min(self.team_cursor, len(rows) - 1)"),

    # -- the explicit suggested-Work link -----------------------------------
    ("Enter opens nothing", APP,
     "\t\t\tsuggested = (selected.get(\"pickup\") or {}).get(\"next_work\")",
     "\t\t\tsuggested = None"),

    ("Enter is advertised on a member with no suggestion", APP,
     "\t\tif (selected.get(\"pickup\") or {}).get(\"next_work\"):\n"
     "\t\t\tbits.append(\"Enter open suggested Work\")",
     "\t\tif True:\n\t\t\tbits.append(\"Enter open suggested Work\")"),

    # THE RULED DIFFERENCE between the two handovers. Inbox hands the
    # operator over to Jobs and Back leaves them there (W292); Teams is a
    # detour and Back returns. Removing the explicit frame makes Teams behave
    # like Inbox, which is a ruling broken rather than a preference changed.
    ("Back does not return to the Teams roster", APP,
     "\t\t\t\t\trestore={**self._nav_capture(), \"tab\": \"teams\",\n"
     "\t\t\t\t\t         \"team_cursor\": self.team_cursor,\n"
     "\t\t\t\t\t         \"team_member\": self.team_member,\n"
     "\t\t\t\t\t         \"teams_own_only\": self.teams_own_only})",
     "\t\t\t\t\trestore=None)"),

    ("Back returns to Teams but not to the same row", APP,
     "\t\t\t\t\t         \"team_member\": self.team_member,",
     "\t\t\t\t\t         \"team_member\": None,"),

    # -- the search scope ---------------------------------------------------
    ("the search result does not name its scope", PROJ,
     "\t        \"team\": viewer_team,", "\t        \"team\": None,"),

    ("the console assumes the scope instead of reading it", APP,
     "\t\tself.search_team = window[\"team\"]",
     "\t\tself.search_team = self.team"),

    ("the heading stops naming the team", APP,
     "\t\t\t               f\"search (team {self.search_team}): \"",
     "\t\t\t               f\"search: \""),

    ("the empty result stops naming the team", APP,
     "\t\t\t\t               f\"{self.search_query!r} in team \"\n"
     "\t\t\t\t               f\"{self.search_team})\", width - 1)",
     "\t\t\t\t               f\"{self.search_query!r})\", width - 1)"),
]

EXPECTED = set()


def run():
    return subprocess.run(
        [str(HOME / ".venv" / "bin" / "python3"), "-m", "pytest", "-q",
         "-p", "no:randomly", *MODULES],
        cwd=HOME, capture_output=True, timeout=1800)


def drop_cache():
    for cache in (HOME / "src").rglob("__pycache__"):
        shutil.rmtree(cache, ignore_errors=True)
    for cache in (HOME / "tests").rglob("__pycache__"):
        shutil.rmtree(cache, ignore_errors=True)


def main():
    drop_cache()
    base = run()
    print(f"BASELINE  {'OK' if base.returncode == 0 else 'FAILING'}\n")
    if base.returncode != 0:
        print(base.stdout.decode()[-3000:])
        return 1
    missed = []
    for name, where, before, after in MUTATIONS:
        place = SRC / where
        original = place.read_text()
        if original.count(before) != 1:
            print(f"[ANCHOR] {name}: {original.count(before)}x")
            missed.append(name)
            continue
        place.write_text(original.replace(before, after))
        drop_cache()
        try:
            found = run()
        finally:
            place.write_text(original)
            drop_cache()
        assert place.read_text() == original
        if found.returncode == 0:
            if name in EXPECTED:
                print(f"[expected-unseen] {name}")
                continue
            print(f"[UNSEEN] {name}")
            missed.append(name)
        else:
            out = found.stdout.decode()
            failed = [line.split("::")[-1].split()[0]
                      for line in out.splitlines() if line.startswith("FAILED")]
            print(f"[caught] {name}\n         {', '.join(failed)[:130]}")
    print()
    if missed:
        print(f"{len(missed)} UNESTABLISHED:")
        for one in missed:
            print(" -", one)
        return 1
    print(f"all {len(MUTATIONS)} mutations caught")
    return 0


if __name__ == "__main__":
    sys.exit(main())
