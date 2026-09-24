"""Claim-249551 source corrections. Run once; kept as the record of the edit."""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent


def main():
    place = HERE / "two_jobs.py"
    body = place.read_text(encoding="utf-8")

    # 1. VALIDATE THE SUBMISSION BEFORE IT IS RETURNED.
    body = body.replace(
        '''    return {"deployment.json": deployment,
            "submission.json": submission(''',
        '''    return {"deployment.json": deployment,
            "submission.json": held_submission(submission(''')
    body = body.replace(
        '''                jobs, submission_id=instance["submission_id"],
                policy_digest=instance["policy_digest"])}''',
        '''                jobs, submission_id=instance["submission_id"],
                policy_digest=instance["policy_digest"]))}''')
    body = body.replace(
        '''def held(document, *, checkout=None):''',
        '''def held_submission(document):
    """The PUBLIC reader's own judgment on the document about to be written.

    Review 2026-09-23T17:25:40Z: `composed` accepted an invalid
    `terminal_policy` and the serialized reader rejected it later. A composer
    that writes a document its own reader refuses has moved the failure from
    composition to submission, where an operator meets it instead.

    `owned_submission` is the reader `submit` uses and it takes no store, so
    this is the same judgment without touching one.
    """
    from baton_v12.job_manager.documents import owned_submission
    try:
        owned_submission(document)
    except Exception as failure:                             # noqa: BLE001
        _refuse(f"this composition produced a submission its own public "
                f"reader refuses: {type(failure).__name__}: {failure}")
    return document


def held(document, *, checkout=None):''')

    # 2. BIND THE COMPOSITION TO THE PINNED SOURCE IT WAS CHECKED AGAINST.
    body = body.replace(
        '''    import verify_247941
    held_pins = verify_247941.pins()
    if not held_pins["agree"]:
        _refuse("the selected artifacts no longer match what "
                "ASSESSMENT-249338.md pinned:\\n"
                + json.dumps(held_pins, indent=2, sort_keys=True))''',
        '''    import verify_247941
    held_pins = verify_247941.pins()
    if not held_pins["agree"]:
        _refuse("the selected artifacts no longer match what "
                "ASSESSMENT-249338.md pinned:\\n"
                + json.dumps(held_pins, indent=2, sort_keys=True))
    # AND THE BYTES THAT ANSWERED ARE THE BYTES THAT WERE PINNED. Review
    # 2026-09-23T17:25:40Z: the pin helper checked the snapshot while the
    # process imported the checkout, so a passing check said nothing about
    # what actually composed. `tools` and `baton_v12` must resolve inside the
    # pinned source, which is what `PYTHONPATH="$BOUND:$DOSSIER"` in step 3
    # arranges.
    imported = imported_from(verify_247941.SNAPSHOT)
    if imported:
        _refuse("this composition is bound to the pinned manager source, and "
                "these packages resolved elsewhere:\\n  - "
                + "\\n  - ".join(imported)
                + f"\\nBind PYTHONPATH to {verify_247941.SNAPSHOT} as step 3 "
                  f"of ADOPTION-247941.md prints it.")''')
    body = body.replace(
        '''def held_submission(document):''',
        '''def imported_from(root):
    """Any package that did NOT resolve inside the pinned source."""
    import baton_v12
    import tools
    root = os.path.realpath(str(root))
    held = []
    for module in (tools, baton_v12):
        place = os.path.realpath(module.__file__ or "")
        if os.path.commonpath([place, root]) != root:
            held.append(f"{module.__name__} resolved to {place}")
    return held


def held_submission(document):''')
    place.write_text(body, encoding="utf-8")
    print("two_jobs.py corrected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
