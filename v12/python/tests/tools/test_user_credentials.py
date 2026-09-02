"""W52821 — the user-scoped credential source, driven through the real seam.

TWO LAYERS, AND THE SECOND ONE IS WHY THIS FILE WAS CORRECTED. Review
2026-09-01T13-04-03Z [P1]: everything this suite claimed about the reader's
place in the deployment was asserted against STAND-INS it defined itself -- a
`_Home` that modelled the manager's materialization order, an argparse parser
that modelled the command's, and documents composed here in the shapes the
command composes them in. Every one of those agreed with the reader by
construction, so the suite could not have failed if the reader and the
production seam had disagreed, which is the only failure that matters.

  THE READER'S OWN RULES are unit-tested directly, because that is what they
  are: a closed registry, an exact selection with no fallback, and a private
  file proved at the descriptor. Nothing else is needed to drive them and
  nothing else is used.
  THE SEAM IS THE PRODUCTION ONE. The cases below that say anything about the
  command or the manager import `tools.dogfood_operator` and
  `baton_v12.worker_manager.credentials` and drive the real
  `argparse` help, the real `main`, the real `_credential_resolver`, the real
  `credentials.resolved_delivery` and the real `CredentialHome.materialize`,
  `Delivery.record`, `written_state` and `tear_down`.

WHAT IS STILL NOT REACHED, and each is a deliberate line rather than an
omission: no provider, no engine, no daemon, no image, no network, no second
worker, and NO REAL CREDENTIAL. Every bearer in this file is a HARMLESS CANARY
-- a string this suite invented, whose only job is to be findable, so that
"the bearer did not reach this document" is a claim a reader can check rather
than take. The manager's §13 registry is the real one, so a canary registered
by a real materialization really does arm the real walk, and two cases prove
that walk refuses while it is live and passes once it is released.

THE ONE THING INJECTED INTO THE MANAGER is `credentials._reader_group`. The
slot's reader group is the deployment's CONFIGURED workspace group, read off a
control store this suite deliberately does not open; the failing paths never
reach the `fchown` that consumes it, and the succeeding ones are given this
process's own gid so the act stays real and local.

AND THE SEAM IS A HARD REQUIREMENT, not a condition. Review
2026-09-01T13-57-01Z [P1]: the imports below sat behind `except Exception` and
turned into a module-wide skip, so the correction that put the production seam
under this suite was itself made optional -- and the ONE outcome a skip cannot
be told apart from is the one that matters, a tree where the manager or the
command genuinely fails to import. `tests/manager/test_credentials.py` imports
the same package at module scope with no guard, and every module in
`tools/parallel_test.py`'s pure phase is run the same way; a suite whose whole
subject is that seam may not hold itself to less. So they are imported flatly:
an unimportable manager or command FAILS this module, loudly, at collection.

NOTHING GLOBAL, ANYWHERE. Every case owns its own temporary tree, its own
registry, its own reader, its own credential home and its own attempt ids, and
the two-context case releases both contexts into the reader at the same
instant so their reads genuinely overlap. A shared cache or a singleton reader
would hand one context the other's canary; a lock held across calls would
leave a thread that never finishes. Both are asserted rather than assumed.
"""

import argparse
import contextlib
import errno
import io
import json
import os
import shutil
import stat
import tempfile
import threading
import unittest
from unittest import mock

from tools import user_credentials

# -- the production seam, imported the way every other module imports it -------
#
# NO GUARD, NO FALLBACK AND NO SKIP. There is no stand-in here because a
# stand-in for `CredentialHome` is exactly the evidence the previous review
# rejected -- and there is no `try` here because a guard around the import is
# the same defect one layer out: it turns "the two ends disagree" and "the two
# ends could not be brought together" into one green result. These three
# imports are requirements of this module, and a tree that cannot satisfy them
# fails it.
from baton_v12.contracts import ContractRefusal, check_no_durable_secret
from baton_v12.worker_manager import credentials
from tools import dogfood_operator


# -- the operator's own two documents, in the closed shapes the command reads --
#
# COMPOSED HERE, HELD BY THE COMMAND. These are not a model of `read_grants`
# and `read_evidence`: they are operands handed TO them, and a case below
# asserts each names exactly the closed member set the command exports, so a
# member added upstream makes this suite fail rather than quietly stop
# exercising the door.

def _grants(**changed):
    given = {
        "engine": "docker",
        "attempt_id": "attempt-w52821-seam",
        "offer_id": "offer-w52821-seam",
        "source": "/nonexistent/source",
        "task_path": "/nonexistent/task.json",
        "storage": "/nonexistent/storage",
        "launch_home": "/nonexistent/launch-home",
        "control_store": "/nonexistent/control.sqlite3",
        "authority_store": "/nonexistent/authority.sqlite3",
        "incarnation": "dogfood-w52821",
        "credential_home": "/nonexistent/credential-home",
        "credential_slots": ["provider-token"],
        "credential_profile": {
            "provider-token": {"provider": "acme-vault",
                               "reference": "op://vault/one"}},
        "image_digest": "sha256:" + "0" * 64,
        "network": "baton-dogfood",
        "review_route": "rview",
        "retention_disposition": "retain",
        "work_ref": {"authority_uuid": "authority-w52821",
                     "work_id": "W52821"},
        "participant": "team.member",
        "generation": 1,
        "now": "2026-09-01T00:00:00.000Z",
        "policies": {"policy_digest": "sha256:" + "1" * 64},
        "record_binding": {"root": "/nonexistent/records",
                           "path": "work/records/W52821"},
        "assignment_contract": "assignment-contract-w52821",
        "human_contract": {"summary": "one bounded dogfood task"},
        "role_instructions_digest": "sha256:" + "2" * 64,
        "runtime_profile_digest": "sha256:" + "3" * 64,
        "toolchain_digest": "sha256:" + "4" * 64,
        "adapter_digest": "sha256:" + "5" * 64,
        "adapter_name": "oci",
        "labels": {"attempt": "w52821"},
        "retention_policy_digest": "sha256:" + "6" * 64,
    }
    given.update(changed)
    return given


def _evidence(**changed):
    """A retained record that AGREES with `_grants`, so `_bound` is the test.

    Every member `_RETRY_BINDING` compares is taken from the same place the
    grants take it, and the committed retention agrees too -- so a case that
    crosses one context's record with another context's grants is measuring
    the identities it changed and nothing else.
    """
    record = {
        "schema": "baton.dogfood-evidence/1",
        "attempt_id": "attempt-w52821-seam",
        "task_id": "task-w52821",
        "input_manifest_digest": "sha256:" + "7" * 64,
        "assignment_manifest_digest": "sha256:" + "8" * 64,
        "source_tree_digest": "sha256:" + "9" * 64,
        "worker_image_digest": "sha256:" + "0" * 64,
        "network": "baton-dogfood",
        "runtime_id": "runtime-w52821-seam",
        "offer_id": "offer-w52821-seam",
        "conversation": {"turns": 1},
        "worker_disposition": "completed",
        "output": {"frozen": True},
        "cleanup": {"lifecycle_state": "torn-down"},
        "independent": {"verified": True},
        "resolved": True,
        "unresolved": None,
        "retention": {"disposition": "retain"},
        "review_route": "rview",
        "retention_policy_digest": "sha256:" + "6" * 64,
        "work_ref": {"authority_uuid": "authority-w52821",
                     "work_id": "W52821"},
        "participant": "team.member",
        "generation": 1,
        "quiescence": {"observed": True},
        "intake_receipt": {"accepted": True},
        "custody": {"locator": "custody-w52821"},
        "review_pass": None,
        "abandoned": None,
        "observed_after": {"runtime": "absent"},
    }
    record.update(changed)
    return record


class _BuilderReached(Exception):
    """Raised by a sentinel builder, so a case can say WHERE it got to.

    The ending-mode cases need two different answers from one command: the
    contradiction is refused BEFORE any builder acts, and the same command
    without the operand reaches its builder. A sentinel that raises this is
    the second half; a sentinel that is never called is the first.
    """


class _Counting:
    """The real reader, with every selection the manager asked it for recorded.

    A SPY AND NOT A STAND-IN. It forwards to the reader under test and adds
    nothing to it; what it exists for is the two claims the reader alone
    cannot make -- that the manager asked with the EXACT pair its own
    `resolved_delivery` produced, and that it had asked nothing at all before
    the delivery was materialized.
    """

    def __init__(self, inner, before=None):
        self.inner = inner
        self.calls = []
        self.before = before

    def __call__(self, provider, reference):
        self.calls.append((provider, reference))
        if self.before is not None:
            self.before()
        return self.inner(provider, reference)


class _Fixture(unittest.TestCase):
    """One disposable private tree per case, and no name shared with any other."""

    def setUp(self):
        self.home = tempfile.mkdtemp(prefix="w52821-user-credentials-")
        self.addCleanup(shutil.rmtree, self.home, ignore_errors=True)

    # -- private material -----------------------------------------------------

    def private_at(self, place, body):
        """A file this user owns, at exactly 0600, created without following."""
        os.makedirs(os.path.dirname(place), exist_ok=True)
        raw = body.encode("utf-8") if isinstance(body, str) else body
        handle = os.open(place, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        try:
            written = 0
            while written < len(raw):
                written += os.write(handle, raw[written:])
        finally:
            os.close(handle)
        os.chmod(place, 0o600)
        return place

    def private(self, name, body):
        return self.private_at(os.path.join(self.home, name), body)

    def registry_at(self, place, sources, *, schema=user_credentials.SCHEMA,
                    extra=None, drop=()):
        document = {"schema": schema, "sources": sources}
        for one in drop:
            document.pop(one, None)
        if extra:
            document.update(extra)
        return self.private_at(place, json.dumps(document))

    def registry(self, name, sources, **named):
        return self.registry_at(os.path.join(self.home, name), sources,
                                **named)

    def resolver(self, place, *, max_bearer=4096):
        return user_credentials.UserCredentialSources(place,
                                                      max_bearer=max_bearer)

    def written(self, name, document):
        """An ordinary operator-written document. Not private, on purpose."""
        place = os.path.join(self.home, name)
        with open(place, "w", encoding="utf-8") as writing:
            json.dump(document, writing)
        return place

    # -- the two assertions this whole slice turns on -------------------------

    def assertNamesNoPath(self, refusal):
        """A refusal is prose, and prose travels. No host path rides in one."""
        self.assertNotIn(self.home, str(refusal))

    def refusing(self):
        return self.assertRaises(user_credentials.SourceRefusal)


# -- the closed registry ---------------------------------------------------------


class TheRegistryIsClosedAndBounded(_Fixture):
    """`baton.user-credential-sources/1`, held as a whole before a source opens."""

    def one_source(self, **changed):
        source = {"provider": "acme-vault", "reference": "opaque/ref/1",
                  "path": os.path.join(self.home, "material.txt")}
        source.update(changed)
        return source

    def held(self, **changed):
        return user_credentials.held_registry(
            {"schema": user_credentials.SCHEMA,
             "sources": [self.one_source(**changed)]})

    def test_the_documented_registry_is_read(self):
        held = user_credentials.held_registry(
            {"schema": user_credentials.SCHEMA,
             "sources": [self.one_source()]})
        self.assertEqual(
            held,
            ({"provider": "acme-vault", "reference": "opaque/ref/1",
              "path": os.path.join(self.home, "material.txt")},))

    def test_a_registry_that_is_not_a_document_is_refused(self):
        for value in ([], "sources", None, 7):
            with self.refusing():
                user_credentials.held_registry(value)

    def test_an_unexpected_member_is_refused(self):
        with self.refusing() as caught:
            user_credentials.held_registry(
                {"schema": user_credentials.SCHEMA,
                 "sources": [self.one_source()],
                 "default_source": "/anywhere"})
        self.assertIn("unexpected default_source", str(caught.exception))

    def test_a_missing_member_is_refused(self):
        with self.refusing() as caught:
            user_credentials.held_registry({"sources": [self.one_source()]})
        self.assertIn("missing schema", str(caught.exception))

    def test_another_generation_is_refused_rather_than_interpreted(self):
        with self.refusing() as caught:
            user_credentials.held_registry(
                {"schema": "baton.user-credential-sources/2",
                 "sources": [self.one_source()]})
        self.assertIn(user_credentials.SCHEMA, str(caught.exception))

    def test_sources_are_a_list_and_never_a_document(self):
        with self.refusing():
            user_credentials.held_registry(
                {"schema": user_credentials.SCHEMA,
                 "sources": {"acme-vault": self.one_source()}})

    def test_a_registry_naming_nothing_is_refused(self):
        with self.refusing() as caught:
            user_credentials.held_registry(
                {"schema": user_credentials.SCHEMA, "sources": []})
        self.assertIn("at least one source", str(caught.exception))

    def test_more_sources_than_the_bound_are_refused(self):
        many = [self.one_source(reference=f"opaque-{index}")
                for index in range(user_credentials.MAX_SOURCES + 1)]
        with self.refusing() as caught:
            user_credentials.held_registry(
                {"schema": user_credentials.SCHEMA, "sources": many})
        self.assertIn(str(user_credentials.MAX_SOURCES),
                      str(caught.exception))
        # ...and exactly the bound is not the bound plus one.
        user_credentials.held_registry(
            {"schema": user_credentials.SCHEMA,
             "sources": many[:user_credentials.MAX_SOURCES]})

    def test_a_source_entry_is_exactly_three_members(self):
        for entry in ({"provider": "acme-vault", "reference": "opaque"},
                      {"provider": "acme-vault", "path": "/a/b"},
                      {"reference": "opaque", "path": "/a/b"},
                      dict(self.one_source(), bearer="canary-never-here")):
            with self.refusing():
                user_credentials.held_registry(
                    {"schema": user_credentials.SCHEMA, "sources": [entry]})

    # -- the provider and the reference, in the manager's own shape ------------
    #
    # Review 2026-09-01T13-04-03Z [P1]. The cases these replace asserted a
    # grammar this reader INVENTED -- 64 characters of alphanumerics, dot, dash
    # and underscore for a provider, 512 characters and no control characters
    # for a reference. Nothing said either, and asserting them made the
    # invention look ruled. What is asserted now is the manager's own hold:
    # exact non-empty encodable text, at both ends of one pair.

    def test_a_provider_is_the_manager_s_shape_and_nothing_narrower(self):
        for provider in ("acme-vault", "vault/team", "acme vault", ".acme",
                         "ACME:Vault", "храни-лище", "a" * 4096):
            self.assertEqual(self.held(provider=provider)[0]["provider"],
                             provider)

    def test_a_provider_that_is_not_text_at_all_is_refused(self):
        for provider in ("", None, 7, [], {}, b"acme", "\ud800"):
            with self.refusing():
                self.held(provider=provider)

    def test_a_reference_is_opaque_and_carries_no_width_of_its_own(self):
        # ANY opaque spelling is accepted: this reader never reads a meaning
        # out of a reference, and the registry document's own 64 KiB bound at
        # the read is the only thing that bounds one.
        for reference in ("op://vault/item", "{json:like}", "1", " ",
                          "with\nnewline", "a" * 513, "b" * 4096):
            self.assertEqual(self.held(reference=reference)[0]["reference"],
                             reference)

    def test_a_reference_that_is_not_text_at_all_is_refused(self):
        for reference in ("", None, [], 7, "\ud800"):
            with self.refusing():
                self.held(reference=reference)

    def test_a_path_is_absolute_canonical_bounded_text(self):
        for path in ("relative/material.txt", "/a/../../etc/shadow", "", None,
                     "/" + "a" * user_credentials.MAX_PATH, "/a/\x00/b"):
            with self.refusing() as caught:
                self.held(path=path)
            self.assertNamesNoPath(caught.exception)

    def test_a_registry_wider_than_the_bound_is_refused_at_the_read(self):
        place = self.private("enormous.json",
                             "x" * (user_credentials.MAX_REGISTRY_BYTES + 1))
        with self.refusing() as caught:
            self.resolver(place).resolve("acme-vault", "opaque")
        self.assertIn("wider than", str(caught.exception))
        self.assertNamesNoPath(caught.exception)

    def test_a_registry_that_is_not_json_is_refused(self):
        place = self.private("broken.json", "{not json at all")
        with self.refusing() as caught:
            self.resolver(place).resolve("acme-vault", "opaque")
        self.assertIn("one JSON document", str(caught.exception))
        self.assertNamesNoPath(caught.exception)

    def test_the_manager_s_own_bearer_bound_is_a_required_operand(self):
        for bound in (None, "4096", 0, -1, True):
            with self.refusing():
                user_credentials.UserCredentialSources("/a/b",
                                                       max_bearer=bound)


# -- selection --------------------------------------------------------------------


class SelectionIsExactAndHasNoFallback(_Fixture):
    """The provider AND the reference, together, or a refusal."""

    def setUp(self):
        super().setUp()
        self.first = self.private("first.txt", "canary-first-9f2a")
        self.second = self.private("second.txt", "canary-second-4c71")
        self.third = self.private("third.txt", "canary-third-0b83")
        self.place = self.registry("sources.json", [
            {"provider": "acme-vault", "reference": "op://vault/first",
             "path": self.first},
            {"provider": "acme-vault", "reference": "op://vault/second",
             "path": self.second},
            {"provider": "other-broker", "reference": "op://vault/first",
             "path": self.third}])

    def test_each_exact_pair_resolves_to_its_own_source(self):
        reading = self.resolver(self.place)
        self.assertEqual(reading.resolve("acme-vault", "op://vault/first"),
                         "canary-first-9f2a")
        self.assertEqual(reading.resolve("acme-vault", "op://vault/second"),
                         "canary-second-4c71")
        self.assertEqual(reading.resolve("other-broker", "op://vault/first"),
                         "canary-third-0b83")

    def test_the_resolver_is_the_provider_callable_the_manager_asks(self):
        # `CredentialHome.materialize` calls `provider(identity, reference)`.
        # Being that callable is what keeps the two operands from being
        # discarded at the seam, which is the defect this slice replaces.
        reading = self.resolver(self.place)
        self.assertEqual(reading("acme-vault", "op://vault/second"),
                         "canary-second-4c71")

    def test_a_pair_the_manager_s_shape_admits_resolves_here_too(self):
        # The same widening the registry hold was corrected for, at the
        # SELECTION: a provider with a slash and a reference wider than the
        # 512 characters this reader used to invent are ordinary values.
        wide = "op://" + "wide-" * 200
        source = self.private("wide.txt", "canary-wide-pair-3311")
        place = self.registry("wide-sources.json", [
            {"provider": "vault/team", "reference": wide, "path": source}])
        self.assertGreater(len(wide), 512)
        self.assertEqual(self.resolver(place).resolve("vault/team", wide),
                         "canary-wide-pair-3311")

    def test_the_same_reference_under_another_provider_is_another_source(self):
        reading = self.resolver(self.place)
        self.assertNotEqual(
            reading.resolve("acme-vault", "op://vault/first"),
            reading.resolve("other-broker", "op://vault/first"))

    def test_an_unknown_reference_does_not_fall_back_to_the_provider(self):
        with self.refusing() as caught:
            self.resolver(self.place).resolve("acme-vault", "op://vault/none")
        self.assertIn("no fallback", str(caught.exception))
        self.assertNamesNoPath(caught.exception)

    def test_an_unknown_provider_does_not_fall_back_to_the_reference(self):
        with self.refusing() as caught:
            self.resolver(self.place).resolve("third-broker",
                                              "op://vault/first")
        self.assertIn("no fallback", str(caught.exception))

    def test_a_single_entry_registry_is_not_a_default_source(self):
        lone = self.registry("lone.json", [
            {"provider": "acme-vault", "reference": "op://vault/only",
             "path": self.first}])
        with self.refusing() as caught:
            self.resolver(lone).resolve("acme-vault", "op://vault/other")
        self.assertIn("not the only entry", str(caught.exception))

    def test_no_operand_refuses_where_the_credential_is_asked_for(self):
        # `None` is an ordinary construction: an attempt that never reaches
        # activation must never learn that it would have had no source.
        reading = self.resolver(None)
        with self.refusing() as caught:
            reading.resolve("acme-vault", "op://vault/first")
        self.assertIn(user_credentials.OPERAND, str(caught.exception))

    def test_an_empty_source_is_not_a_credential(self):
        empty = self.private("empty.txt", "   \n")
        place = self.registry("empty-registry.json", [
            {"provider": "acme-vault", "reference": "op://vault/empty",
             "path": empty}])
        with self.refusing() as caught:
            self.resolver(place).resolve("acme-vault", "op://vault/empty")
        self.assertIn("empty", str(caught.exception))
        self.assertNamesNoPath(caught.exception)

    def test_the_surrounding_newline_an_editor_adds_is_not_the_secret(self):
        padded = self.private("padded.txt", "\ncanary-padded-77aa\n")
        place = self.registry("padded-registry.json", [
            {"provider": "acme-vault", "reference": "op://vault/padded",
             "path": padded}])
        self.assertEqual(
            self.resolver(place).resolve("acme-vault", "op://vault/padded"),
            "canary-padded-77aa")


class AmbiguityRefusesRatherThanChoosing(_Fixture):
    """Two sources for one pair does not say which file backs it."""

    def setUp(self):
        super().setUp()
        self.first = self.private("first.txt", "canary-first-1111")
        self.second = self.private("second.txt", "canary-second-2222")

    def test_a_duplicated_pair_is_refused(self):
        place = self.registry("sources.json", [
            {"provider": "acme-vault", "reference": "op://vault/one",
             "path": self.first},
            {"provider": "acme-vault", "reference": "op://vault/one",
             "path": self.second}])
        with self.refusing() as caught:
            self.resolver(place).resolve("acme-vault", "op://vault/one")
        self.assertIn("twice", str(caught.exception))
        self.assertNamesNoPath(caught.exception)

    def test_a_duplicate_elsewhere_refuses_the_whole_registry(self):
        # A registry that is ambiguous about ANY pair is a registry this
        # reader cannot state; refusing only the selected pair would deliver
        # out of a document whose meaning nobody can say.
        place = self.registry("sources.json", [
            {"provider": "acme-vault", "reference": "op://vault/unique",
             "path": self.first},
            {"provider": "other-broker", "reference": "op://vault/dup",
             "path": self.first},
            {"provider": "other-broker", "reference": "op://vault/dup",
             "path": self.second}])
        with self.refusing() as caught:
            self.resolver(place).resolve("acme-vault", "op://vault/unique")
        self.assertIn("twice", str(caught.exception))

    def test_one_file_may_back_two_distinct_pairs(self):
        # Two pairs sharing a file is not ambiguity: each pair still names
        # exactly one source.
        place = self.registry("sources.json", [
            {"provider": "acme-vault", "reference": "op://vault/a",
             "path": self.first},
            {"provider": "acme-vault", "reference": "op://vault/b",
             "path": self.first}])
        reading = self.resolver(place)
        self.assertEqual(reading.resolve("acme-vault", "op://vault/a"),
                         "canary-first-1111")
        self.assertEqual(reading.resolve("acme-vault", "op://vault/b"),
                         "canary-first-1111")


# -- a large opaque selection: exact at the match, opaque in the prose ------------


class ALargeOpaqueSelectionIsExactAndIsNeverQuotedBack(_Fixture):
    """The two properties of one pair, at a width that makes them separable.

    Review 2026-09-01T13-57-01Z [P1]. Widening this reader to the manager's own
    shape -- exact non-empty encodable text, with no character class and no
    width of its own -- was correct and it removed the ceiling that had been
    bounding this module's refusal prose by accident. Every refusal about a
    selection interpolated `{provider!r}` and `{reference!r}`, so a deployment
    whose trusted profile legitimately maps a slot to a multi-kilobyte opaque
    reference put that reference into a sentence an operator's terminal, a
    report and anything else that carried one would then hold.

    A PREFIX WOULD NOT HAVE BEEN A FIX. A reference is opaque exactly because
    neither end reads a meaning out of it, so neither end can say which of its
    bytes are the harmless ones -- and the leading bytes of an opaque value are
    the ones a naming scheme makes identifying.

    SO THERE ARE TWO CLAIMS HERE AND THEY PULL IN OPPOSITE DIRECTIONS, which is
    why both are driven by the same fixture. The MATCH still uses each value
    whole -- a neighbour differing in its LAST byte alone resolves to a
    different file -- while the PROSE names one fixed label and two widths and
    nothing that came out of the registry or the profile.
    """

    # FAR WIDER THAN ANYTHING A REFUSAL COULD SUMMARIZE, and still inside the
    # registry document's own 64 KiB bound, so what these drive is the
    # selection and the prose rather than `MAX_REGISTRY_BYTES`.
    PROVIDER = "vault/team/" + "p" * 4000
    REFERENCE = "op://baton/" + "r" * 8000
    # THE SAME WIDTH, ONE BYTE APART, AND APART AT THE END. A reader that
    # matched on a prefix, a width or a provider alone would answer this one
    # with the other one's file.
    NEIGHBOUR = "op://baton/" + "r" * 7999 + "s"

    EXACT = "canary-large-exact-3f70"
    OTHER = "canary-large-neighbour-91c4"

    # WHAT "BOUNDED" MEANS HERE, as a number rather than as a word. Every
    # refusal below is the same length whatever the pair is, so a ceiling well
    # under the smaller of the two values is a real measurement.
    BOUND = 512

    def setUp(self):
        super().setUp()
        self.exact = self.private("exact.txt", self.EXACT)
        self.other = self.private("neighbour.txt", self.OTHER)
        self.place = self.registry("sources.json", [
            {"provider": self.PROVIDER, "reference": self.NEIGHBOUR,
             "path": self.other},
            {"provider": self.PROVIDER, "reference": self.REFERENCE,
             "path": self.exact}])

    def assertBoundedSelectionRefusal(self, caught, provider, reference):
        """One fixed label, two widths, and nothing either value contributed."""
        message = str(caught.exception)
        # THIS READER'S OWN TYPE. An `OSError` or a `UnicodeError` crossing
        # here would carry text nothing in this module composed.
        self.assertIsInstance(caught.exception,
                              user_credentials.SourceRefusal)
        self.assertIn(f"a provider identity and opaque reference of "
                      f"{len(provider.encode('utf-8'))} and "
                      f"{len(reference.encode('utf-8'))} encoded bytes",
                      message)
        # NEITHER VALUE, AND NO PREFIX OF EITHER. Both are built out of one
        # repeated fill character that this module's prose cannot produce, so
        # a single run of eight is a quotation however short it is.
        self.assertNotIn("p" * 8, message)
        self.assertNotIn("r" * 8, message)
        self.assertNotIn(provider, message)
        self.assertNotIn(reference, message)
        self.assertNotIn(provider[:64], message)
        self.assertNotIn(reference[:64], message)
        self.assertLess(len(message), self.BOUND)
        self.assertNamesNoPath(caught.exception)

    def test_the_two_wide_references_really_do_differ_by_one_last_byte(self):
        # NOT A TAUTOLOGY GUARD FOR ITS OWN SAKE: if these two ever stopped
        # agreeing on everything but their final byte, the exact-selection
        # case below would still pass and would prove nothing about exactness.
        self.assertEqual(len(self.REFERENCE), len(self.NEIGHBOUR))
        self.assertEqual(self.REFERENCE[:-1], self.NEIGHBOUR[:-1])
        self.assertNotEqual(self.REFERENCE, self.NEIGHBOUR)
        self.assertGreater(len(self.PROVIDER), 512)
        self.assertGreater(len(self.REFERENCE), 4096)

    def test_each_wide_pair_selects_its_own_source_exactly(self):
        reading = self.resolver(self.place)
        self.assertEqual(reading.resolve(self.PROVIDER, self.REFERENCE),
                         self.EXACT)
        self.assertEqual(reading.resolve(self.PROVIDER, self.NEIGHBOUR),
                         self.OTHER)

    def test_the_resolver_callable_selects_the_wide_pair_too(self):
        # `CredentialHome.materialize` asks `provider(identity, reference)`,
        # and the width of what it asks with is not this reader's business.
        self.assertEqual(self.resolver(self.place)(self.PROVIDER,
                                                   self.REFERENCE),
                         self.EXACT)

    def test_an_unknown_wide_pair_refuses_without_quoting_either_value(self):
        unknown = self.REFERENCE + "r"
        with self.refusing() as caught:
            self.resolver(self.place).resolve(self.PROVIDER, unknown)
        self.assertIn("no fallback", str(caught.exception))
        self.assertBoundedSelectionRefusal(caught, self.PROVIDER, unknown)

    def test_a_wide_pair_under_an_unknown_provider_refuses_the_same_way(self):
        other = self.PROVIDER + "p"
        with self.refusing() as caught:
            self.resolver(self.place).resolve(other, self.REFERENCE)
        self.assertIn("no fallback", str(caught.exception))
        self.assertBoundedSelectionRefusal(caught, other, self.REFERENCE)

    def test_a_duplicated_wide_pair_refuses_without_quoting_it(self):
        place = self.registry("duplicated.json", [
            {"provider": self.PROVIDER, "reference": self.REFERENCE,
             "path": self.exact},
            {"provider": self.PROVIDER, "reference": self.REFERENCE,
             "path": self.other}])
        with self.refusing() as caught:
            self.resolver(place).resolve(self.PROVIDER, self.REFERENCE)
        self.assertIn("twice", str(caught.exception))
        self.assertBoundedSelectionRefusal(caught, self.PROVIDER,
                                           self.REFERENCE)

    def test_a_wide_pair_with_no_operand_refuses_without_quoting_it(self):
        with self.refusing() as caught:
            self.resolver(None).resolve(self.PROVIDER, self.REFERENCE)
        self.assertIn(user_credentials.OPERAND, str(caught.exception))
        self.assertBoundedSelectionRefusal(caught, self.PROVIDER,
                                           self.REFERENCE)

    def test_a_wide_pair_whose_source_is_not_private_refuses_boundedly(self):
        # THE DESCRIPTOR PROOF'S OWN REFUSALS carry the selection label too,
        # because they are composed from the same `what`.
        os.chmod(self.exact, 0o640)
        with self.refusing() as caught:
            self.resolver(self.place).resolve(self.PROVIDER, self.REFERENCE)
        self.assertIn("no group and no other permission",
                      str(caught.exception))
        self.assertBoundedSelectionRefusal(caught, self.PROVIDER,
                                           self.REFERENCE)

    def test_a_wide_pair_whose_source_is_absent_refuses_boundedly(self):
        os.remove(self.exact)
        with self.refusing() as caught:
            self.resolver(self.place).resolve(self.PROVIDER, self.REFERENCE)
        self.assertIn("ordinary private file", str(caught.exception))
        self.assertBoundedSelectionRefusal(caught, self.PROVIDER,
                                           self.REFERENCE)

    def test_a_wide_pair_whose_source_is_empty_refuses_boundedly(self):
        empty = self.private("empty.txt", "   \n")
        place = self.registry("empty.json", [
            {"provider": self.PROVIDER, "reference": self.REFERENCE,
             "path": empty}])
        with self.refusing() as caught:
            self.resolver(place).resolve(self.PROVIDER, self.REFERENCE)
        self.assertIn("empty", str(caught.exception))
        self.assertBoundedSelectionRefusal(caught, self.PROVIDER,
                                           self.REFERENCE)

    def test_a_wide_source_over_the_bearer_bound_names_no_part_of_either(self):
        wide = self.private("wide.txt", "canary-over-bound-" + "z" * 400)
        place = self.registry("over.json", [
            {"provider": self.PROVIDER, "reference": self.REFERENCE,
             "path": wide}])
        with self.refusing() as caught:
            self.resolver(place, max_bearer=64).resolve(self.PROVIDER,
                                                        self.REFERENCE)
        self.assertIn("wider than", str(caught.exception))
        self.assertNotIn("canary-over-bound-", str(caught.exception))
        self.assertBoundedSelectionRefusal(caught, self.PROVIDER,
                                           self.REFERENCE)

    def test_the_width_a_refusal_names_is_encoded_bytes(self):
        # BYTES AND NOT CHARACTERS. `MAX_REGISTRY_BYTES` is stated over the
        # same document in bytes, so the number an operator reads out of a
        # refusal and the number this reader enforces are in one unit.
        provider = "хранилище-команды"
        reference = "op://" + "🔑" * 64
        with self.refusing() as caught:
            self.resolver(None).resolve(provider, reference)
        message = str(caught.exception)
        self.assertGreater(len(provider.encode("utf-8")), len(provider))
        self.assertIn(f"{len(provider.encode('utf-8'))} and "
                      f"{len(reference.encode('utf-8'))} encoded bytes",
                      message)
        self.assertNotIn(provider, message)
        self.assertNotIn(reference, message)
        self.assertNotIn("🔑", message)


# -- the private-file proof --------------------------------------------------------


class EveryReadIsProvedAtTheDescriptor(_Fixture):
    """No final symlink, an ordinary file, this user's, and nobody else's."""

    def setUp(self):
        super().setUp()
        self.material = self.private("material.txt", "canary-proved-5e10")

    def registry_naming(self, path, name="sources.json"):
        return self.registry(name, [
            {"provider": "acme-vault", "reference": "op://vault/one",
             "path": path}])

    def resolving(self, place):
        return self.resolver(place).resolve("acme-vault", "op://vault/one")

    # -- injecting a failure at EXACTLY one descriptor -------------------------
    #
    # BY INODE, so the registry read and the source read can be failed
    # independently and everything else in the process keeps working. The real
    # `os.fstat` is captured before the patch, so the predicate that decides
    # which descriptor to fail is never the thing being sabotaged.

    def failing_fstat(self, place):
        real = os.fstat
        target = os.stat(place).st_ino

        def injected(handle, *rest):
            found = real(handle, *rest)
            if found.st_ino == target:
                raise OSError(errno.EIO, "injected at fstat")
            return found

        return mock.patch("os.fstat", injected)

    def failing_read(self, place, *, after=0):
        real_read = os.read
        real_fstat = os.fstat
        target = os.stat(place).st_ino
        seen = []

        def injected(handle, count):
            if real_fstat(handle).st_ino == target:
                seen.append(count)
                if len(seen) > after:
                    raise OSError(errno.EIO, "injected at read")
            return real_read(handle, count)

        return mock.patch("os.read", injected)

    def assertBoundedDescriptorRefusal(self, caught, expected):
        """One of this reader's own outcomes, and NOT one of the other four.

        The value of the correction is that the four rules around the two
        translated acts still answer for themselves: an I/O error is not
        reported as "not an ordinary file", as somebody else's ownership or as
        a widened mode, because reading any of those out of an `EIO` would
        send an operator to change a file that is exactly as they left it.
        """
        message = str(caught.exception)
        self.assertIn(expected, message)
        self.assertIn("OSError", message)
        self.assertNamesNoPath(caught.exception)
        for other in ("not an ordinary file", "does not own",
                      "no group and no other permission",
                      "could not be opened"):
            self.assertNotIn(other, message)

    def test_a_final_symlink_at_the_source_is_refused(self):
        linked = os.path.join(self.home, "linked.txt")
        os.symlink(self.material, linked)
        with self.refusing() as caught:
            self.resolving(self.registry_naming(linked))
        self.assertIn("ordinary private file", str(caught.exception))
        self.assertNamesNoPath(caught.exception)

    def test_a_final_symlink_at_the_registry_is_refused(self):
        real = self.registry_naming(self.material, name="real.json")
        linked = os.path.join(self.home, "linked.json")
        os.symlink(real, linked)
        with self.refusing() as caught:
            self.resolving(linked)
        self.assertIn("ordinary private file", str(caught.exception))

    def test_a_source_that_is_not_a_regular_file_is_refused(self):
        directory = os.path.join(self.home, "a-directory")
        os.mkdir(directory, 0o700)
        with self.refusing() as caught:
            self.resolving(self.registry_naming(directory))
        self.assertIn("not an ordinary file", str(caught.exception))
        self.assertNamesNoPath(caught.exception)

    def test_a_source_that_is_a_pipe_is_refused_without_blocking(self):
        pipe = os.path.join(self.home, "a-pipe")
        os.mkfifo(pipe, 0o600)
        with self.refusing() as caught:
            self.resolving(self.registry_naming(pipe))
        self.assertIn("not an ordinary file", str(caught.exception))

    def test_a_source_this_user_does_not_own_is_refused(self):
        place = self.registry_naming(self.material)
        found = os.stat(self.material)
        with mock.patch("os.geteuid", return_value=found.st_uid + 1):
            with self.refusing() as caught:
                self.resolving(place)
        self.assertIn("does not own", str(caught.exception))
        self.assertNamesNoPath(caught.exception)

    def test_a_group_readable_source_is_refused(self):
        os.chmod(self.material, 0o640)
        with self.refusing() as caught:
            self.resolving(self.registry_naming(self.material))
        self.assertIn("no group and no other permission",
                      str(caught.exception))
        self.assertNamesNoPath(caught.exception)

    def test_a_world_readable_source_is_refused(self):
        os.chmod(self.material, 0o604)
        with self.refusing():
            self.resolving(self.registry_naming(self.material))

    def test_a_group_readable_registry_is_refused(self):
        place = self.registry_naming(self.material)
        os.chmod(place, 0o644)
        with self.refusing() as caught:
            self.resolving(place)
        self.assertIn("no group and no other permission",
                      str(caught.exception))

    def test_an_absent_source_is_refused(self):
        absent = os.path.join(self.home, "not-here.txt")
        with self.refusing() as caught:
            self.resolving(self.registry_naming(absent))
        self.assertIn("ordinary private file", str(caught.exception))
        self.assertNamesNoPath(caught.exception)

    def test_an_absent_registry_is_refused(self):
        with self.refusing() as caught:
            self.resolving(os.path.join(self.home, "no-registry.json"))
        self.assertIn("ordinary private file", str(caught.exception))

    @unittest.skipIf(os.geteuid() == 0,
                     "root reads a mode 0200 file, so the refusal this case "
                     "drives cannot happen for it")
    def test_an_unreadable_source_is_refused(self):
        os.chmod(self.material, 0o200)
        with self.refusing() as caught:
            self.resolving(self.registry_naming(self.material))
        self.assertIn("ordinary private file", str(caught.exception))
        self.assertNamesNoPath(caught.exception)

    # -- the two acts AFTER the open, which used to escape as `OSError` --------
    #
    # Review 2026-09-01T13-04-03Z [P1]. The open was translated into a
    # `SourceRefusal` and `os.fstat` and `os.read` on the proved descriptor
    # were not, so an I/O error on the user's own file left a bare `OSError`
    # crossing a door the command translates only `SourceRefusal` at -- and an
    # `OSError`'s own text carries `strerror` AND THE FILENAME, which is the
    # one thing no refusal in this module may name.

    def test_an_fstat_that_fails_on_the_registry_is_a_bounded_refusal(self):
        place = self.registry_naming(self.material)
        with self.failing_fstat(place):
            with self.refusing() as caught:
                self.resolving(place)
        self.assertBoundedDescriptorRefusal(caught,
                                            "could not be interrogated")

    def test_an_fstat_that_fails_on_the_source_is_a_bounded_refusal(self):
        place = self.registry_naming(self.material)
        with self.failing_fstat(self.material):
            with self.refusing() as caught:
                self.resolving(place)
        self.assertBoundedDescriptorRefusal(caught,
                                            "could not be interrogated")
        # ...and it says WHICH OF THE TWO FILES it was about -- the source
        # rather than the registry -- WITHOUT naming either of the two values
        # that chose it. Review 2026-09-01T13-57-01Z [P1]: this used to assert
        # `acme-vault` and `op://vault/one` in the prose, which made a
        # requirement out of copying an opaque value of unbounded width into a
        # sentence that travels. The fixed label and the two widths are what
        # distinguish the source's refusal from the registry's now.
        message = str(caught.exception)
        self.assertIn("the credential source for a provider identity and "
                      "opaque reference of", message)
        self.assertIn(f"{len('acme-vault')} and {len('op://vault/one')} "
                      f"encoded bytes", message)
        self.assertNotIn("acme-vault", message)
        self.assertNotIn("op://vault/one", message)

    def test_a_read_that_fails_on_the_registry_is_a_bounded_refusal(self):
        place = self.registry_naming(self.material)
        with self.failing_read(place):
            with self.refusing() as caught:
                self.resolving(place)
        self.assertBoundedDescriptorRefusal(caught, "could not be read")

    def test_a_read_that_fails_on_the_source_is_a_bounded_refusal(self):
        place = self.registry_naming(self.material)
        with self.failing_read(self.material):
            with self.refusing() as caught:
                self.resolving(place)
        self.assertBoundedDescriptorRefusal(caught, "could not be read")

    def test_a_read_that_fails_PART_WAY_delivers_no_prefix(self):
        # The first chunk really is read and then the descriptor fails, which
        # is the shape a truncated credential would come out of. What comes
        # out instead is a refusal, and the bytes that were read are dropped
        # rather than answered.
        place = self.registry_naming(self.material)
        with self.failing_read(self.material, after=1):
            with self.refusing() as caught:
                self.resolving(place)
        self.assertBoundedDescriptorRefusal(caught, "could not be read")
        self.assertNotIn("canary-proved-", str(caught.exception))

    def test_a_source_wider_than_the_bearer_bound_is_refused_whole(self):
        wide = self.private("wide.txt", "canary-wide-" + "z" * 200)
        place = self.registry_naming(wide, name="wide.json")
        with self.refusing() as caught:
            self.resolver(place, max_bearer=64).resolve("acme-vault",
                                                        "op://vault/one")
        self.assertIn("wider than", str(caught.exception))
        # A PREFIX IS NOT A CREDENTIAL, and a refusal is not a place to put
        # one either: neither the value nor its beginning rides out in prose.
        self.assertNotIn("canary-wide-", str(caught.exception))
        self.assertNamesNoPath(caught.exception)

    def test_a_source_that_is_not_text_is_refused(self):
        raw = self.private("binary.bin", b"\xff\xfe\x00\x01")
        with self.refusing() as caught:
            self.resolving(self.registry_naming(raw))
        self.assertIn("not text", str(caught.exception))


# -- the reader's own operand rules ------------------------------------------------


class TheOperandIsDeclaredOnceAndReadThroughThatDeclaration(_Fixture):
    """`add_operand`, `named_operand` and `refused_in_ending`, as themselves.

    THE PUBLIC HELP IS NOT ASSERTED HERE ANY MORE. A parser this file composed
    would have said whatever `add_operand` put on it whether or not the real
    command ever called it, which is the stand-in evidence the review rejected;
    the real `dogfood_operator.main --help` is what says the operand is on the
    command, and it is driven below. What is left here is the declaration's own
    behaviour, which is this module's to answer for.
    """

    def parser(self):
        built = argparse.ArgumentParser(prog="declaration", add_help=False)
        user_credentials.add_operand(built)
        return built

    def test_the_declaration_carries_the_value_under_one_name(self):
        parsed = self.parser().parse_args(
            [user_credentials.OPERAND, "/home/someone/sources.json"])
        self.assertEqual(parsed.credential_sources,
                         "/home/someone/sources.json")

    def test_an_omitted_operand_is_none_rather_than_a_default(self):
        self.assertIsNone(self.parser().parse_args([]).credential_sources)

    def test_the_launcher_reads_the_same_declaration(self):
        argv = ["--grants", "g.json", "--evidence", "o.json",
                user_credentials.OPERAND, "/home/someone/sources.json",
                "--retry-handoff"]
        self.assertEqual(user_credentials.named_operand(argv),
                         "/home/someone/sources.json")
        self.assertIsNone(user_credentials.named_operand(
            ["--grants", "g.json", "--evidence", "o.json"]))

    def test_the_launcher_never_speaks_for_the_public_parser(self):
        # A malformed operand answers `None` here rather than printing a usage
        # line and exiting: the public parser reports it, in its own words.
        self.assertIsNone(
            user_credentials.named_operand(["--grants", "g.json",
                                            user_credentials.OPERAND]))

    def test_both_ending_modes_refuse_a_contradictory_operand(self):
        for mode in user_credentials.ENDING_MODES:
            with self.refusing() as caught:
                user_credentials.refused_in_ending("/home/someone/s.json",
                                                   mode=mode)
            self.assertIn(mode, str(caught.exception))
            self.assertIn(user_credentials.OPERAND, str(caught.exception))
            self.assertNotIn("/home/someone/s.json", str(caught.exception))

    def test_both_ending_modes_are_content_without_one(self):
        for mode in user_credentials.ENDING_MODES:
            self.assertIsNone(
                user_credentials.refused_in_ending(None, mode=mode))

    def test_the_modes_this_rule_answers_for_are_a_closed_set(self):
        for mode in ("ordinary", "--abandon-reason", None, ""):
            with self.refusing():
                user_credentials.refused_in_ending(None, mode=mode)

    def test_the_ending_modes_are_the_documented_ones(self):
        # W61984 adds the third. It is an ending mode for the same reason the
        # other two are: it opens no registry and no source, so an operand
        # naming material to deliver is a contradiction in it.
        self.assertEqual(user_credentials.ENDING_MODES,
                         ("--abandon", "--retry-handoff",
                          "--finalize-quiescent"))


# == THE PRODUCTION SEAM ============================================================
#
# Everything below drives the real command and the real manager. There is no
# condition on any of it: the imports at the top of this file are what these
# cases need, they are taken unguarded, and a tree that cannot provide them
# has already failed this module before the first case is collected.


class _Seam(_Fixture):
    """One disposable tree, one real `CredentialHome`, one real reader.

    THE ONLY THING PATCHED IS THE CONFIGURED WORKSPACE GROUP. `_reader_group`
    turns this deployment's own record into the gid the live slot is granted
    to, and reading that record means opening a control store -- which is the
    one manager act this suite is not allowed to perform. So the grant is this
    process's own gid: the `fchown` on the slot descriptor is real, the mode
    is the manager's real `VOLATILE_FILE`, and every failing case here refuses
    before that line is reached at all.
    """

    def setUp(self):
        super().setUp()
        patched = mock.patch.object(credentials, "_reader_group",
                                    return_value=os.getgid())
        patched.start()
        self.addCleanup(patched.stop)

    def manager_home(self, name="manager"):
        return credentials.CredentialHome(os.path.join(self.home, name))

    def delivered(self, home, delivery):
        """Register a live delivery so this case releases it however it ends.

        A bearer registered by a real materialization is live for the PROCESS
        until something forgets it, and a case that left one behind would arm
        every later §13 walk in this suite against a canary nobody is
        delivering.
        """
        self.addCleanup(self._release, home, delivery)
        return delivery

    def _release(self, home, delivery):
        if delivery.state != "torn-down":
            home.tear_down(delivery)

    def resolved(self, slots, profile):
        return credentials.resolved_delivery(slots, profile=profile)


class TheReaderAgreesWithTheProfileTheManagerResolves(_Seam):
    """Whatever `resolved_delivery` produces, this reader must be able to hold.

    Review 2026-09-01T13-04-03Z [P1]: the two ends of one pair were held by
    two different rules and only one of them was tested, so a provider or a
    reference the manager legitimately resolved could be refused at the reader
    for a grammar nobody wrote. These cases take the pair FROM the manager and
    hand it to the reader, which is the only shape in which the agreement can
    fail.
    """

    def profile(self):
        return {
            "broad-token": {"provider": "vault/team",
                            "reference": "op://" + "wide-" * 200},
            "narrow-token": {"provider": "acme-vault",
                             "reference": "op://vault/one"}}

    def test_a_pair_the_manager_resolves_is_a_pair_this_reader_delivers(self):
        resolution = self.resolved(["broad-token", "narrow-token"],
                                   self.profile())
        self.assertEqual(len(resolution), 2)
        canaries = {}
        sources = []
        for index, one in enumerate(resolution):
            canary = f"canary-agreement-{index}-4f0{index}"
            canaries[(one["provider"], one["reference"])] = canary
            sources.append({"provider": one["provider"],
                            "reference": one["reference"],
                            "path": self.private_at(
                                os.path.join(self.home, f"material-{index}"),
                                canary)})
        place = self.registry("sources.json", sources)
        reading = self.resolver(place, max_bearer=credentials.MAX_BEARER)
        for pair, canary in canaries.items():
            self.assertEqual(reading.resolve(*pair), canary)

    def test_the_widths_this_reader_used_to_invent_are_really_exceeded(self):
        # NOT A TAUTOLOGY. If the profile above stopped carrying a provider
        # with a slash in it and a reference wider than 512 characters, the
        # case above would still pass and would prove nothing about the
        # grammar that was removed.
        resolution = self.resolved(["broad-token"], self.profile())
        self.assertIn("/", resolution[0]["provider"])
        self.assertGreater(len(resolution[0]["reference"]), 512)

    # -- the same pair at a width nothing could summarize ----------------------
    #
    # Review 2026-09-01T13-57-01Z [P1], driven through the whole seam rather
    # than at the reader alone. `resolved_delivery` accepts a multi-kilobyte
    # opaque pair, `materialize` asks the reader with EXACTLY it, and the
    # refusal that comes back when the registry does not name it is bounded
    # prose that quotes neither value -- which are the two halves of the
    # correction, and they can only disagree here.

    LARGE_PROVIDER = "vault/team/" + "P" * 4000
    LARGE_REFERENCE = "op://baton/" + "R" * 8000
    LARGE_NEIGHBOUR = "op://baton/" + "R" * 7999 + "S"

    def large_profile(self):
        return {"provider-token": {"provider": self.LARGE_PROVIDER,
                                   "reference": self.LARGE_REFERENCE}}

    def test_a_large_opaque_pair_reaches_the_reader_and_selects_exactly(self):
        chosen = "canary-seam-large-exact-6d11"
        other = "canary-seam-large-neighbour-6d12"
        place = self.registry("sources.json", [
            {"provider": self.LARGE_PROVIDER,
             "reference": self.LARGE_NEIGHBOUR,
             "path": self.private("neighbour.txt", other)},
            {"provider": self.LARGE_PROVIDER,
             "reference": self.LARGE_REFERENCE,
             "path": self.private("chosen.txt", chosen)}])
        resolution = self.resolved(["provider-token"], self.large_profile())
        # THE MANAGER REALLY DOES CARRY BOTH VALUES WHOLE.
        self.assertEqual(resolution[0]["provider"], self.LARGE_PROVIDER)
        self.assertEqual(resolution[0]["reference"], self.LARGE_REFERENCE)
        reading = _Counting(
            self.resolver(place, max_bearer=credentials.MAX_BEARER))
        home = self.manager_home()
        delivery = self.delivered(home, home.materialize(
            resolution, attempt_id="attempt-large-1", workspace_group=None,
            credential_provider=reading))
        # ASKED WITH THE EXACT PAIR, and answered out of the entry that agrees
        # with it rather than out of the neighbour one byte away.
        self.assertEqual(reading.calls,
                         [(self.LARGE_PROVIDER, self.LARGE_REFERENCE)])
        source, _target = delivery.mounts()[0]
        with open(source, encoding="utf-8") as slot:
            self.assertEqual(slot.read(), chosen)

    def test_a_large_opaque_pair_the_registry_lacks_refuses_boundedly(self):
        # THE NEIGHBOUR ALONE, so the registry is a real one that simply does
        # not name what the profile resolved.
        place = self.registry("sources.json", [
            {"provider": self.LARGE_PROVIDER,
             "reference": self.LARGE_NEIGHBOUR,
             "path": self.private("neighbour.txt", "canary-seam-6d13")}])
        home = self.manager_home()
        with self.refusing() as caught:
            home.materialize(
                self.resolved(["provider-token"], self.large_profile()),
                attempt_id="attempt-large-2", workspace_group=None,
                credential_provider=self.resolver(
                    place, max_bearer=credentials.MAX_BEARER))
        message = str(caught.exception)
        # TYPED, BOUNDED, AND QUOTING NOTHING -- across the manager's own
        # unwind, which re-raises this reader's refusal rather than replacing
        # it with one of its own.
        self.assertIn("no fallback", message)
        self.assertIn(f"a provider identity and opaque reference of "
                      f"{len(self.LARGE_PROVIDER.encode('utf-8'))} and "
                      f"{len(self.LARGE_REFERENCE.encode('utf-8'))} "
                      f"encoded bytes", message)
        self.assertNotIn("P" * 8, message)
        self.assertNotIn("R" * 8, message)
        self.assertLess(len(message), 512)
        self.assertNamesNoPath(caught.exception)
        # AND THE FAILED MATERIALIZATION LEFT NO ROOT BEHIND.
        self.assertFalse(
            os.path.lexists(home.volatile_root("attempt-large-2")))


class TheOrdinaryCommandInjectsThisReader(_Seam):
    """The real `dogfood_operator`, its real help, and the bound it passes."""

    def setUp(self):
        super().setUp()
        self.canary = "canary-injected-2c58"
        self.material = self.private("material.txt", self.canary)
        self.place = self.registry("sources.json", [
            {"provider": "acme-vault", "reference": "op://vault/one",
             "path": self.material}])

    def test_the_real_public_help_names_the_operand(self):
        printed = io.StringIO()
        with contextlib.redirect_stdout(printed):
            with self.assertRaises(SystemExit) as caught:
                dogfood_operator.main(["--help"], capabilities=self.fail)
        self.assertEqual(caught.exception.code, 0)
        text = printed.getvalue()
        self.assertIn(user_credentials.OPERAND, text)
        self.assertIn("PATH", text)
        # ...and the bypass it replaced is named nowhere on the real command.
        self.assertNotIn("--credential-file", text)

    def test_the_launcher_builds_this_reader_with_the_manager_bound(self):
        argv = ["--grants", "g.json", "--evidence", "o.json",
                user_credentials.OPERAND, self.place]
        named = user_credentials.named_operand(argv)
        self.assertEqual(named, self.place)
        reading = dogfood_operator._credential_resolver(named)
        self.assertIsInstance(reading, user_credentials.UserCredentialSources)
        self.assertEqual(reading.place, self.place)
        # ONE BOUND, and it is the manager's own object rather than a copy of
        # its value: a second constant is a second bound with nothing
        # comparing the two.
        self.assertIs(reading.max_bearer, credentials.MAX_BEARER)

    def test_a_malformed_operand_becomes_the_command_s_own_type(self):
        with self.assertRaises(dogfood_operator.OperatorRefusal) as caught:
            dogfood_operator._credential_resolver("relative/sources.json")
        self.assertNotIn(self.home, str(caught.exception))

    def test_the_reader_the_launcher_built_is_what_the_manager_delivers(self):
        reading = _Counting(
            dogfood_operator._credential_resolver(self.place))
        home = self.manager_home()
        resolution = self.resolved(
            ["provider-token"],
            {"provider-token": {"provider": "acme-vault",
                                "reference": "op://vault/one"}})
        delivery = self.delivered(home, home.materialize(
            resolution, attempt_id="attempt-injected-1",
            workspace_group=None, credential_provider=reading))
        # THE TWO OPERANDS REACHED THE READER, which is the whole of the
        # defect this slice replaces: the seam it replaced discarded both.
        self.assertEqual(reading.calls, [("acme-vault", "op://vault/one")])
        source, target = delivery.mounts()[0]
        self.assertEqual(target,
                         f"{credentials.CREDENTIAL_ROOT}/provider-token")
        with open(source, encoding="utf-8") as reading_slot:
            self.assertEqual(reading_slot.read(), self.canary)
        self.assertEqual(stat.S_IMODE(os.stat(source).st_mode),
                         credentials.VOLATILE_FILE)
        self.assertEqual(stat.S_IMODE(os.stat(delivery.root).st_mode),
                         credentials.VOLATILE_DIR)


class BothEndingModesRefuseTheOperandBeforeAnyBuilderActs(_Seam):
    """The real `main`, on the two modes that read no registry at all."""

    def setUp(self):
        super().setUp()
        self.reached = []
        self.place = self.registry("sources.json", [
            {"provider": "acme-vault", "reference": "op://vault/one",
             "path": self.private("material.txt", "canary-ending-7d19")}])
        self.evidence = os.path.join(self.home, "evidence.json")

    def sentinel(self, *args, **named):
        self.reached.append(args)
        raise _BuilderReached("a builder acted")

    def test_the_two_closed_documents_are_the_ones_the_command_reads(self):
        # A member added upstream fails HERE rather than quietly turning the
        # cases below into a refusal about the wrong thing.
        self.assertEqual(sorted(_grants()),
                         sorted(dogfood_operator.GRANT_MEMBERS))
        self.assertEqual(sorted(_evidence()),
                         sorted(dogfood_operator.EVIDENCE_MEMBERS))

    def test_an_abandonment_refuses_the_operand_before_its_builder(self):
        with self.assertRaises(dogfood_operator.OperatorRefusal) as caught:
            dogfood_operator.main(
                ["--grants", self.written("grants.json", _grants()),
                 "--evidence", self.evidence,
                 user_credentials.OPERAND, self.place,
                 "--abandon", "--abandon-reason",
                 "the supervising process died"],
                capabilities=self.sentinel,
                abandon_capabilities=self.sentinel,
                retry_capabilities=self.sentinel)
        self.assertIn("--abandon", str(caught.exception))
        self.assertIn(user_credentials.OPERAND, str(caught.exception))
        self.assertNotIn(self.place, str(caught.exception))
        self.assertEqual(self.reached, [])
        self.assertFalse(os.path.exists(self.evidence))

    def test_a_handoff_retry_refuses_the_operand_before_its_builder(self):
        with self.assertRaises(dogfood_operator.OperatorRefusal) as caught:
            dogfood_operator.main(
                ["--grants", self.written("grants.json", _grants()),
                 "--evidence", self.written("evidence.json", _evidence()),
                 user_credentials.OPERAND, self.place, "--retry-handoff"],
                capabilities=self.sentinel,
                abandon_capabilities=self.sentinel,
                retry_capabilities=self.sentinel)
        self.assertIn("--retry-handoff", str(caught.exception))
        self.assertIn(user_credentials.OPERAND, str(caught.exception))
        self.assertNotIn(self.place, str(caught.exception))
        self.assertEqual(self.reached, [])

    def test_that_abandonment_without_the_operand_reaches_its_builder(self):
        # NOT VACUOUS. Without the operand the mode is ordinary and the
        # command goes on to build the ending-only capabilities, so the
        # refusal above is about the contradiction and not about the mode.
        with self.assertRaises(_BuilderReached):
            dogfood_operator.main(
                ["--grants", self.written("grants.json", _grants()),
                 "--evidence", self.evidence, "--abandon",
                 "--abandon-reason", "the supervising process died"],
                capabilities=self.sentinel,
                abandon_capabilities=self.sentinel,
                retry_capabilities=self.sentinel)
        self.assertEqual(len(self.reached), 1)

    def test_the_same_retry_without_the_operand_reaches_its_builder(self):
        with self.assertRaises(_BuilderReached):
            dogfood_operator.main(
                ["--grants", self.written("grants.json", _grants()),
                 "--evidence", self.written("evidence.json", _evidence()),
                 "--retry-handoff"],
                capabilities=self.sentinel,
                abandon_capabilities=self.sentinel,
                retry_capabilities=self.sentinel)
        self.assertEqual(len(self.reached), 1)


class NothingIsReadBeforeTheDeliveryIsMaterialized(_Seam):
    """The reader exists from the command; the delivery exists from activation.

    THE LAZY WINDOW IS THE APPROVED ONE (M59057) and it is asserted against the
    real `CredentialHome`: constructing the home and the reader opens nothing,
    and `materialize` is the first act that reads a registry or writes a slot.
    """

    def setUp(self):
        super().setUp()
        self.canary = "canary-lazy-3d5b"
        self.material = self.private("material.txt", self.canary)
        self.place = self.registry("sources.json", [
            {"provider": "acme-vault", "reference": "op://vault/lazy",
             "path": self.material}])
        self.profile = {"provider-token": {"provider": "acme-vault",
                                           "reference": "op://vault/lazy"}}

    def test_construction_opens_nothing_at_all(self):
        # Sabotaged at the one function that opens a descriptor: if
        # construction read anything, this would raise instead of building.
        with mock.patch.object(user_credentials, "_proved_read",
                               side_effect=AssertionError("read too early")):
            reading = self.resolver(self.place)
            home = self.manager_home()
            resolution = self.resolved(["provider-token"], self.profile)
        self.assertEqual(reading.place, self.place)
        self.assertEqual(len(resolution), 1)
        # ...and the same objects then work once nothing is sabotaged.
        delivery = self.delivered(home, home.materialize(
            resolution, attempt_id="attempt-lazy-0", workspace_group=None,
            credential_provider=reading))
        self.assertEqual(delivery.state, "live")

    def test_a_reader_over_an_absent_registry_still_constructs(self):
        self.resolver(os.path.join(self.home, "nothing-here.json"))

    def test_no_source_is_read_and_no_slot_written_before_activation(self):
        reading = _Counting(self.resolver(self.place))
        home = self.manager_home()
        resolution = self.resolved(["provider-token"], self.profile)
        root = home.volatile_root("attempt-lazy-1")
        self.assertEqual(reading.calls, [])
        self.assertFalse(os.path.lexists(root))
        self.assertIsNone(home.read_state("attempt-lazy-1"))

        delivery = self.delivered(home, home.materialize(
            resolution, attempt_id="attempt-lazy-1", workspace_group=None,
            credential_provider=reading))

        self.assertEqual(reading.calls, [("acme-vault", "op://vault/lazy")])
        self.assertEqual(delivery.root, root)
        self.assertTrue(os.path.isdir(root))
        with open(os.path.join(root, "provider-token"),
                  encoding="utf-8") as reading_slot:
            self.assertEqual(reading_slot.read(), self.canary)


class AFailedResolutionUnwindsExactlyItsOwnRoot(_Seam):
    """A materialization the reader refuses part way tears its own root down.

    AND EXACTLY ITS OWN. A `CredentialHome` is assignment-scoped and can hold
    sibling attempts' roots, so "this delivery failed" is not evidence about
    any other one.
    """

    def setUp(self):
        super().setUp()
        self.keeper = "canary-keeper-1a20"
        self.doomed = "canary-doomed-5b71"
        self.place = self.registry("sources.json", [
            {"provider": "acme-vault", "reference": "op://vault/keeper",
             "path": self.private("keeper.txt", self.keeper)},
            {"provider": "acme-vault", "reference": "op://vault/first",
             "path": self.private("first.txt", self.doomed)}])
        self.profile = {
            "keeper": {"provider": "acme-vault",
                       "reference": "op://vault/keeper"},
            "first": {"provider": "acme-vault",
                      "reference": "op://vault/first"},
            "second": {"provider": "acme-vault",
                       "reference": "op://vault/unknown"}}
        self.manager = self.manager_home()

    def failing(self, attempt_id):
        return self.manager.materialize(
            self.resolved(["first", "second"], self.profile),
            attempt_id=attempt_id, workspace_group=None,
            credential_provider=self.resolver(self.place))

    def test_the_failed_root_is_gone_and_the_sibling_is_untouched(self):
        sibling = self.delivered(self.manager, self.manager.materialize(
            self.resolved(["keeper"], self.profile),
            attempt_id="attempt-sibling", workspace_group=None,
            credential_provider=self.resolver(self.place)))
        failed = self.manager.volatile_root("attempt-cleanup-1")
        with self.refusing():
            self.failing("attempt-cleanup-1")
        self.assertFalse(os.path.lexists(failed))
        # THE BEARER THE FIRST SLOT REALLY DID RECEIVE went with it, and the
        # sibling's did not.
        self.assertEqual(
            sorted(os.listdir(os.path.join(self.manager.place,
                                           "credentials"))),
            ["attempt-sibling"])
        with open(sibling.mounts()[0][0], encoding="utf-8") as reading:
            self.assertEqual(reading.read(), self.keeper)

    def test_a_refusal_on_the_first_slot_leaves_no_root_either(self):
        with self.refusing():
            self.manager.materialize(
                self.resolved(["second"], self.profile),
                attempt_id="attempt-cleanup-2", workspace_group=None,
                credential_provider=self.resolver(self.place))
        self.assertFalse(os.path.lexists(
            self.manager.volatile_root("attempt-cleanup-2")))

    def test_the_registry_that_guards_the_leak_checks_is_released(self):
        # ARMED FIRST, so this is not a check that cannot fail: a live bearer
        # really does refuse a document carrying it.
        sibling = self.delivered(self.manager, self.manager.materialize(
            self.resolved(["keeper"], self.profile),
            attempt_id="attempt-armed", workspace_group=None,
            credential_provider=self.resolver(self.place)))
        self.assertEqual(sibling.state, "live")
        with self.assertRaises(ContractRefusal):
            check_no_durable_secret({"note": self.keeper}, "a §13 probe")
        # ...and the bearer the unwound root held is FORGOTTEN, because the
        # act that acquired it is the act that released it.
        with self.refusing():
            self.failing("attempt-cleanup-3")
        check_no_durable_secret({"note": self.doomed}, "a §13 probe")


class NeitherContentNorSourcePathIsEverPublished(_Seam):
    """The real durable surfaces this arc writes, and what is not on them."""

    def setUp(self):
        super().setUp()
        self.canary = "canary-durable-6b21"
        self.material = self.private("material.txt", self.canary)
        self.place = self.registry("sources.json", [
            {"provider": "acme-vault", "reference": "op://vault/durable",
             "path": self.material}])
        self.manager = self.manager_home()
        self.delivery = self.delivered(self.manager, self.manager.materialize(
            self.resolved(["provider-token"],
                          {"provider-token": {
                              "provider": "acme-vault",
                              "reference": "op://vault/durable"}}),
            attempt_id="attempt-durable-1", workspace_group=None,
            credential_provider=self.resolver(self.place)))

    def test_the_delivered_slot_really_does_hold_the_selected_source(self):
        # The negatives below would pass over an empty delivery, which is the
        # vacuous shape this campaign has been corrected for repeatedly.
        source, _target = self.delivery.mounts()[0]
        with open(source, encoding="utf-8") as reading:
            self.assertEqual(reading.read(), self.canary)

    def test_the_real_lifecycle_record_carries_neither(self):
        record = self.delivery.record(runtime_id="runtime-durable-1")
        answered = self.manager.written_state(self.delivery.attempt_id,
                                              record)
        self.assertEqual(answered["lifecycle_state"], "live")
        with open(self.manager.state_path(self.delivery.attempt_id),
                  "rb") as reading:
            body = reading.read().decode("utf-8")
        # NOT `self.home`: the record legitimately names the MANAGER'S OWN
        # volatile root, which is under this case's tree. What may not be on
        # it is the bearer and the USER'S own two paths.
        self.assertNotIn(self.canary, body)
        self.assertNotIn(self.material, body)
        self.assertNotIn(self.place, body)

    def test_the_walk_that_record_goes_through_is_armed(self):
        record = self.delivery.record(runtime_id="runtime-durable-1")
        with self.assertRaises(ContractRefusal):
            self.manager.written_state(
                self.delivery.attempt_id,
                dict(record, runtime_id=self.canary))

    def test_the_real_grants_door_refuses_a_bearer_that_reached_it(self):
        with self.assertRaises(dogfood_operator.OperatorRefusal) as caught:
            dogfood_operator.read_grants(self.written(
                "leaking-grants.json", _grants(labels={"t": self.canary})))
        self.assertIn("will not be used", str(caught.exception))
        # ...and the same file without it is read, so the door is not simply
        # refusing everything.
        read = dogfood_operator.read_grants(
            self.written("clean-grants.json", _grants()))
        self.assertEqual(read["attempt_id"], "attempt-w52821-seam")

    def test_the_worker_is_told_only_the_fixed_container_entries(self):
        mounts = self.delivery.mounts()
        self.assertEqual(
            [target for _source, target in mounts],
            [f"{credentials.CREDENTIAL_ROOT}/provider-token"])
        for source, _target in mounts:
            self.assertNotEqual(source, self.material)
            self.assertNotIn(self.place, source)


class TwoInvocationContextsConsumeDistinctEverything(_Seam):
    """Two complete worlds, interleaved on purpose at the reader.

    DISTINCT IN EVERY AXIS the slice could accidentally share: registry,
    provider, reference, canary, attempt id, generation and credential home.
    The barrier releases both threads into the reader at the same instant, so
    the two reads genuinely overlap -- a shared cache or a singleton reader
    would then hand one context the other's source, and a lock held ACROSS
    calls would show up as a thread that never finishes rather than as a wrong
    answer nobody notices. Both are asserted below.

    AND NEITHER CONTEXT IS A WORKER. No runtime is started, no engine is
    reached and no container exists: what runs concurrently is two
    materializations inside two private trees.
    """

    def context(self, name, *, provider, reference, canary, attempt_id,
                generation):
        base = os.path.join(self.home, name)
        source = self.private_at(os.path.join(base, "material.txt"), canary)
        place = self.registry_at(
            os.path.join(base, "sources.json"),
            [{"provider": provider, "reference": reference, "path": source}])
        home = credentials.CredentialHome(os.path.join(base, "manager"))
        return {
            "name": name, "source": source, "registry": place,
            "canary": canary, "attempt_id": attempt_id,
            "generation": generation, "provider": provider,
            "reference": reference, "home": home,
            "resolution": self.resolved(
                ["provider-token"],
                {"provider-token": {"provider": provider,
                                    "reference": reference}}),
            "grants": _grants(attempt_id=attempt_id, generation=generation),
            "evidence": _evidence(attempt_id=attempt_id,
                                  generation=generation)}

    def setUp(self):
        super().setUp()
        self.first = self.context(
            "user-a", provider="vault/team", reference="op://vault/alpha",
            canary="canary-alpha-0001", attempt_id="attempt-alpha",
            generation=1)
        self.second = self.context(
            "user-b", provider="other-broker",
            reference="op://" + "beta-" * 200, canary="canary-beta-0002",
            attempt_id="attempt-beta", generation=7)
        self.made = {}

    def run_both(self):
        barrier = threading.Barrier(2)
        faults = {}

        def drive(context):
            try:
                reading = _Counting(
                    self.resolver(context["registry"],
                                  max_bearer=credentials.MAX_BEARER),
                    before=lambda: barrier.wait(timeout=30))
                context["reader"] = reading
                self.made[context["name"]] = context["home"].materialize(
                    context["resolution"],
                    attempt_id=context["attempt_id"],
                    workspace_group=None, credential_provider=reading)
            except BaseException as failed:                # noqa: BLE001
                faults[context["name"]] = failed
                barrier.abort()

        threads = [threading.Thread(target=drive, args=(one,), daemon=True)
                   for one in (self.first, self.second)]
        for one in threads:
            one.start()
        for one in threads:
            one.join(timeout=60)
            self.assertFalse(one.is_alive(),
                             "a context never finished; a global lock in the "
                             "reader would look exactly like this")
        for context in (self.first, self.second):
            made = self.made.get(context["name"])
            if made is not None:
                self.delivered(context["home"], made)
        if faults:
            raise faults[sorted(faults)[0]]
        return self.made

    def slot_of(self, context):
        source, _target = self.made[context["name"]].mounts()[0]
        with open(source, encoding="utf-8") as reading:
            return reading.read()

    def test_each_context_receives_exactly_its_own_source(self):
        self.run_both()
        for context in (self.first, self.second):
            self.assertEqual(self.slot_of(context), context["canary"])
            # THE SELECTION EACH ONE ACTUALLY CONSUMED, taken from the
            # manager's own resolution rather than from this case's literals.
            self.assertEqual(context["reader"].calls,
                             [(context["provider"], context["reference"])])

    def test_neither_context_can_see_the_other_s_material(self):
        self.run_both()
        for context, other in ((self.first, self.second),
                               (self.second, self.first)):
            root = self.made[context["name"]].root
            self.assertNotEqual(root, self.made[other["name"]].root)
            for name in sorted(os.listdir(root)):
                with open(os.path.join(root, name), encoding="utf-8") as one:
                    body = one.read()
                self.assertNotIn(other["canary"], body)
                self.assertNotIn(other["reference"], body)

    def test_neither_home_holds_anything_of_the_other_s_attempt(self):
        self.run_both()
        for context, other in ((self.first, self.second),
                               (self.second, self.first)):
            held = context["home"].orphan_evidence(context["attempt_id"])
            self.assertTrue(held["volatile_root"])
            elsewhere = context["home"].orphan_evidence(other["attempt_id"])
            self.assertFalse(elsewhere["volatile_root"])
            self.assertFalse(elsewhere["lifecycle_record"])

    def test_the_two_generations_and_attempts_are_really_consumed(self):
        self.run_both()
        # THE COMMAND'S OWN BINDING, not an assertion about two literals: each
        # context's retained record agrees with its own grants and refuses the
        # other's, on the identities that differ.
        for context in (self.first, self.second):
            self.assertIs(
                dogfood_operator._bound(context["evidence"],
                                        context["grants"]),
                context["evidence"])
        with self.assertRaises(dogfood_operator.OperatorRefusal) as caught:
            dogfood_operator._bound(self.first["evidence"],
                                    self.second["grants"])
        self.assertIn("generation", str(caught.exception))
        self.assertIn("attempt_id", str(caught.exception))

    def test_tearing_one_context_down_touches_nothing_else(self):
        self.run_both()
        # A THIRD ATTEMPT IN THE SAME HOME, because a home is
        # assignment-scoped and "this attempt is over" is not evidence about
        # any other one.
        sibling = self.delivered(self.first["home"],
                                 self.first["home"].materialize(
                                     self.first["resolution"],
                                     attempt_id="attempt-alpha-sibling",
                                     workspace_group=None,
                                     credential_provider=self.resolver(
                                         self.first["registry"])))

        ended = self.first["home"].tear_down(self.made[self.first["name"]])
        self.assertEqual(ended["lifecycle_state"], "torn-down")

        self.assertFalse(os.path.lexists(self.made[self.first["name"]].root))
        self.assertTrue(os.path.isdir(sibling.root))
        self.assertEqual(self.slot_of(self.second), self.second["canary"])
        # THE USER'S OWN FILES ARE NEVER TOUCHED BY AN ENDING.
        self.assertTrue(os.path.isfile(self.second["source"]))
        self.assertTrue(os.path.isfile(self.first["source"]))


if __name__ == "__main__":
    unittest.main()
