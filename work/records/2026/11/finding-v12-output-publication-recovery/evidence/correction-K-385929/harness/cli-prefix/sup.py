#!/usr/bin/python3
"""PROTOTYPE of the adapter-owned command supervisor behind the CLI's shell prefix."""
import ctypes, json, os, signal, subprocess, sys, time
SECONDS = int(os.environ.get("BATON_COMMAND_SECONDS", "900"))
LEDGER = os.environ.get("BATON_COMMAND_LEDGER")
GRACE = 5.0
def descendants(me):
    parents = {}
    for name in os.listdir("/proc"):
        if not name.isdigit(): continue
        try:
            with open(f"/proc/{name}/stat", "rb") as f: raw = f.read()
        except OSError: continue
        rest = raw[raw.rindex(b")") + 2:].split()
        if rest[0] == b"Z": continue
        parents[int(name)] = int(rest[1])
    found = []
    for pid in parents:
        seen, at = set(), pid
        while at in parents and at not in seen:
            seen.add(at); at = parents[at]
            if at == me: found.append(pid); break
    return found
def end_all(me):
    ended, deadline = set(), time.monotonic() + GRACE
    while True:
        live = descendants(me)
        for pid in live:
            ended.add(pid)
            try: os.kill(pid, signal.SIGKILL)
            except ProcessLookupError: pass
        while True:
            try:
                if os.waitpid(-1, os.WNOHANG)[0] == 0: break
            except ChildProcessError: break
        if not live: return sorted(ended), True
        if time.monotonic() >= deadline: return sorted(ended), False
        time.sleep(0.01)
def main():
    ctypes.CDLL(None, use_errno=True).prctl(36, 1, 0, 0, 0)
    me = os.getpid(); began = time.monotonic()
    record = {"pid": me, "command_digest": None, "seconds_bound": SECONDS, "outcome": None, "status": None}
    child = subprocess.Popen(["/bin/bash", "-c", sys.argv[1]])
    stop = []
    for s in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP): signal.signal(s, lambda n, f: stop.append(n))
    status = None
    while True:
        try:
            pid, raw = os.waitpid(child.pid, os.WNOHANG)
        except ChildProcessError: pid, raw = child.pid, 0
        if pid: status = os.waitstatus_to_exitcode(raw); break
        if stop: record["outcome"] = "signalled"; break
        if time.monotonic() - began >= SECONDS: record["outcome"] = "timed-out"; break
        time.sleep(0.02)
    child.returncode = status if status is not None else -9
    ended, gone = end_all(me)
    if record["outcome"] is None: record["outcome"] = "exited"
    record.update(status=status, seconds=round(time.monotonic() - began, 3), descendants_ended=len([p for p in ended if p != child.pid or status is None]), descendants_gone=gone)
    if LEDGER:
        with open(os.path.join(LEDGER, f"{me}-{time.monotonic_ns()}.json"), "x") as out: json.dump(record, out)
    if record["outcome"] == "timed-out":
        sys.stderr.write(f"baton: this command was ended at its {SECONDS}s bound\n"); sys.exit(124)
    if record["outcome"] == "signalled": sys.exit(128 + stop[0])
    sys.exit(status if status >= 0 else 128 - status)
main()
