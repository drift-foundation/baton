"""Independent review and same-line correction, driven from durable state.

W103076, `work/records/2026/09/finding-v12-standalone-multi-job-pipeline/
findings/finding-standalone-stage-composition/findings/
finding-review-correction-driver/`.

WHAT WAS MISSING, AND IT WAS NOT A COMPONENT. Every operation this module
calls already exists and is accepted: `review_cycles` owns the development
line, its generation-fenced writer, the immutable checkpoint, the independent
reviewer attachment and the verdict; `attempts`, `exchange` and the retention
operations own an attempt's ending; `PooledManagerOperations` owns reviewer
independence. What did not exist is anything that CALLS them in order. The
control plane's own `delegation` module says so in its own words -- freezing
an output, deciding a verdict and importing a proposal "exist and are not
called from here" -- and the only production composition ends an
implementation attempt by handing its frozen result to a v11 review Route.
This module is the missing half for the review side of one Job.

IT IS PROVIDER-NEUTRAL, WHICH IS WHY IT LIVES HERE AND NOT IN `tools/`. Every
capability it needs -- the runtime adapter, the authority-bound port, the
profile, the publication seam -- is an operand. It opens no store, reads no
environment variable, names no image and chooses no worker. Which container
runs and under whose credentials is W103083's, and a module that decided it
would be a second deployment.

THE ORDER IS THE RULING'S. The ending of an implementation attempt is seven
steps whose order was settled by W44657 and re-settled by W81857's review, and
this module changes exactly one of them: where single_worker passes the frozen
result to a v11 Route, this passes it to the publication seam and then fences
the writer into an immutable checkpoint. Everything before that is unchanged,
because the reasons are unchanged -- intake races an ended assignment,
`authorize_cleanup` refuses while the assignment is live, and a freeze takes a
POSITIVELY quiescent runtime rather than an absent one.

AND PUBLICATION HAPPENS WHILE THE PRODUCER IS STILL LIVE. W103068's review
measured this and kept the reproduction: `freeze_checkpoint` finalizes and
fences the writer's Authority assignment, and `Authority.publish` requires the
exact live producer assignment, so a publication attempted after the freeze
refuses with `assignment generation was fenced and ended`. The seam is
therefore called BEFORE the fence. Acceptance of the resulting checkpoint later
controls receipts and queue admission; it does not create the proposal
retroactively.

WHAT THIS MODULE WILL NOT DO. It does not publish -- it calls the seam W103077
owns and keeps none of that leaf's operands. It does not admit, rank, lease or
integrate anything. It does not decide policy: a `rejected`, ambiguous, stale
or unreadable review is HELD, and holding means scheduling nothing rather than
choosing something safe-looking. And it starts no runtime; it prepares what a
runtime will mount and it ends what a runtime produced.
"""

from ..contracts import ContractRefusal
from ..contracts.errors import name_value
from ..worker_manager import (attempts, authorize_cleanup, boundaries,
                              decide_retention, frozen_output_of,
                              load_manifest, observe, reconcile_runtime,
                              request_freeze, request_intake,
                              review_cycles)
from . import episodes

__all__ = ["ADAPTER_IDENTITIES", "FENCE_PORT", "FINDINGS_OUTPUT",
           "IMPLEMENTATION_ENDING", "IMPLEMENTATION_PROFILE",
           "LOGS_OUTPUT", "PUBLICATION_SEAM", "REVIEW_CLAIM_MEMBERS",
           "REVIEW_CLAIM_NAMESPACE", "REVIEW_ENDING",
           "REVIEW_PROFILE", "REVIEW_RESULT_ENDING", "RUNTIME_ADAPTER",
           "VERDICT_OUTCOMES", "end_implementation", "end_review",
           "end_review_from_result", "open_correction",
           "prepare_implementation", "prepare_review",
           "review_verdict_from_result"]

# THE SEAM ONTO W103077, AND IT IS ONE VERB. `publish` is handed the frozen
# producer account and answers with the published proposal. A second verb here
# would be this module deciding part of a lifecycle the integration driver
# owns; a seam with none would be this module publishing.
PUBLICATION_SEAM = ("publish",)

# THE RUNTIME ADAPTER'S SURFACE, TYPED BEFORE THE FIRST EXTERNAL ACT. Review
# [P1]: only the seam was typed, so an adapter carrying `stop` and nothing else
# was ASKED TO STOP a container and only then discovered to be unusable by
# `reconcile_runtime` -- and a missing method arrived as a raw AttributeError
# rather than a refusal. These four are what an ending reaches, through this
# module and through the operations it composes, and all four are proved while
# nothing has happened yet.
RUNTIME_ADAPTER = ("stop", "list", "observe", "seal", "collect", "retain",
                   "destroy", "normalize_directory",
                   # W105982: the actual-line consumption gate. Typed with
                   # the rest and for the same reason -- it runs BEFORE the
                   # first completion read, so an adapter that cannot
                   # perform it must say so before the stop rather than
                   # after it.
                   "prove_line_consumable")

# The one adapter member that is an IDENTITY rather than a verb. Retention and
# cleanup bind the custodian that performed them, so an adapter that cannot say
# which custodian it is fails those acts after the freeze.
ADAPTER_IDENTITIES = ("custodian_image_digest",)

# And the authority-bound port's. `participant` is an attribute and the other
# two are verbs; the freeze, the intake, the retention, the cleanup and the
# fence all reach one of them, so a port missing any fails somewhere in the
# middle of an ending rather than before it starts.
FENCE_PORT = ("assignment_of", "cancel")

# What each ending needs its checkpoint profile to be able to do. The
# implementation ending freezes a checkpoint; the review ending only validates
# one. They are named separately because typing the review ending against the
# writer's surface would refuse a perfectly good review profile.
IMPLEMENTATION_PROFILE = ("freeze", "validate")
REVIEW_PROFILE = ("validate",)

# The ordered steps of an implementation ending, written down because the
# order is a ruling rather than an implementation choice, and because a test
# that asserts an order needs something to assert it against.
IMPLEMENTATION_ENDING = ("quiesce", "observe", "consume", "freeze",
                         "correlate", "intake", "retain", "publish",
                         "checkpoint", "cleanup")

# The same for a review ending. It has no publication and no checkpoint: what
# it produces is a verdict about somebody else's checkpoint.
REVIEW_ENDING = ("quiesce", "observe", "freeze", "intake", "retain",
                 "verdict", "cleanup")

# AND THE SAME ENDING WHEN THE VERDICT IS READ RATHER THAN SUPPLIED.
# W110772 adds exactly two steps: the terminal correlation the
# implementation ending already performs, and the resolution of the
# reviewer's own claim out of the result this ending just froze.
REVIEW_RESULT_ENDING = ("quiesce", "observe", "freeze", "correlate",
                        "intake", "retain", "resolve", "verdict",
                        "cleanup")

# What this module answers with after a verdict, and it is deliberately not
# the verdict vocabulary. `accepted` hands a producer account on, `correction`
# says a round is owed in the Job store, and `held` is every outcome this
# module refuses to act on by itself.
VERDICT_OUTCOMES = ("accepted", "correction", "held")

# WHICH REFUSALS FROM THE VERDICT ARE EVIDENCE RATHER THAN PROGRAMMING. Review
# [P1]: the contract says stale, ambiguous or unreadable review evidence
# returns the explicit `held` outcome, and every such refusal escaped instead.
# These are the categories the custody provider raises ABOUT WHAT IT READ; a
# malformed argument is caught before the ending starts and is not one of them.
_EVIDENCE_REFUSALS = ("refused", "integrity", "policy", "stale-assignment",
                      "runtime-observation", "ambiguous")

# AND THE ONE THAT DELIBERATELY ESCAPES. `unavailable` says a transport or an
# authority did not answer, which is a statement about infrastructure rather
# than about the review; retrying it is right and reporting it as an ending
# that finished in some outcome would be wrong.
#
# `ambiguous` IS HELD, and the round that argued otherwise was overruled. The
# reasoning -- that nobody can say whether the operation committed, so no
# outcome should be reported -- describes exactly the condition this leaf's
# pinned contract calls held: evidence an operator has to look at, with nothing
# advanced and nothing cleaned up. An implementation paragraph is not a
# supersession of a confirmed contract, which is the more useful half of the
# correction.

# Which dispositions are held rather than driven, and why each one is.
_HELD_REASONS = {"rejected": "a rejected checkpoint is a decision about the "
                             "Work and not a round to schedule"}


def _refuse(message, *, category="refused", code="precondition"):
    raise ContractRefusal(category, code, message)


def _seam(value):
    """The publication seam, typed before anything is spent on it."""
    for verb in PUBLICATION_SEAM:
        boundaries.capability(getattr(value, verb, None),
                              f"the integration publication seam's {verb}")
    return value


def _typed(adapter, port, profile, needs):
    """Every capability an ending will reach, proved before it reaches one.

    REVIEW [P1], TWICE. THE ORDER OF DISCOVERY IS PART OF THE CONTRACT: a
    composite that finds out halfway through that it cannot finish has already
    stopped somebody's container, and the refusal it eventually raises
    describes the wrong moment. The first correction typed four adapter verbs
    and the presence of a participant, which left `collect`, `retain`,
    `destroy`, `normalize_directory`, the custodian identity, both port verbs
    and the profile to be discovered after the stop.

    THE WHOLE SURFACE IS NAMED HERE, and it is the union of what this module
    calls and what the operations it composes call: the freeze seals, intake
    collects, retention retains and normalizes and binds a custodian, cleanup
    destroys, and the Authority acts go through the port. `needs` is the
    profile surface THIS ending uses, because the two endings do not use the
    same one.
    """
    for verb in RUNTIME_ADAPTER:
        boundaries.capability(getattr(adapter, verb, None),
                              f"the runtime adapter's {verb}")
    for member in ADAPTER_IDENTITIES:
        # OWNED AS TEXT, NOT MERELY NON-NULL. Third review [P1]: the custody
        # boundary takes this as text and signs an act with it, so a non-null
        # value of any other shape passed here and refused there -- after the
        # stop.
        boundaries.text(getattr(adapter, member, None),
                        f"the runtime adapter's {member}")
    for verb in FENCE_PORT:
        boundaries.capability(getattr(port, verb, None),
                              f"the authority-bound port's {verb}")
    if getattr(port, "participant", None) is None:
        _refuse("the authority-bound port names no participant; the custody "
                "operations compare it, and a port without one refuses after "
                "the freeze rather than before the stop", code="capability")
    # THE PROFILE'S NAME IS AN IDENTITY THIS ENDING WILL BE COMPARED ON, so it
    # is owned here rather than read for the first time by the line provider.
    boundaries.text(getattr(profile, "name", None),
                    "the checkpoint profile's name")
    for verb in needs:
        boundaries.capability(getattr(profile, verb, None),
                              f"the checkpoint profile's {verb}")
    return adapter, port


def _profile_of_the_line(control, profile, line_id):
    """The profile must be the LINE'S profile, compared before the first stop.

    THIRD REVIEW [P1]: a fully callable profile named `other-profile` was
    handed to an ending prepared under `test-profile`, and the adapter recorded
    one stop before `freeze_checkpoint` refused `policy/profile-uncertified`.
    Every custody operation makes this comparison; the ending simply made it
    too late. The line comes from the owner-bound writer or attachment rather
    than from the caller, so this cannot be satisfied by naming a line that
    agrees.
    """
    line = review_cycles.line_of(control, line_id)
    if line["profile_name"] != profile.name:
        raise ContractRefusal(
            "policy", "profile-uncertified",
            f"development line {name_value(line_id)} is kept under "
            f"{name_value(line['profile_name'])} and this ending was handed a "
            f"profile named {name_value(profile.name)}; one ending works one "
            f"line's profile")
    return line


def _acting_for(control, port, attempt_id):
    """The port must ACT FOR the attempt this ending is about.

    REVIEW [P1]: a non-null participant was proved and never compared, so a
    session belonging to somebody else reached `refused/capability` from the
    custody operations -- with the container already stopped. The comparison is
    the same one `freeze_checkpoint` and `record_verdict` make, asked here
    while nothing has happened.
    """
    assignment = attempts.assignment_of(control, attempt_id)
    if assignment["participant"] != port.participant:
        _refuse(f"attempt {name_value(attempt_id)} is assigned to "
                f"{name_value(assignment['participant'])} and this ending was "
                f"handed a session acting for "
                f"{name_value(port.participant)}; one ending acts for one "
                f"assignment", code="capability")
    return assignment


def _own_writer(control, *, writer_id, attempt_id, generation):
    """The writer row this ending will fence, PROVED to be this attempt's.

    REVIEW [P0]: the ending quiesced, observed, froze, collected, retained and
    published for `attempt_id` and then fenced a separately chosen
    `writer_id`. Two live lines could therefore publish A's output and answer
    with B's checkpoint, and every irreversible step happened before anything
    noticed. The writer is read from the owner's own table and bound to this
    attempt and generation before the first external act.
    """
    writer = review_cycles.writer_of(control, writer_id)
    if writer["runtime_attempt_id"] != attempt_id \
            or writer["assignment_generation"] != generation:
        _refuse(f"writer {name_value(writer_id)} belongs to attempt "
                f"{name_value(writer['runtime_attempt_id'])} generation "
                f"{writer['assignment_generation']}, and this ending is for "
                f"{name_value(attempt_id)} generation {generation}; one "
                f"ending answers for one attempt")
    if writer["state"] != "active":
        _refuse(f"writer {name_value(writer_id)} is "
                f"{name_value(writer['state'])}; an ending fences the writer "
                f"that is still holding the line")
    return writer


def _quiesced(control, adapter, attempt_id):
    """Step one: the EXACT runtime, positively observed quiescent.

    ORDERED, NOT WAITED FOR, and `absent` is not the same proof. A runtime that
    is merely gone was never observed to have finished writing, so freezing its
    output would seal bytes nobody watched the end of. This is the accepted
    composition's own rule and its reason is quoted rather than restated.

    AND AN AGENT SESSION NEVER ANSWERS IT. `sessions.satisfies_runtime_
    quiescence_gate` returns false for every one of the nine session states on
    purpose: a finished conversation says nothing about whether the runtime
    that held the generation is gone. Nothing in this module reads a session
    state as though it did.
    """
    row = attempts.attempt_runtime_of(control, attempt_id)
    runtime_id = (row or {}).get("runtime_id")
    if runtime_id is None:
        _refuse(f"attempt {name_value(attempt_id)} has no attached runtime to "
                f"quiesce; an ending observes the runtime that produced the "
                f"work rather than assuming there was none")
    stopped = adapter.stop({"runtime_id": runtime_id,
                            "operation_id": f"quiesce:{attempt_id}"})
    # THE ANSWER IS PROVED BEFORE IT IS READ. Review [P1]: `.get` on whatever
    # came back turned a malformed adapter answer into an AttributeError from
    # inside an ending, which is neither a refusal an operator can act on nor a
    # statement about the runtime.
    if type(stopped) is not dict:
        _refuse(f"the runtime adapter answered a stop of "
                f"{name_value(runtime_id)} with something that is not a "
                f"document; an ending needs an observation and not a value")
    if stopped.get("state") != "quiescent":
        _refuse(f"attempt {name_value(attempt_id)}'s runtime was ordered to "
                f"stop and observed {name_value(stopped.get('state'))}; a "
                f"freeze takes a positively quiescent runtime, and an absent "
                f"one is not the same proof because its writer was never seen "
                f"to finish")
    reconcile_runtime(control, adapter, attempt_id=attempt_id)
    return runtime_id


def _correlated(control, frozen, terminal, attempt_id):
    """Step four: the worker's claimed envelope against this manager's own.

    `manifest_digest` on the terminal names the WORKER's completion envelope;
    the sealed result's `completion_manifest_digest` is what this manager
    computed over the bytes it read. Comparing the terminal against the frozen
    result's own manifest digest would refuse every honest attempt -- two
    documents, and the accepted composition's regression caught exactly that
    confusion.
    """
    if terminal is None:
        return None
    sealed = load_manifest(control, frozen["manifest_digest"], "resultManifest")
    validated = (sealed or {}).get("completion_manifest_digest")
    if terminal.get("manifest_digest") != validated:
        _refuse(f"attempt {name_value(attempt_id)}'s worker answered "
                f"completion manifest "
                f"{name_value(terminal.get('manifest_digest'))} and this "
                f"manager validated {name_value(validated)}; a terminal that "
                f"names another envelope is not evidence about the output "
                f"this manager froze", code="operation-collision")
    return validated


def _collected(control, port, adapter, *, attempt_id, retention_disposition,
               retention_policy_digest):
    """Steps five and six: intake, then retention, and both before any fence.

    THEY PRECEDE THE FENCE FOR A MEASURED REASON. Ending the assignment before
    intake can quarantine the result if the collection races that ending, which
    is why W44657 put the Authority act after intake and retention. This leaf's
    contract lists "retain/clean up" after the checkpoint freeze; only the
    CLEANUP can be there, because `authorize_cleanup` refuses while the
    assignment is live and intake must not race its ending. Recorded rather
    than silently reordered.
    """
    receipt = request_intake(control, port, adapter, attempt_id=attempt_id)
    held = list(receipt["artifacts"])
    decided = decide_retention(
        control, port, adapter, attempt_id=attempt_id,
        artifact_ids=[one["artifact_id"] for one in held],
        disposition=retention_disposition,
        retention_policy_digest=retention_policy_digest)
    return receipt, held, decided


# -- before a runtime starts -------------------------------------------------


def prepare_implementation(control, *, line_id, attempt_id, generation,
                           worker_id, profile, based_checkpoint_id=None):
    """Grant this attempt the line's ONE writer and compose its mount.

    `based_checkpoint_id` is what makes a correction round the SAME line rather
    than a second one: the accepted provider admits a writer on a
    `correction-ready` line only when it names that line's current checkpoint,
    and refuses a first writer that names any. So the caller passes the
    rejected checkpoint on every round after the first, and passes nothing on
    the first, and the provider is what enforces which is which.

    NO SOURCE IS CLONED HERE AND NONE IS CLONED LATER. The line is one durable
    checkout created once by `create_line`; a correction writer attaches to it
    again. That is the property the two-Job proof has to demonstrate, and it is
    a property of the accepted provider rather than of this driver.
    """
    granted = review_cycles.grant_writer(
        control, line_id=line_id, attempt_id=attempt_id, generation=generation,
        worker_id=worker_id, profile=profile,
        based_checkpoint_id=based_checkpoint_id)
    boundary = review_cycles.writer_boundary(
        control, writer_id=granted["writer_id"], generation=generation)
    return {"writer_id": granted["writer_id"], "line_id": line_id,
            "generation": generation,
            "based_checkpoint_id": based_checkpoint_id, "boundary": boundary}


def prepare_review(control, *, checkpoint_id, attempt_id, generation,
                   reviewer_worker_id, profile):
    """Attach the reviewer to the exact current checkpoint, BEFORE it starts.

    THE ATTACHMENT IS THE AUTHORIZATION AND IT COMES FIRST. `review_boundary`
    composes a read-only mount of the frozen checkpoint and a separate writable
    output, and neither exists until the attachment does -- so a reviewer
    cannot be started and then given something to look at. A runtime launched
    before this would have to be handed a path this module had not proved, and
    that is the shape a review of somebody else's checkpoint takes.

    INDEPENDENCE IS NOT PROVED HERE. `PooledManagerOperations` already excluded
    the implementation stage's worker, participant and principal before this
    attempt existed, and `attach_review` refuses a reviewer that is the
    checkpoint's own writer. Re-comparing principals here would be a third
    account of a rule two owners already keep.
    """
    attached = review_cycles.attach_review(
        control, checkpoint_id=checkpoint_id, attempt_id=attempt_id,
        generation=generation, reviewer_worker_id=reviewer_worker_id,
        profile=profile)
    boundary = review_cycles.review_boundary(
        control, attachment_id=attached["attachment_id"], profile=profile)
    return {"attachment_id": attached["attachment_id"],
            "checkpoint_id": checkpoint_id, "generation": generation,
            "boundary": boundary}


# -- the two endings ---------------------------------------------------------


def end_implementation(control, port, adapter, publication, *, attempt_id,
                       disposition, terminal, writer_id, generation, profile,
                       retention_disposition, retention_policy_digest,
                       proposal):
    """End one implementation attempt into an immutable, published checkpoint.

    THE ORDER, and every step of it is somebody else's operation:

      1. positively quiesce and reconcile the exact runtime;
      2. record the worker's returned disposition;
      3. freeze the declared output for that disposition;
      4. correlate the worker's claimed envelope with this manager's own;
      5. collect it and record the intake receipt;
      6. decide every artifact's retention under the configured policy;
      7. PUBLISH the proposal while the producer assignment is still live;
      8. fence that assignment and freeze the immutable checkpoint; and only
         then
      9. authorize runtime cleanup.

    SEVEN BEFORE EIGHT IS THE WHOLE POINT. `freeze_checkpoint` finalizes the
    writer's Authority assignment, and a publication after that refuses --
    W103068 kept the reproduction. Publishing first and freezing second means
    the proposal names a result the checkpoint then seals, rather than a
    checkpoint that can never be published.

    AND EVERY STEP REPLAYS. `stop` re-observes an already quiescent runtime,
    `observe` of the same disposition is a no-op, the freeze replays its
    immutable record, intake and retention replay their journalled operations,
    the seam is effectively-once by the caller's own identity, and
    `freeze_checkpoint` replays a frozen checkpoint. A process death between
    any two steps re-enters here and finishes.
    """
    _seam(publication)
    _typed(adapter, port, profile, IMPLEMENTATION_PROFILE)
    writer = _own_writer(control, writer_id=writer_id, attempt_id=attempt_id,
                         generation=generation)
    _profile_of_the_line(control, profile, writer["line_id"])
    _acting_for(control, port, attempt_id)
    _quiesced(control, adapter, attempt_id)
    observe(control, attempt_id=attempt_id, axis="worker_disposition",
            value=disposition)
    # STEP THREE, AND ITS POSITION IS THE WHOLE OF W105982. The worker wrote
    # this line with its own identity and umask, and every read that follows --
    # the seal, the correlation, the checkpoint profile, and the next serial
    # writer's entry check -- happens over that tree. The ordinary custody
    # normalization is the LAST thing an ending does and addresses the ordinary
    # attempt roots, which are not this tree at all, so until now nothing
    # established that the manager can read what it is about to seal.
    #
    # AFTER THE STOP AND BEFORE THE FIRST READ. After, because a proof taken
    # while the worker is still writing is a proof about a tree that is still
    # changing; before, because a consumer that discovers the denial halfway
    # through sealing has already produced a partial account of somebody's
    # work. It refuses rather than repairing, and a refusal here leaves the
    # line and its evidence exactly as the worker left them.
    adapter.prove_line_consumable(control, assignment_id=attempt_id,
                                  generation=generation)
    frozen = request_freeze(control, port, adapter, attempt_id=attempt_id,
                            disposition=disposition)
    _correlated(control, frozen, terminal, attempt_id)
    receipt, held, decided = _collected(
        control, port, adapter, attempt_id=attempt_id,
        retention_disposition=retention_disposition,
        retention_policy_digest=retention_policy_digest)
    # STEP SEVEN. The producer assignment is live until the next line runs, and
    # this module hands over the manager's own frozen account of the result
    # rather than anything it derived: what a proposal must CONTAIN is the
    # integration driver's contract, not this one's.
    published = publication.publish(
        attempt_id=attempt_id, result_id=frozen["result_id"],
        manifest_digest=frozen["manifest_digest"],
        artifacts=sorted(one["artifact_id"] for one in held),
        proposal=proposal)
    # STEP EIGHT. This ends the assignment, which is why nothing above may
    # follow it.
    checkpoint = review_cycles.freeze_checkpoint(
        control, writer_id=writer_id, generation=generation, profile=profile,
        port=port)
    authorize_cleanup(control, port, adapter, attempt_id=attempt_id,
                      retention_policy_digest=retention_policy_digest)
    return {"attempt_id": attempt_id, "disposition": disposition,
            "result_id": frozen["result_id"],
            "manifest_digest": frozen["manifest_digest"],
            "receipt_digest": receipt["receipt_digest"],
            "artifacts": sorted(one["artifact_id"] for one in held),
            "retention": decided["disposition"],
            "published": published,
            "checkpoint_id": checkpoint["checkpoint_id"],
            "checkpoint": checkpoint}


def end_review(control, port, adapter, *, attachment_id, disposition, verdict,
               profile, retention_disposition, retention_policy_digest):
    """End one review attempt into a recorded verdict, and route on it.

    `disposition` is what the REVIEW WORKER's attempt ended as -- the manager's
    own closed vocabulary -- and `verdict` is what the reviewer decided about
    the checkpoint. They are two different facts and conflating them is how a
    crashed reviewer becomes a rejection: `record_verdict` requires a
    `completed` frozen review result carrying separately frozen findings and
    logs, so a review that did not finish cannot produce any verdict at all.

    WHAT THIS ANSWERS WITH is one of `VERDICT_OUTCOMES`, and `held` is a real
    answer rather than a failure. A rejected checkpoint is a decision about the
    Work; an ambiguous, stale or unreadable one is a question. Neither is a
    round this module may schedule, so both stop here with the evidence intact
    and nothing advanced.

    THE EXPLICIT-OPERAND ENTRY POINT IS PRESERVED EXACTLY, and W110772 did not
    change one thing it does. A caller that already holds a decision -- an
    operator settling a review by hand, a focused test driving one step -- has
    the same function it always had. What that Work added is the entry BELOW,
    for the production case where nobody holds a decision because the reviewer
    is the only party that made one.
    """
    _typed(adapter, port, profile, REVIEW_PROFILE)
    # THE CALLER'S OWN ARGUMENT IS CHECKED FIRST AND IS NOT EVIDENCE. Review
    # [P1]: a disposition this provider does not have is a programming error,
    # so it refuses here rather than being reported as something a reviewer
    # left behind.
    if verdict not in review_cycles.DISPOSITIONS:
        _refuse(f"{name_value(verdict)} is not a review disposition; the "
                f"closed set is {', '.join(review_cycles.DISPOSITIONS)}",
                category="integrity", code="schema")
    return _ended_review(
        control, port, adapter, attachment_id=attachment_id,
        disposition=disposition, terminal=None, profile=profile,
        retention_disposition=retention_disposition,
        retention_policy_digest=retention_policy_digest,
        resolve=lambda _frozen: verdict)


def end_review_from_result(control, port, adapter, *, attachment_id,
                           disposition, terminal, profile,
                           retention_disposition, retention_policy_digest):
    """End one review attempt on the verdict its own frozen output carries.

    W110772. THE PRODUCTION ENTRY POINT, and the whole of its difference from
    `end_review` is where the verdict comes from: nowhere in this process. The
    reviewer decided, wrote its decision into an output this manager then
    measured and sealed, and this reads it back out of that immutable result.
    A deployment that supplied the verdict would be the deployment reviewing
    the checkpoint.

    THE ORDER IS `end_review`'S, with two additions in the two places they can
    honestly go:

      1. positively quiesce and reconcile the exact runtime;
      2. record the worker's returned disposition;
      3. freeze the declared output for that disposition;
      4. CORRELATE the worker's claimed envelope with this manager's own;
      5. collect it and record the intake receipt;
      6. decide every artifact's retention under the configured policy;
      7. RESOLVE the reviewer's claim from the frozen result;
      8. record the verdict; and only then
      9. authorize runtime cleanup.

    STEP FOUR IS WHERE IT IS FOR `end_implementation`'S REASON. The terminal
    names the WORKER's completion envelope and the sealed result names this
    manager's own, so there is nothing to compare until the freeze has
    happened -- and a review whose terminal describes another envelope is not
    evidence about the output this verdict is about to be read from.

    STEP SEVEN IS AFTER THE FREEZE BECAUSE THE CLAIM IS IN IT. That is also
    what makes this re-enterable: a manager that died between the freeze and
    the verdict re-enters here, replays every custody step, and derives the
    same claim from the same retained result. The worker is never asked again
    and never runs again.

    AN UNRESOLVED CLAIM IS `held` WITH NO VERDICT AT ALL. Not rejected, not
    accepted, not a default -- `verdict` is null, no verdict is recorded,
    nothing is cleaned up and nothing advances, and the held reason names the
    frozen evidence an operator has to look at. A reviewer that did not answer
    has not answered; inventing a decision from its silence is the one thing
    this channel exists to prevent.
    """
    _typed(adapter, port, profile, REVIEW_PROFILE)
    return _ended_review(
        control, port, adapter, attachment_id=attachment_id,
        disposition=disposition, terminal=terminal, profile=profile,
        retention_disposition=retention_disposition,
        retention_policy_digest=retention_policy_digest,
        resolve=lambda _frozen: review_verdict_from_result(
            control, attachment_id=attachment_id)["verdict"])


def _ended_review(control, port, adapter, *, attachment_id, disposition,
                  terminal, profile, retention_disposition,
                  retention_policy_digest, resolve):
    """The ordered core both review endings run, and the ONE thing that
    differs between them is `resolve`.

    W110772: written as one body rather than two because every step in it is a
    ruling -- the positive quiescence, the freeze before the read, intake and
    retention before any fence, and cleanup only after a verdict exists. A
    second copy of that order would be a second place for it to drift from the
    reasons recorded above it, and the reasons are what make it right.

    `terminal=None` is a no-op in `_correlated`, which is what keeps the
    explicit-operand entry point's behaviour identical rather than merely
    similar to what it was.
    """
    attachment = review_cycles.review_of(control, attachment_id)
    attempt_id = attachment["runtime_attempt_id"]
    _profile_of_the_line(control, profile, attachment["line_id"])
    _acting_for(control, port, attempt_id)
    _quiesced(control, adapter, attempt_id)
    observe(control, attempt_id=attempt_id, axis="worker_disposition",
            value=disposition)
    frozen = request_freeze(control, port, adapter, attempt_id=attempt_id,
                            disposition=disposition)
    _correlated(control, frozen, terminal, attempt_id)
    receipt, held, decided = _collected(
        control, port, adapter, attempt_id=attempt_id,
        retention_disposition=retention_disposition,
        retention_policy_digest=retention_policy_digest)
    # UNBOUND UNTIL RESOLVED, and the held document below reports exactly what
    # is known. `end_review`'s resolver answers its caller's operand before
    # anything can fail, so that entry point still reports the verdict it was
    # given; the frozen-result resolver may refuse, and then there is no
    # verdict to report and `null` is the honest answer rather than a guess.
    verdict = None
    try:
        verdict = resolve(frozen)
        recorded = review_cycles.record_verdict(
            control, attachment_id=attachment_id, disposition=verdict,
            profile=profile, port=port)
    except ContractRefusal as refusal:
        # STALE, AMBIGUOUS OR UNREADABLE EVIDENCE IS THE HELD OUTCOME, which is
        # what this function's contract says and what it used to do only for
        # `rejected`. Cleanup is deliberately NOT authorized: the assignment is
        # still live, so the runtime stays exactly where an operator can look
        # at it, and the account says the ending is unfinished.
        if refusal.category not in _EVIDENCE_REFUSALS:
            raise
        return {"attempt_id": attempt_id, "attachment_id": attachment_id,
                "verdict": verdict, "verdict_id": None, "verdict_record": None,
                "line_id": None, "checkpoint_id": None,
                "result_id": frozen["result_id"],
                "manifest_digest": frozen["manifest_digest"],
                "receipt_digest": receipt["receipt_digest"],
                "artifacts": sorted(one["artifact_id"] for one in held),
                "retention": decided["disposition"], "outcome": "held",
                "held_reason": f"the checkpoint's review evidence is not one "
                               f"this manager can settle: "
                               f"{refusal.category}/{refusal.code} -- "
                               f"{refusal}",
                "cleaned_up": False}
    authorize_cleanup(control, port, adapter, attempt_id=attempt_id,
                      retention_policy_digest=retention_policy_digest)
    if verdict == "accepted":
        outcome, reason = "accepted", None
    elif verdict == "changes-requested":
        outcome, reason = "correction", None
    else:
        outcome = "held"
        reason = _HELD_REASONS.get(
            verdict, f"a {name_value(verdict)} verdict is not a round this "
                     f"driver may schedule")
    return {"attempt_id": attempt_id, "attachment_id": attachment_id,
            "verdict": verdict, "verdict_id": recorded["verdict_id"],
            # THE WHOLE RECORDED DOCUMENT, because the correction act proves it
            # against this manager's journal rather than trusting an identity.
            "verdict_record": recorded,
            "line_id": recorded["line_id"],
            "checkpoint_id": recorded["checkpoint_id"],
            "cleaned_up": True,
            "result_id": frozen["result_id"],
            "manifest_digest": frozen["manifest_digest"],
            "receipt_digest": receipt["receipt_digest"],
            "artifacts": sorted(one["artifact_id"] for one in held),
            "retention": decided["disposition"],
            "outcome": outcome, "held_reason": reason}




# -- the reviewer's own verdict, read from its frozen result ------------------
#
# W110772, `work/records/2026/09/finding-v12-standalone-multi-job-pipeline/
# findings/finding-standalone-stage-composition/findings/
# finding-review-verdict-channel/`.
#
# WHAT WAS MISSING. `end_review` takes the verdict as an operand and is right
# to: what the review ATTEMPT ended as and what the reviewer DECIDED about the
# checkpoint are two facts, and conflating them turns a crashed reviewer into a
# rejection. But nothing carried the second one out of the container. The
# exchange terminal's members are the manager's own vocabulary and none is the
# reviewer's, so every production caller either had no verdict at all or was
# handed one by its deployment -- which is the deployment deciding the review.
#
# THE SHAPE IS THE ONE W103874 ALREADY ESTABLISHED for the proposal claim, and
# it is reused rather than reinvented: the worker names its own facts under a
# namespace in `result_metadata`, the manager re-reads everything else from the
# owner that holds it, and neither side may manufacture the other's half.

REVIEW_CLAIM_NAMESPACE = "baton.checkpoint-review/1"
REVIEW_CLAIM_MEMBERS = ("base", "head", "tree", "verdict")

# WHICH OUTPUT CARRIES THE CLAIM, and it is not a free choice. `_review_result`
# already requires a frozen review to carry separately frozen `findings` and
# `logs`, so `findings` is the one output a completed review is guaranteed to
# have and the one whose content the claim is about. A claim on `logs` or on a
# proposal output is refused rather than accepted from wherever it turns up:
# two outputs offering a verdict is a reviewer with two answers.
FINDINGS_OUTPUT = "findings"
LOGS_OUTPUT = "logs"


def _claim_output(result, name):
    """One present, measured, artifact-backed output of a frozen result."""
    matches = [one for one in result["outputs"] if one["name"] == name]
    if len(matches) != 1:
        _refuse(f"the frozen review result carries {len(matches)} outputs "
                f"named {name_value(name)}; a review verdict is read from "
                f"exactly one", category="integrity", code="schema")
    output = matches[0]
    if output["status"] != "present" or output["artifact"] is None \
            or output["content_manifest"] is None:
        _refuse(f"the frozen {name_value(name)} output is not present with "
                f"both its artifact and content manifest; a verdict is not "
                f"read from an output nobody measured")
    return output


def _review_claim(result):
    """The reviewer's own four facts, adopted and never extended.

    ADOPTED AS A CLOSED DOCUMENT, for `_claim_of`'s reason one layer over: the
    members this reader would be tempted to accept are exactly the ones it must
    read from their owners -- a checkpoint id, an attachment, a generation, a
    result digest. A reviewer that supplied one of those would be certifying
    the manager's own account of the review it was asked to perform.

    AND A COMPETING CLAIM REFUSES. A namespaced claim on the logs output is not
    a second opinion to weigh against the findings one; it is a reviewer
    answering twice, which is exactly the ambiguity `held` exists for.
    """
    logs = _claim_output(result, LOGS_OUTPUT)
    if type(logs["result_metadata"]) is dict \
            and REVIEW_CLAIM_NAMESPACE in logs["result_metadata"]:
        _refuse(f"the frozen review result carries a "
                f"{name_value(REVIEW_CLAIM_NAMESPACE)} claim on its "
                f"{name_value(LOGS_OUTPUT)} output as well as its "
                f"{name_value(FINDINGS_OUTPUT)} one; one review decides once",
                category="ambiguous", code="collection")
    output = _claim_output(result, FINDINGS_OUTPUT)
    metadata = output["result_metadata"]
    if type(metadata) is not dict or REVIEW_CLAIM_NAMESPACE not in metadata:
        _refuse(f"the frozen {name_value(FINDINGS_OUTPUT)} output carries no "
                f"{name_value(REVIEW_CLAIM_NAMESPACE)} claim; the verdict on a "
                f"checkpoint is the reviewer's own fact and this manager will "
                f"not invent one")
    claim = boundaries.document(metadata[REVIEW_CLAIM_NAMESPACE],
                                "a worker checkpoint-review claim",
                                required=REVIEW_CLAIM_MEMBERS)
    if claim["verdict"] not in review_cycles.DISPOSITIONS:
        _refuse(f"the reviewer claimed verdict "
                f"{name_value(claim['verdict'])}; the closed set is "
                f"{', '.join(review_cycles.DISPOSITIONS)}",
                category="integrity", code="schema")
    for member in ("base", "head", "tree"):
        boundaries.text(claim[member],
                        f"the reviewer's observed {member} object")
    return claim


def review_verdict_from_result(control, *, attachment_id):
    """The verdict a completed review actually recorded in its frozen output.

    READ-ONLY AND PUBLIC. It opens nothing, writes nothing, reads no mutable
    runtime path, takes no clock and calls no provider: every fact below comes
    from an accepted owner of it, so the same call on the next incarnation
    derives the same answer from the same immutable evidence. That is what
    makes an ending re-enterable after the freeze without asking the worker
    anything a second time.

    THE CROSS-BINDING IS THE POINT. A namespaced claim by itself says only that
    somebody wrote four members into an output. What makes it a verdict about
    THIS checkpoint is that the frozen result belongs to this attachment's
    attempt, its retained manifest names the same result and the same fixed
    assignment at the same generation, and the base, head and tree the reviewer
    says it looked at are the ones the checkpoint's own evidence records.

    EVERY REFUSAL HERE IS EVIDENCE RATHER THAN PROGRAMMING, and each carries a
    category `end_review_from_result` holds rather than raises. Missing,
    malformed, foreign or unavailable evidence is a question for an operator;
    none of it is a default decision, and in particular none of it is
    `rejected`. A reviewer that did not answer has not rejected anything.
    """
    boundaries.identity(attachment_id, "a review attachment identity")
    attachment = review_cycles.review_of(control, attachment_id)
    attempt_id = attachment["runtime_attempt_id"]
    frozen = frozen_output_of(control, attempt_id)
    if frozen is None:
        _refuse(f"review attempt {name_value(attempt_id)} has no frozen "
                f"result; a verdict is read from immutable output and never "
                f"from a running one")
    if frozen["disposition"] != "completed":
        _refuse(f"review attempt {name_value(attempt_id)} froze a "
                f"{name_value(frozen['disposition'])} result; a review that "
                f"did not complete decided nothing")
    result = load_manifest(control, frozen["manifest_digest"], "resultManifest")
    if result is None:
        _refuse(f"this manager retains no result manifest at "
                f"{name_value(frozen['manifest_digest'])} for review attempt "
                f"{name_value(attempt_id)}")
    if result["result_id"] != frozen["result_id"]:
        _refuse("the frozen review summary and its retained manifest name "
                "different results", category="integrity", code="schema")
    fixed = attempts.assignment_of(control, attempt_id)
    expected = {"work_ref": {"authority_uuid": fixed["authority_uuid"],
                             "work_id": fixed["work_id"]},
                "participant": fixed["participant"],
                "generation": fixed["generation"]}
    if result["assignment_ref"] != expected:
        _refuse("the frozen review result and the review attempt do not name "
                "one assignment", category="integrity", code="schema")
    # THE ATTACHMENT'S OWN GENERATION, compared separately from the assignment
    # above. `attach_review` recorded which generation this reviewer was
    # attached under, and a result frozen under another one is a different
    # review of the same checkpoint rather than this one's evidence.
    if attachment["assignment_generation"] != fixed["generation"]:
        _refuse(f"review attachment {name_value(attachment_id)} was attached "
                f"at generation {attachment['assignment_generation']} and its "
                f"attempt's assignment is generation {fixed['generation']}",
                category="stale-assignment", code="generation")
    claim = _review_claim(result)
    checkpoint = review_cycles.checkpoint_of(control,
                                             attachment["checkpoint_id"])
    evidence = checkpoint["evidence"]
    for member in ("base", "head", "tree"):
        if claim[member] != evidence.get(member):
            _refuse(f"the reviewer says it reviewed {member} "
                    f"{name_value(claim[member])} and checkpoint "
                    f"{name_value(checkpoint['checkpoint_id'])} records "
                    f"{name_value(evidence.get(member))}; a verdict is about "
                    f"the checkpoint it was attached to",
                    category="integrity", code="schema")
    return {"attachment_id": attachment_id, "attempt_id": attempt_id,
            "checkpoint_id": checkpoint["checkpoint_id"],
            "verdict": claim["verdict"], "base": claim["base"],
            "head": claim["head"], "tree": claim["tree"],
            "result_id": frozen["result_id"],
            "result_digest": frozen["manifest_digest"]}


# -- the correction round ----------------------------------------------------


def open_correction(jobs, control, *, job_id, answered):
    """Advance one Job to its next round from a recorded verdict.

    THIS IS THE ONE ACT THAT TOUCHES THE JOB STORE, and it is separate from
    `end_review` because the two stores commit separately. A review ending that
    also advanced the Job would have a window where the verdict is durable and
    the round is not, and the honest recovery from that window is to re-enter
    here -- which is exactly what a caller that finds `correction` and calls
    this does, on this incarnation or the next one.

    `answered` is `end_review`'s own document. What travels is an IDENTITY,
    and that is safe because `advance_correction` resolves it through the
    owner's own typed reader -- which cross-binds the verdict row against the
    act that recorded it -- rather than believing anything this module says
    about it. The Job's two stages are read from the Job store by `job_id` for
    the same reason.
    """
    if answered.get("outcome") != "correction":
        _refuse(f"a correction round follows a changes-requested verdict; "
                f"this review answered "
                f"{name_value(answered.get('outcome'))}")
    return episodes.advance_correction(
        jobs, control, job_id=job_id, line_id=answered["line_id"],
        checkpoint_id=answered["checkpoint_id"],
        verdict_id=answered["verdict_id"])
