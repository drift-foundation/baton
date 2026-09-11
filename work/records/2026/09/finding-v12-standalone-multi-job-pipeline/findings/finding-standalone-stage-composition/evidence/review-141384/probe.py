"""Independent production-factory B consumer join at controlled external boundaries."""
import unittest
from tests.tools.test_stage_execution import TwoBoundJobsTraverseServingAndCorrection as Base

class FactoryJudgments(Base):
    def coding(self, **members):
        return self.factory_coding(**members)

    def judgment_execution(self, *args, **kwargs):
        one = super().judgment_execution(*args, **kwargs)
        one["deployment"]["credential_sources"] = self.credential_registry()
        return one

if __name__ == "__main__":
    suite = unittest.TestSuite([
        FactoryJudgments("test_real_B_consumer_judges_frozen_reports_and_completes_both_jobs"),
        FactoryJudgments("test_rejected_derived_judgment_cannot_authorize_import"),
    ])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(0 if result.wasSuccessful() else 1)
