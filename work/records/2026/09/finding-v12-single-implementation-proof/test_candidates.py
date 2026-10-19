"""W321528 — a failed turn's RETAINED candidate is reported, or honestly refused.

The defect this closes, in one sentence: the selected live run of this Work
timed out at 900s with a real three-file candidate retained on its private
line, and the report said the run retained nothing at all -- because the only
question anybody asked was "what did it PUBLISH", and a turn that did not
complete publishes nothing by contract.

So these drive `_candidates` at the boundary the review named, over the two
records of one artifact that actually exist: the worker's SEALED result manifest
and the manager's OWN INDEX of what it received. The four states are proved to
be four different answers -- `valid`, `absent`, `refused`, `unreadable` -- and
the last is proved NOT to be reported as absence, which is the conflation that
produced the original false report.

AND THE OPERANDS ARE THE PRODUCERS' OWN, which is the correction this round
made. The earlier fixture invented three of them and every case in the file was
being asserted against an EARLY REFUSAL rather than against the behaviour it
named:

  the artifact reference carried an `artifact-bbbbbbbb` identity and a
  `.bundle` file locator. `sealing._answered` answers `"{attempt}:{output}"`
  over a custody DIRECTORY, so the collector's ownership gate refused every
  case before its attribution, custody and unreadable assertions could be
  reached. The gate was right; the double was not, and it is corrected here
  rather than the gate relaxed to admit it. `_answered` itself is asked what
  the reference is, so this cannot drift again in silence.

  nothing configured a task document, so `_bound_task` could not resolve and
  every ordinary-test observation read `unreported` -- including the four that
  exist to prove an integer status is interpreted. A real document is written
  on disk now and the observation's `task_digest` is the digest of ITS bytes.

  the sealed `content_manifest` was `null` and the locator named nothing, so
  `_retained_bytes` had no measurement to make. The retained artifact is a
  REAL DISPOSABLE TREE now, measured by `workspaces.directory_manifest`, and
  valid, missing, damaged, substituted and unreadable bytes are each driven
  at that normal boundary -- which is the one thing metadata doubles cannot
  establish about bytes.

Nothing here runs a provider, an engine or a container. What is doubled is the
two store reads and the durable line's commit object, so a single custody
disagreement can be introduced on purpose; `test_baseline`'s own cases drive
the real Git reads behind the last of those. What is NOT doubled is the
collector, the contract boundaries it refuses through, or the measurement of
the retained bytes.
"""

import errno
import hashlib
import json
import os
import shutil
import stat
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import baseline                                              # noqa: E402

# THE REAL BOUNDARIES, because `_retained_bytes` refuses THROUGH them: the
# locator grammar, the §12 rule 6 manifest check and the measurement are each
# their owner's, and a double for any of them would be this file holding its
# own opinion about bytes it also supplied.
from baton_v12.contracts import ContractRefusal                # noqa: E402
from baton_v12.worker_manager import attempts as attempt_rows   # noqa: E402
from baton_v12.worker_manager import workspaces                 # noqa: E402
import baton_v12.worker_manager as worker_manager               # noqa: E402

ATTEMPT = "attempt-" + "a" * 8
BASE = "3dcf6dc4bcee97e932d17c93ac13c5811b3af188"
HEAD = "2c89d3aa1c3ccf190a47417f3147593b694948dd"
TASK_ID = "failed-reporting-w321528-321530"

# The verification command the configured task document declares, and the argv
# the observation must name to be an account of THAT command.
ARGV = ["python3", "harness.py"]

# `claude_agent.BUNDLE`, which is the word its `_claim` puts in `transport`.
TRANSPORT = "objects.bundle"

# The four members `claude_agent._publish_line` writes into the declared
# proposal output, which is what the manager seals and what the locator names.
RETAINED = (("change.patch", "--- a/harness.py\n+++ b/harness.py\n@@\n+now\n"),
            ("objects.bundle", "PACK\x00\x02 not a real bundle, real bytes\n"),
            ("result.json", '{"schema": "baton.dogfood-proposal/2"}\n'),
            ("verification.txt", "the ordinary tests ran and answered 0\n"))

_KEEP = object()


def refusal(message):
    """The distribution's own refusal, raised the way its owners raise it.

    A stand-in class here would be caught by `_candidates` only because this
    file also handed it over; the real type is what a real store read raises
    and what the collector's `except` clauses actually name.
    """
    return ContractRefusal("refused", "precondition", message)


class Collector(unittest.TestCase):
    """One attempt, REAL retained bytes, and doubles only where a store is."""

    def setUp(self):
        self.home = tempfile.mkdtemp(prefix="v12-w321528-")
        self.addCleanup(shutil.rmtree, self.home, True)
        # -- THE REAL DISPOSABLE RETAINED ARTIFACT ---------------------------
        #
        # A custody directory holding exactly what `_publish_line` writes, and
        # MEASURED by the owner that measures it in production. Every number
        # the seal below declares comes from this measurement, so a case that
        # changes one byte under it is changing the bytes and not a document
        # about them.
        self.place = os.path.join(self.home, "custody", ATTEMPT, "proposal")
        os.makedirs(self.place)
        for name, body in RETAINED:
            self.wrote(os.path.join(self.place, name), body)
        self.measured = workspaces.directory_manifest(self.place)
        # -- THE DEPLOYMENT'S OWN CONFIGURED MATERIAL ------------------------
        #
        # A real task document at a real path, named by a real implementation
        # worker in a real configuration file. `_bound_task` opens it and
        # digests THE BYTES ON DISK, which is the whole reason the digest is
        # not a member this fixture asserts twice.
        self.task_place = os.path.join(self.home, "task.json")
        self.task_bytes = (json.dumps(
            {"schema": "baton.dogfood-task/2", "task_id": TASK_ID,
             "instructions": "close the failed-run reporting gap",
             "verification": list(ARGV), "source_root": "source",
             "source_profile": "generic", "declared_base": None},
            indent=1, sort_keys=True) + "\n").encode("utf-8")
        self.wrote(self.task_place, self.task_bytes)
        self.task_digest = "sha256:" + hashlib.sha256(
            self.task_bytes).hexdigest()
        self.configured_task = self.task_place
        # HOW MANY IMPLEMENTATION WORKERS this deployment configures. The
        # bound task is derived from exactly one producer's document, so none
        # and two are both unanswerable rather than guessed at.
        self.producers = 1
        self.declared = BASE
        self.config_place = os.path.join(self.home, "deployment.json")
        self.packet = {"deployment": {"config_path": self.config_place}}
        # -- the two store reads, and the durable line's commit object -------
        self.frozen = {"disposition": "unable",
                       "manifest_digest": "sha256:" + "d" * 64,
                       "artifacts": [self.indexed()]}
        self.manifest = self.sealed()
        self.assignment = {"authority_uuid": "0" * 32,
                           "work_id": "00000000-W1",
                           "participant": "baton.impl",
                           "principal": "principal:baton.impl",
                           "generation": 1,
                           "effective_scope": "scope:deployment"}
        # THE RETAINED LINE'S OWN ANSWER. Review 2026-10-18T08-39-00Z P1:
        # metadata agreement between the seal and the index is not custody, so
        # `_candidates` reads the commit object through `line_attribution`'s
        # supported boundary. This stands in for that read so a missing,
        # damaged or substituted retained history can be driven on purpose.
        self.custody = {
            "author": f"{baseline.COMMIT_NAME} <{baseline.COMMIT_EMAIL}>",
            "committer": f"{baseline.COMMIT_NAME} <{baseline.COMMIT_EMAIL}>",
            "parents": [BASE], "head": HEAD, "base": BASE}
        # WHICH READS HAVE ANSWERED, in order. DB-1 is why the measurement is
        # last; `TheMeasurementIsOutsideEveryStoreRead` is what observes it.
        self.order = []
        self.shortfalls = []

    @staticmethod
    def wrote(place, body):
        with open(place, "wb") as writing:
            writing.write(body if isinstance(body, bytes)
                          else body.encode("utf-8"))

    # -- the producers' own documents ---------------------------------------

    def reference(self, **changed):
        """THE SEALER'S OWN `artifactRef`, member for member.

        `sealing._answered` composes exactly this: the identity is
        `"{attempt}:{output}"`, the media type is `application/octet-stream`,
        the width and digest are the MEASURED manifest's aggregates, and the
        locator is `file://` plus the custody DIRECTORY. The agreement is
        asked of `_answered` itself in
        `ForeignBytesUnderThisTurnsSealAreRefused` rather than trusted here.
        """
        held = {"artifact_id": f"{ATTEMPT}:{baseline.PROPOSAL_OUTPUT}",
                "media_type": "application/octet-stream",
                "bytes": self.measured["total_bytes"],
                "content_digest": self.measured["tree_digest"],
                "locator": f"file://{self.place}"}
        held.update(changed)
        return held

    def indexed(self, **changed):
        """The manager's OWN indexed row for the artifact it received."""
        held = dict(self.reference(), output_name=baseline.PROPOSAL_OUTPUT)
        held.update(changed)
        return held

    def observation(self, **changed):
        """THE PRODUCER'S OWN SHAPE, from `claude_agent._ordinary_tests`.

        `task_id`, `task_digest`, `argv`, `status` -- an INTEGER OR `None` --
        plus `base` and `head`. There is no `outcome` member anywhere in it,
        which is the schema the first reader invented and these cases refuse
        to. `task_digest` is the digest of the configured document's exact
        bytes, so a bound observation is bound to a file rather than to a
        constant this file spells on both sides of the comparison.
        """
        held = {"task_id": TASK_ID, "task_digest": self.task_digest,
                "argv": list(ARGV), "status": 0, "base": BASE, "head": HEAD}
        held.update(changed)
        return held

    def output(self, *, claim=True, status="present", artifact=True,
               tests=None, content_manifest=_KEEP, **changed):
        held = {"name": baseline.PROPOSAL_OUTPUT, "type": "git-proposal",
                "status": status,
                "content_manifest": (self.measured
                                     if content_manifest is _KEEP
                                     else content_manifest),
                "artifact": self.reference(**changed) if artifact else None,
                "result_metadata": {}}
        if claim:
            held["result_metadata"][baseline.CLAIM_NAMESPACE] = {
                "base": BASE, "head": HEAD, "transport": TRANSPORT,
                "recap": "the turn retained its candidate and then failed"}
        if tests is not None:
            # ON THE OUTPUT, beside the claim, because that is where the real
            # producer puts it -- not at manifest level, which is where the
            # first reader looked and found nothing.
            held["result_metadata"][baseline.ORDINARY_TESTS_NAMESPACE] = tests
        return held

    def sealed(self, outputs=None):
        return {"outputs": [self.output()] if outputs is None else outputs,
                "result_metadata": {}}

    def restated(self, **changed):
        """One change made in BOTH accounts of the artifact.

        The sealed reference and the manager's indexed row are two records of
        the SAME artifact, so a case about what the seal says must move the
        row with it or it is only driving the disagreement gate again.
        """
        self.manifest = self.sealed(outputs=[self.output(**changed)])
        self.frozen["artifacts"] = [self.indexed(**changed)]

    def configured(self):
        """The deployment configuration, written from this case's operands.

        `_declared_base` and `_bound_task` each OPEN this file. The earlier
        fixture substituted the first and never wrote anything for the second,
        so the configured-material half of the collector was unproved.
        """
        producer = {}
        if self.configured_task is not None:
            producer["task_document"] = self.configured_task
        workers = [{"worker_id": "worker-w321528-review", "role": "review",
                    "deployment": {}}]
        for at in range(self.producers):
            workers.append({"worker_id": f"worker-w321528-impl-{at}",
                            "role": baseline.IMPLEMENTATION_ROLE,
                            "deployment": dict(producer)})
        document = {"workers": workers}
        if self.declared is not None:
            document["line_declared_base"] = self.declared
        self.wrote(self.config_place,
                   json.dumps(document, indent=1, sort_keys=True) + "\n")
        return self.config_place

    # -- the collector, reached unmodified ----------------------------------

    def collected(self, *, measure=None):
        """`_candidates` over this case's operands.

        The store reads are patched on the modules the collector imports them
        from, so the import inside the function resolves to these. The
        contract boundaries and `_retained_bytes` itself are the real ones --
        `measure=None` is the collector's own default and not a double.
        """
        self.configured()

        def frozen_output_of(_control, _attempt):
            if isinstance(self.frozen, Exception):
                raise self.frozen
            self.order.append("frozen")
            return self.frozen

        def load_manifest(_control, _digest, definition):
            assert definition == "resultManifest", definition
            if isinstance(self.manifest, Exception):
                raise self.manifest
            self.order.append("manifest")
            return self.manifest

        def assignment_of(_control, _attempt):
            if isinstance(self.assignment, Exception):
                raise self.assignment
            self.order.append("assignment")
            return self.assignment

        def inspect(_control, **named):
            """The retained line's own answer, so a missing, damaged or
            substituted retained history can be driven on purpose.
            `test_baseline`'s own cases exercise the real git reads behind
            it."""
            del named
            if isinstance(self.custody, Exception):
                raise self.custody
            self.order.append("line")
            return self.custody

        with mock.patch.object(worker_manager, "frozen_output_of",
                               frozen_output_of), \
                mock.patch.object(worker_manager, "load_manifest",
                                  load_manifest), \
                mock.patch.object(attempt_rows, "assignment_of",
                                  assignment_of):
            return baseline._candidates(object(), [ATTEMPT], self.packet,
                                        self.shortfalls, inspect=inspect,
                                        measure=measure)

    def one(self):
        found = self.collected()
        self.assertEqual(len(found), 1, found)
        self.assertEqual(found[0]["attempt_id"], ATTEMPT)
        return found[0]

    def denied(self, place, probe):
        """REALLY deny this process `place`, with the mode restored after.

        W325711 review. The conflation being closed is between an errno and
        an absence, so it cannot be driven by a double that raises
        `PermissionError`: that would be this file asserting that the
        collector classifies whatever this file decided to raise. The mode
        bits are changed on a real directory in a real temporary tree and the
        real kernel refuses the real syscall.

        AND THE REFUSAL IS PROVED TO HAVE HAPPENED. A process that traverses
        a `0o000` directory anyway -- uid 0, CAP_DAC_OVERRIDE, some mounts --
        would run every assertion below over a read that was never denied,
        which is a green test about nothing. `probe` is the syscall the
        collector will itself reach, and a bypass SKIPS: a privilege that
        defeats the setup is not evidence that the code under it is right.
        The source-level case in this class holds while that skip is taken.

        The restore is registered BEFORE the chmod could fail a case, so a
        failing assertion still leaves a tree `shutil.rmtree` can remove.
        """
        held = stat.S_IMODE(os.stat(place).st_mode)
        self.addCleanup(os.chmod, place, held)
        os.chmod(place, 0o000)
        try:
            probe()
        except PermissionError as why:
            self.assertEqual(why.errno, errno.EACCES, why)
            return
        raise unittest.SkipTest(
            f"this process reads {place!r} at mode 0o000, so a real "
            f"permission denial cannot be staged here and the behaviour "
            f"under one cannot be observed; it is NOT thereby proved")

    def refused_why(self):
        held = self.one()
        self.assertEqual(held["state"], baseline.CANDIDATE_REFUSED, held)
        self.assertTrue(self.shortfalls)
        self.assertIn("REFUSED retained candidate", self.shortfalls[0])
        return held["why"]

    def unreadable_why(self):
        held = self.one()
        self.assertEqual(held["state"], baseline.CANDIDATE_UNREADABLE, held)
        self.assertNotEqual(held["state"], baseline.CANDIDATE_ABSENT)
        self.assertTrue(self.shortfalls)
        self.assertIn("UNREADABLE retained candidate", self.shortfalls[0])
        return held["why"]


class AFailedTurnWithARetainedCandidate(Collector):
    """THE CASE THE LIVE RUN GOT WRONG."""

    def test_a_FAILED_turn_still_reports_its_valid_retained_candidate(self):
        held = self.one()
        self.assertEqual(held["state"], baseline.CANDIDATE_VALID)
        self.assertEqual(held["disposition"], "unable")
        self.assertEqual(held["head"], HEAD)
        self.assertEqual(held["base"], BASE)
        self.assertEqual(held["locator"], f"file://{self.place}")
        self.assertEqual(held["content_digest"], self.measured["tree_digest"])
        self.assertEqual(held["bytes"], self.measured["total_bytes"])
        self.assertEqual(held["transport"], TRANSPORT)
        self.assertIsNone(held["why"])

    def test_a_valid_retained_candidate_is_NOT_a_shortfall(self):
        """Reporting the useful fact as a deficiency would be the same mistake
        in the other direction."""
        self.one()
        self.assertEqual(self.shortfalls, [])

    def test_it_is_NOT_a_verification_and_NOT_an_acceptance(self):
        """A valid candidate is "these bytes are retained and their custody
        holds" and nothing about whether they are correct or wanted."""
        held = self.one()
        self.assertEqual(held["verification"],
                         baseline.VERIFICATION_UNREPORTED)
        # REVIEW P2: `none` would claim a read nobody performed. This Job
        # admits no reviewer and this supervisor consults no exact-candidate
        # acceptance evidence, so the honest value is that nobody looked.
        self.assertEqual(held["acceptance"], baseline.ACCEPTANCE_UNOBSERVED)

    def test_a_SUCCESSFUL_turn_is_collected_by_the_same_path(self):
        self.frozen["disposition"] = "completed"
        held = self.one()
        self.assertEqual(held["state"], baseline.CANDIDATE_VALID)
        self.assertEqual(held["disposition"], "completed")
        self.assertEqual(self.shortfalls, [])

    def test_the_PRODUCERS_OWN_STATUS_is_interpreted_not_invented(self):
        """Review P2: the first reader looked at manifest-level metadata for an
        `outcome` key that exists nowhere in the producer. These drive the real
        shape -- the observation on the proposal OUTPUT, with an integer or
        `None` `status`, bound to the configured task document's own bytes."""
        for status, expected in (
                (0, baseline.VERIFICATION_PASSED),
                (1, baseline.VERIFICATION_FAILED),
                (137, baseline.VERIFICATION_FAILED),
                # NOT `not-run`: the producer emits None for a skipped
                # command, a timeout AND a failed start alike.
                (None, baseline.VERIFICATION_NO_STATUS)):
            with self.subTest(status=status):
                self.setUp()
                self.manifest = self.sealed(
                    outputs=[self.output(tests=self.observation(
                        status=status))])
                held = self.one()
                self.assertEqual(held["verification"], expected)
                # AND THE CANDIDATE IS STILL REPORTED. What its command did
                # neither promotes nor demotes the bytes it ran over.
                self.assertEqual(held["state"], baseline.CANDIDATE_VALID)

    def test_a_TRUE_status_is_not_a_measured_zero(self):
        """`bool` is an `int` in Python and is not a status the producer can
        emit; reading `True` as a pass would be inventing the one answer
        nobody measured."""
        self.manifest = self.sealed(
            outputs=[self.output(tests=self.observation(status=True))])
        self.assertEqual(self.one()["verification"],
                         baseline.VERIFICATION_UNREPORTED)

    def test_a_MISSING_or_MALFORMED_observation_is_unreported(self):
        for tests in (None, {}, {"status": "zero"}, {"outcome": "passed"}):
            with self.subTest(tests=tests):
                self.setUp()
                self.manifest = self.sealed(
                    outputs=[self.output(tests=tests)])
                self.assertEqual(self.one()["verification"],
                                 baseline.VERIFICATION_UNREPORTED)

    def test_an_observation_carrying_an_EXTRA_member_is_unreported(self):
        """Held by EQUALITY: a document carrying a member this program does
        not read is not the document the producer it knows writes."""
        self.manifest = self.sealed(
            outputs=[self.output(tests=self.observation(outcome="passed"))])
        self.assertEqual(self.one()["verification"],
                         baseline.VERIFICATION_UNREPORTED)

    def test_an_observation_of_ANOTHER_CANDIDATE_is_not_this_ones(self):
        """An observation whose base/head are not this candidate's is an
        observation of something else."""
        for changed in ({"head": "f" * 40}, {"base": "e" * 40},
                        {"task_id": "some-other-task"}):
            with self.subTest(changed=changed):
                self.setUp()
                self.manifest = self.sealed(
                    outputs=[self.output(tests=self.observation(**changed))])
                self.assertEqual(self.one()["verification"],
                                 baseline.VERIFICATION_UNREPORTED)


class TheObservationIsBoundToTheConfiguredTask(Collector):
    """Review 2026-10-18T10-07-00Z, over a document that really exists.

    `_bound_task` derives the expectation from the DEPLOYMENT's own configured
    producer document rather than from the observation it exists to check, and
    the digest is taken over the exact bytes on disk. None of that was reached
    before: with no `config_path` in the packet the derivation raised, the task
    came back `None`, and every single observation -- correct ones included --
    was reported `unreported` for the wrong reason.
    """

    def observed(self, **changed):
        self.manifest = self.sealed(
            outputs=[self.output(tests=self.observation(**changed))])
        return self.one()

    def test_the_configured_documents_own_bytes_bind_a_passing_observation(
            self):
        held = self.observed()
        self.assertEqual(held["verification"], baseline.VERIFICATION_PASSED)
        self.assertEqual(held["state"], baseline.CANDIDATE_VALID)

    def test_the_bound_task_is_read_from_the_configured_producer(self):
        """The three members come from the file, and the digest is the file's.

        A re-serialisation of the parsed object would be a different document
        with the same meaning, which is exactly what a digest refuses.
        """
        self.configured()
        bound = baseline._bound_task(self.packet)
        with open(self.task_place, "rb") as handle:
            raw = handle.read()
        self.assertEqual(bound, {
            "task_id": TASK_ID, "argv": list(ARGV),
            "task_digest": "sha256:" + hashlib.sha256(raw).hexdigest()})

    def test_a_MISMATCHED_task_digest_stays_unreported(self):
        """The digest names the exact task bytes the turn consumed; an
        observation naming other bytes is an account of another run."""
        held = self.observed(task_digest="sha256:" + "1" * 64)
        self.assertEqual(held["verification"],
                         baseline.VERIFICATION_UNREPORTED)
        self.assertEqual(held["state"], baseline.CANDIDATE_VALID)

    def test_a_MISMATCHED_verification_argv_stays_unreported(self):
        self.assertEqual(self.observed(argv=["python3", "something.py"])[
            "verification"], baseline.VERIFICATION_UNREPORTED)

    def test_an_ABSENT_task_id_stays_unreported(self):
        """The shape the first correction admitted: `task_id` was asked about
        only when it was present, so an observation carrying none passed."""
        tests = self.observation()
        tests.pop("task_id")
        self.manifest = self.sealed(outputs=[self.output(tests=tests)])
        self.assertEqual(self.one()["verification"],
                         baseline.VERIFICATION_UNREPORTED)

    def test_an_UNCONFIGURED_task_document_leaves_it_unreported(self):
        """An observation this program cannot BIND is one it may not read, and
        that is not the same as a verification that did not happen."""
        self.configured_task = None
        held = self.observed()
        self.assertEqual(held["verification"],
                         baseline.VERIFICATION_UNREPORTED)
        self.assertNotEqual(held["verification"],
                            baseline.VERIFICATION_NOT_RUN)
        self.assertNotEqual(held["verification"],
                            baseline.VERIFICATION_PASSED)

    def test_a_task_document_that_IS_NOT_THERE_leaves_it_unreported(self):
        self.configured_task = os.path.join(self.home, "never-written.json")
        self.assertEqual(self.observed()["verification"],
                         baseline.VERIFICATION_UNREPORTED)

    def test_a_document_WIDER_than_the_consumers_ceiling_is_unreported(self):
        """`claude_agent._read_task` stops at `MAX_TASK_BYTES`, so a wider
        document is not the document any turn consumed -- and truncating it
        into an expectation would produce one nothing can ever match."""
        held = dict(json.loads(self.task_bytes.decode("utf-8")))
        held["instructions"] = "x" * baseline.MAX_TASK_BYTES
        self.wrote(self.task_place, json.dumps(held, sort_keys=True))
        self.assertGreater(os.path.getsize(self.task_place),
                           baseline.MAX_TASK_BYTES)
        self.assertEqual(self.observed()["verification"],
                         baseline.VERIFICATION_UNREPORTED)

    def test_a_deployment_configuring_NO_PRODUCER_is_unreported(self):
        """The bound task is derived from exactly one producer's document; a
        deployment that names none leaves nothing to bind against."""
        self.producers = 0
        self.assertEqual(self.observed()["verification"],
                         baseline.VERIFICATION_UNREPORTED)

    def test_a_deployment_configuring_TWO_PRODUCERS_is_unreported(self):
        """And two is ambiguous rather than "pick the first": the observation
        would be bound to whichever document this program happened to read."""
        self.producers = 2
        self.assertEqual(self.observed()["verification"],
                         baseline.VERIFICATION_UNREPORTED)

    def test_an_unresolved_task_does_not_lose_the_candidate(self):
        """The collector exists to report what a failed run retained, so an
        unreadable expectation must not take the record down with it."""
        self.configured_task = None
        held = self.observed()
        self.assertEqual(held["state"], baseline.CANDIDATE_VALID)
        self.assertEqual(held["locator"], f"file://{self.place}")
        self.assertEqual(self.shortfalls, [])


class AFailedTurnWithoutOne(Collector):

    def test_a_turn_that_FROZE_NOTHING_is_absent_and_says_so(self):
        """Absence is an ANSWER and the ordinary shape of a failure."""
        self.frozen = None
        held = self.one()
        self.assertEqual(held["state"], baseline.CANDIDATE_ABSENT)
        self.assertEqual(held["acceptance"], baseline.ACCEPTANCE_NO_CANDIDATE)
        self.assertEqual(held["verification"], baseline.VERIFICATION_NOT_RUN)
        self.assertIn("froze no result", held["why"])
        self.assertEqual(self.shortfalls, [])

    def test_a_turn_that_declared_no_candidate_is_absent(self):
        self.manifest = self.sealed(outputs=[])
        self.frozen["artifacts"] = []
        held = self.one()
        self.assertEqual(held["state"], baseline.CANDIDATE_ABSENT)
        self.assertEqual(held["acceptance"], baseline.ACCEPTANCE_NO_CANDIDATE)
        self.assertEqual(self.shortfalls, [])

    def test_a_MISSING_OPTIONAL_output_with_no_indexed_row_is_absent(self):
        self.manifest = self.sealed(
            outputs=[self.output(status="missing-optional", artifact=False)])
        self.frozen["artifacts"] = []
        self.assertEqual(self.one()["state"], baseline.CANDIDATE_ABSENT)


class InvalidCustodyIsRefusedAndNeverCounted(Collector):
    """Evidence that EXISTS and did not survive a check is a much louder fact
    than absence, and must not be quietly dropped either way."""

    def refused(self):
        held = self.one()
        self.assertEqual(held["state"], baseline.CANDIDATE_REFUSED, held)
        self.assertTrue(self.shortfalls)
        self.assertIn("REFUSED retained candidate", self.shortfalls[0])
        return held

    def test_a_DIGEST_disagreement_between_the_two_records_is_refused(self):
        """The worker's seal and the manager's index are two records of one
        artifact; disagreeing means nobody knows which bytes it is."""
        self.frozen["artifacts"] = [
            self.indexed(content_digest="sha256:" + "e" * 64)]
        self.assertIn("content_digest", self.refused()["why"])

    def test_a_SIZE_disagreement_is_refused(self):
        self.frozen["artifacts"] = [self.indexed(bytes=99)]
        self.assertIn("bytes", self.refused()["why"])

    def test_an_ARTIFACT_ID_disagreement_is_refused(self):
        self.frozen["artifacts"] = [
            self.indexed(artifact_id="artifact-" + "f" * 8)]
        self.assertIn("artifact_id", self.refused()["why"])

    def test_a_LOCATOR_disagreement_is_refused(self):
        self.frozen["artifacts"] = [
            self.indexed(locator="file:///elsewhere/proposal")]
        self.assertIn("locator", self.refused()["why"])

    def test_a_SEALED_candidate_the_manager_never_indexed_is_refused(self):
        """Not absence: the worker's account declares bytes that are not in
        the manager's custody."""
        self.frozen["artifacts"] = []
        self.assertIn("not in its custody", self.refused()["why"])

    def test_an_INDEXED_artifact_the_seal_omits_is_refused(self):
        """And the other direction, which is louder still."""
        self.manifest = self.sealed(outputs=[])
        self.assertIn("disagree about whether a candidate exists",
                      self.refused()["why"])

    def test_a_candidate_on_ANOTHER_BASE_is_refused(self):
        self.manifest["outputs"][0]["result_metadata"][
            baseline.CLAIM_NAMESPACE]["base"] = "0" * 40
        self.assertIn("canonical target", self.refused()["why"])

    def test_a_candidate_whose_HEAD_IS_ITS_BASE_is_refused(self):
        self.manifest["outputs"][0]["result_metadata"][
            baseline.CLAIM_NAMESPACE]["head"] = BASE
        self.assertIn("holds no change", self.refused()["why"])

    def test_an_UNSTATED_claim_is_refused_rather_than_guessed(self):
        for claim in (None, {}, {"base": BASE}, {"base": BASE, "head": HEAD},
                      {"base": BASE, "head": HEAD, "transport": ""}):
            with self.subTest(claim=claim):
                self.setUp()
                held = self.output(claim=False)
                if claim is not None:
                    held["result_metadata"] = {
                        baseline.CLAIM_NAMESPACE: claim}
                self.manifest = self.sealed(outputs=[held])
                self.assertIn("no readable", self.refused()["why"])

    def test_an_UNREADABLE_declared_base_refuses_rather_than_passing(self):
        self.declared = None
        self.assertIn("declared base is unreadable", self.refused()["why"])


class ForeignBytesUnderThisTurnsSealAreRefused(Collector):
    """The ownership gate, still able to FAIL on a real answer.

    This is the gate the earlier fixture tripped on every case, because its
    artifact reference named an invented `artifact-bbbbbbbb` identity. The gate
    is the sealer's own rule and it is kept: the double was corrected, not the
    check relaxed to admit it.
    """

    def test_the_sealers_OWN_reference_is_the_one_this_fixture_offers(self):
        """Asked of `sealing._answered`, so the agreement cannot drift in
        silence the way it just did."""
        from baton_v12.worker_manager import sealing

        answered = sealing._answered(
            baseline.PROPOSAL_OUTPUT, {"type": "git-proposal"}, ATTEMPT,
            self.measured, self.place, {})
        self.assertEqual(answered["artifact"], self.reference())
        self.assertEqual(answered["content_manifest"], self.measured)
        self.assertEqual(answered["name"], baseline.PROPOSAL_OUTPUT)

    def test_an_artifact_id_naming_ANOTHER_ATTEMPT_is_refused(self):
        other = f"attempt-{'b' * 8}:{baseline.PROPOSAL_OUTPUT}"
        self.restated(artifact_id=other)
        said = self.refused_why()
        self.assertIn("not this turn's bytes", said)
        self.assertIn(other, said)

    def test_an_artifact_id_naming_ANOTHER_OUTPUT_is_refused(self):
        self.restated(artifact_id=f"{ATTEMPT}:findings")
        self.assertIn("not this turn's bytes", self.refused_why())

    def test_an_artifact_id_OF_THE_OLD_INVENTED_SHAPE_is_refused(self):
        """The exact double that masked this file, kept as a case so the
        correction cannot be undone by relaxing the rule instead."""
        self.restated(artifact_id="artifact-" + "b" * 8)
        self.assertIn("not this turn's bytes", self.refused_why())


class RetainedCUSTODYIsReadNotInferred(Collector):
    """Review 2026-10-18T08-39-00Z P1, which is the finding that matters most.

    The first correction compared the sealed reference with the manager's
    indexed row and called agreement `valid`. Its own fixture named a locator
    that did not exist and got `valid` with no shortfall: two stored
    descriptions agreeing establishes that nobody disagrees, NOT that the bytes
    are there. So custody is now READ at the supported boundary, and these
    drive what happens when that read fails or disagrees.
    """

    def test_a_candidate_whose_LINE_DOES_NOT_ANSWER_is_not_valid(self):
        """Missing retained history. The metadata still agrees perfectly."""
        self.custody = refusal(
            "this manager holds no line writer for that attempt")
        held = self.one()
        self.assertEqual(held["state"], baseline.CANDIDATE_UNREADABLE)
        self.assertNotEqual(held["state"], baseline.CANDIDATE_VALID)
        self.assertIn("own line did not answer", held["why"])
        self.assertIn("UNREADABLE retained candidate", self.shortfalls[0])

    def test_an_OS_ERROR_reading_the_line_is_unreadable(self):
        self.custody = OSError("the retained workspace is gone")
        self.assertEqual(self.one()["state"], baseline.CANDIDATE_UNREADABLE)

    def test_USEFUL_EVIDENCE_SURVIVES_a_failed_custody_read(self):
        """An operator looking for the bytes needs the locator most when
        something is wrong, so it stays in the record."""
        self.custody = OSError("gone")
        held = self.one()
        self.assertEqual(held["locator"], f"file://{self.place}")
        self.assertEqual(held["head"], HEAD)
        self.assertEqual(held["base"], BASE)
        self.assertEqual(held["content_digest"], self.measured["tree_digest"])
        self.assertIsNotNone(held["assignment"])

    def test_a_SUBSTITUTED_head_is_refused(self):
        """The line answers a different commit than the seal claims."""
        self.custody = dict(self.custody, head="f" * 40)
        held = self.one()
        self.assertEqual(held["state"], baseline.CANDIDATE_REFUSED)
        self.assertIn("answers head", held["why"])

    def test_a_DAMAGED_history_is_refused(self):
        """Parents that are not exactly the declared base: the adapter authors
        one commit per turn, so anything else is a history it did not write."""
        self.custody = dict(self.custody, parents=[BASE, "e" * 40])
        self.assertIn("parents", self.refused_why())

    def test_a_candidate_the_ADAPTER_DID_NOT_AUTHOR_is_refused(self):
        """W236087's live failure: the provider committed its own work."""
        self.custody = dict(self.custody,
                            author="Somebody Else <nobody@example.invalid>",
                            committer="Somebody Else <nobody@example.invalid>")
        self.assertIn("attributed to", self.refused_why())

    def test_a_split_AUTHOR_and_COMMITTER_is_refused(self):
        self.custody = dict(self.custody,
                            committer="Other <other@example.invalid>")
        self.assertIn("committed by", self.refused_why())

    def test_a_valid_candidate_carries_its_WHOLE_attribution(self):
        """Review P1: the record named only the generation, so it could not say
        which authority, Work or participant the bytes belong to."""
        held = self.one()
        self.assertEqual(held["state"], baseline.CANDIDATE_VALID)
        self.assertEqual(held["assignment"]["authority_uuid"], "0" * 32)
        self.assertEqual(held["assignment"]["work_id"], "00000000-W1")
        self.assertEqual(held["assignment"]["participant"], "baton.impl")
        self.assertEqual(held["assignment"]["principal"],
                         "principal:baton.impl")
        self.assertEqual(held["assignment"]["effective_scope"],
                         "scope:deployment")
        self.assertEqual(held["assignment"]["generation"], 1)
        self.assertEqual(held["attribution"]["head"], HEAD)


class RetainedBYTESAreMeasuredNotDescribed(Collector):
    """Review 2026-10-18T10-07-00Z, at the NORMAL boundary over REAL bytes.

    Everything above this is two stored descriptions agreeing, plus a commit
    header in a repository that is NOT the artifact. An artifact that was
    never written, was truncated, had one byte changed or was swapped for a
    different tree satisfies all of it -- and the previous fixture could not
    tell any of those apart, because its sealed `content_manifest` was `null`
    and its locator named a file that never existed.

    So these run `workspaces.directory_manifest` over a real disposable tree
    and drive all five outcomes: bytes that re-measure, bytes that are gone,
    bytes that were edited, bytes that were replaced, and bytes this process
    could not read.
    """

    def test_bytes_that_RE_MEASURE_to_the_seal_are_valid(self):
        held = self.one()
        self.assertEqual(held["state"], baseline.CANDIDATE_VALID)
        # AND THE MEASUREMENT REALLY RAN: the digest in the record is the one
        # the owner's walker answers for the tree on disk right now.
        self.assertEqual(
            held["content_digest"],
            workspaces.directory_manifest(self.place)["tree_digest"])
        self.assertEqual(self.shortfalls, [])

    def test_MISSING_bytes_are_refused_and_never_called_absent(self):
        """The seal declares retained bytes and there is nothing there: two
        accounts disagreeing, not a read that failed and not an absence."""
        shutil.rmtree(self.place)
        held = self.one()
        self.assertEqual(held["state"], baseline.CANDIDATE_REFUSED)
        self.assertNotEqual(held["state"], baseline.CANDIDATE_ABSENT)
        self.assertIn("no retained tree there", held["why"])
        self.assertIn(self.place, held["why"])

    def test_DAMAGED_bytes_are_refused_and_the_FILE_is_named(self):
        """One byte changed under a seal that still agrees with itself. A tree
        digest answers "not the same bytes"; the record says which file."""
        self.wrote(os.path.join(self.place, "result.json"),
                   '{"schema": "baton.dogfood-proposal/2", "edited": 1}\n')
        said = self.refused_why()
        self.assertIn("1 changed", said)
        self.assertIn("result.json", said)

    def test_TRUNCATED_bytes_are_refused(self):
        self.wrote(os.path.join(self.place, "objects.bundle"), "")
        said = self.refused_why()
        self.assertIn("1 changed", said)
        self.assertIn("objects.bundle", said)

    def test_SUBSTITUTED_bytes_are_refused_with_the_shape_of_the_swap(self):
        """A different tree entirely at the same locator."""
        for name in sorted(os.listdir(self.place)):
            os.unlink(os.path.join(self.place, name))
        self.wrote(os.path.join(self.place, "somebody-elses.txt"), "other\n")
        said = self.refused_why()
        self.assertIn(f"{len(RETAINED)} absent", said)
        self.assertIn("1 unexpected", said)

    def test_UNREADABLE_bytes_are_unreadable_and_NEVER_absence(self):
        """The tree is there and this process cannot walk it. Conflating that
        with absence is the exact error this Work exists to close.

        W325711 review: the denial is staged through `denied`, which PROVES
        the kernel refused this process before anything below is asserted. It
        previously chmod'd and read on, so a privileged run would have passed
        it over a walk that succeeded -- and restored mode `0o755` rather
        than the mode the directory actually had.
        """
        self.denied(self.place, lambda: os.listdir(self.place))
        self.assertIn("could not be measured", self.unreadable_why())

    def test_a_seal_DECLARING_NO_MANIFEST_has_nothing_to_be_measured(self):
        self.manifest = self.sealed(
            outputs=[self.output(content_manifest=None)])
        self.assertIn("declares no content manifest", self.refused_why())

    def test_a_DECLARATION_that_does_not_describe_itself_is_refused(self):
        """Held to §12 rule 6 by its own owner BEFORE it is used as an
        expectation: a manifest that miscounts itself can neither convict nor
        acquit a tree."""
        self.manifest = self.sealed(outputs=[self.output(
            content_manifest=dict(self.measured, entry_count=99))])
        self.assertIn("content manifest is not one its own contract admits",
                      self.refused_why())

    def test_a_seal_that_DISAGREES_WITH_ITS_OWN_MANIFEST_about_the_digest(
            self):
        """Refused before any tree is opened: there is no measurement that
        could settle which of its own two numbers the seal meant."""
        self.restated(content_digest="sha256:" + "0" * 64)
        self.assertIn("content manifest measures to", self.refused_why())

    def test_a_seal_that_DISAGREES_WITH_ITS_OWN_MANIFEST_about_the_width(self):
        self.restated(bytes=self.measured["total_bytes"] + 1)
        self.assertIn("content manifest totals", self.refused_why())

    def test_a_locator_THIS_CONTRACT_DOES_NOT_ADMIT_is_refused(self):
        """The grammar is `check_uri`'s, and the old fixture's single-slash
        `file:/...` form is one it refuses -- which is the whole reason the
        locator may not be resolved by this program's own parsing."""
        self.restated(locator="file:/retained/proposal.bundle")
        self.assertIn("not one this contract admits", self.refused_why())

    def test_a_locator_NAMING_ANOTHER_SCHEME_is_refused(self):
        """Evidence about bytes this process cannot measure, and reporting a
        measurement it did not make is the class of error being closed."""
        self.restated(locator="https://store.invalid/proposal")
        self.assertIn("scheme", self.refused_why())

    def test_a_locator_NAMING_A_REMOTE_HOST_is_refused(self):
        """And it is `check_uri` that refuses it, which is the point: the
        grammar has one owner and this program resolves nothing that owner
        has not admitted."""
        self.restated(locator="file://store.invalid/retained/proposal")
        self.assertIn("not one this contract admits", self.refused_why())

    def test_a_locator_NAMING_A_FILE_rather_than_a_tree_is_refused(self):
        place = os.path.join(self.home, "proposal.bundle")
        self.wrote(place, "PACK\x00\n")
        self.restated(locator=f"file://{place}")
        self.assertIn("no retained tree there", self.refused_why())

    def test_REFUSED_bytes_keep_the_locator_an_operator_needs(self):
        shutil.rmtree(self.place)
        held = self.one()
        self.assertEqual(held["state"], baseline.CANDIDATE_REFUSED)
        self.assertEqual(held["locator"], f"file://{self.place}")
        self.assertEqual(held["head"], HEAD)
        self.assertIsNotNone(held["attribution"])
        self.assertIsNotNone(held["assignment"])


class TheMeasurementIsOutsideEveryStoreRead(Collector):
    """DESIGN DB-1, at the part of it this seam can actually observe.

    `_retained_bytes` opens a directory and reads every file under it, and
    DB-1 names traversal, `open` and hashing as external I/O that MUST occur
    after transaction exit -- read transactions included. The collector's
    docstrings say the measurement is outside every store read "by
    construction"; what can be driven here is the construction itself, which
    is that each store read and the durable line's read has ANSWERED before
    the first byte of the retained tree is opened.
    """

    def test_every_store_read_answers_before_the_bytes_are_measured(self):
        seen = []

        def measuring(reference, declared):
            seen.append(tuple(self.order))
            return baseline._retained_bytes(reference, declared)

        found = self.collected(measure=measuring)
        self.assertEqual(found[0]["state"], baseline.CANDIDATE_VALID)
        self.assertEqual(seen, [("frozen", "manifest", "assignment", "line")])

    def test_the_default_measure_is_the_collectors_own(self):
        """And `measure` is a seam for this case rather than the way these
        cases reach the measurement: everything else here runs the real one."""
        self.assertEqual(baseline._candidates.__kwdefaults__,
                         {"inspect": None, "measure": None})
        self.assertEqual(self.one()["state"], baseline.CANDIDATE_VALID)


class AnUnreadableReadIsNeverReportedAsAbsence(Collector):
    """The conflation that produced the original false report."""

    def unreadable(self):
        held = self.one()
        self.assertEqual(held["state"], baseline.CANDIDATE_UNREADABLE, held)
        self.assertNotEqual(held["state"], baseline.CANDIDATE_ABSENT)
        self.assertTrue(self.shortfalls)
        self.assertIn("UNREADABLE retained candidate", self.shortfalls[0])
        return held

    def test_a_frozen_result_that_does_not_read_is_unreadable(self):
        self.frozen = refusal("the output table did not answer")
        said = self.unreadable()
        self.assertIn("did not read", said["why"])
        self.assertIn("not evidence", self.shortfalls[0])

    def test_a_manifest_that_does_not_read_is_unreadable(self):
        self.manifest = refusal("the manifest digest did not recompute")
        self.assertIn("did not read", self.unreadable()["why"])

    def test_a_manifest_this_store_DOES_NOT_HOLD_is_unreadable(self):
        self.manifest = None
        self.assertIn("does not hold", self.unreadable()["why"])

    def test_an_unreadable_ASSIGNMENT_is_unreadable_not_valid(self):
        """The candidate cannot be bound to the attempt that produced it."""
        self.assignment = KeyError("generation")
        self.assertIn("assignment did not read", self.unreadable()["why"])

    def test_an_unreadable_candidate_carries_no_acceptance_claim(self):
        self.frozen = TypeError("row shape")
        self.assertEqual(self.unreadable()["acceptance"],
                         baseline.ACCEPTANCE_UNOBSERVED)


class ADeniedLOOKUPIsUnreadableAndNotAFalseAbsence(Collector):
    """W325711 review, over the REAL filesystem: the defect one line earlier.

    `AnUnreadableReadIsNeverReportedAsAbsence` above drives the store reads
    that do not answer, and `RetainedBYTESAreMeasuredNotDescribed` drives a
    MEASUREMENT that does not answer. Between them sat the lookup that decides
    whether there is anything to measure at all, and it was
    `os.path.isdir(place)` -- one boolean over `os.stat` that swallows every
    OSError on the way to it.

    So a retained tree that was perfectly intact under an ancestor directory
    this process could not traverse was reported as

        "this process finds no retained tree there, so the bytes it declares
        are not where it says they are"

    which is the false absence claim this entire Work exists to close, stated
    by the very function that closes it, with a seal and a custody line that
    both agreed the bytes were written. An operator reading that sentence
    would go looking for a worker that lost its candidate instead of for the
    mode bits on one directory.

    These stage the denial with real `chmod` on real directories and real
    files, PROVE the kernel refused this process (`Collector.denied`), and
    hold the three decisions apart: a lookup that was denied is `unreadable`,
    a lookup that ANSWERED "nothing is there" stays `refused`, and neither
    sentence is allowed to borrow the other's words.
    """

    def ancestor(self):
        """The custody directory ABOVE the artifact: `.../custody/<attempt>`.

        Denying this leaves the artifact itself untouched -- its bytes, its
        mode and its digest are exactly what the seal declares -- so the only
        thing wrong is this process's path to it. That is the case the
        boolean could not express.
        """
        return os.path.dirname(self.place)

    def test_an_inaccessible_ANCESTOR_is_unreadable_and_never_absence(self):
        self.denied(self.ancestor(), lambda: os.stat(self.place))
        said = self.unreadable_why()
        self.assertIn(self.place, said)
        self.assertIn("may not look", said)
        self.assertIn("UNKNOWN", said)
        # AND NOT IN THE WORDS OF THE FINDING IT IS NOT. These are the two
        # sentences the review found false; neither may appear for a read
        # that never happened.
        self.assertNotIn("no retained tree there", said)
        self.assertNotIn("not where it says they are", said)

    def test_the_denied_record_still_carries_what_an_OPERATOR_acts_on(self):
        """`unreadable` is a finding to be chased, so the record keeps the
        locator to chase, the custody that says whose bytes they would be,
        and the assignment that says which attempt retained them."""
        self.denied(self.ancestor(), lambda: os.stat(self.place))
        held = self.one()
        self.assertEqual(held["state"], baseline.CANDIDATE_UNREADABLE, held)
        self.assertEqual(held["locator"], f"file://{self.place}")
        self.assertEqual(held["head"], HEAD)
        self.assertEqual(held["base"], BASE)
        self.assertEqual(held["transport"], TRANSPORT)
        self.assertEqual(held["attribution"], self.custody)
        self.assertEqual(held["assignment"]["generation"], 1)
        self.assertEqual(held["assignment"]["participant"], "baton.impl")
        # AND IT CLAIMS NOTHING IT DID NOT SEE. No verification was reported
        # and no acceptance was observed; an unreadable candidate is not an
        # accepted one, and bytes nobody could read are not a passing turn.
        self.assertEqual(held["verification"], "unreported")
        self.assertEqual(held["acceptance"], baseline.ACCEPTANCE_UNOBSERVED)

    def test_an_unreadable_FILE_in_the_tree_is_not_reported_as_DAMAGE(self):
        """The lookup and the walk both answer and one file will not open.

        The seal still describes bytes that may be exactly right, so this is
        neither absence nor the "1 changed" finding that `_measured_difference`
        reports for bytes that were actually seen to differ.
        """
        held = os.path.join(self.place, "result.json")
        self.denied(held, lambda: open(held, "rb"))
        said = self.unreadable_why()
        self.assertIn("could not be measured", said)
        self.assertNotIn("changed", said)
        self.assertNotIn("no retained tree there", said)

    def test_a_MISSING_ancestor_is_still_the_loud_absence_it_was(self):
        """The correction may not buy its honesty by softening the finding an
        operator most needs: ENOENT through a parent that is gone is the
        filesystem ANSWERING, and it stays `refused`."""
        shutil.rmtree(self.ancestor())
        said = self.refused_why()
        self.assertIn("no retained tree there", said)
        self.assertIn("not where it says they are", said)

    def test_a_NON_DIRECTORY_component_above_the_locator_is_refused(self):
        """ENOTDIR is an answer too, and a different one from both: there is
        a file where a directory would have to be."""
        place = os.path.join(self.home, "proposal.bundle")
        self.wrote(place, "PACK\x00\n")
        self.restated(locator=f"file://{place}/proposal")
        said = self.refused_why()
        self.assertIn("is not a directory", said)
        self.assertIn("no retained tree there", said)

    def test_the_decision_is_NOT_a_BOOLEAN_THAT_SWALLOWS_the_errno(self):
        """The one case here that still holds when a privileged run skips the
        rest.

        `Collector.denied` skips where mode bits do not deny this process,
        and a regression that reinstated the boolean would then be observed
        by nothing at all. `os.path.isdir` cannot tell apart the two findings
        this function's own docstring promises are different, so its absence
        is the invariant.

        ASSERTED OVER THE COMPILED NAMES rather than the source text, because
        the source text NAMES it -- the comment above the lookup exists to
        say why it is not used, and a test that forbade the word would forbid
        the explanation with it.
        """
        import inspect

        names = baseline._retained_bytes.__code__.co_names
        self.assertNotIn("isdir", names)
        self.assertIn("stat", names)
        self.assertIn("S_ISDIR", names)
        # And the errno-bearing clauses, each resolving to the answer it owns.
        said = inspect.getsource(baseline._retained_bytes)
        for clause in ("except FileNotFoundError", "except NotADirectoryError",
                       "except PermissionError", "except OSError"):
            self.assertIn(clause, said)


class EveryRecordCarriesTheSameMEMBERS(Collector):
    """A reader iterating the records must not have to ask which shape it got.

    The four states are different ANSWERS, not different documents: an
    operator scanning for a locator or an attribution cannot be expected to
    know that a record which failed early is missing a member a record that
    failed late carries.
    """

    MEMBERS = ("acceptance", "assignment", "attribution", "attempt_id",
               "base", "bytes", "content_digest", "disposition", "generation",
               "head", "locator", "state", "transport", "verification", "why")

    def driven(self):
        """One record of each state, from this fixture's own operands."""
        found = {}
        for state, arrange in (
                (baseline.CANDIDATE_VALID, lambda: None),
                (baseline.CANDIDATE_ABSENT,
                 lambda: setattr(self, "frozen", None)),
                (baseline.CANDIDATE_REFUSED,
                 lambda: shutil.rmtree(self.place)),
                (baseline.CANDIDATE_UNREADABLE,
                 lambda: setattr(self, "custody", OSError("gone")))):
            self.setUp()
            arrange()
            held = self.one()
            self.assertEqual(held["state"], state, held)
            found[state] = held
        return found

    def test_every_state_answers_the_same_closed_member_set(self):
        for state, held in self.driven().items():
            with self.subTest(state=state):
                self.assertEqual(sorted(held), sorted(self.MEMBERS))


class TheCollectorSurvivesWhatItExistsToReport(Collector):
    """It reports what a FAILED run retained, so it may not fail on the way.

    `_candidates` already takes this care with the deployment configuration
    and the bound task, catching wider than one refusal because "a collector
    whose purpose is reporting what survived a FAILED run must not itself die
    on an unreadable config and lose the candidate it exists to name". The
    manager's indexed row is read with the same exposure and deserves it.
    """

    def test_a_SHORT_indexed_row_is_refused_rather_than_raising(self):
        held = self.indexed()
        held.pop("locator")
        self.frozen["artifacts"] = [held]
        said = self.refused_why()
        self.assertIn("locator", said)

    def test_an_indexed_row_that_is_NOT_A_DOCUMENT_does_not_kill_the_run(self):
        self.frozen["artifacts"] = [{"output_name": baseline.PROPOSAL_OUTPUT}]
        self.assertNotEqual(self.one()["state"], baseline.CANDIDATE_VALID)
        self.assertTrue(self.shortfalls)


class TheAbsenceMessagesNoLongerContradictTheRecord(unittest.TestCase):
    """The two sentences the review found false, corrected in place."""

    def test_the_noncompleted_message_points_at_the_candidate_question(self):
        import inspect

        said = inspect.getsource(baseline._proposals)
        self.assertIn("`candidates` answers it", said)

    def test_the_no_proposal_message_no_longer_claims_nothing_was_retained(
            self):
        import inspect

        said = inspect.getsource(baseline._proposals)
        self.assertNotIn("retained no proposal at all", said)
        self.assertIn("published no proposal at all", said)
        # Split across two source lines; both halves are asserted so the
        # sentence cannot lose the distinction it exists to draw.
        self.assertIn("a retained candidate is not a", said)
        self.assertIn("published proposal, a verification or an acceptance",
                      said)


if __name__ == "__main__":
    unittest.main()
