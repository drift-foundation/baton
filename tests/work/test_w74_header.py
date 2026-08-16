"""W74: the root header drops the redundant '— top-level work' prose.

Identity and the live summary stay; drilled views keep their real
breadcrumbs; narrow behavior is unchanged. Presentation only.
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
	assert header.startswith("lang.ada"), header
	assert "top-level work" not in header, \
		"the redundant root prose survived"
	assert "—" not in header.split("[")[0], \
		"stray prose remains before the summary"
	for token in ("[oblig:", "[park:", "[due:"):
		assert token in header, f"the live summary lost {token}"
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0


def test_drilled_views_keep_their_real_breadcrumb(world):
	config_path, epic = world
	text, status, steps = ptyharness.drive(config_path, "lang.ada", [
		(b"\r", 0.5), (b"qy", 0.4)])
	drilled = ptyharness.replay(steps[0])
	assert "drill target" in drilled[0], \
		"the drilled breadcrumb lost its trail"
	assert "[oblig:" in drilled[0]
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0


def test_the_narrow_root_header_still_fits_and_identifies(world):
	config_path, _epic = world
	from baton_work.tui import app
	narrow = app.MIN_SPLIT_HEIGHT - 2
	text, status, _steps = ptyharness.drive(
		config_path, "lang.ada", [(b"qy", 0.4)], columns=44,
		lines=narrow)
	screen = ptyharness.replay(text, columns=44, lines=narrow)
	assert screen[0].startswith("lang.ada"), screen[0]
	assert "top-level work" not in "\n".join(screen)
	assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0
