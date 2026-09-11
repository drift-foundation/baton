"""Focused probe: does the standalone profile really reconcile and advance?"""
import json, os, subprocess, sys, tempfile

sys.path.insert(0, "/home/sl/src/baton/v12/python/src")
from baton_v12.integration.git_profile import (GitIntegrationProfile,
                                               IntegrationProfileRefusal)

ENV = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "HOME": "/tmp",
       "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_SYSTEM": os.devnull,
       "GIT_TERMINAL_PROMPT": "0", "GIT_AUTHOR_NAME": "T",
       "GIT_AUTHOR_EMAIL": "t@x.invalid", "GIT_COMMITTER_NAME": "T",
       "GIT_COMMITTER_EMAIL": "t@x.invalid"}


def runner(argv):
    a = subprocess.run(list(argv), capture_output=True, text=True, env=ENV,
                       timeout=120)
    return {"returncode": a.returncode, "stdout": a.stdout, "stderr": a.stderr}


def g(place, *args):
    a = runner(["git", "-C", place] + list(args))
    assert a["returncode"] == 0, (args, a["stderr"])
    return a["stdout"].strip()


def w(place, name, body):
    with open(os.path.join(place, name), "w") as handle:
        handle.write(body)


root = tempfile.mkdtemp(prefix="p-profile-")
answers = {}

# the dedicated target, with its own configured reference
target = os.path.join(root, "target")
os.makedirs(target)
g(target, "init", "-q", "-b", "main")
w(target, "harness.py", "print('base')\n")
w(target, "other.py", "print('other base')\n")
g(target, "add", "--all"); g(target, "commit", "-q", "-m", "base")
base = g(target, "rev-parse", "HEAD")
REFERENCE = "refs/baton/integration/target"
g(target, "update-ref", REFERENCE, base)

# Job B's ORIGINAL submission, on the ORIGINAL base -- never rebased
line = os.path.join(root, "line-b")
assert runner(["git", "clone", "-q", target, line])["returncode"] == 0
g(line, "checkout", "-q", "--detach", base)
w(line, "other.py", "print('the second job answered')\n")
g(line, "add", "--all"); g(line, "commit", "-q", "-m", "job b")
candidate = g(line, "rev-parse", "HEAD")

# Job A integrates first: the dedicated target's reference advances
w(target, "harness.py", "print('the first job answered')\n")
g(target, "add", "--all"); g(target, "commit", "-q", "-m", "job a")
advanced = g(target, "rev-parse", "HEAD")
g(target, "update-ref", REFERENCE, advanced, base)

storage = os.path.join(root, "prep")
os.makedirs(storage)
g(storage, "init", "-q", "--bare")
profile = GitIntegrationProfile(runner)

held = profile.prepare(storage, result_id="result-b1", base=base,
                       candidate=candidate, target=advanced,
                       candidate_source=line, target_source=target)
answers["state"] = held["state"]
prepared = held["prepared"]
answers["based_on_the_snapshot"] = prepared["base"] == advanced
answers["content"] = prepared["content"]
combined = prepared["head"]
answers["both_changes"] = [
    g(storage, "show", combined + ":other.py"),
    g(storage, "show", combined + ":harness.py")]
answers["submission_untouched"] = g(line, "rev-parse", "HEAD") == candidate
answers["replay_identical"] = profile.prepare(
    storage, result_id="result-b1", base=base, candidate=candidate,
    target=advanced, candidate_source=line,
    target_source=target)["prepared"] == prepared

# the target advance is a compare-and-swap from the REVIEWED revision
assert runner(["git", "-C", target, "fetch", "--no-tags", storage,
               combined])["returncode"] == 0
answers["target_before"] = profile.revision(target, REFERENCE)
answers["advanced_to"] = profile.advance(target, reference=REFERENCE,
                                         imported=combined, reviewed=advanced)
try:
    profile.advance(target, reference=REFERENCE, imported=advanced,
                    reviewed=base)
    answers["stale_swap"] = "ACCEPTED -- unexpected"
except IntegrationProfileRefusal as refusal:
    answers["stale_swap"] = f"refused: {str(refusal)[:90]}"

# a real conflict holds and writes nothing
line_c = os.path.join(root, "line-c")
assert runner(["git", "clone", "-q", target, line_c])["returncode"] == 0
g(line_c, "checkout", "-q", "--detach", base)
w(line_c, "harness.py", "print('the third job edited the same line')\n")
g(line_c, "add", "--all"); g(line_c, "commit", "-q", "-m", "job c")
conflicting = g(line_c, "rev-parse", "HEAD")
conflict = profile.prepare(storage, result_id="result-c1", base=base,
                           candidate=conflicting, target=advanced,
                           candidate_source=line_c, target_source=target)
answers["conflict_state"] = conflict["state"]
answers["conflict_paths"] = conflict.get("conflicts")
answers["conflict_retained_nothing"] = "result-c1" not in g(
    storage, "for-each-ref", "--format=%(refname)", "refs/baton/")

print(json.dumps(answers, indent=2))
ok = (answers["state"] == "prepared" and answers["based_on_the_snapshot"]
      and answers["both_changes"] == ["print('the second job answered')",
                                      "print('the first job answered')"]
      and answers["submission_untouched"] and answers["replay_identical"]
      and answers["advanced_to"] == combined
      and answers["stale_swap"].startswith("refused")
      and answers["conflict_state"] == "held"
      and answers["conflict_paths"] == ["harness.py"]
      and answers["conflict_retained_nothing"])
print("\nPROFILE:", "OK" if ok else "NOT OK")
sys.exit(0 if ok else 1)
