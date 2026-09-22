"""Bounded independent qualification counterexamples; synthetic state only."""
import json
import subprocess
import types
import unittest

from baton_v12.contracts import ContractRefusal, digest
from baton_v12.worker_manager import provider_context as context
from baton_v12.worker_manager import context_delivery as custody
from tests.manager.test_claude_context import CandidateQualificationFlow


class QualificationReview(unittest.TestCase):
    def test_historical_admission_shape_is_no_longer_readable(self):
        case = CandidateQualificationFlow()
        self.addCleanup(case.doCleanups)
        case.setUp()
        held = case.implemented()
        chain, admitted = context._use(held.control, held.attempt_id)
        historical = dict(admitted["payload"])
        historical.pop("qualification_run")
        old = types.ModuleType("baton_v12.worker_manager.review_old_context")
        old.__package__ = "baton_v12.worker_manager"
        source = subprocess.check_output([
            "git", "show", "HEAD:v12/python/src/baton_v12/worker_manager/provider_context.py"])
        exec(compile(source, "HEAD:provider_context.py", "exec"), old.__dict__)
        old._payload("admit", historical)
        with self.assertRaises(ContractRefusal) as caught:
            context._payload("admit", historical)
        print(json.dumps({"probe": "legacy-shape", "old": "accepted",
                          "current": str(caught.exception)}), flush=True)

    def test_certification_accepts_damaged_retained_generation(self):
        case = CandidateQualificationFlow()
        self.addCleanup(case.doCleanups)
        case.setUp()
        held, first, reviewer, second = case.corrected_ready()
        self.assertEqual(case.turn(held.control, "implementation", second,
                                  case.mounted(held.composed, "implementation", second),
                                  edits={"harness.py": "print('correction round')\n"}), 0)
        case.drive(held.job, held.composed, "implementation", "completed")
        context_id = context.context_use_of(held.control, second)["context_id"]
        context.retire_context(held.control, context_id)
        original = case.context_root / context_id / "generations/1/state/.claude/projects/output/session.json"
        original.chmod(0o600)
        original.write_text("{}")
        chain = context._history(held.control, context_id)
        first_final = next(one["payload"] for one in chain if one["action"] == "finalize")
        with self.assertRaises(ContractRefusal):
            custody.validate_generation(held.control, custody.configured_context_storage(held.control),
                                        context_id, first_final)
        production = dict(case.context_profile, qualification="production")
        # No independently accepted outcome is created at this digest. These
        # strings intentionally mirror the submitted certification test seam.
        evidence = {"run_id": case.RUN, "context_id": context_id,
                    "continuity": {"outcome": "accepted", "evidence_digest": digest("unbacked"),
                                   "statement": "unbacked continuity assertion"},
                    "evidence_refs": ["nonexistent-receipts", "nonexistent-outcome"]}
        context.certify_production_profile(held.control, production, evidence)
        self.assertEqual(context.context_profile_of(held.control, digest(production))["qualification"], "production")
        print(json.dumps({"probe": "certification", "generation_validation": "refused",
                          "certification": "accepted", "continuity": "no retained outcome"}), flush=True)


if __name__ == "__main__":
    unittest.main(defaultTest="QualificationReview", verbosity=2)
