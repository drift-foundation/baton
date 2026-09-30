"""The managed-correction packet, its commands and its bounds -- deterministically.

W236087 item 3, answering review 2026-09-29T21-08-40Z: "Validate generation/CLI
shapes deterministically without touching live roots/credentials" and "Focus
next verification on packet generation, commands and bounds."

SO THAT IS WHAT THESE ARE. No live root, no credential, no container, no engine
and no store of the selected instance is touched: every case builds its own
temporary directories, and the supervisor cases drive the real bounded loop with
a scripted clock and a scripted manager. What is exercised is the code an
operator would run.

WHAT IS SIMULATED AND WHERE. `TheBoundsAreEnforced` replaces four named
manager entry points (`submit`, `serve`, `sweep`, and the attempt/limit/cleanup
reads) with scripted stand-ins so the loop's ARITHMETIC and its stop conditions
are observable without a provider. The supervisor's own code is the code under
test; the manager beneath it is not, and its accepted behaviour is not
re-litigated here.
"""
import contextlib
import io
import json
import os
import re
import shlex
import sys
import tempfile
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:                                     # pragma: no cover
    sys.path.insert(0, HERE)

import correction_packet as packets                          # noqa: E402
import correction_supervisor as supervisor                    # noqa: E402
from correction_packet import PacketRefusal                   # noqa: E402

IMAGE = "sha256:" + "c8" * 32
ADAPTER = "sha256:" + "5f" * 32
POLICY = "sha256:" + "d3" * 32
PROFILE = "sha256:" + "93" * 32
OTHER = "sha256:" + "ab" * 32
# The Authority-qualified Work id a STAGE names, in the shape an
# installed instance records: a bare `W236087` is not one.
WORK_ID = "7ea319da-W236087"


def _write(path, body):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(body if isinstance(body, str)
                     else json.dumps(body, indent=2, sort_keys=True) + "\n")
    return path


def _read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def _expected_assets():
    """The frozen assets the PRODUCT declares, never a list retyped here."""
    from tools import bootstrap
    return tuple(bootstrap.EXPECTED_ASSETS)


ASSETS = _expected_assets()


class Fixture(unittest.TestCase):
    """One self-contained world per case, with nothing live in it."""

    def setUp(self):
        import tempfile

        self.root = tempfile.mkdtemp(prefix="correction-packet-")
        self.addCleanup(__import__("shutil").rmtree, self.root,
                        ignore_errors=True)
        self.instance = os.path.join(self.root, "instances",
                                     "managed-correction-test")
        # THE STAGED SOURCE DOES NOT SHARE A PARENT WITH THE INSTANCE, and
        # that is the layout rule claim 311743 measured rather than assumed:
        # `stage_execution._checkout()` answers three parents above its own
        # file, so `dirname(staging_root)` is the tree the staged code calls
        # its checkout, and `bootstrap.admit` refuses any instance inside it.
        self.staging = os.path.join(self.root, "staging-area", "staging")
        self.destination = os.path.join(self.root, "packet")
        self.source = os.path.join(self.root, "source")
        _write(os.path.join(self.source, "docs", "EXISTING.md"), "existing\n")
        self.distro = os.path.join(self.root, "distro")
        _write(os.path.join(self.distro, "baton-v12-stack"), "#!/bin/false\n")
        self.origin = os.path.join(self.root, "origin")
        _write(os.path.join(self.origin, "src", "baton_v12", "__init__.py"), "")
        _write(os.path.join(self.origin, "src", "baton_v12", "contracts",
                            "__init__.py"), "")
        # THE FIXTURE ORIGIN SHIPS WHAT THE DISTRIBUTION SHIPS. Owner report
        # 311736: the staged source carried modules and no frozen assets, and
        # `tools.bootstrap.EXPECTED_ASSETS` -- read here rather than retyped --
        # names the two schema files that are loaded at IMPORT time. A fixture
        # origin holding only modules could not have shown the defect.
        self.assets = {}
        for one in ASSETS:
            self.assets[one] = os.path.join(
                self.origin, "src", "baton_v12", "contracts", "schema",
                one + ".schema.json")
            _write(self.assets[one], '{"title": "' + one + '"}\n')
        # AND IT READS THEM AT IMPORT TIME, as the product does. The real
        # `baton_v12.contracts.frozen` resolves `__file__ / "schema"` and binds
        # the bytes to module-level constants, so a tree without them raises
        # before one document is read. A fixture whose modules imported happily
        # without their resources could not show owner report 311736 at all.
        _write(os.path.join(self.origin, "src", "baton_v12", "contracts",
                            "frozen.py"),
               "import pathlib\n"
               "_SCHEMA_DIRECTORY = pathlib.Path(__file__).resolve().parent"
               " / 'schema'\n"
               "def schema_bytes(name):\n"
               "    return (_SCHEMA_DIRECTORY / name).read_bytes()\n"
               "WORKER_CONTROL_BYTES = schema_bytes("
               "'worker-control-1.0.schema.json')\n"
               "AGENT_SESSION_BYTES = schema_bytes("
               "'agent-session-1.0.schema.json')\n")
        _write(os.path.join(self.origin, "tools", "__init__.py"), "")
        _write(os.path.join(self.origin, "tools", "bootstrap.py"),
               "SCHEMA = 'baton.v12.stack-bootstrap/1'\n"
               "EXPECTED_ASSETS = " + repr(ASSETS) + "\n")
        # AND THE CHECKOUT RULE AS THE PRODUCT COMPUTES IT: three parents above
        # this file. `tools.stage_execution._checkout` is what
        # `bootstrap.checkout` asks, and `bootstrap.admit` refuses a
        # destination inside its answer.
        _write(os.path.join(self.origin, "tools", "stage_execution.py"),
               "import os\n"
               "def operations_from(*a, **k):\n    return None\n"
               "def _checkout():\n"
               "    return os.path.realpath(os.path.join(\n"
               "        os.path.dirname(os.path.abspath(__file__)),\n"
               "        '..', '..', '..'))\n")
        self.provenance_record = _write(
            os.path.join(self.root, "IMAGE-ARTIFACT.json"),
            {"image": "baton-v12-claude-worker:test"})

    # -- the operands -------------------------------------------------------

    def profile(self, **changes):
        held = {
            "schema": "baton.claude-context-profile/2",
            "qualification": "candidate",
            "evidence_digest": "sha256:" + "16" * 32,
            "cli_build": "2.1.247",
            "image_digest": IMAGE,
            "adapter_digest": ADAPTER,
            "runtime_profile_digest": "sha256:" + "42" * 32,
            "argv_policy_digest": "sha256:" + "19" * 32,
            "environment_policy_digest": "sha256:" + "22" * 32,
            "layout_version": "claude-context-layout/2",
            "reported_model": "opus",
            "model": "opus",
            "cwd": "/output",
            "state_paths": [".claude/projects/-output/{conversation_id}.jsonl"],
            "max_entries": 4096,
            "max_bytes": 67108864,
            "retention_policy_digest": "sha256:" + "0f" * 32,
        }
        held.update(changes)
        return held

    def selections(self, **changes):
        held = {
            "schema": packets.SELECTIONS_SCHEMA,
            "run_id": "managed-correction-test",
            "work": "W236087",
            "instance_root": self.instance,
            "staging_root": self.staging,
            "source": {"root": self.source,
                       "declared_base": "a" * 40,
                       "files": ["docs/EXISTING.md"]},
            "manager_source_origin": self.origin,
            "manager_runtime": {"path": self.distro,
                                "executable_sha256": packets.digest_of(
                                    os.path.join(self.distro,
                                                 "baton-v12-stack")),
                                "build_commit": "1" * 40},
            "worker_image": {"reference": "baton-v12-claude-worker:test",
                             "config_digest": IMAGE,
                             "worker_files": {"opt/baton/claude_agent.py":
                                              "18" * 32},
                             "adapter_descriptor": ADAPTER,
                             "policy_descriptor": POLICY,
                             "profile_descriptor": PROFILE},
            "participants": {"implementation": "baton.claude",
                             "review": "baton.codxpc",
                             "integration": "baton.integrator"},
            "receipts": {"verification": "baton.verifier",
                         "review": "baton.approver-review",
                         "approval": "baton.approver"},
            "credential_reference": "claude-session/operator",
            "runtime_uid": 1000,
            "context_profile": self.profile(),
            "credential_delivery": {"provider": "operator-file",
                                    "slots": ["claude"],
                                    "sources": "/home/sl/.baton/"
                                               "credential-sources.json"},
            "review_route": {"implementation": "rview",
                             "review": "integration"},
            "context_storage": {
                "path": os.path.join(self.instance, "run", "private-contexts"),
                "excluded": [self.source,
                             os.path.join(self.instance, "run", "workspaces")]},
            "workspace_storage": os.path.join(self.instance, "run",
                                              "workspaces"),
            "stores": {
                "authority": os.path.join(self.instance, "db",
                                          "authority.sqlite3"),
                "job": os.path.join(self.instance, "db", "jobs.sqlite3"),
                "control": os.path.join(self.instance, "db",
                                        "control.sqlite3"),
                "integration": os.path.join(self.instance, "db",
                                            "integration.sqlite3"),
                "state_root": os.path.join(self.instance, "run",
                                           "deployment-state")},
        }
        held.update(changes)
        return _write(os.path.join(self.root, "selections.json"), held)

    def staged(self, **changes):
        """Selections, validated and staged. Returns (chosen, prepared)."""
        chosen = packets.held_selections(self.selections(**changes))
        return chosen, packets.stage(chosen, self.destination)

    def packet(self, **changes):
        """A complete packet on disk, as `bind` would emit one.

        `bind` reads the Authority identity and the emitted deployment
        configuration, so this writes the two documents the live instance would
        have left behind. NOTHING IS OPENED: they are files.
        """
        chosen, prepared = self.staged(**changes)
        _write(os.path.join(self.instance, "bootstrap.json"),
               {"authority_uuid": "7ea319da93384b77bc3ddea38602d7a3"})
        _write(os.path.join(self.instance, "deployment.json"),
               {"job_bindings": [{
                   "job_id": "job-managed-correction-test",
                   "job_work_id": WORK_ID,
                   "review_work_id": WORK_ID,
                   "source_worker_id": "implementation-worker"}],
                "workers": [{"worker_id": "w", "deployment": {
                    "workspace_storage": os.path.join(self.instance, "run",
                                                      "workspaces")}}]})
        with mock.patch.object(packets, "certified_digest",
                               return_value="sha256:" + "11" * 32):
            path = packets.bind(
                chosen, self.destination, claim=309356,
                provenance={"worker_image": {
                    "path": self.provenance_record,
                    "sha256": packets.digest_of(self.provenance_record)}},
                compatibility={
                    "adapter_source_sha256": "18" * 32,
                    "context_capable": True,
                    "established": ["the profile is composed against this "
                                    "image"],
                    "not_established": ["the production comparison"]})
        return chosen, path

    def edited(self, path, change):
        with open(path, "rb") as handle:
            held = json.loads(handle.read().decode("utf-8"))
        change(held)
        _write(path, held)
        return path


# -- generation -------------------------------------------------------------

class GenerationProducesRunnableInputs(Fixture):

    def test_the_documents_are_written_and_named(self):
        _chosen, prepared = self.staged()
        for name in ("bootstrap_inputs", "context_profile", "task"):
            self.assertTrue(os.path.exists(prepared[name]), name)
        self.assertEqual(prepared["job_id"], "job-managed-correction-test")

    def test_the_REAL_BOOTSTRAP_VALIDATOR_accepts_the_generated_document(self):
        """Review 2026-09-29T21-41-08Z R1 drove this and it refused: the
        supported schema is `baton.v12.stack-bootstrap/1`, not the
        `baton.v12.bootstrap-input/1` I invented. So the real validator is the
        test now.
        """
        from tools import bootstrap

        _chosen, prepared = self.staged()
        with open(prepared["bootstrap_inputs"], encoding="utf-8") as handle:
            document = json.load(handle)
        self.assertEqual(document["schema"], bootstrap.SCHEMA)
        bootstrap.held(document)                     # refuses, or this passes

    def test_a_FRESH_INSTALL_names_no_jobs_and_no_workers(self):
        """The tool keeps both out of an installation on purpose; naming them
        described a different act.
        """
        _chosen, prepared = self.staged()
        with open(prepared["bootstrap_inputs"], encoding="utf-8") as handle:
            document = json.load(handle)
        self.assertNotIn("jobs", document)
        self.assertNotIn("workers", document)
        self.assertNotIn("authority_uuid", document)

    def test_the_REAL_SUBMISSION_PARSER_accepts_the_generated_document(self):
        """R1: `read_submission` refused my first draft at its first member --
        "a job submission needs submission_id" -- because the whole shape was
        invented. This drives the real parser over the real bytes.
        """
        from baton_v12.job_manager import documents

        self.packet()
        with open(os.path.join(self.destination, "submission.json"),
                  encoding="utf-8") as handle:
            text = handle.read()
        owned = documents.read_submission(text)
        self.assertEqual(owned["schema"], documents.SUBMISSION_SCHEMA)
        self.assertEqual([one["kind"] for one in owned["jobs"][0]["stages"]],
                         ["implementation", "review"])

    def test_the_DECLARED_LIMITS_SURVIVE_the_real_parser(self):
        """A bound the parser drops is a bound this run does not have. The
        member names are the contract's -- `verification_command_seconds`, not
        the `verification_seconds` I invented -- and the schema must be `/2`,
        the only one that admits the member at all.
        """
        from baton_v12.job_manager import documents

        self.packet()
        with open(os.path.join(self.destination, "submission.json"),
                  encoding="utf-8") as handle:
            owned = documents.read_submission(handle.read())
        self.assertEqual(owned["jobs"][0]["execution_limits"],
                         {"provider_turn_seconds": 180,
                          "verification_command_seconds": 180})
        self.assertIn(documents.SUBMISSION_SCHEMA,
                      documents.SUBMISSION_LIMITS_SCHEMAS)

    def test_the_REVIEW_STAGE_DEPENDS_on_the_implementation(self):
        """How the real contract expresses ordering, rather than an order this
        packet asserts beside the document.
        """
        from baton_v12.job_manager import documents

        self.packet()
        with open(os.path.join(self.destination, "submission.json"),
                  encoding="utf-8") as handle:
            owned = documents.read_submission(handle.read())
        stages = {one["kind"]: one for one in owned["jobs"][0]["stages"]}
        self.assertEqual(stages["implementation"]["depends_on"], [])
        self.assertEqual(
            [(one["job_id"], one["kind"])
             for one in stages["review"]["depends_on"]],
            [("job-managed-correction-test", "implementation")])

    def test_the_TASK_DOCUMENT_carries_the_complete_criteria_as_ITS_BYTES(self):
        """R1: the submission contract has no task and no acceptance text --
        `STAGE_MEMBERS` is kind, work_id, profile_name, profile_digest,
        depends_on -- so the criteria reach the worker through the task
        document, which is the manifest's human contract.
        """
        _chosen, prepared = self.staged()
        with open(prepared["task"], encoding="utf-8") as handle:
            task = json.load(handle)
        self.assertEqual(task["schema"], packets.TASK_SCHEMA)
        self.assertEqual(task["declared_base"], "a" * 40)
        for one in packets.CRITERIA:
            self.assertIn(one, task["instructions"])
        self.assertIn(packets.TASK_PATH, task["instructions"])
        self.assertIn("JUDGING IS NOT THIS STAGE", task["instructions"])

    def test_the_TASK_BYTES_are_the_manifest_s_human_contract(self):
        """What makes "the same complete criteria reached the worker" a
        checkable fact: `single_worker._held` compares the worker's task.json
        against this digest, so the two are derived together.
        """
        import hashlib

        self.packet()
        with open(os.path.join(self.destination, "task.json"), "rb") as handle:
            raw = handle.read()
        with open(os.path.join(self.destination, "input-manifest.json"),
                  encoding="utf-8") as handle:
            manifest = json.load(handle)
        self.assertEqual(manifest["human_contract"]["content_digest"],
                         "sha256:" + hashlib.sha256(raw).hexdigest())
        self.assertEqual(manifest["human_contract"]["bytes"], len(raw))

    def test_the_INPUT_DIGEST_is_the_PRODUCT_S_derivation(self):
        """Not a hash this module chose: `job_input_identity` owns its operand
        and refuses a manifest that is not an input one.
        """
        from baton_v12.contracts import job_input_identity
        from baton_v12.job_manager import documents

        self.packet()
        with open(os.path.join(self.destination, "input-manifest.json"),
                  encoding="utf-8") as handle:
            manifest = json.load(handle)
        with open(os.path.join(self.destination, "submission.json"),
                  encoding="utf-8") as handle:
            owned = documents.read_submission(handle.read())
        self.assertEqual(owned["jobs"][0]["input_digest"],
                         job_input_identity(manifest))

    def test_the_MEASURED_DESCRIPTORS_come_from_the_accepted_record(self):
        """My first draft hashed strings of its own making and called them
        policy digests. These are `prepare_two_jobs.ACCEPTED`'s, each measured
        from an accepted record.
        """
        accepted = packets._accepted()
        _chosen, prepared = self.staged()
        with open(prepared["bootstrap_inputs"], encoding="utf-8") as handle:
            document = json.load(handle)
        # THE RETENTION IDENTITY IS THE PROFILE'S, not the accepted record's:
        # one identity across profile, workers and composition, because the
        # finalizer and the ending look a cleanup up under different ones and a
        # split left the context use held as `custody-invalid`.
        self.assertEqual(document["retention_policy_digest"],
                         self.profile()["retention_policy_digest"])
        self.assertEqual(document["checkpoint_profile"],
                         accepted["checkpoint_profile"])
        # THE INTEGRATOR IS THE SELECTION'S, and the rest of the profile is the
        # accepted record's: the Authority refused a composition naming an
        # integrator it had granted nothing to.
        self.assertEqual(
            document["integration_profile"],
            dict(accepted["integration_profile"],
                 integrator_participant="baton.integrator"))
        self.assertIsInstance(
            document["integration_profile"]["profile_version"], int)

    def test_the_staged_source_is_COPIED_and_measured_from_the_copy(self):
        _chosen, prepared = self.staged()
        held = prepared["staged_source"]
        self.assertEqual(held["file_count"], len(held["files"]))
        self.assertIn("tools/stage_execution.py", held["files"])
        self.assertIn("src/baton_v12/__init__.py", held["files"])
        for name, expected in held["files"].items():
            self.assertEqual(
                packets.digest_of(os.path.join(held["path"], name)), expected)

    def test_the_staged_source_carries_the_FROZEN_ASSETS_it_will_import(self):
        """OWNER REPORT 311736, and the defect that report names.

        `_source_files` staged only `.py`, so the bundle reached the operator
        without `src/baton_v12/contracts/schema/worker-control-1.0.schema.json`.
        `tools.bootstrap.EXPECTED_ASSETS` declares it and the tool reads it at
        IMPORT time, so bootstrap refused, and `prepare-work`, `bind` and
        `check` then failed for want of documents bootstrap never wrote.
        """
        _chosen, prepared = self.staged()
        held = prepared["staged_source"]
        self.assertEqual(held["frozen_assets"], sorted(ASSETS))
        for one in ASSETS:
            name = ("src/baton_v12/contracts/schema/" + one + ".schema.json")
            self.assertEqual(
                packets.asset_locations(
                    packets.staged_report(held["path"]))[one], name)
            self.assertIn(name, held["files"], one)
            whole = os.path.join(held["path"], name)
            self.assertTrue(os.path.isfile(whole), whole)
            # MEASURED, not merely present: the asset is digested with every
            # other staged file, so a changed asset is drift `bind` refuses.
            self.assertEqual(packets.digest_of(whole), held["files"][name])
            self.assertEqual(_read(whole), _read(self.assets[one]))

    def test_a_MODULE_ONLY_origin_is_refused_by_the_NAME_of_what_is_absent(self):
        """The failure the owner met was an installer failure several steps
        after the cause. It is refused at the copy now, and the refusal names
        the files -- because `missing asset` without a path is what made the
        original report expensive to act on.
        """
        for one in self.assets.values():
            os.unlink(one)
        with self.assertRaises(packets.PacketRefusal) as raised:
            self.staged()
        said = str(raised.exception)
        # THE OWNER'S FAILURE, WORD FOR WORD IN KIND: an import that cannot
        # read its frozen document, named where the copy is made rather than
        # met at the installer. Only the asset the loader reached is named,
        # because that is where the interpreter stopped -- and one is enough,
        # since the message carries the path, the module and the cause.
        self.assertIn("DOES NOT IMPORT", said)
        self.assertIn("FileNotFoundError", said)
        self.assertIn("baton_v12.contracts.frozen", said)
        self.assertIn("module level", said)
        self.assertIn("bootstrap failure several steps after the cause", said)
        self.assertTrue(
            any(one + ".schema.json" in said for one in ASSETS), said)

    def test_ONE_absent_asset_is_enough_to_refuse(self):
        """A bundle with one of two assets refuses every document it is given
        just as surely as a bundle with none.
        """
        one = "agent-session-1.0"
        self.assertIn(one, ASSETS)
        os.unlink(self.assets[one])
        with self.assertRaises(packets.PacketRefusal) as raised:
            self.staged()
        said = str(raised.exception)
        self.assertIn(one + ".schema.json", said)
        self.assertIn("DOES NOT IMPORT", said)

    def test_a_BOUND_packet_whose_source_lost_an_asset_is_refused(self):
        """`check` reads the packet the operator will run. A source that cannot
        import must be refused before a store is opened, not at the installer.
        """
        _chosen, path = self.packet()
        held = packets.held_packet(path)
        self.assertEqual(held["schema"], packets.PACKET_SCHEMA)
        absent = os.path.join(held["manager_source"]["path"], "src",
                              "baton_v12", "contracts", "schema",
                              "worker-control-1.0.schema.json")
        self.assertTrue(os.path.isfile(absent))
        os.unlink(absent)
        with self.assertRaises(packets.PacketRefusal) as raised:
            packets.held_packet(path)
        said = str(raised.exception)
        self.assertIn("worker-control-1.0.schema.json", said)

    def test_BUILD_OUTPUT_and_SCRATCH_RUN_TREES_are_NOT_staged(self):
        """The correction I wrote FIRST was `everything but derived`, and
        measuring it against the real origin showed it staging a PyInstaller
        bundle under `build/out/distro`, a `.pytest_cache` and 44
        `v12-w71917-*` scratch run directories -- 2874 files and 132M of build
        output and run state copied into a source bundle. Staging is by
        DECLARATION now (`IMPORTED_PACKAGES` where it lives under the import
        roots), so this case holds that narrower rule against exactly those
        trees.
        """
        _write(os.path.join(self.origin, "build", "lib", "baton_v12",
                            "__init__.py"), "")
        _write(os.path.join(self.origin, "build", "out", "distro",
                            "_internal", "base_library.zip"), "not a source\n")
        _write(os.path.join(self.origin, ".pytest_cache", "v", "cache",
                            "lastfailed"), "{}\n")
        _write(os.path.join(self.origin, "v12-w71917-scratch",
                            "control.sqlite3"), "not a source\n")
        _write(os.path.join(self.origin, "v12-w71917-scratch", "tools",
                            "bootstrap.py"), "raise SystemExit\n")
        _write(os.path.join(self.origin, "src", "baton_v12.egg-info",
                            "PKG-INFO"), "Name: baton-v12\n")
        _chosen, prepared = self.staged()
        staged = prepared["staged_source"]
        for name in staged["files"]:
            self.assertTrue(
                name.startswith(("src/baton_v12/", "tools/")), name)
            self.assertNotIn("egg-info", name)
        self.assertEqual(
            sorted({name.split("/")[0] for name in staged["files"]}),
            ["src", "tools"])
        # AND THE BYTES ARE NOT ON DISK EITHER, which is the claim that matters:
        # a name absent from the manifest but present in the tree would still be
        # importable by the run.
        for absent in ("build", ".pytest_cache", "v12-w71917-scratch"):
            self.assertFalse(
                os.path.exists(os.path.join(staged["path"], absent)), absent)

    def test_a_staging_root_holding_an_EARLIER_STAGING_is_refused_not_tidied(self):
        """THE OWNER'S PARTIAL PREPARATION, measured read-only under claim
        311743: `<staging_root>/manager-source` holds 376 `.py` files and no
        resource -- `build/lib`, `tests/` and 44 `v12-w71917-*` scratch run
        trees, because the old walk followed the `.` root into everything beside
        the packages. Staging the CORRECTED 108 over that tree would leave 268
        files no digest binds, on a `PYTHONPATH`, in a packet whose whole
        promise is that the run executes the reviewed bytes.

        It is refused, and NOTHING IS DELETED: this program did not write those
        files and they may be someone's evidence. The recovery is a fresh
        staging root.
        """
        chosen, prepared = self.staged()
        staged = prepared["staged_source"]["path"]
        earlier = os.path.join(staged, "v12-w71917-scratch", "tools",
                               "bootstrap.py")
        _write(earlier, "raise SystemExit('not the reviewed bytes')\n")
        stale = os.path.join(staged, "build", "lib", "baton_v12",
                             "__init__.py")
        _write(stale, "")
        with self.assertRaises(packets.PacketRefusal) as raised:
            packets.staged_source(self.origin, staged)
        said = str(raised.exception)
        self.assertIn("2 file(s)", said)
        self.assertIn("no digest binds", said)
        self.assertIn("FRESH `staging_root`", said)
        # NOT TIDIED UP.
        self.assertTrue(os.path.isfile(earlier))
        self.assertTrue(os.path.isfile(stale))

    def test_STAGING_THE_SAME_TREE_AGAIN_is_not_drift(self):
        """The other half: an idempotent replay of the same staging is not an
        unbound file, or the refusal above would make `stage` unrepeatable.
        """
        _chosen, prepared = self.staged()
        staged = prepared["staged_source"]["path"]
        again = packets.staged_source(self.origin, staged)
        self.assertEqual(again["files"], prepared["staged_source"]["files"])
        self.assertEqual(again["frozen_assets"],
                         prepared["staged_source"]["frozen_assets"])

    def test_an_INSTANCE_INSIDE_THE_STAGED_CODES_CHECKOUT_is_refused(self):
        """THE DEFECT THE DELIVERED PLAN ACTUALLY CARRIED, found by running the
        real `tools.bootstrap` from a real staged tree under claim 311743.

        `stage_execution._checkout()` answers three parents above its own file,
        so a source staged at `<staging_root>/manager-source` makes
        `dirname(staging_root)` the checkout -- and `bootstrap.admit` refuses
        any destination inside it, because an installed instance exists so that
        development in the code's own tree cannot change a running Job. The
        delivered selection put the staged source at
        `/home/sl/baton-instances/managed-correction-309356-source` and the
        instance at `/home/sl/baton-instances/managed-correction-309356`:
        siblings, so step 1 could not have succeeded whatever the assets did.
        The asset failure came first, which is the only reason it went unseen.

        It is refused at `stage` now, with the layout the operator must choose.
        """
        sibling = os.path.join(self.root, "side-by-side")
        with self.assertRaises(packets.PacketRefusal) as raised:
            self.staged(instance_root=os.path.join(sibling, "instances",
                                                   "managed-correction-test"),
                        staging_root=os.path.join(sibling, "staging"))
        said = str(raised.exception)
        self.assertIn("INSIDE the", said)
        self.assertIn("checkout", said)
        self.assertIn("`staging_root` whose PARENT does not contain", said)

    def test_the_DELIVERED_LAYOUT_keeps_the_instance_outside_the_checkout(self):
        """The positive half, and the recovery this turn delivers: the staged
        source's PARENT holds no instance, so the checkout the staged code
        answers cannot contain one.
        """
        _chosen, prepared = self.staged()
        staged = prepared["staged_source"]
        tree = staged["checkout"]
        self.assertTrue(tree)
        self.assertEqual(tree, os.path.realpath(
            os.path.dirname(self.staging)))
        instance = os.path.realpath(self.instance)
        self.assertFalse(instance.startswith(tree.rstrip("/") + os.sep),
                         (instance, tree))

    def test_a_changed_ORIGIN_does_not_change_the_staged_bytes(self):
        """The whole point of staging: the reviewed bytes stop moving."""
        _chosen, prepared = self.staged()
        staged = prepared["staged_source"]
        before = dict(staged["files"])
        _write(os.path.join(self.origin, "tools", "stage_execution.py"),
               "def operations_from(*a, **k):\n    return 'different'\n")
        after = {name: packets.digest_of(os.path.join(staged["path"], name))
                 for name in before}
        self.assertEqual(before, after)

    def test_EVERY_EXECUTABLE_DEPENDENCY_is_bound_including_the_supplier(self):
        """R4, and review 2026-09-29T22-02-59Z item 4: the two programs the run
        imports lived outside the staged packages and were bound by nothing --
        and so did the SIBLING DOSSIER'S DESCRIPTOR SUPPLIER, whose digest the
        candidate merely noted. A note is not an execution check.
        """
        _chosen, prepared = self.staged()
        held = prepared["preparation_modules"]
        self.assertEqual(
            sorted(held),
            ["correction_packet.py", "correction_supervisor.py",
             "finding-v12-real-jobs-adoption-gate/prepare_two_jobs.py"])
        for name, expected in held.items():
            whole = packets._helper_modules()[name]
            self.assertEqual(packets.digest_of(whole), expected, name)


class TheWORKERSAreProvedByTheProgramThatReadsThem(Fixture):
    """Review 2026-09-29T22-02-59Z item 1.

    The previous claim generated NO worker at all, so nothing established that
    the selected source, the worker profiles, the credential reference and the
    task reach the real deployment. These drive `single_worker._held` -- the
    preflight the composition itself runs -- at the generated configurations, in
    disposable fixtures, with no instance installed and no engine or provider
    reached.

    THE REAL PREFLIGHT FOUND THREE FAULTS while this was being written, and each
    one is a fact I had wrong: the worker's `profile_digest` must be the
    manifest's `runtime_profile_digest` ("names another runtime profile"), its
    `image_digest` must be the manifest's `worker_image_digest` ("names another
    worker image"), and a context implementation worker must declare the
    reserved receipt output ("required context receipt declaration is missing").
    """

    def _workers(self):
        self.packet()
        with open(os.path.join(self.destination, "deployment.json"),
                  encoding="utf-8") as handle:
            composed = json.load(handle)
        return composed, {one["worker_id"]: one["deployment"]
                          for one in composed["workers"]}

    def test_BOTH_generated_workers_pass_the_REAL_preflight(self):
        composed, workers = self._workers()
        proved = packets.verify_workers(workers)
        self.assertEqual(sorted(proved), ["implementation-worker",
                                          "review-worker"])
        self.assertEqual(composed["schema"], packets.DEPLOYMENT_SCHEMA)

    def test_the_PRODUCER_carries_the_context_and_the_REVIEWER_cannot(self):
        """The custody rule as two SCHEMAS rather than a sentence: `_held`
        admits `provider_context` only for `/5`, so a `/4` reviewer is
        structurally incapable of being handed the producer's conversation.
        """
        _composed, workers = self._workers()
        producer = workers["implementation-worker"]
        reviewer = workers["review-worker"]
        self.assertEqual(producer["schema"], packets.PRODUCER_SCHEMA)
        self.assertEqual(reviewer["schema"], packets.REVIEWER_SCHEMA)
        self.assertEqual(producer["provider_context"]["mode"], "required")
        self.assertNotIn("provider_context", reviewer)
        self.assertNotEqual(producer["credential_home"],
                            reviewer["credential_home"])
        self.assertNotEqual(producer["principal"], reviewer["principal"])

    def test_a_REVIEWER_HANDED_A_CONTEXT_is_refused_BY_THE_BUILD(self):
        """The structural guarantee, demonstrated rather than asserted: the real
        preflight answers "unexpected provider_context" for a `/4` document,
        because the member is not in its schema at all.
        """
        _composed, workers = self._workers()
        workers["review-worker"]["provider_context"] = dict(
            workers["implementation-worker"]["provider_context"])
        with self.assertRaises(PacketRefusal) as raised:
            packets.verify_workers(workers)
        self.assertIn("unexpected provider_context", str(raised.exception))

    def test_a_REVIEWER_PROMOTED_TO_THE_CONTEXT_SCHEMA_is_still_refused(self):
        """And the custody check is the second line: a reviewer whose SCHEMA was
        also flipped passes the member walk, so this packet refuses it by name.
        `_held` itself refuses it too -- "required provider context is retained
        implementation only" -- and either refusal is the correct answer; what
        matters is that no path admits it.
        """
        _composed, workers = self._workers()
        workers["review-worker"]["schema"] = packets.PRODUCER_SCHEMA
        workers["review-worker"]["provider_context"] = dict(
            workers["implementation-worker"]["provider_context"])
        with self.assertRaises(PacketRefusal) as raised:
            packets.verify_workers(workers)
        said = str(raised.exception)
        self.assertTrue("implementation only" in said
                        or "must not do" in said, said)

    def test_a_PRODUCER_WITHOUT_THE_RECEIPT_DECLARATION_is_refused(self):
        """By the REAL preflight, not by a rule this packet restates."""
        _composed, workers = self._workers()
        producer = workers["implementation-worker"]
        manifest = dict(producer["input_manifest"])
        manifest["outputs"] = [one for one in manifest["outputs"]
                               if one["name"] != "provider-context-receipt"]
        producer["input_manifest"] = packets.with_context_receipt(manifest)
        producer["input_manifest"]["outputs"] = [
            one for one in producer["input_manifest"]["outputs"]
            if one["name"] != "provider-context-receipt"]
        from baton_v12.contracts import digest

        held = dict(producer["input_manifest"])
        held.pop("manifest_digest")
        producer["input_manifest"]["manifest_digest"] = digest(held)
        with self.assertRaises(PacketRefusal) as raised:
            packets.verify_workers(workers)
        self.assertIn("context receipt declaration", str(raised.exception))

    def test_an_OPTIONAL_context_is_refused_for_this_run(self):
        """A run whose context silently did not attach would answer the provider
        question with a fresh session and look like a success.
        """
        _composed, workers = self._workers()
        workers["implementation-worker"]["provider_context"]["mode"] = \
            "optional"
        with self.assertRaises(PacketRefusal) as raised:
            packets.verify_workers(workers)
        self.assertIn("required provider context", str(raised.exception))

    def test_the_CREDENTIAL_REFERENCE_travels_and_NO_BYTES_DO(self):
        _composed, workers = self._workers()
        for name, held in workers.items():
            with self.subTest(worker=name):
                self.assertEqual(held["credential_profile"]["claude"],
                                 {"provider": "operator-file",
                                  "reference": "claude-session/operator"})
                self.assertEqual(held["credential_slots"], ["claude"])
                # THE REGISTRY IS A PATH, never its contents.
                self.assertTrue(os.path.isabs(held["credential_sources"]))
                self.assertNotIn("secret", json.dumps(held).lower())
                self.assertNotIn("token", json.dumps(held).lower())

    def test_the_NOMINATED_SOURCE_is_the_SELECTED_source(self):
        _composed, workers = self._workers()
        for held in workers.values():
            self.assertEqual(held["nominated_source"], self.source)

    def test_the_TASK_reaches_BOTH_workers_as_the_SAME_human_contract(self):
        """What "the same complete requirements reached both parties" means once
        it is a deployment fact: `_held` compares each worker's `task_document`
        bytes against its own manifest's human contract, and both workers are
        handed the same document.
        """
        _composed, workers = self._workers()
        task = os.path.join(self.destination, "task.json")
        digests = set()
        for held in workers.values():
            self.assertEqual(held["task_document"], task)
            digests.add(held["input_manifest"]["human_contract"]
                        ["content_digest"])
        self.assertEqual(len(digests), 1)

    def test_BOTH_manifests_yield_ONE_Job_input_identity(self):
        """Two workers, two `manifest_digest` values, ONE job input identity --
        which is why `outputs` must agree and does.
        """
        from baton_v12.contracts import job_input_identity
        from baton_v12.job_manager import documents

        _composed, workers = self._workers()
        held = {job_input_identity(one["input_manifest"])
                for one in workers.values()}
        self.assertEqual(len(held), 1)
        with open(os.path.join(self.destination, "submission.json"),
                  encoding="utf-8") as handle:
            owned = documents.read_submission(handle.read())
        self.assertEqual(owned["jobs"][0]["input_digest"], held.pop())

    def test_the_DEPLOYMENT_binds_this_Job_to_this_Work_and_base(self):
        """ONE JOB THROUGH THE DOCUMENT'S OWN MEMBERS, and no `job_bindings`:
        the enclosing validator refused the first generated composition for
        carrying both ("two places for one fact is how they drift").
        """
        composed, _workers = self._workers()
        self.assertNotIn("job_bindings", composed)
        self.assertEqual(composed["job_work_id"], WORK_ID)
        self.assertEqual(composed["review_work_id"], WORK_ID)
        self.assertEqual(composed["line_declared_base"], "a" * 40)
        self.assertEqual(composed["canonical_target_id"], "a" * 40)
        self.assertEqual(composed["state_root"],
                         os.path.join(self.instance, "run",
                                      "deployment-state"))

    def test_the_ENCLOSING_VALIDATOR_is_driven_at_the_composition(self):
        """Review 2026-09-29T22-15-01Z: worker validity alone proves nothing
        about the composition around them. `held_configuration` is the reading
        the serving process performs, and `held_packet` drives it.
        """
        composed, _workers = self._workers()
        packets.verify_composition(
            composed, checkout=os.path.join(self.staging, "manager-source"))
        with self.assertRaises(PacketRefusal) as raised:
            packets.verify_composition(composed, checkout=self.root)
        self.assertIn("not one this build composes", str(raised.exception))
        self.assertIn("belongs outside the working tree", str(raised.exception))

    def test_a_DRIFTED_COMPOSITION_refuses_the_packet(self):
        """The composition IS `deployment.config_path`, so drift in it is
        refused by that pin -- one file, one digest, one place."""
        _composed, _workers = self._workers()
        path = os.path.join(self.destination, "deployment.json")
        self.edited(path, lambda held: held["workers"].pop())
        with self.assertRaises(PacketRefusal) as raised:
            packets.held_packet(os.path.join(self.destination, "packet.json"))
        self.assertIn("deployment configuration", str(raised.exception))

    def test_a_COMPOSITION_MISSING_A_WORKER_refuses_the_packet(self):
        """Re-pinned so the bytes check passes and the SHAPE check is what
        answers: one producer and one independent reviewer, or no run.
        """
        _composed, _workers = self._workers()
        path = os.path.join(self.destination, "deployment.json")
        packet = os.path.join(self.destination, "packet.json")
        self.edited(path, lambda held: held.__setitem__(
            "workers", [one for one in held["workers"]
                        if one["worker_id"] != "review-worker"]))
        self.edited(packet, lambda held: held["deployment"].__setitem__(
            "config_sha256", packets.digest_of(path)))
        self.edited(packet, lambda held: held["composition"].__setitem__(
            "workers", ["implementation-worker"]))
        with self.assertRaises(PacketRefusal) as raised:
            packets.held_packet(packet)
        self.assertIn("one independent reviewer", str(raised.exception))

    def test_the_PACKET_PROOF_drives_the_preflight_itself(self):
        """`check` opens no store and still refuses a composition this build
        would not compose -- which is the difference between pinning bytes and
        proving a deployment.
        """
        _composed, _workers = self._workers()
        path = os.path.join(self.destination, "deployment.json")
        packet = os.path.join(self.destination, "packet.json")
        self.edited(path, lambda held: held["workers"][0]["deployment"]
                    .__setitem__("network", "not a valid network name!!"))
        self.edited(packet, lambda held: held["deployment"].__setitem__(
            "config_sha256", packets.digest_of(path)))
        with self.assertRaises(PacketRefusal) as raised:
            packets.held_packet(packet)
        self.assertIn("not one this build accepts", str(raised.exception))

    def test_HELD_PACKET_drives_the_ENCLOSING_validator_after_bind(self):
        """A fault ONLY the enclosing reading catches, introduced after `bind`
        and re-pinned so the bytes check passes.

        `job_bindings` beside the document's own Job members is invisible to
        each worker's preflight and refused by `held_configuration` -- "two
        places for one fact is how they drift" -- so this proves `held_packet`
        really drives it rather than relying on `bind` having done so.
        """
        _composed, _workers = self._workers()
        path = os.path.join(self.destination, "deployment.json")
        packet = os.path.join(self.destination, "packet.json")
        self.edited(path, lambda held: held.__setitem__(
            "job_bindings", [{"job_id": "job-managed-correction-test",
                              "job_work_id": WORK_ID,
                              "review_work_id": WORK_ID,
                              "line_declared_base": "a" * 40,
                              "canonical_target_id": "a" * 40,
                              "source_worker_id": "implementation-worker"}]))
        self.edited(packet, lambda held: held["deployment"].__setitem__(
            "config_sha256", packets.digest_of(path)))
        with self.assertRaises(PacketRefusal) as raised:
            packets.held_packet(packet)
        self.assertIn("names no job_bindings", str(raised.exception))

    def test_the_PRODUCER_S_CONTEXT_STORAGE_is_this_run_s_own(self):
        _composed, workers = self._workers()
        storage = workers["implementation-worker"]["provider_context"]["storage"]
        self.assertEqual(storage, os.path.join(self.instance, "run",
                                               "private-contexts"))


class ThePREPARE_WORK_CLI(Fixture):
    """The ACTUAL CLI operand path, against a genuinely absent Work.

    Review 2026-09-29T23-28-53Z R1: the CLI used a generator that produced an
    identity `authority.identity.check_work_id` refuses, and the connected
    harness passed an EXISTING fixture Work -- so the fresh path was never
    exercised. These drive `correction_packet.main(["prepare-work", ...])`
    against a DISPOSABLE Authority this case creates, where the Work is absent
    until the CLI creates it.

    NO DEPLOYED STORE IS TOUCHED. `Authority.create` makes a new store under this
    case's own temporary root, and it is removed with it.
    """

    def authority(self):
        """A fresh disposable Authority at the path the installer would use."""
        from baton_v12.authority import Authority

        installed = packets.installed_layout(self.instance)
        os.makedirs(os.path.dirname(installed["authority_store"]),
                    exist_ok=True)
        # The identity a real installation would have minted, generated here
        # because this case installs nothing: 32 hex characters.
        import uuid as _uuid

        identity = _uuid.uuid4().hex
        held = Authority.create(installed["authority_store"],
                                authority_uuid=identity)
        held.dispose()
        uuid = identity
        _write(installed["record"], {"authority_uuid": uuid})
        _write(installed["configuration"], {"job_bindings": []})
        return installed, uuid

    def test_the_CLI_creates_a_previously_ABSENT_Work_then_REPLAYS(self):
        installed, uuid = self.authority()
        selections = self.selections()
        stream = io.StringIO()
        self.assertEqual(packets.main(
            ["prepare-work", "--selections", selections,
             "--destination", self.destination], stream=stream), 0)
        first = json.loads(stream.getvalue())
        # THE IDENTITY IS THE QUALIFIED ONE, and the Authority accepted it.
        self.assertEqual(first["work_id"], uuid[:8] + "-W236087")
        self.assertIs(first["created"], True)
        self.assertEqual(sorted(first["route_handlers"]),
                         ["impl", "integration", "rview"])
        self.assertEqual(
            sorted(one["capability"] for one in first["granted"]),
            ["approve", "integrate", "review", "verify"])
        self.assertEqual(first["canonical_target"], "a" * 40)
        self.assertTrue(os.path.exists(
            os.path.join(self.destination, "prepared-work.json")))

        # AND THE EXACT REPLAY: the same command again answers the same Work and
        # reports the creation as a replay rather than a second act.
        stream = io.StringIO()
        self.assertEqual(packets.main(
            ["prepare-work", "--selections", selections,
             "--destination", self.destination], stream=stream), 0)
        again = json.loads(stream.getvalue())
        self.assertEqual(again["work_id"], first["work_id"])
        self.assertEqual(again["scope"], first["scope"])
        self.assertIs(again["created"], False)

    def test_an_INVALID_work_selector_is_refused_by_the_REAL_checker(self):
        """`W` followed by a positive number, or no preparation: the previous
        generator composed the RUN ID into the name and the Authority refused it.
        """
        for said in ("managed-correction-309356", "W", "W0", "W-1", "Wabc",
                     "0000000a-W1"):
            with self.subTest(work=said):
                with self.assertRaises(PacketRefusal) as raised:
                    packets.held_selections(self.selections(work=said))
                self.assertIn("LOCAL selector", str(raised.exception))

    def granted(self, installed, uuid):
        """Every capability grant and the canonical target, read back.

        The refusal cases below assert that a refused preparation changed
        NOTHING, and "nothing" has to be measured rather than assumed.
        """
        from baton_v12.authority import Authority

        held = Authority.open(installed["authority_store"],
                              expected_authority_uuid=uuid)
        try:
            # `capabilities_of` is the supported per-participant reader; the
            # four receipt writers this preparation grants to are the ones to
            # ask, so "nothing changed" is measured rather than assumed.
            who = ("baton.verifier", "baton.approver-review",
                   "baton.approver", "baton.integrator",
                   "baton.claude", "baton.codxpc", "baton.somebody-else",
                   "baton.other")
            return {"target": held.policy("canonical_target"),
                    "capabilities": {one: sorted(held.capabilities_of(one))
                                     for one in who}}
        finally:
            held.dispose()

    def test_an_UNRELATED_same_contract_Work_is_REFUSED_not_adopted(self):
        """Review 2026-09-29T23-40-17Z R1, the reviewer's own reproduction: a
        Work of this name created by ANOTHER act under the ordinary
        `v12-assignment-1` contract was ADOPTED, and four capabilities were then
        granted in its unrelated scope. A common assignment contract is not
        preparation identity.
        """
        from baton_v12.authority import Authority

        installed, uuid = self.authority()
        held = Authority.open(installed["authority_store"],
                              expected_authority_uuid=uuid)
        try:
            held.create_work(uuid[:8] + "-W236087", "impl",
                             contract="v12-assignment-1",
                             operation_id="unrelated-original-creation")
        finally:
            held.dispose()
        before = self.granted(installed, uuid)
        with self.assertRaises(PacketRefusal) as raised:
            packets.main(["prepare-work", "--selections", self.selections(),
                          "--destination", self.destination],
                         stream=io.StringIO())
        said = str(raised.exception)
        self.assertIn("cannot claim Work", said)
        self.assertIn("not preparation identity", said)
        # AND NOTHING WAS GRANTED OR SET: the refusal comes before the acts.
        self.assertEqual(self.granted(installed, uuid), before)

    def test_a_CHANGED_BASE_is_REFUSED_rather_than_called_a_replay(self):
        """Changing the declared base changed what the preparation BINDS, so it
        is a different act. The reviewer's reproduction accepted `b*40` after
        `a*40` and reported the new target as a replay.
        """
        installed, uuid = self.authority()
        self.assertEqual(packets.main(
            ["prepare-work", "--selections", self.selections(),
             "--destination", self.destination], stream=io.StringIO()), 0)
        after = self.granted(installed, uuid)
        self.assertEqual(after["target"], "a" * 40)

        changed = self.selections(source={"root": self.source,
                                          "declared_base": "b" * 40,
                                          "files": ["docs/EXISTING.md"]})
        with self.assertRaises(PacketRefusal) as raised:
            packets.main(["prepare-work", "--selections", changed,
                          "--destination", self.destination],
                         stream=io.StringIO())
        self.assertIn("DIFFERENT operands", str(raised.exception))
        # THE FIRST PREPARATION'S TARGET AND GRANTS STAND, unchanged.
        self.assertEqual(self.granted(installed, uuid), after)

    def test_a_CHANGED_PARTICIPANT_is_REFUSED_too(self):
        """The route handlers and the receipt writers are bound operands as much
        as the base is."""
        installed, uuid = self.authority()
        self.assertEqual(packets.main(
            ["prepare-work", "--selections", self.selections(),
             "--destination", self.destination], stream=io.StringIO()), 0)
        after = self.granted(installed, uuid)
        changed = self.selections(
            participants={"implementation": "baton.somebody-else",
                          "review": "baton.codxpc",
                          "integration": "baton.integrator"})
        with self.assertRaises(PacketRefusal) as raised:
            packets.main(["prepare-work", "--selections", changed,
                          "--destination", self.destination],
                         stream=io.StringIO())
        self.assertIn("DIFFERENT operands", str(raised.exception))
        self.assertEqual(self.granted(installed, uuid), after)

    def test_the_OPERATION_IDENTITY_is_derived_from_the_operands(self):
        """Two selections differing in any bound operand act under two
        identities; identical ones act under the same."""
        chosen = packets.held_selections(self.selections())
        work = packets.prepared_work_id(chosen, "7ea319da" + "0" * 24)
        same = packets.held_selections(self.selections())
        self.assertEqual(packets.preparation_identity(chosen, work),
                         packets.preparation_identity(same, work))
        for changes in (
                {"source": {"root": self.source, "declared_base": "b" * 40,
                            "files": ["docs/EXISTING.md"]}},
                {"participants": {"implementation": "baton.other",
                                  "review": "baton.codxpc",
                                  "integration": "baton.integrator"}},
                {"receipts": {"verification": "baton.other",
                              "review": "baton.approver-review",
                              "approval": "baton.approver"}}):
            with self.subTest(changed=sorted(changes)):
                other = packets.held_selections(self.selections(**changes))
                self.assertNotEqual(
                    packets.preparation_identity(other, work),
                    packets.preparation_identity(chosen, work))

    def test_a_PARTIAL_preparation_is_FINISHED_by_repeating_it(self):
        """Exact recovery: the creation replays through the journal, so a
        preparation interrupted after the Work existed is completed by running
        the same command again -- which is why the gate must not be skipped.
        """
        from baton_v12.authority import Authority

        installed, uuid = self.authority()
        chosen = packets.held_selections(self.selections())
        work = packets.prepared_work_id(chosen, uuid)
        # The interrupted state: the Work created under THIS preparation's own
        # identity, and nothing else done.
        held = Authority.open(installed["authority_store"],
                              expected_authority_uuid=uuid)
        try:
            held.create_work(work, "impl", contract="v12-assignment-1",
                             operation_id=packets.preparation_identity(
                                 chosen, work))
        finally:
            held.dispose()
        self.assertIsNone(self.granted(installed, uuid)["target"])
        stream = io.StringIO()
        self.assertEqual(packets.main(
            ["prepare-work", "--selections", self.selections(),
             "--destination", self.destination], stream=stream), 0)
        answered = json.loads(stream.getvalue())
        self.assertEqual(answered["work_id"], work)
        self.assertIs(answered["created"], False)
        # AND THE REST OF THE PREPARATION COMPLETED.
        after = self.granted(installed, uuid)
        self.assertEqual(after["target"], "a" * 40)
        # The four receipt capabilities, each to the participant this
        # preparation grants it to.
        self.assertEqual(after["capabilities"]["baton.verifier"], ["verify"])
        self.assertEqual(after["capabilities"]["baton.approver-review"],
                         ["review"])
        self.assertEqual(after["capabilities"]["baton.approver"], ["approve"])
        self.assertEqual(after["capabilities"]["baton.integrator"],
                         ["integrate"])

    def test_the_CLI_HAS_NO_operation_id_OVERRIDE_at_all(self):
        """Review 2026-09-29T23-49-58Z: `--operation-id fixed-operator-id` with
        the base changed from `a*40` to `b*40` succeeded TWICE, reported a replay,
        and really moved the canonical target. The option is gone, so the
        argument parser itself refuses it.
        """
        import contextlib

        self.authority()
        said = io.StringIO()
        with self.assertRaises(SystemExit):
            with contextlib.redirect_stderr(said):
                packets.main(["prepare-work", "--selections", self.selections(),
                              "--destination", self.destination,
                              "--operation-id", "fixed-operator-id"],
                             stream=io.StringIO())
        self.assertIn("unrecognized arguments", said.getvalue())
        self.assertIn("--operation-id", said.getvalue())

    def test_prepare_work_TAKES_NO_identity_from_any_caller(self):
        """The same bypass reached through the helper rather than the CLI:
        `prepare_work` trusted a caller-supplied `operation_id`, so a direct
        caller could hold it fixed across changed operands. There is no such
        parameter now, and the signature is the proof.
        """
        import inspect

        held = inspect.signature(packets.prepare_work).parameters
        self.assertEqual(sorted(held), ["authority", "chosen", "work_id"])
        self.assertNotIn("operation_id", held)

    def test_a_FIXED_IDENTITY_cannot_be_reached_to_change_the_base(self):
        """The reviewer's exact reproduction, now impossible: two runs with
        different bases cannot share an identity, so the second is refused and
        the canonical target does NOT move.
        """
        installed, uuid = self.authority()
        self.assertEqual(packets.main(
            ["prepare-work", "--selections", self.selections(),
             "--destination", self.destination], stream=io.StringIO()), 0)
        after = self.granted(installed, uuid)
        self.assertEqual(after["target"], "a" * 40)
        changed = self.selections(source={"root": self.source,
                                          "declared_base": "b" * 40,
                                          "files": ["docs/EXISTING.md"]})
        with self.assertRaises(PacketRefusal):
            packets.main(["prepare-work", "--selections", changed,
                          "--destination", self.destination],
                         stream=io.StringIO())
        self.assertEqual(self.granted(installed, uuid)["target"], "a" * 40)
        self.assertEqual(self.granted(installed, uuid), after)

    def test_the_RECORD_carries_the_operation_and_the_operands(self):
        """A durable record a later reader can verify the replay against."""
        self.authority()
        self.assertEqual(packets.main(
            ["prepare-work", "--selections", self.selections(),
             "--destination", self.destination], stream=io.StringIO()), 0)
        with open(os.path.join(self.destination, "prepared-work.json"),
                  encoding="utf-8") as handle:
            held = json.load(handle)
        chosen = packets.held_selections(self.selections())
        self.assertEqual(held["operation_id"],
                         packets.preparation_identity(chosen, held["work_id"]))
        self.assertEqual(held["operands"],
                         packets.preparation_operands(chosen, held["work_id"]))


class TheSUPPLIED_OPERATOR_TEMPLATE(unittest.TestCase):
    """`SELECTIONS-309356.json` must stay a document an owner can actually fill.

    Review 2026-09-29T23-28-53Z R2: it had DRIFTED from its own generator --
    `held_selections` refused it for a missing `receipts` block before reaching
    the owner placeholders, `stores` was absent, and `participants` still carried
    the receipt principals in the old shape. "Owner selection cannot be asked to
    reconstruct an undocumented schema." These cases hold the template to the
    generator so the drift cannot recur silently.
    """

    TEMPLATE = os.path.join(HERE, "SELECTIONS-309356.json")

    def held(self):
        with open(self.TEMPLATE, encoding="utf-8") as handle:
            return json.load(handle)

    def test_it_refuses_ONLY_for_the_operands_it_names(self):
        """Every refusal an owner meets is a `<OWNER ...>` placeholder, not a
        member they were never told about."""
        with self.assertRaises(PacketRefusal) as raised:
            packets.held_selections(self.TEMPLATE)
        said = str(raised.exception)
        self.assertIn("unresolved owner operand", said)
        # The named operands, and nothing else.
        self.assertEqual(sorted(packets.unresolved(self.held())),
                         ["context_storage.excluded[0]",
                          "credential_reference",
                          "participants.implementation",
                          "participants.integration",
                          "participants.review",
                          "receipts.approval",
                          "receipts.review",
                          "receipts.verification",
                          "source.declared_base",
                          "source.root"])

    def test_replacing_ONLY_those_operands_is_ADMITTED(self):
        """The test the review asked for by name: an owner supplies the marked
        values and nothing more, and the generator accepts the result."""
        held = self.held()
        source = "/home/sl/baton-runs/two-jobs-247941-01-inputs"
        held["source"]["root"] = source
        held["source"]["declared_base"] = "3" * 40
        held["participants"] = {"implementation": "baton.claude",
                                "review": "baton.codxpc",
                                "integration": "baton.integrator"}
        held["receipts"] = {"verification": "baton.verifier",
                            "review": "baton.approver-review",
                            "approval": "baton.approver"}
        held["credential_reference"] = "w202663-development"
        held["context_storage"]["excluded"][0] = source
        with tempfile.NamedTemporaryFile("w", suffix=".json",
                                         delete=False) as handle:
            json.dump(held, handle)
            resolved = handle.name
        self.addCleanup(os.unlink, resolved)
        chosen = packets.held_selections(resolved)
        self.assertEqual(chosen["run_id"], "managed-correction-309356")
        # AND THE WORK IDENTITY IT WOULD CREATE IS A VALID ONE.
        self.assertEqual(
            packets.prepared_work_id(chosen, "7ea319da" + "0" * 24),
            "7ea319da-W236087")

    def test_it_carries_EVERY_member_the_generator_requires(self):
        """A missing member is what made the old template unusable, so the
        membership is checked against the generator's own tuple.
        """
        self.assertEqual(sorted(self.held()), sorted(packets._SELECTIONS))

    def test_the_STORES_are_the_INSTALLED_layout_s_own(self):
        held = self.held()
        root = held["instance_root"]
        self.assertEqual(held["stores"]["authority"],
                         root + "/db/authority.sqlite3")
        self.assertEqual(held["stores"]["job"], root + "/db/jobs.sqlite3")
        self.assertEqual(held["stores"]["state_root"], root + "/deployment-state")

    def test_NO_CREDENTIAL_BYTE_appears_anywhere_in_it(self):
        body = json.dumps(self.held()).lower()
        for forbidden in ("secret", "token", "password", "bearer",
                          "private_key"):
            self.assertNotIn(forbidden, body)


class TheRESOLVED_SELECTION(unittest.TestCase):
    """`SELECTIONS-RESOLVED-311743.json` -- the corrected filled selection.

    Owner reroute 311598 asked for the ten operands resolved "using the accepted
    source/base and configured credential reference and principals where
    applicable". These hold the delivered file to that: ADMITTED with nothing
    unresolved, every value the ACCEPTED record's, and a valid Work identity.

    NOTHING IS EXECUTED HERE and nothing outside this dossier is read except the
    accepted deployment record the values came from.
    """

    RESOLVED = os.path.join(HERE, "SELECTIONS-RESOLVED-311743.json")
    SUPERSEDED = os.path.join(HERE, "SELECTIONS-RESOLVED-311606.json")
    ACCEPTED_DEPLOYMENT = (
        "/home/sl/baton-runs/single-implementation-244216/run/deployment.json")

    def held(self):
        with open(self.RESOLVED, encoding="utf-8") as handle:
            return json.load(handle)

    def deployed(self):
        with open(self.ACCEPTED_DEPLOYMENT, encoding="utf-8") as handle:
            return json.load(handle)

    def test_it_is_ADMITTED_with_nothing_unresolved(self):
        chosen = packets.held_selections(self.RESOLVED)
        self.assertEqual(packets.unresolved(chosen), [])
        self.assertEqual(chosen["run_id"], "managed-correction-309356")

    def test_the_WORK_IDENTITY_it_would_create_is_a_valid_one(self):
        chosen = packets.held_selections(self.RESOLVED)
        self.assertEqual(
            packets.prepared_work_id(chosen, "7ea319da" + "0" * 24),
            "7ea319da-W236087")

    def test_the_SOURCE_and_BASE_are_the_accepted_ones(self):
        held = self.held()
        self.assertEqual(held["source"]["root"],
                         "/home/sl/baton-runs/two-jobs-247941-01-inputs")
        self.assertEqual(held["source"]["declared_base"],
                         "346a809bf0e4c47e52d881bd46d6d62a611c9816")
        # AND THE TASK'S OUTPUT IS ABSENT FROM IT, which is what makes this the
        # Job the packet describes rather than a review of somebody else's file.
        self.assertFalse(os.path.exists(
            os.path.join(held["source"]["root"], packets.TASK_PATH)))

    def test_every_PRINCIPAL_comes_from_the_accepted_deployment(self):
        held = self.held()
        deployed = self.deployed()
        workers = {one["worker_id"]: one["deployment"]
                   for one in deployed["workers"]}
        self.assertEqual(held["participants"]["implementation"],
                         workers["implementation-worker"]["participant"])
        self.assertEqual(held["participants"]["review"],
                         workers["review-worker"]["participant"])
        self.assertEqual(
            held["participants"]["integration"],
            deployed["integration_profile"]["integrator_participant"])
        self.assertEqual(held["receipts"], deployed["receipt_participants"])
        # THE RECEIPT WRITERS ARE NOT THE WORKERS: the Authority refuses a
        # receipt written by an actor it granted nothing to.
        self.assertNotIn(held["participants"]["implementation"],
                         held["receipts"].values())
        self.assertNotIn(held["participants"]["review"],
                         held["receipts"].values())

    def test_the_CREDENTIAL_REFERENCE_is_the_configured_NAME_and_no_bytes(self):
        held = self.held()
        deployed = self.deployed()
        configured = {one["worker_id"]: one["deployment"]
                      for one in deployed["workers"]}["implementation-worker"]
        self.assertEqual(held["credential_reference"],
                         configured["credential_profile"]["claude"]["reference"])
        self.assertEqual(held["credential_delivery"]["provider"],
                         configured["credential_profile"]["claude"]["provider"])
        # A REFERENCE AND A REGISTRY PATH, never a bearer.
        body = json.dumps(held).lower()
        for forbidden in ("secret", "token", "password", "bearer",
                          "private_key", "api_key"):
            self.assertNotIn(forbidden, body)

    def delivered(self):
        with open(os.path.join(HERE, "RUN-COMMANDS-311743.json"),
                  encoding="utf-8") as handle:
            return json.load(handle)

    def regenerated(self):
        """What the generator emits for the DELIVERED selection and paths."""
        chosen = packets.held_selections(self.RESOLVED)
        delivered = self.delivered()
        destination = delivered["destination"]
        prepared = {
            "destination": destination,
            "claim": 311743,
            "selections": self.RESOLVED,
            "provenance": os.path.join(HERE, "PROVENANCE-309356.json"),
            "bootstrap_inputs": destination + "/bootstrap-inputs.json",
            "packet": destination + "/packet.json",
        }
        return packets.commands(chosen, prepared=prepared,
                                job_id=packets.job_id_of(chosen))

    def test_the_DELIVERED_COMMANDS_EQUAL_the_generator_s_output(self):
        """Review 2026-09-30T02-44-57Z R2: the previous case checked only
        FRAGMENTS -- that some string appeared in some argv -- which a delivered
        list could satisfy while differing from what the generator emits. This
        compares the ACTUAL DELIVERED DATA, member for member.
        """
        delivered = self.delivered()
        expected = [one for one in self.regenerated()
                    if one["step"] != 6]
        self.assertEqual(delivered["commands"], expected)

    def test_NO_DELIVERED_ARGV_ELEMENT_IS_A_PLACEHOLDER(self):
        """R2: step 6 carried `<the uuid tools.bootstrap minted, in
        <root>/bootstrap.json>` as an argv element -- a value that would be
        passed to the manager verbatim -- while the operator document claimed the
        identity was already substituted. Nothing delivered may be a placeholder
        or a shell expression.
        """
        for one in self.delivered()["commands"]:
            for part in one["command"]:
                self.assertNotIn("$(", part, one)
                self.assertFalse(part.startswith("<"), (part, one))
                self.assertNotIn("<root>", part, one)
                self.assertNotIn("placeholder", part.lower(), one)

    def test_the_STATUS_STEP_is_PENDING_with_a_read_only_resolver(self):
        """It needs the identity `tools.bootstrap` mints, so it is listed as
        pending -- and the pending entry carries the read-only resolver and
        points at the complete list `bind` writes.
        """
        delivered = self.delivered()
        self.assertEqual([one["step"] for one in delivered["commands"]],
                         [0, 1, 2, 3, 4, 5, 7])
        pending = delivered["commands_pending"]
        self.assertEqual([one["step"] for one in pending], [6])
        self.assertIn("commands.json", pending[0]["why"])
        # THE RESOLVER IS READ-ONLY: it reads one file and prints one field.
        resolver = pending[0]["resolver"]
        self.assertEqual(resolver[0], "python3")
        self.assertIn("authority_uuid", resolver[2])
        self.assertTrue(resolver[-1].endswith("bootstrap.json"))

    def test_the_DELIVERED_STEPS_are_the_ones_the_document_describes(self):
        delivered = self.delivered()
        steps = {one["step"]: one for one in delivered["commands"]}
        self.assertIn("tools.bootstrap", steps[1]["command"])
        self.assertIn("prepare-work", steps[2]["command"])
        self.assertIn("bind", steps[3]["command"])
        self.assertIn("check", steps[4]["command"])
        self.assertIn("correction_supervisor.py", steps[5]["command"][1])
        for step, one in steps.items():
            self.assertIn("PYTHONDONTWRITEBYTECODE", one["environment"], step)

    def test_the_OPERATOR_DOCUMENT_has_NO_broken_shell_continuation(self):
        """R1: fifteen lines ended in TWO backslashes, so a literal backslash
        reached python3 and `--selections`/`--provenance` became separate
        commands. One backslash continues a line; two pass one along.
        """
        with open(os.path.join(HERE, "OPERATOR-311743.md"),
                  encoding="utf-8") as handle:
            body = handle.read()
        # BUILT FROM CHARACTER CODES, because escaping a backslash-count
        # assertion in a Python literal is exactly how the first version of this
        # case came out wrong -- it asserted against the SINGLE backslash a
        # legitimate continuation uses and failed on a correct document.
        backslash = chr(92)
        self.assertEqual(body.count(backslash * 2), 0)
        self.assertNotIn(backslash * 2 + chr(10), body)
        # And a continuation is still there: this is not passing by their absence.
        self.assertIn(backslash + chr(10), body)
        # AND THE FALSE CLAIM IS GONE.
        self.assertNotIn("already substituted", body)


class TheCORRECTED_OPERATOR_SEQUENCE(unittest.TestCase):
    """Owner reroute 311736, and the two further defects running it found.

    The delivered sequence could not have succeeded: the staged source carried
    no frozen resources, the staging root was a SIBLING of the instance so the
    tree the staged code calls its checkout contained the instance, and `stage`
    itself was not in the machine-readable sequence and ran with no import
    path. These hold the corrected documents to all three, and to the reroute's
    own requirement that the sequence stop at its first error.

    NOTHING IS EXECUTED HERE. The evidence documents are the records of runs
    that happened in temporary roots, and the scripts that made them are in the
    dossier for a reviewer to re-run.
    """

    OPERATOR = os.path.join(HERE, "OPERATOR-311743.md")
    RESOLVED = os.path.join(HERE, "SELECTIONS-RESOLVED-311743.json")
    SUPERSEDED = os.path.join(HERE, "SELECTIONS-RESOLVED-311606.json")

    def read(self, path):
        with open(path, encoding="utf-8") as handle:
            return json.load(handle) if path.endswith(".json") \
                else handle.read()

    def test_the_PRODUCTS_OWN_CHECKOUT_RULE_admits_the_CORRECTED_layout(self):
        """MEASURED, not reasoned about: the real origin is staged into a
        temporary tree laid out exactly as the selection lays it out, and the
        STAGED TREE is asked what it calls its checkout.
        """
        chosen = packets.held_selections(self.RESOLVED)
        root = tempfile.mkdtemp(prefix="checkout-rule-")
        self.addCleanup(__import__("shutil").rmtree, root, ignore_errors=True)
        staging = os.path.join(root, "staging",
                               os.path.basename(chosen["staging_root"]))
        staged = os.path.join(staging, "manager-source")
        packets.staged_source(chosen["manager_source_origin"], staged)
        measured = packets.staged_report(staged)["checkout"]
        # THE RULE THE PRODUCT ANSWERS: the parent of the staging root.
        self.assertEqual(measured,
                         os.path.realpath(os.path.dirname(staging)))

        # APPLIED TO THE DELIVERED PATHS: the instance is outside it.
        tree = os.path.dirname(os.path.realpath(chosen["staging_root"]))
        instance = os.path.realpath(chosen["instance_root"])
        self.assertFalse(instance == tree
                         or instance.startswith(tree.rstrip("/") + os.sep),
                         (instance, tree))

        # AND THE SUPERSEDED SELECTION WOULD HAVE BEEN REFUSED AT STEP 1: the
        # two were siblings under /home/sl/baton-instances.
        was = self.read(self.SUPERSEDED)
        before = os.path.dirname(os.path.realpath(was["staging_root"]))
        self.assertTrue(
            os.path.realpath(was["instance_root"]).startswith(
                before.rstrip("/") + os.sep),
            (was["instance_root"], before))

    def test_THE_CORRECTED_SELECTION_CHANGES_ONLY_THE_STAGING_ROOT(self):
        """The accepted operands are not re-chosen under cover of a fix."""
        held = self.read(self.RESOLVED)
        was = self.read(self.SUPERSEDED)
        self.assertNotEqual(held["staging_root"], was["staging_root"])
        self.assertEqual({name: value for name, value in held.items()
                          if name != "staging_root"},
                         {name: value for name, value in was.items()
                          if name != "staging_root"})

    def blocks(self):
        """The document's SHELL BLOCKS, indented four spaces, prose excluded."""
        body = self.read(self.OPERATOR)
        held = []
        for chunk in re.findall(r"(?:^    .*\n|^\n)+", body, re.M):
            for one in chunk.splitlines():
                held.append(one[4:] if one.startswith("    ") else one)
        return held

    def typed(self):
        """Every command the document tells a human to type, as an argv.

        The document's own `export` lines supply the variables, the `$(...)`
        resolver becomes one sentinel element, and `shlex` does the splitting --
        so what is compared is what a shell would actually run rather than a
        substring of the page.
        """
        names = {}
        joined = []
        held = ""
        for line in self.blocks():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.endswith(chr(92)):
                held += line[:-1] + " "
                continue
            joined.append(held + line)
            held = ""
        commands = []
        for line in joined:
            if line.startswith("export "):
                name, _, value = line[len("export "):].partition("=")
                names[name] = value
                continue
            if line.startswith("set "):
                continue
            resolved = re.sub(r"\$\(.*?\)(?=\s|$)", "RESOLVED-AT-RUN-TIME",
                              line)
            for name in sorted(names, key=len, reverse=True):
                value = names[name]
                for other in sorted(names, key=len, reverse=True):
                    value = value.replace("$" + other, names[other])
                resolved = resolved.replace("$" + name, value)
            commands.append(shlex.split(resolved))
        return commands

    def test_THE_STATUS_COMMAND_IS_THE_GENERATED_ONE_AND_THE_PARSER_TAKES_IT(self):
        """REVIEW 311971 R1, and it was a real regression.

        The previous revision displayed `--job-store` and `status --job`, with
        no `--incarnation` and no `--control`. `tools.job_manager` refuses that
        at the PARSER with exit 2, before a store is opened -- so the one
        command an operator would reach for while a run was serving could not
        have run. A stub that accepts arbitrary options cannot see that, which
        is why this case drives the REAL parser.
        """
        from tools import job_manager

        chosen = packets.held_selections(self.RESOLVED)
        typed = [argv for argv in self.typed()
                 if "tools.job_manager" in argv]
        self.assertEqual(len(typed), 1, typed)
        argv = typed[0]

        # IT IS THE GENERATED ARGV. `commands()` step 6 is the owner of this
        # shape; the human form differs only in resolving the identity through
        # a shell substitution instead of carrying the literal.
        generated = [one for one in packets.commands(
            chosen, prepared={"destination": "/x", "claim": 0,
                              "selections": "/x/s.json",
                              "provenance": "/x/p.json",
                              "bootstrap_inputs": "/x/b.json",
                              "packet": "/x/packet.json"},
            job_id=packets.job_id_of(chosen),
            authority_uuid="RESOLVED-AT-RUN-TIME")
            if one["step"] == 6][0]["command"]
        self.assertEqual(argv[argv.index("python3"):], generated)

        # AND THE REAL PARSER TAKES IT, against disposable empty stores: it runs
        # to completion and answers a status document.
        root = tempfile.mkdtemp(prefix="status-reader-")
        self.addCleanup(__import__("shutil").rmtree, root, ignore_errors=True)
        stores = os.path.join(root, "db")
        os.makedirs(stores)
        for name in ("jobs.sqlite3", "control.sqlite3"):
            open(os.path.join(stores, name), "wb").close()
        disposable = []
        for part in generated[3:]:
            if part.endswith("jobs.sqlite3"):
                part = os.path.join(stores, "jobs.sqlite3")
            elif part.endswith("control.sqlite3"):
                part = os.path.join(stores, "control.sqlite3")
            elif part == "RESOLVED-AT-RUN-TIME":
                part = "7ea319da93384b77bc3ddea38602d7a3"
            disposable.append(part)
        stream = io.StringIO()
        job_manager.main(disposable, stream=stream)
        answered = json.loads(stream.getvalue())
        self.assertEqual(answered["jobs"], [])
        self.assertEqual(answered["incarnation"], chosen["run_id"])

        # AND THE REGRESSED SHAPE IS REFUSED AT THE PARSER, so this case cannot
        # pass by accepting anything at all.
        with self.assertRaises(SystemExit) as raised, \
                contextlib.redirect_stderr(io.StringIO()):
            job_manager.main(
                ["--job-store", os.path.join(stores, "jobs.sqlite3"),
                 "--authority-uuid", "7ea319da93384b77bc3ddea38602d7a3",
                 "status", "--job", packets.job_id_of(chosen)],
                stream=io.StringIO())
        self.assertEqual(raised.exception.code, 2)

    def test_THE_STATUS_PARSER_EVIDENCE_RECORDS_BOTH_SHAPES(self):
        """The record of the run above, so a reviewer reads the measurement
        rather than taking the case's word for it.
        """
        held = self.read(os.path.join(HERE,
                                      "STATUS-PARSER-EVIDENCE-311994.json"))
        measured = held["measured"]
        self.assertEqual(
            measured["1_regressed_shape_as_previously_delivered"]["result"]
            ["exit"], 2)
        self.assertEqual(
            measured["3_generated_shape_against_disposable_empty_stores"]
            ["result"]["exit"], 0)
        self.assertEqual(held["status_document"]["jobs"], [])
        for required in ("--store", "--incarnation", "--authority-uuid"):
            self.assertIn(required, held["generated_argv"])

    def test_THE_STOP_SECTION_IS_AN_ACTION_AND_READS_THE_BOUND_OUTCOME(self):
        """REVIEW 311971 R2: the section labelled Stop contained NO STOP
        ACTION. It printed a document, from the wrong path, and called that
        stopping.
        """
        body = self.read(self.OPERATOR)
        stopping = body[body.index("## 5. Stop"):body.index("## 6. ")]
        # THE ACTION, and the semantics the supervisor actually keeps.
        self.assertIn("Ctrl-C", stopping)
        self.assertIn("SIGINT", stopping)
        self.assertIn("130", stopping)
        self.assertIn("defers", stopping)
        self.assertIn("cleanup window", stopping)
        self.assertIn("SIGKILL", stopping)
        # THE BOUND OUTCOME PATH, which is the instance's run directory and not
        # the packet destination.
        chosen = packets.held_selections(self.RESOLVED)
        bound = os.path.join(chosen["instance_root"], "run", "outcome.json")
        generated = [one for one in packets.commands(
            chosen, prepared={"destination": "/x", "claim": 0,
                              "selections": "/x/s.json",
                              "provenance": "/x/p.json",
                              "bootstrap_inputs": "/x/b.json",
                              "packet": "/x/packet.json"},
            job_id=packets.job_id_of(chosen))
            if one["step"] == 7][0]["command"]
        self.assertEqual(generated[-1], bound)
        reading = [argv for argv in self.typed()
                   if any(part.endswith("outcome.json") for part in argv)]
        self.assertEqual(len(reading), 1, reading)
        self.assertEqual(reading[0][-1], bound)
        self.assertNotIn("/managed-correction-309356-packet", reading[0][-1])

    def test_THE_SEQUENCE_STOPS_AT_ITS_FIRST_ERROR(self):
        """The reroute's own requirement. `set -e` is asserted in the document
        AND proved by running it: a stub that fails the Nth step, and no step
        after it.
        """
        body = self.read(self.OPERATOR)
        self.assertIn("set -e", body)
        self.assertIn("set -o pipefail", body)
        evidence = self.read(os.path.join(
            HERE, "STOP-ON-ERROR-EVIDENCE-311994.json"))
        self.assertTrue(evidence["every_case_stopped"])
        self.assertEqual([one["failed_at_invocation"]
                          for one in evidence["measured"]], [1, 2, 3])
        for one in evidence["measured"]:
            self.assertEqual(one["invocations_after_the_failure"], 0, one)
            self.assertNotEqual(one["sequence_returncode"], 0, one)

    def test_THE_ARGV_IS_VERIFIED_AND_STAGE_IS_IN_IT(self):
        evidence = self.read(os.path.join(HERE, "ARGV-EVIDENCE-311994.json"))
        self.assertEqual(evidence["faults"], [])
        self.assertEqual(evidence["sh_n"], "OK")
        self.assertEqual(evidence["returncode"], 0)
        self.assertTrue(evidence["stops_on_first_error"])
        named = [argv for argv in evidence["invocations"] if "stage" in argv]
        self.assertEqual(len(named), 1, named)
        for operand in ("--selections", "--destination", "--claim",
                        "--provenance"):
            self.assertIn(operand, named[0])

    def test_THE_STAGE_TO_BOOTSTRAP_PATH_WAS_DRIVEN_AND_THE_DEFECT_SHOWN(self):
        """The reroute asked for the actual path to be proved in a disposable
        installation without Docker or live providers. This holds the evidence
        that run produced to exactly that.
        """
        held = self.read(os.path.join(
            HERE, "STAGE-BOOTSTRAP-EVIDENCE-311743.json"))
        self.assertEqual(held["docker"], "not used")
        self.assertEqual(held["providers"], "not run")
        self.assertTrue(held["disposable_root_removed"])
        self.assertTrue(held["disposable_root"].startswith("/tmp/"))

        # THE DEFECT, SHOWN: a module-only tree fails at import, naming the
        # asset, from the loader that reads it.
        shown = held["defect_reproduced"]
        self.assertNotEqual(shown["returncode"], 0)
        self.assertIn("worker-control-1.0.schema.json", shown["failure"])
        self.assertIn("FileNotFoundError", shown["failure"])
        self.assertEqual(
            sorted(shown["removed"]),
            ["src/baton_v12/contracts/schema/agent-session-1.0.schema.json",
             "src/baton_v12/contracts/schema/worker-control-1.0.schema.json"])

        # THE CORRECTED STAGE: both assets staged, measured, and IMPORTED.
        self.assertEqual(held["stage"]["returncode"], 0)
        self.assertEqual(held["stage"]["frozen_assets"],
                         sorted(held["staged_source_report"]["assets"]))
        loaded = held["staged_source_report"]["loaded"]
        self.assertTrue(all(count > 0 for count in loaded.values()), loaded)

        # BOOTSTRAP ITSELF, from that tree, and then the three steps that had
        # failed for want of what it never wrote.
        self.assertEqual(held["bootstrap"]["returncode"], 0)
        self.assertTrue(held["bootstrap"]["record_written"])
        self.assertEqual([one["step"] for one in held["recovery"]],
                         ["prepare-work", "bind", "check"])
        for one in held["recovery"]:
            self.assertEqual(one["returncode"], 0, one)
        self.assertEqual(held["packet"]["schema"], packets.PACKET_SCHEMA)
        self.assertEqual(held["packet"]["frozen_assets"],
                         sorted(held["staged_source_report"]["assets"]))

    def test_THE_PARTIAL_PREPARATION_IS_NAMED_AND_PRESERVED(self):
        """Read-only inspection, and paths that cannot collide with it: the
        corrected sequence writes to a NEW packet destination and a NEW staging
        root, so the failed run's tree stays exactly as it left it.
        """
        body = self.read(self.OPERATOR)
        for named in ("/home/sl/baton-instances/managed-correction-309356-source",
                      "/home/sl/baton-instances/managed-correction-309356-packet",
                      "LEFT AS IS", "ABSENT"):
            self.assertIn(named, body)
        delivered = self.read(os.path.join(HERE, "RUN-COMMANDS-311743.json"))
        self.assertNotEqual(
            delivered["destination"],
            "/home/sl/baton-instances/managed-correction-309356-packet")
        chosen = self.read(self.RESOLVED)
        self.assertNotEqual(
            chosen["staging_root"],
            "/home/sl/baton-instances/managed-correction-309356-source")
        # AND NO STEP DELETES OR COPIES ANYTHING BY HAND.
        for one in delivered["commands"]:
            for part in one["command"]:
                for forbidden in ("rm", "rmdir", "cp", "mv", "shutil.rmtree"):
                    self.assertNotEqual(part, forbidden, one)


class TheCommandsAreCommands(Fixture):
    """Review R1: sections 4 and 5 were comments naming APIs. Every step is a
    command with its own argument vector and its own environment."""

    def test_every_step_is_an_argument_vector_with_an_import_environment(self):
        _chosen, prepared = self.staged()
        steps = prepared["commands"]
        # SIX AT `stage` TIME AND SEVEN AFTER `bind`: the status step needs
        # the minted identity, so it is listed as PENDING here rather than
        # written with a placeholder that looks like a value. STEP 0 IS `stage`
        # ITSELF -- the delivered sequence omitted it, so the one command whose
        # defect stopped owner report 311736's run was the one command the
        # machine-readable sequence did not carry.
        self.assertEqual([one["step"] for one in steps],
                         [0, 1, 2, 3, 4, 5, 7])
        self.assertEqual([one["step"] for one in prepared["commands_pending"]],
                         [6])
        for one in steps:
            self.assertIsInstance(one["command"], list)
            self.assertTrue(all(isinstance(part, str)
                                for part in one["command"]), one)
            self.assertTrue(one["command"][0].endswith("python3"), one)
            self.assertEqual(one["environment"]["PYTHONDONTWRITEBYTECODE"], "1")

    def test_the_BOOTSTRAP_runs_with_the_import_path_already_set(self):
        """Review R1: "Bootstrap is invoked before PYTHONPATH is set... the
        command does not establish a reproducible module environment."""
        _chosen, prepared = self.staged()
        steps = {one["step"]: one for one in prepared["commands"]}
        staged = os.path.join(self.staging, "manager-source")
        self.assertIn("tools.bootstrap", steps[1]["command"])
        self.assertEqual(steps[1]["environment"]["PYTHONPATH"],
                         os.path.join(staged, "src") + ":" + staged)
        # AND STEP 0 IMPORTS THE ORIGIN, because the staged tree is what step 0
        # creates. The delivered sequence ran `stage` with no `PYTHONPATH` at
        # all and relied on whatever the operator's interpreter happened to
        # have installed.
        self.assertIn("stage", steps[0]["command"])
        self.assertEqual(steps[0]["environment"]["PYTHONPATH"],
                         os.path.join(self.origin, "src") + ":" + self.origin)
        self.assertNotIn(staged, steps[0]["environment"]["PYTHONPATH"])

    def test_the_SERVING_step_is_the_bounded_supervisor_and_not_a_bare_serve(self):
        """Review R2: a bare `serve` has no timer, no reserve and no cap."""
        _chosen, prepared = self.staged()
        serving = {one["step"]: one for one in prepared["commands"]}[5]
        self.assertIn("correction_supervisor.py", serving["command"][1])
        self.assertNotIn("serve", serving["command"])
        self.assertIn("--packet", serving["command"])

    def test_the_WORK_PREPARATION_step_comes_between_bootstrap_and_bind(self):
        """Review 2026-09-29T23-17-24Z R1: the commands went straight from the
        bootstrap to `bind`, which needs the qualified Work id -- and a FRESH
        installation binds no Job by design, so there was nothing to read.
        """
        _chosen, prepared = self.staged()
        steps = {one["step"]: one for one in prepared["commands"]}
        preparing = steps[2]["command"]
        self.assertIn("prepare-work", preparing)
        self.assertIn("--selections", preparing)
        self.assertIn("--destination", preparing)
        self.assertIn("tools.bootstrap", steps[1]["command"])
        self.assertIn("bind", steps[3]["command"])
        # AND IT SUBMITS NO JOB: `baseline.survey` refuses a Job identity the
        # store already records, so the execution Job is the supervisor's.
        for part in preparing:
            self.assertNotIn("submit", part)

    def test_the_CHECK_step_runs_under_the_STAGED_imports(self):
        """R2: it omitted the staged PYTHONPATH although `held_packet` drives the
        REAL product validators -- it would have imported whatever was ambient,
        which is the exact thing the staging exists to prevent.
        """
        _chosen, prepared = self.staged()
        steps = {one["step"]: one for one in prepared["commands"]}
        checking = steps[4]
        self.assertIn("check", checking["command"])
        staged = os.path.join(self.staging, "manager-source")
        self.assertEqual(checking["environment"]["PYTHONPATH"],
                         os.path.join(staged, "src") + ":" + staged)

    def test_the_BINDING_step_carries_its_own_operands(self):
        """A step whose operands an operator has to reconstruct from prose is
        the defect this file exists to correct."""
        _chosen, prepared = self.staged()
        binding = {one["step"]: one for one in prepared["commands"]}[3]
        self.assertIn("bind", binding["command"])
        for operand in ("--selections", "--destination", "--claim",
                        "--provenance"):
            self.assertIn(operand, binding["command"])

    def test_the_STATUS_step_is_WRITTEN_BY_BIND_with_the_real_identity(self):
        """Review 2026-09-29T21-41-08Z R1, both halves. The argv carried
        `$(python3 -c ...)` as ONE element -- text no shell expands when the
        vector is executed -- and `--job`, which `tools.job_manager status`
        does not have. Its options are `--control` and `--observe`.
        """
        self.packet()
        with open(os.path.join(self.destination, "commands.json"),
                  encoding="utf-8") as handle:
            written = json.load(handle)
        self.assertEqual([one["step"] for one in written["commands"]],
                         [0, 1, 2, 3, 4, 5, 6, 7])
        status = [one for one in written["commands"]
                  if one["step"] == 6][0]["command"]
        self.assertIn("status", status)
        self.assertEqual(status[status.index("--authority-uuid") + 1],
                         "7ea319da93384b77bc3ddea38602d7a3")
        self.assertNotIn("--job", status)
        # AND THE SELECTED STORES, not a layout the command assumed. R2: these
        # were hardcoded under the instance root while `bind` binds the selected
        # ones.
        self.assertEqual(status[status.index("--store") + 1],
                         os.path.join(self.instance, "db", "jobs.sqlite3"))
        self.assertEqual(status[status.index("--control") + 1],
                         os.path.join(self.instance, "db", "control.sqlite3"))
        for part in status:
            self.assertNotIn("$(", part)
        for act in ("serve", "submit", "sweep"):
            self.assertNotIn(act, status)

    def test_the_REAL_STATUS_CLI_accepts_the_emitted_OPTIONS(self):
        """Asked of the real parser rather than of my memory of it.

        `--job` reached the previous draft's argv because nothing checked the
        option set against the program that would receive it. This runs the
        real entry point over the emitted vector and asserts the parser did
        not reject it -- an unknown option exits 2 with `unrecognized
        arguments`, which is a different failure from a missing store.
        """
        import contextlib
        import io as _io

        from tools import job_manager

        self.packet()
        with open(os.path.join(self.destination, "commands.json"),
                  encoding="utf-8") as handle:
            written = json.load(handle)
        status = [one for one in written["commands"]
                  if one["step"] == 6][0]["command"]
        argv = status[status.index("tools.job_manager") + 1:]
        said = _io.StringIO()
        try:
            with contextlib.redirect_stderr(said):
                job_manager.main(argv)
        except BaseException:                                # noqa: BLE001
            pass
        self.assertNotIn("unrecognized arguments", said.getvalue())
        self.assertNotIn("invalid choice", said.getvalue())
        self.assertNotIn("--job", said.getvalue())



    def test_the_serving_step_names_the_deployment_configuration(self):
        _chosen, prepared = self.staged()
        serving = {one["step"]: one for one in prepared["commands"]}[5]
        # THE GENERATED COMPOSITION, which is what the run composes from and
        # what the packet pins; the installer's own configuration binds no Job.
        self.assertEqual(
            serving["environment"]["BATON_V12_STAGE_EXECUTION_CONFIG"],
            os.path.join(self.destination, "deployment.json"))


class GenerationRefusesBeforeItWrites(Fixture):

    def _refusal(self, **changes):
        with self.assertRaises(PacketRefusal) as held:
            packets.held_selections(self.selections(**changes))
        return str(held.exception)

    def test_an_UNRESOLVED_owner_operand_is_named_rather_than_defaulted(self):
        said = self._refusal(credential_reference="<OWNER: which session?>")
        self.assertIn("credential_reference", said)

    def test_a_STAGING_root_inside_the_run_root_is_refused_with_the_walk(self):
        """The boundary rule, measured: `stage_execution._checkout` walks three
        parents, so a source staged inside the run root makes the run root the
        code boundary and this run's own stores live inside it."""
        said = self._refusal(
            staging_root=os.path.join(self.instance, "manager-source"))
        self.assertIn("three parents", said)

    def test_a_RUN_ROOT_inside_the_staging_root_is_the_same_fault(self):
        said = self._refusal(staging_root=os.path.dirname(self.instance))
        self.assertIn("nest", said)

    def test_a_SELF_REVIEWING_producer_is_refused(self):
        said = self._refusal(participants={"implementation": "baton.claude",
                                           "review": "baton.claude",
                                           "integration": "baton.integrator"})
        self.assertIn("independent", said)

    def test_a_PROFILE_composed_against_ANOTHER_image_is_refused(self):
        """Review R3: the reused image must be the one the profile qualifies."""
        said = self._refusal(context_profile=self.profile(image_digest=OTHER))
        self.assertIn("does not qualify these", said)

    def test_a_PROFILE_naming_another_adapter_descriptor_is_refused(self):
        said = self._refusal(context_profile=self.profile(adapter_digest=OTHER))
        self.assertIn("adapter descriptor", said)

    def test_a_FRESH_RUN_profile_that_retains_no_conversation_is_refused(self):
        """The `claude-fresh-implementation` label is not the proof: a profile
        whose allowlist names no conversation file could retain nothing for a
        restore to consume."""
        said = self._refusal(context_profile=self.profile(
            state_paths=[".claude/projects/-output/settings.json"]))
        self.assertIn("no conversation file", said)

    def test_a_SHORT_declared_base_is_refused(self):
        said = self._refusal(source={"root": self.source,
                                     "declared_base": "abc",
                                     "files": ["docs/EXISTING.md"]})
        self.assertIn("full lower-case object name", said)

    def test_an_ABSENT_source_file_is_refused_before_anything_is_written(self):
        chosen = packets.held_selections(
            self.selections(source={"root": self.source,
                                    "declared_base": "a" * 40,
                                    "files": ["docs/ABSENT.md"]}))
        with self.assertRaises(PacketRefusal):
            packets.stage(chosen, self.destination)
        self.assertFalse(os.path.exists(
            os.path.join(self.destination, "submission.json")))

    def test_a_SOURCE_that_already_holds_the_task_output_is_refused(self):
        """A documentation Job whose file already exists at the declared base
        is a different Job, and the reviewer would be reading someone else's
        work."""
        _write(os.path.join(self.source, packets.TASK_PATH), "already here\n")
        chosen = packets.held_selections(self.selections())
        with self.assertRaises(PacketRefusal) as held:
            packets.stage(chosen, self.destination)
        self.assertIn("a different Job", str(held.exception))

    def test_BINDING_before_the_bootstrap_ran_is_refused_by_name(self):
        chosen, _prepared = self.staged()
        with self.assertRaises(PacketRefusal) as held:
            packets.bind(chosen, self.destination, claim=1, provenance={},
                         compatibility={})
        self.assertIn("run the bootstrap command", str(held.exception))


# -- the packet's own proof -------------------------------------------------

class BindRefusesDriftRatherThanResigningIt(Fixture):
    """Review 2026-09-29T21-41-08Z R4, and the finding was exactly right.

    `bind` re-hashed whatever was staged at that moment and wrote those digests
    into the packet, so a module edited between `stage` and `bind` was SIGNED
    rather than refused. Re-signing drift is worse than not checking at all,
    because the packet then testifies to bytes nobody reviewed.
    """

    def _bind(self):
        _write(os.path.join(self.instance, "bootstrap.json"),
               {"authority_uuid": "7ea319da93384b77bc3ddea38602d7a3"})
        _write(os.path.join(self.instance, "deployment.json"),
               {"job_bindings": [{"job_id": "job-managed-correction-test",
                                  "job_work_id": WORK_ID,
                                  "review_work_id": WORK_ID,
                                  "source_worker_id": "implementation-worker"}],
                "workers": [{"worker_id": "w", "deployment": {
                    "workspace_storage": os.path.join(self.instance, "run",
                                                      "workspaces")}}]})
        chosen = packets.held_selections(self.selections())
        with mock.patch.object(packets, "certified_digest",
                               return_value="sha256:" + "11" * 32):
            return packets.bind(
                chosen, self.destination, claim=1,
                provenance={"worker_image": {
                    "path": self.provenance_record,
                    "sha256": packets.digest_of(self.provenance_record)}},
                compatibility={"adapter_source_sha256": "18" * 32,
                               "context_capable": True,
                               "established": ["measured"],
                               "not_established": ["the production branch"]})

    def test_a_STAGED_MODULE_CHANGED_after_stage_is_refused_not_resigned(self):
        _chosen, prepared = self.staged()
        _write(os.path.join(prepared["staged_source"]["path"], "tools",
                            "stage_execution.py"), "drifted\n")
        with self.assertRaises(PacketRefusal) as raised:
            self._bind()
        self.assertIn("CHANGED since `stage`", str(raised.exception))
        self.assertIn("stage_execution.py", str(raised.exception))
        self.assertFalse(os.path.exists(
            os.path.join(self.destination, "packet.json")))

    def test_a_STAGED_MODULE_that_APPEARED_is_also_drift(self):
        """A file nobody reviewed is a difference between the reviewed
        preparation and this one, not an addition to it.
        """
        _chosen, prepared = self.staged()
        _write(os.path.join(prepared["staged_source"]["path"], "tools",
                            "extra.py"), "print('unreviewed')\n")
        with self.assertRaises(PacketRefusal) as raised:
            self._bind()
        self.assertIn("tools/extra.py", str(raised.exception))

    def test_a_STAGED_MODULE_that_DISAPPEARED_is_also_drift(self):
        _chosen, prepared = self.staged()
        os.unlink(os.path.join(prepared["staged_source"]["path"], "tools",
                               "stage_execution.py"))
        with self.assertRaises(PacketRefusal) as raised:
            self._bind()
        self.assertIn("CHANGED since `stage`", str(raised.exception))

    def test_a_HELPER_MODULE_CHANGED_after_stage_is_refused(self):
        """R4: `correction_packet.py` is imported by the supervisor, lives
        outside the staged packages, and was bound by nothing at all.
        """
        _chosen, prepared = self.staged()
        self.edited(os.path.join(self.destination, "prepared.json"),
                    lambda held: held["preparation_modules"].__setitem__(
                        "correction_supervisor.py", "00" * 32))
        del prepared
        with self.assertRaises(PacketRefusal) as raised:
            self._bind()
        self.assertIn("correction_supervisor.py", str(raised.exception))
        self.assertIn("refuses drift", str(raised.exception))

    def test_a_MISSING_retained_manifest_refuses_rather_than_re_measuring(self):
        _chosen, _prepared = self.staged()
        self.edited(os.path.join(self.destination, "prepared.json"),
                    lambda held: held.pop("staged_source"))
        with self.assertRaises(PacketRefusal) as raised:
            self._bind()
        self.assertIn("retains no staged-source manifest",
                      str(raised.exception))

    def test_an_UNCHANGED_preparation_binds(self):
        """The positive half: drift is refused, and NOT everything is drift."""
        self.staged()
        path = self._bind()
        self.assertTrue(os.path.exists(path))
        packets.held_packet(path)


class ThePacketProvesWhatItBinds(Fixture):

    def test_a_generated_packet_proves(self):
        _chosen, path = self.packet()
        held = packets.held_packet(path)
        self.assertEqual(held["schema"], packets.PACKET_SCHEMA)
        self.assertEqual(held["bounds"], dict(packets.BOUNDS))
        self.assertEqual(held["code_boundary"], held["manager_source"]["path"])

    def test_the_BOUNDS_are_this_Job_s_and_cannot_be_widened_in_the_packet(self):
        for name, wider in (("total_seconds", 1800),
                            ("implementer_invocations", 3),
                            ("review_invocations", 3),
                            ("corrections", 2),
                            ("restores", 2),
                            ("turn_seconds", 600),
                            ("retry", True)):
            with self.subTest(bound=name):
                _chosen, path = self.packet()
                self.edited(path, lambda held, n=name, w=wider:
                            held["bounds"].__setitem__(n, w))
                with self.assertRaises(PacketRefusal) as raised:
                    packets.held_packet(path)
                self.assertIn(name, str(raised.exception))

    def test_a_RESERVE_that_is_not_inside_the_total_is_refused(self):
        _chosen, path = self.packet()

        def widen(held):
            held["bounds"]["cleanup_seconds"] = 900
            held["bounds"]["total_seconds"] = 900

        self.edited(path, widen)
        with self.assertRaises(PacketRefusal):
            packets.held_packet(path)

    def test_a_DRIFTED_staged_module_refuses_the_run(self):
        """Review R3: hash listings do not pin imports -- but a moved staged
        file is refused before a store opens."""
        _chosen, path = self.packet()
        held = packets.held_packet(path)
        _write(os.path.join(held["manager_source"]["path"],
                            "tools", "stage_execution.py"), "drifted\n")
        with self.assertRaises(PacketRefusal) as raised:
            packets.held_packet(path)
        self.assertIn("stage_execution.py", str(raised.exception))

    def test_a_DRIFTED_submission_refuses_the_run(self):
        _chosen, path = self.packet()
        _write(os.path.join(self.destination, "submission.json"),
               {"jobs": []})
        with self.assertRaises(PacketRefusal) as raised:
            packets.held_packet(path)
        self.assertIn("Job submission", str(raised.exception))

    def test_a_TASK_DOCUMENT_that_OMITS_a_requirement_refuses_the_run(self):
        """The complete-criteria rule, checked where the criteria live. R1: the
        submission contract has no acceptance text at all, so the old negative
        was mutating members the real parser refuses outright.
        """
        _chosen, path = self.packet()
        task = os.path.join(self.destination, "task.json")

        def hide(held):
            held["instructions"] = held["instructions"].replace(
                packets.CRITERIA[3], "")

        self.edited(task, hide)
        self.edited(path, lambda held: held["submission"].__setitem__(
            "task_sha256", packets.digest_of(task)))
        with self.assertRaises(PacketRefusal) as raised:
            packets.held_packet(path)
        self.assertIn("manufactured correction", str(raised.exception))

    def test_a_MANIFEST_that_binds_OTHER_task_bytes_refuses_the_run(self):
        """`single_worker._held` compares the worker's task.json against the
        manifest's human contract, so a manifest bound to other bytes means the
        worker receives requirements this packet never checked.
        """
        _chosen, path = self.packet()
        manifest = os.path.join(self.destination, "input-manifest.json")
        self.edited(manifest, lambda held: held["human_contract"].__setitem__(
            "content_digest", OTHER))
        self.edited(path, lambda held: held["submission"].__setitem__(
            "manifest_sha256", packets.digest_of(manifest)))
        with self.assertRaises(PacketRefusal) as raised:
            packets.held_packet(path)
        self.assertIn("does not bind these task bytes", str(raised.exception))

    def test_a_THIRD_stage_refuses_the_run(self):
        """A VALID third stage -- `integration` is a real stage kind with every
        required member -- so the real parser accepts it and this packet's own
        two-stage rule is what refuses.
        """
        _chosen, path = self.packet()
        submission = os.path.join(self.destination, "submission.json")
        accepted = packets._accepted()
        self.edited(submission, lambda held: held["jobs"][0]["stages"].append(
            {"kind": "integration", "work_id": WORK_ID,
             "profile_name": accepted["profile_name"],
             "profile_digest": accepted["profile_digest"],
             "depends_on": []}))
        self.edited(path, lambda held: held["submission"].__setitem__(
            "sha256", packets.digest_of(submission)))
        with self.assertRaises(PacketRefusal) as raised:
            packets.held_packet(path)
        self.assertIn("one independent review", str(raised.exception))

    def test_a_REVIEW_that_does_NOT_DEPEND_on_the_work_refuses_the_run(self):
        """Nothing else orders the review after the implementation."""
        _chosen, path = self.packet()
        submission = os.path.join(self.destination, "submission.json")
        self.edited(submission, lambda held: held["jobs"][0]["stages"][1]
                    .__setitem__("depends_on", []))
        self.edited(path, lambda held: held["submission"].__setitem__(
            "sha256", packets.digest_of(submission)))
        with self.assertRaises(PacketRefusal) as raised:
            packets.held_packet(path)
        self.assertIn("does not depend on", str(raised.exception))

    def test_a_DROPPED_LIMIT_refuses_the_run(self):
        """A bound the parser drops is a bound this run does not have."""
        _chosen, path = self.packet()
        submission = os.path.join(self.destination, "submission.json")
        self.edited(submission, lambda held: held["jobs"][0]
                    ["execution_limits"].__setitem__("provider_turn_seconds",
                                                     600))
        self.edited(path, lambda held: held["submission"].__setitem__(
            "sha256", packets.digest_of(submission)))
        with self.assertRaises(PacketRefusal) as raised:
            packets.held_packet(path)
        self.assertIn("execution limits", str(raised.exception))

    def test_an_INVALID_submission_is_refused_BY_THE_REAL_PARSER(self):
        """And the refusal travels with the parser's own words, so a reviewer
        sees what the build actually objected to.
        """
        _chosen, path = self.packet()
        submission = os.path.join(self.destination, "submission.json")
        self.edited(submission, lambda held: held.pop("submission_id"))
        self.edited(path, lambda held: held["submission"].__setitem__(
            "sha256", packets.digest_of(submission)))
        with self.assertRaises(PacketRefusal) as raised:
            packets.held_packet(path)
        self.assertIn("not one this build accepts", str(raised.exception))
        self.assertIn("submission_id", str(raised.exception))

    def test_a_GRANT_for_another_Job_refuses_the_run(self):
        _chosen, path = self.packet()
        self.edited(path, lambda held: held["context"].__setitem__(
            "job_id", "job-somebody-else"))
        with self.assertRaises(PacketRefusal) as raised:
            packets.held_packet(path)
        self.assertIn("one grant serves exactly one Job", str(raised.exception))

    def test_a_PRODUCTION_qualification_refuses_the_run(self):
        _chosen, path = self.packet()
        self.edited(path, lambda held: held["context"].__setitem__(
            "qualification", "production"))
        with self.assertRaises(PacketRefusal) as raised:
            packets.held_packet(path)
        self.assertIn("coverage limit", str(raised.exception))

    def test_MUTABLE_STATE_inside_the_code_boundary_refuses_the_run(self):
        _chosen, path = self.packet()
        held = packets.held_packet(path)
        inside = os.path.join(held["manager_source"]["path"], "jobs.sqlite3")
        self.edited(path, lambda one: one["deployment"].__setitem__(
            "job_store", inside))
        with self.assertRaises(PacketRefusal) as raised:
            packets.held_packet(path)
        self.assertIn("inside the code boundary", str(raised.exception))

    def test_a_CODE_BOUNDARY_that_is_not_the_staged_source_refuses_the_run(self):
        """Refused either by the boundary rule or, earlier, by the enclosing
        composition validator reading that same boundary -- both are this fault
        and neither path admits it.
        """
        _chosen, path = self.packet()
        self.edited(path, lambda held: held.__setitem__("code_boundary",
                                                        self.root))
        with self.assertRaises(PacketRefusal) as raised:
            packets.held_packet(path)
        said = str(raised.exception)
        self.assertTrue("not the staged manager source" in said
                        or "belongs outside the working tree" in said, said)

    def test_an_UNPINNED_provenance_record_refuses_the_run(self):
        """Review R3: name canonical provenance for reused bytes. A record
        named and not checked is a footnote."""
        _chosen, path = self.packet()
        _write(self.provenance_record, {"image": "something else"})
        with self.assertRaises(PacketRefusal) as raised:
            packets.held_packet(path)
        self.assertIn("provenance record", str(raised.exception))

    def test_NO_provenance_record_at_all_refuses_the_run(self):
        _chosen, path = self.packet()
        self.edited(path, lambda held: held.__setitem__("provenance", {}))
        with self.assertRaises(PacketRefusal) as raised:
            packets.held_packet(path)
        self.assertIn("canonical provenance", str(raised.exception))

    def test_an_UNSTATED_LIMIT_refuses_the_run(self):
        """"no-build-required is not established solely by prior fresh-Job
        acceptance" -- so the packet must carry what it does NOT establish, and
        an empty list reads as coverage."""
        _chosen, path = self.packet()
        self.edited(path, lambda held: held["compatibility"].__setitem__(
            "not_established", []))
        with self.assertRaises(PacketRefusal) as raised:
            packets.held_packet(path)
        self.assertIn("unstated limit", str(raised.exception))

    def test_a_PROFILE_that_stopped_matching_the_image_refuses_the_run(self):
        _chosen, path = self.packet()
        profile = os.path.join(self.destination, "context-profile.json")
        self.edited(profile, lambda held: held.__setitem__("image_digest",
                                                          OTHER))
        self.edited(path, lambda held: held["context"].__setitem__(
            "profile_sha256", packets.digest_of(profile)))
        with self.assertRaises(PacketRefusal) as raised:
            packets.held_packet(path)
        self.assertIn("composed against image", str(raised.exception))

    def test_ANOTHER_program_claiming_to_be_the_supervisor_is_refused(self):
        _chosen, path = self.packet()
        with self.assertRaises(PacketRefusal) as raised:
            packets.held_packet(path, supervisor=__file__)
        self.assertIn("this process is running", str(raised.exception))

    def test_the_WHOLE_CLI_runs_end_to_end_with_the_REAL_profile_digest(self):
        """stage -> bind -> check, through `main`, with nothing mocked.

        THE DIGEST IS THE MANAGER'S. `certify_context_profile` keys the
        certification on `digest(_profile(profile))`, which is NOT the file's
        sha256 -- an earlier draft bound the file digest and `baseline.prepare`
        would have refused the run AFTER the instance was installed and the
        one-run grant minted. This case runs the real computation, so that
        cannot come back.
        """
        from baton_v12.contracts import digest
        from baton_v12.worker_manager.provider_context import _profile

        selections = self.selections()
        provenance = _write(
            os.path.join(self.root, "provenance.json"),
            {"provenance": {"worker_image": {
                "path": self.provenance_record,
                "sha256": packets.digest_of(self.provenance_record)}},
             "compatibility": {"adapter_source_sha256": "18" * 32,
                               "context_capable": True,
                               "established": ["measured"],
                               "not_established": ["the production branch"]}})
        stream = io.StringIO()
        self.assertEqual(packets.main(
            ["stage", "--selections", selections,
             "--destination", self.destination, "--claim", "309356",
             "--provenance", provenance], stream=stream), 0)
        _write(os.path.join(self.instance, "bootstrap.json"),
               {"authority_uuid": "7ea319da93384b77bc3ddea38602d7a3"})
        _write(os.path.join(self.instance, "deployment.json"),
               {"job_bindings": [{
                   "job_id": "job-managed-correction-test",
                   "job_work_id": WORK_ID,
                   "review_work_id": WORK_ID,
                   "source_worker_id": "implementation-worker"}],
                "workers": [{"worker_id": "w", "deployment": {
                    "workspace_storage": os.path.join(self.instance, "run",
                                                      "workspaces")}}]})
        stream = io.StringIO()
        self.assertEqual(packets.main(
            ["bind", "--selections", selections,
             "--destination", self.destination, "--claim", "309356",
             "--provenance", provenance], stream=stream), 0)
        path = json.loads(stream.getvalue())["packet"]
        stream = io.StringIO()
        self.assertEqual(
            packets.main(["check", "--packet", path], stream=stream), 0)
        held = packets.held_packet(path)
        self.assertEqual(held["context"]["profile_digest"],
                         digest(_profile(self.profile())))
        self.assertNotEqual(held["context"]["profile_digest"],
                            "sha256:" + held["context"]["profile_sha256"])

    def test_the_CHECK_subcommand_proves_a_packet_and_prints_it(self):
        _chosen, path = self.packet()
        stream = io.StringIO()
        self.assertEqual(
            packets.main(["check", "--packet", path], stream=stream), 0)
        answered = json.loads(stream.getvalue())
        self.assertIs(answered["proved"], True)
        self.assertEqual(answered["bounds"], dict(packets.BOUNDS))


# -- the bounds, enforced ---------------------------------------------------

class TheReusedMachineryIsPinned(unittest.TestCase):

    def test_the_accepted_baseline_digest_is_the_one_on_disk(self):
        self.assertEqual(supervisor.verify_baseline(),
                         supervisor.BASELINE_SHA256)

    def test_a_DRIFTED_baseline_refuses_the_run(self):
        import tempfile

        with tempfile.NamedTemporaryFile("w", suffix=".py") as handle:
            handle.write("# not the accepted supervisor\n")
            handle.flush()
            with self.assertRaises(packets.PacketRefusal) as raised:
                supervisor.verify_baseline(path=handle.name)
        self.assertIn("a changed copy is a changed bound",
                      str(raised.exception))


class TheOutcomesAreClassifiedSeparately(unittest.TestCase):
    """Review R2: "Retain separate accepted/no-correction/rejected/failed
    outcomes and never force review feedback." Five endings, and no
    fall-through that becomes an acceptance."""

    def _classify(self, **changes):
        held = {"stop": "completed", "disposition": supervisor.ACCEPTED,
                "implementations": 1, "reviews": 1,
                "continuity": {"continued": False, "why": "none"},
                "cleanup_outstanding": [], "interrupted": None}
        held.update(changes)
        return supervisor.classify(**held)

    def test_ACCEPTED_WITH_NO_CORRECTION_settles_and_claims_no_restore(self):
        outcome, reasons = self._classify()
        self.assertEqual(outcome, supervisor.ACCEPTED_NO_CORRECTION)
        self.assertEqual(reasons, [])

    def test_CORRECTED_AND_ACCEPTED_requires_the_continued_conversation(self):
        outcome, reasons = self._classify(
            implementations=2, reviews=2,
            continuity={"continued": True, "why": None})
        self.assertEqual(outcome, supervisor.CORRECTED_AND_ACCEPTED)
        self.assertEqual(reasons, [])

    def test_a_SECOND_implementation_without_continuity_is_NOT_a_correction(self):
        outcome, reasons = self._classify(
            implementations=2, reviews=2,
            continuity={"continued": False,
                        "why": "a fresh conversation is not a restored one"})
        self.assertEqual(outcome, supervisor.FAILED)
        self.assertIn("did not demonstrably continue", " ".join(reasons))

    def test_REJECTED_is_a_valid_result_and_nothing_is_manufactured_from_it(self):
        outcome, reasons = self._classify(disposition=supervisor.REJECTED,
                                          reviews=1)
        self.assertEqual(outcome, supervisor.REVIEW_REJECTED)
        self.assertEqual(reasons, [])

    def test_CHANGES_REQUESTED_that_was_never_answered_is_its_own_outcome(self):
        outcome, reasons = self._classify(
            disposition=supervisor.CHANGES_REQUESTED)
        self.assertEqual(outcome, supervisor.UNANSWERED)
        self.assertIn("the correction was not completed", " ".join(reasons))

    def test_an_UNREAD_disposition_is_UNKNOWN_and_never_an_acceptance(self):
        outcome, reasons = self._classify(disposition=None)
        self.assertEqual(outcome, supervisor.FAILED)
        self.assertIn("never an acceptance", " ".join(reasons))

    def test_a_TIMEOUT_holds_the_run_whatever_the_reviewer_said(self):
        outcome, reasons = self._classify(stop="timed-out")
        self.assertEqual(outcome, supervisor.FAILED)
        self.assertIn("timed-out", " ".join(reasons))

    def test_an_INTERRUPTION_holds_the_run(self):
        outcome, reasons = self._classify(interrupted="KeyboardInterrupt: ")
        self.assertEqual(outcome, supervisor.FAILED)
        self.assertIn("interrupted", " ".join(reasons))

    def test_UNPROVED_CLEANUP_holds_the_run(self):
        outcome, reasons = self._classify(cleanup_outstanding=["att-1"])
        self.assertEqual(outcome, supervisor.FAILED)
        self.assertIn("att-1", " ".join(reasons))

    def test_NO_RUNTIME_AT_ALL_answers_nothing(self):
        outcome, reasons = self._classify(implementations=0, reviews=0)
        self.assertEqual(outcome, supervisor.FAILED)
        self.assertIn("answered nothing", " ".join(reasons))


class TheRestoreIsReadFromTheJournal(unittest.TestCase):
    """Continuity is two journal facts and no inference, and absence is
    absence."""

    def _continuity(self, opening, restored):
        from baton_v12.worker_manager import provider_context

        answers = {"open": opening, "new": restored}
        with mock.patch.object(provider_context, "context_use_of",
                               side_effect=lambda _c, one: answers[one]):
            return supervisor.context_continuity(None, opening="open",
                                                 restored="new")

    def test_ONE_CONTEXT_and_a_LATER_generation_is_continuity(self):
        held = self._continuity({"context_id": "c1", "generation": 0,
                                 "status": "ready"},
                                {"context_id": "c1", "generation": 1,
                                 "status": "admitted"})
        self.assertIs(held["continued"], True)

    def test_a_DIFFERENT_context_is_a_fresh_conversation(self):
        held = self._continuity({"context_id": "c1", "generation": 0,
                                 "status": "ready"},
                                {"context_id": "c2", "generation": 1,
                                 "status": "admitted"})
        self.assertIs(held["continued"], False)
        self.assertIn("fresh conversation", held["why"])

    def test_the_SAME_generation_is_not_a_restore(self):
        held = self._continuity({"context_id": "c1", "generation": 0,
                                 "status": "ready"},
                                {"context_id": "c1", "generation": 0,
                                 "status": "admitted"})
        self.assertIs(held["continued"], False)
        self.assertIn("consumes a SAVED generation", held["why"])

    def test_a_FAILED_SAVE_is_not_successful_reuse(self):
        held = self._continuity({"context_id": "c1", "generation": 0,
                                 "status": "held"},
                                {"context_id": "c1", "generation": 1,
                                 "status": "admitted"})
        self.assertIs(held["continued"], False)
        self.assertIn("failed save is not successful reuse", held["why"])

    def test_an_UNREADABLE_journal_is_not_continuity(self):
        from baton_v12.worker_manager import provider_context

        with mock.patch.object(provider_context, "context_use_of",
                               side_effect=RuntimeError("no journal")):
            held = supervisor.context_continuity(None, opening="a",
                                                 restored="b")
        self.assertIs(held["continued"], False)
        self.assertIn("no journal", held["why"])


class TheBoundsAreEnforced(Fixture):
    """The real bounded loop, with a scripted clock and a scripted manager.

    WHAT IS REPLACED, named: `submit`, `serve`, `sweep`, the attempt/limit read
    and the cleanup read. Everything the supervisor itself decides -- the
    deadline arithmetic, the reserve, the stop conditions, the closed gate and
    the published outcome -- is the code under test.
    """

    def _run(self, *, ticks, states, seen=None, interrupt=False,
             during=None, cancelled=None, interrupt_cleanup=False,
             chronology=None, outstanding=(), signal_in_cleanup=False,
             signal_at_publication=False):
        from baton_v12 import job_manager

        _chosen, path = self.packet()
        packet = packets.held_packet(path)
        clock = {"now": 0.0}

        def monotonic():
            return clock["now"]

        def advance(_seconds=1):
            clock["now"] += 1

        answers = list(states)
        observed = []

        def attempts(_job, _operations, _job_id):
            held = answers[min(len(observed), len(answers) - 1)]
            observed.append(held)
            return (dict(seen or {}), dict(held), {"boundaries": {}})

        def serving(_job, gate, **named):
            """The manager's own loop shape: predicate, tick, predicate."""
            self.gate = gate
            for _ in range(ticks):
                if not named["should_continue"]():
                    return
                if during is not None:
                    during(gate)
                clock["now"] += 1
                if interrupt:
                    raise KeyboardInterrupt()

        # THE SHUTDOWN'S OWN DEPENDENCIES ARE SCRIPTED, not left to fail into
        # `uncertainty`. A first version of these cases left `_cancel_active`
        # and the chronology read unpatched, so they were guarded, recorded as
        # unread and the cases still passed -- which is the shutdown NOT being
        # tested while it looks like it is.
        self.cancelled = []

        def cancelling(_operations, _control, _packet, admitted, _states,
                       _uncertainty, *, reason, launched=(), interrupted=None):
            del interrupted
            self.cancelled.append({"admitted": sorted(admitted),
                                   "reason": reason,
                                   "launched": sorted(launched)})
            return dict(cancelled or {})

        real_publish = supervisor.baseline._publish

        def publishing(path, document):
            """THE ONE UNGUARDED STEP. A signal arriving here with the handler
            still raising kills the process with nothing on disk, which is what
            `termination.defer()` exists to prevent.
            """
            if signal_at_publication:
                self.termination._handle(2, None)
            return real_publish(path, document)

        def waiting(_seconds=1):
            clock["now"] += 1
            if signal_in_cleanup:
                # A REAL SIGNAL, delivered to the installed handler rather than
                # an exception this test raises: that is the only way to
                # observe whether the interrupts are DEFERRED.
                self.termination._handle(2, None)
            if interrupt_cleanup:
                raise KeyboardInterrupt("during cleanup")

        self.gate = None
        self.termination = None
        real_termination = supervisor.baseline.Termination

        def watching():
            self.termination = real_termination()
            return self.termination

        with mock.patch.object(supervisor.baseline, "Termination",
                               watching), \
             mock.patch.object(job_manager, "submit",
                               return_value={"submission_id": "s-1"}), \
             mock.patch.object(job_manager, "read_submission",
                               side_effect=lambda text: json.loads(text)), \
             mock.patch.object(job_manager, "serve", serving), \
             mock.patch.object(job_manager, "sweep",
                               side_effect=lambda *a, **k: None), \
             mock.patch.object(supervisor.baseline, "_attempts_of", attempts), \
             mock.patch.object(supervisor.baseline, "_turn_ceiling",
                               return_value={"seconds": 180}), \
             mock.patch.object(supervisor.baseline, "_cleanups",
                               return_value={"cleanup": {}, "outstanding":
                                             list(outstanding)}), \
             mock.patch.object(supervisor.baseline, "survey",
                               return_value={"preexisting_jobs": [],
                                             "accounting_scope": "this run"}), \
             mock.patch.object(supervisor.baseline, "_cancel_active",
                               cancelling), \
             mock.patch.object(supervisor, "stage_episodes",
                               return_value=dict(chronology or {})), \
             mock.patch.object(supervisor.baseline, "_publish", publishing):
            return supervisor.supervise(
                object(), object(), mock.MagicMock(), packet,
                clock=lambda: "2026-09-29T00:00:00.000Z", sleep=waiting,
                monotonic=monotonic,
                disposition=lambda *a: supervisor.ACCEPTED)

    def test_the_RESERVE_is_inside_the_total_and_serving_gets_the_rest(self):
        outcome = self._run(ticks=0, states=[{}])
        self.assertEqual(outcome["serving_seconds"], 840)
        self.assertEqual(outcome["reserved_seconds"], 60)
        self.assertEqual(outcome["serving_seconds"]
                         + outcome["reserved_seconds"], 900)

    def test_SERVING_STOPS_at_its_deadline_rather_than_running_on(self):
        outcome = self._run(ticks=5000,
                            states=[{"implementation": "executing",
                                     "review": "waiting"}])
        self.assertEqual(outcome["stopped"], "overall-bound-exceeded")
        self.assertLessEqual(outcome["serving_seconds_spent"], 841)
        self.assertGreaterEqual(outcome["serving_seconds_spent"], 840)

    def test_BOTH_STAGES_COMPLETED_stops_the_run_early(self):
        outcome = self._run(ticks=5000,
                            states=[{"implementation": "completed",
                                     "review": "completed"}])
        self.assertEqual(outcome["stopped"], "completed")
        self.assertLess(outcome["serving_seconds_spent"], 10)

    def test_an_EXCEPTIONAL_stage_stops_the_run_and_never_retries(self):
        outcome = self._run(ticks=5000,
                            states=[{"implementation": "exceptional"}])
        self.assertEqual(outcome["stopped"], "exceptional")
        self.assertIs(outcome["retry"], False)
        self.assertEqual(outcome["outcome"], supervisor.FAILED)

    def test_a_RUN_THAT_STOPPED_MOVING_says_so_rather_than_spending_the_bound(self):
        outcome = self._run(ticks=5000,
                            states=[{"implementation": "executing",
                                     "review": "waiting"}],
                            seen={"att-1": "implementation"})
        self.assertEqual(outcome["stopped"], "no-progress")
        self.assertLess(outcome["serving_seconds_spent"], 30)

    def test_a_SPENT_INVOCATION_CAP_ends_the_run_instead_of_waiting_it_out(self):
        """Spinning to the overall bound would be the same answer 800 seconds
        later, so a cap refusal is the end of the run."""
        def spend(gate):
            from baton_v12.contracts import ContractRefusal

            for number in range(3):
                try:
                    gate.admit({"kind": "implementation",
                                "job_id": "job-managed-correction-test",
                                "stage_id": f"s-{number}"}, None)
                except ContractRefusal:
                    pass

        outcome = self._run(ticks=5000,
                            states=[{"implementation": "executing",
                                     "review": "waiting"}],
                            during=spend)
        self.assertEqual(outcome["stopped"], "invocation-cap-refused")
        self.assertEqual(outcome["admissions"],
                         {"implementation": 2, "review": 0})
        self.assertIn("all of them are spent",
                      " ".join(outcome["held_because"]))

    def test_the_CLEANUP_WINDOW_cannot_admit_anything(self):
        outcome = self._run(ticks=5000,
                            states=[{"implementation": "completed",
                                     "review": "completed"}])
        self.assertEqual(outcome["intruders"], [])
        # THE GATE IS CLOSED, asked of the gate rather than inferred from an
        # empty list. An admission attempted in the reserve refuses.
        from baton_v12.contracts import ContractRefusal

        self.assertTrue(self.gate.stopped)
        with self.assertRaises(ContractRefusal) as raised:
            self.gate.admit({"kind": "implementation",
                             "job_id": "job-managed-correction-test",
                             "stage_id": "late"}, None)
        self.assertIn("admission is closed", str(raised.exception))

    def test_a_TIMEOUT_with_an_ACTIVE_RUNTIME_orders_the_STOP(self):
        """Review 2026-09-29T21-41-08Z R2: closing the gate stops the NEXT
        runtime and does nothing about one already waiting on a provider turn,
        and a sweep has nothing to finish while it waits -- so my first version
        would have reported `held` with the container still running and the
        engine never asked to stop it.
        """
        outcome = self._run(ticks=5000,
                            states=[{"implementation": "executing",
                                     "review": "waiting"}],
                            seen={"att-1": "implementation"},
                            cancelled={"att-1": {"requested": True}})
        self.assertEqual(len(self.cancelled), 1)
        self.assertIn("att-1", self.cancelled[0]["admitted"])
        self.assertEqual(self.cancelled[0]["reason"], outcome["stopped"])
        self.assertEqual(outcome["cancellation"],
                         {"att-1": {"requested": True}})

    def test_a_LAUNCH_THEN_FAULT_is_still_accounted_for(self):
        """R2: attempts were copied only from the LAST predicate, so an
        admission followed by a fault before the next tick was omitted from
        cleanup accounting entirely. The union with `gate.launched` is what
        makes a launch this process performed impossible to lose.
        """
        def launch_then_fault(gate):
            gate.launched["att-faulted"] = "implementation"
            raise RuntimeError("the deployment faulted after the launch")

        outcome = self._run(ticks=5000,
                            states=[{"implementation": "executing",
                                     "review": "waiting"}],
                            during=launch_then_fault)
        self.assertEqual(outcome["stopped"], "serving-failed")
        self.assertIn("att-faulted", outcome["observed_attempts"])
        self.assertIn("att-faulted", self.cancelled[0]["admitted"])
        self.assertIn("att-faulted", self.cancelled[0]["launched"])

    def test_a_SIGNAL_DURING_CLEANUP_is_DEFERRED_and_still_reported(self):
        """R2: `termination.defer()` was omitted, so a signal arriving during
        the shutdown would have been RAISED out of the cleanup window by the
        installed handler -- killing the accounting before publication. With
        the interrupts deferred the window finishes, the outcome is retained,
        and the interruption is re-raised afterwards rather than lost.
        """
        with self.assertRaises(supervisor.baseline.SupervisorInterrupted) \
                as raised:
            self._run(ticks=5000,
                      states=[{"implementation": "executing",
                               "review": "waiting"}],
                      seen={"att-1": "implementation"},
                      outstanding=["att-1"], signal_in_cleanup=True)
        retained = raised.exception.outcome
        # THE ACCOUNTING COMPLETED: the cancellation ran and the cleanup was
        # read, which is what a raised signal would have prevented.
        self.assertEqual(len(self.cancelled), 1)
        self.assertIn("signal 2", " ".join(retained["interruptions"]))
        self.assertEqual(retained["state"], "held")
        with open(os.path.join(self.instance, "run", "outcome.json"),
                  encoding="utf-8") as handle:
            self.assertEqual(json.load(handle)["outcome"], supervisor.FAILED)

    def test_a_SIGNAL_AT_PUBLICATION_cannot_lose_the_outcome(self):
        """R2's deferral, at the one step that is not guarded.

        Every shutdown step runs inside `_guarded`, so a signal there is caught
        whatever mode the handler is in. Publication is not: with the handler
        still RAISING, a signal delivered while the outcome is being written
        leaves nothing on disk at all. Deferred, the write completes and the
        interruption is re-raised after it.
        """
        with self.assertRaises(supervisor.baseline.SupervisorInterrupted) \
                as raised:
            self._run(ticks=5000,
                      states=[{"implementation": "completed",
                               "review": "completed"}],
                      seen={"att-1": "implementation"},
                      signal_at_publication=True)
        self.assertIn("signal 2",
                      " ".join(raised.exception.outcome["interruptions"]))
        with open(os.path.join(self.instance, "run", "outcome.json"),
                  encoding="utf-8") as handle:
            self.assertEqual(json.load(handle)["run_id"],
                             "managed-correction-test")

    def test_a_SECOND_INTERRUPT_DURING_CLEANUP_cannot_escape(self):
        """R2: `sleep` in the cleanup window was outside a guarded step, so
        another SIGINT could escape before the outcome was published. The
        interrupts are deferred and the wait is guarded, so the window ends,
        the interruption is reported, and the outcome is still retained.
        """
        with self.assertRaises(supervisor.baseline.SupervisorInterrupted) \
                as raised:
            self._run(ticks=5000,
                      states=[{"implementation": "executing",
                               "review": "waiting"}],
                      seen={"att-1": "implementation"},
                      interrupt=True, interrupt_cleanup=True,
                      outstanding=["att-1"])
        retained = raised.exception.outcome
        self.assertEqual(retained["state"], "held")
        self.assertIn("during cleanup",
                      " ".join(retained["uncertainty"]) + " "
                      + " ".join(retained["interruptions"]))
        with open(os.path.join(self.instance, "run", "outcome.json"),
                  encoding="utf-8") as handle:
            self.assertEqual(json.load(handle)["outcome"], supervisor.FAILED)

    def test_the_RECORDED_CHRONOLOGY_decides_the_attempt_order(self):
        """Not the spelling: the restored attempt sorts first lexically."""
        outcome = self._run(
            ticks=5000,
            states=[{"implementation": "completed", "review": "completed"}],
            seen={"aaa-restored": "implementation",
                  "zzz-opening": "implementation"},
            chronology={"implementation": ["zzz-opening", "aaa-restored"]})
        self.assertEqual(outcome["implementation_attempts"],
                         ["zzz-opening", "aaa-restored"])

    def test_an_INTERRUPTION_publishes_the_outcome_BEFORE_it_raises(self):
        with self.assertRaises(supervisor.baseline.SupervisorInterrupted) \
                as raised:
            self._run(ticks=5000,
                      states=[{"implementation": "executing",
                               "review": "waiting"}],
                      interrupt=True)
        retained = raised.exception.outcome
        self.assertEqual(retained["outcome"], supervisor.FAILED)
        self.assertEqual(retained["state"], "held")
        self.assertIn("interrupted", " ".join(retained["held_because"]))
        # AND IT IS ON DISK, which is the half an operator actually needs.
        with open(os.path.join(self.instance, "run", "outcome.json"),
                  encoding="utf-8") as handle:
            self.assertEqual(json.load(handle)["outcome"], supervisor.FAILED)


class TheInvocationCapsAreTheGate(Fixture):
    """Review R2: "Textual limits are not evidence that two implementer/two
    reviewer invocations and one restore will be enforced.\""""

    def _gate(self):
        from baton_v12.contracts import ContractRefusal

        operations = mock.MagicMock()
        operations.admit.return_value = {"admitted": True}
        gate = supervisor.baseline.AdmissionGate(
            operations, job_id="job-1",
            caps={"implementation": packets.BOUNDS["implementer_invocations"],
                  "review": packets.BOUNDS["review_invocations"]})
        return gate, operations, ContractRefusal

    def _stage(self, kind, number):
        return {"kind": kind, "job_id": "job-1",
                "stage_id": f"{kind}-{number}"}

    def test_TWO_implementer_invocations_are_admitted_and_a_THIRD_is_not(self):
        gate, operations, refusal = self._gate()
        gate.admit(self._stage("implementation", 1), None)
        gate.admit(self._stage("implementation", 2), None)
        with self.assertRaises(refusal) as raised:
            gate.admit(self._stage("implementation", 3), None)
        self.assertIn("all of them are spent", str(raised.exception))
        self.assertEqual(operations.admit.call_count, 2)

    def test_TWO_review_invocations_are_a_SEPARATE_permission(self):
        gate, _operations, refusal = self._gate()
        gate.admit(self._stage("implementation", 1), None)
        gate.admit(self._stage("review", 1), None)
        gate.admit(self._stage("review", 2), None)
        with self.assertRaises(refusal):
            gate.admit(self._stage("review", 3), None)
        self.assertEqual(gate.admissions,
                         {"implementation": 1, "review": 2})

    def test_ANOTHER_JOB_S_stage_never_reaches_the_deployment(self):
        gate, operations, refusal = self._gate()
        with self.assertRaises(refusal):
            gate.admit({"kind": "implementation", "job_id": "job-else",
                        "stage_id": "s"}, None)
        self.assertEqual(operations.admit.call_count, 0)
        self.assertEqual(gate.admissions["implementation"], 0)

    def test_a_CLOSED_gate_admits_nothing_at_all(self):
        gate, operations, refusal = self._gate()
        gate.stop()
        with self.assertRaises(refusal):
            gate.admit(self._stage("implementation", 1), None)
        self.assertEqual(operations.admit.call_count, 0)


class TheDispositionIsNeverManufactured(unittest.TestCase):
    """Review 2026-09-29T21-41-08Z R3: the old reader searched
    `stage.disposition/verdict/result`, which the real projection never emits,
    so every real run would have answered `failed-or-unknown` -- and the
    positive test passed because it supplied a `disposition` field of its own
    invention. These drive the SUPPORTED readers instead.
    """

    def _read(self, *, attachment, verdict, record=None, episodes=("att-r1",),
              generation=1, attachments=None, records=None):
        from baton_v12.worker_manager import attempts as attempt_facts
        from baton_v12.worker_manager import review_cycles

        control = mock.MagicMock()
        if records is None:
            control.operation_record.return_value = record
        else:
            control.operation_record.side_effect = \
                lambda key: records.get(key)

        def attaching(_control, *, attempt_id, generation):
            del generation
            if attachments is None:
                return attachment
            return attachments.get(attempt_id)

        with mock.patch.object(supervisor, "stage_episodes",
                               return_value={"review": list(episodes)}), \
             mock.patch.object(attempt_facts, "assignment_of",
                               return_value={"generation": generation}), \
             mock.patch.object(review_cycles, "review_for_attempt",
                               attaching), \
             mock.patch.object(review_cycles, "verdict_of",
                               return_value=verdict):
            return supervisor.review_disposition(control, None, None, "job-1")

    def _committed(self, verdict_id="verdict-1"):
        return {"state": "committed",
                "result": json.dumps({"verdict_id": verdict_id})}

    def test_the_reviewers_own_verdict_is_read_through_the_owner_readers(self):
        from baton_v12.worker_manager import review_cycles

        for said in review_cycles.DISPOSITIONS:
            with self.subTest(disposition=said):
                self.assertEqual(
                    self._read(attachment={"attachment_id": "a-1"},
                               verdict={"disposition": said},
                               record=self._committed()),
                    said)

    def test_NO_ATTACHMENT_answers_nothing_rather_than_a_default(self):
        self.assertIsNone(self._read(attachment=None, verdict=None))

    def test_an_UNCOMMITTED_verdict_act_answers_nothing(self):
        self.assertIsNone(self._read(
            attachment={"attachment_id": "a-1"},
            verdict={"disposition": "accepted"},
            record={"state": "prepared",
                    "result": json.dumps({"verdict_id": "v-1"})}))

    def test_an_UNRECOGNIZED_disposition_answers_nothing(self):
        self.assertIsNone(self._read(attachment={"attachment_id": "a-1"},
                                     verdict={"disposition": "looks fine"},
                                     record=self._committed()))

    def test_a_REFUSING_owner_reader_answers_nothing_and_never_accepts(self):
        from baton_v12.worker_manager import attempts as attempt_facts
        from baton_v12.worker_manager import review_cycles

        control = mock.MagicMock()
        control.operation_record.return_value = self._committed()
        with mock.patch.object(supervisor, "stage_episodes",
                               return_value={"review": ["att-r1"]}), \
             mock.patch.object(attempt_facts, "assignment_of",
                               return_value={"generation": 1}), \
             mock.patch.object(review_cycles, "review_for_attempt",
                               return_value={"attachment_id": "a-1"}), \
             mock.patch.object(review_cycles, "verdict_of",
                               side_effect=RuntimeError("damaged")):
            self.assertIsNone(
                supervisor.review_disposition(control, None, None, "job-1"))

    def test_a_LATER_UNREAD_review_does_NOT_borrow_the_earlier_verdict(self):
        """Review 2026-09-29T22-02-59Z item 2: "do not borrow an earlier verdict
        to characterize a later unread review."

        My first version walked backwards through every review attempt and
        returned the first verdict it found, so a SECOND review still executing
        would have been reported with the FIRST review's disposition -- the
        opening review's verdict attributed to a correction nobody had judged.
        """
        from baton_v12.worker_manager import review_cycles

        self.assertIsNone(self._read(
            attachment=None, verdict={"disposition": "accepted"},
            episodes=("att-r1", "att-r2"),
            attachments={"att-r1": {"attachment_id": "a-1"}, "att-r2": None},
            record=self._committed()))
        del review_cycles

    def test_the_LATEST_review_is_the_one_that_answers(self):
        """The positive half: when the later review HAS a verdict, that is the
        verdict -- not the earlier one.
        """
        self.assertEqual(
            self._read(attachment=None, verdict={"disposition": "accepted"},
                       episodes=("att-r1", "att-r2"),
                       attachments={"att-r1": {"attachment_id": "a-1"},
                                    "att-r2": {"attachment_id": "a-2"}},
                       records={"review-line.verdict:a-2": self._committed(
                           "verdict-2")}),
            "accepted")

    def test_an_ATTEMPT_WITHOUT_AN_ACTIVATED_ASSIGNMENT_answers_nothing(self):
        """`assignment_of` refuses an attempt that never activated one, and a
        refusal is not a generation to guess around.
        """
        from baton_v12.worker_manager import attempts as attempt_facts

        control = mock.MagicMock()
        with mock.patch.object(supervisor, "stage_episodes",
                               return_value={"review": ["att-r1"]}), \
             mock.patch.object(attempt_facts, "assignment_of",
                               side_effect=RuntimeError("never activated")):
            self.assertIsNone(
                supervisor.review_disposition(control, None, None, "job-1"))

    def test_the_GENERATION_is_DERIVED_from_the_canonical_assignment(self):
        """Not guessed from `(2, 1)`: the invocation caps bound how many
        attempts are admitted, not which assignment generation any of them
        activated, so a review on generation 3 answered `None` before.
        """
        from baton_v12.worker_manager import attempts as attempt_facts
        from baton_v12.worker_manager import review_cycles

        seen = {}

        def attaching(_control, *, attempt_id, generation):
            seen[attempt_id] = generation
            return {"attachment_id": "a-1"}

        control = mock.MagicMock()
        control.operation_record.return_value = self._committed()
        with mock.patch.object(supervisor, "stage_episodes",
                               return_value={"review": ["att-r1"]}), \
             mock.patch.object(attempt_facts, "assignment_of",
                               return_value={"generation": 3}), \
             mock.patch.object(review_cycles, "review_for_attempt",
                               attaching), \
             mock.patch.object(review_cycles, "verdict_of",
                               return_value={"disposition": "accepted"}):
            self.assertEqual(
                supervisor.review_disposition(control, None, None, "job-1"),
                "accepted")
        self.assertEqual(seen, {"att-r1": 3})

    def test_a_NON_POSITIVE_generation_answers_nothing(self):
        from baton_v12.worker_manager import attempts as attempt_facts

        for said in (0, -1, True, None, "2"):
            with self.subTest(generation=said):
                control = mock.MagicMock()
                with mock.patch.object(attempt_facts, "assignment_of",
                                       return_value={"generation": said}):
                    self.assertIsNone(
                        supervisor.assignment_generation(control, "att-r1"))

    def test_the_VERDICT_IDENTITY_is_derived_from_the_attachment(self):
        """`record_verdict` journals under `VERDICT_KIND:<attachment_id>`, so
        the reader asks the journal for that act rather than trusting an
        identity handed to it.
        """
        from baton_v12.worker_manager import review_cycles

        from baton_v12.worker_manager import attempts as attempt_facts

        control = mock.MagicMock()
        control.operation_record.return_value = self._committed()
        with mock.patch.object(supervisor, "stage_episodes",
                               return_value={"review": ["att-r1"]}), \
             mock.patch.object(attempt_facts, "assignment_of",
                               return_value={"generation": 1}), \
             mock.patch.object(review_cycles, "review_for_attempt",
                               return_value={"attachment_id": "a-9"}), \
             mock.patch.object(review_cycles, "verdict_of",
                               return_value={"disposition": "accepted"}):
            supervisor.review_disposition(control, None, None, "job-1")
        control.operation_record.assert_called_with(
            review_cycles.VERDICT_KIND + ":a-9")


class TheChronologyIsTheStoreS(unittest.TestCase):
    """R3: "Random identity spelling is not time." The opening and restored
    attempts are selected from recorded episodes, not from a lexical sort.
    """

    def _episodes(self, stages):
        from baton_v12 import job_manager

        document = {"jobs": [{"job_id": "job-1", "stages": stages}]}
        with mock.patch.object(supervisor.baseline, "_moment",
                               return_value="now"), \
             mock.patch.object(job_manager, "status", return_value=document):
            return supervisor.stage_episodes(None, None, "job-1")

    def test_the_RECORDED_EPISODE_decides_the_order_not_the_spelling(self):
        """The restored attempt sorts FIRST lexically and SECOND in time; a
        lexical reader would have compared continuity the wrong way round.
        """
        held = self._episodes([{
            "kind": "implementation", "attempt_id": None, "episode": None,
            "episodes": [{"episode": 2, "attempt_id": "aaa-restored"},
                         {"episode": 1, "attempt_id": "zzz-opening"}]}])
        self.assertEqual(held["implementation"],
                         ["zzz-opening", "aaa-restored"])
        self.assertNotEqual(held["implementation"],
                            sorted(held["implementation"]))

    def test_the_LIVE_attempt_is_an_episode_too(self):
        """A stage executing its correction right now carries it in
        `attempt_id` and not yet in the history; losing it would lose the very
        attempt this run exists to account for.
        """
        held = self._episodes([{
            "kind": "implementation", "attempt_id": "live", "episode": 2,
            "episodes": [{"episode": 1, "attempt_id": "opening"}]}])
        self.assertEqual(held["implementation"], ["opening", "live"])

    def test_an_attempt_the_PROJECTION_did_not_answer_for_is_not_dropped(self):
        """`_ordered` keeps a runtime this process launched even when the store
        has no episode for it: a launch this run performed is this run's to
        account for either way.
        """
        order = supervisor._ordered(["opening"],
                                    {"opening": "implementation",
                                     "faulted": "implementation"},
                                    "implementation")
        self.assertEqual(order, ["opening", "faulted"])

    def test_another_kinds_attempt_is_not_counted_as_this_one(self):
        order = supervisor._ordered([], {"r-1": "review"}, "implementation")
        self.assertEqual(order, [])


if __name__ == "__main__":                                   # pragma: no cover
    unittest.main()
