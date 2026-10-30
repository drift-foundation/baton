#!/usr/bin/env python3
"""Produce the phase-1 mint document `COMMANDS.md` §4 step 1 consumes.

Review 2026-10-28T00-49-31Z: *"COMMANDS.md:229–243 describes `$MINT` but
supplies neither its full concrete selected document nor a command producing
it. The only actual MINT operations are variable declaration and bootstrap
consumption. Referring to STACK.md or a differently rooted example leaves the
operator reconstructing an authorized preparation input."*

It did, and this is the producer. One command, concrete selected values,
destination-derived paths, **no `workers`, no `jobs` and no authority
identity** — because `bootstrap` mints the identity and refuses an input that
names one (`bootstrap.SUPERSEDED`).

DERIVED FROM THE PHASE-2 COMPOSITION, NOT WRITTEN A SECOND TIME. The accepted
child's `capacity.compose` already builds this deployment's top-level members
— checkpoint profile, integration profile, integration target and workspace,
retention identity and disposition, generations, owner participant and receipt
participants — from their named sources. Phase 1 is **that same document minus
`workers` and `jobs`**, so this asks `compose` for it and strips the two
deferred members rather than restating a dozen values that could then disagree
with the install they precede. Restating them is exactly the drift this
campaign has been correcting.

THE THROWAWAY IDENTITY, DECLARED. `compose` requires a 32-hex identity before
it will build anything, and phase 1 exists precisely because none has been
minted yet. So a declared throwaway is passed, the two uuid-bearing members are
dropped, and the result is then **proved** to contain that throwaway nowhere —
by searching the serialized document for it. If it ever appeared, this refuses
rather than emitting a document with a fabricated identity in it.

IT DOES NOT OVERWRITE. A path that already exists is refused by name: an
operator's existing mint input may be the one an instance was installed from,
and silently replacing it is the custody mistake the child's record already
carries an incident about.

    python3 mint_inputs.py --print                     # read-only, writes nothing
    python3 mint_inputs.py --into <path>               # refuses an existing path
    python3 mint_inputs.py --into <path> --destination <dest>

Nothing here installs, builds, clones, starts anything, reaches an engine,
provider or credential, or touches an existing instance.
"""
import argparse
import hashlib
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
CHILD = HERE / "findings" / "finding-one-time-capacity-composition"
if str(CHILD) not in sys.path:
    sys.path.insert(0, str(CHILD))

import capacity                                              # noqa: E402

# A DECLARED STAND-IN, never an identity. 32 hex because `compose` validates
# the shape; `document()` proves it does not survive into what it emits.
THROWAWAY = "0" * 32

# What phase 1 must NOT carry. `bootstrap.DEFERRED` is exactly
# ("jobs", "workers") and an input naming `authority_uuid` is refused.
DEFERRED = ("workers", "jobs")


class Refused(Exception):
    """Something this producer will not do, with the reason."""


def document(destination=capacity.DESTINATION):
    """The phase-1 document for `destination`. Reads only; writes nothing."""
    composed = capacity.compose(THROWAWAY, destination=destination)
    held = json.loads(json.dumps(composed["document"]))
    dropped = {}
    for member in DEFERRED:
        if member in held:
            dropped[member] = len(held.pop(member))
    # THE ONE MEMBER PHASE 1 HAS AND PHASE 2 DOES NOT. The destination-form
    # install takes the destination as `--destination`, so the phase-2
    # document carries no `state_root`; the mint form takes no destination
    # operand at all, so the document has to name it. Set here, from the same
    # destination every derived path above came from.
    held["state_root"] = str(destination)
    body = json.dumps(held, indent=1, sort_keys=True) + "\n"
    if THROWAWAY in body or "authority_uuid" in body:
        raise Refused(
            "the phase-1 document would carry an authority identity, which "
            "`bootstrap` refuses and this producer will not emit. Nothing "
            "was written.")
    if held.get("state_root") != str(destination):
        raise Refused("the composed state_root is %r and the destination is "
                      "%r" % (held.get("state_root"), str(destination)))
    return held, body, dropped


def write(into, destination=capacity.DESTINATION):
    """Emit it. REFUSES a path that already exists."""
    place = pathlib.Path(into)
    if place.exists():
        raise Refused(
            "%s already exists. This producer never replaces an operator's "
            "mint input -- the instance installed from it may be the one it "
            "describes. Name a fresh path." % place)
    held, body, dropped = document(destination)
    place.parent.mkdir(parents=True, exist_ok=True)
    place.write_text(body)
    return held, body, dropped, place


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--destination", default=capacity.DESTINATION)
    parser.add_argument("--into", default=None,
                        help="a path that must NOT already exist")
    parser.add_argument("--print", action="store_true", dest="printing",
                        help="read-only: show the document and write nothing")
    taken = parser.parse_args(argv)
    if not (taken.printing or taken.into):
        print("refused: name --into <path> to produce it, or --print to see "
              "it without writing", file=sys.stderr)
        return 2
    try:
        if taken.printing:
            held, body, dropped = document(taken.destination)
            place = None
        else:
            held, body, dropped, place = write(taken.into, taken.destination)
    except (Refused, capacity.Refused) as refusal:
        print("refused: " + str(refusal), file=sys.stderr)
        return 2
    answer = {
        "schema": "baton.v12.mint-inputs/1",
        "command": "print" if taken.printing else "write",
        "effects": {"wrote": [] if place is None else [str(place)],
                    "created": [], "removed": []},
        "destination": taken.destination,
        "document": held,
        "document_sha256": hashlib.sha256(body.encode()).hexdigest(),
        "bytes": len(body.encode()),
        "deferred_to_phase_2": dropped,
        "carries_no_authority_identity": True,
        "derived_from": "the accepted child's capacity.compose, minus "
                        "workers and jobs -- so phase 1 and phase 2 cannot "
                        "disagree about this deployment's top-level members",
        "throwaway_identity_used_to_derive_it": THROWAWAY,
        "proved_absent_from_the_output": True,
        "next": "bootstrap --inputs <this file>, with no --destination and no "
                "--distro: that is the mint form",
    }
    if taken.printing:
        answer["read_only"] = True
    json.dump(answer, sys.stdout, indent=1, sort_keys=True, default=str)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
