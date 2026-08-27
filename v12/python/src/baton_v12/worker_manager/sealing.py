"""SEALING: taking the declared outputs out of a quiesced runtime.

W6634. `work/records/2026/08/finding-v12-sealed-output-credentials/`.

W6628 built the manager's side of the freeze -- `request_freeze` proves the
preconditions, journals the act, and hands the adapter the exact operation it
is settling. What it then calls is `adapter.seal`, and no adapter had one. This
is that half: the worker/adapter side that produces the sealed result the
manager receives.

THE TWO SHAPES ARE READ OFF THEIR CONSUMERS, not invented here:

  `seal(request)`     is called by `output.request_freeze` and its answer goes
                      straight into `record_frozen_result`, which validates it
                      as a `baton.worker-manifest/result` and then holds it
                      against the input manifest's declarations both ways.
  `collect(operands)` is called by `intake.request_intake` and its answer is
                      compared member by member by `intake._compared`, which
                      adopts only the custody locator and compares identity,
                      content digest and byte count against what the freeze
                      recorded.

WHAT THIS COMPONENT MAY COLLECT IS DECIDED ELSEWHERE, which is the whole
reason the declared outputs are owned at CONSTRUCTION rather than taken per
call. They are assignment-scoped and fixed, exactly like the resolved identity
and the assignment roots this adapter already refuses to exist without; a
per-call operand would make "what may be collected" an argument, and the
acceptance for this Job is precisely that it is not.

ORDERED AFTER QUIESCENCE, AND IT PROVES THAT ITSELF. The manager proves
quiescence from the durable axis before it calls; this asks the ENGINE whether
anything for this attempt is still alive, because the axis is a statement about
observations and this is a statement about a filesystem somebody may still be
writing to. The eight frozen label members split exactly between the request
and this adapter's own identity, so the selector composes without the manager
passing a runtime id it deliberately does not pass.

AND THE MEASUREMENT IS W6631'S, CONSUMED RATHER THAN REBUILT.
`workspaces.directory_manifest` already opens every entry once with
`O_NOFOLLOW` -- so a replacement between the check and the read is a file this
component never sees rather than one it describes wrongly -- takes bytes and
size from that one descriptor, admits only bounded regular files, and sorts
bytewise for the tree digest. A second walker here would be a second thing to
keep true.
"""

import json
import os
import shutil
import stat

from ..contracts import (ContractRefusal, check_manifest_structure,
                         check_no_durable_secret, digest, own)
from ..contracts.errors import name_value
from . import boundaries, workspaces

__all__ = ["DECLARED_OUTPUT_MEMBERS", "QUIET_STATES", "declared_outputs",
           "sealed_result", "collected_result"]

# The frozen `outputDescriptor`'s own member set. Repeated here because this
# component receives declarations at construction rather than through the
# schema validator, and a declaration missing `constraints` is a declaration
# whose limits nobody stated.
DECLARED_OUTPUT_MEMBERS = ("name", "type", "path", "required", "constraints")

# The frozen `outputConstraints` members this component ENFORCES, and the rest
# of that document's own member set beside them.
#
# BOTH LISTS ARE NEEDED, which the first version got wrong: `boundaries.
# document` refuses a member its contract does not name -- deliberately, so
# ignoring one cannot silently assume the recognised members still mean what
# they did -- so declaring only the two enforced ones made every real
# declaration refuse as a schema error before any limit could be reached. That
# is the vacuous shape twice over: a constraint nobody could pass, and two
# limit cases passing for the wrong reason.
#
# `link_policy` is not ENFORCED here because it is not this component's to
# decide: the measurement admits regular files only, so a link is refused by
# construction rather than by policy, and claiming otherwise would credit this
# layer with a decision made one layer down.
_ENFORCED = ("max_bytes", "max_entries")
_DECLARED = ("allowed_media_types", "link_policy", "validator_digest")

# What an engine may answer about a runtime that is NOT gone. Anything else is
# an answer this component cannot read, and reading it would mean guessing
# whether somebody is still writing into the tree it is about to seal.
QUIET_STATES = ("absent", "quiescent")


def _list(value, what):
    """A caller's sequence, as a fresh built-in list.

    `boundaries` has no list kind because a list is not a boundary -- what
    crosses is the MEMBERS, and each is owned by its own rule below. This is
    the same two-part shape `intake._chosen` uses: `own` for the fresh copy
    and the JSON-data proof, then the shape.
    """
    taken = own(value, what=what)
    if type(taken) is not list:
        raise ContractRefusal(
            "integrity", "schema",
            f"{what} is a list; this is {name_value(value)}")
    return taken


def declared_outputs(outputs):
    """The assignment's declared outputs, owned once at construction.

    Every member of the frozen descriptor, and the constraint document beside
    it: a declaration this adapter cannot read is a launch mistake, not a
    freeze-time refusal, because by freeze time a worker has already done the
    work against limits nobody could state.
    """
    # THE SHAPE FIRST, THEN THE CALLER'S OWN SEQUENCE. Sixth review [P1]:
    # iterating the copy `_list` returns hid which operand these members came
    # from, so the boundary inventory reported four owners here as attributed
    # to no entry. Nothing is lost -- `boundaries.document` below takes the
    # deep built-in copy that matters. Same correction `credentials.py` was
    # given, for the same reason.
    _list(outputs, "the assignment's declared outputs")
    if not outputs:
        raise ContractRefusal(
            "integrity", "schema",
            "an assignment declares at least one output; sealing a result "
            "nobody asked for is how an undeclared path gets collected")
    declared = {}
    for entry in outputs:
        one = boundaries.document(entry, "a declared output",
                                  required=DECLARED_OUTPUT_MEMBERS)
        name = boundaries.identity(one["name"], "a declared output name")
        if name in declared:
            raise ContractRefusal(
                "integrity", "schema",
                f"output {name_value(name)} is declared twice; two "
                f"declarations of one name is not one declaration")
        boundaries.identity(one["type"], "a declared output type")
        # THE PATH IS OWNED AT THIS SITE, and its structural rules are one
        # line down. Sixth review [P1]: `_relative` held the only
        # `boundaries.text` for a declared path, and a private helper's
        # parameter is not an entry -- so the label was owned by nothing the
        # inventory could attribute.
        boundaries.text(one["path"], "a declared output path")
        _relative(one["path"], f"the declared path of output {name}")
        if type(one["required"]) is not bool:
            raise ContractRefusal(
                "integrity", "schema",
                f"whether output {name_value(name)} is required is a yes or a "
                f"no; this is {name_value(one['required'])}")
        limits = boundaries.document(one["constraints"],
                                     "a declared output's constraints",
                                     required=_ENFORCED, optional=_DECLARED)
        for member in _ENFORCED:
            if type(limits[member]) is not int or limits[member] < 0:
                raise ContractRefusal(
                    "integrity", "schema",
                    f"a declared {member} is a whole number of at least zero; "
                    f"this is {name_value(limits[member])}")
        declared[name] = {**one, "constraints": limits}
    # NO TWO DECLARATIONS OVER ONE TREE -- review [P1]. Rejecting duplicate
    # NAMES is not the same rule: two names over the same path, or one nested
    # inside the other, make the same bytes two artifacts with two identities
    # and two digests. Cleanup and retention then decide twice about material
    # that is once, which is the overlap the acceptance forbids.
    for name, one in sorted(declared.items()):
        for other, another in sorted(declared.items()):
            if other <= name:
                continue
            if _overlaps(one["path"], another["path"]):
                raise ContractRefusal(
                    "integrity", "path",
                    f"outputs {name_value(name)} and {name_value(other)} "
                    f"declare {name_value(one['path'])} and "
                    f"{name_value(another['path'])}, which are the same tree "
                    f"or one inside the other; two declarations over one tree "
                    f"make the same bytes two artifacts")
    return declared


def _relative(value, what):
    """A CANONICAL relative path, proved at construction.

    Review [P1]: this owned the path only as non-empty text, so an absolute
    path, one escaping through `..`, and non-canonical spellings were all
    accepted when the adapter was built and refused -- if at all -- only during
    seal. By seal time a worker has already run against a declaration nobody
    could act on, which is the wrong party and the wrong moment.

    The rules are the frozen `relativePath`'s own: no leading separator, no
    empty segment (which is what a doubled separator is), and no `.` or `..`
    anywhere. Segments rather than a prefix test, for the reason `_overlaps`
    gives: string containment answers a different question than path structure.
    """
    # THE TEXT RULE IS THE CALLER'S NOW, at the site where the operand
    # arrives; what remains here are the structural rules over an already
    # owned string.
    if value.startswith("/"):
        raise ContractRefusal(
            "integrity", "path",
            f"{what} is {name_value(value)}, which is absolute; a declared "
            f"output names a place inside this assignment's own workspace")
    segments = value.split("/")
    for segment in segments:
        if segment == "":
            raise ContractRefusal(
                "integrity", "path",
                f"{what} is {name_value(value)}, which carries an empty "
                f"segment; two spellings of one path are two paths to every "
                f"comparison that comes after")
        if segment in (".", ".."):
            raise ContractRefusal(
                "integrity", "path",
                f"{what} is {name_value(value)}, which carries a "
                f"{name_value(segment)} segment; a declared output is proved "
                f"canonical before a worker runs, not resolved afterwards")
    return value


def _overlaps(one, other):
    """The same relative tree, or one inside the other.

    Compared SEGMENT BY SEGMENT rather than by prefix, because `out2` starts
    with `out` and is not inside it -- the same mistake `_within` exists to
    avoid for absolute paths.
    """
    first = [piece for piece in one.split("/") if piece]
    second = [piece for piece in other.split("/") if piece]
    shorter, longer = sorted((first, second), key=len)
    return longer[:len(shorter)] == shorter


# THE QUIESCENCE GATE IS NOT HERE, and the inventory is what said so.
#
# My first version called `adapter.list` and `adapter.observe` from this
# module. Both are INJECTED CAPABILITIES with exactly one crossing each --
# `attempts.py:reconcile_runtime` owns them -- and a capability with two
# crossings has two owners, which the boundary inventory refuses by name.
#
# That is a design signal rather than a registration chore. This module is a
# pure function over data: it is handed the roots, the declarations and the
# observation somebody else made, and it decides what the sealed result says.
# The adapter performs its own quiescence check with its own methods, where
# those capabilities already cross exactly once.


def _measured(place, declared, name):
    """One declared output, measured and held against its own limits."""
    manifest = workspaces.directory_manifest(place)
    limits = declared["constraints"]
    if manifest["entry_count"] > limits["max_entries"]:
        raise ContractRefusal(
            "integrity", "limit",
            f"output {name_value(name)} carries {manifest['entry_count']} "
            f"entries and its declaration allows {limits['max_entries']}")
    if manifest["total_bytes"] > limits["max_bytes"]:
        raise ContractRefusal(
            "integrity", "limit",
            f"output {name_value(name)} carries {manifest['total_bytes']} "
            f"bytes and its declaration allows {limits['max_bytes']}")
    return manifest


def _staged(place, into, declared, name):
    """The declared tree MEASURED AND COPIED into manager custody, then frozen.

    Review [P1]: freezing the workspace in place left the observation over a
    path the worker still owns. A host-side write after the freeze changed what
    collection returned, both locators named the live workspace, and retry
    identity depended on a tree somebody else could edit. The dossier's
    acceptance says the material is "copied into immutable staging BEFORE its
    manifest/count/bytes/digest observation is emitted", and this is that copy.

    W26283 [P1]: IT USED TO MEASURE AND THEN REOPEN EACH PATH. The measurement
    is race-safe -- W6631 descends by opened directory identity and opens every
    file `O_NOFOLLOW` relative to it -- and copying afterwards with a plain
    `open(source)` resolved every path string a second time. Two harms were
    driven against that, not argued: a measured subdirectory replaced by a
    symbolic link put material from OUTSIDE the workspace into custody, and a
    measured file replaced by a FIFO made the copy block forever, which is one
    `mkfifo` stalling the manager.

    The bytes written are now the bytes measured, from the descriptor that
    produced them, so there is no second resolution for anything to be
    swapped in. That also retires the double measurement this function used to
    need: comparing two digests was how a moving tree was detected, and a
    single pass leaves nothing to move BETWEEN. What remains below is a
    verification of the WRITE, which is a different question and a cheap one.

    THE DECLARED CEILINGS ARE ENFORCED AS THE PASS RUNS rather than after it,
    so an oversize tree stops at the entry that crosses the line instead of
    being copied whole and then refused.
    """
    _cleared(into)
    limits = declared["constraints"]
    written = workspaces.copied_manifest(
        place, into,
        max_entries=limits["max_entries"], max_bytes=limits["max_bytes"],
        # §13 OVER THE ARTIFACT'S OWN BYTES, W6634. The sealed result and the
        # collection observation were already walked, but those are DOCUMENTS
        # this manager composes -- a worker that wrote its credential into the
        # output it produced put the bearer somewhere no walk of a manager
        # document has ever looked, and this pass is the one moment the content
        # is in hand.
        #
        # BEFORE THE WRITE, so refusing means the bytes never became custody
        # rather than being taken and then objected to.
        #
        # Decoded leniently on purpose. The question is whether a live bearer's
        # characters are present, and a file that is not valid UTF-8 still
        # answers it -- refusing to look at binary would make "write it to a
        # PNG" the way past this.
        admits=lambda relative, content: check_no_durable_secret(
            content.decode("utf-8", "replace"),
            what=f"the staged content of {name}/{relative}"))
    _frozen(into)
    # THE WRITE VERIFIED, over custody this manager now owns and has just made
    # read-only. This is NOT the old race check: nothing the worker does can
    # reach these bytes any more. It answers whether what landed on the device
    # is what was measured -- a short write, a full filesystem, a truncated
    # file -- which a single pass cannot tell you on its own.
    confirmed = workspaces.directory_manifest(into)
    if confirmed["tree_digest"] != written["tree_digest"]:
        raise ContractRefusal(
            "integrity", "digest",
            f"output {name_value(name)} does not re-measure to what was "
            f"copied; custody must describe the bytes that reached the device")
    return confirmed


def _cleared(into):
    """An interrupted attempt's partial tree, removed rather than trusted.

    Review [P1]: custody is frozen when it is complete, so a partial tree from
    a stopped process may also be read-only -- this makes it writable before
    removing it rather than faulting on it.

    REMOVED, not written over. The copy opens every destination `O_EXCL`, so a
    leftover entry would refuse; and a prefix left by an earlier attempt is not
    evidence of anything this pass measured. The committed record above is what
    makes a whole answer replayable.
    """
    if not os.path.isdir(into):
        return
    for base, directories, files in os.walk(into, topdown=False):
        for one in directories:
            os.chmod(os.path.join(base, one), 0o700)
        for one in files:
            os.chmod(os.path.join(base, one), 0o600)
    os.chmod(into, 0o700)
    shutil.rmtree(into)


# THE COMMITTED RESULT, and why a directory is not one.
#
# Review [P1], twice over in one round. Replay was inferred from
# `os.path.isdir(held)`, and directory existence is neither sufficient nor
# necessary:
#
#   NOT SUFFICIENT -- creating custody and copying into it are not atomic, so a
#   process can stop with a PREFIX of the measured tree on disk. Restarting
#   then measured that prefix and published it as the complete output.
#
#   NOT NECESSARY -- `missing-optional` is a settled answer with no tree at
#   all, so it had no marker, and the same freeze operation consulted today's
#   workspace again. An optional path appearing later silently changed the
#   answer from missing to present, which is one operation identity returning
#   two different results.
#
# So the evidence is a RECORD OF THE WHOLE ANSWER, absence included, and it is
# published LAST -- after every output is staged and frozen. That ordering is
# what makes it trustworthy: it exists only if everything it describes already
# succeeded, which is the same publish-last discipline the worker contract puts
# on `output.json`.
#
# What is stored is the sealed manifest ITSELF, byte-stable, so an exact retry
# reproduces the first answer rather than a freshly-derived one that happens to
# agree -- including its instant, which a re-derivation would move.
_COMMITTED = "sealed.json"

# THE NAME THE BYTES ARE WRITTEN UNDER BEFORE THEY ARE THE ANSWER.
#
# Third review [P1]: publishing LAST is not publishing ATOMICALLY. `open` on
# the final name creates or truncates it before a single byte of the answer is
# there, so a process stopped inside the write left `sealed.json` existing and
# empty -- and replay, which reads existence as settlement, handed those zero
# bytes to a JSON decoder and raised a fault that is not a refusal.
#
# A FIXED private name rather than a unique one, deliberately. `os.replace` is
# atomic within one directory, so the final name only ever holds bytes that
# were complete before the rename; and a leftover from a stopped writer is
# truncated by the next `open`, so this cannot accumulate the litter a
# per-attempt unique name would.
_COMMITTING = ".sealed.json.committing"

# Every member of the sealed body that BINDS it to one freeze request, and the
# side each is compared against. Written as a table because the rule is "all of
# them", and a comparison somebody has to remember to add is one that gets
# added late.
_BOUND = ("result_id", "assignment_ref", "disposition", "freeze_operation",
          "input_manifest_digest", "policy_digest")


def _committed_result(custody, expected):
    """The settled answer this attempt published, PROVED to be this one's.

    Third review [P1], twice. Existence was treated as settlement and the
    stored bytes were trusted whole:

      THE BYTES WERE NOT OWNED. An empty or truncated record decoded straight
      into a `JSONDecodeError` escaping this contract's taxonomy. A record this
      component cannot read is not an answer it may return, and it is not an
      answer it may quietly discard either -- re-deriving would move
      `created_at` and could contradict an answer a caller already holds. So it
      fails closed.

      THE ANSWER WAS NOT BOUND. Custody is keyed by ATTEMPT, and an attempt is
      not an operation: a second freeze under a different operation id and
      signature received the first operation's result. Replay reproduces the
      settled answer for the request that settled it; for any other request it
      is a different question with a stored answer attached, which is exactly
      the retry ambiguity the taxonomy has a code for.

    "Replay sits above every state read" was never "replay before identity
    proof", and reading it that way is what this is.
    """
    record = os.path.join(custody, _COMMITTED)
    if not os.path.isfile(record):
        return None
    with open(record, "rb") as reading:
        raw = reading.read()
    try:
        settled = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        raise ContractRefusal(
            "integrity", "schema",
            f"the committed result for attempt "
            f"{name_value(expected['result_id'])} is not a readable document; "
            f"a record this component cannot read is not a settled answer, and "
            f"deriving a fresh one would answer a question somebody may "
            f"already hold a different answer to")
    if type(settled) is not dict or "manifest_digest" not in settled:
        raise ContractRefusal(
            "integrity", "schema",
            f"the committed result for "
            f"{name_value(expected['result_id'])} is not a sealed result "
            f"document")
    # THE DIGEST IS THE COMPLETENESS PROOF. `_commit` stores the body with the
    # digest OF that body beside it, so a record whose digest re-derives is a
    # record whose every member arrived -- which a length check or a successful
    # decode cannot tell you.
    claimed = settled["manifest_digest"]
    body = {name: value for name, value in settled.items()
            if name != "manifest_digest"}
    if digest(body) != claimed:
        raise ContractRefusal(
            "integrity", "digest",
            f"the committed result for "
            f"{name_value(expected['result_id'])} does not re-derive its own "
            f"manifest digest; a record that describes itself wrongly is not "
            f"evidence of what was settled")
    for member in _BOUND:
        if body.get(member) != expected[member]:
            raise ContractRefusal(
                "ambiguous", "operation",
                f"this attempt already settled a result whose {member} is not "
                f"the one this request carries; an answer stored under an "
                f"attempt is that operation's answer, and replaying it for a "
                f"different one would return a result nobody asked for")
    return settled


def _commit(custody, body):
    """Publish the settled answer, last AND atomically.

    Written under a private name, forced to the device, then renamed onto the
    final one. The final name therefore never exists holding an incomplete
    record: the rename is what publishes, and it publishes bytes that were
    already whole.
    """
    os.makedirs(custody, exist_ok=True)
    staged = os.path.join(custody, _COMMITTING)
    with open(staged, "wb") as writing:
        writing.write(json.dumps(body, sort_keys=True,
                                 ensure_ascii=False).encode("utf-8"))
        writing.flush()
        # THE RENAME IS ATOMIC AGAINST OTHER READERS; this is what makes it
        # atomic against a HOST that stops. Without it the directory entry can
        # reach the device before the content it names.
        os.fsync(writing.fileno())
    os.replace(staged, os.path.join(custody, _COMMITTED))
    return body


def _answered(name, declared, attempt_id, manifest, held):
    """One `artifactOutput` over material already in custody.

    Written once because the fresh seal and the retry replay must produce the
    IDENTICAL document: two spellings of one answer would make an exact retry
    return something the first call did not.
    """
    return {"name": name, "type": declared["type"], "status": "present",
            "content_manifest": manifest, "result_metadata": {},
            "artifact": {"artifact_id": f"{attempt_id}:{name}",
                         "media_type": "application/octet-stream",
                         "bytes": manifest["total_bytes"],
                         "content_digest": manifest["tree_digest"],
                         "locator": f"file://{held}"}}


def _frozen(place):
    """The tree made READ-ONLY, deepest first.

    Depth-first because a directory made unwritable before its children are
    is a directory whose children can no longer be changed either -- by this
    process. The order that matters is the one that leaves nothing writable
    when it returns.
    """
    for root, directories, files in os.walk(place, topdown=False):
        for one in files:
            os.chmod(os.path.join(root, one), workspaces.READ_ONLY_FILE)
        for one in directories:
            os.chmod(os.path.join(root, one), workspaces.READ_ONLY_DIR)
    os.chmod(place, workspaces.READ_ONLY_DIR)


# THE WORKER'S COMPLETION ENVELOPE, at the fixed name W14251 pinned.
#
# `/output/output.json` container-side; host-side it is this name under the
# assignment's writable root, which is the same tree the declared outputs live
# in. The name is a CONSTANT of the contract rather than an operand -- a path
# an assignment could vary is a path this manager could be pointed at wrongly.
COMPLETION_MANIFEST = "output.json"

# How much of the worker's document this manager will read before refusing.
# It is a worker-written file in a worker-writable tree, so its size is the
# worker's decision and the bound has to be this manager's.
MAX_COMPLETION_BYTES = 4 * 1024 * 1024


def _read_without_following(place):
    """The completion signal's bytes, from a descriptor that cannot be a link.

    Seventh review [P1]: this used `os.path.isfile` and then an ordinary
    `open`, and BOTH follow symlinks. So a worker could leave an `output.json`
    pointing anywhere on the host and this manager would read it -- turning a
    fixed path the contract chose into a path the worker chose, and
    contradicting the linked-output refusal this Work already applies to every
    other byte it takes.
    
    `O_NOFOLLOW` refuses the link itself rather than resolving it, and the
    regular-file check is on the OPENED DESCRIPTOR rather than on the path, so
    nothing can be replaced between the check and the read. The same descriptor
    is then what is read.
    """
    try:
        # `O_NONBLOCK` TOO, and it is not decoration. A named pipe at this
        # name opens and then BLOCKS until somebody writes to it -- so a
        # worker could hang the manager's freeze with one `mkfifo`, and the
        # mode check below could never reach it because the open never
        # returns. Measured: without the flag the case covering this rule does
        # not terminate. On a regular file it costs nothing.
        handle = os.open(place,
                         os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    except OSError:
        # ABSENT AND UNREADABLE ARE ONE ANSWER HERE, deliberately: a link at
        # this name is not a completion signal, and neither is nothing. What
        # decides the outcome is the disposition, one line up.
        return None
    try:
        if not stat.S_ISREG(os.fstat(handle).st_mode):
            raise ContractRefusal(
                "integrity", "file-type",
                f"the worker's {name_value(COMPLETION_MANIFEST)} is not a "
                f"regular file; the completion signal is a document at a path "
                f"this contract fixed, not whatever a worker pointed that "
                f"name at")
        return os.read(handle, MAX_COMPLETION_BYTES + 1)
    finally:
        os.close(handle)


def _completion_envelope(roots, declared, assignment, disposition):
    """Open, OWN and hold the worker's `/output/output.json`.

    Sixth review [P1], and the correction is a boundary rather than a member.
    This adapter took `completion_manifest_digest` as an optional CALLER
    OPERAND and copied it into the receipt: a claim that a validation happened,
    from the party whose validation it was supposed to be. Nothing opened the
    document, nothing recomputed its digest, and nothing held its answers
    against the declarations.

    THE SIDE OF THE BOUNDARY IS THE POINT. W6633 owns the worker that PUBLISHES
    the envelope; this Work's manager owns VALIDATING it before freeze and the
    receipt over what it validated. My progress account had that backwards --
    I said the consumer belonged with the publisher, which would leave the
    document permanently unread by the only party that needs to check it.

    THREE THINGS HAPPEN HERE AND THEY ARE THREE DIFFERENT QUESTIONS:

      the SHAPE and its standalone semantics, by W14251's settled validator --
      unique names, non-overlapping paths, the reserved output name, and a
      status that agrees with its integrity evidence;
      the DIGEST, recomputed over the bytes this manager read rather than
      taken from anybody's word;
      and §12 RULE 15, which needs the input manifest and so cannot live in a
      validator handed one document: one answer per declaration, no extras, no
      omissions, exact name/type/path, and no `missing-optional` answer for a
      declaration the manager marked required.

    A COMPLETED FREEZE WITHOUT AN ENVELOPE REFUSES. The envelope IS the
    completion signal, so a worker that published none has not completed --
    whatever it told the manager. The other dispositions may have none, because
    those are the endings where a worker may have died before publishing.
    """
    place = os.path.join(roots["workspace"], COMPLETION_MANIFEST)
    raw = _read_without_following(place)
    if raw is None:
        if disposition == "completed":
            raise ContractRefusal(
                "refused", "precondition",
                f"this assignment is completed and published no "
                f"{name_value(COMPLETION_MANIFEST)}; the worker's envelope is "
                f"the completion signal, so a result without one is a "
                f"completion nothing signalled")
        return None, None
    if len(raw) > MAX_COMPLETION_BYTES:
        raise ContractRefusal(
            "integrity", "limit",
            f"the worker's {name_value(COMPLETION_MANIFEST)} is wider than "
            f"{MAX_COMPLETION_BYTES} bytes; a document this manager cannot "
            f"hold is not one it will validate")
    try:
        document = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        raise ContractRefusal(
            "integrity", "schema",
            f"the worker's {name_value(COMPLETION_MANIFEST)} is not a "
            f"readable document")
    # W14251'S SETTLED VALIDATOR, consumed rather than reimplemented. It owns
    # the shape, verifies the document identifies itself, walks §13, and
    # applies the completion semantics that Work put in the shipped layer
    # precisely so this manager would not have a second copy of them.
    owned = check_manifest_structure(document, "completionManifest",
                                     what="a worker completion envelope")
    # THIS ASSIGNMENT, EXACTLY. Seventh review [P1]: standalone validation
    # proves the reference is well formed and the comparison below proves the
    # answers match the declarations -- and two assignments of one Work can
    # declare identical outputs, so neither says the document is THIS
    # attempt's. A generation-2 envelope was being bound into generation 1's
    # receipt. Compared before any custody is touched.
    #
    # W19784, 2026-08-26: THIS COMPARISON FINALLY HAS A SATISFIABLE OTHER SIDE,
    # and it needed no change to gain one. Until that ruling nothing inside the
    # execution container carried the authority generation, so a conforming
    # worker could not author an `assignment_ref` this could match -- the
    # manager's half of the rule was right and the worker's half was
    # impossible. `/input/assignment.json` is now the one source the worker
    # copies from, and what is compared here is that copy against this
    # manager's own assignment. Conformance obligation `A-18`.
    if owned["assignment_ref"] != assignment:
        raise ContractRefusal(
            "stale-assignment", "generation",
            f"the worker's {name_value(COMPLETION_MANIFEST)} answers another "
            f"assignment than the one this freeze settles; identical "
            f"declarations do not make one attempt's envelope another's")
    _answers_the_assignment(owned, declared)
    body = {name: value for name, value in owned.items()
            if name != "manifest_digest"}
    # RECOMPUTED OVER THE BYTES THIS MANAGER READ.
    #
    # MEASURED AS AN EQUIVALENCE, and said so rather than claimed otherwise:
    # `check_manifest_structure` has already refused a document whose declared
    # digest does not describe it, so lifting `owned["manifest_digest"]` gives
    # the identical value and no case can tell the two apart.
    #
    # It is still computed here, and the reason is about where the value comes
    # from rather than about what it equals. The whole correction this round
    # is that the receipt binds something this manager DERIVED instead of
    # something a caller handed it, and a line that read the derivation off
    # the document it is deriving from would be the same shape one layer in.
    return owned, digest(body)


def _answers_the_assignment(envelope, declared):
    """§12 rule 15: the envelope against the exact declarations.

    A rule that needs two documents, which is why W14251 states it in the
    contract rather than in the completion envelope's own validation.
    """
    answers = {}
    for one in envelope["outputs"]:
        if one["name"] in answers:
            raise ContractRefusal(
                "integrity", "schema",
                f"the worker's envelope answers {name_value(one['name'])} "
                f"twice; a name identifies a declaration and two answers to "
                f"one is not one answer (§12 rule 15)")
        answers[one["name"]] = one
    for name in sorted(set(answers) - set(declared)):
        raise ContractRefusal(
            "integrity", "schema",
            f"the worker's envelope answers {name_value(name)}, which this "
            f"assignment did not declare (§12 rule 15)")
    for name, declaration in sorted(declared.items()):
        one = answers.get(name)
        if one is None:
            raise ContractRefusal(
                "integrity", "schema",
                f"the worker's envelope does not answer declared output "
                f"{name_value(name)}; a declaration is answered or the "
                f"assignment is not complete (§12 rule 15)")
        for member in ("type", "path"):
            if one[member] != declaration[member]:
                raise ContractRefusal(
                    "integrity", "schema",
                    f"the worker's envelope answers {name_value(name)} with "
                    f"{member} {name_value(one[member])} and this assignment "
                    f"declared {name_value(declaration[member])} "
                    f"(§12 rule 15)")
        if declaration["required"] and one["status"] == "missing-optional":
            raise ContractRefusal(
                "refused", "precondition",
                f"the worker's envelope answers required output "
                f"{name_value(name)} as missing-optional; whether an output "
                f"was required is this manager's declaration, and a worker "
                f"that could answer it away would be settling its own "
                f"attempt (§12 rule 15)")
    return envelope


def sealed_result(request, *, roots, declared, identity, custody,
                  input_manifest_digest):
    """The frozen result manifest, over the declared outputs only.

    THE MEASUREMENT IS TAKEN TWICE, and the second one is the point. Between
    measuring a tree and freezing it, a worker that is not as quiescent as the
    engine said can replace a file -- so the tree is frozen and measured
    AGAIN, and a digest that moved is a race this component refuses rather
    than a result it describes wrongly.
    """
    taken = boundaries.document(request, "a freeze request",
                                required=("attempt_id", "assignment",
                                          "disposition", "now", "operation"))
    now = boundaries.instant(taken["now"], "a freeze instant")
    # REPLAY SITS ABOVE EVERY STATE READ, which is the rule this module was
    # corrected for once already and got only half right: custody answered a
    # present artifact but nothing answered for the whole result.
    # THE BINDING IS COMPOSED BEFORE CUSTODY IS READ, so replay is a
    # comparison rather than an adoption. Every member of it is a fact this
    # call already holds: four from the request the manager signed, two owned
    # at construction.
    expected = {
        "result_id": f"result-{taken['attempt_id']}",
        "assignment_ref": taken["assignment"],
        "disposition": taken["disposition"],
        "freeze_operation": dict(taken["operation"]),
        "input_manifest_digest": input_manifest_digest,
        "policy_digest": identity["policy_digest"],
    }
    settled = _committed_result(custody, expected)
    if settled is not None:
        return settled
    # THE WORKER'S ENVELOPE IS READ ONLY FOR A FRESH FREEZE, and the ordering
    # is the seventh review's [P1].
    #
    # I put this above the replay and broke the rule I have been corrected on
    # three times in this module: replay sits above every state read. The
    # envelope is worker state -- it lives in a tree the worker owns and which
    # cleanup removes -- so consulting it first made an exact retry depend on
    # a file that may legitimately be gone, and refused where the committed
    # receipt was sitting right there with the digest already bound.
    #
    # THE ENVELOPE IS THEREFORE NOT PART OF THE REPLAY BINDING EITHER. A
    # changed `output.json` is not an operand of an already committed
    # operation: the operation was settled over the envelope this manager
    # validated at the time, and the receipt records which one that was. What
    # binds a replay is the request, and the request does not carry it.
    _envelope, completion_manifest_digest = _completion_envelope(
        roots, declared, taken["assignment"], taken["disposition"])
    writable = roots["workspace"]
    answered = []
    for name, one in sorted(declared.items()):
        place = os.path.join(writable, one["path"])
        # CONTAINMENT FIRST. A declared path that leaves the writable root is
        # a declaration this component refuses to act on, whatever is there.
        workspaces._contained(place, writable, f"the output {name}")
        # NO PER-OUTPUT REPLAY HERE. A partially copied custody tree looks
        # exactly like a complete one to `isdir`, so staging re-runs from the
        # live output and overwrites whatever prefix an interrupted attempt
        # left; the committed record above is what makes a whole answer
        # replayable.
        held = os.path.join(custody, name)
        if not os.path.isdir(place):
            if one["required"]:
                raise ContractRefusal(
                    "refused", "precondition",
                    f"output {name_value(name)} is required and this "
                    f"assignment produced nothing at "
                    f"{name_value(one['path'])}")
            # MISSING-OPTIONAL IS AN ANSWER, not silence. The declaration was
            # made and it is answered; a receiver that saw nothing would lose
            # the fact that the worker was asked.
            # THE FROZEN `artifactOutput`, as a plain document. These are
            # members of a WORKER-PRODUCED manifest the frozen schema
            # validates, not one of this manager's own closed documents, so
            # they are built here and proved by `record_frozen_result`.
            answered.append({"name": name, "type": one["type"],
                             "status": "missing-optional",
                             "content_manifest": None, "artifact": None,
                             # W14251: OPAQUE, and empty is the honest value.
                             # A worker that has nothing format-specific to
                             # say says nothing; the manager never reads it
                             # either way.
                             "result_metadata": {}})
            continue
        after = _staged(place, held, one, name)
        answered.append(_answered(name, one, taken["attempt_id"], after,
                                  held))
    body = {
        "version": {"major": 1, "minor": 0},
        "manifest_id": f"result-{taken['attempt_id']}",
        "created_at": now, "extensions": {},
        "schema": "baton.worker-manifest/result",
        "result_id": f"result-{taken['attempt_id']}",
        "assignment_ref": taken["assignment"],
        "input_manifest_digest": input_manifest_digest,
        "policy_digest": identity["policy_digest"],
        "disposition": taken["disposition"],
        "outputs": answered, "evidence": [],
        "freeze_operation": dict(taken["operation"]),
        "manager_observed_at": now,
    }
    if completion_manifest_digest is not None:
        # OPTIONAL IN THE FROZEN SCHEMA, and absent rather than null when there
        # is nothing to name: a receipt that omits it is one produced for a
        # worker that published no envelope, which is every worker until W6633
        # publishes one.
        body["completion_manifest_digest"] = completion_manifest_digest
    # §13 BEFORE IT LEAVES. A sealed result is a portable document composed
    # from paths and identities this component was handed, and a locator is
    # exactly the kind of member a credential rides in.
    check_no_durable_secret(body, what="a sealed result")
    # LAST, after every declared output is staged and frozen above.
    return _commit(custody, {**body, "manifest_digest": digest(body)})


def collected_result(operands, *, custody, declared):
    """What the manager may take custody of, over the already frozen tree.

    NOTHING NEW IS MEASURED HERE. The freeze is what decided this result's
    identities and digests, and `intake._compared` compares every one of them
    against what the freeze recorded -- so a collection that measured again
    would be offering a second opinion about bytes that are already frozen.
    The one member intake ADOPTS is the custody locator, because where the
    material now is is the one fact the freeze could not already know.
    """
    # THE OPERANDS `intake.request_intake` ACTUALLY SENDS, read off that
    # caller rather than guessed: it passes the result manifest digest too,
    # because an adapter handed only an attempt id would have to guess which
    # frozen result it is collecting. A required set that omitted it refused
    # every real call.
    taken = boundaries.document(operands, "a collect request",
                                required=("attempt_id", "assignment",
                                          "result_id", "result_manifest_digest",
                                          "output_names", "operation"))
    artifacts = []
    _list(taken["output_names"], "the collected output names")
    # ITERATED IN PLACE AND SORTED AFTERWARDS. `sorted(...)` is a call the
    # boundary derivation cannot follow, so sorting first left the identity
    # rule below owning a value nothing could attribute to this operand.
    for name in taken["output_names"]:
        one = declared.get(
            boundaries.identity(name, "a collected output name"))
        if one is None:
            raise ContractRefusal(
                "integrity", "schema",
                f"the collection names output {name_value(name)}, which this "
                f"assignment does not declare")
        # CUSTODY, NOT THE WORKSPACE. The freeze already decided this
        # result's identities and digests over bytes this manager holds; the
        # live tree is the worker's and may have moved since.
        place = os.path.join(custody, name)
        if not os.path.isdir(place):
            continue
        manifest = workspaces.directory_manifest(place)
        artifacts.append({
            "artifact_id": f"{taken['attempt_id']}:{name}",
            "content_digest": manifest["tree_digest"],
            "bytes": manifest["total_bytes"],
            "custody_locator": f"file://{place}"})
    artifacts.sort(key=lambda one: one["artifact_id"])
    answer = {"result_id": taken["result_id"], "artifacts": artifacts}
    check_no_durable_secret(answer, what="a collection observation")
    return answer
