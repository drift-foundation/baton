"""W6633 — the OCI reference worker image and its entry point.

The acceptance this file answers to:

  a reproducible recipe with an immutable base/image digest and explicit
  runtime user/entrypoint; a protected framed channel with bounded input and
  output and no ambient authority or engine access; scripted consent, decline,
  execution and fault fixtures; and the approved `baton.worker-entry/1`
  envelope — every frame bound to an exact posture-session identity with a
  one-use operation id, closed per operation, and answered in one correlated
  shape.

WHAT IS HERE AND WHAT IS NEXT DOOR. This suite establishes what the image WILL
be and what the entry point DOES, from the recipe and the program. The built
image, the real containers, and the manager's actual cancellation path are in
`test_worker_container.py`, which drives a daemon — and which FAILS rather than
skips when there is none, because a required gate that quietly passes for being
unable to run is the failure mode this distribution is built against.
"""

import ast
import copy
import io
import json
import os
import pathlib
import shutil
import sys
import unittest

WORKER = (pathlib.Path(__file__).resolve().parents[3] / "worker")
sys.path.insert(0, str(WORKER))

# THE WORKER'S BYTECODE CACHE GOES BEFORE THE IMPORT, AND IT IS NOT HYGIENE.
#
# W19784 review [P1], 2026-08-27. `v12/worker/` is not a package this
# distribution installs; it is a directory a mutation harness rewrites in
# place, repeatedly, inside a single filesystem timestamp tick. CPython
# invalidates a cached `.pyc` by comparing the source's mtime and size, and
# both can be unchanged across two different sources written that fast -- so
# the suite silently executed MUTATION-ERA CODE against restored source.
#
# What that cost was not abstract. The first round's own evidence reported
# seven failures, listed five of them, and concluded there were two; five were
# phantoms of a previous mutation. The review reproduced it and had to pass
# `-B` by hand to see the real tree, which means the ordinary command could not
# reproduce the gate. A transcript nobody can reproduce from the ordinary
# command is not evidence.
#
# So the removal happens HERE, before the import, rather than in whichever
# harness happens to be running: the suite cannot be run against a stale cache
# even by a caller who has never heard of the harnesses. `-B` remains correct
# and is now redundant instead of required.
shutil.rmtree(WORKER / "__pycache__", ignore_errors=True)

import baton_worker                                          # noqa: E402
from baton_worker import (ANSWER_MEMBERS, COMMON_MEMBERS, MAX_FRAME,  # noqa
                          MAX_IDENTITY, OPERATIONS, POSTURES, PROTOCOL,
                          REQUEST_MEMBERS, Uncorrelated, WorkerFault,
                          check_answer, read_frame, serve, write_frame)
from scripted_agent import ScriptedAgent                     # noqa: E402

# THE TWO SESSIONS ARE DIFFERENT, and that is the topology rather than the
# fixture being tidy: an execution session is never a continuation or a
# promotion of a consent one, so the manager mints a separate identity for the
# separate container.
CONSENT_SESSION = "session-consent-1"
EXECUTION_SESSION = "session-execution-1"

CONSENT = {"BATON_WORKER_POSTURE": "consent",
           "BATON_WORKER_SESSION": CONSENT_SESSION,
           "BATON_WORKER_CONTRACT": "do the thing",
           "BATON_WORKER_ROLE": "implementer"}
# W14251, closed: THE TWO POSTURES CARRY THE SAME FOUR MEMBERS. The assignment,
# the workspace and the output path are gone rather than renamed -- with two
# fixed filesystem roots there is nothing left for them to say, and the
# assignment itself arrives as `/input/input.json`.
EXECUTION = {**CONSENT, "BATON_WORKER_POSTURE": "execution",
             "BATON_WORKER_SESSION": EXECUTION_SESSION}

# The WHOLE frozen `outputDescriptor`, constraints included. W6633 eleventh
# review [P1]: this used to omit `constraints`, and so did the worker's own
# member list -- so the ceilings a declaration states were not merely
# unenforced, they were not required to be present, and every case here was
# driving a declaration the contract would refuse.
UNBOUNDED = {"max_bytes": 1048576, "max_entries": 100,
             "allowed_media_types": ["text/plain"],
             "link_policy": "forbid", "validator_digest": None}
DECLARATION = {"name": "proposal", "type": "directory-result",
               "path": "out", "required": True,
               "constraints": dict(UNBOUNDED)}
WORK_REF = {"authority_uuid": "0123456789abcdef0123456789abcdef",
            "work_id": "01234567-W1"}
ASSIGNMENT_REF = {"work_ref": WORK_REF,
                  "participant": "baton.claude", "generation": 1}
POLICY = "sha256:" + "a" * 64
PROFILE = "sha256:" + "b" * 64

# The canonical input manifest the contract record publishes. A fixture I wrote
# by hand is a document built to pass my own reader; this one is not.
VECTORS = (pathlib.Path(__file__).resolve().parents[4] / "work" / "records"
           / "2026" / "08" / "finding-v12-isolated-agent-workers" / "findings"
           / "finding-v12-worker-contract" / "findings"
           / "finding-worker-control-api-manifests" / "evidence"
           / "vectors.json")


def canonical_input(declarations):
    """The published input manifest, carrying THIS fixture's declarations.

    W19784: the previous fixture wrote `{"assignment_ref": ..., "outputs":
    ...}` -- a document the frozen `inputManifest` schema forbids, invented to
    give the worker an identity the real document does not carry. That fixture
    is exactly what hid the defect this Work fixes, so it is gone rather than
    extended: the input side is now the record's own vector, and the identity
    comes from the second document beside it.
    """
    corpus = json.loads(VECTORS.read_text(encoding="utf-8"))
    manifest = next(one["document"] for one in corpus["valid"]
                    if one["name"] ==
                    "input-manifest-directory-and-declared-output")
    manifest = dict(manifest, work_ref=dict(WORK_REF), outputs=declarations,
                    policy_digest=POLICY, runtime_profile_digest=PROFILE)
    manifest.pop("manifest_digest", None)
    manifest["manifest_digest"] = baton_worker.digest(manifest)
    return manifest


def _resealed_document(document):
    """A document whose own digest describes its own (edited) bytes, so what
    refuses it is the rule under test rather than the digest rule."""
    document.pop("manifest_digest", None)
    document["manifest_digest"] = baton_worker.digest(document)
    return document


def delivered_assignment(given, **spoiled):
    """The assignment manifest the manager materializes beside it.

    Minted against THAT input manifest's digest, which is what makes the pair
    one delivery rather than two halves of two.
    """
    document = {"version": given["version"], "manifest_id": "assignment-1",
                "created_at": given["created_at"], "extensions": {},
                "schema": "baton.worker-manifest/assignment",
                "assignment_ref": copy.deepcopy(ASSIGNMENT_REF),
                "assignment_contract": given["assignment_contract"],
                "offer_id": "offer-1", "runtime_attempt_id": "attempt-1",
                "input_manifest_digest": given["manifest_digest"],
                "policy_digest": given["policy_digest"],
                "runtime_profile_digest": given["runtime_profile_digest"],
                "claim_receipt_digest": "sha256:" + "c" * 64,
                "claim_event_seq": 7,
                "activated_at": given["created_at"]}
    document.update(spoiled)
    document.pop("manifest_digest", None)
    document["manifest_digest"] = baton_worker.digest(document)
    return document


# A fixture sentinel: "this document is not delivered at all", told apart
# from "no override given" so a case can stage a HALF delivery.
DELETE = object()


def staged(case, declarations=None, roots=None, assignment=None,
           input_manifest=None):
    """A read-only `/input/` and a writable `/output/`, for a direct run.

    THE ROOTS ARE PATCHED ON THE MODULE RATHER THAN PASSED IN, and that is the
    contract's own shape showing through: they are CONSTANTS, so there is no
    operand for a fixture to supply. A test may reach into the module; a
    caller may not reach into the contract.

    W19784: `/input/` now carries TWO manager-authored documents. `assignment`
    and `input_manifest` let a case deliver a deliberately mis-composed pair;
    `assignment=DELETE` leaves the second document out entirely.
    """
    import tempfile
    from baton_worker import ASSIGNMENT_MANIFEST, INPUT_MANIFEST
    import baton_worker
    import scripted_agent
    home = tempfile.mkdtemp(prefix="v12-worker-io-")
    inputs = os.path.join(home, "input")
    outputs = os.path.join(home, "output")
    os.makedirs(inputs)
    os.makedirs(outputs)
    declarations = [dict(DECLARATION)] if declarations is None else declarations
    given = canonical_input(declarations) if input_manifest is None \
        else input_manifest
    if assignment is None:
        assignment = delivered_assignment(given)
    for name, document in ((INPUT_MANIFEST, given),
                           (ASSIGNMENT_MANIFEST, assignment)):
        if document is DELETE:
            continue
        with open(os.path.join(inputs, name), "w", encoding="utf-8") as handle:
            json.dump(document, handle)
    for module, name, value in ((baton_worker, "INPUT_ROOT", inputs),
                                (baton_worker, "OUTPUT_ROOT", outputs),
                                (scripted_agent, "OUTPUT_ROOT", outputs)):
        held = getattr(module, name)
        setattr(module, name, value)
        case.addCleanup(setattr, module, name, held)
    case.addCleanup(shutil.rmtree, home, True)
    return inputs, outputs

_minted = iter(range(1, 10_000))


def ask(operation, session, **members):
    """One request in the approved envelope, with a fresh operation id.

    Fresh by default because an id is consumed once per session: a fixture
    that reused one would be driving the replay fence by accident and calling
    it something else.
    """
    return {"protocol": PROTOCOL, "session": session,
            "operation_id": f"op-{next(_minted)}", "operation": operation,
            **members}


def frames(*documents):
    payload = b""
    for document in documents:
        body = json.dumps(document).encode("utf-8")
        payload += str(len(body)).encode("ascii") + b"\n" + body
    return io.BytesIO(payload)


def answers(payload):
    stream = io.BytesIO(payload)
    found = []
    while True:
        one = read_frame(stream)
        if one is None:
            return found
        found.append(one)


def run(environment, *requests, agent=None):
    out = io.BytesIO()
    status = serve(frames(*requests), out, environment,
                   agent or ScriptedAgent())
    return status, answers(out.getvalue())


def consent(operation="describe", **members):
    return ask(operation, CONSENT_SESSION, **members)


def execution(operation="describe", **members):
    return ask(operation, EXECUTION_SESSION, **members)


# -- the envelope ------------------------------------------------------------

class TheEnvelopeBindsEveryFrame(unittest.TestCase):
    """Exclusive stdio is transport isolation, not message identity.

    Every case here drives a frame that is well-formed as a frame and wrong as
    a REQUEST, and requires the refusal to arrive correlated — so a sender can
    always match the answer to what it asked.
    """

    def refusing(self, code, request, environment=None):
        status, given = run(environment or CONSENT, request)
        self.assertEqual(len(given), 1, given)
        self.assertIs(given[0]["ok"], False)
        self.assertEqual(given[0]["code"], code, given[0]["message"])
        return given[0]

    def test_a_well_formed_request_is_answered_and_correlated(self):
        request = consent("describe")
        status, given = run(CONSENT, request)
        self.assertEqual(status, 0)
        self.assertEqual(sorted(given[0]),
                         ["answer", "ok", "operation_id", "protocol",
                          "session"])
        for member in ("protocol", "session", "operation_id"):
            self.assertEqual(given[0][member], request[member], member)

    def test_a_fault_carries_the_same_identity_and_nothing_else(self):
        answer = self.refusing("posture", consent("work", task="x"))
        self.assertEqual(sorted(answer),
                         ["code", "message", "ok", "operation_id", "protocol",
                          "session"])

    def test_a_frame_naming_another_session_is_refused(self):
        """A worker answers only the session the manager minted for it."""
        self.refusing("session", ask("describe", "session-somebody-else"))

    def test_a_consent_worker_refuses_the_execution_sessions_frames(self):
        """The cross-posture case, which is the one the topology is about: an
        execution session is never a continuation of a consent one, so a frame
        minted for the other container is refused even though the OPERATION
        would be legal here."""
        self.refusing("session", ask("describe", EXECUTION_SESSION))
        self.refusing("session", ask("describe", CONSENT_SESSION),
                      environment=EXECUTION)

    def test_a_frame_speaking_another_protocol_is_refused(self):
        self.refusing("protocol",
                      {**consent("describe"), "protocol": "baton.other/9"})

    def test_a_missing_identity_member_is_answered_by_no_frame_at_all(self):
        """The ruling forbids inventing an uncorrelated response shape, so a
        frame this program cannot read an identity out of gets no answer and a
        non-zero exit; the manager already owns the launched session and
        settles that from the engine."""
        for member in ("protocol", "session", "operation_id"):
            with self.subTest(missing=member):
                request = consent("describe")
                del request[member]
                status, given = run(CONSENT, request)
                self.assertEqual((status, given), (1, []))

    def test_an_identity_member_that_is_not_bounded_text_is_uncorrelatable(
            self):
        for what, value in [("null", None), ("a number", 7), ("empty", ""),
                            ("oversized", "x" * (MAX_IDENTITY + 1))]:
            with self.subTest(what=what):
                request = {**consent("describe"), "operation_id": value}
                status, given = run(CONSENT, request)
                self.assertEqual((status, given), (1, []))

    def test_an_operation_id_is_consumed_once_within_a_session(self):
        request = consent("describe")
        status, given = run(CONSENT, request, dict(request))
        self.assertIs(given[0]["ok"], True)
        self.assertIs(given[1]["ok"], False)
        self.assertEqual(given[1]["code"], "replay")
        self.assertEqual(given[1]["operation_id"], request["operation_id"])

    def test_an_id_that_reached_the_agent_is_spent_whatever_the_outcome(self):
        """"It failed, so you may send it again" is exactly the reasoning a
        replay fence exists to refuse: this program cannot know whether the
        first attempt's side effects happened."""
        staged(self)
        class Angry:
            def work(self, seen, request):
                raise ZeroDivisionError("after doing half of it")

        request = execution("work")
        status, given = run(EXECUTION, request, dict(request), agent=Angry())
        self.assertEqual(given[0]["code"], "agent")
        self.assertEqual(given[1]["code"], "replay")

    def test_a_frame_refused_for_its_shape_never_spends_its_id(self):
        """The other side of the same rule, and the reason the fence sits
        where it does: a request that never reached the agent had no effect to
        be uncertain about, so a sender that corrects its frame may use the id
        it never spent."""
        staged(self)
        # W19784, migrating W6633's leftover: this used to send the CLEAN frame
        # first and the broken one second, which worked only while `work` had
        # an operand of its own to omit. Under the artifact-neutral request the
        # clean frame succeeds, so the broken one has to come first for the
        # rule to be about anything.
        request = execution("work")
        status, given = run(EXECUTION, {**request, "invented": "build"},
                            dict(request))
        self.assertEqual(given[0]["code"], "protocol")
        self.assertIs(given[1]["ok"], True)

    def test_a_missing_session_identity_produces_no_frame(self):
        """Without it nothing this program says could be matched to anything,
        which is the case the ruling hands to the Worker Manager."""
        without = {name: value for name, value in CONSENT.items()
                   if name != "BATON_WORKER_SESSION"}
        status, given = run(without, consent("describe"))
        self.assertEqual((status, given), (2, []))


# -- the closure is per operation --------------------------------------------

class TheClosureIsPerOperation(unittest.TestCase):
    """Closure one level coarser than the contract is closure over the wrong
    thing: an execution `describe` carrying `task` used to succeed, because
    some OTHER operation of that posture takes one."""

    def test_each_operation_names_exactly_its_own_members(self):
        self.assertEqual(REQUEST_MEMBERS["describe"], COMMON_MEMBERS)
        self.assertEqual(REQUEST_MEMBERS["consider"], COMMON_MEMBERS)
        self.assertEqual(REQUEST_MEMBERS["work"], COMMON_MEMBERS)

    def test_describe_does_not_accept_another_operations_member(self):
        status, given = run(EXECUTION, execution("describe", invented="x"))
        self.assertIs(given[0]["ok"], False)
        self.assertEqual(given[0]["code"], "protocol")
        self.assertIn("unexpected invented", given[0]["message"])

    def test_an_unknown_member_is_refused_rather_than_ignored(self):
        status, given = run(CONSENT, consent("consider", assignment="a-1"))
        self.assertEqual(given[0]["code"], "protocol")
        self.assertIn("assignment", given[0]["message"])

    def test_a_member_no_operation_names_is_named(self):
        """W19784, migrating W6633's leftover. This asserted "missing task",
        and `work` no longer takes a `task` -- W14251 closed every operation to
        the common envelope. A test of a member that no longer exists asserts
        nothing, so what it checks now is the surviving half of the same rule:
        the refusal NAMES what was wrong rather than saying the frame was bad.
        """
        staged(self)
        request = execution("work")
        status, given = run(EXECUTION, {**request, "task": "build"})
        self.assertEqual(given[0]["code"], "protocol")
        self.assertIn("unexpected task", given[0]["message"])

    def test_an_unknown_operation_is_refused_before_anything_else(self):
        status, given = run(CONSENT, consent("meditate"))
        self.assertEqual(given[0]["code"], "protocol")


# -- the answer is a boundary too --------------------------------------------

class TheAnswerIsValidatedBeforeItIsFramed(unittest.TestCase):
    """The agent is the least trusted thing inside this container, and an
    answer is what crosses out of it."""

    def answering(self, answer, operation="consider", environment=None):
        class Fixed:
            def consider(self, seen, request):
                return answer

            def work(self, seen, request):
                return answer

        request = ask(operation,
                      CONSENT_SESSION if operation == "consider"
                      else EXECUTION_SESSION,
                      )
        status, given = run(environment or CONSENT, request, agent=Fixed())
        return given[0]

    def test_the_pinned_answer_sets_are_what_the_contract_names(self):
        self.assertEqual(ANSWER_MEMBERS["describe"],
                         ("protocol", "posture", "operations", "environment"))
        self.assertEqual(ANSWER_MEMBERS["consider"],
                         ("contract_digest", "decision", "reason"))
        self.assertEqual(ANSWER_MEMBERS["work"],
                         ("disposition", "outputs", "recap"))

    def test_an_answer_with_an_extra_member_never_becomes_a_frame(self):
        given = self.answering({"contract_digest": "sha256:x",
                                "decision": "accept", "reason": "fine",
                                "plan": "and also this"})
        self.assertEqual(given["code"], "answer")
        self.assertIn("unexpected plan", given["message"])

    def test_an_answer_missing_a_member_never_becomes_a_frame(self):
        given = self.answering({"decision": "accept", "reason": "fine"})
        self.assertEqual(given["code"], "answer")
        self.assertIn("missing contract_digest", given["message"])

    def test_an_answer_member_that_is_not_bounded_text_is_refused(self):
        given = self.answering({"contract_digest": "sha256:x",
                                "decision": {"nested": "object"},
                                "reason": "fine"})
        self.assertEqual(given["code"], "answer")

    def test_an_agents_output_answer_is_held_against_the_declarations(self):
        """W14251, closed. `workspace` is gone, and what replaces it is not a
        looser member -- it is a stricter one. The agent says which declared
        outputs it produced; the worker fills the type and the path from the
        DECLARATION and measures the bytes itself, so an agent cannot rename an
        output, move it, invent one, or describe material it did not write."""
        staged(self)
        for what, answer in (
                ("an invented output",
                 {"disposition": "completed", "recap": "done",
                  "outputs": [{"name": "invented", "status": "present",
                               "result_metadata": {}}]}),
                ("a declaration left unanswered",
                 {"disposition": "completed", "recap": "done",
                  "outputs": []}),
                ("a required output answered missing",
                 {"disposition": "completed", "recap": "done",
                  "outputs": [{"name": "proposal",
                               "status": "missing-optional",
                               "result_metadata": {}}]}),
                ("a member the answer does not name",
                 {"disposition": "completed", "recap": "done",
                  "outputs": [{"name": "proposal", "status": "present",
                               "result_metadata": {}, "path": "/elsewhere"}]}),
                ("a disposition this contract never had",
                 {"disposition": None, "recap": "done", "outputs": []})):
            with self.subTest(what=what):
                given = self.answering(answer, operation="work",
                                       environment=EXECUTION)
                self.assertIs(given["ok"], False)
                # `agent` rather than `answer`: these refusals arise on the
                # agent path, which the channel already reports as such. What
                # matters is that the frame is a correlated refusal rather
                # than a published envelope -- the code is the channel's own
                # classification of where it happened.
                self.assertIn(given["code"], ("agent", "answer"))

    def test_the_scripted_work_answer_is_exactly_the_pinned_set(self):
        staged(self)
        status, given = run(EXECUTION, execution("work"))
        self.assertEqual(sorted(given[0]["answer"]),
                         sorted(ANSWER_MEMBERS["work"]))

    def test_the_correlated_work_answer_names_outputs_only(self):
        """The completion envelope carries workerOutput documents; the framed
        answer carries only their bounded names. They are distinct surfaces."""
        staged(self)
        status, given = run(EXECUTION, execution("work"))
        self.assertIs(given[0]["ok"], True)
        self.assertEqual(given[0]["answer"]["outputs"], ["proposal"])


class TheArtifactNeutralInputIsTheFrozenManifest(unittest.TestCase):

    def test_a_contract_valid_input_manifest_reaches_the_agent(self):
        """The reference worker consumes the contract's actual inputManifest.

        W19784 CLOSED THIS. The case used to overwrite the fixture's document
        with the published vector, because the fixture wrote a test-only
        `{"assignment_ref": ..., "outputs": ...}` that the frozen input schema
        forbids -- and the worker read the identity out of it. That was the
        workaround the finding names. `staged` now delivers the record's own
        input manifest AND the assignment manifest beside it, so this case
        needs no overwrite: the ordinary fixture IS the contract-valid pair.
        """
        inputs, _outputs = staged(self)
        with open(os.path.join(inputs, "input.json"), encoding="utf-8") as one:
            self.assertEqual(json.load(one)["schema"],
                             "baton.worker-manifest/input")

        class Reached:
            def work(self, seen, declared):
                raise ZeroDivisionError("the valid input reached the agent")

        status, given = run(EXECUTION, execution("work"), agent=Reached())
        self.assertEqual(given[0]["code"], "agent")

    def test_declared_output_limits_hold_before_completion_publication(self):
        """Constraints are assignment inputs, not manager-only commentary.

        The reference agent writes more than one byte. A declaration with a
        one-byte ceiling must prevent both a success frame and publication of
        the completion signal.
        """
        limited = {**DECLARATION,
                   "constraints": {"max_bytes": 1, "max_entries": 1,
                                   "allowed_media_types": ["text/plain"],
                                   "link_policy": "forbid",
                                   "validator_digest": None}}
        _inputs, outputs = staged(self, declarations=[limited])

        status, given = run(EXECUTION, execution("work"))
        self.assertIs(given[0]["ok"], False)
        self.assertFalse(os.path.exists(os.path.join(outputs, "output.json")))

    def test_a_declared_output_path_cannot_escape_the_output_root(self):
        """The worker consumes the path, so it owns the relative-path check.

        A manager-side validation does not make an unsafe join safe inside the
        container. The scripted agent must not write outside `/output`, and a
        completion manifest must not make such material look authorized.
        """
        escaped = {**DECLARATION, "path": "../tmp/escaped",
                   "constraints": {"max_bytes": 1024, "max_entries": 1,
                                   "allowed_media_types": ["text/plain"],
                                   "link_policy": "forbid",
                                   "validator_digest": None}}
        _inputs, outputs = staged(self, declarations=[escaped])

        status, given = run(EXECUTION, execution("work"))
        self.assertFalse(os.path.exists(os.path.join(
            os.path.dirname(outputs), "tmp", "escaped", "result.txt")))
        self.assertFalse(os.path.exists(os.path.join(outputs, "output.json")))
        self.assertIs(given[0]["ok"], False)


class ADeclarationIsProvedBeforeAnAgentIsDispatched(unittest.TestCase):
    """W6633 eleventh review [P1], and the order is the whole content.

    The worker used to check that four member names were present and hand the
    declarations straight to the agent, which wrote under
    `os.path.join(OUTPUT_ROOT, path)`. Everything below now runs BEFORE
    `agent.work`, so a declaration this worker cannot honour never becomes
    bytes anywhere -- and the cases prove that by watching for the agent.
    """

    def refusing(self, declaration, expect_agent=False):
        reached = []

        class Watching:
            def work(self, seen, declared):
                reached.append(True)
                raise AssertionError("an unproved declaration reached the agent")

        _inputs, outputs = staged(self, declarations=declaration)
        status, given = run(EXECUTION, execution("work"), agent=Watching())
        self.assertIs(given[0]["ok"], False)
        self.assertEqual(given[0]["code"], "input")
        self.assertEqual(reached, [])
        self.assertFalse(os.path.exists(os.path.join(outputs, "output.json")))
        return given[0]

    def test_a_descriptor_that_is_not_the_frozen_shape_refuses(self):
        """The closed set is the contract's own. A member missing is a
        declaration this worker would have to guess the rest of; a member
        extra is one it would be ignoring."""
        for what, spoiled in (
                ("constraints missing",
                 {name: value for name, value in DECLARATION.items()
                  if name != "constraints"}),
                ("required missing",
                 {name: value for name, value in DECLARATION.items()
                  if name != "required"}),
                ("a member the descriptor does not name",
                 {**DECLARATION, "destination": "elsewhere"})):
            with self.subTest(what=what):
                self.refusing([spoiled])

    def test_constraints_that_are_not_the_frozen_shape_refuse(self):
        for what, spoiled in (
                ("a ceiling missing",
                 {name: value for name, value in UNBOUNDED.items()
                  if name != "max_bytes"}),
                ("a member the constraints do not name",
                 {**UNBOUNDED, "max_depth": 3}),
                ("a ceiling that is not a whole number",
                 {**UNBOUNDED, "max_entries": "many"}),
                ("a negative ceiling", {**UNBOUNDED, "max_bytes": -1})):
            with self.subTest(what=what):
                self.refusing([{**DECLARATION, "constraints": spoiled}])

    def test_descriptor_values_are_the_frozen_types_and_bounds(self):
        """Deriving member names is not validation of the members' values.

        These are all outside the shipped schema. Each value is consumed or
        copied by this worker, so none may reach the agent on the strength of
        the manager having validated an earlier view of the input root.
        """
        for what, spoiled in (
                ("a numeric name", {**DECLARATION, "name": 7}),
                ("a numeric type", {**DECLARATION, "type": 7}),
                ("a textual required flag",
                 {**DECLARATION, "required": "true"}),
                ("media types that are not a list",
                 {**DECLARATION, "constraints": {
                     **UNBOUNDED, "allowed_media_types": "text/plain"}}),
                ("a link policy outside the frozen const",
                 {**DECLARATION, "constraints": {
                     **UNBOUNDED, "link_policy": "allow"}}),
                ("an entry ceiling above the frozen maximum",
                 {**DECLARATION, "constraints": {
                     **UNBOUNDED, "max_entries": 100001}}),
                ("a byte ceiling above the frozen maximum",
                 {**DECLARATION, "constraints": {
                     **UNBOUNDED, "max_bytes": 9007199254740992}})):
            with self.subTest(what=what):
                self.refusing([spoiled])

    def test_each_frozen_keyword_can_refuse_on_its_own(self):
        """W6633 twelfth review: prove each guard fails INDEPENDENTLY.

        Every value below is chosen so that exactly ONE keyword rejects it and
        the others accept it. `name` of 161 characters still matches the
        `opaqueId` pattern, so only `maxLength` sees it; a two-character media
        type has no pattern at all, so only `minLength` does; and `True` is an
        `int` in Python and is neither an integer in JSON nor caught by the
        bounds, so only the type rule tells it apart from the number one.
        """
        for what, spoiled in (
                ("a name longer than the frozen maximum",
                 {**DECLARATION, "name": "a" * 161}),
                ("a media type shorter than the frozen minimum",
                 {**DECLARATION, "constraints": {
                     **UNBOUNDED, "allowed_media_types": ["ab"]}}),
                ("a media type longer than the frozen maximum",
                 {**DECLARATION, "constraints": {
                     **UNBOUNDED, "allowed_media_types": ["x" * 161]}}),
                ("a media type that is not text",
                 {**DECLARATION, "constraints": {
                     **UNBOUNDED, "allowed_media_types": [7]}}),
                ("media types that repeat",
                 {**DECLARATION, "constraints": {
                     **UNBOUNDED,
                     "allowed_media_types": ["text/plain", "text/plain"]}}),
                ("a boolean where a ceiling belongs",
                 {**DECLARATION, "constraints": {
                     **UNBOUNDED, "max_entries": True}}),
                ("a validator digest that is neither a digest nor null",
                 {**DECLARATION, "constraints": {
                     **UNBOUNDED, "validator_digest": 7}})):
            with self.subTest(what=what):
                self.refusing([spoiled])

    def test_a_regular_file_link_is_refused_too(self):
        """The other half of `link_policy: forbid`. The review's case covers a
        link to a DIRECTORY, which `os.walk` lists separately; this is the one
        that appears in `files`, and the two are refused by two different
        lines."""
        class Linked:
            def work(self, seen, declared):
                place = os.path.join(baton_worker.OUTPUT_ROOT, "out")
                os.makedirs(place)
                target = os.path.join(place, "real.txt")
                with open(target, "w", encoding="utf-8") as handle:
                    handle.write("real\n")
                os.symlink(target, os.path.join(place, "linked.txt"))
                return {"disposition": "completed", "recap": "linked",
                        "outputs": [{"name": "proposal", "status": "present",
                                     "result_metadata": {}}]}

        _inputs, outputs = staged(self)
        status, given = run(EXECUTION, execution("work"), agent=Linked())
        self.assertIs(given[0]["ok"], False)
        self.assertFalse(os.path.exists(os.path.join(outputs, "output.json")))

    def test_a_keyword_this_worker_does_not_implement_is_a_fault(self):
        """THE PROPERTY THAT KEEPS THIS FROM BECOMING A PARAPHRASE AGAIN.

        `_held` is a closed, bounded reader of the keywords these two frozen
        definitions actually use -- not a JSON Schema engine. If a later
        version of them uses a keyword it does not implement, it must REFUSE
        rather than pass silently over it: skipping one is exactly how a
        derived check quietly becomes a weaker one.
        """
        frozen = baton_worker._frozen_contract()
        with self.assertRaises(WorkerFault) as caught:
            baton_worker._held(frozen, {"type": "string", "format": "email"},
                               "someone@example.invalid", "a probe value")
        self.assertIn("format", caught.exception.message)
        # And a type it does not implement is the same answer.
        with self.assertRaises(WorkerFault):
            baton_worker._held(frozen, {"type": "number"}, 1.5, "a probe value")

    def test_a_value_matching_no_frozen_branch_is_refused(self):
        """`validator_digest` is `oneOf` a digest or null, and this is the
        branch where it is NEITHER.

        Exercised directly rather than through a declaration, and the reason
        is a measurement: `_limits` refuses every non-null validator digest
        immediately afterwards, so a declaration carrying `7` is refused
        whether this branch fires or not. A case that cannot fail for the
        reason it names is not evidence about that reason.
        """
        frozen = baton_worker._frozen_contract()
        rule = frozen["$defs"]["outputConstraints"]["properties"][
            "validator_digest"]
        self.assertIn("oneOf", rule)
        self.assertIsNone(baton_worker._held(frozen, rule, None, "a probe"))
        digest = "sha256:" + "b" * 64
        self.assertEqual(baton_worker._held(frozen, rule, digest, "a probe"),
                         digest)
        for neither in (7, "not-a-digest", ["sha256:" + "b" * 64]):
            with self.subTest(value=neither):
                with self.assertRaises(WorkerFault) as caught:
                    baton_worker._held(frozen, rule, neither, "a probe")
                self.assertIn("none of its frozen forms",
                              caught.exception.message)

    def test_a_spelling_the_grammar_refuses_never_reaches_the_agent(self):
        """SEPARATED FROM CONTAINMENT ON PURPOSE. Each of these stays INSIDE
        the output root once resolved, so containment would accept every one
        of them -- what refuses is the frozen `relativePath` grammar, which is
        about the spelling and not about where it lands."""
        # `out/nested/` is DELIBERATELY ABSENT: the frozen grammar accepts a
        # trailing separator, and inventing a stricter rule here would be the
        # paraphrase mistake W19784's third review is the standing lesson
        # about. The contract is the authority for what the spelling may be.
        for path in ("out/./nested", "out//nested", "out/nested/.",
                     "", "out\\nested"):
            with self.subTest(path=path):
                self.refusing([{**DECLARATION, "path": path}])

    def test_a_path_that_resolves_out_of_the_root_never_reaches_the_agent(
            self):
        """AND SEPARATED THE OTHER WAY. This spelling is perfectly canonical
        -- the grammar accepts it -- and it resolves outside the root anyway,
        because a component of it is a link. The grammar is about text; only
        resolution sees this."""
        inputs, outputs = staged(self)
        elsewhere = os.path.join(os.path.dirname(outputs), "elsewhere")
        os.makedirs(elsewhere)
        os.symlink(elsewhere, os.path.join(outputs, "escape"))
        given = self.pointed(inputs, outputs, "escape/inside")
        self.assertIs(given[0]["ok"], False)
        self.assertEqual(given[0]["code"], "input")
        self.assertFalse(os.path.exists(os.path.join(elsewhere, "inside")))

    def pointed(self, inputs, outputs, path):
        """Re-stage the input manifest in an ALREADY staged root, so a case
        can plant filesystem state first and then declare against it."""
        given = canonical_input([{**DECLARATION, "path": path}])
        assignment = delivered_assignment(given)
        for name, document in (("input.json", given),
                               ("assignment.json", assignment)):
            with open(os.path.join(inputs, name), "w",
                      encoding="utf-8") as handle:
                json.dump(document, handle)

        class Watching:
            def work(self, seen, declared):
                raise AssertionError("an unproved declaration reached the agent")

        status, seen = run(EXECUTION, execution("work"), agent=Watching())
        return seen

    def test_the_output_manifest_name_is_reserved(self):
        """`output.json` is this root's protocol document, and its presence
        under its final name is the completion signal. A declared output there
        would have the agent writing the signal."""
        for path in ("output.json", "output.json/tree"):
            with self.subTest(path=path):
                self.refusing([{**DECLARATION, "path": path}])

    def test_one_name_is_declared_once(self):
        self.refusing([DECLARATION, {**DECLARATION, "path": "other"}])

    def test_two_declarations_cannot_name_one_tree(self):
        """§7.2: the same bytes under two names are two artifacts with two
        identities, and retention would decide twice about material that is
        once."""
        for what, second in (
                ("the same tree", {"name": "twin", "path": "out"}),
                ("one inside the other",
                 {"name": "twin", "path": "out/nested"})):
            with self.subTest(what=what):
                self.refusing([DECLARATION, {**DECLARATION, **second}])

    def test_a_stated_validator_digest_is_refused_rather_than_ignored(self):
        """FAIL-CLOSED, not unimplemented. §7.2 makes `type` opaque and the
        manager never branches on it, so a worker running a type-specific
        validator would be branching on exactly that -- and nothing else in
        1.0 runs one either. Publishing a result while ignoring a constraint
        the manager wrote down is the thing this refuses."""
        stated = {**UNBOUNDED, "validator_digest": "sha256:" + "b" * 64}
        self.refusing([{**DECLARATION, "constraints": stated}])

    def test_the_entry_ceiling_refuses_before_publication(self):
        """The scripted agent writes one file per declared output, so a
        zero-entry ceiling is crossed by the first one."""
        bounded = {**UNBOUNDED, "max_entries": 0}
        _inputs, outputs = staged(
            self, declarations=[{**DECLARATION, "constraints": bounded}])
        status, given = run(EXECUTION, execution("work"))
        self.assertIs(given[0]["ok"], False)
        self.assertFalse(os.path.exists(os.path.join(outputs, "output.json")))

    def test_a_directory_link_is_not_silently_omitted_from_measurement(self):
        """`os.walk(..., followlinks=False)` lists a directory link in
        `directories` and then skips it. Ignoring the link is not enforcing
        the frozen `link_policy: forbid`; the completion manifest would claim
        an empty tree while the declared tree still contains a link.
        """
        class Linked:
            def work(self, seen, declared):
                place = os.path.join(baton_worker.OUTPUT_ROOT, "out")
                os.makedirs(place)
                os.symlink(baton_worker.OUTPUT_ROOT,
                           os.path.join(place, "linked-directory"))
                return {"disposition": "completed", "recap": "linked",
                        "outputs": [{"name": "proposal", "status": "present",
                                     "result_metadata": {}}]}

        _inputs, outputs = staged(self)
        status, given = run(EXECUTION, execution("work"), agent=Linked())
        self.assertIs(given[0]["ok"], False)
        self.assertFalse(os.path.exists(os.path.join(outputs, "output.json")))


class TheFramedAnswerIsNotTheCompletionEnvelope(unittest.TestCase):
    """W6633 eleventh review [P1]. Two surfaces carrying different things.

    The completion envelope is the durable document and holds the whole record
    for each output. The framed answer is the correlated reply on the
    worker-entry channel and carries the bounded NAMES of what was produced.
    They used to carry the same records, so the manager received one document
    twice by two routes -- one of them the transport it is supposed to read
    without interpreting.
    """

    def test_the_rule_has_no_exemption_for_outputs(self):
        """`check_answer` is a boundary and is exercised as one. The member
        used to be skipped here on the reasoning that `answered` had already
        built it -- which was about the OTHER document."""
        record = {"name": "proposal", "type": "directory-result",
                  "path": "out", "status": "present",
                  "content_manifest": None, "result_metadata": {}}
        with self.assertRaises(WorkerFault) as caught:
            check_answer("work", {"disposition": "completed",
                                  "outputs": [record], "recap": "done"})
        self.assertEqual(caught.exception.code, "answer")

    def test_an_entry_wider_than_a_frame_is_not_bounded_text(self):
        """A list of unbounded strings is unbounded text with extra steps."""
        with self.assertRaises(WorkerFault):
            check_answer("work", {"disposition": "completed",
                                  "outputs": ["x" * (MAX_FRAME + 1)],
                                  "recap": "done"})

    def test_a_missing_optional_output_is_not_named_as_produced(self):
        """The member is what was PRODUCED. An output answered
        `missing-optional` exists in the envelope with that status and is not
        in this list."""
        optional = {**DECLARATION, "name": "extra", "path": "extra",
                    "required": False}

        class Partial:
            def work(self, seen, declared):
                # It produces one and not the other, and it WRITES the one it
                # claims: the worker measures what is there rather than
                # believing the answer, so an agent that said `present` and
                # wrote nothing is refused before this case could observe
                # anything about naming.
                place = os.path.join(baton_worker.OUTPUT_ROOT, "out")
                os.makedirs(place, exist_ok=True)
                with open(os.path.join(place, "result.txt"), "w",
                          encoding="utf-8") as handle:
                    handle.write("produced\n")
                return {"disposition": "completed", "recap": "done",
                        "outputs": [{"name": "proposal", "status": "present",
                                     "result_metadata": {}},
                                    {"name": "extra",
                                     "status": "missing-optional",
                                     "result_metadata": {}}]}

        _inputs, outputs = staged(self,
                                  declarations=[dict(DECLARATION), optional])
        status, given = run(EXECUTION, execution("work"), agent=Partial())
        self.assertIs(given[0]["ok"], True)
        self.assertEqual(given[0]["answer"]["outputs"], ["proposal"])
        with open(os.path.join(outputs, "output.json"),
                  encoding="utf-8") as one:
            published = json.load(one)
        self.assertEqual(sorted(one["name"] for one in published["outputs"]),
                         ["extra", "proposal"])


class TheGateCannotRunAgainstStaleBytecode(unittest.TestCase):
    """W19784 review [P1], 2026-08-27.

    The defect this answers was in the EVIDENCE rather than in the product,
    which is why it needs a case rather than a note. `v12/worker/` is rewritten
    in place by the mutation harnesses, faster than CPython's mtime-and-size
    invalidation can distinguish, so the ordinary command executed a previous
    mutation's bytecode against restored source -- and the transcript that
    produced was wrong in a way that read as a real result.
    """

    def test_the_cache_is_removed_before_the_worker_is_imported(self):
        """Ordering is the whole content: a removal after the import would
        leave the stale module already loaded."""
        source = pathlib.Path(__file__).read_text(encoding="utf-8")
        removal = source.index('shutil.rmtree(WORKER / "__pycache__"')
        self.assertLess(removal, source.index("\nimport baton_worker"),
                        "the cache is dropped after the worker is imported")

    def test_the_module_under_test_is_the_file_on_disk(self):
        """Not that a cache is absent -- that what this suite has loaded IS the
        current source. A future change that moved the removal, or a runner
        that imported the worker first, would leave this failing rather than
        quietly measuring a different program."""
        loaded = pathlib.Path(baton_worker.__file__).resolve()
        self.assertEqual(loaded, (WORKER / "baton_worker.py").resolve())
        current = ast.parse(loaded.read_text(encoding="utf-8"))
        defined = {node.name for node in current.body
                   if isinstance(node, (ast.FunctionDef, ast.ClassDef))}
        for name in defined:
            with self.subTest(name=name):
                self.assertTrue(
                    hasattr(baton_worker, name),
                    f"{name} is in the source and not in the loaded module; "
                    f"this gate is running stale bytecode")


class TheAssignmentIdentityComesFromItsOwnDocument(unittest.TestCase):
    """W19784, approved 2026-08-26.

    THE DEFECT. `completionManifest` requires the exact full `assignment_ref`
    -- Work reference, participant AND authority generation. `inputManifest` is
    minted before any claim exists and carries no generation; the `work` frame
    carries only the common worker-entry identity; the execution environment
    carries no assignment value. So this worker had nowhere to learn who the
    assignment was, and the only way it published a valid-looking envelope was
    the test-only `input.json` this suite used to write.

    THE FIX is a path and a lifecycle: the manager delivers the already-defined
    assignment manifest, unchanged, at `/input/assignment.json`.
    """

    def envelope(self, outputs):
        with open(os.path.join(outputs, "output.json"), encoding="utf-8") as f:
            return json.load(f)

    def test_the_envelope_carries_the_delivered_identity_exactly(self):
        """The positive that closes the finding: run the whole path and read
        what actually landed in the durable document."""
        inputs, outputs = staged(self)
        status, given = run(EXECUTION, execution("work"))
        self.assertIs(given[0]["ok"], True)
        with open(os.path.join(inputs, "assignment.json"),
                  encoding="utf-8") as one:
            delivered = json.load(one)["assignment_ref"]
        published = self.envelope(outputs)
        self.assertEqual(published["schema"],
                         "baton.worker-manifest/completion")
        self.assertEqual(published["assignment_ref"], delivered)
        # THE GENERATION IS THE POINT. It is the member the input manifest
        # cannot carry and the envelope must, and it arrived unchanged.
        self.assertEqual(published["assignment_ref"]["generation"],
                         ASSIGNMENT_REF["generation"])

    def test_the_identity_is_not_taken_from_the_input_manifest(self):
        """A worker that fell back to the input side would be reading a
        document that has no generation to give -- which is how the defect
        stayed invisible. Deliver an input manifest naming another Work and the
        envelope must still carry the ASSIGNMENT's, or refuse."""
        elsewhere = canonical_input([dict(DECLARATION)])
        elsewhere["work_ref"] = {"authority_uuid": "f" * 32,
                                 "work_id": "ffffffff-W9"}
        elsewhere.pop("manifest_digest", None)
        elsewhere["manifest_digest"] = baton_worker.digest(elsewhere)
        # Minted against the SPOILED input, so every digest binding agrees and
        # the only thing left disagreeing is the Work itself. Otherwise the
        # digest guard would catch this and the case would witness nothing of
        # its own.
        assignment = delivered_assignment(elsewhere)
        assignment["assignment_ref"] = copy.deepcopy(ASSIGNMENT_REF)
        assignment.pop("manifest_digest", None)
        assignment["manifest_digest"] = baton_worker.digest(assignment)
        _inputs, outputs = staged(self, input_manifest=elsewhere,
                                  assignment=assignment)
        status, seen = run(EXECUTION, execution("work"))
        self.assertIs(seen[0]["ok"], False)
        self.assertEqual(seen[0]["code"], "input")
        self.assertFalse(os.path.exists(os.path.join(outputs, "output.json")))

    def test_a_missing_assignment_document_refuses_before_the_agent(self):
        """Nothing is written, because nothing ran. A worker that dispatched an
        agent and only then discovered it could not name the assignment would
        leave material behind that no envelope can describe."""
        reached = []

        class Watching:
            def work(self, seen, declared):
                reached.append(True)
                raise AssertionError("the agent ran without an identity")

        _inputs, outputs = staged(self, assignment=DELETE)
        status, given = run(EXECUTION, execution("work"), agent=Watching())
        self.assertIs(given[0]["ok"], False)
        self.assertEqual(given[0]["code"], "input")
        self.assertEqual(reached, [])
        self.assertFalse(os.path.exists(os.path.join(outputs, "output.json")))

    def test_a_mis_composed_pair_refuses_before_the_agent(self):
        """Each document below is separately readable and separately
        plausible. What refuses is the RELATIONSHIP, and it refuses BEFORE
        dispatch -- so a container composed from two deliveries writes
        nothing."""
        given = canonical_input([dict(DECLARATION)])
        other = "sha256:" + "9" * 64
        for what, spoiled in (
                ("another Work",
                 {"assignment_ref": {
                     "work_ref": {"authority_uuid": "f" * 32,
                                  "work_id": "ffffffff-W9"},
                     "participant": "baton.claude", "generation": 1}}),
                ("another input manifest", {"input_manifest_digest": other}),
                ("another policy", {"policy_digest": other}),
                ("another runtime profile",
                 {"runtime_profile_digest": other})):
            with self.subTest(what=what):
                reached = []

                class Watching:
                    def work(self, seen, declared):
                        reached.append(True)
                        raise AssertionError("a mis-composed pair ran an agent")

                _inputs, outputs = staged(
                    self, input_manifest=given,
                    assignment=delivered_assignment(given, **spoiled))
                status, seen = run(EXECUTION, execution("work"),
                                   agent=Watching())
                self.assertIs(seen[0]["ok"], False)
                self.assertEqual(seen[0]["code"], "input")
                self.assertEqual(reached, [])
                self.assertFalse(
                    os.path.exists(os.path.join(outputs, "output.json")))

    def test_an_identity_this_worker_would_have_to_invent_refuses(self):
        """`assignment_ref` is COPIED, so a delivered value that is not exactly
        the frozen three members is either short of the generation the envelope
        requires or carrying something this worker would be inventing."""
        given = canonical_input([dict(DECLARATION)])
        for what, ref in (
                ("no generation",
                 {"work_ref": dict(WORK_REF), "participant": "baton.claude"}),
                ("an extra member",
                 {**copy.deepcopy(ASSIGNMENT_REF), "session": "s-1"}),
                ("not an object", "01234567-W1")):
            with self.subTest(what=what):
                _inputs, outputs = staged(
                    self, input_manifest=given,
                    assignment=delivered_assignment(given,
                                                    assignment_ref=ref))
                status, seen = run(EXECUTION, execution("work"))
                self.assertIs(seen[0]["ok"], False)
                self.assertEqual(seen[0]["code"], "input")
                self.assertFalse(
                    os.path.exists(os.path.join(outputs, "output.json")))

    def test_a_delivery_missing_a_binding_member_refuses(self):
        """The pair rule cannot be checked against a document that does not
        carry its side of it, and a worker that skipped the comparison because
        the member was absent would be answering "unbound" with "fine"."""
        given = canonical_input([dict(DECLARATION)])
        for name in ("input_manifest_digest", "policy_digest",
                     "runtime_profile_digest", "assignment_ref"):
            with self.subTest(member=name):
                short = delivered_assignment(given)
                short.pop(name)
                short.pop("manifest_digest", None)
                short["manifest_digest"] = baton_worker.digest(short)
                _inputs, outputs = staged(self, input_manifest=given,
                                          assignment=short)
                status, seen = run(EXECUTION, execution("work"))
                self.assertIs(seen[0]["ok"], False)
                self.assertEqual(seen[0]["code"], "input")

    def test_a_malformed_assignment_document_refuses(self):
        inputs, outputs = staged(self)
        with open(os.path.join(inputs, "assignment.json"), "w",
                  encoding="utf-8") as handle:
            handle.write("{not a document")
        status, given = run(EXECUTION, execution("work"))
        self.assertIs(given[0]["ok"], False)
        self.assertEqual(given[0]["code"], "input")
        self.assertFalse(os.path.exists(os.path.join(outputs, "output.json")))

    def test_both_delivered_manifests_prove_their_own_digest_before_dispatch(self):
        """The approved ruling says the worker validates both CLOSED manifests,
        not only that their untrusted digest strings agree with each other."""
        for what in ("input", "assignment"):
            with self.subTest(document=what):
                given = canonical_input([dict(DECLARATION)])
                assignment = delivered_assignment(given)
                if what == "input":
                    false_digest = "sha256:" + "0" * 64
                    given["manifest_digest"] = false_digest
                    assignment["input_manifest_digest"] = false_digest
                    assignment.pop("manifest_digest", None)
                    assignment["manifest_digest"] = baton_worker.digest(
                        assignment)
                else:
                    assignment["manifest_digest"] = "sha256:" + "0" * 64
                reached = []

                class Watching:
                    def work(self, seen, declared):
                        reached.append(True)
                        raise AssertionError("an unproved manifest ran an agent")

                _inputs, outputs = staged(
                    self, input_manifest=given, assignment=assignment)
                _status, seen = run(EXECUTION, execution("work"),
                                    agent=Watching())
                self.assertEqual(seen[0]["code"], "input")
                self.assertEqual(reached, [])
                self.assertFalse(
                    os.path.exists(os.path.join(outputs, "output.json")))

    def test_both_delivered_manifests_are_closed_before_dispatch(self):
        """A second identity alias is invalid even when all pair bindings and
        self-digests agree; shallow extraction is not manifest validation."""
        for what in ("input", "assignment"):
            with self.subTest(document=what):
                given = canonical_input([dict(DECLARATION)])
                if what == "input":
                    given["compatibility_assignment"] = copy.deepcopy(
                        ASSIGNMENT_REF)
                    given.pop("manifest_digest", None)
                    given["manifest_digest"] = baton_worker.digest(given)
                    assignment = delivered_assignment(given)
                else:
                    assignment = delivered_assignment(given)
                    assignment["compatibility_assignment"] = copy.deepcopy(
                        ASSIGNMENT_REF)
                    assignment.pop("manifest_digest", None)
                    assignment["manifest_digest"] = baton_worker.digest(
                        assignment)
                reached = []

                class Watching:
                    def work(self, seen, declared):
                        reached.append(True)
                        raise AssertionError("an open manifest ran an agent")

                _inputs, outputs = staged(
                    self, input_manifest=given, assignment=assignment)
                _status, seen = run(EXECUTION, execution("work"),
                                    agent=Watching())
                self.assertEqual(seen[0]["code"], "input")
                self.assertEqual(reached, [])
                self.assertFalse(
                    os.path.exists(os.path.join(outputs, "output.json")))

    def test_a_document_that_says_it_is_the_other_one_refuses(self):
        """W19784 second round. The closed-member check alone would NOT catch
        this: a document can carry exactly the input manifest's members and
        still declare itself a completion envelope, because `schema` is one of
        those members. The frozen definition pins its value, so the delivery
        is read as what the contract says it is rather than as what the
        document claims.
        """
        given, assignment = self.paired()
        for what, spoiled in (
                ("the input side claiming another schema",
                 (dict(given, schema="baton.worker-manifest/completion"),
                  assignment)),
                ("the assignment side claiming another schema",
                 (given,
                  dict(assignment, schema="baton.worker-manifest/input")))):
            with self.subTest(what=what):
                one, two = (_resealed_document(dict(part))
                            for part in spoiled)
                reached = []

                class Watching:
                    def work(self, seen, declared):
                        reached.append(True)
                        raise AssertionError("a mislabelled document ran an agent")

                _inputs, outputs = staged(self, input_manifest=one,
                                          assignment=two)
                _status, seen = run(EXECUTION, execution("work"),
                                    agent=Watching())
                self.assertEqual(seen[0]["code"], "input")
                self.assertEqual(reached, [])
                self.assertFalse(
                    os.path.exists(os.path.join(outputs, "output.json")))

    def paired(self):
        given = canonical_input([dict(DECLARATION)])
        return given, delivered_assignment(given)

    def test_consent_reads_neither_input_document(self):
        """§7.0: consent mounts nothing. The identity is a document under a
        root a consent container does not have, so the posture boundary is the
        filesystem rather than a rule about a string."""
        reached = []

        class Watching:
            def consider(self, seen, request):
                reached.append(sorted(os.listdir(baton_worker.INPUT_ROOT))
                               if os.path.isdir(baton_worker.INPUT_ROOT)
                               else None)
                return {"decision": "accept", "reason": "ok",
                        "contract_digest": "sha256:" + "0" * 64}

        status, given = run(CONSENT, consent("consider"), agent=Watching())
        self.assertIs(given[0]["ok"], True)
        # No `staged()` here, so `INPUT_ROOT` is the contract's own `/input`,
        # which does not exist on the host running this suite -- which is
        # exactly the shape a consent container has.
        self.assertEqual(reached, [None])
        self.assertNotIn("work", OPERATIONS["consent"])


# -- a bootstrap fault is latched and correlated -----------------------------

class ABootstrapFaultIsLatchedAndCorrelated(unittest.TestCase):
    """The approved startup-correlation ruling. The framing loop is still
    operable, so the failure is answered through the ORDINARY shape after
    exactly one identity envelope — and it never reaches the agent."""

    def latched(self, environment):
        class Never:
            def consider(self, seen, request):
                raise AssertionError("a latched fault reached the agent")

            def work(self, seen, request):
                raise AssertionError("a latched fault reached the agent")

        out = io.BytesIO()
        status = serve(frames(ask("consider", environment.get(
            "BATON_WORKER_SESSION", "session-consent-1"))),
            out, environment, Never())
        return status, answers(out.getvalue())

    def test_an_invalid_posture_is_one_correlated_fault_and_a_non_zero_exit(
            self):
        for posture in (None, "", "admin", "EXECUTION", "consent "):
            with self.subTest(posture=posture):
                environment = dict(CONSENT)
                if posture is None:
                    del environment["BATON_WORKER_POSTURE"]
                else:
                    environment["BATON_WORKER_POSTURE"] = posture
                status, given = self.latched(environment)
                self.assertEqual(status, 1)
                self.assertEqual(len(given), 1)
                self.assertEqual(given[0]["code"], "posture")
                self.assertEqual(given[0]["session"], CONSENT_SESSION)
                self.assertEqual(given[0]["protocol"], PROTOCOL)

    def test_a_container_built_with_the_wrong_material_latches_too(self):
        for name in ("BATON_WORKER_ASSIGNMENT", "BATON_WORKER_WORKSPACE",
                     "BATON_WORKER_OUTPUT"):
            with self.subTest(name=name):
                status, given = self.latched({**CONSENT, name: "leaked"})
                self.assertEqual(status, 1)
                self.assertEqual(given[0]["code"], "posture")
                self.assertIn(name, given[0]["message"])

    def test_a_latched_fault_does_not_answer_another_sessions_envelope(self):
        """Startup correlation does not relax the common session binding.

        A pending bootstrap failure may be returned only after the one
        envelope has established this posture-specific container's identity;
        a frame minted for another session is still refused as such.
        """
        request = ask("consider", "session-somebody-else")
        status, given = run(
            {**CONSENT, "BATON_WORKER_POSTURE": "admin"}, request)
        self.assertEqual(status, 1)
        self.assertEqual(len(given), 1)
        self.assertEqual(given[0]["code"], "session")
        self.assertEqual(given[0]["session"], request["session"])

    def test_a_latched_fault_refuses_a_foreign_protocol_the_same_way(self):
        """The binding is protocol AND session, and both precede the latched
        answer. A container that failed to start is still a container this
        channel's contract applies to."""
        request = consent("consider")
        request["protocol"] = "baton.worker-entry/2"
        status, given = run(
            {**CONSENT, "BATON_WORKER_POSTURE": "admin"}, request)
        self.assertEqual(status, 1)
        self.assertEqual(len(given), 1)
        self.assertEqual(given[0]["code"], "protocol")

    def test_a_refused_binding_on_a_latched_container_still_answers_once(self):
        """The three properties the correction had to KEEP. Which fault a
        latched container names changed; that it writes exactly one frame,
        exits non-zero, and reaches no agent did not."""
        class Never:
            def consider(self, seen, request):
                raise AssertionError("a latched fault reached the agent")

            def work(self, seen, request):
                raise AssertionError("a latched fault reached the agent")

        out = io.BytesIO()
        status = serve(
            frames(ask("consider", "session-somebody-else"),
                   consent("consider")),
            out, {**CONSENT, "BATON_WORKER_POSTURE": "admin"}, Never())
        self.assertEqual(status, 1)
        given = answers(out.getvalue())
        self.assertEqual(len(given), 1, "more than one envelope was read")
        self.assertEqual(given[0]["code"], "session")

    def test_a_healthy_container_keeps_answering_after_a_foreign_frame(self):
        """The other half of the same move: lifting the binding out of
        `handle` must not turn an ordinary wrong-session refusal into the end
        of the channel. Only a LATCHED container stops."""
        status, given = run(EXECUTION,
                            ask("describe", "session-somebody-else"),
                            execution("describe"))
        self.assertEqual(status, 0)
        self.assertEqual([one["code"] for one in given[:1]], ["session"])
        self.assertEqual(len(given), 2)
        self.assertTrue(given[1]["ok"])
        self.assertEqual(given[1]["answer"]["posture"], "execution")

    def test_exactly_one_envelope_is_read_and_the_task_is_never_dispatched(
            self):
        """Reading the envelope grants no task, workspace, output, tool or
        agent capability."""
        class Never:
            def consider(self, seen, request):
                raise AssertionError("a latched fault reached the agent")

            def work(self, seen, request):
                raise AssertionError("a latched fault reached the agent")

        out = io.BytesIO()
        status = serve(frames(consent("consider"), consent("consider")),
                       out, {**CONSENT, "BATON_WORKER_POSTURE": "admin"},
                       Never())
        self.assertEqual(status, 1)
        self.assertEqual(len(answers(out.getvalue())), 1,
                         "more than one envelope was read")

    def test_a_latched_fault_with_no_readable_envelope_says_nothing(self):
        out = io.BytesIO()
        status = serve(io.BytesIO(b""), out,
                       {**CONSENT, "BATON_WORKER_POSTURE": "admin"},
                       ScriptedAgent())
        self.assertEqual((status, answers(out.getvalue())), (1, []))


# -- the channel -------------------------------------------------------------

class TheChannelIsFramedAndBounded(unittest.TestCase):

    def test_a_frame_round_trips(self):
        out = io.BytesIO()
        write_frame(out, {"ok": True})
        self.assertEqual(answers(out.getvalue()), [{"ok": True}])

    def test_the_framing_is_length_prefixed_and_not_newline_delimited(self):
        """A newline is a byte an agent's output legitimately contains, and a
        protocol whose framing a payload can forge has no framing."""
        out = io.BytesIO()
        write_frame(out, {"recap": "line one\nline two"})
        self.assertEqual(answers(out.getvalue()),
                         [{"recap": "line one\nline two"}])

    def test_an_oversized_frame_is_refused_before_it_is_read(self):
        stream = io.BytesIO(str(MAX_FRAME + 1).encode("ascii") + b"\n")
        with self.assertRaises(Uncorrelated):
            read_frame(stream)
        self.assertEqual(stream.tell(), len(str(MAX_FRAME + 1)) + 1,
                         "the body was read despite the refusal")

    def test_a_header_that_never_ends_is_bounded_too(self):
        """A header is caller input, so the bound is on it as well as on the
        body -- otherwise a peer that sends no newline reads forever."""
        with self.assertRaises(Uncorrelated):
            read_frame(io.BytesIO(b"9" * 4096))

    def test_a_malformed_frame_has_no_identity_so_it_gets_no_answer(self):
        for what, payload in [("a header that is not a length", b"abc\n{}"),
                              ("a body that ends early", b"99\n{}"),
                              ("a body that is not JSON", b"2\nno"),
                              ("a body that is not an object", b"2\n[]")]:
            with self.subTest(what=what):
                with self.assertRaises(Uncorrelated):
                    read_frame(io.BytesIO(payload))
                out = io.BytesIO()
                status = serve(io.BytesIO(payload), out, EXECUTION,
                               ScriptedAgent())
                self.assertEqual((status, answers(out.getvalue())), (1, []))

    def test_a_clean_end_of_input_is_an_answer(self):
        self.assertIsNone(read_frame(io.BytesIO(b"")))

    def test_our_own_answer_is_bounded_and_keeps_its_identity(self):
        """An agent that produced an enormous recap must not make this program
        the thing that broke the channel — and a bounds fault that dropped the
        correlation would be the uncorrelated shape arriving by the back
        door."""
        class Loud:
            def consider(self, seen, request):
                return {"contract_digest": "sha256:x", "decision": "accept",
                        "reason": "x" * (MAX_FRAME - 100)}

        request = consent("consider")
        status, given = run(CONSENT, request, agent=Loud())
        self.assertIs(given[0]["ok"], False)
        self.assertEqual(given[0]["code"], "bounds")
        self.assertEqual(given[0]["operation_id"], request["operation_id"])


# -- consent cannot reach execution ------------------------------------------

class ConsentCannotReachExecution(unittest.TestCase):

    def test_a_consent_container_is_not_asked_to_work(self):
        status, given = run(CONSENT, consent("work", task="build"))
        self.assertIs(given[0]["ok"], False)
        self.assertEqual(given[0]["code"], "posture")
        self.assertIn("not asked to", given[0]["message"])

    def test_an_execution_container_is_not_asked_to_consent(self):
        status, given = run(EXECUTION, execution("consider"))
        self.assertEqual(given[0]["code"], "posture")

    def test_the_posture_is_checked_on_every_operation(self):
        """A check that ran once at start is a check a later message walks
        past."""
        status, given = run(CONSENT, consent("describe"),
                            consent("consider"), consent("work", task="x"),
                            consent("consider"))
        self.assertEqual([answer["ok"] for answer in given],
                         [True, True, False, True])

    def test_there_is_no_message_that_promotes_a_consent_worker(self):
        for operation in ("promote", "activate", "execution", "work",
                          "escalate", "become"):
            with self.subTest(operation=operation):
                status, given = run(CONSENT, consent(operation))
                self.assertIs(given[0]["ok"], False)

    def test_assignment_material_cannot_arrive_inside_a_consent_frame(self):
        for name in ("assignment", "workspace", "output", "task"):
            with self.subTest(member=name):
                status, given = run(CONSENT,
                                    consent("consider", **{name: "/leak"}))
                self.assertIs(given[0]["ok"], False)
                self.assertEqual(given[0]["code"], "protocol")


# -- the scripted fixtures ---------------------------------------------------

class TheScriptedFixtures(unittest.TestCase):

    def test_consent_accepts_and_declines_deterministically(self):
        status, accepted = run(CONSENT, consent("consider"))
        self.assertEqual(accepted[0]["answer"]["decision"], "accept")
        status, declined = run(
            {**CONSENT, "BATON_WORKER_CONTRACT": "please decline this"},
            consent("consider"))
        self.assertEqual(declined[0]["answer"]["decision"], "decline")

    def test_a_consent_answer_names_nothing_it_cannot_see(self):
        status, given = run(CONSENT, consent("consider"))
        self.assertEqual(sorted(given[0]["answer"]),
                         ["contract_digest", "decision", "reason"])

    def test_execution_completes_and_recaps(self):
        """W19784, migrating W6633's leftover. This read `answer["workspace"]`
        and asked for a task echoed back into the recap; W14251 removed both --
        a worker writes under a fixed root and the request carries no operand.
        What survives is the part that was ever about this program: a completed
        disposition and a bounded recap of what it actually did."""
        staged(self)
        status, given = run(EXECUTION, execution("work"))
        answer = given[0]["answer"]
        self.assertEqual(answer["disposition"], "completed")
        self.assertNotIn("workspace", answer)
        self.assertTrue(answer["recap"].strip())
        # WHAT `outputs` CARRIES IS NOT SETTLED and this case deliberately does
        # not decide it. `test_the_correlated_work_answer_names_outputs_only`
        # requires bounded names; `check_answer` explicitly exempts the member
        # and `handle` frames the whole published documents. That contradiction
        # is W6633's open slice, not this Work's, and asserting either reading
        # here would quietly pick a winner. What is asserted is the part both
        # readings agree on: one entry, for the one declaration.
        self.assertEqual(len(answer["outputs"]), 1)

    def test_the_same_request_produces_the_same_bytes(self):
        """DETERMINISTIC is what makes a reproducibility case possible."""
        request = execution("work", task="build")
        first = run(EXECUTION, dict(request))
        second = run(EXECUTION, dict(request))
        self.assertEqual(first, second)

    def test_an_agent_fault_is_a_frame_and_carries_no_traceback(self):
        """A traceback would carry paths from inside the image out through the
        channel, and a worker that died would leave the manager waiting for a
        runtime that is gone."""
        staged(self)
        class Angry:
            def work(self, seen, request):
                raise ZeroDivisionError("inside the image")

        status, given = run(EXECUTION, execution("work"), agent=Angry())
        self.assertIs(given[0]["ok"], False)
        self.assertEqual(given[0]["code"], "agent")
        self.assertEqual(given[0]["message"],
                         "the agent failed: ZeroDivisionError")

    def test_a_closed_channel_is_the_manager_closing_it_and_not_cancellation(
            self):
        """SUPERSEDED FIXTURE, and the ruling is why. An input stream empty
        from its first byte used to be called cancellation; the approved
        contract says cancellation is the manager's runtime stop path and is
        never a worker-entry message or a clean EOF.

        What a clean end of input actually means is that the manager closed
        the channel, and this program exits 0 without inventing a fault about
        it. The real cancellation path is exercised against a real container
        in `test_worker_container.py`.
        """
        status, given = run(EXECUTION)
        self.assertEqual((status, given), (0, []))


# -- the recipe --------------------------------------------------------------

class TheRecipeIsInspectableWithoutADaemon(unittest.TestCase):
    """What the image WILL be, asserted from the recipe.

    The built image proves the same properties and more, next door. These are
    the ones this suite can hold without a daemon; they are not a substitute
    for that gate and the record says so.
    """

    def setUp(self):
        self.recipe = (WORKER / "Dockerfile").read_text(encoding="utf-8")
        self.lines = [line.strip() for line in self.recipe.splitlines()
                      if line.strip() and not line.strip().startswith("#")]

    def test_the_base_is_pinned_by_digest_and_never_by_tag(self):
        base = [line for line in self.lines if line.startswith("FROM ")]
        self.assertEqual(len(base), 1, "one base, so one thing to pin")
        self.assertRegex(base[0], r"^FROM \S+@sha256:[0-9a-f]{64}$")
        self.assertNotIn(":latest", self.recipe)

    def test_the_runtime_user_is_a_fixed_non_root_numeric_id(self):
        self.assertIn("USER 65532:65532", self.lines)

    def test_the_entrypoint_is_exec_form_with_no_shell(self):
        """No shell in the process tree, so nothing interprets a signal or a
        metacharacter on the worker's behalf."""
        entry = [line for line in self.lines if line.startswith("ENTRYPOINT")]
        self.assertEqual(
            entry, ['ENTRYPOINT ["python3", "/opt/baton/baton_worker.py"]'])

    def test_the_image_defaults_to_no_posture_and_no_session(self):
        for line in self.lines:
            if line.startswith("ENV"):
                self.assertNotIn("BATON_WORKER_", line)

    def test_the_image_announces_no_network_or_health_surface(self):
        for directive in ("EXPOSE", "VOLUME", "HEALTHCHECK"):
            with self.subTest(directive=directive):
                self.assertEqual([line for line in self.lines
                                  if line.startswith(directive)], [])

    def test_no_secret_or_assignment_material_enters_a_layer(self):
        """An EXHAUSTIVE list, so a layer cannot carry an assignment, a bearer
        or a workspace.

        W19784 review [P0], 2026-08-27: a third entry. The worker derives the
        closed member sets of the manager's two `/input/` documents from the
        frozen contract rather than from a list typed into the program, and
        that requires the contract to be present where the worker runs.

        It stays exhaustive, which is the property that matters: the third
        entry is named exactly, and `test_frozen` proves the file it copies is
        byte-identical to the other four copies. A contract is not an
        assignment, a bearer or a workspace -- it is the document both sides
        are held to, and it is the same in every image ever built.
        """
        copied = [line for line in self.lines if line.startswith("COPY")]
        self.assertEqual(
            copied,
            ["COPY baton_worker.py /opt/baton/baton_worker.py",
             "COPY scripted_agent.py /opt/baton/scripted_agent.py",
             "COPY worker-control-1.0.schema.json "
             "/opt/baton/worker-control-1.0.schema.json"])

    def test_the_shipped_contract_is_data_and_not_a_second_program(self):
        """The one thing that would make the third COPY a mistake: if it were
        code, or if it opened an import path the recipe's own comment says the
        worker must not have."""
        shipped = WORKER / "worker-control-1.0.schema.json"
        self.assertTrue(shipped.is_file())
        json.loads(shipped.read_text(encoding="utf-8"))
        self.assertNotIn(".py", shipped.name)
        # PYTHONPATH is still exactly the program's own directory, and the
        # worker still cannot import the manager.
        self.assertIn("PYTHONPATH=/opt/baton", " ".join(self.lines))
        self.assertNotIn("baton_v12", "\n".join(self.lines))

    def test_the_user_agrees_with_the_adapters_own_restriction(self):
        """Two places agreeing because they were written from one decision."""
        from baton_v12.worker_manager.oci import RESTRICTIONS

        user = dict((flag, value) for flag, value in RESTRICTIONS)["--user"]
        self.assertIn(f"USER {user}", self.lines)


class TheWorkerHoldsNoneOfTheManagersCapabilities(unittest.TestCase):

    def test_the_entry_point_imports_nothing_from_the_distribution(self):
        """A worker that could import the manager is a worker one bug away
        from holding the manager's capabilities.

        Checked structurally rather than trusted: "we did not import it" is a
        property somebody will break by accident.
        """
        for name in ("baton_worker.py", "scripted_agent.py"):
            with self.subTest(name=name):
                tree = ast.parse((WORKER / name).read_text(encoding="utf-8"))
                imported = set()
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        imported.update(alias.name.split(".")[0]
                                        for alias in node.names)
                    elif isinstance(node, ast.ImportFrom) and node.module:
                        imported.add(node.module.split(".")[0])
                self.assertNotIn("baton_v12", imported)
                self.assertFalse(
                    imported & {"socket", "subprocess", "urllib", "http",
                                "sqlite3", "ssl", "ftplib", "telnetlib"},
                    "the worker reaches for a network, a database or a "
                    "process; it has none of those")

    def test_the_protocol_name_is_the_only_thing_it_announces(self):
        status, given = run(CONSENT, consent("describe"))
        answer = given[0]["answer"]
        self.assertEqual(answer["protocol"], PROTOCOL)
        self.assertEqual(answer["posture"], "consent")
        self.assertEqual(answer["operations"], list(OPERATIONS["consent"]))
        self.assertNotIn("BATON_WORKER_ASSIGNMENT", answer["environment"])

    def test_the_two_postures_are_the_whole_set(self):
        self.assertEqual(POSTURES, ("consent", "execution"))
        self.assertEqual(sorted(OPERATIONS), ["consent", "execution"])


if __name__ == "__main__":
    unittest.main()
