"""Run the preserved overlap schedule with two handles of ONE manager.

Only the second ControlStore.open incarnation operand changes. Store.open permits
that configuration; no product behavior or durable state is patched. The original
probe uses real disposable bytes and a labelled controlled profile effect.
"""
import unittest
from unittest import mock

import review_restore_overlap_20260926 as historical


class SameManager(historical.Overlap):
    def test_two_handles_of_one_manager_cannot_overlap_restoration(self):
        actual_open = historical.ControlStore.open

        def open_for_manager(path, *, incarnation, clock):
            if incarnation == 'second-restorer':
                incarnation = self.store.incarnation
            return actual_open(path, incarnation=incarnation, clock=clock)

        with mock.patch.object(historical.ControlStore, 'open',
                               side_effect=open_for_manager):
            self.test_a_delayed_restorer_cannot_overwrite_an_admitted_successor()


def load_tests(loader, standard, pattern):
    return unittest.TestSuite([SameManager(
        'test_two_handles_of_one_manager_cannot_overlap_restoration')])
