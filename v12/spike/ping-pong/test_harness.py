"""SPIKE ONLY — the guards W17110's reviewer cases do not separately reach.

The review's nine regressions are durable reviewer-owned evidence and live in
`work/records/.../evidence/test_spike_review.py`. They are not edited here.

What is here is the difference between "the suite is green" and "every guard is
established": four of the corrections were measured VACUOUS against those nine,
because another guard reached the same verdict first. A guard nothing can
observe is a guard nobody has established, so each one below is separated by a
case that can only fail for its own reason.

Run from `v12/spike/ping-pong`:  python3 -m unittest test_harness
"""

import contextlib
import hashlib
import importlib.util
import io
import json
import os
import pathlib
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

HERE = pathlib.Path(__file__).resolve().parent


def _loaded(name, place):
    spec = importlib.util.spec_from_file_location(name, place)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


trial = _loaded("w17110_trial", HERE / "trial.py")
preflight = _loaded("w17110_preflight", HERE / "preflight.py")


def _published(**override):
    """A well-formed published document, before anything is spoiled."""
    answer = "pong"
    document = {
        "spike": "w17110-ping-pong", "provider": "claude",
        "correlation_id": None,
        "started_at": "2026-08-27T00:00:00.000Z",
        "finished_at": "2026-08-27T00:00:01.000Z",
        "exit_status": 0,
        "result_digest": "sha256:" + hashlib.sha256(
            answer.encode("utf-8")).hexdigest(),
        "result_bytes": len(answer), "stderr_bytes": 0,
    }
    document.update(override)
    return document


class Engine:
    """The engine seam, answering a script.

    `image_id` is settable because one of the guards below is only reachable
    when there is no recorded id to fall back on -- which is the state a build
    that answered nothing would leave.
    """

    def __init__(self, *, document=None, drop=None, remove_status=0,
                 kill_status=0, rm_status=0, hang=False,
                 image_survives=False, inventory_lists=False):
        self.document = document
        self.drop = drop
        self.remove_status = remove_status
        self.kill_status = kill_status
        self.rm_status = rm_status
        self.hang = hang
        # A REAL ENGINE ANSWERS NON-ZERO FOR AN IMAGE THAT IS GONE, and this
        # fake has to as well. W17110's fourth review made the recorded
        # identity queried after every removal; a stub that answered zero to
        # everything would report every image as surviving and turn every
        # control below into a failure for the wrong reason.
        self.image_survives = image_survives
        # The INVENTORY's own answer, separate from `inspect`'s. They can
        # disagree, and which of them is believed is a rule worth pinning.
        self.inventory_lists = inventory_lists

    def __call__(self, *arguments, **options):
        if arguments[0] == "run":
            if self.hang:
                raise subprocess.TimeoutExpired(arguments, 1)
            sources = {}
            for index, value in enumerate(arguments):
                if value != "--mount":
                    continue
                fields = dict(part.split("=", 1)
                              for part in arguments[index + 1].split(",")
                              if "=" in part)
                sources[fields["target"]] = fields["source"]
            with open(os.path.join(sources["/input"], "input.json"),
                      encoding="utf-8") as reading:
                correlation = json.load(reading)["correlation_id"]
            document = dict(self.document or _published())
            document["correlation_id"] = correlation
            for name in (self.drop or ()):
                document.pop(name, None)
            with open(os.path.join(sources["/output"], "output.json"), "w",
                      encoding="utf-8") as writing:
                json.dump(document, writing)
            return subprocess.CompletedProcess(arguments, 0, b"", b"")
        if arguments[:2] == ("image", "rm"):
            return subprocess.CompletedProcess(
                arguments, self.remove_status, b"", b"")
        if arguments[0] == "kill":
            return subprocess.CompletedProcess(
                arguments, self.kill_status, b"", b"")
        if arguments[:2] == ("image", "ls") and "--all" in arguments:
            listed = b"sha256:image\n" if self.inventory_lists else b""
            return subprocess.CompletedProcess(arguments, 0, listed, b"")
        if arguments[:2] == ("image", "inspect"):
            # THE ENGINE'S REAL WORDING, because the harness now reads it. An
            # absent image is status 1 AND "No such image"; a stub that gave
            # status 1 with silence would be an unreachable daemon as far as
            # the caller can tell, which is exactly the distinction under test.
            if self.image_survives:
                return subprocess.CompletedProcess(arguments, 0, b"", b"")
            return subprocess.CompletedProcess(
                arguments, 1, b"",
                b"Error response from daemon: No such image: sha256:image")
        if arguments[0] == "rm":
            return subprocess.CompletedProcess(
                arguments, self.rm_status, b"", b"")
        return subprocess.CompletedProcess(arguments, 0, b"", b"")


class EachGuardIsReachableOnItsOwn(unittest.TestCase):

    def run_trial(self, engine, *, image_id="sha256:image", remove_staged=True):
        with tempfile.TemporaryDirectory(prefix="w17110-harness-") as root:
            credential = os.path.join(root, "credential.json")
            with open(credential, "w", encoding="utf-8") as writing:
                writing.write("not-opened")
            home = os.path.join(root, "staged")
            os.makedirs(home)
            printed = io.StringIO()
            removal = (trial.shutil.rmtree if remove_staged
                       else lambda *_a, **_k: None)
            with patch.object(trial, "built", return_value=image_id), \
                    patch.object(trial, "engine", engine), \
                    patch.object(trial.tempfile, "mkdtemp",
                                 return_value=home), \
                    patch.object(trial.shutil, "rmtree", removal), \
                    contextlib.redirect_stdout(printed):
                status = trial.main(["claude", "--credentials", credential])
            return status, json.loads(printed.getvalue())

    def test_a_document_short_a_required_member_is_refused(self):
        """SEPARATED FROM THE UNKNOWN-MEMBER RULE. The reviewer's case supplies
        every required fact and two EXTRA ones; nothing there can fail for a
        member that is absent, and the two halves of the closed shape are two
        different mistakes a publisher can make.
        """
        for missing in ("spike", "result_digest", "exit_status",
                        "stderr_bytes"):
            with self.subTest(missing=missing):
                status, report = self.run_trial(Engine(drop=[missing]))
                self.assertNotEqual(status, 0)
                self.assertFalse(report["verdict"]["closed_result_shape"])
                self.assertFalse(report["satisfying"])

    def test_a_refused_image_removal_alone_prevents_clean(self):
        """SEPARATED FROM THE SURVIVING-ID FALLBACK. When a removal fails the
        recorded image id is added to the survivor list, so the reviewer's case
        fails on that instead -- and the removal check itself is never the
        deciding clause. With no recorded id there is no fallback, and only the
        removal's own answer is left to notice.
        """
        status, report = self.run_trial(Engine(remove_status=1), image_id="")
        self.assertEqual(report["images_surviving"], [])
        self.assertFalse(report["image_removed"])
        self.assertFalse(report["clean"])
        self.assertNotEqual(status, 0)

    def test_nothing_to_ask_about_is_not_a_failed_query(self):
        """The default beside the identity query, and it needs its own case.

        With no recorded image id there is nothing to ask the engine about, so
        no identity query runs and its outcome is ABSENT. Absent must not read
        as failed -- a verdict that treated "there was nothing to observe" as
        "the observation failed" would refuse every trial whose build answered
        no id, for a reason that never happened.

        Everything else here succeeds, so `clean` has nothing else to fail on
        and this default is the only clause left deciding.
        """
        status, report = self.run_trial(Engine(), image_id="")
        self.assertNotIn("image_identity_query_ok", report)
        self.assertTrue(report["clean"])

    def test_a_timeout_whose_cleanup_failed_is_not_clean(self):
        """The timeout path's own kill and removal. Recording their status was
        not the fail-closed treatment the review asked for; participating in
        the verdict is."""
        for what, engine in (
                ("the kill failed", Engine(hang=True, kill_status=1)),
                ("the removal failed", Engine(hang=True, rm_status=1))):
            with self.subTest(what=what):
                status, report = self.run_trial(engine)
                self.assertEqual(report["failure_category"], "timeout")
                self.assertFalse(report["clean"])
                self.assertNotEqual(status, 0)

    def test_an_image_that_outlives_its_own_removal_is_a_survivor(self):
        """SEPARATED FROM THE REFUSED-REMOVAL CASE. Here the removal REPORTS
        SUCCESS and the identity is still there — an image untagged out of one
        reference while another still holds it. The removal's own answer says
        nothing about that, and only asking about the id can."""
        status, report = self.run_trial(Engine(image_survives=True))
        self.assertTrue(report["image_removed"])
        self.assertIn("sha256:image", report["images_surviving"])
        self.assertFalse(report["clean"])
        self.assertNotEqual(status, 0)

    def test_an_inventory_that_lists_the_id_outvotes_a_not_found(self):
        """SEPARATED FROM BOTH OTHER SURVIVOR ROUTES. Here the removal reports
        success AND the identity query says the engine has no such image --
        and a successful inventory lists it anyway.

        The inventory is status-bearing and orthogonal to the wording the
        not-found match reads, so when the two disagree the one that positively
        SAW the image wins. It may only ever ADD a survivor: an inventory that
        does not list an id cannot rescue an identity query that never ran,
        which is the direction the sixth review's finding was about.
        """
        status, report = self.run_trial(Engine(inventory_lists=True))
        self.assertTrue(report["image_removed"])
        self.assertTrue(report["image_identity_query_ok"])
        self.assertIn("sha256:image", report["images_surviving"])
        self.assertFalse(report["clean"])
        self.assertNotEqual(status, 0)

    def test_a_timeout_that_cleaned_up_says_so(self):
        """The control beside it: reaching the deadline is a RESULT, and one
        whose cleanup worked reports a clean engine even though the trial
        failed. Without this the case above could pass for the wrong reason."""
        status, report = self.run_trial(Engine(hang=True))
        self.assertEqual(report["failure_category"], "timeout")
        self.assertTrue(report["clean"])
        self.assertFalse(report["satisfying"])


class TheClosedShapeDecidesForItsOwnReasons(unittest.TestCase):
    """`_closed_shape` is exercised DIRECTLY here, and that is the point.

    Through a whole trial these guards are masked: the verdict's own
    `answer_is_exactly_pong` and `provider_exit_zero` clauses reach the same
    conclusion, so a document could be accepted as well-shaped and still fail —
    and the shape rule would never be the deciding clause. The shape is a
    separate claim about whether this harness recognises the document at all,
    so it is asked separately.
    """

    def document(self, **override):
        answer = "pong"
        base = {
            "spike": "w17110-ping-pong", "provider": "claude",
            "correlation_id": "w17110-probe",
            "started_at": "2026-08-27T00:00:00.000Z",
            "finished_at": "2026-08-27T00:00:01.000Z",
            "exit_status": 0,
            "result_digest": "sha256:" + hashlib.sha256(
                answer.encode("utf-8")).hexdigest(),
            "result_bytes": len(answer), "stderr_bytes": 0,
        }
        base.update(override)
        return base

    def test_the_canonical_success_document_is_recognised(self):
        """The control. Without it every case below could pass because the
        rule says no to everything."""
        self.assertTrue(trial._closed_shape(self.document()))

    def test_a_success_shape_must_have_answered_and_exited_clean(self):
        """No category means the document is CLAIMING success, and a claim of
        success that did not answer or did not exit clean is a document
        disagreeing with itself — not a failure document missing its
        category."""
        for what, override in (
                ("a wrong answer", {"result_digest": "sha256:" + "0" * 64}),
                ("a non-zero provider exit", {"exit_status": 1}),
                ("no observed exit at all", {"exit_status": None})):
            with self.subTest(what=what):
                self.assertFalse(trial._closed_shape(self.document(**override)))

    def test_a_boolean_is_not_an_integer_fact(self):
        """`isinstance(True, int)` is true in Python and false in JSON. Without
        the exact type test, `exit_status: true` reads as the number one — and
        `result_bytes: true` as a one-byte answer."""
        for name in ("exit_status", "result_bytes", "stderr_bytes"):
            with self.subTest(fact=name):
                self.assertFalse(
                    trial._closed_shape(self.document(**{name: True})))

    def test_each_fact_is_held_to_its_own_grammar(self):
        for what, override in (
                ("a digest that is not one", {"result_digest": "pong"}),
                ("an instant that is not one", {"started_at": "yesterday"}),
                ("another spike's document", {"spike": "something-else"}),
                ("a provider this harness has no image for",
                 {"provider": "gemini"}),
                ("a negative byte count", {"result_bytes": -1}),
                ("an empty correlation", {"correlation_id": ""})):
            with self.subTest(what=what):
                self.assertFalse(trial._closed_shape(self.document(**override)))

    def test_the_provider_rule_answers_rather_than_raises(self):
        """The RULE, asked directly. `value in CREDENTIAL_TARGET` raises on an
        unhashable value, and the blanket below would catch that — so through
        `_closed_shape` the two mechanisms are indistinguishable and neither
        can be established. This asks the rule on its own."""
        for value in ([], {}, {"a": 1}, ["claude"]):
            with self.subTest(value=value):
                self.assertIs(trial.FACT_RULES["provider"](value), False)
        self.assertIs(trial.FACT_RULES["provider"]("claude"), True)

    def test_the_validator_is_total_even_when_a_rule_misbehaves(self):
        """And the blanket, asked on its own.

        Per-rule typing is the fix; this is the property the review actually
        named — `_closed_shape` must be TOTAL over every JSON value, and that
        holds only if every rule is right. A rule that raises has not refused,
        it has escaped, so the validator answers False rather than letting one
        out. Driven by making a rule misbehave, which is the only way to
        separate it from the typing above.
        """
        def raises(_value):
            raise TypeError("a rule that forgot to check its own input")

        original = dict(trial.FACT_RULES)
        trial.FACT_RULES["spike"] = raises
        try:
            self.assertIs(trial._closed_shape(self.document()), False)
        finally:
            trial.FACT_RULES.clear()
            trial.FACT_RULES.update(original)
        # And restored, so nothing after this measures a patched validator.
        self.assertIs(trial._closed_shape(self.document()), True)

    def test_a_truthful_failure_document_is_recognised(self):
        """The failure branch's own control: a category BESIDE something that
        actually failed is a shape this harness has."""
        self.assertTrue(trial._closed_shape(self.document(
            exit_status=1, failure_category="authentication")))


class TheEnginesOwnWordingIsWhatTheMatchIsAgainst(unittest.TestCase):
    """The claim `NOT_FOUND` rests on, checked against the REAL engine.

    A pattern over another program's diagnostics is an empirical claim about
    that program, not a rule I get to assert -- and the sixth review's finding
    was exactly that I had asserted one. So the strings below are the engine's
    actual output, captured from a real `docker` on this host, and the case
    fails if either ever stops meaning what it means.
    """

    ABSENT = ("Error response from daemon: No such image: "
              "sha256:0000000000000000000000000000000000000000000000000000"
              "000000000000")
    UNREACHABLE = ("failed to connect to the docker API at "
                   "unix:///tmp/absent.sock; check if the path is correct and "
                   "if the daemon is running: dial unix /tmp/absent.sock: "
                   "connect: no such file or directory")
    DENIED = ("permission denied while trying to connect to the Docker API "
              "at unix:///var/run/docker.sock")

    def test_the_engines_not_found_wording_reads_as_observed_absence(self):
        self.assertTrue(trial.NOT_FOUND.search(self.ABSENT))

    def test_no_reachability_failure_reads_as_absence(self):
        """THE ONE THAT MATTERS, and the reason the pattern is narrow: the
        unreachable-daemon message contains 'no such file or directory', so a
        looser 'not found' or bare 'no such' alternative would match the very
        failure this exists to tell apart."""
        for what, said in (("an unreachable daemon", self.UNREACHABLE),
                           ("permission denied", self.DENIED)):
            with self.subTest(what=what):
                self.assertIsNone(trial.NOT_FOUND.search(said))


class AWriteDeniedSomewhereIsNotAWriteDeniedHere(unittest.TestCase):
    """W17110's ninth review [P1], driven against the real classifier.

    The classifier lives in `trial.mjs`, so these run it: node evaluates the
    module's own `category()` over fixed strings and prints the word it chose.
    A Python re-implementation of the rule would be a paraphrase, and this
    campaign has been corrected for paraphrases twice.
    """

    CREDENTIAL = "/home/nonroot/.claude/.credentials.json"

    def classified(self, text, credential=None):
        # `trial.mjs` runs `main()` on import, so the classifier is lifted
        # out and evaluated on its own rather than re-implemented here.
        source = (HERE / "trial.mjs").read_text(encoding="utf-8")
        start = source.index("// The exact path this trial mounted")
        end = source.index("// A last resort") if "// A last resort" in source \
            else source.index("const RUNTIMES")
        module = source[start:end] + "\nconsole.log(category(TEXT));\n"
        wanted = self.CREDENTIAL if credential is None else credential
        module = module.replace(
            'process.env.SPIKE_CREDENTIAL_PATH ?? ""', json.dumps(wanted), 1)
        assert "process.env" not in module, "the credential path was not pinned"
        module = "const TEXT = " + json.dumps(text) + ";\n" + module
        found = subprocess.run(
            ["node", "--input-type=module", "-e", module],
            capture_output=True, text=True, timeout=60, cwd=HERE)
        self.assertEqual(found.returncode, 0, found.stderr[:400])
        return found.stdout.strip()

    def test_a_write_denied_to_the_credential_earns_the_causal_name(self):
        """The one observation that would EXPLAIN rather than describe: the
        engine's own message naming the exact path this trial mounted."""
        self.assertEqual(
            self.classified(
                f"EACCES: permission denied, open '{self.CREDENTIAL}'"),
            "credential-write-denied")

    def test_a_write_denied_elsewhere_does_not(self):
        """THE CONTROL THE REVIEW ASKED FOR. Each of these is a real
        write-denied result and none of them says anything about the
        credential -- they name the output root, a scratch file, a log. A
        classifier that called them credential causation would be making the
        same unearned claim twice over."""
        for what in (
                "EACCES: permission denied, open '/output/out/result.txt'",
                "cannot write to /home/nonroot/.claude/statsig/cache",
                "failed to persist session state to /tmp/session.json",
                "Read-only file system (os error 30)"):
            with self.subTest(what=what[:40]):
                self.assertEqual(self.classified(what), "write-denied")

    def test_a_path_on_one_line_and_a_denial_on_another_is_not_causal(self):
        """THE CROSS-LINE CONTROL the tenth review asked for.

        Neither line below claims the credential could not be written. One
        mentions the path while reading it; the other reports a denial about
        somewhere else entirely. Joined into one blob they used to combine into
        a causal claim that no message in the run actually makes — two facts
        that never met, read as one.
        """
        for what, text in (
                ("a read of the credential, then an unrelated denial",
                 f"loaded credentials from {self.CREDENTIAL}\n"
                 "EACCES: permission denied, open '/output/out/result.txt'"),
                ("the denial first, the path after",
                 "cannot write to /tmp/session.json\n"
                 f"using {self.CREDENTIAL}"),
                ("the path in a line that is not a denial at all",
                 f"reading {self.CREDENTIAL}\n"
                 "Read-only file system (os error 30) while saving history")):
            with self.subTest(what=what):
                self.assertEqual(self.classified(text), "write-denied")

    def test_a_denial_naming_the_credential_on_its_own_line_still_is(self):
        """The control beside it: split by lines, the causal case still has to
        work, or the rule above would just be a way of never concluding."""
        self.assertEqual(
            self.classified(
                "starting up\n"
                f"EACCES: permission denied, open '{self.CREDENTIAL}'\n"
                "exiting"),
            "credential-write-denied")

    def test_with_no_credential_path_known_nothing_is_causal(self):
        """A trial that never learned where it mounted the credential cannot
        recognise a message about it, and must not guess."""
        self.assertEqual(
            self.classified(
                f"EACCES: permission denied, open '{self.CREDENTIAL}'",
                credential=""),
            "write-denied")

    def test_expiry_wording_still_only_describes(self):
        self.assertEqual(
            self.classified("OAuth token expired; refresh required"),
            "credential-expired")


class AnAncestorDecidesReadabilityToo(unittest.TestCase):
    """The reviewer's directory case proves the provider's OWN bits. This is
    the other half: a provider that is perfectly readable underneath a
    directory the container identity cannot traverse."""

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="w17110-ancestors-")
        os.chmod(self.root, 0o755)
        self.addCleanup(self.remove)

    def remove(self):
        for current, directories, _files in os.walk(self.root):
            for one in directories:
                os.chmod(os.path.join(current, one), 0o700)
        shutil.rmtree(self.root, ignore_errors=True)

    def place(self, mode, name="credential.json"):
        holder = os.path.join(self.root, "holder")
        os.makedirs(holder, exist_ok=True)
        where = os.path.join(holder, name)
        with open(where, "w", encoding="utf-8") as writing:
            writing.write("not-opened")
        os.chmod(where, 0o644)
        os.chmod(holder, mode)
        return where

    def test_a_readable_file_under_an_unreachable_directory_is_not_usable(self):
        self.assertFalse(preflight._readable_by_container(self.place(0o700)))

    def test_the_same_file_under_a_traversable_directory_is(self):
        """The control. Without it the case above could pass because the
        readability decision says no to everything."""
        self.assertTrue(preflight._readable_by_container(self.place(0o755)))

    def test_a_traversable_root_whose_entries_are_readable_IS_ready(self):
        """CORRECTED, and the correction is mine to own.

        This case used to assert the opposite: that a root the container cannot
        LIST makes the machine not ready. That rule was wrong, and the operator
        demonstrated it by nominating a provider exactly as asked --
        `/run/baton/credentials` at `0711`, traversable and deliberately not
        listable, which is the right mode for a credential directory -- and
        being refused for it.

        `r` on a directory is permission to read the NAMES. Nothing here needs
        the names: each trial mounts one exact path it was told. Readiness is
        about those paths and only those.
        """
        root = self.provider_root(0o711, 0o644)
        report, status = self.preflighted(
            root, {"probed": True, "readable": True})
        # The host's own numbering still says the root is not readable, and
        # that stays in the report as DESCRIPTION rather than as the decision.
        self.assertFalse(report["credential_providers"]["nominated"]
                         ["readable_by_container_uid"])
        self.assertTrue(all(report["credential_providers"]
                            ["usable_per_provider"].values()))
        self.assertEqual(status, 0)

    def test_a_probe_that_did_not_run_concludes_nothing(self):
        """The observation replaced a model, and it inherits the rule every
        other observation in this harness obeys: a probe that did not run is
        not a probe that found the file readable. With no observation the
        host-side model is all that is left, and it refuses these."""
        root = self.provider_root(0o711, 0o600)
        _report, status = self.preflighted(
            root, {"probed": False, "why": "the probe did not run"})
        self.assertNotEqual(status, 0)

    def provider_root(self, root_mode, entry_mode):
        root = os.path.join(self.root, f"provider-{root_mode:o}-{entry_mode:o}")
        os.makedirs(root)
        for name in ("claude", "codex"):
            where = os.path.join(root, name)
            with open(where, "w", encoding="utf-8") as writing:
                writing.write("not-opened")
            os.chmod(where, entry_mode)
        os.chmod(root, root_mode)
        return root

    def preflighted(self, root, observation):
        printed, complained = io.StringIO(), io.StringIO()
        with patch.object(preflight, "NOMINATED", root), \
                patch.object(preflight, "KNOWN", {}), \
                patch.object(preflight, "_engine", return_value={
                    "present": True, "client": "docker"}), \
                patch.object(preflight, "_reachable", return_value={}), \
                patch.object(preflight, "_observed_readable",
                             return_value=observation), \
                contextlib.redirect_stdout(printed), \
                contextlib.redirect_stderr(complained):
            status = preflight.main()
        return json.loads(printed.getvalue()), status


if __name__ == "__main__":
    unittest.main()
