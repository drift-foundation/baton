"""Finite questions of the revision-4 cleanup, asked of the EXACT functions in the scripts beside this probe's
parent directory. Only the engine is a double (a shell function); no engine, container, stack or model.

  PACKET=<directory holding qualify-w385695.sh, option-a-setup.sh, cli-in-image-driver.py>  TMPDIR=<disk scratch>

Pause (C5.2): for every combination of what the engine answers to the first inspection, to the unpause and to
the read-back, the script's words and whether it released, left alone, or retained as UNRESOLVED.
Outcome: a phase whose own steps succeeded and whose cleanup is unresolved does not exit 0.
Driver (C5.3): of two same-named processes, only the one carrying the run's token is selected and ended.
"""
import importlib.util, json, os, subprocess, sys, tempfile, unittest
from pathlib import Path

packet = Path(os.environ["PACKET"])
script = (packet / "qualify-w385695.sh").read_text()
PAUSE = script[script.index("reconcile_pause() {"):script.index("\nfinish() {")]
FINISH = script[script.index("finish() {"):script.index("\ntrap finish EXIT")]

# The engine double: what `inspect`, `ps` and `unpause` answer is scripted per call from files, and every call is logged.
ENGINE = r'''
say() { echo "$*"; }
ended() { return 0; }
eng() {
  echo "$*" >> "$EVIDENCE/engine-calls"
  local verb="$1" n answer
  n=$(( $(cat "$EVIDENCE/count-$verb" 2>/dev/null || echo 0) + 1 )); echo "$n" > "$EVIDENCE/count-$verb"
  answer="$(sed -n "${n}p" "$EVIDENCE/script-$verb" 2>/dev/null)"; [ -n "$answer" ] || answer="$(tail -1 "$EVIDENCE/script-$verb")"
  case "$answer" in
    down) echo "Cannot connect to the daemon" >&2; return 125;;
    none) echo "No such container" >&2; return 1;;
    empty) return 0;;
    fail) return 1;;
    ok) return 0;;
    *) echo "$answer"; return 0;;
  esac
}
'''


def cleanup(inspect, ps="empty", unpause="ok", files=(".pause-intent", ".paused"), code=143, through_finish=False):
    with tempfile.TemporaryDirectory(dir=os.environ["TMPDIR"]) as d:
        root = Path(d)
        for name in files:
            (root / ("deadline" + name)).write_text("selected-container\n")
        for verb, answers in (("inspect", inspect), ("ps", ps), ("unpause", unpause)):
            (root / ("script-" + verb)).write_text("\n".join(answers.split()) + "\n")
        head = ("set -euo pipefail\nEVIDENCE=%r; PREFIX=\"$EVIDENCE/deadline\"; DEST=\"$EVIDENCE\"; phase=deadline\n"
                "PAUSED=\"\"; ENDING=\"\"; MANAGER_STARTED=\"\"; UNRESOLVED=\"\"; OWNED_PIDS=(); ENGINE_SECONDS=5\n" % d)
        if through_finish:
            body = head + ENGINE + PAUSE + "\n" + FINISH + "\ntrap finish EXIT\nexit %d\n" % code
        else:
            body = head + ENGINE + PAUSE + "\nset +e\nreconcile_pause\necho \"UNRESOLVED=[$UNRESOLVED]\"\n"
        done = subprocess.run(["bash", "-c", body], capture_output=True, text=True, timeout=60)
        calls = (root / "engine-calls").read_text().splitlines() if (root / "engine-calls").exists() else []
        answer = {"exit": done.returncode, "said": done.stdout.strip().splitlines(), "unpauses": sum(c.startswith("unpause ") for c in calls),
                  "intent_retained": (root / "deadline.pause-intent").exists()}
        print("PAUSE", json.dumps({"inspect": inspect, "ps": ps, "unpause": unpause, **answer}))
        return answer


class PauseStateIsPositiveOrUnresolved(unittest.TestCase):
    def test_paused_and_released_is_read_back(self):
        got = cleanup("true false")
        self.assertEqual(got["unpauses"], 1); self.assertIn("UNRESOLVED=[]", got["said"]); self.assertTrue(any("read back: not paused" in s for s in got["said"]))

    def test_an_unpause_whose_reply_was_lost_is_released_by_the_read_back(self):
        got = cleanup("true false", unpause="fail")
        self.assertEqual(got["unpauses"], 1); self.assertIn("UNRESOLVED=[]", got["said"])

    def test_an_unpause_that_failed_and_left_it_paused_is_unresolved(self):
        got = cleanup("true true", unpause="fail")
        self.assertIn("UNRESOLVED=[1]", got["said"]); self.assertTrue(any("still paused" in s for s in got["said"])); self.assertTrue(got["intent_retained"])

    def test_an_unpause_whose_read_back_fails_is_unresolved_even_when_it_was_acknowledged_or_not(self):
        for unpause in ("ok", "fail"):
            got = cleanup("true down", ps="down", unpause=unpause)
            self.assertIn("UNRESOLVED=[1]", got["said"]); self.assertTrue(any("could not be read back" in s for s in got["said"]))

    def test_positively_not_paused_is_left_alone(self):
        got = cleanup("false")
        self.assertEqual(got["unpauses"], 0); self.assertIn("UNRESOLVED=[]", got["said"]); self.assertTrue(any("positively not paused" in s for s in got["said"]))

    def test_positively_absent_is_the_engine_listing_nothing_for_that_id(self):
        got = cleanup("none", ps="empty")
        self.assertEqual(got["unpauses"], 0); self.assertIn("UNRESOLVED=[]", got["said"]); self.assertTrue(any("positively no longer exists" in s for s in got["said"]))

    def test_an_inspection_that_failed_is_not_absence(self):
        for inspect, ps in (("down", "down"), ("none", "down"), ("none", "selected-container"), ("garbage", "empty")):
            got = cleanup(inspect, ps=ps)
            self.assertEqual(got["unpauses"], 0, (inspect, ps)); self.assertIn("UNRESOLVED=[1]", got["said"], (inspect, ps))
            self.assertTrue(any("NOT unpaused blind" in s for s in got["said"])); self.assertTrue(got["intent_retained"])

    def test_an_engine_that_answers_on_a_later_try_is_believed(self):
        got = cleanup("down true false", ps="down")
        self.assertEqual(got["unpauses"], 1); self.assertIn("UNRESOLVED=[]", got["said"])

    def test_a_phase_that_succeeded_with_unresolved_cleanup_does_not_exit_zero(self):
        self.assertEqual(cleanup("down", ps="down", code=0, through_finish=True)["exit"], 1)
        self.assertEqual(cleanup("down", ps="down", code=143, through_finish=True)["exit"], 143)
        self.assertEqual(cleanup("false", code=0, through_finish=True)["exit"], 0)


class TheDriverEndsOnlyWhatItsOwnTurnStarted(unittest.TestCase):
    def test_of_two_same_named_processes_only_the_token_bearer_is_selected_and_ended(self):
        spec = importlib.util.spec_from_file_location("driver_r4", packet / "cli-in-image-driver.py")
        driver = importlib.util.module_from_spec(spec); spec.loader.exec_module(driver)
        token = "probe-" + os.urandom(8).hex()
        # BOTH are `sleep 303`, the name the reviewed driver used to select by. One is another task's.
        foreign = subprocess.Popen(["sleep", "303"])
        mine = subprocess.Popen(["sleep", "303"], env=dict(os.environ, **{driver.TOKEN_NAME: token}))
        try:
            self.assertEqual(driver.survivors(), [], "a driver that started no turn owns nothing")
            self.assertEqual(driver.survivors(token), [mine.pid])
            self.assertEqual(driver.survivors("another-" + token), [])
            self.assertEqual(driver.end_owned(token), [])
            self.assertEqual(mine.wait(timeout=5), -9)
            self.assertIsNone(foreign.poll(), "the same-named process of another task was ended")
            print("DRIVER", json.dumps({"token_bearer_ended": True, "same_named_foreign_alive": foreign.poll() is None}))
        finally:
            for one in (foreign, mine):
                if one.poll() is None:
                    one.terminate()
                one.wait(timeout=5)


if __name__ == "__main__":
    unittest.main(verbosity=2)
