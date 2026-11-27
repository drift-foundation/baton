"""W386447 review 2026-11-27 [3]: the launch reads what each configured image INSTALLED, not what it claims.

DETERMINISTIC AND OFFLINE. The engine is a scripted `docker` executable serving image trees from a fixture; no
real engine is contacted. THE PASSING CASE IS EXACT: its image trees are assembled from this repository's own
`worker/Dockerfile.codex` and `worker/Dockerfile.claude` COPY lines and ENTRYPOINT, from this tree's bytes, so it is
the contents a build of this source installs at /opt/baton.
"""
import io
import json
import os
from pathlib import Path
import shlex
import shutil
import sys
import tempfile
import unittest

_DISTRIBUTION = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_DISTRIBUTION))
sys.path.insert(1, str(_DISTRIBUTION / "src"))
from tools import installed_worker  # noqa: E402

V12 = _DISTRIBUTION.parent
IMPL = "sha256:" + "1" * 64
REVIEW = "sha256:" + "2" * 64

# The scripted engine: image inspect / create / cp / rm, from `images.json` beside it; every call is journalled.
ENGINE = r'''
import io, json, os, sys, tarfile
here = os.path.dirname(os.path.abspath(__file__))
spec = json.load(open(os.path.join(here, "images.json")))
with open(os.path.join(here, "calls.jsonl"), "a") as log:
    log.write(json.dumps(sys.argv[1:]) + "\n")
verb = sys.argv[1:3] if sys.argv[1] == "image" else sys.argv[1:2]
if verb == ["image", "inspect"]:
    image = sys.argv[3]
    if image not in spec:
        sys.stderr.write("No such image: " + image + "\n"); sys.exit(1)
    print(json.dumps([{"Id": spec[image].get("id", image), "Config": {"Entrypoint": spec[image]["entrypoint"]}}]))
elif verb == ["create"]:
    assert sys.argv[2:4] == ["--network", "none"], sys.argv
    print(sys.argv[4][7:19] + "c0ffee")
elif verb == ["cp"]:
    container, path = sys.argv[2].split(":", 1)
    assert path == "/opt/baton" and sys.argv[3] == "-", sys.argv
    image = next(i for i in spec if i[7:19] + "c0ffee" == container)
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w") as archive:
        archive.add(spec[image]["tree"], arcname="baton")
    sys.stdout.buffer.write(buffer.getvalue())
elif verb == ["rm"]:
    pass
else:
    sys.stderr.write("the scripted engine does not " + " ".join(sys.argv[1:3]) + "\n"); sys.exit(97)
'''


def recipe(dockerfile):
    """[(sources, destination)] and the ENTRYPOINT of one of this repository's worker Dockerfiles."""
    text = (V12 / "worker" / dockerfile).read_text().replace("\\\n", " ")
    copies, entrypoint = [], None
    for line in text.splitlines():
        if line.startswith("COPY "):
            words = shlex.split(line)
            copies.append((words[1:-1], words[-1]))
        elif line.startswith("ENTRYPOINT "):
            entrypoint = json.loads(line.split(None, 1)[1])
    assert copies and entrypoint, dockerfile
    return copies, entrypoint


def assemble(dockerfile, into):
    """What a build of THIS tree installs at /opt/baton, laid out under `into`."""
    copies, entrypoint = recipe(dockerfile)
    for sources, destination in copies:
        assert destination.startswith("/opt/baton/"), destination
        target = into / destination[len("/opt/baton/"):]
        [source] = sources
        if (V12 / source).is_dir():
            shutil.copytree(V12 / source, target, ignore=shutil.ignore_patterns("__pycache__"))
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(V12 / source, target)
    return entrypoint


class Fixture(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix="v12-installed-worker-")
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.engine = self.root / "engine"
        self.engine.mkdir()
        (self.engine / "docker.py").write_text(ENGINE)
        self.docker = self.engine / "docker"
        self.docker.write_text("#!/bin/sh\nexec " + shlex.quote(sys.executable) + " -I "
                               + shlex.quote(str(self.engine / "docker.py")) + ' "$@"\n')
        self.docker.chmod(0o700)
        self.images = {}
        for image, dockerfile in ((IMPL, "Dockerfile.codex"), (REVIEW, "Dockerfile.claude")):
            tree = self.root / image[7:15]
            self.images[image] = {"tree": str(tree), "entrypoint": assemble(dockerfile, tree)}
        self.deployment = {"workers": []}
        for worker_id, provider, image in (("impl-codex", "codex", IMPL), ("review-claude", "claude", REVIEW)):
            contract = {"selection": {"provider": provider}, "adapter": {"provider": provider},
                        "runtime_profile": {"provider": provider, "image_digest": image}}
            self.deployment["workers"].append({"worker_id": worker_id, "deployment": {"provider_contract": contract}})

    def measure(self):
        (self.engine / "images.json").write_text(json.dumps(self.images))
        return installed_worker.measure(self.deployment, V12, docker=str(self.docker))

    def calls(self):
        return [json.loads(line) for line in (self.engine / "calls.jsonl").read_text().splitlines()]

    def tree(self, image):
        return Path(self.images[image]["tree"])


class TheExactInstalledContentsQualify(Fixture):

    def test_images_holding_exactly_this_trees_worker_code_qualify(self):
        report = self.measure()
        self.assertTrue(report["qualified"], json.dumps([one["problems"] for one in report["workers"]]))
        impl, review = report["workers"]
        self.assertEqual((impl["worker_id"], impl["image"], review["worker_id"], review["image"]),
                         ("impl-codex", IMPL, "review-claude", REVIEW))
        # THE ADAPTER AND EACH ENTRYPOINT ARE MEASURED, by digest, against this tree's bytes.
        adapter = installed_worker._digest((V12 / "worker" / "claude_agent.py").read_bytes())
        for one, entry in ((impl, "codex_entry.py"), (review, "dogfood_entry.py")):
            self.assertEqual(one["measured"]["claude_agent.py"]["installed"], adapter)
            self.assertEqual(one["entrypoint"], ["python3", "/opt/baton/" + entry])
            self.assertTrue(one["measured"][entry]["equal"])
            self.assertEqual(one["unmatched"], [])
        self.assertIn("codex_agent.py", impl["measured"])
        self.assertTrue(any(name.startswith("provider_policy/") for name in review["measured"]))

    def test_the_command_says_so_and_keeps_the_report(self):
        (self.engine / "images.json").write_text(json.dumps(self.images))
        place = self.root / "deployment.json"
        place.write_text(json.dumps(self.deployment))
        stream = io.StringIO()
        code = installed_worker.main(["--deployment", str(place), "--source", str(V12), "--docker", str(self.docker),
                                      "--report", str(self.root / "report.json")], stream=stream)
        self.assertEqual(code, 0, stream.getvalue())
        self.assertEqual(stream.getvalue().count("QUALIFIED "), 2)
        self.assertTrue(json.loads((self.root / "report.json").read_text())["qualified"])

    def test_nothing_is_started_and_every_created_container_is_removed(self):
        self.measure()
        verbs = [call[0] if call[0] != "image" else "image " + call[1] for call in self.calls()]
        self.assertEqual(verbs, ["image inspect", "create", "cp", "rm"] * 2)
        self.assertFalse({"start", "run", "exec"} & set(verbs))
        created = [call[-1][7:19] + "c0ffee" for call in self.calls() if call[0] == "create"]
        self.assertEqual([call[1] for call in self.calls() if call[0] == "rm"], created)


class AnythingElseDoesNot(Fixture):

    def assertRefusedFor(self, worker, words):
        report = self.measure()
        self.assertFalse(report["qualified"])
        one = next(one for one in report["workers"] if one["worker_id"] == worker)
        self.assertFalse(one["qualified"])
        self.assertTrue(any(words in problem for problem in one["problems"]), one["problems"])

    def test_an_image_whose_adapter_is_not_the_sources(self):
        # The image a revision label vouches for but whose installed adapter predates the owner-decision prompt.
        place = self.tree(REVIEW) / "claude_agent.py"
        place.write_bytes(place.read_bytes().replace(b"THE OWNER'S DECISION ON THAT ESCALATION", b"THE REVIEWER'S"))
        self.assertRefusedFor("review-claude", "claude_agent.py differs from worker/claude_agent.py")

    def test_one_byte_in_any_measured_file(self):
        with open(self.tree(IMPL) / "baton_worker.py", "ab") as appended:
            appended.write(b"\n")
        self.assertRefusedFor("impl-codex", "baton_worker.py differs")

    def test_an_image_without_the_adapter(self):
        os.unlink(self.tree(IMPL) / "claude_agent.py")
        self.assertRefusedFor("impl-codex", "claude_agent.py is not installed")

    def test_codex_refuses_the_installed_claude_entrypoint(self):
        self.images[IMPL]["entrypoint"] = ["python3", "/opt/baton/dogfood_entry.py"]
        self.assertRefusedFor("impl-codex", "codex requires entrypoint")

    def test_codex_requires_its_own_adapter_and_shared_entry_module(self):
        for name in ("codex_agent.py", "dogfood_entry.py"):
            with self.subTest(name=name):
                path = self.tree(IMPL) / name
                original = path.read_bytes()
                path.unlink()
                self.assertRefusedFor("impl-codex", name + " is not installed")
                path.write_bytes(original)

    def test_provider_selection_determines_expected_image_independently_of_worker_id(self):
        contract = self.deployment["workers"][0]["deployment"]["provider_contract"]
        for field in ("selection", "adapter", "runtime_profile"):
            contract[field]["provider"] = "claude"
        self.assertRefusedFor("impl-codex", "claude requires entrypoint")

    def test_unknown_missing_and_inconsistent_provider_contracts_refuse(self):
        contract = self.deployment["workers"][0]["deployment"]["provider_contract"]
        for field, value in (("selection", "other"), ("selection", None), ("adapter", "claude"),
                             ("runtime_profile", "claude")):
            with self.subTest(field=field, value=value):
                contract[field]["provider"] = value
                with self.assertRaises(installed_worker.Unreadable):
                    installed_worker.configured(self.deployment)
                contract[field]["provider"] = "codex"

    def test_an_entrypoint_that_is_not_a_measured_baton_entry(self):
        for entrypoint in (["python3", "/opt/baton/elsewhere.py"], ["/bin/sh", "-c", "python3 /opt/baton/codex_entry.py"],
                           None):
            with self.subTest(entrypoint=entrypoint):
                self.images[IMPL]["entrypoint"] = entrypoint
                self.assertRefusedFor("impl-codex", "is not a measured Baton entry")

    def test_an_entrypoint_whose_bytes_differ(self):
        with open(self.tree(IMPL) / "codex_entry.py", "ab") as appended:
            appended.write(b"# changed\n")
        self.assertRefusedFor("impl-codex", "the entrypoint codex_entry.py is not the source's")

    def test_an_engine_image_that_is_not_the_pinned_id_is_unreadable(self):
        self.images[IMPL]["id"] = "sha256:" + "3" * 64
        with self.assertRaises(installed_worker.Unreadable) as raised:
            self.measure()
        self.assertIn("the engine's image for " + IMPL, str(raised.exception))
        self.assertNotIn("create", [call[0] for call in self.calls()])

    def test_a_missing_image_or_an_unpinned_worker_is_unreadable(self):
        del self.images[REVIEW]
        with self.assertRaises(installed_worker.Unreadable):
            self.measure()
        self.deployment["workers"][0]["deployment"]["provider_contract"]["runtime_profile"]["image_digest"] = "codex:latest"
        with self.assertRaises(installed_worker.Unreadable):
            installed_worker.configured(self.deployment)

    def test_the_command_exits_nonzero_when_one_worker_does_not_qualify(self):
        os.unlink(self.tree(REVIEW) / "claude_agent.py")
        (self.engine / "images.json").write_text(json.dumps(self.images))
        place = self.root / "deployment.json"
        place.write_text(json.dumps(self.deployment))
        stream = io.StringIO()
        code = installed_worker.main(["--deployment", str(place), "--source", str(V12), "--docker", str(self.docker)],
                                     stream=stream)
        self.assertEqual(code, 1)
        self.assertIn("NOT QUALIFIED review-claude", stream.getvalue())
        self.assertIn("QUALIFIED impl-codex", stream.getvalue())


if __name__ == "__main__":
    unittest.main()
