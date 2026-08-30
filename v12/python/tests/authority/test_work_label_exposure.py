"""W29401 — the exposure facts that HAVE a host in the current v12 product.

`work/records/2026/08/finding-v12-work-tags/findings/
finding-v12-work-label-protocol-cli/`.

WHY THIS FILE IS SMALL, and it is the finding's own instruction rather than a
shortfall. W29401's cut exposes the approved label contract through "canonical
create, mutation, projection, list and search protocol/CLI surfaces". Its Host
boundary says, in terms:

    Implementation must revalidate the current v12 protocol and CLI host after
    W29400. If a canonical Work create/list/search surface is still absent,
    document the observed absence and split or park only the unavailable
    exposure rather than introducing a parallel CLI or protocol product.

Revalidated 2026-08-29: **v12 has no CLI and no protocol host.** The product is
a Python library — `baton_v12.authority`, `.contracts`, `.worker_manager` —
and every `argparse`/`sys.argv` under `v12/` belongs to a test harness, a build
tool or the ping-pong spike. So the create/mutation/projection/list/search
bullets are already satisfied at the ONLY surface that exists, by W29400, and
`tests/authority/test_work_labels.py` holds them.

What is left for this file is the one acceptance bullet whose CLI form has no
host but whose UNDERLYING property does, and which nothing else asserts: that a
Work label and an OCI runtime label cannot be confused for one another. The
dossier's remaining CLI-shaped scope is parked rather than invented here.
"""

import os
import tempfile
import unittest

from baton_v12.authority.api import Authority
from baton_v12.authority.errors import Refusal
from baton_v12.authority.labels import canonical_label
from baton_v12.worker_manager.oci import LABEL_PREFIX

UUID = "43c55d4b" + "0" * 24
WORK = "43c55d4b-W1"
ROUTE = "impl"
WHO = "baton.claude"
NOW = "2026-08-29T00:00:00.000Z"


class WorkLabelsAndRuntimeLabelsAreDifferentVOCABULARIES(unittest.TestCase):
    """The acceptance bullet is about DISPATCH, and the spelling is the trap.

    W29401 asks that "Work-label commands cannot dispatch Thread-label or
    OCI-label behaviour". That is a CLI-parsing property and there is no CLI —
    but the reason the bullet exists survives the absence of its host, and it
    is sharper than it looks: the two vocabularies OVERLAP in spelling.
    """

    def setUp(self):
        root = tempfile.TemporaryDirectory(prefix="v12-w29401-")
        self.addCleanup(root.cleanup)
        self.authority = Authority.create(
            os.path.join(root.name, "authority.sqlite3"),
            authority_uuid=UUID, clock=lambda: NOW)
        self.addCleanup(self.authority.dispose)
        self.core = self.authority._core
        self.core.add_route_handler(ROUTE, WHO)

    def test_a_work_label_may_be_spelled_like_a_runtime_label_key(self):
        """MEASURED, because it decides what a future CLI may do.

        `canonical_label`'s grammar admits dots, so `baton.v12.work_id` — an
        OCI runtime label KEY this manager writes on every container — is a
        perfectly valid Work label. Only the `key=value` form is refused, and
        only because `=` is outside the alphabet.

        This is not a defect. The parent decision says no spelling is reserved
        and no behaviour is inferred from one. It IS a constraint on the
        exposure this Work exists to build: a CLI must separate Work labels
        from runtime labels by the COMMAND it dispatches, never by inspecting
        how a label is spelled, because the spellings are not disjoint.
        """
        overlapping = f"{LABEL_PREFIX}work_id"
        self.assertEqual(canonical_label(overlapping), overlapping)
        with self.assertRaises(Refusal):
            canonical_label(f"{LABEL_PREFIX}generation=1")

    def test_such_a_label_still_carries_no_runtime_meaning(self):
        """The property that makes the overlap safe, asserted rather than
        assumed: a Work wearing a runtime-shaped label is unchanged in every
        fact anything reads."""
        self.core.create_work(WORK, ROUTE, operation_id="create-1",
                              labels=(f"{LABEL_PREFIX}work_id",))
        projected = self.authority.project_work(WORK)
        self.assertEqual(projected["labels"], [f"{LABEL_PREFIX}work_id"])
        # NOTHING ELSE MOVED. The label is metadata and the scheduler axes are
        # exactly what an unlabelled Work's would be.
        self.assertEqual(projected["route"], ROUTE)
        self.assertEqual(projected["phase"], "queued")
        self.assertEqual(projected["status"], "open")
        self.assertIsNone(projected["handler"])
        self.assertIsNone(projected["gate"])

    def test_the_two_vocabularies_are_separate_functions_in_separate_packages(
            self):
        """There is no shared entry point that could dispatch the wrong one.

        `authority.labels.canonical_label` owns Work labels;
        `worker_manager.oci` owns the runtime label set. Neither package
        imports the other's label surface, which is what makes a CLI's job
        later a matter of naming two commands rather than untangling one.
        """
        from baton_v12.authority import labels as work_labels
        from baton_v12.worker_manager import oci

        self.assertFalse(hasattr(work_labels, "LABEL_PREFIX"))
        self.assertFalse(hasattr(oci, "canonical_label"))
        source = (os.path.join(os.path.dirname(work_labels.__file__),
                               "labels.py"))
        with open(source, encoding="utf-8") as reading:
            self.assertNotIn("worker_manager", reading.read())


class TheLibrarySurfaceAlreadyCarriesTheApprovedContract(unittest.TestCase):
    """One end-to-end pass over W29401's acceptance matrix at the host that
    exists, so the revalidation recorded in `FINDING.md` is a test rather than
    a claim.

    Every individual rule is W29400's and is held in detail by
    `tests/authority/test_work_labels.py`. What this adds is the ONE reading
    the exposure Work is accountable for: that create, projection and
    list/search compose into the contract W28880 approved.
    """

    def setUp(self):
        root = tempfile.TemporaryDirectory(prefix="v12-w29401-")
        self.addCleanup(root.cleanup)
        self.authority = Authority.create(
            os.path.join(root.name, "authority.sqlite3"),
            authority_uuid=UUID, clock=lambda: NOW)
        self.addCleanup(self.authority.dispose)
        self.core = self.authority._core
        self.core.add_route_handler(ROUTE, WHO)

    def made(self, number, labels):
        work = f"43c55d4b-W{number}"
        self.core.create_work(work, ROUTE, operation_id=f"create-{number}",
                              labels=labels)
        return work

    def test_create_takes_zero_one_and_repeated_labels(self):
        self.assertEqual(self.authority.labels_of(self.made(1, ())), [])
        self.assertEqual(self.authority.labels_of(self.made(2, ("alpha",))),
                         ["alpha"])
        # NORMALIZED AND DETERMINISTICALLY SORTED, which is what a projection
        # consumer and a future CLI both depend on.
        self.assertEqual(
            self.authority.labels_of(self.made(3, ("beta", "Gamma", "delta"))),
            ["beta", "delta", "gamma"])

    def test_the_projection_is_additive_for_unlabelled_work(self):
        """Backward compatibility, stated as the thing it actually is: a Work
        with no labels projects an empty list rather than a missing member, so
        a reader never has to tell absence from omission."""
        self.assertEqual(self.authority.project_work(self.made(1, ()))["labels"],
                         [])

    def test_positives_are_all_of_negatives_are_none_of_and_they_compose(self):
        self.made(1, ())
        self.made(2, ("alpha",))
        self.made(3, ("alpha", "beta"))
        self.assertEqual(sorted(self.authority.works_with_labels(
            all_of=("alpha", "beta"))), ["43c55d4b-W3"])
        self.assertEqual(sorted(self.authority.works_with_labels(
            none_of=("alpha",))), ["43c55d4b-W1"])
        self.assertEqual(sorted(self.authority.works_with_labels(
            all_of=("alpha",), none_of=("beta",))), ["43c55d4b-W2"])
        # AN EMPTY FILTER IS EVERY WORK, which is what makes the unfiltered
        # listing behaviour compatible rather than a special case.
        self.assertEqual(len(self.authority.works_with_labels()), 3)

    def test_no_or_syntax_is_introduced_and_a_contradiction_refuses(self):
        """This cut introduces no OR, and the one form that would need it —
        requiring and excluding the same label — is refused explicitly rather
        than silently answering nothing."""
        self.made(1, ("alpha",))
        with self.assertRaises(Refusal) as caught:
            self.authority.works_with_labels(all_of=("alpha",),
                                             none_of=("alpha",))
        self.assertIn("cannot both carry and not carry", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
