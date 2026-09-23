"""Claim-244389 dossier entries: R1, R2, and the documented entrypoint."""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent

PROGRESS = """
## 2026-09-23 -- baton.claude, claim 244389, R1/R2 and the real entrypoint

Review 2026-09-23T03:42:19Z R1 and R2; owner reroute 244386 selects both and
adds the entrypoint test. Done. No image rebuild, no live provider, no deployed
provisioning, no recovery, no reviewer stage, no resume, no closure. **No file
under `v12/` was edited.**

**R1 -- the documented command could not run as printed.** Step 5a imports
`baton_v12.authority`, and the block did not bind `PYTHONPATH`; the reviewer
ran it in a fresh shell and got `ModuleNotFoundError`. Every other command on
that page binds the selected manager source and this one simply did not. It
now reads `PYTHONPATH="$BOUND" "$PY" -B "$DOSSIER/prepare_instance.py"`, and the
page says why, naming the review that found it.

**R2 -- the freshness check could be walked around.** `fresh()` compared
consumed-instance names with `in` against the raw store string and exempted any
name equal to the run, so `/home/sl/baton-runs/single-implementation-244216/../
single-implementation-239528/jobs.sqlite3` passed: the substring matched the
run, the exemption fired, and the check let a store inside a CONSUMED run
through. It now normalizes the path first and compares COMPONENTS, requires the
run to be a component of each store rather than a substring, and refuses a
consumed `run_id` outright with no exemption. A valid new instance still
replays, which is the behaviour measurement established last claim and which
the R2 work had to preserve rather than trade away.

**The entrypoint is now exercised as an entrypoint.** Earlier cases drove
`prepare_instance.prepare` in-process; `TheDocumentedEntrypointRunsThroughComposition`
runs the command the page prints, as a subprocess, from `/`, against a
disposable Authority, and then composes the SAME resolved document through
`baseline_bindings`. It reads the results back through the Authority's own
public readers, and a companion case runs the same command with `PYTHONPATH`
unset and holds it to the exact failure the review reported -- so R1 has a
regression, not just a corrected sentence.

**Three things the test surfaced, each recorded rather than smoothed over.**
The freshness check refused the fixture's own store paths, because they do not
lie under a run directory -- that is the check working, so the case copies the
disposable Authority into a run-named directory instead of weakening it.
`create_work` refused the fixture's existing Work under a different operation
identity, correctly: preparing a successor must not adopt somebody else's Work,
so the case derives a fresh name that still carries this Authority's prefix.
And the bound source cannot be the fixture's tiny `boundpkg` tree, so it is
derived from where this process actually imported `baton_v12`; the comment says
why, since binding the fixture tree would have made the R1 regression pass for
the wrong reason.

Verification: 174 focused deterministic checks, measured 27.046156366996s,
receipt `verification-11.json` with `verification-11.log`; 8 are new.

Preservation, checked at the end of this claim rather than asserted: all five
product paths carry their currently accepted after-hashes -- the
`test_claude_context.py` entry in `PRODUCT-CHANGE-242687.json` is superseded by
`PRODUCT-CHANGE-244098.json`, whose `before` equals it exactly, and the tree
matches the later record. Both images are unchanged
(`sha256:c862c055...`, `sha256:2e9e84ff...`), the bound manager-source snapshot
verifies at 106 files, all ten inherited W236087 digests are byte-identical,
and `git diff --check` is clean. No mutating Git operation was performed.

Cumulative measured for W239528: 790.244003025s (through claim 244292) +
27.046156367 + 1.569 (claim 244389) = **818.859159392s**.

State: awaiting independent review.
"""

PLAN_DONE = """
## Done under claim 244389

1. `OPERATOR-SUCCESSOR-244216.md` step 5a binds `PYTHONPATH="$BOUND"` and says
   why, naming the review that ran it unbound (R1).
2. `prepare_instance.fresh` refuses a consumed `run_id` unconditionally and
   compares NORMALIZED PATH COMPONENTS, closing the substring/traversal
   walk-around while preserving valid new-instance replay (R2).
3. `AConsumedIdentityIsRefusedHoweverItIsSpelled`: six cases over the spellings
   the old check let through.
4. `TheDocumentedEntrypointRunsThroughComposition`: the printed command run as
   a subprocess against a disposable Authority, composed through
   `baseline_bindings` over the same resolved document, plus the unbound-
   `PYTHONPATH` regression for R1.

Verification: 174 dossier checks, 27.046156366996s, receipt
`verification-11.json`. Accepted source, both images and the 180/300/60 limits
are unchanged.
"""

OWNERSHIP = """
## Claim 244389 -- R1/R2 and the documented entrypoint

Added: `records_244389.py`, `verification-11.json/.log`.

Edited: `prepare_instance.py`, `test_preparation.py`,
`OPERATOR-SUCCESSOR-244216.md`, `verify.py`, `PLAN.md`, `PROGRESS.md`, this
file.

**No file under `v12/` was edited, and no image was rebuilt.** All five product
paths carry their currently accepted after-hashes; both images, both
manager-source snapshots, every consumed instance and all ten inherited
W236087 digests were re-read and are unchanged. The entrypoint test builds only
inside a temporary directory and copies -- never moves or chmods -- the
disposable Authority it opens.
"""


def main():
    progress = HERE / "PROGRESS.md"
    if "claim 244389" not in progress.read_text(encoding="utf-8"):
        progress.write_text(
            progress.read_text(encoding="utf-8").rstrip("\n") + "\n" + PROGRESS,
            encoding="utf-8")
    plan = HERE / "PLAN.md"
    body = plan.read_text(encoding="utf-8")
    old = "## Not in scope\n"
    if "## Done under claim 244389" not in body:
        plan.write_text(body.replace(old, PLAN_DONE + "\n" + old, 1),
                        encoding="utf-8")
    owner = HERE / "OWNERSHIP-239528.md"
    if "Claim 244389" not in owner.read_text(encoding="utf-8"):
        owner.write_text(
            owner.read_text(encoding="utf-8").rstrip("\n") + "\n" + OWNERSHIP,
            encoding="utf-8")
    print("records written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
