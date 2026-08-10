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
	"{{PY}}" -m pip install -r tools/requirements-dev.txt
	echo "[venv] ready."

# Run the complete reusable test suite.
test:
	#!/usr/bin/env bash
	set -euo pipefail
	[[ -x "{{PY}}" ]] || { echo "error: venv missing; run 'just venv' first" >&2; exit 1; }
	"{{PY}}" -c 'import pytest' >/dev/null 2>&1 || { echo "error: pytest missing; run 'just venv' first" >&2; exit 1; }
	# DISCOVERED, not enumerated. The list that used to live here was a
	# hand-maintained subset: adding a test file and forgetting this line
	# meant the suite silently stopped covering it. `tests/` is scanned
	# recursively, and `tests/conftest.py` puts `src/` on the path so this
	# works the same way under bare `pytest` or an IDE runner.
	"{{PY}}" -m pytest -q tests

# Rebuild the deterministic standalone distribution and manifest.
#
# The CLI and the console have SEPARATE builders on purpose: the surest way to
# keep the released CLI byte-frozen is for the code that could change it never
# to run when the console is rebuilt.
build:
	#!/usr/bin/env bash
	set -euo pipefail
	[[ -x "{{PY}}" ]] || { echo "error: venv missing; run 'just venv' first" >&2; exit 1; }
	"{{PY}}" tools/build_zipapp.py

# Rebuild the console (baton-tui) distribution and its manifest.
build-tui:
	#!/usr/bin/env bash
	set -euo pipefail
	[[ -x "{{PY}}" ]] || { echo "error: venv missing; run 'just venv' first" >&2; exit 1; }
	"{{PY}}" tools/build_tui.py
