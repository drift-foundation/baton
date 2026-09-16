"""Reversal probes for corrections179146 and179295. Each reverts ONE guard and must fail.

A probe that was tried and REMOVED is recorded in the evidence rather than
quietly dropped: substituting `shape["high"] == MODEL_KEY_CAP` for the named
OVERFLOW_SHAPES membership changes no behaviour at cap 8, so it reverted nothing
and was not evidence. The source comment that claimed otherwise was corrected.

A probe that passes is a test that was not testing anything. The manifest is
recomputed inside each copy so the only failures reported are the intended
ones rather than `fixture-drift` from every probe at once.

Bytecode discipline, learned at 178875: two patched variants can be identical
in length and land in the same mtime second, so Python's source cache serves
the previous probe's bytecode. Every probe runs with -B in its own directory.
"""
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent / "evidence"
NAMES = ("qualification-fixture.py", "qualification_contract.py", "qualification_worker.py", "test_qualification.py")

PROBES = [
    ("artifact-exact-only", "qualification_contract.py",
     '    if expected.endswith(b"\\n") and raw == expected[:-1]:\n        return "missing-final-lf"\n', "",
     "the second accepted form is gone"),
    ("artifact-strip", "qualification_contract.py",
     "    if raw == expected:\n        return \"exact\"\n",
     "    if raw.strip() == expected.strip():\n        return \"exact\"\n",
     "general whitespace tolerance instead of one newline"),
    # The consistency check moved into the shared validator when the failure
    # path stopped carrying its own copy; the probe follows it there.
    ("no-consistency-guard", "qualification_contract.py",
     "    return consistent(record)\n", "    return True\n",
     "a forged terminal record is no longer refused"),
    ("membership-not-identity", "qualification_contract.py",
     "        if not ((capped is True or capped is False) and (present is True or present is False)):\n",
     "        if not (capped in (True, False) and present in (True, False)):\n",
     "a truthy integer passes as a boolean"),
    ("constant-as-observed", "qualification-fixture.py",
     '        initial = c.artifact_record(c.read_file(workspace / "solution.py"), c.INITIAL)\n',
     '        initial = c.artifact_record(c.INITIAL, c.INITIAL)\n',
     "the export labels a constant as the observed artifact"),
    ("refuse-before-record-turn-2", "qualification-fixture.py",
     '        outcome.update(corrected_artifact=corrected, continuity_artifact=continuity)\n        save(root / "outcome.json", outcome)\n        c.require(corrected["form"] in c.ARTIFACT_FORMS and continuity["form"] == "exact", "correction-artifact")\n',
     '        c.require(corrected["form"] in c.ARTIFACT_FORMS and continuity["form"] == "exact", "correction-artifact")\n        outcome.update(corrected_artifact=corrected, continuity_artifact=continuity)\n        save(root / "outcome.json", outcome)\n',
     "a refused second-turn record no longer survives the refusal"),
    ("refuse-before-record", "qualification-fixture.py",
     '        outcome["initial_artifact"] = initial\n        save(root / "outcome.json", outcome)\n        c.require(initial["form"] in c.ARTIFACT_FORMS, "initial-artifact")\n',
     '        c.require(initial["form"] in c.ARTIFACT_FORMS, "initial-artifact")\n        outcome["initial_artifact"] = initial\n        save(root / "outcome.json", outcome)\n',
     "the observed record no longer survives a refusal"),
    # R1, review 2026-09-15T15-39-27Z -- one probe per NEW relationship.
    ("no-cardinality-bounds", "qualification_contract.py",
     '        if not (type(count) is int and shape["low"] <= count <= shape["high"]):\n',
     '        if not (type(count) is int and 0 <= count <= MODEL_KEY_CAP):\n',
     "the old range check: a singleton may report any in-range count"),
    ("no-overflow-rule", "qualification_contract.py",
     '        if capped and not (count == MODEL_KEY_CAP and usage in OVERFLOW_SHAPES):\n            return False\n', "",
     "overflow may be claimed by any shape at any count"),
    ("no-usage-member-rule", "qualification_contract.py",
     '    if ("modelUsage" in members) != shape["member"]:\n        return False\n', "",
     "a modelUsage diagnostic about an absent member is admitted"),
    ("no-model-member-rule", "qualification_contract.py",
     '    if ("model" in members) != (model != "missing"):\n        return False\n', "",
     "a model diagnostic about an absent member is admitted"),
    ("no-expected-key-rule", "qualification_contract.py",
     '        if present is not shape["expected_key"]:\n            return False\n', "",
     "the expected-key flag need not match its shape"),
    # Owner 2026-09-15T18:04:42Z -- the fresh identity bindings.
    # The direct identity preparation moved the fixture to 20260916T035035Z
    # between claims; the probes follow the current constant, one per consumed
    # name, all four of which are now consumed.
    ("identity-back-to-consumed", "qualification-fixture.py",
     'IDENTITY = "20260916T035035Z"\n', 'IDENTITY = "180078"\n',
     "a consumed run identity is reachable again"),
    ("identity-back-to-the-first-consumed", "qualification-fixture.py",
     'IDENTITY = "20260916T035035Z"\n', 'IDENTITY = "178579"\n',
     "the first consumed run identity is reachable again"),
    ("identity-back-to-the-third-consumed", "qualification-fixture.py",
     'IDENTITY = "20260916T035035Z"\n', 'IDENTITY = "183114"\n',
     "the third consumed run identity is reachable again"),
    ("identity-back-to-the-fourth-consumed", "qualification-fixture.py",
     'IDENTITY = "20260916T035035Z"\n', 'IDENTITY = "183372"\n',
     "the fourth consumed run identity is reachable again"),
    ("no-declared-root-check", "qualification-fixture.py",
     '              manifest["private_root"] == str(ROOT) and manifest["credential_copy_root"] == str(VOLATILE) and\n              manifest["export_root"] == str(export_root()) and manifest["run_identity"] == IDENTITY, "manifest-constants")\n',
     '              True, "manifest-constants")\n',
     "an approved manifest may declare an identity the code does not take"),
    # Derived from VOLATILE rather than an absolute literal ON PURPOSE. The
    # first version of this probe returned a hard-coded /tmp path, so when the
    # patched tests called run() the reservation loop created the REAL export
    # root of the fresh identity -- a probe reaching outside its sandbox and
    # quietly consuming the very identity this turn prepares. VOLATILE is
    # patched by those tests, so this variant stays inside the temporary tree
    # and still breaks both derivation checks.
    ("export-root-pinned-not-derived", "qualification-fixture.py",
     '    return ROOT.with_name(ROOT.name + "-export")\n',
     '    return VOLATILE.with_name(VOLATILE.name + "-export")\n',
     "the export root stops following ROOT and is derived from another operand"),
    # Owner182261, CORRECTION-PROPOSAL-180537.md revision 2.
    ("publish-in-any-turn", "qualification_worker.py",
     "    if turn != 1:\n        return None\n", "",
     "P1a stops being turn-1 only and would aim at the restored 0o660 copy"),
    ("publish-without-uid-check", "qualification_worker.py",
     '    if info.st_uid != os.geteuid():\n        raise c.publication_failure("publish-ownership", "target-owner")\n', "",
     "an object owned by another uid may be relaxed"),
    ("publish-without-gid-check", "qualification_worker.py",
     '    if info.st_gid != c.GROUP:\n        raise c.publication_failure("publish-ownership", "target-group")\n', "",
     "an object outside the workspace group may be relaxed"),
    ("tolerate-unlistable-directory", "qualification_contract.py",
     '        try:\n            entries = os.scandir(place)\n        except OSError as failure:\n            raise wrapped("state-coverage-incomplete", failure.errno) from None\n        with entries:\n',
     "        with os.scandir(place) as entries:\n",
     "an unlistable directory stops refusing, making the absence claims vacuous"),
    ("tolerate-unstattable-entry", "qualification_contract.py",
     '                try:\n                    info = entry.stat(follow_symlinks=False)\n                except OSError as failure:\n                    raise wrapped("state-coverage-incomplete", failure.errno) from None\n',
     "                info = entry.stat(follow_symlinks=False)\n",
     "an unstattable entry stops refusing -- a valid synthetic regression, not the observed operator result"),
    ("accept-unreadable-selected", "qualification_contract.py",
     '    require(selected[0]["content"] == "read" and type(selected[0]["sha256"]) is str, "selected-session-unreadable")\n', "",
     "an unreadable selected session is promoted"),
    ("no-failure-detail", "qualification-fixture.py",
     '        detail = {"step": outcome.get("collection_step"), **c.failure_detail(error)}\n',
     '        detail = {"step": None, "category": "other", "errno": "none"}\n',
     "the closed triple stops naming the step and kind"),
    # review-2026-09-16T00-41-09Z R1-R3.
    # Supersedes the claim182264 `publish-follows-symlinks` probe, whose target
    # line no longer exists: R1 replaced final-component O_NOFOLLOW with a
    # descriptor chain, so the meaningful reversal is now the whole ancestry.
    ("publish-follows-ancestors", "qualification_worker.py",
     "    flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | (os.O_DIRECTORY if directory else 0)\n",
     "    flags = os.O_RDONLY | os.O_NONBLOCK | (os.O_DIRECTORY if directory else 0)\n",
     "a symlinked ancestor is followed out of the home again"),
    ("publish-allows-aliases", "qualification_worker.py",
     '    if not directory and info.st_nlink != 1:\n        raise c.publication_failure("publish-alias", "target-alias")\n', "",
     "a hardlinked session is chmodded through its alias"),
    ("survey-reopens-by-path", "qualification_worker.py",
     '        project = state["keep"].get(state["projects"][0])\n        selected = state["keep"].get("selected")\n',
     '        project = _open_at(home_fd, state["projects"][0].split("/")[-1], True)\n        selected = _open_at(project, session + ".jsonl", False)\n',
     "the targets are reopened by path instead of being the surveyed descriptors"),
    ("survey-not-home-wide", "qualification_worker.py",
     "        child = _open_at(fd, name, True)\n        if relative == PROJECTS:\n",
     "        if not (path in (\".claude\", PROJECTS) or relative in (\".claude\", PROJECTS) or path.startswith(PROJECTS)):\n            continue\n        child = _open_at(fd, name, True)\n        if relative == PROJECTS:\n",
     "the survey descends only the projects chain again"),
    ("publish-skips-the-survey", "qualification_worker.py",
     '        if state["sessions"] != [expected]:\n            raise c.publication_failure("publish-shape", "session-set")\n', "",
     "a foreign or nested session publishes before it is refused"),
    ("publish-skips-credential-shape", "qualification_worker.py",
     '        if CREDENTIAL.search(name):\n            raise c.publication_failure("publish-shape", "credential-name")\n', "",
     "a credential-shaped entry publishes before it is refused"),
    ("coverage-drops-the-cause", "qualification_contract.py",
     '        except OSError as failure:\n            raise wrapped("state-coverage-incomplete", failure.errno) from None\n',
     '        except OSError:\n            raise Refusal("state-coverage-incomplete") from None\n',
     "the coverage refusal throws away the errno it was raised for"),
    ("cause-without-a-relationship", "qualification_contract.py",
     '    return record["cause"] == "none" or record["category"] == "known-refusal"\n',
     "    return True\n",
     "an os-error may claim to have wrapped a cause"),
    # OFFLINE-CORRECTION-CYCLE-183114.
    ("publication-without-a-check", "qualification_worker.py",
     '        if CREDENTIAL.search(name):\n            raise c.publication_failure("publish-shape", "credential-name")\n',
     '        if CREDENTIAL.search(name):\n            raise c.Refusal("publish-shape")\n',
     "a publication refusal stops naming which check it failed"),
    ("publication-loses-the-errno", "qualification_worker.py",
     '        raise c.publication_failure("publish-shape", "listing", failure.errno) from None\n',
     '        raise c.publication_failure("publish-shape", "listing") from None\n',
     "an operation failure stops carrying its errno category"),
    ("observe-after-publishing", "qualification_worker.py",
     '        observed = {"provider_exit": code, "terminal": c.projection(raw, request["session"])}\n        published = publish(request["session"], request["turn"])\n',
     '        published = publish(request["session"], request["turn"])\n        observed = {"provider_exit": code, "terminal": c.projection(raw, request["session"])}\n',
     "run183114's ordering returns: a publication failure discards the observation"),
    ("drop-the-preserved-observation", "qualification_worker.py",
     '                  "observed": observed}\n', '                  "observed": None}\n',
     "the observation is made and then thrown away"),
    ("accept-a-forged-observation", "qualification-fixture.py",
     '            c.require(c.valid_terminal(preserved["terminal"], session), "worker-failure-shape")\n',
     '            c.require(True, "worker-failure-shape")\n',
     "a preserved observation is no longer validated at all"),
    # review-2026-09-16T03-18-48Z.
    ("failure-path-shorter-validator", "qualification-fixture.py",
     '            c.require(c.valid_terminal(preserved["terminal"], session), "worker-failure-shape")\n',
     '            c.require(type(preserved["terminal"]) is dict and set(preserved["terminal"]) == c.TERMINAL_MEMBERS, "worker-failure-shape")\n',
     "the failure path gets its own shorter validator again"),
    ("publication-untyped", "qualification_contract.py",
     '    if type(record["check"]) is not str or type(record["errno"]) is not str:\n        return False\n', "",
     "an unhashable check or errno raises out of the validator instead of being refused"),
    ("target-metadata-unwrapped", "qualification_worker.py",
     '    try:\n        info = os.fstat(fd)\n    except OSError as failure:\n',
     '    if True:\n        info = os.fstat(fd)\n    if False:\n        failure = None\n',
     "the target metadata read escapes as unclassified with a null diagnostic"),
    # review-2026-09-16T03-26-33Z.
    ("terminal-sets-before-types", "qualification_contract.py",
     '    if not string_list(record["members"]) or not set(record["members"]) <= KNOWN_FIELDS:\n',
     '    if type(record["members"]) is not list or not set(record["members"]) <= KNOWN_FIELDS:\n',
     "an unhashable member raises out of valid_terminal instead of being refused"),
    ("diagnostics-untyped", "qualification_contract.py",
     "    if type(model) is not str or type(usage) is not str:\n        return False\n", "",
     "an unhashable model diagnostic raises out of consistent instead of being refused"),
    # OFFLINE-CUSTODY-CORRECTION-20260916.
    ("publish-only-the-two-objects", "qualification_worker.py",
     "                for fd in directories:\n                    os.fchmod(fd, 0o2750)\n",
     "                os.fchmod(directories[-1], 0o2750)\n",
     "only one directory is published again, so whole-HOME coverage still fails"),
    ("publish-file-contents-too", "qualification_worker.py",
     '        mine = info.st_uid == os.geteuid() and info.st_gid == c.GROUP\n',
     '        mine = True\n',
     "objects that are not runtime-owned directories are published"),
    ("no-directory-bound", "qualification_worker.py",
     '            if len(state["directories"]) > c.PUBLISH_DIRECTORIES:\n                raise c.publication_failure("publish-shape", "directory-bound")\n', "",
     "the retained directory descriptors are unbounded"),
]

results = []
for label, filename, old, new, expectation in PROBES:
    with tempfile.TemporaryDirectory(prefix="w177936-probe-") as place:
        copy = Path(place) / "evidence"
        copy.mkdir()
        for name in NAMES + ("qualification-manifest.json",):
            shutil.copy2(HERE / name, copy / name)
        text = (copy / filename).read_text()
        assert text.count(old) == 1, (label, filename)
        (copy / filename).write_text(text.replace(old, new))
        manifest = json.loads((copy / "qualification-manifest.json").read_bytes())
        for name in manifest["files"]:
            manifest["files"][name] = hashlib.sha256((copy / name).read_bytes()).hexdigest()
        (copy / "qualification-manifest.json").write_bytes(json.dumps(manifest, indent=1, sort_keys=True).encode() + b"\n")
        for stale in copy.glob("__pycache__"):
            shutil.rmtree(stale)
        done = subprocess.run([sys.executable, "-B", str(copy / "test_qualification.py")],
                              capture_output=True, text=True, timeout=120, cwd=place)
        failed = sorted(set(re.findall(r"^(?:FAIL|ERROR): (\w+) \(", done.stderr, re.M)))
        results.append({"probe": label, "file": filename, "reverts": expectation,
                        "exit_code": done.returncode, "failing_tests": failed})
        print(json.dumps(results[-1], indent=1))

Path(__file__).resolve().parent.joinpath("evidence/probes-179146.json").write_text(
    json.dumps({"probes": results, "note": "each probe reverts one guard in an isolated copy; every probe must fail"}, indent=1) + "\n")
print("\nall probes failed as required:", all(r["exit_code"] != 0 and r["failing_tests"] for r in results))
