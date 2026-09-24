"""Claim-250974: the bootstrap input is a command, and replay is described.

Review 2026-09-23T20:52:13Z: "its required --inputs is still `<the deployment
inputs document; see v12/STACK.md>`. No file or generator supplies that
document... Owner250730 expressly selected derivation of technical operands and
exact setup commands, not another open configuration task." And: "ADOPTION
still says running it twice replays the same Works. Current main deliberately
refuses an exact completed repeat at the target check."

Both corrected here. The inputs document is derived by the same step that uses
it, the bootstrap command is complete including the runtime seam, and the
replay paragraph now distinguishes what `create_work` does from what the
command does.
"""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
PLACE = HERE / "ADOPTION-247941.md"

OLD_BOOTSTRAP = '''Then bootstrap the instance, through the supported tool:

```sh
PYTHONPATH="$BOUND" "$PY" -B -m tools.bootstrap \\
    --inputs "<the deployment inputs document; see v12/STACK.md>" \\
    --destination "$ROOT" \\
    --distro /home/sl/baton-runs/managed-correction-236087/build/stack/out/distro
```

It writes `$ROOT/bootstrap.json`, `$ROOT/authority-identity.json` and the four
stores under `$ROOT/db/`. **The record is the identity** — the preparation
reads the uuid from it, and an `--authority-uuid` that disagrees is refused
rather than preferred:
'''

NEW_BOOTSTRAP = '''Then bootstrap the instance. Its input document is **derived by the same step
that uses it**, so there is no separate configuration task:

```sh
PYTHONPATH="$BOUND:$DOSSIER" "$PY" -B "$DOSSIER/prepare_two_jobs.py" \\
    --run-root "$ROOT" --source "$SOURCE" --base "$BASE" \\
    --emit-bootstrap-inputs > "$ROOT/bootstrap-inputs.json"

PYTHONPATH="$BOUND" "$PY" -B -m tools.bootstrap \\
    --inputs "$ROOT/bootstrap-inputs.json" \\
    --destination "$ROOT" \\
    --no-repositories \\
    --distro /home/sl/baton-runs/managed-correction-236087/build/stack/out/distro
```

`--emit-bootstrap-inputs` runs before the instance exists, needs no record and
performs no act; it still refuses a root inside a checkout boundary or under a
consumed instance, because an operator who bootstraps into one has already
spent the effort. The document it prints carries only what
`tools.bootstrap.REQUIRED` names — the state root, the checkpoint profile, the
integration profile, the retention policy and disposition, the two generations
and the receipt participants — all from the same accepted configuration as the
rest of this packet.

**`--distro` is the one seam.** The tool refuses without a built runtime —
*"installing into … needs a built runtime; name it with `--distro`"* — and
copies the pinned distribution into `$ROOT/distro`. That copy is the only part
of step 2 this dossier's checks perform rather than reason about; no scheduler
is started and no repository is prepared (`--no-repositories`).

**A fresh install creates no Work**, which is why the preparation's two are
unambiguous. That is the tool's own account of itself, not an inference:

> `job   none; no Work, grant or placeholder was created`

It writes `$ROOT/bootstrap.json`, `$ROOT/authority-identity.json`,
`$ROOT/deployment.json` (the empty-capacity instance configuration) and the
four stores under `$ROOT/db/`. **The record is the identity** — the preparation
reads the uuid from it, and an `--authority-uuid` that disagrees is refused
rather than preferred:
'''

OLD_REPLAY = '''**Running it twice is same-identity replay, not adoption of whatever is
there.** `create_work` is journalled under an act identity derived from the
run, so a repeat answers the same two Works — and a Work that already exists
under somebody ELSE's act is refused rather than absorbed. That was measured
rather than assumed: pointing the step at a Work the witness fixture had
already minted answered `Work '0000000a-W1' already exists`.'''

NEW_REPLAY = '''### Running it twice

Two different things, and this page used to say only the first:

  * **The Authority act replays.** `create_work` is journalled under an act
    identity derived from the run, so calling it again answers the same two
    Works — and a Work that already exists under somebody ELSE's act is
    refused rather than absorbed. Measured rather than assumed: pointing the
    step at a Work the witness fixture had minted answered
    `Work '0000000a-W1' already exists`.
  * **The COMMAND does not replay; it refuses, early.** A completed run has a
    composed target, and the composer is create-only about that path, so a
    second invocation is refused **before** the task documents, the
    selections or the Authority are touched. An invocation with different
    operands — a different base, say — is refused the same way, by comparing
    the bytes it would write against the bytes already there.

So a repeat leaves the first run's packet exactly as it was. To prepare
again, select a fresh run root; that is the same rule as everywhere else in
this campaign, and there is no in-place re-preparation.'''


def swap(body, old, new, what):
    if body.count(old) != 1:
        raise SystemExit(
            f"REFUSED: {what} appears {body.count(old)} times, not once")
    return body.replace(old, new, 1)


def main():
    body = PLACE.read_text(encoding="utf-8")
    if "--emit-bootstrap-inputs" in body:
        raise SystemExit("REFUSED: the bootstrap inputs step is already there")
    body = swap(body, OLD_BOOTSTRAP, NEW_BOOTSTRAP, "the bootstrap block")
    body = swap(body, OLD_REPLAY, NEW_REPLAY, "the replay paragraph")
    if body.count("78 checks") != 2:
        raise SystemExit(
            f"REFUSED: the page states 78 checks {body.count('78 checks')} "
            f"times, not twice")
    body = body.replace("78 checks", "80 checks")
    PLACE.write_text(body, encoding="utf-8")

    written = PLACE.read_text(encoding="utf-8")
    for absent in ("<the deployment inputs document", "78 checks",
                   "Running it twice is same-identity replay"):
        if absent in written:
            raise SystemExit(f"REFUSED: {absent!r} survives in the page")
    for present in ("--emit-bootstrap-inputs", "--no-repositories",
                    "no Work, grant or placeholder was created",
                    "### Running it twice",
                    "The COMMAND does not replay; it refuses, early",
                    "80 checks"):
        if present not in written:
            raise SystemExit(f"REFUSED: {present!r} is not in the page")
    print("the bootstrap input is a command and replay is described")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
