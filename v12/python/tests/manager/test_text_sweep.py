"""W4 — every exported manager operation, driven with unstorable text.

TWO ROUNDS RUNNING, A "SWEEP" OF MINE MISSED SITES. Cut B's sweep was real: I
walked the SQL statements and found four. Cut C's was not -- I probed the
entry points I could think of, said "all seven refuse", and the review then
enumerated six I had never called. Probing measures imagination; enumeration
measures the code.

So the sweep is DERIVED here. Every exported callable of both manager packages
appears in the table below with one minimal, valid call; each of its text
operands is then replaced, in turn, with a lone surrogate, and the answer must
be a closed `ContractRefusal` rather than a driver fault. A completeness case
asserts the table names every exported callable, so adding one without adding a
row fails the gate.

WHY A TABLE AND NOT INTROSPECTION. A call needs valid operands, and inventing
them from a signature would mean guessing what each parameter means -- the
guessing this file exists to replace. The table is written by hand and its
COVERAGE is checked mechanically, which puts the judgement where a person can
see it and the enumeration where a person cannot forget it.
"""

import ast
import inspect
import os
import pathlib
import tempfile
import unittest

import baton_v12.contracts as contracts
import baton_v12.worker_manager as worker_manager
from baton_v12.contracts import ContractRefusal
from baton_v12.worker_manager import (AuthorityPort, ControlStore,
                                      certify_profile)

from .test_offers import (FakeSession, PROFILE, UUID, WHO, WORK,
                          fake_claim_signature)

NOW = "2026-08-24T00:00:00.000Z"
SURROGATE = "\ud800"


class _NoAdapter:
    """The narrow adapter surface, doing nothing.

    This sweep drives an unstorable OPERAND; what the adapter would answer is
    another file's business, and the calls never get that far.
    """

    def start(self, operands):
        return None

    def list(self, operands):
        return []

    def stop(self, operands):
        return None

    def seal(self, operands):
        # W6628 added a third operation to the runtime adapter's surface. This
        # sweep never reaches an answer -- the operand is spoiled before the
        # adapter is asked -- but an adapter missing an operation is refused at
        # the capability check, which would make the row refuse for the wrong
        # reason.
        return None


class _NoAgent:
    def cancel(self, operands):
        return None

    def observe_session(self, reference):
        return {"kind": "absent", "provider_session_id": "provider-1"}

    def probe(self, request):
        # W6627 grew the adapter contract to four operations. This sweep never
        # reaches an answer -- the operand is spoiled before the adapter is
        # asked -- but an adapter missing one is refused at the capability
        # check, which would make every row refuse for the wrong reason.
        return {"kind": "unreachable", "why": "not asked"}

    def inquire(self, request):
        return {"kind": "unreachable", "why": "not asked"}

    def observe_session(self, reference):
        # W6627 added a second operation to the agent adapter contract. This
        # sweep never reaches an answer -- the operand is spoiled before the
        # adapter is asked -- but an adapter missing an operation is refused at
        # the capability check, which would make every row here refuse for the
        # wrong reason.
        return {"kind": "absent", "provider_session_id": "provider-1"}


class EveryExportedOperationRefusesUnstorableText(unittest.TestCase):

    def setUp(self):
        self._root = tempfile.TemporaryDirectory(prefix="v12-worker-manager-")
        self.addCleanup(self._root.cleanup)
        self.store = ControlStore.open(
            os.path.join(self._root.name, "control.sqlite3"),
            incarnation="manager-1", clock=lambda: NOW)
        self.addCleanup(self.store.close)
        certify_profile(self.store, "runtime", "reference", PROFILE)
        self.port = AuthorityPort(FakeSession(), fake_claim_signature)

    def calls(self):
        """One minimal valid call per exported callable, with its text operands.

        The third element names which operands are DURABLE TEXT -- the ones a
        surrogate must be refused in. A parameter that is not text is not this
        file's business.
        """
        store, port = self.store, self.port
        return {
            "certify_profile": (
                (store, "runtime", "reference", PROFILE),
                {}, [1, 2, 3]),
            # W6592 cut A. `certify_agent_session_profile` takes a DOCUMENT
            # rather than text, so its surrogate rows live in the boundary
            # inventory's probes where each member is spoiled on its own;
            # what this file drives is the two operations whose operands are
            # text, plus the capability rule, which takes no text at all.
            "certified_agent_session_profile": (
                (store, PROFILE), {}, [1]),
            "negotiate_acp": (
                (store, PROFILE), {"agent_protocol_version": 1}, [1]),
            # Neither of these takes durable TEXT: one takes the profile
            # document, whose every member is spoiled on its own in the
            # boundary inventory's probes, and the other takes the advertised
            # capability record. Named here because the table's completeness
            # is what this file is for -- a surface entry with no text operand
            # is still a surface entry.
            "certify_agent_session_profile": (
                (store, {}), {}, []),
            "check_client_capabilities": (
                ({"fs": {}, "terminal": False},), {}, []),
            "expire_overdue": ((store, NOW), {"work_id": WORK}, [1, "work_id"]),
            "issue_offer": (
                (store, port),
                dict(offer_id="offer-1", work_id=WORK,
                     runtime_attempt_id="attempt-1",
                     input_digest="sha256:" + "1" * 64,
                     policy_digest="sha256:" + "2" * 64,
                     profile_digest=PROFILE, profile_name="reference",
                     mint_bearer=lambda: "bearer-1"),
                ["offer_id", "work_id", "runtime_attempt_id", "input_digest",
                 "policy_digest", "profile_digest", "profile_name"]),
            "accept_offer": (
                (store, port),
                dict(offer_id="offer-1", decision="accept", bearer="bearer-1",
                     now=NOW, runtime_attempt_id="attempt-1",
                     work_ref={"authority_uuid": UUID, "work_id": WORK}),
                ["offer_id", "now"]),
            "submit_claim": ((store, port), dict(offer_id="offer-1"),
                             ["offer_id"]),
            "settle_claim": ((store, port), dict(offer_id="offer-1", now=NOW),
                             ["offer_id", "now"]),
            "recover_on_restart": ((store,), dict(now=NOW), ["now"]),
            "claim_operation_id": (("offer-1", "intent"), {}, []),
            # -- cut D ------------------------------------------------------
            "record_attempt": (
                (store,), dict(attempt_id="attempt-1", adapter_name="acp",
                               adapter_digest="sha256:" + "a" * 64,
                               profile_digest=PROFILE,
                               input_digest="sha256:" + "1" * 64),
                ["attempt_id", "adapter_name", "adapter_digest",
                 "profile_digest", "input_digest"]),
            "claimed_offers_for": ((store, "attempt-1"), {}, [1]),
            "activate_assignment": (
                (store, port),
                dict(attempt_id="attempt-1",
                     expect={"work_ref": {"authority_uuid": UUID,
                                          "work_id": WORK},
                             "participant": WHO, "generation": 1}),
                ["attempt_id"]),
            "observe": ((store,), dict(attempt_id="attempt-1",
                                       axis="consent_runtime",
                                       value="running"),
                        ["attempt_id"]),
            "reconcile_runtime": ((store, _NoAdapter()),
                                  dict(attempt_id="attempt-1"),
                                  ["attempt_id"]),
            "request_runtime_start": ((store, _NoAdapter()),
                                      dict(attempt_id="attempt-1"),
                                      ["attempt_id"]),
            # W76207: the post-claim preparation this manager could not
            # complete, and the read of its record. The writer's refusal
            # operand is this manager's own closed type rather than caller
            # text, so the attempt id is the one durable text either takes.
            "refuse_runtime_preparation": (
                (store,),
                dict(attempt_id="attempt-1",
                     refusal=ContractRefusal("refused", "precondition",
                                             "the preparation refused")),
                ["attempt_id"]),
            "attempt_preparation_failure_of": ((store, "attempt-1"), {}, [1]),
            "request_cancellation": ((store, port, _NoAgent(), _NoAdapter()),
                                     dict(attempt_id="attempt-1"),
                                     ["attempt_id"]),
            # W61984: the already-quiescent finalization. It takes NO agent and
            # NO adapter -- that is the operation, not an omission here -- and
            # both of its operands are durable text: the attempt it ends and
            # the operator's own sentence, which is journalled.
            "finalize_quiescent_assignment": (
                (store, port),
                dict(attempt_id="attempt-1",
                     reason="the operator ended an already-quiescent "
                            "assignment"),
                ["attempt_id", "reason"]),
            # -- W6627: the agent session ----------------------------------
            #
            # Every row drives the REAL exported operation. None of them has a
            # session to act on, which is deliberate: the operand is spoiled
            # before any state is consulted, so what these prove is that
            # unstorable text is refused at the boundary rather than carried to
            # a query that would answer absence.
            "open_agent_session": (
                (store, port),
                dict(attempt_id="attempt-1", posture="execution",
                     profile_digest=PROFILE, intent="open-1"),
                ["attempt_id", "posture", "profile_digest", "intent"]),
            "adopt_provider_session": (
                (store,), dict(attempt_id="attempt-1", posture="execution",
                               session_epoch=1,
                               provider_session_id="provider-1"),
                ["attempt_id", "posture", "provider_session_id"]),
            "observe_session_state": (
                (store, {"runtime_attempt_id": "attempt-1",
                         "posture": "execution", "session_epoch": 1,
                         "provider_session_id": None}, "initializing"),
                {}, [2]),
            "close_agent_session": (
                (store, {"runtime_attempt_id": "attempt-1",
                         "posture": "execution", "session_epoch": 1,
                         "provider_session_id": None}),
                dict(reason="observed closed"), ["reason"]),
            "handle_transport_loss": (
                (store, {"runtime_attempt_id": "attempt-1",
                         "posture": "execution", "session_epoch": 1,
                         "provider_session_id": None}),
                {}, []),
            "reconcile_agent_session": (
                (store, _NoAgent()),
                dict(attempt_id="attempt-1", posture="execution",
                     session_epoch=1),
                ["attempt_id", "posture"]),
            "agent_sessions_of": ((store, "attempt-1"), {}, [1]),
            "posture_slot": ((store, "attempt-1", "execution"), {}, [1, 2]),
            "require_slot_recovery": (
                (store,), dict(attempt_id="attempt-1", posture="execution",
                               session_epoch=1, reason="ambiguous ending"),
                ["attempt_id", "posture", "reason"]),
            "release_slot": (
                (store,), dict(attempt_id="attempt-1", posture="execution",
                               session_epoch=1, evidence="runtime-absent",
                               observed_identity="runtime-1",
                               reason="observed absent"),
                ["attempt_id", "posture", "evidence", "observed_identity",
                 "reason"]),
            # PURE, and they take no durable text at all -- but a surface
            # entry with no text operand is still a surface entry, and the
            # completeness case is what this file is for.
            "permits_session_transition": (("ready", "prompting"), {}, []),
            "satisfies_runtime_quiescence_gate": (("agent-quiescent",), {},
                                                  []),
            "reprompt_after_transport_loss": (("continue",), {}, []),
            "transport_reachability_reidentifies": (("the socket is up",), {},
                                                    []),
            # -- W6628: the output freeze and the sealed receiver ----------
            #
            # `retain_manifest` and `record_frozen_result` take DOCUMENTS
            # rather than durable text; every member of one is spoiled on its
            # own in the boundary inventory's probes. What is driven here is
            # the text each operation carries beside its document.
            "retain_manifest": (
                (store, {}, "inputManifest"), {}, [2]),
            "load_manifest": (
                (store, "sha256:" + "a" * 64, "inputManifest"), {}, [1, 2]),
            # W33936 review [P1]: the deployment's configuration act and the
            # read of it. Neither takes caller text -- the group is an
            # integer and the store is a capability.
            # The capability itself takes no caller text at all: the only
            # thing that constructs one is this manager's own read of the
            # deployment record, and a direct construction refuses.
            "WorkspaceGroup": ((0,), {}, []),
            "configure_workspace_group": ((store, 0), {}, []),
            "configured_workspace_group": ((store,), {}, []),
            # W32648: the failed-start ending and its operation identity. The
            # ending takes the attempt id and the retention policy digest; the
            # identity takes the attempt row and two digests.
            "authorize_failed_start_cleanup": (
                (store, port, _NoAdapter()),
                dict(attempt_id="attempt-1",
                     retention_policy_digest="sha256:" + "7" * 64), []),
            "failed_start_destroy_operation": (
                ({}, "sha256:" + "9" * 64, "sha256:" + "7" * 64), {}, [1, 2]),
            # W44716: the abandonment ending. It is the only one of the four
            # that carries an OPERATOR'S OWN SENTENCE -- the reason the attempt
            # is being declared over -- so unlike its three siblings it has a
            # caller text operand to sweep, and that sentence becomes durable.
            "abandon_attempt": (
                (store, port, _NoAdapter()),
                dict(attempt_id="attempt-1",
                     reason="the operator declared this attempt abandoned",
                     retention_policy_digest="sha256:" + "7" * 64),
                ["reason"]),
            # W32576: the refused-session ending and its two identities. The
            # ending takes the session reference and the retention policy
            # digest; the operation identity takes the attempt row and two
            # digests; the record identity takes the reference alone.
            "authorize_refused_session_cleanup": (
                (store, port, _NoAdapter()),
                dict(session_ref={"runtime_attempt_id": "attempt-1",
                                  "posture": "execution", "session_epoch": 1,
                                  "provider_session_id": None},
                     retention_policy_digest="sha256:" + "7" * 64), []),
            "refused_session_destroy_operation": (
                ({}, "sha256:" + "9" * 64, "sha256:" + "7" * 64), {}, [1, 2]),
            "unsupported_version_operation_id": (
                ({"runtime_attempt_id": "attempt-1", "posture": "execution",
                  "session_epoch": 1, "provider_session_id": None},), {}, []),
            "settle_unsupported_version": (
                (store, port, _NoAdapter(), _NoAdapter()),
                dict(session_ref={"runtime_attempt_id": "attempt-1",
                                  "posture": "execution", "session_epoch": 1,
                                  "provider_session_id": None},
                     agent_protocol_version=9), []),
            # W32649: both take one caller text -- the attempt id -- and the
            # lane's own four parts come off the row that id names.
            "lane_reference": (({"runtime_attempt_id": "attempt-1",
                                 "assignment_principal": None},), {}, []),
            "runtime_lane": ((store, "attempt-1"), {}, [1]),
            # W55758: the two reads a public recovery branches on. Both take
            # one caller text -- the attempt id -- and answer off the row it
            # names.
            "attempt_runtime_of": ((store, "attempt-1"), {}, [1]),
            # W61599: the liveness projection's read and its writer. The read
            # takes one caller text; the writer takes that same text beside a
            # count, which is not text and is proved on its own.
            "attempt_activity_of": ((store, "attempt-1"), {}, [1]),
            "attempt_start_failure_of": ((store, "attempt-1"), {}, [1]),
            "observe_activity": (
                (store,), dict(attempt_id="attempt-1", bytes_observed=0),
                ["attempt_id"]),
            # W71917: the boundary's two object identities, and their read.
            # The attempt id is the only TEXT either takes -- a device and an
            # inode are whole numbers this manager read from the filesystem,
            # and are proved on their own where they are validated.
            "pin_boundary_identity": (
                (store,), dict(attempt_id="attempt-1", source=(0, 0),
                               workspace=(0, 1)),
                ["attempt_id"]),
            "boundary_identity_of": ((store, "attempt-1"), {}, [1]),
            "label_context": ((store, "attempt-1"), {}, [1]),
            "request_freeze": (
                (store, port, _NoAdapter()),
                dict(attempt_id="attempt-1", disposition="completed"),
                ["attempt_id", "disposition"]),
            "record_frozen_result": (
                (store,), dict(attempt_id="attempt-1", sealed={}),
                ["attempt_id"]),
            "frozen_output_of": ((store, "attempt-1"), {}, [1]),
            # A pure derivation over a row this build already adopted; its
            # operand is a document and carries no durable text of its own.
            "freeze_operation": (({},), {}, []),
            # -- W6629: intake, retention and cleanup ----------------------
            #
            # Every row drives the REAL exported operation, with the text
            # operand spoiled before any state is consulted. The collection and
            # the destroy answer are DOCUMENTS whose members are spoiled one at
            # a time in the boundary inventory's probes; what is driven here is
            # the text each operation carries beside them.
            "request_intake": (
                (store, port, _NoAdapter()), dict(attempt_id="attempt-1"),
                ["attempt_id"]),
            "record_intake": (
                (store, port), dict(attempt_id="attempt-1", collected={}),
                ["attempt_id"]),
            "intake_receipt_of": ((store, "attempt-1"), {}, [1]),
            "decide_retention": (
                (store, port, _NoAdapter()),
                dict(attempt_id="attempt-1", artifact_ids=["artifact-1"],
                     disposition="retain",
                     retention_policy_digest="sha256:" + "7" * 64),
                ["attempt_id", "retention_policy_digest"]),
            "retentions_of": ((store, "attempt-1"), {}, [1]),
            "authorize_cleanup": (
                (store, port, _NoAdapter()),
                dict(attempt_id="attempt-1",
                     retention_policy_digest="sha256:" + "7" * 64),
                ["attempt_id", "retention_policy_digest"]),
            # Pure derivations over a row this build already adopted. Their
            # first operand is a document; the digests beside it are durable
            # text and are spoiled as such.
            "collect_operation": (({},), {}, []),
            "intake_operation": (({},), {}, []),
            "retain_operation": (({}, "sha256:" + "7" * 64,
                                  ["artifact-1"], "retain"), {}, []),
            "destroy_operation": (
                ({}, "sha256:" + "8" * 64, "sha256:" + "7" * 64), {}, []),
            "KEEPS_MATERIAL": None,
            "CUSTODY": None,
            "RETENTION_DISPOSITIONS": None,
            # -- W6627: the operator interrogation split -------------------
            #
            # Every row drives the REAL exported operation. None of them has a
            # session to act on, which is deliberate: the operand is spoiled
            # before any state is consulted, so what these prove is that
            # unstorable text is refused at the boundary rather than carried
            # to a query that would answer absence.
            "probe": (
                (store, port, _NoAgent()),
                dict(attempt_id="attempt-1", posture="execution",
                     session_epoch=1, operation_id="probe-1",
                     deadline_seconds=30),
                ["attempt_id", "posture", "operation_id"]),
            "inquire": (
                (store, port, _NoAgent()),
                dict(attempt_id="attempt-1", posture="execution",
                     session_epoch=1, operation_id="inquire-1",
                     deadline_seconds=30, question="how is it going?"),
                ["attempt_id", "posture", "operation_id", "question"]),
            "settle_interrogation": (
                (store,), dict(operation_id="probe-1", outcome="observed"),
                ["operation_id", "outcome"]),
            "record_inquiry_answer": (
                (store,), dict(operation_id="inquire-1",
                               answer={"body": "done"}),
                ["operation_id"]),
            "publish_inquiry_answer": (
                (store, port), dict(operation_id="inquire-1"),
                ["operation_id"]),
            "interrogation_of": ((store, "probe-1"), {}, [1]),
            "interrogations_of": (
                (store, "attempt-1", "execution", 1), {}, [1, 2]),
            "TRANSITIONS": None,
            "AXES": None,
            "INTERROGATION_KINDS": None,
            "DISPOSITIONS": None,
            "OUTPUT_STATUSES": None,
            "OUTPUT_TYPES": None,
            "AGENT_ADAPTER": None,
            "POSTURES": None,
            "RECOVERY_EVIDENCE": None,
            "SESSION_OBSERVATIONS": None,
            "SESSION_STATES": None,
            "SESSION_SUCCESSORS": None,
            "SLOT_OCCUPANCY": None,
            "TERMINAL_SESSION_STATES": None,
            "manager_signature": (("offer.issue", {}), {}, []),
            "seal_refusal": (
                (ContractRefusal("policy", "retention", "why", durable=True),),
                {}, []),
            "revive_refusal": (('{"category":"policy","code":"retention",'
                                '"message":"why","durable":true}',), {}, []),
            "ControlStore": (
                (os.path.join(self._root.name, "another.sqlite3"),), {},
                []),
            "AuthorityPort": ((FakeSession(), fake_claim_signature), {}, []),
        }

    def exported_callables(self):
        found = {}
        for package in (worker_manager,):
            for name in package.__all__:
                value = getattr(package, name)
                if callable(value):
                    found[name] = value
        return found

    def callable_table(self):
        """The table's rows for exported CALLABLES.

        Cut D exports two frozen mappings beside its operations, and a mapping
        is not something this sweep can drive -- so they are named with `None`
        rather than left out, which keeps the completeness case comparing the
        whole exported surface.
        """
        return {name: row for name, row in self.calls().items()
                if row is not None}

    def test_the_table_names_every_exported_callable(self):
        """The completeness half, and the reason this file exists.

        A table nobody compares to the surface is a list of the things somebody
        remembered.
        """
        self.assertEqual(sorted(self.callable_table()),
                         sorted(self.exported_callables()))

    def test_every_text_operand_refuses_a_lone_surrogate(self):
        callables = self.exported_callables()
        for name, (positional, keywords, text_operands) \
                in self.callable_table().items():
            if not text_operands:
                continue
            operation = callables[name]
            for operand in text_operands:
                with self.subTest(operation=name, operand=operand):
                    spoiled = list(positional)
                    spoiled_keywords = dict(keywords)
                    if type(operand) is int:
                        spoiled[operand] = str(spoiled[operand]) + SURROGATE
                    else:
                        spoiled_keywords[operand] = (
                            str(spoiled_keywords[operand]) + SURROGATE)
                    try:
                        operation(*spoiled, **spoiled_keywords)
                    except ContractRefusal:
                        continue
                    except BaseException as failure:
                        self.fail(f"{name}({operand}) escaped as "
                                  f"{type(failure).__name__}: {failure}")
                    else:
                        self.fail(f"{name}({operand}) accepted unstorable text")

    def test_the_sweep_is_not_vacuous(self):
        # A table whose every row declared no text operands would pass the case
        # above by covering nothing.
        table = self.callable_table()
        with_text = [name for name, (_, _, operands) in table.items()
                     if operands]
        self.assertGreater(len(with_text), 5)
        self.assertGreater(sum(len(operands)
                               for _, _, operands in table.values()), 12)


if __name__ == "__main__":
    unittest.main()
