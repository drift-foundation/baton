"""Claim-243174 dossier entries."""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent

PROGRESS = """
## 2026-09-23 -- baton.claude, claim 243174, the successful-baseline stall

Owner pass 243171, after a run in which the real provider DID follow the
edit-only contract. Findings were recorded in FINDING and the path pinned
BEFORE implementation, as that pass requires (`pin_243174.py`).

`/home/sl/baton-runs/single-implementation-success-239528/run` is preserved and
was read only; no store belonging to it was opened. Evidence copied to
`live-success-243174/`. **No file under `v12/` was edited under this claim**;
the three product paths accepted under claim 242687 still carry their accepted
after-hashes.

**The result that matters.** The provider completed in 18.3s over five turns
and reported: "The change is left uncommitted in the working tree (`git status`
shows ` M harness.py`); nothing else was touched." Verification printed
`READY`. The retained outcome carries one proposal authored AND committed by
`Baton worker <worker@baton.invalid>` with exactly the declared base as its
single parent, a destroyed runtime and `retained`/`absent` cleanup. That is the
first half of `PROVIDER-QUESTION-239528.md` answered.

**Finding 1, the custody failure, established rather than guessed.**
`context_delivery._private` refuses any custody directory carrying group or
other bits. Running the product's own `_state` measurement over the preserved
context home, with `{conversation_id}` resolved, reproduces the refusal
exactly: `protected custody owner or mode changed`. Seven directories the real
CLI created carry `0o755` -- `.claude/backups`, `projects`, `session-env`,
`session-env/<conversation>`, `shell-snapshots`, `projects/-output` and
`projects/-output/memory`. The state file and credential symlink are exactly as
the profile requires; it is the directories on the way to them.

Why no test caught it: the fixture's fake provider chmods its two state parents
to `0o700` -- it has always compensated for precisely this -- and the real CLI
creates four more directories besides those two. **Diagnosed, not fixed**:
whether the manager should tolerate a umask-created directory or the delivery
should impose the mode is a product decision with its own security reasoning,
and it is recorded as the next selection.

**Finding 2, corrected.** Once the context use is held, the composed stage
returns `provider-context-unproved` and never settles, so the stage projects
`answering` forever -- the same conflation corrected under claim 242687 for
`unable`, one branch over, now reaching a COMPLETED turn whose proposal was
produced, published and cleaned up. Nothing could change after that point and
the supervisor swept for 443 of 900 seconds.

`baseline.py` now stops when it stops moving. `STALLED_TICKS = 6` consecutive
identical observations of `(stage states, accountable attempts, each attempt's
cleanup axis)`, and every condition must hold throughout: the stages
non-terminal, at least one accountable attempt, and NO outstanding cleanup. Six
is argued rather than picked -- `serve` ticks at one second, so it is six
seconds of a run doing nothing, long enough that an ending mid-flight across
several journalled operations is not mistaken for a stall. An unreadable
progress read RESETS the counter rather than advancing it: failing towards
keeping the run alive is the only direction that cannot invent a stall. The
outcome reports `stalled_ticks`, `stalled_after`, and a held reason in its own
words. A shorter bound would have made the same non-answer arrive sooner; the
bound stays the backstop and this is the mechanism.

**Finding 3, corrected, and the owner's question answered from the file.**
`outcome.json` WAS retained -- 4127 bytes at 18:34 for a run that began at
18:26, complete and internally consistent. This is read from the file, not
inferred from the exception. What was missing is that `main` never caught
`SupervisorInterrupted`, so the operator got a traceback and the one thing they
needed -- where the outcome is -- was the one thing not printed. `main` now
prints the interruption, the retained outcome's path, its state and stop
reason, and the document, and exits 130. A held ending names its outcome path
too.

**And the builder finding from review 2026-09-23T00:06:24Z.**
`snapshot_242687.py` deleted its destination before copying, so a rerun would
have destroyed the snapshot independent review had just verified and bound --
a reviewer had to tell an operator not to run it. A builder whose safety
depends on nobody running it twice is not safe. It now REFUSES an existing
destination, offers `--verify` to re-check one and `--rebuild-into <path>` to
make another, and never removes a tree. `--verify` confirms the bound snapshot:
106 files, accepted bytes present, preserved snapshot unmoved.

**Reproduced through actual composition.** `test_no_progress.py` stops the
fixture compensating: it leaves the context home as a real CLI leaves it, AFTER
the turn -- which is the live ordering, since the adapter published its receipt
over those modes without complaint and it was the manager that refused later.
The real `finalize_context_use` then refuses for the real reason. Context
integrity is asserted (the use is held and never `ready`), and so is
no-false-success (the run is `held` and the proposal it really produced is
still reported). Three cases guard the other direction: an ordinary successful
run still settles with `stalled_ticks: 0`, an unreadable progress read never
invents a stall, and an outstanding cleanup is never called stalled.

Verification: 112 focused deterministic checks, measured 24.356673542s, receipt
`verification-5.json` with `verification-5.log`. The 100 earlier checks are
unchanged and included; 12 are new.

Cumulative measured for W239528: 409.162404334s (through claim 242906) +
24.356673542 + 8.536 + 5.164 + 3.979 + 5.170 (claim 243174) =
**456.368077876s**. Short diagnostic runs were not individually retained.

State: awaiting independent review.
"""

PLAN_DONE = """
## Done under this claim

1. **Findings recorded before implementation** (`pin_243174.py`), and the live
   run preserved read-only in `live-success-243174/`.
2. **Finding 1 diagnosed**: the custody refusal reproduced through the
   product's own `_state` over the preserved home; seven `0o755` directories
   named. NOT fixed -- recorded as the next selection.
3. **Finding 2 corrected**: `STALLED_TICKS` and `_observation` in
   `baseline.py`; a run that cannot finish stops when it stops moving.
4. **Finding 3 corrected**: `main` catches `SupervisorInterrupted`, prints the
   retained outcome's path and exits 130; a held ending names its path too.
5. **Builder finding corrected**: `snapshot_242687.py` refuses an existing
   destination, gains `--verify` and `--rebuild-into`, and never removes a
   tree. The bound snapshot is verified intact.
6. `test_no_progress.py` reproduces the live stall through actual composition.

Verification: 112 checks, 24.356673542s, receipt `verification-5.json`.

## Next, and whose

* **The reviewer's.** The no-progress rule's conservatism, the interruption
  report, and the custody diagnosis.
* **The owner's.** Whether to select the custody mode gap as the next Work, and
  the remaining `<OWNER>` operands for any further run.
"""

OWNERSHIP = """
## Claim 243174 -- supervisor corrections; no product byte changed

Files added:

    live-success-243174/        read-only copy of the successful run's evidence
    pin_243174.py               the findings and pin, recorded first
    records_243174.py           this claim's dossier writer
    test_no_progress.py         the live stall, reproduced
    verification-5.json/.log    the 112-check receipt

Edited: `baseline.py`, `snapshot_242687.py`, `FINDING.md`, `PLAN.md`,
`PROGRESS.md`, this file.

**Nothing under `v12/` was touched.** The three product paths accepted under
claim 242687 still carry their accepted after-hashes.

PRESERVED and verified under this claim:

    /home/sl/baton-runs/single-implementation-success-239528/run
    /home/sl/baton-runs/single-implementation-242687/manager-source  (--verify)
    /home/sl/baton-runs/managed-correction-236087/manager-source
    /home/sl/baton-runs/single-implementation-239528/
"""


def main():
    progress = HERE / "PROGRESS.md"
    if "claim 243174" not in progress.read_text(encoding="utf-8"):
        progress.write_text(
            progress.read_text(encoding="utf-8").rstrip("\n") + "\n" + PROGRESS,
            encoding="utf-8")
    plan = HERE / "PLAN.md"
    body = plan.read_text(encoding="utf-8")
    old = "## Not in scope\n"
    if "Done under this claim" not in body:
        assert body.count(old) >= 1
        plan.write_text(body.replace(old, PLAN_DONE + "\n" + old, 1),
                        encoding="utf-8")
    owner = HERE / "OWNERSHIP-239528.md"
    if "Claim 243174" not in owner.read_text(encoding="utf-8"):
        owner.write_text(
            owner.read_text(encoding="utf-8").rstrip("\n") + "\n" + OWNERSHIP,
            encoding="utf-8")
    print("records written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
