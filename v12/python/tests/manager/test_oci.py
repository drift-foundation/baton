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
import shutil
import tempfile
import unittest

from baton_v12.contracts import ContractRefusal
from baton_v12.worker_manager import (ControlStore, documents, launch,
                                      oci, workspaces)

from . import input_roots
from baton_v12.worker_manager.oci import (ENGINES, LABEL_PREFIX,
                                          MAX_DIAGNOSTIC, RESTRICTIONS,
                                          ROOT_NAMES, EnginePort, OciAdapter,
                                          destroy_vector, inspect_vector,
                                          list_vector, run_vector, stop_vector)

# A sentinel for "the fixture's own authorized root", so a case can ask for
# the default and a case can ask for none, and the two are different requests.
_UNSET = object()

IMAGE = "sha256:" + "a" * 64
# The assignment's own roots, as `assignment_workspace` answers with them, and
# the posture that decides which of them a container may see. Both are REQUIRED
# inputs since the 2026-08-25 ruling: roots alone cannot choose the topology.
# W33936: the deployment's configured workspace group. An execution start
# without one refuses before the engine, so every execution vector below names
# it -- and this module composes ARGV rather than touching a filesystem, so
# what it proves is the composition. The write itself is proved against a real
# daemon in `test_input_delivery`.
# The deployment's configured workspace group. Obtained per case from the
# manager's own record -- see `Adapting.setUp` -- because it is a capability
# rather than an integer; `GROUP` names the class attribute the vector cases
# read so they say which one they mean.
GROUP = None

ROOTS = {"inputs": "/srv/a-1/inputs", "workspace": "/srv/a-1/workspace",
         }
LABELS = {"runtime_attempt_id": "attempt-1",
          "authority_uuid": "2b077949c86e8bef24304f59c28ec398",
          "work_id": "2b077949-W4", "participant": "baton.claude",
          "generation": 1,
          # W16823: the principal and effective scope the claim was authorized
          # for, beside the four-part fence.
          "principal": "principal:org-a", "effective_scope": "scope:deployment",
          "profile_digest": "sha256:" + "b" * 64,
          "policy_digest": "sha256:" + "d" * 64,
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


def listing(runtime_id="runtime-1", labels=None, engine="docker",
            image=None):
    """One engine listing entry.

    IT NAMES THE IMAGE, because the engine does. Review [P1] required the
    running image to survive restart reconciliation, and it is read from the
    listing rather than from a label -- so a fixture without one is a listing
    no real engine produces.
    """
    labels = LABELS if labels is None else labels
    image = IMAGE if image is None else image
    reported = {f"{LABEL_PREFIX}{name}": str(value)
                for name, value in labels.items()}
    if engine == "podman":
        return json.dumps({"Id": runtime_id, "ImageID": image,
                           "Labels": ",".join(f"{key}={value}" for key, value
                                              in reported.items())})
    return json.dumps({"ID": runtime_id, "Image": image,
                       "Labels": reported})


def inspection(running, runtime_id="runtime-1"):
    return json.dumps({"Id": runtime_id, "State": {"Running": running}})


class Configured(unittest.TestCase):
    """A case that holds the deployment's configured workspace group.

    W33936 review [P1] made that group a capability read from this manager's
    own record rather than an integer a caller composes -- so even a suite that
    proves ARGV without touching a filesystem needs the record, because the
    group is now a deployment fact and not an operand. The store here exists
    for exactly that one read.
    """

    def setUp(self):
        self._configured = tempfile.TemporaryDirectory(prefix="v12-w6632-cfg-")
        self.addCleanup(self._configured.cleanup)
        self.store = ControlStore.open(
            os.path.join(self._configured.name, "control.sqlite3"),
            incarnation="vector-1",
            clock=lambda: "2026-08-24T00:00:00.000Z")
        self.addCleanup(self.store.close)
        self.group = input_roots.configured_group(self.store)


class TheVectorsAreClosedAndOrdered(Configured):
    """GOLDEN VECTORS. No shell, so nothing to escape out of."""

    def test_the_run_vector_is_exact_for_both_engines(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                argv = run_vector(engine, image_digest=IMAGE, labels=LABELS,
                                  assignment_roots=ROOTS, posture="execution", workspace_group=self.group,
                                  name="baton-op-1")
                self.assertEqual(argv[:5],
                                 [engine, "run", "--detach", "--name",
                                  "baton-op-1"])
                # THE IMAGE IS LAST and is a digest, so no caller value can be
                # read as an argument to the engine itself.
                self.assertEqual(argv[-1], IMAGE)
                # 5 for the head, 2 for the configured workspace group,
                # 20 for the restrictions, 20 for the TEN
                # labels, 1 for the image and 1 for `--read-only`, which is the
                # only flag carrying no value. Eight since review [P1] put the
                # policy digest among them: the engine reports the image it is
                # running and has never heard of a policy, so a label is the
                # only way that half of the resolved identity survives a
                # restart. TEN since W16823 put the principal and the effective
                # scope beside the four-part fence: two endpoint addresses the
                # authority maps to one principal produced two unrelated label
                # sets, so one principal's runtimes read as two independent
                # identities to anything listing them.
                # W33936 adds `--group-add <gid>`: an execution runtime is
                # given the deployment's configured workspace group, and one
                # without it refuses before the engine rather than starting a
                # worker that cannot write its own workspace.
                self.assertEqual(len(argv), 49)

    def test_every_restriction_is_present_and_unconditional(self):
        """A policy a caller can turn off is a default."""
        argv = run_vector("docker", image_digest=IMAGE, labels=LABELS,
                          assignment_roots=ROOTS, posture="execution", workspace_group=self.group,
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
                          assignment_roots=ROOTS, posture="execution", workspace_group=self.group,
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
                               assignment_roots=ROOTS, posture="execution", workspace_group=self.group,
                               name="baton-op-1")

    def test_a_label_carrying_a_line_break_is_refused(self):
        with self.assertRaises(ContractRefusal) as caught:
            run_vector("docker", image_digest=IMAGE,
                       assignment_roots=ROOTS, posture="execution",
                       workspace_group=self.group,
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
                               assignment_roots=ROOTS, posture="execution", workspace_group=self.group,
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

    def test_the_listing_selects_candidates_and_never_pre_compares_identity(
            self):
        """REVISED under review [P0]'s explicit case-specific confirmation.

        It used to require a filter for EVERY label, which pinned the defect:
        a real engine applies every filter before returning a row, so a
        runtime from this exact attempt under an old policy never reached the
        adapter at all, and `start` read the empty result as "nothing exists".

        Discovery has to be broader than comparison. The engine answers which
        runtimes belong to this ATTEMPT; the adapter decides in process
        whether each one is this delivery's.
        """
        argv = list_vector("docker", labels=LABELS)
        filters = [argv[at + 1] for at, piece in enumerate(argv)
                   if piece == "--filter"]
        # REVISED A SECOND TIME under review [P0]'s explicit confirmation, and
        # the second revision is the general rule the first one missed. It
        # required the attempt AND the four parts of the assignment, which
        # still let the engine pre-compare `generation` — so a runtime under
        # an old generation was hidden exactly as the digests had been.
        #
        # ANY assignment fact used as a filter hides a runtime that
        # contradicts it, and a contradictory runtime is what this adapter
        # exists to refuse. The one label that selects is the one that answers
        # "is this runtime this attempt's".
        self.assertEqual(
            filters,
            [f"label={LABEL_PREFIX}runtime_attempt_id="
             f"{LABELS['runtime_attempt_id']}"],
            "the candidate selector is the attempt id and nothing else")
        # NOTHING ELSE IS AMONG THEM — not the digests, and not the four
        # assignment parts either. A label used as a filter is a runtime the
        # engine hides rather than one this adapter refuses.
        for name in documents.RUNTIME_LABELS:
            if name == "runtime_attempt_id":
                continue
            with self.subTest(label=name):
                self.assertNotIn(f"label={LABEL_PREFIX}{name}={LABELS[name]}",
                                 filters)

    def test_the_whole_label_set_is_still_owned_before_the_engine_is_asked(
            self):
        """Narrowing the FILTERS did not narrow the ownership. An invented or
        malformed label still refuses before anything is listed."""
        for what, labels in (("an invented member",
                              {**LABELS, "bearer": "secret"}),
                             ("a missing member",
                              {name: value for name, value in LABELS.items()
                               if name != "policy_digest"}),
                             ("a text-shaped digest",
                              dict(LABELS, policy_digest="policy-latest"))):
            with self.subTest(what=what):
                with self.assertRaises(ContractRefusal):
                    list_vector("docker", labels=labels)

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
                               assignment_roots=ROOTS, posture="execution", workspace_group=self.group,
                               name="baton-op-1")


class AMountIsCanonicalAndNeverTheHosts(Configured):

    def mount(self, **overrides):
        one = {"source": "/srv/a-1/workspace", "target": "/workspace",
               "writable": True}
        one.update(overrides)
        return run_vector("docker", image_digest=IMAGE, labels=LABELS,
                          assignment_roots=ROOTS, posture="execution", workspace_group=self.group,
                          name="baton-op-1", mounts=[one])

    def test_the_assignment_root_contract_is_artifact_neutral(self):
        """The core adapter may know generic input and workspace roots, but
        must not require a Git-specific root from every assignment."""
        self.assertEqual(ROOT_NAMES, ("inputs", "workspace"))
        run_vector(
            "docker", image_digest=IMAGE, labels=LABELS,
            assignment_roots={"inputs": "/srv/a-1/inputs",
                              "workspace": "/srv/a-1/workspace"},
            posture="execution", workspace_group=self.group, name="baton-op-1")

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

    def test_a_target_traversal_is_not_normalized_into_another_location(self):
        """The spelling is checked before `normpath` erases the traversal.

        Accepting `/workspace/../etc` and emitting `/etc` silently moves the
        assignment's writable bind over the image filesystem rather than the
        target the topology named.
        """
        with self.assertRaises(ContractRefusal):
            self.mount(target="/workspace/../etc")

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
                    posture="execution", workspace_group=self.group, name="baton-op-1",
                    assignment_roots={"inputs": "/srv/a-1/inputs"})),
                ("a root that is not absolute", lambda: run_vector(
                    "docker", image_digest=IMAGE, labels=LABELS,
                    posture="execution", workspace_group=self.group, name="baton-op-1",
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
                       }
        with self.assertRaises(ContractRefusal):
            run_vector("docker", image_digest=IMAGE, labels=LABELS,
                       assignment_roots=overlapping, posture="execution", workspace_group=self.group,
                       name="baton-op-1")

    def test_a_symlink_descendant_cannot_escape_an_assignment_root(self):
        """Lexical containment is not mount authority.

        The engine resolves a bind source on the host. A symlink planted under
        the writable workspace must not turn an apparently owned spelling into
        an arbitrary host mount.
        """
        with tempfile.TemporaryDirectory() as root:
            roots = {name: os.path.join(root, name)
                     for name in ("inputs", "workspace")}
            for place in roots.values():
                os.mkdir(place)
            outside = os.path.join(root, "outside")
            os.mkdir(outside)
            escape = os.path.join(roots["workspace"], "escape")
            os.symlink(outside, escape)
            with self.assertRaises(ContractRefusal):
                run_vector(
                    "docker", image_digest=IMAGE, labels=LABELS,
                    assignment_roots=roots, posture="execution", workspace_group=self.group,
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
                assignment_roots=roots, posture="execution", workspace_group=self.group,
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
                       assignment_roots=same, posture="execution", workspace_group=self.group,
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
                assignment_roots=roots, posture="execution", workspace_group=self.group,
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
                               assignment_roots=ROOTS, posture="execution", workspace_group=self.group,
                               name="baton-op-1", mounts=mounts)

    def test_two_mounts_cannot_land_on_one_target(self):
        with self.assertRaises(ContractRefusal) as caught:
            run_vector("docker", image_digest=IMAGE, labels=LABELS,
                       assignment_roots=ROOTS, posture="execution", workspace_group=self.group,
                       name="baton-op-1",
                       mounts=[{"source": "/srv/a-1/workspace/a",
                                "target": "/w", "writable": True},
                               {"source": "/srv/a-1/inputs/b",
                                "target": "/w", "writable": False}])
        self.assertIn("would hide the first", caught.exception.message)


class Adapting(Configured):
    """The adapter's own doors, over a fake engine and REAL roots.

    RECERTIFIED, and the word matters. Approver ruling M34916 authorizes a
    fresh certification of this module because its uncommitted assertions were
    destroyed and no authoritative copy exists; nothing below is a
    reconstruction of what they said. What they were is recorded as
    unavailable and stays that way.

    What changed, and why the fixture grew two things it did not have:

      * W26291 made a launch document REQUIRED of every execution start. The
        adapter refuses without one, so a fixture that has none proves the
        refusal and nothing past it -- which is what the twelve stale cases
        were doing.
      * W33936 makes an execution start prove its workspace root's group and
        mode immediately before the engine. That is a question about a real
        directory, so this fixture allocates one through the canonical
        `assignment_workspace` rather than naming a path that does not exist.

    The ENGINE stays fake, which is this module's whole design: the adapter's
    boundary is the vector it composes and the answer it reads, and a real
    daemon proves the same thing more slowly and less exactly. What is real
    here is only what the adapter now insists on being real.
    """

    # ONE RESOLVED IDENTITY, and it AGREES with `LABELS` — because that is
    # the contract now: what a delivery is started under and what its runtime
    # is labelled with are one account, and a fixture whose two halves
    # disagreed would make every case here refuse for the mismatch.
    IDENTITY = {"image_digest": IMAGE,
                "profile_digest": LABELS["profile_digest"],
                "policy_digest": LABELS["policy_digest"],
                "adapter_digest": LABELS["adapter_digest"]}

    def setUp(self):
        super().setUp()
        self._home = tempfile.TemporaryDirectory(prefix="v12-w6632-")
        self.addCleanup(self._cleanup)
        self.home = self._home.name
        self.storage = os.path.join(self.home, "storage")
        os.makedirs(self.storage)
        self.live_roots = workspaces.assignment_workspace(
            self.group, self.storage, "attempt-1")
        self._launches = 0

    def _cleanup(self):
        for current, directories, files in os.walk(self.home):
            for name in directories + files:
                try:
                    os.chmod(os.path.join(current, name), 0o700)
                except OSError:
                    pass
            try:
                os.chmod(current, 0o700)
            except OSError:
                pass
        self._home.cleanup()

    def launched(self):
        """One materialized launch document, authored by the manager.

        Per adapter rather than per attempt: a refused start DISCARDS the
        delivery, so handing a second adapter the same one would hand it a
        document the first tore down.
        """
        self._launches += 1
        home = os.path.join(self.home, f"launch-{self._launches}")
        os.makedirs(home, exist_ok=True)
        return launch.materialize(
            home, attempt_id="attempt-1", session="session-attempt-1",
            contract="exercise the constrained OCI adapter",
            role="implementer")

    def adapter(self, *answers, engine="docker", identity=None, roots=None,
                launch_delivery=False, workspace_group=_UNSET,
                network=_UNSET, interactive=_UNSET):
        self.engine = Engine(answers)
        # W38956's two start operands. `_UNSET` means "do not name it", which
        # is a DIFFERENT request from naming its default -- the whole property
        # under test is that an adapter which names neither composes exactly
        # what it composed before they existed.
        extra = {}
        if network is not _UNSET:
            extra["network"] = network
        if interactive is not _UNSET:
            extra["interactive"] = interactive
        # The identity is passed THROUGH rather than copied, so a case may
        # hand this door something that is not a document at all -- which is
        # one of the things the door has to refuse.
        return OciAdapter(engine, self.engine,
                          identity=self.IDENTITY if identity is None
                          else identity,
                          assignment_roots=dict(roots if roots is not None
                                                else self.live_roots),
                          posture="execution",
                          workspace_group=(self.group
                                           if workspace_group is _UNSET
                                           else workspace_group),
                          launch_delivery=(self.launched()
                                           if launch_delivery is False
                                           else launch_delivery),
                          **extra)


class TheRootThatWasProvedIsTheRootThatIsMounted(Adapting):
    """W19784 second review [P0], 2026-08-27.

    THE AUTHORIZATION AND THE MOUNT WERE TWO OPERATIONS. The manager proved
    one directory named the live assignment, this attempt and the claimed
    input digest -- and then called an adapter whose mount plan is owned at
    CONSTRUCTION and independent of that value. `_mounts` proves containment
    and writability, and none of that says WHICH of an assignment's two roots
    a bind names or where it lands: the sibling workspace is contained and
    readable too, and `/inputs` is a target this manager never fixes.

    So a worker could be started over material nothing had authorized, and
    every check that ran said yes, because each was about a different value.
    """

    def mounted(self, source, target="/input", writable=False):
        return {"source": source, "target": target, "writable": writable}

    def started(self, mounts, authorized=_UNSET, answers=None):
        # The duplicate probe runs FIRST and answers an empty listing, then the
        # run itself. Both are the ordinary shape; this rule sits before both,
        # so the refusing cases never consume either.
        engine = Engine(answers or [answer(stdout=""),
                                    answer(stdout="runtime-1\n")])
        self.engine = engine
        adapter = OciAdapter("docker", engine, identity=self.IDENTITY,
                             assignment_roots=dict(self.live_roots),
                             posture="execution", workspace_group=self.group,
                             launch_delivery=self.launched(), mounts=mounts)
        request = {"labels": LABELS, "operation_id": "runtime.start:1"}
        if authorized is _UNSET:
            authorized = self.live_roots["inputs"]
        if authorized is not None:
            request["input_root"] = authorized
        return adapter.start(request)

    def test_the_authorized_root_reaches_the_engine_argv_exactly(self):
        """The bytes, not the intention. This is the integration half the
        review asked for: what the engine is actually told."""
        self.started([self.mounted(self.live_roots["inputs"])])
        argv = self.engine.vectors[-1]
        binds = [argv[at + 1] for at, flag in enumerate(argv)
                 if flag == "--mount"]
        self.assertIn(
            f"type=bind,source={self.live_roots['inputs']},"
            f"target=/input,readonly=true", binds)
        # AND EXACTLY ONE lands there, so the engine is never the party
        # deciding which of two the worker reads.
        self.assertEqual([one for one in binds if ",target=/input," in one],
                         [f"type=bind,source={self.live_roots['inputs']},"
                          f"target=/input,readonly=true"])

    def test_a_plan_naming_the_sibling_workspace_never_reaches_the_engine(
            self):
        """The exact defect. `workspace` is this assignment's own root and
        passes containment; it is not the directory that was proved."""
        with self.assertRaises(ContractRefusal) as caught:
            self.started([self.mounted(ROOTS["workspace"])])
        self.assertEqual(caught.exception.category, "policy")
        self.assertEqual(self.engine.vectors, [],
                         "a refused plan still reached the engine")

    def test_a_plan_that_mounts_no_input_root_never_reaches_the_engine(self):
        """Omission is a way to be wrong too: a container with nothing at
        `/input` is one whose worker cannot read the assignment it was proved
        against, and the manager authorized a root that went nowhere."""
        with self.assertRaises(ContractRefusal):
            self.started([self.mounted(ROOTS["workspace"],
                                       target="/workspace", writable=True)])
        self.assertEqual(self.engine.vectors, [])

    def test_the_authorized_root_at_another_target_is_not_the_input_root(self):
        """`/inputs` is a path this manager never fixes and the worker never
        reads. A plan that lands the proved source there has mounted nothing
        at `/input`, whatever it looks like."""
        with self.assertRaises(ContractRefusal):
            self.started([self.mounted(ROOTS["inputs"], target="/inputs")])
        self.assertEqual(self.engine.vectors, [])

    def test_the_authorized_root_is_never_mounted_writable(self):
        """The input is the evidence the result is measured against, so a
        runtime that could edit it could edit what it is judged by."""
        with self.assertRaises(ContractRefusal):
            self.started([self.mounted(ROOTS["inputs"], writable=True)])
        self.assertEqual(self.engine.vectors, [])

    def test_a_spelling_that_normalizes_onto_the_fixed_path_is_not_it(self):
        """W19784 third review [P1], at this boundary too.

        `/else/../input` normalizes to `/input`, so a rule that normalized
        FIRST would accept a plan naming a path this manager never fixed and
        call it the fixed one. The spelling is refused before normalization can
        erase it, on both sides of the bind -- a caller writing `..` is asking
        this adapter to compute a path rather than name one.
        """
        for what, mount in (
                ("a target that traverses onto the fixed path",
                 self.mounted(ROOTS["inputs"], target="/else/../input")),
                ("a source that traverses onto the proved root",
                 self.mounted(ROOTS["inputs"] + "/../inputs")),
                ("a target carrying the engine's own separator",
                 self.mounted(ROOTS["inputs"], target="/input:2"))):
            with self.subTest(what=what):
                with self.assertRaises(ContractRefusal) as caught:
                    self.started([mount])
                self.assertEqual(caught.exception.code, "path")
                self.assertEqual(self.engine.vectors, [])

    def test_two_binds_on_the_fixed_path_leave_the_engine_deciding(self):
        with self.assertRaises(ContractRefusal):
            self.started([self.mounted(ROOTS["inputs"]),
                          self.mounted(ROOTS["inputs"] + "/nested")])
        self.assertEqual(self.engine.vectors, [])

    def test_without_an_authorized_root_nothing_may_claim_the_fixed_path(self):
        """ABSENCE IS DECIDED TOO. With nothing proved there is nothing a
        `/input` bind could be, and "the manager did not say" is not a reason
        to expose an unproved directory at the path the worker trusts."""
        with self.assertRaises(ContractRefusal) as caught:
            self.started([self.mounted(ROOTS["inputs"])], authorized=None)
        self.assertEqual(caught.exception.category, "policy")
        self.assertEqual(self.engine.vectors, [])

    def test_a_delivery_with_neither_starts_normally(self):
        """The runtime half of this adapter is constructible and startable
        without an input delivery at all -- that is what a consent container
        and every pre-W19784 case are -- so the new rule must not have made an
        empty plan unstartable."""
        started = self.started([], authorized=None)
        self.assertEqual(started["runtime_id"], "runtime-1")
        self.assertNotIn("/input", " ".join(self.engine.vectors[-1]))


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
            "ID": "runtime-1", "Image": IMAGE,
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

    def test_a_restart_refuses_a_runtime_from_another_resolved_image(self):
        """Labels alone cannot make a stale image this adapter's runtime.

        The dossier requires the exact image identity to survive restart
        reconciliation.  A new adapter resolved to another image must not
        adopt a listed runtime merely because its profile/adapter labels still
        match.
        """
        listing = json.dumps({
            "ID": "runtime-1", "ImageID": IMAGE,
            "Labels": ",".join(f"{LABEL_PREFIX}{name}={LABELS[name]}"
                               for name in documents.RUNTIME_LABELS)})
        identity = dict(self.IDENTITY,
                        image_digest="sha256:" + "9" * 64)
        again = self.adapter(answer(stdout=listing), identity=identity)
        with self.assertRaises(ContractRefusal):
            again.list({"labels": dict(LABELS)})

    def test_a_restart_refuses_a_runtime_labelled_for_another_policy(self):
        """The labelled half of the identity, for the member no engine
        reports. A runtime running the right image under the wrong policy is
        not this delivery's, and nothing but the label can say so."""
        other = dict(LABELS, policy_digest="sha256:" + "e" * 64)
        again = self.adapter(answer(stdout=listing(labels=other)))
        with self.assertRaises(ContractRefusal) as caught:
            again.list({"labels": dict(LABELS)})
        self.assertIn("one delivery carries one identity",
                      caught.exception.message)

    def test_a_listing_that_names_no_image_is_refused(self):
        """An engine that will not say which image is running has not proved
        the identity; the adapter refuses rather than adopting on the labels
        alone, which is the state review [P1] found."""
        entry = json.dumps({"ID": "runtime-1",
                            "Labels": {f"{LABEL_PREFIX}{name}": str(value)
                                       for name, value in LABELS.items()}})
        adapter = self.adapter(answer(stdout=entry))
        with self.assertRaises(ContractRefusal):
            adapter.list({"labels": dict(LABELS)})

    def test_a_tag_is_not_an_image_identity(self):
        """A tag is a pointer that was true when somebody last pushed. The
        comparison this feeds decides whether a restarted manager adopts a
        worker, so it is made against a digest or not at all."""
        adapter = self.adapter(answer(stdout=listing(image="worker:latest")))
        with self.assertRaises(ContractRefusal) as caught:
            adapter.list({"labels": dict(LABELS)})
        self.assertEqual(caught.exception.code, "digest")

    def test_the_engines_two_spellings_of_the_image_are_one_fact(self):
        """Docker answers `Image` and Podman answers `ImageID`, and the id may
        arrive with or without the `sha256:` prefix. One vocabulary for the
        manager, every spelling read here."""
        for what, entry in (
                ("docker", listing()),
                ("podman", listing(engine="podman")),
                ("a bare id", listing(image=IMAGE[len("sha256:"):]))):
            with self.subTest(spelling=what):
                adapter = self.adapter(answer(stdout=entry))
                found = adapter.list({"labels": dict(LABELS)})
                self.assertEqual([one["runtime_id"] for one in found],
                                 ["runtime-1"])

    def test_a_start_labelled_for_another_policy_is_refused(self):
        """The mismatch probe, extended to the member review [P1] restored."""
        adapter = self.adapter(answer(stdout=""))
        with self.assertRaises(ContractRefusal) as caught:
            adapter.start({
                "labels": dict(LABELS, policy_digest="sha256:" + "9" * 64),
                "operation_id": "runtime.start:1"})
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("policy", "denied"))
        self.assertIn("one delivery carries one identity",
                      caught.exception.message)

    def test_a_stale_policy_runtime_is_not_filtered_into_a_duplicate_start(
            self):
        """The candidate query must be broader than the identity comparison.

        A real engine applies every label filter before returning a row. If
        the query includes `policy_digest`, a runtime from this exact attempt
        under the old policy is invisible to the later mismatch check and the
        adapter proceeds to create a second runtime for one attempt.
        """
        stale = dict(LABELS, policy_digest="sha256:" + "e" * 64)

        class FilteringEngine:
            def __init__(self):
                self.vectors = []

            def __call__(self, argv):
                self.vectors.append(list(argv))
                if argv[1] == "ps":
                    exact_policy = (
                        f"label={LABEL_PREFIX}policy_digest="
                        f"{LABELS['policy_digest']}")
                    if exact_policy in argv:
                        return answer(stdout="")
                    return answer(stdout=listing(labels=stale))
                if argv[1] == "run":
                    return answer(stdout="runtime-new\n")
                return answer()

        engine = FilteringEngine()
        adapter = OciAdapter(
            "docker", engine, identity=self.IDENTITY,
            assignment_roots=ROOTS, posture="execution")
        with self.assertRaises(ContractRefusal):
            adapter.start({"labels": dict(LABELS),
                           "operation_id": "runtime.start:1"})
        self.assertFalse(any(vector[1] == "run" for vector in engine.vectors),
                         engine.vectors)

    def test_a_stale_assignment_runtime_is_not_filtered_into_a_duplicate_start(
            self):
        """Candidate discovery cannot pre-compare mutable assignment facts.

        A runtime carrying this exact attempt id but a stale generation is
        still a runtime for this attempt.  If the engine filters on the
        requested generation first, that runtime disappears before the
        adapter can refuse it and `start` creates the forbidden duplicate.
        """
        stale = dict(LABELS, generation=0)

        class FilteringEngine:
            def __init__(self):
                self.vectors = []

            def __call__(self, argv):
                self.vectors.append(list(argv))
                if argv[1] == "ps":
                    exact_generation = (
                        f"label={LABEL_PREFIX}generation="
                        f"{LABELS['generation']}")
                    if exact_generation in argv:
                        return answer(stdout="")
                    return answer(stdout=listing(labels=stale))
                if argv[1] == "run":
                    return answer(stdout="runtime-new\n")
                return answer()

        engine = FilteringEngine()
        adapter = OciAdapter(
            "docker", engine, identity=self.IDENTITY,
            assignment_roots=ROOTS, posture="execution")
        with self.assertRaises(ContractRefusal):
            adapter.start({"labels": dict(LABELS),
                           "operation_id": "runtime.start:1"})
        self.assertFalse(any(vector[1] == "run" for vector in engine.vectors),
                         engine.vectors)

    def test_a_returned_candidate_must_match_the_requested_assignment(self):
        """Engine filters select candidates; they do not prove their labels.

        A compatible engine may ignore a filter, and engine state may be
        stale or corrupted.  The complete returned label record therefore
        has to be compared in process before the runtime is adopted.
        """
        stale = dict(LABELS, generation=0)
        adapter = self.adapter(answer(stdout=listing(labels=stale)))
        with self.assertRaises(ContractRefusal) as caught:
            adapter.list({"labels": dict(LABELS)})
        self.assertIn("one delivery carries one identity",
                      caught.exception.message)

    def test_every_label_that_contradicts_the_request_is_refused(self):
        """The complete returned record, member by member. Engine-side
        selection is not proof that a returned row has the values requested:
        a compatible engine may ignore a filter and engine state may be stale
        or hand-edited."""
        for name in documents.RUNTIME_LABELS:
            if name == "runtime_attempt_id":
                continue
            other = 0 if name == "generation" else "sha256:" + "e" * 64
            if name in ("authority_uuid", "work_id", "participant"):
                other = "somebody-else"
            with self.subTest(label=name):
                stale = dict(LABELS, **{name: other})
                adapter = self.adapter(answer(stdout=listing(labels=stale)))
                with self.assertRaises(ContractRefusal) as caught:
                    adapter.list({"labels": dict(LABELS)})
                self.assertIn("one delivery carries one identity",
                              caught.exception.message)

    def test_a_contradictory_candidate_stops_a_start_before_the_engine_creates(
            self):
        """The reason the whole-record comparison matters: a candidate this
        adapter cannot own has to refuse at the duplicate check rather than
        read as an empty set."""
        stale = dict(LABELS, generation=0)
        adapter = self.adapter(answer(stdout=listing(labels=stale)))
        with self.assertRaises(ContractRefusal):
            adapter.start({"labels": dict(LABELS),
                           "operation_id": "runtime.start:1"})
        self.assertTrue(all("run" not in vector
                            for vector in self.engine.vectors),
                        self.engine.vectors)

    def test_a_stale_candidate_is_refused_rather_than_filtered_away(self):
        """The module's own sentence, now true of the listing too: a stale
        identity is not ABSENT, it is WRONG, and dropping it leaves a
        mislabelled runtime running for this attempt."""
        for name in ("profile_digest", "policy_digest", "adapter_digest"):
            with self.subTest(stale=name):
                stale = dict(LABELS, **{name: "sha256:" + "e" * 64})
                adapter = self.adapter(answer(stdout=listing(labels=stale)))
                with self.assertRaises(ContractRefusal) as caught:
                    adapter.list({"labels": dict(LABELS)})
                self.assertIn("one delivery carries one identity",
                              caught.exception.message)

    def test_a_stale_candidate_stops_a_start_before_the_engine_creates(self):
        """The reason the discovery half matters at all. `start` asks what
        already carries this attempt's labels BEFORE it creates anything, so a
        candidate it cannot own has to refuse there rather than read as an
        empty set."""
        stale = dict(LABELS, policy_digest="sha256:" + "e" * 64)
        adapter = self.adapter(answer(stdout=listing(labels=stale)))
        with self.assertRaises(ContractRefusal):
            adapter.start({"labels": dict(LABELS),
                           "operation_id": "runtime.start:1"})
        self.assertTrue(all("run" not in vector
                            for vector in self.engine.vectors),
                        self.engine.vectors)

    def test_an_ordinary_start_still_finds_no_candidate_and_creates(self):
        """The other half. Broadening discovery must not make every start
        refuse: an attempt with no runtime yet still creates one."""
        adapter = self.adapter(answer(stdout=""), answer(stdout="runtime-1\n"))
        started = adapter.start({"labels": dict(LABELS),
                                 "operation_id": "runtime.start:1"})
        self.assertEqual(started["runtime_id"], "runtime-1")
        self.assertTrue(any(vector[1] == "run"
                            for vector in self.engine.vectors))

    def test_the_resolved_identity_includes_the_assignment_policy(self):
        """Image/profile/adapter is not the dossier's four-digest identity."""
        identity = dict(self.IDENTITY,
                        policy_digest="sha256:" + "d" * 64)
        adapter = self.adapter(identity=identity)
        self.assertEqual(adapter.identity["policy_digest"],
                         identity["policy_digest"])

    def test_a_resolved_identity_is_four_digests_and_nothing_else(self):
        """FOUR, and the count is the case.

        This method asserted THREE, and review [P1] was right that the number
        was a silent narrowing of a confirmed contract rather than a finding:
        the record says image, profile, policy and adapter, and a green test
        naming three is how a narrowing stops looking like one. The member
        list is asserted here so the next change to it has to come through
        this case.
        """
        self.assertEqual(
            tuple(oci.RESOLVED_IDENTITY),
            ("image_digest", "profile_digest", "policy_digest",
             "adapter_digest"))
        for spoiled in ({"image_digest": IMAGE},
                        {name: value for name, value in
                         Adapting.IDENTITY.items() if name != "policy_digest"},
                        dict(Adapting.IDENTITY, extra="x"),
                        dict(Adapting.IDENTITY, image_digest="latest"),
                        dict(Adapting.IDENTITY, policy_digest="latest"),
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
        # TWO VECTORS, and neither is a `run`: the duplicate probe, and the
        # launch delivery's own teardown when the refusal discards it. W26291
        # gave a refused start an ending, so counting vectors is no longer the
        # same question as "did anything start" -- which is what this case is
        # about, and it is now asked directly.
        self.assertEqual([one for one in self.engine.vectors
                          if "run" in one], [],
                         "a duplicate start reached the engine's run vector")

    def test_an_engine_that_names_nothing_started_nothing_nameable(self):
        """Not "started something unnamed": an answer this adapter cannot turn
        into an identity, and inventing one makes every later comparison
        meaningless."""
        adapter = self.adapter(answer(stdout=""), answer(stdout="  \n"))
        # W6634: the answer gained a `credentials` member, because a start that
        # produced no runtime id is a FAILURE ENDING for the delivery too --
        # nothing later could adopt or tear down a delivery it cannot name.
        # This adapter was built without a credential delivery, so it says so.
        #
        # W26291 added the second: an execution start REQUIRES a launch
        # document, so this fixture now has one -- and a start that produced
        # no runtime id ends that delivery for the same reason it ends the
        # credential one. `torn-down` is the ending, and reporting it is what
        # lets a caller tell a document that was cleaned up from one that was
        # never made.
        self.assertEqual(adapter.start({"labels": LABELS,
                                        "operation_id": "op-1"}),
                         {"runtime_id": None, "labels": None,
                          "credentials": {"lifecycle_state":
                                          "not-delivered"},
                          "launch": {"lifecycle_state": "torn-down"}})

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

    def test_an_absence_sentence_for_another_runtime_is_not_this_one_absent(
            self):
        """The requested identity elsewhere in stderr is not association.

        Only the engine sentence that states absence may name the identity;
        two unrelated fragments cannot be combined into death evidence.
        """
        adapter = self.adapter(answer(
            status=1,
            stderr=("Error: No such container: runtime-2; "
                    "request was for runtime-1")))
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

    @staticmethod
    def destroy_command(runtime_id="runtime-1"):
        """W6629 review [P1]: this core is handed `runtimeDestroyBody` now.

        The manager's authorization -- the assignment, the attempt, the intake
        receipt digest and the retention policy digest -- travels WITH the
        command instead of stopping at the boundary. Nothing here interprets
        it; the identity is what this core acts on."""
        return {"assignment_ref": {"work_ref": {"authority_uuid": "u" * 32,
                                                "work_id": "u" * 32 + "-W1"},
                                   "participant": "baton.claude",
                                   "generation": 1},
                "runtime_attempt_id": "attempt-1",
                "runtime_id": runtime_id,
                "intake_receipt_digest": "sha256:" + "6" * 64,
                "retention_policy_digest": "sha256:" + "7" * 64}

    def test_destruction_proves_absence_rather_than_assuming_it(self):
        adapter = self.adapter(answer(),
                               answer(status=1, stderr="Error: No such container: runtime-1"))
        self.assertEqual(
            adapter.destroy(self.destroy_command())["state"], "absent")
        adapter = self.adapter(answer(), answer(stdout=inspection(True)))
        self.assertEqual(
            adapter.destroy(self.destroy_command())["state"], "running")

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

    def test_an_engine_deadline_is_positive_whole_seconds(self):
        reached = []
        port = EnginePort(lambda argv, **keywords:
                          reached.append((argv, keywords)) or answer())
        for seconds in (0, -1, True, 1.5, "30"):
            with self.subTest(seconds=seconds):
                with self.assertRaises(ContractRefusal):
                    port(["docker", "ps"], seconds=seconds)
        self.assertEqual(reached, [])

    def test_the_surface_is_exported(self):
        for name in oci.__all__:
            with self.subTest(name=name):
                self.assertTrue(hasattr(oci, name))


if __name__ == "__main__":
    unittest.main()


class TheTwoExplicitStartOperands(Adapting):
    """W39356 review [P2]: the network and interactive operands, held directly.

    The transport suite exercises the CONVERSATION and the exec vector; these
    two decide what the container it speaks to is, and until this class existed
    nothing drove them at their own boundary. They are the only two operands in
    this module a deployment may use to widen a runtime, so they are the two
    most worth a refusal case each.
    """

    def started(self, **operands):
        """One real start through the adapter, and the argv it composed.

        The adapter is built here rather than through `Adapting.adapter`
        because a start needs the mount plan the authorized input root is held
        against; the duplicate probe answers an empty listing first, which is
        the ordinary shape every start in this module has.
        """
        engine = Engine([answer(stdout=""), answer(stdout="runtime-1\n")])
        self.engine = engine
        adapter = OciAdapter("docker", engine, identity=self.IDENTITY,
                             assignment_roots=dict(self.live_roots),
                             posture="execution", workspace_group=self.group,
                             launch_delivery=self.launched(),
                             mounts=[{"source": self.live_roots["inputs"],
                                      "target": "/input", "writable": False}],
                             **operands)
        adapter.start({"labels": dict(LABELS),
                       "operation_id": "runtime.start:1",
                       "input_root": self.live_roots["inputs"]})
        return next(argv for argv in engine.vectors if "run" in argv)

    # -- the network posture -------------------------------------------------

    def test_naming_nothing_composes_exactly_the_accepted_vector(self):
        """The property that makes this operand safe to have added at all: an
        adapter that names neither operand starts the same container it started
        before either existed."""
        argv = self.started()
        self.assertEqual(argv[argv.index("--network") + 1], "none")
        self.assertNotIn("--interactive", argv)

    def test_an_explicit_posture_reaches_the_argv_exactly_once(self):
        """One `--network`, whatever was asked for. Two would leave the engine
        to decide which won, which is the one thing a closed vector must never
        do."""
        for named in ("none", "bridge", "baton-egress", "host"):
            with self.subTest(network=named):
                argv = run_vector("docker", image_digest=IMAGE, labels=LABELS,
                                  assignment_roots=ROOTS, posture="execution",
                                  workspace_group=self.group,
                                  name="baton-op-1", network=named)
                self.assertEqual(argv.count("--network"), 1, argv)
                self.assertEqual(argv[argv.index("--network") + 1], named)

    def test_a_posture_that_is_not_a_network_name_is_refused(self):
        """The grammar is what keeps this operand a network NAME rather than an
        opening for a second engine argument."""
        for wrong in ("", "-none", "none extra", "../etc", "a" * 200,
                      "net=work", None, 5, ["none"], True):
            with self.subTest(network=wrong):
                with self.assertRaises(ContractRefusal):
                    run_vector("docker", image_digest=IMAGE, labels=LABELS,
                               assignment_roots=ROOTS, posture="execution",
                               workspace_group=self.group, name="baton-op-1",
                               network=wrong)

    def test_the_adapter_refuses_a_bad_posture_before_it_is_built(self):
        """At CONSTRUCTION, like every other assignment-scoped operand here: an
        adapter that cannot say what it may reach should not exist."""
        with self.assertRaises(ContractRefusal):
            self.adapter(network="not a network")

    def test_an_explicit_posture_survives_to_the_started_container(self):
        argv = self.started(network="baton-egress")
        self.assertEqual(argv.count("--network"), 1, argv)
        self.assertEqual(argv[argv.index("--network") + 1], "baton-egress")

    # -- the interactive channel ---------------------------------------------

    def test_interactive_is_composed_only_when_it_is_asked_for(self):
        self.assertNotIn("--interactive", self.started())
        argv = self.started(interactive=True)
        self.assertIn("--interactive", argv)
        # BESIDE `--detach` AND BEFORE THE RESTRICTIONS, so the flag order a
        # reader sees is the order the vector is composed in.
        self.assertLess(argv.index("--interactive"), argv.index("--cap-drop"))

    def test_interactive_takes_a_boolean_and_not_a_number(self):
        """Review [P2]: this was `interactive not in (True, False)`, and
        membership compares by EQUALITY -- so `0` and `1` were accepted at
        construction and then met the vector's exact test one layer later.
        An adapter that builds and cannot start is a refusal in the wrong
        place."""
        for wrong in (0, 1, "true", "", None, [], 2):
            with self.subTest(interactive=wrong):
                with self.assertRaises(ContractRefusal):
                    self.adapter(interactive=wrong)
                with self.assertRaises(ContractRefusal):
                    run_vector("docker", image_digest=IMAGE, labels=LABELS,
                               assignment_roots=ROOTS, posture="execution",
                               workspace_group=self.group, name="baton-op-1",
                               interactive=wrong)

    def test_neither_operand_disturbs_any_other_restriction(self):
        """A widened network and a held-open stdin change those two things and
        nothing else: the capability, privilege, user, filesystem and resource
        posture is the same argv it always was."""
        argv = self.started(network="baton-egress", interactive=True)
        pairs = set(zip(argv, argv[1:]))
        for flag, value in RESTRICTIONS:
            if flag == "--network":
                continue
            with self.subTest(flag=flag, value=value):
                if value is None:
                    self.assertIn(flag, argv)
                else:
                    self.assertIn((flag, value), pairs)


class TheManagersProvedRootsSurviveToTheUse(Configured):
    """W39358 [P1]: an allocation's answer is adopted, never re-derived.

    `AllocatedRoots` is minted only by `assignment_workspace` and
    `adopted_assignment_workspace`, both of which prove each root is a real
    directory of this attempt's own -- not a link, resolving to its own path
    under the configured store. Flattening it to a plain mapping threw that
    away and left the adapter re-resolving pathnames a caller then held, which
    is the check-then-open interval this closes.
    """

    def storage(self):
        place = tempfile.mkdtemp(prefix="v12-proved-roots-")
        self.addCleanup(shutil.rmtree, place, True)
        from baton_v12.worker_manager.workspaces import (
            configure_workspace_storage)
        configure_workspace_storage(self.store, place)
        return place

    def allocated(self):
        from baton_v12.worker_manager.workspaces import assignment_workspace

        return assignment_workspace(self.group, self.storage(), "attempt-1")

    def test_a_nominal_answer_is_accepted_without_being_flattened(self):
        roots = self.allocated()

        held, posture = oci._roots(roots, "execution")

        self.assertEqual(posture, "execution")
        self.assertEqual(sorted(held), ["inputs", "workspace"])
        for name in ("inputs", "workspace"):
            self.assertEqual(held[name], roots[name],
                             "the adapter re-derived a root the manager proved")

    def test_the_answer_the_adapter_holds_is_the_one_it_was_given(self):
        """No second resolution: what the adapter uses is what was proved."""
        roots = self.allocated()

        made = oci.OciAdapter(
            "docker", oci.EnginePort(lambda argv: {"status": 0, "stdout": "",
                                                   "stderr": ""}),
            identity={"image_digest": "sha256:" + "5" * 64,
                      "profile_digest": "sha256:" + "6" * 64,
                      "policy_digest": "sha256:" + "2" * 64,
                      "adapter_digest": "sha256:" + "3" * 64},
            assignment_roots=roots, posture="execution", mounts=[],
            workspace_group=self.group)

        for name in ("inputs", "workspace"):
            self.assertEqual(made.assignment_roots[name], roots[name])

    def test_the_adapter_retains_the_managers_nominal_answer(self):
        """A copied dict loses provenance and is re-resolved at start."""
        roots = self.allocated()

        made = oci.OciAdapter(
            "docker", oci.EnginePort(lambda argv: {"status": 0, "stdout": "",
                                                   "stderr": ""}),
            identity={"image_digest": "sha256:" + "5" * 64,
                      "profile_digest": "sha256:" + "6" * 64,
                      "policy_digest": "sha256:" + "2" * 64,
                      "adapter_digest": "sha256:" + "3" * 64},
            assignment_roots=roots, posture="execution", mounts=[],
            workspace_group=self.group)

        self.assertIs(made.assignment_roots, roots,
                      "construction flattened the manager's nominal answer")

    def test_a_plain_mapping_is_still_proved_here(self):
        """Callers outside the allocation path legitimately hold one, and
        theirs is still canonicalized and contained by this owner."""
        with self.assertRaises(ContractRefusal):
            oci._roots({"inputs": "relative/inputs",
                        "workspace": "relative/workspace"}, "execution")


class ARecoveryEndingNeverClaimsNoCredentialWasDelivered(Adapting):
    """W55758: the false `not-delivered`, and the typed thing that ends it.

    `work/records/2026/08/finding-interrupted-dogfood-attempt-strands-runtime-
    credential/`.

    MEASURED, NOT SUPPOSED. A recovery process is exactly the shape in which
    the in-memory `Delivery` died with the process that materialized it, so a
    reconstructed adapter holds `credential_delivery is None` -- and the
    ending then answered `not-delivered`, positively recording that no
    credential was ever delivered for an attempt that left a readable bearer
    on the host for hours. `_torn_down` chooses that word so a reader cannot
    conclude a credential was torn down because a container was; unqualified
    it made the opposite mistake, and nothing distinguished the record from a
    genuine no-credential attempt.
    """

    def credential_home(self, name="granted"):
        from baton_v12.worker_manager import credentials

        place = os.path.join(self.home, name)
        os.makedirs(place, exist_ok=True)
        return credentials.CredentialHome(place)

    def materialized(self, home, attempt="attempt-1"):
        """One real delivery, whose owning object is then let go."""
        from baton_v12.contracts import forget_secret
        from baton_v12.worker_manager import credentials

        delivery = home.materialize(
            credentials.resolved_delivery(
                ["api"], profile={"api": {"provider": "vault",
                                          "reference": "kv/one"}}),
            attempt_id=attempt, workspace_group=self.group,
            credential_provider=lambda one, two: "c" * 48)
        home.written_state(attempt, delivery.record(runtime_id="runtime-1"))
        for value in delivery.bearers().values():
            forget_secret(value)
        return home

    def orphan(self, *homes, attempt="attempt-1"):
        from baton_v12.worker_manager import credentials

        return credentials.OrphanTeardown(attempt, homes=list(homes))

    def recovering(self, orphan, home=None):
        return OciAdapter(
            "docker", Engine([]), identity=self.IDENTITY,
            assignment_roots=dict(self.live_roots), posture="execution",
            workspace_group=self.group, launch_delivery=None,
            credential_orphan=orphan, credential_home=home)

    ABSENT = {"state": "absent", "why": "the exact runtime is absent"}

    def test_without_an_orphan_the_old_word_is_still_the_true_one(self):
        """An attempt that really delivered nothing says so, unchanged."""
        adapter = self.recovering(None)
        self.assertEqual(adapter._torn_down(self.ABSENT),
                         {"lifecycle_state": "not-delivered"})

    def test_a_recovered_orphan_ends_torn_down_after_positive_absence(self):
        home = self.materialized(self.credential_home())
        adapter = self.recovering(self.orphan(home), home=home)
        answered = adapter._torn_down(self.ABSENT)
        self.assertEqual(answered["lifecycle_state"], "torn-down")
        self.assertNotEqual(answered["lifecycle_state"], "not-delivered")
        self.assertFalse(os.path.lexists(home.volatile_root("attempt-1")))
        self.assertFalse(os.path.exists(home.state_path("attempt-1")))

    def test_a_runtime_not_proved_absent_stops_the_orphan_ending_too(self):
        """The order is the approved one whichever object owns the ending.

        A container this manager cannot say is gone may still be reading the
        mount, and removing the file under it would be reporting an ending
        that has not happened.
        """
        home = self.materialized(self.credential_home())
        adapter = self.recovering(self.orphan(home), home=home)
        answered = adapter._torn_down({"state": "uncertain",
                                       "why": "the engine did not answer"})
        self.assertEqual(answered["lifecycle_state"], "unresolved")
        self.assertTrue(os.path.lexists(home.volatile_root("attempt-1")))

    def test_an_attempt_has_one_credential_ending_and_not_two(self):
        from baton_v12.worker_manager import credentials

        home = self.materialized(self.credential_home())
        delivery = home.adopt(home.read_state("attempt-1"),
                              attempt_id="attempt-1", runtime_id="runtime-1",
                              workspace_group=self.group)
        try:
            with self.assertRaises(ContractRefusal):
                OciAdapter("docker", Engine([]), identity=self.IDENTITY,
                           assignment_roots=dict(self.live_roots),
                           posture="execution", workspace_group=self.group,
                           credential_delivery=delivery,
                           credential_orphan=self.orphan(home))
        finally:
            home.tear_down(delivery)
        del credentials

    def test_an_orphan_teardown_must_be_this_managers_own(self):
        with self.assertRaises(ContractRefusal):
            self.recovering("not a teardown")
        with self.assertRaises(ContractRefusal):
            self.recovering(None, home="/not/a/home/object")

    def test_the_owned_home_is_the_home_this_adapter_uses(self):
        """The one-owner correction, asked of the adapter directly.

        Without it `_credential_home` derived a home from the assignment
        workspace while the deployment materialized under the operator-granted
        one -- two `CredentialHome` objects each assuming the root and the
        record were siblings below themselves, which for a real attempt they
        were not.
        """
        granted = self.credential_home("granted-owner")
        adapter = self.recovering(None, home=granted)
        self.assertIs(adapter._credential_home(), granted)
        # AND AN ADAPTER GIVEN NONE STILL DERIVES ITS OWN, so every caller
        # that never had the split is untouched.
        self.assertEqual(self.recovering(None)._credential_home().place,
                         os.path.dirname(
                             self.live_roots["workspace"].rstrip("/")))


class OneAttemptsEndingNeverRemovesAnothersCredential(
        ARecoveryEndingNeverClaimsNoCredentialWasDelivered):
    """W55758 review (2026-09-01T04:57:06Z) [P1]: the binding that was missing.

    THE MEASURED DEFECT. `OrphanTeardown` carries its own attempt id and this
    adapter checked only its NOMINAL TYPE, so a recovery built over one
    assignment's roots with another attempt's teardown removed that other
    attempt's real credential material on positive absence. A type is not an
    identity, and nothing in the removal path compared the two.

    THE CHECK IS BEFORE THE ENGINE, because a refusal after the engine has
    acted is not a refusal: the mismatched attempt's container would already
    be gone and the wrong credential would be next.
    """

    def command(self, attempt="attempt-1", runtime="runtime-1"):
        return {"assignment_ref": {"authority_uuid": "a" * 32,
                                   "work_id": "w-1", "participant": "p.q",
                                   "generation": 1},
                "runtime_attempt_id": attempt, "runtime_id": runtime,
                "abandonment_record_digest": "sha256:" + "4" * 64,
                "retention_policy_digest": "sha256:" + "5" * 64}

    def removing(self, orphan, home=None, answers=None):
        """An adapter whose engine really answers, so the ORDER is testable."""
        self.engine = Engine(answers if answers is not None
                             else [{"stdout": "", "stderr": "", "status": 0},
                                   {"stdout": "", "stderr": "no such object",
                                    "status": 1}])
        return OciAdapter(
            "docker", self.engine, identity=self.IDENTITY,
            assignment_roots=dict(self.live_roots), posture="execution",
            workspace_group=self.group, launch_delivery=None,
            credential_orphan=orphan, credential_home=home)

    def test_a_teardown_for_another_attempt_refuses_before_the_engine(self):
        other = self.materialized(self.credential_home("other-home"),
                                  attempt="attempt-other")
        orphan = self.orphan(other, attempt="attempt-other")
        adapter = self.removing(orphan, home=other)
        with self.assertRaises(ContractRefusal):
            adapter.destroy_abandoned(self.command(attempt="attempt-1"))
        # NEITHER ATTEMPT WAS TOUCHED, and the engine was never called.
        self.assertTrue(os.path.lexists(
            other.volatile_root("attempt-other")))
        self.assertTrue(os.path.exists(other.state_path("attempt-other")))
        self.assertEqual(self.engine.vectors, [],
                         "a container was removed before the refusal")

    def test_the_matching_attempt_still_ends(self):
        """The positive half, so the refusal above is not passing because
        nothing works: the SAME command reaches the engine and the ending."""
        home = self.materialized(self.credential_home())
        orphan = self.orphan(home)
        adapter = self.removing(orphan, home=home)
        adapter.observe = lambda runtime_id: {
            "runtime_id": runtime_id, "state": "absent",
            "why": "the exact runtime is absent"}
        answered = adapter.destroy_abandoned(self.command())
        self.assertEqual(answered["credentials"]["lifecycle_state"],
                         "torn-down")
        self.assertFalse(os.path.lexists(home.volatile_root("attempt-1")))
        self.assertTrue(self.engine.vectors,
                        "the engine was never asked to remove anything")

    def test_a_removal_that_names_no_attempt_refuses_too(self):
        """An ending that cannot say whose material it is removing is not one
        this manager performs."""
        home = self.materialized(self.credential_home())
        adapter = self.removing(self.orphan(home), home=home)
        with self.assertRaises(ContractRefusal) as raised:
            adapter._removed("runtime-1", "an unnamed")
        # THE REFUSAL IS THIS RULE'S, not an identity door's downstream. A
        # missing operand refused by `boundaries.identity` would answer
        # `integrity/schema` and would leave the rule itself unproved.
        self.assertEqual((raised.exception.category, raised.exception.code),
                         ("refused", "precondition"))
        self.assertIn("names no attempt", raised.exception.message)
        self.assertTrue(os.path.lexists(home.volatile_root("attempt-1")))
        self.assertEqual(self.engine.vectors, [])
