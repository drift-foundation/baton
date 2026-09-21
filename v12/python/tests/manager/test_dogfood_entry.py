"""W202663 (owner 227095) — the dogfood entry supervises now, provably.

Job2's producer killed a background test run inside its container; the
orphans reparented to PID 1 — `dogfood_entry`, which never called `wait` —
and ~498 zombies in the composed 512-PID cgroup made every later `fork`
fail, which broke the authoritative verification capture. The correction is
image-side and two-part: PID 1 becomes a minimal supervisor that reaps, and
the attempt's log room becomes an explicit delivery
(`claude_agent.ROOM_VARIABLE`) only the launched worker holds.

WHY EVERY SUPERVISION CASE RUNS IN A HELPER PROCESS. In the container the
supervisor IS PID 1, so orphans reach it by the kernel's own rule. Outside
one they reach the nearest subreaper instead, so each helper marks itself
`PR_SET_CHILD_SUBREAPER` first — the case reproduces the container's
reparenting topology rather than assuming it. No image is built, no
container runs, no provider exists here.
"""

import os
import pathlib
import shutil
import signal
import subprocess
import sys
import tempfile
import textwrap
import unittest
from unittest import mock

WORKER = (pathlib.Path(__file__).resolve().parents[3] / "worker")
sys.path.insert(0, str(WORKER))
sys.path.insert(0, str(WORKER.parent / "python" / "src" / "baton_v12"))
shutil.rmtree(WORKER / "__pycache__", ignore_errors=True)

import claude_agent                                          # noqa: E402

# The helper preamble every supervision case shares: become a subreaper so
# orphans reparent HERE (as they reparent to PID 1 in the container), then
# import the entry exactly as the image's interpreter would.
_PREAMBLE = textwrap.dedent(f"""\
    import ctypes, os, signal, sys, time
    sys.path.insert(0, {str(WORKER)!r})
    sys.path.insert(0, {str(WORKER.parent / 'python' / 'src' / 'baton_v12')!r})
    PR_SET_CHILD_SUBREAPER = 36
    if ctypes.CDLL(None, use_errno=True).prctl(
            PR_SET_CHILD_SUBREAPER, 1, 0, 0, 0) != 0:
        print("NO-SUBREAPER", flush=True)
        sys.exit(125)
    import dogfood_entry
""")


def _helper(body, *, timeout=30):
    return subprocess.run(
        [sys.executable, "-c", _PREAMBLE + textwrap.dedent(body)],
        capture_output=True, text=True, timeout=timeout)


class TheSupervisorReapsWhatTheWorkerLeaves(unittest.TestCase):
    """The Job2 mechanism, reproduced and closed in one case.

    A child of the worker dies leaving a live grandchild; the grandchild
    reparents to the supervisor while the worker still runs, then ends. A
    PID 1 that does not reap holds that zombie forever — Job2 held ~498 of
    them. The assertion is the strongest one the kernel offers: after
    `supervised` returns, this supervisor has NO child left at all, and the
    worker's own ending came through untouched.
    """

    def test_an_orphan_is_reaped_and_the_status_is_carried(self):
        done = _helper("""
            def run():
                a = os.fork()
                if a == 0:
                    b = os.fork()
                    if b == 0:
                        time.sleep(0.2)   # outlive our parent, then end
                        os._exit(0)
                    os._exit(0)           # orphan b onto the supervisor
                os.waitpid(a, 0)          # the worker's own accounting is clean
                time.sleep(1.0)           # the orphan ends inside this window
                return 7

            status = dogfood_entry.supervised(run=run)
            try:
                left = os.waitpid(-1, os.WNOHANG)
            except ChildProcessError:
                print("REAPED", status, flush=True)
                sys.exit(0 if status == 7 else 2)
            print("REMAINED", left, flush=True)
            sys.exit(1)
        """)
        if done.returncode == 125:
            self.skipTest("this kernel refused PR_SET_CHILD_SUBREAPER")
        self.assertEqual(done.returncode, 0, (done.stdout, done.stderr))
        self.assertIn("REAPED 7", done.stdout)


class TheSupervisorForwardsTheStop(unittest.TestCase):
    """The manager's stop contract is unchanged: signal PID 1.

    The supervisor forwards SIGTERM to the worker, whose default disposition
    ends it, and the supervisor answers with the shell convention the engine
    already reads — 128+15 — rather than a success or a bare 1.
    """

    def test_sigterm_reaches_the_worker_and_the_ending_says_so(self):
        script = _PREAMBLE + textwrap.dedent("""
            def run():
                print("READY", flush=True)
                time.sleep(30)
                return 0

            sys.exit(dogfood_entry.supervised(run=run))
        """)
        held = subprocess.Popen([sys.executable, "-c", script],
                                stdout=subprocess.PIPE, text=True)
        try:
            line = held.stdout.readline().strip()
            if line == "NO-SUBREAPER":
                held.wait(timeout=30)
                self.skipTest("this kernel refused PR_SET_CHILD_SUBREAPER")
            self.assertEqual(line, "READY")
            held.send_signal(signal.SIGTERM)
            self.assertEqual(held.wait(timeout=30), 128 + signal.SIGTERM)
        finally:
            held.stdout.close()
            if held.poll() is None:
                held.kill()
                held.wait(timeout=30)


class TheRoomIsAnExplicitDelivery(unittest.TestCase):
    """`_log_room` opens only what `ROOM_VARIABLE` names — nothing ambient.

    Job2's contamination path was nested adapter code holding the fixed
    `/run/baton/logs` merely by importing this module. A process whose
    environment does not name a room gets `(None, None)` even when a real
    room exists; the worker gets exactly the room its entry named.
    """

    def test_no_marker_means_no_room_even_when_a_room_exists(self):
        import attempt_log_format
        with tempfile.TemporaryDirectory() as place:
            with mock.patch.dict(os.environ, clear=False):
                os.environ.pop(claude_agent.ROOM_VARIABLE, None)
                with mock.patch.object(attempt_log_format, "TARGET", place):
                    room, fmt = claude_agent._log_room()
        self.assertEqual((room, fmt), (None, None))

    def test_the_marker_names_the_room_the_adapter_opens(self):
        with tempfile.TemporaryDirectory() as place:
            with mock.patch.dict(
                    os.environ, {claude_agent.ROOM_VARIABLE: place}):
                room, fmt = claude_agent._log_room()
        self.assertIsNotNone(fmt)
        self.assertIsNotNone(room)
        os.close(room)

    def test_the_entry_and_the_adapter_agree_on_the_name_and_the_target(self):
        import dogfood_entry
        self.assertEqual(dogfood_entry.ROOM_VARIABLE,
                         claude_agent.ROOM_VARIABLE)
        import attempt_log_format
        self.assertEqual(dogfood_entry.ROOM_TARGET, attempt_log_format.TARGET)

    def test_a_composed_child_environment_never_carries_the_marker(self):
        """The composition, asked directly: HOME, PATH and the three
        ephemera, and nothing that names a room — even while this process's
        own environment names one, which is exactly the worker's situation."""
        agent = claude_agent.ClaudeAgent(run=lambda *a, **k: None)
        with tempfile.TemporaryDirectory() as scratch:
            os.chmod(scratch, 0o700)
            home = agent._new_directory(scratch, "home")
            _root, roots = agent._new_ephemera(scratch, "ephemera")
            with mock.patch.dict(
                    os.environ,
                    {claude_agent.ROOM_VARIABLE: "/run/baton/logs"}):
                composed = agent._closed_environment(
                    home=home, roots=roots, scratch=scratch)
        self.assertNotIn(claude_agent.ROOM_VARIABLE, composed)
        self.assertEqual(
            set(composed),
            {"HOME", "PATH", "PYTHONPYCACHEPREFIX", "TMPDIR",
             "XDG_CACHE_HOME"})


if __name__ == "__main__":
    unittest.main()
