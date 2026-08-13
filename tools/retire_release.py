#!/usr/bin/env python3
"""Remove a rejected release, and flatten the frozen pair — bounded, and never
with `rm -rf`.

WHY THIS EXISTS. The PLAN 25 production repair was first written as a runbook
of `chmod -R u+w` and `rm -rf` over paths in `/home/sl/baton`. Those two
commands cannot be reviewed: `rm -rf` deletes whatever is at the path it is
given, and the path is composed by a human at 2am from a directory name they
believe is right. A recursive delete aimed one component too high, or aimed at
a path whose parent was replaced with a symlink, takes the production root with
it — and nothing about the command distinguishes that from the intended act.

WHAT THIS DOES INSTEAD. Every removal is:

  * ENUMERATED BEFORE IT HAPPENS. The plan lists each path, its type, its size
    and its digest. Nothing is removed that the plan did not name.
  * BOUNDED BY A KNOWN SHAPE. A release directory holds `bin/`, `doc/`,
    `conf/` and `PRODUCT.json` and nothing else, because that is what `install`
    creates. Anything unexpected inside it is a REFUSAL, not something to
    delete on the way past: an unrecognised file is either evidence somebody
    should read or a sign this is not the directory we think it is.
  * CONFINED. Every component is opened `O_NOFOLLOW|O_DIRECTORY` from the root
    descriptor, and every unlink happens through the held descriptor, so an
    ancestor swapped after validation cannot redirect it. A symlink anywhere on
    the way in, or in place of any member, refuses.
  * DRY BY DEFAULT. `--apply` is required to write anything.

WHAT IT REFUSES TO BE. It is not a general delete tool. It removes one exact
release of one known product from one generation, or it flattens one frozen
version directory into the direct `legacy/bin/` layout. It takes no glob, no
recursion depth, and no path that is not composed from validated components.
"""

from __future__ import annotations

import errno
import json
import os
import re
import stat as stat_module
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import deploy                                              # noqa: E402

# WHAT AN INSTALLED RELEASE HOLDS. `install()` writes exactly these; a
# directory holding anything else is not a release this tool will remove.
RELEASE_MEMBERS = ("PRODUCT.json", "bin", "conf", "doc")
RELEASE_DIRS = ("bin", "conf", "doc")

RELEASE_NAME = re.compile(r"\Av(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\Z")
NAMESPACE_NAME = re.compile(r"\A(legacy|v(0|[1-9][0-9]*))\Z")
ALIAS = "latest"


class RetireError(Exception):
	"""A refusal a human should read, rather than a traceback."""


def _open_beneath(parent_fd: int, name: str) -> int:
	"""One component in, following nothing and CREATING nothing.

	`deploy._descend` cannot be used here: it `mkdir`s each component on the
	way, which is right for an installer and exactly wrong for a tool whose
	whole job is to remove things -- it would silently manufacture the
	directory it was asked to delete from.
	"""
	try:
		fd = deploy._openat2_beneath(name, parent_fd)
	except OSError as exc:
		# `openat2` REFUSES rather than returning a descriptor: RESOLVE_BENEATH
		# and RESOLVE_NO_SYMLINKS make a swapped ancestor an error at the
		# syscall, which is the whole reason it is preferred here. Its refusal
		# is the answer, not something to fall back from.
		if exc.errno in (errno.ELOOP, errno.EXDEV, errno.ENOTDIR):
			raise RetireError(
				f"{name!r} is a symlink or escapes the deployment root; every "
				f"component of a path this tool removes through must be a real "
				f"directory beneath the root it was given") from None
		if exc.errno == errno.ENOENT:
			raise RetireError(f"{name!r} does not exist") from None
		raise RetireError(f"{name!r} is not usable: {exc.strerror}") from None
	if fd is not None:
		return fd
	try:
		return os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_DIRECTORY,
		               dir_fd=parent_fd)
	except OSError as exc:
		if exc.errno in (errno.ELOOP, errno.ENOTDIR):
			raise RetireError(
				f"{name!r} is a symlink or not a directory; every component of "
				f"a path this tool removes through must be a real directory "
				f"it opened itself") from None
		if exc.errno == errno.ENOENT:
			raise RetireError(f"{name!r} does not exist") from None
		raise RetireError(f"{name!r} is not usable: {exc.strerror}") from None


def _validated(product: str, namespace: str, release: str | None) -> None:
	if product not in set(deploy.PRODUCT_DIRS.values()):
		raise RetireError(
			f"{product!r} is not a product directory this deployment uses "
			f"({sorted(set(deploy.PRODUCT_DIRS.values()))})")
	if not NAMESPACE_NAME.match(namespace):
		raise RetireError(
			f"{namespace!r} is not a generation name; a namespace is `legacy` "
			f"or `v<protocol>`, and a path component this tool composes is "
			f"never free text")
	if release is not None and not RELEASE_NAME.match(release):
		raise RetireError(
			f"{release!r} is not an exact release directory name; this tool "
			f"removes `vX.Y.Z` and nothing else -- not a glob, not a parent, "
			f"not `..`")


def _entries(fd: int) -> list[str]:
	return sorted(os.listdir(fd))


def _describe(dir_fd: int, relative: str, name: str) -> dict:
	"""One member, as the plan will report it. Follows nothing."""
	info = os.lstat(name, dir_fd=dir_fd)
	kind = ("symlink" if stat_module.S_ISLNK(info.st_mode)
	        else "directory" if stat_module.S_ISDIR(info.st_mode)
	        else "file" if stat_module.S_ISREG(info.st_mode)
	        else "other")
	entry = {"path": os.path.join(relative, name), "kind": kind,
	         "mode": oct(info.st_mode & 0o7777), "size": info.st_size}
	if kind == "file":
		entry["sha256"] = deploy.digest(deploy._at(dir_fd, name))
	return entry


def plan_retire(root: str, product: str, namespace: str, release: str) -> dict:
	"""Everything removing this release would touch, and every reason not to.

	Returns the plan; raises only when the request itself is malformed. A
	release that cannot be removed comes back with `refusals`, because "here
	is what is wrong" is more useful to an operator at 2am than a traceback.
	"""
	_validated(product, namespace, release)
	root_fd = deploy._open_root(root)
	held = [root_fd]
	refusals: list[str] = []
	removals: list[dict] = []
	try:
		app_fd = _open_beneath(root_fd, "app")
		held.append(app_fd)
		product_fd = _open_beneath(app_fd, product)
		held.append(product_fd)
		generation_fd = _open_beneath(product_fd, namespace)
		held.append(generation_fd)

		# THE ALIAS FIRST. Removing a release that `latest` still names would
		# leave a dangling alias, and a dangling alias is how a consumer that
		# resolves at launch discovers the deployment mid-repair.
		alias_target = None
		if ALIAS in _entries(generation_fd):
			try:
				alias_target = os.readlink(ALIAS, dir_fd=generation_fd)
			except OSError:
				refusals.append(f"{namespace}/{ALIAS} is not a symlink; this "
				                f"tool does not remove what it cannot read")
			if alias_target == release:
				refusals.append(
					f"{namespace}/{ALIAS} still points at {release}. Drop or "
					f"repoint the alias first -- as its own act, so the "
					f"moment when nothing is discoverable is deliberate.")

		if release not in _entries(generation_fd):
			refusals.append(f"{namespace}/{release} does not exist")
			return {"root": os.path.abspath(root), "product": product,
			        "namespace": namespace, "release": release,
			        "alias_target": alias_target, "removals": [],
			        "refusals": refusals}

		release_fd = _open_beneath(generation_fd, release)
		held.append(release_fd)
		present = _entries(release_fd)
		unexpected = [name for name in present if name not in RELEASE_MEMBERS]
		if unexpected:
			refusals.append(
				f"{namespace}/{release} holds {unexpected}, which an installed "
				f"release does not. Something else is in this directory: read "
				f"it before anything removes it.")
		for name in present:
			entry = _describe(release_fd, f"{namespace}/{release}", name)
			if entry["kind"] == "symlink":
				refusals.append(f"{entry['path']} is a symlink; a release "
				                f"member is a real file or directory")
			removals.append(entry)
			if name in RELEASE_DIRS and entry["kind"] == "directory":
				member_fd = _open_beneath(release_fd, name)
				held.append(member_fd)
				for inner in _entries(member_fd):
					inner_entry = _describe(
						member_fd, f"{namespace}/{release}/{name}", inner)
					if inner_entry["kind"] not in ("file",):
						refusals.append(
							f"{inner_entry['path']} is a {inner_entry['kind']}; "
							f"a release member directory holds regular files")
					removals.append(inner_entry)
		return {"root": os.path.abspath(root), "product": product,
		        "namespace": namespace, "release": release,
		        "alias_target": alias_target,
		        "removals": sorted(removals, key=lambda item: item["path"]),
		        "refusals": refusals}
	finally:
		for fd in reversed(held):
			os.close(fd)


def retire(root: str, product: str, namespace: str, release: str, *,
           apply: bool = False) -> dict:
	"""Remove exactly the release the plan named, and nothing else."""
	report = plan_retire(root, product, namespace, release)
	if report["refusals"]:
		raise RetireError("; ".join(report["refusals"]))
	if not apply:
		report["applied"] = False
		return report

	expected = {item["path"] for item in report["removals"]}
	root_fd = deploy._open_root(root)
	held = [root_fd]
	try:
		app_fd = _open_beneath(root_fd, "app")
		held.append(app_fd)
		product_fd = _open_beneath(app_fd, product)
		held.append(product_fd)
		generation_fd = _open_beneath(product_fd, namespace)
		held.append(generation_fd)
		release_fd = _open_beneath(generation_fd, release)
		held.append(release_fd)

		# RE-READ AND COMPARE. Between the plan and the act, the directory may
		# have changed; removing what a stale plan described is the same class
		# of mistake as `rm -rf` on a path composed by hand.
		present = sorted(_entries(release_fd))
		if {f"{namespace}/{release}/{name}" for name in present} - expected:
			raise RetireError(
				f"{namespace}/{release} changed since it was planned; nothing "
				f"was removed. Re-plan and read it again.")

		# Modes come back one directory at a time, through held descriptors --
		# not `chmod -R`, which walks whatever it finds.
		os.chmod(deploy._at(release_fd), 0o755)
		for name in present:
			if name in RELEASE_DIRS:
				member_fd = _open_beneath(release_fd, name)
				held.append(member_fd)
				os.chmod(deploy._at(member_fd), 0o755)
				for inner in sorted(_entries(member_fd)):
					if f"{namespace}/{release}/{name}/{inner}" not in expected:
						raise RetireError(
							f"{name}/{inner} appeared after planning; stopping "
							f"with the tree partially removed is worse than "
							f"stopping now, so nothing further is touched.")
					os.unlink(inner, dir_fd=member_fd)
				os.rmdir(name, dir_fd=release_fd)
			else:
				os.chmod(name, 0o644, dir_fd=release_fd)
				os.unlink(name, dir_fd=release_fd)
		os.rmdir(release, dir_fd=generation_fd)
		deploy._fsync_dir(deploy._at(generation_fd))
	finally:
		for fd in reversed(held):
			try:
				os.close(fd)
			except OSError:
				pass
	report["applied"] = True
	return report


def drop_alias(root: str, product: str, namespace: str, *,
               apply: bool = False) -> dict:
	"""Remove `<namespace>/latest`. Its own act, deliberately.

	Dropping the alias makes the generation undiscoverable until something
	points at it again. That is a decision an operator makes on purpose, not a
	side effect of removing a release.
	"""
	_validated(product, namespace, None)
	root_fd = deploy._open_root(root)
	held = [root_fd]
	try:
		app_fd = _open_beneath(root_fd, "app")
		held.append(app_fd)
		product_fd = _open_beneath(app_fd, product)
		held.append(product_fd)
		generation_fd = _open_beneath(product_fd, namespace)
		held.append(generation_fd)
		if ALIAS not in _entries(generation_fd):
			return {"alias": f"{product}/{namespace}/{ALIAS}", "target": None,
			        "applied": False, "state": "absent"}
		info = os.lstat(ALIAS, dir_fd=generation_fd)
		if not stat_module.S_ISLNK(info.st_mode):
			raise RetireError(
				f"{product}/{namespace}/{ALIAS} is not a symlink; an alias "
				f"this tool removes is the relative link `install` wrote")
		target = os.readlink(ALIAS, dir_fd=generation_fd)
		if not apply:
			return {"alias": f"{product}/{namespace}/{ALIAS}", "target": target,
			        "applied": False, "state": "present"}
		os.unlink(ALIAS, dir_fd=generation_fd)
		deploy._fsync_dir(deploy._at(generation_fd))
		return {"alias": f"{product}/{namespace}/{ALIAS}", "target": target,
		        "applied": True, "state": "removed"}
	finally:
		for fd in reversed(held):
			os.close(fd)


def flatten(root: str, product: str, namespace: str, version: str, *,
            artifact: str, apply: bool = False) -> dict:
	"""`<namespace>/<version>/bin/<artifact>` -> `<namespace>/bin/<artifact>`.

	The frozen pair stops being a release family. This moves the binaries up
	one level and removes the empty version directory with `rmdir` -- which
	fails loudly if anything is left, where `rm -rf` would take it silently.

	The digest is read before and after: the whole value of this directory is
	that its bytes are the ones production has always run, so a move that
	changed them would be the one failure worth catching.
	"""
	_validated(product, namespace, version)
	if artifact != os.path.basename(artifact) or artifact.startswith("."):
		raise RetireError(f"{artifact!r} is not a bare artifact name")
	root_fd = deploy._open_root(root)
	held = [root_fd]
	try:
		app_fd = _open_beneath(root_fd, "app")
		held.append(app_fd)
		product_fd = _open_beneath(app_fd, product)
		held.append(product_fd)
		generation_fd = _open_beneath(product_fd, namespace)
		held.append(generation_fd)
		if "bin" in _entries(generation_fd):
			raise RetireError(
				f"{product}/{namespace}/bin already exists; this tool will not "
				f"merge into a directory it did not create, because the one "
				f"thing it must never do is overwrite the frozen binaries")
		version_fd = _open_beneath(generation_fd, version)
		held.append(version_fd)
		inside = _entries(version_fd)
		if inside != ["bin"]:
			raise RetireError(
				f"{product}/{namespace}/{version} holds {inside}, not just "
				f"`bin`. This is an installed release, not the hand-made "
				f"directory the relocation left; use `retire` for a release.")
		bin_fd = _open_beneath(version_fd, "bin")
		held.append(bin_fd)
		members = _entries(bin_fd)
		if members != [artifact]:
			raise RetireError(
				f"{product}/{namespace}/{version}/bin holds {members}, not "
				f"exactly [{artifact!r}]")
		info = os.lstat(artifact, dir_fd=bin_fd)
		if not stat_module.S_ISREG(info.st_mode):
			raise RetireError(f"{artifact} is not a regular file")
		before = deploy.digest(deploy._at(bin_fd, artifact))
		report = {"product": product, "namespace": namespace,
		          "version": version, "artifact": artifact,
		          "sha256": before,
		          "from": f"app/{product}/{namespace}/{version}/bin/{artifact}",
		          "to": f"app/{product}/{namespace}/bin/{artifact}"}
		if not apply:
			report["applied"] = False
			return report

		os.rename("bin", "bin", src_dir_fd=version_fd,
		          dst_dir_fd=generation_fd)
		os.rmdir(version, dir_fd=generation_fd)
		deploy._fsync_dir(deploy._at(generation_fd))
		moved_fd = _open_beneath(generation_fd, "bin")
		held.append(moved_fd)
		after = deploy.digest(deploy._at(moved_fd, artifact))
		if after != before:
			raise RetireError(
				f"{artifact} is {after[:12]}… after the move and was "
				f"{before[:12]}… before it. The move changed the bytes, which "
				f"is the one thing this directory exists to prevent.")
		report["applied"] = True
		return report
	finally:
		for fd in reversed(held):
			try:
				os.close(fd)
			except OSError:
				pass


def main(argv=None) -> int:
	import argparse

	parser = argparse.ArgumentParser(
		prog="retire_release",
		description="Remove one rejected release, or flatten the frozen pair")
	sub = parser.add_subparsers(dest="command", required=True)

	for name, needs_release in (("plan", True), ("retire", True),
	                            ("drop-alias", False), ("flatten", True)):
		cmd = sub.add_parser(name)
		cmd.add_argument("root")
		cmd.add_argument("--product", required=True)
		cmd.add_argument("--namespace", required=True)
		if needs_release:
			cmd.add_argument("--release", required=True)
		if name == "flatten":
			cmd.add_argument("--artifact", required=True)
		if name in ("retire", "drop-alias", "flatten"):
			cmd.add_argument("--apply", action="store_true",
			                 help="actually write; without it this reports "
			                      "what would happen and changes nothing")

	args = parser.parse_args(argv)
	try:
		if args.command == "plan":
			report = plan_retire(args.root, args.product, args.namespace,
			                     args.release)
		elif args.command == "retire":
			report = retire(args.root, args.product, args.namespace,
			                args.release, apply=args.apply)
		elif args.command == "drop-alias":
			report = drop_alias(args.root, args.product, args.namespace,
			                    apply=args.apply)
		else:
			report = flatten(args.root, args.product, args.namespace,
			                 args.release, artifact=args.artifact,
			                 apply=args.apply)
		print(json.dumps(report, indent=2, sort_keys=True))
		return 1 if report.get("refusals") else 0
	except (RetireError, deploy.DeployError) as refusal:
		print(f"retire_release: {refusal}", file=sys.stderr)
		return 1


if __name__ == "__main__":
	sys.exit(main())
