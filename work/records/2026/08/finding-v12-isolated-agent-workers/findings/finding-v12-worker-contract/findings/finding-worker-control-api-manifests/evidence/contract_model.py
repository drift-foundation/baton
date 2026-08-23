"""Executable design model for baton.worker-control 1.0.

This is provider-free evidence, not product code.  It intentionally models
only the semantic invariants that JSON Schema cannot express.
"""

from __future__ import annotations

import copy
import hashlib
import json
import posixpath
from dataclasses import dataclass
from urllib.parse import urlsplit


class ContractError(ValueError):
    pass


def canonical_bytes(value: object) -> bytes:
    """JCS-equivalent encoding for the string/integer-only design vectors."""
    return json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")).encode()


def digest(value: object) -> str:
    return "sha256:" + hashlib.sha256(canonical_bytes(value)).hexdigest()


def seal_manifest(document: dict) -> dict:
    sealed = copy.deepcopy(document)
    sealed.pop("manifest_digest", None)
    sealed["manifest_digest"] = digest(sealed)
    return sealed


def verify_manifest_digest(document: dict) -> None:
    candidate = copy.deepcopy(document)
    recorded = candidate.pop("manifest_digest", None)
    if recorded != digest(candidate):
        raise ContractError("manifest digest mismatch")


def verify_body_digest(envelope: dict) -> None:
    if envelope.get("body_digest") != digest(envelope.get("body")):
        raise ContractError("body digest mismatch")


# Review 2026-08-22T14:39:32Z [P1].  Section 4.2 says the operation signature
# is "the canonical digest of the operation kind and every effective durable
# operand", and section 12 rule 9 requires every signature to include all of
# them -- but nothing here computed one, and the W4487 decline vector copied
# `body_digest` into `signature_digest`.  That cannot be the specified
# signature, because the KIND is not in the body; and since `validate_envelope`
# checked only the body digest, a document could change its durable decline
# reason, recompute the body digest, keep the old signature, and pass both the
# frozen schema and this model.  A manager journalling by that unchanged
# signature would replay the first decline against conflicting prose -- the
# exact failure W151's decline model says is impossible.
#
# The payload is pinned here rather than left to each implementation, because
# a signature two peers compute differently is not an identity at all.
#
# WHY THE BEARER IS PRESENT AS ITS VERIFIER RATHER THAN LITERALLY.  A
# signature is durable: it lands in the manager's operation journal and in
# W151's, and section 13 says the claim bearer is never on a durable surface.
# Dropping the bearer entirely would have made an accept under a REUSED
# operation id with a different token an exact replay rather than a collision,
# which is the opposite of "all effective operands".  So a bearer field enters
# the payload as its verifier -- the value the manager already stores for the
# offer -- and `null` stays `null`, so a decline's signature commits to the
# ABSENCE of a bearer as positively as an accept's commits to which one was
# presented.
#
# AND "THE VALUE IT ALREADY STORES" IS ONE EXACT VALUE, which the re-review of
# 2026-08-22T14:57:26Z found it was not.  This module computed `digest(bearer)`
# -- SHA-256 over the bearer's JCS JSON encoding, quotes included -- while
# W151, the contract that OWNS the offer record, hashed the token's raw UTF-8
# bytes and stored bare hexadecimal.  For the bearer `"x" * 43`:
#
#   W151 stored        cc0b1c2c66f3bb9fd1a081c626ba1bef62f6f96441a43be15268523776ac26a1
#   this payload       sha256:6162a6f0b60f2860a9712724c281a7e83d2a74adf304a9dbaf54d43d5aeceadf
#
# Different hashed byte sequences, not formatting variants, so two conforming
# peers computed different operation signatures for the same acceptance --
# exactly the ambiguity section 4.2's clarification existed to remove.
#
# The derivation is now pinned by W151 (`Manager._digest` / `token_verifier`)
# and repeated here verbatim, with the conformance package asserting on a
# GOLDEN bearer that the two produce the identical value.  It is repeated
# rather than imported because these packages are independent provider-free
# records; the golden case is what makes the repetition safe.
_BEARER_FIELDS = ("claim_token",)

# The token's OWN BYTES, not a JSON encoding of them.  A bearer is a secret
# string, not a JSON document: hashing its encoding brings the quotes and the
# escaping rules into the value, so a peer that escapes a character
# differently computes a different verifier for the same secret.  The
# `sha256:` prefix is section 3.2's one digest representation, is what the
# frozen schema's `digest` type accepts, and names the algorithm.
def token_verifier(token: str) -> str:
    """The single-use offer verifier W151 derives from one bearer token."""
    return "sha256:" + hashlib.sha256(token.encode("utf-8")).hexdigest()


# The cross-contract golden pair, pinned as a LITERAL on both sides so a
# change to either derivation fails a comparison rather than moving both
# expected values with it.
GOLDEN_BEARER = "x" * 43
GOLDEN_VERIFIER = ("sha256:cc0b1c2c66f3bb9fd1a081c626ba1bef62f6f96441a43be152"
                   "68523776ac26a1")


def operation_signature_payload(kind: str, body: dict) -> dict:
    """The exact bytes an operation signature is taken over.

    The kind, plus every durable body operand.  Transport correlation
    (`message_id`, `correlation_id`, `sent_at`, `sender`), retry count and
    diagnostic timestamps live outside the body and are therefore excluded by
    construction; `extensions` is excluded because section 2 forbids an
    extension from altering the operation signature.
    """
    operands = copy.deepcopy(body)
    for field in _BEARER_FIELDS:
        if field in operands:
            bearer = operands.pop(field)
            operands[field + "_verifier"] = (None if bearer is None
                                             else token_verifier(bearer))
    return {"kind": kind, "operands": operands}


def operation_signature(kind: str, body: dict) -> str:
    return digest(operation_signature_payload(kind, body))


def verify_operation_signature(envelope: dict) -> None:
    """Recompute and compare a COMMAND's operation signature.

    A reply is exempt on purpose: section 5 says it carries "the same
    operation" as the request it answers, so its `signature_digest` is the
    REQUEST's, and the reply body is a result rather than the operands.
    Recomputing it over the result would reject every conforming reply.  A
    reply's operation identity is proved by correlation to the request whose
    signature this rule already validated.
    """
    operation = envelope.get("operation")
    if operation is None:
        return
    if envelope.get("message_type") != "command":
        return
    if operation["signature_digest"] != operation_signature(envelope["kind"], envelope["body"]):
        raise ContractError("operation signature mismatch")


_ERROR_CODES = {
    "refused": {"precondition", "unsupported-version", "capability", "extension", "operation-collision", "already-terminal"},
    "ambiguous": {"operation", "runtime-start", "collection"},
    "unavailable": {"transport", "authority", "artifact-store", "source-provider"},
    "policy": {"denied", "profile-uncertified", "credential-lifetime", "retention"},
    "integrity": {"schema", "digest", "path", "file-type", "limit", "secret-leak"},
    "stale-assignment": {"ended", "generation", "contract", "target"},
    "runtime-observation": {"identity-mismatch", "duplicate-runtime", "quiescence-unknown", "state-regression"},
}


def validate_envelope(envelope: dict) -> None:
    verify_body_digest(envelope)
    verify_operation_signature(envelope)
    body = envelope["body"]
    for key in ("work_ref", "assignment_ref"):
        if key in body and body[key] is not None:
            work_ref = body[key] if key == "work_ref" else body[key]["work_ref"]
            validate_work_ref(work_ref)
    if envelope["kind"] == "control.error" and body["code"] not in _ERROR_CODES[body["category"]]:
        raise ContractError("error code does not belong to category")


def validate_relative_path(path: str) -> None:
    if not isinstance(path, str) or not path or "\\" in path or "\0" in path:
        raise ContractError("path is not normalized POSIX-relative")
    if path.startswith("/") or posixpath.normpath(path) != path:
        raise ContractError("path is not normalized POSIX-relative")
    if any(segment in ("", ".", "..") for segment in path.split("/")):
        raise ContractError("path is not normalized POSIX-relative")


def validate_uri(uri: str) -> None:
    parts = urlsplit(uri)
    if not parts.scheme or not parts.netloc and parts.scheme not in ("artifact", "urn"):
        raise ContractError("URI is not absolute")
    if parts.username is not None or parts.password is not None:
        raise ContractError("URI contains userinfo")
    if parts.query:
        raise ContractError("URI contains a query")
    if parts.fragment:
        raise ContractError("URI contains a fragment")


def validate_work_ref(work_ref: dict) -> None:
    if work_ref["work_id"].split("-", 1)[0] != work_ref["authority_uuid"][:8]:
        raise ContractError("Work ID prefix does not match authority UUID")


def _paths_overlap(left: str, right: str) -> bool:
    return left == right or left.startswith(right + "/") or right.startswith(left + "/")


def _validate_content_manifest(content: dict) -> None:
    entries = content["entries"]
    paths = [entry["path"] for entry in entries]
    for path in paths:
        validate_relative_path(path)
    if paths != sorted(paths) or len(paths) != len(set(paths)):
        raise ContractError("content entries are not sorted and unique")
    if content["entry_count"] != len(entries):
        raise ContractError("content entry count mismatch")
    if content["total_bytes"] != sum(entry["bytes"] for entry in entries):
        raise ContractError("content byte count mismatch")
    if content["tree_digest"] != digest(entries):
        raise ContractError("content tree digest mismatch")


def _walk_for_durable_secrets(value: object, path: tuple[str, ...] = ()) -> None:
    forbidden = {"claim_token", "password", "authorization", "access_token", "refresh_token", "private_key"}
    if isinstance(value, dict):
        for key, child in value.items():
            if key.lower() in forbidden:
                raise ContractError("durable document contains a secret field")
            _walk_for_durable_secrets(child, path + (key,))
    elif isinstance(value, list):
        for child in value:
            _walk_for_durable_secrets(child, path)


def validate_manifest(document: dict, *, verify_digest: bool = True) -> None:
    """Validate shared and type-specific portable semantic rules."""
    if verify_digest:
        verify_manifest_digest(document)
    _walk_for_durable_secrets(document)

    if "work_ref" in document:
        validate_work_ref(document["work_ref"])
    if "assignment_ref" in document and document["assignment_ref"] is not None:
        validate_work_ref(document["assignment_ref"]["work_ref"])
        if document["assignment_ref"]["generation"] < 1:
            raise ContractError("assignment generation is not positive")

    for artifact in _artifact_refs(document):
        validate_uri(artifact["locator"])

    if document.get("schema") == "baton.worker-manifest/input":
        _validate_input_manifest(document)
    for content in _content_manifests(document):
        _validate_content_manifest(content)


def _validate_input_manifest(document: dict) -> None:
    sources = document["sources"]
    outputs = document["outputs"]
    names = [item["name"] for item in sources + outputs]
    if len(names) != len(set(names)):
        raise ContractError("input/output names are not unique")
    destinations = [item["destination"] for item in sources] + [item["path"] for item in outputs]
    for path in destinations:
        validate_relative_path(path)
    for index, left in enumerate(destinations):
        for right in destinations[index + 1 :]:
            if _paths_overlap(left, right):
                raise ContractError("input/output destinations overlap")
    for source in sources:
        validate_uri(source["uri"])
        if source["type"] == "git" and source["object_format"] != source["base_revision"]["algorithm"]:
            raise ContractError("git object format mismatch")


def _artifact_refs(value: object):
    if isinstance(value, dict):
        if {"artifact_id", "media_type", "bytes", "content_digest", "locator"} <= value.keys():
            yield value
        for child in value.values():
            yield from _artifact_refs(child)
    elif isinstance(value, list):
        for child in value:
            yield from _artifact_refs(child)


def _content_manifests(value: object):
    if isinstance(value, dict):
        if {"entries", "entry_count", "total_bytes", "tree_digest"} <= value.keys():
            yield value
        for child in value.values():
            yield from _content_manifests(child)
    elif isinstance(value, list):
        for child in value:
            yield from _content_manifests(child)


@dataclass(frozen=True)
class OperationResult:
    signature_digest: str
    result_digest: str


class ReplayLedger:
    def __init__(self) -> None:
        self._results: dict[str, OperationResult] = {}

    def apply(self, operation_id: str, signature_digest: str, result: object) -> tuple[str, str]:
        result_digest = digest(result)
        previous = self._results.get(operation_id)
        if previous is None:
            self._results[operation_id] = OperationResult(signature_digest, result_digest)
            return "committed", result_digest
        if previous.signature_digest != signature_digest:
            raise ContractError("operation collision")
        return "replayed", previous.result_digest


# W4487 (`work/records/2026/08/finding-worker-control-decline-token-conflict/`),
# ruled 2026-08-22.
#
# The two frozen contracts contradicted each other: W151 1-ruled §7 required a
# declining worker to present the exact unspent bearer, while §6.1 here and the
# frozen schema require `claim_token: null` for a decline.  The approver kept
# this contract's non-secret envelope and superseded W151's requirement.
#
# The schema proves the SHAPE — null for a decline, a string for an accept —
# and it cannot prove the BINDING, which is what the bearer used to stand in
# for.  So the binding is a §12 semantic rule and is modelled here: a decline
# is authorized by naming one issued offer exactly, and a body that names an
# offer while carrying another's attempt or Work terminates neither.
def validate_offer_decide(body: dict, issued: dict) -> None:
    """Check one `offer.decide` body against the offer it claims to answer.

    `issued` is the manager's durable offer record: `offer_id`,
    `runtime_attempt_id`, `work_ref`, and whether its verifier is still
    unspent.  The bearer is deliberately absent from both sides here — an
    acceptance's token check is a separate proof of possession, and this is
    the proof of identity that every decision needs.
    """
    if body["decision"] not in ("accept", "decline"):
        raise ContractError("decision is not accept or decline")
    if body["decision"] == "decline":
        if body["claim_token"] is not None:
            raise ContractError("a decline must not carry the claim bearer")
    elif not isinstance(body["claim_token"], str):
        raise ContractError("an accept must carry the claim bearer")
    binding = ("offer_id", "runtime_attempt_id")
    if any(body[field] != issued[field] for field in binding):
        raise ContractError("offer.decide binding does not match the issued offer")
    if body["work_ref"] != issued["work_ref"]:
        raise ContractError("offer.decide binding does not match the issued offer")
    if not issued["verifier_unspent"]:
        raise ContractError("the offer verifier is already spent")
    if not body["reason"]:
        raise ContractError("offer.decide carries no reason")


class AssignmentFence:
    def __init__(self, assignment_ref: dict) -> None:
        self.live = copy.deepcopy(assignment_ref)
        self.ended = False

    def require_live(self, supplied: dict) -> None:
        if self.ended:
            raise ContractError("assignment ended")
        if supplied != self.live:
            raise ContractError("stale assignment generation")

    def end(self) -> None:
        self.ended = True


class ObservationLedger:
    _rank = {
        "not-started": 0,
        "start-requested": 1,
        "running": 2,
        "cancel-requested": 3,
        "stopping": 4,
        "quiescent": 5,
        "uncertain": 5,
        "destroyed": 6,
    }

    def __init__(self) -> None:
        self.sequence = -1
        self.state = "not-started"

    def observe(self, sequence: int, state: str) -> None:
        if sequence <= self.sequence:
            raise ContractError("observation sequence regression")
        if self.state == "destroyed" or self._rank[state] < self._rank[self.state]:
            raise ContractError("runtime state regression")
        self.sequence = sequence
        self.state = state
