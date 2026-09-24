# Current action: owner disposition after bounded correction review

2026-09-24T16:25:54Z, baton.rvpc: bounded declaration correction ACCEPTED in
[review](review-2026-09-24T16-25-54Z.md), with 41 tests independently passing
in 0.552s, committed intake and executed retention gates. This supersedes the
correction-pending status below. Return to owner; D2 remains unselected and
still requires its W257624 and fresh-packet prerequisites. No live run selected.

2026-09-24T16:14:50Z, baton.rvpc: owner258136 selected the remaining evidence;
author258208 delivered real-byte/envelope tests. Independent
[review](review-2026-09-24T16-14-50Z.md) passes 32 tests in 0.306s and accepts
that incremental proof. Full correction still awaits committed freeze/intake
receipts and execution of the implementation rejection check already selected
by258136. This supersedes the earlier pending-status description below.
Return to owner for scheduling; D2 remains unselected.

2026-09-24T15:33:06Z, baton.rvpc: owner257834 selected the output-declaration
correction; author257947 delivered it. Independent
[review](review-2026-09-24T15-33-06Z.md) passes 19 tests in 0.185s but leaves
acceptance pending focused downstream result/intake and missing-review-output
evidence. This supersedes the current-action status below. Return to owner;
no automatic correction cycle, D2 or recovery expansion is selected.

2026-09-24T15:06:15Z, baton.rvpc: D1 independently accepted in
[review-2026-09-24T15-06-15Z.md](review-2026-09-24T15-06-15Z.md).
Four tests passed in 0.022s; all 30 recorded hashes matched. This supersedes
the awaiting-review status below. Return to owner before separately selecting
an owned correction. D2 prerequisites remain; no successor execution selected.

D1 executed under claim257715; DIAGNOSIS.md, EVIDENCE.json and
test_startup_boundary.py await independent review, then owner selection.
Four deterministic tests passed (0.022s). No correction or D2 executed.

Owner selected D1 executor baton.tuner on 2026-09-24 after implpc's usage-limit
refusal; independent reviewer baton.rvpc. D1 can proceed alongside R1 because
its only writes are new evidence/docs/tests in this dossier. D2 waits on
accepted D1 and W257624; do not block D1 on machinery it does not use.

## D1 — an evidence-bound original fault diagnosis

One outcome: identify the first failing boundary in the **executed image**, or
name the exact unavailable diagnostic needed to distinguish the remaining
hypotheses. Input: parent DIAGNOSIS-252472.md (with corrections), retained
outcome and launch/exchange artifacts at
/home/sl/baton-instances/two-jobs-251156, actual image/build provenance, and
source corresponding to that image. Product, historical dossier and deployment
are read-only. New owned paths: DIAGNOSIS.md, EVIDENCE.json and
test_startup_boundary.py here. Do not repair source as part of diagnosis.

First executable evidence command after assignment (file-only; no engine,
provider, credentials or store API):

```sh
python3 -B - <<'PY'
import json
from pathlib import Path
p = Path('/home/sl/baton-instances/two-jobs-251156/run/outcome.json')
if not p.is_file() or p.stat().st_size > 8 * 1024 * 1024:
    raise SystemExit('missing or oversized retained outcome; preserve and report')
d = json.loads(p.read_text())
print(json.dumps({k: d.get(k) for k in ('state', 'stopped', 'admitted_attempts', 'outstanding_cleanup')}, indent=2))
PY
```

Then map those identities to retained describe/work/terminal and available log
capture-state artifacts. Record exact executed image digest and adapter source
mapping, where the failing exception is reported or lost, and evidence for each
remaining hypothesis. No credentials in evidence. A missing source/image map
or absent stderr is an operational finding, not permission to guess or run it.
Existing retained image inspection may be read-only if separately allowed;
no image rebuild, container start or provider call is part of this stage.

Planned deterministic acceptance command, once this stage supplies its module:

```sh
cd /home/sl/src/baton
PYTHONPATH="$PWD/v12/python/src:$PWD/v12/python:$PWD/work/records/2026/09/finding-v12-startup-failure-fresh-packet" timeout --signal=TERM --kill-after=5s 30s /home/sl/.local/state/baton-v12-venv/bin/python -B -W error::ResourceWarning -m unittest test_startup_boundary
```

The reproducer uses an isolated fake child/provider at the actual adapter
boundary and source matched to the image, with a negative control. Retain the
original fault signature and causal evidence; label simulation. If bytes or
logs are insufficient, finish with the precise missing input and the smallest
next diagnostic, not a claimed cause. Stop for independent assessment of that
result. Any product correction is a bounded next selection with an exact path
owner, not a silent expansion of D1. Do not claim D1 diagnosis-complete if it
only establishes missing diagnostics.

## D2 — one reviewed fresh packet with literal operator commands

Prerequisites: D1's diagnosed fault is corrected and independently accepted
(or its missing-input question is resolved), and W257624's R1–R5 are accepted.
Proposed serial packet author tuner; shared composer/product corrections stay
with Claude absent explicit handoff. New files here: OPERATOR.md, INPUTS.json,
CANDIDATE.json, test_fresh_packet.py. Parent two_jobs.py, prepare_two_jobs.py,
verify_247941.py, two_job_supervisor.py are read-only inputs unless ownership
is expressly coordinated for an exact correction. Never copy a helper merely
to escape its owner or fork the supported interface.

Outcome: digest-bound successor snapshot/image/packet provenance and literal
bootstrap, preparation, start, status/log inspection, interruption/recovery and
readback commands pass against an isolated fixture. No command reuses a spent
run identity, root, grant or submission. Revalidate source **and executed cache**
boundary: -B prevents cache writes, not loads of old pyc. Preserve old snapshots.
Verify all input hashes/import origins before any fixture Authority effects,
root freshness including aliases, required directories, limits resolved by the
actual public reader, independent identities and output/cleanup locators.

```sh
cd /home/sl/src/baton
PYTHONPATH="$PWD/v12/python/src:$PWD/v12/python:$PWD/work/records/2026/09/finding-v12-startup-failure-fresh-packet" timeout --signal=TERM --kill-after=5s 120s /home/sl/.local/state/baton-v12-venv/bin/python -B -W error::ResourceWarning -m unittest test_fresh_packet
```

This module is a planned deliverable. Exercise the actual emitted argv, not an
equivalent hand-built call, over fake provider/engine and fresh disposable stores.
Preconfigure authorized disk-backed scratch outside source/snapshots; refuse
missing storage, no skipped checks. Record statuses, durations, bindings and
preserved old-root hashes. Actual image build or export needs its own selected
execution boundary; absent new artifact evidence means packet pending, not
ready. Do not run deployment commands here. Stop with independently accepted
packet and exact remaining owner selections for W247941's parallel proof.
