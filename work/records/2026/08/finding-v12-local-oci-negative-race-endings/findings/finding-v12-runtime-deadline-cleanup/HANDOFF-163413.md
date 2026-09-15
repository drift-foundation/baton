# W32577 supervisor interruption correction — awaiting independent review

baton.tuner claim163413 consumed pass163410, review-2026-09-13T20-14-59Z.md,
probe-163385.py and current FINDING/PLAN/PROGRESS. This addresses all three P2
fixture findings within the selected scope. It changes no deadline product rule.

Complete11-file candidate: candidate-163413.json, SHA256
ecd8e311806a2b781f682a75adf396c888c31411bf931030b3c8ba1fad82b896; snapshots under candidate-163413/.
Predecessor candidate-163313.json SHA256 f96cf65d7c201e0a7dda2f69d73fab0b7418fb9cd8da73144368c266cef9bcc7 remains preserved.
Exact two-file delta: correction-163413.patch, SHA256
f248a89107aee5dcd37dd686691d5e17f5c57ff113b4275d8b7e11669b5136f6.

| Changed path | SHA256 |
| --- | --- |
| v12/python/tests/manager/test_runtime_deadline_engine_budget.py | 52ead756e9b964e92af21d81e06ca137053de652117202045b0c01a6aeb1f6cc |
| work/records/2026/08/finding-v12-local-oci-negative-race-endings/findings/finding-v12-runtime-deadline-cleanup/engine-gate.py | a729a7ce7b086444d54a9b73f4ea375c1ee9f4f637a3953033fa23251d244bc2 |

The other nine candidate paths and all six protected/shared hashes match the
predecessor. In particular the existing engine fixture is byte-identical; its
acceptance method and retained-root/provider behavior remain independently
reviewed scope. Only the dossier supervisor and its deterministic budget tests
changed. Existing test-change authority covers the scheduled corrections.

## Entire owned group is settled before cleanup

OwnedProcess.wait uses waitid with WNOWAIT to observe the Popen leader without
reaping it. The waitable leader, including an exited zombie, retains its PID/PGID
while the supervisor remains the sole waiter. Both normal completion and timeout
enter the shared5s settlement slot. The supervisor sends TERM and then KILL to
that owned group, checks /proc group/session membership for live members and only
then reaps/releases the leader. Leader exit alone never enables cleanup.

Signals require retained wait ownership; lost/external reaping or use after
release refuses before killpg. The fixture starts its own session and Docker CLI
children inherit that group; this is the owned host execution boundary. Container
processes belong to Docker and are handled by the exact registered cleanup path.
No unrelated group is signalled. Membership read failure, identity mismatch,
remaining live members or insufficient settlement time fails and retains exact
inventory without starting a cleanup sweep that could race a creator.

## Creation intent survives diagnostic interruption

Durable records now write/fsync a fresh staging file and atomically publish it.
New immutable records use exclusive hard-link publication; diagnostic replacement
uses replace followed by parent-directory fsync. Interruption preserves either the
previous complete record or a retained unpublished staging file. Unpublished
inventory staging files cannot have authorized a create and are not names.

Each create also has an immutable child-create-intent record binding name, run
identity and diagnostic locator, published before the Docker call. Diagnostic
completion never rewrites that intent. Missing/corrupt/incomplete diagnostics
conservatively preserve creation uncertainty and diagnostic errors. They do not
prevent exact-name/label/immutable-ID inspection and removal of known owned
resources. If an uncertain name is currently absent, it remains unresolved;
positive owned identity can still be removed and its absence checked. Diagnostic
errors are retained alongside resolved/unresolved names and prevent gate success.

## Final evidence completion governs exit

A file cannot include the future duration of its own final write. result.json
therefore always has ok=false and status=incomplete-awaiting-supervisor-exit;
candidate_ok describes body/cleanup checks only. No persisted artifact by itself
is a completion receipt. Both durable result writes finish before supervise
measures actual elapsed, computes its returned ok and checks the5s accounting
and absolute180s boundaries. Write failure/overrun cannot return success; any
remaining file is explicitly incomplete.

The CLI prints only a provisional summary, with elapsed_before_stdout clearly
labelled, flushes it, then rechecks the accounting deadline and computes exit.
The **supervisor exit status after completed evidence and stdout flush is the
completion authority**. Exit0 plus the bound evidence is required; provisional
files or stdout alone never mean acceptance. An output error or late flush yields
failure. The returned in-memory elapsed/ok is updated after flush; the later gate
executor must retain the actual process exit and cumulative duration in its own
execution ledger. This avoids an endlessly self-referential final-write receipt.

The selected120s body/5s owned settlement/50s exact cleanup/5s accounting design
and all absolute deadlines remain. Engine180s is still unactivated.

## Focused evidence and remaining gates

Final **33 deterministic cases pass**, verification-162766-28.log. Added
regressions cover leader-exits/descendant-survives with actual OwnedProcess and
fake Popen/waitid/killpg boundaries, no remaining group-settlement time, lost wait
ownership/recycled-group refusal, fake /proc live/zombie/foreign/session cases,
partial diagnostics with positive cleanup, absent uncertainty, interruption of
atomic diagnostic replacement, final/last evidence write overrun/failure and
stdout flush overrun. All earlier runtime/custodian/sibling, reserve and foreign
resource cases remain. No real process-group operation, Docker/API call, engine,
image mutation, installation or model execution was performed.

Log26 retains one harness-only failed case: a new group_alive fake supplied one
answer although settlement and release both check it. Corrected to a repeatable
false answer; log27 passed31 cases, followed by final33 in log28. All costs remain
charged. Existing assertions changed only to require group settlement even after
normal leader exit and to make persisted output explicitly provisional rather
than falsely authoritative. The real engine acceptance assertions are unchanged.

Author cumulative **68.4909876419988/120s**, remaining **51.5090123580012s**, all28 ledger
children retained in verification-162766.json. Reviewer remains
**4.971617716990295/60s**, remaining **55.028382283009705s**, latest
review-ledger-163385.json. No reset/transfer or new bank. Evidence still uses
Python3.13.7/jsonschema4.19.2; required4.26.0 remains pending. The accepted
product/deadline/no-start matrices were not rerun for this isolated harness change.

Latest T32577 read snapshot163454 had no messages after ops requestM163303.
Ops still owes the permitted Docker boundary, pinned interpreter and exact
preloaded current worker image/provenance. Do not retry the denied boundary.
W161230 retains DEPLOYMENT under M163260/M163265 until its two corrections and
fresh-hash handback. Return this exact candidate for independent review; required
pinned verification, real-engine execution, documentation and all parents remain
open. The prepared gate invocation remains in HANDOFF-163313.md and is not
execution authority.
