"""Live PTY reproduction for W1568 — command submission vs Jobs Enter.

    python3 work/records/2026/08/finding-command-submit-opens-next-job/repro_pty.py

Drives the console on a REAL pty: open Jobs with a Job selected, press
`:`, type a command, submit it — once per Return spelling a terminal may
send, and once per shape of command. It prints, for each, whether Work
detail opened and what the bottom row said.

Against the tree BEFORE the fix:

    CR    summary                            detail=False  ok
    LF    summary                            detail=False  ok
    CRLF  summary                            detail=True   <detail footer>

`CR LF` is what a terminal in NEW LINE mode (LNM) sends for ONE Return.
Under ncurses' default `nl()` the tty's ICRNL turns the `CR` into an
`LF`, so the console reads two identical Enter keys: the first submits,
the second is a Jobs Enter. See FINDING.md, "Confirmed cause".

Against the tree AFTER it, every row reads `detail=False`, and the
regression that keeps it that way is
`tests/work/test_w1568_command_submit_enter.py`.
"""

from __future__ import annotations

import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(
	os.path.dirname(os.path.dirname(HERE)))))
sys.path.insert(0, os.path.join(REPO, "tests", "work"))
sys.path.insert(0, os.path.join(REPO, "src"))

import baton_work as bw                                        # noqa: E402
from baton_work import transitions as tr                       # noqa: E402
import fixtures as fx                                          # noqa: E402
import ptyharness                                              # noqa: E402

SPELLINGS = [("CR", b"\r"), ("LF", b"\n"), ("CRLF", b"\r\n")]
COMMANDS = ["summary", "claim work=W2", "bogusverb", "filter phase=queued"]


def build(directory):
	config_path, database = fx.build_instance(
		directory, {"lang": {"members": {"ada": ["dev"]},
		                     "kinds": ["bug"]}})
	store = bw.Authority(database)
	born = tr.create_work(store, team="lang", kind="bug",
	                      title="the one open Work",
	                      origin="external-report",
	                      classification="suspected-defect",
	                      author="ada", body="the opener")
	tr.post_thread(store, born["thread"], author_team="lang", author="ada",
	               body="a message so the detail view has one")
	store.close()
	return config_path


def submit(config_path, command, keys):
	"""One gesture: open the bar, type the command, press Return."""
	_text, _status, steps = ptyharness.drive(config_path, "lang.ada", [
		(b"", 0.7),
		(b":", 0.4),
		(command.encode(), 0.4),
		(keys, 1.2),
		(b"qy", 0.5),
	])
	screen = ptyharness.replay(steps[3])
	painted = [line for line in screen if line.strip()]
	return any("[Messages]" in line for line in screen), painted[-1][:52]


def main():
	for command in COMMANDS:
		for label, keys in SPELLINGS:
			config_path = build(tempfile.mkdtemp(prefix="w1568-"))
			opened, bottom = submit(config_path, command, keys)
			print(f"{label:5s} {command:22s} detail={opened!s:5s}  {bottom}")


if __name__ == "__main__":
	main()
