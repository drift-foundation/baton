"""The TRANSITION from the old staged preparation to the corrected helper.

OWNER REROUTE 312403. The reviewed recovery failed at its first command: `bind`
refuses `correction_packet.py` because it CHANGED since the retained stage
manifest was written. That refusal is correct -- `bind` refuses drift rather
than re-signing it -- and the recovery proposal simply omitted the step that
makes the transition legitimate. This proves the transition instead of asserting
it, starting from the OLD manifest and an EXISTING installation rather than from
a freshly staged fixture.

WHAT IS REPRODUCED, AND HOW FAITHFULLY. The deployed
`<destination>/prepared.json` binds `correction_packet.py` at the digest
`stage` measured under claim 311743; the corrected helper digests differently,
and NOTHING ELSE has moved -- the staged product tree is byte-identical and the
supervisor and the descriptor supplier still match. So this trace builds a
disposable installation, then sets its retained manifest's helper digest to THE
REAL HISTORICAL ONE read from the deployed document, which is exactly the state
the owner's run was in. No digest is invented and none is re-signed afterwards.

WHAT IT THEN PROVES, in order: `bind` refuses; the recovery -- `stage` into a
FRESH destination, `prepare-work`, `bind`, `check` -- succeeds over the SAME
installation and the SAME staged tree; the old destination's documents are
byte-identical afterwards; the instance was not re-bootstrapped; and the
recovered packet actually runs `baseline.prepare`.

Nothing deployed is written. The deployed manifest is READ, once, for the
historical digest. Run it directly; it prints one JSON evidence document.
"""
import json
import os
import shutil
import sys
import tempfile

import staged_bootstrap_trace as trace
import correction_packet as packets

DOSSIER = trace.DOSSIER
INTERPRETER = trace.INTERPRETER
CLAIM = 312411
# THE DEPLOYED MANIFEST THE OWNER'S RECOVERY MET. Read-only, and the only thing
# outside the temporary root this program touches.
DEPLOYED_PREPARED = ("/home/sl/baton-instances/"
                     "managed-correction-309356-packet-311743/prepared.json")
HELPER = "correction_packet.py"


def _read(path):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def _digests(place):
    """Every document in a destination, by digest -- the evidence that must not
    move while the recovery runs."""
    return {name: packets.digest_of(os.path.join(place, name))
            for name in sorted(os.listdir(place))
            if os.path.isfile(os.path.join(place, name))}


def historical_helper_digest():
    """The digest the OLD stage recorded, read from the deployed document."""
    held = _read(DEPLOYED_PREPARED)
    found = (held.get("preparation_modules") or {}).get(HELPER)
    trace._held(isinstance(found, str) and len(found) == 64,
                "the deployed manifest binds no digest for " + HELPER)
    trace._held(found != packets.digest_of(os.path.join(DOSSIER, HELPER)),
                "the deployed manifest already binds the CURRENT helper, so "
                "there is no transition to prove")
    return found


def stale_the_manifest(destination, digest):
    """Put the OLD helper digest back into the retained manifest.

    This is the reproduction, and it is the only write to any manifest here:
    the recovery below never edits one. `stage` is what re-records digests, and
    that is the whole point of the transition.
    """
    path = os.path.join(destination, "prepared.json")
    held = _read(path)
    was = held["preparation_modules"][HELPER]
    held["preparation_modules"][HELPER] = digest
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(json.dumps(held, indent=2, sort_keys=True) + "\n")
    return {"manifest": path, "module": HELPER, "was": was, "now": digest}


def packet_command(argv, *, staged, cwd):
    return trace._run([INTERPRETER, "-B",
                       os.path.join(DOSSIER, "correction_packet.py")] + argv,
                      tree=staged, cwd=cwd)


def transition(root):
    evidence = {"schema": "baton.recovery-transition/1", "claim": CLAIM,
                "answering": "owner reroute 312403",
                "disposable_root": root, "docker": "not used",
                "providers": "not run",
                "deployed_writes": 0,
                "deployed_reads": [DEPLOYED_PREPARED]}

    # 1 -- THE OLD PREPARATION, built the way the owner's was: stage, install,
    # the Authority acts, bind, check. This is the "existing installation".
    # STOPPED WHERE THE OWNER'S RUN STOPPED: through `check`, with the
    # supervisor never reaching `prepare`. That is the state the deployed
    # installation is in -- REPLAY-SAFETY-312166 measured it with the product's
    # own readers -- and it matters here, because
    # `configure_context_storage` pins the workspace root's device and inode
    # inside its signature, so an installation that HAS registered cannot have
    # those roots re-made.
    first = trace.trace(root, prepare=False)
    evidence["existing_installation"] = {
        "instance": first["bootstrap"]["argv"][
            first["bootstrap"]["argv"].index("--destination") + 1],
        "bootstrap_returncode": first["bootstrap"]["returncode"],
        "staged_file_count": first["stage"]["file_count"],
        "recovery_steps_then": [one["step"] for one in first["recovery"]],
        "baseline_prepare_then": first["baseline_prepare"],
    }
    selections = os.path.join(root, "selections.json")
    chosen = packets.held_selections(selections)
    staged = first["stage"]["staged_root"]
    old_destination = os.path.join(root, "packet")
    instance = chosen["instance_root"]
    record = os.path.join(instance, "bootstrap.json")

    # 2 -- THE STATE THE OWNER'S RECOVERY WAS IN: a retained manifest that
    # predates the corrected helper.
    historical = historical_helper_digest()
    evidence["reproduced"] = stale_the_manifest(old_destination, historical)
    before = {"old_destination": _digests(old_destination),
              "bootstrap_record": packets.digest_of(record),
              "staged_tree": {name: packets.digest_of(
                  os.path.join(staged, name))
                  for name in sorted(packets._source_files(staged))}}

    # 3 -- AND `bind` REFUSES, which is the owner's failure.
    done = packet_command(["bind", "--selections", selections,
                           "--destination", old_destination,
                           "--claim", str(CLAIM), "--provenance",
                           os.path.join(DOSSIER, "PROVENANCE-309356.json")],
                          staged=staged, cwd=root)
    said = (done.stdout + done.stderr).strip()
    evidence["bind_over_the_old_manifest"] = {
        "returncode": done.returncode,
        "refusal": said.splitlines()[-1] if said else "",
        "names_the_module": HELPER in said,
        "refuses_rather_than_re_signing": "refuses drift rather than "
                                          "re-signing" in said,
    }
    trace._held(done.returncode != 0,
                "`bind` accepted a manifest that predates the helper")

    # 4 -- THE RECOVERY: `stage` into a FRESH destination, then the rest. The
    # old destination is left exactly as it is, the instance is NOT
    # re-installed, and no digest is edited by hand.
    fresh = os.path.join(root, "packet-recovered")
    steps = []
    for name, argv in (
            ("stage", ["stage", "--selections", selections,
                       "--destination", fresh, "--claim", str(CLAIM),
                       "--provenance", os.path.join(DOSSIER,
                                                    "PROVENANCE-309356.json")]),
            ("prepare-work", ["prepare-work", "--selections", selections,
                              "--destination", fresh]),
            ("bind", ["bind", "--selections", selections,
                      "--destination", fresh, "--claim", str(CLAIM),
                      "--provenance", os.path.join(DOSSIER,
                                                   "PROVENANCE-309356.json")]),
            ("check", ["check", "--packet",
                       os.path.join(fresh, "packet.json")])):
        done = packet_command(argv, staged=staged, cwd=root)
        said = (done.stdout + done.stderr).strip()
        steps.append({"step": name, "returncode": done.returncode,
                      "last_line": said.splitlines()[-1] if said else ""})
        trace._held(done.returncode == 0,
                    "the recovery step `" + name + "` failed:\n" + said)
    recovered = _read(os.path.join(fresh, "prepared.json"))
    evidence["recovery"] = {
        "destination": fresh,
        "steps": steps,
        "bootstrap_re_run": False,
        "helper_digest_now_recorded":
            recovered["preparation_modules"][HELPER],
        "equals_the_corrected_helper":
            recovered["preparation_modules"][HELPER]
            == packets.digest_of(os.path.join(DOSSIER, HELPER)),
        "staged_file_count": recovered["staged_source"]["file_count"],
    }

    # 5 -- WHAT DID NOT MOVE. The old evidence, the installation and the
    # staged tree are all byte-identical.
    after = {"old_destination": _digests(old_destination),
             "bootstrap_record": packets.digest_of(record),
             "staged_tree": {name: packets.digest_of(os.path.join(staged, name))
                             for name in sorted(packets._source_files(staged))}}
    evidence["preserved"] = {
        "old_destination_unchanged":
            before["old_destination"] == after["old_destination"],
        "old_destination_documents": sorted(after["old_destination"]),
        "instance_record_unchanged":
            before["bootstrap_record"] == after["bootstrap_record"],
        "staged_tree_unchanged":
            before["staged_tree"] == after["staged_tree"],
        "staged_tree_file_count": len(after["staged_tree"]),
    }
    for what, held in sorted(evidence["preserved"].items()):
        if what.endswith("_unchanged"):
            trace._held(held, "the recovery moved something it must preserve: "
                        + what)

    # 6 -- AND THE RECOVERED PACKET RUNS. `baseline.prepare` over the SAME
    # installation, with the recovered packet.
    evidence["baseline_prepare_after_recovery"] = trace.prepare_once(
        fresh, os.path.join(fresh, "packet.json"), cwd=root)
    evidence["operational_finding"] = {
        "what": "once `baseline.prepare` has committed, the workspace root's "
                "DEVICE AND INODE are pinned inside the context-storage "
                "signature -- `configure_context_storage` adds that root to "
                "its excluded set -- so a workspace directory that is deleted "
                "and re-made is a DIFFERENT root to the journal and a second "
                "`prepare` is refused: \"already recorded with a different "
                "kind or signature\".",
        "how_it_was_found": "this trace hit it by re-using the negative leg "
                            "that removes the workspace store, then asking "
                            "`prepare` again",
        "why_it_does_not_affect_this_recovery": "the deployed installation has "
            "registered NOTHING -- REPLAY-SAFETY-312166 records both product "
            "readers refusing -- so its roots have never been pinned. The "
            "recovery creates them once, with `bind`, and never removes them.",
        "what_it_forbids": "deleting or re-making `run/workspaces` or "
                           "`run/private-contexts` on an installation whose "
                           "`prepare` has committed. That is a fresh instance, "
                           "not a repair.",
    }
    return evidence


def main():
    root = tempfile.mkdtemp(prefix="recovery-transition-")
    keep = "--keep" in sys.argv[1:]
    written = None
    if "--evidence" in sys.argv:
        written = sys.argv[sys.argv.index("--evidence") + 1]
    try:
        evidence = transition(root)
    finally:
        if not keep:
            shutil.rmtree(root, ignore_errors=True)
    evidence["disposable_root_removed"] = not keep
    body = json.dumps(evidence, indent=2, sort_keys=True) + "\n"
    if written:
        with open(written, "w", encoding="utf-8") as handle:
            handle.write(body)
    print(body, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
