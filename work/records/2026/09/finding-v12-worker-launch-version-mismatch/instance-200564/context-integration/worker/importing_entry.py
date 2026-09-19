"""The fixture INTEGRATION image's entrypoint: the real entry, one agent.

W197661. THE SAME SHAPE `proposing_entry.py` ALREADY IS, and for the same
reason: `integration_entry.main(agent=...)` is the documented seam, so this
composes the REAL entry and the REAL workload with a deterministic agent rather
than reimplementing either. Everything the manager validates -- the launch
reader, the bundle correlation, the whole-path preflight, the read-back of every
scheduled path, the conservative ending -- is the accepted code's, unchanged.

WHAT IS LABELLED. The agent is a deterministic stand-in for a model-driven
provider turn. It claims no model coverage; see `importing_agent` for the
statement in full.

ONE LABELLED DIFFERENCE FROM THE ACCEPTED INTEGRATION IMAGE: it carries this
agent and enters here, where that image constructs `ClaudeAgent` inside
`integration_entry` itself. Same entry, same workload, same contract module.
"""

import sys

import integration_entry
from importing_agent import ImportingAgent


def main(argv=None):
    """Hand the real entry this Work's deterministic integrator."""
    return integration_entry.main(agent=ImportingAgent())


if __name__ == "__main__":
    sys.exit(main())
