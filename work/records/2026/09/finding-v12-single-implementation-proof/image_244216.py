"""Verify the built artefact and record what it actually carries.

Owner reroute 244214: "build a distinct image, verify accepted adapter bytes,
bind actual image and worker digests".

IT ASKS THE ARTEFACT, NOT THE BUILD CONTEXT. `Dockerfile.claude` makes the
point about itself -- "a recipe naming a suite and an image carrying an
interpreter are two facts and only the second one runs" -- so every digest here
is read out of a container started from the image, and the preserved
predecessor is re-read at the same time to prove it was not disturbed.

NO PROVIDER RUNS. The inspection container is `--network none --read-only`
with its entrypoint overridden; it hashes files and exits.
"""
import hashlib
import json
import pathlib
import subprocess

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[4]

REFERENCE = "baton-v12-claude-worker:w239528-244216"
PRESERVED = "baton-v12-claude-worker:w236087-236349"
PRESERVED_DIGEST = (
    "sha256:2e9e84ff23319778760d5b22c70d543d4290931510a3ab3ecf40bcdaad7456bd")
ACCEPTED_ADAPTER = (
    "18c34ff52faa150237df0c8d0206b805801ee71cb9e7a4ec6e84e4379d7f9d8d")
# The predecessor's adapter, which is the whole reason a new image exists.
SUPERSEDED_ADAPTER = (
    "abdf903da3c767f3fe9babf84e4499f455da968a61ee3c975b9899988354bb4d")

WORKER_FILES = ("attempt_log_format.py", "baton_worker.py", "claude_agent.py",
                "dogfood_entry.py")


def sha(path):
    reading = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            reading.update(block)
    return reading.hexdigest()


def inspected(reference):
    answer = subprocess.run(["docker", "image", "inspect", reference],
                            capture_output=True, timeout=120, check=True)
    return json.loads(answer.stdout.decode("utf-8"))[0]


def hashed_inside(reference):
    """Hash /opt/baton inside a container started FROM the image."""
    script = (
        "import hashlib,json,os\n"
        "found={}\n"
        "for base,dirs,names in os.walk('/opt/baton'):\n"
        "    dirs[:]=[d for d in sorted(dirs) if d!='__pycache__']\n"
        "    for name in sorted(names):\n"
        "        if name.endswith('.pyc'): continue\n"
        "        whole=os.path.join(base,name)\n"
        "        h=hashlib.sha256()\n"
        "        with open(whole,'rb') as fh:\n"
        "            for block in iter(lambda: fh.read(1<<20), b''): "
        "h.update(block)\n"
        "        found['opt/baton/'+os.path.relpath(whole,'/opt/baton')]="
        "h.hexdigest()\n"
        "print(json.dumps(found))\n")
    answer = subprocess.run(
        ["docker", "run", "--rm", "--network", "none", "--read-only",
         "--entrypoint", "python3", reference, "-c", script],
        capture_output=True, timeout=600, check=True)
    return json.loads(answer.stdout.decode("utf-8"))


def provider_version(reference):
    answer = subprocess.run(
        ["docker", "run", "--rm", "--network", "none", "--read-only",
         "--entrypoint", "claude", reference, "--version"],
        capture_output=True, timeout=600, check=False)
    return answer.stdout.decode("utf-8").strip() or None


def main():
    built = inspected(REFERENCE)
    kept = inspected(PRESERVED)
    if kept.get("Id") != PRESERVED_DIGEST:
        raise SystemExit(
            f"the preserved image is now {kept.get('Id')!r} and was "
            f"{PRESERVED_DIGEST!r}; it must not have been rebuilt or retagged")
    if built.get("Id") == PRESERVED_DIGEST:
        raise SystemExit("the new image is the preserved one; a DISTINCT "
                         "artefact was selected")

    inside = hashed_inside(REFERENCE)
    adapter = inside.get("opt/baton/claude_agent.py")
    if adapter != ACCEPTED_ADAPTER:
        raise SystemExit(
            f"the built image carries claude_agent.py {adapter!r} and "
            f"independent review accepted {ACCEPTED_ADAPTER!r}")
    if adapter == SUPERSEDED_ADAPTER:
        raise SystemExit("the built image carries the superseded adapter")
    # AND THE CORRECTION IS PRESENT BY NAME, not only by digest.
    named = subprocess.run(
        ["docker", "run", "--rm", "--network", "none", "--read-only",
         "--entrypoint", "python3", REFERENCE, "-c",
         "import claude_agent,json;print(json.dumps("
         "{'umask':claude_agent.PROVIDER_UMASK}))"],
        capture_output=True, timeout=600, check=True)
    umask = json.loads(named.stdout.decode("utf-8"))["umask"]
    if umask != 0o077:
        raise SystemExit(f"the built image's PROVIDER_UMASK is {oct(umask)}")

    # The predecessor's own adapter, re-read, so the record shows both.
    was = hashed_inside(PRESERVED).get("opt/baton/claude_agent.py")

    artifact = {
        "schema": "baton.single-implementation-worker-artifact/1",
        "work": "W239528", "claim": 244216, "participant": "baton.claude",
        "reference": REFERENCE,
        "image_config_digest": built["Id"],
        "entrypoint": built["Config"].get("Entrypoint"),
        "user": built["Config"].get("User"),
        "size_bytes": built.get("Size"),
        "created": built.get("Created"),
        "provider_cli": provider_version(REFERENCE),
        "recipe": "v12/worker/Dockerfile.claude, build context v12/",
        "accepted_adapter": {
            "path": "opt/baton/claude_agent.py",
            "sha256": adapter,
            "accepted_by": "review-2026-09-23T03-19-21Z.md",
            "provider_umask": oct(umask),
            "source_in_tree": sha(ROOT / "v12/worker/claude_agent.py"),
        },
        "worker_files": {f"opt/baton/{one}": inside[f"opt/baton/{one}"]
                         for one in WORKER_FILES},
        "all_worker_files": inside,
        "supersedes": {
            "reference": PRESERVED,
            "image_config_digest": PRESERVED_DIGEST,
            "claude_agent_sha256": was,
            "preserved": True,
            "why": ("that image carries the adapter without PROVIDER_UMASK; "
                    "every earlier packet in this campaign is bound to it and "
                    "it is neither retagged, rebuilt nor removed"),
        },
        "verified_how": ("every digest read from a container started FROM the "
                         "image, with --network none --read-only and the "
                         "entrypoint overridden; no provider ran"),
        "not_established": (
            "how the real CLI behaves under this mask. Review "
            "2026-09-23T03:19:21Z: the retained 0o755 modes are consistent "
            "with umask creation but do not exclude an explicit chmod or a "
            "reset mask, and only a real turn under this image can answer "
            "that. No live provider execution is authorized here."),
    }
    (HERE / "IMAGE-ARTIFACT-244216.json").write_text(
        json.dumps(artifact, indent=2, sort_keys=True) + "\n",
        encoding="utf-8")
    print(json.dumps({one: artifact[one] for one in
                      ("reference", "image_config_digest", "provider_cli")},
                     indent=2, sort_keys=True))
    print("accepted adapter inside the artefact:", adapter)
    print("predecessor's adapter, preserved:", was)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
