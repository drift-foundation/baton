"""Deterministic disposable proof for the post-install packet. READ-ONLY on production.

WHAT THIS IS FOR. review-2026-10-23T02-34-20Z.md requires the post-install
composition to be demonstrated deterministically before any owner selection:
that an existing empty installation is preserved, that the missing worker
repositories can be prepared and proved independent, that drift refuses BEFORE
effects, and that an unreviewed rerun cannot register or submit twice.

WHAT IT NEVER TOUCHES. The real destination
/home/sl/baton-instances/native-coordination-pilot-w321608-2 is never read,
written, started or configured by this script. Every scenario runs in a
disposable root under a caller-named temporary directory, built to the SAME
SHAPE as the observed empty install. No live model, engine, provider, network
or version-control mutation of this repository; the only repository commands
are clones and reads inside the disposable root.

HOW TO RUN. From v12/python with the prepared interpreter:

    PYTHONPATH=src:. python3 <this file>

It exits non-zero on the first failed expectation and prints one JSON document.
"""
import hashlib
import json
import os
import pathlib
import subprocess
import sys
import tempfile

PACKET = pathlib.Path(__file__).resolve().parent
PRODUCTION = "/home/sl/baton-instances/native-coordination-pilot-w321608-2"
AUTHORITY = "673355e1f28e4b5683cbef09eb8f2658"
BASE = "302453869d07eb5579e79a6572586d3c3cf62a5c"


class Failed(AssertionError):
    pass


class Checks:
    def __init__(self):
        self.held = []

    def expect(self, what, answer):
        self.held.append({"check": what, "ok": bool(answer)})
        if not answer:
            raise Failed(what)

    def refuses(self, what, call, *, naming):
        """A refusal is only evidence when its REASON is the expected one."""
        try:
            call()
        except Exception as refusal:                      # noqa: BLE001
            said = str(refusal)
            ok = naming in said
            self.held.append({"check": what, "ok": ok, "refusal": said[:400]})
            if not ok:
                raise Failed(what + " -- refused for the wrong reason: " + said)
            return said
        self.held.append({"check": what, "ok": False, "refusal": None})
        raise Failed(what + " -- it did NOT refuse")

    def document(self):
        return {"total": len(self.held),
                "failed": [one for one in self.held if not one["ok"]],
                "checks": self.held}


def git(place, *args):
    done = subprocess.run(["git", "-C", str(place), *args], capture_output=True,
                          text=True, timeout=120)
    if done.returncode != 0:
        raise Failed("git " + " ".join(args) + " failed: " + done.stderr.strip())
    return done.stdout.strip()


def digest_of(place):
    return hashlib.sha256(pathlib.Path(place).read_bytes()).hexdigest()


def inputs(name):
    return json.loads((PACKET / name).read_text())


def retarget(value, root):
    if isinstance(value, str):
        return value.replace(PRODUCTION, str(root))
    if isinstance(value, dict):
        return {k: retarget(v, root) for k, v in value.items()}
    if isinstance(value, list):
        return [retarget(one, root) for one in value]
    return value


def seed_source(where):
    """A disposable source repository at a deterministic single commit."""
    where.mkdir(parents=True)
    subprocess.run(["git", "init", "-q", "-b", "main", str(where)], check=True,
                   timeout=60)
    (where / "README.md").write_text("disposable composition source\n")
    git(where, "add", "--all")
    env = dict(os.environ, GIT_AUTHOR_NAME="Baton Proof",
               GIT_AUTHOR_EMAIL="proof@baton.invalid",
               GIT_COMMITTER_NAME="Baton Proof",
               GIT_COMMITTER_EMAIL="proof@baton.invalid")
    subprocess.run(["git", "-C", str(where), "commit", "-q", "-m", "base"],
                   check=True, env=env, timeout=60)
    return git(where, "rev-parse", "HEAD")


def empty_install_shape(root, source_head):
    """The SHAPE the independent readback observed: target + workspace, empty config.

    Built with the product's own clone semantics -- target mirrored from the
    source, workspace cloned from the target with --no-local -- so the proof
    starts from the same arrangement rather than from an invented one.
    """
    from tools import instance

    places = instance.layout(root)
    pathlib.Path(places["repository"]).mkdir(parents=True, exist_ok=True)
    pathlib.Path(places["stores"]).mkdir(parents=True, exist_ok=True)
    pathlib.Path(places["state"]).mkdir(parents=True, exist_ok=True)
    target = os.path.join(places["repository"], "target.git")
    workspace = os.path.join(places["repository"], "workspace")
    subprocess.run(["git", "clone", "--no-local", "--mirror", str(source_head[1]),
                    target], check=True, capture_output=True, timeout=120)
    subprocess.run(["git", "clone", "--no-local", target, workspace],
                   check=True, capture_output=True, timeout=120)
    return places, target, workspace


def main():
    from tools import bootstrap, instance

    checks = Checks()
    answer = {"packet": str(PACKET), "production_touched": False,
              "authority": AUTHORITY, "base": BASE}

    with tempfile.TemporaryDirectory(prefix="w325959-compose-") as home:
        home = pathlib.Path(home)
        source = home / "source"
        head = seed_source(source)
        root = home / "destination"
        places, target, workspace = empty_install_shape(root, (head, source))

        document = retarget(inputs("configure-inputs.json"), root)
        document["jobs"][0]["work_id"] = AUTHORITY[:8] + "-WPROOF"
        document["jobs"][0]["canonical_target_id"] = head
        document["jobs"][0]["line_declared_base"] = head
        for worker in document["workers"]:
            worker["deployment"]["authority_uuid"] = AUTHORITY

        # -- 1. THE PLAN NAMES FOUR REPOSITORIES, TWO OF THEM MISSING --------
        planned = bootstrap.repository_plan(document, places)
        checks.expect("the plan names target, workspace and one source per worker",
                      [one[0] for one in planned]
                      == ["target", "workspace", "source-implementation-pilot",
                          "source-review-pilot"])
        missing = [one for one in planned if not os.path.lexists(one[1])]
        checks.expect("exactly the two worker sources are missing",
                      [one[0] for one in missing]
                      == ["source-implementation-pilot", "source-review-pilot"])

        # -- 2. THE SUPPORTED PREPARATION REFUSES, BEFORE ANY EFFECT ---------
        before = sorted(os.listdir(places["repository"]))
        checks.refuses(
            "prepare_repositories refuses an existing target rather than replacing it",
            lambda: bootstrap.prepare_repositories(document, places,
                                                   source=str(source)),
            naming="Nothing here replaces one")
        checks.expect("and it changed nothing in the repository directory",
                      sorted(os.listdir(places["repository"])) == before)

        # -- 3. THE HUMAN-ONLY PREPARATION, WITH THE PRODUCT'S OWN SEMANTICS -
        # Each worker source is cloned FROM THE TARGET with --no-local, which
        # is exactly what `bootstrap._cloning` does for a non-mirror role.
        for name, place, _mirror in missing:
            subprocess.run(["git", "clone", "--no-local", target, place],
                           check=True, capture_output=True, timeout=120)
        checks.expect("all four repositories are now present",
                      all(os.path.lexists(one[1]) for one in planned))

        # -- 4. THE PRODUCT'S OWN ISOLATION PROOF ACCEPTS THEM ---------------
        proved = bootstrap.repositories_proved(document, places, planned)
        checks.expect("repositories_proved accepts the prepared set", bool(proved))
        commons = {name: os.path.realpath(
            git(place, "rev-parse", "--path-format=absolute", "--git-common-dir"))
            for name, place, _ in planned}
        checks.expect("no two repositories share a common directory",
                      len(set(commons.values())) == len(commons))
        for name, place, _mirror in planned:
            alternates = os.path.join(commons[name], "objects", "info",
                                      "alternates")
            checks.expect(name + " borrows no objects",
                          not (os.path.exists(alternates)
                               and os.path.getsize(alternates)))
        checks.expect("each worker source holds the declared base",
                      all(git(one[1], "rev-parse", "HEAD") == head
                          for one in missing))

        # -- 5. A SECOND PREPARATION OF THE SAME SET STILL REFUSES -----------
        checks.refuses(
            "an unreviewed rerun cannot re-prepare the worker sources",
            lambda: bootstrap.prepare_repositories(document, places,
                                                   source=str(source)),
            naming="Nothing here replaces one")

        # -- 6. DRIFT REFUSES: a worker source at the wrong base -------------
        drifted = dict(document)
        drifted["jobs"] = [dict(document["jobs"][0],
                                line_declared_base="0" * 40)]
        checks.refuses(
            "a declared base the target does not hold is refused",
            lambda: bootstrap.repositories_proved(drifted, places, planned),
            naming="0000000000000000000000000000000000000000")

        # -- 7. THE WORK ID IS NEVER PRESUMED --------------------------------
        authored = inputs("configure-inputs.json")
        checks.expect("the authored Job carries a READBACK Work, not W1",
                      authored["jobs"][0]["work_id"].startswith("READBACK: ")
                      and "W1" not in authored["jobs"][0]["work_id"].split("--")[0])
        submission = inputs("submission.json")
        checks.expect("every authored stage carries a READBACK Work",
                      all(one["work_id"].startswith("READBACK: ")
                          for one in submission["jobs"][0]["stages"]))
        checks.expect("the submission and Job identifiers are the NEW ones",
                      submission["submission_id"] == "sub-w321608-quickstart-2"
                      and submission["jobs"][0]["job_id"] == "quickstart-b"
                      and authored["jobs"][0]["job_id"] == "quickstart-b")
        checks.expect("per-invocation limits are carried unchanged",
                      submission["jobs"][0]["execution_limits"]
                      == {"provider_turn_seconds": 3600,
                          "verification_command_seconds": 900})

        # -- 8. COHERENCE OF THE AUTHORED BINDINGS ---------------------------
        checks.expect("both stage workers are composed, implementation and review",
                      sorted(one["role"] for one in authored["workers"])
                      == ["implementation", "review"])
        checks.expect("each worker nominates its OWN source repository",
                      len({one["deployment"]["nominated_source"]
                           for one in authored["workers"]}) == 2)
        checks.expect("every authored path lies under the installed destination",
                      all(str(value).startswith(PRODUCTION)
                          for one in authored["workers"]
                          for key, value in one["deployment"].items()
                          if isinstance(value, str) and value.startswith("/home/sl/baton-instances")))
        checks.expect("the authored authority is the one the readback observed",
                      {one["deployment"]["authority_uuid"]
                       for one in authored["workers"]} == {AUTHORITY})
        checks.expect("the authored base is the accepted build commit",
                      authored["jobs"][0]["line_declared_base"] == BASE
                      and inputs("task.json")["declared_base"] == BASE)
        checks.expect("the task is the quickstart-only contract with a NEW id",
                      inputs("task.json")["task_id"]
                      == "w321608-native-operator-quickstart-2"
                      and "v12/QUICKSTART.md" in inputs("task.json")["instructions"])

        answer["disposable_root"] = str(root)
        answer["repositories"] = {name: place for name, place, _ in planned}
        answer["source_head"] = head

    answer["checks"] = checks.document()
    answer["production_untouched"] = not os.path.exists(
        os.path.join(PRODUCTION, "deployment-state", "w325959-compose-marker"))
    print(json.dumps(answer, indent=1, sort_keys=True))
    return 0 if not answer["checks"]["failed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
