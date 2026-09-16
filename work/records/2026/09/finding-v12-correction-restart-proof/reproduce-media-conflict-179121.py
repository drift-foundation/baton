"""Observed packet/sealer conflict, using actual contracts on restored source."""
import copy
import unittest
from baton_v12.contracts import ContractRefusal, digest, digest_of_bytes
from baton_v12.worker_manager import output, sealing


class ReceiptMediaConflict(unittest.TestCase):
    def setUp(self):
        self.declared = {"name": "provider-context-receipt", "type": "directory-result", "path": "provider-context-receipt", "required": False, "constraints": {"max_entries": 1, "max_bytes": 16384, "allowed_media_types": ["application/json"], "link_policy": "forbid", "validator_digest": None}}
        body = b'{"test":"bounded JSON file"}'
        entries = [{"path": "receipt.json", "bytes": len(body), "content_digest": digest_of_bytes(body)}]
        self.content = {"entries": entries, "entry_count": 1, "total_bytes": len(body), "tree_digest": digest(entries)}
        self.seen = sealing._answered("provider-context-receipt", self.declared, "media-probe-attempt", self.content, "/fixture-owned-custody", {})

    def test_actual_sealer_labels_even_a_json_file_directory_as_octet_stream(self):
        self.assertEqual(self.seen["artifact"]["media_type"], "application/octet-stream")
        self.assertEqual(self.seen["content_manifest"], self.content)

    def test_selected_json_only_declaration_refuses_the_actual_sealer_answer(self):
        with self.assertRaisesRegex(ContractRefusal, "media type.*application/octet-stream"):
            output._check_limits("provider-context-receipt", self.declared, self.seen)

    def test_proposed_artifact_media_amendment_resolves_only_this_check(self):
        proposed = copy.deepcopy(self.declared)
        proposed["constraints"]["allowed_media_types"] = ["application/octet-stream"]
        output._check_limits("provider-context-receipt", proposed, self.seen)
        # Same validator still refuses an unrelated claimed type.
        foreign = copy.deepcopy(self.seen)
        foreign["artifact"]["media_type"] = "text/plain"
        with self.assertRaisesRegex(ContractRefusal, "media type"):
            output._check_limits("provider-context-receipt", proposed, foreign)


if __name__ == "__main__":
    unittest.main(verbosity=2)
