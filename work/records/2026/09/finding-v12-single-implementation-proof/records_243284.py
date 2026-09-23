"""Claim-243284 dossier entries: R1, R2 and R3."""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent

PROGRESS = """
## 2026-09-23 -- baton.claude, claim 243284, R1/R2/R3

Review 2026-09-23T00:50:59Z requested three corrections; owner reroute 243281
selects all three. Done. No file under `v12/` was edited under this claim; the
three product paths accepted under claim 242687 still carry their accepted
after-hashes. No store opened, no container, no credential, no live run, no
renewal, no recovery, no closure.

**R1, P1, and it was mine.** The progress read I added under claim 243174
called `_guarded` with DISPOSABLE `uncertainty=[]` and `interrupted=[]` lists.
`_guarded` catches `BaseException`, so the `KeyboardInterrupt` the installed
handler raises was swallowed there, the predicate returned True and ORDINARY
SERVING RESUMED. The reviewer's actual-composition probe injected SIGINT before
any provider turn and watched a whole turn execute afterwards; a direct
`KeyboardInterrupt` vanished into a `settled` outcome. I introduced that while
correcting a different stall, and it is exactly the kind of regression the
no-progress rule was supposed to prevent.

The read now catches `Exception` only. An unreadable journal is still
progress-neutral -- it resets the counter rather than advancing it, failing
towards keeping the run alive -- and its diagnostic goes into the run's REAL
`uncertainty` list instead of being discarded. `KeyboardInterrupt` and
`SystemExit` travel out of the predicate, out of `serve`, and into the shutdown
handler that already existed; the fix is to stop standing in front of it.

Four regressions at that exact boundary:
`AnInterruptionAtTheProgressReadStopsServing` covers the signal shape and the
direct shape, each asserting NO further provider turn, a retained interrupted
outcome and a non-zero `main` status; a third keeps the ordinary-failure
direction and asserts the diagnostic is kept; a fourth drives `main` to 130.

**R2.** `--rebuild-into` changed only the destination tree and still wrote the
fixed `MANAGER-SOURCE-242687.json`, so a successor replaced the accepted
predecessor's manifest and the default `--verify` then checked the old tree
against the new one. A successor that destroys its predecessor's evidence is
the same mistake the snapshot existed to avoid. `manifest_for` now pairs each
snapshot with its own manifest, an existing manifest is refused as firmly as an
existing tree, and `--verify` checks the selected PAIR and refuses a manifest
that names a different path. Five regressions over disposable trees only,
including the defect itself -- the bound manifest must be byte-identical after
a successor is built -- and each cleans up the manifest it creates.

**R3.** `BOUNDS.total_seconds` is 300 rather than 900, argued rather than
picked: it covers one provider turn at its own 180-second ceiling plus the
launch, the exchange, the ending's nine journalled steps and the publication,
and it no longer has to cover a run that stopped moving, which
`STALLED_TICKS` detects in six. Measured against the two real runs -- 31 ms and
18.3 s of provider time -- 300 leaves two minutes of headroom over a
full-length turn neither came close to using.

`OPERATOR-SUCCESSOR-243284.md` and `SELECTIONS-SUCCESSOR-243284.json` deliver
the concrete successor packet: the verified successor snapshot, 300/60 bounds,
a new run and Job identity, and fresh dedicated stores -- EVERY earlier
instance now holds other work and none is reusable.

**And the packet says first that it is NOT successful-baseline ready.** Owner
reroute 243281 is explicit about this and it is right: the custody-mode blocker
is unresolved, so a run today will reach it. What it will do differently is
report it in about six seconds instead of spending its bound, and name the
retained outcome. That is better reporting, not an end-to-end proof, and the
document, the selections `_unresolved_blocker` block and this entry all say so
rather than leaving a reader to infer it.

Verification: 121 focused deterministic checks, measured 25.037361138s, receipt
`verification-6.json` with `verification-6.log`. The 112 earlier checks are
unchanged and included; 9 are new.

Cumulative measured for W239528: 456.368077876s (through claim 243174) +
25.037361138 + 11.524 + 5.716 + 5.848 + 1.618 (claim 243284) =
**506.111439014s**.

State: awaiting independent review.
"""

PLAN = """# Current action -- R1/R2/R3 corrected; the custody blocker still open

## Active -- claim 243284, baton.claude

Review 2026-09-23T00:50:59Z requested three corrections and owner reroute
243281 selects all three. Done. No product byte changed under this claim.

1. **R1, P1.** The progress read I added under 243174 swallowed
   `KeyboardInterrupt` through `_guarded` with disposable lists, so serving
   resumed after an operator asked the run to stop. It now catches `Exception`
   only; interruptions reach the existing shutdown. Four regressions at that
   exact boundary.
2. **R2.** Each snapshot now has its own manifest; an existing manifest is
   refused as firmly as an existing tree; `--verify` checks the selected pair.
   Five regressions over disposable trees.
3. **R3.** `total_seconds` 300, argued. `OPERATOR-SUCCESSOR-243284.md` and
   `SELECTIONS-SUCCESSOR-243284.json` deliver the concrete packet and commands.

Verification: 121 checks, 25.037361138s, receipt `verification-6.json`.

## THE BLOCKER THIS DOES NOT CLEAR

The custody-mode failure is unresolved. `context_delivery._private` refuses any
custody directory carrying group or other bits and the real CLI creates seven
of them at `0o755`. **The successor packet is therefore NOT
successful-baseline ready and says so first**, as owner reroute 243281
requires.

The next selection is the product decision: whether the manager should tolerate
a umask-created directory inside the private context home, or the delivery
should impose the mode on the tree it hands the container. Diagnosed under
claim 243174 with the exact refusing check; deliberately not decided.

## Not in scope

Any live run, recovery, destructive cleanup, reviewer stage, resume or closure.

---

"""

OWNERSHIP = """
## Claim 243284 -- R1/R2/R3; no product byte changed

Added: `OPERATOR-SUCCESSOR-243284.md`, `SELECTIONS-SUCCESSOR-243284.json`,
`records_243284.py`, `verification-6.json/.log`.

Edited: `baseline.py` (R1), `snapshot_242687.py` (R2),
`baseline_bindings.py` (R3 bounds), `test_no_progress.py`,
`test_successor_snapshot.py`, `PLAN.md`, `PROGRESS.md`, this file.

**Nothing under `v12/` was touched.** The three product paths accepted under
claim 242687 still carry their accepted after-hashes.

PRESERVED and verified: the bound successor snapshot and its manifest
(`--verify`), the W236087 snapshot, and all three earlier run roots. The R2
regressions build only into temporary directories and remove the manifests
they create.
"""


def main():
    progress = HERE / "PROGRESS.md"
    if "claim 243284" not in progress.read_text(encoding="utf-8"):
        progress.write_text(
            progress.read_text(encoding="utf-8").rstrip("\n") + "\n" + PROGRESS,
            encoding="utf-8")
    plan = HERE / "PLAN.md"
    body = plan.read_text(encoding="utf-8")
    if "claim 243284" not in body:
        head = body.split("\n", 1)[0]
        plan.write_text(PLAN + body.replace(
            head, "# Historical action" + head.split("action", 1)[-1], 1),
            encoding="utf-8")
    owner = HERE / "OWNERSHIP-239528.md"
    if "Claim 243284" not in owner.read_text(encoding="utf-8"):
        owner.write_text(
            owner.read_text(encoding="utf-8").rstrip("\n") + "\n" + OWNERSHIP,
            encoding="utf-8")
    print("records written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
