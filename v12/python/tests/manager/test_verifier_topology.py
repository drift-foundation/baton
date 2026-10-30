"""W325695 — THE JOINED PROOF: one topology, composed by the manager and
proved by the worker.

WHY THIS MODULE EXISTS AND WHY IT IS NOT IN EITHER SIDE'S SUITE.
`tests/manager/test_claude_agent.py` deliberately never spells `baton_v12`,
because the adapter it tests runs in an image where that package does not
exist; `tests/manager/test_source_boundary.py` tests a manager module that
must not import a worker. Neither can ask the question review
2026-10-28T03-25-24Z requires an answer to:

    "Source tests must show the configured pair reaches ordinary
    descendant/nested use while incompatible pairs, missing roots,
    replacement and exhaustion refuse honestly."

That is a question about the PAIR, so it is asked here, where both sides are
imported and nothing translates between them.

WHAT IS REAL IN THIS MODULE, and it is almost all of it: the manager's
composition, the image marker it derives, the document bytes, the worker's
reading of both, every refusal in both directions, the capacity partition and
the engine argv.

WHAT IS SUBSTITUTED, at one point each and labelled where it happens: the
MOUNT TABLE, because an unprivileged test cannot mount four private tmpfs
filesystems, and the root-owned 0755 image scaffolding above them. Those two
are the separately selected corrected-image/kernel proof, which this module
does not claim and `TheSelectedPolicyConstants` in the adapter suite pins the
constants of.
"""

import contextlib
import json
import os
import pathlib
import shutil
import stat
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "src"))
WORKER = pathlib.Path(__file__).resolve().parents[3] / "worker"
sys.path.insert(0, str(WORKER))
sys.path.insert(0, str(WORKER.parent / "python" / "src" / "baton_v12"))
shutil.rmtree(WORKER / "__pycache__", ignore_errors=True)

import claude_agent                                             # noqa: E402
from baton_v12.contracts import ContractRefusal                 # noqa: E402
from baton_v12.worker_manager import (oci, source_boundary,     # noqa: E402
                                      workspaces)
from baton_v12.worker_manager.store import ControlStore          # noqa: E402
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from tools import single_worker                                  # noqa: E402

from . import input_roots                                        # noqa: E402

AGENT = claude_agent.ClaudeAgent
ROOT_NAMES = tuple(name for name, _target, _size in
                   source_boundary.VERIFIER_ROOTS)
# The same closed label set `tests/manager/test_oci.py` composes, because a
# runtime's labels are a required operand and inventing a second shape here
# would be inventing a fence.
LABELS = {"runtime_attempt_id": "attempt-w325695",
          "authority_uuid": "2b077949c86e8bef24304f59c28ec398",
          "work_id": "2b077949-W325695", "participant": "baton.claude",
          "generation": 1,
          "principal": "principal:org-a",
          "effective_scope": "scope:deployment",
          "profile_digest": "sha256:" + "b" * 64,
          "policy_digest": "sha256:" + "d" * 64,
          "adapter_digest": "sha256:" + "c" * 64}


# The four digests one adapter is constructed under, and the ones a layout
# selection must agree with. `oci.RESOLVED_IDENTITY` member for member,
# because the adapter compares them that way.
IDENTITY = {"image_digest": "sha256:" + "d" * 64,
            "profile_digest": "sha256:" + "b" * 64,
            "policy_digest": "sha256:" + "d" * 64,
            "adapter_digest": "sha256:" + "c" * 64}


class SimpleIdentity:
    """A uid/gid pair wearing the right member names and nothing else.

    The counterexample for `compose_verifier_layout`'s capability check: a
    duck-typed stand-in is exactly what a caller COULD build, so a check that
    read `.uid`/`.gid` off whatever it was handed would accept it.
    """

    def __init__(self, uid, gid):
        self.uid = uid
        self.gid = gid


def minted_identity(case):
    """THE DEPLOYMENT'S OWN EXECUTION IDENTITY, minted through the record.

    A fixture cannot mint a `WorkspaceGroup` or a `WorkspaceIdentity` any more
    than a caller can -- `input_roots.configured_group` configures one and
    reads the manager's own record back, which is the sequence a deployment
    performs, and `workspaces.identity_for` derives the identity from it.
    """
    store = ControlStore.open(
        os.path.join(tempfile.mkdtemp(dir=case.home), "control.sqlite3"),
        incarnation="w325695-topology",
        clock=lambda: "2026-10-28T00:00:00.000Z")
    case.addCleanup(store.close)
    return workspaces.identity_for(input_roots.configured_group(store))


def composed(identity, *, marker=False, **changed):
    """One manager-composed selection, or whatever refusal it raises."""
    held = source_boundary.compose_verifier_layout(
        marker=(source_boundary.image_layout_marker() if marker is False
                else marker),
        identity=identity, **IDENTITY)
    held.update(changed)
    return held


class TheTopologyIsOneSelectionOnBothSides(unittest.TestCase):
    """The manager composes and the worker proves THE SAME topology.

    Two spellings of one selection agree until they don't, and this is the
    seam where a drift would be invisible at runtime: the manager would mount
    roots the worker does not prove, or the worker would prove roots the
    manager does not mount, and the only symptom would be a refusal nobody
    could attribute. Nothing here is substituted.
    """

    def test_the_fixed_roots_are_the_same_four_paths_on_both_sides(self):
        mounted = {name: target for name, target, _size
                   in source_boundary.VERIFIER_ROOTS}
        self.assertEqual(mounted, AGENT.LAYOUT_ROOTS)

    def test_the_fixed_roots_are_the_topology_the_packet_names(self):
        """`preparation-325908/TASK.md`: fixed
        /run/baton-verifier/{home,tmp,cache,pycache}."""
        self.assertEqual(
            AGENT.LAYOUT_ROOTS,
            {"HOME": "/run/baton-verifier/home",
             "TMPDIR": "/run/baton-verifier/tmp",
             "XDG_CACHE_HOME": "/run/baton-verifier/cache",
             "PYTHONPYCACHEPREFIX": "/run/baton-verifier/pycache"})

    def test_the_four_roots_are_disjoint(self):
        """Review [R1]: "The same mounted directory could be named for all
        four roles by this parser.""" ""
        places = list(AGENT.LAYOUT_ROOTS.values())
        self.assertEqual(len(set(places)), 4)
        for one in places:
            for other in places:
                if one is other:
                    continue
                self.assertFalse(one.startswith(other.rstrip("/") + "/"),
                                 (one, other))

    def test_the_filesystem_options_and_mode_agree(self):
        self.assertEqual(source_boundary.VERIFIER_FILESYSTEM,
                         AGENT.LAYOUT_FILESYSTEM)
        self.assertEqual(sorted(source_boundary.VERIFIER_OPTIONS),
                         sorted(AGENT.LAYOUT_OPTIONS))
        self.assertEqual(source_boundary.VERIFIER_MODE, AGENT.LAYOUT_MODE)

    def test_the_two_schemas_and_targets_agree(self):
        self.assertEqual(source_boundary.LAYOUT_SCHEMA, AGENT.LAYOUT_SCHEMA)
        self.assertEqual(source_boundary.LAYOUT_TARGET, AGENT.LAYOUT_DOCUMENT)
        self.assertEqual(source_boundary.MARKER_SCHEMA, AGENT.MARKER_SCHEMA)
        self.assertEqual(source_boundary.MARKER_TARGET, AGENT.LAYOUT_MARKER)

    def test_the_document_members_agree(self):
        self.assertEqual(sorted(source_boundary.LAYOUT_MEMBERS),
                         sorted(AGENT.LAYOUT_MEMBERS))
        self.assertEqual(sorted(source_boundary.MARKER_MEMBERS),
                         sorted(AGENT.MARKER_MEMBERS))


class TheCapacityPartitionIsTheOneThePacketSelected(unittest.TestCase):
    """The per-root limits, published and accounted. Nothing substituted.

    TASK.md: "/tmp 32MiB, /dev/shm 16MiB, verifier home 4MiB, tmp 16MiB,
    cache 4MiB, pycache 8MiB. Aggregate scratch 80MiB unchanged, workspace
    floor strictly above 80MiB unchanged... total tmpfs 96MiB... This
    redistributes old shared /tmp 64MiB, not extra capacity. Publish exact
    per-root limits."
    """

    def test_every_per_root_limit_is_the_selected_one(self):
        self.assertEqual(
            {name: size >> 20 for name, _target, size
             in source_boundary.VERIFIER_ROOTS},
            {"HOME": 4, "TMPDIR": 16, "XDG_CACHE_HOME": 4,
             "PYTHONPYCACHEPREFIX": 8})

    def test_the_shared_scratch_gave_up_exactly_what_the_roots_took(self):
        """A REDISTRIBUTION, not extra capacity -- and ON THE SELECTED PATH
        ONLY. Review [3]: the first cut reduced the shared `/tmp` for every
        runtime, so an unselected one paid for a topology nothing selected."""
        self.assertEqual(source_boundary.SCRATCH_BYTES, 64 << 20)
        self.assertEqual(source_boundary.VERIFIER_SCRATCH_BYTES, 32 << 20)
        self.assertEqual(
            sum(size for _n, _t, size in source_boundary.VERIFIER_ROOTS),
            source_boundary.SCRATCH_BYTES
            - source_boundary.VERIFIER_SCRATCH_BYTES)

    def test_the_legacy_table_is_exactly_what_it_always_was(self):
        """The preserved path, by value: two mounts at their original sizes
        and not one verifier root among them."""
        self.assertEqual(source_boundary.SCRATCH_MOUNTS,
                         (("/tmp", 64 << 20), ("/dev/shm", 16 << 20)))

    def test_both_tables_hold_the_same_aggregate(self):
        """So a deployment neither gains nor loses room by selecting the new
        topology, and the workspace floor is one number either way."""
        self.assertEqual(
            sum(size for _t, size in source_boundary.SCRATCH_MOUNTS),
            sum(size for _t, size
                in source_boundary.SELECTED_SCRATCH_MOUNTS))

    def test_the_aggregate_and_the_workspace_floor_are_unchanged(self):
        self.assertEqual(source_boundary.SCRATCH_AGGREGATE_BYTES, 80 << 20)
        self.assertEqual(source_boundary.MIN_WORKSPACE_BYTES, 80 << 20)

    def test_the_floor_is_derived_from_the_aggregate(self):
        """And the aggregate is asserted equal across both tables, so the
        floor cannot be left behind by whichever one a runtime gets."""
        self.assertEqual(
            source_boundary.MIN_WORKSPACE_BYTES,
            sum(size for _target, size in source_boundary.SCRATCH_MOUNTS))
        self.assertEqual(
            source_boundary.MIN_WORKSPACE_BYTES,
            sum(size for _target, size
                in source_boundary.SELECTED_SCRATCH_MOUNTS))

    def test_the_total_tmpfs_is_ninety_six_mebibytes(self):
        """80 MiB of scratch plus the existing 16 MiB legacy log decoy, which
        TASK.md keeps separately accounted."""
        from baton_v12.worker_manager import attempt_logs
        decoy = [one for flag, one in oci.RESTRICTIONS
                 if flag == "--tmpfs"
                 and one.startswith(f"{attempt_logs.LEGACY_LOG_TARGET}:")]
        self.assertEqual(decoy,
                         ["/room:rw,noexec,nosuid,nodev,size=16m"
                          if attempt_logs.LEGACY_LOG_TARGET == "/room"
                          else f"{attempt_logs.LEGACY_LOG_TARGET}"
                               f":rw,noexec,nosuid,nodev,size=16m"])
        self.assertEqual((source_boundary.SCRATCH_AGGREGATE_BYTES >> 20) + 16,
                         96)

    def test_no_root_is_in_the_unconditional_restrictions(self):
        """Review [3]: `oci.RESTRICTIONS` is applied to EVERY run, so a
        verifier root in that table is one an unselected runtime gets."""
        composed = dict(one.split(":", 1) for flag, one in oci.RESTRICTIONS
                        if flag == "--tmpfs")
        for _name, target, _size in source_boundary.VERIFIER_ROOTS:
            self.assertNotIn(target, composed, target)
        self.assertEqual(composed["/tmp"],
                         "rw,noexec,nosuid,nodev,size=64m")

    def test_a_workspace_at_the_floor_still_refuses(self):
        """The floor is strictly above the aggregate, as it was before."""
        with self.assertRaises(ContractRefusal):
            source_boundary.workspace_capacity(
                source_boundary.MIN_WORKSPACE_BYTES)
        self.assertEqual(
            source_boundary.workspace_capacity(
                source_boundary.MIN_WORKSPACE_BYTES + 1).max_bytes,
            source_boundary.MIN_WORKSPACE_BYTES + 1)


class TheImageRecipeScaffoldsAndDeclaresTheTopology(unittest.TestCase):
    """The image half, read as bytes. Nothing substituted and nothing built.

    This does NOT claim the image is correct when built -- building it is the
    separately selected image/kernel proof. What it claims is narrower and
    checkable: the recipe creates the mountpoints the manager mounts over and
    ships a marker whose bytes are the composer's own, so the two halves
    cannot drift silently between claims.
    """

    RECIPE = WORKER / "Dockerfile.claude"
    MARKER = WORKER / "verifier-layout-marker.json"

    def setUp(self):
        self.lines = self.RECIPE.read_text(encoding="utf-8").splitlines()

    def test_the_marker_bytes_are_the_composed_ones(self):
        """THE AGREEMENT, PROVED ON THE SHIPPED FILE.

        The marker is literal bytes in the repository so pinned source/image
        checks bind exactly them. That only stays honest if the bytes equal
        what `source_boundary.image_layout_marker()` composes, which is what
        this asserts -- a drift in either direction fails here rather than at
        a deployment nobody can attribute.
        """
        self.assertEqual(json.loads(self.MARKER.read_text(encoding="utf-8")),
                         source_boundary.image_layout_marker())

    def test_the_shipped_marker_is_accepted_by_the_worker(self):
        """The adapter reads the file the image will actually carry."""
        held = AGENT.__new__(AGENT)
        held.LAYOUT_MARKER = str(self.MARKER)
        read = held._trusted_marker()
        self.assertEqual(read["layout_digest"],
                         source_boundary.layout_digest())
        self.assertEqual(read["roots"], AGENT.LAYOUT_ROOTS)

    def test_the_recipe_scaffolds_every_root(self):
        text = "\n".join(self.lines)
        for _name, target, _size in source_boundary.VERIFIER_ROOTS:
            self.assertIn(target, text, target)

    def test_the_scaffolding_is_made_before_privilege_drops(self):
        """Root-owned 0755 image directories: an unprivileged layer could not
        create them, so the ordering is load-bearing."""
        made = [index for index, line in enumerate(self.lines)
                if source_boundary.VERIFIER_PARENT in line]
        dropped = [index for index, line in enumerate(self.lines)
                   if line.startswith("USER ")]
        self.assertTrue(made, "the recipe scaffolds nothing")
        self.assertTrue(dropped, "the recipe never drops privilege")
        self.assertLess(max(made), min(dropped))

    def test_the_marker_is_copied_to_the_path_the_worker_reads(self):
        copied = [line for line in self.lines
                  if line.startswith("COPY")
                  or source_boundary.MARKER_TARGET in line]
        self.assertTrue(
            any(source_boundary.MARKER_TARGET in line for line in copied),
            f"the recipe never places {source_boundary.MARKER_TARGET}")
        self.assertEqual(source_boundary.MARKER_TARGET, AGENT.LAYOUT_MARKER)

    def test_the_marker_is_not_owned_by_the_runtime_identity(self):
        """It is image bytes in a read-only rootfs, so a worker cannot
        rewrite it to agree with a document it was given. Asserted as the
        ABSENCE of a chown to the runtime uid over it."""
        for line in self.lines:
            if source_boundary.MARKER_TARGET in line:
                self.assertNotIn("chown", line)
                self.assertNotIn("65532", line)

    def test_the_scaffolding_is_not_chowned_to_the_runtime_identity(self):
        """A writable ancestor is a directory a process sharing this uid can
        rename, which is the race the mechanism exists to leave."""
        for line in self.lines:
            if source_boundary.VERIFIER_PARENT in line and "chown" in line:
                self.assertIn("0:0", line)
                self.assertNotIn("65532", line)


class TheComposedPairIsAcceptedAndIncompatibleOnesRefuse(unittest.TestCase):
    """THE JOINED CASE. The manager composes; the worker reads what it wrote.

    The document and marker bytes are the manager's own, written to disk and
    read back by the adapter with no translation. Nothing is substituted in
    this class: `_selected_layout` and `_trusted_marker` touch the filesystem
    only for these two documents.
    """

    def setUp(self):
        self.home = tempfile.mkdtemp(prefix="v12-w325695-")
        self.addCleanup(shutil.rmtree, self.home, True)
        self.agent = AGENT.__new__(AGENT)
        self.agent._seen = {}
        self.agent.LAYOUT_DOCUMENT = os.path.join(self.home, "layout.json")
        self.agent.LAYOUT_MARKER = os.path.join(self.home, "marker.json")

    def marker(self, document=None):
        document = (source_boundary.image_layout_marker()
                    if document is None else document)
        with open(self.agent.LAYOUT_MARKER, "w", encoding="utf-8") as handle:
            json.dump(document, handle)
        return document

    def document(self, **changed):
        held = composed(minted_identity(self), **changed)
        with open(self.agent.LAYOUT_DOCUMENT, "w", encoding="utf-8") as handle:
            json.dump(held, handle)
        return held

    # -- the compatible pair ------------------------------------------------

    def test_the_managers_document_is_accepted_by_the_worker(self):
        """ONE SELECTION, END TO END, with nothing in between."""
        self.marker()
        composed = self.document()
        read = self.agent._selected_layout()
        self.assertEqual(read, composed)
        self.assertEqual(read["roots"], AGENT.LAYOUT_ROOTS)
        self.assertEqual(read["layout_digest"],
                         source_boundary.layout_digest())

    def test_the_managers_document_carries_no_unexpected_member(self):
        """The worker refuses extras, so the composer may not add one."""
        self.marker()
        self.assertEqual(sorted(self.document()),
                         sorted(AGENT.LAYOUT_MEMBERS))

    def test_the_trusted_identity_is_the_minted_one(self):
        """TASK.md: "not hardcoded 65532, not ambient login group."

        It is NEITHER, and the capability is what makes that checkable: the
        document's pair is `workspaces.identity_for`'s -- this manager's own
        effective uid behind the deployment's MINTED workspace group -- which
        is the same object `oci.run_vector` composes into `--user`. So the
        assertion is not "it is this number" but "it is the minted identity
        and nothing a caller chose", and the 65532 the recipe drops to is
        deliberately not it.
        """
        self.marker()
        self.document()
        identity = minted_identity(self)
        read = self.agent._selected_layout()
        self.assertEqual((read["uid"], read["gid"]),
                         (identity.uid, identity.gid))
        self.assertNotEqual(read["uid"], 65532)
        self.assertNotEqual(read["uid"], 0)

    # -- the explicitly legacy deployment, which keeps working --------------

    def test_neither_document_is_legacy_and_reads_no_mount_table(self):
        """Supported, unchanged, and it costs nothing."""
        def refuse(cls, place=None):
            raise AssertionError("legacy read the mount table")

        with mock.patch.object(AGENT, "_mount_facts", classmethod(refuse)):
            self.assertIsNone(self.agent._selected_layout())

    # -- both incompatible directions, before the provider -----------------

    def test_an_old_image_with_a_new_document_refuses(self):
        """No marker: the image has no scaffolding to honour the selection."""
        self.document()
        with self.assertRaises(claude_agent.TaskRefusal) as caught:
            self.agent._selected_layout()
        said = str(caught.exception)
        self.assertIn("declares no verifier-layout marker", said)
        self.assertIn("refuses before the provider", said)

    def test_a_new_image_with_no_document_refuses(self):
        """A marker and no delivery: the gap absence used to swallow."""
        self.marker()
        with self.assertRaises(claude_agent.TaskRefusal) as caught:
            self.agent._selected_layout()
        said = str(caught.exception)
        self.assertIn("no trusted layout selection was delivered", said)
        self.assertIn("refuses before the provider", said)

    def test_the_manager_refuses_to_compose_for_an_old_image(self):
        """THE MANAGER-SIDE REFUSAL the review asked for by name.

        "An old worker cannot be made to reject a document it does not read
        merely by adding a schema check to the new worker; prove manager-side
        incompatibility refusal too." An old image carries no marker, and the
        composer will not write a selection it cannot honour -- so no runtime
        starts, rather than a new worker being relied on to decline.
        """
        with self.assertRaises(ContractRefusal) as caught:
            composed(minted_identity(self), marker=None)
        said = str(caught.exception)
        self.assertIn("declares no verifier-layout marker", said)
        self.assertIn("/run/baton-verifier", said)

    def test_the_manager_refuses_a_marker_from_another_topology(self):
        """A new image built from a DIFFERENT topology, caught at compose."""
        stale = dict(source_boundary.image_layout_marker(),
                     layout_digest="0" * 64)
        with self.assertRaises(ContractRefusal) as caught:
            composed(minted_identity(self), marker=stale)
        self.assertIn("were selected from different topologies",
                      str(caught.exception))

    def test_the_manager_refuses_a_named_identity(self):
        """THE REVIEW'S CORRECTION, DRIVEN: "Bind selected topology and
        effective UID/GID through the actual owner composition, not
        self-assertion in an arbitrary document."

        A caller holding two integers -- even the right two -- cannot compose
        a selection. That is what makes the document's identity the one the
        runtime is started under rather than one somebody wrote down: the only
        way to hold a `WorkspaceIdentity` is for this deployment to have
        minted it.
        """
        identity = minted_identity(self)
        for named in (None, 65532, (identity.uid, identity.gid),
                      {"uid": identity.uid, "gid": identity.gid},
                      SimpleIdentity(identity.uid, identity.gid)):
            with self.subTest(named=named):
                with self.assertRaises(ContractRefusal) as caught:
                    composed(named)
                self.assertIn("minted execution identity",
                              str(caught.exception))

    def test_a_document_from_another_topology_refuses_at_the_worker(self):
        self.marker()
        self.document(layout_digest="0" * 64)
        with self.assertRaises(claude_agent.TaskRefusal) as caught:
            self.agent._selected_layout()
        self.assertIn("produced from different topologies",
                      str(caught.exception))

    def test_a_marker_from_another_topology_refuses_at_the_worker(self):
        self.marker(dict(source_boundary.image_layout_marker(),
                         roots={name: f"/elsewhere/{name.lower()}"
                                for name in ROOT_NAMES}))
        self.document()
        with self.assertRaises(claude_agent.TaskRefusal) as caught:
            self.agent._selected_layout()
        self.assertIn("marker declares roots", str(caught.exception))

    def test_a_truncated_document_is_not_legacy(self):
        self.marker()
        with open(self.agent.LAYOUT_DOCUMENT, "w", encoding="utf-8") as one:
            one.write("{not json")
        with self.assertRaises(claude_agent.TaskRefusal) as caught:
            self.agent._selected_layout()
        self.assertIn("does not fall back to the old one",
                      str(caught.exception))

    def test_a_truncated_marker_is_not_an_old_image(self):
        with open(self.agent.LAYOUT_MARKER, "w", encoding="utf-8") as one:
            one.write("{not json")
        self.document()
        with self.assertRaises(claude_agent.TaskRefusal) as caught:
            self.agent._selected_layout()
        self.assertIn("does not fall back to the old one",
                      str(caught.exception))


class TheDocumentIsDeliveredReadOnlyAtItsFixedTarget(unittest.TestCase):
    """The delivery itself: type, target and immutability. Nothing
    substituted.

    Review: "protect document delivery, type, ownership and immutability."
    """

    def setUp(self):
        self.home = tempfile.mkdtemp(prefix="v12-w325695-oci-")
        self.addCleanup(shutil.rmtree, self.home, True)
        self.identity = minted_identity(self)
        self.storage = os.path.join(self.home, "layout-storage")
        os.makedirs(self.storage, 0o700)

    def delivered(self, **changed):
        """THE REAL DELIVERY: composed, written and read back as bytes."""
        return source_boundary.materialize_verifier_layout(
            self.storage, document=composed(self.identity, **changed))

    def test_the_delivery_is_the_fixed_target(self):
        _source, target = self.delivered().mount()
        self.assertEqual(target, "/run/baton/verifier-layout.json")
        self.assertEqual(target, AGENT.LAYOUT_DOCUMENT)

    def test_the_materialized_bytes_are_the_composed_ones(self):
        held = self.delivered()
        with open(held.place, "rb") as reading:
            self.assertEqual(reading.read(),
                             source_boundary.layout_bytes(held.document))

    def test_the_delivered_document_is_readable_and_not_writable(self):
        """The container's execution identity must be able to READ it, and
        nothing may write it. `launch.materialize`'s rule: a creation mode is
        filtered by the umask, so the mode is set on the descriptor after the
        last byte rather than asked for at creation."""
        held = self.delivered()
        mode = stat.S_IMODE(os.lstat(held.place).st_mode)
        self.assertEqual(mode, 0o444)

    def test_the_same_selection_twice_adopts_the_same_bytes(self):
        """A per-deployment selection, not a per-attempt one: refusing the
        second start of one deployment would mean it could serve exactly one
        runtime."""
        first = self.delivered()
        second = self.delivered()
        self.assertEqual(first.place, second.place)
        self.assertEqual(first.document, second.document)

    def test_a_changed_selection_at_the_name_refuses(self):
        """Live runtimes were started against the bytes on disk."""
        self.delivered()
        with self.assertRaises(ContractRefusal) as caught:
            self.delivered(policy_digest="sha256:" + "e" * 64)
        self.assertIn("different verifier-layout selection is already "
                      "delivered", str(caught.exception))

    def test_a_link_at_the_name_refuses_rather_than_being_read_through(self):
        elsewhere = os.path.join(self.home, "elsewhere.json")
        with open(elsewhere, "w", encoding="utf-8") as handle:
            handle.write("{}")
        os.makedirs(os.path.join(self.storage, "verifier-layout"), 0o700,
                    exist_ok=True)
        os.symlink(elsewhere, os.path.join(self.storage, "verifier-layout",
                                           source_boundary.LAYOUT_NAME))
        with self.assertRaises(ContractRefusal) as caught:
            self.delivered()
        self.assertIn("refused rather than read through",
                      str(caught.exception))

    def test_a_pair_of_paths_is_not_a_delivery(self):
        """A path operand would be a caller-selected locator for the one
        document the verifier's roots are proved against."""
        held = self.delivered()
        for named in (held.place, (held.place, source_boundary.LAYOUT_TARGET),
                      {"source": held.place}):
            with self.subTest(named=named):
                with self.assertRaises(ContractRefusal) as caught:
                    oci._layout_mount(named)
                self.assertIn("one this manager materialized",
                              str(caught.exception))

    def test_a_delivery_whose_document_is_gone_refuses(self):
        """The type proof is about the OBJECT and is taken when the vector is
        composed, not when the document was written -- so a delivery whose
        bytes were removed in between refuses rather than composing a bind
        the engine would fail on."""
        held = self.delivered()
        os.unlink(held.place)
        with self.assertRaises(ContractRefusal) as caught:
            oci._layout_mount(held)
        self.assertIn("not a regular file", str(caught.exception))

    def vector(self, **changed):
        """One execution runtime, with the operands this posture requires."""
        held = dict(
            image_digest=IDENTITY["image_digest"],
            labels=LABELS,
            assignment_roots={"inputs": os.path.join(self.home, "inputs"),
                              "workspace": os.path.join(self.home, "work")},
            posture="execution", name="w325695-topology",
            workspace_group=input_roots.configured_group(self.store()))
        held.update(changed)
        return oci.run_vector("docker", **held)

    def store(self):
        store = ControlStore.open(
            os.path.join(tempfile.mkdtemp(dir=self.home), "control.sqlite3"),
            incarnation="w325695-topology",
            clock=lambda: "2026-10-28T00:00:00.000Z")
        self.addCleanup(store.close)
        return store

    def test_the_engine_binds_it_read_only(self):
        """IMMUTABILITY IS NOT A PARAMETER: a worker that could rewrite its
        own layout selection could name its own roots, and the proof would be
        about whatever it chose."""
        held = self.delivered()
        argv = self.vector(layout_delivered=held)
        wanted = (f"type=bind,source={held.place},"
                  f"target={source_boundary.LAYOUT_TARGET},readonly=true")
        self.assertIn(wanted, argv)

    def test_the_document_names_the_identity_the_argv_composes(self):
        """THE ONE OPINION, NOT TWO. `--user` and the document's uid/gid come
        from the same minted capability, and this reads both out of the argv
        this manager would hand the engine."""
        held = self.delivered()
        argv = self.vector(layout_delivered=held)
        at = argv.index("--user")
        self.assertEqual(argv[at + 1],
                         f"{held.document['uid']}:{held.document['gid']}")

    def test_a_document_naming_another_identity_refuses(self):
        """It would describe roots this container cannot own, and the worker
        would refuse mid-run on ownership instead of here with nothing
        started."""
        held = self.delivered()
        held.document = dict(held.document, uid=held.document["uid"] + 1)
        with self.assertRaises(ContractRefusal) as caught:
            self.vector(layout_delivered=held)
        self.assertIn("this container cannot own", str(caught.exception))

    def test_a_document_bound_to_another_image_refuses(self):
        held = self.delivered()
        with self.assertRaises(ContractRefusal) as caught:
            self.vector(layout_delivered=held,
                        image_digest="sha256:" + "f" * 64)
        self.assertIn("composed for another image", str(caught.exception))

    def test_a_consent_runtime_takes_no_selection(self):
        """It mounts nothing and runs no verifier, so a selection there is a
        grant with no object -- and it has no execution identity for the
        document to name."""
        with self.assertRaises(ContractRefusal) as caught:
            self.vector(layout_delivered=self.delivered(), posture="consent",
                        workspace_group=None)
        self.assertIn("runs no verifier", str(caught.exception))

    def test_an_assignment_mount_over_the_document_refuses(self):
        """Nobody else may decide what the worker proves its roots against."""
        with self.assertRaises(ContractRefusal) as caught:
            self.vector(
                mounts=[{"source": os.path.join(self.home, "inputs", "x"),
                         "target": "/run/baton", "writable": False}],
                layout_delivered=self.delivered())
        self.assertIn("neither this manager nor the engine says which",
                      str(caught.exception))

    def tmpfs(self, argv):
        return [argv[at + 1] for at, one in enumerate(argv)
                if one == "--tmpfs"]

    def test_the_selected_roots_carry_the_identity_and_mode_promised(self):
        """REVIEW [2], DRIVEN. The worker's `_proved_root` refuses a root
        whose mode is not 0700 or whose owner is not the selection's uid AND
        gid. Setting `--user` is not a declaration of filesystem-root
        ownership and the image's root-owned 0755 MOUNTPOINT is not the
        mounted root, so the creation has to ask for those facts."""
        held = self.delivered()
        argv = self.vector(layout_delivered=held)
        composed = {one.split(":", 1)[0]: one.split(":", 1)[1]
                    for one in self.tmpfs(argv)}
        for _name, target, size in source_boundary.VERIFIER_ROOTS:
            with self.subTest(target=target):
                self.assertEqual(
                    composed[target],
                    f"rw,noexec,nosuid,nodev,size={size >> 20}m"
                    f",uid={held.document['uid']},gid={held.document['gid']}"
                    f",mode=0700")

    def test_the_mounted_identity_is_the_one_the_document_names(self):
        """One capability, three places: the document, the `--user` flag and
        every root operand."""
        held = self.delivered()
        argv = self.vector(layout_delivered=held)
        pair = f"{held.document['uid']}:{held.document['gid']}"
        self.assertEqual(argv[argv.index("--user") + 1], pair)
        for one in self.tmpfs(argv):
            if one.startswith(source_boundary.VERIFIER_PARENT):
                self.assertIn(f"uid={held.document['uid']}", one)
                self.assertIn(f"gid={held.document['gid']}", one)

    def test_the_mode_is_the_one_the_worker_proves(self):
        for one in self.tmpfs(self.vector(layout_delivered=self.delivered())):
            if one.startswith(source_boundary.VERIFIER_PARENT):
                self.assertIn(f"mode={source_boundary.VERIFIER_MODE:04o}",
                              one)

    def test_the_unselected_vector_gains_no_root_and_keeps_its_scratch(self):
        """REVIEW [3], DRIVEN: the legacy runtime is argv-identical to before
        this Work, with the original 64 MiB shared scratch and not one
        verifier root."""
        composed = self.tmpfs(self.vector())
        self.assertIn("/tmp:rw,noexec,nosuid,nodev,size=64m", composed)
        for one in composed:
            self.assertFalse(
                one.startswith(source_boundary.VERIFIER_PARENT), one)
            self.assertNotIn("uid=", one)
            self.assertNotIn("mode=", one)

    def test_the_selected_vector_redistributes_rather_than_adding_room(self):
        """The shared scratch gives up exactly what the roots take, so the
        selected total equals the legacy one."""
        legacy = self.tmpfs(self.vector())
        selected = self.tmpfs(self.vector(layout_delivered=self.delivered()))

        def total(composed):
            return sum(int(one.rsplit("size=", 1)[1].split("m")[0])
                       for one in composed)

        self.assertIn("/tmp:rw,noexec,nosuid,nodev,size=32m", selected)
        self.assertEqual(total(legacy), total(selected))
        self.assertEqual(len(selected), len(legacy) + 4)

    def test_a_consent_runtime_composes_no_root_either(self):
        """It refuses the selection, so it cannot acquire the roots by a side
        door -- and the refusal happens before any operand is composed from a
        document, which is why it is reachable with no execution identity."""
        with self.assertRaises(ContractRefusal):
            self.vector(layout_delivered=self.delivered(), posture="consent",
                        workspace_group=None)

    def test_no_delivery_composes_no_mount(self):
        """An explicitly legacy deployment is argv-identical to today."""
        self.assertEqual(self.vector(), self.vector(layout_delivered=None))


class TheAdapterBindsTheSelectionToItsOwnIdentity(unittest.TestCase):
    """THE OWNER COMPOSITION, DRIVEN AT ITS OWNER.

    Review 2026-10-28T03-25-24Z: "Bind selected topology and effective
    UID/GID through the actual owner composition, not self-assertion in an
    arbitrary document." One `OciAdapter` holds ONE resolved identity, owned
    at construction, and that is the only authority in this manager on which
    runtime is being started -- so a selection carrying any other image,
    profile, policy or adapter digest is refused there, before anything runs.

    THE ENGINE IS NEVER CALLED in this class: construction is the boundary
    being tested, and a refusal at construction is one no engine sees.
    """

    def setUp(self):
        self.home = tempfile.mkdtemp(prefix="v12-w325695-bind-")
        self.addCleanup(shutil.rmtree, self.home, True)
        self.identity = minted_identity(self)
        self.storage = os.path.join(self.home, "layout-storage")
        os.makedirs(self.storage, 0o700)
        self.roots = {}
        for name in ("inputs", "workspace"):
            place = os.path.join(self.home, name)
            os.makedirs(place, 0o700)
            self.roots[name] = place

    def delivered(self, **changed):
        return source_boundary.materialize_verifier_layout(
            self.storage, document=composed(self.identity, **changed))

    def adapter(self, **changed):
        held = dict(identity=dict(IDENTITY), assignment_roots=self.roots,
                    posture="execution")
        held.update(changed)
        return oci.OciAdapter("docker", lambda *a, **k: None, **held)

    def test_the_matching_selection_is_held(self):
        held = self.delivered()
        self.assertIs(self.adapter(layout_delivery=held).layout_delivery,
                      held)

    def test_no_selection_is_the_unchanged_default(self):
        """Every existing construction path is byte-for-byte unaffected."""
        self.assertIsNone(self.adapter().layout_delivery)

    def test_a_selection_under_another_resolved_identity_refuses(self):
        """EACH MEMBER, SEPARATELY, so none of the four is merely along for
        the ride. `profile_digest` is the one a three-member document left
        unbound."""
        for name in oci.RESOLVED_IDENTITY:
            with self.subTest(member=name):
                held = self.delivered()
                held.document = dict(held.document,
                                     **{name: "sha256:" + "9" * 64})
                with self.assertRaises(ContractRefusal) as caught:
                    self.adapter(layout_delivery=held)
                said = str(caught.exception)
                self.assertIn(name, said)
                self.assertIn("a runtime this adapter does not start", said)

    def test_a_path_is_not_a_selection(self):
        with self.assertRaises(ContractRefusal) as caught:
            self.adapter(layout_delivery=self.delivered().place)
        self.assertIn("one this manager materialized", str(caught.exception))


class TheFixedTargetIsFIXEDForEveryFamily(unittest.TestCase):
    """CONTAINMENT, AND EXACTLY WHAT KIND OF CLAIM IT IS.

    Only ONE mount family in `run_vector` has a caller-chosen target: the
    assignment `mounts` operand. Every other family -- credentials, launch,
    exchange, logs, scratch, source, integration, context -- lands on a
    constant of its own contract, so none of them can be POINTED at the
    layout document. The reachable collision is the assignment one, and it is
    driven in `TheDocumentIsDeliveredReadOnlyAtItsFixedTarget`.

    What is asserted here is therefore the pair of things that CAN be
    asserted: that no fixed target this manager composes contains the layout
    document, and that the containment lists which carry the launch
    document's target carry this one too. The second is DEFENCE IN DEPTH and
    is labelled as such -- it is not reachable today, and it is in the source
    for the same reason the launch document's identical entries are: a family
    added later with a wider target would otherwise land on the one document
    the verifier's roots are proved against, and the entry that would have
    caught it is the one nobody remembers to add.
    """

    def test_no_other_fixed_target_contains_the_document(self):
        """THE PROPERTY the containment entries protect, over the constants.

        A later edit that moves `LAYOUT_TARGET` under another family's root,
        or widens a family's root over it, fails here rather than at a
        deployment where the worker would prove its roots against whichever
        bind the engine happened to order last.
        """
        from baton_v12.worker_manager import (attempt_logs, credentials,
                                              exchange, launch)
        fixed = [credentials.CREDENTIAL_ROOT, launch.LAUNCH_TARGET,
                 attempt_logs.LOG_TARGET, attempt_logs.LEGACY_LOG_TARGET,
                 oci.SCRATCH_TARGET, source_boundary.SOURCE_TARGET,
                 source_boundary.WORKSPACE_TARGET,
                 exchange.COMMAND_TARGET, exchange.EVENT_TARGET]
        mine = source_boundary.LAYOUT_TARGET
        for one in fixed:
            with self.subTest(target=one):
                self.assertNotEqual(one, mine)
                self.assertFalse(oci._within(mine, one), one)
                self.assertFalse(oci._within(one, mine), one)

    def test_every_launch_containment_list_also_carries_the_layout(self):
        """THE SYMMETRY, STRUCTURALLY. A first cut composed the layout mount
        and added it to nobody's list; the launch document was in all of
        them. This counts the two, so the asymmetry that was there cannot
        come back silently."""
        import inspect
        # FROM THE EXCHANGE FAMILY ONWARD, which is every family composed
        # AFTER the layout selection and therefore every one that has to
        # carry this target in its own list. Before that point the two
        # documents are deliberately not symmetric: the layout block checks
        # itself against the launch document, and the launch block cannot
        # check itself against a selection composed after it.
        text = inspect.getsource(oci.run_vector)
        later = text[text.index("W81857: THE FILE EXCHANGE"):]
        self.assertEqual(later.count("_launch_mount(launch_delivered)"),
                         later.count("_layout_mount(layout_delivered)"))
        self.assertGreaterEqual(
            later.count("_layout_mount(layout_delivered)"), 7)

    def test_the_four_verifier_roots_are_not_a_family_target_either(self):
        """The roots are MOUNTED BY THE IMAGE POSTURE, not by a delivery, so
        nothing a caller delivers may land on one."""
        for _name, target, _size in source_boundary.VERIFIER_ROOTS:
            with self.subTest(target=target):
                self.assertFalse(
                    oci._within(target, source_boundary.LAYOUT_TARGET))
                self.assertFalse(oci._within(target, oci.SCRATCH_TARGET))


class TheSupportedDeploymentSelectsAndDeliversIt(unittest.TestCase):
    """THE INSTALLED CONFIGURATION PATH, through the real deployment entry.

    Review 2026-10-28T17-58-14Z [1] and 18-21-11Z: the topology tests composed
    helpers rather than entering through the supported deployment, so nothing
    ever selected or delivered the document. This drives
    `tools.single_worker.layout_delivery`, which is what both `OciAdapter`
    construction sites now call.
    """

    def setUp(self):
        self.home = tempfile.mkdtemp(prefix="v12-w325695-dep-")
        self.addCleanup(shutil.rmtree, self.home, True)
        self.identity = minted_identity(self)
        self.launch = os.path.join(self.home, "launch")
        os.makedirs(self.launch, 0o700)

    def given(self, **changed):
        held = dict(IDENTITY, launch_home=self.launch,
                    verifier_layout=source_boundary.image_layout_marker())
        held.update(changed)
        return held

    def group(self):
        store = ControlStore.open(
            os.path.join(tempfile.mkdtemp(dir=self.home), "c.sqlite3"),
            incarnation="w325695-dep",
            clock=lambda: "2026-10-28T00:00:00.000Z")
        self.addCleanup(store.close)
        return input_roots.configured_group(store)

    def test_the_three_supported_schemas(self):
        """`/4` and `/5` are untouched and `/6` is the one that selects."""
        self.assertEqual(single_worker.CONFIG_SCHEMA,
                         "baton.v12.single-worker-deployment/4")
        self.assertEqual(single_worker.CONTEXT_CONFIG_SCHEMA,
                         "baton.v12.single-worker-deployment/5")
        self.assertEqual(single_worker.LAYOUT_CONFIG_SCHEMA,
                         "baton.v12.single-worker-deployment/6")

    def test_a_legacy_configuration_delivers_nothing(self):
        """EXPLICITLY LEGACY, and it costs nothing: no document is composed,
        nothing is written and no mount is added."""
        self.assertIsNone(single_worker.layout_delivery(
            self.given(verifier_layout=None), self.group()))
        self.assertEqual(os.listdir(self.launch), [])

    def test_the_configured_pair_delivers_the_document_the_worker_reads(self):
        """THE JOINED PATH: the deployment composes, materializes and delivers,
        and the worker's own reader accepts the bytes that land."""
        delivery = single_worker.layout_delivery(self.given(), self.group())
        agent = AGENT.__new__(AGENT)
        agent._seen = {}
        agent.LAYOUT_DOCUMENT = delivery.place
        agent.LAYOUT_MARKER = os.path.join(self.home, "marker.json")
        with open(agent.LAYOUT_MARKER, "w", encoding="utf-8") as handle:
            json.dump(source_boundary.image_layout_marker(), handle)
        self.assertEqual(agent._selected_layout(), delivery.document)

    def test_the_delivered_identity_is_the_deployments_minted_one(self):
        delivery = single_worker.layout_delivery(self.given(), self.group())
        self.assertEqual(
            (delivery.document["uid"], delivery.document["gid"]),
            (self.identity.uid, self.identity.gid))
        self.assertEqual(delivery.document["image_digest"],
                         IDENTITY["image_digest"])

    def test_a_marker_from_another_topology_refuses_at_the_deployment(self):
        """Before any runtime starts, rather than at a worker mid-run."""
        with self.assertRaises(ContractRefusal) as caught:
            single_worker.layout_delivery(
                self.given(verifier_layout=dict(
                    source_boundary.image_layout_marker(),
                    layout_digest="0" * 64)), self.group())
        self.assertIn("different topologies", str(caught.exception))

    def test_the_delivery_is_what_the_adapter_accepts(self):
        """The adapter binds it to its own resolved identity, so a delivery
        composed under another configuration refuses at construction."""
        delivery = single_worker.layout_delivery(self.given(), self.group())
        roots = {}
        for name in ("inputs", "workspace"):
            place = os.path.join(self.home, name)
            os.makedirs(place, 0o700)
            roots[name] = place
        held = oci.OciAdapter("docker", lambda *a, **k: None,
                              identity=dict(IDENTITY),
                              assignment_roots=roots, posture="execution",
                              layout_delivery=delivery)
        self.assertIs(held.layout_delivery, delivery)


if __name__ == "__main__":
    unittest.main()
