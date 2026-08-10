"""Differential parity: frozen `baton_v6` oracle vs `baton_core`.

Since stage 1A the core is what SHIPS: `bin/baton` and `bin/baton-tui` are
both built from it, and `baton_v6.py` is packaged in neither. It stays in the
tree for one job -- to be the reference for what the CLI did before adoption,
so a behaviour change can still be caught by something that did not change
with it.

The danger was never duplication itself. It is a defect fixed in BOTH copies,
after which the two agree with each other about the wrong answer and the
oracle has quietly stopped being an oracle. So fixes land in `baton_core`
only, the oracle stays byte-identical, and every deliberate divergence is
recorded here rather than reconciled by editing the reference.

These tests drive both implementations through the same operations on fresh
equivalent instances and compare what a caller can actually observe: delivery
JSON, error text and exit codes, and `doctor` output.
"""

from __future__ import annotations

import json
import os
import re

import pytest

import baton_v6 as oracle
import baton_core as core


IMPLS = (("oracle", oracle), ("core", core))


def _delivery_of(impl, store, claim):
	"""The oracle exposes the delivery builder privately; the core promotes it
	to public API. Comparing them is the point, so resolve either spelling."""
	builder = getattr(impl, "delivery_for", None) or impl._delivery
	return builder(store, claim)


def _config(tmp_path, name):
	# Separate instance DIRECTORIES: the authority lives beside its config, so
	# two configs in one directory would collide on mailbox.sqlite3.
	home = tmp_path / name
	home.mkdir()
	root = home / "root"
	root.mkdir()
	(root / "EVIDENCE.md").write_bytes(b"pinned evidence\n")
	path = str(home / "baton.json")
	with open(path, "w") as handle:
		json.dump({
			"config_version": 1,
			"protocol_version": 9,
			"generation": 1,
			"mailbox": {"name": "parity"},
			"participants": {"acme.reviewer": {}, "acme.implementer": {},
			                 "hq.lead": {"capabilities": ["recovery", "config"]}},
			"roots": {"src": str(root)},
			"retention_days": 90,
		}, handle)
	return path, root


_VARIES = ("uuid", "id", "seq", "config_sha256")
_HEX_ID_RE = re.compile(r"\b[0-9a-f]{32}\b")


def _scrub(value, home=None):
	"""Normalize what MUST differ between two independent runs, and nothing
	else.

	Ids, timestamps and the instance uuid are blanked -- two instances cannot
	share them. Absolute paths are REWRITTEN rather than blanked, because the
	two runs live in different directories but their internal structure is
	exactly what parity is about: `<home>/root/EVIDENCE.md` differing from
	`<home>/root/EVIDENCE.md` would be a real divergence, and blanking would
	hide it."""
	if isinstance(value, dict):
		out = {}
		for key, item in value.items():
			if key in _VARIES or key.endswith("_id") or key.endswith("_ts"):
				out[key] = "<varies>"
			else:
				out[key] = _scrub(item, home)
		return out
	if isinstance(value, list):
		return [_scrub(v, home) for v in value]
	if isinstance(value, str):
		if home:
			value = value.replace(str(home), "<instance>")
		# Ids also appear INSIDE diagnostics ("claim 'a1b2...' belongs to ...").
		# Error text is part of the contract and must be compared, so normalize
		# the ids within it rather than skipping the field.
		value = _HEX_ID_RE.sub("<id>", value)
	return value


def _run(impl, config_path, root):
	"""One scripted session. Returns everything a caller could observe."""
	observed = {}
	impl.init_instance(config_path)
	with impl.open_instance(config_path) as store:
		mid = store.send("acme.reviewer", "acme.implementer", kind="question",
		                 subject="Parity check", thread_id="topic-1", parts=[
			{"content_type": "text/markdown; charset=utf-8", "body": b"# Ask\nWell?\n"},
			{"content_type": "text/markdown; charset=utf-8", "disposition": "attachment",
			 "filename": "EVIDENCE.md", "attach": "src:EVIDENCE.md"},
		])
		observed["scan_pending"] = store.scan("acme.implementer")
		claim = store.claim("acme.implementer", message_id=mid)
		observed["delivery"] = _delivery_of(impl, store, claim)
		observed["scan_claimed"] = store.scan("acme.implementer")
		observed["reply"] = store.reply(claim["claim_id"], participant="acme.implementer",
		                                kind="answer", body=b"Yes.\n")
		observed["reply_retry"] = store.reply(claim["claim_id"], participant="acme.implementer",
		                                      kind="answer", body=b"Yes.\n")
		# Errors are part of the contract: text and exit code both compared.
		for label, fn in (
			("retry_mismatch", lambda: store.reply(
				claim["claim_id"], participant="acme.implementer", kind="answer",
				body=b"No.\n")),
			("foreign_owner", lambda: store.close_claim(
				claim["claim_id"], participant="acme.reviewer")),
			("bad_subject", lambda: store.send(
				"acme.reviewer", "acme.implementer", kind="q", subject="two\nlines",
				body=b"x")),
			("notice_external", lambda: store.send_notice(
				"hq.lead", kind="n", parts=[{"content_type": "text/plain; charset=utf-8",
				                             "disposition": "attachment",
				                             "attach": "src:EVIDENCE.md"}])),
		):
			try:
				fn()
				observed[label] = "NO ERROR"
			except impl.BatonError as exc:
				observed[label] = {"msg": str(exc), "exit": exc.exit_code}
		nid = store.send_notice("hq.lead", kind="announcement",
		                        subject="Parity notice", body=b"broadcast\n")
		observed["see"] = store.see("acme.implementer")
		observed["notice_id_kind"] = nid is not None
	observed["doctor"] = impl.doctor(config_path)
	observed["dump_tables"] = sorted(impl.dump(config_path))
	return _scrub(observed, os.path.dirname(config_path))


# Deliberate, authorized core-only additions. The oracle is frozen, so the
# core moving ahead is EXPECTED -- but only here, named, with a reason. An
# unlisted divergence still fails, which is the whole point: this is a record
# of decisions, not a mute button.
ALLOWED_DIVERGENCE = {
	"delivery": (
		"core adds a manifest `address` to each  delivered part, making the "
		"envelope self-addressing: a console reading a message can name the "
		"part it wants to materialize without recomputing positions from the "
		"tree, and `materialize --part` takes exactly that string. Additive."),
	"scan_claimed": (
		"core adds `created_ts` to claimed rows. The console sorts ONE list "
		"containing pending rows, claimed rows and notices, and needs a "
		"single clock across all three; the oracle's claimed rows carry only "
		"`claimed_ts`. Authorized under 'richer stable inbox rows'."),
}


def test_oracle_and_core_are_observationally_identical(tmp_path):
	results = {}
	for name, impl in IMPLS:
		config_path, root = _config(tmp_path, name)
		results[name] = _run(impl, config_path, root)
	a, b = results["oracle"], results["core"]
	for key in sorted(set(a) | set(b)):
		if key in ALLOWED_DIVERGENCE:
			continue
		assert a.get(key) == b.get(key), f"unrecorded divergence in {key!r}"


@pytest.mark.parametrize("key", sorted(ALLOWED_DIVERGENCE))
def test_recorded_divergences_are_still_real(tmp_path, key):
	"""A divergence that has quietly gone away should be REMOVED from the
	allowlist, not left standing as a permanent exemption that would hide the
	next one."""
	results = {}
	for name, impl in IMPLS:
		config_path, root = _config(tmp_path, name)
		results[name] = _run(impl, config_path, root)
	assert results["oracle"].get(key) != results["core"].get(key), (
		f"{key!r} no longer diverges; drop it from ALLOWED_DIVERGENCE")


def test_divergence_is_additive_only(tmp_path):
	"""Core may ADD to a row shape. It must not drop or change a field the
	oracle produced.

	The CLI HAS adopted the core -- stage 1A -- so this is no longer a
	precaution about a hypothetical future: a silent removal here is a silent
	removal in the released executable. The oracle remains the reference for
	what the behaviour WAS at adoption, which is the only thing that can catch
	a drop after it."""
	results = {}
	for name, impl in IMPLS:
		config_path, root = _config(tmp_path, name)
		results[name] = _run(impl, config_path, root)
	for old_row, new_row in zip(results["oracle"]["scan_claimed"]["claimed"],
	                            results["core"]["scan_claimed"]["claimed"]):
		for field, value in old_row.items():
			assert field in new_row, f"core dropped {field!r} from a claimed row"
			assert new_row[field] == value, f"core changed {field!r}"


def test_core_reports_its_own_contract(tmp_path):
	"""The core declares an API version separate from the protocol, so a front
	end can state what it was built against."""
	versions = core.core_versions()
	assert versions["protocol_version"] == oracle.PROTOCOL_VERSION
	assert isinstance(versions["core_api_version"], int)


def test_the_tool_version_has_deliberately_left_the_oracle_behind():
	"""The one version the core and the oracle are ALLOWED to disagree on, and
	the disagreement is asserted rather than tolerated.

	`tool_version` describes the CLI SURFACE. The core's four authoring verbs
	gained `--part` and `--references`, so the core is 5.2.0; the oracle is
	frozen and stays 5.1.0 because a frozen artifact does not grow a surface.

	Protocol version and behavioural parity are NOT relaxed by this — they are
	asserted next door and throughout this file. Recorded as an equality
	against both literals rather than a `!=`, so that when either moves again
	this test states what happened instead of silently continuing to pass."""
	assert oracle.TOOL_VERSION == "5.1.0", "the frozen oracle must not be re-versioned"
	assert core.core_versions()["tool_version"] == "5.2.0"
	assert core.core_versions()["protocol_version"] == oracle.PROTOCOL_VERSION


def test_oracle_stays_frozen():
	"""`baton_v6.py` is the parity oracle for the whole scaffolding period. If
	this fails, someone edited the oracle -- fix `baton_core` instead, and
	record the divergence deliberately."""
	import hashlib
	here = os.path.dirname(os.path.abspath(__file__))
	digest = hashlib.sha256(open(os.path.join(here, "baton_v6.py"), "rb").read()).hexdigest()
	assert digest == "6d9ffe8c8021bc692b3b474a8dc18cb468c5ce3b7a67d16e3cb838124e0f2671", (
		"baton_v6.py changed while frozen as the differential parity oracle")
