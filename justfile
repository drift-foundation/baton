set shell := ["bash", "-lc"]
set quiet

VENV := ".venv"
PY := VENV + "/bin/python3"

default: test-v11

# Start only the Codex backend; low-level development recipe, not the complete Baton integration.
codex-app-server:
	#!/usr/bin/env bash
	set -euo pipefail
	command -v codex >/dev/null 2>&1 || { echo "error: codex is not on PATH" >&2; exit 1; }
	exec codex app-server --listen ws://127.0.0.1:4500

# Own the complete backend set declared by MAILBOX/infra.json. These recipes
# infer nothing from the checkout, current release, or running processes.
start MAILBOX:
	python3 tools/infra.py start "{{MAILBOX}}"

stop MAILBOX:
	python3 tools/infra.py stop "{{MAILBOX}}"

status MAILBOX:
	python3 tools/infra.py status "{{MAILBOX}}"

# Create the repository-local development environment. Baton itself remains
# stdlib-only; this installs test tooling only.
venv:
	#!/usr/bin/env bash
	set -euo pipefail
	if [[ ! -x "{{PY}}" ]]; then
		echo "[venv] creating ./{{VENV}} ..."
		python3 -m venv "{{VENV}}"
	fi
	if "{{PY}}" -c 'import pytest, xdist; assert pytest.__version__ == "9.0.1"; assert xdist.__version__ == "3.8.0"' >/dev/null 2>&1; then
		echo "[venv] ./{{VENV}} is ready."
		exit 0
	fi
	"{{PY}}" -m pip install -r tools/requirements-dev.txt
	echo "[venv] ready."
# THE gate. Runs the complete v11 authority/JSON/CLI/console suite directly
# against the checkout, then the external ACP bridge's own acceptance.
# Verbose output names every test. Ordinary tests run through xdist with one
# worker per available CPU; tests that manage their own process pools then run
# serially without xdist. This includes the adversarial soak.
#
# It deliberately builds nothing. Publishing is `just deploy-v11 DESTINATION`,
# which writes one NEW immutable distribution directory and is a separate
# operator decision — the gate proves the source, the deploy produces the
# artifact, and neither performs the other.
test-v11: && test-acp
	#!/usr/bin/env bash
	set -euo pipefail
	[[ -x "{{PY}}" ]] || { echo "error: venv missing; run 'just venv' first" >&2; exit 1; }
	"{{PY}}" -c 'import pytest, xdist' >/dev/null 2>&1 || { echo "error: pytest/xdist missing; run 'just venv' first" >&2; exit 1; }
	"{{PY}}" -m pytest -v -n "$(nproc)" -m "not serial" tests/work
	"{{PY}}" -m pytest -v -m serial tests/work

# W163 R5: the ACP readiness client is a v11 product — its acceptance
# runs inside the ONE operator-facing v11 gate above. The pinned SDK
# installs deterministically from the committed lockfile when absent.
test-acp:
	#!/usr/bin/env bash
	set -euo pipefail
	cd tools/acp-baton-bridge
	command -v node >/dev/null || { echo "error: node (>=20) is required for the ACP gate" >&2; exit 1; }
	[[ -d node_modules/@agentclientprotocol/sdk ]] || npm ci --no-fund --no-audit
	npm test
# Publish the v11 `baton-work` product into one NEW explicit immutable
# distribution directory. `tools/deploy_work.py` is the packaging mechanism;
# this recipe is the operator-facing entry point. It does not initialize or
# activate a coordination home and does not touch v10.
deploy-v11 DESTINATION:
	#!/usr/bin/env bash
	set -euo pipefail
	python3 tools/deploy_work.py "{{DESTINATION}}"
