"""Claim-242687 dossier entries and the post-edit product hashes."""
import hashlib
import json
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[4]

PRODUCT = {
    "v12/python/src/baton_v12/job_manager/review_driver.py":
        "b5b22535ef105f786aa74f61ff894614a1e91bb8e2739f1051151fb893ebe10c",
    "v12/python/tools/stage_execution.py":
        "33c780916a115890767bb79cc3a2dcedc6ec588fb1da08e95490cd7897cd6e81",
    "v12/python/tests/manager/test_claude_context.py": None,
}

PROGRESS = """
## 2026-09-22 -- baton.claude, claim 242687, the expired-credential failure path

Owner pass 242683 after the accepted command RAN. The provider's OAuth token
had expired; the run reported nothing for 900 seconds and left its container
standing. The owner selects failure handling BEFORE credential renewal and
leaves the credentials expired. That decision was recorded in FINDING and PLAN
before any implementation, as the pass requires (`pin_242687.py`).

No credential renewal, no live rerun, no destructive recovery, no reviewer
stage, no resume. `/home/sl/baton-runs/single-implementation-239528/run` was
read and not modified, and no store belonging to it was opened; `live-242687/`
holds a read-only copy of its outcome, task, submission, four exchange events
and both provider logs.

**Reproduced first, from the run's own bytes.** Replaying the retained provider
stdout through the real `ClaudeAgent`, the real ending driver and the real
composed stage gave the live outcome exactly: `implementation answering`,
`stopped overall-bound-exceeded`, no committed cleanup, same shortfall. The
manager's own deferral row named the cause.

**Two defects, and the second only became visible once the first was fixed.**

1. `review_driver.end_implementation` performed publication as an
   UNCONDITIONAL step seven. `integration.retain_proposal` refuses -- rightly
   -- a frozen result that is not `completed`, so steps eight and nine (fence
   the assignment, `authorize_cleanup`) were never reached. `PUBLISHABLE`
   states the rule the module already states for its other ending, and all
   three entry points read it. Cleanup then committed positively -- and the
   stage still sat in `answering` for the whole bound.
2. `stage_execution`'s composed conclude returned `outcome: "held"` for a
   non-completed contextual turn. Holding the CONTEXT USE is right and is
   kept; `outcome: held` is the review vocabulary for "nobody may be scheduled
   on this", and `_finished` reads it as "the ending did not finish" and
   returns before `settle_ending`. Two different facts had one answer. The
   context hold now travels as its own member and the obligation settles.

**Measured on the same bytes**: before, `overall-bound-exceeded` at tick 901
with no cleanup; after, `exceptional` at tick 3 with `retained`/`absent`
cleanup, `outstanding_cleanup: []`, `state: held`, no proposal and no false
success. All four of the owner's requirements have their own check in
`test_failure_path.py`, which pins the retained bytes by digest.

**The reporting is actionable now.** The live run said
`KeyError: 'baton.git-proposal/1'` -- this program's own lookup. `_proposals`
reads the frozen disposition first, reports `ended 'unable' ... read the
attempt's retained provider log`, and the outcome carries a
`workload.dispositions` member so a failed run says what happened where an
operator can find it. A turn that froze no result at all is distinguished from
a completed one whose proposal could not be read.

**Nine accepted product tests changed expectation, and this is the part to
review first.** `tests/manager/test_claude_context.py` asserted through
`assert_owed` that an unhealthy provider terminal leaves the ending obligation
owed. Their SUBJECT is unchanged and still asserted -- the terminal is not
accepted, the context use never becomes `ready`, no generation is written, the
provider is not called again. What changed is the stage half, which is exactly
what the owner ruled wrong. `assert_owed` is KEPT for the cases that genuinely
still owe an ending (a COMPLETED turn whose context finalization refuses); those
call sites are untouched and still pass. The new `assert_reported_and_held`
carries the corrected contract and explains itself.

**Successful-result coverage is preserved.** `tests.job_manager.test_review_driver`
164/164; `tests.manager.test_claude_context` 81/81; this dossier's 87 checks
include every earlier attribution, entrypoint, Job-scope and packet case
unchanged. `tests.tools.test_stage_execution` runs 424 with the SAME 12
pre-existing `SimpleNamespace has no attribute 'reconciles'` fixture errors
that predate this Work, in the port/integration fixtures rather than the ending
path; they are reported, not touched.

Verification: 87 focused deterministic checks, measured 17.608050957s, receipt
`verification-3.json` with `verification-3.log`. Product suites measured
separately: review_driver 5.414s, claude_context 37.901s, stage_execution
159.202s.

Cumulative measured for W239528, listing the runs rather than summarising:
7.146396201 + 7.149914038 + 7.138971223 (claim 239653) + 15.684039575 +
15.704004109 + 7.187 + 6.480 + 7.670 (claim 240196) + 17.608050957 + 15.699 +
5.414 + 37.901 + 159.202 + 38.245 + 38.117 + 2.118 (claim 242687) =
**388.464376103s**. Short diagnostic runs were not individually retained.

State: awaiting independent review.
"""

FINDING = """
### What the correction measures, and what it cost

Same retained bytes, same real adapter, ending driver, composed stage and
cleanup journal: before, `stopped overall-bound-exceeded` at tick 901 with the
stage in `answering` and no committed cleanup; after, `stopped exceptional` at
tick 3 with `retained`/`absent` cleanup, nothing outstanding, `state: held`, no
proposal and no false success.

There were TWO defects, and the second was only visible once the first was
fixed. The second is in `stage_execution`: a non-completed contextual turn
returned `outcome: "held"`, which is the REVIEW vocabulary for "nobody may be
scheduled on this", and the composed stage read it as "the ending did not
finish" and returned before settling its obligation. Holding the provider
CONTEXT USE is right and is kept -- a generation whose turn cannot be accounted
for must never be finalized -- but it is not the same fact as the stage ending
being unfinished, and one answer was serving both.

Nine accepted cases in `tests/manager/test_claude_context.py` asserted the old
stage half through `assert_owed`. Their subject -- an unhealthy provider
terminal is not accepted and its context use never becomes `ready` -- is
unchanged and still asserted. `assert_owed` is kept for the endings that are
genuinely still owed. `DIAGNOSIS-242687.md` records this as the change most
worth a reviewer's attention.

Verification: 87 focused deterministic checks, 17.608050957s measured, plus the
product suites: `test_review_driver` 164/164, `test_claude_context` 81/81, and
`test_stage_execution` 424 with the same 12 pre-existing fixture errors that
predate this Work.
"""


def sha(path):
    reading = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            reading.update(block)
    return reading.hexdigest()


def main():
    progress = HERE / "PROGRESS.md"
    if "claim 242687" not in progress.read_text(encoding="utf-8"):
        progress.write_text(
            progress.read_text(encoding="utf-8").rstrip("\n") + "\n" + PROGRESS,
            encoding="utf-8")
    finding = HERE / "FINDING.md"
    if "What the correction measures" not in finding.read_text(encoding="utf-8"):
        finding.write_text(
            finding.read_text(encoding="utf-8").rstrip("\n") + "\n" + FINDING,
            encoding="utf-8")

    moved = {one: {"before": was, "after": sha(ROOT / one)}
             for one, was in PRODUCT.items()}
    (HERE / "PRODUCT-CHANGE-242687.json").write_text(
        json.dumps({
            "schema": "baton.single-implementation-product-change/1",
            "work": "W239528", "claim": 242687, "participant": "baton.claude",
            "pinned_before_editing": "PLAN.md, by pin_242687.py",
            "paths": moved,
            "test_paths_changed": [
                "v12/python/tests/manager/test_claude_context.py"],
            "test_change_authority": (
                "AGENTS.md standing test-change authority, owner ruling "
                "2026-09-13. Recorded here as that ruling requires; not a "
                "second approval gate."),
            "expectations_changed": (
                "nine cases reached through `assert_owed` in "
                "`terminal_refuses` and "
                "`test_wrong_session_on_restore_cannot_finalize_or_repeat`. "
                "Their subject is unchanged; the stage-obligation half now "
                "asserts the corrected contract. `assert_owed` is kept for "
                "the endings that are genuinely still owed and those call "
                "sites are untouched."),
            "not_changed": [
                "v12/worker/claude_agent.py -- the adapter answered correctly",
                "integration.retain_proposal -- its refusal is right",
                "the provider-context hold -- kept exactly",
                "the provider-context-unproved branch -- untouched",
            ],
        }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(moved, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
