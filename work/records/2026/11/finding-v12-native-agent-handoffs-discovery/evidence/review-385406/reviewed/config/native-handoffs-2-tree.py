"""Classify every dirty path of the checkout before a qualification step, and
hold the build stamp to the truth about them.

W385331 qualification round 5 (M385402). `tools/build_stamp.py` observes the
WHOLE repository (`git status --porcelain --untracked-files=normal`) and calls
the tree dirty for any non-generated entry, which is right: the qualification's
own `bind` step writes untracked records under the pilot dossier, so a bundle
built after it truthfully carries `dirty: true` while `v12/` is clean. This
tool does not argue with the stamp. It takes the SAME observation, classifies
each entry, and refuses anything that is not a named generated record of this
qualification:

  product        any entry under `v12/`                          -> refuse
  declared-input any entry under a declared consumed input of the
                 test runner (`tools.source_identity --declared`)  -> refuse
  generated      an UNTRACKED (`??`) entry at one of the exact
                 record paths this qualification writes for the
                 bound checkpoint (below)                          -> allowed
  stale          a generated-record path of ANOTHER checkpoint
                 (a previous binding's records)                    -> refuse,
                 naming them: the operator removes or commits them
                 before this checkpoint is qualified
  unclassified   anything else                                     -> refuse

With `--stamp`, the stamp must name the bound commit and be TRUTHFUL about
the inventory: `dirty == (entries > 0)` and `changed_entries == entries`, all
of them generated. A stamp claiming a clean tree over existing records, or
counting entries the inventory does not show, refuses. Nothing here excuses a
dirty product input, and nothing here edits or recomputes a stamp.

    python3 -I native-handoffs-2-tree.py --repo DIR --sha SHA --identity ID.json
                                         [--stamp build-stamp.json] [--out inventory.json]

`--identity` is the document `python -m tools.source_identity --repo DIR
[--declared] v12` printed: its `changed` must be empty (clean `v12/`), its
`inputs` are the declared consumed inputs, and its `content_digest` is
recorded. Read-only on Git.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time

PILOT = "work/records/2026/10/finding-v12-development-coordination-pilot"
SCHEMA = "k.native-handoffs-2-tree-state/1"


def generated_records(sha8):
    """The exact untracked paths this qualification writes for one checkpoint.
    A `--porcelain` listing collapses a wholly untracked directory to its name
    with a trailing slash, so directory records are matched by prefix."""
    files = [f"{PILOT}/config/native-bound-2.json",
             f"{PILOT}/config/native-instance-2-{sha8}.json",
             f"{PILOT}/config/native-installed-task-2-{sha8}.json",
             f"{PILOT}/config/native-workers-2-{sha8}.json"]
    for worker in ("impl-a", "review-a"):
        files += [f"{PILOT}/config/{worker}-2-{sha8}.json",
                  f"{PILOT}/config/{worker}-2-{sha8}-compose.log"]
    prefixes = [f"{PILOT}/evidence/checkpoint-{sha8}-packaging/",
                f"{PILOT}/evidence/worker-image-{sha8}/",
                f"{PILOT}/evidence/native-handoffs-2-qualification/create-"]
    return files, prefixes


def stale_record(path, sha8):
    """A record path of this qualification written for a different checkpoint."""
    for pattern in (r"config/(native-instance|native-installed-task|native-workers|impl-a|review-a)-2-([0-9a-f]{8})(-compose\.log|\.json)$",
                    r"evidence/(checkpoint-([0-9a-f]{8})-packaging|worker-image-([0-9a-f]{8}))/"):
        found = re.search(pattern, path)
        if found:
            seen = [g for g in found.groups() if g and re.fullmatch(r"[0-9a-f]{8}", g)]
            if seen and seen[0] != sha8:
                return True
    return False


def entry_path(line):
    said = line[3:] if len(line) > 3 else ""
    if " -> " in said:
        said = said.split(" -> ", 1)[1]
    said = said.strip()
    if said.startswith('"') and said.endswith('"') and len(said) > 1:
        said = said[1:-1]
    return said


def observe(repo):
    """The exact observation `build_stamp.capture` makes."""
    out = subprocess.run(["git", "-C", repo, "status", "--porcelain", "--untracked-files=normal"],
                         capture_output=True, text=True, check=True,
                         env=dict(os.environ, GIT_OPTIONAL_LOCKS="0"))
    return [one for one in out.stdout.splitlines() if one.strip()]


def classify(lines, sha8, declared):
    files, prefixes = generated_records(sha8)
    entries = []
    for line in lines:
        path = entry_path(line)
        status = line[:2]
        if path.startswith("v12/") or path == "v12":
            kind = "product"
        elif any(path == one or path.startswith(one.rstrip("/") + "/") for one in declared):
            kind = "declared-input"
        elif status == "??" and (path in files or any(path.startswith(p) or path.rstrip("/") + "/" == p for p in prefixes)):
            kind = "generated"
        elif path.startswith(PILOT + "/") and stale_record(path, sha8):
            kind = "stale"
        else:
            kind = "unclassified"
        entries.append({"status": status, "path": path, "class": kind})
    return entries


def refuse(message):
    print("refused: " + message, file=sys.stderr)
    raise SystemExit(2)


def main(argv=None):
    parser = argparse.ArgumentParser(prog="native-handoffs-2-tree")
    parser.add_argument("--repo", required=True)
    parser.add_argument("--sha", required=True)
    parser.add_argument("--identity", required=True)
    parser.add_argument("--stamp", default=None)
    parser.add_argument("--out", default=None)
    taken = parser.parse_args(argv)
    identity = json.load(open(taken.identity))
    if identity["head"] != taken.sha:
        refuse(f"the source identity names HEAD {identity['head']}, not the bound {taken.sha}")
    if identity["changed"]:
        refuse(f"v12/ is not clean: {[one['path'] for one in identity['changed']]}; the product inputs drifted from {taken.sha}")
    lines = observe(taken.repo)
    entries = classify(lines, taken.sha[:8], identity["inputs"])
    bad = [one for one in entries if one["class"] != "generated"]
    inventory = {"schema": SCHEMA, "sha": taken.sha, "observed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                 "observation": "git status --porcelain --untracked-files=normal (the build stamp's own)",
                 "entries": entries, "generated": sum(one["class"] == "generated" for one in entries),
                 "refused": bad, "content_digest": identity["content_digest"],
                 "declared_inputs": len(identity["inputs"]), "consumed_files": identity["consumed_count"]}
    if taken.stamp is not None:
        stamp = json.load(open(taken.stamp))
        inventory["stamp"] = stamp
        if stamp.get("commit") != taken.sha:
            bad.append({"status": "--", "path": taken.stamp, "class": f"stamp names commit {stamp.get('commit')}, not {taken.sha}"})
        elif stamp.get("dirty") is None:
            bad.append({"status": "--", "path": taken.stamp, "class": f"stamp could not observe the tree: {stamp.get('detail')}"})
        elif stamp["dirty"] != bool(entries) or stamp.get("changed_entries", -1) != len(entries):
            bad.append({"status": "--", "path": taken.stamp,
                        "class": f"stamp says dirty={stamp['dirty']} changed_entries={stamp.get('changed_entries')} but the inventory shows {len(entries)} entries; an untruthful stamp is not qualified"})
        inventory["refused"] = bad
    if taken.out is not None:
        with open(taken.out, "w", encoding="utf-8") as writing:
            json.dump(inventory, writing, indent=1, sort_keys=True)
            writing.write("\n")
    for one in entries:
        print(f"  {one['status']} {one['path']}  [{one['class']}]")
    if bad:
        for one in bad:
            if one["class"] not in ("product", "declared-input", "unclassified", "stale"):
                print("  " + one["class"], file=sys.stderr)
        kinds = sorted({one["class"] for one in bad if one["class"] in ("product", "declared-input", "unclassified", "stale")})
        hint = "; stale records of a previous binding are removed or committed by the operator, never by this tool" if "stale" in kinds else ""
        refuse(f"{len(bad)} entr{'y' if len(bad) == 1 else 'ies'} not a generated record of this qualification for {taken.sha[:8]} "
               f"({'/'.join(kinds) or 'untruthful stamp'}{hint}); nothing after this runs")
    truth = "" if taken.stamp is None else f"; stamp {os.path.basename(taken.stamp)} truthful: dirty={stamp['dirty']} changed_entries={stamp['changed_entries']}"
    print(f"tree state ok: v12/ clean at {taken.sha[:8]}, {len(entries)} generated qualification record(s) and nothing else, content digest {identity['content_digest'][:16]}{truth}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
