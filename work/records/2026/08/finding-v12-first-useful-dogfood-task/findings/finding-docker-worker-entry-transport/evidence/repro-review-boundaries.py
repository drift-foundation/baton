"""Read-only reproductions for W39356's first independent review.

Run from v12/python with PYTHONPATH=src. The script exits non-zero once both
review findings are fixed; its assertions describe the current, rejected
behaviour rather than the desired contract.
"""

import json

from baton_v12.worker_manager.oci import exec_vector
from baton_v12.worker_manager.worker_entry import ChannelPort, PROTOCOL, converse


def framed(document):
    body = json.dumps(document).encode("utf-8")
    return str(len(body)).encode("ascii") + b"\n" + body


class LateSurplus:
    """Return the correlated answer first and surplus on the next read."""

    def __init__(self):
        self.parts = [
            framed({
                "protocol": PROTOCOL,
                "session": "session-1",
                "operation_id": "operation-1",
                "ok": True,
                "answer": {
                    "protocol": PROTOCOL,
                    "operations": ["describe", "work"],
                    "launch": ["contract", "role", "schema", "session"],
                },
            }),
            framed({
                "protocol": PROTOCOL,
                "session": "session-1",
                "operation_id": "unsolicited",
                "ok": True,
                "answer": {
                    "protocol": PROTOCOL,
                    "operations": ["describe", "work"],
                    "launch": ["contract", "role", "schema", "session"],
                },
            }),
        ]

    def send(self, payload):
        pass

    def receive(self, count):
        return self.parts.pop(0) if self.parts else b""

    def finish(self):
        return {"status": 0, "stderr": ""}


split = exec_vector("docker", runtime_id="runtime-1", program="python3")
assert split[-7:] == list("python3"), split
print("scalar program accepted as argv characters:", split)

channel = LateSurplus()
answer = converse(
    ChannelPort(lambda argv, *, seconds: channel),
    engine="docker",
    runtime_id="runtime-1",
    program=["python3", "/opt/baton/baton_worker.py"],
    session="session-1",
    operations=["describe"],
    operation_ids=["operation-1"],
    seconds=30,
)
assert answer["ending"] == "answered", answer
assert channel.parts, "the surplus frame was consumed"
print("late surplus accepted as answered; unread frames:", len(channel.parts))
