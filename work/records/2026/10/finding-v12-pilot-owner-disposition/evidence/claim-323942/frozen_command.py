"""Drive the FROZEN bundle's `disposition` verb through the whole owner path.

No PYTHONPATH, no checkout on the import path for the binary: the only thing
under test is the installed command. The store, the root and the integration
record are this script's own temporary directory.
"""
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time

ROOT = os.environ.get("W321689_ROOT") or open(
    "/tmp/w321689-frozen-root.txt").read().strip()
BINARY = os.environ.get(
    "W321689_BINARY") or os.path.join(ROOT, "out", "distro",
                                     "baton-v12-stack")
SOURCE = os.environ.get("W321689_SRC") or os.path.join(ROOT, "python", "src")
UUID = "0123456789abcdef0123456789abcdef"
WORK = "0123abcd-W1"
WORKER, REVIEWER, OWNER = "baton.claude", "baton.rvpc", "baton.slaw"
LOCATOR = "operator-quickstart-7f3a91c2"
RECORD = "work/records/2026/10/finding-pilot/INTEGRATION.json"
COMMIT = "433b09d6963ca9789700849b640e242e772b9867"
CANDIDATE = "sha256:" + "2" * 64


def run(*operands, expect=0):
    env = dict(os.environ)
    env.pop("PYTHONPATH", None)
    held = subprocess.run([BINARY, *operands], capture_output=True, text=True,
                          timeout=60, env=env)
    assert held.returncode == expect, (operands, held.returncode, held.stderr)
    return held


def main():
    started = time.monotonic()
    results = []
    with tempfile.TemporaryDirectory(prefix="w321689-frozen-") as place:
        store = os.path.join(place, "authority.sqlite3")
        repo = os.path.join(place, "repo")
        os.makedirs(os.path.join(repo, os.path.dirname(RECORD)))

        # The line up to the human's decision, through the PACKAGE (the
        # authority has no command for publishing: that is a worker's act).
        sys.path.insert(0, SOURCE)
        from baton_v12.authority import Authority, V12

        authority = Authority.create(store, authority_uuid=UUID)
        authority.create_work(WORK, "impl", operation_id="op-create",
                              contract=V12)
        authority.add_route_handler("impl", WORKER)
        scope = authority.project_work(WORK)["scope"]
        for capability in ("verify", "review"):
            authority.grant_capability(REVIEWER, capability, scope=scope)
        for capability in ("approve", "integrate", "close"):
            authority.grant_capability(OWNER, capability, scope=scope)
        authority.bind_dossier(WORK, LOCATOR, operation_id="op-bind")
        mine = authority.session(WORKER).claim(
            {"work_id": WORK, "operation_id": "op-claim"})["assignment"]
        authority.session(WORKER).publish(
            {"expect": mine, "operation_id": "op-pub",
             "proposal_id": "proposal-1", "result_id": "result-1",
             "result_digest": "sha256:" + "1" * 64,
             "candidate_digest": CANDIDATE,
             "input_digest": "sha256:" + "3" * 64,
             "policy_digest": "sha256:" + "4" * 64})
        authority.session(REVIEWER).verify(
            {"proposal_id": "proposal-1", "verification_id": "ver-1",
             "observation": "passed", "operation_id": "op-ver"})
        authority.session(REVIEWER).review(
            {"proposal_id": "proposal-1", "review_id": "rev-1",
             "disposition": "accepted", "operation_id": "op-rev"})
        authority.session(WORKER).end({"expect": mine,
                                       "operation_id": "op-end"})
        generation = authority.policy_generation()
        authority.dispose()

        base = ["--authority-store", store, "--authority-uuid", UUID]

        said = json.loads(run("disposition", "pending", *base, "--work", WORK,
                              "--participant", OWNER).stdout)
        results.append({"what": "pending says approval is due",
                        "owner_action": said["owner_action"],
                        "holds": said["holds"],
                        "locator": said["dossier"]["locator"]})
        assert said["owner_action"] == "approval-due", said
        assert said["holds"] == {"approve": True, "integrate": True,
                                 "close": True}, said

        # A satisfying closure on a green verification and an accepted review
        # alone: REFUSED by the frozen command.
        held = run("disposition", "close", *base, "--participant", OWNER,
                   "--work", WORK, "--outcome", "satisfying",
                   "--rationale", "too early", "--operation-id", "op-early",
                   "--proposal", "proposal-1",
                   "--expect-candidate-digest", CANDIDATE, "--root", repo,
                   expect=2)
        results.append({"what": "satisfying closure before approval refuses",
                        "exit": 2, "says": held.stderr.strip()[:120]})
        assert "approval-due" in held.stderr

        run("disposition", "approve", *base, "--participant", OWNER,
            "--work", WORK, "--proposal", "proposal-1",
            "--expect-candidate-digest", CANDIDATE, "--expect-review", "rev-1",
            "--policy-generation", str(generation), "--approval-id", "app-1",
            "--operation-id", "op-app")
        results.append({"what": "the owner approves", "exit": 0})

        document = {"schema": "baton.v12.human-integration-record/1",
                    "authority_uuid": UUID, "work_id": WORK,
                    "proposal_id": "proposal-1",
                    "candidate_digest": CANDIDATE, "commit": COMMIT,
                    "integrated_by": "Slawomir",
                    "integrated_at": "2026-10-18T13:00:00Z"}
        whole = os.path.join(repo, RECORD)
        with open(whole, "w", encoding="utf-8") as handle:
            json.dump(document, handle, indent=2, sort_keys=True)

        said = json.loads(run(
            "disposition", "integrated", *base, "--participant", OWNER,
            "--work", WORK, "--proposal", "proposal-1",
            "--expect-candidate-digest", CANDIDATE, "--root", repo,
            "--reference", RECORD, "--commit", COMMIT,
            "--integration-id", "int-1", "--operation-id", "op-int",
            "--evidence-operation-id", "op-cite").stdout)
        results.append({"what": "the human integration is recorded",
                        "commit": said["bound"]["commit"],
                        "cited": said["cited"]["reference"],
                        "actor": said["bound"]["actor"]})
        assert said["bound"]["commit"] == COMMIT

        # The record rewritten after it was cited: the satisfying closure
        # refuses, and the Work stays open.
        with open(whole, "a", encoding="utf-8") as handle:
            handle.write("\n")
        held = run("disposition", "close", *base, "--participant", OWNER,
                   "--work", WORK, "--outcome", "satisfying",
                   "--rationale", "delivered", "--operation-id", "op-close",
                   "--proposal", "proposal-1",
                   "--expect-candidate-digest", CANDIDATE, "--root", repo,
                   expect=2)
        results.append({"what": "a rewritten integration record refuses",
                        "exit": 2, "says": held.stderr.strip()[:120]})
        assert "no intact human integration record" in held.stderr

        with open(whole, "w", encoding="utf-8") as handle:
            json.dump(document, handle, indent=2, sort_keys=True)
        said = json.loads(run(
            "disposition", "close", *base, "--participant", OWNER,
            "--work", WORK, "--outcome", "satisfying",
            "--rationale", "delivered", "--operation-id", "op-close",
            "--proposal", "proposal-1", "--expect-candidate-digest", CANDIDATE,
            "--root", repo).stdout)
        results.append({"what": "the selected acceptance closes it",
                        "outcome": said["closed"]["outcome"],
                        "acceptance": said["acceptance"]})
        assert said["closed"]["outcome"] == "satisfying"
        assert said["acceptance"]["human_integration"]["commit"] == COMMIT

        said = json.loads(run("disposition", "pending", *base,
                              "--work", WORK).stdout)
        results.append({"what": "a closed Work owes nothing",
                        "owner_action": said["owner_action"]})
        assert said["owner_action"] == "closed"

    print(json.dumps(
        {"binary": BINARY,
         "binary_sha256": hashlib.sha256(
             open(BINARY, "rb").read()).hexdigest(),
         "boundary": "frozen one-folder bundle; PYTHONPATH removed from the "
                     "command's environment; disposable store, root and "
                     "integration record; no deployment, engine, provider or "
                     "Git command",
         "identity": json.loads(run("identity").stdout),
         "results": results,
         "seconds": round(time.monotonic() - started, 6)},
        indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
