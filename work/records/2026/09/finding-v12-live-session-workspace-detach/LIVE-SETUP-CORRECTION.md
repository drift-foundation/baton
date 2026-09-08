# Live setup correction candidate — W106673

Prepared by baton.tuner under claim 107956, 2026-09-07. Independent review and
separate operator disposition are required before executing this candidate.
The previously approved controller, manifest, supervisor and test files remain
unchanged. No automatic retry or new credential/cleanup authority is requested.

## Finding and evidence

The operator export at `/tmp/baton-w106673-live-export-dzna6j98` contains only
package/network/result projections. Their three hashes match its PROVENANCE.json.
The original protected root was not inspected. The recorded `execution-refused`
does not identify the original exception or establish partial-constructor cleanup.

An ordinary-user reproduction of the exact reviewed snapshot, under clean
`PATH=/usr/bin:/bin` environment and `/usr/bin/python3 -B`, fails during credential
API imports with `FileNotFoundError`, errno 2, for the fixed worker-control schema
asset. `evidence/live-setup-reproduction.json` records the safe observation and
retained reproduction root. No credential constructor or source reader ran.

The reviewed manifest/snapshot included only Python sources. The imported
`contracts/frozen.py` immediately reads two adjacent JSON assets, so that snapshot
cannot load the credential APIs. This is a confirmed packaging defect and the
inferred cause consistent with the historical setup failure; the old flattened
export cannot independently confirm its traceback. The old tests loaded APIs
from the checkout, where the omitted data existed.

## Bounded candidate

`evidence/live_controller_setup.py` is a separate candidate derived from the
unchanged reviewed controller. `evidence/live-setup-manifest.json` binds the
candidate, all previous 80 inputs, and both exact schema assets:

- `v12/python/src/baton_v12/contracts/schema/worker-control-1.0.schema.json`
- `v12/python/src/baton_v12/contracts/schema/agent-session-1.0.schema.json`

The existing snapshot copier includes their hash-checked bytes. No checkout
fallback, replacement schema, dependency installation or production edit exists.
A regression imports the corrected private snapshot in a fresh system-Python
subprocess with user site packages disabled; imports succeed before any source
reader construction. This proves local package completeness, not privileged or
credential-bearing live execution.

Setup now records fixed stages before operations. Failures export only a closed
exception-kind label and bounded errno, never exception messages, paths, custom
class names, stack traces, credentials or arbitrary provider output. The existing
fixed export adds only `setup.json`.

The credential owner is assigned before fallible preparation. Allocation intent
and completed resource kinds survive partial construction. Generated paths are
recorded separately in root-private `setup-private.json`, excluded from export.
An attempted allocation followed by incomplete preparation makes
`cleanup_confirmed=false`, even when no fixture was created. A received fixture
store is closed; a close failure is a separate safe ending diagnostic and cannot
replace the primary failure or claim successful cleanup. A failure before any
credential-resource attempt can be explicitly accounted for.

This correction introduces no orphan deletion or expanded cleanup. Existing
normal credential teardown after confirmed container ending remains unchanged;
incomplete setup resources are retained for exact operator inspection. Ordinary
files/session state remain under the previously reviewed retention policy.

All process/session/mount gates, supervisor argv, real-source selection/delivery,
one-pair/four-turn ordering, fixed image/model, bridge egress and 900-second
runtime budget remain as described in LIVE-PACKAGE.md. The six live options,
actual model/session/restore behavior, useful-correction latency and hard billing
cap are still unverified. The prior one-run approval was consumed by the failed
invocation; it is not authority to execute this replacement.

## Review and operations

Offline verification:

```sh
/usr/bin/python3 -B /home/sl/src/baton/work/records/2026/09/finding-v12-live-session-workspace-detach/evidence/live_controller_setup.py --audit
/usr/bin/python3 -B /home/sl/src/baton/work/records/2026/09/finding-v12-live-session-workspace-detach/evidence/test_live_setup.py
```

The 28 checks comprise all 19 existing assertions rerun unchanged against the
candidate and nine new setup regressions. They include the actual snapshot
import, actual prepare failure at store-open, constructor intent persistence,
received-store closure, close failure, closed diagnostics/export, and the full
outer run reporting partial setup with an empty fixture list. Artificial-source
API tests remain offline; real source bytes are never read.

Candidate operator invocation, only if independently reviewed and separately
approved by baton.ops:

```sh
sudo -- /usr/bin/env -i PATH=/usr/bin:/bin /usr/bin/python3 -B /home/sl/src/baton/work/records/2026/09/finding-v12-live-session-workspace-detach/evidence/live_controller_setup.py --run
```

The original operator command and its evidence are preserved as history. Review
the candidate delta in `evidence/live-setup.patch`, input/export/preservation
audit, tests and manifest, then return to baton.ops. No managed live invocation
or repetition of the accepted deterministic/idle-transport proofs is needed.
