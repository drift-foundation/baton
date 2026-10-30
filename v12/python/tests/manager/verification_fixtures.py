"""The `/3` task, the seal and the 102-gate candidate, built once.

W321776, `work/records/2026/09/finding-v12-complete-verification-context/
findings/finding-paired-context-delivery/`.

WHY A SHARED BUILDER AND NOT TWO. VER-5's acceptance obligation is that the
SAME named gate passes in the worker's independently materialized view and in
the independent operator's, so the two suites must start from one declaration
and one seal -- two fixtures could differ in a way that made each holder pass
against its own arrangement. What is deliberately NOT shared is the view: each
holder materializes its own through its own product code, which is the whole
property under test.

NOTHING HERE MATERIALIZES A VIEW. This builds a candidate tree, a declaration
and a seal; the views are built by `claude_agent` and `dogfood_operator`.

THE LAYOUT IS THE PACKET'S, RESOLVED. `tests/manager/input_roots.py` resolves
its one immutable fixture through `parents[3] / ".."` from its own file, so with
`working_directory` at `candidate/v12/python` that path lands at
`candidate/work/records/.../vectors.json` -- INSIDE the candidate. No
declaration can move it; only a product edit could. So the fixture is handled
as BOTH: a `candidate.pins` entry at the exact digest, which is the bytes the
gate actually reads, and a declared sealed input at a destination DISJOINT from
the candidate, which is the independent reference both holders materialize from
the seal. The two carry the same digest on purpose -- they are two independent
holders of one fact, and a drifted in-candidate copy makes them disagree before
the command starts.
"""

import hashlib
import os
import pathlib
import shutil

REPOSITORY = pathlib.Path(__file__).resolve().parents[4]
DISTRIBUTION = REPOSITORY / "v12" / "python"

# The one immutable input the named gate reads, at its canonical record path.
VECTORS = ("work/records/2026/08/finding-v12-isolated-agent-workers/findings/"
           "finding-v12-worker-contract/findings/"
           "finding-worker-control-api-manifests/evidence/vectors.json")

# THE NAMED ACCEPTANCE OBLIGATION, as LITERAL argv and nothing else. VER-5
# names this gate and says a different passing subset does not substitute for
# it. There is no environment assignment here: the import path is DERIVED from
# the declaration, and an argv carrying one would be a second, disagreeing
# source of the same fact.
GATE_ARGV = [
    "python3", "-m", "unittest",
    "tests.tools.test_user_credentials",
    "tests.tools.test_dogfood_operator.TheDocumentedCommandIsOneGrantsFile"
    ".test_help_names_the_credential_source_the_launcher_requires",
    "tests.tools.test_dogfood_operator.ThePublicRecoveryEndsAnInterruptedAttempt"
    ".test_a_recovery_asks_for_no_credential",
    "tests.tools.test_dogfood_operator"
    ".TheArcMaterializesBetweenActivationAndRuntimeCreation"
    ".test_the_factory_runs_after_activation_and_before_runtime_start",
    "tests.tools.test_dogfood_operator.TheDocumentedRecoveryEndsRealAttachedState"
    ".test_an_uncertain_runtime_settles_nothing_and_keeps_the_bearer",
    "tests.manager.test_credentials.TheTrustedProfileMapsEverySlot"
    ".test_the_reference_is_opaque",
]

GATE_TESTS = 102

INPUT_NAME = "worker-control-api-manifest-vectors"
INPUT_DESTINATION = f"sealed/{INPUT_NAME}/vectors.json"


def digest_of(place):
    with open(place, "rb") as reading:
        return "sha256:" + hashlib.sha256(reading.read()).hexdigest()


def gate_candidate(root, *, name="candidate"):
    """The candidate tree the named gate runs over, at `candidate/`.

    `src`, `tests` AND `tools`, plus the one immutable record path, because
    that is what the gate resolves. `tools` is not optional and leaving it out
    was this fixture's first defect: the named gate drives `dogfood_operator`,
    which lives there, so a view without it fails for a context reason wearing
    the shape of a candidate failure -- the exact confusion this Work exists
    to remove. `__pycache__` is left
    out: it is not source, it is not measured, and a stale one would make the
    two views disagree about bytes nobody declared.
    """
    candidate = os.path.join(root, name)
    for one in ("src", "tests", "tools"):
        shutil.copytree(DISTRIBUTION / one,
                        os.path.join(candidate, "v12", "python", one),
                        ignore=shutil.ignore_patterns("__pycache__"),
                        symlinks=False)
    landing = os.path.join(candidate, VECTORS)
    os.makedirs(os.path.dirname(landing), exist_ok=True)
    shutil.copyfile(REPOSITORY / VECTORS, landing)
    return candidate


def gate_context(*, profile="generic", base=None, pin_digest):
    """The declared `/3` verification context for the named gate."""
    return {
        "working_directory": "candidate/v12/python",
        "candidate_destination": "candidate",
        "candidate": {"profile": profile, "declared_base": base,
                      "pins": [{"path": VECTORS,
                                "content_digest": pin_digest}]},
        "import_roots": ["src"],
        "required_paths": ["src", "tests", "tools", "tests/tools",
                           "tests/manager"],
        "inputs": [{"name": INPUT_NAME, "destination": INPUT_DESTINATION,
                    "content_digest": pin_digest,
                    "bytes": (REPOSITORY / VECTORS).stat().st_size}],
    }


def gate_task(*, profile="generic", base=None, pin_digest,
              task_id="w321776-paired-gate", argv=None, context=None):
    return {"schema": "baton.dogfood-task/3",
            "task_id": task_id,
            "instructions": "Deliver the paired verification contexts.",
            "verification": list(GATE_ARGV if argv is None else argv),
            "source_root": "source",
            "source_profile": profile,
            "declared_base": base,
            "verification_context": (
                gate_context(profile=profile, base=base,
                             pin_digest=pin_digest)
                if context is None else context)}


def gate_seal(place, *, pin_digest):
    """The seal, composed by the OPERATOR'S OWN composer rather than by hand.

    A hand-written seal would agree with this file and prove nothing about the
    product's sealing; `compose_seal` is the one place a seal is measured, so
    both holders read a document the deployment actually produces.
    """
    import sys

    tools = str(DISTRIBUTION / "tools")
    if tools not in sys.path:
        sys.path.insert(0, tools)
    import dogfood_operator

    os.makedirs(place, exist_ok=True)
    document, declared = dogfood_operator.compose_seal(
        place,
        inputs=[{"name": INPUT_NAME, "source": str(REPOSITORY / VECTORS),
                 "destination": INPUT_DESTINATION}],
        pins=[VECTORS], candidate=str(REPOSITORY))
    assert declared[0]["content_digest"] == pin_digest, declared
    return document


def tiny_candidate(root, *, place="candidate", name="harness.py",
                   body="print('the staged harness')\n"):
    """A candidate with one file, for the structural rows.

    THE NEGATIVES DO NOT NEED THE 102 GATE, and running it for each of them
    would make the suite's cost the reason somebody stopped adding cases. What
    each structural row is about is the declaration and the view, so the
    cheapest honest candidate is the right one -- the gate's own two cases are
    the acceptance obligation and say so.
    """
    candidate = os.path.join(root, place)
    os.makedirs(os.path.join(candidate, "work"), exist_ok=True)
    with open(os.path.join(candidate, name), "w", encoding="utf-8") as writing:
        writing.write(body)
    return candidate
