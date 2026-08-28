"""Independent W26328 reproduction: offset paging skips live Work."""

import pathlib
import sys
import tempfile


REPOSITORY = pathlib.Path(__file__).resolve().parents[6]
sys.path.insert(0, str(REPOSITORY / "src"))
sys.path.insert(0, str(REPOSITORY / "tests" / "work"))

import baton_work as bw  # noqa: E402
from baton_work import projection, transitions  # noqa: E402
import fixtures  # noqa: E402


with tempfile.TemporaryDirectory(prefix="w26328-review-") as directory:
    store = fixtures.open_instance(directory)
    made = [
        transitions.create_work(
            store, team="lang", kind="rsrch", title=f"waiting {index}",
            origin="external-report", author="ada",
            classification="confirmed-defect", body="body")["work_id"]
        for index in range(4)
    ]

    first = projection.actionable_work(
        store, viewer_team="lang", viewer_member="ada", limit=2)
    assert [row["id"] for row in first["rows"]] == made[:2]
    assert first["next_after"] == 2

    # A normal action between pages removes an earlier row from the current
    # actionable set. A keyset cursor would still continue after `made[1]`;
    # the submitted positional offset now starts one row too late.
    transitions.claim_work(store, made[0], actor_team="lang", actor="ada")
    second = projection.actionable_work(
        store, viewer_team="lang", viewer_member="ada",
        after=first["next_after"], limit=2)

    returned = [row["id"] for row in second["rows"]]
    print("page one:", [row["local_id"] for row in first["rows"]])
    print("still-actionable unseen:", [work.rsplit("-", 1)[1]
                                        for work in made[2:]])
    print("page two after the earlier claim:",
          [row["local_id"] for row in second["rows"]])
    assert returned == [made[3]]
    assert made[2] not in returned
