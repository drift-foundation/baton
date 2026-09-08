# Progress

## 2026-09-07 — baton.claude — the verdict channel, implemented

PLAN item 2 adopted and implemented; item 3 verified. State: **awaiting
independent review of the four-path candidate**. The adoption and its four
clarifications are pinned in `FINDING.md` under
*2026-09-07 — implementation adoption*; nothing below supersedes them.

### Revalidation, before anything was written

All eleven files `evidence/research-110843/baseline.json` binds are
byte-identical in the current tree, including `tools/single_worker.py` and
`tools/stage_execution.py` at W103083's returned candidate — so the research
inspected exactly this tree. Every confirmed claim was re-checked against the
source rather than against the summary of it, and every one holds. The one
fact that mattered most and was not in the baseline: the launch document
already carries `role`, `baton_worker.launched` validates it as bounded
non-empty text, and `single_worker` fills it from the worker's configured
`launch_role`. So the review branch is selected by an operand this container
was launched under. Nothing inspects the filesystem to decide what kind of
turn it is.

### The worker half: a decision, not an exit status

`ClaudeAgent.work` branches on `seen["role"]`. The review turn does none of
what the implementation turn does — no checkout, copy, reservation, edit,
commit, bundle or verification — because the manager mounts the line read-only
and a reviewer that wrote to it would be a second implementer.

**The report is a dedicated file and its destination is not under `/output`.**
Every declared output directory is measured, sealed and collected, so a
provider-authored file inside one would be adopted custody material before this
adapter had looked at it. The report lands in a fresh private directory under
the tmpfs — `_new_directory` creates exclusively and the destination is proved
absent — is validated here against a closed three-member contract, and the
findings output is then AUTHORED from it.

**Nothing about the report is trusted.** Its bytes are bounded at the read
rather than checked afterwards, because a truncated JSON document is a
different document; its keys refuse duplicates, because `json` would otherwise
resolve that collision silently in the reader's favour; its schema is compared
by equality; its verdict is one of three words this module spells; and its
findings are non-empty bounded text. Every failure answers `None`, which makes
the turn `unable` with no claim on any output. **An exit status is never mapped
into a verdict** and a provider that failed earns none even if it wrote a
valid report, because a turn that failed is a turn whose account is
incomplete.

**The objects are observed and bracketed.** `head` and `tree` are read from the
mounted line with `rev-parse`; `base` is the frozen task's `declared_base`,
proved to be an object this line actually holds. `^{commit}` rather than the
bare name, and that is not a detail: `rev-parse --verify` accepts a well-formed
forty-character object name as SYNTAX and echoes it back whether or not the
repository holds the object, so a base this line had never seen would have
verified itself. The three are re-read after the provider turn and a difference
is a refusal — a review of a tree that moved under it is a review of nothing in
particular.

**The prompt asks for an assessment and names no protocol.** It gives the
source path, the requirements, the report destination and the three words. It
says the task's verification command being NAMED is not evidence that it
passed, because the same provider and the same image run both roles and the one
thing a review must not do is report an unsubstantiated check. It says nothing
about `/output`, the assignment, the attachment, the checkpoint or the manager.

**The logs are adapter-authored.** Status, the observed objects, the verdict
and the provider's own closed failure word — and no byte any child wrote. The
findings are a deliberately authored artifact adopted from a validated
document; they are not a diagnostic-stream exemption, and W39357's boundary is
unchanged.

**The shared Job's declarations.** Every stage of one Job matches that Job's
ONE input digest, so the declaration set is the union and each role produces
its own half. `_selected` admits exactly the common vocabulary, refuses a name
this workload does not know rather than spreading itself over it, and refuses
an output this role does not write being declared required — a declaration no
single turn can satisfy is named as a declaration rather than as an answer.
`_one_declaration` and the original single-output workload are untouched.

### The manager half: two functions, one ordered core

`review_verdict_from_result(control, *, attachment_id)` is read-only and
public. It opens nothing, writes nothing, reads no mutable runtime path, takes
no clock and calls no provider, so the same call on the next incarnation
derives the same answer — which is what makes an ending re-enterable after the
freeze without asking the worker anything twice.

**The cross-binding is the point.** A namespaced claim by itself says only that
somebody wrote four members into an output. What makes it a verdict about THIS
checkpoint is that the frozen result belongs to this attachment's attempt, its
retained manifest names the same result and the same fixed assignment at the
same generation, the attachment's own generation agrees, and the base, head and
tree the reviewer says it looked at are the ones the checkpoint's evidence
records. A claim on the logs output as well as the findings one refuses as
`ambiguous` — one review decides once.

**Every refusal is evidence rather than programming**, and each carries a
category the ending holds rather than raises. Missing, malformed, foreign or
unavailable evidence is a question for an operator; none of it is a default
decision, and in particular none of it is `rejected`. A reviewer that did not
answer has not rejected anything.

`end_review_from_result` takes no caller verdict. It adds two steps to
`end_review`'s order, in the two places they can honestly go: the terminal
correlation after the freeze, because there is nothing to compare until the
freeze has happened; and the claim resolution after intake and retention,
because the claim is inside the result this ending just froze.

**An unresolved claim is `held` with `verdict: null`** — no verdict recorded,
no cleanup authorized, nothing advanced, and the held reason naming the frozen
evidence. A valid `rejected` claim is a different state: it records its fence,
cleans up, and is still held, because it is a decision about the Work rather
than evidence nobody can read.

**`end_review` is unchanged.** Both entry points share one ordered core because
every step in it is a ruling and a second copy would be a second place for the
order to drift from the reasons above it. `terminal=None` is a no-op in
`_correlated`, which is what makes the explicit-operand entry point's behaviour
identical rather than merely similar — and its 52 existing tests pass
untouched, which is the proof of that sentence rather than a claim about it.

### The joined proof

`TheReviewerDecidesAndTheManagerReadsThatDecision` runs the real
`ClaudeAgent.work` review turn over a real Git repository with a deterministic
process seam in place of a model, measures its two output directories through
`baton_worker.answered` — the generic measurement, performed by the worker
rather than by the case — retains that as a real result manifest, and drives
`review_verdict_from_result` and `end_review_from_result` to an accepted
verdict, a correction round and a held rejection. The claim reader and
`record_verdict` are the production ones.

**What stands in, named rather than implied:** the model, and the custody
artifact identities a sealing runtime would mint. The checkpoint profile
answers the REAL objects the reviewer observed — it keeps every rule of the
suite's existing fake and substitutes the three object names, because what is
under test is the channel and Git's own checkpoint profile has its own suite.

**One fixture fact recorded because it cost a debugging round:**
`record_verdict` binds the frozen review result into its own operation
signature, so a manifest retained AFTER the verdict makes the ending's replay a
different act under the same identity — which §4.2 refuses, correctly, and
which reads as a settled review being unsettleable evidence. The fixture
retains before it records.

### Verification

Focused, from `v12/python` with the interpreter `justfile` selects
(`python3`, 3.13):

    PYTHONPATH=src python3 -m unittest tests.job_manager.test_review_driver -q
    PYTHONPATH=src python3 -m unittest tests.manager.test_claude_agent -q

`tests.job_manager.test_review_driver` is 79 passing — 52 before, plus 27.
`tests.manager.test_claude_agent` is 161 passing — 130 before, plus 31. The 52
and the 130 are unchanged and untouched; that is what proves the explicit
ending and the implementation turn still behave exactly as they did.

Canonical subtree gate, from `v12/python`, retained whole at
`evidence/implementation-110915/subtree-gate.txt`:

    PYTHONPATH=src python3 -m unittest discover -s tests -t .

**4665 tests in 242.6s, 11 failures and 1 error, 21 skipped — and none of them
is this change.** Reported as a baseline rather than as a pass, because a green
claim over a red run is the one thing a gate cannot survive. Every failing
assertion was read, and the subjects are:

- `tests.manager.test_boundary_inventory` (5) — unowned persisted-column reads
  and one probe, in `attempts.py`, `lanes.py` and `review_cycles.py`. Neither
  owned source path appears in any of the reported entries;
  `review_driver.py`'s new reader executes no SQL at all and reaches every fact
  through an accepted public reader, which is why it cannot have added one.
- `tests.manager.test_worker_container` (2),
  `tests.manager.test_credentials_engine` (1) and
  `tests.manager.test_output_custody_engine` (1) — a live Docker daemon's
  leftovers from an earlier run of this host's suite, named by container and
  image tag.
- `tests.authority.test_catalog` (1) — an unregistered
  `test_work_label_exposure.py` in the authority suite's own checklist.
- `tests.tools.test_parallel_runner` (1 error) — the previously recorded
  registry condition, naming only the two untracked baseline modules
  `tests.integration.test_driver` and `tests.job_manager.test_review_driver`.
  That second module is the accepted review-driver leaf's landing, not this
  Work's file, and the condition predates this candidate: W103083's own
  checkpoints record it unchanged.

Each is separate Work if it is not already somebody's; none can invalidate the
capability this candidate claims, and none is worked around here.

### Candidate

| Path | SHA-256 |
| --- | --- |
| `v12/worker/claude_agent.py` | `4406af1acbd2e64e8daddee985fca67b4dd7a94b3b91927b06bc2dae98eac2c0` |
| `v12/python/src/baton_v12/job_manager/review_driver.py` | `62db37ee8cd52bf99fc4e68b766841586f921324366e9e0191fc9618b33e6765` |
| `v12/python/tests/manager/test_claude_agent.py` | `578fb990f033314f0f7f72292117bb6d2cfc8d96f6ee90e4511242cbdd6992f6` |
| `v12/python/tests/job_manager/test_review_driver.py` | `21be540bbd03e44a7914582daac1125da7e8328a655ad089f7711f20158bde2b` |

All four are the paths `FINDING.md` froze. No new module, no registry change,
no shared-path edit, and no existing assertion weakened — every test change is
additive except two mechanical ones inside this Work's own scope: the review
fixture gained a `line_base` hook (a line is create-or-recover by Authority and
Work, so a case whose checkpoint evidence must name real objects has to supply
its base before the line exists), and `copy`, `pathlib` and `subprocess`
imports.

### What this does NOT claim

No live provider ran, no container started, no image was rebuilt and no
deployment selected one. The assembly hookup is W103083's: it must call
`end_review_from_result` with the real terminal and supply the common
declarations and one Job input digest, replacing its production reliance on
`_no_verdict`. W110774's integration runtime port remains absent and is not
touched here. W110783 keeps its separate post-fence restart defect.


## 2026-09-07 — baton.claude — the three blockers, corrected

Reclaimed after `review-2026-09-07T15-19-16Z.md`. All three P1s reproduced
before I changed anything and all three were real; the dated correction
adoption is in `FINDING.md`. State: **awaiting independent review of the
corrected four-path candidate**.

### P1 — the serving entry ran without the worker's completion envelope

The review is exactly right, and the shape of the defect is worth stating
plainly: I added a `terminal` operand and then handed it straight through to a
helper whose first line treats `None` as permission to skip. So the entry point
whose whole purpose is to read a verdict out of a frozen result would reach
`accepted` and `cleaned_up` having never checked that the result was the one
the worker finished — and a string operand got worse treatment still, arriving
at `terminal.get` as a raw `AttributeError` after the stop and the freeze.

**The shape and the comparison are now two questions, asked in the two places
they can honestly be asked.** `_own_terminal` runs in the serving entry before
the first external act, so a deployment that forgot the terminal has not
stopped a container; `_correlated` still compares after the freeze, because
there is nothing to compare against until then. Three cases assert zero stops
and an empty recorded sequence for the shape refusals, and one asserts that a
terminal naming another envelope refuses AFTER freeze and correlate and before
verdict and cleanup.

**`end_review` is untouched and that is not in tension with this.** It was
accepted without a terminal, and a caller that already holds a decision is not
claiming to have correlated anything. A case now drives that rather than
leaving it as prose.

### P1 — the competing-claim scan looked at one output

`_review_claim` checked `logs` and nothing else, so a schema-valid result
carrying `accepted` on findings and `rejected` on the proposal output was read
as `accepted`. The common manifest a shared Job declares names `proposal`
expressly, so that is the shape this deployment actually produces.

The reader now walks the whole frozen output set for the namespace and requires
its sole occurrence on `findings`. Naming the outputs to exclude is how the
next output added becomes a second opinion nobody looks for. The refusal is
worded without asserting where the other claim is, because a claim on the
proposal and none on findings is the same refusal and a message saying "as well
as its findings one" would describe a document that does not exist. Five cases:
proposal, logs, claim-on-the-wrong-output-with-none-on-findings, the ending
holding with no verdict and no cleanup, and an unrelated proposal-claim
extension on another output left alone.

### P1 — a FIFO at the report name could hang past the provider's deadline

`_open_under`'s final open is a blocking `O_RDONLY | O_NOFOLLOW` performed
before `fstat` proves a regular file, so a provider that created
`review-report.json` as a FIFO and exited successfully left this adapter
waiting for a writer that never arrives — outside its own bounded invocation,
so `PROVIDER_SECONDS` bounded nothing about it.

The report boundary now has its own opener: parent no-follow, child relative to
it with `O_NONBLOCK`, regular-file proof on the descriptor, then the bounded
read. `_open_under` is unchanged and still owns the measured tree walk; this is
one fixed name in a directory the adapter created exclusively for it, written
by the least trusted process in the container. The FIFO case is its own proof
of not hanging — it runs in-process with no writer anywhere, so returning at
all is the assertion.

**And the report's text is proved encodable at adoption.** `json` decodes an
escaped lone surrogate into a `str` no UTF-8 encoder accepts, so such a report
passed every check and then raised `UnicodeEncodeError` from the `findings.txt`
writer — after the logs output was published and while findings was half
written. Adopting text is adopting the obligation to publish it, so the encode
is proved where the document is adopted and a failure takes the ordinary
unable/no-claim path.

### The joined proof, repaired rather than re-explained

The review is right that it concealed the first defect. Every ending passed
`terminal=None`; the fixture invoked the real `record_verdict` BEFORE the
ending under test, so the ending replayed a verdict rather than producing one;
the canned freeze answered a digest nothing retained, so the correlation and
the resolver were looking at two different documents; and the order assertion
filtered the expected sequence down to the steps observed, so a missing
`correlate` or `resolve` could not fail it.

All four are fixed. `_frozen_endings` answers `frozen_output_of` for the exact
attempt, so one retained result feeds the correlation, the resolver and the
recorded verdict. `reviewed(record=False)` leaves the checkpoint with no
verdict, and the cases assert the count goes 0 to 1. The order assertion
compares the WHOLE recorded sequence against `REVIEW_RESULT_ENDING`. Replay is
driven from the freeze cutpoint: the ending runs twice, answers identically,
runs every step again and leaves exactly one verdict row.

`correlate` and `resolve` are recorded by wrappers that DELEGATE to the real
functions. Neither the reader nor `record_verdict` is substituted; the wrappers
exist because those two are inline calls rather than patched module functions,
and an order assertion that could not see them is the assertion that let their
absence pass.

**What still stands in, named rather than implied:** the quiesce, the
observation, the intake, the retention and the cleanup. Those need an engine, a
delivered workspace and a custody tree — a deployment's half that
`tests/manager` drives and W103083 owns. Real here: the frozen result and its
retained manifest, the completion correlation, the claim reader, and
`record_verdict`.

### The broad-gate account, corrected

The review is right on both counts and I am correcting the record rather than
restating it.

**There are SIX boundary-inventory failures, not five.** My previous entry
listed five; the retained log carries six, and I had miscounted from a
truncated read of my own evidence.

**And the "no container started" sentence was wrong as written.** It is true of
the focused workload demonstration — no provider, container, image rebuild or
deployment selection is involved in the review turn or its tests — and false of
the subtree gate, which runs live-engine suites against a real Docker daemon.
That is where four of the failures come from. The two claims are separate and
are now stated separately; merging them read as a blanket denial that a
container ran anywhere in the turn.

The current gate, retained whole at
`evidence/implementation-110915/subtree-gate-corrected.txt`: **4685 tests in
244.2s, 11 failures and 1 error, 21 skipped.** The distribution is unchanged
from the previous run — six boundary-inventory failures over `attempts.py`,
`lanes.py` and `review_cycles.py`; two `test_worker_container`, one
`test_credentials_engine` and one `test_output_custody_engine` cleanup failure
from a live daemon's leftovers; one authority-catalog failure over an
unregistered `test_work_label_exposure.py`; and the previously recorded
registry error naming `tests.integration.test_driver` and
`tests.job_manager.test_review_driver`. None names either owned source path.

The total moved 4665 to 4685 and every one of the twenty is accounted for:
twelve added to `test_review_driver` and three to `test_claude_agent` by this
Work, plus the five added to `tests/tools/test_stage_execution` by W103083's
generation-ceiling correction, which landed between the two gate runs. The gate
remains red and is handed over red; the failures are separate Work if they are
not already somebody's.

### Verification

    PYTHONPATH=src python3 -m unittest tests.job_manager.test_review_driver -q
    PYTHONPATH=src python3 -m unittest tests.manager.test_claude_agent -q
    PYTHONPATH=src python3 -m unittest discover -s tests -t .

`test_review_driver` is 91 passing — 79 before, plus twelve. `test_claude_agent`
is 164 passing — 161 before, plus three. The 52 pre-existing review-driver
tests and the 130 pre-existing worker tests are still present and passing; the
182 the review asked me to preserve are preserved.

| Path | SHA-256 |
| --- | --- |
| `v12/worker/claude_agent.py` | `8e2001f4a1dc0a7106f041db29afafeb725d1e598c7c165a141fe9dbd44acf33` |
| `v12/python/src/baton_v12/job_manager/review_driver.py` | `fcac6d17e146bf2d89725562addb62e7d8ea5c6d1dccb2bd79f4bb29dd04d610` |
| `v12/python/tests/manager/test_claude_agent.py` | `acbb0d21364d2e442152c45af90c982d8f5e2b3d0c54c3735af83834eba5c6ce` |
| `v12/python/tests/job_manager/test_review_driver.py` | `65b9e9fef04d30f36a16070fea8096f4ee19f4caef56b4132832881703a15f4a` |

### Unchanged and not claimed

No live provider ran in this Work's own demonstration, no image was rebuilt and
no deployment selected one. The assembly hookup remains W103083's. W110774 and
W110935 are untouched, and no handoff of the shared `claude_agent.py` path is
claimed here.

## 2026-09-07 — baton.tuner — claim111406 — joined proof blocked, awaiting review

Owner reroute111403 assigned only
`v12/python/tests/job_manager/test_review_driver.py` and this dossier. I pinned
that scope in FINDING/PLAN before editing and adopted the latest independent
review at `review-2026-09-07T15-37-14Z.md`.

Added `TheWorkerCompletionTraversesPublicCustody`: public offer/assignment and
runtime setup, a prerequisite writer settled through public custody, an
independent reviewer using the real worker completion publisher, actual file
sealing/collection, real manager freeze/intake/retention/verdict/cleanup calls,
and an interruption raised only after real freeze commits. Recording wrappers
delegate to their owners. External provider, engine, Authority transport and
checkpoint-profile transport remain deterministic test seams; no live provider,
container, build, deployment or authoritative Baton store is involved.

The assignment exposed the production incompatibility recorded in the dated
FINDING: intake changes output to sealed, but record_verdict requires frozen
and passed verification. The unmodified ending consequently returns held
after resolving accepted, with two retained artifacts, zero verdicts and zero
cleanup calls. The same boundary refuses after freeze-cutpoint re-entry without
another worker turn. I did not alter production or counterfeit an axis/receipt
to obtain a green result.

Validation and retained evidence under `evidence/tuner-111406/`:

- `joined-proof.txt`: 2 tests, both fail at the exact production refusal.
- `focused-module.txt`: 93 tests, 91 pass and the same 2 new proofs fail.
- `custody-blocker-probe.py` / `custody-blocker-probe.json`: exit 0 when
  checking the observed blocked state, actual completion/result identity,
  independently recomputed custody trees, retention records and cutpoint
  replay. This is diagnostic evidence, not acceptance of the held outcome.
- `candidate.json` and `baseline.json`: both production paths and the worker
  test module retain their accepted hashes. The complete prior review-driver
  test file (111559 bytes) is an exact prefix of the current file; all earlier
  assertions are preserved. Current test SHA-256:
  `048f79a113f7f1d9beb5d56966d923b9fbdbb65456948df7fe251d2519d764c9`.

The broader gate was not repeated for unchanged production. Its existing
`evidence/implementation-110915/subtree-gate-corrected.txt` account remains
4685 tests, 11 failures, 1 error and 21 skipped. That earlier gate included
live-engine tests; this claim's focused proof and diagnostic did not. The prior
164-passing worker-module evidence is reused for its unchanged bytes.

Status: **blocked acceptance, awaiting independent review**. The success
assertions beyond record_verdict, including final cleanup, have not been
reached and are not claimed validated. Return to baton.bug to assess this
evidence and arrange the explicitly bounded production correction. Dependent
source gates stay closed.


## 2026-09-07 — baton.claude — the first-verdict blocker, cleared

Claimed under Slawomir's reroute 111888, which approves `FIRST-PROOF-PLAN.md`
and its ten paths. **Two of those ten are delivered and eight are not started**;
the last section says exactly which and why, and one concrete finding stops the
two custody proofs from going green.

### Revalidation

All fifteen paths `evidence/planning-111746/baseline.json` binds are
byte-identical in the current tree, so the planning inspected exactly this tree.

### The blocker, and it was one line of precondition

`_completed_review` required `output == "frozen"` **and**
`verification == "passed"`. Both halves were wrong for the milestone the owner
has now ruled on, and each for its own reason.

**`sealed` is what real custody produces.** An ending that actually performs
intake and retention leaves the output axis at `sealed`, and admitting only
`frozen` meant the very custody the lifecycle requires made a first verdict
impossible. The two real proofs failed on exactly that and nothing else was
wrong with them.

**But `sealed` is admitted only with the receipt that made it sealed**, which
is the difference between moving a check and relaxing one. `frozen` says the
manager sealed the bytes; `sealed` says it also collected them, and the
evidence for the second is the intake receipt rather than the axis word. So
`_custodied_review` reads the receipt from its owner and cross-binds it to the
exact frozen result — same attempt, same result id, same manifest digest, every
artifact the result declares present in the receipt — and requires the
retention decisions to exist, because an attempt sealed with nothing retained
is one whose material nobody decided about. Nothing writes an axis and nothing
moves `sealed` back to `frozen`.

**The reviewer's verification axis is no longer a prerequisite**, per M111752.
There is no producer that could write `passed` into a REVIEW attempt's axis
under this milestone's workflow, so requiring one made every honest review
unsettleable. The axis is left exactly as found: nothing forges it, resets it,
or reinterprets a `failed` or `unable` somebody else recorded — and the
scheduled case now drives all three values and asserts the axis is unchanged
after the verdict is recorded.

What still gates a verdict is untouched: the exact attached runtime positively
quiescent, a `completed` worker disposition, a frozen result naming this
attempt, and separately frozen findings and logs. Custody alone never proves a
review happened; it proves the output a review is about is one this manager
holds.

### One concrete finding, reported rather than worked around

**`verdict_of` and `record_verdict` are two different projections of one
verdict, and the two custody proofs assert they are equal.** With the
precondition corrected both proofs now reach a recorded verdict and fail on
that comparison instead:

    only in verdict_of:      base_object, head_object, tree_object,
                             review_assignment_generation, recorded_at
    only in record_verdict:  base, head, tree, review_generation

That is by construction rather than by accident: `verdict_of` answers the
persisted ROW proved against the committed act, and `record_verdict` answers
the act's OPERANDS. Neither is wrong on its own terms, and the equality the
assertion expects has never been a property of this build — my correction did
not break it and was not scheduled to make it true.

I have not changed either side. `verdict_of` is a shared public reader that
`advance_correction` resolves through, so reconciling the two shapes is a
decision with other consumers; the plan says to record a concrete interface
question rather than widen into one, and the same plan tells me to keep those
two assertions intact, so I may not weaken the test either. **The exact
decision needed: whether the public reader should answer the act's operand
spellings, whether the recording should answer the row's, or whether the
assertion should compare identity rather than the whole document.**

### Delivered, of the ten approved paths

| Path | State |
| --- | --- |
| 1. `worker_manager/review_cycles.py` | **done** — sealed custody, reviewer-axis prerequisite removed |
| 5. `tests/manager/test_review_cycles.py` | **done** — the scheduled expectation change |
| 2. `job_manager/review_driver.py` | not started — proved post-cleanup ending replay |
| 3. `integration/driver.py` | not started — ordinary-test evidence, `required_tests`, receipt |
| 4. `v12/worker/claude_agent.py` | not started — namespaced ordinary-test metadata |
| 6. `tests/job_manager/test_review_driver.py` | not started |
| 7. `tests/integration/test_driver.py` | not started |
| 8. `tests/manager/test_claude_agent.py` | not started |
| 9. `v12/python/REVIEW-CYCLES.md` | not started |
| 10. `tests/manager/test_dependencies.py` | not started |

The eight are not started rather than partly done. Item 1 was the measured
blocker — it is what both failing proofs stopped on — and it is a bounded,
independently reviewable correction to one precondition. Items 3 and 4 are a
different piece of work: a new namespaced worker observation, a new
`required_tests` operand on `admit_accepted`, and replacing the unconditional
`passed` receipt with evidence-driven publication, with its own integration
test surface. Beginning that and handing it over half-wired would put a
partially built receipt path into the shared integration driver, which is the
same hazard I declined to create in `oci.py` and the reviewer agreed with then.

**The scheduling is the reviewer's and Slawomir's**, not mine to settle by
starting it. If the preference is that I carry the remaining eight in one pass,
route it back and I will.

### Verification

    PYTHONPATH=src python3 -m unittest tests.manager.test_review_cycles -q
    PYTHONPATH=src python3 -m unittest tests.job_manager.test_review_driver -q
    PYTHONPATH=src python3 -m unittest discover -s tests/manager -t . -q

`tests.manager.test_review_cycles` is 69 passing. `tests/manager` is 2845 with
**ten failures, all of them the standing baseline** — six boundary-inventory
and four live-daemon cleanup — so this correction introduced none.
`tests.job_manager.test_review_driver` is 93 with the two custody proofs
failing on the projection mismatch above, which is the finding rather than a
regression: before this correction they failed earlier, on the precondition.

No broad subtree gate was run this turn; the plan asks for focused changed
suites and one appropriate gate, and a broad run belongs with the complete
candidate rather than with a partial one.

| Path | SHA-256 |
| --- | --- |
| `v12/python/src/baton_v12/worker_manager/review_cycles.py` | `c635fc8442c2689c336501a4527d608153c6f4605affe0d4630ebdeba9e63d4f` |
| `v12/python/tests/manager/test_review_cycles.py` | `319fa540e2ec37b43ab2207da2149554367044622d84891ec46bd01ec68f557d` |

The other eight approved paths are byte-identical to the planning baseline.

### Not claimed

No ordinary-test evidence path exists yet, so `integration.driver` still
publishes its unconditional `passed` receipt — the correction that replaces it
is item 3 and is not started. No worker behaviour changed. No Authority or
schema change was made or needed. W103083, W110935 and W106673 stay gated.

## 2026-09-07 — baton.tuner — claim112077 — lifecycle complete, awaiting review

Implemented owner112006 / handoff112074's LIFECYCLE-PLAN in exactly its five
source/test/documentation paths. All incoming hashes matched split112022 before
editing. W112029's ordinary-test sources, tests and dossier were not edited.

Historical eligibility and verdict replay now prove the exact ended attachment,
committed verdict and fence, retained result manifest, accepted intake, required
retention decisions and the positive runtime.destroy journal. The driver takes
that read-only path before attempting quiescence or custody again, compares the
original completion and retention operands and returns the original ending.
Unresolved cleanup returns held rather than claiming success. REVIEW-CYCLES.md
now describes this lifecycle and the owner-approved ordinary-tests/independent-
review interpretation without manufacturing a reviewer-axis passed value.

### Proof and assertion scope

Both actual public-custody proofs pass through first verdict, real cleanup,
retained-byte reopening, integration_checkpoint and two exact ending replays.
The actual freeze interruption remains. They assert one worker, verdict, fence
and destroy, no replay writes and no repeated external calls. Six additive
negative tests cover missing/mismatched custody and result manifests, incomplete
retention, changed replay operands, missing/uncommitted history, wrong runtime,
destroyed-without-verdict and nonpositive/unresolved cleanup.

The manager axis case now records a verdict in a fresh eligible fixture for EACH
none/failed/unable value before checking the unchanged axis, one fence, one
verdict and exact eligibility. One added method runs under the two existing
ReviewCycles classes, increasing that suite69→71. The driver suite grows93→99.

Exact scheduled assertion edits, audited in evidence/lifecycle-112077/candidate.json:

- The ineffective `self.assertEqual(held, axis)` in the prior write/read-only loop
  is replaced by the fresh actual recording cases. All other original assertions
  in that test remain, including quiescence/findings/logs and no-side-effect checks.
- The whole-document verdict comparison is replaced by the four approved field
  mappings and separate recorded_at validation against the fixture clock. Every
  remaining field is compared exactly. All other custody assertions remain and
  the original two success test bodies are unchanged.
- `_endings` and `_frozen_endings` return a positive structured cleanup answer
  instead of None so their existing success/order assertions keep exercising
  the actual returned-outcome contract. No assertion was weakened or removed.

### Verification and limitation

From v12/python:

    PYTHONPATH=src python3 -B -m unittest tests.manager.test_review_cycles tests.job_manager.test_review_driver -v
    PYTHONPATH=src python3 -B -m unittest tests.manager.test_dependencies tests.manager.test_contracts_inventory tests.manager.test_boundary_inventory -q

Final focused result: **170 passed, 2.612s**. Final inventory result: **176 tests,
six failures, one skipped, 6.805s**. Logs are retained whole. An earlier inventory
run preceded the final retained-manifest check and is kept separately.

The six inventory failures are the named probe/ownership/universe checks in the
log. An isolated AST comparison against the retained before-source finds a NEW
orphan validation label, `review_cycles.py:_cleaned_review` / `a historical
review cleanup` (55→56 orphan calls). Unowned185 and the two untracked column
names are unchanged. Reported explicitly rather than attributed wholesale to
baseline. The required boundary-inventory attribution/probe disposition is
outside the assigned five paths and remains for independent review to allocate;
the source gate is not green. The comparison script changes only its in-memory
source snapshot, never the inventory test or application files.

No broad manager/subtree/live-engine run was repeated. Earlier broad failures
remain historical evidence and are not re-certified for this candidate. No live
provider, runtime, image, deployment, canonical target or authoritative database
mutation outside canonical Baton operations occurred. Temporary stores, negative
row corruption and deterministic transport are confined to disposable tests.

### Candidate

All five current hashes, exact added/changed test definitions, retained snapshots
and source/test deltas are in `evidence/lifecycle-112077/candidate.json` and
`candidate/`. Source hashes:

- review_cycles.py: `9b9e86680fedfb6f5667bd3c8cf0ec248a629d32d81e637c22414d9f6694382e`
- review_driver.py: `0ba2b2bb7adb9c6181cb843a4b90ddf5da6bd8dadd43ed9e6e5a5952020c2262`

Return to baton.bug for independent review, including the exact remaining
inventory diagnostic. W112039 still requires BOTH this lifecycle candidate and
W112029's ordinary-test admission before joined acceptance; no consumer gate is
released by this implementation handoff.

## 2026-09-07 — baton.tuner claim112312, bounded inventory correction

Owner112288 and review-2026-09-07T17-53-32Z.md revalidated. Implemented only the
newly assigned test_boundary_inventory.py path. Added an exact NOT_AN_ENTRY
declaration for the historical runtime.destroy document check as a property
chained onto the journal's adopted operations.result decode, plus a dedicated
reaching probe. This is not a generic exception or a new discovery rule: the
probe asserts the exact registered site/kind/label exists, completes the real
public custody lifecycle and positive no-effect replay, corrupts only that
disposable committed cleanup answer, then proves refusal at the named validator
and held replay without external acts/journal writes. Every existing function's
source bytes and every existing assertion are preserved. All original five
lifecycle paths remain byte-identical to claim112077.

Focused new probe/staleness checks: 2 pass. Required inventory gate: 177 tests,
6 failures, 1 skip (7.275s). Exact diagnostic comparison with the incoming
inventory against the same source snapshot: unowned185 unchanged; orphans56→55
with only the historical-cleanup label removed; untracked columns2 unchanged.
The gate remains red; prior failures are neither fixed nor waived. Full output,
source/test byte snapshots, delta, AST/source-preservation audit and six hashes
are under evidence/correction-112312/. After relocating the new method below
the unchanged class docstring, the two focused checks passed again.

P1 remains open: existing custody adoption requires an adapter image identity
that historical eligibility does not possess. The actual public-custody seam
probe confirms that exact blocker for both roots, with positive actual-adapter
controls and no repeat acts. Review explicitly required identifying this before
expanding custody/intake. CUSTODY-READER-SCOPE.md gives the exact additive
custody.py/test_custody.py allocation and reader contract for ops disposition.
No custody/intake implementation or invented adapter was introduced. The nested
malformed/foreign cleanup issue is still present; this partial delivery does not
claim source acceptance. Return to ops for the concrete missing owner seam, then
complete the bounded source correction and independent review. All joined and
downstream gates remain intact.

## 2026-09-07 — baton.tuner claim112385, nested custody correction complete for review

Owner112383 approved CUSTODY-READER-SCOPE.md. Implemented the additive
custody.historical_directory_custody reader with no adapter operand. It derives
the existing normalization operation identity at custody, requires a committed
record of the exact kind, validates the closed signature/operands and historical
image text, and replays against the exact attempt/root/verb/current recorded
workspace-store signature. The image remains historical evidence; this does not
select or certify the current deployment image. It requires the closed receipt,
exact attempt/root/verb/operation and the canonical normalization account, using
custody's existing _accountable owner. Missing/refused/wrong records or malformed
accounts refuse. Existing normalization/adoption APIs and journal formats are
unchanged. No normalizer, helper, filesystem repair or new adapter is used.

review_cycles._cleaned_review reads both result/workspace owner receipts and
compares the entire nested mapping in the committed cleanup answer. Empty/scalar/
partial/foreign/additional nested custody is insufficient. All earlier attachment,
verdict/fence/result/intake/retention/runtime checks remain. REVIEW-CYCLES.md
now states that exact nested proof. review_driver.py and test_review_cycles.py
remain byte-identical to the incoming accepted-scope candidate.

Additive tests: four owner tests plus one damage helper, two actual-public-custody
driver tests, one five-label inventory reaching test. Every existing test method
retains its complete source bytes. The only changed existing test helper is
custody_probes, with two additive caller/root entries; corresponding root
delegation is added. Five exact custody validator declarations follow the
journal's already adopted signature/result decode and are individually exercised
at their named labels without external actions or journal changes. The prior
cleanup declaration and reaching test remain unchanged. No discovery rule,
existing assertion, unrelated inventory entry or W112029 file was changed.

Verification for final source/test bytes:

- Full focused custody/manager-review/driver suites: **293 pass, 6.622s**.
- Required inventory gate: **178 tests, 6 failures, 1 skip, 6.955s**. All six
  failure identities match incoming baseline. Exact source+inventory comparison
  records unowned185→185, orphan55→55 and untracked columns2→2 with empty
  added/removed sets. The required gate remains red; nothing is waived.
- Reviewer112223's probe was copied byte-for-byte into this claim's evidence
  and run on the corrected source. Positive control still accepts and replays
  exactly; empty/scalar/missing-workspace/foreign-attempt nested custody all
  refuse eligibility and return held/cleaned_up=false. One worker/destroy and
  no repeated external acts or journal writes are preserved.
- git diff --check passes. No Git state mutation or live runtime occurred.

During new test development the first draft tried a pending operation row that
the existing SQLite schema correctly rejects (only committed/refused are legal)
and expected an external act on an already recorded normalization. Corrected
only those newly added fixtures: the refused row now has a sealed refusal and
NULL result, and replay preserves its captured call count. One new inventory
test initially lacked its local mock import; that new fixture was corrected.
The final suites above pass these cases; no existing expectation was weakened.

All eight candidate hashes, exact before/candidate bytes, individual deltas,
existing-test-source audit, full outputs and diagnostic/probe scripts are under
evidence/custody-reader-112385/. handoff-manifest.json SHA-256:
9855df426d5838c34697d48960c9ccd4417d79db388c12a0870aede438e3fad4.

Return the complete candidate to baton.bug for independent review. Source
acceptance and W112039 joined/downstream gates remain with their reviewers;
no consumer is released by this implementation claim.
