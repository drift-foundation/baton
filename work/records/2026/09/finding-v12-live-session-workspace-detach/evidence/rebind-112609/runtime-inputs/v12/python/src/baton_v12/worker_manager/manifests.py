"""THE RETAINED MANIFESTS: validated documents this manager is holding.

W6628, ported from the frozen Node `manifests.mjs` by obligation.

A DIGEST IS NOT A RECORD, and that is the whole reason this exists. Before it,
the store held `attempts.input_digest` and nothing else about the document that
digest names -- so a freeze could not compare a sealed result against the
OUTPUT DECLARATIONS the input manifest carries, because it had never seen them,
and every later reader was left with a number and nothing to inspect or
replay.

ONE TABLE SERVES BOTH DIRECTIONS, because they are the same fact: a validated
document this manager holds, keyed by the digest that identifies it. The input
declaration and the frozen result are retained the same way and read back the
same way.

THE KEY IS THE DIGEST, which buys two properties rather than one. Retention is
idempotent by construction -- the same document stored twice is the same row --
and a stored body cannot drift from its key, because the key is computed from
the bytes rather than declared beside them.

BEING AT THE NAMED KEY IS NOT THE SAME AS BEING THE NAMED THING. `load` takes
the definition it must be and refuses to default it: a retained RESULT manifest
is a perfectly valid thing to hold, and naming one as an attempt's input digest
would let its similarly shaped output rows be read as trusted DECLARATIONS. A
caller that has not said what it expects has not made the check that matters.
"""

import json

from ..contracts import (ContractRefusal, canonical_bytes,
                         check_manifest_structure, verify_manifest_digest)
from ..contracts.errors import name_value
from . import boundaries, documents, schema

__all__ = ["retain_manifest", "load_manifest"]


def _definition(definition):
    """The kind a caller says a document must be.

    REQUIRED rather than defaulted, and owned as text so a caller handing this
    boundary something unstorable is refused here rather than inside the
    validator's own vocabulary check.
    """
    boundaries.text(definition, "a retained manifest definition")
    return definition


def _manifest_row(connection, key):
    """THE ONE CROSSING out of the manifests table, and every column owned.

    `body` is proved to DECODE here, so a retained document this build can no
    longer read is caught where the row is adopted rather than by the caller
    that was about to compare declarations against it.
    """
    found = connection.execute(
        "SELECT * FROM manifests WHERE digest = ?", (key,)).fetchone()
    if found is None:
        return None
    return boundaries.row(found, "a retained manifest",
                          schema.MANIFEST_COLUMNS)


def retain_manifest(store, document, definition):
    """Validate a manifest and retain its canonical bytes.

    Returns the digest that identifies it, which is what every other table
    stores. The document is validated FIRST: a manifest this manager could not
    read is not one it should be holding, and retaining it would make the store
    the place a malformed document survives.

    NOT JOURNALLED. Retention is keyed by the digest of the bytes, so it is
    idempotent by construction and there is no "did this already happen"
    question for a journal to answer -- and the effectively-once contract
    answers a different question anyway, which W6592's certification path
    learned the hard way.
    """
    _definition(definition)
    owned = check_manifest_structure(document, definition,
                                     what="a retained manifest")
    key = verify_manifest_digest(owned, what="a retained manifest")
    connection = store._connection
    connection.execute("BEGIN IMMEDIATE")
    try:
        retained = _retain_canonical(connection, store._now(), key,
                                     owned["schema"], owned)
    except BaseException:
        try:
            connection.execute("ROLLBACK")
        except Exception:
            pass
        raise
    connection.execute("COMMIT")
    return documents.manifest_retained(digest=key, schema=owned["schema"],
                                       retained=retained)


def _retain_canonical(connection, at, key, kind, owned):
    """COMPARE BEFORE REFERENCE, on whatever connection is doing the writing.

    `INSERT OR IGNORE` would BYPASS the collision refusal this module exists to
    make: if the digest already named different bytes the insert is ignored,
    the row that references it commits, and a reload returns a document its
    digest does not identify. One rule, one place, and every writer goes
    through it.

    A digest collision with different bytes is not something SHA-256 hands out.
    "Cannot happen" is not a reason to write the second one over the first --
    and the same check catches a store somebody edited by hand.
    """
    bytes_out = canonical_bytes(owned).decode("utf-8")
    found = _manifest_row(connection, key)
    if found is not None:
        if found["body"] != bytes_out:
            raise ContractRefusal(
                "integrity", "digest",
                f"{name_value(key)} is already retained with different bytes; "
                f"a digest identifies a document and cannot name two")
        return False
    connection.execute(
        "INSERT INTO manifests (digest, schema, body, retained_at) "
        "VALUES (?, ?, ?, ?)", (key, kind, bytes_out, at))
    return True


def load_manifest(store, manifest_digest, definition):
    """The retained document for a digest, or None -- VALIDATED AS WHAT THE
    CALLER ASKED FOR, and RE-BOUND TO ITS KEY.

    Two rules, and each closes a different hole. The DEFINITION check stops a
    document of one kind being read as another merely because it sits at the
    named key. The RECOMPUTATION stops a store nobody validates on the way out
    from becoming a store where a hand edit outlives every guard on the way in.

    Parsed fresh on every call. A cached document handed to two callers is a
    durable record one of them can edit for the other -- the same
    time-of-check aliasing the validator already refuses to hand out.
    """
    boundaries.identity(manifest_digest, "a retained manifest digest")
    _definition(definition)
    row = _manifest_row(store._connection, manifest_digest)
    if row is None:
        return None
    owned = check_manifest_structure(_decoded(row["body"]), definition,
                                     what="a retained manifest")
    recomputed = verify_manifest_digest(owned, what="a retained manifest")
    if recomputed != manifest_digest:
        raise ContractRefusal(
            "integrity", "digest",
            f"a retained manifest is stored under {name_value(manifest_digest)}"
            f" and its bytes recompute to {name_value(recomputed)}; a digest "
            f"identifies the document it names")
    return owned


def _decoded(body):
    """The adopted body as a value.

    `boundaries.row` already proved this text decodes -- that is what the
    `json` column contract IS -- so this parse cannot fail, and it is private
    for the reason every projector over an adopted row is: an exported one
    would be a boundary nobody owns.
    """
    return json.loads(body)
