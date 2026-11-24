"""THE SUPPORTED OWNER SURFACE FOR A RETAINED OUTPUT PUBLICATION FAILURE:
inspect the original, then decide it -- and an approval asks the manager to
compose the admission that decision reaches.

W385695 internal checkpoint 1, under DESIGN REC-9 and the owner-selected
contract CONTRACT-PROPOSED-385720.md. Two verbs of the installed `manager`
command, reachable from the deployed bundle exactly as `cancel-job`,
`settle-stopped` and `recovery-item` are:

    manager publication-inspect ... what the owner is being asked to decide
    manager publication-decide  ... approve, hold or deny it, bound to the
                                    exact execution, original bytes, candidate
                                    and producer attribution

WHAT WAS MISSING, and it is the same shape of absence W321689 found for the
owner's ordinary disposition and W385624 found for a retained verification
failure. A producer completed, its own required verification passed, its
output exceeded the declared ceiling, and the publication faulted -- so there
is no frozen result, no custody and no owner item, and every supported command
truthfully reports that there is nothing to collect. The bytes are on the
host. Nothing exposed them: the attempt, its measured original, the adapter's
own `result.json` and the candidate's correspondence with its base were
reachable only by writing Python against the package or by reading a path an
operator typed, and a trust root reachable only by typing a path is a trust
root an agent can forge.

WHAT THIS IS. A wrapper over the public faces and nothing more.
`job_manager.publication_recovery` owns every rule about eligibility, the
trust root, producer qualification, authorization, exact operands, stage sets,
profiles, fences, replay and the admission boundary; the Authority owns who
may decide and in which scope; the workspace owner owns the original bytes;
the host owns cessation; the source-aware consumer owns Git. This module
decides which owner each operand reaches and prints what it was told --
REC-7's "the CLI requests the operation and reports its outcome", which REC-9
composes unchanged.

THERE IS NO `--actor`, NO `--scope` AND NO `--output-path`, and the three
absences are the point. `--participant` mints the owner authorization port and
the Authority resolves the principal; the scope comes off the Work's own row;
and the original output is resolved FROM THE ATTEMPT through its owner, so a
caller cannot name the bytes this command then treats as the trust root.

THE CONTROL STORE IS OPENED READ-ONLY, and the Authority is opened read-only
for both verbs -- an owner decision writes no Authority row, it is authorized
by one. The Job store is writable only for `publication-decide`, because
asking what you are being asked to decide must not take a write lock on a
serving deployment.

IT LAUNCHES NOTHING, AND IN THIS CHECKPOINT IT ADMITS NOTHING EITHER.
`--deny` and `--hold` record an attributable disposition and stop. `--approve`
records the decision and then asks the manager to compose the admission; the
manager re-establishes the trust root, reuses the Work, evaluates what an
actual admission would need, and answers with a HELD PREREQUISITE and a CLOSED
gate -- no Job, no binding, no reservation, no offer. The answer says so in
`readiness`, because an answer carrying a Job id and saying nothing else would
read as a recovery that happened.
"""
import argparse
import importlib
import json
import os
import sys

from baton_v12.contracts import ContractRefusal
from baton_v12.job_manager import JobStore, publication_recovery
from baton_v12.worker_manager import ControlStore

__all__ = ["COMMANDS", "OWNERS", "OPTIONAL_OWNERS", "owners",
           "main"]

COMMANDS = ("publication-inspect", "publication-decide",
            "publication-status")

# THE OWNER-PORT SET ONE DEPLOYMENT SUPPLIES, written down rather than
# discovered from whatever object a factory returned -- `delegation.
# OPERATIONS`' and `recovery_decision.OWNERS`' rule, for their reason: a
# member that cannot be called would otherwise fault between a committed
# decision and the boundary that decision reaches.
#
#   `owner`         the owner authorization port: who is acting, the Work's
#                   own row and the Authority's one decision seam.
#   `host`          the workspace owner's proved, measured ORIGINAL output.
#   `exclusion`     the host's record of the prior attempt's runtime and
#                   workspace token.
#   `source`        the Git-aware consumer that corresponds candidate, base
#                   and path set.
#   `authorization` the Authority's answer about the Work this recovery
#                   reuses. Read only: this boundary never mints a Work.
#   `binding`       the deployment configuration's own binding and selector.
#   `ownership`     the instance guard, plus this boundary's invocation lock.
#
# W385695 checkpoint 2 adds an EIGHTH that is deliberately NOT in this tuple:
#   `ending`        the Authority's exact-expect transition that releases the
#                   assignment the reused Work already holds.
# It is optional because an INSPECTION and a DECISION perform no assignment
# transition at all, and requiring it would make a read-only inspection
# refuse for want of a capability it never uses. The admission refuses an
# absent one where it would be used, naming why.
OWNERS = ("owner", "host", "exclusion", "source", "authorization", "binding",
          "ownership")
OPTIONAL_OWNERS = ("ending",)


def _say(value, stream):
    json.dump(value, stream, indent=2, sort_keys=True, ensure_ascii=False)
    stream.write("\n")
    return 0


def _refused(message):
    """ONE REFUSAL LINE ON STDERR, and the answer stays on stdout.

    `recovery_decision._refused`'s posture, for its reason: where BOTH are
    true -- the owner's decision committed and its admission boundary refused
    -- the document goes to stdout and this line to stderr, so neither reader
    loses its half.
    """
    print("refused: " + message, file=sys.stderr)
    return 1


def owners(request):
    """Compose this deployment's seven owner ports over the stores it owns.

    Every port here is an accepted adapter over this instance's own layout and
    its own emitted configuration; nothing is searched for and nothing is
    guessed.
    """
    from tools.fresh_attempt_ports import (DeploymentBinding, HostExclusion,
                                           InstanceOwnership,
                                           WorkAuthorization,
                                           instance_identity)
    from tools.publication_ports import HostOutput, SourceCorrespondence
    from tools.recovery_decision import OwnerAuthorization

    identity = instance_identity(request["instance"])
    _agreeing("job_store", request["job_store"], "Job store", identity)
    _agreeing("control_store", request["control"], "control store", identity)
    _agreeing("authority_store", request["authority"], "Authority store",
              identity)
    binding = DeploymentBinding(request["instance"], stream=request["stream"],
                                identity=identity)
    from baton_v12.authority import Authority

    authority = Authority.open_readonly(
        request["authority"],
        expected_authority_uuid=request["authority_uuid"])
    from tools.publication_ports import PriorAssignment

    return {
        "owner": OwnerAuthorization(authority,
                                    participant=request["participant"]),
        "host": HostOutput(request["control_handle"], identity),
        # Inspection owns no producer session. A held assignment therefore
        # remains held until its existing serving owner ends it; this default
        # must never mint a session for the participant it happens to read.
        #
        # W385695 checkpoint 2: AND THE SERVING OWNER NOW DOES. An admission
        # composed here reserves the recovery and stops at the held
        # assignment with a typed capability refusal. The serving manager --
        # the one process holding the producer participant's session -- ends
        # exactly that assignment on its next tick
        # (`manager._publish` -> `publication_recovery.advance_endings`), and
        # the same admission, repeated, replays that journalled ending and
        # admits. Nothing is ended by this command.
        "ending": PriorAssignment(authority, identity),
        "exclusion": HostExclusion(request["control_handle"],
                                   identity=identity),
        "source": SourceCorrespondence(identity),
        # COMPOSED WITH NO ROUTE AND NO PRODUCERS, because REC-9 REUSES the
        # failed Job's open Work and never creates one: the admission
        # boundary refuses an absent or terminal Work rather than minting
        # one, so `create_work` is not on this path and a route is not an
        # operand of this surface at all.
        "authorization": WorkAuthorization(authority, route=None,
                                           identity=identity),
        "binding": binding,
        "ownership": InstanceOwnership.of(request["control_handle"],
                                          binding.configuration(),
                                          identity=identity),
        "release": authority.dispose,
    }


def _agreeing(named, supplied, what, identity):
    if os.path.realpath(str(supplied)) != identity[named]:
        raise ContractRefusal(
            "refused", "precondition",
            f"the {what} this command was given is {str(supplied)!r} and "
            f"instance {identity['root']!r} owns {identity[named]!r}; a "
            f"publication recovery is inspected and decided against the "
            f"instance whose failure it is about")
    return identity[named]


def _owners_from(name, request, *, needed):
    """Import exactly the owner-port factory the operator named.

    `module:attribute`, and nothing is searched for -- `_operations_from`'s
    rule, which exists because a tool that guessed at a factory would be
    choosing which authority the manager acts under.
    """
    if ":" not in name:
        raise SystemExit(f"--owners names an owner-port factory as "
                         f"module:attribute; this is {name!r}")
    where, _, attribute = name.partition(":")
    held = getattr(importlib.import_module(where), attribute)(request)
    missing = [one for one in needed if held.get(one) is None]
    if missing:
        raise ContractRefusal(
            "refused", "capability",
            f"the owner-port factory {name!r} supplies no "
            f"{', '.join(missing)}; a publication recovery composes "
            f"{', '.join(OWNERS)} and this operation does not decide an "
            f"owner's fact for it by assuming one")
    return held


def _stores(taken, clock, opened):
    """The three stores this surface touches, each opened as its role allows.

    The Job store WRITABLY for a decision and READ-ONLY for an inspection; the
    control store always read-only; the Authority always read-only. A read
    that took a write lock on a serving deployment would make asking about
    your own original an operational act -- and an inspection that could write
    to the Worker Manager could change the evidence it is judging.
    """
    jobs = opened.enter_context(
        JobStore.open(taken.store, authority_uuid=taken.authority_uuid,
                      incarnation=taken.incarnation, clock=clock)
        if taken.command == "publication-decide" else
        JobStore.open_readonly(taken.store,
                               authority_uuid=taken.authority_uuid,
                               incarnation=taken.incarnation, clock=clock))
    control = opened.enter_context(
        ControlStore.open_readonly(taken.control,
                                   incarnation=taken.incarnation,
                                   clock=clock))
    return jobs, control


def _request(taken, control):
    return {"instance": taken.instance, "job_store": taken.store,
            "control": taken.control, "control_handle": control,
            "authority": taken.authority,
            "authority_uuid": taken.authority_uuid,
            "participant": getattr(taken, "participant", None),
            "stream": sys.stderr}


def _inspect(taken, clock, stream):
    """WHAT THE OWNER IS BEING ASKED TO DECIDE. READ-ONLY.

    The whole document is `publication_recovery.inspect`'s: the exact failed
    execution and its assignment, the absence of any published result, the
    proved and measured ORIGINAL, the adapter's qualified producer evidence,
    the candidate/base/path correspondence, the host's cessation and exclusion
    answers, the corrective output declaration, the approved profile and its
    digest, the selectable stage set, what the reviewer still owes, every
    standing hold, and the canonical selection digest a decision binds.
    """
    from contextlib import ExitStack

    with ExitStack() as opened:
        jobs, control = _stores(taken, clock, opened)
        needed = ("host", "exclusion", "source")
        if taken.participant is not None:
            needed += ("owner",)
        held = _owners_from(taken.owners, _request(taken, control),
                            needed=needed)
        if held.get("release") is not None:
            opened.callback(held["release"])
        return _say(publication_recovery.inspect(
            jobs, control, job_id=taken.job, stage_id=taken.stage,
            episode=taken.episode, host=held["host"],
            exclusion=held["exclusion"], source=held["source"],
            authorization=held.get("owner") if taken.participant else None,
            now=clock() if taken.control_report else None), stream)


def _decide(taken, clock, stream):
    """THE OWNER'S OWN ACT, and the admission boundary an approval reaches.

    TWO DURABLE ACTS AND THEY ARE NOT ONE. The decision is journalled under
    the owner's own operation key with every operand compared first; the
    admission boundary is a separate manager operation with its own identity
    and its own prerequisite evaluation. So a crash between them leaves a
    decision that can be carried out rather than an effect nobody decided, and
    running the same command again replays the first and resumes the second.
    """
    from contextlib import ExitStack

    with ExitStack() as opened:
        jobs, control = _stores(taken, clock, opened)
        held = _owners_from(taken.owners, _request(taken, control),
                            needed=OWNERS)
        if held.get("release") is not None:
            opened.callback(held["release"])
        decision = publication_recovery.decide(
            jobs, control, job_id=taken.job, stage_id=taken.stage,
            episode=taken.episode, decision_id=taken.decision_id,
            disposition=taken.disposition, authorization=held["owner"],
            expected={
                "attempt_id": taken.expect_attempt,
                "producer_argv": list(taken.producer_verification or []),
                "producer_status": taken.expect_producer_status,
                "candidate_base": taken.expect_candidate_base,
                "candidate_head": taken.expect_candidate_head,
                "output_tree_digest": taken.expect_output_digest,
                "output_total_bytes": taken.expect_output_bytes,
                "verification_context_digest": taken.context_digest,
                "selection_digest": taken.expect_selection_digest},
            profile=taken.profile, profile_digest=taken.profile_digest,
            stages=list(taken.stage_word or []),
            declaration_digest=taken.declaration_digest,
            host=held["host"], exclusion=held["exclusion"],
            source=held["source"], now=clock())
        answer = {"decision": decision, "admission": None, "admitted": False,
                  "refusal": None}
        if taken.disposition != publication_recovery.APPROVED:
            return _say(answer, stream)
        try:
            answer["admission"] = publication_recovery.admit_publication(
                jobs, control, decision_id=taken.decision_id,
                exclusion=held["exclusion"],
                authorization=held["authorization"], binding=held["binding"],
                ownership=held["ownership"], host=held["host"],
                source=held["source"],
                # W385695 checkpoint 2: AND THE ENDING PORT WHEN THIS
                # DEPLOYMENT COMPOSED ONE. It is `get` rather than `[...]`
                # because `OWNERS` names the seven a DECISION needs and this
                # is the eighth, needed only by an admission that will really
                # reach a fresh assignment -- the operation itself refuses an
                # absent one at the moment it would be used, with the sentence
                # that says why, rather than this surface refusing an
                # inspection for want of a transition it never performs.
                ending=held.get("ending"), now=clock())
        except ContractRefusal as refusal:
            # THE OWNER'S ACT HAPPENED AND THE BOUNDARY REFUSED, and an
            # operator is owed BOTH facts. A bare refusal on stderr would
            # leave them unable to tell "nothing was recorded" from "your
            # decision stands and the original moved under it".
            answer["refusal"] = {"category": refusal.category,
                                 "code": refusal.code,
                                 "message": refusal.message}
            _say(answer, stream)
            return _refused(f"{refusal.category}/{refusal.code}: "
                            f"{refusal.message}")
        # `admitted` IS FALSE AND IT IS NOT A FAILURE. The boundary composed,
        # the decision stands, the prerequisites are named and the gate is
        # closed -- which is the whole truthful answer this checkpoint has.
        answer["admitted"] = answer["admission"]["state"] == "admitted"
        answer["gate"] = publication_recovery.execution_gate(
            jobs, taken.decision_id)
        return _say(answer, stream)


def _review(jobs, control, admitted, ready):
    """The recovery's review: stage state, reviewer and recorded verdict."""
    from baton_v12.worker_manager import attempt_runtime_of, review_cycles

    stage = ready.get("review_stage")
    if stage is None:
        return {"state": "blocked: no publication custody and hand-off yet",
                "verdict": None}
    answer = {"stage_id": stage["stage_id"], "episode": stage["episode"],
              "attempt_id": stage["attempt_id"], "state": stage["state"],
              "ended_without_verdict": stage["ended"],
              "reviewer": None, "verdict": None}
    if stage["attempt_id"] is None:
        return answer
    recorded = attempt_runtime_of(control, stage["attempt_id"])
    if recorded is None or recorded.get("assignment") is None:
        return answer
    answer["reviewer"] = recorded["assignment"]["participant"]
    attachment = review_cycles.review_for_attempt(
        control, attempt_id=stage["attempt_id"],
        generation=recorded["assignment"]["generation"])
    if attachment is None:
        return answer
    # THE VERDICT'S OWN COMMITTED ACT, by the identity the review owner
    # journals it under; the owner then validates the whole record.
    act = control.operation_record(
        review_cycles.VERDICT_KIND + ":" + attachment["attachment_id"])
    if act is not None and act["state"] == "committed" and act["result"]:
        verdict = review_cycles.verdict_of(
            control, json.loads(act["result"])["verdict_id"])
        answer["verdict"] = {
            "disposition": verdict["disposition"],
            "checkpoint_id": verdict["checkpoint_id"],
            "head": verdict["head_object"],
            "recorded_at": verdict["recorded_at"],
            "candidate_is_the_approved_original":
                verdict["head_object"] == admitted["candidate"]["head"]}
    return answer


def _status(taken, clock, stream):
    """WHERE ONE DECIDED RECOVERY STANDS. READ-ONLY, and it takes no
    participant: it reports operational facts under the local instance's
    existing trust boundary and grants nothing.

    THE ORIGINAL FAILURE, THE RECOVERY, THE CUSTODY AND THE REVIEW ARE FOUR
    DIFFERENT THINGS and are reported as four. The failed Job is never
    described as recovered; a recovery that did not publish is reported with
    what ended it, whether its runtime was settled, and the item delivered to
    the owner who decided it.

    WHAT IS KNOWN IS SEPARATED FROM WHAT WAS LAST RECORDED. The publication
    attempt's runtime axis is the Worker Manager's journal -- the last thing
    somebody observed -- and is printed as `recorded`. Whether that is
    current knowledge is `runtime_knowledge`, which says `unknown` from the
    moment an engine read failed until a settlement supersedes it.

    NO BYTES, NO PATH INTO AN OUTPUT, NO TASK TEXT AND NO CREDENTIAL. Only
    identities, digests, instants, states and the typed ending.
    """
    from contextlib import ExitStack

    from baton_v12.job_manager import publication_execution
    from baton_v12.worker_manager import attempt_runtime_of

    with ExitStack() as opened:
        jobs, control = _stores(taken, clock, opened)
        decision = publication_recovery.decision_of(jobs, taken.decision_id)
        if decision is None:
            raise ContractRefusal(
                "refused", "precondition",
                f"this store records no publication decision "
                f"{taken.decision_id!r}")
        answer = {
            "schema": "baton.v12.output-publication-status/1",
            "observed_at": clock(),
            "decision": {
                "decision_id": decision["decision_id"],
                "disposition": decision["disposition"],
                "decided_at": decision["decided_at"],
                "owner": decision["owner"]["endpoint"]},
            "original": {
                "job_id": decision["job_id"],
                "stage_id": decision["stage_id"],
                "episode": decision["episode"],
                "attempt_id": decision["attempt_id"],
                "work_id": decision["work_id"],
                "state": "failed at output publication; unchanged by any "
                         "recovery"},
            "admission": None, "recovery": None, "publication_attempt": None,
            "gate": None}
        admitted = publication_recovery.admission_of(jobs, taken.decision_id)
        reserved = publication_recovery.intent_of(jobs, taken.decision_id)
        if admitted is None:
            answer["admission"] = {
                "state": "reserved; admission incomplete"
                if reserved is not None else "not admitted",
                "job_id": None if reserved is None else reserved["job_id"],
                "next": "repeat the same publication-decide --approve; it "
                        "replays the decision and resumes the admission"}
            return _say(answer, stream)
        job_id = admitted["job_id"]
        answer["admission"] = {"state": "admitted", "job_id": job_id,
                               "admitted_at": admitted["admitted_at"],
                               "input_digest": admitted["input_digest"]}
        ready = publication_execution.publication_readiness(
            jobs, taken.decision_id, control=control)
        answer["recovery"] = ready
        deadline = publication_execution.deadline_of(
            jobs, taken.decision_id, now=answer["observed_at"])
        answer["recovery"]["publication_deadline"] = {
            "deadline_at": deadline["deadline_at"],
            "origin": deadline["origin"], "reached": deadline["reached"],
            "restart_resets": False}
        launched = publication_execution.launch_of(jobs, job_id)
        if launched is not None:
            recorded = attempt_runtime_of(control, launched["attempt_id"])
            answer["publication_attempt"] = {
                "attempt_id": launched["attempt_id"],
                # THE JOURNAL'S LAST WORD, labelled as that.
                "recorded": None if recorded is None else {
                    "execution_runtime": recorded["execution_runtime"],
                    "cleanup": recorded["cleanup"]},
                "runtime_knowledge": ready["runtime_knowledge"]}
        item = publication_execution.owner_item_of(jobs, job_id)
        answer["owner_item"] = item
        # THE REVIEW, AS ITS OWN STATEMENT. Where the stage stands is this
        # store's; the verdict is the review owner's record and is read from
        # it, never inferred from the stage having ended. No findings text.
        answer["review"] = _review(jobs, control, admitted, ready)
        answer["review_item"] = publication_execution.review_item_of(
            jobs, job_id)
        answer["gate"] = publication_execution.execution_gate(jobs, job_id)
        return _say(answer, stream)


VERBS = {"publication-inspect": _inspect, "publication-decide": _decide,
         "publication-status": _status}


def main(argv, *, clock=None, stream=None):
    from tools.job_manager import _utc_clock

    parser = argparse.ArgumentParser(
        prog="manager publication",
        description="Inspect one completed implementation whose OUTPUT "
                    "PUBLICATION failed, or decide it. An approval records "
                    "the owner's exact disposition and asks the manager to "
                    "compose the admission it reaches; a denial or a hold "
                    "launches nothing, and neither does an approval while the "
                    "publication execution path is unavailable.")
    parser.add_argument("command", choices=COMMANDS)
    parser.add_argument("--store", required=True,
                        help="the Job store the failed Job lives in")
    parser.add_argument("--authority-uuid", required=True,
                        help="the 32-lowercase-hex Authority this Job store "
                             "belongs to")
    parser.add_argument("--incarnation", required=True,
                        help="this process's incarnation, which is what "
                             "restart recovery distinguishes managers by")
    parser.add_argument("--control", required=True,
                        help="the Worker Manager control store, opened "
                             "READ-ONLY: the original output, the attempt's "
                             "assignment and the absence of any published "
                             "result are read through their owner, and a "
                             "decision must not be able to change the "
                             "evidence it is judging")
    parser.add_argument("--authority", default=None,
                        help="the Authority store whose Work this failure "
                             "ran under; it resolves the deciding "
                             "participant's principal and the Work's own "
                             "effective scope, and this command writes "
                             "nothing to it")
    parser.add_argument("--instance", default=None,
                        help="the deployment's state root, whose own layout "
                             "and emitted configuration say which stores, "
                             "which Authority and which workspace storage it "
                             "owns")
    parser.add_argument("--owners",
                        default="tools.publication_decision:owners",
                        help="the deployment's owner-port factory as "
                             "module:attribute; it composes the owner "
                             "authorization, the host OUTPUT owner, the host "
                             "exclusion, the source-aware consumer, the Work "
                             "authorization, the deployment binding and the "
                             "instance guard over this instance's own stores")
    parser.add_argument("--job", default=None,
                        help="the failed Job whose output was never published")
    parser.add_argument("--stage", default=None,
                        help="that Job's implementation stage; another "
                             "stage's ending is another ending")
    parser.add_argument("--episode", default=None, type=int,
                        help="the episode whose attempt produced the retained "
                             "output; the attempt is resolved FROM it and is "
                             "deliberately not an operand")

    reading = parser.add_argument_group("publication-inspect")
    reading.add_argument("--participant", default=None,
                         help="the acting participant. On "
                              "publication-inspect it is optional and reports "
                              "whether that address holds the decision "
                              "capability in the Work's own scope; on "
                              "publication-decide it is required and there is "
                              "deliberately no --actor")
    reading.add_argument("--control-report", action="store_true",
                         help="also report the failed Job's own LIM-5 control "
                              "and whichever fence closed it")

    deciding = parser.add_argument_group("publication-decide")
    deciding.add_argument("--decision-id", default=None,
                          help="the owner's own operation key. The same key "
                               "with the same operands replays the committed "
                               "decision; with different operands it "
                               "collides, and a later disposition is a NEW "
                               "key and a new attributable act")
    held = deciding.add_mutually_exclusive_group()
    held.add_argument("--approve", dest="disposition", action="store_const",
                      const=publication_recovery.APPROVED,
                      help="approve the exact corrective publication "
                           "disposition below")
    held.add_argument("--deny", dest="disposition", action="store_const",
                      const=publication_recovery.DENIED,
                      help="deny it; nothing is launched")
    held.add_argument("--hold", dest="disposition", action="store_const",
                      const=publication_recovery.HELD,
                      help="hold it for a later explicit disposition; "
                           "nothing is launched")
    deciding.add_argument("--expect-attempt", default=None,
                          help="the exact failed execution this decision is "
                               "about, as the inspection reported it")
    deciding.add_argument("--expect-selection-digest", default=None,
                          help="the canonical digest of the inspection the "
                               "owner read; an inspection that changed under "
                               "them collides rather than being decided")
    deciding.add_argument("--expect-candidate-base", default=None)
    deciding.add_argument("--expect-candidate-head", default=None)
    deciding.add_argument("--expect-output-digest", default=None,
                          help="the measured tree digest of the ORIGINAL "
                               "host-held output; a path or a name is not an "
                               "output")
    deciding.add_argument("--expect-output-bytes", default=None, type=int,
                          help="that measurement's total byte count")
    deciding.add_argument("--expect-producer-status", default=None, type=int,
                          help="the producer verifier's observed exit status; "
                               "only 0 is reusable evidence")
    deciding.add_argument("--producer-verification", action="append",
                          default=None, metavar="WORD",
                          help="one argument word of the command the PRODUCER "
                               "ran, repeatable in order (write a word that "
                               "starts with a dash as "
                               "--producer-verification=-m). It is producer "
                               "evidence and never independent acceptance, "
                               "and the recovery pipeline does not repeat it")
    deciding.add_argument("--context-digest", default=None,
                          help="the digest of the producer's declared "
                               "execution context; a command string must not "
                               "hide a changed input identity")
    deciding.add_argument("--declaration-digest", default=None,
                          help="the exact digest of the corrective output "
                               "declaration W385694 published")
    deciding.add_argument("--profile", default=None,
                          help="the owner-approved finite profile identity")
    deciding.add_argument("--profile-digest", default=None,
                          help="that profile definition's exact digest; the "
                               "admission boundary checks exact agreement")
    deciding.add_argument("--stage-word", action="append", default=None,
                          metavar="STAGE",
                          help="one selected stage word, repeatable in order: "
                               "publication then review. implementation, "
                               "verification and integration are refused by "
                               "name")

    taken = parser.parse_args(argv)
    if taken.command == "publication-status":
        # A STATUS READ NAMES ONE DECISION AND NOTHING ELSE: no participant,
        # no Authority, no instance and no selectors of the failed execution,
        # all of which it reads off the committed decision.
        if taken.decision_id is None:
            parser.error("publication-status needs --decision-id")
    else:
        absent = sorted(flag for flag, value in (
            ("--authority", taken.authority), ("--instance", taken.instance),
            ("--job", taken.job), ("--stage", taken.stage),
            ("--episode", taken.episode)) if value is None)
        if absent:
            parser.error(taken.command + " needs " + ", ".join(absent))
    if taken.command == "publication-decide":
        required = {"--participant": taken.participant,
                    "--decision-id": taken.decision_id,
                    "--expect-attempt": taken.expect_attempt,
                    "--expect-selection-digest":
                        taken.expect_selection_digest,
                    "--expect-candidate-base": taken.expect_candidate_base,
                    "--expect-candidate-head": taken.expect_candidate_head,
                    "--expect-output-digest": taken.expect_output_digest,
                    "--expect-output-bytes": taken.expect_output_bytes,
                    "--expect-producer-status": taken.expect_producer_status,
                    "--producer-verification": taken.producer_verification,
                    "--context-digest": taken.context_digest,
                    "--declaration-digest": taken.declaration_digest,
                    "--profile": taken.profile,
                    "--profile-digest": taken.profile_digest,
                    "--stage-word": taken.stage_word}
        absent = sorted(one for one, value in required.items()
                        if value is None)
        if absent:
            parser.error("publication-decide needs " + ", ".join(absent))
        if taken.disposition is None:
            parser.error("publication-decide needs one of --approve, --deny "
                         "or --hold; an owner disposition is an explicit act")
    said = stream if stream is not None else sys.stdout
    try:
        return VERBS[taken.command](taken, clock or _utc_clock(), said)
    except ContractRefusal as refusal:
        # THE OPERATION'S OWN SENTENCE, not a traceback. Every refusal this
        # command can reach is a contract answer an owner is meant to read,
        # and the typed pair is printed with it so a scripted caller can
        # branch on the kind rather than on the prose.
        return _refused(f"{refusal.category}/{refusal.code}: "
                        f"{refusal.message}")


if __name__ == "__main__":                                # pragma: no cover
    raise SystemExit(main(sys.argv[1:]))
