"""W275774 — THE CONNECTED LIFECYCLE: real rows, real start, real ending.

Review 18:46:09Z corrected a claim of mine rather than accepting it, and this file
exists because the correction was right. `TheSplitOnREALATTEMPTROWS.governed_start`
in `test_governed_start.py` does NOT call `attempts.request_runtime_start`: it reads
an already-retained, already-ended fixture row and then reserves, binds and settles
the token directly. That proves the governance COMPOSITION over a real row and a real
allocation, which is worth keeping, and it is not the connected execution I named it.

So here the token is acquired BY THE PRODUCTION START ITSELF. The one fixture hook is
`attempt`, which the intake suite's own `frozen`/`retained_ready` chain already calls,
and it differs from `IntakeCase.attempt` in exactly three ways -- each one required to
make the seam real rather than adjacent:

  * THE WORKSPACE IS ALLOCATED UNDER THE DEPLOYMENT'S CONFIGURED STORAGE, through
    `assignment_workspace`, so the object `workspaces.governed_resource_identity`
    resolves is the object this attempt's runtime is composed against. The shared
    fixture composes its root under a private temporary storage, which is fine for a
    suite about intake and would have left the governed identity naming a directory
    nothing here had built.
  * THE BOUNDARY IDENTITY IS PINNED FROM A REAL `os.stat` of that allocation, before
    the start. No fabricated device or inode appears in this file.
  * THE START IS `attempts.request_runtime_start` WITH CONTROL-BOUND GOVERNANCE, and
    the adapter counts what crossed -- one `start`, one admission document naming the
    exact container.

AND THE CONTENTION LOSER IS NOW RECOVERABLE, which review 19:13:42Z directed after the
previous claim measured the gap here. A losing start was settled `uncertain` -- the
value reserved for a state this manager cannot establish -- even though the engine was
provably never reached, and no ending anywhere would then act on it, so its Work's
runtime lane stayed occupied for the life of the store. The corrections are in
`attempts._identify` (a proved non-submission is a positive absence, not uncertainty)
and `intake.authorize_failed_start_cleanup` (a proved non-launch is an ending too), and
the last four cases below are their evidence in both directions: positive absence
releases, unknown discovery still holds, and a discovered runtime is attached rather
than called absent.

Real disposable stores, real allocations under a temporary configured storage, the
suites' own controlled adapter doubles. No live engine, no provider, no container
created or signalled.
"""
import os
import sqlite3
import unittest

from baton_v12.contracts import ContractRefusal
from baton_v12.worker_manager import (accept_offer, activate_assignment,
                                      issue_offer, load_manifest, observe,
                                      reconcile_runtime, record_attempt,
                                      request_runtime_start, submit_claim)
from baton_v12.worker_manager import attempts, intake, tokens, workspaces
from baton_v12.worker_manager import documents as manager_documents

from tests.manager import input_roots
from tests.manager.test_attempts import ADAPTER, Adapter as RuntimeAdapter
from tests.manager.test_offers import (NOW, PROFILE, ROUTE, SCOPE, WHO,
                                       decision)
from tests.manager.test_output import (ATTEMPT, AUTHORITY, JOB, POLICY,
                                       OutputCase)
from tests.manager.test_intake import (RETENTION, Custodian,
                                       RetainedAndCompleteAreDifferentEndings)

# THE SECOND AND THIRD REAL ATTEMPTS, and their own Works. The runtime LANE is keyed
# by `(authority_uuid, work_id)` and excludes every other attempt over one Work -- so
# a competing attempt inside this Work never reaches the token at all, and a case
# that used one would be measuring the lane. Two Works over one workspace object is
# also the contention the token is FOR: the lane cannot see the other Work, and the
# durable resource does not care which Work is writing to it.
BESIDE = "attempt-beside"
OTHER_JOB = "43c55d4b-W1440"


class Counting(RuntimeAdapter):
    """The two-act adapter, counting what actually crossed the seam."""

    def __init__(self, runtime_id="runtime-1"):
        super().__init__(runtime_id)
        self.admissions = []

    def start(self, request, *, bind=None):
        # THE ADMISSION IS TAKEN BEFORE THE ENGINE WOULD BE, which is the order
        # `oci.OciAdapter.start` enforces: bind the container, ask permission, and
        # only then activate. A double that started first would pass every case here
        # while proving the opposite of the boundary.
        if bind is not None:
            self.admissions.append(bind(self.runtime_id)())
        return super().start(request)


class Discovering(Counting):
    """A start adapter whose DISCOVERY a case decides.

    `_start_failed` asks the adapter which runtimes carry this attempt's labels, and
    what that answer is decides whether a failed start is attached, uncertain or a
    proved non-launch. Two cases below need the two answers a controlled listing can
    give that the default cannot: another runtime already carrying these labels, and
    an adapter that cannot answer at all.
    """

    def __init__(self, runtime_id="runtime-2", listing=None, failure=None):
        super().__init__(runtime_id)
        self._listing = listing
        self._failure = failure

    def list(self, operands):
        if self._failure is not None:
            raise self._failure
        if self._listing is not None:
            return [{"runtime_id": self.runtime_id,
                     "labels": operands["labels"]}]
        return super().list(operands)


class Attaching(Counting):
    """An adapter that reports an empty listing AND lets a writer in behind it.

    The attachment race review 19-53-28Z asked for, driven where it can actually
    happen: `list` is the last thing the identification asks, so an attachment that
    lands during it is one this call's own answer cannot see. It is performed by the
    REAL `reconcile_runtime` over a second adapter, so the row is changed by
    production code rather than by a fixture writing columns.
    """

    def __init__(self, store, attempt_id, runtime_id="runtime-9"):
        super().__init__(runtime_id)
        self._store = store
        self._attempt = attempt_id
        self.attached = []

    def list(self, operands):
        if not self.attached:
            self.attached.append(self.runtime_id)
            reconcile_runtime(self._store, Discovering(self.runtime_id, True),
                              attempt_id=self._attempt)
        return []


class Remover(Custodian):
    """The cleanup double plus the one verb a failed-start ending requires.

    THE VERB EXISTS SO THE BOUNDARY IS NOT WEAKENED FOR A FIXTURE.
    `authorize_failed_start_cleanup` owns `destroy_failed_start` as a capability
    at its public boundary, before it knows whether anything needs destroying,
    and that order is right -- so the double answers it and the non-launch case
    asserts it was NEVER CALLED rather than arranging for it to be absent.
    """

    def __init__(self, *arguments, **operands):
        super().__init__(*arguments, **operands)
        self.removed = []

    def destroy_failed_start(self, command):
        self.removed.append(dict(command))
        return {"runtime_id": command["runtime_id"], "state": "absent",
                "why": "the engine answered that this exact identity does not "
                       "exist",
                "credentials": {"lifecycle_state": "not-delivered"},
                "launch": {"lifecycle_state": "not-delivered"}}


class TheGovernedStartAndItsOwnEnding(RetainedAndCompleteAreDifferentEndings):
    """One attempt's whole governed lifecycle, driven through both productions."""

    def governance(self):
        """The control-bound authority, which is what `tools/single_worker.py` starts
        with: the identity carries the containment argument because a store is here."""
        return tokens.workspace_governance(control=self.store)

    def workspace_of(self, assignment_id):
        return os.path.join(self.storage, assignment_id, "workspace")

    def row_of(self, assignment_id):
        beside = sqlite3.connect(self.path)
        beside.row_factory = sqlite3.Row
        try:
            found = beside.execute(
                "SELECT * FROM attempts WHERE runtime_attempt_id = ?",
                (assignment_id,)).fetchone()
            return {name: found[name] for name in found.keys()}
        finally:
            beside.close()

    def lanes(self):
        beside = sqlite3.connect(self.path)
        try:
            return [one[0] for one in beside.execute(
                "SELECT holder FROM runtime_lanes ORDER BY holder")]
        finally:
            beside.close()

    # -- the fixture hook ------------------------------------------------------

    def attempt(self, *, quiescent=True, disposition="completed"):
        """The intake suite's own attempt, WITH THE START GOVERNED.

        Called by `frozen` -> `retained_ready` exactly as the shared one is, so
        every inherited case in this class also runs through the governed start --
        which is the cheapest regression evidence available: an ending that stopped
        working under governance would fail here without any case of mine.
        """
        OutputCase.attempt(self, quiescent=False, disposition=None)
        self.runtime = Counting()
        inputs, _ = input_roots.composed(
            self, self.storage,
            given=load_manifest(self.store, self.input_digest, "inputManifest"),
            work_ref={"authority_uuid": AUTHORITY, "work_id": JOB},
            participant=WHO, generation=1, runtime_attempt_id=ATTEMPT)
        self.pinned = self.pin(ATTEMPT, inputs)
        request_runtime_start(self.store, self.runtime, attempt_id=ATTEMPT,
                              inputs=inputs, govern=self.governance())
        reconcile_runtime(self.store, self.runtime, attempt_id=ATTEMPT)
        if quiescent:
            observe(self.store, attempt_id=ATTEMPT, axis="execution_runtime",
                    value="quiescent")
        if disposition is not None:
            observe(self.store, attempt_id=ATTEMPT, axis="worker_disposition",
                    value=disposition)
        return ATTEMPT

    def pin(self, assignment_id, inputs):
        """The two boundary objects AS THIS MANAGER READ THEM, and nothing invented."""
        root = self.workspace_of(assignment_id)
        found, source = os.stat(root), os.stat(inputs)
        attempts.pin_boundary_identity(
            self.store, attempt_id=assignment_id,
            source=(source.st_dev, source.st_ino),
            workspace=(found.st_dev, found.st_ino))
        return f"{found.st_dev}:{found.st_ino}"

    def authorized(self, assignment_id, *, offer_id, work_id):
        """A SECOND REAL AUTHORIZED ATTEMPT ROW, through the production path.

        Review 18:46:09Z: "Do not substitute a copied dictionary." So this is the
        whole offer/accept/record/claim/activate sequence a delivery performs, with
        its own composed input root under the same configured storage. It answers the
        `inputs` a governed start needs, and the row it leaves is a row every
        production entry accepts.
        """
        live = {"work_ref": {"authority_uuid": AUTHORITY, "work_id": work_id},
                "participant": WHO, "generation": 1}
        self.session._work = {"status": "open", "phase": "queued",
                              "handler": None, "gate": None,
                              "authority_uuid": AUTHORITY,
                              "scope": SCOPE, "route": ROUTE}
        self.session.claim_answer = {"assignment": dict(live),
                                     "claim_event": 1, "decision": decision()}
        self.session.live_assignment = dict(live)
        given, assignment = input_roots.documents(
            work_ref=dict(live["work_ref"]), participant=WHO, generation=1,
            runtime_attempt_id=assignment_id)
        issue_offer(self.store, self.port, offer_id=offer_id, work_id=work_id,
                    runtime_attempt_id=assignment_id,
                    input_digest=given["manifest_digest"],
                    policy_digest=POLICY, profile_digest=PROFILE,
                    profile_name="reference",
                    mint_bearer=lambda: "bearer-" + assignment_id)
        accept_offer(self.store, self.port, offer_id=offer_id,
                     decision="accept", bearer="bearer-" + assignment_id,
                     now=NOW, runtime_attempt_id=assignment_id,
                     work_ref=dict(live["work_ref"]))
        record_attempt(self.store, attempt_id=assignment_id,
                       adapter_name="acp", adapter_digest=ADAPTER,
                       profile_digest=PROFILE,
                       input_digest=given["manifest_digest"],
                       policy_digest=POLICY)
        submit_claim(self.store, self.port, offer_id=offer_id)
        activate_assignment(self.store, self.port, attempt_id=assignment_id,
                            expect=dict(live))
        inputs = workspaces.assignment_workspace(
            input_roots.configured_group(self.store), self.storage,
            assignment_id)["inputs"]
        workspaces.compose_input_root(
            inputs, given, assignment,
            assignment=dict(assignment["assignment_ref"]),
            runtime_attempt_id=assignment_id)
        self.addCleanup(input_roots._forcibly_remove, inputs)
        return inputs

    def carried_over(self, assignment_id):
        """Carry THE FIRST ATTEMPT'S OWN OBJECT into the later assignment's position.

        WHY A MOVE RATHER THAN A SECOND ALLOCATION. The canonical layout gives every
        assignment its own sibling directory, so two allocations are two objects and
        could never contend -- the shared durable resource only exists when one
        object is REUSED. Renaming carries the inode, so the later assignment's
        governed root provably resolves to the object the first one held; the cases
        assert that equality rather than assuming it.

        THE LATER ASSIGNMENT'S OWN OBJECT IS PRESERVED BESIDE IT rather than removed,
        for review 18:42:29Z's reason: an unlinked directory frees its inode and the
        move could then be handed the same number back, which would make "the same
        resource" an accident of allocation instead of a fact.

        AND THE MODE IS RESTORED. These homes are deliberately not writable by the
        worker; this manager owns them, and relaxing one to move an object inside it
        is the same act `input_roots._forcibly_remove` performs to take one away.
        """
        homes = [os.path.dirname(self.workspace_of(one))
                 for one in (ATTEMPT, assignment_id)]
        modes = [os.stat(one).st_mode & 0o7777 for one in homes]
        for one in homes:
            os.chmod(one, 0o700)
        place = self.workspace_of(assignment_id)
        try:
            os.rename(place, place + ".own")
            os.rename(self.workspace_of(ATTEMPT), place)
        finally:
            for one, mode in zip(homes, modes):
                os.chmod(one, mode)

    def ending(self, govern):
        """The real cleanup ending, governed."""
        return intake.authorize_cleanup(
            self.store, self.port, Custodian(), attempt_id=ATTEMPT,
            retention_policy_digest=RETENTION, govern=govern)

    # -- one attempt, start to ending -----------------------------------------

    def test_the_real_start_reserves_and_the_real_ending_returns(self):
        """THE CONNECTED CASE, and every crossing is asserted at its own boundary.

        The token is acquired by `request_runtime_start`, the container that crossed
        is the container the token was bound to, the admission was taken before the
        engine, and the real `authorize_cleanup` returns the generation that start
        reserved. A reservation taken beside the start instead of by it would not
        carry the journalled start's operation identity, which is asserted here
        against the row rather than against a constant.
        """
        self.retained_ready("discard-after-intake")
        row = self.row_of(ATTEMPT)
        domain = tokens.domain_of("workspace", self.pinned)
        operation = attempts._start_operation_id(row)
        # WHAT CROSSED, counted at the adapter.
        self.assertEqual(len(self.runtime.started), 1)
        self.assertEqual(len(self.runtime.admissions), 1)
        self.assertEqual(self.runtime.admissions[0]["container"], "runtime-1")
        self.assertEqual(self.runtime.started[0]["operation_id"], operation)
        # WHAT THE ROW SAYS, which is the durable half.
        self.assertEqual(row["runtime_id"], "runtime-1")
        # AND WHAT THE TOKEN SAYS, over the object that was really allocated.
        current = tokens.token_of(self.store, domain, 1)
        self.assertEqual(current["container"], "runtime-1")
        self.assertEqual(current["launch"], operation)
        self.assertEqual(current["execution"], ATTEMPT)
        self.assertTrue(current["activation_started"])
        self.assertFalse(current["activating"])
        self.assertEqual(
            self.pinned,
            workspaces.governed_resource_identity(self.store, ATTEMPT),
            "the governed identity is the allocation, not the pin's word for it")
        # AND THE REAL ENDING, with the identity form the real tool passes.
        self.ended()
        answer = self.ending(tokens.workspace_governance())
        self.assertEqual(answer["cleanup"], "complete")
        self.assertEqual(answer["state"], "absent")
        self.assertEqual(tokens.outstanding(self.store, domain), [],
                         "the ending returned what the start reserved")

    def test_a_control_bound_ENDING_cannot_name_what_it_has_removed(self):
        """WHY THE ENDING TAKES THE PIN AND THE START TAKES THE ARGUMENT.

        This asymmetry looks like an oversight in `tools/single_worker.py` -- the
        start is governed with `control=` and the endings are not -- and it is
        load-bearing. `authorize_cleanup` performs the ordinary removal of the two
        execution roots BEFORE it commits the ending, and `_released` runs after that
        commit, so a control-bound ending asks the filesystem for an object the same
        call has already deleted and is refused. The token is then left held with the
        cleanup's own answer lost.

        THE PIN IS WHAT SURVIVES THE OBJECT, and the start is what makes the pin
        trustworthy: `governed_workspace_identity` refuses unless the containment
        argument AGREES with the pinned identity, so the domain the ending computes
        from the row is the domain the argument approved. This case is the one that
        fails if somebody "completes" that asymmetry.
        """
        self.retained_ready("discard-after-intake")
        domain = tokens.domain_of("workspace", self.pinned)
        self.ended()
        with self.assertRaises(ContractRefusal) as caught:
            self.ending(self.governance())
        self.assertEqual(caught.exception.category, "integrity")
        self.assertIn("could not be read at", caught.exception.message)
        self.assertEqual(len(tokens.outstanding(self.store, domain)), 1,
                         "and the resource stays held rather than stranded quietly")

    # -- two real attempts over one durable object -----------------------------

    def test_a_competing_real_attempt_is_refused_before_the_engine(self):
        """REAL COMPETING ATTEMPTS: two Works, one object, one domain.

        The loser's own governed start refuses, and NOTHING CROSSED -- no `start`,
        no admission -- which is the property that makes a refused reservation
        reportable as a failed start rather than an unknown one.

        AND THE LOSER IS RECORDED AS THE ABSENCE IT IS, which is what review
        19:13:42Z directed after the previous claim measured the gap. The start
        provably never reached the engine, the adapter's own discovery then found no
        runtime carrying these labels, so the durable record says `destroyed` with no
        identity rather than `uncertain` -- the value reserved for a state this
        manager cannot establish. The record is read back rather than inferred from
        the row.
        """
        self.attempt()
        domain = tokens.domain_of("workspace", self.pinned)
        inputs = self.authorized(BESIDE, offer_id="offer-2", work_id=OTHER_JOB)
        self.carried_over(BESIDE)
        self.assertEqual(self.pinned, self.pin(BESIDE, inputs),
                         "the later assignment's root IS the first one's object")
        beside = Counting("runtime-2")
        with self.assertRaises(ContractRefusal) as caught:
            request_runtime_start(self.store, beside, attempt_id=BESIDE,
                                  inputs=inputs, govern=self.governance())
        self.assertEqual(caught.exception.category, "refused")
        self.assertIn("is owned by token generation 1", caught.exception.message)
        self.assertEqual(beside.started, [], "the engine was never reached")
        self.assertEqual(beside.admissions, [])
        held = tokens.outstanding(self.store, domain)
        self.assertEqual([one["execution"] for one in held], [ATTEMPT])
        # THE DURABLE NON-SUBMISSION, in the row AND in the journalled record.
        loser = self.row_of(BESIDE)
        self.assertEqual(loser["execution_runtime"], "destroyed")
        self.assertIsNone(loser["runtime_id"])
        record = attempts.attempt_start_failure_of(self.store, BESIDE)
        self.assertEqual(record["execution_runtime"], "destroyed")
        self.assertIsNone(record["runtime_id"])
        self.assertIn("committed as 'not-submitted' and this attempt's "
                      "execution runtime is now 'destroyed'",
                      caught.exception.message,
                      "the operator-facing account names the fact, not a guess")
        # AND THE LANE IS STILL HELD HERE: the refusal is not the ending, and the
        # next case is what releases it.
        self.assertEqual(self.lanes(), [ATTEMPT, BESIDE])

    def test_a_real_later_execution_takes_generation_two(self):
        """GENERATION 1 THEN GENERATION 2, both by real governed starts.

        The first attempt's ending returns generation 1; the later attempt's own
        `request_runtime_start` over the carried-over object takes generation 2 in
        the SAME domain and reaches the engine once. This is the same-resource later
        execution review 18:46:09Z said my previous case did not perform: there the
        later execution was a copied dictionary and a direct reservation, and here it
        is a second authorized row whose start crossed the adapter seam.
        """
        self.retained_ready("discard-after-intake")
        domain = tokens.domain_of("workspace", self.pinned)
        inputs = self.authorized(BESIDE, offer_id="offer-2", work_id=OTHER_JOB)
        self.carried_over(BESIDE)
        self.assertEqual(
            self.pinned,
            workspaces.governed_resource_identity(self.store, BESIDE),
            "the later assignment's governed root resolves to the same object")
        self.pin(BESIDE, inputs)
        # GENERATION 1 IS RETURNED BY ITS OWN ENDING FIRST.
        self.ended()
        self.ending(tokens.workspace_governance())
        self.assertEqual(tokens.outstanding(self.store, domain), [])
        # AND GENERATION 2 IS TAKEN BY A REAL START.
        beside = Counting("runtime-2")
        request_runtime_start(self.store, beside, attempt_id=BESIDE,
                              inputs=inputs, govern=self.governance())
        self.assertEqual(len(beside.started), 1)
        self.assertEqual(len(beside.admissions), 1)
        self.assertEqual(self.row_of(BESIDE)["runtime_id"], "runtime-2")
        held = tokens.outstanding(self.store, domain)
        self.assertEqual([one["generation"] for one in held], [2])
        self.assertEqual(held[0]["execution"], BESIDE)
        self.assertEqual(tokens.token_of(self.store, domain, 2)["container"],
                         "runtime-2",
                         "generation 2 is bound to the container that crossed")

    def test_the_first_ENDING_REPLAYED_leaves_the_later_generation_alone(self):
        """THE STALE REPLAY, against a live generation 2 a real start took.

        The first attempt's ending is journalled, so running it again replays. It
        resolves the generation from its OWN execution and operation, so the replay
        finds the generation it already returned and touches generation 2 not at all.
        """
        self.retained_ready("discard-after-intake")
        domain = tokens.domain_of("workspace", self.pinned)
        inputs = self.authorized(BESIDE, offer_id="offer-2", work_id=OTHER_JOB)
        self.carried_over(BESIDE)
        self.pin(BESIDE, inputs)
        self.ended()
        self.ending(tokens.workspace_governance())
        request_runtime_start(self.store, Counting("runtime-2"),
                             attempt_id=BESIDE, inputs=inputs,
                             govern=self.governance())
        self.assertEqual(
            [one["generation"]
             for one in tokens.outstanding(self.store, domain)], [2])
        # THE REPLAY.
        again = self.ending(tokens.workspace_governance())
        self.assertEqual(again["cleanup"], "complete")
        held = tokens.outstanding(self.store, domain)
        self.assertEqual([one["generation"] for one in held], [2],
                         "a replayed ending released a live later generation")
        self.assertEqual(held[0]["execution"], BESIDE)

    def test_unrelated_progress_over_its_own_object_is_not_blocked(self):
        """UNRELATED PROGRESS, which is the other half of an exclusion being correct.

        A second real attempt over its OWN canonical allocation reaches the engine
        and takes generation 1 of its own domain while the first attempt still holds
        its own. An exclusion that stopped this would be a global lock wearing a
        resource token's name.
        """
        self.attempt()
        mine = tokens.domain_of("workspace", self.pinned)
        inputs = self.authorized(BESIDE, offer_id="offer-2", work_id=OTHER_JOB)
        theirs = tokens.domain_of("workspace", self.pin(BESIDE, inputs))
        self.assertNotEqual(mine, theirs,
                            "two canonical allocations are two objects")
        beside = Counting("runtime-2")
        request_runtime_start(self.store, beside, attempt_id=BESIDE,
                              inputs=inputs, govern=self.governance())
        self.assertEqual(len(beside.admissions), 1)
        self.assertEqual([one["generation"]
                          for one in tokens.outstanding(self.store, theirs)], [1])
        self.assertEqual([one["generation"]
                          for one in tokens.outstanding(self.store, mine)], [1])


    # -- the loser's bounded recovery -----------------------------------------

    def losing(self, beside=None):
        """One real contention loser, left by its own refused governed start."""
        self.attempt()
        inputs = self.authorized(BESIDE, offer_id="offer-2", work_id=OTHER_JOB)
        self.carried_over(BESIDE)
        self.pin(BESIDE, inputs)
        beside = Counting("runtime-2") if beside is None else beside
        with self.assertRaises(ContractRefusal) as caught:
            request_runtime_start(self.store, beside, attempt_id=BESIDE,
                                  inputs=inputs, govern=self.governance())
        self.refusal = caught.exception
        return beside

    def recovered(self, adapter=None):
        """The EXISTING bounded failure recovery, on the loser."""
        self.session.live_assignment = None
        adapter = Remover() if adapter is None else adapter
        return adapter, intake.authorize_failed_start_cleanup(
            self.store, self.port, adapter, attempt_id=BESIDE,
            retention_policy_digest=RETENTION)

    def test_the_loser_is_recovered_by_the_EXISTING_failed_start_ending(self):
        """THE RECOVERY REVIEW 19:13:42Z ASKED FOR, and no new ending for it.

        `authorize_failed_start_cleanup` is authorized by this manager's own durable
        start-failure record, which is exactly what a refused reservation leaves. It
        refused before this claim for want of an attached runtime -- correctly, for
        the state that refusal NAMES, which is "no identity and no proof" -- and a
        proved non-launch is the other state: no identity BECAUSE nothing was created.

        NOTHING CROSSES, and that is asserted rather than arranged: the double holds
        the destroy verb the boundary requires and is never called, because there is
        no container to remove. Both roots are still normalized under this manager's
        custody, because those receipts are what authorize the removal.
        """
        self.losing()
        domain = tokens.domain_of("workspace", self.pinned)
        adapter, answer = self.recovered()
        self.assertEqual(answer["cleanup"], "retained")
        self.assertEqual(answer["state"], "absent")
        self.assertEqual(adapter.removed, [],
                         "nothing was destroyed, because nothing was created")
        self.assertEqual(adapter.normalized,
                         [(BESIDE, "result"), (BESIDE, "workspace")])
        # THE LANE IS GIVEN BACK, which is what makes the Work usable again.
        self.assertEqual(self.lanes(), [ATTEMPT])
        # AND THE WINNER IS UNTOUCHED BY ANY OF IT.
        held = tokens.outstanding(self.store, domain)
        self.assertEqual([one["execution"] for one in held], [ATTEMPT])

    def test_a_fresh_attempt_for_that_WORK_then_proceeds(self):
        """FRESH-ATTEMPT RECOVERY, the whole point of releasing the lane.

        A real third attempt over the loser's Work, authorized through the same
        production path and started over its own canonical allocation, reaches the
        engine. Before the recovery it could not: `_no_predecessor_holds` refuses a
        successor while any other attempt holds a lane over that Work.
        """
        self.losing()
        self.recovered()
        fresh = "attempt-fresh"
        inputs = self.authorized(fresh, offer_id="offer-3", work_id=OTHER_JOB)
        self.pin(fresh, inputs)
        adapter = Counting("runtime-3")
        request_runtime_start(self.store, adapter, attempt_id=fresh,
                              inputs=inputs, govern=self.governance())
        self.assertEqual(len(adapter.started), 1)
        self.assertEqual(self.row_of(fresh)["runtime_id"], "runtime-3")
        self.assertEqual(self.lanes(), [ATTEMPT, fresh])

    def test_an_UNKNOWN_discovery_still_holds_and_releases_nothing(self):
        """THE SAFETY HALF: no answer from the engine is not a proof of absence.

        The adapter cannot be asked -- its listing raises -- so the identification
        has no plan, the settlement records `uncertain`, and the recovery ending
        REFUSES `runtime-observation/quiescence-unknown`. The lane stays held, which
        is the correct cost of not knowing, and no positive fact is invented from a
        failure to look.
        """
        self.losing(Discovering(failure=RuntimeError("the engine is unreachable")))
        loser = self.row_of(BESIDE)
        self.assertEqual(loser["execution_runtime"], "uncertain")
        self.session.live_assignment = None
        with self.assertRaises(ContractRefusal) as caught:
            intake.authorize_failed_start_cleanup(
                self.store, self.port, Remover(), attempt_id=BESIDE,
                retention_policy_digest=RETENTION)
        self.assertEqual(caught.exception.code, "quiescence-unknown")
        self.assertEqual(self.lanes(), [ATTEMPT, BESIDE])

    def test_a_DISCOVERED_runtime_is_attached_rather_than_called_absent(self):
        """THE OTHER SAFETY HALF, in the review's own words: no current start call
        is not by itself proof no prior or delayed writer exists.

        The discovery finds a runtime already carrying this attempt's labels, so the
        non-submission narrows nothing: the identification ATTACHES that exact
        runtime, the axis is what the engine observed it to be, and the recovery
        ending then has an identity to remove and removes it.
        """
        self.losing(Discovering(listing=True))
        loser = self.row_of(BESIDE)
        self.assertEqual(loser["runtime_id"], "runtime-2",
                         "a discovered runtime is attached, not ignored")
        self.assertNotEqual(loser["execution_runtime"], "destroyed")
        adapter, answer = self.recovered()
        self.assertEqual(answer["state"], "absent")
        self.assertEqual([one["runtime_id"] for one in adapter.removed],
                         ["runtime-2"],
                         "the discovered container is the one destroyed")
        self.assertEqual(self.lanes(), [ATTEMPT])


    # -- the narrow non-launch boundary ---------------------------------------

    def test_an_UNCERTAIN_EXACT_RUNTIME_is_never_narrowed_to_absence(self):
        """THE DEFECT REVIEW 19:53:28Z FOUND IN MY OWN CORRECTION, as my case.

        `_identify` has TWO uncertain outputs and the first cut of
        `_proved_non_launch` converted both, on the decision word alone: an exact
        container the engine could not describe was reported as positive absence --
        the substitution this Work exists to remove, made by the function written to
        remove it.

        THE EVIDENCE IS NOW TYPED AND IS ASSERTED AS A MEMBER, not read out of the
        prose: `known_identity` carries the runtime the uncertainty is ABOUT, and is
        `None` only on the branch where there was no identity to ask about.
        """
        self.retained_ready("discard-after-intake")

        class Unknowable:
            """The engine answers about this exact runtime and cannot say what it is."""

            def list(self, operands):
                return []

            def observe(self, runtime_id):
                return {"runtime_id": runtime_id, "state": "uncertain",
                        "why": "the engine cannot establish this container's state"}

        plan = attempts._identify(self.store, Unknowable(), ATTEMPT)
        self.assertEqual(plan["decision"], "uncertain")
        self.assertEqual(plan["known_identity"], "runtime-1",
                         "the uncertainty names the runtime it is about")
        narrowed = attempts._proved_non_launch(
            plan, store=self.store, attempt_id=ATTEMPT,
            operation=attempts._start_operation_id(self.row_of(ATTEMPT)))
        self.assertEqual(narrowed["decision"], "uncertain",
                         "an uncertain exact runtime is not a proved non-launch")
        self.assertIs(narrowed, plan, "the plan is passed through untouched")

    def test_the_NARROWING_IS_FAIL_CLOSED_without_evidence_to_revalidate(self):
        """A plan alone cannot establish a non-launch.

        The typed member says the engine found no identity; it does not say the ROW
        still names none. So the revalidation operands are required, and a caller
        that supplies none narrows nothing -- which is also why the reviewer's own
        probe may keep calling this with a plan by itself.
        """
        plan = {"decision": "uncertain", "runtimes": None,
                "known_identity": None, "why": "the adapter reports no runtime"}
        self.assertIs(attempts._proved_non_launch(plan), plan)
        # AND A PLAN FROM ANY OTHER PATH, which has not said what this needs.
        silent = {"decision": "uncertain", "runtimes": None, "why": "no member"}
        self.assertIs(attempts._proved_non_launch(
            silent, store=self.store, attempt_id=ATTEMPT,
            operation="runtime.start:whatever"), silent)

    def test_an_ATTACHMENT_during_the_identification_prevents_the_absence(self):
        """THE RACE AT THE REFUSAL BOUNDARY, with a real writer.

        The losing start's identification asks the adapter for a listing; while it
        does, `reconcile_runtime` attaches a runtime to that same attempt. The empty
        listing this call receives is therefore true and stale, and the row is what
        catches it: no absence is recorded, the durable ending is `uncertain`, and
        the recovery ending then refuses -- so the lane stays held, which is the
        correct cost of another writer existing.
        """
        self.attempt()
        inputs = self.authorized(BESIDE, offer_id="offer-2", work_id=OTHER_JOB)
        self.carried_over(BESIDE)
        self.pin(BESIDE, inputs)
        racing = Attaching(self.store, BESIDE)
        with self.assertRaises(ContractRefusal):
            request_runtime_start(self.store, racing, attempt_id=BESIDE,
                                  inputs=inputs, govern=self.governance())
        self.assertEqual(racing.attached, ["runtime-9"],
                         "the attachment really landed inside the window")
        loser = self.row_of(BESIDE)
        self.assertEqual(loser["runtime_id"], "runtime-9")
        self.assertNotEqual(loser["execution_runtime"], "destroyed",
                            "no absence is recorded over another writer's act")
        self.session.live_assignment = None
        with self.assertRaises(ContractRefusal) as caught:
            intake.authorize_failed_start_cleanup(
                self.store, self.port, Remover(), attempt_id=BESIDE,
                retention_policy_digest=RETENTION)
        self.assertEqual(caught.exception.code, "quiescence-unknown")
        self.assertEqual(self.lanes(), [ATTEMPT, BESIDE])

    def test_the_COMMIT_takes_the_same_three_READS_again(self):
        """AND THE WRITE ITSELF REVALIDATES, because the narrowing proves one instant.

        Driven at `_reconciled`, which is where the settlement applies a plan inside
        its own transaction: handed a non-submission plan for an attempt whose row
        now names a runtime, it records `uncertain` rather than the absence the plan
        asked for.

        WHAT THIS DOES NOT ESTABLISH, stated rather than implied: a same-connection
        interleave cannot commit anything inside that transaction at all, so the
        window this guard defends is a SEPARATE connection's, and a two-process
        proof is not part of this case. What is measured is that the guard reads the
        row at commit and downgrades on it.
        """
        self.retained_ready("discard-after-intake")
        row = self.row_of(ATTEMPT)
        self.assertEqual(row["runtime_id"], "runtime-1")
        answer = attempts._reconciled(
            self.store, ATTEMPT,
            {"decision": "not-submitted", "runtimes": None,
             "operation": attempts._start_operation_id(row),
             "why": "no start request crossed the adapter under this operation"})
        self.assertEqual(answer["decision"], "uncertain")
        self.assertIn("another writer", answer["why"])
        self.assertEqual(self.row_of(ATTEMPT)["execution_runtime"], "uncertain")


class TheGENERATIONSEQUENCE(TheGovernedStartAndItsOwnEnding):
    """GENERATIONS 1, 2 AND 3 over ONE durable object, each by a real row.

    The original assignment (275774) asked for generations 1/2/3 as a connected
    sequence, and the abandonment is what ENDS generation 2 here -- proving them apart
    would have left the sequence resting on a reservation released by hand.

    AND THE LABEL IS THE MANAGER'S FOURTH ENDING, NOT THE TOOL'S. Review 20:48:20Z
    corrected me: `abandoned` below calls `intake.abandon_attempt` directly and never
    `tools/single_worker.py`, so nothing here is evidence about the tool. The
    full-tool claim is proved in `test_tool_abandonment.py`, which drives the real
    composition's own `operations.abandon_attempt`.

      * generation 1: attempt-1's governed `request_runtime_start`, returned by its
        real `intake.authorize_cleanup`;
      * generation 2: a second authorized row's governed start over the SAME object,
        returned by the real `intake.abandon_attempt` -- the fourth ending, whose
        `destroy_abandoned` crossing is the combined stop and remove and whose
        observation owns positive absence;
      * generation 3: a third authorized row's governed start over that same object.

    ONE DOMAIN THROUGHOUT, asserted rather than assumed: the object is carried from
    each assignment's position to the next by rename, so the inode is provably the
    same one and the three generations are three permissions over one resource rather
    than three resources that happened to be counted.
    """

    THIRD = "attempt-third"
    THIRD_JOB = "43c55d4b-W1441"
    REASON = "the supervised worker conversation was lost"

    class Abandoner(Remover):
        """The cleanup double plus the abandonment's own force-removal verb.

        `abandon_attempt` calls ONLY `destroy_abandoned`: a worker that never
        answered has no receipt to authorize an ordinary destroy, which is the whole
        reason that ending exists. The double records the command so the case asserts
        what crossed.
        """

        def __init__(self, *arguments, **operands):
            super().__init__(*arguments, **operands)
            self.abandoned_with = []

        def destroy_abandoned(self, command):
            self.abandoned_with.append(dict(command))
            return {"runtime_id": command["runtime_id"], "state": "absent",
                    "why": "the engine answered that this exact identity does "
                           "not exist",
                    "credentials": {"lifecycle_state": "not-delivered"},
                    "launch": {"lifecycle_state": "not-delivered"}}

    def carried(self, source, target):
        """The object moved from one assignment's position to the next.

        The same act `carried_over` performs, parameterized by source -- the local
        composition review 19:13:42Z authorized instead of the shared fixture's
        `ATTEMPT` constants.
        """
        homes = [os.path.dirname(self.workspace_of(one))
                 for one in (source, target)]
        modes = [os.stat(one).st_mode & 0o7777 for one in homes]
        for one in homes:
            os.chmod(one, 0o700)
        place = self.workspace_of(target)
        try:
            os.rename(place, place + ".own")
            os.rename(self.workspace_of(source), place)
        finally:
            for one, mode in zip(homes, modes):
                os.chmod(one, mode)

    def live(self, assignment_id):
        """The authority's live assignment and fence answer FOR THIS ATTEMPT.

        The shared fake composes its default from the first offer, and each attempt
        here is fixed to its own Work -- so an answer left at the default fences
        somebody else's assignment and the port refuses before the ending is reached.
        """
        row = self.row_of(assignment_id)
        expect = manager_documents.assignment(
            work_ref=manager_documents.work_ref(
                authority_uuid=row["authority_uuid"], work_id=row["work_id"]),
            participant=row["assignment_participant"],
            generation=row["assignment_generation"])
        self.session.live_assignment = dict(expect)
        self.session.fence_answer = {
            "cause": "cancelled", "assignment": dict(expect), "phase": "block",
            "gate": f"runtime-quiescence:{expect['generation']}",
            "fenced": True}
        self.session.discharge_answer = {
            "gate": f"runtime-quiescence:{expect['generation']}",
            "kind": "runtime-absent", "phase": "queued"}
        return expect

    def abandoned(self, assignment_id, adapter=None):
        """The real fourth ending, governed."""
        self.live(assignment_id)
        adapter = self.Abandoner() if adapter is None else adapter
        return adapter, intake.abandon_attempt(
            self.store, self.port, adapter, attempt_id=assignment_id,
            reason=self.REASON, retention_policy_digest=RETENTION,
            govern=tokens.workspace_governance())

    def sequence(self):
        """Generations 1 and 2, and the second row still holding generation 2."""
        self.retained_ready("discard-after-intake")
        domain = tokens.domain_of("workspace", self.pinned)
        inputs = self.authorized(BESIDE, offer_id="offer-2", work_id=OTHER_JOB)
        self.carried(ATTEMPT, BESIDE)
        self.assertEqual(
            self.pinned,
            workspaces.governed_resource_identity(self.store, BESIDE),
            "the second assignment's root IS the first one's object")
        self.pin(BESIDE, inputs)
        # GENERATION 1 IS RETURNED BY ITS OWN REAL ENDING.
        self.ended()
        self.ending(tokens.workspace_governance())
        self.assertEqual(tokens.outstanding(self.store, domain), [])
        # AND GENERATION 2 IS TAKEN BY A REAL GOVERNED START.
        beside = Counting("runtime-2")
        request_runtime_start(self.store, beside, attempt_id=BESIDE,
                              inputs=inputs, govern=self.governance())
        self.assertEqual([one["generation"]
                          for one in tokens.outstanding(self.store, domain)], [2])
        return domain

    def test_generations_one_two_three_over_one_durable_object(self):
        domain = self.sequence()
        # GENERATION 2 IS RETURNED BY THE MANAGER'S FOURTH ENDING.
        adapter, answer = self.abandoned(BESIDE)
        self.assertEqual([one["runtime_id"] for one in adapter.abandoned_with],
                         ["runtime-2"],
                         "only `destroy_abandoned` crosses, on the exact runtime")
        self.assertEqual(adapter.removed, [],
                         "no receipt-bound destroy is performed for an abandonment")
        self.assertEqual(answer["cleanup"]["cleanup"], "retained")
        self.assertEqual(answer["cleanup"]["state"], "absent")
        self.assertEqual(sorted(answer["cleanup"]["directory_custody"]),
                         ["result", "workspace"],
                         "both governed roots are normalized under this manager")
        self.assertEqual(tokens.outstanding(self.store, domain), [],
                         "the abandonment returned what the start reserved")
        self.assertEqual(self.lanes(), [],
                         "and the lane comes back with it")
        # GENERATION 3, by a third real row over that same durable object.
        inputs = self.authorized(self.THIRD, offer_id="offer-3",
                                 work_id=self.THIRD_JOB)
        self.carried(BESIDE, self.THIRD)
        self.assertEqual(
            self.pinned,
            workspaces.governed_resource_identity(self.store, self.THIRD),
            "still the same object, three assignments later")
        self.pin(self.THIRD, inputs)
        third = Counting("runtime-3")
        request_runtime_start(self.store, third, attempt_id=self.THIRD,
                              inputs=inputs, govern=self.governance())
        held = tokens.outstanding(self.store, domain)
        self.assertEqual([one["generation"] for one in held], [3])
        self.assertEqual(held[0]["execution"], self.THIRD)
        self.assertEqual(len(third.admissions), 1)
        # AND THE WHOLE SEQUENCE, read back from the journal.
        self.assertEqual(
            [(one, tokens.token_of(self.store, domain, one)["execution"],
              bool(tokens.token_of(self.store, domain, one)["returned"]))
             for one in (1, 2, 3)],
            [(1, ATTEMPT, True), (2, BESIDE, True), (3, self.THIRD, False)])
        self.assertEqual(tokens.token_of(self.store, domain, 3)["container"],
                         "runtime-3")

    def test_a_stale_abandonment_replay_leaves_generation_three_alone(self):
        """The terminal ending is journalled, so it replays -- and a replay arriving
        after a later execution has taken the resource must touch nothing."""
        domain = self.sequence()
        self.abandoned(BESIDE)
        inputs = self.authorized(self.THIRD, offer_id="offer-3",
                                 work_id=self.THIRD_JOB)
        self.carried(BESIDE, self.THIRD)
        self.pin(self.THIRD, inputs)
        request_runtime_start(self.store, Counting("runtime-3"),
                             attempt_id=self.THIRD, inputs=inputs,
                             govern=self.governance())
        self.assertEqual([one["generation"]
                          for one in tokens.outstanding(self.store, domain)], [3])
        # THE STALE TERMINAL REPLAY.
        self.abandoned(BESIDE)
        held = tokens.outstanding(self.store, domain)
        self.assertEqual([one["generation"] for one in held], [3],
                         "a replayed abandonment released a live generation")
        self.assertEqual(held[0]["execution"], self.THIRD)


if __name__ == "__main__":
    unittest.main()
