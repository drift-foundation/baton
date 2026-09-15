"""Measured runner for W103525 claim155666: times a subprocess, logs it, and
appends the charge to the dossier ledger. Every run is retained."""
import json, os, subprocess, sys, time

ROOT = "/home/sl/src/baton"
DOSSIER = os.path.join(ROOT, "work/records/2026/09/finding-v12-deterministic-scheduler-stress")
LEDGER = os.path.join(DOSSIER, "ledger-153769.json")


def main(argv):
    step = int(argv[0]); label = argv[1]; rest = argv[2:]
    log = os.path.join(DOSSIER, f"run-153769-step-{step:02d}.log")
    if os.path.exists(log):
        sys.stderr.write(f"refusing to overwrite {log}\n"); return 2
    cwd = os.path.join(ROOT, "v12/python")
    argvv = ["env", "PYTHONPATH=src:tools:."] + rest
    # OWNER RULING M159696: THE PER-COMMAND GUARD, part of the approval rather
    # than an optional habit. The cap was exceeded by starting a run whose
    # recent measured cost did not fit the remainder, so before EVERY
    # subprocess this reads the cumulative ledger, computes what is actually
    # left, refuses to start when the expected cost plus margin cannot fit, and
    # bounds the child with a timeout below the remainder.
    held = json.load(open(LEDGER))
    cap = 960.0
    spent = sum(one["elapsed_seconds"] for one in held["runs"])
    remaining = cap - spent
    margin = 1.0
    expected = float(os.environ.get("W103525_EXPECT", "17"))
    if remaining <= margin or expected + margin > remaining:
        sys.stderr.write(
            f"REFUSING to start: {remaining:.6f}s remain of {cap}s, this "
            f"command is expected to cost about {expected:.1f}s and the margin "
            f"is {margin}s. Pick a narrower selector or stop.\n")
        return 3
    bound = max(1.0, remaining - margin)
    started = time.perf_counter()
    try:
        done = subprocess.run(argvv, cwd=cwd, capture_output=True,
                              timeout=bound)
    except subprocess.TimeoutExpired as cut:
        elapsed = time.perf_counter() - started
        with open(log, "wb") as w:
            w.write(b"$ " + " ".join(argvv).encode() + b"\n")
            w.write(b"TIMED OUT at the remaining-budget bound\n")
            w.write(cut.stdout or b"")
            w.write(cut.stderr or b"")
        held["runs"].append({"step": step, "label": label, "cwd": cwd,
                             "argv": argvv, "exit": None,
                             "elapsed_seconds": elapsed,
                             "log": os.path.relpath(log, ROOT), "ok": False,
                             "timed_out_at": bound})
        held["spent_seconds"] = sum(one["elapsed_seconds"]
                                    for one in held["runs"])
        json.dump(held, open(LEDGER, "w"), indent=1, sort_keys=True)
        sys.stderr.write(f"step {step} TIMED OUT after {elapsed:.6f}s; "
                         f"cumulative={held['spent_seconds']:.6f}s\n")
        return 4
    elapsed = time.perf_counter() - started
    with open(log, "wb") as w:
        w.write(b"$ " + " ".join(argvv).encode() + b"\n")
        w.write(done.stdout); w.write(done.stderr)
    held = json.load(open(LEDGER))
    held["runs"].append({"step": step, "label": label, "cwd": cwd,
                         "argv": argvv, "exit": done.returncode,
                         "elapsed_seconds": elapsed,
                         "log": os.path.relpath(log, ROOT),
                         "ok": done.returncode == 0})
    held["author_cap_seconds"] = 960.0
    held["cap_authority"] = (
        "owner153764: 120s author / 30s reviewer / 100 ticks per trace; "
        "owner155646: cumulative 165s author / 40s reviewer, prior spending preserved; "
        "owner155911 (Slawomir 2026-09-12T23:50:14Z, FINDING 'Owner verification budget'): "
        "cumulative 300s author / 300s reviewer, superseding 165s/40s and the proposed 177s/40s, "
        "all prior spending preserved; "
        "owner157085 (Slawomir 2026-09-13T03:02:44Z): cumulative 600s author, "
        "reviewer unchanged at 300s, prior spending preserved, R6d and the "
        "accepted four-Job composition to be completed under it; "
        "owner159439 (Slawomir 2026-09-13T09:34:52Z) approving "
        "CONTINUATION-PROPOSAL-2026-09-13.md: cumulative 780s author, "
        "reviewer 300s unchanged, prior spending preserved; "
        "owner159714 (Slawomir 2026-09-13T10:12:58Z) approving "
        "BUDGET-DISPOSITION-2026-09-13T10-09-12Z.md after a recorded "
        "0.8047997559610849s OVERRUN of the 780s cap: cumulative 960s author, "
        "reviewer 300s unchanged, per-command guards required, no reset or "
        "waiver")
    spent = sum(one["elapsed_seconds"] for one in held["runs"])
    held["author_spent_seconds"] = spent
    held["author_remaining_seconds"] = held["author_cap_seconds"] - spent
    json.dump(held, open(LEDGER, "w"), indent=1, sort_keys=True)
    sys.stderr.write(f"step {step} exit={done.returncode} "
                     f"{elapsed:.6f}s spent={spent:.6f} "
                     f"remaining={held['author_remaining_seconds']:.6f}\n")
    tail = (done.stdout + done.stderr).decode(errors="replace")
    sys.stderr.write(tail[-6000:])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
