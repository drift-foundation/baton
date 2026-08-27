"""W9707 — run the safe v12 source tests across the host's available CPUs.

`work/records/2026/08/finding-v12-parallel-test-runner/`.

The canonical `just test` recipe runs ONE `unittest` process over the whole
source tree. On the 16-core/32-CPU development host that measured 423.54s
elapsed against 422.65s user: one CPU, all of it, for seven minutes, while the
other thirty-one idled. The baseline is
`evidence/serial-pure-baseline-2026-08-25.txt`.

WHAT THIS IS NOT. It is not `pytest -n`, and it is not a shell fan-out over the
module list. Parallelism here is a property of the HARNESS and never of the
product: nothing under `src/` learns that it might be run concurrently. Every
shard is a fresh interpreter, which is most of the safety proof — module
`sys.path` and environment state, live-secret registries, SQLite handles, mocks
and worker-entry counters cannot cross a process boundary. The rest of the
proof is the registry below, which is EXPLICIT and FAILS CLOSED: a test module
that belongs to neither list stops the runner rather than being guessed into
the parallel phase.

WHY CLASSES AND NOT MODULES. A module-level partition was measured and
rejected: the baseline showed `test_boundary_inventory`'s whole-universe scans
dominating the wall clock, so a module fan-out would have kept exactly one long
pole and bought much less than it looks like it would. The ordinary shard is
therefore one concrete `TestCase` class, and the two aggregate scan classes are
split one test METHOD per shard. That split is safe to state as a rule because
no source test outside `tests/manager/test_worker_container.py` declares
`setUpClass`/`tearDownClass`/`setUpModule`/`tearDownModule`, so splitting a
class bypasses no shared fixture — and that module is serial anyway.

COMPLETION ORDER NEVER DECIDES PRESENTATION. The parent drains every scheduled
shard before it prints anything about results, then reports in sorted shard
order. A run whose shards finish in a different order every time still produces
byte-identical stdout, which is what makes `jobs=1` and `jobs=32` comparable at
all. Durations and live progress go to stderr, where they cannot make stdout
nondeterministic.

THE PARENT NEVER IMPORTS A TEST MODULE. Collection happens in disposable child
interpreters that report exact `unittest` ids back as JSON; the parent only
ever partitions strings. A test module with an expensive or side-effecting
import therefore costs the parent nothing and cannot contaminate it.
"""

import argparse
import io
import json
import os
import pathlib
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import unittest

HERE = pathlib.Path(__file__).resolve()
ROOT = HERE.parents[1]

# -- the registries ----------------------------------------------------------
#
# Both lists are written by hand and their COMPLETENESS is checked
# mechanically, so a new module is a loud failure rather than a silent
# assumption. `tests/tools/test_parallel_runner.py` owns that check.

PARALLEL_MODULES = ("tests.authority.test_assignment",
                    "tests.authority.test_boundary",
                    "tests.authority.test_catalog",
                    "tests.authority.test_contract",
                    "tests.authority.test_identity",
                    "tests.authority.test_operations",
                    "tests.authority.test_session",
                    "tests.authority.test_store",
                    "tests.manager.test_attempts",
                    "tests.manager.test_boundary_inventory",
                    "tests.manager.test_canonical",
                    "tests.manager.test_contracts_inventory",
                    "tests.manager.test_dependencies",
                    "tests.manager.test_diagnostic_rendering",
                    "tests.manager.test_frozen",
                    "tests.manager.test_handshake",
                    "tests.manager.test_credentials",
                    "tests.manager.test_intake",
                    "tests.manager.test_sealing",
                    "tests.manager.test_interrogation",
                    "tests.manager.test_manifest_rules",
                    "tests.manager.test_oci",
                    "tests.manager.test_offers",
                    "tests.manager.test_output",
                    "tests.manager.test_pod",
                    "tests.manager.test_secrets",
                    "tests.manager.test_sessions",
                    "tests.manager.test_store",
                    "tests.manager.test_text_sweep",
                    "tests.manager.test_validate",
                    "tests.manager.test_worker_image",
                    "tests.manager.test_workspaces",
                    "tests.tools.test_parallel_runner",
                    "tests.tools.test_worker_image_build")

# ONE AT A TIME, IN THIS ORDER, AND NEVER BESIDE THE PARALLEL PHASE.
#
# `test_worker_container` builds THIS repository's worker image, owns the
# suite-global `baton-w6633-test` names and is the only source module with
# class fixtures. `test_oci_engine` drives a real Docker/Podman daemon and
# PULLS the pinned base into the shared image store when it is absent; its own
# comments record a full run where an unconditional pull changed what the image
# gate resolved between two builds. Running either concurrently with anything —
# including the other — puts two suites in disagreement about one daemon's
# artefacts, which is not a result about either of them. The image gate runs
# first because it produces the artefact; the engine gate then observes a store
# nobody else is still writing to.
# `test_lifecycle_composition` (W6636) is serial for BOTH reasons at once: it
# builds this repository's worker image AND drives a real daemon through the
# manager's whole ordered lifecycle, including a case that asks the engine
# whether exactly one container carries an assignment's labels. A concurrent
# suite creating or removing containers makes that count a fact about the run
# rather than about the manager. It runs LAST, because it observes both
# artefacts the two before it produce.
SERIAL_MODULES = ("tests.manager.test_worker_container",
                  "tests.manager.test_oci_engine",
                  "tests.manager.test_lifecycle_composition")

# The two whole-universe scans from the baseline. Split one test method per
# shard; every other class ships as one shard.
METHOD_SPLIT = ("tests.manager.test_boundary_inventory.EveryReceivingEntryHasOneOwner",
                "tests.manager.test_boundary_inventory.EveryProbeProvesItArrived")


class RunnerRefusal(Exception):
    """The runner refusing to run, rather than running something it guessed."""


class Interrupted(Exception):
    """A recorded signal, raised at a SAFE POINT rather than inside the handler.

    Review R4 (2026-08-25T16:49:30Z) is why this type exists. Acting on a
    signal from async context means acting at an arbitrary bytecode, and the
    scheduler has instants — between creating a shard process and recording it
    — where its own bookkeeping does not yet describe reality. A handler that
    cleaned up there cleaned up the wrong picture and left a whole shard
    running. So the handler now records and returns, and the loop decides when
    the picture is complete enough to act on.
    """

    def __init__(self, number):
        self.number = number
        super().__init__(f"signal {number}")


# -- pure decisions the parent makes, with no process and no filesystem -------


def resolve_jobs(override, detected, shards):
    """The bounded worker count: LOWER-ONLY against the DETECTED CPU count.

    The finding pins two caps and they compose in one order. The refusal is
    evaluated against `detected`, never against `shards`: binding the operator
    override to the shard count would refuse a legitimate lowering whenever the
    selection happened to be small, which would make `--jobs 8` mean different
    things on different days. The shard count then only avoids starting workers
    that would have nothing to run.
    """
    if detected < 1:
        raise RunnerRefusal(f"the host reports {detected} available CPUs")
    requested = detected
    if override is not None:
        text = str(override).strip()
        # Deliberately not int(text): int() accepts "  8\n", "+8" and "8_0",
        # and an operator who typed one of those did not mean this.
        if not text.isdigit():
            raise RunnerRefusal(f"jobs must be a whole number 1..{detected}; got {override!r}")
        requested = int(text)
        if requested < 1 or requested > detected:
            raise RunnerRefusal(f"jobs must be a whole number 1..{detected} "
                                f"(this host's available CPUs); got {requested}")
    return max(1, min(requested, shards)) if shards else 1


def partition(ids, method_split=METHOD_SPLIT):
    """Exact test ids -> deterministic shards, losing and duplicating nothing.

    A `unittest` id is `package.module.Class.method`, so the class key is the
    id with its last segment removed. The returned shards are sorted by label
    and each shard's ids are sorted, which is the whole of the presentation
    order: nothing downstream re-sorts by completion.
    """
    seen = sorted(ids)
    duplicates = sorted({one for one in seen if seen.count(one) > 1})
    if duplicates:
        raise RunnerRefusal(f"collection produced duplicate test ids: {duplicates[:5]}")
    split = set(method_split)
    classes = {}
    shards = []
    for one in seen:
        key = one.rsplit(".", 1)[0]
        if key in split:
            shards.append({"label": one, "ids": [one]})
        else:
            classes.setdefault(key, []).append(one)
    for key in classes:
        shards.append({"label": key, "ids": sorted(classes[key])})
    shards.sort(key=lambda shard: shard["label"])
    covered = sorted(one for shard in shards for one in shard["ids"])
    if covered != seen:
        raise RunnerRefusal("partitioning lost or invented test ids")
    return shards


# -- the suite under management ----------------------------------------------


class Suite:
    """One source tree, its two registries, and the way to run them.

    Parameterized rather than hard-coded so the runner's own regressions drive
    THIS code over disposable fake trees instead of a re-implementation of it.
    """

    def __init__(self, root, parallel, serial, method_split=METHOD_SPLIT,
                 tests_dir="tests", pythonpath="src"):
        self.root = pathlib.Path(root)
        self.parallel = tuple(parallel)
        self.serial = tuple(serial)
        self.method_split = tuple(method_split)
        self.tests_dir = tests_dir
        self.pythonpath = pythonpath

    # -- registry completeness, checked against the filesystem ---------------

    def discovered(self):
        """Every module `unittest discover` would find, WITHOUT importing one.

        The glob is `test*.py` because that is `unittest`'s own default
        pattern; matching `test_*.py` instead would let a `testthing.py` be
        discovered by the canonical gate and missed by this check, which is
        precisely the residue the registry exists to make impossible.
        """
        base = self.root / self.tests_dir
        found = []
        for path in sorted(base.rglob("test*.py")):
            relative = path.relative_to(self.root).with_suffix("")
            found.append(".".join(relative.parts))
        return tuple(found)

    def check_registry(self):
        registered = list(self.parallel) + list(self.serial)
        repeated = sorted({one for one in registered if registered.count(one) > 1})
        if repeated:
            raise RunnerRefusal(f"modules registered more than once: {repeated}")
        found = set(self.discovered())
        unregistered = sorted(found - set(registered))
        if unregistered:
            raise RunnerRefusal("these test modules belong to no registry; add each to the "
                                "parallel or serial list in tools/parallel_test.py after "
                                f"deciding what it owns: {unregistered}")
        missing = sorted(set(registered) - found)
        if missing:
            raise RunnerRefusal(f"these registered test modules are not in the tree: {missing}")

    # -- children ------------------------------------------------------------

    def environment(self):
        """The child's import path, stated rather than inherited.

        The canonical gate is `PYTHONPATH=src python3 -m unittest ... -t .`, and
        `-m` is what puts the top-level directory on `sys.path` there. These
        children are started as a SCRIPT, whose `sys.path[0]` is the script's
        own directory instead — so the tree root is named explicitly here and
        the child resolves exactly the same two places the gate does. The
        packaging proof is unaffected: it is the `build` stage that runs with
        `PYTHONPATH=` from outside the tree, and nothing here touches it.
        """
        environment = dict(os.environ)
        places = [str(self.root)]
        if self.pythonpath:
            places.append(str(self.root / self.pythonpath))
        environment["PYTHONPATH"] = os.pathsep.join(places)
        return environment

    def spawn(self, argv, err):
        """One child, in ITS OWN SESSION so its descendants can be reaped.

        `start_new_session=True` makes the child a process-group leader, which
        is what lets an interrupt kill the tests the child itself started
        rather than orphaning them. A test that spawns real processes — and
        several of these do — would otherwise survive the runner.

        Its stderr goes to ITS OWN FILE rather than a pipe. A pipe would be a
        64KiB deadlock waiting to happen: several of these modules emit
        ResourceWarnings, and a parent that only drains the pipe after `wait()`
        hangs forever the first time one of them is chatty. A file per shard is
        also why there is no shared log path to interleave.
        """
        handle = open(err, "wb")
        try:
            return subprocess.Popen([sys.executable, str(HERE)] + argv, cwd=str(self.root),
                                    env=self.environment(), stdout=subprocess.DEVNULL,
                                    stderr=handle, start_new_session=True)
        finally:
            handle.close()


class Run:
    """One invocation: its children, its disposable result root, its cleanup."""

    # How long a terminated shard's own descendants get to honour SIGTERM
    # before the group is killed outright. Bounded on purpose: this path only
    # runs when a run is being abandoned, and an abort that hangs waiting to be
    # polite is an abort that gets killed harder from outside.
    GRACE_SECONDS = 3.0

    def __init__(self, suite, jobs_override=None, progress=sys.stderr):
        self.suite = suite
        self.jobs_override = jobs_override
        self.progress = progress
        self.detected = os.process_cpu_count() or 1
        self.result_root = None
        self.live = {}
        # Popen -> the process group id recorded when this runner created it.
        # Kept beside `live` rather than derived from it, because shutdown must
        # still be able to reach a group whose leader has already exited.
        self.groups = {}
        # Set by the signal handler and by NOTHING else; read only at safe
        # points. The handler never touches `live`, `groups` or `result_root`.
        self.pending_signal = None

    # -- lifecycle -----------------------------------------------------------

    def note(self, line):
        if self.progress is not None:
            print(line, file=self.progress, flush=True)

    def open_result_root(self):
        self.result_root = pathlib.Path(tempfile.mkdtemp(prefix="v12-parallel-test-"))
        return self.result_root

    def shutdown(self):
        """Terminate every runner-owned process GROUP, then reap, then drop the root.

        Review R1 (2026-08-25T16:21:40Z) found the ordering bug this now avoids.
        The previous version dropped a shard from `self.live` the moment its
        LEADER exited, and escalated only over what remained — so a descendant
        that ignores SIGTERM outlived the runner whenever its leader took the
        signal and died first, and the entry naming its group was already gone.
        A shard leader's death says nothing about what the tests it started are
        still doing.

        Two rules follow, and the order of the steps below is the whole fix:

        1. THE GROUP IS THE UNIT, AND ITS IDENTITY IS RECORDED AT SPAWN. Every
           group id in `self.groups` was captured when this runner created that
           group, so escalation never depends on a leader still being alive and
           never has to re-derive an id from a process that has exited.
        2. NOTHING IS REAPED UNTIL AFTER THE KILL PASS. An unreaped leader is a
           zombie, and a zombie's pid is still reserved — so its group id cannot
           be recycled onto an unrelated process group in the window between
           TERM and KILL. Reaping first is what would make the KILL pass a
           danger to somebody else's processes, which is exactly the boundary
           the review asked to keep.

        The cost is that an abort always spends the grace period rather than
        exiting the moment the leaders die. That is deliberate: a zombie leader
        remains a member of its own group, so "is this group empty?" cannot be
        answered by signalling it, and the alternative is a /proc scan that buys
        a couple of seconds on a path that only runs when a run is being
        abandoned.
        """
        groups = list(self.groups.values())
        for pgid in groups:
            self.signal_group(pgid, signal.SIGTERM)
        if groups:
            deadline = time.monotonic() + self.GRACE_SECONDS
            while time.monotonic() < deadline:
                time.sleep(0.05)
            # Every group, including those whose leader already exited.
            for pgid in groups:
                self.signal_group(pgid, signal.SIGKILL)
        for child in list(self.live):
            try:
                child.wait(timeout=5)
            except subprocess.TimeoutExpired:
                pass
            self.live.pop(child, None)
        self.groups.clear()
        if self.result_root is not None:
            shutil.rmtree(self.result_root, ignore_errors=True)
            self.result_root = None

    def record_signal(self, number, frame=None):
        """The whole of the asynchronous handler.

        It records and returns. It reads no scheduler state and mutates none,
        because it can run between any two bytecodes — including the two that
        register a freshly spawned shard. The FIRST signal is kept so the
        reported exit code does not depend on how many times somebody pressed
        Ctrl-C; a second one is deliberately not a fast path around cleanup.
        """
        if self.pending_signal is None:
            self.pending_signal = number

    def checkpoint(self):
        """A SAFE POINT: act on a recorded signal now that bookkeeping is true.

        Called only where `live` and `groups` describe every process this
        runner has actually created — never between a spawn and its
        registration, and never between a cleanup side effect and the state
        change that follows it.
        """
        if self.pending_signal is not None:
            raise Interrupted(self.pending_signal)

    def has_exited(self, child):
        """Has this leader exited? Asked WITHOUT reaping it.

        `Popen.poll()` cannot answer this question safely, and review R2
        (2026-08-25T16:30:55Z) is why: poll() reaps, reaping releases the pid,
        and a released pid takes the process-group id with it. Any cleanup done
        after that is either impossible or — worse — aimed at whatever process
        inherits the number next.

        `waitid` with `WNOWAIT` reports the exit and leaves the leader as a
        zombie, which is exactly the state `retire()` needs: dead enough to have
        a final status, undead enough that the group id still provably belongs
        to this runner.
        """
        try:
            return os.waitid(os.P_PID, child.pid,
                             os.WEXITED | os.WNOHANG | os.WNOWAIT) is not None
        except ChildProcessError:
            # Somebody already reaped it; treat it as finished rather than
            # spinning on a child that will never report again.
            return True

    def retire(self, child):
        """Finish one shard: kill what it left running, THEN reap it.

        The order is the whole of review R2's required correction, and it is
        unconditional rather than conditioned on the shard's verdict. A shard
        can fail an assertion and let its worker exit 1 perfectly normally
        while a process it started keeps running; the leader's clean exit says
        nothing about that. Deciding whether to clean up based on the verdict
        would also mean computing the verdict first, so cleaning up ALWAYS is
        both simpler and strictly stronger than what the review asked for.

        SIGKILL with no grace period, deliberately: this shard is over. Its
        descendants are not being asked to wind down mid-run — they are already
        orphans of a finished shard, and the acceptance boundary says none may
        survive. The graceful TERM-then-grace path stays where it belongs, in
        `shutdown()`, where a run is being abandoned while shards are still
        legitimately working.

        The leader is still an unreaped zombie at the moment of the signal, so
        the group id cannot have been recycled onto anybody else's processes.
        Only after the group is cleared is the leader reaped and its ownership
        identity released.

        EVERY STATE MUTATION HERE FOLLOWS ITS SIDE EFFECT, which is review R3
        (2026-08-25T16:39:27Z). This method can be interrupted at any line: the
        SIGINT handler runs `shutdown()`, and `shutdown()` can only clean up
        what is still registered. The previous version popped the group BEFORE
        signalling it, so an interrupt landing in that window found nothing to
        signal and exited 130 with the descendant still running. The window was
        tiny and entirely real. The order below leaves no instant at which a
        descendant is both alive and untracked:

            groups[child] still set   -> shutdown() TERM/grace/KILLs the group
            signal issued, entry gone -> the group is already dead; a later
                                         handler has nothing left to do
            live[child] still set     -> shutdown() still reaps the leader
        """
        pgid = self.groups.get(child)
        if pgid is not None:
            # The side effect FIRST, while the group is still registered.
            self.signal_group(pgid, signal.SIGKILL)
            # Safe to forget only now: the fatal signal has been delivered, so
            # an interrupt from here on has nothing left to kill — and holding
            # a PGID past its leader's reaping is the reuse hazard R2 forbids.
            self.groups.pop(child, None)
        try:
            child.wait(timeout=5)
        except subprocess.TimeoutExpired:
            pass
        return child.returncode

    def group_of(self, child):
        """This child's process group, recorded while it is certainly alive.

        `start_new_session=True` makes the child its own group leader, so the
        group id IS the child's pid; `getpgid` is asked anyway and the pid is
        the fallback, because reading it back is what proves the child really
        got its own group rather than inheriting the runner's.
        """
        try:
            return os.getpgid(child.pid)
        except (ProcessLookupError, PermissionError):
            return child.pid

    def signal_group(self, pgid, which):
        """Signal ONE group this runner created. Never anything else."""
        try:
            os.killpg(pgid, which)
        except (ProcessLookupError, PermissionError):
            # The group is already empty. That is the goal, not a failure.
            pass

    # -- the bounded scheduler -----------------------------------------------

    def drive(self, work, jobs, label):
        """Run `work` items at most `jobs` at a time, and DRAIN THEM ALL.

        A failing item never abandons its siblings: the phase's verdict is
        decided after everything scheduled has finished, because a partial
        parallel result is not comparable with the serial baseline it has to
        stand against.
        """
        queue = list(work)
        total = len(queue)
        for index, item in enumerate(queue):
            item["err"] = self.result_root / f"{label.replace(' ', '-')}-{index:05d}.err"
        done = []
        started = 0
        while queue or self.live:
            while queue and len(self.live) < jobs:
                item = queue.pop(0)
                item["started"] = time.monotonic()
                child = self.suite.spawn(item["argv"], item["err"])
                # REGISTRATION IS NOT INTERRUPTIBLE WORK (R4). A signal landing
                # anywhere in here is only recorded, so these two lines always
                # complete and the checkpoint below sees the real picture.
                self.live[child] = item
                self.groups[child] = self.group_of(child)
                started += 1
                self.note(f"[{label}] start {started}/{total} {item['label']}")
            # Safe point: everything spawned above is registered. This is also
            # the check that covers an IDLE scheduler, since the sleep path
            # below comes straight back around to it.
            self.checkpoint()
            finished = [child for child in self.live if self.has_exited(child)]
            if not finished:
                time.sleep(0.01)
                continue
            for child in finished:
                # The child stays registered in `live` ACROSS retirement (R3):
                # an interrupt part-way through must still find a leader to
                # reap. It is released only once retirement has returned.
                item = self.live[child]
                item["returncode"] = self.retire(child)
                self.live.pop(child, None)
                item["stderr"] = item["err"].read_text(encoding="utf-8", errors="replace")
                item["elapsed"] = time.monotonic() - item["started"]
                done.append(item)
                # STDERR, and only stderr. A duration is the one thing about a
                # shard that is different every run, so putting it in stdout
                # would cost the byte-identical comparison that makes jobs=1
                # and jobs=32 checkable against each other. It belongs in the
                # progress stream, where finding the long pole is what it is
                # for.
                self.note(f"[{label}] done  {len(done)}/{total} {item['label']}"
                          f" rc={child.returncode} in {item['elapsed']:.2f}s")
            # Safe point: every retirement above ran to completion, so no group
            # is half-released and no leader is half-reaped.
            self.checkpoint()
        return done


# -- collection ---------------------------------------------------------------


def collect(run, jobs):
    """Exact test ids for every parallel module, gathered by child processes."""
    root = run.result_root
    work = []
    for module in run.suite.parallel:
        out = root / f"collect-{module}.json"
        work.append({"label": module, "module": module, "out": out,
                     "argv": ["collect-one", module, str(out)]})
    done = run.drive(work, jobs, "collect")
    ids = []
    for item in sorted(done, key=lambda one: one["label"]):
        # The child's own recorded reason first: it names the import that
        # failed, where a returncode and a stderr tail often name nothing.
        if item["out"].exists():
            answer = json.loads(item["out"].read_text(encoding="utf-8"))
            if answer.get("error"):
                raise RunnerRefusal(f"collecting {item['label']} failed: {answer['error']}")
            if item["returncode"] == 0:
                ids.extend(answer["ids"])
                continue
        raise RunnerRefusal(f"collecting {item['label']} failed "
                            f"(rc={item['returncode']}): {item['stderr'].strip()[:500]}")
    return ids


# -- phases -------------------------------------------------------------------


def shard_work(run, shards, kind):
    work = []
    for index, shard in enumerate(shards):
        plan = run.result_root / f"{kind}-{index:05d}.plan.json"
        report = run.result_root / f"{kind}-{index:05d}.report.json"
        plan.write_text(json.dumps({"ids": shard["ids"], "report": str(report)}), encoding="utf-8")
        work.append({"label": shard["label"], "ids": shard["ids"], "report": report,
                     "argv": ["run-shard", str(plan)]})
    return work


def harvest(item):
    """One shard's structured outcome, or a synthetic one if it never wrote it.

    A child that is killed, faults in the interpreter or dies before writing
    its report is a FAILURE of that shard and says so. Treating a missing
    report as an absence of failures is how a runner reports green for tests it
    never actually ran.
    """
    if item["report"].exists():
        answer = json.loads(item["report"].read_text(encoding="utf-8"))
        answer["label"] = item["label"]
        answer["returncode"] = item["returncode"]
        if item["returncode"] != 0 and answer.get("ok"):
            answer["ok"] = False
            answer["errors"] = list(answer.get("errors", [])) + [
                {"id": item["label"], "trace": f"shard reported success but exited {item['returncode']}"}]
        return answer
    trace = item["stderr"].strip() or f"the shard process exited {item['returncode']} without a report"
    return {"label": item["label"], "ids": item["ids"], "ran": 0, "ok": False,
            "failures": [], "skipped": [], "expected_failures": [], "unexpected_successes": [],
            "errors": [{"id": item["label"], "trace": trace}],
            "returncode": item["returncode"]}


def present(results, heading, out):
    """The deterministic half of the output: sorted, and free of durations."""
    print(f"--- {heading} ---", file=out)
    for answer in results:
        verdict = "pass" if answer["ok"] else "FAIL"
        count = answer["ran"]
        print(f"[{verdict}] {answer['label']} ({count} tests)", file=out)
    broken = [answer for answer in results if not answer["ok"]]
    if broken:
        print(f"--- {heading}: failures ---", file=out)
        for answer in broken:
            for kind in ("errors", "failures"):
                for one in answer.get(kind, []):
                    print(f"=== {kind[:-1].upper()}: {one['id']} ===", file=out)
                    print(one["trace"].rstrip(), file=out)
    ran = sum(answer["ran"] for answer in results)
    failures = sum(len(answer.get("failures", [])) for answer in results)
    errors = sum(len(answer.get("errors", [])) for answer in results)
    skipped = sum(len(answer.get("skipped", [])) for answer in results)
    ok = all(answer["ok"] for answer in results)
    print(f"[{heading}] {len(results)} shards, {ran} tests, {failures} failures, "
          f"{errors} errors, {skipped} skipped -> {'OK' if ok else 'FAILED'}", file=out)
    return {"shards": len(results), "ran": ran, "failures": failures, "errors": errors,
            "skipped": skipped, "ok": ok}


def main(argv=None, suite=None, out=sys.stdout, progress=sys.stderr):
    parser = argparse.ArgumentParser(prog="parallel_test",
                                     description="Run the safe v12 source tests across available CPUs.")
    parser.add_argument("--jobs", default=None,
                        help="lower the worker count; a whole number from 1 to the host's "
                             "available CPUs. Omitted means all of them.")
    parser.add_argument("--phase", choices=("all", "parallel", "serial"), default="all")
    parser.add_argument("--print-ids", action="store_true",
                        help="print every collected test id and exit without running them")
    parser.add_argument("--root", default=None, help=argparse.SUPPRESS)
    options = parser.parse_args(argv)

    if suite is None:
        suite = Suite(options.root or ROOT, PARALLEL_MODULES, SERIAL_MODULES)
    run = Run(suite, options.jobs, progress=progress)

    previous = {}
    for number in (signal.SIGINT, signal.SIGTERM):
        previous[number] = signal.getsignal(number)
        signal.signal(number, run.record_signal)

    def phases():
        suite.check_registry()
        run.open_result_root()
        # Collection is bounded by the same worker count, and by the module
        # count rather than the shard count that does not exist yet.
        jobs = resolve_jobs(options.jobs, run.detected, len(suite.parallel))
        ids = collect(run, jobs) if options.phase != "serial" else []
        shards = partition(ids, suite.method_split) if ids else []

        if options.print_ids:
            for one in sorted(ids):
                print(one, file=out)
            return 0

        summaries = {}
        if options.phase != "serial":
            jobs = resolve_jobs(options.jobs, run.detected, len(shards))
            print(f"[collect] {len(suite.parallel)} parallel modules -> {len(ids)} tests "
                  f"in {len(shards)} shards", file=out)
            print(f"[parallel] jobs={jobs} (available CPUs {run.detected})", file=out)
            done = run.drive(shard_work(run, shards, "parallel"), jobs, "parallel")
            results = sorted((harvest(item) for item in done), key=lambda one: one["label"])
            summaries["parallel source"] = present(results, "parallel source", out)
            if not summaries["parallel source"]["ok"]:
                # The canonical gate's fail-fast ORDERING, preserved: a broken
                # source phase does not get to spend a Docker daemon's time.
                print("[summary] parallel source FAILED; the serial registry did not run", file=out)
                return 1

        if options.phase != "parallel":
            serial = [{"label": module, "ids": [module]} for module in suite.serial]
            print(f"[serial] {len(serial)} source modules, one at a time", file=out)
            done = run.drive(shard_work(run, serial, "serial"), 1, "serial")
            results = sorted((harvest(item) for item in done), key=lambda one: one["label"])
            summaries["serial source"] = present(results, "serial source", out)

        line = " | ".join(f"{name}: {one['ran']} tests, "
                          f"{one['failures'] + one['errors']} failed, {one['skipped']} skipped"
                          for name, one in summaries.items())
        ok = all(one["ok"] for one in summaries.values())
        print(f"[summary] {line} -> {'OK' if ok else 'FAILED'}", file=out)
        return 0 if ok else 1

    try:
        code = phases()
    except RunnerRefusal as refusal:
        print(f"[runner] refused: {refusal}", file=out)
        code = 2
    except Interrupted as stopped:
        run.note(f"[runner] signal {stopped.number}; terminating "
                 f"{len(run.live)} live shards")
        print(f"[runner] interrupted by signal {stopped.number}", file=out)
        code = 128 + stopped.number
    finally:
        # RECORDING STAYS ARMED THROUGH CLEANUP, and the handlers are restored
        # only afterwards. Restoring first would give a signal arriving during
        # `shutdown()` the caller's default disposition — which for SIGINT
        # raises KeyboardInterrupt straight through the middle of the bounded
        # cleanup, abandoning the kill pass and the result root. The review's
        # rule is that a second signal need not bypass bounded cleanup; this is
        # what makes that true rather than merely intended. The signal is not
        # lost: it is recorded, and the check below reports it.
        try:
            run.shutdown()
        finally:
            for number, handler in previous.items():
                signal.signal(number, handler)

    # A signal recorded but never reached by a checkpoint — one that arrived
    # while the last phase was finishing, or during cleanup itself — must not
    # be silently converted into a successful exit (R4). A run that already
    # FAILED keeps its own code: the failures are the more informative answer,
    # and 1 is not a success being papered over.
    if code == 0 and run.pending_signal is not None:
        print(f"[runner] interrupted by signal {run.pending_signal} during cleanup",
              file=out)
        code = 128 + run.pending_signal
    return code


# -- the child modes ----------------------------------------------------------
#
# Both run in a fresh interpreter with the source tree's own PYTHONPATH. This
# is the ONLY place a test module is ever imported.


def collect_one(module, out):
    answer = {"module": module, "ids": [], "error": None}
    try:
        suite = unittest.TestLoader().loadTestsFromName(module)
        for test in iterate(suite):
            name = type(test).__name__
            if name in ("_FailedTest", "ModuleImportFailure"):
                # Fail closed. A module that cannot be imported must not be
                # collected as "one test that will fail somewhere later".
                raise RunnerRefusal(f"{module} could not be loaded: {test.id()}")
            answer["ids"].append(test.id())
    except Exception as trouble:
        answer["error"] = f"{type(trouble).__name__}: {trouble}"
    pathlib.Path(out).write_text(json.dumps(answer), encoding="utf-8")
    return 0 if answer["error"] is None else 1


def iterate(suite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from iterate(item)
        else:
            yield item


def run_shard(plan_path):
    plan = json.loads(pathlib.Path(plan_path).read_text(encoding="utf-8"))
    # The runner's own text output is discarded on purpose: the parent presents
    # this shard from the STRUCTURED report below, in sorted order, so a stream
    # written at completion time could only reintroduce the nondeterminism the
    # whole design removes.
    result = unittest.TextTestRunner(stream=io.StringIO(), verbosity=0).run(
        unittest.TestLoader().loadTestsFromNames(plan["ids"]))
    answer = {"ids": plan["ids"], "ran": result.testsRun, "ok": result.wasSuccessful(),
              "failures": [{"id": test.id(), "trace": trace} for test, trace in result.failures],
              "errors": [{"id": test.id(), "trace": trace} for test, trace in result.errors],
              "skipped": [{"id": test.id(), "reason": why} for test, why in result.skipped],
              "expected_failures": [test.id() for test, _ in result.expectedFailures],
              "unexpected_successes": [test.id() for test in result.unexpectedSuccesses]}
    pathlib.Path(plan["report"]).write_text(json.dumps(answer), encoding="utf-8")
    return 0 if answer["ok"] else 1


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "collect-one":
        raise SystemExit(collect_one(sys.argv[2], sys.argv[3]))
    if len(sys.argv) > 1 and sys.argv[1] == "run-shard":
        raise SystemExit(run_shard(sys.argv[2]))
    raise SystemExit(main(sys.argv[1:]))
