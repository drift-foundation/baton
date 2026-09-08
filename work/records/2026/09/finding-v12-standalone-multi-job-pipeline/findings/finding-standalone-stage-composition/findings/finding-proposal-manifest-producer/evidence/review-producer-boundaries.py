"""W103874 independent probes over real frozen-output and assignment reads.

Only disposable test stores are used. Existing fixture-owned cleanup applies.
The runtime seal and Authority remain supplied fixtures; no engine/Git operation
or live coordination store is involved. Run directly with Python from any cwd.
"""

import copy
from pathlib import Path
import sys
import unittest

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "AGENTS.md").is_file())
sys.path[:0] = [str(ROOT / "v12/python/src"), str(ROOT / "v12/python")]

from baton_v12.contracts import ContractRefusal, digest
from baton_v12.integration import driver
from baton_v12.worker_manager import load_manifest, record_frozen_result, request_freeze
from tests.manager.test_output import ATTEMPT, Collector, OutputCase, sealed
from tests.integration.test_driver import CLAIM, LinePublisher, PRIVATE_BASE, PRIVATE_HEAD


class ProducerBoundaryReview(unittest.TestCase):
    def prepared(self, result_id="result-review-1"):
        case = OutputCase()
        case.setUp()
        self.addCleanup(case.doCleanups)
        outputs = [dict(one, type="git-change-proposal") for one in case.declaration["outputs"]]
        case.redeclared(outputs=outputs)
        case.attempt()
        measured = case.present()
        output = measured[0]
        output["type"] = "git-change-proposal"
        entries = output["content_manifest"]["entries"]
        entries[0]["path"] = "objects.bundle"
        output["content_manifest"]["tree_digest"] = digest(entries)
        output["artifact"]["content_digest"] = digest(entries)
        output["result_metadata"] = {CLAIM: {
            "base": PRIVATE_BASE, "head": PRIVATE_HEAD,
            "transport": "objects.bundle", "recap": "bounded independent review fixture"}}
        result = case.result(outputs=measured, result_id=result_id)
        frozen = request_freeze(case.store, case.port, Collector(result),
                                attempt_id=ATTEMPT, disposition="completed")
        self.assertEqual(frozen["result_id"], result_id)
        return case, result, LinePublisher(PRIVATE_BASE)

    def test_real_frozen_assignment_reads_retention_publication_and_replay(self):
        case, result, publisher = self.prepared()
        key = driver.retain_proposal(case.store, publisher, attempt_id=ATTEMPT)
        held = load_manifest(case.store, key, "proposalManifest")
        self.assertEqual(held["result_manifest_digest"], result["manifest_digest"])
        self.assertEqual(held["assignment_ref"], result["assignment_ref"])
        self.assertEqual(key, driver.retain_proposal(case.store, publisher, attempt_id=ATTEMPT))
        answer = driver.publish_candidate(case.store, publisher, attempt_id=ATTEMPT,
                                          proposal_manifest_digest=key)
        self.assertEqual(answer["candidate_digest"], PRIVATE_HEAD)

    def test_changed_claim_cannot_replace_the_same_frozen_result(self):
        case, result, publisher = self.prepared()
        key = driver.retain_proposal(case.store, publisher, attempt_id=ATTEMPT)
        changed = copy.deepcopy(result)
        changed["outputs"][0]["result_metadata"][CLAIM]["head"] = "c3" * 20
        with self.assertRaises(ContractRefusal):
            record_frozen_result(case.store, attempt_id=ATTEMPT, sealed=sealed(changed))
        self.assertEqual(key, driver.retain_proposal(case.store, publisher, attempt_id=ATTEMPT))

    def test_a_valid_maximum_width_result_id_remains_proposable(self):
        # opaqueId permits 160 characters. The real receiver accepts this result
        # before the composer is called; failure therefore reaches the new seam.
        case, result, publisher = self.prepared(result_id="r" * 160)
        key = driver.retain_proposal(case.store, publisher, attempt_id=ATTEMPT)
        held = load_manifest(case.store, key, "proposalManifest")
        self.assertEqual(held["result_id"], result["result_id"])
        self.assertLessEqual(len(held["manifest_id"]), 160)


if __name__ == "__main__":
    unittest.main(verbosity=2)
