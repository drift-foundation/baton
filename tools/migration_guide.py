#!/usr/bin/env python3
"""Generate the deployment-specific migration guide and runbook.

ONE BODY OF BYTES, published twice: as a broadcast notice and as one durable
directed delivery per registered participant. Two renderings of "the same"
document is how half a team ends up following instructions the other half never
saw, so this generates the text once and the publisher sends those exact bytes
to every audience.

GENERATED, not written. Every path, version and digest in the guide is read
from the deployment it describes -- the installed product records, the mailbox
identity, the accepted config's participant list -- so a guide cannot describe
a release that is not there. A hand-written runbook drifts from the tree it
documents on the first day nobody re-reads it.

This writes a file. It publishes nothing, edits no configuration, moves no
mailbox and executes nothing it describes.
"""

from __future__ import annotations

import json
import os
import sys
import textwrap

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import deploy                                          # noqa: E402  (sibling)


class GuideError(Exception):
	"""A refusal a human should read, rather than a traceback."""


def _release(destination: str, tool: str) -> dict:
	"""The exact release a consumer will be told to run, and its facts.

	Read through the ALIAS and then resolved to the exact path, which is
	exactly what a consumer must do: the guide tells people to run a path that
	cannot move under them, and it works out that path the same way they will.
	"""
	product = deploy.PRODUCT_DIRS[tool]
	app_dir = os.path.join(destination, "app", product)
	if not os.path.isdir(app_dir):
		raise GuideError(f"{app_dir} does not exist; install the applications "
		                 f"before generating a guide about them")
	namespaces = sorted(name for name in os.listdir(app_dir)
	                    if os.path.isdir(os.path.join(app_dir, name)))
	if len(namespaces) != 1:
		raise GuideError(
			f"{app_dir} holds {namespaces or 'no generations'}; a guide names "
			f"one generation, so say which by installing only what this "
			f"cutover is about")
	generation = os.path.join(app_dir, namespaces[0])
	release_dir = deploy.resolve_alias(generation)
	record = json.load(open(os.path.join(release_dir, deploy.PRODUCT_RECORD)))
	return {"tool": tool, "namespace": namespaces[0], "generation": generation,
	        "release": release_dir, "record": record,
	        "execute": os.path.join(release_dir, record["artifact"])}


def _accepted(config_path: str) -> tuple[list[str], str, int]:
	"""The audience, read from the AUTHORITY rather than from a file.

	R3. This used to `json.load` the config. A config file is a PROPOSAL until
	`regen` accepts it: editing it without regen changes the file and changes
	nothing the authority believes, so an edited file could have quietly
	removed real participants from a handoff whose whole value is that it
	reached everyone.

	`open_instance` validates the accepted digest and generation before it
	will open at all, so the participants below are the ones the authority
	actually recognises -- and the digest is returned so publication can prove
	the config did not change between generating the guide and sending it.
	"""
	sys.path.insert(0, os.path.join(os.path.dirname(HERE), "src"))
	import baton_core

	try:
		with baton_core.open_instance(config_path, readonly=True) as store:
			people = [entry["address"] for entry in store.list_participants()]
			return sorted(people), store.config_digest, store.config["generation"]
	except baton_core.BatonError as refusal:
		raise GuideError(
			f"the authority at {config_path} would not open read-only: "
			f"{refusal}. The audience for a complete handoff comes from the "
			f"accepted config, never from an unaccepted file.") from None


def _preexisting_problems(config_path: str) -> int:
	"""How many problems this authority ALREADY has, counted read-only.

	Named in the guide because somebody will run `doctor` after the move and
	attribute what they see to it. Every one of these is an external part
	pinned into a repository that has moved on -- a reference, not a mailbox
	defect -- and they predate the migration.
	"""
	sys.path.insert(0, os.path.join(os.path.dirname(HERE), "src"))
	import baton_core

	return len(baton_core.doctor(config_path).get("problems", []))


def _identity(mailbox_dir: str, cli: dict, tui: dict) -> dict:
	"""The destination mailbox's handshake, read as a TRUST DOCUMENT and
	cross-checked against the releases this guide is about.

	R12. This used to be a plain `json.load`, so a guide could tell people to
	point a generation-11 console at a legacy mailbox and read perfectly well
	while doing it. The core's own reader is used -- strict JSON, known fields,
	namespace agreeing with protocol -- and then the two products are checked
	against what it says.

	What it says is a PROTOCOL, and nothing about which applications or
	versions may open the mailbox: that grant was withdrawn on 2026-08-13. So
	this guide asks the only question there is -- can the executables it
	documents speak this mailbox's generation.
	"""
	sys.path.insert(0, os.path.join(os.path.dirname(HERE), "src"))
	import baton_core

	identity_path = os.path.join(mailbox_dir, deploy.MAILBOX_RECORD)
	if not os.path.isfile(identity_path):
		raise GuideError(f"{identity_path} does not exist; the destination "
		                 f"mailbox has no identity to describe")
	try:
		document = baton_core.mailbox_identity(
			os.path.join(mailbox_dir, "baton.json"))
	except baton_core.BatonError as refusal:
		raise GuideError(f"the destination mailbox identity is not usable: "
		                 f"{refusal}") from None
	if document is None:
		raise GuideError(f"{identity_path} could not be read")
	# THE SAME RULE STARTUP USES, not a hand-written approximation of it:
	# `check_mailbox_identity` is what the client runs, so asking it is the
	# only way to be sure the guide describes a pair that works. Since the
	# per-application grant was withdrawn, what it answers is the protocol
	# question -- and the namespace check below is this guide's own, because a
	# guide naming a release from another generation is a guide nobody can
	# follow even when the protocols agree.
	for release in (cli, tui):
		record = release["record"]
		try:
			baton_core.check_mailbox_identity(
				os.path.join(mailbox_dir, "baton.json"), release["tool"])
		except baton_core.BatonError as refusal:
			raise GuideError(
				f"{release['tool']} {record['product_version']} could not open "
				f"this mailbox: {refusal} A guide that told people to run that "
				f"pair would be telling them to fail.") from None
		if record["namespace"] != document["namespace"]:
			raise GuideError(
				f"{release['tool']} is installed under "
				f"{record['namespace']!r} and the mailbox is "
				f"{document['namespace']!r}")
	return document


def render(destination: str, source_config: str, mailbox_dir: str) -> str:
	"""The complete guide, as one deterministic body of bytes."""
	cli = _release(destination, "baton")
	tui = _release(destination, "baton-tui")
	if cli["namespace"] != tui["namespace"]:
		raise GuideError(
			f"the CLI is in {cli['namespace']} and the console in "
			f"{tui['namespace']}; one cutover moves one generation")
	identity = _identity(mailbox_dir, cli, tui)
	people, config_digest, generation = _accepted(source_config)
	problems = _preexisting_problems(source_config)
	destination_config = os.path.join(mailbox_dir, "baton.json")

	def paragraph(text: str) -> str:
		"""Wrapped, because this is read in a terminal and in a console pane
		whose width nobody controls. Generated prose that arrives as one long
		line is prose people skim."""
		return "\n".join(textwrap.wrap(text, width=72))

	versions = (f"`baton` {cli['record']['product_version']} and `baton-tui` "
	            f"{tui['record']['product_version']}")
	# ONE SENTENCE, because there is one rule. This used to branch on whether
	# the release sat in the granted `legacy` namespace; that family was
	# removed on 2026-08-13, so a guide that still explained an exception
	# would be teaching a layout the deployer cannot produce.
	generation_sentence = (
		f"They serve protocol {identity['protocol_version']}, and their major "
		f"version IS that number: a release's major and the generation it "
		f"serves are the same thing, which is why they live under "
		f"`{cli['namespace']}`.")

	lines = [
		f"# Baton is moving: new paths for the same {versions}",
		"",
		"Nothing about the software changes in this move. The executables you",
		"will be running are the ones you are running now, byte for byte; what",
		"changes is where they live and where the mailbox lives.",
		"",
		"## What is changing",
		"",
		f"- the mailbox moves to `{mailbox_dir}`",
		f"- `baton` becomes `{cli['execute']}`",
		f"- `baton-tui` becomes `{tui['execute']}`",
		f"- your `--config` becomes `{destination_config}`",
		"",
		"## Why the paths look like that",
		"",
		paragraph(f"{versions} are now installed as IMMUTABLE exact releases. "
		          f"A release directory is never rewritten: a new version "
		          f"arrives beside the old one, and nothing you are running "
		          f"changes underneath you."),
		"",
		paragraph(generation_sentence),
		"",
		"## Run the exact path, never `latest`",
		"",
		paragraph(f"There is a `{cli['generation']}/latest` symlink and it is "
		          f"for DISCOVERY: it tells a human which release is current. "
		          f"It is not a path to configure or to run."),
		"",
		"The reason is specific rather than stylistic. These executables are",
		"Python zipapps, and CPython reopens the archive BY PATH every time it",
		"lazily imports a module. A process that started through `latest`",
		"would, after the alias moved, seek offsets from the archive it began",
		"with into the archive that replaced it. The good outcome is a crash.",
		"",
		"So: resolve once, then run what you resolved.",
		"",
		"```text",
		f"deploy.py resolve {cli['generation']}",
		f"→ {cli['execute']}",
		"```",
		"",
		"## What to change, exactly",
		"",
		"Every place that names the old executable or the old config:",
		"",
		"```text",
		f"baton      →  {cli['execute']}",
		f"baton-tui  →  {tui['execute']}",
		f"--config   →  {destination_config}",
		"```",
		"",
		"Supervisors, bridge configuration, shell aliases, notes to yourself.",
		paragraph(
			"A stale path does not silently misbehave. The old directory keeps "
			"a `MOVED` file naming where the mailbox went, and no `baton.json` "
			"-- so an old command finds no config and says so, and the file "
			"beside it tells a human where to look. Nothing follows that "
			"automatically: the chain is read by people, one hop at a time."),
		"",
		"## The order this happens in",
		"",
		"```text",
		"1. this guide is published (you are reading it)",
		"2. every active claim is resolved and every participant stops",
		"3. the mailbox is moved: one offline `mv` of the config and the",
		"   database, on the same filesystem, with nothing running",
		"4. consumers are pointed at the exact paths above",
		"5. everyone relaunches and a directed message is proved end to end",
		"```",
		"",
		paragraph(
			"Between 2 and 5 nothing can be sent, claimed or replied to, and "
			"that is the point: the move is an OFFLINE one. Everything stops, "
			"the files are moved with nothing holding them open, and everything "
			"starts again on the new path. A message in flight during a move is "
			"a message nobody can prove arrived."),
		"",
		"## What you do",
		"",
		"1. Finish or reply to anything you hold a claim on. `scan` shows you.",
		"2. Stop your Baton processes when asked.",
		"3. Change your paths to the two above.",
		"4. Start again, and check with:",
		"",
		"```text",
		f"{cli['execute']} --config {destination_config} scan --participant YOU",
		"```",
		"",
		paragraph(
			f"You should see your own queue. `--version` reports "
			f"`{cli['record']['tool']} {cli['record']['product_version']} "
			f"(protocol {cli['record']['protocol_version']})` — the same "
			f"version you have been running."),
		"",
		"## `doctor` was already unhappy, and the move is not why",
		"",
		paragraph(
			f"Before any of this, `doctor` reported {problems} problems on "
			f"this authority. Every one is an external attachment pinned into "
			f"a source repository that has since moved on -- a file whose "
			f"hash changed or whose path is gone. None of them is a database "
			f"problem, and the move neither causes nor cures them. If you run "
			f"`doctor` afterwards and see them, that is what you are looking "
			f"at."),
		"",
		"## If something is wrong",
		"",
		paragraph(
			"The old directory is not deleted. It keeps a `MOVED` file naming "
			"the new location -- one hop, written by hand, not followed by any "
			"client. If you come back later and find it, read it and use the "
			"path it names; ask Slawomir if a hop is missing rather than "
			"guessing or restoring an older mailbox."),
		"",
		"Say so through Baton once you are on the new paths, or to Slawomir",
		"directly if you cannot get there.",
		"",
		"## For the record",
		"",
		"```text",
		f"mailbox            {mailbox_dir}",
		f"                   protocol {identity['protocol_version']}, "
		f"namespace {identity['namespace']}",
		f"baton              {cli['release']}",
		f"                   {cli['record']['artifact_sha256']}",
		f"baton-tui          {tui['release']}",
		f"                   {tui['record']['artifact_sha256']}",
		f"candidate          {cli['record']['provenance']['set_digest']}",

		f"participants       {len(people)} accepted, config generation "
		f"{generation}",
		f"config digest      {config_digest}",
		"```",
		"",
	]
	return "\n".join(lines)


def audience(source_config: str) -> list[str]:
	"""Everyone who must receive it: the ACCEPTED participants, frozen at the
	moment the guide is generated so the broadcast and the directed deliveries
	cannot disagree about who was included."""
	return _accepted(source_config)[0]


def accepted_digest(source_config: str) -> str:
	"""The config digest the audience was taken from. Publication re-reads it
	and refuses if it moved: a `regen` between generating and sending would
	mean the frozen audience is no longer the audience."""
	return _accepted(source_config)[1]


def main(argv=None) -> int:
	import argparse

	parser = argparse.ArgumentParser(
		prog="migration_guide",
		description="Generate the deployment-specific migration guide")
	parser.add_argument("destination", help="the deployment root")
	parser.add_argument("--config", required=True,
	                    help="the CURRENT accepted config, for the audience")
	parser.add_argument("--mailbox", required=True,
	                    help="the destination mailbox directory")
	parser.add_argument("--output", required=True,
	                    help="exact path to write; never replaces differing bytes")
	args = parser.parse_args(argv)
	try:
		body = render(args.destination, args.config, args.mailbox)
		people, digest, generation = _accepted(args.config)
		if os.path.lexists(args.output):
			if open(args.output, encoding="utf-8").read() != body:
				raise GuideError(
					f"{args.output} exists and differs; refusing to replace a "
					f"guide that may already have been published")
		else:
			with open(args.output, "x", encoding="utf-8") as handle:
				handle.write(body)
		print(json.dumps({"written": args.output, "bytes": len(body.encode()),
		                  "audience": people, "config_digest": digest,
		                  "config_generation": generation},
		                 indent=2, sort_keys=True))
		return 0
	except (GuideError, deploy.DeployError) as refusal:
		print(f"migration_guide: {refusal}", file=sys.stderr)
		return 1


if __name__ == "__main__":
	sys.exit(main())
