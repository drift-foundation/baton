"""W375516 — configured prerequisites and application-read-only validation.

Nothing here installs operationally, runs an engine or provider, or touches a
retained store: every store is a disposable one this module creates and the
prerequisite roots are temporary directories.
"""

import hashlib
import os
import pathlib
import shutil
import stat
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "src"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

from tools import bootstrap                                      # noqa: E402


def worker(home, who="w-1", **named):
    held = {"workspace_storage": os.path.join(home, who, "storage"),
            "launch_home": os.path.join(home, who, "launch"),
            "credential_home": os.path.join(home, who, "credentials")}
    held.update(named)
    return {"worker_id": who, "deployment": held}


class TheTripleIsTheOneStageExecutionNames(unittest.TestCase):
    """REQUIRED REUSE: the roots are the triple that module already holds
    together, not a second list."""

    def test_the_three_names(self):
        from tools import stage_execution  # noqa: F401
        self.assertEqual(bootstrap.PREREQUISITE_ROOTS,
                         ("workspace_storage", "launch_home",
                          "credential_home"))

    def test_every_configured_root_of_every_worker_is_named(self):
        home = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, home, True)
        document = {"workers": [worker(home, "w-1"), worker(home, "w-2")]}
        self.assertEqual(len(bootstrap.prerequisite_places(document)), 6)

    def test_a_shared_root_is_named_once(self):
        """Two workers of one instance sharing a root is the operator's
        business; preparing it twice is not."""
        home = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, home, True)
        one = worker(home, "w-1")
        two = worker(home, "w-2", **one["deployment"])
        held = bootstrap.prerequisite_places({"workers": [one, two]})
        self.assertEqual(len(held), 3)

    def test_a_malformed_worker_entry_names_nothing(self):
        for named in ({"workers": None}, {"workers": [None]},
                      {"workers": [{"worker_id": "w"}]}, {}):
            with self.subTest(document=named):
                self.assertEqual(bootstrap.prerequisite_places(named), [])


class TheReportIsApplicationReadOnly(unittest.TestCase):
    """It says what is wrong and changes nothing. No initialize, migrate,
    repair, chmod or writable fallback."""

    def setUp(self):
        self.home = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.home, True)
        self.document = {"workers": [worker(self.home)]}

    def test_every_missing_root_is_reported_by_exact_path(self):
        said = bootstrap.prerequisite_report(self.document)
        self.assertEqual(len(said), 3)
        for _who, _name, place, why in said:
            self.assertEqual(why, "does not exist")
            self.assertTrue(place.startswith(self.home))

    def test_it_creates_nothing(self):
        before = sorted(os.listdir(self.home))
        bootstrap.prerequisite_report(self.document)
        self.assertEqual(sorted(os.listdir(self.home)), before)
        for _who, _name, place in bootstrap.prerequisite_places(self.document):
            self.assertFalse(os.path.lexists(place), place)

    def test_a_prepared_deployment_reports_nothing(self):
        with open(os.devnull, "w") as quiet:
            bootstrap.prepare_prerequisites(self.document, {}, made={},
                                            stream=quiet)
        self.assertEqual(bootstrap.prerequisite_report(self.document), [])

    def test_a_link_is_unusable_rather_than_followed(self):
        place = bootstrap.prerequisite_places(self.document)[0][2]
        os.makedirs(os.path.dirname(place), exist_ok=True)
        real = os.path.join(self.home, "elsewhere")
        os.makedirs(real)
        os.symlink(real, place)
        said = dict((one[2], one[3])
                    for one in bootstrap.prerequisite_report(self.document))
        self.assertEqual(said[place], "is a symbolic link")

    def test_a_linked_ancestor_is_reported_too(self):
        """W376246: the observation and the preparation disagreed -- a root
        under a linked parent refused at prepare and was reported as fine
        here, so an operator could be told a deployment was ready that an
        install would refuse to make."""
        real = os.path.join(self.home, "real-w-1")
        os.makedirs(real)
        os.symlink(real, os.path.join(self.home, "w-1"))
        said = [one[3] for one in
                bootstrap.prerequisite_report(self.document)]
        self.assertTrue(said)
        for why in said:
            self.assertIn("which resolves to", why)

    def test_a_file_at_an_owed_name_is_reported_as_what_it_is(self):
        place = bootstrap.prerequisite_places(self.document)[1][2]
        os.makedirs(os.path.dirname(place), exist_ok=True)
        with open(place, "w", encoding="utf-8") as handle:
            handle.write("not a root")
        said = dict((one[2], one[3])
                    for one in bootstrap.prerequisite_report(self.document))
        self.assertIn("not a directory", said[place])

    def test_an_unusable_mode_is_reported_without_repair(self):
        place = bootstrap.prerequisite_places(self.document)[2][2]
        os.makedirs(place)
        os.chmod(place, 0o000)
        self.addCleanup(os.chmod, place, 0o700)
        if os.geteuid() == 0:
            self.skipTest("root bypasses the access check this case drives")
        said = dict((one[2], one[3])
                    for one in bootstrap.prerequisite_report(self.document))
        self.assertIn("not readable, writable and traversable", said[place])
        self.assertEqual(stat.S_IMODE(os.lstat(place).st_mode), 0o000,
                         "the report must not chmod anything")


class ThePrepareOwnsOnlyWhatItMade(unittest.TestCase):

    def setUp(self):
        self.home = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.home, True)
        self.document = {"workers": [worker(self.home)]}
        self.quiet = open(os.devnull, "w")
        self.addCleanup(self.quiet.close)

    def prepared(self, made=None):
        """`made` IS THE CALLER'S, so a refusal mid-way still hands back the
        roots this attempt created -- the property the review found missing."""
        made = {} if made is None else made
        return bootstrap.prepare_prerequisites(self.document, {}, made=made,
                                               stream=self.quiet)

    def test_every_configured_root_is_created_and_owned(self):
        """EVERY COMPONENT, not just the leaf. W376246: `os.makedirs` creates
        missing PARENTS, and recording only the leaves left every intermediate
        this attempt made outside the unwind."""
        made = self.prepared()
        for _who, _name, place in bootstrap.prerequisite_places(self.document):
            self.assertIn(place, made, place)
        self.assertIn(os.path.join(self.home, "w-1"), made,
                      "the intermediate this attempt created is owned too")
        self.assertEqual(len(made), 4)
        for place, identity in made.items():
            held = os.lstat(place)
            self.assertTrue(stat.S_ISDIR(held.st_mode))
            self.assertEqual(identity, (held.st_dev, held.st_ino))

    def test_an_existing_root_is_left_alone_and_is_not_ours(self):
        """An occupied prerequisite is the operator's: not repaired, and NOT
        in the unwind, so a later failure cannot remove somebody else's."""
        place = bootstrap.prerequisite_places(self.document)[0][2]
        os.makedirs(place)
        os.chmod(place, 0o755)
        made = self.prepared()
        self.assertNotIn(place, made)
        self.assertEqual(stat.S_IMODE(os.lstat(place).st_mode), 0o755,
                         "an existing root must not be chmodded")

    def test_a_link_at_an_owed_name_refuses(self):
        place = bootstrap.prerequisite_places(self.document)[0][2]
        os.makedirs(os.path.dirname(place), exist_ok=True)
        real = os.path.join(self.home, "elsewhere")
        os.makedirs(real)
        os.symlink(real, place)
        with self.assertRaises(bootstrap.BootstrapRefusal) as caught:
            self.prepared()
        said = str(caught.exception)
        self.assertIn("nothing here follows a link", said)
        self.assertTrue(os.path.islink(place), "the link must be left as is")
        self.assertEqual(os.listdir(real), [], "nothing written through it")

    def test_a_file_at_an_owed_name_refuses(self):
        place = bootstrap.prerequisite_places(self.document)[1][2]
        os.makedirs(os.path.dirname(place), exist_ok=True)
        with open(place, "w", encoding="utf-8") as handle:
            handle.write("foreign")
        with self.assertRaises(bootstrap.BootstrapRefusal) as caught:
            self.prepared()
        self.assertIn("left exactly as it is", str(caught.exception))
        with open(place, encoding="utf-8") as reading:
            self.assertEqual(reading.read(), "foreign")

    def test_a_refusal_still_hands_back_what_was_already_created(self):
        """THE REVIEW'S FIRST BLOCKER. A link at the third owed name used to
        throw away the two roots this attempt had just made, so `install`'s
        unwind never saw them and the residue blocked its own retry."""
        places = bootstrap.prerequisite_places(self.document)
        os.makedirs(os.path.dirname(places[2][2]), exist_ok=True)
        real = os.path.join(self.home, "elsewhere")
        os.makedirs(real)
        for place in (places[0][2], places[1][2]):
            os.makedirs(place)
        os.symlink(real, places[2][2])
        made = {}
        with self.assertRaises(bootstrap.BootstrapRefusal):
            self.prepared(made)
        # Nothing was created, because every root is inspected first -- and
        # the dictionary is the caller's either way, so whatever HAD been made
        # would be in it.
        self.assertEqual(made, {})

    def test_nothing_is_created_when_a_later_root_refuses(self):
        """Every root is inspected before any is created, so an install that
        is going to refuse refuses with nothing made at all."""
        places = bootstrap.prerequisite_places(self.document)
        os.makedirs(os.path.dirname(places[2][2]), exist_ok=True)
        with open(places[2][2], "w", encoding="utf-8") as handle:
            handle.write("foreign")
        made = {}
        with self.assertRaises(bootstrap.BootstrapRefusal):
            self.prepared(made)
        self.assertEqual(made, {})
        for _who, _name, place in places[:2]:
            self.assertFalse(os.path.lexists(place), place)

    def test_an_inaccessible_existing_root_refuses(self):
        """THE REVIEW'S SECOND BLOCKER: it used to be accepted, which moved
        the failure to the first start."""
        if os.geteuid() == 0:
            self.skipTest("root bypasses the access check this case drives")
        place = bootstrap.prerequisite_places(self.document)[0][2]
        os.makedirs(place)
        os.chmod(place, 0o000)
        self.addCleanup(os.chmod, place, 0o700)
        with self.assertRaises(bootstrap.BootstrapRefusal) as caught:
            self.prepared()
        self.assertIn("nothing here chmods a root", str(caught.exception))
        self.assertEqual(stat.S_IMODE(os.lstat(place).st_mode), 0o000)

    def test_a_linked_ancestor_refuses(self):
        """THE REVIEW'S THIRD BLOCKER. `os.makedirs` creates missing parents
        and traverses existing ones, so a link above an owed name put this
        deployment's state somewhere it did not choose."""
        who = os.path.join(self.home, "w-1")
        real = os.path.join(self.home, "real-w-1")
        os.makedirs(real)
        os.symlink(real, who)
        with self.assertRaises(bootstrap.BootstrapRefusal) as caught:
            self.prepared()
        self.assertIn("through a link", str(caught.exception))
        self.assertEqual(os.listdir(real), [],
                         "nothing may be created through the link")

    def test_a_prepared_root_is_private_whatever_the_umask(self):
        """W376246: a creation mode is umask-filtered, so under `umask 000` a
        prepared root was 0777 -- world-writable mutable state nobody asked
        for. The mode is named and applied on what this call created."""
        before = os.umask(0o000)
        self.addCleanup(os.umask, before)
        for place in self.prepared():
            self.assertEqual(stat.S_IMODE(os.lstat(place).st_mode),
                             bootstrap.PREREQUISITE_MODE, place)

    def test_a_populated_root_this_attempt_made_is_not_removed(self):
        """W376246: the unwind used `rmtree`, so a directory this attempt
        created that somebody else wrote into had THEIR content deleted. The
        uncertainty is reported instead."""
        made = self.prepared()
        place = bootstrap.unwound_order(made)[0]
        theirs = os.path.join(place, "theirs.txt")
        with open(theirs, "w", encoding="utf-8") as handle:
            handle.write("not this attempt's")
        said = bootstrap._remove_if_still_ours(place, made[place], "root")
        self.assertIn("would take somebody else's content", said)
        self.assertTrue(os.path.isfile(theirs), "their file must survive")
        self.assertTrue(os.path.isdir(place))

    def test_a_populated_owned_runtime_unwinds_through_its_own_ledger(self):
        """W376956 REPLACES THE `whole=True` CASE THIS USED TO BE.

        That case asserted a populated owned root was `rmtree`d, because the
        copied runtime was owned as ONE root identity and wholesale removal
        was the only way to remove it at all. The parent FINDING forbids
        exactly that -- "whole=True/root identity... cannot alone establish
        ownership" -- and `copy_runtime` now records every object, so the
        subtree unwinds one object at a time through the guard that was
        already here. The operand is gone.
        """
        self.assertNotIn("whole", bootstrap._remove_if_still_ours.__code__
                         .co_varnames[:bootstrap._remove_if_still_ours
                                      .__code__.co_argcount])
        source = os.path.join(self.home, "source")
        os.makedirs(os.path.join(source, "inner"))
        with open(os.path.join(source, "inner", "f"), "w",
                  encoding="utf-8") as handle:
            handle.write("this attempt's")
        place = os.path.join(self.home, "runtime")
        made = {}
        bootstrap.copy_runtime(source, place, made=made)
        said = [bootstrap._remove_if_still_ours(one, made[one], "runtime")
                for one in bootstrap.unwound_order(made)]
        self.assertEqual([one for one in said if one and "unwound" not in one],
                         [])
        self.assertFalse(os.path.lexists(place))

    def test_a_populated_root_is_still_refused(self):
        """And the prepared-root rule is unchanged: no recursive removal, so
        somebody else's content is never taken."""
        made = self.prepared()
        place = bootstrap.unwound_order(made)[0]
        with open(os.path.join(place, "theirs"), "w",
                  encoding="utf-8") as handle:
            handle.write("not ours")
        said = bootstrap._remove_if_still_ours(place, made[place], "root")
        self.assertIn("would take somebody else's content", said)
        self.assertTrue(os.path.isdir(place))

    def test_a_replacement_between_mkdir_and_chmod_refuses(self):
        """THE TOCTOU: the mode used to be applied BY NAME right after the
        `mkdir`, so a racer swapping the new directory for a link had its
        FOREIGN target chmodded from 0755 to 0700 and the replacement
        recorded as ours. The open is `O_NOFOLLOW`, so it refuses."""
        foreign = os.path.join(self.home, "foreign-target")
        os.makedirs(foreign)
        os.chmod(foreign, 0o755)
        places = bootstrap.prerequisite_places(self.document)
        made = {}
        original = os.mkdir

        def mkdir(path, *args, **named):
            original(path, *args, **named)
            if path == os.path.basename(places[0][2]):
                os.rmdir(path, dir_fd=named["dir_fd"])
                os.symlink(foreign, path, dir_fd=named["dir_fd"])

        from unittest import mock
        with mock.patch("os.mkdir", mkdir):
            with self.assertRaises(bootstrap.BootstrapRefusal) as caught:
                self.prepared(made)
        self.assertIn("identity failure is not evidence of replacement",
                      str(caught.exception))
        self.assertEqual(stat.S_IMODE(os.lstat(foreign).st_mode), 0o755,
                         "the foreign target's mode must be untouched")
        self.assertIsInstance(made[places[0][2]], bootstrap._UncertainPrerequisite,
                              "uncertain effects never grant deletion authority")

    def test_a_mode_that_cannot_be_applied_refuses_and_is_owned(self):
        """It used to `continue`, so a root that could not be made private was
        reported as prepared. It refuses -- and the directory is still owned,
        so the unwind can try to remove it."""
        made = {}
        from unittest import mock
        with mock.patch("os.chmod", side_effect=OSError(1, "nope")):
            with self.assertRaises(bootstrap.BootstrapRefusal) as caught:
                self.prepared(made)
        self.assertIn("is not one it reports as ready", str(caught.exception))
        self.assertTrue(made, "what was created is owned so it can be undone")

    def test_a_file_at_an_existing_ancestor_refuses(self):
        """W376246 finding 3: the realpath rule catches a LINK anywhere above,
        but a plain FILE at an intermediate resolves to itself -- so it
        escaped the check a file at the leaf gets, and the `mkdir` beneath it
        failed with a bare OS error instead of this module's refusal."""
        with open(os.path.join(self.home, "w-1"), "w",
                  encoding="utf-8") as handle:
            handle.write("foreign")
        made = {}
        with self.assertRaises(bootstrap.BootstrapRefusal) as caught:
            self.prepared(made)
        said = str(caught.exception)
        self.assertIn("not a directory", said)
        self.assertIn("beneath another object's name", said)
        self.assertEqual(made, {}, "nothing is created beneath it")
        with open(os.path.join(self.home, "w-1"), encoding="utf-8") as one:
            self.assertEqual(one.read(), "foreign")

    def test_a_racing_link_at_an_owed_name_is_revalidated(self):
        """W376246: `FileExistsError` was accepted without revalidation, so an
        object appearing in that window was treated as usable. A link that
        races in refuses, and is not owned."""
        places = bootstrap.prerequisite_places(self.document)
        real = os.path.join(self.home, "elsewhere")
        os.makedirs(real)
        made = {}
        original = os.mkdir
        racing = {"done": False}

        def mkdir(path, *args, **named):
            original(path, *args, **named)
            if not racing["done"] and path == os.path.basename(os.path.dirname(places[0][2])):
                racing["done"] = True
                os.symlink(real, places[0][2])

        from unittest import mock
        with mock.patch("os.mkdir", mkdir):
            with self.assertRaises(bootstrap.BootstrapRefusal) as caught:
                self.prepared(made)
        self.assertIn("follows a link", str(caught.exception))
        self.assertNotIn(places[0][2], made,
                         "a racer's object is never owned by this attempt")
        self.assertTrue(os.path.islink(places[0][2]))

    def test_the_owned_unwind_removes_exactly_what_was_made(self):
        """`install`'s existing helper, driven over this answer."""
        made = self.prepared()
        foreign = os.path.join(self.home, "foreign")
        os.makedirs(foreign)
        # INNERMOST FIRST, which is what `unwound_order` answers: a parent
        # cannot go before its child, and the unwind refuses to remove a
        # populated directory.
        for place in bootstrap.unwound_order(made):
            bootstrap._remove_if_still_ours(place, made[place], "root")
            self.assertFalse(os.path.lexists(place), place)
        self.assertTrue(os.path.isdir(foreign))

    def test_a_replaced_root_is_no_longer_ours_and_survives(self):
        made = self.prepared()
        place = bootstrap.unwound_order(made)[0]
        identity = made[place]
        os.rmdir(place)
        os.makedirs(place)
        bootstrap._remove_if_still_ours(place, identity, "root")
        self.assertTrue(os.path.isdir(place),
                        "a root replaced since creation is not this "
                        "attempt's and must survive the unwind")


class TheCreationHasProvenance(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = pathlib.Path(self.temp.name)
        self.root = self.home / 'root'
        self.document = {'workers': [{'worker_id': 'probe', 'deployment': {'workspace_storage': str(self.root)}}]}
        self.made = {}

    def prepare(self):
        import io
        return bootstrap.prepare_prerequisites(self.document, {}, made=self.made, stream=io.StringIO())

    def test_ordinary_replacement_cannot_be_chmodded_or_adopted(self):
        from unittest import mock
        foreign = self.home / 'foreign'
        foreign.mkdir(mode=0o755)
        identity = (foreign.stat().st_dev, foreign.stat().st_ino)
        mkdir = os.mkdir
        def replace(leaf, mode, *, dir_fd):
            mkdir(leaf, mode, dir_fd=dir_fd)
            os.rmdir(leaf, dir_fd=dir_fd)
            os.rename(foreign, leaf, dst_dir_fd=dir_fd)
        with mock.patch.object(os, 'mkdir', side_effect=replace), mock.patch.object(os, 'chmod', side_effect=AssertionError('foreign permission mutation')):
            with self.assertRaisesRegex(bootstrap.BootstrapRefusal, 'creation identity is uncertain'):
                self.prepare()
        self.assertEqual((self.root.stat().st_dev, self.root.stat().st_ino), identity)
        self.assertEqual(stat.S_IMODE(self.root.stat().st_mode), 0o755)
        effect = self.made[str(self.root)]
        self.assertIsInstance(effect, bootstrap._UncertainPrerequisite)
        with mock.patch.object(os, 'lstat', side_effect=AssertionError('uncertainty must not inspect for deletion')):
            self.assertIn('no deletion authority', bootstrap._remove_if_still_ours(str(self.root), effect, 'root'))
        self.assertTrue(self.root.exists())

    def test_replacement_after_proof_cannot_redirect_permission_change(self):
        from unittest import mock
        foreign = self.home / 'foreign'
        foreign.mkdir(mode=0o755)
        original = self.home / 'created'
        prove = bootstrap._CreationWatch.prove
        def replace(watch, leaf):
            prove(watch, leaf)
            self.root.rename(original)
            foreign.rename(self.root)
        with mock.patch.object(bootstrap._CreationWatch, 'prove', replace):
            with self.assertRaisesRegex(bootstrap.BootstrapRefusal, 'changed at'):
                self.prepare()
        self.assertEqual(stat.S_IMODE(self.root.stat().st_mode), 0o755)
        self.assertEqual(self.made[str(self.root)], (original.stat().st_dev, original.stat().st_ino))
        self.assertIn('no longer', bootstrap._remove_if_still_ours(str(self.root), self.made[str(self.root)], 'root'))
        self.assertTrue(self.root.exists())

    def test_ancestor_replacement_does_not_redirect_creation(self):
        from unittest import mock
        parent = self.home / 'parent'
        parent.mkdir()
        self.root = parent / 'root'
        self.document['workers'][0]['deployment']['workspace_storage'] = str(self.root)
        moved = self.home / 'moved-parent'
        foreign = self.home / 'foreign'
        foreign.mkdir(mode=0o755)
        mkdir = os.mkdir
        def replace(leaf, mode, *, dir_fd):
            parent.rename(moved)
            foreign.rename(parent)
            return mkdir(leaf, mode, dir_fd=dir_fd)
        with mock.patch.object(os, 'mkdir', side_effect=replace):
            with self.assertRaises(bootstrap.BootstrapRefusal):
                self.prepare()
        self.assertEqual(list(parent.iterdir()), [])
        self.assertEqual(stat.S_IMODE(parent.stat().st_mode), 0o755)
        self.assertTrue((moved / 'root').is_dir())
        self.assertIsInstance(self.made[str(self.root)], bootstrap._UncertainPrerequisite)

    def test_component_appearance_during_discovery_refuses(self):
        from unittest import mock
        components = bootstrap._components
        def appear(place):
            self.root.mkdir(mode=0o755)
            return components(place)
        with mock.patch.object(bootstrap, '_components', side_effect=appear):
            with self.assertRaisesRegex(bootstrap.BootstrapRefusal, 'appeared'):
                self.prepare()
        self.assertEqual(self.made, {})
        self.assertEqual(stat.S_IMODE(self.root.stat().st_mode), 0o755)

    def test_open_failure_records_uncertainty_without_replacement_claim(self):
        from unittest import mock
        opening = bootstrap._prerequisite_handle
        def denied(parent, leaf):
            if leaf == 'root':
                raise PermissionError('injected access refusal')
            return opening(parent, leaf)
        with mock.patch.object(bootstrap, '_prerequisite_handle', side_effect=denied):
            with self.assertRaisesRegex(bootstrap.BootstrapRefusal, 'PermissionError') as caught:
                self.prepare()
        self.assertIn('not evidence of replacement', str(caught.exception))
        self.assertTrue(self.root.exists())
        self.assertIsInstance(self.made[str(self.root)], bootstrap._UncertainPrerequisite)

    def test_identity_failure_records_uncertainty(self):
        from unittest import mock
        identity = bootstrap._identity_of_handle
        def fail(handle):
            if os.readlink('/proc/self/fd/' + str(handle)) == str(self.root):
                raise OSError('injected fstat refusal')
            return identity(handle)
        with mock.patch.object(bootstrap, '_identity_of_handle', side_effect=fail):
            with self.assertRaises(bootstrap.BootstrapRefusal):
                self.prepare()
        self.assertIsInstance(self.made[str(self.root)], bootstrap._UncertainPrerequisite)
        self.assertTrue(self.root.exists())

    def test_missing_events_and_overflow_never_grant_ownership(self):
        import struct
        from unittest import mock
        for raw in (b'', struct.pack('iIII', -1, 0x4000, 0, 0), b'incomplete'):
            with self.subTest(raw=raw):
                with mock.patch.object(os, 'read', return_value=raw):
                    with self.assertRaises(bootstrap.BootstrapRefusal):
                        self.prepare()
                self.assertIsInstance(self.made[str(self.root)], bootstrap._UncertainPrerequisite)
                self.root.rmdir()
                self.made.clear()

    def test_observer_failure_precedes_any_creation(self):
        from unittest import mock
        with mock.patch.object(bootstrap, '_CreationWatch', side_effect=PermissionError('watch denied')):
            with self.assertRaises(bootstrap.BootstrapRefusal):
                self.prepare()
        self.assertEqual(self.made, {})
        self.assertFalse(self.root.exists())

    def test_partial_mkdir_failure_has_no_unproved_deletion_authority(self):
        from unittest import mock
        mkdir = os.mkdir
        def failed(leaf, mode, *, dir_fd):
            mkdir(leaf, mode, dir_fd=dir_fd)
            raise OSError('lost completion')
        with mock.patch.object(os, 'mkdir', side_effect=failed):
            with self.assertRaises(bootstrap.BootstrapRefusal):
                self.prepare()
        self.assertTrue(self.root.exists())
        self.assertIsInstance(self.made[str(self.root)], bootstrap._UncertainPrerequisite)

    def test_restrictive_umask_without_global_umask_changes(self):
        # Set only in this test; the implementation never changes global umask.
        from unittest import mock
        prior = os.umask(0o777)
        try:
            with mock.patch.object(os, 'umask', side_effect=AssertionError('global umask mutation')):
                self.prepare()
            self.assertEqual(stat.S_IMODE(self.root.stat().st_mode), 0o700)
            self.assertEqual(bootstrap.prerequisite_report(self.document), [])
        finally:
            os.umask(prior)

    def test_identity_remains_pinned_for_later_unwind(self):
        self.prepare()
        identity = self.made[str(self.root)]
        self.assertIsInstance(identity, bootstrap._OwnedPrerequisite)
        self.root.rmdir()
        self.assertEqual(os.fstat(identity.handle).st_nlink, 0)
        self.root.mkdir()
        self.assertNotEqual(identity, (self.root.stat().st_dev, self.root.stat().st_ino))
        self.assertIn('no longer', bootstrap._remove_if_still_ours(str(self.root), identity, 'root'))
        self.assertTrue(self.root.exists())

    def test_readonly_report_refuses_raced_ancestor_link(self):
        from unittest import mock
        self.root.mkdir()
        foreign = self.home / 'foreign'
        foreign.mkdir()
        opening = bootstrap._prerequisite_handle
        def replace(parent, leaf):
            if leaf == 'root':
                self.root.rmdir()
                self.root.symlink_to(foreign, target_is_directory=True)
            return opening(parent, leaf)
        with mock.patch.object(bootstrap, '_prerequisite_handle', side_effect=replace):
            report = bootstrap.prerequisite_report(self.document)
        self.assertEqual(len(report), 1)
        self.assertIn('cannot be bound', report[0][3])
        self.assertEqual(list(foreign.iterdir()), [])

    def test_failed_later_root_keeps_proven_intermediates(self):
        from unittest import mock
        self.root = self.home / 'parent' / 'root'
        self.document['workers'][0]['deployment']['workspace_storage'] = str(self.root)
        opening = bootstrap._prerequisite_handle
        def denied(parent, leaf):
            if leaf == 'root':
                raise PermissionError('later refusal')
            return opening(parent, leaf)
        with mock.patch.object(bootstrap, '_prerequisite_handle', side_effect=denied):
            with self.assertRaises(bootstrap.BootstrapRefusal):
                self.prepare()
        parent = self.home / 'parent'
        self.assertEqual(self.made[str(parent)], (parent.stat().st_dev, parent.stat().st_ino))
        self.assertIsInstance(self.made[str(self.root)], bootstrap._UncertainPrerequisite)
        self.assertEqual(bootstrap.unwound_order(self.made), [str(self.root), str(parent)])



class TheControlStoreIsInitializedThroughItsOwnOpener(unittest.TestCase):

    def setUp(self):
        self.home = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.home, True)
        self.places = {"control_store": os.path.join(self.home,
                                                     "control.sqlite3")}

    def test_an_absent_store_is_initialized_and_closed(self):
        bootstrap.initialize_control_store(
            self.places, incarnation="bootstrap-test",
            clock=lambda: "2026-10-28T00:00:00.000Z")
        self.assertTrue(os.path.isfile(self.places["control_store"]))

    def test_initializing_twice_adopts_rather_than_refusing(self):
        """A second install of the same destination is refused elsewhere; the
        opener itself must adopt a store it already initialized."""
        for _ in range(2):
            bootstrap.initialize_control_store(
                self.places, incarnation="bootstrap-test",
                clock=lambda: "2026-10-28T00:00:00.000Z")

    def test_an_unopenable_store_refuses_in_this_commands_voice(self):
        """So `main` prints "refused:" rather than raising a traceback out of
        a setup command."""
        os.makedirs(self.places["control_store"])
        with self.assertRaises(bootstrap.BootstrapRefusal) as caught:
            bootstrap.initialize_control_store(
                self.places, incarnation="bootstrap-test",
                clock=lambda: "2026-10-28T00:00:00.000Z")
        self.assertIn("not a prepared one", str(caught.exception))

    def test_nothing_holds_the_store_afterwards(self):
        """A prepared instance is one nothing is attached to: the first start
        has to be able to open it."""
        bootstrap.initialize_control_store(
            self.places, incarnation="bootstrap-test",
            clock=lambda: "2026-10-28T00:00:00.000Z")
        from baton_v12.worker_manager.store import ControlStore
        again = ControlStore.open(self.places["control_store"],
                                  incarnation="first-start",
                                  clock=lambda: "2026-10-28T00:00:01.000Z")
        again.close()


if __name__ == "__main__":
    unittest.main()


class TheRuntimeCopyOwnsEveryObjectItMakes(unittest.TestCase):
    """W376956 — runtime copy effects, partial failure, and owned unwind.

    `shutil.copytree` created every entry and this attempt learned about none:
    ONE identity, of the ROOT, taken AFTER the copy finished. So a mid-copy
    failure owned nothing and removed nothing, and the unwind had to be told
    `whole=True` -- which `rmtree`d foreign descendants along with the
    subtree. These cases are about the ledger that replaced it.
    """

    def setUp(self):
        self.home = tempfile.mkdtemp(prefix="v12-runtime-copy-")
        self.addCleanup(shutil.rmtree, self.home, ignore_errors=True)
        self.source = os.path.join(self.home, "source")
        os.makedirs(os.path.join(self.source, "a", "b"))
        for place, text in (("top.txt", "top"),
                            ("a/mid.txt", "mid"),
                            ("a/b/deep.txt", "deep")):
            with open(os.path.join(self.source, place), "w",
                      encoding="utf-8") as handle:
                handle.write(text)
        os.symlink("top.txt", os.path.join(self.source, "link"))
        os.chmod(os.path.join(self.source, "a", "mid.txt"), 0o640)
        self.destination = os.path.join(self.home, "distro")

    def copied(self, **named):
        made = {}
        counted = bootstrap.copy_runtime(self.source, self.destination,
                                         made=made, **named)
        return made, counted

    def unwinding(self, made):
        return [one for one in
                (bootstrap._remove_if_still_ours(place, made[place],
                                                 "copied runtime object")
                 for place in bootstrap.unwound_order(made)) if one]

    # -- what the copy records ---------------------------------------------

    def test_every_object_is_recorded_as_it_is_created(self):
        made, counted = self.copied()
        self.assertEqual(counted, {"directory": 3, "file": 3, "symlink": 1})
        self.assertEqual(
            sorted(one[len(self.destination):] for one in made),
            ["", "/a", "/a/b", "/a/b/deep.txt", "/a/mid.txt", "/link",
             "/top.txt"])
        # THE CONTENT AND THE MODES ARE THE SOURCE'S, which is what the bulk
        # copy preserved and this must not lose.
        with open(os.path.join(self.destination, "a", "b", "deep.txt"),
                  encoding="utf-8") as handle:
            self.assertEqual(handle.read(), "deep")
        self.assertEqual(
            stat.S_IMODE(os.lstat(os.path.join(self.destination, "a",
                                               "mid.txt")).st_mode), 0o640)
        self.assertTrue(os.path.islink(os.path.join(self.destination, "link")))
        self.assertEqual(os.readlink(os.path.join(self.destination, "link")),
                         "top.txt")

    def test_a_copied_file_carries_the_bytes_it_was_given(self):
        """The digest travels with the identity, taken from the buffers the
        copy streamed rather than from a second read."""
        made, _counted = self.copied()
        held = made[os.path.join(self.destination, "top.txt")]
        self.assertEqual(getattr(held, "digest", None),
                         hashlib.sha256(b"top").hexdigest())

    def test_a_copied_directory_retains_its_handle(self):
        made, _counted = self.copied()
        held = made[os.path.join(self.destination, "a")]
        self.assertIsNotNone(getattr(held, "handle", None))
        self.assertEqual(tuple(held),
                         bootstrap._identity_of_handle(held.handle))

    # -- the unwind ---------------------------------------------------------

    def test_a_clean_unwind_removes_exactly_what_was_copied(self):
        made, _counted = self.copied()
        self.assertEqual(
            [one for one in self.unwinding(made) if "unwound" not in one], [])
        self.assertFalse(os.path.lexists(self.destination))

    def test_a_foreign_addition_is_preserved_and_reported(self):
        """THE DEFECT THE OLD `whole=True` UNWIND HAD. Somebody else's file
        under a directory this attempt created is not this attempt's to
        remove, and the directory holding it is left with the uncertainty
        said out loud rather than taken."""
        made, _counted = self.copied()
        theirs = os.path.join(self.destination, "a", "theirs.txt")
        with open(theirs, "w", encoding="utf-8") as handle:
            handle.write("foreign")
        said = self.unwinding(made)
        self.assertTrue(os.path.isfile(theirs))
        self.assertTrue(os.path.isdir(os.path.join(self.destination, "a")))
        self.assertTrue(os.path.isdir(self.destination))
        self.assertTrue(any("would take somebody else's content" in one
                            for one in said))
        # AND THE OBJECTS THAT ARE STILL OURS ARE STILL REMOVED.
        self.assertFalse(os.path.lexists(
            os.path.join(self.destination, "a", "mid.txt")))

    def test_a_same_name_replacement_is_left_to_whoever_replaced_it(self):
        made, _counted = self.copied()
        place = os.path.join(self.destination, "top.txt")
        os.unlink(place)
        with open(place, "w", encoding="utf-8") as handle:
            handle.write("somebody else's file at the same name")
        said = self.unwinding(made)
        self.assertTrue(os.path.isfile(place))
        self.assertTrue(any("belongs to whoever replaced it" in one
                            for one in said))

    def test_a_mutation_of_a_copied_file_is_preserved(self):
        """IDENTITY CANNOT SEE A MUTATION: an edited file is the same inode
        this attempt created. The FINDING requires mutations preserved, so the
        digest is asked as well."""
        made, _counted = self.copied()
        place = os.path.join(self.destination, "a", "b", "deep.txt")
        with open(place, "w", encoding="utf-8") as handle:
            handle.write("somebody edited this")
        said = self.unwinding(made)
        with open(place, encoding="utf-8") as handle:
            self.assertEqual(handle.read(), "somebody edited this")
        self.assertTrue(any("its content has changed since" in one
                            for one in said))

    # -- partial failure ----------------------------------------------------

    def test_a_mid_copy_failure_owns_what_it_already_made(self):
        """THE OTHER HALF OF THE DEFECT. The bulk copy took one identity after
        it finished, so a failure part-way left a partial tree that nothing
        owned -- and the retry then refused for this attempt's own leftovers.

        The source gains an object this copy refuses (a FIFO), so the walk
        fails after some entries exist.
        """
        os.mkfifo(os.path.join(self.source, "a", "pipe"))
        made = {}
        with self.assertRaises(bootstrap.BootstrapRefusal) as raised:
            bootstrap.copy_runtime(self.source, self.destination, made=made)
        self.assertIn("neither a directory, a symlink nor an ordinary file",
                      str(raised.exception))
        # SOMETHING WAS MADE, AND IT IS ALL IN THE LEDGER.
        self.assertIn(self.destination, made)
        self.assertTrue(os.path.isdir(self.destination))
        for place in made:
            self.assertTrue(os.path.lexists(place), place)
        # AND THE UNWIND TAKES ALL OF IT.
        self.assertEqual(
            [one for one in self.unwinding(made) if "unwound" not in one], [])
        self.assertFalse(os.path.lexists(self.destination))

    def test_an_appearing_entry_is_never_adopted(self):
        """A destination entry that appears under a name this copy is about to
        create is refused rather than written through or adopted."""
        os.makedirs(self.destination)
        with open(os.path.join(self.destination, "top.txt"), "w",
                  encoding="utf-8") as handle:
            handle.write("somebody got there first")
        made = {}
        with self.assertRaises(bootstrap.BootstrapRefusal) as raised:
            bootstrap.copy_runtime(self.source, self.destination, made=made)
        self.assertIn("nothing here follows a link or adopts an appearing "
                      "object", str(raised.exception))
        self.assertNotIn(self.destination, made)

    def test_a_source_that_is_not_a_directory_refuses(self):
        """THE OPEN IS THE CHECK, and the refusal asserted is the one that
        actually happens: `_runtime_source` opens the source `O_DIRECTORY`, so
        a file refuses there before anything is created. My first version
        asserted a second message from a branch that cannot be reached, and
        the branch is gone rather than the case."""
        place = os.path.join(self.home, "not-a-tree")
        with open(place, "w", encoding="utf-8") as handle:
            handle.write("a file")
        made = {}
        with self.assertRaises(bootstrap.BootstrapRefusal) as raised:
            bootstrap.copy_runtime(place, os.path.join(self.home, "to"),
                                   made=made)
        self.assertIn("NotADirectoryError", str(raised.exception))
        self.assertEqual(made, {})
        self.assertFalse(os.path.lexists(os.path.join(self.home, "to")))


class TheOwnershipRacesTheReviewReproduced(unittest.TestCase):
    """W376956 review 2026-10-28T23-50-44Z — both confirmed blockers.

    Blocker 1: the symlink branch did `symlink` then `lstat` and recorded
    whatever the name held by then, so a seam that replaced the new link with a
    foreign one in between made the ledger record the FOREIGN object -- and the
    unwind then deleted it and reported `unwound`.

    Blocker 2: the removal checked `lstat` identity and then resolved the
    PATHNAME again for `unlink`, so a seam that renamed the original aside and
    installed a foreign object at the name between those steps made the unwind
    delete the replacement and report success while the original survived.
    """

    def setUp(self):
        self.home = tempfile.mkdtemp(prefix="v12-ownership-")
        self.addCleanup(shutil.rmtree, self.home, ignore_errors=True)
        self.source = os.path.join(self.home, "source")
        os.makedirs(self.source)
        with open(os.path.join(self.source, "target"), "w",
                  encoding="utf-8") as handle:
            handle.write("a target")
        os.symlink("target", os.path.join(self.source, "link"))
        self.destination = os.path.join(self.home, "distro")

    # -- blocker 1 ----------------------------------------------------------

    def test_a_symlink_replaced_before_identity_capture_refuses(self):
        """THE SEAM THE REVIEW USED. The link this attempt created is replaced
        with a foreign one before the identity is taken; the copy must refuse
        rather than record the replacement, and the foreign link must survive.
        """
        real = os.symlink
        foreign = os.path.join(self.home, "foreign-target")
        with open(foreign, "w", encoding="utf-8") as handle:
            handle.write("not ours")

        def replacing(target, leaf, **named):
            real(target, leaf, **named)
            # The window: the name now holds OUR link, and somebody swaps it.
            os.unlink(leaf, dir_fd=named["dir_fd"])
            real(foreign, leaf, **named)

        made = {}
        with mock.patch.object(os, "symlink", replacing):
            with self.assertRaises(bootstrap.BootstrapRefusal) as raised:
                bootstrap.copy_runtime(self.source, self.destination,
                                       made=made)
        self.assertIn("creation identity is uncertain", str(raised.exception))
        # NOTHING FOREIGN IS OWNED: the ledger holds an UNCERTAIN effect for
        # that entry, which carries no deletion authority at all.
        held = made[os.path.join(self.destination, "link")]
        self.assertIsInstance(held, bootstrap._UncertainPrerequisite)
        said = bootstrap._remove_if_still_ours(
            os.path.join(self.destination, "link"), held, "runtime object")
        self.assertIn("no deletion authority", said)
        self.assertTrue(os.path.islink(os.path.join(self.destination, "link")))
        self.assertEqual(
            os.readlink(os.path.join(self.destination, "link")), foreign)

    def test_an_ordinary_symlink_is_proved_and_owned(self):
        """The counterpart, so the refusal above is not passing by accident."""
        made = {}
        bootstrap.copy_runtime(self.source, self.destination, made=made)
        held = made[os.path.join(self.destination, "link")]
        self.assertIsNotNone(getattr(held, "handle", None))
        self.assertEqual(tuple(held),
                         bootstrap._identity_of_handle(held.handle))
        said = [one for one in
                (bootstrap._remove_if_still_ours(place, made[place],
                                                 "runtime object")
                 for place in bootstrap.unwound_order(made)) if one]
        self.assertEqual([one for one in said if "unwound" not in one], [])

    # -- blocker 2 ----------------------------------------------------------

    def test_a_replacement_between_the_check_and_the_removal_is_reported(self):
        """THE WINDOW `unlinkat` CANNOT CLOSE, and what is done about it.

        No POSIX call removes a name BY INODE, so the gap between the
        parent-relative identity check and the parent-relative unlink cannot be
        eliminated. What can be done is to ask the RETAINED HANDLE afterwards:
        a removed object's link count reaches zero, so if this attempt's own
        object is still there, the name that went was somebody else's -- and
        that is REPORTED rather than counted as an unwind.
        """
        place = os.path.join(self.home, "ours")
        with open(place, "w", encoding="utf-8") as handle:
            handle.write("ours")
        pinned = os.open(place, os.O_PATH | os.O_NOFOLLOW | os.O_CLOEXEC)
        self.addCleanup(os.close, pinned)
        identity = bootstrap._OwnedCopy(
            bootstrap._identity_of_handle(pinned), "unused", pinned)
        # The seam: our object is renamed aside and a foreign one takes the
        # name, after the check this helper would have made.
        os.rename(place, os.path.join(self.home, "ours-moved"))
        with open(place, "w", encoding="utf-8") as handle:
            handle.write("somebody else's")
        parent = os.open(self.home, os.O_RDONLY | os.O_DIRECTORY
                         | os.O_CLOEXEC)
        self.addCleanup(os.close, parent)
        # W376956 review 2026-10-29T00-00-39Z: IT IS A STOP, NOT A SENTENCE.
        # The old helper RETURNED text claiming "nothing further is deleted"
        # while the install's unwind kept iterating; the review reproduced a
        # second owned file being removed straight after. It raises now, and
        # every iteration site handles it.
        with self.assertRaises(bootstrap._UnprovenRemoval) as raised:
            bootstrap._removed(place, "ours", parent, identity.handle,
                               identity, "runtime object")
        said = str(raised.exception)
        self.assertIn("was NOT the runtime object this attempt made", said)
        self.assertIn("no further removal is attempted", said)
        # AND THIS ATTEMPT'S OWN OBJECT IS UNTOUCHED.
        self.assertTrue(os.path.isfile(os.path.join(self.home, "ours-moved")))

    def test_a_replacement_before_the_removal_is_left_alone(self):
        """The ordinary case the parent-relative check catches outright: the
        name holds a different object by the time the unwind looks, so nothing
        is removed at all."""
        made = {}
        bootstrap.copy_runtime(self.source, self.destination, made=made)
        place = os.path.join(self.destination, "target")
        os.rename(place, os.path.join(self.home, "moved-aside"))
        with open(place, "w", encoding="utf-8") as handle:
            handle.write("a different object, same content")
        said = bootstrap._remove_if_still_ours(place, made[place],
                                               "runtime object")
        self.assertIn("belongs to whoever replaced it", said)
        self.assertTrue(os.path.isfile(place))
        self.assertTrue(os.path.isfile(os.path.join(self.home, "moved-aside")))

    def test_an_effect_with_no_retained_handle_has_no_deletion_authority(self):
        """A bare identity tuple cannot prove anything at the destructive
        call, so it is not permitted to make one."""
        place = os.path.join(self.home, "bare")
        with open(place, "w", encoding="utf-8") as handle:
            handle.write("bare")
        held = os.lstat(place)
        said = bootstrap._remove_if_still_ours(
            place, (held.st_dev, held.st_ino), "runtime object")
        self.assertIn("no retained handle", said)
        self.assertTrue(os.path.isfile(place))
