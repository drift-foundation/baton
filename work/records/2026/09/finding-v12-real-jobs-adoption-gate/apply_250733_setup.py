"""Claim-250733: the setup commands, with the questions replaced by a step.

Owner reroute 250730 selected a fresh isolated two-Job proof instance and asked
for complete operator preparation: "derive technical operands from accepted
configuration and supported APIs instead of leaving them as owner questions.
Deliver exact setup commands and a preparation script..."

So steps 2 and 3 stop asking twelve questions. Step 2 is the fresh instance --
the two acts only a human can do, the directory and the fixture commit, and the
bootstrap. Step 3 is `prepare_two_jobs.py`, one command that derives every
technical operand from the accepted configuration, writes both task documents,
registers the identities, routes and scoped capabilities through the supported
Authority API, resolves the selections and composes and validates the packet
through the shipped composer.

The separation the owner asked for is kept explicit: preparation and execution
are different steps, and preparation reaches no provider, container, credential
or deployed store.
"""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
PLACE = HERE / "ADOPTION-247941.md"

START = "## Step 2 — resolve the selections"
END = "## Step 4 — serve the bounded run, as ONE command"

STEPS = """## Step 2 — create the fresh instance

**The two acts only a human performs**, because this preparation performs no
Git operation and creates no repository for you:

```sh
ROOT=/home/sl/baton-runs/two-jobs-<the fresh identity you choose>
mkdir -p "$ROOT/db"

# The fixture both Jobs are declared from. One base, one repository, and
# nothing in it that either task's target path already occupies.
mkdir -p "$ROOT/fixture-source"
#   ... create the fixture's files, then commit them ...
BASE="$(git -C "$ROOT/fixture-source" rev-parse HEAD)"
```

**The run identity must be fresh.** `prepare_two_jobs.CONSUMED` names every
root this campaign has spent — each holds other work and is preserved evidence
— and the preparation refuses a root that lies under one or that does not name
its own run.

Then bootstrap the instance's Authority with the pinned stack executable, and
keep the uuid it mints:

```sh
AUTH="$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["authority_uuid"])' "$ROOT/bootstrap.json")"
```

## Step 3 — prepare, in one command

```sh
PYTHONPATH="$BOUND:$DOSSIER" "$PY" -B "$DOSSIER/prepare_two_jobs.py" \\
    --run-root "$ROOT" \\
    --authority-uuid "$AUTH" \\
    --source "$ROOT/fixture-source" \\
    --base "$BASE"
```

**This is the whole preparation.** In order it:

  1. refuses a run root that is not this run's own or that lies under a
     consumed instance, and refuses a `--base` that is not one full object
     name;
  2. writes both Jobs' task documents under `$ROOT/tasks/` and **checks that
     their target paths are disjoint** — `greet_a.py` and `greet_b.py`, one
     tiny change each against the one declared base. Two Jobs writing one path
     are one contended change rather than two independent development lines,
     so this is a refusal rather than a convention;
  3. derives the resolved selections — including each Job's full input
     manifest and its `job_input_identity`, computed from the task bytes just
     written so the manifest's `human_contract` and the worker's
     `task_document` cannot disagree — and writes
     `$ROOT/selections-resolved.json`;
  4. performs the Authority acts through the supported API: two Works under a
     derived act identity, both implementers on `impl`, both reviewers on
     `rview`, the integrator on `integration` (the review worker passes its
     answered assignment there), the four scoped capability grants per Work,
     and `canonical_target`;
  5. composes and validates the concrete packet by running `two_jobs.py` —
     the same command this page used to print separately, not a second path.

**What it does not do**: no container, credential, provider, engine or network
is reached, no Job or control store is opened, and no Git operation is
performed. **Executing the run is step 4 and a separate decision.**

A credential is named by REFERENCE — the private registry path and a slot
mapping — and no secret passes through this script or anything it writes.

### Where the operands came from

`prepare_two_jobs.ACCEPTED` carries them with their provenance: the image,
adapter and runtime from W239528 claim 244216 as accepted by
review-2026-09-23T03:19:21Z; the worker profile, policy and retention digests
from the review deployment W239533 executed; the manager source from
ASSESSMENT-249338.md's pin. Step 1 re-checks the artifact digests among them
before any of this runs.

Four identities are this gate's own and are checked for distinctness:
`baton.impl-a`, `baton.review-a`, `baton.impl-b`, `baton.review-b`.

**Running it twice is same-identity replay, not adoption of whatever is
there.** `create_work` is journalled under an act identity derived from the
run, so a repeat answers the same two Works — and a Work that already exists
under somebody ELSE's act is refused rather than absorbed. That was measured
rather than assumed: pointing the step at a Work the witness fixture had
already minted answered `Work '0000000a-W1' already exists`.

"""


def swap(body, old, new, what):
    if body.count(old) != 1:
        raise SystemExit(
            f"REFUSED: {what} appears {body.count(old)} times, not once")
    return body.replace(old, new, 1)


def main():
    body = PLACE.read_text(encoding="utf-8")
    if "## Step 3 — prepare, in one command" in body:
        raise SystemExit("REFUSED: the setup steps are already replaced")
    start, end = body.index(START), body.index(END)
    if not 0 < start < end:
        raise SystemExit("REFUSED: steps 2 and 4 are not where expected")
    body = body[:start] + STEPS + body[end:]
    if body.count("62 checks") != 2:
        raise SystemExit(
            f"REFUSED: the page states 62 checks {body.count('62 checks')} "
            f"times, not twice")
    body = body.replace("62 checks", "71 checks")
    PLACE.write_text(body, encoding="utf-8")

    written = PLACE.read_text(encoding="utf-8")
    for absent in ("62 checks", "## Step 3 — compose, create-only",
                   "Every `<OWNER: …>` in"):
        if absent in written:
            raise SystemExit(f"REFUSED: {absent!r} survives in the page")
    for present in ("## Step 2 — create the fresh instance",
                    "## Step 3 — prepare, in one command",
                    "prepare_two_jobs.py", "--authority-uuid",
                    "Where the operands came from",
                    "Executing the run is step 4 and a separate decision",
                    "71 checks"):
        if present not in written:
            raise SystemExit(f"REFUSED: {present!r} is not in the page")
    print("the setup commands are the preparation step, verified on disk")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
