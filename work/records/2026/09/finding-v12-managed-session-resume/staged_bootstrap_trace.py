"""The STAGE-TO-BOOTSTRAP path, driven for real in a disposable installation.

OWNER REROUTE 311736. The operator's setup failed before live execution: the
staged manager lacked
`src/baton_v12/contracts/schema/worker-control-1.0.schema.json`, so bootstrap
failed, and `prepare-work`, `bind` and `check` then failed for want of the
`bootstrap.json` and `packet.json` bootstrap never wrote. The reroute asks for
the actual path to be PROVED rather than reasoned about, in a disposable
installation, WITHOUT Docker and WITHOUT live providers.

WHAT THIS DRIVES, AND WHAT IT DELIBERATELY DOES NOT.

  It runs the REAL `stage` over the REAL reviewed selection, with only the
    instance, staging, store, context and workspace paths redirected into one
    disposable temporary root. The origin, the reviewed source base, the
    runtime distro and the image and profile digests are the reviewed ones.
  It then runs `tools.bootstrap` FROM THE STAGED TREE, as a subprocess whose
    `PYTHONPATH` is the staged source and nothing else -- which is the exact
    condition the owner's failure occurred under.
  It reproduces the DEFECT on a copy of the same staged tree with the resources
    removed, so the failure the report describes is shown rather than asserted.
  It builds no image, starts no engine, runs no provider, and opens nothing
    outside the temporary root. The only thing it reads outside is reviewed and
    read-only: the origin, the declared source base and the built distro.

Run it directly; it prints one JSON evidence document and exits non-zero if any
expectation fails.
"""
import copy
import json
import os
import shutil
import subprocess
import sys
import tempfile

import correction_packet as packets

DOSSIER = os.path.dirname(os.path.realpath(__file__))
SELECTIONS = os.path.join(DOSSIER, "SELECTIONS-RESOLVED-311606.json")
# The interpreter this dossier's runs use. Named rather than `sys.executable`
# so the recorded evidence says which one.
INTERPRETER = "/home/sl/.local/state/baton-v12-venv/bin/python"
# What `frozen.py` reads at import time, and what a bundle without it does.
IMPORTS = ("import tools.bootstrap as bootstrap;"
           "import baton_v12.contracts.frozen as frozen;"
           "print(json.dumps({'schema': bootstrap.SCHEMA,"
           "'assets': sorted(bootstrap.EXPECTED_ASSETS),"
           "'worker_control_bytes': len(frozen.WORKER_CONTROL_BYTES),"
           "'agent_session_bytes': len(frozen.AGENT_SESSION_BYTES)}))")


# The claim this trace is recorded under; `bind` retains it in the packet.
CLAIM = 311743


class TraceFailed(Exception):
    """An expectation this trace exists to hold did not hold."""


def _held(what, said):
    if not what:
        raise TraceFailed(said)


def disposable_selection(root):
    """The reviewed selection with every WRITTEN path inside `root`.

    NOTHING DEPLOYED IS TOUCHED. The instance, the four stores, the state root,
    the private-context store, the workspaces and the staging root move into
    the temporary root; the origin, the reviewed source, the runtime and every
    digest stay exactly as reviewed, because those are what the proof is about.
    """
    with open(SELECTIONS, encoding="utf-8") as handle:
        chosen = json.load(handle)
    chosen = copy.deepcopy(chosen)
    # THE RUN NAMES ITS OWN STATE: `held_selections` refuses an instance root
    # whose path does not carry the run id, so the disposable paths carry it
    # too. The run id itself stays as reviewed, so the documents `stage` writes
    # here are the documents it would write there.
    # AND THE STAGED SOURCE DOES NOT SHARE A PARENT WITH THE INSTANCE.
    # `stage_execution._checkout()` answers three parents above its own file,
    # so `dirname(staging_root)` is the tree the staged code calls its
    # checkout and `bootstrap.admit` refuses any instance inside it. The
    # delivered plan made them siblings under `/home/sl/baton-instances`; this
    # trace is where that was found, by running the real bootstrap.
    instance = os.path.join(root, "instances", chosen["run_id"])
    chosen["instance_root"] = instance
    chosen["staging_root"] = os.path.join(root, "staging",
                                          chosen["run_id"] + "-source")
    chosen["stores"] = {
        "authority": os.path.join(instance, "db", "authority.sqlite3"),
        "control": os.path.join(instance, "db", "control.sqlite3"),
        "integration": os.path.join(instance, "db", "integration.sqlite3"),
        "job": os.path.join(instance, "db", "jobs.sqlite3"),
        "state_root": os.path.join(instance, "deployment-state")}
    chosen["workspace_storage"] = os.path.join(instance, "run", "workspaces")
    chosen["context_storage"] = {
        "path": os.path.join(instance, "run", "private-contexts"),
        "excluded": [chosen["source"]["root"],
                     os.path.join(instance, "run", "workspaces")]}
    return chosen


def _run(argv, *, tree=None, cwd, timeout=600, extra=None):
    """One subprocess, with the staged tree as the ONLY import path."""
    environment = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    if tree is None:
        environment.pop("PYTHONPATH", None)
    else:
        environment["PYTHONPATH"] = os.path.join(tree, "src") + ":" + tree
    if extra:
        environment.update(extra)
    return subprocess.run(argv, capture_output=True, text=True, cwd=cwd,
                          env=environment, timeout=timeout)


def modules_only(staged, destination):
    """The DEFECT'S tree: the corrected staging with every resource removed.

    This is what the owner ran: a bundle of modules. Built by SUBTRACTION from
    the corrected stage so the two trees differ in nothing else.
    """
    shutil.copytree(staged, destination)
    removed = []
    for here, _directories, names in os.walk(destination):
        for name in sorted(names):
            if not name.endswith(".py"):
                whole = os.path.join(here, name)
                removed.append(os.path.relpath(whole, destination))
                os.unlink(whole)
    return destination, sorted(removed)


# WHAT THE CHILD DOES, and why it is a child. `baseline.prepare` must run with
# the STAGED tree as its import path -- the same condition the supervisor runs
# under -- and it opens a control store, so it is given its own interpreter and
# its own process rather than sharing this one's imports.
_PREPARE = """
import json, os, sys
sys.path.insert(0, os.environ["DOSSIER"])
import correction_packet as packets
import correction_supervisor as supervisor
from baton_v12.worker_manager import ControlStore, context_delivery, workspaces

packet = packets.held_packet(os.environ["PACKET"],
                             supervisor=supervisor.__file__)
answer = {"roots_before": [
    {"role": one["role"], "path": one["path"], "mode": one["mode"],
     "exists": os.path.isdir(one["path"])}
    for one in packet["filesystem_roots"]]}
deployment = packet["deployment"]
with ControlStore.open(deployment["control_store"],
                       incarnation=packet["run_id"],
                       clock=supervisor.baseline._moment) as control:
    answer["prepared"] = supervisor.baseline.prepare(control, packet)
    # AND THE PRODUCT'S OWN READERS AGREE, which is what makes the two
    # registrations facts rather than a return value.
    answer["configured_workspace_storage"] = (
        workspaces.configured_workspace_storage(control).place)
    answer["configured_context_storage"] = (
        context_delivery.configured_context_storage(control).path)
print(json.dumps(answer))
"""


def _prepare_leg(destination, packet_path, *, cwd):
    """Run the real `baseline.prepare`, then try it again with a root removed.

    BOTH DIRECTIONS. The positive leg proves the corrected preparation is
    sufficient; the negative leg reproduces the owner's failure on the same
    instance by removing one root, so the evidence shows the absence being
    refused rather than only its presence succeeding.
    """
    with open(packet_path, encoding="utf-8") as handle:
        packet = json.load(handle)
    staged = packet["manager_source"]["path"]
    environment = {"PACKET": packet_path, "DOSSIER": DOSSIER}
    held = {}

    done = _run([INTERPRETER, "-B", "-c", _PREPARE], tree=staged, cwd=cwd,
                extra=environment)
    said = (done.stdout + done.stderr).strip()
    _held(done.returncode == 0,
          "`baseline.prepare` failed over the corrected preparation:\n" + said)
    answered = json.loads(done.stdout)
    held["succeeded"] = {
        "returncode": done.returncode,
        "roots_the_bind_step_established": answered["roots_before"],
        "prepared": answered["prepared"],
        "configured_workspace_storage":
            answered["configured_workspace_storage"],
        "configured_context_storage": answered["configured_context_storage"],
        "read_back_with": "workspaces.configured_workspace_storage and "
                          "context_delivery.configured_context_storage",
    }
    for one in answered["roots_before"]:
        _held(one["exists"], "the bind step left " + one["path"] + " absent")

    # THE OWNER'S FAILURE, REPRODUCED on the same instance: remove the
    # workspace store and ask again.
    removed = [one for one in packet["filesystem_roots"]
               if one["role"] == "workspace_storage"][0]["path"]
    # `rmtree` AND NOT `rmdir`, because the registration above left the store's
    # own bookkeeping inside it. This is the disposable root only: nothing
    # outside this temporary directory is touched by this program, ever.
    shutil.rmtree(removed)
    done = _run([INTERPRETER, "-B", "-c", _PREPARE], tree=staged, cwd=cwd,
                extra=environment)
    said = (done.stdout + done.stderr).strip()
    held["refused_when_the_root_is_absent"] = {
        "removed": removed,
        "returncode": done.returncode,
        "failure": said.strip().splitlines()[-1] if said else "",
        "refused_by_the_packet_before_a_store_opened":
            "re-run the bind step" in said,
    }
    _held(done.returncode != 0,
          "removing the workspace store did not stop `baseline.prepare`")
    os.makedirs(removed, exist_ok=True)
    return held


def trace(root):
    evidence = {"schema": "baton.stage-bootstrap-trace/1",
                "disposable_root": root,
                "interpreter": INTERPRETER,
                "docker": "not used", "providers": "not run"}

    chosen = disposable_selection(root)
    selections = os.path.join(root, "selections.json")
    with open(selections, "w", encoding="utf-8") as handle:
        handle.write(json.dumps(chosen, indent=2, sort_keys=True) + "\n")
    # READ BACK THROUGH THE PROGRAM'S OWN READER, so the trace runs over the
    # document `stage` will read rather than over the dict that wrote it.
    held = packets.held_selections(selections)

    # 1 -- THE REAL `stage`, through its own command line.
    destination = os.path.join(root, "packet")
    done = _run([INTERPRETER, "-B", os.path.join(DOSSIER,
                                                 "correction_packet.py"),
                 "stage", "--selections", selections,
                 "--destination", destination],
                tree=None, cwd=DOSSIER)
    _held(done.returncode == 0,
          "`stage` refused the disposable selection:\n" + done.stdout
          + done.stderr)
    with open(os.path.join(destination, "prepared.json"),
              encoding="utf-8") as handle:
        prepared = json.load(handle)
    staged = prepared["staged_source"]
    # WHAT THE STAGED TREE ITSELF SAYS IT NEEDS, asked in a child whose import
    # path is that tree; the names and their location are never retyped here.
    report = packets.staged_report(staged["path"])
    locations = packets.asset_locations(report)
    evidence["staged_source_report"] = report
    evidence["stage"] = {
        "returncode": done.returncode,
        "staged_root": staged["path"],
        "file_count": staged["file_count"],
        "frozen_assets": staged["frozen_assets"],
        "documents": sorted(os.listdir(destination))}
    _held(staged["frozen_assets"] == sorted(report["assets"]),
          "the staged source does not carry the declared assets")
    for name in locations.values():
        _held(name in staged["files"], "the manifest omits " + name)
        _held(os.path.isfile(os.path.join(staged["path"], name)),
              "the staged tree omits " + name)

    # 2 -- THE DEFECT, REPRODUCED from the same stage minus its resources.
    broken, removed = modules_only(staged["path"],
                                   os.path.join(root, "modules-only"))
    done = _run([INTERPRETER, "-B", "-c", "import json;" + IMPORTS],
                tree=broken, cwd=root)
    said = done.stdout + done.stderr
    _held(done.returncode != 0,
          "a module-only staged source IMPORTED, so this trace proves nothing")
    _held("worker-control-1.0.schema.json" in said,
          "the reproduced failure does not name the absent asset:\n" + said)
    evidence["defect_reproduced"] = {
        "tree": broken, "removed": removed, "returncode": done.returncode,
        "failure": said.strip().splitlines()[-1],
        "read_at": "baton_v12.contracts.frozen, at import time"}

    # 3 -- THE CORRECTED STAGE IMPORTS, and the bytes are the staged bytes.
    done = _run([INTERPRETER, "-B", "-c", "import json;" + IMPORTS],
                tree=staged["path"], cwd=root)
    _held(done.returncode == 0,
          "the corrected staged source did not import:\n" + done.stdout
          + done.stderr)
    imported = json.loads(done.stdout)
    for name, relative in sorted(locations.items()):
        with open(os.path.join(staged["path"], relative), "rb") as handle:
            measured = len(handle.read())
        key = ("worker_control_bytes" if name.startswith("worker-control")
               else "agent_session_bytes")
        _held(imported[key] == measured,
              "the imported asset is not the staged asset: " + name)
    evidence["staged_source_imports"] = imported

    # 4 -- BOOTSTRAP ITSELF, run FROM the staged tree.
    instance = chosen["instance_root"]
    # THE DOCUMENT `stage` ACTUALLY WROTE, taken from the manifest rather than
    # from a name typed here: it is `bootstrap-inputs.json`, and bootstrap's
    # own `bootstrap.json` is the RECORD it writes inside the instance.
    inputs = prepared["bootstrap_inputs"]
    _held(os.path.isfile(inputs), "`stage` wrote no input document at " + inputs)
    done = _run([INTERPRETER, "-B", "-m", "tools.bootstrap",
                 "--inputs", inputs,
                 "--destination", instance,
                 "--distro", held["manager_runtime"]["path"],
                 "--no-repositories"],
                tree=staged["path"], cwd=root)
    said = (done.stdout + done.stderr).strip()
    record = packets.installed_layout(instance)["record"]
    evidence["bootstrap"] = {
        "inputs": inputs,
        "argv": ["python", "-m", "tools.bootstrap", "--inputs", inputs,
                 "--destination", instance,
                 "--distro", held["manager_runtime"]["path"],
                 "--no-repositories"],
        "returncode": done.returncode,
        "reached_the_module": "No module named" not in said,
        "read_its_input": "no input document" not in said,
        "record_written": os.path.isfile(record),
        "last_line": said.splitlines()[-1] if said else "",
        "output": said[-4000:]}
    _held(evidence["bootstrap"]["reached_the_module"],
          "`tools.bootstrap` was not importable from the staged tree:\n" + said)
    if os.path.isfile(record):
        with open(record, encoding="utf-8") as handle:
            evidence["bootstrap"]["record"] = json.load(handle)
    if done.returncode != 0:
        return evidence

    # 5 -- THE THREE STEPS THAT FAILED FOR WANT OF WHAT BOOTSTRAP NEVER WROTE.
    # The owner's `prepare-work`, `bind` and `check` failed because
    # `bootstrap.json` and `packet.json` were absent. With the corrected
    # staging and the corrected layout they are run here, in order, over the
    # disposable instance -- which is the whole recovery path, proved rather
    # than described.
    evidence["recovery"] = []
    for step, argv in (
            ("prepare-work",
             ["prepare-work", "--selections", selections,
              "--destination", destination]),
            ("bind",
             ["bind", "--selections", selections, "--destination", destination,
              "--claim", str(CLAIM), "--provenance",
              os.path.join(DOSSIER, "PROVENANCE-309356.json")]),
            ("check",
             ["check", "--packet", os.path.join(destination, "packet.json")])):
        done = _run([INTERPRETER, "-B",
                     os.path.join(DOSSIER, "correction_packet.py")] + argv,
                    tree=staged["path"], cwd=root)
        said = (done.stdout + done.stderr).strip()
        evidence["recovery"].append({
            "step": step, "returncode": done.returncode,
            "last_line": said.splitlines()[-1] if said else "",
            "output": said[-2500:]})
        _held(done.returncode == 0,
              "`" + step + "` failed in the disposable installation:\n" + said)
    packet_path = os.path.join(destination, "packet.json")
    with open(packet_path, encoding="utf-8") as handle:
        packet = json.load(handle)
    # 6 -- ACTUAL `baseline.prepare`, WITH NOTHING PRE-CREATED BY A FIXTURE.
    #
    # OWNER REROUTE 312164. The live run reached exactly here and stopped:
    # `configure_workspace_storage` refused because `<instance>/run/workspaces`
    # did not exist, and the accepted connected fixture never showed it because
    # that fixture creates the root itself. This runs the REAL
    # `baseline.prepare` against the disposable instance's own control store,
    # and the only thing that created those roots is the bind step above. No
    # Docker, no provider, no engine: two registrations, a certification and
    # one grant, inside the temporary root.
    evidence["baseline_prepare"] = _prepare_leg(destination, packet_path,
                                                cwd=root)

    submission = packet["submission"]
    evidence["packet"] = {
        "schema": packet["schema"],
        "work": packet["work"],
        "work_id": submission.get("work_id"),
        "job_id": submission.get("job_id"),
        "submission_id": submission.get("submission_id"),
        "input_digest": submission.get("input_digest"),
        "code_boundary": packet.get("code_boundary"),
        "frozen_assets": packet["manager_source"].get("frozen_assets"),
        "file_count": packet["manager_source"].get("file_count"),
        "checked": "`check` proved this packet with the product validators"}
    _held(packet["manager_source"].get("frozen_assets")
          == sorted(report["assets"]),
          "the bound packet does not record the frozen assets")
    return evidence


def main():
    argv = sys.argv[1:]
    keep = "--keep" in argv
    written = None
    if "--evidence" in argv:
        written = argv[argv.index("--evidence") + 1]
    root = tempfile.mkdtemp(prefix="stage-bootstrap-")
    try:
        evidence = trace(root)
    finally:
        if not keep:
            shutil.rmtree(root, ignore_errors=True)
    evidence["disposable_root_removed"] = not keep
    body = json.dumps(evidence, indent=2, sort_keys=True) + "\n"
    if written:
        with open(written, "w", encoding="utf-8") as handle:
            handle.write(body)
    print(body, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
