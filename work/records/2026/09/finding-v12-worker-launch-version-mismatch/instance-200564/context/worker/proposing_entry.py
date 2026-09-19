"""The fixture image's entrypoint: W6633's worker, THIS image's agent.

W197661 claim200000, and it exists because of a defect review199914 found in
what I shipped one claim earlier. `Dockerfile.fixture` copied
`proposing_agent.py` into the image and then entered `baton_worker.py`
directly -- so `main` saw `agent=None`, took the `_scripted_default()` branch,
and imported `scripted_agent.ScriptedAgent`, the ORIGINAL fixture that writes
`result_metadata: {}`. The new agent travelled in the image and nothing ever
selected it. **Copying a module is not composing with it**, and the built
artefact still emitted exactly the empty metadata the claim said was fixed.

THE PATTERN IS THE ACCEPTED ONE, deliberately: `dogfood_entry.py` is the
provider image's entrypoint and does the same single thing for the same reason.
One line of composition, in a file, rather than a shell incantation in the
recipe -- so the injection is an artefact a reviewer can read and a case can
import, and so `ENTRYPOINT` stays exec-form with no shell in the process tree.

WHAT IT DOES NOT DO is the whole point. It does not reimplement `main`, does not
wrap it, does not read the launch document, and does not touch the framing:
`baton_worker.main(agent=...)` is the documented injection seam and this uses
exactly that. A fixture image with its own serve loop would be a second
worker-entry implementation nobody reviewed.

AND THE IMAGE NO LONGER CARRIES `scripted_agent.py`. Two agents in one image,
one of them selected by a branch nobody reads, is precisely the arrangement that
produced this defect. `_scripted_default` is now unreachable here because the
module it imports is absent -- so a future recipe that drops this entrypoint
fails loudly at import rather than quietly running the wrong agent.
"""

import sys

from baton_worker import main
from proposing_agent import ProposingAgent

if __name__ == "__main__":
    sys.exit(main(agent=ProposingAgent()))
