# W63255 pre-attach abandonment fence — implementation handoff

Advisory Work W174050, claim 174060, baton.claude via baton.impl.
**Read-only pass. Nothing was executed:** no test, probe, provider, model,
engine, build, Git mutation or worker. No product, test or original dossier was
edited. Advice for the future W63255 implementer; **not acceptance**, and it
grants no implementation scope.

Baseline: live tree, 2026-09-15, under claim 174060. Provisional.

**Already decided, not reopened here:** `--abandon` stays supported and the
fence is implemented (owner, 2026-09-14T11:40:26Z). The 2026-09-02 approved
technical direction stands. Release-surface exclusion is not on the table.

## 1. The failure path is unchanged and the correction still applies

`v12/python/tools/dogfood_operator.py`:

    2456    if state is None or state["runtime_id"] is None:
    2457        record["branch"] = "pre-attach"
    2458        return _pre_attach_recovered(record, store, adapter, given,
    2459                                     orphan=orphan, launch_home=launch_home)

    2905    def _pre_attach_recovered(record, store, adapter, given, *, orphan,
    2906                              launch_home):

**The helper still receives neither the Authority port nor the operator's
reason.** No authority operation is reachable on that branch, so
`authority_fence` is necessarily null while `resolved` can still become true
from resource facts alone. That is precisely the 2026-09-01 root cause, and it
is still true today.

## 2. Reusable boundaries — all present, unchanged in shape

| Symbol | Location | Why it is the right piece |
| --- | --- | --- |
| `_abandon_intent` | `src/baton_v12/worker_manager/intake.py:3194` | Commits or replays the declaration **before any external call**, so a crash between steps resumes from what was declared. Signature carries `attempt_id`, `expect`, `runtime_id`, `reason`, `authority_operation_id`. Fresh eligibility is checked *inside* the write transaction; a replay deliberately does not re-check. |
| `_abandon_fence_operation_id` | `intake.py:3179` | The authority's effectively-once identity, **distinct from both** `attempt.cancel:*` and the declaration — "three identities because they are three acts". |
| `AuthorityPort.cancel` | `src/baton_v12/worker_manager/authority_port.py:392` | Proves the authority fenced the exact four-member assignment; refuses a fence that ended somebody else's. |
| `abandon_attempt` | `intake.py:2259` | The attached sibling. **Do not weaken it** to accept a null runtime. |
| `request_cancellation` | `attempts.py:2757` | Can fence without a runtime but requires agent and runtime-stop capabilities the pre-attach path does not own. **Not a shortcut.** |

`runtime_id` being `None` in the intent signature is coherent — the declaration
records the world as it was, and for a pre-attach attempt that world has no
runtime.

## 3. Evidence discipline — what is covered, and the one demonstrated gap

I read the test bodies, not the names. Distinguishing the four things the
FINDING asks me to keep apart:

**Existing implementation + test bodies + recorded passing evidence**, on the
**attached** branch:
- `tests/tools/test_dogfood_operator.py:5187
  test_an_attached_attempt_ends_and_its_credential_is_torn_down` asserts
  `branch == "abandonment"`, then `authority_fence["fenced"]` true, cleanup
  `retained`, runtime `absent`, credentials `torn-down`, `resolved` true, the
  host clean on the filesystem, and `output == "open"` /
  `worker_disposition == "none"` unpromoted.
- Further fence assertions at `:5909`, `:6009`, and fence membership in the
  record shape at `:6544` and `:6667`.
- `tests/manager/test_attempts.py:2184
  test_a_restart_after_the_declaration_reissues_one_authority_fence` covers the
  crash-after-declaration replay for the attached path.
- `tests/tools/test_quiescent_assignment_finalization.py:755-758` and `:809`
  cover W61984's finalizer fence and its refusal-becomes-an-account case.

**Existing test bodies on the pre-attach branch — none assert a fence:**
- `test_dogfood_operator.py:5010` onward is the pre-attach block. Its cases
  assert credentials, runtime, zombie rows and `unresolved` text. `:6976`,
  `:7009`, `:7048` (ambiguous, listed-twice, mismatched candidates) each assert
  `branch == "pre-attach"` and that nothing was stopped.
- **No pre-attach case asserts `authority_fence` at all.** Every one of the four
  `authority_fence` assertions in that file is on the attached branch, and one
  of them states `branch == "abandonment"` two lines earlier.
- **No pre-attach case asserts `resolved` true.** The two `resolved`-true
  assertions at `:5191` and `:5212` both build `self.attached()`.
- The direct call at `:5422` passes `object()` where the port would go —
  positive evidence that the helper takes no port and uses none.

**Therefore the gap is demonstrated, not inferred:** the pre-attach branch has
no fence in the implementation and no fence in its coverage. I am stating this
after reading the bodies because filenames are not coverage — a lesson from my
own W156162 correction one claim ago.

**Uncertain, and labelled so:** I did not search every test module for an
end-to-end command-level pre-attach case outside
`test_dogfood_operator.py`/`test_quiescent_assignment_finalization.py`. The
implementer should confirm before adding a duplicate.

## 4. Smallest source and test ownership set

**Source (2 files):**
- `src/baton_v12/worker_manager/intake.py` — add the public pre-attach
  abandonment fence operation beside the existing abandonment pieces, factoring
  `_abandon_intent` / `_abandon_fence_operation_id` rather than duplicating.
- `v12/python/tools/dogfood_operator.py` — pass `port` and `reason` into
  `_pre_attach_recovered`, call the new operation, and require the recorded
  fence before `resolved`.

**Tests (2 files):**
- `tests/manager/test_attempts.py` or a sibling manager module for the new
  operation's own cases (replay, collision, race, precondition refusals).
- `tests/tools/test_dogfood_operator.py` for the command-level regression, in
  the existing pre-attach block at `:5010`.

**Do not touch:** `abandon_attempt`, `request_cancellation`, W61984's finalizer,
or `AuthorityPort.cancel`. The approved direction says so and the tests above
pin their current meaning.

## 5. Ordering — the part most likely to be got wrong

The approved sequence, restated with the mechanism made explicit:

1. **Read the atomic projection.** Require the fixed assignment, matching
   participant, `runtime_id is None`, `execution_runtime == "not-started"`,
   worker disposition `none`, output `open`, nonterminal cleanup.
2. **Commit the abandonment intent and the no-start state in one
   transaction.** The axis vocabulary is
   `("not-started", "start-requested", "running", "cancel-requested",
   "stopping", "quiescent", "uncertain", "destroyed")`, and
   `request_runtime_start` refuses unless it reads `not-started`. Moving off
   `not-started` atomically with the intent is what makes the race safe in both
   directions: if a start won first this operation refuses **without fencing**
   and a fresh observation selects the attached branch; if the intent won,
   `request_runtime_start` can no longer pass its precondition.
3. **Then** `AuthorityPort.cancel`, using the **adopted intent's** assignment,
   operation id and reason — not the caller's freshly derived ones. The intent
   is the authorization; that is why every member of it is compared.
4. **Only then** the existing positive-absence proof and credential/launch
   cleanup, unchanged.
5. `resolved` additionally requires
   `authority_fence == {"fenced": true, "generation": <fixed generation>}`.

Replay uses the same intent and the same authority operation. A changed reason
collides; a changed attempt or fixed assignment is a different operation. The
operation accepts no output, settles no custody, makes no retention decision and
invokes no finalizer.

## 6. Focused acceptance — proposed, not executed

Deterministic public-Authority/manager/command cases only:

1. **The fence happens and is recorded.** Activate, fail before attachment,
   abandon; assert `branch == "pre-attach"`, `authority_fence["fenced"]` true
   with the exact generation, and the public projection showing the Handler and
   live generation gone.
2. **A recovery without that proof exits nonzero** and writes `resolved: false`
   with the exact unresolved reason — the FINDING asks for this explicitly.
3. **The no-start race, both ways.** A start that wins first → refuse without
   fencing, and the next observation takes the attached branch. The intent that
   wins first → `request_runtime_start` refuses its precondition.
4. **Replay and collision.** Exact retry replays one intent and one fence;
   changed reason collides; changed attempt or assignment is not the same
   operation.
5. **Crash recovery** between declaration and fence resumes from the declaration
   — the attached analogue already exists at `test_attempts.py:2184` and is the
   model.
6. **Preserved semantics**, as regression: attached abandonment, ordinary
   cancellation and W61984's finalizer unchanged.

Pair each positive with the reversal that would catch a vacuous case —
especially 2 and 3, where "it refused" can be true for the wrong reason. Run
experiments under the same supervision as final runs and record failures too.
No broad suite, live model or engine is selected by the ruling.

## 7. Coordination recommendation only — two owner acts are still outstanding

The 2026-09-14 decision says in as many words that it "does not claim those
acts". Measured now, **neither has happened**:

- **W63255 is `phase: parked`**, `classification: confirmed-defect`, seq 168933,
  with `blocked_by: []` and `blocks: []` — no links at all.
- **W2 is `blocked_by` W161230, W161234, W156162, W103525, W61599 — and
  not W63255.**

So a Work the owner has declared a required minimum-release provider is parked
and absent from the release umbrella's dependency set. **I have changed
nothing** — this is a recommendation that the owner perform the unpark and add
the W2 dependency, as the decision itself anticipated.

## 8. Proposed wording reconciliation

- `RELEASE-CHECKLIST-167877.md`'s W63255 row still reads as a conditional
  ("require correction … **or** explicit positive release-surface exclusion
  evidence"). M167954's 2026-09-14T11:40:26Z decision supersedes it by name.
  Proposed for its owner; I did not edit it. (Also raised in the W161234
  pre-work, and still unactioned.)
- Where any dossier still frames cumulative test seconds as an allowance,
  `AGENTS.md` line 95 records that cumulative stopwatch budgets are not
  approval.

## 9. Assumptions and limits

- I ran nothing. Behavioural claims come from reading source, test bodies and
  recorded decisions; structural claims are file/symbol citations.
- §3's "uncertain" item is genuinely uncertain and labelled rather than
  commissioned as work.
- I did not read `evidence/research-2026-09-01/README.md`, which the FINDING
  says holds the detailed code paths and regression matrix. The implementer
  should read it before starting; my §5 and §6 are derived from the FINDING's
  own summary of it and may be narrower.
- Nothing here changes the original Work, its parked state, its route or the
  dependency graph, and none of it is a new release prerequisite.
