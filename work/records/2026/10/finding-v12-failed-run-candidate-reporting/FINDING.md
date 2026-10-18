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

## 2026-10-18T16:51Z — independent retained-artifact correction

Reviewer claim324431 found retained candidate6132a4fb989c0518fa0f485cfc93071fadb9ef45, bundle and patch despite supervisor omission. Structured result explicitly reports timeout900s with stale seconds_bound3600; this supersedes preliminary no-proposal and timeout-unproved statements. Underlying stall cause remains unknown; empty stdout/no-stdin warning does not prove authentication failure. Fresh exact Docker inspect reports absent; retained outcome confirms destroyed/no uncertainty. Evidence copies/digests in evidence/review-324431/, review-2026-10-18T16-51-00Z.md. Only baseline.py changed from correction322059; adds artifact measurement, but exact task association remains deficient and tests unchanged. Preserve partial work, prepare fresh v12 continuation under unchanged scope and independent review; original invocation spent, no retry selected. W321776 gate remains.

## 2026-10-18T16:58Z — continuation packet independently accepted

Review review-2026-10-18T16-58-00Z.md under claim324502 accepts preparation-324477 manifest7807bfe731322257c60bd8fdee4b96a50832f92fc0c7a54544baaad0d9e9e25a for fresh execution selection. All packet/runtime/generated hashes and full five-file retained6132a4fb patch reconstruction match; evidence/review-324502/CHECK.json. Basefba1a7fc, new identity/destination absent, unchanged scope and limits. This supersedes preparation-pending status only, not product defects or acceptance. Prior run spent; no new execution or auth proof. Return concrete OPERATOR commands for owner selection, then v12 correction and independent exact-byte review.

## 2026-10-18T17-35-03Z — repeated timeout diagnosed from retained native activity

review-2026-10-18T17-35-03Z.md records selected run324477 held after900s, retained1bb8c162, exact runtime independently absent. Native transcripts show79/66 tool calls through near both cutoffs, superseding the earlier unknown-stall characterization insofar as active implementation/test work is now observed. No credential/hang claim or timeout increase is justified. Only baseline.py advanced; copied retained candidate tests35/14fail. Preserve all inputs and prepare a bounded correction packet using this exact checkpoint and diagnostic evidence, without launch. Product acceptance and W321776 gate remain open.

## 2026-10-18T17:38:47Z — owner revises proposed continuation allowance

Poke324810 pinned in OWNER-CONTINUATION-324810.md: proposed3600s provider and adjusted supervisor total (reviewer proposes4200s), separate30s formal verification/60s cleanup, supported context reuse preferred, no launch. This supersedes unchanged900s/1500s instructions for next preparation only. Exact spent packets were fresh and unconfigured for managed context; native logs are not a finalized reusable generation. Preserve exact retained candidate. Preparer must report supported reuse or concrete blocker; independent packet review and execution selection remain.

## 2026-10-18T17-39-37Z — packet324799 predates owner steering

review-2026-10-18T17-39-37Z.md confirms all11 input hashes, but900s/1500s fields and absent explicit reuse assessment are superseded by poke324810. Return bounded revised preparation; preserve retained candidate and old packet, no launch or product rework.

## 2026-10-18T17:44:45Z — interrupted-session recovery deferred, successful reuse retained

Owner poke324905 pinned at baton:work/records/2026/10/finding-v12-development-coordination-pilot/OWNER-INTERRUPTED-SESSION-RECOVERY-324905.md. Interrupted-provider-session recovery is deferred and does not gate current3600s continuations or native coordination cutover. Successful-turn context reuse remains required for v12. Preserve all findings/evidence and candidate checkpoints; revisit if longer runs show material interruption loss. This supersedes any broader gating interpretation of earlier reuse investigation, not its facts. No launch authorized; existing claims/dependencies unchanged.

## 2026-10-18T17-46-55Z — revised continuation preparation accepted

Claim324932 verified preparation324881, manifest f881a33e432e371be3919da192b9f3674edbdf7d128c076e5a6324b32b594bd4. Exact retained candidate preserved;3600/4200/30/60 limits accepted for selection, no launch. See review-2026-10-18T17-46-55Z.md and evidence/review-324932/CHECK.json. Owner324905 interrupted-session deferral applies; successful-turn reuse remains in target.

## Startup comparison for owner poke324949

W321528 preparation324881 is unaffected by the confirmed argument-size blocker in W324214 run324832. Exact committed _prompt composer produces117830 UTF-8 bytes (117831 including NUL), versus195345 (195346 with NUL) for visibility. Same-host inert /bin/true with the exact prompt succeeds for reporting and raises errno7/E2BIG for visibility. Observed single-argument ceiling131072 including NUL leaves13241 bytes for reporting. This proves only this boundary, not authentication or future provider success. Visibility retained only OSError, so its historical errno remains inferred; its exact runtime is absent and no candidate was produced.

Compared generated implementation deployments: identical image digest c862c055c6430addc918ca078a9e4d55f6bd8173ed9c9878a8ad9d6cad334ca2, adapter, engine, bridge network, profile, credential-source reference (no secret read), workspace capacity and launch contract. Both select the same image/CLI; identity-bound authorities, roots, tasks, manifests differ as expected. Reporting comparison uses its reviewed disposable preflight because no live target is selected. Task size is the discriminating startup input; same image does not make every task exceed argv limits. Worker _provider puts the prompt in one argv member and catches OSError without errno.

Evidence: evidence/poke-324949/COMPARISON.json; W324214 review-2026-10-18T17-48-31Z.md and evidence/review-324945. Revalidated every accepted packet input; manifest f881a33e432e371be3919da192b9f3674edbdf7d128c076e5a6324b32b594bd4 unchanged. Retained1bb8c162 unchanged. No launch/live probe/credential read/product mutation; existing independent packet acceptance stands for owner selection, no new dependency or recovery gate. Visibility correction separately passed E324958.

## 2026-10-18T19-28-47Z — retained completion and independent correction review

Reviewer baton.rvpc claim325674, owner diagnosis E325666 and selected run M325175. Candidate0addd2afca3c4ebe3a4cec9f2936791f58a6591d on base372281f4a473300efb474d5a6573954c15ade367. Exact five changed paths and custody hashes in evidence/review-325674/CANDIDATE.json; copies of all five blobs retained there. Worker/worker-test bytes equal prior1bb8c162; this continuation advances baseline.py and its two tests. No shared-tree product edits or launch this review.

## Execution and independent verification

Job job-failed-reporting-w321528-324881, attempt-56140519173556c244266696f80af267a5f5b2cc0fb174ade98283f6d81a0fd3, authority6b911555f47649f5ad9bae9abbbaa3b6. Provider status0, bound3600; formal verification status1, held/exceptional/unable, served1457.303273567s. Retained candidate is not a published proposal or accepted delivery. Runtime3351059123e9baca191a95511819da2f1959c9c1b63ebb3382a00df2de3c6e1e independently absent via docker inspect exit1/no such object; supervisor uncertainty/outstanding cleanup empty. Invocation spent, no retry selected.

Materialized exact candidate Python source/tests and required vector input via read-only Git objects into /var/tmp/baton-w257624/w321528-review325674-o0loc2uw. Credential-free explicit environment, ordinary filesystem TMPDIR default, supported disk root. Initial reviewer view omitted vectors.json:186 tests/31 errors in0.782s; this is reviewer preparation error, not candidate failure. Added exact candidate vectors input and reran the unchanged selected command:186 tests PASS7.688s (8.220848s wall). FOCUSED-COMPLETE.json/log bind command/environment. Fixture tests create private disposable Git histories; no canonical index/history mutations performed.

Then varied only TMPDIR to a directory descriptor path inherited by the initial command: same186 tests reproduce40 failures/20 errors7.145s (7.671801s wall), matching formal worker failure classes. FOCUSED-FD.json/log records exact input. Child subprocess closes fd and git cannot resolve /proc/self/fd/3/...; nested adapter _checked_directory also compares resolved path to lexical scratch and refuses. Current _pinned_environment/_verify deliberately pass descriptor aliases to the first verifier for anti-substitution protection; arbitrary descendants do not retain those descriptors. This is an existing environment compatibility defect, not provider timeout or absence of candidate, and not introduced by this candidate's worker delta. Independently recorded W325695 owns bounded diagnosis/packet planning; do not erase the isolation protection, broaden W321528 into an environment redesign, or create a reverse gate to W321776. Formal failure remains honestly recorded despite independent focused pass.

## Required reporting correction

Confirmed P1 at candidate baseline.py:_retained_bytes, `if not os.path.isdir(place)` around2511. os.path.isdir suppresses PermissionError. With a real retained artifact initially valid, remove search permission from its ancestor; os.stat reports EACCES13 but collector returns state=refused and says the process finds no retained tree / bytes are not where declared. This is false absence evidence when inspection could not answer. Required unreadable-versus-missing distinction is original accepted scope. The new unreadable test chmods only the artifact directory, which permits stat and reaches the walker, so it misses the inaccessible ancestor case.

Independent permission_probe.py and PERMISSION-PROBE.json reproduce this with real filesystem permissions as uid1000, using existing fixture doubles only for store/line attribution. Preserve locator, assignment and claims; distinguish actual missing/non-directory/malformed evidence from permission or other indeterminate inspection failure. Do not weaken real-byte/digest/task association checks. This is one bounded collector correction; no further split within W321528. Separate environment defect has its own Work because its ownership/acceptance differ.

## Handoff

- Outcome this turn: substantial retained progress,186 focused passes outside worker, exact formal failure reproduced separately; no product acceptance because unreadable ancestor still misreported.
- Confirmed blocker and location: _retained_bytes preflight isdir conflates inaccessible path with missing tree; exact independent evidence above.
- Required change: prepare fresh current-base continuation preserving exact0addd2af and diagnostic checkpoint, for this one reporting correction with real permission-denial regression. Preparation only through baton.codx; return concrete packet to baton.bug before execution selection. No relaunch of324881. Keep provider3600/total4200/verification30/cleanup60 proposal unless exact reviewed packet changes; no launch authorized. Review whether independent credential-free verification can be retained as candidate evidence without pretending worker formal success; preserve W325695 environment finding rather than weakening security to force green.
- Verification behaviors: valid real custody; actual missing/damaged/substituted versus inaccessible ancestor/root/file; exact task id/digest/argv; effective timeout publisher paths and no-status/unobserved distinctions. Existing186 focused passes establish the other tested behavior on this exact view, not universal correctness. Additional focused checks only for the concrete correction or execution-context question. No broader suite/live model required merely for tests.
- Handoff condition: exact reviewed continuation packet, retained provenance, supported execution route and explicit remaining environment limitation. Product correction executes through v12 after selection; independent review then human integration/checkpoint. W321776 remains gated on W321528 accepted delivery. Reviewer owns FINDING/PLAN/evidence; preparer owns new packet/PROGRESS; no sibling or child source ownership changes.

Accounting: formal worker186 tests6.972s; reviewer initial1.314968 wall, complete8.220848 wall, descriptor reproduction7.671801 wall, permission probe0.117399 tool wall. Preserve all earlier costs; no aggregate historical total asserted. No authentication probe, credential read, live engine/provider or retry this review.

## 2026-10-18T19-36-47Z — continuation packet independently reviewed

Preparation-325711 accepted for fresh owner execution selection; manifest ec793a20eff935ee45873a46b96171776ed80f88d2f5b91e42e42e98b2c918fb. See review-2026-10-18T19-36-47Z.md and evidence/review-325758/CHECK.json. Lossless reconstruction matches retained0addd2af all5 paths; composed50885-byte prompt passes inert exec, oversize control E2BIG. No launch or product acceptance. Unreadable-ancestor correction remains next; separate W325695 environment defect stays open. This supersedes the19:28 preparation-pending checkpoint only; spent-run evidence and W321776 gate remain.
