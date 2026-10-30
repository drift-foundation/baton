"""Corrected exact-object absence classification for the verifier kernel proof.

W325695 claim376852, answering review 2026-10-28T19-49-07Z. PREPARATION ONLY:
nothing here invokes an engine. It classifies an engine answer that a caller
already obtained.

WHY THIS EXISTS. `preparation-376414/engine-proof.py` `Proof.inspect` rejected
the SUPPORTED exact-name absence answer. A direct Docker `inspect` of an
absent object returns exit 1, `[]` on stdout and a LOWERCASE
`error: no such object` on stderr; that parser required a non-empty stdout and
an uppercase-only error, so it matched neither variant. Selection B therefore
left `exact_absence` false and raised in the execution phase with nothing
created. The same defect sat in the final cleanup absence check, which is the
worse half: a cleanup that cannot recognise "gone" cannot report that it is.

CORRECTIONS TO MY OWN EARLIER CLAIMS, both of which reviews were right about.
I reported Selection B's failure as "not a socket denial", reasoning from two
measurements taken at the shell afterwards; the original receipt records no
stdout or stderr, so what the runner actually saw is not in evidence and that
assertion is withdrawn. I also described exit-1-with-`[]`-and-a-lowercase-
error as "the observed shape"; what I actually observed was a shell and a
child process, not this runner, so the shapes below are the ones this
classifier ADMITS rather than ones it has seen a runner receive. The
classifier records BOTH streams on every answer so the next run leaves neither
question open.

THE CLASSIFICATION IS CLOSED, and `UNCERTAIN` is a first-class answer rather
than a failure of the parser:

    ABSENT      the engine answered, for THIS EXACT NAME and about nothing
                else, that it is not there
    PRESENT     the engine answered with a document for this exact name
    UNCERTAIN   anything else -- permission denied, daemon unreachable,
                malformed JSON, a document for a DIFFERENT name, mixed output,
                or an exit status this contract does not recognise

UNCERTAIN NEVER PROVES ABSENCE, which is the property the original design got
right and must keep: a lost create answer stays uncertain, and nothing may be
removed or declared clean on an answer nobody could read.
"""

import json

ABSENT = "absent"
PRESENT = "present"
UNCERTAIN = "uncertain"

# The lowercase substring a supported engine uses for an absent object. Matched
# case-insensitively because the two engines this packet admits differ in case
# and the original parser was pinned to one of them.
_NO_SUCH = ("no such object", "no such container")
# Any of these ANYWHERE in the error text means the answer is about the
# engine's reachability or this caller's permission, not about the object.
# Review 2026-10-28T19-55-29Z: a mixed message carrying both a denial and a
# no-such-object was classified ABSENT, which is the dangerous direction.
_NOT_ABOUT_THE_OBJECT = ("permission denied", "cannot connect",
                         "connection refused", "daemon", "timeout",
                         "deadline exceeded", "tls", "certificate",
                         "unauthorized", "forbidden")


def _names_this_object(said, name):
    """True only when the error text names THIS object and nothing else.

    Review 2026-10-28T19-55-29Z: the substring test accepted
    `no such object: somebody-else` as absence for a different name. An answer
    about another object proves nothing about this one.
    """
    lowered = name.lower()
    for one in _NO_SUCH:
        at = said.find(one)
        while at != -1:
            tail = said[at + len(one):].strip().lstrip(":").strip()
            if tail.startswith(lowered):
                return True
            at = said.find(one, at + 1)
    return False


def classify(name, *, status, stdout, stderr):
    """Classify one `inspect` answer about ONE exact object name.

    Every operand is required and the answer carries both streams, so a
    receipt written from this can be re-read without the question the last
    one left open.
    """
    held = {"name": name, "status": status,
            "stdout": stdout if isinstance(stdout, str) else "",
            "stderr": stderr if isinstance(stderr, str) else ""}
    said = held["stderr"].lower()
    text = held["stdout"].strip()

    def answer(state, why):
        return dict(held, state=state, why=why)

    if status == 0:
        # A ZERO STATUS MUST STILL CARRY A DOCUMENT FOR THIS NAME. An engine
        # that exits 0 with nothing readable has not said what is there.
        try:
            document = json.loads(text) if text else None
        except ValueError:
            return answer(UNCERTAIN, "exit 0 with unreadable output")
        if type(document) is not list:
            return answer(UNCERTAIN, "exit 0 without an inspect array")
        if any(one in said for one in _NOT_ABOUT_THE_OBJECT):
            # Review: a zero status with a denial on stderr became ABSENT.
            # An answer this caller could not fully obtain is uncertain
            # whatever the status says.
            return answer(UNCERTAIN, "exit 0 beside an error about access")
        if not document:
            # The documented empty-array-with-zero-status case, which some
            # engines use for an absent object.
            return answer(ABSENT, "exit 0 with an empty inspect array")
        if len(document) != 1 or type(document[0]) is not dict:
            return answer(UNCERTAIN, "exit 0 with more than one object")
        # THE DOCUMENT MUST POSITIVELY IDENTIFY THIS NAME. Review: `[{}]` was
        # read as PRESENT because an absent `Name` was tolerated. A document
        # that does not say which object it describes describes none.
        named = document[0].get("Name")
        named = named[1:] if type(named) is str and named.startswith("/") \
            else named
        if named != name and document[0].get("Id") != name:
            return answer(UNCERTAIN, "exit 0 without this object's identity")
        return answer(PRESENT, "exit 0 with this object's document")
    if status == 1:
        # THE SUPPORTED ABSENCE ANSWER, and the one the old parser refused:
        # exit 1, an empty array or nothing at all on stdout, and a
        # case-insensitive no-such-object on stderr.
        if any(one in said for one in _NOT_ABOUT_THE_OBJECT):
            return answer(UNCERTAIN, "an error about access, not the object")
        if _names_this_object(said, name):
            if text in ("", "[]", "[ ]"):
                return answer(ABSENT, "exit 1 with no such object")
            return answer(UNCERTAIN, "no such object beside other output")
        if any(one in said for one in _NO_SUCH):
            return answer(UNCERTAIN, "no such object, but not this one")
        return answer(UNCERTAIN, "exit 1 without a recognised reason")
    return answer(UNCERTAIN, "unrecognised exit status")


def proved_absent(answer):
    """True only for a classified ABSENT. Nothing else may stand in for it."""
    return type(answer) is dict and answer.get("state") == ABSENT
