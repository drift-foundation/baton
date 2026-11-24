"""The reviewer's `evidence/review-385934/probe-qualification.py`, ADAPTED to the corrected script.

Theirs asserts the literal wrong path is present in the reviewed packet, so it can only ever describe that
packet. These are the same two questions asked of the corrected script, plus the lost-reply cut:
  * every installed path the script derives equals the reviewed tree's `tools.instance.layout`;
  * the EXACT `finish` and `reconcile_pause` functions, entered at the cut after the watcher acknowledged a
    pause and before the parent copied it into its variable, unpause the selected container;
  * the same with only the INTENT recorded (the pause reply was lost);
  * and a container that is not paused, or is gone, is not unpaused.
Only a fake `eng`; no engine.
"""
import json, os, re, subprocess, sys, tempfile, unittest
from pathlib import Path
root = Path.cwd(); sys.path[:0] = [str(root), str(root / "src")]
from tools import instance
script = Path(os.environ["QUALIFY_SCRIPT"]).read_text()


class Preparation(unittest.TestCase):
    def test_every_installed_path_is_the_supported_layout(self):
        want = instance.layout("/fixture/instance")
        derived = dict(re.findall(r'\("([A-Z_]+)", d \+ "([^"]+)"\)', script))
        print("LAYOUT", json.dumps(derived))
        self.assertEqual({"CMD": "/fixture/instance" + derived["CMD"], "AUTHORITY": "/fixture/instance" + derived["AUTHORITY"],
                          "STACK_STATE": "/fixture/instance" + derived["STACK_STATE"]},
                         {"CMD": want["command"], "AUTHORITY": want["authority_store"], "STACK_STATE": want["state"]})
        self.assertNotIn("/stores/", script)

    def cut(self, files, paused):
        body = script.split("reconcile_pause() {", 1)[1].split("\ntrap finish EXIT", 1)[0]
        with tempfile.TemporaryDirectory(dir=os.environ["TMPDIR"]) as d:
            pre = Path(d) / "deadline"
            for name in files:
                Path(str(pre) + name).write_text("selected-container\n")
            setup = ("set -euo pipefail\nEVIDENCE=%r\nPREFIX=%r\nPAUSED=\"\"; ENDING=\"\"; MANAGER_STARTED=\"\"; phase=deadline; OWNED_PIDS=()\n" % (d, str(pre)))
            fake = ('say() { echo "$*"; }; ended() { return 0; }\n'
                    'eng() { echo "$*" >> "$EVIDENCE/engine-calls"; if [ "$1" = inspect ]; then %s; fi; }\n' % paused)
            text = setup + fake + "reconcile_pause() {" + body + "\ntrap finish EXIT\nexit 143\n"
            done = subprocess.run(["bash", "-c", text], capture_output=True, text=True, timeout=20)
            calls = (Path(d) / "engine-calls").read_text() if (Path(d) / "engine-calls").exists() else ""
            print("PAUSE_CUT", json.dumps({"files": files, "exit": done.returncode, "engine_calls": calls.splitlines()}))
            return done, calls

    def test_cleanup_recovers_a_pause_acknowledged_before_the_parent_assigned_it(self):
        done, calls = self.cut([".pause-intent", ".paused"], "echo true")
        self.assertEqual(done.returncode, 143)
        self.assertEqual(calls.count("unpause selected-container"), 1)

    def test_cleanup_recovers_a_pause_whose_reply_was_lost(self):
        done, calls = self.cut([".pause-intent"], "echo true")
        self.assertEqual(calls.count("unpause selected-container"), 1)

    def test_cleanup_leaves_a_container_that_is_not_paused_or_is_gone(self):
        for paused in ("echo false", "return 1"):
            done, calls = self.cut([".pause-intent", ".paused"], paused)
            self.assertNotIn("unpause", calls)
            self.assertEqual(done.returncode, 143)


if __name__ == "__main__":
    unittest.main(verbosity=2)
