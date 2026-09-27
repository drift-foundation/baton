"""W275774 — the REAL TOOL's abandonment returns the token its start reserved.

Review 20:48:20Z corrected a label of mine rather than accepting it, and it was right:
`TheGENERATIONSEQUENCE.abandoned` calls `intake.abandon_attempt` DIRECTLY, so what it
proves is the manager API's fourth ending and not the tool's. The full-tool claim was
unproved, and this file is it.

WHAT IS REAL HERE. The whole `tools/single_worker.py` composition over real Authority,
Job and Control stores: the offer, the claim, the activation, the governed two-act
launch, the published command sequence, then the tool's own
`operations.abandon_attempt(...)` with the attempt's real stage document -- which
composes the per-attempt adapter, the credential and launch deliveries, the Authority
fence, `destroy_abandoned`, both custody acts and the gate discharge.

WHAT IS CONTROLLED, and only this: the engine process boundary, exactly as every case in
`tests/tools/test_single_worker.py` controls it. `Removing` extends that suite's own
`Engine` with two facts it does not model -- that a force-removed identity is afterwards
ABSENT, and that a custody act prints its account -- because an abandonment cannot reach
its ending without either. Nothing about the manager, the tool or the token path is
substituted. No live engine, no provider, no container.
"""
import json
import unittest

from baton_v12.job_manager import submit
from baton_v12.worker_manager import attempts as manager_attempts
from baton_v12.worker_manager import tokens

from tests.tools.test_single_worker import Engine, SingleWorkerCase


class Removing(Engine):
    """That suite's engine, plus REMOVAL and the custodian's own account.

    REMOVAL: `destroy_abandoned` force-removes the exact identity and then proves it
    gone, and the base fixture answers `inspect` with the same `Id` forever -- so
    absence was unreachable and the ending settled `failed`. An `rm` here makes the
    identity absent afterwards, which is the one engine fact the ending rests on.

    THE CUSTODY ACCOUNT: the act is a container whose STDOUT is its answer, and the
    manager refuses an act it cannot account for. The verb and the submission token are
    read off the composed argv and echoed, so the answer belongs to the act that asked
    -- which is the property `custody._accountable` checks and a fixture inventing its
    own token would bypass.
    """

    def __init__(self):
        super().__init__()
        self.removed = False
        self.custody = []

    def __call__(self, argv, *, seconds=None):
        if "--entrypoint" in argv:
            self.vectors.append(list(argv))
            verb, submission = argv[-2], argv[-1]
            self.custody.append((verb, submission))
            return self.answer(stdout=json.dumps(
                {"custody": verb, "submission": submission, "entries": 0,
                 "not_ours": 0, "running_as": [0, 0]}))
        if argv[1] == "rm":
            self.vectors.append(list(argv))
            self.removed = True
            return self.answer(stdout=(self.runtime_id or "") + "\n")
        if self.removed and argv[1] in ("inspect", "ps"):
            self.vectors.append(list(argv))
            if argv[1] == "ps":
                return self.answer()
            return self.answer(status=1,
                               stderr=f"No such object: {self.runtime_id}")
        return super().__call__(argv, seconds=seconds)


class TheToolsOwnAbandonment(SingleWorkerCase):

    REASON = "the supervised worker conversation was lost"

    def started(self, incarnation):
        """The tool driven to a commanded worker, with its token held."""
        engine = Removing()
        job, control = self.stores(incarnation)
        submit(job, self.submission)
        operations = self.operations(job, control, engine)
        stage = self.commanded(job, operations)["jobs"][0]["stages"][0]
        attempt = manager_attempts._require_attempt(control,
                                                   stage["attempt_id"])
        domain = tokens.domain_of("workspace",
                                  tokens.workspace_identity(attempt))
        held = tokens.outstanding(control, domain)
        self.assertEqual([one["execution"] for one in held],
                         [stage["attempt_id"]],
                         "the governed start must hold this workspace object")
        return engine, control, operations, stage, domain

    def abandoned(self, operations, stage):
        return operations.abandon_attempt(attempt_id=stage["attempt_id"],
                                          reason=self.REASON, stage=stage)

    def test_the_tools_own_abandonment_returns_the_governed_token(self):
        """THE FULL-TOOL CLAIM, made where it can actually be made.

        The tool's own ending, over the token its own governed start reserved. Every
        assertion is on what crossed or what the journal says, not on the composition's
        word for it.
        """
        engine, control, operations, stage, domain = self.started("tool-abandon")
        attempt_id = stage["attempt_id"]
        runtime = engine.runtime_id
        answered = self.abandoned(operations, stage)
        # THE AUTHORITY WAS FENCED AND THE ENDING SETTLED ON POSITIVE ABSENCE.
        self.assertTrue(answered["fenced"]["fenced"])
        self.assertEqual(answered["cleanup"]["cleanup"], "retained")
        self.assertEqual(answered["cleanup"]["state"], "absent")
        # THE ENGINE'S OWN ACCOUNT: the exact identity force-removed, once.
        removals = [one for one in engine.vectors if one[1] == "rm"]
        self.assertEqual([one[-1] for one in removals], [runtime])
        self.assertIn("--force", removals[0])
        # AND BOTH GOVERNED ROOTS NORMALIZED under this manager's own custody.
        self.assertEqual([one[0] for one in engine.custody],
                         ["normalize", "normalize"])
        self.assertEqual(sorted(answered["cleanup"]["directory_custody"]),
                         ["result", "workspace"])
        # THE RESOURCE IS RETURNED, by the tool's ending and not by hand.
        self.assertEqual(tokens.outstanding(control, domain), [],
                         "the tool's abandonment must return what it reserved")
        self.assertTrue(tokens.token_of(control, domain, 1)["returned"])
        self.assertEqual(tokens.token_of(control, domain, 1)["execution"],
                         attempt_id)
        operations.close()

    def test_a_replayed_tool_abandonment_leaves_a_later_generation_alone(self):
        """THE ISOLATION HALF: the terminal ending replays, and touches nothing else.

        An abandonment is terminal, so its replay is the last thing that will ever run
        for that attempt -- and it must resolve the generation ITS OWN start reserved
        rather than whatever the domain holds now.

        WHAT GENERATION 2 IS HERE, stated exactly: a production `Governance.reserve`
        for a different execution over the same domain. It is not a second tool start
        -- this harness serves one worker and a second Work would be a different
        fixture -- so what this case establishes is the REPLAY's behaviour, which is
        the tool's side of the property, and not a second connected execution. The
        connected generations 1/2/3 are proved in `test_connected_lifecycle.py`.
        """
        engine, control, operations, stage, domain = self.started("tool-replay")
        self.abandoned(operations, stage)
        self.assertEqual(tokens.outstanding(control, domain), [])
        later = tokens.workspace_governance().reserve(
            control, {"runtime_attempt_id": "attempt-later",
                      "workspace_device": int(domain.split(":")[1]),
                      "workspace_inode": int(domain.split(":")[2])},
            operation="runtime.start:attempt-later")
        self.assertEqual(later.token["generation"], 2)
        # THE TERMINAL REPLAY.
        self.abandoned(operations, stage)
        held = tokens.outstanding(control, domain)
        self.assertEqual([one["generation"] for one in held], [2],
                         "a replayed tool abandonment released a live generation")
        self.assertEqual(held[0]["execution"], "attempt-later")
        operations.close()


if __name__ == "__main__":
    unittest.main()
