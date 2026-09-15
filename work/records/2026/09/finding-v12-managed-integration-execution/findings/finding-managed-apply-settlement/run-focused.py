"""Supervised focused runner for W170385 (group2).

Inherited from the parent's /tmp/w166281_run.py and the reviewer's own
supervisor: per-run timeout, its own process group, and TERM->KILL escalation
driven by GROUP liveness rather than by the direct child alone.
"""
import json, os, signal, subprocess, sys, time

RECORD_ROOT = ("/home/sl/src/baton/work/records/2026/09/"
        "finding-v12-managed-integration-execution/findings/"
        "finding-managed-apply-settlement")
LEDGER = os.path.join(RECORD_ROOT, "ledger-170385.json")
CWD = "/home/sl/src/baton/v12/python"
TIMEOUT = float(os.environ.get("W170385_TIMEOUT", "180"))
TERM_GRACE, KILL_GRACE = 5.0, 5.0


def group_alive(pgid):
    try:
        os.killpg(pgid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def main():
    step, label, argv = sys.argv[1], sys.argv[2], sys.argv[3:]
    log = os.path.join(RECORD_ROOT, f"run-170385-step-{step}.log")
    if os.path.exists(log):
        sys.exit(f"refusing to overwrite {log}")
    env = dict(os.environ, PYTHONPATH="src:tools:.")
    started = time.monotonic()
    out, err = b"", b""
    signalled, group_proved_gone, timed_out = [], False, False
    proc = subprocess.Popen(argv, cwd=CWD, env=env, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, start_new_session=True)
    pgid = os.getpgid(proc.pid)
    try:
        out, _ = proc.communicate(timeout=TIMEOUT)
    except subprocess.TimeoutExpired:
        timed_out = True
        os.killpg(pgid, signal.SIGTERM)
        signalled.append("TERM")
        deadline = time.monotonic() + TERM_GRACE
        while time.monotonic() < deadline and group_alive(pgid):
            time.sleep(0.1)
        if group_alive(pgid):
            os.killpg(pgid, signal.SIGKILL)
            signalled.append("KILL")
            deadline = time.monotonic() + KILL_GRACE
            while time.monotonic() < deadline and group_alive(pgid):
                time.sleep(0.1)
        group_proved_gone = not group_alive(pgid)
        try:
            out, _ = proc.communicate(timeout=KILL_GRACE)
        except subprocess.TimeoutExpired:
            pass
    else:
        group_proved_gone = not group_alive(pgid)
    elapsed = time.monotonic() - started
    open(log, "wb").write(out or b"")
    row = {"step": step, "label": label, "argv": argv, "cwd": CWD,
           "budget": TIMEOUT, "elapsed_seconds": elapsed,
           "exit": proc.returncode, "ok": proc.returncode == 0,
           "timed_out": timed_out, "signalled": signalled,
           "group_proved_gone": group_proved_gone, "log": log}
    rows = json.load(open(LEDGER)) if os.path.exists(LEDGER) else []
    rows.append(row)
    json.dump(rows, open(LEDGER, "w"), indent=1)
    sys.stdout.write((out or b"").decode("utf-8", "replace"))
    sys.stderr.write(f"\n[step {step} {label}] exit={proc.returncode} "
                     f"{elapsed:.6f}s signalled={signalled} "
                     f"group_gone={group_proved_gone}\n")
    sys.exit(proc.returncode)


main()
