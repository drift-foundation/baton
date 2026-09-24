"""Claim-255929: a claim of mine measured, found wrong, and corrected."""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent

PLAN = """# Current action — after claim 255929; RETURNED INCOMPLETE

Review 2026-09-24T10:17:23Z accepted the prior-fence correction and asked for
the six remaining items. This claim closed the second one — by measuring it and
finding that what I had told you about it was wrong.

## The unpooled / bypassed context gap, MEASURED

`probe_pooled_kind_255929.py` calls the POOLED worker's own `_Operations`
directly, bypassing the router's binding, with `kind`, `stage_id` and `episode`
altered. All three are ACCEPTED.

**And that is harmless, which is not what I told you.** Under claim 255665 I
reported that `kind` "decides MOUNTS", so a review kind over an implementation
attempt would recover the frozen checkpoint where the private line belongs.
It does not:

  * `StageComposition._prepare` branches on its OWN `self.role` — the worker's
    composition — and never on the caller's `stage["kind"]`;
  * `_recovered` reads the attempt's DURABLE grant by attempt id, so a
    restarted manager repopulates from evidence rather than from operands;
  * the caller's `job_id` reaches `deployment.line_for` only on a FIRST
    preparation, which an attempt with a started runtime no longer has — and
    a wrong `job_id` is refused by adoption anyway.

`test_routed_abandonment.py::test_an_altered_context_at_the_worker_cannot_divert_the_tree`
pins that directly: the roots recovered under an altered kind, stage_id and
episode are equal to the roots the container was started over, and the ending
settles `retained` over that same tree.

**The router binding stays, with its rationale corrected in the file.** It is
operand hygiene — a context disagreeing with the record is refused before any
worker is reached, which is where a wrong operand should stop. It is not what
keeps the tree correct, and the comment no longer claims to be. A false
rationale in a product comment is worse than no comment.

## What this changes about the supervisor item

The abandonment now recovers a cancelled receiptless attempt, so the
supervisor's explicit shutdown declaration has somewhere to go: after
`_cancel_active` and the bounded cleanup sweeps, each still-outstanding attempt
can be DECLARED abandoned, which settles its cleanup and discharges its gate.
`TwoJobGate` already records a per-attempt stage id at `launch`, so the
document that declaration needs is one recording change away. That is the next
item and it is not started.

## REMAINING — five items, and they are multi-turn work

  1. first-call crash and launch-absent alternate recovery;
  2. the supervisor's explicit shutdown declaration (shape established above,
     not implemented);
  3. the two operator grants documents with validation and readback;
  4. the executed-image fault diagnosis;
  5. a new digest-bound manager snapshot, then exact recovery and fresh-run
     commands.

**No external blocker.** These are unstarted or partly-started work, not
something waiting on anybody. I am reporting the honest state rather than
claiming a packet I have not built.

## Standing constraints

No deployed mutation, live rerun or cleanup execution. The preserved instance
and the pinned snapshot are read-only. Recovery of the preserved run is
PREPARED, not performed.

## Ownership

`OWNERSHIP-255823.md`: `tools/single_worker.py`, `tools/stage_execution.py`,
`src/baton_v12/worker_manager/intake.py`. `attempts.py`, `deadlines.py` and
`authority/` are untouched.
"""

PROGRESS = """
## 2026-09-24 — baton.claude, claim 255929

### I measured my own claim and it was wrong

Two claims ago I told you an altered `kind` was a live hazard because it
"decides MOUNTS". I reasoned that from the shape of the mount code instead of
running it. Running it says otherwise: `StageComposition._prepare` branches on
its own `self.role`, `_recovered` reads the attempt's durable grant by attempt
id, and the caller's `job_id` only matters on a first preparation an already
started attempt does not have.

So a caller holding the worker's own operations — bypassing the router's
binding entirely — still cannot divert the tree, and there is now a case
asserting exactly that: altered kind, stage_id and episode, roots equal to the
recorded ones, ending settled over the same tree.

The binding I added to the router is still worth having as operand hygiene, and
it stays. What does not stay is the rationale I wrote into the product comment
beside it, which claimed the thing I have just disproved. That is corrected in
the file. A false explanation in a comment outlives the claim that produced it.

### What it unblocks

With a cancelled receiptless attempt now recoverable, the supervisor's shutdown
declaration has somewhere to go: after the cancellation and the bounded cleanup
sweeps, each outstanding attempt can be declared abandoned and settle.
`TwoJobGate` already records a per-attempt stage id at launch, so the document
is one recording change away. Not started this claim, and I am not going to
describe it as though it were.

### Verification spending

`test_abandonment` + `test_routed_abandonment` — 29 cases, all passing,
**1.805s**, clean under `-W error::ResourceWarning`; 1.760s earlier this claim.
`tests.tools.test_stage_execution.TheDeploymentRoutesACancellationToItsOwner` —
3 tests, OK, **0.094s**. One probe (`probe_pooled_kind_255929.py`) ran in a few
seconds and was not timed.

The 424-case stage-execution suite was NOT repeated. Everything prior stands:
899 tests OK 19.828s, 9.308s, 10.337s, 159.910s plus its untimed repeat,
0.966s, 1.170s, 10.041s, 9.966s, 0.348s, 0.130s, the combined
1.090/1.334/1.536/1.677s, the focused runs listed in earlier entries, the
untimed probes and diagnostic reads, the unmeasured ~120s command-timeout run
and the earlier unknowns, alongside named **1047.869180986s**. The reviewer's
1.157s/1.186783992s and 1.064s/1.092317897s measurements are additional.

State: returned INCOMPLETE through baton.bug with one item closed by
measurement, one claim of mine retracted, and five items open.
"""


def main():
    (HERE / "PLAN.md").write_text(PLAN, encoding="utf-8")
    progress = HERE / "PROGRESS.md"
    body = progress.read_text(encoding="utf-8")
    if "claim 255929" not in body:
        progress.write_text(body.rstrip("\n") + "\n" + PROGRESS,
                            encoding="utf-8")
    print("records written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
