# Progress

## Claim 174087 — baton.claude, advisory read-only pre-work

Claimed W174051 standalone at seq 174087, after returning W174050. Read this
dossier's FINDING.md and PLAN.md, the original W61599 record
`work/records/2026/09/finding-live-worker-log-observability/FINDING.md` through
its 2026-09-01 implementation decisions and the 2026-09-14 minimum-subset
selection, the current activity source in `tools/dogfood_operator.py`
(`_Channel._drain`, `_report`, `_activity_observer`), the owner
`worker_manager/attempts.py:427 observe_activity`, and the **test bodies** in
`tests/manager/test_attempts.py`, `tests/tools/test_dogfood_operator.py`,
`tests/tools/test_job_viewer.py` and `tests/job_manager/test_status.py`.
Claimed no original Work.

**Each of the four selected corrections was traced to source and then checked
against read test bodies**, and they do not all have the same status:

- **Outer-stderr misclassification** — defect confirmed, and the current
  behaviour is *pinned by an existing assertion*
  (`test_every_byte_is_counted_including_the_ones_discarded`). The correction is
  therefore not purely additive; the implementer must name that method and its
  changed expectation before editing. This is the finding most worth having
  before planning the slice.
- **Publisher backpressure** — demonstrated gap. The existing case covers an
  observer that *raises*; `_report` still calls the observer synchronously, so a
  *slow* store stalls the drain. No case makes the observer slow.
- **Zero-byte EOF stamp** — demonstrated gap, confirmed at the owner: `_drain`
  publishes unconditionally at EOF and `observe_activity`'s
  `activity_bytes IS NULL` clause stamps a fresh instant for a zero total. No
  test exercises a zero first observation.
- **Restart honesty** — partly covered (never-observed versus zero, the viewer's
  `unknown`, the running-stage projection); whether any case carries activity
  across a manager restart is **labelled uncertain rather than commissioned**,
  because I did not search exhaustively.

One genuinely open design question is recorded with a recommendation rather than
as a request for a ruling: whether the zero-stamp fix belongs in the caller or
at the owner.

Deliverable: `PREWORK.md`,
`sha256:6e3c90fac64e3eaf79a9a1f625ff1df09936cd8402219d947fedb9cd655d4ded`.

**Boundaries honoured.** No test, probe, provider, model, engine, build, Git
mutation or worker; no product, test or original dossier edit; deferred
items 5b/6/7/9 not revived. Verification spending this claim: **zero measured
seconds**.

## Claim 174145 — correction after owner reroute 174118

The owner rerouted this advisory Work to read the full
`review-2026-09-01T14-24-19Z.md` and current `PLAN.md`, trace a concrete
provider-safe native activity producer through the worker/deployment boundary,
and correct the unsupported one-source-file scope claim.

**All three are warranted.** My §6 said plainly that I had not read the review
or the PLAN item list — and I then made scope and coverage claims that reading
them would have prevented. Two specific errors:

- **The one-source-file scope claim is wrong.** The correction is not a change
  to how the existing stream is counted; it is wiring a *different* stream that
  is produced inside the container. `ClaudeAgent._ran_provider` owns a private
  provider-stdout pipe read inside the container, provider stderr is `DEVNULL`
  and never opened, and neither `baton_worker.py` nor `dogfood_entry.py` writes
  progress to stderr. The correction names the required worker-side and
  deployment-side paths and three explicitly unresolved producer facts — which
  native source, which seam, and how the read stays content-free — rather than
  proposing a design, because the review makes proving the source a
  precondition.
- **The zero-byte case IS pinned by an existing test.** I claimed no body
  exercised it; `test_a_silent_worker_is_observed_as_silent_and_not_as_unobserved`
  asserts `seen == [0]` and argues the position in its docstring. The review had
  already said so. So *both* corrections change existing assertions, not one.

Also withdrawn: the caller-versus-owner escalation, which the reroute says needs
no owner gate. Also newly recorded: the review's measured blocking-observer
reproduction and the 5,000 ms `ControlStore.open` busy timeout, which corroborate
the backpressure gap my report reasoned to without evidence.

`PREWORK.md` now carries the correction appended after the original text.
`sha256:65243e410ae3526b1895c7f53bfae9453b8b8e933db04953889fdd27ce5778c9`.

Read-only throughout. Verification spending this claim: **zero measured
seconds**.
