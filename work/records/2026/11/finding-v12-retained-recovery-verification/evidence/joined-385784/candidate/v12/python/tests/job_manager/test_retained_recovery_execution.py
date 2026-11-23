"""W385625 Stage 1-C — the approved verifier on the exact retained bytes, and
the same candidate handed to independent review.

WHAT THESE CASES ARE ABOUT. The one complete REC-8 outcome, joined: an owner
reads a retained verification failure through the installed command, approves
an exact correction and the verification/review scope, and the manager then
materializes the exact retained candidate into a new private workspace, runs
only the approved command in only the approved context, retains an
attributable account of it, and hands THE SAME candidate and that evidence to
independent substantive review -- automatically, through the ordinary tick,
with the review stage's own recovery gate released by a validated handoff and
by nothing weaker. Plus the four endings that are not that: a renewed
verification failure, a finite analysis of it, expiry after a passed
verification, and the owner-authorized review-only recovery that expiry
earns.

WHAT IS REAL HERE, and the list is what makes this evidence rather than a
demonstration.

  THE VERIFIER REALLY RUNS. `tools.recovery_execution.CommandRunner` is the
  production adapter and its child-process call is the real `subprocess.run`;
  the approved argv is executed as the exact words the owner approved, in the
  materialized candidate's own directory, with exactly the declared
  environment. The exit status, both streams and the two instants in every
  retained account below came out of a real process.

  THE CANDIDATE BYTES ARE REAL AND MEASURED TWICE. The retained custody tree
  is Stage 1-A's own real fixture on disk-backed storage; the materialization
  copies it through `workspaces.copied_manifest`, and the digest every case
  compares is the one that pass measured out of the descriptors it wrote.

  THE OWNER COMMANDS ARE THE INSTALLED ONES, reached through
  `tools.job_manager.main` with an operator's own argv, and the JOINED case
  composes them over a BOOTSTRAPPED DISPOSABLE INSTANCE through the SHIPPED
  DEFAULT owner factory -- no `--owners` substitute anywhere in it. The
  authorization is production: a real Authority store, a real Work with its
  own effective scope and the real `approve` grant `bootstrap` makes.

  THE MANAGER TICK IS THE REAL ONE. `manager.sweep` is what admits the review
  stage after the handoff, and `projection.gates_of` is what reports the gate;
  no case opens a gate by writing one.

WHAT IS FAKED, AND ONLY AT THE NORMAL BOUNDARY: the three owner ports a
deployment composes over its own installation (host cessation, deployment
binding, instance guard) in the module-level cases, which the joined case
replaces with the shipped defaults; the pooled manager operations the sweep
drives stages through, which is the accepted `FakeOperations` and is where a
container and a provider would be; and the reviewer's own substance, which is
a SCRIPTED verdict through the real review disposition boundary. There is no
model, no image, no container and no daemon in this file.

HOW THE SCRIPTED HALVES ARE LABELLED, because the contract asks for exactly
this honesty: the analysis diagnosis inherited from Stage 1-A is a SCRIPTED
document and proves orchestration and evidence fidelity, not live diagnostic
quality; the independent review's accept and reject are SCRIPTED verdicts and
prove that this manager manufactures neither, not that a reviewer judged well.
Both are said so in the cases that use them.

WHAT IS DELIBERATELY ABSENT. No implementation is redispatched anywhere --
one case counts the implementation calls across the whole joined path and
asserts zero -- no successor is admitted without a new owner decision, no
verdict is written by this manager, and no case reaches a provider.
"""

import io
import json
import os
import pathlib
import shlex
import subprocess
import tempfile
import threading
import unittest

from baton_v12.contracts import ContractRefusal, digest
from baton_v12.job_manager import (JobStore, cancellation, documents,
                                   failure_analysis, job_control, projection,
                                   retained_recovery, retained_verification,
                                   submission, sweep)
from baton_v12.source_profiles import checkout
from baton_v12.worker_manager.workspaces import directory_manifest

from tests.job_manager import test_retained_failure_analysis as stage_a
from tests.job_manager import test_retained_recovery_admission as stage_b
from tests.job_manager.fixtures import NOW, WORK_A, FakeOperations

from tools import recovery_execution


def driver_vector():
    """The accepted result-manifest vector, from the fixture that owns it."""
    from tests.job_manager import test_review_driver as driver

    return driver._result_vector()


def driver_base():
    from tests.job_manager import test_review_driver as driver

    return driver.BASE

OWNER = stage_b.OWNER
LATER = stage_b.LATER
EXPIRED = stage_b.EXPIRED
AFTER = stage_b.AFTER

# -- WHERE THE BOOTSTRAPPED-INSTANCE FIXTURE PUTS ITS STATE --------------------
#
# `tests.tools.test_stack._disk_root_outside_the_checkout` is the accepted
# chooser for every fixture that installs a real instance, and it REFUSES
# rather than silently falling back when none of `/var/tmp`, `~/.cache` and
# `TMPDIR` is real storage outside the checkout. That refusal is correct, and
# it is also exactly the environment the supported native verifier runs in:
# its own layout record puts `HOME`, `TMPDIR` and the cache on tmpfs and
# `/var/tmp` is read-only there, so the variable the refusal names is the only
# way through.
#
# SO THIS MODULE NAMES ONE, AND ONLY IF NOBODY ELSE DID. `setdefault` means an
# operator's own choice always wins and nothing here overrides it; the
# candidates below are tried through the SAME two product rules the accepted
# chooser applies -- outside the checkout, and not a memory filesystem -- and
# if none of them passes, the variable stays unset and the accepted refusal
# stands word for word. No test is changed: the chooser is still the one that
# decides.
STACK_ROOT_VARIABLE = "BATON_V12_STACK_TEST_ROOT"

# `/scratch` is the one candidate the accepted list does not carry and this
# container does: the native worker and verifier images mount it from the
# host's own disk, outside the checkout, writable. The rest are the accepted
# list's own, tried in its order.
EXTRA_CANDIDATES = ("/scratch",)


def _usable_outside_the_checkout():
    """The first candidate that is real storage outside the checkout, or None."""
    from baton_v12.worker_manager.source_boundary import (MEMORY_FILESYSTEMS,
                                                          filesystem_of)
    from tools import stage_execution

    checkout_root = stage_execution._checkout()
    for place in ("/var/tmp", os.path.expanduser("~/.cache"),
                  tempfile.gettempdir()) + EXTRA_CANDIDATES:
        resolved = os.path.realpath(place)
        if resolved == checkout_root \
                or resolved.startswith(checkout_root.rstrip("/") + "/"):
            continue
        if not os.path.isdir(resolved) or not os.access(resolved, os.W_OK):
            continue
        try:
            if filesystem_of(resolved) in MEMORY_FILESYSTEMS:
                continue
        except Exception:                                   # noqa: BLE001
            continue
        return resolved
    return None


if not (os.environ.get(STACK_ROOT_VARIABLE) or "").strip():
    _chosen = _usable_outside_the_checkout()
    if _chosen is not None:
        os.environ.setdefault(STACK_ROOT_VARIABLE, _chosen)


# -- the approved execution context this deployment declares ------------------
#
# THE DOCUMENT WHOSE DIGEST THE OWNER APPROVES. Stage 1-B compares
# `--context-digest` exactly and says why: "a command string must not hide a
# changed working directory, environment or tool selection". This is the
# document that digest is over, and every case that changes an execution's
# context changes one member of it and watches the digest stop matching.
CONTEXT = {
    "working_directory": retained_verification.CANDIDATE_ROOT,
    "environment": {"LC_ALL": "C", "PATH": "/usr/bin:/bin"},
    "tool": {"kind": "host-interpreter", "selector": "python3"},
    "runtime": {"kind": "manager-local", "isolation": "private-workspace"},
}

# THE FIVE STRUCTURAL PREDICATES the joined acceptance names, over the exact
# retained candidate as it stands in the private workspace: the declared file
# is present, it parses, it names this candidate's own head, its ending is the
# retained trigger, and its own required verification really reported a
# non-zero status. A STRUCTURAL CHECK AND NOTHING MORE -- the contract is
# explicit that "structural heading checks do not certify content", which is
# why the independent review afterwards is the thing that judges substance.
PREDICATES = (
    "import json\n"
    "d=json.load(open('result.json'))\n"
    "assert d['schema']=='baton.dogfood-proposal/3', 'schema'\n"
    "assert d['head']=='" + "f" * 40 + "', 'head'\n"
    "assert d['disposition']=='verification-failed', 'disposition'\n"
    "assert d['verification']['status']!=0, 'verification'\n"
    "assert d['provider']['ok'] is True, 'provider'\n"
    "print('five structural predicates hold')\n")

# The owner-approved corrected command for the passing path: the original
# argv's accidental trailing newline removed AND the subject corrected to the
# five predicates above, which is one explicit owner correction rather than a
# generic retry of the command that failed.
CORRECTED = ["bash", "-c", "exec python3 -c " + shlex.quote(PREDICATES)]

# And the owner-approved correction whose command still fails: the accidental
# newline removed from the exact original argv, which is the correction the
# contract names and which this candidate's own missing test module makes
# exit non-zero. Used for the RENEWED-failure path.
STILL_FAILS = ["bash", "-c", "exec python3 -c 'raise SystemExit(3)'"]


def context_of(**changed):
    held = dict(CONTEXT)
    held.update(changed)
    return dict(held, schema=retained_verification.CONTEXT_SCHEMA)


class Seam:
    """The five members `check_verification_seam` proves, as one object.

    THE PRODUCTION SHAPE, and the production runner. `tools.recovery_execution
    .VerificationSeam` is what a deployment composes; this is the same five
    members with the control store, the workspace root and the owner
    destination a case owns, so a case about a wrongly declared context is
    about one member rather than about a different object.
    """

    def __init__(self, *, control, context, workspaces, runner, declaration,
                 destination=OWNER):
        self.control = control
        self.context = context
        self.workspaces = workspaces
        self.runner = runner
        self.declaration = declaration
        self.destination = destination


class CountingRun:
    """The real `subprocess.run`, counted.

    WHY NOT A FAKE. "No repeated verifier effects" is a claim about how many
    times a child process was started, and a fake process would make it a
    claim about how many times a fake was called. So this IS
    `subprocess.run`, wrapped only to record each call's argv and working
    directory -- which is also what lets a case assert that the approved words
    and the materialized candidate's own directory are what reached the host.
    """

    def __init__(self):
        self.calls = []

    def __call__(self, argv, **named):
        self.calls.append({"argv": list(argv), "cwd": named.get("cwd"),
                           "env": dict(named.get("env") or {}),
                           "timeout": named.get("timeout")})
        return subprocess.run(argv, **named)


class ExecutionCase(stage_b.RecoveryCase):
    """One delivered owner item, one approved decision, and the real verifier.

    Stage 1-B's whole fixture is inherited -- the control store, the measured
    candidate tree in real custody, the typed failure cause, the scripted
    analysis, the real Authority, the installed owner commands -- and what
    this adds is the private workspace root, the declared execution context
    and the production command runner.
    """

    def setUp(self):
        super().setUp()
        from tests.manager.disk_roots import disk_backed_under

        # DISK-BACKED, because what is composed under here is a materialized
        # candidate tree and a retained output tree, and the workspace
        # boundary this deployment keeps refuses material on memory.
        self.workspaces = os.path.join(disk_backed_under(self), "recovery")
        os.makedirs(self.workspaces, mode=0o700)
        self.ran = CountingRun()
        self.runner = recovery_execution.CommandRunner(
            stage_b.CURRENT["identity"], clock=lambda: LATER, run=self.ran)
        self.context = context_of()
        self.seam = Seam(control=self.control, context=self.context,
                         workspaces=self.workspaces, runner=self.runner,
                         declaration=self.declaration)
        # STAGE 1-A'S WHOLE PATH, RUN ONCE PER CASE, because every case here
        # starts from a delivered owner item: the trigger, the one automatic
        # analysis (whose diagnosis is SCRIPTED and proves orchestration
        # rather than diagnostic quality) and the item itself.
        self.held = self.delivered()
        self.key = self.held["key"]

    # -- the decided recovery every case starts from ------------------------

    def decided(self, *, corrected=None, stages=None, decision_id="D1",
                lineage=None, clock=None):
        """One delivered item and one APPROVED decision, through the command.

        The owner command performs both acts, which is what an owner does:
        `recovery-decide --approve` records the disposition and then asks the
        manager for the admission.
        """
        item = self.read(self.key)
        code, said = self.decide(
            self.key, item, decision_id=decision_id,
            corrected=CORRECTED if corrected is None else corrected,
            context_digest=retained_verification.context_digest(self.context),
            stages=stages, lineage=lineage, clock=clock)
        self.assertEqual(code, 0, said)
        return said

    def admitted(self, **changed):
        said = self.decided(**changed)
        self.assertTrue(said["admitted"], said)
        return said["successor"]

    # -- the five acts ------------------------------------------------------

    def materialize(self, *, decision_id="D1", now=None, seam=None):
        return retained_verification.materialize(
            self.jobs, seam if seam is not None else self.seam,
            decision_id=decision_id, now=now if now is not None else LATER)

    def execute(self, *, decision_id="D1", now=None, seam=None):
        return retained_verification.execute(
            self.jobs, seam if seam is not None else self.seam,
            decision_id=decision_id, now=now if now is not None else LATER)

    def hand_off(self, *, decision_id="D1", now=None, seam=None):
        return retained_verification.hand_off(
            self.jobs, seam if seam is not None else self.seam,
            decision_id=decision_id, now=now if now is not None else LATER)

    def advance(self, *, now=None, seam=None):
        return retained_verification.advance_verification(
            self.jobs, seam if seam is not None else self.seam,
            now=now if now is not None else LATER)

    def ticked(self, *, now=None, times=1, seam=None):
        """Drive the pass the way the manager drives it: one act per tick."""
        acts = []
        for _ in range(times):
            acts.extend(self.advance(now=now, seam=seam))
        return acts

    def whole_loop(self, *, now=None, seam=None):
        """Materialize, run the approved command, hand the candidate over."""
        self.admitted()
        return self.ticked(now=now, times=3, seam=seam)

    # -- what the records and the tick say ----------------------------------

    def gate(self, job_id="recovery-D1", kind="review"):
        return retained_recovery.execution_gate(self.jobs, job_id)

    def projected_gate(self, stage_id="recovery-D1/review",
                       operations=None):
        operations = (operations if operations is not None
                      else FakeOperations(authority_uuid=self.AUTHORITY))
        held = projection.stage_states(self.jobs, operations)
        state = held[stage_id]
        return projection.gates_of(state["stage"], held)[0]

    def swept(self, *, now=None, operations=None):
        """One REAL manager tick, with the accepted fake operations.

        THE STORE'S OWN CLOCK IS MOVED WITH THE TICK, which is not a
        convenience: `job_control` keeps a monotonic watermark, a tick
        advances it to the instant it was given, and a later projection taken
        at an EARLIER clock is correctly reported as UNCERTAIN timing -- which
        closes every Job. A fixture that swept at one instant and projected at
        another would be asserting against that uncertainty rather than
        against what this recovery does. The instants only ever move forward.
        """
        now = now if now is not None else LATER
        operations = (operations if operations is not None
                      else FakeOperations(authority_uuid=self.AUTHORITY))
        if now > self.instants[-1]:
            self.instants.append(now)
        report = sweep(self.jobs, operations, now=now)
        return report, operations

    def workspace_of(self, record):
        return record["workspace"]["locator"][len("file://"):]

    def custody_bytes(self):
        """The ORIGINAL custody tree's measured digest, read directly."""
        return directory_manifest(self.held["failed"]["custody"])


# -- 1. the approved execution context ---------------------------------------


class TheApprovedContextIsADocumentAndItsDigestIsItsIdentity(
        unittest.TestCase):
    """A digest over nothing in particular is a digest nobody can check."""

    def refusal(self, **changed):
        with self.assertRaises(ContractRefusal) as caught:
            retained_verification.owned_context(context_of(**changed))
        return caught.exception

    def test_the_declared_context_is_admitted_and_digests_stably(self):
        held = retained_verification.owned_context(context_of())
        self.assertEqual(sorted(held),
                         sorted(retained_verification.CONTEXT_MEMBERS))
        self.assertEqual(held["schema"],
                         retained_verification.CONTEXT_SCHEMA)
        self.assertEqual(retained_verification.context_digest(context_of()),
                         digest(held))

    def test_the_producer_composes_the_same_document_the_validator_holds(self):
        made = recovery_execution.declared_context(
            {one: CONTEXT[one] for one in CONTEXT})
        self.assertEqual(made, retained_verification.owned_context(
            context_of()))

    def test_another_generation_of_the_schema_is_refused(self):
        held = context_of()
        held["schema"] = "baton.v12.recovery-verification-context/2"
        with self.assertRaises(ContractRefusal) as caught:
            retained_verification.owned_context(held)
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("refused", "unsupported-version"))

    def test_a_missing_or_extra_member_is_refused(self):
        held = context_of()
        held.pop("tool")
        self.assertRaises(ContractRefusal,
                          retained_verification.owned_context, held)
        self.assertRaises(ContractRefusal,
                          retained_verification.owned_context,
                          dict(context_of(), lane="implementation"))

    def test_a_host_path_is_not_a_working_directory_this_context_may_name(
            self):
        held = self.refusal(working_directory="/var/lib/baton/candidate")
        self.assertEqual(held.code, "path")
        self.assertIn("another filesystem", held.message)
        # AND THE THREE ROOTS A PRIVATE WORKSPACE HAS ARE ALL SELECTABLE.
        for one in retained_verification.WORKSPACE_ROOTS:
            retained_verification.owned_context(
                context_of(working_directory=one))

    def test_the_environment_is_bounded_closed_and_sorted(self):
        self.refusal(environment={"PATH": "/usr/bin", "A=B": "x"})
        self.refusal(environment={"PATH": 7})
        self.refusal(environment={f"N{one}": "v"
                                  for one in range(
                                      retained_verification.MAX_ENVIRONMENT
                                      + 1)})
        held = retained_verification.owned_context(
            context_of(environment={"Z": "1", "A": "2"}))
        self.assertEqual(list(held["environment"]), ["A", "Z"])

    def test_the_tool_and_runtime_selections_are_closed_text(self):
        self.refusal(tool={"kind": "host-interpreter"})
        self.refusal(tool={"kind": "host-interpreter", "selector": None})
        self.refusal(runtime={"kind": "manager-local"})

    def test_every_member_moves_the_digest(self):
        base = retained_verification.context_digest(context_of())
        for changed in (
                {"working_directory": retained_verification.SCRATCH_ROOT},
                {"environment": {"LC_ALL": "C", "PATH": "/bin"}},
                {"tool": {"kind": "host-interpreter", "selector": "python3.13"}},
                {"runtime": {"kind": "manager-local", "isolation": "shared"}}):
            with self.subTest(member=sorted(changed)[0]):
                self.assertNotEqual(
                    retained_verification.context_digest(
                        context_of(**changed)), base)


# -- 2. the retained candidate's declared source -----------------------------


class TheCandidatesSourceIsValidatedBeforeAnyByteIsCopied(unittest.TestCase):
    """Source-aware rather than source-guessing."""

    def candidate(self, **changed):
        held = {"base": "a" * 40, "head": "f" * 40,
                "transport": "bundle/candidate.bundle"}
        held.update(changed)
        return held

    def test_a_bundle_transport_is_the_git_profile_with_its_pair_proved(self):
        held = retained_verification.candidate_source_profile(self.candidate())
        self.assertEqual(held["source_profile"], checkout.GIT_PROFILE)
        self.assertEqual(held["declared_base"], "a" * 40)
        self.assertEqual(held["declared_head"], "f" * 40)

    def test_an_abbreviated_or_upper_case_name_is_refused_not_expanded(self):
        for one in ("a" * 7, "A" * 40, "", None):
            with self.subTest(base=one):
                with self.assertRaises(ContractRefusal) as caught:
                    retained_verification.candidate_source_profile(
                        self.candidate(base=one))
                self.assertEqual(caught.exception.code, "schema")
        with self.assertRaises(ContractRefusal):
            retained_verification.candidate_source_profile(
                self.candidate(head="f" * 7))

    def test_a_generic_candidate_carrying_a_revision_is_refused(self):
        with self.assertRaises(ContractRefusal) as caught:
            retained_verification.candidate_source_profile(
                self.candidate(transport="archive/candidate.tar"))
        self.assertIn("source profile package refuses",
                      caught.exception.message)

    def test_a_generic_candidate_with_no_revision_is_admitted(self):
        held = retained_verification.candidate_source_profile(
            self.candidate(transport="archive/candidate.tar", base=None,
                           head=None))
        self.assertEqual(held["source_profile"], checkout.GENERIC_PROFILE)
        self.assertIsNone(held["declared_base"])

    def test_the_profile_words_come_from_the_package_that_owns_them(self):
        for one in retained_verification.SOURCE_PROFILES:
            self.assertIn(one, checkout.PROFILES)


# -- 3. the one complete outcome ---------------------------------------------


class OneApprovedRecoveryVerifiesTheRetainedBytesAndReachesReview(
        ExecutionCase):
    """The first usable result of 1-C, and the whole of REC-8's own sentence.

    THE SCRIPTED HALF, SAID OUT LOUD: the analysis diagnosis this path
    consumes is Stage 1-A's scripted document and proves orchestration and
    evidence fidelity rather than live diagnostic quality. Everything after
    the owner's decision is real -- a real copy of real bytes, a real process,
    a real tick.
    """

    def test_the_whole_loop_performs_three_acts_and_releases_the_review(self):
        acts = self.whole_loop()
        self.assertEqual([one["act"] for one in acts],
                         ["materialize", "execute", "hand-off"])
        self.assertEqual([one["outcome"] for one in acts],
                         ["materialized", "executed", "handed-off"])
        # EVERY ACT NAMES THE ORIGINAL FAILURE AND THE SUCCESSOR, which is
        # what makes a tick report attributable rather than a log line.
        for one in acts:
            self.assertEqual(one["failure_key"], self.key)
            self.assertEqual(one["job_id"], "recovery-D1")
        self.assertEqual(
            retained_verification.execution_readiness(
                self.jobs,
                retained_recovery.successor_of(self.jobs, "D1"))["state"],
            "handed-off")

    def test_the_materialization_is_the_exact_retained_candidate(self):
        self.admitted()
        held = self.materialize()
        candidate = held["candidate"]
        measured = self.custody_bytes()
        self.assertEqual(held["measured"]["tree_digest"],
                         candidate["content_digest"])
        self.assertEqual(held["measured"]["tree_digest"],
                         measured["tree_digest"])
        self.assertEqual(held["source"]["source_profile"],
                         checkout.GIT_PROFILE)
        self.assertEqual(held["source"]["declared_base"], candidate["base"])
        # AND THE BYTES ARE REALLY THERE, in a workspace of their own.
        root = self.workspace_of(held)
        self.assertTrue(root.startswith(self.workspaces))
        self.assertEqual(
            directory_manifest(os.path.join(
                root, retained_verification.CANDIDATE_ROOT))["tree_digest"],
            candidate["content_digest"])
        self.assertEqual(
            sorted(os.listdir(root)),
            sorted(retained_verification.WORKSPACE_ROOTS))

    def test_the_command_that_ran_is_the_approved_argv_and_context(self):
        self.admitted()
        self.materialize()
        result = self.execute()
        self.assertEqual(len(self.ran.calls), 1)
        call = self.ran.calls[0]
        self.assertEqual(call["argv"], CORRECTED)
        self.assertEqual(
            call["cwd"],
            os.path.join(self.workspace_of(result),
                         retained_verification.CANDIDATE_ROOT))
        self.assertEqual(call["env"], CONTEXT["environment"])
        # THE APPROVED PER-COMMAND CEILING, from the owner-approved profile
        # and not from this adapter: 900 seconds, which is also what the
        # retained timing records it ran under.
        self.assertEqual(call["timeout"], 900)
        self.assertEqual(result["timing"]["ceiling_seconds"], 900)
        self.assertFalse(result["timing"]["timed_out"])
        self.assertEqual(result["outcome"], "passed")
        self.assertEqual(result["exit_status"], 0)

    def test_the_retained_account_is_measured_and_attributable(self):
        self.admitted()
        self.materialize()
        result = self.execute()
        place = result["retained"]["locator"][len("file://"):]
        self.assertEqual(directory_manifest(place)["tree_digest"],
                         result["retained"]["result_digest"])
        self.assertEqual(sorted(os.listdir(place)),
                         ["exit", "stderr", "stdout", "timing.json"])
        with open(os.path.join(place, "stdout"), "rb") as reading:
            self.assertIn(b"five structural predicates hold", reading.read())
        # AND THE SUPPORTED DURABLE ACCOUNT STAGE 1-B OWNS WAS WRITTEN
        # THROUGH ITS OWN BOUNDARY, with this execution's retained digest.
        account = retained_recovery.verification_of(self.jobs, "recovery-D1")
        self.assertEqual(account["outcome"], "passed")
        self.assertEqual(account["argv"], CORRECTED)
        self.assertEqual(account["result_digest"],
                         result["retained"]["result_digest"])
        self.assertEqual(account["verification_attempt_id"],
                         "verification-recovery-D1")
        self.assertEqual(
            retained_recovery.successor_disposition(self.jobs, "D1"),
            "verified")

    def test_the_handoff_binds_the_same_candidate_and_this_evidence(self):
        self.whole_loop()
        handoff = retained_verification.handoff_of(self.jobs, "recovery-D1")
        self.assertEqual(handoff["review_stage_id"], "recovery-D1/review")
        self.assertEqual(handoff["candidate"]["content_digest"],
                         self.custody_bytes()["tree_digest"])
        self.assertEqual(handoff["workspace"]["tree_digest"],
                         handoff["candidate"]["content_digest"])
        self.assertEqual(handoff["workspace"]["delivered"], "read-only")
        self.assertEqual(handoff["verification"]["outcome"], "passed")
        self.assertEqual(handoff["verification"]["argv"], CORRECTED)
        self.assertEqual(
            handoff["verification"]["context_digest"],
            retained_verification.context_digest(self.context))
        # THE PRODUCER IS THE ORIGINAL ATTEMPT'S, UNCHANGED: this recovery
        # never publishes as the stopped producer, and review is independent
        # OF somebody rather than of nobody.
        failure = failure_analysis.failure_of(self.jobs, self.key)
        self.assertEqual(handoff["producer"]["attempt_id"],
                         failure["selectors"]["attempt_id"])
        self.assertEqual(handoff["producer"]["participant"],
                         failure["execution"]["participant"])
        self.assertEqual(handoff["producer"]["job_id"], "job-a")
        self.assertEqual(handoff["evidence"]["custody_locator"],
                         "file://" + self.held["failed"]["custody"])

    def test_the_gate_opens_only_on_the_handoff_and_the_tick_then_admits(self):
        self.admitted()
        # BEFORE: the exact reservation is visible and the review is held.
        gate = self.gate()
        self.assertFalse(gate["open"])
        self.assertEqual(gate["reason"], retained_recovery.GATE_UNAVAILABLE)
        self.assertEqual(gate["decision_id"], "D1")
        self.ticked(times=2)
        # A PASSED ACCOUNT ALONE DOES NOT OPEN IT, which is the whole of the
        # correction this slice was asked for.
        self.assertEqual(
            retained_recovery.verification_of(self.jobs,
                                              "recovery-D1")["outcome"],
            "passed")
        self.assertFalse(self.gate()["open"])
        report, operations = self.swept()
        self.assertEqual([one for one in report["acts"]
                          if "recovery-D1" in json.dumps(one)], [])
        # AND THE HANDOFF OPENS IT, after which the ORDINARY tick admits the
        # review stage automatically. No case writes a gate.
        self.ticked()
        gate = self.gate()
        self.assertTrue(gate["open"])
        self.assertEqual(gate["reason"], retained_recovery.GATE_VALIDATED)
        self.assertEqual(self.projected_gate()["open"], True)
        report, operations = self.swept()
        admitted = [one for one in report["acts"]
                    if one["stage_id"] == "recovery-D1/review"]
        self.assertEqual([one["act"] for one in admitted], ["admit"])
        self.assertEqual(admitted[0]["outcome"], "performed")

    def test_the_review_the_tick_admits_is_for_the_same_candidate(self):
        self.whole_loop()
        report, operations = self.swept()
        self.assertIn(("admit", "recovery-D1/review"), operations.calls)
        # AND THE ONE STAGE OF THAT JOB IS A REVIEW OF THE FAILED JOB'S OWN
        # WORK, carrying the candidate the handoff bound -- which is the
        # worker's own claim about the tree it produced, unchanged.
        rows = submission.stages_of(self.jobs, "recovery-D1")
        self.assertEqual([(row["kind"], row["work_id"]) for row in rows],
                         [("review", WORK_A)])
        handoff = retained_verification.handoff_of(self.jobs, "recovery-D1")
        self.assertEqual(handoff["candidate"]["head"],
                         self.held["failed"]["document"]["outputs"][0][
                             "result_metadata"][
                                 failure_analysis.CANDIDATE_CLAIM]["head"])

    def test_zero_implementation_calls_across_the_whole_loop(self):
        """NO IMPLEMENTATION REDISPATCH, counted rather than asserted in prose.

        COUNTED OVER THE RECOVERY, which is what the claim is about. The
        FAILED Job's own implementation stage is still an ordinary queued
        stage of an ordinary Job and this tick admits it exactly as it would
        have before any recovery existed; what must not happen -- and what is
        counted here -- is an implementation act of the SUCCESSOR, or a
        successor that carries such a stage at all.
        """
        self.whole_loop()
        report, operations = self.swept()
        self.assertEqual([call for call in operations.calls
                          if call[1].startswith("recovery-")
                          and "implementation" in call[1]], [])
        self.assertEqual([call for call in operations.calls
                          if call[1].startswith("recovery-")],
                         [("admit", "recovery-D1/review")])
        self.assertEqual(
            [row["kind"] for row in submission.stages_of(self.jobs,
                                                         "recovery-D1")],
            ["review"])
        # AND THE ORIGINAL JOB IS UNTOUCHED: its own stages, its own failure
        # and its own terminal are exactly what they were.
        self.assertEqual(
            [row["kind"] for row in submission.stages_of(self.jobs, "job-a")],
            ["implementation", "review"])
        self.assertEqual(
            failure_analysis.failure_of(self.jobs, self.key)["verification"][
                "argv"],
            ["bash", "-c", "exec python3 -m unittest -v x\n"])

    def test_the_owner_read_reports_the_execution_beside_the_admission(self):
        self.whole_loop()
        read = self.read(self.key, "--participant", OWNER)
        held = read["successors"][0]
        self.assertEqual(held["execution_readiness"]["state"], "handed-off")
        self.assertEqual(held["execution_readiness"]["review"], "releasable")
        self.assertEqual(
            held["execution"]["handoff"]["candidate"]["content_digest"],
            self.custody_bytes()["tree_digest"])
        self.assertEqual(
            held["execution"]["result"]["outcome"], "passed")
        self.assertIsNone(held["execution"]["renewed_item"])
        self.assertIsNone(held["execution"]["hold"])


# -- 4. the verifier never replaces candidate custody ------------------------


class VerifierOutputNeverBecomesACandidate(ExecutionCase):
    """REC-8 in four words, kept structurally rather than by intention."""

    def test_the_original_custody_is_byte_identical_after_the_whole_loop(self):
        before = self.control_bytes()
        custody = self.custody_bytes()
        self.whole_loop()
        self.assertEqual(self.custody_bytes(), custody)
        # AND THE CONTROL STORE ITSELF IS UNTOUCHED: this slice reads the
        # Worker Manager and writes only its own Job-store journal.
        self.assertEqual(self.control_bytes(), before)

    def test_the_candidate_is_the_same_tree_before_and_after_the_command(self):
        self.admitted()
        self.materialize()
        result = self.execute()
        self.assertTrue(result["workspace"]["candidate_unchanged"])
        self.assertEqual(result["workspace"]["candidate_tree_digest_before"],
                         result["workspace"]["candidate_tree_digest_after"])
        self.assertEqual(result["workspace"]["candidate_tree_digest_after"],
                         result["candidate"]["content_digest"])

    def test_the_retained_output_lives_under_its_own_root(self):
        self.admitted()
        material = self.materialize()
        result = self.execute()
        root = self.workspace_of(material)
        self.assertTrue(result["retained"]["locator"].startswith(
            "file://" + os.path.join(root,
                                     retained_verification.OUTPUT_ROOT)))
        # NOTHING THE COMMAND WROTE IS INSIDE THE CANDIDATE ROOT, and the
        # scratch root is its own place.
        self.assertEqual(
            sorted(os.listdir(os.path.join(
                root, retained_verification.CANDIDATE_ROOT))),
            ["result.json"])

    def test_a_workspace_the_verifier_changed_is_never_handed_to_review(self):
        """The one case that breaks the rule on purpose."""
        self.admitted()
        material = self.materialize()
        self.execute()
        root = self.workspace_of(material)
        place = os.path.join(root, retained_verification.CANDIDATE_ROOT,
                             "generated.txt")
        os.chmod(os.path.join(root, retained_verification.CANDIDATE_ROOT),
                 0o700)
        with open(place, "wb") as writing:
            writing.write(b"a verifier wrote this\n")
        held = self.refusal(self.hand_off)
        self.assertEqual(held.code, "digest")
        self.assertIn("never becomes a new candidate", held.message)
        self.assertIsNone(retained_verification.handoff_of(self.jobs,
                                                           "recovery-D1"))
        self.assertFalse(self.gate()["open"])

    def test_a_candidate_that_does_not_materialize_to_its_bytes_refuses(self):
        self.admitted()
        with open(os.path.join(self.held["failed"]["custody"], "extra.json"),
                  "wb") as writing:
            writing.write(b"{}\n")
        held = self.refusal(self.materialize)
        self.assertEqual(held.code, "digest")
        self.assertIsNone(retained_verification.materialization_of(
            self.jobs, "recovery-D1"))


# -- 5. only the approved command, only in the approved context --------------


class OnlyTheApprovedCommandRunsAndOnlyOnce(ExecutionCase):
    """Zero automatic retry and zero correction, as a property of records."""

    def test_a_changed_declared_context_refuses_before_the_command(self):
        self.admitted()
        self.materialize()
        moved = Seam(control=self.control,
                     context=context_of(environment={"PATH": "/bin"}),
                     workspaces=self.workspaces, runner=self.runner,
                     declaration=self.declaration)
        held = self.refusal(self.execute, seam=moved)
        self.assertEqual(held.code, "digest")
        self.assertIn("changed inputs after approval", held.message)
        self.assertEqual(self.ran.calls, [])
        self.assertIsNone(retained_verification.execution_result_of(
            self.jobs, "recovery-D1"))

    def test_an_unmaterialized_successor_runs_nothing(self):
        self.admitted()
        held = self.refusal(self.execute)
        self.assertIn("materialized no candidate", held.message)
        self.assertEqual(self.ran.calls, [])

    def test_a_second_execution_replays_and_starts_no_second_process(self):
        self.admitted()
        self.materialize()
        first = self.execute()
        again = self.execute(now=AFTER)
        self.assertEqual(again, first)
        self.assertEqual(len(self.ran.calls), 1)
        self.assertEqual(len(self.journal(retained_verification.RESULT_KIND)),
                         1)

    def test_every_act_replays_under_its_own_derived_identity(self):
        self.whole_loop()
        for kind in (retained_verification.MATERIALIZATION_KIND,
                     retained_verification.RESULT_KIND,
                     retained_verification.HANDOFF_KIND):
            with self.subTest(kind=kind):
                self.assertEqual(self.journal(kind),
                                 [f"{kind}:recovery-D1"])
        self.assertEqual(self.ticked(times=2), [])
        self.assertEqual(len(self.ran.calls), 1)

    def test_the_review_only_decision_never_re_runs_the_verification(self):
        self.whole_loop()
        job_control.expire(self.jobs, job_id="recovery-D1",
                           trigger="job-deadline", stage_id=None,
                           deadline_at=EXPIRED, observed_at=EXPIRED)
        self.ticked(now=AFTER)
        read = self.read(self.key)
        lineage = [one for one in read["successors"]
                   if one["job_id"] == "recovery-D1"][0]
        self.decided(decision_id="D2", stages=["review"],
                     lineage={"successor_job_id": "recovery-D1",
                              "verification_attempt_id":
                                  lineage["verification_attempt_id"],
                              "verification_result_digest":
                                  lineage["verification_result_digest"]},
                     clock=lambda: AFTER)
        held = self.refusal(self.execute, decision_id="D2")
        self.assertEqual((held.category, held.code), ("policy", "denied"))
        self.assertIn("OMITTED", held.message)
        self.assertEqual(len(self.ran.calls), 1)

    def test_a_runner_that_cannot_start_the_command_is_a_condition(self):
        self.admitted()
        self.materialize()

        def refusing(argv, **named):
            raise OSError(2, "no such file")

        seam = Seam(control=self.control, context=self.context,
                    workspaces=self.workspaces,
                    runner=recovery_execution.CommandRunner(
                        stage_b.CURRENT["identity"], clock=lambda: LATER,
                        run=refusing),
                    declaration=self.declaration)
        held = self.refusal(self.execute, seam=seam)
        self.assertEqual((held.category, held.code),
                         ("unavailable", "transport"))
        self.assertIsNone(retained_verification.execution_result_of(
            self.jobs, "recovery-D1"))
        # THE DURABLE INTENT STANDS, which is REC-3's order: it was written
        # before the effect, so what happened afterwards is a question with
        # an answer rather than a gap.
        intent = retained_verification.execution_intent_of(self.jobs,
                                                           "recovery-D1")
        self.assertEqual(intent["argv"], CORRECTED)
        # AND THE NEXT ATTEMPT HOLDS RATHER THAN STARTING A SECOND COMMAND.
        # This manager did not watch the child; it will not decide from a
        # refusal that nothing ran.
        again = self.refusal(self.execute, seam=seam)
        self.assertEqual((again.category, again.code),
                         ("ambiguous", "operation"))
        self.assertIn("UNKNOWN", again.message)
        readiness = retained_verification.execution_readiness(
            self.jobs, retained_recovery.successor_of(self.jobs, "D1"))
        self.assertEqual(readiness["state"], "unknown")
        self.assertIsNone(readiness["owed"])
        self.assertEqual(readiness["review"], "blocked")
        # SO THE PASS GOES QUIET AND THE OWNER DISPOSES OF IT.
        self.assertEqual(self.ticked(times=2, seam=seam), [])
        self.assertFalse(self.gate()["open"])

    def test_a_ceiling_that_stopped_the_command_is_never_a_pass(self):
        self.admitted()
        self.materialize()

        def timing_out(argv, **named):
            raise subprocess.TimeoutExpired(argv, named["timeout"],
                                            output=b"partial\n", stderr=b"")

        seam = Seam(control=self.control, context=self.context,
                    workspaces=self.workspaces,
                    runner=recovery_execution.CommandRunner(
                        stage_b.CURRENT["identity"], clock=lambda: LATER,
                        run=timing_out),
                    declaration=self.declaration)
        result = self.execute(seam=seam)
        self.assertEqual(result["outcome"], "failed")
        self.assertTrue(result["timing"]["timed_out"])
        self.assertNotEqual(result["exit_status"], 0)
        # THE PARTIAL OUTPUT IS KEPT, because evidence about less than what
        # happened is not evidence about what happened.
        self.assertEqual(
            result["retained"]["streams"]["stdout"]["bytes"], len(b"partial\n"))


# -- 6. a renewed verification failure ---------------------------------------


class ARenewedFailureEarnsOneAnalysisAndOneOwnerItemAndNoSuccessor(
        ExecutionCase):
    """"Each recovery round needs a new owner decision.\""""

    def failed(self):
        self.admitted(corrected=STILL_FAILS)
        return self.ticked(times=3)

    def test_the_renewed_failure_has_its_own_key_and_one_of_each_record(self):
        acts = self.failed()
        self.assertEqual([one["act"] for one in acts],
                         ["materialize", "execute", "renew"])
        failure = retained_verification.renewed_failure_of(self.jobs,
                                                           "recovery-D1")
        self.assertNotEqual(failure["failure_key"], self.key)
        self.assertEqual(failure["original_failure_key"], self.key)
        self.assertEqual(failure["stage_id"], "recovery-D1/verification")
        self.assertIsNone(failure["successor"])
        self.assertEqual(failure["next"], "a new explicit owner decision")
        self.assertEqual(failure["verification"]["exit_status"], 3)
        for kind in (retained_verification.RENEWED_KIND,
                     retained_verification.RENEWED_ANALYSIS_KIND,
                     retained_verification.RENEWED_ITEM_KIND):
            with self.subTest(kind=kind):
                self.assertEqual(self.journal(kind),
                                 [f"{kind}:recovery-D1"])

    def test_the_one_analysis_is_admitted_under_the_approved_bounds(self):
        self.failed()
        held = retained_verification.renewed_analysis_of(self.jobs,
                                                         "recovery-D1")
        self.assertEqual(held["profile"], failure_analysis.ANALYSIS_PROFILE)
        self.assertEqual(held["profile_digest"],
                         "sha256:" + stage_a.APPROVED_PROFILE_DIGEST)
        self.assertEqual(held["role"], failure_analysis.ANALYSIS_ROLE)
        self.assertEqual(held["participant"], stage_a.ANALYST)
        self.assertEqual(held["policy"]["overall_job_seconds"], 4800)
        self.assertEqual(held["deadlines"]["admitted_at"], LATER)
        self.assertEqual(held["input_digest"],
                         retained_verification.renewed_failure_of(
                             self.jobs, "recovery-D1")["input_digest"])

    def test_the_owner_item_says_no_successor_follows_automatically(self):
        self.failed()
        item = retained_verification.renewed_item_of(self.jobs, "recovery-D1")
        self.assertEqual(item["destination"], OWNER)
        self.assertEqual(item["outcome"],
                         retained_verification.RENEWED_OUTCOME)
        self.assertFalse(item["automatic_successor"])
        self.assertIn("exited 3", item["reason"])
        self.assertEqual(retained_verification.owner_items_of(self.jobs),
                         {"renewed": [item], "endpoints": [], "held": []})

    def test_no_review_is_ever_released_by_a_failed_verification(self):
        self.failed()
        self.assertIsNone(retained_verification.handoff_of(self.jobs,
                                                           "recovery-D1"))
        gate = self.gate()
        self.assertFalse(gate["open"])
        self.assertEqual(gate["reason"], retained_recovery.GATE_UNAVAILABLE)
        report, operations = self.swept()
        self.assertEqual([one for one in report["acts"]
                          if "recovery-D1" in json.dumps(one)], [])
        held = self.refusal(self.hand_off)
        self.assertEqual((held.category, held.code), ("policy", "denied"))

    def test_no_second_successor_is_admitted_and_no_further_act_happens(self):
        """NEVER AN AUTOMATIC RECOVERY LOOP, and never a second one by hand.

        The pass stops. And a second APPROVAL of the ORIGINAL failure is
        refused by Stage 1-B's own fence in the words it was written in: one
        retained failure has one verification/review successor, and "a
        further round is a new owner decision on NEW EVIDENCE". The new
        evidence is what this slice delivers -- the renewed failure's own key,
        its one analysis and its one owner item -- and admitting a successor
        against that key is the owner's next explicit act, which nothing here
        performs.
        """
        self.failed()
        self.assertEqual(self.ticked(times=3), [])
        self.assertEqual(len(self.ran.calls), 1)
        self.assertEqual(
            [one["job_id"]
             for one in retained_recovery.successors_for(self.jobs,
                                                         self.key)],
            ["recovery-D1"])
        code, said = self.command(
            *self.decide_argv(self.key, self.read(self.key),
                              decision_id="D3", corrected=CORRECTED,
                              context_digest=retained_verification
                              .context_digest(self.context)))
        self.assertEqual(code, 1, said)
        self.assertIsNone(self.job_row("recovery-D3"))
        self.assertEqual(
            [one["job_id"]
             for one in retained_recovery.successors_for(self.jobs,
                                                         self.key)],
            ["recovery-D1"])

    def test_the_renewed_analysis_endpoint_goes_to_the_owner_once(self):
        """Analysis failure, expiry or cancellation: owner, no recursion."""
        self.failed()
        item = retained_verification.renewed_item_of(self.jobs, "recovery-D1")
        endpoint = retained_verification.deliver_renewed_endpoint(
            self.jobs, self.seam, decision_id="D1",
            outcome="analysis-expired",
            reason="the analysis reached its 4800-second bound", now=AFTER)
        self.assertEqual(endpoint["outcome"], "analysis-expired")
        self.assertEqual(endpoint["destination"], OWNER)
        self.assertEqual(endpoint["failure_key"], item["failure_key"])
        self.assertIsNone(endpoint["automatic_retry"])
        self.assertIsNone(endpoint["recursive_analysis"])
        self.assertEqual(endpoint["analysis"]["profile"],
                         failure_analysis.ANALYSIS_PROFILE)
        # THE ONE OWNER ITEM IS UNCHANGED -- a second item for one failure
        # would be a second item -- and a second endpoint replays rather than
        # recursing.
        self.assertEqual(
            retained_verification.renewed_item_of(self.jobs, "recovery-D1"),
            item)
        again = retained_verification.deliver_renewed_endpoint(
            self.jobs, self.seam, decision_id="D1",
            outcome="analysis-failed", reason="another reason", now=AFTER)
        self.assertEqual(again, endpoint)
        for kind in (retained_verification.RENEWED_ITEM_KIND,
                     retained_verification.RENEWED_ANALYSIS_KIND,
                     retained_verification.RENEWED_ENDPOINT_KIND):
            with self.subTest(kind=kind):
                self.assertEqual(self.journal(kind),
                                 [f"{kind}:recovery-D1"])
        self.assertEqual(self.ticked(times=2), [])
        self.assertEqual(
            retained_verification.owner_items_of(self.jobs),
            {"renewed": [item], "endpoints": [endpoint], "held": []})

    def test_an_endpoint_outside_the_closed_set_is_refused(self):
        self.failed()
        held = self.refusal(retained_verification.deliver_renewed_endpoint,
                            self.jobs, self.seam, decision_id="D1",
                            outcome="analysed", reason="x")
        self.assertEqual(held.code, "schema")

    def test_a_renewed_failure_without_an_execution_is_refused(self):
        self.admitted()
        held = self.refusal(retained_verification.renew, self.jobs, self.seam,
                            decision_id="D1")
        self.assertIn("journalled no verification execution", held.message)

    def test_a_passed_verification_is_never_renewed(self):
        self.admitted()
        self.ticked(times=2)
        held = self.refusal(retained_verification.renew, self.jobs, self.seam,
                            decision_id="D1")
        self.assertEqual((held.category, held.code), ("policy", "denied"))


# -- 7. expiry after a passed verification -----------------------------------


class ExpiryAfterAPassedVerificationHoldsAndNeverAnalyses(ExecutionCase):
    """M385611, and it is neither of the two things it looks like."""

    def expired(self, job_id="recovery-D1"):
        return job_control.expire(self.jobs, job_id=job_id,
                                  trigger="job-deadline", stage_id=None,
                                  deadline_at=EXPIRED, observed_at=EXPIRED)

    def verified_then_expired(self):
        self.admitted()
        self.ticked(times=2)
        self.expired()
        return self.ticked(now=AFTER)

    def test_the_hold_preserves_the_verification_and_names_its_lineage(self):
        acts = self.verified_then_expired()
        self.assertEqual([one["act"] for one in acts], ["hold"])
        item = retained_verification.hold_of(self.jobs, "recovery-D1")
        self.assertEqual(item["outcome"], retained_verification.HOLD_OUTCOME)
        self.assertEqual(item["destination"], OWNER)
        self.assertEqual(item["fence"]["trigger"], "job-deadline")
        self.assertEqual(item["verification"]["outcome"], "passed")
        self.assertIsNone(item["analysis"])
        self.assertIsNone(item["retry"])
        account = retained_recovery.verification_of(self.jobs, "recovery-D1")
        self.assertEqual(item["lineage"],
                         {"successor_job_id": "recovery-D1",
                          "verification_attempt_id":
                              account["verification_attempt_id"],
                          "verification_result_digest": digest(account)})

    def test_time_expiry_alone_invalidates_nothing_and_triggers_nothing(self):
        self.verified_then_expired()
        # NO FAILURE ANALYSIS, NO RENEWED ITEM, NO RETRY, NO HANDOFF.
        self.assertIsNone(retained_verification.renewed_failure_of(
            self.jobs, "recovery-D1"))
        self.assertIsNone(retained_verification.renewed_item_of(
            self.jobs, "recovery-D1"))
        self.assertIsNone(retained_verification.handoff_of(self.jobs,
                                                           "recovery-D1"))
        self.assertFalse(self.gate()["open"])
        self.assertEqual(self.ticked(now=AFTER, times=2), [])
        self.assertEqual(len(self.ran.calls), 1)
        # AND THE EXPIRED DEADLINE IS EXACTLY WHERE IT WAS.
        self.assertEqual(
            job_control.expiry_of(self.jobs, "recovery-D1")["requested_at"],
            EXPIRED)

    def test_the_busy_reviewer_wait_is_the_same_disposition(self):
        """A successor that expired WAITING for a reviewer, not failing."""
        self.admitted()
        self.ticked(times=3)
        report, operations = self.swept()
        self.assertEqual(
            [one["act"] for one in report["acts"]
             if one["stage_id"] == "recovery-D1/review"], ["admit"])
        # THE REVIEW IS QUEUED AND NOBODY CLAIMED IT, and the Job's own
        # deadline passes while it waits.
        self.expired()
        acts = self.ticked(now=AFTER)
        self.assertEqual([one["act"] for one in acts], ["hold"])
        item = retained_verification.hold_of(self.jobs, "recovery-D1")
        self.assertEqual(item["verification"]["outcome"], "passed")
        self.assertIsNone(item["analysis"])
        # AND THE EXPIRED JOB EARNS NO FURTHER ADMISSION, which is the Job's
        # own fence deciding it: the handoff that opened the gate stays
        # visible and committed, and nothing acts through it again.
        self.assertTrue(retained_recovery.execution_gate(
            self.jobs, "recovery-D1")["open"])
        report, operations = self.swept(now=AFTER)
        self.assertEqual([one for one in report["acts"]
                          if one["stage_id"] == "recovery-D1/review"], [])
        self.assertEqual(self.ticked(now=AFTER, times=2), [])

    def test_the_hold_is_delivered_once_and_replays(self):
        self.verified_then_expired()
        first = retained_verification.hold_of(self.jobs, "recovery-D1")
        again = retained_verification.hold(self.jobs, self.seam,
                                           decision_id="D1", now=NOW)
        self.assertEqual(again, first)
        self.assertEqual(self.journal(retained_verification.HOLD_KIND),
                         [f"{retained_verification.HOLD_KIND}:recovery-D1"])

    def test_a_live_successor_is_never_held_and_a_cancelled_one_is_not(self):
        self.admitted()
        self.ticked(times=2)
        held = self.refusal(retained_verification.hold, self.jobs, self.seam,
                            decision_id="D1")
        self.assertIn("neither expired nor cancelled", held.message)
        cancellation.request(self.jobs, job_id="recovery-D1",
                             reason="the owner stopped it")
        held = self.refusal(retained_verification.hold, self.jobs, self.seam,
                            decision_id="D1")
        self.assertIn("cancelled", held.message)

    def test_the_owner_reads_the_held_item_and_its_exact_operands(self):
        self.verified_then_expired()
        item = retained_verification.hold_of(self.jobs, "recovery-D1")
        self.assertEqual(retained_verification.owner_items_of(self.jobs),
                         {"renewed": [], "endpoints": [], "held": [item]})
        read = self.read(self.key, "--participant", OWNER)
        held = read["successors"][0]
        self.assertEqual(held["execution_readiness"]["state"], "held")
        self.assertEqual(held["execution_readiness"]["owed"],
                         "a review-only owner decision")
        self.assertEqual(held["execution"]["hold"]["lineage"],
                         item["lineage"])
        # AND THE THREE OPERANDS THE REVIEW-ONLY DECISION NAMES BACK ARE THE
        # ONES STAGE 1-B'S OWN READ ALREADY REPORTS.
        self.assertEqual(held["verification_result_digest"],
                         item["lineage"]["verification_result_digest"])


# -- 8. the owner-authorized review-only recovery ----------------------------


class ReviewOnlyRecoveryReusesTheEvidenceAndNeverReVerifies(ExecutionCase):
    """Section 3.7: the same approved profile, with verification omitted."""

    def held_item(self):
        self.admitted()
        self.ticked(times=2)
        job_control.expire(self.jobs, job_id="recovery-D1",
                           trigger="job-deadline", stage_id=None,
                           deadline_at=EXPIRED, observed_at=EXPIRED)
        self.ticked(now=AFTER)
        return retained_verification.hold_of(self.jobs, "recovery-D1")

    def review_only(self, *, decision_id="D2", lineage=None):
        item = self.held_item() if lineage is None else None
        return self.decided(decision_id=decision_id, stages=["review"],
                            lineage=lineage or item["lineage"],
                            clock=lambda: AFTER)

    def test_the_review_only_successor_hands_over_without_running_anything(
            self):
        said = self.review_only()
        self.assertEqual(said["successor"]["stages"], ["review"])
        acts = self.ticked(now=AFTER, times=2)
        self.assertEqual([one["act"] for one in acts],
                         ["materialize", "hand-off"])
        self.assertEqual(len(self.ran.calls), 1)
        self.assertIsNone(retained_verification.execution_result_of(
            self.jobs, "recovery-D2"))
        handoff = retained_verification.handoff_of(self.jobs, "recovery-D2")
        self.assertEqual(handoff["stages"], ["review"])
        self.assertIn("reused and not repeated", handoff["verification"]["why"])
        self.assertEqual(handoff["verification"]["attempt_id"],
                         "verification-recovery-D1")
        self.assertEqual(handoff["candidate"]["content_digest"],
                         self.custody_bytes()["tree_digest"])

    def test_the_review_only_gate_opens_and_the_tick_admits_that_review(self):
        self.review_only()
        self.ticked(now=AFTER, times=2)
        gate = retained_recovery.execution_gate(self.jobs, "recovery-D2")
        self.assertTrue(gate["open"])
        self.assertEqual(gate["reason"], retained_recovery.GATE_VALIDATED)
        report, operations = self.swept(now=AFTER)
        self.assertEqual(
            [one["stage_id"] for one in report["acts"]
             if one["act"] == "admit"], ["recovery-D2/review"])
        # AND THE EXPIRED PREDECESSOR IS NEVER ADMITTED AGAIN.
        self.assertFalse(retained_recovery.execution_gate(
            self.jobs, "recovery-D1")["open"])

    def test_the_approved_bounds_are_the_same_profile_and_digest(self):
        said = self.review_only()
        bounds = said["successor"]["bounds"]
        self.assertEqual(bounds["profile"],
                         retained_recovery.SUCCESSOR_PROFILE)
        self.assertEqual(bounds["digest"],
                         "sha256:" + stage_b.APPROVED_PROFILE_DIGEST)
        self.assertEqual(bounds["overall_job_seconds"], 9960)
        self.assertEqual(bounds["each_stage_seconds"], 4800)
        self.assertEqual(bounds["verification_command_seconds"], 900)
        self.assertEqual(bounds["admitted_at"], AFTER)

    def test_a_lineage_naming_another_execution_refuses_the_handoff(self):
        item = self.held_item()
        self.decided(decision_id="D2", stages=["review"],
                     lineage=item["lineage"], clock=lambda: AFTER)
        self.materialize(decision_id="D2", now=AFTER)
        # THE DECISION'S OWN LINEAGE IS WHAT THE HANDOFF RE-VALIDATES, and a
        # journal whose account has moved under it refuses by digest.
        self.jobs._connection.execute(
            "UPDATE operations SET result = REPLACE(result, '\"passed\"', "
            "'\"unknown\"') WHERE kind = ? ",
            (retained_recovery.VERIFICATION_KIND,))
        held = self.refusal(self.hand_off, decision_id="D2", now=AFTER)
        self.assertIn("digests to", held.message)
        self.assertIsNone(retained_verification.handoff_of(self.jobs,
                                                           "recovery-D2"))

    def test_a_review_only_expiry_holds_again_with_no_further_admission(self):
        self.review_only()
        self.ticked(now=AFTER, times=2)
        job_control.expire(self.jobs, job_id="recovery-D2",
                           trigger="job-deadline", stage_id=None,
                           deadline_at="2026-09-02T05:46:00.000Z",
                           observed_at="2026-09-02T05:46:00.000Z")
        acts = self.ticked(now="2026-09-02T06:00:00.000Z")
        self.assertEqual([one["act"] for one in acts], ["hold"])
        item = retained_verification.hold_of(self.jobs, "recovery-D2")
        self.assertEqual(item["outcome"], retained_verification.HOLD_OUTCOME)
        self.assertEqual(item["verification"]["attempt_id"],
                         "verification-recovery-D1")
        self.assertEqual(self.ticked(now="2026-09-02T06:00:00.000Z",
                                     times=2), [])


# -- 9. restart, concurrency and the fault cuts ------------------------------


class EveryCutBetweenTheActsResumesAndRepeatsNoEffect(ExecutionCase):
    """Fault cuts: materialize, run, handoff, review handoff."""

    def interrupted_account(self, status, concurrent=False, cancelled=False):
        import sys
        from unittest import mock
        self.admitted(corrected=[sys.executable, "-c", f"raise SystemExit({status})"])
        self.materialize()
        with mock.patch.object(retained_recovery, "record_verification", side_effect=RuntimeError("account cut")):
            with self.assertRaisesRegex(RuntimeError, "account cut"):
                self.execute()
        self.assertEqual(len(self.ran.calls), 1)
        self.assertIsNone(retained_recovery.verification_of(self.jobs, "recovery-D1"))
        self.assertFalse(self.gate()["open"])
        if cancelled:
            from baton_v12.job_manager import cancellation
            cancellation.request(self.jobs, job_id="recovery-D1", reason="cancel after committed result")
        restarted = self.reopened()
        if concurrent:
            import concurrent.futures
            from baton_v12.worker_manager import ControlStore
            barrier = threading.Barrier(2, timeout=30)
            def replay(number):
                with JobStore.open(self.jobs.database, authority_uuid=self.AUTHORITY,
                                   incarnation=f"account-{number}", clock=lambda: LATER) as store:
                    with ControlStore.open_readonly(self.control.database,
                                                   incarnation=f"account-{number}", clock=lambda: LATER) as control:
                        seam = Seam(control=control, context=self.context,
                                    workspaces=self.workspaces, runner=self.runner,
                                    declaration=self.declaration)
                        barrier.wait()
                        return retained_verification.execute(store, seam, decision_id="D1", now=LATER)
            with concurrent.futures.ThreadPoolExecutor(2) as pool:
                answers = list(pool.map(replay, (1, 2)))
            self.assertEqual(answers[0], answers[1])
        else:
            self.resumed(restarted, self.ticked)
        self.assertEqual(len(self.ran.calls), 1)
        self.assertEqual(retained_recovery.verification_of(restarted, "recovery-D1")["outcome"], "passed" if status == 0 else "failed")
        self.assertFalse(self.gate()["open"])
        self.resumed(restarted, self.ticked)
        self.resumed(restarted, self.ticked)
        self.assertEqual(len(self.ran.calls), 1)
        self.assertEqual(bool(retained_verification.handoff_of(restarted, "recovery-D1")), status == 0 and not cancelled)
        if cancelled:
            self.assertFalse(self.gate()["open"])
            self.assertIsNone(retained_verification.renewed_item_of(restarted, "recovery-D1"))
        elif status:
            self.assertIsNotNone(retained_verification.renewed_item_of(restarted, "recovery-D1"))

    def test_committed_pass_is_accounted_on_restart_without_another_child(self):
        self.interrupted_account(0)

    def test_committed_failure_is_accounted_on_restart_without_another_child(self):
        self.interrupted_account(1)

    def test_concurrent_pass_account_replays_do_not_repeat_the_child(self):
        self.interrupted_account(0, concurrent=True)

    def test_concurrent_failure_account_replays_do_not_repeat_the_child(self):
        self.interrupted_account(1, concurrent=True)

    def test_account_reconciliation_after_cancellation_does_not_release_review(self):
        self.interrupted_account(0, cancelled=True)

    def reopened(self, incarnation="execution-2"):
        store = JobStore.open(self.jobs.database,
                              authority_uuid=self.AUTHORITY,
                              incarnation=incarnation, clock=lambda: LATER)
        self.addCleanup(store.close)
        return store

    def resumed(self, store, act, **named):
        original, self.jobs = self.jobs, store
        try:
            return act(**named)
        finally:
            self.jobs = original

    def test_a_crash_after_the_materialization_resumes_at_the_command(self):
        self.admitted()
        material = self.materialize()
        restarted = self.reopened()
        self.assertEqual(
            retained_verification.materialization_of(restarted,
                                                     "recovery-D1"),
            material)
        acts = self.resumed(restarted, self.ticked)
        self.assertEqual([one["act"] for one in acts], ["execute"])
        self.assertEqual(len(self.ran.calls), 1)

    def test_a_crash_after_the_command_resumes_at_the_handoff(self):
        self.admitted()
        self.materialize()
        self.execute()
        restarted = self.reopened("execution-3")
        acts = self.resumed(restarted, self.ticked)
        self.assertEqual([one["act"] for one in acts], ["hand-off"])
        self.assertEqual(len(self.ran.calls), 1)
        self.assertTrue(retained_recovery.execution_gate(
            restarted, "recovery-D1")["open"])

    def test_a_restart_before_the_handoff_never_starts_a_second_process(self):
        self.admitted()
        self.materialize()
        self.execute()
        for one in ("execution-4", "execution-5"):
            self.resumed(self.reopened(one), self.ticked)
        self.assertEqual(len(self.ran.calls), 1)
        self.assertEqual(self.journal(retained_verification.RESULT_KIND),
                         [f"{retained_verification.RESULT_KIND}:recovery-D1"])

    def test_two_concurrent_passes_perform_each_act_once(self):
        """THE RACE, SYNCHRONIZED PAST THE POINT A READ WOULD HAVE DECIDED.

        Both threads are inside `execute` and past its first read before
        either takes the exclusive window, so what they meet is the fence
        rather than the order two threads happened to start in. Each opens its
        OWN store and its OWN control handle, because a SQLite connection
        belongs to the thread that made it -- which is also what a second
        manager process would be.
        """
        import concurrent.futures

        from baton_v12.worker_manager import ControlStore

        self.admitted()
        self.materialize()
        barrier = threading.Barrier(2, timeout=30)
        counted = []
        lock = threading.Lock()

        def run(argv, **named):
            with lock:
                counted.append(list(argv))
            return subprocess.run(argv, **named)

        def deciding(incarnation):
            store = JobStore.open(self.jobs.database,
                                  authority_uuid=self.AUTHORITY,
                                  incarnation=incarnation,
                                  clock=lambda: LATER)
            control = ControlStore.open_readonly(self.control.database,
                                                 incarnation=incarnation,
                                                 clock=lambda: LATER)
            seam = Seam(control=control, context=self.context,
                        workspaces=self.workspaces,
                        runner=recovery_execution.CommandRunner(
                            stage_b.CURRENT["identity"],
                            clock=lambda: LATER, run=run),
                        declaration=self.declaration)
            try:
                barrier.wait()
                return retained_verification.execute(store, seam,
                                                     decision_id="D1",
                                                     now=LATER)
            except ContractRefusal as refusal:
                return refusal
            finally:
                barrier.abort()
                control.close()
                store.close()

        with concurrent.futures.ThreadPoolExecutor(2) as pool:
            answers = list(pool.map(deciding, ["concurrent-1",
                                               "concurrent-2"]))
        settled = [one for one in answers if isinstance(one, dict)]
        self.assertTrue(settled, answers)
        # ONE CHILD PROCESS, ONE INTENT AND ONE ACCOUNT, whichever thread won.
        self.assertEqual(len(counted), 1, counted)
        self.assertEqual(self.journal(retained_verification.INTENT_KIND),
                         [f"{retained_verification.INTENT_KIND}:recovery-D1"])
        self.assertEqual(self.journal(retained_verification.RESULT_KIND),
                         [f"{retained_verification.RESULT_KIND}:recovery-D1"])

    def test_the_whole_loop_is_byte_stable_across_a_replayed_tick(self):
        self.whole_loop()
        before = retained_verification.successor_execution(self.jobs,
                                                           "recovery-D1")
        self.ticked(times=3, now=AFTER)
        self.assertEqual(
            retained_verification.successor_execution(self.jobs,
                                                      "recovery-D1"),
            before)

    def test_a_dispatch_replay_of_the_review_admits_it_once(self):
        self.whole_loop()
        operations = FakeOperations(authority_uuid=self.AUTHORITY)
        first, _ = self.swept(operations=operations)
        again, _ = self.swept(operations=operations)
        admits = [one for one in first["acts"]
                  if one["stage_id"] == "recovery-D1/review"
                  and one["act"] == "admit"]
        self.assertEqual([one["outcome"] for one in admits], ["performed"])
        # THE SECOND TICK NEVER ADMITS IT AGAIN: it owes the NEXT act of the
        # ordinary lifecycle, and the deployment was asked to admit once.
        self.assertEqual(
            [one["act"] for one in again["acts"]
             if one["stage_id"] == "recovery-D1/review"], ["claim"])
        self.assertEqual([call for call in operations.calls
                          if call == ("admit", "recovery-D1/review")],
                         [("admit", "recovery-D1/review")])


# -- 10. cancellation, unknown cessation and the two gates -------------------


class CancellationAndUnknownNeverReleaseAReview(ExecutionCase):
    """Unknown holds, and a cancelled execution is never revived."""

    def test_a_cancelled_successor_performs_no_act_and_stays_blocked(self):
        self.admitted()
        cancellation.request(self.jobs, job_id="recovery-D1",
                             reason="the owner stopped it")
        self.assertEqual(self.ticked(times=2), [])
        for act in (self.materialize, self.execute, self.hand_off):
            with self.subTest(act=act.__name__):
                held = self.refusal(act)
                self.assertIn("cancelled", held.message)
        self.assertFalse(self.gate()["open"])
        self.assertEqual(len(self.ran.calls), 0)

    def test_a_cancellation_between_the_command_and_the_handoff_blocks_it(
            self):
        self.admitted()
        self.materialize()
        self.execute()
        cancellation.request(self.jobs, job_id="recovery-D1",
                             reason="the owner stopped it")
        held = self.refusal(self.hand_off)
        self.assertIn("never revived", held.message)
        self.assertFalse(self.gate()["open"])
        self.assertEqual(
            retained_verification.execution_readiness(
                self.jobs,
                retained_recovery.successor_of(self.jobs, "D1"))["state"],
            "cancelled")

    def test_an_expired_successor_runs_no_approved_command(self):
        self.admitted()
        job_control.expire(self.jobs, job_id="recovery-D1",
                           trigger="job-deadline", stage_id=None,
                           deadline_at=EXPIRED, observed_at=EXPIRED)
        held = self.refusal(self.materialize)
        self.assertIn("admitted deadline passed", held.message)
        self.assertEqual(len(self.ran.calls), 0)

    def test_an_unknown_verification_account_holds_rather_than_releasing(self):
        self.admitted()
        self.materialize()
        held = self.refusal(self.hand_off)
        self.assertIn("UNKNOWN, unknown holds", held.message)
        self.assertFalse(self.gate()["open"])

    def test_the_seam_this_pass_cannot_attribute_is_refused_first(self):
        for changed in ({"control": None}, {"runner": None},
                        {"destination": None}):
            with self.subTest(member=sorted(changed)[0]):
                seam = Seam(control=self.control, context=self.context,
                            workspaces=self.workspaces, runner=self.runner,
                            declaration=self.declaration)
                for one, value in changed.items():
                    setattr(seam, one, value)
                held = self.refusal(retained_verification.advance_verification,
                                    self.jobs, seam, now=LATER)
                self.assertEqual(held.code, "capability")

    def test_another_deployments_control_store_is_refused(self):
        from baton_v12.worker_manager import ControlStore

        self.admitted()
        other = os.path.join(self.root, "other-control.sqlite3")
        with ControlStore.open(other, incarnation="other",
                               clock=lambda: NOW) as elsewhere:
            seam = Seam(control=elsewhere, context=self.context,
                        workspaces=self.workspaces, runner=self.runner,
                        declaration=self.declaration)
            held = self.refusal(self.materialize, seam=seam)
        self.assertIn("another deployment", held.message)

    def test_a_workspace_root_that_is_not_a_directory_is_refused(self):
        self.admitted()
        seam = Seam(control=self.control, context=self.context,
                    workspaces=os.path.join(self.workspaces, "absent"),
                    runner=self.runner, declaration=self.declaration)
        held = self.refusal(self.materialize, seam=seam)
        self.assertEqual(held.code, "path")


# -- 11. the gate, the scheduler and the status surface (K M1-M3) ------------


class TheGateTheSchedulerAndTheStatusSurfaceAgree(ExecutionCase):
    """K's review notes M1, M2 and M3, each as its own candidate case."""

    def test_the_status_reason_names_the_recovery_gate_rather_than_unknown(
            self):
        """M1: the operator text was `held: waiting on unknown (unknown)`."""
        from tools import job_observation

        self.admitted()
        operations = FakeOperations(authority_uuid=self.AUTHORITY)
        held = projection.stage_states(self.jobs, operations)
        state = held["recovery-D1/review"]
        gates = projection.gates_of(state["stage"], held)
        stage = {"gates": gates, "exchange": None}
        reason = job_observation._reason(stage, "blocked")
        self.assertIn(retained_recovery.GATE_UNAVAILABLE, reason)
        self.assertIn("recovery-D1", reason)
        self.assertNotIn("unknown (unknown)", reason)

    def test_the_dependency_gate_text_is_unchanged(self):
        """The other document shape still reads the way it always did."""
        from tools import job_observation

        stage = {"gates": [documents.dependency_gate(
            stage_id="job-a/implementation", state="claimed", open=False)],
            "exchange": None}
        self.assertEqual(job_observation._reason(stage, "blocked"),
                         "held: waiting on job-a/implementation (claimed)")

    def test_the_status_surface_stops_holding_once_the_gate_opens(self):
        from tools import job_observation

        self.whole_loop()
        operations = FakeOperations(authority_uuid=self.AUTHORITY)
        held = projection.stage_states(self.jobs, operations)
        state = held["recovery-D1/review"]
        gates = projection.gates_of(state["stage"], held)
        self.assertEqual([one["open"] for one in gates], [True])
        self.assertEqual(
            job_observation._reason({"gates": gates, "exchange": None},
                                    "blocked"),
            "held: blocker unknown")

    def test_the_scheduler_admit_refuses_a_closed_gate_directly(self):
        """M2: the refusal had no candidate case, only a reviewer's probe.

        DRIVEN AT THE SCHEDULER rather than through a tick, because that is
        the write-side guard: the projection's gate is the read-side answer
        and a race it loses is decided here. The pool is deliberately EMPTY --
        the gate is read before an allocation is created, so a refusal that
        reached a worker would be a different refusal.
        """
        self.admitted()
        stage, job = self.review_stage()
        pooled = self.pooled()
        held = self.refusal(pooled.admit, stage, job)
        self.assertIn("validated candidate execution handoff", held.message)
        self.assertIn(retained_recovery.GATE_UNAVAILABLE, held.message)
        self.assertIn("recovery-D1/review", held.message)

    def test_the_scheduler_admit_stops_refusing_once_the_handoff_is_valid(
            self):
        """The other half: the gate is no longer what refuses."""
        self.whole_loop()
        stage, job = self.review_stage()
        pooled = self.pooled()
        held = self.refusal(pooled.admit, stage, job)
        self.assertNotIn("validated candidate execution handoff",
                         held.message)
        self.assertNotIn(retained_recovery.GATE_UNAVAILABLE, held.message)

    def test_an_ordinary_stage_is_unaffected_by_the_recovery_gate(self):
        self.admitted()
        self.assertIsNone(retained_recovery.execution_gate(self.jobs,
                                                           "job-a"))

    def test_a_gate_with_no_predecessor_state_never_faults_a_fresh_attempt(
            self):
        """M3: `_over` read `gate["state"]`, which a recovery gate lacks."""
        from baton_v12.job_manager import fresh_attempt

        self.admitted()
        operations = FakeOperations(authority_uuid=self.AUTHORITY)
        held = projection.stage_states(self.jobs, operations)
        entry = held["recovery-D1/review"]
        self.assertFalse(fresh_attempt._over(entry, "blocked", held))
        self.assertFalse(fresh_attempt._over(entry, "queued", held))

    def test_a_fresh_attempt_of_a_recovery_job_refuses_before_any_effect(self):
        """And the path above stays unreachable, which is the other half."""
        from baton_v12.job_manager import fresh_attempt

        self.admitted()
        ports = self.stand_ins()
        held = self.refusal(
            fresh_attempt.admit, self.jobs, None,
            prior_job_id="recovery-D1", exclusion=ports["exclusion"],
            authorization=stage_b.WorkPort(self.authority),
            binding=ports["binding"], ownership=ports["ownership"])
        self.assertIn("requires retained-recovery", held.message)

    def pooled(self):
        """The real pooled surface, over this case's own Job store."""
        from baton_v12.job_manager import scheduler

        return scheduler.PooledManagerOperations(self.jobs, {},
                                                 resolved_principals={})

    def review_stage(self):
        """The successor's review ATTEMPT document and its Job, as projected.

        THE OPERAND THE TICK ACTUALLY PASSES. `manager._delegate` hands
        `PooledManagerOperations.admit` the live episode's attempt document --
        which carries the offer and attempt identities an allocation is keyed
        by -- so a case that handed it a stage row would be driving a surface
        the manager does not drive.
        """
        operations = FakeOperations(authority_uuid=self.AUTHORITY)
        held = projection.stage_states(self.jobs, operations)
        state = held["recovery-D1/review"]
        return dict(state["attempt"]), state["job"]


# -- 12. independent review judges substance ---------------------------------


class ThisManagerManufacturesNoVerdictAndReviewMayStillReject(ExecutionCase):
    """Structural checks alone cannot establish acceptance.

    THE SCRIPTED HALF, SAID OUT LOUD: both verdicts below are SCRIPTED. What
    they prove is that this recovery path writes neither of them and that the
    review stage's outcome is the reviewer's own, not that a reviewer judged
    this candidate well.
    """

    def test_the_handoff_establishes_no_acceptance_of_any_kind(self):
        self.whole_loop()
        handoff = retained_verification.handoff_of(self.jobs, "recovery-D1")
        self.assertNotIn("verdict", json.dumps(handoff))
        self.assertNotIn("accepted", json.dumps(handoff))
        # THE REVIEW STAGE IS QUEUED, NOT COMPLETED: nothing about this path
        # moves it to a terminal state.
        self.swept()
        operations = FakeOperations(authority_uuid=self.AUTHORITY)
        state = projection.stage_states(self.jobs,
                                        operations)["recovery-D1/review"]
        self.assertNotIn(state["state"], documents.TERMINAL_STAGE_STATES)

    def test_a_scripted_rejection_is_the_reviewers_own_outcome(self):
        self.whole_loop()
        report, operations = self.swept()
        operations.canonical_state("offer-recovery-D1/review", "attempt-1",
                                   "changes-requested")
        self.assertEqual(
            retained_verification.execution_readiness(
                self.jobs,
                retained_recovery.successor_of(self.jobs,
                                               "D1"))["review"],
            "releasable")
        # A REJECTION IS NOT THIS TRIGGER. No renewed failure, no analysis and
        # no owner item is created by a review outcome.
        self.assertIsNone(retained_verification.renewed_failure_of(
            self.jobs, "recovery-D1"))
        self.assertEqual(self.ticked(times=2), [])

    def test_a_scripted_acceptance_adds_no_record_to_this_path_either(self):
        self.whole_loop()
        before = retained_verification.successor_execution(self.jobs,
                                                           "recovery-D1")
        report, operations = self.swept()
        operations.canonical_state("offer-recovery-D1/review", "attempt-1",
                                   "completed")
        self.assertEqual(
            retained_verification.successor_execution(self.jobs,
                                                      "recovery-D1"),
            before)


# -- 13. the joined acceptance -----------------------------------------------
#
# WHAT MAKES THIS ONE DIFFERENT FROM EVERY CASE ABOVE. The cases above compose
# the three owner ports a deployment supplies -- host cessation, deployment
# binding, instance guard -- as stand-ins, which is correct at that boundary
# and is what `--owners` exists for. This one does not: it installs a real
# disposable instance with `tools.bootstrap`, builds the retained verification
# failure INTO that instance's own Job store and control store, and then runs
# the installed owner commands with NO `--owners` operand at all -- so the
# five ports are `tools.recovery_decision.owners`', composed over the
# instance's own emitted configuration, its own persisted identity and its own
# Authority. A composition error here would ship a non-functional owner
# command, which is exactly what Stage 1-B's review F3 asked to be covered.

from tests.tools.test_bootstrap import ValidFixture as _InstalledFixture

INSTANCE_OWNER = "baton.owner"
WRITER = stage_a.WRITER


class TheJoinedAcceptanceRunsTheShippedOwnersOnABootstrappedInstance(
        _InstalledFixture):
    """READ, DECIDE, BIND/ADMIT, SERVE, VERIFY, HAND OFF, REVIEW -- joined.

    HONESTLY LABELLED, because the contract asks for exactly that:

      the ANALYSIS is a SCRIPTED report. It proves that the orchestration
      carries the exact evidence and that the owner is shown what they must
      bind; it is not evidence of diagnostic quality;
      the REVIEWER is not run. What is proved is that the ordinary tick admits
      the configured independent review of the same candidate once the handoff
      is validated, and that this manager writes no verdict;
      everything else is real: a real installed instance, real stores, real
      retained bytes, the shipped owner commands, a real child process and a
      real manager tick.
    """

    instants = [NOW]

    def clock(self):
        return self.instants[-1]

    def setUp(self):
        from baton_v12.worker_manager import ControlStore
        from baton_v12.job_manager import submit
        from tests.job_manager.fixtures import job, stage
        from tools import bootstrap

        super().setUp()
        self.instants = [NOW]
        # THE INSTANCE, INSTALLED BY ITS OWN OWNER. `bootstrap.prepare`
        # composes the Authority, creates the Work in its own scope, grants
        # the selected owner `approve` there, and emits the one deployment
        # configuration the five shipped ports read.
        self.install_document = self.document(owner_participant=INSTANCE_OWNER,
            recovery_verification={"context": context_of(),
                                   "declaration": stage_a.analysis_declaration(),
                                   "destination": INSTANCE_OWNER})
        with open(os.devnull, "w") as quiet:
            self.installed = bootstrap.prepare(self.install_document,
                                               stream=quiet)
        self.places = bootstrap.layout(self.state)
        # THE DOCUMENT THE INSTALL CONSUMED, written where `bootstrap.install`
        # writes it, because that is where the SHIPPED binding port reads it
        # from when it adds this successor's binding: "an additive binding is
        # prepared from this instance's own install document". These bytes are
        # that document rather than a reconstruction of one.
        pathlib.Path(self.places["install_inputs"]).write_text(
            json.dumps(self.install_document, indent=2, sort_keys=True),
            encoding="utf-8")
        self.uuid = self.installed["configuration"]["authority_uuid"]
        self.jobs = JobStore.open(self.places["job_store"],
                                  authority_uuid=self.uuid,
                                  incarnation="joined-1", clock=self.clock)
        self.addCleanup(self.jobs.close)
        self.control = ControlStore.open(self.places["control_store"],
                                         incarnation="joined-1",
                                         clock=self.clock)
        self.addCleanup(self.control.close)
        # THE JOB'S OWN OPERANDS, TAKEN FROM THE WORKERS THIS INSTANCE
        # CONFIGURED. `stage_execution.servable_workers` is the selector the
        # admission asks, and what it compares is the submitted input, the
        # submitted policy and the stage's own profile against each worker's
        # declared deployment -- so a Job assembled out of this fixture's
        # defaults would be refused for the fixture's reason rather than
        # tested against the deployment's.
        from tools import stage_execution

        reviewer = [one for one in
                    self.installed["configuration"]["workers"]
                    if one["role"] == "review"][0]["deployment"]
        self.submitted = {
            "input_digest": stage_execution.job_input_identity(
                reviewer["input_manifest"]),
            "policy_digest": reviewer["policy_digest"],
            "profile_name": reviewer["profile_name"],
            "profile_digest": reviewer["profile_digest"]}
        held = job("job-a",
                   input_digest=self.submitted["input_digest"],
                   policy_digest=self.submitted["policy_digest"],
                   stages=[
                       stage("implementation", WORK_A,
                             profile_name=self.submitted["profile_name"],
                             profile_digest=self.submitted["profile_digest"]),
                       stage("review", WORK_A,
                             profile_name=self.submitted["profile_name"],
                             profile_digest=self.submitted["profile_digest"],
                             depends_on=[{"job_id": "job-a",
                                          "kind": "implementation"}])])
        held["control"] = {"profile": job_control.NATIVE_HANDOFF_PROFILE}
        submit(self.jobs, {"schema": documents.SUBMISSION_CONTROL_SCHEMA,
                           "submission_id": "sub-1", "jobs": [held]})
        self.custody = os.path.join(self.state, "retained-custody")
        os.makedirs(self.custody)
        self.declaration = stage_a.analysis_declaration()
        self.key = self.delivered()
        # THE PRIVATE VERIFICATION WORKSPACE ROOT THIS INSTANCE OWNS, composed
        # by the shipped helper rather than chosen here.
        self.workspaces = recovery_execution.workspaces_root(self.state)
        self.ran = CountingRun()
        self.runner = recovery_execution.CommandRunner(
            {"root": os.path.realpath(self.state),
             "job_store": os.path.realpath(self.places["job_store"]),
             "control_store": os.path.realpath(self.places["control_store"]),
             "authority_store": os.path.realpath(
                 self.places["authority_store"]),
             "authority_uuid": self.uuid},
            clock=lambda: LATER, run=self.ran)
        self.context = context_of()
        self.seam = Seam(control=self.control, context=self.context,
                         workspaces=self.workspaces, runner=self.runner,
                         declaration=self.declaration,
                         destination=INSTANCE_OWNER)

    # -- the retained failure, in THIS instance's own stores ----------------

    def _attempt(self, attempt_id, participant, principal):
        self.control._connection.execute(
            "INSERT INTO attempts (runtime_attempt_id, adapter_name, "
            "adapter_digest, profile_digest, created_at, work_id, "
            "authority_uuid, assignment_participant, assignment_generation, "
            "assignment_claim_event_seq, assignment_principal, "
            "assignment_scope, assignment_role, assignment_grant, "
            "assignment_policy_generation) VALUES (?, 'adapter', "
            "'adapter-digest', 'profile-digest', ?, ?, ?, ?, 1, 1, ?, "
            "'scope', 'role', 'grant', 1)",
            (attempt_id, NOW, WORK_A, self.uuid, participant, principal))
        # THE WORKSPACE OBJECT THIS ATTEMPT'S START CONTENDED FOR, real:
        # a directory this fixture makes, named by its own device and inode,
        # which is how the Worker Manager pins one.
        place = os.path.join(self.state, "attempt-workspaces", attempt_id)
        os.makedirs(place)
        measured = os.stat(place)
        source = os.stat(self.state)
        self.control._connection.execute(
            "UPDATE attempts SET runtime_id = ?, execution_runtime = "
            "'destroyed', worker_disposition = 'completed', output = "
            "'frozen', cleanup = 'retained', workspace_device = ?, "
            "workspace_inode = ?, source_device = ?, source_inode = ? "
            "WHERE runtime_attempt_id = ?",
            ("runtime-" + attempt_id, measured.st_dev, measured.st_ino,
             source.st_dev, source.st_ino, attempt_id))
        self._settled(attempt_id)
        return attempt_id

    def _settled(self, attempt_id):
        """ACQUIRE, LAUNCH, BIND AND RETURN this attempt's workspace token.

        THROUGH THE RESOURCE OWNER'S OWN OPERATIONS, because the shipped
        `HostExclusion` reads exactly what they journal: an absent token is
        "uncertainty about a resource rather than evidence it was returned",
        and a fixture that left one absent would be asserting against that
        uncertainty instead of against the admission. So the attempt's start
        really acquired the workspace, really bound a container, and the
        resource is really returned under positive cessation -- which is the
        host state a terminal ending leaves and the one a successor is
        admitted against.
        """
        from baton_v12.worker_manager import attempts as held_attempts
        from baton_v12.worker_manager import tokens

        row = dict(self.control._connection.execute(
            "SELECT * FROM attempts WHERE runtime_attempt_id = ?",
            (attempt_id,)).fetchone())
        start = held_attempts._start_operation_id(row)
        domain = tokens.domain_of("workspace", tokens.workspace_identity(row))
        token = tokens.acquire(self.control, domain, operation=start,
                               execution=attempt_id, attempt=attempt_id)
        tokens.journal_launch(self.control, token, start)
        container = row["runtime_id"]
        tokens.bind_container(
            self.control,
            tokens.token_of(self.control, domain, token["generation"]),
            container, launch=start)
        tokens.returned(
            self.control,
            tokens.token_of(self.control, domain, token["generation"]),
            cessation={"domain": domain, "generation": token["generation"],
                       "launch": start, "container": container,
                       "stopped": True, "helpers": []})
        return token

    def _custody(self, attempt_id, name, payload):
        from baton_v12.contracts import digest_of_bytes

        place = os.path.join(self.custody, f"{attempt_id}--{name}")
        os.makedirs(place)
        with open(os.path.join(place, "result.json"), "wb") as writing:
            writing.write(payload)
        entries = [{"path": "result.json", "bytes": len(payload),
                    "content_digest": digest_of_bytes(payload)}]
        return place, {"entries": entries, "entry_count": 1,
                       "total_bytes": len(payload),
                       "tree_digest": digest(entries)}

    def _frozen(self, attempt_id, *, participant, disposition, output,
                content, place):
        from baton_v12.worker_manager import retain_manifest

        document = dict(
            driver_vector(), result_id="result-" + attempt_id,
            disposition=disposition,
            assignment_ref={"work_ref": {"authority_uuid": self.uuid,
                                         "work_id": WORK_A},
                            "participant": participant, "generation": 1},
            outputs=[output])
        document.pop("manifest_digest")
        document["manifest_digest"] = digest(document)
        kept = retain_manifest(self.control, document,
                               "resultManifest")["digest"]
        self.control._connection.execute(
            "INSERT INTO outputs (runtime_attempt_id, result_id, "
            "disposition, manifest_digest, freeze_operation_id, frozen_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (attempt_id, document["result_id"], disposition, kept,
             "freeze-" + attempt_id, NOW))
        self.control._connection.execute(
            "INSERT INTO output_artifacts (runtime_attempt_id, output_name, "
            "artifact_id, media_type, bytes, content_digest, locator) VALUES "
            "(?, ?, ?, ?, ?, ?, ?)",
            (attempt_id, output["name"], output["artifact"]["artifact_id"],
             output["artifact"]["media_type"], content["total_bytes"],
             content["tree_digest"], output["artifact"]["locator"]))
        return document

    def _output(self, attempt_id, name, *, kind, content, metadata, place):
        return {"name": name, "type": kind, "status": "present",
                "content_manifest": content,
                "artifact": {"artifact_id": f"{attempt_id}:{name}",
                             "media_type": "application/json",
                             "bytes": content["total_bytes"],
                             "content_digest": content["tree_digest"],
                             "locator": "file://" + place},
                "result_metadata": metadata}

    def delivered(self):
        """Stage 1-A's whole path, against this instance's own stores."""
        attempt_id = self._attempt("writer-attempt-1", WRITER,
                                   "writer-principal-1")
        payload = stage_a.worker_result()
        place, content = self._custody(attempt_id, "proposal", payload)
        head = json.loads(payload)["head"]
        self.original_argv = ["bash", "-c", "exec python3 -m unittest -v x\n"]
        metadata = {
            failure_analysis.CANDIDATE_CLAIM: {
                "base": driver_base(), "head": head,
                "transport": "bundle/candidate.bundle",
                "recap": "the candidate changed the source and its own "
                         "verification failed"},
            failure_analysis.ORDINARY_TESTS: {
                "argv": self.original_argv, "base": driver_base(),
                "head": head, "status": 1,
                "task_digest": "sha256:" + "7" * 64,
                "task_id": "w385625-joined-1"}}
        self.failed = self._frozen(
            attempt_id, participant=WRITER, disposition="unable",
            output=self._output(attempt_id, "proposal",
                                kind="git-change-proposal", content=content,
                                metadata=metadata, place=place),
            content=content, place=place)
        self.custody_place = place
        self.control._connection.execute(
            "UPDATE attempts SET verification = 'failed' WHERE "
            "runtime_attempt_id = ?", (attempt_id,))
        seen = failure_analysis.observe_terminal_failure(
            self.jobs, self.control, stage_id="job-a/implementation",
            episode=1, attempt_id=attempt_id, declaration=self.declaration,
            now=NOW)
        key = seen["failure"]["failure_key"]
        # THE SCRIPTED ANALYSIS, said out loud: a real frozen report by the
        # declared analysis participant, whose CONTENT this fixture wrote.
        report = stage_a.analysis_report(key, seen["intent"]["input_digest"],
                                         proposed_verification={
                                             "argv": CORRECTED,
                                             "context_digest":
                                                 retained_verification
                                                 .context_digest(
                                                     context_of())})
        analysis_id = self._attempt("analysis-attempt-1", stage_a.ANALYST,
                                    "analysis-principal-1")
        body = json.dumps(report, indent=2, sort_keys=True).encode("utf-8")
        place, content = self._custody(analysis_id, "analysis", body)
        self._frozen(analysis_id, participant=stage_a.ANALYST,
                     disposition="completed",
                     output=self._output(
                         analysis_id, failure_analysis.ANALYSIS_OUTPUT,
                         kind="record-output", content=content,
                         metadata={failure_analysis.REPORT_SCHEMA: report},
                         place=place),
                     content=content, place=place)
        failure_analysis.admit_dispatch(self.jobs, self.control, key=key,
                                        analysis_attempt_id=analysis_id,
                                        now=NOW)
        failure_analysis.deliver_analysis(self.jobs, self.control, key=key,
                                          destination=INSTANCE_OWNER,
                                          now=NOW)
        self.report = report
        return key

    # -- the SHIPPED owner commands, with no `--owners` operand --------------

    def argv(self, command, *extra):
        return [command,
                "--store", self.places["job_store"],
                "--authority-uuid", self.uuid,
                "--incarnation", "joined-owner",
                "--control", self.places["control_store"],
                "--authority", self.places["authority_store"],
                "--instance", self.state,
                "--failure", self.key,
                *extra]

    def command(self, *argv, clock=None):
        from tools import job_manager

        said = io.StringIO()
        code = job_manager.main(list(argv), clock=clock or (lambda: NOW),
                                stream=said)
        text = said.getvalue()
        return code, (json.loads(text) if text.strip() else None)

    def read(self, *extra):
        code, document = self.command(*self.argv("recovery-item", *extra))
        self.assertEqual(code, 0)
        return document

    def approve(self, item, *, decision_id="D1", stages=None):
        expected = dict(item["expected"])
        flat = ["--decision-id=" + decision_id,
                "--participant=" + INSTANCE_OWNER,
                "--expect-failure-digest=" + expected["failure_digest"],
                "--expect-report-digest=" + expected["report_digest"],
                "--expect-candidate-base=" + expected["candidate_base"],
                "--expect-candidate-head=" + expected["candidate_head"],
                "--expect-candidate-digest="
                + expected["candidate_content_digest"],
                "--context-digest="
                + retained_verification.context_digest(self.context),
                "--profile=" + item["profile"]["profile"],
                "--profile-digest=" + item["profile"]["digest"]]
        for word in expected["original_argv"]:
            flat.append("--original-verification=" + word)
        for word in CORRECTED:
            flat.append("--corrected-verification=" + word)
        for word in (list(retained_recovery.FULL_STAGES) if stages is None
                     else stages):
            flat.append("--stage=" + word)
        return self.command(*self.argv("recovery-decide", "--approve", *flat))

    def refusal(self, call, *operands, **named):
        with self.assertRaises(ContractRefusal) as caught:
            call(*operands, **named)
        return caught.exception

    def swept(self, *, now=None, operations=None):
        now = now if now is not None else LATER
        operations = (operations if operations is not None
                      else FakeOperations(authority_uuid=self.uuid))
        if now > self.instants[-1]:
            self.instants.append(now)
        return sweep(self.jobs, operations, now=now), operations

    # -- the joined proof ---------------------------------------------------

    def serving_recovery(self):
        from tools import stage_execution
        from tests.tools.test_single_worker import Engine
        given = json.loads(pathlib.Path(self.places["configuration"]).read_text())
        operations = stage_execution.operations_from(
            given, self.jobs, self.control, engine_run=Engine(),
            credential_provider=lambda provider, reference: self.secret,
            clock=lambda: LATER, checkout=self.checkout)
        self.addCleanup(operations.close)
        self.assertIsNotNone(operations.recovery_verification)
        operations.recovery_verification.runner._run = self.ran
        return operations

    def test_configuration_refuses_unknown_members_and_context_revision(self):
        import copy
        from tools import bootstrap
        for changed in ("member", "revision"):
            given = copy.deepcopy(self.install_document)
            if changed == "member":
                given["recovery_verification"]["unexpected"] = True
            else:
                given["recovery_verification"]["context"]["schema"] = "unknown/99"
            with self.subTest(changed=changed), self.assertRaises(bootstrap.BootstrapRefusal):
                bootstrap.validated(given)

    def test_the_whole_loop_runs_on_the_instance_through_its_own_owners(self):
        item = self.read("--participant", INSTANCE_OWNER)
        # THE OWNER IS AUTHORIZED BY THE INSTANCE'S OWN AUTHORITY, in the
        # Work's own scope, through the shipped `OwnerAuthorization`.
        self.assertTrue(item["authorization"]["holds"], item["authorization"])
        self.assertEqual(item["authorization"]["effective_scope"],
                         item["authorization"]["effective_scope"])
        self.assertEqual(item["original_verification"]["argv"],
                         self.original_argv)
        self.assertTrue(item["evidence"]["valid"])
        self.assertEqual(item["proposed_correction"]["argv"], CORRECTED)

        code, said = self.approve(item)
        self.assertEqual(code, 0, said)
        self.assertTrue(said["admitted"], said)
        successor = said["successor"]
        self.assertEqual(successor["job_id"], "recovery-D1")
        self.assertEqual(successor["stages"], ["verification", "review"])
        # THE DEPLOYMENT ITSELF BOUND IT AND ITS OWN SELECTOR CAN SERVE IT.
        self.assertEqual(successor["binding"]["disposition"], "added")
        self.assertEqual(successor["binding"]["job_work_id"], WORK_A)
        # THE DEPLOYMENT'S OWN SELECTOR NAMED THE REVIEWER IT CONFIGURED.
        self.assertEqual(successor["binding"]["serving"],
                         {"review": ["review-a"]})
        self.assertEqual(successor["work"]["disposition"], "reused")

        # Drive the shipped composition and the actual manager restart/tick path.
        from baton_v12.job_manager import manager
        self.instants.append(LATER)
        # The retained-failure fixture has no live original execution. Fence
        # its otherwise queued placeholder before exercising the real server.
        from baton_v12.job_manager import cancellation
        cancellation.request(self.jobs, job_id="job-a", reason="fixture retained original has ended")
        for ordinal in range(3):
            operations = self.serving_recovery()
            manager.reconcile(self.jobs, operations, now=LATER)
            operations.close()
            self.assertEqual(retained_recovery.execution_gate(self.jobs, "recovery-D1")["open"], ordinal == 2)
        self.assertEqual(len(self.ran.calls), 1)
        self.assertEqual(self.ran.calls[0]["argv"], CORRECTED)

        result = retained_verification.execution_result_of(self.jobs,
                                                           "recovery-D1")
        self.assertEqual(result["outcome"], "passed")
        self.assertEqual(result["exit_status"], 0)
        self.assertTrue(result["workspace"]["candidate_unchanged"])

        handoff = retained_verification.handoff_of(self.jobs, "recovery-D1")
        self.assertEqual(handoff["review_stage_id"], "recovery-D1/review")
        self.assertEqual(handoff["candidate"]["content_digest"],
                         directory_manifest(
                             self.custody_place)["tree_digest"])

        # Separate scheduler contract check: FakeOperations records admission.
        # The real serving/restart proof above ends at the durable handoff;
        # no reviewer container is launched by this fixture.
        gate = retained_recovery.execution_gate(self.jobs, "recovery-D1")
        self.assertTrue(gate["open"])
        self.assertEqual(gate["reason"], retained_recovery.GATE_VALIDATED)
        report, operations = self.swept()
        self.assertIn(("admit", "recovery-D1/review"), operations.calls)
        # ZERO IMPLEMENTATION ACTS OF THE SUCCESSOR, AND ZERO COURIER ACTS:
        # every act above is an operation of the installed product.
        self.assertEqual([call for call in operations.calls
                          if call[1].startswith("recovery-")],
                         [("admit", "recovery-D1/review")])
        self.assertEqual(
            [row["kind"] for row in submission.stages_of(self.jobs,
                                                         "recovery-D1")],
            ["review"])
        # THE ORIGINAL FAILURE AND ITS CANDIDATE ARE UNCHANGED.
        self.assertEqual(
            failure_analysis.failure_of(self.jobs,
                                        self.key)["verification"]["argv"],
            self.original_argv)
        self.assertIsNotNone(retained_verification.handoff_of(self.jobs,
                                                              "recovery-D1"))

    def test_the_default_factory_refuses_a_store_the_instance_does_not_own(
            self):
        """The shipped `_agreeing` checks, over a real installed instance."""
        from contextlib import redirect_stderr
        from baton_v12.worker_manager import ControlStore

        item = self.read("--participant", INSTANCE_OWNER)
        for flag in ("--store", "--control", "--authority"):
            with self.subTest(flag=flag):
                other = os.path.join(self.root, "other-" + flag[2:]
                                     + ".sqlite3")
                if flag == "--store":
                    with JobStore.open(other, authority_uuid=self.uuid,
                                       incarnation="other",
                                       clock=lambda: NOW):
                        pass
                elif flag == "--control":
                    with ControlStore.open(other, incarnation="other",
                                           clock=lambda: NOW):
                        pass
                argv = self.argv("recovery-item", "--participant",
                                 INSTANCE_OWNER)
                argv[argv.index(flag) + 1] = other
                said = io.StringIO()
                with redirect_stderr(said):
                    code = self.command(*argv)[0]
                self.assertEqual(code, 1)
                self.assertIn("owns", said.getvalue())

    def test_an_unauthorized_participant_is_refused_by_the_real_authority(
            self):
        from contextlib import redirect_stderr

        item = self.read("--participant", "baton.reviewer")
        self.assertFalse(item["authorization"]["holds"])
        said = io.StringIO()
        with redirect_stderr(said):
            code, answer = self.command(
                *[one.replace(INSTANCE_OWNER, "baton.reviewer")
                  for one in self.approve_argv(item)])
        self.assertEqual(code, 1)
        self.assertIsNone(retained_recovery.decision_of(self.jobs, "D1"))
        self.assertIsNone(self.jobs._connection.execute(
            "SELECT job_id FROM jobs WHERE job_id = 'recovery-D1'"
        ).fetchone())

    def approve_argv(self, item, *, decision_id="D1"):
        expected = dict(item["expected"])
        flat = ["--decision-id=" + decision_id,
                "--participant=" + INSTANCE_OWNER,
                "--expect-failure-digest=" + expected["failure_digest"],
                "--expect-report-digest=" + expected["report_digest"],
                "--expect-candidate-base=" + expected["candidate_base"],
                "--expect-candidate-head=" + expected["candidate_head"],
                "--expect-candidate-digest="
                + expected["candidate_content_digest"],
                "--context-digest="
                + retained_verification.context_digest(self.context),
                "--profile=" + item["profile"]["profile"],
                "--profile-digest=" + item["profile"]["digest"]]
        for word in expected["original_argv"]:
            flat.append("--original-verification=" + word)
        for word in CORRECTED:
            flat.append("--corrected-verification=" + word)
        for word in retained_recovery.FULL_STAGES:
            flat.append("--stage=" + word)
        return self.argv("recovery-decide", "--approve", *flat)

    # -- the Authority assignment, ended and re-claimed ---------------------

    def authority(self):
        from baton_v12.authority import Authority

        held = Authority.open(self.places["authority_store"],
                              expected_authority_uuid=self.uuid)
        self.addCleanup(held.dispose)
        return held

    def test_host_settlement_alone_does_not_end_the_authority_assignment(self):
        """K W385695 D4, as it applies to this joined acceptance.

        THE TWO AXES ARE SEPARATE AND THE ORDER IS THE POINT. REC-2: "Docker
        termination and positive absence discharge physical ownership. Workflow
        claim release and resource/capacity release are not equivalent." So
        this case establishes the host side first -- the runtime destroyed, the
        cleanup settled, the workspace token RETURNED through the resource
        owner's own operations -- and then asks the Authority whether the
        prior assignment is over. It is not. It ends only by its own supported
        operation, and what follows is a FRESH claim on the SAME reused Work:
        a new generation, taken by its own session, with no impersonation of
        the participant whose assignment ended and no takeover of it.
        """
        from baton_v12.worker_manager import attempts as held_attempts

        # THE HOST SIDE, POSITIVE. This is the fixture's own state and it is
        # what the shipped `HostExclusion` reads.
        runtime = held_attempts.attempt_runtime_of(self.control,
                                                   "writer-attempt-1")
        self.assertEqual(runtime["execution_runtime"], "destroyed")
        self.assertEqual(runtime["cleanup"], "retained")

        authority = self.authority()
        session = authority.session("baton.impl-a")
        mine = session.claim({"work_id": WORK_A,
                              "operation_id": "joined-claim-1"})["assignment"]
        # HOST SETTLEMENT IS ALREADY COMPLETE AND THE CLAIM IS STILL LIVE.
        self.assertEqual(authority.assignment_of(WORK_A)["participant"],
                         "baton.impl-a")
        self.assertEqual(authority.assignment_of(WORK_A)["generation"],
                         mine["generation"])

        # AND IT ENDS BY ITS OWN SUPPORTED OPERATION, not by the host's.
        session.end({"expect": mine, "operation_id": "joined-end-1",
                     "disposition": "release",
                     "reason": "the retained verification failure is the "
                               "owner's to dispose of"})
        self.assertIsNone(authority.assignment_of(WORK_A))

        # THEN A FRESH CLAIM ON THE REUSED WORK, which is a new generation of
        # the same Work rather than a revival of the old assignment.
        again = session.claim({"work_id": WORK_A,
                               "operation_id": "joined-claim-2"})["assignment"]
        self.assertNotEqual(again["generation"], mine["generation"])
        self.assertEqual(authority.project_work(WORK_A)["status"], "open")
        # AND THE RECOVERY RUNS UNDER THAT SAME REUSED WORK, never under one
        # it minted and never as the participant whose assignment ended.
        item = self.read("--participant", INSTANCE_OWNER)
        code, said = self.approve(item)
        self.assertEqual(code, 0, said)
        self.assertEqual(said["successor"]["work_id"], WORK_A)
        self.assertEqual(said["successor"]["work"]["disposition"], "reused")
        self.assertEqual(said["decision"]["owner"]["endpoint"],
                         INSTANCE_OWNER)
        self.assertNotEqual(said["decision"]["owner"]["endpoint"],
                            "baton.impl-a")

    def test_the_admission_rests_on_positive_cessation_and_a_returned_token(
            self):
        """Unknown holds: the one fact removed is the one that refuses."""
        from baton_v12.worker_manager import tokens, attempts as held_attempts

        item = self.read("--participant", INSTANCE_OWNER)
        row = dict(self.control._connection.execute(
            "SELECT * FROM attempts WHERE runtime_attempt_id = ?",
            ("writer-attempt-1",)).fetchone())
        domain = tokens.domain_of("workspace", tokens.workspace_identity(row))
        start = held_attempts._start_operation_id(row)
        generation = tokens.generation_of(self.control, domain,
                                          execution="writer-attempt-1",
                                          operation=start)
        self.assertIsNotNone(generation)
        self.assertTrue(tokens.token_of(self.control, domain,
                                        generation)["returned"])
        # THE CLEANUP THIS HOST STILL OWES IS A HOLD, through the SHIPPED
        # port, with no stand-in anywhere on the path.
        self.control._connection.execute(
            "UPDATE attempts SET cleanup = 'pending' WHERE "
            "runtime_attempt_id = ?", ("writer-attempt-1",))
        from contextlib import redirect_stderr

        said = io.StringIO()
        with redirect_stderr(said):
            code, answer = self.command(*self.approve_argv(item,
                                                           decision_id="D9"))
        self.assertEqual(code, 1)
        self.assertIn("cleanup is 'pending'", said.getvalue())
        self.assertFalse(answer["admitted"])
        # THE OWNER'S OWN ACT HAPPENED AND THE ADMISSION DID NOT, which is
        # both facts rather than one.
        self.assertEqual(answer["decision"]["disposition"], "approved")
        self.assertIsNone(answer["successor"])

    def test_the_shipped_seam_factory_composes_over_this_instance(self):
        """`tools.recovery_execution.verification_seam`, over the real root.

        THE OTHER SHIPPED FACTORY ON THIS PATH. `recovery_decision.owners`
        composes the five owner ports; this composes the verification seam, and
        a composition error in either would ship something non-functional. So
        it is driven here over this instance's own layout and then PROVED by
        the validator the pass itself uses.
        """
        seam = recovery_execution.verification_seam({
            "instance": self.state,
            "control_handle": self.control,
            "context": {one: CONTEXT[one] for one in CONTEXT},
            "declaration": self.declaration,
            "destination": INSTANCE_OWNER,
            "clock": lambda: LATER})
        held = retained_verification.check_verification_seam(seam)
        self.assertEqual(held["destination"], INSTANCE_OWNER)
        self.assertEqual(
            retained_verification.context_digest(held["context"]),
            retained_verification.context_digest(self.context))
        # THE WORKSPACE ROOT IS THIS INSTANCE'S OWN AND IS PRIVATE.
        self.assertEqual(
            held["workspaces"],
            os.path.join(os.path.realpath(self.state),
                         recovery_execution.DEFAULT_WORKSPACES))
        self.assertEqual(os.stat(held["workspaces"]).st_mode & 0o777, 0o700)
        self.assertEqual(held["runner"].instance()["control_store"],
                         os.path.realpath(self.places["control_store"]))
        # AND IT DRIVES THE WHOLE LOOP, the shipped composition end to end.
        item = self.read("--participant", INSTANCE_OWNER)
        self.assertEqual(self.approve(item)[0], 0)
        for _ in range(3):
            retained_verification.advance_verification(self.jobs, seam,
                                                       now=LATER)
        self.assertIsNotNone(retained_verification.handoff_of(self.jobs,
                                                              "recovery-D1"))


# -- 14. the approved finite control, unchanged ------------------------------


class TheApprovedBoundsAreTheOwnersExactPublishedDefinition(
        unittest.TestCase):
    """M385612's two profiles, by value, and nothing of this slice's own.

    NO NUMBER IN THIS SLICE IS A LITERAL. Every bound the execution enforces is
    read out of the owner-approved definition records the product holds and
    proves at import; this class is what binds those resolved values to the
    contract's own table, so a build that drifted would fail here rather than
    quietly verify under a ceiling nobody approved.
    """

    def test_the_successor_bounds_and_clock_origins_are_the_approved_ones(
            self):
        held = retained_recovery.resolved_profile()
        self.assertEqual(held["profile"], "stage1-verification-review/1")
        self.assertEqual(held["digest"],
                         "sha256:" + stage_b.APPROVED_PROFILE_DIGEST)
        self.assertEqual(held["units"], "seconds")
        self.assertEqual(held["overall_job_seconds"], 9960)
        self.assertTrue(held["overall_job_includes_queue"])
        self.assertEqual(held["overall_job_origin"], "accepted_admission")
        self.assertEqual(held["each_stage_seconds"], 4800)
        self.assertEqual(held["each_stage_origin"], "stage_admission")
        self.assertEqual(held["verification_command_seconds"], 900)
        self.assertEqual(held["verification_command_origin"], "command_start")
        self.assertTrue(held["verification_command_covers_review"])
        self.assertEqual(held["review_provider_invocation_seconds"], 3600)
        self.assertEqual(held["review_provider_invocation_origin"],
                         "invocation_start")
        self.assertEqual(held["automatic_retries"], 0)
        self.assertEqual(held["automatic_corrections"], 0)

    def test_the_analysis_profile_is_untouched_by_this_slice(self):
        held = failure_analysis.resolved_profile()
        self.assertEqual(held["profile"], "stage1-analysis/1")
        self.assertEqual(held["digest"],
                         "sha256:" + stage_a.APPROVED_PROFILE_DIGEST)
        self.assertEqual(held["overall_job_seconds"], 4800)
        self.assertEqual(held["stage_seconds"], 4800)
        self.assertEqual(held["provider_invocation_seconds"], 3600)
        self.assertEqual(held["automatic_retries"], 0)
        self.assertEqual(held["automatic_corrections"], 0)

    def test_the_existing_bounded_shutdown_attempt_is_unchanged(self):
        """LIM-5's 120 s, and an unresolved cessation keeps the hold."""
        self.assertEqual(cancellation.SHUTDOWN_BOUND_SECONDS, 120)

    def test_this_slice_adds_no_profile_and_widens_none(self):
        self.assertEqual(sorted(retained_recovery.SUCCESSOR_PROFILES),
                         ["stage1-verification-review/1"])
        self.assertEqual(sorted(failure_analysis.ANALYSIS_PROFILES),
                         ["stage1-analysis/1"])
        # AND THE EXECUTION'S OWN CEILING IS THE PROFILE'S, not a constant of
        # this module: there is no per-command number in
        # `retained_verification` at all.
        source = pathlib.Path(
            retained_verification.__file__).read_text(encoding="utf-8")
        for number in ("900", "4800", "9960", "3600"):
            self.assertNotIn("= " + number, source)


from tests.tools.test_stage_execution import ComposedOneJobCase as _ComposedRecoveryCase


class RetainedRecoveryReachesTheIndependentReviewer(_ComposedRecoveryCase):
    """Real workload/custody/Authority; engine and provider boundary fakes."""

    from tests.tools.test_bootstrap import ValidFixture as _BootstrapFixture
    stage_worker = _BootstrapFixture.stage_worker
    workers = _BootstrapFixture.workers
    job = _BootstrapFixture.job

    def setUp(self):
        from tools import bootstrap
        from tests.job_manager import fixtures
        self.now = fixtures.NOW
        super().setUp()
        self.state = os.path.join(self.root, "recovery-instance")
        self.places = bootstrap.layout(self.state)
        bootstrap.persist_identity(self.places, self.config["authority_uuid"])
        self.install_document = self._BootstrapFixture.document(
            self, owner_participant=INSTANCE_OWNER,
            jobs=[self.job(work_id=self.work, base=self.base)],
            recovery_verification={"context": context_of(),
                                   "declaration": stage_a.analysis_declaration(),
                                   "destination": INSTANCE_OWNER})
        with open(os.devnull, "w") as quiet:
            self.installed = bootstrap.prepare(self.install_document, stream=quiet)
        pathlib.Path(self.places["install_inputs"]).write_text(json.dumps(self.install_document))
        self.authority_path = self.places["authority_store"]
        self.config["authority_store"] = self.authority_path

    def stores(self, incarnation):
        from baton_v12.worker_manager import ControlStore
        from tests.job_manager import fixtures
        jobs = JobStore.open(self.places["job_store"],
                             authority_uuid=self.config["authority_uuid"],
                             incarnation=incarnation, clock=lambda: self.now)
        control = ControlStore.open(self.places["control_store"], incarnation=incarnation,
                                    clock=lambda: self.now)
        self.addCleanup(jobs.close)
        self.addCleanup(control.close)
        return jobs, control

    def composed_document(self, **members):
        return json.loads(pathlib.Path(self.places["configuration"]).read_text())

    def mounted_view(self, role, attempt_id, roots):
        view = super().mounted_view(role, attempt_id, roots)
        if role == "review":
            # A real input mount contains a regular file. The inherited
            # daemon-free view uses links; the workload correctly refuses
            # links for this bounded document, so copy the pinned input bytes.
            path = pathlib.Path(view["inputs"], "recovery-review.json")
            if path.is_symlink():
                data = path.read_bytes()
                path.unlink()
                path.write_bytes(data)
        return view

    def provider(self, edits=None, status=0):
        import claude_agent
        actual = super().provider(edits=edits, status=status)
        def run(argv, **options):
            if argv[0] == claude_agent.PROVIDER_PROGRAM and "review-report.json" in (edits or {}):
                inputs = pathlib.Path(claude_agent.INPUT_ROOT)
                # Scripted review reads the delivered candidate and verifier
                # account at the provider boundary, not a synthetic receipt.
                self.assertEqual((inputs / "source" / "harness.py").read_text(), "raise SystemExit(1)\n")
                evidence = json.loads((inputs / "recovery-review.json").read_text())
                self.assertEqual(evidence["handoff_digest"], digest(evidence["handoff"]))
                self.assertEqual(evidence["handoff"]["verification"]["outcome"], "passed")
                self.assertIn(evidence["handoff_digest"], " ".join(argv))
                self.examined += 1
            return actual(argv, **options)
        return run

    def connected_review(self, verdict="accepted", evidence="valid", review_only=False, drift=False, restart=False):
        from baton_v12.job_manager import submit, sweep
        from tools import stage_execution
        from baton_v12.worker_manager import frozen_output_of
        from tests.job_manager import fixtures

        self.examined = 0
        jobs, control, operations = self.serving()
        submit(jobs, self.submission)
        self.drive(jobs, operations, "implementation", "waiting")
        attempt = self.only_attempt(operations, "implementation")
        self.assertEqual(self.turn(control, "implementation", attempt,
                                   self.mounted(operations, "implementation", attempt),
                                   edits={"harness.py": "raise SystemExit(1)\n"}), 0)
        for _ in range(12):
            sweep(jobs, operations, now=self.now)
        frozen = frozen_output_of(control, attempt)
        self.assertEqual(frozen["disposition"], "unable")
        original_custody = frozen["artifacts"][0]["locator"][len("file://"):]
        original_bytes = directory_manifest(original_custody)

        line = operations.deployment.line_for("job-a")
        self.assertIsNone(line["current_checkpoint_id"])
        # Reuse the accepted finite analysis endpoint; this probe targets
        # reviewer execution, not diagnostic quality. No custody or Authority
        # receipt is synthesized: the original producer above ran its workload.
        declaration = stage_a.analysis_declaration()
        seen = failure_analysis.observe_terminal_failure(
            jobs, control, stage_id="job-a/implementation", episode=1,
            attempt_id=attempt, declaration=declaration, now=self.now)
        self.key = seen["failure"]["failure_key"]
        failure_analysis.deliver_endpoint(jobs, control, key=self.key,
            outcome="analysis-failed", why="scripted analysis endpoint for focused reviewer probe",
            destination=INSTANCE_OWNER, now=self.now)
        self.uuid = self.config["authority_uuid"]
        self.context = context_of()
        owner = TheJoinedAcceptanceRunsTheShippedOwnersOnABootstrappedInstance
        argv = owner.argv(self, "recovery-item", "--participant", INSTANCE_OWNER)
        code, item = owner.command(self, *argv, clock=lambda: self.now)
        self.assertEqual(code, 0)
        expected = item["expected"]
        flags = ["--approve", "--decision-id=D1", "--participant=" + INSTANCE_OWNER,
                 "--profile=" + item["profile"]["profile"], "--profile-digest=" + item["profile"]["digest"],
                 "--context-digest=" + retained_verification.context_digest(self.context)]
        for flag, key in (("failure-digest", "failure_digest"), ("report-digest", "report_digest"),
                          ("candidate-base", "candidate_base"), ("candidate-head", "candidate_head"),
                          ("candidate-digest", "candidate_content_digest")):
            if expected[key] is not None:
                flags.append("--expect-" + flag + "=" + expected[key])
        flags.extend("--original-verification=" + arg for arg in expected["original_argv"])
        flags.extend("--corrected-verification=" + arg for arg in ["python3", "-c", "print('corrected verifier')"])
        flags.extend("--stage=" + stage for stage in retained_recovery.FULL_STAGES)
        code, answer = owner.command(self, *owner.argv(self, "recovery-decide", *flags), clock=lambda: self.now)
        self.assertEqual(code, 0, answer)
        self.assertTrue(answer["admitted"], answer)
        operations.close()
        operations = self._composed = stage_execution.operations_from(
            self.composed_document(), jobs, control, engine_run=self.engine,
            credential_provider=lambda provider, reference: self.secret,
            clock=lambda: self.now, checkout=self.checkout)
        self.addCleanup(operations.close)
        if drift:
            subprocess.run(["git", "-C", line["line_path"], "checkout", "--detach", self.base],
                           env=self.environment(), check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        ran = CountingRun()
        operations.recovery_verification.runner._run = ran
        recovery_job = "recovery-D1"
        if review_only:
            for _ in range(2):
                sweep(jobs, operations, now=self.now)
            self.assertEqual(len(ran.calls), 1)
            self.now = AFTER
            job_control.expire(jobs, job_id=recovery_job, trigger="job-deadline", stage_id=None,
                               deadline_at=EXPIRED, observed_at=self.now)
            sweep(jobs, operations, now=self.now)
            held = retained_verification.hold_of(jobs, recovery_job)
            self.assertIsNotNone(held)
            again = [flag for flag in flags if not flag.startswith("--stage=") and not flag.startswith("--decision-id=")]
            again.extend(["--decision-id=D2", "--stage=review",
                          "--prior-successor=" + held["lineage"]["successor_job_id"],
                          "--prior-verification-attempt=" + held["lineage"]["verification_attempt_id"],
                          "--prior-verification-digest=" + held["lineage"]["verification_result_digest"]])
            code, answer = owner.command(self, *owner.argv(self, "recovery-decide", *again), clock=lambda: self.now)
            self.assertEqual(code, 0, answer)
            self.assertTrue(answer["admitted"], answer)
            operations.close()
            operations = self._composed = stage_execution.operations_from(
                self.composed_document(), jobs, control, engine_run=self.engine,
                credential_provider=lambda provider, reference: self.secret,
                clock=lambda: self.now, checkout=self.checkout)
            self.addCleanup(operations.close)
            operations.recovery_verification.runner._run = ran
            recovery_job = "recovery-D2"
        if restart:
            from baton_v12.job_manager import reconcile
            for _ in range(3):
                sweep(jobs, operations, now=self.now)
            before = retained_verification.handoff_of(jobs, recovery_job)
            self.assertIsNotNone(before)
            operations.close()
            operations = self._composed = stage_execution.operations_from(
                self.composed_document(), jobs, control, engine_run=self.engine,
                credential_provider=lambda provider, reference: self.secret,
                clock=lambda: self.now, checkout=self.checkout)
            self.addCleanup(operations.close)
            operations.recovery_verification.runner._run = ran
            reconcile(jobs, operations, now=self.now)
            self.assertEqual(retained_verification.handoff_of(jobs, recovery_job), before)
        reports = [sweep(jobs, operations, now=self.now) for _ in range(8)]
        if drift:
            refusals = [one for report in reports for one in report["started"] if one["outcome"] == "refused"]
            self.assertTrue(refusals, reports)
            self.assertEqual(refusals[0]["detail"]["code"], "digest")
            self.assertEqual(self.examined, 0)
            self.assertEqual(len([one for one in self.engine.starts if "--entrypoint" not in one]), 1)
            self.assertEqual(frozen_output_of(control, attempt), frozen)
            self.assertEqual(directory_manifest(original_custody), original_bytes)
            return
        self.assertEqual(len(ran.calls), 1)
        if review_only:
            self.assertIsNone(retained_verification.execution_result_of(jobs, recovery_job))
        handoff = retained_verification.handoff_of(jobs, recovery_job)
        self.assertTrue(any(one["stage_id"] == recovery_job + "/review" and one["state"] == "waiting"
                            for one in __import__("baton_v12.job_manager", fromlist=["status"]).status(
                                jobs, operations, observed_at=self.now)["jobs"][-1]["stages"]))

        reviewer = self.only_attempt(operations, "review")
        prepared = self.worker_of(operations, "review").stage._prepared[reviewer]
        delivered = json.loads(pathlib.Path(prepared["boundary"]["roots"]["inputs"], "recovery-review.json").read_text())
        self.assertEqual(delivered["handoff"], handoff)
        self.assertEqual(delivered["handoff_digest"], digest(handoff))
        self.assertEqual(handoff["candidate"]["head"], seen["failure"]["candidate"]["head"])
        report = {"schema": "baton.review-report/1", "verdict": verdict,
                  "findings": "Scripted substantive review: inspected retained candidate and verifier account."}
        if evidence != "missing":
            report["recovery_digest"] = digest(handoff) if evidence == "valid" else "sha256:" + "0" * 64
        self.assertEqual(self.turn(control, "review", reviewer,
                                  self.mounted(operations, "review", reviewer),
                                  edits={"review-report.json": json.dumps(report)}), 0)
        for _ in range(8):
            sweep(jobs, operations, now=self.now)
        from baton_v12.worker_manager import review_cycles
        recorded = control._connection.execute("SELECT verdict_id FROM checkpoint_verdicts WHERE attachment_id = ?", (prepared["attachment_id"],)).fetchone()
        if evidence == "valid":
            self.assertIsNotNone(recorded)
            result = review_cycles.verdict_of(control, recorded["verdict_id"])
            self.assertEqual(result["disposition"], verdict)
            self.assertEqual(result["head_object"], handoff["candidate"]["head"])
        else:
            self.assertIsNone(recorded)
        self.assertEqual(self.worker_of(operations, "implementation").stage._prepared, {})
        self.assertEqual(len([one for one in self.engine.starts if "--entrypoint" not in one]), 2)
        self.assertEqual([one["kind"] for one in submission.stages_of(jobs, recovery_job)], ["review"])
        self.assertEqual(frozen_output_of(control, attempt), frozen)
        self.assertEqual(directory_manifest(original_custody), original_bytes)
        self.assertEqual(self.examined, 1)
        self.assertEqual(len(ran.calls), 1)

    def test_retained_candidate_reaches_actual_independent_acceptance(self):
        self.connected_review()

    def test_substantive_rejection_remains_rejected(self):
        self.connected_review("rejected")

    def test_acceptance_without_verifier_evidence_binding_is_held(self):
        self.connected_review(evidence="missing")

    def test_acceptance_for_other_verifier_evidence_is_held(self):
        self.connected_review(evidence="wrong")

    def test_review_only_reaches_acceptance_without_another_verifier(self):
        self.connected_review(review_only=True)

    def test_advanced_line_is_not_reviewed_as_the_retained_candidate(self):
        self.connected_review(drift=True)

    def test_restart_after_handoff_reaches_review_without_repeating_verification(self):
        self.connected_review(restart=True)
