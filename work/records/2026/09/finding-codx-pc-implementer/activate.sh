#!/usr/bin/env bash
set -euo pipefail
python3 /home/sl/src/baton/work/records/2026/09/finding-codx-pc-implementer/install.py
/home/sl/opt/baton/v11/0650c61/bin/baton --config /home/sl/baton-v11.14aecfb/baton.json --participant baton.slaw regen
python3 /home/sl/src/baton/tools/infra.py start /home/sl/baton-v11.14aecfb/codx-pc
python3 /home/sl/src/baton/tools/infra.py status /home/sl/baton-v11.14aecfb/codx-pc
