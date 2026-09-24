"""Claim-251064: the page says where the preflight runs, and why that matters."""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
PLACE = HERE / "ADOPTION-247941.md"

OLD = '''  3. derives the resolved selections — including each Job's full input
     manifest and its `job_input_identity`, computed from the task bytes so
     the manifest's `human_contract` and the worker's `task_document` cannot
     disagree — and **validates the whole proposed packet through the
     product** before opening the Authority or composing anything;'''

NEW = '''  3. derives the resolved selections — including each Job's full input
     manifest and its `job_input_identity`, computed from the task bytes so
     the manifest's `human_contract` and the worker's `task_document` cannot
     disagree — and **validates the whole proposed packet in the PINNED
     process** before opening the Authority or composing anything, through
     `two_jobs.py --check`, which runs the digest pins, the import provenance
     and the entire composition and writes nothing;'''

OLD_ORDER = '''**The order is refusals, then effects.** Every refusal above — the boundary,
the run identity, the symlink, the base, the source, the bootstrap record, a
repeat with different bytes, an existing composed target — happens before the
first byte is written. The only thing written before validation is the two
task documents, because the validator OPENS the configured task; they are
never written over differing bytes, and a validation failure leaves exactly
those two files and says so.'''

NEW_ORDER = '''**The order is refusals, then effects.** Every refusal above — the boundary,
the run identity, the symlink, the base, the source, the bootstrap record, a
repeat with different bytes, an existing composed target — happens before the
first byte is written. The only thing written before validation is the two
task documents, because the validator OPENS the configured task; they are
never written over differing bytes, and a validation failure leaves exactly
those two files and says so.

**And the validation happens where the composition happens.** Review
2026-09-23T21:06:44Z found the preflight validating in the preparation's own
process — `composed` → `held` → `from tools import stage_execution` →
`held_configuration`, three lines apart — so the `tools` that validated was
whichever one that process had found, and an earlier version of this step had
explicitly tolerated a checkout one. `two_jobs.py --check` now does the whole
preflight in a subprocess with `PYTHONPATH` bound to the pinned source and
`cwd` at the root: the same program, the same environment and the same
working directory as the composition that follows it. The digest pins are
part of that check, so a drifted artifact is refused before any Authority act
rather than after.'''


def swap(body, old, new, what):
    if body.count(old) != 1:
        raise SystemExit(
            f"REFUSED: {what} appears {body.count(old)} times, not once")
    return body.replace(old, new, 1)


def main():
    body = PLACE.read_text(encoding="utf-8")
    if "two_jobs.py --check" in body:
        raise SystemExit("REFUSED: the pinned preflight is already described")
    body = swap(body, OLD, NEW, "the step 3 item")
    body = swap(body, OLD_ORDER, NEW_ORDER, "the order paragraph")
    if body.count("80 checks") != 2:
        raise SystemExit(
            f"REFUSED: the page states 80 checks {body.count('80 checks')} "
            f"times, not twice")
    body = body.replace("80 checks", "83 checks")
    PLACE.write_text(body, encoding="utf-8")

    written = PLACE.read_text(encoding="utf-8")
    for absent in ("80 checks",):
        if absent in written:
            raise SystemExit(f"REFUSED: {absent!r} survives in the page")
    for present in ("two_jobs.py --check",
                    "the validation happens where the composition happens",
                    "83 checks"):
        if present not in written:
            raise SystemExit(f"REFUSED: {present!r} is not in the page")
    print("the page names the pinned preflight")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
