"""K probe (M385328): the NEW bundled `work` CLI and `manager create --label`
through the FRESHLY BUILT bundle, against a disposable instance the bundle
itself installs. Mirrors tests.tools.test_connected_creation.
CreateTimeWorkLabelsThroughTheRealCommand, but every command is the frozen
executable run as a subprocess with nothing of the checkout in its environment
(tests.tools.test_packaged_creation.PackagedCreationCase.ran). The only
in-process acts are reading the disposable instance's own Authority to confirm
durable state, and granting `manage-work-labels` to the acting participant
(the connected test does the same; no bundled grant verb is in scope).
Disposable probe module: NOT part of the tree's test registry."""
import json, os, re, time, unittest
from pathlib import Path

from tests.tools import test_packaged_creation as packaged

OUT = Path(os.environ["K_PROBE_OUT"])


class PackagedWorkLabels(packaged.PackagedCreationCase):
    def setUp(self):
        super().setUp()
        self.transcript = []; self.t0 = time.monotonic()
        self.addCleanup(self._dump)

    def _dump(self):
        name = self.id().rsplit(".", 1)[-1]
        (OUT / f"transcript-{name}.json").write_text(json.dumps(
            {"test": self.id(), "bundle": str(self.command), "seconds": round(time.monotonic() - self.t0, 3),
             "calls": self.transcript}, indent=1) + "\n")

    def ran(self, *operands):
        done = super().ran(*operands)
        self.transcript.append({"argv": list(operands), "returncode": done.returncode,
                                "stdout": done.stdout, "stderr": done.stderr[-2000:]})
        return done

    # -- helpers --------------------------------------------------------------
    def labelled(self, *labels, task=None):
        extra = []
        for one in labels: extra += ["--label", one]
        return (task, None, *extra)

    def authority(self, *, writable=False):
        from baton_v12.authority import Authority
        opener = Authority.open if writable else Authority.open_readonly
        held = opener(self.owned["authority_store"], expected_authority_uuid=self.owned["authority_uuid"])
        self.addCleanup(held.dispose); return held

    def work_cli(self, *operands):
        done = self.ran("work", *operands, "--authority-store", self.owned["authority_store"],
                        "--authority-uuid", self.owned["authority_uuid"])
        return done.returncode, done.stdout, done.stderr

    def act(self, verb, operation_id, *labels):
        operands = [verb, "--participant", "baton.slaw", "--work", self.work, "--operation-id", operation_id]
        for one in labels: operands += ["--label", one]
        return self.work_cli(*operands)

    def jobless_install(self):
        self.packaged_install(jobs=[], line_declared_base="a" * 40, canonical_target_id="target-1")

    # -- cases ----------------------------------------------------------------
    def test_the_work_subcommand_is_offered_with_its_four_verbs(self):
        self.packaged_install()
        done = self.ran("work", "--help")
        self.assertEqual(done.returncode, 0, done.stderr)
        for verb in ("label-work", "unlabel-work", "labels", "list"):
            self.assertIn(verb, done.stdout)
        # argparse re-wraps the description, so the sentence is checked in fragments.
        self.assertIn("not v11's", done.stdout); self.assertIn("thread label/unlabel", done.stdout)
        done = self.ran("work")
        self.assertEqual(done.returncode, 2, done.stderr)   # argparse: a verb is required
        code, said, err = self.work_cli("labels", "--work", self.work)
        self.assertEqual(code, 0, err)
        self.assertEqual(json.loads(said)["labels"], [])

    def test_a_creation_that_makes_the_work_applies_its_labels(self):
        self.jobless_install()
        done = self.packaged_refusal(*self.labelled("Release-Foo", "V12"))
        self.assertIn("is RESERVED", done.stderr)
        code, said, err = self.work_cli("labels", "--work", self.work)
        self.assertEqual(code, 0, err)
        answer = json.loads(said)
        self.assertEqual(answer["labels"], ["release-foo", "v12"])
        self.assertEqual([(e["label"], e["act"]) for e in answer["events"]],
                         [("release-foo", "work-create"), ("v12", "work-create")])
        code, said, err = self.work_cli("list", "--label", "v12")
        self.assertEqual(code, 0, err); self.assertEqual(json.loads(said)["work"], [self.work])
        code, said, err = self.work_cli("list", "--label", "v12", "--without-label", "release-foo")
        self.assertEqual(code, 0, err); self.assertEqual(json.loads(said)["work"], [])
        from baton_v12.job_manager import creation as creating
        self.assertEqual(self.authority().work_creation(self.work)["operation_id"],
                         creating.work_operation_id(self.JOB, self.work))
        again = self.packaged_refusal(*self.labelled("Release-Foo", "V12"))
        self.assertIn("is RESERVED", again.stderr); self.assertNotIn("work label-work", again.stderr)
        self.assertEqual(self.authority().labels_of(self.work), ["release-foo", "v12"])

    def test_a_reused_work_refuses_relabel_and_the_work_verb_adds_the_label(self):
        self.packaged_install()
        done = self.packaged_refusal(*self.labelled("v12"))
        for sentence in ("would reuse the existing Work", "was not made by this creation",
                         "it was made by the operation `bootstrap-job-a`", "work label-work",
                         "Nothing was reserved by this request"):
            self.assertIn(sentence, done.stderr)
        self.assertNotIn(self.JOB, self.bindings()); self.assertEqual(self.submitted(self.JOB), [])
        code, said, err = self.work_cli("labels", "--work", self.work)
        self.assertEqual(json.loads(said)["labels"], [])
        # Without the capability the bundled act is refused by the Authority, exit 2, nothing changed.
        code, said, err = self.act("label-work", "labels-0", "V12")
        self.assertEqual(code, 2, (said, err)); self.assertTrue(err.startswith("refused: "), err)
        self.assertEqual(self.authority().labels_of(self.work), [])
        self.authority(writable=True).grant_capability("baton.slaw", "manage-work-labels")
        code, said, err = self.act("label-work", "labels-1", "V12")
        self.assertEqual(code, 0, err)
        answer = json.loads(said)
        self.assertEqual(answer["changed"], ["v12"]); self.assertEqual(answer["labels"], ["v12"])
        self.assertEqual(answer["acts"][0]["decision"]["role"], "manage-work-labels")
        # EXACT REPLAY: same identity, same operands -> byte-identical answer, no second effect.
        code2, said2, err2 = self.act("label-work", "labels-1", "V12")
        self.assertEqual(code2, 0, err2); self.assertEqual(said2, said)
        self.assertEqual(len(self.authority().work_label_events(self.work)), 1)
        # COLLISION: same identity, different operands -> refused, nothing changed.
        code, said3, err3 = self.act("label-work", "labels-1", "other")
        self.assertEqual(code, 2, (said3, err3)); self.assertEqual(self.authority().labels_of(self.work), ["v12"])
        again = self.packaged_refusal(*self.labelled("v12"))
        self.assertIn("was not made by this creation", again.stderr)
        held = self.packaged_answer()
        self.assertEqual(held["work"]["state"], "reused"); self.assertEqual(held["work"]["requested_labels"], [])
        self.assertIn(self.JOB, self.bindings())
        code, said, err = self.work_cli("list", "--label", "v12")
        self.assertEqual(json.loads(said)["work"], [self.work])
        code, said, err = self.act("unlabel-work", "labels-2", "v12")
        self.assertEqual(code, 0, err); self.assertEqual(json.loads(said)["labels"], [])
        code, said, err = self.work_cli("labels", "--work", self.work)
        self.assertEqual(json.loads(said)["labels"], [])
        self.assertEqual(len(json.loads(said)["events"]), 2)

    def test_full_capacity_restoring_acts_run_in_the_named_order(self):
        from baton_v12.authority.labels import MAX_LABELS
        minted = [f"label-{i:02}" for i in range(MAX_LABELS)]
        self.jobless_install()
        first = self.packaged_refusal(*self.labelled(*minted))
        self.assertIn("reported no binding", first.stderr)
        self.assertEqual(self.authority().labels_of(self.work), minted)
        self.authority(writable=True).grant_capability("baton.slaw", "manage-work-labels")
        code, said, err = self.act("unlabel-work", "drift-1", "label-00"); self.assertEqual(code, 0, err)
        code, said, err = self.act("label-work", "drift-2", "extra"); self.assertEqual(code, 0, err)
        drifted = sorted(minted[1:] + ["extra"])
        self.assertEqual(self.authority().labels_of(self.work), drifted); self.assertEqual(len(drifted), MAX_LABELS)
        again = self.packaged_refusal(*self.labelled(*minted))
        self.assertIn("this creation minted the Work", again.stderr); self.assertIn("is RESERVED", again.stderr)
        named = re.findall(r"`(baton-v12-stack work [^`]+)`", again.stderr)
        self.assertEqual(named, [f"baton-v12-stack work unlabel-work --work {self.work} --label extra",
                                 f"baton-v12-stack work label-work --work {self.work} --label label-00"])
        code, said, err = self.act("label-work", "wrong-order", "label-00")
        self.assertEqual(code, 2, (said, err)); self.assertIn("maximum", err)
        self.assertEqual(self.authority().labels_of(self.work), drifted)
        for index, command in enumerate(named):
            operands = command.split()[2:]
            code, said, err = self.work_cli(*operands, "--participant", "baton.slaw", "--operation-id", f"restore-{index}")
            self.assertEqual(code, 0, (command, said, err))
        self.assertEqual(self.authority().labels_of(self.work), minted)
        third = self.packaged_refusal(*self.labelled(*minted))
        self.assertIn("reported no binding", third.stderr); self.assertNotIn("label-work", third.stderr)
        self.assertEqual(self.submitted(self.JOB), [])
        code, said, err = self.work_cli("labels", "--work", self.work)
        self.assertEqual(len(json.loads(said)["events"]), MAX_LABELS + 4)

    def test_malformed_and_duplicate_labels_refuse_before_any_effect(self):
        self.packaged_install()
        done = self.packaged_refusal(*self.labelled("v12", "V12"))
        self.assertIn("one label after normalization", done.stderr)
        for bad in ("team=core", "v12,hot", "has space", "a" * 65):
            done = self.packaged_refusal(*self.labelled(bad))
            self.assertIn("a Work label is 1 to 64 characters", done.stderr)
        self.authority(writable=True).grant_capability("baton.slaw", "manage-work-labels")
        for bad in ("team=core", "v12,hot"):
            code, said, err = self.act("label-work", "bad-" + bad, bad)
            self.assertEqual(code, 2, (said, err)); self.assertTrue(err.startswith("refused: "), err)
        code, said, err = self.act("label-work", "dup", "v12", "V12")
        self.assertEqual(code, 2, (said, err))
        self.assertEqual(self.authority().labels_of(self.work), [])
        self.assertEqual(self.authority().work_label_events(self.work), [])
        self.assertNotIn(self.JOB, self.bindings())
        self.assertEqual([j["job_id"] for j in self.install_document()["jobs"]], ["job-a"])
