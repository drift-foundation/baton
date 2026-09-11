"""W101492 -- one fenced model-driven integration, end to end.

WHAT THESE CASES ARE ABOUT. The assembly: a target's smallest queued entry gets
one live fenced grant and exclusive writable access, a model runs under its own
Work instructions, and the claim it leaves behind earns exactly one coordinator
verb. They are not about admitting a candidate (W101491 proves every member of
the account) or about the boundary's own proofs (W101490 drives those); what is
driven here is the composition and the decision.

THE MODEL IS A FAKE PORT AND IT REALLY WRITES. A deployment supplies a runtime
that starts a container; this suite supplies one that performs a bounded
transformation against a DISPOSABLE TARGET directory and answers through the
same durable delivery, because the contract between them is the files and the
target. Review [P1]: an earlier version of this suite wrote only
`result.json`, so a "clean import" marked an entry integrated when no candidate
byte had moved at all -- `imported_paths` was prose in an untrusted claim. Every
case now snapshots the target's bytes and modes and asserts what did or did not
change.

Still no case starts a runtime, reaches a daemon, or runs a version control
system: the target is a directory and the transformation is one file write.
"""

import copy
import json
import os
import stat
import sys
import unittest
from types import SimpleNamespace
from unittest import mock

from baton_v12.contracts import ContractRefusal, digest
from baton_v12.integration import activate_target, entries_of, lease_of, target_of
from baton_v12.integration import (admission, driver, execution, reconciliation,
                                   runtime)
from baton_v12.integration.admission import admit_candidate
from baton_v12.integration.queue import enqueue
from baton_v12.source_profiles import GIT_PROFILE
from baton_v12.worker_manager import attempts
from .fixtures import (PATHS, PROFILE_KIND, TARGET, TEST_SCOPE, UUID_A,
                       CoordinatorCase, target)

# W133120's end-to-end import reuses W133117's ACCEPTED real fixture rather
# than duplicating a second real Authority, target and producer line. The
# import is the transition; the material it acts on is already proved.
from .test_reconciliation import (FIXED, HARNESS_IDENTITY, INTEGRATOR,
                                  REFERENCE, ResultCase, _run, runner)

# A DEPLOYMENT CHECK THE IMPORTED BYTES REALLY FAIL. It is not the harness the
# result was approved on: review 2026-09-10T14:20:24Z [R1] is about the tests
# an IMPORT must run, and a deployment's post-import suite is not the same
# suite as the combined observation. This one runs for real and really exits
# non-zero on the correct combined content, which is exactly the case the
# failed-test hold exists for.
DEPLOYMENT_CHECK = ("from feature import total\n\n"
                    "answered = total([1, 2, 3])\n"
                    "assert answered == 7, (\n"
                    "    f'the deployment check wanted 7 and got {answered}')\n"
                    "print('the deployment check passed')\n")


class PostImportVerifier:
    """The configured post-import test owner, and it RUNS THE TESTS.

    Review [R1]: the importer used to read the imported tree back and label
    that `verification`. This owner materializes the imported candidate FROM
    THE DEDICATED TARGET and executes a real interpreter against it, so what
    the settlement retains is a command, an input commit and tree, an exit
    status and real output rather than an object comparison.
    """

    def __init__(self, case, *, participant="baton.integration-verify",
                 script=None, identity=HARNESS_IDENTITY, execution=None):
        self._case = case
        self._script = script
        self._identity = identity
        self._execution = execution
        self.participant = participant
        self.asked = []

    def verify_imported(self, basis):
        self.asked.append(dict(basis))
        content = self._case.materialize(self._case.target,
                                         basis["input_commit"])
        if self._script is not None:
            self._case.write(content, "harness.py", self._script)
        with open(os.path.join(content, "harness.py")) as handle:
            body = handle.read()
        answered = _run([sys.executable, "harness.py"], cwd=content)
        tail = answered.stderr.strip().splitlines()[-1:]
        return {"command": sys.executable + " harness.py",
                "test_identity": self._identity,
                "input_commit": basis["input_commit"],
                "input_tree": basis["input_tree"],
                "test_digest": digest(body),
                "environment": sys.executable + " / " + GIT_PROFILE,
                "status": answered.returncode,
                "output": answered.stdout.strip() or (tail[0] if tail else ""),
                "execution": self._execution or self.participant}

PARTICIPANT = "baton.merge"
INSTRUCTIONS = "sha256:" + "7" * 64
IMPORTED = "src/a.py"
CANDIDATE = b"the candidate bytes\n"
# THE MODE AN IMPORTER ESTABLISHES. `open(..., "wb")` takes whatever the
# ambient umask leaves, so a case asserting a mode has to be asserting one
# somebody set -- second review [P1].
IMPORTED_MODE = 0o644
REFUSAL = {"reason": "scope", "detail": {"path": "outside the reviewed set"}}
HELD = {"reason": "integrity", "detail": {"observed": "a mixed working tree"}}


def profile(**changed):
    operands = {"profile_kind": PROFILE_KIND, "profile_version": 1,
                "integrator_participant": PARTICIPANT,
                "instructions_digest": INSTRUCTIONS}
    operands.update(changed)
    return runtime.integration_profile(**operands)


class Model:
    """A runtime port that TRANSFORMS A TARGET and answers through the files.

    IT IS NOT A MOCK OF THE ASSEMBLY. It reaches the delivery exactly as a
    container would -- one document at the fixed name in the namespace it was
    given -- and, where a real one would import, it writes the one declared
    path into the disposable target it was wired with. Where the target lives
    is DEPLOYMENT WIRING and reaches this port rather than the coordinator,
    which is why the port carries it and no core document names it.

    `runs_after` is the manager transition a deployment performs when the
    container stops. It runs INSIDE the port, so the attempt is non-quiescent
    while the model writes and quiescent only afterwards -- the sequence the
    review required and the previous fixture inverted.
    """

    starts = None                       # set by the fixture that owns a manager

    def __init__(self, *, outcome="integrated", detail=None, raw=None,
                 target=None, imports=True, runs=True, runs_after=None,
                 before=None):
        self.outcome, self.detail, self.raw = outcome, detail, raw
        self.target, self.imports, self.runs = target, imports, runs
        self.runs_after, self.before, self.asked = runs_after, before, []
        self.verification = None

    def _started(self, attempt_id):
        """The manager transitions a deployment performs as the container comes
        up. The assembly requires `not-started` when it asks, so the runtime
        that writes is one this port started -- and the delivery already
        existed when it did."""
        if self.runs and self.starts is not None:
            for state in ("start-requested", "running"):
                self.starts(attempt_id, state)

    def _observed(self):
        """The verification a real model produces: what it can READ BACK after
        importing, rather than a constant."""
        place = os.path.join(self.target, IMPORTED)
        with open(place, "rb") as reading:
            return {"path": IMPORTED, "bytes": len(reading.read()),
                    "mode": oct(stat.S_IMODE(os.stat(place).st_mode))}

    def run(self, delivery, assignment):
        self.asked.append((delivery.attempt_id, assignment["entry_id"]))
        try:
            self._started(assignment["attempt_id"])
            if self.outcome == "integrated" and self.imports and self.target:
                place = os.path.join(self.target, IMPORTED)
                os.makedirs(os.path.dirname(place), exist_ok=True)
                with open(place, "wb") as writing:
                    writing.write(CANDIDATE)
                os.chmod(place, IMPORTED_MODE)
                self.verification = self._observed()
            if self.outcome is None and self.raw is None:
                return                                 # started and silent
            place = os.path.join(delivery.result_root,
                                 runtime.RESULT_DOCUMENT)
            if self.raw is not None:
                with open(place, "wb") as writing:
                    writing.write(self.raw)
                return
            detail = self.detail
            if detail is None:
                detail = ({"imported_paths": [IMPORTED],
                           "verification": self.verification}
                          if self.outcome == "integrated" and self.verification
                          else {"integrated": {"imported_paths": [],
                                               "verification": {}},
                                "refused": REFUSAL,
                                "held": HELD}[self.outcome])
            answer = {"schema": runtime.RESULT_SCHEMA,
                      "attempt_id": assignment["attempt_id"],
                      "lease_id": assignment["lease_id"],
                      "canonical_target_id": assignment["canonical_target_id"],
                      "entry_id": assignment["entry_id"],
                      "fence": assignment["fence"],
                      "outcome": self.outcome, "detail": detail}
            with open(place, "wb") as writing:
                writing.write(json.dumps(answer, sort_keys=True).encode("utf-8"))
        finally:
            if self.runs_after is not None:
                self.runs_after(assignment["attempt_id"])
            if self.before is not None:
                self.before()


class _Authority:
    """The Authority source `resolved_account` re-reads, in process.

    `current` is mutable ON PURPOSE: advancing the canonical target while an
    entry waits is exactly the staleness this leaf has to refuse, and a case
    that could not move it could not drive that.
    """

    def __init__(self, proposals, receipts, current):
        self.proposals, self.receipts, self.current = (proposals, receipts,
                                                       current)

    def proposal(self, proposal_id):
        return copy.deepcopy(self.proposals[proposal_id])

    def receipt(self, proposal_id, kind):
        return copy.deepcopy(self.receipts[proposal_id][kind])

    def canonical_target(self):
        return self.current


class ExecutionCase(CoordinatorCase):
    """Two candidates admitted through their REAL producers, one disposable
    target, and a manager whose runtime axis the port drives.

    THE ENTRIES ARE ADMITTED RATHER THAN ENQUEUED. This leaf re-resolves an
    entry's account from the same producers admission used, so a suite that
    inserted entries directly would be testing that re-resolution against
    nothing. The producer reads are patched in `admission`'s own namespace, as
    that leaf's suite patches them, and they DISPATCH ON THE SELECTOR so two
    candidates can exist honestly.
    """

    WORK = "0000000a-W1"
    NOW = "2026-09-06T14:00:00.000Z"

    def setUp(self):
        super().setUp()
        from .test_runtime import _group_of, _manager_of, _recorded_attempt
        self.coordinator = self.store()
        activate_target(self.coordinator, target())
        self.manager = _manager_of(self)
        self.group = _group_of(self)
        self.recorded = _recorded_attempt
        self.launch = os.path.join(self.root, "launch")
        os.makedirs(self.launch)
        # THE DISPOSABLE TARGET. Where a target lives is deployment wiring, so
        # it reaches the PORT and no core document names it.
        self.target = os.path.join(self.root, "target")
        os.makedirs(os.path.join(self.target, "src"))
        with open(os.path.join(self.target, "src", "kept.py"), "wb") as one:
            one.write(b"untouched\n")
        self._producers()
        self.admitted = []
        for one in (1, 2):
            self.admit(one)

    # -- the accepted producers, one set per candidate ----------------------

    def _candidate(self, index):
        evidence = {"profile": GIT_PROFILE, "base": "a" * 40,
                    "head": chr(ord("b") + index) * 40, "tree": "c" * 40,
                    "paths": list(PATHS), "path_set_digest": digest(PATHS),
                    "reference": f"checkpoint/line-{index}/1"}
        line, checkpoint = f"line-{index}", f"checkpoint-{index}"
        writer, proposal = f"writer-{index}", f"proposal-{index}"
        attempt, result = f"writer-attempt-{index}", f"result-{index}"
        manifest = "sha256:" + str(index) * 64
        return {
            "accepted": {"line_id": line, "checkpoint_id": checkpoint,
                         "verdict_id": f"verdict-{index}",
                         "checkpoint_digest": digest(evidence),
                         "evidence": evidence},
            "line": {"line_id": line, "authority_uuid": UUID_A,
                     "work_id": self.WORK,
                     "current_checkpoint_id": checkpoint},
            "checkpoint": {"checkpoint_id": checkpoint, "writer_id": writer,
                           "line_id": line,
                           "checkpoint_digest": digest(evidence),
                           "path_set_digest": digest(PATHS),
                           "evidence": copy.deepcopy(evidence)},
            "writer": {"writer_id": writer, "line_id": line,
                       "runtime_attempt_id": attempt,
                       "assignment_generation": 1,
                       "participant": "baton.impl"},
            "assignment": {"runtime_attempt_id": attempt,
                           "authority_uuid": UUID_A, "work_id": self.WORK,
                           "participant": "baton.impl", "generation": 1,
                           "principal": "principal.impl",
                           "effective_scope": "repository"},
            "frozen": {"attempt_id": attempt, "result_id": result,
                       "disposition": "completed",
                       "manifest_digest": manifest,
                       "freeze_operation_id": f"freeze-{index}",
                       "frozen_at": self.NOW, "artifacts": []},
            "proposal": {
                "proposal_id": proposal,
                "assignment_ref": {
                    "work_ref": {"authority_uuid": UUID_A,
                                 "work_id": self.WORK},
                    "participant": "baton.impl", "generation": 1},
                "decision": {}, "result_id": result,
                "result_digest": manifest,
                "candidate_digest": "sha256:" + str(index) * 63 + "a",
                "input_digest": "sha256:input",
                "policy_digest": "sha256:policy",
                "target": "revision-1", "published_at": self.NOW},
        }

    def _producers(self):
        self.candidates = {one: self._candidate(one) for one in (1, 2)}
        by_line = {c["line"]["line_id"]: c for c in self.candidates.values()}
        by_checkpoint = {c["checkpoint"]["checkpoint_id"]: c
                         for c in self.candidates.values()}
        by_writer = {c["writer"]["writer_id"]: c
                     for c in self.candidates.values()}
        by_attempt = {c["assignment"]["runtime_attempt_id"]: c
                      for c in self.candidates.values()}
        proposals = {c["proposal"]["proposal_id"]: c["proposal"]
                     for c in self.candidates.values()}
        receipts = {
            name: {kind: {"receipt_id": f"{kind}-{name}", "kind": kind,
                          "proposal_id": name, "actor": "baton." + kind,
                          "disposition": disposition,
                          "candidate_digest": one["candidate_digest"],
                          "target": one["target"],
                          "policy_generation":
                              1 if kind == "approval" else None,
                          "recorded_at": self.NOW, "decision": {}}
                   for kind, disposition
                   in admission._RECEIPT_DISPOSITIONS.items()}
            for name, one in proposals.items()}
        self.authority = _Authority(proposals, receipts, "revision-1")
        self.jobs = SimpleNamespace(_connection=lambda: None,
                                    authority_uuid=UUID_A)
        self.job = {"job_id": "job-1", "submission_id": "submission-1",
                    "ordinal": 0, "input_digest": "sha256:input",
                    "policy_digest": "sha256:policy",
                    "test_scope": json.dumps(TEST_SCOPE),
                    "terminal_policy": "report-and-hold"}
        self.stages = [{"stage_id": "job-1/implementation", "job_id": "job-1",
                        "ordinal": 0, "kind": "implementation",
                        "work_id": self.WORK,
                        "profile_name": "implementation",
                        "profile_digest": "sha256:profile",
                        "depends_on": "[]"}]
        patches = {
            "integration_checkpoint": lambda store, line_id:
                copy.deepcopy(by_line[line_id]["accepted"]),
            "line_of": lambda store, line_id:
                copy.deepcopy(by_line[line_id]["line"]),
            "checkpoint_of": lambda store, checkpoint_id:
                copy.deepcopy(by_checkpoint[checkpoint_id]["checkpoint"]),
            "writer_of": lambda store, writer_id:
                copy.deepcopy(by_writer[writer_id]["writer"]),
            "assignment_of": lambda store, attempt_id:
                copy.deepcopy(by_attempt[attempt_id]["assignment"]),
            "frozen_output_of": lambda store, attempt_id:
                copy.deepcopy(by_attempt[attempt_id]["frozen"]),
            "job_rows": lambda store: [copy.deepcopy(self.job)],
            "stages_of": lambda store, job_id: copy.deepcopy(self.stages),
        }
        self.patch = mock.patch.multiple(admission, **patches)
        self.patch.start()
        self.addCleanup(self.patch.stop)

    def admit(self, index):
        answered = admit_candidate(
            self.coordinator, self.manager, self.jobs, self.authority,
            canonical_target_id=TARGET, entry_id=f"entry-{index}",
            line_id=f"line-{index}", proposal_id=f"proposal-{index}")
        self.admitted.append(answered)
        return answered

    # -- running one attempt ------------------------------------------------

    def stopped(self, attempt_id):
        """The manager transition a deployment performs when the container
        stops. It runs inside the port, AFTER the model has written."""
        from .test_runtime import _observed
        _observed(self, attempt_id, "destroyed")

    def started(self, attempt_id, state):
        """One legal manager transition as the container comes up."""
        from .test_runtime import _observed
        _observed(self, attempt_id, state)

    def model(self, **changed):
        operands = {"target": self.target, "runs_after": self.stopped}
        operands.update(changed)
        made = Model(**operands)
        made.starts = self.started
        return made

    def integrate(self, model=None, *, attempt_id="attempt-1",
                  lease_id="lease-1", state=None, complete=True, **changed):
        """One attempt, recorded `not-started` as `record_attempt` leaves it.

        THE PORT DRIVES THE LIFECYCLE, because the assembly requires the
        attempt to be unstarted when it asks: the delivery is materialized
        first, the port's own `_started` records `start-requested` then
        `running`, and its `runs_after` records the stop. `state` is for the
        negatives that need the manager somewhere else before the call.
        """
        model = self.model() if model is None else model
        if isinstance(model, Model) and model.starts is None:
            model.starts = self.started
        self.recorded(self, attempt_id)
        if state is not None:
            from .test_runtime import _observed
            _observed(self, attempt_id, state)
        suffix = attempt_id.rsplit("-", 1)[-1]
        operands = {"canonical_target_id": TARGET,
                    "entry_id": "entry-" + suffix, "profile": profile(),
                    "lease_id": lease_id, "attempt_id": attempt_id,
                    "launch_root": os.path.join(self.launch, attempt_id),
                    "workspace_group": self.group}
        operands.update(changed)
        os.makedirs(operands["launch_root"], exist_ok=True)
        answer = execution.integrate_next(
            self.coordinator, self.manager, self.jobs, self.authority, model,
            **operands)
        if complete and answer["outcome"] == "integrated":
            execution.complete_integrated(
                self.coordinator, answer["assignment"], answer["settlement"])
        return answer

    def states(self):
        return [(one["entry_id"], one["state"])
                for one in entries_of(self.coordinator, TARGET)]

    def target_state(self):
        """Every path under the disposable target, with its bytes and mode."""
        seen = {}
        for current, _, files in os.walk(self.target):
            for name in files:
                place = os.path.join(current, name)
                with open(place, "rb") as reading:
                    seen[os.path.relpath(place, self.target)] = (
                        reading.read(), stat.S_IMODE(os.stat(place).st_mode))
        return seen


class TheSmallestEligibleEntryIsTheONEThatRuns(ExecutionCase):
    """The acceptance clause: one live lease, the smallest queued rank, and
    independent targets untouched."""

    def test_the_first_integration_takes_rank_one(self):
        answered = self.integrate()
        self.assertEqual(answered["entry"], "entry-1")
        self.assertEqual(answered["outcome"], "integrated")

    def test_the_model_is_asked_for_the_entry_the_grant_named(self):
        model = self.model()
        self.integrate(model)
        self.assertEqual(model.asked, [("attempt-1", "entry-1")])

    def test_a_later_exact_entry_is_a_retryable_no_act_until_it_is_head(self):
        later = self.model()
        first_try = self.integrate(
            later, attempt_id="attempt-2", lease_id="lease-2",
            entry_id="entry-2")
        self.assertIsNone(first_try["outcome"])
        self.assertEqual(later.asked, [])
        self.assertIsNone(lease_of(self.coordinator, "lease-2"))
        self.assertIsNone(self.coordinator._connection.execute(
            "SELECT operation_id FROM operations "
            "WHERE operation_id = 'lease.grant:lease-2'").fetchone())

        self.integrate()
        answered = self.integrate(
            later, attempt_id="attempt-2", lease_id="lease-2",
            entry_id="entry-2")
        self.assertEqual(answered["entry"], "entry-2")
        self.assertEqual(later.asked, [("attempt-2", "entry-2")])

    def test_the_next_integration_takes_the_next_rank(self):
        self.integrate()
        second = self.integrate(attempt_id="attempt-2", lease_id="lease-2")
        self.assertEqual(second["entry"], "entry-2")
        self.assertEqual(self.states(),
                         [("entry-1", "integrated"), ("entry-2", "integrated")])

    def test_an_empty_queue_grants_nothing_and_starts_nothing(self):
        self.integrate()
        self.integrate(attempt_id="attempt-2", lease_id="lease-2")
        model = self.model()
        answered = self.integrate(model, attempt_id="attempt-3",
                                  lease_id="lease-3")
        self.assertEqual(answered["outcome"], None)
        self.assertEqual(model.asked, [])
        self.assertEqual(target_of(self.coordinator, TARGET)["fence"], 2)

    def test_a_second_attempt_cannot_run_while_one_is_live(self):
        """The whole point of the lock: the model is never even asked."""
        self.integrate(self.model(outcome=None, runs_after=None))
        model = self.model()
        answered = self.integrate(model, attempt_id="attempt-2",
                                  lease_id="lease-2")
        self.assertIsNone(answered["outcome"])
        self.assertEqual(model.asked, [])


class OneCleanImportChangesExactlyTheDeclaredPath(ExecutionCase):
    """Review [P1]: the earlier suite marked an entry integrated when no
    candidate byte had moved, because the model wrote only `result.json` and
    `imported_paths` was prose in an untrusted claim."""

    def test_a_clean_import_writes_the_declared_path_and_nothing_else(self):
        before = self.target_state()
        self.assertNotIn(IMPORTED, before)
        self.integrate()
        after = self.target_state()
        self.assertEqual(after[IMPORTED][0], CANDIDATE)
        self.assertEqual(set(after) - set(before), {IMPORTED})
        for name, held in before.items():
            self.assertEqual(after[name], held, name)

    def test_the_verification_is_derived_from_the_bytes_and_mode_imported(self):
        """Second review [P1]: the verification was a constant, so the case
        asserted the target independently and the recorded account said
        nothing. The model now READS BACK what it wrote, and the persisted
        verification is compared with those exact facts.

        The core limitation stands and is deliberate: this is the MODEL'S
        account. Core invents no verification of its own -- see the case
        below."""
        self.integrate()
        settled = json.loads(self.coordinator._connection.execute(
            "SELECT settlement FROM entries WHERE entry_id = 'entry-1'"
        ).fetchone()[0])
        self.assertEqual(settled["imported_paths"], [IMPORTED])
        held = self.target_state()
        for one in settled["imported_paths"]:
            self.assertEqual(held[one][0], CANDIDATE)
            self.assertEqual(held[one][1], IMPORTED_MODE)
        self.assertEqual(settled["verification"],
                         {"path": IMPORTED, "bytes": len(CANDIDATE),
                          "mode": oct(IMPORTED_MODE)})

    def test_every_imported_path_carries_the_mode_the_importer_set(self):
        """`open(..., "wb")` takes whatever the umask leaves, so a mode
        assertion has to be about one somebody established."""
        held = os.umask(0o077)
        self.addCleanup(os.umask, held)
        self.integrate()
        self.assertEqual(self.target_state()[IMPORTED][1], IMPORTED_MODE)

    def test_an_ordinary_refusal_changes_no_target_byte_or_mode(self):
        before = self.target_state()
        answered = self.integrate(self.model(outcome="refused"))
        self.assertEqual(answered["outcome"], "refused")
        self.assertEqual(self.target_state(), before)

    def test_malformed_output_changes_no_target_byte_or_mode(self):
        """A model that answers with garbage BEFORE touching the target: the
        entry is held and every byte and mode is where it was."""
        before = self.target_state()
        answered = self.integrate(self.model(raw=b"not json at all",
                                             imports=False))
        self.assertEqual(answered["outcome"], "held")
        self.assertEqual(self.target_state(), before)

    def test_a_model_that_wrote_before_answering_badly_still_holds(self):
        """And the other order, which is why a hold keeps the lease: the
        target may now carry base bytes, candidate bytes or a mixture, and
        that is exactly the state nobody may integrate into until an operator
        says so."""
        answered = self.integrate(self.model(raw=b"not json at all",
                                             outcome="integrated"))
        self.assertEqual(answered["outcome"], "held")
        self.assertEqual(self.target_state()[IMPORTED][0], CANDIDATE)
        self.assertEqual(
            self.coordinator._connection.execute(
                "SELECT state FROM leases WHERE lease_id = 'lease-1'"
            ).fetchone()[0], "live")

    def test_a_model_that_claims_an_import_it_did_not_make_still_settles(self):
        """Recorded rather than asserted away: this seam CANNOT tell. The
        coordinator records the runtime's account of what it imported, and
        proving that account against the target is the verification the model
        performs under its own Work instructions -- which is why the
        settlement's `verification` member is the model's and this module does
        not invent one. A deployment that wants an independent check adds it to
        the profile's instructions, not to core."""
        before = self.target_state()
        answered = self.integrate(self.model(imports=False))
        self.assertEqual(answered["outcome"], "integrated")
        self.assertEqual(self.target_state(), before)


class StaleEvidenceEarnsTheRULEDVerb(ExecutionCase):
    """Review [P0] then [P1]: an entry WAITS, and a stale one is an ordinary
    refusal rather than a wedged queue.

    The targeted review of 2026-09-05 ruled the split years of rounds ago in
    this record's terms: an ordinary policy, scope or target failure found
    before any mutation terminally refuses THAT entry and the queue moves on,
    while an integrity or ambiguous-custody account is a statement about the
    TARGET. Raising instead left the entry leased behind a live lease.
    """

    def test_an_advanced_canonical_target_refuses_the_entry(self):
        before = self.target_state()
        self.authority.current = "revision-2"
        model = self.model()
        answered = self.integrate(model)
        self.assertEqual(answered["outcome"], "refused")
        self.assertEqual(model.asked, [])
        self.assertEqual(self.target_state(), before)

    def test_the_refused_entry_frees_the_target_for_the_next_rank(self):
        """The whole point of the ordinary disposition: rank two proceeds."""
        self.authority.current = "revision-2"
        self.integrate()
        self.assertEqual(self.states()[0], ("entry-1", "refused"))
        self.assertEqual(target_of(self.coordinator, TARGET)["state"], "open")
        self.assertEqual(
            self.coordinator._connection.execute(
                "SELECT state FROM leases WHERE lease_id = 'lease-1'"
            ).fetchone()[0], "released")
        # And the queue moves on, with the producers agreeing again.
        #
        # THE NEVER-STARTED ATTEMPT IS STILL RECONCILED, which is a real
        # operational consequence rather than a fixture detail: the next
        # grant's predecessor is this refused one, and `target_access` proves a
        # predecessor STOPPED. An attempt whose port was never asked has no
        # runtime, and saying so is the manager's own `not-started -> destroyed`
        # transition -- the deployment's reconciliation, not this assembly's.
        self.started("attempt-1", "destroyed")
        self.authority.current = "revision-1"
        second = self.integrate(attempt_id="attempt-2", lease_id="lease-2")
        self.assertEqual(second["entry"], "entry-2")
        self.assertEqual(second["outcome"], "integrated")

    def test_the_refusal_records_what_the_producers_said(self):
        self.authority.current = "revision-2"
        self.integrate()
        settled = json.loads(self.coordinator._connection.execute(
            "SELECT settlement FROM entries WHERE entry_id = 'entry-1'"
        ).fetchone()[0])
        self.assertIn("expected target revision",
                      settled["detail"]["observed"])
        self.assertEqual(settled["detail"]["category"], "refused")

    def test_a_member_the_producers_still_agree_on_is_compared_here(self):
        """The half `resolved_account` cannot catch: every producer agrees
        with every other, and the account they now describe is not the one the
        entry was admitted with. The Job's own test scope is a member no
        cross-binding touches."""
        self.job["test_scope"] = json.dumps(["v12/python/tests/somewhere-else"])
        model = self.model()
        answered = self.integrate(model)
        self.assertEqual(answered["outcome"], "refused")
        self.assertEqual(model.asked, [])
        settled = json.loads(self.coordinator._connection.execute(
            "SELECT settlement FROM entries WHERE entry_id = 'entry-1'"
        ).fetchone()[0])
        self.assertIn("scope_digest", settled["detail"]["observed"])

    def test_an_integrity_account_blocks_the_target_instead(self):
        """The other branch of the ruled split, driven: persisted evidence
        this build cannot own is a statement about the target."""
        self.authority.proposals["proposal-1"] = "not a document"
        model = self.model()
        answered = self.integrate(model)
        self.assertEqual(answered["outcome"], "held")
        self.assertEqual(model.asked, [])
        found = target_of(self.coordinator, TARGET)
        self.assertEqual(found["state"], "blocked")
        self.assertEqual(self.states()[0], ("entry-1", "held"))

    def test_the_selectors_come_from_the_entry_and_not_a_caller(self):
        import inspect
        taken = inspect.signature(execution.integrate_next).parameters
        self.assertNotIn("line_id", taken)
        self.assertNotIn("proposal_id", taken)

    def test_a_sound_entry_re_resolves_and_runs(self):
        """The matrix above would pass if everything refused."""
        self.assertEqual(self.integrate()["outcome"], "integrated")


class TheGrantIsProvedAgainRIGHTBeforeTheModelWrites(ExecutionCase):
    """Review [P0]: producer revalidation is a cross-store proof and a grant
    can end inside it.

    The reviewer ended and abandoned the grant from the Authority callback and
    watched the port write anyway; the completion cutpoint then refused, after
    the target had moved. Two cutpoints answer two races and neither replaces
    the other.
    """

    def ending(self):
        """End the grant from INSIDE producer revalidation, exactly as the
        reproduction does."""
        from baton_v12.integration import abandon_lease, block_target
        held = {"done": False}

        def reading():
            if not held["done"]:
                held["done"] = True
                block_target(self.coordinator, canonical_target_id=TARGET,
                             entry_id="entry-1", lease_id="lease-1", fence=1,
                             reason="integrity",
                             detail={"observed": "an operator"})
                abandon_lease(self.coordinator, lease_id="lease-1", fence=1,
                              recovery={"attempt_id": "attempt-1",
                                        "evidence": "the operator ended it"})
            return "revision-1"

        self.authority.canonical_target = reading

    def test_a_grant_that_ended_during_revalidation_never_reaches_the_port(self):
        before = self.target_state()
        self.ending()
        model = self.model()
        caught = self.refusal(self.integrate, model)
        self.assertEqual(caught.code, "denied")
        self.assertIn("a grant is proved live at the moment it is used",
                      caught.message)
        self.assertEqual(model.asked, [])
        self.assertEqual(self.target_state(), before)

    def test_the_delivery_exists_but_nothing_was_asked_to_use_it(self):
        """The namespaces are made before the runtime starts, so they exist --
        and the cutpoint is what stops anything being told to write."""
        self.ending()
        self.refusal(self.integrate, self.model())
        self.assertTrue(os.path.isdir(os.path.join(
            self.launch, "attempt-1", runtime.DELIVERY_DIRECTORY)))

    def test_the_post_run_cutpoint_still_answers_its_own_race(self):
        """A grant that ends WHILE the model runs is the other race, and the
        second cutpoint is what catches it."""
        from baton_v12.integration import abandon_lease, block_target

        def ended(attempt_id):
            self.stopped(attempt_id)
            block_target(self.coordinator, canonical_target_id=TARGET,
                         entry_id="entry-1", lease_id="lease-1", fence=1,
                         reason="integrity", detail={"observed": "an operator"})
            abandon_lease(self.coordinator, lease_id="lease-1", fence=1,
                          recovery={"attempt_id": attempt_id,
                                    "evidence": "the operator ended it"})

        model = self.model(runs_after=ended)
        caught = self.refusal(self.integrate, model)
        self.assertEqual(model.asked, [("attempt-1", "entry-1")])
        self.assertIn("a grant is proved live at the moment it is used",
                      caught.message)


class TheModelSCLAIMEarnsExactlyOneVerb(ExecutionCase):
    """What the runtime boundary deliberately deferred: which coordinator verb
    a claim earns."""

    def test_an_integrated_claim_settles_and_releases(self):
        self.integrate()
        self.assertEqual(self.states()[0], ("entry-1", "integrated"))
        held = self.coordinator._connection.execute(
            "SELECT state, ending FROM leases WHERE lease_id = 'lease-1'"
        ).fetchone()
        self.assertEqual(held["state"], "released")
        self.assertIn("integrated", held["ending"])
        self.assertEqual(target_of(self.coordinator, TARGET)["state"], "open")

    def test_an_integrated_claim_keeps_the_lease_until_completion(self):
        answered = self.integrate(complete=False)
        self.assertEqual(self.states()[0], ("entry-1", "leased"))
        self.assertEqual(lease_of(self.coordinator, "lease-1")["state"],
                         "live")
        execution.complete_integrated(
            self.coordinator, answered["assignment"], answered["settlement"])
        self.assertEqual(self.states()[0], ("entry-1", "integrated"))
        self.assertEqual(lease_of(self.coordinator, "lease-1")["state"],
                         "released")

    def test_a_refused_claim_refuses_the_entry_and_frees_the_target(self):
        answered = self.integrate(self.model(outcome="refused"))
        self.assertEqual(answered["outcome"], "refused")
        self.assertEqual(self.states()[0], ("entry-1", "refused"))
        self.assertEqual(target_of(self.coordinator, TARGET)["state"], "open")
        second = self.integrate(attempt_id="attempt-2", lease_id="lease-2")
        self.assertEqual(second["entry"], "entry-2")

    def test_a_held_claim_blocks_the_target_and_keeps_the_lease(self):
        answered = self.integrate(self.model(outcome="held"))
        self.assertEqual(answered["outcome"], "held")
        found = target_of(self.coordinator, TARGET)
        self.assertEqual(found["state"], "blocked")
        self.assertEqual(found["blocked_reason"], "integrity")
        self.assertEqual(self.states()[0], ("entry-1", "held"))
        self.assertEqual(
            self.coordinator._connection.execute(
                "SELECT state FROM leases WHERE lease_id = 'lease-1'"
            ).fetchone()[0], "live")

    def test_a_blocked_target_offers_nothing_to_the_next_attempt(self):
        self.integrate(self.model(outcome="held"))
        caught = self.refusal(self.integrate, attempt_id="attempt-2",
                              lease_id="lease-2")
        self.assertEqual(caught.code, "denied")
        self.assertIn("blocked", caught.message)


class OnlyANOTSTARTEDAttemptIsAskedToRun(ExecutionCase):
    """Review [P0]: refusing only the two terminal states let five others
    through, and none of them says no runtime is writing.

    `start-requested` and `running` have one, `cancel-requested` and `stopping`
    are taking one down, and `uncertain` is the state the manager's own table
    refuses to let become `destroyed` because nobody looked successfully. The
    reviewer reproduced a target mutated while the attempt was `uncertain`.
    """

    def test_every_state_but_not_started_refuses_before_the_port(self):
        for state in attempts.TRANSITIONS["execution_runtime"]:
            if state == execution.UNSTARTED:
                continue
            with self.subTest(execution_runtime=state):
                case = self.__class__(self._testMethodName)
                case.setUp()
                self.addCleanup(case.doCleanups)
                before = case.target_state()
                model = case.model(runs=False, runs_after=None)
                caught = case.refusal(case.integrate, model, state=state)
                self.assertEqual(caught.code, "denied", state)
                self.assertIn("only for an attempt whose runtime is",
                              caught.message)
                self.assertEqual(model.asked, [], state)
                self.assertEqual(case.target_state(), before, state)

    def test_uncertain_is_named_because_it_is_the_tempting_one(self):
        model = self.model(runs=False, runs_after=None)
        caught = self.refusal(self.integrate, model, state="uncertain")
        self.assertIn("'uncertain'", caught.message)
        self.assertEqual(model.asked, [])

    def test_the_delivery_exists_before_the_runtime_starts(self):
        """`materialize_delivery`'s own contract, and what requiring
        `not-started` is what makes realizable."""
        seen = {}
        launch = os.path.join(self.launch, "attempt-1")

        class Watching(Model):
            def _started(self, attempt_id):
                seen["delivery"] = os.path.isdir(
                    os.path.join(launch, runtime.DELIVERY_DIRECTORY))
                seen["assignment"] = os.path.exists(os.path.join(
                    launch, runtime.DELIVERY_DIRECTORY,
                    runtime.ASSIGNMENT_DIRECTORY, runtime.ASSIGNMENT_DOCUMENT))
                super()._started(attempt_id)

        model = Watching(target=self.target, runs_after=self.stopped)
        model.starts = self.started
        self.integrate(model)
        self.assertTrue(seen["delivery"])
        self.assertTrue(seen["assignment"])

    def test_the_port_drives_the_attempt_through_its_legal_lifecycle(self):
        """Recorded `not-started`, started by the port, stopped by the port,
        settled only then."""
        seen = []

        def watching(attempt_id, state):
            seen.append(state)
            self.started(attempt_id, state)

        model = self.model()
        model.starts = watching
        answered = self.integrate(model)
        self.assertEqual(seen, ["start-requested", "running"])
        self.assertEqual(answered["outcome"], "integrated")

    def test_a_settlement_waits_for_the_manager_s_own_observation(self):
        """The model finishes and the manager has NOT seen the runtime stop."""
        caught = self.refusal(self.integrate, self.model(runs_after=None))
        self.assertEqual(caught.code, "denied")
        self.assertIn("has not finished writing it", caught.message)

    def test_the_refused_settlement_moved_nothing_in_the_coordinator(self):
        self.refusal(self.integrate, self.model(runs_after=None))
        self.assertEqual(self.states()[0], ("entry-1", "leased"))
        self.assertEqual(
            self.coordinator._connection.execute(
                "SELECT state FROM leases WHERE lease_id = 'lease-1'"
            ).fetchone()[0], "live")

    def test_the_observation_is_the_one_made_after_the_model_wrote(self):
        seen = []

        def stopping(attempt_id):
            seen.append(runtime.prior_runtime_witness(
                self.manager, attempt_id)["execution_runtime"])
            self.stopped(attempt_id)

        self.integrate(self.model(runs_after=stopping))
        self.assertEqual(seen, ["running"])
        self.assertEqual(self.states()[0], ("entry-1", "integrated"))


class AnUnansweredAttemptIsReportedAndLeftAlone(ExecutionCase):
    """The owner ruling of 2026-09-06: restart may observe and classify. It may
    not retry, accept, complete a receipt, clean up, release or reassign."""

    def silent(self):
        return self.model(outcome=None, runs_after=None)

    def test_a_silent_model_is_running_rather_than_failed(self):
        answered = self.integrate(self.silent())
        self.assertEqual(answered["outcome"], "running")
        self.assertEqual(answered["observed"]["state"], "waiting")

    def test_a_running_attempt_keeps_its_grant_and_its_entry(self):
        self.integrate(self.silent())
        self.assertEqual(self.states()[0], ("entry-1", "leased"))
        self.assertEqual(
            self.coordinator._connection.execute(
                "SELECT state FROM leases WHERE lease_id = 'lease-1'"
            ).fetchone()[0], "live")
        self.assertEqual(target_of(self.coordinator, TARGET)["state"], "open")

    def test_reading_a_running_attempt_again_changes_nothing(self):
        answered = self.integrate(self.silent())
        delivery = runtime.adopt_delivery(
            os.path.join(self.launch, "attempt-1"), attempt_id="attempt-1",
            workspace_group=self.group)
        again = execution.settle_observed(self.coordinator, self.manager,
                                          delivery, answered["assignment"])
        self.assertEqual(again["outcome"], "running")
        self.assertEqual(self.states()[0], ("entry-1", "leased"))

    def test_a_restart_reads_the_result_without_settling_it(self):
        answered = self.integrate(self.silent())
        delivery = runtime.adopt_delivery(
            os.path.join(self.launch, "attempt-1"), attempt_id="attempt-1",
            workspace_group=self.group)
        # The model finishes after the first sweep looked, and the manager
        # then observes its runtime stop. It is already `running` -- the silent
        # port started it -- so this one only writes and stops.
        self.model(runs=False).run(delivery, answered["assignment"])
        again = execution.settle_observed(self.coordinator, self.manager,
                                          delivery, answered["assignment"])
        self.assertEqual(again["outcome"], "integrated")
        self.assertEqual(self.states()[0], ("entry-1", "leased"))
        self.assertEqual(lease_of(self.coordinator, "lease-1")["state"],
                         "live")
        self.assertEqual(self.target_state()[IMPORTED][0], CANDIDATE)


class AGrantThatEndedWhileTheModelRanCannotSettle(ExecutionCase):
    """The ruling's second cutpoint, driven: the live grant is re-read AFTER
    the model finished rather than before it started."""

    def ended(self, attempt_id):
        """A third party blocks the target and recovers the holder while the
        model is finishing -- the grant this attempt holds is gone."""
        from baton_v12.integration import abandon_lease, block_target
        self.stopped(attempt_id)
        block_target(self.coordinator, canonical_target_id=TARGET,
                     entry_id="entry-1", lease_id="lease-1", fence=1,
                     reason="integrity", detail={"observed": "an operator"})
        abandon_lease(self.coordinator, lease_id="lease-1", fence=1,
                      recovery={"attempt_id": attempt_id,
                                "evidence": "the operator ended it"})

    def test_a_grant_ended_between_the_run_and_the_settlement_refuses(self):
        caught = self.refusal(self.integrate,
                              self.model(runs_after=self.ended))
        self.assertEqual(caught.code, "denied")
        self.assertIn("a grant is proved live at the moment it is used",
                      caught.message)

    def test_the_entry_keeps_the_state_the_third_party_left_it_in(self):
        self.refusal(self.integrate, self.model(runs_after=self.ended))
        self.assertEqual(self.states()[0], ("entry-1", "held"))
        self.assertEqual(target_of(self.coordinator, TARGET)["state"],
                         "blocked")


class UnreadableOrForeignMaterialHoldsTheTarget(ExecutionCase):
    """The least trusted program in the deployment must not be able to raise
    out of a sweep, and must not leave a target that looks free."""

    def test_material_that_does_not_decode_holds_the_target(self):
        answered = self.integrate(self.model(raw=b"not json at all"))
        self.assertEqual(answered["outcome"], "held")
        self.assertEqual(target_of(self.coordinator, TARGET)["blocked_reason"],
                         "result-unreadable")

    def test_a_result_answering_another_integration_holds_the_target(self):
        class Elsewhere(Model):
            def run(self, delivery, assignment):
                super().run(delivery,
                            dict(assignment, fence=assignment["fence"] + 1))

        answered = self.integrate(
            Elsewhere(target=self.target, runs_after=self.stopped))
        self.assertEqual(answered["outcome"], "held")
        self.assertEqual(target_of(self.coordinator, TARGET)["blocked_reason"],
                         "result-foreign")

    def test_a_settlement_the_coordinator_cannot_record_holds_the_target(self):
        answered = self.integrate(self.model(
            outcome="integrated", detail={"imported_paths": [IMPORTED]}))
        self.assertEqual(answered["outcome"], "held")
        self.assertEqual(target_of(self.coordinator, TARGET)["blocked_reason"],
                         "result-foreign")
        self.assertEqual(self.states()[0], ("entry-1", "held"))

    def test_a_refused_settlement_of_the_wrong_shape_holds_too(self):
        answered = self.integrate(self.model(
            outcome="refused", detail={"imported_paths": []}))
        self.assertEqual(answered["outcome"], "held")
        self.assertEqual(target_of(self.coordinator, TARGET)["blocked_reason"],
                         "result-foreign")

    def test_the_settlement_shape_is_the_coordinator_s_own_rule(self):
        from baton_v12.integration import queue
        self.assertIs(execution._settlement, queue._settlement)


class TheAuthorizedResultIsImportedAndSettled(ResultCase):
    """W133120, the transition W131409 has been missing.

    THE WHOLE POINT OF THE CAMPAIGN, end to end on real things. Job A
    integrated and moved both the dedicated reference and the Authority's
    canonical cursor; Job B's accepted submission is behind it and cannot be
    imported directly. W133117 reconciled B into its own reviewed, observed and
    independently approved candidate. This puts that candidate ON THE TARGET
    through the ordinary coordinator -- its own queue rank, one burned fence,
    the live grant re-read before the write, a compare-and-swap advance, the
    post-import readback, the Authority's own integration receipt, terminal
    custody and the released capacity.

    The fixture is P's, reused rather than duplicated: a real Git target, a
    real producer line, a real Authority with real sessions and receipts, and a
    real `IntegrationStore`.
    """

    def setUp(self):
        super().setUp()
        self.verifier = PostImportVerifier(self)

    def tick(self, held, *, verifier=None, **over):
        operands = {"result_id": held["result_id"],
                    "attempt_id": "attempt-import"}
        operands.update(over)
        return driver.admit_authorized_result(
            self.store, self.profile, runner, self.manager, self.jobs,
            self.authority, self.session, verifier or self.verifier,
            **operands)

    def test_both_jobs_changes_land_on_the_target_and_it_settles(self):
        held = self.through_authorization()
        before = self.git(self.target, "rev-parse", REFERENCE)
        self.assertEqual(before, self.advanced)
        answer = self.tick(held)
        self.assertEqual(answer["outcome"], "integrated")

        # 1. THE PHYSICAL BYTES. The dedicated reference now holds the
        #    reconciled commit, and BOTH Jobs' changes are in its tree.
        after = self.git(self.target, "rev-parse", REFERENCE)
        self.assertEqual(after, held["prepared"]["head"])
        self.assertNotEqual(after, before)
        content = self.materialize(self.target, after)
        with open(os.path.join(content, "feature.py")) as handle:
            self.assertEqual(handle.read(), FIXED)
        with open(os.path.join(content, "other.py")) as handle:
            self.assertIn("the first job answered", handle.read())

        # 2. THE COORDINATOR. The entry is integrated, its settlement names the
        #    imported paths and the readback, and the lease is released.
        entry = [one for one in entries_of(self.store, TARGET)
                 if one["entry_id"] == answer["entry"]][0]
        self.assertEqual(entry["state"], "integrated")
        self.assertEqual(sorted(entry["settlement"]["imported_paths"]),
                         ["feature.py", "harness.py", "other.py", "scale.py"])
        self.assertEqual(entry["settlement"]["verification"]["settled"], after)
        self.assertEqual(entry["settlement"]["verification"]["reviewed"],
                         self.advanced)
        leases = self.store._connection.execute(
            "SELECT lease_id, state FROM leases").fetchall()
        self.assertEqual([one["state"] for one in leases], ["released"])

        # 3. THE AUTHORITY. Its integration receipt is on the DERIVED proposal
        #    and its canonical cursor is the imported candidate.
        receipt = self.authority.receipt(held["derived_proposal_id"],
                                         "integration")
        self.assertEqual(receipt["actor"], INTEGRATOR)
        self.assertEqual(receipt["disposition"], "integrated")
        self.assertEqual(receipt["candidate_digest"], after)
        self.assertEqual(self.authority.canonical_target(), after)

        # 4. TERMINAL CUSTODY, which is what P could not express.
        self.assertEqual(answer["result"]["state"], "imported")
        self.assertEqual(answer["result"]["entry_id"], answer["entry"])
        self.assertEqual(
            reconciliation.result_of(self.store, held["result_id"])["state"],
            "imported")
        # BOTH IDENTITIES SURVIVE: the producer's untouched submission and the
        # result's own derived candidate.
        self.assertEqual(answer["result"]["source_proposal_id"], "proposal-b1")
        self.assertEqual(self.authority.proposal("proposal-b1")["result_id"],
                         "result-b1")
        self.assertEqual(self.git(self.line, "rev-parse", "HEAD"),
                         self.candidate)

    def test_the_tick_replays_after_the_import_completed(self):
        """The target and the Authority cursor have both moved, so nothing can
        re-resolve the account -- and the settled entry is what a replay reads
        instead, exactly as the direct path does."""
        held = self.through_authorization()
        first = self.tick(held)
        again = self.tick(held)
        self.assertEqual(again["outcome"], "integrated")
        self.assertEqual(again["entry"], first["entry"])
        self.assertEqual(again["result"]["state"], "imported")
        self.assertEqual(self.git(self.target, "rev-parse", REFERENCE),
                         held["prepared"]["head"])

    def test_a_target_that_moved_AGAIN_takes_no_rank_and_no_byte(self):
        """A third Job advanced the dedicated reference before this tick. The
        account refuses at composition, so the result never reaches the queue
        -- the same place the direct path refuses a candidate whose evidence
        moved before it was ever admitted."""
        held = self.through_authorization()
        moved = self.advance("other.py", "MESSAGE = 'a third job'\n")
        with self.assertRaises(ContractRefusal) as caught:
            self.tick(held)
        self.assertIn("reconciled again rather than imported",
                      caught.exception.message)
        self.assertEqual(caught.exception.category, "stale-assignment")
        self.assertEqual(self.git(self.target, "rev-parse", REFERENCE), moved)
        self.assertEqual(self.store._connection.execute(
            "SELECT COUNT(*) FROM entries").fetchone()[0], 0)
        self.assertEqual(
            reconciliation.result_of(self.store, held["result_id"])["state"],
            "authorized")
        self.assertIsNone(self.authority.receipt(held["derived_proposal_id"],
                                                 "integration"))

    def test_a_target_that_moves_UNDER_THE_GRANT_refuses_the_entry(self):
        """THE RACE THE PRE-WRITE PROOF EXISTS FOR. The entry took its rank
        while the target was current and a third Job advanced the reference
        before the import ran. It is an ordinary refusal: the entry is settled
        `refused`, the lease is released so the queue moves on, and not one
        byte of the target was written."""
        held = self.through_authorization()
        _account, eligibility = driver.authorized_result_eligibility(
            self.store, self.profile, self.manager, self.jobs, self.authority,
            result_id=held["result_id"])
        entry_id = driver._identity(
            "entry", {"canonical_target_id": TARGET,
                      "eligibility": eligibility})
        enqueue(self.store, canonical_target_id=TARGET, entry_id=entry_id,
                eligibility=eligibility)
        moved = self.advance("other.py", "MESSAGE = 'a third job'\n")
        answer = execution.import_authorized_result(
            self.store, self.profile, runner, self.manager, self.jobs,
            self.authority, self.verifier,
            canonical_target_id=TARGET, entry_id=entry_id,
            lease_id="lease-" + entry_id, integrator_participant=INTEGRATOR,
            attempt_id="attempt-import", result_id=held["result_id"])
        self.assertEqual(answer["outcome"], "refused")
        self.assertEqual(self.git(self.target, "rev-parse", REFERENCE), moved)
        entry = [one for one in entries_of(self.store, TARGET)
                 if one["entry_id"] == entry_id][0]
        self.assertEqual(entry["state"], "refused")
        self.assertEqual([one["state"] for one in
                          self.store._connection.execute(
                              "SELECT state FROM leases").fetchall()],
                         ["released"])
        self.assertEqual(target_of(self.store, TARGET)["state"], "open")
        self.assertEqual(
            reconciliation.result_of(self.store, held["result_id"])["state"],
            "authorized")

    def test_an_unapproved_result_imports_nothing(self):
        """PUBLICATION IS NOT AUTHORIZATION, and this is where that matters
        most: the candidate is real, the Authority holds its proposal, and no
        byte of the target moves."""
        published = self.through_publication()
        before = self.git(self.target, "rev-parse", REFERENCE)
        with self.assertRaises(ContractRefusal) as caught:
            self.tick(published)
        self.assertIn("its owners have not accepted yet",
                      caught.exception.message)
        self.assertEqual(self.git(self.target, "rev-parse", REFERENCE), before)
        self.assertEqual(self.store._connection.execute(
            "SELECT COUNT(*) FROM entries").fetchone()[0], 0)
        self.assertIsNone(self.authority.receipt(
            published["derived_proposal_id"], "integration"))

    def test_a_blocked_combination_never_reaches_the_target(self):
        """The combined run FAILED, so there is no candidate at all."""
        self.advance("scale.py", "SCALE = 2\n")
        blocked = self.observe_result(self.prepare())
        self.assertEqual(blocked["state"], "blocked")
        before = self.git(self.target, "rev-parse", REFERENCE)
        with self.assertRaises(ContractRefusal):
            self.tick(blocked)
        self.assertEqual(self.git(self.target, "rev-parse", REFERENCE), before)

    def test_the_required_post_import_tests_ACTUALLY_RUN(self):
        """REVIEW 2026-09-10T14:20:24Z [R1]. The settlement retains an
        EXECUTION -- a command, the imported commit and tree, an exit status
        and real output -- and the owner was asked about the bytes that were
        actually delivered, before the reference named them."""
        held = self.through_authorization()
        answer = self.tick(held)
        self.assertEqual(answer["outcome"], "integrated")
        self.assertEqual(len(self.verifier.asked), 1)
        asked = self.verifier.asked[0]
        self.assertEqual(asked["input_commit"], held["prepared"]["head"])
        self.assertEqual(asked["input_tree"], held["prepared"]["tree"])
        executed = answer["verification"]
        self.assertEqual(executed["status"], 0)
        self.assertEqual(executed["output"], "the regression harness passed")
        self.assertEqual(executed["execution"], "baton.integration-verify")
        self.assertIn("harness.py", executed["command"])
        # It is retained where an operator reads it, beside the readback.
        entry = [one for one in entries_of(self.store, TARGET)
                 if one["entry_id"] == answer["entry"]][0]
        self.assertEqual(entry["settlement"]["verification"]
                         ["post_import_tests"], executed)

    def test_a_FAILED_post_import_test_holds_and_never_advances(self):
        """The deployment's own check really fails on the imported bytes. The
        reference is not advanced, no Authority receipt is written, nothing is
        settled or released, and the target is held with the execution."""
        held = self.through_authorization()
        before = self.git(self.target, "rev-parse", REFERENCE)
        answer = self.tick(held, verifier=PostImportVerifier(
            self, script=DEPLOYMENT_CHECK, identity="deployment/post-import"))
        self.assertEqual(answer["outcome"], "held")
        self.assertEqual(answer["verification"]["status"], 1)
        self.assertIn("wanted 7", answer["verification"]["output"])

        # THE TARGET DID NOT MOVE and nobody claimed it did.
        self.assertEqual(self.git(self.target, "rev-parse", REFERENCE), before)
        self.assertIsNone(self.authority.receipt(held["derived_proposal_id"],
                                                 "integration"))
        self.assertEqual(
            reconciliation.result_of(self.store, held["result_id"])["state"],
            "authorized")
        # THE CONSERVATIVE HOLD: the target is blocked with the failure and the
        # lease is kept for the explicit recovery.
        target_row = target_of(self.store, TARGET)
        self.assertEqual(target_row["state"], "blocked")
        self.assertEqual(target_row["blocked_reason"],
                         "post-import-tests-failed")
        self.assertEqual(
            target_row["blocked_account"]["detail"]["verification"]["status"],
            1)
        self.assertEqual([one["state"] for one in
                          self.store._connection.execute(
                              "SELECT state FROM leases").fetchall()],
                         ["live"])

    def test_a_GRANT_FOR_ANOTHER_PROPOSAL_writes_nothing(self):
        """REVIEW [R2], the reviewer's own probe. An entry admitted for the
        PRODUCER's proposal is offered as this result's, and the importer is
        asked to import the derived result under that entry's lease. It refuses
        before any fence, object or reference write."""
        held = self.through_authorization()
        before = self.git(self.target, "rev-parse", REFERENCE)
        _account, eligibility = execution.authorized_result_eligibility(
            self.store, self.profile, self.manager, self.jobs, self.authority,
            result_id=held["result_id"])
        # The SAME account, except that it names the producer's own proposal --
        # which is exactly what the reviewer's probe supplied at the queue.
        foreign = dict(eligibility, proposal_id="proposal-b1")
        entry_id = driver._identity(
            "entry", {"canonical_target_id": TARGET, "eligibility": foreign})
        enqueue(self.store, canonical_target_id=TARGET, entry_id=entry_id,
                eligibility=foreign)
        with self.assertRaises(ContractRefusal) as caught:
            execution.import_authorized_result(
                self.store, self.profile, runner, self.manager, self.jobs,
                self.authority, self.verifier, canonical_target_id=TARGET,
                entry_id=entry_id, lease_id="lease-" + entry_id,
                integrator_participant=INTEGRATOR,
                attempt_id="attempt-import", result_id=held["result_id"])
        self.assertIn("authorizes no byte of this one",
                      caught.exception.message)
        # NOTHING WAS BURNED AND NOTHING WAS WRITTEN.
        self.assertEqual(self.git(self.target, "rev-parse", REFERENCE), before)
        self.assertEqual(self.store._connection.execute(
            "SELECT COUNT(*) FROM leases").fetchone()[0], 0)
        self.assertEqual(target_of(self.store, TARGET)["fence"], 0)
        self.assertEqual([one["state"] for one in
                          entries_of(self.store, TARGET)], ["queued"])
        self.assertEqual(self.verifier.asked, [])

    def test_a_reconciled_entry_is_never_handed_to_a_runtime(self):
        """Its bytes were composed, observed and approved already; there is
        nothing for a model to compose. The wiring refusal is an INTEGRITY
        statement about the target rather than a verdict on the candidate."""
        held = self.through_authorization()
        _account, eligibility = driver.authorized_result_eligibility(
            self.store, self.profile, self.manager, self.jobs, self.authority,
            result_id=held["result_id"])
        entry_id = driver._identity(
            "entry", {"canonical_target_id": TARGET,
                      "eligibility": eligibility})
        enqueue(self.store, canonical_target_id=TARGET, entry_id=entry_id,
                eligibility=eligibility)
        entry = [one for one in entries_of(self.store, TARGET)
                 if one["entry_id"] == entry_id][0]
        self.assertEqual(execution.reconciled_result(self.store, entry),
                         held["result_id"])
        account, refused = execution._current(
            self.store, self.manager, self.jobs, self.authority, entry)
        self.assertIsNone(account)
        self.assertEqual(refused.category, "integrity")
        self.assertIn("imported by its own owner", refused.message)


class ThePortIsInjectedAndTyped(ExecutionCase):

    def test_a_port_without_its_one_verb_is_refused(self):
        self.assertEqual(
            self.refusal(self.integrate, object()).category, "integrity")

    def test_the_port_is_asked_after_the_assignment_is_published(self):
        seen = {}

        class Watching(Model):
            def run(self, delivery, assignment):
                place = os.path.join(delivery.assignment_root,
                                     runtime.ASSIGNMENT_DOCUMENT)
                seen["published"] = os.path.exists(place)
                super().run(delivery, assignment)

        self.integrate(Watching(target=self.target, runs_after=self.stopped))
        self.assertTrue(seen["published"])

    def test_this_module_runs_no_version_control_system(self):
        from .test_runtime import called_names, imported_names
        for forbidden in ("source_profiles", "checkpoint_profiles",
                          "subprocess"):
            self.assertNotIn(forbidden, imported_names(execution), forbidden)
        self.assertNotIn("run_git", called_names(execution))
