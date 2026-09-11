"""Independent factory completion join; configured credential provider unchanged.

Only factory_serving's documented engine, checkout and clock boundaries are
controlled. All coding in this subclass uses the literal factory; integrating
therefore cannot fall back to the injected operations_from fixture.
"""
import unittest
from tests.tools.test_stage_execution import TwoBoundJobsTraverseServingAndCorrection as Base


class FactoryContinuation(Base):
    def coding(self, **members):
        return self.factory_coding(**members)


if __name__ == "__main__":
    suite = unittest.TestSuite([
        FactoryContinuation("test_the_constructed_port_is_the_same_one_through_completion"),
    ])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(0 if result.wasSuccessful() else 1)
