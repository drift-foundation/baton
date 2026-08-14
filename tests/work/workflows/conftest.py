"""Workflow-suite fixtures: one built artifact per session, every workflow
parametrized over both drive modes (WORKFLOW-TESTS.md discipline 8)."""

from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import wfdriver                                               # noqa: E402


@pytest.fixture(scope="session")
def archive(tmp_path_factory):
	return wfdriver.build_archive(str(tmp_path_factory.mktemp("wfpack")))


@pytest.fixture(params=["source", "packaged"])
def flow(request, tmp_path, archive):
	return wfdriver.Flow(str(tmp_path), request.param, archive)
