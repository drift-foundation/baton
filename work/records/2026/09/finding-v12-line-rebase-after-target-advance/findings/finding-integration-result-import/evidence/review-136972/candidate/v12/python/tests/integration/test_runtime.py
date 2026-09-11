"""W101490 -- the generic integration runtime boundary.

WHAT THESE CASES ARE ABOUT. What a fenced integration runtime is composed
FROM, and what it may not be composed without. They are not about admitting a
candidate, mutating a target, recording an Authority receipt or recovering an
interrupted integration: those are the sibling leaves of the same parent, and
nothing here calls a coordinator settlement verb.

THE CASE THE ACCEPTANCE BOUNDARY NAMES is `WritableAccessNeedsTheLiveGrant`.
A composed assignment cannot exist without the coordinator's currently live
grant read at the moment of composition, and it cannot exist behind a prior
runtime that was not observed to have stopped.
"""

import json
import os
import stat
import unittest

from baton_v12.contracts import ContractRefusal, digest
from baton_v12.integration import (activate_target, block_target, enqueue,
                                   entries_of, grant_lease, refuse_entry,
                                   release_lease, settle_integrated)
from baton_v12.integration import runtime
from baton_v12.worker_manager import attempts, workspaces

from .fixtures import (PROFILE_KIND, TARGET, CoordinatorCase, eligibility,
                       target)

INSTRUCTIONS = "sha256:" + "7" * 64
PARTICIPANT = "baton.merge"


def _tree(module):
    import ast
    import inspect
    return ast.parse(inspect.getsource(module))


def called_names(module):
    """Every name this module actually CALLS, whatever its prose says."""
    import ast
    names = set()
    for node in ast.walk(_tree(module)):
        if isinstance(node, ast.Call):
            called = node.func
            if isinstance(called, ast.Name):
                names.add(called.id)
            elif isinstance(called, ast.Attribute):
                names.add(called.attr)
    return names


def imported_names(module):
    """Every module this one reaches, whatever its prose mentions."""
    import ast
    names = set()
    for node in ast.walk(_tree(module)):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            names.add(node.module or "")
            names.update(alias.name for alias in node.names)
    return names


def profile(**changed):
    operands = {"profile_kind": PROFILE_KIND, "profile_version": 1,
                "integrator_participant": PARTICIPANT,
                "instructions_digest": INSTRUCTIONS}
    operands.update(changed)
    return runtime.integration_profile(**operands)


def _manager_of(case):
    """The Worker Manager control store this boundary reads runtime state
    from. It is not a fixture convenience: the review's [P0] is that a
    caller-authored dictionary is not a runtime observation, so the answer has
    to come from the manager's own durable row."""
    from baton_v12.worker_manager import ControlStore
    if getattr(case, "_manager", None) is None:
        case._manager = ControlStore.open(
            os.path.join(case.root, "control.sqlite3"), incarnation="i-1",
            clock=lambda: "2026-09-06T00:00:00.000Z")
        case.addCleanup(case._manager.close)
    return case._manager


def _recorded_attempt(case, attempt_id, execution_runtime=None):
    """One durable attempt in the manager, through the manager's own verbs.

    `record_attempt` and `observe` rather than SQL, because what this boundary
    reads is the manager's durable row and a row this suite hand-wrote would be
    testing the fixture. `observe` also decides the transition inside its own
    write, so a state this suite asks for is one the manager's frozen table
    actually permits.
    """
    manager = _manager_of(case)
    attempts.record_attempt(manager, attempt_id=attempt_id,
                            adapter_name="adapter",
                            adapter_digest="sha256:" + "a" * 64,
                            profile_digest="sha256:" + "b" * 64)
    if execution_runtime is not None:
        _observed(case, attempt_id, execution_runtime)
    return attempt_id


def _observed(case, attempt_id, execution_runtime):
    """Walk the manager's own table to the state this case needs.

    `stopping` does not follow `not-started`, and asking for it directly is
    asking the manager to accept a transition it does not have. The shortest
    legal path is derived from `TRANSITIONS` rather than written down here, so
    a table change moves this fixture with it instead of stranding it.
    """
    manager = _manager_of(case)
    if execution_runtime == "not-started":
        # Where `record_attempt` already left it; there is no transition INTO
        # the state an attempt starts in.
        return
    moves = attempts.TRANSITIONS["execution_runtime"]
    frontier, seen = [("not-started", [])], {"not-started"}
    route = None
    while frontier and route is None:
        state, path = frontier.pop(0)
        for step in moves[state]:
            if step in seen:
                continue
            if step == execution_runtime:
                route = path + [step]
                break
            seen.add(step)
            frontier.append((step, path + [step]))
    if route is None:
        raise AssertionError(execution_runtime)
    for step in route:
        attempts.observe(manager, attempt_id=attempt_id,
                         axis="execution_runtime", value=step)


def _group_of(case):
    """The deployment's configured workspace group, minted the ONE way it can
    be.

    `WorkspaceGroup` refuses to be constructed: only the manager's own record
    of what the deployment configured mints one, because a type any caller can
    build is a group any caller chose. So this fixture opens a control store
    and configures it, exactly as `tests/manager/test_exchange` does -- the
    coupling is the contract's, not this suite's.
    """
    from baton_v12.worker_manager import (configure_workspace_group,
                                          configured_workspace_group)
    control = _manager_of(case)
    configure_workspace_group(control, os.getgid())
    return configured_workspace_group(control)


class RuntimeCase(CoordinatorCase):
    """One target, one queued entry, one live grant over it."""

    def setUp(self):
        super().setUp()
        self.coordinator = self.store()
        activate_target(self.coordinator, target())
        enqueue(self.coordinator, canonical_target_id=TARGET,
                entry_id="entry-1", eligibility=eligibility())
        granted = grant_lease(self.coordinator, canonical_target_id=TARGET,
                              entry_id="entry-1",
                              lease_id="lease-1",
                              integrator_participant=PARTICIPANT,
                              attempt_id="attempt-1")
        self.fence = granted["lease"]["fence"]
        self.manager = _manager_of(self)
        self.group = _group_of(self)
        _recorded_attempt(self, "attempt-1")

    def compose(self, **changed):
        operands = {"profile": profile(), "canonical_target_id": TARGET,
                    "entry_id": "entry-1", "lease_id": "lease-1",
                    "fence": self.fence, "attempt_id": "attempt-1"}
        operands.update(changed)
        return runtime.compose_assignment(self.coordinator, self.manager,
                                          **operands)

    def result(self, assignment, **changed):
        answer = {"schema": runtime.RESULT_SCHEMA,
                  "attempt_id": assignment["attempt_id"],
                  "lease_id": assignment["lease_id"],
                  "canonical_target_id": assignment["canonical_target_id"],
                  "entry_id": assignment["entry_id"],
                  "fence": assignment["fence"],
                  "outcome": "integrated",
                  "detail": {"imported_paths": ["src/a.py"]}}
        answer.update(changed)
        return answer


class TheProfileIsWiringAndNotAPlan(unittest.TestCase):

    def refusal(self, action, *operands, **named):
        with self.assertRaises(ContractRefusal) as caught:
            action(*operands, **named)
        return caught.exception

    def test_a_profile_is_authored_over_its_own_members(self):
        self.assertEqual(sorted(profile()), sorted(runtime.PROFILE_MEMBERS))
        self.assertEqual(profile()["schema"], runtime.PROFILE_SCHEMA)

    def test_a_caller_supplies_values_and_never_a_document_shape(self):
        """`launch_document`'s rule, here for its reason: how a caller happened
        to build its dict must not reach a document this build then treats as
        its own."""
        self.assertNotIn("extra", profile())
        self.assertRaises(TypeError, runtime.integration_profile,
                          profile_kind="k", profile_version=1,
                          integrator_participant="p",
                          instructions_digest="d", extra="smuggled")

    def test_a_profile_version_counts_from_one(self):
        self.assertEqual(
            self.refusal(profile, profile_version=0).category, "integrity")
        self.assertEqual(
            self.refusal(profile, profile_version="1").category, "integrity")

    def test_a_result_contract_this_build_does_not_answer_is_refused(self):
        caught = self.refusal(profile, result_contract="something.else/1")
        self.assertIn("baton.v12.integration-result/1", caught.message)

    def test_a_persisted_profile_is_owned_where_it_is_read(self):
        """One document with one lock and two doors is the shape
        `boundaries.sealed` records having been caught twice."""
        wrong = dict(profile(), schema="baton.v12.integration-profile/99")
        self.assertEqual(
            self.refusal(runtime._owned_profile, wrong).category, "integrity")
        short = dict(profile())
        del short["instructions_digest"]
        self.assertEqual(
            self.refusal(runtime._owned_profile, short).category, "integrity")


class WritableAccessNeedsTheLiveGrant(RuntimeCase):
    """The acceptance clause: no composition without a currently live grant.

    A lease id with a fence is a replayable VALUE, which W71878's seam review
    settled and this composition does not re-open: the grant is read from the
    coordinator inside the same call that composes, and there is no path here
    that reaches a document without it.
    """

    def test_a_held_grant_composes_a_writable_assignment(self):
        composed = self.compose()
        self.assertEqual(composed["schema"], runtime.ASSIGNMENT_SCHEMA)
        self.assertEqual(composed["target_access"], "writable")
        self.assertEqual(sorted(composed), sorted(runtime.ASSIGNMENT_MEMBERS))
        self.assertEqual(composed["canonical_target_id"], TARGET)
        self.assertEqual((composed["lease_id"], composed["fence"],
                          composed["entry_id"]),
                         ("lease-1", self.fence, "entry-1"))

    def test_the_one_access_composed_is_the_one_that_can_do_the_work(self):
        """A one-member vocabulary, because the alternatives are refusals. A
        runtime that cannot write the target cannot integrate, and composing
        one anyway would put a container in front of a target for no reason."""
        self.assertEqual(runtime.ACCESS_KINDS, ("writable",))

    def test_the_stored_grant_fills_the_document_and_not_the_caller(self):
        """Two values are the same only when the proof passed, and using the
        store's is what makes that visible rather than assumed."""
        held = self.coordinator._connection.execute(
            "SELECT entry_id, fence FROM leases WHERE lease_id = 'lease-1'"
        ).fetchone()
        composed = self.compose()
        self.assertEqual(composed["entry_id"], held["entry_id"])
        self.assertEqual(composed["fence"], held["fence"])

    def test_a_stale_fence_composes_nothing(self):
        caught = self.refusal(self.compose, fence=self.fence + 1)
        self.assertEqual((caught.category, caught.code), ("policy", "denied"))

    def test_another_entry_under_this_lease_composes_nothing(self):
        enqueue(self.coordinator, canonical_target_id=TARGET,
                entry_id="entry-2", eligibility=eligibility(
                    checkpoint_id="checkpoint-2"))
        self.assertEqual(
            self.refusal(self.compose, entry_id="entry-2").code, "denied")

    def test_a_lease_that_never_existed_composes_nothing(self):
        self.assertEqual(self.refusal(self.compose, lease_id="lease-9").code,
                         "denied")

    def test_an_ended_grant_composes_nothing(self):
        settle_integrated(self.coordinator, lease_id="lease-1",
                          canonical_target_id=TARGET, fence=self.fence,
                          entry_id="entry-1",
                          settlement={"imported_paths": ["src/a.py"],
                                      "verification": {"final": "checked"}})
        release_lease(self.coordinator, lease_id="lease-1",
                      canonical_target_id=TARGET, entry_id="entry-1",
                      fence=self.fence, ending={"outcome": "integrated"})
        self.assertEqual(self.refusal(self.compose).code, "denied")

    def test_a_blocked_target_composes_nothing_even_for_its_holder(self):
        block_target(self.coordinator, canonical_target_id=TARGET,
                     entry_id="entry-1", lease_id="lease-1", fence=self.fence,
                     reason="integrity", detail={"observed": "ambiguous"})
        self.assertEqual(self.refusal(self.compose).code, "denied")

    def test_the_holder_of_the_grant_is_the_participant_that_runs_under_it(self):
        caught = self.refusal(
            self.compose, profile=profile(integrator_participant="somebody.else"))
        self.assertIn("the participant that holds the grant", caught.message)

    def test_a_refused_composition_starts_nothing_and_moves_nothing(self):
        before = [tuple(row) for row in self.coordinator._connection.execute(
            "SELECT * FROM leases")]
        self.refusal(self.compose, fence=self.fence + 1)
        self.assertEqual(
            [tuple(row) for row in self.coordinator._connection.execute(
                "SELECT * FROM leases")], before)


class ThePriorRuntimeIsPROVEDUnableToMutate(RuntimeCase):
    """Review [P0]: a caller-authored dictionary is not a runtime observation.

    The record was right that agent quiescence is not runtime quiescence --
    `sessions.satisfies_runtime_quiescence_gate` answers false by construction.
    The reviewer was right that moving the same unsupported claim into a
    `prior=` operand did not make it a runtime fact: a witness naming an
    unrelated attempt as `destroyed` authorized a writer, and omitting the
    operand authorized one unconditionally.

    So there is no operand. WHICH attempt held the previous grant is the
    coordinator's answer, out of the same relationship as the live grant, and
    WHAT its runtime is doing is the manager's durable row. Neither is
    reachable from a caller -- and neither is reachable from this suite either,
    which is why every case below builds a whole scenario instead of editing
    one: repointing a lease at another attempt is refused by the coordinator's
    own journal proof, exactly as it should be.
    """

    def scenario(self, state, name=None):
        """One target whose FIRST grant went to a runtime now in `state`, and
        whose second grant is the one being composed."""
        holder = f"attempt-holder-{state}"
        follower = f"attempt-follower-{state}"
        _recorded_attempt(self, holder, state)
        _recorded_attempt(self, follower)
        coordinator = self.store(path=f"{self.path}.{name or state}")
        activate_target(coordinator, target())
        enqueue(coordinator, canonical_target_id=TARGET, entry_id="entry-1",
                eligibility=eligibility())
        first = grant_lease(coordinator, canonical_target_id=TARGET,
                            entry_id="entry-1",
                            lease_id="lease-1",
                            integrator_participant=PARTICIPANT,
                            attempt_id=holder)
        refuse_entry(coordinator, canonical_target_id=TARGET,
                     entry_id="entry-1",
                     settlement={"reason": "scope", "detail": {}},
                     lease_id="lease-1", fence=first["lease"]["fence"])
        enqueue(coordinator, canonical_target_id=TARGET, entry_id="entry-2",
                eligibility=eligibility(checkpoint_id="checkpoint-2"))
        second = grant_lease(coordinator, canonical_target_id=TARGET,
                             entry_id="entry-2",
                             lease_id="lease-2",
                             integrator_participant=PARTICIPANT,
                             attempt_id=follower)
        fence = second["lease"]["fence"]

        def compose():
            return runtime.compose_assignment(
                coordinator, self.manager, profile=profile(),
                canonical_target_id=TARGET, entry_id="entry-2",
                lease_id="lease-2", fence=fence, attempt_id=follower)

        return coordinator, holder, compose

    def test_the_vocabulary_is_the_manager_s_own(self):
        self.assertEqual(
            set(runtime.QUIESCENT_STATES) | set(runtime.MUTATING_STATES),
            set(attempts.TRANSITIONS["execution_runtime"]))

    def test_a_predecessor_observed_stopped_or_absent_lets_a_writer_start(self):
        for state in runtime.QUIESCENT_STATES:
            with self.subTest(execution_runtime=state):
                _, _, compose = self.scenario(state)
                self.assertEqual(compose()["target_access"], "writable")

    def test_no_other_state_lets_a_writer_start(self):
        for state in runtime.MUTATING_STATES:
            with self.subTest(execution_runtime=state):
                _, _, compose = self.scenario(state)
                caught = self.refusal(compose)
                self.assertEqual(caught.code, "denied", state)
                self.assertIn("an unobserved runtime is not an absent one",
                              caught.message)

    def test_uncertain_is_refused_by_name(self):
        """The one the asymmetry is about: the manager's own table refuses to
        let `uncertain` become `destroyed`, because destruction is a fact about
        the world and inferring it from a failure to look reports a cleaned-up
        runtime that is still executing somebody's code."""
        _, _, compose = self.scenario("uncertain")
        self.assertIn("'uncertain'", self.refusal(compose).message)

    def test_the_refusal_names_the_predecessor_the_coordinator_chose(self):
        """A caller never supplies it, so the refusal has to say which runtime
        it is about."""
        _, holder, compose = self.scenario("running")
        self.assertIn(holder, self.refusal(compose).message)

    def test_there_is_no_prior_operand_to_supply(self):
        _, _, _ = self.scenario("running", name="no-operand")
        self.assertRaises(TypeError, runtime.compose_assignment,
                          self.coordinator, self.manager, profile=profile(),
                          canonical_target_id=TARGET, entry_id="entry-1",
                          lease_id="lease-1", fence=self.fence,
                          attempt_id="attempt-1", prior={"anything": True})

    def test_an_unrelated_quiescent_attempt_authorizes_nothing(self):
        """The reproduction the review drove: a quiet attempt somewhere else is
        not this target's predecessor, and there is no door to offer it at."""
        _recorded_attempt(self, "attempt-elsewhere", "destroyed")
        _, _, compose = self.scenario("running", name="unrelated")
        self.assertEqual(self.refusal(compose).code, "denied")

    def test_a_predecessor_the_manager_cannot_account_for_is_refused(self):
        """Absence of a record is not absence of a runtime."""
        _, holder, compose = self.scenario("destroyed", name="forgotten")
        self.manager._connection.execute(
            "DELETE FROM attempts WHERE runtime_attempt_id = ?", (holder,))
        caught = self.refusal(compose)
        self.assertIn("absence of a record is not absence of a runtime",
                      caught.message)

    def test_a_first_grant_has_no_predecessor_to_prove(self):
        """Durable state again rather than an assertion: the coordinator's own
        lease history says this target had never been granted before."""
        self.assertEqual(self.compose()["target_access"], "writable")

    def test_a_reopened_store_gives_the_same_durable_answer(self):
        """It was never in a process's memory, so a restart reads the same
        thing."""
        coordinator, _, compose = self.scenario("running", name="restart")
        self.assertEqual(self.refusal(compose).code, "denied")
        again = self.store(incarnation="coordinator-2",
                           path=f"{self.path}.restart")
        self.assertEqual(len(entries_of(again, TARGET)), 2)
        self.assertEqual(self.refusal(compose).code, "denied")


class TheRuntimeSCLAIMIsNotASettlement(RuntimeCase):

    def setUp(self):
        super().setUp()
        self.assignment = self.compose()

    def test_a_result_is_adopted_in_the_coordinator_s_own_vocabulary(self):
        for outcome in runtime.RESULT_OUTCOMES:
            with self.subTest(outcome=outcome):
                answer = runtime.observed_result(
                    self.assignment, self.result(self.assignment,
                                                 outcome=outcome))
                self.assertEqual(answer["outcome"], outcome)

    def test_the_outcomes_are_the_entry_states_a_settlement_uses(self):
        from baton_v12.integration import schema as coordinator
        self.assertEqual(set(runtime.RESULT_OUTCOMES),
                         set(coordinator.ENTRY_STATES)
                         - {"queued", "leased"})

    def test_adopting_a_result_settles_nothing(self):
        runtime.observed_result(self.assignment,
                                self.result(self.assignment))
        self.assertEqual(
            self.coordinator._connection.execute(
                "SELECT state FROM entries WHERE entry_id = 'entry-1'"
            ).fetchone()[0], "leased")

    def test_a_result_answers_the_integration_it_was_composed_for(self):
        for name, value in (("attempt_id", "attempt-9"),
                            ("lease_id", "lease-9"),
                            ("canonical_target_id", "target:other"),
                            ("entry_id", "entry-9"),
                            ("fence", self.fence + 1)):
            with self.subTest(member=name):
                caught = self.refusal(
                    runtime.observed_result, self.assignment,
                    self.result(self.assignment, **{name: value}))
                self.assertEqual(caught.code, "denied")

    def test_an_outcome_this_build_does_not_own_is_refused(self):
        caught = self.refusal(runtime.observed_result, self.assignment,
                              self.result(self.assignment,
                                          outcome="mostly-integrated"))
        self.assertEqual(caught.category, "integrity")

    def test_a_foreign_or_short_result_is_refused(self):
        wrong = self.result(self.assignment, schema="something.else/1")
        self.assertEqual(
            self.refusal(runtime.observed_result, self.assignment,
                         wrong).category, "integrity")
        short = self.result(self.assignment)
        del short["detail"]
        self.assertEqual(
            self.refusal(runtime.observed_result, self.assignment,
                         short).category, "integrity")

    def test_the_assignment_a_result_answers_is_owned_too(self):
        forged = dict(self.assignment, target_access="nonsense")
        self.assertEqual(
            self.refusal(runtime.observed_result, forged,
                         self.result(self.assignment)).category, "integrity")

    def test_an_assignment_digest_is_taken_over_an_owned_document(self):
        self.assertEqual(runtime.assignment_digest(self.assignment),
                         digest(self.assignment))
        self.assertEqual(
            self.refusal(runtime.assignment_digest,
                         dict(self.assignment, fence=0)).category, "integrity")


class AnInterruptionProducesAHoldAndNothingElse(RuntimeCase):
    """The owner ruling of 2026-09-06: restart may observe and classify. It may
    not retry, accept, complete a receipt, clean up, release, discard output or
    reassign."""

    def test_a_hold_carries_exactly_what_block_target_takes(self):
        held = runtime.hold_account(reason="runtime-interrupted",
                                    observed="the manager restarted",
                                    detail={"attempt_id": "attempt-1"})
        self.assertEqual(sorted(held), sorted(runtime.HOLD_MEMBERS))
        block_target(self.coordinator, canonical_target_id=TARGET,
                     entry_id="entry-1", lease_id="lease-1", fence=self.fence,
                     reason=held["reason"], detail=held["detail"])
        blocked = self.coordinator._connection.execute(
            "SELECT blocked_reason FROM targets").fetchone()[0]
        self.assertEqual(blocked, "runtime-interrupted")

    def test_a_reason_this_build_does_not_own_is_refused(self):
        caught = self.refusal(runtime.hold_account, reason="probably-fine",
                              observed="a guess", detail={})
        self.assertEqual(caught.category, "integrity")

    def test_composing_a_hold_applies_nothing(self):
        runtime.hold_account(reason="runtime-ambiguous",
                             observed="two runtimes answered",
                             detail={"seen": 2})
        target = self.coordinator._connection.execute(
            "SELECT state FROM targets").fetchone()[0]
        self.assertEqual(target, "open")
        self.assertEqual(
            self.coordinator._connection.execute(
                "SELECT state FROM entries").fetchone()[0], "leased")

    def test_this_module_reaches_no_settlement_verb(self):
        """A gate rather than a promise: the leaf that decides which verb a
        claim earns is the fenced-integration one, and this module must not
        become it.

        THE CALLS, NOT THE PROSE. Commentary here names those verbs on purpose
        -- explaining which one a claim will earn is most of why this boundary
        exists -- so the gate reads what the module CALLS.
        """
        for verb in ("settle_integrated", "refuse_entry", "block_target",
                     "abandon_lease", "release_lease", "enqueue",
                     "grant_lease", "activate_target"):
            self.assertNotIn(verb, called_names(runtime), verb)


class TheIntegrationBoundaryIsVCSNeutral(unittest.TestCase):
    """The owner clarifications of 2026-09-06, as a gate over this module's own
    names.

    Core Baton owns serialized admission, the live fenced grant, exclusive
    target write access, quiescence and durable settlement; it does not parse or
    validate commits, refs, branches, trees, ancestry or merges, and v12
    requires no VCS-aware adapter. `source_profiles/` is the working shape of
    that separation and this is the same one: the generic contract here, the
    version-control plan outside it, and a gate rather than a paragraph.
    """

    VCS_NOUNS = frozenset((
        "commit", "commits", "ref", "refs", "branch", "branches", "tree",
        "trees", "blob", "blobs", "tag", "tags", "object", "objects",
        "checkout", "clone", "merge", "rebase", "ancestry", "transport",
        "sha1", "packfile", "worktree"))

    def vocabulary(self):
        names = set()
        for members in (runtime.PROFILE_MEMBERS, runtime.ASSIGNMENT_MEMBERS,
                        runtime.RESULT_MEMBERS, runtime.HOLD_MEMBERS,
                        runtime.OBSERVED_RUNTIME_MEMBERS):
            names.update(members)
        names.update(runtime.HOLD_REASONS)
        names.update(runtime.RESULT_OUTCOMES)
        names.update(runtime.ACCESS_KINDS)
        return names

    def test_no_boundary_name_is_a_version_control_noun(self):
        found = sorted(name for name in self.vocabulary()
                       if set(name.split("_")) & self.VCS_NOUNS)
        self.assertEqual(found, [],
                         "integration runtime vocabulary naming a version "
                         "control concept")

    def test_this_module_imports_no_version_control_package(self):
        """`source_profiles` is where a repository plan lives, and this
        boundary does not reach it.

        THE IMPORTS, NOT THE PROSE, for the same reason the name gate above
        reads identifiers: the module docstring names that package deliberately,
        because the separation it established is the shape this one follows.
        """
        for forbidden in ("source_profiles", "checkpoint_profiles"):
            self.assertNotIn(forbidden, imported_names(runtime), forbidden)


class TheDeliveryIsDurableAndManagerCustodied(RuntimeCase):
    """The acceptance clause about files: closed schemas, atomic publication,
    and a runtime's material read as untrusted input.

    WHY A FOURTH DELIVERY. `exchange.py` is the third -- after `inputs` and
    `workspace` -- and its two namespaces carry one attempt's OPERATION
    SEQUENCE, which an integration assignment is not one of; `inputs` is frozen
    before the runtime starts and closed over its own protocol pair; and
    anything under `workspace` is reachable through the runtime's own writable
    mount, so an assignment placed there could be replaced by the program it is
    addressed to. What is reused is the RULE --
    the same five-step publication, the same modes, the same no-follow bounded
    read, the same untrusted-versus-integrity split.
    """

    def setUp(self):
        super().setUp()
        self.assignment = self.compose()
        self.root = os.path.join(self.root, "launch")
        os.makedirs(self.root)
        self.delivery = runtime.materialize_delivery(
            self.root, attempt_id="attempt-1",
            workspace_group=_group_of(self))

    def result_bytes(self, document):
        place = os.path.join(self.delivery.result_root,
                             runtime.RESULT_DOCUMENT)
        with open(place, "wb") as writing:
            writing.write(document)

    def write_result(self, **changed):
        self.result_bytes(json.dumps(self.result(self.assignment, **changed),
                                     sort_keys=True).encode("utf-8"))

    # -- publication --------------------------------------------------------

    def test_the_namespaces_are_made_before_anything_is_published(self):
        self.assertTrue(os.path.isdir(self.delivery.assignment_root))
        self.assertTrue(os.path.isdir(self.delivery.result_root))
        self.assertEqual(
            stat.S_IMODE(os.stat(self.delivery.assignment_root).st_mode),
            runtime.ASSIGNMENT_DIR)

    def test_publishing_is_atomic_and_leaves_no_staging_name(self):
        answered = runtime.publish_assignment(self.delivery, self.assignment)
        self.assertTrue(answered["published"])
        self.assertEqual(sorted(os.listdir(self.delivery.assignment_root)),
                         [runtime.ASSIGNMENT_DOCUMENT])

    def test_republishing_the_same_assignment_replays(self):
        first = runtime.publish_assignment(self.delivery, self.assignment)
        again = runtime.publish_assignment(self.delivery, self.assignment)
        self.assertFalse(again["published"])
        self.assertEqual(again["assignment_digest"],
                         first["assignment_digest"])

    def test_a_different_assignment_under_one_attempt_is_refused(self):
        runtime.publish_assignment(self.delivery, self.assignment)
        other = dict(self.assignment, instructions_digest="sha256:other")
        caught = self.refusal(runtime.publish_assignment, self.delivery, other)
        self.assertEqual(caught.code, "denied")
        self.assertIn("one integration is assigned once", caught.message)

    def test_a_delivery_carries_the_attempt_its_assignment_names(self):
        elsewhere = runtime.materialize_delivery(
            os.path.join(self.root, "other"), attempt_id="attempt-9",
            workspace_group=_group_of(self))
        self.assertEqual(
            self.refusal(runtime.publish_assignment, elsewhere,
                         self.assignment).code, "denied")

    def test_paths_are_never_operands(self):
        """A caller holding two strings could point a runtime at a namespace
        this manager did not make."""
        self.assertEqual(
            self.refusal(runtime.publish_assignment,
                         self.delivery.assignment_root,
                         self.assignment).code, "denied")
        self.assertEqual(
            self.refusal(runtime.observed_delivery, self.delivery.root,
                         self.assignment).code, "denied")

    # -- observation --------------------------------------------------------

    def test_an_unassigned_delivery_says_so(self):
        self.assertEqual(
            runtime.observed_delivery(self.delivery, self.assignment)["state"],
            "not-assigned")

    def test_a_published_assignment_with_no_result_is_waiting(self):
        runtime.publish_assignment(self.delivery, self.assignment)
        seen = runtime.observed_delivery(self.delivery, self.assignment)
        self.assertEqual(seen["state"], "waiting")
        self.assertIsNone(seen["hold"])

    def test_waiting_is_not_rounded_to_a_hold(self):
        """An integration with no result yet may still be running, and only
        positive evidence about the runtime turns that into anything else."""
        runtime.publish_assignment(self.delivery, self.assignment)
        for _ in range(3):
            self.assertEqual(
                runtime.observed_delivery(self.delivery,
                                          self.assignment)["state"],
                "waiting")

    def test_a_sound_result_is_answered(self):
        runtime.publish_assignment(self.delivery, self.assignment)
        self.write_result(outcome="integrated")
        seen = runtime.observed_delivery(self.delivery, self.assignment)
        self.assertEqual(seen["state"], "answered")
        self.assertEqual(seen["result"]["outcome"], "integrated")
        self.assertIsNone(seen["hold"])

    def test_the_full_read_is_authoritative_and_repeatable(self):
        runtime.publish_assignment(self.delivery, self.assignment)
        self.write_result()
        first = runtime.observed_delivery(self.delivery, self.assignment)
        self.assertEqual(first,
                         runtime.observed_delivery(self.delivery,
                                                   self.assignment))

    # -- untrusted runtime material becomes a hold, never an exception ------

    def test_material_that_does_not_decode_is_held(self):
        runtime.publish_assignment(self.delivery, self.assignment)
        self.result_bytes(b"not json at all")
        seen = runtime.observed_delivery(self.delivery, self.assignment)
        self.assertEqual(seen["state"], "held")
        self.assertEqual(seen["hold"]["reason"], "result-unreadable")

    def test_material_outside_the_contract_is_held(self):
        runtime.publish_assignment(self.delivery, self.assignment)
        self.write_result(outcome="mostly-integrated")
        seen = runtime.observed_delivery(self.delivery, self.assignment)
        self.assertEqual(seen["state"], "held")
        self.assertEqual(seen["hold"]["reason"], "result-foreign")

    def test_a_result_answering_another_integration_is_held(self):
        runtime.publish_assignment(self.delivery, self.assignment)
        self.write_result(fence=self.fence + 1)
        seen = runtime.observed_delivery(self.delivery, self.assignment)
        self.assertEqual(seen["state"], "held")
        self.assertEqual(seen["hold"]["reason"], "result-foreign")

    def test_a_link_at_the_fixed_result_name_is_held(self):
        """A link at a name this contract fixes is not a document."""
        runtime.publish_assignment(self.delivery, self.assignment)
        os.symlink("/etc/hostname",
                   os.path.join(self.delivery.result_root,
                                runtime.RESULT_DOCUMENT))
        seen = runtime.observed_delivery(self.delivery, self.assignment)
        self.assertEqual(seen["state"], "held")
        self.assertEqual(seen["hold"]["reason"], "result-unreadable")

    def test_material_wider_than_the_bound_is_held(self):
        runtime.publish_assignment(self.delivery, self.assignment)
        self.result_bytes(b"x" * (runtime.MAX_DELIVERY_BYTES + 1))
        seen = runtime.observed_delivery(self.delivery, self.assignment)
        self.assertEqual(seen["state"], "held")
        self.assertEqual(seen["hold"]["reason"], "result-unreadable")

    def test_an_assignment_replaced_underneath_the_observation_is_held(self):
        runtime.publish_assignment(self.delivery, self.assignment)
        place = os.path.join(self.delivery.assignment_root,
                             runtime.ASSIGNMENT_DOCUMENT)
        os.chmod(place, 0o644)
        with open(place, "wb") as writing:
            writing.write(b'{"schema": "baton.v12.integration-assignment/1"}')
        seen = runtime.observed_delivery(self.delivery, self.assignment)
        self.assertEqual(seen["state"], "held")
        self.assertEqual(seen["hold"]["reason"], "result-foreign")

    def test_every_hold_a_delivery_produces_is_one_block_target_takes(self):
        runtime.publish_assignment(self.delivery, self.assignment)
        self.result_bytes(b"not json at all")
        held = runtime.observed_delivery(self.delivery,
                                         self.assignment)["hold"]
        self.assertEqual(sorted(held), sorted(runtime.HOLD_MEMBERS))
        block_target(self.coordinator, canonical_target_id=TARGET,
                     entry_id="entry-1", lease_id="lease-1", fence=self.fence,
                     reason=held["reason"], detail=held["detail"])
        self.assertEqual(
            self.coordinator._connection.execute(
                "SELECT blocked_reason FROM targets").fetchone()[0],
            "result-unreadable")

    # -- restart ------------------------------------------------------------

    def test_a_restart_adopts_the_delivery_off_the_disk(self):
        runtime.publish_assignment(self.delivery, self.assignment)
        self.write_result()
        again = runtime.adopt_delivery(self.root, attempt_id="attempt-1",
                               workspace_group=self.group)
        self.assertEqual(
            runtime.observed_delivery(again, self.assignment)["state"],
            "answered")

    def test_a_delivery_that_was_never_made_adopts_nothing(self):
        self.assertIsNone(runtime.adopt_delivery(
            os.path.join(self.root, "never"), attempt_id="attempt-1",
            workspace_group=self.group))

    def test_a_half_made_delivery_is_not_adopted(self):
        os.rmdir(self.delivery.result_root)
        caught = self.refusal(runtime.adopt_delivery, self.root,
                              attempt_id="attempt-1",
                              workspace_group=self.group)
        self.assertEqual(caught.code, "denied")

    def test_adopting_performs_no_recovery(self):
        """Restart may observe and classify. It may not retry, accept, clean
        up, release, discard or reassign."""
        runtime.publish_assignment(self.delivery, self.assignment)
        self.result_bytes(b"not json at all")
        before = os.listdir(self.delivery.result_root)
        again = runtime.adopt_delivery(self.root, attempt_id="attempt-1",
                               workspace_group=self.group)
        runtime.observed_delivery(again, self.assignment)
        self.assertEqual(os.listdir(self.delivery.result_root), before)
        self.assertEqual(
            self.coordinator._connection.execute(
                "SELECT state FROM entries").fetchone()[0], "leased")


class ThePublishedAssignmentIsReadableAsADocument(RuntimeCase):
    """W110934: the one public reader that answers the document itself.

    `observed_delivery` compares published bytes against an assignment its
    caller already holds and answers a STATE. A consumer that must bind a mount
    plan to the exact assignment a runtime will read needs the document, and
    deriving it from a private helper would be reaching around this module's
    own boundary.

    IT COMPOSES ITS OWN DELIVERY rather than inheriting the custody case's.
    Subclassing a live `TestCase` re-runs every one of its cases under a second
    name, which inflates a suite's count and makes two classes fail for one
    defect.
    """

    def setUp(self):
        super().setUp()
        self.assignment = self.compose()
        self.launch = os.path.join(self.root, "reader-launch")
        os.makedirs(self.launch)
        self.delivery = runtime.materialize_delivery(
            self.launch, attempt_id="attempt-1",
            workspace_group=_group_of(self))

    def test_an_unpublished_namespace_answers_absent(self):
        self.assertIsNone(runtime.published_assignment(self.delivery))

    def test_the_published_document_is_answered_whole(self):
        runtime.publish_assignment(self.delivery, self.assignment)
        self.assertEqual(runtime.published_assignment(self.delivery),
                         self.assignment)

    def test_it_is_owned_before_it_is_answered(self):
        """A hand-edited or corrupted file is not a mount plan's idea of an
        assignment."""
        runtime.publish_assignment(self.delivery, self.assignment)
        place = os.path.join(self.delivery.assignment_root,
                             runtime.ASSIGNMENT_DOCUMENT)
        os.chmod(place, 0o644)
        with open(place, "w", encoding="utf-8") as writing:
            json.dump(dict(self.assignment, schema="something/else"), writing)
        self.refusal(runtime.published_assignment, self.delivery)

    def test_material_that_does_not_decode_is_untrusted_rather_than_absent(self):
        runtime.publish_assignment(self.delivery, self.assignment)
        place = os.path.join(self.delivery.assignment_root,
                             runtime.ASSIGNMENT_DOCUMENT)
        os.chmod(place, 0o644)
        with open(place, "wb") as writing:
            writing.write(b"{not a document")
        caught = self.refusal(runtime.published_assignment, self.delivery)
        self.assertEqual((caught.category, caught.code),
                         ("refused", "precondition"))

    def test_it_is_read_through_the_typed_delivery_and_not_a_path(self):
        self.refusal(runtime.published_assignment,
                     self.delivery.assignment_root)

    def test_it_proves_nothing_about_a_grant(self):
        """An assignment stays readable after the lease that authorized it has
        ended, which is exactly why the live proof is a separate call."""
        runtime.publish_assignment(self.delivery, self.assignment)
        from baton_v12.integration.queue import block_target
        block_target(self.coordinator, canonical_target_id=TARGET,
                     entry_id="entry-1", lease_id="lease-1", fence=self.fence,
                     reason="runtime-interrupted",
                     detail={"observed": "blocked", "attempt_id": "attempt-1"})
        self.assertEqual(runtime.published_assignment(self.delivery),
                         self.assignment)
        self.refusal(self.compose)


class TheGrantDecidesEveryIdentityInTheAssignment(RuntimeCase):
    """Review [P0], twice: the attempt and the accepted profile kind.

    The acceptance boundary names an exact target, queue entry, ATTEMPT and
    fence. `compose_assignment` validated the caller's attempt id and wrote it
    in without ever comparing it to the grant's, so a live lease for one
    attempt composed an assignment and a delivery for any other -- three out of
    four is a different boundary. And it checked only the integrator
    participant against the lease, so a lease admitted for one profile kind
    composed a runtime for another.
    """

    def test_every_operand_current_and_the_attempt_differing_refuses(self):
        caught = self.refusal(self.compose, attempt_id="attempt-9")
        self.assertEqual(caught.code, "denied")
        self.assertIn("a runtime runs under the grant it was given",
                      caught.message)

    def test_the_assignment_carries_the_grant_s_attempt(self):
        self.assertEqual(self.compose()["attempt_id"], "attempt-1")

    def test_a_refused_attempt_composes_no_delivery_either(self):
        """The delivery is keyed by the attempt, so an assignment for the wrong
        one would be published into the wrong namespace."""
        self.refusal(self.compose, attempt_id="attempt-9")
        self.assertFalse(os.path.exists(os.path.join(self.root, "launch")))

    def test_the_admitted_profile_kind_is_what_runs(self):
        self.assertEqual(self.compose()["profile_kind"],
                         eligibility()["profile_kind"])

    def test_a_differing_profile_kind_refuses_against_stored_evidence(self):
        caught = self.refusal(self.compose,
                              profile=profile(profile_kind="different.profile"))
        self.assertEqual(caught.code, "denied")
        self.assertIn("under the profile it was accepted for", caught.message)
        # And it is the STORED entry that decides, not the caller's account.
        self.assertEqual(
            self.coordinator._connection.execute(
                "SELECT profile_kind FROM entries WHERE entry_id = 'entry-1'"
            ).fetchone()[0], eligibility()["profile_kind"])

    def test_the_entry_comes_from_the_same_snapshot_as_the_grant(self):
        """A separate unsynchronised read would give away the one-snapshot
        property the grant proof depends on."""
        from baton_v12.integration.queue import granted_context
        context = granted_context(self.coordinator, lease_id="lease-1",
                                  canonical_target_id=TARGET,
                                  entry_id="entry-1", fence=self.fence)
        self.assertEqual(sorted(context), ["entry", "lease", "predecessor"])
        self.assertEqual(context["entry"]["entry_id"], "entry-1")
        self.assertEqual(context["lease"]["lease_id"], "lease-1")
        self.assertIsNone(context["predecessor"])


class PublicationIsTheINHERITEDMechanism(RuntimeCase):
    """Review [P1]: the first draft copied a SUPERSEDED publication shape.

    One fixed staging name, one unchecked `os.write`, umask-dependent creation
    and `os.rename` -- and the record claimed it was `exchange.py`'s current
    mechanism. It was that module's OLD one, and every invariant W81857's own
    review added to fix it was missing. These are those invariants, driven.
    """

    def setUp(self):
        super().setUp()
        self.assignment = self.compose()
        self.launch = os.path.join(self.root, "launch")
        os.makedirs(self.launch)
        self.delivery = runtime.materialize_delivery(
            self.launch, attempt_id="attempt-1", workspace_group=self.group)

    def published(self):
        return os.path.join(self.delivery.assignment_root,
                            runtime.ASSIGNMENT_DOCUMENT)

    def test_a_stale_staging_file_does_not_wedge_publication(self):
        """A fixed staging name plus O_EXCL means a process that died between
        creation and publication fails every later incarnation forever -- a
        permanent wedge created by a crash, on the one path a durable transport
        exists to survive."""
        stale = os.path.join(self.delivery.assignment_root,
                             f".{runtime.ASSIGNMENT_DOCUMENT}.1.deadbeef."
                             f"publishing")
        with open(stale, "wb") as writing:
            writing.write(b"{}")
        self.assertTrue(
            runtime.publish_assignment(self.delivery,
                                       self.assignment)["published"])
        self.assertTrue(os.path.exists(self.published()))

    def test_a_short_write_is_not_reported_as_a_whole_one(self):
        original = runtime.os.write
        calls = {"n": 0}

        def trickle(handle, payload):
            calls["n"] += 1
            return original(handle, payload[:1])

        runtime.os.write = trickle
        self.addCleanup(setattr, runtime.os, "write", original)
        runtime.publish_assignment(self.delivery, self.assignment)
        with open(self.published(), "rb") as reading:
            self.assertEqual(len(reading.read()),
                             len(runtime._payload(self.assignment)))
        self.assertGreater(calls["n"], 1)

    def test_a_write_that_makes_no_progress_refuses(self):
        original = runtime.os.write
        runtime.os.write = lambda handle, payload: 0
        self.addCleanup(setattr, runtime.os, "write", original)
        caught = self.refusal(runtime.publish_assignment, self.delivery,
                              self.assignment)
        self.assertIn("made no progress", caught.message)
        self.assertFalse(os.path.exists(self.published()))

    def test_the_mode_is_established_and_not_requested(self):
        """Creation mode is masked by whatever umask the process holds, so the
        declared contract has to be set on the descriptor."""
        held = os.umask(0o777)
        self.addCleanup(os.umask, held)
        runtime.publish_assignment(self.delivery, self.assignment)
        self.assertEqual(
            stat.S_IMODE(os.stat(self.published()).st_mode),
            runtime.ASSIGNMENT_FILE)

    def test_the_staging_name_never_survives_an_ordinary_publication(self):
        runtime.publish_assignment(self.delivery, self.assignment)
        self.assertEqual(os.listdir(self.delivery.assignment_root),
                         [runtime.ASSIGNMENT_DOCUMENT])

    def test_an_identical_racer_is_adopted_rather_than_clobbering(self):
        """`link` fails closed on an existing name, which turns the race into a
        comparison."""
        payload = runtime._payload(self.assignment)
        self.assertTrue(runtime._publish_once(
            self.delivery.assignment_root, runtime.ASSIGNMENT_DOCUMENT,
            payload))
        self.assertFalse(runtime._publish_once(
            self.delivery.assignment_root, runtime.ASSIGNMENT_DOCUMENT,
            payload))
        answered = runtime.publish_assignment(self.delivery, self.assignment)
        self.assertFalse(answered["published"])

    def test_a_conflicting_racer_refuses_rather_than_replacing(self):
        other = dict(self.assignment, instructions_digest="sha256:other")
        runtime._publish_once(self.delivery.assignment_root,
                              runtime.ASSIGNMENT_DOCUMENT,
                              runtime._payload(other))
        caught = self.refusal(runtime.publish_assignment, self.delivery,
                              self.assignment)
        self.assertEqual(caught.code, "denied")
        with open(self.published(), "rb") as reading:
            self.assertEqual(reading.read(), runtime._payload(other))


class AdoptionProvesMANAGERCustody(RuntimeCase):
    """Review [P1]: `os.path.isdir` follows links and proves neither type nor
    mode, so a delivery whose custody had moved was still reported as this
    manager's own."""

    def setUp(self):
        super().setUp()
        self.launch = os.path.join(self.root, "launch")
        os.makedirs(self.launch)
        self.delivery = runtime.materialize_delivery(
            self.launch, attempt_id="attempt-1", workspace_group=self.group)

    def adopt(self):
        return runtime.adopt_delivery(self.launch, attempt_id="attempt-1",
                                      workspace_group=self.group)

    def test_a_sound_delivery_adopts(self):
        self.assertIsNotNone(self.adopt())

    def test_a_symlinked_namespace_is_refused(self):
        elsewhere = os.path.join(self.root, "elsewhere")
        os.makedirs(elsewhere, mode=runtime.ASSIGNMENT_DIR)
        os.rmdir(self.delivery.assignment_root)
        os.symlink(elsewhere, self.delivery.assignment_root)
        self.assertEqual(self.refusal(self.adopt).code, "denied")

    def test_a_namespace_that_is_not_a_directory_is_refused(self):
        os.rmdir(self.delivery.assignment_root)
        with open(self.delivery.assignment_root, "wb") as writing:
            writing.write(b"")
        self.assertEqual(self.refusal(self.adopt).code, "denied")

    def test_a_moved_assignment_mode_is_refused(self):
        os.chmod(self.delivery.assignment_root, 0o700)
        caught = self.refusal(self.adopt)
        self.assertIn("whose modes have moved", caught.message)

    def test_a_moved_result_mode_is_refused(self):
        os.chmod(self.delivery.result_root, 0o700)
        caught = self.refusal(self.adopt)
        self.assertIn("whose modes have moved", caught.message)

    def test_a_result_namespace_in_another_group_is_refused(self):
        moved = None
        for gid in os.getgroups():
            if gid == os.getgid():
                continue
            try:
                os.chown(self.delivery.result_root, -1, gid)
            except OSError:
                continue
            moved = gid
            break
        if moved is None:
            self.skipTest("this host's user can move the namespace into no "
                          "other group, so a wrong-group delivery cannot be "
                          "created honestly")
        os.chmod(self.delivery.result_root, workspaces.WORKSPACE_DIR)
        caught = self.refusal(self.adopt)
        self.assertIn("does not share", caught.message)

    def test_the_group_comes_from_the_manager_s_own_record(self):
        """A gid a caller could choose is a group a caller chose."""
        self.assertEqual(
            self.refusal(runtime.adopt_delivery, self.launch,
                         attempt_id="attempt-1",
                         workspace_group=os.getgid()).code, "denied")


class OneObservationDocumentAndOneAnswer(RuntimeCase):
    """Re-review [P1]: the removed caller-witness schema stayed exported.

    `WITNESS_MEMBERS` declared `attempt_id`, `execution_runtime` and
    `evidence`; the manager-derived helper that replaced the caller document
    returns two members. A public contract advertising a closed document no
    function returns is worse than none, and `evidence` was the CALLER's word
    for why it believed itself -- the manager's row needs no such member,
    because the row IS the evidence.
    """

    def test_the_exported_members_are_exactly_what_the_helper_returns(self):
        observed = runtime.prior_runtime_witness(self.manager, "attempt-1")
        self.assertEqual(sorted(observed),
                         sorted(runtime.OBSERVED_RUNTIME_MEMBERS))

    def test_the_superseded_witness_shape_is_not_a_public_surface(self):
        self.assertNotIn("WITNESS_MEMBERS", runtime.__all__)
        self.assertFalse(hasattr(runtime, "WITNESS_MEMBERS"))
        self.assertNotIn("evidence", runtime.OBSERVED_RUNTIME_MEMBERS)

    def test_the_export_contract_is_one_closed_list(self):
        """Third review [P2], and it is the same boundary as the finding above.

        Replacing one stale public shape should leave ONE coherent export, and
        my correction left two entries for its replacement -- 37 names, 36 of
        them distinct. A closed list with a repeat in it is a contract that has
        not been read since it was edited, so this reads it.
        """
        self.assertEqual(sorted(runtime.__all__),
                         sorted(set(runtime.__all__)))
        for name in runtime.__all__:
            with self.subTest(name=name):
                self.assertTrue(hasattr(runtime, name))

    def test_the_observation_is_the_manager_s_row_and_refuses_absence(self):
        caught = self.refusal(runtime.prior_runtime_witness, self.manager,
                              "attempt-never-recorded")
        self.assertIn("absence of a record is not absence of a runtime",
                      caught.message)


class AdoptionProvesTheROOTAsWellAsItsChildren(RuntimeCase):
    """Re-review [P1]: `O_NOFOLLOW` binds only the FINAL component.

    Adoption proved the two leaf namespaces and never opened their parent, so
    opening `<root>/integration/assignment` no-follow said nothing about
    `integration` -- a symlink there was followed and an arbitrary correctly
    shaped tree behind it was reported as this manager's own delivery.
    """

    def setUp(self):
        super().setUp()
        self.launch = os.path.join(self.root, "launch")
        os.makedirs(self.launch)
        self.delivery = runtime.materialize_delivery(
            self.launch, attempt_id="attempt-1", workspace_group=self.group)

    def adopt(self):
        return runtime.adopt_delivery(self.launch, attempt_id="attempt-1",
                                      workspace_group=self.group)

    def test_the_root_is_established_at_an_exact_mode(self):
        self.assertEqual(stat.S_IMODE(os.stat(self.delivery.root).st_mode),
                         runtime.DELIVERY_DIR)

    def test_the_root_mode_is_established_under_any_umask(self):
        """`makedirs` asks for a mode and the umask decides what it gets."""
        elsewhere = os.path.join(self.root, "masked")
        os.makedirs(elsewhere)
        held = os.umask(0o077)
        self.addCleanup(os.umask, held)
        made = runtime.materialize_delivery(elsewhere, attempt_id="attempt-2",
                                            workspace_group=self.group)
        self.assertEqual(stat.S_IMODE(os.stat(made.root).st_mode),
                         runtime.DELIVERY_DIR)

    def test_an_intermediate_root_symlink_is_refused(self):
        """The reproduction: move the intact delivery aside and leave a link
        at the fixed name."""
        moved = os.path.join(self.root, "moved")
        os.rename(self.delivery.root, moved)
        os.symlink(moved, self.delivery.root)
        caught = self.refusal(self.adopt)
        self.assertEqual(caught.code, "denied")
        self.assertIn("delivery root", caught.message)

    def test_a_root_that_is_not_a_directory_is_refused(self):
        moved = os.path.join(self.root, "moved")
        os.rename(self.delivery.root, moved)
        with open(self.delivery.root, "wb") as writing:
            writing.write(b"")
        self.assertEqual(self.refusal(self.adopt).code, "denied")

    def test_a_moved_root_mode_is_refused(self):
        os.chmod(self.delivery.root, 0o755)
        caught = self.refusal(self.adopt)
        self.assertIn("whose modes have moved", caught.message)

    def test_a_sound_delivery_still_adopts(self):
        self.assertIsNotNone(self.adopt())

    def test_absence_is_still_an_ordinary_answer(self):
        self.assertIsNone(runtime.adopt_delivery(
            os.path.join(self.root, "never"), attempt_id="attempt-1",
            workspace_group=self.group))
