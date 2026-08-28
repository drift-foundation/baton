"""W74: the root header drops the redundant '— top-level work' prose.

Identity stays; drilled views keep their real breadcrumbs; narrow
behavior is unchanged. Presentation only.

SUPERSEDED IN PART by W25 (finding-tui-jobs-teams-inbox), 2026-08-19:
the "live summary" half of W74 is gone. The header now leads with the
three top-level tabs and right-aligns the participant identity, and the
`[oblig] [park] [due]` counters are retired — owed action is the Inbox
tab's subject and parked Work is filterable in Jobs. W74's own
question survives unchanged and is what these tests still ask: does the
root header identify the operator without redundant prose, do drilled
views keep their real trail, and does a narrow terminal still say who
and where you are.
"""

from __future__ import annotations

import json as _json
import os
import pty as _pty
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(
	os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
	"src"))

import baton_work as bw                                       # noqa: E402
from baton_work import lifecycle as lc                        # noqa: E402
from baton_work import transitions as tr                      # noqa: E402
import fixtures                                               # noqa: E402
import ptyharness                                             # noqa: E402

pytestmark = pytest.mark.skipif(not hasattr(_pty, "fork"),
                                reason="no pty support")


@pytest.fixture()
def world(tmp_path):
	config_path = str(tmp_path / "baton.json")
	document = fixtures.config_document(
		{"lang": {"members": {"ada": ["dev"]}, "kinds": ["bug"]}})
	with open(config_path, "w") as handle:
		_json.dump(document, handle, indent=2, sort_keys=True)
	result = lc.init_from_config(config_path, participant="lang.ada")
	store = bw.Authority(result["database"])
	epic = tr.create_work(store, team="lang", kind="bug",
	                      title="drill target", origin="external-report", classification="suspected-defect",
	                      author="ada", body="opener")
	store.close()
	return config_path, epic


def test_the_root_header_is_identity_plus_summary_only(world):
	config_path, _epic = world
	text, status, _steps = ptyharness.drive(config_path, "lang.ada",
	                                        [(b"qy", 0.4)])
	screen = ptyharness.replay(text)
	header = screen[0]
	assert header.startswith("[Jobs "), header
	assert header.rstrip().endswith("lang.ada"), \
		"the participant identity left the right edge"
	assert "top-level work" not in header, \
		"the redundant root prose survived"
	for token in ("[oblig:", "[park:", "[due:"):
		assert token not in header, \
			f"the retired counter {token} came back"
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0


def test_drilled_views_keep_their_real_breadcrumb(world):
	"""W292 supersedes this test's tab expectation, and only that.

	A drilled view still shows its real location and still keeps the
	participant identity at the right edge. What changed is that the
	location is now the whole navigation path starting at the top-level
	page, and the global tab row is NOT repeated beneath it — two tab
	rows on one screen implied two peer navigation surfaces when one of
	them is a drill-down inside the other."""
	config_path, epic = world
	text, status, steps = ptyharness.drive(config_path, "lang.ada", [
		(b"\r", 0.5), (b"qy", 0.4)])
	drilled = ptyharness.replay(steps[0])
	assert "drill target" in drilled[0], \
		"the drilled breadcrumb lost its trail"
	assert drilled[0].startswith("Jobs > "), \
		f"the drilled trail does not start at its page: {drilled[0]!r}"
	for label in ("[Jobs ", "[Teams]", "[Inbox"):
		assert label not in drilled[0], \
			f"the global tab row survived the drill-in: {drilled[0]!r}"
	assert drilled[0].rstrip().endswith("lang.ada")
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0


def test_the_narrow_root_header_still_fits_and_identifies(world):
	config_path, _epic = world
	from baton_work.tui import app
	narrow = app.MIN_SPLIT_HEIGHT - 2
	text, status, _steps = ptyharness.drive(
		config_path, "lang.ada", [(b"qy", 0.4)], columns=44,
		lines=narrow)
	screen = ptyharness.replay(text, columns=44, lines=narrow)
	# Identity overdraws LAST, so the one fact a narrow header can
	# never lose is who the operator is signed in as.
	assert screen[0].rstrip().endswith("lang.ada"), screen[0]
	assert screen[0].startswith("[Jobs "), screen[0]
	assert "top-level work" not in "\n".join(screen)
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0
