set shell := ["bash", "-lc"]
set quiet

VENV := ".venv"
PY := VENV + "/bin/python3"

default: test

# Wire every configured Codex session to its Baton participant in one supervised foreground stack.
codex-baton CONFIG:
	#!/usr/bin/env bash
	set -euo pipefail
	command -v node >/dev/null 2>&1 || { echo "error: node is not on PATH" >&2; exit 1; }
	exec node tools/codex-event-bridge/src/stack.mjs --config "{{CONFIG}}"

# Start only the Codex backend; low-level development recipe, not the complete Baton integration.
codex-app-server:
	#!/usr/bin/env bash
	set -euo pipefail
	command -v codex >/dev/null 2>&1 || { echo "error: codex is not on PATH" >&2; exit 1; }
	exec codex app-server --listen ws://127.0.0.1:4500

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

# Run the complete reusable test suite AGAINST THE CANDIDATE `just build`
# prepared. Step two of three:
#
#     just build
#     just test
#     just deploy DESTINATION
#
# It does not build. An earlier version prepared the candidate itself when one
# was missing, which made the gate report on bytes it had just manufactured
# rather than on the bytes a human is about to publish. A missing candidate is
# a refusal naming the step that was skipped.
test:
	#!/usr/bin/env bash
	set -euo pipefail
	[[ -x "{{PY}}" ]] || { echo "error: venv missing; run 'just venv' first" >&2; exit 1; }
	# ONE refusal, before pytest starts, from the same locator the fixtures
	# use -- not a second hand-written list of artifacts that can drift from
	# it. It reads only; there is no path in it that builds anything.
	"{{PY}}" tests/candidate.py >/dev/null
	"{{PY}}" -c 'import pytest' >/dev/null 2>&1 || { echo "error: pytest missing; run 'just venv' first" >&2; exit 1; }
	# DISCOVERED, not enumerated. The list that used to live here was a
	# hand-maintained subset: adding a test file and forgetting this line
	# meant the suite silently stopped covering it. `tests/` is scanned
	# recursively, and `tests/conftest.py` puts `src/` on the path so this
	# works the same way under bare `pytest` or an IDE runner.
	"{{PY}}" -m pytest -q tests

# Run the complete focused Gate A authority/JSON/CLI suite directly against
# the checkout. Verbose output names every test. Ordinary tests run through
# xdist with one worker per available CPU; tests that manage their own process
# pools then run serially without xdist. This includes the adversarial soak,
# but deliberately does not build or certify release artifacts; `just build`
# then `just test` remains the full candidate gate.
test-v11:
	#!/usr/bin/env bash
	set -euo pipefail
	[[ -x "{{PY}}" ]] || { echo "error: venv missing; run 'just venv' first" >&2; exit 1; }
	"{{PY}}" -c 'import pytest, xdist' >/dev/null 2>&1 || { echo "error: pytest/xdist missing; run 'just venv' first" >&2; exit 1; }
	"{{PY}}" -m pytest -v -n "$(nproc)" -m "not serial" tests/work
	"{{PY}}" -m pytest -v -m serial tests/work

# Prepare the WHOLE release candidate under `build/`: both products, both
# manifests, and a snapshot of every Git-owned payload file, from one catalog,
# deterministically.
#
# IT DOES NOT TOUCH THE CHECKOUT. Installing a finished set over `bin/baton`
# and `bin/baton-tui` made every successful build a production cutover, since
# teams run the repository executables and the event bridge names one by
# absolute path. `build/` is disposable, ignored by Git, and safe to delete.
#
# ONE COMMAND, by ruling. `baton` and `baton-tui` are independently versioned
# but they are built from one catalog and embed one core, and the deployer
# refuses a set whose products disagree about either -- so two commands made
# that coherence something a human had to remember between them.
#
# THE CANDIDATE IS COMPLETE OR IT IS ABSENT. Everything is prepared beside
# `build/`, certified there, and published by renaming a directory -- so a
# failure at any point leaves the previous candidate whole or leaves nothing,
# and never a tree holding bytes from two builds. The per-product builders
# remain as internal mechanisms:
# `python3 tools/build_zipapp.py [outdir]` and `tools/build_tui.py [outdir]`
# still build one product into another distribution root.
build:
	#!/usr/bin/env bash
	set -euo pipefail
	[[ -x "{{PY}}" ]] || { echo "error: venv missing; run 'just venv' first" >&2; exit 1; }
	"{{PY}}" tools/build_release.py

# Install the certified candidate from `build/` into a destination OUTSIDE the
# repository, as immutable per-product exact releases:
#
#     DEST/app/baton-cli/<namespace>/vX.Y.Z/     one immutable release
#     DEST/app/baton-cli/<namespace>/latest      relative discovery alias
#
# It certifies the aggregate candidate exactly as before -- one core, one
# protocol, manifests attested against the bytes -- keeps the set digest as
# provenance, and reads payload bytes from the candidate and NOTHING ELSE, so
# what reaches the destination is what `just test` examined.
#
# Reinstalling the same candidate is idempotent: an identical exact release
# reports `already_installed` and is not rewritten. Any difference refuses,
# because distinct bytes are a distinct version.
#
# It never builds, never opens a mailbox, never edits consumer configuration
# and never executes what it installs.
deploy DESTINATION:
	#!/usr/bin/env bash
	set -euo pipefail
	python3 tools/deploy.py publish "{{DESTINATION}}"

# Publish the v11 `baton-work` product into one NEW explicit immutable
# distribution directory. `tools/deploy_work.py` is the packaging mechanism;
# this recipe is the operator-facing entry point. It does not initialize or
# activate a coordination home and does not touch v10.
deploy-v11 DESTINATION:
	#!/usr/bin/env bash
	set -euo pipefail
	python3 tools/deploy_work.py "{{DESTINATION}}"

# Point <generation>/latest at an exact release, after that release fully
# verifies. Rollback is this same command naming the previous release, which is
# still installed. SUPERSEDES `deploy-activate`: there is no global `current`.
deploy-alias GENERATION_DIR RELEASE:
	#!/usr/bin/env bash
	set -euo pipefail
	python3 tools/deploy.py alias "{{GENERATION_DIR}}" "{{RELEASE}}"

# Read what <generation>/latest names, and print the EXACT path to execute.
# A consumer resolves once at launch and runs that path: `latest` must never be
# the path a running zipapp holds open.
deploy-resolve GENERATION_DIR:
	#!/usr/bin/env bash
	set -euo pipefail
	python3 tools/deploy.py resolve "{{GENERATION_DIR}}"

# Generate the deployment-specific migration guide. Reads the deployment and
# the ACCEPTED config; writes one file; publishes nothing.
guide DESTINATION MAILBOX CONFIG OUTPUT:
	#!/usr/bin/env bash
	set -euo pipefail
	python3 tools/migration_guide.py "{{DESTINATION}}" --mailbox "{{MAILBOX}}" \
		--config "{{CONFIG}}" --output "{{OUTPUT}}"

# What publishing the guide WOULD do: the audience, what is already sent, and
# what remains. Sends nothing.
guide-plan GUIDE CONFIG RECEIPT PARTICIPANT:
	#!/usr/bin/env bash
	set -euo pipefail
	python3 tools/publish_guide.py "{{GUIDE}}" --config "{{CONFIG}}" \
		--receipt "{{RECEIPT}}" --participant "{{PARTICIPANT}}"

# PUBLISH the guide: one notice and one durable delivery per registered
# participant, the same bytes to both. A HUMAN GATE -- this sends messages to
# everybody. Resumable: re-running completes a partial publication, and a step
# that may have committed is never repeated without --resend-uncertain.
guide-publish GUIDE CONFIG RECEIPT PARTICIPANT *FLAGS:
	#!/usr/bin/env bash
	set -euo pipefail
	python3 tools/publish_guide.py "{{GUIDE}}" --config "{{CONFIG}}" \
		--receipt "{{RECEIPT}}" --participant "{{PARTICIPANT}}" --send {{FLAGS}}

# Re-hash one exact product release against its own record.
verify-release RELEASE_DIR:
	#!/usr/bin/env bash
	set -euo pipefail
	python3 tools/deploy.py verify-release "{{RELEASE_DIR}}"

# Re-hash a deployed set directory against its own record. Kept for sets
# published under the superseded `set-<digest>/` layout.
verify-deployment SET_DIR:
	#!/usr/bin/env bash
	set -euo pipefail
	python3 tools/deploy.py verify "{{SET_DIR}}"
