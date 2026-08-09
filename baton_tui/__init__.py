"""Baton console: a human-oriented terminal front end over `baton_core`.

Separate distribution, separate version, no protocol logic of its own. It
calls the same public core API an agent CLI would; it does not read SQLite and
does not shell out to the JSON CLI.

`curses` is the only terminal dependency and it is stdlib, so the console
stays as installable as the tool it fronts. No part of this package may enter
the agent CLI artifact or its import graph.
"""

TUI_VERSION = "0.1.0"

# The `baton_core` API this console was built against. Declared rather than
# assumed so the two can release on different cadences: a console shipped
# faster than the protocol moves still states what it needs.
REQUIRES_CORE_API = 1


def check_core_compatibility(core) -> None:
	"""Fail at startup, not mid-render, if the core is not what this console
	was built for."""
	versions = core.core_versions()
	if versions["core_api_version"] < REQUIRES_CORE_API:
		raise RuntimeError(
			f"baton-tui {TUI_VERSION} requires core API {REQUIRES_CORE_API}, "
			f"but this baton_core offers {versions['core_api_version']}")
