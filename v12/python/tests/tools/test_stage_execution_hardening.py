"""Construction cleanup across concrete stage-deployment boundaries.

W103950: work/records/2026/09/finding-v12-stage-composition-hardening/.
Use the established isolated stores and engine; inject only the failing step
and observe the real close methods, rather than supplying fake handle APIs.
"""

from contextlib import ExitStack
from unittest import mock

from baton_v12.job_manager import scheduler
from tools import single_worker, stage_execution
from tests.job_manager.fixtures import NOW
from tests.tools import test_stage_execution as assembly
from tests.tools.test_single_worker import Engine


class ConstructionUnwindsConcreteHandles(assembly.ServingCase):

    def failed_construction(self, cut):
        job, control = self.stores("hardening-construction")
        failure = RuntimeError("injected construction failure")
        opened, closed = [], []
        names = {}
        authority_open = stage_execution.Authority.open
        authority_dispose = stage_execution.Authority.dispose
        coordinator_open = stage_execution.IntegrationStore.open
        coordinator_close = stage_execution.IntegrationStore.close
        preflight = single_worker.worker_preflight
        worker_operations = single_worker.worker_operations
        worker_close = single_worker._Operations.close

        def acquired(owner, name, close):
            names[id(owner)] = name
            opened.append(name)

            def cleanup_if_unwinding_missed_it():
                if name not in closed:
                    close(owner)

            self.addCleanup(cleanup_if_unwinding_missed_it)
            return owner

        def open_authority(*args, **kwargs):
            return acquired(authority_open(*args, **kwargs), "authority",
                            authority_dispose)

        def open_coordinator(*args, **kwargs):
            if cut == "coordinator":
                raise failure
            return acquired(coordinator_open(*args, **kwargs), "coordinator",
                            coordinator_close)

        def worker_preflight(given, *args, **kwargs):
            if cut == "preflight" and given["launch_role"] == "review":
                raise failure
            return preflight(given, *args, **kwargs)

        def open_worker(given, *args, **kwargs):
            if cut == "worker" and given["launch_role"] == "review":
                raise failure
            return acquired(worker_operations(given, *args, **kwargs),
                            given["launch_role"], worker_close)

        def observed_close(original):
            def close(owner):
                original(owner)
                closed.append(names[id(owner)])
            return close

        with ExitStack() as patches:
            patches.enter_context(mock.patch.object(
                stage_execution.Authority, "open", side_effect=open_authority))
            patches.enter_context(mock.patch.object(
                stage_execution.Authority, "dispose", observed_close(authority_dispose)))
            patches.enter_context(mock.patch.object(
                stage_execution.IntegrationStore, "open", side_effect=open_coordinator))
            patches.enter_context(mock.patch.object(
                stage_execution.IntegrationStore, "close", observed_close(coordinator_close)))
            patches.enter_context(mock.patch.object(
                single_worker, "worker_preflight", side_effect=worker_preflight))
            patches.enter_context(mock.patch.object(
                single_worker, "worker_operations", side_effect=open_worker))
            patches.enter_context(mock.patch.object(
                single_worker._Operations, "close", observed_close(worker_close)))
            activate = patches.enter_context(mock.patch.object(
                scheduler, "activate_pool", side_effect=AssertionError("pool reached after failure")))
            with self.assertRaises(RuntimeError) as caught:
                stage_execution.operations_from(
                    self.composed_document(), job, control, engine_run=Engine(),
                    credential_provider=lambda provider, reference: self.secret,
                    clock=lambda: NOW, checkout=self.checkout)
            self.assertIs(caught.exception, failure)
            activate.assert_not_called()

        self.assertIsNone(scheduler.active_generation(job))
        return opened, closed

    def test_preflight_failure_disposes_the_acquired_authority(self):
        opened, closed = self.failed_construction("preflight")
        self.assertEqual(opened, ["authority"])
        self.assertEqual(closed, ["authority"])

    def test_coordinator_open_failure_disposes_the_acquired_authority(self):
        opened, closed = self.failed_construction("coordinator")
        self.assertEqual(opened, ["authority"])
        self.assertEqual(closed, ["authority"])

    def test_worker_construction_failure_closes_every_acquired_handle(self):
        opened, closed = self.failed_construction("worker")
        self.assertEqual(opened, ["authority", "coordinator", "implementation"])
        self.assertEqual(closed, ["implementation", "coordinator", "authority"])
