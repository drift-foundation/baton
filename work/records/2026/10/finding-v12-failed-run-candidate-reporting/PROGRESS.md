# Implementer progress — W321528

## Claim 321893 (baton.claude, impl) — the collector the review required

Read first: canonical `detail` at snapshot321892 (queued, unclaimed, routed
baton.impl, next baton.bug, no obligations, no open blockers, blocking W321776),
then the standalone claim; `work-events` complete, 321528 → 321893, `next_after`
null; `thread` T321528, both messages including W61981's overlap coordination.
Then this dossier's PLAN, FINDING, TASK, and `review-2026-10-18T08-07-31Z.md`.

### The defect, confirmed before correcting it

`_proposals` in the pinned supervisor skips every attempt whose disposition is
not `completed` **before** it reads the sealed manifest. That is correct for the
question it asks — a turn that did not complete published no proposal by
contract. It is the only question anybody asked, and the consequence is the one
this Work exists for: the selected live run of W321528 itself timed out at 900s
with a real three-file candidate retained on its private line, and the report
said the run retained nothing at all. An operator reading that would have
deleted a workspace holding the work.

The previous candidate `2c89d3aa` added 47 lines of well-chosen vocabulary —
`CANDIDATE_VALID/ABSENT/REFUSED/UNREADABLE`, the verification and acceptance
states, `PROPOSAL_OUTPUT` — and no implementation. The review proved zero
manifest loads. That vocabulary is exactly right and this correction implements
against it rather than inventing a second one.

### The correction

**`_candidates(control, implementation, packet, shortfalls)`** — asks the other
question for every attempt, whatever it ended as: is a candidate retained, and
does its custody hold? The four states are kept as four different answers:

- `absent` — the turn retained nothing. An answer, and the ordinary shape of a
  failure. **Not a shortfall.**
- `unreadable` — a read that did not answer. **Never** evidence of absence;
  conflating those two is what produced the original false report.
- `refused` — evidence that EXISTS and failed a custody check. Louder than
  absence: something is on disk and this program will not vouch for it.
- `valid` — the only one countable, and only after all three checks agree.

`valid` requires, none of it on the worker's word: the sealed result is this
attempt's (the manager bound that at `record_frozen_result`; re-read by attempt
id, with the assignment read back so an unreadable one is `unreadable` rather
than assumed sound); the sealed artifact reference and the manager's own
`output_artifacts` row agree on `artifact_id`, `content_digest`, `bytes` and
`locator` — two records of one artifact that disagree mean nobody knows which
bytes the candidate is; and the claim is offered against the deployment's
declared base with a head that is not its base.

**It is not a verdict.** `verification` reports what the turn's own verification
command did and `acceptance` what the line owner records. Neither is a formal
verification or an acceptance by anybody — this run performs none and invents
none. A `valid` candidate is exactly "these bytes are retained here and their
custody holds", and nothing about whether they are correct, reviewed or wanted.

**The two false sentences, corrected in place.** The noncompleted message now
says whether a candidate was retained anyway is a separate question that
`candidates` answers; the run-level one says "published no proposal at all"
rather than "retained no proposal at all", and names the distinction between a
retained candidate and a published, verified or accepted one.

**One product hardening I added deliberately.** `_candidates` bounds its
declared-base read wider than `SupervisorRefusal` — `_declared_base` opens and
parses the deployment config, so a malformed or absent document arrives as the
driver's own exception. A collector whose whole purpose is reporting what
survived a FAILED run must not itself die on an unreadable config and lose the
candidate it exists to name. Found by driving it: four existing `test_baseline`
cases double `_proposals` out and reached the new call with a minimal packet.

### Where the work lives — no host edits, no Git operations

`/home/sl/baton-instances/w321528-321893-candidate`, a plain directory copy of
the retained candidate checkout with `.git` removed. **No host product file was
edited and no Git operation of any kind was performed** — I cannot create a
commit, so the immutable candidate is delivered as digest-bound bytes plus
`correction-321893/correction.patch`, which applies to the sealed candidate
`2c89d3aa` and reproduces this correction exactly. `CORRECTION.json` carries
every digest.

`v12/worker/claude_agent.py` and `tests/manager/test_claude_agent.py` are
**byte-identical to the sealed candidate** — so the timeout portion the review
already accepted is preserved untouched, and the W61981 overlap the thread asked
me to coordinate is not touched at all.

### Measured

    test_candidates (new, 25 cases) ......................... PASS   0.001s
    tests.manager.test_claude_agent (timeout portion) ... 241 PASS  15.8s
    test_baseline ........................................ 49 PASS   7.0s
    the nine supervisor suites together ................. 222 run,
      6 failures, ALL PRE-EXISTING                              75.2s

The four required behaviours are driven at the boundary the review named:
failed-with-candidate (`AFailedTurnWithARetainedCandidate` — the case the live
run got wrong), failed-without-candidate (`AFailedTurnWithoutOne`), invalid
custody (`InvalidCustodyIsRefusedAndNeverCounted` — digest, size, id, locator,
either-direction index/seal disagreement, wrong base, head-is-base, unstated
claim, unreadable target), and successful (same path, same collector). Plus
`AnUnreadableReadIsNeverReportedAsAbsence`, which is the conflation itself.

### SIX RED RESULTS, PROVEN PRE-EXISTING

`test_successor_packet` and `test_successor_snapshot` pin `baseline.py`'s own
SHA256 as "this dossier's current supervisor". I ran those two modules **in the
sealed candidate's own retained checkout**: 44 run, the **identical six
failures**, 2.195s. They are an inherent consequence of the accepted scope —
this Work requires editing a digest-pinned supervisor — and not of this
correction. Re-pinning them is a separate decision about that dossier's
supervisor identity and I did not make it unilaterally; the reviewer or owner
should say whether the pins move with this delivery.

### Not claimed

No live provider, engine or container; no new live run or retry; no host product
edit; no Git operation; no integration. Formal run verification remains **null**
and the failed run's evidence is preserved untouched — a retained candidate does
not imply completed execution, verification or acceptance, which is the whole
point of the vocabulary this implements. I did not prepare a new live packet
because the remaining work was one specified function and doing it
deterministically spends no provider grant; the handoff permits either.

Cumulative verification this claim: about 98 seconds of measured deterministic
execution plus one comparison run against the sealed candidate.

A human Git checkpoint is due on acceptance, not this pass; the integration path
is the reviewed bytes, and Slawomir owns Git.

### Files

In `correction-321893/`: `CORRECTION.json` 17089178a99d, `correction.patch`,
`test_candidates.py`. Corrected bytes in the isolated tree:
`baseline.py` d5d1ec5150b3, `test_baseline.py` b10898c52a16,
`test_candidates.py` 716c9c46f50f. Unchanged from the sealed candidate:
`claude_agent.py` b014ea3f5f58, `test_claude_agent.py` 42191d077e41.
FINDING, PLAN, TASK, OPERATOR and the reviews are the reviewer's and untouched.


## Claim 322059 (baton.claude, impl) — review P1/P2/P2 corrected

APPEND-ONLY. Read: `detail` at snapshot322057, `work-events` after 321779
(events 321893→322059), `thread` T321528 both messages, then
`review-2026-10-18T08-39-00Z.md`, the current PLAN and FINDING.

Three findings, all three correct, and the first is the one that matters.

### P1 — I asserted custody without validating it

My `_candidates` compared the sealed reference with the manager's indexed row
and then declared `valid`. **Agreement between two stored descriptions
establishes that nobody disagrees, not that the bytes are there** — and my own
fixture named `file:/retained/proposal.bundle`, which does not exist, and got
`valid` with no shortfall. That is the same class of error as the defect I was
sent to fix: a report asserting something it never looked at.

Custody is now **read** at the supported boundary this file already owns.
`line_attribution` reads the commit object out of the durable line the manager
named, through the closed read-only verb list, outside any store transaction.
A candidate whose line does not answer is `unreadable` and never `valid`; a
substituted head, damaged parents, foreign authorship or a split
author/committer is `refused`. And **useful evidence survives a failed check** —
locator, base, head, digest and the assignment stay in the record, because an
operator hunting for the bytes needs them most when something is wrong.

The attribution is now whole too: `authority_uuid`, `work_id`, `participant`,
`principal`, `generation`, `effective_scope`. Before it was generation alone,
which could not say which authority or Work the retained bytes belong to.

### P2 — my verification reader did not match the producer

I read manifest-level `result_metadata` for an `outcome` key. The real producer
puts its observation on the **proposal output**, and `_ordinary_tests` emits
`task_id`, `task_digest`, `argv`, `status` and `base`/`head` — with `status` an
**integer or `None`**, and no `outcome` anywhere. So a real passing turn read as
`unreported`, and my unit tests invented the shape and passed while missing the
integration entirely. That is exactly the trap the reviewer named.

Corrected to the real shape, with four honest answers. `0` → passed, nonzero →
failed, **explicit `None` → `no-status`** — a new state, because the producer's
own docstring says a skipped command, a timeout and a failed start all emit
`None`, so calling that `not-run` would invent proof of whichever of the three
sounds most harmless. Missing, malformed or **unassociated** → `unreported`;
the observation's `base`/`head`/`task_id` must be this candidate's, because an
observation of something else is not evidence about this one.

### P2 — acceptance was assumed

The constants promise acceptance read from the line owner; I performed no read
and set `none` for every valid record. `ACCEPTANCE_UNOBSERVED` added and used:
this Job admits no reviewer and this supervisor consults no exact-candidate
acceptance evidence, so the honest value is that **nobody looked** — and that
stays distinct from this run's absent formal verification.

### Measured

    test_candidates ...................................... 35 PASS  0.002s
    + test_baseline + test_failure_path + test_no_progress
      + test_entrypoints + test_baseline_bindings
      + test_preparation ................................ 188 PASS 72.9s

Run with `BATON_V12_DISK_ROOT`, as the reviewer established is required.

**Not rerun, and said rather than implied.** `test_successor_packet` and
`test_successor_snapshot` pin `baseline.py`'s own SHA256 as the historical
supervisor identity and fail identically in the *unaccepted* sealed candidate
(44 run, same six failures, measured last claim). The review directs that
historical packet pins be preserved, that historical supervisor identity be
distinguished from corrected identity, and that a fresh packet needs fresh pins
— that pinning decision is the reviewer's or owner's, not mine to make
unilaterally. `tests.manager.test_claude_agent` was 241 PASS last claim and its
bytes are byte-identical here, so the review's own "no redundant timeout suite
rerun" applies.

### Delivery

Isolated candidate at `/home/sl/baton-instances/w321528-321893-candidate`;
`correction-322059/` holds `CORRECTION.json` cdfe8bbf4bcd,
`correction.patch` against sealed `2c89d3aa`, and `test_candidates.py`.
Corrected: `baseline.py` 652e91b05ebd, `test_baseline.py` b10898c52a16,
`test_candidates.py` 3ff58ec3e3e3. `claude_agent.py` and
`test_claude_agent.py` remain byte-identical to the sealed candidate, so the
accepted timeout slice and the W61981 overlap are untouched. No host product
edit and no Git operation of any kind.

### Not claimed

No live provider, engine or container; no new live run or retry; no
integration. Formal run verification remains **null** and the failed run's
evidence is preserved untouched. A retained candidate still implies no completed
execution, no verification and no acceptance — which is the whole point of the
vocabulary, and the reason `valid` now means "the bytes were read in the
manager's own line" rather than "two records agree".

Cumulative verification this claim: about 73 seconds of measured deterministic
execution.


## 2026-10-18 — claim324054 (baton.codxpc): current-base packet prepared

Read canonical detail324052; standalone claim324054 succeeded. Read complete
work-events321528 through324054 (pagination exhausted), T321528 through M322087
(all three messages, no continuation), current FINDING/PLAN and latest review
review-2026-10-18T08-56-00Z.md. Both dependency gates closed satisfying.
Revalidated HEAD d0b211b42f724c6747ebdcd8fc71885388579761 and its W321688 parent
433b09d6963ca9789700849b640e242e772b9867. Concurrent W321689 bytes are excluded.

Milestone delivered for review: preparation-324054/{OPERATOR.md,prepare.py,TASK.md,
PREPARATION-PINS.json,PROVENANCE.json,retained.patch,PREFLIGHT.json,PACKET-INPUTS.json}.
All five retained hashes match correction322059. The four existing source paths
are byte-identical across previous/current bases; the new test path is absent in
both. Full patch dry-run passes. Frozen manager110 files and supervisor3 files
come from committed objects, not the dirty checkout. The normal task input embeds
the exact continuation patch and the remaining real-custody/task-association
requirements. No candidate bytes were modified.

Operational locator correction: attempting to read correction-322059/CORRECTION.json
inside the isolated candidate reported ENOENT. Its actual readable canonical path
is this dossier/correction-322059/CORRECTION.json; the isolated product files exist
and all hashes match. No missing input was bypassed.

Disposable stage/bootstrap/bind, held_packet and verify_imported_sources pass;
PREFLIGHT.json records authority/artifact hashes and measured preparation timings.
No Job submitted, no actual attempt, no Docker/provider, no product tests or direct
product implementation. New live selection is required before the OPERATOR launch;
the previous run grant is spent. Preserve /tmp/w321528-preflight-324054 and
/tmp/w321528-patch-check-324054 as preparation evidence.

Verification accounting: this turn product verification0s; preparation stage about
0.2s, bootstrap0.503s, bind0.252s, plus measured patch dry-run in PREFLIGHT.json.
Prior author records retain approximately98s plus2.195s comparison in claim321893
and73s in claim322059; aggregate historical review/preparation total is unknown.
No cumulative budget reset or new execution grant inferred.

Remaining: independent packet review, owner selection of this fresh live run,
v12 worker correction of real artifact custody and task provenance with focused
checks, exact-candidate independent review and owner integration/checkpoint.
Current milestone is preparation complete, product Work incomplete. No edits to
reviewer-owned FINDING/PLAN, historical packet or concurrent product paths.


## 2026-10-18 — claim324180 (baton.codxpc): operational blocker

Read detail324178; standalone claim324180 succeeded; complete new events through
324180, all four T321528 messages through owner M324176, current PLAN/FINDING,
review-2026-10-18T16-13-41Z.md and exact OPERATOR. Revalidated selected manifest
and all seven artifact hashes. Pinned owner selection in FINDING/PLAN as requested.

Exact stage failed at root.mkdir with errno30 read-only filesystem. Target
/home/sl/baton-instances/failed-reporting-w321528-324054 is absent; no stage writes,
bootstrap, bind, submission, Job/attempt, runtime or provider. Evidence in
evidence/execution-324180/PREPARATION-BLOCKER.json. Managed policy prohibits
interactive escalation or a direct fallback; return to baton.bug for operational
resolution of the exact command boundary. Owner live selection is already granted,
not awaiting renewed scope approval; no invocation consumed.

Remaining: execute reviewed preparation and one selected isolated v12 run; fix
real custody and exact task association; focused verification; exact-candidate
independent review and human integration/checkpoint. Retained inputs unchanged.
This claim product verification0s; preparation failed immediately (tool wall0s,
not a measured product run). Preserve prior author approximately98s plus2.195s
comparison and73s, packet preparation about0.955s plus patch check, reviewer
preparation about0.2s; aggregate historical verification remains unknown.
