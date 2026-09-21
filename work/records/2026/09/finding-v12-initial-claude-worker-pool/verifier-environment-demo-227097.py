#!/usr/bin/env python3
"""W202663 claim227097 — the EXACT frozen verifier, in its ACTUAL environment.

Review226905 [3]: the producer's manual 160-OK ran with
`BATON_V12_STACK_TEST_ROOT` exported, but the adapter's frozen invocation
composes only HOME/PATH and the three ephemera, and the container's default
`/var/tmp` is read-only -- so the manual green proved nothing about the
invocation that actually gates a candidate. This demonstration answers that
question deterministically, with the adapter's OWN code path:

  * the candidate is `git archive` of the accepted base 446fa8f7 (read-only;
    no Git mutation), plus the claim225590-precedent LABELED discovery
    fixture `test_pool.py` (launch plumbing proof only, NOT coverage);
  * the environment is composed by the REAL `ClaudeAgent` members --
    `_closed_environment` then `_pinned_environment`, so the verifier sees
    `/proc/self/fd/<n>` names over held directory objects, exactly as in the
    container;
  * the command is the EXACT corrected verification argv read from
    `compose-pool-207219.py`'s own task document (no second spelling);
  * the run is the REAL `_verify` (real subprocess, real bound, real
    transcript path), with `BATON_V12_STACK_TEST_ROOT` deliberately absent.

Two cases:
  1. UNSET  -- the argv must establish the fixture root ITSELF, under the
     invocation's own TMPDIR (the held ephemera object), and exit 0.
  2. EXPORTED -- an explicit operator selection must be respected: no
     argv-made root appears, the exported root is the one used, exit 0.

No container, no image, no provider, no live episode. Evidence lands in
VERIFIER-ENV-DEMO-227097.json beside this script.
"""

import glob
import importlib.util
import json
import os
import pathlib
import subprocess
import sys
import tarfile
import tempfile
import time

HERE = pathlib.Path(__file__).resolve().parent
REPO = pathlib.Path("/home/sl/src/baton")
BASE = "446fa8f79d9569799a77e888e8236070e1dc78f7"
WORKER = REPO / "v12" / "worker"
EVIDENCE = HERE / "VERIFIER-ENV-DEMO-227097.json"

FIXTURE = '''\
"""CLAIM227097 DEMONSTRATION FIXTURE -- NOT COVERAGE, NOT THE REAL test_pool.

The frozen argv names `tests.tools.test_pool`, which exists only once a
producer writes it. This file exists so the demonstration can run the EXACT
argv (claim225590 precedent: a discovery proof, clearly labeled); its one
case asserts nothing about any product behaviour.
"""

import unittest


class TheDemonstrationFixtureLoads(unittest.TestCase):
    def test_discovery_reaches_this_module(self):
        self.assertTrue(True)
'''


def composed_argv():
    """The exact task verification argv, from the composer's own document."""
    spec = importlib.util.spec_from_file_location(
        "compose_pool_207219", HERE / "compose-pool-207219.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.task_document({"declared_base": BASE})["verification"]


def candidate_at_base(root):
    """`git archive` of the accepted base, extracted -- read-only on the repo."""
    candidate = os.path.join(root, "candidate")
    os.mkdir(candidate)
    archive = os.path.join(root, "base.tar")
    with open(archive, "wb") as out:
        subprocess.run(["git", "-C", str(REPO), "archive", BASE],
                       check=True, stdout=out)
    with tarfile.open(archive) as held:
        held.extractall(candidate, filter="data")
    os.unlink(archive)
    fixture = os.path.join(candidate, "v12", "python", "tests", "tools",
                           "test_pool.py")
    with open(fixture, "w", encoding="utf-8") as out:
        out.write(FIXTURE)
    return candidate


def verified(argv, candidate, exported=None):
    """One real `_verify` run over a freshly composed pinned environment."""
    sys.path.insert(0, str(WORKER))
    sys.path.insert(0, str(REPO / "v12" / "python" / "src" / "baton_v12"))
    import claude_agent

    agent = claude_agent.ClaudeAgent()
    agent._seen = None
    scratch = tempfile.mkdtemp(prefix="verifier-demo-")
    os.chmod(scratch, 0o700)
    home = agent._new_directory(scratch, claude_agent.VERIFICATION_HOME)
    _root, roots = agent._new_ephemera(
        scratch, claude_agent.VERIFICATION_EPHEMERA)
    environment = agent._closed_environment(
        home=home, roots=roots, scratch=scratch)
    pinned, held = agent._pinned_environment(scratch, environment)
    if exported is not None:
        pinned = dict(pinned, BATON_V12_STACK_TEST_ROOT=exported)
    task = {"task_id": "w202663-verifier-env-demo", "verification": argv}
    started = time.monotonic()
    answer = agent._verify(task, candidate, pinned, held)
    elapsed = time.monotonic() - started
    made = glob.glob(os.path.join(roots["TMPDIR"], "stack-test-root-*"))
    for _name, descriptor in held:
        os.close(descriptor)
    return {"status": answer["status"], "transcript": answer["text"],
            "elapsed_seconds": elapsed,
            "tmpdir_real_path": roots["TMPDIR"],
            "argv_made_roots_under_tmpdir": made,
            "environment_names": sorted(pinned)}


def partition(candidate):
    """The measured split of `test_bootstrap` at the accepted base.

    An EXPLICIT memory-filesystem root is refused by name by exactly the
    classes whose `_disk_root_outside_the_checkout` demand cannot be met
    in-container (read-only rootfs, memory /tmp and /dev/shm, and /output IS
    the checkout); everything else runs. The refusing class list is what the
    corrected argv excludes, and the passing count is its floor.
    """
    program = (
        "import os, sys, unittest\n"
        "os.chdir('v12/python')\n"
        "sys.path[:0] = [os.path.abspath('src'), os.path.abspath('.')]\n"
        "loader = unittest.TestLoader()\n"
        "suite = loader.loadTestsFromName('tests.tools.test_bootstrap')\n"
        "quiet = open(os.devnull, 'w')\n"
        "result = unittest.TextTestRunner(verbosity=0, stream=quiet)"
        ".run(suite)\n"
        "import json\n"
        "print(json.dumps({'total': result.testsRun,\n"
        "  'refused': len(result.failures) + len(result.errors),\n"
        "  'refusing_classes': sorted({type(one).__name__ for one, _ in\n"
        "      result.failures} | {type(one).__name__ for one, _ in\n"
        "      result.errors})}))\n")
    done = subprocess.run(
        [sys.executable, "-c", program], cwd=candidate, text=True,
        capture_output=True, timeout=600,
        env={"HOME": candidate, "PATH": os.environ.get("PATH", ""),
             "BATON_V12_STACK_TEST_ROOT": "/dev/shm"})
    return json.loads(done.stdout.strip().splitlines()[-1])


def main():
    argv = composed_argv()
    with tempfile.TemporaryDirectory(prefix="w202663-demo-") as root:
        candidate = candidate_at_base(root)

        divided = partition(candidate)
        unset = verified(argv, candidate)
        exported_root = os.path.join(root, "operator-selected-root")
        os.mkdir(exported_root)
        exported = verified(argv, candidate, exported=exported_root)

        evidence = {
            "schema": "baton.w202663.verifier-env-demo/1",
            "claim": 227097,
            "base": BASE,
            "argv": argv,
            "fixture": "labeled discovery-only test_pool (claim225590 "
                       "precedent); not coverage",
            "partition": {
                **divided,
                "proves": "at the accepted base, the refusing classes "
                          "demand a disk-backed writable root OUTSIDE the "
                          "checkout, which the container cannot offer by "
                          "mount contract (read-only rootfs, memory /tmp "
                          "and /dev/shm, /output IS the git-line checkout); "
                          "they refuse rather than skip, so the corrected "
                          "argv excludes exactly these by name and floors "
                          "the count at the runnable remainder plus "
                          "test_pool; the full family still gates every "
                          "host rerun",
            },
            "case_unset": {
                **unset,
                "proves": "the exact frozen argv, in the adapter's own "
                          "pinned closed environment with "
                          "BATON_V12_STACK_TEST_ROOT ABSENT, establishes "
                          "its fixture root under the invocation's own "
                          "TMPDIR (the held ephemera object) and exits 0",
            },
            "case_exported": {
                **exported,
                "exported_root": exported_root,
                "proves": "an explicit operator selection is respected: "
                          "the argv makes NO root of its own and exits 0",
            },
        }
        acceptable = (
            unset["status"] == 0
            and len(unset["argv_made_roots_under_tmpdir"]) == 1
            and exported["status"] == 0
            and exported["argv_made_roots_under_tmpdir"] == []
            and divided["total"] - divided["refused"] == 50
            and len(divided["refusing_classes"]) == 11)
        evidence["acceptable"] = acceptable
        with open(EVIDENCE, "w", encoding="utf-8") as out:
            json.dump(evidence, out, indent=1, sort_keys=True)
            out.write("\n")
        print(json.dumps({k: evidence[k] for k in
                          ("acceptable", "base")}, indent=1))
        print("case_unset:", unset["status"], unset["transcript"][-120:])
        print("case_exported:", exported["status"],
              exported["transcript"][-120:])
        return 0 if acceptable else 1


if __name__ == "__main__":
    sys.exit(main())
