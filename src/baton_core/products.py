"""The maintained product catalog, and the only place versions are declared.

Slawomir's ruling of 2026-08-12 replaced the single shared release version:
`baton`, `baton-tui` and `baton_core` are independently versioned products,
the mailbox protocol is a separate compatibility contract, and a JSON catalog
owns all of it. Everything else -- the `--version` lines, both artifact
manifests, the deployment record -- DERIVES from this file. Nothing repeats a
version by hand.

WHY A DATA FILE AND NOT CONSTANTS. Constants in three packages are three
places to forget, and the drift that follows is silent: two numbers that
disagree still both look authoritative. One maintained document with derived
attestations is the same shape the protocol document and its manifest pin
already use.

WHY IT SHIPS INSIDE `baton_core`. Every product embeds the core, so a catalog
that travels with the core travels everywhere without being copied. It is read
through `importlib.resources`, which works identically from the source tree
and from inside a zipapp -- the executables must answer `--version` offline,
with no repository anywhere near them.

The catalog is READ ONLY at runtime. Editing it is a deliberate release act
performed in the source tree; nothing here writes it back.
"""

from __future__ import annotations

import json
from importlib import resources

CATALOG_NAME = "products.json"
# The document's own shape, versioned separately from everything it describes.
# A reader that does not know a format is not entitled to guess at it.
SUPPORTED_FORMAT = "baton.products"
SUPPORTED_FORMAT_VERSIONS = (1,)


class CatalogError(Exception):
	"""The product catalog is missing or unusable.

	Raised at import time, deliberately: a build that failed to package the
	catalog produces an executable that cannot say what it is, and finding
	that out at `--version` is better than finding it out three commands into
	someone's morning.
	"""


def _load() -> dict:
	try:
		raw = (resources.files(__package__) / CATALOG_NAME).read_bytes()
	except (FileNotFoundError, OSError) as error:
		raise CatalogError(
			f"the product catalog {CATALOG_NAME} is missing from this "
			f"distribution: {error}") from None
	try:
		document = json.loads(raw.decode("utf-8"))
	except (ValueError, UnicodeDecodeError) as error:
		raise CatalogError(f"the product catalog is unreadable: {error}") from None
	_validate(document)
	return document


def _validate(document) -> None:
	"""Refuse a catalog this reader cannot honour, rather than half-read it.

	Every check here exists because the alternative is a plausible-looking
	default: a missing version reported as `None`, a missing product silently
	absent from a manifest, a format nobody has seen treated as this one.
	"""
	if not isinstance(document, dict):
		raise CatalogError("the product catalog is not an object")
	if document.get("format") != SUPPORTED_FORMAT:
		raise CatalogError(
			f"the product catalog is not {SUPPORTED_FORMAT!r}: "
			f"{document.get('format')!r}")
	if document.get("format_version") not in SUPPORTED_FORMAT_VERSIONS:
		raise CatalogError(
			f"the product catalog is format version "
			f"{document.get('format_version')!r}, which this build does not read")
	if not isinstance(document.get("protocol_version"), int):
		raise CatalogError("the product catalog has no integer protocol_version")
	core = document.get("core")
	if not isinstance(core, dict):
		raise CatalogError("the product catalog has no core section")
	_semantic(core.get("version"), "core.version")
	if not isinstance(core.get("api_version"), int):
		raise CatalogError("core.api_version is not an integer")
	floors = document.get("floors")
	if not isinstance(floors, dict):
		raise CatalogError("the product catalog has no floors section")
	for key in ("python_min", "sqlite_min"):
		if not isinstance(floors.get(key), str) or not floors[key]:
			raise CatalogError(f"floors.{key} is not a version string")
	products = document.get("products")
	if not isinstance(products, dict) or not products:
		raise CatalogError("the product catalog lists no products")
	seen_artifacts = {}
	for name, entry in products.items():
		if not isinstance(entry, dict):
			raise CatalogError(f"product {name!r} is not an object")
		_semantic(entry.get("version"), f"products.{name}.version")
		if not isinstance(entry.get("requires_core_api"), int):
			raise CatalogError(f"products.{name}.requires_core_api is not an integer")
		# COHERENCE AT THE SOURCE. The deployer refuses a set whose product
		# requires an API its embedded core does not offer; every product here
		# embeds THIS core, so a catalog that declares the mismatch would build
		# an artifact that could never be published.
		if entry["requires_core_api"] != core["api_version"]:
			raise CatalogError(
				f"products.{name}.requires_core_api is "
				f"{entry['requires_core_api']} but this core offers API "
				f"{core['api_version']}")
		artifact = entry.get("artifact")
		if not isinstance(artifact, str) or not artifact:
			raise CatalogError(f"products.{name}.artifact is not a path")
		_relative(artifact, f"products.{name}.artifact")
		if artifact in seen_artifacts:
			raise CatalogError(
				f"products.{name}.artifact is also {seen_artifacts[artifact]}'s: "
				f"{artifact}")
		seen_artifacts[artifact] = name


def _relative(value: str, where: str) -> None:
	"""A path that can only address INSIDE a distribution root.

	Refused rather than normalized: an artifact address is joined to a root and
	then opened, so `/etc/passwd` or `../../elsewhere` reaching that join is the
	difference between a manifest and an instruction."""
	if value.startswith("/") or value.startswith("~") or "\\" in value:
		raise CatalogError(f"{where} must be a relative POSIX path: {value!r}")
	parts = value.split("/")
	if any(part in ("", ".", "..") for part in parts):
		raise CatalogError(f"{where} must have no empty or dotted component: {value!r}")


# The SAME spelling the deployer enforces. `01.2.3` is all digits and would
# have passed an `isdigit` check here and then been refused at publication --
# a builder must not succeed at producing an artifact its own deployer
# necessarily rejects.
_SEMANTIC = "0|[1-9][0-9]*"


def _semantic(value, where: str) -> None:
	"""`major.minor.patch`, no leading zeros. Checked rather than assumed: a
	version string is compared, printed and used to name a release document,
	and every one of those is worse with a typo in it than without."""
	if not isinstance(value, str):
		raise CatalogError(f"{where} is not a string")
	parts = value.split(".")
	if len(parts) != 3 or not all(
			part.isdigit() and (part == "0" or not part.startswith("0"))
			for part in parts):
		raise CatalogError(f"{where} is not major.minor.patch: {value!r}")


_CATALOG = _load()


def catalog() -> dict:
	"""The whole catalog, copied. Callers get data, not a shared mutable."""
	return json.loads(json.dumps(_CATALOG))


def product(name: str) -> dict:
	"""One product's declaration. Unknown names are an error, not an empty
	dict: a manifest built from a silent default would attest to nothing."""
	entry = _CATALOG["products"].get(name)
	if entry is None:
		raise CatalogError(f"no such product in the catalog: {name!r}")
	return dict(entry)


def product_names() -> tuple[str, ...]:
	return tuple(sorted(_CATALOG["products"]))


CORE_VERSION = _CATALOG["core"]["version"]
CORE_API_VERSION = _CATALOG["core"]["api_version"]
PROTOCOL_VERSION = _CATALOG["protocol_version"]
PYTHON_MIN = _CATALOG["floors"]["python_min"]
SQLITE_MIN_TEXT = _CATALOG["floors"]["sqlite_min"]
SQLITE_MIN = tuple(int(part) for part in SQLITE_MIN_TEXT.split("."))
CLI_VERSION = _CATALOG["products"]["baton"]["version"]
TUI_VERSION = _CATALOG["products"]["baton-tui"]["version"]
