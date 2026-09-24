"""Claim-253533: recover-or-refuse replaces three wrong assumptions."""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent

PLAN = """# Current action — after claim 253533; RETURNED INCOMPLETE

Review 2026-09-24T03:49:06Z found three P1 defects in the capability I wrote.
All three were real and all three are corrected.

## The three, and what replaced them

  1. **`assignment_workspace` creates missing entries.** So "roots from
     `assignment_workspace` rather than `_mounted`" avoided the stage
     composition and NOT the allocation — my stated reason for the choice was
     wrong. Replaced by `workspaces.adopted_assignment_workspace`, which is
     "the roots an attempt ALREADY HAS, proved and never allocated" and which
     refuses an attempt whose roots are gone, because that "is not a state an
     ending can be performed over".
  2. **`stage=None` omitted an EXISTING launch delivery**, and the adapter then
     reports not-delivered without removing its root — the 172346 leak,
     reintroduced by making the operand optional. `stage` is now REQUIRED and
     bound to this attempt in both the worker and the routing, and a delivery
     that cannot be adopted is a REFUSAL before the fence rather than a None
     passed downstream.
  3. **Ordinary roots do not establish a stage's alternate mounts or custody.**
     Answered by refusing rather than guessing: a worker whose stage
     composition may mount a private line as the writable root is refused by
     name, because a teardown over the ordinary pair would remove the wrong
     tree. The sub-question — a stage composition that can answer its roots
     WITHOUT allocating them — is recorded as the next product step inside the
     owned files.

## Evidence for the edit

  * `tests.tools.test_single_worker` — **162 tests, OK**, 10.103s.
  * `tests.tools.test_stage_execution` — 424 tests, 12 errors, 162.834s; those
    12 were proved PRE-EXISTING last claim by running the identical suite
    against the unmodified pinned snapshot's `tools/`.
  * Every added line fits 79 columns.

**These do not verify the new behaviour** and I am not offering them as that;
they show the edit breaks nothing in the suites that own these files.

## NOT DONE

  1. the seven acceptance boundaries with a fake adapter — omission and
     mismatch, a real stage composition, receiptless fault, prior cancellation
     fence, replay without recreated roots or deliveries, adapter refusal and
     uncertain absence, and positive root cleanup;
  2. the supervisor's explicit shutdown declaration;
  3. the stage composition's adopt-only root answer, which finding 3 defers;
  4. the new digest-bound manager snapshot, then fresh-run commands;
  5. the two operator grants documents with pure and fake-boundary validation;
  6. the executed-image fault diagnosis.

## Standing constraints

The deployed snapshot is immutable and was read only. The failed instance stays
preserved and read-only. No live rerun, deployed-store mutation, container
deletion or cleanup execution.

## Ownership

baton.claude owns this dossier and, from claim 253397,
`v12/python/tools/single_worker.py` and `v12/python/tools/stage_execution.py`.
"""

PROGRESS = """
## 2026-09-24 — baton.claude, claim 253533

### Three assumptions, all wrong, all named by the reviewer

**`assignment_workspace` creates.** I chose it over `_mounted` and wrote down a
reason — that a removal must allocate nothing — which the choice did not
deliver. It avoided the stage composition, not the allocation.
`adopted_assignment_workspace` is the reader that actually asks the invariant
read-only, and it refuses an attempt whose roots are gone rather than making
them.

**Making `stage` optional WAS the leak.** I argued that an absent delivery is a
fact and tolerated None. With an existing delivery omitted, the adapter reports
not-delivered and leaves the launch root — the exact 172346 defect I had quoted
two claims earlier as the thing to avoid. `stage` is required now, bound to the
attempt in the worker and again in the routing, and an unadoptable delivery
refuses before the fence.

**Ordinary roots are not a composed stage's roots.** A stage may mount a
private line as the writable root, so a teardown over the ordinary pair can
remove the wrong tree. I refuse that case by name instead of choosing, and the
sub-question — a stage composition that answers its roots without allocating
them — is recorded rather than improvised.

### And one more of my own, in the checking

The apply script's own guard refused on `stage=None` surviving, and what it had
found was two unrelated pre-existing constructor defaults. The edit was already
on disk; only the over-broad check failed. Same class of mistake as the
`"180s per attempt"` guard that could not tell a claim from a correction of one
— a check that reads text without asking where it is.

### Evidence, and what it is not

`test_single_worker`: 162 tests, OK. `test_stage_execution`: 424 tests, 12
errors — proved pre-existing last claim against the unmodified pinned `tools/`.
Every added line fits 79 columns. **None of this verifies the new behaviour**,
and the seven boundaries remain the thing that would.

### Verification spending

Product suites, disclosed separately from the named subtotal:
`test_single_worker` 10.103s, `test_stage_execution` 162.834s — 172.937s this
claim, on top of the 335.453s disclosed last claim. The named suite subtotal is
unchanged at **1047.869180986s** (`verification-27.json`, 85 checks, 0
failures, pins agree), and the unmeasured 120s command-timeout run and all
earlier unknowns stand.

State: returned INCOMPLETE through baton.bug with the remaining scope named.
"""


def main():
    (HERE / "PLAN.md").write_text(PLAN, encoding="utf-8")
    progress = HERE / "PROGRESS.md"
    body = progress.read_text(encoding="utf-8")
    if "claim 253533" not in body:
        progress.write_text(body.rstrip("\n") + "\n" + PROGRESS,
                            encoding="utf-8")
    print("records written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
