"""Do the two facts that decide the design hold? Measured, not reasoned.

1. Does a RUNNING container's bind survive the host source being renamed and
   replaced?  If it does, the running worker cannot be fooled and the window is
   only between composition and start.
2. Does the inode change on replacement?  If it does, pinning (st_dev, st_ino)
   at composition and re-proving it before start DETECTS the substitution
   without needing any privilege the manager does not have.
"""
import json, os, subprocess, tempfile, time, uuid

root = tempfile.mkdtemp(prefix="w33935-identity-")
original = os.path.join(root, "inputs")
os.makedirs(original)
with open(os.path.join(original, "input.json"), "w") as handle:
    handle.write('{"who": "the original"}')
before = os.stat(original)

name = "w33935-identity-" + uuid.uuid4().hex[:8]
run = subprocess.run(
    ["docker", "run", "--detach", "--name", name, "--network", "none",
     "--read-only", "--user", "65532:65532",
     "--mount", f"type=bind,source={original},target=/input,readonly=true",
     "python:3.13-slim", "sleep", "60"],
    capture_output=True, timeout=300)
assert run.returncode == 0, run.stderr.decode()[:400]
try:
    def inside():
        got = subprocess.run(
            ["docker", "exec", name, "cat", "/input/input.json"],
            capture_output=True, timeout=120)
        return got.stdout.decode().strip() or got.stderr.decode().strip()

    answers = {"before-replacement": inside()}
    # THE ATTACK, exactly as the reviewer performed it on the host.
    os.rename(original, original + ".displaced")
    os.makedirs(original)
    with open(os.path.join(original, "input.json"), "w") as handle:
        handle.write('{"who": "the REPLACEMENT"}')
    after = os.stat(original)
    answers["after-replacement"] = inside()
    answers["host-now-reads"] = open(
        os.path.join(original, "input.json")).read()
    answers["inode-before"] = [before.st_dev, before.st_ino]
    answers["inode-after"] = [after.st_dev, after.st_ino]
    answers["inode-changed"] = (before.st_dev, before.st_ino) != (
        after.st_dev, after.st_ino)
    print(json.dumps(answers, indent=1))
finally:
    subprocess.run(["docker", "rm", "--force", name], capture_output=True,
                   timeout=120)
