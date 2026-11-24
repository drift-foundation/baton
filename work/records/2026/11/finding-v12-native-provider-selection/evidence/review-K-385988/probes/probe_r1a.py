"""K probes of the R1a delta (candidate 5b76e700): provider_home.acquire on a record left `preparing` by another holder.
Pure home owner; no harness, engine or provider. cwd=<tree>/v12/python, PYTHONPATH=src, PROBE_TMP names a disk directory."""
import json, os, tempfile, unittest
from pathlib import Path
from unittest import mock
from baton_v12.worker_manager import provider_home as homes

ID = dict(authority_uuid="0" * 32, job_id="job-k", worker_id="worker-k")
GONE = lambda holder: {"attempt_id": holder, "runtime": "not-started", "ended_before_start": True}


class Preparing(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(dir=os.environ["PROBE_TMP"])
        self.place = homes.location(homes.check_placement(self.root, ()), homes.identity(**ID))

    def interrupted(self, point):
        """Leave a1's record `preparing`: fail the final mkdir ('mkdir') or the write that would record `ready` ('ready')."""
        real_mkdir, real_write = os.mkdir, homes._write
        def mkdir(path, *a, **k):
            if point == "mkdir" and path == "home" and k.get("dir_fd") is not None and os.readlink("/proc/self/fd/%d" % k["dir_fd"]) == str(self.place):
                raise OSError(28, "probe")
            return real_mkdir(path, *a, **k)
        def write(fd, record):
            if point == "ready" and record.get("state") == "ready":
                raise OSError(5, "probe")
            return real_write(fd, record)
        with mock.patch.object(os, "mkdir", side_effect=mkdir), mock.patch.object(homes, "_write", side_effect=write):
            with self.assertRaises(OSError):
                homes.acquire(self.root, **ID, attempt_id="a1")
        record = (self.place / "record.json").read_bytes()
        self.assertEqual(json.loads(record)["state"], "preparing")
        self.assertEqual(json.loads(record)["holder"], "a1")
        return record

    def test_E1_every_unproved_form_of_evidence_stays_pending_and_writes_nothing(self):
        for point in ("mkdir", "ready"):
            self.setUp()
            before = self.interrupted(point)
            listing = sorted(os.listdir(self.place))
            cases = {"no callback": None, "callback answers None": lambda h: None, "empty": lambda h: {},
                "not-started without the ending": lambda h: {"attempt_id": h, "runtime": "not-started"},
                "ending flag not exactly True": lambda h: {"attempt_id": h, "runtime": "not-started", "ended_before_start": 1},
                "start-requested": lambda h: {"attempt_id": h, "runtime": "start-requested", "ended_before_start": True},
                "uncertain": lambda h: {"attempt_id": h, "runtime": "uncertain", "cleanup": "pending", "observed_at": None, "last_activity_at": "2026-01-01T00:00:00+00:00"},
                "running": lambda h: {"attempt_id": h, "runtime": "running", "cleanup": "pending"},
                "destroyed but cleanup pending": lambda h: {"attempt_id": h, "runtime": "destroyed", "cleanup": "pending", "observed_at": "2026-01-02T00:00:00+00:00", "last_activity_at": "2026-01-01T00:00:00+00:00"},
                "destroyed before last activity": lambda h: {"attempt_id": h, "runtime": "destroyed", "cleanup": "complete", "observed_at": "2026-01-01T00:00:00+00:00", "last_activity_at": "2026-01-02T00:00:00+00:00"},
                "destroyed without observation": lambda h: {"attempt_id": h, "runtime": "destroyed", "cleanup": "complete", "observed_at": None, "last_activity_at": "2026-01-02T00:00:00+00:00"},
                "evidence about another attempt": lambda h: dict(GONE("someone-else")),
                "evidence about the asker": lambda h: dict(GONE("a2"))}
            for name, callback in cases.items():
                with self.assertRaises(homes.HomePending, msg=name):
                    homes.acquire(self.root, **ID, attempt_id="a2", previous_runtime=callback)
                self.assertEqual((self.place / "record.json").read_bytes(), before, name)
                self.assertEqual(sorted(os.listdir(self.place)), listing, name)
            print("E1 interrupted at %s: %d unproved forms all pending; record bytes and directory listing unchanged; home present: %s" % (point, len(cases), (self.place / "home").exists()))

    def test_E2_proved_cessation_takes_over_and_finishes(self):
        for point, evidence in (("mkdir", GONE), ("ready", GONE),
                ("mkdir", lambda h: {"attempt_id": h, "runtime": "destroyed", "cleanup": "complete", "observed_at": "2026-01-02T00:00:00+00:00", "last_activity_at": "2026-01-01T00:00:00+00:00"})):
            self.setUp()
            before = json.loads(self.interrupted(point))
            asked = []
            got = homes.acquire(self.root, **ID, attempt_id="a2", previous_runtime=lambda h: (asked.append(h), evidence(h))[1])
            after = json.loads((self.place / "record.json").read_text())
            info = os.stat(self.place / "home")
            print("E2 interrupted at %s: asked about %s; record now %s/%s; identity and created_at kept: %s; home mode %o" % (point, asked, after["holder"], after["state"],
                  (after["identity"], after["created_at"]) == (before["identity"], before["created_at"]), info.st_mode & 0o777))
            self.assertEqual(asked, ["a1"])
            self.assertEqual(after, dict(before, holder="a2", state="ready"))
            self.assertEqual(got["home"], str(self.place / "home"))
            self.assertEqual(info.st_mode & 0o777, 0o700)
            # the earlier holder is now the one that waits; a replay by the new holder asks nobody
            with self.assertRaises(homes.HomePending):
                homes.acquire(self.root, **ID, attempt_id="a1", previous_runtime=lambda h: None)
            self.assertEqual(homes.acquire(self.root, **ID, attempt_id="a2"), got)

    def test_E3_takeover_interrupted_again_is_replayable_by_the_successor_only(self):
        before = json.loads(self.interrupted("mkdir"))
        real = os.mkdir
        def mkdir(path, *a, **k):
            # (first run matched any component named home, including the /home ancestor of the probe root: my error)
            if path == "home" and k.get("dir_fd") is not None and os.readlink("/proc/self/fd/%d" % k["dir_fd"]) == str(self.place):
                raise OSError(28, "probe")
            return real(path, *a, **k)
        with mock.patch.object(os, "mkdir", side_effect=mkdir):
            with self.assertRaises(OSError):
                homes.acquire(self.root, **ID, attempt_id="a2", previous_runtime=GONE)
        middle = json.loads((self.place / "record.json").read_text())
        print("E3 successor interrupted too: record", middle["holder"], middle["state"], "| home present:", (self.place / "home").exists())
        self.assertEqual(middle, dict(before, holder="a2"))
        with self.assertRaises(homes.HomePending):
            homes.acquire(self.root, **ID, attempt_id="a3", previous_runtime=lambda h: None)
        got = homes.acquire(self.root, **ID, attempt_id="a2")
        self.assertEqual(json.loads((self.place / "record.json").read_text()), dict(before, holder="a2", state="ready"))
        print("E3 successor replay finishes:", Path(got["home"]).is_dir())

    def test_E4_ready_branch_is_unchanged(self):
        homes.acquire(self.root, **ID, attempt_id="a1")
        before = (self.place / "record.json").read_bytes()
        with self.assertRaises(homes.HomePending):
            homes.acquire(self.root, **ID, attempt_id="a2", previous_runtime=lambda h: {"attempt_id": h, "runtime": "uncertain"})
        self.assertEqual((self.place / "record.json").read_bytes(), before)
        os.rmdir(self.place / "home")
        with self.assertRaises(homes.HomeRefusal) as caught:
            homes.acquire(self.root, **ID, attempt_id="a2", previous_runtime=GONE)
        self.assertNotIsInstance(caught.exception, homes.HomePending)
        print("E4 ready record: uncertain holder pending; a ready record whose home is absent is still refused outright:", str(caught.exception))


if __name__ == "__main__":
    unittest.main(verbosity=2)
