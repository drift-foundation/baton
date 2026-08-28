"""Measure W26328's CONSOLE half by removing its rules.

Same discipline as `/tmp/w26328_mutation.py`, over the surfaces an operator
reads: the tab count, the mandatory `Mine` column, and the flattened page.
Nothing here is a fix; every mutation is reverted before the next runs.
"""
import pathlib, shutil, subprocess, sys

HOME = pathlib.Path("/home/sl/src/baton")
SRC = HOME / "src" / "baton_work"
MODULES = ["tests/work/test_w26328_actionable_console.py",
           "tests/work/test_w26328_actionable_discovery.py",
           "tests/work/test_parity.py",
           "tests/work/test_w110_tab_grammar.py",
           "tests/work/test_w167_inbox_owed_marker.py",
           "tests/work/test_w25_jobs_teams_inbox.py",
           "tests/work/test_w292_breadcrumb_navigation.py"]

APP = "tui/app.py"

MUTATIONS = [
    # -- the tab count ------------------------------------------------------
    ("the Jobs tab carries no count at all", APP,
     '\t\t\t\tlabel += f" {self._window()[\'actionable_for_viewer\']}"',
     '\t\t\t\tpass'),

    ("zero is omitted instead of spelled", APP,
     '\t\t\t\tlabel += f" {self._window()[\'actionable_for_viewer\']}"',
     '\t\t\t\tif self._window()["actionable_for_viewer"]:\n'
     '\t\t\t\t\tlabel += f" {self._window()[\'actionable_for_viewer\']}"'),

    ("the count is how much Work is here, not how much is mine", APP,
     '\t\t\t\tlabel += f" {self._window()[\'actionable_for_viewer\']}"',
     '\t\t\t\tlabel += f" {len(self._window()[\'rows\'])}"'),

    ("the count comes from a second read of its own", APP,
     '\t\t\t\tlabel += f" {self._window()[\'actionable_for_viewer\']}"',
     '\t\t\t\tlabel += " 0"'),

    # -- the Mine column ----------------------------------------------------
    ("the mine cell forgets what is below", APP,
     '\treturn here + (f"+{below}" if below else "")',
     '\treturn here'),

    ("the mine cell forgets this row itself", APP,
     '\there = "me" if row.get("viewer_actionable") else ""',
     '\there = ""'),

    ("a blank cell is spelled as a zero", APP,
     '\treturn here + (f"+{below}" if below else "")',
     '\treturn (here + (f"+{below}" if below else "")) or "0"'),

    ("a wide count is clipped instead of widening the column", APP,
     '\tlongest = max((len(mine_cell(row)) for row in rows), default=0)\n'
     '\treturn max(len("Mine"), longest)',
     '\treturn len("Mine")'),

    ("the column is dropped under width pressure", APP,
     '\t\tmine_width = mine_column_width(selectable) if mine else 0',
     '\t\tmine_width = mine_column_width(selectable) \\\n'
     '\t\t\tif (mine and width >= 100) else 0'),

    ("the column is omitted when every cell is blank", APP,
     '\t\tmine_width = mine_column_width(selectable) if mine else 0',
     '\t\tmine_width = mine_column_width(selectable) if (\n'
     '\t\t\tmine and any(mine_cell(row) for row in selectable)) else 0'),

    ("the column leaks onto every table-shaped view", APP,
     '\t\t\t\tself._render_table(screen, height, width, rows,\n'
     '\t\t\t\t                   top=2)',
     '\t\t\t\tself._render_table(screen, height, width, rows,\n'
     '\t\t\t\t                   top=2, mine=True)'),

    ("the mandatory column is not in the width budget", APP,
     '\t\tmandatory = id_width + ((1 + mine_width) if mine_width else 0)',
     '\t\tmandatory = id_width'),

    # -- the flattened page -------------------------------------------------
    ("the breadcrumb is truncated rather than wrapped", APP,
     '\t\tfor index, text in enumerate(_wrap_value(crumb, room)):',
     '\t\tfor index, text in enumerate([crumb[:room]]):'),

    ("the entry names the Work instead of the path to it", APP,
     '\t\tcrumb = " > ".join(entry["title"]\n'
     '\t\t                   for entry in row.get("breadcrumb") or ())',
     '\t\tcrumb = row["title"]'),

    ("the page is bounded by something other than the ruled limit", APP,
     '\t\t\t\tafter=self.mine_after, limit=MINE_LIMIT))',
     '\t\t\t\tafter=self.mine_after, limit=10))'),

    ("the empty page is silent", APP,
     '\t\t\tscreen.addnstr(3, 0, "(no work awaiting you)", width - 1)',
     '\t\t\tpass'),

    ("entering the page records no navigation", APP,
     '\t\tself._nav_push("mine", "awaiting me")\n\t\tself.mode = "mine"',
     '\t\tself.mode = "mine"'),

    ("paging forward does not move the window", APP,
     '\t\t\tself.mine_after = self.mine_next\n\t\t\tself.mine_page += 1',
     '\t\t\tself.mine_page += 1'),

    ("the page inherits the tree's closed-visibility state", APP,
     '\t\trows = list(window["rows"])\n'
     '\t\tself._spend_owed_cycle(owed)\n'
     '\t\tself._observe_phases(rows)\n'
     '\t\treturn rows\n\n'
     '\tdef _spend_owed_cycle',
     '\t\trows = [one for one in window["rows"]\n'
     '\t\t        if self.show_closed or one["priority"] != "normal"]\n'
     '\t\tself._spend_owed_cycle(owed)\n'
     '\t\tself._observe_phases(rows)\n'
     '\t\treturn rows\n\n'
     '\tdef _spend_owed_cycle'),

    ("the key is bound but never taught", APP,
     '\t\t\t\t"[d] deps · m mine · Esc back · : command · q quit",',
     '\t\t\t\t"[d] deps · Esc back · : command · q quit",'),

    ("the page keeps no selection to come back to", APP,
     '\t"mine_after", "mine_page", "mine_next",',
     '\t"mine_after", "mine_next",'),
]

EXPECTED = set()


def run():
    return subprocess.run(
        [str(HOME / ".venv" / "bin" / "python3"), "-m", "pytest", "-q",
         "-p", "no:randomly", *MODULES],
        cwd=HOME, capture_output=True, timeout=1800)


def drop_cache():
    for c in (HOME / "src").rglob("__pycache__"):
        shutil.rmtree(c, ignore_errors=True)
    for c in (HOME / "tests").rglob("__pycache__"):
        shutil.rmtree(c, ignore_errors=True)


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
    caught = len(MUTATIONS) - len(EXPECTED)
    print(f"{caught} of {len(MUTATIONS)} mutations caught"
          + (f"; {len(EXPECTED)} expected-unseen and named above"
             if EXPECTED else ", none expected-unseen"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
