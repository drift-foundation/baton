"""Claim-242906 dossier entries: R1 and R2 packet corrections."""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent

PROGRESS = """
## 2026-09-22 -- baton.claude, claim 242906, R1 and R2 packet corrections

Review 2026-09-22T23:53:34Z ACCEPTED the product correction and refused the
failure command on two counts; owner reroute 242903 selects only those two
corrections. Both are done. No product byte changed under this claim, no store
was opened, no container started, no credential read, no live provider called,
no deployment provisioned and nothing recovered. Credentials remain expired.

**R1 -- the command would have run the uncorrected code, and the reviewer is
right.** `OPERATOR-FAILURE-242687.md` bound
`/home/sl/baton-runs/managed-correction-236087/manager-source` as its import
path. That snapshot was taken under W236087; I bound it without reading it. It
holds `review_driver.py` `b5b22535...ebe10c` and `stage_execution.py`
`33c78091...6e81` -- exactly the PRE-correction bytes -- so the documented
command would have imported the unconditional publication and the context-held
ending, and reproduced the 900-second stall it exists to disprove. I confirmed
that by reading those two files directly.

`snapshot_242687.py` prepares a SUCCESSOR snapshot at
`/home/sl/baton-runs/single-implementation-242687/manager-source`: the same
flat `baton_v12/` + `tools/` layout, 106 files, copied from the corrected
checkout. It then VERIFIES rather than assumes -- the two corrected modules
must carry the independently accepted digests (`9a8a4a81...20ae4`,
`ebc9be29...032896`) and the preserved snapshot must still carry the superseded
ones -- and refuses to write its manifest if either check fails. The old
snapshot is untouched: W236087's own packet is bound to those bytes, and the
reviewer said plainly that overwriting it is not the remedy.

`test_successor_snapshot.py` exercises it in three parts, because the claim has
three halves that can each be wrong alone: the snapshot carries the accepted
bytes and the preserved one still carries the superseded ones (asserted against
the FILES, not against the manifest that describes them, plus a check that the
two digests genuinely differ so the other two mean something); a CHILD PROCESS
with the documented `PYTHONPATH` reports which `review_driver.py` it actually
loaded and that `PUBLISHABLE` is present, with the reviewer's counterexample
kept as a regression -- the same child bound to the preserved snapshot answers
`False`; and the expired-credential replay settles against a packet whose
`manager_source` and `code_boundary` ARE the snapshot, at the owner's bounds.

**R2 -- the operational finding is exactly right.** `OPERATOR-FAILURE-242687.md`
named `SELECTIONS-FAILURE-242687.json` and the dossier contained no such file,
so the lower bounds and the new run and store operands were prose rather than a
composed input anyone could review. That file now exists, and
`test_the_selections_name_this_snapshot_and_these_bounds` checks it against the
packet the replay actually proved rather than letting it drift.

It binds `total_seconds: 120` and `cleanup_seconds: 30` per owner reroute
242903, the successor snapshot, a new run identity
`single-implementation-242687` (the 239528 grant was consumed by its own
failure), and genuinely fresh dedicated Authority, Job, control and integration
stores.

**And I weakened an accepted boundary, which the reviewer caught.** The previous
precondition said the first run's instance was reusable and reduced the rule to
"no other live work". The accepted boundary excludes stores containing OTHER
WORK, and the first W239528 run left an unfinished ending and cleanup in those
stores -- that is preserved failure evidence, not an empty instance. Admission
filtering scopes new stages to this Job; it does not isolate store-wide
recovery and endings. The corrected preconditions say the first run's instance
is NOT reusable, and the selections point at fresh stores; a test asserts none
of the four store paths names the 239528 root.

The operator document also now tells an operator the one thing that would
silently reproduce the defect: check `manager_source.files` in the composed
packet, and if `review_driver.py` reads `b5b22535...` you are composing against
the preserved snapshot.

Verification: 100 focused deterministic checks, measured 19.205028231s, receipt
`verification-4.json` with `verification-4.log`. The 87 earlier checks are
unchanged and included; 13 are new. No product suite was re-run under this
claim because no product byte changed -- `PRODUCT-CHANGE-242687.json`'s after
hashes still describe the tree, and the reviewer verified all three
independently.

Cumulative measured for W239528, listing the runs: 7.146396201 + 7.149914038 +
7.138971223 (claim 239653) + 15.684039575 + 15.704004109 + 7.187 + 6.480 +
7.670 (claim 240196) + 17.608050957 + 15.699 + 5.414 + 37.901 + 159.202 +
38.245 + 38.117 + 2.118 (claim 242687) + 19.205028231 + 1.493 (claim 242906) =
**409.162404334s**. Short diagnostic runs were not individually retained.

State: awaiting independent review.
"""

PLAN = """# Current action -- the successor failure-path command, awaiting review

## Active -- claim 242906, baton.claude

Review 2026-09-22T23:53:34Z accepted the product correction and refused the
failure command on two counts. Owner reroute 242903 selects only those two
packet corrections. Both are done.

No product byte changed under this claim. No store opened, no container, no
credential, no live provider, no provisioning, no recovery. Credentials remain
expired by owner decision.

### Done

1. **R1.** `snapshot_242687.py` prepares and verifies a SUCCESSOR
   manager-source snapshot at
   `/home/sl/baton-runs/single-implementation-242687/manager-source` carrying
   the accepted `review_driver.py` and `stage_execution.py`; the W236087
   snapshot is preserved untouched. `MANAGER-SOURCE-242687.json` manifests
   both. `test_successor_snapshot.py` proves the bytes, proves a child process
   with the documented import path loads them, keeps the reviewer's
   counterexample, and drives the expired-credential replay against a packet
   bound to that exact snapshot.
2. **R2.** `SELECTIONS-FAILURE-242687.json` exists and binds the 120/30 bounds,
   the successor snapshot, the new run and Job identity, and genuinely fresh
   dedicated Authority/Job/control/integration stores. The first run's instance
   is recorded as NOT reusable -- it holds unfinished work and is preserved
   evidence. `OPERATOR-FAILURE-242687.md` is rewritten around both.

Verification: 100 focused deterministic checks, 19.205028231s, receipt
`verification-4.json`.

### Next, and whose

* **The reviewer's.** The successor snapshot binding, the composed selections
  and the store boundary.
* **The owner's**, and none of it authorized here: bootstrapping the fresh
  instance, step 5a, the `<OWNER>` selections, and whether to run the bounded
  failure command at all.

## Not in scope, and not done

Credential renewal. Any live run. Any deployed provisioning. Reuse of, or
recovery on, the first W239528 run's stores or runtime, or W236087's.
Overwriting the preserved snapshot. Any reviewer stage or session resume. Any
Work closure.

---

"""

OWNERSHIP = """
## Claim 242906 -- packet corrections only; no product byte changed

Files added:

    MANAGER-SOURCE-242687.json     manifests both snapshots
    SELECTIONS-FAILURE-242687.json the composed failure-path input
    snapshot_242687.py             prepares and VERIFIES the successor snapshot
    test_successor_snapshot.py     the three-part exercise of it
    records_242906.py              this claim's dossier writer
    verification-4.json/.log       the 100-check receipt

`OPERATOR-FAILURE-242687.md`, `PLAN.md`, `PROGRESS.md` and this file were
edited under this claim.

OUTSIDE the checkout, and both are new rather than modified:

    /home/sl/baton-runs/single-implementation-242687/manager-source
        the successor snapshot, 106 files

PRESERVED and NOT written to, verified under this claim:

    /home/sl/baton-runs/managed-correction-236087/manager-source
        still the pre-correction bytes W236087's packet is bound to
    /home/sl/baton-runs/single-implementation-239528/
        the first run's stores, runtime and evidence; its ending and cleanup
        are unfinished and that is the evidence

Nothing under `v12/` was touched under this claim; the three paths changed
under claim 242687 still carry their accepted after-hashes. The reviewers' own
files for all three reviews are untouched.
"""


def main():
    progress = HERE / "PROGRESS.md"
    if "claim 242906" not in progress.read_text(encoding="utf-8"):
        progress.write_text(
            progress.read_text(encoding="utf-8").rstrip("\n") + "\n" + PROGRESS,
            encoding="utf-8")
    plan = HERE / "PLAN.md"
    body = plan.read_text(encoding="utf-8")
    if "claim 242906" not in body:
        head = body.split("\n", 1)[0]
        plan.write_text(PLAN + body.replace(
            head, "# Historical action" + head.split("action", 1)[-1], 1),
            encoding="utf-8")
    owner = HERE / "OWNERSHIP-239528.md"
    if "Claim 242906" not in owner.read_text(encoding="utf-8"):
        owner.write_text(
            owner.read_text(encoding="utf-8").rstrip("\n") + "\n" + OWNERSHIP,
            encoding="utf-8")
    print("records written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
