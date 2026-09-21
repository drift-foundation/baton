"""Prove the SELECTED image emits task-derived output, two successive tasks.

Review219927: the corrected `ProposingAgent` derives its candidate from
`task_id`, but the composer selected the immutable historical images -- so
the correction existed in source and in no artefact anything launches. This
proof runs THE IMAGE ITSELF (the digest the composer now pins), not the
checkout: two `work` turns with distinct task ids, the SECOND on a line
whose head IS the first turn's output -- the exact successive-Job shape that
faulted installed (verification-3 staged nothing at a base already carrying
the fixed file).

RUNS ENTIRELY INSIDE THE CONTAINER under its own fixed uid: the line is
created here, the fixture's own `git` acts on it, and nothing outside the
mounted staging directory is read or written. Run it with:

    docker run --rm --network none --entrypoint python3 \
      -v <staging>:/work -e HOME=/work <image digest> \
      /work/test-image-task-derivation-219950.py

It exits nonzero with a named reason on any miss; its stdout is the record.
"""
import json
import os
import subprocess
import sys

sys.path.insert(0, "/opt/baton")
from proposing_agent import ProposingAgent  # noqa: E402  (image-side module)

LINE = "/work/line"
GIT = ["git", "-c", "user.name=w202663-proof", "-c",
       "user.email=proof@w202663", "-C", LINE]


def ran(*arguments):
    answer = subprocess.run([*GIT[:1], *GIT[1:], *arguments],
                            capture_output=True, text=True, timeout=60)
    if answer.returncode != 0:
        sys.exit(f"git {' '.join(arguments)} failed: {answer.stderr[:300]}")
    return answer.stdout.strip()


def turn(number, task_id):
    """One `work` turn of the image's own agent over the line."""
    inputs = f"/work/inputs-{number}"
    os.makedirs(inputs, exist_ok=True)
    with open(os.path.join(inputs, "task.json"), "w") as out:
        json.dump({"schema": "baton.dogfood-task/2", "task_id": task_id,
                   "source_root": "source", "source_profile": "git-line",
                   "declared_base": ran("rev-parse", "HEAD")}, out)
    agent = ProposingAgent(root=LINE, inputs=inputs)
    answer = agent.work(
        {"role": "implementation"},
        [{"name": "proposal", "path": f"proposal-{number}",
          "type": "git-change-proposal"}])
    if answer.get("disposition") != "completed":
        sys.exit(f"turn {number} did not complete: {answer}")
    return answer


os.makedirs(LINE, exist_ok=True)
ran("init", "-q", ".")
ran("commit", "-q", "--allow-empty", "-m", "R0: the empty base")

first = turn(1, "proof-task-1")
first_head = ran("rev-parse", "HEAD")
first_files = ran("show", "--name-only", "--format=", "HEAD").split()

# THE SECOND TASK RUNS ON THE FIRST OUTPUT: HEAD already carries task 1's
# candidate, which is exactly where the fixed-name fixture staged nothing.
second = turn(2, "proof-task-2")
second_head = ran("rev-parse", "HEAD")
second_files = ran("show", "--name-only", "--format=", "HEAD").split()

expected = {"proof-task-1": "w197661-fixture-proof-task-1.txt",
            "proof-task-2": "w197661-fixture-proof-task-2.txt"}
if first_files != [expected["proof-task-1"]]:
    sys.exit(f"turn 1 committed {first_files}, not the task-derived file")
if second_files != [expected["proof-task-2"]]:
    sys.exit(f"turn 2 committed {second_files}, not the task-derived file")
if first_head == second_head:
    sys.exit("the second turn moved nothing")
if ran("rev-parse", "HEAD~1") != first_head:
    sys.exit("the second commit is not based on the first output")
for task_id, name in expected.items():
    with open(os.path.join(LINE, name)) as reading:
        held = reading.read()
    want = f"w197661 deterministic fixture candidate for {task_id}\n"
    if held != want:
        sys.exit(f"{name} holds {held!r}, not the task-derived line")

print(json.dumps({
    "proof": "task-derived-output-for-successive-distinct-tasks",
    "turn_1": {"task_id": "proof-task-1", "head": first_head,
               "committed": first_files},
    "turn_2": {"task_id": "proof-task-2", "head": second_head,
               "based_on": first_head, "committed": second_files},
    "both_lines_exact": True}, indent=1))
