"""W32385: a restart adopts the exact ENDED runtime before any lane reuse.

`work/records/2026/08/finding-v12-local-oci-ended-runtime-adoption/`.

Split from W6636 by the 2026-08-28 approver scheduling ruling. W6636 already
proves a second incarnation adopts one exact RUNNING runtime and refuses
mismatch and multiplicity. This module owns the case it does not reach:

    AN EXITED CONTAINER IS NOT AN ABSENT ONE.

A runtime object that still exists is a process domain that still exists, so
`exited` cannot release the lane, satisfy cleanup, or admit a replacement. The
manager must identify the exact attempt and runtime, force-remove it, observe
positive absence through the adapter, settle the delivered roots, and only
then permit reuse.

It subclasses W6636's composition fixture, so every case here runs against the
same real daemon, the same built reference worker image and the same manager
seams -- a change that broke the accepted arc breaks these too.
"""

from __future__ import annotations

import os
import subprocess
import unittest
import uuid

from baton_v12.contracts import ContractRefusal
from baton_v12.worker_manager import credentials
from baton_v12.worker_manager import (authorize_cleanup, decide_retention,
                                      observe, reconcile_runtime,
                                      request_freeze, request_intake,
                                      request_runtime_start, retain_manifest)

from baton_v12.worker_manager.oci import LABEL_PREFIX
from .test_lifecycle_composition import (MARK, Lifecycle,
                                         RETENTION)


class EndedRuntimeAdoption(Lifecycle):

    def ended(self, **adapter_kwargs):
        """One attempt whose container has EXITED and is still present.

        The reference worker starts, reads its launch document, finds EOF on a
        closed stdin and shuts down cleanly -- so an exited-but-present
        container is the ORDINARY shape here rather than a fault this suite
        has to manufacture.
        """
        roots = self.roots()
        given, assignment = self.activated()
        inputs = self.composed(roots, given, assignment)
        adapter = self.adapter(roots=roots, mounts=self.plan(roots),
                               **adapter_kwargs)
        request_runtime_start(self.store, adapter, attempt_id=self.attempt,
                              inputs=inputs)
        runtime_id = self.attempt_row()["runtime_id"]
        self.settled(runtime_id)
        # STILL THERE, asked of the daemon. Everything below depends on this.
        self.assertEqual(self.inspected(runtime_id)["State"]["Status"],
                         "exited")
        return adapter, roots, given, assignment, runtime_id

    def restarted(self):
        """A second manager incarnation over the SAME durable store, which is
        what a restart actually is."""
        return self.open_store(incarnation="manager-w32385-restarted")

    # -- 1: the restart discovers the exact ended runtime --------------------

    def test_a_restart_adopts_the_exact_ended_runtime_as_quiescent(self):
        """NOT running, and NOT absent.

        Membership in `ps --all` includes exited containers, so a listing
        alone would say `running`; an empty listing would say nothing at all.
        The exact identity is asked about, and `quiescent` is the answer --
        a worker that finished, whose container is still there.
        """
        _adapter, _roots, _given, _assignment, runtime_id = self.ended()
        again = self.restarted()
        adapter = self.adapter(roots=self.roots(), mounts=self.plan(
            self.roots()))
        answer = reconcile_runtime(again, adapter, attempt_id=self.attempt)

        self.assertEqual(self.attempt_row(again)["runtime_id"], runtime_id)
        self.assertEqual(self.attempt_row(again)["execution_runtime"],
                         "quiescent", answer)
        # AND THE ENGINE STILL HOLDS IT: adoption observed, it did not remove.
        self.assertEqual(len(self.carrying(self.labels())), 1)

    def test_an_exited_container_does_not_admit_a_replacement(self):
        """THE LANE IS NOT REUSABLE while the domain still exists.

        A runtime object that exists is a process domain that exists, and
        starting a replacement beside it is the compounding this whole
        ordering is arranged against.
        """
        _adapter, roots, _given, _assignment, _runtime = self.ended()
        again = self.restarted()
        fresh = self.adapter(roots=roots, mounts=self.plan(roots))
        reconcile_runtime(again, fresh, attempt_id=self.attempt)
        # THE ROOT IS COMPOSED ONCE AND FROZEN, so the replacement start is
        # offered the same one -- which is what a real replacement would have.
        inputs = roots["inputs"]
        with self.assertRaises(ContractRefusal) as refused:
            request_runtime_start(again, fresh, attempt_id=self.attempt,
                                  inputs=inputs)
        self.assertIn("execution is", str(refused.exception))
        self.assertEqual(len(self.carrying(self.labels())), 1)

    def test_exited_but_present_does_not_satisfy_cleanup(self):
        """Cleanup is authorized by an intake receipt, and an exited container
        is not one. The engine is not reached at all."""
        adapter, _roots, _given, _assignment, _runtime = self.ended()
        again = self.restarted()
        reconcile_runtime(again, adapter, attempt_id=self.attempt)
        before = len(self.engine_calls)
        self.session.live_assignment = None
        blocked = authorize_cleanup(again, self.port, adapter,
                                    attempt_id=self.attempt,
                                    retention_policy_digest=RETENTION)
        self.assertEqual(self.attempt_row(again)["cleanup"],
                         "blocked-on-intake", blocked)
        self.assertEqual(len(self.engine_calls), before)
        self.assertEqual(len(self.carrying(self.labels())), 1)

    # -- 2: removal, absence, teardown, and only then reuse ------------------

    def test_force_removal_absence_teardown_then_and_only_then_reuse(self):
        """THE WHOLE ORDERING, TRACED, WITH A SIBLING BESIDE IT AND THE LANE
        REUSED AFTERWARDS.

        Review [P1] x3, and all three were the same shape: the case asserted
        the FINAL STATE and called it an ordering, a bound and a reuse.

          - the final state is satisfied by a teardown that ran BEFORE
            absence was proved, which is the process-domain invariant this
            follow-up exists to preserve. So one shared trace is written by
            the engine's remove/inspect boundary and by BOTH provider
            teardowns, and the order is compared rather than the outcome.
          - nothing constructed an unrelated attempt, so a cleanup that
            deleted by a broad label or by the credential HOME rather than by
            the exact attempt would have passed. A sibling runtime and a
            sibling credential root are here, and both survive.
          - and nothing was ever started after the crossing, so a manager
            that permanently refused reuse would have passed too. A real
            second attempt takes the lane afterwards.
        """
        delivery = self.credential()
        adapter, roots, given, _assignment, runtime_id = self.ended(
            credential_delivery=delivery)
        declared = self.declarations(given)
        retain_manifest(self.store, given, "inputManifest")

        # AN UNRELATED ATTEMPT, with its own credential root in the SAME
        # assignment-scoped home, which is where a broad cleanup would reach.
        sibling = f"{self.attempt}-sibling"
        home = adapter._credential_home()
        theirs = home.materialize(
            credentials.resolved_delivery(
                ["registry"],
                profile={"registry": {"provider": "vault",
                                      "reference": "ref-registry"}}),
            attempt_id=sibling,
            workspace_group=self.group,
            credential_provider=lambda name, reference: f"bearer-{name}")
        self.addCleanup(self._release_credential, home, theirs)

        again = self.restarted()
        adopting = self.adapter(roots=roots, mounts=self.plan(roots),
                                outputs=declared,
                                credential_delivery=delivery,
                                launch_delivery=adapter.launch_delivery)
        # ONE SHARED TRACE, written by the three boundaries whose ORDER is
        # the invariant. Separate lists could not be compared for order.
        order = []
        engine = adopting.run

        class Traced:
            def __call__(self, argv, *, seconds=None):
                if "rm" in argv:
                    order.append("force-remove")
                if "inspect" in argv:
                    order.append("observe")
                return engine(argv)

        adopting.run = Traced()
        credentials_ended, launch_ended = adopting._torn_down, \
            adopting._launch_ended
        adopting._torn_down = lambda observed: (
            order.append("credentials"), credentials_ended(observed))[1]
        adopting._launch_ended = lambda proved, why: (
            order.append("launch"), launch_ended(proved, why))[1]

        reconcile_runtime(again, adopting, attempt_id=self.attempt)
        self.produced(roots, declared)
        self.published(roots, declared)
        observe(again, attempt_id=self.attempt, axis="worker_disposition",
                value="completed")
        request_freeze(again, self.port, adopting, attempt_id=self.attempt,
                       disposition="completed")
        receipt = request_intake(again, self.port, adopting,
                                 attempt_id=self.attempt)
        decide_retention(
            again, self.port, adopting, attempt_id=self.attempt,
            artifact_ids=[one["artifact_id"] for one in receipt["artifacts"]],
            disposition="discard-after-intake",
            retention_policy_digest=RETENTION)

        # NO REPLACEMENT BEFORE THE CROSSING.
        with self.assertRaises(ContractRefusal):
            request_runtime_start(again, adopting, attempt_id=self.attempt,
                                  inputs=roots["inputs"])
        self.assertEqual(len(self.carrying(self.labels())), 1)

        self.session.live_assignment = None
        order.clear()
        settled = authorize_cleanup(again, self.port, adopting,
                                    attempt_id=self.attempt,
                                    retention_policy_digest=RETENTION)
        self.assertEqual(settled["cleanup"], "complete", settled)

        # THE ORDER ITSELF: force-removal, then the observation that proves
        # absence, and only THEN either provider's teardown.
        self.assertIn("force-remove", order)
        self.assertIn("observe", order)
        removal, proof = (order.index("force-remove"),
                          order.index("observe"))
        self.assertLess(removal, proof, order)
        for provider in ("credentials", "launch"):
            self.assertIn(provider, order, order)
            self.assertLess(proof, order.index(provider), order)

        self.assertEqual(self.carrying(self.labels()), [])
        self.assertEqual(delivery.state, "torn-down")
        self.assertFalse(os.path.exists(delivery.root))
        self.assertFalse(os.path.exists(adopting.launch_delivery.root))
        # THE SIBLING SURVIVED ALL OF IT, root and live bearer both.
        self.assertTrue(os.path.isdir(theirs.root),
                        "the cleanup reached an unrelated attempt's root")
        self.assertEqual(theirs.state, "live")

        # AND THE LANE IS REUSED: a real second attempt is offered, claimed,
        # activated and STARTED after the crossing. Exactly one replacement,
        # where zero were permitted before it.
        self.attempt = f"{self.attempt}-next"
        # W16823: the authority answers a CLOSED claim result, so a case that
        # re-points the fence re-points the member rather than the whole.
        self.session.claim_answer = dict(self.session.claim_answer,
                                         assignment=dict(self.live))
        self.session.live_assignment = dict(self.live)
        fresh_roots = self.roots()
        fresh_given, fresh_assignment = self.activated(store=again)
        fresh_inputs = self.composed(fresh_roots, fresh_given,
                                     fresh_assignment)
        replacement = self.adapter(roots=fresh_roots,
                                   mounts=self.plan(fresh_roots))
        request_runtime_start(again, replacement, attempt_id=self.attempt,
                              inputs=fresh_inputs)
        self.assertEqual(len(self.carrying(self.labels())), 1)
        self.assertIsNotNone(self.attempt_row(again)["runtime_id"])

    def container(self, labels, name_hint):
        """One REAL container carrying exactly these labels, registered for
        removal before it is created."""
        name = f"{MARK}-{name_hint}-{uuid.uuid4().hex[:8]}"
        self.made.append(name)
        argv = [self.engine, "run", "--detach", "--name", name,
                "--entrypoint", "sleep"]
        for key, value in sorted(labels.items()):
            argv += ["--label", f"{LABEL_PREFIX}{key}={value}"]
        argv += [self.image_digest, "600"]
        made = subprocess.run(argv, capture_output=True, timeout=300)
        self.assertEqual(made.returncode, 0,
                         made.stderr.decode("utf-8", "replace"))
        return made.stdout.decode("utf-8").strip()

    def test_two_ended_restart_candidates_cancel_without_removing_either(
            self):
        """MULTIPLICITY AT THE ENDED-RESTART SEAM, which is reachable.

        The previous round delegated this to W6636's stranger case and the
        review refused that, correctly: that case races two RUNNING
        containers. Two candidates discovered by a RESTART, one of them the
        exact ended target, is a different state and this is it.

        The manager cancels rather than choosing, and — the half that matters
        for a cleanup keyed on labels — it removes NEITHER.
        """
        _adapter, roots, _given, _assignment, runtime_id = self.ended()
        stranger = self.container(self.labels(), "ended-stranger")
        again = self.restarted()
        adapter = self.adapter(roots=roots, mounts=self.plan(roots))

        decided = reconcile_runtime(again, adapter, attempt_id=self.attempt)

        self.assertEqual(decided["decision"], "cancel", decided)
        self.assertIn("2 runtimes", decided["why"])
        self.assertEqual(self.attempt_row(again)["execution_runtime"],
                         "cancel-requested")
        # NEITHER CONTAINER WENT. A reconciliation that cannot say which one
        # is the attempt's may not remove either, and the engine is asked.
        held = self.carrying(self.labels())
        self.assertEqual(len(held), 2, held)
        for one in (runtime_id, stranger):
            self.assertTrue(any(one.startswith(seen[:12]) or
                                seen.startswith(one[:12]) for seen in held),
                            (one, held))

    def test_an_unrelated_attempts_runtime_survives_the_target_cleanup(self):
        """A SIBLING RUNTIME, not only a sibling root.

        The previous round proved a sibling credential root survives. A
        cleanup that removed containers by a BROAD label — the assignment
        rather than the attempt — would still have passed that. This starts a
        real sibling container under a DIFFERENT attempt's labels and requires
        it to outlive the target's whole crossing.
        """
        delivery = self.credential()
        adapter, roots, given, _assignment, _runtime = self.ended(
            credential_delivery=delivery)
        sibling_labels = dict(self.labels(),
                              runtime_attempt_id=f"{self.attempt}-sibling")
        sibling = self.container(sibling_labels, "sibling-runtime")
        declared = self.declarations(given)
        retain_manifest(self.store, given, "inputManifest")

        again = self.restarted()
        adopting = self.adapter(roots=roots, mounts=self.plan(roots),
                                outputs=declared,
                                credential_delivery=delivery,
                                launch_delivery=adapter.launch_delivery)
        reconcile_runtime(again, adopting, attempt_id=self.attempt)
        self.produced(roots, declared)
        self.published(roots, declared)
        observe(again, attempt_id=self.attempt, axis="worker_disposition",
                value="completed")
        request_freeze(again, self.port, adopting, attempt_id=self.attempt,
                       disposition="completed")
        receipt = request_intake(again, self.port, adopting,
                                 attempt_id=self.attempt)
        decide_retention(
            again, self.port, adopting, attempt_id=self.attempt,
            artifact_ids=[one["artifact_id"] for one in receipt["artifacts"]],
            disposition="discard-after-intake",
            retention_policy_digest=RETENTION)
        self.session.live_assignment = None
        settled = authorize_cleanup(again, self.port, adopting,
                                    attempt_id=self.attempt,
                                    retention_policy_digest=RETENTION)

        self.assertEqual(settled["cleanup"], "complete", settled)
        self.assertEqual(self.carrying(self.labels()), [])
        # THE SIBLING IS STILL RUNNING, asked of the daemon by ITS labels.
        surviving = self.carrying(sibling_labels)
        self.assertEqual(len(surviving), 1, surviving)
        self.assertEqual(self.inspected(sibling)["State"]["Status"],
                         "running")

    def test_a_destroy_answer_about_another_runtime_is_refused(self):
        """THE REACHABLE IDENTITY DISAGREEMENT, at the answer boundary.

        The disagreement my earlier case tried to build — an attempt row
        edited behind the manager — is unreachable, because `_attach` is
        effectively-once and the first incarnation's attachment replays. The
        one that IS reachable is the adapter answering the destroy about a
        DIFFERENT runtime, which `intake._destroyed` compares and refuses.
        """
        adapter, roots, given, _assignment, runtime_id = self.ended()
        declared = self.declarations(given)
        retain_manifest(self.store, given, "inputManifest")
        again = self.restarted()
        adopting = self.adapter(roots=roots, mounts=self.plan(roots),
                                outputs=declared,
                                launch_delivery=adapter.launch_delivery)
        reconcile_runtime(again, adopting, attempt_id=self.attempt)
        self.produced(roots, declared)
        self.published(roots, declared)
        observe(again, attempt_id=self.attempt, axis="worker_disposition",
                value="completed")
        request_freeze(again, self.port, adopting, attempt_id=self.attempt,
                       disposition="completed")
        receipt = request_intake(again, self.port, adopting,
                                 attempt_id=self.attempt)
        decide_retention(
            again, self.port, adopting, attempt_id=self.attempt,
            artifact_ids=[one["artifact_id"] for one in receipt["artifacts"]],
            disposition="discard-after-intake",
            retention_policy_digest=RETENTION)

        honest = adopting.destroy
        adopting.destroy = lambda command: dict(
            honest({**command, "runtime_id": command["runtime_id"]}),
            runtime_id=f"{runtime_id}-somebody-else")
        self.session.live_assignment = None
        with self.assertRaises(ContractRefusal) as caught:
            authorize_cleanup(again, self.port, adopting,
                              attempt_id=self.attempt,
                              retention_policy_digest=RETENTION)
        self.assertEqual(caught.exception.code, "identity-mismatch")
        self.assertEqual(self.attempt_row(again)["cleanup"], "pending")

    def test_an_observation_the_adapter_cannot_make_never_releases_the_lane(
            self):
        """Uncertainty preserves the retry obligation.

        An engine that cannot say what the exact runtime is leaves the axis
        `uncertain`, and the frozen asymmetry then refuses cleanup outright —
        so the lane stays held rather than being released on a failure to
        look.
        """
        adapter, roots, _given, _assignment, _runtime = self.ended()
        again = self.restarted()
        blind = self.adapter(roots=roots, mounts=self.plan(roots),
                             launch_delivery=adapter.launch_delivery)
        blind.observe = lambda runtime_id: {
            "state": "uncertain", "why": "the engine could not be inspected",
            "mounts": None}
        reconcile_runtime(again, blind, attempt_id=self.attempt)
        self.assertEqual(self.attempt_row(again)["execution_runtime"],
                         "uncertain")
        self.session.live_assignment = None
        # AND THE ORDER IS WORTH STATING. The frozen asymmetry -- `uncertain`
        # never becomes `destroyed` -- sits BELOW the intake-receipt check, so
        # an attempt with no receipt blocks on intake first and never reaches
        # it. Asserting `quiescence-unknown` here would have been asserting a
        # refusal this state cannot reach; what IS true is that nothing was
        # released.
        blocked = authorize_cleanup(again, self.port, blind,
                                    attempt_id=self.attempt,
                                    retention_policy_digest=RETENTION)
        self.assertNotIn("cleanup", blocked)
        self.assertEqual(self.attempt_row(again)["cleanup"],
                         "blocked-on-intake")
        self.assertEqual(self.attempt_row(again)["execution_runtime"],
                         "uncertain")
        # THE LANE IS STILL HELD: the container is there and no replacement
        # may start.
        self.assertEqual(len(self.carrying(self.labels())), 1)
        with self.assertRaises(ContractRefusal):
            request_runtime_start(again, blind, attempt_id=self.attempt,
                                  inputs=roots["inputs"])


class DockerEndedRuntimeAdoption(EndedRuntimeAdoption, unittest.TestCase):
    engine = "docker"
    required = True


class PodmanEndedRuntimeAdoption(EndedRuntimeAdoption, unittest.TestCase):
    engine = "podman"
    required = False
