"""W39357 — the real Claude adapter, proved without a provider or a secret.

`work/records/2026/08/finding-v12-first-useful-dogfood-task/findings/
finding-real-claude-adapter-image/`.

WHY THERE IS NO LIVE PROVIDER HERE, and it is the acceptance's own decision
rather than a shortcut: the first live provider invocation needs the operator's
exact credential grant and an approved network posture, and it belongs to
W39364. What this file owns is everything a live run could not establish
deterministically anyway — the composed argv, the composed environment, the
credential boundary, the source copy, the write boundary, and the four ways a
turn fails to produce a candidate.

THE PROVIDER IS INJECTED, NOT MOCKED-OVER. `ClaudeAgent(run=...)` takes the
process-running capability, exactly as the manager's own components take theirs,
so what these cases drive is the real `work` path with one seam supplied.

NO SECRET EVER EXISTS IN THIS FILE. The credential is a file containing the
literal text `not-a-credential`, and one case asserts the adapter never opens
it.
"""

import json
import os
import pathlib
import shutil
import stat
import subprocess
import sys
import tempfile
import time
import unittest

WORKER = (pathlib.Path(__file__).resolve().parents[3] / "worker")
sys.path.insert(0, str(WORKER))
shutil.rmtree(WORKER / "__pycache__", ignore_errors=True)

import claude_agent                                          # noqa: E402
from claude_agent import ClaudeAgent, TaskRefusal            # noqa: E402

DECLARED = [{"name": "proposal", "type": "directory-result",
             "path": "proposal", "required": True,
             "constraints": {"max_bytes": 1 << 20, "max_entries": 100,
                             "allowed_media_types": ["text/plain"],
                             "link_policy": "forbid",
                             "validator_digest": None}}]

TASK = {"schema": "baton.dogfood-task/1",
        "task_id": "w39364-ping-pong-coverage",
        "instructions": "Add focused unit coverage for _observed_readable.",
        "verification": ["python3", "harness.py"],
        "source_root": "source"}


class AdapterCase(unittest.TestCase):
    """A staged `/input`, a writable `/output`, and no provider.

    THE ROOTS ARE PATCHED ON THE MODULE, like `test_worker_image` does with the
    worker's own: they are CONSTANTS of the workload contract, so there is no
    operand for a fixture to supply. A test may reach into the module; a caller
    may not reach into the contract.
    """

    def setUp(self):
        home = tempfile.mkdtemp(prefix="v12-w39357-")
        self.addCleanup(shutil.rmtree, home, True)
        self.home = home
        self.inputs = os.path.join(home, "input")
        self.outputs = os.path.join(home, "output")
        self.scratch = os.path.join(home, "scratch")
        self.credentials = os.path.join(home, "credentials")
        for place in (self.inputs, self.outputs, self.scratch,
                      self.credentials):
            os.makedirs(place)
        self.source = os.path.join(self.inputs, "source")
        os.makedirs(self.source)
        self.write(os.path.join(self.source, "harness.py"),
                   "print('the staged harness')\n")
        self.write(os.path.join(self.source, "preflight.py"),
                   "def _observed_readable():\n    return True\n")
        self.task(TASK)
        # THE CREDENTIAL IS A FILE THAT SAYS IT IS NOT ONE. Its content is
        # asserted never to be read, so a real bearer would prove nothing that
        # this does not and would put a secret in a repository.
        self.slot = os.path.join(self.credentials, "claude")
        self.write(self.slot, "not-a-credential\n")
        for module, name, value in (
                (claude_agent, "INPUT_ROOT", self.inputs),
                (claude_agent, "OUTPUT_ROOT", self.outputs),
                (claude_agent, "CREDENTIAL_ROOT", self.credentials)):
            held = getattr(module, name)
            setattr(module, name, value)
            self.addCleanup(setattr, module, name, held)

    @staticmethod
    def write(place, body):
        os.makedirs(os.path.dirname(place), exist_ok=True)
        with open(place, "w", encoding="utf-8") as handle:
            handle.write(body)

    def task(self, document):
        place = os.path.join(self.inputs, claude_agent.TASK_DOCUMENT)
        if document is None:
            if os.path.exists(place):
                os.unlink(place)
            return
        self.write(place, json.dumps(document))

    # -- the injected provider ----------------------------------------------

    def provider(self, *, edits=None, status=0, verify=0,
                 timeout=False, missing=False):
        """One recorded process-running capability.

        `edits` is what the "provider" writes into the candidate copy — which
        is the only way a real one changes anything, so a fake that wrote
        nowhere else is exactly as capable here.

        THERE IS NO `stderr=` OPERAND, and its removal is the fixture half of
        W39357 review 2026-08-30T04:01:29Z [P1]. The adapter hands both
        children `subprocess.DEVNULL`, so a fake cannot write to a stream at
        all — an operand that quietly wrote nowhere would leave every case
        using it looking like it proved something about a diagnostic. The
        cases that genuinely need a child to SAY something drive a real
        `subprocess.run`; see `NoChildStreamByteReachesTheProposal`.
        """
        self.calls = []

        def run(argv, **options):
            self.calls.append((list(argv), dict(options)))
            if argv[0] == claude_agent.PROVIDER_PROGRAM:
                if timeout:
                    raise subprocess.TimeoutExpired(argv, 1)
                if missing:
                    raise OSError("no such file")
                for name, body in (edits or {}).items():
                    self.write(os.path.join(options["cwd"], name), body)
                return subprocess.CompletedProcess(argv, status, None, None)
            return subprocess.CompletedProcess(argv, verify, None, None)

        return run

    def worked(self, **operands):
        agent = ClaudeAgent(run=self.provider(**operands),
                            home=self.scratch)
        return agent.work({"contract": "the frozen task"}, list(DECLARED))

    def proposal(self, *parts):
        return os.path.join(self.outputs, "proposal", *parts)

    def result(self):
        with open(self.proposal("result.json"), encoding="utf-8") as handle:
            return json.load(handle)


class ThePositiveTurnWritesTheDeclaredProposal(AdapterCase):

    def test_a_changed_and_verified_candidate_is_completed(self):
        answered = self.worked(edits={"harness.py": "print('now covered')\n"})
        self.assertEqual(answered["disposition"], "completed")
        self.assertEqual(answered["outputs"],
                         [{"name": "proposal", "status": "present",
                           "result_metadata": {}}])
        self.assertEqual(self.result()["disposition"], "candidate")
        self.assertEqual(self.result()["changed_paths"], ["harness.py"])

    def test_the_four_declared_members_are_all_written(self):
        self.worked(edits={"harness.py": "print('now covered')\n"})
        for name in ("candidate", "change.patch", "result.json",
                     "verification.txt"):
            self.assertTrue(os.path.exists(self.proposal(name)), name)
        # THE CANDIDATE IS THE WHOLE TREE, not only what changed: the operator
        # diffs it against the recorded input manifest, which needs every file.
        self.assertEqual(sorted(os.listdir(self.proposal("candidate"))),
                         ["harness.py", "preflight.py"])

    def test_the_patch_is_a_unified_diff_of_the_changed_paths(self):
        self.worked(edits={"harness.py": "print('now covered')\n"})
        with open(self.proposal("change.patch"), encoding="utf-8") as handle:
            patch = handle.read()
        self.assertIn("--- a/harness.py", patch)
        self.assertIn("+++ b/harness.py", patch)
        self.assertIn("+print('now covered')", patch)

    def test_the_verification_transcript_carries_the_command_and_status(self):
        self.worked(edits={"harness.py": "print('now covered')\n"})
        with open(self.proposal("verification.txt"),
                  encoding="utf-8") as handle:
            transcript = handle.read()
        self.assertIn("python3 harness.py", transcript)
        self.assertIn("exit: 0", transcript)

    def test_the_written_tree_is_group_readable_for_collection(self):
        """A STATED COOPERATION, not custody.

        W36540 owns unconditional custody; until it lands, an owner-only tree
        is one the manager fails closed on. This adapter cooperates on purpose
        and the mode is asserted so a later change cannot quietly stop.
        """
        self.worked(edits={"harness.py": "print('now covered')\n"})
        self.assertEqual(os.stat(self.proposal()).st_mode & 0o777,
                         claude_agent.DIRECTORY_MODE & 0o777)
        self.assertEqual(os.stat(self.proposal("result.json")).st_mode & 0o777,
                         claude_agent.FILE_MODE)

    def test_the_staged_source_is_never_written(self):
        """The read-only input is the evidence the result is measured against.

        Asserted by CONTENT rather than by mode: this fixture's `/input` is an
        ordinary directory, so a mode assertion would prove the fixture rather
        than the adapter.
        """
        def held():
            found = {}
            for name in sorted(os.listdir(self.source)):
                with open(os.path.join(self.source, name),
                          encoding="utf-8") as handle:
                    found[name] = handle.read()
            return found

        before = held()
        self.worked(edits={"harness.py": "print('now covered')\n"})
        self.assertEqual(held(), before)


class TheProviderArgvAndEnvironmentAreClosed(AdapterCase):

    def spoken(self):
        self.worked(edits={"harness.py": "print('now covered')\n"})
        return next((argv, options) for argv, options in self.calls
                    if argv[0] == claude_agent.PROVIDER_PROGRAM)

    def test_the_argv_is_exactly_the_pinned_vector_plus_one_prompt(self):
        """GOLDEN. The one operand a golden test cannot establish is whether
        `acceptEdits` is the right spelling — W39364's live turn owns that —
        so what this pins is that nothing else is composed and that the prompt
        is the last word."""
        argv, _options = self.spoken()
        self.assertEqual(argv[:-1], ["claude", "--print",
                                     "--permission-mode", "acceptEdits",
                                     "--output-format", "json"])
        self.assertEqual(len(argv), 7)

    def test_the_prompt_carries_the_task_and_names_nothing_protocol(self):
        argv, _options = self.spoken()
        prompt = argv[-1]
        self.assertIn(TASK["instructions"], prompt)
        self.assertIn("python3 harness.py", prompt)
        # THE PROVIDER IS NOT TOLD ABOUT THE PROTOCOL. A provider that could
        # see the output root, the session or the assignment could write into
        # them or name them in its answer.
        for forbidden in ("/output", "output.json", "session", "assignment",
                          "worker-entry", "/run/baton"):
            self.assertNotIn(forbidden, prompt)

    def test_the_environment_is_composed_and_never_inherited(self):
        """A credential variable in this process must not reach the child.

        This is the failure the provider's own resolution order makes silent:
        an `ANTHROPIC_API_KEY` present in the container outranks every other
        source, so a forwarded environment would decide which account the
        trial ran as.
        """
        os.environ["ANTHROPIC_API_KEY"] = "not-a-credential-either"
        self.addCleanup(os.environ.pop, "ANTHROPIC_API_KEY", None)
        _argv, options = self.spoken()
        self.assertEqual(sorted(options["env"]), ["HOME", "PATH"])
        self.assertNotIn("ANTHROPIC_API_KEY", options["env"])

    def test_the_provider_runs_in_the_private_copy_and_not_the_source(self):
        _argv, options = self.spoken()
        self.assertTrue(options["cwd"].startswith(self.scratch), options)
        self.assertNotEqual(options["cwd"], self.source)

    def test_the_turn_is_bounded(self):
        _argv, options = self.spoken()
        self.assertEqual(options["timeout"], claude_agent.PROVIDER_SECONDS)

    def test_the_provider_stderr_is_discarded_rather_than_captured(self):
        """W39357 review 2026-08-30T04:01:29Z [P1], and it is why the stderr
        half of that finding is UNCHANGED by W55360.

        Stderr was captured and interpolated into `result.json` and, through
        `recap`, into the worker's own `/output/output.json` — and the
        process writing it is the one holding this attempt's credential.
        That is the stream where a bearer actually appeared, and this
        adapter still has no descriptor onto it.

        SUPERSEDED IN ONE HALF ONLY. This case used to require BOTH provider
        streams on `DEVNULL`. W55360's approver ruling (event 55479) narrowly
        allows the adapter to read provider STDOUT when it has selected the
        CLI's structured JSON mode, so that half moved to
        `test_the_provider_stdout_is_a_bounded_anonymous_pipe` below. Stderr
        did not move, and neither did either verification stream.
        """
        _argv, options = self.spoken()
        self.assertIs(options["stderr"], subprocess.DEVNULL)

    def test_the_provider_stdout_is_a_bounded_anonymous_pipe(self):
        """W55360: read, but never through a name a child could reach.

        The first two W39357 review rounds were both about capture PLUMBING —
        a pathname a child could replace, then a descriptor read back too
        late — so the shape matters as much as the boundedness. What the
        child is handed is an anonymous pipe descriptor this process
        created: not `DEVNULL` any more, and not a file, a path, or
        anything under the output root either.
        """
        seen = {}
        handed = self.provider(edits={"harness.py": "print('now covered')\n"})

        def run(argv, **options):
            if argv[0] == claude_agent.PROVIDER_PROGRAM:
                # FSTAT'ED WHILE THE CHILD WOULD HOLD IT. The adapter closes
                # both ends when the run returns, which is the behaviour a
                # later case asserts, so the descriptor has to be examined
                # here rather than out of the recorded options.
                found = os.fstat(options["stdout"])
                seen.update(fifo=stat.S_ISFIFO(found.st_mode),
                            fd=options["stdout"])
            return handed(argv, **options)

        ClaudeAgent(run=run, home=self.scratch).work(
            {"contract": "t"}, list(DECLARED))
        self.assertIsInstance(seen["fd"], int)
        self.assertNotIn(seen["fd"], (subprocess.DEVNULL, subprocess.PIPE,
                                      subprocess.STDOUT))
        # AN ANONYMOUS PIPE AND NOT A FILE, asserted of the descriptor itself
        # rather than of how it was made.
        self.assertTrue(seen["fifo"], "the provider's stdout is not a pipe")

    def test_both_verification_streams_are_discarded_too(self):
        """The sharper of the two, because this child is provider-EDITED code
        running with the same credential mount readable."""
        self.worked(edits={"harness.py": "print('now covered')\n"})
        _argv, options = next(
            (argv, options) for argv, options in self.calls
            if argv[0] != claude_agent.PROVIDER_PROGRAM)
        self.assertIs(options["stdout"], subprocess.DEVNULL)
        self.assertIs(options["stderr"], subprocess.DEVNULL)


class NoChildStreamByteReachesTheProposal(AdapterCase):
    """W39357 review 2026-08-30T04:01:29Z [P1], as one property.

    SUPERSEDES `OutputIsBoundedBeforeItIsAllocated`, whose two ceiling cases
    and `_window` case are gone with their subject. Those asked how much of a
    child's stream reached the artifact and how safely it was read back; this
    review's finding is that the question was wrong. The provider holds the
    attempt's bearer and the verification command is provider-edited code with
    the same mount readable, so no window onto either stream is publishable at
    any size. `MAX_DIAGNOSTIC`, `MAX_VERIFICATION` and `_window` are deleted
    rather than tightened, and what replaces them is this: NOTHING a child
    wrote appears anywhere in the proposal or in the worker's answer.

    THESE CASES USE A REAL `subprocess.run`, deliberately and for the same
    reason the deleted ones did. A fake that "wrote" to a handle would prove
    the fixture, and `subprocess.DEVNULL` is the thing under test — only a real
    child can be given it.
    """

    def shouting(self, *, marker, words=1, status=0, verify=0):
        """A real child that writes a distinctive marker to BOTH streams."""
        program = (f"import sys;"
                   f"sys.stdout.write({marker!r} * {words});"
                   f"sys.stderr.write({marker!r} * {words});"
                   f"raise SystemExit(%d)")

        def run(argv, **options):
            if argv[0] == claude_agent.PROVIDER_PROGRAM:
                self.write(os.path.join(options["cwd"], "harness.py"),
                           "print('now covered')\n")
                argv = [sys.executable, "-c", program % status]
            else:
                argv = [sys.executable, "-c", program % verify]
            return subprocess.run(argv, **options)

        return run

    def published(self):
        """Every byte this turn made host-visible, as one blob."""
        found = []
        for base, _directories, files in os.walk(self.proposal()):
            for name in sorted(files):
                with open(os.path.join(base, name), "rb") as handle:
                    found.append(handle.read())
        return b"".join(found)

    def test_a_shouting_provider_puts_nothing_in_the_proposal_or_the_answer(
            self):
        agent = ClaudeAgent(run=self.shouting(marker="PROVIDER-SAID",
                                              words=8192, status=3),
                            home=self.scratch)
        answered = agent.work({"contract": "t"}, list(DECLARED))
        self.assertEqual(answered["disposition"], "unable")
        self.assertNotIn(b"PROVIDER-SAID", self.published())
        # AND THE ANSWER TOO. `recap` is composed from `why`, so the old
        # interpolation reached the worker's protocol document as well as
        # `result.json` — a sink the review did not have to name for it to be
        # real.
        self.assertNotIn("PROVIDER-SAID", answered["recap"])
        # WHAT SURVIVES IS THE STATUS, which this adapter got from `wait` and
        # not from a stream. Failure stays honest without being transcribed.
        self.assertIn("the provider exited 3", self.result()["why"])

    def test_a_shouting_verification_puts_nothing_in_the_transcript(self):
        agent = ClaudeAgent(run=self.shouting(marker="COMMAND-SAID",
                                              words=8192),
                            home=self.scratch)
        answered = agent.work({"contract": "t"}, list(DECLARED))
        self.assertEqual(answered["disposition"], "completed")
        self.assertNotIn(b"COMMAND-SAID", self.published())
        self.assertNotIn("COMMAND-SAID", answered["recap"])

    def test_the_transcript_still_carries_the_operator_authored_evidence(self):
        """Withholding is not emptying. What is left is the frozen command,
        which the OPERATOR wrote into `/input/task.json`, and the ending, which
        came from `wait` — neither of them a byte any child produced."""
        agent = ClaudeAgent(run=self.shouting(marker="COMMAND-SAID", verify=4),
                            home=self.scratch)
        agent.work({"contract": "t"}, list(DECLARED))
        with open(self.proposal("verification.txt"),
                  encoding="utf-8") as handle:
            transcript = handle.read()
        self.assertIn("$ python3 harness.py", transcript)
        self.assertIn("exit: 4", transcript)
        # AND IT SAYS THE OUTPUT IS WITHHELD, so absence does not read as a
        # command that said nothing.
        self.assertIn("deliberately not", transcript)

    def test_the_module_keeps_no_ceiling_on_bytes_it_never_reads(self):
        """The deletions asserted directly, so re-adding a capture ceiling is
        a deliberate act rather than drift back toward the finding."""
        for gone in ("MAX_DIAGNOSTIC", "MAX_VERIFICATION", "_window",
                     "_capture"):
            self.assertFalse(hasattr(claude_agent, gone), gone)


class TheStructuredRecordIsMappedAndNeverPublished(AdapterCase):
    """W55360, as one property: a WORD comes out and no BYTE does.

    THESE DRIVE A REAL CHILD, for the reason
    `NoChildStreamByteReachesTheProposal` gives and one more of its own. A
    fake handing back a prebuilt buffer would prove this file's arithmetic;
    what is under test is fd plumbing — an anonymous pipe, a drain running
    beside the child, a bounded retention and a close that lets the reader
    see EOF — and only a real process writing into a real descriptor
    exercises any of it.

    THE MARKER STANDS IN FOR THE BEARER. It is placed in every part of the
    document that is not the one matched value: other members, member NAMES,
    nested values, the terminal reason itself when unknown, and the bytes after
    the ceiling. None of them may appear in the proposal or the answer.
    """

    MARKER = "PROVIDER-BEARER-fbb1c0"

    def speaking(self, *, says, status, chunks=1, also_stderr=True, verify=0):
        """A real child that writes `says` to stdout in `chunks` pieces.

        Written in pieces on purpose: one `write` per chunk with a flush
        between, so the parent's drain performs several reads and a reader
        that only ever read once would be visible.
        """
        # THE BODY TRAVELS IN A FILE, not in argv. A single argument is capped
        # at 128 KiB on Linux, and the overflow cases here are deliberately
        # larger than that -- an argv-carried body would have made those cases
        # fail as "the provider could not be started", which is a different
        # ending than the one under test.
        carried = os.path.join(self.home, "provider-says.txt")
        with open(carried, "w", encoding="utf-8") as handle:
            handle.write(says)
        program = (
            "import sys, time\n"
            "body = open(sys.argv[1], encoding='utf-8').read()\n"
            "count = int(sys.argv[2])\n"
            "size = max(1, (len(body) + count - 1) // count)\n"
            "for at in range(0, len(body), size):\n"
            "    sys.stdout.write(body[at:at + size])\n"
            "    sys.stdout.flush()\n"
            "    time.sleep(0.001)\n"
            "if int(sys.argv[4]):\n"
            "    sys.stderr.write(body)\n"
            "raise SystemExit(int(sys.argv[3]))\n")

        def run(argv, **options):
            if argv[0] == claude_agent.PROVIDER_PROGRAM:
                self.write(os.path.join(options["cwd"], "harness.py"),
                           "print('now covered')\n")
                argv = [sys.executable, "-c", program, carried, str(chunks),
                        str(status), "1" if also_stderr else "0"]
            else:
                argv = [sys.executable, "-c", "raise SystemExit(%d)" % verify]
            return subprocess.run(argv, **options)

        return run

    LINGERS = 20.0

    def outliving(self, *, says, status, leader_sleeps=0.0):
        """A real child that leaves a DESCENDANT holding stdout, then exits.

        This is W55360 review (2026-09-01T03:35:56Z) [P1] as a fixture, and
        the shape matters: the leader writes its record and starts a
        `subprocess.Popen` it never waits for. The descendant INHERITS the
        write end of the adapter's pipe, so EOF cannot arrive while it lives —
        and it lives `LINGERS` seconds, an order longer than the adapter is
        allowed to wait for it.

        THE DESCENDANT WRITES THE MARKER, on purpose. Its bytes really are
        retained by the drain, which is what makes this more than a timing
        case: the record the adapter holds contains the marker, is PARTIAL,
        and must still publish nothing but one of this module's own words.
        """
        carried = os.path.join(self.home, "provider-says.txt")
        with open(carried, "w", encoding="utf-8") as handle:
            handle.write(says)
        descendant = os.path.join(self.home, "descendant.py")
        self.write(descendant,
                   "import sys, time\n"
                   "sys.stdout.write(sys.argv[1])\n"
                   "sys.stdout.flush()\n"
                   "time.sleep(float(sys.argv[2]))\n")
        program = (
            "import subprocess, sys, time\n"
            "sys.stdout.write(open(sys.argv[1], encoding='utf-8').read())\n"
            "sys.stdout.flush()\n"
            "subprocess.Popen([sys.executable, sys.argv[2], sys.argv[3],\n"
            "                  sys.argv[4]])\n"
            "time.sleep(float(sys.argv[5]))\n"
            "raise SystemExit(int(sys.argv[6]))\n")

        def run(argv, **options):
            if argv[0] == claude_agent.PROVIDER_PROGRAM:
                self.write(os.path.join(options["cwd"], "harness.py"),
                           "print('now covered')\n")
                argv = [sys.executable, "-c", program, carried, descendant,
                        f"{self.MARKER}-from-a-descendant", str(self.LINGERS),
                        str(leader_sleeps), str(status)]
            else:
                argv = [sys.executable, "-c", "raise SystemExit(0)"]
            return subprocess.run(argv, **options)

        return run

    def turned(self, **operands):
        agent = ClaudeAgent(run=self.speaking(**operands), home=self.scratch)
        return agent.work({"contract": "t"}, list(DECLARED))

    def published(self):
        """Every byte this turn made host-visible, as one blob."""
        found = []
        for base, _directories, files in os.walk(self.proposal()):
            for name in sorted(files):
                with open(os.path.join(base, name), "rb") as handle:
                    found.append(handle.read())
        return b"".join(found)

    def document(self, reason, **members):
        """The structured record, with the marker in every other part."""
        body = {"terminal_reason": reason,
                "is_error": True,
                "duration_api_ms": 0,
                "result": self.MARKER,
                f"{self.MARKER}-member": {"nested": self.MARKER}}
        body.update(members)
        return json.dumps(body)

    def clean(self, answered):
        """No marker anywhere host-visible or returned, ever."""
        self.assertNotIn(self.MARKER.encode("ascii"), self.published())
        self.assertNotIn(self.MARKER, answered["recap"])

    # -- the one value the evidence earned -----------------------------------

    def test_the_observed_api_error_becomes_the_adapter_word(self):
        """The whole point of the Work, end to end through a real child."""
        answered = self.turned(says=self.document("api_error"), status=1,
                               chunks=4)
        self.assertEqual(self.result()["provider"]["failure_reason"],
                         "api-error")
        self.assertEqual(self.result()["disposition"], "provider-failed")
        self.assertEqual(answered["disposition"], "unable")
        self.clean(answered)

    def test_the_providers_own_spelling_never_reaches_a_sink(self):
        """`api_error` earns `api-error`, and the underscore form is not what
        gets written down. A published raw spelling would be a one-value
        passthrough, which is the thing the closed map exists to not be."""
        answered = self.turned(says=self.document("api_error"), status=1)
        self.assertNotIn(b"api_error", self.published())
        self.assertNotIn("api_error", answered["recap"])
        self.assertIn("api-error", self.result()["why"])

    def test_the_mapped_word_reaches_the_recap_and_the_status_survives(self):
        answered = self.turned(says=self.document("api_error"), status=7)
        self.assertIn("api-error", answered["recap"])
        self.assertIn("the provider exited 7", self.result()["why"])
        self.assertEqual(self.result()["provider"]["status"], 7)

    # -- everything else is one word ----------------------------------------

    def test_every_unusable_record_is_unclassified_and_says_nothing_more(self):
        """One case per way the document can fail to earn a word.

        Each carries the marker, and each must publish the SAME word: telling
        these apart in the record would be publishing a parser's reading of
        untrusted bytes.
        """
        marker = self.MARKER
        cases = {
            "an unknown reason": self.document(f"{marker}-unknown"),
            "no reason at all": json.dumps({"result": marker}),
            "a non-string reason": self.document(None),
            "a reason that is a document": json.dumps(
                {"terminal_reason": {"kind": marker}}),
            "a non-object root": json.dumps([{"terminal_reason": "api_error"},
                                             marker]),
            "malformed json": '{"terminal_reason": "api_error", ' + marker,
            "trailing data": ('{"terminal_reason": "api_error"} '
                              '{"second": "%s"}' % marker),
            # BOTH ORDERS, and the second is the one that makes the guard
            # load-bearing: `json.loads` keeps the LAST of two equal keys, so
            # a document whose duplicate resolves to the earned value would
            # publish `api-error` if the check were dropped.
            "a duplicated reason, marker last":
                ('{"terminal_reason": "api_error", '
                 '"terminal_reason": "%s"}' % marker),
            "a duplicated reason, the earned value last":
                ('{"terminal_reason": "%s", '
                 '"terminal_reason": "api_error"}' % marker),
            "nothing at all": "",
            "not json at all": marker,
            # PYTHON'S EXTENSIONS ARE NOT THE GRAMMAR. `json.loads` accepts
            # `NaN` and the infinities; JSON does not, so neither does this.
            "a non-standard constant":
                '{"terminal_reason": "api_error", "%s": NaN}' % marker,
            # AND A DOCUMENT INSIDE THE CEILING THE PARSER STILL CANNOT
            # FINISH: bytes were bounded, recursion was not.
            "nesting the parser cannot finish":
                ('{"terminal_reason": "api_error", "%s": ' % marker
                 + "[" * 30000 + "]" * 30000 + "}"),
        }
        for why, says in cases.items():
            with self.subTest(record=why):
                self.setUp()
                answered = self.turned(says=says, status=1, chunks=3)
                self.assertEqual(
                    self.result()["provider"]["failure_reason"],
                    "unclassified", why)
                self.clean(answered)

    def test_invalid_utf8_is_unclassified_rather_than_replaced(self):
        """Decoded strictly, so an undecodable record cannot become a
        different record by substitution."""
        agent = ClaudeAgent(run=self.provider(status=1), home=self.scratch)
        self.assertEqual(
            claude_agent._failure_reason(
                b'{"terminal_reason": "api_error", "x": "\xff\xfe"}',
                partial=False),
            "unclassified")
        # AND THE VALID FORM OF THE SAME DOCUMENT STILL EARNS ITS WORD, so the
        # case above is about the bytes rather than about the members.
        self.assertEqual(
            claude_agent._failure_reason(
                b'{"terminal_reason": "api_error", "x": "ok"}',
                partial=False),
            "api-error")
        del agent

    def test_pythons_non_standard_constants_are_not_json(self):
        """W55360 review (2026-09-01T03:35:56Z) [P1]: the parser was strict
        about duplicates and permissive about the grammar.

        `NaN`, `Infinity` and `-Infinity` are Python extensions and are not
        JSON. A record carrying one used to earn `api-error` — the adapter
        called a document well-formed that the approved rule says is
        unusable, which makes the classification the provider's choice rather
        than this module's.
        """
        for literal in ("NaN", "Infinity", "-Infinity", "[NaN]",
                        '{"nested": Infinity}'):
            with self.subTest(constant=literal):
                record = ('{"terminal_reason": "api_error", "x": %s}'
                          % literal).encode("utf-8")
                self.assertEqual(
                    claude_agent._failure_reason(record, partial=False),
                    "unclassified")
        # AND THE SAME DOCUMENT WITH A REAL NUMBER STILL EARNS ITS WORD, so
        # the cases above are about the grammar rather than about the member.
        self.assertEqual(
            claude_agent._failure_reason(
                b'{"terminal_reason": "api_error", "x": 0}', partial=False),
            "api-error")

    def test_a_record_the_parser_cannot_finish_is_unclassified(self):
        """The same review's second half: `_failure_reason` was not TOTAL.

        A record well inside the 64 KiB ceiling can still exhaust the decoder's
        recursion, and `RecursionError` is not a `ValueError` — so a provider
        could fault the worker from inside the function whose whole contract is
        to answer one of two words. The bound on bytes was never a bound on
        parser depth, and this is the shape that shows the difference.
        """
        depth = 30000
        record = ('{"terminal_reason": "api_error", "x": '
                  + "[" * depth + "]" * depth + "}").encode("utf-8")
        self.assertLess(len(record), claude_agent.MAX_PROVIDER_RECORD)
        self.assertEqual(
            claude_agent._failure_reason(record, partial=False),
            "unclassified")

    # -- the boundedness, and that it is a bound on MEMORY not on the child --

    def test_a_flood_is_drained_to_the_end_and_retained_bounded(self):
        """The two properties together, against a real child.

        A provider writing far more than the ceiling must neither wedge on a
        full pipe nor make this process hold what it wrote. So the child emits
        several times `MAX_PROVIDER_RECORD`, the turn still completes, and the
        retained record is measured directly at the seam.
        """
        flood = self.MARKER * ((claude_agent.MAX_PROVIDER_RECORD * 3)
                               // len(self.MARKER))
        self.assertGreater(len(flood), claude_agent.MAX_PROVIDER_RECORD * 2)
        agent = ClaudeAgent(run=self.speaking(says=flood, status=1, chunks=16),
                            home=self.scratch)
        status, record, partial = agent._ran_provider(
            [claude_agent.PROVIDER_PROGRAM], cwd=self.scratch, seconds=60,
            env={"HOME": self.scratch, "PATH": "/usr/bin:/bin"})
        self.assertEqual(status, 1)
        self.assertTrue(partial, "the overflow was not noticed")
        self.assertLessEqual(len(record), claude_agent.MAX_PROVIDER_RECORD)
        self.assertEqual(_failure := claude_agent._failure_reason(
            record, partial=partial), "unclassified")
        del _failure

    def test_a_partial_record_is_unclassified_even_when_it_parses(self):
        """The guard on its own, with the parser deliberately unable to help.

        Every end-to-end flood case below also fails to PARSE, so none of them
        can tell whether the partial check is doing anything. This hands
        `_failure_reason` a perfectly good `api_error` document and the
        partial flag, which is the only shape that isolates it: the stream was
        not proved whole, so what survived is not known to be the whole
        record, and a prefix that happens to parse is not a document the
        provider sent.

        BOTH WAYS OF BEING PARTIAL ARRIVE HERE AS THIS ONE FLAG -- bytes
        dropped at the ceiling, and a stream whose EOF never came because a
        provider descendant still held the write end.
        """
        earned = json.dumps({"terminal_reason": "api_error"}).encode("utf-8")
        self.assertEqual(
            claude_agent._failure_reason(earned, partial=False),
            "api-error")
        self.assertEqual(
            claude_agent._failure_reason(earned, partial=True),
            "unclassified")

    def test_a_flood_beginning_with_a_good_record_is_unclassified(self):
        """Overflow is not a reason to trust the prefix.

        A provider that emitted a valid `api_error` document and then a
        megabyte of anything else has not sent one document, and reassembling
        the readable part would be this module deciding which bytes counted.
        """
        says = (self.document("api_error")
                + self.MARKER * claude_agent.MAX_PROVIDER_RECORD)
        answered = self.turned(says=says, status=1, chunks=32)
        self.assertEqual(self.result()["provider"]["failure_reason"],
                         "unclassified")
        self.clean(answered)

    def test_a_descendant_holding_stdout_cannot_outlive_the_bound(self):
        """W55360 review (2026-09-01T03:35:56Z) [P1], at the seam.

        EOF arrives when the LAST writer closes the descriptor, and the
        provider's own children are writers it never told this adapter about.
        The reader used to wait for that EOF with no deadline, so a leader
        that spawned something long-lived and exited wedged the worker AFTER
        `self._run` had returned — past the one bound, `PROVIDER_SECONDS`,
        that was supposed to cover this.

        So the assertion is a CLOCK as much as a word: the call returns while
        the descendant is still alive and still holding the pipe.
        """
        self.assertGreater(self.LINGERS,
                           claude_agent.PROVIDER_DRAIN_SECONDS + 5,
                           "the fixture must outlive the bound under test")
        agent = ClaudeAgent(
            run=self.outliving(says=self.document("api_error"), status=1),
            home=self.scratch)
        began = time.monotonic()
        status, record, partial = agent._ran_provider(
            [claude_agent.PROVIDER_PROGRAM], cwd=self.scratch, seconds=600,
            env={"HOME": self.scratch, "PATH": "/usr/bin:/bin"})
        elapsed = time.monotonic() - began
        self.assertEqual(status, 1)
        self.assertLess(elapsed, claude_agent.PROVIDER_DRAIN_SECONDS + 5,
                        "the reader waited on a descendant's descriptor")
        self.assertTrue(partial, "an unfinished stream was called whole")
        self.assertEqual(claude_agent._failure_reason(record, partial=partial),
                         "unclassified")

    def test_a_descendant_holding_stdout_publishes_only_the_fallback(self):
        """End to end, and the retained bytes really do carry the marker.

        The document the LEADER wrote parses and would have earned a word.
        It does not get one, because a stream that never proved it finished is
        a prefix of a record rather than a record — the same rule the ceiling
        is under, arrived at the other way.
        """
        agent = ClaudeAgent(
            run=self.outliving(says=self.document("api_error"), status=1),
            home=self.scratch)
        began = time.monotonic()
        answered = agent.work({"contract": "t"}, list(DECLARED))
        elapsed = time.monotonic() - began
        self.assertLess(elapsed, claude_agent.PROVIDER_DRAIN_SECONDS + 5)
        self.assertEqual(self.result()["provider"]["failure_reason"],
                         "unclassified")
        self.assertEqual(answered["disposition"], "unable")
        self.clean(answered)

    def test_a_timed_out_provider_with_a_descendant_still_ends(self):
        """The same hazard, reached from the timeout path.

        `subprocess.run` kills its DIRECT child and nothing else, so a
        provider that timed out can leave exactly the same inherited writer
        behind. The bound has to be in the `finally`, which is where the
        reader's clock is started, or the failing turn hangs instead.
        """
        agent = ClaudeAgent(
            run=self.outliving(says=self.document("api_error"), status=1,
                               leader_sleeps=self.LINGERS),
            home=self.scratch)
        began = time.monotonic()
        with self.assertRaises(subprocess.TimeoutExpired):
            agent._ran_provider([claude_agent.PROVIDER_PROGRAM],
                                cwd=self.scratch, seconds=1,
                                env={"HOME": self.scratch,
                                     "PATH": "/usr/bin:/bin"})
        elapsed = time.monotonic() - began
        self.assertLess(elapsed, claude_agent.PROVIDER_DRAIN_SECONDS + 6)

    # -- the streams that did not move --------------------------------------

    def test_a_success_publishes_no_reason_and_none_of_the_marker(self):
        """A clean turn writes its structured record too, and none of it is
        read into anything published -- the field is null rather than a word
        readers learn to ignore."""
        answered = self.turned(says=self.document("api_error"), status=0)
        self.assertEqual(answered["disposition"], "completed")
        self.assertIsNone(self.result()["provider"]["failure_reason"])
        self.clean(answered)

    def test_the_provider_stderr_is_still_never_read(self):
        """The child above writes the marker to BOTH streams. Stdout is read,
        bounded and discarded; stderr is not opened at all, and that half of
        W39357 is untouched by this Work."""
        answered = self.turned(says=self.document("api_error"), status=1,
                               also_stderr=True)
        self.clean(answered)
        self.assertEqual(self.result()["provider"]["failure_reason"],
                         "api-error")

    def test_the_verification_streams_are_still_devnull(self):
        """W55360 must not weaken the sharper half: verification is
        provider-EDITED code with the same credential mount readable."""
        agent = ClaudeAgent(run=self.speaking(says=self.document("api_error"),
                                              status=0),
                            home=self.scratch)
        calls = []
        held = agent._run

        def watched(argv, **options):
            calls.append((list(argv), dict(options)))
            return held(argv, **options)

        agent._run = watched
        agent.work({"contract": "t"}, list(DECLARED))
        _argv, options = next(
            (argv, options) for argv, options in calls
            if argv[0] != claude_agent.PROVIDER_PROGRAM)
        self.assertIs(options["stdout"], subprocess.DEVNULL)
        self.assertIs(options["stderr"], subprocess.DEVNULL)

    def test_the_map_is_closed_and_matched_by_equality(self):
        """No prefix, no substring, no pattern. A near miss is a miss."""
        self.assertEqual(claude_agent.PROVIDER_FAILURE_REASONS,
                         {"api_error": "api-error"})
        for near in ("api_error ", " api_error", "api_errors", "API_ERROR",
                     "an api_error occurred", "api-error"):
            with self.subTest(reason=near):
                self.assertEqual(
                    claude_agent._failure_reason(
                        json.dumps({"terminal_reason": near}).encode("utf-8"),
                        partial=False),
                    "unclassified")


class TheCredentialIsLinkedAndNeverRead(AdapterCase):

    def test_the_providers_credential_path_points_at_the_mounted_slot(self):
        self.worked(edits={"harness.py": "print('now covered')\n"})
        _argv, options = next((argv, options) for argv, options in self.calls
                              if argv[0] == claude_agent.PROVIDER_PROGRAM)
        link = os.path.join(options["env"]["HOME"], ".claude",
                            ".credentials.json")
        self.assertTrue(os.path.islink(link), link)
        self.assertEqual(os.readlink(link), self.slot)

    def test_the_bearer_bytes_are_never_opened(self):
        """THE PROPERTY, measured rather than asserted about intent.

        The slot is replaced by a directory, which makes any attempt to READ
        it fail — and the turn still completes, because this adapter only ever
        writes a path.
        """
        os.unlink(self.slot)
        os.makedirs(self.slot)
        answered = self.worked(edits={"harness.py": "print('covered')\n"})
        self.assertEqual(answered["disposition"], "completed")

    def test_an_absent_credential_refuses_rather_than_falling_back(self):
        """The finding forbids a home-directory or ambient default."""
        os.unlink(self.slot)
        with self.assertRaises(TaskRefusal) as refused:
            self.worked(edits={"harness.py": "print('covered')\n"})
        self.assertIn("no home-directory or ambient fallback",
                      str(refused.exception))

    def test_an_unreadable_credential_refuses_before_the_provider_runs(self):
        """W52800, and it is the case that would have saved three attempts.

        THE OLD GUARD WAS `os.path.exists`, which is a `stat` -- so a slot
        delivered at a mode this container's fixed uid cannot open passed it,
        was symlinked into the private home, and became a provider that
        printed `Not logged in` and exited 1. The manager's mode was the
        defect and is corrected there; this is the half that makes the same
        failure SAY WHAT IT IS instead of arriving three layers away from its
        cause.

        MISSING AND UNREADABLE ARE DIFFERENT REFUSALS, because they are
        different operator actions: one is a delivery that did not happen, the
        other is a delivery whose permissions do not admit this runtime.

        THAT THE CHECK ITSELF READS NOTHING is already the property
        `test_the_bearer_bytes_are_never_opened` measures, by replacing the
        slot with a directory and requiring the turn to complete: `os.access`
        answers for the effective identity without a descriptor, so that case
        still passes with this guard in place.
        """
        os.chmod(self.slot, 0o000)
        self.addCleanup(os.chmod, self.slot, 0o600)

        with self.assertRaises(TaskRefusal) as refused:
            self.worked(edits={"harness.py": "print('covered')\n"})

        self.assertIn("cannot READ its credential", str(refused.exception))
        self.assertNotIn("no home-directory or ambient fallback",
                         str(refused.exception))
        # AND NO PROVIDER RAN. The refusal is before the launch, which is the
        # whole point: an unreadable delivery must not become a provider
        # failure whose diagnostic may not be published.
        self.assertEqual(
            [argv for argv, _options in self.calls
             if argv and argv[0] == claude_agent.PROVIDER_PROGRAM], [],
            "the provider was launched with a credential it cannot read")

    def test_no_bearer_reaches_the_argv_or_the_result(self):
        self.worked(edits={"harness.py": "print('now covered')\n"})
        rendered = json.dumps(self.result()) + json.dumps(
            [argv for argv, _options in self.calls])
        self.assertNotIn("not-a-credential", rendered)

    def test_a_provider_created_link_cannot_copy_the_bearer_to_the_proposal(
            self):
        """The provider controls the candidate after the trusted source-copy
        check. Its tree must be revalidated before diffing or publication, or
        a link can turn the fixed credential mount into an output source."""
        def run(argv, **options):
            if argv[0] == claude_agent.PROVIDER_PROGRAM:
                os.symlink(self.slot,
                           os.path.join(options["cwd"], "credential-copy"))
                return subprocess.CompletedProcess(argv, 0, b"", b"")
            return subprocess.CompletedProcess(argv, 0, b"ok\n", b"")

        agent = ClaudeAgent(run=run, home=self.scratch)
        try:
            agent.work({"contract": "the frozen task"}, list(DECLARED))
        except TaskRefusal:
            return
        copied = self.proposal("candidate", "credential-copy")
        self.assertFalse(os.path.exists(copied), copied)
        for name in ("change.patch", "result.json", "verification.txt"):
            with open(self.proposal(name), encoding="utf-8") as handle:
                self.assertNotIn("not-a-credential", handle.read(), name)

    def test_verification_cannot_swap_a_checked_parent_for_the_credential_root(
            self):
        """Validation must remain true through the final candidate read.

        Verification executes code from the provider-edited candidate after
        `_checked_tree` and `_diff`, but before `_publish`.  `O_NOFOLLOW` on
        the final file does not protect an intermediate directory component,
        so replacing that directory with a link can redirect the later open
        into the mounted credential root.
        """
        def run(argv, **options):
            nested = os.path.join(options["cwd"], "nested")
            if argv[0] == claude_agent.PROVIDER_PROGRAM:
                self.write(os.path.join(nested, "claude"), "ordinary\n")
            else:
                shutil.rmtree(nested)
                os.symlink(self.credentials, nested)
            return subprocess.CompletedProcess(argv, 0, b"", b"")

        agent = ClaudeAgent(run=run, home=self.scratch)
        with self.assertRaises(TaskRefusal):
            agent.work({"contract": "the frozen task"}, list(DECLARED))
        copied = self.proposal("candidate", "nested", "claude")
        if os.path.exists(copied):
            with open(copied, encoding="utf-8") as handle:
                self.assertNotIn("not-a-credential", handle.read())

    def test_verification_cannot_replace_checked_file_bytes_with_the_credential(
            self):
        """Revalidation must hold CONTENT, not only path shape.

        The verification program runs after `_diff` measures the candidate and
        before `_publish` reads it.  Replacing an already-checked regular
        file's bytes therefore needs no link at all: a path-only revalidation
        accepts the file and publishes bytes that neither `change.patch` nor
        `changed_paths` measured.  The mounted credential makes that evidence
        mismatch a disclosure boundary as well as an integrity failure.
        """
        def run(argv, **options):
            nested = os.path.join(options["cwd"], "nested")
            target = os.path.join(nested, "claude")
            if argv[0] == claude_agent.PROVIDER_PROGRAM:
                self.write(target, "ordinary\n")
                self.write(os.path.join(options["cwd"], "harness.py"),
                           "print('now covered')\n")
            else:
                shutil.copyfile(self.slot, target)
            return subprocess.CompletedProcess(argv, 0, b"", b"")

        agent = ClaudeAgent(run=run, home=self.scratch)
        with self.assertRaises(TaskRefusal):
            agent.work({"contract": "the frozen task"}, list(DECLARED))
        self.assertFalse(os.path.exists(self.proposal()), self.proposal())

    def test_verification_cannot_replace_its_capture_with_the_credential(self):
        """Capture state must not be reachable by the verification command.

        The reviewer's regression (2026-08-29T22:18:55Z [P1]) ran the attack
        against the `capture-*/stdout` pathname the first round created inside
        the candidate: unlink it once its descriptor is open, put a link to
        the credential there, and the bounded reader — which reopened the NAME
        — transcribed the bearer.

        The adapter now captures NOTHING at all, so the case asserts the
        strongest form of what it started as: the child sees no capture
        pathname anywhere it can reach, and the swap it can still attempt
        against any pathname it does find cannot reach the transcript. The
        credential assertion is the reviewer's, unchanged through three
        rounds of remedy.
        """
        visible = []

        def run(argv, **options):
            if argv[0] == claude_agent.PROVIDER_PROGRAM:
                self.write(os.path.join(options["cwd"], "harness.py"),
                           "print('now covered')\n")
                return subprocess.CompletedProcess(argv, 0, b"", b"")
            # NOTHING NAMED IS LEFT FOR IT, in its own working directory or in
            # the adapter's private scratch — which the same-uid child could
            # have reached just as easily as its own cwd.
            for base in (options["cwd"], self.scratch):
                for where, directories, files in os.walk(base):
                    visible.extend(
                        os.path.join(where, name)
                        for name in directories + files
                        if name.startswith("capture-")
                        or name in ("stdout", "stderr"))
            # ...and the historical attack, against whatever it did find.
            for place in visible:
                os.unlink(place)
                os.symlink(self.slot, place)
            return subprocess.CompletedProcess(argv, 0, b"", b"")

        agent = ClaudeAgent(run=run, home=self.scratch)
        agent.work({"contract": "the frozen task"}, list(DECLARED))
        self.assertEqual(visible, [])
        with open(self.proposal("verification.txt"),
                  encoding="utf-8") as handle:
            transcript = handle.read()
        self.assertNotIn("not-a-credential", transcript)
        # THE TRANSCRIPT IS STILL A TRANSCRIPT. This asserted `"ok"` — the
        # child's own stdout — which is precisely what the 2026-08-30T04:01:29Z
        # finding says may not be there. What proves the file is not merely
        # empty is the evidence no child wrote.
        self.assertIn("$ python3 harness.py", transcript)
        self.assertIn("exit: 0", transcript)

    def test_verification_cannot_print_the_mounted_credential(self):
        """The transcript cannot trust provider-edited verification output.

        The frozen command runs code from the candidate the provider just
        edited, and that process can read the same fixed credential mount as
        the provider.  It therefore needs no pathname race to disclose the
        bearer: writing it to either captured stream is enough unless the
        verification boundary makes the mount unavailable or withholds the
        untrusted bytes from the proposal.

        THE REVIEWER'S CASE, RUN AGAINST A REAL CHILD. Its original form wrote
        the bearer to `options["stdout"]`, which was a file object while the
        adapter still captured. The remedy is that both streams are
        `subprocess.DEVNULL` — an operand only a real `subprocess.run` can
        honour — so the disclosure it models is performed by an actual process
        writing the actual bytes to its actual fd 1 and 2. The assertion is
        the reviewer's, unchanged and now stronger.
        """
        def run(argv, **options):
            if argv[0] == claude_agent.PROVIDER_PROGRAM:
                self.write(os.path.join(options["cwd"], "harness.py"),
                           "print('now covered')\n")
                return subprocess.CompletedProcess(argv, 0, b"", b"")
            return subprocess.run(
                [sys.executable, "-c",
                 f"import sys;"
                 f"bearer = open({self.slot!r}, 'rb').read();"
                 f"sys.stdout.buffer.write(bearer);"
                 f"sys.stderr.buffer.write(bearer)"], **options)

        agent = ClaudeAgent(run=run, home=self.scratch)
        agent.work({"contract": "the frozen task"}, list(DECLARED))
        with open(self.proposal("verification.txt"), "rb") as handle:
            transcript = handle.read()
        self.assertNotIn(b"not-a-credential", transcript)

    def test_provider_stderr_cannot_print_the_mounted_credential(self):
        """A bounded provider diagnostic is still an untrusted secret sink.

        THE REVIEWER'S CASE, RUN AGAINST A REAL CHILD for the reason the case
        above gives, and EXTENDED TO THE SINK IT DID NOT NAME: `why` is what
        `recap` is composed from, so the interpolated diagnostic reached the
        worker's own `/output/output.json` as well as `result.json`.
        """
        def run(argv, **options):
            self.assertEqual(argv[0], claude_agent.PROVIDER_PROGRAM)
            return subprocess.run(
                [sys.executable, "-c",
                 f"import sys;"
                 f"sys.stderr.buffer.write("
                 f"open({self.slot!r}, 'rb').read());"
                 f"raise SystemExit(3)"], **options)

        agent = ClaudeAgent(run=run, home=self.scratch)
        answered = agent.work({"contract": "the frozen task"}, list(DECLARED))
        with open(self.proposal("result.json"), "rb") as handle:
            result = handle.read()
        self.assertNotIn(b"not-a-credential", result)
        self.assertNotIn("not-a-credential", answered["recap"])


class TheCheckedTreeIsProvedAtEveryComponent(AdapterCase):
    """W39357 review 2026-08-29T22:18:55Z [P1], as properties of the reader.

    The reviewer's own regressions drive the attack through `work`. These hold
    the two invariants that make it impossible, so a later change that keeps
    the attack out by accident still fails here.
    """

    def rooted(self):
        root = os.path.join(self.home, "rooted")
        self.write(os.path.join(root, "nested", "claude"), "ordinary\n")
        return root

    def test_an_intermediate_link_is_refused_rather_than_followed(self):
        root = self.rooted()
        self.assertEqual(claude_agent._read_under(root, "nested/claude", "t"),
                         b"ordinary\n")
        shutil.rmtree(os.path.join(root, "nested"))
        os.symlink(self.credentials, os.path.join(root, "nested"))
        with self.assertRaises(TaskRefusal) as refused:
            claude_agent._read_under(root, "nested/claude", "t")
        self.assertIn("without following a link", str(refused.exception))

    def test_a_final_link_is_refused_rather_than_followed(self):
        root = self.rooted()
        os.unlink(os.path.join(root, "nested", "claude"))
        os.symlink(self.slot, os.path.join(root, "nested", "claude"))
        with self.assertRaises(TaskRefusal):
            claude_agent._read_under(root, "nested/claude", "t")

    def test_a_swapped_tree_refuses_before_one_output_byte_is_written(self):
        """`_open_under` makes each read safe on its own; the revalidation
        after the payload's own command is what keeps a refusal from landing
        part-way through a published proposal."""
        def run(argv, **options):
            nested = os.path.join(options["cwd"], "nested")
            if argv[0] == claude_agent.PROVIDER_PROGRAM:
                self.write(os.path.join(nested, "claude"), "ordinary\n")
            else:
                shutil.rmtree(nested)
                os.symlink(self.credentials, nested)
            return subprocess.CompletedProcess(argv, 0, b"", b"")

        agent = ClaudeAgent(run=run, home=self.scratch)
        with self.assertRaises(TaskRefusal):
            agent.work({"contract": "the frozen task"}, list(DECLARED))
        self.assertFalse(os.path.exists(self.proposal()), self.proposal())


class TheMeasuredBytesAreWhatGetPublished(AdapterCase):
    """W39357 review 2026-08-29T22:51:53Z [P1], as properties.

    The reviewer's regression drives the mutation through `work`. These hold
    the rule around it: what verification may do, what it may not, and what
    the ceilings still cover once untrusted code has run.
    """

    def verifying(self, act):
        """A provider that edits, then a verification command that does
        `act` in the candidate."""
        def run(argv, **options):
            if argv[0] == claude_agent.PROVIDER_PROGRAM:
                self.write(os.path.join(options["cwd"], "harness.py"),
                           "print('now covered')\n")
            else:
                act(options["cwd"])
            return subprocess.CompletedProcess(argv, 0, b"", b"")
        return ClaudeAgent(run=run, home=self.scratch)

    def test_a_verification_that_grows_a_checked_file_is_refused(self):
        """Appending needs no link and no new inode, and it makes the patch an
        account of bytes the proposal does not carry."""
        def grow(cwd):
            with open(os.path.join(cwd, "harness.py"), "a") as handle:
                handle.write("# and one more line\n")

        with self.assertRaises(TaskRefusal) as refused:
            self.verifying(grow).work({"contract": "t"}, list(DECLARED))
        self.assertIn("changed at harness.py", str(refused.exception))
        self.assertFalse(os.path.exists(self.proposal()))

    def test_a_verification_that_deletes_a_checked_file_is_refused(self):
        with self.assertRaises(TaskRefusal):
            self.verifying(
                lambda cwd: os.unlink(os.path.join(cwd, "preflight.py"))
            ).work({"contract": "t"}, list(DECLARED))
        self.assertFalse(os.path.exists(self.proposal()))

    def test_a_verification_that_only_adds_is_not_a_fault(self):
        """A command that leaves a cache behind has invalidated nobody's
        evidence: what it added was never measured and is never published."""
        answered = self.verifying(
            lambda cwd: self.write(os.path.join(cwd, "__pycache__", "x.pyc"),
                                   "bytecode\n")
        ).work({"contract": "t"}, list(DECLARED))
        self.assertEqual(answered["disposition"], "completed")
        self.assertEqual(sorted(os.listdir(self.proposal("candidate"))),
                         ["harness.py", "preflight.py"])

    def test_what_verification_adds_is_counted_against_the_ceiling(self):
        """A fixed list could not see what ran AFTER it, so the bound the
        module advertises stopped applying at exactly the moment untrusted
        code did."""
        held = claude_agent.MAX_SOURCE_ENTRIES
        claude_agent.MAX_SOURCE_ENTRIES = 2
        self.addCleanup(setattr, claude_agent, "MAX_SOURCE_ENTRIES", held)
        with self.assertRaises(TaskRefusal) as refused:
            self.verifying(
                lambda cwd: os.mkdir(os.path.join(cwd, "one-more-entry"))
            ).work({"contract": "t"}, list(DECLARED))
        self.assertIn("exceeds this adapter's bound", str(refused.exception))

    def test_a_link_verification_leaves_behind_is_refused_by_the_fresh_walk(
            self):
        with self.assertRaises(TaskRefusal):
            self.verifying(
                lambda cwd: os.symlink(self.slot,
                                       os.path.join(cwd, "late-link"))
            ).work({"contract": "t"}, list(DECLARED))
        self.assertFalse(os.path.exists(self.proposal()))

    def test_the_published_bytes_are_the_bytes_the_patch_describes(self):
        """The positive half, so the rule is not only proved by refusals."""
        self.worked(edits={"harness.py": "print('now covered')\n"})
        with open(self.proposal("candidate", "harness.py"),
                  encoding="utf-8") as handle:
            published = handle.read()
        with open(self.proposal("change.patch"), encoding="utf-8") as handle:
            patch = handle.read()
        self.assertEqual(published, "print('now covered')\n")
        self.assertIn("+print('now covered')", patch)


class FailureIsHonest(AdapterCase):
    """Four ways a turn does not produce a useful result, and none of them may
    be reported as one."""

    def ended(self, **operands):
        answered = self.worked(**operands)
        return answered["disposition"], self.result()["disposition"]

    def test_a_provider_that_exits_nonzero_is_not_completed(self):
        self.assertEqual(self.ended(status=3),
                         ("unable", "provider-failed"))
        # THE STATUS, WHICH CAME FROM `wait`. This asserted that the
        # provider's own stderr appeared in `why` — which was the disclosure
        # W39357 review 2026-08-30T04:01:29Z [P1] found, so the assertion had
        # to go with it. What replaces it is that the failure is still named
        # exactly, and `NoChildStreamByteReachesTheProposal` holds the other
        # half: a real shouting provider reaches neither `why` nor `recap`.
        self.assertIn("the provider exited 3", self.result()["why"])

    def test_a_provider_that_never_started_is_not_completed(self):
        self.assertEqual(self.ended(missing=True),
                         ("unable", "provider-failed"))

    def test_a_provider_that_did_not_finish_is_not_completed(self):
        self.assertEqual(self.ended(timeout=True),
                         ("unable", "provider-failed"))

    def test_a_clean_turn_that_changed_nothing_is_not_completed(self):
        self.assertEqual(self.ended(), ("unable", "no-candidate"))

    def test_a_candidate_whose_verification_failed_is_not_completed(self):
        self.assertEqual(
            self.ended(edits={"harness.py": "raise SystemExit(1)\n"},
                       verify=1),
            ("unable", "verification-failed"))

    def test_a_failed_turn_still_publishes_the_required_output(self):
        """The declaration says the proposal is required, and the worker
        refuses an answer that reports a required output absent. So a failure
        writes the tree and says what happened in it."""
        self.worked(status=3)
        self.assertTrue(os.path.isdir(self.proposal()))
        self.assertTrue(os.path.exists(self.proposal("result.json")))

    def test_the_verification_is_not_run_when_there_is_no_candidate(self):
        """A verification against an unchanged tree would pass and mean
        nothing; running it would manufacture evidence."""
        self.worked()
        self.assertEqual([argv for argv, _o in self.calls
                          if argv[0] != claude_agent.PROVIDER_PROGRAM], [])


class TheFrozenTaskIsAClosedDocument(AdapterCase):

    def refuses(self, document, expected):
        self.task(document)
        with self.assertRaises(TaskRefusal) as refused:
            self.worked()
        self.assertIn(expected, str(refused.exception))

    def test_an_absent_task_refuses(self):
        self.refuses(None, "no readable")

    def test_a_task_from_another_generation_refuses(self):
        self.refuses(dict(TASK, schema="baton.dogfood-task/2"),
                     "another generation")

    def test_an_extra_member_refuses(self):
        self.refuses(dict(TASK, alias="a second identity"), "unexpected alias")

    def test_a_missing_member_refuses(self):
        short = {name: value for name, value in TASK.items()
                 if name != "verification"}
        self.refuses(short, "missing verification")

    def test_a_task_identity_is_text_before_it_is_matched(self):
        """`str(7)` matches the identity regex, but a JSON number is not the
        versioned task's text identity and the sender already refuses it."""
        self.refuses(dict(TASK, task_id=7), "usable task identity")

    def test_a_verification_that_is_a_string_refuses(self):
        """There is no shell in this image, so a command this adapter would
        have to split is a command it cannot run."""
        self.refuses(dict(TASK, verification="python3 harness.py"),
                     "non-empty list of words")

    def test_a_source_root_other_than_the_fixed_one_refuses(self):
        """Review [P2]: containment was the wrong rule.

        `SOURCE_ROOT` was defined and never read, so the effective source was
        selected by the task payload while the module and the dossier both
        said the path is a constant. Any OTHER value is refused now, not only
        an escaping one — a sibling inside `/input` is exactly as much a
        payload-selected source as `../elsewhere` is.
        """
        for wrong in ("../elsewhere", "/etc", "a/../..", "..", "elsewhere",
                      "source/nested", ""):
            with self.subTest(source_root=wrong):
                self.refuses(dict(TASK, source_root=wrong),
                             "stages exactly 'source'"
                             if wrong else "bounded non-empty text")


class TheSourceCopyIsBoundedAndFollowsNoLink(AdapterCase):

    def test_a_link_in_the_staged_tree_refuses(self):
        os.symlink("/etc", os.path.join(self.source, "escape"))
        with self.assertRaises(TaskRefusal) as refused:
            self.worked()
        self.assertIn("link", str(refused.exception))

    def test_an_absent_source_tree_refuses(self):
        shutil.rmtree(self.source)
        with self.assertRaises(TaskRefusal) as refused:
            self.worked()
        self.assertIn("stages no source tree", str(refused.exception))

    def test_an_empty_source_tree_refuses(self):
        for name in os.listdir(self.source):
            os.unlink(os.path.join(self.source, name))
        with self.assertRaises(TaskRefusal) as refused:
            self.worked()
        self.assertIn("is empty", str(refused.exception))

    def test_a_tree_past_the_entry_bound_refuses(self):
        held = claude_agent.MAX_SOURCE_ENTRIES
        claude_agent.MAX_SOURCE_ENTRIES = 1
        self.addCleanup(setattr, claude_agent, "MAX_SOURCE_ENTRIES", held)
        with self.assertRaises(TaskRefusal) as refused:
            self.worked()
        self.assertIn("exceeds this adapter's bound", str(refused.exception))

    def test_staged_directories_count_against_the_entry_bound(self):
        """Review [P2], the other walk. A second party that counts differently
        from the walk it is checking is not proving the same thing."""
        os.mkdir(os.path.join(self.source, "one-more-entry"))
        held = claude_agent.MAX_SOURCE_ENTRIES
        claude_agent.MAX_SOURCE_ENTRIES = 2
        self.addCleanup(setattr, claude_agent, "MAX_SOURCE_ENTRIES", held)
        with self.assertRaises(TaskRefusal) as refused:
            self.worked()
        self.assertIn("exceeds this adapter's bound", str(refused.exception))

    def test_provider_created_directories_count_against_the_entry_bound(self):
        """The candidate bound covers directories as well as regular files."""
        held = claude_agent.MAX_SOURCE_ENTRIES
        claude_agent.MAX_SOURCE_ENTRIES = 2
        self.addCleanup(setattr, claude_agent, "MAX_SOURCE_ENTRIES", held)

        def run(argv, **options):
            if argv[0] == claude_agent.PROVIDER_PROGRAM:
                os.mkdir(os.path.join(options["cwd"], "one-more-entry"))
                self.write(os.path.join(options["cwd"], "harness.py"),
                           "print('now covered')\n")
            return subprocess.CompletedProcess(argv, 0, b"", b"")

        agent = ClaudeAgent(run=run, home=self.scratch)
        with self.assertRaises(TaskRefusal) as refused:
            agent.work({"contract": "the frozen task"}, list(DECLARED))
        self.assertIn("exceeds this adapter's bound", str(refused.exception))


class TheAgentContractIsWholeAndTheWorkerOwnsTheRest(AdapterCase):

    def test_exactly_one_declared_output_is_honoured(self):
        agent = ClaudeAgent(run=self.provider(), home=self.scratch)
        for declared in ([], list(DECLARED) * 2, "not a list"):
            with self.subTest(declared=declared):
                with self.assertRaises(TaskRefusal):
                    agent.work({}, declared)

    def test_consider_declines_rather_than_inventing_a_decision(self):
        """This runtime is not entitled to be asked; the object still answers
        the whole contract rather than the reachable half."""
        answered = ClaudeAgent().consider({"contract": "anything"}, {})
        self.assertEqual(answered["decision"], "decline")
        self.assertEqual(sorted(answered),
                         ["contract_digest", "decision", "reason"])

    def test_the_adapter_publishes_no_completion_manifest(self):
        """`/output/output.json` is the WORKER's document, published after
        this returns. An adapter that wrote one would be publishing protocol
        identity from the least trusted thing in the container."""
        self.worked(edits={"harness.py": "print('now covered')\n"})
        self.assertFalse(os.path.exists(
            os.path.join(self.outputs, "output.json")))

    def test_this_module_imports_nothing_from_the_manager(self):
        """The image's whole isolation rule, held as a property of the source
        rather than as a comment."""
        import ast
        tree = ast.parse((WORKER / "claude_agent.py").read_text("utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for one in node.names:
                    self.assertFalse(one.name.startswith("baton_v12"))
            elif isinstance(node, ast.ImportFrom):
                self.assertFalse((node.module or "").startswith("baton_v12"))


class TheRecipeIsInspectableWithoutADaemon(unittest.TestCase):
    """What the image says about itself, read off the recipe."""

    def setUp(self):
        self.lines = [one.strip() for one
                      in (WORKER / "Dockerfile.claude").read_text(
                          "utf-8").splitlines()
                      if one.strip() and not one.strip().startswith("#")]

    def test_the_provider_version_is_pinned(self):
        self.assertIn("ARG CLAUDE_VERSION=2.1.247", self.lines)

    def test_the_entrypoint_is_the_reference_worker_with_the_agent_injected(
            self):
        self.assertIn('ENTRYPOINT ["python3", "/opt/baton/dogfood_entry.py"]',
                      self.lines)
        entry = (WORKER / "dogfood_entry.py").read_text("utf-8")
        self.assertIn("from baton_worker import main", entry)
        self.assertIn("main(agent=ClaudeAgent())", entry)

    def test_the_reviewed_worker_and_its_frozen_contract_travel(self):
        for copied in ("COPY baton_worker.py /opt/baton/baton_worker.py",
                       "COPY claude_agent.py /opt/baton/claude_agent.py",
                       "COPY worker-control-1.0.schema.json "
                       "/opt/baton/worker-control-1.0.schema.json"):
            self.assertIn(copied, self.lines)

    def test_the_fixed_non_root_identity_matches_the_adapters_restriction(
            self):
        self.assertIn("USER 65532:65532", self.lines)

    def test_no_provider_credential_is_named_in_the_image(self):
        """ASSERTED OVER THE INSTRUCTIONS, not the file.

        `self.lines` is comment-stripped, and the first cut of this case was
        not: it read the whole recipe and failed on the paragraph that explains
        why `ENV ANTHROPIC_*` is absent. A case that a comment can fail is a
        case that says nothing about the image.
        """
        for line in self.lines:
            self.assertFalse(line.startswith("ENV ANTHROPIC"), line)
            self.assertNotIn("ANTHROPIC_API_KEY=", line)
            self.assertNotIn("ANTHROPIC_AUTH_TOKEN=", line)

    def test_the_retired_environment_transport_is_absent(self):
        for line in self.lines:
            self.assertNotIn("BATON_WORKER_", line)

    def test_nothing_from_the_manager_is_copied_in(self):
        for line in self.lines:
            if line.startswith("COPY"):
                self.assertNotIn("baton_v12", line)


if __name__ == "__main__":
    unittest.main()
