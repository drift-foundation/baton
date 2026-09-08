"""Read-only environment evidence for W106673; never creates a runtime."""

import json
import os
from pathlib import Path
import platform
import shutil
import subprocess


def docker(*arguments):
    result = subprocess.run(["docker", *arguments], capture_output=True, text=True, timeout=30)
    return {"exit": result.returncode, "stdout": result.stdout.strip(), "stderr": result.stderr.strip()}


status = {}
for line in Path("/proc/self/status").read_text().splitlines():
    name, _, value = line.partition(":")
    if name in ("Uid", "Gid", "CapInh", "CapPrm", "CapEff", "CapBnd", "CapAmb", "NoNewPrivs", "Seccomp"):
        status[name] = value.strip()

print(json.dumps({
    "proof": "preflight-only",
    "kernel": platform.release(),
    "process": status,
    "namespaces": {kind: os.readlink(f"/proc/self/ns/{kind}") for kind in ("mnt", "user", "pid")},
    "tools": {name: shutil.which(name) for name in ("nsenter", "mount", "umount")},
    "dedicated_workspace_group": os.environ.get("BATON_V12_WORKSPACE_GROUP"),
    "docker_version": docker("version", "--format", "{{.Server.Version}}"),
    "docker_security": docker("info", "--format", "{{json .SecurityOptions}}"),
    "experiment_containers": docker("ps", "--all", "--filter", "label=baton.experiment=W106673", "--format", "{{.ID}}\t{{.Image}}\t{{.Names}}"),
}, indent=2, sort_keys=True))
