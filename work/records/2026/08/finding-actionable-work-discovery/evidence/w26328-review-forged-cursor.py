"""Reproduce acceptance of a well-shaped cursor the authority never returned.

Run from the repository root:

    python3 -B work/records/2026/08/finding-actionable-work-discovery/evidence/w26328-review-forged-cursor.py
"""

import base64
import pathlib
import sys
import tempfile


REPOSITORY = pathlib.Path(__file__).resolve().parents[6]
sys.path.insert(0, str(REPOSITORY / "src"))
sys.path.insert(0, str(REPOSITORY / "tests" / "work"))

from baton_work import projection, transitions  # noqa: E402
import fixtures  # noqa: E402


def token(*parts):
	text = "\x1f".join(str(one) for one in parts)
	return base64.urlsafe_b64encode(text.encode()).decode().rstrip("=")


with tempfile.TemporaryDirectory(prefix="w26328-forged-cursor-") as directory:
	store = fixtures.open_instance(directory)
	work = transitions.create_work(
		store, team="lang", kind="rsrch", title="still waiting",
		origin="external-report", author="ada",
		classification="confirmed-defect", body="body")["work_id"]
	forged = token("w1", 99, 99, 999999999, "not-this-authority-W999999999")
	answer = projection.actionable_work(
		store, viewer_team="lang", viewer_member="ada", after=forged)
	print("forged token accepted:", forged)
	print("still actionable:", work)
	print("returned rows:", [row["id"] for row in answer["rows"]])
	assert answer["rows"] == []
