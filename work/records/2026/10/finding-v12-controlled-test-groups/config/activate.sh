#!/usr/bin/env bash
# SUPERSEDED 2026-10-29: owner selected arrangement B (owner-held claim at baton.decide).
# Retained as record only. Refuses to run.
echo "superseded by arrangement B; see FINDING.md" >&2; exit 1
# W384870 — owner-only: install and accept generation 15 (adds baton.k, role impl).
# Starts no service. Managed services stay stopped.
set -euo pipefail
python3 /home/sl/src/baton/work/records/2026/10/finding-v12-controlled-test-groups/config/install.py
/home/sl/opt/baton/v11/0650c61/bin/baton --config /home/sl/baton-v11.14aecfb/baton.json --participant baton.slaw regen
/home/sl/opt/baton/v11/0650c61/bin/baton --config /home/sl/baton-v11.14aecfb/baton.json --participant baton.k instructions role=impl
