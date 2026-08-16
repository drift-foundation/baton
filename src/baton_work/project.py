"""WS-6 Slice B: the filesystem-domain operations.

Three independent location domains, none inferred from another: the
DISTRIBUTION (immutable exact releases with sibling `bin/ doc/ conf/
tmpl/`), the COORDINATION HOME (the editable instance root `init`
scaffolds and `activate` turns into an authority), and PROJECT ROOTS
(repositories `bootstrap` vendors templates into, each selected by the
accepted `baton.json` — the single explicit root config, W4). Root
selection reads the SAME validated document the config-bound open
digest-checked; lifecycle performs that binding validation, and root
resolution here merely RECHECKS that the captured accepted digest has
not advanced before answering. Filesystem writes stay entirely outside
authority state.
"""

from __future__ import annotations

import json
import os
import secrets

from baton_work.authority import WorkError
from baton_work.config import _no_duplicates, validate_root_id

# The files `init` manages in a coordination home. `init` is
# deliberately ONE-SHOT (ruled, superseding R88): if any managed target
# exists the operation refuses before writing, naming the blockers;
# interrupted attempts are inspected and cleaned up MANUALLY. Baton
# never recognizes, adopts, resumes, overwrites, or deletes.
MANAGED_HOME = ("baton.json", "BATON-SETUP.md",
                "work.sqlite3")

# The scaffold's CONTENT comes from exact-release assets (R107):
# `doc/BATON-SETUP.md` and `conf/baton.example.json` ride every
# distribution byte-for-byte (source tree: docs/ and conf/). init
# consumes them and refuses when one is absent — it never substitutes
# embedded text.


def _release_dir(release_name: str, source_name: str,
                 label: str | None = None) -> str:
	"""Locate one exact-release asset family. Release layout first —
	the directory beside the `bin/` the executable runs from (M6:
	separate assets, never zipapp-embedded) — then the source tree."""
	candidates = []
	argv0 = os.path.abspath(sys_argv0())
	candidates.append(os.path.join(
		os.path.dirname(os.path.dirname(argv0)), release_name))
	here = os.path.dirname(os.path.abspath(__file__))
	candidates.append(os.path.join(
		os.path.dirname(os.path.dirname(here)), source_name))
	for candidate in candidates:
		if os.path.isdir(candidate):
			return candidate
	raise WorkError(
		f"no {label or release_name} assets found: "
		f"expected {release_name}/ "
		f"beside this release's bin/ or {source_name}/ in the source "
		f"tree; the distribution may be incomplete")


def _release_asset(release_name: str, source_name: str,
                   filename: str) -> str:
	directory = _release_dir(release_name, source_name)
	path = os.path.join(directory, filename)
	try:
		with open(path, "r", encoding="utf-8") as handle:
			return handle.read()
	except OSError as failure:
		raise WorkError(
			f"required release asset {release_name}/{filename} is "
			f"missing or unreadable ({failure}); the distribution is "
			f"incomplete — init refuses rather than substituting "
			f"embedded text") from None


def scaffold_home(directory: str) -> dict:
	"""`baton init DIR`: write the editable coordination-home scaffold —
	valid strict JSON plus separate Markdown instructions — creating no
	database and refusing whole if ANY managed target already exists."""
	directory = os.path.abspath(directory)
	if not os.path.isdir(directory):
		raise WorkError(f"{directory} is not an existing directory; "
		                f"create it first (mkdir) — init writes only "
		                f"into a directory you chose")
	blockers = [name for name in MANAGED_HOME
	            if os.path.lexists(os.path.join(directory, name))]
	if blockers:
		raise WorkError(
			f"{directory} already contains managed Baton files "
			f"{blockers}; init may already have run here, or an "
			f"interrupted attempt needs inspection and manual cleanup. "
			f"init never adopts, resumes, overwrites, or deletes.")
	# R107: the scaffold documents are the RELEASE'S assets — the setup
	# instructions byte-for-byte, and the strict
	# configuration EXAMPLE as the seed: its skeleton (versions,
	# instance shape) is kept, its demonstration teams/roots are reset
	# to the editable empty sections, and only name and authority uuid
	# are substituted. Never embedded constants.
	setup_text = _release_asset("doc", "docs", "BATON-SETUP.md")
	example_seed = _release_asset("conf", "conf", "baton.example.json")
	try:
		document = json.loads(example_seed,
		                      object_pairs_hook=_no_duplicates)
	except WorkError:
		raise
	except ValueError as broken:
		raise WorkError(f"the release asset conf/baton.example.json "
		                f"is not valid JSON: {broken}") from None
	if not isinstance(document, dict) or \
			not isinstance(document.get("instance"), dict):
		raise WorkError("the release asset conf/baton.example.json "
		                "must be an object with an 'instance' section")
	authority_uuid = secrets.token_hex(16)
	document["teams"] = {}
	document["roots"] = {}
	document["instance"]["name"] = "edit-me"
	document["instance"]["authority_uuid"] = authority_uuid
	files = (
		("BATON-SETUP.md", setup_text),
		("baton.json",
		 json.dumps(document, indent=2, sort_keys=True) + "\n"),
	)
	created = []
	for name, content in files:
		target = os.path.join(directory, name)
		try:
			handle = os.open(target,
			                 os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
		except OSError as failure:
			raise WorkError(
				f"init failed at {name}: {failure}. Created so far: "
				f"{created or 'nothing'}. Nothing was overwritten or "
				f"deleted; inspect and clean up manually, then rerun "
				f"in a clean directory.") from None
		data = content.encode("utf-8")
		try:
			try:
				written = os.write(handle, data)
			except OSError as failure:
				# R94: O_EXCL created the target before its bytes
				# failed — the partial file is part of what the
				# operator must now inspect.
				created.append(name)
				raise WorkError(
					f"init failed writing {name}: {failure}. Created "
					f"so far, including the partial {name}: "
					f"{created}. Nothing was overwritten or deleted; "
					f"inspect and clean up manually, then rerun in a "
					f"clean directory.") from None
			if written != len(data):
				# R98: a short write is a PARTIAL failure, never
				# success — the truncated managed file is reported
				# exactly like a raised one.
				created.append(name)
				raise WorkError(
					f"init managed only a short write of {name} "
					f"({written} of {len(data)} bytes). Created so "
					f"far, including the partial {name}: {created}. "
					f"Nothing was overwritten or deleted; inspect "
					f"and clean up manually, then rerun in a clean "
					f"directory.")
		finally:
			os.close(handle)
		created.append(name)
	return {"directory": directory, "created": created,
	        "authority_uuid": authority_uuid,
	        # W2 (fresh authority): the hint IS a valid public
	        # invocation — launcher globals precede the verb, and the
	        # operand speaks the one key=value grammar.
	        "next": "edit baton.json, then: baton --participant "
	                "team.member activate directory=."}


def store_root_base(store, root_id: str) -> str:
	"""W4 (schema-preserving): the accepted baton.json is the SINGLE
	explicit root config. The base comes from the validated document the
	ordinary open already digest-checked — never from SQLite rows and
	never from a second unbound file read. A configuration replaced
	since this open refuses rather than resolving stale bases; existence
	is checked here, at use time."""
	accepted = getattr(store, "accepted_roots", None)
	if accepted is None:
		raise WorkError(
			"root resolution requires the config-bound open; this "
			"store carries no accepted configuration")
	live = store.meta().get("accepted_digest")
	if live != store.accepted_digest:
		raise WorkError(
			"the accepted configuration changed after this open; "
			"re-open against the newly accepted baton.json before "
			"resolving roots")
	if root_id not in accepted:
		raise WorkError(
			f"root {root_id!r} is not a live configured root in the "
			f"accepted baton.json - the single explicit root config")
	base = accepted[root_id]
	if not os.path.isdir(base):
		raise WorkError(
			f"root {root_id!r} declares base {base}, which is not an "
			f"existing directory on this machine; fix baton.json (and "
			f"re-accept) or check out the repository")
	return base


def template_dir() -> str:
	"""Locate this product's template assets — the same exact-release
	resolution as every other asset family (M6)."""
	return _release_dir("tmpl", "tmpl", label="template")


def sys_argv0() -> str:
	import sys
	return sys.argv[0] or "."


def _assert_contained(base: str, target: str) -> None:
	real_base = os.path.realpath(base)
	# The PARENT chain must stay inside the base and free of symlinks —
	# the target itself may not exist yet.
	parent = os.path.dirname(target)
	real_parent = os.path.realpath(parent)
	if real_parent != real_base and \
			not real_parent.startswith(real_base + os.sep):
		raise WorkError(
			f"{target} escapes the resolved project root {base}; "
			f"bootstrap never writes outside the base")
	probe = parent
	while len(probe) >= len(real_base) and probe != os.sep:
		if os.path.islink(probe):
			raise WorkError(
				f"{probe} is a symlink; bootstrap refuses symlinked "
				f"managed paths rather than following them")
		if os.path.realpath(probe) == real_base:
			break
		probe = os.path.dirname(probe)


def bootstrap_project(root_id: str, base: str,
                      templates=None) -> dict:
	"""`baton bootstrap`: vendor this release's numbered templates into
	one resolved project root and create the `work/` structure. Two
	phases: validate everything, then create with O_EXCL — identical
	existing files report already-present; conflicting bytes, wrong
	types, symlinks, and escapes refuse without replacement; nothing is
	ever deleted, overwritten, or written back to the distribution."""
	validate_root_id(root_id, "bootstrap root")
	source_dir = template_dir()
	if templates is None:
		templates = sorted(name for name in os.listdir(source_dir)
		                   if name.endswith(".md"))
	if not templates:
		raise WorkError(f"the release template directory {source_dir} "
		                f"holds no templates; nothing to vendor")
	payload = {}
	for name in templates:
		source = os.path.join(source_dir, name)
		if os.path.basename(name) != name or not os.path.isfile(source):
			raise WorkError(f"{name} is not a template shipped with "
			                f"this release")
		with open(source, "rb") as handle:
			payload[name] = handle.read()

	directories = [os.path.join(base, "tmpl"),
	               os.path.join(base, "work"),
	               os.path.join(base, "work", "open"),
	               os.path.join(base, "work", "records")]
	files = {os.path.join(base, "tmpl", name): content
	         for name, content in payload.items()}

	# Phase 1: validate every managed target; no writes.
	for path in directories:
		_assert_contained(base, path)
		if os.path.lexists(path):
			if os.path.islink(path):
				raise WorkError(f"{path} is a symlink; bootstrap "
				                f"refuses symlinked managed paths")
			if not os.path.isdir(path):
				raise WorkError(f"{path} exists and is not a "
				                f"directory; refusing without "
				                f"replacement")
	for path, content in files.items():
		_assert_contained(base, path)
		if os.path.lexists(path):
			if os.path.islink(path) or not os.path.isfile(path):
				raise WorkError(f"{path} exists as a symlink or "
				                f"non-file; refusing without "
				                f"replacement")
			with open(path, "rb") as handle:
				existing = handle.read()
			if existing != content:
				raise WorkError(
					f"{path} exists with different bytes than this "
					f"release's template; bootstrap never overwrites — "
					f"adopting a newer or different template is an "
					f"explicit repository change")

	# Phase 2: create. The boundary is adversarial (R93): EEXIST never
	# means success by itself — the actual entry is revalidated through
	# an O_NOFOLLOW dir-fd chain from the resolved base, and template
	# bytes are written through that same chain, so a parent symlink
	# inserted after phase 1 is never followed. Every failure stops,
	# deletes nothing, and reports exactly what THIS invocation
	# created (R94) — including a file O_EXCL made whose bytes then
	# failed to write.
	created, present = [], []

	def _partial(relative, failure):
		return WorkError(
			f"bootstrap failed at {relative}: {failure}. Created so "
			f"far: {created or 'nothing'}. Nothing was overwritten or "
			f"deleted; inspect and clean up manually.")

	def _chain_fd(relative_dir):
		"""Open base/<relative_dir> component-by-component with
		O_NOFOLLOW: a symlink anywhere on the managed chain refuses
		(ELOOP) instead of being followed."""
		fd = os.open(base, os.O_RDONLY | os.O_DIRECTORY)
		try:
			for component in [piece for piece in
			                  relative_dir.split(os.sep) if piece]:
				fresh = os.open(
					component,
					os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
					dir_fd=fd)
				os.close(fd)
				fd = fresh
		except OSError:
			os.close(fd)
			raise
		return fd

	for path in directories:
		relative = os.path.relpath(path, base)
		name = os.path.basename(relative)
		# R96: the parent is opened through the O_NOFOLLOW chain
		# BEFORE creation, and the created-or-existing child is
		# validated through that same parent fd — a parent swapped for
		# a symlink mid-run is detected, this invocation's own
		# misplaced empty directory is withdrawn, and the operation
		# refuses. No path-based creation outcome is ever trusted
		# without the fd-relative validation.
		try:
			parent = _chain_fd(os.path.dirname(relative))
		except OSError as failure:
			raise WorkError(
				f"{path} changed while bootstrap ran and its parent "
				f"is now a symlink or non-directory ({failure}); "
				f"refusing without replacement. Created so far: "
				f"{created or 'nothing'}.") from None
		try:
			made = False
			try:
				# R99: creation itself is fd-relative — mkdir through
				# the held O_NOFOLLOW parent fd, never a pathname a
				# raced symlink could redirect. A parent unlinked
				# after its fd was opened makes this fail (ENOENT)
				# and the operation refuses; there is NO cleanup
				# delete, ever.
				os.mkdir(name, dir_fd=parent)
				made = True
			except FileExistsError:
				pass
			except OSError as failure:
				raise WorkError(
					f"{path} changed while bootstrap ran "
					f"({failure}); its validated parent is gone or "
					f"swapped; refusing without replacement or "
					f"cleanup. Created so far: "
					f"{created or 'nothing'}.") from None
			try:
				os.close(os.open(
					name,
					os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
					dir_fd=parent))
			except OSError as failure:
				raise WorkError(
					f"{path} changed while bootstrap ran and is now "
					f"a symlink or non-directory ({failure}); "
					f"refusing without replacement. Created so far: "
					f"{created or 'nothing'}.") from None
			if made:
				created.append(relative)
			else:
				present.append(relative)
		finally:
			os.close(parent)
	for path, content in files.items():
		relative = os.path.relpath(path, base)
		name = os.path.basename(relative)
		try:
			parent = _chain_fd(os.path.dirname(relative))
		except OSError as failure:
			raise WorkError(
				f"{path} changed while bootstrap ran and its parent "
				f"is now a symlink or non-directory ({failure}); "
				f"refusing without replacement. Created so far: "
				f"{created or 'nothing'}.") from None
		try:
			try:
				handle = os.open(
					name, os.O_WRONLY | os.O_CREAT | os.O_EXCL |
					os.O_NOFOLLOW, 0o644, dir_fd=parent)
			except FileExistsError:
				try:
					reader = os.open(name,
					                 os.O_RDONLY | os.O_NOFOLLOW,
					                 dir_fd=parent)
				except OSError as failure:
					raise WorkError(
						f"{path} changed while bootstrap ran and is "
						f"now a symlink ({failure}); refusing without "
						f"replacement. Created so far: "
						f"{created or 'nothing'}.") from None
				with os.fdopen(reader, "rb") as existing:
					if existing.read() != content:
						raise WorkError(
							f"{path} changed while bootstrap ran; "
							f"refusing without replacement. Created "
							f"so far: {created or 'nothing'}.")
				present.append(relative)
				continue
			except OSError as failure:
				raise _partial(relative, failure) from None
			try:
				try:
					written = os.write(handle, content)
				except OSError as failure:
					created.append(relative)
					raise _partial(relative, failure) from None
				if written != len(content):
					# R98: a short write is a partial failure — a
					# successful bootstrap guarantees byte parity.
					created.append(relative)
					raise _partial(
						relative,
						f"short write ({written} of {len(content)} "
						f"bytes); the partial file needs inspection")
			finally:
				os.close(handle)
			created.append(relative)
		finally:
			os.close(parent)
	return {"root": root_id, "base": base, "created": created,
	        "already_present": sorted(present),
	        "templates": sorted(payload)}
