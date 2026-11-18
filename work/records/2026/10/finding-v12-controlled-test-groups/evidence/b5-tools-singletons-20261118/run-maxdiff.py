import sys, unittest
unittest.TestCase.maxDiff = None
sys.argv = ["unittest", "-v"] + sys.argv[1:]
unittest.main(module=None)
