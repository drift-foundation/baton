"""Claim-255622: the boundaries the review named, measured rather than argued."""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent

PLAN = """# Current action — after claim 255622; RETURNED INCOMPLETE

Review 2026-09-24T09:29:06Z listed the coverage still owed on the abandonment
packet. This claim delivered it. **19 cases across the two focused fixtures,
all passing, clean under `-W error::ResourceWarning`.** No product file changed
this claim; the diff is still the two additions from claims 253397–255518.

## What the review asked for, and where it now is

**Actual alternate-path IDENTITY, not just the branch.** The spies stay, and
beside them the routed case now asserts that the roots `_mounted` RETURNED are
equal to `self.mounted(composed, "implementation", attempt_id)` — the roots the
stage composition's own preparation record says the container was started over.
"Recovering an ordinary pair for a different stage tree" is exactly what a
branch assertion would have passed over.

**Retained bytes, measured.** A sentinel file is written into the recorded
workspace root before the ending and read back after it. A cleanup that
reported `retained` over a tree it had emptied would have passed every other
assertion.

**The router's missing-capability case** — a worker whose operations predate
the capability refuses by name rather than raising an attribute error inside
routing.

**Positive credential and launch ROOT absence, asked of the filesystem.** Both
roots are proved present before the call and absent after it, and the
credential lifecycle record reads `None`. The fake custody report is not
evidence about either, which the review is right about and this does not rely
on.

**Discharge interruption / lost receipt.** The discharge is severed, the call
refuses, and the COMMITTED CLEANUP SURVIVES with no discharge receipt. The
retry then discharges — and the effect counts (removals, custody acts,
credential roots) are identical across it, so nothing destructive repeats.

**Adapter refusal** — an engine that raises settles nothing, journals nothing,
and a later retry over a working engine reaches the ordinary ending.

**A changed reason on a second declaration is refused**, with the effect counts
unchanged. The retention policy and the stage context are not operands a caller
can vary through this composition, and that is stated rather than tested around.

## The prior cancellation fence — MEASURED, and it carries a finding

After `cancel_attempt` the attempt sits at `execution_runtime: cancel-requested`,
`cleanup: pending`, runtime still attached, and NO cleanup record: that ending
travels the reconciliation path. The abandonment's own fence then meets the
authority's rule and refuses — nothing is settled, nothing is journalled, no
effect repeats.

**It refuses as `baton_v12.authority.errors.Refusal`, not as a typed
`ContractRefusal`.** The case records that rather than papering over it.
Whether an operator-facing composition should translate that refusal is a
ruling for the owner or reviewer; changing it quietly here would be deciding it
myself.

## Not re-run, as directed

The 424-case suite was NOT repeated; the 12 baseline errors are already
identified and compared against the pinned snapshot.
`tests.tools.test_single_worker` — 162 tests, OK, 10.041s — was re-run because
these fixtures subclass it.

## REMAINING

  1. the supervisor's explicit shutdown declaration for its own failed or
     stopped attempts;
  2. the two operator grants documents with pure and fake-boundary validation
     and readback;
  3. the executed-image fault diagnosis;
  4. a new digest-bound manager snapshot, then exact recovery and fresh-run
     commands;
  5. the ruling above on translating the authority refusal.

## Standing constraints

The deployed snapshot is immutable and was read only. The failed instance stays
preserved and read-only. No live rerun, deployed-store mutation, container
deletion or cleanup execution.

## Ownership

baton.claude owns this dossier and, from claim 253397,
`v12/python/tools/single_worker.py` and `v12/python/tools/stage_execution.py`.
"""

PROGRESS = """
## 2026-09-24 — baton.claude, claim 255622

### The list, done

Identity rather than branch: the routed case now compares the roots `_mounted`
returned against the stage composition's own preparation record, so recovering
an ordinary pair for a different stage tree fails instead of passing. Retained
bytes are a sentinel written before and read after. The router's
missing-capability boundary has a case. The credential and launch roots are
proved present before and absent after — asked of the filesystem, because you
are right that a fake custody report is not that proof.

The discharge interruption was the most useful one to write: sever the
discharge, and the committed cleanup survives with no receipt; the retry
discharges and the effect counts are identical across it. That is the crash
boundary the fresh-composition case was not.

### The prior fence taught me something I would have got wrong by reasoning

I expected either a clean refusal or a completed second ending. What actually
happens is that `cancel_attempt` leaves `cancel-requested`, `cleanup: pending`,
the runtime still attached and NO cleanup record — that ending travels
reconciliation — and the abandonment's fence then meets "assignment generation
was fenced and ended". Nothing settles, nothing journals, no effect repeats.

But it surfaces as `authority.errors.Refusal` rather than a typed
`ContractRefusal`. I have recorded that in the case instead of translating it.
Whether an operator-facing composition owes the translation is a ruling, and
quietly making one would be the kind of thing this Work has corrected me for
before.

### Verification spending

Both fixtures together — 19 cases, all passing, **1.090s**, clean under
`-W error::ResourceWarning`. `test_abandonment` alone at 11 and 13 cases:
0.632s, 0.701s. `test_routed_abandonment` alone at 6 cases: 0.371s. One probe
(`probe_fence_255622.py`) ran in a few seconds and was not timed.
`tests.tools.test_single_worker` — 162 tests, OK, **10.041s**.

The 424-case suite was NOT repeated, as directed; its 159.910s, the additional
untimed full run, the 0.966s and 1.170s probes all stand. Named suite subtotal
unchanged at **1047.869180986s** (`verification-27.json`). Earlier focused runs
(0.269s, 0.312s, 0.352s, 0.364s, 0.388s, 0.428s, 0.439s, 0.747s, and the routed
0.163/0.193/0.201/0.292/0.335/0.366/0.366s), the earlier product-suite times
(9.955s, 10.041s, 335.453s, 172.937s, 10.135s, 10.116s, 10.100s), the untimed
diagnostic reads, the unmeasured ~120s command-timeout run and the earlier
unknowns all stand.

State: returned INCOMPLETE through baton.bug, with the abandonment packet's
coverage complete and four non-abandonment items outstanding.
"""


def main():
    (HERE / "PLAN.md").write_text(PLAN, encoding="utf-8")
    progress = HERE / "PROGRESS.md"
    body = progress.read_text(encoding="utf-8")
    if "claim 255622" not in body:
        progress.write_text(body.rstrip("\n") + "\n" + PROGRESS,
                            encoding="utf-8")
    print("records written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
