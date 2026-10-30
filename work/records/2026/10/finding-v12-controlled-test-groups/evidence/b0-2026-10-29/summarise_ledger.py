"""W384870 B0 — summarise a test-all ledger (the --summary JSON) per group and module.

Usage: python3 -I summarise_ledger.py test-all.summary.json [module-registry.tsv]
Reads only; prints a Markdown table of collected / passed / failed / errors /
skipped per group and the failing modules with counts. Pure evidence tooling.
"""
import collections
import json
import pathlib
import sys

GROUP_MODULES = {
    "manager-engine": {"tests.manager.test_worker_container", "tests.manager.test_failed_start_destroy_engine",
                       "tests.manager.test_oci_engine", "tests.manager.test_lifecycle_composition",
                       "tests.manager.test_negative_race_endings", "tests.manager.test_ended_runtime_adoption",
                       "tests.manager.test_output_custody_engine", "tests.manager.test_credentials_engine",
                       "tests.manager.test_refused_session_engine", "tests.manager.test_custody_engine",
                       "tests.manager.test_input_delivery", "tests.manager.test_worker_entry_engine",
                       "tests.manager.test_dogfood_image", "tests.manager.test_abandoned_attempt_engine",
                       "tests.manager.test_private_line_access_engine", "tests.tools.test_dogfood_arc_engine",
                       "tests.tools.test_dogfood_retry_engine"},
    "supervised": {"tests.manager.test_runtime_deadline_engine"},
    "scans": {"tests.manager.test_boundary_inventory", "tests.manager.test_dependencies",
              "tests.manager.test_contracts_inventory", "tests.manager.test_text_sweep",
              "tests.manager.test_source_boundary"},
    "tools-packaged": {"tests.tools.test_packaging", "tests.tools.test_packaged_creation"},
}
PACKAGES = {"tests.authority": "authority", "tests.job_manager": "job_manager", "tests.integration": "integration",
            "tests.manager": "manager-pure", "tests.tools": "tools-pure"}


def module_of(test_id):
    text = test_id.split(" (")[0]
    parts = text.split(".")
    if len(parts) >= 2 and parts[-2][:1].isupper():
        return ".".join(parts[:-2])
    return ".".join(parts[:-1])


def group_of(module):
    for name, modules in GROUP_MODULES.items():
        if module in modules:
            return name
    return PACKAGES.get(module.rsplit(".", 1)[0], "?")


def main(path):
    ledger = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    per_group = collections.defaultdict(lambda: collections.Counter())
    per_module = collections.defaultdict(lambda: collections.Counter())
    for key in ("collected", "passed", "failed", "errors", "unaccounted"):
        for one in ledger.get(key, []):
            module = module_of(one)
            per_group[group_of(module)][key] += 1
            per_module[module][key] += 1
    for key in ("optional_skipped", "required_skipped"):
        for one in ledger.get(key, {}):
            module = module_of(one)
            per_group[group_of(module)][key] += 1
            per_module[module][key] += 1
    print("| group | collected | passed | failed | errors | optional skip | required skip | unaccounted |")
    print("|---|---|---|---|---|---|---|---|")
    for group in ("authority", "job_manager", "manager-pure", "manager-engine", "integration", "tools-pure",
                  "tools-packaged", "supervised", "scans"):
        c = per_group[group]
        print(f"| {group} | {c['collected']} | {c['passed']} | {c['failed']} | {c['errors']} | "
              f"{c['optional_skipped']} | {c['required_skipped']} | {c['unaccounted']} |")
    total = collections.Counter()
    for c in per_group.values():
        total.update(c)
    print(f"| total | {total['collected']} | {total['passed']} | {total['failed']} | {total['errors']} | "
          f"{total['optional_skipped']} | {total['required_skipped']} | {total['unaccounted']} |")
    print()
    print("| module | failed | errors | required skip | unaccounted |")
    print("|---|---|---|---|---|")
    rows = [(m, c) for m, c in per_module.items() if c["failed"] or c["errors"] or c["required_skipped"] or c["unaccounted"]]
    for module, c in sorted(rows, key=lambda item: (-(item[1]["failed"] + item[1]["errors"] + item[1]["unaccounted"]), item[0])):
        print(f"| {module} | {c['failed']} | {c['errors']} | {c['required_skipped']} | {c['unaccounted']} |")
    print()
    print("stray errors (not collected ids, e.g. setUpClass):", len(ledger.get("stray_errors", [])))
    print("duplicates:", len(ledger.get("duplicates", [])), "uncollected:", len(ledger.get("uncollected", [])),
          "ok:", ledger.get("ok"))


if __name__ == "__main__":
    main(sys.argv[1])
