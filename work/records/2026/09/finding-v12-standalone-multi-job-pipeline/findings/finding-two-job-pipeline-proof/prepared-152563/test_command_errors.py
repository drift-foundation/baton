"""Synthetic manager/engine command output; no provider or credential streams."""
import subprocess
import unittest
from unittest import mock

import run as runner


class CommandErrorTests(unittest.TestCase):
    def error_for(self, stderr, code=1):
        completed = subprocess.CompletedProcess(['synthetic-status'], code, '', stderr)
        with mock.patch.object(runner.subprocess, 'run', return_value=completed) as called:
            with self.assertRaises(RuntimeError) as raised:
                runner.command(['synthetic-status'])
        called.assert_called_once_with(['synthetic-status'], cwd=runner.CWD,
                                       capture_output=True, text=True, timeout=10)
        return str(raised.exception)

    def test_long_traceback_keeps_terminal_exception_and_marks_omission(self):
        terminal = 'ContractRefusal: this deployment names 2 implementation workers\n'
        stderr = 'Traceback (most recent call last):\n' + '  synthetic frame\n' * 300 + terminal
        error = self.error_for(stderr)
        self.assertTrue(error.endswith(stderr[-2000:]))
        self.assertIn('stderr truncated to final 2000 of ' + str(len(stderr)), error)
        self.assertIn(terminal, error)
        self.assertNotIn('Traceback (most recent call last):', error)
        self.assertLess(len(error), 2200)

    def test_short_error_is_kept_in_full_with_nonzero_status(self):
        error = self.error_for('ContractRefusal: unbound Job\n', code=7)
        self.assertIn('command failed (exit 7)', error)
        self.assertTrue(error.endswith('ContractRefusal: unbound Job\n'))
        self.assertNotIn('truncated', error)

    def test_empty_stderr_still_reports_command_and_status(self):
        error = self.error_for('', code=2)
        self.assertIn('exit 2', error)
        self.assertIn('synthetic-status', error)

    def test_success_preserves_stdout_and_does_not_expose_stderr(self):
        with mock.patch.object(runner.subprocess, 'run', return_value=
                subprocess.CompletedProcess(['synthetic-status'], 0, '{"ok":true}', 'ignored')):
            self.assertEqual(runner.command(['synthetic-status']), '{"ok":true}')

    def test_deadline_exception_stays_primary(self):
        expired = subprocess.TimeoutExpired(['synthetic-status'], 3)
        with mock.patch.object(runner.subprocess, 'run', side_effect=expired):
            with self.assertRaises(subprocess.TimeoutExpired) as raised:
                runner.command(['synthetic-status'], seconds=3)
        self.assertIs(raised.exception, expired)


if __name__ == '__main__':
    unittest.main(verbosity=2)
