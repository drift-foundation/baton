"""THE DETERMINISTIC PUBLICATION OF ONE RETAINED OUTPUT: the read-only
staging, the absolute deadline, the adoption, the custody it enters and the
one handoff that opens review.

W385695 internal checkpoint 2, under DESIGN REC-9 and the owner-selected
contract `work/records/2026/11/finding-v12-output-publication-recovery/
CONTRACT-PROPOSED-385720.md`, whose pending-approval wording is superseded by
that dossier's FINDING.md "Consolidated owner selection — 2026-11-22". The
owning record is `work/records/2026/11/finding-v12-output-publication-
recovery/`.

WHAT CHECKPOINT 1 LEFT AND THIS PICKS UP. `publication_recovery` resolves the
ORIGINAL host-held output through its owner, qualifies the producer's own
adapter attribution, records the owner's exact decision and -- now -- admits
one `/4` recovery Job carrying one publication stage and one review stage
gated on it. At that point nothing has been published: no byte has been
staged, no attempt has been claimed, nothing is frozen and the review gate is
shut. This module is every act between there and a candidate a reviewer can
be offered, and there are four:

  1. `stage_input` -- READ-ONLY STAGING. The approved original is resolved
     AGAIN through the host owner, under positive writer cessation, and copied
     into a recovery-owned private input root by the one no-follow
     copy-and-measure pass this build has. The staged manifest binds the
     original root identity, the original attempt, the measured digest and
     the owner decision; the copy's measured tree digest is held against the
     digest the decision bound, and a mismatch REFUSES. The root is then
     frozen read-only, which is how the new execution is delivered bytes it
     cannot write.
  2. THE CONFINED DETERMINISTIC ADOPTION, which this module DECIDES AND
     MEASURES and does not perform. `prepare_launch` reads the publication
     stage's own FRESH assignment from its live episode, derives the absolute
     publication deadline from the PERSISTED stage execution admission and
     commits a durable launch intent BEFORE any runtime is started. The
     adoption itself is run by the separately selected deterministic
     publication WORKER, in its own container, through the ordinary worker
     lifecycle: the staged tree is bound READ-ONLY inside `/input`, the copy
     is supervised to the absolute instant, and the worker publishes the
     ordinary completion envelope. `record_adoption` then MEASURES this
     attempt's output roots -- only after the runtime was positively observed
     to stop -- and holds them to the approved tree digest and to the
     SEPARATELY declared, separately bounded provenance descriptor. Zero
     models and zero producer-verification commands, counted from the
     worker's own envelope and held to zero. `publish` is the pass's
     accounting of that one launch and never launches.
  3. `take_custody` -- NORMAL COMPLETION AND INTAKE, BOUND. The existing
     public owners freeze the result and take it into custody, called by the
     publication worker's own ordinary ending; nothing here reimplements or
     even requests either, and nothing here starts or stops a runtime. What
     this act adds is the comparison nobody else can make: that the frozen
     result's candidate output is byte-for-byte the original the owner
     approved, that the provenance is a SEPARATE output inside its own
     descriptor, and that the intake receipt belongs to this attempt.
  4. `hand_off` -- THE ONE RECORD THAT OPENS REVIEW. It binds the decision,
     the failed attempt, the original candidate, the new publication attempt,
     its frozen result, its custody, its intake receipt and the reviewer's
     own input and servability. `execution_gate` is shut until it commits and
     there is no other switch: an approval, a qualified producer result, a
     candidate digest, a submitted graph edge or an operator's journalled
     account cannot open it.

WHAT IT REFUSES, every one a ruling rather than a preference:

  * THE ORIGINAL IS STILL THE TRUST ROOT, AND IT IS RE-READ. Staging does not
    trust the admission's recorded digest: it asks the host owner for the
    original again, under a completed preparation, proved object identity and
    settled writers, and compares. A missing, replaced or unreadable original
    HOLDS. The approved selection is what the staged bytes are compared with
    BEFORE anything launches.
  * THE ORIGINAL IS NEVER WRITABLE AND NEVER MUTATED. The copy is out of the
    original into a private root; the original's own `output.json` is not
    written, its tree digest is unchanged by this whole path, and the staged
    root is frozen before the new execution sees it.
  * THE PROVENANCE IS SEPARATE. It is its own declared output with its own
    16384-byte, one-regular-file, no-links descriptor, and it NEVER alters the
    adopted proposal tree digest -- which is the whole point of the capability
    and is asserted on the measurement rather than argued.
  * NO PROVIDER AND NO PRODUCER VERIFIER. The pinned request the worker is
    delivered carries no command, no credential slot and no provider
    configuration, the publication worker's deployment declares no credential
    at all, and the worker's envelope must declare zero provider invocations
    and zero verifier invocations. The reviewer's own required verification
    stays owed.
  * THE DEADLINE IS ABSOLUTE AND IS ENFORCED TWICE. It is derived from the
    PERSISTED publication-stage execution admission -- the same durable origin
    the stage wall is derived from -- so a restart re-derives the same instant
    and never a fresh 900 seconds, and the launch intent binds it once. The
    WORKER is delivered that instant, runs its copy as a child process group
    and ends the whole group at it. The HOST enforces it independently:
    `job_control`'s evaluation journals the expiry and the ordinary
    cancellation pass orders the exact runtime to stop through the engine
    owner, whether or not the worker is still there. A reached deadline stops
    new effects and is never evidence that anything ceased; cessation is the
    runtime owner's positive observation.
  * UNCERTAINTY HOLDS AND NEVER REPEATS. The intent is durable before the
    start and the start is the Worker Manager's own journalled operation, so
    a lost start reply is reconciled against the engine's listing of the
    exact runtime -- attached, never started twice. A worker that faulted, an
    exchange that was lost, a runtime the host lost or cannot ask about: each
    is journalled UNCERTAIN, nothing is recorded as published, and no second
    launch is made.
  * CANCELLATION, EXPIRY AND UNKNOWN AUTHORITY STOP NEW EFFECTS AND RETAIN
    EVIDENCE. Every act is fenced, every fence is re-asked, and nothing
    already recorded is deleted or rewritten.
  * REVIEW IS NOT RUNNABLE UNTIL THE HANDOFF IS VALID. `execution_gate`
    derives `open` from the committed handoff and from nothing else, and the
    handoff is composed only when every binding above is present and agrees.
"""

import json
import os
import stat

from ..contracts import ContractRefusal, digest
from ..contracts.errors import name_value
from ..worker_manager import boundaries, frozen_output_of
from ..worker_manager.workspaces import copied_manifest, directory_manifest
from . import (cancellation, documents, episodes, job_control,
               publication_recovery, role_contract, submission)
from .store import job_signature

__all__ = ["PUBLICATION_SEAM", "HOST_OUTPUT", "HOST_EXCLUSION",
           "RUNTIME_PORT", "check_publication_seam",
           "REQUEST_SCHEMA", "REQUEST_DOCUMENT", "REQUEST_MEMBERS",
           "METADATA_KEY", "COMPLETION_MANIFEST",
           "prepare_launch", "publication_request", "record_adoption",
           "STAGED_ROOT", "PROVENANCE_ROOT", "STAGING_LOCK",
           "MAX_STAGED_ENTRIES", "MAX_STAGED_BYTES",
           "STAGING_KIND", "STAGING_MEMBERS", "staging_operation_id",
           "staging_of",
           "LAUNCH_KIND", "LAUNCH_MEMBERS", "launch_operation_id",
           "launch_of",
           "RESULT_KIND", "RESULT_MEMBERS", "result_operation_id",
           "result_of",
           "HOLD_KIND", "HOLD_MEMBERS", "hold_operation_id", "hold_of",
           "CUSTODY_KIND", "CUSTODY_MEMBERS", "custody_operation_id",
           "custody_of",
           "HANDOFF_KIND", "HANDOFF_MEMBERS", "handoff_operation_id",
           "handoff_of",
           "PROVENANCE_SCHEMA",
           "GATE_UNAVAILABLE", "GATE_VALIDATED", "GATE_REASONS",
           "GATE_BINDINGS",
           "deadline_of", "fresh_assignment_of", "provenance_document",
           "stage_input", "publish", "take_custody", "hand_off",
           "execution_gate", "publication_readiness", "advance_publication",
           "ENDED_KIND", "ENDED_MEMBERS", "ENDED_OUTCOMES", "ending_of",
           "UNKNOWN_KIND", "KNOWN_KIND", "UNKNOWN_MEMBERS", "unknown_of",
           "SETTLED_KIND", "SETTLED_MEMBERS", "settlement_of",
           "OWNER_ITEM_KIND", "OWNER_ITEM_MEMBERS", "owner_item_of",
           "owner_items_of", "settle",
           "ACTS", "ACT_OUTCOMES"]


def _refuse(message, *, category="refused", code="precondition"):
    raise ContractRefusal(category, code, message)


def _denied(message):
    raise ContractRefusal("policy", "denied", message)


# -- 1. the seam a deployment composes ---------------------------------------
#
# FIVE MEMBERS, each one an OWNER rather than a convenience, and the module
# decides with all of them and holds none of them itself.
#
#   control    the Worker Manager's control store: where the attempt, its
#              workspace preparation, its runtime observations, its frozen
#              result and its intake receipt live. Read only through that
#              package's own public readers.
#   host       the owner of the ORIGINAL output -- the trust root door. The
#              ONLY way to the original bytes; a path is never an operand.
#   exclusion  the host's cessation evidence about an attempt. `unknown` holds.
#   workspaces the private root recovery-owned staging is allocated under. A
#              sibling of the stores and never a child of custody: a writable
#              tree inside immutable evidence is a wider boundary than the one
#              the contract declares.
#   runtime    the serving composition's READ of the publication execution's
#              exchange: whether the confined worker answered its one command,
#              faulted, or was lost. It reads and never starts anything.
#
# AND THERE IS NO WRITER HERE ANY MORE, which is the whole of this revision.
# The first cut of this seam carried a `writer` whose `adopt` copied the
# staged bytes IN THIS PROCESS, on the host, straight into the attempt's
# output root. That is not the execution REC-9 and contract section 2
# describe: no read-only `/input`, no containment, no supervised bound and no
# runtime anybody could observe stopping. The adoption is now performed by the
# deterministic publication WORKER, launched by the ordinary worker lifecycle
# over the ordinary launch, workspace, token and engine owners
# (`tools.publication_worker.PublicationStage`), and what this module does is
# decide BEFORE that launch (`prepare_launch`) and MEASURE AFTER the runtime
# has positively stopped (`record_adoption`). The custody owners the first cut
# also carried (`authority`, `adapter`) are gone with it: the freeze and the
# intake are the ordinary ending's, performed by the worker's own composition,
# and this module reads their records.
PUBLICATION_SEAM = ("control", "host", "exclusion", "workspaces", "runtime")
HOST_OUTPUT = ("instance", "output_of")
HOST_EXCLUSION = ("instance", "evidence_of")
# `observation_of` and `settle` are the two members review
# 2026-11-23T20-28-00Z's settlement finding added. The first is a FRESH read
# of the engine through the serving composition, answered as known or not
# known -- the recorded runtime axis is the last thing somebody saw and is not
# that. The second is the composition's own supported fourth ending
# (`abandon_attempt`): the one operation that removes the exact runtime,
# proves it absent, retains the workspace and returns the exact token.
RUNTIME_PORT = ("instance", "terminal_of", "observation_of", "settle")

# WHERE THE STAGED ORIGINAL AND THE RECOVERY'S OWN PROVENANCE SIT inside the
# private staging root. Two names and they are two: the staged original is
# the read-only input a publication consumes, and the provenance is the
# recovery's own account, which is a SEPARATE declared output and must never
# be inside the tree whose digest this capability exists to preserve.
STAGED_ROOT = "input"
PROVENANCE_ROOT = "provenance"
STAGING_LOCK = ".staging.lock"
PRIVATE = 0o700
READ_ONLY_FILE = 0o444
READ_ONLY_DIR = 0o555

# THE CEILINGS THE STAGING COPY IS BOUNDED BY, read from the declaration owner
# that states them rather than restated. W385694's exact selected revision is
# what a recovery publishes under, so it is also the most a recovery may
# STAGE: a copy that could exceed the declaration would be a copy nothing
# could publish, made at full cost first.
MAX_STAGED_ENTRIES = role_contract.MAX_OUTPUT_ENTRIES
MAX_STAGED_BYTES = role_contract.MAX_PROPOSAL_BYTES

# THE PROVENANCE DOCUMENT'S OWN IDENTITY. It is a document and not prose: a
# reviewer and an operator read it, and an unversioned account would be one
# nobody could tell had changed shape.
PROVENANCE_SCHEMA = "baton.v12.output-publication-provenance/1"
PROVENANCE_FILE = "recovery-provenance.json"

# THE PINNED REQUEST THE CONFINED WORKER IS DELIVERED, at one fixed name in
# its read-only input root. `v12/worker/publication_entry.py` spells these a
# second time because a worker in a container cannot import this package; a
# conformance case holds the two spellings equal.
REQUEST_SCHEMA = "baton.v12.output-publication-request/1"
REQUEST_DOCUMENT = "publication.json"
REQUEST_MEMBERS = ("schema", "decision_id", "job_id", "attempt_id",
                   "deadline", "staged", "provenance", "outputs")
# The worker's per-output account inside its completion envelope, and the
# envelope's own name in the attempt's output root.
METADATA_KEY = "baton.v12.output-publication/1"
COMPLETION_MANIFEST = "output.json"
MAX_ENVELOPE_BYTES = 4 * 1024 * 1024


def check_publication_seam(seam, *, what="the publication seam"):
    """The five members this module decides with, proved before anything.

    `retained_verification.check_verification_seam`'s rule and its reason: a
    deployment that discovered a missing owner halfway through would have
    staged an original, started an execution or published a result and then
    been unable to finish accounting for it.
    """
    def member(name):
        # AN OBJECT OR THE ALREADY-PROVED MAPPING, because this check is
        # IDEMPOTENT on purpose: `advance_publication` proves the seam once
        # before it spends anything and then hands it to each act, and each
        # act proves it again because each is also a supported entry point an
        # owner surface may call directly. `boundaries.document` is the wrong
        # tool here for a reason that is not stylistic: a seam carries OWNERS,
        # and that boundary refuses an operand that carries behaviour -- which
        # is exactly what a control store, a host port and a runtime reader
        # are.
        if isinstance(seam, dict):
            return seam.get(name)
        return getattr(seam, name, None)

    missing = [one for one in PUBLICATION_SEAM if member(one) is None]
    if missing:
        _refuse(f"{what} supplies exactly {', '.join(PUBLICATION_SEAM)}; "
                f"this one carries no {', '.join(missing)}",
                category="refused", code="capability")
    taken = {one: member(one) for one in PUBLICATION_SEAM}
    for member_name, members in (("host", HOST_OUTPUT),
                            ("exclusion", HOST_EXCLUSION),
                            ("runtime", RUNTIME_PORT)):
        port = taken[member_name]
        absent = [one for one in members
                  if getattr(port, one, None) is None]
        if absent:
            _refuse(f"{what}'s {member_name} supplies exactly "
                    f"{', '.join(members)}; this one carries no "
                    f"{', '.join(absent)}",
                    category="refused", code="capability")
    place = taken["workspaces"]
    boundaries.text(place, f"{what}'s private staging root")
    if not os.path.isabs(place):
        _refuse(f"{what} names private staging root {name_value(place)}; an "
                f"allocation root is one absolute path",
                category="integrity", code="path")
    if os.path.islink(place) or not os.path.isdir(place):
        _refuse(f"{what}'s private staging root {name_value(place)} is not a "
                f"directory this manager can allocate under",
                category="integrity", code="path")
    return taken


def _agreeing_instance(seam, *, what):
    """The control store this act writes is the HOST PORT's own.

    `retained_recovery._agreeing_control`'s rule, applied to the one operand
    these acts take that the ports do not supply: a handle the host port would
    have refused must not reach this execution through a second door.
    """
    declared = getattr(seam["host"], "instance", None)
    held = declared() if callable(declared) else None
    expected = (held or {}).get("control_store")
    here = getattr(seam["control"], "database", None)
    if expected is not None \
            and os.path.realpath(str(here or "")) \
            != os.path.realpath(str(expected)):
        _refuse(f"{what} reads and writes {name_value(here)} and instance "
                f"{name_value((held or {}).get('root'))} owns "
                f"{name_value(expected)}; an execution composed over another "
                f"deployment's store is an execution in another deployment")
    return seam


# -- 2. the durable records --------------------------------------------------
#
# SIX KINDS, all ordinary operations of this store's existing journal, for
# `publication_recovery`'s reasons: exact replay, collision on changed
# operands, and a committed result later incarnations read instead of
# re-deciding. No schema change and no new table.
#
# THE IDENTITIES ARE KEYED BY THE RECOVERY JOB and never by a clock or a
# counter, so every incarnation derives the same operation name for the same
# act -- which is what makes "lost reply" a reconciliation rather than a
# second effect.
STAGING_KIND = "publication.input-staged"
LAUNCH_KIND = "publication.adoption-intent"
RESULT_KIND = "publication.adopted"
HOLD_KIND = "publication.adoption-uncertain"
CUSTODY_KIND = "publication.custody"
HANDOFF_KIND = "publication.candidate-handoff"
# FOUR MORE, for what happens when a recovery does NOT publish (review
# 2026-11-23T20-28-00Z; COMPLETION-PLAN-385909 outcomes 1 and 3).
#
#   ENDED      this recovery's publication did not and will not publish, and
#              WHY is known: its worker faulted, its bound was reached, or it
#              was cancelled. A different durable fact from HOLD, which says
#              nobody knows. Recorded once and never revised.
#   UNKNOWN    a fresh read of the engine could not be made. It records that
#              the runtime's cessation is NOT KNOWN as of an instant, so a
#              status read never presents the last recorded axis as current.
#   SETTLED    the supported settlement finished: the exact runtime is
#              positively gone, its workspace retained, its token returned.
#   OWNER_ITEM the one durable item delivered to the owner who decided, with
#              the retained evidence and whatever effects remain.
ENDED_KIND = "publication.ended"
UNKNOWN_KIND = "publication.runtime-unknown"
# AND ITS COUNTERPART: a later fresh read that DID succeed. The pair is
# appended in alternation, one record per change of knowledge and never one
# per tick, so "not known since T" is true exactly until something was learned
# again -- and a journal of immutable records can still say so.
KNOWN_KIND = "publication.runtime-known"
SETTLED_KIND = "publication.settled"
OWNER_ITEM_KIND = "publication.owner-item"
ENDED_OUTCOMES = ("failed", "expired", "cancelled")

STAGING_MEMBERS = ("decision_id", "job_id", "prior_job_id", "attempt_id",
                   "original", "staged", "provenance", "input_digest",
                   "delivery", "cessation", "staged_at")
LAUNCH_MEMBERS = ("decision_id", "job_id", "stage_id", "attempt_id",
                  "assignment", "staged_digest", "deadline", "intended_at")
RESULT_MEMBERS = ("decision_id", "job_id", "stage_id", "attempt_id",
                  "assignment", "outcome", "adopted", "provenance",
                  "invocations", "deadline", "adopted_at")
HOLD_MEMBERS = ("decision_id", "job_id", "stage_id", "attempt_id", "outcome",
                "observed", "held_at")
CUSTODY_MEMBERS = ("decision_id", "job_id", "stage_id", "attempt_id",
                   "frozen", "artifacts", "intake", "adopted", "provenance",
                   "settled_at")
ENDED_MEMBERS = ("decision_id", "job_id", "stage_id", "attempt_id",
                 "outcome", "cause", "ended_at")
UNKNOWN_MEMBERS = ("decision_id", "job_id", "attempt_id", "recorded",
                   "why", "observed_at")
SETTLED_MEMBERS = ("decision_id", "job_id", "stage_id", "attempt_id",
                   "outcome", "runtime", "settlement", "settled_at")
OWNER_ITEM_MEMBERS = ("decision_id", "job_id", "prior_job_id", "outcome",
                      "cause", "destination", "evidence", "remaining",
                      "automatic_retry", "delivered_at")
HANDOFF_MEMBERS = ("decision_id", "job_id", "prior_job_id",
                   "review_stage_id", "publication_stage_id",
                   "publication_attempt_id", "failed_attempt_id",
                   "candidate", "output", "provenance", "custody", "intake",
                   "reviewer", "deadline", "handed_at")


def _operation_id(kind, name):
    boundaries.identity(name, "an operation operand")
    return f"{kind}:{name}"


def staging_operation_id(job_id):
    return _operation_id(STAGING_KIND, job_id)


def launch_operation_id(job_id):
    return _operation_id(LAUNCH_KIND, job_id)


def result_operation_id(job_id):
    return _operation_id(RESULT_KIND, job_id)


def hold_operation_id(job_id):
    return _operation_id(HOLD_KIND, job_id)


def custody_operation_id(job_id):
    return _operation_id(CUSTODY_KIND, job_id)


def ended_operation_id(job_id):
    return _operation_id(ENDED_KIND, job_id)


def unknown_operation_id(job_id, sequence=1):
    return _operation_id(UNKNOWN_KIND, f"{job_id}:{sequence}")


def known_operation_id(job_id, sequence=1):
    return _operation_id(KNOWN_KIND, f"{job_id}:{sequence}")


def settled_operation_id(job_id):
    return _operation_id(SETTLED_KIND, job_id)


def owner_item_operation_id(job_id):
    return _operation_id(OWNER_ITEM_KIND, job_id)


def handoff_operation_id(job_id):
    return _operation_id(HANDOFF_KIND, job_id)


def _committed(store, kind, operation_id, members, *, named=None, value=None):
    """One committed record of this store's journal, PROVED to be the one
    asked for. `publication_recovery._committed`'s rule: a signature is not
    ownership, so a well-made record of another recovery copied to this
    identity does not read as this one's."""
    row = store._connection.execute(
        "SELECT state, result FROM operations WHERE operation_id = ? AND "
        "kind = ?", (operation_id, kind)).fetchone()
    if row is None or row["state"] != "committed" or row["result"] is None:
        return None
    record = json.loads(row["result"])
    if type(record) is not dict or any(one not in record for one in members):
        _refuse(f"the committed {kind} record at {name_value(operation_id)} "
                f"is not one this build can read",
                category="integrity", code="schema")
    if named is not None and record[named] != value:
        _refuse(f"the committed {kind} record at {name_value(operation_id)} "
                f"names {named} {name_value(record[named])} and it was "
                f"selected as {name_value(value)}; a record is proved to be "
                f"the one asked for rather than merely well made",
                category="integrity", code="schema")
    return record


def staging_of(store, job_id):
    return _committed(store, STAGING_KIND, staging_operation_id(job_id),
                      STAGING_MEMBERS, named="job_id", value=job_id)


def launch_of(store, job_id):
    return _committed(store, LAUNCH_KIND, launch_operation_id(job_id),
                      LAUNCH_MEMBERS, named="job_id", value=job_id)


def result_of(store, job_id):
    return _committed(store, RESULT_KIND, result_operation_id(job_id),
                      RESULT_MEMBERS, named="job_id", value=job_id)


def hold_of(store, job_id):
    return _committed(store, HOLD_KIND, hold_operation_id(job_id),
                      HOLD_MEMBERS, named="job_id", value=job_id)


def custody_of(store, job_id):
    return _committed(store, CUSTODY_KIND, custody_operation_id(job_id),
                      CUSTODY_MEMBERS, named="job_id", value=job_id)


def ending_of(store, job_id):
    return _committed(store, ENDED_KIND, ended_operation_id(job_id),
                      ENDED_MEMBERS, named="job_id", value=job_id)


def _knowledge(store, job_id):
    """`(unknown records, known records)` of one recovery, oldest first."""
    def held(kind):
        return [one for one in publication_recovery._records_of(
            store, kind, UNKNOWN_MEMBERS) if one["job_id"] == job_id]
    return (sorted(held(UNKNOWN_KIND), key=lambda one: one["observed_at"]),
            sorted(held(KNOWN_KIND), key=lambda one: one["observed_at"]))


def unknown_of(store, job_id):
    """The STANDING failed observation of this recovery's runtime, or `None`.

    Standing means not yet superseded by a later successful read: the two
    kinds alternate, so it stands exactly while there are more failures on
    record than recoveries.
    """
    unknown, known = _knowledge(store, job_id)
    return unknown[-1] if len(unknown) > len(known) else None


def settlement_of(store, job_id):
    return _committed(store, SETTLED_KIND, settled_operation_id(job_id),
                      SETTLED_MEMBERS, named="job_id", value=job_id)


def owner_item_of(store, job_id):
    return _committed(store, OWNER_ITEM_KIND, owner_item_operation_id(job_id),
                      OWNER_ITEM_MEMBERS, named="job_id", value=job_id)


def owner_items_of(store):
    """Every publication owner item this store delivered, oldest first.

    THE LIST A STATUS SURFACE READS. Each is one recovery that did not
    publish, addressed to the owner who decided it, and none of them is a
    retry, an analysis or a verdict.
    """
    return publication_recovery._records_of(store, OWNER_ITEM_KIND,
                                            OWNER_ITEM_MEMBERS)


def handoff_of(store, job_id):
    return _committed(store, HANDOFF_KIND, handoff_operation_id(job_id),
                      HANDOFF_MEMBERS, named="job_id", value=job_id)


# -- 3. the admitted recovery this act is about ------------------------------

def _admitted(store, decision_id):
    """The committed admission, or a refusal naming what is owed instead.

    EVERY ACT BELOW IS ABOUT AN ADMITTED RECOVERY JOB and about nothing else.
    A held admission performed no effect at all, so an execution act against
    one would be an execution for a Job that does not exist.
    """
    boundaries.identity(decision_id, "an owner decision id")
    held = publication_recovery.admission_of(store, decision_id)
    if held is None:
        if publication_recovery.held_admission_of(store, decision_id) \
                is not None:
            _refuse(f"owner decision {name_value(decision_id)} reached a HELD "
                    f"admission: this instance could not serve a publication "
                    f"stage, so no Job was submitted and there is nothing to "
                    f"publish. The prerequisites it named are what is owed")
        _refuse(f"this store holds no admitted publication recovery for "
                f"decision {name_value(decision_id)}; an execution act is "
                f"about a Job this manager admitted and never about a "
                f"caller's claim about one")
    return held


def _unfenced(store, held, what):
    """Cancellation, expiry and uncertain timing stop NEW effects.

    BOTH JOBS ARE ASKED AND THEY ARE ASKED DIFFERENT QUESTIONS, which is
    `publication_recovery._refuse_cancelled`'s distinction and its reason.

    OF THE ORIGINAL, ONLY ITS EXPLICIT CANCELLATION. A retained output is
    ordinarily published well after the Job that produced it reached its own
    wall -- that is the commonest case of the ending this capability exists
    for -- so refusing on the original's EXPIRY would make the capability
    unreachable. Refusing on its CANCELLATION is the ruling: a cancelled
    execution is never revived and its retained output is not published under
    a new identity.

    OF THE RECOVERY, EVERYTHING. Its own cancellation, its own reached
    deadline (Job, stage or the publication sub-bound) and uncertain timing
    all stop new effects, because those are this execution's own finite
    control and it is running inside them right now.

    NOTHING ALREADY RECORDED IS DELETED OR REWRITTEN by any of these. The
    staged input, the adoption, the custody and the evidence stay exactly as
    they are, and the refusal names which fence it met.
    """
    fence = cancellation.fenced(store._connection, held["prior_job_id"])
    if fence is not None and fence.get("trigger", "operator") == "operator":
        _refuse(f"the original Job {name_value(held['prior_job_id'])} was "
                f"cancelled at {fence['requested_at']} ({fence['reason']}); "
                f"{what} performs no new effect after an explicit "
                f"cancellation, a cancelled execution is never revived, and "
                f"every record already taken is retained")
    closed = job_control.closed_of(store, held["job_id"], any_stage=True)
    if closed is not None:
        _refuse(f"this recovery Job {name_value(held['job_id'])} admits "
                f"nothing more: "
                f"{job_control.closed_message(closed, what)}. Every record "
                f"already taken is retained")
    return None


# -- 4. the absolute publication deadline ------------------------------------

def deadline_of(store, decision_id, *, now=None):
    """THE PUBLICATION STAGE'S ABSOLUTE BOUND, derived from durable rows.

    EVERY MEMBER OF THIS ANSWER COMES OUT OF THE STORE, which is the whole
    property the contract states twice: the origin is the PERSISTED
    publication-stage execution admission -- the Worker Manager's own
    journalled instant of the stage's `admit`, as `job_control.stage_origin_in`
    already reads it -- so this incarnation, the next one and a concurrent
    sweep derive the SAME instant, and a restart re-derives a deadline that
    has already partly elapsed rather than a fresh 900 seconds.

    `origin` IS `None` BEFORE THE STAGE IS ADMITTED, and that is not a
    deadline of `None`: it means the clock has not started, which is why
    queue time is charged to the Job and why no staging or publication work
    may be charged to this stage before it. `reached` is never True on an
    unstarted clock and is never inferred from a clock this store cannot
    order.
    """
    held = _admitted(store, decision_id)
    stage_id = held["publication_stage_id"]
    sub = job_control.stage_sub_bound_in(store._connection, held["job_id"],
                                         stage_id)
    if sub is None:                                       # pragma: no cover
        _refuse(f"this store records no publication sub-bound for stage "
                f"{name_value(stage_id)}; a recovery publication runs under "
                f"the owner-selected absolute bound or it does not run",
                category="integrity", code="schema")
    evaluation = job_control.evaluate(store._connection, held["job_id"],
                                      now if now is not None
                                      else store._now())
    view = None
    for one in (evaluation or {}).get("stages", ()):
        if one["stage_id"] == stage_id:
            view = one
    answer = {
        "stage_id": stage_id, "profile": sub["profile"],
        "seconds": sub["seconds"], "units": sub["units"],
        "origin": sub["origin"], "origin_is": sub["origin_is"],
        "restart_resets": False,
        "deadline_at": sub["deadline_at"],
        # THE STAGE WALL AND THE JOB WALL TRAVEL BESIDE IT, because the
        # publication is bounded by all three and an operator reading only the
        # narrowest would not know which one closed it.
        "stage_deadline_at": (None if view is None
                              else view.get("stage_wall_at")),
        "enforced_deadline_at": None if view is None else view["deadline_at"],
        "job_deadline_at": (None if evaluation is None
                            else evaluation["job"]["deadline_at"]),
        "timing": None if evaluation is None else evaluation["timing"],
        "enforced_by": ("the manager's own control evaluation and fence, "
                        "whose cancellation pass stops the exact runtime "
                        "through the engine owner; and the confined worker's "
                        "own supervisor, which is delivered this same "
                        "absolute instant and ends its copy's process group "
                        "at it"),
        "reached": bool(view is not None and view.get("sub_bound")
                        and view["sub_bound"]["reached"]),
    }
    answer["remaining_seconds"] = _remaining(answer, now if now is not None
                                             else store._now())
    return answer


def _remaining(deadline, now):
    """The seconds a worker has LEFT, or None when the clock has not started.

    NOT A FRESH BUDGET. This is the absolute instant minus the observed one,
    so a worker restarted with 40 seconds left is handed 40 and not 900 --
    which is the sentence "it is not merely a worker-local 900 s timer reset
    by restart", expressed as the only number the worker is ever given.
    """
    if deadline["deadline_at"] is None or deadline["origin"] is None:
        return None
    from datetime import datetime

    def _at(text):
        try:
            return datetime.fromisoformat(str(text).replace("Z", "+00:00"))
        except ValueError:                                # pragma: no cover
            return None

    left, right = _at(deadline["deadline_at"]), _at(now)
    if left is None or right is None:                     # pragma: no cover
        return None
    return int((left - right).total_seconds())


def _within_deadline(store, held, *, now, what):
    """The absolute bound, re-derived and enforced BEFORE the act it bounds.

    A REACHED DEADLINE STOPS NEW EFFECTS AND IS NOT EVIDENCE OF CESSATION,
    which is the contract's own distinction and the reason this refuses rather
    than reporting a stop. The host's fence is what carries the expiry; this
    is the guard that keeps a new effect from being started inside one.
    """
    deadline = deadline_of(store, held["decision_id"], now=now)
    if deadline["timing"] == "uncertain":
        _refuse(f"this recovery Job's timing is uncertain, so the absolute "
                f"publication bound cannot be ordered against the clock; "
                f"{what} is held rather than performed against a deadline "
                f"nobody can place",
                category="runtime-observation", code="quiescence-unknown")
    if deadline["origin"] is None:
        _refuse(f"the publication stage {name_value(deadline['stage_id'])} "
                f"has no persisted execution admission, so its "
                f"{deadline['seconds']}-second bound has no origin yet; "
                f"{what} is work charged to a stage that has not durably "
                f"started, and queue time is charged to the Job")
    if deadline["reached"]:
        _refuse(f"the publication stage reached its "
                f"{deadline['seconds']}-second bound at "
                f"{deadline['deadline_at']} (origin {deadline['origin']}); "
                f"{what} starts no new effect after it, and the deadline "
                f"having passed is not evidence that anything ceased",
                category="policy", code="denied")
    return deadline


# -- 5. the fresh assignment this publication runs under ---------------------

def fresh_assignment_of(store, control, held):
    """THE PUBLICATION STAGE'S OWN ASSIGNMENT, and PROVED to be a fresh one.

    REC-9: the deterministic worker "adopts exact retained bytes under its own
    fresh assignment and declaration". So four things are proved, and each is
    a different way the opposite could be true:

      THE EPISODE EXISTS. The publication stage has a LIVE episode. A
        submission opens the first one, so this is ordinarily true the moment
        the recovery is admitted -- what it rules out is a stage whose episode
        ended and has no replacement.
      THE ASSIGNMENT IS ACTIVATED. The Worker Manager holds an attempt under
        that episode's derived identity AND it has activated an assignment.
        An absent attempt is a stage nobody has claimed, and a claim without
        an activation is not an execution this manager may write for; both
        refuse, in the owner's own words, carried rather than restated.
      IT IS THE PUBLICATION WORKER'S. The participant is the deterministic
        publication worker the admission bound, not whoever happened to claim.
      IT IS NOT THE STOPPED PRODUCER'S. Neither the participant nor the
        generation may be the failed attempt's: "It MUST NOT publish as the
        stopped producer" is REC-9's own sentence, and this is where that
        stops being prose.
    """
    from ..worker_manager import attempts

    stage_id = held["publication_stage_id"]
    live = episodes.live_of(store, stage_id)
    if live is None:
        _refuse(f"the publication stage {name_value(stage_id)} has no live "
                f"episode, so this recovery holds no publication assignment; "
                f"a fresh claim is what an adoption runs under and there is "
                f"none to run under yet")
    attempt_id = live["attempt_id"]
    try:
        assignment = attempts.assignment_of(control, attempt_id)
    except ContractRefusal as refusal:
        _refuse(f"the publication stage {name_value(stage_id)} holds no "
                f"claimed execution: {refusal.message}. A fresh claim is "
                f"what an adoption runs under, and nothing is staged, "
                f"published or collected for an execution nobody claimed",
                category=refusal.category, code=refusal.code)
    if assignment["work_id"] != held["work_id"]:
        _refuse(f"publication attempt {name_value(attempt_id)} runs under "
                f"Work {name_value(assignment['work_id'])} and this recovery "
                f"reuses {name_value(held['work_id'])}; an execution under "
                f"another Work is another execution",
                category="integrity", code="schema")
    if assignment["participant"] != held["worker"]["participant"]:
        _denied(f"publication attempt {name_value(attempt_id)} is claimed by "
                f"{name_value(assignment['participant'])} and this recovery "
                f"was admitted for the deterministic publication worker "
                f"{name_value(held['worker']['participant'])}; a publication "
                f"is performed by the separately selected no-provider worker "
                f"and by nobody else")
    failed = held["candidate"]["attempt_id"]
    if attempt_id == failed:
        _denied(f"this recovery would publish under the FAILED attempt "
                f"{name_value(failed)}'s own identity; a recovery publishes "
                f"under its own fresh assignment and never as the stopped "
                f"producer")
    return {"attempt_id": attempt_id, "episode": live["episode"],
            "offer_id": live["offer_id"],
            **{one: assignment[one] for one in
               ("authority_uuid", "work_id", "participant", "generation",
                "principal", "effective_scope")}}


# -- 6. act one: READ-ONLY STAGING -------------------------------------------

def _staging_root(seam, held):
    """A NEW private staging root, named by the admitted recovery Job.

    DERIVED RATHER THAN ALLOCATED, which is this whole path's replay rule: the
    admission reserved the recovery Job's identity before any execution
    existed, so a re-entry after a crash composes the SAME root instead of
    leaving an orphan beside a second one.
    """
    root = os.path.join(seam["workspaces"], held["job_id"])
    if os.path.islink(root):
        _refuse(f"the private staging root {name_value(root)} is a symbolic "
                f"link; a root this manager did not create is not one it "
                f"stages an approved original into",
                category="integrity", code="path")
    os.makedirs(root, mode=PRIVATE, exist_ok=True)
    os.chmod(root, PRIVATE)
    return root


def _cleared(place):
    """Preserve an interrupted tree before allocating a fresh staging target."""
    import tempfile

    if os.path.lexists(place):
        if os.path.islink(place) or not os.path.isdir(place):
            _refuse(f"{name_value(place)} is not a staging directory",
                    category="integrity", code="path")
        retained = tempfile.mkdtemp(prefix="interrupted-", dir=os.path.dirname(place))
        os.rename(place, os.path.join(retained, os.path.basename(place)))
    os.makedirs(place, mode=PRIVATE)
    return place


def _frozen(place):
    """The staged tree, made READ-ONLY on disk.

    THE MODE SAYS ON DISK WHAT THE CONTRACT SAYS IN PROSE, and both halves are
    needed: 0444 files inside a 0555 directory, because unlink and rename are
    permissions of the DIRECTORY -- a read-only file in a writable directory
    can be removed and replaced under a reader that has already opened the
    root. `workspaces.compose_input_root` records the same correction for the
    same reason.

    THIS IS NOT CUSTODY AND IS NOT CLAIMED TO BE. The contract's sentence is
    "private staging is not custody": these bytes are an input a publication
    consumes, and the only custody in this capability is the one the frozen
    result enters.
    """
    for base, directories, files in os.walk(place, topdown=False):
        for one in files:
            full = os.path.join(base, one)
            if not os.path.islink(full):
                os.chmod(full, READ_ONLY_FILE)
        for one in directories:
            full = os.path.join(base, one)
            if not os.path.islink(full):
                os.chmod(full, READ_ONLY_DIR)
    os.chmod(place, READ_ONLY_DIR)
    return place


def _staging_lock(root, *, name=STAGING_LOCK):
    """ONE STAGER OF ONE RECOVERY'S ORIGINAL, in this host.

    `retained_verification._exclusive`'s rule and its reason: a journal
    identity alone cannot close this window, because two callers that both
    read "nothing staged yet" would both start copying before either
    committed. The lock is `flock` in this manager's own private root -- the
    one place this operation owns exclusively -- so two opens in one process
    contend exactly as two processes do and the kernel releases it if the
    holder dies.
    """
    import contextlib
    import fcntl

    place = os.path.join(root, name)

    @contextlib.contextmanager
    def holding():
        descriptor = os.open(place, os.O_RDWR | os.O_CREAT | os.O_CLOEXEC | os.O_NOFOLLOW,
                             0o600)
        try:
            if not stat.S_ISREG(os.fstat(descriptor).st_mode):
                _refuse("publication lock must be a regular file",
                        category="integrity", code="path")
            try:
                fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                _refuse("publication execution is already active; no second effect starts",
                        category="runtime-observation", code="quiescence-unknown")
            yield
        finally:
            os.close(descriptor)

    return holding()


def _original(seam, held, *, what):
    """THE APPROVED ORIGINAL, RE-READ through the host owner. A read.

    IT DOES NOT TRUST THE ADMISSION'S RECORDED DIGEST, and that is the point
    of asking again: the host owner proves a completed preparation, positive
    writer cessation, no-link entries and the DURABLE OBJECT IDENTITY of the
    root against the one the preparation recorded, and only then measures.
    An original that was replaced, moved aside or re-pointed since the
    decision is a SUBSTITUTED original and the owner says so.
    """
    attempt_id = held["candidate"]["attempt_id"]
    output = seam["host"].output_of(
        attempt_id,
        output=publication_recovery.corrective_declaration()["output"]["path"])
    taken = boundaries.document(output, "the host's retained output read",
                                required=("attempt_id", "root", "identity",
                                          "manifest"),
                                optional=("storage", "published", "entries",
                                          "layout", "output",
                                          "output_identity",
                                          "completion_envelope", "source"))
    if taken["attempt_id"] != attempt_id:                 # pragma: no cover
        _refuse(f"the host answered about attempt "
                f"{name_value(taken['attempt_id'])} and {what} is about "
                f"{name_value(attempt_id)}",
                category="integrity", code="schema")
    recorded = held["output"]
    if taken["identity"] != recorded["root_identity"]:
        _refuse(f"the original output root is object "
                f"{name_value(taken['identity'])} and the owner decided "
                f"about {name_value(recorded['root_identity'])}; a replaced "
                f"object is not the original this recovery was approved for",
                category="runtime-observation", code="identity-mismatch")
    if taken["manifest"]["tree_digest"] != recorded["tree_digest"]:
        _refuse(f"the original output now measures "
                f"{name_value(taken['manifest']['tree_digest'])} and this "
                f"recovery is bound to {name_value(recorded['tree_digest'])}; "
                f"bytes that moved under an owner decision are not the bytes "
                f"it was taken about", category="integrity", code="digest")
    return taken


def _ceased(seam, held, *, what):
    """POSITIVE CESSATION OF THE ORIGINAL WRITER, and `unknown` REFUSES.

    The host owner's own read already refuses while any governed writer of
    that attempt is unsettled; this is the second half -- the runtime, the
    cleanup and the workspace token -- asked of the host that holds them.
    Both are needed and neither implies the other: a settled preparation says
    this manager owes nothing, and the token says the resource is free.
    """
    from . import fresh_attempt

    attempt_id = held["candidate"]["attempt_id"]
    found = seam["exclusion"].evidence_of((attempt_id,))
    taken = boundaries.document(found if isinstance(found, dict) else {},
                                "the host's attempt evidence",
                                required=("host",), optional=(attempt_id,))
    if attempt_id not in taken or taken[attempt_id] is None:
        _refuse(f"the host returned no evidence about attempt "
                f"{name_value(attempt_id)}; an execution nobody can account "
                f"for is unknown, and unknown is not permission to copy the "
                f"bytes it may still be writing",
                category="runtime-observation", code="quiescence-unknown")
    one = taken[attempt_id]
    runtime = (one.get("runtime") or {}).get("execution_runtime")
    cleanup = (one.get("runtime") or {}).get("cleanup")
    token = one.get("token")
    if runtime not in fresh_attempt.CEASED_RUNTIME \
            or cleanup not in fresh_attempt.SETTLED_CLEANUP \
            or not (token and token.get("returned")):
        _refuse(f"attempt {name_value(attempt_id)} is runtime "
                f"{name_value(runtime)}, cleanup {name_value(cleanup)} and "
                f"resource {'returned' if token and token.get('returned') else 'outstanding'}; "
                f"{what} reads the original under POSITIVE cessation and an "
                f"uncertain writer is a writer",
                category="runtime-observation", code="quiescence-unknown")
    return {"runtime": runtime, "cleanup": cleanup, "resource": "returned",
            "ceased": True, "basis": "the host's own record"}


def provenance_document(held, assignment, *, staged, staged_at):
    """THE RECOVERY'S OWN ACCOUNT, as its own bounded document.

    IT IS SEPARATE FROM THE PROPOSAL AND THAT IS THE WHOLE DESIGN. The
    contract: "it never alters the original proposal tree digest". So the
    original producer's attribution and this publisher's identity live in a
    SEPARATELY DECLARED output with its own 16384-byte, one-regular-file,
    no-links descriptor -- and the adopted proposal tree is byte-for-byte what
    the producer wrote.

    BOTH ATTRIBUTIONS TRAVEL AND NEITHER IS PROMOTED. The original producer is
    named as the producer; the publication worker is named as the publisher;
    the producer's own verification is carried with the words
    `producer-evidence` and `independent_acceptance: false` beside it, and the
    reviewer's own required verification is recorded as still owed.
    """
    declaration = held["input_declaration"]
    document = {
        "schema": PROVENANCE_SCHEMA,
        "decision_id": held["decision_id"],
        "recovery_job_id": held["job_id"],
        "original_job_id": held["prior_job_id"],
        "original_stage_id": declaration["stage_id"],
        "original_episode": declaration["episode"],
        "producer": {
            "attempt_id": held["candidate"]["attempt_id"],
            "participant": held["candidate"].get("participant"),
            "principal": held["candidate"].get("principal"),
            "candidate": dict(declaration["candidate"]),
            "verification": dict(declaration["producer"]),
            "disposition": "completed implementation whose output publication "
                           "failed; this recovery publishes its exact bytes "
                           "and claims nothing about its acceptance"},
        "publisher": {
            "attempt_id": assignment["attempt_id"],
            "participant": assignment["participant"],
            "generation": assignment["generation"],
            "kind": "deterministic publication worker",
            "provider_invocations": 0,
            "verifier_invocations": 0},
        "adopted": {"tree_digest": staged["tree_digest"],
                    "entry_count": staged["entry_count"],
                    "total_bytes": staged["total_bytes"],
                    "delivery": "read-only"},
        "reviewer": {
            "independent_verification": "required and owed",
            "producer_evidence": "qualified and reused, never acceptance"},
        "staged_at": staged_at,
    }
    document["provenance_digest"] = digest(
        {one: document[one] for one in sorted(document)})
    return document


def stage_input(store, seam, *, decision_id, now=None):
    """Serialize the effect and its durable result for this recovery."""
    taken = check_publication_seam(seam)
    held = _admitted(store, decision_id)
    # Lock outside the frozen input tree, before changing its permissions.
    lock_root = os.path.join(taken["workspaces"], ".execution-locks")
    if os.path.islink(lock_root):
        _refuse("publication lock root must not be a symlink",
                category="integrity", code="path")
    os.makedirs(lock_root, mode=PRIVATE, exist_ok=True)
    with _staging_lock(lock_root, name=held["job_id"]):
        return _stage_input(store, seam, decision_id=decision_id, now=now)


def _stage_input(store, seam, *, decision_id, now=None):
    """ACT ONE: the approved original, staged READ-ONLY into a recovery-owned
    input root.

    THE ORDER THE CONTRACT FIXES, and each step is somebody else's fact:

      the admitted recovery, the fences and the Work;
      the FRESH ASSIGNMENT, because staging happens "after fresh recovery
        claim and host exclusion" -- a copy made for an execution nobody
        claimed is a copy made for nothing;
      the absolute publication bound, because staging IS work charged to this
        stage and may not happen before its durable start;
      POSITIVE CESSATION of the original writer;
      the ORIGINAL ITSELF, re-read through the host owner and held to the
        object identity and tree digest the decision bound;
      ONE no-follow copy-and-measure pass into the private root, bounded by
        the selected declaration's own ceilings;
      the measured copy held against the approved digest -- a mismatch
        refuses, and nothing launches;
      the recovery's own provenance document, written BESIDE the staged tree
        and never inside it;
      and then the root is FROZEN read-only and the staged manifest is
        committed.

    THE ORIGINAL IS NEVER WRITTEN. This reads it and copies out of it. Its
    `output.json` is not authored, its tree is not touched, and the staged
    copy is the only thing this act creates.
    """
    taken = check_publication_seam(seam)
    _agreeing_instance(taken, what="this publication staging")
    held = _admitted(store, decision_id)
    job_id = held["job_id"]
    recorded = staging_of(store, job_id)
    if recorded is not None:
        return recorded
    _unfenced(store, held, "staging the approved original")
    assignment = fresh_assignment_of(store, taken["control"], held)
    staged_at = boundaries.instant(now if now is not None else store._now(),
                                   "a staging instant")
    _within_deadline(store, held, now=staged_at,
                     what="staging the approved original")
    cessation = _ceased(taken, held, what="staging the approved original")
    output = _original(taken, held, what="this publication staging")
    root = _staging_root(taken, held)
    with _staging_lock(root):
        into = _cleared(os.path.join(root, STAGED_ROOT))
        measured = copied_manifest(output["root"], into,
                                   max_entries=MAX_STAGED_ENTRIES,
                                   max_bytes=MAX_STAGED_BYTES)
        if measured["tree_digest"] != held["output"]["tree_digest"]:
            _refuse(f"the staged original measures "
                    f"{name_value(measured['tree_digest'])} in this "
                    f"recovery's own input root and the owner decision is "
                    f"bound to {name_value(held['output']['tree_digest'])}; "
                    f"an original that does not stage to the bytes it was "
                    f"approved as is reported and is not recovery input",
                    category="integrity", code="digest")
        if measured["total_bytes"] != held["output"]["total_bytes"] \
                or measured["entry_count"] != held["output"]["entry_count"]:
            _refuse(f"the staged original carries "
                    f"{measured['entry_count']} entries and "
                    f"{measured['total_bytes']} bytes and the decision bound "
                    f"{held['output']['entry_count']} and "
                    f"{held['output']['total_bytes']}",
                    category="integrity", code="digest")
        provenance = provenance_document(held, assignment, staged=measured,
                                         staged_at=staged_at)
        place = _cleared(os.path.join(root, PROVENANCE_ROOT))
        payload = (json.dumps(provenance, indent=2, sort_keys=True,
                              ensure_ascii=False) + "\n").encode("utf-8")
        bounded = dict(held["input_declaration"]["provenance"])
        if len(payload) > bounded["max_bytes"]:           # pragma: no cover
            _refuse(f"this recovery's provenance account is {len(payload)} "
                    f"bytes and its approved descriptor allows "
                    f"{bounded['max_bytes']}; a bounded output is bounded",
                    category="integrity", code="limit")
        handle = os.open(os.path.join(place, PROVENANCE_FILE),
                         os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                         0o600)
        try:
            os.write(handle, payload)
        finally:
            os.close(handle)
        provenance_measured = directory_manifest(place)
        _frozen(os.path.join(root, STAGED_ROOT))
        _frozen(place)
        # AND THE PARENT, which is the only thing that governs those two roots'
        # OWN ENTRIES. `workspaces.compose_input_root` records the correction
        # this repeats: 0555 inside a root denies create, unlink and rename
        # THERE, while renaming or replacing the root itself is a write to its
        # parent -- so a frozen staged tree under a writable parent could be
        # moved aside and a writable one put at the same canonical path.
        # `_staging_root` makes the parent writable again at the top of every
        # pass, which is what lets an INTERRUPTED staging be cleared; after a
        # committed one there is no further pass, because the record answers.
        os.chmod(root, READ_ONLY_DIR)
    record = {
        "decision_id": decision_id, "job_id": job_id,
        "prior_job_id": held["prior_job_id"],
        "attempt_id": assignment["attempt_id"],
        "original": {"attempt_id": held["candidate"]["attempt_id"],
                     "root_identity": output["identity"],
                     "tree_digest": output["manifest"]["tree_digest"],
                     "entry_count": output["manifest"]["entry_count"],
                     "total_bytes": output["manifest"]["total_bytes"],
                     "mutated": False},
        "staged": {"locator": "file://" + os.path.join(root, STAGED_ROOT),
                   "tree_digest": measured["tree_digest"],
                   "entry_count": measured["entry_count"],
                   "total_bytes": measured["total_bytes"],
                   "paths": [one["path"] for one in measured["entries"]]},
        "provenance": {
            "locator": "file://" + os.path.join(root, PROVENANCE_ROOT),
            "name": bounded["name"], "file": PROVENANCE_FILE,
            "document": provenance,
            "tree_digest": provenance_measured["tree_digest"],
            "entry_count": provenance_measured["entry_count"],
            "total_bytes": provenance_measured["total_bytes"],
            "max_bytes": bounded["max_bytes"],
            "max_entries": bounded["max_entries"]},
        "input_digest": held["input_digest"],
        "delivery": "read-only",
        "cessation": cessation, "staged_at": staged_at}
    operands = {name: record[name] for name in STAGING_MEMBERS
                if name != "staged_at"}
    return store.transact(staging_operation_id(job_id), STAGING_KIND,
                          job_signature(STAGING_KIND, operands),
                          lambda connection: record)


# -- 7. act two: THE DETERMINISTIC ADOPTION ----------------------------------

def _declared_outputs(held):
    """The TWO outputs a recovery publication declares, and they are two.

    The candidate output is W385694's exact selected revision -- read from the
    descriptor owner, so its ceiling, its media types and its link policy are
    the owner's and not a copy -- and the provenance is the recovery's own
    bounded descriptor BESIDE it. A single widened output would have put this
    manager's account inside the tree whose digest the whole capability exists
    to preserve.
    """
    declaration = publication_recovery.corrective_declaration()
    if declaration["digest"] != held["input_declaration"]["declaration"]:
        _refuse(f"this build's selected output declaration digests to "
                f"{name_value(declaration['digest'])} and this recovery was "
                f"admitted under {name_value(held['input_declaration']['declaration'])}; "
                f"a publication writes under the exact revision its decision "
                f"bound", category="integrity", code="digest")
    bound = held["input_declaration"]["provenance"]
    for member in ("name", "max_bytes", "max_entries", "link_policy"):
        if bound.get(member) != publication_recovery.PROVENANCE[member]:
            _refuse(f"this recovery was admitted with a provenance "
                    f"descriptor whose {member} is "
                    f"{name_value(bound.get(member))} and this build's "
                    f"approved descriptor states "
                    f"{name_value(publication_recovery.PROVENANCE[member])}; "
                    f"a separately bounded output is published under the "
                    f"exact descriptor its decision bound",
                    category="integrity", code="schema")
    return {"candidate": dict(declaration["output"]),
            "provenance": dict(publication_recovery.PROVENANCE_OUTPUT)}


def _locked(seam, held):
    """The per-recovery host lock every effect of this module is taken under."""
    lock_root = os.path.join(seam["workspaces"], ".execution-locks")
    if os.path.islink(lock_root):
        _refuse("publication lock root must not be a symlink",
                category="integrity", code="path")
    os.makedirs(lock_root, mode=PRIVATE, exist_ok=True)
    return _staging_lock(lock_root, name=held["job_id"])


def _placed(text):
    """An absolute instant as a comparable value, or `None`."""
    from datetime import datetime

    try:
        held = datetime.fromisoformat(str(text).replace("Z", "+00:00"))
    except ValueError:
        return None
    return held if held.tzinfo is not None else None


def prepare_launch(store, seam, *, decision_id, now=None):
    """EVERYTHING THIS MODULE DECIDES BEFORE THE CONFINED WORKER STARTS.

    Called by the publication worker's own composition from its mount, which
    is the last host act before the ordinary runtime start. In order: the
    approved original is staged read-only (act one, replayed if it already
    happened), and then ONE durable launch intent is committed.

    THE INTENT IS COMMITTED BEFORE THE RUNTIME START IS REQUESTED, and it
    names the attempt, the fresh assignment, the staged digest and the
    absolute deadline. After it commits, the start itself is the Worker
    Manager's journalled `runtime.start`, so a lost start reply is reconciled
    by that owner against the engine's own listing of the exact runtime
    labels -- one launch, observed, never a second one. This module holds no
    retry and starts nothing.

    THE DEADLINE MUST BE AN INSTANT THIS MANAGER CAN PLACE, STILL AHEAD. A
    missing origin, an unparseable instant, an uncertain clock or a reached
    bound each refuse here, before a container exists; there is no default
    bound to fall back to.
    """
    taken = check_publication_seam(seam)
    _agreeing_instance(taken, what="this publication launch")
    held = _admitted(store, decision_id)
    job_id = held["job_id"]
    staging = stage_input(store, taken, decision_id=decision_id, now=now)
    with _locked(taken, held):
        if result_of(store, job_id) is not None:
            _refuse(f"recovery {name_value(job_id)} already recorded its "
                    f"adoption; a publication is launched once and a "
                    f"finished one is not launched again")
        if hold_of(store, job_id) is not None:
            _refuse(f"recovery {name_value(job_id)}'s adoption is UNCERTAIN "
                    f"and recorded so; no second launch is started while the "
                    f"first is unaccounted for",
                    category="runtime-observation", code="quiescence-unknown")
        _unfenced(store, held, "launching the confined adoption")
        assignment = fresh_assignment_of(store, taken["control"], held)
        if staging["attempt_id"] != assignment["attempt_id"]:
            _refuse(f"the approved original was staged for publication "
                    f"attempt {name_value(staging['attempt_id'])} and the "
                    f"live assignment is "
                    f"{name_value(assignment['attempt_id'])}; a staged input "
                    f"belongs to the execution it was staged for",
                    category="integrity", code="schema")
        at = boundaries.instant(now if now is not None else store._now(),
                                "a launch instant")
        standing = launch_of(store, job_id)
        if standing is not None:
            # THE SAME INTENT, REPLAYED. A restart between the intent and the
            # runtime start re-enters here; whether a runtime already exists
            # is the runtime owner's question and is answered there. The
            # deadline is the one the FIRST intent bound and is never
            # re-derived into a later one.
            if standing["attempt_id"] != assignment["attempt_id"]:
                _refuse(f"recovery {name_value(job_id)} committed a launch "
                        f"intent for attempt "
                        f"{name_value(standing['attempt_id'])} and the live "
                        f"assignment is "
                        f"{name_value(assignment['attempt_id'])}; an intent "
                        f"belongs to the execution it was committed for",
                        category="integrity", code="schema")
            return {"staging": staging, "intent": standing,
                    "assignment": assignment}
        deadline = _within_deadline(store, held, now=at,
                                    what="launching the confined adoption")
        bound = _placed(deadline["deadline_at"])
        if bound is None or _placed(at) is None or bound <= _placed(at):
            _refuse(f"the publication stage's absolute bound is "
                    f"{name_value(deadline['deadline_at'])} at {at}; a "
                    f"confined adoption is launched only under an instant "
                    f"this manager can place and that is still ahead, and "
                    f"there is no default bound",
                    category="policy", code="denied")
        _declared_outputs(held)
        intent = {"decision_id": decision_id, "job_id": job_id,
                  "stage_id": held["publication_stage_id"],
                  "attempt_id": assignment["attempt_id"],
                  "assignment": {one: assignment[one] for one in
                                 ("authority_uuid", "work_id", "participant",
                                  "generation")},
                  "staged_digest": staging["staged"]["tree_digest"],
                  "deadline": {one: deadline[one] for one in
                               ("deadline_at", "origin", "seconds",
                                "restart_resets")},
                  "intended_at": at}
        operands = {name: intent[name] for name in LAUNCH_MEMBERS
                    if name != "intended_at"}
        intent = store.transact(launch_operation_id(job_id), LAUNCH_KIND,
                                job_signature(LAUNCH_KIND, operands),
                                lambda connection: intent)
        return {"staging": staging, "intent": intent,
                "assignment": assignment}


def publication_request(store, decision_id):
    """THE PINNED REQUEST the confined worker reads, composed from RECORDS.

    EVERY MEMBER COMES FROM THE COMMITTED STAGING AND THE COMMITTED INTENT, so
    it is byte-for-byte the same on every restart -- which it has to be,
    because the worker lifecycle re-proves a delivered document against its
    own copy. In particular it carries the ABSOLUTE deadline and never a
    remaining number: a remainder is true only at the instant it was computed,
    and the worker recomputes its own against the clock.

    THERE IS NO COMMAND, NO ARGV, NO ENVIRONMENT, NO CREDENTIAL SLOT, NO
    PROVIDER CONFIGURATION AND NO TASK in it. Returns `None` before a launch
    intent exists.
    """
    held = _admitted(store, decision_id)
    job_id = held["job_id"]
    staging, intent = staging_of(store, job_id), launch_of(store, job_id)
    if staging is None or intent is None:
        return None
    outputs = _declared_outputs(held)
    return {"schema": REQUEST_SCHEMA, "decision_id": decision_id,
            "job_id": job_id, "attempt_id": intent["attempt_id"],
            "deadline": {one: intent["deadline"][one] for one in
                         ("deadline_at", "origin", "seconds",
                          "restart_resets")},
            "staged": {"root": STAGED_ROOT,
                       "tree_digest": staging["staged"]["tree_digest"],
                       "entry_count": staging["staged"]["entry_count"],
                       "total_bytes": staging["staged"]["total_bytes"]},
            "provenance": {"root": PROVENANCE_ROOT,
                           "file": staging["provenance"]["file"],
                           "tree_digest":
                               staging["provenance"]["tree_digest"]},
            "outputs": {"candidate": outputs["candidate"]["name"],
                        "provenance": outputs["provenance"]["name"]}}


def _runtime_of(seam, attempt_id):
    """The Worker Manager's own runtime axes for the publication attempt."""
    from ..worker_manager import attempt_runtime_of

    return attempt_runtime_of(seam["control"], attempt_id)


def _terminal_of(seam, attempt_id):
    """The confined worker's exchange terminal, through the serving reader."""
    answer = seam["runtime"].terminal_of(attempt_id)
    if answer is None:
        return None
    return boundaries.document(
        answer, "a publication exchange terminal",
        required=("ending",),
        optional=("disposition", "manifest_digest", "answered", "detail"))


def _envelope(seam, attempt_id, intent, outputs):
    """THE WORKER'S OWN COMPLETION ENVELOPE, read once and held to its claims.

    IT IS THE WORKER'S ACCOUNT AND IS NOT BELIEVED ABOUT BYTES -- the
    measurement below is this manager's own. What is taken from it is what
    only the worker can say: which assignment it published under, that it
    produced both declared outputs, and its own count of provider and
    producer-verifier invocations, which must both be ZERO.
    """
    from ..contracts import check_manifest_structure

    place = os.path.join(_workspace_of(seam, attempt_id), COMPLETION_MANIFEST)
    try:
        handle = os.open(place, os.O_RDONLY | os.O_NOFOLLOW)
    except OSError:
        _refuse(f"publication attempt {name_value(attempt_id)} answered its "
                f"command and its output root carries no completion "
                f"envelope; an adoption nobody published is not recorded",
                category="integrity", code="path")
    try:
        found = os.fstat(handle)
        if not stat.S_ISREG(found.st_mode) \
                or found.st_size > MAX_ENVELOPE_BYTES:
            _refuse("the publication completion envelope is one bounded "
                    "regular file", category="integrity", code="limit")
        payload = os.read(handle, MAX_ENVELOPE_BYTES + 1)
    finally:
        os.close(handle)
    try:
        body = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        _refuse("the publication completion envelope is not one JSON "
                "document", category="integrity", code="schema")
    check_manifest_structure(body, "completionManifest",
                             what="this publication's completion envelope")
    said = body["assignment_ref"]
    expected = {"work_ref": {
        "authority_uuid": intent["assignment"]["authority_uuid"],
        "work_id": intent["assignment"]["work_id"]},
        "participant": intent["assignment"]["participant"],
        "generation": intent["assignment"]["generation"]}
    if said != expected:
        _denied(f"publication attempt {name_value(attempt_id)}'s completion "
                f"envelope names another assignment than the fresh one this "
                f"launch was committed under; a publication is published by "
                f"its own execution and by nobody else")
    if body.get("disposition") != "completed":
        _refuse(f"the publication worker's envelope states disposition "
                f"{name_value(body.get('disposition'))}; only a completed "
                f"adoption is recorded as one",
                category="runtime-observation", code="quiescence-unknown")
    by_name = {one["name"]: one for one in body["outputs"]}
    counts = {"provider": 0, "verifier": 0}
    for name in ("candidate", "provenance"):
        declared = outputs[name]["name"]
        one = by_name.get(declared)
        if one is None or one.get("status") != "present":
            _refuse(f"the publication worker's envelope does not answer "
                    f"declared output {name_value(declared)} present",
                    category="integrity", code="schema")
        account = (one.get("result_metadata") or {}).get(METADATA_KEY)
        if type(account) is not dict:
            _refuse(f"the publication worker's envelope carries no "
                    f"{METADATA_KEY} account for {name_value(declared)}; the "
                    f"zero-provider and zero-verifier counts are the "
                    f"worker's own statement and an envelope without them "
                    f"states nothing", category="integrity", code="schema")
        for member, key in (("provider_invocations", "provider"),
                            ("verifier_invocations", "verifier")):
            value = account.get(member)
            if type(value) is not int or type(value) is bool or value < 0:
                _refuse(f"the publication worker declares {member} "
                        f"{name_value(value)}; a count is a whole number",
                        category="integrity", code="schema")
            if value != 0:
                _denied(f"the publication worker declares {value} "
                        f"{member.replace('_', ' ')}; a deterministic "
                        f"publication invokes ZERO models and ZERO "
                        f"producer-verification commands, and a worker that "
                        f"did either is not the no-provider worker this "
                        f"recovery reserved capacity for")
            counts[key] = max(counts[key], value)
    return {"manifest_digest": body.get("manifest_digest"),
            "outputs": by_name, "counts": counts}


def record_adoption(store, seam, *, decision_id, now=None):
    """ACT TWO'S RESULT: what the confined worker published, MEASURED after
    its runtime positively stopped.

    Called by the publication worker's own ending, after it has ordered the
    runtime to stop and OBSERVED it quiescent, and before the ordinary freeze.
    It may also be re-entered by the pass; it replays its committed record.

    WHAT IS REQUIRED, each from its own owner:

      a committed staging and a committed launch intent for THIS attempt;
      the Worker Manager's own record that the runtime is QUIESCENT or
        already destroyed after a settled cleanup -- a tree whose writer
        nobody saw stop is not measured, and an `uncertain` runtime holds;
      the exchange's own ANSWERED terminal with disposition `completed` --
        a faulted or lost exchange is journalled as UNCERTAIN and nothing is
        recorded as published;
      the worker's completion envelope, published under the fresh assignment,
        declaring zero provider and zero verifier invocations;
      and THIS MANAGER'S OWN MEASUREMENT of both output roots, held to the
        approved original's tree digest and to the provenance descriptor.

    A worker's answer does not make other bytes the approved ones: the digest
    comparison is on the measurement.
    """
    taken = check_publication_seam(seam)
    _agreeing_instance(taken, what="this publication adoption")
    held = _admitted(store, decision_id)
    job_id = held["job_id"]
    recorded = result_of(store, job_id)
    if recorded is not None:
        return recorded
    staging, intent = staging_of(store, job_id), launch_of(store, job_id)
    if staging is None or intent is None:
        _refuse(f"recovery {name_value(job_id)} has "
                + ("staged no approved original" if staging is None
                   else "committed no launch intent")
                + "; an adoption is recorded for bytes this manager staged, "
                  "under a launch it committed, and never for a tree it was "
                  "shown")
    attempt_id = intent["attempt_id"]
    at = boundaries.instant(now if now is not None else store._now(),
                            "an adoption instant")
    state = _runtime_of(taken, attempt_id)
    stopped = state["execution_runtime"] == "quiescent" \
        or (state["execution_runtime"] == "destroyed"
            and state["cleanup"] in ("complete", "retained"))
    if not stopped:
        _refuse(f"publication attempt {name_value(attempt_id)}'s runtime is "
                f"{name_value(state['execution_runtime'])}; an adoption is "
                f"measured only after its writer was positively observed to "
                f"stop, and a deadline or an answer is not that observation",
                category="runtime-observation", code="quiescence-unknown")
    terminal = _terminal_of(taken, attempt_id)
    if terminal is None or terminal["ending"] != "answered" \
            or terminal.get("disposition") != "completed":
        observed = ("the confined worker's exchange reports "
                    + ("no terminal" if terminal is None else
                       f"{terminal['ending']}"
                       + (f"/{terminal.get('disposition')}"
                          if terminal.get("disposition") else ""))
                    + " after its runtime stopped")
        _hold(store, held, {"attempt_id": attempt_id}, observed=observed,
              now=at)
        _refuse(f"{observed} for attempt {name_value(attempt_id)}; the "
                f"adoption is UNCERTAIN, nothing is recorded as published, "
                f"no second launch is started, and the staged input, the "
                f"original and whatever the worker wrote are retained",
                category="runtime-observation", code="quiescence-unknown")
    outputs = _declared_outputs(held)
    envelope = _envelope(taken, attempt_id, intent, outputs)
    if terminal.get("manifest_digest") is not None \
            and terminal["manifest_digest"] != envelope["manifest_digest"]:
        _refuse(f"publication attempt {name_value(attempt_id)}'s terminal "
                f"names completion envelope "
                f"{name_value(terminal['manifest_digest'])} and its output "
                f"root holds {name_value(envelope['manifest_digest'])}; a "
                f"terminal naming another envelope is not evidence about "
                f"this output", category="integrity", code="digest")
    measured = _measured_outputs(taken, held, {"attempt_id": attempt_id},
                                 outputs)
    for name in ("candidate", "provenance"):
        claimed = envelope["outputs"][outputs[name]["name"]].get(
            "content_manifest") or {}
        if claimed.get("tree_digest") != measured[name]["tree_digest"]:
            _refuse(f"the publication worker's envelope describes its "
                    f"{name} output as "
                    f"{name_value(claimed.get('tree_digest'))} and this "
                    f"manager measures "
                    f"{name_value(measured[name]['tree_digest'])}; an "
                    f"envelope that does not describe the bytes on disk is "
                    f"not recorded", category="integrity", code="digest")
    record = {
        "decision_id": decision_id, "job_id": job_id,
        "stage_id": held["publication_stage_id"],
        "attempt_id": attempt_id,
        "assignment": intent["assignment"],
        "outcome": "published",
        "adopted": measured["candidate"],
        "provenance": measured["provenance"],
        "invocations": {"provider": envelope["counts"]["provider"],
                        "verifier": envelope["counts"]["verifier"],
                        "commands": 0},
        "deadline": intent["deadline"],
        "adopted_at": at}
    operands = {name: record[name] for name in RESULT_MEMBERS
                if name != "adopted_at"}

    def act(connection):
        # THE AUTHORITATIVE COMMIT BOUNDARY (review 2026-11-23T20-28-00Z R2;
        # COMPLETION-PLAN-385909 outcome 1). Everything above is evidence that
        # a worker finished; none of it is permission to record a NEW
        # publication. That is decided here, inside the one transaction that
        # would write the result, against this store's own fence and the
        # persisted absolute bound at the manager's own instant -- so a
        # terminal that says `completed`, published in the window after the
        # worker's last gate, cannot carry an adoption past a cancellation or
        # past the instant.
        #
        # A RESULT COMMITTED EARLIER IS NOT RE-JUDGED: the replay above
        # returned it before this function measured anything, and
        # `transact` replays a committed operation without running this.
        del connection
        _open_for_adoption(store, held, at)
        return record

    try:
        return store.transact(result_operation_id(job_id), RESULT_KIND,
                              job_signature(RESULT_KIND, operands), act)
    except ContractRefusal as refusal:
        closed = _closure_of(store, held, at)
        if closed is None:
            raise
        # KNOWN, AND SAID AS WHAT IT IS. Not an uncertainty: the bytes are
        # there, measured, and they are NOT a publication. They stay where
        # they are as evidence for the owner.
        _ended(store, held, attempt_id, outcome=closed["outcome"],
               cause=closed["cause"]
               + "; the confined worker's output is retained as evidence "
                 "and was not recorded as published", now=at)
        raise refusal


def _closure_of(store, held, at):
    """Why this recovery admits no NEW effect at `at`, or `None`.

    ONE CLASSIFICATION, from this store's own rows: the original's explicit
    cancellation, then this recovery's own fence, then its own reached bound.
    `_unfenced` and `_within_deadline` refuse on these; this names which, so
    an ending is recorded as what it was rather than as "refused".
    """
    fence = cancellation.fenced(store._connection, held["prior_job_id"])
    if fence is not None and fence.get("trigger", "operator") == "operator":
        return {"outcome": "cancelled",
                "cause": f"the original Job was cancelled at "
                         f"{fence['requested_at']} ({fence['reason']})"}
    own = cancellation.fenced(store._connection, held["job_id"])
    if own is not None:
        expired = own.get("trigger", "operator") != "operator"
        return {"outcome": "expired" if expired else "cancelled",
                "cause": f"this recovery was "
                         f"{'expired' if expired else 'cancelled'} at "
                         f"{own['requested_at']} ({own['reason']})"}
    closed = job_control.closed_of(store, held["job_id"], at,
                                   any_stage=True)
    if closed is not None and closed["cause"] == "deadline":
        first = closed["first"]
        return {"outcome": "expired",
                "cause": f"this recovery reached its {first['trigger']} at "
                         f"{first['deadline_at']}"}
    deadline = deadline_of(store, held["decision_id"], now=at)
    if deadline["reached"]:
        return {"outcome": "expired",
                "cause": f"the publication stage reached its "
                         f"{deadline['seconds']}-second bound at "
                         f"{deadline['deadline_at']}"}
    return None


def _open_for_adoption(store, held, at):
    """Refuse a NEW adoption this recovery's own control no longer admits."""
    what = "a new publication adoption"
    _unfenced(store, held, what)
    closed = job_control.closed_of(store, held["job_id"], at, any_stage=True)
    if closed is not None:
        _refuse(f"this recovery Job {name_value(held['job_id'])} admits "
                f"nothing more: "
                f"{job_control.closed_message(closed, what)}. A worker that "
                f"answered `completed` does not make a late adoption an "
                f"on-time one; its output is retained as evidence",
                category="policy", code="denied")
    _within_deadline(store, held, now=at, what=what)


def _ended(store, held, attempt_id, *, outcome, cause, now):
    """ONE durable ending per recovery: it did not publish, and why is known.

    FIRST WRITER WINS AND IS NEVER REVISED. A recovery that faulted and then
    also reached its bound ended because it faulted; recording the later fact
    over the earlier one would be rewriting history to match the clock.
    """
    recorded = ending_of(store, held["job_id"])
    if recorded is not None:
        return recorded
    if outcome not in ENDED_OUTCOMES:                     # pragma: no cover
        _refuse(f"a publication ending is one of "
                f"{', '.join(ENDED_OUTCOMES)}", category="integrity",
                code="schema")
    record = {"decision_id": held["decision_id"], "job_id": held["job_id"],
              "stage_id": held["publication_stage_id"],
              "attempt_id": attempt_id, "outcome": outcome,
              "cause": boundaries.text(cause, "a publication ending cause"),
              "ended_at": boundaries.instant(now, "an ending instant")}
    try:
        return store.transact(
            ended_operation_id(held["job_id"]), ENDED_KIND,
            job_signature(ENDED_KIND,
                          {"decision_id": record["decision_id"],
                           "job_id": record["job_id"]}),
            lambda connection: record)
    except ContractRefusal:                               # pragma: no cover
        return ending_of(store, held["job_id"])


def publish(store, seam, *, decision_id, now=None):
    """ACT TWO, AS THE PASS SEES IT: account for the launched adoption.

    THE PASS NEVER LAUNCHES. The confined worker is started by its own
    lifecycle, which calls `prepare_launch` first; what a tick does here is
    read what has happened to that one launch and say so:

      a recorded result replays;
      no intent yet -- the launch has not been committed; held;
      a runtime still starting, running or waiting -- in flight; held;
      a runtime positively stopped with an answered, completed exchange --
        `record_adoption`, exactly as the ending calls it;
      a runtime positively stopped, or destroyed, WITHOUT that answer; or an
        `uncertain` runtime -- journalled as UNCERTAIN and held.

    No branch starts a second adoption, and an uncertainty once journalled is
    never cleared by a later tick.
    """
    taken = check_publication_seam(seam)
    held = _admitted(store, decision_id)
    with _locked(taken, held):
        return _published(store, taken, held, decision_id=decision_id,
                          now=now)


def _published(store, seam, held, *, decision_id, now=None):
    _agreeing_instance(seam, what="this publication adoption")
    job_id = held["job_id"]
    recorded = result_of(store, job_id)
    if recorded is not None:
        return recorded
    if staging_of(store, job_id) is None:
        _refuse(f"recovery {name_value(job_id)} has staged no approved "
                f"original; an adoption publishes bytes this manager staged "
                f"and measured, never a locator it was handed")
    standing = hold_of(store, job_id)
    if standing is not None:
        _refuse(f"recovery {name_value(job_id)}'s adoption of attempt "
                f"{name_value(standing['attempt_id'])} is UNCERTAIN "
                f"({standing['observed']}). No second adoption is started "
                f"while the first is unaccounted for; the staged input, the "
                f"original and every record are retained",
                category="runtime-observation", code="quiescence-unknown")
    intent = launch_of(store, job_id)
    if intent is None:
        _refuse(f"recovery {name_value(job_id)} has committed no launch "
                f"intent; the confined adoption is launched by the "
                f"publication worker's own lifecycle and this pass does not "
                f"launch one")
    attempt_id = intent["attempt_id"]
    at = boundaries.instant(now if now is not None else store._now(),
                            "an adoption instant")
    state = _runtime_of(seam, attempt_id)
    runtime = state["execution_runtime"]
    if runtime == "uncertain":
        _hold(store, held, {"attempt_id": attempt_id},
              observed="the host cannot say whether the launched runtime "
                       "exists", now=at)
        _refuse(f"publication attempt {name_value(attempt_id)}'s runtime is "
                f"UNCERTAIN; nothing is recorded as published and no second "
                f"launch is started",
                category="runtime-observation", code="quiescence-unknown")
    stopped = runtime == "quiescent" or (
        runtime == "destroyed" and state["cleanup"] in ("complete",
                                                         "retained"))
    terminal = _terminal_of(seam, attempt_id)
    if terminal is not None and terminal["ending"] != "answered":
        # THE WORKER ITSELF SAID IT DID NOT PUBLISH -- a faulted exchange is
        # what a supervised adoption ended by its bound, or by a failed copy,
        # produces. No later tick can turn that into a publication, so it is
        # journalled now rather than after the host has also stopped the
        # runtime. Whether that runtime has CEASED is a separate fact and
        # stays the runtime owner's.
        _hold(store, held, {"attempt_id": attempt_id},
              observed=f"the confined worker's exchange ended "
                       f"{terminal['ending']} and published nothing",
              now=at)
        _refuse(f"publication attempt {name_value(attempt_id)}'s confined "
                f"worker ended its command {name_value(terminal['ending'])}; "
                f"the adoption is UNCERTAIN, nothing is recorded as "
                f"published and no second launch is started",
                category="runtime-observation", code="quiescence-unknown")
    if not stopped and runtime != "destroyed":
        # IN FLIGHT ON THE RECORD -- AND THE RECORD IS THE LAST OBSERVATION,
        # NOT NOW (review 2026-11-23T20-28-00Z). So the engine is asked. A
        # read that fails is journalled: the runtime's state is then UNKNOWN
        # and is reported as unknown, where this used to answer "in flight"
        # off an axis nobody had been able to refresh. It is not a hold --
        # nothing is latched, and an engine that answers again lets the same
        # adoption be accounted for.
        if _observed(store, seam, held, attempt_id, at) is None:
            _refuse(f"publication attempt {name_value(attempt_id)}'s runtime "
                    f"could not be observed; it is recorded "
                    f"{name_value(runtime)}, which is the last observation "
                    f"and not current knowledge. Nothing is recorded as "
                    f"published, nothing is released and no second launch "
                    f"is started",
                    category="runtime-observation", code="quiescence-unknown")
        _refuse(f"publication attempt {name_value(attempt_id)}'s runtime is "
                f"{name_value(runtime)}; the confined adoption is in flight "
                f"and is accounted for only once its runtime has positively "
                f"stopped")
    if runtime == "destroyed" and not stopped:
        _hold(store, held, {"attempt_id": attempt_id},
              observed="the launched runtime is gone and its cleanup is not "
                       "settled", now=at)
        _refuse(f"publication attempt {name_value(attempt_id)}'s runtime is "
                f"gone without a settled cleanup; the adoption is UNCERTAIN",
                category="runtime-observation", code="quiescence-unknown")
    return record_adoption(store, seam, decision_id=decision_id, now=at)


def _hold(store, held, assignment, *, observed, now):
    """ONE journalled uncertainty per recovery, and it is not a failure.

    IT RECORDS THAT NOBODY KNOWS, which is a different durable fact from "it
    did not work": a failure would authorize an owner item and a retry
    decision, and this authorizes neither. What it does is make the next
    incarnation refuse to start a second adoption, with the exact cut named.
    """
    record = {"decision_id": held["decision_id"], "job_id": held["job_id"],
              "stage_id": held["publication_stage_id"],
              "attempt_id": assignment["attempt_id"],
              "outcome": "unknown", "observed": observed,
              "held_at": boundaries.instant(now, "an uncertainty instant")}
    operands = {name: record[name] for name in HOLD_MEMBERS
                if name != "held_at"}
    try:
        return store.transact(hold_operation_id(held["job_id"]), HOLD_KIND,
                              job_signature(HOLD_KIND, operands),
                              lambda connection: record)
    except ContractRefusal:                               # pragma: no cover
        # AN UNCERTAINTY ALREADY RECORDED IS STILL AN UNCERTAINTY. A collision
        # here means a previous incarnation journalled a different observation
        # of the same cut, and the refusal below is raised either way.
        return hold_of(store, held["job_id"])


def _measured_outputs(seam, held, assignment, outputs):
    """WHAT IS ACTUALLY ON DISK, measured by this manager, and held to the
    approved bytes.

    THE TWO COMPARISONS THAT MATTER:

      THE ADOPTED PROPOSAL IS THE ORIGINAL, tree digest for tree digest. Not
        "similar", not "measured by the writer": `directory_manifest` opens
        every entry once with `O_NOFOLLOW`, refuses a link or a special file,
        and recomputes the tree digest over the canonical ordered entry
        array. A writer that wrote anything else is refused here with its
        answer already in hand and nothing frozen.
      THE PROVENANCE IS SEPARATE AND BOUNDED. One regular file, inside its
        own approved descriptor's byte ceiling, at its own declared path --
        and the proposal tree digest above is UNCHANGED by it, which is the
        sentence "it never alters the original proposal tree digest" expressed
        as the measurement of two disjoint trees.
    """
    attempt_id = assignment["attempt_id"]
    place = _workspace_of(seam, attempt_id)
    measured = {}
    for name, declaration in (("candidate", outputs["candidate"]),
                              ("provenance", outputs["provenance"])):
        at = os.path.join(place, declaration["path"])
        if not os.path.isdir(at) or os.path.islink(at):
            _refuse(f"the publication attempt declared output "
                    f"{name_value(declaration.get('name', name))} at "
                    f"{name_value(at)} and this manager finds no directory "
                    f"there; an output nobody wrote is not one a freeze may "
                    f"describe", category="integrity", code="path")
        measured[name] = directory_manifest(at)
    if measured["candidate"]["tree_digest"] != held["output"]["tree_digest"]:
        _refuse(f"the adopted proposal measures "
                f"{name_value(measured['candidate']['tree_digest'])} in the "
                f"publication attempt's own output and the approved original "
                f"is {name_value(held['output']['tree_digest'])}; a recovery "
                f"publishes the exact retained bytes and a writer's answer "
                f"does not make other bytes them",
                category="integrity", code="digest")
    bounded = outputs["provenance"]["constraints"]
    if measured["provenance"]["entry_count"] > bounded["max_entries"] \
            or measured["provenance"]["total_bytes"] > bounded["max_bytes"]:
        _refuse(f"the recovery provenance carries "
                f"{measured['provenance']['entry_count']} entries and "
                f"{measured['provenance']['total_bytes']} bytes and its "
                f"approved descriptor allows {bounded['max_entries']} and "
                f"{bounded['max_bytes']}; a separately bounded output is "
                f"bounded", category="integrity", code="limit")
    return {"candidate": {**measured["candidate"],
                          "name": outputs["candidate"]["name"],
                          "path": outputs["candidate"]["path"],
                          "equals_original": True,
                          "root": place},
            "provenance": {**measured["provenance"],
                           "name": outputs["provenance"]["name"],
                           "path": outputs["provenance"]["path"],
                           "max_bytes": bounded["max_bytes"],
                           "max_entries": bounded["max_entries"],
                           "alters_proposal_tree": False}}


def _workspace_of(seam, attempt_id):
    """The publication attempt's own output root, through the owner that
    prepared it.

    NOT COMPOSED FROM A PATH THIS MODULE CHOSE, which is the same rule
    `workspaces.retained_output_of` keeps for the original: a consumer that
    assembled `<storage>/<attempt>/workspace` for itself would be a caller
    choosing a path and then calling it an execution's output.
    """
    from ..worker_manager.workspaces import (configured_workspace_storage,
                                             settlement_preparation)
    from ..worker_manager import custody as custody_owner

    prepared = settlement_preparation(seam["control"], attempt_id)
    if prepared.get("workspace_layout") != "attempt":
        _refuse(f"publication attempt {name_value(attempt_id)}'s completed "
                f"preparation states workspace layout "
                f"{name_value(prepared.get('workspace_layout'))} and this "
                f"read reconstructs the attempt layout only",
                category="integrity", code="path")
    storage = configured_workspace_storage(seam["control"])
    home = os.path.join(os.path.realpath(storage.place), attempt_id)
    custody_owner._no_link(home, what="the publication attempt's home")
    place = os.path.join(home, "workspace")
    custody_owner._no_link(place, what="the publication attempt's workspace")
    found = os.stat(place, follow_symlinks=False)
    identity = f"{found.st_dev}:{found.st_ino}"
    if identity != prepared.get("workspace"):
        _refuse(f"publication attempt {name_value(attempt_id)}'s workspace "
                f"root was {name_value(prepared.get('workspace'))} when its "
                f"preparation completed and the entry there now is "
                f"{name_value(identity)}; a replaced object is not the output "
                f"this attempt wrote",
                category="runtime-observation", code="identity-mismatch")
    if not stat.S_ISDIR(found.st_mode):                   # pragma: no cover
        _refuse(f"{name_value(place)} is not a directory",
                category="integrity", code="path")
    return place


# -- 8. act three: NORMAL COMPLETION, CUSTODY AND INTAKE ---------------------

def take_custody(store, seam, *, decision_id, now=None):
    """ACT THREE: bind the ordinary freeze and intake of this new execution.

    NOTHING HERE IS A SECOND CUSTODY PATH, and after this revision nothing
    here even ASKS for one. `request_freeze` and `request_intake` are the
    Worker Manager's own public operations and they are called by the
    publication worker's ordinary ending -- the same composition that stopped
    the runtime and holds its engine adapter -- exactly as every
    implementation and review stage's are. REC-9's "normal completion, custody
    and collection checks apply to this new execution" is kept by there being
    no publication-specific variant of either, and no second caller.

    SO THIS ACT READS. Until that ending has frozen the result and recorded
    its intake receipt, there is no custody to bind and this is held.

    WHAT THIS ACT ADDS is the comparison nobody else can make: that the frozen
    result's candidate artifact is the approved original byte for byte, that
    the provenance is a SEPARATE artifact inside its own descriptor, and that
    the intake receipt belongs to THIS attempt and to this manager's own
    frozen result.
    """
    from ..worker_manager.intake import intake_receipt_of

    taken = check_publication_seam(seam)
    _agreeing_instance(taken, what="this publication custody")
    held = _admitted(store, decision_id)
    job_id = held["job_id"]
    recorded = custody_of(store, job_id)
    if recorded is not None:
        return recorded
    _unfenced(store, held, "taking custody of the published candidate")
    result = result_of(store, job_id)
    if result is None:
        _refuse(f"recovery {name_value(job_id)} adopted nothing; custody "
                f"describes bytes a publication wrote and this manager "
                f"measured, and there are none recorded")
    attempt_id = result["attempt_id"]
    frozen = frozen_output_of(taken["control"], attempt_id)
    if frozen is None:
        _refuse(f"publication attempt {name_value(attempt_id)}'s ordinary "
                f"ending has frozen no result yet; nothing entered custody "
                f"and no handoff is composed")
    receipt = intake_receipt_of(taken["control"], attempt_id)
    if receipt is None:
        _refuse(f"publication attempt {name_value(attempt_id)}'s ordinary "
                f"ending has recorded no intake receipt yet; a candidate "
                f"nothing took custody of is not handed to review")
    artifacts = _custody_artifacts(frozen, receipt, result, held,
                                   attempt_id=attempt_id)
    record = {
        "decision_id": decision_id, "job_id": job_id,
        "stage_id": held["publication_stage_id"], "attempt_id": attempt_id,
        "frozen": {"result_id": frozen["result_id"],
                   "disposition": frozen["disposition"],
                   "manifest_digest": frozen["manifest_digest"]},
        "artifacts": artifacts["artifacts"],
        "intake": {"receipt_id": receipt.get("receipt_id"),
                   "result_id": receipt.get("result_id"),
                   "artifacts": sorted(one["artifact_id"] for one in
                                       receipt.get("artifacts", ()))},
        "adopted": artifacts["candidate"],
        "provenance": artifacts["provenance"],
        "settled_at": boundaries.instant(
            now if now is not None else store._now(), "a custody instant")}
    operands = {name: record[name] for name in CUSTODY_MEMBERS
                if name != "settled_at"}
    return store.transact(custody_operation_id(job_id), CUSTODY_KIND,
                          job_signature(CUSTODY_KIND, operands),
                          lambda connection: record)


def _custody_artifacts(frozen, receipt, result, held, *, attempt_id):
    """THE FROZEN RESULT'S OWN ARTIFACTS, held to what was adopted.

    THE FROZEN RESULT IS THE MANAGER'S RECORD OF WHAT A WORKER PUBLISHED, so
    its artifacts are where "the candidate is in custody" stops being a claim
    about a directory. Two of them are expected and both are checked: the
    candidate, whose content digest must be the approved original's tree
    digest, and the provenance, which must be present, separate, and inside
    its own descriptor.

    AN INTAKE RECEIPT THAT NAMES ANOTHER RESULT IS NOT THIS ONE'S. The receipt
    and the frozen result are two records of one custody, and a receipt copied
    from another attempt would otherwise read as this attempt's collection.
    """
    if receipt.get("result_id") not in (None, frozen["result_id"]):
        _refuse(f"the intake receipt for attempt {name_value(attempt_id)} "
                f"names result {name_value(receipt.get('result_id'))} and "
                f"this manager froze {name_value(frozen['result_id'])}; two "
                f"records of one custody name one result",
                category="integrity", code="schema")
    # KEYED BY THE DECLARED OUTPUT NAME the frozen result records them under,
    # which is `output_name` -- the artifact's own id is a custody identity and
    # is not the declaration it answers.
    held_artifacts = {}
    for one in frozen.get("artifacts", ()):
        held_artifacts[one.get("output_name")] = one
    for name in (result["adopted"]["name"], result["provenance"]["name"]):
        if name not in held_artifacts:
            _refuse(f"the frozen result of attempt {name_value(attempt_id)} "
                    f"carries no {name_value(name)} artifact; a publication "
                    f"whose declared outputs did not enter custody has not "
                    f"completed, whatever it published",
                    category="integrity", code="schema")
    candidate = held_artifacts[result["adopted"]["name"]]
    provenance = held_artifacts[result["provenance"]["name"]]
    if candidate.get("content_digest") != held["output"]["tree_digest"]:
        _refuse(f"the candidate artifact in custody measures "
                f"{name_value(candidate.get('content_digest'))} and the "
                f"approved original is "
                f"{name_value(held['output']['tree_digest'])}; a candidate "
                f"that is not the retained bytes is not handed to review",
                category="integrity", code="digest")
    if provenance.get("content_digest") == candidate.get("content_digest"):
        _refuse(f"the provenance artifact and the candidate artifact in "
                f"custody carry one digest; the recovery's own account is a "
                f"SEPARATE output and a tree that holds both is a proposal "
                f"this recovery altered", category="integrity", code="digest")
    return {"artifacts": sorted(held_artifacts),
            "candidate": {"name": candidate.get("output_name"),
                          "artifact_id": candidate.get("artifact_id"),
                          "content_digest": candidate.get("content_digest"),
                          "locator": candidate.get("locator"),
                          "equals_original": True},
            "provenance": {"name": provenance.get("output_name"),
                           "artifact_id": provenance.get("artifact_id"),
                           "content_digest": provenance.get("content_digest"),
                           "locator": provenance.get("locator"),
                           "alters_proposal_tree": False}}


# -- 9. act four: THE ONE HANDOFF THAT OPENS REVIEW --------------------------

# EVERY BINDING THE GATE IS DECIDED ON, named so a closed gate can say which
# one is missing rather than only that it is shut.
GATE_BINDINGS = ("decision", "admission", "staged-input", "adoption",
                 "custody", "intake", "reviewer-servability")
GATE_UNAVAILABLE = "publication-custody-handoff-unavailable"
GATE_VALIDATED = "publication-custody-handoff-validated"
GATE_REASONS = (GATE_UNAVAILABLE, GATE_VALIDATED)


def _reviewer(store, held):
    """THE REVIEW STAGE'S OWN SUBMITTED BINDING, and the independence it
    carries.

    THE CANDIDATE IDENTITY MUST EQUAL THE APPROVED ORIGINAL, which is the
    contract's reviewer-binding sentence, and the producer edge the review
    consumes is the PUBLICATION stage -- named by kind in the submitted graph
    rather than looked up as a nonexistent implementation stage.

    THE EXCLUDED PRINCIPALS ARE BOTH OF THEM. The original implementation
    principal and the publication principal, because "a new Job must not
    erase the original producer exclusion". The scheduler enforces it at
    reservation time; this records what the enforcement must cover so a
    reviewer offered despite it is a failing comparison rather than a missing
    one.
    """
    stage_id = held["review_stage_id"]
    rows = {one["stage_id"]: one for one in
            submission.stages_of(store, held["job_id"])}
    stage = rows.get(stage_id)
    if stage is None:                                     # pragma: no cover
        _refuse(f"recovery Job {name_value(held['job_id'])} carries no "
                f"review stage {name_value(stage_id)}",
                category="integrity", code="schema")
    gates = [one for one in json.loads(stage["depends_on"])]
    wanted = {"job_id": held["job_id"],
              "kind": documents.PUBLICATION_STAGE}
    if gates != [wanted]:                                 # pragma: no cover
        _refuse(f"the recovery review stage gates on "
                f"{name_value(json.dumps(gates))} and a publication recovery "
                f"review consumes exactly its own publication stage",
                category="integrity", code="schema")
    return {"stage_id": stage_id,
            "producer_stage_kind": documents.PUBLICATION_STAGE,
            "producer_stage_id": held["publication_stage_id"],
            "profile_name": stage["profile_name"],
            "profile_digest": stage["profile_digest"],
            "work_id": stage["work_id"],
            "input_digest": held["input_digest"],
            "candidate": {"base": held["candidate"]["base"],
                          "head": held["candidate"]["head"]},
            "excluded_principals": sorted({
                one for one in (held["candidate"].get("principal"),
                                held["worker"].get("participant"))
                if one}),
            "excluded_participants": sorted({
                one for one in (held["candidate"].get("participant"),
                                held["worker"].get("participant"))
                if one}),
            "invocation_seconds": held["bounds"][
                "review_provider_invocation_seconds"],
            "each_command_seconds": held["bounds"][
                "verification_command_seconds"],
            "independent_verification": "required and owed",
            "producer_evidence": "qualified and reused, never acceptance"}


def hand_off(store, seam, *, decision_id, now=None):
    """ACT FOUR: bind the published candidate and its custody to the review.

    WHAT THIS RELEASES AND WHAT IT DOES NOT. After this commits,
    `execution_gate` reports the review stage's gate OPEN and the ordinary
    manager tick admits the deployment's configured independent reviewer. What
    it does not do is judge: no verdict is written here, no structural check is
    treated as acceptance, the producer's reused evidence is carried with its
    qualification attached, and the reviewer's own required verification and
    investigation remain the reviewer's.

    EVERY BINDING IS PRESENT AND AGREES, OR THERE IS NO HANDOFF. The owner
    decision, the admission, the staged input, the adoption, the frozen
    result, the custody artifacts, the intake receipt and the review stage's
    own servable binding -- and the candidate identity equal to the approved
    original. A completion without custody, an unattached candidate or a
    receipt belonging to another attempt each leave the gate shut.
    """
    taken = check_publication_seam(seam)
    _agreeing_instance(taken, what="this publication handoff")
    held = _admitted(store, decision_id)
    job_id = held["job_id"]
    recorded = handoff_of(store, job_id)
    if recorded is not None:
        return recorded
    _unfenced(store, held, "handing the published candidate to review")
    custody = custody_of(store, job_id)
    if custody is None:
        _refuse(f"recovery {name_value(job_id)} holds no publication custody; "
                f"a review handoff delivers a candidate this manager took "
                f"custody of and never a name it was given")
    result = result_of(store, job_id)
    staging = staging_of(store, job_id)
    # THE OUTGOING EXECUTION HAS POSITIVELY CEASED, which is the contract's
    # own clause in the gate's condition -- "outgoing execution is ceased" --
    # and is read from the Worker Manager's record of the runtime rather than
    # from the deadline, the answer or the freeze. A frozen result with a
    # runtime nobody saw end is an ending in progress.
    state = _runtime_of(taken, custody["attempt_id"])
    if not (state["execution_runtime"] == "destroyed"
            or state["cleanup"] in ("complete", "retained")):
        _refuse(f"publication attempt {name_value(custody['attempt_id'])}'s "
                f"runtime is {name_value(state['execution_runtime'])} with "
                f"cleanup {name_value(state['cleanup'])}; review is released "
                f"only after the publishing execution has positively ceased",
                category="runtime-observation", code="quiescence-unknown")
    reviewer = _reviewer(store, held)
    record = {
        "decision_id": decision_id, "job_id": job_id,
        "prior_job_id": held["prior_job_id"],
        "review_stage_id": held["review_stage_id"],
        "publication_stage_id": held["publication_stage_id"],
        "publication_attempt_id": custody["attempt_id"],
        "failed_attempt_id": held["candidate"]["attempt_id"],
        "candidate": {**{one: held["candidate"][one] for one in
                         ("base", "head", "changed_paths")},
                      "content_digest": held["output"]["tree_digest"],
                      "equals_approved_original": True},
        "output": {"tree_digest": result["adopted"]["tree_digest"],
                   "entry_count": result["adopted"]["entry_count"],
                   "total_bytes": result["adopted"]["total_bytes"],
                   "declared_name": result["adopted"]["name"],
                   "staged_from": staging["staged"]["locator"],
                   "original_mutated": False},
        "provenance": {"declared_name": result["provenance"]["name"],
                       "tree_digest": result["provenance"]["tree_digest"],
                       "total_bytes": result["provenance"]["total_bytes"],
                       "alters_proposal_tree": False,
                       "document_digest":
                           staging["provenance"]["document"][
                               "provenance_digest"]},
        "custody": {"result_id": custody["frozen"]["result_id"],
                    "manifest_digest": custody["frozen"]["manifest_digest"],
                    "artifact_id": custody["adopted"]["artifact_id"],
                    "locator": custody["adopted"]["locator"],
                    "artifacts": list(custody["artifacts"])},
        "intake": dict(custody["intake"]),
        "reviewer": reviewer,
        "deadline": dict(result["deadline"]),
        "handed_at": boundaries.instant(
            now if now is not None else store._now(), "a handoff instant")}
    document = documents.publication_handoff(
        **{one: record[one] for one in HANDOFF_MEMBERS})
    operands = {name: record[name] for name in HANDOFF_MEMBERS
                if name != "handed_at"}
    return store.transact(handoff_operation_id(job_id), HANDOFF_KIND,
                          job_signature(HANDOFF_KIND, operands),
                          lambda connection: document)


# -- 10. the review gate -----------------------------------------------------

def execution_gate(store, job_id, stage_id=None):
    """KEEP REVIEW NON-RUNNABLE UNTIL A VALIDATED HANDOFF EXISTS.

    IT IS THE REVIEW STAGE'S GATE AND NOBODY ELSE'S. REC-8's recovery Job has
    one stage, so a per-Job gate is also a per-stage one there; a publication
    recovery Job has TWO, and a gate that answered for both would hold the
    PUBLICATION stage shut behind a handoff only the publication can produce.
    That is a deadlock, not a safety property. So `stage_id` scopes it: a
    caller that names a stage gets an answer only for the review stage, and a
    caller that names none gets the Job's own gate for a status read.

    `retained_recovery.execution_gate`'s shape, for REC-9's own sentence:
    "Review MUST remain non-runnable until attributable publication custody
    and the exact candidate handoff are validated". `open` is DERIVED from the
    committed handoff record and from nothing else -- there is no operand, no
    flag and no caller that can set it. An approval, a qualified producer
    result, a candidate digest, a submitted dependency edge and an operator's
    journalled account all leave it shut.

    AND A CLOSED GATE SAYS WHICH BINDING IS MISSING. `prerequisites` carried
    the checkpoint-1 answer -- the capabilities this instance lacked -- and
    `bindings` carries this one: which of the decision, admission, staged
    input, adoption, custody, intake and reviewer binding is not there yet.
    A reader asking why a review is held gets the same answer from every
    incarnation, off durable rows.

    IT ANSWERS `None` FOR AN ORDINARY JOB, which is what makes it composable
    into the projection: a Job with no publication recovery control profile
    has no publication gate, and a gate that answered `closed` for one would
    block every ordinary review in the deployment.
    """
    boundaries.identity(job_id, "a Job id")
    control = job_control.control_of(store, job_id)
    if control is None \
            or control["profile"] != publication_recovery.PUBLICATION_PROFILE:
        return None
    held = publication_recovery.admission_for(store, job_id)
    if held is None:
        return None
    if stage_id is not None and stage_id != held["review_stage_id"]:
        return None
    handoff = handoff_of(store, job_id)
    present = {
        "decision": publication_recovery.decision_of(
            store, held["decision_id"]) is not None,
        "admission": True,
        "staged-input": staging_of(store, job_id) is not None,
        "adoption": result_of(store, job_id) is not None,
        "custody": custody_of(store, job_id) is not None,
        "intake": bool((custody_of(store, job_id) or {}).get("intake")),
        "reviewer-servability": handoff is not None,
    }
    return documents.publication_gate(
        job_id=job_id, open=handoff is not None,
        reason=(GATE_VALIDATED if handoff is not None else GATE_UNAVAILABLE),
        decision_id=held["decision_id"],
        prior_job_id=held["prior_job_id"],
        candidate=dict(held["candidate"]),
        runnable=handoff is not None,
        # THE CAPABILITY PREREQUISITES ARE EMPTY ON THIS PATH, and that is a
        # fact rather than an omission: an ADMITTED recovery is one every
        # prerequisite was available for, which is why it was admitted. What
        # is owed now is execution, and `bindings` is where that is said.
        prerequisites=[],
        stage_id=held["review_stage_id"],
        bindings=[{"name": one, "present": bool(present[one])}
                  for one in GATE_BINDINGS])


# -- 10b. a recovery that did not publish: settle it and tell the owner ------
#
# REVIEW 2026-11-23T20-28-00Z; COMPLETION-PLAN-385909 outcome 3. A publication
# that faulted, expired or was cancelled used to stop at a journalled hold:
# its runtime quiescent or still recorded as running, its cleanup pending, its
# workspace token never returned, and nobody told. Four things are owed and
# this act performs them in order, each replayable:
#
#   1. SAY WHAT ENDED IT, once (`ENDED`), when that is known. An exchange that
#      ended faulted is a worker saying it did not publish; a closed fence or
#      a reached bound is this store's own fact. A runtime nobody can read is
#      NOT an ending -- it stays an uncertainty.
#   2. ASK THE ENGINE NOW (`observation_of`). An answer that could not be
#      obtained is journalled as UNKNOWN and the act stops there: nothing is
#      removed, no token is returned and no item claims an outcome.
#   3. SETTLE THROUGH THE SUPPORTED ENDING (`settle`), which is the
#      composition's own `abandon_attempt`: it removes the exact runtime,
#      requires it positively absent, retains the workspace and returns the
#      exact token. Resource release does not wait on anybody accepting a
#      result, because there is no result.
#   4. DELIVER ONE OWNER ITEM, to the participant who decided, naming the
#      retained evidence and any effect that remains. No retry is started, no
#      analysis is requested and nothing is re-admitted.

def _known_ending(store, seam, held, intent, at):
    """The ending this recovery has, classified from facts, or `None` while
    nobody can say."""
    job_id = held["job_id"]
    recorded = ending_of(store, job_id)
    if recorded is not None:
        return recorded
    attempt_id = None if intent is None else intent["attempt_id"]
    terminal = None if intent is None else _terminal_of(seam, attempt_id)
    if terminal is not None and terminal["ending"] != "answered":
        return _ended(
            store, held, attempt_id, outcome="failed",
            cause=f"the confined publication worker ended its command "
                  f"{terminal['ending']} and published nothing", now=at)
    closed = _closure_of(store, held, at)
    if closed is not None:
        return _ended(store, held, attempt_id, outcome=closed["outcome"],
                      cause=closed["cause"], now=at)
    return None


def _unknown(store, held, attempt_id, *, recorded, why, now):
    """Journal that the runtime's cessation is NOT KNOWN as of `now`.

    ONE RECORD PER CHANGE OF KNOWLEDGE. A failure that is already standing is
    returned as it is: an engine that stays unreachable for an hour is one
    fact with one instant, not a row per tick.
    """
    standing = unknown_of(store, held["job_id"])
    if standing is not None:
        return standing
    return _noted(store, held, attempt_id, UNKNOWN_KIND, recorded, why, now)


def _known(store, held, attempt_id, *, recorded, now):
    """Journal that a fresh read SUCCEEDED after one that did not. Nothing is
    written when no failure is standing."""
    if unknown_of(store, held["job_id"]) is None:
        return None
    return _noted(store, held, attempt_id, KNOWN_KIND, recorded,
                  "the engine answered", now)


def _noted(store, held, attempt_id, kind, recorded, why, now):
    unknown, known = _knowledge(store, held["job_id"])
    sequence = (len(unknown) if kind == UNKNOWN_KIND else len(known)) + 1
    record = {"decision_id": held["decision_id"], "job_id": held["job_id"],
              "attempt_id": attempt_id, "recorded": recorded,
              "why": boundaries.text(why, "an observation note"),
              "observed_at": boundaries.instant(now, "an observation "
                                                     "instant")}
    operation = (unknown_operation_id if kind == UNKNOWN_KIND
                 else known_operation_id)(held["job_id"], sequence)
    try:
        return store.transact(
            operation, kind,
            job_signature(kind, {"decision_id": record["decision_id"],
                                 "job_id": record["job_id"],
                                 "sequence": sequence}),
            lambda connection: record)
    except ContractRefusal:                               # pragma: no cover
        return unknown_of(store, held["job_id"])


def _observed(store, seam, held, attempt_id, at):
    """A FRESH READ of the publication runtime, journalled as knowledge.

    Answers the port's own document. A read that failed leaves a standing
    UNKNOWN; one that succeeded clears a standing one. The recorded runtime
    axis is never returned as though it were this answer.
    """
    seen = seam["runtime"].observation_of(attempt_id)
    if type(seen) is not dict or seen.get("known") is not True:
        _unknown(store, held, attempt_id,
                 recorded=(seen or {}).get("recorded")
                 if type(seen) is dict else None,
                 why=str((seen or {}).get("why") if type(seen) is dict
                         else "") or "the engine could not be read", now=at)
        return None
    _known(store, held, attempt_id, recorded=seen.get("recorded"), now=at)
    return seen


def settle(store, seam, *, decision_id, now=None):
    """SETTLE ONE RECOVERY THAT DID NOT PUBLISH, and deliver its owner item.

    Replays its committed item. Refuses -- as a HELD act, changing nothing --
    while the ending is not known or the engine cannot be read.
    """
    taken = check_publication_seam(seam)
    _agreeing_instance(taken, what="this publication settlement")
    held = _admitted(store, decision_id)
    job_id = held["job_id"]
    delivered = owner_item_of(store, job_id)
    if delivered is not None:
        return delivered
    if result_of(store, job_id) is not None:
        _refuse(f"recovery {name_value(job_id)} published; there is no "
                f"failed publication to settle")
    at = boundaries.instant(now if now is not None else store._now(),
                            "a settlement instant")
    intent = launch_of(store, job_id)
    ended = _known_ending(store, taken, held, intent, at)
    if ended is None:
        _refuse(f"recovery {name_value(job_id)}'s publication has no known "
                f"ending; an uncertain adoption is held and is not settled "
                f"as a failure nobody observed",
                category="runtime-observation", code="quiescence-unknown")
    settled = settlement_of(store, job_id)
    if settled is None and intent is not None:
        attempt_id = intent["attempt_id"]
        if _observed(store, taken, held, attempt_id, at) is None:
            _refuse(f"publication attempt {name_value(attempt_id)}'s runtime "
                    f"could not be observed; its cessation is UNKNOWN, so "
                    f"nothing is removed, its workspace token stays held and "
                    f"no outcome is delivered as settled",
                    category="runtime-observation", code="quiescence-unknown")
        answered = taken["runtime"].settle(
            attempt_id,
            reason=f"publication recovery {decision_id} "
                   f"{ended['outcome']}: {ended['cause']}"[:480])
        state = _runtime_of(taken, attempt_id)
        if not (state["execution_runtime"] == "destroyed"
                and state["cleanup"] in ("complete", "retained")):
            _refuse(f"publication attempt {name_value(attempt_id)} was "
                    f"settled and its runtime is recorded "
                    f"{name_value(state['execution_runtime'])} with cleanup "
                    f"{name_value(state['cleanup'])}; a settlement is "
                    f"recorded only over a positively absent runtime",
                    category="runtime-observation", code="quiescence-unknown")
        record = {"decision_id": decision_id, "job_id": job_id,
                  "stage_id": held["publication_stage_id"],
                  "attempt_id": attempt_id, "outcome": ended["outcome"],
                  "runtime": {"execution_runtime":
                                  state["execution_runtime"],
                              "cleanup": state["cleanup"]},
                  "settlement": {name: (answered or {}).get(name)
                                 for name in ("outcome", "cleanup",
                                              "disposition")
                                 if type(answered) is dict},
                  "settled_at": at}
        settled = store.transact(
            settled_operation_id(job_id), SETTLED_KIND,
            job_signature(SETTLED_KIND, {"decision_id": decision_id,
                                         "job_id": job_id,
                                         "attempt_id": attempt_id}),
            lambda connection: record)
    return _delivered(store, held, ended, settled, intent, at)


def _delivered(store, held, ended, settled, intent, at):
    """THE OWNER ITEM, addressed to the participant who decided.

    WHAT IT CARRIES IS WHAT AN OWNER NEEDS TO DISPOSE OF IT: what ended the
    publication, where the retained material is, and what -- if anything --
    is still owed. It carries no bytes, no path an agent could redirect and
    no verdict.
    """
    job_id = held["job_id"]
    decision = publication_recovery.decision_of(store, held["decision_id"])
    staging = staging_of(store, job_id)
    remaining = []
    if intent is not None and settled is None:              # pragma: no cover
        remaining.append("the publication runtime's settlement")
    record = {
        "decision_id": held["decision_id"], "job_id": job_id,
        "prior_job_id": held["prior_job_id"],
        "outcome": ended["outcome"], "cause": ended["cause"],
        # THE PARTICIPANT WHO DECIDED, read off the committed decision. The
        # item goes to whoever approved this recovery and to nobody else.
        "destination": ((decision or {}).get("owner") or {}).get("endpoint"),
        "evidence": {
            "original": "the failed Job's retained output, unchanged; read "
                        "it with publication-inspect",
            "original_attempt_id": held["candidate"].get("attempt_id"),
            "staged_input": None if staging is None
            else staging["staged"]["locator"],
            "publication_attempt_id": None if intent is None
            else intent["attempt_id"],
            "publication_workspace": (
                None if intent is None else
                "retained under the publication attempt; not published, not "
                "frozen and not a candidate"),
            "runtime": None if settled is None else settled["runtime"]},
        "remaining": remaining,
        "automatic_retry": False,
        "delivered_at": at}
    return store.transact(
        owner_item_operation_id(job_id), OWNER_ITEM_KIND,
        job_signature(OWNER_ITEM_KIND, {"decision_id": record["decision_id"],
                                        "job_id": job_id}),
        lambda connection: record)


# -- 11. the level-triggered pass --------------------------------------------
#
# WHICH ACT ONE TICK PERFORMS, DERIVED FROM DURABLE ROWS and never from a
# process's memory. `retained_verification.advance_verification`'s shape and
# its reason: a restarted manager must owe exactly what the records say is
# owed, and a pass that remembered where it was would owe something else.
ACTS = ("stage", "publish", "custody", "hand-off", "settle")
ACT_OUTCOMES = ("performed", "held", "refused")


def publication_readiness(store, decision_id):
    """WHICH ACT THIS RECOVERY OWES NEXT, and what has already happened.

    THE WHOLE ANSWER IS DERIVED, so the same question asked by a status
    command, by the sweep and by a case gets the same answer. `owed` is the
    next act or `None` when the handoff is done -- and `None` does NOT mean
    "reviewed": it means this module has nothing further to do and the review
    stage is now the ordinary pipeline's.
    """
    held = _admitted(store, decision_id)
    job_id = held["job_id"]
    staged = staging_of(store, job_id)
    adopted = result_of(store, job_id)
    custody = custody_of(store, job_id)
    handoff = handoff_of(store, job_id)
    uncertain = hold_of(store, job_id)
    launched = launch_of(store, job_id)
    ended = ending_of(store, job_id)
    unknown = unknown_of(store, job_id)
    settled = settlement_of(store, job_id)
    item = owner_item_of(store, job_id)
    # A RECOVERY THAT DID NOT PUBLISH OWES ITS SETTLEMENT, and one whose own
    # control has closed before anything was recorded owes it too -- an
    # expired recovery nobody settled is an owner nobody told.
    closed = adopted is None and item is None and ended is None \
        and _closure_of(store, held, store._now()) is not None
    owed = None
    if adopted is None and item is not None:
        owed = None
    elif adopted is None and (uncertain is not None or ended is not None
                              or closed):
        owed = "settle"
    elif staged is None:
        owed = "stage"
    elif adopted is None:
        owed = "publish"
    elif custody is None:
        owed = "custody"
    elif handoff is None:
        owed = "hand-off"
    # WHAT IS KNOWN ABOUT THE RUNTIME, said so a reader cannot take the last
    # recorded axis for current knowledge (review 2026-11-23T20-28-00Z). A
    # failed observation stands until a settlement or a result supersedes it.
    not_known = unknown is not None and settled is None and adopted is None
    outcome = ("published" if adopted is not None else
               ended["outcome"] if ended is not None else
               "unknown" if (uncertain is not None or not_known) else None)
    return {"decision_id": decision_id, "job_id": job_id,
            "prior_job_id": held["prior_job_id"],
            "staged": staged is not None,
            "launched": launched is not None,
            "published": adopted is not None,
            "custody": custody is not None,
            "handed_off": handoff is not None,
            "uncertain": adopted is None and ended is None
            and (uncertain is not None or not_known),
            "outcome": outcome,
            "ended": None if ended is None else {
                "outcome": ended["outcome"], "cause": ended["cause"],
                "ended_at": ended["ended_at"]},
            "runtime_knowledge": (
                "settled: positively absent" if settled is not None else
                f"unknown: the engine could not be read at "
                f"{unknown['observed_at']}; the recorded runtime axis is the "
                f"last observation and is not current knowledge"
                if not_known else
                "recorded: the Worker Manager's own journal; read the "
                "attempt for it"),
            "settled": settled is not None,
            "owner_item": None if item is None else {
                "destination": item["destination"],
                "outcome": item["outcome"],
                "delivered_at": item["delivered_at"],
                "remaining": list(item["remaining"])},
            "review": "runnable" if handoff is not None else "blocked",
            "owed": owed,
            "original_job": "failed; unchanged by this recovery",
            "detail": ("the published candidate is in custody and the review "
                       "gate is open; the independent reviewer's own required "
                       "verification is owed to the review contract and "
                       "nothing here has judged it"
                       if handoff is not None else
                       "nothing is runnable for review: the exact publication "
                       "custody and candidate handoff REC-9 requires are not "
                       "both present")}


def _act(decision_id, job_id, act, outcome, detail=None):
    return documents.publication_act(decision_id=decision_id, job_id=job_id,
                                     act=act, outcome=outcome, detail=detail)


def advance_publication(store, seam, *, now=None):
    """ONE TICK of the publication pass, over every admitted recovery.

    LEVEL-TRIGGERED AND ORDERED. Each recovery owes exactly one act, derived
    from its own committed records, and this performs that one and stops --
    so a tick never tries to publish an unstaged original or hand off an
    uncollected candidate, and a crash anywhere leaves the next tick owing
    the same act.

    A CONTAINED REFUSAL IS REPORTED AND DOES NOT STOP THE PASS. One recovery
    whose host went uncertain, whose deadline was reached or whose Job was
    cancelled must not keep another recovery's tick from running; what crosses
    into the report is the refusal's typed category and code and never its
    prose, which is `documents`' own rule for every other pass.
    """
    taken = check_publication_seam(seam)
    at = boundaries.instant(now if now is not None else store._now(),
                            "a publication pass instant")
    acts = []
    for admitted in publication_recovery.admissions_of(store):
        decision_id = admitted["decision_id"]
        job_id = admitted["job_id"]
        try:
            owed = publication_readiness(store, decision_id)["owed"]
        except ContractRefusal as refusal:                # pragma: no cover
            acts.append(_act(decision_id, job_id, "stage", "refused",
                             {"category": refusal.category,
                              "code": refusal.code}))
            continue
        if owed is None:
            continue
        performer = {"stage": stage_input, "publish": publish,
                     "custody": take_custody, "hand-off": hand_off,
                     "settle": settle}[owed]
        try:
            answer = performer(store, taken, decision_id=decision_id, now=at)
        except ContractRefusal as refusal:
            acts.append(_act(decision_id, job_id, owed,
                             "held" if refusal.code in
                             ("quiescence-unknown", "precondition")
                             else "refused",
                             {"category": refusal.category,
                              "code": refusal.code}))
            continue
        acts.append(_act(decision_id, job_id, owed, "performed",
                         {"attempt_id": answer.get("attempt_id")
                          if type(answer) is dict else None}))
    return {"observed_at": at, "acts": acts}
