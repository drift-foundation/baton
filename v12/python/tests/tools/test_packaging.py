"""The REAL one-folder bundle, asked what it is. W183883.

EVERYTHING ELSE ABOUT THIS DELIVERY IS CHECKED AGAINST STAND-INS -- a directory
of ordinary files, a printing script -- because those checks are about the
CONTRACT and a stand-in makes them deterministic and fast. This module is the
opposite on purpose: it runs the bundle that `just build` produced, and it
exists because the stand-ins cannot see what only a real build has.

WHAT A REAL BUILD ALREADY CAUGHT, and what this now holds: the identity reported
`rpds.__file__`, which for a one-folder build names an `__init__.py` frozen into
the archive and NOT present on disk. Every stand-in said the bundle was fine;
the first real install refused it for reporting a native validator that is not
one of the files it binds. What has to have travelled is the compiled extension.

IT NEEDS A BUILD, and says so rather than passing quietly. `just test-packaging`
builds and then runs this; without a bundle it SKIPS with the exact command,
because a check that cannot be answered must not answer.
"""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

_DISTRIBUTION = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_DISTRIBUTION))
sys.path.insert(1, str(_DISTRIBUTION / "src"))
from tools import instance, stack_command

# Where `just build` puts it, and the one way to point somewhere else.
VARIABLE = "BATON_V12_STACK_DISTRO"
# And the way `just test-packaging` says "this run is the gate": a skip there
# would be exit 0 from the one check that cannot be stood in for.
REQUIRED = "BATON_V12_STACK_PACKAGING_REQUIRED"


def built():
    """The bundle to examine, or None."""
    named = os.environ.get(VARIABLE)
    place = Path(named) if named else _DISTRIBUTION / "build" / "out" / "distro"
    return place if (place / stack_command.COMMAND).exists() else None


class Fixture(unittest.TestCase):
    def setUp(self):
        self.distro = built()
        if self.distro is None:
            missing = (
                "no built runtime at "
                + str(Path(os.environ[VARIABLE]) if os.environ.get(VARIABLE)
                      else _DISTRIBUTION / "build/out/distro")
                + " -- run `just build` from v12/ (or `just test-packaging`, "
                "which builds and then runs this), or name one with "
                + VARIABLE + ". A bundle is the one thing these cases cannot "
                "stand in for.")
            if os.environ.get(REQUIRED):
                # THE GATE DOES NOT SKIP. `just test-packaging` builds and then
                # runs this; if the bundle it built is not the one being
                # examined, exit 0 with nine skips would report that the real
                # thing was checked when nothing was.
                self.fail(missing + " -- and " + REQUIRED + " is set, so this "
                          "run is the gate and a skip would be a false pass.")
            raise unittest.SkipTest(missing)
        self.command = self.distro / stack_command.COMMAND
        self.temp = tempfile.TemporaryDirectory(prefix="v12-packaging-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def ran(self, *operands, cwd="/"):
        """The bundle, run with NOTHING from this checkout in its environment.

        No PYTHONPATH, no BATON_V12_*, no virtual environment, and not from the
        distribution directory -- which is the whole claim an installed
        deployment makes.
        """
        return subprocess.run([str(self.command), *operands],
                              capture_output=True, text=True, timeout=300,
                              cwd=cwd, env={"HOME": str(self.root),
                                            "PATH": "/usr/bin:/bin"})


class WhatTheBundleSaysItIs(Fixture):
    def test_it_answers_for_itself_with_nothing_from_this_checkout(self):
        done = self.ran("identity")
        self.assertEqual(done.returncode, 0, done.stderr)
        said = json.loads(done.stdout)
        self.assertIs(said["frozen"], True)
        self.assertEqual(said["command"], stack_command.COMMAND)
        self.assertEqual(said["executable"], str(self.command.resolve()))

    def test_the_frozen_schema_assets_travelled(self):
        """`contracts.frozen` reads them at IMPORT time, so a bundle without
        them refuses every document later -- inside a child a supervisor has
        already started."""
        said = json.loads(self.ran("identity").stdout)
        assets = said["schema_assets"]
        self.assertEqual(sorted(assets), ["agent-session-1.0",
                                          "worker-control-1.0"])
        for name, length in assets.items():
            self.assertGreater(length, 0, name)

    def test_the_native_validator_is_ONE_OF_THE_FILES_THIS_BUNDLE_BINDS(self):
        """The defect a real build found. `rpds` has no pure-Python fallback,
        and `rpds.__file__` names an `__init__.py` that a one-folder build
        freezes into the archive -- so the identity reported a path that is not
        on disk and not in the manifest, while the extension beside it was."""
        said = json.loads(self.ran("identity").stdout)
        named = said["native_rpds"]
        self.assertTrue(os.path.isfile(named), named)
        held = instance.manifest(str(self.distro))
        inside = {os.path.realpath(os.path.join(str(self.distro), one))
                  for one in held["entries"]}
        self.assertIn(os.path.realpath(named), inside)

    def test_it_says_its_version_with_NO_checkout_and_NO_repository_tool(self):
        """OWNER-VERSION-STAMP-20260916.md: `--version` must answer where the
        development tree and the repository tool are both unavailable. The
        environment here has neither: PATH is a directory of nothing, and the
        command is run from `/`."""
        from baton_v12 import version as application

        nothing = self.root / "empty-path"
        nothing.mkdir(exist_ok=True)
        done = subprocess.run([str(self.command), "--version"],
                              capture_output=True, text=True, timeout=300,
                              cwd="/", env={"HOME": str(self.root),
                                            "PATH": str(nothing)})
        self.assertEqual(done.returncode, 0, done.stderr)
        said = done.stdout.strip()
        self.assertTrue(said.startswith("baton " + application.VERSION),
                        said)
        # AND IT IS THE CAPTURED STAMP, not a live read: there is nothing here
        # to read it from.
        self.assertNotIn("source commit unknown", said)

    def test_the_captured_stamp_is_the_one_the_build_recorded(self):
        """The final artifact must contain the same metadata the build
        recorded, which is what makes it provenance rather than decoration."""
        said = json.loads(self.ran("identity").stdout)
        stamp = said["build_stamp"]
        self.assertEqual(stamp["schema"], "baton.v12.build-stamp/1")
        self.assertEqual(said["version"], "12.0.0")
        held = json.loads(
            (self.distro / "_internal" / "build-stamp.json").read_bytes())
        self.assertEqual(held, stamp)
        # A dirty build is allowed and says which it was; unknown is not clean.
        self.assertIn(stamp.get("dirty"), (True, False, None))

    def test_an_unknown_subcommand_is_refused_by_name(self):
        done = self.ran("nonsense")
        self.assertEqual(done.returncode, 2)
        for verb in ("start", "stop", "status", "monitor", "bootstrap",
                     "manager", "view", "identity"):
            self.assertIn(verb, done.stderr, verb)

    def test_every_subcommand_this_command_serves_is_offered(self):
        done = self.ran("--help")
        self.assertEqual(done.returncode, 0, done.stderr)
        for verb in sorted(stack_command.COMMANDS):
            self.assertIn(verb, done.stdout, verb)


class WhatTheBundleIS(Fixture):
    """The manifest over a real bundle, and what an instance holds it to."""

    def copied(self):
        """A COPY, so nothing here can change the build under test."""
        destination = self.root / "deployment"
        places = instance.layout(str(destination))
        shutil.copytree(str(self.distro), places["distro"], symlinks=True)
        for name in ("stores", "repository", "logs", "state"):
            Path(places[name]).mkdir(parents=True, exist_ok=True)
        held = instance.manifest(places["distro"])
        document = instance.emit(str(destination), authority_uuid="0" * 31 + "a",
                                 identity=json.loads(self.ran("identity").stdout),
                                 runtime=held, now=1.0)
        instance.create(places["instance"], document)
        return places, document

    def test_a_real_bundle_digests_whole_and_verifies(self):
        places, document = self.copied()
        held = instance.verify(document)
        self.assertEqual(held["digest"], document["runtime"]["digest"])
        self.assertGreater(held["files"], 10)
        self.assertEqual(instance.read(places["instance"]), document)

    def test_one_changed_byte_in_a_real_library_is_refused(self):
        places, document = self.copied()
        library = sorted(Path(places["distro"], "_internal").glob("*.so*"))
        self.assertTrue(library, "a one-folder bundle carries shared libraries")
        held = library[0].read_bytes()
        library[0].write_bytes(held[:-1] + bytes([held[-1] ^ 0xFF]))
        with self.assertRaises(instance.InstanceRefusal) as raised:
            instance.verify(document)
        self.assertIn("not the one this instance was prepared with",
                      str(raised.exception))

    def test_an_unbound_extra_file_in_a_real_bundle_is_refused(self):
        places, document = self.copied()
        (Path(places["distro"]) / "_internal" / "nobody-recorded-this").write_text("x")
        with self.assertRaises(instance.InstanceRefusal):
            instance.verify(document)

    def test_the_copy_is_the_same_runtime_as_the_build(self):
        """`install` re-digests what it copied for exactly this reason."""
        places, _document = self.copied()
        self.assertEqual(instance.manifest(places["distro"])["digest"],
                         instance.manifest(str(self.distro))["digest"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
