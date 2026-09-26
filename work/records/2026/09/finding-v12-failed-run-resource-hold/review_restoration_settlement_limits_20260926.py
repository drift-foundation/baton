"""Reviewer271927: deterministic fake-profile/real-store settlement limitations.

No live child/provider/engine/Git. Empty-claim record has no lifecycle-version evidence;
dirty validation models an interrupted reset/clean, with all recorded effects ended.
"""
from pathlib import Path
import unittest

import test_restore_outside_the_lock as author
from baton_v12.contracts import ContractRefusal
from baton_v12.checkpoint_profiles import ProfileRefusal


class SettlementLimits(author.RestoreOutsideTheLock):
    def test_empty_account_without_coverage_provenance_stays_held(self):
        self.abandoned()
        honest = self.profile.restore_checkpoint
        def stop(repository, evidence, *, runner=None):
            raise RuntimeError("interrupted before any recorded command")
        self.profile.restore_checkpoint = stop
        with self.assertRaises(RuntimeError):
            self.restore()
        self.profile.restore_checkpoint = honest
        recovery = author.review_cycles._restore_operation_id(author.RESTORE_KIND, author.ABANDONED, 2)
        claim = self.store.operation_record(author.review_cycles._execution_id(recovery, 1))
        _, document = self.store.replay(author.review_cycles._execution_id(recovery, 1),
                                       claim["signature"], kind=author.review_cycles.RESTORE_EXECUTION_KIND)
        # These are the same fields as pre-launch-accounting episodes: there is no
        # certified coverage/version bit distinguishing stopped-before-launch from legacy.
        self.assertEqual(set(document), {"schema", "recovery", "episode", "executor"})
        with self.assertRaises(ContractRefusal):
            self.settle(store=self.fresh_manager())

    def test_ended_partial_restore_can_be_settled_for_retry(self):
        self.abandoned()
        dirty = Path(self.temporary.name) / "review-partial-restore"
        honest_restore = self.profile.restore_checkpoint
        honest_validate = self.profile.validate
        def partial(repository, evidence, *, runner=None):
            honest_restore(repository, evidence, runner=runner)
            dirty.write_text("interrupted after partial filesystem effect")
            raise RuntimeError("partial restoration stopped")
        self.profile.restore_checkpoint = partial
        with self.assertRaises(RuntimeError):
            self.restore()
        self.profile.restore_checkpoint = honest_restore
        def validate(repository, evidence, *, current=False, **kwargs):
            if current and dirty.exists():
                raise ProfileRefusal("checkout is partially restored, not clean")
            return honest_validate(repository, evidence, current=current, **kwargs)
        self.profile.validate = validate
        settled = self.settle(store=self.fresh_manager())
        self.assertEqual(settled["episode"], 1)


def load_tests(loader, standard, pattern):
    return unittest.TestSuite(SettlementLimits(name) for name in (
        "test_empty_account_without_coverage_provenance_stays_held",
        "test_ended_partial_restore_can_be_settled_for_retry"))
