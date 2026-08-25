"""The v12 assignment authority.

THE EXPORTED SURFACE IS THE PROMISE.  What a consumer can reach from here is
the trusted `Authority` bootstrap, the `Refusal` outcome, the frozen identity
and gate vocabulary, and the one authority-owned claim-signature helper the
Worker Manager persists.

What is NOT here is equally deliberate: no store, no path, no database handle,
no SQL, no schema, and no way to mint a session for a participant other than
through the trusted bootstrap.

AND THE CLAIM IS HONEST ABOUT WHAT PYTHON CAN ENFORCE.  Private attributes and
module names are not a sandbox: a determined trusted in-process module can
import `baton_v12.authority.store` or read a private attribute, and no amount
of underscores changes that.  The guarantee this package makes is exact -- the
SUPPORTED, EXPORTED API hands a consumer neither bootstrap nor store, path, SQL
or session-mint authority, and the deployment and filesystem boundary does not
hand it those objects or paths either.  Untrusted workers are isolated by
process and container, which is a mechanism that does enforce something.
"""

from .api import Authority
from .core import CAPABILITIES
from .errors import Refusal
from .session import SESSION_READS, SESSION_TRANSITIONS, Session
from .identity import (
    ABSENT,
    GATE_CONTRACT_RUNTIME, GATE_PLAN_REVISION, GATE_QUIESCENCE,
    MAX_SAFE_INTEGER, V11, V12,
    assignment_ref, claim_signature, gate_token, is_v12_contract, parse_gate,
    same_assignment, work_ref,
)

__all__ = [
    "ABSENT",
    "Authority",
    "CAPABILITIES",
    "GATE_CONTRACT_RUNTIME",
    "GATE_PLAN_REVISION",
    "GATE_QUIESCENCE",
    "MAX_SAFE_INTEGER",
    "Refusal",
    "SESSION_READS",
    "SESSION_TRANSITIONS",
    "Session",
    "V11",
    "V12",
    "assignment_ref",
    "claim_signature",
    "gate_token",
    "is_v12_contract",
    "parse_gate",
    "same_assignment",
    "work_ref",
]
