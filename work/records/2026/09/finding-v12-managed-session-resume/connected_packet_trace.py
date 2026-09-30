"""THIS PACKET, CONNECTED: real stores, real manager, this packet's own documents.

W236087 item 3's remaining milestone, from review 2026-09-29T22-15-01Z and
2026-09-29T22-23-10Z: "The packet's own submission, generated composition,
preparation and supervisor must be the consumed path; real disposable stores,
actual attachments/verdicts and positive cleanup must decide the observations."

WHAT IS REAL HERE. The Job and control stores, the Authority, the manager's own
serving and sweeping, `stage_execution.operations_from` over THIS packet's
generated deployment, `single_worker._held` and
`stage_execution.held_configuration` over its workers, the candidate
qualification grant through `provider_context.authorize_qualification_run`, the
review attachments and verdicts through `review_cycles`, the context journal, the
cleanup journal, and `correction_supervisor.supervise` itself.

WHAT IS SIMULATED, AND LABELLED. The OCI engine is the accepted fixture's
in-process one and the provider is a real child process running a scripted
script: `correction_restart_trace.World` owns both and this reuses them rather
than building a second harness. Review 2026-09-29T22-15-01Z authorizes exactly
this -- "deterministic fake/replay providers and scripted scenario inputs ARE
authorized and expected... Label them simulated" -- and the prohibition it
restates is on forging an owner receipt or calling a fixture a live independent
judgment, which nothing here does: every verdict below is recorded through the
real owner API by a scripted reviewer, and is labelled a scripted disposition.

WHAT THIS FIXTURE IS NOT. It is not a live run: no deployed store, no deployed
grant, no credential byte, no real engine and no real provider. The stores are
disposable and created per test; the qualification grant is minted in them and
nowhere else. Review 2026-09-29T22-23-10Z: "Candidate qualification in a
disposable deterministic fixture is test state."

THE WORKLOAD IS THIS PACKET'S TWO STAGES, not the fixture's three. The accepted
World submits implementation, review and integration; this submits the packet's
own generated submission, which is implementation and review, and the
integration worker and its judgment machinery are outside this Job.
"""
import copy
import json
import os
import sys
from pathlib import Path

HERE = os.path.dirname(os.path.realpath(__file__))
if HERE not in sys.path:                                     # pragma: no cover
    sys.path.insert(0, HERE)

from baton_v12.contracts import digest                       # noqa: E402
from baton_v12.worker_manager import provider_context as context  # noqa: E402
from tests.tools import correction_restart_trace as accepted  # noqa: E402

import correction_packet as packets                           # noqa: E402
import correction_supervisor as supervisor                    # noqa: E402

# The run identity this fixture uses. `a` so the generated Job id is `job-a`,
# which is the identity the accepted World's own readers name -- reusing its
# `review`, `turn` and `until` helpers is the whole point of the vehicle, and
# renaming the Job would mean reimplementing them.
RUN = "a"
GRANT = "managed-correction-connected"


class ConnectedPacket(accepted.World):
    """The accepted World, with this packet's documents as the consumed path."""

    def setUp(self):
        super().setUp()
        # THE PROFILE IS THE CANDIDATE ONE THIS PACKET REQUIRES. The World's is
        # `deterministic`; `candidate` is admissible only under a live one-run
        # authorization, which `serving` below mints in these disposable stores.
        self.state_path = ".claude/projects/-output/{conversation_id}.jsonl"
        self.context_profile = dict(self.context_profile,
                                    schema=context.SESSION_PROFILE_SCHEMA,
                                    qualification="candidate",
                                    state_paths=[self.state_path])
        self.context_digest = digest(self.context_profile)
        # THE REAL CONVERSATION-PATH SUBSTITUTION, restored exactly as the
        # accepted `ManagedSessionResume` case restores it.
        #
        # Review 2026-09-29T22-51-42Z read the retained proposal and found the
        # real blocker: disposition `provider-failed`, reason `start-error`, why
        # "provider context terminal identity is unproved", changed_paths empty
        # and NO verification attempted -- so my speculation about the test scope
        # and the verification command was wrong and is withdrawn.
        #
        # THE CAUSE IS THIS SEAM. `ServingContextCase.setUp` patches
        # `oci.OciAdapter._context_execution` to return None, because the
        # composed flow it serves uses a `/1` profile whose state path is FIXED
        # (`.claude/projects/output/session.json`). This packet requires the
        # SESSION profile, whose allowlist names `{conversation_id}.jsonl` --
        # that is what makes a restore possible at all -- and with the
        # substitution stubbed out the adapter cannot prove the conversation's
        # terminal identity, so the turn fails before any verification.
        # `ManagedSessionResume` restores the real function for exactly this
        # reason; this does the same rather than weakening the identity check.
        from unittest import mock

        from baton_v12.worker_manager import oci

        guard = mock.patch.object(oci.OciAdapter, "_context_execution",
                                  self.real_context_execution)
        guard.start()
        self.addCleanup(guard.stop)
        self.script_guard()
        self.packet_root = os.path.join(self.root, RUN)
        self.packet_destination = os.path.join(self.root, "packet")
        # THE STAGING ROOT IS OUTSIDE THE CHECKOUT, because the fixture's own
        # root lives INSIDE it: `staged_source` refuses a copy nested with what
        # it copies, and `held_selections` refuses a staging root nested with the
        # run root. Both refusals are correct, so the fixture obeys them.
        import tempfile
        self.packet_staging = tempfile.mkdtemp(prefix="connected-staging-")
        self.addCleanup(__import__("shutil").rmtree, self.packet_staging,
                        ignore_errors=True)
        os.makedirs(self.packet_root, exist_ok=True)
        self.prepared = self.prepare_packet()
        self.packet = packets.held_packet(self.prepared["packet"])
        # THE CONSUMED PATH: this packet's composition and this packet's
        # submission, in place of the fixture's own.
        self.configuration = copy.deepcopy(self.composition)
        self.submission = copy.deepcopy(self.generated_submission)
        self.adopt_generated_worker()

    def failing_script(self):
        """A scripted provider that FAILS, injected into the script itself.

        `provider_status` is an operand of the generic stub helper; the provider
        this fixture actually runs is a real child process, and its exit code
        comes from the script rather than from that operand. A test asserting a
        provider failure while passing `provider_status=1` was asserting
        something this fixture does not produce -- found by that very test -- so
        the failure is injected where the child's status really comes from.
        """
        from unittest import mock

        original = accepted.PROVIDER
        injected = original.replace(
            "for name,body in edits.items():Path(name).write_text(body)",
            "import sys;sys.stderr.write('scripted provider failure\\n');"
            "sys.exit(1)")
        if injected == original:                             # pragma: no cover
            raise AssertionError("the provider script's edit line no longer "
                                 "matches; the failure injection anchor moved")
        guard = mock.patch.object(accepted, "PROVIDER", injected)
        guard.start()
        self.addCleanup(guard.stop)

    def script_guard(self):
        """The scripted provider writes THE SELECTED session path.

        Review 2026-09-29T23-04-18Z named this static mismatch: the inherited
        `World.PROVIDER` script has `.claude/projects/output/session.json`
        EMBEDDED IN ITS TEXT, and assigning `self.state_path` does not change a
        literal inside a string. This packet selects
        `.claude/projects/-output/{conversation_id}.jsonl`, so the child was
        retaining its conversation somewhere the selected profile's allowlist
        does not name.

        PATCHED BY THE SAME MECHANISM THE ACCEPTED TESTS USE for their own
        variants -- a text substitution on the script constant, asserted to have
        changed something -- so the child retains and restores exactly the
        conversation file this profile allows. The `{conversation_id}` is the
        session the argv carries, which is what the adapter substitutes.
        """
        from unittest import mock

        original = accepted.PROVIDER
        selected = ("state=Path(os.environ['HOME'])/("
                    "'.claude/projects/-output/'+session+'.jsonl')")
        injected = original.replace(
            "state=Path(os.environ['HOME'])/'.claude/projects/output/"
            "session.json'\n    previous=json.loads(state.read_text()) "
            "if state.exists() else None\n    session=argv[-2]",
            "session=argv[-2]\n    " + selected
            + "\n    previous=json.loads(state.read_text()) "
              "if state.exists() else None")
        if injected == original:                             # pragma: no cover
            raise AssertionError(
                "the provider script's embedded session path did not change; "
                "the substitution anchor no longer matches "
                "correction_restart_trace.PROVIDER")
        guard = mock.patch.object(accepted, "PROVIDER", injected)
        guard.start()
        self.addCleanup(guard.stop)
        self.provider_script = injected

    def adopt_generated_worker(self):
        """Make the INHERITED helpers read the GENERATED worker's operands.

        Review 2026-09-29T22-44-32Z disproved my previous diagnosis and gave the
        real one: `mounted` succeeds, and the failure is inside the inherited
        `turn` helper, which calls `launch.adopt(self.config['launch_home'], ...,
        contract=self.config['launch_contract'], ...)`. Replacing
        `self.configuration` and `self.submission` while LEAVING `self.config`
        alone left that helper adopting from the OLD fixture launch root while
        the generated worker writes its delivery under the packet instance's own.
        `adopt` found nothing there and answered None.

        SO THE FIXTURE'S OWN OPERAND MAP IS MADE COHERENT WITH THE DOCUMENT THE
        RUN IS COMPOSED FROM, rather than the delivery being fabricated or copied
        to make the old path appear valid. The real adoption and the real
        `serve_exchange` are untouched; what changes is WHERE the helper looks,
        which is a fixture-coherence fact and not a manager one.

        EVERY VALUE COMES FROM THE GENERATED PRODUCER WORKER, so a later change
        to the generator moves both ends together.
        """
        producer = next(one["deployment"] for one in self.configuration["workers"]
                        if one["worker_id"] == "implementation-worker")
        # The keys the inherited helpers read off `self.config`. Named
        # explicitly: a blanket update would also overwrite fixture-only members
        # the World needs, and silently.
        for name in ("launch_home", "launch_contract", "participant",
                     "principal", "profile_name", "profile_digest",
                     "policy_digest", "adapter_name", "adapter_digest",
                     "image_digest", "engine", "network", "workspace_storage",
                     "workspace_group", "credential_home", "credential_sources",
                     "credential_slots", "credential_profile",
                     "nominated_source", "workspace_capacity", "input_manifest",
                     "task_document", "review_route",
                     "retention_policy_digest", "retention_disposition",
                     "authority_store", "authority_uuid", "schema"):
            if name in producer:
                self.config[name] = producer[name]
        # THE LAUNCH ROOT HAS TO EXIST before the delivery is adopted into it:
        # the generated document names it and this fixture installs nothing.
        os.makedirs(producer["launch_home"], exist_ok=True)
        os.makedirs(producer["credential_home"], exist_ok=True)

    # -- the packet's own preparation ---------------------------------------

    def selections(self):
        """The generator's operands, pointed at THIS fixture's world.

        Review 2026-09-29T22-23-10Z: "adapt fixture paths instead of importing
        the older three-stage integration workload."
        """
        return {
            "schema": packets.SELECTIONS_SCHEMA,
            "run_id": RUN,
            # THIS PREPARATION'S OWN WORK, not the World's.
            #
            # Review 2026-09-29T23-40-17Z: "the connected fixture must stop
            # relying on adoption of an unrelated preexisting World Work as if
            # it proved exact replay". It was passing `W1` -- the fixture's own
            # Work, created by the World's setUp under ITS act -- so the
            # preparation adopted somebody else's Work and the exact-replay claim
            # rested on that adoption. `W236087` is absent from this Authority
            # until `prepare_work` creates it under its own journalled identity,
            # so the connected proof exercises the FRESH path and the CLI cases
            # exercise replay and collision separately.
            "work": "W236087",
            "instance_root": self.packet_root,
            "staging_root": self.packet_staging,
            "source": {"root": self.source, "declared_base": self.base,
                       "files": sorted(
                           one for one in os.listdir(self.source)
                           if os.path.isfile(os.path.join(self.source, one)))},
            # THE IMPORT ROOTS THIS PROCESS IS ACTUALLY RUNNING, which is what
            # `staged_source` copies and `verify_imported_sources` would hold a
            # real run to. Derived from the loaded module rather than typed.
            "manager_source_origin": os.path.dirname(os.path.dirname(
                os.path.dirname(os.path.realpath(accepted.__file__)))),
            "manager_runtime": {"path": self.runtime_path(),
                                "executable_sha256": self.runtime_digest(),
                                "build_commit": "0" * 40},
            "worker_image": {
                "reference": "baton-v12-claude-worker:connected-fixture",
                "config_digest": self.config["image_digest"],
                "worker_files": {"opt/baton/claude_agent.py": "1" * 64},
                "adapter_descriptor": self.config["adapter_digest"],
                "policy_descriptor": self.config["policy_digest"],
                "profile_descriptor": self.config["profile_digest"]},
            "participants": {
                "implementation": self.config["participant"],
                "review": "baton.reviewer",
                "integration": "baton.integrator"},
            # THE FIXTURE'S OWN RECEIPT WRITERS, which hold the capabilities
            # its Authority granted -- not the review worker's participant.
            "receipts": {"verification": "baton.verifier",
                         "review": "baton.approver-review",
                         "approval": "baton.approver"},
            "credential_reference": "connected-fixture-reference",
            "runtime_uid": os.getuid(),
            "context_profile": dict(self.context_profile),
            "credential_delivery": {
                "provider": self.config["credential_profile"]["api"]["provider"],
                "slots": list(self.config["credential_slots"]),
                "sources": self.config["credential_sources"]},
            "review_route": {"implementation": self.config["review_route"],
                             "review": "integration"},
            # THE FIXTURE'S OWN WORLD, so the generated worker and the
            # configured owner agree -- the composition preflight refused a
            # packet that named a second one.
            "context_storage": {"path": str(self.context_root),
                                "excluded": [self.source, self.storage]},
            "workspace_storage": self.storage,
            # THE FIXTURE'S OWN STORES, which is what the run will open.
            "stores": {"authority": self.authority_path,
                       "job": os.path.join(self.root, "jobs.sqlite3"),
                       "control": os.path.join(self.root, "control.sqlite3"),
                       "integration": os.path.join(self.root,
                                                   "integration.sqlite3"),
                       "state_root": os.path.join(self.root, "state")},
        }

    def runtime_path(self):
        """A disposable stand-in for the installed runtime.

        `held_packet` pins `<path>/baton-v12-stack`, and this fixture installs
        no runtime: what it proves is the DOCUMENTS and the SUPERVISOR, not an
        installation. The file is written here and named as a stand-in rather
        than borrowed from a real distro, so nothing reads a deployed tree.
        """
        place = os.path.join(self.root, "runtime-stand-in")
        os.makedirs(place, exist_ok=True)
        whole = os.path.join(place, "baton-v12-stack")
        if not os.path.exists(whole):
            Path(whole).write_text("# simulated runtime stand-in\n")
        return place

    def runtime_digest(self):
        return packets.digest_of(os.path.join(self.runtime_path(),
                                              "baton-v12-stack"))

    def prepare_packet(self):
        """Run the packet's own `stage` and `bind`, and keep what they wrote."""
        selections = os.path.join(self.root, "selections.json")
        Path(selections).write_text(
            json.dumps(self.selections(), indent=2, sort_keys=True) + "\n")
        chosen = packets.held_selections(selections)
        prepared = packets.stage(chosen, self.packet_destination,
                                 selections=selections, claim=309871)
        # THE INSTALLATION RECORD, at the path `bootstrap.layout` names. This
        # fixture runs no `tools.bootstrap` -- that is the one installation seam
        # it simulates, and it is recorded as such -- so the identity the
        # installer would have minted is written where the installer writes it.
        installed = packets.installed_layout(self.packet_root)
        Path(installed["record"]).write_text(
            json.dumps({"authority_uuid": self.config["authority_uuid"]}) + "\n")
        # A FRESH INSTALLATION BINDS NO JOB, so the emitted configuration is
        # written with none -- exactly what `tools.bootstrap.configuration`
        # produces -- and the qualified Work id comes from the SUPPORTED
        # preparation below rather than from an invented binding.
        Path(installed["configuration"]).write_text(
            json.dumps({"job_bindings": []}, indent=2) + "\n")
        # THE SUPPORTED WORK PREPARATION, through `prepare_work`'s real Authority
        # acts against THIS fixture's disposable Authority. Review
        # 2026-09-29T23-17-24Z R1: the fixture previously invented a preexisting
        # Work binding and bypassed this boundary entirely.
        self.prepared_work = self.prepare_supported_work()
        provenance = os.path.join(self.root, "provenance.json")
        Path(provenance).write_text(json.dumps({
            "provenance": {"fixture": {"path": selections,
                                       "sha256": packets.digest_of(selections)}},
            "compatibility": {
                "adapter_source_sha256": "1" * 64,
                "context_capable": True,
                "established": ["this is a disposable deterministic fixture; "
                                "the composition is generated and proved here"],
                "not_established": ["no live provider, engine, image or "
                                    "deployed store is involved"]}}) + "\n")
        packets.bind(chosen, self.packet_destination, claim=309871,
                     provenance=json.loads(
                         Path(provenance).read_text())["provenance"],
                     compatibility=json.loads(
                         Path(provenance).read_text())["compatibility"])
        with open(os.path.join(self.packet_destination, "deployment.json"),
                  encoding="utf-8") as handle:
            self.composition = json.load(handle)
        with open(os.path.join(self.packet_destination, "submission.json"),
                  encoding="utf-8") as handle:
            self.generated_submission = json.load(handle)
        prepared["packet"] = os.path.join(self.packet_destination,
                                          "packet.json")
        return prepared

    def prepare_supported_work(self):
        """Drive `correction_packet.prepare_work` against the real Authority.

        THE ACTS ARE REAL and the Authority is this fixture's disposable one: the
        Work is created under the assignment contract, the impl/rview/integration
        route handlers are registered, the four receipt capabilities are granted
        in the Work's own scope, and the canonical target is set. No Job is
        submitted -- `baseline.survey` refuses a Job identity the store already
        records, and the execution Job belongs to the supervisor.

        THE WORK THIS FIXTURE ALREADY HAS is the one the preparation names. The
        accepted World creates `self.work` in its own setUp, so `create_work`
        REPLAYS under its journalled identity rather than making a second Work --
        which is the idempotence the step claims, exercised rather than asserted.
        """
        from baton_v12.authority import Authority

        installed = packets.installed_layout(self.packet_root)
        chosen = packets.held_selections(
            os.path.join(self.root, "selections.json"))
        authority = Authority.open(
            self.authority_path,
            expected_authority_uuid=self.config["authority_uuid"])
        try:
            # THE IDENTITY IS DERIVED INSIDE `prepare_work` and is not an
            # operand any caller -- including this fixture -- can supply.
            work_id = packets.prepared_work_id(
                chosen, self.config["authority_uuid"])
            prepared = packets.prepare_work(authority, chosen, work_id=work_id)
        finally:
            authority.dispose()
        prepared["authority_uuid"] = self.config["authority_uuid"]
        prepared["authority_store"] = self.authority_path
        record = os.path.join(self.packet_destination, "prepared-work.json")
        os.makedirs(self.packet_destination, exist_ok=True)
        Path(record).write_text(
            json.dumps(prepared, indent=2, sort_keys=True) + "\n")
        del installed
        return prepared

    def serving(self, **unused):
        """THE PACKET'S OWN PREPARATION, over the fixture's disposable stores.

        This deliberately does NOT delegate to the World's `serving`. The
        composition preflight refused that: "required context configuration
        disagrees with its preconfigured owner", because the World configures
        its own context root while the generated worker names the packet's. The
        packet's document is the consumed path, so the owner acts here configure
        what the PACKET says -- which is the whole point of the milestone.

        EVERY ACT IS THE REAL OWNER API: `configure_workspace_storage`,
        `context_delivery.configure_context_storage`,
        `certify_context_profile`, and `authorize_qualification_run`. The grant
        is minted in THESE disposable stores and nowhere else; no deployed grant
        or store is read, created or mutated.
        """
        from types import SimpleNamespace

        from baton_v12.worker_manager import context_delivery as custody
        from baton_v12.worker_manager.workspaces import \
            configure_workspace_storage
        from tests.job_manager import fixtures
        from tools import stage_execution

        job, control = self.stores("connected-packet")
        # THE ACTUAL SUPERVISOR PREPARATION ENTRY, which is what review
        # 2026-09-29T23-17-24Z's closure asks for: `baseline.prepare` is the
        # function `correction_supervisor.main` calls, and it composes the four
        # owner acts in the order the admission boundary requires -- the
        # workspace store first (the context storage's containment checks read
        # it), then the private context storage, then the profile certification
        # compared against the packet's bound digest, then the ONE qualification
        # grant. Driving the individual calls myself proved they each work and
        # NOT that this composition does.
        self.prepared_owner_acts = supervisor.baseline.prepare(control,
                                                              self.packet)
        selected = self.packet["context"]
        self.assertEqual(self.prepared_owner_acts["profile_digest"],
                         selected["profile_digest"])
        self.assertEqual(self.prepared_owner_acts["qualification_run"],
                         self.packet["run_id"])
        composed = stage_execution.operations_from(
            self.configuration, job, control, engine_run=self.engine,
            credential_provider=lambda provider, reference: self.secret,
            clock=lambda: fixtures.NOW, checkout=self.checkout)
        self.addCleanup(composed.close)
        self._composed = composed
        return SimpleNamespace(job=job, control=control, composed=composed)

    def provider(self, edits=None, status=0):
        """The scripted provider, with the NESTED output path it is asked to write.

        Review 2026-09-29T22-58-46Z captured the child's actual stderr:
        `FileNotFoundError` writing `docs/v12-context-correction.md`, because the
        `docs` parent does not exist in the candidate -- so the child exited 1
        before it could emit terminal JSON, and the adapter then reported the
        context terminal identity as unproved. My earlier stdout-None hypothesis
        was wrong, and the `_context_execution` restoration did NOT fix this
        error; I am not claiming it did.

        THE PACKET'S TASK NAMES A FILE IN A SUBDIRECTORY and that is the point of
        it -- `docs/v12-context-correction.md` is where an operator guide belongs.
        A real provider creates the directory it writes into; the SIMULATED one
        this fixture scripts did not, which is a fixture boundary fault and not a
        product one.

        SO THE PARENTS ARE CREATED AND NOTHING ELSE CHANGES. The proposal is
        still authored by the provider writing into the candidate, the real
        version-control child still runs, the task's own verification command
        still runs, and no identity or receipt check is touched.
        """
        original = super().provider(edits=edits, status=status)

        def run(argv, **options):
            import claude_agent

            if argv[0] == claude_agent.PROVIDER_PROGRAM:
                for name in (edits or {}):
                    whole = os.path.join(options["cwd"], name)
                    parent = os.path.dirname(whole)
                    if parent:
                        os.makedirs(parent, exist_ok=True)
            return original(argv, **options)

        return run

    # -- the connected run --------------------------------------------------

    EDITS = {
        "opening": {"docs/v12-context-correction.md":
                    "# Managed context correction\n\nThe opening proposal.\n"},
        "corrected": {"docs/v12-context-correction.md":
                      "# Managed context correction\n\nThe revised proposal, "
                      "answering the review.\n"},
    }

    def run_packet(self, *, dispositions, interrupt_at=None,
                   provider_status=0):
        """Drive THIS packet's supervisor over the real stores.

        THE SCENARIO IS SCRIPTED THROUGH THE SUPERVISOR'S OWN `sleep` HOOK,
        which is the honest place for it: the supervisor injects `sleep` for
        exactly this reason, so the scenario advances the provider and the
        reviewer between ticks of the REAL serving loop rather than replacing
        it. Nothing about the manager, the stores, the admission gate, the
        attachments, the verdicts or the cleanup is substituted.

        `dispositions` is the list of SCRIPTED reviewer verdicts, in order. Each
        is committed through the real `review_cycles` owner API by
        `World.review`; it is a scripted disposition and this fixture says so,
        which is different from forging an owner receipt.
        """
        held = self.serving()
        self.turns = []
        self.reviews = []
        self.scripted = list(dispositions)
        self.interrupt_at = interrupt_at
        self.provider_status = provider_status
        self.stage_states = {}

        def advance(_seconds=1):
            """One scenario step, between two ticks of the real loop."""
            self.tick_count += 1
            if self.tick_count > 90:
                raise AssertionError("the scenario did not converge")
            states = self.states(held.job, held.composed)
            self.stage_states = dict(states)
            if self.interrupt_at is not None \
                    and len(self.turns) >= self.interrupt_at:
                self.interrupt_at = None
                raise KeyboardInterrupt("scripted interruption")
            if states.get("implementation") == "waiting":
                # THE COMPOSED DEPLOYMENT'S OWN ANSWER, which is what the
                # accepted trace uses: the projection's live episode identity
                # exists before the worker has a runtime to mount.
                # THE LIVE EPISODE'S ATTEMPT, which is the manager's own answer
                # for which one is current. `only_attempt` asserts there is
                # exactly one and the CORRECTION ROUND makes two -- it failed
                # with "2 != 1" on the restored attempt, which is the round this
                # packet exists to drive.
                attempt = self.live_attempt(held, "implementation")
                if attempt is not None and attempt not in self.turns:
                    self.turns.append(attempt)
                    edits = (self.EDITS["opening"] if len(self.turns) == 1
                             else self.EDITS["corrected"])
                    self.turn(held.control, "implementation", attempt,
                              self.mounted(held.composed, "implementation",
                                           attempt),
                              edits=edits, status=self.provider_status)
            elif states.get("review") == "waiting" and self.scripted:
                said = self.scripted.pop(0)
                self.reviews.append(self.review(held, said))

        outcome = supervisor.supervise(
            held.job, held.control, held.composed, self.packet,
            sleep=advance, monotonic=self.monotonic())
        return held, outcome

    def monotonic(self):
        """A scripted clock: one second per scenario step, so the 840-second
        serving bound and the 60-second reserve are real numbers over a run that
        takes no wall time."""
        held = {"now": 0.0}

        def reading():
            held["now"] += 1
            return held["now"]

        return reading

    def live_attempt(self, held, kind):
        from baton_v12.job_manager import episodes, submission

        for stage in submission.stages_of(held.job, "job-a"):
            if stage["kind"] != kind:
                continue
            live = episodes.live_of(held.job, stage["stage_id"])
            return None if live is None else live["attempt_id"]
        return None
