"""The frozen product schemas as PACKAGE DATA, and the constants they type.

W4 cut A. The two schema documents are copied into the distribution and read
from the installed layout, so the manager carries its contract rather than
reaching for a checkout. A test asserts byte identity with the canonical dossier
assets AND with the frozen Node copies, from source and from the wheel.

THIS MODULE READS AND PARSES; IT DOES NOT VALIDATE. The ruled Draft 2020-12
validator (PLAN 4bh) lives in `validate.py` and nowhere else, so the dependency
reaches exactly one file. What is exported from here is the READABLE schema, and
a caller may edit that projection freely -- runtime validation is built from a
private parse of the same bytes, because a readable copy that could rewrite the
contract would not be a projection at all.

The paragraph this replaces said no validator was pinned. That was true while
the question was open and became wrong when it was answered; a comment that
argues for a superseded state is worse than no comment.
"""

import json
import pathlib

__all__ = ["WORKER_CONTROL_BYTES", "WORKER_CONTROL", "AGENT_SESSION_BYTES",
           "AGENT_SESSION", "PROTOCOL", "VERSION", "CAPABILITIES",
           "OPAQUE_ID_LIMIT", "schema_bytes"]


_SCHEMA_DIRECTORY = pathlib.Path(__file__).resolve().parent / "schema"


def schema_bytes(name):
    """The exact bytes of one frozen schema asset, beside this module.

    Bytes rather than a parsed document, because byte identity with the
    canonical dossier asset is the property under test and a parse-then-dump
    round trip would prove something weaker.

    Read relative to `__file__` rather than through `importlib.resources`. The
    resources API is the more principled one for an importer that is not a
    filesystem, and this distribution has no such importer: the locked build
    installs plain files into site-packages and the gate imports them from
    there. Reaching for `importlib` would also have widened the distribution's
    standard-library surface, which a case in the authority slice measures --
    and I would rather change my own module than another Work's test.
    """
    return (_SCHEMA_DIRECTORY / name).read_bytes()


WORKER_CONTROL_BYTES = schema_bytes("worker-control-1.0.schema.json")
WORKER_CONTROL = json.loads(WORKER_CONTROL_BYTES.decode("utf-8"))

AGENT_SESSION_BYTES = schema_bytes("agent-session-1.0.schema.json")
AGENT_SESSION = json.loads(AGENT_SESSION_BYTES.decode("utf-8"))

PROTOCOL = "baton.worker-control"
VERSION = {"major": 1, "minor": 0}

# §2's closed capability set. `core.errors` is mandatory for every 1.0
# connection; the rest gate exact kinds.
CAPABILITIES = ("core.errors", "core.offer", "core.assignment",
                "core.runtime-lifecycle", "core.activity",
                "core.output-freeze", "core.proposal", "core.receipts")

# The frozen `$defs.opaqueId` bound, taken FROM the schema rather than retyped.
# A limit written twice is a limit that holds in one of the two places, and this
# one already produced a false diagnostic in the Node host when the two sites
# measured in different units.
OPAQUE_ID_LIMIT = WORKER_CONTROL["$defs"]["opaqueId"]["maxLength"]
OPAQUE_ID_PATTERN = WORKER_CONTROL["$defs"]["opaqueId"]["pattern"]


def schema_error_categories():
    return tuple(WORKER_CONTROL["$defs"]["controlErrorBody"]
                 ["properties"]["category"]["enum"])


def schema_error_codes():
    return tuple(WORKER_CONTROL["$defs"]["controlErrorBody"]
                 ["properties"]["code"]["enum"])

