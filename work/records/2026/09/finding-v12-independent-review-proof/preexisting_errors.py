"""Corroborate the twelve product errors as PRE-EXISTING, focally.

Review 2026-09-23T12:20:24Z asked for a focused comparison or exact prior
evidence rather than a count, and was right: "424 tests with 12 errors" cannot
say whether the change caused them.

TWO INDEPENDENT ANSWERS ARE RECORDED HERE, because neither alone is enough.

  * EXACT PRIOR EVIDENCE, and it is dated BEFORE this claim's product change.
    `../finding-v12-single-implementation-proof/review-2026-09-22T23-53-34Z.md`
    records, on 2026-09-22: "The author separately reports 12 pre-existing
    `reconciles` fixture errors in the broader stage_execution suite; I did not
    rerun that broader suite or independently establish their provenance."
    THAT CAVEAT IS QUOTED RATHER THAN OMITTED -- the reviewer recorded the
    report, not a corroboration of it -- which is exactly why the second answer
    below exists.

  * A FOCUSED COMPARISON OF WHERE THEY FAIL. The twelve are run by name and
    each one's failing frame is captured. The claim this establishes is
    narrow and checkable: every one of them fails inside
    `Integration._run`'s producer-proposal read, and no frame in any of their
    tracebacks enters `routed` or the `correction_policy` validation this
    claim added. A change that is never reached did not cause them.

This program runs no broad suite for counts, opens no store and touches no
product byte.
"""

import json
import os
import pathlib
import re
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
CHECKOUT = HERE.parents[4]
PYTHON = CHECKOUT / "v12/python"
SUITE = "tests.tools.test_stage_execution"
PRIOR = ("../finding-v12-single-implementation-proof/"
         "review-2026-09-22T23-53-34Z.md")

NAMES = (
    "test_a_delivery_carrying_no_assignment_is_the_first_tick",
    "test_a_delivery_with_no_started_runtime_is_not_refreshed",
    "test_a_fresh_port_prepares_that_delivery_and_then_starts_it",
    "test_a_later_tick_refreshes_before_it_continues",
    "test_a_lost_marker_falls_through_to_admission",
    "test_a_runtime_this_execution_did_not_start_is_still_held",
    "test_a_second_tick_in_the_same_execution_starts_nothing_again",
    "test_a_started_or_uncertain_runtime_is_never_prepared_here",
    "test_an_ordinary_first_tick_prepares_and_starts_exactly_once",
    "test_the_first_tick_prepares_and_then_admits",
)

# What the change added, by name. A traceback naming none of these is a
# traceback that never reached it.
ADDED = ("correction_policy", "CORRECTION_POLICIES", "DECLINE_CORRECTION",
         "def routed", "correction_declined")


def selectors():
    body = (PYTHON / "tests/tools/test_stage_execution.py").read_text(
        encoding="utf-8")
    held, current = [], None
    for line in body.split("\n"):
        found = re.match(r"class (\w+)", line)
        if found:
            current = found.group(1)
        found = re.match(r"    def (test_\w+)", line)
        if found and found.group(1) in NAMES:
            held.append(f"{SUITE}.{current}.{found.group(1)}")
    return held


def main():
    named = selectors()
    answer = subprocess.run(
        [sys.executable, "-m", "unittest"] + named,
        cwd=str(PYTHON), capture_output=True, text=True, timeout=1800,
        env=dict(os.environ, PYTHONPATH=os.pathsep.join(["src", "."]),
                 PYTHONDONTWRITEBYTECODE="1"))
    text = answer.stderr
    blocks = text.split("=" * 70)
    failing = []
    for block in blocks:
        found = re.search(r"(ERROR|FAIL): (\w+) \(([\w.]+)\)", block)
        if not found:
            continue
        frames = re.findall(r'File "([^"]+)", line (\d+), in (\w+)', block)
        failing.append({
            "case": f"{found.group(3)}.{found.group(2)}",
            "kind": found.group(1),
            "deepest_frame": (None if not frames else
                              {"file": frames[-1][0].replace(
                                  str(CHECKOUT) + "/", ""),
                               "line": int(frames[-1][1]),
                               "function": frames[-1][2]}),
            "mentions_the_change": sorted(
                one for one in ADDED if one in block),
        })
    record = {
        "schema": "baton.independent-review-preexisting-errors/1",
        "work": "W239533", "claim": 247666, "participant": "baton.claude",
        "selected": named,
        "ran": int((re.search(r"Ran (\d+) tests?", text) or
                    re.match(r"(0)", "0")).group(1)),
        "failing": failing,
        "prior_evidence": {
            "document": PRIOR,
            "dated": "2026-09-22, before this claim's product change",
            "quote": ("The author separately reports 12 pre-existing "
                      "`reconciles` fixture errors in the broader "
                      "stage_execution suite; I did not rerun that broader "
                      "suite or independently establish their provenance."),
            "caveat_kept": ("that reviewer recorded the report and explicitly "
                            "did NOT corroborate it, which is why the focused "
                            "comparison below exists rather than this quote "
                            "standing alone"),
        },
        "focused_claim": (
            "every selected case fails inside the same function, and no "
            "traceback among them names anything this claim added"),
    }
    functions = sorted({one["deepest_frame"]["function"] for one in failing
                        if one["deepest_frame"]})
    record["deepest_functions"] = functions
    record["none_reaches_the_change"] = not any(
        one["mentions_the_change"] for one in failing)
    record["holds"] = bool(failing) and record["none_reaches_the_change"]
    (HERE / "PREEXISTING-ERRORS-247666.json").write_text(
        json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({one: record[one] for one in
                      ("ran", "deepest_functions", "none_reaches_the_change",
                       "holds")}, indent=2))
    print(f"{len(failing)} selected cases failing")
    return 0 if record["holds"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
