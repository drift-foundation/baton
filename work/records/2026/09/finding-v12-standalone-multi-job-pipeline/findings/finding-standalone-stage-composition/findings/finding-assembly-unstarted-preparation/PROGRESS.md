# Progress

Implementation entries belong to the assigned change author.

## 2026-09-08 — W119113 claim119155 — baton.claude — awaiting review

**Delivered: the never-started preparation correction, and nothing wider.**
Two paths changed, both inside the accepted five-path assembly scope:
`v12/python/tools/stage_execution.py` and
`v12/python/tests/tools/test_stage_execution.py`.

### Revalidation before editing

The pinned rulings were re-read against the current tree, not from memory.
`../finding-shared-stage-assembly/FINDING.md` and its
`review-2026-09-08T12-41-47Z.md` both stand, and the tree still carries the
exact reviewed candidate hashes for all five assembly paths — so review
119091's P1 is a live finding against these bytes and not a stale one.

**The reported permission blocker is gone and I am not repeating it.** My
previous account under claim118937 said the assertion change had no owner
approval. That account is history and is preserved where it was written; it is
not current authority. M118923 approved the exact observed-then-prepare
expectation at 12:19:42Z, before that claim, and M118986 reconfirmed it. The
approval is pinned in this record's FINDING and in the parent's. No new
disposition was requested and none was needed.

### The source correction

`Integration.run` took a published delivery with an assignment straight to
`admit_accepted` whenever the runtime was `not-started`. `integrate_next`
proves the runtime `not-started` and then asks the port to run, and a
reconstructed port holds no execution-local credential delivery — so the
attempt could never start again. The later-tick branch now splits:

- `execution_runtime == not-started` → `port.prepare(stage, job)` and then the
  same single admission. No refresh is reached, because reconciling an attempt
  no start was ever requested for is the write that path refuses.
- anything else → the unchanged `refresh`, then `may_continue`, then either
  the normal continuation or the admission hold. A started or uncertain
  attempt is **not** prepared: preparation mints a bearer only for a runtime
  that has not started, and the custody of a runtime this execution did not
  start belongs to that runtime.

No credential is minted inside admission, the closed W110774 port provider is
untouched, and no operand, path or driver interface moved. The correction is
one hunk: inverting it reproduces the reviewed
`dee7a1c9e20831f25d2edd1727dbd7acf767c0aa00658d76174bcd065006d3ca` byte for
byte.

### The test changes

**One existing test method changed, and it is the approved one.**
`TheIntegrationStageConsumesTheAcceptedPort.
test_a_delivery_with_no_started_runtime_is_not_refreshed` now records
`observed` then `prepare`. Its other three assertions — no refresh, exactly
one admission, no continuation — are unchanged, which is what makes the
preparation the whole of the delta. Everything else is additive:

- `test_a_started_or_uncertain_runtime_is_never_prepared_here`, the other side
  of that branch over both held states.
- `AFreshPortReentersANeverStartedDelivery`, the focused acceptance, over the
  **real production `IntegrationRuntimePort`** and the port suite's composed
  world — real Worker Manager, coordinator, Authority, delivery namespaces and
  both accepted drivers, with the deterministic engine and child-process
  provider standing in for a daemon and a model. It borrows that fixture by
  composition rather than subclassing, which is the inflation that suite's own
  docstring records. Five cases: the valid initial tick prepares and starts
  exactly once; a same-execution second tick refreshes, continues and starts
  nothing again; an admission interrupted before `port.run` really does leave
  a published assignment over a `not-started` runtime with zero engine starts;
  a fresh port over that delivery prepares it, does not refresh it and starts
  it once; and a runtime this execution did not start is answered `held` with
  no preparation, no second start and no second credential minted.
- `TheFactorysOwnOperandsReachTheIntegrationStage`, review 119091's own
  independent controls kept as ordinary tests over the actual
  `operations_from` factory: requirement derivation from the held producer,
  a task document replaced after construction changing nothing, a producer
  naming no verification refusing, a Job naming another producer's input
  refusing, and the nominal `WorkspaceGroup` adopting a really materialized
  delivery.

The world's own required-test selection is substituted in the real-port cases
and only there: that borrowed deployment carries no configured workers to
derive one from, and the derivation has its own real-factory cases above. No
public reader is mocked at the boundary being proved.

### Verification

From `v12/python`, `PYTHONPATH=.:src python3 -m unittest -v
tests.tools.test_stage_execution tests.tools.test_integration_worker
tests.tools.test_single_worker tests.integration.test_driver`:
**308 tests, OK, 15.070s**.

Against the reconstructed pre-correction source the three affected classes are
**19 tests, 1 failure and 1 error**, refusing with `has no credential delivery
from this execution's own preparation` — review 119091's exact measurement.
The other 17 pass on both versions.

**No whole-subtree run was performed, deliberately.** The retained gate log
`b4f19ea440037846d4e1a5b0abfb3a84e4a0d8da05e1e66fa01770c4fe4f70c6` (5167
tests, 275.509s, 28 failures, 21 skips) is audited rather than repeated: its
actual diagnostics are 24 boundary-inventory failures and 4 engine-cleanup
failures, none in `tools/` or `tests/tools`, all owned by
`work/records/2026/09/finding-v12-unresolved-suite-checks/` and unwaived.
Rerunning it would not answer the composed lifecycle, which is W119114's.

Evidence: `evidence/implementation-119155/` — `EXECUTION.md`, `focused.txt`,
`prior-source-regression.txt`, `prior-stage_execution.py`,
`assertion-audit.json`.

| Path relative to `v12/python` | SHA-256 |
| --- | --- |
| `tools/stage_execution.py` | `db280363bf8e1f7bc534a25dd163275a87aad3a21d784d330801823ce9f3cb60` |
| `tests/tools/test_stage_execution.py` | `44dd0d4ccef341f4d33e41560a46fef4987b37fd8dc2d64f812e9b8884534b54` |
| `tools/single_worker.py` | `5dfd0df1b393f87e6a48e75f0845b266c73d2929e5cd6ad53509e1c02ef9dc27` (unchanged) |
| `tests/tools/test_single_worker.py` | `95808aee8529d27bab0519f3fe8d45ae4e51507594c4825495530a8882d9af6c` (unchanged) |
| `tools/parallel_test.py` | `f00fec0efebca9df1e25c025d1c9f07d350d1c79f0f0c880e673888bac884547` (unchanged) |

`parallel_test.py` needed no entry: its registry names modules and
`tests.tools.test_stage_execution` is already among them, so the two added
classes are picked up without touching the shared registry W110774 owns.

### Not delivered here, and not claimed

The complete one-Job lifecycle, retained custody, the reconstructed-manager
restart and the preserved operator-held uncertain integration remain
undelivered and are W119114's, serially after this correction is accepted.
This entry claims the bounded correction and nothing else.

**State: awaiting independent review.**
