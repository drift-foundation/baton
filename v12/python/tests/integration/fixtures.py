"""One disposable coordinator store, and the documents its cases hand it.

WHY THE ELIGIBILITY ACCOUNT IS BUILT HERE AND NOT PROVED HERE. PLAN item 4
owns admission: re-resolving W71918's custody surface and Authority's policy
receipts and proving their corresponding operands describe one candidate. This
seam stores an account that has ALREADY been proved, so these fixtures mint a
well-formed one and vary the operands a case cares about. A fixture that
validated eligibility would be testing item 4 through item 3's door.
"""

import os
import tempfile
import unittest

from baton_v12.contracts import digest
from baton_v12.integration import IntegrationStore, TARGET_SCHEMA
from baton_v12.source_profiles import GIT_PROFILE

# WHAT THE NAMED PRODUCERS ACTUALLY EMIT. The profile kind is one of
# `source_profiles.PROFILES`; the path set is the sorted, relative, canonical
# collection `checkpoint_profiles` digests; the test scope is the accepted
# Job's own `test_scope` list.
PROFILE_KIND = GIT_PROFILE
PATHS = ["src/a.py", "src/b.py"]
TEST_SCOPE = ["v12/python/tests/integration"]

NOW = "2026-09-05T00:00:00.000Z"
LATER = "2026-09-05T00:05:00.000Z"

# Two Authorities, which is the whole point of this store: both are configured
# for one canonical target, and this record's identity model requires them to
# contend on ONE lock rather than on one lock each.
UUID_A = "0" * 31 + "a"
UUID_B = "0" * 31 + "b"

TARGET = "target:mainline"

# WHAT A TARGET DOCUMENT NO LONGER CARRIES. The owner clarified on 2026-09-06
# that a checkout is a version-control idea and coordinator schema is neutral
# about those, so the document is a NAME and a description; where the named
# thing lives is the integration profile's.
DESCRIPTION = "the mainline target"


def target(canonical_target_id=TARGET, description=DESCRIPTION):
    return {"schema": TARGET_SCHEMA,
            "canonical_target_id": canonical_target_id,
            "description": description}


def eligibility(authority_uuid=UUID_A, checkpoint_id="checkpoint-1", **rest):
    """One already-proved account, carrying every operand an entry retains.

    The two digest families are BOTH here and are deliberately unequal: the
    targeted review of 2026-09-05 ruled that requiring them equal merely to
    manufacture a cross-binding would silently reinterpret one of them.

    AND NOTHING IN IT IS A GIT OPERAND. `profile_kind` is the accepted
    checkpoint evidence's own profile NAME, and the profile-shaped account that
    name belongs to is bound by `checkpoint_digest`, which W71918 computes as
    the digest of that evidence.

    EVERY MEMBER HAS A PRODUCER AND THIS FIXTURE SPELLS ITS VALUES THE WAY THAT
    PRODUCER WOULD. W101491 found two members with no producer at all;
    W101714's review then found a third, and found this fixture asserting a
    profile kind the named producer cannot emit.
    `EveryMemberOfTheAccountHasAProducer` is where that is checked rather than
    described.
    """
    account = {"authority_uuid": authority_uuid,
               "work_id": "0000000a-W1",
               "assignment_generation": 1,
               "line_id": "line-1",
               "checkpoint_id": checkpoint_id,
               "verdict_id": "verdict-1",
               "checkpoint_digest": "sha256:" + "1" * 64,
               "proposal_id": "proposal-1",
               "candidate_digest": "sha256:" + "2" * 64,
               "result_id": "result-1",
               "result_digest": "sha256:" + "3" * 64,
               # NOT AN INVENTED WORD. W101714's review found this fixture
               # asserting `repository`, which the named producer cannot emit:
               # the accepted checkpoint evidence's `profile` member is one of
               # `source_profiles.PROFILES`. A fixture demonstrating that the
               # coordinator accepts arbitrary text demonstrates something that
               # was already true.
               "profile_kind": PROFILE_KIND,
               "expected_target_revision": "d" * 40,
               # COMPUTED THE WAY THEIR PRODUCERS COMPUTE THEM, so a case that
               # re-resolves either one compares against the real rule rather
               # than against a constant this file chose.
               "path_set_digest": digest(PATHS),
               "scope_digest": digest(TEST_SCOPE)}
    account.update(rest)
    return account


class CoordinatorCase(unittest.TestCase):
    """One temporary root, one pinned clock, one coordinator store."""

    def setUp(self):
        self._root = tempfile.TemporaryDirectory(prefix="v12-integration-")
        self.addCleanup(self._root.cleanup)
        self.root = self._root.name
        self.path = os.path.join(self.root, "integration.sqlite3")
        self.instants = [NOW]

    def clock(self):
        return self.instants[-1]

    def store(self, incarnation="coordinator-1", path=None):
        store = IntegrationStore.open(path or self.path,
                                      incarnation=incarnation,
                                      clock=self.clock)
        self.addCleanup(store.close)
        return store

    def next_position(self, store):
        """The position a FORGED journal act would commit at.

        `operations.seq` is the durable order the coordinator derives rank,
        fence and selection from, so a fabricated act must take a real
        position in it or the density proof answers before the case's own
        subject does. A case that wants to test the ordering itself sets the
        column deliberately instead of calling this.
        """
        return store._connection.execute(
            "SELECT COALESCE(MAX(seq), 0) + 1 FROM operations").fetchone()[0]

    def refusal(self, action, *operands, **named):
        from baton_v12.contracts import ContractRefusal
        with self.assertRaises(ContractRefusal) as caught:
            action(*operands, **named)
        return caught.exception
