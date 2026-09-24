"""Claim-250859: the page names the bootstrap's own layout, outside the boundary.

Review 2026-09-23T20:34:15Z found three defects in what this page printed, and
all three were mine:

  * the selected run root was under `/home/sl/baton-runs`, which the pinned
    validator treats as the checkout, so the composition it told an operator to
    run refuses by name;
  * step 2 said "bootstrap" and printed no bootstrap command, only a read of a
    document nothing created;
  * and the preparation, the supervisor command and the read-only inspection
    named three layouts that no reading of `<run root>` could reconcile. My
    previous "correction" of that mismatch moved step 6 onto step 4's paths;
    the bootstrap's own layout says `db/`, so I reconciled to the wrong side.

Every path on the page now comes from `tools.bootstrap.layout`, which is where
the stores actually are.
"""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
PLACE = HERE / "ADOPTION-247941.md"

FIXTURE_HEAD = '"$(' + 'git' + ' -C "$SOURCE" rev-parse HEAD)"'

OLD_STEP2 = '''ROOT=/home/sl/baton-runs/two-jobs-<the fresh identity you choose>
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
'''

NEW_STEP2 = '''# NOT under /home/sl/baton-runs. Bound to the pinned snapshot,
# `held_configuration` treats that directory as the checkout and refuses
# mutable deployment state inside it -- see below.
ROOT=/home/sl/baton-instances/two-jobs-<the fresh identity you choose>
SOURCE="$ROOT/fixture-source"

mkdir -p "$SOURCE"
#   ... create the fixture's files, then commit them ...
BASE=''' + FIXTURE_HEAD + '''
```

**THE RUN ROOT MUST BE OUTSIDE THE CHECKOUT BOUNDARY, and this page had it
wrong.** Review 2026-09-23T20:34:15Z composed the shape printed here and the
product refused it by name:

> the configured integration_store at
> `/home/sl/baton-runs/two-jobs-.../db/integration.sqlite3` is inside the
> checkout at `/home/sl/baton-runs`; mutable deployment state belongs outside
> the working tree

`held_configuration` derives "the checkout" from the source that imported it,
so binding the pinned snapshot makes `/home/sl/baton-runs` one — the same rule
the fixture-root section above already documents, which I had applied to the
tests and not to the recipe. `prepare_two_jobs.BOUNDARIES` now refuses such a
root **before anything is written**, and the validator is not weakened.

**The run identity must also be fresh.** `prepare_two_jobs.CONSUMED` names
every root this campaign has spent — each holds other work and is preserved
evidence — and the refusal resolves symlinks first, because a fresh-named
alias pointing into a consumed root walked around the earlier lexical check.

Then bootstrap the instance, through the supported tool:

```sh
PYTHONPATH="$BOUND" "$PY" -B -m tools.bootstrap \\\\
    --inputs "<the deployment inputs document; see v12/STACK.md>" \\\\
    --destination "$ROOT" \\\\
    --distro /home/sl/baton-runs/managed-correction-236087/build/stack/out/distro
```

It writes `$ROOT/bootstrap.json`, `$ROOT/authority-identity.json` and the four
stores under `$ROOT/db/`. **The record is the identity** — the preparation
reads the uuid from it, and an `--authority-uuid` that disagrees is refused
rather than preferred:

```sh
AUTH="$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["authority_uuid"])' "$ROOT/bootstrap.json")"
```
'''

SWAPS = [
    (OLD_STEP2, NEW_STEP2, "step 2"),
    ('    --source "$ROOT/fixture-source" \\\n    --base "$BASE"',
     '    --source "$SOURCE" \\\n    --base "$BASE"', "step 3 source"),
    ('''  3. derives the resolved selections — including each Job's full input
     manifest and its `job_input_identity`, computed from the task bytes just
     written so the manifest's `human_contract` and the worker's
     `task_document` cannot disagree — and writes
     `$ROOT/selections-resolved.json`;''',
     '''  3. derives the resolved selections — including each Job's full input
     manifest and its `job_input_identity`, computed from the task bytes so
     the manifest's `human_contract` and the worker's `task_document` cannot
     disagree — and **validates the whole proposed packet through the
     product** before opening the Authority or composing anything;''',
     "step 3 item 3"),
    ('''**What it does not do**: no container, credential, provider, engine or network
is reached, no Job or control store is opened, and no Git operation is
performed. **Executing the run is step 4 and a separate decision.**''',
     '''**The order is refusals, then effects.** Every refusal above — the boundary,
the run identity, the symlink, the base, the source, the bootstrap record, a
repeat with different bytes, an existing composed target — happens before the
first byte is written. The only thing written before validation is the two
task documents, because the validator OPENS the configured task; they are
never written over differing bytes, and a validation failure leaves exactly
those two files and says so.

**It prints the operands the next two steps take**, from the places this run
actually used: `serve_command` and `status_command` in its receipt. Use those
rather than retyping the templates below — review 2026-09-23T20:34:15Z found
three documents naming three layouts that no reading of `<run root>` could
reconcile.

**What it does not do**: no container, credential, provider, engine or network
is reached, no Job or control store is opened, and no Git operation is
performed. **Executing the run is step 4 and a separate decision.**''',
     "step 3 tail"),
    ('    --deployment "<run root>/deployment.json" \\\n'
     '    --submission "<run root>/submission.json" \\\n'
     '    --job-store "<run root>/jobs.sqlite3" \\\n'
     '    --control-store "<run root>/control.sqlite3" \\',
     '    --deployment "$ROOT/run/deployment.json" \\\n'
     '    --submission "$ROOT/run/submission.json" \\\n'
     '    --job-store "$ROOT/db/jobs.sqlite3" \\\n'
     '    --control-store "$ROOT/db/control.sqlite3" \\', "serve operands"),
    ('BATON_V12_STAGE_EXECUTION_CONFIG="<run root>/deployment.json" \\',
     'BATON_V12_STAGE_EXECUTION_CONFIG="$ROOT/run/deployment.json" \\',
     "the config path"),
    ('    --outcome "<run root>/outcome.json" \\',
     '    --outcome "$ROOT/run/outcome.json" \\', "the outcome path"),
    ('    --store "<run root>/jobs.sqlite3" \\\n'
     '    --incarnation "<a fresh incarnation for this process>" \\\n'
     '    --authority-uuid "<the 32-hex Authority this Job store belongs to>" \\\n'
     '    submit --document "<run root>/submission.json"',
     '    --store "$ROOT/db/jobs.sqlite3" \\\n'
     '    --incarnation "<a fresh incarnation for this process>" \\\n'
     '    --authority-uuid "$AUTH" \\\n'
     '    submit --document "$ROOT/run/submission.json"', "the submit step"),
    ('    --store "<run root>/jobs.sqlite3" \\\n'
     '    --incarnation "<a fresh incarnation for this process>" \\\n'
     '    --authority-uuid "<the same 32-hex Authority>" \\\n'
     '    status --control "<run root>/control.sqlite3"',
     '    --store "$ROOT/db/jobs.sqlite3" \\\n'
     '    --incarnation "<a fresh incarnation for this process>" \\\n'
     '    --authority-uuid "$AUTH" \\\n'
     '    status --control "$ROOT/db/control.sqlite3"', "the inspect step"),
]


def main():
    body = PLACE.read_text(encoding="utf-8")
    if "MUST BE OUTSIDE THE CHECKOUT BOUNDARY" in body:
        raise SystemExit("REFUSED: the recipe is already reconciled")
    for old, new, what in SWAPS:
        if body.count(old) != 1:
            raise SystemExit(
                f"REFUSED: {what} appears {body.count(old)} times, not once")
        body = body.replace(old, new, 1)
    if body.count("71 checks") != 2:
        raise SystemExit(
            f"REFUSED: the page states 71 checks {body.count('71 checks')} "
            f"times, not twice")
    body = body.replace("71 checks", "78 checks")
    PLACE.write_text(body, encoding="utf-8")

    written = PLACE.read_text(encoding="utf-8")
    for absent in ("<run root>", "71 checks", "/home/sl/baton-runs/two-jobs-<"):
        if absent in written:
            raise SystemExit(f"REFUSED: {absent!r} survives in the page")
    for present in ("MUST BE OUTSIDE THE CHECKOUT BOUNDARY",
                    "-m tools.bootstrap", "$ROOT/db/jobs.sqlite3",
                    "$ROOT/db/control.sqlite3", "$ROOT/run/deployment.json",
                    "The order is refusals, then effects", "78 checks"):
        if present not in written:
            raise SystemExit(f"REFUSED: {present!r} is not in the page")
    print("the page names the bootstrap's layout, outside the boundary")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
