"""Inventory the checkout's dirty paths, prove the qualification's INPUTS stable
across the gate, and record the build stamp as the truthful history it is.

W385331 qualification round 6 (review 2026-11-21T02-34-34Z G1/G2). What a
qualification step consumes is bounded and named: the selected source (`v12/`
at the bound commit, proved clean by `tools.source_identity`), the test
runner's declared consumed inputs (hashed by content, whether or not git
calls them changed), and the reviewed helper bytes (checked by `sha256sum -c`
in the helper before this tool runs). Everything else in the repository --
review evidence, older qualification records, dossier notes -- is NOT an
input: it is inventoried here with its class and is never an execution gate,
so the finite path check -> bundle -> image -> install needs no commit for
evidence that steps themselves write.

`tools/build_stamp.py` observes the whole repository and excuses only its
three build outputs; a stamp captured after `bind` is therefore truthfully
`dirty: true` with `v12/` clean. This tool keeps that stamp UNCHANGED and does
not re-derive its counts from a later observation (evidence written after the
capture would make a true stamp look false). What it proves instead is that
the INPUTS did not move while the gate ran: the identity's content digest and
the declared inputs are the same at every step (`--stable`), and the stamp
names the bound commit.

  python3 -I native-handoffs-2-tree.py --repo DIR --sha SHA --identity ID.json
      --capture LIVE.json [--stable INPUTS.json] [--stamp RECORDED.json]
      [--helper-sums SUMS.sha256] [--out INVENTORY.json]

`--identity`: `python -m tools.source_identity --repo DIR --declared v12`.
`--capture`: the LIVE `tools.build_stamp.capture(source=DIR)` document taken
now (actual capture semantics, including its excusals), recorded beside the
inventory for comparison; never substituted for a recorded stamp.
`--stable`: the inputs record of this checkpoint; written on first use, then
compared (content digest, declared inputs, helper sums) -- a difference
refuses as input drift. `--stamp`: a recorded stamp that must name SHA and
carry an observation (`dirty` not null); it is recorded as captured.
Refusals: identity not at SHA; `v12/` changed; a declared input dirty in git;
input drift against `--stable`; a stamp naming another commit or no
observation. Read-only on Git; writes only the files named.
"""
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time

PILOT = "work/records/2026/10/finding-v12-development-coordination-pilot"
SCHEMA = "k.native-handoffs-2-tree-state/2"
STABLE_SCHEMA = "k.native-handoffs-2-inputs/1"
# `tools.build_stamp.GENERATED`, spelled here only to LABEL inventory entries
# the real capture excuses; the live capture's own counts are what is recorded.
BUILD_OUTPUT = ("v12/python/build/out/", "v12/python/build/work/", "v12/python/packaging/build-stamp.json")


def git(repo, *argv):
    return subprocess.run(["git", "-C", repo, *argv], capture_output=True, text=True, check=True,
                          env=dict(os.environ, GIT_OPTIONAL_LOCKS="0")).stdout


def observe(repo):
    """The exact observation `build_stamp.capture` makes."""
    return [one for one in git(repo, "status", "--porcelain", "--untracked-files=normal").splitlines() if one.strip()]


def dirty_inputs(repo, inputs):
    """Declared inputs git considers changed or untracked, file by file (collapsed
    directories expanded: `--untracked-files=all`)."""
    if not inputs:
        return []
    raw = subprocess.run(["git", "-C", repo, "status", "--porcelain=v1", "-z", "--untracked-files=all", "--", *inputs],
                         capture_output=True, check=True, env=dict(os.environ, GIT_OPTIONAL_LOCKS="0")).stdout
    return [one.decode("utf-8", "surrogateescape") for one in raw.split(b"\0") if one]


def entry_path(line):
    said = line[3:] if len(line) > 3 else ""
    if " -> " in said:
        said = said.split(" -> ", 1)[1]
    said = said.strip()
    if said.startswith('"') and said.endswith('"') and len(said) > 1:
        said = said[1:-1]
    return said


def generated_records(sha8):
    files = [f"{PILOT}/config/native-bound-2.json", f"{PILOT}/config/native-inputs-2-{sha8}.json",
             f"{PILOT}/config/native-instance-2-{sha8}.json", f"{PILOT}/config/native-installed-task-2-{sha8}.json",
             f"{PILOT}/config/native-workers-2-{sha8}.json"]
    for worker in ("impl-a", "review-a"):
        files += [f"{PILOT}/config/{worker}-2-{sha8}.json", f"{PILOT}/config/{worker}-2-{sha8}-compose.log"]
    prefixes = [f"{PILOT}/evidence/checkpoint-{sha8}-packaging/", f"{PILOT}/evidence/worker-image-{sha8}/",
                f"{PILOT}/evidence/native-handoffs-2-qualification/create-"]
    return files, prefixes


def classify(lines, sha8, inputs, helper=()):
    """Informational classes for the inventory. `product`, `declared-input` and
    `helper` are the inputs; the gates on them are the identity and the
    reviewed sums, not this list."""
    files, prefixes = generated_records(sha8)
    held = []
    for line in lines:
        path, status = entry_path(line), line[:2]
        if any(path == one or path.startswith(one) or path.rstrip("/") + "/" == one for one in BUILD_OUTPUT):
            kind = "build-output (excused by the stamp)"
        elif path == "v12" or path.startswith("v12/"):
            kind = "product"
        elif any(path == one or path.startswith(one.rstrip("/") + "/") for one in inputs):
            kind = "declared-input"
        elif path in helper:
            kind = "helper (reviewed bytes, bound by the sums file)"
        elif status == "??" and (path in files or any(path.startswith(p) or path.rstrip("/") + "/" == p for p in prefixes)):
            kind = "generated (this qualification, this checkpoint)"
        elif path.startswith(PILOT + "/") and re.search(r"-2-[0-9a-f]{8}|checkpoint-[0-9a-f]{8}-packaging|worker-image-[0-9a-f]{8}", path):
            kind = "unrelated (an earlier qualification record; retained, not an input)"
        else:
            kind = "unrelated (not an input)"
        held.append({"status": status, "path": path, "class": kind})
    return held


def sha256_of(place):
    with open(place, "rb") as reading:
        return hashlib.sha256(reading.read()).hexdigest()


def refuse(message):
    print("refused: " + message, file=sys.stderr)
    raise SystemExit(2)


def main(argv=None):
    parser = argparse.ArgumentParser(prog="native-handoffs-2-tree")
    parser.add_argument("--repo", required=True)
    parser.add_argument("--sha", required=True)
    parser.add_argument("--identity", required=True)
    parser.add_argument("--capture", required=True)
    parser.add_argument("--stable", default=None)
    parser.add_argument("--stamp", default=None)
    parser.add_argument("--helper-sums", default=None)
    parser.add_argument("--out", default=None)
    taken = parser.parse_args(argv)
    identity = json.load(open(taken.identity))
    live = json.load(open(taken.capture))
    if identity["head"] != taken.sha:
        refuse(f"the source identity names HEAD {identity['head']}, not the bound {taken.sha}")
    if identity["changed"]:
        refuse(f"v12/ is not clean: {[one['path'] for one in identity['changed']]}; the product inputs drifted from {taken.sha}")
    drift = dirty_inputs(taken.repo, identity["inputs"])
    if drift:
        refuse(f"declared consumed input(s) changed or untracked in git: {drift}; the qualification consumes the committed inputs of {taken.sha}")
    if live.get("commit") != taken.sha:
        refuse(f"the live build-stamp capture names commit {live.get('commit')}, not {taken.sha}")
    inputs = {"schema": STABLE_SCHEMA, "sha": taken.sha, "content_digest": identity["content_digest"],
              "declared_inputs": identity["inputs"], "consumed_count": identity["consumed_count"],
              "helper_sums_sha256": sha256_of(taken.helper_sums) if taken.helper_sums else None}
    stability = "first record"
    if taken.stable is not None:
        if os.path.exists(taken.stable):
            held = json.load(open(taken.stable))
            differences = [name for name in ("sha", "content_digest", "declared_inputs", "consumed_count", "helper_sums_sha256")
                           if held.get(name) != inputs[name]]
            if differences:
                refuse(f"the qualification inputs drifted since {taken.stable} was recorded: {differences} differ "
                       f"(recorded digest {str(held.get('content_digest'))[:16]}, now {inputs['content_digest'][:16]}); nothing after this runs")
            stability = f"stable since {held.get('recorded_at')}"
        else:
            inputs["recorded_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            with open(taken.stable, "x", encoding="utf-8") as writing:
                json.dump(inputs, writing, indent=1, sort_keys=True)
                writing.write("\n")
    helper = []
    if taken.helper_sums:
        helper = [one.split(maxsplit=1)[1].lstrip("*") for one in open(taken.helper_sums).read().splitlines() if one.strip()]
        helper = [os.path.relpath(os.path.join(taken.repo, one), taken.repo) if not os.path.isabs(one) else os.path.relpath(one, taken.repo) for one in helper]
        helper.append(os.path.relpath(taken.helper_sums if os.path.isabs(taken.helper_sums) else os.path.join(os.getcwd(), taken.helper_sums), taken.repo))
    lines = observe(taken.repo)
    entries = classify(lines, taken.sha[:8], identity["inputs"], helper)
    inventory = {"schema": SCHEMA, "sha": taken.sha, "observed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                 "observation": "git status --porcelain --untracked-files=normal (the build stamp's own); informational, not a gate",
                 "entries": entries, "inputs": inputs, "inputs_stability": stability, "live_capture": live}
    if taken.stamp is not None:
        stamp = json.load(open(taken.stamp))
        inventory["recorded_stamp"] = stamp
        if stamp.get("commit") != taken.sha:
            refuse(f"the recorded stamp names commit {stamp.get('commit')}, not {taken.sha}")
        if stamp.get("dirty") is None:
            refuse(f"the recorded stamp carries no observation of the tree: {stamp.get('detail')}")
    if taken.out is not None:
        with open(taken.out, "w", encoding="utf-8") as writing:
            json.dump(inventory, writing, indent=1, sort_keys=True)
            writing.write("\n")
    for one in entries:
        print(f"  {one['status']} {one['path']}  [{one['class']}]")
    said = (f"inputs ok at {taken.sha[:8]}: v12/ clean, {identity['consumed_count']} consumed file(s) of "
            f"{len(identity['inputs'])} declared input(s) committed, content digest {identity['content_digest'][:16]} ({stability}); "
            f"live capture dirty={live.get('dirty')} changed_entries={live.get('changed_entries')} excused={live.get('excused_build_output')}; "
            f"{len(entries)} dirty path(s) inventoried, none an input")
    if taken.stamp is not None:
        said += f"; recorded stamp {os.path.basename(taken.stamp)} at {stamp['commit'][:8]} dirty={stamp['dirty']} changed_entries={stamp.get('changed_entries')} kept as captured"
    print(said)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
