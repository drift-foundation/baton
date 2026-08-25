"""W6632 — the constrained OCI adapter core.

The acceptance this file answers to, from the bound record:

  golden Docker and Podman argv/inspect vectors sharing ONE worker-control
  vocabulary and rejecting unknown or contradictory engine data; exact labels
  and digests surviving restart reconciliation; stop, quiescent, destroyed and
  positive absence all DISTINCT; duplicate starts, stale identities and
  ambiguous multi-match listings failing closed without inferring authority
  from engine state.

The engine is a fake that records every vector and answers whatever the case
needs. That is the point rather than a compromise: the adapter's own boundary
is the vector it builds and the answer it reads, and a real daemon proves the
same thing more slowly and less exactly. The isolated mutable smoke test that
drives a real engine is its own cut, as the acceptance itself separates it.
"""

import json
import os
import re
import tempfile
import unittest

from baton_v12.contracts import ContractRefusal
from baton_v12.worker_manager import documents, oci
from baton_v12.worker_manager.oci import (ENGINES, LABEL_PREFIX,
                                          MAX_DIAGNOSTIC, RESTRICTIONS,
                                          ROOT_NAMES, EnginePort, OciAdapter,
                                          destroy_vector, inspect_vector,
                                          list_vector, run_vector, stop_vector)

IMAGE = "sha256:" + "a" * 64
# The assignment's own roots, as `assignment_workspace` answers with them, and
# the posture that decides which of them a container may see. Both are REQUIRED
# inputs since the 2026-08-25 ruling: roots alone cannot choose the topology.
ROOTS = {"inputs": "/srv/a-1/inputs", "workspace": "/srv/a-1/workspace",
         "git": "/srv/a-1/git"}
LABELS = {"runtime_attempt_id": "attempt-1",
          "authority_uuid": "2b077949c86e8bef24304f59c28ec398",
          "work_id": "2b077949-W4", "participant": "baton.claude",
          "generation": 1, "profile_digest": "sha256:" + "b" * 64,
          "adapter_digest": "sha256:" + "c" * 64}


class Engine:
    """A fake engine that records every vector and answers a script."""

    def __init__(self, answers=None):
        self.answers = list(answers or [])
        self.vectors = []

    def __call__(self, argv):
        self.vectors.append(list(argv))
        if self.answers:
            return self.answers.pop(0)
        return {"status": 0, "stdout": "", "stderr": ""}


def answer(status=0, stdout="", stderr=""):
    return {"status": status, "stdout": stdout, "stderr": stderr}


def listing(runtime_id="runtime-1", labels=None, engine="docker"):
    labels = LABELS if labels is None else labels
    reported = {f"{LABEL_PREFIX}{name}": str(value)
                for name, value in labels.items()}
    if engine == "podman":
        return json.dumps({"Id": runtime_id,
                           "Labels": ",".join(f"{key}={value}" for key, value
                                              in reported.items())})
    return json.dumps({"ID": runtime_id, "Labels": reported})


def inspection(running, runtime_id="runtime-1"):
    return json.dumps({"Id": runtime_id, "State": {"Running": running}})


class TheVectorsAreClosedAndOrdered(unittest.TestCase):
    """GOLDEN VECTORS. No shell, so nothing to escape out of."""

    def test_the_run_vector_is_exact_for_both_engines(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                argv = run_vector(engine, image_digest=IMAGE, labels=LABELS,
                                  assignment_roots=ROOTS, posture="execution", 
                                  name="baton-op-1")
                self.assertEqual(argv[:5],
                                 [engine, "run", "--detach", "--name",
                                  "baton-op-1"])
                # THE IMAGE IS LAST and is a digest, so no caller value can be
                # read as an argument to the engine itself.
                self.assertEqual(argv[-1], IMAGE)
                # 5 for the head, 20 for the restrictions, 14 for the seven
                # labels, 1 for the image and 1 for `--read-only`, which is the
                # only flag carrying no value.
                self.assertEqual(len(argv), 41)

    def test_every_restriction_is_present_and_unconditional(self):
        """A policy a caller can turn off is a default."""
        argv = run_vector("docker", image_digest=IMAGE, labels=LABELS,
                          assignment_roots=ROOTS, posture="execution", 
                          name="baton-op-1")
        # PAIRWISE, because two restrictions share the `--security-opt` flag
        # and two share `--tmpfs`: asking for the first occurrence would let a
        # second one go missing without this noticing.
        pairs = [(argv[at], argv[at + 1] if at + 1 < len(argv) else None)
                 for at in range(len(argv))]
        for flag, value in RESTRICTIONS:
            with self.subTest(flag=flag, value=value):
                if value is None:
                    self.assertIn(flag, argv)
                else:
                    self.assertIn((flag, value), pairs)
        self.assertIn("--read-only", argv)
        self.assertEqual(argv[argv.index("--network") + 1], "none")
        self.assertEqual(argv[argv.index("--user") + 1], "65532:65532")
        self.assertEqual(argv[argv.index("--cap-drop") + 1], "ALL")

    def test_the_labels_are_the_frozen_contracts_own_set_in_its_own_order(self):
        argv = run_vector("docker", image_digest=IMAGE, labels=LABELS,
                          assignment_roots=ROOTS, posture="execution", 
                          name="baton-op-1")
        written = [argv[at + 1] for at, piece in enumerate(argv)
                   if piece == "--label"]
        self.assertEqual(
            written,
            [f"{LABEL_PREFIX}{name}={LABELS[name]}"
             for name in documents.RUNTIME_LABELS],
            "the label order is the contract's, not a dict's")

    def test_a_label_set_that_is_not_the_contracts_is_refused(self):
        for what, labels in [("a missing member",
                              {name: value for name, value in LABELS.items()
                               if name != "work_id"}),
                             ("an invented member",
                              {**LABELS, "bearer": "secret"})]:
            with self.subTest(what=what):
                with self.assertRaises(ContractRefusal):
                    run_vector("docker", image_digest=IMAGE, labels=labels,
                               assignment_roots=ROOTS, posture="execution", 
                               name="baton-op-1")

    def test_a_label_carrying_a_line_break_is_refused(self):
        with self.assertRaises(ContractRefusal) as caught:
            run_vector("docker", image_digest=IMAGE,
                       assignment_roots=ROOTS, posture="execution", 
                       labels={**LABELS, "work_id": "W4\nW5"},
                       name="baton-op-1")
        self.assertIn("line break", caught.exception.message)

    def test_an_image_that_is_not_a_digest_is_refused(self):
        """A tag is a name somebody can move, and a runtime started from a
        moved tag is one nobody can say the contents of afterwards."""
        for image in ("worker:latest", "sha256:short", "", "sha256:" + "A" * 64):
            with self.subTest(image=image):
                with self.assertRaises(ContractRefusal):
                    run_vector("docker", image_digest=image, labels=LABELS,
                               assignment_roots=ROOTS, posture="execution", 
                               name="baton-op-1")

    def test_an_engine_this_adapter_does_not_speak_is_refused(self):
        for engine in ("kubectl", "docker ", "DOCKER", ""):
            with self.subTest(engine=engine):
                with self.assertRaises(ContractRefusal):
                    list_vector(engine, labels=LABELS)

    def test_the_query_vectors_name_one_exact_identity(self):
        self.assertEqual(inspect_vector("podman", runtime_id="r-1"),
                         ["podman", "inspect", "--type", "container",
                          "--format", "{{json .}}", "r-1"])
        self.assertEqual(stop_vector("docker", runtime_id="r-1"),
                         ["docker", "stop", "--time", "30", "r-1"])
        self.assertEqual(destroy_vector("docker", runtime_id="r-1"),
                         ["docker", "rm", "--force", "--volumes", "r-1"])

    def test_the_listing_filters_on_every_label(self):
        argv = list_vector("docker", labels=LABELS)
        filters = [argv[at + 1] for at, piece in enumerate(argv)
                   if piece == "--filter"]
        self.assertEqual(len(filters), len(documents.RUNTIME_LABELS))
        self.assertTrue(all(piece.startswith(f"label={LABEL_PREFIX}")
                            for piece in filters))

    def test_digest_and_generation_labels_keep_their_semantic_types(self):
        """The adapter reconciles these values, so text-shaped substitutes
        are not the exact profile, adapter, or assignment generation."""
        for name, value in (("profile_digest", "profile-latest"),
                            ("adapter_digest", "adapter-latest"),
                            ("generation", -1)):
            with self.subTest(name=name, value=value):
                with self.assertRaises(ContractRefusal):
                    run_vector("docker", image_digest=IMAGE,
                               labels={**LABELS, name: value},
                               assignment_roots=ROOTS, posture="execution",
                               name="baton-op-1")


class AMountIsCanonicalAndNeverTheHosts(unittest.TestCase):

    def mount(self, **overrides):
        one = {"source": "/srv/a-1/workspace", "target": "/workspace",
               "writable": True}
        one.update(overrides)
        return run_vector("docker", image_digest=IMAGE, labels=LABELS,
                          assignment_roots=ROOTS, posture="execution",
                          name="baton-op-1", mounts=[one])

    def test_a_writable_and_a_read_only_mount_are_spelled_apart(self):
        self.assertIn("type=bind,source=/srv/a-1/workspace,"
                      "target=/workspace,readonly=false",
                      self.mount())
        self.assertIn("type=bind,source=/srv/a-1/inputs,target=/inputs,readonly=true",
                      self.mount(source="/srv/a-1/inputs", target="/inputs",
                                 writable=False))

    def test_the_engine_and_the_hosts_own_state_are_never_mounted(self):
        """Each of these is a way to hand a worker the manager's own authority
        or the engine itself."""
        for source in ("/var/run/docker.sock", "/run/podman/podman.sock",
                       "/proc", "/sys/fs/cgroup", "/etc/shadow", "/root/.ssh",
                       "/dev/mem"):
            with self.subTest(source=source):
                with self.assertRaises(ContractRefusal) as caught:
                    self.mount(source=source)
                self.assertEqual(
                    (caught.exception.category, caught.exception.code),
                    ("policy", "denied"))

    def test_a_repository_outside_assignment_owned_roots_is_not_mountable(self):
        """A denylist cannot prove that a host path belongs to this assignment.

        Repository internals are explicitly outside the worker boundary even
        when their spelling does not happen to begin with a listed system
        prefix. The adapter needs the assignment-owned roots to distinguish
        them from legitimate inputs and workspace mounts.
        """
        with self.assertRaises(ContractRefusal) as caught:
            self.mount(source="/srv/repositories/baton/.git")
        self.assertEqual(
            (caught.exception.category, caught.exception.code),
            ("policy", "denied"))

    def test_a_path_that_is_not_canonical_is_refused(self):
        for what, one in [("a relative source", {"source": "ws"}),
                          ("a relative target", {"target": "workspace"}),
                          ("a traversal", {"source": "/srv/../etc"}),
                          ("an engine separator", {"source": "/srv/a:b"})]:
            with self.subTest(what=what):
                with self.assertRaises(ContractRefusal):
                    self.mount(**one)

    def test_a_mount_reaches_the_engine_only_in_canonical_spelling(self):
        argv = self.mount(source="/srv/a-1//workspace/./",
                          target="/workspace/./")
        rendered = argv[argv.index("--mount") + 1]
        self.assertEqual(
            rendered,
            "type=bind,source=/srv/a-1/workspace,target=/workspace,"
            "readonly=false")

    def test_only_this_assignments_own_material_is_mountable(self):
        """PROVED TO BE OURS, not proved not to be theirs.

        Ruled 2026-08-25, replacing a denylist. A denylist answers "is this one
        of the bad ones" when the rule is "is this one of OURS" -- so a
        repository path that happened not to match a listed prefix was
        mountable, and every new spelling needed a new entry.
        """
        for what, source in [
                ("a repository", "/srv/repositories/baton/objects"),
                ("another assignment's inputs", "/srv/a-2/inputs"),
                ("a root that merely shares a prefix", "/srv/a-1/inputs-2"),
                ("the host's own state", "/etc/shadow"),
                ("the engine", "/var/run/docker.sock")]:
            with self.subTest(what=what):
                with self.assertRaises(ContractRefusal) as caught:
                    self.mount(source=source)
                self.assertEqual(
                    (caught.exception.category, caught.exception.code),
                    ("policy", "denied"))
                self.assertIn("not this assignment's material",
                              caught.exception.message)

    def test_the_private_metadata_root_is_never_mountable(self):
        """A worker that could reach it could move another assignment's
        refs."""
        with self.assertRaises(ContractRefusal) as caught:
            self.mount(source=ROOTS["git"])
        self.assertEqual(caught.exception.code, "denied")

    def test_delivered_inputs_are_evidence_rather_than_scratch(self):
        """Read-only under `inputs`, read/write only under `workspace`."""
        self.assertIn("source=/srv/a-1/inputs/tree,target=/inputs,"
                      "readonly=true",
                      "".join(self.mount(source="/srv/a-1/inputs/tree",
                                         target="/inputs", writable=False)))
        with self.assertRaises(ContractRefusal) as caught:
            self.mount(source="/srv/a-1/inputs/tree", target="/inputs",
                       writable=True)
        self.assertIn("writes only under its workspace",
                      caught.exception.message)

    def test_a_consent_container_mounts_nothing(self):
        """ROOTS ALONE CANNOT CHOOSE THE TOPOLOGY, which is why the posture is
        its own required input: a consent container that could see the inputs
        would be the promotion the two-container topology exists to prevent.
        """
        with self.assertRaises(ContractRefusal) as caught:
            run_vector("docker", image_digest=IMAGE, labels=LABELS,
                       assignment_roots=ROOTS, posture="consent",
                       name="baton-op-1",
                       mounts=[{"source": "/srv/a-1/inputs",
                                "target": "/inputs", "writable": False}])
        self.assertIn("mounts nothing", caught.exception.message)
        # ...and it still starts, with no mount at all.
        argv = run_vector("docker", image_digest=IMAGE, labels=LABELS,
                          assignment_roots=ROOTS, posture="consent",
                          name="baton-op-1")
        self.assertNotIn("--mount", argv)

    def test_both_roots_and_posture_are_required_and_closed(self):
        for what, call in [
                ("no roots", lambda: run_vector(
                    "docker", image_digest=IMAGE, labels=LABELS,
                    posture="execution", name="baton-op-1",
                    assignment_roots={"inputs": "/srv/a-1/inputs"})),
                ("a root that is not absolute", lambda: run_vector(
                    "docker", image_digest=IMAGE, labels=LABELS,
                    posture="execution", name="baton-op-1",
                    assignment_roots={**ROOTS, "workspace": "workspace"})),
                ("a posture this build does not have", lambda: run_vector(
                    "docker", image_digest=IMAGE, labels=LABELS,
                    assignment_roots=ROOTS, posture="admin",
                    name="baton-op-1"))]:
            with self.subTest(what=what):
                with self.assertRaises(ContractRefusal):
                    call()

    def test_assignment_roots_cannot_overlap(self):
        """A source inside two roots has no unique posture authority.

        The approved API explicitly refuses ambiguous/overlapping roots. If
        workspace sits below inputs, `_mounts` currently classifies it by the
        first matching root and silently changes whether it may be writable.
        """
        overlapping = {"inputs": "/srv/a-1", "workspace": "/srv/a-1/workspace",
                       "git": "/srv/a-1/git"}
        with self.assertRaises(ContractRefusal):
            run_vector("docker", image_digest=IMAGE, labels=LABELS,
                       assignment_roots=overlapping, posture="execution",
                       name="baton-op-1")

    def test_a_symlink_descendant_cannot_escape_an_assignment_root(self):
        """Lexical containment is not mount authority.

        The engine resolves a bind source on the host. A symlink planted under
        the writable workspace must not turn an apparently owned spelling into
        an arbitrary host mount.
        """
        with tempfile.TemporaryDirectory() as root:
            roots = {name: os.path.join(root, name)
                     for name in ("inputs", "workspace", "git")}
            for place in roots.values():
                os.mkdir(place)
            outside = os.path.join(root, "outside")
            os.mkdir(outside)
            escape = os.path.join(roots["workspace"], "escape")
            os.symlink(outside, escape)
            with self.assertRaises(ContractRefusal):
                run_vector(
                    "docker", image_digest=IMAGE, labels=LABELS,
                    assignment_roots=roots, posture="execution",
                    name="baton-op-1",
                    mounts=[{"source": escape, "target": "/workspace",
                             "writable": True}])

    def test_the_engine_is_handed_what_this_adapter_proved(self):
        """The other half of resolving: proving the resolved path and then
        emitting the SPELLING would leave the engine free to resolve it again,
        which is the same defect with an extra step."""
        with tempfile.TemporaryDirectory() as root:
            real = os.path.join(root, "real")
            os.mkdir(real)
            for name in ROOT_NAMES:
                os.mkdir(os.path.join(real, name))
            linked = os.path.join(root, "linked")
            os.symlink(real, linked)
            roots = {name: os.path.join(linked, name) for name in ROOT_NAMES}
            tree = os.path.join(roots["workspace"], "tree")
            os.mkdir(tree)
            argv = run_vector(
                "docker", image_digest=IMAGE, labels=LABELS,
                assignment_roots=roots, posture="execution",
                name="baton-op-1",
                mounts=[{"source": tree, "target": "/workspace",
                         "writable": True}])
            rendered = argv[argv.index("--mount") + 1]
            self.assertIn(f"source={os.path.realpath(tree)},", rendered)
            self.assertNotIn(f"source={tree},", rendered)

    def test_two_roots_that_are_the_same_place_are_refused(self):
        """Equality is containment's degenerate case with the same defect: a
        source under it belongs to two roots at once."""
        same = dict(ROOTS)
        same["workspace"] = same["inputs"]
        with self.assertRaises(ContractRefusal) as caught:
            run_vector("docker", image_digest=IMAGE, labels=LABELS,
                       assignment_roots=same, posture="execution",
                       name="baton-op-1")
        self.assertIn("no unique posture authority", caught.exception.message)

    def test_a_symlinked_root_and_a_symlinked_source_agree(self):
        """Resolution is applied to BOTH sides or it decides nothing: a
        resolved source compared against an unresolved root would refuse every
        legitimate mount under a symlinked root."""
        with tempfile.TemporaryDirectory() as root:
            real = os.path.join(root, "real")
            os.makedirs(os.path.join(real, "workspace", "tree"))
            for name in ROOT_NAMES:
                if name != "workspace":
                    os.mkdir(os.path.join(real, name))
            linked = os.path.join(root, "linked")
            os.symlink(real, linked)
            roots = {name: os.path.join(linked, name) for name in ROOT_NAMES}
            argv = run_vector(
                "docker", image_digest=IMAGE, labels=LABELS,
                assignment_roots=roots, posture="execution",
                name="baton-op-1",
                mounts=[{"source": os.path.join(real, "workspace", "tree"),
                         "target": "/workspace", "writable": True}])
            self.assertIn("--mount", argv)

    def test_nested_mount_sources_and_targets_are_ambiguous(self):
        """No mount may hide or alias a second mount by containment."""
        cases = [
            ("sources",
             [{"source": "/srv/a-1/workspace/tree", "target": "/one",
               "writable": True},
              {"source": "/srv/a-1/workspace/tree/child", "target": "/two",
               "writable": True}]),
            ("targets",
             [{"source": "/srv/a-1/workspace/one", "target": "/workspace",
               "writable": True},
              {"source": "/srv/a-1/workspace/two",
               "target": "/workspace/child", "writable": True}]),
        ]
        for what, mounts in cases:
            with self.subTest(what=what):
                with self.assertRaises(ContractRefusal):
                    run_vector("docker", image_digest=IMAGE, labels=LABELS,
                               assignment_roots=ROOTS, posture="execution",
                               name="baton-op-1", mounts=mounts)

    def test_two_mounts_cannot_land_on_one_target(self):
        with self.assertRaises(ContractRefusal) as caught:
            run_vector("docker", image_digest=IMAGE, labels=LABELS,
                       assignment_roots=ROOTS, posture="execution",
                       name="baton-op-1",
                       mounts=[{"source": "/srv/a-1/workspace/a",
                                "target": "/w", "writable": True},
                               {"source": "/srv/a-1/inputs/b",
                                "target": "/w", "writable": False}])
        self.assertIn("would hide the first", caught.exception.message)


class Adapting(unittest.TestCase):

    # ONE RESOLVED IDENTITY, and it AGREES with `LABELS` — because that is
    # the contract now: what a delivery is started under and what its runtime
    # is labelled with are one account, and a fixture whose two halves
    # disagreed would make every case here refuse for the mismatch.
    IDENTITY = {"image_digest": IMAGE,
                "profile_digest": LABELS["profile_digest"],
                "adapter_digest": LABELS["adapter_digest"]}

    def adapter(self, *answers, engine="docker", identity=None):
        self.engine = Engine(answers)
        # The identity is passed THROUGH rather than copied, so a case may
        # hand this door something that is not a document at all -- which is
        # one of the things the door has to refuse.
        return OciAdapter(engine, self.engine,
                          identity=self.IDENTITY if identity is None
                          else identity,
                          assignment_roots=ROOTS,
                          posture="execution")


class OneDeliveryCarriesOneResolvedIdentity(Adapting):
    """Review: the adapter held an image digest and `start` took labels
    independently, so what was STARTED and what the runtime was LABELLED with
    were two accounts nothing compared — and reconciliation after a restart
    reads the labels and reasons about the image from them.

    One record owned at construction is what makes them one account.
    """

    def test_the_started_image_comes_from_the_resolved_identity(self):
        adapter = self.adapter(answer(stdout=""), answer(stdout="runtime-1\n"))
        adapter.start({"labels": dict(LABELS),
                       "operation_id": "runtime.start:1"})
        started = self.engine.vectors[-1]
        self.assertIn(IMAGE, started)
        # And the labels the engine was told to write are the same digests.
        rendered = " ".join(started)
        self.assertIn(f"{LABEL_PREFIX}profile_digest="
                      f"{LABELS['profile_digest']}", rendered)
        self.assertIn(f"{LABEL_PREFIX}adapter_digest="
                      f"{LABELS['adapter_digest']}", rendered)

    def test_labels_that_disagree_with_the_identity_are_refused(self):
        """The mismatch probe. A runtime labelled with a profile or adapter
        digest other than the one it is started under is a runtime
        reconciliation would describe wrongly for the rest of its life."""
        for name in ("profile_digest", "adapter_digest"):
            with self.subTest(member=name):
                adapter = self.adapter(answer(stdout=""))
                with self.assertRaises(ContractRefusal) as caught:
                    adapter.start({
                        "labels": dict(LABELS, **{name: "sha256:" + "9" * 64}),
                        "operation_id": "runtime.start:1"})
                self.assertEqual(
                    (caught.exception.category, caught.exception.code),
                    ("policy", "denied"))
                self.assertIn("one delivery carries one identity",
                              caught.exception.message)

    def test_nothing_is_started_when_the_identity_disagrees(self):
        """Refused BEFORE the engine is asked to run anything: a start that
        had already created a container and then refused would leave exactly
        the state no later reconciliation can undo."""
        adapter = self.adapter(answer(stdout=""))
        with self.assertRaises(ContractRefusal):
            adapter.start({"labels": dict(LABELS,
                                          profile_digest="sha256:" + "9" * 64),
                           "operation_id": "runtime.start:1"})
        self.assertTrue(all("run" not in vector
                            for vector in self.engine.vectors),
                        self.engine.vectors)

    def test_a_restart_finds_the_runtime_by_the_identity_it_started_under(
            self):
        """The restart probe. A new adapter over the same resolved identity
        lists by the same labels and recognises what the first one started —
        which is what makes the labels a description of the image rather than
        an independent claim beside it."""
        first = self.adapter(answer(stdout=""), answer(stdout="runtime-1\n"))
        started = first.start({"labels": dict(LABELS),
                               "operation_id": "runtime.start:1"})
        listing = json.dumps({
            "ID": "runtime-1",
            "Labels": ",".join(f"{LABEL_PREFIX}{name}={LABELS[name]}"
                               for name in documents.RUNTIME_LABELS)})
        again = self.adapter(answer(stdout=listing))
        found = again.list({"labels": dict(LABELS)})
        self.assertEqual([entry["runtime_id"] for entry in found],
                         [started["runtime_id"]])
        self.assertEqual(found[0]["labels"]["profile_digest"],
                         again.identity["profile_digest"])
        self.assertEqual(found[0]["labels"]["adapter_digest"],
                         again.identity["adapter_digest"])

    def test_a_resolved_identity_is_three_digests_and_nothing_else(self):
        for spoiled in ({"image_digest": IMAGE},
                        dict(Adapting.IDENTITY, extra="x"),
                        dict(Adapting.IDENTITY, image_digest="latest"),
                        dict(Adapting.IDENTITY, profile_digest=""),
                        "not a document"):
            with self.subTest(identity=spoiled):
                with self.assertRaises(ContractRefusal):
                    self.adapter(identity=spoiled)


class TheEngineReportsFactsAndDecidesNothing(Adapting):

    def test_a_start_answers_what_was_started(self):
        adapter = self.adapter(answer(stdout=""),
                               answer(stdout="runtime-1\n"))
        started = adapter.start({"labels": LABELS, "operation_id": "op-1"})
        self.assertEqual(started, {"runtime_id": "runtime-1",
                                   "labels": LABELS})

    def test_the_managers_real_operation_identity_makes_a_valid_runtime_name(
            self):
        """`attempts._start_operation_id` includes `runtime.start:`. The
        adapter must derive an engine name rather than copy that colon into
        Docker/Podman's closed name grammar."""
        operation_id = "runtime.start:" + "a" * 64
        adapter = self.adapter(answer(stdout=""),
                               answer(stdout="runtime-1\n"))
        adapter.start({"labels": LABELS, "operation_id": operation_id})
        vector = self.engine.vectors[1]
        runtime_name = vector[vector.index("--name") + 1]
        self.assertRegex(runtime_name,
                         re.compile(r"\A[a-zA-Z0-9][a-zA-Z0-9_.-]*\Z"))

    def test_a_duplicate_start_fails_closed_before_anything_is_created(self):
        """Two runtimes for one assignment is the state no later
        reconciliation can undo, so the question is asked BEFORE the create."""
        adapter = self.adapter(answer(stdout=listing()))
        with self.assertRaises(ContractRefusal) as caught:
            adapter.start({"labels": LABELS, "operation_id": "op-1"})
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("policy", "denied"))
        self.assertEqual(len(self.engine.vectors), 1,
                         "a duplicate start reached the engine's run vector")

    def test_an_engine_that_names_nothing_started_nothing_nameable(self):
        """Not "started something unnamed": an answer this adapter cannot turn
        into an identity, and inventing one makes every later comparison
        meaningless."""
        adapter = self.adapter(answer(stdout=""), answer(stdout="  \n"))
        self.assertEqual(adapter.start({"labels": LABELS,
                                        "operation_id": "op-1"}),
                         {"runtime_id": None, "labels": None})

    def test_a_refused_start_is_reported_with_bounded_prose(self):
        adapter = self.adapter(answer(stdout=""),
                               answer(status=125, stderr="x" * 10_000))
        with self.assertRaises(ContractRefusal) as caught:
            adapter.start({"labels": LABELS, "operation_id": "op-1"})
        self.assertLess(len(caught.exception.message), 500)

    def test_both_engines_listings_read_into_one_vocabulary(self):
        """RUNTIME-NEUTRAL: one vocabulary for the manager, two spellings read
        here."""
        for engine in ENGINES:
            with self.subTest(engine=engine):
                adapter = self.adapter(
                    answer(stdout=listing(engine=engine)), engine=engine)
                self.assertEqual(adapter.list({"labels": LABELS}),
                                 [{"runtime_id": "runtime-1",
                                   "labels": LABELS}])

    def test_a_listing_whose_labels_are_not_the_whole_set_is_refused(self):
        """A runtime whose labels this adapter had to guess at is one
        reconciliation cannot use."""
        short = {name: value for name, value in LABELS.items()
                 if name != "participant"}
        adapter = self.adapter(answer(stdout=listing(labels=short)))
        with self.assertRaises(ContractRefusal) as caught:
            adapter.list({"labels": LABELS})
        self.assertIn("reconciles on the whole label set",
                      caught.exception.message)

    def test_an_extra_manager_owned_label_is_not_silently_ignored(self):
        reported = {f"{LABEL_PREFIX}{name}": str(value)
                    for name, value in LABELS.items()}
        reported[f"{LABEL_PREFIX}bearer"] = "must-not-be-a-label"
        adapter = self.adapter(answer(stdout=json.dumps(
            {"ID": "runtime-1", "Labels": reported})))
        with self.assertRaises(ContractRefusal):
            adapter.list({"labels": LABELS})

    def test_engine_output_this_adapter_cannot_read_is_refused(self):
        for what, stdout in [("prose", "Error: daemon not running"),
                             ("half a document", '{"ID": "r-1"'),
                             ("a list where a record belongs", "[1, 2]"),
                             ("no identity member", '{"Labels": {}}')]:
            with self.subTest(what=what):
                adapter = self.adapter(answer(stdout=stdout))
                with self.assertRaises(ContractRefusal):
                    adapter.list({"labels": LABELS})

    def test_a_hostile_listing_never_escapes_as_a_fault(self):
        """Engine output is a caller input. Every one of these is ordinary."""
        for what, given in [("nothing at all", answer()),
                            ("a blank line", answer(stdout="\n\n")),
                            ("a refusal", answer(status=1, stderr="nope"))]:
            with self.subTest(what=what):
                adapter = self.adapter(given)
                try:
                    self.assertEqual(adapter.list({"labels": LABELS}), [])
                except ContractRefusal as refusal:
                    self.assertEqual(refusal.category, "policy")

    def test_the_generation_label_comes_back_as_the_number_it_was(self):
        """`1` and `"1"` are one fact spelled two ways, and a comparison that
        called them different would report every reconciliation as a
        mismatch."""
        adapter = self.adapter(answer(stdout=listing()))
        self.assertEqual(adapter.list({"labels": LABELS})[0]["labels"],
                         LABELS)
        self.assertIs(type(adapter.list.__self__), OciAdapter)

    def test_an_ambiguous_listing_is_returned_whole_for_the_manager_to_judge(
            self):
        """The adapter does not choose. `attempts.py` already refuses when more
        than one runtime carries an assignment's labels, and an adapter that
        picked one would be deciding authority from engine state.
        """
        adapter = self.adapter(answer(
            stdout=listing("runtime-1") + "\n" + listing("runtime-2")))
        found = adapter.list({"labels": LABELS})
        self.assertEqual([one["runtime_id"] for one in found],
                         ["runtime-1", "runtime-2"])


class AbsenceIsProvedRatherThanInferred(Adapting):

    def test_the_four_states_are_distinct(self):
        cases = [("running", answer(stdout=inspection(True)), "running"),
                 ("quiescent", answer(stdout=inspection(False)), "quiescent"),
                 ("absent", answer(status=1, stderr="Error: No such object: runtime-1"),
                  "absent"),
                 ("uncertain", answer(status=1, stderr="daemon unreachable"),
                  "uncertain")]
        for what, given, expected in cases:
            with self.subTest(what=what):
                adapter = self.adapter(given)
                self.assertEqual(adapter.observe("runtime-1")["state"],
                                 expected)

    def test_inspection_must_name_the_exact_runtime_it_describes(self):
        """State without identity, or state for another identity, cannot
        prove this runtime quiescent."""
        for what, document in (
                ("missing identity", {"State": {"Running": False}}),
                ("another identity", {"Id": "runtime-2",
                                      "State": {"Running": False}})):
            with self.subTest(what=what):
                adapter = self.adapter(answer(stdout=json.dumps(document)))
                try:
                    observed = adapter.observe("runtime-1")
                except ContractRefusal:
                    continue
                self.assertEqual(observed["state"], "uncertain")

    def test_unrelated_not_found_prose_is_not_positive_absence(self):
        adapter = self.adapter(answer(
            status=1,
            stderr="inspection helper not found while daemon is unavailable"))
        self.assertEqual(adapter.observe("runtime-1")["state"], "uncertain")

    def test_an_empty_listing_is_never_death(self):
        """It is one question answered about a filter. Absence is a question
        about an exact identity, and only the engine can answer it."""
        adapter = self.adapter(answer(stdout=""))
        self.assertEqual(adapter.list({"labels": LABELS}), [])
        adapter = self.adapter(answer(status=1, stderr="daemon unreachable"))
        self.assertEqual(adapter.observe("runtime-1")["state"], "uncertain")

    def test_engine_confusion_is_uncertain_and_never_quiescent(self):
        """A manager that treated confusion as death would release an
        assignment whose worker is still running."""
        for what, given in [
                ("a record with no state", answer(stdout='{"Id": "r"}')),
                ("a state that is not a record",
                 answer(stdout='{"State": "up"}')),
                ("Running as prose",
                 answer(stdout='{"State": {"Running": "yes"}}')),
                ("two runtimes for one identity",
                 answer(stdout=json.dumps([{"State": {"Running": True}},
                                           {"State": {"Running": False}}]))),
                ("output that is not JSON", answer(stdout="Up 3 minutes"))]:
            with self.subTest(what=what):
                adapter = self.adapter(given)
                try:
                    observed = adapter.observe("runtime-1")
                except ContractRefusal as refusal:
                    self.assertEqual(refusal.category, "integrity")
                    continue
                self.assertEqual(observed["state"], "uncertain", what)

    def test_a_stop_orders_and_then_proves(self):
        """A stop acknowledgement is the engine saying it accepted an ORDER."""
        adapter = self.adapter(answer(), answer(stdout=inspection(False)))
        settled = adapter.stop({"runtime_id": "runtime-1",
                                "operation_id": "op-1"})
        self.assertEqual(settled["ordered"], True)
        self.assertEqual(settled["state"], "quiescent")
        self.assertEqual(self.engine.vectors[0][:2], ["docker", "stop"])
        self.assertEqual(self.engine.vectors[1][:2], ["docker", "inspect"])

    def test_a_stop_the_engine_refused_still_reports_what_is_true(self):
        adapter = self.adapter(answer(status=1, stderr="no"),
                               answer(stdout=inspection(True)))
        settled = adapter.stop({"runtime_id": "runtime-1",
                                "operation_id": "op-1"})
        self.assertEqual(settled["ordered"], False)
        self.assertEqual(settled["state"], "running")

    def test_destruction_proves_absence_rather_than_assuming_it(self):
        adapter = self.adapter(answer(),
                               answer(status=1, stderr="Error: No such container: runtime-1"))
        self.assertEqual(adapter.destroy("runtime-1")["state"], "absent")
        adapter = self.adapter(answer(), answer(stdout=inspection(True)))
        self.assertEqual(adapter.destroy("runtime-1")["state"], "running")

    def test_the_diagnostic_is_bounded_however_loud_the_engine_is(self):
        adapter = self.adapter(answer(status=1, stderr="e" * 100_000))
        self.assertLessEqual(len(adapter.observe("runtime-1")["why"]),
                             MAX_DIAGNOSTIC + 60)


class TheEngineIsInjectedAndTyped(Adapting):

    def test_an_engine_answer_that_is_not_one_is_refused(self):
        for what, given in [("nothing", None), ("text", "ok"),
                            ("a missing stream", {"status": 0,
                                                  "stdout": "x"}),
                            ("a status that is not a number",
                             {"status": True, "stdout": "", "stderr": ""}),
                            ("a stream that is not text",
                             {"status": 0, "stdout": 1, "stderr": ""})]:
            with self.subTest(what=what):
                port = EnginePort(lambda argv, given=given: given)
                with self.assertRaises(ContractRefusal):
                    port(["docker", "ps"])

    def test_a_run_operation_that_is_not_callable_is_refused(self):
        for value in (None, "docker", 7):
            with self.subTest(value=repr(value)):
                with self.assertRaises(ContractRefusal):
                    EnginePort(value)

    def test_the_surface_is_exported(self):
        for name in oci.__all__:
            with self.subTest(name=name):
                self.assertTrue(hasattr(oci, name))


if __name__ == "__main__":
    unittest.main()
