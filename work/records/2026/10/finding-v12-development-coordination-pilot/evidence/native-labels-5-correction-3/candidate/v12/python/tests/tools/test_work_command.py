"""W29401 — the bundled `work` command: the Work-label CLI, driven as argv.

Every case here enters `tools.work_command.main` with an operator's own
argument list and reads the JSON it prints, because that is the whole claim of
this Work: W29400's label behaviour was accepted and UNREACHABLE, so what has
to be proved is the reachability -- the verbs, the operand spellings, the
refusals an operator actually sees, and the exit codes.

WHAT IS REAL. A real `Authority` store in a temporary directory, real grants,
real sessions minted inside the command, real replay through the real operation
journal. Nothing is mocked except where a case is specifically about which
OPENER a verb uses.

WHAT THIS SUITE DOES NOT RE-PROVE. The grammar, the cardinality, the
scope-resolved decision and the one-snapshot predicate are W29400's and are
proved against the model in `tests/authority/test_work_labels.py` and, through
the two public faces a command can reach, in
`tests/authority/test_work_label_exposure.py`. What is asserted here is that
the command REACHES them and adds no second opinion:
where a refusal is quoted it is quoted to prove the operator is told the
authority's own sentence rather than a paraphrase this file invented.
"""

import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest import mock

from baton_v12.authority import Authority, V12
from baton_v12.authority.labels import MAX_LABELS, MAX_LABEL_LENGTH

from tools import stack_command, work_command

UUID = "0123456789abcdef0123456789abcdef"
WORK = "0123abcd-W1"
OTHER = "0123abcd-W2"
THIRD = "0123abcd-W3"
CLAUDE = "baton.claude"
SLAW = "baton.slaw"
ROUTE = "impl"
NOW = "2026-11-19T12:00:00.000Z"
PLATFORM = "scope:platform"

# Every subcommand the installed command served BEFORE this Work, written out
# so the one thing this change does to that table -- add `work` -- is a
# comparison rather than a claim.
BEFORE = {"bootstrap", "start", "stop", "status", "publish", "monitor",
          "repository", "manager", "view", "logs", "record", "disposition",
          "identity", "pool", "attempt-diagnostics"}


class WorkCommandCase(unittest.TestCase):
    """One disposable Authority, and the command entered as argv."""

    def setUp(self):
        self._root = tempfile.TemporaryDirectory(prefix="v12-w29401-cli-")
        self.addCleanup(self._root.cleanup)
        self.store = os.path.join(self._root.name, "authority.sqlite3")
        authority = Authority.create(self.store, authority_uuid=UUID,
                                     clock=lambda: NOW)
        self.addCleanup(authority.dispose)
        self.authority = authority
        self._operations = 0

    def op(self):
        self._operations += 1
        return f"op-{self._operations}"

    def work(self, work_id=WORK, *, labels=(), scope=None):
        self.authority.create_work(work_id, ROUTE, contract=V12,
                                   operation_id="create-" + work_id,
                                   labels=labels, scope=scope)
        self.authority.add_route_handler(ROUTE, CLAUDE)
        return work_id

    def allow(self, participant=SLAW, scope=None):
        self.authority.grant_capability(participant, "manage-work-labels",
                                        scope=scope)
        return participant

    def closed(self, work_id=WORK):
        self.authority.grant_capability(CLAUDE, "close")
        self.authority.session(CLAUDE).close(
            {"work_id": work_id, "operation_id": "close-" + work_id,
             "outcome": "satisfying", "rationale": "done"})
        return work_id

    # -- entering the command ------------------------------------------------

    def run_command(self, verb, *operands, participant=None, work=None,
                    operation_id=None, labels=(), without=()):
        """`work <verb> ...` as an operator writes it, with its output.

        Returns `(code, stdout, stderr)`. The store selection is always
        supplied because every verb takes it; everything else is the case's.
        """
        argv = [verb, "--authority-store", self.store,
                "--authority-uuid", UUID]
        if participant is not None:
            argv += ["--participant", participant]
        if work is not None:
            argv += ["--work", work]
        if operation_id is not None:
            argv += ["--operation-id", operation_id]
        for one in labels:
            argv += ["--label", one]
        for one in without:
            argv += ["--without-label", one]
        argv += list(operands)
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = work_command.main(argv)
        return code, out.getvalue(), err.getvalue()

    def answered(self, verb, **named):
        """One invocation that succeeded, as its parsed answer."""
        code, said, err = self.run_command(verb, **named)
        self.assertEqual(code, 0, said + err)
        return json.loads(said)

    def refused(self, verb, **named):
        """One invocation this command refuses, as its `refused:` sentence."""
        code, said, err = self.run_command(verb, **named)
        self.assertEqual(code, 2, said + err)
        self.assertTrue(err.startswith("refused: "), err)
        return err

    def live(self, work_id=WORK):
        return self.authority.labels_of(work_id)

    def events(self, work_id=WORK):
        return self.authority.work_label_events(work_id)


class TheCommandIsBundledAndItsVocabularyIsItsOwn(WorkCommandCase):
    """W29401's whole premise: the verbs exist, at the deployed command, and
    they are not somebody else's label verbs."""

    def test_the_installed_command_serves_work(self):
        self.assertIn("work", stack_command.COMMANDS)
        with mock.patch.object(work_command, "main",
                               lambda operands: ("reached", operands)):
            self.assertEqual(stack_command.COMMANDS["work"](["labels"]),
                             ("reached", ["labels"]))

    def test_the_existing_subcommands_are_untouched_and_work_is_additive(self):
        """The change to this table is ONE new name and nothing else."""
        self.assertEqual(set(stack_command.COMMANDS) - {"work"}, BEFORE)

    def test_the_four_verbs_are_the_whole_surface(self):
        self.assertEqual(sorted(work_command.VERBS),
                         ["label-work", "labels", "list", "unlabel-work"])

    def test_v11s_thread_verbs_are_not_reachable_here(self):
        """v11's `baton label` BINDS A THREAD TO A WORK; this command's
        `label-work` adds an opaque value TO a Work.

        The two hosts run side by side, so the short spellings are absent
        rather than meaning a second thing: an operator who writes `work
        label` is told what this command serves instead of silently reaching
        the wrong semantics.
        """
        for absent in ("label", "unlabel", "tag", "untag", "bind"):
            with self.subTest(absent=absent):
                self.assertNotIn(absent, work_command.VERBS)
                out, err = io.StringIO(), io.StringIO()
                with redirect_stdout(out), redirect_stderr(err):
                    with self.assertRaises(SystemExit) as caught:
                        work_command.main([absent, "--authority-store",
                                           self.store, "--authority-uuid",
                                           UUID])
                self.assertEqual(caught.exception.code, 2)
                self.assertIn("invalid choice", err.getvalue())

    def test_dispatch_is_by_command_name_and_never_by_how_a_label_is_spelled(self):
        """A label that LOOKS like another vocabulary is still just a value.

        `0123abcd-w9` is shaped like a Work identity, `baton.claude` like a
        participant and `t123` like a v11 thread name -- and every one of them
        is accepted here as an ordinary opaque key that changes nothing but
        the label set. The command reads no label to decide what it does,
        which is why there is no branch here to point at: the proof is that
        all three behave identically and the Work's own facts do not move.
        """
        self.work()
        self.allow()
        answer = self.answered(
            "label-work", participant=SLAW, work=WORK,
            operation_id=self.op(),
            labels=["0123abcd-w9", "baton.claude", "t123"])
        self.assertEqual(answer["changed"],
                         ["0123abcd-w9", "baton.claude", "t123"])
        projection = self.authority.project_work(WORK)
        self.assertIsNone(projection["handler"])
        self.assertEqual(projection["status"], "open")
        self.assertEqual(projection["phase"], "queued")

    def test_the_command_reaches_no_oci_or_runtime_label_vocabulary(self):
        """The Worker Manager's `labels` are OCI execution identity.

        Asserted from the SOURCE rather than remembered: this module imports
        neither the worker manager nor the stage execution adapters, so there
        is nothing in it that could reach a container label at all.
        """
        import ast
        import pathlib

        source = pathlib.Path(work_command.__file__).read_text(
            encoding="utf-8")
        imported = set()
        for node in ast.walk(ast.parse(source)):
            if type(node) is ast.Import:
                imported.update(one.name for one in node.names)
            elif type(node) is ast.ImportFrom and node.module:
                imported.add(node.module)
        self.assertEqual(
            sorted(one for one in imported if one.startswith("baton_v12")),
            ["baton_v12.authority", "baton_v12.authority.errors",
             "baton_v12.authority.labels"])
        for forbidden in ("worker_manager", "integration", "stage_execution",
                          "docker", "oci"):
            with self.subTest(forbidden=forbidden):
                self.assertFalse(
                    [one for one in imported if forbidden in one], imported)


class TheGrammarAndCardinalityAreTheAuthoritys(WorkCommandCase):
    def setUp(self):
        super().setUp()
        self.work()
        self.allow()

    def test_a_key_value_tag_is_refused_as_a_key_this_grammar_lacks(self):
        said = self.refused("label-work", participant=SLAW, work=WORK,
                            operation_id=self.op(), labels=["team=core"])
        self.assertIn("'team=core'", said)
        self.assertIn("a Work label is 1 to 64 characters", said)
        self.assertEqual(self.live(), [])

    def test_an_or_like_operand_is_refused_rather_than_split(self):
        """A comma-joined or space-joined list is not one key, and this
        command has no splitter that could make it two."""
        for spelling in ("v12,hot", "v12 hot", "v12|hot", "v12+hot"):
            with self.subTest(spelling=spelling):
                self.refused("label-work", participant=SLAW, work=WORK,
                             operation_id=self.op(), labels=[spelling])
        self.assertEqual(self.live(), [])

    def test_the_grammar_boundaries_reach_the_operator_unaltered(self):
        for bad in ("", ".leading", "_leading", "has/slash", "caf\u00e9",
                    "a" * (MAX_LABEL_LENGTH + 1)):
            with self.subTest(bad=bad):
                self.refused("label-work", participant=SLAW, work=WORK,
                             operation_id=self.op(), labels=[bad])
        for good in ("a", "0", "a.b_c-d", "a" * MAX_LABEL_LENGTH):
            with self.subTest(good=good):
                answer = self.answered("label-work", participant=SLAW,
                                       work=WORK, operation_id=self.op(),
                                       labels=[good])
                self.assertEqual(answer["changed"], [good])

    def test_a_label_that_starts_with_a_dash_is_written_as_one_operand(self):
        """`--label=-leading` is how argparse takes a value that looks like an
        option, which is the same rule `--verification=-m` already documents.

        Written that way the operand REACHES the grammar and is refused by
        it -- a label starting with a hyphen is not a key -- rather than being
        read as an unknown option, which is a different answer to a different
        question.
        """
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = work_command.main(
                ["label-work", "--authority-store", self.store,
                 "--authority-uuid", UUID, "--participant", SLAW,
                 "--work", WORK, "--operation-id", "op-dash",
                 "--label=-leading"])
        self.assertEqual(code, 2)
        self.assertIn("'-leading'", err.getvalue())
        self.assertIn("starts with an ASCII letter or digit", err.getvalue())
        self.assertEqual(self.live(), [])

    def test_repeated_label_operands_normalize_into_one_sorted_set(self):
        answer = self.answered("label-work", participant=SLAW, work=WORK,
                               operation_id=self.op(),
                               labels=["Release-Foo", "V12", "hot"])
        self.assertEqual([one["label"] for one in answer["acts"]],
                         ["hot", "release-foo", "v12"])
        self.assertEqual(answer["labels"], ["hot", "release-foo", "v12"])

    def test_the_act_identities_are_derived_from_the_labels_not_their_order(self):
        """So the same request written in another order is the same acts."""
        first = self.answered("label-work", participant=SLAW, work=WORK,
                              operation_id="op-order", labels=["b", "a"])
        self.assertEqual([one["operation_id"] for one in first["acts"]],
                         ["op-order:label-work:a", "op-order:label-work:b"])
        again = self.answered("label-work", participant=SLAW, work=WORK,
                              operation_id="op-order", labels=["a", "b"])
        self.assertEqual(again, first)

    def test_two_operands_that_are_one_key_refuse_and_change_nothing(self):
        said = self.refused("label-work", participant=SLAW, work=WORK,
                            operation_id=self.op(), labels=["v12", "V12"])
        self.assertIn("one label after normalization", said)
        self.assertEqual(self.live(), [])
        self.assertEqual(self.events(), [])

    def test_a_request_beyond_the_cardinality_refuses_at_the_boundary(self):
        full = [f"label-{index:02d}" for index in range(MAX_LABELS)]
        self.answered("label-work", participant=SLAW, work=WORK,
                      operation_id="op-full", labels=full)
        self.assertEqual(len(self.live()), MAX_LABELS)
        said = self.refused("label-work", participant=SLAW, work=WORK,
                            operation_id=self.op(), labels=["one-too-many"])
        self.assertIn("maximum", said)
        self.assertEqual(len(self.live()), MAX_LABELS)
        # ...AND A LABEL THE WORK ALREADY HOLDS IS STILL ACCEPTED, because a
        # no-op is not charged against the bound.
        answer = self.answered("label-work", participant=SLAW, work=WORK,
                               operation_id=self.op(), labels=[full[0]])
        self.assertEqual(answer["changed"], [])

    def test_an_operation_id_too_long_to_derive_from_refuses_first(self):
        """Named with its bound, before the store is touched at all."""
        said = self.refused("label-work", participant=SLAW, work=WORK,
                            operation_id="o" * 150, labels=["v12"])
        self.assertIn("at most 160 characters", said)
        self.assertEqual(self.live(), [])


class MutationsAreAuthorizedOrTheyDoNotHappen(WorkCommandCase):
    def test_a_granted_participant_labels_and_unlabels(self):
        self.work(WORK, labels=["v12"])
        self.allow()
        added = self.answered("label-work", participant=SLAW, work=WORK,
                              operation_id=self.op(), labels=["hot"])
        self.assertEqual(added["actor"], SLAW)
        self.assertEqual(added["acts"][0]["decision"]["role"],
                         "manage-work-labels")
        self.assertEqual(added["labels"], ["hot", "v12"])
        removed = self.answered("unlabel-work", participant=SLAW, work=WORK,
                                operation_id=self.op(), labels=["v12"])
        self.assertEqual(removed["acts"][0]["action"], "removed")
        self.assertEqual(removed["labels"], ["hot"])
        self.assertEqual(self.live(), ["hot"])

    def test_the_actor_comes_from_the_participant_and_there_is_no_actor_operand(self):
        """`--actor` does not exist here, and that absence is the point."""
        self.work()
        self.allow()
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            with self.assertRaises(SystemExit):
                work_command.main(
                    ["label-work", "--authority-store", self.store,
                     "--authority-uuid", UUID, "--participant", SLAW,
                     "--actor", CLAUDE, "--work", WORK,
                     "--operation-id", "op-actor", "--label", "v12"])
        self.assertIn("unrecognized arguments", err.getvalue())
        self.assertEqual(self.live(), [])

    def test_a_participant_without_the_grant_is_refused_and_nothing_moves(self):
        self.work(WORK, labels=["v12"])
        for who in (CLAUDE, "baton.nobody"):
            with self.subTest(participant=who):
                said = self.refused("label-work", participant=who, work=WORK,
                                    operation_id=self.op(), labels=["hot"])
                self.assertIn("manage-work-labels", said)
                self.assertIn("does not hold", said)
                self.refused("unlabel-work", participant=who, work=WORK,
                             operation_id=self.op(), labels=["v12"])
        self.assertEqual(self.live(), ["v12"])
        self.assertEqual(len(self.events()), 1)

    def test_authorization_is_resolved_in_the_works_own_scope(self):
        """A deployment-wide grant does not authorize a scoped Work, and the
        scoped grant does."""
        self.work(WORK, scope=PLATFORM)
        self.allow()
        said = self.refused("label-work", participant=SLAW, work=WORK,
                            operation_id=self.op(), labels=["v12"])
        self.assertIn("manage-work-labels", said)
        self.assertEqual(self.live(), [])
        self.allow(scope=PLATFORM)
        answer = self.answered("label-work", participant=SLAW, work=WORK,
                               operation_id=self.op(), labels=["v12"])
        self.assertEqual(answer["acts"][0]["decision"]["effective_scope"],
                         PLATFORM)

    def test_a_repeated_request_stops_at_the_first_unauthorized_label(self):
        """A revocation between two acts of one request leaves the first
        committed and the second refused, which is the honest answer: each
        label is its own authorized act and nothing here batches a decision.
        """
        self.work()
        self.allow()
        session = self.authority.session(SLAW)
        original = type(session).label_work

        def revoking(one, *documents):
            answer = original(one, *documents)
            self.authority.revoke_capability(SLAW, "manage-work-labels")
            return answer

        with mock.patch.object(type(session), "label_work", revoking):
            said = self.refused("label-work", participant=SLAW, work=WORK,
                                operation_id="op-revoked",
                                labels=["aaa", "zzz"])
        self.assertIn("manage-work-labels", said)
        self.assertEqual(self.live(), ["aaa"])

    def test_a_work_this_authority_does_not_hold_refuses(self):
        self.allow()
        said = self.refused("label-work", participant=SLAW,
                            work="0123abcd-W99", operation_id=self.op(),
                            labels=["v12"])
        self.assertIn("0123abcd-W99", said)


class TerminalWorkStaysLabellable(WorkCommandCase):
    def test_a_closed_work_is_labelled_and_unlabelled_through_the_command(self):
        self.work(WORK, labels=["v12"])
        self.closed()
        self.allow()
        answer = self.answered("label-work", participant=SLAW, work=WORK,
                               operation_id="op-archive", labels=["archived"])
        self.assertEqual(answer["changed"], ["archived"])
        self.answered("unlabel-work", participant=SLAW, work=WORK,
                      operation_id="op-retire", labels=["v12"])
        self.assertEqual(self.live(), ["archived"])
        projection = self.authority.project_work(WORK)
        # THE CLOSURE IS UNTOUCHED. Archive metadata reopens nothing.
        self.assertEqual(projection["status"], "closed")
        self.assertIsNone(projection["phase"])
        self.assertEqual(projection["outcome"], "satisfying")

    def test_the_post_closure_change_is_audited_and_readable(self):
        self.work(WORK, labels=["v12"])
        self.closed()
        self.allow()
        self.answered("label-work", participant=SLAW, work=WORK,
                      operation_id="op-archive", labels=["archived"])
        read = self.answered("labels", work=WORK)
        last = read["events"][-1]
        self.assertEqual((last["label"], last["action"], last["act"]),
                         ("archived", "added", "work-label"))
        self.assertEqual(last["act_id"], "op-archive:label-work:archived")
        self.assertEqual(last["decision"]["role"], "manage-work-labels")


class ReplayConvergenceAndCollision(WorkCommandCase):
    def setUp(self):
        super().setUp()
        self.work()
        self.allow()

    def test_an_exact_retry_prints_byte_identical_output(self):
        first = self.run_command("label-work", participant=SLAW, work=WORK,
                                 operation_id="op-exact",
                                 labels=["v12", "hot"])
        again = self.run_command("label-work", participant=SLAW, work=WORK,
                                 operation_id="op-exact",
                                 labels=["v12", "hot"])
        self.assertEqual(again, first)
        self.assertEqual(json.loads(first[1])["changed"], ["hot", "v12"])
        # AND THE JOURNAL GAINED NOTHING: a replay is not a second act.
        self.assertEqual(len(self.events()), 2)

    def test_a_retry_replays_even_after_the_grant_is_revoked(self):
        """Replay answers the committed act, not whether it could happen
        now."""
        first = self.run_command("label-work", participant=SLAW, work=WORK,
                                 operation_id="op-exact", labels=["v12"])
        self.authority.revoke_capability(SLAW, "manage-work-labels")
        self.assertEqual(
            self.run_command("label-work", participant=SLAW, work=WORK,
                             operation_id="op-exact", labels=["v12"]),
            first)

    def test_an_exact_retry_after_an_intervening_removal_prints_the_committed_result(
            self):
        """W385292 review: the first cut read the LIVE set into the replay
        answer, so a retry after the label was removed again printed the
        original acts beside an empty set -- neither the committed outcome
        nor the byte-identical replay promised."""
        first = self.run_command("label-work", participant=SLAW, work=WORK,
                                 operation_id="op-exact", labels=["v12"])
        self.answered("unlabel-work", participant=SLAW, work=WORK,
                      operation_id="op-undo", labels=["v12"])
        self.assertEqual(self.live(), [])
        again = self.run_command("label-work", participant=SLAW, work=WORK,
                                 operation_id="op-exact", labels=["v12"])
        self.assertEqual(again, first)
        self.assertEqual(json.loads(again[1])["labels"], ["v12"])
        self.assertEqual(json.loads(again[1])["changed"], ["v12"])
        # NO SECOND EFFECT: the Work still carries nothing, and the journal
        # holds the two acts that happened.
        self.assertEqual(self.live(), [])
        self.assertEqual(len(self.events()), 2)
        # WHAT THE WORK CARRIES NOW IS THE READ VERB'S ANSWER, as itself.
        self.assertEqual(
            self.answered("labels", work=WORK)["labels"], [])

    def test_an_exact_retry_after_an_intervening_addition_reports_its_own_set(
            self):
        first = self.answered("label-work", participant=SLAW, work=WORK,
                              operation_id="op-exact", labels=["v12"])
        self.assertEqual(first["labels"], ["v12"])
        self.answered("label-work", participant=SLAW, work=WORK,
                      operation_id="op-more", labels=["hot"])
        self.assertEqual(self.live(), ["hot", "v12"])
        again = self.answered("label-work", participant=SLAW, work=WORK,
                              operation_id="op-exact", labels=["v12"])
        self.assertEqual(again, first)
        self.assertEqual(again["labels"], ["v12"])
        self.assertEqual(len(self.events()), 2)

    def test_a_retry_after_revocation_and_an_intervening_change_still_replays(
            self):
        first = self.run_command("label-work", participant=SLAW, work=WORK,
                                 operation_id="op-exact",
                                 labels=["hot", "v12"])
        self.answered("unlabel-work", participant=SLAW, work=WORK,
                      operation_id="op-undo", labels=["hot"])
        self.authority.revoke_capability(SLAW, "manage-work-labels")
        again = self.run_command("label-work", participant=SLAW, work=WORK,
                                 operation_id="op-exact",
                                 labels=["v12", "hot"])
        self.assertEqual(again, first)
        self.assertEqual(json.loads(again[1])["labels"], ["hot", "v12"])
        self.assertEqual(self.live(), ["v12"])
        self.assertEqual(len(self.events()), 3)

    def test_a_multi_label_request_completes_per_label_and_a_retry_finishes_it(
            self):
        """PER-LABEL ACTS, STATED AS SUCH. A request refused part-way keeps
        the acts before the refusal, says so with exit 2 and no summary, and
        an exact retry under the same identity replays the completed acts and
        performs the rest -- no second effect, no atomic batch."""
        from baton_v12.authority.labels import MAX_LABELS

        self.work(OTHER,
                  labels=[f"label-{index:02d}" for index in range(MAX_LABELS - 1)])
        minted = len(self.events(OTHER))
        code, said, err = self.run_command(
            "label-work", participant=SLAW, work=OTHER,
            operation_id="op-overflow", labels=["z-last-slot", "zz-overflow"])
        self.assertEqual(code, 2)
        self.assertEqual(said, "")
        self.assertIn(f"maximum {MAX_LABELS} labels", err)
        self.assertIn("z-last-slot", self.live(OTHER))
        self.assertNotIn("zz-overflow", self.live(OTHER))
        self.assertEqual(len(self.events(OTHER)), minted + 1)
        # THE REPAIR THE REFUSAL NAMES, then the same request again.
        self.answered("unlabel-work", participant=SLAW, work=OTHER,
                      operation_id="op-make-room", labels=["label-00"])
        answer = self.answered("label-work", participant=SLAW, work=OTHER,
                               operation_id="op-overflow",
                               labels=["z-last-slot", "zz-overflow"])
        self.assertEqual([one["label"] for one in answer["acts"]],
                         ["z-last-slot", "zz-overflow"])
        self.assertTrue(all(one["changed"] for one in answer["acts"]))
        self.assertEqual(answer["changed"], ["z-last-slot", "zz-overflow"])
        self.assertIn("zz-overflow", answer["labels"])
        # ONE EVENT PER LABEL THAT MOVED: the replayed act added none.
        self.assertEqual(len(self.events(OTHER)), minted + 3)

    def test_a_convergent_request_succeeds_as_changed_false(self):
        self.answered("label-work", participant=SLAW, work=WORK,
                      operation_id=self.op(), labels=["v12"])
        answer = self.answered("label-work", participant=SLAW, work=WORK,
                               operation_id=self.op(), labels=["v12"])
        self.assertEqual(answer["changed"], [])
        self.assertFalse(answer["acts"][0]["changed"])
        self.assertEqual(answer["labels"], ["v12"])
        absent = self.answered("unlabel-work", participant=SLAW, work=WORK,
                               operation_id=self.op(),
                               labels=["never-there"])
        self.assertEqual(absent["changed"], [])
        self.assertEqual(absent["labels"], ["v12"])
        # ONE EVENT FOR THE ONE THING THAT HAPPENED.
        self.assertEqual(len(self.events()), 1)

    def test_the_same_identity_for_a_different_label_set_collides(self):
        self.answered("label-work", participant=SLAW, work=WORK,
                      operation_id="op-reused", labels=["v12"])
        code, said, err = self.run_command(
            "label-work", participant=SLAW, work=WORK,
            operation_id="op-reused", labels=["v12", "hot"])
        self.assertEqual(code, 2)
        self.assertIn("is not the one operation 'op-reused' already carries",
                      err)
        # THE ANSWER SHOWS BOTH REQUESTS AND SAYS NOTHING WAS DONE.
        shown = json.loads(said)
        self.assertEqual(shown["performed"], "nothing")
        self.assertFalse(shown["replayed"])
        self.assertEqual(shown["already_carries"]["request"]["labels"],
                         ["v12"])
        self.assertEqual(shown["this_request"]["labels"], ["hot", "v12"])
        self.assertEqual(self.live(), ["v12"])

    def test_the_same_identity_for_the_other_verb_collides(self):
        """`label-work` and `unlabel-work` under one identity are two
        different requests, and the verb is in the bound request."""
        self.answered("label-work", participant=SLAW, work=WORK,
                      operation_id="op-reused", labels=["v12"])
        said = self.refused("unlabel-work", participant=SLAW, work=WORK,
                            operation_id="op-reused", labels=["v12"])
        self.assertIn("already carries", said)
        self.assertEqual(self.live(), ["v12"])

    def test_the_same_identity_for_another_work_collides(self):
        self.work(OTHER)
        self.answered("label-work", participant=SLAW, work=WORK,
                      operation_id="op-reused", labels=["v12"])
        self.refused("label-work", participant=SLAW, work=OTHER,
                     operation_id="op-reused", labels=["v12"])
        self.assertEqual(self.live(OTHER), [])

    def test_the_same_identity_for_another_participant_collides(self):
        self.allow(CLAUDE)
        self.answered("label-work", participant=SLAW, work=WORK,
                      operation_id="op-reused", labels=["v12"])
        self.refused("label-work", participant=CLAUDE, work=WORK,
                     operation_id="op-reused", labels=["hot"])
        self.assertEqual(self.live(), ["v12"])


class TheReadVerbs(WorkCommandCase):
    def setUp(self):
        super().setUp()
        self.work(WORK, labels=["V12", "release-foo"])
        self.work(OTHER, labels=["v12"])
        self.work(THIRD)

    def test_labels_reads_the_sorted_live_set_and_its_events(self):
        answer = self.answered("labels", work=WORK)
        self.assertEqual(answer["work_id"], WORK)
        self.assertEqual(answer["authority_uuid"], UUID)
        self.assertEqual(answer["labels"], ["release-foo", "v12"])
        self.assertEqual([(one["label"], one["action"], one["act"])
                          for one in answer["events"]],
                         [("release-foo", "added", "work-create"),
                          ("v12", "added", "work-create")])
        # A CREATE-TIME ADDITION NAMES ITS CREATION, not a grant.
        self.assertIsNone(answer["events"][0]["decision"])
        self.assertEqual(answer["events"][0]["creation"]["kind"],
                         "trusted-bootstrap")

    def test_an_unlabelled_work_reads_an_empty_set_and_an_empty_history(self):
        """The behaviour of a Work nobody labelled, PRESERVED: absence is an
        answer, not a missing member and not a refusal."""
        answer = self.answered("labels", work=THIRD)
        self.assertEqual(answer["labels"], [])
        self.assertEqual(answer["events"], [])

    def test_an_unfiltered_list_is_every_work(self):
        answer = self.answered("list")
        self.assertEqual(answer["work"], sorted([WORK, OTHER, THIRD]))
        self.assertEqual(answer["matched"], 3)
        self.assertEqual(answer["filter"], {"all_of": [], "none_of": []})

    def test_repeated_label_operands_are_all_of_and_never_or(self):
        self.assertEqual(self.answered("list", labels=["v12"])["work"],
                         sorted([WORK, OTHER]))
        # BOTH, not either: an OR would answer two Work here and does not.
        answer = self.answered("list", labels=["v12", "release-foo"])
        self.assertEqual(answer["work"], [WORK])
        self.assertEqual(answer["matched"], 1)

    def test_repeated_without_label_operands_are_none_of(self):
        self.assertEqual(self.answered("list", without=["v12"])["work"],
                         [THIRD])
        self.assertEqual(
            self.answered("list", without=["v12", "release-foo"])["work"],
            [THIRD])

    def test_the_positive_and_negative_halves_compose(self):
        answer = self.answered("list", labels=["v12"], without=["release-foo"])
        self.assertEqual(answer["work"], [OTHER])
        self.assertEqual(answer["filter"],
                         {"all_of": ["v12"], "none_of": ["release-foo"]})
        self.assertEqual(
            self.answered("list", labels=["v12", "release-foo"],
                          without=["archived"])["work"],
            [WORK])

    def test_a_filter_requiring_and_excluding_one_label_refuses(self):
        said = self.refused("list", labels=["v12"], without=["V12"])
        self.assertIn("cannot both carry and not carry", said)

    def test_a_filter_operand_is_matched_exactly_and_never_as_a_substring(self):
        for near in ("v1", "12", "release", "foo"):
            with self.subTest(near=near):
                self.assertEqual(self.answered("list", labels=[near])["work"],
                                 [])
        # ...and another spelling of a real key DOES match.
        self.assertEqual(self.answered("list", labels=["V12"])["work"],
                         sorted([WORK, OTHER]))

    def test_a_malformed_filter_operand_refuses_rather_than_matching_nothing(self):
        for bad in ("team=core", "v12,hot", "v12 hot"):
            with self.subTest(bad=bad):
                self.refused("list", labels=[bad])
                self.refused("list", without=[bad])

    def test_every_answer_is_deterministic_json(self):
        """Key-sorted and stable, so two invocations are comparable rather
        than merely both correct."""
        for verb, named in (("labels", {"work": WORK}),
                            ("list", {"labels": ["v12"],
                                      "without": ["archived"]})):
            with self.subTest(verb=verb):
                first = self.run_command(verb, **named)
                self.assertEqual(self.run_command(verb, **named), first)
                body = first[1]
                self.assertEqual(
                    body, json.dumps(json.loads(body), indent=2,
                                     sort_keys=True) + "\n")

    def test_the_read_verbs_never_open_the_store_writably(self):
        """So asking a serving deployment what it carries takes no write lock.

        `Authority.open` is made to fail: the two read verbs still answer, and
        a mutation -- which legitimately needs it -- does not.
        """
        def refuse_open(*arguments, **named):
            raise AssertionError("a read verb opened the store writably")

        with mock.patch.object(Authority, "open", refuse_open):
            self.assertEqual(self.answered("labels", work=WORK)["labels"],
                             ["release-foo", "v12"])
            self.assertEqual(self.answered("list", labels=["v12"])["work"],
                             sorted([WORK, OTHER]))
            self.allow()
            with self.assertRaises(AssertionError):
                self.run_command("label-work", participant=SLAW, work=WORK,
                                 operation_id=self.op(), labels=["hot"])

    def test_the_read_verbs_take_no_participant_and_no_operation_identity(self):
        """They write nothing, so there is no act to attribute or replay."""
        for verb in ("labels", "list"):
            with self.subTest(verb=verb):
                out, err = io.StringIO(), io.StringIO()
                with redirect_stdout(out), redirect_stderr(err):
                    with self.assertRaises(SystemExit):
                        work_command.main(
                            [verb, "--authority-store", self.store,
                             "--authority-uuid", UUID, "--work", WORK,
                             "--participant", SLAW])
                self.assertIn("unrecognized arguments", err.getvalue())


class TheStoreSelectionIsCompared(WorkCommandCase):
    """The two operands every verb takes, and what they refuse."""

    def test_a_wrong_authority_identity_refuses_and_reads_nothing(self):
        """`--authority-uuid` is a compare-and-swap on identity, not a label:
        a deployment that already knows which authority it reads supplies it,
        and being wrong is a refusal rather than a different answer."""
        self.work(WORK, labels=["v12"])
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = work_command.main(
                ["labels", "--authority-store", self.store,
                 "--authority-uuid", "f" * 32, "--work", WORK])
        self.assertEqual(code, 2)
        self.assertIn("refused: ", err.getvalue())
        self.assertEqual(out.getvalue(), "")

    def test_an_absent_store_is_refused_as_a_readable_sentence(self):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = work_command.main(
                ["list", "--authority-store",
                 os.path.join(self._root.name, "nothing.sqlite3"),
                 "--authority-uuid", UUID])
        self.assertEqual(code, 2)
        self.assertIn("refused: ", err.getvalue())

    def test_every_verb_requires_the_store_and_its_identity(self):
        for verb, rest in (("labels", ["--work", WORK]),
                           ("list", []),
                           ("label-work", ["--participant", SLAW, "--work",
                                           WORK, "--operation-id", "op-1",
                                           "--label", "v12"]),
                           ("unlabel-work", ["--participant", SLAW, "--work",
                                             WORK, "--operation-id", "op-1",
                                             "--label", "v12"])):
            with self.subTest(verb=verb):
                out, err = io.StringIO(), io.StringIO()
                with redirect_stdout(out), redirect_stderr(err):
                    with self.assertRaises(SystemExit):
                        work_command.main([verb] + rest)
                self.assertIn("--authority-store", err.getvalue())


if __name__ == "__main__":                                  # pragma: no cover
    unittest.main()
