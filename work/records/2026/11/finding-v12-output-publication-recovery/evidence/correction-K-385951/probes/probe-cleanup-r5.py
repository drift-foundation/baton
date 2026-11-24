"""Revision-5 questions (review 2026-11-24T05-49-33Z R1, R2), asked of the EXACT functions in the scripts under
PACKET. Doubles only: no stack, engine, container or model. TMPDIR is disk scratch.

R1  A retained start or pause intent is reconciled only on POSITIVE evidence about its command: missing and
    unreadable records stay UNRESOLVED with the intent retained and no new effect made over them; a completion
    record, a recorded command that has positively ended, and an invocation that never forked are reconciled.
R2  A failed image removal makes the phase nonzero and keeps images.owned; success, positive absence and a tag
    that now names another image keep their outcomes.
"""
import json, os, subprocess, sys, tempfile, time, unittest
from pathlib import Path
packet = Path(os.environ["PACKET"])
text = {name: (packet / name).read_text() for name in ("qualify-w385695.sh", "option-a-setup.sh")}
STACK = {name: s[s.index("op_recorded() {"):s.index("\ntrap finish EXIT")] for name, s in text.items()}
q = text["qualify-w385695.sh"]
PAUSE = q[q.index("reconcile_pause() {"):q.index("\nfinish() {")]
CLEANUP = q[q.index("cleanup() {"):q.index('\ncase "$phase" in', q.index("cleanup() {"))]
tick = lambda pid: Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()[19]


def stack(name, files, stage="", after="reconcile_stack", live=""):
    """Run `after` over a retained state. `files` maps suffix -> content. stack_live answers `live`; stop is logged."""
    with tempfile.TemporaryDirectory(dir=os.environ["TMPDIR"]) as d:
        pre = Path(d) / "phase"
        for suffix, content in files.items():
            Path(str(pre) + suffix).write_text(content)
        body = (f'set -uo pipefail\nEVIDENCE={d!r}; PREFIX={str(pre)!r}; DEST="$EVIDENCE"; UNRESOLVED=""; MANAGER_STARTED=""; RUN=run; STACK_START_STAGE={stage!r}\n'
                'say() { echo "$*"; }; fail() { say "FAIL: $*"; exit 1; }\n'
                f'stack_live() {{ [ -e "$EVIDENCE/stopped" ] || printf %s {live!r}; }}\n'
                'timeout() { case "$*" in *" stop") touch "$EVIDENCE/stopped";; *" start") touch "$EVIDENCE/started";; esac; }\n'
                + STACK[name] + f'\n{after}\necho "unresolved=[$UNRESOLVED]"\n')
        done = subprocess.run(["bash", "-c", body], capture_output=True, text=True, timeout=60)
        got = {"script": name, "exit": done.returncode, "said": done.stdout.strip().splitlines(), "intent_retained": Path(str(pre) + ".stack-start-intent").exists(),
               "reconciled": Path(str(pre) + ".stack-start-reconciled").exists(), "started": (Path(d) / "started").exists(), "stopped": (Path(d) / "stopped").exists()}
        print("STACK", json.dumps({"state": sorted(files), "stage": stage, **got}))
        return got


class ARetainedStartNeedsPositiveEvidenceOfItsCommand(unittest.TestCase):
    def both(self, check):
        for name in text:
            with self.subTest(script=name):
                check(name)

    def unresolved(self, got):
        self.assertTrue(got["intent_retained"]); self.assertFalse(got["reconciled"]); self.assertFalse(got["stopped"])
        self.assertIn("unresolved=[1]", got["said"]); self.assertTrue(any(s.startswith("UNRESOLVED") for s in got["said"]))

    def test_no_record_of_the_command_stays_unresolved(self):
        self.both(lambda n: self.unresolved(stack(n, {".stack-start-intent": "t\n"})))

    def test_an_empty_or_unreadable_record_stays_unresolved(self):
        for content in ("", "garbage\n", "123\n", "123 x\n", "12 34 56\n"):
            self.both(lambda n: self.unresolved(stack(n, {".stack-start-intent": "t\n", ".stack-start-op": content})))

    def test_no_new_start_is_made_over_a_retained_intent(self):
        def check(n):
            got = stack(n, {".stack-start-intent": "t\n"}, after='start_stack "$EVIDENCE/log"')
            self.assertEqual(got["exit"], 1); self.assertFalse(got["started"]); self.assertTrue(got["intent_retained"])
        self.both(check)

    def test_a_completion_record_is_reconciled(self):
        def check(n):
            got = stack(n, {".stack-start-intent": "t\n", ".stack-start-op-done": "0\n"})
            self.assertTrue(got["reconciled"]); self.assertFalse(got["intent_retained"]); self.assertIn("unresolved=[]", got["said"])
        self.both(check)

    def test_a_recorded_command_that_has_positively_ended_is_reconciled_and_its_stack_stopped(self):
        def check(n):
            child = subprocess.Popen(["true"]); child.wait()
            got = stack(n, {".stack-start-intent": "t\n", ".stack-start-op": f"{child.pid} 1\n"}, live="manager 7\n")
            self.assertTrue(got["reconciled"]); self.assertTrue(got["stopped"]); self.assertIn("unresolved=[]", got["said"])
        self.both(check)

    def test_a_recorded_command_still_running_is_waited_for_before_anything_is_reconciled(self):
        def check(n):
            child = subprocess.Popen(["sleep", "2"]); began = time.monotonic()
            try:
                got = stack(n, {".stack-start-intent": "t\n", ".stack-start-op": f"{child.pid} {tick(child.pid)}\n"})
            finally:
                child.wait()
            self.assertGreaterEqual(time.monotonic() - began, 1.5); self.assertTrue(got["reconciled"])
        self.both(check)

    def test_an_invocation_that_wrote_the_intent_and_never_forked_is_reconciled(self):
        def check(n):
            got = stack(n, {".stack-start-intent": "t\n"}, stage="intent-only")
            self.assertTrue(got["reconciled"]); self.assertIn("unresolved=[]", got["said"])
        self.both(check)

    def test_an_invocation_that_forked_and_finds_no_record_stays_unresolved(self):
        self.both(lambda n: self.unresolved(stack(n, {".stack-start-intent": "t\n"}, stage="launched")))


def pause(files, inspect="true false"):
    with tempfile.TemporaryDirectory(dir=os.environ["TMPDIR"]) as d:
        pre = Path(d) / "deadline"
        for suffix, content in files.items():
            Path(str(pre) + suffix).write_text(content)
        (Path(d) / "answers").write_text("\n".join(inspect.split()) + "\n")
        body = (f'set -uo pipefail\nEVIDENCE={d!r}; PREFIX={str(pre)!r}; PAUSED=""; UNRESOLVED=""; ENGINE_SECONDS=5\nsay() {{ echo "$*"; }}\n'
                'eng() { echo "$*" >> "$EVIDENCE/calls"; case "$1" in inspect) n=$(( $(cat "$EVIDENCE/n" 2>/dev/null || echo 0) + 1 )); echo $n > "$EVIDENCE/n"; sed -n "${n}p" "$EVIDENCE/answers";; esac; }\n'
                + STACK["qualify-w385695.sh"] + "\n" + PAUSE + '\nreconcile_pause\necho "unresolved=[$UNRESOLVED]"\n')
        done = subprocess.run(["bash", "-c", body], capture_output=True, text=True, timeout=60)
        calls = (Path(d) / "calls").read_text().splitlines() if (Path(d) / "calls").exists() else []
        got = {"said": done.stdout.strip().splitlines(), "unpauses": sum(c.startswith("unpause") for c in calls),
               "intent_retained": Path(str(pre) + ".pause-intent").exists(), "filed": Path(str(pre) + ".pause-reconciled").exists()}
        print("PAUSE", json.dumps({"state": sorted(files), **got}))
        return got


class ARetainedPauseNeedsPositiveEvidenceOfItsRequest(unittest.TestCase):
    def test_no_or_unreadable_record_of_the_request_stays_unresolved_and_what_is_paused_is_still_released(self):
        for extra in ({}, {".pause-op": "garbage\n"}, {".pause-op": ""}):
            got = pause({".pause-intent": "c\n", **extra})
            self.assertEqual(got["unpauses"], 1); self.assertTrue(got["intent_retained"]); self.assertFalse(got["filed"]); self.assertIn("unresolved=[1]", got["said"])

    def test_a_completed_request_is_reconciled_and_filed(self):
        got = pause({".pause-intent": "c\n", ".paused": "c\n", ".pause-op": "1 1\n", ".pause-op-done": ""})
        self.assertEqual(got["unpauses"], 1); self.assertTrue(got["filed"]); self.assertFalse(got["intent_retained"]); self.assertIn("unresolved=[]", got["said"])

    def test_a_recorded_request_that_has_positively_ended_is_reconciled(self):
        child = subprocess.Popen(["true"]); child.wait()
        got = pause({".pause-intent": "c\n", ".pause-op": f"{child.pid} 1\n"}, inspect="false")
        self.assertEqual(got["unpauses"], 0); self.assertTrue(got["filed"]); self.assertIn("unresolved=[]", got["said"])

    def test_the_deadline_phase_refuses_to_freeze_over_a_retained_pause_intent(self):
        body = q[q.index("deadline() {"):q.index("\ncleanup() {")]
        with tempfile.TemporaryDirectory(dir=os.environ["TMPDIR"]) as d:
            (Path(d) / "deadline.pause-intent").write_text("c\n")
            run = (f'set -euo pipefail\nPREFIX={d + "/deadline"!r}; JOB2=j STAGE2=s EPISODE2=1 DECISION2=d\nsay() {{ echo "$*"; }}; fail() {{ say "FAIL: $*"; exit 1; }}; stores() {{ :; }}\n'
                   'preflight_checks() { echo REACHED; }\n' + body + "\ndeadline\n")
            done = subprocess.run(["bash", "-c", run], capture_output=True, text=True, timeout=20)
            print("DEADLINE_OVER_INTENT", json.dumps({"exit": done.returncode, "said": done.stdout.strip()}))
            self.assertEqual(done.returncode, 1); self.assertNotIn("REACHED", done.stdout); self.assertIn("not reconciled", done.stdout)


def images(inspect, remove="ok", listing="empty"):
    with tempfile.TemporaryDirectory(dir=os.environ["TMPDIR"]) as d:
        owned = "fixture owned-tag sha256:owned\n"; (Path(d) / "images.owned").write_text(owned)
        answer = {"owned": "echo sha256:owned", "other": "echo sha256:other", "none": "return 1", "down": "return 125"}[inspect]
        body = (f'EVIDENCE={d!r}; PREFIX="$EVIDENCE/cleanup"; UNRESOLVED=""\nsay() {{ echo "$*"; }}; run_id() {{ echo run; }}\n'
                f'eng() {{ echo "$*" >> "$EVIDENCE/calls"; case "$2" in inspect) {answer};; ls) {"return 0" if listing == "empty" else "return 125"};; rm) {"return 0" if remove == "ok" else "return 1"};; esac; }}\n'
                + CLEANUP + '\ncleanup\nif [ -n "$UNRESOLVED" ]; then exit 1; fi\n')
        done = subprocess.run(["bash", "-c", body], capture_output=True, text=True, timeout=20)
        calls = (Path(d) / "calls").read_text().splitlines()
        got = {"exit": done.returncode, "said": done.stdout.strip().splitlines(), "removes_asked": [c for c in calls if c.startswith("image rm")],
               "owned_record_kept": (Path(d) / "images.owned").read_text() == owned}
        print("IMAGE", json.dumps({"inspect": inspect, "remove": remove, "listing": listing, **got}))
        return got


class ImageCleanupIsTruthful(unittest.TestCase):
    def test_a_failed_removal_is_nonzero_keeps_the_record_and_is_not_forced(self):
        got = images("owned", remove="fails")
        self.assertEqual(got["exit"], 1); self.assertTrue(got["owned_record_kept"]); self.assertEqual(got["removes_asked"], ["image rm owned-tag"])
        self.assertTrue(any("UNRESOLVED" in s and "sha256:owned" in s for s in got["said"]))

    def test_a_successful_removal_is_zero(self):
        got = images("owned"); self.assertEqual(got["exit"], 0); self.assertTrue(any("removed owned-tag" in s for s in got["said"]))

    def test_positively_absent_is_zero_and_nothing_is_removed(self):
        got = images("none"); self.assertEqual(got["exit"], 0); self.assertEqual(got["removes_asked"], [])

    def test_a_tag_that_now_names_another_image_is_left_alone(self):
        got = images("other"); self.assertEqual(got["exit"], 0); self.assertEqual(got["removes_asked"], []); self.assertTrue(any("left alone" in s for s in got["said"]))

    def test_an_engine_that_does_not_answer_is_nonzero_and_nothing_is_removed(self):
        got = images("down", listing="down"); self.assertEqual(got["exit"], 1); self.assertEqual(got["removes_asked"], []); self.assertTrue(got["owned_record_kept"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
