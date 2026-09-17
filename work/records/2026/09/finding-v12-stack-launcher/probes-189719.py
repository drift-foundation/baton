"""W183883 claim189719 -- reversal probes for the fresh-install boundary and its custody.

OWNER-FRESH-INSTALL-20260916.md: an installation starts with zero Jobs and
generates its own Authority identity. These ask whether each guard that makes
that true actually fails when it is removed.

Every probe proves a PASSING BASELINE on pristine code first [J1].

Run against an isolated COPY of the tree. Nothing here edits the checkout, and
nothing here builds, clones, submits a Job or reaches an index.
"""
import json, os, pathlib, shutil, subprocess, sys, time

HERE = pathlib.Path("/home/sl/src/baton/v12")
TREE = pathlib.Path(os.environ.get(
    "W183883_PROBE_TREE", "/tmp/w183883-probes-189719")) / "v12"
SKIP = {".venv", "dist", "build", "__pycache__", ".pytest_cache"}

if TREE.exists():
    shutil.rmtree(TREE)
TREE.parent.mkdir(parents=True, exist_ok=True)
shutil.copytree(HERE, TREE, ignore=shutil.ignore_patterns(*SKIP), symlinks=True)
link = TREE.parent / "work"
if not link.exists():
    os.symlink("/home/sl/src/baton/work", link)

FILES = {"bootstrap": TREE / "python" / "tools" / "bootstrap.py",
         "stage": TREE / "python" / "tools" / "stage_execution.py",
         "guide": TREE / "STACK.md"}
PRISTINE = {place: place.read_text() for place in FILES.values()}

FRESH = "tests.tools.test_bootstrap.AFreshInstallHasZeroJobs."
IDENT = "tests.tools.TheInstanceGeneratesItsOwnIdentity."
IDENTITY = "tests.tools.test_bootstrap.TheInstanceGeneratesItsOwnIdentity."
BLOCKED = "tests.tools.test_bootstrap.TheFreshInstallStillNeedsTheWORKERSToBeSeparable."

PROBES = [
    {"label": "F1-the-emitted-configuration-invents-a-global-work-again",
     "file": "bootstrap",
     "before": '''    built = {
        "schema": chosen,''',
     "after": '''    built = {
        "job_work_id": (jobs or [{"work_id": "invented"}])[0].get("work_id"),
        "review_work_id": (jobs or [{"work_id": "invented"}])[0].get("work_id"),
        "line_declared_base": "invented",
        "canonical_target_id": "invented",
        "schema": chosen,''',
     "checks": [FRESH + "test_the_emitted_configuration_binds_NOTHING_and_says_so"],
     # PROVED NOTHING AS FIRST WRITTEN, and the investigation is the finding.
     # The token was `unexpectedly found` -- my own assertNotIn. The reverted
     # code never reaches it: `prepare` calls the MANAGER's validator, whose
     # closed schema refuses an instance-only document carrying a global Work
     # before the check can look. So the guard is load-bearing one layer down
     # from where I expected, which is the better place for it to be.
     "intended": "carries exactly"},

    {"label": "F2-the-manager-refuses-a-deployment-that-binds-nothing",
     "file": "stage",
     "before": "    if bindings == []:\n        return []\n",
     "after": "",
     "checks": [FRESH + "test_it_is_a_document_the_MANAGER_accepts",
                FRESH + "test_the_emitted_configuration_binds_NOTHING_and_says_so"],
     "intended": "ContractRefusal"},

    {"label": "F3-an-instance-only-document-may-carry-a-global-work-after-all",
     "file": "stage",
     "before": '''                           _INSTANCE_MEMBERS if binds_nothing else _MEMBERS,''',
     "after": '''                           _MEMBERS,''',
     "checks": [FRESH + "test_it_is_a_document_the_MANAGER_accepts"],
     "intended": "carries exactly"},

    {"label": "F4-a-fresh-install-composes-a-placeholder-work-and-grants",
     "file": "bootstrap",
     "before": '    for job in jobs_of(document):\n        held_work = _work(authority, job["work_id"])',
     "after": '    for job in jobs_of(document) or [{"job_id": "placeholder",\n'
              '                                     "work_id": "0000000a-W1"}]:\n'
              '        held_work = _work(authority, job["work_id"])',
     "checks": [FRESH + "test_NO_placeholder_work_job_grant_or_binding_is_composed"],
     "intended": "AssertionError"},

    {"label": "F5-the-identity-is-minted-fresh-every-time",
     "file": "bootstrap",
     "before": "    held = _identity_held(places[\"identity\"])\n    if held is not None:\n        return held, False",
     "after": "    held = None\n    if held is not None:\n        return held, False",
     "checks": [IDENTITY + "test_a_root_that_has_one_KEEPS_it"],
     "intended": "AssertionError"},

    {"label": "F6-two-installations-may-be-one-instance",
     "file": "bootstrap",
     "before": "    return identities.uuid4().hex, True",
     "after": '    return "0" * 31 + "a", True',
     "checks": [IDENTITY + "test_two_installations_are_two_instances"],
     # AND THIS ONE PROVED NOTHING BECAUSE MY TOKEN WAS BACKWARDS:
     # `assertEqual(len(made), 3)` prints the FIRST operand first.
     "intended": "1 != 3"},

    {"label": "F7-the-persisted-identity-is-overwritten-rather-than-refused",
     "file": "bootstrap",
     "before": "        handle = os.open(str(place), os.O_WRONLY | os.O_CREAT | os.O_EXCL\n"
               "                         | os.O_NOFOLLOW, 0o644)",
     "after": "        handle = os.open(str(place), os.O_WRONLY | os.O_CREAT\n"
              "                         | os.O_NOFOLLOW, 0o644)",
     "checks": [IDENTITY + "test_a_racing_second_writer_reads_what_the_first_wrote"],
     "intended": "BootstrapRefusal not raised"},

    {"label": "F8-a-document-may-name-an-authority-again",
     "file": "bootstrap",
     "before": '''SUPERSEDED = {
    "authority_uuid":''',
     "after": '''SUPERSEDED = {
    "authority_uuid_disabled":''',
     "checks": ["tests.tools.test_bootstrap.RepeatingIt."
                "test_a_document_may_not_NAME_an_authority_at_all"],
     "intended": "AssertionError"},

    {"label": "G1-the-identity-read-follows-a-link-again",
     "file": "bootstrap",
     "before": "        handle = os.open(str(place), os.O_RDONLY | os.O_NOFOLLOW)",
     "after": "        handle = os.open(str(place), os.O_RDONLY)",
     "checks": [IDENTITY + "test_a_LINKED_identity_record_is_refused_and_left_alone",
                IDENTITY + "test_a_DANGLING_identity_link_is_not_read_as_absent"],
     "intended": "BootstrapRefusal not raised"},

    {"label": "G2-a-non-regular-identity-record-is-accepted",
     "file": "bootstrap",
     "before": "        if not stat.S_ISREG(held.st_mode):",
     "after": "        if False:",
     "checks": [IDENTITY + "test_an_identity_that_is_not_a_regular_file_is_refused"],
     # PROVED NOTHING AS FIRST WRITTEN, and the investigation is the point.
     # Without the explicit check the reverted code does not ACCEPT the
     # directory -- `os.read` raises IsADirectoryError, which escapes from the
     # middle of `identity()` as an unhandled OSError. That is the whole reason
     # the guard is worth having: an operator gets a sentence about what this
     # root is bound to instead of a traceback.
     "intended": "IsADirectoryError"},

    {"label": "G3-the-identity-name-leaves-destination-custody",
     "file": "bootstrap",
     "before": '''                 "state", "deployment_state", "deployment", "record",
                 "identity", "justfile"):''',
     "after": '''                 "state", "deployment_state", "deployment", "record",
                 "justfile"):''',
     "checks": [IDENTITY + "test_the_identity_is_a_name_the_DESTINATION_owns"],
     "intended": "BootstrapRefusal not raised"},

    {"label": "F9-the-guide-s-minimal-input-drifts-from-what-is-required",
     "file": "guide",
     "before": '  "policy_generation": 1,\n  "receipt_participants"',
     "after": '  "receipt_participants"',
     "checks": [FRESH + "test_the_guides_minimal_block_NAMES_what_is_required_and_no_more"],
     "intended": "policy_generation"},

    {"label": "G4-the-guide-offers-the-member-the-helper-refuses",
     "file": "guide",
     "before": '  "state_root": "/var/lib/baton-v12/deployment",\n  "checkpoint_profile"',
     "after": '  "state_root": "/var/lib/baton-v12/deployment",\n'
              '  "authority_uuid": "<32 lowercase hex>",\n  "checkpoint_profile"',
     "checks": [FRESH + "test_the_guides_minimal_block_NAMES_what_is_required_and_no_more"],
     "intended": "authority_uuid"},
]


def caches():
    for cache in TREE.rglob("__pycache__"):
        shutil.rmtree(cache, ignore_errors=True)


def restore():
    for place, text in PRISTINE.items():
        place.write_text(text)
    caches()


def run(names):
    started = time.monotonic()
    done = subprocess.run(
        [sys.executable, "-B", "-m", "unittest"] + list(names),
        cwd=str(TREE / "python"), capture_output=True, text=True, timeout=900,
        env=dict(os.environ, PYTHONPATH="src:.",
                 BATON_V12_STACK_TEST_ROOT="/var/tmp"))
    return done, time.monotonic() - started


results, spent = [], 0.0
for probe in PROBES:
    restore()
    target = FILES[probe["file"]]
    baseline, base_seconds = run(probe["checks"])
    spent += base_seconds
    text = target.read_text()
    assert probe["before"] in text, probe["label"]
    target.write_text(text.replace(probe["before"], probe["after"], 1))
    caches()
    reverted, seconds = run(probe["checks"])
    spent += seconds
    restore()
    said = reverted.stderr
    intended = probe["intended"] in said
    killed = (baseline.returncode == 0 and reverted.returncode != 0 and intended)
    results.append({
        "probe": probe["label"], "checks": probe["checks"],
        "baseline_passes_on_pristine": baseline.returncode == 0,
        "reverted_returncode": reverted.returncode,
        "failed_on_the_intended_assertion": intended,
        "valid_kill": killed,
        "seconds": round(base_seconds + seconds, 3)})
    if not killed:
        print("---- stderr tail, " + probe["label"] + " ----")
        print(said[-1500:])
    print(("KILL   " if killed else "PROVES NOTHING ") + probe["label"]
          + ("" if baseline.returncode == 0 else "  (NO BASELINE -- INVALID)"))

restore()
restored, restore_seconds = run(["tests.tools.test_bootstrap",
                                 "tests.tools.test_instance"])
spent += restore_seconds
print("restored:", "OK" if restored.returncode == 0 else "BROKEN")
(TREE.parent / "results-189719.json").write_text(json.dumps(
    {"probes": results, "restored_ok": restored.returncode == 0,
     "all_killed": all(one["valid_kill"] for one in results),
     "total_seconds": round(spent, 3)}, indent=2, sort_keys=True))
print("all probes killed:", all(one["valid_kill"] for one in results))
