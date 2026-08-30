"""The dogfood image's entrypoint: W6633's worker, this image's agent.

W39357. One line of composition, in a file, rather than a shell incantation in
the recipe -- so the injection is an artefact a reviewer can read and a case
can import, and so `ENTRYPOINT` stays exec-form with no shell in the process
tree.

WHAT IT DOES NOT DO is the whole point. It does not reimplement `main`, does
not wrap it, does not read the launch document, and does not touch the
framing: `baton_worker.main(agent=...)` is the documented seam and this uses
exactly that. A dogfood image that had its own serve loop would be a second
worker-entry implementation nobody reviewed.
"""

import sys

from baton_worker import main
from claude_agent import ClaudeAgent

if __name__ == "__main__":
    sys.exit(main(agent=ClaudeAgent()))
