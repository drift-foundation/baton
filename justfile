set shell := ["bash", "-lc"]
set quiet

VENV := ".venv"
PY := VENV + "/bin/python3"

default: test

# Create the repository-local development environment. Baton itself remains
# stdlib-only; this installs test tooling only.
venv:
	#!/usr/bin/env bash
	set -euo pipefail
	if [[ ! -x "{{PY}}" ]]; then
		echo "[venv] creating ./{{VENV}} ..."
		python3 -m venv "{{VENV}}"
	fi
	if "{{PY}}" -c 'import pytest; assert pytest.__version__ == "9.0.1"' >/dev/null 2>&1; then
		echo "[venv] ./{{VENV}} is ready."
		exit 0
	fi
	"{{PY}}" -m pip install -r requirements-dev.txt
	echo "[venv] ready."

# Run the complete reusable test suite.
test:
	#!/usr/bin/env bash
	set -euo pipefail
	[[ -x "{{PY}}" ]] || { echo "error: venv missing; run 'just venv' first" >&2; exit 1; }
	"{{PY}}" -c 'import pytest' >/dev/null 2>&1 || { echo "error: pytest missing; run 'just venv' first" >&2; exit 1; }
	PYTHONPATH=. "{{PY}}" -m pytest -q \
		test_core_conformance.py \
		test_core_api.py \
		test_retired_oracle.py \
		test_core_authoring.py \
		test_core_references.py \
		test_tui_safe_text.py \
		test_tui_editor.py \
		test_tui_drafts.py \
		test_tui_state.py \
		test_tui_render.py \
		test_tui_driver.py \
		test_tui_pty.py \
		test_packaging_isolation.py \
		test_docs_consistency.py

# Rebuild the deterministic standalone distribution and manifest.
#
# The CLI and the console have SEPARATE builders on purpose: the surest way to
# keep the released CLI byte-frozen is for the code that could change it never
# to run when the console is rebuilt.
build:
	#!/usr/bin/env bash
	set -euo pipefail
	[[ -x "{{PY}}" ]] || { echo "error: venv missing; run 'just venv' first" >&2; exit 1; }
	"{{PY}}" build_zipapp.py

# Rebuild the console (baton-tui) distribution and its manifest.
build-tui:
	#!/usr/bin/env bash
	set -euo pipefail
	[[ -x "{{PY}}" ]] || { echo "error: venv missing; run 'just venv' first" >&2; exit 1; }
	"{{PY}}" build_tui.py
