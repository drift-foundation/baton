# W32577 cleanup supervisor correction — awaiting independent review

baton.tuner claim163313 consumed pass163305, review-2026-09-13T19-57-38Z.md,
current FINDING/PLAN/PROGRESS, READINESS-163241.md and OPS-READINESS-163284.md.
This implements the selected deterministic fixture correction. Real engine180s
remains unactivated; no Docker/API, image, installation, live-model/provider or
real-child execution was performed in this claim.

**Complete candidate:** candidate-163313.json, SHA256
f96cf65d7c201e0a7dda2f69d73fab0b7418fb9cd8da73144368c266cef9bcc7. Full11-file snapshots under candidate-163313/.
The nine-file candidate163184 is the predecessor, SHA256 e006a1e264463454be3aedb3355905dea7d5ceff09b139170f2d49f286c09a10.
**Exact three-file delta:** correction-163313.patch, SHA256
0ca2f2202daa1627ce782d018c5870c19ffd8127c79a0d04bdcbe4d18e54b8aa.

| Changed path | SHA256 |
| --- | --- |
| v12/python/tests/manager/test_runtime_deadline_engine.py | 6a7156689506266c948572a3e7de0f4fc161b12beed55c0aaf9ffdcf8affad1d |
| v12/python/tests/manager/test_runtime_deadline_engine_budget.py | 96e7c73105a312d6a4d5ab6a0e7c0df808839f0f832e5db46356af5fc48573e6 |
| work/records/2026/08/finding-v12-local-oci-negative-race-endings/findings/finding-v12-runtime-deadline-cleanup/engine-gate.py | 4fc8bd4698b34f090f47e26822daaaa16682ce80a24b4ab81c72fd7566cb30da |

The eight other predecessor candidate files remain unchanged. All four original
protected hashes plus shared test_lifecycle_composition.py and DEPLOYMENT.md
still match. The entire existing engine acceptance method has an identical AST
to candidate163184; its assertions, scenario and ordering were preserved.
Only the explicitly scheduled existing engine fixture, new deterministic test
module and dossier supervisor changed. Existing test-change authority applies.

## Supervisor and fixture behavior

The prepared engine test now requires BATON_W32577_GATE_DIR from engine-gate.py;
its direct selector alone refuses before Docker. The supervisor launches one
owned test process session, keeps its output as body.log and survives child
failure/timeout. The single absolute180s design allocates setup/body120s,
stop/reap5s, exact cleanup50s, accounting5s. Cleanup may start early; its own50s
and the absolute175s end both apply. No unused slot extends the absolute total.
Child commands and parent cleanup commands persist expected/margin/timeout
records before launching, then recheck allowance after durable guard I/O.
Actual child/phase results and elapsed times are retained in the run directory.

Each runtime, custodian and direct sibling create/run registers its exact name
and run identity in an fsynced inventory file before crossing Docker. The same
boundary adds a unique gate ownership label. Supervisor cleanup reads only this
inventory, inspects the exact name, requires the matching label/name and removes
the inspected immutable container ID. It then verifies exact absence. A foreign
same-name container or replacement is never removed; there is no global listing,
broad name filter, image mutation or unrelated process termination.

The parent terminates/kills only its owned subprocess session and reaps it within
the shared5s slot. If it cannot reap that child, it fails and retains the inventory
rather than racing a still-running creator. Every cleanup child draws from one
remaining reserve, not a fresh30s allowance per resource. Body errors/status and
cleanup failures coexist in result.json. Exact unresolved names remain on disk.
A pending/failed create reply plus current absence remains unresolved; one absent
observation cannot settle possible late creation. An observed owned container
can be removed and positively checked. Missing/ambiguous daemon evidence fails.

Fixture-local directories are intentionally retained under the per-run fixtures/
directory as durable evidence, including partial output and the closed control
store. The child closes its store but defers inherited directory/provider teardown
callbacks so they cannot race the surviving parent's later container cleanup.
fixture-retained.json lists the root and deferred callback names. This fixture
uses synthetic credentials; no live provider is contacted. Normal deadline
acceptance still independently asserts both provider endings and retained custody.
No filesystem-evidence deletion is part of this supervisor.

## Deterministic evidence and next gate

Final **21 fake clock/process/Docker cases pass**, verification-162766-25.log.
They cover runtime/custodian/direct sibling registration before creation, normal
cleanup, timeout, TERM resistance/KILL, unreapable child, uncertain and interrupted
create, body plus cleanup failure, reserve exhaustion, slow guard persistence,
exact foreign/name-replacement protection, ambiguous absence, corrupt inventory,
phase totals, final-accounting overrun and deferred fixture filesystem cleanup.
The load_tests hook selects only these cases; importing the fixture does not
select its real-engine test. No actual subprocess factory or Docker runner runs
in these regressions. Logs23/24 retain earlier passing16/19-case selections.
The accepted deadline matrix was not rerun because its source/tests did not change.

Author cumulative **67.54953842499526/120s**, remaining **52.45046157500474s**, all25 children
retained in verification-162766.json. The earlier three readiness probes remain
charged within this same total. Reviewer unchanged4.757895970993559/60s,
remaining55.24210402900644s. Qualified Python3.13.7/jsonschema4.19.2 evidence only;
required4.26.0 verification remains outstanding. No budget reset/transfer.

After independent harness review and separately activated execution scope, the
entrypoint is this dossier engine-gate.py with --python ABSOLUTE_PINNED_INTERPRETER
and --run-dir ABSOLUTE_FRESH_RUN_DIRECTORY, under an executor that can reach the
selected Docker daemon. BATON_W32577_IMAGE_DIGEST must already name the independently
reviewed preloaded worker image; the unchanged fixture checks dependency, immutable
image ID and exact reference-worker entrypoint. The supervisor supplies the exact
source selector, PYTHONPATH and durable run environment. All three environment
operands remain unresolved in this claim; this prepared command is not execution
authority. Preserve the supervisor/run evidence if it is itself externally stopped.

M163303 to baton.ops remains pending at the latest T32577 read, snapshot163361;
no new response after that request. It owns denied tuner Docker access, existing
pinned interpreter/provisioning selection and immutable worker-image provenance.
Do not repeat the denied Docker boundary. W161230 retains DEPLOYMENT under
M163260/M163265 pending its two corrections and explicit fresh-hash handback;
DEPLOYMENT-DEADLINE-DRAFT-162766.md remains untouched. Return the complete candidate
to baton.feat. W32577/W32382/W33755 remain open pending actual final gates.
