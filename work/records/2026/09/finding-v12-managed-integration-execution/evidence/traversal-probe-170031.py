"""Bounded, runnable, measured traversal probe for the managed path.

Review claim169999 asked that diagnostics be bounded runnable measured
evidence rather than ad-hoc. This drives the real selected deployment to its
current furthest point and prints where it stops.
"""
import time
from unittest import mock

from tests.tools import test_stage_execution as T
from tests.job_manager import fixtures
from baton_v12.job_manager import sweep as tick
from tools import integration_worker


class Selected(T.TheComposedJobTraversesReviewAndAcceptance):
    def serving(self, **members):
        members.setdefault("integration_preparation", True)
        return super().serving(**members)


def main():
    started = time.perf_counter()
    case = Selected("test_the_implementation_handoff_moves_the_work_to_the_review_route")
    case.setUp()
    try:
        held = case.reviewed()
        prep = held.composed.deployment._integration_operations._preparation
        # THE DEPLOYMENT ACT, not the coordinator's: the child route's handler.
        held.composed.deployment.authority.add_route_handler(
            "integration-preparation", "baton.integrator")
        seen = []
        real = integration_worker.ManagedPreparation.admit

        def traced(self, operations, stage, job):
            try:
                return real(self, operations, stage, job)
            except Exception as failed:
                seen.append((type(failed).__name__, str(failed)[:240]))
                raise

        with mock.patch.object(integration_worker.ManagedPreparation,
                               "admit", traced):
            for _ in range(30):
                tick(held.job, held.composed, now=fixtures.NOW)
                if prep.started:
                    break
        print("stops at:", seen[0] if seen else None)
        print("states:", case.states(held.job, held.composed))
        print("preparations started:", len(prep.started))
    finally:
        case.doCleanups()
    print("seconds:", round(time.perf_counter() - started, 6))


if __name__ == "__main__":
    main()
