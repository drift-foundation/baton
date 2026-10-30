"""W325959 -- the native task-token lifetime, at the acquisition boundary.

THE RECORDED FAILURE THESE CASES CLOSE. The native pilot's implementation
attempt had its workspace token expire at 900 seconds with zero renewals while
its Job allowed a 3600-second provider turn
(`OWNER-FAILURE-EVIDENCE-20261019.md`). The cause was one unsupplied argument:
`workspaces.PreparedGovernance.reserve` acquired with neither `seconds` nor a
permission, so `tokens.acquire` took its `LIFETIME_SECONDS` default.

WHAT THE NATIVE MECHANISM IS, and why it is a lifetime rather than an
envelope. The native stop owner is the serving loop's reclaim pass:
`tokens.Governance.overdue` answers only for an EXPIRED token and
`tools/job_manager._reclaiming` acts on what it answers. Nothing native reads
an envelope's `stop_at`, so an envelope would record an execution deadline no
native party enforces. The bounded `seconds` the acquisition already supports
is enforced by the owner that already exists.

DETERMINISTIC: a real `ControlStore` on a fake clock, no engine, no provider,
no container and no process. Nothing here starts anything.
"""
import os
import tempfile
import unittest

from baton_v12.contracts import ContractRefusal
from baton_v12.job_manager import execution_limits
from baton_v12.worker_manager import attempts, tokens, workspaces
from baton_v12.worker_manager.store import ControlStore

INSTANT = "2026-10-22T12:00:00.000Z"


class NativeTaskTokenLifetime(unittest.TestCase):
    """The lifetime the Job's own resolution composes, and what it preserves."""

    def test_the_lifetime_covers_every_bounded_operation_it_names(self):
        """Not a floor: each addend is a named bound, and the sum is exact."""
        resolved = execution_limits.resolved({}, 1)
        provider = resolved["boundaries"]["provider_turn"]["seconds"]
        verification = resolved["boundaries"]["ordinary_verification"]["seconds"]
        expected = (execution_limits.CHECKOUT_STEPS
                    * execution_limits.CHECKOUT_SECONDS
                    + provider + verification
                    + execution_limits.CLEANUP_RESERVE_SECONDS)
        self.assertEqual(execution_limits.task_token_seconds(resolved),
                         expected)
        # AND IT IS LONGER THAN THE DEFAULT THAT CAUSED THE FAILURE.
        self.assertGreater(execution_limits.task_token_seconds(resolved),
                           tokens.LIFETIME_SECONDS)
        # Specifically, it covers one whole provider turn, which 900 did not.
        self.assertGreater(execution_limits.task_token_seconds(resolved),
                           provider)

    def test_it_FOLLOWS_THE_JOBS_OWN_SELECTION_rather_than_a_constant(self):
        """A Job that selected smaller limits gets a smaller token."""
        selected = execution_limits.resolved(
            {"provider_turn_seconds": 120,
             "verification_command_seconds": 45}, 1)
        default = execution_limits.resolved({}, 1)
        self.assertLess(execution_limits.task_token_seconds(selected),
                        execution_limits.task_token_seconds(default))

    def test_THE_PER_INVOCATION_CEILINGS_ARE_UNCHANGED_BY_IT(self):
        """A longer token does not lengthen a turn or a verification."""
        before = execution_limits.resolved({}, 1)
        execution_limits.task_token_seconds(before)
        after = execution_limits.resolved({}, 1)
        self.assertEqual(before, after)
        self.assertEqual(after["boundaries"]["provider_turn"]["seconds"], 3600)
        self.assertEqual(
            after["boundaries"]["ordinary_verification"]["seconds"], 900)
        self.assertEqual(after["scope"], execution_limits.SCOPE)

    def test_a_NEGATIVE_allowance_is_REFUSED_not_clamped(self):
        resolved = execution_limits.resolved({}, 1)
        for bad in ({"checkout_steps": -1}, {"cleanup_reserve": -1}):
            with self.subTest(**bad):
                with self.assertRaises(Exception):
                    execution_limits.task_token_seconds(resolved, **bad)


class TheAcquisitionTakesIt(unittest.TestCase):
    """`reserve` with and without a resolved lifetime, over a real store."""

    def setUp(self):
        root = tempfile.TemporaryDirectory(prefix="w325959-native-")
        self.addCleanup(root.cleanup)
        self.instant = INSTANT
        self.store = ControlStore.open(
            os.path.join(root.name, "control.sqlite3"),
            incarnation="w325959", clock=lambda: self.instant)
        self.addCleanup(self.store.close)
        self.attempt = {"runtime_attempt_id": "attempt-native-1",
                        "workspace_device": 66306, "workspace_inode": 4242}

    def governance(self, seconds=None):
        held = workspaces.prepared_workspace_governance(
            self.store, self.attempt["runtime_attempt_id"], seconds=seconds)
        # The preparation predicate is this manager's own and needs a recorded
        # completed preparation; these cases are about the LIFETIME the
        # acquisition composes, so the condition is answered as satisfied and
        # nothing else about it is changed.
        return held

    def test_the_governance_ACCEPTS_a_resolved_lifetime(self):
        """The one argument whose absence caused the pilot failure."""
        self.assertIsNotNone(self.governance(seconds=7320))
        # And it is optional, so every pre-existing caller is unaffected.
        self.assertIsNotNone(self.governance())

    def test_acquire_REFUSES_a_lifetime_beside_a_permission(self):
        """The two are exclusive, so a deployment cannot supply both."""
        domain = tokens.domain_of("workspace", "line/workspace")
        envelope = {"started_at": INSTANT,
                    "stop_at": "2026-10-22T13:00:00.000Z",
                    "expires_at": "2026-10-22T13:10:00.000Z",
                    "policy": {"run": "r", "job": "j"}}
        with self.assertRaises(ContractRefusal) as caught:
            tokens.acquire(self.store, domain, operation="runtime.start:x",
                           execution="attempt-native-1", seconds=7320,
                           permission=envelope)
        self.assertIn("not both", str(caught.exception))

    def test_a_token_at_the_NATIVE_lifetime_is_not_overdue_before_it_expires(self):
        """Expiry is the native stop trigger, so the lifetime IS the bound."""
        domain = tokens.domain_of("workspace", "line/workspace")
        seconds = execution_limits.task_token_seconds(
            execution_limits.resolved({}, 1))
        token = tokens.acquire(self.store, domain,
                               operation="runtime.start:native",
                               execution="attempt-native-1",
                               attempt="attempt-native-1", seconds=seconds)
        self.assertEqual(token["seconds"], seconds)
        held = tokens.token_of(self.store, domain, token["generation"])
        self.assertFalse(held["expired"])
        # PAST THE 900-SECOND DEFAULT AND STILL VALID -- the whole point.
        self.instant = "2026-10-22T12:20:00.000Z"
        held = tokens.token_of(self.store, domain, token["generation"])
        self.assertFalse(held["expired"],
                         "a native token must survive past the old default")
        # AND STILL BOUNDED: past its own lifetime it expires, which is what
        # Governance.overdue -- and therefore _reclaiming -- acts on.
        self.instant = "2026-10-22T15:00:00.000Z"
        held = tokens.token_of(self.store, domain, token["generation"])
        self.assertTrue(held["expired"], "the lifetime is still a bound")
        self.assertFalse(held["returned"],
                         "expiry is not release: the resource stays held")


if __name__ == "__main__":                                # pragma: no cover
    unittest.main()
