"""Independent check of the witness's exit-status-blind ancestry assertion."""
import json
from pathlib import Path
import subprocess
import unittest
from tests.tools.test_stage_execution import TwoBoundJobsTraverseServingAndCorrection


class IndependentAncestry(TwoBoundJobsTraverseServingAndCorrection):
    def vcs(self, *arguments):
        if arguments[:2] == ('merge-base', '--is-ancestor'):
            argv = ['git', '-C', self.source, *arguments]
            answer = subprocess.run(argv, capture_output=True, text=True, timeout=1)
            Path(__file__).with_suffix('.json').write_text(json.dumps({'argv': argv, 'exit_code': answer.returncode, 'stdout': answer.stdout, 'stderr': answer.stderr}, indent=2) + '\n')
            self.assertEqual(answer.returncode, 0, answer.stderr)
            return answer.stdout
        return super().vcs(*arguments)


if __name__ == '__main__':
    suite = unittest.TestSuite([IndependentAncestry('test_BOTH_JOBS_REACH_TERMINAL_ON_ONE_TARGET')])
    answer = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(not answer.wasSuccessful())
