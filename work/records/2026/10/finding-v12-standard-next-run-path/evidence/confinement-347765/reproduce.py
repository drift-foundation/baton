"""Reproduce the confined-Git startup denial. READ-ONLY, disposable.

What this is: a bounded author DIAGNOSTIC, not the independent acceptance
evidence and not a product-test run. It imports the product module
`tools/next_run_confinement.py` unchanged, applies the REAL Landlock
restriction in a throwaway child process under a temporary root, and then
attempts (a) the exact `/dev/null` O_RDWR open the hypothesis names and (b) a
REAL `git` clone of a real local source line. It writes only beneath its own
temporary directory, mutates nothing installed, starts no runtime, submits no
Job and reads no credential.

Why it exists: review-2026-10-21T16-16-14Z.md requires the /dev/null hypothesis
to be DYNAMICALLY REPRODUCED before any correction, and says in terms that a
mocked Git or a provider fixture is not proof of the kernel boundary.

Usage: reproduce.py <confinement-module-path> <work-dir>
"""
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

CHILD = r'''
import importlib.util, json, os, subprocess, sys

module_path, root, line, scratch = sys.argv[1:5]
spec = importlib.util.spec_from_file_location("confinement", module_path)
confinement = importlib.util.module_from_spec(spec)
spec.loader.exec_module(confinement)

out = {"module": module_path, "root": root}
try:
    confinement.restrict_writes(root)
    out["restricted"] = True
except BaseException as failed:
    out["restricted"] = False
    out["restriction_error"] = "%s: %s" % (type(failed).__name__, failed)
    json.dump(out, sys.stdout); raise SystemExit(0)

# 1. the exact operation the hypothesis names
try:
    fd = os.open("/dev/null", os.O_RDWR)
    os.close(fd)
    out["dev_null_O_RDWR"] = "allowed"
except OSError as failed:
    out["dev_null_O_RDWR"] = "denied: errno %d %s" % (failed.errno, failed.strerror)

# 2. a write INSIDE the allowed root must still work
try:
    with open(os.path.join(root, "inside.txt"), "w") as handle:
        handle.write("x")
    out["write_inside_root"] = "allowed"
except OSError as failed:
    out["write_inside_root"] = "denied: errno %d" % failed.errno

# 3. a write OUTSIDE the allowed root must still be denied
try:
    with open(os.path.join(scratch, "outside.txt"), "w") as handle:
        handle.write("x")
    out["write_outside_root"] = "ALLOWED -- CONFINEMENT BROKEN"
except OSError as failed:
    out["write_outside_root"] = "denied: errno %d" % failed.errno

# 4. REAL git, the actual materialization shape: clone a real local line
done = subprocess.run(
    ["git", "clone", "--quiet", "--no-hardlinks", line,
     os.path.join(root, "checkout")],
    capture_output=True, text=True)
out["git_clone"] = {"status": done.returncode,
                    "stderr": done.stderr.strip()[-400:],
                    "stdout_bytes": len(done.stdout)}
json.dump(out, sys.stdout)
'''


def main():
    module, work = sys.argv[1], Path(sys.argv[2])
    work.mkdir(parents=True, exist_ok=True)
    scratch = Path(tempfile.mkdtemp(prefix='outside-', dir=str(work)))
    root = Path(tempfile.mkdtemp(prefix='runroot-', dir=str(work)))
    line = Path(tempfile.mkdtemp(prefix='line-', dir=str(work)))

    # A REAL local source line: a genuine repository with one commit, created
    # here and thrown away. No host repository is read, written or referenced.
    env = dict(os.environ, GIT_CONFIG_GLOBAL='/dev/null',
               GIT_CONFIG_SYSTEM='/dev/null',
               GIT_AUTHOR_NAME='fixture', GIT_AUTHOR_EMAIL='fixture@invalid',
               GIT_COMMITTER_NAME='fixture',
               GIT_COMMITTER_EMAIL='fixture@invalid')
    for argv in (['git', 'init', '--quiet', '-b', 'main', str(line)],
                 ['git', '-C', str(line), 'commit', '--quiet',
                  '--allow-empty', '-m', 'fixture']):
        done = subprocess.run(argv, capture_output=True, text=True, env=env)
        if done.returncode != 0:
            raise SystemExit('the fixture line could not be built: '
                             + done.stderr.strip())

    started = time.monotonic()
    done = subprocess.run([sys.executable, '-c', CHILD, module, str(root),
                           str(line), str(scratch)],
                          capture_output=True, text=True, env=env)
    seconds = round(time.monotonic() - started, 3)
    observed = json.loads(done.stdout) if done.stdout.strip() else None
    report = dict(
        schema='baton.w339626-confinement-reproduction/1',
        what='a bounded author DIAGNOSTIC: the real product confinement module '
             'applied in a throwaway child under a temporary root, then the '
             'exact /dev/null O_RDWR open and a REAL git clone of a real local '
             'line. NOT a product-test run and NOT independent acceptance '
             'evidence.',
        module=module, work=str(work), child_status=done.returncode,
        child_stderr=done.stderr.strip()[-600:], seconds=seconds,
        observed=observed,
        wrote_only_under=str(work),
        mutated_nothing_installed=True, started_no_runtime=True,
        submitted_no_job=True, read_no_credential=True)
    json.dump(report, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write('\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
