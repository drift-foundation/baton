"""Measure the Baton worker code actually installed in each configured image. W386447.

WHY THIS EXISTS (review 2026-11-27 [3]). Whether a resumed provider is told
the owner's decision is decided by the adapter INSIDE the worker image, so a
launch that depends on it must know what that image holds. A revision label
and a source marker say what an image claims it was built from; they do not
say what was installed. This reads the installed files themselves, from the
exact immutable image ID each configured worker pins, and compares every
Baton file there byte for byte with a source tree.

WHAT IS READ, AND HOW. For each worker in a deployment document: the
configured `image_digest`; `image inspect`, whose `Id` must BE that digest
(a moved tag or a different artefact refuses); a container CREATED from the
ID and never started (`--network none`); `cp <container>:/opt/baton -`, the
installed tree as a tar stream read in memory; and `rm` of exactly that
container. Nothing is executed inside an image.

WHAT QUALIFIES. Every regular file under `/opt/baton` that the source tree
also provides (`worker/<name>` or `python/src/baton_v12/<name>`) is equal to
it. The configured provider determines the required adapter modules and the
exact ENTRYPOINT, whose installed bytes must also match. Installed
files the source does not provide are listed, not judged. The report binds
each image ID to the digests measured, and is the evidence a launch keeps.

Run: `python -m tools.installed_worker --deployment <deployment.json>
--source <v12 tree> [--docker docker] [--report out.json]`. Exit 0 when every
configured worker qualifies, 1 when one does not, 2 when one cannot be read.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tarfile

INSTALLED = "/opt/baton"
SOURCES = ("worker", "python/src/baton_v12")
# codex_entry imports dogfood_entry, and CodexAgent uses the shared Claude adapter module.
PROVIDER_LAYOUTS = {
    "claude": ("dogfood_entry.py", ("claude_agent.py",)),
    "codex": ("codex_entry.py", ("dogfood_entry.py", "claude_agent.py", "codex_agent.py")),
}
TIMEOUT = 300


class Unreadable(Exception):
    pass


def configured(deployment):
    """[(worker_id, provider, image ID)] in the deployment's own order."""
    found = []
    for worker in deployment.get("workers") or []:
        contract = (worker.get("deployment") or {}).get("provider_contract") or {}
        profile = contract.get("runtime_profile") or {}
        provider = (contract.get("selection") or {}).get("provider")
        if type(provider) is not str or provider not in PROVIDER_LAYOUTS:
            raise Unreadable("worker " + str(worker.get("worker_id")) + " has no supported provider selection")
        if provider != profile.get("provider") or provider != (contract.get("adapter") or {}).get("provider"):
            raise Unreadable("worker " + str(worker.get("worker_id")) + " has inconsistent configured providers")
        image = profile.get("image_digest")
        if type(image) is not str or not image.startswith("sha256:") or len(image) != 71:
            raise Unreadable("worker " + str(worker.get("worker_id")) + " pins no immutable image ID")
        found.append((worker["worker_id"], provider, image))
    if not found:
        raise Unreadable("the deployment configures no worker")
    return found


def _docker(docker, *arguments):
    try:
        done = subprocess.run([docker, *arguments], stdin=subprocess.DEVNULL, capture_output=True,
                              timeout=TIMEOUT, check=False)
    except (OSError, subprocess.TimeoutExpired) as failure:
        raise Unreadable(docker + " " + arguments[0] + ": " + type(failure).__name__) from failure
    if done.returncode != 0:
        raise Unreadable(" ".join((docker,) + arguments[:2]) + " exited " + str(done.returncode) + ": "
                         + done.stderr.decode("utf-8", "replace").strip()[:400])
    return done.stdout


def installed(docker, image):
    """The image's config and {relative path: bytes} under /opt/baton, read without running it."""
    try:
        [inspected] = json.loads(_docker(docker, "image", "inspect", image))
    except ValueError as failure:
        raise Unreadable("image inspect of " + image + " is not one image document") from failure
    if inspected.get("Id") != image:
        raise Unreadable("the engine's image for " + image + " is " + str(inspected.get("Id")))
    container = _docker(docker, "create", "--network", "none", image).decode("ascii", "replace").strip()
    if not container or any(c not in "0123456789abcdef" for c in container):
        raise Unreadable("create answered no container ID")
    try:
        stream = _docker(docker, "cp", container + ":" + INSTALLED, "-")
    finally:
        _docker(docker, "rm", container)
    files = {}
    try:
        with tarfile.open(fileobj=io.BytesIO(stream), mode="r:") as archive:
            for member in archive:
                parts = Path(member.name).parts[1:]
                if not member.isreg() or not parts or "__pycache__" in parts:
                    continue
                files["/".join(parts)] = archive.extractfile(member).read()
    except tarfile.TarError as failure:
        raise Unreadable("the copied tree of " + image + " is not a tar stream") from failure
    return inspected, files


def _digest(data):
    return "sha256:" + hashlib.sha256(data).hexdigest()


def compare(source, inspected, files, provider):
    """Judge one image's installed tree against a v12 source tree."""
    source = Path(source)
    measured, unmatched, problems = {}, [], []
    for name in sorted(files):
        origin = next((source / root / name for root in SOURCES if (source / root / name).is_file()), None)
        if origin is None:
            unmatched.append(name)
            continue
        wanted = origin.read_bytes()
        measured[name] = {"installed": _digest(files[name]), "source": _digest(wanted),
                          "source_path": str(origin.relative_to(source)), "equal": files[name] == wanted}
        if files[name] != wanted:
            problems.append(name + " differs from " + str(origin.relative_to(source)))
    required_entry, adapters = PROVIDER_LAYOUTS[provider]
    for name in adapters:
        if name not in measured:
            problems.append(name + " is not installed at " + INSTALLED)
    entrypoint = (inspected.get("Config") or {}).get("Entrypoint")
    entry = None
    if type(entrypoint) is list and len(entrypoint) == 2 and entrypoint[0] == "python3" \
            and type(entrypoint[1]) is str and entrypoint[1].startswith(INSTALLED + "/"):
        entry = entrypoint[1][len(INSTALLED) + 1:]
    if entry is None or entry not in measured:
        problems.append("the entrypoint " + json.dumps(entrypoint) + " is not a measured Baton entry")
    elif entry != required_entry:
        problems.append(provider + " requires entrypoint " + INSTALLED + "/" + required_entry)
    elif not measured[entry]["equal"]:
        problems.append("the entrypoint " + entry + " is not the source's")
    return {"entrypoint": entrypoint, "measured": measured, "unmatched": unmatched,
            "problems": problems, "qualified": not problems}


def measure(deployment, source, *, docker="docker"):
    report = {"schema": "baton.v12.installed-worker/1", "installed_root": INSTALLED, "workers": []}
    for worker_id, provider, image in configured(deployment):
        inspected, files = installed(docker, image)
        report["workers"].append(dict(compare(source, inspected, files, provider), worker_id=worker_id, provider=provider, image=image))
    report["qualified"] = all(one["qualified"] for one in report["workers"])
    return report


def main(argv=None, *, stream=None):
    stream = stream or sys.stdout
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--deployment", required=True)
    parser.add_argument("--source", required=True, help="a v12 tree: the directory holding worker/ and python/")
    parser.add_argument("--docker", default="docker")
    parser.add_argument("--report")
    taken = parser.parse_args(argv)
    try:
        report = measure(json.loads(Path(taken.deployment).read_text()), taken.source, docker=taken.docker)
    except (Unreadable, OSError, ValueError) as failure:
        print("unreadable: " + str(failure), file=stream)
        return 2
    if taken.report:
        Path(taken.report).write_text(json.dumps(report, indent=1, sort_keys=True) + "\n")
    for one in report["workers"]:
        print(("QUALIFIED " if one["qualified"] else "NOT QUALIFIED ") + one["worker_id"] + " " + one["image"]
              + ": " + str(len(one["measured"])) + " Baton file(s) measured"
              + "".join("; " + problem for problem in one["problems"]), file=stream)
    return 0 if report["qualified"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
