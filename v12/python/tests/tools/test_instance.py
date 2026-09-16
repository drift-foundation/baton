"""Focused checks for the deployed v12 instance selector. W183883.

DETERMINISTIC AND OFFLINE. No bundle is built here and nothing is executed: a
one-folder runtime is stood in for by a directory of files, because what these
prove is the CONTRACT -- what an instance derives, what it binds, and what it
refuses -- rather than PyInstaller, which has its own.

THESE EXIST BECAUSE A LIVE DEMONSTRATION IS NOT A REGRESSION. Reviews
2026-09-16T12-35-10Z [K1-K4] and 2026-09-16T12-43-53Z found five ways a selector
or a runtime could be accepted when it should not be, and each was shown by
running a bundle that was afterwards removed. A refusal nothing holds is a
refusal that can be undone by the next edit without anybody noticing.
"""
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

_DISTRIBUTION = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_DISTRIBUTION))
sys.path.insert(1, str(_DISTRIBUTION / "src"))
from tools import instance, stack_command


class Fixture(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="v12-instance-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def runtime(self, destination, *, files=("baton-v12-stack", "_internal/lib.so")):
        """A stand-in one-folder runtime: a directory of real files."""
        distro = Path(instance.layout(destination)["distro"])
        for name in files:
            place = distro / name
            place.parent.mkdir(parents=True, exist_ok=True)
            place.write_text("bytes of " + name)
        return distro

    def prepared(self, name="a", **members):
        """One destination with a runtime and a published selector."""
        destination = str(self.root / name)
        places = instance.layout(destination)
        self.runtime(destination)
        for key in ("stores", "repository", "logs", "state"):
            Path(places[key]).mkdir(parents=True, exist_ok=True)
        held = instance.manifest(places["distro"])
        document = instance.emit(
            destination, authority_uuid="0" * 31 + "a",
            identity={"frozen": True}, runtime=held, now=1.0)
        document.update(members)
        instance.publish(places["instance"], document)
        return destination, places, document

    def refused(self, place):
        with self.assertRaises(instance.InstanceRefusal) as raised:
            instance.read(place)
        return str(raised.exception)

    def rewrite(self, places, **members):
        document = json.loads(Path(places["instance"]).read_bytes())
        document.update(members)
        instance.publish(places["instance"], document)
        return document


class EveryPathIsDerived(Fixture):
    """K1. A selector does not get to name where this instance's state lives."""

    def test_a_prepared_instance_reads_back(self):
        destination, places, _ = self.prepared()
        held = instance.read(places["instance"])
        self.assertEqual(held["destination"], destination)
        self.assertEqual(held["state"], places["state"])

    def test_a_path_the_destination_does_not_derive_is_refused(self):
        """The original K1: a selector kept at A carrying B's state passed, and
        `stop` went to B's state root."""
        _destination, places, _ = self.prepared()
        other, elsewhere, _ = self.prepared("b")
        for name in ("state", "job_store", "control_store", "deployment",
                     "logs", "repository", "command"):
            self.rewrite(places, **{name: elsewhere[name]})
            said = self.refused(places["instance"])
            self.assertIn(name, said, name)
            self.assertIn("DERIVED from its", said, name)
            self.rewrite(places, **{name: places[name]})

    def test_a_derived_path_that_LINKS_out_of_the_instance_is_refused(self):
        """K1's remainder, and the subtler half: comparing RESOLVED paths made
        `a/state` symlinked to `b/state` compare equal to itself, because both
        sides resolved to b. Equality is not containment."""
        _destination, places, _ = self.prepared()
        _other, elsewhere, _ = self.prepared("b")
        Path(places["state"]).rmdir()
        os.symlink(elsewhere["state"], places["state"])
        said = self.refused(places["instance"])
        self.assertIn("outside this instance", said)
        self.assertIn(elsewhere["state"], said)

    def test_a_path_that_is_not_text_is_refused_rather_than_raising(self):
        """K1's remainder: `isabs` on an integer raised TypeError out of the
        validator whose whole job is to turn a bad document into a refusal."""
        _destination, places, _ = self.prepared()
        for value in (17, None, [], {}):
            self.rewrite(places, state=value)
            said = self.refused(places["instance"])
            self.assertTrue("state" in said, repr(value))
        self.rewrite(places, state=places["state"])

    def test_a_relative_path_is_refused(self):
        _destination, places, _ = self.prepared()
        self.rewrite(places, state="state")
        self.assertIn("relative", self.refused(places["instance"]))

    def test_a_selector_read_from_another_place_is_refused(self):
        destination, places, _ = self.prepared()
        _other, elsewhere, _ = self.prepared("b")
        copied = os.path.join(elsewhere["destination"], "copied.json")
        Path(copied).write_bytes(Path(places["instance"]).read_bytes())
        said = self.refused(copied)
        self.assertIn("was prepared for", said)
        self.assertIn(destination, said)

    def test_an_absent_or_unreadable_selector_is_refused(self):
        self.assertIn("no instance at", self.refused(self.root / "nothing.json"))
        broken = self.root / "broken.json"
        broken.write_text("{ not json")
        self.assertIn("could not be read", self.refused(broken))

    def test_a_selector_of_another_schema_is_refused(self):
        _destination, places, _ = self.prepared()
        self.rewrite(places, schema="baton.v12.stack-instance/99")
        self.assertIn(instance.SCHEMA, self.refused(places["instance"]))

    def test_a_selector_missing_a_member_is_refused(self):
        _destination, places, _ = self.prepared()
        document = json.loads(Path(places["instance"]).read_bytes())
        del document["runtime"]
        Path(places["instance"]).write_text(json.dumps(document))
        self.assertIn("runtime", self.refused(places["instance"]))


class TheRuntimeIsBoundWhole(Fixture):
    """K2. The manifest is what an instance holds the bundle to."""

    def test_every_file_is_digested_and_the_digest_covers_the_listing(self):
        destination, places, _ = self.prepared()
        held = instance.manifest(places["distro"])
        self.assertEqual(held["files"], 2)
        changed = Path(places["distro"]) / "_internal" / "lib.so"
        changed.write_text("different bytes")
        self.assertNotEqual(instance.manifest(places["distro"])["digest"],
                            held["digest"])

    def test_a_changed_runtime_is_refused_by_verify(self):
        _destination, places, document = self.prepared()
        (Path(places["distro"]) / "_internal" / "lib.so").write_text("tampered")
        with self.assertRaises(instance.InstanceRefusal) as raised:
            instance.verify(document)
        self.assertIn("is not the one this instance was prepared with",
                      str(raised.exception))

    def test_an_unchanged_runtime_verifies(self):
        _destination, _places, document = self.prepared()
        self.assertEqual(instance.verify(document)["files"], 2)

    def test_a_link_out_of_the_bundle_is_refused(self):
        """Recording only the LINK TEXT left an external target free to change
        while the manifest stayed identical."""
        destination, places, _ = self.prepared()
        outside = self.root / "outside.so"
        outside.write_text("somebody else's bytes")
        os.symlink(outside, Path(places["distro"]) / "_internal" / "borrowed.so")
        with self.assertRaises(instance.InstanceRefusal) as raised:
            instance.manifest(places["distro"])
        self.assertIn("pointing outside it", str(raised.exception))

    def test_a_broken_link_is_refused(self):
        _destination, places, _ = self.prepared()
        os.symlink(self.root / "never", Path(places["distro"]) / "dangling")
        with self.assertRaises(instance.InstanceRefusal) as raised:
            instance.manifest(places["distro"])
        self.assertIn("broken link", str(raised.exception))

    def test_a_link_INSIDE_the_bundle_is_safe_and_is_recorded(self):
        _destination, places, _ = self.prepared()
        os.symlink(Path(places["distro"]) / "_internal" / "lib.so",
                   Path(places["distro"]) / "alias.so")
        held = instance.manifest(places["distro"])
        self.assertTrue(held["entries"]["alias.so"].startswith("link:"))

    def test_a_distro_that_is_itself_a_link_is_refused(self):
        """K2's remainder: every link INSIDE was bound and the root was not, so
        a `distro` that was a name for another tree digested that tree."""
        destination, places, _ = self.prepared()
        elsewhere = self.root / "another-tree"
        elsewhere.mkdir()
        (elsewhere / "baton-v12-stack").write_text("someone else's build")
        aliased = str(self.root / "aliased")
        os.makedirs(aliased)
        os.symlink(elsewhere, Path(instance.layout(aliased)["distro"]))
        with self.assertRaises(instance.InstanceRefusal) as raised:
            instance.manifest(instance.layout(aliased)["distro"])
        self.assertIn("is itself a link", str(raised.exception))

    def test_an_absent_or_empty_runtime_is_refused(self):
        with self.assertRaises(instance.InstanceRefusal) as raised:
            instance.manifest(self.root / "nothing")
        self.assertIn("no bundled runtime", str(raised.exception))
        empty = self.root / "empty"
        empty.mkdir()
        with self.assertRaises(instance.InstanceRefusal) as raised:
            instance.manifest(empty)
        self.assertIn("is empty", str(raised.exception))


class TheRunningCommandIsBoundToo(Fixture):
    """K2's other half: verifying a folder said nothing about which command was
    executing, so one build dispatched children on behalf of another."""

    def test_frozen_a_foreign_command_is_refused(self):
        _destination, _places, document = self.prepared()
        _other, elsewhere, _ = self.prepared("b")
        with mock.patch.object(stack_command, "frozen", lambda: True), \
                mock.patch.object(stack_command, "executable",
                                  lambda: elsewhere["command"]):
            with self.assertRaises(instance.InstanceRefusal) as raised:
                instance.verify(document)
        said = str(raised.exception)
        self.assertIn(elsewhere["command"], said)
        self.assertIn("drives its OWN instance", said)

    def test_frozen_its_own_command_is_accepted(self):
        _destination, places, document = self.prepared()
        with mock.patch.object(stack_command, "frozen", lambda: True), \
                mock.patch.object(stack_command, "executable",
                                  lambda: places["command"]):
            self.assertEqual(instance.verify(document)["files"], 2)

    def test_from_source_the_running_command_is_not_compared(self):
        """Running from the checkout, `sys.executable` is an interpreter and
        comparing it to a bundled path would refuse every development run."""
        _destination, _places, document = self.prepared()
        self.assertFalse(stack_command.frozen())
        self.assertEqual(instance.verify(document)["files"], 2)


class WhatAnInstanceDerives(Fixture):
    def test_the_layout_is_all_under_one_destination(self):
        places = instance.layout("/srv/deployment")
        for name, place in places.items():
            self.assertTrue(place.startswith("/srv/deployment"), name)
        self.assertEqual(places["job_store"], "/srv/deployment/db/jobs.sqlite3")
        self.assertEqual(places["state"], "/srv/deployment/state")
        # NOT the same path as the stack's own process records.
        self.assertNotEqual(places["deployment_state"], places["state"])

    def test_bootstrap_derives_the_same_places(self):
        """Two layouts that disagreed about where a Job store is would be two
        deployments sharing a name."""
        from tools import bootstrap

        mine = instance.layout("/srv/deployment")
        theirs = bootstrap.layout("/srv/deployment")
        for name in ("authority_store", "job_store", "control_store",
                     "integration_store", "deployment_state"):
            self.assertEqual(mine[name], theirs[name], name)
        self.assertEqual(mine["deployment"], theirs["configuration"])
        self.assertEqual(mine["record"], theirs["record"])

    def test_the_settings_are_the_vocabulary_the_lifecycle_already_reads(self):
        _destination, places, document = self.prepared()
        settings = instance.settings(document)
        self.assertEqual(settings["BATON_V12_JOB_STORE"], places["job_store"])
        self.assertEqual(settings["BATON_V12_STAGE_EXECUTION_CONFIG"],
                         places["deployment"])

    def test_publication_is_atomic(self):
        """The selector arrives by a rename from a temporary beside it, never
        by writing the final name in place where a reader could catch it half
        written. The temporary's NAME is deliberately not fixed: review
        2026-09-16T13-20-49Z showed a fixed one is a name somebody else can
        already hold.
        """
        seen = []
        real = os.replace

        def watched(source, target):
            seen.append((Path(source), Path(target)))
            return real(source, target)

        with mock.patch.object(os, "replace", watched):
            _destination, places, _ = self.prepared()
        self.assertEqual(len(seen), 1)
        source, target = seen[0]
        self.assertEqual(str(target), places["instance"])
        self.assertEqual(source.parent, target.parent)
        self.assertTrue(source.name.startswith(".instance-"), source.name)


class BootstrapFixture(Fixture):
    """A stand-in built runtime and the two ways to answer for its identity.

    Nothing is built or executed here either. `admit` asks the BUILT COMMAND
    what it is by running it; these substitute that one answer -- never the
    rules applied to it -- because what is under test is the admission.
    `tests/tools/test_packaging` owns the real bundle.
    """

    SOURCE = object()   # so `distro=""` is a case rather than a default

    def setUp(self):
        super().setUp()
        from tools import bootstrap

        self.bootstrap = bootstrap
        self.source = self.root / "built"
        (self.source / "_internal" / "rpds").mkdir(parents=True)
        (self.source / "baton-v12-stack").write_text("the launcher")
        (self.source / "_internal" / "rpds" / "rpds.so").write_text("native")
        self.destination = str(self.root / "dest")

    def identity(self, **members):
        """What a good build answers, and the hook to make it a bad one."""
        said = {"command": "baton-v12-stack", "frozen": True,
                "python": "3.13.7", "platform": "Linux", "machine": "x86_64",
                "schema_assets": {"agent-session-1.0": 10,
                                  "worker-control-1.0": 20},
                "native_rpds": str(self.source / "_internal" / "rpds" / "rpds.so"),
                "resources": str(self.source / "_internal")}
        said.update(members)
        return said

    def answering(self, said):
        """The real `_identity_of`, over a substituted subprocess."""
        import subprocess

        done = subprocess.CompletedProcess([], 0, stdout=json.dumps(said),
                                           stderr="")
        return mock.patch.object(subprocess, "run", lambda *a, **k: done)

    def admitting(self, destination=None, distro=SOURCE, **identity):
        said = self.identity(**identity)
        with self.answering(said):
            return self.bootstrap.admit(
                self.destination if destination is None else destination,
                str(self.source) if distro is self.SOURCE else distro)

    def refusing(self, **named):
        with self.assertRaises(self.bootstrap.BootstrapRefusal) as raised:
            self.admitting(**named)
        return str(raised.exception)


class TheAdmissionDecidesBeforeAnythingHappens(BootstrapFixture):
    """K1/K3's remainder. Every refusal here was demonstrated by running a
    bootstrap that was afterwards removed; a refusal nothing holds is one the
    next edit can undo without anybody noticing."""

    def test_a_good_source_is_admitted(self):
        places, runtime, identity = self.admitting()
        self.assertEqual(places["destination"], self.destination)
        self.assertEqual(runtime["files"], 2)
        self.assertIs(identity["frozen"], True)

    def test_a_relative_or_inside_the_checkout_destination_is_refused(self):
        self.assertIn("absolute", self.refusing(destination="dest"))
        inside = os.path.join(str(_DISTRIBUTION), "would-be-instance")
        self.assertIn("inside the checkout", self.refusing(destination=inside))
        self.assertFalse(os.path.exists(inside))

    def test_an_owned_path_that_LINKS_out_of_the_destination_is_refused(self):
        """Install SUCCEEDED with `state` linked outside and published a
        selector the very next read rejected -- a deployment that could never
        be started, left behind."""
        places = instance.layout(self.destination)
        os.makedirs(self.destination)
        elsewhere = self.root / "elsewhere"
        elsewhere.mkdir()
        os.symlink(elsewhere, places["state"])
        said = self.refusing()
        self.assertIn("carries a link at", said)
        self.assertIn(places["state"], said)
        self.assertFalse(os.path.exists(places["instance"]))
        self.assertEqual(list(elsewhere.iterdir()), [])

    def test_a_DANGLING_selector_link_is_refused_rather_than_written_through(self):
        """`exists` follows the final link, so a dangling `instance.json` link
        read as ABSENT and was then overwritten -- through the link, into
        wherever it pointed."""
        places = instance.layout(self.destination)
        os.makedirs(self.destination)
        target = self.root / "never-existed"
        os.symlink(target, places["instance"])
        said = self.refusing()
        self.assertIn("carries a link at", said)
        self.assertIn(places["instance"], said)
        self.assertFalse(target.exists())

    def test_an_existing_runtime_or_selector_is_never_replaced(self):
        places = instance.layout(self.destination)
        os.makedirs(places["distro"])
        self.assertIn("already a runtime", self.refusing())
        os.rmdir(places["distro"])
        Path(places["instance"]).write_text("{}")
        self.assertIn("already an instance selector", self.refusing())
        self.assertEqual(Path(places["instance"]).read_text(), "{}")

    def test_FROZEN_the_checkout_is_the_bundle_and_not_the_destination(self):
        """The first real installed run found this. Frozen, walking three
        parents up from `__file__` answered the INSTANCE DESTINATION, so a
        repeated bootstrap into a prepared destination was refused for being
        "inside the checkout at <that same destination>" -- instead of the
        honest "there is already a runtime here". The rule has one owner,
        `stage_execution._checkout`, which answers the BUNDLE when frozen."""
        places = instance.layout(self.destination)
        bundle = Path(places["distro"])
        (bundle / "_internal").mkdir(parents=True)
        with mock.patch.object(sys, "frozen", True, create=True), \
                mock.patch.object(sys, "_MEIPASS", str(bundle / "_internal"),
                                  create=True):
            # The destination is the bundle's PARENT, which is exactly where an
            # installed instance keeps its own mutable state.
            self.assertIn("already a runtime", self.refusing())
            # And a path INSIDE the bundle is still refused for what it is.
            inside = str(bundle / "would-be-instance")
            self.assertIn("inside the checkout", self.refusing(destination=inside))

    def test_an_unnamed_or_absent_runtime_is_refused_before_anything(self):
        self.assertIn("needs a built runtime", self.refusing(distro=""))
        self.assertIn("no built runtime at",
                      self.refusing(distro=str(self.root / "nothing")))
        self.assertFalse(os.path.exists(self.destination))


class TheIdentityHasToMeanSomething(BootstrapFixture):
    """K3's remainder: what a build SAYS about itself may not widen what counts
    as proof of what it carries."""

    def test_a_build_that_is_not_frozen_is_refused(self):
        self.assertIn("not a frozen build", self.refusing(frozen=False))

    def test_assets_must_be_exactly_the_ones_this_distribution_ships(self):
        for bad in ({}, {"agent-session-1.0": 10},
                    {"agent-session-1.0": 10, "worker-control-1.0": 0},
                    {"something-else": 10, "worker-control-1.0": 20},
                    {"agent-session-1.0": 10, "worker-control-1.0": 20,
                     "extra": 5}):
            self.assertIn("frozen schema assets",
                          self.refusing(schema_assets=bad), repr(bad))

    def test_a_native_validator_from_the_HOST_is_refused(self):
        said = self.refusing(native_rpds="/usr/lib/python3/rpds.so")
        self.assertIn("not one of the", said)
        self.assertIn("files this bundle binds", said)

    def test_a_permissive_resources_claim_cannot_widen_what_counts(self):
        """`resources: "/"` made every path on the host qualify under the
        anchoring this replaced."""
        self.assertIn("not one of the",
                      self.refusing(native_rpds="/usr/lib/rpds.so",
                                    resources="/"))

    def test_a_path_under_the_reported_resources_that_is_not_in_the_manifest(self):
        self.assertIn("not one of the",
                      self.refusing(native_rpds=str(self.source / "_internal"
                                                    / "never-built.so")))

    def test_a_missing_native_report_is_refused(self):
        for bad in ("", None, 17, ["a"]):
            self.assertIn("native validator", self.refusing(native_rpds=bad),
                          repr(bad))

    def test_the_bundled_one_IS_admitted(self):
        """The counterpart, so the refusals above are not passing by accident."""
        _places, _runtime, identity = self.admitting()
        self.assertEqual(identity["native_rpds"],
                         str(self.source / "_internal" / "rpds" / "rpds.so"))


class TheAdmissionIsCarriedNotRepeated(BootstrapFixture):
    """K3's last remainder: `main` admitted, discarded the answer, and
    `install` admitted again -- so a source changed while `prepare` was
    composing was re-admitted and installed, exit 0, with a digest nobody had
    agreed to."""

    def installing(self, admitted, destination=None):
        with self.assertRaises(self.bootstrap.BootstrapRefusal) as raised:
            with open(os.devnull, "w") as quiet:
                self.bootstrap.install(
                    self.destination if destination is None else destination,
                    str(self.source), {"authority_uuid": "0" * 31 + "a"},
                    stream=quiet, admitted=admitted)
        return str(raised.exception)

    def test_a_source_changed_after_admission_is_refused(self):
        admitted = self.admitting()
        (self.source / "baton-v12-stack").write_text("a different build")
        said = self.installing(admitted)
        self.assertIn("changed after it was admitted", said)
        self.assertFalse(
            os.path.exists(instance.layout(self.destination)["distro"]))

    def test_an_admission_for_another_destination_is_refused(self):
        admitted = self.admitting()
        other = str(self.root / "somewhere-else")
        self.assertIn("is being used to install into",
                      self.installing(admitted, destination=other))
        self.assertFalse(os.path.exists(other))

    def test_the_admission_it_was_given_is_installed(self):
        """The counterpart: an unchanged source installs, and the selector the
        install publishes is one `instance.read` accepts."""
        admitted = self.admitting()
        with open(os.devnull, "w") as quiet:
            self.bootstrap.install(self.destination, str(self.source),
                                   {"authority_uuid": "0" * 31 + "a"},
                                   stream=quiet, admitted=admitted,
                                   now=1.0)
        places = instance.layout(self.destination)
        held = instance.read(places["instance"])
        self.assertEqual(held["runtime"]["digest"], admitted[1]["digest"])


class TheDestinationIsAskedAboutAgain(BootstrapFixture):
    """Review 2026-09-16T13-09-22Z: carrying the admission fixed one half and
    opened the other. An admission decides about a RUNTIME; it cannot promise
    the destination still looks the way it did while `prepare` was composing an
    Authority into it, and `install` was believing it did.

    These are deterministic INTERLEAVINGS -- the destination is changed between
    the two calls -- not a claim to withstand arbitrary hostile mutation.
    """

    def installing(self, admitted, destination=None, **named):
        with open(os.devnull, "w") as quiet:
            return self.bootstrap.install(
                self.destination if destination is None else destination,
                str(self.source), {"authority_uuid": "0" * 31 + "a"},
                stream=quiet, admitted=admitted, now=1.0, **named)

    def refused(self, admitted, **named):
        with self.assertRaises(self.bootstrap.BootstrapRefusal) as raised:
            self.installing(admitted, **named)
        return str(raised.exception)

    def test_a_selector_that_APPEARS_after_admission_is_not_overwritten(self):
        """install returned success and overwrote another writer's selector."""
        admitted = self.admitting()
        places = instance.layout(self.destination)
        os.makedirs(self.destination)
        theirs = "another writer owns this selector"
        Path(places["instance"]).write_text(theirs)
        said = self.refused(admitted)
        self.assertIn("already an instance selector", said)
        self.assertEqual(Path(places["instance"]).read_text(), theirs)
        self.assertFalse(os.path.exists(places["distro"]))

    def test_a_STATE_LINK_that_appears_after_admission_is_refused(self):
        """install succeeded and published a selector `instance.read` rejects
        on the very next read."""
        admitted = self.admitting()
        places = instance.layout(self.destination)
        os.makedirs(self.destination)
        elsewhere = self.root / "foreign-state"
        elsewhere.mkdir()
        os.symlink(elsewhere, places["state"])
        said = self.refused(admitted)
        self.assertIn("carries a link at", said)
        self.assertFalse(os.path.lexists(places["instance"]))
        self.assertEqual(list(elsewhere.iterdir()), [])

    def test_a_RUNTIME_that_appears_after_admission_is_not_replaced(self):
        admitted = self.admitting()
        places = instance.layout(self.destination)
        os.makedirs(places["distro"])
        theirs = Path(places["distro"]) / "somebody-elses-build"
        theirs.write_text("not ours")
        self.assertIn("already a runtime", self.refused(admitted))
        self.assertEqual(theirs.read_text(), "not ours")
        self.assertFalse(os.path.lexists(places["instance"]))

    def test_what_this_attempt_s_own_prepare_made_is_NOT_in_the_way(self):
        """`prepare` composes the Authority INTO the destination before
        `install` runs, so the stores, logs, state root, configuration and
        record are legitimately there. A custody check that refused those would
        refuse every real bootstrap."""
        admitted = self.admitting()
        places = instance.layout(self.destination)
        for name in ("stores", "repository", "logs", "state",
                     "deployment_state"):
            os.makedirs(places[name], exist_ok=True)
        for name in ("deployment", "record"):
            Path(places[name]).write_text("{}")
        self.installing(admitted)
        self.assertEqual(instance.read(places["instance"])["runtime"]["digest"],
                         admitted[1]["digest"])

    def test_an_unchanged_preparation_installs_and_reads_back(self):
        """The control. Every refusal above is worth nothing if the ordinary
        path stopped working."""
        admitted = self.admitting()
        selector = self.installing(admitted)
        places = instance.layout(self.destination)
        held = instance.read(places["instance"])
        self.assertEqual(held, selector)
        self.assertEqual(held["identity"], admitted[2])
        self.assertEqual(instance.manifest(places["distro"])["digest"],
                         admitted[1]["digest"])
        for name in ("stores", "repository", "logs", "state"):
            self.assertTrue(os.path.isdir(places[name]), name)

    def test_a_selector_appearing_BETWEEN_custody_and_publication_is_refused(self):
        """The interval no check can cover, and the reason publication itself
        has to refuse: `custody` looked, and then the copy took however long a
        copy takes. The appearance is INJECTED at the step immediately before
        publication, deterministically -- this is not a concurrency test and
        does not claim protection from arbitrary mutation.
        """
        admitted = self.admitting()
        places = instance.layout(self.destination)
        theirs = "another writer got there first"
        real = instance.emit

        def emitting(*operands, **named):
            Path(places["instance"]).write_text(theirs)
            return real(*operands, **named)

        with mock.patch.object(instance, "emit", emitting):
            said = self.refused(admitted)
        self.assertIn("already an instance selector", said)
        self.assertEqual(Path(places["instance"]).read_text(), theirs)
        # AND THIS ATTEMPT'S OWN COPY IS UNWOUND -- only ours, so nothing
        # foreign is touched and a retry is not blocked by our leftovers.
        self.assertFalse(os.path.exists(places["distro"]))

    def test_a_cooperating_bootstrap_holding_the_destination_is_waited_for(self):
        """Two attempts preparing one destination would interleave a copy and a
        publication. This coordinates attempts that both take the lock; it is
        not a defence against arbitrary mutation, which is why the publication
        refuses exclusively as well."""
        import fcntl

        admitted = self.admitting()
        places = instance.layout(self.destination)
        os.makedirs(self.destination)
        other = os.open(places["lock"], os.O_RDWR | os.O_CREAT, 0o600)
        self.addCleanup(os.close, other)
        fcntl.flock(other, fcntl.LOCK_EX)
        said = self.refused(admitted, wait=0.05)
        self.assertIn("another bootstrap is holding", said)
        self.assertFalse(os.path.exists(places["distro"]))
        self.assertFalse(os.path.lexists(places["instance"]))
        # AND IT PROCEEDS ONCE THE OTHER ONE IS DONE.
        fcntl.flock(other, fcntl.LOCK_UN)
        self.installing(admitted)
        self.assertEqual(instance.read(places["instance"])["runtime"]["digest"],
                         admitted[1]["digest"])


class PublicationRefusesToReplace(Fixture):
    """`os.replace` is atomic for a REPLACEMENT -- which is exactly what must
    not happen to a selector that appeared while this one was being prepared."""

    def test_a_first_publication_creates_the_selector(self):
        place = self.root / "instance.json"
        instance.create(place, {"schema": instance.SCHEMA})
        self.assertEqual(json.loads(place.read_bytes())["schema"],
                         instance.SCHEMA)
        self.assertFalse((self.root / "instance.json.new").exists())

    def test_an_existing_selector_is_left_exactly_as_it_was(self):
        place = self.root / "instance.json"
        place.write_text("somebody else got here first")
        with self.assertRaises(instance.InstanceRefusal) as raised:
            instance.create(place, {"schema": instance.SCHEMA})
        self.assertIn("already an instance selector", str(raised.exception))
        self.assertEqual(place.read_text(), "somebody else got here first")
        self.assertFalse((self.root / "instance.json.new").exists())

    def test_a_DANGLING_link_is_not_written_through_either(self):
        place = self.root / "instance.json"
        target = self.root / "never-existed"
        os.symlink(target, place)
        with self.assertRaises(instance.InstanceRefusal):
            instance.create(place, {"schema": instance.SCHEMA})
        self.assertFalse(target.exists())

    # -- the temporary is OWNED before it is written ------------------------
    # Review 2026-09-16T13-20-49Z: a FIXED `instance.json.new` was written
    # through whatever was already at it, so publication damaged foreign data
    # BEFORE the final name was ever considered.

    def foreign(self, name, bytes_):
        place = self.root / name
        place.write_text(bytes_)
        return place

    def leftovers(self):
        """Anything this attempt made and did not clean up."""
        return sorted(one.name for one in self.root.iterdir()
                      if one.name.startswith(".instance-"))

    def test_a_SYMLINK_at_the_old_temporary_name_cannot_redirect_the_write(self):
        """It redirected the write into a foreign document and then published a
        SYMLINK as the selector."""
        theirs = self.foreign("their-document.json", "somebody else's bytes")
        pointer = self.root / "instance.json.new"
        os.symlink(theirs, pointer)
        place = self.root / "instance.json"
        instance.create(place, {"schema": instance.SCHEMA})
        self.assertEqual(theirs.read_text(), "somebody else's bytes")
        self.assertFalse(place.is_symlink())
        self.assertEqual(json.loads(place.read_bytes())["schema"],
                         instance.SCHEMA)
        # AND THE UNKNOWN ENTRY IS LEFT ALONE: it is not this attempt's to
        # truncate, reuse or remove.
        self.assertTrue(pointer.is_symlink())
        self.assertEqual(self.leftovers(), [])

    def test_a_HARDLINK_at_the_old_temporary_name_cannot_damage_the_selector(self):
        """Publication refused and said the selector was left exactly as it
        was -- after its bytes had already been overwritten."""
        place = self.root / "instance.json"
        place.write_text("somebody else got here first")
        os.link(place, self.root / "instance.json.new")
        with self.assertRaises(instance.InstanceRefusal):
            instance.create(place, {"schema": instance.SCHEMA})
        self.assertEqual(place.read_text(), "somebody else got here first")
        self.assertEqual((self.root / "instance.json.new").read_text(),
                         "somebody else got here first")
        self.assertEqual(self.leftovers(), [])

    def test_a_REGULAR_file_at_the_old_temporary_name_is_left_alone(self):
        theirs = self.foreign("instance.json.new", "not this attempt's file")
        instance.create(self.root / "instance.json", {"schema": instance.SCHEMA})
        self.assertEqual(theirs.read_text(), "not this attempt's file")
        self.assertEqual(self.leftovers(), [])

    def test_rewriting_an_OWN_selector_cannot_write_through_a_link_either(self):
        """`publish` replaces on purpose, and had the same fixed-name defect."""
        theirs = self.foreign("their-document.json", "somebody else's bytes")
        os.symlink(theirs, self.root / "instance.json.tmp")
        place = self.root / "instance.json"
        place.write_text("the instance's own older selector")
        instance.publish(place, {"schema": instance.SCHEMA})
        self.assertEqual(theirs.read_text(), "somebody else's bytes")
        self.assertFalse(place.is_symlink())
        self.assertEqual(json.loads(place.read_bytes())["schema"],
                         instance.SCHEMA)
        self.assertEqual(self.leftovers(), [])


class TheDestinationOwnsItsWorkspace(Fixture):
    """W183883 review 2026-09-16T14-06-35Z: `repo/` was created and bound to
    nothing, so an installed deployment had a working area its configuration
    never mentioned."""

    def setUp(self):
        super().setUp()
        from tools import bootstrap

        self.bootstrap = bootstrap
        self.destination = str(self.root / "deployment")
        self.places = instance.layout(self.destination)

    def bound(self, **members):
        return self.bootstrap.workspace_bound(
            dict({"schema": "baton.v12.stack-bootstrap/1"}, **members),
            self.places)

    def refused(self, **members):
        with self.assertRaises(self.bootstrap.BootstrapRefusal) as raised:
            self.bound(**members)
        return str(raised.exception)

    def test_an_absent_workspace_is_DERIVED_from_the_destination(self):
        held = self.bound()
        # ASKED BEFORE IT IS READ: indexing a document that does not carry the
        # member raises KeyError out of the check, which is an error rather
        # than the answer this is about.
        self.assertIn("integration_workspace", held)
        self.assertEqual(held["integration_workspace"], self.places["repository"])

    def test_the_input_document_is_not_mutated(self):
        """A helper that edited its operand would have two callers disagreeing
        about what was configured."""
        given = {"schema": "baton.v12.stack-bootstrap/1"}
        self.bootstrap.workspace_bound(given, self.places)
        self.assertNotIn("integration_workspace", given)

    def test_a_workspace_inside_the_destination_travels_verbatim(self):
        mine = os.path.join(self.places["repository"], "somewhere")
        self.assertEqual(self.bound(integration_workspace=mine)
                         ["integration_workspace"], mine)

    def test_a_workspace_OUTSIDE_the_destination_is_refused(self):
        elsewhere = str(self.root / "somebody-elses")
        said = self.refused(integration_workspace=elsewhere)
        self.assertIn("outside the destination", said)
        self.assertIn(elsewhere, said)

    def test_a_LINK_out_of_the_destination_is_refused_too(self):
        elsewhere = self.root / "somebody-elses"
        elsewhere.mkdir()
        os.makedirs(self.destination)
        linked = os.path.join(self.destination, "repo")
        os.symlink(elsewhere, linked)
        self.assertIn("outside the destination",
                      self.refused(integration_workspace=linked))

    def test_an_explicit_null_still_travels_to_be_refused_by_its_consumer(self):
        """[G2]: an explicit null is refused in the consumer's own words rather
        than quietly replaced, which would turn an invalid request into a
        different valid one."""
        self.assertIsNone(self.bound(integration_workspace=None)
                          ["integration_workspace"])

    def test_the_TARGET_is_never_derived(self):
        """The repository this deployment integrates INTO is not deployment
        state, outlives any instance, and is the owner's selection."""
        self.assertNotIn("integration_target", self.bound())


class TheDeploymentCarriesItsOwnJustfile(Fixture):
    """OWNER-STANDALONE-INTERFACE-20260916.md: "once deployed, we shouldn't
    have to require more than the destination for stop/start/status", and
    "just should have justfile in the destination"."""

    def setUp(self):
        super().setUp()
        from tools import bootstrap

        self.bootstrap = bootstrap
        self.destination = str(self.root / "deployment")
        self.places = instance.layout(self.destination)
        self.text = bootstrap.deployed_justfile(self.places)

    def test_it_is_an_owned_path_under_the_destination(self):
        self.assertEqual(self.places["justfile"],
                         os.path.join(self.destination, "justfile"))

    def test_every_lifecycle_verb_is_there_and_takes_no_operand(self):
        for verb in ("start", "stop", "status", "repository", "identity"):
            self.assertIn("\n" + verb + ":\n", self.text, verb)
        self.assertIn('monitor INTERVAL="5":', self.text)

    def test_every_path_is_resolved_from_the_justfile_s_OWN_directory(self):
        """`just --justfile <destination>/justfile status` has to mean the
        same deployment as `cd <destination> && just status`, and it only does
        if nothing is resolved from the caller's working directory."""
        self.assertIn("HERE := justfile_directory()", self.text)
        self.assertIn('COMMAND := HERE / "distro" / "baton-v12-stack"', self.text)
        self.assertIn('INSTANCE := HERE / "instance.json"', self.text)
        for line in self.text.splitlines():
            if line.startswith("\t"):
                self.assertIn("{{COMMAND}}", line, line)
                self.assertNotIn("$PWD", line, line)

    def test_the_instance_selector_is_still_what_selects(self):
        """The public interface got simpler; the identity beneath it did not
        change. Every recipe still passes --instance, so the command still
        verifies the runtime and still refuses another instance's selector."""
        for line in self.text.splitlines():
            if line.startswith("\t") and "identity" not in line:
                self.assertIn('--instance "{{INSTANCE}}"', line, line)

    def test_it_is_not_a_login_shell(self):
        """The first live run printed a profile permission error before every
        recipe: a deployed command must not depend on whoever's profile happens
        to be readable where it runs."""
        self.assertIn('set shell := ["bash", "-euo", "pipefail", "-c"]',
                      self.text)
        self.assertNotIn('"-lc"', self.text)

    def test_it_does_not_need_the_checkout_or_its_environment(self):
        for banned in ("PYTHONPATH", "tools.instance", "tools.environment",
                       "tools.stack", "python3", "venv", "BATON_V12_"):
            self.assertNotIn(banned, self.text, banned)

    def test_installing_writes_it(self):
        admitted = None
        source = self.root / "built"
        (source / "_internal" / "rpds").mkdir(parents=True)
        (source / "baton-v12-stack").write_text("the launcher")
        (source / "_internal" / "rpds" / "rpds.so").write_text("native")
        said = {"command": "baton-v12-stack", "frozen": True,
                "python": "3.13.7", "platform": "Linux", "machine": "x86_64",
                "schema_assets": {"agent-session-1.0": 10,
                                  "worker-control-1.0": 20},
                "native_rpds": str(source / "_internal" / "rpds" / "rpds.so")}
        with mock.patch.object(self.bootstrap, "_identity_of",
                               lambda command, runtime=None, distro=None: said):
            admitted = self.bootstrap.admit(self.destination, str(source))
            with open(os.devnull, "w") as quiet:
                self.bootstrap.install(self.destination, str(source),
                                       {"authority_uuid": "0" * 31 + "a"},
                                       stream=quiet, admitted=admitted, now=1.0)
        self.assertEqual(Path(self.places["justfile"]).read_text(), self.text)

    def test_existing_material_at_that_name_is_refused(self):
        """[R3]: custody refused only a LINK there, so a regular justfile
        somebody else had put in the destination was overwritten and the
        selector published over it."""
        os.makedirs(self.destination)
        theirs = "# somebody else's justfile\n"
        Path(self.places["justfile"]).write_text(theirs)
        with self.assertRaises(self.bootstrap.BootstrapRefusal) as raised:
            self.bootstrap.custody(self.places, self.destination)
        self.assertIn("already a justfile at", str(raised.exception))
        self.assertEqual(Path(self.places["justfile"]).read_text(), theirs)

    def test_and_it_is_created_EXCLUSIVELY_when_install_writes_it(self):
        """Custody looks; the exclusive create is what closes the interval
        between looking and writing."""
        source = self.root / "built"
        (source / "_internal" / "rpds").mkdir(parents=True)
        (source / "baton-v12-stack").write_text("the launcher")
        (source / "_internal" / "rpds" / "rpds.so").write_text("native")
        said = {"command": "baton-v12-stack", "frozen": True,
                "python": "3.13.7", "platform": "Linux", "machine": "x86_64",
                "schema_assets": {"agent-session-1.0": 10,
                                  "worker-control-1.0": 20},
                "native_rpds": str(source / "_internal" / "rpds" / "rpds.so")}
        theirs = "# it appeared after custody looked\n"
        with mock.patch.object(self.bootstrap, "_identity_of",
                               lambda command, runtime=None, distro=None: said):
            admitted = self.bootstrap.admit(self.destination, str(source))
            os.makedirs(self.destination, exist_ok=True)
            Path(self.places["justfile"]).write_text(theirs)
            with self.assertRaises(self.bootstrap.BootstrapRefusal) as raised:
                with open(os.devnull, "w") as quiet:
                    self.bootstrap.install(
                        self.destination, str(source),
                        {"authority_uuid": "0" * 31 + "a"}, stream=quiet,
                        admitted=admitted, now=1.0)
        self.assertIn("already a justfile at", str(raised.exception))
        self.assertEqual(Path(self.places["justfile"]).read_text(), theirs)
        self.assertFalse(os.path.lexists(self.places["instance"]))

    def installing(self, **named):
        source = self.root / "built"
        if not source.exists():
            (source / "_internal" / "rpds").mkdir(parents=True)
            (source / "baton-v12-stack").write_text("the launcher")
            (source / "_internal" / "rpds" / "rpds.so").write_text("native")
        said = {"command": "baton-v12-stack", "frozen": True,
                "python": "3.13.7", "platform": "Linux", "machine": "x86_64",
                "schema_assets": {"agent-session-1.0": 10,
                                  "worker-control-1.0": 20},
                "native_rpds": str(source / "_internal" / "rpds" / "rpds.so")}
        with mock.patch.object(self.bootstrap, "_identity_of",
                               lambda command, runtime=None, distro=None: said):
            admitted = self.bootstrap.admit(self.destination, str(source))
            with open(os.devnull, "w") as quiet:
                return self.bootstrap.install(
                    self.destination, str(source),
                    {"authority_uuid": "0" * 31 + "a"},
                    stream=named.pop("stream", quiet), admitted=admitted,
                    now=1.0, **named)

    def test_a_FAILED_publication_unwinds_what_this_attempt_made(self):
        """[R3 remainder]: a transient publication failure left this attempt's
        OWN justfile behind, removed the runtime, published no selector -- and
        the retry then refused for that leftover, which this attempt had
        created. Both are ours, both go."""
        import io

        out = io.StringIO()
        with mock.patch.object(instance, "create",
                               side_effect=OSError("the disk went away")):
            with self.assertRaises(OSError):
                self.installing(stream=out)
        self.assertFalse(os.path.exists(self.places["distro"]))
        self.assertFalse(os.path.lexists(self.places["justfile"]))
        self.assertFalse(os.path.lexists(self.places["instance"]))
        self.assertIn("unwound", out.getvalue())

    def test_and_the_retry_then_SUCCEEDS(self):
        """Which is the point: an attempt that cleans up after itself leaves a
        destination another attempt can use."""
        with mock.patch.object(instance, "create",
                               side_effect=OSError("the disk went away")):
            with self.assertRaises(OSError):
                self.installing()
        selector = self.installing()
        self.assertEqual(instance.read(self.places["instance"]), selector)
        self.assertTrue(os.path.isfile(self.places["justfile"]))

    def test_a_PARTIAL_write_is_still_this_attempt_s_to_unwind(self):
        """[R3 remainder]: ownership was a flag set AFTER the write finished,
        so a write that failed part-way left bytes nobody would remove -- and
        the retry was then blocked by this attempt's own leftover."""
        import io

        real = self.bootstrap.deployed_justfile

        def partial(places):
            # What a short write leaves: the file exists, with some of it.
            Path(places["justfile"]).write_text("# half of it")
            raise OSError("the disk filled up")

        out = io.StringIO()
        with mock.patch.object(self.bootstrap, "deployed_justfile", partial):
            with self.assertRaises(OSError):
                self.installing(stream=out)
        self.assertFalse(os.path.lexists(self.places["justfile"]),
                         "the partial justfile was left behind")
        self.assertFalse(os.path.exists(self.places["distro"]))
        self.assertIn("unwound", out.getvalue())
        # AND THE RETRY WORKS, which is the point of unwinding at all.
        selector = self.installing()
        self.assertEqual(instance.read(self.places["instance"]), selector)

    def test_a_justfile_REPLACED_after_this_attempt_made_it_is_left(self):
        """The other half: cleanup deleted the foreign REPLACEMENT and then
        said nothing else had been touched. A path is not an identity."""
        import io

        theirs = "# somebody replaced it between create and publication\n"

        def replacing(place, document):
            os.unlink(self.places["justfile"])
            Path(self.places["justfile"]).write_text(theirs)
            raise OSError("and then the publication failed")

        out = io.StringIO()
        with mock.patch.object(instance, "create", replacing):
            with self.assertRaises(OSError):
                self.installing(stream=out)
        self.assertTrue(os.path.lexists(self.places["justfile"]),
                        "the replacement was removed by this attempt")
        self.assertEqual(Path(self.places["justfile"]).read_text(), theirs)
        self.assertIn("no longer the justfile this attempt made",
                      out.getvalue())
        # AND THE RUNTIME, which IS still ours, is unwound.
        self.assertFalse(os.path.exists(self.places["distro"]))

    def test_a_runtime_REPLACED_after_this_attempt_copied_it_is_left_too(self):
        import io

        def replacing(place, document):
            import shutil as removing

            removing.rmtree(self.places["distro"])
            os.makedirs(self.places["distro"])
            Path(self.places["distro"], "theirs").write_text("not ours")
            raise OSError("and then the publication failed")

        out = io.StringIO()
        with mock.patch.object(instance, "create", replacing):
            with self.assertRaises(OSError):
                self.installing(stream=out)
        self.assertTrue(os.path.exists(
            os.path.join(self.places["distro"], "theirs")))
        self.assertIn("no longer the runtime this attempt made", out.getvalue())

    def test_a_cleanup_that_cannot_remove_says_so_rather_than_raising(self):
        """A cleanup failure must not be thrown over the refusal that caused
        it, and must not be reported as a removal that happened."""
        import io

        real = os.unlink

        def failing(place, *operands, **named):
            # ONLY the justfile: patching every unlink would break the
            # temporary-directory teardown rather than the case under test.
            if str(place) == self.places["justfile"]:
                raise OSError("permission denied")
            return real(place, *operands, **named)

        out = io.StringIO()
        with mock.patch.object(instance, "create",
                               side_effect=OSError("the disk went away")), \
                mock.patch.object(os, "unlink", failing):
            with self.assertRaises(OSError):
                self.installing(stream=out)
        self.assertIn("could not remove", out.getvalue())
        self.assertIn("it is still there", out.getvalue())

    def test_a_path_it_CANNOT_READ_is_left_alone_and_said_so(self):
        """Not being able to tell whether something is still ours is not
        permission to delete it. The uncertain case is left and reported."""
        import io

        real = os.lstat

        def unreadable(place, *operands, **named):
            if str(place) == self.places["justfile"]:
                raise PermissionError("not allowed to look")
            return real(place, *operands, **named)

        out = io.StringIO()
        with mock.patch.object(instance, "create",
                               side_effect=OSError("the disk went away")), \
                mock.patch.object(os, "lstat", unreadable):
            with self.assertRaises(OSError):
                self.installing(stream=out)
        self.assertTrue(os.path.lexists(self.places["justfile"]))
        self.assertIn("could not tell whether", out.getvalue())

    def test_a_FOREIGN_justfile_that_appears_is_never_removed_either(self):
        """The unwind removes what THIS attempt wrote. A justfile that appeared
        after custody looked belongs to whoever put it there: the exclusive
        create refuses it, and the unwind leaves it."""
        theirs = "# it appeared inside the lock\n"
        real = instance.manifest

        def appearing(distro):
            # The step immediately before the justfile is created -- the
            # manifest of the COPIED runtime -- so the file is there when the
            # EXCLUSIVE open happens, which is the interval custody cannot
            # cover. The same function digests the SOURCE during admission,
            # before the destination exists, and that call is left alone.
            if str(distro) == self.places["distro"]:
                Path(self.places["justfile"]).write_text(theirs)
            return real(distro)

        with mock.patch.object(instance, "manifest", appearing):
            with self.assertRaises(self.bootstrap.BootstrapRefusal) as raised:
                self.installing()
        self.assertIn("already a justfile at", str(raised.exception))
        # ASKED BEFORE IT IS READ: reading a file the unwind has removed raises
        # FileNotFoundError out of the check, which is an error rather than the
        # answer this is about.
        self.assertTrue(os.path.lexists(self.places["justfile"]),
                        "their justfile was removed by this attempt's unwind")
        self.assertEqual(Path(self.places["justfile"]).read_text(), theirs)
        # AND THIS ATTEMPT'S OWN COPY IS STILL UNWOUND.
        self.assertFalse(os.path.exists(self.places["distro"]))
        self.assertFalse(os.path.lexists(self.places["instance"]))

    def test_a_FOREIGN_selector_that_appears_is_never_removed(self):
        """The other half: what this attempt did not create, it does not
        touch -- even while unwinding its own."""
        theirs = "somebody else got there first"

        def appearing(place, document):
            Path(place).write_text(theirs)
            raise instance.InstanceRefusal("there is already an instance "
                                           "selector at " + str(place))

        with mock.patch.object(instance, "create", appearing):
            with self.assertRaises(self.bootstrap.BootstrapRefusal):
                self.installing()
        self.assertEqual(Path(self.places["instance"]).read_text(), theirs)
        self.assertFalse(os.path.exists(self.places["distro"]))
        self.assertFalse(os.path.lexists(self.places["justfile"]))

    def test_the_PUBLIC_command_answers_an_installation_failure(self):
        """Review 2026-09-16T19-20-14Z: `main` caught only `BootstrapRefusal`,
        so an expected publication OSError escaped as a traceback AFTER a clean
        unwind -- nothing an operator can act on. The helper still raises it;
        the public command says what happened and exits 2.

        `prepare` is substituted to avoid composing an Authority, which is
        `test_bootstrap`'s; the real `main`, `install` and cleanup run.
        """
        import io

        source = self.root / "built"
        (source / "_internal" / "rpds").mkdir(parents=True)
        (source / "baton-v12-stack").write_text("the launcher")
        (source / "_internal" / "rpds" / "rpds.so").write_text("native")
        said = {"command": "baton-v12-stack", "frozen": True,
                "python": "3.13.7", "platform": "Linux", "machine": "x86_64",
                "schema_assets": {"agent-session-1.0": 10,
                                  "worker-control-1.0": 20},
                "native_rpds": str(source / "_internal" / "rpds" / "rpds.so")}
        inputs = self.root / "inputs.json"
        inputs.write_text(json.dumps({"schema": self.bootstrap.SCHEMA,
                                      "authority_uuid": "0" * 31 + "a"}))
        out = io.StringIO()
        with mock.patch.object(self.bootstrap, "_identity_of",
                               lambda command, runtime=None, distro=None: said), \
                mock.patch.object(self.bootstrap, "prepare",
                                  lambda document, **named: None), \
                mock.patch.object(instance, "create",
                                  side_effect=OSError("the disk went away")):
            code = self.bootstrap.main(
                ["--inputs", str(inputs), "--destination", self.destination,
                 "--distro", str(source), "--no-repositories"], stream=out)
        printed = out.getvalue()
        self.assertEqual(code, 2, printed)
        self.assertIn("refused: the installation could not finish", printed)
        self.assertIn("the disk went away", printed)
        # AND THE CLEANUP DIAGNOSTICS ARE THERE TO READ, above the refusal.
        self.assertIn("cleanup", printed)
        self.assertLess(printed.index("cleanup"), printed.index("refused:"))
        self.assertFalse(os.path.exists(self.places["distro"]))
        self.assertFalse(os.path.lexists(self.places["justfile"]))

    def test_the_PUBLIC_refusal_never_claims_a_cleanup_that_did_not_happen(self):
        """[review 2026-09-16T19-25-41Z]: the refusal asserted that anything
        this attempt made had been unwound -- even when the cleanup had just
        printed that it could not remove a file, which was still there."""
        import io

        source = self.root / "built"
        (source / "_internal" / "rpds").mkdir(parents=True)
        (source / "baton-v12-stack").write_text("the launcher")
        (source / "_internal" / "rpds" / "rpds.so").write_text("native")
        said = {"command": "baton-v12-stack", "frozen": True,
                "python": "3.13.7", "platform": "Linux", "machine": "x86_64",
                "schema_assets": {"agent-session-1.0": 10,
                                  "worker-control-1.0": 20},
                "native_rpds": str(source / "_internal" / "rpds" / "rpds.so")}
        inputs = self.root / "inputs.json"
        inputs.write_text(json.dumps({"schema": self.bootstrap.SCHEMA,
                                      "authority_uuid": "0" * 31 + "a"}))
        real = os.unlink

        def refusing(place, *operands, **named):
            if str(place) == self.places["justfile"]:
                raise PermissionError("not allowed to remove it")
            return real(place, *operands, **named)

        out = io.StringIO()
        with mock.patch.object(self.bootstrap, "_identity_of",
                               lambda command, runtime=None, distro=None: said), \
                mock.patch.object(self.bootstrap, "prepare",
                                  lambda document, **named: None), \
                mock.patch.object(instance, "create",
                                  side_effect=OSError("the disk went away")), \
                mock.patch.object(os, "unlink", refusing):
            code = self.bootstrap.main(
                ["--inputs", str(inputs), "--destination", self.destination,
                 "--distro", str(source), "--no-repositories"], stream=out)
        printed = out.getvalue()
        self.assertEqual(code, 2, printed)
        self.assertIn("could not remove", printed)
        self.assertIn("it is still there", printed)
        # THE FILE IS STILL THERE, and the refusal does not say otherwise.
        self.assertTrue(os.path.lexists(self.places["justfile"]))
        self.assertNotIn("was unwound and reported above", printed)
        self.assertIn("See the cleanup messages above", printed)
        # And the failure itself is still named.
        self.assertIn("the disk went away", printed)

    def test_a_programming_fault_is_NOT_dressed_up_as_a_refusal(self):
        """Only OSError. A TypeError is this implementation's bug and must
        reach whoever can fix it, not be reported to an operator as something
        they did."""
        import io

        source = self.root / "built"
        (source / "_internal" / "rpds").mkdir(parents=True)
        (source / "baton-v12-stack").write_text("the launcher")
        (source / "_internal" / "rpds" / "rpds.so").write_text("native")
        said = {"command": "baton-v12-stack", "frozen": True,
                "python": "3.13.7", "platform": "Linux", "machine": "x86_64",
                "schema_assets": {"agent-session-1.0": 10,
                                  "worker-control-1.0": 20},
                "native_rpds": str(source / "_internal" / "rpds" / "rpds.so")}
        inputs = self.root / "inputs.json"
        inputs.write_text(json.dumps({"schema": self.bootstrap.SCHEMA,
                                      "authority_uuid": "0" * 31 + "a"}))
        with mock.patch.object(self.bootstrap, "_identity_of",
                               lambda command, runtime=None, distro=None: said), \
                mock.patch.object(self.bootstrap, "prepare",
                                  lambda document, **named: None), \
                mock.patch.object(instance, "create",
                                  side_effect=TypeError("a bug in here")):
            with self.assertRaises(TypeError):
                self.bootstrap.main(
                    ["--inputs", str(inputs), "--destination", self.destination,
                     "--distro", str(source), "--no-repositories"],
                    stream=io.StringIO())

    def test_a_link_at_that_name_is_refused_like_any_owned_path(self):
        os.makedirs(self.destination)
        os.symlink(self.root / "somebody-elses", self.places["justfile"])
        with self.assertRaises(self.bootstrap.BootstrapRefusal) as raised:
            self.bootstrap.custody(self.places, self.destination)
        self.assertIn("carries a link at", str(raised.exception))


class TheBootstrapPreparesTheRepositories(Fixture):
    """OWNER-STANDALONE-INTERFACE-20260916.md: the two-argument bootstrap
    "creates the bundled distro, databases and independent repositories".

    THE REPOSITORY TOOL IS SUBSTITUTED HERE, and that is not a convenience:
    this Work performs no version-control mutation, so the commands are
    recorded and the directories they would have made are created as plain
    ones. What is under test is which commands are issued, in which order, and
    which answers are refused -- the owner runs the real ones.
    """

    def setUp(self):
        super().setUp()
        from tools import bootstrap

        self.bootstrap = bootstrap
        self.destination = str(self.root / "deployment")
        self.places = instance.layout(self.destination)
        self.issued = []
        self.answers = {}
        self.common = {}

    def runner(self, argv, **named):
        """A stand-in: it records, makes the directory a clone would have made,
        and answers the reads from a table this test controls."""
        import types

        self.issued.append(list(argv))
        if argv[1] == "clone":
            place = Path(argv[-1])
            common = self.common.get(str(place), place)
            Path(common, "objects", "info").mkdir(parents=True, exist_ok=True)
            place.mkdir(parents=True, exist_ok=True)
            return types.SimpleNamespace(returncode=0, stdout="", stderr="")
        key = " ".join(argv[2:4] if argv[1] == "-C" else argv[1:])
        answer = self.answers.get(" ".join(argv[1:]),
                                  self.answers.get(key, ("", 0)))
        if isinstance(answer, tuple):
            said, code = answer
        else:
            said, code = answer, 0
        if "rev-parse" in argv and "--verify" not in argv:
            said = said or str(self.common.get(argv[2], argv[2]))
        return types.SimpleNamespace(returncode=code, stdout=said, stderr="say why")

    def document(self, **members):
        """A STRUCTURALLY VALID input, because preparation now proves the whole
        document before it clones anything [R2]. A source-only stub used to
        make two clones and only then hit "this input does not supply workers,
        jobs, ..."."""
        given = {
            "schema": self.bootstrap.SCHEMA,
            "state_root": self.destination,
            "authority_uuid": "0" * 31 + "a",
            "checkpoint_profile": "profile",
            "integration_profile": {
                "profile_kind": "profile", "profile_version": 1,
                "integrator_participant": "baton.integrator",
                "instructions_digest": "sha256:" + "e" * 64},
            "retention_policy_digest": "sha256:" + "5" * 64,
            "retention_disposition": "retain",
            "pool_generation": 1, "policy_generation": 1,
            "receipt_participants": {"verification": "baton.verifier",
                                     "review": "baton.approver-review",
                                     "approval": "baton.approver"},
            "workers": [self.worker("impl-a", "implementation", "baton.impl-a"),
                        self.worker("review-a", "review", "baton.review-a"),
                        self.worker("integ-a", "integration",
                                    "baton.integrator")],
            "jobs": [{"job_id": "job-a", "work_id": "0000000a-W1",
                      "line_declared_base": "a" * 40,
                      "canonical_target_id": "target-1",
                      "source_worker_id": "impl-a"}],
            "integration_target_reference": "refs/heads/main"}
        given.update(members)
        return given

    def worker(self, worker_id, role, participant):
        return {"worker_id": worker_id, "role": role, "participant": participant,
                "deployment": {"schema": "baton.v12.single-worker-deployment/4",
                               "image_digest": "sha256:" + "a" * 64}}

    def source(self):
        """Where the clones come FROM. OWNER-VERSION-STAMP-20260916.md moved
        this out of the input document: it is the checkout the bootstrap runs
        from, or an operand naming another one."""
        return str(self.root / "their-source")

    def preparing(self, **members):
        import io

        return self.bootstrap.prepare_repositories(
            self.document(**members), self.places, runner=self.runner,
            stream=io.StringIO(), source=members.pop("source", self.source()))

    def refused(self, **members):
        with self.assertRaises(self.bootstrap.BootstrapRefusal) as raised:
            self.preparing(**members)
        return str(raised.exception)

    def test_the_source_is_INFERRED_from_this_distribution_s_checkout(self):
        """Not the caller's working directory, which is where somebody
        happened to be standing."""
        found = self.bootstrap.repository_source()
        self.assertTrue(found, "no checkout containing v12/justfile was found")
        self.assertTrue(os.path.isfile(os.path.join(found, "v12", "justfile")))
        # And an operand names another one.
        self.assertEqual(self.bootstrap.repository_source("/srv/another"),
                         "/srv/another")

    def test_a_document_that_still_names_a_source_is_REFUSED_by_name(self):
        """Superseded members are refused with the reason, not ignored: the
        two are indistinguishable to an operator until the deployment behaves
        differently from what they asked for."""
        with self.assertRaises(self.bootstrap.BootstrapRefusal) as raised:
            self.bootstrap.held(self.document(repository_source="/srv/theirs"))
        said = str(raised.exception)
        self.assertIn("repository_source", said)
        self.assertIn("no longer names a source", said)
        self.assertIn("--repository-source", said)

    def test_every_role_is_prepared_from_one_source(self):
        held = self.preparing()
        self.assertEqual([one["role"] for one in held["prepared"]],
                         ["target", "workspace", "source-impl-a",
                          "source-review-a", "source-integ-a"])
        clones = [one for one in self.issued if one[1] == "clone"]
        self.assertEqual(len(clones), 5)
        # THE TARGET FROM THE OWNER'S SOURCE, the other two FROM THE TARGET, so
        # each has its own object store rather than a link into another's.
        self.assertIn("--mirror", clones[0])
        self.assertEqual(clones[0][-2], str(self.root / "their-source"))
        for one in clones[1:]:
            self.assertEqual(one[-2], os.path.join(self.places["repository"],
                                                   "target.git"))
        for one in clones:
            self.assertIn("--no-local", one)

    def test_nothing_is_prepared_when_there_is_no_source(self):
        """`--no-repositories`, or a distribution with no checkout to clone
        from: the install says so and leaves a deployment that schedules and
        never reconciles."""
        import io

        self.assertIsNone(self.bootstrap.prepare_repositories(
            self.document(), self.places, runner=self.runner,
            stream=io.StringIO(), source=None))
        self.assertEqual(self.issued, [])
        self.assertFalse(os.path.exists(self.places["repository"]))

    def test_an_existing_path_is_refused_and_left_alone(self):
        theirs = Path(self.places["repository"]) / "workspace"
        theirs.mkdir(parents=True)
        (theirs / "theirs").write_text("somebody else's")
        said = self.refused()
        self.assertIn("already something at", said)
        self.assertEqual((theirs / "theirs").read_text(), "somebody else's")
        # AND NOTHING WAS CLONED: the refusal comes before any of it.
        self.assertEqual(self.issued, [])

    def test_two_repositories_that_are_ONE_repository_are_refused(self):
        root = self.places["repository"]
        self.common[os.path.join(root, "workspace")] = Path(root, "target.git")
        said = self.refused()
        self.assertIn("ONE repository", said)

    def test_borrowed_objects_are_refused(self):
        held = None
        root = Path(self.places["repository"])

        def borrowing(argv, **named):
            answer = self.runner(argv, **named)
            if argv[1] == "clone" and argv[-1].endswith("workspace"):
                borrowed = Path(argv[-1], "objects", "info", "alternates")
                borrowed.parent.mkdir(parents=True, exist_ok=True)
                borrowed.write_text("/somewhere/else/objects\n")
            return answer

        with self.assertRaises(self.bootstrap.BootstrapRefusal) as raised:
            import io

            self.bootstrap.prepare_repositories(
                self.document(), self.places, runner=borrowing,
                stream=io.StringIO(), source=self.source())
        self.assertIn("borrows objects from elsewhere", str(raised.exception))

    def test_a_declared_base_that_is_not_in_the_target_is_refused(self):
        self.answers["cat-file -e"] = ("", 1)
        self.answers[" ".join(["-C", os.path.join(self.places["repository"],
                                                  "target.git")])] = ("", 1)

        def failing(argv, **named):
            if "cat-file" in argv:
                import types

                self.issued.append(list(argv))
                return types.SimpleNamespace(returncode=1, stdout="",
                                             stderr="not a commit")
            return self.runner(argv, **named)

        with self.assertRaises(self.bootstrap.BootstrapRefusal) as raised:
            import io

            self.bootstrap.prepare_repositories(
                self.document(), self.places, runner=failing,
                stream=io.StringIO(), source=self.source())
        said = str(raised.exception)
        self.assertIn("declared base", said)
        self.assertIn("a" * 40, said)

    def test_a_missing_import_reference_is_refused(self):
        def failing(argv, **named):
            if "--verify" in argv:
                import types

                self.issued.append(list(argv))
                return types.SimpleNamespace(returncode=1, stdout="", stderr="no")
            return self.runner(argv, **named)

        with self.assertRaises(self.bootstrap.BootstrapRefusal) as raised:
            import io

            self.bootstrap.prepare_repositories(
                self.document(), self.places, runner=failing,
                stream=io.StringIO(), source=self.source())
        self.assertIn("import reference", str(raised.exception))

    def test_a_source_only_input_clones_NOTHING(self):
        """[R2]: it made two clones and then refused for missing structure."""
        with self.assertRaises(self.bootstrap.BootstrapRefusal) as raised:
            import io

            self.bootstrap.prepare_repositories(
                {"schema": self.bootstrap.SCHEMA}, self.places,
                runner=self.runner, stream=io.StringIO(), source=self.source())
        self.assertIn("not named and cannot be derived", str(raised.exception))
        self.assertEqual(self.issued, [])
        self.assertFalse(os.path.exists(self.places["repository"]))

    def test_a_worker_id_that_is_a_PATH_is_refused_before_anything(self):
        """[R2]: `x/../../../escape` planned a clone outside the destination."""
        escaping = self.worker("x/../../../escape", "implementation",
                               "baton.impl-a")
        said = self.refused(workers=[escaping,
                                     self.worker("review-a", "review",
                                                 "baton.review-a"),
                                     self.worker("integ-a", "integration",
                                                 "baton.integrator")],
                            jobs=[{"job_id": "job-a", "work_id": "0000000a-W1",
                                   "line_declared_base": "a" * 40,
                                   "canonical_target_id": "target-1",
                                   "source_worker_id": "x/../../../escape"}])
        self.assertIn("one path component", said)
        self.assertEqual(self.issued, [])

    def test_a_named_target_that_is_not_the_prepared_one_is_REFUSED(self):
        """[R4]: the fixed plan and a preserved external selection would have
        been two different repositories -- one prepared and proved, the other
        actually configured. Neither is silently overridden."""
        said = self.refused(integration_target="/srv/somewhere/else.git")
        self.assertIn("names different ones", said)
        self.assertIn("/srv/somewhere/else.git", said)
        self.assertIn(os.path.join(self.places["repository"], "target.git"),
                      said)
        self.assertEqual(self.issued, [])

    def test_a_named_source_that_is_not_the_prepared_one_is_REFUSED(self):
        workers = [self.worker("impl-a", "implementation", "baton.impl-a"),
                   self.worker("review-a", "review", "baton.review-a"),
                   self.worker("integ-a", "integration", "baton.integrator")]
        workers[0]["deployment"]["nominated_source"] = "/srv/elsewhere"
        said = self.refused(workers=workers)
        self.assertIn("nominated_source", said)
        self.assertIn("/srv/elsewhere", said)
        self.assertEqual(self.issued, [])

    def test_the_paths_the_plan_derives_ARE_accepted(self):
        root = self.places["repository"]
        workers = [self.worker("impl-a", "implementation", "baton.impl-a"),
                   self.worker("review-a", "review", "baton.review-a"),
                   self.worker("integ-a", "integration", "baton.integrator")]
        for worker in workers:
            worker["deployment"]["nominated_source"] = os.path.join(
                root, "source-" + worker["worker_id"])
        held = self.preparing(
            integration_target=os.path.join(root, "target.git"),
            integration_workspace=os.path.join(root, "workspace"),
            workers=workers)
        self.assertEqual(len(held["prepared"]), 5)

    def test_what_was_already_prepared_is_NAMED_when_a_later_clone_fails(self):
        """[R2]: a partial preparation is repository data this command cannot
        re-derive, so it is reported rather than removed."""
        def failing(argv, **named):
            if argv[1] == "clone" and argv[-1].endswith("workspace"):
                import types

                self.issued.append(list(argv))
                return types.SimpleNamespace(returncode=1, stdout="",
                                             stderr="the clone failed")
            return self.runner(argv, **named)

        with self.assertRaises(self.bootstrap.BootstrapRefusal) as raised:
            import io

            self.bootstrap.prepare_repositories(
                self.document(), self.places, runner=failing,
                stream=io.StringIO(), source=self.source())
        said = str(raised.exception)
        self.assertIn("STILL THERE and was not removed", said)
        self.assertIn("target.git", said)
        self.assertTrue(os.path.exists(os.path.join(self.places["repository"],
                                                    "target.git")))

    def test_preparation_is_serialized_with_other_attempts(self):
        """[R2]: two bootstraps preparing one destination would each find the
        repositories absent. The existence checks are inside the same lock the
        install already takes."""
        import fcntl
        import io

        os.makedirs(self.destination, exist_ok=True)
        other = os.open(self.places["lock"], os.O_RDWR | os.O_CREAT, 0o600)
        self.addCleanup(os.close, other)
        fcntl.flock(other, fcntl.LOCK_EX)
        with self.assertRaises(self.bootstrap.BootstrapRefusal) as raised:
            self.bootstrap.prepare_repositories(
                self.document(), self.places, runner=self.runner,
                stream=io.StringIO(), wait=0.05, source=self.source())
        self.assertIn("another bootstrap is holding", str(raised.exception))
        self.assertEqual(self.issued, [])
        fcntl.flock(other, fcntl.LOCK_UN)
        self.assertEqual(len(self.preparing()["prepared"]), 5)

    def test_worker_storage_OUTSIDE_the_destination_is_refused(self):
        """[R4 remainder]: `workspace_storage` was neither derived nor checked,
        so a deployment whose repositories were prepared under its own
        destination still wrote its workers' storage somewhere else -- possibly
        somewhere shared with another deployment."""
        workers = [self.worker("impl-a", "implementation", "baton.impl-a"),
                   self.worker("review-a", "review", "baton.review-a"),
                   self.worker("integ-a", "integration", "baton.integrator")]
        workers[0]["deployment"]["workspace_storage"] = "/srv/shared/storage"
        said = self.refused(workers=workers)
        self.assertIn("workspace_storage", said)
        self.assertIn("/srv/shared/storage", said)
        self.assertEqual(self.issued, [])

    def test_absent_worker_storage_is_DERIVED_under_the_destination(self):
        held = self.bootstrap.storage_bound(self.document(), self.places)
        for worker in held["workers"]:
            self.assertEqual(
                worker["deployment"]["workspace_storage"],
                os.path.join(self.destination, "workers",
                             worker["worker_id"], "storage"))

    def test_two_workers_sharing_storage_INSIDE_the_instance_is_left_alone(self):
        """Intra-instance sharing is the operator's business; what the rule is
        about is storage that leaves the deployment."""
        shared = os.path.join(self.destination, "workers", "shared")
        workers = [self.worker("impl-a", "implementation", "baton.impl-a"),
                   self.worker("review-a", "review", "baton.review-a"),
                   self.worker("integ-a", "integration", "baton.integrator")]
        for worker in workers[:2]:
            worker["deployment"]["workspace_storage"] = shared
        held = self.bootstrap.storage_bound(self.document(workers=workers),
                                            self.places)
        self.assertEqual(held["workers"][0]["deployment"]["workspace_storage"],
                         shared)
        self.assertEqual(held["workers"][1]["deployment"]["workspace_storage"],
                         shared)
        self.assertEqual(len(self.preparing(workers=workers)["prepared"]), 5)

    def test_the_credential_registry_is_never_moved(self):
        """It is the OWNER'S file, outside the destination on purpose."""
        workers = [self.worker("impl-a", "implementation", "baton.impl-a"),
                   self.worker("review-a", "review", "baton.review-a"),
                   self.worker("integ-a", "integration", "baton.integrator")]
        registry = "/home/somebody/.baton/credential-sources.json"
        for worker in workers:
            worker["deployment"]["credential_sources"] = registry
        held = self.bootstrap.storage_bound(self.document(workers=workers),
                                            self.places)
        for worker in held["workers"]:
            self.assertEqual(worker["deployment"]["credential_sources"],
                             registry)

    def test_a_destination_TAKEN_while_this_attempt_queued_is_refused(self):
        """[R2 remainder]: custody was asked before the wait, so a foreign
        runtime, selector or justfile that appeared while this attempt queued
        for the lock was never seen -- and every clone went ahead into a
        destination somebody else had taken."""
        import fcntl
        import io
        import threading

        os.makedirs(self.destination, exist_ok=True)
        other = os.open(self.places["lock"], os.O_RDWR | os.O_CREAT, 0o600)
        self.addCleanup(os.close, other)
        fcntl.flock(other, fcntl.LOCK_EX)

        def taking():
            # What the other attempt finished while this one waited.
            os.makedirs(self.places["distro"], exist_ok=True)
            Path(self.places["justfile"]).write_text("# theirs\n")
            Path(self.places["instance"]).write_text("{}")
            fcntl.flock(other, fcntl.LOCK_UN)

        threading.Timer(0.1, taking).start()
        with self.assertRaises(self.bootstrap.BootstrapRefusal) as raised:
            self.bootstrap.prepare_repositories(
                self.document(), self.places, runner=self.runner,
                stream=io.StringIO(), wait=5.0, source=self.source())
        said = str(raised.exception)
        self.assertTrue("already a runtime" in said
                        or "already a justfile" in said
                        or "already an instance selector" in said, said)
        # ZERO CLONES, and their material untouched.
        self.assertEqual([one for one in self.issued if one[1] == "clone"], [])
        self.assertEqual(Path(self.places["justfile"]).read_text(), "# theirs\n")

    def test_the_configuration_NAMES_what_was_prepared(self):
        held = self.bootstrap.repositories_bound(self.document(), self.places)
        root = self.places["repository"]
        self.assertEqual(held["integration_target"],
                         os.path.join(root, "target.git"))
        self.assertEqual(held["workers"][0]["deployment"]["nominated_source"],
                         os.path.join(root, "source-impl-a"))

    def test_a_workspace_derived_as_the_ROOT_becomes_the_workspace_clone(self):
        given = self.bootstrap.workspace_bound(self.document(), self.places)
        self.assertEqual(given["integration_workspace"],
                         self.places["repository"])
        held = self.bootstrap.repositories_bound(given, self.places)
        self.assertEqual(held["integration_workspace"],
                         os.path.join(self.places["repository"], "workspace"))

    def test_what_the_owner_named_is_still_never_overwritten(self):
        """`repositories_bound` fills what is ABSENT and changes nothing that
        is named. Naming something the plan does not prepare is refused by
        `repositories_agree` BEFORE any of this -- the two rules together are
        what stop a prepared repository and a configured one diverging."""
        theirs = "/srv/somewhere/else.git"
        held = self.bootstrap.repositories_bound(
            self.document(integration_target=theirs), self.places)
        self.assertEqual(held["integration_target"], theirs)
        with self.assertRaises(self.bootstrap.BootstrapRefusal):
            self.bootstrap.repositories_agree(
                self.document(integration_target=theirs), self.places)

    def test_nothing_is_named_when_nothing_is_prepared(self):
        given = self.document()
        self.assertEqual(
            self.bootstrap.repositories_bound(given, self.places, False), given)
        self.assertEqual(
            self.bootstrap.storage_bound(given, self.places, False), given)


class WhatARecipeAsksAnInstance(Fixture):
    """The lifecycle recipes need the INSTALLED command's path. Deriving it in
    shell would be a second copy of `layout`, and two derivations that disagree
    are two deployments sharing a name."""

    def answering(self, *operands):
        out = io.StringIO()
        code = instance.main(list(operands), stream=out)
        return code, out.getvalue().strip()

    def test_it_answers_the_installed_command(self):
        _destination, places, _ = self.prepared()
        code, said = self.answering("command", places["instance"])
        self.assertEqual(code, 0)
        self.assertEqual(said, places["command"])

    def test_it_answers_the_other_derived_places(self):
        destination, places, _ = self.prepared()
        for question in ("destination", "state", "logs", "repository"):
            code, said = self.answering(question, places["instance"])
            self.assertEqual((code, said), (0, places[question]), question)

    def test_a_selector_it_would_refuse_answers_nothing(self):
        """The recipe runs what this prints. A path out of a document the
        module would refuse is the one thing it must never print."""
        _destination, places, _ = self.prepared()
        _other, elsewhere, _ = self.prepared("b")
        self.rewrite(places, state=elsewhere["state"])
        code, said = self.answering("command", places["instance"])
        self.assertEqual((code, said), (2, ""))

    def test_a_CHANGED_LAUNCHER_is_never_handed_back_to_be_run(self):
        """[K2]: `read` validates the selector and says nothing about the bytes
        at the end of it, so the recipes ran a changed runtime and returned
        zero. A runtime cannot check its own bytes after it is loaded."""
        _destination, places, _ = self.prepared()
        (Path(places["distro"]) / "baton-v12-stack").write_text("a different build")
        code, said = self.answering("command", places["instance"])
        self.assertEqual((code, said), (2, ""))

    def test_a_CHANGED_LIBRARY_beside_it_is_refused_too(self):
        _destination, places, _ = self.prepared()
        (Path(places["distro"]) / "_internal" / "lib.so").write_text("tampered")
        code, said = self.answering("command", places["instance"])
        self.assertEqual((code, said), (2, ""))

    def test_an_UNBOUND_EXTRA_file_in_the_bundle_is_refused(self):
        """The manifest binds the whole folder, so a file nobody recorded is a
        different runtime rather than a harmless addition."""
        _destination, places, _ = self.prepared()
        (Path(places["distro"]) / "_internal" / "extra.so").write_text("new")
        code, said = self.answering("command", places["instance"])
        self.assertEqual((code, said), (2, ""))

    def test_the_places_an_operator_LOOKS_are_still_answered(self):
        """Nothing executes `state` or `logs`, and they are where somebody
        looks when a deployment is broken. A refusal there would take away the
        means of finding out why."""
        _destination, places, _ = self.prepared()
        (Path(places["distro"]) / "baton-v12-stack").write_text("a different build")
        for question in ("state", "logs", "destination"):
            code, said = self.answering(question, places["instance"])
            self.assertEqual((code, said), (0, places[question]), question)

    def test_an_absent_selector_answers_nothing(self):
        code, said = self.answering("command", str(self.root / "nothing.json"))
        self.assertEqual((code, said), (2, ""))


if __name__ == "__main__":
    unittest.main(verbosity=2)
