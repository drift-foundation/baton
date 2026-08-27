"""W6633 — the reproducible output step, without a daemon.

`work/records/2026/08/finding-v12-oci-reference-worker-image/`.

`tests/manager/test_worker_container.py` proves the built artefact against a
real engine: two executions of the recipe, one identity. It cannot run without
a daemon and it costs a build each time, so the RULE that makes the identity
reproducible is held here over a layout this file writes itself.

WHAT THIS FILE OWNS is `normalize_layout`: which layers it rewrites, which it
must leave alone, what it removes from the config, and — the property the whole
step exists for — that two layouts differing only in build receipts normalize
to one digest.

WHAT IT DELIBERATELY DOES NOT OWN is whether a real engine accepts the result.
A normalizer that produced a self-consistent layout no daemon would load would
pass every case here, so the load is the daemon gate's to prove and is named
there rather than assumed.
"""

import hashlib
import io
import json
import pathlib
import tarfile
import tempfile
import unittest
from unittest.mock import patch

from tools.worker_image import (EPOCH, build_vector, build_worker_image,
                                normalize_layout, recipe_base, staging_tag)

BASE_CREATED = "2026-08-10T21:02:16.000000000Z"
# One layer the base image contributed, and one the recipe added. The rule that
# tells them apart is the base's own layer set, so the fixture states it.
BASE_LAYER_BODY = b"base layer bytes"


def digest_of(data):
    return "sha256:" + hashlib.sha256(data).hexdigest()


def tar_of(entries):
    """One layer tar. `entries` is (name, kind, mtime) with kind d or f."""
    out = io.BytesIO()
    with tarfile.open(fileobj=out, mode="w", format=tarfile.PAX_FORMAT) as tf:
        for name, kind, mtime in entries:
            info = tarfile.TarInfo(name)
            info.mtime = mtime
            info.uid = info.gid = 0
            info.uname = info.gname = "root"
            if kind == "d":
                info.type = tarfile.DIRTYPE
                info.mode = 0o755
                tf.addfile(info)
            else:
                body = b"program bytes"
                info.size = len(body)
                info.mode = 0o644
                tf.addfile(info, io.BytesIO(body))
    return out.getvalue()


class LayoutCase(unittest.TestCase):
    """A saved OCI layout, written here rather than produced by an engine."""

    def setUp(self):
        self.root = tempfile.TemporaryDirectory(prefix="v12-worker-image-")
        self.addCleanup(self.root.cleanup)
        self.layout = pathlib.Path(self.root.name)

    def blob(self, data):
        digest = digest_of(data)
        algorithm, value = digest.split(":")
        path = self.layout / "blobs" / algorithm / value
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return digest, len(data)

    def write(self, *, clock, recipe_layer=None, extra_config=None,
              history_created=None):
        """One layout: a base layer, one recipe layer, and a config."""
        base_digest, base_size = self.blob(BASE_LAYER_BODY)
        recipe = recipe_layer if recipe_layer is not None else tar_of([
            ("opt", "d", clock), ("opt/baton", "d", clock),
            ("opt/baton/baton_worker.py", "f", 1787650104)])
        recipe_digest, recipe_size = self.blob(recipe)
        config = {
            "created": f"2026-08-25T23:59:{clock % 60:02d}.000000000Z",
            "architecture": "amd64", "os": "linux",
            "container": f"{clock:064x}",
            "container_config": {"Hostname": f"{clock:012x}"},
            "config": {"User": "65532:65532",
                       "Entrypoint": ["python3", "/opt/baton/baton_worker.py"],
                       "Image": f"sha256:{clock:064x}"},
            "rootfs": {"type": "layers",
                       "diff_ids": [base_digest, recipe_digest]},
            "history": [
                {"created": BASE_CREATED, "created_by": "the base"},
                {"created": history_created or
                 f"2026-08-25T23:59:{clock % 60:02d}.000000000Z",
                 "created_by": "COPY baton_worker.py /opt/baton/"}]}
        config.update(extra_config or {})
        config_digest, config_size = self.blob(
            json.dumps(config).encode("utf-8"))
        manifest = {
            "schemaVersion": 2,
            "mediaType": "application/vnd.oci.image.manifest.v1+json",
            "config": {
                "mediaType": "application/vnd.oci.image.config.v1+json",
                "digest": config_digest, "size": config_size},
            "layers": [
                {"mediaType": "application/vnd.oci.image.layer.v1.tar",
                 "digest": base_digest, "size": base_size},
                {"mediaType": "application/vnd.oci.image.layer.v1.tar",
                 "digest": recipe_digest, "size": recipe_size}]}
        manifest_digest, manifest_size = self.blob(
            json.dumps(manifest).encode("utf-8"))
        index = {"schemaVersion": 2,
                 "mediaType": "application/vnd.oci.image.index.v1+json",
                 "manifests": [{
                     "mediaType": manifest["mediaType"],
                     "digest": manifest_digest, "size": manifest_size,
                     "annotations": {"io.containerd.image.name": "staged"}}]}
        (self.layout / "index.json").write_text(json.dumps(index),
                                                encoding="utf-8")
        (self.layout / "oci-layout").write_text(
            json.dumps({"imageLayoutVersion": "1.0.0"}), encoding="utf-8")
        return base_digest

    def normalized(self, base_digest, reference="worker:probe"):
        # AN ORDERED SEQUENCE since review [P1]: ancestry is a prefix, so the
        # base's layers are passed in the base's own order.
        return normalize_layout(self.layout, (base_digest,),
                                BASE_CREATED, reference)

    def config_of(self, digest):
        algorithm, value = digest.split(":")
        return json.loads((self.layout / "blobs" / algorithm / value)
                          .read_text(encoding="utf-8"))


class TwoBuildsReachOneIdentity(LayoutCase):

    def identity(self, clock):
        root = tempfile.TemporaryDirectory(prefix="v12-worker-image-")
        self.addCleanup(root.cleanup)
        self.layout = pathlib.Path(root.name)
        return self.normalized(self.write(clock=clock))

    def test_layouts_differing_only_in_receipts_normalize_to_one_digest(self):
        """The property the whole step exists for.

        The two layouts differ in every place a real pair of builds differs:
        the config timestamp, the intermediate container id, the parent chain
        id, the history entry's timestamp, and the mtime on the directories
        the copy created — which changes the recipe layer's own digest.
        """
        self.assertEqual(self.identity(clock=1787702374),
                         self.identity(clock=1787702375))

    def test_a_real_difference_still_makes_two_identities(self):
        """The other half. A normalizer that answered one digest for two
        different programs would have erased the difference rather than the
        receipt, and every case above would still pass."""
        first = self.identity(clock=1787702374)
        root = tempfile.TemporaryDirectory(prefix="v12-worker-image-")
        self.addCleanup(root.cleanup)
        self.layout = pathlib.Path(root.name)
        other = self.normalized(self.write(
            clock=1787702374,
            recipe_layer=tar_of([("opt", "d", 1787702374),
                                 ("opt/baton", "d", 1787702374),
                                 ("opt/baton/other.py", "f", 1787650104)])))
        self.assertNotEqual(first, other)

    def test_source_checkout_mtime_is_not_part_of_the_image_identity(self):
        """Git carries the file bytes and executable bit, not its mtime.

        Two independent checkouts of the same recipe can therefore present
        identical worker files with different mtimes.  Treating that ambient
        filesystem clock as content makes the claimed reproducible image
        identity depend on when each checkout was populated.
        """
        def identity(file_mtime):
            root = tempfile.TemporaryDirectory(prefix="v12-worker-image-")
            self.addCleanup(root.cleanup)
            self.layout = pathlib.Path(root.name)
            layer = tar_of([("opt", "d", 1787702374),
                            ("opt/baton", "d", 1787702374),
                            ("opt/baton/baton_worker.py", "f", file_mtime)])
            return self.normalized(self.write(clock=1787702374,
                                               recipe_layer=layer))

        self.assertEqual(identity(1787650104), identity(1787659999),
                         "identical source bytes from two checkouts produce "
                         "different image identities")


class OnlyTheRecipesOwnWorkIsRewritten(LayoutCase):

    def test_the_bases_layer_travels_byte_for_byte(self):
        """A normalizer that rewrote the base would be describing a different
        base from the one the recipe pins, which is what the digest pin
        exists to protect."""
        base = self.write(clock=1787702374)
        identity = self.normalized(base)
        config = self.config_of(identity)
        self.assertEqual(config["rootfs"]["diff_ids"][0], base)

    def test_the_recipes_layer_is_rewritten(self):
        base = self.write(clock=1787702374)
        before = self.config_of(self.staged_config())
        after = self.config_of(self.normalized(base))
        self.assertNotEqual(after["rootfs"]["diff_ids"][1],
                            before["rootfs"]["diff_ids"][1])

    def staged_config(self):
        index = json.loads((self.layout / "index.json")
                           .read_text(encoding="utf-8"))
        algorithm, value = index["manifests"][0]["digest"].split(":")
        manifest = json.loads((self.layout / "blobs" / algorithm / value)
                              .read_text(encoding="utf-8"))
        return manifest["config"]["digest"]

    def test_a_layout_whose_layers_are_all_the_bases_refuses(self):
        """Nothing was recognised as this recipe's own, so there is nothing to
        normalize — and answering a digest anyway would be the quiet failure
        this refuses."""
        base = self.write(clock=1787702374)
        every = self.config_of(self.staged_config())["rootfs"]["diff_ids"]
        # IN ORDER. A `frozenset` here would have made the case depend on set
        # iteration order the moment ancestry became a prefix — passing for
        # one arrangement of the same two digests and not the other.
        with self.assertRaises(AssertionError) as caught:
            normalize_layout(self.layout, tuple(every), BASE_CREATED,
                             "worker:probe")
        self.assertIn("nothing this recipe added", str(caught.exception))

    def test_a_layout_sharing_no_layer_with_the_base_refuses(self):
        """The other degenerate answer, and it is the more alarming one: the
        base facts describe a different image from the one that was built, so
        every layer would be rewritten as though the recipe had made it."""
        self.write(clock=1787702374)
        with self.assertRaises(AssertionError) as caught:
            normalize_layout(self.layout, (), BASE_CREATED, "worker:probe")
        self.assertIn("came from the pinned base", str(caught.exception))

    def test_a_partial_base_layer_match_refuses(self):
        """Set membership is not image ancestry.

        The built image must start with every layer of the pinned base in its
        exact order.  Recognising only one of two claimed base layers would
        otherwise let the normalizer rewrite and certify an image that did
        not actually descend from the base whose digest the recipe pins.
        """
        base = self.write(clock=1787702374)
        absent_base_layer = "sha256:" + "f" * 64
        with self.assertRaises(AssertionError):
            normalize_layout(self.layout,
                             (base, absent_base_layer),
                             BASE_CREATED, "worker:probe")

    def test_a_layout_carrying_two_manifests_refuses(self):
        """One built image is one identity. A layout with two is not an
        artefact this step can name."""
        self.write(clock=1787702374)
        index = json.loads((self.layout / "index.json")
                           .read_text(encoding="utf-8"))
        index["manifests"] = index["manifests"] * 2
        (self.layout / "index.json").write_text(json.dumps(index),
                                                encoding="utf-8")
        with self.assertRaises(AssertionError):
            normalize_layout(self.layout, ("sha256:" + "0" * 64,),
                             BASE_CREATED, "worker:probe")


class TheReceiptsAreRemovedAndTheContentIsNot(LayoutCase):

    def normalized_config(self, **spoiled):
        base = self.write(clock=1787702374, **spoiled)
        return self.config_of(self.normalized(base))

    def test_the_build_receipts_are_gone(self):
        config = self.normalized_config()
        self.assertNotIn("container", config)
        self.assertNotIn("container_config", config)
        self.assertNotIn("Image", config["config"])

    def test_the_applied_configuration_is_untouched(self):
        """The receipts go; what the engine will APPLY stays, because that is
        the artefact rather than a note about how it was made."""
        config = self.normalized_config()
        self.assertEqual(config["config"]["User"], "65532:65532")
        self.assertEqual(config["config"]["Entrypoint"],
                         ["python3", "/opt/baton/baton_worker.py"])
        self.assertEqual((config["os"], config["architecture"]),
                         ("linux", "amd64"))

    def test_the_bases_history_keeps_its_own_provenance(self):
        """Only entries newer than the base's `Created` are this build's."""
        config = self.normalized_config()
        self.assertEqual(config["history"][0]["created"], BASE_CREATED)
        self.assertEqual(config["history"][1]["created"],
                         "1970-01-01T00:00:00Z")
        self.assertEqual(config["history"][1]["created_by"],
                         "COPY baton_worker.py /opt/baton/")


class InsideTheRewrittenLayerOnlyTheClockMoves(LayoutCase):

    def rewritten(self):
        base = self.write(clock=1787702374)
        config = self.config_of(self.normalized(base))
        algorithm, value = config["rootfs"]["diff_ids"][1].split(":")
        return self.layout / "blobs" / algorithm / value

    def test_a_directory_takes_the_one_instant(self):
        with tarfile.open(self.rewritten()) as tf:
            times = {m.name: m.mtime for m in tf.getmembers() if m.isdir()}
        self.assertEqual(set(times.values()), {EPOCH}, times)

    def test_two_checkouts_of_one_revision_reach_one_identity(self):
        """The property the mtime rule exists for, stated at the level a
        reader cares about: the same recipe, checked out twice, is one image.

        The real-engine case cannot establish this — it builds twice from ONE
        context, so both builds see one set of source mtimes.
        """
        def identity(file_mtime):
            root = tempfile.TemporaryDirectory(prefix="v12-worker-image-")
            self.addCleanup(root.cleanup)
            self.layout = pathlib.Path(root.name)
            return self.normalized(self.write(clock=1787702374,
                recipe_layer=tar_of([
                    ("opt", "d", 1787702374),
                    ("opt/baton", "d", 1787702374),
                    ("opt/baton/baton_worker.py", "f", file_mtime)])))

        self.assertEqual(identity(1787650104), identity(1799999999))

    def test_normalizing_the_clock_did_not_normalize_the_content(self):
        """The other half, and the one that would make this correction a
        different defect: mode, bytes and member set are content and have to
        survive the rewrite."""
        with tarfile.open(self.rewritten()) as tf:
            members = {m.name: m for m in tf.getmembers()}
            body = tf.extractfile("opt/baton/baton_worker.py").read()
        self.assertEqual(body, b"program bytes")
        self.assertEqual(members["opt/baton/baton_worker.py"].mode, 0o644)
        self.assertEqual(members["opt/baton"].mode, 0o755)
        self.assertEqual(sorted(members),
                         ["opt", "opt/baton", "opt/baton/baton_worker.py"])

    def test_every_member_time_is_the_one_instant(self):
        """REVISED under review [P1]'s explicit confirmation, and the old
        assertion was the defect.

        It required a regular file to keep the mtime it came in with, on the
        reasoning that it "came out of the build context and is content". The
        build context is a checkout, and a checkout does not pin mtimes — the
        version-control source carries bytes and the executable bit and
        nothing about when a working tree was populated. So two fresh
        checkouts of one revision produced two identities.

        A member time is a clock reading whatever member carries it.
        """
        with tarfile.open(self.rewritten()) as tf:
            times = {m.name: m.mtime for m in tf.getmembers()}
        self.assertEqual(set(times.values()), {EPOCH}, times)
        self.assertIn("opt/baton/baton_worker.py", times,
                      "the file left the layer along with its clock")

    def test_the_member_order_is_stable_and_the_bytes_survive(self):
        with tarfile.open(self.rewritten()) as tf:
            members = tf.getmembers()
            names = [m.name for m in members]
            body = tf.extractfile(
                "opt/baton/baton_worker.py").read()
        self.assertEqual(names, sorted(names))
        self.assertEqual(body, b"program bytes")

    def test_the_owner_names_go_and_the_numeric_ids_stay(self):
        """A name is a lookup in whatever passwd file the builder had; the
        numeric id is the fact the kernel will use."""
        with tarfile.open(self.rewritten()) as tf:
            member = tf.getmember("opt/baton/baton_worker.py")
        self.assertEqual((member.uname, member.gname), ("", ""))
        self.assertEqual((member.uid, member.gid), (0, 0))


class TheBuildVectorIsClosed(unittest.TestCase):

    WORKER = (pathlib.Path(__file__).resolve().parents[3] / "worker")

    def test_the_vector_is_exact(self):
        # THE STAGE IS AN OPERAND since review [P1] made it an allocation. A
        # vector that allocated its own would name a reference its caller
        # could not save, remove, or read back — which is the shared-tag
        # defect wearing a different hat.
        argv = build_vector("docker", self.WORKER,
                            self.WORKER / "Dockerfile",
                            "worker:probe-unnormalized-abcdef123456",
                            "linux/amd64")
        self.assertEqual(argv[:6], ["docker", "build", "--no-cache",
                                    "--platform", "linux/amd64", "--tag"])
        self.assertEqual(argv[6], "worker:probe-unnormalized-abcdef123456")
        self.assertEqual(argv[-1], str(self.WORKER))

    def test_an_allocated_stage_still_names_its_destination(self):
        """Unique, and still readable. A leftover stage has to say which
        artefact it was on its way to being."""
        stage = staging_tag("worker:probe")
        self.assertTrue(stage.startswith("worker:probe-"), stage)
        self.assertNotEqual(stage, "worker:probe")

    def test_one_invocation_builds_saves_and_removes_ONE_stage(self):
        """The thread-through, which is what the uniqueness is for. Review
        [P1]: the stage was re-derived at each step, so a second invocation
        could save or delete the reference this one was still using."""
        seen = []

        def record(argv, timeout=900):
            seen.append(list(argv))
            raise AssertionError("stop after the build; nothing to save")

        import tools.worker_image as tool
        real_run, real_facts = tool._run, tool._base_facts
        tool._run = record
        tool._base_facts = lambda engine, base: (("sha256:" + "a" * 64,), "x")
        try:
            with self.assertRaises(AssertionError):
                tool.build_worker_image("docker", self.WORKER,
                                        self.WORKER / "Dockerfile",
                                        "worker:probe", "linux/amd64")
        finally:
            tool._run, tool._base_facts = real_run, real_facts
        build = [argv for argv in seen if argv[1] == "build"][0]
        stage = build[build.index("--tag") + 1]
        removals = [argv for argv in seen if "rm" in argv]
        self.assertTrue(stage.startswith("worker:probe-unnormalized-"), stage)
        # And whatever else this invocation touched, it touched THAT stage.
        for argv in seen:
            for piece in argv:
                if piece.startswith("worker:probe-unnormalized-"):
                    self.assertEqual(piece, stage,
                                     "a second stage reference appeared "
                                     "inside one invocation")
        self.assertEqual(removals, [])

    def test_the_staging_tag_is_never_the_artefact(self):
        self.assertNotEqual(staging_tag("worker:probe"), "worker:probe")
        self.assertIn("worker:probe", staging_tag("worker:probe"))

    def test_concurrent_builds_for_one_destination_have_distinct_stages(self):
        """One build's cleanup must not remove another build's input.

        Deriving the staging reference only from the destination gives two
        simultaneous invocations the same mutable tag.  Either invocation can
        then save or delete the other's unnormalized image.
        """
        stages = {staging_tag("worker:probe") for _ in range(2)}
        self.assertEqual(len(stages), 2,
                         "concurrent builds share one mutable staging tag")

    def test_a_failed_stage_removal_cannot_report_a_successful_build(self):
        """The unnormalized image is not an optional temporary resource.

        Returning the pinnable identity while its mutable staging reference
        remains makes the documented remove-on-every-path guarantee false and
        leaves an image an operator can mistake for build output.
        """
        import tools.worker_image as tool

        def successful(argv, timeout=900):
            return ""

        refused_cleanup = __import__("subprocess").CompletedProcess(
            ["docker", "image", "rm"], 1, b"", b"removal refused")
        with patch.object(tool, "_base_facts", return_value=(
                ("sha256:" + "a" * 64,), "2026-08-10T00:00:00Z")), \
                patch.object(tool, "_run", side_effect=successful), \
                patch.object(tool, "normalize_layout",
                             return_value="sha256:" + "b" * 64), \
                patch.object(tool.subprocess, "run",
                             return_value=refused_cleanup):
            with self.assertRaises(AssertionError):
                build_worker_image("docker", self.WORKER,
                                   self.WORKER / "Dockerfile",
                                   "worker:probe", "linux/amd64")

    def test_a_refused_cleanup_does_not_replace_an_earlier_failure(self):
        """A build that failed and then could not clean up is reported as the
        build failure it is. The cleanup evidence is in the log; it does not
        take the primary failure's place."""
        import tools.worker_image as tool

        def failing(argv, timeout=900):
            raise AssertionError("the engine refused to build")

        refused = __import__("subprocess").CompletedProcess(
            ["docker", "image", "rm"], 1, b"", b"removal refused")
        with patch.object(tool, "_base_facts", return_value=(
                ("sha256:" + "a" * 64,), "2026-08-10T00:00:00Z")), \
                patch.object(tool, "_run", side_effect=failing), \
                patch.object(tool.subprocess, "run", return_value=refused):
            with self.assertRaises(AssertionError) as caught:
                tool.build_worker_image("docker", self.WORKER,
                                        self.WORKER / "Dockerfile",
                                        "worker:probe", "linux/amd64")
        self.assertIn("refused to build", str(caught.exception),
                      "a cleanup refusal replaced the failure that mattered")

    def test_a_refused_cleanup_is_attached_to_the_earlier_failure(self):
        """Preserving the primary exception is only half the requirement.

        The surviving mutable stage still needs actionable evidence.  A
        captured removal result that is discarded while the primary exception
        unwinds is silent cleanup failure, not retained evidence.
        """
        import tools.worker_image as tool

        def failing(argv, timeout=900):
            raise AssertionError("the engine refused to build")

        refused = __import__("subprocess").CompletedProcess(
            ["docker", "image", "rm"], 1, b"", b"removal refused")
        with patch.object(tool, "_base_facts", return_value=(
                ("sha256:" + "a" * 64,), "2026-08-10T00:00:00Z")), \
                patch.object(tool, "_run", side_effect=failing), \
                patch.object(tool.subprocess, "run", return_value=refused):
            with self.assertRaises(AssertionError) as caught:
                tool.build_worker_image("docker", self.WORKER,
                                        self.WORKER / "Dockerfile",
                                        "worker:probe", "linux/amd64")
        notes = getattr(caught.exception, "__notes__", ())
        self.assertTrue(any("removal refused" in note for note in notes),
                        "the cleanup refusal was captured and discarded")

    def test_a_cleanup_exception_cannot_replace_an_earlier_failure(self):
        """The cleanup process can fail to start or time out as well as
        return nonzero.  That path must preserve the earlier build failure by
        the same rule; a cleanup exception is evidence, not a new primary.
        """
        import tools.worker_image as tool

        def failing(argv, timeout=900):
            raise AssertionError("the engine refused to build")

        timeout = tool.subprocess.TimeoutExpired(
            ["docker", "image", "rm"], 120, stderr=b"cleanup timed out")
        with patch.object(tool, "_base_facts", return_value=(
                ("sha256:" + "a" * 64,), "2026-08-10T00:00:00Z")), \
                patch.object(tool, "_run", side_effect=failing), \
                patch.object(tool.subprocess, "run", side_effect=timeout):
            with self.assertRaises(AssertionError) as caught:
                tool.build_worker_image("docker", self.WORKER,
                                        self.WORKER / "Dockerfile",
                                        "worker:probe", "linux/amd64")
        self.assertIn("refused to build", str(caught.exception),
                      "the cleanup exception replaced the primary failure")

    def test_the_base_is_read_from_the_recipe_and_pinned_by_digest(self):
        """One place names the base. A second copy of the digest in the tool
        would be a second thing to keep true."""
        base = recipe_base(self.WORKER / "Dockerfile")
        self.assertRegex(base, r"^python@sha256:[0-9a-f]{64}$")

    def test_a_recipe_with_no_base_refuses(self):
        empty = tempfile.NamedTemporaryFile("w", suffix=".Dockerfile",
                                            delete=False)
        empty.write("# nothing here names an image\n")
        empty.close()
        self.addCleanup(lambda: pathlib.Path(empty.name).unlink())
        with self.assertRaises(AssertionError):
            recipe_base(empty.name)


if __name__ == "__main__":
    unittest.main()
