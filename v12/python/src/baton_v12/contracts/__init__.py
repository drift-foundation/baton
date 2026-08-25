"""The frozen worker-control contract, as this distribution's manager sees it.

W4 cut A: the exported surface is the promise. Nothing here opens a store,
performs a transition, or reaches for the authority; the manager's state and
its injected authority session arrive in later cuts.

THE VALIDATOR IS THE RULED ONE. PLAN item 4bh: a real Draft 2020-12 validator,
pinned with its complete Python 3.13 closure in the hash-locked build,
with no handwritten substitute. It is a dependency of THIS SLICE ONLY -- the
authority remains standard-library only, and separate cases hold each of them to
its own list.
"""

from .canonical import (MAX_SAFE_INTEGER, canonical_bytes, canonical_text,
                        digest, digest_of_bytes)
from .errors import ContractRefusal, ERROR_CODES, MESSAGE_LIMIT
from .frozen import (AGENT_SESSION, AGENT_SESSION_BYTES, CAPABILITIES,
                     OPAQUE_ID_LIMIT, PROTOCOL, VERSION, WORKER_CONTROL,
                     WORKER_CONTROL_BYTES)
from .pod import MAX_DEPTH, MAX_MEMBERS, own, own_record
from .manifest import (ARTIFACT_REF_MEMBERS, CONTENT_MANIFEST_MEMBERS,
                       check_content_manifest, check_manifest_structure,
                       check_relative_path, check_uri, check_work_ref)
from .validate import (AGENT_SESSION_DEFINITIONS, DEFINITIONS,
                       validate_against, validate_agent_session,
                       validate_agent_session_fragment, validate_fragment,
                       validate_worker_control, verify_manifest_digest)

__all__ = [
    "AGENT_SESSION_DEFINITIONS", "DEFINITIONS", "validate_fragment",
    "validate_agent_session_fragment", "verify_manifest_digest",
    "ARTIFACT_REF_MEMBERS", "CONTENT_MANIFEST_MEMBERS",
    "check_content_manifest", "check_manifest_structure",
    "check_relative_path", "check_uri", "check_work_ref",
    "AGENT_SESSION", "AGENT_SESSION_BYTES", "CAPABILITIES", "ContractRefusal",
    "ERROR_CODES", "MESSAGE_LIMIT", "MAX_DEPTH", "MAX_MEMBERS", "MAX_SAFE_INTEGER",
    "OPAQUE_ID_LIMIT", "PROTOCOL", "VERSION", "WORKER_CONTROL",
    "WORKER_CONTROL_BYTES", "canonical_bytes", "canonical_text", "digest",
    "digest_of_bytes", "own", "own_record", "validate_against",
    "validate_agent_session", "validate_worker_control",
]
