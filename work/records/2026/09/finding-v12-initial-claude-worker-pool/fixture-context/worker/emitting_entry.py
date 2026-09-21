"""The EMITTING fixture image's entrypoint: W6633's worker, THIS image's agent.

W202663 claim208916, the same one-line composition pattern as
`proposing_entry.py` and for the same reviewed reason: `baton_worker.main
(agent=...)` is the documented injection seam, and copying a module is not
composing with it. Nothing else differs from the silent producer image.
"""

import sys

from baton_worker import main
from emitting_agent import EmittingAgent

if __name__ == "__main__":
    sys.exit(main(agent=EmittingAgent()))
