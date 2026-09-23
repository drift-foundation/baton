"""Complete the claim-242687 records: the test-path hash, PLAN and OWNERSHIP."""
import json
import pathlib

HERE = pathlib.Path(__file__).resolve().parent

PLAN_DONE = """
## Steps -- all done under this claim

1. Owner decision and product pin recorded BEFORE implementation
   (`pin_242687.py`). Done.
2. Live failure evidence preserved read-only in `live-242687/` and summarised
   in `DIAGNOSIS-242687.md`. Done.
3. Stall reproduced deterministically from the retained provider bytes through
   the real adapter and the real manager ending path, and the manager's own
   deferral row read. Done.
4. Product corrected in two places, with `test_failure_path.py` asserting each
   of the owner's four requirements separately and the earlier
   successful-result coverage preserved unchanged. Done.
5. `OPERATOR-FAILURE-242687.md` prepares the bounded expired-credential
   failure-path command. Done -- prepared, not run.
6. Independent review, then baton.decide. THIS HANDOFF.

## Product and test paths changed, with before/after digests

`PRODUCT-CHANGE-242687.json` carries them. Test-path changes are covered by
the standing test-change authority (AGENTS.md, owner ruling 2026-09-13) and are
recorded here as that ruling requires; they are not a second approval gate.

**The change most worth reviewing first** is the nine accepted cases in
`tests/manager/test_claude_context.py` whose stage-obligation assertion moved.
Their subject is unchanged and still asserted; `DIAGNOSIS-242687.md` says why,
and `assert_owed` is kept for the endings that genuinely still owe.

## Verification

87 focused deterministic checks, 17.608050957s, receipt `verification-3.json`.
Product suites: `test_review_driver` 164/164 (5.414s),
`test_claude_context` 81/81 (37.901s), `test_stage_execution` 424 with the
SAME 12 pre-existing `reconciles` fixture errors that predate this Work
(159.202s).
"""

OWNERSHIP = """
## Claim 242687 -- the first product change this Job has made

Files added:

    DIAGNOSIS-242687.md           the expired-credential diagnosis
    OPERATOR-FAILURE-242687.md    the bounded failure-path command
    PRODUCT-CHANGE-242687.json    before/after digests of every changed path
    live-242687/                  read-only copy of the live failure evidence
    test_failure_path.py          the retained-bytes regression
    pin_242687.py, records_242687.py, finish_242687.py
    verification-3.json/.log

PRODUCT paths edited, pinned in PLAN before the first edit:

    v12/python/src/baton_v12/job_manager/review_driver.py
    v12/python/tools/stage_execution.py
    v12/python/tests/manager/test_claude_context.py

Nothing else under `v12/` was touched. `v12/worker/claude_agent.py` is
deliberately unchanged: the adapter answered correctly.

`/home/sl/baton-runs/single-implementation-239528/run` was READ and not
modified, and no store belonging to it was opened. The W236087 dossier and its
ten preserved digests are unchanged; the reviewer's own files for both earlier
reviews are untouched.
"""


def main():
    change = HERE / "PRODUCT-CHANGE-242687.json"
    held = json.loads(change.read_text(encoding="utf-8"))
    held["paths"]["v12/python/tests/manager/test_claude_context.py"]["before"] = (
        "af586ae0e50276824dfdd4643ec826cd2cddef3cf4aa53a2d54111b07a154e98")
    change.write_text(json.dumps(held, indent=2, sort_keys=True) + "\n",
                      encoding="utf-8")

    plan = HERE / "PLAN.md"
    body = plan.read_text(encoding="utf-8")
    old = """## Steps

1. Record the owner decision and this pin. (done -- `pin_242687.py`)
2. Preserve and summarise the live failure evidence read-only.
   (`LIVE-RUN-242687.md`)
3. Reproduce the stall deterministically from the retained provider bytes
   through the real adapter and the real manager ending path.
4. Correct the product, with focused regressions at the product boundary AND
   in this dossier's baseline, preserving the successful-result coverage.
5. Prepare a bounded expired-credential failure-path command for the owner.
6. Independent review, then baton.decide.
"""
    assert body.count(old) == 1
    plan.write_text(body.replace(old, PLAN_DONE, 1), encoding="utf-8")

    owner = HERE / "OWNERSHIP-239528.md"
    if "Claim 242687" not in owner.read_text(encoding="utf-8"):
        owner.write_text(
            owner.read_text(encoding="utf-8").rstrip("\n") + "\n" + OWNERSHIP,
            encoding="utf-8")

    # The FINDING referred to a record that is named DIAGNOSIS-242687.md.
    finding = HERE / "FINDING.md"
    body = finding.read_text(encoding="utf-8")
    finding.write_text(body.replace("`LIVE-RUN-242687.md`",
                                    "`DIAGNOSIS-242687.md`"), encoding="utf-8")
    print("records completed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
