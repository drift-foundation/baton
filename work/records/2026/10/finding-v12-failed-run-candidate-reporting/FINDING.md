# V12 failed-run candidate and effective-timeout reporting

## 2026-10-18 — owner selects next useful v12 development Job

Owner accepts scheduling a bounded reporting correction through v12 after
W319114. Distinguish unsuccessful execution from absent retained artifacts,
report the effective configured provider timeout, and expose the retained
candidate locator when a failed attempt produced one. Do not relabel a failed
attempt successful or manufacture independent acceptance/verification.

Observed evidence: W319114 review-2026-10-18T02-50-40Z.md and
review-2026-10-18T07-32-54Z.md in
baton:work/records/2026/10/finding-v12-status-concurrent-submission/.
Both actual runs timed out but preserved sealed candidates. The single-implementation
supervisor baseline.py workload collector skipped noncompleted dispositions before
inventorying artifacts, reporting no proposal. The provider result publisher used
the default3600 seconds instead of the effective600/900-second bounds. Revalidate
these exact locations and current behavior before implementation.

Required behavior: accurately distinguish completed/failed execution, retained
candidate availability and verification/acceptance state. Inventory/locator output
must derive from validated retained artifacts; missing, malformed or mismatched
evidence must not become a claimed valid candidate. Preserve failure reason,
cessation/uncertainty and cleanup accounting, with no retry or automatic import.
Report the actual bound used for the attempt, including explicit versus default
selection where applicable. Do not expose credentials or raw provider transcripts.

Verification uses deterministic fake/replay boundaries and focused positive/negative
cases: successful candidate, failed attempt with candidate, failed attempt without
candidate, invalid custody/reference, explicit and default timeout. Implementer
chooses necessary files/tests; coordinate overlap and record actual ownership.
Stop after required focused/affected checks pass unless a concrete new concern
justifies more verification. No whole-suite expansion merely for reassurance.

Execute product development through an isolated v12 Job; v11 remains coordination
and independent-review authority. Prepare a concrete fresh execution packet from
an appropriate committed base; owner retains live-run selection and Git ownership.
No live invocation is authorized merely by scheduling. Independent acceptance and
exact reviewed-byte integration remain required. Clean end-to-end completion is
desired evidence, never fabricated from a salvaged candidate.

Activity-based timeout semantics and a simplified launcher are deferred separate
enhancements, not part of this correction. Owner's earlier timeout direction is
preserved: activity should generally distinguish a working worker from an idle
one; this Work only reports the existing effective hard limit accurately.

## 2026-10-18 — reviewer revalidation and concrete packet, claim321530

Confirmed committed base3dcf6dc4bcee97e932d17c93ac13c5811b3af188 includes W319114.
Current baseline.py:_proposals (1771 onward) skips noncompleted disposition at1816
before load_manifest. Deterministic replay with W319114's actual second sealed
manifest behind the normal frozen-output/load seams yields proposals=[] and both
no-proposal messages, load_manifest calls0. This is simulated collector evidence,
not a new store/engine/provider run. Historical real sealed outputs remain at
W319114 evidence/diagnosis-319578 and evidence/review-321452.

Current claude_agent publishers at2123,2148,2258 write PROVIDER_SECONDS3600;
_invoke at3287 resolves self._bound(...provider_turn...) and supplies that to
_ran_provider. Existing real sealed results say timeout600/900 beside3600. No
need for another live run merely to reproduce either defect. Correct all affected
publisher shapes and use resolved timeout semantics already owned by the adapter.

Two finite suboutcomes form one operator reporting correction: truthful retained
artifact inventory and truthful effective bound. They are independently testable
but small, share result evidence and one acceptance consumer; separate live Jobs
would add coordination/verification overhead. Keep one bounded Job with explicit
tests for each; no dependency gates or child Work needed. Reviewer owns this dossier;
worker exclusively owns future isolated candidate, no host product edits.

TASK.md/prepare.py/OPERATOR.md and PREPARATION-PINS.json supply concrete proposal.
One fresh900s provider/30s verification/1500s total/60s cleanup, no retry. Required
focused test vector passes93 tests7.332s on current source with supported disk
fixture root; no broad suite. Disposable preparation stage/bootstrap/bind pass,
held_packet/imported-source checks pass; no Job submitted. Evidence/PREPARED-PREFLIGHT
records the disposable UUID/artifacts, not a selected live authority. No source
reconstruction needed: nominated base already exists in host Git history.

Neither old failed run is relabeled; the new worker must stop after focused checks
and return so formal verification can run. Exact new live selection remains owner
responsibility per M321528. Source/worker image reused unchanged; modifying future
supervisor/adapter bytes does not modify the running supervisor or image.


## 2026-10-18 — owner selects prepared execution

Owner directs W321528 to move on after packet preparation. Select the one fresh execution in OPERATOR.md at base3dcf6dc4:900s provider,30s verification,1500s total,60s cleanup, no automatic retry. Owner runs preparation/start commands. This supersedes pending-owner-selection wording for this packet only; independent review and separate integration remain required. No outcome or successful authentication claimed by this selection.


## 2026-10-18 — selected run timed out; retained candidate for review

Owner reports held outcome in /home/sl/baton-instances/failed-reporting-w321528-321530/packet/outcome.json. Prompt read outcome906.785s, exceptional/unable, exact attempted-runtime cleanup absent, empty uncertainty/outstanding cleanup. Sealed result explicitly confirms timeout900s and retains head2c89d3aa1c3ccf190a47417f3147593b694948dd over3dcf6dc4, changing claude_agent.py, test_claude_agent.py and single-implementation-proof/baseline.py. Formal verification null; no acceptance or successful runtime claim. Current runner/image remain old as expected; their old diagnostics do not establish whether candidate fixes failed. Next independent review verifies artifacts, exact code and focused tests, and diagnoses provider activity despite the explicit focused-stop instruction. No retry or integration selected.


## 2026-10-18T08:07:31Z — independent review requests collector completion

Reviewer baton.rvpc, claim321731. Candidate2c89d3aa1c3ccf190a47417f3147593b694948dd over3dcf6dc4bcee97e932d17c93ac13c5811b3af188. No integration approval.


See review-2026-10-18T08-07-31Z.md and evidence/review-321731. Timeout changes pass focused review; collector still skips noncompleted results before loading manifests.110 focused tests pass after correcting a missing immutable fixture in the reviewer extraction. Provider activity shows unfinished collector investigation, not whole-suite expansion. Keep one bounded correction milestone; preserve failed outcome, sealed candidate and null formal verification. No new live execution or integration selected.


## 2026-10-18 — collector correction reviewed under claim321981

review-2026-10-18T08-39-00Z.md requests real retained-custody validation and actual producer-shaped verification/acceptance reporting. Matching metadata currently labels a nonexistent locator valid; ordinary tests are read from the wrong level and wrong key; acceptance none is assumed.74 focused tests pass but use doubles that miss these boundaries. Corrected hashes and unchanged timeout hashes verified. Preserve prior failed run, null formal verification and historical pins. Ordinary correction continues in isolated candidate without new live execution.


## 2026-10-18 — M322087 execution hold and review claim322120

review-2026-10-18T08-56-00Z.md records35 passing collector tests, verified candidate hashes and surviving custody blocker: line attribution reads commit headers, not retained artifact bytes. Verification shape/no-status and unobserved acceptance improve prior P2 findings. Owner M322087 supersedes immediate correction execution: wait for W321688 clean acceptance and actual human checkpoint, represented by separate owner gate W322125, then rebuild/revalidate packet from committed base and execute product correction through v12. Preserve all candidates; none newly accepted. No earlier packet executable after base change, no new live grant.

## 2026-10-18 — owner parallel priority, poke324037

Owner directs current-base packet and file ownership coordination for W321528
alongside W321689, preserving real gates and independent review, and requests
actual Job/attempt IDs when launched. W321689 alone has the direct-completion
exception. Current AGENTS requires v11 preparation and isolated v12 executable
work with no general direct fallback; existing live-selection boundaries remain.

Confirmed: W321528 gates are closed satisfying; Claude actively holds W321689;
baton.codxpc is idle and configured for baton.codx. Select that endpoint for
parallel packet preparation without taking over Claude's claim. Current PLAN
records disjoint product paths, retained-candidate provenance, current committed
base and return to independent review. No product changes or launch occur in this
coordination turn. The old waiting statement is superseded by satisfied gates,
not by removing them. No new decomposition needed for the bounded reporting fix.

Full open graph at snapshot324048+ and queued-tree inspection identify W321780
as an additional independently reviewed packet awaiting owner disposition and
human dossier checkpoint, not another ready product execution. W321776 still
requires W321528/W321780; W321690 still requires W321689. No other queued product
packet was found; parked work is not silently activated to inflate parallelism.

## 2026-10-18T16:13Z — current-base preparation independently accepted

Review `review-2026-10-18T16-13-41Z.md` accepts exact preparation-324054 inputs
for the existing owner live-selection boundary, after committed runtime/input
hash checks and reconstruction of all five retained patch files. This supersedes
the packet-preparation-pending checkpoint only; product custody/task-association
defects and independent acceptance remain open. No new Job/attempt was launched,
no product implementation/test occurred, and no dependency changed. Current PLAN
pins exact packet digest, commands/limits and continued v12-only execution.


## 2026-10-18 — owner live selection M324176, claim324180

Owner authorizes exact preparation-324054/OPERATOR.md execution accepted by
review-2026-10-18T16-13-41Z.md, manifest SHA256
c56d0605201b1b76be0d7292e959f17435dfc76cfa91657287d54395f9adceb0.
One fresh invocation:900s provider,30s verification,1500s total,60s cleanup;
no retry. This supersedes pending-live-selection wording for this packet only.
Preserve W321689 ownership and return actual retained result to baton.bug.
All seven packet hashes revalidated before preparation. Current HEAD6348161e
differs from selected base d0b211b4; selection explicitly binds d0b211b4 and
staging reads its committed objects, not HEAD or concurrent working changes.
No live outcome inferred; record actual execution identities after submission.


## 2026-10-18 — selected execution blocked by managed filesystem

Claim324180 attempted the exact selected stage command. prepare.py:55 failed
at root.mkdir with OSError errno30, read-only filesystem, for
/home/sl/baton-instances/failed-reporting-w321528-324054. Target remains absent.
This is an operational policy blocker before staging, not a provider failure or
spent invocation. No Job/attempt exists; bootstrap/bind/start were not reached.
Evidence: evidence/execution-324180/PREPARATION-BLOCKER.json. Resolve the exact
managed execution boundary or have the authorized operator execute the reviewed
commands. Preserve M324176 selection and packet; no new product decision is
required, no alternate location or direct implementation fallback selected.

## 2026-10-18T16:26Z — independent operational routing

Review `review-2026-10-18T16-26-20Z.md` confirms the owner live selection and
independently observes the selected target absent. Route the existing Work to
baton.ops for execution access repair or authorized operator execution, preserving
the unconsumed selection and exact packet. This is an operational repair, not a
request to reapprove scope or a fallback to direct product implementation.

## 2026-10-18T16:31:54Z — operator-launched v12 execution observed

Owner confirms running the provided exact OPERATOR commands. Prompt preflight found the selected destination already populated and did not launch or retry. The packet-generated supported status command reports Job `job-failed-reporting-w321528-324054`, implementation episode1, attempt `attempt-ba6a05f353081045b7c70347e80d6d7b626ce8b357a9074a2537cdc62eeb0ffd`, v12 Work `9e8e5b4a-W1`, authority `9e8e5b4a898d45858bec0df1d6b1714f`. Stage and runtime are running; exchange work is dispatched/working, terminal absent. Runtime ID `55c5cdabc3ecc5d8d4f54260912bd32cee819d266b943c10677d11cf63f78391`. This supersedes the prior not-launched observation; it is not completion or acceptance. Retain original one-invocation limits and review the immutable result after cessation. Operator owns the active supervisor; no second invocation or claim takeover by prompt.

## 2026-10-18T16:46:26Z — operator run retained held, no proposal

Prompt read the operator-reported `/home/sl/baton-instances/failed-reporting-w321528-324054/packet/outcome.json`. The selected Job stopped exceptional; its sole attempt ended unable and published no proposal. Outcome reports 907.576 served seconds, effective provider limit 900 seconds, runtime destroyed and exact runtime identity absent, with no uncertainty or outstanding cleanup. These are retained supervisor observations, not independent acceptance. Provider stdout is empty; stderr contains only the warning that no stdin data arrived in 3 seconds. The root cause is not established by these logs; elapsed time alone does not prove a provider timeout cause.

This supersedes the running and unconsumed-selection checkpoints. The one invocation has been consumed; no retry is authorized by the original selection. Next: managed reviewer diagnoses the retained execution and determines a bounded correction/continuation packet. Work remains open, queued at baton.ops (episode324199); no route or claim changed by this observation. No accepted candidate is available for integration or product commit.
