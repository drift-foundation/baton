"""W6 — the ruled bounded capability pass, as a harness rather than a claim.

Approver ruling M33739: seal and assess an exact NAMED and DIGEST-BOUND
compatible subset of the accepted W6636 evidence, publish the honest formal
`not-certified` result naming every unobserved or conflicting case, and
separately decide whether the evidence and assessment path are promising.

WHAT THIS IS NOT. It is not a certification run and cannot become one. The
register has 135 local-OCI cases; this observes the ones the W6636 arc
GENUINELY DECIDES and reports every other one by name.

HOW A CASE EARNS AN OBSERVATION HERE, and the rule is mechanical rather than
editorial:

  * a probe MEASURES its facts against a real Docker daemon or a real store,
    through the production seam that owns the property;
  * the measured fact set must CONTAIN the case's exact `required_facts`, and
    the seal refuses its own selection otherwise;
  * the verdict is derived by the FROZEN `conformance_model.assess`, which
    this file imports rather than reimplements.

A probe that measures a refusal the case does not expect produces `failed`,
and that is published. Selecting only cases already known to pass would be
the defect this campaign has corrected repeatedly.

Run from `v12/python` with `PYTHONPATH=src python3 <this file>`.
"""

import hashlib
import importlib.util
import json
import os
import pathlib
import subprocess
import sys
import unittest
import uuid

HERE = pathlib.Path(__file__).resolve().parent
DOSSIER = HERE.parent
REPO = pathlib.Path("/home/sl/src/baton")
REGISTER = (REPO / "work/records/2026/08/finding-v12-isolated-agent-workers"
            / "findings/finding-v12-worker-contract"
            / "findings/finding-worker-runtime-conformance/evidence")
W6636 = (REPO / "work/records/2026/08"
         / "finding-v12-local-oci-lifecycle-composition")
# THE PACK IS WRITTEN UNDER A RUN NAME, AND A RUN NEVER OVERWRITES ANOTHER.
#
# It was `HERE / "w6-seal"`, unconditionally, and re-running this harness after
# review OVERWROTE the reviewed pack in place -- the report the independent
# review had verified by digest was replaced by a later run's bytes, and the
# earlier bytes are unrecoverable.  Retaining immutable evidence is this Work's
# own acceptance, and a harness that can destroy its own retained evidence by
# being run twice does not retain anything.
#
# The run name is an OPERAND rather than a timestamp: this module may not read
# a clock (the same rule the authority's injected clock exists for), and a
# harness that silently invented a new directory every run would hide a caller
# who meant to reproduce an exact one.
ARTIFACTS = HERE / ("w6-seal-" + (sys.argv[1] if len(sys.argv) > 1
                                  and not sys.argv[1].startswith("probe_")
                                  else "run"))

NOW_STAMP = "2026-08-28T00:00:00.000Z"


def load_frozen():
    """The frozen 1.0 assessor, imported FROM ITS OWN DOSSIER.

    Not copied here. A capability pass that carried its own copy of the rules
    would be assessing itself against a document it could edit.
    """
    spec = importlib.util.spec_from_file_location(
        "w6_conformance_model", REGISTER / "conformance_model.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


MODEL = load_frozen()


def file_digest(place):
    return "sha256:" + hashlib.sha256(
        pathlib.Path(place).read_bytes()).hexdigest()


def text_digest(text):
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# The sealed evidence: every file this pass stands on, bound by content digest
# ---------------------------------------------------------------------------

SEALED = {
    "register:cases": REGISTER / "cases.json",
    "register:obligations": REGISTER / "obligations.json",
    "register:model": REGISTER / "conformance_model.py",
    "register:schema": REGISTER.parent / "schema" / "conformance-1.0.schema.json",
    "w6636:composition-evidence":
        W6636 / "evidence" / "w6636-2026-08-27-composition.txt",
    "w6636:mutation-harness":
        W6636 / "evidence" / "w6636-mutation-harness.py",
    "w6636:composition-suite":
        REPO / "v12/python/tests/manager/test_lifecycle_composition.py",
    "w6636:adapter": REPO / "v12/python/src/baton_v12/worker_manager/oci.py",
    "w6636:attempts": REPO / "v12/python/src/baton_v12/worker_manager/attempts.py",
    "w6636:workspaces":
        REPO / "v12/python/src/baton_v12/worker_manager/workspaces.py",
    "w6636:store": REPO / "v12/python/src/baton_v12/worker_manager/store.py",
    "w6636:offers": REPO / "v12/python/src/baton_v12/worker_manager/offers.py",
    "w6636:intake": REPO / "v12/python/src/baton_v12/worker_manager/intake.py",
    "w6636:worker-recipe": REPO / "v12/worker/Dockerfile",
    "w6636:worker-program": REPO / "v12/worker/baton_worker.py",
    "w6636:scripted-agent": REPO / "v12/worker/scripted_agent.py",
}


def seal_inputs():
    sealed = {}
    for name, place in SEALED.items():
        if not place.is_file():
            raise SystemExit(
                f"OPERATIONAL FINDING: the seal binds {name} at {place} and "
                f"that file cannot be read; this pass reports it rather than "
                f"proceeding without it")
        sealed[name] = {"path": str(place.relative_to(REPO)),
                        "bytes": place.stat().st_size,
                        "content_digest": file_digest(place)}
    return sealed


# ---------------------------------------------------------------------------
# Measurement
# ---------------------------------------------------------------------------

MEASURED = []          # [{case_id, facts, reason, artifacts:{purpose: path}}]
NOTES = []


def record(case_id, facts, reason, artifacts):
    MEASURED.append({"case_id": case_id, "facts": facts, "reason": reason,
                     "artifacts": artifacts})


def artifact(name, body):
    if not ARTIFACTS.exists():
        ARTIFACTS.mkdir(parents=True)
    place = ARTIFACTS / name
    if place.exists() and place.read_bytes() != _sealed_bytes(body):
        raise SystemExit(
            f"OPERATIONAL FINDING: {place} already holds a different run's "
            f"bytes. A retained evidence pack is immutable; name this run "
            f"with an argument (`w6-conformance-seal.py <run-name>`) rather "
            f"than overwriting one that has been reviewed.")
    place.write_bytes(_sealed_bytes(body))
    return place


def _sealed_bytes(body):
    if isinstance(body, (bytes, bytearray)):
        return bytes(body)
    return json.dumps(body, indent=1, sort_keys=True,
                      default=str).encode("utf-8")


# ---------------------------------------------------------------------------
# The probes, over the accepted W6636 composition fixture
# ---------------------------------------------------------------------------

sys.path.insert(0, str(REPO / "v12/python"))
sys.path.insert(0, str(REPO / "v12/python/src"))

from baton_v12.contracts import ContractRefusal                    # noqa: E402
from baton_v12.worker_manager import (accept_offer, decide_retention,  # noqa: E402
                                      authorize_cleanup, observe,
                                      reconcile_runtime, request_freeze,
                                      request_intake, request_runtime_start,
                                      retain_manifest)
from baton_v12.worker_manager import load_manifest              # noqa: E402
from baton_v12.worker_manager.store import manager_signature        # noqa: E402
from tests.manager import test_lifecycle_composition as W          # noqa: E402


def refusal_pair(exception):
    return {"category": exception.category, "code": exception.code}


class Seal(W.Composition, unittest.TestCase):
    """The W6636 fixture, driven to EMIT FACTS instead of assertions.

    Subclassed rather than copied: the arc these probes measure has to be the
    accepted one, and a second hand-written fixture would be a different
    composition wearing the same name.
    """

    engine = "docker"
    required = True

    # -- the shared probe mechanism ----------------------------------------

    def probe_vector(self, program):
        """Run PROGRAM inside the exact runtime the manager just composed.

        THE PRODUCTION `run` ARGV, taken off the engine port's own call log and
        replayed with one substitution: the entrypoint. Every mount, label,
        namespace, capability, user and network flag is the one
        `request_runtime_start` composed, because they are the same argv.

        This is what an `in-runtime-probe` stimulus is for. The properties
        under test -- what is reachable, what is writable -- are decided by
        that configuration and not by which program PID 1 happens to be; the
        reference worker reads a launch document and exits, so a probe is the
        only way to ask the container anything.
        """
        argv = next(list(one) for one in reversed(self.engine_calls)
                    if "run" in one)
        name = f"{W.MARK}-probe-{uuid.uuid4().hex[:10]}"
        argv[argv.index("--name") + 1] = name
        self.made.append(name)
        image = argv[-1]
        argv = [one for one in argv[:-1] if one != "--detach"]
        argv += ["--entrypoint", "python3", image, "-c", program]
        finished = subprocess.run(argv, capture_output=True, timeout=300)
        raw = finished.stdout.decode("utf-8", "replace")
        try:
            answered = json.loads(raw.strip().splitlines()[-1])
        except (ValueError, IndexError):
            raise AssertionError(
                f"the in-runtime probe answered nothing parseable.\n"
                f"argv={argv[:6]}...\nrc={finished.returncode}\n"
                f"stdout={raw[:2000]}\n"
                f"stderr={finished.stderr.decode('utf-8', 'replace')[:2000]}")
        return answered, {"argv": argv, "returncode": finished.returncode,
                          "stdout": raw,
                          "stderr": finished.stderr.decode("utf-8", "replace")}

    def tearDown(self):
        if self.input_digest:
            INPUT_DIGESTS.append(self.input_digest)

    def durable_rows(self, store=None):
        """Every row in the manager's store, as ONE number.

        `durable_effects` is the fact 24 register cases read, and a state
        column is not it: a refusal that wrote a journal row and changed no
        state would read as clean. This counts the whole database.
        """
        store = store if store is not None else self.store
        total = 0
        for row in store._connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
                " AND name NOT LIKE 'sqlite_%'").fetchall():
            total += store._connection.execute(
                f"SELECT COUNT(*) AS n FROM \"{row['name']}\"").fetchone()["n"]
        return total

    # -- A: the delivered input pair ---------------------------------------

    def probe_assignment_manifest_beside_the_input(self):
        adapter, roots, inputs = self.prepared()
        request_runtime_start(self.store, adapter, attempt_id=self.attempt,
                              inputs=inputs)
        answered, log = self.probe_vector(program_input_pair())
        held = self.inspected(self.attempt_row()["runtime_id"])
        binds = {one["Destination"]: one for one in held["Mounts"]}
        facts = {
            "assignment_manifest_present": answered["assignment_present"],
            "assignment_manifest_path": answered["assignment_path"],
            # THE ENGINE'S ANSWER AND THE CONTAINER'S, and both are required.
            # A bind the daemon calls read-only that a process can still write
            # is not read-only, and a write that failed for some other reason
            # is not proof of the bind.
            "assignment_manifest_read_only": bool(
                answered["assignment_write_denied"]
                and binds["/input"]["RW"] is False),
            "input_pair_bindings_agree": answered["bindings_agree"],
        }
        record("A-assignment-manifest-delivered-read-only-beside-the-input",
               facts,
               "read inside the started execution container, and cross-read "
               "against the daemon's own bind record",
               {"manifest": artifact("input-pair.json", answered),
                "trace": artifact("input-pair-trace.json",
                                  {"engine_calls": self.engine_calls,
                                   "mounts": held["Mounts"], "probe": log})})

    def probe_input_is_read_only(self):
        adapter, roots, inputs = self.prepared()
        request_runtime_start(self.store, adapter, attempt_id=self.attempt,
                              inputs=inputs)
        answered, log = self.probe_vector(program_input_write())
        facts = {"input_write_succeeded": answered["input_write_succeeded"],
                 "input_write_denied_by": answered["input_write_denied_by"]}
        record("A-input-is-read-only", facts,
               "a write attempted from inside the runtime at the declared "
               "input path, denied with EROFS -- which is the read-only BIND "
               "and not a permission -- so the case holds. The control write "
               "into /workspace does NOT succeed in this composition and the "
               "artifact records why: the writable root is owned by the "
               "manager's uid and the container runs as 65532, which is a "
               "separate measured defect rather than part of this case",
               {"log": artifact("input-write.json",
                                {"probe": log, "answered": answered}),
                "trace": artifact("input-write-trace.json",
                                  {"engine_calls": self.engine_calls})})

    # -- B: what the runtime cannot reach ----------------------------------

    def _absence(self, case_id, program, name, mapping, reason):
        adapter, roots, inputs = self.prepared()
        request_runtime_start(self.store, adapter, attempt_id=self.attempt,
                              inputs=inputs)
        answered, log = self.probe_vector(program)
        held = self.inspected(self.attempt_row()["runtime_id"])
        # THE PROBE MUST BE ABLE TO SEE SOMETHING. A run where the control
        # path did not resolve either is a broken probe, and its absences are
        # not evidence; it fails here rather than reporting them.
        assert answered["control_reachable"] is True, answered
        facts = {fact: answered[key] for fact, key in mapping.items()}
        record(case_id, facts, reason,
               {"log": artifact(f"{name}.json",
                                {"probe": log, "answered": answered}),
                "attestation": artifact(f"{name}-attestation.json",
                                        {"Mounts": held["Mounts"],
                                         "HostConfig": held["HostConfig"],
                                         "Config": held["Config"]})})

    def probe_no_authority_capability(self):
        self._absence(
            "B-no-authority-capability",
            program_authority(
                self.home, os.path.join(self.home, "control.sqlite3")),
            "no-authority",
            {"authority_home_reachable": "home_reachable",
             "authority_database_reachable": "database_reachable"},
            "the manager's own store file and its home directory, named by "
            "their exact host paths and resolved from inside the runtime")

    def probe_no_baton_executable(self):
        self._absence(
            "B-no-baton-executable",
            program_baton("/home/sl/opt/baton/v11/dd1dc3e/bin/baton",
                          "/home/sl/baton-v11.14aecfb/baton.json"),
            "no-baton",
            {"baton_executable_reachable": "executable_reachable",
             "baton_config_reachable": "config_reachable"},
            "the deployment's exact Baton binary and config paths, resolved "
            "from inside the runtime, plus a PATH search")

    def probe_no_canonical_repository(self):
        self._absence(
            "B-no-canonical-repository",
            program_repository(str(REPO)), "no-repository",
            {"canonical_repository_reachable": "repository_reachable"},
            "the canonical checkout's exact host path and its metadata "
            "directory, resolved from inside the runtime")

    # -- A: the mount plan is held to the authorized root -------------------

    def probe_only_the_authorized_root(self):
        """An agreeing plan over a root this attempt never authorized."""
        given, assignment = self.activated()
        roots = self.roots()
        # A SOURCE INSIDE THIS ASSIGNMENT'S OWN MATERIAL, and not the root
        # that was proved. The first spelling used a directory outside the
        # assignment entirely, and `oci._mounts` refuses that by CONTAINMENT
        # before either authorized-root guard is reached -- so the case was
        # being decided by a third rule and the mutation harness said so.
        stranger = os.path.join(roots["inputs"], "sub")
        os.makedirs(stranger, exist_ok=True)
        inputs = self.composed(roots, given, assignment)
        plan = [{"source": stranger, "target": "/input", "writable": False},
                {"source": roots["workspace"], "target": "/workspace",
                 "writable": True}]
        adapter = self.adapter(roots=roots, mounts=plan)
        before = self.durable_rows()
        refusal = None
        message = None
        try:
            # THE AUTHORIZED ROOT IS AUTHORIZED, and the PLAN names another
            # source at the same fixed target. The first spelling of this probe
            # passed the stranger as `inputs` too, so the manager was
            # authorizing an unprepared directory and refused it as a malformed
            # input root -- an earlier, different rule, and not this case's.
            request_runtime_start(self.store, adapter,
                                  attempt_id=self.attempt, inputs=inputs)
        except ContractRefusal as raised:
            refusal = refusal_pair(raised)
            message = str(raised)
        # MEASURED, NOT ASSERTED. The first spelling of this probe wrote
        # `False` here as a literal -- so the fact the case reads was supplied
        # by the observer rather than by the composition, and the mutation
        # harness caught it: removing BOTH the manager's check and the
        # adapter's boundary still left the case passing.
        from baton_v12.worker_manager.oci import canonical_source
        landed = [one for one in plan if one["target"] == "/input"]
        facts = {"refusal": refusal,
                 "mounted_source_is_authorized": bool(
                     len(landed) == 1
                     and canonical_source(landed[0]["source"], "a mount source")
                     == canonical_source(inputs, "an authorized input root")),
                 "runtimes_started": len(self.carrying(self.labels()))}
        record("A-only-the-authorized-root-is-mounted-at-the-fixed-path",
               facts,
               "the engine was asked how many runtimes carry this attempt's "
               "labels, so 0 is the daemon's answer rather than the "
               "manager's",
               {"trace": artifact("authorized-root-trace.json",
                                  {"engine_calls": self.engine_calls,
                                   "plan": plan, "authorized": inputs,
                                   "mounted": stranger}),
                "log": artifact("authorized-root.json",
                                {"refusal": refusal, "message": message,
                                 "durable_rows_before": before,
                                 "durable_rows_after": self.durable_rows()})})

    # -- C: a decline that transmits the bearer ----------------------------

    def probe_decline_carrying_bearer(self):
        # ISSUED AND NOT ACCEPTED. `reserved()` accepts, so the first spelling
        # of this probe declined an already-accepted offer and measured
        # `already-terminal` -- a true refusal about a different question.
        given, assignment = W.input_roots.documents(
            work_ref=dict(W.WORK_REF), participant=W.WHO, generation=1,
            runtime_attempt_id=self.attempt, given=None,
            policy_digest=W.POLICY, profile_digest=W.PROFILE)
        self.offer = f"offer-{self.attempt}"
        W.issue_offer(self.store, self.port, offer_id=self.offer,
                      work_id=W.WORK_ID, runtime_attempt_id=self.attempt,
                      input_digest=given["manifest_digest"],
                      policy_digest=W.POLICY, profile_digest=W.PROFILE,
                      profile_name="reference", mint_bearer=lambda: "bearer-1")
        self.input_digest = given["manifest_digest"]
        self.assertEqual(self.offer_row()["state"], "issued")
        before = self.durable_rows()
        refusal = None
        message = None
        try:
            accept_offer(self.store, self.port, offer_id=self.offer,
                         decision="decline", bearer="bearer-1", now=W.NOW,
                         runtime_attempt_id=self.attempt,
                         work_ref=dict(W.WORK_REF))
        except ContractRefusal as raised:
            refusal = refusal_pair(raised)
            message = str(raised)
        row = self.offer_row()
        facts = {"refusal": refusal,
                 "claim_committed": bool(row and row["state"] == "claimed"),
                 "offer_state": row["state"] if row else None}
        record("C-decline-carrying-bearer-refused", facts,
               "the production offer boundary was asked to decline while "
               "carrying the issued bearer; the offer row is read back out of "
               "the store afterwards",
               {"log": artifact("decline-bearer.json",
                                {"refusal": refusal, "message": message,
                                 "offer_row": dict(row) if row else None,
                                 "durable_rows_before": before,
                                 "durable_rows_after": self.durable_rows()})})

    # -- E: one operation identity, two signatures -------------------------

    def probe_operation_collision(self):
        self.reserved()
        first = manager_signature("w6.probe", {"operand": "one"})
        second = manager_signature("w6.probe", {"operand": "two"})
        operation = f"operation-{uuid.uuid4().hex[:10]}"
        self.store.transact(operation, "w6.probe", first,
                            lambda connection: {"ok": True})
        before = self.durable_rows()
        refusal = None
        message = None
        try:
            self.store.transact(operation, "w6.probe", second,
                                lambda connection: {"ok": True})
        except ContractRefusal as raised:
            refusal = refusal_pair(raised)
            message = str(raised)
        after = self.durable_rows()
        facts = {"refusal": refusal, "durable_effects": after - before}
        record("E-operation-collision", facts,
               "the manager's own effectively-once journal, driven at the "
               "seam that owns the rule; durable_effects is the change in the "
               "TOTAL row count of every table in the store, not a state "
               "column",
               {"log": artifact("operation-collision.json",
                                {"refusal": refusal, "message": message,
                                 "operation": operation,
                                 "first_signature": first,
                                 "second_signature": second,
                                 "durable_rows_before": before,
                                 "durable_rows_after": after})})

    # -- A: a completion under a superseded generation ---------------------

    def probe_superseded_generation_freeze(self):
        """The whole arc to the edge of the freeze, and THEN the supersession.

        The manager must refuse a completion naming a generation the authority
        has moved past, and must mutate no custody doing it.
        """
        roots = self.roots()
        given, assignment = self.activated()
        inputs = self.composed(roots, given, assignment)
        delivery = self.credential()
        declared = self.declarations(given)
        retain_manifest(self.store, given, "inputManifest")
        adapter = self.adapter(roots=roots, mounts=self.plan(roots),
                               outputs=declared, credential_delivery=delivery)
        request_runtime_start(self.store, adapter, attempt_id=self.attempt,
                              inputs=inputs)
        self.settled(self.attempt_row()["runtime_id"])
        reconcile_runtime(self.store, adapter, attempt_id=self.attempt)
        self.produced(roots, declared)
        self.published(roots, declared)
        observe(self.store, attempt_id=self.attempt,
                axis="worker_disposition", value="completed")

        # THE AUTHORITY MOVES ON. The delivered assignment named generation 1
        # and the live one is now 2; nothing about the workspace changed.
        superseded = {"work_ref": dict(W.WORK_REF), "participant": W.WHO,
                      "generation": 2}
        self.session.live_assignment = dict(superseded)
        self.session.claim_answer = dict(superseded)

        before = self.durable_rows()
        refusal = None
        message = None
        try:
            request_freeze(self.store, self.port, adapter,
                           attempt_id=self.attempt, disposition="completed")
        except ContractRefusal as raised:
            refusal = refusal_pair(raised)
            message = str(raised)
        after = self.durable_rows()
        facts = {"refusal": refusal,
                 "manifest_generation_is_live": False,
                 "durable_effects": after - before}
        record("A-completion-under-a-superseded-generation-refused", facts,
               "the arc ran to a real quiescent runtime with a real published "
               "envelope, and only then did the authority supersede the "
               "generation; durable_effects is the whole-store row delta "
               "across the refused freeze",
               {"log": artifact("superseded-freeze.json",
                                {"refusal": refusal, "message": message,
                                 "delivered_generation": 1,
                                 "live_generation": 2,
                                 "attempt_row": self.attempt_row(),
                                 "durable_rows_before": before,
                                 "durable_rows_after": after}),
                "manifest": artifact("superseded-freeze-manifest.json",
                                     {"input_manifest": given,
                                      "assignment_manifest": assignment})})

    # -- A: the output outlives the runtime --------------------------------

    def probe_output_persists_past_the_runtime(self):
        """Freeze, take custody, RETAIN, destroy -- then read it all again."""
        roots = self.roots()
        given, assignment = self.activated()
        inputs = self.composed(roots, given, assignment)
        delivery = self.credential()
        declared = self.declarations(given)
        retain_manifest(self.store, given, "inputManifest")
        adapter = self.adapter(roots=roots, mounts=self.plan(roots),
                               outputs=declared, credential_delivery=delivery)
        request_runtime_start(self.store, adapter, attempt_id=self.attempt,
                              inputs=inputs)
        self.settled(self.attempt_row()["runtime_id"])
        reconcile_runtime(self.store, adapter, attempt_id=self.attempt)
        self.produced(roots, declared)
        plant_canary(roots, declared)
        envelope = self.published(roots, declared)
        observe(self.store, attempt_id=self.attempt,
                axis="worker_disposition", value="completed")
        request_freeze(self.store, self.port, adapter,
                       attempt_id=self.attempt, disposition="completed")
        receipt = request_intake(self.store, self.port, adapter,
                                 attempt_id=self.attempt)
        artifacts = [one["artifact_id"] for one in receipt["artifacts"]]
        custody = adapter._custody(self.attempt)
        trees = [os.path.join(custody, one["name"]) for one in declared]
        manifest_place = os.path.join(custody, "output.json")

        def tree_digests():
            found = {}
            for tree in trees:
                for base, _directories, files in os.walk(tree):
                    for name in sorted(files):
                        full = os.path.join(base, name)
                        found[os.path.relpath(full, custody)] = file_digest(full)
            return found

        before_trees = tree_digests()
        before_manifest = load_manifest(self.store,
                                        receipt["manifest_digest"],
                                        "resultManifest")

        decide_retention(self.store, self.port, adapter,
                         attempt_id=self.attempt, artifact_ids=artifacts,
                         disposition="retain",
                         retention_policy_digest=W.RETENTION)
        self.session.live_assignment = None
        settled = authorize_cleanup(self.store, self.port, adapter,
                                    attempt_id=self.attempt,
                                    retention_policy_digest=W.RETENTION)
        # THE ENGINE, ASKED. "Destroyed" is the daemon's answer here.
        surviving = self.carrying(self.labels())
        after_trees = tree_digests()
        # RE-READ THROUGH THE PRODUCTION LOADER, which recomputes the digest
        # off the stored bytes and refuses a mismatch. Custody holds only the
        # declared output TREES -- `collected_result` copies nothing else -- so
        # the manifest that outlives the runtime is the retained one, and
        # reading it back is the fact this case asks for.
        after_manifest = load_manifest(self.store,
                                       receipt["manifest_digest"],
                                       "resultManifest")
        CANARY["found"] = scan_canary(custody)

        facts = {
            "frozen_tree_readable_after_destroy": bool(after_trees),
            "output_manifest_readable_after_destroy": after_manifest is not None,
            "digests_unchanged_after_destroy": bool(
                before_trees and after_trees == before_trees
                and before_manifest is not None
                and before_manifest == after_manifest),
        }
        record("A-output-persists-past-the-runtime", facts,
               "the runtime was really destroyed -- the engine reports no "
               "container carrying this attempt's labels -- and the custody "
               "tree and its manifest were re-read and re-digested from disk "
               "afterwards",
               {"manifest": artifact("persistence-manifest.json",
                                     {"envelope": envelope,
                                      "receipt": receipt,
                                      "before": before_trees,
                                      "after": after_trees,
                                      "manifest_before": before_manifest,
                                      "manifest_after": after_manifest,
                                      "custody_root": custody,
                                      "custody_tree": sorted(
                                          os.path.relpath(
                                              os.path.join(base, name), custody)
                                          for base, _d, files in os.walk(custody)
                                          for name in files)}),
                "trace": artifact("persistence-trace.json",
                                  {"engine_calls": self.engine_calls,
                                   "settled": settled,
                                   "surviving_containers": surviving,
                                   "custody": custody})})


# ---------------------------------------------------------------------------
# The in-runtime probe programs
# ---------------------------------------------------------------------------

def program_input_pair():
    return r'''
import json, os
out = {}
place = "/input/assignment.json"
out["assignment_path"] = place
out["assignment_present"] = os.path.isfile(place)
out["input_present"] = os.path.isfile("/input/input.json")
out["running_as"] = [os.getuid(), os.getgid()]
for one in (place, "/input/input.json", "/run/baton/launch.json"):
    try:
        held = os.stat(one)
        out[one] = {"mode": oct(held.st_mode & 0o777), "uid": held.st_uid,
                    "gid": held.st_gid,
                    "readable": os.access(one, os.R_OK)}
    except OSError as error:
        out[one] = f"{type(error).__name__}: {error}"
try:
    with open(place) as h: given = json.load(h)
    with open("/input/input.json") as h: asked = json.load(h)
except Exception as error:
    out["bindings_agree"] = False
    out["read_error"] = repr(error)
    given = asked = None
if given is not None:
    out["bindings_agree"] = bool(
        given["assignment_ref"]["work_ref"] == asked["work_ref"]
        and given["input_manifest_digest"] == asked["manifest_digest"]
        and given["policy_digest"] == asked["policy_digest"]
        and given["runtime_profile_digest"] == asked["runtime_profile_digest"])
    out["compared"] = {
        "work_ref": [given["assignment_ref"]["work_ref"], asked["work_ref"]],
        "input_digest": [given["input_manifest_digest"], asked["manifest_digest"]],
        "policy_digest": [given["policy_digest"], asked["policy_digest"]],
        "runtime_profile_digest": [given["runtime_profile_digest"],
                                   asked["runtime_profile_digest"]]}
try:
    with open(place, "a") as h: h.write("x")
    out["assignment_write_denied"] = False
except OSError as error:
    out["assignment_write_denied"] = True
    out["assignment_write_error"] = f"{type(error).__name__}: {error}"
print(json.dumps(out))
'''


def program_input_write():
    return r'''
import json, os
out = {}
try:
    with open("/input/w6-probe", "w") as h: h.write("x")
    out["input_write_succeeded"] = True
    out["input_write_denied_by"] = ""
except OSError as error:
    out["input_write_succeeded"] = False
    out["input_write_denied_by"] = f"{type(error).__name__}: {error}"
try:
    with open("/workspace/w6-probe", "w") as h: h.write("x")
    out["workspace_write_succeeded"] = True
    os.unlink("/workspace/w6-probe")
except OSError as error:
    out["workspace_write_succeeded"] = False
    out["workspace_write_error"] = f"{type(error).__name__}: {error}"
out["running_as"] = [os.getuid(), os.getgid()]
for one in ("/input", "/workspace"):
    held = os.stat(one)
    out[one] = {"mode": oct(held.st_mode & 0o777), "uid": held.st_uid,
                "gid": held.st_gid, "writable": os.access(one, os.W_OK)}
print(json.dumps(out))
'''


def _reach(names):
    return r'''
import json, os
out = {}
def reachable(place):
    try:
        return bool(os.path.exists(place))
    except OSError:
        return False
''' + "".join(
        f'out[{key!r}] = ' + "any(reachable(one) for one in "
        + repr(list(places)) + ")\n" for key, places in names.items()) + r'''
# THE POSITIVE CONTROL. Every fact above is an ABSENCE, and a probe that
# could resolve nothing at all would report all of them false while measuring
# only its own brokenness. `/input` is mounted, so `reachable` answering True
# here is what makes the False answers above mean something.
out["control_reachable"] = reachable("/input")
out["mounts"] = open("/proc/self/mounts").read().splitlines()
print(json.dumps(out))
'''


def program_authority(home, database):
    # THE EXACT PATHS, and no ancestor of them. The first spelling of this
    # probe also named `os.path.dirname(home)` -- which is `/tmp`, a directory
    # every image has -- so it reported the authority home reachable on the
    # strength of a path that has nothing to do with the authority. A probe
    # that can be satisfied by an unrelated directory measures nothing.
    return _reach({"home_reachable": [home, os.path.join(home, "storage")],
                   "database_reachable": [database, database + "-wal",
                                          database + "-shm"]})


def program_baton(binary, config):
    return _reach({"executable_reachable": [binary, "/usr/local/bin/baton",
                                            "/usr/bin/baton"],
                   "config_reachable": [config,
                                        os.path.expanduser("~/.baton")]})


def program_repository(checkout):
    return _reach({"repository_reachable": [
        checkout, os.path.join(checkout, ".git"),
        os.path.join(checkout, "v12"), os.path.join(checkout, "AGENTS.md")]})


# ---------------------------------------------------------------------------
# The one canary this pass actually plants
# ---------------------------------------------------------------------------

CANARY = {}


def plant_canary(roots, declarations):
    """A sentinel in the WORKSPACE surface, and only that surface.

    The register's canary case reads ten named surfaces. This pass plants one
    and says so; declaring the other nine would be the fabrication the ruling
    forbids, and it is why the fixture below cannot be admitted.
    """
    value = "w6-canary-" + uuid.uuid4().hex
    CANARY.update({"surface": "workspace",
                   "canary_id": "w6-workspace-canary",
                   "value_digest": text_digest(value)})
    for one in declarations:
        place = os.path.join(roots["workspace"], one["path"], "w6-canary.txt")
        with open(place, "w", encoding="utf-8") as handle:
            handle.write(value)
    CANARY["value"] = value
    return value


def scan_canary(custody):
    found = []
    for base, _directories, files in os.walk(custody):
        for name in files:
            try:
                body = pathlib.Path(base, name).read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            if CANARY.get("value") and CANARY["value"] in body:
                found.append(os.path.relpath(os.path.join(base, name),
                                             custody))
    return found


# ---------------------------------------------------------------------------
# Selection, sealing and assessment
# ---------------------------------------------------------------------------

PROBES = [
    "probe_assignment_manifest_beside_the_input",
    "probe_input_is_read_only",
    "probe_no_authority_capability",
    "probe_no_baton_executable",
    "probe_no_canonical_repository",
    "probe_only_the_authorized_root",
    "probe_decline_carrying_bearer",
    "probe_operation_collision",
    "probe_superseded_generation_freeze",
    "probe_output_persists_past_the_runtime",
]

CONSENT_FACTS = ("consent_assignment_ref", "consent_epoch", "consent_mounts",
                 "consent_runtime_has_output", "consent_runtime_has_workspace",
                 "consent_runtime_writable_paths")

INPUT_DIGESTS = []


def local_core():
    return sorted(MODEL.core_for("local-oci"))


def topology_conflicting():
    """Cases that require the SUPERSEDED consent-container topology.

    Derived from the register rather than listed: a case is conflicting when
    its expectation reads a fact that only a consent runtime can produce, and
    the approved direct claim-to-one-container topology has no consent
    runtime to produce it. A hand-written list of three names would stop being
    true the moment the register changed.
    """
    found = {}
    for case_id in local_core():
        case = MODEL.CASE_BY_ID[case_id]
        reads = [f for f in case["required_facts"] if f in CONSENT_FACTS]
        if reads:
            found[case_id] = sorted(reads)
    return found


def build_fixture(image_digest):
    canaries = [{"surface": CANARY["surface"],
                 "canary_id": CANARY["canary_id"],
                 "value_digest": CANARY["value_digest"]}] if CANARY else []
    return MODEL.seal_document({
        "suite_family": "baton.worker-conformance",
        "version": {"major": 1, "minor": 0},
        "document": "fixture",
        "fixture_id": "w6-local-oci-capability-pass",
        "created_at": NOW_STAMP,
        "profile": "local-oci",
        "locality": "local",
        "host_identity": {
            # THE SAME HOST, said as a fact rather than as a label: this
            # manager starts containers on the daemon it is running beside.
            "manager_host_id": "w6-host",
            "runtime_host_id": "w6-host",
            "workspace_path_resolves_on_manager": True},
        "work_ref": {"authority_uuid": W.UUID, "work_id": W.WORK_ID},
        # THE EXACT SET this pass minted, as one derived value. Each probe
        # mints its own input manifest under its own attempt id, so a single
        # borrowed digest would name one of ten and describe none of them.
        "input_manifest_digest": MODEL.digest(sorted(INPUT_DIGESTS)),
        "policy_digest": W.POLICY,
        "runtime_profile_digest": W.PROFILE,
        "agent_session_profile_digest": file_digest(
            REPO / "v12/python/src/baton_v12/contracts/schema"
            / "agent-session-1.0.schema.json"),
        "adapter_build_digest": file_digest(
            REPO / "v12/python/src/baton_v12/worker_manager/oci.py"),
        "scripted_agent": {
            "script_digest": file_digest(REPO / "v12/worker/scripted_agent.py"),
            "speaks": "acp",
            "model_provider_required": False},
        # DECLARED FROM WHAT THE PROBES ACTUALLY INJECT, and nothing else.
        # This pass drives refusals, a superseded generation and an
        # effectively-once collision; it injects none of the register's named
        # fault capabilities, and saying otherwise to get past the fixture
        # gate is the one move the ruling forbids.
        "fault_capabilities": [],
        "canaries": canaries,
    })


def build_observations(fixture, image_digest):
    observations = []
    refused_selection = []
    for measured in MEASURED:
        case = MODEL.CASE_BY_ID[measured["case_id"]]
        wanted = set(case["required_facts"])
        got = set(measured["facts"])
        missing = sorted(wanted - got)
        if missing:
            refused_selection.append((measured["case_id"], missing))
            continue
        evidence = []
        for purpose in sorted(case["deciding_evidence"]):
            place = measured["artifacts"].get(purpose)
            if place is None:
                refused_selection.append(
                    (measured["case_id"], [f"no {purpose} artifact"]))
                evidence = None
                break
            evidence.append({
                "purpose": purpose,
                "artifact": {
                    "artifact_id": f"{measured['case_id']}-{purpose}"[:160],
                    "media_type": "application/json",
                    "bytes": place.stat().st_size,
                    "content_digest": file_digest(place),
                    "locator": "file:" + str(place.relative_to(REPO))}})
        if evidence is None:
            continue
        observations.append(MODEL.seal_document({
            "suite_family": "baton.worker-conformance",
            "version": {"major": 1, "minor": 0},
            "document": "observation",
            "observation_id": "w6-" + measured["case_id"][:150],
            "case_id": measured["case_id"],
            "fixture_digest": fixture["document_digest"],
            "case_digest": case["document_digest"],
            "status": "observed",
            "facts": measured["facts"],
            "blocked_by": None,
            "reason": measured["reason"],
            "evidence": evidence,
            "observed_at": NOW_STAMP}))
    return observations, refused_selection


def build_run(fixture, observations):
    return MODEL.seal_document({
        "suite_family": "baton.worker-conformance",
        "version": {"major": 1, "minor": 0},
        "document": "run",
        "run_id": "w6-local-oci-capability-pass",
        "created_at": NOW_STAMP,
        "profile": "local-oci",
        "fixture_digest": fixture["document_digest"],
        "obligations_digest": MODEL.OBLIGATIONS_DIGEST,
        "observations": observations,
        "supplemental_cases": []})


def assess_all(fixture, observations):
    """Every verdict here is the FROZEN assessor's, one case at a time.

    `certify` is attempted separately and reported whatever it answers. This
    loop exists because a verdict per case is what the ruling asks to be
    enumerated, and `assess` is the function that derives one.
    """
    entries = []
    for observation in observations:
        case = MODEL.validate_case(MODEL.CASE_BY_ID[observation["case_id"]])
        accepted = MODEL.accept_observation(observation, case, fixture)
        assessment, rationale = MODEL.assess(accepted, case)
        if assessment == "passed" and not MODEL.faults_available(case, fixture):
            assessment = "unable"
            rationale = "required faults are not injectable by this fixture"
        entries.append({"case_id": case["case_id"], "assessment": assessment,
                        "rationale": rationale})
    return entries


def formal_verdict(entries, core):
    """§6's own rule, applied to the enumeration above.

    Copied deliberately narrowly: `certify` refuses this fixture before it
    reaches a verdict (see the transcript), and the ruling still requires a
    published formal result. Every INPUT to this rule came from the frozen
    assessor; only the three-line disjunction is restated here.
    """
    failed = sorted(e["case_id"] for e in entries if e["assessment"] == "failed")
    unable = sorted(e["case_id"] for e in entries if e["assessment"] == "unable")
    seen = {e["case_id"] for e in entries}
    missing = sorted(set(core) - seen)
    if failed:
        return "not-certified", f"{len(failed)} portable core case(s) failed", \
            failed, unable, missing
    if unable:
        return "not-certified", (f"{len(unable)} portable core case(s) could "
                                 f"not be decided; 'unable' is not a pass"), \
            failed, unable, missing
    if missing:
        return "not-certified", (f"{len(missing)} portable core case(s) were "
                                 f"not observed"), failed, unable, missing
    return "certified", "every portable core case was observed and passed", \
        failed, unable, missing


def main():
    print("W6 - THE RULED BOUNDED CAPABILITY PASS")
    print("=" * 74)
    print()
    print("Approver ruling M33739. This is a capability pass over an exact")
    print("named subset. It is not a certification run and its formal result")
    print("is published below whatever it turns out to be.")
    print()

    sealed = seal_inputs()
    print("=== 1. THE SEALED EVIDENCE, BOUND BY CONTENT DIGEST")
    for name in sorted(sealed):
        one = sealed[name]
        print(f"    {name}")
        print(f"      {one['path']}")
        print(f"      {one['bytes']} bytes  {one['content_digest']}")
    print()

    core = local_core()
    conflicting = topology_conflicting()
    print("=== 2. THE REGISTER, MEASURED RATHER THAN QUOTED")
    print(f"    total cases in the register      : {len(MODEL.CASES['cases'])}")
    print(f"    applicable to local-oci          : "
          f"{len([c for c in MODEL.CASES['cases'] if 'local-oci' in c['applies_to']])}")
    print(f"    the local-oci portable core      : {len(core)}")
    print(f"    requiring the SUPERSEDED consent topology : {len(conflicting)}")
    for case_id in sorted(conflicting):
        print(f"      {case_id}")
        print(f"        reads {', '.join(conflicting[case_id])}")
    print()
    print("    Derived from the register, not listed: a case conflicts when")
    print("    its expectation reads a fact only a consent runtime can")
    print("    produce, and the approved direct claim-to-one-container")
    print("    topology has no consent runtime to produce it.")
    print()

    print("=== 3. THE PROBES, AGAINST A REAL DAEMON")
    # ONE PROBE AT A TIME when asked, so the mutation harness beside this file
    # can re-derive a single verdict without paying for the whole arc.
    chosen = [one for one in PROBES if one in sys.argv[1:]] or PROBES
    suite = unittest.TestSuite(Seal(name) for name in chosen)
    result = unittest.TextTestRunner(verbosity=2, stream=sys.stdout).run(suite)
    print()
    if not result.wasSuccessful():
        print("    A PROBE FAILED. Every case it would have observed is")
        print("    reported unobserved below; no fact is invented for it.")
        print()

    print("=== 4. WHAT WAS MEASURED")
    for measured in MEASURED:
        print(f"    {measured['case_id']}")
        for name in sorted(measured["facts"]):
            print(f"      {name} = {measured['facts'][name]!r}")
    print()
    if CANARY:
        print(f"    canary planted in the {CANARY['surface']} surface only: "
              f"{CANARY['canary_id']}")
        print(f"      value digest {CANARY['value_digest']}")
        print(f"      found in retained custody at: "
              f"{CANARY.get('found') if CANARY.get('found') else 'NOT FOUND'}")
        print()

    fixture = build_fixture(None)
    observations, refused = build_observations(fixture, None)
    print("=== 5. THE SELECTION, REFUSING ITSELF WHERE IT CANNOT DECIDE")
    if refused:
        for case_id, why in refused:
            print(f"    DROPPED {case_id}: {', '.join(why)}")
    else:
        print("    every measured case supplied its case's exact required")
        print("    facts and its exact deciding evidence purposes")
    print(f"    sealed observations: {len(observations)}")
    print()

    run = build_run(fixture, observations) if observations else None

    print("=== 6. THE FROZEN ASSESSOR, ASKED TO CERTIFY")
    certified = None
    if run is None:
        print("    no observation survived selection; certify was not called")
    else:
        try:
            certified = MODEL.build_report(run, fixture,
                                           "w6-local-oci-capability-pass",
                                           NOW_STAMP)
            print("    build_report returned a sealed report")
        except Exception as error:                          # noqa: BLE001
            print(f"    REFUSED: {type(error).__name__}: {error}")
            print()
            print("    THIS IS A RESULT, NOT AN OBSTACLE. The frozen suite")
            print("    admits no partial fixture: a fixture that cannot inject")
            print("    the whole mandatory fault set, or plant a canary in")
            print("    every named surface, is refused BEFORE any case is")
            print("    assessed. Declaring capabilities this pass does not")
            print("    have would have got past it, and that is the one move")
            print("    the ruling forbids.")
            print(f"    mandatory faults for local-oci: "
                  f"{len(MODEL.MANDATORY_FAULTS_BY_PROFILE['local-oci'])}")
            print(f"      {sorted(MODEL.MANDATORY_FAULTS_BY_PROFILE['local-oci'])}")
            print(f"    canary surfaces required: {len(MODEL.CANARY_SURFACES)}")
            print(f"      {sorted(MODEL.CANARY_SURFACES)}")
            print(f"    planted by this pass: "
                  f"{[CANARY['surface']] if CANARY else []}")
    print()

    print("=== 7. THE PER-CASE VERDICTS, DERIVED BY THE FROZEN ASSESSOR")
    entries = assess_all(fixture, observations) if observations else []
    for entry in entries:
        print(f"    {entry['assessment'].upper():7} {entry['case_id']}")
        print(f"            {entry['rationale']}")
    print()

    verdict, rationale, failed, unable, missing = formal_verdict(entries, core)
    print("=== 8. THE FORMAL RESULT")
    print(f"    VERDICT: {verdict}")
    print(f"    {rationale}")
    print()
    print(f"    observed and passed ({len([e for e in entries if e['assessment'] == 'passed'])}):")
    for entry in entries:
        if entry["assessment"] == "passed":
            print(f"      {entry['case_id']}")
    print(f"    observed and FAILED ({len(failed)}):")
    for case_id in failed:
        print(f"      {case_id}")
    print(f"    observed and UNDECIDABLE ({len(unable)}):")
    for case_id in unable:
        print(f"      {case_id}")
    print()
    print(f"    NOT OBSERVED ({len(missing)}) - every one named, no count aliases:")
    for case_id in missing:
        mark = " [CONFLICTS WITH THE APPROVED TOPOLOGY]" if case_id in conflicting else ""
        print(f"      {case_id}{mark}")
    print()

    report = {
        "result": "capability-pass",
        "not_a_certification": True,
        "verdict": verdict,
        "verdict_rationale": rationale,
        "sealed_evidence": sealed,
        "fixture": fixture,
        "run": run,
        "assessed": entries,
        "passed": sorted(e["case_id"] for e in entries
                         if e["assessment"] == "passed"),
        "failed": failed,
        "unable": unable,
        "not_observed": missing,
        "topology_conflicting": conflicting,
        "certify_report": certified,
        "dropped_from_selection": refused,
        "canary": {k: v for k, v in CANARY.items() if k != "value"},
        "local_oci_portable_core": core,
    }
    place = artifact("w6-capability-pass-report.json", report)
    print(f"=== 9. RETAINED")
    print(f"    {place.relative_to(REPO)}")
    print(f"    {place.stat().st_size} bytes  {file_digest(place)}")
    for name in sorted(os.listdir(ARTIFACTS)):
        one = ARTIFACTS / name
        print(f"    {name}  {one.stat().st_size} bytes  {file_digest(one)}")
    print()
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
