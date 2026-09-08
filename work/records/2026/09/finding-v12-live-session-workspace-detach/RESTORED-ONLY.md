# Restored-session-only runnable candidate — W106673

Prepared by baton.tuner, claim 110487, under owner M110484 and independent
diagnostic sign-off review-2026-09-07T13-08-30Z.md. This package is ready for
independent source/invocation review, then separate baton.ops execution approval.
No live run occurred during preparation.

The owner selected restoration-only evidence. The accepted retained actual-Claude
process/session/workspace correction and its 11.936325138-second observation
remain separate. This run never executes that retained arm, combines its timing
with a new result, or claims a controlled speedup/matched comparison. The earlier
restored-first failure cause remains unknown.

## Exact candidate and invocation

`evidence/live_controller_restore.py` and `evidence/live_supervisor_restore.py`
are separate files derived from the signed-off diagnostic sources. The frozen
manifest is `evidence/restore-only-manifest.json`. All 108 preceding bound inputs,
including nine accepted runtime exports, remain unchanged. New evidence paths
are claim-specific and exclusively created; this does not recover or conceal
the older unbound reviewer-output loss disclosed in FINDING.md.

Offline audit and checks:

```sh
/usr/bin/python3 -B /home/sl/src/baton/work/records/2026/09/finding-v12-live-session-workspace-detach/evidence/live_controller_restore.py --audit
/usr/bin/python3 -B /home/sl/src/baton/work/records/2026/09/finding-v12-live-session-workspace-detach/evidence/test_restored_only.py
```

Proposed single operator invocation, only after independent review and separate
exact execution approval:

```sh
sudo -- /usr/bin/env -i PATH=/usr/bin:/bin /usr/bin/python3 -B /home/sl/src/baton/work/records/2026/09/finding-v12-live-session-workspace-detach/evidence/live_controller_restore.py --run
```

No arbitrary inputs, existing-session path, image/model substitute, build/pull,
automatic retry or retained-arm selection is exposed. This is a newly constructed
restoration experiment, not reuse of the protected failed-run session.

## Two-step experiment and bounded authority

1. Create only `restored-first`, with a fresh private workspace/session and a
   fresh UUID. Give the unchanged initial prompt and private memory token. Observe
   the actual CLI/session identity and successful first turn. Confirm exact
   container shutdown, consume its shutdown receipt, and verify the initial
   fixed artifact bytes before any replacement is constructed.
2. After the unchanged five-second review delay, create only `restored-second`
   with the same workspace and private session directory. Request exactly
   `--resume <first actual session UUID>`. Give the unchanged correction, which
   does not repeat the remembered token. Require a different process, the same
   actual session/workspace, correct solution bytes and remembered token. Consume
   only an ordinary-revocation receipt before reading correction artifacts, then
   confirm final shutdown and normal credential teardown.

The first verified checkpoint is retained even if replacement initialization or
correction fails. No first-turn/stop/initial-verifier failure permits replacement.
Both host and supervisor enforce at most one user turn per container. There are
at most two containers and two user turns, each at most 180 seconds. The work
cutoff is 420 seconds; 180 seconds are reserved for ending within a 600-second
runtime ceiling. Result/export flushing follows ending as previously reviewed.
These are narrower ceilings, not a guarantee every maximum-duration turn will
fit alongside setup and review overhead. Uncertain ending still retains delivery.

Image remains
`sha256:979f11d53433f2930d69b70d81e265332547895cbd674e3e8b190cafb236243f`.
CLI must report 2.1.247; configured model is `claude-fable-5[1m]`, with actual
validated stream model `claude-fable-5`. The new supervisor preserves all CLI argv
bytes and options: first process uses `--session-id`, replacement uses `--resume`.
Only its allowed user-turn count narrows to one for both processes.

Each container retains UID/GID65532, dropped capabilities, no-new-privileges,
read-only root, default seccomp, 64 PIDs, 2 GiB memory, one CPU and 64 MiB /tmp.
The same four reviewed bind targets hold workspace, private session, read-only
supervisor and read-only credential slot. The new supervisor's source bytes are
staged at the same target; no new mount is introduced. Ordinary default bridge
outbound is resolved/pinned once; no published ports or provider-only firewall
claim. Root namespace authority stays confined to the accepted ordinary mount
helper. Existing source/group/private-delivery APIs and teardown rules remain
unchanged; real source contents are never manually copied, hashed or exported.

`--max-turns 8` and `--max-budget-usd 1` remain per CLI invocation. This two-process
scope has a nominal USD2 proposal, **not a verified hard billing/quota cap**.
Actual restoration, future provider behavior, internal cache/context cost and
production adoption remain unproved until separately reviewed evidence exists.

## Evidence and acceptance

Closed arm/operation/refusal and host/provider intent/write/result diagnostics
from LIVE-DIAGNOSTICS.md remain intact. Missing observations never prove absence
of dispatch or side effects. All existing process/session/mount/receipt checks,
exact bounded file verifier and partial-setup accounting remain in force.

Success is `restored-only-passed`, with `experiment=restored-only-separate-run`,
`matched_comparison=false`, one `arms.restored` record, and
`restoration_timings`. There is no retained row, pair evaluator, comparison ratio
or original matched-pair timing. The independent restoration acceptance function
requires both artifact verifications, both receipt checks, old and final confirmed
shutdown, original actual session/resume equality, unchanged workspace, a new
process, exact runtime identity and ordered monotonic timestamps.

Reported intervals are first-turn completion to safely verified correction,
review readiness, correction response and final revocation/verification. Existing
events separately time initial startup, old stop, replacement initialization and
final detach. A restored initialization observation alone does not prove useful
restoration; the remembered-token correction is required.

The first printed /tmp path retains private fixture resources; the second is the
UID1000-owned closed evidence export. Export remains package/network/arms/result/
setup JSON and the two restored event/gate pairs, with hashes in PROVENANCE.json.
It excludes credentials/source registry, private setup paths, session transcripts,
workspace bytes, fixture DB and runtime snapshot. Stopped containers and ordinary
private files remain; only existing normal credential teardown removes sensitive
delivery files after confirmed ending. No stronger cleanup is introduced.

Twenty-one offline checks include the 16 unchanged diagnostic assertions against
these sources and five restoration tests. The orchestration tests use actual
fixture gates and fixed-byte verification with simulated processes: they prove
the sequence/guards, not live restoration. Negative cases reject premature
replacement, failed/incorrect initial work, lost identity/custody/clock proof and
extra turns. Independent review precedes the proposed operator execution; the
owner's scope selection alone is not execution approval.
