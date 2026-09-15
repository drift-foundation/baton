"""Prove the runner's group cleanup on a real descendant that outlives its parent."""
import json, os, subprocess, sys, tempfile

home = tempfile.mkdtemp(prefix="w161230-timeout-proof-")
child = os.path.join(home, "spawner.py")
open(child, "w").write(
    "import subprocess, sys, time\n"
    "held = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(600)'])\n"
    "print('DESCENDANT', held.pid, flush=True)\n"
    "time.sleep(600)\n")
ledger = "/home/sl/src/baton/work/records/2026/09/finding-v12-managed-integration-execution/ledger-166281-prospective.json"
before = json.load(open(ledger))["runs"]
done = subprocess.run(
    ["python3", "/tmp/w166281_run.py", "999", "timeout-proof",
     sys.executable, child],
    env=dict(os.environ, W161230_TIMEOUT="3"), capture_output=True, text=True)
after = json.load(open(ledger))["runs"]
row = after[-1]
print("exit:", done.returncode)
print("timed_out:", row["timed_out"], "signalled:", row.get("signalled"),
      "group_proved_gone:", row.get("group_proved_gone"))
print("elapsed includes cleanup:", row["elapsed_seconds"] > 3.0)
print("row appended:", len(after) == len(before) + 1)
