"""The EMITTING deterministic producer agent. W202663 claim208916.

WHY IT EXISTS, in review208890's words: "Repeating a silent fixture cannot
satisfy nonempty retained logs." The capture chain was proven twice with
every stream absent because `ProposingAgent` prints nothing, so the tee in
`baton_worker._WorkerCapture` had nothing to retain. This agent is
`ProposingAgent` -- the same reviewed candidate production, unchanged and
composed rather than copied -- plus deterministic prose printed to the
wrapper's stdout AND stderr around each turn, which is exactly the scope the
tee retains ("the ordinary prose a wrapper prints ... what previously
vanished with the container").

FIXTURE OUTPUT, NOT PROVIDER EVIDENCE. Every line carries the marker below
and says in words that no provider was entered. Capture proof made with this
image establishes that the deployment retains nonempty worker streams; it
establishes nothing about a live provider's native session files, which stay
a separate, later proof.

DETERMINISTIC ON PURPOSE. The lines are fixed strings plus the delegate's own
answer fields -- no clock, no randomness, no environment -- so two runs of one
assignment emit identical bytes and the capture assertion can require exact
content rather than mere nonemptiness.
"""

import sys

from proposing_agent import ProposingAgent

__all__ = ["EmittingAgent", "MARK"]

MARK = "w202663-emitting-fixture"


class EmittingAgent:
    """`ProposingAgent` with a voice. Same turns, same candidate, same claims."""

    def __init__(self):
        self._within = ProposingAgent()

    def consider(self, seen, request):
        print(f"{MARK}: consider begins; deterministic fixture, no provider "
              f"entered, no credential read", flush=True)
        print(f"{MARK}: stderr is retained too; this line proves it",
              file=sys.stderr, flush=True)
        answered = self._within.consider(seen, request)
        print(f"{MARK}: consider ends decision="
              f"{answered.get('decision')}", flush=True)
        return answered

    def work(self, seen, declared):
        print(f"{MARK}: work begins on the frozen task", flush=True)
        answered = self._within.work(seen, declared)
        print(f"{MARK}: work ends disposition="
              f"{answered.get('disposition')}", flush=True)
        print(f"{MARK}: work stderr closing line", file=sys.stderr, flush=True)
        return answered
