"""Claim-255973: the supervisor declares; and why the pinned suite was red."""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent

PLAN = """# Current action — after claim 255973; RETURNED INCOMPLETE

Review 2026-09-24T10:23:12Z asked for the stale docstring, the five remaining
items, and named the constraints the supervisor step must keep. Two items
moved, and a third thing turned up on the way.

## The stale docstring, corrected

`test_abandonment.py::test_an_altered_stage_context_is_measured_and_not_assumed`
still said the acceptance was "a real hazard" because `kind` decides mounts.
It now says what claim 255929 measured: `StageComposition._prepare` branches on
its own `self.role`, `_recovered` reads the attempt's durable grant, and in the
UNPOOLED composition `self.stage` is `None`, so the stage-mount branch is not
reached at all. The accepted members are inert context, and the routed binding
is operand hygiene rather than what keeps the tree correct.

## The supervisor's explicit shutdown declaration — DONE

`two_job_supervisor.py` (this dossier's, mine):

  * **`TwoJobGate` records the whole launch document** beside the stage id it
    already kept, copied rather than held. An abandonment takes the attempt's
    own stage and there is nowhere else to get it once the run is stopping.
  * **`_abandonment_eligible`** answers per attempt, with a sentence.
    "Outstanding alone is not eligibility": no attached runtime, a terminal
    cleanup axis, an `uncertain` observation, or a committed intake receipt
    each disqualifies, and each is somebody else's ending. The receipt one is
    the one that matters most — declaring an answered turn abandoned would
    relabel somebody's result.
  * **`_declare_abandonment`** declares each eligible attempt, reads the
    cleanup and the discharge BACK rather than taking them from the answer,
    and reports every outcome including the failures with their type and text.
  * **`outstanding_cleanup` is left exactly as it was.** `baseline._cleanups`
    reads the ORDINARY cleanup journal, which an abandonment does not write
    to; folding these into it would report one ending's record under another's
    name. `abandonment`, `abandoned_cleanup` and `undeclared_cleanup` are
    separate members.

Proved in `test_abandonment.py`: the step is CALLED over the real stores — one
eligible attempt settles `retained` with its gate discharged, and two
ineligible ones are reported with their own reasons; and the answered-worker
rule refuses by name.

## An operational finding, and it is why the dossier suite was red

`verify_247941.py` pins the manager-source snapshot at **106 files** and
manifest `ab5e5b0b…`. The snapshot now holds **193**. The extra 87 are
`__pycache__` byte-code written into it at 2026-09-24T04:27 — importing from a
directory writes caches into that directory, which is what the documented
`PYTHONPATH=<snapshot>` invocation does.

**No source file was touched**, and that is established rather than assumed:
none has an mtime later than the pin; the 106 remaining are byte-identical to
the working tree except the three files this Work owns and has edited; and with
the caches excluded the manifest reproduces the pinned `ab5e5b0b…` EXACTLY.

So `manifest_digest` and the file count now take SOURCE files, which is what
they were always meant to describe, and the suite is run with byte-code
writing disabled so nothing writes into preserved material again. **Nothing was
deleted from the snapshot** — removing files from preserved evidence is not
this Work's to do, and a digest made true by tidying the evidence would not be
a digest.

With that, `test_two_jobs` is **85 tests, OK, 69.207s** — including the
supervisor running end to end with the new step in it.

## REMAINING

  1. first-call crash and launch-absent alternate recovery;
  2. a supervised run that actually STRANDS an attempt, so the declaration is
     proved through `supervise` and not only through its own function;
  3. the two operator grants documents with validation and readback;
  4. the executed-image fault diagnosis;
  5. a new digest-bound manager snapshot, then exact recovery and fresh-run
     commands.

No external blocker.

## Standing constraints

No deployed mutation, live rerun or cleanup execution. The preserved instance
and the snapshot are read-only; the snapshot was READ and its stray caches were
left where they are.

## Ownership

`OWNERSHIP-255823.md`: `tools/single_worker.py`, `tools/stage_execution.py`,
`src/baton_v12/worker_manager/intake.py`, and this dossier.
"""

PROGRESS = """
## 2026-09-24 — baton.claude, claim 255973

### The supervisor declares now, and only where it may

The step exists: record the launch document, ask each outstanding attempt
whether an abandonment may end it, declare the ones that qualify, read the
cleanup and discharge back, and report every outcome — the refusals with their
type and text. Your sentence set the shape: outstanding is the candidate list,
not the eligibility. A worker that ANSWERED keeps its ordinary ending, and
declaring it abandoned would relabel somebody's result.

I left `outstanding_cleanup` alone on purpose. It reads the ordinary cleanup
journal, which an abandonment does not write to, so folding the declared ones
into it would report one ending's record under another's name.

### Why the dossier's own suite was red, and it was not the supervisor

I ran `test_two_jobs` and got 22 failures. My first thought was my edit. It was
not: the suite requires `baton_v12` to resolve to the pinned snapshot, and I
had it on the working tree. Bound correctly, it still failed — on the pin:
193 files where 106 are pinned.

The 87 extra are `__pycache__`, written into the snapshot at 04:27 by a run
that imported from it. Importing from a directory writes into that directory,
which is exactly what the documented invocation asks for.

I checked before concluding, because "the snapshot drifted" is the kind of
sentence that should cost something to say: no source file has a later mtime,
the 106 are byte-identical to the working tree apart from the three I own and
have edited, and excluding the caches reproduces the pinned digest exactly.
One thing I got wrong on the way and corrected: my first recomputation
disagreed with the pin because my helper prefixed `sha256:` and the module's
does not — the mismatch was mine, not the snapshot's.

So the manifest takes source files now, the suite runs with byte-code disabled,
and I deleted nothing from the preserved snapshot. A digest made true by tidying
the evidence is not a digest.

### Verification spending

`test_abandonment` + `test_routed_abandonment` — 31 cases, all passing,
**1.870s**, clean under `-W error::ResourceWarning`; 1.106s and 1.251s
intermediates.
`test_two_jobs` — 85 tests, **OK, 69.207s**, with the pinned snapshot bound and
byte-code disabled. Before that, two red runs of the same suite at 31.663s and
31.822s — both invocation and pin problems rather than results, and both
disclosed here as spent.

The 424-case stage-execution suite was NOT repeated. Everything prior stands:
899 tests OK 19.828s, 9.308s, 10.337s, 159.910s plus its untimed repeat,
0.966s, 1.170s, 10.041s, 9.966s, 0.348s, 0.130s, 0.094s, the combined
1.090/1.334/1.536/1.677/1.760/1.805s, the focused runs listed in earlier
entries, the untimed probes and diagnostic reads, the unmeasured ~120s
command-timeout run and the earlier unknowns, alongside named
**1047.869180986s**.

State: returned INCOMPLETE through baton.bug with the supervisor step
delivered, the pin question resolved honestly, and four items open.
"""


def main():
    (HERE / "PLAN.md").write_text(PLAN, encoding="utf-8")
    progress = HERE / "PROGRESS.md"
    body = progress.read_text(encoding="utf-8")
    if "claim 255973" not in body:
        progress.write_text(body.rstrip("\n") + "\n" + PROGRESS,
                            encoding="utf-8")
    print("records written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
