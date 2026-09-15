"""Prove bounded escalation against a TERM-RESISTANT descendant that outlives
its leader and closes the pipes -- the exact shape review claim169780 named."""
import json, os, subprocess, sys, tempfile, time

home = tempfile.mkdtemp(prefix="w161230-term-resistant-")
grandchild = os.path.join(home, "stubborn.py")
open(grandchild, "w").write(
    "import os, signal, sys, time\n"
    "signal.signal(signal.SIGTERM, signal.SIG_IGN)\n"   # ignores TERM
    "os.close(1); os.close(2)\n"                          # closes the pipes
    "time.sleep(600)\n")
leader = os.path.join(home, "leader.py")
open(leader, "w").write(
    "import subprocess, sys, time\n"
    "subprocess.Popen([sys.executable, %r])\n" % grandchild +
    "time.sleep(600)\n")
ledger = "/home/sl/src/baton/work/records/2026/09/finding-v12-managed-integration-execution/ledger-166281-prospective.json"
before = len(json.load(open(ledger))["runs"])
started = time.perf_counter()
done = subprocess.run(
    ["python3", "/tmp/w166281_run.py", "998", "term-resistant-proof",
     sys.executable, leader],
    env=dict(os.environ, W161230_TIMEOUT="3"), capture_output=True, text=True)
row = json.load(open(ledger))["runs"][-1]
print("exit:", done.returncode)
print("signalled:", row.get("signalled"))
print("group_proved_gone:", row.get("group_proved_gone"))
print("elapsed:", round(row["elapsed_seconds"], 2))
print("row appended:", len(json.load(open(ledger))["runs"]) == before + 1)
print("wall:", round(time.perf_counter() - started, 2))
