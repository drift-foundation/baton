"""Deterministic proof for the corrected revision-4 preparation. W325959.

Answers `review-2026-10-24T02-35-41Z.md` R1-R3. Every case that matters here
drives the thing the previous proof asserted ABOUT instead of exercising:

  R1 the operator's workspace command is run against the ACTUAL emitted
     `generated/preparation-readback.json`, not against an assumed shape;
  R2a a VALID edit to a packet document before loading must refuse -- the
     previous test changed the expectation rather than the document, which
     is why it could not see the defect;
  R2b a DIFFERENT otherwise-admissible selected bundle must refuse, because
     the bundle that is verified has to be the bundle that is used;
  R3  a source that is not a repository, and one at another revision, must
     both refuse before the mint; and the declared base, the cloned target
     and the recorded source must be one commit.

NOTHING REAL IS INSTALLED. Every apply runs against a disposable root with a
simulated repository runner and a stub bundle, so what is established is
composition, ordering, identity and refusal -- not that a real clone, a real
runtime or a real provider turn succeeds.
"""
import hashlib
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import time

PACKET = pathlib.Path(__file__).resolve().parent
ACCEPTED = PACKET.parent / "fresh3-358443"
ROOT = PACKET.parents[5]
sys.path[:0] = [str(ROOT / "v12" / "python" / "src"),
                str(ROOT / "v12" / "python"), str(ACCEPTED), str(PACKET)]
os.environ.setdefault("BATON_V12_STACK_TEST_ROOT", "/var/tmp")

import fresh5                                               # noqa: E402

CHECKS = []


class Done:
    def __init__(self, stdout="", returncode=0, stderr=""):
        self.stdout, self.returncode, self.stderr = stdout, returncode, stderr


def runner(argv, **named):
    """The accepted proof's SIMULATED repository tool, carried verbatim.

    Restated rather than imported because `fresh3-358443/prove.py` is a
    script whose whole revision-3 proof runs at import time.
    """
    argv = list(argv)
    if len(argv) > 1 and argv[1] == "clone":
        where = pathlib.Path(argv[-1])
        where.mkdir(parents=True, exist_ok=False)
        (where / ".simulated-git" / "objects" / "info").mkdir(parents=True)
        return Done()
    if len(argv) > 3 and argv[3] == "rev-parse":
        if "--git-common-dir" in argv:
            return Done(str(pathlib.Path(argv[2]) / ".simulated-git"))
        return Done(fresh5.COMMIT)
    return Done()


def stub_bundle(where, mark=b"sim\n"):
    """A bundle satisfying `admit`'s identity checks. SIMULATED, not a build.

    `mark` makes two stubs that are both admissible but NOT the same bytes,
    which is what the selected-bundle case needs.
    """
    where.mkdir(parents=True)
    command = where / "baton-v12-stack"
    command.write_text("#!/bin/sh\ncat <<I\n" + json.dumps(
        {"frozen": True,
         "schema_assets": {"agent-session-1.0": 1, "worker-control-1.0": 1},
         "native_rpds": str(where / "rpds.so")}) + "\nI\n")
    command.chmod(0o755)
    (where / "rpds.so").write_bytes(mark)
    return where


def ok(what, answer, **extra):
    CHECKS.append(dict({"check": what, "outcome": bool(answer)}, **extra))
    return answer


def refuses(what, call, naming, *, root=None, accepting=None):
    """`accepting` widens the refusal to the PRODUCT's own class, for the
    cases the product itself is the right thing to refuse."""
    try:
        call()
        return ok(what, False, detail="it did not refuse")
    except (accepting or ()) + (fresh5.Refused,) as refusal:
        said = str(refusal)
        made = root is not None and pathlib.Path(root).exists()
        return ok(what, naming in said and not made, detail=said[:240],
                  destination_exists=made)
    except Exception as failure:                             # noqa: BLE001
        return ok(what, False,
                  detail=f"{type(failure).__name__}: {failure}"[:240])


def staged(home, root, name="packet"):
    """The packet retargeted to a disposable root, with recomputed pins."""
    where = pathlib.Path(home, name)
    where.mkdir(parents=True)
    for one in fresh5.PACKET_PINS:
        (where / one).write_text(
            (PACKET / one).read_text().replace(fresh5.DESTINATION, str(root)))
    pins = {one: "sha256:" + hashlib.sha256(
        (where / one).read_bytes()).hexdigest() for one in fresh5.PACKET_PINS}
    return where, pins


def simulated(home, mark=b"sim\n", name="distro"):
    """A stub bundle, plus THE REAL SOURCE used read-only.

    No repository is created here. Standing policy forbids mutating
    repository operations anywhere, a disposable fixture included, so the
    source operand is the real tree and the only thing asked of it is its
    revision -- a read. Nothing is ever cloned from it either: the clone
    goes through the injected simulated runner below.
    """
    bundle = stub_bundle(pathlib.Path(home, name), mark)
    return bundle, _manifest(bundle), fresh5.SOURCE


def _manifest(bundle):
    from tools import instance

    return instance.manifest(str(bundle))


def _reads_only():
    """Every repository verb the shipped entrypoint names is a read."""
    import ast

    mutating = {"init", "add", "commit", "checkout", "switch", "merge",
                "rebase", "reset", "clean", "push", "fetch", "pull", "tag",
                "branch", "stash", "apply", "am", "cherry-pick", "restore",
                "mv", "rm", "clone", "worktree", "gc", "prune"}
    verbs = set()
    tree = ast.parse((PACKET / "fresh5.py").read_text())
    for node in ast.walk(tree):
        if not isinstance(node, ast.List):
            continue
        words = [one.value for one in node.elts
                 if isinstance(one, ast.Constant) and isinstance(one.value,
                                                                 str)]
        if words and words[0].endswith("git"):
            verbs.update(words[1:])
    return bool(verbs) and not (verbs & mutating)


def _source_commit(source):
    ran = subprocess.run(["git", "-C", str(source), "rev-parse", "HEAD"],
                         capture_output=True, text=True)
    return ran.stdout.strip() if ran.returncode == 0 else None


# -- the shipped pins are the real digests of the real documents -------------

def the_shipped_pins_are_real():
    for name, want in fresh5.PACKET_PINS.items():
        ok(f"the literal pin for {name} is the real digest of the real "
           f"document",
           want == "sha256:" + hashlib.sha256(
               (PACKET / name).read_bytes()).hexdigest())
    ok("the literal pin for the accepted helper is its real digest",
       fresh5.ACCEPTED_PINS["fresh.py"] == "sha256:" + hashlib.sha256(
           (ACCEPTED / "fresh.py").read_bytes()).hexdigest())
    # AND THE DECLARED BASE IS THE RECORDED SOURCE. R3.
    task = json.loads((PACKET / "task.json").read_text())
    configured = json.loads((PACKET / "configure-inputs.json").read_text())
    bases = {task["declared_base"]} | {
        one["line_declared_base"] for one in configured["jobs"]} | {
        one["canonical_target_id"] for one in configured["jobs"]}
    ok("the declared base, the canonical target and the recorded source are "
       "ONE commit", bases == {fresh5.COMMIT}, bases=sorted(bases))
    ok("and that commit is the one the real source is at",
       _source_commit(fresh5.SOURCE) == fresh5.COMMIT)


# -- R2a: a valid edit must refuse -------------------------------------------

def an_edited_document_refuses():
    home = tempfile.mkdtemp(prefix="w325959-r5-edit-")
    root = pathlib.Path(home, "destination")
    where, pins = staged(home, root)
    bundle, held, source = simulated(home)

    # A VALID EDIT -- still legal JSON, still a usable task, different bytes.
    task = json.loads((where / "task.json").read_text())
    task["instructions"] = task["instructions"] + "\nAnd one more thing.\n"
    (where / "task.json").write_text(json.dumps(task, indent=1,
                                                sort_keys=True) + "\n")
    refuses("a VALID edit to a packet document refuses before the mint",
            lambda: fresh5.prepare(str(root), where, apply=True,
                                   bundle=bundle, source=source,
                                   runner=runner, pins=pins,
                                   bundle_digest=held["digest"],
                                   bundle_files=held["files"],
                                   commit=_source_commit(source)),
            "is not the reviewed one", root=root)
    ok("and the shipped entrypoint carries LITERAL pins rather than hashing "
       "its own documents at import",
       "hashlib.sha256(" not in
       (PACKET / "fresh5.py").read_text().split("PACKET_PINS = {")[1]
       .split("}")[0])


# -- R2b: the verified bundle is the used bundle -----------------------------

def another_bundle_refuses():
    home = tempfile.mkdtemp(prefix="w325959-r5-bundle-")
    root = pathlib.Path(home, "destination")
    where, pins = staged(home, root)
    first, held, source = simulated(home, b"sim-one\n", "distro-one")
    second = stub_bundle(pathlib.Path(home, "distro-two"), b"sim-two\n")
    other = _manifest(second)
    ok("the two stub bundles are both admissible and NOT the same bytes",
       held["digest"] != other["digest"],
       first=held["digest"][:16], second=other["digest"][:16])
    refuses("selecting a DIFFERENT admissible bundle while expecting the "
            "first refuses",
            lambda: fresh5.prepare(str(root), where, apply=True,
                                   bundle=second, source=source,
                                   runner=runner, pins=pins,
                                   bundle_digest=held["digest"],
                                   bundle_files=held["files"],
                                   commit=_source_commit(source)),
            "the SELECTED bundle", root=root)
    refuses("and selecting another bundle against the SHIPPED expectation "
            "refuses too",
            lambda: fresh5.prepare(str(root), where, apply=False,
                                   bundle=second, source=source,
                                   runner=runner, pins=pins,
                                   commit=_source_commit(source)),
            "the SELECTED bundle", root=root)


# -- R3: the source revision is enforced -------------------------------------

def source_drift_refuses():
    home = tempfile.mkdtemp(prefix="w325959-r5-source-")
    root = pathlib.Path(home, "destination")
    where, pins = staged(home, root)
    bundle, held, source = simulated(home)

    plain = pathlib.Path(home, "plain")
    (plain / "v12").mkdir(parents=True)
    refuses("an unversioned directory carrying v12 refuses before the mint",
            lambda: fresh5.prepare(str(root), where, apply=True,
                                   bundle=bundle, source=plain,
                                   runner=runner, pins=pins,
                                   bundle_digest=held["digest"],
                                   bundle_files=held["files"]),
            "not a repository", root=root)
    # THE REAL REPOSITORY, held to a revision it is not at. Read-only.
    refuses("a real repository at ANOTHER revision refuses before the mint",
            lambda: fresh5.prepare(str(root), where, apply=True,
                                   bundle=bundle, source=source,
                                   runner=runner, pins=pins,
                                   bundle_digest=held["digest"],
                                   bundle_files=held["files"],
                                   commit="0" * 40),
            "silently changes what is cloned", root=root)
    ok("and the revision is obtained by a READ -- the shipped entrypoint's "
       "only repository call is rev-parse, with no mutating verb",
       _reads_only())
    refuses("and a source with no v12 tree refuses",
            lambda: fresh5.prepare(str(root), where, apply=False,
                                   bundle=bundle, source=pathlib.Path(home),
                                   runner=runner, pins=pins,
                                   bundle_digest=held["digest"],
                                   bundle_files=held["files"]),
            "carries no v12 tree", root=root)


# -- R1: the operator's command, against the emitted document ----------------

def the_apply_and_the_operator_command():
    from tools import stage_execution

    home = tempfile.mkdtemp(prefix="w325959-r5-apply-")
    root = pathlib.Path(home, "destination")
    where, pins = staged(home, root)
    bundle, held, source = simulated(home)

    answer = fresh5.prepare(str(root), where, apply=True, bundle=bundle,
                            source=source, runner=runner, pins=pins,
                            bundle_digest=held["digest"],
                            bundle_files=held["files"],
                            commit=_source_commit(source))
    prepared = answer["preparation"]
    uuid = prepared["authority_uuid"]
    ok("the apply mints an authority and reads it back", len(uuid) == 32,
       authority=uuid)
    ok("the Work carries THIS authority's prefix and is not instance 3's",
       prepared["work"] == uuid[:8] + "-W1"
       and prepared["work"] != "5a8fa4b4-W1", work=prepared["work"])
    ok("both stages, one binding, four repositories",
       prepared["installed_workers"] == ["implementation", "review"]
       and prepared["installed_job_bindings"] == 1
       and len(prepared["repositories"]) == 4,
       repositories=prepared["repositories"])
    installed = json.loads((root / "deployment.json").read_text())
    ok("the installed configuration is one this build accepts",
       stage_execution.held_configuration(installed) is not None)
    submission = prepared["submission_document"]
    ok("the submission keeps 3600/900 and names neither quickstart-c nor "
       "5a8fa4b4-W1",
       submission["jobs"][0]["execution_limits"] ==
       {"provider_turn_seconds": 3600,
        "verification_command_seconds": 900}
       and "quickstart-c" not in json.dumps(submission)
       and "5a8fa4b4-W1" not in json.dumps(submission))

    # R1: THE OPERATOR'S OWN EXTRACTION, against the ACTUAL emitted file.
    emitted = root / "generated" / "preparation-readback.json"
    ok("the preparation emitted its readback", emitted.is_file())
    document = json.loads(emitted.read_text())
    ok("the emitted readback has NO `preparation` member -- which is what "
       "the previous command indexed", "preparation" not in document,
       top_level=sorted(document)[:8])
    extracted = subprocess.run(
        [sys.executable, "-c",
         'import json,sys;print(json.load(open(sys.argv[1]))'
         '["workspace_storage"][0])', str(emitted)],
        capture_output=True, text=True)
    ok("the CORRECTED selection-2b command extracts a path from the real "
       "document", extracted.returncode == 0 and extracted.stdout.strip(),
       path=extracted.stdout.strip(), stderr=extracted.stderr.strip()[:160])
    storage = extracted.stdout.strip()
    ok("and that path is the workspace storage the installed workers name",
       storage in {one.get("deployment", {}).get("workspace_storage")
                   for one in installed.get("workers") or []})
    ok("it is inside this instance's own destination, and does not exist "
       "yet -- which is why selection 2b exists",
       storage.startswith(str(root)) and not pathlib.Path(storage).is_dir())
    # AND THE COMMAND THE PREVIOUS PACKET SHIPPED REALLY DOES FAIL.
    was = subprocess.run(
        [sys.executable, "-c",
         'import json,sys;print(json.load(open(sys.argv[1]))'
         '["preparation"]["workspace_storage"][0])', str(emitted)],
        capture_output=True, text=True)
    ok("the PREVIOUS packet's command raises on the same document, which is "
       "the defect R1 names", was.returncode != 0,
       stderr=was.stderr.strip().splitlines()[-1:] )

    refuses("a second apply of the same destination refuses",
            lambda: fresh5.prepare(str(root), where, apply=True,
                                   bundle=bundle, source=source,
                                   runner=runner, pins=pins,
                                   bundle_digest=held["digest"],
                                   bundle_files=held["files"],
                                   commit=_source_commit(source)),
            "already")
    return {"root": str(root), "authority": uuid, "work": prepared["work"],
            "workspace_storage": storage}


def retained_isolation():
    home = tempfile.mkdtemp(prefix="w325959-r5-retained-")
    bundle, held, source = simulated(home)
    for retained in ("native-coordination-pilot-w321608-1",
                     "native-coordination-pilot-w321608-2",
                     "native-coordination-pilot-w321608-3"):
        inside = f"/home/sl/baton-instances/{retained}/inside"
        where, pins = staged(home, inside, name="inside" + retained[-1])
        refuses(f"a destination inside retained instance {retained[-1]} "
                f"refuses",
                lambda where=where, inside=inside, p=pins: fresh5.prepare(
                    inside, where, apply=False, bundle=bundle, source=source,
                    runner=runner, pins=p, bundle_digest=held["digest"],
                    bundle_files=held["files"],
                    commit=_source_commit(source)),
                "lies inside")


def carried_forward():
    """The accepted cases the corrections must not have cost. fresh4."""
    home = tempfile.mkdtemp(prefix="w325959-r5-carried-")
    root = pathlib.Path(home, "destination")
    where, pins = staged(home, root)
    bundle, held, source = simulated(home)

    answer = fresh5.prepare(str(root), where, apply=False, bundle=bundle,
                            source=source, runner=runner, pins=pins,
                            bundle_digest=held["digest"],
                            bundle_files=held["files"],
                            commit=_source_commit(source))
    prepared = answer["preparation"]
    ok("the preflight validates, plans the mint and creates NOTHING",
       prepared["static"]["validated"] is True
       and prepared["step1"]["planned"] is True and not root.exists())
    ok("and it still reports the selected bundle and the read revision",
       answer["bundle"]["digest"] == held["digest"]
       and answer["source_commit"] == fresh5.COMMIT)

    drifted = pathlib.Path(home, "drifted-helper")
    drifted.mkdir()
    (drifted / "fresh.py").write_text("# not the accepted bytes\n")
    was = fresh5.ACCEPTED
    try:
        fresh5.ACCEPTED = drifted
        refuses("a DRIFTED accepted helper refuses",
                fresh5.accepted_helper, "is not the reviewed one")
    finally:
        fresh5.ACCEPTED = was
    ok("and the real accepted helper still hashes to its pin after that",
       bool(fresh5.accepted_helper()))

    from tools.instance import InstanceRefusal

    gone = pathlib.Path(home, "no-such-bundle")
    refuses("an absent bundle refuses -- through the PRODUCT's own refusal, "
            "not a restatement of it",
            lambda: fresh5.prepare(str(root), where, apply=False,
                                   bundle=gone, source=source,
                                   runner=runner, pins=pins,
                                   commit=_source_commit(source)),
            "no bundled runtime", root=root,
            accepting=(InstanceRefusal,))


def main():
    started = time.monotonic()
    the_shipped_pins_are_real()
    an_edited_document_refuses()
    another_bundle_refuses()
    source_drift_refuses()
    applied = the_apply_and_the_operator_command()
    retained_isolation()
    carried_forward()
    answer = {"revision": 4, "corrected": "claim361402",
              "packet": str(PACKET), "source_commit": fresh5.COMMIT,
              "bundle": str(fresh5.DISTRO),
              "bundle_digest": fresh5.BUNDLE_DIGEST,
              "disposable_apply": applied, "checks": CHECKS,
              "failed": [one for one in CHECKS if not one["outcome"]],
              "seconds": time.monotonic() - started}
    print(json.dumps(answer, indent=1, sort_keys=True, default=str))
    return 1 if answer["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
