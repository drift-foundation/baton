"""W112630: the immutable integration evidence bundle, byte for byte.

`work/records/2026/09/finding-v12-integration-worker-workload/findings/
finding-integration-evidence-bundle/`.

WHAT THIS FILE OWNS. The producer's read-only version-control reading, the
published bundle's exact bytes and modes, the worker contract's bounded readers
over that real material, and the conformance that keeps three spellings of one
protocol equal.

THE VERSION CONTROL IS A DETERMINISTIC READ-ONLY SEAM OVER REAL TEMPORARY
FILES, which is the methodology the parent finding fixes for this producer:
`Objects` answers the module's OWN composed vectors from real files on disk and
refuses any argv the module did not compose, so a vector that drifts stops
being answered rather than being quietly accepted. No `git` process runs, no
repository is created and nothing is committed -- the parent is explicit that
Git is not to be mutated merely to build a reviewer fixture.

AND THE MANAGER HALF IS NOT SEAMED AT ALL. `TheProducerComposesFromRealOwners`
drives the real `_OrdinaryAdmissionWorld` -- a real worker turn, real custody,
real Authority receipts, a real accepted checkpoint and a real Job store,
imported from its own suite and never edited -- so what `compose_bundle`
resolves is what those owners actually answer. My own mocked eligibility
document is what hid a `KeyError` in W112029; the lesson is applied here rather
than restated.
"""

import hashlib
import json
import os
import pathlib
import stat
import subprocess
import sys
import tempfile
import unittest

from baton_v12.contracts import ContractRefusal, digest, digest_of_bytes
from baton_v12.integration import runtime
from baton_v12.worker_manager import launch as launch_module
from baton_v12.worker_manager.source_boundary import SOURCE_TARGET

from tools import integration_bundle as producer

from tests.integration.test_execution import profile as integration_profile


WORKER = pathlib.Path(__file__).resolve().parents[3] / "worker"
if str(WORKER) not in sys.path:
    sys.path.insert(0, str(WORKER))

import integration_contract as contract              # noqa: E402


INSTRUCTIONS = ("Import only the approved candidate bytes.\n"
                "Preserve the reviewed modes.\n").encode("utf-8")

BASE = "a1" * 20
HEAD = "b2" * 20
BASE_TREE = "c3" * 20
HEAD_TREE = "d4" * 20


def object_name(payload):
    """The name version control gives one blob, computed the way it does."""
    return hashlib.sha1(b"blob " + str(len(payload)).encode("ascii") + b"\x00"
                        + payload).hexdigest()


class Objects:
    """A read-only Git runner answering from real files, and nothing else.

    IT REFUSES AN ARGV THE MODULE DID NOT COMPOSE. Every answer is dispatched
    by comparing the argv it was handed with the vector the module builds for
    that question, so this seam cannot drift into answering a command the
    producer does not actually issue -- which is the failure a hand-written
    fake usually hides.
    """

    def __init__(self, root, repository):
        self.root = root
        self.repository = repository
        # THE DIRECTORY THIS SEAM IS BOUND TO, resolved once at construction
        # and never re-read from the name: `self.repository` is only what the
        # fixture calls it, and `identity` is a private duplicate that a
        # transient swap of that name cannot move.
        self.identity = os.path.join(root, "identity")
        if not os.path.isdir(self.identity):
            os.makedirs(self.identity, exist_ok=True)
        self.directories = []
        self.opened = []
        self.pinned = os.stat(self.identity)
        os.makedirs(os.path.join(root, "objects"), exist_ok=True)
        self.trees = {}
        self.revisions = {}
        self.missing = set()
        self.calls = []
        self.answers = {}
        # WHAT HAPPENS WHILE THE PRODUCER IS READING. Review
        # 2026-09-07T19:29:28Z drives its custody probe from exactly here: the
        # world changes at the first extraction query and the seam then goes
        # on answering normally, so what the case measures is whether the
        # producer looks again -- not whether a real race is winnable.
        self.on_first = None

    # -- composing the world -------------------------------------------------

    def blob(self, payload):
        """One real temporary file, addressed the way version control does."""
        name = object_name(payload)
        with open(os.path.join(self.root, "objects", name), "wb") as handle:
            handle.write(payload)
        return name

    def tree(self, name, entries):
        """`entries` maps a path to `(mode, payload)` or `(mode, object)`."""
        held = {}
        for path, (mode, payload) in entries.items():
            held[path] = (mode, self.blob(payload)
                          if isinstance(payload, bytes) else payload)
        self.trees[name] = held
        return name

    def revision(self, name, tree):
        self.revisions[name] = tree
        return name

    # -- answering -----------------------------------------------------------

    def _answer(self, payload):
        return {"returncode": 0, "stdout": payload, "stderr": b""}

    def _failed(self, detail):
        return {"returncode": 128, "stdout": b"", "stderr": detail}

    def __call__(self, argv, *, directory=None):
        """Parse the question, then PROVE the argv is the module's own vector.

        Parsing first and comparing second is what keeps this seam honest: it
        answers only a command `integration_bundle` itself composes for those
        exact operands, so a vector that quietly changed shape would stop
        being answered rather than being met by a fake that had been taught
        the new shape at the same time.

        AND IT ANSWERS FROM THE DESCRIPTOR, not from a name. Review
        2026-09-07T19:51:54Z [P1]: a pathname is resolved again on every use,
        so a transient swap redirected the reads and was gone before anything
        looked. A real runner reaches its working directory by `fchdir` on
        this descriptor; this one identifies the directory by `fstat`, which
        is the same question and the reason the swap below is invisible to it.
        """
        argv = list(argv)
        if self.on_first is not None:
            during, self.on_first = self.on_first, None
            during()
        self.calls.append(argv)
        if directory is None:
            self.directories.append(None)
        else:
            held = os.fstat(directory)
            self.directories.append((held.st_dev, held.st_ino))
        if tuple(argv) in self.answers:
            return self.answers[tuple(argv)]
        if directory is None:
            return self._failed(b"fatal: no directory to run in")
        # AGAINST THE IDENTITY PINNED WHEN THIS SEAM WAS BOUND, never against
        # a fresh `stat` of the name -- re-reading the name is the behaviour
        # the descriptor replaced, and a seam that did it would answer from
        # whatever the name points at now.
        if not os.path.samestat(os.fstat(directory), self.pinned):
            return self._failed(b"fatal: not this repository")
        if argv[:2] != ["git", "--no-optional-locks"]:
            return self._failed(b"fatal: not a bounded read")
        rest = argv[2:]
        if rest[:2] == ["rev-parse", "--verify"] and len(rest) == 3:
            revision = rest[2].removesuffix("^{tree}")
            if argv != producer.tree_vector(revision):
                return self._failed(b"fatal: unrecognized revision vector")
            if revision not in self.revisions:
                return self._failed(b"fatal: not a valid object name")
            return self._answer(self.revisions[revision].encode("ascii")
                                + b"\n")
        if rest[0] == "ls-tree" and len(rest) == 6:
            tree, path = rest[3], rest[5]
            if argv != producer.entry_vector(tree, path):
                return self._failed(b"fatal: unrecognized tree vector")
            if tree not in self.trees:
                return self._failed(b"fatal: not a tree object")
            entries = self.trees[tree]
            if path not in entries:
                return self._answer(b"")
            mode, name = entries[path]
            return self._answer(
                f"{mode} blob {name}\t{path}".encode("utf-8") + b"\x00")
        if rest[0] == "cat-file" and len(rest) == 3 \
                and rest[1] in ("-s", "blob"):
            name = rest[2]
            vector = (producer.size_vector if rest[1] == "-s"
                      else producer.content_vector)
            if argv != vector(name):
                return self._failed(b"fatal: unrecognized object vector")
            place = os.path.join(self.root, "objects", name)
            if name in self.missing or not os.path.exists(place):
                return self._failed(b"fatal: not a valid object name")
            if rest[1] == "-s":
                return self._answer(
                    str(os.path.getsize(place)).encode("ascii") + b"\n")
            with open(place, "rb") as handle:
                return self._answer(handle.read())
        return self._failed(b"fatal: this seam answers no such command")

    def bind(self, place):
        """Bind this seam to one directory, by identity and not by name."""
        self.identity = place
        self.pinned = os.stat(place)
        return self

    def held(self):
        """One descriptor for the directory this seam belongs to."""
        holder = os.open(self.identity, os.O_RDONLY | os.O_DIRECTORY)
        self.opened.append(holder)
        return holder

    def release(self):
        for one in self.opened:
            try:
                os.close(one)
            except OSError:
                pass
        self.opened = []


def evidence(**changed):
    """One checkpoint profile's closed evidence, in its own spellings."""
    paths = changed.pop("paths", ["src/edited.py", "src/gone.py",
                                  "src/new.py"])
    held = {"profile": "git", "base": BASE, "head": HEAD, "tree": HEAD_TREE,
            "paths": list(paths), "path_set_digest": digest(list(paths)),
            "reference": "refs/baton/checkpoints/line-1/1"}
    held.update(changed)
    return held


class PathTableCase(unittest.TestCase):
    """One reviewed change with an add, an edit and a delete in it."""

    EDITED_BASE = b"print('before')\n"
    EDITED_HEAD = b"print('after')\n"
    GONE = b"# removed entirely\n"
    NEW = b"#!/bin/sh\necho added\n"

    def setUp(self):
        self._root = tempfile.TemporaryDirectory(prefix="v12-bundle-")
        self.addCleanup(self._root.cleanup)
        self.root = self._root.name
        self.repository = os.path.join(self.root, "line")
        os.mkdir(self.repository)
        self.objects = Objects(self.root, self.repository)
        self.addCleanup(self.objects.release)
        self.objects.revision(BASE, BASE_TREE)
        self.objects.revision(HEAD, HEAD_TREE)
        self.base_entries = {"src/edited.py": ("100644", self.EDITED_BASE),
                             "src/gone.py": ("100644", self.GONE)}
        self.head_entries = {"src/edited.py": ("100644", self.EDITED_HEAD),
                             "src/new.py": ("100755", self.NEW)}
        self.objects.tree(BASE_TREE, self.base_entries)
        self.objects.tree(HEAD_TREE, self.head_entries)

    def table(self, **changed):
        return producer.reviewed_path_table(self.objects, self.objects.held(),
                                            evidence(**changed))

    def refused(self, action, *operands, **named):
        with self.assertRaises(ContractRefusal) as caught:
            action(*operands, **named)
        return caught.exception


class TheReviewedPathTableComesFromRetainedObjects(PathTableCase):

    def test_one_row_per_reviewed_path_with_its_operation(self):
        table = self.table()
        self.assertEqual([(one["path"], one["operation"])
                          for one in table["paths"]],
                         [("src/edited.py", "edit"), ("src/gone.py", "delete"),
                          ("src/new.py", "add")])

    def test_each_side_names_both_identities_and_the_reviewed_mode(self):
        rows = {one["path"]: one for one in self.table()["paths"]}
        edited = rows["src/edited.py"]
        self.assertEqual(set(edited["base"]), set(producer.SIDE_MEMBERS))
        self.assertEqual(edited["base"]["object"],
                         object_name(self.EDITED_BASE))
        self.assertEqual(
            edited["base"]["blob"],
            digest_of_bytes(self.EDITED_BASE).split(":", 1)[1])
        self.assertEqual(edited["base"]["bytes"], len(self.EDITED_BASE))
        # THE VERSION-CONTROL NAME AND THE CONTENT ADDRESS ARE NOT ONE MEMBER.
        self.assertNotEqual(edited["base"]["object"], edited["base"]["blob"])
        self.assertEqual(rows["src/new.py"]["candidate"]["mode"], "100755")
        self.assertEqual(rows["src/gone.py"]["candidate"], None)
        self.assertEqual(rows["src/new.py"]["base"], None)

    def test_the_blobs_are_the_exact_reviewed_bytes(self):
        table = self.table()
        held = {digest_of_bytes(one).split(":", 1)[1]: one
                for one in (self.EDITED_BASE, self.EDITED_HEAD, self.GONE,
                            self.NEW)}
        self.assertEqual(table["blobs"], held)
        self.assertEqual(table["total_bytes"], sum(len(one) for one in held.values()))

    def test_one_content_is_carried_once_however_many_rows_name_it(self):
        """Two paths holding identical bytes address one blob."""
        same = dict(self.head_entries)
        same["src/new.py"] = ("100644", self.EDITED_HEAD)
        self.objects.tree(HEAD_TREE, same)
        table = self.table()
        addresses = [one[side]["blob"] for one in table["paths"]
                     for side in ("base", "candidate") if one[side]]
        self.assertEqual(len(addresses), 4)
        self.assertEqual(len(table["blobs"]), 3)

    def test_the_vectors_are_read_only_and_lock_free(self):
        self.table()
        for argv in self.objects.calls:
            self.assertEqual(argv[:2], ["git", "--no-optional-locks"])
            self.assertIn(argv[2], ("rev-parse", "ls-tree", "cat-file"))
        # NOTHING THAT WRITES, spelled out rather than implied by the three
        # verbs above: a later vector added without a case is caught here.
        words = {word for argv in self.objects.calls for word in argv}
        for forbidden in ("clone", "fetch", "checkout", "reset", "update-ref",
                          "add", "commit", "push", "gc", "unpack-objects"):
            self.assertNotIn(forbidden, words)

    def test_the_composed_vectors_are_exactly_these(self):
        """AND NOT ONE OF THEM NAMES THE REPOSITORY. Review
        2026-09-07T19:51:54Z [P1]: where the command runs is the descriptor's
        business now, and a word carrying the pathname would put back the one
        thing the binding removed."""
        self.assertEqual(
            producer.tree_vector(HEAD),
            ["git", "--no-optional-locks", "rev-parse", "--verify",
             HEAD + "^{tree}"])
        self.assertEqual(
            producer.entry_vector(HEAD_TREE, "src/new.py"),
            ["git", "--no-optional-locks", "ls-tree", "--full-tree", "-z",
             HEAD_TREE, "--", "src/new.py"])
        self.assertEqual(producer.content_vector(BASE),
                         ["git", "--no-optional-locks", "cat-file", "blob",
                          BASE])
        self.assertEqual(producer.size_vector(BASE),
                         ["git", "--no-optional-locks", "cat-file", "-s",
                          BASE])
        for argv in (producer.tree_vector(HEAD),
                     producer.entry_vector(HEAD_TREE, "src/new.py"),
                     producer.content_vector(BASE),
                     producer.size_vector(BASE)):
            self.assertNotIn("-C", argv)
            self.assertNotIn(self.repository, argv)


class ThePathTableRefusesWhatItCannotAccountFor(PathTableCase):

    def test_a_missing_retained_object_is_a_producer_gap(self):
        self.objects.missing.add(object_name(self.NEW))
        caught = self.refused(self.table)
        self.assertEqual((caught.category, caught.code),
                         ("refused", "precondition"))

    def test_a_reviewed_path_in_neither_tree_refuses(self):
        caught = self.refused(self.table, paths=["src/nowhere.py"])
        self.assertEqual((caught.category, caught.code),
                         ("refused", "precondition"))
        self.assertIn("nowhere", str(caught))

    def test_an_unchanged_reviewed_path_refuses(self):
        entries = dict(self.head_entries)
        entries["src/gone.py"] = ("100644", self.GONE)
        self.objects.tree(HEAD_TREE, entries)
        caught = self.refused(self.table)
        self.assertIn("identical on both sides", str(caught))

    def test_a_symlink_or_a_submodule_refuses_the_whole_proposal(self):
        for mode, kind in (("120000", "blob"), ("160000", "commit"),
                           ("040000", "tree")):
            with self.subTest(mode=mode):
                objects = Objects(
                    os.path.join(self.root, "unsupported-" + mode),
                    self.repository)
                objects.revision(BASE, BASE_TREE)
                objects.revision(HEAD, HEAD_TREE)
                objects.tree(BASE_TREE, {})
                name = objects.blob(self.NEW)
                objects.trees[HEAD_TREE] = {"src/new.py": (mode, name)}
                if kind != "blob":
                    objects.answers[tuple(producer.entry_vector(
                        HEAD_TREE, "src/new.py"))] = {
                            "returncode": 0,
                            "stdout": f"{mode} {kind} {name}\tsrc/new.py"
                                      .encode("utf-8") + b"\x00",
                            "stderr": b""}
                caught = self.refused(producer.reviewed_path_table, objects,
                                      objects.held(),
                                      evidence(paths=["src/new.py"]))
                self.assertEqual((caught.category, caught.code),
                                 ("policy", "denied"))

    def test_the_candidate_tree_must_be_the_one_the_checkpoint_recorded(self):
        self.objects.revision(HEAD, BASE_TREE)
        caught = self.refused(self.table)
        self.assertIn("accepted checkpoint recorded", str(caught))

    def test_a_text_runner_is_not_this_modules_runner(self):
        self.objects.answers[tuple(producer.tree_vector(BASE))] = {"returncode": 0, "stdout": BASE_TREE,
                                        "stderr": ""}
        caught = self.refused(self.table)
        self.assertIn("exact bytes", str(caught))

    def test_a_malformed_runner_answer_refuses(self):
        for answer in ({"returncode": 0, "stdout": b""},
                       {"returncode": True, "stdout": b"", "stderr": b""},
                       ["returncode", 0]):
            with self.subTest(answer=type(answer).__name__):
                self.objects.answers[tuple(producer.tree_vector(BASE))] = answer
                self.refused(self.table)

    def test_more_than_one_entry_for_one_path_refuses(self):
        name = object_name(self.NEW)
        self.objects.answers[tuple(producer.entry_vector(
            HEAD_TREE, "src/new.py"))] = {
                "returncode": 0,
                "stdout": (f"100644 blob {name}\tsrc/new.py".encode() + b"\x00"
                           + f"100644 blob {name}\tsrc/new.py".encode()
                           + b"\x00"),
                "stderr": b""}
        caught = self.refused(self.table)
        self.assertIn("answered 2 entries", str(caught))

    def test_an_entry_for_another_path_refuses(self):
        name = object_name(self.NEW)
        self.objects.answers[tuple(producer.entry_vector(
            HEAD_TREE, "src/new.py"))] = {
                "returncode": 0,
                "stdout": f"100644 blob {name}\tsrc/other.py".encode()
                          + b"\x00",
                "stderr": b""}
        self.refused(self.table)

    def test_content_that_disagrees_with_its_declared_size_refuses(self):
        self.objects.answers[tuple(producer.size_vector(
            object_name(self.NEW)))] = {
                "returncode": 0, "stdout": b"3\n", "stderr": b""}
        caught = self.refused(self.table)
        self.assertIn("declared 3", str(caught))

    def test_content_above_the_blob_bound_refuses_before_it_is_read(self):
        name = object_name(self.NEW)
        self.objects.answers[tuple(producer.size_vector(name))] = {
                "returncode": 0,
                "stdout": str(producer.MAX_BLOB_BYTES + 1).encode() + b"\n",
                "stderr": b""}
        caught = self.refused(self.table)
        self.assertIn(str(producer.MAX_BLOB_BYTES), str(caught))
        # AND THE CONTENT WAS NEVER ASKED FOR.
        self.assertNotIn(producer.content_vector(name),
                         self.objects.calls)

    def test_an_unsafe_reviewed_path_refuses(self):
        for path in ("/etc/passwd", "../escape", "a/../b", ".git/config",
                     "src/.git/hooks/pre-commit", "", "a//b", "a\x00b"):
            with self.subTest(path=path):
                self.refused(self.table, paths=[path])

    def test_an_unsorted_duplicated_or_nested_path_set_refuses(self):
        for paths in (["src/new.py", "src/edited.py"],
                      ["src/new.py", "src/new.py"],
                      ["src", "src/new.py"]):
            with self.subTest(paths=paths):
                self.refused(self.table, paths=paths)

    def test_more_paths_than_the_bound_refuses(self):
        """And the bound is reached BEFORE any digest is attempted, which is
        what makes it this module's bound rather than a serializer accident."""
        many = sorted(f"src/{index:05d}.py"
                      for index in range(producer.MAX_PATHS + 1))
        held = evidence(paths=["src/edited.py"])
        held["paths"] = many
        caught = self.refused(producer.reviewed_path_table, self.objects,
                              self.objects.held(), held)
        self.assertIn(str(producer.MAX_PATHS), str(caught))

    def test_a_path_set_digest_that_is_not_its_paths_refuses(self):
        caught = self.refused(self.table,
                              path_set_digest="sha256:" + "0" * 64)
        self.assertIn("path-set digest", str(caught))

    def test_evidence_of_another_profile_or_another_shape_refuses(self):
        caught = self.refused(self.table, profile="mercurial")
        self.assertEqual((caught.category, caught.code), ("policy", "denied"))
        held = evidence()
        del held["reference"]
        self.refused(producer.reviewed_path_table, self.objects,
                     self.objects.held(), held)


# -- the worker's own contract ----------------------------------------------


class TheThreeSpellingsOfOneProtocolAgree(unittest.TestCase):
    """A conformance case, because the worker cannot import the owner."""

    def test_the_producer_and_the_worker_contract_name_one_layout(self):
        for name in ("BUNDLE_SCHEMA", "ENVELOPE_DOCUMENT",
                     "INSTRUCTIONS_DOCUMENT", "EVIDENCE_DIRECTORY",
                     "BLOB_DIRECTORY", "ENVELOPE_MEMBERS", "LAUNCH_MEMBERS",
                     "EVIDENCE_DOCUMENTS", "EVIDENCE_MEMBERS", "PATH_MEMBERS",
                     "SIDE_MEMBERS", "OPERATIONS", "MODES",
                     "MAX_ENVELOPE_BYTES", "MAX_INSTRUCTION_BYTES",
                     "MAX_PATHS", "MAX_BLOB_BYTES", "MAX_EVIDENCE_BYTES"):
            with self.subTest(name=name):
                self.assertEqual(getattr(producer, name),
                                 getattr(contract, name))

    def test_the_worker_contract_and_the_manager_runtime_name_one_protocol(self):
        for name in ("ASSIGNMENT_SCHEMA", "ASSIGNMENT_MEMBERS",
                     "RESULT_SCHEMA", "RESULT_MEMBERS", "RESULT_OUTCOMES",
                     "HOLD_SCHEMA", "HOLD_MEMBERS", "HOLD_REASONS",
                     "ASSIGNMENT_TARGET", "RESULT_TARGET",
                     "ASSIGNMENT_DOCUMENT", "RESULT_DOCUMENT"):
            with self.subTest(name=name):
                self.assertEqual(getattr(contract, name),
                                 getattr(runtime, name))
        self.assertEqual(contract.MAX_RESULT_BYTES, runtime.MAX_DELIVERY_BYTES)
        self.assertEqual(contract.MAX_REPORT_BYTES, runtime.MAX_DELIVERY_BYTES)
        self.assertEqual(contract.BUNDLE_TARGET, SOURCE_TARGET)

    def test_the_eligibility_members_are_the_admission_owners_own(self):
        from baton_v12.integration import admission
        import inspect

        source = inspect.getsource(admission.resolved_account)
        for member in contract.ELIGIBILITY_MEMBERS:
            with self.subTest(member=member):
                self.assertIn(f'"{member}":', source)
        self.assertEqual(len(contract.ELIGIBILITY_MEMBERS), 15)

    def test_the_worker_contract_imports_no_manager_package(self):
        """The packaging claim, proved by an interpreter that cannot cheat."""
        script = ("import sys, json\n"
                  "sys.path = [%r]\n"
                  "import integration_contract as one\n"
                  "print(json.dumps(sorted(\n"
                  "    name for name in sys.modules\n"
                  "    if name.split('.')[0] in ('baton_v12', 'tools',\n"
                  "                              'source_profiles'))))\n"
                  % str(WORKER))
        answer = subprocess.run([sys.executable, "-I", "-c", script],
                                capture_output=True, text=True, timeout=120,
                                cwd=str(WORKER))
        self.assertEqual(answer.returncode, 0, answer.stderr)
        self.assertEqual(json.loads(answer.stdout), [])


class ReadBackCase(unittest.TestCase):
    """One real bundle on disk, composed the way the producer composes one."""

    def setUp(self):
        self._root = tempfile.TemporaryDirectory(prefix="v12-read-back-")
        self.addCleanup(self._root.cleanup)
        self.root = self._root.name
        self.place = os.path.join(self.root, "bundle")

    def refused(self, action, *operands, **named):
        with self.assertRaises(contract.BundleRefusal) as caught:
            action(*operands, **named)
        return caught.exception

    def build(self, **changed):
        from baton_v12.contracts.canonical import canonical_bytes

        payload = b"print('after')\n"
        address = digest_of_bytes(payload).split(":", 1)[1]
        rows = changed.pop("paths", [
            {"path": "src/edited.py", "operation": "edit",
             "base": {"object": object_name(b"print('before')\n"),
                      "blob": digest_of_bytes(b"print('before')\n")
                              .split(":", 1)[1],
                      "bytes": 16, "mode": "100644"},
             "candidate": {"object": object_name(payload), "blob": address,
                           "bytes": len(payload), "mode": "100644"}}])
        envelope = {
            "schema": contract.BUNDLE_SCHEMA,
            "assignment_digest": "sha256:" + "1" * 64,
            "launch": {"schema": launch_module.LAUNCH_SCHEMA, "role": "impl",
                       "digest": "sha256:" + "2" * 64},
            "eligibility": {name: "x" for name in
                            contract.ELIGIBILITY_MEMBERS},
            "checkpoint": {"line_id": "line-1", "checkpoint_id": "cp-1",
                           "verdict_id": "v-1",
                           "checkpoint_digest": "sha256:" + "3" * 64,
                           "evidence": evidence()},
            "evidence": [],
            "instructions": {"digest": digest_of_bytes(INSTRUCTIONS)
                                       .split(":", 1)[1],
                             "bytes": len(INSTRUCTIONS)},
            "paths": rows}
        envelope.update(changed)
        os.makedirs(os.path.join(self.place, contract.EVIDENCE_DIRECTORY))
        os.makedirs(os.path.join(self.place, contract.BLOB_DIRECTORY))
        if envelope["evidence"] == []:
            for name in contract.EVIDENCE_DOCUMENTS:
                body = canonical_bytes({"name": name})
                envelope["evidence"].append(
                    {"name": name,
                     "digest": digest_of_bytes(body).split(":", 1)[1],
                     "bytes": len(body)})
                self.write(contract.EVIDENCE_DIRECTORY, name, body)
        for row in rows:
            for side in ("base", "candidate"):
                if row[side]:
                    body = (b"print('before')\n" if side == "base"
                            else payload)
                    self.write(contract.BLOB_DIRECTORY, row[side]["blob"],
                               body)
        self.write(contract.INSTRUCTIONS_DOCUMENT, INSTRUCTIONS)
        self.write(contract.ENVELOPE_DOCUMENT, canonical_bytes(envelope))
        return envelope

    def write(self, *parts):
        payload = parts[-1]
        place = os.path.join(self.place, *parts[:-1])
        with open(place, "wb") as handle:
            handle.write(payload)
        return place


class TheWorkerReadsOnlyWhatTheEnvelopeNames(ReadBackCase):

    def test_a_whole_bundle_reads_back_as_its_own_documents(self):
        composed = self.build()
        taken = contract.read_bundle(self.place)
        self.assertEqual(taken["envelope"], composed)
        self.assertEqual(taken["instructions"], INSTRUCTIONS)
        self.assertEqual(sorted(taken["evidence"]),
                         sorted(contract.EVIDENCE_DOCUMENTS))
        row = taken["envelope"]["paths"][0]
        self.assertEqual(contract.bundle_blob(self.place, row["candidate"]),
                         b"print('after')\n")

    def test_the_blobs_are_not_resident_because_an_envelope_was_parsed(self):
        self.build()
        taken = contract.read_bundle(self.place)
        self.assertEqual(set(taken), {"root", "envelope", "instructions",
                                      "evidence"})

    def test_instruction_bytes_that_are_not_the_named_ones_refuse(self):
        self.build()
        self.write(contract.INSTRUCTIONS_DOCUMENT, INSTRUCTIONS + b"and more")
        caught = self.refused(contract.read_bundle, self.place)
        self.assertIn("not the ones the envelope names", str(caught))

    def test_evidence_that_is_not_the_named_document_refuses(self):
        self.build()
        self.write(contract.EVIDENCE_DIRECTORY, "tests.json", b"{}")
        self.refused(contract.read_bundle, self.place)

    def test_a_blob_that_is_not_its_own_address_refuses(self):
        composed = self.build()
        row = composed["paths"][0]
        self.write(contract.BLOB_DIRECTORY, row["candidate"]["blob"],
                   b"print('substituted')\n")
        self.refused(contract.bundle_blob, self.place, row["candidate"])

    def test_a_symlink_anywhere_in_the_bundle_refuses(self):
        self.build()
        os.unlink(os.path.join(self.place, contract.INSTRUCTIONS_DOCUMENT))
        os.symlink("/etc/hostname",
                   os.path.join(self.place, contract.INSTRUCTIONS_DOCUMENT))
        caught = self.refused(contract.read_bundle, self.place)
        self.assertIn("ordinary file", str(caught))

    def test_a_fifo_refuses_instead_of_blocking(self):
        self.build()
        place = os.path.join(self.place, contract.EVIDENCE_DIRECTORY,
                             "tests.json")
        os.unlink(place)
        os.mkfifo(place)
        caught = self.refused(contract.read_bundle, self.place)
        self.assertIn("regular file", str(caught))

    def test_an_oversized_document_refuses_rather_than_truncating(self):
        self.build()
        self.write(contract.ENVELOPE_DOCUMENT,
                   b"x" * (contract.MAX_ENVELOPE_BYTES + 1))
        caught = self.refused(contract.read_bundle, self.place)
        self.assertIn("never truncated", str(caught))

    def test_invalid_json_invalid_utf8_and_duplicate_names_refuse(self):
        for payload, expected in (
                (b"{not json", "readable JSON"),
                (b'{"schema": "\xff\xfe"}', "valid UTF-8"),
                (b'{"schema": "a", "schema": "b"}', "repeats a member name")):
            with self.subTest(expected=expected):
                self.build()
                self.write(contract.ENVELOPE_DOCUMENT, payload)
                caught = self.refused(contract.read_bundle, self.place)
                self.assertIn(expected, str(caught))
                import shutil
                shutil.rmtree(self.place)

    def test_an_envelope_member_this_build_does_not_know_refuses(self):
        self.build(extra="a channel")
        caught = self.refused(contract.read_bundle, self.place)
        self.assertIn("closed members", str(caught))

    def test_a_path_table_that_is_not_sorted_unique_and_disjoint_refuses(self):
        side = {"object": object_name(b"x"), "blob": digest_of_bytes(b"x")
                .split(":", 1)[1], "bytes": 1, "mode": "100644"}
        for rows, expected in (
                ([{"path": "b", "operation": "add", "base": None,
                   "candidate": dict(side)},
                  {"path": "a", "operation": "add", "base": None,
                   "candidate": dict(side)}], "not sorted"),
                ([{"path": "a", "operation": "add", "base": None,
                   "candidate": dict(side)},
                  {"path": "a", "operation": "add", "base": None,
                   "candidate": dict(side)}], "repeats a path"),
                ([{"path": "a", "operation": "add", "base": None,
                   "candidate": dict(side)},
                  {"path": "a/b", "operation": "add", "base": None,
                   "candidate": dict(side)}], "a path beneath it"),
                ([{"path": "a", "operation": "edit", "base": None,
                   "candidate": dict(side)}], "do not match that claim"),
                ([{"path": "../a", "operation": "add", "base": None,
                   "candidate": dict(side)}], "canonical spelling"),
                ([{"path": ".git/config", "operation": "add", "base": None,
                   "candidate": dict(side)}], "version-control metadata")):
            with self.subTest(expected=expected):
                self.build(paths=rows)
                caught = self.refused(contract.read_bundle, self.place)
                self.assertIn(expected, str(caught))
                import shutil
                shutil.rmtree(self.place)

    def test_an_unsupported_mode_refuses_in_the_reader_too(self):
        side = {"object": object_name(b"x"),
                "blob": digest_of_bytes(b"x").split(":", 1)[1], "bytes": 1,
                "mode": "120000"}
        self.build(paths=[{"path": "a", "operation": "add", "base": None,
                           "candidate": side}])
        caught = self.refused(contract.read_bundle, self.place)
        self.assertIn("regular reviewed files", str(caught))


class TheReaderProvesEveryComponentAndNotJustTheLast(ReadBackCase):
    """Review 2026-09-07T19:29:28Z [P1], restated as assertions.

    `O_NOFOLLOW` on a whole pathname rejects only the final component, so a
    symlinked `evidence/`, a symlinked `blobs/` and a symlink naming the whole
    bundle root were all accepted -- and every content digest still matched,
    because a digest says what the bytes are and nothing about which directory
    they were read out of. These are the reviewer's three reproductions plus
    the two adjacent ones.
    """

    def elsewhere(self, name):
        """Move one bundle member out of the bundle and link to it."""
        import shutil

        outside = os.path.join(self.root, "outside")
        os.makedirs(outside, exist_ok=True)
        held = os.path.join(self.place, name)
        moved = os.path.join(outside, name)
        shutil.move(held, moved)
        os.symlink(moved, held)
        return moved

    def test_a_symlinked_evidence_directory_is_refused(self):
        self.build()
        self.elsewhere(contract.EVIDENCE_DIRECTORY)
        caught = self.refused(contract.read_bundle, self.place)
        self.assertIn("directory of its own inside the bundle", str(caught))

    def test_a_symlinked_blob_directory_is_refused(self):
        composed = self.build()
        self.elsewhere(contract.BLOB_DIRECTORY)
        row = composed["paths"][0]
        caught = self.refused(contract.bundle_blob, self.place,
                              row["candidate"])
        self.assertIn("directory of its own inside the bundle", str(caught))

    def test_a_symlink_naming_the_whole_bundle_root_is_refused(self):
        self.build()
        linked = os.path.join(self.root, "linked-bundle")
        os.symlink(self.place, linked)
        caught = self.refused(contract.read_bundle, linked)
        self.assertIn("without following a link", str(caught))
        # AND THE SAME ROOT REACHED BY ITS OWN NAME STILL READS, so what the
        # case above measures is the link and not the material.
        self.assertEqual(contract.read_bundle(self.place)["instructions"],
                         INSTRUCTIONS)

    def test_a_substituted_directory_does_not_become_reachable(self):
        """Content that hashes correctly is still refused from another place."""
        composed = self.build()
        moved = self.elsewhere(contract.EVIDENCE_DIRECTORY)
        self.assertTrue(os.path.isfile(os.path.join(moved, "tests.json")))
        self.refused(contract.read_bundle, self.place)
        with open(os.path.join(moved, contract.EVIDENCE_DOCUMENTS[0]),
                  "rb") as handle:
            outside = contract.sha256_hex(handle.read())
        self.assertEqual(composed["evidence"][0]["digest"], outside)

    def test_an_ordinary_file_where_a_directory_belongs_is_refused(self):
        import shutil

        self.build()
        shutil.rmtree(os.path.join(self.place, contract.EVIDENCE_DIRECTORY))
        with open(os.path.join(self.place, contract.EVIDENCE_DIRECTORY),
                  "wb") as handle:
            handle.write(b"not a directory")
        caught = self.refused(contract.read_bundle, self.place)
        self.assertIn("directory of its own inside the bundle", str(caught))

    def test_the_assignment_namespace_is_read_the_same_way(self):
        from baton_v12.contracts.canonical import canonical_bytes

        namespace = os.path.join(self.root, "assignment")
        os.makedirs(namespace)
        document = {name: "x" for name in contract.ASSIGNMENT_MEMBERS}
        document["schema"] = contract.ASSIGNMENT_SCHEMA
        with open(os.path.join(namespace, contract.ASSIGNMENT_DOCUMENT),
                  "wb") as handle:
            handle.write(canonical_bytes(document))
        self.assertEqual(contract.read_assignment(namespace), document)
        linked = os.path.join(self.root, "linked-assignment")
        os.symlink(namespace, linked)
        caught = self.refused(contract.read_assignment, linked)
        self.assertIn("without following a link", str(caught))


class TheRootIsTraversedAndNotJustOpened(ReadBackCase):
    """Review 2026-09-07T19:51:54Z [P2]: opening the ROOT pathname whole left
    two ways through. An ancestor link was ordinary kernel traversal, and
    `alias + "/."` moved the link out of the final component so `O_NOFOLLOW`
    never saw it. Calling the root's ancestors somebody else's business
    narrowed a requirement I had already written down."""

    def test_the_valid_root_still_reads(self):
        """The control every refusal below is measured against."""
        composed = self.build()
        self.assertEqual(contract.read_bundle(self.place)["envelope"],
                         composed)
        self.assertEqual(
            contract.bundle_blob(self.place,
                                 composed["paths"][0]["candidate"]),
            b"print('after')\n")

    def test_an_alias_with_a_trailing_dot_is_refused(self):
        composed = self.build()
        alias = os.path.join(self.root, "alias")
        os.symlink(self.place, alias)
        for supplied in (alias, alias + "/.", alias + "/./",
                         self.place + "/."):
            with self.subTest(supplied=supplied):
                self.refused(contract.read_bundle, supplied)
                self.refused(contract.bundle_blob, supplied,
                             composed["paths"][0]["candidate"])

    def test_a_root_reached_through_a_linked_ancestor_is_refused(self):
        import shutil

        composed = self.build()
        parent = os.path.join(self.root, "parent")
        os.makedirs(parent)
        shutil.move(self.place, os.path.join(parent, "bundle"))
        linked = os.path.join(self.root, "linked-parent")
        os.symlink(parent, linked)
        through = os.path.join(linked, "bundle")
        caught = self.refused(contract.read_bundle, through)
        self.assertIn("without following a link", str(caught))
        self.refused(contract.bundle_blob, through,
                     composed["paths"][0]["candidate"])
        # AND THE SAME MATERIAL BY ITS OWN NAME STILL READS.
        self.assertEqual(
            contract.read_bundle(os.path.join(parent, "bundle"))["envelope"],
            composed)

    def test_a_noncanonical_spelling_is_refused_before_anything_is_opened(self):
        self.build()
        for supplied in (self.place + "/", self.place + "//",
                         os.path.join(self.place, "evidence", "..") ,
                         self.place.replace("/", "//", 1),
                         "relative/bundle", ""):
            with self.subTest(supplied=supplied):
                self.refused(contract.read_bundle, supplied)

    def test_the_assignment_reader_traverses_the_same_way(self):
        from baton_v12.contracts.canonical import canonical_bytes

        namespace = os.path.join(self.root, "assignment")
        os.makedirs(namespace)
        document = {name: "x" for name in contract.ASSIGNMENT_MEMBERS}
        document["schema"] = contract.ASSIGNMENT_SCHEMA
        with open(os.path.join(namespace, contract.ASSIGNMENT_DOCUMENT),
                  "wb") as handle:
            handle.write(canonical_bytes(document))
        self.assertEqual(contract.read_assignment(namespace), document)
        alias = os.path.join(self.root, "alias-assignment")
        os.symlink(namespace, alias)
        self.refused(contract.read_assignment, alias + "/.")


class TheBundleBoundsAreDerivedAndReconciled(ReadBackCase):

    def test_the_path_bound_is_derived_from_the_manifest_bound(self):
        self.assertEqual(contract.MAX_BUNDLE_FILES, 512)
        self.assertEqual(contract.FIXED_FILES,
                         2 + len(contract.EVIDENCE_DOCUMENTS))
        self.assertEqual(
            contract.MAX_PATHS,
            (contract.MAX_BUNDLE_FILES - contract.FIXED_FILES) // 2)
        # THE EXACT MAXIMUM FITS AND ONE MORE DOES NOT.
        self.assertLessEqual(
            contract.FIXED_FILES + 2 * contract.MAX_PATHS,
            contract.MAX_BUNDLE_FILES)
        self.assertGreater(
            contract.FIXED_FILES + 2 * (contract.MAX_PATHS + 1),
            contract.MAX_BUNDLE_FILES)
        self.assertEqual(producer.MAX_PATHS, contract.MAX_PATHS)
        self.assertEqual(producer.MAX_BUNDLE_FILES,
                         contract.MAX_BUNDLE_FILES)

    def side(self, payload, mode="100644"):
        return {"object": object_name(payload),
                "blob": digest_of_bytes(payload).split(":", 1)[1],
                "bytes": len(payload), "mode": mode}

    def test_one_content_shared_by_two_rows_is_counted_once(self):
        """The producer totals unique content and the reader now does too."""
        payload = b"print('after')\n"
        rows = [{"path": "src/a.py", "operation": "add", "base": None,
                 "candidate": self.side(payload)},
                {"path": "src/b.py", "operation": "add", "base": None,
                 "candidate": self.side(payload)}]
        self.build(paths=rows)
        taken = contract.read_bundle(self.place)
        self.assertEqual(len(taken["envelope"]["paths"]), 2)
        self.assertEqual(taken["envelope"]["paths"][0]["candidate"]["blob"],
                         taken["envelope"]["paths"][1]["candidate"]["blob"])

    def test_two_byte_counts_for_one_content_address_refuse(self):
        payload = b"print('after')\n"
        other = dict(self.side(payload), bytes=len(payload) + 1)
        rows = [{"path": "src/a.py", "operation": "add", "base": None,
                 "candidate": self.side(payload)},
                {"path": "src/b.py", "operation": "add", "base": None,
                 "candidate": other}]
        self.build(paths=rows)
        caught = self.refused(contract.read_bundle, self.place)
        self.assertIn("one address is one content", str(caught))


class TheProviderReportIsBoundedAndClosed(unittest.TestCase):

    def report(self, **changed):
        held = {"schema": contract.REPORT_SCHEMA,
                "assignment_digest": "sha256:" + "1" * 64,
                "bundle_digest": "sha256:" + "2" * 64,
                "outcome": "imported", "phase": "verification",
                "paths": ["src/edited.py"],
                "verification": {"argv": ["python3", "harness.py"],
                                 "status": 0},
                "code": None}
        held.update(changed)
        return json.dumps(held).encode("utf-8")

    def refused(self, payload):
        with self.assertRaises(contract.BundleRefusal) as caught:
            contract.check_report(payload)
        return caught.exception

    def test_a_well_formed_report_is_taken_as_a_claim(self):
        taken = contract.check_report(self.report())
        self.assertEqual(taken["outcome"], "imported")
        self.assertEqual(taken["code"], None)

    def test_an_imported_report_carries_no_code_and_a_held_one_must(self):
        self.refused(self.report(code="partial-import"))
        self.refused(self.report(outcome="held", code=None))
        self.refused(self.report(outcome="held", code="invented-code"))
        contract.check_report(self.report(outcome="held",
                                          code="partial-import"))

    def test_an_unrun_verification_is_null_and_not_a_failure(self):
        taken = contract.check_report(
            self.report(verification={"argv": ["python3"], "status": None}))
        self.assertIsNone(taken["verification"]["status"])
        self.refused(self.report(verification={"argv": [], "status": 0}))
        self.refused(self.report(verification={"argv": ["a"], "status": True}))

    def test_an_oversized_or_foreign_report_refuses(self):
        self.refused(b"x" * (contract.MAX_REPORT_BYTES + 1))
        self.refused(self.report(schema="baton.integration-report/2"))
        self.refused(self.report(outcome="integrated"))
        self.refused(self.report(phase="afterwards"))

    def test_reported_paths_are_sorted_unique_and_safe(self):
        self.refused(self.report(paths=["b", "a"]))
        self.refused(self.report(paths=["a", "a"]))
        self.refused(self.report(paths=["../a"]))
        self.refused(self.report(paths=[".git/config"]))


# -- the real owners --------------------------------------------------------


class ProducerCase(unittest.TestCase):
    """The real admission world, driven rather than described.

    COMPOSED AND NOT SUBCLASSED, and the import is inside the method. A
    module-level `TestCase` binding is collected by the loader and a subclass
    re-runs every case of its parent under a second name; both inflations
    happened in this campaign and both are avoided deliberately here.
    """

    def setUp(self):
        from unittest import mock

        from baton_v12.source_profiles import GIT_PROFILE
        from tests.integration.test_driver import _OrdinaryAdmissionWorld
        from tests.job_manager.test_review_driver import Profile

        # THE ACCEPTED WORLD'S CHECKPOINT PROFILE IS A MANAGER-SIDE FAKE
        # standing in for `GitCheckpointProfile`; it answers the REAL object
        # names a real repository holds and keeps every lifecycle rule, and its
        # NAME is the only thing that says "reference" rather than "git". This
        # patches that one attribute for the duration, so the line row, the
        # checkpoint row and the sealed evidence all agree on the profile a
        # Git deployment configures. No behaviour is replaced and the file is
        # not edited; the producer's own rule -- that it reads Git checkpoints
        # and refuses any other profile -- stays exactly as written, and
        # `test_evidence_of_another_profile_or_another_shape_refuses` drives
        # it.
        patched = mock.patch.object(Profile, "name", GIT_PROFILE)
        patched.start()
        self.addCleanup(patched.stop)
        self.world = _OrdinaryAdmissionWorld(self)
        # THE THREE POLICY RECEIPTS, WRITTEN BY THE REAL AUTHORITY SESSIONS.
        # `resolved_account` refuses a proposal that has none, so a bundle can
        # only be composed once the deployment has actually recorded them --
        # which is the world's own `_accepted_receipts` call, not a fixture
        # shortcut around it.
        self.world.receipts()
        self.destination = os.path.join(self.world.owner.root, "bundle")
        self.checkpoint = self.world.owner.profile
        self.accepted = self.world.evidence()
        held = self.world.owner.observed
        from baton_v12.worker_manager.review_cycles import line_of

        self.line = line_of(self.world.manager, self.world.line_id)
        self.objects = Objects(
            os.path.join(self.world.owner.root, "seam"),
            self.line["line_path"])
        self.objects.bind(self.line["line_path"])
        self.addCleanup(self.objects.release)
        self.objects.revision(held["base"], BASE_TREE)
        self.objects.revision(held["head"], held["tree"])
        self.objects.tree(BASE_TREE, {})
        self.objects.tree(held["tree"],
                          {one: ("100644", b"the reviewed candidate\n")
                           for one in self.evidence()["paths"]})
        self.profile = integration_profile(
            instructions_digest=digest_of_bytes(INSTRUCTIONS))
        self.launch = launch_module.launch_document(
            session="session-token", contract="baton.worker-control/1",
            role="integrator")
        self.assignment = {
            "schema": runtime.ASSIGNMENT_SCHEMA,
            "canonical_target_id": self.world.target,
            "entry_id": "entry-bundle", "lease_id": "lease-bundle",
            "fence": 1, "attempt_id": "attempt-bundle",
            "integrator_participant": self.profile["integrator_participant"],
            "profile_kind": self.profile["profile_kind"],
            "profile_version": self.profile["profile_version"],
            "instructions_digest": self.profile["instructions_digest"],
            "target_access": "writable"}

    def evidence(self):
        from baton_v12.worker_manager.review_cycles import integration_checkpoint

        return integration_checkpoint(
            self.world.manager, self.world.line_id)["evidence"]

    def compose(self, **changed):
        operands = {"manager": self.world.manager, "jobs": self.world.jobs,
                    "authority": self.world.authority_read,
                    "checkpoint_profile": self.checkpoint,
                    "integration_profile": self.profile,
                    "assignment": self.assignment, "launch": self.launch,
                    "instructions": INSTRUCTIONS,
                    "line_id": self.world.line_id,
                    "proposal_id": self.world.proposal_id,
                    "runner": self.objects}
        place = changed.pop("destination", self.destination)
        operands.update(changed)
        return producer.compose_bundle(place, **operands)

    def refused(self, **changed):
        with self.assertRaises(ContractRefusal) as caught:
            self.compose(**changed)
        return caught.exception


class TheProducerComposesFromRealOwners(ProducerCase):

    def test_the_envelope_carries_the_owners_own_answers(self):
        answer = self.compose()
        taken = contract.read_bundle(answer["root"])
        envelope = taken["envelope"]
        from baton_v12.integration.admission import resolved_account

        self.assertEqual(
            envelope["eligibility"],
            resolved_account(self.world.manager, self.world.jobs,
                             self.world.authority_read,
                             line_id=self.world.line_id,
                             proposal_id=self.world.proposal_id))
        self.assertEqual(envelope["eligibility"], answer["eligibility"])
        self.assertEqual(envelope["checkpoint"]["evidence"], self.evidence())
        self.assertEqual(envelope["assignment_digest"],
                         runtime.assignment_digest(self.assignment))
        self.assertEqual(envelope["launch"],
                         {"schema": self.launch["schema"],
                          "role": self.launch["role"],
                          "digest": digest(self.launch)})

    def test_no_live_session_token_reaches_the_bundle(self):
        """The launch's SESSION is a credential and the bundle carries a
        digest of the document instead of the document."""
        answer = self.compose()
        for root, _, names in os.walk(answer["root"]):
            for name in names:
                with open(os.path.join(root, name), "rb") as handle:
                    self.assertNotIn(b"session-token", handle.read())

    def test_the_evidence_projections_are_the_public_readers_answers(self):
        answer = self.compose()
        held = contract.read_bundle(answer["root"])["evidence"]
        self.assertEqual(sorted(held), sorted(contract.EVIDENCE_DOCUMENTS))
        self.assertEqual(held["tests.json"]["observation"],
                         self.world.observation)
        self.assertEqual(held["proposal.json"]["proposal_id"],
                         self.world.proposal_id)
        self.assertEqual(sorted(held["receipts.json"]),
                         ["approval", "review", "verification"])
        self.assertEqual(held["review.json"]["disposition"], "accepted")
        self.assertEqual(held["job.json"]["scope_digest"],
                         answer["eligibility"]["scope_digest"])
        self.assertEqual(held["checkpoint.json"]["evidence"], self.evidence())

    def test_every_published_byte_is_read_only_and_measured(self):
        answer = self.compose()
        measured = []
        for root, directories, names in os.walk(answer["root"]):
            for one in directories:
                self.assertEqual(
                    stat.S_IMODE(os.stat(os.path.join(root, one)).st_mode),
                    producer.BUNDLE_DIR)
            for one in names:
                place = os.path.join(root, one)
                self.assertEqual(stat.S_IMODE(os.stat(place).st_mode),
                                 producer.BUNDLE_FILE)
                with open(place, "rb") as handle:
                    payload = handle.read()
                measured.append(
                    {"path": os.path.relpath(place, answer["root"]),
                     "bytes": len(payload),
                     "digest": digest_of_bytes(payload)})
        self.assertEqual(
            stat.S_IMODE(os.stat(answer["root"]).st_mode),
            producer.BUNDLE_DIR)
        measured.sort(key=lambda one: one["path"].encode("utf-8"))
        self.assertEqual(measured, answer["manifest"])
        self.assertEqual(answer["bundle_digest"], digest(measured))

    def test_the_answer_binds_the_directory_and_not_a_pathname(self):
        from baton_v12.worker_manager.source_boundary import NominatedSource

        answer = self.compose()
        self.assertIs(type(answer["source"]), NominatedSource)
        held = os.stat(answer["root"])
        self.assertEqual((answer["source"].device, answer["source"].inode),
                         (held.st_dev, held.st_ino))

    def test_an_existing_destination_is_never_appended_to(self):
        self.compose()
        caught = self.refused()
        self.assertEqual((caught.category, caught.code),
                         ("refused", "operation-collision"))

    def test_an_abandoned_staging_directory_refuses(self):
        os.mkdir(self.destination + ".incomplete")
        caught = self.refused()
        self.assertEqual((caught.category, caught.code),
                         ("refused", "operation-collision"))

    def test_nothing_consumable_survives_a_refusal(self):
        caught = self.refused(instructions=b"other instructions")
        self.assertIn("instruction bytes", str(caught))
        self.assertFalse(os.path.exists(self.destination))
        self.assertFalse(os.path.exists(self.destination + ".incomplete"))

    def test_a_missing_retained_object_refuses_before_publication(self):
        self.objects.trees[self.world.owner.observed["tree"]] = {}
        caught = self.refused()
        self.assertEqual((caught.category, caught.code),
                         ("refused", "precondition"))
        self.assertFalse(os.path.exists(self.destination))

    def test_a_foreign_assignment_launch_or_profile_refuses(self):
        self.refused(assignment=dict(self.assignment, profile_version=2))
        self.refused(assignment=dict(self.assignment,
                                     schema="baton.v12.something/1"))
        self.refused(launch={"schema": self.launch["schema"]})
        self.refused(integration_profile=dict(self.profile, schema="other"))

    def test_a_proposal_the_owners_do_not_know_refuses(self):
        caught = self.refused(proposal_id="proposal-nobody-published")
        self.assertEqual(caught.category, "refused")
        self.assertFalse(os.path.exists(self.destination))

    def test_the_line_directory_must_be_the_recorded_one(self):
        import shutil

        line = self.line["line_path"]
        moved = line + "-moved"
        shutil.move(line, moved)
        os.mkdir(line)
        caught = self.refused()
        self.assertEqual((caught.category, caught.code),
                         ("runtime-observation", "identity-mismatch"))


class TheProducerLooksAgainAfterItHasRead(ProducerCase):
    """Review 2026-09-07T19:29:28Z [P1]: nothing was re-resolved after the
    extraction, so a line directory replaced underneath it was published from
    without a word. These drive the reviewer's own seam."""

    def replacement(self):
        """Move the recorded line aside and put a different directory there."""
        import shutil

        place = self.line["line_path"]
        moved = place + "-moved"
        shutil.move(place, moved)
        os.mkdir(place)
        return moved

    def test_a_line_replaced_during_extraction_refuses(self):
        before = os.stat(self.line["line_path"])
        self.objects.on_first = self.replacement
        caught = self.refused()
        after = os.stat(self.line["line_path"])
        self.assertNotEqual((before.st_dev, before.st_ino),
                            (after.st_dev, after.st_ino))
        self.assertEqual((caught.category, caught.code),
                         ("runtime-observation", "identity-mismatch"))
        self.assertFalse(os.path.exists(self.destination))
        self.assertFalse(os.path.exists(self.destination + ".incomplete"))

    def test_an_accepted_account_that_drifts_during_extraction_refuses(self):
        """A real Job store write, through the owner admission reads."""
        import json as _json

        def widen():
            self.world.jobs._connection.execute(
                "UPDATE jobs SET test_scope = ?",
                (_json.dumps(["v12/python/tests/integration",
                              "v12/python/tests/tools"]),))
            self.world.jobs._connection.commit()

        self.objects.on_first = widen
        caught = self.refused()
        self.assertEqual((caught.category, caught.code),
                         ("runtime-observation", "identity-mismatch"))
        self.assertIn("accepted account changed", str(caught))
        self.assertFalse(os.path.exists(self.destination))

    def test_an_eligibility_withdrawn_during_extraction_refuses(self):
        def withdraw():
            self.world.manager._connection.execute(
                "DELETE FROM integration_eligibility WHERE line_id = ?",
                (self.world.line_id,))
            self.world.manager._connection.commit()

        self.objects.on_first = withdraw
        caught = self.refused()
        self.assertEqual(caught.category, "refused")
        self.assertFalse(os.path.exists(self.destination))

    def test_the_unchanged_world_still_composes(self):
        """The control for the three above: no drift, one bundle."""
        answer = self.compose()
        self.assertTrue(os.path.isdir(answer["root"]))


class TheManifestIsRepresentableBeforeAnythingIsPublished(ProducerCase):
    """Review 2026-09-07T19:29:28Z [P1]: 252 two-sided edits published 513
    files and only then refused, leaving a consumable destination and no
    digest.

    THE WIDE PATH SET IS A STRUCTURAL FIXTURE AND NOT A REAL HISTORY, said
    plainly because the reviewer said it about their own probe: the real
    accepted world has one reviewed path, and these substitute a coherent
    N-path resolution derived from that real one. What they measure is the
    publication bound, not an Authority that ever approved 251 paths.
    """

    def widened(self, count):
        import copy
        from unittest import mock

        real = producer._accepted_evidence(
            self.world.manager, self.world.jobs, self.world.authority_read,
            line_id=self.world.line_id, proposal_id=self.world.proposal_id,
            checkpoint_profile=self.checkpoint)
        paths = sorted(f"src/{index:04d}.py" for index in range(count))
        held = digest(paths)
        evidence = dict(real["checkpoint"]["evidence"], paths=paths,
                        path_set_digest=held)
        projection = {
            "account": dict(real["account"], path_set_digest=held),
            "line": real["line"],
            "checkpoint": dict(real["checkpoint"], evidence=evidence),
            "documents": dict(
                real["documents"],
                **{"checkpoint.json": dict(real["documents"]["checkpoint.json"],
                                           evidence=evidence,
                                           path_set_digest=held)})}
        # EVERY ROW A TWO-SIDED EDIT WITH DISTINCT CONTENT, which is the worst
        # case the bound is derived from: two blobs per path.
        self.objects.tree(BASE_TREE,
                          {one: ("100644", f"base {one}\n".encode())
                           for one in paths})
        self.objects.tree(self.world.owner.observed["tree"],
                          {one: ("100644", f"head {one}\n".encode())
                           for one in paths})
        patched = mock.patch.object(
            producer, "_accepted_evidence",
            side_effect=lambda *a, **k: copy.deepcopy(projection))
        patched.start()
        self.addCleanup(patched.stop)
        return paths

    def test_the_exact_maximum_publishes_and_measures(self):
        paths = self.widened(producer.MAX_PATHS)
        answer = self.compose()
        self.assertEqual(answer["path_count"], producer.MAX_PATHS)
        self.assertEqual(len(answer["manifest"]),
                         producer.FIXED_FILES + 2 * producer.MAX_PATHS)
        self.assertEqual(len(answer["manifest"]), 511)
        self.assertEqual(answer["bundle_digest"], digest(answer["manifest"]))
        taken = contract.read_bundle(answer["root"])
        self.assertEqual([one["path"] for one in taken["envelope"]["paths"]],
                         paths)

    def test_one_path_past_the_maximum_refuses_with_nothing_published(self):
        """And it refuses at the PATH bound, which is where the derivation
        puts it: `_publish`'s file-count guard is the backstop behind it and
        is unreachable through this entry precisely because 251 is derived
        from 512 rather than chosen beside it."""
        self.widened(producer.MAX_PATHS + 1)
        caught = self.refused()
        self.assertIn(str(producer.MAX_PATHS), str(caught))
        self.assertIn("252 reviewed paths", str(caught))
        self.assertFalse(os.path.exists(self.destination))
        self.assertFalse(os.path.exists(self.destination + ".incomplete"))

    def test_a_retry_after_that_refusal_is_not_blocked_by_leftovers(self):
        self.widened(producer.MAX_PATHS + 1)
        self.refused()
        # The projection patch is per-case, so a second composition over the
        # same destination has to succeed on the real one-path world.
        from unittest import mock

        mock.patch.stopall()
        self.setUp()
        answer = self.compose()
        self.assertTrue(os.path.isdir(answer["root"]))

    def test_an_evidence_projection_above_its_bound_refuses(self):
        import copy
        from unittest import mock

        real = producer._accepted_evidence(
            self.world.manager, self.world.jobs, self.world.authority_read,
            line_id=self.world.line_id, proposal_id=self.world.proposal_id,
            checkpoint_profile=self.checkpoint)
        projection = copy.deepcopy(real)
        projection["documents"]["tests.json"] = {
            "padding": "x" * (producer.MAX_EVIDENCE_BYTES + 16)}
        patched = mock.patch.object(
            producer, "_accepted_evidence",
            side_effect=lambda *a, **k: copy.deepcopy(projection))
        patched.start()
        self.addCleanup(patched.stop)
        caught = self.refused()
        self.assertIn(str(producer.MAX_EVIDENCE_BYTES), str(caught))
        self.assertFalse(os.path.exists(self.destination))


class TheExtractionIsBoundToOneDirectory(ProducerCase):
    """Review 2026-09-07T19:51:54Z [P1]: the second nomination is DETECTION and
    not the binding review112857 asked for, and a substitution restored before
    that second look publishes with both measurements agreeing. I described
    the detection as if it closed the finding. It did not, and these drive the
    reviewer's own transient seam against the binding that replaces it."""

    def transient(self):
        """Swap the name for exactly one runner call, then put it back."""
        import shutil

        place = self.line["line_path"]
        parked = place + "-parked"
        shutil.move(place, parked)
        os.mkdir(place)
        self.substitute = os.stat(place)
        shutil.move(place, place + "-substitute")
        shutil.move(parked, place)

    def test_a_transient_swap_does_not_redirect_a_single_read(self):
        before = os.stat(self.line["line_path"])
        self.objects.on_first = self.transient
        answer = self.compose()
        after = os.stat(self.line["line_path"])
        self.assertTrue(os.path.samestat(before, after))
        self.assertNotEqual((self.substitute.st_dev, self.substitute.st_ino),
                            (before.st_dev, before.st_ino))
        # EVERY READ WENT THROUGH THE PROVED DIRECTORY. The seam records the
        # identity of the descriptor it was handed for each call, and the swap
        # is invisible to all of them because the name is not what was used.
        self.assertTrue(self.objects.directories)
        for held in self.objects.directories:
            self.assertEqual(held, (before.st_dev, before.st_ino))
        self.assertTrue(os.path.isdir(answer["root"]))
        contract.read_bundle(answer["root"])

    def test_no_composed_command_carries_the_repository_pathname(self):
        self.compose()
        self.assertTrue(self.objects.calls)
        for argv in self.objects.calls:
            self.assertNotIn("-C", argv)
            self.assertNotIn(self.line["line_path"], argv)
            self.assertEqual(argv[:2], ["git", "--no-optional-locks"])

    def test_a_pathname_is_not_a_directory_this_producer_reads_through(self):
        with self.assertRaises(ContractRefusal) as caught:
            producer.reviewed_path_table(self.objects,
                                         self.line["line_path"],
                                         self.evidence())
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("policy", "denied"))
        self.assertIn("resolved again on every use", str(caught.exception))
        place = os.path.join(self.world.owner.root, "not-a-directory")
        with open(place, "wb") as handle:
            handle.write(b"an ordinary file")
        holder = os.open(place, os.O_RDONLY)
        try:
            with self.assertRaises(ContractRefusal) as caught:
                producer.reviewed_path_table(self.objects, holder,
                                             self.evidence())
            self.assertEqual(caught.exception.code, "denied")
        finally:
            os.close(holder)


class TheSharedContentIsChargedOnce(ProducerCase):
    """Review 2026-09-07T19:51:54Z [P2]: the remaining budget was charged
    before the content address was known, so one blob two rows share was read
    twice and could refuse as oversized while adding nothing -- the producer
    refusing input its own reader accepts."""

    SHARED = b"shared-content\n"

    def two_paths(self, base=None, head=None):
        """Two added paths, by default holding the very same content."""
        paths = ["src/one.py", "src/two.py"]
        real = producer._accepted_evidence(
            self.world.manager, self.world.jobs, self.world.authority_read,
            line_id=self.world.line_id, proposal_id=self.world.proposal_id,
            checkpoint_profile=self.checkpoint)
        held = digest(paths)
        evidence = dict(real["checkpoint"]["evidence"], paths=paths,
                        path_set_digest=held)
        projection = {
            "account": dict(real["account"], path_set_digest=held),
            "line": real["line"],
            "checkpoint": dict(real["checkpoint"], evidence=evidence),
            "documents": dict(
                real["documents"],
                **{"checkpoint.json": dict(real["documents"]["checkpoint.json"],
                                           evidence=evidence,
                                           path_set_digest=held)})}
        self.objects.tree(BASE_TREE, {})
        content = head or {one: self.SHARED for one in paths}
        self.objects.tree(self.world.owner.observed["tree"],
                          {one: ("100644", content[one]) for one in paths})
        import copy
        from unittest import mock

        patched = mock.patch.object(
            producer, "_accepted_evidence",
            side_effect=lambda *a, **k: copy.deepcopy(projection))
        patched.start()
        self.addCleanup(patched.stop)
        return paths, evidence

    def scaled(self, limit):
        from unittest import mock

        for module in (producer, contract):
            patched = mock.patch.object(module, "MAX_BLOB_BYTES", limit)
            patched.start()
            self.addCleanup(patched.stop)

    def test_content_larger_than_half_the_limit_may_be_shared(self):
        """The reviewer's own scaled probe: five unique bytes under a bound of
        eight, referenced twice, which the reader has always accepted."""
        self.two_paths()
        self.scaled(len(self.SHARED) + 1)
        answer = self.compose()
        self.assertEqual(answer["blob_bytes"], len(self.SHARED))
        taken = contract.read_bundle(answer["root"])
        rows = taken["envelope"]["paths"]
        self.assertEqual(rows[0]["candidate"]["blob"],
                         rows[1]["candidate"]["blob"])
        self.assertEqual(
            contract.bundle_blob(answer["root"], rows[0]["candidate"]),
            self.SHARED)
        # ONE OBJECT, READ ONCE. The second reference costs no command at all.
        reads = [argv for argv in self.objects.calls
                 if argv[2:4] == ["cat-file", "blob"]]
        self.assertEqual(len(reads), 1)

    def test_the_exact_unique_maximum_publishes(self):
        paths, _ = self.two_paths(
            head={"src/one.py": b"aaaa", "src/two.py": b"bbbb"})
        self.scaled(8)
        answer = self.compose()
        self.assertEqual(answer["blob_bytes"], 8)
        self.assertEqual(len(contract.read_bundle(answer["root"])
                             ["envelope"]["paths"]), 2)

    def test_true_unique_overflow_still_refuses(self):
        self.two_paths(head={"src/one.py": b"aaaa", "src/two.py": b"bbbbb"})
        self.scaled(8)
        caught = self.refused()
        self.assertIn("8 blob bytes", str(caught))
        self.assertFalse(os.path.exists(self.destination))


if __name__ == "__main__":
    unittest.main()
