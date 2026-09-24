"""Claim-251064: the preflight runs in the PINNED process, before the effects.

Review 2026-09-23T21:06:44Z: "Its rationale says tools only answers in the
later composer subprocess. That is false: main calls two_jobs.composed(document)
before the Authority acts; composed calls held; held imports `from tools import
stage_execution` and calls held_configuration IN PROCESS."

That is exactly right and my rationale was wrong. I reasoned about where the
composer runs and never followed `composed -> held -> from tools import
stage_execution`, which is three lines away. So the package I explicitly
tolerated was the one validating the packet, and under the suite's own imports
that was the checkout's.

THE FIX IS NOT A STRICTER FILTER. Filtering is what produced the wrong claim.
The whole validation preflight now runs where the operator's own composition
runs -- a subprocess with `PYTHONPATH` bound to the pinned source and `cwd` at
the root -- through `two_jobs.py --check`, which performs the digest pins, the
import provenance and the full composition and writes nothing. So the bytes
that validate are the bytes that compose, by construction rather than by
argument, and the digest pins are checked at the same pre-effect boundary the
review asks for.
"""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
COMPOSER = HERE / "two_jobs.py"
PLACE = HERE / "prepare_two_jobs.py"

OLD_ARGS = '''    parser.add_argument("--selections", required=True)
    parser.add_argument("--into", required=True,
                        help="the run root to write the packet into; it is "
                             "created and must not already exist")
    chosen = parser.parse_args(argv)'''

NEW_ARGS = '''    parser.add_argument("--selections", required=True)
    parser.add_argument("--into", default=None,
                        help="the run root to write the packet into; it is "
                             "created and must not already exist")
    parser.add_argument("--check", action="store_true",
                        help="run every check this composition runs -- the "
                             "digest pins, the import provenance and the "
                             "whole composition -- and WRITE NOTHING. A "
                             "caller that needs the validation to happen "
                             "where the composition happens runs this first.")
    chosen = parser.parse_args(argv)
    if not chosen.check and chosen.into is None:
        parser.error("--into is required unless --check is given")'''

OLD_WRITE = '''    documents = composed(selections)
    into = pathlib.Path(chosen.into)'''

NEW_WRITE = '''    documents = composed(selections)
    if chosen.check:
        # NOTHING IS WRITTEN. The pins, the provenance and the composition
        # have all run in THIS process, which is the pinned one.
        print(json.dumps({"_checked": sorted(documents),
                          "_pins_agree": True, "_written": []},
                         indent=2, sort_keys=True))
        return 0
    into = pathlib.Path(chosen.into)'''

OLD_PREFLIGHT = '''    # AND THE PROVENANCE CHECK THE COMPOSER RUNS, run here instead of after
    # the effects. `imported_from` names any package that did not resolve
    # inside the pinned source.
    if str(HERE) not in sys.path:
        sys.path.insert(0, str(HERE))
    import two_jobs
    strayed = two_jobs.imported_from(SNAPSHOT)
    # WHAT THIS CAN TRUTHFULLY REFUSE, and what it can only report. The
    # VALIDATION below runs IN THIS PROCESS, so the `baton_v12` that answers
    # it has to be the pinned one; that is a refusal. `tools` is imported by
    # the COMPOSER, which runs as a subprocess with `PYTHONPATH` bound
    # explicitly and `cwd` at the root, and which runs this same check itself
    # -- so this process resolving `tools` from a checkout it happens to be
    # sitting in says nothing about the packet. It is recorded rather than
    # refused, because refusing it would be this step failing a caller for a
    # condition that does not reach the artifact.
    validating = [one for one in strayed if one.startswith("baton_v12 ")]
    if validating:
        _refuse(f"the validator that checks this packet is not the pinned "
                f"one: {'; '.join(validating)}. Bind PYTHONPATH to "
                f"{SNAPSHOT} -- a packet held by the checkout's rules is a "
                f"different product's packet.")
'''

NEW_PREFLIGHT = '''    # THE PACKET THIS STEP BUILDS IS BUILT WITH THE PINNED CONTRACTS. The
    # manifests and their `job_input_identity` are computed in THIS process,
    # so `baton_v12` here has to be the selected one. The VALIDATION does not
    # happen here at all any more -- see below.
    if str(HERE) not in sys.path:
        sys.path.insert(0, str(HERE))
    import two_jobs
    strayed = two_jobs.imported_from(SNAPSHOT)
    building = [one for one in strayed if one.startswith("baton_v12 ")]
    if building:
        _refuse(f"this preparation derives digests with contracts that are "
                f"not the pinned ones: {'; '.join(building)}. Bind PYTHONPATH "
                f"to {SNAPSHOT}.")
'''

OLD_VALIDATE = '''    # THE PRODUCT VALIDATES THE WHOLE PROPOSED PACKET, in process, BEFORE the
    # Authority is opened or anything is composed. `two_jobs.composed` builds
    # the deployment and the submission and runs `held_configuration` over
    # them. Review 2026-09-23T20:34:15Z met this refusal only after the
    # Authority acts had already run.
    try:
        two_jobs.composed(document)
    except Exception as failure:                             # noqa: BLE001
        _refuse(f"the product refuses this packet, and nothing beyond the two "
                f"task documents under {places['tasks']!r} was written: "
                f"{failure}")
'''

NEW_VALIDATE = '''    # THE WHOLE PREFLIGHT RUNS WHERE THE COMPOSITION RUNS. Review
    # 2026-09-23T21:06:44Z: validating in THIS process meant `held` imported
    # `tools` from wherever this process found it, and I had explicitly
    # tolerated that. `two_jobs.py --check` performs the digest pins, the
    # import provenance and the entire composition in a subprocess bound to
    # the pinned source, and writes nothing -- so the bytes that validate are
    # the bytes that compose, by construction rather than by argument, and
    # the pins are checked before any Authority act.
    #
    # The selections it reads are written to a TEMPORARY path, because the
    # real one is an effect this step has not earned yet.
    import tempfile
    handle, staged = tempfile.mkstemp(prefix="two-jobs-check-", suffix=".json")
    try:
        with os.fdopen(handle, "wb") as writing:
            writing.write(raw_selections)
        answer = _composer(["--selections", staged, "--check"])
    finally:
        os.unlink(staged)
    if answer.returncode != 0:
        _refuse(f"the pinned product refuses this packet, and nothing beyond "
                f"the two task documents under {places['tasks']!r} was "
                f"written:\\n{(answer.stderr or answer.stdout).strip()}")
'''

OLD_COMPOSE = '''def compose(document_path, into, *, stream):
    """The packet, through the SHIPPED composer rather than a second path."""
    answer = subprocess.run(
        [sys.executable, "-B", str(HERE / "two_jobs.py"),
         "--selections", document_path, "--into", into],
        capture_output=True, text=True, timeout=600, cwd=os.sep,
        env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1",
                 PYTHONPATH=os.pathsep.join([SNAPSHOT, str(HERE)])))
    print(answer.stdout, end="", file=stream)
    if answer.returncode != 0:
        _refuse(f"the composer refused this packet:\\n{answer.stderr.strip()}")
    return {"into": into, "stdout": answer.stdout.strip().splitlines()}
'''

NEW_COMPOSE = '''def _composer(arguments):
    """The shipped composer, in a process bound to the PINNED source.

    One place builds this invocation, so the preflight and the composition
    cannot drift apart: `--check` and the real write run the same program with
    the same environment and the same working directory.
    """
    return subprocess.run(
        [sys.executable, "-B", str(HERE / "two_jobs.py"), *arguments],
        capture_output=True, text=True, timeout=600, cwd=os.sep,
        env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1",
                 PYTHONPATH=os.pathsep.join([SNAPSHOT, str(HERE)])))


def compose(document_path, into, *, stream):
    """The packet, through the SHIPPED composer rather than a second path."""
    answer = _composer(["--selections", document_path, "--into", into])
    print(answer.stdout, end="", file=stream)
    if answer.returncode != 0:
        _refuse(f"the composer refused this packet:\\n{answer.stderr.strip()}")
    return {"into": into, "stdout": answer.stdout.strip().splitlines()}
'''


def swap(place, body, old, new, what):
    if body.count(old) != 1:
        raise SystemExit(
            f"REFUSED: {what} appears {body.count(old)} times in {place}, "
            f"not once")
    return body.replace(old, new, 1)


def main():
    body = COMPOSER.read_text(encoding="utf-8")
    if "--check" not in body:
        body = swap("two_jobs.py", body, OLD_ARGS, NEW_ARGS, "the arguments")
        body = swap("two_jobs.py", body, OLD_WRITE, NEW_WRITE, "the write")
        COMPOSER.write_text(body, encoding="utf-8")
        compile(body, str(COMPOSER), "exec")

    body = PLACE.read_text(encoding="utf-8")
    if "_composer(" in body:
        raise SystemExit("REFUSED: the pinned preflight is already applied")
    body = swap(PLACE.name, body, OLD_PREFLIGHT, NEW_PREFLIGHT, "the preflight")
    body = swap(PLACE.name, body, OLD_VALIDATE, NEW_VALIDATE, "the validation")
    body = swap(PLACE.name, body, OLD_COMPOSE, NEW_COMPOSE, "the composer call")
    PLACE.write_text(body, encoding="utf-8")

    written = PLACE.read_text(encoding="utf-8")
    if "two_jobs.composed(document)" in written:
        raise SystemExit("REFUSED: the in-process validation survives")
    for present in ("def _composer(", '"--check"', "tempfile.mkstemp"):
        if present not in written:
            raise SystemExit(f"REFUSED: {present!r} is not in the file")
    compile(written, str(PLACE), "exec")
    print("the preflight runs in the pinned process, before the effects")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
