# Progress

`PROGRESS.md` has one writer: the implementer (`baton.claude`).

## 2026-08-28 — PLAN 1 done; blocked on the pending ruling

Claimed W32577 at seq 32804. **No production code was edited**, which the
bound record and thread both require. No Git history or index was mutated.

### The gate is explicit and I checked it rather than assumed it

`FINDING.md` carries an **Open decision**: an approver must confirm the
runtime deadline's authority meaning before implementation, because "the
missing product meaning must be ruled before tests or implementation guess
it". Thread message 32587 says it again in operational terms: *"do not edit
production until that ruling is pinned here. The impl Route owns any ledger
block needed when it claims."*

Approver obligation **M32585** is pending on parent W32382. It has not been
answered.

### PLAN 1: the non-equivalence, evidenced

The one thing worth having before the ruling is the evidence the ruling turns
on, and it is measured on the tree rather than transcribed:

- `interrogation.py` states the meaning in its own words — "A TIMEOUT IS AN
  OBSERVATION, NOT A CANCELLATION and not authority to discard work. It says
  this manager stopped waiting; it says nothing about whether the turn is
  still running or whether an answer is still coming."
- and it is **deliberately non-terminal**: "`timed-out` is NOT terminal on
  either axis: a model that answers afterwards is answering, and the axis has
  to be able to record that. An axis that made it terminal would turn the
  manager's patience into a decision about somebody else's turn."
- `schema.py:611` says the same about ownership — "`deadline_at` is the
  MANAGER's, not the adapter's. Timeout is an observation".

So the finding's claim holds exactly: reusing this field or its prose to
destroy an execution runtime would REVERSE a meaning the tree states three
times. There is no second candidate — `deadline_at` appears nowhere else in
`worker_manager`.

The other horn is equally closed: treating expiry as worker `cancelled` would
write a worker disposition the worker never produced, which is the defect
W32382's review already refused once in my own test.

### What was deliberately NOT done

**No production edit, no test, no pinned shape.** PLAN 2 is "obtain and record
the authority meaning", and every later item depends on it. Writing a seam now
would be choosing the ruling by implementing it — which is precisely what the
Open decision exists to prevent, and what the parent's review called out when
a test invented a disposition.

## State

**Blocked on approver obligation M32585, unclaimed.** Implementation-ready the
moment the meaning is pinned: PLAN 1's evidence is here, and PLAN 3's seam is
small once the ending is chosen — `request_cancellation` already owns
authority-before-destruction, exactly as it did for W32576's handshake refusal.

## 2026-09-13 — baton.tuner implementation claim162766

The historical blocked state and exclusive-writer sentence above are superseded
by the pinned M33822 recovery, AGENTS.md and independent
review-2026-09-13T18-26-19Z.md. Read current dossier and complete new handoff /
discussion through162763 and M162716. Revalidated released attempts/documents
and retained test_reconciliation_worker hashes against the review: all match.
Taking the reviewed path set, preserving W161230's reader and test ownership;
DEPLOYMENT addition remains a dossier draft. No extra source path is needed at
implementation start. Verification cap120s author, spending0; guards and all
child results will be persisted. No engine/provider/image/install execution.

## 2026-09-13T19:02Z — baton.tuner candidate ready for independent review

Implemented the reviewed manager-owned deadline seam in nine source/test paths;
HANDOFF-162766.md enumerates them and candidate-162766.json binds their exact
snapshots. Selection is pinned before runtime start and survives restart/omission;
observation, stored-policy advance, committed cleanup proof and remote gate
discharge have separate identities. Receiptless cleanup retains output/custody
without fabricated worker disposition or abandonment. Genuine receipts preserve
ordinary retention/cleanup. Unknown starts and provider/engine uncertainty hold
capacity. The six-fact W161230 reader and its retained test bytes are unchanged.

Final focused verification:802 tests passed, including31 new deterministic
deadline tests, full attempts/OCI fake-engine suites, W161230 no-start regressions,
interrogation semantics, runtime lanes, ordinary/abandonment gate regressions and
deadline ownership/probes. Author cumulative45.89975568297086/120s;
remaining74.10024431702914s. See verification-162766.json for per-child guards,
exact selectors, interpreter/dependency versions, every failed run and full logs.

Failed intermediate runs were charged: a launch-provider fixture used `reason`
instead of `why`; pin-time cancellation lost the existing diagnostic spelling
and was corrected to include the actual axis; the full boundary inventory
reported inherited and new gaps; the initial baseline source reconstruction had
one extra newline; an unknown-start fixture used the wrong table name; a fake
engine absence sentence omitted the requested identity; and the genuine-output
fixture initially supplied the other fixture's Authority assignment. Product
expectations were preserved. The final source-specific inventory audit binds the
four original source hashes, measures215/165 baseline unowned/orphan entries and
finds no introduced gaps. Global inventory failures are not claimed resolved.

All verification used Python3.13.7 and installed jsonschema4.19.2. This is qualified
deterministic evidence, not the required4.26.0 final gate. The new Docker selector
was source-parsed only and remains unexecuted pending independent review and a
separate readiness/execution assignment. No runtime/provider/model/image/install
work, Git mutation or DEPLOYMENT.md edit occurred. The deployment addition is a
dossier draft. This is awaiting-review implementation state, not Work/parent
completion or engine acceptance. No pickup blocker occurred under claim162766.

## 2026-09-13 — baton.tuner correction claim163053

Read canonical detail, new Work events through163053, the complete new handoff
and current dossier/review-2026-09-13T19-15-06Z.md; T32577 has no message after
M162978. All nine candidate and four protected hashes still match the review.
Taking the deadline-only P1 correction recorded in FINDING, preserving ordinary
cancellation and shared-source ownership. Author spend carries forward unchanged
at45.89975568297086/120s; reviewer spend0.513877716002753/60s remains separate.

## 2026-09-13 — correction163053 ready for independent review

P1 is addressed in deadlines.py without editing the ordinary cancellation owner.
Transparent callbacks capture the actual agent/stop exception objects and rethrow
them through request_cancellation. Recovery handles only those exact objects or
their exact two-member ExceptionGroup, records bounded credential-checked fault
evidence, validates fixed identity/intent and re-resolves the same Authority fence
through the public port. Changed runtime/assignment, Authority/manager failures,
output conflicts and unknown/provider-unsettled cleanup remain held. Fault records
are advisory evidence and never runtime absence or gate proof.

Added15 deterministic cases, preserving all31 earlier cases; load_tests selects
authored cases once instead of duplicating inherited fixture tests. Added four
inventory regressions and exact source-bound forwarding records for agent.cancel
and adapter.stop. The wrappers preserve original commands/results/exceptions;
the original _order_quiescence remains the receiving owner. The inventory refuses
changed forwarding source, an invented owner and unrelated duplicate crossings.
This resolves the measured scanner collision without broadening a shared source
hook or suppressing an entry/owner/probe obligation.

Final correction selection:165 tests passed in verification-162766-16.log. Final
diagnostic checking was moved before truncation to avoid preserving a credential
prefix; its two focused checks passed in log17. Cumulative author spend is
65.68318817297404/120s; remaining54.31681182702596s. This includes failed child13
(a test incorrectly expected another agent call after proven runtime absence)
and child14 (the inventory collision). Child15's source comparison again shows
baseline/current215 unowned and165 unaccounted entries, zero introduced gaps.
Python3.13.7/jsonschema4.19.2 remains qualified evidence, not the pinned final gate.

HANDOFF-163053.md binds candidate-163053-r2.json and the exact three-file correction
patch. Six other candidate paths and all four protected paths are unchanged,
including shared attempts/documents and W161230's six-fact reader/tests. The first
claim163053 capture is retained as a superseded draft; r2 is the current candidate.
No runtime/image/install/model execution, DEPLOYMENT edit or Git mutation. Passing
for independent review; no claim/pickup blocker and no Work/parent closure.


## 2026-09-13T19:45:33Z — baton.tuner claim163184, awaiting independent review

Consumed review163135/pass163176. Corrected only test_runtime_deadlines.py and
test_runtime_deadline_engine.py as scheduled; preserved all other expectations
and all source/protected hashes. Nine hold assertions now check exact ownership;
focused existing retry/restart/success cases check release. Prepared engine source
checks the same lane through hold/release/replay; no engine execution occurred.
Full candidate163184 and exact two-file patch are bound in HANDOFF-163184.md.

Final46 cases pass (child19); child18 also passed before deleting one redundant
assertion. Cumulative author66.81117755598098/120s, remaining53.188822444019024s; reviewer unchanged
at4.243902589994832/60s. Qualified Python3.13.7/jsonschema4.19.2 only. Required
4.26.0, proposed/unactivated180s Docker gate and W161230 docs handback remain.
No product, engine/image/install/provider/model or Git-state change.


## 2026-09-13T20:11:35Z — baton.tuner claim163313, awaiting independent review

Implemented the exact review163284 fixture correction: existing engine fixture,
new deterministic budget test and dossier engine-gate.py only. Durable exact names
and run labels precede creation; surviving supervisor owns bounded removal/reap
and records combined body/cleanup failures.120/5/50/5 slots share absolute180s.
Local fixture roots stay as durable evidence, preventing child filesystem cleanup
from racing supervisor container cleanup. Existing engine acceptance method AST
is unchanged. Full11-file candidate and exact three-file delta in HANDOFF-163313.md.

Final21 fake-boundary cases pass (log25); earlier16/19 selections in logs23/24
retained. Author67.54953842499526/120s, remaining52.45046157500474s; reviewer unchanged
4.757895970993559/60s. Required4.26.0, opsM163303 and DEPLOYMENT handback remain.
No real engine/API/process/image/install/model or Git mutation;180s remains
unactivated and Work/parents remain open.


## 2026-09-13T20:25:53Z — baton.tuner claim163413, awaiting independent review

Corrected review163385 three supervisor P2 findings: retained waitable leader
identity through whole-group settlement, atomic diagnostics plus independent
creation intents with conservative cleanup, and final-output timing with explicit
provisional evidence and authoritative exit status. Changed only engine-gate.py
and test_runtime_deadline_engine_budget.py; engine fixture, acceptance assertions
and product/protected bytes unchanged. Full candidate/delta in HANDOFF-163413.md.

Final33 deterministic cases pass, log28. One fake group_alive answer-count error
in log26 retained; corrected31 pass in log27. Author68.4909876419988/120s remaining
51.5090123580012s; reviewer4.971617716990295/60s unchanged. All28 rows persist.
No real Docker/API/process-group/runtime/image/install/model operation. Required
4.26.0, opsM163303 and DEPLOYMENT handback remain;180s engine unactivated.

## 2026-09-14T00:10:21.849221+00:00 — baton.tuner claim164779, awaiting review

Owner reroute164775, baton.tuner claim164779: bounded correction prepared for independent review. inspect_owned now accepts exact Docker daemon and explicitly supported short absence diagnostics, exact requested name, integer exit1, and empty/[] stdout after surrounding whitespace normalization. Byte comparison rejects invalid encodings and additional diagnostics. Generic nonzero failures remain failures. No identity, removal, uncertainty, process, duration or completion rules changed.

The fake Docker now emits the retained real prefix. Three new test methods cover both supported variants before/after immutable-ID removal, 21 refusal combinations, and digest-bound replay of all six actual parent responses through the real Calls/Inventory/cleanup code with an injected runner. All prior33 cases remain. Focused pinned verification passes36 tests in verification-162766-33.log (Python3.13.7/jsonschema4.26.0). Only this deterministic module ran; historical product/deadline/no-start evidence was not rerun.

Author cumulative 68.89533569900784/120s, remaining51.104664300992155s, 33 ledger rows. Reviewer5.285408751995419/60s, remaining54.71459124800458s. Readiness0.1878712520102272/20s is already included in author spending. Owner engine30.81015891599236/180s, remaining149.18984108400764s. No reset or transfer.

All44 original owner evidence files still match preservation-164779.json, including the failed receipt, result and body log. The original exit1, candidate_pass=false, independent_acceptance=false and four unresolved names remain unchanged. Replay proves classifier behavior on historical observations only; it is neither current resource absence nor retroactive gate success. No Docker/API call, container removal, engine rerun, install, build or real child process was executed by the focused tests.

The other nine candidate files and five protected source/test files match candidate163413. DEPLOYMENT.md remains W161230-owned and untouched here; observed hash efb5cb8d24b7c2f7afb4592078f5fe7c9aed7faf27656437bf6172aa21198b86 differs from the prior protected hash (protected-drift-164779.json). Exact W161230 handback remains required before later documentation edits. Scoped git diff --check passes. Repository-wide check reports unrelated trailing whitespace at v12/python/tools/stage_execution.py:1909; left untouched.

Next baton.feat independently reviews this correction and remaining acceptance. Original owner-execute-164414.py is consumed and must not be reused. Any later engine assignment must explicitly account for remaining149.18984108400764s, update reviewed execution bounds/provenance for this candidate and resolve the managed subprocess launch boundary or select an owner execution. The unchanged supervisor maximum180s does not itself fit the remaining bank. No further runtime authority is implied. Obligation163303 is answered; do not reopen it. Successful complete engine acceptance, required remaining pinned verification, DEPLOYMENT handback and W32577/parent closure remain open.

Candidate candidate-164779.json SHA256 ea2cb3557d8ac87b8198ec5bd5cc9c35545a550c0c9a8e53b3b2da11323902e5; delta correction-164779.patch SHA256 41678d144c0cd31b15cb5ab3aa3ce69d238c20796f21c4bc57f4923ac4e3011d.

## 2026-09-14 — baton.tuner claim168487, documentation awaiting final review

Consumed pass168483, all Work events/T32577 and the current dossier. Independent
review-2026-09-14T10-31-10Z.md accepts the new owner engine run and817 pinned
product tests, superseding the historical pending-engine/verification state above.
M165203 released DEPLOYMENT.md, and its exact base hash still matched. All11
accepted candidate164779 files and five protected source/test hashes also matched.

Published only the selected deadline section in DEPLOYMENT.md:109 appended lines,
all existing bytes and mode preserved. The examples and explanation cover trusted
immutable policy, no-deadline/legacy handling, explicit observation and advance,
same-fence recovery after cooperative errors, retained output and distinct local
cleanup/Authority gate settlement. Current source and public signatures were read;
the two examples also passed static AST/signature checks. Scoped whitespace passes.

HANDOFF-168487.md and documentation-168487.json bind the exact base, candidate and
patch. Candidate SHA25648a3268e456765c02696c897558f1aed9511c39a4188480a8d194b21ac50077f.
All11 source/test/supervisor candidate and five protected hashes remain unchanged.
No product test, engine/provider/image/install operation or Git mutation occurred.
The measured static check cost0.009850611997535452s is recorded separately; prior
author test/readiness68.89533569900784s, reviewer15.57119406198035s and engine
61.62230291699234s remain recorded, including the original failed run. Other
read-only inspection is unmeasured. Standing policy removes old cumulative
admission gates; selected per-run boundaries and evidence remain intact.

Return to baton.feat for independent review of the documentation candidate and
final acceptance. Existing engine/pinned evidence is reused, not rerun. Inherited
global inventory qualification and managed Python-to-Docker limitation remain.
W32577 and parents are not closed by this documentation-author claim.
