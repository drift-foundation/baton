"""W384870 B0 — reconcile attempt 3's ledger from RETAINED evidence, without a rerun.

The first ledger (test-all.summary.json) trusted each shard's loaded plan as
"executed", so tests whose class fixture skipped or errored (never started) were
counted as passed, and every `setUpClass (...)` skip collapsed into one key.
This script re-derives the never-started ids from two retained facts:
  * the log's per-shard line `[pass|FAIL] <label> (<N> tests)` = tests that RAN,
  * the ledger's collected ids, grouped by shard label (class, or module for
    serial shards, or the single method for method-split shards).
Where a shard ran fewer tests than its collected ids and recorded no per-id
outcome for the difference, those ids never started. Output: a reconciled
ledger beside the original and a Markdown account. Reads only.
"""
import collections
import json
import pathlib
import re
import sys

E = pathlib.Path(__file__).resolve().parent
log = (E / "test-all.log").read_text(encoding="utf-8", errors="replace")
ledger = json.loads((E / "test-all.summary.json").read_text(encoding="utf-8"))
sys.path.insert(0, str(E.parents[6] / "v12" / "python"))
from tools.parallel_test import METHOD_SPLIT, SERIAL_MODULES, SUPERVISED_MODULES  # noqa: E402
MODULE_SHARDS = set(SERIAL_MODULES) | {entry["module"] for entry in SUPERVISED_MODULES}

ran = {}
for m in re.finditer(r"^\[(?:pass|FAIL)\] (\S+) \((\d+) tests\)$", log, re.M):
    ran[m.group(1)] = int(m.group(2))

def label_of(test_id):
    module = ".".join(test_id.split(".")[:3])
    if module in MODULE_SHARDS:
        return module
    cls = test_id.rsplit(".", 1)[0]
    return test_id if cls in METHOD_SPLIT else cls

by_label = collections.defaultdict(list)
for one in ledger["collected"]:
    by_label[label_of(one)].append(one)
outcomes = set(ledger["failed"]) | set(ledger["errors"]) | set(ledger["required_skipped"]) | set(ledger["optional_skipped"])
never_started = []
short = []
for label, ids in sorted(by_label.items()):
    if label not in ran:
        raise SystemExit(f"no shard line for {label}")
    missing = len(ids) - ran[label]
    if missing > 0:
        candidates = [one for one in ids if one not in outcomes]
        # For a class shard every candidate never started. For a serial MODULE
        # shard the never-started tests are the classes whose fixture skipped;
        # name them through the podman-class list the audit established.
        short.append((label, len(ids), ran[label], missing, len(candidates)))
        never_started.extend(candidates if len(candidates) == missing else [])
podman = json.loads((E / "podman-classes.json").read_text()) if (E / "podman-classes.json").exists() else []
unresolved = [row for row in short if row[3] != row[4]]
if unresolved and podman:
    for label, n_ids, n_ran, missing, _ in unresolved:
        chosen = [one for one in by_label[label] if any(one.startswith(cls + ".") for cls, _ in podman)]
        if len(chosen) != missing:
            raise SystemExit(f"cannot resolve never-started ids for {label}: {missing} missing, {len(chosen)} podman ids")
        never_started.extend(chosen)
passed = sorted(set(ledger["passed"]) - set(never_started))
reconciled = dict(ledger, passed=passed, unaccounted=sorted(never_started),
                  note="reconciled from retained evidence; see RECONCILIATION.md")
(E / "test-all.reconciled.summary.json").write_text(json.dumps(reconciled, indent=1, sort_keys=True) + "\n")
lines = ["# Reconciliation of attempt 3 (B0 baseline) — from retained evidence, no rerun", "",
         f"Shards that ran fewer tests than they collected: {len(short)}", "",
         "| shard label | collected | ran | never started |", "|---|---|---|---|"]
for label, n_ids, n_ran, missing, _ in short:
    lines.append(f"| {label} | {n_ids} | {n_ran} | {missing} |")
lines += ["", f"Never-started test ids: {len(never_started)} (listed in test-all.reconciled.summary.json `unaccounted`)",
          f"Original ledger: passed {len(ledger['passed'])}, unaccounted {len(ledger['unaccounted'])}",
          f"Reconciled: passed {len(passed)}, unaccounted {len(never_started)}, "
          f"failed {len(ledger['failed'])}, errors {len(ledger['errors'])}, optional skipped {len(ledger['optional_skipped'])}, "
          f"required skipped (per-test) {len([k for k in ledger['required_skipped'] if not k.startswith('setUpClass')])}, "
          f"collected {len(ledger['collected'])}",
          f"Check: passed + optional + required-per-test + failed + errors + never-started = "
          f"{len(passed) + len(ledger['optional_skipped']) + len([k for k in ledger['required_skipped'] if not k.startswith('setUpClass')]) + len(ledger['failed']) + len(ledger['errors']) + len(never_started)}"]
(E / "RECONCILIATION.md").write_text("\n".join(lines) + "\n")
print("\n".join(lines))
