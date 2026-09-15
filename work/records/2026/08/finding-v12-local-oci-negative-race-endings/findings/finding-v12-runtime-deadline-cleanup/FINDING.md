# Define and compose a runtime deadline into exact cleanup

## Discovery and parent

Discovered while implementing W32382 under
`work/records/2026/08/finding-v12-local-oci-negative-race-endings/`.
The parent requires a manager-owned execution deadline to traverse the same
exact runtime/provider cleanup crossing as every other ending.

## Confirmed gap

The current tree has no runtime-attempt deadline. The only durable
`deadline_at` lives in `worker_manager/interrogation.py` and belongs to one
probe/inquiry operation. Its `timed-out` outcome deliberately records only
that the manager stopped waiting: it is not cancellation, is non-terminal, and
permits a later answer. Reusing that field or prose to destroy an execution
runtime would reverse its confirmed meaning.

No current production owner defines who observes an execution deadline, what
clock/generation fixes it, how it orders authority fencing/assignment ending,
or how it enters exact runtime and provider cleanup. The missing product
meaning must be ruled before tests or implementation guess it.

## Required boundary

- Define one explicit runtime-attempt deadline identity, owner, clock and
  durable observation. Do not borrow interrogation timeout semantics.
- Rule whether expiry requests cancellation/fencing or another typed authority
  ending, and preserve that authority-before-destruction ordering.
- Compose expiry through existing exact reconciliation, output custody as
  applicable, force-removal, positive absence, credential/launch teardown and
  cleanup settlement.
- Bind the operation to exact assignment generation, attempt, deadline policy
  generation and observed instant. Restart/retry replays the first accepted
  deadline fact; stale generations and changed policies fail closed.
- Preserve unrelated attempts and forbid replacement while deadline cleanup is
  pending, uncertain or provider-unsettled.

## Open decision

An approver must confirm the runtime deadline's authority meaning before
implementation: the existing interrogation `timed-out` observation cannot
authorize runtime destruction, while silently treating expiry as worker
`cancelled` would attribute a worker disposition the worker never produced.

## Acceptance

- The confirmed deadline rule is pinned here before production edits.
- A real Docker runtime crosses the deadline while present, the authority
  ending/fence occurs first, and the exact container is force-removed with
  positive absence and provider settlement before lane reuse.
- A deadline cannot be caller-backdated, moved by retry, applied to a stale
  generation, or confused with an interrogation timeout.
- Restart, concurrent observation, already-quiescent runtime, uncertain engine
  observation, provider-unresolved retry and sibling preservation are covered.
- Required Docker evidence fails rather than skips; daemon-free policy and
  replay tests remain warning-clean.

## 2026-09-13 — recovered owner ruling and tuner revalidation

Recorded by baton.prompt after rereading T32382/M33822 and current W32577 state.
The owner answered the deadline question on 2026-08-28T20:04:34Z, after this
Work was parked, but that answer was not pinned here. The Open decision above,
PLAN's pending-M32585 gate and historical PROGRESS blocked state are superseded:
they describe the earlier state, not a missing owner decision today.

Owner M33822 rules that the Worker Manager owns the authoritative runtime-attempt
clock and persists its exact deadline and policy generation before runtime start.
Expiry records only a typed deadline-reached observation. It does not itself
kill, fence, cancel, discard output or fabricate worker-cancelled. The configured
route/runtime policy determines the action: report-only leaves execution running;
cancel first commits an Authority-owned deadline cancellation or fence before
exact runtime removal and cleanup. Retries preserve the original deadline and
policy generation; stale or already-terminal attempts fail closed.

Slawomir now authorizes advancing this independent queue branch using the idle
tuner. W161230 is not a prerequisite. First revalidate this ruling and the old
gap against current owners, including later per-Job limits and managed recovery.
Produce the smallest concrete implementation scope and independent-review handoff.
Do not turn the recovered decision into another request for the same approval.

For this initial assignment, baton.tuner owns this dossier's FINDING/PLAN and a
new revalidation/handoff note after prompt's pinning edit. Source inspection and
planning can proceed now. Product/test edits must first establish exact ownership
with W161230: worker_manager/attempts.py and documents.py and related runtime
owners may overlap its active implementation. Preserve that claim and candidate.
Identify disjoint work that can proceed and exact shared changes that need serial
integration; no blanket dependency on complete W161230 is justified by overlap.
Do not run tests or real Docker as part of this initial read-only revalidation.
Specify focused verification and any needed runtime evidence in the resulting
bounded plan. Current standing test authority removes old test-only approval gates;
fake/replay verification is the default, with actual Docker reserved for a named
engine-specific question. No historical acceptance is silently waived.

This recovery logs a coordination/documentation omission, not a demonstrated
Baton scheduler defect: the parked Work correctly retained its recorded phase.
W32382/W33755 retain their final dependency until the deadline outcome is satisfied.

## 2026-09-13 — source revalidation under tuner claim162662

**Confirmed:** M33822 matches the actual owner message in T32382. Per-Job
provider/verification limits, custody-command bounds and managed recovery do not
implement its runtime-attempt deadline. The historical inventory and claim that
the implementation would only need a small cancellation wrapper are superseded
as a current plan by [REVALIDATION-162662.md](REVALIDATION-162662.md). In particular,
ordinary cleanup requires an intake receipt; a policy-cancelled worker that never
answered needs a typed receiptless deadline ending without fabricated worker
disposition or abandonment. Exact cleanup, retained untrusted output, provider
settlement, lane release and Authority gate discharge all remain required.

The note records inspected symbols/digests, a finite proposed path set and
deterministic verification followed by the named real-engine acceptance. Its
policy/API shapes and proposed execution bounds await independent design review;
they are not product changes or a repeated request for M33822. Initial revalidation
and planning are complete; no tests/runtime/product edits were performed, and
PROGRESS is preserved. M162672 requests exact W161230 ownership coordination;
attempts.py, documents.py and DEPLOYMENT.md remain with that live claimant until
an explicit file handoff. No blanket dependency on W161230 completion is added.

## 2026-09-13T18:26:19Z — independent design review and serial ownership resolved

baton.codex claim162733 read the entire dossier, Work events and T32577, and the
actual T32382/M33822. REVALIDATION-162662.md matches its handed-off digest.
review-2026-09-13T18-26-19Z.md accepts journal-only manager deadline/policy with
observation-only expiry and policy-selected Authority-first cancellation. Source
inspection confirms ordinary cleanup's receipt requirement and the distinct
abandonment declaration; a deadline-specific typed authorization can reuse exact
OCI removal and recordless retained-custody settlement without relabelling either.

The review concretizes trusted policy operands, explicit no-deadline selection,
immutable manager time, legacy committed-start treatment, stable observation and
advance identities, receiptless command/proof contents, output races and separate
Authority gate discharge. Its requirements are implementation design under the
confirmed ruling, not a new owner ruling. Read the complete review before editing.

**Ownership update, superseding the pending-request wording above:** M162711 and
correction M162716 release attempts.py/documents.py after the then-in-flight
W161230 review; that round returned at162727. Fresh bases match respectively
8c321ac7d9c1c5764c4f181e50a1e99d911c481dad0c20ea1ac11d7a2b349730 and
b3fc43f26ffef5a76f1329b273ea722f04c4544b722511c681c3c1a0418b20bd.
Tuner may take them in the next implementing claim and must record new hashes.
DEPLOYMENT.md stays with W161230; draft the addition here until serial release.
test_reconciliation_worker.py stays there too, hash
c0d7f2d1f90a1a5d024c034c83ef71fdc161888f37817e198fd318b08c67bd98; run its six-fact
proof regressions after shared-source changes and coordinate needed test edits.
Standing test authority avoids another test-only approval gate. AGENTS.md's actual
change author rule governs the tuner's PROGRESS append, superseding historical
wording that reserves it permanently to baton.claude.

The next bounded assignment is deterministic implementation on the reviewed path
table, with DEPLOYMENT deferred. The review selects the proposed120s author/60s
reviewer cumulative ceilings; both start at0 and every child requires persisted
guards. No tests/probes ran during either planning/review claim. The proposed180s
engine run remains a separate final gate after candidate review; prepare its
exact selector/readiness evidence without running, pulling, building or installing
here. No live provider is needed. W32382/W33755 retain their acceptance dependency;
design review does not close W32577. Reviewer changed only this review/FINDING/PLAN,
not product/tests/PROGRESS/runtime/environment or Git state.

## 2026-09-13T19:02Z — deterministic candidate and observed verification limits

**Confirmed implementation, awaiting independent review.** Tuner claim162766
implements M33822 through immutable manager-journal selection/reached records,
the existing Authority-first cancellation owner, distinct receiptless deadline
cleanup and separate gate discharge. HANDOFF-162766.md and candidate-162766.json
bind the nine-file candidate. The selection includes explicit None for new
unconfigured starts; committed legacy starts cannot acquire a retroactive pin.
Exact retry identities are preserved across interrupted removal and discharge.
Ordinary receipted output remains with its actual owner. No policy ruling is
superseded; the older unimplemented/pending-decision description is historical.

**Observed inherited verification gap.** The full boundary-inventory class was
not green. Source reconstruction in inventory_audit_162766.py verifies the four
exact pre-change source hashes before measuring the same inventory against
baseline/current trees. Both retain215 unowned receiving entries and165
unaccounted helper calls after this candidate's26 receiving entries and13 helper
call accounts were supplied. No new unowned/unaccounted entry remains. The
deadline-specific source ownership, delegated arrival probes and stated-rule
witnesses pass; this evidence does not repair or certify the global inventory.
The original failing output and the final comparison are preserved, not waived.

**Observed environment limit.** Python3.13.7/jsonschema4.19.2 ran the802 passing
focused tests. pyproject requires jsonschema4.26.0, so the required pinned final
verification remains unavailable in that selected environment. No installation
was attempted. The author ledger charges every child, including failures, at
45.89975568297086/120s; remaining74.10024431702914s. Independent review retains its
separate60s allowance. The new required Docker selector is prepared but was
source-parsed only, with no Docker/image/provider/model execution. Its proposed
180s gate and image/dependency readiness need the later assignment documented in
ENGINE-READINESS-162766.md. W32577 and its parents remain open.

**Ownership.** W161230's released attempts/documents bases are preserved except
for the reviewed deadline hook/constructors. Their resulting hashes are
1f7c1532372bbf714d3c7d77ebb1a3d29e6d34a98afb0a718fa9f3a9ef4853f6 and
5f31654f699448a8e52d076f6ba517e9acfef201ada30dea0559051af474b014.
The six-fact reader and test_reconciliation_worker.py bytes are unchanged.
DEPLOYMENT-DEADLINE-DRAFT-162766.md is ready for its eventual serial handback;
DEPLOYMENT.md was not edited. No pickup or claim blocker occurred.

## 2026-09-13T19:15:06Z — independent review finds cooperative failure veto

baton.codex claim163016 reviews return162981/M162978. HANDOFF and candidate
manifest hashes match; all nine current candidate paths and four protected paths
match. review-2026-09-13T19-15-06Z.md records the exact review and remaining gates.

**Confirmed P1:** advance_deadline waits for request_cancellation to return
normally. The existing owner commits Authority cancellation, issues runtime stop
even if agent cancellation failed, then rethrows that agent fault. The new
deadline composition consequently never reaches force-removal. Independent
two-retry reproduction with a persistently unreachable agent has a confirmed
fence, two successful stop orders, zero destroy calls, pending cleanup and held
lane/gate. A failed cooperative stop likewise prevents available exact removal.
Preserve advisory failure evidence and positively re-resolve the fence/runtime
before progressing; do not require an already stopped agent to become reachable.
Authority refusal, unknown identity/start, conflicting output and unsettled
providers still hold. Ordinary cancellation error semantics remain unchanged.

The prior candidate-ready statement is superseded as current action by changes
requested. Independent31 deadline+26 no-start tests pass, plus two research
observations of the defect (59 checks total, warnings as errors). One guarded
child0.513877716002753s; reviewer cumulative0.513877716002753/60s,
remaining59.48612228399725s in review-ledger-163016.json. Author remains
45.89975568297086/120s, remaining74.10024431702914s. Qualified4.19.2/pinned4.26.0,
global inherited inventory and unactivated180s engine gate remain explicit.
No source/engine acceptance, Work/parent closure or live model execution.
Reviewer records/research only; tuner retains correction ownership and must
coordinate further shared-file edits. DEPLOYMENT remains with W161230.

## 2026-09-13 — correction plan under tuner claim163053

Revalidated P1 against attempts._order_quiescence: it preserves cooperative
errors after the Authority fence and runtime-stop attempt. Correct only the
deadline composition in deadlines.py: capture provenance at the two cooperative
call boundaries, preserve/rethrow their original exceptions through the ordinary
cancellation owner, and recover only the exact captured exception(s). Journal
their failure evidence, revalidate the same fixed assignment/runtime and matching
cancel intent, then re-resolve the exact Authority cancellation operation through
the public port before cleanup. An Authority or manager failure that did not
originate at a captured cooperative call must propagate. No private Authority
session access or inferred fence is permitted. Existing output/provider/start
holds and final positive-proof requirements remain.

This supersedes the implementation assumption that a normal return from the whole
ordinary cancellation composition is necessary for deadline force-cleanup. It
does not change M33822 or ordinary cancellation semantics. The bounded correction
uses deadlines.py, additive cases in test_runtime_deadlines.py, and inventory
accounts if actual discovery needs them. attempts.py/documents.py, the retained
no-start tests and DEPLOYMENT.md stay untouched. Verification continues the same
120s author ledger from45.89975568297086s; no new runtime/image/install authority.

## 2026-09-13 — P1 corrected, candidate163053-r2 awaits review

The normal-return prerequisite identified in review163016 is removed from the
deadline composition. The actual exception objects are captured only at the
agent.cancel/adapter.stop callbacks and rethrown through the unchanged ordinary
owner. Only that exact exception or its exact two-member group is recoverable;
other Authority/manager failures propagate. A recoverable advisory fault is
journalled under runtime.deadline-cooperative-failure, with fixed attempt,
assignment/runtime, reached/cancel identities, stage and bounded typed diagnostic.
Credential checks precede diagnostic truncation; unsafe diagnostics retain a
fixed withheld account. The journal is evidence of failure, not authority.

Cleanup then requires the matching committed cancel intent and a successful
public-port replay of the exact Authority cancellation operation, with the same
fixed runtime checked before and after. Existing output eligibility, no-start
proof, provider endings, custody, local lane and remote gate requirements remain.
Persistent agent/stop failure no longer requires the stopped agent to recover.
Ordinary request_cancellation preserves its original errors and stop ordering.

The source analyzer initially counted the transparent callbacks as second
receiving owners. Exact forwarding records now bind both callbacks to the
unchanged attempts._order_quiescence owner and the complete helper AST digest;
tests prove unchanged settlement/exception forwarding and reject altered source,
invented owners and unrelated duplicate crossings. No callback or receiving entry
is omitted from discovery. The source-specific audit remains zero-delta over the
inherited215 unowned/165 unaccounted global gaps; no global acceptance is claimed.

The corrected delta is deadlines.py, test_runtime_deadlines.py and
test_boundary_inventory.py only. candidate-163053-r2.json binds the full nine-file
candidate and explicitly supersedes the earlier claim163053 draft capture.
165 focused checks plus two final diagnostic checks pass. All17 author children
remain in one ledger:65.68318817297404/120s, remaining54.31681182702596s. Reviewer
spend and all pinned-dependency/engine/documentation gates remain as in PLAN.
This is the tuner's correction claim, not independent signoff or parent completion.


## 2026-09-13T19:38:00Z — cooperative-failure P1 resolved; lane assertions need correction

Independent baton.codex claim163135 reviewed candidate-163053-r2.json, digest
d60e1f546ab113d61e1ff29fbad59a9b4e91ce14cde600f702985b56b11aecd7.
See review-2026-09-13T19-38-00Z.md. The earlier19:15 P1 is resolved for these
source bytes: exact captured advisory faults can recover only through replayed
Authority fence and fixed identity; force cleanup succeeds and exact retries do
not reexecute. Replacement manager errors and process interruption still refuse.

**Confirmed P2:** runtime_lane is a projection, including after lane release.
The prepared engine test's whole-value None expectation is incorrect; nine
assertIsNotNone hold checks in test_runtime_deadlines.py do not prove occupancy.
The next bounded tuner assignment corrects those two accepted test surfaces to
assert holder and held_by_this_attempt, preserving all acceptance obligations.
Standing test-change authority supplies permission; no product scope extension.
My initial independent probe had the same incorrect None expectation, retained
as reviewer harness error rather than product evidence. The corrected four
independent checks pass;76 unchanged candidate/no-start/inventory cases pass.

Reviewer4.243902589994832/60s cumulative, remaining55.75609741000517s, includes
both children and the harness failure; latest review-ledger-163135-r2.json.
Author65.68318817297404/120s, remaining54.31681182702596s, unchanged this review.
Evidence remains Python3.13.7/jsonschema4.19.2 deterministic, qualified for the
missing4.26.0 pin. Engine180s unactivated; exact image/dependency readiness,
required real Docker evidence and W161230 DEPLOYMENT handback remain due.
No Work or parent closure; PLAN names the current correction assignment.


## 2026-09-13T19:45:33Z — tuner corrects lane hold/release assertions for review

Claim163184 addresses review163135 P2 in exactly the two assigned test paths.
The runtime_lane projection remains present after release; tests now require the
exact holder and held_by_this_attempt fields. Existing failure/retry/restart
cases gain release checks, and the prepared engine case binds hold, release and
replay to the same lane identity. All product and protected bytes are unchanged.
See HANDOFF-163184.md and candidate-163184.json (SHA256 e006a1e264463454be3aedb3355905dea7d5ceff09b139170f2d49f286c09a10).
The earlier P2 describes the superseded test bytes; resolution awaits independent
review of this correction. No product acceptance rule is superseded.

Final46 deterministic cases pass; author66.81117755598098/120s, remaining53.188822444019024s,
all19 children retained. Reviewer4.243902589994832/60s remains unchanged.
Required dependency4.26.0, real Docker evidence and DEPLOYMENT handback remain
outstanding; proposed180s engine allowance remains unactivated. Readable base
image source pin is recorded in the handoff without claiming worker-image
readiness. No engine/image/install/provider/model execution occurred.


## 2026-09-13T19:48:10Z — lane correction accepted; bounded readiness selected

Independent baton.codex claim163219 accepts source/test candidate163184, SHA256
e006a1e264463454be3aedb3355905dea7d5ceff09b139170f2d49f286c09a10. See
review-2026-09-13T19-48-10Z.md. The earlier19:38 P2 lane assertion finding is
resolved: exact holder/held_by_this_attempt now prove hold and release; engine
source additionally binds the same lane through replay. Earlier P1 remains
resolved on unchanged product bytes. All46 deadline cases pass independently.

Reviewer cumulative4.757895970993559/60s, remaining55.24210402900644s, latest
review-ledger-163219.json. Author66.81117755598098/120s unchanged, remaining
53.188822444019024s. Qualified Python3.13.7/jsonschema4.19.2 evidence only.
No Docker/image/install/model operation ran in this review.

The next selected tuner assignment is read-only readiness, specified in that
review: locate an existing pinned interpreter, inspect daemon and local worker
image metadata/provenance, prepare the exact gate packet or report missing facts,
and coordinate W161230 DEPLOYMENT handback. Readiness probe ceiling20s aggregate,
10s each, charged within existing author120s with persisted guards. No separate
budget/reset, no engine selector or container creation, no install/build/pull,
no product/test changes. Proposed engine180s remains unactivated until readiness
is assessed. Required4.26.0 verification, actual engine acceptance and final docs
remain due; W32577 and parents stay open. PLAN names this current assignment.


## 2026-09-13 readiness claim163241 — operational access and dependency findings

The bounded read-only Docker version child reports client29.1.3/API1.52,
Server=null and permission denied connecting to unix:///var/run/docker.sock.
See readiness-163241-20.log and socket-metadata-163241.json. Current daemon and
preloaded image metadata therefore remain unverified through this installed
execution boundary; no escalation, alternate socket or privileged workaround was
used. This is an environment access finding, not evidence of a Baton defect.
The system Python probe confirms3.13.7/jsonschema4.19.2; repository .venv probe
raises PackageNotFoundError for jsonschema. Logs21/22 retain both results and
the original author ledger charges all children, including failures.

A broad preliminary metadata search could not read /tmp/snap-private-tmp and
systemd-private service directories (Bluetooth, chrony, lm-sensors, polkit,
logind, ModemManager, bolt, colord, fwupd and upower). Those unrelated paths were
not required inputs; the search was narrowed to readable repository, installed
Baton and Python cache metadata. No complete-machine absence claim is made.


## 2026-09-13T19:55:15Z — completed readiness research; concrete gates retained

READINESS-163241.md records all three guarded probes and immutable source bindings.
Readiness0.09727905600448139/20s was charged within author66.90845661198546/120s, remaining53.09154338801454s;
reviewer4.757895970993559/60s unchanged. Accepted candidate163184 and protected
bytes still match. Docker connection access, pinned4.26.0 environment and exact
preloaded/current worker provenance remain unestablished. Historical image records
have three current-source mismatches and cannot supply that evidence by themselves.

M163260 explicitly retains DEPLOYMENT until managed-storage corrections and
owner-obligation163010 queue-reader correction land. M163265 selects later serial
handback with fresh hash; no draft insertion occurs now. M163260 corrects the
earlier no-pip inference: venv pip exists; no installation was attempted.

Source revalidation also confirms the proposed180s engine fixture shares its
deadline with cleanup but reserves no cleanup time. The next executor packet
needs an explicit within-bound cleanup/outer-guard strategy before activation.
No new product/test/doc edit was made or authorized by this readiness finding.
PROGRESS remains the prior implementation account. Return facts to baton.feat;
no Work/parent closure or runtime acceptance is claimed.


## 2026-09-13T19:57:38Z — independent readiness acceptance and cleanup correction scope

Review claim163284 accepts READINESS-163241.md and independently verifies its
bindings, unchanged candidate163184/protected hashes and22-row spending totals.
Raw logs establish denied tuner Docker socket access and inspected-interpreter
pin mismatch, not daemon failure or universal absence of4.26.0. M163260 image
listing is attributed to another execution boundary. Historical image provenance
is insufficient without current identity/entrypoint and source assessment.
See review-2026-09-13T19-57-38Z.md and OPS-READINESS-163284.md.

Confirmed fixture gap: one180s deadline currently covers body and cleanup without
reserve, and owned names exist only in the test child. Exhausted time or an outer
kill can prevent cleanup. Before gate activation, select120s body/setup +5s reap
+50s exact owned cleanup +5s accounting, all within one absolute180s deadline,
with durable name registration before create/run and a surviving supervisor.
Timeout or cleanup failure must retain unresolved names and fail the gate.
This is a test-fixture correction; no deadline product behavior changes.

Next tuner scope is existing test_runtime_deadline_engine.py, new deterministic
test_runtime_deadline_engine_budget.py and dossier engine-gate.py/evidence.
Preserve engine acceptance, test boundaries with fake clock/process/Docker only,
and return a bound candidate. Standing test authority applies. An asynchronous
baton.ops request addresses environment/access/image resolution separately; it
creates no install/build/execution allowance. Proposed engine180s remains inactive.

No tests or Docker/API probes ran in this review. Author66.90845661198546/120s,
remaining53.09154338801454s; reviewer4.757895970993559/60s, remaining55.24210402900644s.
M163260/M163265 still retain DEPLOYMENT with W161230 until the two recorded edits
and explicit fresh-hash handback. All final acceptance gates/parents remain open.


## 2026-09-13T20:11:35Z — tuner supplies reserved cleanup supervisor for independent review

Claim163313 implements review163284 fixture scope in engine-gate.py, existing
test_runtime_deadline_engine.py and new test_runtime_deadline_engine_budget.py.
See HANDOFF-163313.md; candidate-163313.json SHA256 f96cf65d7c201e0a7dda2f69d73fab0b7418fb9cd8da73144368c266cef9bcc7.
The prior180s no-reserve/process-local-name fixture is superseded by these
prepared bytes, pending independent review. No deadline product rule changes.

One absolute180s design selects120s body,5s owned stop/reap,50s exact cleanup,5s
accounting. Durable registration and run label precede every create/run. Cleanup
requires exact registered name/label and removes immutable inspected IDs; failed
or pending creation plus absence remains unresolved. Foreign replacements are
preserved. Child failures and unresolved names survive the child process.
Fixture roots remain per-run evidence; store closure runs in the child, while
container cleanup is supervised before any later optional filesystem housekeeping.
All existing engine acceptance method AST and other source/protected bytes match.

21 final deterministic fake-boundary cases pass. Author67.54953842499526/120s, remaining
52.45046157500474s; all25 children persist, reviewer4.757895970993559/60s unchanged.
No real Docker/API/runtime/image/install/model work occurred. OpsM163303 remains
pending; DEPLOYMENT handback and all required final acceptance gates remain open.


## 2026-09-13T20:14:59Z — independent supervisor review requires three corrections

Claim163385 reviewed candidate163313 digest
f96cf65d7c201e0a7dda2f69d73fab0b7418fb9cd8da73144368c266cef9bcc7. All candidate/
protected hashes and unchanged engine acceptance AST match. See
review-2026-09-13T20-14-59Z.md and probe-163385.py. Prior claimed fixture readiness
is qualified by three confirmed P2 gaps: TERM plus leader wait can leave an owned
descendant alive during cleanup; a partial in-place child call-record rewrite
prevents every cleanup attempt despite valid name inventory; and final accounting
omits its last durable write, allowing success after simulated total exhaustion.
No real processes, signals, Docker/API or long sleep were used to establish these.

All21 supplied deterministic cases pass; three additional research cases reproduce
the defects. Passing research is not acceptance. Next tuner scope remains the
engine fixture, its budget tests and dossier supervisor, with focused fake-boundary
corrections and the original120/5/50/5 within180s requirements. Preserve all engine
acceptance assertions and product/shared files. This explicitly schedules the
needed test changes under standing authority without another permission gate.

Reviewer4.971617716990295/60s, remaining55.028382283009705s includes this0.213721745996736s
child; latest review-ledger-163385.json. Author67.54953842499526/120s, remaining
52.45046157500474s unchanged. OpsM163303 remains pending; DEPLOYMENT retained by
W161230. Required pinned/real-engine/docs gates remain open; no engine activation
or Work/parent closure. PLAN names the correction as current work.


## 2026-09-13T20:25:53Z — tuner corrects three supervisor interruption boundaries

Claim163413 addresses review163385 P2 findings in the dossier supervisor and
budget test only. HANDOFF-163413.md binds candidate-163413.json SHA256
ecd8e311806a2b781f682a75adf396c888c31411bf931030b3c8ba1fad82b896. The prior leader-only wait, in-place diagnostic
replacement and pre-last-write success claims are superseded by this prepared
correction, pending independent review. Existing engine fixture bytes and all
product/protected files remain unchanged.

Leader WNOWAIT custody retains PID/PGID through TERM/KILL, live-member checks and
final reap; lost ownership or exhausted time fails without racing cleanup. Atomic
diagnostic replacement and separate immutable creation intents let damaged logs
retain errors/uncertainty while permitting positive exact owned cleanup. Persisted
result/stdout are always provisional; completion authority is supervisor exit
after final evidence writes and stdout flush have been timed and checked.

Final33 deterministic cases pass (log28); one earlier new-fake call-count failure
is retained in log26 and corrected. Author68.4909876419988/120s, remaining51.5090123580012s,
all28 children; reviewer4.971617716990295/60s unchanged. No real engine/API/process
group/image/install/model action. OpsM163303, DEPLOYMENT handback, required4.26.0
and real-engine180s activation/acceptance remain pending. No Work/parent closure.


## 2026-09-13T20:28:07Z — supervisor correction accepted; operations prerequisites next

Independent claim163472 accepts candidate163413 SHA256
ecd8e311806a2b781f682a75adf396c888c31411bf931030b3c8ba1fad82b896. See
review-2026-09-13T20-28-07Z.md. All three20:14 supervisor P2 findings are resolved
for these bytes: retained WNOWAIT leader identity through full group settlement;
atomic diagnostic replacement and immutable creation intents; final-write/flush
completion included in authoritative exit decision. Persisted result and stdout
remain explicitly provisional and require the bound supervisor exit receipt.
Engine fixture/product/protected bytes and acceptance assertions are unchanged.

All33 focused deterministic cases pass independently. Reviewer cumulative
5.285408751995419/60s, remaining54.71459124800458s, review-ledger-163472.json.
Author68.4909876419988/120s, remaining51.5090123580012s,28 children unchanged.
Qualified Python3.13.7/jsonschema4.19.2 only; no real process-group/Docker/API,
image/install/model action ran. No remaining source/test correction identified.

Pass to baton.ops for existing M163303 permitted execution boundary, pinned
interpreter and exact worker-image/provenance prerequisites, or concrete bounded
provisioning selection. Then baton.feat selects the actual engine invocation.
No new spending bank or install/build/engine authority is created;180s remains
unactivated. DEPLOYMENT retained under M163260/M163265. Required pinned/engine/
docs evidence and W32577/parent closure remain open; PLAN names the next action.

## 2026-09-13 — host evidence and preloaded reference-image inspection

Recorded by baton.prompt from Slawomir's host output and subsequent read-only
Docker image inspection. The host shell reaches both Docker client and server
29.1.3/API1.52; repository venv pip reports jsonschema absent. This establishes
host reachability, not a repair of the tuner's previously denied boundary.

The owner's full image listing exposes reference-worker candidates omitted from
the earlier integration/provider image leads. Prompt successfully inspected:

- sha256:b24786fc124a937c742332a34885519057c039e407b46edd61dedaea38a7b004,
  tagged baton-w6636-lifecycle:432ef36e0038 and :c74de564476d.
- sha256:3cc64b770fbacd84f4e865bc6398ed281713fc88b876c90acf9d8abbbe852e81,
  tagged baton-w39358-retry:07439ae69136 and :5fdbef30b3fe; its parent is the
  preceding lifecycle image.

Both inspect responses declare entrypoint ["python3", "/opt/baton/baton_worker.py"],
user65532:65532 and Python3.13.15. No labels were present. An initial formatted
inspection failed because it assumed Config.Labels existed; full inspection
corrected that lookup. Neither image was run, created, built, pulled or changed.
Search over work/records and v12 found no matching full image IDs or selected
tag fragments, so source/build correspondence remains unestablished. Entrypoint
and availability alone do not certify either image for the accepted candidate.

The original Docker denial is therefore specific to an execution boundary:
owner host and prompt image inspection work; tuner access remains unverified.
Do not infer a host Docker outage or a need to change socket permissions from
that refusal. Package installation and final engine execution were not performed.
Resolve pinned jsonschema4.26.0 and select/verify image provenance before the
bounded gate; reuse these image leads before proposing an unnecessary rebuild.

## 2026-09-13 — owner installed pinned jsonschema; interpreter prerequisite satisfied

Slawomir supplied successful installation output for jsonschema4.26.0 into the
repository virtualenv, with attrs26.1.0, jsonschema-specifications2025.9.1,
referencing0.37.0 and rpds-py2026.6.3. A subsequent read-only baton.prompt probe
using /home/sl/src/baton/.venv/bin/python3 independently reported that exact
executable, Python3.13.7 and importlib.metadata version jsonschema4.26.0.

This supersedes the earlier host-evidence entry's missing-package status and
the corresponding unresolved interpreter prerequisite in OPS-READINESS-163284.md.
The owner performed the installation; prompt only queried installed metadata.
No test or engine gate was run, so this is environment evidence rather than
pinned acceptance coverage. Managed tuner Docker access and reviewed worker
image provenance remain unresolved. Obligation163303 is still pending; its
other requirements and final engine/docs evidence are not waived.

## 2026-09-13 — owner image-content probe confirms historical worker mismatch

Slawomir ran host sha256sum and a temporary, read-only, network-disabled
container with sha256sum replacing the worker entrypoint, then docker history.
For image sha256:b24786fc124a937c742332a34885519057c039e407b46edd61dedaea38a7b004:

- Current v12/worker/baton_worker.py:
  85b48a2461e259f345ea9f984db4f2c522f83be943b40837882ce5c8241278dd.
  Image /opt/baton/baton_worker.py:
  da34aa2c1dff8b9f25d748db79fc078c6082de9a13e5908c2cf247b99753a923.
- scripted_agent.py matches:
  f3a47fa86537d509fec58cdccefb4f0ffd53a55592cf08c75d7fafaa16c3b27c.
- worker-control-1.0.schema.json matches:
  22caa60ae0aab610d93d9c676925b52c49a893352b2f8a72b03bee7a6a3301bc.

History contains the expected three COPY destinations, numeric non-root user,
reference entrypoint and Python3.13.15 base metadata. This supersedes the earlier
possibility that this lifecycle image is an exact match for the current worker.
Matching entrypoint/history does not override the measured source mismatch.
The retry derivative has not been content-tested; no equivalence claim is made.

Proposed owner provisioning: build v12/worker/Dockerfile with context v12/worker
and its existing pinned FROM, then capture immutable image ID/config and compare
the three copied file hashes. This is a fresh reference image, not a change to
the Dockerfile or product source, and does not start a model or satisfy the
managed deadline acceptance gate. No build was executed by baton.prompt.
Tuner execution-boundary access remains unresolved.

## 2026-09-13 — owner built current reference image and confirmed copied bytes

Slawomir supplied successful output from docker build --pull=false using
v12/worker/Dockerfile and context v12/worker, tag baton-w32577-reference:20260913.
The build used the recipe's existing pinned base
python@sha256:8fef26df932191825664e4957ff488c96dfe64918327634a357a55facbc994d3
(local base9351a9a0a697), all three COPY steps, user, entrypoint and environment.
Resulting immutable image ID:
sha256:9b8c98820877e33d38d33352d86cc3810e5b72d4935a181b82b512b4d3291de8.
Owner inspect reports ["python3","/opt/baton/baton_worker.py"] and "65532:65532".

Owner's temporary sha256sum container reports:
- baton_worker.py: 85b48a2461e259f345ea9f984db4f2c522f83be943b40837882ce5c8241278dd.
- scripted_agent.py: f3a47fa86537d509fec58cdccefb4f0ffd53a55592cf08c75d7fafaa16c3b27c.
- worker-control-1.0.schema.json: 22caa60ae0aab610d93d9c676925b52c49a893352b2f8a72b03bee7a6a3301bc.

Prompt independently rehashed the current three source files and confirmed all
match those reported image bytes. Current Dockerfile SHA256 is
0aa92e0b07c10e72bc6ca6c03c2c95f2e94da7fb9585c7a3969774f214d5cc0f.
Build and image-content execution were performed by the owner, not prompt.
Docker's legacy-builder deprecation warning did not prevent build success.

This completes the proposed owner build and supplies exact current-source image
evidence in place of the historical mismatch. It supersedes the prior open
image-provisioning/provenance lead; the managed reviewer can bind this immutable
image and the already supplied interpreter into the final assignment. Managed
tuner Docker access remains unverified. No live model or deadline acceptance
test was run by these build/hash commands; obligation163303, final gate and docs
remain open pending their remaining requirements.


## 2026-09-13T22:57:46Z — tuner direct managed Docker checks succeed

Claim164329 executed exactly owner reroute164326: standalone managed docker
version, then image inspect for immutable
sha256:9b8c98820877e33d38d33352d86cc3810e5b72d4935a181b82b512b4d3291de8.
Both exit0. Client/server29.1.3/API1.52 are reachable; image Id matches, entrypoint
is ["python3", "/opt/baton/baton_worker.py"], user65532:65532. Full raw outputs and
guards are bound in MANAGED-ACCESS-164329.md. No escalation was requested.

This supersedes the broad current inference of inaccessible Docker from tuner.
Earlier Python-wrapped denial remains valid historical evidence for that other
invocation boundary. No claim is made that direct-tool success proves equivalent
Docker access from the Python supervisor; ops must select the final permitted
invocation. No tests, runtime/container, build/install/image mutation or further
API probe occurred. Owner image/source and interpreter evidence is retained.

This claim0.080s; readiness cumulative0.1772790560044814/20s within author68.5709876419988/120s,
remaining51.4290123580012s, all30 rows retained. Reviewer5.285408751995419/60s unchanged.
Return to baton.ops; M163303, engine activation/acceptance and final docs remain.


## 2026-09-13T23:01:32Z — pinned-Python Docker subprocess access remains denied

Owner reroute164359 was executed under tuner claim164363. Both assigned metadata
commands through /home/sl/src/baton/.venv/bin/python3 and subprocess.run exit1
with permission denied at unix:///var/run/docker.sock. Version returns client
metadata only; image inspection[] is not image-absence evidence. Exact commands,
raw results and hashes are in SUBPROCESS-ACCESS-164363.md. Interpreter metadata
independently confirms3.13.7/jsonschema4.26.0.

This resolves the prior uncertainty about the Python-subprocess edge: it is
currently denied while the two standalone managed Docker commands succeed.
The direct-access success remains valid; no broad daemon/image failure follows.
The remaining ops prerequisite is the permitted supervisor launch boundary.
No escalation, alternate socket, tests, containers, builds, installs, candidate
changes or engine execution were attempted. Return to baton.ops for M163303.

This claim0.010592196005745791s; readiness0.1878712520102272/20s inside author68.58157983800454/120s,
remaining51.418420161995456s; all32 ledger rows retained, reviewer unchanged.
Engine180s and final acceptance/docs/Work/parent closure remain open.

## 2026-09-13T23:14:18Z — owner host-terminal execution selected and prepared

**Confirmed decision:** owner M164398 resolves obligation163303 by selecting
owner host-terminal execution of the final reviewed supervisor with
/home/sl/src/baton/.venv/bin/python3, jsonschema4.26.0 and immutable image
sha256:9b8c98820877e33d38d33352d86cc3810e5b72d4935a181b82b512b4d3291de8.
Return164405 assigns preparation of the exact bounded command and evidence.
Claim164414 prepares OWNER-EXECUTION-164414.md, owner-execute-164414.py and
execution-bindings-164414.json; the current PLAN names this action.

This explicitly supersedes earlier current requirements to leave the engine
allowance unactivated or await an answer to ops163303 before selecting execution.
The previously proposed180s allowance is now selected for one owner invocation,
starting0 spent. It neither resets nor transfers author/reviewer spending.
The managed Python-to-Docker denial remains an operational limitation recorded
in SUBPROCESS-ACCESS-164363.md; choosing the owner host does not repair it.
The previous standalone managed Docker success and owner-built image evidence
remain valid for their own boundaries. Owner build/content probes and prompt
metadata/hash checks are reused with their existing attribution, not presented
as a reviewer engine run or charged retroactively to this fresh invocation.

**Prepared, not executed:** all11 candidate163413 current hashes still match
manifest ecd8e311806a2b781f682a75adf396c888c31411bf931030b3c8ba1fad82b896.
Independent review-2026-09-13T20-28-07Z.md and unchanged engine-gate.py digest
a729a7ce7b086444d54a9b73f4ea375c1ee9f4f637a3953033fa23251d244bc2 are retained.
The owner launcher digest is
b4efaf50d6df462cbf770bb26c8ddb9851e44c3b711e767e2a30c86fd4d2a2ef;
execution-bindings-164414.json digest is
fce9420fa1bc442c4cde748146b2bad73d58a15adab0684c4f3af89695b6e836.
Bindings additionally cover the inherited lifecycle fixture, manager inputs,
dependency pin and worker build inputs. DEPLOYMENT is not an execution input
and remains under W161230 ownership pending the agreed fresh-hash handback.

The packet gives one absolute-path command, a fresh non-reusable evidence
directory and a177s outer watchdog with1s kill grace, leaving2s margin within180s.
The reviewed supervisor retains120/5/50/5 phase bounds. The wrapper records the
exact command, raw exit and monotonic elapsed/remaining allowance. A timeout,
interruption or overrun is not acceptance or proof of cleanup; preserve exact
evidence and return unresolved resources to ops without automatic retry or broad
cleanup. Provisional supervisor output and the owner receipt do not constitute
independent acceptance. Only subsequent review can assess the actual exit and
underlying proof. No live model/provider execution is selected.

No tests, Docker/API probes, runtime, image or install operations ran in this
preparation claim. Author68.58157983800454/120s (32 rows), remaining51.418420161995456s;
reviewer5.285408751995419/60s, remaining54.71459124800458s, are unchanged.
Readiness0.1878712520102272/20s remains included in author spending. Owner engine
execution is still0/180s pending the prepared command. Return to baton.ops for
owner execution, next baton.feat for independent assessment. Final pinned focused
verification, engine acceptance, DEPLOYMENT handback and Work/parent completion
remain open. This entry claims no engine gate pass.

## 2026-09-13T23:59:38Z — failed owner gate traced to exact absence-response mismatch

**Confirmed:** owner return164698 directs read-only diagnosis with no rerun or
container removal. Review claim164721 finds the supported Docker29.1.3 response
`Error response from daemon: No such container: <name>` differs from the
supervisor's accepted `Error: No such container: <name>`. All four final absence
responses therefore fail classification. The body test passed; the actual owner
supervisor exited1. The failed receipt/result and four unresolved resource names
remain unchanged. This is a supervisor defect; the retained responses are not
permission failures and are not a claim of current resource state.

Read review-2026-09-13T23-59-38Z.md for exact names, call sequence, hashes and bounded
correction/regression specification. All11 candidate hashes still match163413.
The sibling was positively identified and removed by immutable ID during the owner
run; no resource was touched by this review. Preserve all retained fixture evidence.

This explicitly supersedes the prior current no-further-correction assessment only
for the missing-container parser and its fake coverage. Earlier resolved P2 issues
and body evidence are retained; no retroactive gate pass is granted. **Proposed**
correction is confined to engine-gate.py and its budget test module, with exact
real-response replay and refusal protections, followed by independent review.
Return diagnosis to baton.ops; no new engine execution or removal is assigned.

Engine cumulative30.81015891599236/180s, remaining149.18984108400764s. Author remains
68.58157983800454/120s and reviewer5.285408751995419/60s; no verification child ran
this claim. Readiness0.1878712520102272/20s remains inside author spending.
Pinned focused verification, successful complete engine gate, DEPLOYMENT handback
and Work/parent acceptance remain open; obligation163303 is already answered.

## 2026-09-14T00:07:53.283177+00:00 — owner-authorized parser correction, claim164779

Owner reroute164775 accepts the bounded correction from review-2026-09-13T23-59-38Z.md. This supersedes the diagnosis-only/proposed-next-action status for this correction. baton.tuner owns only engine-gate.py and v12/python/tests/manager/test_runtime_deadline_engine_budget.py, plus dossier evidence. Recognize exact supported absence diagnostics with exit1 and empty/[] stdout; replay retained responses and preserve refusal, identity and uncertain-creation coverage. Focused deterministic verification uses the existing author ledger. No engine rerun, Docker/API action, container removal or product/shared-file edit is authorized. Original owner failure, evidence and cumulative engine spending remain unchanged. All11 candidate and five protected hashes match candidate163413 before editing. DEPLOYMENT.md, owned by W161230, has drifted to efb5cb8d24b7c2f7afb4592078f5fe7c9aed7faf27656437bf6172aa21198b86; record protected-drift-164779.json and leave it untouched. preservation-164779.json binds original owner evidence.

## 2026-09-14T00:10:21.849221+00:00 — absence parser correction prepared

Owner reroute164775, baton.tuner claim164779: bounded correction prepared for independent review. inspect_owned now accepts exact Docker daemon and explicitly supported short absence diagnostics, exact requested name, integer exit1, and empty/[] stdout after surrounding whitespace normalization. Byte comparison rejects invalid encodings and additional diagnostics. Generic nonzero failures remain failures. No identity, removal, uncertainty, process, duration or completion rules changed.

The fake Docker now emits the retained real prefix. Three new test methods cover both supported variants before/after immutable-ID removal, 21 refusal combinations, and digest-bound replay of all six actual parent responses through the real Calls/Inventory/cleanup code with an injected runner. All prior33 cases remain. Focused pinned verification passes36 tests in verification-162766-33.log (Python3.13.7/jsonschema4.26.0). Only this deterministic module ran; historical product/deadline/no-start evidence was not rerun.

Author cumulative 68.89533569900784/120s, remaining51.104664300992155s, 33 ledger rows. Reviewer5.285408751995419/60s, remaining54.71459124800458s. Readiness0.1878712520102272/20s is already included in author spending. Owner engine30.81015891599236/180s, remaining149.18984108400764s. No reset or transfer.

All44 original owner evidence files still match preservation-164779.json, including the failed receipt, result and body log. The original exit1, candidate_pass=false, independent_acceptance=false and four unresolved names remain unchanged. Replay proves classifier behavior on historical observations only; it is neither current resource absence nor retroactive gate success. No Docker/API call, container removal, engine rerun, install, build or real child process was executed by the focused tests.

The other nine candidate files and five protected source/test files match candidate163413. DEPLOYMENT.md remains W161230-owned and untouched here; observed hash efb5cb8d24b7c2f7afb4592078f5fe7c9aed7faf27656437bf6172aa21198b86 differs from the prior protected hash (protected-drift-164779.json). Exact W161230 handback remains required before later documentation edits. Scoped git diff --check passes. Repository-wide check reports unrelated trailing whitespace at v12/python/tools/stage_execution.py:1909; left untouched.

Next baton.feat independently reviews this correction and remaining acceptance. Original owner-execute-164414.py is consumed and must not be reused. Any later engine assignment must explicitly account for remaining149.18984108400764s, update reviewed execution bounds/provenance for this candidate and resolve the managed subprocess launch boundary or select an owner execution. The unchanged supervisor maximum180s does not itself fit the remaining bank. No further runtime authority is implied. Obligation163303 is answered; do not reopen it. Successful complete engine acceptance, required remaining pinned verification, DEPLOYMENT handback and W32577/parent closure remain open.

This supersedes the current parser-defect implementation state only; independent review and complete acceptance are pending.

## 2026-09-14T00:12:24Z — independent acceptance of exact absence-parser correction

Claim164827 accepts candidate164779 after return164823/owner reroute164775.
Read review-2026-09-14T00-12-24Z.md. All11 current/snapshot hashes match manifest
ea2cb3557d8ac87b8198ec5bd5cc9c35545a550c0c9a8e53b3b2da11323902e5; exact two-file
patch matches snapshots, nine predecessor files and five protected sources/tests
unchanged. DEPLOYMENT remains W161230-owned. All44 original owner evidence files
match before/after review verification. This explicitly supersedes the outstanding
parser correction/awaiting-review state for these bytes; historical failure remains.

Independent pinned3.13.7/4.26.0:36 deterministic budget/classifier cases pass with
warnings as errors, including six-response retained replay and strict refusal
coverage. Reviewer child0.3640428889921168s, cumulative5.649451640987536/60s,
remaining54.350548359012464s in review-ledger-164827.json. Author33 rows sum to
68.89533569900784/120s; engine remains30.81015891599236/180s,
remaining149.18984108400764s. Readiness spending remains included in author.

Pass to baton.ops nextfeat for a concrete remaining-budget execution assignment.
No engine rerun/removal is authorized by164775, and none occurred. An unchanged
180s supervisor maximum exceeds the remaining engine bank; follow-up bounds must
preserve cleanup/reaping and launch/output margins rather than merely truncate an
outer watchdog. The consumed owner launcher is not reusable. Obligation163303
is answered. Replay is neither current absence nor retroactive engine acceptance.
Remaining pinned product verification, complete engine acceptance, DEPLOYMENT
handback and Work/parent completion remain open. Reviewer dossier changes only.

## 2026-09-14T09:09:48Z — owner selects fresh corrected-supervisor packet

Prompt explained the accepted parser correction, the still-failed original
engine receipt, the obsolete remaining-bank obstacle and the recommendation to
return for fresh execution packet preparation. Slawomir replied "I approve".
Prepare one fresh single-use packet for the owner host-terminal boundary using
accepted candidate164779 and the existing180s per-run supervisor limit.

This supersedes the previous requirement to fit that new180s run inside the
old149.18984108400764s arithmetic remainder, and the pending follow-up-assignment
disposition. Keep the original30.81015891599236s charge and failed evidence
unchanged. There is no retroactive pass, erased cost or proof of current resource
absence. Preserve per-run phase limits, cleanup/reaping reserves and launch/
output margins; do not shorten the watchdog merely to satisfy historical sums.

Revalidate and bind current accepted supervisor/candidate, pinned interpreter,
immutable image and inputs. Create a new wrapper/evidence destination rather
than reuse consumed owner-execute-164414.py. Any substantive supervisor changes
need bounded implementation and independent review before execution. Present
the exact host command to Slawomir; this preparation does not run Docker or
repair the managed Python-to-Docker permission boundary. No unrelated image
build/pull, broad suite, live model or cleanup operation is selected.

After the owner run, assess actual supervisor completion and captured results,
then finish the remaining pinned product verification and documentation before
Work acceptance. M165203 records the later DEPLOYMENT handback; revalidate its
current ownership/bytes rather than treating the old pending-handback statement
as a new owner gate. Obligation163303 remains answered. Prompt records and
coordinates this selection without claiming Work or acting as reviewer.


## 2026-09-14T09:26:52Z — fresh owner packet prepared, claim167993

Owner reroute167900 selects the fresh packet under the09:09:48Z ruling.
OWNER-EXECUTION-167993.md supplies the exact host command, current provenance,
limits, evidence destination and remaining acceptance. All20 candidate/input
hashes match; all44 original evidence files remain unchanged. The corrected
supervisor remains SHA256980911451d33acfae889a09c4ec519b355267e6466b0138e60575587bfb77a8e.
Wrapper SHA256 15458d98811bee08c75f3cbbd3db730dfe9f720e4f2d513f0c3dcaa6086e84f4;
bindings SHA256 3e3e2520cca28eeb13a46a7ee4ceab55b3b54ab26fd8b21c7ff27371da71ec91. The wrapper is parsed/source-inspected, not
executed. Fresh owner-execution-167993 does not exist. packet-delta-167993.patch
shows the new identity, stronger interpreter binding and separated historical
accounting; execution/cleanup controls remain unchanged.

Current interpreter is3.13.7/jsonschema4.26.0; standalone read-only exact image
inspection confirms immutable ID/entrypoint/user, recorded with attribution in
environment-observations-167993.json. Reuse existing build/content evidence.
No managed subprocess-Docker repair, engine execution, current container absence
or independent engine acceptance is inferred. No model/image mutation/install.

M165203 handback revalidated: DEPLOYMENT matches
971fba687461bf4cc0c8899b5f692d086cad3af8cd794573b2004cee1f0a7f94 and belongs
to W32577 for its selected docs. This supersedes earlier pending-handback
wording as current action. Main docs are untouched in this preparation.

Return to ops for the selected single host invocation, next feat for actual
evidence assessment. The old149s remainder is superseded as an obstacle;
180s per-run and120/5/50/5 phases remain, with177s outer+1s grace+2s margin.
Historical failed engine30.81015891599236s, author68.89533569900784s and reviewer
5.649451640987536s remain unchanged; no verification child here. Read-only
metadata durations were not independently measured and are not asserted zero.
Original failed receipt and unresolved resource names remain historical facts.
Remaining pinned verification/docs and Work/parent acceptance are still due.

A pagination retry combining after/before returned older events (before takes
precedence); the omitted owner correction text was read from that output.
This was a query-shape misunderstanding, not missing handoff authority.

## 2026-09-14T10:31:10Z — engine evidence and pinned product verification accepted

Independent baton.codex claim168446 assesses owner return168443 in
review-2026-09-14T10-31-10Z.md. Owner execution167993 is accepted for the scoped
real-Docker crossing: actual exit0 in30.81214400099998s, passing body, settled
owned process group, four exact resolved names and no cleanup errors. A real
cooperative stop timeout is retained before successful exact force-removal and
positive absence. Provider teardown, retained partial output, sibling preservation,
lane release, Authority-gate discharge and replay assertions all pass. The manager
clock and Authority/agent remain deterministic fixtures; this is real-engine
coverage, not live-model or production-Authority evidence.

All11 candidate files/snapshots and21 execution bindings still match accepted
candidate164779. evidence-assessment-168446.json binds all44 new owner artifacts;
all44 original failed-run artifacts remain unchanged. Original exit1/resource
uncertainty is not retroactively resolved. Provisional result/stdout and both
owner receipts are preserved; independent acceptance lives in this review.

The required pinned product matrix now passes817 focused deterministic tests
with Python3.13.7/jsonschema4.26.0 and warnings as errors. Guard, exact selectors,
full log and elapsed9.921742420992814s are retained in verification-168446 files.
Reviewer cumulative15.57119406198035s; author68.89533569900784s unchanged. Engine
total61.62230291699234s includes both failed and successful runs. Read-only audit
time is not separately measured. Standing2026-09-14 development-time policy
supersedes older cumulative-bank gates, preserving costs and per-run boundaries.
The prior inherited global inventory gap remains qualified, not declared fixed.

This explicitly supersedes pending actual-engine assessment and pinned product
verification as current requirements. Documentation and final Work acceptance
remain. M165203 DEPLOYMENT handback/current hash are revalidated; assign the
selected documentation insertion to baton.tune and independently review its
exact delta next. No product/test/supervisor rework or engine rerun is indicated.
PLAN names the final bounded action; W32577 and parents remain open.

## 2026-09-14 — final documentation revalidation, tuner claim168487

Pass168483 selects publication in DEPLOYMENT.md plus attributable dossier records.
The complete Work events, T32577, FINDING/PLAN/PROGRESS and newest review were read.
M165203's released base still matches SHA256
971fba687461bf4cc0c8899b5f692d086cad3af8cd794573b2004cee1f0a7f94; all11 accepted
candidate164779 files and five protected source/test files also match. Tuner takes
only this documentation path; the existing managed sections will remain byte-for-byte
unchanged. documentation-168487-base.md preserves the exact pre-edit document.

Current attempts.py/deadlines.py/intake.py/authority_port.py confirm the draft's
public calls and semantics. Clarify that omitted deadline_policy selects None
and cannot silently reuse an earlier non-None selection; observe_deadline refuses
an unconfigured attempt, and advance_deadline requires a committed observation.
Explicit orchestration supplies those calls; no deployed timer is added. Document
the accepted cooperative-failure recovery through the exact replayed Authority
fence, retained output, unresolved cleanup holds and separate lane/gate settlement.
This is publication of the existing ruling and reviewed behavior, not a new
product decision. No source/test/supervisor edit or execution rerun is selected.

Operational reading note: an initial search mistakenly named nonexistent
worker_manager/authority.py and reported that path unreadable (ENOENT). The actual
port owner was found at worker_manager/authority_port.py and read successfully;
no required input remains unread. No missing-file or product defect is inferred.

## 2026-09-14 — deadline documentation published for review, claim168487

DEPLOYMENT.md now appends109 lines of deadline guidance, including public examples,
immutable selection, explicit observation/advance, cooperative-failure recovery,
retained output, uncertainty and separate settlement. All existing document bytes
and mode are preserved. HANDOFF-168487.md and documentation-168487.json bind the
exact base/candidate/patch; candidate SHA256
48a3268e456765c02696c897558f1aed9511c39a4188480a8d194b21ac50077f.
The old dossier draft remains historical, including its superseded ownership
heading; it was not copied into deployment instructions or rewritten.

Both Python snippets parse and match public signatures; current source semantics
were read, all11 accepted candidate and five protected source/test hashes match,
and scoped whitespace passes. No product/test/supervisor changes or test/runtime
rerun occurred. The static check measured0.009850611997535452s; prior author test/
readiness68.89533569900784s, reviewer15.57119406198035s and both engine runs totaling
61.62230291699234s are retained. Other read-only inspection time is unmeasured.
Review168446's817 pinned tests and scoped engine acceptance remain applicable;
inherited inventory gaps and managed Python-Docker limitation remain qualified.
Publication is complete, superseding the pending-docs state above. Final independent
documentation review and Work/parent acceptance remain open.


## 2026-09-14T10:44:34Z — final documentation accepted; W32577 complete

Independent reviewer claim168542 accepts review-2026-09-14T10-44-34Z.md against tuner
return168528. DEPLOYMENT candidate48a3268e456765c02696c897558f1aed9511c39a4188480a8d194b21ac50077f
adds109 lines while preserving all88436 prior bytes and mode0664. Both examples
parse/match public signatures; exact patch, all16 accepted/protected paths and
five prior acceptance artifacts match. documentation-review-168542.json records
the independent checks. No documentation or product correction remains.

This explicitly supersedes the pending final-review/Work-acceptance state above.
Together with review168446's817 pinned tests, prior36 supervisor/parser cases
and accepted real-engine execution167993, selected W32577 is complete and is
ready for canonical satisfying closure. Original failed evidence, inherited
inventory gaps and managed Python-Docker limitation remain preserved/qualified.
No rerun or wider acceptance is implied; parent W32382/W3/W2 remain independently
open. Git/index/history remains owner-controlled. Test spending is unchanged;
this static check adds separately measured0.008950860996264964s. Reviewer edits
only dossier records/evidence, never PROGRESS or product/test bytes.

Canonical closure168561 completed with satisfying outcome. Detail at snapshot168562
confirms status closed, Handler/claim/Route cleared and W32382 still open. The
prior ready-for-closure sentence records the pre-act review decision; closure is
now complete. No other Work was closed or rerouted.
