"""Claim-250974: the bootstrap input is derived, and the preflight is whole.

Review 2026-09-23T20:52:13Z, three remaining items:

  * "ADOPTION now names tools.bootstrap, but its required --inputs is still
    `<the deployment inputs document; see v12/STACK.md>`. No file or generator
    supplies that document." So `--emit-bootstrap-inputs` derives it from the
    same ACCEPTED configuration everything else here comes from. A fresh
    install names NO workers and NO jobs -- the tool says so itself -- so the
    document is instance-level only.
  * "main only refuses an existing places['run'] if deployment.json or
    submission.json is present... compose calls two_jobs.main, which refuses
    ANY existing target directory." The preflight now refuses ANY existing
    target, including a symlink or a non-directory, matching the composer.
  * "The composer also checks pins/import provenance only after the
    preparation's Authority acts." `two_jobs.imported_from` now runs in the
    preflight, before anything is written.

AND WHAT THE REAL BOOTSTRAP ANSWERED, measured on a disposable destination
rather than reasoned about: `job   none; no Work, grant or placeholder was
created`. A fresh install creates no Works, so this step's two are not in
competition with any the bootstrap made -- the reconciliation the review asked
for, settled by running the tool.
"""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
PLACE = HERE / "prepare_two_jobs.py"

OLD_LAYOUT_TAIL = '''        "outcome": os.path.join(run_root, "run", "outcome.json"),
    }
'''

NEW_LAYOUT_TAIL = '''        "outcome": os.path.join(run_root, "run", "outcome.json"),
        "bootstrap_inputs": os.path.join(run_root, "bootstrap-inputs.json"),
    }


# THE BOOTSTRAP SCHEMA, and the exact set it accepts. `tools.bootstrap.REQUIRED`
# is this list; `workers` and `jobs` are deliberately NOT here, because an
# installation configures no capacity -- "a worker, a Work, a declared base, a
# canonical target and a producer are supplied together when a Job is created".
BOOTSTRAP_SCHEMA = "baton.v12.stack-bootstrap/1"


def bootstrap_inputs(run_root):
    """The instance document `tools.bootstrap --inputs` takes, DERIVED.

    Review 2026-09-23T20:52:13Z: the page named the tool and left its required
    operand as `<see v12/STACK.md>`, which is another open configuration task
    rather than the derivation the owner selected. Every member below comes
    from the same ACCEPTED configuration as the rest of this preparation.

    A FRESH INSTALL NAMES NO JOBS AND NO WORKERS, and that is the tool's own
    rule rather than a simplification here. Running it on a disposable
    destination answers `job   none; no Work, grant or placeholder was
    created` -- so the two Works this preparation creates are its own, and
    nothing the bootstrap did competes with them.
    """
    return {
        "schema": BOOTSTRAP_SCHEMA,
        "state_root": layout(run_root)["state_root"],
        "checkpoint_profile": ACCEPTED["checkpoint_profile"],
        "integration_profile": dict(ACCEPTED["integration_profile"]),
        "retention_policy_digest": ACCEPTED["retention_policy_digest"],
        "retention_disposition": ACCEPTED["retention_disposition"],
        "pool_generation": ACCEPTED["pool_generation"],
        "policy_generation": ACCEPTED["policy_generation"],
        "receipt_participants": dict(ACCEPTED["receipt_participants"]),
    }
'''

OLD_TARGET = '''    if os.path.exists(places["run"]):
        held = [one for one in ("deployment.json", "submission.json")
                if os.path.exists(os.path.join(places["run"], one))]
        if held:
            _refuse(f"{places['run']!r} already holds {', '.join(held)}; the "
                    f"composer is create-only and would refuse after this "
                    f"step had acted. Nothing was written.")
'''

NEW_TARGET = '''    # THE COMPOSER'S ACTUAL RULE, not a weaker reading of it. Review
    # 2026-09-23T20:52:13Z: this refused only when `deployment.json` or
    # `submission.json` was already there, so an EMPTY target passed the
    # preflight and the composer refused it afterwards -- after the task
    # documents, the selections and the Authority acts. `two_jobs.main` is
    # create-only about the path itself, and so is this.
    if os.path.lexists(places["run"]):
        _refuse(f"{places['run']!r} already exists; the composer is "
                f"create-only about the target path itself, so this would "
                f"refuse after the Authority had been acted on. Nothing was "
                f"written. Select a fresh run root.")

    # AND THE PROVENANCE CHECK THE COMPOSER RUNS, run here instead of after
    # the effects. `imported_from` names any package that did not resolve
    # inside the pinned source.
    if str(HERE) not in sys.path:
        sys.path.insert(0, str(HERE))
    import two_jobs
    strayed = two_jobs.imported_from(SNAPSHOT)
    if strayed:
        _refuse(f"this preparation is not bound to the pinned source: "
                f"{'; '.join(strayed)}. Bind PYTHONPATH to {SNAPSHOT} -- a "
                f"packet composed from the checkout is a different product's "
                f"packet.")
'''

OLD_IMPORT = '''    if str(HERE) not in sys.path:
        sys.path.insert(0, str(HERE))
    import two_jobs
    try:
        two_jobs.composed(document)'''

NEW_IMPORT = '''    try:
        two_jobs.composed(document)'''

OLD_ARGS = '''    parser.add_argument("--operation-prefix", default=None,
                        help="defaults to w247941-<run id>")
    taken = parser.parse_args(argv)
'''

NEW_ARGS = '''    parser.add_argument("--operation-prefix", default=None,
                        help="defaults to w247941-<run id>")
    parser.add_argument("--emit-bootstrap-inputs", action="store_true",
                        help="derive and print the `tools.bootstrap --inputs` "
                             "document for this run root, and do nothing "
                             "else. This runs BEFORE the instance exists, so "
                             "it needs no bootstrap record and performs no "
                             "act of any kind.")
    taken = parser.parse_args(argv)

    if taken.emit_bootstrap_inputs:
        # THE ONE MODE THAT PRECEDES THE INSTANCE. It still refuses a root
        # inside a checkout boundary or under a consumed instance, because an
        # operator who bootstraps into one has already spent the effort.
        held = fresh(os.path.abspath(os.path.expanduser(taken.run_root)),
                     taken.run_id or os.path.basename(
                         os.path.abspath(taken.run_root).rstrip(os.sep)))
        print(json.dumps(bootstrap_inputs(held), indent=2, sort_keys=True),
              file=stream)
        return 0
'''


def swap(body, old, new, what):
    if body.count(old) != 1:
        raise SystemExit(
            f"REFUSED: {what} appears {body.count(old)} times, not once")
    return body.replace(old, new, 1)


def main():
    body = PLACE.read_text(encoding="utf-8")
    if "def bootstrap_inputs(" in body:
        raise SystemExit("REFUSED: the bootstrap derivation is already there")
    body = swap(body, OLD_LAYOUT_TAIL, NEW_LAYOUT_TAIL, "the layout tail")
    body = swap(body, OLD_TARGET, NEW_TARGET, "the target preflight")
    body = swap(body, OLD_IMPORT, NEW_IMPORT, "the composer import")
    body = swap(body, OLD_ARGS, NEW_ARGS, "the argument block")
    PLACE.write_text(body, encoding="utf-8")

    written = PLACE.read_text(encoding="utf-8")
    for present in ("def bootstrap_inputs(", "--emit-bootstrap-inputs",
                    "os.path.lexists(places[\"run\"])",
                    "two_jobs.imported_from(SNAPSHOT)"):
        if present not in written:
            raise SystemExit(f"REFUSED: {present!r} is not in the file")
    compile(written, str(PLACE), "exec")
    print("bootstrap inputs derived; preflight now whole and provenance-bound")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
