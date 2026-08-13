"""Baton console: a human-oriented terminal front end over `baton_core`.

Separate distribution, no protocol logic of its own. It calls the same public
core API an agent CLI would; it does not read SQLite and does not shell out to
the JSON CLI.

It IS its own versioned product. `baton-tui` and `baton` move on separate
cadences and report separate numbers, both derived from the catalog in
`baton_core/products.json` -- see `baton_core.products` for why one maintained
document owns them.

(Superseded 2026-08-12. This package used to carry no version at all, because
`baton_core.RELEASE_VERSION` was the single number both executables reported
and being told two numbers for one release was the failure being prevented.
Slawomir ruled independent products instead; the drift that rule feared is now
prevented by having one OWNER per version rather than one version.)

`curses` is the only terminal dependency and it is stdlib, so the console
stays as installable as the tool it fronts. No part of this package may enter
the agent CLI artifact or its import graph.
"""

from baton_core import products as _products

# This console's own product version, and the `baton_core` API it was built
# against. Both come from the catalog: declared rather than assumed, because
# the console can be run against a core it did not ship beside, and then the
# number it needs has to be checkable rather than presumed.
TUI_VERSION = _products.TUI_VERSION
REQUIRES_CORE_API = _products.product("baton-tui")["requires_core_api"]


def check_core_compatibility(core) -> None:
	"""Fail at startup, not mid-render, if the core is not what this console
	was built for.

	EQUALITY, not `>=`. The old check accepted any newer core, which is only
	safe if the API never removes anything -- and protocol 10 removed
	`filename` from every delivery and every Store signature. Under `>=`, a
	console built for API 1 would have started happily against API 2 and then
	failed on the first message carrying a part name: a startup check that
	passes and then breaks mid-render is worse than none, because it has
	already told the human everything is fine.

	If a compatible range is ever wanted, it has to be declared and tested as
	a range. Until then the contract is exact.
	"""
	versions = core.core_versions()
	if versions["core_api_version"] != REQUIRES_CORE_API:
		raise RuntimeError(
			f"baton-tui requires core API {REQUIRES_CORE_API}, "
			f"but this baton_core offers {versions['core_api_version']}")
