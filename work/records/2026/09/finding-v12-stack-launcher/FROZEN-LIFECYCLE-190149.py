"""W183883 claim190149 -- the CURRENT candidate, built, installed, and served.

Review 2026-09-16T23-16-06Z: after the runtime guard is corrected, perform one
focused build / install / empty-lifecycle verification of the current
candidate. Bind the source and the bundle, use the DESTINATION-LOCAL commands,
and run them with no checkout, no PYTHONPATH and no build environment.

WHAT THIS RUNS: pip (from the committed lock) and PyInstaller, once; then the
source installer, once; then the frozen launcher's own start/status/monitor/
stop through the destination's justfile. `--no-repositories`, so no clone and
no version-control command happens at all. No provider, no engine, no Job, no
model, no network beyond what the pinned build already needs.

Evidence lands in FROZEN-LIFECYCLE-190149.json beside this file. The temporary
destination is removed at the end and the removal is recorded.
"""
import hashlib, json, os, pathlib, shutil, subprocess, sys, tempfile, time

CHECKOUT = pathlib.Path("/home/sl/src/baton")
V12 = CHECKOUT / "v12"
PYTHON = V12 / "python"
sys.path.insert(0, str(PYTHON))
sys.path.insert(1, str(PYTHON / "src"))

RECORD = pathlib.Path(__file__).resolve().parent
evidence = {"claim": 190149, "what": "the current candidate, frozen and served"}


def digest(relative):
    return hashlib.sha256((CHECKOUT / relative).read_bytes()).hexdigest()


evidence["candidate_source"] = {
    name: digest(name) for name in (
        "v12/python/tools/stage_execution.py",
        "v12/python/tools/bootstrap.py",
        "v12/python/src/baton_v12/worker_manager/offers.py",
        "v12/python/src/baton_v12/job_manager/scheduler.py",
        "v12/STACK.md")}


def ran(argv, *, cwd, env=None, timeout=3600, label=""):
    started = time.monotonic()
    done = subprocess.run(argv, cwd=str(cwd), capture_output=True, text=True,
                          timeout=timeout,
                          env=os.environ if env is None else env)
    return {"label": label or argv[0], "returncode": done.returncode,
            "seconds": round(time.monotonic() - started, 3),
            "stdout": done.stdout[-4000:], "stderr": done.stderr[-4000:]}


JUST = shutil.which("just")
assert JUST, "`just` is not on PATH"

# -- 1. build the current candidate -------------------------------------------
built = ran([JUST, "--justfile", str(V12 / "justfile"), "build"], cwd=V12,
            label="just build (pip from the committed lock, then PyInstaller "
                  "--clean)", timeout=7200)
evidence["build"] = {name: built[name] for name in
                     ("label", "returncode", "seconds")}
evidence["build"]["stderr_tail"] = built["stderr"][-1500:]
assert built["returncode"] == 0, built["stderr"][-4000:]

from tools import instance as instances                      # noqa: E402

DISTRO = PYTHON / "build" / "out" / "distro"
held = instances.manifest(str(DISTRO))
evidence["bundle"] = {"path": str(DISTRO), "digest": held["digest"],
                      "files": len(held["entries"])}
evidence["bundle"]["stamp"] = json.loads(
    (DISTRO / "_internal" / "build-stamp.json").read_bytes())
evidence["bundle"]["bytes"] = sum(
    (DISTRO / one).stat().st_size for one in held["entries"])

# THE BUNDLE CARRIES THIS CANDIDATE. `stage_execution.py` is frozen into the
# archive rather than left on disk, so the binding is the stamp's commit plus
# the dirty flag plus the launcher answering for itself below.
evidence["bundle"]["binds_candidate"] = {
    "how": "the build ran from this checkout; the stamp records its commit and "
           "dirty state, and `--version` below is the bundle's own answer",
    "source_digests": evidence["candidate_source"]}

# -- 2. install it into a fresh destination -----------------------------------
root = tempfile.mkdtemp(prefix="w183883-frozen-190149-", dir="/var/tmp")
destination = os.path.join(root, "deployment")
from tests.tools.test_bootstrap import guide_example            # noqa: E402

inputs = os.path.join(root, "inputs.json")
pathlib.Path(inputs).write_text(json.dumps(guide_example()) + "\n")
evidence["input"] = {"path": inputs, "members": sorted(guide_example()),
                     "from": "STACK.md's fresh-install block"}

install = ran([JUST, "--justfile", str(V12 / "justfile"), "bootstrap",
               inputs, destination, str(DISTRO), "--no-repositories"],
              cwd=V12, label="just bootstrap (two operands + no repositories)")
evidence["install"] = install
assert install["returncode"] == 0, install["stdout"] + install["stderr"]

places = instances.layout(destination)
evidence["installed"] = {
    "selector": json.loads(pathlib.Path(places["instance"]).read_bytes()),
    "justfile_present": os.path.isfile(places["justfile"]),
    "runtime_digest": instances.manifest(places["distro"])["digest"],
    "identity": json.loads(pathlib.Path(places["identity"]).read_bytes()),
    "repository_entries": sorted(os.listdir(places["repository"]))}
assert evidence["installed"]["runtime_digest"] == evidence["bundle"]["digest"]

# -- 3. the lifecycle, with NOTHING from this checkout ------------------------
# No PYTHONPATH, no BATON_V12_*, no virtual environment, and `cd`-ed into the
# destination rather than the checkout. PATH carries the system tools the
# recipes need and `just` itself, and nothing from the build environment.
bare = {"HOME": root, "PATH": os.path.dirname(JUST) + ":/usr/bin:/bin",
        "XDG_RUNTIME_DIR": root}
evidence["environment"] = {"kept": sorted(bare), "PATH": bare["PATH"],
                           "no_pythonpath": "PYTHONPATH" not in bare,
                           "no_baton_v12_variables": True,
                           "cwd": destination}

version = ran([os.path.join(places["distro"], "baton-v12-stack"), "--version"],
              cwd="/", env=bare, label="the installed launcher --version")
evidence["version"] = version

# `just monitor` IS UNBOUNDED BY DESIGN -- STACK.md says Ctrl-C is the way out
# of it, and the deployed recipe forwards only an interval. A harness cannot
# press Ctrl-C, and the first attempt at this run proved it by hanging there
# for its whole 600s timeout. So the WATCH is asked of the bundled command
# directly, with the `--ticks` bound it already takes, and the recipe forms are
# used for everything that returns on its own.
COMMAND = os.path.join(places["distro"], "baton-v12-stack")
lifecycle = []
try:
    for argv, label, through in (
            (["start"], "just start", "recipe"),
            (["status"], "just status", "recipe"),
            (["monitor", "--instance", places["instance"], "--interval", "1",
              "--ticks", "2"],
             "the installed command, monitor bounded to two refreshes "
             "(`just monitor` itself is unbounded by design)", "command"),
            (["stop"], "just stop", "recipe"),
            (["status"], "just status (after stop)", "recipe")):
        whole = ([JUST, "--justfile", places["justfile"]] + argv
                 if through == "recipe" else [COMMAND] + argv)
        one = ran(whole, cwd=destination, env=bare, timeout=300, label=label)
        one["through"] = through
        lifecycle.append(one)
        assert one["returncode"] == 0, one["stdout"] + one["stderr"]
finally:
    # NOTHING THIS RUN STARTED OUTLIVES IT, whatever happened above.
    ran([JUST, "--justfile", places["justfile"], "stop"], cwd=destination,
        env=bare, timeout=300, label="stop (cleanup)")
evidence["lifecycle"] = lifecycle

# -- 4. what the run left, then remove it -------------------------------------
# THE LOGS ARE UNDER THE STACK'S OWN STATE ROOT, which is where `start` said
# it put them -- `<destination>/state` -- rather than under `logs/`.
evidence["logs"] = {}
for where in (places["state"], places["logs"]):
    held = pathlib.Path(where)
    if held.exists():
        evidence["logs"].update({one.name: one.read_text()[-3000:]
                                 for one in sorted(held.glob("*.log"))})
snapshot = pathlib.Path(places["state"]) / "status.json"
evidence["published_snapshot"] = (json.loads(snapshot.read_bytes())
                                  if snapshot.exists() else None)

removal = time.monotonic()
shutil.rmtree(root, ignore_errors=True)
evidence["cleanup"] = {"removed": root, "still_there": os.path.exists(root),
                       "seconds": round(time.monotonic() - removal, 3)}
evidence["total_seconds"] = round(
    evidence["build"]["seconds"] + install["seconds"] + version["seconds"]
    + sum(one["seconds"] for one in lifecycle), 3)

(RECORD / "FROZEN-LIFECYCLE-190149.json").write_text(
    json.dumps(evidence, indent=1, sort_keys=False) + "\n")
print("build", evidence["build"]["seconds"], "s;",
      evidence["bundle"]["files"], "files;", evidence["bundle"]["digest"][:16])
for one in [version] + lifecycle:
    print(one["label"], "->", one["returncode"])
    print("   ", one["stdout"].strip().replace("\n", "\n    ")[:800])
print("cleanup:", evidence["cleanup"])
