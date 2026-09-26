"""W257624 ownership edge probes: stale pre-claim and distinct OS process.

Real disposable stores/files and supported restore/grant calls. Checkpoint resets
are labelled controlled file writes, not real Git or engine operations. The child
opens its own store and profile; no inherited registry or connection is modified.
"""
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest import mock

import test_restore_outside_the_lock as author


CHILD = r'''
import json, sys
from pathlib import Path
from baton_v12.worker_manager import ControlStore
from baton_v12.worker_manager.review_cycles import restore_abandoned_correction
from tests.manager.test_review_cycles import Profile, NOW
p = json.load(sys.stdin)
profile = Profile()
evidence = p['evidence']
revision = int(evidence['head'], 16)
profile.held[revision] = evidence
profile.current_revision = revision
original = profile.restore_checkpoint
def restoring(repository, evidence):
    answer = original(repository, evidence)
    Path(p['marker']).write_text('restored checkpoint')
    return answer
profile.restore_checkpoint = restoring
store = ControlStore.open(p['store'], incarnation=p['incarnation'], clock=lambda: NOW)
try:
    result = restore_abandoned_correction(store, attempt_id=p['attempt'],
        generation=2, retention_policy_digest=p['policy'], profile=profile)
    print(json.dumps(result))
finally:
    store.close()
'''


class RegistryEdges(author.RestoreOutsideTheLock):
    def marker(self):
        path = Path(self.line_path) / 'review-registry-successor.txt'
        path.write_text('abandoned scratch')
        return path

    def successor(self, path):
        granted = self.granted(self.line_id, 3,
                               based=self.checkpoint['checkpoint_id'])
        self.assertEqual(granted['state'], 'active')
        path.write_text('successor work must survive')

    def test_stale_preclaim_caller_cannot_restore_after_successor_admission(self):
        self.abandoned()
        marker = self.marker()
        other = author.ControlStore.open(self.control_path,
            incarnation=self.store.incarnation, clock=lambda: author.NOW)
        self.addCleanup(other.close)
        claim = author.review_cycles._claim_restoration
        original = self.profile.restore_checkpoint
        entered = []
        crossed = []
        results = []

        def restoring(repository, evidence):
            crossed.append(repository)
            answer = original(repository, evidence)
            marker.write_text('restored checkpoint')
            return answer

        def delayed(*args):
            if not entered:
                entered.append(True)
                # A completed its preliminary reads but has not acquired guard.
                results.append(self.restore(store=other))
                self.successor(marker)
            return claim(*args)

        self.profile.restore_checkpoint = restoring
        with mock.patch.object(author.review_cycles, '_claim_restoration', delayed):
            answer = self.restore()
        self.assertEqual(answer, results[0])
        self.assertEqual(len(crossed), 2)
        self.assertEqual(marker.read_text(), 'successor work must survive')

    def test_another_process_cannot_release_while_parent_restoration_is_live(self):
        self.abandoned()
        marker = self.marker()
        original = self.profile.restore_checkpoint
        results = []

        def restoring(repository, evidence):
            request = dict(store=self.control_path, incarnation=self.store.incarnation,
                           attempt=author.ABANDONED, policy=author.RETENTION,
                           evidence=evidence, marker=str(marker))
            child = subprocess.run([sys.executable, '-B', '-W',
                'error::ResourceWarning', '-c', CHILD], input=json.dumps(request),
                text=True, capture_output=True, timeout=10, check=False)
            self.assertEqual(child.returncode, 0, child.stderr)
            results.append(json.loads(child.stdout))
            self.successor(marker)
            answer = original(repository, evidence)
            marker.write_text('restored checkpoint')
            return answer

        self.profile.restore_checkpoint = restoring
        answer = self.restore()
        self.assertEqual(answer, results[0])
        self.assertEqual(self.line_row()['state'], 'writing')
        self.assertEqual(marker.read_text(), 'successor work must survive')


def load_tests(loader, standard, pattern):
    return unittest.TestSuite(RegistryEdges(name) for name in (
        'test_stale_preclaim_caller_cannot_restore_after_successor_admission',
        'test_another_process_cannot_release_while_parent_restoration_is_live'))
