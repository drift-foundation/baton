"""Claim-247423 dossier entries: the selected product change; R3b open."""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent

FINDING = """
## 2026-09-23 -- the no-correction boundary, implemented

Owner reroute 247421 selected "the smallest supported product change needed
for review-only completion without opening a correction round; preserve
existing correction behavior for other Jobs". The decision and the exact file
ownership are recorded in `OWNER-PRODUCT-CHANGE-247423.md`, written BEFORE any
product byte was edited, as that reroute requires.

THE CHANGE IS ONE OPTIONAL MEMBER AND ONE CONDITION.
`correction_policy: "open" | "decline"` on the stage-execution deployment,
absent meaning `"open"`. `held_configuration` owns the value where every other
member is owned; `StageDeployment` carries it; and `routed` declines to reach
`review_driver.open_correction` when it says `decline`, recording
`correction_declined` instead. Every existing deployment document carries no
such member and is unchanged -- the preservation half is a DEFAULT rather than
a migration.

WHY IT FAILS CLOSED RATHER THAN REPORTING. Review 2026-09-23T11:56:42Z R4:
"returning held does not undo that store effect". Claim 247318 detected the
round after the act; this declines before it. What is declined is the ROUND,
never the verdict: a reviewer remains free to answer any of the three
dispositions and nothing in this path reads or prefers one.

AND THE PACKET IS NOT RUNNABLE WITHOUT IT. `review_supervisor.held_packet`
reads the deployment document and refuses a packet whose `correction_policy`
is not `decline`, so the boundary is a precondition of running rather than a
promise in prose.

THE CHANGE HAD A DEFECT AND THE PRODUCT SUITE FOUND IT. The first version read
`self.deployment.correction_policy` inside `routed` -- and `routed` IS the
deployment's own method, so 38 product cases answered `AttributeError`. The
suite now runs 424 with 12 errors, and those 12 are the pre-existing
`Integration._run` fixture errors recorded before this Work: each fails inside
that function's producer-proposal read and none names `correction_policy` or
`routed`. `PRODUCT-CHANGE-247423.json` records the before and after digests and
that accounting.

## 2026-09-23 -- an interrupt during the first owner act lost the outcome

Review 2026-09-23T11:56:42Z R3a. The submission publishing region added under
claim 247318 caught `Exception` only. The installed termination handler raises
`KeyboardInterrupt`, which is not an `Exception`, so an interrupt arriving
during `submit` or the turn-ceiling read escaped through `supervise`'s
`finally` -- which only restores handlers -- leaving a COMMITTED stage with no
outcome on disk.

An owner act is exactly where this matters most: it is the first moment the run
has changed anything. The guard now catches `BaseException`, records the
interruption, skips serving, and re-raises `SupervisorInterrupted` at the end
by the same path every other interruption takes -- after the accounting and
after the publication. The regression wraps the real public `submit`, lets it
COMMIT, and then injects the interrupt, which is how the reviewer reproduced
it.
"""

PLAN = """# Current action -- one piece of executable evidence remains

1. DONE. W239528's proposal and cleanup are independently accepted.
2. DONE, accepted 2026-09-23T04:50:12Z. The attachment arrangement.
3. DONE, accepted 2026-09-23T05:08:49Z. The two P2 fixture corrections.
4. DONE, accepted 2026-09-23T11:56:42Z. R1 startup identity and documented
   clock; R2 public verdict and attachment contracts.
5. DONE under claim 247423. R3a: interruption from the first owner act through
   final publication, with the regression driving a committed submission.
6. DONE under claim 247423. R4: the owner-selected product change --
   `correction_policy` on the stage-execution deployment, declining the round
   BEFORE the act, with existing behaviour preserved by default. The packet is
   refused unless the deployment carries it.
7. OUTSTANDING -- R3b. The actual supervisor admitting and ending ONE reviewer
   through a deterministic provider with real coordination: frozen result,
   verdict attribution, cancellation and cleanup with an accountable attempt.
   The current supervision fixture defers every admission, and the reviewer is
   right that this proves the calls reaching a composition that refuses them
   rather than an admitted attempt.
8. Then the packet is runnable only after 7 and the product change are
   independently accepted. No live run is selected.

## Not in scope

No deployed-store access, live execution, provider, container, recovery,
implementation rerun or resume. No closure of W239533 or W236087.
"""

PROGRESS_ENTRY = """
## 2026-09-23 -- baton.claude, claim 247423

Owner reroute 247421, addressing review 2026-09-23T11:56:42Z. Read canonical
state, the complete work-events, thread T239533 in full (2 messages, no
pagination remaining), the review, and this dossier. **R3a and R4 are done.
R3b is not, and it is the single remaining item.**

**No deployed store was opened.** One product file was edited under the
owner's explicit selection, recorded before the edit.

### R4 -- the owner-selected product change

`OWNER-PRODUCT-CHANGE-247423.md` records the decision, the reasoning, the
exact file and its before-digest, written BEFORE the first edit as reroute
247421 requires. `PRODUCT-CHANGE-247423.json` records the after-digest and the
product-suite accounting.

`v12/python/tools/stage_execution.py` gains an optional `correction_policy`
deployment member. Absent or `open` is byte-for-byte today's behaviour, so
every existing deployment is preserved by DEFAULT rather than by a migration.
`decline` makes `routed` not reach `open_correction` and record
`correction_declined`. `review_bindings` sets it; `held_packet` refuses a
packet without it, so the packet is non-runnable until the boundary is
configured -- which is what reroute 247421 asked for.

The change had a real defect and the product suite found it: the first version
read `self.deployment.correction_policy` inside `routed`, and `routed` IS the
deployment's own method, so 38 cases answered `AttributeError`. Fixed. The
suite runs 424 with 12 errors, and those 12 are the pre-existing
`Integration._run` fixture errors that predate this Work -- each fails inside
that function's producer-proposal read and none names `correction_policy` or
`routed`.

Four new cases drive the REAL `StageDeployment.routed` with `open_correction`
WATCHED rather than stubbed away, because the question is whether it is
reached: declining never reaches it, absent and `open` both do, a
non-correction verdict is returned as it arrived under either policy, and the
supervisor's mirrored constant is held equal to the product's own.

### R3a -- the interrupt that lost the outcome

The guard caught `Exception`; the handler raises `KeyboardInterrupt`. Now
`BaseException`, recorded, serving skipped, and re-raised after the accounting
and the publication. The regression wraps the real public `submit`, lets it
COMMIT, then injects the interrupt -- and asserts the committed submission,
the published outcome and that the final canonical read still ran.

### R3b -- not delivered, and the reviewer's objection is correct

`Serving` defers every admission, so `test_exactly_one_review_is_admitted...`
measured calls reaching a composition that refuses them. I renamed and
re-scoped that case last claim, which made it honest but did not make it the
proof. What remains unexercised is exactly what the reviewer listed: an
admitted attempt, cancellation of one, cleanup uncertainty and interruption
with an outstanding attempt, a completed review, and real frozen-result
collection.

The reviewer is also right that my "a real frozen output needs a live
provider" claim was not established: `ManagedSessionResume` and W239528's
`test_baseline` already drive deterministic providers over real coordination.
The remaining work is to extend that fixture to admit and end the separate
review while preserving producer/reviewer identities and the frozen checkpoint
provenance, with the simulated provider labelled. I did not reach it this
claim, and the packet stays non-runnable until it and the product change are
independently accepted.

Verification: 86 focused deterministic checks, 0 failures, measured
1.3391616380104097s, receipt `verification-6.json` with `verification-6.log`;
7 are new. Separately, the product suite `tests.tools.test_stage_execution`:
424 tests, 12 pre-existing errors, measured 159.751s.

Cumulative measured for W239533: 0.432753846 + 0.590057723 + 0.588589542 +
1.167917072 + 1.325346095 + 1.339161638 + 159.751 = **165.194825916s**. The
reviewers' independent measurements (0.571337769s, 0.596305013s,
1.152729417s, 1.311204790s) are theirs and are preserved separately.

State: returned for independent review with R3b outstanding.
"""

OWNERSHIP = """
## Claim 247423 -- the selected product change, and R3a

Added: `OWNER-PRODUCT-CHANGE-247423.md`, `PRODUCT-CHANGE-247423.json`,
`records_247423.py`, `verification-6.json/.log`.

Edited in this dossier: `review_supervisor.py`, `review_bindings.py`,
`test_review_supervisor.py`, `verify.py`, `FINDING.md`, `PLAN.md`,
`PROGRESS.md`, this file.

PRODUCT PATH EDITED, under owner selection 247421 and pinned before the edit:

    v12/python/tools/stage_execution.py
        before ebc9be29d2bd23cf129afe33943f5336832df2ef24256c724708004220032896
        after  318e9a4bdf111cb3b93bddbe63c6d6fe6911702023db7196c507fbae54d18d11

**Nothing else under `v12/` was edited**, and no product test was weakened:
`tests/tools/test_stage_execution.py` is unmodified. The four new cases for
the boundary live in this dossier and drive the real product function.

`review_driver.open_correction` is untouched -- the decision to call it moved,
the act did not. W239528's `baseline.py` is unchanged at its accepted digest,
both images are unchanged, no deployed store was opened, the disclosed
`control.sqlite3-shm` and zero-length `control.sqlite3-wal` beside W239528's
retained control store are preserved, and every reviewer file in this dossier
is append-only history that was not modified.
"""


def main():
    finding = HERE / "FINDING.md"
    body = finding.read_text(encoding="utf-8")
    if "the no-correction boundary, implemented" not in body:
        finding.write_text(body.rstrip("\n") + "\n" + FINDING, encoding="utf-8")
    (HERE / "PLAN.md").write_text(PLAN, encoding="utf-8")
    progress = HERE / "PROGRESS.md"
    body = progress.read_text(encoding="utf-8")
    if "claim 247423" not in body:
        progress.write_text(body.rstrip("\n") + "\n" + PROGRESS_ENTRY,
                            encoding="utf-8")
    owner = HERE / "OWNERSHIP-239533.md"
    body = owner.read_text(encoding="utf-8")
    if "Claim 247423" not in body:
        owner.write_text(body.rstrip("\n") + "\n" + OWNERSHIP, encoding="utf-8")
    print("records written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
