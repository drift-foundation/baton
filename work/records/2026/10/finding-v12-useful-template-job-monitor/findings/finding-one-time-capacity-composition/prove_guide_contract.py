#!/usr/bin/env python3
"""Drive the selected guide's verification contract to real outcomes.

Review 2026-10-27T18-27-26Z [R1] asks for exactly this: "prove missing/wrong/
stale guide outcomes refuse while a qualifying output passes". Nothing here is
asserted -- every case RUNS `guide_contract.verification()` as the workload
runs it, in a workspace this script creates and owns, and records the exit code
and the message.

THE FIXTURE GUIDE IS A FIXTURE AND IS LABELLED ONE. `fixtures/qualifying-
TEMPLATE-JOBS.md` exists so the positive outcome can be driven; it is NOT the
deliverable and is not part of the composition the installer consumes. Writing
the real guide is the Job's work and this preparation does not do it.

THE WORKSPACE IS OWNED. Each case runs in a `mkdtemp` directory this call
created, holding a real `v12/` with a SYMLINK to the checkout's `v12/python`
so the owning parsers are the real ones and nothing is written into the
repository. Only directories this invocation created are ever removed.
"""
import io
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import capacity                                              # noqa: E402
import guide_contract                                        # noqa: E402

REPOSITORY = capacity.REPOSITORY
FIXTURES = HERE / "fixtures"


def workspace(root, guide_text, *, quickstart=True):
    """A staged source root: real `v12/`, the checkout's own parsers."""
    place = pathlib.Path(tempfile.mkdtemp(prefix="guide-case-", dir=str(root)))
    (place / "v12").mkdir()
    os.symlink(str(REPOSITORY / "v12" / "python"), str(place / "v12/python"))
    if quickstart:
        shutil.copyfile(str(REPOSITORY / "v12/QUICKSTART.md"),
                        str(place / "v12/QUICKSTART.md"))
    if guide_text is not None:
        (place / "v12/TEMPLATE-JOBS.md").write_text(guide_text,
                                                    encoding="utf-8")
    return place


def ran(place, sections=()):
    """Run the verification argv exactly as the workload would.

    `sections` empty is the DEFAULT contract -- no format gate at all. The
    non-empty form is what `capacity.installed_task(proposed_format=True)`
    composes, and then the task's own instructions carry the addendum that
    announces exactly these headings.
    """
    done = subprocess.run(guide_contract.verification(sections),
                          cwd=str(place), capture_output=True, text=True,
                          timeout=300)
    return {"exit": done.returncode,
            "format_selected": bool(sections),
            "said": " ".join((done.stdout + done.stderr).split())[:400]}


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    scratch = pathlib.Path(argv[0] if argv else capacity.SCRATCH)
    if not scratch.is_dir():
        print("refused: no scratch root at " + str(scratch), file=sys.stderr)
        return 2
    root = pathlib.Path(tempfile.mkdtemp(prefix="w367232-guidecases-",
                                         dir=str(scratch)))
    qualifying = (FIXTURES / "qualifying-TEMPLATE-JOBS.md").read_text()
    cases, failures = {}, []

    # -- the defect the review found, driven ---------------------------------
    # The INHERITED pilot contract, run against a tree that has the quickstart
    # and no selected guide: it exits 0. This is the false success, reproduced
    # rather than described.
    inherited = json.loads(
        (capacity.PILOT.parent / "task.json").read_text())["verification"]
    place = workspace(root, None)
    done = subprocess.run(inherited, cwd=str(place), capture_output=True,
                          text=True, timeout=300)
    cases["inherited_pilot_contract_on_a_tree_without_the_guide"] = {
        "exit": done.returncode,
        "said": " ".join((done.stdout + done.stderr).split())[:200],
        "guide_present": (place / "v12/TEMPLATE-JOBS.md").exists(),
        "meaning": "exit 0 with the deliverable absent -- R1's false success"}
    if done.returncode != 0:
        failures.append("the inherited pilot contract did not reproduce its "
                        "false success")

    # -- and the selected contract on the same tree --------------------------
    cases["selected_contract_missing_guide"] = ran(workspace(root, None))
    cases["selected_contract_quickstart_only"] = ran(
        workspace(root, None, quickstart=True))

    # -- THE FORMAT IS A SELECTION, AND BY DEFAULT IT IS NOT MADE -----------
    # review-2026-10-27T18-50-04Z: "Do not treat a differently organized
    # semantically correct guide as proof of product failure." It is not one.
    # A guide with its own headings, covering the same ground and documenting
    # the same commands, PASSES the default contract -- driven here, not
    # claimed.
    renamed = qualifying
    for one, instead in zip(guide_contract.SECTIONS,
                            ("# 1. Standing the Job up",
                             "# 2. The operands, one at a time",
                             "# 3. Observation",
                             "# 4. The verdict and the hold",
                             "# 5. Failures",
                             "# 6. What the human decides")):
        renamed = renamed.replace(one, instead)
    cases["differently_organised_guide_passes_by_default"] = ran(
        workspace(root, renamed))
    # And the SAME file is refused once the format addendum is selected,
    # because then the task told its author what the shape had to be.
    cases["differently_organised_guide_refused_when_format_selected"] = ran(
        workspace(root, renamed), guide_contract.SECTIONS)

    # -- a guide that is there but does not satisfy its contract -------------
    cases["sections_missing"] = ran(workspace(
        root, "# Template Jobs\n\nNothing but a title.\n"),
        guide_contract.SECTIONS)
    cases["sections_out_of_order"] = ran(workspace(root, "\n\n".join(
        [qualifying.split("## Creating the Job")[0]]
        + list(reversed(guide_contract.SECTIONS)))),
        guide_contract.SECTIONS)
    cases["template_version_absent"] = ran(workspace(
        root, qualifying.replace(guide_contract.TEMPLATE_VERSION,
                                 "baton.v12.job-template.implementation-"
                                 "review/999")))
    cases["unresolved_marker"] = ran(workspace(
        root, qualifying.replace("## The human disposition",
                                 "## The human disposition\n\nTODO: finish")))

    # -- STALE: written against a CLI this build does not serve --------------
    cases["stale_subcommand"] = ran(workspace(
        root, qualifying.replace('baton-v12-stack" status',
                                 'baton-v12-stack" job-status')))
    cases["stale_option"] = ran(workspace(
        root, qualifying.replace("--work-scope v12/TEMPLATE-JOBS.md",
                                 "--scope v12/TEMPLATE-JOBS.md")))
    # AND ONE THAT REACHES THE OWNING PARSER. The case above is caught by this
    # contract's own required-operand list before argparse sees it, so it does
    # not show that the guide is checked against the IMPLEMENTATION. These two
    # keep every required operand and add one the parser does not serve, so
    # the refusal is the product's own.
    cases["stale_create_option_refused_by_the_parser"] = ran(workspace(
        root, qualifying.replace("--source installed",
                                 "--source installed --retry-limit 2")))
    cases["stale_monitor_option_refused_by_the_parser"] = ran(workspace(
        root, qualifying.replace("monitor --instance",
                                 "monitor --follow --instance")))
    cases["wrong_template_version_in_the_example"] = ran(workspace(
        root, qualifying.replace(
            "--template " + guide_contract.TEMPLATE_VERSION,
            "--template baton.v12.job-template.implementation-review/2")))
    cases["create_example_authors_a_document"] = ran(workspace(
        root, qualifying.replace("--source installed",
                                 "--source installed --document sub.json")))
    cases["undefined_expansion"] = ran(workspace(
        root, qualifying.replace('--instance "$DEST/instance.json"',
                                 '--instance "$UNDEFINED/instance.json"')))

    # -- and the qualifying output passes, in BOTH modes ---------------------
    cases["qualifying_guide"] = ran(workspace(root, qualifying))
    cases["qualifying_guide_with_the_format_selected"] = ran(
        workspace(root, qualifying), guide_contract.SECTIONS)

    passes = ("qualifying_guide", "qualifying_guide_with_the_format_selected",
              "differently_organised_guide_passes_by_default",
              "inherited_pilot_contract_on_a_tree_without_the_guide")
    must_refuse = [name for name in cases if name not in passes]
    for name in must_refuse:
        if cases[name]["exit"] == 0:
            failures.append("%s passed and had to refuse" % name)
    for name in passes[:3]:
        if cases[name]["exit"] != 0:
            failures.append("%s did not pass: %s" % (name,
                                                     cases[name]["said"]))

    answer = {"schema": "baton.v12.guide-contract-proof/1",
              "effects": {"created": [str(root)], "removed": [],
                          "retained": [str(root)]},
              "fixture": {
                  "path": str((FIXTURES
                               / "qualifying-TEMPLATE-JOBS.md").relative_to(
                                   capacity.REPOSITORY)),
                  "sha256": capacity._digest_of(
                      FIXTURES / "qualifying-TEMPLATE-JOBS.md"),
                  "this_is_not_the_deliverable":
                      "a verification fixture only; writing v12/TEMPLATE-"
                      "JOBS.md is the Job's own work"},
              "verification_argv_sha256": {
                  "default": capacity.sha256_of(json.dumps(
                      guide_contract.verification(), sort_keys=True).encode()),
                  "format_selected": capacity.sha256_of(json.dumps(
                      guide_contract.verification(guide_contract.SECTIONS),
                      sort_keys=True).encode())},
              "the_format_is_a_selection": {
                  "default": "no heading is checked; a differently organised "
                             "guide passes",
                  "selected": "the six headings are checked AND the task's "
                              "own instructions carry the addendum that "
                              "announces them (capacity.FORMAT_ADDENDUM)",
                  "withdrawn": "the previous cut claimed the parent "
                               "enumerates these headings. It does not; "
                               "USEFUL-JOB.md enumerates topics."},
              "cases": cases,
              "refusals_required": sorted(must_refuse),
              "failures": failures,
              "semantic_judgment": "this contract is mechanical; the five "
                                   "acceptance criteria remain the "
                                   "independent reviewer's",
              "ok": not failures}
    json.dump(answer, sys.stdout, indent=1, sort_keys=True)
    sys.stdout.write("\n")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
