"""Claim-243990 dossier entries: the remaining R2 and R3."""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent

PROGRESS = """
## 2026-09-23 -- baton.claude, claim 243990, remaining R2/R3

Review 2026-09-23T01:02:06Z closed R1 and left four narrow corrections; owner
reroute 243987 selects exactly those. Done. No file under `v12/` was edited;
the three product paths accepted under claim 242687 still carry their accepted
after-hashes. No store opened, no container, no credential, no live run, no
provisioning, no recovery, no closure.

**R2 -- truthful creation provenance.** The CLI called the builder with the
ORIGINAL's claim for every build, so a successor created under a different
assignment still recorded 242906. A manifest naming the wrong episode is worse
than one naming none: it reads as evidence somebody produced under review that
nobody did. `--claim <seq>` is now required for a successor and refused before
anything is copied; the original replays its own `ORIGINAL_CLAIM` and its
historical manifest is untouched. The manifest distinguishes CREATION from
RECIPE -- `created_by_claim` is the episode that ran it, `recipe.original_claim`
and `recipe.original_path` are what it shares with the original -- because a
successor shares the recipe and does not share the authorship. Three CLI
regressions: the claimless refusal, the recorded provenance, and the original's
claim still reading 242906.

**R3 -- four defects in the successor command, all real.**

* `$BASE` was invoked but never assigned, so in a fresh shell it expanded
  empty. It is bound now from the fixture repository step 2 creates, and the
  document says `$BASE` must also be the Authority's canonical target.
* Precondition 3 linked `OPERATOR-239528.md`'s step 5a, which literally opens
  `/home/sl/baton-runs/single-implementation-239528/db/authority.sqlite3` and
  writes to it. That is a write-capable example pointed at a preserved
  instance holding an unfinished Job. The successor now carries its own
  preparation block reading STORE, UUID, Work, participants and receipts from
  `$SEL`, with an assertion that refuses if an older instance creeps in.
* The comparison table credited the REFUSED draft's pre-correction snapshot
  and 900-second bound to `OPERATOR-FAILURE-242687.md`, which was ACCEPTED and
  already carries the corrected snapshot and 120/30. Two tables now: what this
  successor changes against the accepted failure packet (300/60, and which
  ending it expects to reach), and separately what has changed since the
  refused draft.
* No test referenced the actual successor selections or its document.
  `test_successor_packet.py` reads the delivered file as delivered -- bounds,
  bound snapshot, every store the successor's own with all four older roots
  named and excluded, run and Job identity, supervisor digest, and which
  members are still `<OWNER>` -- asserts the document's four corrections, and
  composes the real selections substituting ONLY the `<OWNER>` members, then
  runs the documented composer as a child process with `PYTHONPATH` bound to
  the real successor snapshot. `manager_source` and `code_boundary` travel
  verbatim, because substituting them would test a tree nobody ships.

**The custody blocker stays explicit.** The document still opens with it, the
selections still carry `_unresolved_blocker`, and
`TheDocumentSaysWhatItIsNotReadyFor` asserts both rather than trusting them to
stay.

Verification: 139 focused deterministic checks, measured 25.444851811989793s,
receipt `verification-7.json` with `verification-7.log`. The 121 earlier checks
are unchanged and included; 18 are new.

Cumulative measured for W239528: 506.111439014s (through claim 243284) +
25.444851812 + 25.374094302 + 0.408 + 1.618 (claim 243990) =
**558.956385128s**.

State: awaiting independent review. Successful baseline still not ready, and
the packet says so first.
"""

PLAN = """# Current action -- remaining R2/R3 done; custody blocker still open

## Active -- claim 243990, baton.claude

Review 2026-09-23T01:02:06Z closed R1; owner reroute 243987 selects the four
narrow corrections that remained. Done. No product byte changed.

1. **R2.** `--claim <seq>` is required for a successor snapshot and refused
   before anything is copied; the original replays its own and its historical
   manifest is untouched. The manifest separates `created_by_claim` from
   `recipe`. Three CLI regressions.
2. **R3.** `$BASE` bound from the fixture; a successor-specific step 5a
   reading every operand from `$SEL` with an assertion against older
   instances; the comparison table corrected so the ACCEPTED failure packet is
   no longer credited with the refused draft's inputs;
   `test_successor_packet.py` exercising the actual selections and the
   documented entrypoint deterministically.

Verification: 139 checks, 25.444851811989793s, receipt `verification-7.json`.

## THE BLOCKER THIS DOES NOT CLEAR

The custody-mode failure is unresolved, so the successor packet is NOT
successful-baseline ready and says so first -- asserted, not merely written.
The next selection is the product decision: whether the manager should
tolerate a umask-created directory inside the private context home, or the
delivery should impose the mode.

## Not in scope

Any live run, provisioning, recovery, reviewer stage, resume or closure.

---

"""

OWNERSHIP = """
## Claim 243990 -- remaining R2/R3; no product byte changed

Added: `test_successor_packet.py`, `records_243990.py`,
`verification-7.json/.log`.

Edited: `snapshot_242687.py` (R2 provenance),
`OPERATOR-SUCCESSOR-243284.md` (R3), `test_successor_snapshot.py`,
`PLAN.md`, `PROGRESS.md`, this file.

**Nothing under `v12/` was touched.** The historical
`MANAGER-SOURCE-242687.json` is unchanged and still records claim 242906. The
R2 regressions build only into temporary directories and remove the manifests
they create.
"""


def main():
    progress = HERE / "PROGRESS.md"
    if "claim 243990" not in progress.read_text(encoding="utf-8"):
        progress.write_text(
            progress.read_text(encoding="utf-8").rstrip("\n") + "\n" + PROGRESS,
            encoding="utf-8")
    plan = HERE / "PLAN.md"
    body = plan.read_text(encoding="utf-8")
    if "claim 243990" not in body:
        head = body.split("\n", 1)[0]
        plan.write_text(PLAN + body.replace(
            head, "# Historical action" + head.split("action", 1)[-1], 1),
            encoding="utf-8")
    owner = HERE / "OWNERSHIP-239528.md"
    if "Claim 243990" not in owner.read_text(encoding="utf-8"):
        owner.write_text(
            owner.read_text(encoding="utf-8").rstrip("\n") + "\n" + OWNERSHIP,
            encoding="utf-8")
    print("records written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
