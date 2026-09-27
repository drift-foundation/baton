"""W275774 — the host-enforced pre-effect launch boundary, proved at the engine.

REVIEW 2026-09-26T14:41:35Z REJECTED THE PREVIOUS PROPOSAL, correctly. Binding a
token from `adapter.start`'s returned runtime id is too late: `oci.run_vector`
composed `run --detach`, so `OciAdapter.start` executed the container WITH ITS
WRITABLE MOUNTS ALREADY PRESENT and only then answered with an identity. A later
`effects_permitted` call cannot retroactively prevent an effect that has happened,
and a worker that politely waits for input is worker cooperation, not host
exclusion.

So the launch is now TWO ENGINE ACTS: `create` composes the identical vector and
leaves it inert, the token binds that exact container, and `start` runs it. These
cases ask the CONTROLLED ENGINE what it was actually told and in what order --
which is the only place the ordering claim can be settled -- using the same
recording `Engine` double the adapter's own suite uses, real disposable
`ControlStore` instances, and no live Docker.
"""
import os
import tempfile
import unittest

from baton_v12.contracts import ContractRefusal
from baton_v12.worker_manager import oci, tokens
from baton_v12.worker_manager.oci import OciAdapter
from baton_v12.worker_manager.store import ControlStore

from tests.manager.test_oci import IMAGE, LABELS, Adapting, Engine, answer


class ActivationBoundary(Adapting):
    """The ordering property, asked of the engine rather than of the design."""

    instant = "2026-09-26T14:00:00.000Z"

    def setUp(self):
        super().setUp()
        room = tempfile.TemporaryDirectory(prefix="v12-activation-")
        self.addCleanup(room.cleanup)
        self.store = ControlStore.open(
            os.path.join(room.name, "control.sqlite3"),
            incarnation="activation", clock=lambda: self.instant)
        self.addCleanup(self.store.close)
        self.domain = tokens.domain_of("workspace", "line-7/workspace")

    def adapter(self, answers):
        engine = Engine(answers)
        self.engine = engine
        return OciAdapter("docker", engine, identity=self.IDENTITY,
                          assignment_roots=dict(self.live_roots),
                          posture="execution", workspace_group=self.group,
                          launch_delivery=self.launched(),
                          mounts=[{"source": self.live_roots["inputs"],
                                   "target": "/input", "writable": False}])

    def request(self):
        return {"labels": LABELS, "operation_id": "runtime.start:1",
                "input_root": self.live_roots["inputs"]}

    def acting(self):
        """The engine script for one governed launch: probe, create, activate."""
        return [answer(stdout=""), answer(stdout="runtime-1\n"), answer()]

    def subcommands(self):
        return [vector[1] for vector in self.engine.vectors]

    def held(self, *, seconds=900):
        return tokens.acquire(self.store, self.domain,
                              operation="runtime.start:1", execution="attempt-1",
                              attempt="attempt-1", seconds=seconds)

    # -- the cutpoint ---------------------------------------------------------

    def test_a_governed_launch_creates_and_binds_before_anything_runs(self):
        """THE CUTPOINT, observed from inside the binding itself.

        At the instant the token is asked to bind, this reads what the engine has
        been told so far. `create` must have happened -- otherwise there is no
        identity to bind -- and `start` must NOT have, because that is the act
        that makes the mounts reachable. Asserting it inside the callback is what
        makes this a cutpoint rather than an after-the-fact summary that cannot
        distinguish "bound before" from "bound after".
        """
        token = self.held()
        tokens.journal_launch(self.store, token, "runtime.start:1")
        adapter = self.adapter(self.acting())
        seen = {}

        def binding(runtime_id):
            seen["subcommands"] = self.subcommands()
            seen["runtime_id"] = runtime_id
            tokens.bind_container(self.store, token, runtime_id,
                                  launch="runtime.start:1")
            seen["permitted_when_bound"] = tokens.effects_permitted(
                self.store, token)
            # THE PERMISSION IS THE TOKEN'S OWN ADMISSION RECORD, minted at the
            # last moment. A boolean would be indistinguishable from a stale one.
            return lambda: tokens.admit_activation(self.store, token,
                                                   container=runtime_id)

        started = adapter.start(self.request(), bind=binding)
        self.assertEqual(started["runtime_id"], "runtime-1")
        # WHAT THE ENGINE HAD BEEN TOLD WHEN THE BINDING RAN.
        self.assertIn("create", seen["subcommands"])
        self.assertNotIn("start", seen["subcommands"],
                         "the container must not be running when it is bound")
        self.assertNotIn("run", seen["subcommands"],
                         "a governed launch must never compose `run`")
        self.assertEqual(seen["runtime_id"], "runtime-1")
        self.assertTrue(seen["permitted_when_bound"])
        # AND THE ACTIVATION IS THE LAST THING THAT HAPPENED, by name.
        self.assertEqual(self.subcommands()[-1], "start")
        self.assertEqual(self.engine.vectors[-1],
                         ["docker", "start", "runtime-1"])
        self.assertEqual(
            tokens.token_of(self.store, self.domain, 1)["container"],
            "runtime-1")

    def test_the_deferred_vector_is_the_immediate_one_but_inert(self):
        """A DIFFERENT CONTAINER WOULD DEFEAT THE WHOLE POINT.

        The binding is only meaningful if the thing bound is the thing that later
        runs, so the two vectors must agree on every mount, restriction, label
        and identity and differ ONLY in the subcommand that decides whether a
        process exists.
        """
        composed = {}
        for which, activation in (("immediate", oci.ACTIVATE_IMMEDIATELY),
                                  ("deferred", oci.ACTIVATE_DEFERRED)):
            composed[which] = oci.run_vector(
                "docker", image_digest=IMAGE, labels=LABELS,
                assignment_roots=dict(self.live_roots), posture="execution",
                name="baton-activation", workspace_group=self.group,
                activation=activation)
        self.assertEqual(composed["immediate"][1:3], ["run", "--detach"])
        self.assertEqual(composed["deferred"][1:2], ["create"])
        self.assertEqual(list(composed["deferred"][2:]),
                         list(composed["immediate"][3:]),
                         "the inert vector must describe the same container")

    def test_an_unknown_activation_is_refused_rather_than_guessed(self):
        with self.assertRaises(ContractRefusal):
            oci.run_vector("docker", image_digest=IMAGE,
                           labels=LABELS,
                           assignment_roots=dict(self.live_roots),
                           posture="execution", name="baton-activation",
                           workspace_group=self.group, activation="launch-it")

    # -- the refusals, which must leave nothing running -----------------------

    def test_a_refused_binding_never_activates_the_container(self):
        """A token that will not bind means the resource is not exposed.

        The refusal is a POST-CREATE exit: an inert container exists and is
        settled by name. What must not happen is activation, and that is asked
        of the engine.
        """
        token = self.held()
        # REVIEW 14:54:16Z: the launch is journalled and the refusal is named, so
        # this case proves the OWNER boundary. Without the journal it refused for
        # the unjournalled launch instead -- true, and about a different rule.
        tokens.journal_launch(self.store, token, "runtime.start:1")
        forged = dict(token, owner="somebody-elses-owner")
        adapter = self.adapter(self.acting() + [answer(), answer()])

        def binding(runtime_id):
            tokens.bind_container(self.store, forged, runtime_id,
                                  launch="runtime.start:1")
            return lambda: tokens.admit_activation(self.store, token,
                                                   container=runtime_id)

        with self.assertRaises(ContractRefusal) as caught:
            adapter.start(self.request(), bind=binding)
        # THE ADAPTER'S POST-CREATE SETTLEMENT RE-CODES THE EXIT as `denied`
        # -- it is reporting a start it refused, not re-raising the token's
        # verdict -- and it CARRIES THE ORIGINAL MESSAGE. So the named boundary
        # is asserted in the text, where it actually survives. Measured: the
        # code is 'denied' here, not 'identity-mismatch'.
        self.assertEqual(caught.exception.code, "denied")
        self.assertIn("could not be bound before activation",
                      caught.exception.message)
        # The token names the boundary without echoing the forged owner back --
        # measured wording, not assumed: "asked by an act that does not own it".
        self.assertIn("does not own it", caught.exception.message)
        self.assertNotIn(["docker", "start", "runtime-1"], self.engine.vectors,
                         "a container nothing could bind must never run")
        self.assertIsNone(
            tokens.token_of(self.store, self.domain, 1)["container"])

    def test_an_expiry_between_reservation_and_activation_withholds_the_run(self):
        """EXPIRY IN THE WINDOW THE REVIEW NAMED.

        The reservation is taken, the container is created -- and the token
        expires before the binding. The generation is no longer entitled to the
        resource, so the created container is never activated. This is the case
        that a post-hoc gate cannot answer at all: without the two acts the
        process would already be running by now.
        """
        token = self.held(seconds=1)
        # THE LAUNCH IS JOURNALLED WHILE THE TOKEN IS STILL LIVE, so what the
        # binding meets below is EXPIRY and not the unjournalled-launch refusal.
        # Measured: without this the refusal named "not the launch this token
        # journalled" -- also correct, and about a different rule than this case.
        tokens.journal_launch(self.store, token, "runtime.start:1")
        adapter = self.adapter(self.acting() + [answer(), answer()])

        def binding(runtime_id):
            self.instant = "2026-09-26T15:00:00.000Z"
            tokens.bind_container(self.store, token, runtime_id,
                                  launch="runtime.start:1")
            return lambda: tokens.admit_activation(self.store, token,
                                                   container=runtime_id)

        with self.assertRaises(ContractRefusal) as caught:
            adapter.start(self.request(), bind=binding)
        self.assertIn("expired at", caught.exception.message)
        self.assertNotIn(["docker", "start", "runtime-1"], self.engine.vectors)
        self.assertEqual(
            tokens.token_of(self.store, self.domain, 1)["container"], None,
            "an expired generation binds no container")

    def test_a_creation_reply_naming_nothing_binds_and_runs_nothing(self):
        """AN UNNAMED CREATION REPLY, which is all this case claims.

        Review 14:54:16Z is right that an empty reply is NOT evidence about a
        delayed external completion -- the engine may have created something this
        manager cannot name, and that uncertainty is exactly why nothing may be
        bound or activated. What is proved here is narrow and local: an answer
        this adapter cannot turn into an identity binds nothing, activates
        nothing, and permits no effects. A genuinely delayed or lost reply
        against a real engine is a separate property and is NOT proved here.
        """
        token = self.held()
        bound = []
        adapter = self.adapter([answer(stdout=""), answer(stdout="\n")])

        def binding(runtime_id):
            bound.append(runtime_id)
            return lambda: tokens.admit_activation(self.store, token,
                                                   container=runtime_id)

        started = adapter.start(self.request(), bind=binding)
        self.assertIsNone(started["runtime_id"])
        self.assertEqual(bound, [], "an unnamed creation binds nothing")
        self.assertNotIn("start", self.subcommands())
        self.assertFalse(tokens.effects_permitted(self.store, token))

    def test_an_expired_launch_still_holds_the_resource_against_a_replacement(self):
        """THE OTHER HALF OF THE ARGUMENT, asserted rather than asserted-in-prose.

        A window remains between the last-moment permission and the engine, and
        no in-process check can close it. What makes that window safe is that a
        late activation can only ever be THE GENERATION THAT STILL HOLDS THE
        RESOURCE: expiry does not return a token, so a generation whose launch
        was journalled and whose cessation is unsettled keeps the domain, and a
        competing attempt is refused rather than admitted beside it.

        I asserted this in prose in the previous handoff. Here it is measured.
        """
        token = self.held(seconds=1)
        tokens.journal_launch(self.store, token, "runtime.start:1")
        tokens.bind_container(self.store, token, "runtime-1",
                              launch="runtime.start:1")
        self.instant = "2026-09-26T15:00:00.000Z"
        self.assertFalse(tokens.effects_permitted(self.store, token),
                         "the expired generation may not expose the resource")
        with self.assertRaises(ContractRefusal) as caught:
            tokens.acquire(self.store, self.domain,
                           operation="runtime.start:2", execution="attempt-2",
                           attempt="attempt-2")
        self.assertIn("is owned by token generation 1", caught.exception.message)
        self.assertEqual(len(tokens.outstanding(self.store, self.domain)), 1,
                         "an unsettled expired generation still holds the domain")

    def test_a_stale_boolean_permission_admits_nothing(self):
        """REVIEW 15:00:16Z's PROBE, as my own case and with the outcome named.

        The reviewer's `review_activation_admission_20260926.py` reads a permission
        while the token is live, then -- standing in for another host -- settles the
        inert container and takes generation 2, and finally answers the STALE `True`
        it read earlier. That must not activate generation 1's container.

        It does not, because a boolean is no longer a permission: the adapter
        requires the token's own admission document naming this exact runtime. Note
        the difference from that probe's expectation, which is a real question for
        the reviewer rather than a detail: this manager REFUSES the start instead of
        returning from it. A start that could not be admitted is not a start that
        worked, and reporting it as success would leave a created container nobody
        was told about. The probe's safety assertion holds either way, which is
        what the two assertions below measure.
        """
        token = self.held()
        tokens.journal_launch(self.store, token, "runtime.start:1")
        adapter = self.adapter(self.acting() + [answer(), answer()])
        replacements = []

        def binding(runtime_id):
            tokens.bind_container(self.store, token, runtime_id,
                                  launch="runtime.start:1")

            def permit():
                stale = tokens.effects_permitted(self.store, token)
                self.assertTrue(stale)
                tokens.returned(self.store, token, cessation={
                    "domain": token["domain"], "generation": token["generation"],
                    "launch": "runtime.start:1", "container": runtime_id,
                    "stopped": True, "helpers": []})
                replacements.append(tokens.acquire(
                    self.store, self.domain, operation="runtime.start:2",
                    execution="attempt-2", attempt="attempt-2"))
                return stale

            return permit

        with self.assertRaises(ContractRefusal) as caught:
            adapter.start(self.request(), bind=binding)
        self.assertIn("an activation admission is one exact document",
                      caught.exception.message)
        self.assertEqual(replacements[0]["generation"], 2)
        self.assertNotIn(["docker", "start", "runtime-1"], self.engine.vectors,
                         "a delayed generation-1 activation followed a "
                         "generation-2 acquisition")

    def test_an_admitted_activation_holds_the_resource_through_settlement(self):
        """THE DURABLE HALF: a real admission stops the handoff at its source.

        The case above is safe because the stale verdict is rejected. This one is
        about the path where the admission IS real: once an activation is admitted,
        the return itself refuses, so the resource cannot be given to a replacement
        while a starter may still be about to run. The hold ends when the activation
        is settled either way -- a conclusive outcome, not a timeout.
        """
        token = self.held()
        tokens.journal_launch(self.store, token, "runtime.start:1")
        tokens.bind_container(self.store, token, "runtime-1",
                              launch="runtime.start:1")
        tokens.admit_activation(self.store, token, container="runtime-1")
        evidence = {"domain": self.domain, "generation": 1,
                    "launch": "runtime.start:1", "container": "runtime-1",
                    "stopped": True, "helpers": []}
        with self.assertRaises(ContractRefusal) as caught:
            tokens.returned(self.store, token, cessation=evidence)
        self.assertEqual(caught.exception.code, "quiescence-unknown")
        self.assertIn("ADMITTED ACTIVATION", caught.exception.message)
        with self.assertRaises(ContractRefusal):
            tokens.acquire(self.store, self.domain, operation="runtime.start:2",
                           execution="attempt-2", attempt="attempt-2")
        # AND THE HOLD ENDS ON A CONCLUSIVE OUTCOME, either way.
        tokens.settle_activation(self.store, token, container="runtime-1",
                                 started=True)
        self.assertFalse(
            tokens.token_of(self.store, self.domain, 1)["activating"])
        tokens.returned(self.store, token, cessation=evidence)
        second = tokens.acquire(self.store, self.domain,
                                operation="runtime.start:2",
                                execution="attempt-2", attempt="attempt-2")
        self.assertEqual(second["generation"], 2)

    def test_an_unresolved_activation_outcome_is_not_a_settlement(self):
        """A truthy string is not an outcome here either."""
        token = self.held()
        tokens.journal_launch(self.store, token, "runtime.start:1")
        tokens.bind_container(self.store, token, "runtime-1",
                              launch="runtime.start:1")
        tokens.admit_activation(self.store, token, container="runtime-1")
        with self.assertRaises(ContractRefusal) as caught:
            tokens.settle_activation(self.store, token, container="runtime-1",
                                     started="false")
        self.assertEqual(caught.exception.code, "quiescence-unknown")

    def test_a_replayed_admission_cannot_authorize_a_second_start(self):
        """REVIEW 15:14:13Z ASKED FOR THIS PROPERTY BY NAME.

        `transact` answers an identical earlier record without re-running the
        guard, which is correct for retrying an activation still in flight and
        wrong once that activation is settled or the generation returned: the
        caller could re-present the replayed document and obtain a SECOND engine
        start of a container the resource no longer belongs to. Both terminal
        facts are monotone, so a pre-read that sees either is conclusive.
        """
        token = self.held()
        tokens.journal_launch(self.store, token, "runtime.start:1")
        tokens.bind_container(self.store, token, "runtime-1",
                              launch="runtime.start:1")
        first = tokens.admit_activation(self.store, token, container="runtime-1")
        # IN FLIGHT: an ordinary retry is idempotent and answers the original.
        self.assertEqual(
            tokens.admit_activation(self.store, token, container="runtime-1"),
            first)
        tokens.settle_activation(self.store, token, container="runtime-1",
                                 started=True)
        with self.assertRaises(ContractRefusal) as caught:
            tokens.admit_activation(self.store, token, container="runtime-1")
        self.assertIn("already been settled", caught.exception.message)
        # AND AFTER THE RETURN, for the same reason. MEASURED WORDING: the lifecycle
        # check answers first once the generation is returned, naming the return --
        # the same boundary, reached by the nearer rule.
        tokens.returned(self.store, token, cessation={
            "domain": self.domain, "generation": 1, "launch": "runtime.start:1",
            "container": "runtime-1", "stopped": True, "helpers": []})
        with self.assertRaises(ContractRefusal) as caught:
            tokens.admit_activation(self.store, token, container="runtime-1")
        self.assertIn("has been returned", caught.exception.message)

    def test_a_forged_owner_cannot_settle_an_activation(self):
        """The one record that RELEASES the in-flight hold is the owner's act.

        It accepted any caller holding a token copy, which made the hold
        releasable by a non-owner. Compared against the ADMISSION's own record
        rather than through `_owning`, deliberately -- see the next case.
        """
        token = self.held()
        tokens.journal_launch(self.store, token, "runtime.start:1")
        tokens.bind_container(self.store, token, "runtime-1",
                              launch="runtime.start:1")
        tokens.admit_activation(self.store, token, container="runtime-1")
        forged = dict(token, owner="somebody-elses-owner")
        with self.assertRaises(ContractRefusal) as caught:
            tokens.settle_activation(self.store, forged, container="runtime-1",
                                     started=True)
        self.assertEqual(caught.exception.code, "identity-mismatch")
        self.assertTrue(
            tokens.token_of(self.store, self.domain, 1)["activating"],
            "a forged settlement releases nothing")

    def test_an_expired_generation_may_still_settle_what_already_happened(self):
        """THE RECONCILIATION THE REVIEW REQUIRED TO STAY POSSIBLE.

        Expiry is a reason to stop ACTING, not a reason to refuse the answer about
        what already happened. If an expired generation could not settle its own
        activation, the in-flight hold would become permanent and the resource
        could never be reconciled -- so the owner check here is against the
        admission record, not `_owning`.
        """
        token = self.held(seconds=1)
        tokens.journal_launch(self.store, token, "runtime.start:1")
        tokens.bind_container(self.store, token, "runtime-1",
                              launch="runtime.start:1")
        tokens.admit_activation(self.store, token, container="runtime-1")
        self.instant = "2026-09-26T15:00:00.000Z"
        self.assertTrue(tokens.token_of(self.store, self.domain, 1)["expired"])
        tokens.settle_activation(self.store, token, container="runtime-1",
                                 started=True)
        self.assertFalse(
            tokens.token_of(self.store, self.domain, 1)["activating"],
            "an expired generation must still be able to resolve its activation")

    def test_no_terminal_fact_can_land_inside_the_admission_transaction(self):
        """THE REPLAY RACE, answered at the seam THIS implementation really has.

        Review 15:19:45Z's probe hooks `store.transact`, because the previous cut
        admitted through it. This one does not: the admission takes `BEGIN IMMEDIATE`
        itself and decides the replay disposition under that lock, so `transact` is
        never called for an admission and that hook has nothing to intercept. **That
        is a mechanism mismatch and NOT evidence of safety**, so the property is
        proved here instead.

        AND THE MEASURED ANSWER IS STRONGER THAN A REFUSAL: the interleave cannot
        happen at all. Injected into the record read immediately after the in-flight
        admission is read -- the exact window the review described -- every attempt
        to commit a terminal fact fails at its own `BEGIN IMMEDIATE`, because a
        transaction cannot start inside this one. Nothing is settled, nothing is
        returned, no generation 2 exists, and the admission's own transaction rolls
        back rather than answering on a half-changed world.

        WHAT THIS DOES AND DOES NOT ESTABLISH, stated rather than implied: it
        establishes that no same-connection work can slip a terminal fact into this
        window. For a SEPARATE connection the exclusion is `BEGIN IMMEDIATE`'s write
        lock rather than anything asserted here, and a genuinely concurrent two-process
        proof is not part of this case.
        """
        import sqlite3

        token = self.held()
        tokens.journal_launch(self.store, token, "runtime.start:1")
        tokens.bind_container(self.store, token, "runtime-1",
                              launch="runtime.start:1")
        tokens.admit_activation(self.store, token, container="runtime-1")
        evidence = {"domain": self.domain, "generation": 1,
                    "launch": "runtime.start:1", "container": "runtime-1",
                    "stopped": True, "helpers": []}
        honest = self.store.operation_record
        attempted = []

        def interleaving(operation_id):
            answer = honest(operation_id)
            if operation_id == tokens._activating_id(self.domain, 1) \
                    and not attempted:
                attempted.append("tried")
                tokens.settle_activation(self.store, token,
                                         container="runtime-1", started=False)
            return answer

        self.store.operation_record = interleaving
        try:
            with self.assertRaises(sqlite3.OperationalError) as caught:
                tokens.admit_activation(self.store, token, container="runtime-1")
        finally:
            self.store.operation_record = honest
        self.assertIn("within a transaction", str(caught.exception))
        self.assertEqual(attempted, ["tried"], "the window was actually reached")
        # AND NOTHING TERMINAL LANDED. The generation is still in flight, still
        # unreturned, and the domain is still its own.
        current = tokens.token_of(self.store, self.domain, 1)
        self.assertTrue(current["activating"])
        self.assertFalse(current["returned"])
        self.assertIsNone(current["activation_started"])
        with self.assertRaises(ContractRefusal):
            tokens.acquire(self.store, self.domain, operation="runtime.start:2",
                           execution="attempt-2", attempt="attempt-2")

    # -- and the ungoverned path is untouched ---------------------------------

    def test_an_ungoverned_launch_is_the_historical_single_act(self):
        """No token, no binding, no behaviour change: `run --detach`, once."""
        adapter = self.adapter([answer(stdout=""), answer(stdout="runtime-1\n")])
        started = adapter.start(self.request())
        self.assertEqual(started["runtime_id"], "runtime-1")
        self.assertEqual(self.subcommands(), ["ps", "run"])
        self.assertNotIn("create", self.subcommands())


if __name__ == "__main__":
    unittest.main()
