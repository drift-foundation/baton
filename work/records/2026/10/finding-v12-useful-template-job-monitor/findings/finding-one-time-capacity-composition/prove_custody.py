#!/usr/bin/env python3
"""The custody guard over the PUBLIC commands, repeated and in both orders.

review-2026-10-27T22-59-54Z, the whole of the required correction:

    "Test entire public compose/proof invocation with both opt-ins, asserting
    all bound candidate/proposal/input bytes and file inventory remain
    unchanged, not only a preflight subcall. Include repeated invocation and
    variants so run order cannot silently select proposal content."

So this runs the PUBLIC commands as an operator runs them -- as subprocesses,
unmodified, with their real argv -- twice each and in both opt-in orders, and
digests the whole child directory and the published proposal inventory around
all of it. `prove_capacity.py`'s own step 11 guards one invocation of itself;
this guards the commands as a SET, because the defect being corrected was
exactly an ordering effect: whichever variant ran last won, silently.

WHAT IT ASSERTS:

  * every file under the child directory is byte-identical afterwards, and
    the file inventory itself is identical -- nothing appeared or vanished;
  * the published proposal set still matches its own `INVENTORY.json`, which
    is checked by `proposed_grants.py --verify`, a read-only command;
  * the bound digests in the claim binding still hold;
  * the two success forms `CLEAN-START.md` publishes run VERBATIM against the
    two sets published in this record, so the operator page cannot drift from
    the commands;
  * and the three custody REFUSALS fire: publishing a variant over a set
    composed for another task, publishing a default set over a variant, and
    binding one set to the other's task.

It writes nothing into the child directory. Its own scratch is `mkdtemp` under
the scratch root and is retained.
"""
import hashlib
import json
import os
import pathlib
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import capacity                                              # noqa: E402
import proposed_grants                                       # noqa: E402

PYTHON = sys.executable or "python3"


def tree(place):
    """Every ordinary file under a directory, by digest. `__pycache__` out."""
    held = {}
    for one in sorted(pathlib.Path(place).rglob("*")):
        if one.is_file() and "__pycache__" not in one.parts:
            held[str(one.relative_to(place))] = hashlib.sha256(
                one.read_bytes()).hexdigest()
    return held


def ran(argv, *, cwd=HERE):
    done = subprocess.run([PYTHON] + argv, cwd=str(cwd), capture_output=True,
                          text=True, timeout=1800)
    return {"argv": argv, "exit": done.returncode,
            "said": " ".join((done.stdout + done.stderr).split())[-300:]}


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    scratch = pathlib.Path(argv[0] if argv else capacity.SCRATCH)
    if not scratch.is_dir():
        print("refused: no scratch root at " + str(scratch), file=sys.stderr)
        return 2
    mine = pathlib.Path(tempfile.mkdtemp(prefix="w367232-custody-",
                                         dir=str(scratch)))
    opening = tree(HERE)
    inventory_before = (proposed_grants.PLACE
                        / proposed_grants.INVENTORY).read_text()

    # A WELL-FORMED IDENTITY FOR THE COMPOSE RUNS. `compose` writes nothing
    # and only derives paths, so no instance has to exist for it; the two
    # runs differ ONLY in their opt-ins, which is the point.
    uuid = "a1b2c3d4" * 4
    destination = str(mine / "never-created")
    variant = str(mine / "format-variant")

    runs = []
    # The variant is published ONCE, explicitly, into a directory this run
    # owns -- which is the shape the correction requires. Publishing it a
    # second time must be accepted (same set, same task) and must not change
    # a byte.
    runs.append(ran(["proposed_grants.py", "--proposed-format",
                     "--into", variant]))
    runs.append(ran(["proposed_grants.py", "--proposed-format",
                     "--into", variant]))
    variant_after_first = tree(variant)

    # BOTH OPT-INS, IN BOTH ORDERS, TWICE. If run order could select proposal
    # content, these would disagree with each other or with `opening`.
    order = [
        ["capacity.py", "compose", "--minted-uuid", uuid,
         "--destination", destination, "--proposed-grants"],
        ["capacity.py", "compose", "--minted-uuid", uuid,
         "--destination", destination, "--grants-from", variant,
         "--proposed-format"],
    ]
    for pair in (order, list(reversed(order)), order):
        for one in pair:
            runs.append(ran(one))

    # AND THE TWO FORMS `CLEAN-START.md` PUBLISHES, VERBATIM, against the two
    # sets published in this record. review-2026-10-27T23-11-07Z found the
    # page advertising a combination that refuses; these run the corrected
    # examples exactly as written, so the page cannot drift from the commands
    # without this failing.
    documented = [
        ["capacity.py", "compose", "--minted-uuid", uuid,
         "--destination", destination, "--proposed-grants"],
        ["capacity.py", "compose", "--minted-uuid", uuid,
         "--destination", destination,
         "--grants-from", "proposed-grants-format", "--proposed-format"],
    ]
    for one in documented:
        runs.append(ran(one))

    # The whole public proof, twice, unmodified.
    runs.append(ran(["prove_capacity.py", "--scratch", str(scratch)]))
    runs.append(ran(["prove_capacity.py", "--scratch", str(scratch)]))

    # And the read-only verification of the canonical set.
    runs.append(ran(["proposed_grants.py", "--verify"]))

    # -- the two refusals this correction exists to guarantee ---------------
    refusals = {
        "publishing_the_variant_over_the_canonical_set":
            ran(["proposed_grants.py", "--proposed-format"]),
        "binding_the_canonical_set_to_the_format_task":
            ran(["capacity.py", "compose", "--minted-uuid", uuid,
                 "--destination", destination, "--proposed-grants",
                 "--proposed-format"]),
        "publishing_the_default_set_over_the_variant":
            ran(["proposed_grants.py", "--into", variant]),
    }

    closing = tree(HERE)
    appeared = sorted(set(closing) - set(opening))
    vanished = sorted(set(opening) - set(closing))
    rewritten = sorted(name for name in set(opening) & set(closing)
                       if opening[name] != closing[name])
    inventory_after = (proposed_grants.PLACE
                       / proposed_grants.INVENTORY).read_text()

    failures = []
    for one in runs:
        if one["exit"] != 0:
            failures.append("a public command failed: %s -> %s"
                            % (" ".join(one["argv"]), one["said"]))
    for name, one in refusals.items():
        if one["exit"] == 0:
            failures.append("%s was NOT refused" % name)
    if appeared or vanished or rewritten:
        failures.append("the child directory changed: appeared %s; vanished "
                        "%s; rewritten %s" % (appeared, vanished, rewritten))
    if inventory_before != inventory_after:
        failures.append("the published inventory changed")
    if variant_after_first != tree(variant):
        failures.append("republishing the same variant changed its bytes")

    # AND THE CLAIM BINDINGS STILL HOLD, read from the records themselves.
    bindings = {}
    for record in sorted((HERE / "evidence").glob("claim-*/BINDING.json")):
        held = json.loads(record.read_text())
        # BOTH BINDING SHAPES. `/2` carries one `proposed_grants.members`;
        # `/3` carries two named sets under `proposal_sets`, and a checker
        # that knew only the first reported "no drift" for a binding it had
        # not actually looked at -- found by reading its own answer, which
        # said `proposal_members: 0` for claim-369298.
        proposals = dict(held.get("proposed_grants", {}).get("members", {}))
        for name, one in sorted(held.get("proposal_sets", {}).items()):
            if isinstance(one, dict) and one.get("members"):
                for member, each in one["members"].items():
                    proposals[name + ":" + member] = each
        # AND BOTH PATH FORMS. `/2` records repository-relative paths and
        # `/3` recorded them relative to this child directory. A checker that
        # assumed one reported every member of the other as drifted -- which
        # is how this was found, not by assuming. Neither form is wrong; a
        # verifier that only understood one was.
        drift = []
        for member, one in sorted(proposals.items()):
            where = [capacity.REPOSITORY / one["path"], HERE / one["path"]]
            found = [place for place in where if place.is_file()]
            if not found:
                drift.append(member + " (no such file)")
            elif hashlib.sha256(
                    found[0].read_bytes()).hexdigest() != one["file_sha256"]:
                drift.append(member)
        bindings[str(record.relative_to(HERE))] = {
            "proposal_members": len(proposals), "drifted": drift}
        if drift:
            failures.append("%s: proposal bytes drifted for %s"
                            % (record.name, ", ".join(drift)))

    answer = {"schema": "baton.v12.custody-proof/1",
              "effects": {"created": [str(mine)], "removed": [],
                          "retained": [str(mine)]},
              "wrote_into_the_child_directory": appeared,
              "files_digested": len(opening),
              "public_runs": runs,
              "refusals": refusals,
              "appeared": appeared, "vanished": vanished,
              "rewritten": rewritten,
              "published_inventory_unchanged":
                  inventory_before == inventory_after,
              "repeated_publication_is_byte_identical":
                  variant_after_first == tree(variant),
              "claim_bindings": bindings,
              "documented_examples_run_verbatim": [
                  " ".join(one) for one in documented],
              "what_this_adds": "prove_capacity's step 11 guards ONE "
                                "invocation of itself. This guards the "
                                "public commands as a SET, run twice and in "
                                "both opt-in orders, because the defect "
                                "being corrected was an ordering effect: "
                                "whichever variant ran last won, silently.",
              "failures": failures,
              "ok": not failures}
    json.dump(answer, sys.stdout, indent=1, sort_keys=True, default=str)
    sys.stdout.write("\n")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
