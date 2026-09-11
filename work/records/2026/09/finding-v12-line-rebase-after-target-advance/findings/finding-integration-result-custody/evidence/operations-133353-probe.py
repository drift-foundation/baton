"""Focused control: evidence, derived publication (REAL Authority), import."""
import json, os, subprocess, sys, tempfile

sys.path.insert(0, "/home/sl/src/baton/v12/python/src")
from baton_v12.authority import Authority
from baton_v12.contracts import ContractRefusal
from baton_v12.integration import IntegrationStore, TARGET_SCHEMA, activate_target
from baton_v12.integration.git_profile import GitIntegrationProfile
from baton_v12.integration import reconciliation as R

NOW = "2026-09-10T04:10:00.000Z"
UUID = "0123456789abcdef0123456789abcdef"
WORK = "0123456f-W2"
TARGET = "target:mainline"
REFERENCE = "refs/baton/integration/target"
INTEGRATOR = "baton.integrator"
ENV = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "HOME": "/tmp",
       "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_SYSTEM": os.devnull,
       "GIT_AUTHOR_NAME": "T", "GIT_AUTHOR_EMAIL": "t@x.invalid",
       "GIT_COMMITTER_NAME": "T", "GIT_COMMITTER_EMAIL": "t@x.invalid"}


def runner(argv):
    a = subprocess.run(list(argv), capture_output=True, text=True, env=ENV,
                       timeout=120)
    return {"returncode": a.returncode, "stdout": a.stdout, "stderr": a.stderr}


def g(place, *args):
    a = runner(["git", "-C", place] + list(args))
    assert a["returncode"] == 0, (args, a["stderr"])
    return a["stdout"].strip()


def w(place, name, body):
    open(os.path.join(place, name), "w").write(body)


root = tempfile.mkdtemp(prefix="p-ops-")
answers = {}

target = os.path.join(root, "target"); os.makedirs(target)
g(target, "init", "-q", "-b", "main")
w(target, "harness.py", "print('base')\n"); w(target, "other.py", "print('o')\n")
g(target, "add", "--all"); g(target, "commit", "-q", "-m", "base")
base = g(target, "rev-parse", "HEAD"); g(target, "update-ref", REFERENCE, base)
line = os.path.join(root, "line")
assert runner(["git", "clone", "-q", target, line])["returncode"] == 0
g(line, "checkout", "-q", "--detach", base)
w(line, "other.py", "print('the second job answered')\n")
g(line, "add", "--all"); g(line, "commit", "-q", "-m", "b")
candidate = g(line, "rev-parse", "HEAD")
w(target, "harness.py", "print('the first job answered')\n")
g(target, "add", "--all"); g(target, "commit", "-q", "-m", "a")
advanced = g(target, "rev-parse", "HEAD")
g(target, "update-ref", REFERENCE, advanced, base)
workspace = os.path.join(root, "work"); os.makedirs(workspace)
g(workspace, "init", "-q", "--bare")
assert runner(["git", "-C", workspace, "fetch", "--no-tags", line,
               candidate])["returncode"] == 0

# a REAL Authority, with the Work in the integrator's hands
authority = Authority.create(os.path.join(root, "authority.sqlite3"),
                             authority_uuid=UUID)
authority.set_policy("canonical_target", base)
authority.create_work(WORK, "integ", contract="v12-assignment-1",
                      operation_id="create-work")
authority.add_route_handler("integ", INTEGRATOR)
session = authority.session(INTEGRATOR)
fixed = session.claim({"work_id": WORK, "operation_id": "claim-1"})["assignment"]

store = IntegrationStore.open(os.path.join(root, "coord.sqlite3"),
                              incarnation="coord-1", clock=lambda: NOW)
activate_target(store, {"schema": TARGET_SCHEMA, "canonical_target_id": TARGET,
                        "description": "the mainline target"})
ws, ts = os.stat(workspace), os.stat(target)
profile = GitIntegrationProfile(runner)
held = R.prepare_result(
    store, profile,
    submission={"authority_uuid": UUID, "work_id": WORK, "job_id": "job-b",
                "line_id": "line-b", "source_checkpoint_id": "checkpoint-b1",
                "source_verdict_id": "verdict-b1",
                "source_proposal_id": "proposal-b1",
                "source_result_id": "result-b1",
                "source_result_digest": "sha256:" + "1" * 64,
                "source_checkpoint_digest": "sha256:" + "2" * 64,
                "source_base": base, "source_candidate": candidate},
    workspace={"path": workspace, "device": ws.st_dev, "inode": ws.st_ino},
    target_source={"path": target, "device": ts.st_dev, "inode": ts.st_ino},
    target_reference=REFERENCE, integration_attempt_id="attempt-i",
    integration_assignment=fixed, canonical_target_id=TARGET)
result_id = held["result_id"]
answers["prepared"] = held["state"]


def evidence(kind, actor, digest_=None):
    return {"kind": kind, "identity": f"{kind}-1", "actor": actor,
            "disposition": {"verification": "passed", "review": "accepted",
                            "approval": "approved"}[kind],
            "content_digest": digest_ or held["content_digest"]}


# -- publishing before evidence refuses -----------------------------------
try:
    R.publish_result(store, session, result_id=result_id,
                     input_digest="sha256:" + "5" * 64,
                     policy_digest="sha256:" + "6" * 64)
    answers["publish_before_evidence"] = "ACCEPTED -- unexpected"
except ContractRefusal as refusal:
    answers["publish_before_evidence"] = f"refused: {refusal.message[:70]}"

# -- evidence about OTHER bytes refuses -----------------------------------
try:
    R.record_result_evidence(
        store, result_id=result_id,
        verification=evidence("verification", "baton.verifier",
                              "sha256:" + "9" * 64),
        review=evidence("review", "baton.reviewer"),
        approval=evidence("approval", "baton.approver"))
    answers["foreign_evidence"] = "ACCEPTED -- unexpected"
except ContractRefusal as refusal:
    answers["foreign_evidence"] = f"refused: {refusal.message[:64]}"

# -- one actor giving two judgements refuses ------------------------------
try:
    R.record_result_evidence(
        store, result_id=result_id,
        verification=evidence("verification", "baton.same"),
        review=evidence("review", "baton.same"),
        approval=evidence("approval", "baton.approver"))
    answers["same_actor"] = "ACCEPTED -- unexpected"
except ContractRefusal as refusal:
    answers["same_actor"] = f"refused: {refusal.message[:60]}"

# -- the real thing --------------------------------------------------------
authorized = R.record_result_evidence(
    store, result_id=result_id,
    verification=evidence("verification", "baton.verifier"),
    review=evidence("review", "baton.reviewer"),
    approval=evidence("approval", "baton.approver"))
answers["authorized"] = authorized["state"]

published = R.publish_result(store, session, result_id=result_id,
                             input_digest="sha256:" + "5" * 64,
                             policy_digest="sha256:" + "6" * 64)
answers["published"] = published["state"]
proposal = authority.proposal(published["derived_proposal_id"])
answers["derived_names_integration_assignment"] = (
    proposal["assignment_ref"] == fixed)
answers["derived_target_is_the_snapshot"] = proposal["target"] == advanced
answers["derived_candidate_is_the_combined"] = (
    proposal["candidate_digest"] == held["prepared"]["head"])
answers["derived_result_is_its_own"] = (
    proposal["result_id"] == published["derived_result_id"] != "result-b1")
answers["publish_retry_identical"] = R.publish_result(
    store, session, result_id=result_id, input_digest="sha256:" + "5" * 64,
    policy_digest="sha256:" + "6" * 64) == published

account = R.resolve_import_account(store, profile, result_id=result_id)
answers["import_account"] = {
    "expected_target_revision": account["expected_target_revision"] == advanced,
    "source_proposal_kept": account["source_proposal_id"] == "proposal-b1",
    "derived_proposal": account["derived_proposal_id"]
    == published["derived_proposal_id"],
    "content": sorted(account["content"])}

# -- and a target that moved AGAIN refuses the import ---------------------
w(target, "third.py", "print('a third job')\n")
g(target, "add", "--all"); g(target, "commit", "-q", "-m", "c")
moved = g(target, "rev-parse", "HEAD")
g(target, "update-ref", REFERENCE, moved, advanced)
try:
    R.resolve_import_account(store, profile, result_id=result_id)
    answers["stale_result"] = "ACCEPTED -- unexpected"
except ContractRefusal as refusal:
    answers["stale_result"] = f"refused: {refusal.message[:64]}"

store.close(); authority.dispose()
print(json.dumps(answers, indent=2))
ok = (answers["prepared"] == "prepared"
      and answers["publish_before_evidence"].startswith("refused")
      and answers["foreign_evidence"].startswith("refused")
      and answers["same_actor"].startswith("refused")
      and answers["authorized"] == "authorized"
      and answers["published"] == "published"
      and answers["derived_names_integration_assignment"]
      and answers["derived_target_is_the_snapshot"]
      and answers["derived_candidate_is_the_combined"]
      and answers["derived_result_is_its_own"]
      and answers["publish_retry_identical"]
      and all(v for k, v in answers["import_account"].items() if k != "content")
      and answers["stale_result"].startswith("refused"))
print("\nOPERATIONS:", "OK" if ok else "NOT OK")
sys.exit(0 if ok else 1)
