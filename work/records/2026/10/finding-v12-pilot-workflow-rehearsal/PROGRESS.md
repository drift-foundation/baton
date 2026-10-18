# Implementer progress — W321690

Author: `baton.claude` (role `impl`), v11 claim 324772, 2026-10-18.
Bound dossier: this directory. Both blockers closed satisfying: W321688
(`433b09d6`) and W321689 (`372281f4`, the human checkpoint for the owner
disposition and closure commands). Source base `372281f4`; the working tree
carries only W321528's own records, which are not touched here.

## 2026-10-18 — execution provenance determined BEFORE any edit

The W321689-only completion exception expired when that Work closed, and
AGENTS.md now states the boundary without a fallback: "If v12 execution is
blocked, record the exact failed or unavailable operation and resolve it; the
blocker does not authorize direct execution outside v12. There is no general
direct-execution fallback." So the first question for this Work is what, if
anything, here is executable work that must run as an isolated v12 Job.

**Determination: nothing in this Work's accepted outcome requires a v12
implementation Job, and the rehearsal itself IS v12 execution.** Three parts,
each placed deliberately:

1. *The packet* (`PACKET.md` and its pinned identities) is packet preparation.
   The owner boundary puts that in v11 explicitly: "V11 remains the current
   preparation and coordination authority: dossiers, scope, acceptance, packet
   preparation and handoffs stay here."
2. *The rehearsal* runs the real v12 coordination code — authority, job
   manager, review driver, worker-manager operations — on a disposable
   instance through the packaged surfaces, with the provider and engine
   simulated at their own boundary. That is this Work's own instruction
   ("Simulate providers/engine at their normal boundary; exercise real
   coordination APIs") and it is v12 execution, not a substitute for it.
3. *No product source is authored here.* That is what would require an
   isolated implementation Job, and this Work's outcome does not include it.
   Thread M324395 is explicit about the disposition of anything found:
   "file only reproduced residual defects". A defect found by the rehearsal is
   therefore filed, not fixed in place.

**No new provider or engine run is performed, and that is this Work's own
exclusion** rather than a limitation I am accepting: "Existing W247941/W236087
proofs answer real execution questions already; no new provider/engine run or
broad certification." The accepted container-arc proofs stand as the execution
evidence; what is missing and what this Work owes is the JOINED coordination
proof over them.

Recorded so the boundary is checkable rather than asserted: the host could run
a container arc (`docker` 29.1.3 serving, the immutable base image
`sha256:0697b659…` present, membership in `baton-workspace` gid 1001, and
`v12/testing/standalone_ab` available), and it is deliberately not run. The
one operation that remains genuinely unavailable is a live-provider worker
attempt: it needs credential delivery from `/home/sl/.baton/credential-sources.json`
over a granted `--network`, which no owner selection covers and which
AGENTS.md's v12 verification default admits only for a stated question
deterministic coverage cannot answer. This Work states the opposite — its
proofs are coordination proofs — so that operation is not needed and is not
attempted.

## Owned paths

This Work authors no product source. Everything it writes is in this dossier:

- `PROGRESS.md` (this file) — implementer account.
- `PACKET.md` — the concrete pilot packet, with every pinned identity and
  every value that remains an explicit owner selection named as one.
- `rehearsal-324772/` — the rehearsal driver and its captured evidence.

If the rehearsal reproduces a product defect, it is filed as its own finding
with the reproduction; it is not corrected here. W321528 (`claude_agent.py`,
baseline/test paths) and W324214 (its own record directory) remain untouched,
and no shared product file is edited.

## 2026-10-18 — delivered this claim, and what remains

**Delivered.**

- The execution-provenance determination above, written before anything else.
- `PACKET.md` — the concrete packet with its pinned half established and
  checkable: source/candidate identities and the two accepted manifests, the
  thirteen-subcommand installed surface, the bootstrap input contract and the
  derived instance layout, the effective execution limits, the closed
  recovery-set membership, the rollback procedure, and — named as open rather
  than filled in with something plausible — the seven values that remain
  explicit owner selections. The FINDING's rule is that the packet is not
  executable until those are pinned, so it says so at the top.
- `rehearsal-324772/` — rehearsal step 1, run through the installed command
  on a disposable store: a native two-stage Job submitted and read back, with
  the review stage `blocked` on its implementation, both stages bound to the
  exact Work, each carrying its own offer and attempt identity, and the
  effective limits reported per boundary with their origin. That is the
  structural half of M324395 proof 1 and it pins the submission contract the
  packet needed. `REHEARSAL.md` states exactly what it does and does not
  establish.

**Remaining scope, named precisely so the next claim starts rather than
re-derives.** Four of the five joined proofs, plus the joined owner half:

1. *Terminal result reaches the review assignment* — the behavioural half of
   proof 1. Admit the implementation stage, produce a candidate through the
   simulated provider/engine, and show `prepare_review` publishing an eligible
   review assignment carrying the exact Work/Job/attempt/candidate binding.
   The supported simulation seam is
   `tools.stage_execution.operations_from(document, job_store, control_store,
   engine_run=…, credential_provider=…, clock=…, review_verdict=…)` — the
   same seam the accepted manager suites drive, which is what "simulate the
   provider and engine at their normal boundary" means here. The deployment
   document is composed by `bootstrap` with `owner_participant` set, so the
   owner grants exist on the same instance.
2. *Diagnostic owner for unable / provider-failed / no-candidate /
   held-unknown* (proof 2), through `job_manager/ending.py pending_endings`,
   without treating any of them as an accepted proposal and without releasing
   an uncertain runtime gate.
3. *Manager restart and lost reply* (proof 3): the ending obligation and the
   exact review claim survive, with no duplicate reviewer or correction.
4. *Stale episode and wrong principal* (proof 4) cannot publish a review or
   take over newer ownership.
5. *The owner half, JOINED* (proof 5): `disposition pending/approve/
   integrated/close` against the same instance the Job ran on, then readback.
   W321689 proved these on their own fixture and through a frozen bundle; what
   is owed here is the same acts joined to a real Job-bearing instance.

Then the packet's open selections are reduced to the ones that are genuinely
owner decisions, and the whole thing returns for independent review.

**Cumulative verification spending for this claim:** small and all
deterministic — two packaged `manager` invocations (submit and status, each
well under the 120s per-run timeout) plus the read-only inspections used to
pin the packet values. No test suite was run, because nothing in this claim
changed a line of product source; no build, no container, no provider, no
deployment, no Git command. The W321689 budget it continues from stands at
about 365s of measured test runtime, six PyInstaller builds and six frozen
drives, with the previously disclosed 600s abandoned full-suite discover still
claimed for nothing.

**Returning rather than claiming completion.** The rehearsal's remaining four
proofs are the substance of this Work, and a packet whose rehearsal is one
step in is not a reviewable joined result. This is returned through
`baton.bug` with the scope above rather than passed as delivered.

## 2026-10-18 — claim 324890: the joined rehearsal runs, and finds the gap

Reviewer 2026-10-18T17-42-19Z required one shared deterministic fixture
carrying continuity from an admitted native attempt to the owner's closure,
and corrected my earlier execution-provenance statement as too broad. Both
taken: `rehearsal-324890/joined_rehearsal.py` is that one fixture, and it
reports actual native admission, attempt and private-output identities rather
than treating host orchestration as execution evidence.

**What it drives, all through accepted code.** It borrows the accepted
`ComposedOneJobCase` world — `tools.stage_execution`'s own `operations_from`
composition, real Authority/Job/Control/Integration stores, a real
version-controlled line materialized by the accepted checkpoint profile, the
actual `claude_agent` workload entered through `baton_worker.serve_exchange`,
and `review_driver`'s ending — and carries one submitted Job by ordinary
manager ticks: implementation `completed` (Work route to `rview`), review
`completed` (route to `integration`), integration `claimed`. The engine and
provider are the accepted simulated seams, labelled as such in every evidence
file. No daemon, container, image, network, live model, live credential,
deployment or Git command.

**Established (M324395 proof 1, both halves).** The terminal implementation
result reaches a native eligible independent review assignment with exact
binding, not a status row: implementation attempt `attempt-7b5e070a…`, review
attempt `attempt-9e961a44…`, and a published proposal
`integration-driver.proposal:fa5686a9…` whose `assignment_ref` names the
implementation participant and generation. The Work's route moves through
`rview` to `integration` under the real ending, and the owner surface reads
that same authority: `record bind` binds the dossier and `disposition pending`
answers on the Work the Job ran on. With the three owner grants made as the
deployment act they are — the `owner_participant` selection W321689 added to
`bootstrap`, applied here through the trusted bootstrap face and labelled —
`pending` reports `holds: {approve, integrate, close}` all true.

**Reproduced gap, recorded and not fixed** (`rehearsal-324890/JOINED-GAP.md`):
at every point reachable above, all four authority receipts on that published
proposal are `null`, so `disposition pending` stays at `awaiting-verification`
and the owner's approval can never become due. The native review ending
records its verdict on the Job side and writes no verification or review
receipt on the authority side, which is where the owner's disposition reads
from. The two halves of the selected workflow do not meet on this path. Bounded
honestly: integration is `claimed`, not run, and its worker turn is a container
this Work excludes — so whether that turn writes the receipts is unproven
either way, and the gap note says exactly that rather than overclaiming. The
suggested follow-up answers one question deterministically, using the
integration-worker world `tests/tools/test_integration_worker.py` already
composes.

This is the joined proof gap this Work exists to find, and it changes what the
packet may claim: a deployment cannot promise the owner disposition is
reachable until that link is demonstrated. `PACKET.md` is updated accordingly.

**Evidence.** `rehearsal-324890/MANIFEST.json` binds all nine files by
SHA-256, with the driver, its exact invocation, the borrowed world, the two
labelled simulated seams and the list of what was not reached. Steps 1, 2, 3,
3b, 4 and 5 are separate JSON answers.

**Remaining scope.** The negative and recovery matrix the FINDING names —
unable/provider-failed/no-candidate/held-unknown diagnostic ownership
(proof 2), manager restart and lost reply (proof 3), stale episode and wrong
principal refusal (proof 4), withheld approval, non-satisfying outcome,
cancellation, one writable authority and disposable recovery — on this same
fixture. Proof 5's owner half cannot complete until the gap above is resolved,
because the owner's inputs do not exist on this path; that is a finding, not a
step I can drive.

**Cumulative verification spending this claim:** four driver runs over the
composed world (each well inside its 560s timeout; the full run completes in
seconds and `JOINED-REHEARSAL.json` records its own duration) plus two
read-only inspections. No product source changed, no test suite run, no build,
no container, no provider, no deployment, no Git command. The budget carried
forward stands at about 365s of measured test runtime, six PyInstaller builds
and six frozen-command drives, with the previously disclosed 600s abandoned
full-suite discover still claimed for nothing.

## 2026-10-18 — claim 324985: the reviewer was right, and the real finding

Review 2026-10-18T17-50-33Z corrected claim 324890 and the correction is
accepted in full: my driver stopped at integration `claimed`, which is before
ADMISSION, and `integration/driver.py:_accepted_receipts` (1105-1178) writes
verification, review and approval -- `admit_accepted` calls it around 1513,
before any runtime. Null receipts at a stop point I chose proved nothing. That
note is now explicitly superseded in place, with its stale proposal reference
corrected, and `rehearsal-324985/RECEIPT-BOUNDARY.md` carries what is actually
true.

**Driven, not read** (`rehearsal-324985/receipt_boundary.py`, on the accepted
integration-worker world -- real coordinator, admission driver, Authority and
worker entry, with the engine and provider simulated and labelled): at the
admission boundary, before any runtime, the receipts on proposal
`integration-driver.proposal:e8e10a8f...` are verification `passed` by
`baton.verify`, review `accepted` by `baton.review`, and **approval
`approved` by `baton.approve`**.

**The answer to the review's exact question.** Asked on that same store
through the installed command: `disposition pending --participant baton.slaw`
answers `owner_action: integration-due` with all three capabilities held, and
`disposition approve` as that owner is **refused, exit 2, `approval receipt is
immutable`**. So on the native path the owner cannot make the approval
decision at all -- not because their inputs are missing, but because one of
those inputs is an approval they did not give. And there is no supported way to
withhold it: `_accepted_receipts` takes one `issue` flag that skips all three
writes together, and both `admit_accepted` and `continue_accepted` require an
approver session holding `approve`.

**Spec basis for calling it a defect** rather than a configuration choice:
M321677 selects single-human approval; T321689 M321689 says "never infer owner
approval from worker verdict or completed Job"; the pilot assessment's P1 says
"automatic integration receipt actors cannot stand in for Slawomir's
decision"; and nothing here invented a receipt -- the receipt is the product's
own. The bounded follow-up is stated in the note and deliberately not chosen,
because the two candidate shapes (grow the receipt granularity, or make
owner-approval-first the selected ordering and have admission consume an
existing approval) are a product decision with an owner dimension.

`PACKET.md` section 7a now carries this instead of the withdrawn claim.

**Evidence.** `rehearsal-324985/MANIFEST.json` (4 members) and
`rehearsal-324890/MANIFEST.json` (9 members) bind every file by SHA-256 with
the drivers, their exact invocations, the borrowed worlds, the labelled
simulated seams and what was not reached.

**Remaining scope, unchanged by this and explicitly not blocked by it:** the
independent negative and recovery cases on these same fixtures -- diagnostic
ownership for unable/provider-failed/no-candidate/held-unknown (proof 2),
manager restart and lost reply without duplicate ownership or correction
(proof 3), stale episode and wrong principal refusal (proof 4), withheld
approval, non-satisfying outcome, cancellation, one writable authority and
disposable recovery. The owner-side half of proof 5 is now blocked on a
product decision rather than on a step I can drive, and that is the finding
above rather than an excuse: the parts of it that CAN be driven -- pending
readback, the grants, the refusal -- are driven and evidenced.

**Cumulative verification spending this claim:** four driver runs (two
exploratory, two recorded) over the accepted worlds, each completing in under a
second and well inside its 560s timeout, plus two read-only source
inspections. No product source changed, no test suite run, no build, no
container, no live provider, no deployment, no Git command. Budget carried
forward stands at about 365s of measured test runtime, six PyInstaller builds
and six frozen-command drives, with the previously disclosed 600s abandoned
full-suite discover still claimed for nothing.

## 2026-10-18 — claim 325675: the joined packet is reconciled, and three claims of mine are withdrawn

Both children closed satisfying (W325034 E325651, W325035 E325653) and the
parent carries zero open blockers, so this claim did the one bounded milestone
review 2026-10-18T19-24-38Z named: a reconciled joined evidence map and a
concrete operator packet, reusing accepted evidence rather than rerunning
anything.

**Authored this claim, and nothing else:** `reconciliation-325675/COVERAGE.md`
(the evidence map), `reconciliation-325675/MANIFEST.json` (which re-verifies
every child manifest by digest), the rebuilt `PACKET.md`, and this entry. No
child evidence was modified, no manifest rewritten, no driver rerun, and
`git status --porcelain -- v12/` is empty.

**The child digests agree with the reviewer's independently published values.**
Recomputed here: `boundary-325197/MANIFEST.json`
`dd2d071a1669fe861a7a4e3eaea80ed4f2310ad9fe7aafd593f56a0c1a907a4f`,
`matrix-325259/MANIFEST.json`
`970a1a22f209069a7db1595d8d02f34ad40584258ab8d550a31a3d239dd26309`. W321688's
`DIGESTS.json` is now pinned by digest too
(`e8f3f8d96aea26dccbb231310e6e05e33be5cbe23f7464548e32db435e532e25`), which the
packet previously cited by path alone.

**Every pin revalidated against the current tree**, as the role contract
requires: thirteen subcommands read back from `stack_command.COMMANDS`;
`bootstrap`'s nine required inputs, seven optional, `owner_participant` and the
three owner grants read from `bootstrap`; `CURRENT_GENERATION` 1 with
3600/900/1800/300 and bounds 1/86400 read from `execution_limits`; authority
schema 6, instance schema `baton.v12.stack-instance/1`, recovery schema
`baton.v12.instance-recovery-set/3` and the three closed membership sets read
from their owners. `git diff --stat 372281f4 HEAD -- v12/` is empty, so the
pins hold at HEAD and the two later commits are record-only — which is also why
no pin differs between this packet and the child evidence.

**Coverage.** `COVERAGE.md` maps M324395's five proofs and the FINDING's
acceptance list to the exact scenario and assertion each rests on: proof 1 to
`matrix-325259` sc. 4 plus `boundary-325197` sc. 2; proof 2 to sc. 5, 6 and 2;
proof 3 to sc. 1 and 3; proof 4 to sc. 7 and 8 plus the boundary negatives;
proof 5 to `boundary-325197` sc. 2 with sc. 8 for the non-satisfying half. It
says plainly that these were **four separate runs over four disposable worlds**
and not one continuous session, and that a shared attempt identity is the
fixture lineage deriving the same value from the same inputs.

**Three claims of mine are withdrawn in the packet, with their observations
preserved.** §7a previously said the packet cannot promise single-human
approval on the native path — superseded by W325034. What stands is narrower
and became §9's one prohibition: automatic integration admission writes
verification, review and approval together, so running it for a human-approved
Work pre-empts the owner and the later `approve` is refused as immutable. Also
withdrawn: that no supported operation names a diagnostic owner, and that the
composed fixture exposed no engine-absence seam. **No product defect is claimed
by this Work.**

**§5 is corrected where the review said it misled.** `record recovery-check`
reports and **refuses**; it never admits anything, and a clean report is the
precondition for an operator's admission rather than the admission. The three
operator obligations are stated as obligations the packet does not discharge:
stop admissions (not "stop the supervisor"), positively account for every
runtime and launch, and admit one writable instance. The matrix's same-authority
restart is explicitly not restoration, not failover and not exclusion of a
second writable copy; W321688's contract remains the authority for that.

**§3a is new and is labelled a proposal, not a selection:** concrete addresses
and grants for the implementation and review workers, the two receipt actors,
the owner (`approve`/`integrate`/`close`, never `verify`/`review`), the
integrator used only on the automatic path, and the diagnostic handler — with
the note that the W325034 evidence world's `policy_generation: 14` in
`scope:deployment` is a fixture value and the production generation must be read
back from the selected instance. §6 keeps seven owner selections open and adds
an eighth, the diagnostic selection, since W325035 proves both mechanisms and
the choice between them is policy.

**§9 is the ordered supported operations** — result pickup; independent
verification and review including the five requirement clauses a judge must
evaluate itself; the owner's pending/bind/approve/integrated/close and
readback; the diagnostic notice/claim/label path; and the recovery selection —
with the automatic-admission prohibition stated where it applies.

**The harness limitation the review flagged is cited rather than waved past.**
`boundary-325197`'s runner used the broad expected-failure classifier, so a
setup or cleanup error could in principle have satisfied its self-check. It did
not: the retained `scenario-0-harness-self-check.json` records `failed_check` =
"the review stage is completed immediately after submission (INTENTIONALLY
FALSE)" with no `failure` and no `cleanup_failure` member, and the accepting
review independently validated those facts. The strict classifier is in
`matrix-325259/matrix3.py` and the packet says any rerun must use it, because a
zero exit alone is never acceptance.

**Cumulative verification spending this claim:** no driver run and no native
rerun — deliberately, under the instruction to reuse accepted evidence. Four
digest recomputations of the child manifests, one `v12/` diff against the child
base, six short read-only reads of the pinned constants
(`stack_command.COMMANDS`, `bootstrap`, `execution_limits`, the authority and
instance schemas, the recovery membership sets), and reads of the two accepted
child reviews, `RECOVERY.md` and the retained self-check record. No product
source changed, no test suite run, no build, no container, no live provider, no
live credential, no deployment, no raw SQL, and nothing that mutates this
repository's history, index or working tree.

## 2026-10-18 — claim 325757: the boundary is now a control, not an instruction

Review 2026-10-18T19-33-42Z found the real defect in my packet and it was a
substantive one: §9A said the manager serves and §9B told the operator not to
call automatic integration admission. **An instruction is not a control.**
`tools/stage_execution.py` reaches `admit_accepted` (3118, 3153) and
`continue_accepted` (3149) during ordinary manager progress with the
deployment's own verification, review and approval sessions, so a serving
composition can take the owner's decision however firmly a document forbids it.
The review was right that W325034's proof establishes the judgment boundary and
not that a continuously serving three-stage composition will wait there.

**The supported control is the submitted Job's own stage set, and it is now
driven rather than asserted.** `composition-325757/composition.py`, one run:
**32 checks passed, 3 scenarios observed, 1 failed exactly as it must, 0
unexpected, 3.667s**, bound by `composition-325757/MANIFEST.json` (11 members)
with `COMPOSITION.md` as the readable result.

A Job declaring `implementation` and `review` only (scenario 1, 15 checks) is
served normally — pickup, a real worker turn, the implementation ending, the
independent review assignment and its real turn — **publishes the candidate**,
whose `candidate_digest` equals the reviewed frozen checkpoint's own head, and
leaves **all four receipts absent** through 40 further ticks *and* a fresh
serving composition over the same stores with `recover()`. No falsely complete
integration stage exists, because none is declared. The Work is handed on to the
configured outgoing route with no handler, where the owner's `disposition` acts
take it. This is not a new operation and not a product change: it is a
submission the deployment already composes, so no owner product choice is
needed to have it.

Scenario 2 (11 checks) then drives the receipt path on that same shape: the
owner holds no `verify`/`review` grant, the two independent actors publish
`passed` and `accepted` attributed to themselves, **the approval stays absent**,
`disposition pending` answers `approval-due`, and both `disposition integrated`
and `close --outcome satisfying` are refused while the approval is withheld with
no receipt changed. The owner's own approve/integrated/close/readback chain is
the accepted W325034 proof and is deliberately not repeated.

Scenario 3 (6 checks) measures the contrast honestly and says in its own
`not_claimed` member what it does **not** show: with the integration stage
composed, this fixture's deployment configures no integration instructions, so
the sweep *defers* the stage with its own contained refusal and writes nothing.
What it does establish is the operational difference — with an integration
stage composed the Work does not reach the owner at all; it is held by the
integration participant under a decision nobody has made. The evidence for a
fully configured integration deployment at that boundary remains the retained
`rehearsal-324985/RECEIPT-BOUNDARY.md`. **No product defect is claimed.**

**Packet changes.** New §3b pins the two-stage submitted Job as the control,
with the call sites named and the driven properties listed, and states that the
outgoing route is a per-worker deployment operand that should name the route the
owner is served on. §9B's prohibition now points at that control instead of
standing alone. §6 gains a ninth selection — the owner's route and its handler —
since §3b makes it a real choice rather than a detail. The documentary
corrections the review listed are done: shortened cross-record locators are now
canonical `baton:work/records/...` addresses in both the packet and
`reconciliation-325675/COVERAGE.md`, the selection count is correct, and the
final receipts are described as **four receipts from three distinct actors**
(the owner legitimately appearing twice) rather than four distinct actors.
`reconciliation-325675/MANIFEST.json` is left unmodified; the new manifest
records the revised digests of `PACKET.md` and `COVERAGE.md` beside the digest
the earlier manifest had recorded, so the change is visible rather than silent.

**An operational fault of my own, reported and repaired as far as I can.** The
review found that canonical event E325725 contains the literal string
`@/tmp/w321690-handoff.txt` instead of that file's contents: `comment=@<path>`
is not a supported indirection in the v11 CLI. I checked my other passes —
E325252 (W325034) and E325378 (W325035) are affected the same way; E325090,
E325131 and E325190 carried their text inline and are fine. The canonical
events cannot be rewritten and both child Works are closed, so the three texts
are preserved with their digests in
`composition-325757/handoffs/` with a README naming exactly which event each
belongs to. From this claim on, every pass comment carries its actual text
inline with canonical locators and no `@file` operand.

**Two faults of mine caught by the strict harness rather than by prose**, which
is what it is for: a misplaced subcommand verb (the CLI takes the verb first)
made `argparse` exit the whole process after scenario 1 with no summary —
`except Exception` does not catch `SystemExit` — so `command()` now contains it
and the scenario loop catches `BaseException`; and a wrong sweep-report key
(`started`, not `progressed`) made the contained-refusal check fail. Both are
in the driver's own comments.

**Cumulative verification spending this claim:** five probe runs of the fixture
world at 0.9–4s each (the two-stage shape, the restart non-pre-emption, the
three-stage contrast, the sweep report shape, the publication chain) and five
runs of the driver at 0.2–3.7s, three of them failing — the verify operand
shape, the report key, and the process-exiting verb order — each of which became
a correction in the driver. Plus read-only source reads of the integration
progress path, `publish_candidate`, `review_driver._published`,
`integration_port_for` and the disposition CLI grammar, and four digest
recomputations. No product source changed, no test suite run, no build, no
container, no live provider, no live credential, no deployment, no raw SQL, and
nothing that mutates this repository's history, index or working tree.
