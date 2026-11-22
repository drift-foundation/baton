"""THE SUPPORTED OWNER SURFACE FOR A RETAINED VERIFICATION FAILURE: read the
delivered item, then decide it -- and an approval asks the manager to admit the
one linked verification/review-only successor.

W385624 Stage 1-B, under DESIGN REC-8 and the accepted Stage 1 contract. Two
verbs of the installed `manager` command, reachable from the deployed bundle
exactly as `cancel-job` and `settle-stopped` are:

    manager recovery-item    ... what the owner is being asked to decide
    manager recovery-decide  ... approve, deny or hold it, bound to the exact
                                 failure, report, candidate and verifier

WHAT WAS MISSING, and it is the same shape of absence W321689 found for the
owner's ordinary disposition. Stage 1-A delivers an owner item with a bounded
diagnosis and a proposed corrected command, and nothing exposed it: the item,
the report bytes, the original argv and the four digests a decision must bind
were reachable only by writing Python against the package, and the decision
itself did not exist at all. An owner surface that is reachable only out of
band is reachable only by an agent, and a recovery authorized by an agent is
the thing this whole contract refuses.

WHAT THIS IS. A wrapper over the public faces and nothing more. The Job store
holds the records; `job_manager.retained_recovery` owns every rule about
authorization, exact inputs, generic retries, stage sets, profiles, fences,
replay and review-only evidence; the Authority owns who may decide and in
which scope; the host, the deployment and the instance guard own cessation,
binding and exclusion. This module decides which owner each operand reaches
and prints what it was told -- REC-7's "the CLI requests the operation and
reports its outcome", which REC-8 composes unchanged.

THERE IS NO `--actor` AND NO `--scope`, and those two absences are the point.
`--participant` mints the owner authorization port and the Authority resolves
the principal; the scope comes off the Work's own row. A caller cannot name an
identity this command then treats as authorized, and cannot choose the scope
an act is authorized in.

THE CONTROL STORE IS OPENED READ-ONLY. A decision reads the host's record of
the failed execution and the retained candidate and asks it nothing else; a
surface that needed write access to the Worker Manager to admit a successor
would be able to change the evidence it was judging. The Authority is opened
WRITABLY for neither verb: an owner decision writes no Authority row -- it is
authorized by one -- so both verbs take the read-only handle and a serving
deployment is not write-locked by somebody reading their own item.

IT LAUNCHES NOTHING ITSELF. `recovery-decide --deny` and `--hold` record an
attributable disposition and stop. `--approve` records the decision and then
asks the manager for the admission; the manager reserves an identity, composes
the owners and submits a Job whose stages carry no implementation. The
approved corrected verifier is NOT executed here and no candidate is
materialized or handed to review: the answer's `readiness` says which acts are
still owed, because an answer carrying a Job id and saying nothing else would
read as a recovery that happened.
"""
import argparse
import importlib
import json
import os
import sys

from baton_v12.contracts import ContractRefusal
from baton_v12.job_manager import JobStore, retained_recovery
from baton_v12.worker_manager import ControlStore

__all__ = ["COMMANDS", "OWNERS", "OwnerAuthorization", "owners", "main"]

COMMANDS = ("recovery-item", "recovery-decide")

# THE OWNER-PORT SET ONE DEPLOYMENT SUPPLIES, written down rather than
# discovered from whatever object a factory returned -- `delegation.OPERATIONS`
# and `failure_analysis.ANALYSIS_SEAM`'s rule, for their reason: a member that
# cannot be called would otherwise fault between a committed reservation and
# the effects that reservation authorizes.
#
#   `owner`        the owner authorization port: who is acting, the Work's own
#                  row and the Authority's one decision seam.
#   `exclusion`    the host's record of each prior attempt's runtime and
#                  workspace token.
#   `authorization` the Authority's answer about the Work this successor runs
#                  under. Read only: this admission never mints a Work.
#   `binding`      the deployment configuration's own additive binding and its
#                  servability selector.
#   `ownership`    the instance guard, plus this admission's own invocation
#                  lock.
OWNERS = ("owner", "exclusion", "authorization", "binding", "ownership")


def _say(value, stream):
    json.dump(value, stream, indent=2, sort_keys=True, ensure_ascii=False)
    stream.write("\n")
    return 0


def _refused(message):
    """ONE REFUSAL LINE ON STDERR, and the answer stays on stdout.

    `disposition_command._refused`'s posture: a refusal is for whoever ran the
    command, and a scripted caller reading stdout must not have to parse one
    out of the document it was expecting. Where BOTH are true -- the owner's
    decision committed and its admission did not -- the document goes to
    stdout and this line to stderr, so neither reader loses its half.
    """
    print("refused: " + message, file=sys.stderr)
    return 1


class OwnerAuthorization:
    """WHO IS DECIDING, and the Authority's own answer about whether they may.

    THREE MEMBERS AND NOT ONE MORE. `participant` is the address this port was
    minted for -- there is no operand on the operation through which a caller
    could name another -- `work_of` answers the Work's own row, which is where
    the EFFECTIVE SCOPE is read from, and `authorize` is W16821's one decision
    seam, which answers with the decision rather than with a boolean so what
    is recorded beside the act says who acted, in which scope, by which grant
    and under which policy generation.

    IT HOLDS NO RULE. Whether the capability is the right one, whether the
    scope agrees with the Work's and whether the decision document describes
    this act are `retained_recovery._owner`'s, enforced inside the operation.
    An adapter that decided any of them would be the script-side precheck
    REC-7 forbids, wearing the product's name.
    """

    def __init__(self, authority, *, participant):
        self._authority = authority
        self.participant = participant

    def work_of(self, work_id):
        from baton_v12.authority import Refusal

        try:
            return self._authority.project_work(work_id)
        except Refusal:
            # ABSENCE IS CONFIRMED BY A SECOND OWNER READ rather than by
            # reading a refusal's prose -- `WorkAuthorization.work_of`'s rule,
            # for its reason: branching on the wording of a refusal is a
            # branch that changes when the sentence is improved.
            if self._authority.work_creation(work_id) is None:
                return None
            raise

    def authorize(self, participant, *, capability, scope):
        return self._authority.authorize_capability(participant, capability,
                                                    scope=scope)


def owners(request):
    """Compose this deployment's five owner ports over the stores it owns.

    THE DEFAULT FACTORY, and the reason there is an operand for it at all is
    `status --observe`'s and `serve --operations`': which owners a command
    acts through is a DEPLOYMENT fact, and a tool that could only ever compose
    one set would be this file deciding it for every installation. Every port
    here is the accepted W358969 adapter over this instance's own layout and
    its own emitted configuration; nothing is searched for and nothing is
    guessed.
    """
    from tools.fresh_attempt_ports import (DeploymentBinding, HostExclusion,
                                           InstanceOwnership,
                                           WorkAuthorization,
                                           instance_identity)

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
    return {
        "owner": OwnerAuthorization(authority,
                                    participant=request["participant"]),
        "exclusion": HostExclusion(request["control_handle"],
                                   identity=identity),
        # COMPOSED WITH NO ROUTE AND NO PRODUCERS, because the recovery
        # admission REUSES the failed Job's Work and never creates one:
        # `retained_recovery._authorized` refuses an absent Work rather than
        # minting one, so `create_work` is not on this path and a route is not
        # an operand of this surface at all. A route here would be this
        # command offering to create a Work that nothing would then serve.
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
            f"retained recovery is decided and admitted against the instance "
            f"whose failure it is about")
    return identity[named]


def _owners_from(name, request):
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
    missing = [one for one in OWNERS if held.get(one) is None]
    if missing:
        raise ContractRefusal(
            "refused", "capability",
            f"the owner-port factory {name!r} supplies no "
            f"{', '.join(missing)}; a retained recovery composes "
            f"{', '.join(OWNERS)} and this operation does not decide an "
            f"owner's fact for it by assuming one")
    return held


def _stores(taken, clock, opened):
    """The three stores this surface touches, each opened as its role allows.

    The Job store WRITABLY for a decision and READ-ONLY for the item; the
    control store always read-only; the Authority always read-only. The roles
    are the operands' own and not a convention: a read that took a write lock
    on a serving deployment would make asking about your own item an
    operational act.
    """
    jobs = opened.enter_context(
        JobStore.open(taken.store, authority_uuid=taken.authority_uuid,
                      incarnation=taken.incarnation, clock=clock)
        if taken.command == "recovery-decide" else
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


def _item(taken, clock, stream):
    """WHAT THE OWNER IS BEING ASKED TO DECIDE. READ-ONLY.

    The whole document is `retained_recovery.owner_item_read`'s: the delivered
    item, the diagnosis resolved out of the custody that holds it, the
    original failed verifier and its declared execution context, the retained
    candidate, the four digests a decision binds in the exact spelling it
    compares them in, the proposed correction, the approved profile and its
    digest, the selectable stage sets, what has already been decided and
    whether the asking participant holds the capability at all.
    """
    from contextlib import ExitStack

    with ExitStack() as opened:
        jobs, control = _stores(taken, clock, opened)
        authorization = None
        if taken.participant is not None:
            held = _owners_from(taken.owners, _request(taken, control))
            if held.get("release") is not None:
                opened.callback(held["release"])
            authorization = held["owner"]
        return _say(retained_recovery.owner_item_read(
            jobs, control, taken.failure, authorization=authorization,
            now=clock() if taken.control_report else None), stream)


def _decide(taken, clock, stream):
    """THE OWNER'S OWN ACT, and the admission an approval asks for.

    TWO DURABLE ACTS AND THEY ARE NOT ONE. The decision is journalled under
    the owner's own operation key with every operand compared first; the
    admission is a separate manager operation with its own identity, its own
    fences and its own reservation. So a crash between them leaves a decision
    that can be carried out rather than an effect nobody decided, and running
    the same command again replays the first and resumes the second.
    """
    from contextlib import ExitStack

    disposition = taken.disposition
    with ExitStack() as opened:
        jobs, control = _stores(taken, clock, opened)
        held = _owners_from(taken.owners, _request(taken, control))
        if held.get("release") is not None:
            opened.callback(held["release"])
        decision = retained_recovery.decide(
            jobs, control, key=taken.failure,
            decision_id=taken.decision_id, disposition=disposition,
            authorization=held["owner"],
            expected={
                "failure_digest": taken.expect_failure_digest,
                "report_digest": taken.expect_report_digest,
                "candidate_base": taken.expect_candidate_base,
                "candidate_head": taken.expect_candidate_head,
                "candidate_content_digest": taken.expect_candidate_digest,
                "original_argv": list(taken.original_verification or [])},
            correction={"argv": list(taken.corrected_verification or []),
                        "context_digest": taken.context_digest},
            profile=taken.profile, profile_digest=taken.profile_digest,
            stages=list(taken.stage or []),
            lineage=_lineage(taken), now=clock())
        answer = {"decision": decision, "successor": None,
                  "admitted": False, "refusal": None}
        if disposition != retained_recovery.APPROVED:
            return _say(answer, stream)
        try:
            answer["successor"] = retained_recovery.admit_successor(
                jobs, control, decision_id=taken.decision_id,
                exclusion=held["exclusion"],
                authorization=held["authorization"],
                binding=held["binding"], ownership=held["ownership"],
                now=clock())
        except ContractRefusal as refusal:
            # THE OWNER'S ACT HAPPENED AND THE ADMISSION DID NOT, and an
            # operator is owed BOTH facts. A bare refusal on stderr would
            # leave them unable to tell "nothing was recorded" from "your
            # decision stands and the host could not account for the prior
            # runtime", which are two different things to do next -- and the
            # second one is finished by running this same command again.
            answer["refusal"] = {"category": refusal.category,
                                 "code": refusal.code,
                                 "message": refusal.message}
            _say(answer, stream)
            return _refused(f"{refusal.category}/{refusal.code}: "
                            f"{refusal.message}")
        answer["admitted"] = True
        return _say(answer, stream)


def _lineage(taken):
    """The review-only lineage, or nothing -- and never half of one.

    THREE OPERANDS OR NONE. A lineage naming an expired successor and no
    verification attempt is not a weaker lineage, it is an incomplete one, and
    accepting it here would hand the operation a document it then has to
    refuse from the wrong end.
    """
    named = {"successor_job_id": taken.prior_successor,
             "verification_attempt_id": taken.prior_verification_attempt,
             "verification_result_digest": taken.prior_verification_digest}
    if all(one is None for one in named.values()):
        return None
    absent = sorted(one for one, value in named.items() if value is None)
    if absent:
        raise ContractRefusal(
            "refused", "precondition",
            f"a review-only recovery names the expired successor, its "
            f"verification attempt and the passed result it reuses; this one "
            f"names no {', '.join(absent)}")
    return named


VERBS = {"recovery-item": _item, "recovery-decide": _decide}


def main(argv, *, clock=None, stream=None):
    from tools.job_manager import _utc_clock

    parser = argparse.ArgumentParser(
        prog="manager recovery",
        description="Read one retained verification failure's owner item, or "
                    "decide it. An approval asks the manager to admit the one "
                    "linked verification/review-only successor; a denial or a "
                    "hold launches nothing.")
    parser.add_argument("command", choices=COMMANDS)
    parser.add_argument("--store", required=True,
                        help="the Job store the recovery records live in")
    parser.add_argument("--authority-uuid", required=True,
                        help="the 32-lowercase-hex Authority this Job store "
                             "belongs to")
    parser.add_argument("--incarnation", required=True,
                        help="this process's incarnation, which is what "
                             "restart recovery distinguishes managers by")
    parser.add_argument("--control", required=True,
                        help="the Worker Manager control store, opened "
                             "READ-ONLY: the retained candidate and the "
                             "delivered diagnosis are read through their "
                             "owner, and a decision must not be able to "
                             "change the evidence it is judging")
    parser.add_argument("--authority", required=True,
                        help="the Authority store whose Work this failure "
                             "ran under; it resolves the deciding "
                             "participant's principal and the Work's own "
                             "effective scope, and this command writes "
                             "nothing to it")
    parser.add_argument("--instance", required=True,
                        help="the deployment's state root, whose own layout "
                             "and emitted configuration say which stores and "
                             "which Authority it owns and whose selector is "
                             "asked whether a worker can serve the "
                             "successor's review stage")
    parser.add_argument("--owners", default="tools.recovery_decision:owners",
                        help="the deployment's owner-port factory as "
                             "module:attribute; it composes the owner "
                             "authorization, the host exclusion, the Work "
                             "authorization, the deployment binding and the "
                             "instance guard over this instance's own stores")
    parser.add_argument("--failure", required=True,
                        help="the failure key Stage 1-A attributed this "
                             "ending under")

    reading = parser.add_argument_group("recovery-item")
    reading.add_argument("--participant", default=None,
                         help="the acting participant. On recovery-item it "
                              "is optional and reports whether that address "
                              "holds the decision capability in the Work's "
                              "own scope; on recovery-decide it is required "
                              "and there is deliberately no --actor")
    reading.add_argument("--control-report", action="store_true",
                         help="also report the failed Job's own LIM-5 control "
                              "and whichever fence closed it")

    deciding = parser.add_argument_group("recovery-decide")
    deciding.add_argument("--decision-id", default=None,
                          help="the owner's own operation key. The same key "
                               "with the same operands replays the committed "
                               "decision; with different operands it "
                               "collides, and a later disposition is a NEW "
                               "key and a new attributable act")
    held = deciding.add_mutually_exclusive_group()
    held.add_argument("--approve", dest="disposition", action="store_const",
                      const=retained_recovery.APPROVED,
                      help="approve the exact correction and the "
                           "verification/review-only scope below")
    held.add_argument("--deny", dest="disposition", action="store_const",
                      const=retained_recovery.DENIED,
                      help="deny it; nothing is launched")
    held.add_argument("--hold", dest="disposition", action="store_const",
                      const=retained_recovery.HELD,
                      help="hold it for a later explicit disposition; "
                           "nothing is launched")
    deciding.add_argument("--expect-failure-digest", default=None,
                          help="the fixed input digest the delivered analysis "
                               "was admitted on")
    deciding.add_argument("--expect-report-digest", default=None,
                          help="the delivered diagnosis's own digest; omitted "
                               "for a finite analysis ending, which "
                               "delivered partial evidence and no report")
    deciding.add_argument("--expect-candidate-base", default=None)
    deciding.add_argument("--expect-candidate-head", default=None)
    deciding.add_argument("--expect-candidate-digest", default=None,
                          help="the retained candidate's measured content "
                               "digest; a commit name alone is not a "
                               "candidate")
    deciding.add_argument("--original-verification", action="append",
                          default=None, metavar="WORD",
                          help="one argument word of the command that FAILED, "
                               "repeatable in order (write a word that starts "
                               "with a dash as --original-verification=-m)")
    deciding.add_argument("--corrected-verification", action="append",
                          default=None, metavar="WORD",
                          help="one argument word of the APPROVED corrected "
                               "command, repeatable in order. Approving the "
                               "command that failed is refused as the generic "
                               "retry it is")
    deciding.add_argument("--context-digest", default=None,
                          help="the approved execution context's digest; a "
                               "command string must not hide a changed "
                               "working directory, environment or tool "
                               "selection")
    deciding.add_argument("--profile", default=None,
                          help="the owner-approved finite profile identity")
    deciding.add_argument("--profile-digest", default=None,
                          help="that profile definition's exact digest; "
                               "admission checks exact agreement")
    deciding.add_argument("--stage", action="append", default=None,
                          metavar="STAGE",
                          help="one selected stage word, repeatable in order: "
                               "verification then review, or review alone "
                               "under a review-only decision. implementation "
                               "is refused by name")
    deciding.add_argument("--prior-successor", default=None,
                          help="the expired successor a review-only decision "
                               "follows")
    deciding.add_argument("--prior-verification-attempt", default=None,
                          help="that successor's verification attempt "
                               "identity")
    deciding.add_argument("--prior-verification-digest", default=None,
                          help="the digest of its journalled passed "
                               "verification account")

    taken = parser.parse_args(argv)
    if taken.command == "recovery-decide":
        required = {"--participant": taken.participant,
                    "--decision-id": taken.decision_id,
                    "--expect-failure-digest": taken.expect_failure_digest,
                    "--expect-candidate-base": taken.expect_candidate_base,
                    "--expect-candidate-head": taken.expect_candidate_head,
                    "--expect-candidate-digest":
                        taken.expect_candidate_digest,
                    "--original-verification": taken.original_verification,
                    "--corrected-verification": taken.corrected_verification,
                    "--context-digest": taken.context_digest,
                    "--profile": taken.profile,
                    "--profile-digest": taken.profile_digest,
                    "--stage": taken.stage}
        absent = sorted(one for one, value in required.items()
                        if value is None)
        if absent:
            parser.error("recovery-decide needs " + ", ".join(absent))
        if taken.disposition is None:
            parser.error("recovery-decide needs one of --approve, --deny or "
                         "--hold; an owner disposition is an explicit act")
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
