"""Measured runner for W161230 slice2.

OWNER M166331 REMOVED THE CUMULATIVE STOPWATCH AS A GATE, and review
claim169546 measured that this file had not caught up: the header said so while
`CAP = 1200.0` stayed an EXECUTABLE refusal, and at 1175.66s of recorded work it
began refusing ordinary focused runs. A retired rule that still runs is worse
than either keeping it or dropping it, because the record and the behaviour say
different things.

SO THE CUMULATIVE GATE IS GONE and what remains is what the owner kept: a
SENSIBLE PER-RUN TIMEOUT, cleanup, and measured append-only accounting. Costs
are still recorded in full -- they were never the problem -- and no row is
rewritten, no total is reset and no spending is replenished. The ledger stays
exactly the history it was.
"""
import json
import os
import signal
import subprocess
import sys
import time

ROOT = "/home/sl/src/baton"
DOSSIER = os.path.join(
    ROOT, "work/records/2026/09/finding-v12-managed-integration-execution")
LEDGER = os.path.join(DOSSIER, "ledger-166281-prospective.json")

# THE ONE BOUND THAT REMAINS, and it is a product requirement rather than a
# budget: a focused deterministic run that has not finished in this long has
# stopped being focused. It is per-run and says nothing about any total.
RUN_TIMEOUT = 300.0


def main(argv):
    step = int(argv[0])
    label = argv[1]
    rest = argv[2:]
    log = os.path.join(DOSSIER, f"run-166281-step-{step:02d}.log")
    if os.path.exists(log):
        sys.stderr.write(f"refusing to overwrite {log}\n")
        return 2
    cwd = os.path.join(ROOT, "v12/python")
    argvv = ["env", "PYTHONPATH=src:tools:."] + rest
    bound = float(os.environ.get("W161230_TIMEOUT", RUN_TIMEOUT))
    operands = {"timeout_seconds": bound,
                "cumulative_gate": "removed by owner M166331; this runner's "
                                   "stale CAP was retired at claim169578"}
    started = time.perf_counter()
    timed_out = False
    # ITS OWN PROCESS GROUP, so the bound reaches the DESCENDANTS too.
    #
    # Review claim169609 measured my "cleanup" claim as too broad, and it was:
    # `subprocess.run(timeout=)` kills the DIRECT CHILD only. A test module
    # that spawned a worker process, a container client or a harness would
    # leave those running past the bound, and the next run would inherit
    # them -- which is exactly the state a worker-process verification is
    # about to start creating. So the child leads a new session and the bound
    # signals the GROUP: TERM first, because an ordinary shutdown is what a
    # bounded run should ask for, then KILL for whatever did not take it.
    held = subprocess.Popen(argvv, cwd=cwd, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, start_new_session=True)
    try:
        out, err = held.communicate(timeout=bound)
        elapsed = time.perf_counter() - started
        payload = out + err
        code = held.returncode
    except subprocess.TimeoutExpired:
        timed_out = True
        code = None
        # EVIDENCE FIRST. Review claim169661: `out`/`err` were bound only
        # inside the signal loop, so a `ProcessLookupError` on the first signal
        # broke out before they existed and the whole log and ledger row were
        # lost to a NameError -- the run's evidence destroyed by its own
        # cleanup. They are initialised before anything can fail.
        out, err = b"", b""
        signalled = []

        def group_gone():
            """Whether the group still exists, asked WITHOUT sending anything.

            Signal 0 is the standing "does this exist" question. `None` means
            this process may not ask -- which is not the same answer as gone,
            and is never recorded as one.
            """
            try:
                os.killpg(held.pid, 0)
            except ProcessLookupError:
                return True
            except PermissionError:
                return None
            return False

        # ESCALATION IS DRIVEN BY THE GROUP, NOT BY THE PIPES.
        #
        # Review claim169780's exact defect: `communicate` returning broke this
        # loop, so a TERM-RESISTANT descendant that outlives its leader -- the
        # leader dies, the pipes close, `communicate` returns -- was polled for
        # thirty seconds and NEVER KILLED. The direct child's exit is not the
        # group's exit, which is the whole reason this signals a group at all.
        # So each signal is followed by a bounded wait on the GROUP's own
        # liveness, and only that decides whether to escalate.
        gone = group_gone()
        for signal_name, grace in ((signal.SIGTERM, 10.0),
                                   (signal.SIGKILL, 20.0)):
            if gone is not False:
                break
            try:
                os.killpg(held.pid, signal_name)
                signalled.append(signal_name.name)
            except (ProcessLookupError, PermissionError) as failed:
                signalled.append(f"{signal_name.name}:{type(failed).__name__}")
                gone = group_gone()
                break
            deadline = time.perf_counter() + grace
            while time.perf_counter() < deadline:
                # THE PIPES ARE DRAINED WITHOUT ENDING THE ESCALATION. A short
                # `communicate` collects whatever the leader wrote; whether it
                # returns says nothing about the group, so its answer is kept
                # and its completion is not a decision.
                try:
                    out, err = held.communicate(timeout=0.2)
                except subprocess.TimeoutExpired:
                    pass
                except ValueError:
                    pass
                gone = group_gone()
                if gone is not False:
                    break
                time.sleep(0.1)
        # AND CLEANUP IS MEASURED SEPARATELY rather than omitted. `elapsed` used
        # to be taken before any of this, so the seconds spent terminating a
        # group were charged to nobody.
        elapsed = time.perf_counter() - started
        payload = (b"TIMED OUT at the per-run bound; signalled "
                   + (", ".join(signalled) or "nothing").encode()
                   + b"; group proved gone: " + repr(gone).encode() + b"\n"
                   + (out or b"") + (err or b""))
    with open(log, "wb") as writing:
        writing.write(b"$ " + " ".join(argvv).encode() + b"\n")
        writing.write(payload)
    held = json.load(open(LEDGER))
    held["runs"].append({"step": step, "label": label, "cwd": cwd,
                         "argv": argvv, "exit": code,
                         "elapsed_seconds": elapsed,
                         "log": os.path.relpath(log, ROOT),
                         "ok": code == 0, "budget": operands,
                         "timed_out": timed_out,
                         "signalled": locals().get("signalled"),
                         "group_proved_gone": locals().get("gone")})
    spent = sum(one["elapsed_seconds"] for one in held["runs"])
    # RECORDED, NOT GATED. The two cap members are left exactly as the history
    # wrote them rather than deleted, so the record of what the gate once was
    # survives its retirement.
    held["author_spent_seconds"] = spent
    json.dump(held, open(LEDGER, "w"), indent=1, sort_keys=True)
    sys.stderr.write(f"step {step} exit={code} {elapsed:.6f}s "
                     f"spent={spent:.6f}\n")
    sys.stderr.write(payload.decode(errors="replace")[-6000:])
    return 0 if code == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
