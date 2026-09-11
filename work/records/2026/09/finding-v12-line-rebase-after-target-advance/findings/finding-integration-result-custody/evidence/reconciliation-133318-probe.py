"""Focused control: intent vs outcome, resume, and reader binding."""
import json, os, subprocess, sys, tempfile

sys.path.insert(0, "/home/sl/src/baton/v12/python/src")
from baton_v12.contracts import ContractRefusal
from baton_v12.integration import IntegrationStore, TARGET_SCHEMA, activate_target
from baton_v12.integration.git_profile import GitIntegrationProfile
from baton_v12.integration import reconciliation as R

NOW = "2026-09-10T04:00:00.000Z"
UUID = "0" * 31 + "a"
TARGET = "target:mainline"
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


root = tempfile.mkdtemp(prefix="p-recon-")
answers = {}

target = os.path.join(root, "target"); os.makedirs(target)
g(target, "init", "-q", "-b", "main")
w(target, "harness.py", "print('base')\n"); w(target, "other.py", "print('o')\n")
g(target, "add", "--all"); g(target, "commit", "-q", "-m", "base")
base = g(target, "rev-parse", "HEAD")
REFERENCE = "refs/baton/integration/target"
g(target, "update-ref", REFERENCE, base)

line = os.path.join(root, "line"); assert runner(["git", "clone", "-q", target, line])["returncode"] == 0
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
# the workspace holds the submission objects; the profile fetches from it
assert runner(["git", "-C", workspace, "fetch", "--no-tags", line, candidate])["returncode"] == 0

store = IntegrationStore.open(os.path.join(root, "coord.sqlite3"),
                              incarnation="coord-1", clock=lambda: NOW)
activate_target(store, {"schema": TARGET_SCHEMA, "canonical_target_id": TARGET,
                        "description": "the mainline target"})
status = os.stat(workspace)
tstatus = os.stat(target)
submission = {
    "authority_uuid": UUID, "work_id": "0000000a-W2", "job_id": "job-b",
    "line_id": "line-b", "source_checkpoint_id": "checkpoint-b1",
    "source_verdict_id": "verdict-b1", "source_proposal_id": "proposal-b1",
    "source_result_id": "result-b1",
    "source_result_digest": "sha256:" + "1" * 64,
    "source_checkpoint_digest": "sha256:" + "2" * 64,
    "source_base": base, "source_candidate": candidate}
operands = dict(
    submission=submission,
    workspace={"path": workspace, "device": status.st_dev, "inode": status.st_ino},
    target_source={"path": target, "device": tstatus.st_dev, "inode": tstatus.st_ino},
    target_reference=REFERENCE,
    integration_attempt_id="attempt-integration",
    integration_assignment={"work_ref": {"authority_uuid": UUID,
                                         "work_id": "0000000a-W2"},
                            "participant": "baton.integrator", "generation": 4},
    canonical_target_id=TARGET)
profile = GitIntegrationProfile(runner)

# -- 1. an ordinary preparation ------------------------------------------
held = R.prepare_result(store, profile, **operands)
answers["state"] = held["state"]
answers["target_revision_pinned"] = held["target_revision"] == advanced
answers["content"] = held["prepared"]["content"]
combined = held["prepared"]["head"]
answers["both_changes"] = [g(workspace, "show", combined + ":other.py"),
                           g(workspace, "show", combined + ":harness.py")]
answers["submission_untouched"] = g(line, "rev-parse", "HEAD") == candidate
result_id = held["result_id"]

# -- 2. an exact retry replays the settled outcome ------------------------
again = R.prepare_result(store, profile, **operands)
answers["retry_identical"] = again == held

# -- 3. THE RESUME: a committed INTENT with no outcome must call the profile
#       again and finish, not answer "already done".
store._connection.execute("DELETE FROM operations WHERE operation_id = ?",
                          (R.OUTCOME_KIND + ":" + result_id,))
store._connection.execute(
    "UPDATE integration_results SET state = 'preparing', prepared = NULL, "
    "content_digest = NULL, operation_id = ? WHERE result_id = ?",
    (R.INTENT_KIND + ":" + result_id, result_id))
store._connection.commit()
resumed = R.prepare_result(store, profile, **operands)
answers["resume_finishes"] = resumed["state"] == "prepared"
answers["resume_same_target"] = resumed["target_revision"] == advanced
answers["resume_same_content"] = resumed["prepared"] == held["prepared"]

# -- 4. THE READER BINDING: an edited row no longer derives its identity ---
store._connection.execute(
    "UPDATE integration_results SET target_revision = ? WHERE result_id = ?",
    ("e" * 40, result_id))
store._connection.commit()
try:
    R.result_of(store, result_id)
    answers["tampered_row"] = "ACCEPTED -- unexpected"
except ContractRefusal as refusal:
    answers["tampered_row"] = f"refused: {refusal.message[:90]}"
store._connection.execute(
    "UPDATE integration_results SET target_revision = ? WHERE result_id = ?",
    (advanced, result_id))
store._connection.commit()
answers["restored_reads"] = R.result_of(store, result_id)["state"] == "prepared"

# -- 5. a submission already on the target refuses ------------------------
try:
    R.prepare_result(store, profile, **dict(
        operands, submission=dict(submission, source_base=advanced)))
    answers["already_based"] = "ACCEPTED -- unexpected"
except ContractRefusal as refusal:
    answers["already_based"] = f"refused: {refusal.message[:70]}"

store.close()
print(json.dumps(answers, indent=2))
ok = (answers["state"] == "prepared" and answers["target_revision_pinned"]
      and answers["both_changes"] == ["print('the second job answered')",
                                      "print('the first job answered')"]
      and answers["submission_untouched"] and answers["retry_identical"]
      and answers["resume_finishes"] and answers["resume_same_target"]
      and answers["resume_same_content"]
      and answers["tampered_row"].startswith("refused")
      and answers["restored_reads"]
      and answers["already_based"].startswith("refused"))
print("\nRECONCILIATION:", "OK" if ok else "NOT OK")
sys.exit(0 if ok else 1)
