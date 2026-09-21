"""Focused isolation checks for composer instance-derived facts. W202663,
review208890 item 3.

WHAT THIS PROVES. Loading `compose-verification-208217.py` fresh and
selecting two different fake instances, every instance-derived fact the
selection owns follows the SELECTED instance and never the module-load
constants: the destination, the persisted authority identity, the derived
Work id, the credential registry path, and -- the D5 fact -- the declared
base read from the selected target's own refs. Plus: `select_job` rebinds
the Job and its three participants together, and `select_emitting` moves the
IMPLEMENTATION image/recipe only.

WHAT IT TOUCHES. Two fake instance directories under a temporary root, each
holding an `authority-identity.json` and a target refs FILE (text files
written by this test; no version-control tool runs). Nothing real is read
beyond the composer module itself; nothing is written elsewhere.

The audit note this belongs to: both composers were swept for computed
signature defaults (the D5 class) -- `declared_base` was the only site, now
call-time in BOTH; `compose-pool-207219.py` still carries only the
superseded instance's constants and must gain instance selection before it
composes for another destination.
"""

import importlib.util
import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent

A_UUID = "aaaa208916" + "0" * 18 + "aaaa"
B_UUID = "bbbb208916" + "0" * 18 + "bbbb"
A_REV = "1111111111111111111111111111111111111111"
B_REV = "2222222222222222222222222222222222222222"


def fake_instance(root, name, uuid, revision):
    place = Path(root) / name
    (place / "repo/target.git/refs/heads").mkdir(parents=True)
    (place / "repo/target.git/refs/heads/main").write_text(revision + "\n")
    (place / "authority-identity.json").write_text(json.dumps(
        {"schema": "baton.v12.instance-identity/1", "authority_uuid": uuid}))
    return place


def loaded():
    spec = importlib.util.spec_from_file_location(
        "verification_composer", HERE / "compose-verification-208217.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    failures = []

    def check(name, passed):
        print(("ok   " if passed else "FAIL ") + name)
        if not passed:
            failures.append(name)

    m = loaded()
    historical = (str(m.DEST), m.UUID, m.WORK, str(m.CREDENTIAL_SOURCES))

    with tempfile.TemporaryDirectory(prefix="w202663-isolation-") as root:
        a = fake_instance(root, "instance-a", A_UUID, A_REV)
        b = fake_instance(root, "instance-b", B_UUID, B_REV)

        m.select_instance(str(a))
        check("A: DEST follows the selection", str(m.DEST) == str(a))
        check("A: authority is the instance's own persisted one",
              m.UUID == A_UUID)
        check("A: Work id derives from the selected authority",
              m.WORK == A_UUID[:8] + "-W1")
        check("A: credential registry lives under the selection",
              m.CREDENTIAL_SOURCES == str(a / "credentials/registry.json"))
        check("A: declared base is the SELECTED target's revision (D5)",
              m.declared_base() == A_REV)

        m.select_instance(str(b))
        check("B: declared base follows a SECOND selection (D5)",
              m.declared_base() == B_REV)
        check("B: authority follows too", m.UUID == B_UUID)
        check("B: nothing still answers instance A",
              str(a) not in (str(m.DEST), m.CREDENTIAL_SOURCES))
        check("historical constants appear nowhere after selection",
              all(one not in (str(m.DEST), m.UUID, m.WORK,
                              m.CREDENTIAL_SOURCES)
                  for one in historical))

        before_actors = dict(m.ACTORS)
        m.select_job("w202663-deterministic-verification-7")
        check("job: id follows", m.JOB == "w202663-deterministic-verification-7")
        check("job: all three participants take the job's suffix",
              m.ACTORS == {"implementation": "baton.fixture-coder-7",
                           "review": "baton.fixture-reviewer-7",
                           "integration": "baton.fixture-integrator-7"})
        check("job: participants actually moved",
              m.ACTORS != before_actors)
        check("job: the Work FOLLOWS the job (review209459: an independent "
              "Job carries its own fresh Work, never the completed one)",
              m.WORK == B_UUID[:8] + "-W7")
        m.select_job("w202663-deterministic-verification-8", work_number="12")
        check("job: an explicit --work overrides the suffix",
              m.WORK == B_UUID[:8] + "-W12")
        check("job: the explicit-work job id still moved",
              m.JOB == "w202663-deterministic-verification-8")

        images_before = dict(m.IMAGES)
        recipes_before = dict(m.RECIPES)
        m.select_emitting()
        check("emitting: implementation image is the emitting build",
              m.IMAGES["implementation"] == m.EMITTING_IMAGE)
        check("emitting: implementation recipe follows",
              m.RECIPES["implementation"] == m.EMITTING_RECIPE)
        check("emitting: review and integration are untouched",
              all(m.IMAGES[r] == images_before[r]
                  and m.RECIPES[r] == recipes_before[r]
                  for r in ("review", "integration")))

    fresh = loaded()
    check("a fresh load still answers the historical record",
          (str(fresh.DEST), fresh.UUID) == (historical[0], historical[1]))

    if failures:
        print(f"\n{len(failures)} isolation check(s) failed", file=sys.stderr)
        return 1
    print("all composer isolation checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
