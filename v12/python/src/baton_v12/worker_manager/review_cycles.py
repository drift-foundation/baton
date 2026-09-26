"""Durable development lines, immutable review checkpoints and corrections.

The Worker Manager owns this lifecycle above disposable runtime attempts.  A
line is keyed by Authority and Work, while every writable or read-only
attachment is fenced to one activated assignment generation.  Source-specific
commands live behind an injected checkpoint profile; this component persists
only its closed evidence.
"""

import json
import os
import threading

from ..contracts import ContractRefusal, canonical_text, digest
from ..contracts.errors import name_value, sample_of
from . import (attempts, boundaries, custody, intake, manifests, output, schema,
               source_boundary, workspaces)
from .attempts import assignment_of
from .store import _recorded, manager_signature

__all__ = ["ABANDONED_CORRECTION", "ABANDONED_CORRECTION_SCHEMA",
           "ATTACH_KIND", "DISPOSITIONS", "GRANT_KIND", "LINE_HOME",
           "RESTORE_KIND", "VERDICT_KIND",
           "abandoned_correction_of", "attach_review", "audit_checkpoint",
           "checkpoint_of",
           "create_line", "freeze_checkpoint", "grant_writer",
           "RESTORE_SETTLED_KIND", "settle_restoration_execution",
           "integration_checkpoint", "line_of", "line_status",
           "record_progress", "record_verdict",
           "restore_abandoned_correction", "review_boundary",
           "review_for_attempt", "review_of", "verdict_of", "writer_boundary",
           "writer_for_attempt", "writer_of"]

DISPOSITIONS = ("accepted", "changes-requested", "rejected")

# W103076: THE TWO OPERATION KINDS THIS MODULE COMMITS ITS ATTACHMENTS AND
# VERDICTS UNDER. They are named here because the readers below cross-bind a
# materialized row against the act that wrote it, and because a consumer that
# had to spell them for itself would be keeping a copy of this module's
# journal shape -- which is exactly what the readers exist to stop.
ATTACH_KIND = "review-line.attach-review"
VERDICT_KIND = "review-line.verdict"
# W124331: the writer grant's kind, named beside the other two for the reason
# they are named -- the readers below cross-bind a materialized row against
# the act that wrote it, and a consumer spelling this for itself would be
# keeping a copy of this module's journal shape.
GRANT_KIND = "review-line.grant-writer"
LINE_HOME = ".baton-review-lines"

# W128692: THE ABANDONED CORRECTION'S RECOVERY, AS ITS OWN TWO ACTS.
#
# The INTENT is journalled before the profile is asked to write anything, and
# the OUTCOME after the restoration has been validated -- two identities
# because they are two facts. A crash between them leaves a recorded intent and
# no completion, which is exactly what a retry needs to find: the same
# exclusion, the same checkpoint, and no completed history to mistake for one.
RESTORE_INTENT_KIND = "review-line.restore-abandoned-intent"
# EXACTLY WHAT THE FIXED INTENT CARRIES. A resumed call adopts it from the
# journal rather than rebuilding it, so it is held to a contract on the way in
# as well as on the way out.
# W257624, review 2026-09-26T01:49:21Z [P1]: AND WHO IS EXECUTING IT. The other
# members identify WHICH recovery this is; `executor_incarnation` identifies the
# one manager instance whose external restoration is in flight for it, which is a
# different question and was the one nothing answered.
_RESTORE_INTENT = ("schema", "attempt_id", "assignment", "runtime_id",
                   "retention_policy_digest", "writer_id", "line_id",
                   "checkpoint_id", "checkpoint_digest", "cleanup_operation",
                   "discharge_operation_id", "executor_incarnation")
RESTORE_KIND = "review-line.restore-abandoned"
ABANDONED_CORRECTION_SCHEMA = "baton.v12.abandoned-correction/1"

# EXACTLY WHAT A COMPLETED RECOVERY CARRIES. Owner128669's contract, and both
# exits are held to it.
ABANDONED_CORRECTION = ("schema", "operation_id", "attempt_id", "assignment",
                        "runtime_id", "retention_policy_digest", "writer_id",
                        "line_id", "checkpoint_id", "checkpoint_evidence",
                        "cleanup_operation", "discharge_operation_id", "state")

# The state the recovered line is returned to, and it is the one
# `record_verdict` puts a changes-requested line in -- not a new state and not
# a new checkpoint.
_CORRECTION_READY = "correction-ready"
# The one revocation reason an abandoned-correction recovery writes. Named
# because the intent's revocation and the resumption's proof of it are two ends
# of one fact, and two spellings of it is how they come to disagree.
_ABANDONED_REVOCATION = "abandoned"

# W257624, review 2026-09-26T02:11:12Z [P1]: WHO OWNS THE EXTERNAL ACT, AND IT IS
# A ROW RATHER THAN A FACT ABOUT THIS PROCESS.
#
# THREE MECHANISMS WERE TRIED AND EACH WAS REPRODUCED PAST. The executor
# incarnation: `ControlStore.open` neither reserves an identity nor serializes its
# callers, so two handles naming one manager overlapped. A process-local registry
# keyed by the recovery: a caller paused between its eligibility reads and its
# acquisition took the guard AFTER a competitor had completed and released it, then
# ran its profile from cached rows; and a second operating-system process never saw
# the registry at all. What all three share is that none of them is durable, so the
# claim is journalled now.
#
# THE EPISODE IS THE OWNERSHIP. Each execution of one recovery's external act claims
# the NEXT episode through the ordinary journal, and a claim that has no completion
# behind it is an execution nobody has settled -- so the next caller is held rather
# than repeating an act whose effects are unknown. There is no expiry, no renewal and
# no heartbeat: this is not a lease, it is one row per attempt at one act.
RESTORE_EXECUTION_KIND = "review-line.restore-execution"

# W257624, review 2026-09-26T04:58:07Z [P1]: THE COVERAGE AN EPISODE WAS CLAIMED UNDER,
# RECORDED BEFORE ANY EFFECT.
#
# The settlement may read an EMPTY launch account as "nothing was ever started", because
# each launch intent is committed before its child exists. That inference is only sound
# if the executor that claimed the episode was actually running the accounting protocol
# and actually held the exclusion -- and the claim row said nothing about either. Its
# fields were exactly those of a pre-accounting episode, so a legacy claim and a
# current-protocol crash before the first command were INDISTINGUISHABLE, and the
# settlement read the second meaning into both.
#
# So the claim now carries its own provenance, written in the same transaction that takes
# it and therefore before the profile is reached: which protocol recorded it, that launches
# are recorded BEFORE they exist, and that the exclusion was held when it was taken. A
# claim without this is a claim whose coverage is unknown, and unknown is HELD.
RESTORE_ACCOUNTING_PROTOCOL = "launch-account/1"
_CLAIM_COVERAGE = {"protocol": RESTORE_ACCOUNTING_PROTOCOL,
                   "coverage": "pre-launch-record",
                   "exclusion": "held"}

# Per-invocation executor tokens. The process id separates processes and the counter
# separates invocations within one, so two callers cannot compose the same episode
# signature and silently replay each other's claim.
_EXECUTOR_GUARD = threading.Lock()
_EXECUTOR_COUNT = [0]


def _executor_token(store):
    with _EXECUTOR_GUARD:
        _EXECUTOR_COUNT[0] += 1
        return f"{store.incarnation}:{os.getpid()}:{_EXECUTOR_COUNT[0]}"


def _execution_id(recovery_id, episode):
    return f"{RESTORE_EXECUTION_KIND}:{recovery_id}:{episode}"


# W257624, owner ruling 2026-09-26T02:57:40Z: AND WHEN AN INTERRUPTED EXECUTION MAY
# BE RETRIED, which is the one thing the episode machinery could not say.
#
# A CLAIMED EPISODE WITH NO COMPLETION HELD FOREVER, deliberately, because an
# exception is not evidence that a checkout stopped being written. What the ruling
# adds is the other exit: a POSITIVE SETTLEMENT, journalled at its own identity,
# recording BOTH halves of what ending an execution means -- that the executor has
# ended and that its effects are accounted for.
RESTORE_SETTLED_KIND = "review-line.restore-execution-settled"

# W257624, review 2026-09-26T03:08:20Z [P1]: THE FORGEABLE ATTESTATION IS GONE.
#
# What stood here took a DOCUMENT -- a kind, an executor token and an observer string
# -- and treated it as evidence that an execution had ended. The token is readable
# from the journal, so any caller could author it about a demonstrably live executor;
# the reviewer's reproduction did exactly that and lost a successor's bytes. A shape
# check is not an observation and a blacklist of other words does not reject the same
# unsupported inference wearing the permitted one. The helper is REMOVED rather than
# tightened, because dead forgeable code is worse than none.
#
# THE BOUNDARY THAT ANSWERS IT now exists and the entry is ENABLED (2026-09-26, review
# 271851): an exclusive advisory lock held beside the line for the span of the external
# act, probed NON-BLOCKING by a later caller, which the kernel releases when a process
# dies and which therefore distinguishes a crashed executor from a live one. The manager
# performs that probe itself -- it is not handed a document about it -- and pairs it with
# the launch account, because the kernel answers for managers and nothing but the account
# answers for the children their runners forked.


def _settled_episodes(store, recovery_id):
    """Every episode of this recovery that carries a settlement, by number."""
    settled = {}
    for episode in range(1, len(_claimed_episodes(store, recovery_id)) + 1):
        found = store.operation_record(_settled_id(recovery_id, episode))
        if found is not None:
            settled[episode] = found
    return settled


def _settled_id(recovery_id, episode):
    return f"{RESTORE_SETTLED_KIND}:{recovery_id}:{episode}"


def _claimed_episodes(store, recovery_id):
    """Every episode this store has a claim row for, lowest first.

    READ BY DERIVED IDENTITY rather than by scanning the journal table, which is the
    same rule `ending.pending_endings` follows: nothing here reads raw journal SQL,
    so another deployment's operations are invisible to it.
    """
    episodes = []
    while True:
        found = store.operation_record(_execution_id(recovery_id,
                                                    len(episodes) + 1))
        if found is None:
            return episodes
        episodes.append(found)


RESTORE_LAUNCH_KIND = "review-line.restoration-launch"


def _launch_id(recovery_id, episode, ordinal, part):
    return f"{RESTORE_LAUNCH_KIND}:{recovery_id}:{episode}:{ordinal}:{part}"


def _launch_recorder(store, recovery_id, episode):
    """The per-invocation recorder a restoration's launcher writes through.

    W257624. BOUND TO THE EXACT STORE, RECOVERY AND EPISODE, which is the binding the
    owner ruling requires: every identity below is derived from all three, so a launch
    record can never be read as belonging to another recovery or another attempt at this
    one.

    EVERY LAUNCHED COMMAND IS COUNTED, not just the first. A restoration issues more than
    one command, and an account that recorded only one would leave the others unexamined;
    the ordinal advances per launch so each has its own intent and its own group.

    THE INTENT IS COMMITTED BEFORE ITS CHILD EXISTS and the group immediately after the
    fork -- that ordering is the launcher's, and this only supplies the durable place for
    it. An intent with no group is the mid-call death window and its consumer HOLDS.

    ONE-TIME ADMISSION, NOT A REPLAY. Review 2026-09-26T04:27:09Z [P2] reproduced the
    defect and also caught a false claim of mine: I wrote that a second `intent` at a
    taken ordinal refuses, and the code returned silently. A recorder recreated for the
    same store, recovery and episode restarted its ordinals at one, found intent one
    already recorded, returned as though it had recorded something, and the launcher then
    forked a SECOND child under an identity that already accounted for a different one.

    SO A RECREATED RECORDER REFUSES, and the ordinal is claimed from the RECORD rather
    than counted in memory. Each `intent` opens a short raw transaction -- `create_line`'s
    own precedent in this module -- reads the launches this episode holds, and writes the
    next number; the closure then remembers only which ordinal IT won, so its `group` lands
    against its own launch. A recorder built for an episode that already holds launches
    refuses its first `intent` outright: the executor owning this episode already has its
    recorder, so a second one is re-entry that cannot be told apart from an unaccounted
    duplicate.

    MEASURED, AND WEAKER THAN IT READS: with that refusal in place, counting in memory
    instead of reading the record fails NO case of mine -- probed, 2026-09-26. The raw
    transaction is defence in depth against a concurrency the outer exclusion already
    forbids; the REFUSAL is what carries the property today.

    AND A GROUP IS WRITTEN ONCE, WITH ITS BYTES COMPARED. A second `group` for an ordinal
    that already holds one refuses unless it is byte-identical; the previous code returned
    silently and would have let a different payload pass unnoticed, which is the same
    defect one record along.
    """
    # ONE RECORDER PER EPISODE'S LAUNCH SEQUENCE. Review 2026-09-26T04:27:09Z [P2] reads
    # the contract as a RECREATED recorder refusing, and that is the fail-closed reading:
    # the executor that owns this episode already has its recorder, so a second one for an
    # episode that already holds launches is re-entry that cannot be told apart from an
    # unaccounted duplicate. Captured at construction, so this recorder's OWN later
    # launches advance normally.
    existing = _launch_count(store, recovery_id, episode)
    claimed = []

    def record(part, payload):
        document = lambda ordinal: {
            "schema": ABANDONED_CORRECTION_SCHEMA, "recovery": recovery_id,
            "episode": episode, "ordinal": ordinal, "part": part,
            "observed": dict(payload) if payload is not None else None}
        if part == "intent":
            if existing and not claimed:
                raise ContractRefusal(
                    "refused", "operation-collision",
                    f"this recovery's episode {episode} already holds {existing} "
                    f"recorded launch(es) and this recorder has claimed none of them; a "
                    f"recreated recorder is re-entry rather than a fresh account, and a "
                    f"launch it admitted could not be told apart from a duplicate")
            connection = store._connection
            connection.execute("BEGIN IMMEDIATE")
            try:
                taken = _launch_count(store, recovery_id, episode)
                ordinal = taken + 1
                held = document(ordinal)
                store._record(
                    _launch_id(recovery_id, episode, ordinal, part),
                    RESTORE_LAUNCH_KIND,
                    manager_signature(RESTORE_LAUNCH_KIND, held),
                    "committed", _recorded(held), None)
                connection.execute("COMMIT")
            except BaseException:
                try:
                    connection.execute("ROLLBACK")
                except Exception:
                    pass
                raise
            claimed.append(ordinal)
            return
        if not claimed:
            raise ContractRefusal(
                "refused", "precondition",
                "a restoration launch records its group against the intent it claimed, "
                "and this recorder has claimed none")
        ordinal = claimed[-1]
        held = document(ordinal)
        operation_id = _launch_id(recovery_id, episode, ordinal, part)
        signature = manager_signature(RESTORE_LAUNCH_KIND, held)
        recorded = store.operation_record(operation_id)
        if recorded is not None:
            if recorded["signature"] != signature:
                raise ContractRefusal(
                    "refused", "operation-collision",
                    f"launch {ordinal} of this recovery already recorded a different "
                    f"group; one launch has one group and a second account of it is not "
                    f"a replay")
            return
        store.transact(operation_id, RESTORE_LAUNCH_KIND, signature,
                       lambda connection: dict(held))

    return record


def _launched_commands(store, recovery_id, episode):
    """Every launch this episode recorded, as (intent, group-or-absence) pairs."""
    launches = []
    ordinal = 1
    while True:
        intent = store.operation_record(_launch_id(recovery_id, episode, ordinal,
                                                   "intent"))
        if intent is None:
            return launches
        group = store.operation_record(_launch_id(recovery_id, episode, ordinal,
                                                  "group"))
        answered = None
        if group is not None:
            _, answered = store.replay(
                _launch_id(recovery_id, episode, ordinal, "group"),
                group["signature"], kind=RESTORE_LAUNCH_KIND)
        launches.append((ordinal, answered))
        ordinal += 1


def _launch_count(store, recovery_id, episode):
    """How many launches this episode has recorded. A pure journal read."""
    return len(_launched_commands(store, recovery_id, episode))


def _effects_ended(store, recovery_id, episode, cessation, what, *,
                   unlaunched_is_settled=False):
    """Refuse unless EVERY launch this episode recorded has positively ended.

    W257624, review 2026-09-26T04:06:15Z [P1]. This is the check the completion did not
    make. The bound launcher's direct child exited zero, a same-group descendant closed
    its stdio and stayed, the profile answered that the checkout was clean -- and the
    release committed while that descendant was still able to write, which it then did.
    A profile's answer describes one instant; it says nothing about work still running.

    SO BOTH EXITS ASK THE SAME ACCOUNT. The normal completion and the settlement are
    gated here, not on a leader's exit status and not on profile evidence.

    AN EMPTY LIST IS NOT AN ACCOUNT ON THE COMPLETION PATH. A restoration that ran its
    profile and recorded no launch recorded nothing, and reading that as "everything
    ended" is the same mistake in a different place.

    BUT AN EMPTY LIST IS EXACTLY WHAT AN EXECUTOR THAT DIED BEFORE FORKING LEAVES, and
    `unlaunched_is_settled` is the settlement's own reading of it -- allowed there and
    nowhere else. The intent for each launch is COMMITTED BEFORE its child exists, which
    is the whole reason it is written first: no intent means no child was ever started,
    so there is nothing outstanding to observe. The settlement may only rely on that
    having already proved, through the kernel, that no MANAGER still holds the execution;
    an empty account on its own says nothing, and this parameter does not change that.

    AN INTENT WITHOUT ITS GROUP IS THE MID-CALL DEATH WINDOW, and `unknown` from the
    probe is unknown -- neither is ended, and both HOLD on BOTH paths. The refusal is
    NON-DURABLE so the episode stays claimed, the line stays `writing` and nothing is
    admitted.
    """
    launches = _launched_commands(store, recovery_id, episode)
    if not launches:
        if unlaunched_is_settled:
            return 0
        raise ContractRefusal(
            "refused", "precondition",
            f"{what}'s episode {episode} recorded no launch, so nothing accounts for "
            f"the external work it performed; an empty account is not an account and "
            f"this act is held rather than releasing a line whose effects are unknown")
    for ordinal, group in launches:
        if group is None:
            raise ContractRefusal(
                "refused", "precondition",
                f"{what}'s episode {episode} launch {ordinal} recorded an intent with "
                f"no group behind it; a child may exist for it and nothing can say "
                f"otherwise, so this act is held")
        answered = cessation(group.get("observed"))
        if answered != "ended":
            raise ContractRefusal(
                "refused", "precondition",
                f"{what}'s episode {episode} launch {ordinal} is {name_value(answered)} "
                f"rather than ended; a restoration's line is released when its external "
                f"work has stopped, not when its checkout happened to look clean")
    return len(launches)


def _unsettled_episodes(store, recovery_id):
    """Every claimed episode of this recovery that carries no settlement, lowest first.

    W257624. One reading of the journal, used by the executor gate in
    `restore_abandoned_correction` and by `_admitted_execution`'s transaction, so the
    condition a caller is held on and the condition its admission is decided on are the
    same sentence rather than two similar ones.
    """
    claimed = _claimed_episodes(store, recovery_id)
    settled = _settled_episodes(store, recovery_id)
    return [number for number in range(1, len(claimed) + 1)
            if number not in settled]


def _admitted_execution(store, operation_id, line, writer, checkpoint, what):
    """Decide replay, eligibility AND exclusive ownership in ONE transaction.

    W257624, review 2026-09-26T02:25:54Z [P1]. My previous cut committed the
    read-and-check transaction and then claimed the episode in a SECOND one, while
    the comments claimed the two were one act. They were not, and the reviewer
    scheduled the gap: A pauses between them, B claims episode 1, restores,
    completes and releases, a successor is granted and writes -- and A then claims
    episode TWO, because another execution had become visible in between, and
    restores over the successor's work. Allocating a later episode merely because a
    competitor appeared is exactly the defect.

    SO THERE IS ONE TRANSACTION AND THE CLAIM IS INSIDE IT. `BEGIN IMMEDIATE`
    serializes every caller that reaches here, so the completion read, the
    eligibility proof, the unsettled-episode check and the INSERT of this
    invocation's own claim are one observation and one decision. Two callers cannot
    both compute the same next episode and both write it, and a caller that was
    asleep re-reads the completion here and returns it having performed nothing at
    all.

    THE RAW SHORT TRANSACTION IS THIS MODULE'S OWN PRECEDENT -- `create_line` takes
    `BEGIN IMMEDIATE` and commits or rolls back by hand -- and it is necessary
    rather than stylistic: `store.transact` is keyed by an operation identity and
    replays, so it cannot make a fresh decision, and it cannot be nested inside
    this lock either.

    THE JOURNAL ROW IS WRITTEN THROUGH `ControlStore._record`, this build's one
    journal writer, because the row has to land in THIS transaction rather than a
    later one. That is the recorded path extension for this correction. Nothing
    here touches a filesystem and the whole act is a handful of statements.

    ANSWERS EITHER a completed recovery -- meaning this caller performs no effect --
    or the episode and token this invocation now owns.
    """
    connection = store._connection
    connection.execute("BEGIN IMMEDIATE")
    try:
        if store.operation_record(operation_id) is not None:
            answered = abandoned_correction_of(
                store, attempt_id=writer["runtime_attempt_id"],
                generation=writer["assignment_generation"])
            connection.execute("COMMIT")
            return answered, None, None
        current_line = line_of(store, line["line_id"])
        current_writer = writer_of(store, writer["writer_id"])
        if current_line["state"] != "writing" \
                or current_line["current_checkpoint_id"] \
                != checkpoint["checkpoint_id"] \
                or current_writer["state"] != "revoked" \
                or current_writer["revocation_reason"] != _ABANDONED_REVOCATION:
            raise ContractRefusal(
                "refused", "precondition",
                f"{what}'s line no longer holds the exclusion this recovery was "
                f"proved against; a restoration is admitted against the state the "
                f"store holds now and not the state its caller last read")
        if _line_object(current_line) != _line_object(line):
            raise ContractRefusal(
                "runtime-observation", "identity-mismatch",
                f"{what}'s line row no longer names the object this admission was "
                f"proved against")
        claimed = _claimed_episodes(store, operation_id)
        unsettled = _unsettled_episodes(store, operation_id)
        if unsettled:
            raise ContractRefusal(
                "refused", "precondition",
                f"{what}'s external restoration was claimed as episode "
                f"{unsettled[0]} and neither a completion nor a settlement stands "
                f"behind it; that execution's effects are unknown, so this act is "
                f"held rather than repeating them")
        # THE CLAIM, IN THIS SAME TRANSACTION. The next episode is one past the last
        # claimed one, and reaching here means every earlier episode carries a
        # POSITIVE SETTLEMENT -- the owner ruling's condition for a retry. A caller
        # can no longer take a later number merely because a competitor appeared,
        # because an unsettled episode holds above.
        episode, token = len(claimed) + 1, _executor_token(store)
        # THE COVERAGE IS PART OF THE CLAIM, not a later annotation: this transaction runs
        # before the profile is reached, under the exclusion this caller already holds, so
        # the row is durable evidence of both by the time any effect could exist.
        document = {"schema": ABANDONED_CORRECTION_SCHEMA,
                    "recovery": operation_id, "episode": episode,
                    "executor": token, **_CLAIM_COVERAGE}
        store._record(_execution_id(operation_id, episode),
                      RESTORE_EXECUTION_KIND,
                      manager_signature(RESTORE_EXECUTION_KIND, document),
                      "committed", _recorded(document), None)
        connection.execute("COMMIT")
        return None, episode, token
    except BaseException:
        try:
            connection.execute("ROLLBACK")
        except Exception:
            pass
        raise


def _id(prefix, value):
    return prefix + "-" + digest(value).split(":", 1)[1]


def _profile(profile, methods):
    name = getattr(profile, "name", None)
    boundaries.text(name, "a checkpoint profile name")
    for method in methods:
        boundaries.capability(getattr(profile, method, None),
                              f"a checkpoint profile's {method} capability")
    return name


def line_of(store, line_id):
    boundaries.identity(line_id, "a development line identity")
    row = store._connection.execute(
        "SELECT * FROM review_lines WHERE line_id = ?", (line_id,)).fetchone()
    if row is None:
        raise ContractRefusal("refused", "precondition",
                              f"no development line {name_value(line_id)}")
    return boundaries.row(row, "a persisted development line",
                          schema.REVIEW_LINE_COLUMNS)


def writer_of(store, writer_id):
    boundaries.identity(writer_id, "a line writer identity")
    row = store._connection.execute(
        "SELECT * FROM line_writers WHERE writer_id = ?", (writer_id,)).fetchone()
    if row is None:
        raise ContractRefusal("refused", "precondition",
                              f"no line writer {name_value(writer_id)}")
    return boundaries.row(row, "a persisted line writer",
                          schema.LINE_WRITER_COLUMNS)


def checkpoint_of(store, checkpoint_id):
    boundaries.identity(checkpoint_id, "a line checkpoint identity")
    row = store._connection.execute(
        "SELECT * FROM line_checkpoints WHERE checkpoint_id = ?",
        (checkpoint_id,)).fetchone()
    if row is None:
        raise ContractRefusal("refused", "precondition",
                              f"no line checkpoint {name_value(checkpoint_id)}")
    taken = boundaries.row(row, "a persisted line checkpoint",
                           schema.LINE_CHECKPOINT_COLUMNS)
    if taken["evidence"] is not None:
        taken["evidence"] = _evidence(json.loads(taken["evidence"]))
    if taken["fence"] is not None:
        taken["fence"] = _fence(json.loads(taken["fence"]),
                                "a persisted checkpoint fence")
        if taken["fence_digest"] != digest(taken["fence"]):
            raise ContractRefusal(
                "integrity", "digest",
                "persisted checkpoint fence does not match its digest")
        _committed_fence(store, taken["fence"],
                         "the persisted checkpoint fence")
    if taken["state"] == "frozen":
        evidence = taken["evidence"]
        recorded = (taken["profile_name"], taken["base_object"],
                    taken["head_object"], taken["tree_object"],
                    taken["path_set_digest"], taken["reference_name"],
                    taken["checkpoint_digest"])
        derived = (evidence["profile"], evidence["base"], evidence["head"],
                   evidence["tree"], evidence["path_set_digest"],
                   evidence["reference"], digest(evidence))
        if recorded != derived:
            raise ContractRefusal(
                "integrity", "digest",
                "persisted checkpoint columns do not match their sealed evidence")
    return taken


def _evidence(value):
    taken = boundaries.document(
        value, "persisted checkpoint evidence",
        required=("base", "head", "path_set_digest", "paths", "profile",
                  "reference", "tree"))
    for member in ("base", "head", "path_set_digest", "profile", "reference",
                   "tree"):
        boundaries.text(taken[member],
                        f"persisted checkpoint evidence's {member}")
    paths = taken["paths"]
    if type(paths) is not list:
        raise ContractRefusal("integrity", "schema",
                              "persisted checkpoint evidence's paths is a list")
    for path in paths:
        boundaries.text(path, "a persisted checkpoint evidence path")
        if path.startswith("/") or ".." in path.split("/"):
            raise ContractRefusal("integrity", "path",
                                  "a persisted checkpoint path is relative and canonical")
    if paths != sorted(set(paths)) or taken["path_set_digest"] != digest(paths):
        raise ContractRefusal("integrity", "digest",
                              "persisted checkpoint paths do not match their digest")
    return taken


def _committed_operands(store, kind, operation_id, what):
    """The OPERANDS one of this module's own acts was authorized with.

    W103076 second re-review [P0]. `_committed_act` answers what an act
    RETURNED, and for `attach_review` that is three members -- so a reader
    comparing only those left `runtime_attempt_id`, the generation and the
    reviewer identity unbound, and a rewritten attempt row was answered without
    refusal. The operands are the whole of what the act was authorized with,
    they are in the signature this module built, and they are read here rather
    than by anybody else because a journal's shape is the owner's.
    """
    record = store.operation_record(operation_id)
    if record is None or record["kind"] != kind \
            or record["state"] != "committed":
        raise ContractRefusal(
            "refused", "precondition",
            f"{what} has no committed {kind} act; a materialized row this "
            f"manager cannot explain is not evidence about anything")
    document = json.loads(record["signature"])
    if not isinstance(document, dict) or document.get("kind") != kind \
            or not isinstance(document.get("operands"), dict):
        raise ContractRefusal(
            "integrity", "schema",
            f"the committed {kind} act for {what} carries no operands this "
            f"build can read")
    return document["operands"]


def _bound_to_act(operands, held, what, kind):
    """Every member of a row that its act fixed, compared with what it fixed.

    A DISAGREEMENT REFUSES RATHER THAN BEING RECONCILED, because two accounts
    of one decision have no tie-break and inventing one here would be this
    module choosing which of its own records to believe.
    """
    for member, (source, value) in held.items():
        if operands.get(source) != value:
            raise ContractRefusal(
                "integrity", "schema",
                f"{what} and the {kind} act that wrote it disagree about "
                f"{member}")


def _committed_act(store, kind, operation_id, what):
    """The committed journal row for one of THIS module's own acts.

    W103076. WHY THE READERS BELOW DO THIS AT ALL. A materialized row says what
    this store currently holds; the journal says which committed act put it
    there. Cross-binding them is what makes a reader's answer evidence rather
    than a projection -- a row that no committed act of the right kind explains
    is a row this build must not hand out as though somebody had decided it.

    It is the same discipline `_committed_fence` already applies to a
    persisted fence, and it belongs at the OWNER: a consumer that reconstructed
    this module's operation identities and parsed its journal for itself would
    be keeping a second account of a shape only this module gets to change.
    """
    record = store.operation_record(operation_id)
    if record is None or record["kind"] != kind \
            or record["state"] != "committed":
        raise ContractRefusal(
            "refused", "precondition",
            f"{what} has no committed {kind} act; a materialized row this "
            f"manager cannot explain is not evidence about anything")
    return json.loads(record["result"]) if record["result"] else None


def _verdict_row(store, verdict_id):
    """THE ONE CROSSING out of `checkpoint_verdicts`, or absence.

    W103076 extracted it. Two readers now answer about a recorded verdict --
    integration eligibility and `verdict_of` -- and a table adopted in two
    places is two column contracts that can drift, which is the shape the
    manager's own boundary inventory exists to prevent. One site, one
    adoption, and each caller decides what absence means for it.
    """
    boundaries.identity(verdict_id, "a checkpoint verdict identity")
    row = store._connection.execute(
        "SELECT * FROM checkpoint_verdicts WHERE verdict_id = ?",
        (verdict_id,)).fetchone()
    if row is None:
        return None
    return boundaries.row(row, "a persisted checkpoint verdict",
                          schema.CHECKPOINT_VERDICT_COLUMNS)


def review_of(store, attachment_id):
    """One review attachment, bound to the act that attached it.

    W103076. WHAT A CONSUMER NEEDS FROM THIS and could not get before: WHICH
    RUNTIME ATTEMPT a reviewer attachment belongs to. A composite that ends a
    review has an attachment identity and must not take the attempt as a
    second, independently chosen operand -- two live lines would otherwise let
    it freeze one reviewer's output and record a verdict about another's.

    THE ANSWER IS THE ROW, PROVED BY THE ACT. `attach_review` commits under an
    identity derived from the attachment and journals the checkpoint it
    attached to, so the row's own `checkpoint_id` is compared with what that
    act recorded. A row and an act that disagree refuse rather than being
    reconciled here.
    """
    attachment = _attachment(store, attachment_id)
    what = f"review attachment {name_value(attachment_id)}"
    operands = _committed_operands(store, ATTACH_KIND,
                                   ATTACH_KIND + ":" + attachment_id, what)
    _bound_to_act(operands, {
        "attachment_id": ("attachment_id", attachment_id),
        "checkpoint_id": ("checkpoint_id", attachment["checkpoint_id"]),
        # THE ONE THE SECOND RE-REVIEW REWROTE. Without it a
        # foreign-key-valid attempt from another lane was answered as this
        # attachment's, and a composite that trusts the answer stops and
        # freezes the wrong runtime.
        "runtime_attempt_id": ("attempt_id",
                               attachment["runtime_attempt_id"]),
        "assignment_generation": ("generation",
                                  attachment["assignment_generation"]),
        "reviewer_worker_id": ("reviewer_worker_id",
                               attachment["reviewer_worker_id"]),
        "reviewer_participant": ("participant",
                                 attachment["reviewer_participant"]),
        "reviewer_principal": ("principal", attachment["reviewer_principal"]),
    }, what, ATTACH_KIND)
    # AND THE LINE, WHICH THE ACT DID NOT NAME AND THE CHECKPOINT DOES. An
    # attachment whose line is not its checkpoint's line is a row no act of
    # this module could have written.
    if attachment["line_id"] != checkpoint_of(
            store, attachment["checkpoint_id"])["line_id"]:
        raise ContractRefusal(
            "integrity", "schema",
            f"{what} names a line its checkpoint does not belong to")
    return attachment


# W124331 review 2026-09-09T03:05Z [P1]. THE CLOSED JOURNAL SHAPE each
# historical reader proves its row against. Naming the members is what turns
# `.get` from a guess into a read: an operand that may legitimately be null --
# `based_checkpoint_id` on a first round -- is indistinguishable from a MISSING
# one under `.get` equality, and the reader would then answer a truncated act
# as though it agreed.
_SIGNATURE_MEMBERS = ("kind", "operands")
_GRANT_OPERANDS = ("writer_id", "line_id", "attempt_id", "generation",
                   "worker_id", "profile_name", "participant", "principal",
                   "based_checkpoint_id")
_GRANT_RESULT = ("writer_id", "line_id", "generation", "state")
# W124331 review 2026-09-09T03:14Z [P1]. THE STATE EACH ACT RETURNS, which is
# not the state its row is in later. A grant returns `active` and an
# attachment returns `active`; the row afterwards is `revoked` and `ended`,
# and those are different statements about different objects. The result is
# the act's own frozen account of what it did, so its state is exact -- a
# result recording `revoked`, a list or nothing at all is not the account
# either act emits, whatever the row has since become.
_ACT_RETURNS = "active"
_ATTACH_OPERANDS = ("attachment_id", "checkpoint_id", "attempt_id",
                    "generation", "reviewer_worker_id", "participant",
                    "principal")
_ATTACH_RESULT = ("attachment_id", "checkpoint_id", "state")


def _requested_pair(attempt_id, generation):
    """The exact pair a historical lookup selects on, typed before selection.

    W124331. `boundaries.generation` excludes `bool` in its own words, and that
    matters here twice: a boolean would select generation 1's row and would
    then compare equal to it. Owning both operands before the query is what
    stops a lookup from answering somebody else's history.
    """
    return (boundaries.identity(attempt_id, "a runtime attempt id"),
            boundaries.generation(generation, "an assignment generation"))


def _one_by_attempt(store, table, columns, attempt_id, generation, what):
    """The one row for this attempt and generation, or absence.

    THE UNIQUENESS IS THE SCHEMA'S AND IS REUSED RATHER THAN RESTATED. Both
    tables carry `UNIQUE (runtime_attempt_id, assignment_generation)`, so a
    pair selects one row or none and this reader never has to choose between
    two. A second row cannot exist for the query to find.
    """
    found = store._connection.execute(
        f"SELECT * FROM {table} WHERE runtime_attempt_id = ? "
        f"AND assignment_generation = ?", (attempt_id, generation)).fetchall()
    if not found:
        return None
    if len(found) > 1:
        raise ContractRefusal(
            "integrity", "schema",
            f"{what} selects {len(found)} rows for one attempt and "
            f"generation; the table's own uniqueness says there is one")
    return boundaries.row(found[0], what, columns)


def _journalled(text, what):
    """One committed journal document, refused in THIS domain's words.

    W124331 review [P1]: both new readers reached `json.loads` directly and a
    damaged signature escaped as `JSONDecodeError`. A parser error is not a
    refusal -- it carries no category, no code and no pairing, so a consumer
    that handles this manager's refusals does not handle it at all, and the
    one thing the reader exists to say ("this history cannot be trusted") is
    the one thing it fails to say.
    """
    if type(text) is not str or not text:
        raise ContractRefusal(
            "integrity", "schema",
            f"{what} is not journalled text; a row whose act recorded nothing "
            f"is not evidence about anything")
    try:
        document = json.loads(text)
    except ValueError:
        raise ContractRefusal(
            "integrity", "schema",
            f"{what} is not readable as a journal document") from None
    return document


def _committed_history(store, kind, operation_id, what, operand_members,
                       result_members, result_state):
    """This module's own committed act behind a historical row, read WHOLE.

    W124331 review [P1]. `_committed_operands` answers what an act was
    authorized with and is left exactly as it is -- the existing readers'
    behaviour is not this Work's to change. What a HISTORICAL reader needs on
    top of it is everything a damaged journal can be: unparseable, a document
    of another shape, an act that recorded no result, or a result belonging to
    something else. Each of those was answered with the honest row before this,
    which is the worst possible outcome for a reader whose whole purpose is
    telling a resuming consumer that its history is intact.

    So the signature, its operands and the act's own result are each adopted
    against a CLOSED member contract, and EVERY generation either carries is
    typed rather than compared -- a journalled `true` would otherwise satisfy
    an equality against generation one, for `_requested_pair`'s reason one
    layer down. Review [P1] found that reasoning applied to the operands and
    not to the result, which is the same value under a different key: closing
    a member set says the value is PRESENT, and nothing at all about what it
    is.

    Kept private to the new boundary, as the approved proposal requires.
    """
    record = store.operation_record(operation_id)
    if record is None or record["kind"] != kind \
            or record["state"] != "committed":
        raise ContractRefusal(
            "refused", "precondition",
            f"{what} has no committed {kind} act; a materialized row this "
            f"manager cannot explain is not evidence about anything")
    signed = f"the committed {kind} signature for {what}"
    signature = boundaries.document(_journalled(record["signature"], signed),
                                    signed, required=_SIGNATURE_MEMBERS)
    if signature["kind"] != kind:
        raise ContractRefusal(
            "integrity", "schema",
            f"{signed} was signed as {name_value(signature['kind'])}")
    operands = boundaries.document(
        signature["operands"], f"the committed {kind} operands for {what}",
        required=operand_members)
    answered = f"the committed {kind} result for {what}"
    result = boundaries.document(_journalled(record["result"], answered),
                                 answered, required=result_members)
    boundaries.generation(operands["generation"],
                          f"the committed {kind} generation for {what}")
    if "generation" in result_members:
        boundaries.generation(result["generation"],
                              f"the committed {kind} result generation for "
                              f"{what}")
    # THE ACT'S OWN ACCOUNT OF WHAT IT DID, not a claim about the row now.
    if result["state"] != result_state:
        raise ContractRefusal(
            "integrity", "schema",
            f"{answered} records state {name_value(result['state'])} rather "
            f"than the {name_value(result_state)} that act returns")
    return operands, result


def _derived_identity(prefix, operands, members, held, what):
    """The identity re-minted from the very operands that minted it.

    W124331 review [P1]. Comparing an act's members one by one says they agree;
    it does not say the act's IDENTITY follows from them. These identities are
    deterministic digests, so re-deriving is the whole proof -- and a row filed
    under an identity its own operands do not produce is one no act of this
    module could have written, however well its members read.
    """
    derived = _id(prefix, {member: operands[source]
                           for member, source in members})
    if derived != held:
        raise ContractRefusal(
            "integrity", "schema",
            f"{what} is filed under {name_value(held)}, which its committed "
            f"operands do not derive")


def _assignment_agrees(store, attempt_id, line, held, what, kind):
    """The WHOLE fixed assignment the act read, checked against its own owner.

    W124331 review [P1]: participant and principal alone left the generation
    and the Work/Authority correlation unbound, so an attempt whose fixed
    generation had been moved to 99 still answered generation one's writer.
    The assignment is a four-part identity and the schema keeps its columns
    together; reading three quarters of one is how a row outlives the
    authorization it was made under without saying so.
    """
    assignment = assignment_of(store, attempt_id)
    boundaries.generation(assignment["generation"],
                          f"{what}'s fixed assignment generation")
    disagreements = sorted(member for member, value in held.items()
                           if assignment[member] != value)
    if disagreements:
        raise ContractRefusal(
            "integrity", "schema",
            f"{what} and the fixed assignment its {kind} act read disagree "
            f"about {', '.join(disagreements)}")
    if assignment["work_id"] != line["work_id"] \
            or assignment["authority_uuid"] != line["authority_uuid"]:
        raise ContractRefusal(
            "integrity", "schema",
            f"{what} belongs to a line held for another Work or Authority "
            f"than the assignment its {kind} act read")


def writer_for_attempt(store, *, attempt_id, generation):
    """The line writer this attempt was granted, whatever became of it.

    W124331, `work/records/2026/09/finding-v12-composed-ending-consumer/
    findings/finding-attempt-history-readers/`.

    WHAT COULD NOT BE ASKED BEFORE. Every historical reader here takes a writer
    or attachment identity, and those identities are DERIVED inside
    `grant_writer` and `attach_review` from facts a consumer holds -- so a
    deployment recovering its own ended attempt could reach its writer only by
    copying that derivation or by reading the line's CURRENT checkpoint. The
    first keeps a second copy of an identity only this module may change; the
    second is a mutable pointer that every later round moves, which is exactly
    how an honest recovery of an earlier ending became impossible. This answers
    from the attempt and its generation, which do not move.

    HISTORY IS THE POINT, so no state filter on the ROW. A revoked writer is
    what a finished round leaves behind, and its row is returned with the state
    it actually has -- while the grant's own recorded result must still say the
    `active` it returned, which is a statement about the act rather than about
    the row. Absence is absence: an attempt nobody granted, or another
    generation of one that was, answers `None` rather than refusing.

    OWNERSHIP IS ESTABLISHED HERE AND NOT ASSUMED FROM `writer_of`. That reader
    owns the row's SHAPE; what it does not do is bind the row to the committed
    grant that fixed it. So the act is read whole -- signature, closed operands
    and its own recorded result -- its identity is re-derived from the operands
    that minted it, every immutable member is compared, and the two facts the
    act took from their own owners are checked against those owners: the line's
    profile and the attempt's fixed assignment. A row and an act that disagree
    refuse rather than being reconciled.

    IT READS AND DOES NOTHING ELSE. No insert, no update, no transaction, no
    profile call, no line revalidation, no port and no adapter.
    """
    attempt_id, generation = _requested_pair(attempt_id, generation)
    what = (f"the line writer for attempt {name_value(attempt_id)} "
            f"generation {generation}")
    writer = _one_by_attempt(store, "line_writers", schema.LINE_WRITER_COLUMNS,
                             attempt_id, generation, what)
    if writer is None:
        return None
    # THE SELECTED ROW MUST BE THE REQUESTED PAIR'S. The query says so, and
    # saying it again costs nothing next to answering somebody else's writer.
    if writer["runtime_attempt_id"] != attempt_id \
            or writer["assignment_generation"] != generation:
        raise ContractRefusal(
            "integrity", "schema",
            f"{what} selected a row for attempt "
            f"{name_value(writer['runtime_attempt_id'])} generation "
            f"{writer['assignment_generation']}")
    held = writer_of(store, writer["writer_id"])
    if held != writer:
        raise ContractRefusal(
            "integrity", "schema",
            f"{what} reads differently through its own identity than through "
            f"its attempt")
    line = line_of(store, writer["line_id"])
    operands, result = _committed_history(
        store, GRANT_KIND, GRANT_KIND + ":" + writer["writer_id"], what,
        _GRANT_OPERANDS, _GRANT_RESULT, _ACT_RETURNS)
    _derived_identity("writer", operands,
                      (("line_id", "line_id"), ("attempt_id", "attempt_id"),
                       ("generation", "generation")),
                      writer["writer_id"], what)
    # EVERY MEMBER THE ACT FIXED. `.get` is a read rather than a guess now:
    # `_committed_history` has already proved each of these members present.
    _bound_to_act(operands, {
        "writer_id": ("writer_id", writer["writer_id"]),
        "line_id": ("line_id", writer["line_id"]),
        "runtime_attempt_id": ("attempt_id", attempt_id),
        "assignment_generation": ("generation", generation),
        "worker_id": ("worker_id", writer["worker_id"]),
        "participant": ("participant", writer["participant"]),
        "principal": ("principal", writer["principal"]),
        # THE BASE THIS ROUND WAS BUILT ON, which is the member the consumer
        # came for: a correction writer names the checkpoint it corrected, and
        # a first writer names none. A changed base refuses here rather than
        # being handed out as the operand a later grant would replay under.
        "based_checkpoint_id": ("based_checkpoint_id",
                                writer["based_checkpoint_id"]),
    }, what, GRANT_KIND)
    # AND THE RESULT THE ACT ITSELF RECORDED, on the members that name THIS
    # row. Its `state` is owned one layer up, against the value the grant
    # returns rather than against the row: review [P1] is right that the two
    # were confused here. The row may be `revoked` and the result must still
    # say `active`, because they describe different moments -- proving the
    # second costs the first nothing.
    _bound_to_act(result, {
        "writer_id": ("writer_id", writer["writer_id"]),
        "line_id": ("line_id", writer["line_id"]),
        "assignment_generation": ("generation", generation),
    }, f"{what}'s recorded result", GRANT_KIND)
    if operands["profile_name"] != line["profile_name"]:
        raise ContractRefusal(
            "integrity", "schema",
            f"{what} was granted under profile "
            f"{name_value(operands['profile_name'])} and its line is kept "
            f"under {name_value(line['profile_name'])}")
    _assignment_agrees(store, attempt_id, line,
                       {"participant": writer["participant"],
                        "principal": writer["principal"],
                        "generation": generation}, what, GRANT_KIND)
    return writer


def review_for_attempt(store, *, attempt_id, generation):
    """The review attachment this attempt was given, whatever became of it.

    W124331, and the writer reader's twin. `review_of` binds an attachment to
    the act that attached it and to its checkpoint's line, and that is reused
    rather than repeated; what this adds is finding it from the attempt and
    generation rather than from an identity the consumer no longer holds, and
    the committed-history ownership `review_of` does not carry.

    WHY IT DOES NOT SIMPLY DELEGATE. Review [P1] measured the difference: a
    journalled boolean generation, a damaged signature and a foreign recorded
    result all passed straight through the inherited binding -- ordinary
    equality accepts `true` against generation one, and `review_of` never reads
    the act's result at all. So the strict read runs FIRST, before the
    inherited one, and the inherited binding is then taken on a record already
    proved readable.

    AN ENDED ATTACHMENT IS ORDINARY HISTORY. A recorded verdict ends it and a
    correction round then advances the line; the row is returned with the state
    it has. Absence stays absence, and this repeats none of `attach_review`'s
    current eligibility, independence or profile admission -- those decide
    whether a review MAY be attached, which is a different question from which
    one was.
    """
    attempt_id, generation = _requested_pair(attempt_id, generation)
    what = (f"the review attachment for attempt {name_value(attempt_id)} "
            f"generation {generation}")
    attachment = _one_by_attempt(store, "review_attachments",
                                 schema.REVIEW_ATTACHMENT_COLUMNS,
                                 attempt_id, generation, what)
    if attachment is None:
        return None
    if attachment["runtime_attempt_id"] != attempt_id \
            or attachment["assignment_generation"] != generation:
        raise ContractRefusal(
            "integrity", "schema",
            f"{what} selected a row for attempt "
            f"{name_value(attachment['runtime_attempt_id'])} generation "
            f"{attachment['assignment_generation']}")
    operands, result = _committed_history(
        store, ATTACH_KIND, ATTACH_KIND + ":" + attachment["attachment_id"],
        what, _ATTACH_OPERANDS, _ATTACH_RESULT, _ACT_RETURNS)
    _derived_identity("review", operands,
                      (("checkpoint_id", "checkpoint_id"),
                       ("attempt_id", "attempt_id"),
                       ("generation", "generation")),
                      attachment["attachment_id"], what)
    _bound_to_act(result, {
        "attachment_id": ("attachment_id", attachment["attachment_id"]),
        "checkpoint_id": ("checkpoint_id", attachment["checkpoint_id"]),
    }, f"{what}'s recorded result", ATTACH_KIND)
    _assignment_agrees(store, attempt_id,
                       line_of(store, attachment["line_id"]),
                       {"participant": attachment["reviewer_participant"],
                        "principal": attachment["reviewer_principal"],
                        "generation": generation}, what, ATTACH_KIND)
    # AND THE BINDING `review_of` ALREADY OWNS, on a record now proved
    # readable. Repeating it here would be a second account of one decision.
    held = review_of(store, attachment["attachment_id"])
    if held != attachment:
        raise ContractRefusal(
            "integrity", "schema",
            f"{what} reads differently through its own identity than through "
            f"its attempt")
    return held


def verdict_of(store, verdict_id):
    """One recorded checkpoint verdict, bound to the act that recorded it.

    W103076. A CONSUMER MAY BE HANDED A VERDICT IDENTITY AND MUST NOT BELIEVE
    IT. `record_verdict` journals the exact operands it bound -- verdict,
    attachment, line, checkpoint, Authority, Work, disposition and the sealed
    evidence -- so this reads the materialized row and proves every member of
    it against that committed act before answering.

    THE JOURNAL IS REACHED THROUGH THE ATTACHMENT, because that is the identity
    the act was named by. A verdict row whose attachment names a different
    verdict, or whose disposition or bindings differ from what was committed,
    refuses: two accounts of one decision have no tie-break and this module
    does not invent one.
    """
    verdict = _verdict_row(store, verdict_id)
    if verdict is None:
        raise ContractRefusal(
            "refused", "precondition",
            f"no checkpoint verdict {name_value(verdict_id)}")
    what = f"checkpoint verdict {name_value(verdict_id)}"
    operands = _committed_operands(
        store, VERDICT_KIND, VERDICT_KIND + ":" + verdict["attachment_id"],
        what)
    # THE RETAINED EVIDENCE, PARSED THROUGH ITS OWN OWNERS. Second re-review
    # [P0]: the row's `review_result_digest` was rewritten to another
    # well-formed digest and answered, so a correction could be scheduled on a
    # verdict whose retained evidence contradicted its act.
    verdict["review_result"] = _review_result(
        json.loads(verdict["review_result"]))
    verdict["review_fence"] = _fence(json.loads(verdict["review_fence"]),
                                     "a persisted review fence")
    if verdict["review_result_digest"] != digest(verdict["review_result"]) \
            or verdict["review_fence_digest"] != digest(verdict["review_fence"]):
        raise ContractRefusal(
            "integrity", "digest",
            f"{what} does not match the digests of the evidence it retains")
    _bound_to_act(operands, {
        "verdict_id": ("verdict_id", verdict["verdict_id"]),
        "attachment_id": ("attachment_id", verdict["attachment_id"]),
        "line_id": ("line_id", verdict["line_id"]),
        "checkpoint_id": ("checkpoint_id", verdict["checkpoint_id"]),
        "authority_uuid": ("authority_uuid", verdict["authority_uuid"]),
        "work_id": ("work_id", verdict["work_id"]),
        "disposition": ("disposition", verdict["disposition"]),
        "checkpoint_digest": ("checkpoint_digest",
                              verdict["checkpoint_digest"]),
        "revision": ("revision", verdict["revision"]),
        # THE REVIEWER'S OWN IDENTITY, which is the half of a verdict that
        # says WHO decided it and was entirely unbound.
        "review_assignment_generation": ("review_generation",
                                         verdict["review_assignment_generation"]),
        "reviewer_worker_id": ("reviewer_worker_id",
                               verdict["reviewer_worker_id"]),
        "reviewer_participant": ("reviewer_participant",
                                 verdict["reviewer_participant"]),
        "reviewer_principal": ("reviewer_principal",
                               verdict["reviewer_principal"]),
        # AND THE SEALED ACCOUNT OF WHAT WAS REVIEWED.
        "base_object": ("base", verdict["base_object"]),
        "head_object": ("head", verdict["head_object"]),
        "tree_object": ("tree", verdict["tree_object"]),
        "path_set_digest": ("path_set_digest", verdict["path_set_digest"]),
        "review_result": ("review_result", verdict["review_result"]),
        "review_result_digest": ("review_result_digest",
                                 verdict["review_result_digest"]),
        "review_fence": ("review_fence", verdict["review_fence"]),
        "review_fence_digest": ("review_fence_digest",
                                verdict["review_fence_digest"]),
    }, what, VERDICT_KIND)
    return verdict


def _attachment_row(store, attachment_id):
    row = store._connection.execute(
        "SELECT * FROM review_attachments WHERE attachment_id = ?",
        (attachment_id,)).fetchone()
    if row is None:
        raise ContractRefusal("refused", "precondition",
                              f"no review attachment {name_value(attachment_id)}")
    return boundaries.row(row, "a persisted review attachment",
                          schema.REVIEW_ATTACHMENT_COLUMNS)


def _attachment(store, attachment_id):
    boundaries.identity(attachment_id, "a review attachment identity")
    return _attachment_row(store, attachment_id)


def _same_assignment(assignment, line, generation):
    boundaries.generation(generation, "an assignment generation")
    if (assignment["authority_uuid"] != line["authority_uuid"]
            or assignment["work_id"] != line["work_id"]
            or assignment["generation"] != generation):
        raise ContractRefusal(
            "stale-assignment", "generation",
            "the runtime attempt is not the named generation of this line's "
            "Authority and Work")


def _within(child, parent):
    try:
        return os.path.commonpath((child, parent)) == parent
    except ValueError:
        return False


def _line_place(storage, line_id, source):
    boundaries.text(storage, "the manager's workspace storage")
    if not os.path.isabs(storage) or os.path.realpath(storage) != storage:
        raise ContractRefusal("integrity", "path",
                              "review-line storage is one canonical absolute path")
    root = os.path.join(storage, LINE_HOME)
    home = os.path.join(root, line_id)
    path = os.path.join(home, "checkout")
    if source == path or _within(source, path) or _within(path, source):
        raise ContractRefusal(
            "policy", "denied",
            "the nominated source and persistent development line contain one another")
    for place in (root, home):
        try:
            os.mkdir(place, 0o700)
        except FileExistsError:
            if os.path.islink(place) or not os.path.isdir(place) \
                    or os.path.realpath(place) != place:
                raise ContractRefusal(
                    "integrity", "path",
                    f"review-line custody {name_value(place)} is not its own directory")
    return path


def _object(place, what):
    if os.path.islink(place) or not os.path.isdir(place) \
            or os.path.realpath(place) != place:
        raise ContractRefusal("integrity", "path",
                              f"{what} is no longer its own directory")
    held = os.stat(place, follow_symlinks=False)
    return held.st_dev, held.st_ino


def _consumable_line(store, line_id):
    """The line row as it is NOW, with its recorded object proved again.

    One function because the two halves are one question: a pathname is only
    evidence while the object it names is the object the lifecycle recorded,
    and a row read before an external call is a memory rather than a fact.
    """
    line = line_of(store, line_id)
    _validate_line_object(line)
    return line


def _validate_line_object(line):
    held = _object(line["line_path"], "the durable development line")
    if held != (line["line_device"], line["line_inode"]):
        raise ContractRefusal(
            "runtime-observation", "identity-mismatch",
            "the durable development line pathname now names another object")


# The three recorded members that name WHICH object a line row is about. They
# are written once by `review-line.create` and never updated afterwards, so a
# proof taken over them outside a transaction can be bound to the row inside one
# by comparison alone.
_LINE_OBJECT = ("line_path", "line_device", "line_inode")


def _line_object(line):
    return tuple(line[member] for member in _LINE_OBJECT)


def _proved_line_object(store, line):
    """Prove this line's object and access BEFORE any write lock is taken.

    W257624, owner ruling 2026-09-26T01:04:01Z reaffirming the 2026-09-25
    short-transactions ruling: never hold a database lock while performing I/O
    other than the database's own, and a read-only filesystem check is I/O --
    `stat`, path validation and access validation included. `grant_writer` was
    doing exactly that: `_validate_line_object` and `_prove_line_access` both ran
    inside `ControlStore.transact`, and the second reaches
    `check_workspace_group`'s `os.getgroups()` as well.

    SO THE PROOF MOVES OUT AND A PIN COMES BACK. What is returned is the exact
    recorded object triple the proofs were taken over, and the caller compares it
    against the row again under the lock. That comparison is pure SQL, so the
    admission still refuses a row that does not name the object this proof was
    about, and no filesystem call is left in the callback.

    WHY THE WINDOW THIS OPENS IS NOT WHERE THE GUARANTEE LIVED. An admission has
    never held a filesystem lock, so neither the old placement nor this one
    survives a `chgrp` or a rename committed a moment later -- and the act that
    must not proceed on a stale proof is the LAUNCH, not the grant.
    `writer_boundary` composes its roots through `workspaces._granted_roots` with
    a `line_proof`, and `_writer_access` re-runs BOTH of these proofs against the
    current writer grant before any container is given the line. This is an
    admission check; the launch keeps its own.

    AND TWO THINGS PINNED HERE CANNOT DRIFT UNDER THE LOCK. The recorded triple
    is immutable after creation, per `_LINE_OBJECT`. The configured workspace
    group cannot change on a live store either: `configure_workspace_group`
    refuses a different group outright -- "a changed group is a fresh store
    rather than a reconfiguration" -- so a gid proved here is the gid the store
    will still name.
    """
    _validate_line_object(line)
    pinned = (line["line_device"], line["line_inode"])
    workspaces._prove_line_access(
        line["line_path"], pinned,
        workspaces.configured_workspace_group(store).gid)
    return _line_object(line)


def _proved_restoration_object(store, line, what):
    """Prove the line object this restoration is about to write, and PIN it.

    W257624, owner ruling 2026-09-26T01:35:02Z. The completing transaction used to
    call `_validate_line_object` under the write lock; the proof now happens here,
    outside every transaction and immediately before the profile writes, and the
    completion compares this pin in pure SQL.

    THE SAME PATTERN THE `grant_writer` CORRECTION ESTABLISHED, for the same
    reason: the recorded triple is written once at line creation and never
    updated, so a comparison inside the lock is a fail-closed binding rather than
    an ordinary transition. What it refuses is a completion whose row no longer
    describes the object the checkout was actually restored in.
    """
    _validate_line_object(line)
    return _line_object(line)


def _storage(store):
    return workspaces.configured_workspace_storage(store).place


def _attempt(store, attempt_id):
    return attempts._require_attempt(store, attempt_id)


def _quiescent_completed(store, attempt_id, *, review=False):
    attempt = _attempt(store, attempt_id)
    if attempt["runtime_id"] is None or attempt["execution_runtime"] != "quiescent":
        raise ContractRefusal(
            "refused", "precondition",
            "review completion requires the exact attached runtime to be "
            "positively quiescent" if review else
            "checkpoint completion requires the exact attached runtime to be "
            "positively quiescent")
    required = "completed" if review else None
    if (required is not None and attempt["worker_disposition"] != required) \
            or (required is None and attempt["worker_disposition"] == "none"):
        raise ContractRefusal(
            "refused", "precondition",
            "review completion requires a completed worker disposition" if review else
            "checkpoint completion requires a terminal worker disposition")
    return attempt


def _fence(value, what):
    taken = boundaries.document(value, "a persisted assignment fence",
                                required=("intent", "fenced"))
    return taken


def _committed_fence(store, fence, what):
    held = _fence(fence, what)
    intent = attempts.adopt_finalization_record(held["intent"])
    operation_id = "attempt.finalize-quiescent:" + digest({
        "attempt_id": intent["attempt_id"],
        "assignment": intent["assignment"],
    }).split(":", 1)[1]
    signature = manager_signature("attempt.finalize-quiescent", {
        "attempt_id": intent["attempt_id"], "expect": intent["assignment"],
        "runtime_id": intent["runtime_id"],
        "worker_disposition": intent["worker_disposition"],
        "authority_operation_id": intent["authority_operation_id"],
        "reason": intent["reason"]})
    found, record = store.replay(operation_id, signature,
                                 kind="attempt.finalize-quiescent")
    if not found or record != intent:
        raise ContractRefusal("integrity", "schema",
                              f"{what} has no exact committed manager decision")
    return held, intent


def _current_fence(store, attempt, fence, what):
    held, intent = _committed_fence(store, fence, what)
    assignment = intent["assignment"]
    current = {"participant": attempt["assignment_participant"],
               "generation": attempt["assignment_generation"],
               "work_ref": {"work_id": attempt["work_id"],
                            "authority_uuid": attempt["authority_uuid"]}}
    if intent["attempt_id"] != attempt["runtime_attempt_id"] \
            or intent["runtime_id"] != attempt["runtime_id"] \
            or intent["worker_disposition"] != attempt["worker_disposition"] \
            or assignment != current:
        raise ContractRefusal("integrity", "schema",
                              f"{what} is not the current attempt's committed fence")
    return held


def _review_result(value):
    taken = boundaries.document(
        value, "a frozen review result",
        required=("attempt_id", "result_id", "disposition", "manifest_digest",
                  "freeze_operation_id", "frozen_at", "artifacts"))
    for member in ("attempt_id", "result_id", "manifest_digest",
                   "freeze_operation_id"):
        boundaries.identity(taken[member], f"a frozen review result's {member}")
    boundaries.instant(taken["frozen_at"], "a frozen review result's frozen_at")
    if taken["disposition"] != "completed":
        raise ContractRefusal("refused", "precondition",
                              "a review verdict requires a completed frozen result")
    if type(taken["artifacts"]) is not list:
        raise ContractRefusal("integrity", "schema",
                              "a frozen review result's artifacts is a list")
    names = []
    for artifact in taken["artifacts"]:
        held = boundaries.document(
            artifact, "a frozen review artifact",
            required=("output_name", "artifact_id", "media_type", "bytes",
                      "content_digest", "locator"))
        boundaries.identity(held["output_name"], "a frozen review output name")
        names.append(held["output_name"])
    if not {"findings", "logs"}.issubset(names):
        raise ContractRefusal(
            "refused", "precondition",
            "a review verdict requires separately frozen findings and logs outputs")
    return taken


def create_line(store, *, source, declared_base, profile,
                authority_uuid, work_id):
    """Create or recover the one persistent line for Authority and Work."""
    boundaries.text(authority_uuid, "a line's authority UUID")
    boundaries.identity(work_id, "a line's Work identity")
    boundaries.text(declared_base, "a line's declared base")
    storage = _storage(store)
    profile_name = _profile(profile, ("materialize", "validate"))
    if type(source) is not source_boundary.NominatedSource:
        raise ContractRefusal("integrity", "schema",
                              "a line source is a manager-nominated source")
    manager_signature("review-line.create.prepare", {
        "storage": storage, "source_path": source.place,
        "source_device": source.device, "source_inode": source.inode,
        "declared_base": declared_base, "profile_name": profile_name,
        "authority_uuid": authority_uuid, "work_id": work_id})
    line_id = _id("line", {"authority_uuid": authority_uuid,
                           "work_id": work_id})
    path = _line_place(storage, line_id, source.place)
    expected = (profile_name, declared_base, source.place, source.device,
                source.inode, path)
    connection = store._connection
    connection.execute("BEGIN IMMEDIATE")
    try:
        existing = connection.execute(
            "SELECT * FROM review_lines WHERE line_id = ?", (line_id,)).fetchone()
        if existing is None:
            connection.execute(
                "INSERT INTO review_lines (line_id, authority_uuid, work_id, "
                "profile_name, declared_base, source_path, source_device, "
                "source_inode, line_path, line_device, line_inode, state, "
                "revision, current_checkpoint_id, created_at) VALUES (?, ?, ?, "
                "?, ?, ?, ?, ?, ?, NULL, NULL, 'materializing', 0, NULL, ?)",
                (line_id, authority_uuid, work_id, profile_name, declared_base,
                 source.place, source.device, source.inode, path, store._now()))
        connection.execute("COMMIT")
    except BaseException:
        try:
            connection.execute("ROLLBACK")
        except Exception:
            pass
        raise
    held = line_of(store, line_id)
    recorded = (held["profile_name"], held["declared_base"],
                held["source_path"], held["source_device"],
                held["source_inode"], held["line_path"])
    if recorded != expected:
        raise ContractRefusal(
            "refused", "operation-collision",
            "this Authority and Work already own a line under different immutable operands")
    if held["state"] != "materializing":
        operands = {member: held[member] for member in (
            "line_id", "authority_uuid", "work_id", "profile_name",
            "declared_base", "source_path", "source_device", "source_inode",
            "line_path", "line_device", "line_inode")}
        signature = manager_signature("review-line.create", operands)
        found, result = store.replay("review-line.create:" + line_id,
                                     signature, kind="review-line.create")
        if found:
            _validate_line_object(held)
            return result
        raise ContractRefusal("integrity", "schema",
                              "a materialized line has no committed creation operation")
    materialized = profile.materialize(source.place, path, declared_base)
    if type(materialized) is not dict or set(materialized) != {
            "profile", "base", "head"} or materialized["profile"] != profile_name \
            or materialized["base"] != declared_base:
        raise ContractRefusal("integrity", "schema",
                              "line materialization returned malformed evidence")
    boundaries.text(materialized["head"], "a materialized line head")
    device, inode = _object(path, "the materialized development line")
    operands = {"line_id": line_id, "authority_uuid": authority_uuid,
                "work_id": work_id, "profile_name": profile_name,
                "declared_base": declared_base, "source_path": source.place,
                "source_device": source.device, "source_inode": source.inode,
                "line_path": path, "line_device": device, "line_inode": inode}
    signature = manager_signature("review-line.create", operands)

    def act(connection):
        current = line_of(store, line_id)
        if current["state"] != "materializing":
            raise ContractRefusal("integrity", "schema",
                                  "line materialization changed state before completion")
        if _object(path, "the materialized development line") != (device, inode):
            raise ContractRefusal("runtime-observation", "identity-mismatch",
                                  "the materialized development line changed before publication")
        # W194457: PROVE, then ESTABLISH -- and the two are different costs.
        # `prove_line_integrity` keeps every constraint the removed
        # whole-tree provisioning pass also enforced (special files,
        # hardlinks, the entry/byte/depth ceilings, and that the tree belongs
        # to this deployment's execution identity) and is bounded by DEPTH
        # rather than by entry count. `establish_line_access` then does the
        # permission work, which under a shared execution identity is the
        # ROOT's group and mode and nothing else -- two acts, whatever the
        # checkout holds.
        identity = workspaces.configured_workspace_identity(store)
        workspaces.prove_line_integrity(path, (device, inode), identity)
        workspaces.establish_line_access(path, (device, inode), identity)
        connection.execute(
            "UPDATE review_lines SET line_device = ?, line_inode = ?, "
            "state = 'idle' WHERE line_id = ? AND state = 'materializing'",
            (device, inode, line_id))
        return {"line_id": line_id, "state": "idle", "revision": 0,
                "path": path}

    result = store.transact("review-line.create:" + line_id,
                            "review-line.create", signature, act)
    _validate_line_object(line_of(store, line_id))
    return result


def grant_writer(store, *, line_id, attempt_id, generation, worker_id, profile,
                 based_checkpoint_id=None):
    """Attach exactly one generation-fenced writer to the durable line."""
    profile_name = _profile(profile, ("validate",))
    boundaries.identity(worker_id, "a writer worker identity")
    if based_checkpoint_id is not None:
        boundaries.identity(based_checkpoint_id, "a based checkpoint identity")
    line = line_of(store, line_id)
    if line["state"] == "materializing":
        raise ContractRefusal("refused", "precondition",
                              "the development line is still materializing")
    assignment = assignment_of(store, attempt_id)
    _same_assignment(assignment, line, generation)
    _validate_line_object(line)
    if line["profile_name"] != profile_name:
        raise ContractRefusal("policy", "profile-uncertified",
                              "the line and writer profile do not match")
    writer_id = _id("writer", {"line_id": line_id, "attempt_id": attempt_id,
                               "generation": generation})
    operands = {"writer_id": writer_id, "line_id": line_id,
                "attempt_id": attempt_id, "generation": generation,
                "worker_id": worker_id, "profile_name": profile_name,
                "participant": assignment["participant"],
                "principal": assignment["principal"],
                "based_checkpoint_id": based_checkpoint_id}
    signature = manager_signature("review-line.grant-writer", operands)
    operation_id = "review-line.grant-writer:" + writer_id
    found, result = store.replay(operation_id, signature,
                                 kind="review-line.grant-writer")
    if found:
        return result
    if line["state"] == "idle":
        if based_checkpoint_id is not None:
            raise ContractRefusal("refused", "precondition",
                                  "the first writer is not based on a checkpoint")
    elif line["state"] == "correction-ready":
        if based_checkpoint_id != line["current_checkpoint_id"]:
            raise ContractRefusal("stale-assignment", "generation",
                                  "a correction writer must name the current checkpoint")
        checkpoint = checkpoint_of(store, based_checkpoint_id)
        if checkpoint["line_id"] != line_id or checkpoint["state"] != "frozen":
            raise ContractRefusal("integrity", "schema",
                                  "a correction checkpoint is not this line's frozen checkpoint")
        profile.validate(line["line_path"], checkpoint["evidence"], current=True)
    else:
        raise ContractRefusal("refused", "precondition",
                              f"line state {line['state']!r} does not admit a writer")
    # THE RELOCATED PROOF, OUTSIDE THE TRANSACTION -- and after the replay above,
    # so a grant that already committed does not repeat it. `act` below compares
    # this pin and touches no file.
    #
    # NOT "every filesystem proof this admission makes", which is what this
    # comment claimed until review 2026-09-26T01:23:34Z corrected it: the
    # `_validate_line_object(line)` above runs FIRST on every call including a
    # replay, and this correction neither moved it nor has a mandate to. What a
    # replay skips is this access proof alone.
    proved = _proved_line_object(store, line)

    def act(connection):
        current = line_of(store, line_id)
        if current["state"] not in ("idle", "correction-ready"):
            raise ContractRefusal("refused", "precondition",
                                  "the line acquired another active attachment")
        current_assignment = assignment_of(store, attempt_id)
        _same_assignment(current_assignment, current, generation)
        if (current_assignment != assignment
                or current["state"] != line["state"]
                or current["current_checkpoint_id"] != line["current_checkpoint_id"]):
            raise ContractRefusal("stale-assignment", "generation",
                                  "writer admission changed after its checkpoint validation")
        # THE PIN, COMPARED RATHER THAN RE-MEASURED. `_proved_line_object` proved
        # the object and its access outside this lock; this binds the row being
        # written to the row those proofs were taken over, in pure SQL. The
        # triple is immutable after line creation, so what this refuses is a row
        # that was changed out of band rather than an ordinary transition -- and
        # an admission that could not tell those apart would be carrying a proof
        # about one object into a grant for another.
        if _line_object(current) != proved:
            raise ContractRefusal(
                "runtime-observation", "identity-mismatch",
                "the development line row no longer names the object this "
                "writer admission proved")
        now = store._now()
        connection.execute(
            "INSERT INTO line_writers (writer_id, line_id, runtime_attempt_id, "
            "assignment_generation, worker_id, participant, principal, "
            "based_checkpoint_id, state, granted_at) VALUES (?, ?, ?, ?, ?, ?, "
            "?, ?, 'active', ?)",
            (writer_id, line_id, attempt_id, generation, worker_id,
             assignment["participant"], assignment["principal"],
             based_checkpoint_id, now))
        connection.execute("UPDATE review_lines SET state = 'writing' "
                           "WHERE line_id = ?", (line_id,))
        return {"writer_id": writer_id, "line_id": line_id,
                "generation": generation, "state": "active"}

    return store.transact(operation_id,
                          "review-line.grant-writer", signature, act)


def record_progress(store, *, writer_id, generation, sequence, document):
    boundaries.generation(generation, "a progress assignment generation")
    boundaries.generation(sequence, "a progress sequence")
    body = canonical_text(document)
    writer = writer_of(store, writer_id)
    if writer["assignment_generation"] != generation:
        raise ContractRefusal("stale-assignment", "generation",
                              "progress belongs to the active writer generation")
    operands = {"writer_id": writer_id, "generation": generation,
                "sequence": sequence, "document": document}
    signature = manager_signature("review-line.progress", operands)
    operation_id = f"review-line.progress:{writer_id}:{sequence}"
    found, result = store.replay(operation_id, signature,
                                 kind="review-line.progress")
    if found:
        return result

    def act(connection):
        if writer_of(store, writer_id)["state"] != "active":
            raise ContractRefusal("stale-assignment", "generation",
                                  "the writer was revoked before progress arrived")
        connection.execute(
            "INSERT INTO line_progress (writer_id, sequence, "
            "assignment_generation, progress_digest, document, recorded_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (writer_id, sequence, generation, digest(document), body,
             store._now()))
        return {"writer_id": writer_id, "sequence": sequence,
                "progress_digest": digest(document)}

    return store.transact(operation_id,
                          "review-line.progress", signature, act)


def freeze_checkpoint(store, *, writer_id, generation, profile, port):
    """Revoke and authority-fence the quiescent writer before freezing."""
    profile_name = _profile(profile, ("freeze", "validate"))
    boundaries.generation(generation, "a checkpoint assignment generation")
    writer = writer_of(store, writer_id)
    line = line_of(store, writer["line_id"])
    if line["profile_name"] != profile_name:
        raise ContractRefusal("policy", "profile-uncertified",
                              "the line and checkpoint profile do not match")
    if writer["assignment_generation"] != generation:
        raise ContractRefusal("stale-assignment", "generation",
                              "checkpoint completion names a stale writer generation")
    existing = store._connection.execute(
        "SELECT checkpoint_id FROM line_checkpoints WHERE writer_id = ?",
        (writer_id,)
    ).fetchone()
    if existing is None:
        revision = line["revision"] + 1
        checkpoint_id = _id("checkpoint", {"line_id": line["line_id"],
                                           "revision": revision})
    else:
        existing_id = boundaries.identity(
            existing["checkpoint_id"], "a persisted line checkpoint identity")
        held = checkpoint_of(store, existing_id)
        revision = held["revision"]
        checkpoint_id = held["checkpoint_id"]
        if held["state"] == "frozen":
            evidence = held["evidence"]
            operands = {"writer_id": writer_id, "generation": generation,
                        "checkpoint_id": checkpoint_id, "evidence": evidence,
                        "fence": held["fence"]}
            signature = manager_signature("review-line.freeze", operands)
            found, result = store.replay("review-line.freeze:" + checkpoint_id,
                                         signature, kind="review-line.freeze")
            if found:
                return result
    attempt = _quiescent_completed(store, writer["runtime_attempt_id"])
    if attempt["assignment_participant"] != getattr(port, "participant", None):
        raise ContractRefusal("refused", "capability",
                              "the writer fence session acts for another participant")
    connection = store._connection
    connection.execute("BEGIN IMMEDIATE")
    try:
        current = writer_of(store, writer_id)
        found = connection.execute(
            "SELECT * FROM line_checkpoints WHERE checkpoint_id = ?",
            (checkpoint_id,)).fetchone()
        if found is None:
            if current["state"] != "active":
                raise ContractRefusal("refused", "precondition",
                                      "checkpoint preparation has no active writer")
            _quiescent_completed(store, current["runtime_attempt_id"])
            now = store._now()
            connection.execute(
                "UPDATE line_writers SET state = 'revoked', revoked_at = ?, "
                "revocation_reason = 'checkpoint' WHERE writer_id = ? "
                "AND state = 'active'", (now, writer_id))
            connection.execute(
                "INSERT INTO line_checkpoints (checkpoint_id, writer_id, line_id, revision, "
                "profile_name, state, path_set_digest, prepared_at) VALUES (?, ?, "
                "?, ?, ?, 'preparing', NULL, ?)",
                (checkpoint_id, writer_id, line["line_id"], revision,
                 profile_name, now))
            connection.execute("UPDATE review_lines SET state = 'freezing' "
                               "WHERE line_id = ?", (line["line_id"],))
        connection.execute("COMMIT")
    except BaseException:
        try:
            connection.execute("ROLLBACK")
        except Exception:
            pass
        raise
    checkpoint = checkpoint_of(store, checkpoint_id)
    if checkpoint["fence"] is None:
        fenced = _fence(attempts.finalize_quiescent_assignment(
            store, port, attempt_id=writer["runtime_attempt_id"],
            reason="review checkpoint writer completed"),
            "the checkpoint writer fence")
        fence_operands = {"checkpoint_id": checkpoint_id,
                          "writer_id": writer_id, "fence": fenced}
        fence_signature = manager_signature("review-line.fence-writer",
                                            fence_operands)

        def record_fence(connection):
            current = checkpoint_of(store, checkpoint_id)
            if current["state"] != "preparing" or current["fence"] is not None:
                raise ContractRefusal("integrity", "schema",
                                      "a checkpoint writer fence changed before recording")
            connection.execute(
                "UPDATE line_checkpoints SET fence = ?, fence_digest = ? "
                "WHERE checkpoint_id = ? AND state = 'preparing' AND fence IS NULL",
                (canonical_text(fenced), digest(fenced), checkpoint_id))
            return fenced

        store.transact("review-line.fence-writer:" + checkpoint_id,
                       "review-line.fence-writer", fence_signature,
                       record_fence)
        checkpoint = checkpoint_of(store, checkpoint_id)
    fenced = checkpoint["fence"]
    # THE PIN IS RE-PROVED HERE, AT THE CONSUMING BOUNDARY. W105982 candidate
    # review 2026-09-07 kept the reproduction: the early adapter gate runs
    # before sealing, retention, publication and an EXTERNAL Authority fence,
    # and a checkout directory replaced during that fence call reached
    # `profile.freeze` and was frozen as this line's checkpoint. Re-resolving
    # after the early walk cannot protect a read this far downstream, so the
    # object is proved again against the durable row immediately before the
    # profile is handed the path.
    #
    # THE ROW IS RE-READ RATHER THAN REUSED, because `line` was loaded before
    # the fence and a stale copy proves only that it once agreed with itself.
    # NO WRITER IS REQUIRED TO STILL BE ACTIVE: this runs after the checkpoint
    # legitimately revoked it, so the question asked here is about the LINE'S
    # object identity and nothing else -- which is also what keeps the
    # preparing/frozen replay paths working exactly as they did.
    line = _consumable_line(store, line["line_id"])
    evidence = profile.freeze(line["line_path"], line_id=line["line_id"],
                              revision=revision,
                              declared_base=line["declared_base"])
    required = {"profile", "base", "head", "tree", "paths",
                "path_set_digest", "reference"}
    if type(evidence) is not dict or set(evidence) != required \
            or evidence["profile"] != profile_name:
        raise ContractRefusal("integrity", "schema",
                              "checkpoint profile returned malformed evidence")
    evidence = _evidence(evidence)
    if evidence["base"] != line["declared_base"]:
        raise ContractRefusal("integrity", "digest",
                              "checkpoint evidence does not use the line's declared base")
    profile.validate(line["line_path"], evidence, current=True)
    checkpoint_digest = digest(evidence)
    operands = {"writer_id": writer_id, "generation": generation,
                "checkpoint_id": checkpoint_id, "evidence": evidence,
                "fence": fenced}
    signature = manager_signature("review-line.freeze", operands)

    def act(connection):
        checkpoint = checkpoint_of(store, checkpoint_id)
        if checkpoint["state"] == "preparing":
            now = store._now()
            connection.execute(
                "UPDATE line_checkpoints SET state = 'frozen', evidence = ?, "
                "checkpoint_digest = ?, base_object = ?, head_object = ?, "
                "tree_object = ?, path_set_digest = ?, reference_name = ?, "
                "frozen_at = ? WHERE checkpoint_id = ? AND state = 'preparing'",
                (canonical_text(evidence), checkpoint_digest, evidence["base"],
                 evidence["head"], evidence["tree"],
                 evidence["path_set_digest"], evidence["reference"], now,
                 checkpoint_id))
            connection.execute(
                "UPDATE review_lines SET state = 'review-ready', revision = ?, "
                "current_checkpoint_id = ? WHERE line_id = ?",
                (revision, checkpoint_id, line["line_id"]))
        return {"checkpoint_id": checkpoint_id, "line_id": line["line_id"],
                "revision": revision, "checkpoint_digest": checkpoint_digest,
                "evidence": evidence, "fence": fenced}

    return store.transact("review-line.freeze:" + checkpoint_id,
                          "review-line.freeze", signature, act)


def attach_review(store, *, checkpoint_id, attempt_id, generation,
                  reviewer_worker_id, profile):
    """Attach an independent reviewer to the exact current checkpoint."""
    profile_name = _profile(profile, ("validate",))
    boundaries.identity(reviewer_worker_id, "a reviewer worker identity")
    checkpoint = checkpoint_of(store, checkpoint_id)
    line = line_of(store, checkpoint["line_id"])
    if checkpoint["state"] != "frozen":
        raise ContractRefusal("integrity", "schema",
                              "a review attachment requires a frozen checkpoint")
    if line["profile_name"] != profile_name:
        raise ContractRefusal("policy", "profile-uncertified",
                              "the line and review profile do not match")
    assignment = assignment_of(store, attempt_id)
    _same_assignment(assignment, line, generation)
    producer = writer_of(store, checkpoint["writer_id"])
    if producer["line_id"] != line["line_id"]:
        raise ContractRefusal("integrity", "schema",
                              "a checkpoint writer belongs to another line")
    same = []
    if reviewer_worker_id == producer["worker_id"]:
        same.append("worker")
    if assignment["participant"] == producer["participant"]:
        same.append("participant")
    if assignment["principal"] == producer["principal"]:
        same.append("principal")
    if same:
        raise ContractRefusal("refused", "precondition",
                              "review is not independent at: " + ", ".join(same))
    attachment_id = _id("review", {"checkpoint_id": checkpoint_id,
                                   "attempt_id": attempt_id,
                                   "generation": generation})
    operands = {"attachment_id": attachment_id,
                "checkpoint_id": checkpoint_id, "attempt_id": attempt_id,
                "generation": generation, "reviewer_worker_id": reviewer_worker_id,
                "participant": assignment["participant"],
                "principal": assignment["principal"]}
    signature = manager_signature("review-line.attach-review", operands)
    operation_id = "review-line.attach-review:" + attachment_id
    found, result = store.replay(operation_id, signature,
                                 kind="review-line.attach-review")
    if found:
        return result
    if line["state"] != "review-ready" \
            or line["current_checkpoint_id"] != checkpoint_id:
        raise ContractRefusal("refused", "precondition",
                              "review attaches only to the current review-ready checkpoint")
    if store._connection.execute(
            "SELECT 1 FROM line_writers WHERE line_id = ? AND state = 'active'",
            (line["line_id"],)).fetchone() is not None:
        raise ContractRefusal("refused", "precondition",
                              "read-only review cannot coexist with a writer")
    profile.validate(line["line_path"], checkpoint["evidence"], current=True)

    def act(connection):
        current = line_of(store, line["line_id"])
        if current["state"] != "review-ready" \
                or current["current_checkpoint_id"] != checkpoint_id:
            raise ContractRefusal("refused", "precondition",
                                  "the checkpoint acquired another attachment")
        connection.execute(
            "INSERT INTO review_attachments (attachment_id, line_id, "
            "checkpoint_id, runtime_attempt_id, assignment_generation, "
            "reviewer_worker_id, reviewer_participant, reviewer_principal, "
            "state, attached_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'active', ?)",
            (attachment_id, line["line_id"], checkpoint_id, attempt_id,
             generation, reviewer_worker_id, assignment["participant"],
             assignment["principal"], store._now()))
        connection.execute("UPDATE review_lines SET state = 'reviewing' "
                           "WHERE line_id = ?", (line["line_id"],))
        return {"attachment_id": attachment_id, "checkpoint_id": checkpoint_id,
                "state": "active"}

    return store.transact(operation_id,
                          "review-line.attach-review", signature, act)


def _custodied_review(store, attempt, result):
    """A review whose output was TAKEN INTO CUSTODY, proved through its receipt.

    W110772, owner ruling M111752 and `FIRST-PROOF-PLAN.md`. The measured
    blocker: an ending that actually performs intake and retention leaves the
    output axis at `sealed`, and this precondition admitted only `frozen` -- so
    the very custody the lifecycle requires made the first verdict impossible.
    Two real proofs failed on it and nothing else was wrong with them.

    SEALED IS ADMITTED ONLY WITH THE RECEIPT THAT MADE IT SEALED, which is the
    whole difference between relaxing a check and moving it. `frozen` says the
    manager sealed the bytes; `sealed` says it also collected them, and the
    evidence for the second is the intake receipt, not the axis word. So the
    receipt is read from its owner and cross-bound to the exact frozen result:
    same attempt, same result id, same manifest digest, and every artifact the
    result declares present in it.

    AND THE RETENTION DECISIONS MUST EXIST. `authorize_cleanup` refuses without
    them and the whole point of admitting `sealed` is that this attempt went
    through custody; an attempt sealed with nothing retained is one whose
    material nobody decided about, which is not evidence a verdict may rest on.

    THIS IS NOT A TRANSITION. Nothing here moves `sealed` back to `frozen` or
    writes any axis; the axis is read and the receipt is what is believed.
    """
    manifest = manifests.load_manifest(store, result["manifest_digest"], "resultManifest")
    if manifest is None:
        raise ContractRefusal("refused", "precondition",
                              "the custodied review has no retained result manifest")
    assignment = {"participant": attempt["assignment_participant"],
                  "generation": attempt["assignment_generation"],
                  "work_ref": {"work_id": attempt["work_id"], "authority_uuid": attempt["authority_uuid"]}}
    artifacts = [dict(output_name=one["name"], **one["artifact"])
                 for one in manifest["outputs"] if one["artifact"] is not None]
    if manifest["result_id"] != result["result_id"] \
            or manifest["disposition"] != result["disposition"] \
            or manifest["assignment_ref"] != assignment \
            or manifest["input_manifest_digest"] != attempt["input_digest"] \
            or manifest["policy_digest"] != attempt["policy_digest"] \
            or manifest["freeze_operation"]["operation_id"] != result["freeze_operation_id"] \
            or sorted(artifacts, key=lambda one: one["output_name"]) != result["artifacts"]:
        raise ContractRefusal("integrity", "digest",
                              "the retained review manifest differs from its frozen result and assignment")
    receipt = intake.intake_receipt_of(store, attempt["runtime_attempt_id"])
    if receipt is None:
        raise ContractRefusal(
            "refused", "precondition",
            f"attempt {name_value(attempt['runtime_attempt_id'])} reports "
            f"sealed output and this manager holds no intake receipt for it; "
            f"the axis is a claim and the receipt is the evidence")
    if receipt["attempt_id"] != attempt["runtime_attempt_id"] \
            or receipt["result_id"] != result["result_id"] \
            or receipt["manifest_digest"] != result["manifest_digest"]:
        raise ContractRefusal(
            "integrity", "schema",
            "the intake receipt and the frozen review result name different "
            "results; a verdict rests on one account of one output")
    if receipt["custody"] != "accepted":
        raise ContractRefusal("refused", "precondition",
                              "a review verdict requires accepted intake custody")
    collected = {one["artifact_id"] for one in receipt["artifacts"]}
    declared = {one["artifact_id"] for one in result["artifacts"]}
    if not declared <= collected:
        raise ContractRefusal(
            "refused", "precondition",
            f"the frozen review result declares "
            f"{', '.join(sorted(name_value(one) for one in declared - collected))} "
            f"and the intake receipt collected neither; a verdict rests on "
            f"material this manager took custody of")
    measured = {(one["artifact_id"], one["bytes"], one["content_digest"])
                for one in result["artifacts"]}
    received = {(one["artifact_id"], one["bytes"], one["content_digest"])
                for one in receipt["artifacts"]}
    if measured != received or len(receipt["artifacts"]) != len(result["artifacts"]):
        raise ContractRefusal("integrity", "digest",
                              "review intake artifacts differ from the frozen measurements")
    retained = intake.retentions_of(store, attempt["runtime_attempt_id"])
    if {one["artifact_id"] for one in retained if one["disposition"] == "retain"} != declared:
        raise ContractRefusal(
            "refused", "precondition",
            "every frozen review artifact requires its retained decision")
    return receipt


def _cleaned_review(store, attachment, attempt, result, verdict):
    """Historical completion is exact committed evidence, never an axis alone."""
    proved = verdict_of(store, verdict["verdict_id"])
    operation_id = VERDICT_KIND + ":" + attachment["attachment_id"]
    if _committed_act(store, VERDICT_KIND, operation_id, "the historical verdict") \
            != _committed_operands(store, VERDICT_KIND, operation_id, "the historical verdict"):
        raise ContractRefusal("integrity", "schema",
                              "historical verdict answer differs from its committed operands")
    if proved != verdict or review_of(store, attachment["attachment_id"]) != attachment \
            or attachment["state"] != "ended" \
            or attempt["runtime_id"] is None \
            or attempt["worker_disposition"] != "completed" \
            or attempt["output"] != "sealed" \
            or attempt["cleanup"] != "retained" \
            or result != verdict["review_result"]:
        raise ContractRefusal("refused", "precondition",
                              "historical review completion requires its ended verdict and retained cleanup")
    for member in ("attachment_id", "line_id", "checkpoint_id", "reviewer_worker_id",
                   "reviewer_participant", "reviewer_principal"):
        if attachment[member] != verdict[member]:
            raise ContractRefusal("integrity", "schema",
                                  "historical review verdict belongs to another attachment")
    if attachment["assignment_generation"] != verdict["review_assignment_generation"] \
            or attempt["assignment_generation"] != verdict["review_assignment_generation"] \
            or attempt["assignment_participant"] != verdict["reviewer_participant"] \
            or attempt["assignment_principal"] != verdict["reviewer_principal"]:
        raise ContractRefusal("integrity", "schema",
                              "historical review verdict belongs to another assignment")
    fence = _current_fence(store, attempt, verdict["review_fence"],
                           "the historical review fence")
    receipt = _custodied_review(store, attempt, result)
    retained = intake.retentions_of(store, attempt["runtime_attempt_id"])
    policies = {one["retention_policy_digest"] for one in retained}
    if len(policies) != 1:
        raise ContractRefusal("refused", "precondition",
                              "historical review cleanup requires one exact retention policy")
    policy = next(iter(policies))
    operation = intake.destroy_operation(attempt, receipt["receipt_digest"], policy)
    record = store.operation_record(operation["operation_id"])
    if record is None or record["kind"] != "runtime.destroy" or record["state"] != "committed":
        raise ContractRefusal("refused", "precondition",
                              "historical review has no committed positive cleanup")
    signature = manager_signature("runtime.destroy", {
        "attempt_id": attempt["runtime_attempt_id"], "expect": fence["intent"]["assignment"],
        "runtime_id": attempt["runtime_id"], "intake_receipt_digest": receipt["receipt_digest"],
        "retention_policy_digest": policy})
    found, cleaned = store.replay(operation["operation_id"], signature, kind="runtime.destroy")
    cleaned = boundaries.document(cleaned, "a historical review cleanup",
        required=("attempt_id", "cleanup", "state", "why", "kept", "operation", "directory_custody"))
    if not found or cleaned["attempt_id"] != attempt["runtime_attempt_id"] \
            or cleaned["cleanup"] != "retained" or cleaned["state"] != "absent" \
            or cleaned["operation"] != operation \
            or cleaned["kept"] != sorted(one["artifact_id"] for one in retained) \
            or cleaned["directory_custody"] is None:
        raise ContractRefusal("refused", "precondition",
                              "historical review cleanup does not prove positive absence and retained custody")
    adopted = {which: custody.historical_directory_custody(store, attempt["runtime_attempt_id"], which)
               for which in ("result", "workspace")}
    if cleaned["directory_custody"] != adopted:
        raise ContractRefusal("integrity", "schema",
                              "historical review cleanup differs from its committed directory custody")


def _completed_review(store, attachment, *, verdict=None):
    attempt = _attempt(store, attachment["runtime_attempt_id"])
    historical = attempt["execution_runtime"] == "destroyed" and verdict is not None
    if not historical:
        attempt = _quiescent_completed(store, attachment["runtime_attempt_id"], review=True)
    # THE REVIEWER'S OWN VERIFICATION AXIS IS NO LONGER A PREREQUISITE, and
    # that is an owner ruling rather than a relaxation this module chose.
    # M111752: for this milestone the implementer runs the ordinary required
    # tests and an independent reviewer assesses the checkpoint; there is no
    # separate producer that could write `passed` into a REVIEW attempt's axis,
    # so requiring one made every honest review unsettleable. The axis stays
    # exactly as it is -- nothing here writes it, resets it, or reinterprets a
    # `failed` or `unable` value somebody else recorded.
    #
    # WHAT REPLACES IT IS NOT NOTHING. A verdict still requires the exact
    # attached runtime positively quiescent, a `completed` worker disposition,
    # a frozen result naming this attempt, separately frozen findings and logs,
    # and -- below -- custody evidence when the output has been sealed. Custody
    # alone never proves a review happened; it proves the output a review is
    # about is one this manager holds.
    if attempt["output"] not in ("frozen", "sealed"):
        raise ContractRefusal(
            "refused", "precondition",
            f"a review verdict requires frozen or sealed output and this "
            f"attempt reports {name_value(attempt['output'])}")
    result = output.frozen_output_of(store, attachment["runtime_attempt_id"])
    if result is None:
        raise ContractRefusal("refused", "precondition",
                              "a review verdict requires a frozen review result")
    result = _review_result(result)
    if result["attempt_id"] != attachment["runtime_attempt_id"]:
        raise ContractRefusal("integrity", "schema",
                              "the frozen review result names another attempt")
    if attempt["output"] == "sealed":
        _custodied_review(store, attempt, result)
    if historical:
        _cleaned_review(store, attachment, attempt, result, verdict)
    return attempt, result


def record_verdict(store, *, attachment_id, disposition, profile, port):
    """Bind one disposition to all immutable checkpoint and reviewer evidence."""
    profile_name = _profile(profile, ("validate",))
    if disposition not in DISPOSITIONS:
        raise ContractRefusal("integrity", "schema",
                              f"a review disposition is one of {DISPOSITIONS!r}")
    attachment = _attachment(store, attachment_id)
    checkpoint = checkpoint_of(store, attachment["checkpoint_id"])
    line = line_of(store, attachment["line_id"])
    if checkpoint["line_id"] != line["line_id"] \
            or checkpoint["state"] != "frozen":
        raise ContractRefusal("integrity", "schema",
                              "a verdict attachment does not name its line's frozen checkpoint")
    if line["profile_name"] != profile_name:
        raise ContractRefusal("policy", "profile-uncertified",
                              "the line and verdict profile do not match")
    if attachment["state"] == "active" and (
            line["state"] != "reviewing"
            or line["current_checkpoint_id"] != checkpoint["checkpoint_id"]):
        raise ContractRefusal("refused", "precondition",
                              "a verdict applies only to the active current review")
    if _attempt(store, attachment["runtime_attempt_id"])["execution_runtime"] == "destroyed":
        verdict = verdict_of(store, _id("verdict", {"attachment_id": attachment_id,
                                                    "disposition": disposition}))
        attempt, _ = _completed_review(store, attachment, verdict=verdict)
        if attempt["assignment_participant"] != getattr(port, "participant", None):
            raise ContractRefusal("refused", "capability",
                                  "the review fence session acts for another participant")
        return _committed_act(store, VERDICT_KIND, VERDICT_KIND + ":" + attachment_id,
                              "the historical review verdict")
    attempt, review_result = _completed_review(store, attachment)
    if attempt["assignment_participant"] != getattr(port, "participant", None):
        raise ContractRefusal("refused", "capability",
                              "the review fence session acts for another participant")
    if attachment["state"] == "active":
        profile.validate(line["line_path"], checkpoint["evidence"], current=True)
    review_fence = _fence(attempts.finalize_quiescent_assignment(
        store, port, attempt_id=attachment["runtime_attempt_id"],
        reason="independent checkpoint review completed"),
        "the checkpoint review fence")
    _current_fence(store, attempt, review_fence,
                   "the checkpoint review fence")
    evidence = checkpoint["evidence"]
    verdict_id = _id("verdict", {"attachment_id": attachment_id,
                                 "disposition": disposition})
    operands = {"verdict_id": verdict_id, "authority_uuid": line["authority_uuid"],
                "work_id": line["work_id"], "line_id": line["line_id"],
                "checkpoint_id": checkpoint["checkpoint_id"],
                "checkpoint_digest": checkpoint["checkpoint_digest"],
                "revision": checkpoint["revision"], "base": evidence["base"],
                "head": evidence["head"], "tree": evidence["tree"],
                "path_set_digest": evidence["path_set_digest"],
                "attachment_id": attachment_id,
                "review_generation": attachment["assignment_generation"],
                "reviewer_worker_id": attachment["reviewer_worker_id"],
                "reviewer_participant": attachment["reviewer_participant"],
                "reviewer_principal": attachment["reviewer_principal"],
                "disposition": disposition,
                "review_result": review_result,
                "review_result_digest": digest(review_result),
                "review_fence": review_fence,
                "review_fence_digest": digest(review_fence)}
    signature = manager_signature("review-line.verdict", operands)
    operation_id = "review-line.verdict:" + attachment_id
    found, result = store.replay(operation_id, signature,
                                 kind="review-line.verdict")
    if found:
        return result
    if attachment["state"] != "active" or line["state"] != "reviewing" \
            or line["current_checkpoint_id"] != checkpoint["checkpoint_id"]:
        raise ContractRefusal("refused", "precondition",
                              "a verdict applies only to the active current review")
    def act(connection):
        _completed_review(store, attachment)
        current_attachment = _attachment(store, attachment_id)
        current_line = line_of(store, line["line_id"])
        if current_attachment["state"] != "active":
            raise ContractRefusal("refused", "precondition",
                                  "the review attachment has already ended")
        if current_attachment["line_id"] != current_line["line_id"] \
                or current_attachment["checkpoint_id"] != checkpoint["checkpoint_id"] \
                or current_line["state"] != "reviewing" \
                or current_line["current_checkpoint_id"] != checkpoint["checkpoint_id"]:
            raise ContractRefusal("integrity", "schema",
                                  "the active review no longer names the current checkpoint")
        now = store._now()
        connection.execute(
            "INSERT INTO checkpoint_verdicts (verdict_id, line_id, checkpoint_id, "
            "attachment_id, authority_uuid, work_id, review_assignment_generation, "
            "reviewer_worker_id, reviewer_participant, reviewer_principal, "
            "disposition, checkpoint_digest, revision, base_object, head_object, "
            "tree_object, path_set_digest, review_result, review_result_digest, "
            "review_fence, review_fence_digest, recorded_at) VALUES (?, ?, ?, ?, "
            "?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (verdict_id, line["line_id"], checkpoint["checkpoint_id"],
             attachment_id, line["authority_uuid"], line["work_id"],
             attachment["assignment_generation"], attachment["reviewer_worker_id"],
             attachment["reviewer_participant"], attachment["reviewer_principal"],
             disposition, checkpoint["checkpoint_digest"], checkpoint["revision"],
             evidence["base"], evidence["head"], evidence["tree"],
             evidence["path_set_digest"], canonical_text(review_result),
             digest(review_result), canonical_text(review_fence),
             digest(review_fence), now))
        connection.execute("UPDATE review_attachments SET state = 'ended', "
                           "ended_at = ? WHERE attachment_id = ?", (now, attachment_id))
        next_state = {"accepted": "accepted", "changes-requested":
                      "correction-ready", "rejected": "rejected"}[disposition]
        connection.execute("UPDATE review_lines SET state = ? WHERE line_id = ?",
                           (next_state, line["line_id"]))
        if disposition == "accepted":
            connection.execute(
                "INSERT INTO integration_eligibility (checkpoint_id, line_id, "
                "verdict_id, eligible_at) VALUES (?, ?, ?, ?)",
                (checkpoint["checkpoint_id"], line["line_id"], verdict_id, now))
        return dict(operands)

    return store.transact(operation_id,
                          "review-line.verdict", signature, act)


def _restore_operation_id(kind, attempt_id, generation):
    """One recovery identity per attempt and fenced generation.

    DERIVED FROM THE TWO THINGS THAT DO NOT MOVE, exactly as the sibling
    historical readers are: a manager resuming after a crash re-derives it
    without first re-establishing the evidence, so an intent it already
    committed is found before anything mutable is read. The kind rides the
    identity, so the intent and the completion cannot collide on one.
    """
    return kind + ":" + _id("restore", {"kind": kind,
                                        "attempt_id": attempt_id,
                                        "generation": generation})


def _abandoned_evidence(store, attempt_id, generation, retention_policy_digest,
                        what):
    """W128682's two accepted readers, cross-bound to THIS attempt and
    generation.

    THE PROVIDER BOUNDARY IS ITS PUBLIC SURFACE AND NOTHING ELSE. Both readers
    are `intake`'s public operations; no private helper is called and no table
    of its is read. What they answer is already validated whole on their own
    side -- the declaration, the authority's fence, the removal's settled
    absence and the committed gate discharge -- so what is left for this
    module is the crossing: that all of it is about the attempt, the
    generation and the policy THIS recovery is for.
    """
    cleanup = intake.abandonment_cleanup_of(
        store, attempt_id=attempt_id,
        retention_policy_digest=retention_policy_digest)
    if cleanup is None:
        raise ContractRefusal(
            "refused", "precondition",
            f"{what} has no committed abandoned cleanup under retention "
            f"policy {name_value(retention_policy_digest)}; a correction is "
            f"restored behind a declared abandonment this manager committed "
            f"and never behind the absence of one")
    discharge = intake.abandoned_gate_discharge_of(store, attempt_id)
    if discharge is None:
        raise ContractRefusal(
            "refused", "precondition",
            f"{what}'s abandonment has not discharged its runtime-quiescence "
            f"gate; the generation is still held at the authority, and a "
            f"checkout is not restored for a successor that cannot be "
            f"assigned")
    if cleanup["assignment"]["generation"] != generation:
        raise ContractRefusal(
            "stale-assignment", "generation",
            f"{what}'s committed abandonment is for generation "
            f"{cleanup['assignment']['generation']}; one recovery answers for "
            f"one fenced generation")
    # THE DISCHARGE IS THE CLEANUP'S OWN, compared whole. Its
    # `cleanup_operation` carries the identity AND the signature, and the
    # signature is the half that names the runtime -- so comparing one and
    # dropping the other would let a discharge earned behind one removal
    # authorize a recovery after another.
    if discharge["cleanup_operation"] != cleanup["cleanup"]["operation"] \
            or discharge["assignment"] != cleanup["assignment"] \
            or discharge["runtime_id"] != cleanup["runtime_id"] \
            or discharge["retention_policy_digest"] \
            != cleanup["retention_policy_digest"]:
        raise ContractRefusal(
            "integrity", "schema",
            f"{what}'s committed gate discharge and its committed abandoned "
            f"cleanup do not describe one act; the discharge names the "
            f"removal it was earned behind, and two accounts of one ending "
            f"have no tie-break")
    return cleanup, discharge


def _abandoned_writer(store, attempt_id, generation, what):
    """The historical writer this correction was granted, still holding the
    line.

    THROUGH THE EXISTING OWNER, never through the line's current pointer:
    `writer_for_attempt` answers from the attempt and its generation, which do
    not move, and binds the row to the committed grant that fixed it.

    AND `active` IS REQUIRED HERE, unlike in that reader. It is what makes this
    an UNFINISHED correction: a revoked writer is what a round that reached its
    checkpoint leaves behind, and there is nothing to restore for one.
    """
    writer = writer_for_attempt(store, attempt_id=attempt_id,
                                generation=generation)
    if writer is None:
        raise ContractRefusal(
            "refused", "precondition",
            f"{what} was granted no line writer at that generation; there is "
            f"no correction here to restore")
    if writer["state"] != "active":
        raise ContractRefusal(
            "refused", "precondition",
            f"{what}'s writer is {name_value(writer['state'])}; a restore "
            f"recovers a correction that never reached its checkpoint, and a "
            f"revoked writer is what one that did leaves behind")
    if writer["based_checkpoint_id"] is None:
        raise ContractRefusal(
            "refused", "precondition",
            f"{what}'s writer is based on no checkpoint; this recovery "
            f"restores a CORRECTION to the checkpoint it was based on, and a "
            f"first writer has none to return to")
    return writer


def _resumed_writer(store, attempt_id, generation, what):
    """The writer THIS recovery's own intent already revoked.

    W257624, owner ruling 2026-09-26T01:35:02Z. The intent transaction takes the
    exclusion by revoking, so a resumed recovery must NOT look for an active
    writer -- `_abandoned_writer` requires one and is the fresh path's reader.
    What a resumption proves instead is that the revocation standing here is the
    one its own intent made: this attempt's writer at this generation, revoked
    for `abandoned`, still based on a checkpoint.

    A REVOCATION THIS RECOVERY DID NOT MAKE IS NOT ITS EXCLUSION. The reason is
    compared because `freeze_checkpoint` also revokes, and a correction that
    reached its checkpoint leaves exactly that behind -- so accepting any revoked
    writer would let a finished round look like an unfinished recovery's
    resumption.
    """
    writer = writer_for_attempt(store, attempt_id=attempt_id,
                               generation=generation)
    if writer is None:
        raise ContractRefusal(
            "refused", "precondition",
            f"{what} was granted no line writer at that generation; there is "
            f"no correction here to restore")
    if writer["state"] != "revoked" \
            or writer["revocation_reason"] != _ABANDONED_REVOCATION:
        raise ContractRefusal(
            "refused", "precondition",
            f"{what}'s writer is {name_value(writer['state'])} for "
            f"{name_value(writer['revocation_reason'])} and this recovery's own "
            f"intent revoked it as {name_value(_ABANDONED_REVOCATION)}; a "
            f"resumption finishes the exclusion it took and never somebody "
            f"else's")
    if writer["based_checkpoint_id"] is None:
        raise ContractRefusal(
            "refused", "precondition",
            f"{what}'s writer is based on no checkpoint; this recovery "
            f"restores a CORRECTION to the checkpoint it was based on, and a "
            f"first writer has none to return to")
    return writer


def _restorable_line(store, writer, what):
    """The same durable line, proved to be the one this writer is holding.

    EVERY MEMBER IS A RELATIONSHIP RATHER THAN A SHAPE. The line is the
    writer's own; it is still `writing`, because that is what an unfinished
    correction leaves and any other state means somebody else already moved it;
    its pathname still names the same object, by device and inode rather than
    by name; and its current checkpoint is the one the writer was based on --
    which is the committed provenance, because `grant_writer` admits a
    correction writer ONLY from a `correction-ready` line whose
    `current_checkpoint_id` equals that checkpoint, and a line reaches
    `correction-ready` ONLY through a `changes-requested` verdict.
    """
    line = line_of(store, writer["line_id"])
    if line["state"] != "writing":
        raise ContractRefusal(
            "refused", "precondition",
            f"{what}'s line is {name_value(line['state'])}; a correction that "
            f"is still owed a restore leaves its line writing, and any other "
            f"state is one somebody else already moved")
    if line["current_checkpoint_id"] != writer["based_checkpoint_id"]:
        raise ContractRefusal(
            "integrity", "schema",
            f"{what}'s line currently points at checkpoint "
            f"{name_value(line['current_checkpoint_id'])} and its writer was "
            f"based on {name_value(writer['based_checkpoint_id'])}; a "
            f"correction is restored to the checkpoint it was granted "
            f"against")
    _validate_line_object(line)
    return line


def _correcting_verdict(store, checkpoint_id, line_id, what):
    """The committed changes-requested verdict this correction came from.

    REVIEW 2026-09-09T15:50Z [P1], and the finding is right. My first cut used
    the committed GRANT as the provenance, on the ground that `grant_writer`
    admits a correction writer only from a `correction-ready` line at this
    checkpoint. That proves ADMISSION and it does not re-read the verdict: a
    retained verdict whose principal had been edited made `verdict_of` refuse
    while this act still wrote a checkout and completed.

    ONE IDENTITY IS SELECTED AND THE OWNER VALIDATES THE RECORD. The
    clarification pinned in this Work's FINDING before editing: the query below
    answers a verdict IDENTITY, and `verdict_of` then owns the whole row and
    binds it to the act that recorded it. No second column contract for
    `checkpoint_verdicts` is created, which is what `_verdict_row`'s own
    comment is about.
    """
    row = store._connection.execute(
        "SELECT verdict_id FROM checkpoint_verdicts WHERE checkpoint_id = ?",
        (checkpoint_id,)).fetchone()
    if row is None:
        raise ContractRefusal(
            "refused", "precondition",
            f"{what}'s based checkpoint carries no recorded verdict; a "
            f"correction is restored behind the changes-requested decision "
            f"that scheduled it")
    verdict = verdict_of(store, row["verdict_id"])
    if verdict["disposition"] != "changes-requested":
        raise ContractRefusal(
            "refused", "precondition",
            f"{what}'s based checkpoint was decided "
            f"{name_value(verdict['disposition'])}; only a changes-requested "
            f"decision schedules a correction to restore")
    if verdict["checkpoint_id"] != checkpoint_id \
            or verdict["line_id"] != line_id:
        raise ContractRefusal(
            "integrity", "schema",
            f"{what}'s verdict names checkpoint "
            f"{name_value(verdict['checkpoint_id'])} on line "
            f"{name_value(verdict['line_id'])} and this recovery is for "
            f"{name_value(checkpoint_id)} on {name_value(line_id)}")
    return verdict


def _sole_attachment(store, line, writer, what):
    """Nobody else is attached to this line, writable or read-only.

    A restore discards a whole checkout, so the question is not only whether
    another WRITER exists -- a live review attachment is reading the same tree,
    and returning it to an earlier checkpoint underneath one would be
    destroying the subject of somebody's review.
    """
    writers = store._connection.execute(
        "SELECT writer_id FROM line_writers WHERE line_id = ? AND "
        "state = 'active'", (line["line_id"],)).fetchall()
    held = sorted(row["writer_id"] for row in writers)
    # A RESUMED RECOVERY OWNS NO ACTIVE WRITER -- its own intent already
    # revoked one -- so `None` asks for exactly that: nobody at all.
    if held != ([] if writer is None else [writer["writer_id"]]):
        raise ContractRefusal(
            "refused", "precondition",
            f"{what}'s line holds active writers {sample_of(held)}, and this "
            f"recovery owns "
            f"{'none' if writer is None else name_value(writer['writer_id'])}"
            f"; a checkout is not restored under an attachment this act does "
            f"not hold")
    reviewing = store._connection.execute(
        "SELECT attachment_id FROM review_attachments WHERE line_id = ? AND "
        "state = 'active'", (line["line_id"],)).fetchall()
    if reviewing:
        raise ContractRefusal(
            "refused", "precondition",
            f"{what}'s line has an active review attachment; a restore "
            f"discards the whole checkout, and doing that under a live review "
            f"would destroy what is being reviewed")


def _fixed_intent(store, intent_id, record, attempt_id, generation,
                  retention_policy_digest, what):
    """The recovery intent an earlier attempt of THIS call already committed.

    Adopted from the journal rather than rebuilt: the whole point of resuming
    is that the earlier attempt's decisions are the ones being finished, and
    recomposing them here would let a changed world produce a second account
    of one recovery.

    BUT ADOPTED IS NOT BELIEVED, and review 2026-09-09T16:31Z [P1] is why this
    says so. `store.replay` compares the row's signature to the one it is
    HANDED, so passing the row's own signature back compares it with itself --
    which proves nothing. Replacing that column with canonical operand text
    under a FOREIGN KIND therefore left the identity and the result untouched
    and the retry went on to write a checkout.

    SO THE SIGNATURE IS RECOMPOSED FROM THE ADOPTED DOCUMENT, under THIS
    family's kind, and compared with what the journal recorded. That is one
    comparison for a relationship the members cannot state separately: an
    intent whose kind, shape or any member was changed cannot reproduce it.

    AND THE SHAPE IS CLOSED BEFORE ANY NESTED FIELD IS INDEXED. `fixed
    ["assignment"]["generation"]` on a malformed row is a `TypeError` at a
    persisted-input boundary, which bypasses the portable refusal path every
    other reader here uses.
    """
    if record["kind"] != RESTORE_INTENT_KIND:
        raise ContractRefusal(
            "integrity", "schema",
            f"{what} names intent operation {name_value(intent_id)}, which "
            f"this manager committed as {name_value(record['kind'])}")
    _, committed = store.replay(intent_id, record["signature"],
                                kind=RESTORE_INTENT_KIND)
    if committed is None:
        raise ContractRefusal(
            "integrity", "schema",
            f"{what} names intent operation {name_value(intent_id)}, which "
            f"this manager committed with no recorded answer to replay")
    fixed = boundaries.document(committed, f"{what}'s recovery intent",
                                required=_RESTORE_INTENT)
    if fixed["schema"] != ABANDONED_CORRECTION_SCHEMA:
        raise ContractRefusal(
            "integrity", "schema",
            f"{what}'s recorded intent names schema "
            f"{name_value(fixed['schema'])} and this manager writes "
            f"{name_value(ABANDONED_CORRECTION_SCHEMA)}")
    for member in ("attempt_id", "runtime_id", "writer_id", "line_id",
                   "checkpoint_id", "discharge_operation_id"):
        boundaries.identity(fixed[member], f"{what}'s intent {member}")
    boundaries.text(fixed["retention_policy_digest"],
                    f"{what}'s intent retention policy digest")
    boundaries.text(fixed["checkpoint_digest"],
                    f"{what}'s intent checkpoint digest")
    boundaries.document(fixed["cleanup_operation"],
                        f"{what}'s intent cleanup operation",
                        required=("operation_id", "signature_digest"))
    # CLOSED BEFORE IT IS INDEXED.
    assignment = boundaries.document(
        fixed["assignment"], f"{what}'s intent assignment",
        required=("work_ref", "participant", "generation"))
    boundaries.document(assignment["work_ref"],
                        f"{what}'s intent Work reference",
                        required=("authority_uuid", "work_id"))
    boundaries.generation(assignment["generation"],
                          f"{what}'s intent generation")
    # THE ONE COMPARISON THAT BINDS THEM ALL, against the journal's own record.
    if record["signature"] != manager_signature(RESTORE_INTENT_KIND, fixed):
        raise ContractRefusal(
            "integrity", "schema",
            f"{what}'s recorded intent composes a signature its own members do "
            f"not match the one this manager committed for "
            f"{name_value(intent_id)}; the schema, the attempt, the "
            f"assignment, the writer, the line, the checkpoint and both "
            f"provider operations are ONE signed relationship, and an intent "
            f"whose kind or members were changed cannot reproduce it")
    if fixed["retention_policy_digest"] != retention_policy_digest:
        raise ContractRefusal(
            "refused", "operation-collision",
            f"{what} was begun under retention policy "
            f"{name_value(fixed['retention_policy_digest'])} and this call "
            f"names {name_value(retention_policy_digest)}; a retry finishes "
            f"what it started and never something else (§4.2)")
    if fixed["attempt_id"] != attempt_id \
            or assignment["generation"] != generation:
        raise ContractRefusal(
            "integrity", "schema",
            f"{what} names an intent recorded for another attempt or "
            f"generation")
    return fixed


def _intent_agrees(fixed, writer, line, checkpoint, cleanup, discharge, what):
    """The committed intent, bound back to the world it named.

    REVIEW 2026-09-09T16:04Z. A retry that adopted its intent and then acted on
    freshly read rows would be finishing an intent whose writer, line,
    checkpoint or evidence had moved under it -- which is the same class of
    defect as trusting a receipt because it is internally consistent.
    """
    for member, mine in (("writer_id", writer["writer_id"]),
                         ("line_id", line["line_id"]),
                         ("checkpoint_id", checkpoint["checkpoint_id"]),
                         ("checkpoint_digest", checkpoint["checkpoint_digest"]),
                         ("runtime_id", cleanup["runtime_id"]),
                         ("assignment", cleanup["assignment"]),
                         ("cleanup_operation", cleanup["cleanup"]["operation"]),
                         ("discharge_operation_id", discharge["operation_id"])):
        if fixed[member] != mine:
            raise ContractRefusal(
                "integrity", "schema",
                f"{what}'s recorded intent names {member} "
                f"{name_value(fixed[member])} and the owners now describe "
                f"{name_value(mine)}; a retry finishes the recovery it began "
                f"and not one the world has moved out from under")


def _adopted_correction(value, what, *, operation_id=None, attempt_id=None,
                        assignment=None):
    """One completed recovery, owned with its VALUES and its RELATIONSHIPS.

    BOTH PUBLIC EXITS COME THROUGH HERE -- the completing transaction and
    `abandoned_correction_of` -- so what is written is held to exactly the
    contract what is read is held to, rather than being trusted because this
    process just built it. Generic parsing establishes that bytes decode; it
    establishes nothing about whose recovery they describe.
    """
    taken = boundaries.document(value, what, required=ABANDONED_CORRECTION)
    if taken["schema"] != ABANDONED_CORRECTION_SCHEMA:
        raise ContractRefusal(
            "integrity", "schema",
            f"{what} records schema {name_value(taken['schema'])} and this "
            f"manager writes {name_value(ABANDONED_CORRECTION_SCHEMA)}")
    if taken["state"] != _CORRECTION_READY:
        raise ContractRefusal(
            "integrity", "schema",
            f"{what} records state {name_value(taken['state'])}; a completed "
            f"recovery returned its line to {name_value(_CORRECTION_READY)}, "
            f"and a record that does not say so is not evidence that one did")
    for member in ("operation_id", "attempt_id", "runtime_id", "writer_id",
                   "line_id", "checkpoint_id", "discharge_operation_id"):
        boundaries.identity(taken[member], f"{what}'s {member}")
    boundaries.text(taken["retention_policy_digest"],
                    f"{what}'s retention policy digest")
    _evidence(taken["checkpoint_evidence"])
    boundaries.document(taken["cleanup_operation"],
                        f"{what}'s cleanup operation",
                        required=("operation_id", "signature_digest"))
    held = boundaries.document(taken["assignment"], f"{what}'s assignment",
                               required=("work_ref", "participant",
                                         "generation"))
    boundaries.document(held["work_ref"], f"{what}'s Work reference",
                        required=("authority_uuid", "work_id"))
    boundaries.generation(held["generation"], f"{what}'s generation")
    for member, expected in (("operation_id", operation_id),
                             ("attempt_id", attempt_id)):
        if expected is not None and taken[member] != expected:
            raise ContractRefusal(
                "integrity", "schema",
                f"{what} records {member} {name_value(taken[member])} and "
                f"this read selected {name_value(expected)}")
    if assignment is not None and held != assignment:
        raise ContractRefusal(
            "integrity", "schema",
            f"{what} records an assignment that is not the one this attempt "
            f"is fixed to")
    return taken


def abandoned_correction_of(store, *, attempt_id, generation):
    """The completed recovery for this attempt and generation, or absence.

    W128692, `work/records/2026/09/finding-v12-abandoned-checkpoint-restore/`.

    THE DISCOVERABILITY HALF, and it is a read. It performs no profile act, no
    Authority act, no runtime act and no write of any kind -- there is no
    branch in it that could.

    IT ANSWERS ABOUT HISTORY AND NOT ABOUT NOW. A completed recovery is a fact
    about one attempt's generation, and it stays true after the line has moved
    on: a later writer may already hold the line, and a later checkpoint may
    already have been frozen. So this deliberately does NOT claim the CURRENT
    line is correction-ready because this operation completed. A consumer
    deciding whether it may start work checks its own live episode and its own
    admissibility, and this tells it only that the restore it was waiting on
    happened.

    ABSENCE IS THE ONLY `None`. An attempt with no committed completion has not
    been recovered; a present record this manager cannot own is an integrity
    failure an operator has to look at, and reporting the second as the first
    would invite a consumer to run a restore over a checkout somebody else now
    holds.
    """
    attempt_id, generation = _requested_pair(attempt_id, generation)
    what = (f"the abandoned-correction recovery for attempt "
            f"{name_value(attempt_id)} generation {generation}")
    operation_id = _restore_operation_id(RESTORE_KIND, attempt_id, generation)
    record = store.operation_record(operation_id)
    if record is None:
        return None
    if record["kind"] != RESTORE_KIND:
        raise ContractRefusal(
            "integrity", "schema",
            f"{what} names operation {name_value(operation_id)}, which this "
            f"manager committed as {name_value(record['kind'])}")
    _, committed = store.replay(operation_id, record["signature"],
                                kind=RESTORE_KIND)
    if committed is None:
        raise ContractRefusal(
            "integrity", "schema",
            f"{what} names operation {name_value(operation_id)}, which this "
            f"manager committed with no recorded answer to replay")
    taken = _adopted_correction(committed, what, operation_id=operation_id,
                                attempt_id=attempt_id)
    # THE JOURNAL'S OWN SIGNATURE, DERIVED FROM THE RECORD AND COMPARED. A
    # stored row and the digest beside it can be edited together; what a store
    # edit cannot reproduce is the relationship this manager signed.
    if record["signature"] != _correction_signature(taken):
        raise ContractRefusal(
            "integrity", "schema",
            f"{what} composes a signature its own members do not match the "
            f"one this manager committed; the attempt, the assignment, the "
            f"writer, the line, the checkpoint and the cleanup operation are "
            f"ONE signed relationship")
    _historical_owners(store, taken, generation, what)
    return taken


def _historical_owners(store, taken, generation, what):
    """The immutable records this recovery was earned against, RE-READ.

    REVIEW 2026-09-09T15:50Z [P1]. My first cut checked the receipt against a
    signature recomposed from that same receipt -- which proves the record is
    internally consistent and nothing else. Editing the old writer's principal
    made the public `writer_for_attempt` owner refuse, and this reader still
    answered as though the recovery's evidence were intact.

    SO THE OWNERS ARE FOLLOWED, and each refuses on its own behalf: the writer
    for this attempt and generation, the checkpoint it was based on, and the
    changes-requested verdict that scheduled the correction.

    AND NOTHING MUTABLE IS A PREDICATE. Not the line's state, not the writer's
    state, not the line's current pointer -- all three move when a later round
    runs, and a completed recovery is a fact about one attempt's generation
    that stays true afterwards. What is compared is identity and immutable
    relationship.
    """
    # REVIEW 2026-09-09T16:16Z [P1]. A canonical signature is operand TEXT, so
    # editing the committed result and its operands together reproduces it --
    # which is how a receipt naming a FOREIGN runtime survived a check that
    # recomposed the signature from the receipt. The whole relationship is
    # therefore bound back to W128682's public owners, for the SELECTED
    # generation, and none of it is a mutable predicate.
    cleanup = intake.abandonment_cleanup_of(
        store, attempt_id=taken["attempt_id"],
        retention_policy_digest=taken["retention_policy_digest"])
    discharge = intake.abandoned_gate_discharge_of(store, taken["attempt_id"])
    if cleanup is None or discharge is None:
        raise ContractRefusal(
            "integrity", "schema",
            f"{what} records a recovery whose committed abandonment or gate "
            f"discharge this manager cannot show under the policy it names")
    for member, mine in (
            ("assignment", cleanup["assignment"]),
            ("runtime_id", cleanup["runtime_id"]),
            ("cleanup_operation", cleanup["cleanup"]["operation"]),
            ("discharge_operation_id", discharge["operation_id"])):
        if taken[member] != mine:
            raise ContractRefusal(
                "integrity", "schema",
                f"{what} records {member} {name_value(taken[member])} and the "
                f"committed abandonment it was earned behind records "
                f"{name_value(mine)}; one recovery answers for one attempt, "
                f"one runtime and one removal")
    if cleanup["assignment"]["generation"] != generation:
        raise ContractRefusal(
            "stale-assignment", "generation",
            f"{what} is for generation "
            f"{cleanup['assignment']['generation']}; one recovery answers for "
            f"one fenced generation")
    writer = writer_for_attempt(store, attempt_id=taken["attempt_id"],
                                generation=generation)
    if writer is None or writer["writer_id"] != taken["writer_id"] \
            or writer["line_id"] != taken["line_id"] \
            or writer["based_checkpoint_id"] != taken["checkpoint_id"]:
        raise ContractRefusal(
            "integrity", "schema",
            f"{what} names a writer its own historical owner does not "
            f"describe; one recovery answers for one writer, one line and one "
            f"based checkpoint")
    checkpoint = checkpoint_of(store, taken["checkpoint_id"])
    if checkpoint["line_id"] != taken["line_id"] \
            or checkpoint["state"] != "frozen" \
            or checkpoint["evidence"] != taken["checkpoint_evidence"]:
        raise ContractRefusal(
            "integrity", "schema",
            f"{what} records checkpoint evidence its own owner does not hold")
    _correcting_verdict(store, taken["checkpoint_id"], taken["line_id"], what)


def _correction_signature(taken):
    """The operands a completed recovery signs, recomposed from the record."""
    cleanup = taken["cleanup_operation"]
    return manager_signature(RESTORE_KIND, {
        "attempt_id": taken["attempt_id"],
        "assignment": taken["assignment"],
        "runtime_id": taken["runtime_id"],
        "retention_policy_digest": taken["retention_policy_digest"],
        "writer_id": taken["writer_id"], "line_id": taken["line_id"],
        "checkpoint_id": taken["checkpoint_id"],
        "checkpoint_digest": digest(taken["checkpoint_evidence"]),
        "cleanup_operation_id": cleanup["operation_id"],
        "cleanup_signature_digest": cleanup["signature_digest"],
        "discharge_operation_id": taken["discharge_operation_id"]})


def restore_abandoned_correction(store, *, attempt_id, generation,
                                 retention_policy_digest, profile, launcher=None,
                                 cessation=None):
    """Give a declared abandoned correction's line back, at its own checkpoint.

    W128692. W119114's composed proof measured what an operator declaration
    leaves behind: the runtime is destroyed and the generation fenced, and the
    LINE is still `writing` with the abandoned attempt's writer still `active`.
    `grant_writer` admits a writer only from `idle` or `correction-ready`, and
    the only thing in this build that revokes one is `freeze_checkpoint` --
    which an abandoned correction by definition never reaches. So no successor
    could ever be granted the line.

    AND MOVING THE ROWS WOULD NOT BE ENOUGH. The checkout still holds the
    abandoned worker's uncommitted scratch, and `validate(current=True)`
    requires a clean checkout at the retained head -- so the next writer's own
    admission would refuse. The checkout has to go back to the checkpoint the
    correction was based on, which is what the profile's new
    `restore_checkpoint` is for.

    THE ORDER, and each step is the next one's precondition:

      1. own the operands and the profile's two capabilities;
      2. REPLAY a completed recovery and return it, before anything mutable is
         read. A restore that already finished must answer without touching a
         checkout a later writer may now hold -- which is the whole reason the
         completed record exists;
      3. prove W128682's committed abandonment and gate discharge, cross-bound
         to this attempt, this generation and this policy;
      4. prove the exclusion: the historical writer is this attempt's and is
         still active on a based frozen checkpoint, the line is that writer's
         own and still `writing` at that same checkpoint, and NOTHING else is
         attached to it;
      5. commit the INTENT, which TAKES THE EXCLUSION by revoking the writer
         in the same transaction that records what this recovery is for;
      6. only then ask the profile to restore, and
      7. commit the completion, returning the line to `correction-ready` at
         the SAME retained checkpoint.

    FIVE AND SIX CANNOT BE ONE TRANSACTION, for the reason a remote act cannot
    be: the profile writes a filesystem this database does not own, and holding
    a write lock across it would block every other manager act for the length
    of a checkout. So the intent commits first and the completion second, and a
    crash between them leaves a recorded intent with no completion -- exactly
    what a retry needs to find.

    AND THAT IS AGAIN WHAT THIS CODE DOES, after a detour. Review 2026-09-09T16:04Z
    moved the restoration INSIDE the completing transaction and this docstring's
    steps 5 to 7 were left describing the shape the code had abandoned. Owner
    ruling 2026-09-26T01:35:02Z withdraws that acceptance -- no database lock may
    be held across I/O other than the database's own -- so the three steps below
    are once more what runs, and the contrary comments that stood in `act` are
    superseded rather than left beside it. The one thing this ordering does NOT
    achieve is recorded at the restoration itself and in the bound dossier's PLAN:
    a short transaction cannot serialize a filesystem act that happens outside it.

    WHICH IS WHY THE INTENT REVOKES, and review 2026-09-09T15:50Z [P1] is what
    taught me that. My first cut revoked at COMPLETION, so two restorers could
    both pass the entry checks; one completed, a successor was admitted, and
    the other -- still inside the profile -- then reset that successor's
    checkout and returned the first one's committed result as its own success.
    A check after writing, or only at entry, cannot serialize a destructive act
    that happens between them.

    THE REVOCATION IS THE SERIALIZATION, and it holds at both ends. A second
    restorer finds the writer already revoked and refuses before it reaches the
    profile at all. A SUCCESSOR cannot be admitted in the window either,
    because the line is deliberately LEFT `writing` until step seven and
    `grant_writer` admits a writer only from `idle` or `correction-ready` --
    so the release to a successor happens after the restoration, in one
    transaction, or it does not happen.

    A FAILED RESTORE ADMITS NOBODY, and that is the same fact read from the
    other side: the line stays `writing`, so the next `grant_writer` still
    refuses and no successor is handed a checkout this act could not prove.

    IT DOES NOTHING ELSE. No operator declaration, no runtime act, no Authority
    act, no publication, no verdict, no Job episode replacement, and NO NEW
    CHECKPOINT -- the line comes back to the one it already had. Custody
    beside the line is never named, and no pin moves.
    """
    attempt_id, generation = _requested_pair(attempt_id, generation)
    boundaries.text(retention_policy_digest, "a retention policy digest")
    profile_name = _profile(profile, ("validate", "restore_checkpoint"))
    what = (f"the abandoned correction for attempt {name_value(attempt_id)} "
            f"generation {generation}")

    operation_id = _restore_operation_id(RESTORE_KIND, attempt_id, generation)
    record = store.operation_record(operation_id)
    if record is not None:
        # STEP TWO, AND ITS POSITION IS THE CONTRACT. Answered through the
        # public reader so the completed exit and the replay exit are one
        # spelling of one question; nothing mutable has been read yet, so a
        # later writer's checkout is not touched and not even looked at.
        held = abandoned_correction_of(store, attempt_id=attempt_id,
                                       generation=generation)
        if held["retention_policy_digest"] != retention_policy_digest:
            raise ContractRefusal(
                "refused", "operation-collision",
                f"{what} was recovered under retention policy "
                f"{name_value(held['retention_policy_digest'])} and this call "
                f"names {name_value(retention_policy_digest)}; one identity "
                f"carries one act, and reusing it with a different operand "
                f"changes nothing (§4.2)")
        return held

    intent_id = _restore_operation_id(RESTORE_INTENT_KIND, attempt_id,
                                      generation)
    recorded = store.operation_record(intent_id)
    if recorded is not None:
        # THE CRASH-RETRY PATH, and it deliberately does not re-take the
        # exclusion: this recovery already holds it, and the writer the fresh
        # path looks for is the one its own earlier attempt revoked. What is
        # re-proved is that the exclusion is still HERE -- the line has not
        # moved and still points at the checkpoint the intent fixed.
        fixed = _fixed_intent(store, intent_id, recorded, attempt_id,
                              generation, retention_policy_digest, what)
        # REVIEW 2026-09-09T16:04Z: A RETRY IS NOT A SHORTCUT PAST PROVENANCE.
        # The first cut read the writer row directly and skipped both of
        # W128682's readers and the verdict entirely, so a retry after a failed
        # profile call restored a checkout on evidence that had since been
        # broken. Every unfinished retry re-proves the SAME fixed
        # relationships, before any effect.
        cleanup, discharge = _abandoned_evidence(
            store, attempt_id, generation, retention_policy_digest, what)
        # THE WRITER THIS RECOVERY'S OWN INTENT REVOKED, and therefore NOBODY
        # attached. The intent takes the exclusion now, so the fresh path's
        # active-writer reader is wrong here -- `_sole_attachment`'s `None`
        # branch is written for exactly this state and is reached by it.
        writer = _resumed_writer(store, attempt_id, generation, what)
        line = _restorable_line(store, writer, what)
        if line["profile_name"] != profile_name:
            raise ContractRefusal(
                "policy", "profile-uncertified",
                f"{what}'s line was materialized by profile "
                f"{name_value(line['profile_name'])} and this restore offers "
                f"{name_value(profile_name)}")
        _sole_attachment(store, line, None, what)
        checkpoint = checkpoint_of(store, fixed["checkpoint_id"])
        _correcting_verdict(store, checkpoint["checkpoint_id"],
                            line["line_id"], what)
        # AND THE INTENT IS BOUND BACK TO THE WORLD IT NAMED, so a retry cannot
        # finish an intent whose writer, line, checkpoint or evidence have
        # moved under it.
        _intent_agrees(fixed, writer, line, checkpoint, cleanup, discharge,
                       what)
    else:
        cleanup, discharge = _abandoned_evidence(
            store, attempt_id, generation, retention_policy_digest, what)
        writer = _abandoned_writer(store, attempt_id, generation, what)
        line = _restorable_line(store, writer, what)
        if line["profile_name"] != profile_name:
            raise ContractRefusal(
                "policy", "profile-uncertified",
                f"{what}'s line was materialized by profile "
                f"{name_value(line['profile_name'])} and this restore offers "
                f"{name_value(profile_name)}")
        _sole_attachment(store, line, writer, what)
        checkpoint = checkpoint_of(store, writer["based_checkpoint_id"])
        if checkpoint["line_id"] != line["line_id"] \
                or checkpoint["state"] != "frozen" \
                or checkpoint["profile_name"] != profile_name:
            raise ContractRefusal(
                "integrity", "schema",
                f"{what}'s based checkpoint is not this line's frozen "
                f"checkpoint under this profile")
        # THE DECISION THAT SCHEDULED THIS CORRECTION, read through its own
        # owner rather than inferred from the grant that followed it.
        _correcting_verdict(store, checkpoint["checkpoint_id"],
                            line["line_id"], what)
        intent = {"schema": ABANDONED_CORRECTION_SCHEMA,
                  "attempt_id": attempt_id,
                  "assignment": dict(cleanup["assignment"]),
                  "runtime_id": cleanup["runtime_id"],
                  "retention_policy_digest": retention_policy_digest,
                  "writer_id": writer["writer_id"], "line_id": line["line_id"],
                  "checkpoint_id": checkpoint["checkpoint_id"],
                  "checkpoint_digest": checkpoint["checkpoint_digest"],
                  "cleanup_operation": dict(cleanup["cleanup"]["operation"]),
                  "discharge_operation_id": discharge["operation_id"],
                  # THE EXECUTOR, fixed by the act that takes the exclusion.
                  "executor_incarnation": store.incarnation}

        def take(connection):
            """RECORD THE INTENT AND TAKE THE EXCLUSION, in one short act.

            W257624, owner ruling 2026-09-26T01:35:02Z. This function's own
            docstring has always said the intent revokes; the code stopped doing
            it when the restoration was moved under one lock, and the ruling puts
            it back. Nothing here touches a filesystem, so the write lock is held
            for two statements.

            THE REVOCATION IS CONDITIONAL ON THE ROW IT PROVED. `state =
            'active'` is in the WHERE clause, so a writer somebody else revoked
            between the proof above and this lock is not revoked twice and the
            changed count says so.

            AND THE LINE IS DELIBERATELY LEFT `writing`. That is what keeps a
            successor out for the whole restoration: `grant_writer` admits a
            writer only from `idle` or `correction-ready`, so the release happens
            in the completion or it does not happen.
            """
            now = store._now()
            taken = connection.execute(
                "UPDATE line_writers SET state = 'revoked', revoked_at = ?, "
                "revocation_reason = ? WHERE writer_id = ? AND state = 'active'",
                (now, _ABANDONED_REVOCATION, writer["writer_id"]))
            if taken.rowcount != 1:
                raise ContractRefusal(
                    "refused", "precondition",
                    f"{what}'s writer was no longer the active attachment when "
                    f"this recovery took its exclusion; a restoration does not "
                    f"proceed on an exclusion it did not take")
            return dict(intent)

        try:
            fixed = store.transact(intent_id, RESTORE_INTENT_KIND,
                                   manager_signature(RESTORE_INTENT_KIND,
                                                     intent),
                                   take)
        except ContractRefusal as collision:
            # LOSING THE INTENT RACE IS A HELD EXECUTION, NOT OPERAND ABUSE, and
            # it has to be told apart from one. `executor_incarnation` is part of
            # the signed intent -- deliberately, so a stored executor cannot be
            # edited to redirect an in-flight restoration -- which means a caller
            # that composed its own executor and lost the race collides at §4.2
            # rather than replaying. Measured, not assumed: that is exactly what
            # the first cut of this correction produced, and the message it gave
            # described operand reuse.
            #
            # SO THE COMMITTED INTENT IS ADOPTED and this call rejoins the
            # resumed path, where the executor comparison below answers with the
            # held refusal that describes what actually happened. A collision
            # that is NOT this -- a different retention policy, say -- is
            # re-raised by `_fixed_intent`'s own comparisons instead.
            recorded = store.operation_record(intent_id)
            if collision.code != "operation-collision" or recorded is None:
                raise
            fixed = _fixed_intent(store, intent_id, recorded, attempt_id,
                                  generation, retention_policy_digest, what)
        fixed = boundaries.document(fixed, f"{what}'s recovery intent",
                                    required=_RESTORE_INTENT)

    # THE EXECUTOR CHECK, WHERE BOTH BRANCHES CONVERGE.
    #
    # W257624, review 2026-09-26T01:49:21Z [P1], reproduced with real bytes: the
    # resumed branch treated a revoked writer plus a shared intent as permission
    # for ANY caller to perform the external act. Neither proves the previous
    # executor stopped. A second handle adopted A's intent, restored, completed
    # and released; a successor was admitted and wrote; A returned from its
    # profile and overwrote those bytes; and A's completing `transact` then
    # REPLAYED the foreign completion, so its own post-effect checks never ran
    # and it answered success. One intent, one revocation and one completion
    # record is not one external restoration.
    #
    # THE IDENTITY IS THE ONE THIS BUILD ALREADY USES for in-flight work owned by
    # one manager instance. `ControlStore.open` refuses a store that names no
    # incarnation -- "a manager instance names its incarnation" -- and
    # `offers.py` already compares `offer["incarnation"] == store.incarnation` to
    # separate its own in-flight offers from another instance's. So the executor
    # of a restoration is the incarnation that committed its intent. No lease, no
    # heartbeat, no new table.
    #
    # PLACED HERE RATHER THAN IN THE RESUMED BRANCH, and the placement is the
    # point: a caller that raced the intent transaction gets the COMMITTED
    # document back through `transact`'s replay, so it arrives here holding an
    # intent naming somebody else and is held by exactly the same rule as a
    # caller that adopted an older one.
    #
    # AND THE REFUSAL IS NON-DURABLE, because this is an unresolved execution and
    # not a failed one. Nothing journals a refused row, the committed intent
    # stands, and the exclusion stays taken -- which is the held state the owner
    # ruling requires rather than a presumption that the executor died.
    #
    # AND "NOBODY HAS POSITIVELY SETTLED IT" IS NOW A READABLE CONDITION rather than a
    # permanent one. W257624, review 2026-09-26T04:43:58Z requires a FRESH MANAGER RETRY
    # after a settlement, and this gate was what made one impossible: the committed intent
    # names the dead incarnation forever, so a new manager could never get past it. The
    # gate now asks the journal the question its own message asks -- is there an episode
    # nobody has settled -- and holds only then. Every earlier episode carrying a
    # settlement is exactly the owner ruling's condition for a retry, and the same
    # condition is re-read inside `_admitted_execution`'s transaction, so this read cannot
    # be raced into an admission.
    #
    # AN INTENT WITH NO EPISODE AT ALL also passes here, and that is not a loosening: the
    # intent commits before any episode is claimed and before the profile is reached, so
    # nothing external can have been started, and the exclusion below is still taken
    # before anything is admitted.
    unsettled = _unsettled_episodes(store, operation_id)
    if unsettled and fixed["executor_incarnation"] != store.incarnation:
        raise ContractRefusal(
            "refused", "precondition",
            f"{what}'s external restoration is in flight under manager "
            f"incarnation {name_value(fixed['executor_incarnation'])} and this "
            f"is {name_value(store.incarnation)}; episode {unsettled[0]} of it is "
            f"claimed with neither a completion nor a settlement behind it, and an "
            f"execution nobody has positively settled stays held rather than being "
            f"repeated")

    # COMPOSED FROM THE FIXED INTENT, so a resumed call and a fresh one answer
    # the same document rather than two accounts assembled from different
    # reads.
    completed = {"schema": ABANDONED_CORRECTION_SCHEMA,
                 "operation_id": operation_id,
                 "attempt_id": fixed["attempt_id"],
                 "assignment": dict(fixed["assignment"]),
                 "runtime_id": fixed["runtime_id"],
                 "retention_policy_digest": fixed["retention_policy_digest"],
                 "writer_id": fixed["writer_id"], "line_id": fixed["line_id"],
                 "checkpoint_id": fixed["checkpoint_id"],
                 "checkpoint_evidence": dict(checkpoint["evidence"]),
                 "cleanup_operation": dict(fixed["cleanup_operation"]),
                 "discharge_operation_id": fixed["discharge_operation_id"],
                 "state": _CORRECTION_READY}
    signature = _correction_signature(completed)

    # ADMISSION AND OWNERSHIP, AS ONE ACT.
    #
    # Review 2026-09-26T02:11:12Z [P1], second reproduction: a caller that had
    # completed every entry read above and then paused took the old process guard
    # AFTER a competitor had completed and released it, and ran its profile from the
    # rows it had cached. So the replay decision and the ownership decision cannot be
    # two reads with a gap -- they are made together, under one lock, from rows read
    # inside it.
    #
    # A STALE CALLER OBSERVES THE COMPLETION AND PERFORMS NO EFFECT. That is the exit
    # below, and it is the whole answer to that reproduction: the completed recovery
    # is re-read here rather than at step two only.
    # THE EXECUTION EXCLUSION IS TAKEN BEFORE ADMISSION AND HELD ACROSS THE WHOLE
    # EXTERNAL ACT. Review 2026-09-26T03:17:01Z: "no admission-before-acquire or
    # probe-and-drop gap". The lock is an operating-system observation -- the kernel
    # releases it when a holder dies -- so acquiring it is positive evidence that no
    # MANAGER holds this recovery's execution, in this process or any other, and
    # holding it means nothing slips between that evidence and the act it authorized.
    #
    # THE FILESYSTEM WORK IS OUTSIDE EVERY TRANSACTION, which is the standing ruling:
    # the lock is opened and taken here, before `_admitted_execution` opens its own
    # short transaction, and released only after the completion has committed.
    #
    # WHAT IT DOES NOT PROVE, and the refusal below does not claim it: that no external
    # work a previous executor started is still running. The profile resets through a
    # supplied runner and a runner child can outlive its manager; that is what the launch
    # account answers, and `settle_restoration_execution` now asks it under this same lock.
    with workspaces.hold_restoration_lock(_storage(store), line["line_id"],
                                          control=store) as exclusive:
        if not exclusive:
            raise ContractRefusal(
                "refused", "precondition",
                f"{what}'s restoration execution is held by another manager on this "
                f"line; one execution at a time, and an execution nobody has "
                f"positively settled stays held rather than being repeated")
        settled, episode, token = _admitted_execution(
            store, operation_id, line, writer, checkpoint, what)
        if settled is not None:
            return settled
        try:
            # THE RESTORATION ITSELF, OUTSIDE EVERY TRANSACTION.
            #
            # W257624, owner ruling 2026-09-26T01:35:02Z, which WITHDRAWS the acceptance
            # the previous shape rested on. Review 2026-09-09T16:04Z put the checkout
            # write inside `store.transact` and this code said so plainly: "`store.
            # transact` IS THE SERIALIZATION OWNER" and "THE TRADEOFF IS REAL AND IS THE
            # REVIEWER'S TO HAVE ACCEPTED: the store's write lock is held across a
            # bounded local restoration". That tradeoff is no longer available: no
            # database lock may be held across I/O other than the database's own, and a
            # read-only `stat` is I/O too. Both statements are superseded here rather
            # than left standing beside code that contradicts them.
            #
            # WHAT SERIALIZES INSTEAD IS THE EXCLUSION THE INTENT TOOK. The intent
            # revoked the writer in its own short transaction, so a second caller that
            # arrives before it races on the intent identity and `transact` replays --
            # exactly one revocation happens -- and a second caller that arrives after it
            # takes the resumed path, which is the same path a crashed restorer's retry
            # takes. The line stays `writing` throughout, so no successor can be admitted
            # while this runs.
            #
            # AND THE OVERLAP IS PREVENTED BEFORE THIS IS REACHED, which is where it
            # has to be. Review 2026-09-26T01:49:21Z [P1] reproduced the alternative
            # with real bytes: a second caller performing this act concurrently
            # overwrote an admitted successor's work and then answered success by
            # replaying a completion it had not produced. A post-effect check cannot
            # recover overwritten bytes, so the executor check above refuses a
            # non-executor at step two, before it reaches the profile at all. An
            # earlier form of this comment called that race an unclosed residual
            # needing a separate owner decision; owner 270482 had already required
            # exclusive restoration ownership, so that paragraph is WITHDRAWN rather
            # than left standing beside code that now closes it.
            #
            # WHAT IS STILL HELD RATHER THAN SOLVED: a restoration whose executor
            # incarnation is gone stays held, because an intent and a revocation are
            # not evidence that their executor stopped. Nothing in this build
            # positively settles a dead incarnation's in-flight external act; the
            # bound dossier's PLAN records supplying one as remaining scope.
            pinned = _proved_restoration_object(store, line, what)
            # THE LAUNCH ACCOUNT IS BOUND HERE, to this store, this recovery and this
            # episode, and the runner is built PER INVOCATION so nothing about it lives
            # on the profile -- review 2026-09-26T03:46:49Z [P1]. A deployment with no
            # launcher supplies no runner, the profile claims no covered lifetime, and
            # the settlement holds rather than working around the absence.
            # THE OPERAND IS PASSED ONLY WHEN THERE IS ONE, so a profile that never
            # takes it is called exactly as it always was. That keeps this optional in
            # EFFECT as well as in signature: no accepted fixture and no deployment
            # profile has to grow a parameter to keep working, which matters because
            # those fixtures are not mine to change.
            # THE ACCOUNTABLE BOUNDARY IS REQUIRED BEFORE ANY DESTRUCTIVE WORK.
            #
            # Review 2026-09-26T04:15:08Z [P1] withdraws the asymmetry I argued for. A
            # deployment that cannot account for a restoration's external work does not
            # get today's behaviour as a courtesy: unknown, no-launcher and missing
            # coverage HOLD, which 271584 and owner 271080 had already decided. And the
            # refusal is HERE, before the checkout is touched, because a restoration that
            # is performed and then cannot be released is worse than one never started.
            if launcher is None or cessation is None:
                raise ContractRefusal(
                    "refused", "capability",
                    f"{what} needs both a restoration launcher and a cessation observer "
                    f"before it writes a checkout: external work that is not recorded "
                    f"before it exists, or recorded and never asked about, can never be "
                    f"accounted for -- and an unaccountable restoration is held rather "
                    f"than performed")
            if True:
                evidence = profile.restore_checkpoint(
                    line["line_path"], checkpoint["evidence"],
                    runner=launcher(_launch_recorder(store, operation_id,
                                                     episode)))
            if evidence != checkpoint["evidence"]:
                raise ContractRefusal(
                    "integrity", "schema",
                    f"{what}'s restore answered evidence that is not the checkpoint it "
                    f"was asked to restore; a profile that changed the evidence "
                    f"restored something else")

            # THE OBSERVATION, OUTSIDE EVERY TRANSACTION and inside the exclusion this
            # call has held since before admission. `_effects_ended` refuses unless every
            # recorded launch of this episode has positively ended, so nothing below is
            # reached while external work is still running.
            accounted = _effects_ended(store, operation_id, episode, cessation, what)

            def act(connection):
                """THE RELEASE, AND NOTHING ELSE, IN ONE SHORT TRANSACTION.

                Every operand it acts on is already committed or already proved: the
                intent fixed the recovery, the restoration above performed the one
                effect, and what is left is to hand the line to a successor. So this
                holds the write lock for two statements and touches no file.

                WHAT IT RE-PROVES, and each is a pure database read. The writer is still
                revoked as THIS recovery revoked it; the line is still `writing` at the
                exact checkpoint the intent fixed; nobody at all is attached; and the
                line row still names the object the restoration was actually performed
                against. A restoration whose line has moved on releases nothing.

                AND THE REFUSALS ARE NON-DURABLE, so the transaction rolls back, no
                refused row is journalled, and the committed intent stays retryable. A
                durable refusal here would turn a transient interruption into a permanent
                one.
                """
                # FENCED TO THE EXECUTOR, so a release is written only by the instance
                # that performed the effect -- and the EPISODE CLAIM is what says which
                # instance that is, not the incarnation recorded in the intent.
                #
                # W257624, 2026-09-26: this compared `fixed["executor_incarnation"]`, which
                # names the manager that opened the recovery. Once a settlement lets a
                # FRESH manager retry, that name belongs to the dead executor forever, so
                # the comparison refused the very instance that had just performed the
                # effect -- measured, as an error in the retry case below. The token check
                # that follows is strictly stronger: a token is
                # `incarnation:pid:invocation`, so holding the claim for THIS episode
                # already proves the incarnation, the process and the individual call.
                # AND TO THE EXACT EXECUTION EPISODE, which is what makes the release
                # the act of the invocation that performed the effect rather than of
                # whoever happens to arrive holding the same incarnation.
                claimed = store.operation_record(
                    _execution_id(operation_id, episode))
                _, owner = store.replay(
                    _execution_id(operation_id, episode),
                    None if claimed is None else claimed["signature"],
                    kind=RESTORE_EXECUTION_KIND) if claimed else (False, None)
                if owner is None or owner.get("executor") != token:
                    raise ContractRefusal(
                        "refused", "precondition",
                        f"{what}'s release belongs to the executor that claimed "
                        f"episode {episode}, and this act does not hold that claim")
                # AND HOLDING THAT CLAIM IS NOT ENOUGH IF IT HAS BEEN SUPERSEDED.
                #
                # Review 2026-09-26T03:08:20Z: this checked possession of its OWN old
                # claim and nothing else, so an executor whose episode had been settled
                # and replaced by a retry still satisfied it -- and an old episode must
                # never release a line a retry now owns. Both conditions are refused: a
                # settled episode is one somebody else was told had ended, and a later
                # claimed episode is a retry in possession.
                if store.operation_record(_settled_id(operation_id, episode)) \
                        is not None:
                    raise ContractRefusal(
                        "refused", "precondition",
                        f"{what}'s execution episode {episode} was settled as ended, so "
                        f"this act may not release the line it was restoring; a "
                        f"settlement is what let somebody else take over")
                if store.operation_record(
                        _execution_id(operation_id, episode + 1)) is not None:
                    raise ContractRefusal(
                        "refused", "precondition",
                        f"{what}'s execution was superseded by episode {episode + 1}; an "
                        f"old episode does not release a line a retry now owns")
                # THE ACCOUNT IS RE-READ HERE IN PURE SQL, and it was OBSERVED outside
                # this transaction. Review 2026-09-26T04:15:08Z [P1]: the observation
                # itself used to run here, so the production observer's `killpg` and
                # `/proc` reads executed with the write lock held -- the exact rule this
                # selection exists to enforce, broken while fixing something else.
                #
                # WHAT IS COMPARED IS THE IMMUTABLE ACCOUNT. `accounted` is the launch
                # count the observation proved ended for THIS episode; if the episode's
                # recorded launches have changed since, this is not the account that was
                # observed and the release refuses. The outer exclusion is held across
                # both halves, so nothing can start between them.
                if _launch_count(store, operation_id, episode) != accounted:
                    raise ContractRefusal(
                        "refused", "precondition",
                        f"{what}'s episode {episode} recorded a launch after its effects "
                        f"were observed to have ended; the account this release rests on "
                        f"is not the account that was proved")
                settled_writer = _resumed_writer(store, attempt_id, generation, what)
                settled_line = line_of(store, line["line_id"])
                if settled_writer["writer_id"] != writer["writer_id"] \
                        or settled_line["state"] != "writing" \
                        or settled_line["current_checkpoint_id"] \
                        != checkpoint["checkpoint_id"]:
                    raise ContractRefusal(
                        "refused", "precondition",
                        f"{what}'s line no longer holds the exclusion this recovery "
                        f"was proved against; a restoration does not release a line "
                        f"whose attachment moved while it was being restored")
                _sole_attachment(store, settled_line, None, what)
                if _line_object(settled_line) != pinned:
                    raise ContractRefusal(
                        "runtime-observation", "identity-mismatch",
                        f"{what}'s line row no longer names the object this "
                        f"restoration was performed against")
                # THE SAME LINE, THE SAME CHECKPOINT AND THE SAME REVISION. Nothing
                # here freezes anything, and `current_checkpoint_id` is deliberately
                # not written: it already names this checkpoint, and writing it would
                # be this act claiming a pointer it did not move.
                connection.execute(
                    "UPDATE review_lines SET state = ? WHERE line_id = ?",
                    (_CORRECTION_READY, line["line_id"]))
                return _adopted_correction(
                    dict(completed), f"{what}'s completed recovery",
                    operation_id=operation_id, attempt_id=attempt_id,
                    assignment=fixed["assignment"])

            return store.transact(operation_id, RESTORE_KIND, signature, act)
        finally:
            # THE EPISODE IS NOT RELEASED HERE, and that distinction is the whole of
            # the settlement question. The `with` above gives this line's EXECUTION
            # exclusion back as the call leaves -- which is correct, because this
            # manager is no longer executing -- but the claimed EPISODE stays
            # UNSETTLED, because a profile exception is not evidence that the external
            # work it started has ended. Releasing the episode here would be exactly
            # the inference the review rules out; the lock and the episode answer
            # different questions and only one of them is this frame's to answer.
            pass


def _proved_coverage(owner, episode, what):
    """Refuse unless this episode's claim records the coverage it was taken under.

    W257624, review 2026-09-26T04:58:07Z [P1]. A settlement reasons from the ABSENCE of
    launch records, and absence only means "nothing started" for an executor that would
    have recorded a launch before starting it and that held the exclusion while doing so.
    An older claim carries neither fact, and its fields are identical to a current one's
    minus this provenance -- so without this check a legacy episode and a
    current-protocol crash before the first command are the same row.

    MISSING, LEGACY OR A DIFFERENT PROTOCOL VERSION IS UNKNOWN, AND UNKNOWN IS HELD. That
    is the same rule every other uncertainty in this recovery follows, and a held episode
    stays retryable the moment a supported observation exists.
    """
    recorded = {name: owner.get(name) for name in _CLAIM_COVERAGE}
    if recorded != _CLAIM_COVERAGE:
        raise ContractRefusal(
            "refused", "capability",
            f"{what}'s execution episode {episode} was claimed without recorded "
            f"coverage provenance -- it names {name_value(recorded)} rather than "
            f"{name_value(dict(_CLAIM_COVERAGE))} -- so nothing says its executor "
            f"recorded its launches before starting them or held the exclusion while it "
            f"ran; an execution whose coverage is unknown is held rather than settled")


def _settlement_label(episode, attempt):
    return f"settlement-{episode}-{attempt}"


def _retired_settlement_label(episode):
    """The FIXED label the immediately preceding implementation wrote under.

    W257624, review 2026-09-26T05:19:28Z. The attempt walk looked only at
    `settlement-<episode>-<attempt>` and never at the single `settlement-<episode>` label
    the previous cut used, so a store carrying an incomplete or still-running launch there
    was walked straight past and a fresh attempt ran beside work nobody had accounted for.
    Both formats declare the same coverage protocol, so provenance cannot tell them apart
    and recognising the label is the only honest answer.

    IT IS READ AND ACCOUNTED, NEVER WRITTEN, RENAMED OR DELETED. Those records are real
    evidence about real children; a migration or a version bump that invalidated them
    would be exactly the "reason around the evidence" this recovery is not allowed to do.
    No new attempt is ever taken under this label -- fresh attempts are always versioned --
    so it can only ever be accounted for and held on.
    """
    return f"settlement-{episode}"


def _settlement_attempt(store, recovery_id, episode, cessation, what):
    """Prove every PRIOR settlement-validation attempt stopped, then name a fresh one.

    W257624, review 2026-09-26T05:08:54Z [P2]. The settlement validated through a runner
    bound to ONE fixed label, so the first attempt that journalled a command made every
    later attempt impossible: `_launch_recorder` saw an existing account and refused its
    first intent as a recreated recorder. That refusal is right -- a launch identity is
    never reused -- but the caller offered no continuation, so an interrupted validation
    stranded the recovery permanently even after its effects had positively ended.

    SO ATTEMPTS ARE ENUMERATED AND EACH PRIOR ONE IS PROVED STOPPED. This walks the
    attempt labels in order. An attempt that launched anything must have had EVERY launch
    positively end, through the same probe as everything else; `running`, `unknown` or an
    intent with no group HOLDS, so a live own-child is never walked past. Only when it is
    accounted for does the walk advance.

    THE FRESH LABEL IS THE FIRST ONE WITH NO ACCOUNT, and that is not a blind suffix: the
    walk stopped there because every earlier attempt was proved ended, and a label with no
    launch record has no survivor to collide with -- each launch intent is committed before
    its child exists. Nothing is deleted, no identity is reused, and the recorder's
    one-time admission is untouched, because the recorder for this label is seeing its
    first launch.

    ANSWERS the label this attempt owns and the accounts of the attempts before it, which
    the settlement binds into its decision and revalidates in its writing transaction.
    """
    prior = []
    # THE RETIRED FIXED LABEL FIRST, because a store may carry an account under it and
    # nothing else would ever look. It is accounted on exactly the same terms as any other
    # attempt -- incomplete, running or unknown HOLDS -- and it is never chosen as a fresh
    # attempt, so its records are read and kept rather than written over.
    retired = _retired_settlement_label(episode)
    if _launch_count(store, recovery_id, retired):
        prior.append({"attempt": retired,
                      "launches": _effects_ended(store, recovery_id, retired,
                                                 cessation, what)})
    attempt = 1
    while True:
        label = _settlement_label(episode, attempt)
        if _launch_count(store, recovery_id, label) == 0:
            return label, prior
        prior.append({"attempt": label,
                      "launches": _effects_ended(store, recovery_id, label,
                                                 cessation, what)})
        attempt += 1


def settle_restoration_execution(store, *, attempt_id, generation, profile,
                                 cessation, launcher):
    """Record that an interrupted restoration's execution has POSITIVELY ended.

    W257624, owner ruling 2026-09-26T02:57:40Z, and ENABLED here for the first time
    (review 2026-09-26T04:43:58Z: "implement supported settlement under pinned
    exclusion"). A claimed execution episode with no completion behind it holds every
    later caller, deliberately: an exception is not evidence that a checkout stopped
    being written. This is the only other exit, and it requires BOTH halves of what
    ending an execution means, each OBSERVED BY THIS MANAGER rather than asserted to it.

    THE EXECUTOR HALF IS THE KERNEL'S ANSWER, NOT A CALLER'S DOCUMENT. Review
    2026-09-26T03:08:20Z [P1] reproduced a settlement obtained about a LIVE executor from
    a caller-authored attestation read out of the journal, and the `ended` operand that
    carried it is GONE from this signature. What stands in its place is the exclusive
    advisory lock this recovery's execution is performed under: a living manager holds it
    for the whole span of its external act, and the kernel releases it when that process
    dies. So ACQUIRING it here is a positive observation that no manager -- in this
    process or any other -- still holds this line's restoration execution. Failing to
    acquire it means an executor is alive, and this refuses NON-DURABLY: the episode stays
    claimed and nothing is admitted.

    THE EFFECTS HALF IS TWO OBSERVATIONS, BOTH OUTSIDE EVERY TRANSACTION, because they
    are external I/O and the standing ruling forbids holding a database lock over it:

    - EVERY LAUNCH THIS EPISODE RECORDED must have positively ended, through the same
      account and the same probe the normal completion is gated on. A manager can die
      while a child of its runner lives on; the lock says nothing about that child, and
      an unresolved or `unknown` child HOLDS.
    - THE CHECKOUT IS CLEAN AT THE RETAINED CHECKPOINT, which is what "the effects are
      accounted for" means for a working tree: the interrupted restoration either
      completed its intended effect or left nothing of its own behind. A half-restored
      tree is exactly the state a retry must not be let loose on.

    AN EPISODE THAT RECORDED NO LAUNCH AT ALL IS SETTLEABLE HERE, and only here. Each
    launch intent is committed BEFORE its child exists, so an empty account means no
    child was ever started -- an executor that died between claiming the episode and its
    first command. Combined with the lock, that is a complete account of nothing having
    happened. On the completion path the same emptiness means a profile ran and recorded
    nothing, which is not an account and holds.

    THE ACCOUNT AND THE OWNERSHIP ARE REVALIDATED IN THE WRITING TRANSACTION, in pure
    SQL: the line still names the object the validation was performed against, no
    completion arrived, the claim row is still the one that was read, and the episode's
    recorded launches are still the ones that were observed. The observations happened
    outside the lock the write takes, so the write refuses if anything moved under them.

    IT SETTLES ONE EPISODE AND DECIDES NOTHING ELSE. No completion is written, no line
    state moves, no writer is revoked or restored and no successor is admitted -- the
    retry this permits is an ordinary `restore_abandoned_correction` that takes the next
    episode through the ordinary admission, and it may be performed by a FRESH manager
    because a settled episode is what releases the executor-incarnation hold.
    """
    attempt_id, generation = _requested_pair(attempt_id, generation)
    what = (f"the abandoned correction for attempt {name_value(attempt_id)} "
            f"generation {generation}")
    # THE OBSERVER IS MANDATORY, refused before anything is read. A settlement without a
    # cessation probe could only ever guess about the children a dead executor's runner
    # forked, and owner 271080 holds that unaccountable recovery is held rather than
    # performed. This is the same rule `restore_abandoned_correction` applies to its own
    # boundary operands.
    if not callable(cessation) or not callable(launcher):
        raise ContractRefusal(
            "refused", "capability",
            f"{what}'s execution cannot be settled without a cessation observer and a "
            f"launcher: the kernel answers whether a MANAGER still holds the execution, "
            f"nothing else answers whether the children its runner forked have ended, and "
            f"the settlement's OWN validation commands need the same account as anybody "
            f"else's, so an unaccountable execution is held rather than settled")
    profile_name = _profile(profile, ("validate",))
    recovery_id = _restore_operation_id(RESTORE_KIND, attempt_id, generation)
    if store.operation_record(recovery_id) is not None:
        raise ContractRefusal(
            "refused", "precondition",
            f"{what} is already completed; a completed recovery needs no execution "
            f"settlement and replays through its own record")
    claimed = _claimed_episodes(store, recovery_id)
    if not claimed:
        raise ContractRefusal(
            "refused", "precondition",
            f"{what} has claimed no execution episode; there is no execution here to "
            f"settle")
    episode = len(claimed)
    held = _settled_id(recovery_id, episode)
    recorded = store.operation_record(held)
    _, owner = store.replay(_execution_id(recovery_id, episode),
                            claimed[-1]["signature"],
                            kind=RESTORE_EXECUTION_KIND)
    if owner is None:
        raise ContractRefusal(
            "integrity", "schema",
            f"{what}'s execution episode {episode} has no recorded claim to replay")
    if recorded is not None:
        # AN EXACT REPLAY ANSWERS ITS COMMITTED RECORD (§4.2) AND OBSERVES NOTHING. A
        # settled episode is settled; re-probing would re-run external I/O for a decision
        # already journalled, and a second observation could only disagree with the
        # record it cannot change.
        _, answered = store.replay(held, recorded["signature"],
                                   kind=RESTORE_SETTLED_KIND)
        return answered
    intent = _restore_operation_id(RESTORE_INTENT_KIND, attempt_id, generation)
    fixed = store.operation_record(intent)
    if fixed is None:
        raise ContractRefusal(
            "integrity", "schema",
            f"{what} claimed an execution episode with no recovery intent behind it")
    _, committed = store.replay(intent, fixed["signature"],
                                kind=RESTORE_INTENT_KIND)
    if committed is None:
        raise ContractRefusal(
            "integrity", "schema",
            f"{what}'s recovery intent has no recorded answer to replay")
    line = line_of(store, committed["line_id"])
    if line["profile_name"] != profile_name:
        raise ContractRefusal(
            "policy", "profile-uncertified",
            f"{what}'s line was materialized by profile "
            f"{name_value(line['profile_name'])} and this settlement offers "
            f"{name_value(profile_name)}")
    pinned = _proved_restoration_object(store, line, what)
    checkpoint = checkpoint_of(store, committed["checkpoint_id"])
    # THE EXECUTOR HALF. The lock is taken NON-BLOCKING and held across both effect
    # observations and the write, so nothing slips between the evidence and the decision
    # it authorizes -- the same discipline the restoration itself follows, under the same
    # pinned lock object beside the same line.
    with workspaces.hold_restoration_lock(_storage(store), line["line_id"],
                                          control=store) as exclusive:
        if not exclusive:
            raise ContractRefusal(
                "refused", "precondition",
                f"{what}'s restoration execution is still held by a manager on this "
                f"line, which is the kernel's answer that its executor is alive; an "
                f"execution in flight is not settled and stays held")
        # THE COVERAGE THIS EPISODE WAS CLAIMED UNDER, read before its account is
        # believed. Review 2026-09-26T04:58:07Z [P1]: absence of launch records only
        # means "nothing started" for an executor that records before it starts.
        _proved_coverage(owner, episode, what)
        # THE EFFECTS HALF, OUTSIDE EVERY TRANSACTION and inside the exclusion.
        accounted = _effects_ended(store, recovery_id, episode, cessation, what,
                                   unlaunched_is_settled=True)
        # THE RETAINED INPUT OBJECT, NOT A SUCCESSFUL RESTORATION.
        #
        # Review 2026-09-26T04:58:07Z [P2]. This asked for `current=True`, which is a
        # CLEAN WORKTREE at the checkpoint -- so an execution whose effects had all ended
        # but which stopped half way through its reset could never be settled, and never
        # retried either: the one state a retry exists for was the one state that
        # permanently refused. Cessation and the identity of the retained checkpoint are
        # separate questions from whether a restoration succeeded, and only the first two
        # belong here. The RETRY resets the tree and ITS completion validates clean, so
        # nothing is released on a half-restored checkout by this change.
        #
        # AND THIS SETTLEMENT'S OWN COMMANDS ARE ACCOUNTED, under their own episode label
        # beside the executor's. Validation runs commands; running them through the
        # constructor runner would have put unaccounted external work right after the
        # account was observed, which is the hole the accounting exists to close, and
        # "they are only reads" is exactly the assumption that was wrong before.
        # EVERY PRIOR SETTLEMENT ATTEMPT ACCOUNTED FOR BEFORE A NEW ONE IS NAMED.
        own_episode, prior_attempts = _settlement_attempt(
            store, recovery_id, episode, cessation, what)
        validated = profile.validate(
            line["line_path"], checkpoint["evidence"],
            runner=launcher(_launch_recorder(store, recovery_id, own_episode)))
        if validated != checkpoint["evidence"]:
            raise ContractRefusal(
                "integrity", "schema",
                f"{what}'s settlement validated evidence that is not the checkpoint "
                f"this recovery is about; effects are accounted for against the "
                f"checkpoint the restoration was for and not against another")
        # AND ITS OWN CHILDREN MUST HAVE ENDED TOO, asked with the same probe. A
        # settlement that left its own validation running would be the same defect it is
        # here to close, one caller along.
        own_accounted = _effects_ended(store, recovery_id, own_episode, cessation, what,
                                       unlaunched_is_settled=True)
        observed = {"exclusion": "acquired", "launches": accounted,
                    "settlement_attempt": own_episode,
                    "settlement_launches": own_accounted,
                    "prior_settlement_attempts": [dict(one) for one in prior_attempts],
                    "coverage": RESTORE_ACCOUNTING_PROTOCOL,
                    "effects": "retained-checkpoint-identity"}
        document = {"schema": ABANDONED_CORRECTION_SCHEMA,
                    "recovery": recovery_id, "episode": episode,
                    "executor": owner["executor"], "ended": dict(observed),
                    "line_id": line["line_id"],
                    "checkpoint_id": checkpoint["checkpoint_id"],
                    "checkpoint_digest": checkpoint["checkpoint_digest"],
                    "line_object": list(pinned)}
        signature = manager_signature(RESTORE_SETTLED_KIND, document)

        def act(connection):
            # EVERY OBSERVATION REVALIDATED IN PURE SQL, because each was made outside
            # the lock this write holds.
            current = line_of(store, line["line_id"])
            if _line_object(current) != pinned:
                raise ContractRefusal(
                    "runtime-observation", "identity-mismatch",
                    f"{what}'s line row no longer names the object this settlement's "
                    f"validation was performed against")
            if store.operation_record(recovery_id) is not None:
                raise ContractRefusal(
                    "refused", "precondition",
                    f"{what} completed while its execution was being settled; a "
                    f"completed recovery needs no settlement")
            still = store.operation_record(_execution_id(recovery_id, episode))
            if still is None or still["signature"] != claimed[-1]["signature"]:
                raise ContractRefusal(
                    "runtime-observation", "identity-mismatch",
                    f"{what}'s execution episode {episode} is no longer the claim this "
                    f"settlement observed; an execution is settled for the executor "
                    f"that claimed it and not for a later one")
            if _launch_count(store, recovery_id, own_episode) != own_accounted:
                raise ContractRefusal(
                    "refused", "precondition",
                    f"{what}'s settlement recorded a launch of its own after its "
                    f"validation was observed, so its own account is no longer complete")
            # AND EVERY EARLIER ATTEMPT'S ACCOUNT, because the decision is bound to ALL of
            # them: an attempt proved stopped outside this transaction must still be the
            # account that was proved when the row that rests on it is written.
            for one in prior_attempts:
                if _launch_count(store, recovery_id,
                                 one["attempt"]) != one["launches"]:
                    raise ContractRefusal(
                        "refused", "precondition",
                        f"{what}'s earlier settlement attempt {one['attempt']} recorded a "
                        f"launch after it was proved stopped, so this decision no longer "
                        f"covers the work it rests on")
            if _launch_count(store, recovery_id, episode) != accounted:
                raise ContractRefusal(
                    "refused", "precondition",
                    f"{what}'s episode {episode} recorded a launch after its effects "
                    f"were observed, so the account this settlement rests on is no "
                    f"longer complete and it is held rather than settling work it "
                    f"never examined")
            return dict(document)

        return store.transact(held, RESTORE_SETTLED_KIND, signature, act)


def integration_checkpoint(store, line_id):
    line = line_of(store, line_id)
    eligibility_row = store._connection.execute(
        "SELECT * FROM integration_eligibility WHERE line_id = ?", (line_id,)
    ).fetchone()
    if eligibility_row is None:
        return None
    owned = boundaries.row(eligibility_row, "persisted integration eligibility",
                           schema.INTEGRATION_ELIGIBILITY_COLUMNS)
    checkpoint = checkpoint_of(store, owned["checkpoint_id"])
    evidence = checkpoint["evidence"]
    if owned["line_id"] != line_id or line["state"] != "accepted" \
            or checkpoint["line_id"] != line_id \
            or checkpoint["state"] != "frozen" \
            or checkpoint["checkpoint_id"] != line["current_checkpoint_id"]:
        raise ContractRefusal("integrity", "schema",
                              "integration eligibility is not the line's accepted checkpoint")
    verdict = _verdict_row(store, owned["verdict_id"])
    if verdict is None:
        raise ContractRefusal("integrity", "schema",
                              "integration eligibility has no exact accepted verdict")
    verdict["review_result"] = _review_result(
        json.loads(verdict["review_result"]))
    verdict["review_fence"] = _fence(
        json.loads(verdict["review_fence"]), "a persisted review fence")
    recorded = (verdict["line_id"], verdict["checkpoint_id"],
                verdict["authority_uuid"], verdict["work_id"],
                verdict["disposition"], verdict["checkpoint_digest"],
                verdict["revision"], verdict["base_object"],
                verdict["head_object"], verdict["tree_object"],
                verdict["path_set_digest"])
    expected = (line_id, checkpoint["checkpoint_id"], line["authority_uuid"],
                line["work_id"], "accepted", checkpoint["checkpoint_digest"],
                checkpoint["revision"], evidence["base"], evidence["head"],
                evidence["tree"], evidence["path_set_digest"])
    if recorded != expected \
            or verdict["review_result_digest"] != digest(verdict["review_result"]) \
            or verdict["review_fence_digest"] != digest(verdict["review_fence"]):
        raise ContractRefusal("integrity", "digest",
                              "integration eligibility has no exact accepted verdict")
    verdict = verdict_of(store, verdict["verdict_id"])
    attachment = review_of(store, verdict["attachment_id"])
    attempt, current_result = _completed_review(store, attachment, verdict=verdict)
    _current_fence(store, attempt, verdict["review_fence"],
                   "the persisted review fence")
    if attachment["state"] != "ended" \
            or attachment["assignment_generation"] != verdict["review_assignment_generation"] \
            or attachment["reviewer_worker_id"] != verdict["reviewer_worker_id"] \
            or attachment["reviewer_participant"] != verdict["reviewer_participant"] \
            or attachment["reviewer_principal"] != verdict["reviewer_principal"] \
            or attempt["assignment_generation"] != verdict["review_assignment_generation"] \
            or current_result != verdict["review_result"]:
        raise ContractRefusal(
            "integrity", "schema",
            "integration eligibility is not bound to its completed review attempt")
    return {"line_id": line_id, "checkpoint_id": owned["checkpoint_id"],
            "verdict_id": owned["verdict_id"],
            "checkpoint_digest": checkpoint["checkpoint_digest"],
            "evidence": checkpoint["evidence"]}


def audit_checkpoint(store, checkpoint_id, profile):
    """Re-resolve an older immutable checkpoint without requiring current HEAD."""
    profile_name = _profile(profile, ("validate",))
    checkpoint = checkpoint_of(store, checkpoint_id)
    if checkpoint["state"] != "frozen":
        raise ContractRefusal("refused", "precondition",
                              "only a frozen checkpoint is audit evidence")
    line = line_of(store, checkpoint["line_id"])
    if line["profile_name"] != profile_name:
        raise ContractRefusal("policy", "profile-uncertified",
                              "the line and audit profile do not match")
    return profile.validate(line["line_path"], checkpoint["evidence"],
                            current=False)


def line_status(store, line_id, storage_usage):
    """Operator status including externally metered accumulated line storage."""
    boundaries.capability(storage_usage,
                          "the deployment's development-line storage meter")
    line = line_of(store, line_id)
    usage = storage_usage(line["line_path"])
    if (type(usage) is not dict or set(usage) != {"bytes", "entries"}
            or any(type(value) is not int or type(value) is bool or value < 0
                   for value in usage.values())):
        raise ContractRefusal("integrity", "schema",
                              "line storage usage is exact non-negative bytes and entries")
    return {"line_id": line_id, "state": line["state"],
            "revision": line["revision"],
            "current_checkpoint_id": line["current_checkpoint_id"],
            "storage": dict(usage)}


def _writer_grant(store, writer_id, line_id, generation):
    writer = writer_of(store, writer_id)
    line = line_of(store, line_id)
    return (writer["line_id"] == line_id and writer["state"] == "active"
            and writer["assignment_generation"] == generation
            and line["state"] == "writing")


def _writer_access(store, writer_id, generation, roots, gid, labels):
    """Bind actual launch roots to the current durable writer and assignment."""
    writer = writer_of(store, writer_id)
    line = line_of(store, writer["line_id"])
    assignment = assignment_of(store, writer["runtime_attempt_id"])
    _same_assignment(assignment, line, generation)
    if (not _writer_grant(store, writer_id, line["line_id"], generation)
            or writer["participant"] != assignment["participant"]
            or writer["principal"] != assignment["principal"]
            or any(labels.get(name) != value for name, value in assignment.items())
            or gid != workspaces.configured_workspace_group(store).gid):
        raise ContractRefusal("stale-assignment", "generation",
                              "the launch is not this development line's current writer assignment")
    _validate_line_object(line)
    expected = workspaces.line_assignment_workspace(
        _storage(store), writer["runtime_attempt_id"], line["line_path"],
        (line["line_device"], line["line_inode"]), control=store)
    if dict(roots) != dict(expected):
        raise ContractRefusal("runtime-observation", "identity-mismatch",
                              "the actual launch roots differ from the durable writer line")
    return workspaces._prove_line_access(
        roots["workspace"], (line["line_device"], line["line_inode"]), gid)


def consumption_subject(store, *, attempt_id, generation):
    """WHICH line this attempt may be consumed from, resolved from durable
    state and from nothing else.

    W105982. The defect this exists for is a subject defect rather than a
    permission one: `custody._derived_root` addresses `S/<attempt>/workspace`
    while a writer attempt was mounted at `S/.baton-review-lines/<line>/
    checkout`, so an ordinary receipt was accurate about directories that had
    nothing to do with the tree the manager actually read. Naming the right
    tree is therefore the whole of this function.

    RESOLVED, NOT ACCEPTED. Nothing here takes a host path from a caller and
    nothing consults an adapter's held root map -- `AllocatedRoots` disclaims
    being durable authority in its own words, and a map composed at launch is
    a memory of what was true then. The chain is entirely inside the control
    store: this attempt's ACTIVE writer at this exact generation, that writer's
    line, the assignment the line is bound to, and the object identity the line
    recorded when it was materialized.

    THE CUSTODY SIBLING IS DERIVED THE SAME WAY. It is the parent of the line
    checkout plus `custody/<attempt>`, which is what `OciAdapter._home` reaches
    by taking the dirname of a mounted workspace -- the difference being that
    this one is computed from the RECORDED line path, so a comparison against
    the adapter's own answer is a comparison of two independent derivations
    rather than of one value with itself.

    EXCLUSIVITY IS ALREADY THE SCHEMA'S. `line_one_active_writer` makes a
    second active writer per line impossible, so this asks the question it can
    actually answer -- which line is THIS attempt's -- and does not re-count
    what the store cannot let happen. The caller is expected to ask again after
    its filesystem proof: this answers what is true now, and the interval
    between two reads is exactly where a fence belongs.
    """
    boundaries.identity(attempt_id, "a runtime attempt identity")
    boundaries.generation(generation, "an assignment generation")
    rows = store._connection.execute(
        "SELECT writer_id FROM line_writers WHERE runtime_attempt_id = ? "
        "AND assignment_generation = ? AND state = 'active'",
        (attempt_id, generation)).fetchall()
    if len(rows) != 1:
        raise ContractRefusal(
            "refused", "precondition",
            f"attempt {name_value(attempt_id)} holds {len(rows)} active line "
            f"writers at generation {generation}; consumption names exactly "
            f"the one line a live writer was granted")
    # THE COLUMN IS NOT OWNED HERE. `writer_of` is the one crossing out of
    # this table and it owns the identity and the row; a second owner for the
    # same value is exactly what the boundary inventory refuses.
    writer = writer_of(store, rows[0]["writer_id"])
    line = line_of(store, writer["line_id"])
    if line["state"] != "writing":
        raise ContractRefusal(
            "refused", "precondition",
            f"development line {name_value(line['line_id'])} is "
            f"{name_value(line['state'])}; only the line its own live writer "
            f"is still writing may be consumed for that writer's result")
    # EXCLUSIVITY IS NOT RE-ASKED HERE. `line_one_active_writer` is a UNIQUE
    # INDEX over `line_writers(line_id) WHERE state = 'active'`, so a second
    # active writer cannot exist to be counted -- and a count that can never
    # come back other than one is a boundary nobody reaches. The dependency is
    # not left implicit: a case pins that the schema carries the rule, so if it
    # ever stops, the gate says so.
    assignment = assignment_of(store, attempt_id)
    _same_assignment(assignment, line, generation)
    # AND THE GRANT'S OWN IDENTITIES, which `_same_assignment` does not reach.
    # W105982 candidate review 2026-09-07: Authority, Work and generation can
    # all agree while the attempt's assignment names a different participant or
    # principal from the one the writer was granted to -- and the accepted
    # launch boundary `_writer_access` already requires both equalities, so a
    # consumption gate that did not would authorize a subject the launch would
    # have refused.
    if writer["participant"] != assignment["participant"] \
            or writer["principal"] != assignment["principal"]:
        raise ContractRefusal(
            "stale-assignment", "generation",
            "the granted writer and this attempt's current assignment name "
            "different participants or principals; consumption follows the "
            "grant rather than the row that happens to share its generation")
    _validate_line_object(line)
    home = os.path.dirname(line["line_path"].rstrip("/"))
    return {"attempt_id": attempt_id, "generation": generation,
            "writer_id": writer["writer_id"], "line_id": line["line_id"],
            "line_path": line["line_path"],
            "pinned": (line["line_device"], line["line_inode"]),
            "custody_path": os.path.join(home, "custody", attempt_id),
            "storage": _storage(store)}


def writer_boundary(store, *, writer_id, generation):
    """Compose the direct writable line mount for the active writer attempt."""
    boundaries.generation(generation, "an assignment generation")
    writer = writer_of(store, writer_id)
    line = line_of(store, writer["line_id"])
    if writer["state"] != "active" or writer["assignment_generation"] != generation:
        raise ContractRefusal("stale-assignment", "generation",
                              "only the active writer generation mounts the line writable")
    assignment = assignment_of(store, writer["runtime_attempt_id"])
    _same_assignment(assignment, line, generation)
    _validate_line_object(line)
    nominated = source_boundary.nominate_source(line["source_path"])
    if (nominated.device, nominated.inode) != (line["source_device"],
                                               line["source_inode"]):
        raise ContractRefusal("runtime-observation", "identity-mismatch",
                              "the nominated source pathname now names another object")
    roots = workspaces.line_assignment_workspace(
        _storage(store), writer["runtime_attempt_id"], line["line_path"],
        (line["line_device"], line["line_inode"]), control=store)
    roots = workspaces._granted_roots(
        roots, lambda: _writer_grant(store, writer_id,
                                     line["line_id"], generation),
        line_proof=lambda actual, gid, labels: _writer_access(
            store, writer_id, generation, actual, gid, labels))
    return {"roots": roots,
            "boundary": source_boundary.compose_runtime_storage_boundary(
                nominated, roots)}


def _review_grant(store, attachment_id, line_id, checkpoint_id):
    attachment = _attachment(store, attachment_id)
    line = line_of(store, line_id)
    return (attachment["line_id"] == line_id
            and attachment["checkpoint_id"] == checkpoint_id
            and attachment["state"] == "active"
            and line["state"] == "reviewing"
            and line["current_checkpoint_id"] == checkpoint_id)


def review_boundary(store, *, attachment_id, profile):
    """Compose read-only current-checkpoint input and separate review output."""
    profile_name = _profile(profile, ("validate",))
    attachment = _attachment(store, attachment_id)
    line = line_of(store, attachment["line_id"])
    if attachment["state"] != "active" or line["state"] != "reviewing":
        raise ContractRefusal("refused", "precondition",
                              "only the active review attachment mounts a checkpoint")
    if store._connection.execute(
            "SELECT 1 FROM line_writers WHERE line_id = ? AND state = 'active'",
            (line["line_id"],)).fetchone() is not None:
        raise ContractRefusal("integrity", "schema",
                              "a read-only review checkpoint has an active writer")
    checkpoint = checkpoint_of(store, attachment["checkpoint_id"])
    if line["profile_name"] != profile_name:
        raise ContractRefusal("policy", "profile-uncertified",
                              "the line and review-mount profile do not match")
    if checkpoint["line_id"] != line["line_id"] \
            or checkpoint["state"] != "frozen" \
            or line["current_checkpoint_id"] != checkpoint["checkpoint_id"]:
        raise ContractRefusal("integrity", "schema",
                              "the review mount is not the line's current checkpoint")
    profile.validate(line["line_path"], checkpoint["evidence"], current=True)
    roots = workspaces.adopted_assignment_workspace(
        _storage(store), attachment["runtime_attempt_id"], control=store)
    roots = workspaces._granted_roots(
        roots, lambda: _review_grant(
            store, attachment_id, line["line_id"], checkpoint["checkpoint_id"]))
    nominated = source_boundary.nominate_source(line["line_path"])
    if (nominated.device, nominated.inode) != (line["line_device"],
                                               line["line_inode"]):
        raise ContractRefusal("runtime-observation", "identity-mismatch",
                              "the review checkpoint line is no longer its recorded object")
    return {"roots": roots,
            "boundary": source_boundary.compose_runtime_storage_boundary(
                nominated, roots)}
