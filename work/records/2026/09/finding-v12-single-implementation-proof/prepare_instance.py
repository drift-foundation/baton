"""Prepare ONE fresh instance's Authority, from ITS OWN selections.

Review 2026-09-23T03:30:58Z R1: `OPERATOR-SUCCESSOR-244216.md` told an operator
to follow `OPERATOR-SUCCESSOR-243284.md`'s step-5a block "with `$SEL` pointing
at this packet's selections" -- but that block HARDCODES the 243284 selections
path and asserts `"single-implementation-243284" in store`, so pointing it at
the 244216 file raises `AssertionError` before `Authority.open` is even
reached. A preparation step that cannot be pointed at the packet it is
documented beside is not a preparation step.

So this is the step, parameterized, and the documents reference it instead of
reprinting a block that only worked for one run.

WHAT IT VALIDATES, AND IT DERIVES RATHER THAN HARDCODES. The freshness marker
is the selections' own `run_id`: every store the instance names must contain
it, and none may name any other run root this campaign has consumed. A helper
carrying a literal run name is exactly the defect above, one release later.

WHAT IT DOES. `create_work`, the two route handlers, the four capability
grants, and `set_policy("canonical_target", base)` -- the acts the earlier
block performed, against the Authority the selections name. Nothing else: it
opens no Job or control store, starts no container, reads no credential and
runs no provider.

IT REPLAYS RATHER THAN REFUSING, and that is MEASURED rather than assumed.
`create_work` is journalled under an operation identity, and this derives that
identity from the run -- `w239528-<run_id>` unless one is given -- so running
the step twice against the same Authority replays the same act and answers the
same Work and scope. A first draft of this file claimed the opposite in its own
docstring; driving it twice showed otherwise, and the claim is corrected here
rather than left as plausible prose.

WHAT REPLAY IS NOT. It is not an adoption of whatever happens to be there: the
operation identity is derived from the selections, so a DIFFERENT packet
pointed at the same Authority performs a different act under a different
identity and is not silently absorbed into this one.
"""
import argparse
import json
import os
import pathlib
import sys

# Every run root this campaign has consumed. A successor's stores may name
# none of them -- the accepted isolation boundary excludes stores holding other
# work, and each of these holds some.
CONSUMED = (
    "managed-correction-236087",
    "single-implementation-239528",
    "single-implementation-success-239528",
    "single-implementation-242687",
)
STORES = ("authority_store", "job_store", "control_store",
          "integration_store")


class PreparationRefusal(Exception):
    """Refused rather than prepared. Never a partial instance's excuse."""


def _refuse(message):
    raise PreparationRefusal(message)


def chosen_from(selections):
    with open(selections, "r", encoding="utf-8") as handle:
        held = json.load(handle)
    if "compose" not in held:
        _refuse(f"{selections} carries no `compose` block")
    return held["compose"]


def _components(place):
    """The path's own components, NORMALIZED.

    Review 2026-09-23T03:42:19Z R2 asks for normalized locations. A substring
    test over a raw string answers the wrong question twice: `/a/b/../<consumed>`
    reads as neither, and a run whose name merely CONTAINS a consumed one would
    match on text rather than on where the file is. Comparing components of a
    normalized absolute path asks where the store actually lives.
    """
    whole = os.path.normpath(os.path.abspath(os.path.expanduser(place)))
    return whole, [one for one in whole.split(os.sep) if one]


def fresh(chosen, *, selections="the selections"):
    """Is this instance this run's own, and nobody else's?

    DERIVED FROM `run_id`, so the check moves with the packet. Answers the
    marker it validated, which is what a caller reports.

    A CONSUMED IDENTITY IS REFUSED UNCONDITIONALLY. Review
    2026-09-23T03:42:19Z R2: the first version exempted a consumed root when
    its name EQUALLED `run_id`, so naming the run after a consumed instance
    let every one of its stores through -- the exemption defeated the check it
    was written into. There is no case where a successor may run against one
    of these: each holds other work and is preserved evidence, and reusing the
    identity is precisely what the grant and Job-identity rules already
    forbid.
    """
    run = chosen.get("run_id")
    if type(run) is not str or not run:
        _refuse(f"{selections} names no run_id, so freshness cannot be checked")
    if run in CONSUMED:
        _refuse(f"{selections} names run_id {run!r}, which is a CONSUMED "
                f"instance: its grant is spent, its stores hold other work "
                f"and its evidence is preserved. A successor takes a new "
                f"identity.")
    instance = chosen.get("instance") or {}
    for member in STORES:
        place = instance.get(member)
        if type(place) is not str or not place:
            _refuse(f"{selections} names no {member}")
        whole, parts = _components(place)
        if run not in parts:
            _refuse(f"{member} {whole!r} does not name this run {run!r} in "
                    f"its own path; a successor's stores are its own")
        for older in CONSUMED:
            if older in parts:
                _refuse(f"{member} {whole!r} lies under {older!r}, which "
                        f"holds other work and is preserved evidence")
    return run


def unresolved(chosen):
    """Every member still marked `<OWNER`, named rather than discovered at
    the first act that needs it."""
    found = []

    def walk(value, path):
        if isinstance(value, dict):
            for name in sorted(value):
                walk(value[name], f"{path}.{name}" if path else name)
        elif isinstance(value, str) and value.startswith("<OWNER"):
            found.append(path)

    walk(chosen, "")
    return found


def prepare(authority, chosen, *, base, operation_id):
    """The acts, against an ALREADY OPEN Authority handle.

    Taking the handle rather than opening one is what lets a disposable
    instance drive this exact function; `main` below opens the one the
    selections name.
    """
    participants = chosen["participants"]
    profile = chosen["instance"]["integration_profile"]
    integrator = profile["integrator_participant"]
    receipts = participants["receipts"]
    work = participants["work_id"]

    authority.create_work(work, "impl", contract="v12-assignment-1",
                          operation_id=operation_id)
    scope = authority.project_work(work)["scope"]
    authority.add_route_handler("impl", participants["implementation"])
    # The review worker is CONFIGURED and never admitted -- `stage_execution`
    # resolves its principal, so it must exist -- and this Job submits no
    # review stage, so `rview` handler registration is not a prerequisite.
    authority.add_route_handler("integration", integrator)
    granted = []
    for who, capability in ((receipts["verification"], "verify"),
                            (receipts["review"], "review"),
                            (receipts["approval"], "approve"),
                            (integrator, "integrate")):
        authority.grant_capability(who, capability, scope=scope)
        granted.append({"participant": who, "capability": capability})
    authority.set_policy("canonical_target", base)
    return {"work_id": work, "scope": scope, "canonical_target": base,
            "route_handlers": {"impl": participants["implementation"],
                               "integration": integrator},
            "granted": granted}


def main(argv=None, *, stream=None):
    stream = sys.stdout if stream is None else stream
    parser = argparse.ArgumentParser(
        prog="prepare_instance",
        description="Prepare one FRESH instance's Authority from its own "
                    "selections. Opens no Job or control store, starts no "
                    "container and runs no provider.")
    parser.add_argument("--selections", required=True,
                        help="the packet's own selections document")
    parser.add_argument("--base", required=True,
                        help="the fixture repository's HEAD, which also "
                             "becomes the Authority's canonical target")
    parser.add_argument("--operation-id", default=None,
                        help="defaults to w239528-<run_id>")
    taken = parser.parse_args(argv)

    chosen = chosen_from(taken.selections)
    run = fresh(chosen, selections=taken.selections)
    still = unresolved(chosen)
    if still:
        _refuse(f"{taken.selections} still carries unresolved owner "
                f"operands: {', '.join(still)}")
    if len(taken.base) != 40 or any(one not in "0123456789abcdef"
                                    for one in taken.base):
        _refuse(f"--base is one full lower-case object name; this is "
                f"{taken.base!r}")

    from baton_v12.authority import Authority

    store = chosen["instance"]["authority_store"]
    if not pathlib.Path(store).exists():
        _refuse(f"{store} does not exist; bootstrap the fresh instance first")
    authority = Authority.open(
        store, expected_authority_uuid=chosen["instance"]["authority_uuid"])
    try:
        prepared = prepare(
            authority, chosen, base=taken.base,
            operation_id=taken.operation_id or f"w239528-{run}")
    finally:
        authority.dispose()
    prepared["run_id"] = run
    prepared["authority_store"] = store
    print(json.dumps(prepared, indent=2, sort_keys=True), file=stream)
    return 0


if __name__ == "__main__":                                   # pragma: no cover
    try:
        raise SystemExit(main())
    except PreparationRefusal as refusal:
        print(f"refused: {refusal}", file=sys.stderr)
        raise SystemExit(2)
