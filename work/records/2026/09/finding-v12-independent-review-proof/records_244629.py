"""Claim-244629 dossier entries: the satisfied prerequisite, and G1/G2."""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent

FINDING = """
## 2026-09-23 -- the prerequisite is satisfied, and what it settled

W239528's live baseline was independently accepted by
[review-2026-09-23T04-15-56Z.md](../finding-v12-single-implementation-proof/review-2026-09-23T04-15-56Z.md)
(reviewer claim 244558, owner execution claim 244464), which accepts "the
narrow successful implementation/proposal/custody/stopped-runtime/positive-
cleanup baseline". PLAN step 1 is therefore done. It was accepted on the
COMBINED retained and independent evidence that review names, and this Job
should carry its limits forward rather than round them off:

  * No Authority, Job or Control SQLite store was opened by that reviewer, so
    ledger completion and publication state remain the retained supervisor's
    account. The line state this Job attaches to is read directly here, and
    `PROGRESS.md` records what was read and how.
  * The reviewer recorded a metadata discrepancy it explicitly did not treat
    as proof of a 3600-second invocation: `proposal/result.json`'s
    `provider.seconds_bound` is 3600 while `outcome.provider_turn` reports the
    selected 180. It is a retained diagnostic for a bounded follow-up, not an
    input to this Job's bounds.
  * That run was 7.485 provider seconds and exercised no timeout enforcement.

WHAT THE SUBJECT ACTUALLY IS. Read read-only from the accepted run's own
control store under this claim: v12 Authority `7ea319da93384b77bc3ddea38602d7a3`,
v12 Work `7ea319da-W1`, line
`line-0d5b62ba32f714e3dd0a8bb8a2c88ed1622ad5cf1dbf5db1d3bd40e0af044c8d` in
state `review-ready` at revision 1, current checkpoint
`checkpoint-ab8207baa93b5abc12393a67c1e04046e14bebd7e9defdf0940e168203b711a9`,
`frozen`, digest `sha256:9d3aa3ca7733d4ec983b5841f1b99be09e4dc98bdb45c8b255890772acdd9324`,
base `cee07eeb`, head `f84ae35d`, tree `5b4c0f45`, one changed path
(`harness.py`). Its producer is writer
`writer-a67688eb...`, worker `implementation-worker`, participant `baton.impl`,
principal `principal:baton.impl`, now `revoked` with reason `checkpoint`. The
line holds NO review attachment. The proposal is attachable and nobody has
reviewed it.

## 2026-09-23 -- G2 is answered: the separate Job recovers the line

W244180's preparation left the cross-Job binding open, and rightly: "A
brand-new unrelated line has no accepted producer checkpoint; copying the
proposal file or supplying a new Work ID does not create that provenance."

The supported arrangement is that the reviewer Job brings its OWN Job store,
submission, stage, attempt, criteria and outcome, and RECOVERS the producer's
line rather than creating one. `create_line` derives `line_id` from
`(authority_uuid, work_id)` alone and replays its committed creation when the
row is already there; `StageDeployment.line_for` calls it with the deployment's
Authority and the binding's `job_work_id` on every tick, so a second deployment
naming the same v12 Authority and Work reaches the same line and
`StageComposition._prepare` takes its current checkpoint. No row is copied, no
writer or checkpoint is manufactured, and no validator is weakened.

FOUR THINGS ARE NECESSARILY SHARED, and the reason is the product's, not a
convenience: the v12 Authority and Work (they ARE the line's identity), the
control store (the line, writer, checkpoint and attachment are rows in it), and
the workspace storage and nominated source (`create_line` recomputes
`line_path` from the control store's own configured storage and refuses an
`operation-collision` on any difference, then `_validate_line_object` re-proves
device and inode -- so a copy of the retained tree at another path is NOT
available, and running the review against a copy is not proposed).

THE SEPARATION IS REAL AND IT IS ELSEWHERE. The distinct v11 Work, claim,
dossier and evidence are preserved; so are the Job store, Job identity,
submission, stage, attempt, generation, criteria, launch home, credential home,
private-context storage, deployment state and outcome. Independence is decided
by `attach_review` on worker, participant and principal, and the producer's
three (`implementation-worker` / `baton.impl` / `principal:baton.impl`) differ
from the reviewer's (`review-worker` / `baton.review` /
`principal:baton.review`) on all three.

THE COST OF THAT ARRANGEMENT, STATED PLAINLY: the review appends its rows to
W239528's retained control store and its boundary under W239528's workspace
storage. It does not rewrite the producer's artifacts, and it cannot -- but
"separate execution" here means separate Job and evidence, not a separate
filesystem root, and a reader should not be left to infer otherwise.
"""

PLAN = """# Current action -- the review Job's own composition

1. DONE. W239528's retained proposal and cleanup are independently accepted
   (review-2026-09-23T04-15-56Z.md). See FINDING for what that acceptance
   covers and what it explicitly does not.
2. DONE. The attachment arrangement is established and proven:
   `attachment.py` and `test_attachment.py`. Producer/reviewer independence
   and wrong, stale and foreign checkpoint rejection are each driven through
   the real `review_cycles.attach_review` against a real `ControlStore`, and
   the preflight's account is required to agree with the validator's.
3. DONE. The review-only composition: `review_bindings.py` and
   `test_review_bindings.py`. One review stage, `findings` and `logs` both
   required, no `proposal` output, criteria that ask for a judgment instead of
   supplying one, and a subject READ from the producer's records so a packet
   naming the wrong proposal cannot be composed.
4. OUTSTANDING -- the bounded review-only supervisor, and it is the next
   claim's whole job. `PROGRESS.md` states the exact remaining scope.
5. OUTSTANDING -- the exact packet and operator commands, which wait on 4:
   `PACKET.json` names its supervisor and its digest, so composing one before
   the supervisor exists would be composing a packet that names nothing.
6. Then accept only a valid attributed verdict, stopped execution and positive
   cleanup. Pass the retained result to W236087; do not run correction here.

## Not in scope

No live execution, provider, container, recovery, implementation rerun or
resume. No closure of W239533 or W236087.
"""

PROGRESS = """# Implementer progress

## 2026-09-23 -- baton.claude, claim 244629

Owner reroute 244627. Read AGENTS.md policy, EFFECTIVE-BATON.md, W239533's
canonical state, its complete work-events, thread T239533 in full (2 messages,
no pagination remaining), this dossier, W244180's preparation in full and
W239528's accepted live review. Delivered items 1-3 of PLAN; items 4 and 5 are
outstanding and their exact scope is below.

**No file under `v12/` was edited, and no other dossier was written to.** The
accepted run's stores, artifacts and both images are untouched; the survey
opens the producer's control store through SQLite `mode=ro` and nothing else.

### What was delivered

`attachment.py` -- the supported arrangement, and the answer to G2. It reads
the producer's retained control store READ-ONLY, composes the immutable
subject, and answers the exact refusals. G3 in W244180's checklist is the
reason it is not `ControlStore.open`: that path can initialize or migrate a
store, and a survey that migrated W239528's accepted evidence would have
altered the thing it was asked to describe.

`test_attachment.py` -- 15 cases over a REAL `ControlStore` with a real line,
writer and frozen checkpoint built through the supported `review_cycles` API.
Every refusal case asks BOTH accounts about the same store and requires them to
agree, because a preflight that restates a validator's rules and then drifts
from them is worse than no preflight. Covered: the accepted proposal is
attachable by an independent reviewer; a second Job recovers the same line
while a different v12 Work reaches a different line with no checkpoint; a
checkpoint this line never held; a real frozen checkpoint belonging to another
line; a genuinely superseded revision; self-review on all three identities and
on each one alone; a line under correction; and that the survey moves no byte
and leaves no journal companion beside the store.

`review_bindings.py` and `test_review_bindings.py` -- the review-only
composition, 19 cases, composed against that same real line.

### Three things the measurements corrected, left visible

**`immutable=1` was wrong and the test found it.** The read-only opener first
used `mode=ro&immutable=1` to guarantee no lock or journal file appeared beside
the retained store. These stores are journalled `wal`, and `immutable=1` makes
SQLite ignore the write-ahead log: against a store whose last commits are still
in the log it answers a SILENTLY STALE picture. The symptom was a refusal
reporting "no lines at all" about a store holding one. `mode=ro` alone, and the
docstring says why rather than quietly dropping the flag.

**A stale checkpoint cannot be manufactured, only produced.** The first attempt
granted a second writer to make a second revision and was refused -- "line
state 'review-ready' does not admit a writer". The case now runs the real
correction round (attach, `changes-requested`, correction writer, freeze), which
is the only way a checkpoint becomes stale.

**`attach_review`'s writer-coexistence branch is defensive, not ordinary.**
Reaching "read-only review cannot coexist with a writer" from `review-ready` is
impossible, because that state admits no writer; by the time one is active the
line has left `review-ready` and the earlier precondition refuses first. The
case proves the reachable thing and names which refusal actually fires.

### Exact remaining scope

1. **The bounded review-only supervisor.** W239528's `baseline.py` is closed
   over `implementation` and W236087's `supervisor.py` requires at least one
   implementer invocation, so neither is it -- G1 in W244180's checklist stands
   exactly as written. It needs: `KINDS` closed over `review`; one admission,
   retry disabled; finite turn, total and reserved cleanup limits with an
   actionable no-progress rule; admission closed before cancellation; every
   discovered attempt accounted for; the ordinary ending and cleanup path
   driven; an outcome published on interruption and on failure; verdict
   evidence (`review_verdict_from_result`, attribution against the attached
   checkpoint's base/head/tree) where `baseline.py` gathers proposal evidence;
   and an explicit refusal to open a correction on `changes-requested`.
2. **`review_bindings.write` held against the manager's own validator.** The
   19 composition cases inspect the in-memory documents; they do not run
   `write`, so `stage_execution.held_configuration` has not yet been asked
   about this deployment over a disposable Authority and no `PACKET.json` has
   been produced. `test_review_bindings`'s docstring says so in place rather
   than leaving a reader to assume coverage.
3. **The packet and the operator commands.** They wait on 1: `PACKET.json`
   names its supervisor path and digest.
4. **The real-provider question, once 1-3 exist.** Whether the actual reviewer,
   given these criteria and the retained bytes, returns its own valid report
   through the production boundary. Deterministic checks cannot establish it,
   and no live run is selected or authorized here.

Also outstanding and not this Job's: the `seconds_bound` 3600/180 metadata
discrepancy the accepted review retained for a bounded follow-up.

Verification: 34 focused deterministic checks, 0 failures, measured
0.4300506520085037s, receipt `verification-1.json` with `verification-1.log`.
No container, image, live provider, network, credential or operator deployment.

Cumulative measured for W239533: **0.430050652s** (this is the Job's first
claim; W239528's and W236087's budgets are their own).

State: returned for independent review with the remaining scope above.
"""

OWNERSHIP = """# File ownership for W239533

Claim 244629, baton.claude.

## What this claim created and owns

    attachment.py             the supported checkpoint-attachment arrangement
    test_attachment.py        15 real-boundary cases over review_cycles
    review_bindings.py        the review-only composer
    test_review_bindings.py   19 composition cases over a real line
    verify.py                 the measurement that writes the receipt
    verification-1.json/.log  that receipt
    records_244629.py         this claim's dossier writer
    PROGRESS.md               this implementer's record
    OWNERSHIP-239533.md       this file

`FINDING.md` and `PLAN.md` were appended to and rewritten respectively, as the
owner reroute directs ("Update FINDING/PLAN for the satisfied prerequisite").

## What it READS and did not edit

`work/records/2026/09/finding-v12-single-implementation-proof/` in full. It is
W239528's, that Work is open pending owner disposition, and its accepted live
review is this Job's prerequisite. `review_bindings.py` IMPORTS its
`baseline_bindings` helpers -- reuse, not modification -- and `verify.py`
records that module's digest so a drift is visible in the next receipt.

`work/records/2026/09/finding-v12-review-job-preparation/` in full. It is
W244180's. Nothing here was written into it; G1, G2 and G3 are answered or
carried forward in this dossier's own files.

`work/records/2026/09/finding-v12-managed-session-resume/` was not touched.

## Product and deployment

**No file under `v12/` was edited.** `tests.manager.test_review_cycles` is
imported as a fixture and `review_cycles`, `review_driver` and
`stage_execution` are read; all four digests are recorded in the receipt.

`/home/sl/baton-runs/single-implementation-244216/` was READ and not modified.
Its control store is opened only through SQLite `mode=ro`, and
`TheSurveyOpensTheStoreWithoutChangingIt` measures that the survey moves no
byte and leaves no journal companion. No image was built, retagged or removed.
No store was migrated, no runtime started and no Git operation performed.
"""


def main():
    finding = HERE / "FINDING.md"
    if "claim 244629" not in finding.read_text(encoding="utf-8") \
            and "the prerequisite is satisfied" not in finding.read_text(
                encoding="utf-8"):
        finding.write_text(
            finding.read_text(encoding="utf-8").rstrip("\n") + "\n" + FINDING,
            encoding="utf-8")
    (HERE / "PLAN.md").write_text(PLAN, encoding="utf-8")
    progress = HERE / "PROGRESS.md"
    if not progress.exists() or "claim 244629" not in progress.read_text(
            encoding="utf-8"):
        progress.write_text(PROGRESS, encoding="utf-8")
    (HERE / "OWNERSHIP-239533.md").write_text(OWNERSHIP, encoding="utf-8")
    print("records written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
