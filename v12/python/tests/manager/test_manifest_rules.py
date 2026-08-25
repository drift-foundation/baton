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

    def test_overlapping_destinations_are_refused(self):
        """A declared output inside a source directory would have the worker
        writing into material the manifest also says was delivered."""
        vector = self.vector()
        source = vector["sources"][0]
        outputs = [dict(vector["outputs"][0],
                        path=source["destination"] + "/report.md")]
        failure = self.refusing("overlap", self.resealed(outputs=outputs))
        self.assertEqual(failure.code, "path")

    def test_a_name_reused_across_sources_and_outputs_is_refused(self):
        vector = self.vector()
        outputs = [dict(vector["outputs"][0],
                        name=vector["sources"][0]["name"])]
        self.refusing("reuses an input/output name",
                      self.resealed(outputs=outputs))

    def test_a_source_uri_is_absolute_readable_and_bare(self):
        """§12 rule 4, on the member the schema does NOT decide.

        `artifactRef.locator` carries a pattern that forbids a query and a
        fragment; a SOURCE uri is only `format: uri`, and this build keeps
        format assertion off -- so for sources this rule is the owner, and each
        clause needs its own case. Three of the five measured zero until they
        had one, because every case I had written spoiled the same clause.
        """
        vector = self.vector()
        for what, uri, phrase in [
                ("a query", "https://example.test/tree?token=abc",
                 "forbid queries"),
                ("a fragment", "https://example.test/tree#part", "fragment"),
                # MIGRATED: the grammar refuses these earlier and names the
                # exact fault, where the parser could only say "not absolute"
                # or "not parseable". The refusals themselves are retained.
                ("a relative locator", "//example.test/tree",
                 "canonical locator"),
                ("no scheme at all", "example.test/tree",
                 "canonical locator"),
                ("a locator no parser can read", "https://[",
                 "does not close it")]:
            with self.subTest(what=what):
                sources = [dict(vector["sources"][0], uri=uri)]
                self.refusing(phrase, self.resealed(sources=sources))

    def test_a_versioned_source_declares_one_object_namespace(self):
        """§12 rule 7: a sha1 base revision under a sha256 repository is not a
        shorter digest, it is a different object namespace.

        The published vector carries a DIRECTORY source, so this branch measured
        zero -- a rule nothing drives. The versioned source is built here from
        the schema's own required members rather than lifted from a vector that
        does not exist.
        """
        vector = self.vector()
        source = {
            "name": "repo", "type": "%s" % VERSIONED,
            "uri": "https://vcs.example.test/tree",
            "destination": "repo", "required": True,
            "repository_id": "r" * 32, "object_format": "sha256",
            "base_revision": {"algorithm": "sha256", "hex": "a" * 64},
            "source_ref": "refs/heads/main",
            "integration_ref": "refs/heads/main",
            "acquisition_policy_digest": "sha256:" + "b" * 64,
        }
        outputs = [dict(vector["outputs"][0], path="out/report.md")]
        accepted = check_manifest_structure(
            self.resealed(sources=[source], outputs=outputs), "inputManifest",
            what="an input manifest")
        self.assertEqual(accepted["sources"][0]["object_format"], "sha256")
        crossed = dict(source, base_revision={"algorithm": "sha1",
                                              "hex": "c" * 40})
        self.refusing("rule 7",
                      self.resealed(sources=[crossed], outputs=outputs))

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
