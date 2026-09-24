"""Claim-249586: R3 complete; R4's admission boundary done, its run not."""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent

PLAN = """# Current action — after claim 249586

**R3 is COMPLETE. R4 is started: its admission boundary is done and driven;
its bounded run, stop, cleanup and outcome are not.**

## Done under claim 249586

  * **R3 — both Jobs' FROZEN ATTRIBUTED verdicts.** Both review turns are
    driven to completion and each verdict is read back through
    `review_driver.review_verdict_from_result` — the manager's own deriver,
    which refuses unless the frozen result belongs to that attachment's
    attempt, its retained manifest names the same result and assignment at the
    same generation, and the base, head and tree match the checkpoint's own
    evidence. Two distinct attachments, two distinct results, each reviewer
    the one configured for its Job, and both lines `accepted` with no
    correction round opened.
  * **R4 (first part) — `two_job_supervisor.TwoJobGate`.** W239528's accepted
    `AdmissionGate`, bound by digest, with the ONE rule a two-Job run needs
    changed: `_ours` serves two Job identities instead of one. Four
    admissions are taken ON THE GATE and a fifth of either kind is refused; a
    stopped gate admits nothing further; a stage of neither Job is recorded as
    FOREIGN rather than as a cap refusal, and reaches the wrapped operations
    not at all.

35 focused checks, 0 failures, measured 6.941682081000181s,
`verification-5.json`; 9 are new.

## R4's remainder, exactly

The bounded serving loop over four admissions, its stop, cancellation of every
admitted attempt through the composition's own port, positive cleanup for all
four, the inclusive deadline arithmetic and the published outcome — plus the
affected failure and interruption checks. `baseline.supervise` is written for
ONE workload's packet; what remains is the two-Job equivalent over this gate.

## Ownership

Reviewer-owned and immutable: ASSESSMENT-249338.md, every `review-*.md` and
`review-*.json`/`.log`. baton.claude owns two_jobs.py, two_job_supervisor.py,
test_two_jobs.py, ADOPTION-247941.md, CONTINUITY-247941.md,
SELECTIONS-247941.json, verify_247941.py, the `align_template.py`,
`add_roundtrip.py`, `apply_*.py` edit records, verification-*.json/.log,
PROGRESS.md, records_*.py and PLAN.md.
"""

PROGRESS = """
## 2026-09-23 — baton.claude, claim 249586

No new findings this round; the instruction was to start R3 and R4 and I did.

### R3 — two frozen attributed verdicts, derived rather than counted

Both review turns are driven to completion and each verdict is read back the
way the manager itself reads one: `review_verdict_from_result`, which refuses
unless the frozen result belongs to that attachment's attempt, its retained
manifest names the same result and the same assignment AT THE SAME GENERATION,
and the base, head and tree the reviewer reports are the checkpoint's own.

Two things the product corrected on the way. `review_for_attempt` takes the
generation as a required keyword, because an attempt may be offered more than
once and an attachment belongs to one of those assignments; the generation
comes from the preparation record the worker that prepared the attempt holds,
which is the same fact `preparing` uses. And `line_status` needs a
storage-usage operand a witness has no business supplying, so the line's state
is read through `line_of`.

Two distinct attachments, two distinct results, each reviewer the one
configured for its own Job, both lines `accepted`, no correction round.

### R4 — the admission boundary, and one case I had to rewrite

`TwoJobGate` is W239528's accepted `AdmissionGate` with exactly one rule
changed: `_ours` serves two Job identities rather than one. Everything else --
the caps, counting after the act commits, recording every launched runtime,
refusing all three admitting acts once stopped -- is inherited, and the
baseline is bound by digest so a change underneath is a refusal rather than a
passing run.

**The first version of the admission case was not honest.** It ran the fixture
traversal, which goes through the COMPOSED operations rather than through this
gate, then SET `gate.admissions` by hand before asserting the fifth was
refused. That asserts an assignment. The four admitting acts are now taken on
the gate, over a recorder, and the recorder shows exactly which four
(job, kind) pairs reached it -- because handing the gate synthetic stages and
the real deployment reaches operands a real stage carries and proves nothing
about the rule.

### What R4 still needs

The bounded serving loop, its stop, cancellation through the composition's own
port, positive cleanup for all four admitted attempts, the inclusive deadline
arithmetic and the published outcome, with the affected failure and
interruption checks. `baseline.supervise` is written for one workload's packet.

### Verification spending

35 focused deterministic checks, 0 failures, measured 6.941682081000181s,
receipt `verification-5.json` with `verification-5.log`; 9 are new.

Cumulative MEASURED for W247941, every retained invocation preserved:
1.678180975 + 2.122556141 + 2.145897528 + 2.868183810 + 2.876618006 +
3.646601886 + 3.682941216 + 6.941682081 = **25.962661643s**. Pin checks are
separate and were not measured. The reviewers' own runs stay in their evidence.

State: returned for independent review of R3 and R4's admission boundary, with
R4's bounded run named as the remaining scope.
"""


def main():
    (HERE / "PLAN.md").write_text(PLAN, encoding="utf-8")
    progress = HERE / "PROGRESS.md"
    body = progress.read_text(encoding="utf-8")
    if "claim 249586" not in body:
        progress.write_text(body.rstrip("\n") + "\n" + PROGRESS,
                            encoding="utf-8")
    print("records written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
