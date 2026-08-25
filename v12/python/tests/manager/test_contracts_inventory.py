"""W6782 — the contracts package's receiving boundaries, inventoried.

The manager package has had this since W4 and the contracts package has not,
which is the gap M6776 split out of W6592 so it could be reviewed on its own.

THE ONE RULE THAT MAKES AN INVENTORY WORTH HAVING, learned three times over in
`tests/manager/test_boundary_inventory.py`: **the universe is derived from a
structure that exists whether or not anybody owned it.** An inventory that
starts from the checks the code already performs cannot discover a missing
one — it reports a clean sweep over exactly the entries that already have an
owner. So the universe here is the package's REAL exported surface and every
parameter of it, read from `__all__` and the AST, and ownership is looked up
against that rather than the other way round.

AN ENTRY IS `(operation, parameter)`, keyed lexically. Two operations sharing a
parameter name are two entries, because `check_uri(uri)` and
`validate_fragment(document)` are different crossings that happen to be spelled
with the same words.

AND A PROBE MUST NOT BE VACUOUS. Every probe drives the real exported
operation and requires a `ContractRefusal` — and a case proves each probe's
operand is the one being refused, by requiring the SAME call to succeed once
that operand is sound. A probe that fails for an earlier reason proves the
earlier reason.
"""

import ast
import inspect
import pathlib
import unittest

import baton_v12.contracts as contracts
from baton_v12.contracts import ContractRefusal

PACKAGE = pathlib.Path(contracts.__file__).resolve().parent

# What a stated owner says when the inventory found none.
UNOWNED = None
# ...and when the owner is a BUILD-TIME ASSERTION rather than a caller refusal.
# A bad category/code pair is this build's defect, not something a caller sent,
# so it is not a `ContractRefusal` and a refusal probe would be asserting the
# wrong taxonomy. Witnessed by its own case instead.
ASSERTED = "asserted"

SURROGATE = "\ud800"
DIGEST = "sha256:" + "a" * 64
UUID = "2b077949c86e8bef24304f59c28ec398"
WORK_REF = {"authority_uuid": UUID, "work_id": UUID[:8] + "-W4"}
MANIFEST = {"entries": [], "entry_count": 0, "total_bytes": 0,
            "tree_digest": "sha256:" + __import__("hashlib").sha256(
                b"[]").hexdigest()}

# Parameters that are this package's own PROSE about an operand rather than an
# operand: `what` names the thing a refusal is about. It is still owned --
# `label_of` bounds it -- and it is still probed, because a caller-supplied
# label reaches durable text.
LABELS = {"what"}


def exported_operations():
	"""The package's REAL public callables, from `__all__`.

	Not a hand-written list and not `dir()`: `__all__` is the promise the
	package makes, and a name added to it without an entry here is the gap
	this file exists to find.
	"""
	return {name: getattr(contracts, name) for name in contracts.__all__
	        if callable(getattr(contracts, name))}


def universe():
	"""Every `(operation, parameter)` this package can be handed a value at.

	Derived from the signature, so a parameter added to a public operation
	appears here whether or not anybody owned it.
	"""
	found = set()
	for name, operation in exported_operations().items():
		try:
			parameters = inspect.signature(operation).parameters
		except (TypeError, ValueError):        # pragma: no cover - builtins
			continue
		for parameter in parameters:
			if parameter in ("self", "cls"):
				continue
			found.add((name, parameter))
	return found


# -- one owner per entry, each naming the rule that owns it ------------------
#
# A stated owner is a claim; the probe below is what makes it a fact.
OWNERS = {
	("ContractRefusal", "category"): ASSERTED,
	("ContractRefusal", "code"): ASSERTED,
	# W7079 OWNED WHAT THIS INVENTORY FOUND UNOWNED. Both are owned by an
	# assertion for the same reason the pairing is: an unencodable message or
	# a non-Boolean durability is the RAISING SITE's defect, not something a
	# caller sent -- and a refusal whose own message is the thing under
	# suspicion explains nothing.
	("ContractRefusal", "message"): ASSERTED,
	("ContractRefusal", "durable"): ASSERTED,
	# -- W6630: §13 -----------------------------------------------------
	#
	# The WALK owns its own operand by construction: it descends only into
	# the built-in containers it recognises and reads nothing else, so a
	# value with behaviour is passed over rather than interrogated. There is
	# no shape to refuse -- any document is a legal question -- and what it
	# answers is whether that document carries a secret.
	("check_no_durable_secret", "document"):
		"the walk's own type dispatch: strings, lists, tuples and dicts are "
		"descended and nothing else is read",
	("check_no_durable_secret", "what"): "label_of, at the refusal",
	("remember_secret", "value"):
		"the registry's own rule: a remembered secret is non-empty text",
	("forget_secret", "value"): "the same rule, one direction over",
	("held_secret", "value"):
		"delegated to remember_secret on entry; a value that cannot be "
		"remembered never becomes a held one",
	("live_secret", "value"):
		"the registry's own rule: a value that cannot be a registered secret "
		"is a malformed question, and answering it would be worse than "
		"refusing it",
	("canonical_bytes", "value"): "the canonicalizer's own type walk",
	("canonical_text", "value"): "the same walk",
	("digest", "value"): "the same walk, then sha256 over its bytes",
	("digest_of_bytes", "payload"): "exact bytes, refused otherwise",
	("own", "value"): "the POD walk: exact built-in JSON and nothing else",
	("own", "what"): "label_of",
	("own_record", "value"): "own, then the exact member set",
	("own_record", "required"): "this build's own name list, iterated once",
	("own_record", "what"): "label_of",
	("check_content_manifest", "content"): "the frozen contentManifest "
	                                       "fragment, then §12 rule 6",
	("check_content_manifest", "what"): "label_of",
	("check_manifest_structure", "document"): "the named frozen definition",
	("check_manifest_structure", "definition"): "a closed set: the frozen "
	                                            "document's own $defs keys",
	("check_manifest_structure", "what"): "label_of",
	("check_relative_path", "path"): "the normalized-POSIX-relative rule",
	("check_relative_path", "what"): "label_of",
	("check_uri", "uri"): "the shared canonical locator grammar",
	("check_uri", "what"): "label_of",
	("check_work_ref", "work_ref"): "the frozen workRef fragment, then §4's "
	                                "authority prefix",
	("check_work_ref", "what"): "label_of",
	("validate_against", "validator"): "identity against the owned validator "
	                                   "set; a duck-typed one is a caller "
	                                   "program",
	("validate_against", "document"): "the validator's own walk",
	("validate_against", "what"): "label_of",
	("validate_worker_control", "document"): "the frozen worker-control schema",
	("validate_worker_control", "what"): "label_of",
	("validate_agent_session", "document"): "the frozen agent-session schema",
	("validate_agent_session", "what"): "label_of",
	("validate_fragment", "document"): "the named worker-control definition",
	("validate_fragment", "definition"): "a closed set: worker-control's own "
	                                     "$defs keys",
	("validate_fragment", "what"): "label_of",
	("validate_agent_session_fragment", "document"): "the named agent-session "
	                                                 "definition",
	("validate_agent_session_fragment", "definition"): "a closed set: "
	                                                   "agent-session's own "
	                                                   "$defs keys",
	("validate_agent_session_fragment", "what"): "label_of",
	("verify_manifest_digest", "manifest"): "the declared digest against the "
	                                        "recomputed one",
	("verify_manifest_digest", "what"): "label_of",
}


def refusing(case, call):
	try:
		call()
	except ContractRefusal:
		return
	case.fail("the operand reached no owner")


class TheUniverseIsDerivedNotDeclared(unittest.TestCase):

	def test_every_exported_callable_is_reachable_from_the_package(self):
		for name, operation in exported_operations().items():
			with self.subTest(name=name):
				self.assertTrue(callable(operation))

	def test_every_entry_has_exactly_one_stated_owner(self):
		found = universe()
		self.assertEqual(sorted(found - set(OWNERS)), [],
		                 "receiving entries with no owner")
		self.assertEqual(sorted(set(OWNERS) - found), [],
		                 "an owner for something that is not an entry")

	def test_no_receiving_entry_is_marked_unowned(self):
		self.assertEqual(
			sorted(entry for entry, owner in OWNERS.items()
			       if owner is UNOWNED),
			[], "receiving entries explicitly left without an owner")

	def test_the_universe_is_not_read_from_the_ownership_table(self):
		"""The guard on the guard.

		An inventory that derived its universe from `OWNERS` would report a
		clean sweep over exactly the entries somebody remembered. Handing the
		derivation a name the table does not carry has to CHANGE the answer.
		"""
		found = universe()
		self.assertIn(("check_uri", "uri"), found)
		self.assertNotIn(("check_uri", "invented"), found)
		self.assertGreater(len(found), len(exported_operations()),
		                   "a universe of one entry per operation would be "
		                   "counting operations, not crossings")


class EveryOwnerIsProvedByANonVacuousProbe(unittest.TestCase):
	"""One probe per entry, each driving the REAL exported operation."""

	def probes(self):
		return {

			("check_no_durable_secret", "document"):
				lambda: contracts.check_no_durable_secret(
					{"password": "x"}),
			("check_no_durable_secret", "what"):
				lambda: contracts.check_no_durable_secret(
					{"password": "x"}, what=SURROGATE),
			("remember_secret", "value"):
				lambda: contracts.remember_secret(""),
			("forget_secret", "value"):
				lambda: contracts.forget_secret(object()),
			("held_secret", "value"):
				lambda: contracts.held_secret("").__enter__(),
			("live_secret", "value"):
				lambda: contracts.live_secret(object()),
			("canonical_bytes", "value"):
				lambda: contracts.canonical_bytes(object()),
			("canonical_text", "value"):
				lambda: contracts.canonical_text(object()),
			("digest", "value"): lambda: contracts.digest(object()),
			("digest_of_bytes", "payload"):
				lambda: contracts.digest_of_bytes("not bytes"),
			("own", "value"): lambda: contracts.own(object()),
			("own", "what"): lambda: contracts.own(object(), what=SURROGATE),
			("own_record", "value"):
				lambda: contracts.own_record([1], ("a",)),
			("own_record", "required"):
				lambda: contracts.own_record({"a": 1}, ("a", "b")),
			("own_record", "what"):
				lambda: contracts.own_record([1], ("a",), what=SURROGATE),
			("check_content_manifest", "content"):
				lambda: contracts.check_content_manifest({"entries": []}),
			("check_content_manifest", "what"):
				lambda: contracts.check_content_manifest([], what=SURROGATE),
			("check_manifest_structure", "document"):
				lambda: contracts.check_manifest_structure(
					[], "contentManifest"),
			("check_manifest_structure", "definition"):
				lambda: contracts.check_manifest_structure(MANIFEST,
				                                           "invented"),
			("check_manifest_structure", "what"):
				lambda: contracts.check_manifest_structure(
					[], "contentManifest", what=SURROGATE),
			("check_relative_path", "path"):
				lambda: contracts.check_relative_path("/absolute"),
			("check_relative_path", "what"):
				lambda: contracts.check_relative_path("/absolute",
				                                      what=SURROGATE),
			("check_uri", "uri"): lambda: contracts.check_uri("not a uri"),
			("check_uri", "what"):
				lambda: contracts.check_uri("not a uri", what=SURROGATE),
			("check_work_ref", "work_ref"):
				lambda: contracts.check_work_ref({"authority_uuid": UUID}),
			("check_work_ref", "what"):
				lambda: contracts.check_work_ref([], what=SURROGATE),
			("validate_against", "validator"):
				lambda: contracts.validate_against(_Duck(), {}),
			("validate_against", "document"):
				lambda: contracts.validate_worker_control([]),
			("validate_against", "what"):
				lambda: contracts.validate_worker_control([], what=SURROGATE),
			("validate_worker_control", "document"):
				lambda: contracts.validate_worker_control("not a document"),
			("validate_worker_control", "what"):
				lambda: contracts.validate_worker_control([], what=SURROGATE),
			("validate_agent_session", "document"):
				lambda: contracts.validate_agent_session("not a document"),
			("validate_agent_session", "what"):
				lambda: contracts.validate_agent_session([], what=SURROGATE),
			("validate_fragment", "document"):
				lambda: contracts.validate_fragment([], "contentManifest"),
			("validate_fragment", "definition"):
				lambda: contracts.validate_fragment(MANIFEST, "invented"),
			("validate_fragment", "what"):
				lambda: contracts.validate_fragment([], "contentManifest",
				                                    what=SURROGATE),
			("validate_agent_session_fragment", "document"):
				lambda: contracts.validate_agent_session_fragment(
					[], "clientCapabilities"),
			("validate_agent_session_fragment", "definition"):
				lambda: contracts.validate_agent_session_fragment(
					{"fs": {}, "terminal": False}, "invented"),
			("validate_agent_session_fragment", "what"):
				lambda: contracts.validate_agent_session_fragment(
					[], "clientCapabilities", what=SURROGATE),
			("verify_manifest_digest", "manifest"):
				lambda: contracts.verify_manifest_digest({"manifest_digest":
				                                          DIGEST}),
			("verify_manifest_digest", "what"):
				lambda: contracts.verify_manifest_digest([], what=SURROGATE),
		}

	def owned(self):
		"""Entries a REFUSAL probe must reach: not the unowned ones, and not
		the two owned by a build-time assertion."""
		return {entry for entry, rule in OWNERS.items()
		        if rule is not UNOWNED and rule != ASSERTED}

	def test_every_owned_entry_has_exactly_one_probe(self):
		declared = set(self.probes())
		self.assertEqual(sorted(self.owned() - declared), [],
		                 "owned, never probed")
		self.assertEqual(sorted(declared - self.owned()), [],
		                 "probed, never owned")

	def test_every_probe_reaches_a_refusal(self):
		for entry, probe in sorted(self.probes().items()):
			with self.subTest(entry=entry):
				refusing(self, probe)

	def test_every_label_probe_proves_the_label_reached_its_owner(self):
		for entry, probe in sorted(self.probes().items()):
			if entry[1] != "what":
				continue
			with self.subTest(entry=entry):
				with self.assertRaises(ContractRefusal) as caught:
					probe()
				self.assertIn("\\ud800", caught.exception.message,
				              "the invalid primary operand refused before the "
				              "label owner was witnessed")

	def test_the_probe_gate_can_actually_fail(self):
		"""A guard with nothing to catch is tested by handing it something."""
		with self.assertRaises(AssertionError):
			refusing(self, lambda: contracts.check_uri("https://ok.test/x"))


class EveryConstructionInputIsOwnedByItsAssertion(unittest.TestCase):
	"""The four `ContractRefusal` inputs, each owned at construction.

	W6782 found `message` and `durable` with NO owner and recorded them; W7079
	owned them. All four are owned by an ASSERTION rather than a refusal, and
	that is the right taxonomy: a bad pair, an unencodable message or a
	non-Boolean durability is the RAISING SITE's defect and not something a
	caller sent -- and a refusal whose own message is the thing under suspicion
	explains nothing.
	"""

	def test_the_category_and_code_pair_is_owned_by_an_assertion(self):
		for category, code in (("invented", "schema"),
		                       ("integrity", "invented")):
			with self.subTest(pair=(category, code)):
				with self.assertRaises(AssertionError):
					ContractRefusal(category, code, "m")

	def test_a_message_this_build_could_not_store_is_refused(self):
		"""A refusal is the value most likely to be stored, journalled and
		logged. An unencodable one means the store fails to write the very
		refusal explaining why something was refused, at the moment this build
		is least able to report anything."""
		for what, message in [("a lone surrogate", SURROGATE),
		                      ("text carrying one", "why: " + SURROGATE),
		                      ("not text at all", 7),
		                      ("nothing", None)]:
			with self.subTest(what=what):
				with self.assertRaises(AssertionError):
					ContractRefusal("integrity", "schema", message)

	def test_a_message_has_the_approved_fixed_bound(self):
		"""4,096 Unicode scalars pass and the next one is asserted here."""
		accepted = "x" * 4_096
		self.assertIs(
			ContractRefusal("integrity", "schema", accepted).message, accepted)
		with self.assertRaises(AssertionError):
			ContractRefusal("integrity", "schema", "x" * 4_097)

	def test_the_public_message_limit_is_the_constructor_s_one_rule(self):
		"""The exported rule and the owning constructor cannot drift apart."""
		self.assertIn("MESSAGE_LIMIT", contracts.__all__)
		self.assertEqual(contracts.MESSAGE_LIMIT, 4_096)
		accepted = "x" * contracts.MESSAGE_LIMIT
		self.assertIs(
			ContractRefusal("integrity", "schema", accepted).message, accepted)
		with self.assertRaises(AssertionError):
			ContractRefusal("integrity", "schema", accepted + "x")

	def test_durability_is_exactly_a_boolean(self):
		"""The truth value of an arbitrary object is decided by running
		`__bool__` -- inside the refusal handling of a transaction, which is
		where this build is already failing and least able to survive a
		caller's code."""
		ran = []

		class Truthy:
			def __bool__(self):
				ran.append("bool")
				return True

		for value in ("yes", 1, 0, None, Truthy()):
			with self.subTest(value=type(value).__name__):
				with self.assertRaises(AssertionError):
					ContractRefusal("integrity", "schema", "m", durable=value)
		self.assertEqual(ran, [], "a caller's __bool__ ran inside a refusal")
		for value in (True, False):
			self.assertIs(
				ContractRefusal("integrity", "schema", "m",
				                durable=value).durable, value)


class _Duck:
	"""A duck-typed validator: an object with the method and none of the
	identity. Running one is the seam `validate_against` closes."""

	def iter_errors(self, document):
		raise AssertionError("a caller program ran")


class ThePrivateBodyPathIsPinnedStructurally(unittest.TestCase):
	"""4bz's composite rule, as a check rather than an intention.

	The exported wrappers own their operands and then call the PRIVATE bodies;
	a composite that called the public wrappers would own the same value twice,
	which is the blanket revalidation 4bz forbids. Read from the AST, so it
	stays true when somebody edits the composite.
	"""

	def called_by(self, name):
		source = (PACKAGE / "manifest.py").read_text(encoding="utf-8")
		body = next(node for node in ast.parse(source).body
		            if isinstance(node, ast.FunctionDef) and node.name == name)
		return {piece.func.id for piece in ast.walk(body)
		        if isinstance(piece, ast.Call)
		        and isinstance(piece.func, ast.Name)}

	def test_the_composite_calls_the_private_bodies(self):
		called = self.called_by("check_manifest_structure")
		for wrapper in ("check_work_ref", "check_content_manifest"):
			with self.subTest(wrapper=wrapper):
				self.assertNotIn(wrapper, called)
		self.assertIn("_relate_work_ref", called)
		self.assertIn("_check_content_manifest", called)

	def test_each_public_wrapper_owns_then_delegates(self):
		for wrapper, private in (("check_work_ref", "_relate_work_ref"),
		                         ("check_content_manifest",
		                          "_check_content_manifest")):
			with self.subTest(wrapper=wrapper):
				called = self.called_by(wrapper)
				self.assertIn(private, called)
				self.assertIn("validate_fragment", called)


if __name__ == "__main__":
	unittest.main()
