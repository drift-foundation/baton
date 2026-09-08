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
