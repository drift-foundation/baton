"""Show that worker-entry operation ids fence one exec session, not a restart.

Run from ``v12/python`` with ``PYTHONPATH=src:.``.  Two independent worker
entry processes receive the same launched-session and operation identities.
The shared counting agent proves that both ``work`` requests reach it.
"""

import json
import unittest

from tests.manager.test_worker_entry import LiveWorker, launch_document, spoken
from tests.manager.test_worker_image import DECLARATION, staged
from scripted_agent import ScriptedAgent


class CountingAgent(ScriptedAgent):
    def __init__(self):
        self.work_calls = 0

    def work(self, seen, declared):
        self.work_calls += 1
        return super().work(seen, declared)


def main():
    case = unittest.TestCase()
    agent = CountingAgent()
    try:
        place = launch_document(case)
        staged(case, [dict(DECLARATION)])
        conversations = [
            spoken(case, LiveWorker(agent, place), ["describe", "work"],
                   ["describe:attempt-1", "work:attempt-1"])
            for _ in range(2)
        ]
        print(json.dumps({
            "endings": [one["ending"] for one in conversations],
            "answered": [[answer["operation"] for answer in one["answers"]]
                         for one in conversations],
            "work_calls": agent.work_calls,
        }, sort_keys=True))
    finally:
        case.doCleanups()


if __name__ == "__main__":
    main()
