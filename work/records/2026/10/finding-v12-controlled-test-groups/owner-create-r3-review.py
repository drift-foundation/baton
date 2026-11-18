#!/usr/bin/env python3
"""Owner runs this: creates claimable read-only codexpc review; no tests or Git."""
from pathlib import Path
import subprocess
p = Path(__file__).resolve().parent
body = (p / 'CODEXPC-R3-REVIEW-ASSIGNMENT.md').read_text()
raise SystemExit(subprocess.call(['/home/sl/opt/baton/v11/0650c61/bin/baton', '--config', '/home/sl/baton-v11.14aecfb/baton.json', '--participant', 'baton.slaw', 'create', 'team=baton', 'kind=codx', 'title=V12: independent review of shutdown signal-count failure', 'origin=decomposition', 'classification=suspected-defect', 'parent=W384870', 'priority=high', 'body='+body, 'op-id=w384870-r3-signal-review-owner']))
