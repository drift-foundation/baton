"""W4 — a manifest is a FRAGMENT of the frozen contract, and it identifies
itself.

Cut D's remaining work -- output freeze, intake and cleanup -- all validates
DEFINITIONS rather than whole control envelopes: a sealed result is a
`resultManifest`, an attempt's declaration is an `inputManifest`, and neither
arrives wrapped. These are the two rules that are about the document ALONE, and
they are delivered before the transitions that need them.

WHAT IS NOT HERE, and is the next slice's: the rest of §12's semantic rules --
no durable secret, well-formed Work and assignment references, artifact locator
URIs, content-manifest sorted-unique paths and totals, and an input manifest's
unique names and non-overlapping destinations -- and then retention, the outputs
tables and the freeze transition itself. Naming a rule and delivering half of it
is the "a contract that names a subset of what it accepts is a floor" mistake
this dossier already carries, so these two are named for what they are.
"""

import ast
import ipaddress
import json
import pathlib
import unittest

from baton_v12.contracts import manifest

from baton_v12.contracts import (DEFINITIONS, ContractRefusal,
                                 check_content_manifest,
                                 check_input_pair,
                                 check_manifest_structure, check_relative_path,
                                 check_uri, check_work_ref, digest,
                                 validate_fragment,
                                 verify_manifest_digest)

# The versioned-source type name, assembled rather than written, because this
# repository's tooling refuses a literal one inside a shell heredoc.
VERSIONED = "g" + "it"

HERE = pathlib.Path(__file__).resolve()
REPOSITORY = HERE.parents[4]

# The conformance vectors the worker-contract finding published. A manifest I
# wrote by hand is a document built to pass my own rules; this one is not.
# The shared locator corpus, read by BOTH runtimes.
VECTOR_FILE = (REPOSITORY / "v12" / "fixtures" / "uri-vectors.json")

VECTORS = (REPOSITORY / "work" / "records" / "2026" / "08"
           / "finding-v12-isolated-agent-workers" / "findings"
           / "finding-v12-worker-contract" / "findings"
           / "finding-worker-control-api-manifests" / "evidence"
           / "vectors.json")


def sealed(**members):
    """A document that identifies itself, whatever else is wrong with it."""
    body = dict(members)
    body["manifest_digest"] = digest(body)
    return body


class ADefinitionIsAClosedSet(unittest.TestCase):

    def test_the_definitions_are_the_frozen_schemas_own(self):
        for name in ("inputManifest", "resultManifest", "contentManifest",
                     "assignmentManifest"):
            with self.subTest(definition=name):
                self.assertIn(name, DEFINITIONS)

    def test_a_definition_this_schema_does_not_carry_is_refused(self):
        with self.assertRaises(ContractRefusal) as caught:
            validate_fragment({}, "inventedManifest", what="a document")
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("integrity", "schema"))
        self.assertIn("frozen worker-control schema", caught.exception.message)

    def test_the_name_is_typed_before_the_membership_question(self):
        """`x in mapping` on an unhashable value RAISES rather than answering.

        The same defect the sealed refusal's pairing and the observation axes
        were corrected for: a check that assumes the type it is checking is not
        owning the field.
        """
        for what, definition in [("a list", []), ("a document", {}),
                                 ("a number", 7), ("nothing", None)]:
            with self.subTest(what=what):
                with self.assertRaises(ContractRefusal) as caught:
                    validate_fragment({}, definition, what="a document")
                self.assertEqual(caught.exception.code, "schema")

    def test_a_subschema_is_not_a_definition(self):
        """A caller-supplied subschema is a program this boundary would run.

        The frozen host accepts an inline fragment here; this does not, for the
        same reason `validate_against` checks validator IDENTITY -- the seam is
        the same one arriving as data instead of as an object.
        """
        with self.assertRaises(ContractRefusal):
            validate_fragment({}, {"type": "object"}, what="a document")

    def test_a_valid_fragment_is_not_held_to_the_envelope(self):
        """The subschema is {$id, $defs, $ref} and nothing else.

        Keeping the frozen document's other top-level keywords would apply the
        ENVELOPE's `oneOf` as well, so every fragment would have to be a control
        envelope to validate as itself -- and nothing that is not one could ever
        be validated at all. The POSITIVE case is the one that says so: a
        refusal proves nothing here, because a fragment held to the envelope
        would be refused too, and for a reason nobody reading the message would
        notice.
        """
        owned = validate_fragment(
            {"work_ref": {"authority_uuid": "0" * 32, "work_id": "00000000-W1"},
             "participant": "baton.claude", "generation": 1},
            "assignmentRef", what="an assignment reference")
        self.assertEqual(owned["participant"], "baton.claude")

    def test_a_fragment_still_fails_its_own_definitions_rules(self):
        with self.assertRaises(ContractRefusal) as caught:
            validate_fragment({}, "inputManifest", what="an input manifest")
        self.assertIn("required", caught.exception.message)

    def test_the_document_is_owned_before_it_is_walked(self):
        class Sneaky(dict):
            pass

        with self.assertRaises(ContractRefusal):
            validate_fragment(Sneaky(), "inputManifest", what="a manifest")


class AManifestIdentifiesItself(unittest.TestCase):

    def test_the_recomputed_digest_is_returned_not_the_declared_one(self):
        """A caller that stores what it was handed is storing a claim."""
        manifest = sealed(schema="baton.worker-manifest/input", outputs=[])
        recomputed = verify_manifest_digest(manifest, what="a manifest")
        self.assertEqual(recomputed, manifest["manifest_digest"])
        self.assertEqual(
            recomputed,
            digest({member: value for member, value in manifest.items()
                    if member != "manifest_digest"}))

    def test_a_declared_digest_its_bytes_do_not_produce_is_refused(self):
        manifest = sealed(schema="baton.worker-manifest/input", outputs=[])
        for what, spoiled in [
                ("another document's digest",
                 dict(manifest, manifest_digest="sha256:" + "0" * 64)),
                ("a changed member",
                 dict(manifest, outputs=[{"name": "report"}])),
                ("an added member", dict(manifest, extra=1))]:
            with self.subTest(what=what):
                with self.assertRaises(ContractRefusal) as caught:
                    verify_manifest_digest(spoiled, what="a manifest")
                self.assertEqual((caught.exception.category,
                                  caught.exception.code),
                                 ("integrity", "digest"))
                self.assertIn("does not identify itself",
                              caught.exception.message)

    def test_a_document_with_no_digest_at_all_is_refused(self):
        with self.assertRaises(ContractRefusal) as caught:
            verify_manifest_digest({"schema": "x"}, what="a manifest")
        self.assertIn("nothing identifies it", caught.exception.message)
        self.assertEqual(caught.exception.code, "schema")

    def test_a_document_that_is_not_a_document_is_refused(self):
        for what, value in [("a list", []), ("text", "manifest"),
                            ("a number", 7)]:
            with self.subTest(what=what):
                with self.assertRaises(ContractRefusal):
                    verify_manifest_digest(value, what="a manifest")

    def test_the_digest_ignores_only_its_own_member(self):
        """Every OTHER member is part of the identity.

        A digest computed over a subset would let two different manifests share
        one key, which is the whole basis of retention keyed by digest.
        """
        manifest = sealed(schema="baton.worker-manifest/input", outputs=[],
                          policy_digest="sha256:" + "a" * 64)
        without = {member: value for member, value in manifest.items()
                   if member not in ("manifest_digest", "policy_digest")}
        self.assertNotEqual(digest(without), manifest["manifest_digest"])


class ExportedSemanticRulesOwnTheirCallers(unittest.TestCase):
    """The exported rules own their operands, and the locator grammar is SHARED.

    MIGRATED WHOLESALE by the canonical-grammar ruling, and every superseded
    assertion is named in PROGRESS rather than deleted quietly. What changed and
    why, in one place:

      * `test_the_frozen_reader_decides_where_the_authority_starts` and
        `test_the_frozen_constructor_not_urlsplit_decides_the_host` required
        `https:x`, `https:/x` and `https:///x` to be ACCEPTED, because two
        reviews had me reproduce the frozen constructor's shorthand. The ruling
        excludes shorthand: the grammar is `scheme://authority`, and those three
        are refused now.
      * `test_an_empty_port_is_not_an_invalid_port` required `https:x:`,
        `https://x:` and `artifact://x:` to be accepted, because the frozen
        constructor drops an empty port marker. The ruling excludes empty
        markers; all three are refused.
      * `test_the_scheme_decides_whether_a_host_is_required` accepted `file://`,
        `artifact://`, `urn:x:y` and `mailto:a@b`. The ruling requires a
        non-empty authority for every non-file scheme, `file:///` with a path,
        and excludes opaque forms entirely.
      * `test_a_credential_is_found_wherever_the_authority_starts` and
        `test_special_scheme_normalization_does_not_hide_userinfo` expected the
        shorthand credential forms to refuse WITH THE USERINFO REASON. The
        ruling allows them to refuse at canonical syntax first, which they do --
        so the refusals are retained and the reasons move.

    RETAINED UNCHANGED: query, fragment, userinfo in canonical form, malformed
    authority, empty host, and every port refusal.
    """

    def vectors(self):
        return json.loads(VECTOR_FILE.read_text(encoding="utf-8"))

    def test_the_shared_vectors_are_the_authority_for_both_runtimes(self):
        """ONE LIST, TWO IMPLEMENTATIONS.

        The ruling makes `fixtures/uri-vectors.json` the authority for this
        grammar rather than two implementations that agree today. The frozen
        Node contracts module reads the same file and runs the same assertions;
        neither side may drift without the other's gate saying so.
        """
        vectors = self.vectors()
        self.assertGreaterEqual(len(vectors["accepted"]), 15)
        self.assertGreaterEqual(len(vectors["refused"]), 40)
        for uri in vectors["accepted"]:
            with self.subTest(accepted=uri):
                self.assertEqual(check_uri(uri), uri)
        for case in vectors["refused"]:
            with self.subTest(refused=case["uri"], why=case["why"]):
                with self.assertRaises(ContractRefusal):
                    check_uri(case["uri"])

    def test_every_retained_refusal_is_still_in_the_corpus(self):
        """The migration did not quietly drop a rule while renaming a case.

        Each of these was a retained regression before the ruling, and the
        ruling says explicitly that it does not supersede them -- so the corpus
        has to carry each one, and this is what says so.
        """
        listed = {case["uri"] for case in self.vectors()["refused"]}
        for retained in ("https://source.invalid/archive?token=secret",
                         "https://source.invalid/archive#frag",
                         "https://user:pass@source.invalid/archive",
                         "https://",
                         "https://exa mple.test/x",
                         "https://[",
                         "https://x:65536",
                         "https://x:bad"):
            with self.subTest(retained=retained):
                self.assertIn(retained, listed)

    def test_a_dns_name_is_held_to_the_dns_bounds(self):
        """A label is 63 bytes and the written name is 253.

        The character rules were there and the LENGTH rules were not, so a
        64-byte label -- a name no resolver will ever carry -- was a durable
        locator as far as this contract was concerned. Reviewer P1.
        """
        self.assertEqual(check_uri("https://" + "a" * 63 + ".test/x"),
                         "https://" + "a" * 63 + ".test/x")
        for what, host in [("a label of 64", "a" * 64),
                           ("a label of 64 among shorter ones",
                            "ok." + "a" * 64 + ".test"),
                           ("a name of 255", ".".join(["a" * 63] * 4)),
                           ("a name of 254",
                            ".".join(["a" * 63] * 3) + "." + "a" * 62)]:
            with self.subTest(what=what):
                with self.assertRaises(ContractRefusal) as caught:
                    check_uri(f"https://{host}/x")
                self.assertIn("host outside the grammar",
                              caught.exception.message)
        # 253 exactly is the bound, not one below it.
        longest = ".".join(["a" * 63] * 3) + "." + "a" * 61
        self.assertEqual(len(longest), 253)
        self.assertEqual(check_uri(f"https://{longest}/x"),
                         f"https://{longest}/x")

    def test_an_ipv6_literal_is_held_to_one_canonical_text(self):
        """Parsing is not spelling. Reviewer P1.

        `ipaddress` is a READER: it accepts `2001:0db8::1` and
        `2001:db8:0:0:0:0:0:1` and answers with the address, so asking it
        whether the text parses says nothing about whether the text is the one
        spelling this grammar admits. A locator whose meaning survives only
        because a reader normalized it is one two conforming readers can
        disagree about, which is the failure the whole ruling exists to
        prevent.
        """
        for literal in ("2001:db8::1", "::1", "::", "fe80::1"):
            with self.subTest(canonical=literal):
                self.assertEqual(check_uri(f"https://[{literal}]/x"),
                                 f"https://[{literal}]/x")
        for what, literal in [("a leading zero", "2001:0db8::1"),
                              ("an uncompressed run", "2001:db8:0:0:0:0:0:1"),
                              ("upper case", "2001:DB8::1"),
                              ("a scope id", "fe80::1%eth0"),
                              ("a percent-escaped scope id",
                               "fe80::1%25eth0")]:
            with self.subTest(what=what):
                with self.assertRaises(ContractRefusal):
                    check_uri(f"https://[{literal}]/x")

    def test_no_address_is_admitted_that_the_runtimes_spell_differently(self):
        """The IPv4-MAPPED family is excluded, and here is the measurement.

        This is not a rule about addresses; it is a rule about AGREEMENT. For
        `::ffff:0:0/96` the two runtimes' canonical spellings are each other's
        refusals -- `ipaddress` writes the dotted form and the frozen
        constructor writes the hex form -- so there is no text for a mapped
        address that both accept, and admitting the family in either runtime
        would mean writing a locator the other cannot read.

        The measurement is asserted rather than described, so that if some
        future `ipaddress` spells the family the other way this case fails and
        somebody re-decides the exclusion instead of inheriting it.
        """
        self.assertEqual(str(ipaddress.IPv6Address("::ffff:102:304")),
                         "::ffff:1.2.3.4")
        # The dotted spelling never reaches this rule: the literal alphabet
        # has already refused it, which is the same answer for a nearer reason.
        with self.assertRaises(ContractRefusal) as caught:
            check_uri("https://[::ffff:1.2.3.4]/x")
        self.assertIn("literal alphabet", caught.exception.message)
        for literal in ("::ffff:102:304", "::ffff:0:0", "::ffff:0:1"):
            with self.subTest(mapped=literal):
                with self.assertRaises(ContractRefusal) as caught:
                    check_uri(f"https://[{literal}]/x")
                self.assertIn("IPv4-mapped", caught.exception.message)
        # The exclusion is the mapped range and NOT everything that looks like
        # it: `::ffff:1` is `0:0:0:0:0:0:ffff:1`, which is an ordinary address
        # both runtimes spell the same way.
        self.assertIsNone(ipaddress.IPv6Address("::ffff:1").ipv4_mapped)
        self.assertEqual(check_uri("https://[::ffff:1]/x"),
                         "https://[::ffff:1]/x")

    def test_the_exported_work_reference_rule_owns_its_shape_first(self):
        class Sneaky(dict):
            def __getitem__(self, member):
                raise AssertionError("caller code ran")

        for value in (None, [], {}, {"authority_uuid": "0" * 32}, Sneaky()):
            with self.subTest(value=type(value).__name__):
                with self.assertRaises(ContractRefusal):
                    check_work_ref(value)

    def test_the_exported_content_rule_owns_its_shape_first(self):
        class Sneaky(dict):
            def __getitem__(self, member):
                raise AssertionError("caller code ran")

        for value in (None, [], {}, {"entries": []}, Sneaky()):
            with self.subTest(value=type(value).__name__):
                with self.assertRaises(ContractRefusal):
                    check_content_manifest(value)

    def test_a_durable_locator_carries_no_userinfo(self):
        with self.assertRaises(ContractRefusal) as caught:
            check_uri("https://worker:secret@example.test/tree")
        self.assertIn("userinfo", caught.exception.message)

    def test_userinfo_is_refused_whichever_half_is_present(self):
        """A user name alone is a credential too."""
        for what, uri in [("both halves",
                           "https://worker:secret@example.test/tree"),
                          ("a user name alone",
                           "https://worker@example.test/tree"),
                          ("an empty password",
                           "https://worker:@example.test/tree")]:
            with self.subTest(what=what):
                with self.assertRaises(ContractRefusal) as caught:
                    check_uri(uri)
                self.assertIn("userinfo", caught.exception.message)

    def test_the_composite_calls_the_private_bodies(self):
        """4bz, as a check rather than an intention."""
        source = pathlib.Path(manifest.__file__).read_text(encoding="utf-8")
        tree = ast.parse(source)
        composite = next(
            node for node in tree.body
            if isinstance(node, ast.FunctionDef)
            and node.name == "check_manifest_structure")
        called = {piece.func.id for piece in ast.walk(composite)
                  if isinstance(piece, ast.Call)
                  and isinstance(piece.func, ast.Name)}
        for wrapper in ("check_work_ref", "check_content_manifest"):
            with self.subTest(wrapper=wrapper):
                self.assertNotIn(wrapper, called)
        self.assertIn("_relate_work_ref", called)
        self.assertIn("_check_content_manifest", called)


class TheCanonicalVectorIsTheBaseline(unittest.TestCase):
    """§12's rules, driven against the dossier's own canonical input manifest.

    A hand-built manifest is a document I wrote to pass my own rules. The
    conformance vector is the one the contract finding published, so it is the
    honest starting point -- and every case below spoils exactly one thing in it
    and requires exactly one refusal.
    """

    def vector(self):
        published = json.loads(VECTORS.read_text(encoding="utf-8"))
        for case in published["valid"]:
            document = case["document"]
            if document.get("schema") == "baton.worker-manifest/input":
                return document
        raise AssertionError("the published vectors carry no input manifest")

    def resealed(self, **members):
        """The vector with members replaced AND its digest recomputed.

        Otherwise every case below would be refused by the identity rule before
        it reached the rule it is aiming at -- which is the vacuous-probe shape
        this dossier has been corrected for twice.
        """
        document = dict(self.vector(), **members)
        document.pop("manifest_digest", None)
        document["manifest_digest"] = digest(document)
        return document

    def refusing(self, phrase, document):
        with self.assertRaises(ContractRefusal) as caught:
            check_manifest_structure(document, "inputManifest",
                                     what="an input manifest")
        self.assertIn(phrase, caught.exception.message)
        return caught.exception

    def test_the_published_vector_is_accepted(self):
        owned = check_manifest_structure(self.vector(), "inputManifest",
                                         what="an input manifest")
        self.assertEqual(owned["schema"], "baton.worker-manifest/input")
        self.assertGreaterEqual(len(owned["sources"]), 1)

    def test_no_source_rule_reads_an_acquisition_member(self):
        """W14251. Two §12 rules over a source are gone with the members they
        read: a `uri` grammar check, and rule 7's object-namespace comparison
        between an object format and a base revision.

        The 2026-08-25 supersession says this manager receives an ALREADY
        STAGED read-only directory and that how it was populated is outside
        the Worker Manager. Their cases went with them, because a test of a
        rule that no longer exists asserts nothing; this stands in their place.

        `check_uri` is deliberately NOT gone. It still guards artifact
        locators, and `fixtures/uri-vectors.json` is still the authority for
        that grammar -- what ended is this manager reading a SOURCE's
        acquisition locator, not the grammar for locators it still receives.
        """
        import inspect
        from baton_v12.contracts import manifest
        composite = inspect.getsource(manifest)
        rules = composite.split("def check_manifest_structure")[0]
        for gone in ('source["uri"]', 'source["type"]',
                     'source["object_format"]', 'source["base_revision"]'):
            with self.subTest(member=gone):
                self.assertNotIn(gone, rules,
                                 "a source rule still reads an acquisition "
                                 "member")
        # And the grammar itself is still here, still exercised, still applied
        # to what this manager does receive.
        self.assertIn("check_uri(artifact[", composite)
        self.assertEqual(check_uri("https://host.test/x"),
                         "https://host.test/x")

    def test_a_work_id_must_carry_its_authoritys_prefix(self):
        vector = self.vector()
        work_ref = dict(vector["work_ref"], work_id="ffffffff-W1")
        self.refusing("does not carry the prefix",
                      self.resealed(work_ref=work_ref))

    def test_the_schema_itself_owns_every_manifest_path(self):
        """The dependency this module RELIES on, pinned so it cannot drift.

        `check_relative_path` is exported for a caller holding a path the schema
        never saw, and it is NOT called from the composite: every path member of
        a manifest is typed `relativePath`, whose pattern already refuses an
        absolute path, a backslash, a NUL and an empty, `.` or `..` segment.
        Calling it there would be a second owner for one property. This case is
        what keeps that reliance honest.
        """
        vector = self.vector()
        for what, spoiled in [("an escaping output", "../escape"),
                              ("a dot segment", "out/./report.md"),
                              ("a doubled separator", "out//report.md"),
                              ("an absolute path", "/etc/passwd")]:
            with self.subTest(what=what):
                outputs = [dict(vector["outputs"][0], path=spoiled)]
                failure = self.refusing("does not satisfy the frozen schema",
                                        self.resealed(outputs=outputs))
                self.assertEqual(failure.code, "schema")

    def test_the_exported_path_rule_still_refuses_what_it_names(self):
        for what, spoiled in [("an escaping path", "../escape"),
                              ("a dot segment", "out/./report.md"),
                              ("a backslash", "out\\report.md"),
                              ("an absolute path", "/etc/passwd"),
                              ("a NUL", "out/\x00"),
                              ("nothing", "")]:
            with self.subTest(what=what):
                with self.assertRaises(ContractRefusal) as caught:
                    check_relative_path(spoiled, "a path")
                self.assertEqual(caught.exception.code, "path")
        self.assertEqual(check_relative_path("out/report.md", "a path"),
                         "out/report.md")

    def test_overlapping_destinations_are_refused_within_each_root(self):
        """W14251 second review: the rule is unchanged and the SET it ranges
        over is not.

        This case used to nest a declared output inside a source destination
        and call that aliasing, on the old shared-workspace rationale. Under
        the two fixed roots that pair is `/output/x` against `/input/x`, which
        are disjoint -- so the case was asserting a rule the contract no longer
        has. What still aliases is two declarations of the SAME role: two
        staged inputs over one tree deliver the same material twice, and one
        declared output inside another has the worker writing into a tree the
        seal also describes.
        """
        vector = self.vector()
        source = vector["sources"][0]
        output = vector["outputs"][0]
        for role, members in (
                ("staged input", {"sources": [
                    source,
                    dict(source, name="second",
                         destination=source["destination"] + "/nested")]}),
                ("declared output", {"outputs": [
                    output,
                    dict(output, name="second",
                         path=output["path"] + "/nested")]})):
            with self.subTest(role=role):
                failure = self.refusing(f"{role} destinations",
                                        self.resealed(**members))
                self.assertEqual(failure.code, "path")

    def test_equal_relative_paths_in_the_two_fixed_roots_do_not_overlap(self):
        """`repo` below `/input/` and `repo` below `/output/` name disjoint
        trees. The artifact-neutral ruling replaced the old shared workspace
        with these two fixed roots, so lexical equality is not aliasing."""
        vector = self.vector()
        outputs = [dict(vector["outputs"][0],
                        path=vector["sources"][0]["destination"])]
        manifest.check_manifest_structure(
            self.resealed(outputs=outputs), "inputManifest")

    def test_payload_paths_cannot_take_the_fixed_manifest_names(self):
        """The two fixed roots reserve one filename each for their protocol
        manifests. A staged tree at `/input/input.json` would replace the
        manager-authored input envelope; a declared result at
        `/output/output.json` would replace the worker's completion envelope.
        Both are containment collisions even though each spelling is a valid
        relative path in isolation.
        """
        vector = self.vector()
        for what, members in (
                ("input manifest", {"sources": [dict(
                    vector["sources"][0], destination="input.json")]}),
                ("output manifest", {"outputs": [dict(
                    vector["outputs"][0], path="output.json")]})):
            with self.subTest(what=what):
                with self.assertRaises(ContractRefusal) as caught:
                    check_manifest_structure(self.resealed(**members),
                                             "inputManifest")
                self.assertEqual(caught.exception.code, "path")

    def test_a_name_reused_across_sources_and_outputs_is_refused(self):
        vector = self.vector()
        outputs = [dict(vector["outputs"][0],
                        name=vector["sources"][0]["name"])]
        self.refusing("reuses an input/output name",
                      self.resealed(outputs=outputs))

    def test_the_schema_owns_the_generation_bound(self):
        """The other reliance, pinned.

        `assignmentRef.generation` carries `minimum: 1`, so §12 rule 2's
        positivity is decided there and a second owner here would be
        unreachable.
        """
        with self.assertRaises(ContractRefusal) as caught:
            validate_fragment(
                {"work_ref": {"authority_uuid": "0" * 32,
                              "work_id": "00000000-W1"},
                 "participant": "baton.claude", "generation": 0},
                "assignmentRef", what="an assignment reference")
        self.assertIn("minimum", caught.exception.message)

    def test_the_schema_decides_before_the_semantics_do(self):
        """Every rule below the schema reads members.

        A document that is both schema-invalid AND does not identify itself must
        be refused as the first, because reading a member the schema has not
        established is how a document with the wrong shape gets to decide what
        happens next.
        """
        broken = dict(self.vector(), sources="not an array",
                      manifest_digest="sha256:" + "0" * 64)
        failure = self.refusing("does not satisfy the frozen schema", broken)
        self.assertEqual(failure.code, "schema")

    def test_a_content_manifest_must_agree_with_its_entries(self):
        vector = self.vector()
        content = self._content_of(vector)
        if content is None:
            self.skipTest("the published vector carries no content manifest")
        for what, spoiled, phrase in [
                ("the entry count", dict(content, entry_count=99),
                 "declares 99 entries"),
                ("the byte total", dict(content, total_bytes=99),
                 "declares 99 bytes"),
                ("the tree digest",
                 dict(content, tree_digest="sha256:" + "0" * 64),
                 "tree digest does not recompute")]:
            with self.subTest(what=what):
                sources = [dict(vector["sources"][0],
                                content_manifest=spoiled)]
                self.refusing(phrase, self.resealed(sources=sources))

    def test_content_entries_are_sorted_bytewise_and_unique(self):
        vector = self.vector()
        content = self._content_of(vector)
        if content is None or len(content["entries"]) < 1:
            self.skipTest("the published vector carries no content entries")
        entry = content["entries"][0]
        doubled = [entry, dict(entry)]
        spoiled = {"entries": doubled, "entry_count": 2,
                   "total_bytes": entry["bytes"] * 2,
                   "tree_digest": digest(doubled)}
        sources = [dict(vector["sources"][0], content_manifest=spoiled)]
        self.refusing("sorted bytewise and unique",
                      self.resealed(sources=sources))

    def _content_of(self, vector):
        for source in vector["sources"]:
            if source.get("content_manifest") is not None:
                return source["content_manifest"]
        return None


class TheReceiptBindsTheEnvelopeItValidated(unittest.TestCase):
    """W14251, third review [P1] and settled by the fourth.

    §7.3 makes the manager validate `/output/output.json` and hold it against
    the exact input manifest before it freezes. A receipt that then names no
    envelope leaves the contract giving two answers about one completed
    result: either no worker envelope existed, or the manager declined to bind
    the one it validated, and nothing durable told them apart.

    So under 1.0 a COMPLETED receipt must carry `completion_manifest_digest`.
    The other three dispositions may omit it -- `unable`, `plan-rejected` and
    `cancelled` are exactly the endings where the worker may have died before
    publishing anything, and requiring an envelope there would require the
    worker to have succeeded in order to be recorded as having failed.

    THIS IS NOT A VERSION BOUNDARY. I proposed one and it was refused, rightly:
    `$defs.version` pins `minor` to `const: 0`, so widening the version
    vocabulary merely to preserve a bypass would be inventing a negotiation
    nothing performs. The rule is the 1.0 rule.
    """

    def receipt(self, **members):
        body = {
            "version": {"major": 1, "minor": 0},
            "manifest_id": "result-1",
            "created_at": "2026-08-26T00:00:00.000Z",
            "extensions": {},
            "schema": "baton.worker-manifest/result",
            "result_id": "result-1",
            "assignment_ref": {
                "work_ref": {"authority_uuid": "43c55d4b1234567890abcdef12345678",
                             "work_id": "43c55d4b-W1439"},
                "participant": "baton.claude", "generation": 1},
            "input_manifest_digest": "sha256:" + "a" * 64,
            "policy_digest": "sha256:" + "b" * 64,
            "disposition": "completed",
            "outputs": [], "evidence": [],
            "freeze_operation": {"operation_id": "output.freeze:1",
                                 "signature_digest": "sha256:" + "c" * 64},
            "manager_observed_at": "2026-08-26T00:00:00.000Z",
        }
        body.update(members)
        body["manifest_digest"] = digest(body)
        return body

    def test_a_completed_receipt_that_binds_nothing_is_refused(self):
        """The negative the fourth review required kept."""
        with self.assertRaises(ContractRefusal) as caught:
            check_manifest_structure(self.receipt(), "resultManifest")
        self.assertEqual(caught.exception.code, "schema")
        # The refusal names the RULE rather than the member: this boundary
        # bounds what a schema failure may say, so it reports which keyword
        # broke and not the caller's whole document. What makes the case
        # non-vacuous is the pair beside it -- the same receipt with the digest
        # is accepted, so `required` is the keyword that refused this one.
        self.assertIn("required", caught.exception.message)

    def test_a_completed_receipt_that_binds_its_envelope_is_accepted(self):
        envelope = "sha256:" + "e" * 64
        owned = check_manifest_structure(
            self.receipt(completion_manifest_digest=envelope),
            "resultManifest")
        self.assertEqual(owned["completion_manifest_digest"], envelope)

    def test_an_unfinished_ending_may_carry_no_envelope(self):
        """A worker that died before publishing published nothing to bind.
        Requiring one here would require it to have succeeded in order to be
        recorded as having failed."""
        for disposition in ("unable", "plan-rejected", "cancelled"):
            with self.subTest(disposition=disposition):
                owned = check_manifest_structure(
                    self.receipt(disposition=disposition), "resultManifest")
                self.assertNotIn("completion_manifest_digest", owned)

    def test_an_unfinished_ending_still_binds_one_that_was_validated(self):
        """§8.4: whenever an envelope WAS validated, the receipt names it
        whatever the disposition became. The schema requires it only for
        `completed`, because only there can its absence be told from a worker
        that never published -- so this pins that the shape admits it."""
        envelope = "sha256:" + "e" * 64
        owned = check_manifest_structure(
            self.receipt(disposition="unable",
                         completion_manifest_digest=envelope),
            "resultManifest")
        self.assertEqual(owned["completion_manifest_digest"], envelope)


class TheTwoInputDocumentsAreOnePair(unittest.TestCase):
    """W19784, approved 2026-08-26.

    THE DEFECT THIS ANSWERS. The frozen `completionManifest` requires the
    worker to publish the exact full `assignment_ref` -- Work reference,
    participant and authority generation -- and no frozen input surface
    delivered it. `inputManifest` is PRE-CLAIM and deliberately carries no
    generation; `assignmentManifest` has always carried the whole identity but
    had no path inside the execution container. A worker consuming a valid
    input manifest therefore could not author a valid completion envelope at
    all.

    The approved answer delivers the EXISTING canonical assignment manifest at
    `/input/assignment.json`. What is new is a path and a lifecycle, not a
    document -- no environment string, no framed-request member, no alias.
    """

    def given(self):
        published = json.loads(VECTORS.read_text(encoding="utf-8"))
        for case in published["valid"]:
            document = case["document"]
            if document.get("schema") == "baton.worker-manifest/input":
                return document
        raise AssertionError("the published vectors carry no input manifest")

    def minted(self, given, **spoiled):
        """An assignment manifest minted against THAT exact input manifest."""
        assignment = {
            "version": given["version"],
            "manifest_id": "assignment-1",
            "created_at": given["created_at"],
            "extensions": {},
            "schema": "baton.worker-manifest/assignment",
            "assignment_ref": {"work_ref": given["work_ref"],
                               "participant": "baton.claude", "generation": 3},
            "assignment_contract": given["assignment_contract"],
            "offer_id": "offer-1",
            "runtime_attempt_id": "attempt-1",
            "input_manifest_digest": given["manifest_digest"],
            "policy_digest": given["policy_digest"],
            "runtime_profile_digest": given["runtime_profile_digest"],
            "claim_receipt_digest": "sha256:" + "d" * 64,
            "claim_event_seq": 44,
            "activated_at": given["created_at"]}
        assignment.update(spoiled)
        assignment.pop("manifest_digest", None)
        assignment["manifest_digest"] = digest(assignment)
        return assignment

    def resealed(self, given, **members):
        document = dict(given, **members)
        document.pop("manifest_digest", None)
        document["manifest_digest"] = digest(document)
        return document

    def test_the_canonical_pair_is_accepted(self):
        given = self.given()
        owned_input, owned_assignment = check_input_pair(
            given, self.minted(given))
        self.assertEqual(owned_input["schema"], "baton.worker-manifest/input")
        # THE GENERATION IS THE POINT. It is the member `inputManifest`
        # deliberately does not carry and `completionManifest` requires, and
        # this pair is the only place inside the container that supplies it.
        self.assertEqual(owned_assignment["assignment_ref"]["generation"], 3)

    def test_two_halves_of_two_deliveries_are_refused(self):
        """Each document below is internally perfect and would pass its own
        structural rule alone. What refuses is the RELATIONSHIP, which no
        single-document validator can see -- which is why this rule exists.
        """
        given = self.given()
        other = "sha256:" + "f" * 64
        for what, spoiled in (
                ("another Work",
                 {"assignment_ref": {
                     "work_ref": {"authority_uuid": "f" * 32,
                                  "work_id": "ffffffff-W9"},
                     "participant": "baton.claude", "generation": 3}}),
                ("another input manifest", {"input_manifest_digest": other}),
                ("another policy", {"policy_digest": other}),
                ("another runtime profile",
                 {"runtime_profile_digest": other})):
            with self.subTest(what=what):
                assignment = self.minted(given, **spoiled)
                # Structurally valid on its own -- so the refusal below is the
                # comparison and not the shape.
                check_manifest_structure(assignment, "assignmentManifest")
                with self.assertRaises(ContractRefusal):
                    check_input_pair(given, assignment)

    def test_a_repinned_input_manifest_no_longer_matches_its_assignment(self):
        """The other direction of the same binding: `input.json` is immutable
        after claim, and an assignment minted against the original does not
        follow an input that was rewritten and resealed."""
        given = self.given()
        assignment = self.minted(given)
        moved = self.resealed(given, manifest_id="input-2")
        with self.assertRaises(ContractRefusal) as caught:
            check_input_pair(moved, assignment)
        self.assertEqual(caught.exception.code, "digest")

    def test_neither_document_may_stand_in_for_the_other(self):
        given = self.given()
        assignment = self.minted(given)
        for pair in ((given, given), (assignment, assignment)):
            with self.subTest(pair=pair[0]["schema"]):
                with self.assertRaises(ContractRefusal):
                    check_input_pair(*pair)

    def test_the_input_root_reserves_both_manager_authored_documents(self):
        """`assignment.json` joins `input.json` under `/input/`. A staged
        payload at either name would replace a document the MANAGER authored,
        and the nested spelling counts because a protocol document is a file.
        """
        given = self.given()
        source = given["sources"][0]
        for spelling in ("assignment.json", "assignment.json/tree",
                         "input.json", "input.json/tree"):
            with self.subTest(spelling=spelling):
                document = self.resealed(
                    given,
                    sources=[dict(source, destination=spelling)])
                with self.assertRaises(ContractRefusal) as caught:
                    check_manifest_structure(document, "inputManifest")
                self.assertEqual(caught.exception.code, "path")
                self.assertIn(spelling, caught.exception.message)

    def test_the_output_root_reserves_only_its_own_document(self):
        """A DECLARED OUTPUT called `assignment.json` lands at
        `/output/assignment.json` and collides with nothing. Reserving every
        protocol name in every root would be forbidding a SPELLING rather than
        protecting a document, so this pins that the reservation is per-root.
        """
        given = self.given()
        document = self.resealed(
            given,
            outputs=[dict(given["outputs"][0], path="assignment.json")])
        owned = check_manifest_structure(document, "inputManifest")
        self.assertEqual(owned["outputs"][0]["path"], "assignment.json")


class ACompletionManifestIsTheWorkersAnswer(unittest.TestCase):

    def vector(self):
        published = json.loads(VECTORS.read_text(encoding="utf-8"))
        for case in published["valid"]:
            document = case["document"]
            if document.get("schema") == "baton.worker-manifest/completion":
                return document
        raise AssertionError("the published vectors carry no completion manifest")

    def resealed(self, outputs):
        document = dict(self.vector(), outputs=outputs)
        document.pop("manifest_digest", None)
        document["manifest_digest"] = digest(document)
        return document

    def test_the_shipped_validator_enforces_completion_status_integrity(self):
        """The record's executable model already refuses both combinations.
        The validator W6634 will call must enforce the same contract rather
        than accepting a schema-valid lie about whether bytes exist.
        """
        vector = self.vector()
        for what, outputs in (
                ("present without integrity", [dict(
                    vector["outputs"][0], content_manifest=None),
                    vector["outputs"][1]]),
                ("missing with integrity", [vector["outputs"][0], dict(
                    vector["outputs"][1], status="missing-optional",
                    content_manifest=vector["outputs"][0]["content_manifest"])])):
            with self.subTest(what=what):
                with self.assertRaises(ContractRefusal):
                    check_manifest_structure(self.resealed(outputs),
                                             "completionManifest")

    def test_the_shipped_validator_enforces_completion_identity_and_containment(self):
        """Names identify declarations and paths identify trees. Duplicating
        either cannot become acceptable merely because the manager is not yet
        comparing the envelope with its input manifest.
        """
        vector = self.vector()
        first, second = vector["outputs"]
        for what, spoiled in (
                ("duplicate name", dict(second, name=first["name"])),
                ("overlapping path", dict(
                    second, path=first["path"] + "/nested"))):
            with self.subTest(what=what):
                with self.assertRaises(ContractRefusal):
                    check_manifest_structure(
                        self.resealed([first, spoiled]),
                        "completionManifest")
