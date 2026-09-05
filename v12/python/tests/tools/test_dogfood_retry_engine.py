"""W39358 — the public retry, settled for real.

`test_dogfood_operator` proves the retry over a real authority with the world
outside the manager supplied. `test_dogfood_arc_engine` proves the ordinary arc
against a real daemon. This proves the thing neither does: the documented
`--retry-handoff` command, over durable state a real failing command produced,
COMPLETING the manager's settlement — positive absence, released material,
`resolved` and exit zero — with no second worker act.

THE IMAGE IS THIS TEST'S OWN, and that is the whole reason this gate is
writable. It keeps `/opt/baton/dogfood_entry.py` at the exact path
`WORKER_PROGRAM` execs — so the operator's binding to the dogfood image's own
entry is preserved rather than un-fixed — and injects the DETERMINISTIC
scripted agent through the same documented seam the Claude adapter uses,
`baton_worker.main(agent=...)`. A live provider turn is W39364's gate; a real
worker that really completes is not, once the agent behind the seam is one this
suite owns.

EVERYTHING ELSE IS REAL: the public commands, the authority, the control
store, the OCI adapter and engine port, the framed transport, the launch and
credential deliveries, and the manager's own freeze, intake, retention, custody
and destroy.

IT FAILS RATHER THAN SKIPS WITHOUT DOCKER, inheriting the lifecycle gate.
"""

import json
import os
import subprocess
import sys
import unittest
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))

from baton_v12.contracts import ContractRefusal            # noqa: E402
from tools import dogfood_operator                          # noqa: E402
from tests.manager import input_roots                       # noqa: E402
from tests.manager import test_lifecycle_composition as W   # noqa: E402

MARK = "baton-w39358-retry"
# THE AGENT THE IMAGE INSTALLS, and it is the reason this gate can settle.
#
# `dogfood_operator.PROPOSAL_MEMBERS` is `candidate`, `change.patch`,
# `result.json` and `verification.txt`, and `_derived` rederives the candidate
# tree against the staged source and reruns the task's frozen command over it.
# The M2 scripted agent writes one `result.txt` per declared path, which is a
# correct answer to the declaration and nothing this operator can verify -- so
# the agent is this test's own, injected through the same documented seam the
# Claude adapter uses, `baton_worker.main(agent=...)`.
#
# A RAW LITERAL, and that is not cosmetic. Written as an ordinary string, every
# `\n` inside the agent's own string literals became a REAL newline when this
# module was parsed, and the file the image installs was then syntactically
# invalid -- which reaches the operator as a bare `faulted` conversation
# naming nothing true.
ENTRY = r'''"""A test-owned entry at the dogfood path, writing a REAL proposal."""
import json
import os
import shutil
import sys

from baton_worker import main

OUTPUT = "/output"
SOURCE = "/input/source"


class ProposalAgent:
    """Deterministic, and in the shape THIS operator independently derives.

    The M2 scripted agent writes one `result.txt` under each declared path,
    which answers the DECLARATION correctly and produces nothing
    `dogfood_operator._derived` can verify: that function rederives
    `candidate/` against the staged source and reruns the task's own frozen
    command over it. So this writes the four `PROPOSAL_MEMBERS` -- the
    candidate tree and its three siblings -- and nothing else.

    DETERMINISTIC MEANS DERIVED, exactly as it does for the scripted agent:
    every byte comes from the declaration and the staged input, so two runs of
    one assignment produce one tree.
    """

    def consider(self, seen, request):
        del seen
        return {"contract_digest": request.get("contract_digest", ""),
                "decision": "accept",
                "reason": "the bounded task is one this agent performs"}

    def work(self, seen, declared):
        del seen
        answers = []
        for one in declared:
            place = os.path.join(OUTPUT, one["path"])
            candidate = os.path.join(place, "candidate")
            os.makedirs(candidate, exist_ok=True)
            # THE STAGED SOURCE, COPIED WITHOUT ITS METADATA. `copyfile` and
            # not `copy2`: the delivery is 0444 and owned by the manager, and
            # this runs as the container's fixed 65532 -- so preserving the
            # source's mode is a `chmod` toward an owner this process is not.
            for name in sorted(os.listdir(SOURCE)):
                here = os.path.join(SOURCE, name)
                if os.path.isfile(here):
                    shutil.copyfile(here, os.path.join(candidate, name))
            with open(os.path.join(candidate, "added.py"), "w",
                      encoding="utf-8") as handle:
                handle.write("def added():\n    return True\n")
            with open(os.path.join(place, "change.patch"), "w",
                      encoding="utf-8") as handle:
                handle.write("--- a/added.py\n+++ b/added.py\n")
            with open(os.path.join(place, "result.json"), "w",
                      encoding="utf-8") as handle:
                json.dump({"produced": one["name"]}, handle)
            with open(os.path.join(place, "verification.txt"), "w",
                      encoding="utf-8") as handle:
                handle.write("the agent ran no verification of its own\n")
            answers.append({"name": one["name"], "status": "present",
                            "result_metadata": {}})
        return {"disposition": "completed", "outputs": answers,
                "recap": "wrote a candidate tree and its three siblings"}


if __name__ == "__main__":
    sys.exit(main(agent=ProposalAgent()))
'''


class ThePublicRetrySettlesAgainstARealEngine(W.Lifecycle):
    """One real attempt, one failed handoff, one retry that settles it."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # DERIVED FROM THE REFERENCE IMAGE, which carries `baton_worker.py` and
        # the deterministic agent. What this adds is the ONE file the operator
        # execs, at the path it execs it from.
        cls.retry_image = f"{MARK}:{uuid.uuid4().hex[:12]}"
        cls.addClassCleanup(
            lambda: subprocess.run(
                [cls.engine, "image", "rm", "--force", cls.retry_image],
                capture_output=True, timeout=300))
        recipe = (f"FROM {cls.image}\n"
                  f"COPY dogfood_entry.py /opt/baton/dogfood_entry.py\n")
        import shutil
        import tempfile
        context = tempfile.mkdtemp(prefix="v12-w39358-retry-ctx-")
        cls.addClassCleanup(shutil.rmtree, context, True)
        with open(os.path.join(context, "dogfood_entry.py"), "w",
                  encoding="utf-8") as writing:
            writing.write(ENTRY)
        with open(os.path.join(context, "Dockerfile"), "w",
                  encoding="utf-8") as writing:
            writing.write(recipe)
        built = subprocess.run([cls.engine, "build", "-t", cls.retry_image,
                                context], capture_output=True, timeout=600)
        assert built.returncode == 0, (
            f"the retry image did not build: "
            f"{built.stderr.decode('utf-8', 'replace')[-1500:]}")
        found = subprocess.run(
            [cls.engine, "image", "inspect", cls.retry_image, "--format",
             "{{.Id}}"], capture_output=True, timeout=120)
        assert found.returncode == 0, found.stderr.decode("utf-8", "replace")
        resolved = found.stdout.decode("utf-8").strip()
        cls.retry_digest = (resolved if resolved.startswith("sha256:")
                            else f"sha256:{resolved}")

    def test_the_image_keeps_the_entry_the_operator_execs(self):
        """The binding this gate must not un-fix."""
        found = subprocess.run(
            [self.engine, "run", "--rm", "--network", "none",
             "--entrypoint", "/bin/sh", self.retry_digest,
             "-c", "test -s /opt/baton/dogfood_entry.py && echo present"],
            capture_output=True, timeout=300)
        self.assertEqual(found.returncode, 0,
                         found.stderr.decode("utf-8", "replace"))
        self.assertIn("present", found.stdout.decode("utf-8"))
        self.assertEqual(dogfood_operator.WORKER_PROGRAM[-1],
                         "/opt/baton/dogfood_entry.py")


    def world(self, retention="discard-after-intake"):
        """A real authority, a real store, and the grants that name them."""
        from baton_v12.authority import Authority
        from baton_v12.worker_manager import ControlStore, certify_profile
        from baton_v12.worker_manager.workspaces import (
            configure_workspace_storage)

        attempt = f"attempt-{uuid.uuid4().hex[:10]}"
        place = os.path.join(self.home, "authority.sqlite3")
        authority = Authority.create(place, authority_uuid=W.UUID,
                                     clock=lambda: W.NOW)
        authority.create_work(W.WORK_ID, "baton.impl",
                              contract="v12-assignment-1",
                              operation_id=f"create-{attempt}")
        authority.add_route_handler("baton.impl", W.WHO)
        # BOTH ROUTES ARE INSTALLED, and the round that withheld `rview` was
        # measured wrong. Review 2026-08-30T19:28:05Z asked for it on the
        # premise that a review route with no handler makes the pass REFUSE,
        # so the handoff would fail without this test arranging it. It does
        # not: `Authority.pass_work` moves the Work's route and ends the
        # assignment, and neither act consults `route_handler` at all -- run
        # against the real authority with `rview` withheld, the pass committed
        # and the whole arc resolved. A queued Work on a route nobody handles
        # yet is an ordinary v11 state, not a refusal.
        #
        # So the failure this gate recovers is produced the way the reviewed
        # operator suite already produces it -- `ThePublicRetryRunsFromReal\
        # DurableState.ordinary_capabilities` -- by a deployment facade whose
        # ONE act refuses. Everything else stays real.
        authority.add_route_handler("rview", W.WHO)
        authority.dispose()
        control = os.path.join(self.home, "control.sqlite3")
        store = ControlStore.open(control, incarnation="retry-setup",
                                  clock=lambda: W.NOW)
        certify_profile(store, "runtime", "dogfood", W.PROFILE)
        group = input_roots.configured_group(store)
        configure_workspace_storage(store, self.storage)
        store.close()
        del group

        source = os.path.join(self.home, "source")
        os.makedirs(source, exist_ok=True)
        with open(os.path.join(source, "harness.py"), "w",
                  encoding="utf-8") as writing:
            writing.write("print('the staged harness')\n")
        task = os.path.join(self.home, "task.json")
        with open(task, "w", encoding="utf-8") as writing:
            # W71917 moved the workload contract to `/2`. This staged tree is
            # an ordinary directory read in place, so the profile is `generic`
            # and no base is declared.
            json.dump({"schema": "baton.dogfood-task/2",
                       "task_id": "w39358-public-retry",
                       "instructions": "Do the bounded thing.",
                       "verification": ["python3", "harness.py"],
                       "source_root": "source",
                       "source_profile": "generic",
                       "declared_base": None}, writing)

        policies = {one: "sha256:" + f"{index}" * 64
                    for index, one in enumerate(
                        dogfood_operator.POLICY_DIGESTS, start=1)}
        given = {one: f"{one}-value"
                 for one in dogfood_operator.GRANT_MEMBERS}
        given.update({
            "engine": self.engine, "attempt_id": attempt,
            "offer_id": f"offer-{attempt}", "source": source,
            "task_path": task, "storage": self.storage,
            "launch_home": os.path.join(self.home, "launch"),
            "control_store": control, "authority_store": place,
            "incarnation": "retry-1",
            "credential_home": os.path.join(self.home, "credential-home"),
            "credential_slots": ["api"],
            "credential_profile": {"api": {"provider": "vault",
                                           "reference": "kv/one"}},
            "image_digest": self.retry_digest, "network": "none",
            "review_route": "rview",
            # W51473 made this an operator grant. The default this fixture
            # names is the one W39358's gate was written against, so the
            # discard arc it proves is unchanged; `world(retention=...)` is
            # what the retained gate below varies.
            "retention_disposition": retention,
            "work_ref": {"authority_uuid": W.UUID, "work_id": W.WORK_ID},
            "participant": W.WHO, "generation": 1, "now": W.NOW,
            "policies": policies,
            "record_binding": {"root": "baton-repository",
                               "path": "work/records",
                               "finding_digest": "sha256:" + "d" * 64,
                               "plan_digest": "sha256:" + "e" * 64},
            "assignment_contract": "v12-assignment-1",
            "human_contract": {"artifact_id": "human-1",
                               "media_type": "text/markdown", "bytes": 12,
                               "content_digest": "sha256:" + "b" * 64,
                               "locator": "artifact://human-1"},
            "role_instructions_digest": "sha256:" + "2" * 64,
            "runtime_profile_digest": W.PROFILE,
            "toolchain_digest": "sha256:" + "4" * 64,
            "adapter_digest": W.ADAPTER, "adapter_name": "oci",
            "labels": self.labels_for() if hasattr(self, "labels_for")
            else {"attempt": attempt},
            "retention_policy_digest": "sha256:" + "7" * 64})
        os.makedirs(given["launch_home"], exist_ok=True)
        os.makedirs(given["credential_home"], exist_ok=True)
        self.authority_place = place
        return given

    def refusing_capabilities(self, given):
        """The ordinary command's real capabilities, with a FAILING pass.

        The container, the worker, the transport, the freeze, the intake, the
        retention, the custody and the destroy are all the real ones this
        launcher builds. The single substitution is the deployment facade's
        `pass_work`, which is the act the retry exists to redo -- and it is
        the same substitution the reviewed operator suite makes for the same
        reason.
        """
        built = dogfood_operator._launched(
            given, credential_provider=lambda _p, _r: "probe-secret")

        class Refusing:
            """The deployment's facade, with the one act that fails."""

            def __init__(self, facade):
                self._facade = facade
                self.participant = facade.participant

            def __getattr__(self, name):
                return getattr(self._facade, name)

            def pass_work(self, operands):
                del operands
                raise ContractRefusal(
                    "refused", "precondition",
                    "the review route is not accepting work just now")

        built["session"] = Refusing(built["session"])
        return built

    def test_the_public_retry_settles_a_handoff_the_command_failed(self):
        """The whole gate: a real failed handoff, and the documented retry.

        THE ORDINARY COMMAND IS REAL ALL THE WAY DOWN -- a container, a
        worker, a framed conversation, a freeze over the worker's own
        envelope, an intake receipt, a retention decision, an independent
        rederivation of the candidate tree and the task's frozen command rerun
        outside the container, then a destroy, directory custody and the
        removal of both execution roots. Only the pass refuses.

        THEN THE DOCUMENTED COMMAND SETTLES IT, over nothing but the retained
        record and the manager's own durable state: the pass commits, the
        ending replays, `unresolved` empties and the status is zero -- with no
        second container, no second conversation and no second freeze.
        """
        given = self.world()
        grants = os.path.join(self.home, "grants.json")
        with open(grants, "wb") as writing:
            writing.write(json.dumps(given).encode("utf-8"))
        evidence = os.path.join(self.home, "evidence.json")

        # -- the ordinary command, whose handoff fails ----------------------
        self.assertEqual(
            dogfood_operator.main(["--grants", grants, "--evidence", evidence],
                                  capabilities=self.refusing_capabilities),
            1, "a command whose pass refused reported success")
        failed = self.written(evidence)

        self.assertEqual(failed["conversation"],
                         {"answered": ["describe", "work"],
                          "ending": "answered", "why": None},
                         "the real worker conversation did not complete")
        self.assertEqual(failed["worker_disposition"], "completed")
        self.assertIsNotNone(failed["output"]["manifest_digest"],
                             "the manager did not freeze a real result")
        self.assertIsNotNone(failed["intake_receipt"]["receipt_digest"],
                             "the manager did not take custody of it")
        self.assertEqual(failed["retention"]["disposition"],
                         "discard-after-intake")
        # THE OPERATOR'S OWN DERIVATION, over the tree custody holds: all four
        # proposal members present, the one added file seen by BYTES against
        # the staged source, and the task's frozen command exiting zero.
        self.assertEqual(failed["independent"]["members_present"],
                         list(dogfood_operator.PROPOSAL_MEMBERS))
        self.assertEqual(failed["independent"]["changed_paths"], ["added.py"])
        self.assertEqual(failed["independent"]["verification_status"], 0)
        # AND THE ENDING COULD NOT BE CLAIMED, which is the manager's own
        # answer and not this deployment declining to try. `_after_start`
        # settles in a `finally`, so `authorize_cleanup` really was asked --
        # and it refused, because a pass that did not commit leaves the
        # assignment LIVE, and cleanup destroys the runtime of an assignment
        # that has ended. So the two acts the retry redoes are the two that
        # are missing here, in the order it redoes them: the pass ends the
        # assignment, and only then is the ending authorized at all.
        self.assertIsNone(failed["cleanup"], "the ending was claimed anyway")
        self.assertIsNone(failed["review_pass"], "the pass did not fail")
        self.assertFalse(failed["resolved"])
        self.assertEqual(len(failed["unresolved"]), 2, failed["unresolved"])
        self.assertIn("the review route is not accepting work just now",
                      failed["unresolved"][0])
        self.assertIn("is still the live assignment",
                      failed["unresolved"][1])
        # THE RUNTIME IS STOPPED EITHER WAY. Quiescence is ordered before the
        # ending is attempted, so a handoff this deployment could not complete
        # does not leave somebody's code executing.
        self.assertEqual(failed["quiescence"]["state"], "quiescent")

        # -- the documented retry, over that record and nothing else --------
        from baton_v12.worker_manager import worker_entry
        from unittest import mock

        with mock.patch.object(
                worker_entry, "converse",
                side_effect=AssertionError("a retry opened a conversation")):
            self.assertEqual(
                dogfood_operator.main(
                    ["--grants", grants, "--evidence", evidence,
                     "--retry-handoff"],
                    capabilities=lambda _g: self.fail(
                        "the ordinary builder ran during a retry"),
                    retry_capabilities=dogfood_operator._for_retry),
                0, "the retry did not resolve the attempt")
        settled = self.written(evidence)

        # THE PASS, ASKED OF THE AUTHORITY rather than of the record this
        # deployment wrote.
        from baton_v12.authority import Authority

        authority = Authority.open(self.authority_place)
        try:
            self.assertIsNone(authority.assignment_of(W.WORK_ID),
                              "the assignment was not ended by the pass")
            self.assertEqual(authority.project_work(W.WORK_ID)["route"],
                             "rview", "the Work was not passed to review")
        finally:
            authority.dispose()
        self.assertEqual(settled["review_pass"]["route"], "rview")
        self.assertEqual(settled["review_pass"]["cause"], "pass")
        self.assertFalse(settled["review_pass"]["fenced"])
        self.assertEqual(settled["review_pass"]["phase"], "queued")
        self.assertIsNone(settled["review_pass"]["gate"])
        # THE SETTLEMENT IS COMPLETE, and the record says so with nothing left
        # over: the retry sets the failed command's own sentences aside and
        # writes what is true after it.
        self.assertEqual(settled["unresolved"], [])
        self.assertTrue(settled["resolved"])
        self.assertEqual(settled["cleanup"]["state"], "absent")

        # AND NOTHING WORKER-SIDE HAPPENED A SECOND TIME. The conversation is
        # the one the first command held, the runtime is the one it started,
        # and the daemon does not have it.
        self.assertEqual(settled["conversation"], failed["conversation"])
        self.assertEqual(settled["runtime_id"], failed["runtime_id"])
        self.assertEqual(settled["output"], failed["output"])
        found = subprocess.run(
            [self.engine, "inspect", settled["runtime_id"]],
            capture_output=True, timeout=120)
        self.assertNotEqual(found.returncode, 0,
                            "the runtime this attempt started still exists")

    def written(self, place):
        """The evidence document, read the way an operator reads it."""
        with open(place, "rb") as reading:
            return json.loads(reading.read())

    def ordinary(self, given):
        """The real capabilities, with a pass that works."""
        return dogfood_operator._launched(
            given, credential_provider=lambda _p, _r: "probe-secret")

    def commanded(self, given):
        """One ordinary command over these grants; answers status and record."""
        grants = os.path.join(self.home, f"grants-{given['attempt_id']}.json")
        with open(grants, "wb") as writing:
            writing.write(json.dumps(given).encode("utf-8"))
        evidence = os.path.join(self.home,
                                f"evidence-{given['attempt_id']}.json")
        status = dogfood_operator.main(
            ["--grants", grants, "--evidence", evidence],
            capabilities=self.ordinary)
        return status, self.written(evidence)

    def test_a_retained_run_resolves_and_leaves_a_reviewable_candidate(self):
        """W51473's acceptance, against a real daemon and no live provider.

        THE DEFECT THIS CLOSES was found by the first live attempt and not by
        reading: the arc completed, the manager took custody of an
        86,417-byte proposal, and a HARD-CODED `discard-after-intake` then
        removed it -- taking the worker's own account of its answer and the
        candidate a human is required to inspect. The sealed result's own
        locator named a directory that no longer existed.

        SO THIS ASKS THE DISK, AFTER THE COMMAND RETURNS. `_settle` discards
        the execution roots inside the terminal transaction, so a candidate
        that is still readable here is one that survived the ending rather
        than one observed before it.

        AND IT PERFORMS THE ACCEPTANCE ITSELF -- the independent diff and the
        verification rerun the review contract requires a human to do. A
        retained locator that could not be diffed and rerun would satisfy the
        letter of "retained" and none of its purpose.
        """
        given = self.world(retention="retain")
        status, written = self.commanded(given)

        self.assertEqual(status, 0, written.get("unresolved"))
        self.assertEqual(written["unresolved"], [])
        self.assertTrue(written["resolved"])
        # THE MANAGER'S OWN COMMITTED DECISION, not the grant echoed back.
        self.assertEqual(written["retention"]["disposition"], "retain")
        # `retained` AND NOT `complete`, which is the whole reason a literal
        # swap would not have been the fix: this deployment used to call every
        # ending but `complete` a failure, so an intended keep was unresolved.
        self.assertEqual(written["cleanup"],
                         {"cleanup": "retained", "state": "absent"})
        # POSITIVE ABSENCE IS STILL REQUIRED. Keeping the material says
        # nothing about the runtime, and `retained` does not relax it.
        self.assertEqual(written["observed_after"]["state"], "absent")

        # -- and now the acceptance the retention exists for ----------------
        self.assertEqual(len(written["custody"]), 1, written["custody"])
        locator = written["custody"][0]["custody_locator"]
        proposal = dogfood_operator._proposal_root(locator)
        self.assertTrue(os.path.isdir(proposal),
                        f"the retained candidate at {locator} is gone")
        self.assertEqual(
            sorted(os.listdir(proposal)),
            sorted(dogfood_operator.PROPOSAL_MEMBERS),
            "the retained proposal is not the one the operator derived")

        candidate = os.path.join(proposal, "candidate")
        # THE INDEPENDENT DIFF, performed rather than promised.
        self.assertEqual(
            sorted(dogfood_operator._changed_paths(
                os.path.join(given["source"]), candidate)),
            ["added.py"])
        # AND THE TASK'S OWN VERIFICATION, RERUN OUTSIDE THE WORKER over the
        # retained tree -- the exact command the review contract names.
        task = dogfood_operator.frozen_task(given["task_path"])
        rerun = subprocess.run(list(task["verification"]), cwd=candidate,
                               capture_output=True, timeout=300)
        self.assertEqual(rerun.returncode, 0,
                         rerun.stderr.decode("utf-8", "replace"))

    def test_an_explicit_discard_still_ends_complete_and_removes_the_tree(self):
        """The control, and the regression this Work must not cause.

        A deployment that explicitly chooses a discard gets exactly what the
        hard-coded literal used to give it -- `complete`, an absent tree --
        and the difference is that it CHOSE it. Without this case the change
        could have made every run retain and nobody would notice.
        """
        given = self.world(retention="discard-after-intake")
        status, written = self.commanded(given)

        self.assertEqual(status, 0, written.get("unresolved"))
        self.assertEqual(written["unresolved"], [])
        self.assertTrue(written["resolved"])
        self.assertEqual(written["retention"]["disposition"],
                         "discard-after-intake")
        self.assertEqual(written["cleanup"],
                         {"cleanup": "complete", "state": "absent"})
        locator = written["custody"][0]["custody_locator"]
        self.assertFalse(
            os.path.isdir(dogfood_operator._proposal_root(locator)),
            "an explicit discard left the material behind")




class DockerPublicRetry(ThePublicRetrySettlesAgainstARealEngine,
                        unittest.TestCase):
    engine = "docker"
    required = True
