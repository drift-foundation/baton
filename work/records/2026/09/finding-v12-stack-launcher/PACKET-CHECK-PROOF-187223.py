"""W183883 — the packet's check block, EXTRACTED and run against failures.

Review 2026-09-16T14-40-22Z extracted the previous block, drove it with
simulated repository reads, and found it returned 0 when the workspace could
not be stat-ed and when the workspace had alternates. A check that passes when
its reads fail is worse than no check: it converts "I could not tell" into "it
is fine".

So the block is not asserted to be fail-closed here; it is EXTRACTED from
OPERATOR-INDEPENDENT-REPOSITORY.md -- the same text an operator copies -- and
run against one good case and seven bad ones. Every bad one must exit non-zero
and name what it refused.

WHAT IS SIMULATED AND WHAT IS NOT. `git` is a stub on PATH answering the four
reads the block makes; `realpath` and `stat` are the host's own. Directories,
alternates files and missing paths are real. NO REPOSITORY IS CREATED, CLONED
OR MODIFIED -- this Work performs no version-control mutation, which is exactly
why the block has to be checkable without one.

    python3 PACKET-CHECK-PROOF-187223.py > PACKET-CHECK-PROOF-187223.json
"""
import json
import os
import pathlib
import re
import shutil
import subprocess
import tempfile

PACKET = pathlib.Path(__file__).with_name("OPERATOR-INDEPENDENT-REPOSITORY.md")

STUB = r'''#!/usr/bin/env python3
"""A stand-in for the repository tool, answering from a scripted table."""
import json, os, sys

table = json.loads(os.environ["W183883_STUB"])
argv = sys.argv[1:]
if argv[:1] == ["-C"]:
    repository, argv = argv[1], argv[2:]
else:
    repository = os.getcwd()
answer = table.get(repository, {})
if argv[:1] == ["rev-parse"] and "--git-common-dir" in argv:
    said = answer.get("common")
    if said is None:
        sys.stderr.write("not a repository\n"); raise SystemExit(128)
    print(said); raise SystemExit(0)
if argv[:1] == ["rev-parse"] and "--verify" in argv:
    wanted = argv[-1]
    raise SystemExit(0 if wanted in answer.get("references", []) else 1)
if argv[:1] == ["cat-file"]:
    wanted = argv[-1].split("^")[0]
    raise SystemExit(0 if wanted in answer.get("commits", []) else 1)
if argv[:1] == ["remote"]:
    print("origin\tsomewhere (fetch)"); raise SystemExit(0)
if argv[:1] == ["count-objects"]:
    print("count: 0"); raise SystemExit(0)
sys.stderr.write("the stub was asked something the packet should not ask: "
                 + " ".join(argv) + "\n")
raise SystemExit(129)
'''


def block():
    """The shell the packet actually tells an operator to copy."""
    text = PACKET.read_text()
    found = re.findall(r"```sh\n(#!/usr/bin/env bash\n.*?)```", text, re.S)
    if len(found) != 1:
        raise AssertionError("expected exactly one check block, found %d"
                             % len(found))
    return found[0]


def repository_at(root, name, *, common=None, commits=(), references=()):
    """A directory that LOOKS like a repository to the stub, on real disk."""
    place = root / name
    place.mkdir(parents=True, exist_ok=True)
    held = place if common is None else common
    (held / "objects" / "info").mkdir(parents=True, exist_ok=True)
    return {"path": str(place), "common": str(held),
            "commits": list(commits), "references": list(references)}


def case(name, build):
    """One scenario: build the world, run the block, report the outcome."""
    root = pathlib.Path(tempfile.mkdtemp(prefix="w183883-packet-"))
    try:
        table, destination, sources = build(root)
        script = block()
        script = script.replace("D=/srv/baton-v12", "D=" + str(destination))
        script = script.replace('SOURCES=("$D/repo/source-impl-a")',
                                "SOURCES=(%s)" % " ".join(
                                    '"%s"' % one for one in sources))
        script = script.replace("BASE=<BASE>", "BASE=" + "a" * 40)
        script = script.replace("REFERENCE=refs/heads/<REFERENCE>",
                                "REFERENCE=refs/heads/main")
        binaries = root / "bin"
        binaries.mkdir(exist_ok=True)
        stub = binaries / "git"
        stub.write_text(STUB)
        stub.chmod(0o755)
        done = subprocess.run(
            ["bash", "-c", script], capture_output=True, text=True, timeout=120,
            env=dict(os.environ, PATH=str(binaries) + ":" + os.environ["PATH"],
                     W183883_STUB=json.dumps(table)))
        return {"case": name, "exit": done.returncode,
                "refused": [one for one in done.stderr.splitlines()
                            if one.startswith("REFUSED")],
                "stdout_tail": done.stdout.strip().splitlines()[-1:]}
    finally:
        shutil.rmtree(root, ignore_errors=True)


def world(root, *, workspace_common=None, source_common=None,
          workspace_missing=False, alternates=None, commits=("a" * 40,),
          references=("refs/heads/main",), workspace_unreadable=False):
    destination = root / "deployment"
    target = repository_at(destination, "repo/target.git", commits=commits,
                           references=references)
    if workspace_missing:
        workspace = {"path": str(destination / "repo/workspace"),
                     "common": str(destination / "repo/workspace")}
    else:
        common = (pathlib.Path(target["common"]) if workspace_common == "target"
                  else None)
        workspace = repository_at(destination, "repo/workspace", common=common)
    if workspace_unreadable:
        workspace = {"path": str(destination / "repo/workspace"), "common": None}
        (destination / "repo/workspace").mkdir(parents=True, exist_ok=True)
    common = (pathlib.Path(target["common"]) if source_common == "target"
              else pathlib.Path(workspace["common"])
              if source_common == "workspace" else None)
    source = repository_at(destination, "repo/source-impl-a", common=common)
    if alternates:
        held = {"target": target, "workspace": workspace,
                "source": source}[alternates]
        borrowed = pathlib.Path(held["common"]) / "objects" / "info" / "alternates"
        borrowed.parent.mkdir(parents=True, exist_ok=True)
        borrowed.write_text("/somewhere/else/objects\n")
    table = {one["path"]: one for one in (target, workspace, source)}
    return table, destination, [source["path"]]


results = [
    case("everything holds", lambda root: world(root)),
    case("the workspace directory is absent",
         lambda root: world(root, workspace_missing=True)),
    case("the workspace is not a repository the tool can identify",
         lambda root: world(root, workspace_unreadable=True)),
    case("the workspace shares the target's repository",
         lambda root: world(root, workspace_common="target")),
    case("the workspace borrows objects from elsewhere",
         lambda root: world(root, alternates="workspace")),
    case("the target borrows objects from elsewhere",
         lambda root: world(root, alternates="target")),
    case("a source shares the workspace's repository",
         lambda root: world(root, source_common="workspace")),
    case("the declared base is not in the target",
         lambda root: world(root, commits=())),
    case("the import reference does not exist",
         lambda root: world(root, references=())),
]

good = results[0]
bad = results[1:]
print(json.dumps({
 "work": "W183883", "claim": 187223,
 "what": "the packet's own check block, extracted from "
         "OPERATOR-INDEPENDENT-REPOSITORY.md and driven against one good case "
         "and eight bad ones. Review 2026-09-16T14-40-22Z found the previous "
         "block returned 0 when the workspace could not be stat-ed and when it "
         "had alternates.",
 "simulated": "the repository tool is a stub answering four reads; `realpath` "
              "and `stat` are the host's own and the directories, alternates "
              "files and missing paths are real. Nothing is created, cloned or "
              "modified.",
 "the_good_case_passes": good["exit"] == 0,
 "every_bad_case_refuses": all(one["exit"] != 0 and one["refused"]
                               for one in bad),
 "results": results,
}, indent=1, sort_keys=True))
