"""Record the owner decision and PIN the product path, BEFORE implementation.

Owner pass 242683: "Record this decision in FINDING/PLAN before implementation."
This script is that record. It is run first and nothing under `v12/` is edited
until it has been.
"""
import hashlib
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[4]

PINNED = ("v12/python/src/baton_v12/job_manager/review_driver.py",
          "v12/python/tests/job_manager/test_review_driver.py")

FINDING = """
## 2026-09-22 -- OWNER: failure handling before credential renewal

Owner pass 242683, recorded here BEFORE implementation as that pass requires.

The owner ran the accepted bounded command on the fresh isolated instance. The
provider returned an OAuth authentication failure immediately. **The owner
selects failure handling before credential renewal, and the credentials are
left expired on purpose**: a deployment that only works when the token is valid
has not been shown to fail safely, and renewing first would have thrown away
the one set of real failure bytes this campaign has.

    "Owner selects failure handling before credential renewal. Leave
     credentials expired. Record this decision in FINDING/PLAN before
     implementation. Preserve /home/sl/baton-runs/single-implementation-239528/
     run, including outcome.json, provider logs and worker terminal events.
     Diagnose and correct unable-result settlement and cleanup. Use retained
     failure bytes in deterministic regressions through real manager/adapter
     boundaries. Require prompt actionable failure, stopped execution and
     positive cleanup, without a proposal or false success. Preserve
     successful-result coverage and prior evidence. Pass for independent
     review, then baton.decide with a bounded expired-credential failure-path
     command. No credential renewal, live rerun, destructive recovery,
     reviewer stage or resume in this correction."

The live run directory is preserved and was read only. Its evidence is
summarised in `LIVE-RUN-242687.md`; nothing in it was modified, moved or
deleted, and no store belonging to it was opened.

### What the run showed

The provider failed in 31 ms -- `is_error: true`, `terminal_reason: api_error`,
`"Failed to authenticate: OAuth session expired and could not be refreshed"` --
and the adapter did exactly the right thing: it answered `ending: answered`,
`disposition: unable`, `fault_code: null`, with a real result manifest and no
proposal claim.

**The manager then sat in `answering` for the full 900-second bound and never
committed cleanup.** That is the defect, and it is a product defect rather than
a packet one: a deployment whose credentials expire takes fifteen minutes to
report a thirty-one-millisecond failure, and leaves the container behind.

### The cause, established

`review_driver.end_implementation` performs publication as an UNCONDITIONAL
step seven of nine. `integration.retain_proposal` refuses -- correctly, at its
own boundary -- when the frozen result's disposition is not `completed`:

    attempt '...' has no completed frozen result to propose

So steps one to six commit (quiesce, observe, freeze, correlate, intake
receipt, retention), step seven refuses durably, and steps eight and nine --
fencing the assignment and `authorize_cleanup` -- are never reached.
`_ending_owed` stays true, the stage projects `answering`, and every sweep
re-attempts `conclude` and records the same refusal until the bound elapses.
The manager's own deferral row names it exactly.

**This is not W236087's cleanup stall.** That one never reached
`authorize_cleanup` because a faulted turn froze and collected nothing, so no
intake receipt existed. Here the receipt DOES exist and every step up to
retention committed; the ending is blocked one step further on, at a
publication that cannot exist for a result with no candidate.

### The correction, and where it belongs

Publication is conditional on the result being `completed`. An `unable` or
`cancelled` implementation result has no candidate, so there is nothing to
retain, nothing to publish and nothing to read back on resume -- while the
assignment still has to be fenced and the runtime still has to be positively
cleaned up.

`review_driver` already states this rule for its own other ending: "The
`completed` disposition stays HERE because it is the review's own rule -- a
review that did not complete decided nothing -- rather than something every
ending owes." The implementation ending owes the same statement and did not
make it. The correction is that statement, applied consistently to the ordinary
ending and to both resume entries.
"""

PLAN = """# Current action -- the expired-credential failure path

## Active -- claim 242687, baton.claude

Owner pass 242683. The accepted command RAN on the fresh isolated instance and
exposed a product defect: an `unable` implementation result never settles and
never cleans up. Diagnosis and correction are this claim's scope. Credentials
stay expired by owner decision; no renewal, no live rerun, no destructive
recovery, no reviewer stage, no resume.

`/home/sl/baton-runs/single-implementation-239528/run` is preserved and was
read only.

## PINNED PRODUCT OWNERSHIP -- pinned BEFORE the first edit

Recording it here is the pin. Pre-edit digests, taken under this claim:

%s

The change: `review_driver.end_implementation` performs publication as an
unconditional step seven, and `integration.retain_proposal` refuses a result
whose disposition is not `completed`. Publication becomes conditional on the
disposition in the ordinary ending and in both resume entries, so that steps
eight and nine -- fencing the assignment and `authorize_cleanup` -- are reached
for a result that produced no candidate. `published` is `null` for such an
ending, which is the honest answer and is not a false success.

Test paths are covered by the standing test-change authority (AGENTS.md, owner
ruling 2026-09-13); they are recorded here as that ruling requires and are not
a second approval gate.

## Steps

1. Record the owner decision and this pin. (done -- `pin_242687.py`)
2. Preserve and summarise the live failure evidence read-only.
   (`LIVE-RUN-242687.md`)
3. Reproduce the stall deterministically from the retained provider bytes
   through the real adapter and the real manager ending path.
4. Correct the product, with focused regressions at the product boundary AND
   in this dossier's baseline, preserving the successful-result coverage.
5. Prepare a bounded expired-credential failure-path command for the owner.
6. Independent review, then baton.decide.

## Not in scope, and not done

Credential renewal. Any live rerun. Any destructive recovery. Any cleanup of
W236087's outstanding runtime. Any reviewer stage or session resume. Any Work
closure.

---

"""


def sha(path):
    reading = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            reading.update(block)
    return reading.hexdigest()


def main():
    pins = "\n".join(f"    {one}\n        {sha(ROOT / one)}"
                     for one in PINNED)
    finding = HERE / "FINDING.md"
    if "OWNER: failure handling before credential renewal" not in \
            finding.read_text(encoding="utf-8"):
        finding.write_text(
            finding.read_text(encoding="utf-8").rstrip("\n") + "\n" + FINDING,
            encoding="utf-8")
    plan = HERE / "PLAN.md"
    body = plan.read_text(encoding="utf-8")
    if "claim 242687" not in body:
        head = body.split("\n", 1)[0]
        plan.write_text(
            (PLAN % pins) + body.replace(head, "# Historical action" + (
                head.split("action", 1)[-1] if "action" in head
                else " -- " + head.lstrip("# ")), 1),
            encoding="utf-8")
    print(pins)
    print("recorded")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
